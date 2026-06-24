"""M2 IPAM — Data Access Layer."""
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.module2_ipam.models import IPAllocation, Subnet


class SubnetRepository:
    def __init__(self, session: AsyncSession):
        self._s = session

    async def create(self, data: dict) -> Subnet:
        obj = Subnet(**data)
        self._s.add(obj)
        await self._s.commit()
        await self._s.refresh(obj)
        return obj

    async def get_by_id(self, subnet_id: UUID) -> Subnet | None:
        return await self._s.get(Subnet, subnet_id)

    async def list_all(self, page: int, page_size: int) -> tuple[int, list[Subnet]]:
        q = select(Subnet).order_by(Subnet.created_at.desc())
        cq = select(func.count(Subnet.id))
        total = (await self._s.execute(cq)).scalar() or 0
        rows = (await self._s.execute(q.offset((page - 1) * page_size).limit(page_size))).scalars().all()
        return total, list(rows)

    async def update(self, obj: Subnet, data: dict) -> Subnet:
        for k, v in data.items():
            if v is not None:
                setattr(obj, k, v)
        await self._s.commit()
        await self._s.refresh(obj)
        return obj

    async def delete(self, obj: Subnet):
        await self._s.delete(obj)
        await self._s.commit()


class IPAllocationRepository:
    def __init__(self, session: AsyncSession):
        self._s = session

    async def create(self, data: dict) -> IPAllocation:
        obj = IPAllocation(**data)
        self._s.add(obj)
        await self._s.commit()
        await self._s.refresh(obj)
        return obj

    async def get_by_id(self, alloc_id: UUID) -> IPAllocation | None:
        return await self._s.get(IPAllocation, alloc_id)

    async def find_by_ip(self, subnet_id: UUID, ip: str) -> IPAllocation | None:
        q = select(IPAllocation).where(
            IPAllocation.subnet_id == subnet_id, IPAllocation.ip_address == ip
        )
        result = await self._s.execute(q)
        return result.scalar_one_or_none()

    async def list_all(self, page: int, page_size: int,
                       subnet_id: UUID | None, status: str | None,
                       ) -> tuple[int, list[IPAllocation]]:
        q = select(IPAllocation)
        cq = select(func.count(IPAllocation.id))
        if subnet_id:
            q = q.where(IPAllocation.subnet_id == subnet_id)
            cq = cq.where(IPAllocation.subnet_id == subnet_id)
        if status:
            q = q.where(IPAllocation.status == status)
            cq = cq.where(IPAllocation.status == status)
        q = q.order_by(IPAllocation.ip_address).offset((page - 1) * page_size).limit(page_size)
        total = (await self._s.execute(cq)).scalar() or 0
        rows = (await self._s.execute(q)).scalars().all()
        return total, list(rows)

    async def update(self, obj: IPAllocation, data: dict) -> IPAllocation:
        for k, v in data.items():
            if v is not None:
                setattr(obj, k, v)
        await self._s.commit()
        await self._s.refresh(obj)
        return obj
