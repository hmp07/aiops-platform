"""M8 AIOps — Knowledge Graph builder (sxdevops architecture, simplified).

Builds a runtime knowledge graph from existing platform data sources:
- Devices (Module 1 Asset) → infrastructure nodes
- Subnets (Module 2 IPAM) → network nodes
- Services (Module 6 APM) → application nodes + edges
- iTop dependency graph → CI relationship edges

No K8s/Docker real-time discovery — uses our existing data.
"""

import hashlib
import json
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import select

from app.core.database.session import async_session_factory

logger = logging.getLogger(__name__)

# Simple in-memory cache (TTL-based would be better but this suffices)
_graph_cache: Dict[str, dict] = {}

NODE_KIND_DEVICE = "device"
NODE_KIND_SUBNET = "subnet"
NODE_KIND_SERVICE = "service"
NODE_KIND_APPLICATION = "application"


async def build_knowledge_graph(
    environment: str = "",
    system: str = "",
    service: str = "",
    limit: int = 50,
) -> dict:
    """Build knowledge graph from platform data.

    Args:
        environment: Filter by environment (unused currently, reserved for future)
        system: Filter by business system
        service: Filter by service name
        limit: Max nodes per category

    Returns:
        {"nodes": [...], "edges": [...], "summary": {...}}
    """
    cache_key = _cache_key(environment, system, service, limit)
    if cache_key in _graph_cache:
        return _graph_cache[cache_key]

    nodes: list[dict] = []
    edges: list[dict] = []
    edge_ids: set[str] = set()

    async with async_session_factory() as db:
        # ── Device nodes ──────────────────────────────────────
        from app.modules.module1_asset.models import Device

        device_rows = (await db.execute(
            select(Device)
            .where(Device.deleted_at.is_(None))
            .limit(limit)
        )).scalars().all()

        for d in device_rows:
            if system and d.business_system != system:
                continue
            node_id = f"device:{d.id}"
            nodes.append({
                "id": node_id,
                "label": d.device_name,
                "kind": NODE_KIND_DEVICE,
                "category": d.device_type or "device",
                "status": d.lifecycle_status or "unknown",
                "metric": str(d.management_ip) if d.management_ip else "",
                "description": f"{d.vendor or ''} {d.model or ''}".strip(),
            })

            # Uplink edges
            if d.up_link_device_id:
                edge_id = f"uplink:{d.id}->{d.up_link_device_id}"
                if edge_id not in edge_ids:
                    edge_ids.add(edge_id)
                    edges.append({
                        "id": edge_id,
                        "source": node_id,
                        "target": f"device:{d.up_link_device_id}",
                        "label": "uplink",
                        "relation": "uplink",
                    })

        # ── Subnet nodes ──────────────────────────────────────
        from app.modules.module2_ipam.models import Subnet

        subnet_rows = (await db.execute(
            select(Subnet).limit(limit)
        )).scalars().all()

        for s in subnet_rows:
            node_id = f"subnet:{s.id}"
            nodes.append({
                "id": node_id,
                "label": s.cidr or str(s.id)[:12],
                "kind": NODE_KIND_SUBNET,
                "category": "subnet",
                "status": "active",
                "metric": f"{s.used_ips or 0}/{s.total_ips or 0} IPs",
                "description": s.description or "",
            })

        # ── Service nodes + edges ─────────────────────────────
        from app.modules.module6_apm.models import APMService, ServiceEdge

        svc_rows = (await db.execute(
            select(APMService).limit(limit)
        )).scalars().all()

        svc_id_map: dict = {}
        for s in svc_rows:
            if service and service.lower() not in (s.name or "").lower():
                continue
            node_id = f"service:{s.id}"
            svc_id_map[str(s.id)] = node_id
            nodes.append({
                "id": node_id,
                "label": s.display_name or s.name,
                "kind": NODE_KIND_SERVICE,
                "category": s.language or "service",
                "status": "active",
                "metric": f"{s.instances or 0} instances, p99={s.p99_latency_ms or 0}ms",
                "description": "",
            })

        # Service edges
        edge_rows = (await db.execute(
            select(ServiceEdge).limit(limit * 2)
        )).scalars().all()

        for e in edge_rows:
            src = svc_id_map.get(str(e.source_service_id))
            tgt = svc_id_map.get(str(e.target_service_id))
            if src and tgt:
                edge_id = f"svc:{e.id}"
                if edge_id not in edge_ids:
                    edge_ids.add(edge_id)
                    edges.append({
                        "id": edge_id,
                        "source": src,
                        "target": tgt,
                        "label": f"{e.rps or 0}rps",
                        "relation": "dependency",
                    })

        # ── iTop dependency graph ─────────────────────────────
        try:
            from app.modules.module6_apm.dependency_graph import build_dependency_graph
            from app.integrations.itop.client import ItopAdapter
            itop = ItopAdapter()
            itop_graph = await build_dependency_graph(itop)
            if itop_graph and itop_graph.get("nodes"):
                for node in itop_graph.get("nodes", [])[:limit]:
                    node["kind"] = NODE_KIND_APPLICATION
                    if node["id"] not in {n["id"] for n in nodes}:
                        nodes.append(node)
                for edge in itop_graph.get("edges", [])[:limit * 2]:
                    if edge["id"] not in edge_ids:
                        edge_ids.add(edge["id"])
                        edges.append(edge)
        except Exception:
            logger.debug("iTop dependency graph unavailable, skipping")

    summary = {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "device_count": sum(1 for n in nodes if n["kind"] == NODE_KIND_DEVICE),
        "subnet_count": sum(1 for n in nodes if n["kind"] == NODE_KIND_SUBNET),
        "service_count": sum(1 for n in nodes if n["kind"] == NODE_KIND_SERVICE),
    }

    result = {
        "nodes": nodes,
        "edges": edges,
        "summary": summary,
        "filters": {
            "environment": environment,
            "system": system,
            "service": service,
        },
    }

    # Cache result
    _graph_cache[cache_key] = result
    if len(_graph_cache) > 20:
        _graph_cache.pop(next(iter(_graph_cache)))

    return result


def _cache_key(environment: str, system: str, service: str, limit: int) -> str:
    raw = json.dumps([environment, system, service, limit], sort_keys=True)
    return hashlib.md5(raw.encode()).hexdigest()
