from fastapi import APIRouter

from mock_data import KNOWLEDGE_ARTICLES

router = APIRouter(tags=["Knowledge"])


@router.get("/knowledge/articles")
async def list_articles(page: int = 1, page_size: int = 20, article_type: str = "", keyword: str = "", tag: str = ""):
    items = KNOWLEDGE_ARTICLES
    if article_type:
        items = [a for a in items if a["article_type"] == article_type]
    if keyword:
        kw = keyword.lower()
        items = [a for a in items if kw in a["title"].lower() or kw in a["content"].lower()]
    if tag:
        items = [a for a in items if tag in a.get("tags", [])]
    return {"total": len(items), "items": items}


@router.get("/knowledge/articles/{article_id}")
async def get_article(article_id: str):
    for a in KNOWLEDGE_ARTICLES:
        if a["id"] == article_id:
            return a
    return None


@router.get("/knowledge/stats")
async def knowledge_stats():
    return {
        "total": len(KNOWLEDGE_ARTICLES),
        "by_type": {
            "case": len([a for a in KNOWLEDGE_ARTICLES if a["article_type"] == "case"]),
            "template": len([a for a in KNOWLEDGE_ARTICLES if a["article_type"] == "template"]),
            "emergency": len([a for a in KNOWLEDGE_ARTICLES if a["article_type"] == "emergency"]),
            "faq": len([a for a in KNOWLEDGE_ARTICLES if a["article_type"] == "faq"]),
        },
        "published": len([a for a in KNOWLEDGE_ARTICLES if a["status"] == "published"]),
        "draft": len([a for a in KNOWLEDGE_ARTICLES if a["status"] == "draft"]),
    }
