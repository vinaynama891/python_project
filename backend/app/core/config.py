"""
CloudPulse Backend Configuration
"""
import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "CloudPulse"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "cloudpulse-enterprise-super-secret-key-change-in-production-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./cloudpulse.db")

    # Server Host & Port
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]

    # Alert Engine Thresholds
    DEFAULT_HEARTBEAT_TIMEOUT_SECONDS: int = 30
    CPU_WARNING_THRESHOLD: float = 80.0
    CPU_CRITICAL_THRESHOLD: float = 90.0
    RAM_WARNING_THRESHOLD: float = 85.0
    RAM_CRITICAL_THRESHOLD: float = 95.0
    DISK_WARNING_THRESHOLD: float = 85.0
    DISK_CRITICAL_THRESHOLD: float = 95.0

    # ML Anomaly Detection
    ML_MIN_TRAINING_SAMPLES: int = 15

    # Optional AWS CloudWatch
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_DEFAULT_REGION: str = "us-east-1"
    ENABLE_AWS_CLOUDWATCH: bool = False

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
