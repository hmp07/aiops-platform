"""M8 AIOps — Core Services (sxdevops architecture, FastAPI adaptation).

All business logic lives here. API endpoints in api.py / admin_api.py are thin
routers that delegate to these functions.

Porting from: sxdevops/backend/aiops/services.py (~7400 lines)
"""

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.session import async_session_factory
from app.modules.module8_aiops.models import (
    AIOpsAgentConfig,
    AIOpsChatMessage,
    AIOpsChatSession,
    AIOpsMCPServer,
    AIOpsModelProvider,
    AIOpsPendingAction,
    AIOpsSkill,
    AIOpsToolInvocation,
    AIOpsModelInvocation,
)

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# Constants (from sxdevops)
# ═══════════════════════════════════════════════════════════════

DEFAULT_SYSTEM_PROMPT = (
    "You are an AIOps intelligent operations assistant. "
    "Prioritize using available MCP tools to fetch structured platform data. "
    "Never fabricate resources, alerts, logs, traces, or execution results. "
    "Distinguish between facts, inferences, and suggestions in your answers. "
    "For execution-related actions, only generate drafts before confirmation."
)

DEFAULT_WELCOME_MESSAGE = (
    "你好，我可以帮你结合平台上下文查询资源、分析告警、生成待执行任务等。"
)

DEFAULT_SUGGESTED_QUESTIONS = [
    "当前有多少设备？",
    "最近有哪些未确认的告警？",
    "查询设备列表及其状态",
    "最近有哪些严重告警？",
    "帮我分析一下当前告警情况",
    "查询 IP 地址管理中的子网信息",
]


def _now():
    return datetime.now(timezone.utc)


# ═══════════════════════════════════════════════════════════════
# Config & Bootstrap
# ═══════════════════════════════════════════════════════════════


async def get_agent_config(db: AsyncSession) -> AIOpsAgentConfig:
    """Get or create the singleton agent config (sxdevops pattern).

    Ensures defaults are present and repairs legacy/mojibake values.
    """
    result = await db.execute(select(AIOpsAgentConfig).limit(1))
    config = result.scalar_one_or_none()

    if config is None:
        config = AIOpsAgentConfig(
            system_prompt=DEFAULT_SYSTEM_PROMPT,
            welcome_message=DEFAULT_WELCOME_MESSAGE,
            suggested_questions=DEFAULT_SUGGESTED_QUESTIONS,
        )
        db.add(config)
        await db.commit()
        await db.refresh(config)
        return config

    # Repair missing defaults (sxdevops pattern: fix up on read)
    needs_save = False

    if not config.system_prompt:
        config.system_prompt = DEFAULT_SYSTEM_PROMPT
        needs_save = True

    if not config.welcome_message:
        config.welcome_message = DEFAULT_WELCOME_MESSAGE
        needs_save = True

    if not config.suggested_questions:
        config.suggested_questions = DEFAULT_SUGGESTED_QUESTIONS
        needs_save = True

    if config.require_confirmation is not True:
        config.require_confirmation = True
        needs_save = True

    if needs_save:
        await db.commit()
        await db.refresh(config)

    return config


async def get_active_provider(db: AsyncSession, config: AIOpsAgentConfig | None = None):
    """Pick the best available LLM provider (sxdevops pattern).

    Priority: config.default_provider → first enabled → first by id.
    """
    if config is None:
        config = await get_agent_config(db)

    # Try the configured default provider first
    if config.default_provider_id:
        provider_result = await db.execute(
            select(AIOpsModelProvider).where(
                AIOpsModelProvider.id == config.default_provider_id,
                AIOpsModelProvider.is_enabled == True,
            )
        )
        provider = provider_result.scalar_one_or_none()
        if provider and _provider_is_ready(provider):
            return provider

    # Fallback: first enabled provider that is ready
    result = await db.execute(
        select(AIOpsModelProvider)
        .where(AIOpsModelProvider.is_enabled == True)
        .order_by(AIOpsModelProvider.id)
    )
    for item in result.scalars().all():
        if _provider_is_ready(item):
            return item

    return None


def _provider_is_ready(provider: AIOpsModelProvider) -> bool:
    """Check if a provider has the minimum config to work."""
    return bool(provider.base_url and provider.default_model)


