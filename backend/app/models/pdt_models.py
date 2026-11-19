"""Performance Debt Tracker (PDT) SQLAlchemy models.
This file defines the database tables used by the PDT module. It follows the
existing project's conventions: Base is imported from the shared declarative
base, helper functions like `generate_uuid` are reused, and relationships are
mirrored with back_populates.
"""

from datetime import datetime, timezone
from typing import List

from sqlalchemy import (
    Column,
    String,
    Text,
    Float,
    Integer,
    DateTime,
    ForeignKey,
    Index,
    Boolean,
    JSON,
)
from sqlalchemy.orm import relationship

from ..database.session import Base
from ..utils import generate_uuid  # helper to create UUID strings

# ---------------------------------------------------------------------------
# Performance Metrics – raw time‑series data collected by the agent.
# ---------------------------------------------------------------------------
class PerformanceMetric(Base):
    __tablename__ = "performance_metrics"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    server_id = Column(String(36), ForeignKey("servers.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    # Metric payload stored as JSON for flexibility (e.g., {'cpu': 73.2, 'mem': 61.4, ...})
    payload = Column(JSON, nullable=False)

    server = relationship("Server", back_populates="performance_metrics")

    __table_args__ = (
        Index("idx_metric_server_timestamp", "server_id", "timestamp"),
    )

# ---------------------------------------------------------------------------
# Baselines – aggregated typical values for a server.
# ---------------------------------------------------------------------------
class PerformanceBaseline(Base):
    __tablename__ = "performance_baselines"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    server_id = Column(String(36), ForeignKey("servers.id", ondelete="CASCADE"), nullable=False, index=True)
    # Window expressed in days (e.g., 7 for a weekly baseline)
    window_days = Column(Integer, nullable=False, default=7)
    # Baseline values stored as JSON, same shape as metric payload
    baseline = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    server = relationship("Server", back_populates="performance_baselines")

# ---------------------------------------------------------------------------
# Performance Debt – aggregated score for a period of inefficiency.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Performance Debt – aggregated score for a period of inefficiency.
# ---------------------------------------------------------------------------
class PerformanceDebt(Base):
    __tablename__ = "performance_debts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    server_id = Column(String(36), ForeignKey("servers.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)  # cpu, memory, disk, network, response
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    debt_score = Column(Float, default=0.0)  # 0‑100 severity score
    trend_direction = Column(String(20), default="stable")  # improving, stable, degrading
    occurrence_count = Column(Integer, default=1)
    first_detected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_detected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    avg_metric_value = Column(Float, nullable=True)
    peak_metric_value = Column(Float, nullable=True)
    threshold_value = Column(Float, nullable=True)
    estimated_impact = Column(String(50), default="medium")  # low, medium, high, critical
    status = Column(String(20), default="open", index=True)  # open, investigating, mitigated, closed, ignored
    resolution_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    organization = relationship("Organization", back_populates="performance_debts")
    server = relationship("Server", back_populates="performance_debts")

    __table_args__ = (
        Index("idx_perf_debt_org_status", "organization_id", "status"),
        Index("idx_perf_debt_server_category", "server_id", "category"),
    )

# ---------------------------------------------------------------------------
# Performance Issue – a concrete instance of a debt that can be tracked.
# ---------------------------------------------------------------------------
class PerformanceIssue(Base):
    __tablename__ = "performance_issues"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    debt_id = Column(String(36), ForeignKey("performance_debts.id", ondelete="CASCADE"), nullable=False, index=True)
    server_id = Column(String(36), ForeignKey("servers.id", ondelete="CASCADE"), nullable=False)
    resource_type = Column(String(20), nullable=False)  # cpu, memory, disk, network, response
    description = Column(Text, nullable=False)
    baseline_value = Column(Float, nullable=True)
    current_value = Column(Float, nullable=True)
    debt_score = Column(Float, default=0.0)
    severity = Column(String(20), default="low")  # low, medium, high, critical
    first_detected = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_detected = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(String(20), default="open", index=True)  # open, in_progress, resolved, ignored
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    debt = relationship("PerformanceDebt", back_populates="issues")
    server = relationship("Server", back_populates="performance_issues")
    history = relationship("IssueHistory", back_populates="issue", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_issue_server_status", "server_id", "status"),
    )

# ---------------------------------------------------------------------------
# Issue History – audit trail of status changes and notes.
# ---------------------------------------------------------------------------
class IssueHistory(Base):
    __tablename__ = "issue_history"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    issue_id = Column(String(36), ForeignKey("performance_issues.id", ondelete="CASCADE"), nullable=False, index=True)
    changed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    old_status = Column(String(20), nullable=False)
    new_status = Column(String(20), nullable=False)
    notes = Column(Text, nullable=True)

    issue = relationship("PerformanceIssue", back_populates="history")

# ---------------------------------------------------------------------------
# Monitoring Configuration – weights, thresholds, and retention settings.
# ---------------------------------------------------------------------------
class MonitoringConfig(Base):
    __tablename__ = "monitoring_config"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    # JSON dict of metric weights, e.g., {"cpu": 1.2, "memory": 1.0, ...}
    metric_weights = Column(JSON, nullable=False, default={"cpu": 1.0, "memory": 1.0, "disk": 1.0, "network": 1.0, "response": 1.0})
    # Baseline window in days per resource type
    baseline_window_days = Column(Integer, nullable=False, default=7)
    # Retention policy in days for raw metrics
    metric_retention_days = Column(Integer, nullable=False, default=30)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

# ---------------------------------------------------------------------------
# ML Model Metadata – tracks training timestamps, versions, and evaluation.
# ---------------------------------------------------------------------------
class MLModelMeta(Base):
    __tablename__ = "ml_model_meta"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    model_type = Column(String(30), nullable=False)  # isolation_forest, random_forest, kmeans
    version = Column(String(20), nullable=False)
    trained_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    parameters = Column(JSON, nullable=True)
    metrics = Column(JSON, nullable=True)  # e.g., {"roc_auc": 0.92}
    active = Column(Boolean, default=True)

# ---------------------------------------------------------------------------
# Relationship back‑references – extend existing Server and Organization models.
# Assuming `Server` and `Organization` are defined in other modules.
# ---------------------------------------------------------------------------
# The imports are placed here to avoid circular imports at runtime.
from .models import Server, Organization  # type: ignore

Server.performance_metrics = relationship("PerformanceMetric", back_populates="server", cascade="all, delete-orphan")
Server.performance_baselines = relationship("PerformanceBaseline", back_populates="server", cascade="all, delete-orphan")
Server.performance_debts = relationship("PerformanceDebt", back_populates="server", cascade="all, delete-orphan")
Server.performance_issues = relationship("PerformanceIssue", back_populates="server", cascade="all, delete-orphan")

Organization.performance_debts = relationship("PerformanceDebt", back_populates="organization", cascade="all, delete-orphan")

PerformanceDebt.issues = relationship("PerformanceIssue", back_populates="debt", cascade="all, delete-orphan")
