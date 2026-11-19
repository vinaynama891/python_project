"""Backend metric helper services.

This module provides utility functions for retrieving metric data from the database.
It is deliberately lightweight – only the functions needed for the ML Anomaly
Detection pipeline are included.
"""

from datetime import datetime, timedelta
from typing import List

from sqlalchemy.orm import Session

from backend.app.models.models import Metric


def get_recent_metrics(db: Session, server_id: str, minutes: int = 60) -> List[Metric]:
    """Return all Metric records for ``server_id`` newer than ``minutes`` ago.

    Parameters
    ----------
    db: Session
        Active SQLAlchemy session.
    server_id: str
        UUID of the server whose metrics are requested.
    minutes: int, optional
        Age window in minutes (default 60). Use larger values for training data.

    Returns
    -------
    List[Metric]
        List of Metric ORM objects ordered by timestamp descending.
    """
    cutoff: datetime = datetime.utcnow() - timedelta(minutes=minutes)
    return (
        db.query(Metric)
        .filter(Metric.server_id == server_id, Metric.timestamp >= cutoff)
        .order_by(Metric.timestamp.desc())
        .all()
    )
