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
# ═══════════════════════════════════════════════════════════════
# Runtime Prompt & Tool Registry
# ═══════════════════════════════════════════════════════════════

DEFAULT_RUNTIME_PROMPT = (
    "你是 AIOps 平台内的智能运维助手。"
    "必须优先通过可用的 MCP 工具获取平台内结构化数据，严禁编造不存在的资源、告警、日志和执行结果。"
    "回答时区分事实、推断和建议；涉及执行类动作时，未确认前只能生成草稿。"
)


def _build_runtime_prompt(
    config: AIOpsAgentConfig | None = None,
    action: dict | None = None,
) -> str:
    """Build the system prompt with tool schemas, skill SOP, and action context.

    This is the Phase 1 prompt — focused on tool selection and fact-finding.
    """
    parts = [config.system_prompt if (config and config.system_prompt) else DEFAULT_RUNTIME_PROMPT]

    # Add available MCP tools summary
    from app.modules.module8_aiops.tools.registry import ToolRegistry
    tool_names = [t["name"] for t in ToolRegistry.list_all()]
    if tool_names:
        parts.append(f"\n可用平台工具: {', '.join(tool_names)}")

    # Add action context if matched
    if action:
        parts.append(f"\n当前 Action: {action.get('display_name') or action.get('code')}")
        parts.append(f"Agent 模式: {action.get('agent_mode_display', action.get('agent_mode', 'direct'))}")
        parts.append(f"可用工具: {', '.join(action.get('allowed_tools', []))}")
        if action.get("description"):
            parts.append(f"Action 描述: {action['description']}")

    # Add Skill SOP content for matched skills
    # (Skills will be loaded from DB in P3; for now, inject builtin content)
    skill_slugs = action.get("skills", []) if action else []
    if skill_slugs:
        parts.append("\n适用 Skill 的 SOP 指引:")
        for slug in skill_slugs:
            sop = _get_skill_sop_content(slug)
            if sop:
                parts.append(f"\n--- Skill: {slug} ---\n{sop}")

    # Constraints
    parts.append("\n约束:")
    parts.append("- 必须通过工具获取数据，不得编造")
    parts.append("- 使用中文回答")
    parts.append("- 区分事实与推断")
    if action and action.get("risk_level") != RISK_READ_ONLY:
        parts.append("- 高风险操作仅生成草稿，需用户确认后执行")

    return "\n".join(parts)


def _get_skill_sop_content(slug: str) -> str:
    """Get SOP content for a builtin skill slug (will be DB-backed in P3)."""
    sops = {
        "answer-formatter": (
            "适用场景：所有回答的格式化输出。\n"
            "输出要求：先给结论，再列依据，最后给出建议操作。"
            "使用结构化格式：结论/依据/建议操作。不能脱离工具事实自由发挥。"
        ),
        "alert-evidence-checklist": (
            "适用场景：告警根因、告警风险、告警影响范围分析。\n"
            "取证顺序：1. 查询告警详情 2. 关联设备信息 3. 检查拓扑依赖 4. 关联日志证据。\n"
            "判断要求：结论必须区分事实、推断和待验证假设。根因只能基于工具事实给出置信度。"
        ),
        "log-pattern-analysis": (
            "适用场景：日志查询、日志聚合、日志异常模式解释。\n"
            "查询规范：1. 按时间窗口过滤 2. 按服务/设备分组 3. 按错误级别排序。\n"
            "输出要求：明确查询条件、命中概览、错误模式分类和后续建议。"
        ),
        "topology-impact": (
            "适用场景：服务拓扑和依赖关系分析、故障影响范围评估。\n"
            "取证顺序：1. 查询服务拓扑 2. 识别关键依赖 3. 分析故障爆炸半径。\n"
            "输出要求：明确受影响的服务节点、依赖链路和恢复优先级。"
        ),
        "change-risk-assessment": (
            "适用场景：配置变更审查和风险评估。\n"
            "取证顺序：1. 查询配置差异 2. 识别高危关键词 3. 评估影响范围。\n"
            "判断要求：基于差异内容和风险模式给出等级评估，提供回滚建议。"
        ),
    }
    return sops.get(slug, "")


