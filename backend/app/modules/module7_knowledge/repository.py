"""M7 Knowledge — Data Access Layer."""
from uuid import UUID

from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.module7_knowledge.models import KnowledgeArticle


class ArticleRepository:
    def __init__(self, session: AsyncSession): self._s = session
    async def create(self, data: dict) -> KnowledgeArticle:
        obj = KnowledgeArticle(**data); self._s.add(obj); await self._s.commit(); await self._s.refresh(obj); return obj
    async def get_by_id(self, aid: UUID) -> KnowledgeArticle | None: return await self._s.get(KnowledgeArticle, aid)
    async def list_all(self, page, page_size, article_type, keyword, tag) -> tuple[int, list[KnowledgeArticle]]:
        q = select(KnowledgeArticle); cq = select(func.count(KnowledgeArticle.id))
        if article_type: q = q.where(KnowledgeArticle.article_type == article_type); cq = cq.where(KnowledgeArticle.article_type == article_type)
        if keyword:
            kw = f"%{keyword}%"
            filt = or_(KnowledgeArticle.title.ilike(kw), KnowledgeArticle.content.ilike(kw))
            q = q.where(filt); cq = cq.where(filt)
        if tag: q = q.where(KnowledgeArticle.tags.contains([tag])); cq = cq.where(KnowledgeArticle.tags.contains([tag]))
        q = q.order_by(KnowledgeArticle.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        total = (await self._s.execute(cq)).scalar() or 0
        rows = (await self._s.execute(q)).scalars().all(); return total, list(rows)
    async def update(self, obj: KnowledgeArticle, data: dict) -> KnowledgeArticle:
        for k, v in data.items():
            if v is not None: setattr(obj, k, v)
        await self._s.commit(); await self._s.refresh(obj); return obj
