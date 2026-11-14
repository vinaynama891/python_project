"""
CloudPulse Performance Profiler Endpoints
"""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_org, get_db
from backend.app.models.models import Organization, Server
from backend.app.services.profiler_service import profiler_service

router = APIRouter()


@router.get("/server/{server_id}")
def profile_server(
    server_id: str,
    current_org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
) -> Any:
    """Profiles a specific server, diagnosing bottlenecks and generating tuning suggestions."""
    server = db.query(Server).filter(
        Server.id == server_id,
        Server.organization_id == current_org.id
    ).first()

    if not server:
        raise HTTPException(status_code=404, detail="Server not found.")

    analysis = profiler_service.analyze_server(db, server_id)
    return analysis
