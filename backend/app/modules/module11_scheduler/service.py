"""M11 — DataSource Service with adapter factory."""
from datetime import datetime, timezone
from uuid import UUID
from app.core.exceptions import NotFoundError
from app.modules.module11_scheduler.repository import DataSourceRepository

ADAPTER_MAP = {
    "zabbix": "app.integrations.zabbix.client.ZabbixAdapter",
    "prometheus": "app.integrations.prometheus.client.PrometheusAdapter",
    "itop": "app.integrations.itop.client.ItopAdapter",
    "signoz": "app.integrations.signoz.client.SigNozAdapter",
}

class DataSourceService:
    def __init__(self, repo: DataSourceRepository): self._repo = repo

    async def list_all(self) -> list[dict]:
        rows = await self._repo.list_all()
        return [self._to_dict(r) for r in rows]

    async def create(self, data: dict) -> dict:
        data["status"] = "disconnected"
        obj = await self._repo.create(data)
        return self._to_dict(obj)

    async def get(self, ds_id: UUID) -> dict:
        obj = await self._repo.get_by_id(ds_id)
        if not obj: raise NotFoundError("Data source not found")
        return self._to_dict(obj)

    async def update(self, ds_id: UUID, data: dict) -> dict:
        obj = await self._repo.get_by_id(ds_id)
        if not obj: raise NotFoundError("Data source not found")
        obj = await self._repo.update(obj, data)
        return self._to_dict(obj)

    async def delete(self, ds_id: UUID):
        obj = await self._repo.get_by_id(ds_id)
        if not obj: raise NotFoundError("Data source not found")
        await self._repo.delete(obj)

    async def test_connection(self, ds_id: UUID) -> dict:
        obj = await self._repo.get_by_id(ds_id)
        if not obj: raise NotFoundError("Data source not found")
        adapter = self._get_adapter(obj)
        if not adapter:
            return {"status": "error", "message": f"Unknown source type: {obj.source_type}"}
        try:
            ok = await adapter.health_check()
            status = "connected" if ok else "disconnected"
            await self._repo.update(obj, {"status": status, "last_error": None if ok else "Connection failed"})
            return {"status": status, "message": "Connection successful" if ok else "Connection failed"}
        except Exception as e:
            await self._repo.update(obj, {"status": "error", "last_error": str(e)[:500]})
            return {"status": "error", "message": str(e)[:200]}

    async def sync(self, ds_id: UUID, db_session=None) -> dict:
        obj = await self._repo.get_by_id(ds_id)
        if not obj: raise NotFoundError("Data source not found")
        adapter = self._get_adapter(obj)
        if not adapter: return {"status": "error", "message": f"Unknown type: {obj.source_type}"}
        try:
            result = await adapter.sync(db_session)
            await self._repo.update(obj, {"status": "connected", "last_sync_at": datetime.now(timezone.utc), "last_error": None})
            return {"status": "ok", **result}
        except Exception as e:
            await self._repo.update(obj, {"status": "error", "last_error": str(e)[:500]})
            return {"status": "error", "message": str(e)[:200]}

    def _get_adapter(self, obj):
        cls_path = ADAPTER_MAP.get(obj.source_type)
        if not cls_path: return None
        mod_name, cls_name = cls_path.rsplit(".", 1)
        import importlib
        mod = importlib.import_module(mod_name)
        cls = getattr(mod, cls_name)
        return cls(obj.endpoint_url, obj.auth_config)

    def _to_dict(self, obj) -> dict:
        return {"id": obj.id, "name": obj.name, "source_type": obj.source_type,
                "description": obj.description, "endpoint_url": obj.endpoint_url,
                "auth_config": {k:v for k,v in obj.auth_config.items() if k not in ("password","token","secret")},
                "sync_config": obj.sync_config, "status": obj.status,
                "last_sync_at": obj.last_sync_at, "last_error": obj.last_error,
                "is_enabled": obj.is_enabled, "created_at": obj.created_at}