async def bootstrap_payload_for_user(db: AsyncSession, user: dict) -> dict:
    """Return the full bootstrap payload for the frontend (sxdevops pattern).

    Includes: agent config, provider info, permissions, runtime settings,
    enabled MCP servers, enabled skills, and action registry.
    """
    config = await get_agent_config(db)
    provider = await get_active_provider(db, config)

    # Build permissions map
    user_permissions = user.get("permissions", []) if user else []

    return {
        "enabled": True,
        "welcome_message": config.welcome_message or DEFAULT_WELCOME_MESSAGE,
        "suggested_questions": config.suggested_questions or DEFAULT_SUGGESTED_QUESTIONS,
        "permissions": {
            "chat": "aiops:chat:view" in user_permissions if user_permissions else True,
            "analyze": "aiops:chat:analyze" in user_permissions if user_permissions else True,
            "config_view": "aiops:config:view" in user_permissions if user_permissions else True,
            "config_manage": "aiops:config:manage" in user_permissions if user_permissions else True,
        },
        "provider": {
            "name": provider.name if provider else "未配置模型",
            "model": provider.default_model if provider else "",
        },
        "runtime": {
            "allow_action_execution": config.allow_action_execution if config else False,
            "require_confirmation": config.require_confirmation if config else True,
            "show_evidence": config.show_evidence if config else True,
        },
        # MCP tools populated from ToolRegistry
        "active_mcp_servers": [
            {
                "id": "builtin-platform",
                "name": "平台内置 MCP",
                "description": "查询设备、告警、日志、IPAM、拓扑和知识库。",
                "tool_whitelist": list(PLATFORM_MCP_TOOL_MAP.keys()),
                "is_builtin": True,
            }
        ],
        "active_skills": [],
        "action_registry": list_action_registry(),
        "action_registry_summary": build_action_registry_summary(),
    }


# ═══════════════════════════════════════════════════════════════
# Action Registry (sxdevops: BUILTIN_ACTION_REGISTRY pattern)
# ═══════════════════════════════════════════════════════════════

# Agent mode constants
AGENT_MODE_DIRECT = "direct"
AGENT_MODE_REACT = "react"
AGENT_MODE_PLAN_REACT = "plan_react"

AGENT_MODE_LABELS = {
    AGENT_MODE_DIRECT: "Direct",
    AGENT_MODE_REACT: "ReAct",
    AGENT_MODE_PLAN_REACT: "Plan+ReAct",
}

# Risk level constants
RISK_READ_ONLY = "read_only"
RISK_DRAFT = "draft"
RISK_WRITE = "write"
RISK_EXECUTE = "execute"

RISK_LEVEL_LABELS = {
    RISK_READ_ONLY: "只读",
    RISK_DRAFT: "草稿",
    RISK_WRITE: "写入",
    RISK_EXECUTE: "执行",
}

# ── Built-in Action Registry ─────────────────────────────────

