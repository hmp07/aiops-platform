"""M4 Log — Data Access Layer."""
from uuid import UUID
from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.module4_log.models import LogEntry, LogSource

class LogRepository:
    def __init__(self, s: AsyncSession): self._s = s
    async def create(self, data: dict) -> LogEntry:
        obj = LogEntry(**data); self._s.add(obj); await self._s.commit(); await self._s.refresh(obj); return obj
    async def list_all(self, page, page_size, device_id, severity, source, keyword) -> tuple[int, list[LogEntry]]:
        q = select(LogEntry); cq = select(func.count(LogEntry.id))
        if device_id: q = q.where(LogEntry.device_id == device_id); cq = cq.where(LogEntry.device_id == device_id)
        if severity: q = q.where(LogEntry.severity == severity); cq = cq.where(LogEntry.severity == severity)
        if source: q = q.where(LogEntry.source == source); cq = cq.where(LogEntry.source == source)
        if keyword:
            kw = f"%{keyword}%"
            f = or_(LogEntry.message.ilike(kw), LogEntry.hostname.ilike(kw))
            q = q.where(f); cq = cq.where(f)
        q = q.order_by(LogEntry.time.desc()).offset((page - 1) * page_size).limit(page_size)
        total = (await self._s.execute(cq)).scalar() or 0
        rows = (await self._s.execute(q)).scalars().all(); return total, list(rows)

class LogSourceRepository:
    def __init__(self, s: AsyncSession): self._s = s
    async def create(self, data: dict) -> LogSource:
        obj = LogSource(**data); self._s.add(obj); await self._s.commit(); await self._s.refresh(obj); return obj
    async def list_all(self) -> list[LogSource]:
        q = select(LogSource).order_by(LogSource.created_at.desc())
        rows = (await self._s.execute(q)).scalars().all(); return list(rows)