def _build_runtime_tool_registry() -> tuple[list[dict], dict]:
    """Build LLM-facing tool definitions and a handler lookup map.

    Returns:
        (tools_list, handler_map)
        tools_list: OpenAI function-calling format tool definitions
        handler_map: {tool_name: handler_name} for dispatch
    """
    from app.modules.module8_aiops.tools.registry import ToolRegistry

    tools = []
    handler_map = {}

    for spec_dict in ToolRegistry.list_all():
        tools.append({
            "type": "function",
            "function": {
                "name": spec_dict["name"],
                "description": spec_dict.get("description", ""),
                "parameters": spec_dict.get("inputSchema", {"type": "object", "properties": {}}),
            },
        })
        handler_map[spec_dict["name"]] = spec_dict["name"]

    return tools, handler_map


# ═══════════════════════════════════════════════════════════════
# Agent Mode Execution Strategies
# ═══════════════════════════════════════════════════════════════

async def _execute_direct_mode(
    user_input: str,
    user: dict,
    action: dict,
    messages: list[dict],
    tools: list[dict],
    handler_map: dict,
    session_id: str = "",
    max_iterations: int = 3,
) -> dict:
    """Direct mode: single LLM call with tool results inline.

    For simple queries where one tool call should resolve the question.
    """
    tool_results = []
    tool_calls_made = []
    sections = []
    citations = []
    total_tokens = 0
    total_cost = 0.0

    for _round in range(max(1, max_iterations)):
        result = await _request_model_completion(messages=messages, tools=tools)

        if result.get("error"):
            break

        total_tokens += result.get("prompt_tokens", 0) + result.get("completion_tokens", 0)
        total_cost += result.get("estimated_cost", 0.0)

        tc_list = result.get("tool_calls")
        if not tc_list:
            # LLM gave final answer
            return {
                "content": result.get("content", ""),
                "sections": sections,
                "citations": citations,
                "tool_calls": tool_calls_made,
                "tool_results": tool_results,
                "total_tokens": total_tokens,
                "total_cost": total_cost,
            }

        # Execute tools
        for tc in tc_list:
            tool_name = tc.get("name", "")
            try:
                args = json.loads(tc.get("arguments", "{}"))
            except (json.JSONDecodeError, TypeError):
                args = {"query": user_input}

            import time as _time
            _t0 = _time.time()
            try:
                tr = await invoke_platform_mcp_tool(tool_name, args, user)
                _latency = int((_time.time() - _t0) * 1000)
                tool_calls_made.append(tool_name)
                tool_results.append({"tool": tool_name, "result": tr})
                sections.append({
                    "title": tool_name,
                    "items": [f"Found {tr.get('found', 0)} results"],
                })
                await record_tool_invocation(
                    session_id=session_id, tool_name=tool_name,
                    input_params=args, latency_ms=_latency,
                    output_summary=f"Found {tr.get('found', 0)} results",
                    status="success",
                )
                # Append tool result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.get("id", f"call_{_round}"),
                    "content": json.dumps(tr, ensure_ascii=False, default=str)[:2000],
                })
            except Exception:
                logger.exception("Direct mode tool %s failed", tool_name)

    # Format results if no final answer from LLM
    return {
        "content": "",
        "sections": sections,
        "citations": citations,
        "tool_calls": tool_calls_made,
        "tool_results": tool_results,
        "total_tokens": total_tokens,
        "total_cost": total_cost,
    }