BUILTIN_ACTION_REGISTRY: list[dict] = [
    {
        "code": "device.query",
        "display_name": "设备查询",
        "category": "资产查询",
        "risk_level": RISK_READ_ONLY,
        "agent_mode": AGENT_MODE_DIRECT,
        "required_context": [],
        "allowed_tools": ["aiops.query_devices", "aiops.query_ipam"],
        "skills": ["answer-formatter"],
        "output_blocks": ["tool_trace"],
        "preflight_required": False,
        "description": "查询设备资产信息，包括设备类型、厂商、IP地址和状态。支持按设备类型、厂商、状态和关键字过滤。",
        "permission": "asset:device:list",
    },
    {
        "code": "alert.root_cause",
        "display_name": "告警根因分析",
        "category": "告警排障",
        "risk_level": RISK_READ_ONLY,
        "agent_mode": AGENT_MODE_PLAN_REACT,
        "required_context": [],
        "allowed_tools": [
            "aiops.query_alerts", "aiops.query_devices",
            "aiops.query_topology", "aiops.query_logs",
        ],
        "skills": ["alert-evidence-checklist", "answer-formatter"],
        "output_blocks": ["incident_card", "evidence_timeline", "risk_notice"],
        "preflight_required": False,
        "description": "分析告警根因，结合设备信息、拓扑依赖和日志证据链给出可能原因和影响范围。",
        "permission": "monitoring:alert:list",
    },
    {
        "code": "log.analyze",
        "display_name": "日志分析",
        "category": "日志查询",
        "risk_level": RISK_READ_ONLY,
        "agent_mode": AGENT_MODE_REACT,
        "required_context": [],
        "allowed_tools": ["aiops.query_logs", "aiops.query_devices"],
        "skills": ["log-pattern-analysis", "answer-formatter"],
        "output_blocks": ["log_samples", "pattern_summary", "tool_trace"],
        "preflight_required": False,
        "description": "查询和分析日志条目，识别错误模式，关联设备和时间窗口。",
        "permission": "log:entry:search",
    },
    {
        "code": "topology.analyze",
        "display_name": "拓扑分析",
        "category": "服务拓扑",
        "risk_level": RISK_READ_ONLY,
        "agent_mode": AGENT_MODE_REACT,
        "required_context": [],
        "allowed_tools": ["aiops.query_topology", "aiops.query_devices", "aiops.query_itop_ci"],
        "skills": ["topology-impact", "answer-formatter"],
        "output_blocks": ["topology_graph", "impact_analysis", "tool_trace"],
        "preflight_required": False,
        "description": "分析服务拓扑和依赖关系图，评估变更影响范围和故障爆炸半径。",
        "permission": "apm:topology:view",
    },
    {
        "code": "config.review",
        "display_name": "配置审查",
        "category": "变更管理",
        "risk_level": RISK_READ_ONLY,
        "agent_mode": AGENT_MODE_DIRECT,
        "required_context": ["device_id"],
        "allowed_tools": ["aiops.query_config_diff", "aiops.query_devices"],
        "skills": ["change-risk-assessment", "answer-formatter"],
        "output_blocks": ["config_diff", "risk_notice", "tool_trace"],
        "preflight_required": True,
        "description": "审查设备配置变更差异，评估变更风险等级，提供回滚建议。",
        "permission": "config:diff:view",
    },
    {
        "code": "knowledge.search",
        "display_name": "知识搜索",
        "category": "知识库",
        "risk_level": RISK_READ_ONLY,
        "agent_mode": AGENT_MODE_DIRECT,
        "required_context": [],
        "allowed_tools": ["aiops.query_knowledge"],
        "skills": ["answer-formatter"],
        "output_blocks": ["tool_trace"],
        "preflight_required": False,
        "description": "搜索知识库中的文章、SOP和Runbook，获取运维经验和标准化流程。",
        "permission": "knowledge:search:execute",
    },
]


def list_action_registry(
    user: dict | None = None,
    include_unavailable: bool = True,
) -> list[dict]:
    """Build a rich action list from BUILTIN_ACTION_REGISTRY (sxdevops pattern).

    Enriches each action with: available flag, human-readable labels, handler info.
    """
    from app.modules.module8_aiops.action_handlers import handler_for_action

    actions = []
    for item in BUILTIN_ACTION_REGISTRY:
        entry = dict(item)
        handler = handler_for_action(item["code"])
        user_perms = user.get("permissions", []) if user else []

        # Permission check
        entry["available"] = (
            not item["permission"]
            or not user_perms
            or item["permission"] in user_perms
        )
        entry["available_reason"] = (
            "" if entry["available"]
            else f"缺少权限：{item['permission']}"
        )

        # Human-readable labels
        entry["agent_mode_display"] = AGENT_MODE_LABELS.get(
            item["agent_mode"], item["agent_mode"]
        )
        entry["risk_level_display"] = RISK_LEVEL_LABELS.get(
            item["risk_level"], item["risk_level"]
        )

        # Handler info
        entry["page_prefixes"] = handler.page_prefixes if handler else []
        entry["keywords"] = handler.keywords[:5] if handler else []

        actions.append(entry)

    if not include_unavailable:
        actions = [a for a in actions if a["available"]]

    return actions


def build_action_registry_summary(actions: list[dict] | None = None) -> dict:
    """Aggregated summary of all actions (sxdevops pattern)."""
    if actions is None:
        actions = list_action_registry()

    available = [a for a in actions if a.get("available", True)]
    by_risk = {}
    for level in [RISK_READ_ONLY, RISK_DRAFT, RISK_WRITE, RISK_EXECUTE]:
        count = len([a for a in actions if a.get("risk_level") == level])
        if count > 0:
            by_risk[level] = count

    return {
        "total": len(actions),
        "available": len(available),
        "unavailable": len(actions) - len(available),
        "by_risk": by_risk,
        "preflight_required": len([a for a in actions if a.get("preflight_required")]),
    }


