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

    def __init__(self, endpoint_url: str = "", auth_config: dict | None = None):
        self._url = endpoint_url or settings.ZABBIX_API_URL
        auth = auth_config or {}
        self._user = auth.get("username") or settings.ZABBIX_API_USER
        self._password = auth.get("password") or settings.ZABBIX_API_PASSWORD
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

    async def sync(self, db_session=None) -> dict:
        """Sync Zabbix data into AIOps: triggers→alerts, hosts→devices."""
        import uuid as _uuid
        from datetime import datetime, timezone

        triggers = await self.get_triggers(min_severity=1)
        hosts = await self.get_hosts()
        items = await self.get_metrics("", [], 0)  # get metric items

        alerts_created = 0
        devices_synced = 0

        if db_session:
            from app.modules.module3_monitoring.models import Alert
            from app.modules.module1_asset.models import Device

            now = datetime.now(timezone.utc)
            severity_map = {0: "info", 1: "info", 2: "warning", 3: "warning", 4: "critical", 5: "critical"}

            # Sync hosts as devices
            for host in hosts:
                hostid = host.get("hostid", "")
                hostname = host.get("host", "")
                # Check if device already exists
                from sqlalchemy import select
                existing = (await db_session.execute(
                    select(Device).where(Device.device_name == hostname)
                )).scalar_one_or_none()
                if not existing:
                    dev = Device(
                        id=_uuid.uuid4(), device_name=hostname,
                        device_type="server", vendor="Zabbix",
                        model=host.get("name", hostname),
                        management_ip=host.get("interfaces", [{}])[0].get("ip", "") if host.get("interfaces") else "",
                        lifecycle_status="in_use",
                        business_system="Zabbix Monitored",
                        extra_attrs=host,
                    )
                    db_session.add(dev)
                    devices_synced += 1

            # Sync triggers as alerts
            for trigger in triggers:
                triggerid = trigger.get("triggerid", "")
                description = trigger.get("description", "")
                priority = int(trigger.get("priority", 0))
                host_list = trigger.get("hosts", [])
                host_name = host_list[0].get("host", "") if host_list else "Unknown"

                # Find device_id from host
                existing_dev = (await db_session.execute(
                    select(Device).where(Device.device_name == host_name)
                )).scalar_one_or_none()
                device_id = existing_dev.id if existing_dev else None

                # Check for existing alert (dedup by triggerid)
                existing_alert = (await db_session.execute(
                    select(Alert).where(Alert.description.ilike(f"%zbx:{triggerid}%"))
                )).scalar_one_or_none()
                if not existing_alert:
                    alert = Alert(
                        id=_uuid.uuid4(), time=now,
                        device_id=device_id,
                        severity=severity_map.get(priority, "warning"),
                        status="triggered",
                        title=f"[Zabbix] {description}",
                        description=f"Trigger: {description} on {host_name} (zbx:{triggerid})",
                        source="zabbix",
                    )
                    db_session.add(alert)
                    alerts_created += 1

            if alerts_created > 0 or devices_synced > 0:
                await db_session.commit()

        return {
            "status": "ok",
            "triggers_count": len(triggers),
            "hosts_count": len(hosts),
            "devices_synced": devices_synced,
            "alerts_created": alerts_created,
            "message": f"Synced {devices_synced} devices, {alerts_created} alerts from {len(hosts)} hosts, {len(triggers)} triggers"
        }

    async def close(self):
        if self._token:
            await self._call("user.logout", [])
            self._token = None
