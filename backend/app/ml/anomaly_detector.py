"""
CloudPulse Machine Learning Anomaly Detection Engine
Uses Scikit-learn Isolation Forest with StandardScaler preprocessing to identify abnormal infrastructure behavior.
"""
import os
import pickle
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.models import Metric, AnomalyLog, ModelMetadata, Server

logger = logging.getLogger("CloudPulse.ML")

MODELS_DIR = Path(__file__).resolve().parent / "saved_models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


class AnomalyDetectionService:
    def __init__(self):
        self.model_cache: Dict[str, Tuple[IsolationForest, StandardScaler]] = {}

    def _extract_features(self, metrics: List[Metric]) -> Optional[pd.DataFrame]:
        """Converts raw SQLAlchemy metric records into engineered feature vectors."""
        if not metrics or len(metrics) < 2:
            return None

        data = []
        for m in metrics:
            net_throughput = (m.net_upload_speed or 0.0) + (m.net_download_speed or 0.0)
            data.append({
                "timestamp": m.timestamp,
                "cpu_percent": float(m.cpu_percent or 0.0),
                "ram_percent": float(m.ram_percent or 0.0),
                "disk_percent": float(m.disk_percent or 0.0),
                "net_throughput": float(net_throughput)
            })

        df = pd.DataFrame(data).sort_values("timestamp").reset_index(drop=True)
        # Compute trends (first-order differences)
        df["cpu_trend"] = df["cpu_percent"].diff().fillna(0.0)
        df["ram_trend"] = df["ram_percent"].diff().fillna(0.0)

        feature_cols = ["cpu_percent", "ram_percent", "disk_percent", "net_throughput", "cpu_trend", "ram_trend"]
        return df[feature_cols]

    def train_model(self, db: Session, org_id: str, contamination: float = 0.05) -> Dict[str, Any]:
        """
        Trains an Isolation Forest model using historical metrics collected across the organization's servers.
        Handles cold-start conditions transparently.
        """
        # Fetch servers belonging to this organization
        servers = db.query(Server).filter(Server.organization_id == org_id).all()
        server_ids = [s.id for s in servers]

        if not server_ids:
            return {
                "success": False,
                "message": "No registered servers found in this organization to train ML model.",
                "training_samples": 0
            }

        # Query metrics
        metrics = db.query(Metric).filter(
            Metric.server_id.in_(server_ids)
        ).order_by(Metric.timestamp.asc()).all()

        if len(metrics) < settings.ML_MIN_TRAINING_SAMPLES:
            return {
                "success": False,
                "message": f"Insufficient historical data to train the anomaly detection model (Need at least {settings.ML_MIN_TRAINING_SAMPLES} metric records; currently have {len(metrics)}).",
                "training_samples": len(metrics)
            }

        df_features = self._extract_features(metrics)
        if df_features is None or len(df_features) < settings.ML_MIN_TRAINING_SAMPLES:
            return {
                "success": False,
                "message": "Insufficient valid feature samples after preprocessing.",
                "training_samples": len(metrics)
            }

        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(df_features.values)

        # Train Isolation Forest
        model = IsolationForest(
            n_estimators=100,
            contamination=contamination,
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_scaled)

        # Cache model
        self.model_cache[org_id] = (model, scaler)

        # Save to disk
        model_file = MODELS_DIR / f"isolation_forest_org_{org_id}.pkl"
        with open(model_file, "wb") as f:
            pickle.dump({"model": model, "scaler": scaler}, f)

        # Record metadata in database
        meta = db.query(ModelMetadata).filter(
            ModelMetadata.organization_id == org_id,
            ModelMetadata.is_active == True
        ).first()

        summary = {
            "mean_cpu": float(df_features["cpu_percent"].mean()),
            "std_cpu": float(df_features["cpu_percent"].std()),
            "mean_ram": float(df_features["ram_percent"].mean()),
            "mean_disk": float(df_features["disk_percent"].mean()),
            "features": list(df_features.columns)
        }

        if not meta:
            meta = ModelMetadata(
                organization_id=org_id,
                model_name="IsolationForestAnomalyDetector",
                version="1.0.0",
                algorithm="Isolation Forest (Scikit-learn)",
                training_samples=len(df_features),
                metrics_summary=summary,
                file_path=str(model_file),
                is_active=True
            )
            db.add(meta)
        else:
            meta.training_samples = len(df_features)
            meta.metrics_summary = summary
            meta.updated_at = datetime.now(timezone.utc)

        db.commit()

        logger.info(f"Trained Isolation Forest for org {org_id} on {len(df_features)} samples.")
        return {
            "success": True,
            "message": f"Successfully trained Isolation Forest on {len(df_features)} telemetry records.",
            "training_samples": len(df_features),
            "summary": summary
        }

    def _load_model(self, org_id: str) -> Optional[Tuple[IsolationForest, StandardScaler]]:
        if org_id in self.model_cache:
            return self.model_cache[org_id]

        model_file = MODELS_DIR / f"isolation_forest_org_{org_id}.pkl"
        if model_file.exists():
            try:
                with open(model_file, "rb") as f:
                    data = pickle.load(f)
                    self.model_cache[org_id] = (data["model"], data["scaler"])
                    return self.model_cache[org_id]
            except Exception as e:
                logger.error(f"Failed to load cached model {model_file}: {e}")
        return None

    def evaluate_live_metric(self, db: Session, server: Server, metric: Metric) -> Optional[AnomalyLog]:
        """
        Evaluates a single incoming metric snapshot against the trained ML model.
        Returns an AnomalyLog if an anomaly is detected.
        """
        model_pack = self._load_model(server.organization_id)
        if not model_pack:
            return None

        model, scaler = model_pack
        net_throughput = (metric.net_upload_speed or 0.0) + (metric.net_download_speed or 0.0)

        # Fetch previous metric for trend calculation
        prev_metric = db.query(Metric).filter(
            Metric.server_id == server.id,
            Metric.id != metric.id
        ).order_by(Metric.timestamp.desc()).first()

        cpu_trend = (metric.cpu_percent - prev_metric.cpu_percent) if prev_metric else 0.0
        ram_trend = (metric.ram_percent - prev_metric.ram_percent) if prev_metric else 0.0

        features = np.array([[
            float(metric.cpu_percent),
            float(metric.ram_percent),
            float(metric.disk_percent),
            float(net_throughput),
            float(cpu_trend),
            float(ram_trend)
        ]])

        try:
            X_scaled = scaler.transform(features)
            pred = model.predict(X_scaled)[0]  # -1 for anomaly, 1 for inlier
            # score_samples returns the opposite of anomaly score (lower is more anomalous)
            raw_score = model.score_samples(X_scaled)[0]
            normalized_score = round(float(1.0 - (raw_score + 0.5)), 3)

            if pred == -1:
                # Determine explanation
                reasons = []
                if metric.cpu_percent > 75:
                    reasons.append(f"Abnormal CPU surge ({metric.cpu_percent:.1f}%)")
                if metric.ram_percent > 85:
                    reasons.append(f"Memory saturation ({metric.ram_percent:.1f}%)")
                if net_throughput > 1_000_000:
                    reasons.append(f"Network throughput spike ({net_throughput / 1_000_000:.2f} MB/s)")
                if abs(cpu_trend) > 25:
                    reasons.append(f"Rapid CPU acceleration ({cpu_trend:+.1f}%)")

                explanation = "; ".join(reasons) if reasons else "Multi-dimensional deviation from baseline operational profile."

                log = AnomalyLog(
                    server_id=server.id,
                    organization_id=server.organization_id,
                    timestamp=metric.timestamp,
                    anomaly_score=normalized_score,
                    is_anomaly=True,
                    cpu_val=metric.cpu_percent,
                    ram_val=metric.ram_percent,
                    disk_val=metric.disk_percent,
                    net_val=net_throughput,
                    explanation=explanation,
                    model_version="1.0.0"
                )
                db.add(log)
                db.commit()
                logger.info(f"Detected AI Anomaly on server {server.name}: score={normalized_score}, explanation={explanation}")
                return log
        except Exception as e:
            logger.debug(f"Live anomaly scoring error: {e}")

        return None


ml_service = AnomalyDetectionService()
