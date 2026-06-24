"""M6 APM — APMService, ServiceEdge, CrossLayerMapping models."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.base import Base
from app.core.database.event_mixin import EventRecordingMixin


class APMService(Base, EventRecordingMixin):
    __tablename__ = "apm_services"
    __event_resource_type__ = "apm_service"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    language: Mapped[str] = mapped_column(String(32), default="unknown")
    instances: Mapped[int] = mapped_column(Integer, default=1)
    host_ids: Mapped[list] = mapped_column(JSONB, default=list)
    p99_latency_ms: Mapped[float] = mapped_column(Float, default=0)
    error_rate_pct: Mapped[float] = mapped_column(Float, default=0)
    throughput_rps: Mapped[float] = mapped_column(Float, default=0)
    health: Mapped[str] = mapped_column(String(16), default="healthy")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ServiceEdge(Base, EventRecordingMixin):
    __tablename__ = "service_edges"
    __event_resource_type__ = "service_edge"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_service_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("apm_services.id"), nullable=False, index=True)
    target_service_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("apm_services.id"), nullable=False, index=True)
    latency_ms: Mapped[float] = mapped_column(Float, default=0)
    rps: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(16), default="healthy")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CrossLayerMapping(Base, EventRecordingMixin):
    __tablename__ = "cross_layer_mappings"
    __event_resource_type__ = "cross_layer_mapping"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("apm_services.id"), nullable=False, unique=True, index=True)
    host_ids: Mapped[list] = mapped_column(JSONB, default=list)
    switch_ids: Mapped[list] = mapped_column(JSONB, default=list)
    context: Mapped[dict] = mapped_column(JSONB, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
