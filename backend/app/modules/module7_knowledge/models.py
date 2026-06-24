"""M7 Knowledge Base — KnowledgeArticle with pgvector embedding."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
try:
    from pgvector.sqlalchemy import Vector
    HAS_PGVECTOR = True
except ImportError:
    from sqlalchemy import JSON as _JSON
    Vector = None
    HAS_PGVECTOR = False

from app.core.database.base import Base
from app.core.database.event_mixin import EventRecordingMixin


class KnowledgeArticle(Base, EventRecordingMixin):
    __tablename__ = "knowledge_articles"
    __event_resource_type__ = "knowledge_article"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    article_type: Mapped[str] = mapped_column(String(32), nullable=False, default="case")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[list] = mapped_column(JSONB, default=list)
    source: Mapped[str] = mapped_column(String(32), default="manual")
    status: Mapped[str] = mapped_column(String(16), default="published")
    embedding: Mapped[list | None] = mapped_column(
        Vector(1536) if HAS_PGVECTOR else _JSON, nullable=True
    )
    created_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
