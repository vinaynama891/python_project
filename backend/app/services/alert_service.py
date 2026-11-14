"""
CloudPulse Intelligent Alert Engine
Evaluates telemetry against dynamic thresholds, deduplicates continuous alerts, and manages alert state transitions.
"""
import logging
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.models import Alert, Server

logger = logging.getLogger("CloudPulse.AlertEngine")


class AlertEngine:
    @staticmethod
    def evaluate_metrics(db: Session, server: Server, cpu_percent: float, ram_percent: float, disk_percent: float) -> List[Alert]:
        """
        Evaluates incoming metrics against threshold rules.
        Deduplicates alerts: if an active alert for this metric_type already exists on this server,
        it updates its current reading rather than spamming duplicate records.
        """
        generated_alerts: List[Alert] = []
        checks = [
            ("cpu", cpu_percent, settings.CPU_WARNING_THRESHOLD, settings.CPU_CRITICAL_THRESHOLD, "%"),
            ("ram", ram_percent, settings.RAM_WARNING_THRESHOLD, settings.RAM_CRITICAL_THRESHOLD, "%"),
            ("disk", disk_percent, settings.DISK_WARNING_THRESHOLD, settings.DISK_CRITICAL_THRESHOLD, "%")
        ]

        for metric_type, val, warn_th, crit_th, unit in checks:
            severity = None
            threshold = None
            if val >= crit_th:
                severity = "critical"
                threshold = crit_th
            elif val >= warn_th:
                severity = "warning"
                threshold = warn_th

            # Check existing active alert for this server and metric_type
            existing = db.query(Alert).filter(
                Alert.server_id == server.id,
                Alert.metric_type == metric_type,
                Alert.status.in_(["active", "acknowledged"])
            ).first()

            if severity:
                msg = f"{metric_type.upper()} utilization on server '{server.name}' is {val:.1f}{unit} (Exceeds {severity} threshold {threshold:.1f}{unit})"
                if existing:
                    # Update existing alert with latest value to avoid deduplication explosion
                    existing.value = val
                    existing.severity = severity
                    existing.threshold = threshold
                    existing.message = msg
                    db.commit()
                else:
                    # Create new alert
                    new_alert = Alert(
                        organization_id=server.organization_id,
                        server_id=server.id,
                        metric_type=metric_type,
                        severity=severity,
                        message=msg,
                        value=val,
                        threshold=threshold,
                        status="active"
                    )
                    db.add(new_alert)
                    db.commit()
                    db.refresh(new_alert)
                    generated_alerts.append(new_alert)
            else:
                # If metric recovered below warning, auto-resolve active alerts for this metric
                if existing and existing.status == "active":
                    existing.status = "resolved"
                    existing.resolved_at = datetime.now(timezone.utc)
                    existing.resolved_by = "System Auto-Recovery"
                    db.commit()
                    logger.info(f"Auto-resolved {metric_type} alert on server {server.name} as value dropped to {val:.1f}{unit}")

        return generated_alerts

    @staticmethod
    def check_heartbeat_timeouts(db: Session, timeout_seconds: int = 30) -> List[Alert]:
        """
        Scans all servers and marks those with missing heartbeats as offline,
        generating offline alerts if not already generated.
        """
        now = datetime.now(timezone.utc)
        servers = db.query(Server).filter(Server.is_active == True).all()
        offline_alerts = []

        for s in servers:
            if not s.last_heartbeat:
                is_offline = True
            else:
                diff = (now - s.last_heartbeat.replace(tzinfo=timezone.utc if s.last_heartbeat.tzinfo is None else s.last_heartbeat.tzinfo)).total_seconds()
                is_offline = diff > timeout_seconds

            if is_offline and s.status != "offline":
                s.status = "offline"
                # Check existing offline alert
                existing = db.query(Alert).filter(
                    Alert.server_id == s.id,
                    Alert.metric_type == "heartbeat",
                    Alert.status.in_(["active", "acknowledged"])
                ).first()
                if not existing:
                    alert = Alert(
                        organization_id=s.organization_id,
                        server_id=s.id,
                        metric_type="heartbeat",
                        severity="critical",
                        message=f"Server '{s.name}' ({s.hostname or 'unknown'}) is OFFLINE - Heartbeat timed out.",
                        value=0.0,
                        threshold=0.0,
                        status="active"
                    )
                    db.add(alert)
                    offline_alerts.append(alert)

        db.commit()
        return offline_alerts

    @staticmethod
    def acknowledge_alert(db: Session, alert_id: str, acknowledged_by: str = "Admin") -> Optional[Alert]:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if alert and alert.status == "active":
            alert.status = "acknowledged"
            alert.acknowledged_at = datetime.now(timezone.utc)
            alert.acknowledged_by = acknowledged_by
            db.commit()
            db.refresh(alert)
            return alert
        return alert

    @staticmethod
    def resolve_alert(db: Session, alert_id: str, resolved_by: str = "Admin") -> Optional[Alert]:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if alert and alert.status in ["active", "acknowledged"]:
            alert.status = "resolved"
            alert.resolved_at = datetime.now(timezone.utc)
            alert.resolved_by = resolved_by
            db.commit()
            db.refresh(alert)
            return alert
        return alert
