"""M6 APM — API Endpoints."""
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.session import get_db
from app.core.middleware.auth import get_current_user
from app.core.middleware.permissions import require_permission
from app.modules.module6_apm.repository import CrossLayerRepository, EdgeRepository, ServiceRepository
from app.modules.module6_apm.schemas import (
    CrossLayerResponse, EdgeCreate, EdgeResponse, ServiceCreate,
    ServiceListResponse, ServiceResponse, ServiceUpdate, TopologyResponse,
)
from app.modules.module6_apm.service import APMService as APMServiceLayer

router = APIRouter(prefix="/apm", tags=["APM"])

def _get_svc(db: AsyncSession = Depends(get_db)) -> APMServiceLayer:
    return APMServiceLayer(ServiceRepository(db), EdgeRepository(db), CrossLayerRepository(db))


@router.get("/services", response_model=ServiceListResponse)
async def list_services(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user), svc: APMServiceLayer = Depends(_get_svc)):
    total, items = await svc.list_services(page, page_size)
    return ServiceListResponse(total=total, items=items)

@router.post("/services", response_model=ServiceResponse, status_code=201)
@require_permission("apm:service:create")
async def create_service(req: ServiceCreate, current_user: dict = Depends(get_current_user),
                         svc: APMServiceLayer = Depends(_get_svc)):
    return await svc.create_service(req.model_dump())

@router.get("/services/{service_id}", response_model=ServiceResponse)
async def get_service(service_id: UUID, current_user: dict = Depends(get_current_user),
                      svc: APMServiceLayer = Depends(_get_svc)):
    return await svc.get_service(service_id)

@router.post("/services/{service_id}/update", response_model=ServiceResponse)
@require_permission("apm:service:update")
async def update_service(service_id: UUID, req: ServiceUpdate,
    current_user: dict = Depends(get_current_user), svc: APMServiceLayer = Depends(_get_svc)):
    return await svc.update_service(service_id, req.model_dump(exclude_none=True))

@router.post("/topology/refresh")
@require_permission("apm:topology:create")
async def refresh_topology_from_itop(
    current_user: dict = Depends(get_current_user),
):
    """Refresh service dependency topology from iTop."""
    from app.core.database.session import async_session_factory
    from app.modules.module11_scheduler.repository import DataSourceRepository
    from app.modules.module11_scheduler.service import DataSourceService
    from app.modules.module6_apm.dependency_graph import build_dependency_graph

    async with async_session_factory() as db:
        ds_repo = DataSourceRepository(db)
        ds_svc = DataSourceService(ds_repo)
        itop_adapter = None
        for ds_obj in await ds_svc.list_all():
            if ds_obj.get("source_type") == "itop" and ds_obj.get("is_enabled"):
                itop_adapter = ds_svc._get_adapter(
                    await ds_repo.get_by_id(ds_obj["id"])
                )
                break

        if not itop_adapter:
            return {"status": "error", "message": "No enabled iTop datasource found"}

        graph = await build_dependency_graph(itop_adapter)
        return {
            "status": "ok",
            "nodes": len(graph.get("nodes", [])),
            "edges": len(graph.get("edges", [])),
            "graph": graph,
        }


@router.get("/topology/app/{app_name}")
async def get_app_topology(
    app_name: str,
    current_user: dict = Depends(get_current_user),
):
    """Get dependency topology for a specific application."""
    from app.core.database.session import async_session_factory
    from app.modules.module11_scheduler.repository import DataSourceRepository
    from app.modules.module11_scheduler.service import DataSourceService
    from app.modules.module6_apm.dependency_graph import build_dependency_graph

    async with async_session_factory() as db:
        ds_repo = DataSourceRepository(db)
        ds_svc = DataSourceService(ds_repo)
        itop_adapter = None
        for ds_obj in await ds_svc.list_all():
            if ds_obj.get("source_type") == "itop" and ds_obj.get("is_enabled"):
                itop_adapter = ds_svc._get_adapter(
                    await ds_repo.get_by_id(ds_obj["id"])
                )
                break

        if not itop_adapter:
            return {"status": "error", "message": "No enabled iTop datasource found"}

        full_graph = await build_dependency_graph(itop_adapter)

        # Filter: find the app node and its connected subgraph
        app_node_id = f"ApplicationSolution:{app_name}"
        app_node = None
        for n in full_graph.get("nodes", []):
            if n.get("label") == app_name or n.get("id", "").endswith(f":{app_name}"):
                app_node = n
                break

        if not app_node:
            return {"status": "error", "message": f"Application '{app_name}' not found"}

        # Collect reachable nodes from app
        reachable = _reachable_subgraph(full_graph, app_node["id"])
        return {
            "status": "ok",
            "app": app_name,
            "nodes": len(reachable["nodes"]),
            "edges": len(reachable["edges"]),
            "graph": reachable,
        }


def _reachable_subgraph(graph: dict, root_id: str) -> dict:
    """Extract the subgraph reachable from root_id via BFS."""
    node_map = {n["id"]: n for n in graph.get("nodes", [])}
    edges = graph.get("edges", [])
    adj: dict[str, list[str]] = {}
    for e in edges:
        adj.setdefault(e["source"], []).append(e["target"])

    visited: set[str] = set()
    queue = [root_id]
    while queue:
        nid = queue.pop(0)
        if nid in visited:
            continue
        visited.add(nid)
        for tgt in adj.get(nid, []):
            if tgt not in visited:
                queue.append(tgt)

    sub_nodes = [node_map[nid] for nid in visited if nid in node_map]
    sub_edges = [e for e in edges if e["source"] in visited and e["target"] in visited]
    return {"nodes": sub_nodes, "edges": sub_edges}


@router.get("/topology", response_model=TopologyResponse)
async def get_topology(current_user: dict = Depends(get_current_user),
                       svc: APMServiceLayer = Depends(_get_svc)):
    return await svc.get_topology()

@router.post("/topology/edges", response_model=EdgeResponse, status_code=201)
@require_permission("apm:topology:create")
async def add_edge(req: EdgeCreate, current_user: dict = Depends(get_current_user),
                   svc: APMServiceLayer = Depends(_get_svc)):
    return await svc.add_edge(req.model_dump())

@router.get("/cross-layer/{service_id}", response_model=CrossLayerResponse)
async def get_cross_layer(service_id: UUID, current_user: dict = Depends(get_current_user),
                          svc: APMServiceLayer = Depends(_get_svc)):
    return await svc.get_cross_layer(service_id)
