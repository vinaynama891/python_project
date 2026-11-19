"""
CloudPulse Performance Debt Tracker (PDT) API Endpoints
"""
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_org, get_db
from backend.app.models.models import Organization, Server
from backend.app.models.pdt_models import PerformanceDebt
from backend.app.services.pdt_service import pdt_service
from backend.app.schemas.schemas import (
    PerformanceDebtOut, PerformanceDebtUpdate, PerformanceDebtSummary
)

router = APIRouter()


@router.get("/debts", response_model=List[PerformanceDebtOut])
def list_performance_debts(
    status: Optional[str] = Query(None, description="Filter by status: open, investigating, mitigated, closed"),
    category: Optional[str] = Query(None, description="Filter by category: cpu, memory, disk, network, process"),
    server_id: Optional[str] = Query(None, description="Filter by server ID"),
    impact: Optional[str] = Query(None, description="Filter by impact: low, medium, high, critical"),
    current_org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
) -> Any:
    """List all performance debt items for the current organization with optional filters."""
    query = db.query(PerformanceDebt).filter(
        PerformanceDebt.organization_id == current_org.id
    )
    
    if status:
        query = query.filter(PerformanceDebt.status == status)
    if category:
        query = query.filter(PerformanceDebt.category == category)
    if server_id:
        query = query.filter(PerformanceDebt.server_id == server_id)
    if impact:
        query = query.filter(PerformanceDebt.estimated_impact == impact)
    
    debts = query.order_by(PerformanceDebt.debt_score.desc()).all()
    
    # Enrich with server name
    result = []
    for debt in debts:
        server = db.query(Server).filter(Server.id == debt.server_id).first()
        debt_dict = {
            "id": debt.id,
            "server_id": debt.server_id,
            "server_name": server.name if server else "Unknown",
            "organization_id": debt.organization_id,
            "category": debt.category,
            "title": debt.title,
            "description": debt.description,
            "debt_score": debt.debt_score,
            "trend_direction": debt.trend_direction,
            "occurrence_count": debt.occurrence_count,
            "first_detected_at": debt.first_detected_at,
            "last_detected_at": debt.last_detected_at,
            "avg_metric_value": debt.avg_metric_value,
            "peak_metric_value": debt.peak_metric_value,
            "threshold_value": debt.threshold_value,
            "estimated_impact": debt.estimated_impact,
            "status": debt.status,
            "resolution_notes": debt.resolution_notes,
            "resolved_at": debt.resolved_at,
            "resolved_by": debt.resolved_by,
            "created_at": debt.created_at,
        }
        result.append(debt_dict)
    
    return result


@router.get("/summary")
def get_debt_summary(
    current_org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
) -> Any:
    """Returns aggregate summary statistics for performance debts across the organization."""
    return pdt_service.get_debt_summary(db, current_org.id)


@router.get("/analyze/{server_id}")
def analyze_server_debt(
    server_id: str,
    hours: int = Query(24, ge=1, le=168, description="Analysis window in hours (1-168)"),
    current_org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
) -> Any:
    """Analyzes a server's historical metrics to detect recurring performance degradation patterns."""
    server = db.query(Server).filter(
        Server.id == server_id,
        Server.organization_id == current_org.id
    ).first()
    
    if not server:
        raise HTTPException(status_code=404, detail="Server not found in your organization.")
    
    return pdt_service.analyze_server_debt(db, server_id, hours)


@router.get("/debts/{debt_id}", response_model=PerformanceDebtOut)
def get_debt_detail(
    debt_id: str,
    current_org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
) -> Any:
    """Get detailed information about a specific performance debt item."""
    debt = db.query(PerformanceDebt).filter(
        PerformanceDebt.id == debt_id,
        PerformanceDebt.organization_id == current_org.id
    ).first()
    
    if not debt:
        raise HTTPException(status_code=404, detail="Performance debt item not found.")
    
    server = db.query(Server).filter(Server.id == debt.server_id).first()
    debt_dict = {
        "id": debt.id,
        "server_id": debt.server_id,
        "server_name": server.name if server else "Unknown",
        "organization_id": debt.organization_id,
        "category": debt.category,
        "title": debt.title,
        "description": debt.description,
        "debt_score": debt.debt_score,
        "trend_direction": debt.trend_direction,
        "occurrence_count": debt.occurrence_count,
        "first_detected_at": debt.first_detected_at,
        "last_detected_at": debt.last_detected_at,
        "avg_metric_value": debt.avg_metric_value,
        "peak_metric_value": debt.peak_metric_value,
        "threshold_value": debt.threshold_value,
        "estimated_impact": debt.estimated_impact,
        "status": debt.status,
        "resolution_notes": debt.resolution_notes,
        "resolved_at": debt.resolved_at,
        "resolved_by": debt.resolved_by,
        "created_at": debt.created_at,
    }
    return debt_dict


@router.put("/debts/{debt_id}")
def update_debt(
    debt_id: str,
    update_data: PerformanceDebtUpdate,
    current_org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
) -> Any:
    """Update a performance debt item (change status, add resolution notes, etc.)."""
    debt = db.query(PerformanceDebt).filter(
        PerformanceDebt.id == debt_id,
        PerformanceDebt.organization_id == current_org.id
    ).first()
    
    if not debt:
        raise HTTPException(status_code=404, detail="Performance debt item not found.")
    
    if update_data.status:
        debt.status = update_data.status
        if update_data.status in ["mitigated", "closed"]:
            from datetime import datetime, timezone
            debt.resolved_at = datetime.now(timezone.utc)
            debt.resolved_by = update_data.resolved_by or "Admin"
    
    if update_data.resolution_notes is not None:
        debt.resolution_notes = update_data.resolution_notes
    if update_data.debt_score is not None:
        debt.debt_score = update_data.debt_score
    if update_data.trend_direction is not None:
        debt.trend_direction = update_data.trend_direction
    if update_data.estimated_impact is not None:
        debt.estimated_impact = update_data.estimated_impact
    
    db.commit()
    db.refresh(debt)
    
    server = db.query(Server).filter(Server.id == debt.server_id).first()
    return {
        "id": debt.id,
        "server_id": debt.server_id,
        "server_name": server.name if server else "Unknown",
        "category": debt.category,
        "title": debt.title,
        "debt_score": debt.debt_score,
        "status": debt.status,
        "trend_direction": debt.trend_direction,
        "estimated_impact": debt.estimated_impact,
        "resolution_notes": debt.resolution_notes,
        "message": f"Debt item updated to '{debt.status}'."
    }
