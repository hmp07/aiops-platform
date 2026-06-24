"""M6 APM — Business Logic."""
from uuid import UUID

from app.core.exceptions import NotFoundError
from app.modules.module6_apm.repository import CrossLayerRepository, EdgeRepository, ServiceRepository


class APMService:
    def __init__(self, s_repo: ServiceRepository, e_repo: EdgeRepository, cl_repo: CrossLayerRepository):
        self._s = s_repo; self._e = e_repo; self._cl = cl_repo

    async def list_services(self, page=1, page_size=20) -> tuple[int, list[dict]]:
        total, rows = await self._s.list_all(page, page_size)
        return total, [self._s_to_dict(r) for r in rows]

    async def create_service(self, data: dict) -> dict:
        return self._s_to_dict(await self._s.create(data))

    async def get_service(self, sid: UUID) -> dict:
        obj = await self._s.get_by_id(sid)
        if not obj: raise NotFoundError("Service not found")
        return self._s_to_dict(obj)

    async def update_service(self, sid: UUID, data: dict) -> dict:
        obj = await self._s.get_by_id(sid)
        if not obj: raise NotFoundError("Service not found")
        return self._s_to_dict(await self._s.update(obj, data))

    async def get_topology(self) -> dict:
        services = (await self._s.list_all(1, 100))[1]
        edges = await self._e.list_all()
        nodes = [{"id": str(r.id), "label": r.display_name, "type": "service",
                   "health": r.health, "metrics": f"P99:{r.p99_latency_ms}ms"} for r in services]
        e_list = [{"source": str(e.source_service_id), "target": str(e.target_service_id),
                    "latency_ms": e.latency_ms, "rps": e.rps, "status": e.status} for e in edges]
        return {"nodes": nodes, "edges": e_list}

    async def add_edge(self, data: dict) -> dict:
        obj = await self._e.create(data)
        return {"id": obj.id, "source_service_id": obj.source_service_id,
                "target_service_id": obj.target_service_id, "latency_ms": obj.latency_ms,
                "rps": obj.rps, "status": obj.status, "created_at": obj.created_at}

    async def get_cross_layer(self, service_id: UUID) -> dict:
        """F6.9 Cross-layer mapping: service → hosts → switches."""
        cl = await self._cl.get_by_service(service_id)
        if not cl:
            svc = await self._s.get_by_id(service_id)
            if svc:
                host_ids = svc.host_ids or []
                cl = await self._cl.create({"service_id": service_id, "host_ids": host_ids,
                    "switch_ids": [], "context": {"host_count": len(host_ids)}})
        return {"service_id": cl.service_id, "host_ids": cl.host_ids,
                "switch_ids": cl.switch_ids, "context": cl.context, "updated_at": cl.updated_at}

    def _s_to_dict(self, obj) -> dict:
        return {"id": obj.id, "name": obj.name, "display_name": obj.display_name,
                "language": obj.language, "instances": obj.instances, "host_ids": obj.host_ids,
                "p99_latency_ms": obj.p99_latency_ms, "error_rate_pct": obj.error_rate_pct,
                "throughput_rps": obj.throughput_rps, "health": obj.health,
                "created_at": obj.created_at, "updated_at": obj.updated_at}
