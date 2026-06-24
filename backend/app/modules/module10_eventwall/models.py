"""EventWall — Unified event store with TimescaleDB hypertables."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.base import Base


class EventRecord(Base):
    """Universal event record — 35+ fields covering all event types.

    Stored in TimescaleDB hypertable partitioned by `timestamp`.
    """

    __tablename__ = "eventwall_events"

    # -- Identity --
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    event_version: Mapped[int] = mapped_column(default=1)

    # -- Source --
    source_module: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_component: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # -- Timing --
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # -- Producer --
    producer_type: Mapped[str] = mapped_column(String(32), nullable=False, default="system")  # system|webhook|user|agent
    producer_user_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    producer_agent_session_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # -- Correlation (ties events into business flows) --
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    parent_event_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    root_event_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    fault_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    incident_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # -- Resource (what entity is this event about) --
    resource_type: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    resource_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    resource_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    resource_module: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # -- Classification --
    severity: Mapped[str] = mapped_column(String(16), nullable=False, default="info")  # info|debug|warning|critical|emergency
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="new")      # new|processing|completed|failed

    # -- Payloads --
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    tags: Mapped[dict] = mapped_column(JSONB, default=dict)
    metrics: Mapped[dict] = mapped_column(JSONB, default=dict)

    # -- Context --
    context_ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    context_user_agent: Mapped[str | None] = mapped_column(String(256), nullable=True)
    context_request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # -- Retention --
    retention_ttl_days: Mapped[int] = mapped_column(default=90)

    # -- Composite indexes for common query patterns --
    __table_args__ = (
        Index("ix_eventwall_resource_ts", "resource_type", "resource_id", "timestamp"),
        Index("ix_eventwall_correlation_ts", "correlation_id", "timestamp"),
        Index("ix_eventwall_fault_ts", "fault_id", "timestamp"),
        Index("ix_eventwall_type_module_ts", "event_type", "source_module", "timestamp"),
    )


class FaultCluster(Base):
    """Pre-computed fault clusters from the fault analysis engine.

    Stored in TimescaleDB hypertable partitioned by `created_at`.
    """

    __tablename__ = "eventwall_faults"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fault_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True, unique=True)
    score: Mapped[float] = mapped_column(default=0.0)
    event_ids: Mapped[list] = mapped_column(JSONB, default=list)
    event_count: Mapped[int] = mapped_column(default=0)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    top_event_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    affected_resources: Mapped[list] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_eventwall_faults_score", "score", "created_at"),
    )


class EventSource(Base):
    """Configurations for external event sources (webhooks, integrations)."""

    __tablename__ = "eventwall_sources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)  # zabbix|signoz|grafana|jenkins|gitlab|custom
    slug: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(default=True)
    auth_token_hash: Mapped[str | None] = mapped_column(String(256), nullable=True)
    transform_config: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
