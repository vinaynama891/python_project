#!/usr/bin/env python
"""Periodic AI anomaly detection runner.

This script is intended to be scheduled (via the `/schedule` slash command) to
run every N minutes. It iterates over all *online* servers and triggers the
`detect_anomalies` service for each one, persisting `AnomalyLog` and `Alert`
records.

The script can also be executed manually for ad‑hoc runs:
    python scripts/run_anomaly_detection.py
"""

import logging
from datetime import datetime
from pathlib import Path

# Ensure the project root is on sys.path for imports
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from backend.app.database.session import SessionLocal
from backend.app.models.models import Server, Organization
from backend.app.ml.anomaly_detector import detect_anomalies

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

def run_detection():
    db = SessionLocal()
    try:
        # Fetch all online & active servers
        servers = (
            db.query(Server)
            .filter(Server.status == "online", Server.is_active == True)
            .all()
        )
        if not servers:
            logging.info("No online servers found – nothing to process.")
            return
        logging.info(f"Running anomaly detection on {len(servers)} server(s).")
        for srv in servers:
            # Organization check is implicit – the model is scoped per org
            try:
                detect_anomalies(db, srv.id, minutes=60)
                logging.info(f"Processed server {srv.name} ({srv.id})")
            except Exception as e:
                logging.error(f"Error processing server {srv.id}: {e}")
        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    run_detection()
