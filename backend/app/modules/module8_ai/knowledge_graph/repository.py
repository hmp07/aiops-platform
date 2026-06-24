"""M8 Knowledge Graph — Data Access Layer."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.module8_ai.knowledge_graph.models import GraphEdge, GraphNode


class GraphRepository:
    def __init__(self, session: AsyncSession): self._s = session

    async def create_node(self, data: dict) -> GraphNode:
        obj = GraphNode(**data); self._s.add(obj); await self._s.commit(); await self._s.refresh(obj); return obj

    async def create_edge(self, data: dict) -> GraphEdge:
        obj = GraphEdge(**data); self._s.add(obj); await self._s.commit(); await self._s.refresh(obj); return obj

    async def get_node(self, nid: UUID) -> GraphNode | None: return await self._s.get(GraphNode, nid)

    async def list_nodes(self, entity_type: str | None = None) -> list[GraphNode]:
        q = select(GraphNode);
        if entity_type: q = q.where(GraphNode.entity_type == entity_type)
        rows = (await self._s.execute(q)).scalars().all(); return list(rows)

    async def list_edges(self) -> list[GraphEdge]:
        rows = (await self._s.execute(select(GraphEdge))).scalars().all(); return list(rows)

    async def get_edges_for_node(self, node_id: UUID) -> list[GraphEdge]:
        from sqlalchemy import or_
        q = select(GraphEdge).where(or_(GraphEdge.source_node_id == node_id, GraphEdge.target_node_id == node_id))
        rows = (await self._s.execute(q)).scalars().all(); return list(rows)
