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
        """Fetch all monitored hosts (with interface IPs)."""
        return await self._call("host.get", {
            "output": ["hostid", "host", "name", "status"],
            "selectInterfaces": ["ip", "dns", "type", "main"],
        })

    async def get_triggers(self, min_severity: int = 2) -> list[dict]:
        """Fetch active triggers with severity >= min_severity."""
        return await self._call("trigger.get", {
            "output": ["triggerid", "description", "priority", "value"],
            "filter": {"value": 1}, "min_severity": min_severity,
            "selectHosts": ["hostid", "host"],
        })

    async def get_items(self, hostids: str | list[str], search_keys: list[str] | None = None) -> list[dict]:
        """Fetch monitored items for a host, optionally filtered by key patterns.

        Fetches all items for the host, then filters in Python using the
        search_keys patterns (ITOps-Watch approach).  This avoids Zabbix
        ``search`` parameter quirks across versions (7.0 vs 7.4).
        """
        hostid_list = hostids if isinstance(hostids, list) else [hostids]
        params: dict = {
            "output": ["itemid", "hostid", "name", "key_", "lastvalue", "lastclock", "units", "value_type"],
            "hostids": hostid_list,
            "limit": 50000,
        }
        items = await self._call("item.get", params)

        if search_keys:
            filtered = []
            for item in items:
                key = item.get("key_", "")
                for pattern in search_keys:
                    # Match prefix (strip everything after '[' for partial match)
                    clean = pattern.split("[")[0]
                    if clean in key:
                        filtered.append(item)
                        break
            return filtered

        return items

    async def get_history(
        self, hostids: str | list[str], item_key: str,
        start_time: int, end_time: int, limit: int = 500,
    ) -> list[dict]:
        """Fetch historical data for a specific metric key.

        Two-step ITOps-Watch pattern:
        1. ``item.get`` with ``search:{key_: item_key}`` → itemids + value_type
        2. ``history.get`` with those itemids + time range
        """
        hostid_list = hostids if isinstance(hostids, list) else [hostids]

        # Step 1: Resolve item key → itemids
        items = await self._call("item.get", {
            "output": ["itemid", "value_type"],
            "hostids": hostid_list,
            "search": {"key_": item_key},
        })
        if not items:
            return []

        itemids = [i["itemid"] for i in items]
        value_type = int(items[0].get("value_type", 0))  # 0=float, 3=unsigned

        # Step 2: Fetch history
        return await self._call("history.get", {
            "output": ["itemid", "clock", "value"],
            "itemids": itemids,
            "history": value_type,
            "time_from": start_time,
            "time_till": end_time,
            "sortfield": "clock",
            "sortorder": "ASC",
            "limit": limit,
        })

    async def _call(self, method: str, params: dict) -> list[dict]:
        """Make a JSON-RPC call to Zabbix API.

        Zabbix 7.4+ uses ``Authorization: Bearer <token>`` HTTP header.
        Older versions put ``auth`` in the JSON-RPC body.  We try the
        Bearer header first (7.4 style), then fall back to body-auth.
        """
        if not self._url:
            return []
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as client:
                headers = {"Content-Type": "application/json"}
                if self._token:
                    headers["Authorization"] = f"Bearer {self._token}"

                body: dict = {
                    "jsonrpc": "2.0", "method": method,
                    "params": params, "id": 1,
                }

                resp = await client.post(self._url, json=body, headers=headers)
                data = resp.json()

                if "result" in data:
                    return data["result"]

                # If request failed and we have no token, login first
                if "error" in data and not self._token:
                    login_resp = await client.post(self._url, json={
                        "jsonrpc": "2.0", "method": "user.login",
                        "params": {"username": self._user, "password": self._password},
                        "id": 1,
                    })
                    login_data = login_resp.json()
                    self._token = login_data.get("result", "")
                    if self._token:
                        # Retry with the new token (Bearer header for 7.4+)
                        headers["Authorization"] = f"Bearer {self._token}"
                        retry_resp = await client.post(self._url, json=body, headers=headers)
                        retry_data = retry_resp.json()
                        if "result" in retry_data:
                            return retry_data["result"]
                return []
        except Exception:
            return []

    async def sync(self, db_session=None) -> dict:
        """Sync Zabbix data into AIOps: triggers→alerts, hosts→devices."""
        import uuid as _uuid
        from datetime import datetime, timezone

        triggers = await self.get_triggers(min_severity=1)
        hosts = await self.get_hosts()

        alerts_created = 0
        devices_synced = 0

        if db_session:
            from app.modules.module3_monitoring.models import Alert
            from app.modules.module1_asset.models import Device
            from sqlalchemy import select

            now = datetime.now(timezone.utc)
            severity_map = {0: "info", 1: "info", 2: "warning", 3: "warning", 4: "critical", 5: "critical"}

            try:
                # Sync hosts as devices
                for host in hosts:
                    hostid = host.get("hostid", "")
                    hostname = host.get("host", "")
                    # Extract primary IP from interfaces
                    interfaces = host.get("interfaces", [])
                    primary_ip = None
                    if interfaces:
                        main_if = [i for i in interfaces if i.get("main") == "1"]
                        iface = main_if[0] if main_if else interfaces[0]
                        ip_val = iface.get("ip", "")
                        primary_ip = ip_val if ip_val else None

                    # Check if device already exists (by hostname)
                    existing = (await db_session.execute(
                        select(Device).where(Device.device_name == hostname)
                    )).scalar_one_or_none()
                    if not existing:
                        dev = Device(
                            id=_uuid.uuid4(), device_name=hostname,
                            device_type="server", vendor="Zabbix",
                            model=host.get("name", hostname),
                            management_ip=primary_ip,
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

            except Exception:
                # Rollback on any DB error so the session stays usable
                await db_session.rollback()
                raise

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
