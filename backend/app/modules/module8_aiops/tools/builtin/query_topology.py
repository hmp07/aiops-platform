"""Builtin MCP tool: query_topology.

Queries service topology and dependency graph from Module 6 (APM).
"""

import logging

from app.core.database.session import async_session_factory
from app.modules.module6_apm.repository import ServiceRepository, EdgeRepository

logger = logging.getLogger(__name__)

TOOL_DEFINITION = {
    "name": "aiops.query_topology",
    "title": "查询服务拓扑",
    "description": "查询平台 APM 中的服务拓扑和依赖关系图。返回服务节点和边信息。",
    "handler_name": "query_topology",
    "permission": "apm:service:list",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索关键字，匹配服务名称",
            },
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 20,
                "description": "返回服务数量上限，默认 10",
            },
        },
    },
}


async def execute(query: str = "", limit: int = 10) -> dict:
    """Execute query_topology tool."""
    async with async_session_factory() as db:
        svc_repo = ServiceRepository(db)
        edge_repo = EdgeRepository(db)

        total, services = await svc_repo.list_all(
            page=1,
            page_size=min(max(limit, 1), 20),
        )

        service_list = []
        for s in services:
            name = s.name or ""
            if query and query.lower() not in name.lower():
                continue

            service_list.append({
                "id": str(s.id),
                "name": name,
                "display_name": s.display_name or name,
                "language": s.language or "",
                "instances": s.instances or 0,
                "p99_latency_ms": s.p99_latency_ms or 0,
            })

        edges = await edge_repo.list_all()
        edge_list = []
        for e in edges[:50]:  # Cap edges
            edge_list.append({
                "id": str(e.id),
                "source": str(e.source_service_id) if e.source_service_id else "",
                "target": str(e.target_service_id) if e.target_service_id else "",
                "latency_ms": e.latency_ms or 0,
                "rps": e.rps or 0,
                "status": e.status or "healthy",
            })

        return {
            "found": total,
            "returned": len(service_list),
            "items": service_list,
            "edges": edge_list,
        }
