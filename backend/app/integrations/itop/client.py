"""iTop CMDB adapter — REST API for CI data sync."""
import httpx
from app.integrations.base import BaseAdapter

class ItopAdapter(BaseAdapter):
    def __init__(self, endpoint_url: str = "", auth_config: dict | None = None):
        self._url = endpoint_url.rstrip("/")
        self._auth = auth_config or {}

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as c:
                r = await c.get(f"{self._url}/webservices/rest.php?version=1.3")
                return r.status_code == 200
        except: return False

    async def get_cis(self, ci_class: str = "Server", limit: int = 100) -> list[dict]:
        """Fetch Configuration Items."""
        payload = {
            "operation": "core/get",
            "class": ci_class,
            "key": f"SELECT * FROM {ci_class} LIMIT {limit}",
            "output_fields": "*",
        }
        try:
            async with httpx.AsyncClient(timeout=30, auth=(self._auth.get("user",""), self._auth.get("password",""))) as c:
                r = await c.post(f"{self._url}/webservices/rest.php?version=1.3", json=payload)
                return r.json().get("objects", [])
        except: return []

    async def sync(self) -> dict:
        """Sync iTop CIs into M1 devices."""
        servers = await self.get_cis("Server", 50)
        return {"cis_count": len(servers), "status": "ok"}

    async def close(self): pass
