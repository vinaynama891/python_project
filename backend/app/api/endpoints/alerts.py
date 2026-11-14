"""
CloudPulse Alerts Endpoints
"""
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_current_org, get_db
from backend.app.models.models import Organization, Alert, User, Server
from backend.app.schemas.schemas import AlertOut, AlertAcknowledge, AlertResolve
from backend.app.services.alert_service import AlertEngine

router = APIRouter()


@router.get("", response_model=List[AlertOut])
def list_alerts(
    status_filter: Optional[str] = Query("active", alias="status"),
    severity: Optional[str] = Query(None),
    server_id: Optional[str] = Query(None),
    current_org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
) -> Any:
    """Lists alerts filtered by status, severity, or server."""
    query = db.query(Alert).filter(Alert.organization_id == current_org.id)

    if status_filter and status_filter.lower() != "all":
        query = query.filter(Alert.status == status_filter.lower())

    if severity:
        query = query.filter(Alert.severity == severity.lower())

    if server_id:
        query = query.filter(Alert.server_id == server_id)

    alerts = query.order_by(Alert.created_at.desc()).all()
    results = []

    for a in alerts:
        server = db.query(Server).filter(Server.id == a.server_id).first()
        results.append(AlertOut(
            id=a.id,
            server_id=a.server_id,
            server_name=server.name if server else "Unknown",
            metric_type=a.metric_type,
            severity=a.severity,
            message=a.message,
            value=a.value,
            threshold=a.threshold,
            status=a.status,
            acknowledged_at=a.acknowledged_at,
            resolved_at=a.resolved_at,
            acknowledged_by=a.acknowledged_by,
            resolved_by=a.resolved_by,
            created_at=a.created_at
        ))

    return results


@router.get("/{alert_id}", response_model=AlertOut)
def get_alert(
    alert_id: str,
    current_org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
) -> Any:
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.organization_id == current_org.id
    ).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")

    server = db.query(Server).filter(Server.id == alert.server_id).first()
    return AlertOut(
        id=alert.id,
        server_id=alert.server_id,
        server_name=server.name if server else "Unknown",
        metric_type=alert.metric_type,
        severity=alert.severity,
        message=alert.message,
        value=alert.value,
        threshold=alert.threshold,
        status=alert.status,
        acknowledged_at=alert.acknowledged_at,
        resolved_at=alert.resolved_at,
        acknowledged_by=alert.acknowledged_by,
        resolved_by=alert.resolved_by,
        created_at=alert.created_at
    )


@router.put("/{alert_id}/acknowledge", response_model=AlertOut)
def acknowledge_alert_endpoint(
    alert_id: str,
    body: Optional[AlertAcknowledge] = None,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
) -> Any:
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.organization_id == current_org.id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")

    ack_name = body.acknowledged_by if body and body.acknowledged_by else current_user.full_name or current_user.email
    updated = AlertEngine.acknowledge_alert(db, alert_id, acknowledged_by=ack_name)
    server = db.query(Server).filter(Server.id == updated.server_id).first()

    return AlertOut(
        id=updated.id,
        server_id=updated.server_id,
        server_name=server.name if server else "Unknown",
        metric_type=updated.metric_type,
        severity=updated.severity,
        message=updated.message,
        value=updated.value,
        threshold=updated.threshold,
        status=updated.status,
        acknowledged_at=updated.acknowledged_at,
        resolved_at=updated.resolved_at,
        acknowledged_by=updated.acknowledged_by,
        resolved_by=updated.resolved_by,
        created_at=updated.created_at
    )


@router.put("/{alert_id}/resolve", response_model=AlertOut)
def resolve_alert_endpoint(
    alert_id: str,
    body: Optional[AlertResolve] = None,
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
) -> Any:
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.organization_id == current_org.id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")

    res_name = body.resolved_by if body and body.resolved_by else current_user.full_name or current_user.email
    updated = AlertEngine.resolve_alert(db, alert_id, resolved_by=res_name)
    server = db.query(Server).filter(Server.id == updated.server_id).first()

    return AlertOut(
        id=updated.id,
        server_id=updated.server_id,
        server_name=server.name if server else "Unknown",
        metric_type=updated.metric_type,
        severity=updated.severity,
        message=updated.message,
        value=updated.value,
        threshold=updated.threshold,
        status=updated.status,
        acknowledged_at=updated.acknowledged_at,
        resolved_at=updated.resolved_at,
        acknowledged_by=updated.acknowledged_by,
        resolved_by=updated.resolved_by,
        created_at=updated.created_at
    )
