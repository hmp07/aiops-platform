"""AIOps Platform Demo — FastAPI Backend with Mock Data."""
import asyncio
import random

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import auth, dashboard, devices, ipam, alerts, configs, apm, knowledge, ai, platform

app = FastAPI(title="AIOps Platform Demo", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Simulated latency middleware ----
@app.middleware("http")
async def add_latency(request, call_next):
    delay = random.uniform(0.15, 0.5)
    await asyncio.sleep(delay)
    response = await call_next(request)
    return response


# ---- Mount routes ----
app.include_router(auth.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(devices.router, prefix="/api/v1")
app.include_router(ipam.router, prefix="/api/v1")
app.include_router(alerts.router, prefix="/api/v1")
app.include_router(configs.router, prefix="/api/v1")
app.include_router(apm.router, prefix="/api/v1")
app.include_router(knowledge.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")
app.include_router(platform.router, prefix="/api/v1")


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0", "mode": "demo"}
