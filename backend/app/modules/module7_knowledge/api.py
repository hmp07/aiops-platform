"""M7 Knowledge Base — API Endpoints."""
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.session import get_db
from app.core.middleware.auth import get_current_user
from app.core.middleware.permissions import require_permission
from app.modules.module7_knowledge.repository import ArticleRepository
from app.modules.module7_knowledge.schemas import (
    ArticleCreate, ArticleListResponse, ArticleResponse,
    ArticleUpdate, SearchRequest, SearchResponse,
)
from app.modules.module7_knowledge.service import KnowledgeService

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])

def _get_svc(db: AsyncSession = Depends(get_db)) -> KnowledgeService:
    return KnowledgeService(ArticleRepository(db))


@router.get("/articles", response_model=ArticleListResponse)
async def list_articles(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    article_type: str | None = None, keyword: str | None = None, tag: str | None = None,
    current_user: dict = Depends(get_current_user), svc: KnowledgeService = Depends(_get_svc)):
    total, items = await svc.list_articles(page, page_size, article_type, keyword, tag)
    return ArticleListResponse(total=total, items=items)

@router.post("/articles", response_model=ArticleResponse, status_code=201)
@require_permission("knowledge:article:create")
async def create_article(req: ArticleCreate, current_user: dict = Depends(get_current_user),
                         svc: KnowledgeService = Depends(_get_svc)):
    return await svc.create_article(req.model_dump())

@router.get("/articles/{article_id}", response_model=ArticleResponse)
async def get_article(article_id: UUID, current_user: dict = Depends(get_current_user),
                      svc: KnowledgeService = Depends(_get_svc)):
    return await svc.get_article(article_id)

@router.post("/articles/{article_id}/update", response_model=ArticleResponse)
@require_permission("knowledge:article:update")
async def update_article(article_id: UUID, req: ArticleUpdate,
    current_user: dict = Depends(get_current_user), svc: KnowledgeService = Depends(_get_svc)):
    return await svc.update_article(article_id, req.model_dump(exclude_none=True))

@router.post("/search", response_model=SearchResponse)
async def search(req: SearchRequest, current_user: dict = Depends(get_current_user),
                 svc: KnowledgeService = Depends(_get_svc)):
    total, items = await svc.search(req.keyword, req.article_type, req.limit)
    return SearchResponse(keyword=req.keyword, total=total, items=items)
