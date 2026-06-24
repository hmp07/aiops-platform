"""M8 Knowledge Graph — API Endpoints."""
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.session import get_db
from app.core.middleware.auth import get_current_user
from app.modules.module8_ai.knowledge_graph.repository import GraphRepository

router = APIRouter(prefix="/knowledge-graph", tags=["Knowledge Graph"])

def _get_repo(db: AsyncSession = Depends(get_db)) -> GraphRepository:
    return GraphRepository(db)


@router.get("/nodes")
async def list_nodes(entity_type: str | None = None, current_user: dict = Depends(get_current_user),
                     repo: GraphRepository = Depends(_get_repo)):
    nodes = await repo.list_nodes(entity_type)
    return {"total": len(nodes), "items": [{"id": n.id, "entity_type": n.entity_type,
        "entity_id": n.entity_id, "module": n.module, "label": n.label,
        "metadata": n.extra} for n in nodes]}

@router.get("/edges")
async def list_edges(current_user: dict = Depends(get_current_user),
                     repo: GraphRepository = Depends(_get_repo)):
    edges = await repo.list_edges()
    return {"total": len(edges), "items": [{"id": e.id, "source_node_id": str(e.source_node_id),
        "target_node_id": str(e.target_node_id), "relationship_type": e.relationship_type} for e in edges]}

@router.get("/subgraph/{entity_id}")
async def get_subgraph(entity_id: UUID, depth: int = Query(1, ge=1, le=3),
    current_user: dict = Depends(get_current_user), repo: GraphRepository = Depends(_get_repo)):
    # Simple: return node + directly connected edges
    node = await repo.get_node(entity_id)
    if not node: return {"node": None, "edges": [], "neighbors": []}
    edges = await repo.get_edges_for_node(entity_id)
    neighbor_ids = [e.target_node_id for e in edges if e.source_node_id == entity_id]
    neighbor_ids += [e.source_node_id for e in edges if e.target_node_id == entity_id]
    neighbors = []
    for nid in neighbor_ids[:20]:
        n = await repo.get_node(nid)
        if n: neighbors.append({"id": str(n.id), "label": n.label, "entity_type": n.entity_type})
    return {"node": {"id": str(node.id), "label": node.label, "entity_type": node.entity_type},
            "edges": [{"source": str(e.source_node_id), "target": str(e.target_node_id),
                       "type": e.relationship_type} for e in edges],
            "neighbors": neighbors}
