#!/usr/bin/env python
"""End‑to‑end sanity check for the ML Anomaly Detection pipeline.
It:
1. Ensures there is at least one Organization and one online Server.
2. Inserts synthetic Metric records for the last 30 minutes (with all required fields).
3. Trains the IsolationForest model for the organization.
4. Runs the detection function on the test server.
5. Prints a summary of any anomalies detected and the number of Alerts created.
"""

import sys
from pathlib import Path
import random
from datetime import datetime, timedelta

# Make project root importable
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from backend.app.database.session import SessionLocal
from backend.app.models.models import Organization, Server, Metric, Alert
from backend.app.ml.anomaly_detector import train_model, detect_anomalies


def main():
    db = SessionLocal()
    try:
        # 1️⃣ Ensure organization
        org = db.query(Organization).first()
        if not org:
            print("❌ No organization found in the DB – cannot proceed.")
            return
        # 2️⃣ Ensure at least one online server for that org
        server = (
            db.query(Server)
            .filter(Server.organization_id == org.id, Server.is_active == True)
            .first()
        )
        if not server:
            # create a dummy server
            server = Server(
                organization_id=org.id,
                name="DemoServer",
                status="online",
                is_active=True,
            )
            db.add(server)
            db.commit()
            db.refresh(server)
            print(f"🛠 Created demo server {server.id}")
        else:
            if server.status != "online":
                server.status = "online"
                db.commit()
        # 3️⃣ Insert synthetic metrics (30 records, 1‑minute apart) – include required fields
        now = datetime.utcnow()
        for i in range(30):
            m = Metric(
                server_id=server.id,
                timestamp=now - timedelta(minutes=30 - i),
                cpu_percent=random.uniform(5, 95),
                cpu_per_core=None,
                cpu_frequency_current=None,
                cpu_cores=None,
                cpu_temperature=None,
                # RAM fields (all required)
                ram_total=random.uniform(8, 32),
                ram_used=random.uniform(2, 24),
                ram_available=random.uniform(0, 16),
                ram_percent=random.uniform(10, 90),
                swap_percent=None,
                # Disk fields (required)
                disk_total=random.uniform(100, 500),
                disk_used=random.uniform(20, 400),
                disk_free=random.uniform(0, 200),
                disk_percent=random.uniform(10, 90),
                disk_read_speed=0.0,
                disk_write_speed=0.0,
                disk_io_ops=0,
                # Network (nullable but provide defaults)
                net_bytes_sent=random.uniform(1000, 5000),
                net_bytes_recv=random.uniform(1000, 5000),
                net_upload_speed=0.0,
                net_download_speed=0.0,
                net_packets_sent=0,
                net_packets_recv=0,
                raw_details=None,
            )
            db.add(m)
        db.commit()
        print(f"🔢 Inserted 30 fake Metric rows for server {server.id}")
        # 4️⃣ Train the model for the organization
        train_res = train_model(db, org.id, contamination=0.05)
        print("🧠 Training result:", train_res["status_message"])
        # 5️⃣ Run detection on the server (last 60 min window)
        anomalies = detect_anomalies(db, server.id, minutes=60)
        if not anomalies:
            print("✅ No anomalies detected – pipeline works and returned an empty list.")
        else:
            print(f"⚠️ Detected {len(anomalies)} anomalies:")
            for a in anomalies[:5]:
                ts = a["timestamp"].isoformat() if hasattr(a["timestamp"], "isoformat") else str(a["timestamp"])
                print(f" • {ts} – score {a['score']:.3f} (cpu={a['cpu']:.1f}%, ram={a['ram']:.1f}%)")
        # Show that alerts were created
        alerts = db.query(Alert).filter(Alert.server_id == server.id).all()
        print(f"📣 Alerts created for this server: {len(alerts)}")
    finally:
        db.close()

if __name__ == "__main__":
    main()

"""End‑to‑end sanity check for the ML Anomaly Detection pipeline.
It:
1. Ensures there is at least one Organization and one online Server.
2. Inserts synthetic Metric records for the last 30 minutes.
3. Trains the IsolationForest model for the organization.
4. Runs the detection endpoint (via the service function) on the test server.
5. Prints a summary of any anomalies detected.
"""

import sys
from pathlib import Path
import random
from datetime import datetime, timedelta

# Make project root importable
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from backend.app.database.session import SessionLocal
from backend.app.models.models import Organization, Server, Metric
from backend.app.ml.anomaly_detector import train_model, detect_anomalies


def main():
    db = SessionLocal()
    try:
        # 1️⃣ Ensure organization
        org = db.query(Organization).first()
        if not org:
            print("❌ No organization found in the DB – cannot proceed.")
            return
        # 2️⃣ Ensure at least one online server for that org
        server = (
            db.query(Server)
            .filter(Server.organization_id == org.id, Server.is_active == True)
            .first()
        )
        if not server:
            # create a dummy server
            server = Server(
                organization_id=org.id,
                name="DemoServer",
                status="online",
                is_active=True,
            )
            db.add(server)
            db.commit()
            db.refresh(server)
            print(f"🛠 Created demo server {server.id}")
        else:
            # make sure it's marked online
            if server.status != "online":
                server.status = "online"
                db.commit()
        # 3️⃣ Insert synthetic metrics (30 records, 1‑minute apart)
        now = datetime.utcnow()
        for i in range(30):
            m = Metric(
                server_id=server.id,
                timestamp=now - timedelta(minutes=30 - i),
                cpu_percent=random.uniform(5, 95),
                ram_percent=random.uniform(10, 90),
                disk_percent=random.uniform(20, 80),
                net_bytes_sent=random.uniform(1000, 5000),
                net_bytes_recv=random.uniform(1000, 5000),
            )
            db.add(m)
        db.commit()
        print(f"🔢 Inserted 30 fake Metric rows for server {server.id}")
        # 4️⃣ Train the model for the organization
        train_res = train_model(db, org.id, contamination=0.05)
        print("🧠 Training result:", train_res["status_message"])
        # 5️⃣ Run detection on the server (last 60 min window)
        anomalies = detect_anomalies(db, server.id, minutes=60)
        if not anomalies:
            print("✅ No anomalies detected – pipeline works and returned an empty list.")
        else:
            print(f"⚠️ Detected {len(anomalies)} anomalies:")
            for a in anomalies[:5]:
                ts = a["timestamp"].isoformat() if hasattr(a["timestamp"], "isoformat") else str(a["timestamp"])
                print(f" • {ts} – score {a['score']:.3f} (cpu={a['cpu']:.1f}%, ram={a['ram']:.1f}%)")
        # Show that alerts were created
        alerts = db.query(Alert).filter(Alert.server_id == server.id).all()
        print(f"📣 Alerts created for this server: {len(alerts)}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
