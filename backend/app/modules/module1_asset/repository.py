"""M1 Asset — Data Access Layer."""
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.module1_asset.models import CalibrationReport, Device


class DeviceRepository:
    def __init__(self, session: AsyncSession):
        self._s = session

    async def create(self, data: dict) -> Device:
        obj = Device(**data)
        self._s.add(obj)
        await self._s.commit()
        await self._s.refresh(obj)
        return obj

    async def get_by_id(self, device_id: UUID) -> Device | None:
        return await self._s.get(Device, device_id)

    async def find_by_ip(self, ip: str) -> Device | None:
        q = select(Device).where(Device.management_ip == ip).where(Device.deleted_at.is_(None))
        result = await self._s.execute(q)
        return result.scalar_one_or_none()

    async def list_devices(
        self, page: int, page_size: int, device_type: str | None,
        vendor: str | None, lifecycle_status: str | None, keyword: str | None,
    ) -> tuple[int, list[Device]]:
        q = select(Device).where(Device.deleted_at.is_(None))
        cq = select(func.count(Device.id)).where(Device.deleted_at.is_(None))

        if device_type:
            q = q.where(Device.device_type == device_type)
            cq = cq.where(Device.device_type == device_type)
        if vendor:
            q = q.where(Device.vendor == vendor)
            cq = cq.where(Device.vendor == vendor)
        if lifecycle_status:
            q = q.where(Device.lifecycle_status == lifecycle_status)
            cq = cq.where(Device.lifecycle_status == lifecycle_status)
        if keyword:
            kw_filter = or_(
                Device.device_name.ilike(f"%{keyword}%"),
                Device.management_ip.cast(str).ilike(f"%{keyword}%"),
                Device.model.ilike(f"%{keyword}%"),
            )
            q = q.where(kw_filter)
            cq = cq.where(kw_filter)

        q = q.order_by(Device.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        total = (await self._s.execute(cq)).scalar() or 0
        rows = (await self._s.execute(q)).scalars().all()
        return total, list(rows)

    async def update(self, obj: Device, data: dict) -> Device:
        for k, v in data.items():
            if v is not None:
                setattr(obj, k, v)
        await self._s.commit()
        await self._s.refresh(obj)
        return obj

    async def soft_delete(self, obj: Device):
        obj.deleted_at = datetime.now(timezone.utc)
        await self._s.commit()


class CalibrationRepository:
    def __init__(self, session: AsyncSession):
        self._s = session

    async def create(self, data: dict) -> CalibrationReport:
        obj = CalibrationReport(**data)
        self._s.add(obj)
        await self._s.commit()
        await self._s.refresh(obj)
        return obj

    async def get_by_id(self, report_id: UUID) -> CalibrationReport | None:
        return await self._s.get(CalibrationReport, report_id)

    async def list_reports(
        self, page: int, page_size: int, device_id: UUID | None, status: str | None,
    ) -> tuple[int, list[CalibrationReport]]:
        q = select(CalibrationReport)
        cq = select(func.count(CalibrationReport.id))
        if device_id:
            q = q.where(CalibrationReport.device_id == device_id)
            cq = cq.where(CalibrationReport.device_id == device_id)
        if status:
            q = q.where(CalibrationReport.status == status)
            cq = cq.where(CalibrationReport.status == status)
        q = q.order_by(CalibrationReport.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        total = (await self._s.execute(cq)).scalar() or 0
        rows = (await self._s.execute(q)).scalars().all()
        return total, list(rows)

    async def update(self, obj: CalibrationReport, data: dict) -> CalibrationReport:
        for k, v in data.items():
            if v is not None:
                setattr(obj, k, v)
        await self._s.commit()
        await self._s.refresh(obj)
        return obj
