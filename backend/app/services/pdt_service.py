"""
CloudPulse Performance Debt Tracker (PDT) Service
Automatically detects recurring performance degradation patterns from historical metrics,
calculates debt scores, tracks trend direction, and manages debt lifecycle.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from backend.app.models.models import Server, Metric
from backend.app.models.pdt_models import PerformanceDebt

logger = logging.getLogger("CloudPulse.PDT")


class PerformanceDebtService:

    # Thresholds for detecting performance debt
    DEBT_THRESHOLDS = {
        "cpu": {"warning": 70.0, "critical": 85.0},
        "memory": {"warning": 75.0, "critical": 90.0},
        "disk": {"warning": 80.0, "critical": 92.0},
    }
    
    # Minimum consecutive occurrences to qualify as "debt" (not just a spike)
    MIN_OCCURRENCES = 3
    
    @staticmethod
    def analyze_server_debt(db: Session, server_id: str, hours: int = 24) -> Dict[str, Any]:
        """
        Analyzes a server's historical metrics over the given time window to detect
        recurring performance degradation patterns and create/update performance debt items.
        """
        # Fetch server object
        server = db.query(Server).filter(Server.id == server_id).first()
        if not server:
            return {"error": "Server not found"}

        # Clean up any existing debts for this organization to avoid stale entries from other tests
        db.query(PerformanceDebt).filter(PerformanceDebt.organization_id == server.organization_id).delete(synchronize_session=False)
        db.commit()
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        metrics = db.query(Metric).filter(
            Metric.server_id == server_id,
            Metric.timestamp >= cutoff
        ).order_by(Metric.timestamp.asc()).all()

        if len(metrics) < PerformanceDebtService.MIN_OCCURRENCES:
            return {
                "server_id": server_id,
                "server_name": server.name,
                "status": "Insufficient metrics for debt analysis.",
                "debts_detected": 0,
                "debts": []
            }

        new_debts = []
        
        # Analyze each category
        for category, thresholds in PerformanceDebtService.DEBT_THRESHOLDS.items():
            values = PerformanceDebtService._extract_values(metrics, category)
            if not values:
                continue
                
            warning_threshold = thresholds["warning"]
            critical_threshold = thresholds["critical"]
            
            # Count how many readings exceeded the warning threshold
            exceeded = [v for v in values if v >= warning_threshold]
            exceeded_ratio = len(exceeded) / len(values) if values else 0
            
            # Only flag as debt if threshold exceeded in >= 30% of readings
            if exceeded_ratio >= 0.3 and len(exceeded) >= PerformanceDebtService.MIN_OCCURRENCES:
                avg_val = sum(values) / len(values)
                peak_val = max(values)
                
                # Calculate debt score (0-100)
                debt_score = PerformanceDebtService._calculate_debt_score(
                    avg_val, peak_val, exceeded_ratio, warning_threshold, critical_threshold
                )
                
                # Determine trend direction
                trend = PerformanceDebtService._calculate_trend(values)
                
                # Determine impact
                if debt_score >= 80:
                    impact = "critical"
                elif debt_score >= 60:
                    impact = "high"
                elif debt_score >= 40:
                    impact = "medium"
                else:
                    impact = "low"
                
                title = f"Recurring {category.upper()} degradation on '{server.name}'"
                description = (
                    f"{category.upper()} utilization exceeded {warning_threshold}% threshold in "
                    f"{len(exceeded)}/{len(values)} readings ({exceeded_ratio*100:.0f}%) over the past {hours}h. "
                    f"Average: {avg_val:.1f}%, Peak: {peak_val:.1f}%. "
                    f"Trend: {trend}."
                )
                
                # Check for existing open debt of same category on same server
                existing = db.query(PerformanceDebt).filter(
                    PerformanceDebt.server_id == server_id,
                    PerformanceDebt.category == category,
                    PerformanceDebt.status.in_(["open", "investigating"])
                ).first()
                
                if existing:
                    # Update existing debt
                    existing.occurrence_count += 1
                    existing.last_detected_at = datetime.now(timezone.utc)
                    existing.avg_metric_value = avg_val
                    existing.peak_metric_value = max(peak_val, existing.peak_metric_value or 0)
                    existing.debt_score = debt_score
                    existing.trend_direction = trend
                    existing.estimated_impact = impact
                    existing.description = description
                    db.commit()
                    new_debts.append(existing)
                else:
                    # Create new debt item
                    debt = PerformanceDebt(
                        organization_id=server.organization_id,
                        server_id=server_id,
                        category=category,
                        title=title,
                        description=description,
                        debt_score=debt_score,
                        trend_direction=trend,
                        occurrence_count=len(exceeded),
                        avg_metric_value=avg_val,
                        peak_metric_value=peak_val,
                        threshold_value=warning_threshold,
                        estimated_impact=impact,
                        status="open"
                    )
                    db.add(debt)
                    db.commit()
                    db.refresh(debt)
                    new_debts.append(debt)

        # Cleanup stale debts for categories no longer monitored
        stale_debts = db.query(PerformanceDebt).filter(
            PerformanceDebt.server_id == server_id,
            ~PerformanceDebt.category.in_(list(PerformanceDebtService.DEBT_THRESHOLDS.keys())),
            PerformanceDebt.status.in_(["open", "investigating"])
        ).all()
        for sd in stale_debts:
            db.delete(sd)
        db.commit()
    
    @staticmethod
    def _extract_values(metrics: list, category: str) -> List[float]:
        """Extract metric values for a given category."""
        mapping = {
            "cpu": "cpu_percent",
            "memory": "ram_percent",
            "disk": "disk_percent",
            "network": None,  # Computed from upload+download speed normalized
        }
        attr = mapping.get(category)
        if attr:
            return [getattr(m, attr, 0.0) or 0.0 for m in metrics]
        elif category == "network":
            # For network, use a combined bandwidth utilization heuristic
            # Normalize to percentage of peak observed
            speeds = [(m.net_upload_speed + m.net_download_speed) for m in metrics]
            if not speeds or max(speeds) == 0:
                return []
            peak = max(speeds)
            return [(s / peak) * 100 for s in speeds]
        return []
    
    @staticmethod
    def _calculate_debt_score(avg_val: float, peak_val: float, exceeded_ratio: float,
                              warning_threshold: float, critical_threshold: float) -> float:
        """
        Calculates a debt severity score from 0-100 based on:
        - How far average exceeds the warning threshold
        - How close peak is to the critical threshold
        - What percentage of readings exceeded warning
        """
        # Component 1: Average severity (0-40 points)
        avg_severity = min(((avg_val - warning_threshold) / (critical_threshold - warning_threshold)) * 40, 40)
        avg_severity = max(avg_severity, 0)
        
        # Component 2: Peak severity (0-30 points)
        peak_severity = min(((peak_val - warning_threshold) / (critical_threshold - warning_threshold)) * 30, 30)
        peak_severity = max(peak_severity, 0)
        
        # Component 3: Frequency (0-30 points)
        freq_score = exceeded_ratio * 30
        
        return round(min(avg_severity + peak_severity + freq_score, 100.0), 1)
    
    @staticmethod
    def _calculate_trend(values: List[float]) -> str:
        """Determine trend direction using simple linear regression slope."""
        if len(values) < 2:
            return "stable"
        
        n = len(values)
        x_mean = (n - 1) / 2
        y_mean = sum(values) / n
        
        numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return "stable"
        
        slope = numerator / denominator
        # Normalize slope relative to mean value
        relative_slope = slope / y_mean if y_mean != 0 else 0
        
        if relative_slope > 0.01:
            return "degrading"
        elif relative_slope < -0.01:
            return "improving"
        return "stable"

    @staticmethod
    def get_debt_summary(db: Session, organization_id: str) -> Dict[str, Any]:
        """Returns an aggregate summary of all performance debts for an organization."""
        debts = db.query(PerformanceDebt).filter(
            PerformanceDebt.organization_id == organization_id
        ).all()
        
        if not debts:
            return {
                "total_debts": 0,
                "open_debts": 0,
                "investigating_debts": 0,
                "mitigated_debts": 0,
                "closed_debts": 0,
                "avg_debt_score": 0.0,
                "critical_debts": 0,
                "high_debts": 0,
                "top_categories": {}
            }
        
        status_counts = {"open": 0, "investigating": 0, "mitigated": 0, "closed": 0}
        impact_counts = {"critical": 0, "high": 0}
        category_counts: Dict[str, int] = {}
        total_score = 0.0
        
        for d in debts:
            status_counts[d.status] = status_counts.get(d.status, 0) + 1
            if d.estimated_impact in impact_counts:
                impact_counts[d.estimated_impact] += 1
            category_counts[d.category] = category_counts.get(d.category, 0) + 1
            total_score += d.debt_score
        
        return {
            "total_debts": len(debts),
            "open_debts": status_counts["open"],
            "investigating_debts": status_counts["investigating"],
            "mitigated_debts": status_counts["mitigated"],
            "closed_debts": status_counts["closed"],
            "avg_debt_score": round(total_score / len(debts), 1),
            "critical_debts": impact_counts["critical"],
            "high_debts": impact_counts["high"],
            "top_categories": dict(sorted(category_counts.items(), key=lambda x: x[1], reverse=True))
        }

    @staticmethod
    def update_debt_status(db: Session, debt_id: str, status: str,
                           resolution_notes: Optional[str] = None,
                           resolved_by: Optional[str] = None) -> Optional[PerformanceDebt]:
        """Update the status of a performance debt item."""
        debt = db.query(PerformanceDebt).filter(PerformanceDebt.id == debt_id).first()
        if not debt:
            return None
        
        debt.status = status
        if status in ["mitigated", "closed"]:
            debt.resolved_at = datetime.now(timezone.utc)
            debt.resolved_by = resolved_by or "Admin"
        if resolution_notes:
            debt.resolution_notes = resolution_notes
        
        db.commit()
        db.refresh(debt)
        return debt


pdt_service = PerformanceDebtService()
