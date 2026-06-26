"""M8 AIOps — API endpoints (sxdevops architecture).

Session & message endpoints. Admin endpoints are in admin_api.py.
Core business logic is in services.py.
"""
import asyncio
import json
import logging
import uuid as _uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.session import async_session_factory, get_db
from app.core.middleware.auth import get_current_user
from app.core.middleware.permissions import require_permission
from app.modules.module8_aiops.models import (
    AIOpsAgentConfig, AIOpsChatMessage, AIOpsChatSession,
    AIOpsModelProvider, AIOpsPendingAction, AIOpsSkill,
    AIOpsToolInvocation, AIOpsModelInvocation,
)
from app.modules.module8_aiops import services as aiops_services

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/aiops", tags=["AIOps"])

# ── helpers ──────────────────────────────────────────────────

def _now():
    return datetime.now(timezone.utc)


# ============================================================
# Bootstrap
# ============================================================

@router.get("/bootstrap")
async def get_bootstrap(current_user: dict = Depends(get_current_user)):
    """Return agent config, suggested questions, permissions (sxdevops pattern)."""
    async with async_session_factory() as db:
        return await aiops_services.bootstrap_payload_for_user(db, current_user)


# ============================================================
# Sessions
# ============================================================

@router.get("/sessions")
async def list_sessions(current_user: dict = Depends(get_current_user)):
    async with async_session_factory() as db:
        rows = (await db.execute(
            select(AIOpsChatSession)
            .where(AIOpsChatSession.user_id == current_user.get("user_id", ""))
            .order_by(AIOpsChatSession.updated_at.desc())
        )).scalars().all()
        return {
            "items": [
                {"id": str(r.id), "title": r.title, "message_count": r.message_count,
                 "last_message_at": r.last_message_at.isoformat() if r.last_message_at else None,
                 "created_at": r.created_at.isoformat()}
                for r in rows
            ],
        }


@router.post("/sessions", status_code=201)
async def create_session(body: dict = Body(...), current_user: dict = Depends(get_current_user)):
    async with async_session_factory() as db:
        sess = AIOpsChatSession(
            user_id=current_user.get("user_id", ""),
            title=body.get("title", "New Chat")[:256],
            context=body.get("context", {}),
        )
        db.add(sess)
        await db.commit()
        await db.refresh(sess)
        return {"id": str(sess.id), "title": sess.title, "created_at": sess.created_at.isoformat()}


@router.post("/sessions/{session_id}/delete_session")
async def delete_session(session_id: str, current_user: dict = Depends(get_current_user)):
    uid = current_user.get("user_id", "")
    async with async_session_factory() as db:
        obj = await db.get(AIOpsChatSession, _uuid.UUID(session_id))
        if obj and obj.user_id == uid:
            await db.delete(obj)
            await db.commit()
        return {"status": "deleted"}


# ============================================================
# Messages
# ============================================================

