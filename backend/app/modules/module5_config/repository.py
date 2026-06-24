"""M5 Config — Data Access Layer."""
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.module5_config.models import BatchOperation, ConfigBackup, ConfigDiff


class BackupRepository:
    def __init__(self, session: AsyncSession):
        self._s = session

    async def create(self, data: dict) -> ConfigBackup:
        obj = ConfigBackup(**data)
        self._s.add(obj)
        await self._s.commit()
        await self._s.refresh(obj)
        return obj

    async def list_all(self, page: int, page_size: int,
                       device_id: UUID | None, status: str | None,
                       ) -> tuple[int, list[ConfigBackup]]:
        q = select(ConfigBackup)
        cq = select(func.count(ConfigBackup.id))
        if device_id:
            q = q.where(ConfigBackup.device_id == device_id)
            cq = cq.where(ConfigBackup.device_id == device_id)
        if status:
            q = q.where(ConfigBackup.status == status)
            cq = cq.where(ConfigBackup.status == status)
        q = q.order_by(ConfigBackup.backup_at.desc()).offset((page - 1) * page_size).limit(page_size)
        total = (await self._s.execute(cq)).scalar() or 0
        rows = (await self._s.execute(q)).scalars().all()
        return total, list(rows)


class DiffRepository:
    def __init__(self, session: AsyncSession):
        self._s = session

    async def create(self, data: dict) -> ConfigDiff:
        obj = ConfigDiff(**data)
        self._s.add(obj)
        await self._s.commit()
        await self._s.refresh(obj)
        return obj

    async def list_all(self, page: int, page_size: int,
                       device_id: UUID | None) -> tuple[int, list[ConfigDiff]]:
        q = select(ConfigDiff)
        cq = select(func.count(ConfigDiff.id))
        if device_id:
            q = q.where(ConfigDiff.device_id == device_id)
            cq = cq.where(ConfigDiff.device_id == device_id)
        q = q.order_by(ConfigDiff.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        total = (await self._s.execute(cq)).scalar() or 0
        rows = (await self._s.execute(q)).scalars().all()
        return total, list(rows)


class BatchRepository:
    def __init__(self, session: AsyncSession):
        self._s = session

    async def create(self, data: dict) -> BatchOperation:
        obj = BatchOperation(**data)
        self._s.add(obj)
        await self._s.commit()
        await self._s.refresh(obj)
        return obj
