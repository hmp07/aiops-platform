"""M1 Asset — Cross-source asset matching engine.

Matches devices across Zabbix and iTop using IP address and
visible name as correlation anchors.  Produces scored match
candidates for automatic merge or manual confirmation.
"""
from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.module1_asset.models import Device


@dataclass
class MatchCandidate:
    """A pair of devices that may represent the same physical asset."""
    device_a: dict          # Zabbix device
    device_b: dict          # iTop device
    score: float            # 0.0 – 1.0 confidence
    rule: str               # which rule produced this match
    reason: str = ""        # human-readable explanation


@dataclass
class MatchResult:
    candidates: list[MatchCandidate] = field(default_factory=list)
    merged: int = 0
    skipped: int = 0


# ── matching rules ──────────────────────────────────────────

def _ip_exact(a: dict, b: dict) -> tuple[float, str]:
    """Both devices have the same management IP."""
    ip_a = (a.get("management_ip") or "").strip()
    ip_b = (b.get("management_ip") or "").strip()
    if ip_a and ip_b and ip_a == ip_b:
        return 0.95, f"IP exact match: {ip_a}"
    return 0.0, ""


def _name_exact(a: dict, b: dict) -> tuple[float, str]:
    """Zabbix visible_name equals iTop device_name."""
    extra_a = a.get("extra_attrs") or {}
    vis = (extra_a.get("visible_name") or extra_a.get("name") or "").strip()
    name_b = (b.get("device_name") or "").strip()
    if vis and name_b and vis.lower() == name_b.lower():
        return 0.90, f"Name exact match: '{vis}'"
    return 0.0, ""


def _ip_and_name(a: dict, b: dict) -> tuple[float, str]:
    """Both IP and name match — highest confidence."""
    ip_score, ip_reason = _ip_exact(a, b)
    name_score, name_reason = _name_exact(a, b)
    if ip_score > 0 and name_score > 0:
        return 0.99, f"IP + Name: {ip_reason} & {name_reason}"
    return 0.0, ""


def _ip_subnet(a: dict, b: dict) -> tuple[float, str]:
    """IPs are in the same /24 subnet."""
    ip_a = (a.get("management_ip") or "").strip()
    ip_b = (b.get("management_ip") or "").strip()
    if not ip_a or not ip_b:
        return 0.0, ""
    try:
        parts_a, parts_b = ip_a.split("."), ip_b.split(".")
        if len(parts_a) == 4 and len(parts_b) == 4:
            if parts_a[:3] == parts_b[:3]:
                # Bonus if names are similar
                extra_a = a.get("extra_attrs") or {}
                vis = (extra_a.get("visible_name") or "").lower()
                name_b = b.get("device_name", "").lower()
                bonus = 0.05 if vis and name_b and (
                    vis in name_b or name_b in vis or _edit_distance(vis, name_b) < 5
                ) else 0.0
                return 0.70 + bonus, f"Same /24 subnet: {parts_a[0]}.{parts_a[1]}.{parts_a[2]}.x"
    except Exception:
        pass
    return 0.0, ""


RULES = [
    ("ip_and_name", _ip_and_name),
    ("ip_exact", _ip_exact),
    ("name_exact", _name_exact),
    ("ip_subnet", _ip_subnet),
]

THRESHOLD_AUTO = 0.90   # auto-merge above this
THRESHOLD_CANDIDATE = 0.65  # show as candidate below this

# ── service ──────────────────────────────────────────────────

