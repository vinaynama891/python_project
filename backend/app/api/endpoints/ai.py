"""
CloudPulse AI & Anomaly Detection Endpoints
"""
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_org, get_db
from backend.app.models.models import Organization, AnomalyLog, ModelMetadata, Recommendation, Server
from backend.app.schemas.schemas import AnomalyOut, ModelStatusOut, RecommendationOut
from backend.app.ml.anomaly_detector import ml_service

router = APIRouter()


@router.get("/anomalies", response_model=List[AnomalyOut])
def get_anomalies(
    limit: int = Query(50, ge=1, le=200),
    server_id: Optional[str] = Query(None),
    current_org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
) -> Any:
    """Lists anomaly detection logs identified by the Scikit-learn model."""
    query = db.query(AnomalyLog).filter(
        AnomalyLog.organization_id == current_org.id
    )
    if server_id:
        query = query.filter(AnomalyLog.server_id == server_id)

    logs = query.order_by(AnomalyLog.timestamp.desc()).limit(limit).all()
    results = []
    for l in logs:
        server = db.query(Server).filter(Server.id == l.server_id).first()
        results.append(AnomalyOut(
            id=l.id,
            server_id=l.server_id,
            server_name=server.name if server else "Unknown",
            timestamp=l.timestamp,
            anomaly_score=l.anomaly_score,
            is_anomaly=l.is_anomaly,
            cpu_val=l.cpu_val,
            ram_val=l.ram_val,
            disk_val=l.disk_val,
            net_val=l.net_val,
            explanation=l.explanation,
            created_at=l.created_at
        ))
    return results


@router.post("/detect/{server_id}", response_model=List[AnomalyOut])
def detect_anomalies_endpoint(
    server_id: str,
    minutes: int = Query(60, ge=1, le=1440),
    current_org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db),
) -> Any:
    """Detect anomalies for a specific server and return them.

    The endpoint triggers the ML model to score recent metrics for ``server_id``
    (default look‑back is 60 minutes). Detected outliers are persisted as
    ``AnomalyLog`` rows and corresponding ``Alert`` entries, then the newest
    anomaly logs for that server are returned.
    """
    # Verify the server belongs to the organization
    server = (
        db.query(Server)
        .filter(Server.id == server_id, Server.organization_id == current_org.id)
        .first()
    )
    if not server:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Server not found in your organization")

    # Run detection – this will create AnomalyLog and Alert entries
    ml_service.detect_anomalies(db, server_id, minutes=minutes)

    # Return the freshly created anomaly logs for this server
    logs = (
        db.query(AnomalyLog)
        .filter(AnomalyLog.organization_id == current_org.id, AnomalyLog.server_id == server_id)
        .order_by(AnomalyLog.timestamp.desc())
        .all()
    )
    results = []
    for l in logs:
        results.append(
            AnomalyOut(
                id=l.id,
                server_id=l.server_id,
                server_name=server.name,
                timestamp=l.timestamp,
                anomaly_score=l.anomaly_score,
                is_anomaly=l.is_anomaly,
                cpu_val=l.cpu_val,
                ram_val=l.ram_val,
                disk_val=l.disk_val,
                net_val=l.net_val,
                explanation=l.explanation,
                created_at=l.created_at,
            )
        )
    return results


@router.post("/detect/{server_id}", response_model=List[AnomalyOut])
def detect_anomalies_endpoint(
    server_id: str,
    minutes: int = Query(60, ge=1, le=1440),
    current_org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db),
) -> Any:
    """Detect anomalies for a specific server and return them.

    The endpoint triggers the ML model to score recent metrics for ``server_id``
    (default look‑back is 60 minutes). Detected outliers are persisted as
    ``AnomalyLog`` rows and corresponding ``Alert`` entries, then the newest
    anomaly logs for that server are returned.
    """
    # Verify the server belongs to the organization
    server = (
        db.query(Server)
        .filter(Server.id == server_id, Server.organization_id == current_org.id)
        .first()
    )
    if not server:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Server not found in your organization")

    # Run detection – this will create AnomalyLog and Alert entries
    ml_service.detect_anomalies(db, server_id, minutes=minutes)

    # Return the freshly created anomaly logs for this server
    logs = (
        db.query(AnomalyLog)
        .filter(AnomalyLog.organization_id == current_org.id, AnomalyLog.server_id == server_id)
        .order_by(AnomalyLog.timestamp.desc())
        .all()
    )
    results = []
    for l in logs:
        results.append(
            AnomalyOut(
                id=l.id,
                server_id=l.server_id,
                server_name=server.name,
                timestamp=l.timestamp,
                anomaly_score=l.anomaly_score,
                is_anomaly=l.is_anomaly,
                cpu_val=l.cpu_val,
                ram_val=l.ram_val,
                disk_val=l.disk_val,
                net_val=l.net_val,
                explanation=l.explanation,
                created_at=l.created_at,
            )
        )
    return results


