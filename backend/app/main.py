"""
CloudPulse - Enterprise Cloud Infrastructure Monitor & Performance Tuning Profiler
FastAPI Application Entry Point
"""
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.app.core.config import settings
from backend.app.core.security import decode_token
from backend.app.database.session import engine, Base
from backend.app.api.api import api_router
from backend.app.websocket.manager import ws_manager

dist_path = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist in SQLite or PostgreSQL
    Base.metadata.create_all(bind=engine)
    print(f"[{settings.APP_NAME}] Database schema initialized successfully.")
    yield
    # Shutdown logic if any
    print(f"[{settings.APP_NAME}] Server shutting down cleanly.")


app = FastAPI(
    title="CloudPulse API",
    description="Enterprise Cloud Infrastructure Monitor & Performance Tuning Profiler API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount master API router
app.include_router(api_router, prefix="/api")

if dist_path.exists() and (dist_path / "assets").exists():
    app.mount("/assets", StaticFiles(directory=dist_path / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Don't intercept API, WS, or docs
        if any(full_path.startswith(p) for p in ["api", "ws", "docs", "redoc", "openapi.json"]):
            raise HTTPException(status_code=404, detail="Not Found")
        target_file = dist_path / full_path
        if target_file.exists() and target_file.is_file():
            return FileResponse(target_file)
        return FileResponse(dist_path / "index.html")
else:
    @app.get("/")
    def root():
        return {
            "app": settings.APP_NAME,
            "version": "1.0.0",
            "status": "operational",
            "docs": "/docs",
            "environment": settings.ENVIRONMENT
        }


@app.websocket("/ws/{org_id}")
async def websocket_org_endpoint(websocket: WebSocket, org_id: str):
    """
    Real-time WebSocket telemetry stream partitioned by Organization ID.
    Clients receive real-time METRIC_UPDATE events, alert triggers, and anomaly notifications.
    """
    await ws_manager.connect(websocket, org_id)
    try:
        while True:
            # Keep socket alive by listening for heartbeats or client messages
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, org_id)
    except Exception:
        ws_manager.disconnect(websocket, org_id)


@app.websocket("/ws")
async def websocket_default_endpoint(websocket: WebSocket, token: str = Query(None)):
    """Default WebSocket endpoint that extracts org_id from JWT token query parameter."""
    org_id = "default"
    if token:
        payload = decode_token(token)
        if payload and payload.get("org_id"):
            org_id = payload["org_id"]

    await ws_manager.connect(websocket, org_id)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, org_id)
    except Exception:
        ws_manager.disconnect(websocket, org_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.BACKEND_HOST, port=settings.BACKEND_PORT, reload=True)
