"""M8 AI Engine — Data Access Layer."""
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.module8_ai.models import (
    AgentLLMCall, AgentPendingAction, AgentPreflightLog,
    AgentSession, AgentToolCall, AIOpsSkill,
    ChatMessage, ChatSession,
)


class AgentSessionRepository:
    def __init__(self, session: AsyncSession):
        self._s = session

    async def create(self, data: dict) -> AgentSession:
        obj = AgentSession(**data)
        self._s.add(obj)
        await self._s.commit()
        await self._s.refresh(obj)
        return obj

    async def get(self, sid: UUID) -> AgentSession | None:
        return await self._s.get(AgentSession, sid)

    async def update(self, obj: AgentSession, data: dict):
        for k, v in data.items():
            if v is not None:
                setattr(obj, k, v)
        await self._s.commit()

    async def list_by_user(self, user_id: str, page: int, page_size: int) -> tuple[int, list[AgentSession]]:
        q = select(AgentSession).where(AgentSession.user_id == user_id).order_by(AgentSession.started_at.desc())
        cq = select(func.count(AgentSession.id)).where(AgentSession.user_id == user_id)
        total = (await self._s.execute(cq)).scalar() or 0
        rows = (await self._s.execute(q.offset((page - 1) * page_size).limit(page_size))).scalars().all()
        return total, list(rows)


class ToolCallRepository:
    def __init__(self, session: AsyncSession):
        self._s = session

    async def create(self, data: dict) -> AgentToolCall:
        obj = AgentToolCall(**data)
        self._s.add(obj)
        await self._s.commit()
        return obj

    async def list_by_session(self, session_id: UUID) -> list[AgentToolCall]:
        q = select(AgentToolCall).where(AgentToolCall.session_id == session_id).order_by(AgentToolCall.step_number)
        rows = (await self._s.execute(q)).scalars().all()
        return list(rows)


class LLMCallRepository:
    def __init__(self, session: AsyncSession):
        self._s = session

    async def create(self, data: dict) -> AgentLLMCall:
        obj = AgentLLMCall(**data)
        self._s.add(obj)
        await self._s.commit()
        return obj

    async def list_by_session(self, session_id: UUID) -> list[AgentLLMCall]:
        q = select(AgentLLMCall).where(AgentLLMCall.session_id == session_id).order_by(AgentLLMCall.created_at)
        rows = (await self._s.execute(q)).scalars().all()
        return list(rows)


class PreflightLogRepository:
    def __init__(self, session: AsyncSession):
        self._s = session

    async def create(self, data: dict) -> AgentPreflightLog:
        obj = AgentPreflightLog(**data)
        self._s.add(obj)
        await self._s.commit()
        return obj

    async def list_by_session(self, session_id: UUID) -> list[AgentPreflightLog]:
        q = select(AgentPreflightLog).where(AgentPreflightLog.session_id == session_id)
        rows = (await self._s.execute(q)).scalars().all()
        return list(rows)


class PendingActionRepository:
    def __init__(self, session: AsyncSession):
        self._s = session

    async def create(self, data: dict) -> AgentPendingAction:
        obj = AgentPendingAction(**data)
        self._s.add(obj)
        await self._s.commit()
        return obj

    async def list_by_session(self, session_id: UUID) -> list[AgentPendingAction]:
        q = select(AgentPendingAction).where(AgentPendingAction.session_id == session_id)
        rows = (await self._s.execute(q)).scalars().all()
        return list(rows)


class SkillRepository:
    def __init__(self, session: AsyncSession):
        self._s = session

    async def ensure_skill(self, skill_data: dict) -> AIOpsSkill:
        q = select(AIOpsSkill).where(AIOpsSkill.skill_id == skill_data["skill_id"])
        existing = (await self._s.execute(q)).scalar_one_or_none()
        if existing:
            for k, v in skill_data.items():
                setattr(existing, k, v)
            await self._s.commit()
            return existing
        obj = AIOpsSkill(**skill_data)
        self._s.add(obj)
        await self._s.commit()
        await self._s.refresh(obj)
        return obj

    async def get_by_skill_id(self, skill_id: str) -> AIOpsSkill | None:
        q = select(AIOpsSkill).where(AIOpsSkill.skill_id == skill_id)
        return (await self._s.execute(q)).scalar_one_or_none()

    async def list_all(self, category: str | None = None) -> list[AIOpsSkill]:
        q = select(AIOpsSkill).where(AIOpsSkill.is_enabled == True).order_by(AIOpsSkill.category, AIOpsSkill.name)
        if category:
            q = q.where(AIOpsSkill.category == category)
        rows = (await self._s.execute(q)).scalars().all()
        return list(rows)


class ChatSessionRepository:
    def __init__(self, session: AsyncSession):
        self._s = session

    async def create(self, data: dict) -> ChatSession:
        obj = ChatSession(**data)
        self._s.add(obj)
        await self._s.commit()
        await self._s.refresh(obj)
        return obj

    async def get(self, sid: UUID) -> ChatSession | None:
        return await self._s.get(ChatSession, sid)

    async def update(self, obj: ChatSession, data: dict):
        for k, v in data.items():
            if v is not None:
                setattr(obj, k, v)
        await self._s.commit()

    async def delete(self, obj: ChatSession):
        await self._s.delete(obj)
        await self._s.commit()

    async def list_by_user(self, user_id: str, page: int, page_size: int) -> tuple[int, list[ChatSession]]:
        q = select(ChatSession).where(ChatSession.user_id == user_id).order_by(ChatSession.updated_at.desc())
        cq = select(func.count(ChatSession.id)).where(ChatSession.user_id == user_id)
        total = (await self._s.execute(cq)).scalar() or 0
        rows = (await self._s.execute(q.offset((page - 1) * page_size).limit(page_size))).scalars().all()
        return total, list(rows)


class ChatMessageRepository:
    def __init__(self, session: AsyncSession):
        self._s = session

    async def create(self, data: dict) -> ChatMessage:
        obj = ChatMessage(**data)
        self._s.add(obj)
        await self._s.commit()
        return obj

    async def list_by_session(self, session_id: UUID) -> list[ChatMessage]:
        q = select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.sequence)
        rows = (await self._s.execute(q)).scalars().all()
        return list(rows)

    async def get_max_sequence(self, session_id: UUID) -> int:
        q = select(func.max(ChatMessage.sequence)).where(ChatMessage.session_id == session_id)
        return (await self._s.execute(q)).scalar() or 0
