"""
CloudPulse Database Models (SQLAlchemy)
Implements all 12 core tables with multi-tenant isolation, relational constraints and indexing.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime,
    ForeignKey, Text, JSON, Index
)
from sqlalchemy.orm import relationship

from backend.app.database.session import Base


def generate_uuid() -> str:
    return uuid.uuid4().hex


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    role = Column(String(50), default="member")  # admin, member, viewer
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    memberships = relationship("OrganizationMember", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    members = relationship("OrganizationMember", back_populates="organization", cascade="all, delete-orphan")
    servers = relationship("Server", back_populates="organization", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="organization", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="organization", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="organization", cascade="all, delete-orphan")
    models = relationship("ModelMetadata", back_populates="organization", cascade="all, delete-orphan")


class OrganizationMember(Base):
    __tablename__ = "organization_members"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), default="member")  # owner, admin, member
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="memberships")
    organization = relationship("Organization", back_populates="members")


class Server(Base):
    __tablename__ = "servers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    hostname = Column(String(255), nullable=True)
    os = Column(String(100), nullable=True)
    os_version = Column(String(100), nullable=True)
    architecture = Column(String(50), nullable=True)
    ip_address = Column(String(100), nullable=True)
    status = Column(String(50), default="offline", index=True)  # online, offline, warning, critical
    last_heartbeat = Column(DateTime, nullable=True, index=True)
    registration_token = Column(String(255), unique=True, nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    organization = relationship("Organization", back_populates="servers")
    credentials = relationship("AgentCredential", back_populates="server", uselist=False, cascade="all, delete-orphan")
    metrics = relationship("Metric", back_populates="server", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="server", cascade="all, delete-orphan")
    anomalies = relationship("AnomalyLog", back_populates="server", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="server", cascade="all, delete-orphan")


class AgentCredential(Base):
    __tablename__ = "agent_credentials"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    server_id = Column(String(36), ForeignKey("servers.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    agent_token_hash = Column(String(255), nullable=False)
    is_revoked = Column(Boolean, default=False)
    last_used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    server = relationship("Server", back_populates="credentials")


class Metric(Base):
    __tablename__ = "metrics"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    server_id = Column(String(36), ForeignKey("servers.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # CPU
    cpu_percent = Column(Float, nullable=False)
    cpu_per_core = Column(JSON, nullable=True)
    cpu_frequency_current = Column(Float, nullable=True)
    cpu_cores = Column(Integer, nullable=True)
    cpu_temperature = Column(Float, nullable=True)

    # Memory
    ram_total = Column(Float, nullable=False)
    ram_used = Column(Float, nullable=False)
    ram_available = Column(Float, nullable=False)
    ram_percent = Column(Float, nullable=False)
    swap_percent = Column(Float, nullable=True)

    # Disk
    disk_total = Column(Float, nullable=False)
    disk_used = Column(Float, nullable=False)
    disk_free = Column(Float, nullable=False)
    disk_percent = Column(Float, nullable=False)
    disk_read_speed = Column(Float, default=0.0)
    disk_write_speed = Column(Float, default=0.0)
    disk_io_ops = Column(Integer, default=0)

    # Network
    net_bytes_sent = Column(Float, default=0.0)
    net_bytes_recv = Column(Float, default=0.0)
    net_upload_speed = Column(Float, default=0.0)
    net_download_speed = Column(Float, default=0.0)
    net_packets_sent = Column(Integer, default=0)
    net_packets_recv = Column(Integer, default=0)

    # Raw details
    raw_details = Column(JSON, nullable=True)

    server = relationship("Server", back_populates="metrics")
    processes = relationship("ProcessMetric", back_populates="metric", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_metric_server_time", "server_id", "timestamp"),
    )


class ProcessMetric(Base):
    __tablename__ = "process_metrics"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    metric_id = Column(String(36), ForeignKey("metrics.id", ondelete="CASCADE"), nullable=False, index=True)
    server_id = Column(String(36), ForeignKey("servers.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    pid = Column(Integer, nullable=False)
    name = Column(String(255), nullable=False)
    username = Column(String(255), nullable=True)
    status = Column(String(50), nullable=True)
    cpu_percent = Column(Float, default=0.0)
    memory_percent = Column(Float, default=0.0)
    memory_bytes = Column(Float, default=0.0)

    metric = relationship("Metric", back_populates="processes")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    server_id = Column(String(36), ForeignKey("servers.id", ondelete="CASCADE"), nullable=False, index=True)
    metric_type = Column(String(50), nullable=False, index=True)  # cpu, ram, disk, network, heartbeat, ai_anomaly
    severity = Column(String(20), nullable=False, index=True)      # warning, critical
    message = Column(Text, nullable=False)
    value = Column(Float, nullable=True)
    threshold = Column(Float, nullable=True)
    status = Column(String(20), default="active", index=True)      # active, acknowledged, resolved
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String(255), nullable=True)
    resolved_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    organization = relationship("Organization", back_populates="alerts")
    server = relationship("Server", back_populates="alerts")

    __table_args__ = (
        Index("idx_alert_org_status", "organization_id", "status"),
    )


class AnomalyLog(Base):
    __tablename__ = "anomaly_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    server_id = Column(String(36), ForeignKey("servers.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    anomaly_score = Column(Float, nullable=False)
    is_anomaly = Column(Boolean, default=True)
    cpu_val = Column(Float, nullable=True)
    ram_val = Column(Float, nullable=True)
    disk_val = Column(Float, nullable=True)
    net_val = Column(Float, nullable=True)
    explanation = Column(Text, nullable=True)
    model_version = Column(String(50), default="1.0.0")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    server = relationship("Server", back_populates="anomalies")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    server_id = Column(String(36), ForeignKey("servers.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(50), nullable=False)  # CPU, Memory, Disk, Network, Process
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    impact = Column(String(50), default="medium")  # low, medium, high
    suggested_action = Column(Text, nullable=True)
    is_applied = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    server = relationship("Server", back_populates="recommendations")
    organization = relationship("Organization", back_populates="recommendations")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(String(255), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    user = relationship("User", back_populates="audit_logs")
    organization = relationship("Organization", back_populates="audit_logs")


class ModelMetadata(Base):
    __tablename__ = "model_metadata"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    model_name = Column(String(100), default="IsolationForestAnomalyDetector")
    version = Column(String(50), default="1.0.0")
    algorithm = Column(String(100), default="Isolation Forest (Scikit-learn)")
    training_samples = Column(Integer, default=0)
    metrics_summary = Column(JSON, nullable=True)
    file_path = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    organization = relationship("Organization", back_populates="models")
