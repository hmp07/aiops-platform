"""M8 AIOps — Core Services (sxdevops architecture, FastAPI adaptation).

All business logic lives here. API endpoints in api.py / admin_api.py are thin
routers that delegate to these functions.

Porting from: d:\projects\sxdevops\backend\aiops\services.py (~7400 lines)
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
        # Will be populated in later units
        "active_mcp_servers": [],
        "active_skills": [],
        "action_registry": [],
        "action_registry_summary": None,
    }
