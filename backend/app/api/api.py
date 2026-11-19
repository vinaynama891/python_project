"""
CloudPulse Master API Router
"""
from fastapi import APIRouter

from backend.app.api.endpoints import (
    auth,
    servers,
    agent,
    metrics,
    alerts,
    analytics,
    ai,
    reports,
    profiler,
    pdt
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(servers.router, prefix="/servers", tags=["Servers"])
api_router.include_router(agent.router, prefix="/agent", tags=["Agent"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["Metrics"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI & Anomaly"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(profiler.router, prefix="/profiler", tags=["Performance Profiler"])
api_router.include_router(pdt.router, prefix="/pdt", tags=["Performance Debt Tracker"])
