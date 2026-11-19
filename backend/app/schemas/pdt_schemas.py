"""Pydantic schemas for Performance Debt Tracker (PDT).
These schemas are used for API request/response validation.
"""

from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel, Field

# ---------------- Performance Metric Ingestion ----------------
class PerformanceMetricIn(BaseModel):
    server_id: str = Field(..., description="ID of the server the metrics belong to")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)
    payload: dict = Field(..., description="Metric payload, e.g., {'cpu': 73.2, 'memory': 61.4, ...}")

class PerformanceMetricOut(BaseModel):
    id: str
    server_id: str
    timestamp: datetime
    payload: dict

    class Config:
        orm_mode = True

# ---------------- Baseline ----------------
class PerformanceBaselineCreate(BaseModel):
    server_id: str
    window_days: int = Field(7, ge=1)
    baseline: dict

class PerformanceBaselineOut(BaseModel):
    id: str
    server_id: str
    window_days: int
    baseline: dict
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# ---------------- Debt ----------------
class PerformanceDebtCreate(BaseModel):
    server_id: str
    category: str = Field(..., pattern=r"^(cpu|memory|disk|network|response)$")
    title: str
    description: str
    debt_score: float = Field(0.0, ge=0.0, le=100.0)
    trend_direction: str = "stable"
    estimated_impact: str = "medium"

class PerformanceDebtUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern=r"^(open|investigating|mitigated|closed|ignored)$")
    resolution_notes: Optional[str] = None
    resolved_by: Optional[str] = None
    debt_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    trend_direction: Optional[str] = None
    estimated_impact: Optional[str] = None

class PerformanceDebtOut(BaseModel):
    id: str
    organization_id: str
    server_id: str
    category: str
    title: str
    description: str
    debt_score: float
    trend_direction: str
    occurrence_count: int
    first_detected_at: datetime
    last_detected_at: datetime
    avg_metric_value: Optional[float]
    peak_metric_value: Optional[float]
    threshold_value: Optional[float]
    estimated_impact: str
    status: str
    resolution_notes: Optional[float]
    resolved_at: Optional[datetime]
    resolved_by: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# ---------------- Issue ----------------
class PerformanceIssueCreate(BaseModel):
    debt_id: str
    server_id: str
    resource_type: str = Field(..., pattern=r"^(cpu|memory|disk|network|response)$")
    description: str
    baseline_value: Optional[float] = None
    current_value: Optional[float] = None
    debt_score: float = Field(0.0, ge=0.0, le=100.0)
    severity: str = "low"

class PerformanceIssueUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern=r"^(open|in_progress|resolved|ignored)$")
    notes: Optional[str] = None

class PerformanceIssueOut(BaseModel):
    id: str
    debt_id: str
    server_id: str
    resource_type: str
    description: str
    baseline_value: Optional[float]
    current_value: Optional[float]
    debt_score: float
    severity: str
    first_detected: datetime
    last_detected: datetime
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# ---------------- Recommendation ----------------
class RecommendationOut(BaseModel):
    issue_id: str
    recommendation: str
    confidence: Optional[float] = None

    class Config:
        orm_mode = True

# ---------------- Report Generation ----------------
class ReportRequest(BaseModel):
    format: str = Field(..., pattern=r"^(pdf|csv)$")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    class Config:
        orm_mode = True
