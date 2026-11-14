"""
CloudPulse Performance Tuning Profiler
Analyzes bottlenecks, profiles Python runtime execution with cProfile & time.perf_counter,
and generates non-destructive optimization recommendations.
"""
import io
import time
import cProfile
import pstats
import logging
from functools import wraps
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.app.models.models import Server, Metric, ProcessMetric, Recommendation

logger = logging.getLogger("CloudPulse.Profiler")


def profile_execution(threshold_ms: float = 50.0):
    """
    Advanced Python Decorator demonstrating execution-time measurement
    using time.perf_counter and detailed function profiling using cProfile.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            profiler = cProfile.Profile()
            profiler.enable()
            start_t = time.perf_counter()

            result = func(*args, **kwargs)

            elapsed_ms = (time.perf_counter() - start_t) * 1000
            profiler.disable()

            if elapsed_ms > threshold_ms:
                s = io.StringIO()
                ps = pstats.Stats(profiler, stream=s).sort_stats(pstats.SortKey.CUMULATIVE)
                ps.print_stats(10)
                logger.warning(
                    f"[Slow Function Detected] {func.__name__} took {elapsed_ms:.2f}ms (threshold: {threshold_ms}ms)\n"
                    f"{s.getvalue()}"
                )
            return result
        return wrapper
    return decorator


class PerformanceProfilerService:
    @staticmethod
    def analyze_server(db: Session, server_id: str) -> Dict[str, Any]:
        """
        Conducts deep performance inspection on a server's recent metrics and top processes,
        emitting actionable optimization recommendations.
        """
        server = db.query(Server).filter(Server.id == server_id).first()
        if not server:
            return {"error": "Server not found"}

        latest_metric = db.query(Metric).filter(
            Metric.server_id == server_id
        ).order_by(Metric.timestamp.desc()).first()

        if not latest_metric:
            return {
                "server_id": server_id,
                "server_name": server.name,
                "status": "No metrics available yet for profiling.",
                "recommendations": []
            }

        # Query top CPU and memory consuming processes for this metric
        top_processes = db.query(ProcessMetric).filter(
            ProcessMetric.server_id == server_id,
            ProcessMetric.metric_id == latest_metric.id
        ).all()

        recommendations_to_add = []
        bottlenecks = []

        # 1. CPU Bottleneck Inspection
        if latest_metric.cpu_percent >= 80.0:
            bottlenecks.append({
                "component": "CPU",
                "severity": "Critical" if latest_metric.cpu_percent >= 90 else "Warning",
                "description": f"Aggregate CPU load is high at {latest_metric.cpu_percent:.1f}%."
            })

            # Check if a single process dominates CPU
            high_cpu_procs = [p for p in top_processes if p.cpu_percent >= 25.0]
            for p in high_cpu_procs:
                rec_title = f"High CPU utilization in '{p.name}' (PID: {p.pid})"
                rec_desc = f"Process '{p.name}' (PID {p.pid}) consumed {p.cpu_percent:.1f}% CPU. Investigate its workload, thread contention, or computational complexity."
                action = f"Inspect process logs, verify execution thread count, and optimize loop algorithms for '{p.name}'."
                recommendations_to_add.append(("CPU", rec_title, rec_desc, "high", action))

        # 2. Memory Bottleneck Inspection
        if latest_metric.ram_percent >= 85.0:
            bottlenecks.append({
                "component": "RAM",
                "severity": "Critical" if latest_metric.ram_percent >= 95 else "Warning",
                "description": f"RAM utilization reached {latest_metric.ram_percent:.1f}% ({latest_metric.ram_used / 1e9:.2f} GB used / {latest_metric.ram_total / 1e9:.2f} GB total)."
            })

            high_mem_procs = [p for p in top_processes if p.memory_percent >= 10.0]
            for p in high_mem_procs:
                rec_title = f"Elevated Memory Allocation in '{p.name}'"
                rec_desc = f"Process '{p.name}' (PID {p.pid}) is consuming {p.memory_percent:.1f}% of total physical RAM ({p.memory_bytes / 1e6:.1f} MB)."
                action = f"Check '{p.name}' for memory leaks, unclosed database connections, or large unindexed object caches."
                recommendations_to_add.append(("Memory", rec_title, rec_desc, "high", action))

        # 3. Disk Utilization Bottleneck
        if latest_metric.disk_percent >= 85.0:
            bottlenecks.append({
                "component": "Disk",
                "severity": "Critical" if latest_metric.disk_percent >= 95 else "Warning",
                "description": f"Primary disk space is {latest_metric.disk_percent:.1f}% full (Free: {latest_metric.disk_free / 1e9:.2f} GB)."
            })
            rec_title = "Disk Storage Exhaustion Risk"
            rec_desc = f"Storage volume on server '{server.name}' is approaching capacity at {latest_metric.disk_percent:.1f}%."
            action = "Purge archived system logs, compress inactive metric tables, or expand virtual disk volume capacity."
            recommendations_to_add.append(("Disk", rec_title, rec_desc, "medium", action))

        # 4. Save recommendations to database without duplication
        created_records = []
        for cat, title, desc, impact, action in recommendations_to_add:
            existing = db.query(Recommendation).filter(
                Recommendation.server_id == server_id,
                Recommendation.title == title,
                Recommendation.is_applied == False
            ).first()
            if not existing:
                rec = Recommendation(
                    server_id=server_id,
                    organization_id=server.organization_id,
                    category=cat,
                    title=title,
                    description=desc,
                    impact=impact,
                    suggested_action=action,
                    is_applied=False
                )
                db.add(rec)
                created_records.append(rec)

        if created_records:
            db.commit()

        # Query all active recommendations for this server
        active_recs = db.query(Recommendation).filter(
            Recommendation.server_id == server_id,
            Recommendation.is_applied == False
        ).order_by(Recommendation.created_at.desc()).all()

        return {
            "server_id": server_id,
            "server_name": server.name,
            "cpu_percent": latest_metric.cpu_percent,
            "ram_percent": latest_metric.ram_percent,
            "disk_percent": latest_metric.disk_percent,
            "bottlenecks": bottlenecks,
            "recommendations": [
                {
                    "id": r.id,
                    "category": r.category,
                    "title": r.title,
                    "description": r.description,
                    "impact": r.impact,
                    "suggested_action": r.suggested_action,
                    "created_at": r.created_at
                }
                for r in active_recs
            ]
        }


profiler_service = PerformanceProfilerService()