# ═══════════════════════════════════════════════════════════════
# MCP Tool System
# ═══════════════════════════════════════════════════════════════

# Will be populated by register_builtin_tools()
PLATFORM_MCP_TOOL_MAP: dict = {}


def _register_builtin_mcp_tools():
    """Register all builtin platform MCP tools into the ToolRegistry.

    Called at app startup (see main.py lifespan).
    """
    from app.modules.module8_aiops.tools.registry import ToolSpec, register_tool
    from app.modules.module8_aiops.tools.builtin.query_devices import (
        TOOL_DEFINITION as DEVICE_TOOL,
        execute as execute_query_devices,
    )
    from app.modules.module8_aiops.tools.builtin.query_alerts import (
        TOOL_DEFINITION as ALERT_TOOL,
        execute as execute_query_alerts,
    )
    from app.modules.module8_aiops.tools.builtin.query_knowledge import (
        TOOL_DEFINITION as KNOWLEDGE_TOOL,
        execute as execute_query_knowledge,
    )
    from app.modules.module8_aiops.tools.builtin.query_ipam import (
        TOOL_DEFINITION as IPAM_TOOL,
        execute as execute_query_ipam,
    )
    from app.modules.module8_aiops.tools.builtin.query_topology import (
        TOOL_DEFINITION as TOPOLOGY_TOOL,
        execute as execute_query_topology,
    )
    from app.modules.module8_aiops.tools.builtin.query_logs import (
        TOOL_DEFINITION as LOGS_TOOL,
        execute as execute_query_logs,
    )

    builtins = [
        (DEVICE_TOOL, execute_query_devices),
        (ALERT_TOOL, execute_query_alerts),
        (KNOWLEDGE_TOOL, execute_query_knowledge),
        (IPAM_TOOL, execute_query_ipam),
        (TOPOLOGY_TOOL, execute_query_topology),
        (LOGS_TOOL, execute_query_logs),
    ]

    for tool_def, handler in builtins:
        spec = ToolSpec(
            name=tool_def["name"],
            title=tool_def["title"],
            description=tool_def["description"],
            handler_name=tool_def["handler_name"],
            input_schema=tool_def["input_schema"],
            permission=tool_def.get("permission", ""),
        )
        register_tool(spec, handler)
        PLATFORM_MCP_TOOL_MAP[tool_def["name"]] = tool_def["handler_name"]

    logger.info("Registered %d builtin MCP tools", len(builtins))


def list_platform_mcp_tools(user: dict | None = None) -> list[dict]:
    """List all registered platform MCP tools (sxdevops pattern).

    Filters by user permissions if user provided.
    """
    from app.modules.module8_aiops.tools.registry import list_tools
    return list_tools(user)


async def invoke_platform_mcp_tool(
    tool_name: str,
    arguments: dict | None = None,
    user: dict | None = None,
) -> dict:
    """Invoke a platform MCP tool by name (sxdevops pattern).

    Args:
        tool_name: Full tool name, e.g. 'aiops.query_devices'
        arguments: Tool arguments dict with 'query', 'limit', etc.
        user: Current user dict for permission checks

    Returns:
        Tool result dict with 'found', 'items', etc.
    """
    from app.modules.module8_aiops.tools.registry import get_tool

    arguments = arguments if isinstance(arguments, dict) else {}
    tool = get_tool(tool_name)

    if tool is None:
        return {"found": 0, "items": [], "error": f"Unknown tool: {tool_name}"}

    if tool.handler is None:
        return {"found": 0, "items": [], "error": f"Tool handler not bound: {tool_name}"}

    # Permission check (sxdevops pattern)
    if tool.permission and user:
        user_perms = user.get("permissions", []) if isinstance(user, dict) else []
        if user_perms and tool.permission not in user_perms:
            return {"found": 0, "items": [], "error": "Forbidden: insufficient permissions"}

    query = str(arguments.get("query") or "").strip()
    limit = max(1, min(int(arguments.get("limit") or 10), 20))

    try:
        # Build kwargs based on what the handler accepts
        result = await tool.handler(
            query=query,
            limit=limit,
            **{k: v for k, v in arguments.items() if k not in ("query", "limit")},
        )
        return result
    except Exception:
        logger.exception("MCP tool %s failed", tool_name)
        return {"found": 0, "items": [], "error": "Tool execution failed"}