@router.post("/detect/{server_id}", response_model=List[AnomalyOut])
def detect_anomalies_endpoint(
    server_id: str,
    minutes: int = Query(60, ge=1, le=1440),
    current_org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db),
) -> Any:
    """Detect anomalies for a specific server and return them.

    The endpoint triggers the ML model to score recent metrics for ``server_id``
    (default look‑back is 60 minutes). Detected outliers are persisted as
    ``AnomalyLog`` rows and corresponding ``Alert`` entries, then the newest
    anomaly logs for that server are returned.
    """
    # Verify the server belongs to the organization
    server = (
        db.query(Server)
        .filter(Server.id == server_id, Server.organization_id == current_org.id)
        .first()
    )
    if not server:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Server not found in your organization")

    # Run detection – this will create AnomalyLog and Alert entries
    ml_service.detect_anomalies(db, server_id, minutes=minutes)

    # Return the freshly created anomaly logs for this server
    logs = (
        db.query(AnomalyLog)
        .filter(AnomalyLog.organization_id == current_org.id, AnomalyLog.server_id == server_id)
        .order_by(AnomalyLog.timestamp.desc())
        .all()
    )
    results = []
    for l in logs:
        results.append(
            AnomalyOut(
                id=l.id,
                server_id=l.server_id,
                server_name=server.name,
                timestamp=l.timestamp,
                anomaly_score=l.anomaly_score,
                is_anomaly=l.is_anomaly,
                cpu_val=l.cpu_val,
                ram_val=l.ram_val,
                disk_val=l.disk_val,
                net_val=l.net_val,
                explanation=l.explanation,
                created_at=l.created_at,
            )
        )
    return results


@router.post("/train")
def train_anomaly_model(
    contamination: float = Query(0.05, ge=0.01, le=0.5),
    current_org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
) -> Any:
    """Trains or retrains the Isolation Forest model on historical real metrics."""
    result = ml_service.train_model(db, current_org.id, contamination=contamination)
    return result


@router.get("/model-status", response_model=ModelStatusOut)
def get_model_status(
    current_org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
) -> Any:
    """Returns training state, sample count, and metadata of the anomaly detection model."""
    meta = db.query(ModelMetadata).filter(
        ModelMetadata.organization_id == current_org.id,
        ModelMetadata.is_active == True
    ).first()

    if not meta:
        return ModelStatusOut(
            is_trained=False,
            model_name="IsolationForestAnomalyDetector",
            algorithm="Isolation Forest (Scikit-learn)",
            version="1.0.0",
            training_samples=0,
            last_trained=None,
            status_message="Insufficient historical data to train the anomaly detection model. (Awaiting metric ingestion)"
        )

    return ModelStatusOut(
        is_trained=True,
        model_name=meta.model_name,
        algorithm=meta.algorithm,
        version=meta.version,
        training_samples=meta.training_samples,
        last_trained=meta.created_at,
        status_message=f"Model trained on {meta.training_samples} historical telemetry records."
    )


@router.get("/recommendations", response_model=List[RecommendationOut])
def get_recommendations(
    server_id: Optional[str] = Query(None),
    current_org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
) -> Any:
    """Lists intelligent optimization recommendations generated by the profiler engine."""
    query = db.query(Recommendation).filter(
        Recommendation.organization_id == current_org.id
    )
    if server_id:
        query = query.filter(Recommendation.server_id == server_id)

    recs = query.order_by(Recommendation.created_at.desc()).all()
    results = []
    for r in recs:
        server = db.query(Server).filter(Server.id == r.server_id).first()
        results.append(RecommendationOut(
            id=r.id,
            server_id=r.server_id,
            server_name=server.name if server else "Unknown",
            category=r.category,
            title=r.title,
            description=r.description,
            impact=r.impact,
            suggested_action=r.suggested_action,
            is_applied=r.is_applied,
            created_at=r.created_at
        ))
    return results


