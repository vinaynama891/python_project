"""
CloudPulse Infrastructure Analytics Endpoints
"""
from typing import Any, Dict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_org, get_db
from backend.app.models.models import Organization, Server, Metric, Alert
from backend.app.schemas.schemas import OverviewAnalytics
from backend.app.services.alert_service import AlertEngine
from backend.app.core.config import settings

router = APIRouter()


@router.get("/overview", response_model=OverviewAnalytics)
def get_overview_analytics(
    current_org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
) -> Any:
    """Aggregates enterprise overview counters across all registered servers."""
    AlertEngine.check_heartbeat_timeouts(db, settings.DEFAULT_HEARTBEAT_TIMEOUT_SECONDS)

    servers = db.query(Server).filter(
        Server.organization_id == current_org.id,
        Server.is_active == True
    ).all()

    total_servers = len(servers)
    online_servers = sum(1 for s in servers if s.status == "online")
    offline_servers = sum(1 for s in servers if s.status == "offline")
    warning_servers = sum(1 for s in servers if s.status == "warning")
    critical_servers = sum(1 for s in servers if s.status == "critical")

    latest_metrics = []
    total_up_speed = 0.0
    total_down_speed = 0.0

    for s in servers:
        m = db.query(Metric).filter(Metric.server_id == s.id).order_by(Metric.timestamp.desc()).first()
        if m:
            latest_metrics.append(m)
            total_up_speed += (m.net_upload_speed or 0.0)
            total_down_speed += (m.net_download_speed or 0.0)

    if latest_metrics:
        avg_cpu = sum(m.cpu_percent for m in latest_metrics) / len(latest_metrics)
        avg_ram = sum(m.ram_percent for m in latest_metrics) / len(latest_metrics)
        avg_disk = sum(m.disk_percent for m in latest_metrics) / len(latest_metrics)
    else:
        avg_cpu = avg_ram = avg_disk = 0.0

    active_alerts = db.query(Alert).filter(
        Alert.organization_id == current_org.id,
        Alert.status == "active"
    ).count()

    return OverviewAnalytics(
        total_servers=total_servers,
        online_servers=online_servers,
        offline_servers=offline_servers,
        warning_servers=warning_servers,
        critical_servers=critical_servers,
        avg_cpu_percent=round(avg_cpu, 1),
        avg_ram_percent=round(avg_ram, 1),
        avg_disk_percent=round(avg_disk, 1),
        total_network_upload_speed=round(total_up_speed, 1),
        total_network_download_speed=round(total_down_speed, 1),
        active_alerts_count=active_alerts
    )


@router.get("/cpu")
def get_cpu_analytics(
    current_org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
) -> Any:
    servers = db.query(Server).filter(Server.organization_id == current_org.id, Server.is_active == True).all()
    data = []
    for s in servers:
        m = db.query(Metric).filter(Metric.server_id == s.id).order_by(Metric.timestamp.desc()).first()
        data.append({
            "server_id": s.id,
            "server_name": s.name,
            "status": s.status,
            "cpu_percent": m.cpu_percent if m else 0.0,
            "cpu_cores": m.cpu_cores if m else 1,
            "frequency": m.cpu_frequency_current if m else 0.0
        })
    return sorted(data, key=lambda x: x["cpu_percent"], reverse=True)


@router.get("/memory")
def get_memory_analytics(
    current_org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
) -> Any:
    servers = db.query(Server).filter(Server.organization_id == current_org.id, Server.is_active == True).all()
    data = []
    for s in servers:
        m = db.query(Metric).filter(Metric.server_id == s.id).order_by(Metric.timestamp.desc()).first()
        data.append({
            "server_id": s.id,
            "server_name": s.name,
            "status": s.status,
            "ram_percent": m.ram_percent if m else 0.0,
            "ram_used_gb": round(m.ram_used / 1e9, 2) if m else 0.0,
            "ram_total_gb": round(m.ram_total / 1e9, 2) if m else 0.0
        })
    return sorted(data, key=lambda x: x["ram_percent"], reverse=True)


@router.get("/disk")
def get_disk_analytics(
    current_org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
) -> Any:
    servers = db.query(Server).filter(Server.organization_id == current_org.id, Server.is_active == True).all()
    data = []
    for s in servers:
        m = db.query(Metric).filter(Metric.server_id == s.id).order_by(Metric.timestamp.desc()).first()
        data.append({
            "server_id": s.id,
            "server_name": s.name,
            "disk_percent": m.disk_percent if m else 0.0,
            "disk_used_gb": round(m.disk_used / 1e9, 2) if m else 0.0,
            "disk_total_gb": round(m.disk_total / 1e9, 2) if m else 0.0
        })
    return sorted(data, key=lambda x: x["disk_percent"], reverse=True)


@router.get("/network")
def get_network_analytics(
    current_org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
) -> Any:
    servers = db.query(Server).filter(Server.organization_id == current_org.id, Server.is_active == True).all()
    data = []
    for s in servers:
        m = db.query(Metric).filter(Metric.server_id == s.id).order_by(Metric.timestamp.desc()).first()
        data.append({
            "server_id": s.id,
            "server_name": s.name,
            "upload_speed_kb_s": round((m.net_upload_speed or 0.0) / 1024, 2) if m else 0.0,
            "download_speed_kb_s": round((m.net_download_speed or 0.0) / 1024, 2) if m else 0.0,
            "packets_sent": m.net_packets_sent if m else 0,
            "packets_recv": m.net_packets_recv if m else 0
        })
    return sorted(data, key=lambda x: x["upload_speed_kb_s"] + x["download_speed_kb_s"], reverse=True)
