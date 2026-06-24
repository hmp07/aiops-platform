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
# Audit
# ============================================================

@router.get("/sessions/{session_id}/audit", response_model=AgentAuditTrailResponse)
async def get_audit_trail(
    session_id: UUID,
    _: dict = Depends(get_current_user),
    svc: AgentService = Depends(_get_agent_service),
):
    return await svc.get_audit_trail(session_id)
