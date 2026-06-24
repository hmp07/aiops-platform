"""M2 IPAM — Subnet and IPAllocation models."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import INET, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.base import Base
from app.core.database.event_mixin import EventRecordingMixin


class Subnet(Base, EventRecordingMixin):
    __tablename__ = "subnets"
    __event_resource_type__ = "subnet"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cidr: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    vlan_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gateway: Mapped[str | None] = mapped_column(INET, nullable=True)
    description: Mapped[str | None] = mapped_column(String(256), nullable=True)
    total_ips: Mapped[int] = mapped_column(Integer, default=0)
    used_ips: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class IPAllocation(Base, EventRecordingMixin):
    __tablename__ = "ip_allocations"
    __event_resource_type__ = "ip_allocation"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subnet_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("subnets.id"), nullable=False, index=True)
    ip_address: Mapped[str] = mapped_column(INET, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="free")
    device_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=True)
    interface_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="manual")
    allocated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
