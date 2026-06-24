"""Built-in tool: query_device — mock implementation."""
from app.modules.module8_ai.tools.base import BaseTool, ToolSpec

MOCK_DEVICES = [
    {"id": "d1", "name": "CORE-SW-01", "type": "switch", "vendor": "Cisco",
     "model": "Catalyst 9500", "ip": "10.1.1.1", "status": "active",
     "cpu_usage": 95, "location": "A座-3F-核心机房"},
    {"id": "d2", "name": "CORE-SW-02", "type": "switch", "vendor": "Cisco",
     "model": "Catalyst 9500", "ip": "10.1.1.2", "status": "active",
     "cpu_usage": 25, "location": "A座-3F-核心机房"},
    {"id": "d3", "name": "AGG-SW-01", "type": "switch", "vendor": "Huawei",
     "model": "S6730-H48X6C", "ip": "10.1.2.1", "status": "active",
     "cpu_usage": 45, "location": "A座-3F-核心机房"},
    {"id": "d9", "name": "ROUTER-01", "type": "router", "vendor": "Cisco",
     "model": "ISR 4451", "ip": "10.1.0.254", "status": "active",
     "cpu_usage": 55, "location": "A座-3F-核心机房"},
    {"id": "d11", "name": "SRV-APP-01", "type": "server", "vendor": "Dell",
     "model": "R750xs", "ip": "10.1.10.11", "status": "active",
     "cpu_usage": 70, "location": "B座-2F-服务器机房"},
    {"id": "d13", "name": "SRV-DB-01", "type": "server", "vendor": "HPE",
     "model": "DL380 Gen11", "ip": "10.1.10.21", "status": "warning",
     "cpu_usage": 82, "location": "B座-2F-服务器机房"},
]


class QueryDeviceTool(BaseTool):
    spec = ToolSpec(
        tool_id="query_device",
        name="Query Device",
        description="Query device information by name, IP address, or device type. "
                    "Returns device details including status, CPU usage, location, "
                    "model, and vendor.",
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
        device_name = kwargs.get("device_name", "").lower()
        device_type = kwargs.get("device_type", "").lower()
        ip_address = kwargs.get("ip_address", "")

        results = MOCK_DEVICES
        if device_name:
            results = [d for d in results if device_name in d["name"].lower()]
        if device_type:
            results = [d for d in results if d["type"] == device_type]
        if ip_address:
            results = [d for d in results if d["ip"] == ip_address]

        return {
            "found": len(results),
            "devices": results[:10],  # max 10 results
        }
