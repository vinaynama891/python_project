"""
CloudPulse Agent Ingestion & Lifecycle Endpoints
Receives authentic hardware telemetry from Python agents, evaluates alerts, triggers ML anomaly scoring, and broadcasts real-time WebSocket frames.
"""
import secrets
from datetime import datetime, timezone
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

from backend.app.api.deps import verify_agent_auth, get_db
from backend.app.core.security import hash_agent_token
from backend.app.models.models import Server, AgentCredential, Metric, ProcessMetric
from backend.app.schemas.schemas import (
    AgentRegisterRequest,
    AgentRegisterResponse,
    AgentHeartbeatRequest,
    AgentMetricPayload
)
from backend.app.services.alert_service import AlertEngine
from backend.app.ml.anomaly_detector import detect_anomalies, train_model, ml_service
from backend.app.websocket.manager import ws_manager

router = APIRouter()


@router.post("/register", response_model=AgentRegisterResponse)
def register_agent(payload: AgentRegisterRequest, db: Session = Depends(get_db)) -> Any:
    """Agent registers itself using an admin-issued registration token."""
    server = db.query(Server).filter(
        Server.registration_token == payload.registration_token,
        Server.is_active == True
    ).first()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired registration token."
        )

    # Generate permanent revocable agent credentials
    agent_token = f"cp_agt_{secrets.token_urlsafe(32)}"
    token_hash = hash_agent_token(agent_token)

    # Save credentials
    cred = db.query(AgentCredential).filter(AgentCredential.server_id == server.id).first()
    if cred:
        cred.agent_token_hash = token_hash
        cred.is_revoked = False
    else:
        cred = AgentCredential(
            server_id=server.id,
            agent_token_hash=token_hash,
            is_revoked=False
        )
        db.add(cred)

    # Update server details from real host
    server.hostname = payload.hostname
    if payload.server_name and server.name.startswith("Server-"):
        server.name = payload.server_name
    server.os = payload.os
    server.os_version = payload.os_version
    server.architecture = payload.architecture
    server.ip_address = payload.ip_address
    server.status = "online"
    server.last_heartbeat = datetime.now(timezone.utc)
    # Clear registration token after successful pairing
    server.registration_token = None

    db.commit()
    db.refresh(server)

    return AgentRegisterResponse(
        server_id=server.id,
        agent_token=agent_token,
        message="Agent registered successfully."
    )


@router.post("/heartbeat")
def receive_heartbeat(payload: AgentHeartbeatRequest, db: Session = Depends(get_db)) -> Any:
    """Processes lightweight heartbeat packet."""
    server = db.query(Server).filter(Server.id == payload.server_id, Server.is_active == True).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found.")

    server.last_heartbeat = datetime.now(timezone.utc)
    if server.status == "offline":
        server.status = "online"

    db.commit()
    return {"status": "acknowledged", "server_id": server.id, "server_status": server.status}


@router.post("/metrics", status_code=status.HTTP_201_CREATED)
async def ingest_metrics(
    payload: AgentMetricPayload,
    server: Server = Depends(verify_agent_auth),
    db: Session = Depends(get_db)
) -> Any:
    """Ingests real-time hardware telemetry from authenticated agent."""
    now = datetime.now(timezone.utc)
    server.last_heartbeat = now
    server.status = "online"

    # 1. Insert Core Metric Record
    metric_record = Metric(
        server_id=server.id,
        timestamp=now,
        cpu_percent=payload.cpu.cpu_percent,
        cpu_per_core=payload.cpu.cpu_per_core,
        cpu_frequency_current=payload.cpu.cpu_frequency.get("current", 0.0),
        cpu_cores=payload.cpu.cpu_cores_logical,
        cpu_temperature=payload.cpu.cpu_temperature,
        ram_total=payload.memory.ram_total,
        ram_used=payload.memory.ram_used,
        ram_available=payload.memory.ram_available,
        ram_percent=payload.memory.ram_percent,
        swap_percent=payload.memory.swap_percent or 0.0,
        disk_total=payload.disk.disk_total,
        disk_used=payload.disk.disk_used,
        disk_free=payload.disk.disk_free,
        disk_percent=payload.disk.disk_percent,
        disk_read_speed=payload.disk.disk_read_speed_bytes_sec or 0.0,
        disk_write_speed=payload.disk.disk_write_speed_bytes_sec or 0.0,
        disk_io_ops=payload.disk.disk_io_operations or 0,
        net_bytes_sent=payload.network.bytes_sent,
        net_bytes_recv=payload.network.bytes_recv,
        net_upload_speed=payload.network.upload_speed_bytes_sec,
        net_download_speed=payload.network.download_speed_bytes_sec,
        net_packets_sent=payload.network.packets_sent,
        net_packets_recv=payload.network.packets_recv,
        raw_details={
            "system": payload.system.model_dump(),
            "interfaces": payload.network.interfaces
        }
    )
    db.add(metric_record)
    db.flush()

    # 2. Store Process Snapshots
    for proc in payload.processes.top_cpu[:10]:
        db.add(ProcessMetric(
            metric_id=metric_record.id,
            server_id=server.id,
            timestamp=now,
            pid=proc.pid,
            name=proc.name,
            username=proc.username,
            status=proc.status,
            cpu_percent=proc.cpu_percent,
            memory_percent=proc.memory_percent,
            memory_bytes=proc.memory_bytes
        ))

    db.commit()

    # 3. Evaluate Alert Engine Thresholds
    alerts = AlertEngine.evaluate_metrics(
        db=db,
        server=server,
        cpu_percent=payload.cpu.cpu_percent,
        ram_percent=payload.memory.ram_percent,
        disk_percent=payload.disk.disk_percent
    )

    # 4. Trigger ML Anomaly Evaluation
    anomaly = ml_service.evaluate_live_metric(db, server, metric_record)

    # 5. Broadcast Telemetry Frame via WebSockets
    ws_event = {
        "event": "METRIC_UPDATE",
        "server_id": server.id,
        "server_name": server.name,
        "timestamp": now.isoformat(),
        "cpu_percent": payload.cpu.cpu_percent,
        "ram_percent": payload.memory.ram_percent,
        "disk_percent": payload.disk.disk_percent,
        "net_upload_speed": payload.network.upload_speed_bytes_sec,
        "net_download_speed": payload.network.download_speed_bytes_sec,
        "new_alerts_count": len(alerts),
        "is_anomaly": anomaly is not None
    }
    await ws_manager.broadcast_to_org(server.organization_id, ws_event)

    return {
        "status": "success",
        "metric_id": metric_record.id,
        "server_id": server.id,
        "alerts_triggered": len(alerts),
        "anomaly_detected": anomaly is not None
    }


@router.post("/revoke")
def revoke_agent_credentials(server_id: str, db: Session = Depends(get_db)) -> Any:
    """Revokes credentials for a specific server agent."""
    cred = db.query(AgentCredential).filter(AgentCredential.server_id == server_id).first()
    if not cred:
        raise HTTPException(status_code=404, detail="Credentials not found.")

    cred.is_revoked = True
    db.commit()
    return {"message": "Agent credentials revoked successfully."}
