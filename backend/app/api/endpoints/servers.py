"""
CloudPulse Server Management Endpoints
"""
import uuid
import secrets
from datetime import datetime, timezone
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_current_org, get_db
from backend.app.core.config import settings
from backend.app.models.models import User, Organization, Server, Metric
from backend.app.schemas.schemas import ServerCreate, ServerUpdate, ServerOut, ServerRegisterToken
from backend.app.services.alert_service import AlertEngine

router = APIRouter()


def update_server_online_status(server: Server):
    """Calculates online/offline state dynamically based on heartbeat freshness."""
    if not server.last_heartbeat:
        server.status = "offline"
        return

    now = datetime.now(timezone.utc)
    hb_time = server.last_heartbeat.replace(tzinfo=timezone.utc) if server.last_heartbeat.tzinfo is None else server.last_heartbeat
    diff = (now - hb_time).total_seconds()

    if diff > settings.DEFAULT_HEARTBEAT_TIMEOUT_SECONDS:
        server.status = "offline"
    elif server.status == "offline":
        server.status = "online"


@router.get("", response_model=List[ServerOut])
def list_servers(
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    current_org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
) -> Any:
    """Lists all servers registered to the organization with real-time health checks."""
    AlertEngine.check_heartbeat_timeouts(db, settings.DEFAULT_HEARTBEAT_TIMEOUT_SECONDS)

    query = db.query(Server).filter(
        Server.organization_id == current_org.id,
        Server.is_active == True
    )

    if status_filter:
        query = query.filter(Server.status == status_filter.lower())

    if search:
        query = query.filter(Server.name.ilike(f"%{search}%") | Server.hostname.ilike(f"%{search}%"))

    servers = query.order_by(Server.created_at.desc()).all()
    results = []

    for s in servers:
        update_server_online_status(s)
        latest_metric = db.query(Metric).filter(Metric.server_id == s.id).order_by(Metric.timestamp.desc()).first()

        results.append(ServerOut(
            id=s.id,
            organization_id=s.organization_id,
            name=s.name,
            description=s.description,
            hostname=s.hostname,
            os=s.os,
            os_version=s.os_version,
            architecture=s.architecture,
            ip_address=s.ip_address,
            status=s.status,
            last_heartbeat=s.last_heartbeat,
            registration_token=s.registration_token,
            is_active=s.is_active,
            created_at=s.created_at,
            latest_cpu=latest_metric.cpu_percent if latest_metric else None,
            latest_ram=latest_metric.ram_percent if latest_metric else None,
            latest_disk=latest_metric.disk_percent if latest_metric else None
        ))

    return results


@router.post("", response_model=ServerRegisterToken, status_code=status.HTTP_201_CREATED)
def create_server(
    server_in: ServerCreate,
    current_org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
) -> Any:
    """Creates a new server slot and generates an agent registration token with installation command."""
    reg_token = f"cp_reg_{secrets.token_urlsafe(24)}"
    new_server = Server(
        organization_id=current_org.id,
        name=server_in.name,
        description=server_in.description,
        registration_token=reg_token,
        status="offline"
    )
    db.add(new_server)
    db.commit()
    db.refresh(new_server)

    win_cmd = f"python main.py --register {reg_token} --url http://localhost:8000 --name \"{new_server.name}\""
    linux_cmd = f"python3 main.py --register {reg_token} --url http://localhost:8000 --name \"{new_server.name}\""

    return ServerRegisterToken(
        server_id=new_server.id,
        registration_token=reg_token,
        registration_command_windows=win_cmd,
        registration_command_linux=linux_cmd
    )


@router.get("/{server_id}", response_model=ServerOut)
def get_server(
    server_id: str,
    current_org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
) -> Any:
    """Retrieves detailed configuration and operational metrics for an individual server."""
    server = db.query(Server).filter(
        Server.id == server_id,
        Server.organization_id == current_org.id,
        Server.is_active == True
    ).first()

    if not server:
        raise HTTPException(status_code=404, detail="Server not found.")

    update_server_online_status(server)
    latest_metric = db.query(Metric).filter(Metric.server_id == server.id).order_by(Metric.timestamp.desc()).first()

    return ServerOut(
        id=server.id,
        organization_id=server.organization_id,
        name=server.name,
        description=server.description,
        hostname=server.hostname,
        os=server.os,
        os_version=server.os_version,
        architecture=server.architecture,
        ip_address=server.ip_address,
        status=server.status,
        last_heartbeat=server.last_heartbeat,
        registration_token=server.registration_token,
        is_active=server.is_active,
        created_at=server.created_at,
        latest_cpu=latest_metric.cpu_percent if latest_metric else None,
        latest_ram=latest_metric.ram_percent if latest_metric else None,
        latest_disk=latest_metric.disk_percent if latest_metric else None
    )


@router.put("/{server_id}", response_model=ServerOut)
def update_server(
    server_id: str,
    update_in: ServerUpdate,
    current_org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
) -> Any:
    server = db.query(Server).filter(
        Server.id == server_id,
        Server.organization_id == current_org.id
    ).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found.")

    if update_in.name is not None:
        server.name = update_in.name
    if update_in.description is not None:
        server.description = update_in.description

    db.commit()
    db.refresh(server)
    return server


@router.delete("/{server_id}")
def delete_server(
    server_id: str,
    current_org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
) -> Any:
    server = db.query(Server).filter(
        Server.id == server_id,
        Server.organization_id == current_org.id
    ).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found.")

    server.is_active = False
    server.status = "offline"
    db.commit()
    return {"message": f"Server '{server.name}' has been deregistered successfully."}
