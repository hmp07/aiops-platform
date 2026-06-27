"""M8 AIOps — Admin API endpoints (sxdevops architecture).

Agent config, MCP servers, Skills, Actions, Providers, Audit.
All endpoints require appropriate permissions.
"""

import logging
import uuid as _uuid

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy import select, func

from app.core.database.session import async_session_factory
from app.core.middleware.auth import get_current_user
from app.core.middleware.permissions import require_permission
from app.modules.module8_aiops.models import (
    AIOpsAgentConfig,
    AIOpsChatMessage,
    AIOpsChatSession,
    AIOpsMCPServer,
    AIOpsModelProvider,
    AIOpsModelInvocation,
    AIOpsPendingAction,
    AIOpsSkill,
    AIOpsToolInvocation,
)
from app.modules.module8_aiops import services as aiops_services

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/aiops/admin", tags=["AIOps Admin"])

_SENSITIVE_AUTH_KEYS = {"password", "token", "secret", "api_key", "bearer", "api_key_encrypted",
                          "service_account_token", "access_key", "secret_key"}


def _sanitize_auth_config(auth_config: dict | None) -> dict:
    """Strip sensitive values from auth_config before returning to clients."""
    if not isinstance(auth_config, dict):
        return {}
    return {
        k: ("***" if k.lower() in _SENSITIVE_AUTH_KEYS or any(s in k.lower() for s in ("token", "secret", "password", "key")) else v)
        for k, v in auth_config.items()
    }


# ═══════════════════════════════════════════════════════════════
# Agent Config
# ═══════════════════════════════════════════════════════════════

@router.get("/config")
async def get_agent_config(current_user: dict = Depends(get_current_user)):
    """Get the singleton agent configuration."""
    async with async_session_factory() as db:
        config = await aiops_services.get_agent_config(db)
        return {
            "id": str(config.id),
            "default_provider_id": str(config.default_provider_id) if config.default_provider_id else None,
            "system_prompt": config.system_prompt,
            "welcome_message": config.welcome_message,
            "suggested_questions": config.suggested_questions,
            "enabled_skill_ids": config.enabled_skill_ids,
            "enabled_mcp_server_ids": config.enabled_mcp_server_ids,
            "allow_action_execution": config.allow_action_execution,
            "require_confirmation": config.require_confirmation,
            "show_evidence": config.show_evidence,
            "max_history_messages": config.max_history_messages,
        }


@router.put("/config")
@require_permission("ai:provider:manage")
async def update_agent_config(
    body: dict = Body(...),
    current_user: dict = Depends(get_current_user),
):
    """Update the agent configuration."""
    async with async_session_factory() as db:
        config = await aiops_services.get_agent_config(db)

        updatable = [
            "default_provider_id", "system_prompt", "welcome_message",
            "suggested_questions", "enabled_skill_ids", "enabled_mcp_server_ids",
            "allow_action_execution", "require_confirmation", "show_evidence",
            "max_history_messages",
        ]
        for key in updatable:
            if key in body:
                val = body[key]
                if key == "default_provider_id" and val:
                    val = _uuid.UUID(val)
                setattr(config, key, val)

        await db.commit()
        await db.refresh(config)
        return {"status": "updated", "id": str(config.id)}


# ═══════════════════════════════════════════════════════════════
# Model Providers
# ═══════════════════════════════════════════════════════════════

@router.get("/providers/presets")
async def list_provider_presets(current_user: dict = Depends(get_current_user)):
    """List model provider presets (DeepSeek, GLM, Qwen, etc.)."""
    from app.modules.module8_aiops.llm.providers import PROVIDER_PRESETS
    return {"presets": [
        {"key": k, "name": {
            "deepseek": "DeepSeek", "zhipu": "智谱 GLM",
            "qwen": "通义千问", "openai_compatible": "OpenAI 兼容",
        }.get(k, k), **v}
        for k, v in PROVIDER_PRESETS.items()
    ]}


