"""iTop CMDB REST API adapter.

Authentication uses form-field ``auth_user`` + ``auth_pwd`` embedded
in the POST body together with ``json_data`` — NOT HTTP Basic Auth.
Reference: itop-clinet project (Go client + Python test scripts).
"""
import json as _json
from datetime import datetime, timezone

from app.integrations.base import BaseAdapter


# ── iTop class → AIOps device_type mapping ──
CLASS_TYPE_MAP: dict[str, str] = {
    "Server": "server",
    "NetworkDevice": "switch",
    "StorageSystem": "storage",
    "VirtualMachine": "vm",
    "PC": "desktop",
    "Printer": "printer",
}

# CI classes to sync
SYNC_CLASSES = ["Server", "NetworkDevice", "StorageSystem", "VirtualMachine"]


class ItopAdapter(BaseAdapter):
    """iTop CMDB adapter.

    Connects to iTop REST/JSON API to pull Configuration Items (CIs)
    and map them to AIOps Device records.
    """

    def __init__(self, endpoint_url: str = "", auth_config: dict | None = None):
        base = (endpoint_url or "").rstrip("/")
        self._url = f"{base}/webservices/rest.php"
        auth = auth_config or {}
        self._user = auth.get("username") or auth.get("user", "")
        self._password = auth.get("password", "")
        self._version = "1.4"

    # ── public API ────────────────────────────────────────────

    async def health_check(self) -> bool:
        """Verify connectivity by calling list_operations."""
        if not self._url:
            return False
        try:
            result = await self._call({"operation": "list_operations"})
            return result.get("code") == 0
        except Exception:
            return False

    async def get_cis(
        self, ci_class: str = "Server", limit: int = 100, page: int = 1,
    ) -> list[dict]:
        """Fetch a page of CIs for the given class.

        Returns a flat list of field dicts (the ``fields`` block from
        each ``"Class::ID"`` entry in the iTop response).
        """
        payload: dict = {
            "operation": "core/get",
            "class": ci_class,
            "key": f"SELECT {ci_class}",
            "output_fields": "*",
        }
        if limit:
            payload["limit"] = limit
        if page > 1:
            payload["page"] = page

        result = await self._call(payload)
        return self._parse_objects(result, ci_class)

    async def sync(self, db_session=None) -> dict:
        """Sync iTop CIs → AIOps Device records."""
        import uuid as _uuid

        total_synced = 0
        details: dict[str, int] = {}

        if db_session:
            from app.modules.module1_asset.models import Device
            from sqlalchemy import select

            try:
                for ci_class in SYNC_CLASSES:
                    cis = await self.get_cis(ci_class, limit=200)
                    class_synced = 0

                    for ci in cis:
                        name = ci.get("name", "")
                        if not name:
                            continue

                        ci_id = ci.get("id", "")
                        finalclass = ci.get("finalclass") or ci_class

                        # Dedup by name + extra_attrs.ci_class
                        existing = (await db_session.execute(
                            select(Device).where(
                                Device.device_name == name,
                                Device.extra_attrs["ci_class"].as_string() == ci_class,
                            )
                        )).scalar_one_or_none()

                        if not existing:
                            dev = Device(
                                id=_uuid.uuid4(),
                                device_name=name,
                                device_type=self._map_type(finalclass, ci),
                                vendor=ci.get("brand_name") or "",
                                model=ci.get("model_name") or "",
                                serial_number=ci.get("serialnumber"),
                                software_version=ci.get("osversion_name"),
                                location=ci.get("location_name"),
                                lifecycle_status=self._map_status(ci.get("status", "")),
                                business_system=ci.get("business_criticity") or ci.get("organization_name"),
                                user_department=ci.get("organization_name"),
                                extra_attrs={
                                    "source": "itop",
                                    "ci_class": ci_class,
                                    "ci_id": ci_id,
                                    "finalclass": finalclass,
                                    **{k: v for k, v in ci.items()
                                       if v is not None and k not in (
                                           "id", "name", "brand_name", "model_name",
                                           "serialnumber", "osversion_name", "location_name",
                                           "status", "business_criticity", "organization_name",
                                           "finalclass",
                                       )},
                                },
                            )
                            db_session.add(dev)
                            class_synced += 1

                    total_synced += class_synced
                    details[ci_class] = class_synced

                if total_synced > 0:
                    await db_session.commit()

            except Exception:
                await db_session.rollback()
                raise

        return {
            "status": "ok",
            "cis_synced": total_synced,
            "by_class": details,
            "message": f"Synced {total_synced} CIs from iTop: {details}",
        }

    async def close(self):
        """No persistent connection to close."""

    # ── internals ─────────────────────────────────────────────

    async def _call(self, payload: dict) -> dict:
        """POST to iTop REST/JSON API with form-field auth."""
        import httpx

        form_data = {
            "version": self._version,
            "auth_user": self._user,
            "auth_pwd": self._password,
            "json_data": _json.dumps(payload),
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(self._url, data=form_data)
            resp.raise_for_status()
            data = resp.json()
            if data.get("code") != 0:
                raise RuntimeError(
                    f"iTop API error {data.get('code')}: {data.get('message', 'unknown')}"
                )
            return data

    @staticmethod
    def _parse_objects(result: dict, ci_class: str) -> list[dict]:
        """Convert iTop ``objects`` dict → flat list of field dicts."""
        objects = result.get("objects")
        if not objects or not isinstance(objects, dict):
            return []
        return [
            {**v.get("fields", {}), "ci_class": ci_class,
             "id": int(v.get("key", 0))}
            for v in objects.values()
        ]

    @staticmethod
    def _map_type(finalclass: str, ci: dict) -> str:
        """Map iTop CI class to AIOps device_type."""
        mapped = CLASS_TYPE_MAP.get(finalclass, "")
        if mapped:
            return mapped
        # NetworkDevice sub-type from networkdevicetype_name
        nw_type = ci.get("networkdevicetype_name", "").lower()
        if "router" in nw_type:
            return "router"
        return "switch"

    @staticmethod
    def _map_status(status: str) -> str:
        """Map iTop status → AIOps lifecycle_status."""
        if status == "production":
            return "in_use"
        if status in ("obsolete", "end-of-life"):
            return "retired"
        if status == "implementation":
            return "testing"
        return "in_use"
