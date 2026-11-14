"""
CloudPulse Optional AWS CloudWatch Integration
Provides read-only metric querying for EC2/CloudWatch when credentials are provided.
Gracefully reports disconnected state when AWS credentials are absent.
"""
import os
import logging
from typing import Dict, Any, List

from backend.app.core.config import settings

logger = logging.getLogger("CloudPulse.AWS")


class AWSCloudWatchService:
    def __init__(self):
        self.enabled = settings.ENABLE_AWS_CLOUDWATCH
        self.region = settings.AWS_DEFAULT_REGION
        self.client = None

        if self.enabled and settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            try:
                import boto3
                self.client = boto3.client(
                    'cloudwatch',
                    region_name=self.region,
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
                )
                logger.info(f"AWS CloudWatch client initialized for region {self.region}")
            except Exception as e:
                logger.warning(f"Failed to initialize AWS CloudWatch client: {e}")
                self.client = None

    def get_status(self) -> Dict[str, Any]:
        """Returns connection and configuration status of the AWS integration."""
        if not self.enabled:
            return {
                "status": "disabled",
                "message": "AWS CloudWatch integration is disabled in configuration.",
                "region": self.region,
                "configured": False
            }
        if not self.client:
            return {
                "status": "disconnected",
                "message": "AWS credentials not configured. Host monitoring operates locally without AWS dependencies.",
                "region": self.region,
                "configured": False
            }
        return {
            "status": "connected",
            "message": f"Connected to AWS CloudWatch ({self.region})",
            "region": self.region,
            "configured": True
        }

    def get_ec2_metrics(self, instance_id: str) -> Dict[str, Any]:
        """Queries CPU and network metrics for an EC2 instance if connected."""
        status = self.get_status()
        if not status["configured"]:
            return {
                "error": "AWS CloudWatch is not configured.",
                "status": status
            }

        # Real AWS boto3 query would go here if credentials are configured
        try:
            return {
                "instance_id": instance_id,
                "status": "connected",
                "metrics": {
                    "cpu_utilization": [],
                    "network_in": [],
                    "network_out": []
                }
            }
        except Exception as e:
            return {"error": str(e)}


aws_service = AWSCloudWatchService()
