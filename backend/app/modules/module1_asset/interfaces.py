"""M1 Asset — Abstract Interfaces."""
from abc import ABC, abstractmethod
from uuid import UUID


class IDeviceQueryService(ABC):
    @abstractmethod
    async def get_device(self, device_id: UUID) -> dict | None: ...
    @abstractmethod
    async def list_devices(self, page: int, page_size: int, device_type: str | None,
                           vendor: str | None, lifecycle_status: str | None,
                           keyword: str | None) -> tuple[int, list[dict]]: ...
    @abstractmethod
    async def find_by_ip(self, ip: str) -> dict | None: ...


class IDeviceManageService(ABC):
    @abstractmethod
    async def create_device(self, data: dict) -> dict: ...
    @abstractmethod
    async def update_device(self, device_id: UUID, data: dict) -> dict: ...
    @abstractmethod
    async def delete_device(self, device_id: UUID): ...


class ICalibrationService(ABC):
    @abstractmethod
    async def list_reports(self, page: int, page_size: int, device_id: UUID | None,
                           status: str | None) -> tuple[int, list[dict]]: ...
    @abstractmethod
    async def run_calibration(self, device_ids: list[UUID] | None, source: str) -> list[dict]: ...
    @abstractmethod
    async def approve_report(self, report_id: UUID, status: str) -> dict: ...
