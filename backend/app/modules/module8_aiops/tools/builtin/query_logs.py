"""Builtin MCP tool: query_logs.

Queries log entries from Module 4 (Log Management).
"""

import logging

from app.core.database.session import async_session_factory
from app.modules.module4_log.repository import LogRepository

logger = logging.getLogger(__name__)

TOOL_DEFINITION = {
    "name": "aiops.query_logs",
    "title": "查询日志",
    "description": "查询平台日志源中的日志条目。支持按严重级别、设备、来源和关键字过滤。",
    "handler_name": "query_logs",
    "permission": "log:entry:list",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索关键字，匹配日志消息和主机名",
            },
            "severity": {
                "type": "string",
                "description": "日志级别：error / warning / info / debug",
            },
            "source": {
                "type": "string",
                "description": "日志来源",
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
    source: str = "",
    limit: int = 10,
) -> dict:
    """Execute query_logs tool."""
    async with async_session_factory() as db:
        repo = LogRepository(db)
        total, items = await repo.list_all(
            page=1,
            page_size=min(max(limit, 1), 20),
            device_id=None,
            severity=severity or None,
            source=source or None,
            keyword=query or None,
        )

        log_list = []
        for entry in items:
            log_list.append({
                "id": str(entry.id),
                "message": (entry.message or "")[:300],
                "severity": entry.severity or "",
                "source": entry.source or "",
                "hostname": entry.hostname or "",
                "time": entry.time.isoformat() if entry.time else "",
            })

        return {
            "found": total,
            "returned": len(log_list),
            "items": log_list,
        }
