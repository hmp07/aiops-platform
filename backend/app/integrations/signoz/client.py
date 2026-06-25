"""SigNoz adapter — APM traces, metrics, services."""
import httpx
from app.integrations.base import BaseAdapter

class SigNozAdapter(BaseAdapter):
    def __init__(self, endpoint_url: str = "", auth_config: dict | None = None):
        self._url = endpoint_url.rstrip("/")
        self._auth = auth_config or {}

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as c:
                r = await c.get(f"{self._url}/api/v1/services", headers=self._headers())
                return r.status_code == 200
        except: return False

    def _headers(self) -> dict:
        h = {}
        if self._auth.get("api_key"): h["Authorization"] = f"Bearer {self._auth['api_key']}"
        return h

    async def get_services(self) -> list[dict]:
        try:
            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.get(f"{self._url}/api/v1/services", headers=self._headers())
                return r.json() if r.status_code == 200 else []
        except: return []

    async def get_traces(self, service: str, limit: int = 10) -> list[dict]:
        try:
            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.get(f"{self._url}/api/v1/traces", params={"service": service, "limit": limit}, headers=self._headers())
                return r.json() if r.status_code == 200 else []
        except: return []

    async def get_metrics(self, service: str) -> dict:
        try:
            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.get(f"{self._url}/api/v1/metrics", params={"service": service}, headers=self._headers())
                return r.json() if r.status_code == 200 else {}
        except: return {}

    async def sync(self) -> dict:
        """Sync SigNoz data into M6 APM."""
        services = await self.get_services()
        return {"services_count": len(services), "status": "ok"}

    async def close(self): pass
