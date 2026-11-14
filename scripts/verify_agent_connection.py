"""
CloudPulse Phase 4 Verification Script
Verifies end-to-end integration: User Registration -> Server Provisioning ->
Agent Self-Registration -> Real Hardware Telemetry Ingestion -> DB Verification.
"""
import sys
import time
import requests
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.collector.system_collector import SystemCollector
from agent.transport.auth import register_agent
from agent.transport.sender import MetricSender
from agent.config.settings import AgentConfig


def run_verification():
    base_url = "http://127.0.0.1:8000"
    print(">>> 1. Checking backend health...")
    r = requests.get(f"{base_url}/")
    assert r.status_code == 200, f"Backend not reachable: {r.status_code}"
    print("    Backend is operational:", r.json())

    print("\n>>> 2. Registering admin user...")
    user_payload = {
        "email": "admin@cloudpulse.io",
        "password": "CloudPulsePassword2026!",
        "full_name": "Infrastructure Lead",
        "organization_name": "Capstone Production Systems"
    }
    r = requests.post(f"{base_url}/api/auth/register", json=user_payload)
    if r.status_code == 400 and "already exists" in r.text:
        # Try login
        r = requests.post(f"{base_url}/api/auth/login", json={
            "email": user_payload["email"],
            "password": user_payload["password"]
        })
    assert r.status_code in (200, 201), f"Auth failed: {r.status_code} {r.text}"
    auth_data = r.json()
    token = auth_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("    Authenticated! Access token obtained.")

    print("\n>>> 3. Creating server slot...")
    r = requests.post(f"{base_url}/api/servers", json={
        "name": "Host-Windows-Workstation",
        "description": "Real physical development machine running CloudPulse agent"
    }, headers=headers)
    assert r.status_code == 201, f"Failed to create server: {r.status_code} {r.text}"
    server_info = r.json()
    server_id = server_info["server_id"]
    reg_token = server_info["registration_token"]
    print(f"    Server created! ID: {server_id}")
    print(f"    Registration Token: {reg_token}")

    print("\n>>> 4. Registering Agent using token...")
    pair_res = register_agent(base_url, reg_token, "Host-Windows-Workstation")
    assert pair_res is not None, "Agent registration failed!"
    paired_server_id, agent_token = pair_res
    print(f"    Agent successfully registered with token: {agent_token[:12]}...")

    print("\n>>> 5. Collecting real hardware metrics using SystemCollector...")
    collector = SystemCollector(agent_version="1.0.0")
    time.sleep(1.0)
    real_telemetry = collector.collect_all_metrics()
    print(f"    Collected: CPU={real_telemetry['cpu']['cpu_percent']}% | "
          f"RAM={real_telemetry['memory']['ram_percent']}% | "
          f"Disk={real_telemetry['disk']['disk_percent']}% | "
          f"Top CPU Processes={len(real_telemetry['processes']['top_cpu'])}")

    print("\n>>> 6. Transmitting real telemetry to backend...")
    cfg = AgentConfig(
        server_url=base_url,
        server_id=paired_server_id,
        agent_token=agent_token
    )
    sender = MetricSender(cfg)
    sent = sender.send_metrics(real_telemetry)
    assert sent, "Failed to send metrics to backend!"
    print("    Telemetry transmitted successfully to /api/agent/metrics!")

    print("\n>>> 7. Verifying data in backend via admin API...")
    r = requests.get(f"{base_url}/api/servers/{paired_server_id}", headers=headers)
    assert r.status_code == 200
    server_details = r.json()
    print("    Server Status:", server_details["status"])
    print("    Server Hostname:", server_details["hostname"])
    print("    Server OS:", server_details["os"], server_details["os_version"])
    print("    Latest CPU:", server_details["latest_cpu"], "%")
    print("    Latest RAM:", server_details["latest_ram"], "%")
    assert server_details["status"] == "online", "Server status is not online!"
    assert server_details["latest_cpu"] is not None, "Latest CPU was not stored!"

    print("\n>>> 8. Verifying latest metrics and process records...")
    r = requests.get(f"{base_url}/api/metrics/{paired_server_id}", headers=headers)
    assert r.status_code == 200
    metrics_data = r.json()
    assert metrics_data["has_metrics"] is True
    processes = metrics_data["processes"]
    print(f"    Retrieved {len(processes)} recorded process metrics from database.")
    if processes:
        print(f"    Sample recorded process: {processes[0]['name']} (PID: {processes[0]['pid']}, RAM: {processes[0]['memory_percent']}%)")

    print("\n" + "=" * 60)
    print("PHASE 4 VERIFICATION COMPLETE: ALL CHECKS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    run_verification()