def build_mcp_tool_definitions() -> list[dict]:
    """Build OpenAI function-calling compatible tool definitions.

    Returns a list of tool definitions suitable for the LLM 'tools' parameter.
    """
    from app.modules.module8_aiops.tools.registry import ToolRegistry

    definitions = []
    for spec_dict in ToolRegistry.list_all():
        definitions.append({
            "type": "function",
            "function": {
                "name": spec_dict["name"],
                "description": spec_dict["description"],
                "parameters": spec_dict["inputSchema"],
            },
        })
    return definitions


# ═══════════════════════════════════════════════════════════════
# LLM Call Wrapper
# ═══════════════════════════════════════════════════════════════

async def _request_model_completion(
    messages: list[dict],
    tools: list[dict] | None = None,
    db_session=None,
) -> dict:
    """Send a chat completion request to the active LLM provider.

    Args:
        messages: OpenAI-format message list
        tools: Optional function-calling tool definitions
        db_session: Optional DB session (creates new if None)

    Returns:
        Dict with content, tool_calls, tokens, cost, error
    """
    if db_session is None:
        from app.core.database.session import async_session_factory
        db = async_session_factory()
        own_db = True
    else:
        db = db_session
        own_db = False

    try:
        if own_db:
            async with db as session:
                config = await get_agent_config(session)
                provider = await get_active_provider(session, config)
        else:
            config = await get_agent_config(db)
            provider = await get_active_provider(db, config)

        if provider is None:
            return {"content": "", "tool_calls": None, "error": "No LLM provider configured"}

        from app.modules.module8_aiops.llm.providers import create_provider_from_config

        llm = create_provider_from_config({
            "provider_type": provider.provider_type,
            "base_url": provider.base_url,
            "api_key_encrypted": provider.api_key_encrypted or "",
            "default_model": provider.default_model,
            "input_price": float(provider.input_price or 0),
            "output_price": float(provider.output_price or 0),
        })

        result = await llm.chat(messages=messages, tools=tools, stream=False)

        return {
            "content": result.content or "",
            "tool_calls": result.tool_calls,
            "prompt_tokens": result.prompt_tokens,
            "completion_tokens": result.completion_tokens,
            "estimated_cost": result.estimated_cost,
            "finish_reason": result.finish_reason,
            "error": None,
        }

    except Exception:
        logger.exception("LLM completion failed")
        return {"content": "", "tool_calls": None, "error": "LLM request failed"}
    finally:
        if own_db:
            pass  # context manager handles cleanup


# ═══════════════════════════════════════════════════════════════
# Chat Planning & Dispatch
# ═══════════════════════════════════════════════════════════════

async def _llm_chat_planning(
    user_input: str,
    user: dict,
    session_id: str = "",
) -> dict:
    """Use LLM to plan the response — select tools, analyze intent.

    Returns a dict with:
        intent: "tool_call" | "chat"
        tool_name: selected tool name (if tool_call)
        tool_args: arguments for the tool
        direct_answer: fallback answer if no tool needed
    """
    system_prompt = (
        "You are an AIOps intelligent assistant. Your job is to analyze the user's "
        "question and decide whether to call a platform tool or answer directly.\n\n"
        "Rules:\n"
        "1. If the question asks about devices, alerts, logs, IP addresses, subnets, "
        "topology, services, or knowledge articles, you MUST call the appropriate tool.\n"
        "2. If the question is a simple greeting or general inquiry, answer directly.\n"
        "3. Never make up data — always use tools for factual queries.\n"
        "4. Use Chinese when the user uses Chinese."
    )

    tool_defs = build_mcp_tool_definitions()

    # If no tools registered, fall through to direct chat
    if not tool_defs:
        return {"intent": "chat", "direct_answer": None}

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
    ]

    result = await _request_model_completion(messages=messages, tools=tool_defs)

    if result.get("error"):
        return {"intent": "chat", "direct_answer": None}

    tool_calls = result.get("tool_calls")
    if tool_calls and len(tool_calls) > 0:
        tc = tool_calls[0]
        tool_name = tc.get("name", "")
        try:
            import json
            tool_args = json.loads(tc.get("arguments", "{}"))
        except (json.JSONDecodeError, TypeError):
            tool_args = {"query": user_input}

        return {
            "intent": "tool_call",
            "tool_name": tool_name,
            "tool_args": tool_args,
            "direct_answer": None,
        }

    # No tool call — LLM chose to answer directly
    return {
        "intent": "chat",
        "direct_answer": result.get("content") or None,
    }


