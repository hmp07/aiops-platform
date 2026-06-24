from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.module10_eventwall.models import EventRecord, EventSource, FaultCluster


class EventRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, data: dict) -> EventRecord:
        event = EventRecord(**data)
        self._session.add(event)
        await self._session.commit()
        return event

    async def get_by_id(self, event_id: str) -> EventRecord | None:
        result = await self._session.execute(
            select(EventRecord).where(EventRecord.id == event_id)
        )
        return result.scalar_one_or_none()

    async def get_by_correlation(self, correlation_id: str) -> list[EventRecord]:
        result = await self._session.execute(
            select(EventRecord)
            .where(EventRecord.correlation_id == correlation_id)
            .order_by(EventRecord.timestamp.asc())
        )
        return list(result.scalars().all())

    async def query(
        self, page: int, page_size: int,
        event_type: str | None = None, source_module: str | None = None,
        resource_type: str | None = None, resource_id: str | None = None,
        correlation_id: str | None = None, fault_id: str | None = None,
        severity: str | None = None,
        start_time: str | None = None, end_time: str | None = None,
    ) -> tuple[int, list[EventRecord]]:
        query = select(EventRecord)
        count_query = select(func.count(EventRecord.id))

        filters = []
        if event_type: filters.append(EventRecord.event_type == event_type)
        if source_module: filters.append(EventRecord.source_module == source_module)
        if resource_type: filters.append(EventRecord.resource_type == resource_type)
        if resource_id: filters.append(EventRecord.resource_id == resource_id)
        if correlation_id: filters.append(EventRecord.correlation_id == correlation_id)
        if fault_id: filters.append(EventRecord.fault_id == fault_id)
        if severity: filters.append(EventRecord.severity == severity)
        if start_time: filters.append(EventRecord.timestamp >= start_time)
        if end_time: filters.append(EventRecord.timestamp <= end_time)

        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        query = query.order_by(EventRecord.timestamp.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        total = (await self._session.execute(count_query)).scalar() or 0
        result = await self._session.execute(query)
        return total, list(result.scalars().all())

    async def query_time_window(
        self, start: datetime, end: datetime
    ) -> list[EventRecord]:
        result = await self._session.execute(
            select(EventRecord)
            .where(and_(EventRecord.timestamp >= start, EventRecord.timestamp <= end))
            .order_by(EventRecord.timestamp.desc())
            .limit(500)
        )
        return list(result.scalars().all())


class FaultRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, data: dict) -> FaultCluster:
        fault = FaultCluster(**data)
        self._session.add(fault)
        await self._session.commit()
        return fault

    async def get_by_fault_id(self, fault_id: str) -> FaultCluster | None:
        result = await self._session.execute(
            select(FaultCluster).where(FaultCluster.fault_id == fault_id)
        )
        return result.scalar_one_or_none()

    async def list_faults(
        self, page: int, page_size: int, resolved: bool = False
    ) -> tuple[int, list[FaultCluster]]:
        query = select(FaultCluster)
        count_query = select(func.count(FaultCluster.id))
        if resolved:
            query = query.where(FaultCluster.resolved_at.isnot(None))
            count_query = count_query.where(FaultCluster.resolved_at.isnot(None))
        else:
            query = query.where(FaultCluster.resolved_at.is_(None))
            count_query = count_query.where(FaultCluster.resolved_at.is_(None))

        query = query.order_by(FaultCluster.score.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        total = (await self._session.execute(count_query)).scalar() or 0
        result = await self._session.execute(query)
        return total, list(result.scalars().all())

    async def resolve(self, fault_id: str):
        fault = await self.get_by_fault_id(fault_id)
        if fault:
            from datetime import datetime, timezone
            fault.resolved_at = datetime.now(timezone.utc)
            await self._session.commit()


class EventSourceRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, data: dict) -> EventSource:
        source = EventSource(**data)
        self._session.add(source)
        await self._session.commit()
        return source

    async def get_by_slug(self, slug: str) -> EventSource | None:
        result = await self._session.execute(
            select(EventSource).where(EventSource.slug == slug)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[EventSource]:
        result = await self._session.execute(select(EventSource).order_by(EventSource.name))
        return list(result.scalars().all())
