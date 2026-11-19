#!/usr/bin/env python
"""One‑off script to train the IsolationForest anomaly detection model for all
organizations. It can be run manually or invoked from a scheduled job.

Usage:
    python scripts/train_anomaly_model.py
"""

import logging
from pathlib import Path
import sys

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from backend.app.database.session import SessionLocal
from backend.app.models.models import Organization
from backend.app.ml.anomaly_detector import train_model

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

def main():
    db = SessionLocal()
    try:
        orgs = db.query(Organization).all()
        if not orgs:
            logging.info("No organizations found – nothing to train.")
            return
        for org in orgs:
            try:
                result = train_model(db, org.id, contamination=0.05)
                logging.info(f"Trained model for org {org.name} (id={org.id}): {result['status_message']}")
            except Exception as e:
                logging.error(f"Training failed for org {org.id}: {e}")
        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    main()
