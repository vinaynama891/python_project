"""
CloudPulse Executive Reports Endpoints
"""
from typing import Any
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_org, get_db
from backend.app.models.models import Organization
from backend.app.services.report_service import report_service

router = APIRouter()


@router.get("/daily")
def get_daily_report(
    current_org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
) -> Any:
    return report_service.get_summary_report(db, current_org.id, days=1)


@router.get("/weekly")
def get_weekly_report(
    current_org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
) -> Any:
    return report_service.get_summary_report(db, current_org.id, days=7)


@router.get("/export")
def export_report(
    format: str = Query("csv", pattern="^(csv|pdf)$"),
    days: int = Query(7, ge=1, le=90),
    current_org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
) -> Any:
    if format == "csv":
        csv_data = report_service.generate_csv(db, current_org.id, days=days)
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=cloudpulse_report_{days}d.csv"}
        )
    else:
        pdf_bytes = report_service.generate_pdf(db, current_org.id, days=days)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=cloudpulse_report_{days}d.pdf"}
        )
