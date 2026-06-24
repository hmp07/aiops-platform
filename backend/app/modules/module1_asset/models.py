"""M1 Asset — Device and CalibrationReport models."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.base import Base
from app.core.database.event_mixin import EventRecordingMixin


class Device(Base, EventRecordingMixin):
    __tablename__ = "devices"
    __event_resource_type__ = "device"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    device_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # switch/router/firewall/server
    vendor: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    serial_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    software_version: Mapped[str | None] = mapped_column(String(128), nullable=True)
    management_ip: Mapped[str | None] = mapped_column(INET, nullable=True)
    location: Mapped[str | None] = mapped_column(String(256), nullable=True)
    cabinet: Mapped[str | None] = mapped_column(String(64), nullable=True)
    lifecycle_status: Mapped[str] = mapped_column(String(32), nullable=False, default="in_use")
    business_system: Mapped[str | None] = mapped_column(String(128), nullable=True)
    user_department: Mapped[str | None] = mapped_column(String(128), nullable=True)
    up_link_device_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=True)
    up_link_port: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_backup_status: Mapped[str | None] = mapped_column(String(16), nullable=True)
    last_backup_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_inspection_status: Mapped[str | None] = mapped_column(String(16), nullable=True)
    last_inspection_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    extra_attrs: Mapped[dict] = mapped_column("extra_attrs", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CalibrationReport(Base, EventRecordingMixin):
    __tablename__ = "calibration_reports"
    __event_resource_type__ = "calibration"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False)  # snmp/ssh/itop
    field_name: Mapped[str] = mapped_column(String(64), nullable=False)
    current_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    discovered_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")  # pending/confirmed/rejected
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
