"""Builtin MCP tool: query_devices.

Queries device assets from Module 1 (Asset Management).
"""

import logging

from app.core.database.session import async_session_factory
from app.modules.module1_asset.repository import DeviceRepository

logger = logging.getLogger(__name__)

TOOL_DEFINITION = {
    "name": "aiops.query_devices",
    "title": "查询设备",
    "description": "查询平台中的设备资产信息，包括设备名称、类型、厂商、型号、IP 地址和状态。支持按设备类型、厂商、状态和关键字过滤。",
    "handler_name": "query_devices",
    "permission": "asset:device:list",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索关键字，匹配设备名称、IP 地址或型号",
            },
            "device_type": {
                "type": "string",
                "description": "设备类型过滤：server / switch / router / firewall / storage",
            },
            "status": {
                "type": "string",
                "description": "设备生命周期状态：active / standby / retired",
            },
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 20,
                "description": "返回数量上限，默认 10",
            },
        },
    },
}


async def execute(query: str = "", device_type: str = "", status: str = "", limit: int = 10) -> dict:
    """Execute query_devices tool.

    Returns a dict compatible with the MCP result format.
    """
    async with async_session_factory() as db:
        repo = DeviceRepository(db)
        total, items = await repo.list_devices(
            page=1,
            page_size=min(max(limit, 1), 20),
            device_type=device_type or None,
            vendor=None,
            lifecycle_status=status or None,
            keyword=query or None,
        )

        device_list = []
        for d in items:
            extra = d.extra_attrs if isinstance(d.extra_attrs, dict) else {}
            device_list.append({
                "id": str(d.id),
                "name": d.device_name,
                "type": d.device_type or "",
                "vendor": d.vendor or "",
                "model": d.model or "",
                "status": d.lifecycle_status or "",
                "ip": str(d.management_ip) if d.management_ip else "",
                "source": extra.get("source", ""),
                "external_id": extra.get("external_id", ""),
            })

        return {
            "found": total,
            "returned": len(device_list),
            "items": device_list,
        }
