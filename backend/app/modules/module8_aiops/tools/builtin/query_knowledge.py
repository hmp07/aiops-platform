"""Builtin MCP tool: query_knowledge.

Queries knowledge articles from Module 7 (Knowledge Base).
"""

import logging

from app.core.database.session import async_session_factory
from app.modules.module7_knowledge.repository import ArticleRepository

logger = logging.getLogger(__name__)

TOOL_DEFINITION = {
    "name": "aiops.query_knowledge",
    "title": "查询知识库",
    "description": "查询平台知识库中的文章、SOP 和 Runbook。支持按文章类型、标签和关键字过滤。",
    "handler_name": "query_knowledge",
    "permission": "knowledge:article:list",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索关键字，匹配标题和内容",
            },
            "article_type": {
                "type": "string",
                "description": "文章类型：sop / runbook / faq / reference",
            },
            "tag": {
                "type": "string",
                "description": "按标签过滤",
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


async def execute(
    query: str = "",
    article_type: str = "",
    tag: str = "",
    limit: int = 10,
) -> dict:
    """Execute query_knowledge tool."""
    async with async_session_factory() as db:
        repo = ArticleRepository(db)
        total, items = await repo.list_all(
            page=1,
            page_size=min(max(limit, 1), 20),
            article_type=article_type or None,
            keyword=query or None,
            tag=tag or None,
        )

        article_list = []
        for a in items:
            article_list.append({
                "id": str(a.id),
                "title": a.title or "",
                "type": a.article_type or "",
                "tags": a.tags if isinstance(a.tags, list) else [],
                "summary": (a.content or "")[:200],
                "created_at": a.created_at.isoformat() if a.created_at else "",
            })

        return {
            "found": total,
            "returned": len(article_list),
            "items": article_list,
        }
