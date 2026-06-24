from fastapi import APIRouter

from mock_data import CROSS_LAYER_DIAGNOSIS, SERVICE_TOPOLOGY, SERVICES

router = APIRouter(tags=["APM"])


@router.get("/apm/services")
async def list_services():
    return {"items": SERVICES}


@router.get("/apm/services/{service_id}")
async def get_service(service_id: str):
    for s in SERVICES:
        if s["id"] == service_id:
            return s
    return None


@router.get("/apm/topology")
async def get_topology():
    return SERVICE_TOPOLOGY


@router.get("/apm/traces/{trace_id}")
async def get_trace(trace_id: str = "abc123def456"):
    return {
        "trace_id": trace_id,
        "duration_ms": 3520,
        "spans": [
            {"service": "api-gateway", "operation": "POST /api/payment/submit", "duration_ms": 3520, "start_ms": 0},
            {"service": "payment-service", "operation": "processPayment", "duration_ms": 3480, "start_ms": 20},
            {"service": "payment-service", "operation": "db.query", "duration_ms": 3200, "start_ms": 250},
            {"service": "mysql-db", "operation": "SELECT ... FROM orders WHERE ...", "duration_ms": 3150, "start_ms": 280},
        ],
    }


@router.get("/apm/cross-layer/{alert_id}")
async def get_cross_layer_diagnosis(alert_id: str):
    if alert_id == CROSS_LAYER_DIAGNOSIS.get("alert_id"):
        return CROSS_LAYER_DIAGNOSIS
    return {"message": "No cross-layer analysis for this alert"}
