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

    async def update_ci(self, ci_class: str, ci_id: int, fields: dict) -> dict:
        """Update an iTop CI via core/update.

        Used for Zabbix → iTop data enrichment (serial numbers,
        OS versions, etc. collected by Zabbix monitoring).
        """
        payload: dict = {
            "operation": "core/update",
            "class": ci_class,
            "key": ci_id,
            "fields": fields,
        }
        result = await self._call(payload)
        return result

    # ── TeemIp IPAM ─────────────────────────────────────────

    async def get_ipv4_subnets(self, org_id: int | None = None) -> list[dict]:
        """Fetch IPv4 subnets via core/get."""
        key = f"SELECT IPv4Subnet WHERE org_id = {org_id}" if org_id else "SELECT IPv4Subnet"
        result = await self._call({
            "operation": "core/get", "class": "IPv4Subnet",
            "key": key, "output_fields": "*", "limit": 200,
        })
        return self._parse_objects(result, "IPv4Subnet")

    async def get_ipv4_addresses(self, subnet_id: int | None = None) -> list[dict]:
        """Fetch IPv4 addresses, optionally filtered by subnet."""
        key = f"SELECT IPv4Address WHERE subnet_id = {subnet_id}" if subnet_id else "SELECT IPv4Address"
        result = await self._call({
            "operation": "core/get", "class": "IPv4Address",
            "key": key, "output_fields": "*", "limit": 500,
        })
        return self._parse_objects(result, "IPv4Address")

    async def get_subnet_stats(self) -> list[dict]:
        """Get per-subnet IP usage statistics via TeemIp."""
        result = await self._call({
            "operation": "teemip/get_nb_of_registered_ips_in_subnet",
            "class": "IPv4Subnet",
            "key": "SELECT IPv4Subnet",
        })
        objects = result.get("objects") or {}
        return [
            {
                **v.get("fields", {}),
                "subnet_size": v.get("subnet_size", 0),
                "allocated": v.get("nb_of_ips", {}).get("allocated", 0),
                "released": v.get("nb_of_ips", {}).get("released", 0),
                "reserved": v.get("nb_of_ips", {}).get("reserved", 0),
                "unassigned": v.get("nb_of_ips", {}).get("unassigned", 0),
                "total_registered": v.get("nb_of_ips", {}).get("total registered", 0),
                "free_ips": v.get("nb_of_ips", {}).get("free ips", 0),
            }
            for v in objects.values()
        ]

    # ── sync ─────────────────────────────────────────────────

    async def sync(self, db_session=None) -> dict:
        """Sync iTop CIs + TeemIp IPAM → AIOps Device + IPAM tables."""
        ci_result = await self._sync_cis(db_session)

        if db_session:
            ipam_result = await self._sync_ipam(db_session)
        else:
            ipam_result = {}

        return {
            "status": "ok",
            **ci_result,
            **ipam_result,
            "message": ci_result.get("message", "") + "; " + ipam_result.get("message", ""),
        }

    async def _sync_cis(self, db_session) -> dict:
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

                        ext_id = f"itop:{ci_id}"
                        # Dedup by external_id (unique across sources), skip soft-deleted
                        existing = (await db_session.execute(
                            select(Device).where(
                                Device.extra_attrs["external_id"].as_string() == ext_id,
                                Device.deleted_at.is_(None),
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
                                    "external_id": ext_id,
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
            "cis_synced": total_synced,
            "by_class": details,
            "message": f"Synced {total_synced} CIs from iTop: {details}",
        }

    async def _sync_ipam(self, db_session) -> dict:
        """Sync TeemIp IPAM data → AIOps Subnet + IPAllocation tables."""
        import uuid as _uuid
        from app.modules.module2_ipam.models import Subnet, IPAllocation
        from sqlalchemy import select

        try:
            # ── Sync subnets with usage stats ──
            stats = await self.get_subnet_stats()
            subnets_synced = 0

            for s in stats:
                ip = s.get("ip", "")
                mask = s.get("mask", "")
                if not ip or not mask:
                    continue
                cidr = f"{ip}/{self._mask_to_prefix(mask)}"

                existing = (await db_session.execute(
                    select(Subnet).where(Subnet.cidr == cidr)
                )).scalar_one_or_none()

                if not existing:
                    obj = Subnet(
                        id=_uuid.uuid4(),
                        cidr=cidr,
                        description=s.get("name") or "",
                        total_ips=s.get("subnet_size", 0),
                        used_ips=s.get("total_registered", 0),
                    )
                    db_session.add(obj)
                    subnets_synced += 1
                else:
                    existing.total_ips = s.get("subnet_size", 0)
                    existing.used_ips = s.get("total_registered", 0)

            # ── Build a quick subnet lookup: CIDR prefix → subnet_id ──
            from sqlalchemy import select as _sel
            all_subnets = (await db_session.execute(_sel(Subnet))).scalars().all()
            cidr_to_id: dict[str, object] = {s.cidr: s.id for s in all_subnets}

            # ── Sync IP addresses ──
            addresses = await self.get_ipv4_addresses()
            addr_synced = 0

            for a in addresses:
                ip_addr = a.get("ip", "")
                if not ip_addr:
                    continue
                status = a.get("status", "free")
                short_name = a.get("short_name") or ""

                # Look up existing allocation
                existing_check = (await db_session.execute(
                    select(IPAllocation).where(IPAllocation.ip_address == ip_addr)
                )).scalar_one_or_none()

                if not existing_check:
                    # Determine which subnet this IP belongs to
                    matched_subnet_id = None
                    for cidr, sid in cidr_to_id.items():
                        if self._ip_in_cidr(ip_addr, str(cidr)):
                            matched_subnet_id = sid
                            break

                    # Fallback: use first available subnet
                    if matched_subnet_id is None and cidr_to_id:
                        matched_subnet_id = list(cidr_to_id.values())[0]

                    if matched_subnet_id is not None:
                        alloc = IPAllocation(
                            id=_uuid.uuid4(),
                            subnet_id=matched_subnet_id,
                            ip_address=ip_addr,
                            status=status,
                            interface_name=short_name if short_name else None,
                            source="itop",
                        )
                        db_session.add(alloc)
                        addr_synced += 1

            if subnets_synced > 0 or addr_synced > 0:
                await db_session.commit()

        except Exception:
            await db_session.rollback()
            raise

        return {
            "ipam_subnets": subnets_synced,
            "ipam_addresses": addr_synced,
            "message": f"IPAM: {subnets_synced} subnets, {addr_synced} addresses",
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

    @staticmethod
    def _mask_to_prefix(mask: str) -> int:
        """Convert dotted netmask to CIDR prefix length (e.g. 255.255.254.0 → 23)."""
        try:
            return sum(bin(int(octet)).count("1") for octet in mask.split("."))
        except Exception:
            return 24

    @staticmethod
    def _ip_in_cidr(ip: str, cidr: str) -> bool:
        """Check if an IP address falls within a CIDR range."""
        import ipaddress
        try:
            return ipaddress.ip_address(ip) in ipaddress.ip_network(cidr, strict=False)
        except Exception:
            return False
