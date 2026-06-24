"""M2 IPAM — Business Logic."""
from datetime import datetime, timezone
from uuid import UUID

from app.core.exceptions import ConflictError, NotFoundError
from app.modules.module2_ipam.repository import IPAllocationRepository, SubnetRepository


class SubnetService:
    def __init__(self, repo: SubnetRepository):
        self._repo = repo

    async def list_subnets(self, page: int = 1, page_size: int = 20) -> tuple[int, list[dict]]:
        total, rows = await self._repo.list_all(page, page_size)
        return total, [self._to_dict(r) for r in rows]

    async def create_subnet(self, data: dict) -> dict:
        # Calculate total IPs from CIDR
        cidr = data.get("cidr", "")
        data["total_ips"] = self._cidr_size(cidr)
        obj = await self._repo.create(data)
        return self._to_dict(obj)

    async def update_subnet(self, subnet_id: UUID, data: dict) -> dict:
        obj = await self._repo.get_by_id(subnet_id)
        if not obj:
            raise NotFoundError("Subnet not found")
        if "cidr" in data and data["cidr"]:
            data["total_ips"] = self._cidr_size(data["cidr"])
        obj = await self._repo.update(obj, data)
        return self._to_dict(obj)

    async def delete_subnet(self, subnet_id: UUID):
        obj = await self._repo.get_by_id(subnet_id)
        if not obj:
            raise NotFoundError("Subnet not found")
        await self._repo.delete(obj)

    def _cidr_size(self, cidr: str) -> int:
        try:
            parts = cidr.split("/")
            prefix = int(parts[1]) if len(parts) > 1 else 32
            return 2 ** (32 - prefix)
        except (ValueError, IndexError):
            return 0

    def _to_dict(self, obj) -> dict:
        return {
            "id": obj.id, "cidr": obj.cidr, "vlan_id": obj.vlan_id,
            "gateway": str(obj.gateway) if obj.gateway else None,
            "description": obj.description, "total_ips": obj.total_ips,
            "used_ips": obj.used_ips, "created_at": obj.created_at,
        }


class IPAllocationService:
    def __init__(self, alloc_repo: IPAllocationRepository, subnet_repo: SubnetRepository):
        self._repo = alloc_repo
        self._subnet = subnet_repo

    async def list_allocations(self, page: int = 1, page_size: int = 50,
                               subnet_id: UUID | None = None, status: str | None = None,
                               ) -> tuple[int, list[dict]]:
        total, rows = await self._repo.list_all(page, page_size, subnet_id, status)
        return total, [self._to_dict(r) for r in rows]

    async def allocate(self, data: dict) -> dict:
        # Check IP not already allocated
        existing = await self._repo.find_by_ip(data["subnet_id"], data["ip_address"])
        if existing and existing.status == "allocated":
            raise ConflictError(f"IP {data['ip_address']} is already allocated")
        data["status"] = "allocated"
        data["source"] = "manual"
        data["allocated_at"] = datetime.now(timezone.utc)
        obj = await self._repo.create(data)
        # Update subnet used count
        subnet = await self._subnet.get_by_id(data["subnet_id"])
        if subnet:
            await self._subnet.update(subnet, {"used_ips": subnet.used_ips + 1})
        return self._to_dict(obj)

    async def release(self, allocation_id: UUID) -> dict:
        obj = await self._repo.get_by_id(allocation_id)
        if not obj:
            raise NotFoundError("IP allocation not found")
        obj = await self._repo.update(obj, {
            "status": "free", "device_id": None, "interface_name": None,
            "released_at": datetime.now(timezone.utc),
        })
        subnet = await self._subnet.get_by_id(obj.subnet_id)
        if subnet and subnet.used_ips > 0:
            await self._subnet.update(subnet, {"used_ips": subnet.used_ips - 1})
        return self._to_dict(obj)

    def _to_dict(self, obj) -> dict:
        return {
            "id": obj.id, "subnet_id": obj.subnet_id,
            "ip_address": str(obj.ip_address) if obj.ip_address else None,
            "status": obj.status, "device_id": obj.device_id,
            "interface_name": obj.interface_name, "source": obj.source,
            "allocated_at": obj.allocated_at, "released_at": obj.released_at,
            "created_at": obj.created_at,
        }
