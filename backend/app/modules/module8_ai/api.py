"""M8 AI Engine — API Endpoints (SSE + CRUD + Skills + Audit)."""
import json
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.session import get_db
from app.core.middleware.auth import get_current_user
from app.core.middleware.permissions import require_permission
from app.modules.module8_ai.repository import (
    AgentSessionRepository, ChatMessageRepository, ChatSessionRepository,
    LLMCallRepository, PendingActionRepository, PreflightLogRepository,
    SkillRepository, ToolCallRepository,
)
from app.modules.module8_ai.schemas import (
    ActionConfirmRequest, ActionRejectRequest,
    ChatMessageListResponse, ChatMessageSend,
    ChatSessionCreate, ChatSessionListResponse, ChatSessionResponse,
    SkillResponse, SkillUpdate, SuggestionsResponse,
    AgentAuditTrailResponse,
)
from app.modules.module8_ai.service import AgentService, SkillService

router = APIRouter(prefix="/ai", tags=["AI Engine"])


# ---- Dependency Injection ----
def _get_agent_service(db: AsyncSession = Depends(get_db)) -> AgentService:
    return AgentService(
        ChatSessionRepository(db), ChatMessageRepository(db),
        AgentSessionRepository(db), ToolCallRepository(db),
        LLMCallRepository(db), PreflightLogRepository(db),
        PendingActionRepository(db), SkillRepository(db),
    )


def _get_skill_service(db: AsyncSession = Depends(get_db)) -> SkillService:
    return SkillService(SkillRepository(db))


# ============================================================
# Chat Sessions
# ============================================================

@router.get("/sessions", response_model=ChatSessionListResponse)
async def list_sessions(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=50),
    user: dict = Depends(get_current_user),
    svc: AgentService = Depends(_get_agent_service),
):
    total, items = await svc.list_sessions(user["user_id"], page, page_size)
    return ChatSessionListResponse(total=total, items=items)


@router.post("/sessions", response_model=ChatSessionResponse, status_code=201)
async def create_session(
    req: ChatSessionCreate,
    user: dict = Depends(get_current_user),
    svc: AgentService = Depends(_get_agent_service),
):
    return await svc.create_session(user, req.title, req.context_page, req.context_resource)


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_session(
    session_id: UUID,
    user: dict = Depends(get_current_user),
    svc: AgentService = Depends(_get_agent_service),
):
    return await svc.get_session(session_id, user["user_id"])


@router.post("/sessions/{session_id}/delete")
async def delete_session(
    session_id: UUID,
    user: dict = Depends(get_current_user),
    svc: AgentService = Depends(_get_agent_service),
):
    await svc.delete_session(session_id, user["user_id"])
    return {"status": "deleted", "session_id": str(session_id)}


# ============================================================
# Messages (SSE Stream)
# ============================================================

@router.get("/sessions/{session_id}/messages", response_model=ChatMessageListResponse)
async def get_messages(
    session_id: UUID,
    user: dict = Depends(get_current_user),
    svc: AgentService = Depends(_get_agent_service),
):
    items = await svc.get_messages(session_id, user["user_id"])
    return ChatMessageListResponse(items=items)


@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: UUID,
    req: ChatMessageSend,
    user: dict = Depends(get_current_user),
    svc: AgentService = Depends(_get_agent_service),
):
    """Main SSE streaming endpoint for agent chat."""
    async def event_stream():
        async for sse_event in svc.send_message(
            session_id, req.content, user, req.skill_id, req.analysis_only,
        ):
            yield sse_event

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ============================================================
# Pending Actions
# ============================================================

@router.post("/actions/{action_id}/confirm")
async def confirm_action(
    action_id: UUID,
    _body: ActionConfirmRequest = None,
    user: dict = Depends(get_current_user),
    svc: AgentService = Depends(_get_agent_service),
):
    await svc.confirm_action(action_id, user["user_id"])
    return {"status": "approved"}


@router.post("/actions/{action_id}/reject")
async def reject_action(
    action_id: UUID,
    body: ActionRejectRequest = ActionRejectRequest(),
    user: dict = Depends(get_current_user),
    svc: AgentService = Depends(_get_agent_service),
):
    await svc.reject_action(action_id, user["user_id"], body.reason)
    return {"status": "rejected"}


# ============================================================
# Suggestions
# ============================================================

@router.get("/suggestions", response_model=SuggestionsResponse)
async def get_suggestions(
    page: str = Query("default"),
    _: dict = Depends(get_current_user),
    svc: AgentService = Depends(_get_agent_service),
):
    suggestions = await svc.get_suggestions(page)
    return SuggestionsResponse(suggestions=suggestions, page=page)


# ============================================================
# Skills
# ============================================================

@router.get("/skills", response_model=list[SkillResponse])
async def list_skills(
    category: str | None = None,
    _: dict = Depends(get_current_user),
    svc: SkillService = Depends(_get_skill_service),
):
    return await svc.list_skills(category)


@router.post("/skills/{skill_id}/update", response_model=SkillResponse)
async def update_skill(
    skill_id: str,
    req: SkillUpdate,
    _: dict = Depends(get_current_user),
    svc: SkillService = Depends(_get_skill_service),
):
    return await svc.update_skill(skill_id, req.model_dump(exclude_none=True))


# ============================================================
# Model Providers
# ============================================================

