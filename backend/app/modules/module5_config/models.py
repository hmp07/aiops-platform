"""M5 Config — ConfigBackup, ConfigDiff, BatchOperation models."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.base import Base
from app.core.database.event_mixin import EventRecordingMixin


class ConfigBackup(Base, EventRecordingMixin):
    __tablename__ = "config_backups"
    __event_resource_type__ = "config_backup"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=False, index=True)
    backup_type: Mapped[str] = mapped_column(String(16), nullable=False, default="scheduled")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="success")
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    file_path: Mapped[str | None] = mapped_column(String(256), nullable=True)
    config_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    backup_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ConfigDiff(Base, EventRecordingMixin):
    __tablename__ = "config_diffs"
    __event_resource_type__ = "config_diff"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=False, index=True)
    old_backup_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("config_backups.id"), nullable=False)
    new_backup_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("config_backups.id"), nullable=False)
    diff_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_level: Mapped[str] = mapped_column(String(16), nullable=False, default="normal")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BatchOperation(Base, EventRecordingMixin):
    __tablename__ = "batch_operations"
    __event_resource_type__ = "batch_operation"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    operation_type: Mapped[str] = mapped_column(String(32), nullable=False)
    device_ids: Mapped[list] = mapped_column(JSONB, default=list)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    result_summary: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
