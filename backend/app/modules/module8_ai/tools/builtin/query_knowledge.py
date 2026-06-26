"""Built-in tool: query_knowledge — real DB query."""
from app.modules.module8_ai.tools.base import BaseTool, ToolSpec


class QueryKnowledgeTool(BaseTool):
    spec = ToolSpec(
        tool_id="query_knowledge",
        name="Query Knowledge Base",
        description="Search the knowledge base for articles, runbooks, templates, "
                    "and emergency plans. Returns relevant articles with summaries.",
        parameters={
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "Search keyword"},
                "article_type": {"type": "string", "description": "case, template, emergency, faq"},
                "tag": {"type": "string", "description": "Filter by tag"},
                "limit": {"type": "integer", "description": "Max results (default 5)"},
            },
        },
        required_permissions=["knowledge:article:list"],
        risk_level="read_only",
        timeout_seconds=10,
        module="module7_knowledge",
    )

    async def execute(self, **kwargs) -> dict:
        from app.core.database.session import async_session_factory
        from app.modules.module7_knowledge.repository import ArticleRepository

        keyword = kwargs.get("keyword")
        article_type = kwargs.get("article_type")
        tag = kwargs.get("tag")
        limit = kwargs.get("limit", 5)

        async with async_session_factory() as db:
            repo = ArticleRepository(db)
            total, items = await repo.list_all(
                1, limit or 10, article_type or None, keyword, tag or None,
            )
            return {
                "found": total,
                "articles": [
                    {"id": str(a.id), "title": a.title, "type": a.article_type,
                     "tags": a.tags, "status": a.status,
                     "summary": a.content[:200] if a.content else ""}
                    for a in items[:limit or 10]
                ],
            }
