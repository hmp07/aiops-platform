"""M6 APM — API Endpoints."""
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.session import get_db
from app.core.middleware.auth import get_current_user
from app.core.middleware.permissions import require_permission
from app.modules.module6_apm.repository import CrossLayerRepository, EdgeRepository, ServiceRepository
from app.modules.module6_apm.schemas import (
    CrossLayerResponse, EdgeCreate, EdgeResponse, ServiceCreate,
    ServiceListResponse, ServiceResponse, ServiceUpdate, TopologyResponse,
)
from app.modules.module6_apm.service import APMService as APMServiceLayer

router = APIRouter(prefix="/apm", tags=["APM"])

def _get_svc(db: AsyncSession = Depends(get_db)) -> APMServiceLayer:
    return APMServiceLayer(ServiceRepository(db), EdgeRepository(db), CrossLayerRepository(db))


@router.get("/services", response_model=ServiceListResponse)
async def list_services(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user), svc: APMServiceLayer = Depends(_get_svc)):
    total, items = await svc.list_services(page, page_size)
    return ServiceListResponse(total=total, items=items)

@router.post("/services", response_model=ServiceResponse, status_code=201)
@require_permission("apm:service:list")
async def create_service(req: ServiceCreate, current_user: dict = Depends(get_current_user),
                         svc: APMServiceLayer = Depends(_get_svc)):
    return await svc.create_service(req.model_dump())

@router.get("/services/{service_id}", response_model=ServiceResponse)
async def get_service(service_id: UUID, current_user: dict = Depends(get_current_user),
                      svc: APMServiceLayer = Depends(_get_svc)):
    return await svc.get_service(service_id)

@router.post("/services/{service_id}/update", response_model=ServiceResponse)
@require_permission("apm:service:retrieve")
async def update_service(service_id: UUID, req: ServiceUpdate,
    current_user: dict = Depends(get_current_user), svc: APMServiceLayer = Depends(_get_svc)):
    return await svc.update_service(service_id, req.model_dump(exclude_none=True))

@router.get("/topology", response_model=TopologyResponse)
async def get_topology(current_user: dict = Depends(get_current_user),
                       svc: APMServiceLayer = Depends(_get_svc)):
    return await svc.get_topology()

@router.post("/topology/edges", response_model=EdgeResponse, status_code=201)
@require_permission("apm:topology:view")
async def add_edge(req: EdgeCreate, current_user: dict = Depends(get_current_user),
                   svc: APMServiceLayer = Depends(_get_svc)):
    return await svc.add_edge(req.model_dump())

@router.get("/cross-layer/{service_id}", response_model=CrossLayerResponse)
async def get_cross_layer(service_id: UUID, current_user: dict = Depends(get_current_user),
                          svc: APMServiceLayer = Depends(_get_svc)):
    return await svc.get_cross_layer(service_id)