@router.post("/detect/{server_id}", response_model=List[AnomalyOut])
def detect_anomalies_endpoint(
    server_id: str,
    minutes: int = Query(60, ge=1, le=1440),
    current_org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db),
) -> Any:
    """Detect anomalies for a specific server and return them.

    The endpoint triggers the ML model to score recent metrics for ``server_id``
    (default look‑back is 60 minutes). Detected outliers are persisted as
    ``AnomalyLog`` rows and corresponding ``Alert`` entries, then the newest
    anomaly logs for that server are returned.
    """
    # Verify the server belongs to the organization
    server = (
        db.query(Server)
        .filter(Server.id == server_id, Server.organization_id == current_org.id)
        .first()
    )
    if not server:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Server not found in your organization")

    # Run detection – this will create AnomalyLog and Alert entries
    ml_service.detect_anomalies(db, server_id, minutes=minutes)

    # Return the freshly created anomaly logs for this server
    logs = (
        db.query(AnomalyLog)
        .filter(AnomalyLog.organization_id == current_org.id, AnomalyLog.server_id == server_id)
        .order_by(AnomalyLog.timestamp.desc())
        .all()
    )
    results = []
    for l in logs:
        results.append(
            AnomalyOut(
                id=l.id,
                server_id=l.server_id,
                server_name=server.name,
                timestamp=l.timestamp,
                anomaly_score=l.anomaly_score,
                is_anomaly=l.is_anomaly,
                cpu_val=l.cpu_val,
                ram_val=l.ram_val,
                disk_val=l.disk_val,
                net_val=l.net_val,
                explanation=l.explanation,
                created_at=l.created_at,
            )
        )
    return results


@router.post("/detect/{server_id}", response_model=List[AnomalyOut])
def detect_anomalies_endpoint(
    server_id: str,
    minutes: int = Query(60, ge=1, le=1440),
    current_org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db),
) -> Any:
    """Detect anomalies for a specific server and return them.

    The endpoint triggers the ML model to score recent metrics for ``server_id``
    (default look‑back is 60 minutes). Detected outliers are persisted as
    ``AnomalyLog`` rows and corresponding ``Alert`` entries, then the newest
    anomaly logs for that server are returned.
    """
    # Verify the server belongs to the organization
    server = (
        db.query(Server)
        .filter(Server.id == server_id, Server.organization_id == current_org.id)
        .first()
    )
    if not server:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Server not found in your organization")

    # Run detection – this will create AnomalyLog and Alert entries
    ml_service.detect_anomalies(db, server_id, minutes=minutes)

    # Return the freshly created anomaly logs for this server
    logs = (
        db.query(AnomalyLog)
        .filter(AnomalyLog.organization_id == current_org.id, AnomalyLog.server_id == server_id)
        .order_by(AnomalyLog.timestamp.desc())
        .all()
    )
    results = []
    for l in logs:
        results.append(
            AnomalyOut(
                id=l.id,
                server_id=l.server_id,
                server_name=server.name,
                timestamp=l.timestamp,
                anomaly_score=l.anomaly_score,
                is_anomaly=l.is_anomaly,
                cpu_val=l.cpu_val,
                ram_val=l.ram_val,
                disk_val=l.disk_val,
                net_val=l.net_val,
                explanation=l.explanation,
                created_at=l.created_at,
            )
        )
    return results


@router.post("/detect/{server_id}", response_model=List[AnomalyOut])
def detect_anomalies_endpoint(
    server_id: str,
    minutes: int = Query(60, ge=1, le=1440),
    current_org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db),
) -> Any:
    """Detect anomalies for a specific server and return them.

    The endpoint triggers the ML model to score recent metrics for ``server_id``
    (default look‑back is 60 minutes). Detected outliers are persisted as
    ``AnomalyLog`` rows and corresponding ``Alert`` entries, then the newest
    anomaly logs for that server are returned.
    """
    # Verify the server belongs to the organization
    server = (
        db.query(Server)
        .filter(Server.id == server_id, Server.organization_id == current_org.id)
        .first()
    )
    if not server:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Server not found in your organization")

    # Run detection – this will create AnomalyLog and Alert entries
    ml_service.detect_anomalies(db, server_id, minutes=minutes)

    # Return the freshly created anomaly logs for this server
    logs = (
        db.query(AnomalyLog)
        .filter(AnomalyLog.organization_id == current_org.id, AnomalyLog.server_id == server_id)
        .order_by(AnomalyLog.timestamp.desc())
        .all()
    )
    results = []
    for l in logs:
        results.append(
            AnomalyOut(
                id=l.id,
                server_id=l.server_id,
                server_name=server.name,
                timestamp=l.timestamp,
                anomaly_score=l.anomaly_score,
                is_anomaly=l.is_anomaly,
                cpu_val=l.cpu_val,
                ram_val=l.ram_val,
                disk_val=l.disk_val,
                net_val=l.net_val,
                explanation=l.explanation,
                created_at=l.created_at,
            )
        )
    return results