async def dispatch_chat(
    user_input: str,
    user: dict,
    session_id: str = "",
) -> dict:
    """Full chat dispatch pipeline (sxdevops pattern).

    Flow: planning → tool execution → response formatting

    Returns a dict with:
        content: final Markdown-formatted answer
        steps: list of processing steps
        tool_events: list of tool invocation summaries
        total_tokens: total LLM tokens used
        total_cost: estimated cost
        pending_action: any action requiring confirmation
    """
    steps: list[dict] = []
    tool_events: list[dict] = []
    total_tokens = 0
    total_cost = 0.0

    # Step 1: LLM Planning
    steps.append({"title": "Analyzing intent", "status": "running"})
    plan = await _llm_chat_planning(user_input, user, session_id)
    steps[-1]["status"] = "completed"

    intent = plan.get("intent", "chat")

    # Step 2: Execute tool if needed
    tool_result = None
    if intent == "tool_call":
        tool_name = plan.get("tool_name", "")
        tool_args = plan.get("tool_args", {})
        steps.append({"title": f"Calling {tool_name}", "status": "running"})

        import time as _time
        _t0 = _time.time()
        try:
            tool_result = await invoke_platform_mcp_tool(tool_name, tool_args, user)
            _latency = int((_time.time() - _t0) * 1000)
            found = tool_result.get("found", 0) if tool_result else 0
            tool_events.append({
                "name": tool_name,
                "detail": f"Found {found} results",
                "status": "success",
            })
            steps[-1]["status"] = "completed"
            # Audit: record tool invocation
            await record_tool_invocation(
                session_id=session_id,
                tool_name=tool_name,
                input_params=tool_args,
                output_summary=f"Found {found} results"[:500],
                latency_ms=_latency,
                status="success",
            )
        except Exception:
            _latency = int((_time.time() - _t0) * 1000)
            logger.exception("Tool %s failed in dispatch", tool_name)
            tool_events.append({
                "name": tool_name,
                "detail": "Tool execution failed",
                "status": "error",
            })
            steps[-1]["status"] = "failed"
            tool_result = {"found": 0, "items": [], "error": "Tool execution failed"}
            await record_tool_invocation(
                session_id=session_id,
                tool_name=tool_name,
                input_params=tool_args,
                output_summary="Tool execution failed",
                latency_ms=_latency,
                status="failed",
            )

    # Step 3: Format response
    steps.append({"title": "Generating response", "status": "running"})

    if intent == "chat" and plan.get("direct_answer"):
        # LLM already gave a direct answer, use it
        content = plan["direct_answer"]
    elif tool_result:
        # Format tool results
        content = _format_tool_result_for_display(user_input, tool_result)
    else:
        # Fallback: ask LLM to format tool results or answer directly
        content = _format_tool_result_for_display(user_input, tool_result or {"found": 0, "items": []})

    steps[-1]["status"] = "completed"

    return {
        "content": content,
        "steps": steps,
        "tool_events": tool_events,
        "pending_action": None,
        "total_tokens": total_tokens,
        "total_cost": total_cost,
    }


def _format_tool_result_for_display(user_input: str, tool_result: dict) -> str:
    """Format tool results into a Markdown response string."""
    if tool_result.get("error"):
        return f"查询时遇到问题：{tool_result['error']}"

    found = tool_result.get("found", 0)
    items = tool_result.get("items", [])
    returned = tool_result.get("returned", len(items))

    lines = [f"根据查询结果（共 {found} 条，显示前 {returned} 条）：\n"]

    for i, item in enumerate(items[:10], 1):
        if "title" in item:
            # Alert or article
            severity = item.get("severity", "")
            status = item.get("status", "")
            tags = f" [{severity}]" if severity else ""
            tags += f" ({status})" if status else ""
            lines.append(f"{i}. **{item['title']}**{tags}")
        elif "name" in item:
            # Device or service
            dev_type = item.get("type", "")
            ip = item.get("ip", "")
            info = f" ({dev_type})" if dev_type else ""
            info += f" - IP: {ip}" if ip else ""
            lines.append(f"{i}. **{item['name']}**{info}")
        elif "cidr" in item:
            # Subnet
            used = item.get("used_ips", 0)
            total = item.get("total_ips", 0)
            lines.append(f"{i}. **{item['cidr']}** - {used}/{total} IPs used")
        elif "message" in item:
            # Log entry
            sev = item.get("severity", "")
            host = item.get("hostname", "")
            msg = item.get("message", "")[:100]
            lines.append(f"{i}. [{sev}] {host}: {msg}")
        else:
            # Generic
            lines.append(f"{i}. {json.dumps(item, ensure_ascii=False, default=str)[:200]}")

    return "\n".join(lines)


