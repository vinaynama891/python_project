"""
CloudPulse Pydantic Schemas for Request & Response Serialization
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field


# ---------------- Auth & User ----------------
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    organization_name: Optional[str] = "Default Organization"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(UserBase):
    id: str
    is_active: bool
    is_superuser: bool
    role: str
    organization_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    org_id: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[int] = None
    type: Optional[str] = None


# ---------------- Organization ----------------
class OrgBase(BaseModel):
    name: str
    description: Optional[str] = None


class OrgCreate(OrgBase):
    pass


class OrgOut(OrgBase):
    id: str
    slug: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------- Server ----------------
class ServerBase(BaseModel):
    name: str
    description: Optional[str] = None


class ServerCreate(ServerBase):
    pass


class ServerUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ServerOut(ServerBase):
    id: str
    organization_id: str
    hostname: Optional[str] = None
    os: Optional[str] = None
    os_version: Optional[str] = None
    architecture: Optional[str] = None
    ip_address: Optional[str] = None
    status: str
    last_heartbeat: Optional[datetime] = None
    registration_token: Optional[str] = None
    is_active: bool
    created_at: datetime
    # Latest telemetry preview
    latest_cpu: Optional[float] = None
    latest_ram: Optional[float] = None
    latest_disk: Optional[float] = None

    class Config:
        from_attributes = True


class ServerRegisterToken(BaseModel):
    server_id: str
    registration_token: str
    registration_command_windows: str
    registration_command_linux: str


# ---------------- Agent ----------------
class AgentRegisterRequest(BaseModel):
    registration_token: str
    server_name: Optional[str] = None
    hostname: str
    os: str
    os_version: str
    architecture: str
    ip_address: str


class AgentRegisterResponse(BaseModel):
    server_id: str
    agent_token: str
    message: str


class AgentHeartbeatRequest(BaseModel):
    server_id: str
    agent_version: str = "1.0.0"
    health_status: str = "healthy"


class ProcessItem(BaseModel):
    pid: int
    name: str
    username: Optional[str] = "N/A"
    status: Optional[str] = "running"
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_bytes: float = 0.0


class SystemInfoPayload(BaseModel):
    hostname: str
    ip_address: str
    os: str
    os_version: str
    architecture: str
    cpu_cores_physical: int
    cpu_cores_logical: int
    boot_time: str
    uptime_seconds: float
    agent_version: str
    agent_health: str


class CpuPayload(BaseModel):
    cpu_percent: float
    cpu_per_core: List[float]
    cpu_frequency: Dict[str, Any]
    cpu_cores_logical: int
    cpu_cores_physical: int
    cpu_temperature: Optional[float] = None


class MemoryPayload(BaseModel):
    ram_total: float
    ram_used: float
    ram_available: float
    ram_percent: float
    swap_total: Optional[float] = 0.0
    swap_used: Optional[float] = 0.0
    swap_free: Optional[float] = 0.0
    swap_percent: Optional[float] = 0.0


class DiskPayload(BaseModel):
    disk_total: float
    disk_used: float
    disk_free: float
    disk_percent: float
    disk_read_bytes: Optional[int] = 0
    disk_write_bytes: Optional[int] = 0
    disk_io_operations: Optional[int] = 0
    disk_read_speed_bytes_sec: Optional[float] = 0.0
    disk_write_speed_bytes_sec: Optional[float] = 0.0


class NetworkPayload(BaseModel):
    bytes_sent: float
    bytes_recv: float
    upload_speed_bytes_sec: float
    download_speed_bytes_sec: float
    packets_sent: int
    packets_recv: int
    interfaces: Optional[List[Dict[str, Any]]] = []


class ProcessesPayload(BaseModel):
    top_cpu: List[ProcessItem]
    top_memory: List[ProcessItem]


class AgentMetricPayload(BaseModel):
    server_id: Optional[str] = None
    timestamp: str
    system: SystemInfoPayload
    cpu: CpuPayload
    memory: MemoryPayload
    disk: DiskPayload
    network: NetworkPayload
    processes: ProcessesPayload


# ---------------- Metrics Out ----------------
class MetricOut(BaseModel):
    id: str
    server_id: str
    timestamp: datetime
    cpu_percent: float
    cpu_per_core: Optional[List[float]] = None
    cpu_frequency_current: Optional[float] = None
    ram_total: float
    ram_used: float
    ram_percent: float
    disk_total: float
    disk_used: float
    disk_percent: float
    disk_read_speed: float
    disk_write_speed: float
    net_upload_speed: float
    net_download_speed: float

    class Config:
        from_attributes = True


class MetricHistoryPoint(BaseModel):
    timestamp: datetime
    cpu_percent: float
    ram_percent: float
    disk_percent: float
    net_upload_speed: float
    net_download_speed: float


# ---------------- Alerts ----------------
class AlertOut(BaseModel):
    id: str
    server_id: str
    server_name: Optional[str] = None
    metric_type: str
    severity: str
    message: str
    value: Optional[float] = None
    threshold: Optional[float] = None
    status: str
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_by: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AlertAcknowledge(BaseModel):
    acknowledged_by: Optional[str] = "Admin"


class AlertResolve(BaseModel):
    resolved_by: Optional[str] = "Admin"


# ---------------- AI & Anomaly ----------------
class AnomalyOut(BaseModel):
    id: str
    server_id: str
    server_name: Optional[str] = None
    timestamp: datetime
    anomaly_score: float
    is_anomaly: bool
    cpu_val: Optional[float] = None
    ram_val: Optional[float] = None
    disk_val: Optional[float] = None
    net_val: Optional[float] = None
    explanation: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ModelStatusOut(BaseModel):
    is_trained: bool
    model_name: str
    algorithm: str
    version: str
    training_samples: int
    last_trained: Optional[datetime] = None
    status_message: str


class RecommendationOut(BaseModel):
    id: str
    server_id: str
    server_name: Optional[str] = None
    category: str
    title: str
    description: str
    impact: str
    suggested_action: Optional[str] = None
    is_applied: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------- Overview & Analytics ----------------
class OverviewAnalytics(BaseModel):
    total_servers: int
    online_servers: int
    offline_servers: int
    warning_servers: int
    critical_servers: int
    avg_cpu_percent: float
    avg_ram_percent: float
    avg_disk_percent: float
    total_network_upload_speed: float
    total_network_download_speed: float
    active_alerts_count: int
