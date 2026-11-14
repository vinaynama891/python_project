"""
Tests for Metric Ingestion, Schemas & Time-Series Retrieval
"""
from datetime import datetime, timezone


def helper_register_server(client, headers, name="Metrics-Test-Node"):
    create_res = client.post("/api/servers", json={"name": name}, headers=headers)
    reg_token = create_res.json()["registration_token"]
    pair_res = client.post("/api/agent/register", json={
        "registration_token": reg_token,
        "hostname": f"{name}-host",
        "server_name": name,
        "os": "Windows",
        "os_version": "10",
        "architecture": "AMD64",
        "ip_address": "10.0.0.12"
    })
    return pair_res.json()["server_id"], pair_res.json()["agent_token"]


def make_sample_payload(server_id: str, cpu: float = 45.0, ram: float = 60.0, disk: float = 50.0):
    return {
        "server_id": server_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "system": {
            "hostname": "test-box",
            "ip_address": "10.0.0.12",
            "os": "Windows",
            "os_version": "10",
            "architecture": "AMD64",
            "cpu_cores_physical": 4,
            "cpu_cores_logical": 8,
            "boot_time": "2026-11-10T00:00:00Z",
            "uptime_seconds": 12000.0,
            "agent_version": "1.0.0",
            "agent_health": "healthy"
        },
        "cpu": {
            "cpu_percent": cpu,
            "cpu_per_core": [cpu, cpu],
            "cpu_frequency": {"current": 2400.0, "min": 800.0, "max": 3200.0},
            "cpu_cores_logical": 8,
            "cpu_cores_physical": 4,
            "cpu_temperature": None
        },
        "memory": {
            "ram_total": 16000000000,
            "ram_used": int(16000000000 * (ram / 100)),
            "ram_available": int(16000000000 * (1 - (ram / 100))),
            "ram_percent": ram,
            "swap_total": 4000000000,
            "swap_used": 0,
            "swap_free": 4000000000,
            "swap_percent": 0.0
        },
        "disk": {
            "disk_total": 500000000000,
            "disk_used": int(500000000000 * (disk / 100)),
            "disk_free": int(500000000000 * (1 - (disk / 100))),
            "disk_percent": disk,
            "disk_read_bytes": 100000,
            "disk_write_bytes": 100000,
            "disk_io_operations": 500,
            "disk_read_speed_bytes_sec": 1200.0,
            "disk_write_speed_bytes_sec": 3400.0
        },
        "network": {
            "bytes_sent": 50000,
            "bytes_recv": 80000,
            "upload_speed_bytes_sec": 500.0,
            "download_speed_bytes_sec": 1200.0,
            "packets_sent": 100,
            "packets_recv": 150,
            "interfaces": []
        },
        "processes": {
            "top_cpu": [
                {
                    "pid": 101,
                    "name": "python.exe",
                    "username": "tester",
                    "status": "running",
                    "cpu_percent": 15.0,
                    "memory_percent": 2.5,
                    "memory_bytes": 40000000
                }
            ],
            "top_memory": []
        }
    }


def test_metric_ingestion_success(client, test_user_and_org):
    headers = test_user_and_org["headers"]
    server_id, agent_token = helper_register_server(client, headers, "Ingest-Test-Node")

    payload = make_sample_payload(server_id, cpu=35.0, ram=55.0)
    agent_headers = {
        "X-Agent-Token": agent_token,
        "X-Server-ID": server_id
    }
    r = client.post("/api/agent/metrics", json=payload, headers=agent_headers)
    assert r.status_code == 201
    assert r.json()["status"] == "success"


def test_metric_ingestion_unauthenticated(client, test_user_and_org):
    headers = test_user_and_org["headers"]
    server_id, _ = helper_register_server(client, headers, "Unauth-Node")
    payload = make_sample_payload(server_id)

    # Missing X-Agent-Token header
    r = client.post("/api/agent/metrics", json=payload)
    assert r.status_code == 401


def test_metric_retrieval(client, test_user_and_org):
    headers = test_user_and_org["headers"]
    server_id, agent_token = helper_register_server(client, headers, "Query-Node")
    agent_headers = {"X-Agent-Token": agent_token, "X-Server-ID": server_id}

    # Ingest 2 metrics
    client.post("/api/agent/metrics", json=make_sample_payload(server_id, cpu=40.0), headers=agent_headers)
    client.post("/api/agent/metrics", json=make_sample_payload(server_id, cpu=50.0), headers=agent_headers)

    # 1. Test latest
    latest_r = client.get("/api/metrics/latest", headers=headers)
    assert latest_r.status_code == 200
    assert server_id in latest_r.json()
    assert latest_r.json()[server_id]["cpu_percent"] == 50.0

    # 2. Test history
    hist_r = client.get(f"/api/metrics/history?server_id={server_id}&hours=1", headers=headers)
    assert hist_r.status_code == 200
    assert len(hist_r.json()) == 2

    # 3. Test detailed server metrics
    det_r = client.get(f"/api/metrics/{server_id}", headers=headers)
    assert det_r.status_code == 200
    assert det_r.json()["has_metrics"] is True
    assert len(det_r.json()["processes"]) == 1
    assert det_r.json()["processes"][0]["name"] == "python.exe"
