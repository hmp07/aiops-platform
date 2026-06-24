from fastapi import APIRouter

from mock_data import IP_ALLOCATIONS, SUBNETS

router = APIRouter(tags=["IPAM"])


@router.get("/ipam/subnets")
async def list_subnets():
    return {"items": SUBNETS}


@router.get("/ipam/subnets/{subnet_id}")
async def get_subnet(subnet_id: str):
    for s in SUBNETS:
        if s["id"] == subnet_id:
            return {"subnet": s, "allocations": [ip for ip in IP_ALLOCATIONS if ip["subnet_id"] == subnet_id]}
    return None


@router.get("/ipam/allocations")
async def list_allocations(subnet_id: str = "", status: str = "", page: int = 1, page_size: int = 50):
    items = IP_ALLOCATIONS
    if subnet_id:
        items = [ip for ip in items if ip["subnet_id"] == subnet_id]
    if status:
        items = [ip for ip in items if ip["status"] == status]
    return {"total": len(items), "items": items}


@router.get("/ipam/stats")
async def ipam_stats():
    return {
        "total_subnets": len(SUBNETS),
        "total_ips": sum(s["total_ips"] for s in SUBNETS),
        "total_used": sum(s["used_ips"] for s in SUBNETS),
        "ghost_ips": 2,
        "subnets": SUBNETS,
    }
