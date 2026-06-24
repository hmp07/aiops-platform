"""M3 Monitoring — Data Access Layer."""
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.module3_monitoring.models import (
    Alert, AlertRule, EvidenceSnapshot, Metric,
    NotificationChannel, NotificationPolicy,
)


class AlertRepository:
    def __init__(self, session: AsyncSession): self._s = session

    async def create(self, data: dict) -> Alert:
        obj = Alert(**data); self._s.add(obj); await self._s.commit(); await self._s.refresh(obj); return obj

    async def get_by_id(self, aid: UUID) -> Alert | None: return await self._s.get(Alert, aid)

    async def list_all(self, page, page_size, severity, status, device_id, source) -> tuple[int, list[Alert]]:
        q = select(Alert); cq = select(func.count(Alert.id))
        if severity: q = q.where(Alert.severity == severity); cq = cq.where(Alert.severity == severity)
        if status: q = q.where(Alert.status == status); cq = cq.where(Alert.status == status)
        if device_id: q = q.where(Alert.device_id == device_id); cq = cq.where(Alert.device_id == device_id)
        if source: q = q.where(Alert.source == source); cq = cq.where(Alert.source == source)
        q = q.order_by(Alert.time.desc()).offset((page - 1) * page_size).limit(page_size)
        total = (await self._s.execute(cq)).scalar() or 0
        rows = (await self._s.execute(q)).scalars().all()
        return total, list(rows)

    async def find_recent(self, device_id: UUID, title_prefix: str, minutes: int = 5) -> Alert | None:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        q = select(Alert).where(
            Alert.device_id == device_id, Alert.title.ilike(f"{title_prefix}%"),
            Alert.time >= cutoff, Alert.status == "triggered",
        ).order_by(Alert.time.desc()).limit(1)
        result = await self._s.execute(q)
        return result.scalar_one_or_none()

    async def update(self, obj: Alert, data: dict) -> Alert:
        for k, v in data.items():
            if v is not None: setattr(obj, k, v)
        await self._s.commit(); await self._s.refresh(obj); return obj


class AlertRuleRepository:
    def __init__(self, session: AsyncSession): self._s = session
    async def create(self, data: dict) -> AlertRule:
        obj = AlertRule(**data); self._s.add(obj); await self._s.commit(); await self._s.refresh(obj); return obj
    async def get_by_id(self, rid: UUID) -> AlertRule | None: return await self._s.get(AlertRule, rid)
    async def list_all(self, page, page_size) -> tuple[int, list[AlertRule]]:
        q = select(AlertRule).order_by(AlertRule.created_at.desc()); cq = select(func.count(AlertRule.id))
        total = (await self._s.execute(cq)).scalar() or 0
        rows = (await self._s.execute(q.offset((page - 1) * page_size).limit(page_size))).scalars().all()
        return total, list(rows)
    async def update(self, obj: AlertRule, data: dict) -> AlertRule:
        for k, v in data.items():
            if v is not None: setattr(obj, k, v)
        await self._s.commit(); await self._s.refresh(obj); return obj
    async def delete(self, obj: AlertRule): await self._s.delete(obj); await self._s.commit()


class EvidenceRepository:
    def __init__(self, session: AsyncSession): self._s = session
    async def create(self, data: dict) -> EvidenceSnapshot:
        obj = EvidenceSnapshot(**data); self._s.add(obj); await self._s.commit(); await self._s.refresh(obj); return obj
    async def get_by_alert(self, alert_id: UUID) -> EvidenceSnapshot | None:
        q = select(EvidenceSnapshot).where(EvidenceSnapshot.alert_id == alert_id).order_by(EvidenceSnapshot.collected_at.desc()).limit(1)
        result = await self._s.execute(q); return result.scalar_one_or_none()


class ChannelRepository:
    def __init__(self, session: AsyncSession): self._s = session
    async def create(self, data: dict) -> NotificationChannel:
        obj = NotificationChannel(**data); self._s.add(obj); await self._s.commit(); await self._s.refresh(obj); return obj
    async def list_all(self) -> list[NotificationChannel]:
        q = select(NotificationChannel).order_by(NotificationChannel.created_at.desc())
        rows = (await self._s.execute(q)).scalars().all(); return list(rows)


class PolicyRepository:
    def __init__(self, session: AsyncSession): self._s = session
    async def create(self, data: dict) -> NotificationPolicy:
        obj = NotificationPolicy(**data); self._s.add(obj); await self._s.commit(); await self._s.refresh(obj); return obj
    async def list_all(self) -> list[NotificationPolicy]:
        q = select(NotificationPolicy).order_by(NotificationPolicy.created_at.desc())
        rows = (await self._s.execute(q)).scalars().all(); return list(rows)


class MetricRepository:
    def __init__(self, session: AsyncSession): self._s = session
    async def create(self, data: dict) -> Metric:
        obj = Metric(**data); self._s.add(obj); await self._s.commit(); await self._s.refresh(obj); return obj
    async def query(self, device_id: UUID, metric_name: str, limit: int = 100) -> list[Metric]:
        q = select(Metric).where(Metric.device_id == device_id, Metric.metric_name == metric_name).order_by(Metric.time.desc()).limit(limit)
        rows = (await self._s.execute(q)).scalars().all(); return list(rows)
