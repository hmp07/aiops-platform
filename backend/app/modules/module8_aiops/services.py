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
        "action_registry": [],
        "action_registry_summary": None,
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