async def _execute_react_mode(
    user_input: str,
    user: dict,
    action: dict,
    messages: list[dict],
    tools: list[dict],
    handler_map: dict,
    session_id: str = "",
    max_iterations: int = 5,
) -> dict:
    """ReAct mode: reasoning-action-observation loop.

    LLM iteratively calls tools, observes results, and decides next steps.
    """
    tool_results = []
    tool_calls_made = []
    sections = []
    citations = []
    total_tokens = 0
    total_cost = 0.0

    for round_idx in range(max_iterations):
        result = await _request_model_completion(messages=messages, tools=tools)

        if result.get("error"):
            break

        total_tokens += result.get("prompt_tokens", 0) + result.get("completion_tokens", 0)
        total_cost += result.get("estimated_cost", 0.0)

        tc_list = result.get("tool_calls")
        if not tc_list:
            return {
                "content": result.get("content", ""),
                "sections": sections,
                "citations": citations,
                "tool_calls": tool_calls_made,
                "tool_results": tool_results,
                "total_tokens": total_tokens,
                "total_cost": total_cost,
            }

        # Append assistant message (with tool_calls) to history
        assistant_msg = {"role": "assistant", "content": result.get("content") or ""}
        if tc_list:
            assistant_msg["tool_calls"] = tc_list
        messages.append(assistant_msg)

        for tc in tc_list:
            tool_name = tc.get("name", "")
            try:
                args = json.loads(tc.get("arguments", "{}"))
            except (json.JSONDecodeError, TypeError):
                args = {"query": user_input}

            import time as _time
            _t0 = _time.time()
            try:
                tr = await invoke_platform_mcp_tool(tool_name, args, user)
                _latency = int((_time.time() - _t0) * 1000)
                tool_calls_made.append(tool_name)
                tool_results.append({"tool": tool_name, "result": tr})
                found = tr.get("found", 0) if tr else 0
                sections.append({"title": f"Round {round_idx+1}: {tool_name}", "items": [f"Found {found} results"]})
                await record_tool_invocation(
                    session_id=session_id, tool_name=tool_name,
                    input_params=args, latency_ms=_latency,
                    output_summary=f"Found {found} results", status="success",
                )
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.get("id", f"call_{round_idx}"),
                    "content": json.dumps(tr, ensure_ascii=False, default=str)[:2000],
                })
            except Exception:
                logger.exception("ReAct tool %s failed in round %d", tool_name, round_idx)

    # Max iterations reached — return collected results
    return {
        "content": "",
        "sections": sections,
        "citations": citations,
        "tool_calls": tool_calls_made,
        "tool_results": tool_results,
        "total_tokens": total_tokens,
        "total_cost": total_cost,
    }


# ═══════════════════════════════════════════════════════════════
# Main Dispatch Engine (sxdevops: _dispatch_with_tool_runtime)
# ═══════════════════════════════════════════════════════════════

async def _dispatch_with_tool_runtime(
    user_input: str,
    user: dict,
    session_id: str = "",
    page_context: dict | None = None,
) -> dict:
    """Phase 1: LLM tool planning + MCP execution.

    sxdevops-style dispatch: action routing → preflight → tool registry → ReAct loop.
    """
    # Load config
    async with async_session_factory() as db:
        config = await get_agent_config(db)

    # Select action
    action = _select_action_for_question(user_input, page_context)

    # Build tool registry
    tools, handler_map = _build_runtime_tool_registry()

    # Build system prompt
    system_prompt = _build_runtime_prompt(config, action)

    # Build messages
    messages = [
        {"role": "system", "content": system_prompt},
    ]

    # Add page context hints if available
    if page_context:
        from app.modules.module8_aiops.action_handlers import (
            build_prompt_hint_lines, normalize_page_context,
        )
        ctx = normalize_page_context(page_context)
        hint_lines = build_prompt_hint_lines(action, ctx)
        if hint_lines:
            messages.append({
                "role": "system",
                "content": "页面上下文提示:\n" + "\n".join(hint_lines),
            })

    messages.append({"role": "user", "content": user_input})

    # Get agent mode and max iterations from action
    agent_mode = action.get("agent_mode", AGENT_MODE_DIRECT) if action else AGENT_MODE_DIRECT
    max_iterations = 5 if agent_mode == AGENT_MODE_PLAN_REACT else (3 if agent_mode == AGENT_MODE_REACT else 1)

    # Execute based on agent mode
    if agent_mode == AGENT_MODE_PLAN_REACT:
        # Plan first, then ReAct
        plan_result = await _request_model_completion(
            messages=messages + [{
                "role": "user",
                "content": "请先制定分析计划（列出需要查询的步骤），然后逐步执行。",
            }],
            tools=tools,
        )
        if plan_result.get("content"):
            messages.append({"role": "assistant", "content": f"分析计划: {plan_result['content']}"})

        result = await _execute_react_mode(
            user_input, user, action, messages, tools, handler_map,
            session_id, max_iterations,
        )
    elif agent_mode == AGENT_MODE_REACT:
        result = await _execute_react_mode(
            user_input, user, action, messages, tools, handler_map,
            session_id, max_iterations,
        )
    else:
        result = await _execute_direct_mode(
            user_input, user, action, messages, tools, handler_map,
            session_id, max_iterations,
        )

    result["action"] = action
    result["agent_mode"] = agent_mode
    result["skill_trace"] = _build_skill_trace(action, result.get("tool_calls", []))
    return result