import json as _json


# ═══════════════════════════════════════════════════════════════
# Audit Recording
# ═══════════════════════════════════════════════════════════════

async def record_tool_invocation(
    session_id: str,
    tool_name: str,
    input_params: dict | None = None,
    output_summary: str = "",
    latency_ms: int = 0,
    status: str = "success",
    message_id: str | None = None,
):
    """Record a tool invocation for audit trail."""
    import uuid as _uuid
    async with async_session_factory() as db:
        inv = AIOpsToolInvocation(
            session_id=_uuid.UUID(session_id) if session_id else _uuid.uuid4(),
            message_id=_uuid.UUID(message_id) if message_id else None,
            tool_name=tool_name,
            input_params=input_params or {},
            output_summary=output_summary[:500],
            latency_ms=latency_ms,
            status=status,
        )
        db.add(inv)
        await db.commit()


async def record_model_invocation(
    session_id: str,
    model_name: str,
    purpose: str = "reasoning",
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    total_cost: float = 0.0,
    latency_ms: int = 0,
    message_id: str | None = None,
):
    """Record a model invocation for audit trail."""
    import uuid as _uuid
    async with async_session_factory() as db:
        inv = AIOpsModelInvocation(
            session_id=_uuid.UUID(session_id) if session_id else _uuid.uuid4(),
            message_id=_uuid.UUID(message_id) if message_id else None,
            model_name=model_name,
            purpose=purpose,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_cost=total_cost,
            latency_ms=latency_ms,
        )
        db.add(inv)
        await db.commit()


async def get_audit_overview(db_session=None) -> dict:
    """Return audit overview statistics."""
    if db_session is None:
        db = async_session_factory()
        own_db = True
    else:
        db = db_session
        own_db = False

    try:
        if own_db:
            async with db as session:
                return await _get_audit_overview(session)
        else:
            return await _get_audit_overview(db)
    finally:
        pass


async def _get_audit_overview(db) -> dict:
    from sqlalchemy import func

    # Session count
    session_count = (await db.execute(
        select(func.count(AIOpsChatSession.id))
    )).scalar() or 0

    # Tool invocation count
    tool_count = (await db.execute(
        select(func.count(AIOpsToolInvocation.id))
    )).scalar() or 0

    # Model invocation count
    model_count = (await db.execute(
        select(func.count(AIOpsModelInvocation.id))
    )).scalar() or 0

    # Total cost
    total_cost = (await db.execute(
        select(func.sum(AIOpsModelInvocation.total_cost))
    )).scalar() or 0.0

    return {
        "total_sessions": session_count,
        "total_tool_invocations": tool_count,
        "total_model_invocations": model_count,
        "total_cost": float(total_cost),
    }


async def get_audit_costs(db_session=None) -> dict:
    """Return cost breakdown by model."""
    if db_session is None:
        db = async_session_factory()
        own_db = True
    else:
        db = db_session
        own_db = False

    try:
        if own_db:
            async with db as session:
                return await _get_audit_costs(session)
        else:
            return await _get_audit_costs(db)
    finally:
        pass


async def _get_audit_costs(db) -> dict:
    from sqlalchemy import func

    rows = (await db.execute(
        select(
            AIOpsModelInvocation.model_name,
            func.count(AIOpsModelInvocation.id),
            func.sum(AIOpsModelInvocation.prompt_tokens),
            func.sum(AIOpsModelInvocation.completion_tokens),
            func.sum(AIOpsModelInvocation.total_cost),
        ).group_by(AIOpsModelInvocation.model_name)
    )).all()

    items = []
    for row in rows:
        items.append({
            "model_name": row[0],
            "invocations": row[1],
            "total_prompt_tokens": row[2] or 0,
            "total_completion_tokens": row[3] or 0,
            "total_cost": float(row[4] or 0),
        })

    return {"items": items}
