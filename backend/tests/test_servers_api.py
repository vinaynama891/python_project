"""
Tests for Server Lifecycle, Token Provisioning & Heartbeats
"""
from datetime import datetime, timedelta, timezone
from backend.app.models.models import Server


def test_create_server_slot(client, test_user_and_org):
    headers = test_user_and_org["headers"]
    payload = {
        "name": "Prod-Node-Alpha",
        "description": "Primary API Server"
    }
    r = client.post("/api/servers", json=payload, headers=headers)
    assert r.status_code == 201
    data = r.json()
    assert "server_id" in data
    assert "registration_token" in data
    assert data["registration_token"].startswith("cp_reg_")
    assert "registration_command_windows" in data
    assert "registration_command_linux" in data


def test_agent_registration_flow(client, test_user_and_org):
    headers = test_user_and_org["headers"]
    # 1. Create Server
    create_res = client.post("/api/servers", json={"name": "Linux-Worker-01"}, headers=headers)
    reg_token = create_res.json()["registration_token"]

    # 2. Agent pairs with registration token
    agent_payload = {
        "registration_token": reg_token,
        "hostname": "worker-linux-box",
        "server_name": "Linux-Worker-01",
        "os": "Linux",
        "os_version": "Ubuntu 22.04 LTS",
        "architecture": "x86_64",
        "ip_address": "192.168.1.105"
    }
    pair_res = client.post("/api/agent/register", json=agent_payload)
    assert pair_res.status_code == 200
    pair_data = pair_res.json()
    assert "server_id" in pair_data
    assert "agent_token" in pair_data
    assert pair_data["agent_token"].startswith("cp_agt_")

    # 3. Verify server status is now online
    server_res = client.get(f"/api/servers/{pair_data['server_id']}", headers=headers)
    assert server_res.status_code == 200
    assert server_res.json()["status"] == "online"
    assert server_res.json()["hostname"] == "worker-linux-box"


def test_agent_registration_invalid_token(client):
    agent_payload = {
        "registration_token": "cp_reg_fake_invalid_token",
        "hostname": "fake-host",
        "os": "Linux",
        "os_version": "1.0",
        "architecture": "x86_64",
        "ip_address": "127.0.0.1"
    }
    r = client.post("/api/agent/register", json=agent_payload)
    assert r.status_code == 404


def test_agent_heartbeat(client, test_user_and_org):
    headers = test_user_and_org["headers"]
    create_res = client.post("/api/servers", json={"name": "Node-Heartbeat-Test"}, headers=headers)
    server_id = create_res.json()["server_id"]

    hb_res = client.post("/api/agent/heartbeat", json={
        "server_id": server_id,
        "agent_version": "1.0.0",
        "health_status": "healthy"
    })
    assert hb_res.status_code == 200
    assert hb_res.json()["status"] == "acknowledged"


def test_offline_detection(client, test_user_and_org, db_session):
    headers = test_user_and_org["headers"]
    create_res = client.post("/api/servers", json={"name": "Stale-Node"}, headers=headers)
    server_id = create_res.json()["server_id"]

    # Manually backdate the last heartbeat by 2 hours
    server = db_session.query(Server).filter(Server.id == server_id).first()
    server.last_heartbeat = datetime.now(timezone.utc) - timedelta(hours=2)
    server.status = "online"
    db_session.commit()

    # Query server list to trigger offline timeout check
    r = client.get("/api/servers", headers=headers)
    assert r.status_code == 200
    servers = r.json()
    stale_s = next(s for s in servers if s["id"] == server_id)
    assert stale_s["status"] == "offline"
