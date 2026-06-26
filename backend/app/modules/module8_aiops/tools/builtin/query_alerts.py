"""Builtin MCP tool: query_alerts.

Queries alerts from Module 3 (Monitoring).
"""

import logging

from app.core.database.session import async_session_factory
from app.modules.module3_monitoring.repository import AlertRepository

logger = logging.getLogger(__name__)

TOOL_DEFINITION = {
    "name": "aiops.query_alerts",
    "title": "查询告警",
    "description": "查询平台告警中心中的只读告警事实。支持按严重级别、状态、设备 ID 和来源过滤。",
    "handler_name": "query_alerts",
    "permission": "monitoring:alert:list",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索关键字",
            },
            "severity": {
                "type": "string",
                "description": "告警严重级别：critical / warning / info",
            },
            "status": {
                "type": "string",
                "description": "告警状态：triggered / acknowledged / resolved",
            },
            "source": {
                "type": "string",
                "description": "告警来源：zabbix / prometheus / manual",
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


async def execute(
    query: str = "",
    severity: str = "",
    status: str = "",
    source: str = "",
    limit: int = 10,
) -> dict:
    """Execute query_alerts tool."""
    async with async_session_factory() as db:
        repo = AlertRepository(db)
        total, items = await repo.list_all(
            page=1,
            page_size=min(max(limit, 1), 20),
            severity=severity or None,
            status=status or None,
            device_id=None,
            source=source or None,
        )

        alert_list = []
        for a in items:
            alert_list.append({
                "id": str(a.id),
                "title": a.title or "",
                "severity": a.severity or "",
                "status": a.status or "",
                "source": a.source or "",
                "device_id": str(a.device_id) if a.device_id else "",
                "time": a.time.isoformat() if a.time else "",
                "description": (a.description or "")[:300],
            })

        return {
            "found": total,
            "returned": len(alert_list),
            "items": alert_list,
        }
