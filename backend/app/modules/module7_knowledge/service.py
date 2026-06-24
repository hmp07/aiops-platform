"""M7 Knowledge — Business Logic."""
from uuid import UUID

from app.core.exceptions import NotFoundError
from app.modules.module7_knowledge.repository import ArticleRepository


class KnowledgeService:
    def __init__(self, repo: ArticleRepository): self._repo = repo

    async def list_articles(self, page=1, page_size=20, article_type=None, keyword=None, tag=None) -> tuple[int, list[dict]]:
        total, rows = await self._repo.list_all(page, page_size, article_type, keyword, tag)
        return total, [self._to_dict(r) for r in rows]

    async def create_article(self, data: dict) -> dict:
        obj = await self._repo.create(data)
        return self._to_dict(obj)

    async def get_article(self, aid: UUID) -> dict:
        obj = await self._repo.get_by_id(aid)
        if not obj: raise NotFoundError("Article not found")
        return self._to_dict(obj)

    async def update_article(self, aid: UUID, data: dict) -> dict:
        obj = await self._repo.get_by_id(aid)
        if not obj: raise NotFoundError("Article not found")
        return self._to_dict(await self._repo.update(obj, data))

    async def search(self, keyword: str, article_type=None, limit=10) -> tuple[int, list[dict]]:
        total, rows = await self._repo.list_all(1, limit, article_type, keyword, None)
        return total, [self._to_dict(r) for r in rows]

    async def auto_archive(self, alert_data: dict) -> dict | None:
        """G7.9: Generate case draft from resolved alert."""
        title = f"Case: {alert_data.get('title', 'Unknown Alert')}"
        content = f"## Alert Summary\n{alert_data.get('description', '')}\n\n## Resolution\n*Auto-generated draft — please edit.*"
        obj = await self._repo.create({
            "title": title, "content": content, "article_type": "case",
            "source": "auto_archive", "status": "draft",
            "tags": ["auto-generated"],
        })
        return self._to_dict(obj)

    def _to_dict(self, obj) -> dict:
        return {"id": obj.id, "title": obj.title, "article_type": obj.article_type,
                "content": obj.content, "tags": obj.tags, "source": obj.source,
                "status": obj.status, "created_by": obj.created_by,
                "created_at": obj.created_at, "updated_at": obj.updated_at}
