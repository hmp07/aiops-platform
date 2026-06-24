"""Zabbix API client adapter."""
from app.config.settings import get_settings
from app.integrations.base import BaseAdapter

settings = get_settings()


class ZabbixAdapter(BaseAdapter):
    """Zabbix monitoring system adapter.

    Connects to Zabbix API to pull:
    - Active triggers (→ alerts)
    - Host inventory (→ device calibration)
    - Performance metrics (→ metrics hypertable)
    """

    def __init__(self):
        self._url = settings.ZABBIX_API_URL
        self._user = settings.ZABBIX_API_USER
        self._password = settings.ZABBIX_API_PASSWORD
        self._token: str | None = None

    async def health_check(self) -> bool:
        if not self._url:
            return False
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.post(self._url, json={
                    "jsonrpc": "2.0", "method": "apiinfo.version",
                    "params": [], "id": 1,
                })
                return resp.status_code == 200
        except Exception:
            return False

    async def get_hosts(self) -> list[dict]:
        """Fetch all monitored hosts."""
        return await self._call("host.get", {"output": ["hostid", "host", "name", "status"]})

    async def get_triggers(self, min_severity: int = 2) -> list[dict]:
        """Fetch active triggers with severity >= min_severity."""
        return await self._call("trigger.get", {
            "output": ["triggerid", "description", "priority", "value"],
            "filter": {"value": 1}, "min_severity": min_severity,
            "selectHosts": ["hostid", "host"],
        })

    async def get_metrics(self, host_id: str, item_keys: list[str], limit: int = 10) -> list[dict]:
        """Fetch recent metric values."""
        return await self._call("history.get", {
            "output": ["itemid", "clock", "value"],
            "hostids": host_id, "sortfield": "clock",
            "sortorder": "DESC", "limit": limit,
        })

    async def _call(self, method: str, params: dict) -> list[dict]:
        """Make a JSON-RPC call to Zabbix API."""
        if not self._url:
            return []
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(self._url, json={
                    "jsonrpc": "2.0", "method": method,
                    "params": params, "auth": self._token,
                    "id": 1,
                })
                data = resp.json()
                if "result" in data:
                    return data["result"]
                # Login if needed
                if "error" in data and not self._token:
                    auth_resp = await client.post(self._url, json={
                        "jsonrpc": "2.0", "method": "user.login",
                        "params": {"username": self._user, "password": self._password},
                        "id": 1,
                    })
                    auth_data = auth_resp.json()
                    self._token = auth_data.get("result", "")
                    if self._token:
                        return await self._call(method, params)
                return []
        except Exception:
            return []

    async def close(self):
        if self._token:
            await self._call("user.logout", [])
            self._token = None
