"""M11 — DataSource Repository."""
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.module11_scheduler.models import DataSource

class DataSourceRepository:
    def __init__(self, s: AsyncSession): self._s = s
    async def create(self, data: dict) -> DataSource:
        obj = DataSource(**data); self._s.add(obj); await self._s.commit(); await self._s.refresh(obj); return obj
    async def get_by_id(self, ds_id: UUID) -> DataSource | None: return await self._s.get(DataSource, ds_id)
    async def list_all(self) -> list[DataSource]:
        q = select(DataSource).order_by(DataSource.created_at.desc())
        rows = (await self._s.execute(q)).scalars().all(); return list(rows)
    async def update(self, obj: DataSource, data: dict) -> DataSource:
        for k, v in data.items():
            if v is not None: setattr(obj, k, v)
        await self._s.commit(); await self._s.refresh(obj); return obj
    async def delete(self, obj: DataSource): await self._s.delete(obj); await self._s.commit()