@router.get("/models")
async def list_model_providers(
    _: dict = Depends(get_current_user),
):
    """List configured LLM model providers."""
    from app.core.database.session import async_session_factory
    from app.modules.module8_ai.models import ModelProvider
    from sqlalchemy import select

    async with async_session_factory() as db:
        rows = (await db.execute(
            select(ModelProvider).order_by(ModelProvider.created_at.desc())
        )).scalars().all()
        return {
            "total": len(rows),
            "items": [
                {"id": str(r.id), "name": r.name, "provider_type": r.provider_type,
                 "base_url": r.base_url, "default_model": r.default_model,
                 "backup_model": r.backup_model, "models_list": r.models_list,
                 "is_enabled": r.is_enabled, "created_at": r.created_at.isoformat()}
                for r in rows
            ],
        }


def _validate_base_url(url: str) -> bool:
    """Reject private/loopback/link-local URLs to prevent SSRF."""
    from urllib.parse import urlparse
    import ipaddress, socket

    host = urlparse(url).hostname
    if not host:
        return False
    try:
        for addr in socket.getaddrinfo(host, None):
            ip = ipaddress.ip_address(addr[4][0])
            if ip.is_loopback or ip.is_private or ip.is_link_local:
                return False
    except socket.gaierror:
        return False
    return True


@router.post("/models", status_code=201)
async def create_model_provider(
    body: dict,
    _: dict = Depends(get_current_user),
):
    """Add a new LLM provider configuration."""
    from app.core.database.session import async_session_factory
    from app.modules.module8_ai.models import ModelProvider

    if not _validate_base_url(body.get("base_url", "")):
        return {"status": "error", "message": "Invalid or unsafe base_url"}

    async with async_session_factory() as db:
        obj = ModelProvider(
            name=body["name"],
            provider_type=body.get("provider_type", "openai_compatible"),
            base_url=body["base_url"],
            api_key_encrypted=body.get("api_key_encrypted", ""),
            default_model=body.get("default_model", ""),
            backup_model=body.get("backup_model"),
            models_list=body.get("models_list", []),
            input_price=body.get("input_price", 0.0),
            output_price=body.get("output_price", 0.0),
        )
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return {"id": str(obj.id), "name": obj.name, "status": "created"}


@router.post("/models/{provider_id}/test")
async def test_model_provider(
    provider_id: UUID,
    _: dict = Depends(get_current_user),
):
    """Test connectivity to a model provider."""
    from app.core.database.session import async_session_factory
    from app.modules.module8_ai.models import ModelProvider
    from app.modules.module8_ai.llm.providers import create_provider_from_config
    from sqlalchemy import select

    async with async_session_factory() as db:
        row = (await db.execute(
            select(ModelProvider).where(ModelProvider.id == provider_id)
        )).scalar_one_or_none()
        if not row:
            return {"status": "error", "message": "Provider not found"}

        provider = create_provider_from_config({
            "provider_type": row.provider_type,
            "base_url": row.base_url,
            "api_key_encrypted": row.api_key_encrypted,
            "default_model": row.default_model,
            "input_price": row.input_price,
            "output_price": row.output_price,
        })
        ok = await provider.health_check()
        return {"status": "ok" if ok else "error",
                "message": "Ping successful" if ok else "Connection failed"}


@router.post("/models/{provider_id}/delete")
async def delete_model_provider(
    provider_id: UUID,
    _: dict = Depends(get_current_user),
):
    """Delete a model provider configuration."""
    from app.core.database.session import async_session_factory
    from app.modules.module8_ai.models import ModelProvider
    from sqlalchemy import select

    async with async_session_factory() as db:
        row = (await db.execute(
            select(ModelProvider).where(ModelProvider.id == provider_id)
        )).scalar_one_or_none()
        if not row:
            return {"status": "error", "message": "Not found"}
        await db.delete(row)
        await db.commit()
        return {"status": "deleted"}


# ============================================================
# Provider Presets (built-in model provider templates)
# ============================================================

@router.get("/models/presets")
async def list_presets(_: dict = Depends(get_current_user)):
    """List built-in model provider presets."""
    from app.modules.module8_ai.llm.providers import PROVIDER_PRESETS

    return {
        "presets": [
            {"type": k, "base_url": v["base_url"], "default_model": v["default_model"],
             "models": v["models"], "input_price": v["input_price"], "output_price": v["output_price"]}
            for k, v in PROVIDER_PRESETS.items()
        ],
    }


# ============================================================
# Agent Profiles
# ============================================================

@router.get("/agents")
async def list_agent_profiles(_: dict = Depends(get_current_user)):
    from app.core.database.session import async_session_factory
    from app.modules.module8_ai.models import AgentProfile
    from sqlalchemy import select

    async with async_session_factory() as db:
        rows = (await db.execute(
            select(AgentProfile).where(AgentProfile.is_enabled == True)
        )).scalars().all()
        return {
            "items": [
                {"agent_id": r.agent_id, "name": r.name, "description": r.description,
                 "allowed_skills": r.allowed_skills, "default_mode": r.default_mode,
                 "icon": r.icon, "suggested_questions": r.suggested_questions}
                for r in rows
            ],
        }


# ============================================================
# Audit
# ============================================================

@router.get("/sessions/{session_id}/audit", response_model=AgentAuditTrailResponse)
async def get_audit_trail(
    session_id: UUID,
    _: dict = Depends(get_current_user),
    svc: AgentService = Depends(_get_agent_service),
):
    return await svc.get_audit_trail(session_id)
