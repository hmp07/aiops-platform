"""Builtin MCP tool: query_events — EventWall events query."""
import logging
from app.core.database.session import async_session_factory
from app.modules.module10_eventwall.repository import EventRepository

logger = logging.getLogger(__name__)

TOOL_DEFINITION = {
    "name": "aiops.query_events",
    "title": "查询事件墙",
    "description": "查询平台事件墙中的事件记录，支持按事件类型、来源模块、严重级别和资源过滤。",
    "handler_name": "query_events",
    "permission": "eventwall:event:list",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "搜索关键字"},
            "severity": {"type": "string", "description": "严重级别：info/warning/critical"},
            "event_type": {"type": "string", "description": "事件类型"},
            "limit": {"type": "integer", "minimum": 1, "maximum": 20},
        },
    },
}


async def execute(query: str = "", severity: str = "", event_type: str = "", limit: int = 10) -> dict:
    async with async_session_factory() as db:
        repo = EventRepository(db)
        total, items = await repo.query(
            page=1, page_size=min(max(limit, 1), 20),
            event_type=event_type or None, severity=severity or None,
            start_time=None, end_time=None,
            source_module=None, resource_type=None, resource_id=None,
            correlation_id=None, fault_id=None,
        )
        event_list = [{
            "id": str(e.id), "event_type": e.event_type or "",
            "severity": e.severity or "", "status": e.status or "",
            "source_module": e.source_module or "",
            "resource_name": e.resource_name or "",
            "timestamp": e.timestamp.isoformat() if e.timestamp else "",
        } for e in items]
        return {"found": total, "returned": len(event_list), "items": event_list}
