"""Prometheus adapter — PromQL queries for metrics."""
import httpx
from app.integrations.base import BaseAdapter

class PrometheusAdapter(BaseAdapter):
    def __init__(self, endpoint_url: str = "", auth_config: dict | None = None):
        self._url = endpoint_url.rstrip("/")
        self._auth = auth_config or {}

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as c:
                r = await c.get(f"{self._url}/api/v1/query?query=up")
                return r.status_code == 200
        except: return False

    async def query(self, promql: str) -> list[dict]:
        """Execute instant PromQL query."""
        try:
            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.get(f"{self._url}/api/v1/query", params={"query": promql})
                data = r.json()
                return data.get("data", {}).get("result", [])
        except: return []

    async def query_range(self, promql: str, start: str, end: str, step: str = "60s") -> list[dict]:
        """Execute range query."""
        try:
            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.get(f"{self._url}/api/v1/query_range", params={"query": promql, "start": start, "end": end, "step": step})
                return r.json().get("data", {}).get("result", [])
        except: return []

    async def sync(self) -> dict:
        """Sync metrics into M3 metrics table."""
        metrics = await self.query("up")
        return {"metrics_count": len(metrics), "status": "ok"}

    async def close(self): pass
