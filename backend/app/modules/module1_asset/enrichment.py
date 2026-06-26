"""M1 Asset — Zabbix → iTop data enrichment.

After asset matching, pushes hardware info (serial numbers, OS
versions) collected by Zabbix monitoring back into the iTop CMDB.
"""
from app.integrations.itop.client import ItopAdapter
from app.integrations.zabbix.client import ZabbixAdapter


# ── Zabbix item key → iTop CI field mapping ──────────────────

ENRICHMENT_MAP: list[dict] = [
    {
        "label": "serialnumber",
        "keys": ["system.hw.serialnumber",      # SNMP
                 "system.serialnumber",           # generic
                 "hw.serialnumber"],              # custom
        "itop_field": "serialnumber",
    },
    {
        "label": "os_version",
        "keys": ["system.sw.os[name]",           # SNMP
                 "system.sw.version",             # another SNMP variant
                 "agent.version"],                # Zabbix agent
        "itop_field": "osversion_id",
        "needs_lookup": True,                     # needs to match iTop OSVersion
    },
    {
        "label": "model",
        "keys": ["system.hw.model",               # SNMP
                 "hw.model"],                     # custom
        "itop_field": "model_id",
        "needs_lookup": True,                     # needs to match iTop Model
    },
    {
        "label": "description",
        "keys": ["system.descr",                  # SNMP sysDescr
                 "system.description"],           # generic
        "itop_field": "description",
    },
]


class EnrichmentService:
    """Push Zabbix-collected data back to iTop CIs."""

    def __init__(self, zabbix: ZabbixAdapter, itop: ItopAdapter):
        self._zabbix = zabbix
        self._itop = itop

    async def enrich(
        self, zabbix_hostid: str, itop_ci_class: str, itop_ci_id: int,
    ) -> dict:
        """Enrich an iTop CI with data from Zabbix monitoring.

        Returns a dict of {field: old_value → new_value} for
        fields that were successfully updated.
        """
        # 1. Fetch all items for this Zabbix host
        items = await self._zabbix.get_items(zabbix_hostid)
        if not items:
            return {"status": "error", "message": "No Zabbix items found"}

        # 2. Extract enrichment fields
        updates: dict = {}
        for mapping in ENRICHMENT_MAP:
            value = self._find_value(items, mapping["keys"])
            if value:
                field = mapping["itop_field"]
                if mapping.get("needs_lookup"):
                    # Resolve string value to iTop FK id if possible
                    updates[field] = value  # For now, iTop handles string values too
                else:
                    updates[field] = str(value)[:255]

        if not updates:
            return {"status": "ok", "message": "No enrichment data found", "updates": {}}

        # 3. Push to iTop
        result = await self._itop.update_ci(itop_ci_class, itop_ci_id, updates)
        return {
            "status": "ok",
            "itop_class": itop_ci_class,
            "itop_id": itop_ci_id,
            "updates": updates,
            "itop_response": result.get("message", ""),
        }

    @staticmethod
    def _find_value(items: list[dict], keys: list[str]) -> str | None:
        """Find the first non-empty lastvalue for any of the given keys."""
        for item in items:
            key = item.get("key_", "")
            for pattern in keys:
                if pattern.split("[")[0] in key:
                    val = item.get("lastvalue")
                    if val is not None and str(val).strip():
                        return str(val).strip()
        return None
