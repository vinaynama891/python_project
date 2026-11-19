"""Machine Learning anomaly detection utilities.

This module implements a lightweight training and inference pipeline using
scikit‑learn's ``IsolationForest``. It provides two public functions:

* ``train_model`` – called by ``/api/ai/train``. It gathers all telemetry
  metrics for a given organization, fits an IsolationForest model, persists the
  model to ``backend/app/ml/models/`` and updates ``ModelMetadata``.
* ``detect_anomalies`` – called by the ``/api/ai/detect/{server_id}`` endpoint.
  It loads the latest active model for the server's organization, scores recent
  metrics, creates ``AnomalyLog`` and ``Alert`` rows for any outliers, and returns
  a structured list.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
import pathlib
import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest

from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.models.models import (
    Metric,
    ModelMetadata,
    AnomalyLog,
    Alert,
    Server,
    Organization,
)

# ---------------------------------------------------------------------------
# Helper: collect metric rows for an organization
# ---------------------------------------------------------------------------

def _load_metrics_for_org(db: Session, org_id: str) -> pd.DataFrame:
    """Return a DataFrame of numeric telemetry for *all* servers in ``org_id``.

    Only the columns required for a basic anomaly detection are kept. Missing
    values are filled with ``0`` (the model can handle zeros because they simply
    represent "no activity").
    """
    query = (
        db.query(Metric)
        .join(Server, Metric.server_id == Server.id)
        .filter(Server.organization_id == org_id)
    )
    raw = [m.__dict__ for m in query]
    if not raw:
        return pd.DataFrame()
    df = pd.DataFrame(raw)
    cols = [
        "cpu_percent",
        "ram_percent",
        "disk_percent",
        "net_bytes_sent",
        "net_bytes_recv",
    ]
    df = df[cols].fillna(0)
    return df

# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def train_model(db: Session, org_id: str, contamination: float = 0.05) -> Dict[str, Any]:
    """Train (or retrain) the IsolationForest model for ``org_id``.

    Parameters
    ----------
    db: Session
        Active SQLAlchemy session.
    org_id: str
        Organization UUID.
    contamination: float, optional
        Expected proportion of anomalies in the training data. Default ``0.05``.

    Returns
    -------
    dict
        Summary of the training run – compatible with the API schema
        ``ModelStatusOut``.
    """
    df = _load_metrics_for_org(db, org_id)
    if df.empty:
        return {
            "is_trained": False,
            "model_name": "IsolationForestAnomalyDetector",
            "algorithm": "Isolation Forest (Scikit-learn)",
            "version": "1.0.0",
            "training_samples": 0,
            "last_trained": None,
            "status_message": "No metric data available for training.",
        }

    model = IsolationForest(contamination=contamination, random_state=42)
    model.fit(df)

    # Persist the model file – deterministic path per organization
    models_dir = pathlib.Path(__file__).parent / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    model_file = models_dir / f"isolation_{org_id}.pkl"
    joblib.dump(model, model_file)

    # Update or create ModelMetadata entry
    meta = (
        db.query(ModelMetadata)
        .filter(ModelMetadata.organization_id == org_id, ModelMetadata.is_active == True)
        .first()
    )
    if not meta:
        meta = ModelMetadata(
            organization_id=org_id,
            model_name="IsolationForestAnomalyDetector",
            version="1.0.0",
            algorithm="Isolation Forest (Scikit-learn)",
            training_samples=len(df),
            file_path=str(model_file),
            is_active=True,
        )
        db.add(meta)
    else:
        # Deactivate previous model and add a new active one
        meta.is_active = False
        db.flush()
        meta = ModelMetadata(
            organization_id=org_id,
            model_name="IsolationForestAnomalyDetector",
            version="1.0.0",
            algorithm="Isolation Forest (Scikit-learn)",
            training_samples=len(df),
            file_path=str(model_file),
            is_active=True,
        )
        db.add(meta)

    db.commit()

    return {
        "is_trained": True,
        "model_name": meta.model_name,
        "algorithm": meta.algorithm,
        "version": meta.version,
        "training_samples": meta.training_samples,
        "last_trained": meta.created_at,
        "status_message": f"Model trained on {meta.training_samples} metric records.",
    }

# ---------------------------------------------------------------------------
# Inference / detection
# ---------------------------------------------------------------------------

def detect_anomalies(db: Session, server_id: str, minutes: int = 60) -> List[Dict[str, Any]]:
    """Score recent metrics for ``server_id`` and store anomalies.

    This function is used by the ``POST /ai/detect/{server_id}`` endpoint.
    It returns a list of dictionaries describing each detected anomaly.
    """
    # Load server and organization context
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise ValueError("Server not found")
    org_id = server.organization_id

    # Load active model metadata for the organization
    meta = (
        db.query(ModelMetadata)
        .filter(ModelMetadata.organization_id == org_id, ModelMetadata.is_active == True)
        .order_by(ModelMetadata.created_at.desc())
        .first()
    )
    if not meta or not meta.file_path:
        raise RuntimeError("No trained anomaly detection model available for this organization.")

    model = joblib.load(meta.file_path)

    # Fetch recent metrics for the server
    cutoff = datetime.utcnow() - timedelta(minutes=minutes)
    metrics = (
        db.query(Metric)
        .filter(Metric.server_id == server_id, Metric.timestamp >= cutoff)
        .order_by(Metric.timestamp.asc())
        .all()
    )
    if not metrics:
        return []

    df = pd.DataFrame([m.__dict__ for m in metrics])
    cols = ["cpu_percent", "ram_percent", "disk_percent", "net_bytes_sent", "net_bytes_recv"]
    df = df[cols].fillna(0)

    # IsolationForest decision_function returns higher scores for normal points;
    # negative values indicate outliers.
    scores = model.decision_function(df)
    anomaly_flags = scores < 0

    results: List[Dict[str, Any]] = []
    for metric_obj, score, is_anomaly in zip(metrics, scores, anomaly_flags):
        if not is_anomaly:
            continue
        # Persist AnomalyLog
        log = AnomalyLog(
            organization_id=org_id,
            server_id=server_id,
            anomaly_score=float(score),
            is_anomaly=True,
            cpu_val=metric_obj.cpu_percent,
            ram_val=metric_obj.ram_percent,
            disk_val=metric_obj.disk_percent,
            net_val=metric_obj.net_bytes_sent + metric_obj.net_bytes_recv,
            explanation="IsolationForest outlier",
            timestamp=metric_obj.timestamp,
        )
        db.add(log)
        # Create Alert for immediate visibility
        alert = Alert(
            organization_id=org_id,
            server_id=server_id,
            metric_type="ai_anomaly",
            severity="critical",
            message="AI detected anomalous telemetry",
            value=score,
            created_at=datetime.utcnow(),
        )
        db.add(alert)
        results.append(
            {
                "timestamp": metric_obj.timestamp,
                "score": float(score),
                "cpu": metric_obj.cpu_percent,
                "ram": metric_obj.ram_percent,
                "disk": metric_obj.disk_percent,
                "net": metric_obj.net_bytes_sent + metric_obj.net_bytes_recv,
            }
        )
    db.commit()
    return results

# ---------------------------------------------------------------------------
# Backward‑compatible wrapper for legacy imports
# ---------------------------------------------------------------------------

# Preserve original function under a private name to avoid recursion in the wrapper.
_detect_anomalies = detect_anomalies


class MLService:
    @staticmethod
    def evaluate_live_metric(db, server, metric_record):
        """Safely evaluate a live metric.
        If no trained model exists, attempt to train one automatically.
        If training fails or not enough data, return ``None`` instead of raising.
        """
        try:
            results = _detect_anomalies(db, server.id, minutes=1)
        except RuntimeError:
            # No model – try to auto-train if we have sufficient data
            count = db.query(func.count()).select_from(Metric).filter(
                Metric.server_id == server.id
            ).scalar()
            if count and count >= 50:
                train_model(db, server.organization_id, contamination=0.05)
                try:
                    results = _detect_anomalies(db, server.id, minutes=1)
                except RuntimeError:
                    return None
            else:
                return None
        for r in results:
            if r.get("timestamp") == metric_record.timestamp:
                return r
        return None

    @staticmethod
    def detect_anomalies(db, server_id, minutes=60):
        """Thin wrapper to keep backward compatibility with legacy imports."""
        return _detect_anomalies(db, server_id, minutes)

    @staticmethod
    def train_model(db, org_id, contamination=0.05):
        """Wrapper around the module-level train_model."""
        return train_model(db, org_id, contamination)


# Expose a singleton compatible with previous `ml_service` import
ml_service = MLService()


