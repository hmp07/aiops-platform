"""M6 APM — Data Access Layer."""
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.module6_apm.models import APMService, CrossLayerMapping, ServiceEdge


class ServiceRepository:
    def __init__(self, session: AsyncSession): self._s = session
    async def create(self, data: dict) -> APMService:
        obj = APMService(**data); self._s.add(obj); await self._s.commit(); await self._s.refresh(obj); return obj
    async def get_by_id(self, sid: UUID) -> APMService | None: return await self._s.get(APMService, sid)
    async def list_all(self, page, page_size) -> tuple[int, list[APMService]]:
        q = select(APMService).order_by(APMService.created_at.desc()); cq = select(func.count(APMService.id))
        total = (await self._s.execute(cq)).scalar() or 0
        rows = (await self._s.execute(q.offset((page - 1) * page_size).limit(page_size))).scalars().all()
        return total, list(rows)
    async def update(self, obj: APMService, data: dict) -> APMService:
        for k, v in data.items():
            if v is not None: setattr(obj, k, v)
        await self._s.commit(); await self._s.refresh(obj); return obj


class EdgeRepository:
    def __init__(self, session: AsyncSession): self._s = session
    async def create(self, data: dict) -> ServiceEdge:
        obj = ServiceEdge(**data); self._s.add(obj); await self._s.commit(); await self._s.refresh(obj); return obj
    async def list_all(self) -> list[ServiceEdge]:
        q = select(ServiceEdge).order_by(ServiceEdge.created_at.desc())
        rows = (await self._s.execute(q)).scalars().all(); return list(rows)


class CrossLayerRepository:
    def __init__(self, session: AsyncSession): self._s = session
    async def create(self, data: dict) -> CrossLayerMapping:
        obj = CrossLayerMapping(**data); self._s.add(obj); await self._s.commit(); await self._s.refresh(obj); return obj
    async def get_by_service(self, service_id: UUID) -> CrossLayerMapping | None:
        q = select(CrossLayerMapping).where(CrossLayerMapping.service_id == service_id)
        result = await self._s.execute(q); return result.scalar_one_or_none()