# ═══════════════════════════════════════════════════════════════
# Phase 2: Answer Formatter + Code Fallback
# ═══════════════════════════════════════════════════════════════

def _build_fallback_answer(
    user_input: str,
    tool_results: list[dict],
    action: dict | None = None,
) -> str:
    """Build a deterministic fallback answer from tool results.

    This is the code fallback draft — always available, never hallucinates.
    """
    if not tool_results:
        return "未能获取到平台数据，请确认数据源配置正确后重试。"

    lines = ["## 查询结果\n"]
    for tr in tool_results:
        tool_name = tr.get("tool", "unknown")
        result = tr.get("result", {})
        found = result.get("found", 0)
        items = result.get("items", [])

        lines.append(f"### {tool_name}（共 {found} 条）\n")

        for i, item in enumerate(items[:10], 1):
            if "name" in item:
                extra = f" ({item.get('type', '')})" if item.get("type") else ""
                extra += f" - IP: {item.get('ip', '')}" if item.get("ip") else ""
                lines.append(f"{i}. **{item['name']}**{extra}")
            elif "title" in item:
                sev = f" [{item.get('severity', '')}]" if item.get("severity") else ""
                lines.append(f"{i}. **{item['title']}**{sev}")
            elif "cidr" in item:
                lines.append(f"{i}. **{item['cidr']}** - {item.get('used_ips', 0)}/{item.get('total_ips', 0)} IPs")
            elif "message" in item:
                lines.append(f"{i}. [{item.get('severity', '')}] {item.get('hostname', '')}: {item.get('message', '')[:100]}")
            else:
                lines.append(f"{i}. {json.dumps(item, ensure_ascii=False, default=str)[:200]}")

    # Add structured sections if action has output_contract
    if action and action.get("output_blocks"):
        lines.append("\n---\n")
        lines.append("**结论**：基于以上平台数据，请参考具体条目。\n")
        lines.append("**依据**：以上数据均来自平台工具查询结果。\n")
        lines.append("**建议操作**：如有异常项，建议进一步排查相关设备和告警。")

    return "\n".join(lines)


async def _run_answer_formatter(
    user_input: str,
    dispatch_result: dict,
    action: dict | None = None,
) -> str:
    """Phase 2: Format tool results into a structured answer.

    Build code fallback, then optionally call LLM to format.
    Falls back to code draft if LLM fails or returns empty/invalid.
    """
    tool_results = dispatch_result.get("tool_results", [])

    # 1. Build code fallback (always available)
    fallback = _build_fallback_answer(user_input, tool_results, action)

    # 2. Try LLM formatting (if no tool results, just use fallback)
    if not tool_results:
        return fallback

    # Build formatter messages
    formatter_messages = [
        {
            "role": "system",
            "content": (
                "你是 AIOps 答案整形器。根据工具查询结果整理结构化回答。\n"
                "要求：\n"
                "1. 仅使用工具返回的数据，不得编造\n"
                "2. 使用「结论 / 依据 / 建议操作」结构\n"
                "3. 明确指出证据不足的情况\n"
                "4. 区分事实、推断和假设\n"
            ),
        },
        {
            "role": "user",
            "content": (
                f"用户问题: {user_input}\n\n"
                f"工具结果:\n{json.dumps(tool_results, ensure_ascii=False, default=str)[:3000]}\n\n"
                f"请基于以上工具结果，输出结构化的运维分析回答。"
            ),
        },
    ]

    try:
        fmt_result = await _request_model_completion(messages=formatter_messages, tools=None)

        content = (fmt_result.get("content") or "").strip()

        # Quality gate
        if not content or len(content) < 20:
            logger.warning("Formatter returned empty/short content, using fallback")
            return fallback

        # Check for required sections
        has_structure = any(
            section in content
            for section in ["结论", "依据", "建议", "##", "###"]
        )
        if not has_structure and len(tool_results) > 0:
            # Append fallback sections
            content = content + "\n\n---\n**数据依据**: " + fallback[:500]

        return content

    except Exception:
        logger.exception("Answer formatter failed, using fallback")
        return fallback


def _build_skill_trace(
    action: dict | None = None,
    tool_calls: list[str] | None = None,
) -> dict:
    """Build skill trace for audit/observability."""
    tool_calls = tool_calls or []
    skill_slugs = action.get("skills", []) if action else []

    items = []
    for slug in skill_slugs:
        status = "available"
        if slug == "answer-formatter":
            status = "called"
        items.append({"slug": slug, "status": status})

    return {
        "enabled_count": len(skill_slugs),
        "matched_count": len(skill_slugs),
        "called_count": len([i for i in items if i["status"] == "called"]),
        "items": items,
    }


