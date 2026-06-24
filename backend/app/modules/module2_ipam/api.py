"""M2 IPAM — API Endpoints."""
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.session import get_db
from app.core.middleware.auth import get_current_user
from app.core.middleware.permissions import require_permission
from app.modules.module2_ipam.repository import IPAllocationRepository, SubnetRepository
from app.modules.module2_ipam.schemas import (
    IPAllocationCreate, IPAllocationListResponse, IPAllocationRelease,
    SubnetCreate, SubnetListResponse, SubnetResponse, SubnetUpdate,
)
from app.modules.module2_ipam.service import IPAllocationService, SubnetService

router = APIRouter(prefix="/ipam", tags=["IPAM"])


def _get_subnet_svc(db: AsyncSession = Depends(get_db)) -> SubnetService:
    return SubnetService(SubnetRepository(db))


def _get_alloc_svc(db: AsyncSession = Depends(get_db)) -> IPAllocationService:
    return IPAllocationService(IPAllocationRepository(db), SubnetRepository(db))


# Subnets
@router.get("/subnets", response_model=SubnetListResponse)
async def list_subnets(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    _: dict = Depends(get_current_user),
    svc: SubnetService = Depends(_get_subnet_svc),
):
    total, items = await svc.list_subnets(page, page_size)
    return SubnetListResponse(total=total, items=items)


@router.post("/subnets", response_model=SubnetResponse, status_code=201)
@require_permission("ipam:subnet:create")
async def create_subnet(
    req: SubnetCreate,
    _u: dict = Depends(get_current_user),
    svc: SubnetService = Depends(_get_subnet_svc),
):
    return await svc.create_subnet(req.model_dump())


@router.post("/subnets/{subnet_id}/update", response_model=SubnetResponse)
@require_permission("ipam:subnet:update")
async def update_subnet(
    subnet_id: UUID, req: SubnetUpdate,
    _u: dict = Depends(get_current_user),
    svc: SubnetService = Depends(_get_subnet_svc),
):
    return await svc.update_subnet(subnet_id, req.model_dump(exclude_none=True))


@router.post("/subnets/{subnet_id}/delete")
@require_permission("ipam:subnet:delete")
async def delete_subnet(
    subnet_id: UUID,
    _u: dict = Depends(get_current_user),
    svc: SubnetService = Depends(_get_subnet_svc),
):
    await svc.delete_subnet(subnet_id)
    return {"status": "deleted", "subnet_id": str(subnet_id)}


# IP Allocations
@router.get("/allocations", response_model=IPAllocationListResponse)
async def list_allocations(
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
    subnet_id: UUID | None = None, status: str | None = None,
    _: dict = Depends(get_current_user),
    svc: IPAllocationService = Depends(_get_alloc_svc),
):
    total, items = await svc.list_allocations(page, page_size, subnet_id, status)
    return IPAllocationListResponse(total=total, items=items)


@router.post("/allocations/allocate", status_code=201)
@require_permission("ipam:ip:allocate")
async def allocate_ip(
    req: IPAllocationCreate,
    _u: dict = Depends(get_current_user),
    svc: IPAllocationService = Depends(_get_alloc_svc),
):
    return await svc.allocate(req.model_dump())


@router.post("/allocations/{allocation_id}/release")
@require_permission("ipam:ip:release")
async def release_ip(
    allocation_id: UUID, _req: IPAllocationRelease = IPAllocationRelease(),
    _u: dict = Depends(get_current_user),
    svc: IPAllocationService = Depends(_get_alloc_svc),
):
    return await svc.release(allocation_id)