@router.post("/providers/{provider_id}/test_connection")
@require_permission("ai:provider:manage")
async def test_provider_connection(
    provider_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Test connectivity to a model provider."""
    async with async_session_factory() as db:
        obj = await db.get(AIOpsModelProvider, _uuid.UUID(provider_id))
        if not obj:
            return {"status": "error", "message": "Provider not found"}

        from app.modules.module8_aiops.llm.providers import create_provider_from_config
        llm = create_provider_from_config({
            "provider_type": obj.provider_type,
            "base_url": obj.base_url,
            "api_key_encrypted": obj.api_key_encrypted or "",
            "default_model": obj.default_model,
        })
        try:
            ok = await llm.health_check()
            return {"status": "ok" if ok else "failed", "message": "Connection test passed" if ok else "No response"}
        except Exception as e:
            return {"status": "failed", "message": str(e)[:200]}


@router.get("/providers/{provider_id}/models")
@require_permission("ai:provider:manage")
async def list_provider_models(
    provider_id: str,
    current_user: dict = Depends(get_current_user),
):
    """List available models from a provider."""
    async with async_session_factory() as db:
        obj = await db.get(AIOpsModelProvider, _uuid.UUID(provider_id))
        if not obj:
            return {"models": [], "error": "Provider not found"}

        from app.modules.module8_aiops.llm.providers import create_provider_from_config
        llm = create_provider_from_config({
            "provider_type": obj.provider_type,
            "base_url": obj.base_url,
            "api_key_encrypted": obj.api_key_encrypted or "",
            "default_model": obj.default_model,
        })
        try:
            models = await llm.list_models()
            return {"models": models}
        except Exception:
            return {"models": obj.models_list or []}


# ═══════════════════════════════════════════════════════════════
# MCP Servers
# ═══════════════════════════════════════════════════════════════

@router.get("/mcp-servers")
@require_permission("ai:analysis:view")
async def list_mcp_servers(current_user: dict = Depends(get_current_user)):
    """List all MCP servers."""
    async with async_session_factory() as db:
        rows = (await db.execute(
            select(AIOpsMCPServer).order_by(AIOpsMCPServer.created_at.desc())
        )).scalars().all()
        return {"items": [
            {
                "id": str(r.id), "name": r.name, "server_type": r.server_type,
                "endpoint_or_command": r.endpoint_or_command,
                "auth_config": _sanitize_auth_config(r.auth_config),
                "tool_whitelist": r.tool_whitelist, "is_enabled": r.is_enabled,
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ]}


@router.post("/mcp-servers", status_code=201)
@require_permission("ai:provider:manage")
async def create_mcp_server(
    body: dict = Body(...),
    current_user: dict = Depends(get_current_user),
):
    """Create a new MCP server."""
    async with async_session_factory() as db:
        obj = AIOpsMCPServer(
            name=body["name"],
            server_type=body.get("server_type", "http"),
            endpoint_or_command=body.get("endpoint_or_command", ""),
            auth_config=body.get("auth_config", {}),
            tool_whitelist=body.get("tool_whitelist", []),
            is_enabled=body.get("is_enabled", True),
        )
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return {"id": str(obj.id), "name": obj.name, "status": "created"}


@router.patch("/mcp-servers/{server_id}")
@require_permission("ai:provider:manage")
async def update_mcp_server(
    server_id: str,
    body: dict = Body(...),
    current_user: dict = Depends(get_current_user),
):
    """Update an MCP server."""
    async with async_session_factory() as db:
        obj = await db.get(AIOpsMCPServer, _uuid.UUID(server_id))
        if not obj:
            return {"status": "error", "message": "Not found"}
        for key in ["name", "server_type", "endpoint_or_command", "auth_config",
                     "tool_whitelist", "is_enabled"]:
            if key in body:
                setattr(obj, key, body[key])
        await db.commit()
        return {"status": "updated"}


@router.delete("/mcp-servers/{server_id}")
@require_permission("ai:provider:manage")
async def delete_mcp_server(
    server_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete an MCP server."""
    async with async_session_factory() as db:
        obj = await db.get(AIOpsMCPServer, _uuid.UUID(server_id))
        if obj:
            await db.delete(obj)
            await db.commit()
        return {"status": "deleted"}


@router.post("/mcp-servers/{server_id}/test_connection")
@require_permission("ai:provider:manage")
async def test_mcp_server(server_id: str, current_user: dict = Depends(get_current_user)):
    """Test connection to an external MCP server."""
    return {"status": "ok", "message": "MCP server connection test (not implemented for external servers yet)"}


@router.get("/mcp-servers/{server_id}/list_tools")
@require_permission("ai:analysis:view")
async def list_mcp_server_tools(server_id: str, current_user: dict = Depends(get_current_user)):
    """List tools from an MCP server (builtin platform tools)."""
    tools = aiops_services.list_platform_mcp_tools(current_user)
    return {"tools": tools}


# ═══════════════════════════════════════════════════════════════
# Skills
# ═══════════════════════════════════════════════════════════════

@router.get("/skills")
@require_permission("ai:skill:manage")
async def list_skills(current_user: dict = Depends(get_current_user)):
    """List all skills."""
    async with async_session_factory() as db:
        rows = (await db.execute(
            select(AIOpsSkill).where(AIOpsSkill.is_enabled == True).order_by(AIOpsSkill.created_at.desc())
        )).scalars().all()
        return {"items": [
            {
                "id": str(r.id), "slug": r.slug, "name": r.name, "description": r.description,
                "category": r.category, "risk_level": r.risk_level,
                "source_type": r.source_type, "is_builtin": r.is_builtin,
                "version": r.version, "applicable_actions": r.applicable_actions,
                "builtin_tools": r.builtin_tools, "recommended_tools": r.recommended_tools,
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ]}


@router.post("/skills", status_code=201)
@require_permission("ai:skill:manage")
async def create_skill(body: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Create a new skill."""
    async with async_session_factory() as db:
        obj = AIOpsSkill(
            slug=body["slug"],
            name=body["name"],
            description=body.get("description", ""),
            category=body.get("category", "diagnosis"),
            content=body.get("content", ""),
            output_contract=body.get("output_contract", {}),
            builtin_tools=body.get("builtin_tools", []),
            recommended_tools=body.get("recommended_tools", []),
            applicable_actions=body.get("applicable_actions", []),
            risk_level=body.get("risk_level", "read_only"),
            source_type=body.get("source_type", "inline"),
            is_enabled=body.get("is_enabled", True),
        )
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return {"id": str(obj.id), "slug": obj.slug, "status": "created"}


@router.patch("/skills/{skill_id}")
@require_permission("ai:skill:manage")
async def update_skill(skill_id: str, body: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Update a skill."""
    async with async_session_factory() as db:
        obj = await db.get(AIOpsSkill, _uuid.UUID(skill_id))
        if not obj:
            return {"status": "error", "message": "Not found"}
        updatable = ["name", "description", "category", "content", "output_contract",
                      "builtin_tools", "recommended_tools", "applicable_actions",
                      "risk_level", "is_enabled"]
        for key in updatable:
            if key in body:
                setattr(obj, key, body[key])
        await db.commit()
        return {"status": "updated"}


@router.delete("/skills/{skill_id}")
@require_permission("ai:skill:manage")
async def delete_skill(skill_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a skill."""
    async with async_session_factory() as db:
        obj = await db.get(AIOpsSkill, _uuid.UUID(skill_id))
        if obj and not obj.is_builtin:
            await db.delete(obj)
            await db.commit()
        return {"status": "deleted" if obj and not obj.is_builtin else "protected"}


@router.get("/skills/marketplace")
@require_permission("ai:skill:manage")
async def skill_marketplace(current_user: dict = Depends(get_current_user)):
    """Browse skill marketplace (builtin skills catalog)."""
    return {"categories": [
        {"name": "诊断", "slug": "diagnosis", "count": 2},
        {"name": "报告", "slug": "report", "count": 1},
        {"name": "咨询", "slug": "advisory", "count": 1},
    ]}


@router.post("/skills/{skill_id}/clone")
@require_permission("ai:skill:manage")
async def clone_skill(skill_id: str, body: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Clone a skill for team customization."""
    async with async_session_factory() as db:
        source = await db.get(AIOpsSkill, _uuid.UUID(skill_id))
        if not source:
            return {"status": "error", "message": "Source skill not found"}
        cloned = AIOpsSkill(
            slug=f"{source.slug}-clone-{_uuid.uuid4().hex[:6]}",
            name=body.get("name", f"{source.name} (副本)"),
            description=source.description,
            category=source.category,
            content=source.content,
            output_contract=source.output_contract,
            builtin_tools=source.builtin_tools,
            recommended_tools=source.recommended_tools,
            applicable_actions=source.applicable_actions,
            risk_level=source.risk_level,
            source_type="inline",
            is_builtin=False,
        )
        db.add(cloned)
        await db.commit()
        await db.refresh(cloned)
        return {"id": str(cloned.id), "slug": cloned.slug, "status": "cloned"}


# ═══════════════════════════════════════════════════════════════
# Actions Registry
# ═══════════════════════════════════════════════════════════════

@router.get("/actions")
async def action_registry(current_user: dict = Depends(get_current_user)):
    """Return the full action registry with handler details."""
    actions = aiops_services.list_action_registry(current_user)
    return {
        "actions": actions,
        "summary": aiops_services.build_action_registry_summary(actions),
    }


@router.post("/actions/preflight")
async def action_preflight(body: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Validate whether an action has all required context."""
    from app.modules.module8_aiops.action_handlers import build_context_form_block
    action_code = body.get("action_code", "")
    page_context = body.get("page_context", {})
    actions = aiops_services.list_action_registry()
    action = next((a for a in actions if a["code"] == action_code), None)
    if not action:
        return {"status": "error", "message": f"Unknown action: {action_code}"}
    missing = body.get("missing_fields", [])
    form_block = build_context_form_block(action, missing, page_context)
    return {"status": "ok", "action": action_code, "form_block": form_block}


# ═══════════════════════════════════════════════════════════════
# Audit
# ═══════════════════════════════════════════════════════════════

@router.get("/audit/overview")
@require_permission("ai:audit:view")
async def audit_overview(current_user: dict = Depends(get_current_user)):
    """Audit dashboard overview."""
    return await aiops_services.get_audit_overview()


@router.get("/audit/costs")
@require_permission("ai:audit:view")
async def audit_costs(current_user: dict = Depends(get_current_user)):
    """Model cost breakdown."""
    return await aiops_services.get_audit_costs()


@router.get("/audit/sessions")
@require_permission("ai:audit:view")
async def audit_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """List auditable chat sessions."""
    async with async_session_factory() as db:
        total = (await db.execute(select(func.count(AIOpsChatSession.id)))).scalar() or 0
        rows = (await db.execute(
            select(AIOpsChatSession)
            .order_by(AIOpsChatSession.updated_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )).scalars().all()
        return {
            "total": total,
            "items": [
                {"id": str(r.id), "user_id": r.user_id, "title": r.title,
                 "message_count": r.message_count, "last_message_at": r.last_message_at.isoformat() if r.last_message_at else None,
                 "created_at": r.created_at.isoformat()}
                for r in rows
            ],
        }


@router.delete("/audit/sessions/{session_id}")
@require_permission("ai:audit:manage")
async def delete_audit_session(session_id: str, current_user: dict = Depends(get_current_user)):
    """Delete an audit session."""
    async with async_session_factory() as db:
        obj = await db.get(AIOpsChatSession, _uuid.UUID(session_id))
        if obj:
            await db.delete(obj)
            await db.commit()
        return {"status": "deleted"}


@router.post("/audit/sessions/bulk-delete")
@require_permission("ai:audit:manage")
async def bulk_delete_audit_sessions(body: dict = Body(...), current_user: dict = Depends(get_current_user)):
    """Bulk delete audit sessions."""
    ids = body.get("session_ids", [])
    async with async_session_factory() as db:
        for sid in ids:
            obj = await db.get(AIOpsChatSession, _uuid.UUID(sid))
            if obj:
                await db.delete(obj)
        await db.commit()
    return {"status": "deleted", "count": len(ids)}


@router.get("/audit/tool-invocations")
@require_permission("ai:audit:view")
async def audit_tool_invocations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """List tool invocation audit records."""
    async with async_session_factory() as db:
        total = (await db.execute(select(func.count(AIOpsToolInvocation.id)))).scalar() or 0
        rows = (await db.execute(
            select(AIOpsToolInvocation)
            .order_by(AIOpsToolInvocation.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )).scalars().all()
        return {
            "total": total,
            "items": [
                {"id": str(r.id), "session_id": str(r.session_id), "tool_name": r.tool_name,
                 "input_params": r.input_params, "output_summary": r.output_summary,
                 "latency_ms": r.latency_ms, "status": r.status, "created_at": r.created_at.isoformat()}
                for r in rows
            ],
        }


@router.get("/audit/model-invocations")
@require_permission("ai:audit:view")
async def audit_model_invocations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """List model invocation audit records."""
    async with async_session_factory() as db:
        total = (await db.execute(select(func.count(AIOpsModelInvocation.id)))).scalar() or 0
        rows = (await db.execute(
            select(AIOpsModelInvocation)
            .order_by(AIOpsModelInvocation.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )).scalars().all()
        return {
            "total": total,
            "items": [
                {"id": str(r.id), "session_id": str(r.session_id), "model_name": r.model_name,
                 "purpose": r.purpose, "prompt_tokens": r.prompt_tokens,
                 "completion_tokens": r.completion_tokens, "total_cost": r.total_cost,
                 "latency_ms": r.latency_ms, "created_at": r.created_at.isoformat()}
                for r in rows
            ],
        }


@router.get("/audit/actions")
@require_permission("ai:audit:view")
async def audit_actions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """List pending action audit records."""
    async with async_session_factory() as db:
        total = (await db.execute(select(func.count(AIOpsPendingAction.id)))).scalar() or 0
        rows = (await db.execute(
            select(AIOpsPendingAction)
            .order_by(AIOpsPendingAction.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )).scalars().all()
        return {
            "total": total,
            "items": [
                {"id": str(r.id), "session_id": str(r.session_id), "user_id": r.user_id,
                 "action_type": r.action_type, "title": r.title, "risk_level": r.risk_level,
                 "status": r.status, "created_at": r.created_at.isoformat()}
                for r in rows
            ],
        }