# ═══════════════════════════════════════════════════════════════
# Action Selection (deterministic, pre-LLM)
# ═══════════════════════════════════════════════════════════════

def _select_action_for_question(
    question: str,
    page_context: dict | None = None,
) -> dict | None:
    """Select the best action based on question keywords + page context.

    Deterministic routing — no LLM involved. Returns BUILTIN_ACTION_REGISTRY entry.
    """
    lowered = question.lower()

    # Keyword → action code mapping
    keyword_map = [
        (["告警", "根因", "alert", "报警", "异常告警"], "alert.root_cause"),
        (["日志", "log", "error", "warn"], "log.analyze"),
        (["拓扑", "topology", "依赖", "dependency", "服务拓扑"], "topology.analyze"),
        (["配置", "config", "变更", "备份", "版本差异"], "config.review"),
        (["知识", "knowledge", "sop", "runbook", "文档", "预案"], "knowledge.search"),
        (["设备", "device", "server", "服务器", "资产", "ip", "子网"], "device.query"),
    ]

    # First pass: check page context
    if page_context:
        from app.modules.module8_aiops.action_handlers import (
            select_action_by_handler, normalize_page_context,
        )
        ctx = normalize_page_context(page_context)
        actions_by_code = {a["code"]: a for a in BUILTIN_ACTION_REGISTRY}
        handler_match = select_action_by_handler(question, actions_by_code, ctx)
        if handler_match:
            return handler_match

    # Second pass: keyword matching
    for keywords, action_code in keyword_map:
        if any(kw in lowered for kw in keywords):
            for action in BUILTIN_ACTION_REGISTRY:
                if action["code"] == action_code:
                    return dict(action)

    return None


# ═══════════════════════════════════════════════════════════════
# Main dispatch_chat — full pipeline
# ═══════════════════════════════════════════════════════════════

async def dispatch_chat(
    user_input: str,
    user: dict,
    session_id: str = "",
    page_context: dict | None = None,
) -> dict:
    """Full chat dispatch pipeline (sxdevops dual-phase architecture).

    Flow:
    1. Action Router (deterministic) → action code
    2. Phase 1: _dispatch_with_tool_runtime (LLM tool selection + MCP execution)
    3. Phase 2: _run_answer_formatter (LLM answer formatting + code fallback)
    4. Return: {content, steps, tool_events, citations, total_tokens, total_cost, pending_action}
    """
    steps: list[dict] = []
    tool_events: list[dict] = []

    # Step 1: Action routing
    steps.append({"title": "Analyzing question", "status": "completed"})

    # Step 2: Phase 1 — Tool dispatch
    steps.append({"title": "Executing tools", "status": "running"})
    try:
        dispatch_result = await _dispatch_with_tool_runtime(
            user_input, user, session_id, page_context,
        )
        steps[-1]["status"] = "completed"

        # Collect tool events
        for tr in dispatch_result.get("tool_results", []):
            found = tr.get("result", {}).get("found", 0)
            tool_events.append({
                "name": tr.get("tool", "unknown"),
                "detail": f"Found {found} results",
                "status": "success",
            })
    except Exception:
        logger.exception("Dispatch failed")
        dispatch_result = {"content": "", "tool_results": [], "tool_calls": [], "sections": []}
        steps[-1]["status"] = "failed"

    # Step 3: Phase 2 — Answer formatting
    steps.append({"title": "Formatting response", "status": "running"})
    action = dispatch_result.get("action")
    try:
        content = await _run_answer_formatter(
            user_input, dispatch_result, action,
        )
        steps[-1]["status"] = "completed"
    except Exception:
        logger.exception("Answer formatter failed")
        content = _build_fallback_answer(
            user_input,
            dispatch_result.get("tool_results", []),
            action,
        )
        steps[-1]["status"] = "completed"

    return {
        "content": content,
        "steps": steps,
        "tool_events": tool_events,
        "citations": [],
        "tool_calls": dispatch_result.get("tool_calls", []),
        "pending_action": None,
        "total_tokens": dispatch_result.get("total_tokens", 0),
        "total_cost": dispatch_result.get("total_cost", 0.0),
    }


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
