"""M1 Asset — Business Logic."""
from uuid import UUID

from app.core.exceptions import NotFoundError
from app.modules.module1_asset.interfaces import ICalibrationService, IDeviceManageService, IDeviceQueryService
from app.modules.module1_asset.repository import CalibrationRepository, DeviceRepository

MOCK_CALIBRATION_FIELDS = ["serial_number", "software_version", "model"]


class DeviceQueryService(IDeviceQueryService):
    def __init__(self, repo: DeviceRepository):
        self._repo = repo

    async def get_device(self, device_id: UUID) -> dict | None:
        obj = await self._repo.get_by_id(device_id)
        return self._to_dict(obj) if obj else None

    async def list_devices(self, page: int = 1, page_size: int = 20,
                           device_type: str | None = None, vendor: str | None = None,
                           lifecycle_status: str | None = None, keyword: str | None = None,
                           ) -> tuple[int, list[dict]]:
        total, rows = await self._repo.list_devices(page, page_size, device_type, vendor, lifecycle_status, keyword)
        return total, [self._to_dict(r) for r in rows]

    async def find_by_ip(self, ip: str) -> dict | None:
        obj = await self._repo.find_by_ip(ip)
        return self._to_dict(obj) if obj else None

    def _to_dict(self, obj) -> dict:
        return {
            "id": obj.id, "device_name": obj.device_name, "device_type": obj.device_type,
            "vendor": obj.vendor, "model": obj.model, "serial_number": obj.serial_number,
            "software_version": obj.software_version, "management_ip": str(obj.management_ip) if obj.management_ip else None,
            "location": obj.location, "cabinet": obj.cabinet, "lifecycle_status": obj.lifecycle_status,
            "business_system": obj.business_system, "user_department": obj.user_department,
            "up_link_device_id": obj.up_link_device_id, "up_link_port": obj.up_link_port,
            "last_backup_status": obj.last_backup_status, "last_backup_at": obj.last_backup_at,
            "last_inspection_status": obj.last_inspection_status, "last_inspection_at": obj.last_inspection_at,
            "metadata": obj.extra_attrs, "created_at": obj.created_at, "updated_at": obj.updated_at,
        }


class DeviceManageService(IDeviceManageService):
    def __init__(self, repo: DeviceRepository, query_svc: DeviceQueryService):
        self._repo = repo
        self._query = query_svc

    async def create_device(self, data: dict) -> dict:
        obj = await self._repo.create(data)
        return self._query._to_dict(obj)

    async def update_device(self, device_id: UUID, data: dict) -> dict:
        obj = await self._repo.get_by_id(device_id)
        if not obj:
            raise NotFoundError("Device not found")
        obj = await self._repo.update(obj, data)
        return self._query._to_dict(obj)

    async def delete_device(self, device_id: UUID):
        obj = await self._repo.get_by_id(device_id)
        if not obj:
            raise NotFoundError("Device not found")
        await self._repo.soft_delete(obj)


class CalibrationService(ICalibrationService):
    def __init__(self, cal_repo: CalibrationRepository, device_repo: DeviceRepository):
        self._cal = cal_repo
        self._dev = device_repo

    async def list_reports(self, page: int = 1, page_size: int = 20,
                           device_id: UUID | None = None, status: str | None = None,
                           ) -> tuple[int, list[dict]]:
        total, rows = await self._cal.list_reports(page, page_size, device_id, status)
        return total, [self._to_dict(r) for r in rows]

    async def run_calibration(self, device_ids: list[UUID] | None = None, source: str = "snmp") -> list[dict]:
        """Mock calibration — in production this would call SNMP/SSH adapters."""
        if device_ids:
            devices = []
            for did in device_ids:
                d = await self._dev.get_by_id(did)
                if d:
                    devices.append(d)
        else:
            _, devices = await self._dev.list_devices(1, 100, None, None, "in_use", None)

        reports = []
        for d in devices[:10]:  # Limit to 10 devices per run
            import random
            field = random.choice(MOCK_CALIBRATION_FIELDS)
            current = getattr(d, field, "")
            discovered = f"{current}_SNMP_DISCOVERED" if random.random() > 0.5 else current
            r = await self._cal.create({
                "device_id": d.id, "source": source, "field_name": field,
                "current_value": current, "discovered_value": discovered,
                "status": "pending" if discovered != current else "confirmed",
            })
            reports.append(self._to_dict(r))
        return reports

    async def approve_report(self, report_id: UUID, status: str) -> dict:
        obj = await self._cal.get_by_id(report_id)
        if not obj:
            raise NotFoundError("Calibration report not found")
        obj = await self._cal.update(obj, {"status": status})
        # If confirmed, update the device field
        if status == "confirmed" and obj.discovered_value:
            device = await self._dev.get_by_id(obj.device_id)
            if device:
                await self._dev.update(device, {obj.field_name: obj.discovered_value})
        return self._to_dict(obj)

    def _to_dict(self, obj) -> dict:
        return {
            "id": obj.id, "device_id": obj.device_id, "source": obj.source,
            "field_name": obj.field_name, "current_value": obj.current_value,
            "discovered_value": obj.discovered_value, "status": obj.status,
            "created_at": obj.created_at,
        }
