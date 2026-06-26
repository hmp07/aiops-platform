"""Builtin MCP tool: query_ipam.

Queries IP address management data from Module 2 (IPAM).
"""

import logging

from app.core.database.session import async_session_factory
from app.modules.module2_ipam.repository import SubnetRepository, IPAllocationRepository

logger = logging.getLogger(__name__)

TOOL_DEFINITION = {
    "name": "aiops.query_ipam",
    "title": "查询 IP 地址管理",
    "description": "查询平台 IP 地址管理中的子网和 IP 分配信息。支持搜索子网和 IP 地址。",
    "handler_name": "query_ipam",
    "permission": "ipam:subnet:list",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索关键字，匹配子网名称或 CIDR",
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


async def execute(query: str = "", limit: int = 10) -> dict:
    """Execute query_ipam tool."""
    async with async_session_factory() as db:
        subnet_repo = SubnetRepository(db)
        total, subnets = await subnet_repo.list_all(
            page=1,
            page_size=min(max(limit, 1), 20),
        )

        subnet_list = []
        for s in subnets:
            cidr = s.cidr or ""
            # Filter by query if provided
            desc = s.description or ""
            if query and query.lower() not in cidr.lower() and query.lower() not in desc.lower():
                continue

            subnet_list.append({
                "id": str(s.id),
                "name": cidr,
                "cidr": cidr,
                "gateway": str(s.gateway) if s.gateway else "",
                "vlan_id": s.vlan_id or 0,
                "total_ips": s.total_ips or 0,
                "used_ips": s.used_ips or 0,
                "description": desc[:200],
            })

        return {
            "found": total,
            "returned": len(subnet_list),
            "items": subnet_list,
        }