@router.get("/sessions/{session_id}/messages")
async def list_messages(session_id: str, current_user: dict = Depends(get_current_user)):
    """List messages. Does NOT trigger agent execution — use execute_pending for that."""
    uid = current_user.get("user_id", "")
    async with async_session_factory() as db:
        sess = await db.get(AIOpsChatSession, _uuid.UUID(session_id))
        if not sess or sess.user_id != uid:
            return {"items": [], "error": "session not found"}
        rows = (await db.execute(
            select(AIOpsChatMessage)
            .where(AIOpsChatMessage.session_id == _uuid.UUID(session_id))
            .order_by(AIOpsChatMessage.created_at.asc())
        )).scalars().all()
        return {"items": [
            {
                "id": str(r.id), "role": r.role, "content": r.content,
                "message_type": r.message_type,
                "processing_status": r.processing_status,
                "blocks": r.blocks, "citations": r.citations,
                "tool_calls": r.tool_calls,
                "pending_action_id": str(r.pending_action_id) if r.pending_action_id else None,
                "metadata": r.extra_meta if hasattr(r, 'extra_meta') else None,
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ]}


@router.post("/sessions/{session_id}/execute_pending")
async def execute_pending(session_id: str, current_user: dict = Depends(get_current_user)):
    """Execute the agent for any pending assistant message. Blocks until done."""
    uid = current_user.get("user_id", "")
    async with async_session_factory() as db:
        sid = _uuid.UUID(session_id)
        sess = await db.get(AIOpsChatSession, sid)
        if not sess or sess.user_id != uid:
            return {"status": "error", "message": "session not found"}
        rows = (await db.execute(
            select(AIOpsChatMessage).where(
                AIOpsChatMessage.session_id == sid,
                AIOpsChatMessage.role == "assistant",
                AIOpsChatMessage.processing_status == "pending",
            ).order_by(AIOpsChatMessage.created_at.desc()).limit(1)
        )).scalars().all()

        if not rows:
            return {"status": "no_pending"}

        msg = rows[0]
        # Find user message
        user_rows = (await db.execute(
            select(AIOpsChatMessage).where(
                AIOpsChatMessage.session_id == sid, AIOpsChatMessage.role == "user",
            ).order_by(AIOpsChatMessage.created_at.desc()).limit(1)
        )).scalars().all()
        user_input = user_rows[0].content if user_rows else ""

        # Mark running
        msg.processing_status = "running"
        msg.extra_meta = {"processing_text": "Analyzing..."}
        await db.commit()

        # Execute
        try:
            result = await _execute_agent_pipeline(user_input, current_user, str(session_id))
            msg.content = result.get("content", "")
            msg.processing_status = "completed"
            msg.extra_meta = {"processing_text": "Completed", "processing_steps": result.get("steps", []),
                               "tool_events": result.get("tool_events", [])}
        except Exception as e:
            logger.exception("Agent pipeline error in session %s", str(session_id))
            msg.content = "An internal error occurred while processing your request."
            msg.processing_status = "failed"
        await db.commit()

        return {"status": msg.processing_status, "content": msg.content[:500]}


# ============================================================
# Send Message Async (core — sxdevops pattern)
# ============================================================

@router.post("/sessions/{session_id}/send_message_async")
async def send_message_async(
    session_id: str,
    body: dict = Body(...),
    current_user: dict = Depends(get_current_user),
):
    """Async send: creates user + pending assistant message, returns immediately.

    Backend processes the agent flow in background, updating assistant message
    content + status. Frontend polls GET /messages until status=completed.
    """
    content = (body.get("content") or "").strip()[:8000]
    if not content:
        return {"error": "content required"}

    uid = current_user.get("user_id", "")
    async with async_session_factory() as db:
        sid = _uuid.UUID(session_id)
        sess = await db.get(AIOpsChatSession, sid)
        if not sess or sess.user_id != uid:
            return {"error": "session not found"}

        now = _now()

        # Save user message
        user_msg = AIOpsChatMessage(
            session_id=sid, role="user", content=content,
            created_at=now,
        )
        db.add(user_msg)

        # Create pending assistant message
        assistant_msg = AIOpsChatMessage(
            session_id=sid, role="assistant", content="",
            processing_status="pending",
            extra_meta={"processing_text": "Thinking..."},
            created_at=now,
        )
        db.add(assistant_msg)

        sess.message_count = (sess.message_count or 0) + 2
        sess.last_message_at = now
        await db.commit()
        await db.refresh(user_msg)
        await db.refresh(assistant_msg)

        uid = str(user_msg.id)
        aid = str(assistant_msg.id)

    # Messages created, return immediately. Agent runs on next poll.
    return {
        "user_message": {"id": uid, "role": "user", "content": content, "created_at": now.isoformat()},
        "assistant_message": {"id": aid, "role": "assistant", "content": "", "processing_status": "pending", "created_at": now.isoformat()},
    }


async def _execute_agent_pipeline(user_input: str, user: dict, session_id) -> dict:
    """Run the full Agent pipeline: planning → tool calls → response format.

    Delegates to services.dispatch_chat() (sxdevops architecture).
    """
    return await aiops_services.dispatch_chat(user_input, user, session_id)


# ============================================================
# Pending Actions
# ============================================================

@router.post("/actions/{action_id}/confirm")
async def confirm_action(action_id: str, current_user: dict = Depends(get_current_user)):
    uid = current_user.get("user_id", "")
    async with async_session_factory() as db:
        action = await db.get(AIOpsPendingAction, _uuid.UUID(action_id))
        if action and action.user_id == uid:
            action.status = "confirmed"
            action.decided_at = _now()
            action.decided_by = uid
            await db.commit()
        return {"status": "confirmed"}


@router.post("/actions/{action_id}/cancel")
async def cancel_action(action_id: str, current_user: dict = Depends(get_current_user)):
    uid = current_user.get("user_id", "")
    async with async_session_factory() as db:
        action = await db.get(AIOpsPendingAction, _uuid.UUID(action_id))
        if action and action.user_id == uid:
            action.status = "canceled"
            action.decided_at = _now()
            action.decided_by = uid
            await db.commit()
        return {"status": "canceled"}


# ============================================================
# Model Providers (admin)
# ============================================================

@router.get("/admin/providers")
@require_permission("aiops:provider:list")
async def list_providers(current_user: dict = Depends(get_current_user)):
    async with async_session_factory() as db:
        rows = (await db.execute(select(AIOpsModelProvider).order_by(AIOpsModelProvider.created_at.desc()))).scalars().all()
        return {"items": [
            {"id": str(r.id), "name": r.name, "provider_type": r.provider_type,
             "base_url": r.base_url, "default_model": r.default_model,
             "is_enabled": r.is_enabled, "created_at": r.created_at.isoformat()}
            for r in rows
        ]}


@router.post("/admin/providers", status_code=201)
@require_permission("aiops:provider:create")
async def create_provider(body: dict = Body(...), current_user: dict = Depends(get_current_user)):
    from app.modules.module8_ai.llm.providers import PROVIDER_PRESETS
    from urllib.parse import urlparse
    import ipaddress, socket

    # SSRF guard: reject private/loopback URLs
    base_url = body.get("base_url", "")
    host = urlparse(base_url).hostname
    if host:
        try:
            for addr in socket.getaddrinfo(host, None):
                ip = ipaddress.ip_address(addr[4][0])
                if ip.is_loopback or ip.is_private or ip.is_link_local:
                    return {"status": "error", "message": "Invalid or unsafe base_url"}
        except socket.gaierror:
            return {"status": "error", "message": "Cannot resolve base_url hostname"}

    preset = PROVIDER_PRESETS.get(body.get("provider_type", "openai_compatible"), {})
    async with async_session_factory() as db:
        obj = AIOpsModelProvider(
            name=body["name"],
            provider_type=body.get("provider_type", "openai_compatible"),
            base_url=body.get("base_url", preset.get("base_url", "")),
            api_key_encrypted=body.get("api_key_encrypted", ""),
            default_model=body.get("default_model", preset.get("default_model", "")),
            models_list=body.get("models_list", preset.get("models", [])),
            input_price=body.get("input_price", preset.get("input_price", 0)),
            output_price=body.get("output_price", preset.get("output_price", 0)),
        )
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return {"id": str(obj.id), "name": obj.name, "status": "created"}


# ============================================================
# Skills (admin)
# ============================================================

@router.get("/admin/skills")
@require_permission("aiops:skill:list")
async def list_skills(current_user: dict = Depends(get_current_user)):
    async with async_session_factory() as db:
        rows = (await db.execute(select(AIOpsSkill).where(AIOpsSkill.is_enabled == True))).scalars().all()
        return {"items": [
            {"id": str(r.id), "slug": r.slug, "name": r.name, "category": r.category,
             "risk_level": r.risk_level, "is_builtin": r.is_builtin}
            for r in rows
        ]}