class AssetMatchService:
    """Cross-source asset matching engine."""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def find_candidates(self, source_a: str = "zabbix", source_b: str = "itop") -> MatchResult:
        """Find and score all match candidates between two sources."""
        devices_a = await self._load_source(source_a)
        devices_b = await self._load_source(source_b)
        result = MatchResult()

        for dev_a in devices_a:
            best_score = 0.0
            best_rule = ""
            best_reason = ""
            best_match: dict | None = None

            for dev_b in devices_b:
                for rule_name, rule_fn in RULES:
                    score, reason = rule_fn(dev_a, dev_b)
                    if score > best_score:
                        best_score = score
                        best_rule = rule_name
                        best_reason = reason
                        best_match = dev_b

            if best_score >= THRESHOLD_AUTO and best_match:
                await self._merge(dev_a, best_match, best_score, best_rule)
                result.merged += 1
                # Remove matched iTop device from pool
                devices_b = [d for d in devices_b if d["id"] != best_match["id"]]
            elif best_score >= THRESHOLD_CANDIDATE and best_match:
                result.candidates.append(MatchCandidate(
                    device_a=dev_a, device_b=best_match,
                    score=best_score, rule=best_rule, reason=best_reason,
                ))
            else:
                result.skipped += 1

        return result

    async def confirm_merge(self, device_a_id: UUID, device_b_id: UUID) -> dict:
        """Manually confirm a candidate match."""
        a = await self._db.get(Device, device_a_id)
        b = await self._db.get(Device, device_b_id)
        if not a or not b:
            raise ValueError("Device not found")
        return await self._merge(self._to_dict(a), self._to_dict(b), 1.0, "manual")

    # ── internals ────────────────────────────────────────────

    async def _load_source(self, source: str) -> list[dict]:
        q = select(Device).where(
            Device.extra_attrs["source"].as_string() == source,
            Device.deleted_at.is_(None),
        )
        rows = (await self._db.execute(q)).scalars().all()
        return [self._to_dict(r) for r in rows]

    async def _merge(self, a: dict, b: dict, score: float, rule: str) -> dict:
        """Merge device B into A.  B is soft-deleted, A gets enriched.

        Merge strategy:
        - name → iTop (CMDB authoritative)
        - vendor/model/serial → iTop
        - management_ip → Zabbix (real-time accurate)
        - lifecycle_status → iTop
        - extra_attrs → merged from both sources
        """
        obj_a = await self._db.get(Device, a["id"])
        obj_b = await self._db.get(Device, b["id"])
        extra_a = a.get("extra_attrs") or {}
        extra_b = b.get("extra_attrs") or {}

        # Update A with B's CMDB data
        if b.get("device_name"):
            obj_a.device_name = b["device_name"]
        if b.get("vendor"):
            obj_a.vendor = b["vendor"]
        if b.get("model"):
            obj_a.model = b["model"]
        if b.get("serial_number"):
            obj_a.serial_number = b["serial_number"]
        if b.get("software_version"):
            obj_a.software_version = b["software_version"]
        if b.get("location"):
            obj_a.location = b["location"]

        # Merge extra_attrs with merge metadata
        obj_a.extra_attrs = {
            **extra_a,
            **{k: v for k, v in extra_b.items() if k not in ("source", "external_id")},
            "source": "merged",
            "merged_from": {
                "source": extra_b.get("source"),
                "external_id": extra_b.get("external_id"),
                "device_id": str(b["id"]),
            },
            "merge_score": score,
            "merge_rule": rule,
            "sources": ["zabbix", "itop"],
        }

        # Soft-delete B
        from datetime import datetime, timezone
        obj_b.deleted_at = datetime.now(timezone.utc)

        await self._db.commit()
        return {"status": "merged", "device": self._to_dict(obj_a)}

    @staticmethod
    def _to_dict(obj: Device) -> dict:
        return {
            "id": str(obj.id), "device_name": obj.device_name,
            "device_type": obj.device_type, "vendor": obj.vendor,
            "model": obj.model, "serial_number": obj.serial_number,
            "software_version": obj.software_version,
            "management_ip": str(obj.management_ip) if obj.management_ip else None,
            "location": obj.location, "lifecycle_status": obj.lifecycle_status,
            "business_system": obj.business_system, "user_department": obj.user_department,
            "extra_attrs": obj.extra_attrs or {},
            "created_at": obj.created_at, "updated_at": obj.updated_at,
        }


def _edit_distance(s1: str, s2: str) -> int:
    """Levenshtein distance."""
    if len(s1) < len(s2):
        return _edit_distance(s2, s1)
    if not s2:
        return len(s1)
    prev = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr = [i + 1]
        for j, c2 in enumerate(s2):
            curr.append(min(
                prev[j + 1] + 1,   # insert
                curr[j] + 1,       # delete
                prev[j] + (0 if c1 == c2 else 1),  # substitute
            ))
        prev = curr
    return prev[-1]
