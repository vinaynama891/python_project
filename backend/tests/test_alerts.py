"""
Tests for Alert Engine: Thresholds, Deduplication & Lifecycle States
"""
from backend.tests.test_metrics_api import helper_register_server, make_sample_payload


def test_alert_generation_and_deduplication(client, test_user_and_org):
    headers = test_user_and_org["headers"]
    server_id, agent_token = helper_register_server(client, headers, "Alert-Test-Node")
    agent_headers = {"X-Agent-Token": agent_token, "X-Server-ID": server_id}

    # 1. Ingest normal metric (CPU 40%, RAM 50%)
    client.post("/api/agent/metrics", json=make_sample_payload(server_id, cpu=40.0, ram=50.0), headers=agent_headers)
    alerts_res = client.get("/api/alerts?status=active", headers=headers)
    assert len(alerts_res.json()) == 0

    # 2. Ingest CPU warning (>80%: 85%)
    r = client.post("/api/agent/metrics", json=make_sample_payload(server_id, cpu=85.0), headers=agent_headers)
    assert r.json()["alerts_triggered"] == 1

    alerts_res = client.get("/api/alerts?status=active", headers=headers)
    assert len(alerts_res.json()) == 1
    alert = alerts_res.json()[0]
    assert alert["metric_type"] == "cpu"
    assert alert["severity"] == "warning"
    assert alert["value"] == 85.0

    # 3. Test Deduplication: Ingest subsequent high CPU metric (92%: critical)
    # Should update existing alert rather than generating a 2nd duplicate active row
    client.post("/api/agent/metrics", json=make_sample_payload(server_id, cpu=92.0), headers=agent_headers)
    alerts_after = client.get("/api/alerts?status=active", headers=headers)
    assert len(alerts_after.json()) == 1  # Deduplicated!
    updated_alert = alerts_after.json()[0]
    assert updated_alert["severity"] == "critical"
    assert updated_alert["value"] == 92.0


def test_alert_acknowledge_and_resolve(client, test_user_and_org):
    headers = test_user_and_org["headers"]
    server_id, agent_token = helper_register_server(client, headers, "Lifecycle-Alert-Node")
    agent_headers = {"X-Agent-Token": agent_token, "X-Server-ID": server_id}

    # Trigger critical alert (RAM 96%)
    client.post("/api/agent/metrics", json=make_sample_payload(server_id, ram=96.0), headers=agent_headers)
    alerts = client.get("/api/alerts?status=active", headers=headers).json()
    assert len(alerts) >= 1
    alert_id = alerts[0]["id"]

    # Acknowledge
    ack_res = client.put(f"/api/alerts/{alert_id}/acknowledge", json={"acknowledged_by": "OnCall Engineer"}, headers=headers)
    assert ack_res.status_code == 200
    assert ack_res.json()["status"] == "acknowledged"
    assert ack_res.json()["acknowledged_by"] == "OnCall Engineer"

    # Resolve
    res_res = client.put(f"/api/alerts/{alert_id}/resolve", json={"resolved_by": "OnCall Engineer"}, headers=headers)
    assert res_res.status_code == 200
    assert res_res.json()["status"] == "resolved"
    assert res_res.json()["resolved_at"] is not None
