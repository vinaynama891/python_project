"""
CloudPulse Metrics Endpoints
Retrieves current and historical time-series telemetry data.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_org, get_db
from backend.app.models.models import Organization, Server, Metric, ProcessMetric
from backend.app.schemas.schemas import MetricOut, MetricHistoryPoint

router = APIRouter()


@router.get("/latest")
def get_latest_metrics(
    current_org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
) -> Any:
    """Returns the most recent metric record for all servers in the organization."""
    servers = db.query(Server).filter(Server.organization_id == current_org.id, Server.is_active == True).all()
    results = {}
    for s in servers:
        latest = db.query(Metric).filter(Metric.server_id == s.id).order_by(Metric.timestamp.desc()).first()
        if latest:
            results[s.id] = {
                "server_id": s.id,
                "server_name": s.name,
                "timestamp": latest.timestamp,
                "cpu_percent": latest.cpu_percent,
                "ram_percent": latest.ram_percent,
                "disk_percent": latest.disk_percent,
                "net_upload_speed": latest.net_upload_speed,
                "net_download_speed": latest.net_download_speed
            }
    return results


@router.get("/history", response_model=List[MetricHistoryPoint])
def get_metric_history(
    server_id: str = Query(...),
    hours: int = Query(1, ge=1, le=168),
    limit: int = Query(100, ge=10, le=1000),
    current_org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
) -> Any:
    """Retrieves time-series data points for charting."""
    server = db.query(Server).filter(
        Server.id == server_id,
        Server.organization_id == current_org.id
    ).first()

    if not server:
        raise HTTPException(status_code=404, detail="Server not found.")

    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    metrics = db.query(Metric).filter(
        Metric.server_id == server_id,
        Metric.timestamp >= since
    ).order_by(Metric.timestamp.asc()).limit(limit).all()

    return [
        MetricHistoryPoint(
            timestamp=m.timestamp,
            cpu_percent=m.cpu_percent,
            ram_percent=m.ram_percent,
            disk_percent=m.disk_percent,
            net_upload_speed=m.net_upload_speed or 0.0,
            net_download_speed=m.net_download_speed or 0.0
        )
        for m in metrics
    ]


@router.get("/{server_id}")
def get_server_detailed_metrics(
    server_id: str,
    current_org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
) -> Any:
    """Retrieves the full telemetry payload (system specs, CPU per core, top processes) for a server."""
    server = db.query(Server).filter(
        Server.id == server_id,
        Server.organization_id == current_org.id
    ).first()

    if not server:
        raise HTTPException(status_code=404, detail="Server not found.")

    latest = db.query(Metric).filter(Metric.server_id == server_id).order_by(Metric.timestamp.desc()).first()
    if not latest:
        return {
            "server_id": server_id,
            "has_metrics": False,
            "message": "No telemetry data collected yet."
        }

    top_procs = db.query(ProcessMetric).filter(
        ProcessMetric.server_id == server_id,
        ProcessMetric.metric_id == latest.id
    ).all()

    return {
        "server_id": server_id,
        "has_metrics": True,
        "latest": {
            "id": latest.id,
            "timestamp": latest.timestamp,
            "cpu_percent": latest.cpu_percent,
            "cpu_per_core": latest.cpu_per_core,
            "cpu_frequency_current": latest.cpu_frequency_current,
            "cpu_cores": latest.cpu_cores,
            "cpu_temperature": latest.cpu_temperature,
            "ram_total": latest.ram_total,
            "ram_used": latest.ram_used,
            "ram_available": latest.ram_available,
            "ram_percent": latest.ram_percent,
            "swap_percent": latest.swap_percent,
            "disk_total": latest.disk_total,
            "disk_used": latest.disk_used,
            "disk_free": latest.disk_free,
            "disk_percent": latest.disk_percent,
            "disk_read_speed": latest.disk_read_speed,
            "disk_write_speed": latest.disk_write_speed,
            "disk_io_ops": latest.disk_io_ops,
            "net_bytes_sent": latest.net_bytes_sent,
            "net_bytes_recv": latest.net_bytes_recv,
            "net_upload_speed": latest.net_upload_speed,
            "net_download_speed": latest.net_download_speed,
            "raw_details": latest.raw_details
        },
        "processes": [
            {
                "pid": p.pid,
                "name": p.name,
                "username": p.username,
                "status": p.status,
                "cpu_percent": p.cpu_percent,
                "memory_percent": p.memory_percent,
                "memory_bytes": p.memory_bytes
            }
            for p in top_procs
        ]
    }
