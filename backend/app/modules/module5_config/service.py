"""M5 Config — Business Logic."""
import random
import string
from datetime import datetime, timezone
from uuid import UUID

from app.core.exceptions import NotFoundError
from app.modules.module5_config.diff_engine import compute_diff, compute_hash, compute_risk_level
from app.modules.module5_config.repository import BackupRepository, BatchRepository, DiffRepository


class ConfigBackupService:
    def __init__(self, repo: BackupRepository):
        self._repo = repo

    async def list_backups(self, page: int = 1, page_size: int = 20,
                           device_id: UUID | None = None, status: str | None = None,
                           ) -> tuple[int, list[dict]]:
        total, rows = await self._repo.list_all(page, page_size, device_id, status)
        return total, [self._to_dict(r) for r in rows]

    async def trigger_backup(self, device_ids: list[UUID] | None = None) -> list[dict]:
        """Mock backup — generates random config text and computes hash."""
        if device_ids:
            devices = device_ids
        else:
            # Get first device from DB as default target
            from app.modules.module1_asset.repository import DeviceRepository
            from app.core.database.session import async_session_factory
            async with async_session_factory() as db:
                repo = DeviceRepository(db)
                _, rows = await repo.list_devices(1, 1, None, None, None, None)
                devices = [r.id for r in rows] if rows else []
        if not devices:
            return []
        results = []
        for did in devices:
            config_text = "hostname mock-device\n" + "".join(
                random.choices(string.ascii_letters, k=200)
            )
            hash_val = compute_hash(config_text)
            obj = await self._repo.create({
                "device_id": did, "backup_type": "manual", "status": "success",
                "file_size": len(config_text), "config_hash": hash_val,
            })
            results.append(self._to_dict(obj))
        return results

    def _to_dict(self, obj) -> dict:
        return {
            "id": obj.id, "device_id": obj.device_id, "backup_type": obj.backup_type,
            "status": obj.status, "file_size": obj.file_size, "file_path": obj.file_path,
            "config_hash": obj.config_hash, "backup_at": obj.backup_at, "created_at": obj.created_at,
        }


class ConfigDiffService:
    def __init__(self, diff_repo: DiffRepository, backup_repo: BackupRepository):
        self._repo = diff_repo
        self._backup = backup_repo

    async def list_diffs(self, page: int = 1, page_size: int = 20,
                         device_id: UUID | None = None) -> tuple[int, list[dict]]:
        total, rows = await self._repo.list_all(page, page_size, device_id)
        return total, [self._to_dict(r) for r in rows]

    async def get_diff(self, device_id: UUID) -> dict | None:
        """Get latest diff for a device, or generate mock if none exists."""
        total, rows = await self._repo.list_all(1, 1, device_id)
        if rows:
            return self._to_dict(rows[0])
        # Generate mock diff
        old_config = "hostname device-v1\ninterface Gi1/0/1\n description Old\n"
        new_config = "hostname device-v1\ninterface Gi1/0/1\n shutdown\n description New\n"
        diff_content = compute_diff(old_config, new_config)
        risk = compute_risk_level(diff_content)
        obj = await self._repo.create({
            "device_id": device_id,
            "old_backup_id": UUID("00000000-0000-0000-0000-000000000001"),
            "new_backup_id": UUID("00000000-0000-0000-0000-000000000002"),
            "diff_content": diff_content, "risk_level": risk,
        })
        return self._to_dict(obj)

    def _to_dict(self, obj) -> dict:
        return {
            "id": obj.id, "device_id": obj.device_id,
            "old_backup_id": obj.old_backup_id, "new_backup_id": obj.new_backup_id,
            "diff_content": obj.diff_content, "risk_level": obj.risk_level,
            "created_at": obj.created_at,
        }
