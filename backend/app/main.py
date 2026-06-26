import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config.settings import get_settings
from app.core.cache.redis import close_redis
from app.core.database.event_mixin import register_event_listeners
from app.core.exceptions import AIOpsError

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    register_event_listeners()
    _register_builtin_tools()
    await _init_builtin_skills()
    yield
    await close_redis()
    logger.info("Shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DemoGuard — blocks mutation for demo accounts (pure ASGI, no anyio TaskGroup)
from app.core.middleware.demo_guard import DemoGuardMiddleware

app.add_middleware(DemoGuardMiddleware)


@app.exception_handler(AIOpsError)
async def aoips_error_handler(request: Request, exc: AIOpsError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message},
    )


@app.exception_handler(Exception)
async def catchall_error_handler(request: Request, exc: Exception) -> JSONResponse:
    import traceback
    logger.error(f"Unhandled exception on {request.url.path}: {exc}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"code": "INTERNAL_ERROR", "message": str(exc)},
    )


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}


# ---- Module Visibility Endpoint ----
from app.modules.module9_platform.permission_registry import BUILTIN_ROLES, PERMISSION_DEFINITIONS


@app.get("/api/v1/auth/modules")
async def get_accessible_modules(current_user: dict = None):
    """Return list of module keys the current user can access.

    Used by frontend to dynamically render sidebar menu.
    """
    from app.core.middleware.permissions import get_effective_permissions

    role = current_user.get("role", "viewer") if current_user else "viewer"
    perms = get_effective_permissions({"role": role, "user_id": ""})
    modules = set()
    for p in perms:
        parts = p.split(":")
        if parts:
            modules.add(parts[0])
    return {"modules": sorted(modules), "role": role}


@app.get("/api/v1/auth/permissions")
async def get_all_permissions():
    """Return all permission definitions (for admin UI)."""
    return {
        "permissions": [
            {"code": code, **defn}
            for code, defn in PERMISSION_DEFINITIONS.items()
        ],
        "roles": [
            {"code": code, "name": defn["name"], "description": defn["description"]}
            for code, defn in BUILTIN_ROLES.items()
        ],
    }


# ---- Builtin Tools & Skills Registration (module8_aiops) ----
def _register_builtin_tools():
    # Tools are now defined inline in api.py (sxdevops pattern)
    logger.info("AIOps tools ready (inline in api.py)")


async def _init_builtin_skills():
    # Skills are managed via AIOpsSkill model in module8_aiops
    logger.info("AIOps skills ready (managed via admin API)")


# ---- Router Registration ----
from app.modules.module9_platform.api import router as platform_router
from app.modules.module10_eventwall.api import router as eventwall_router
from app.modules.module8_aiops.api import router as aiops_router
from app.modules.module1_asset.api import router as asset_router, cal_router as asset_cal_router
from app.modules.module2_ipam.api import router as ipam_router
from app.modules.module5_config.api import router as config_router
from app.modules.module3_monitoring.api import router as alert_router, rule_router, notif_router
from app.modules.module6_apm.api import router as apm_router
from app.modules.module7_knowledge.api import router as knowledge_router
# kg_router kept from module8_ai for now (knowledge_graph is standalone)
from app.modules.module8_ai.knowledge_graph.api import router as kg_router
from app.modules.module4_log.api import router as log_router
from app.modules.module11_scheduler.api import router as scheduler_router, ds_router

app.include_router(platform_router, prefix="/api/v1")
app.include_router(eventwall_router, prefix="/api/v1")
app.include_router(aiops_router, prefix="/api/v1")
app.include_router(asset_router, prefix="/api/v1")
app.include_router(asset_cal_router, prefix="/api/v1")
app.include_router(ipam_router, prefix="/api/v1")
app.include_router(config_router, prefix="/api/v1")
app.include_router(alert_router, prefix="/api/v1")
app.include_router(rule_router, prefix="/api/v1")
app.include_router(notif_router, prefix="/api/v1")
app.include_router(apm_router, prefix="/api/v1")
app.include_router(knowledge_router, prefix="/api/v1")
app.include_router(kg_router, prefix="/api/v1")
app.include_router(log_router, prefix="/api/v1")
app.include_router(scheduler_router, prefix="/api/v1")
app.include_router(ds_router, prefix="/api/v1")
