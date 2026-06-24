"""M7 Knowledge — Pydantic Schemas."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ArticleCreate(BaseModel):
    title: str; content: str; article_type: str = "case"
    tags: list = []; source: str = "manual"

class ArticleUpdate(BaseModel):
    title: str | None = None; content: str | None = None
    tags: list | None = None; status: str | None = None

class ArticleResponse(BaseModel):
    id: UUID; title: str; article_type: str; content: str
    tags: list; source: str; status: str; created_by: str | None = None
    created_at: datetime; updated_at: datetime
    model_config = {"from_attributes": True}

class ArticleListResponse(BaseModel): total: int; items: list[ArticleResponse]

class SearchRequest(BaseModel):
    keyword: str; article_type: str | None = None; limit: int = 10

class SearchResponse(BaseModel):
    keyword: str; total: int; items: list[ArticleResponse]
