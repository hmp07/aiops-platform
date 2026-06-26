"""Built-in tool: query_device — real DB query."""
from app.modules.module8_ai.tools.base import BaseTool, ToolSpec


class QueryDeviceTool(BaseTool):
    spec = ToolSpec(
        tool_id="query_device",
        name="Query Device",
        description="Query device information by name, IP address, or device type. "
                    "Returns device details including status, vendor, model, and location.",
        parameters={
            "type": "object",
            "properties": {
                "device_name": {"type": "string", "description": "Device name (partial match supported)"},
                "device_type": {"type": "string", "description": "Device type: switch, router, firewall, server"},
                "ip_address": {"type": "string", "description": "Management IP address"},
            },
        },
        required_permissions=["asset:device:list"],
        risk_level="read_only",
        timeout_seconds=10,
        module="module1_asset",
    )

    async def execute(self, **kwargs) -> dict:
        from app.core.database.session import async_session_factory
        from app.modules.module1_asset.repository import DeviceRepository

        device_name = kwargs.get("device_name", "")
        device_type = kwargs.get("device_type", "")
        ip_address = kwargs.get("ip_address", "")

        async with async_session_factory() as db:
            repo = DeviceRepository(db)
            total, items = await repo.list_devices(
                1, 50, device_type or None, None, None,
                device_name or ip_address or None,
            )
            return {
                "found": total,
                "devices": [
                    {"id": str(d.id), "name": d.device_name, "type": d.device_type,
                     "vendor": d.vendor, "model": d.model,
                     "ip": str(d.management_ip) if d.management_ip else None,
                     "status": d.lifecycle_status, "location": d.location}
                    for d in items[:10]
                ],
            }
