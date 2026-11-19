"""
Tests for Performance Debt Tracker (PDT) - Debt Detection, Lifecycle, and Summary
"""
from backend.tests.test_metrics_api import helper_register_server, make_sample_payload


def test_pdt_analyze_no_metrics(client, test_user_and_org):
    """PDT analysis returns informative message when no metrics exist."""
    headers = test_user_and_org["headers"]
    server_id, agent_token = helper_register_server(client, headers, "PDT-Empty-Node")

    r = client.get(f"/api/pdt/analyze/{server_id}?hours=24", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["debts_detected"] == 0
    assert "Insufficient" in data["status"]


def test_pdt_analyze_detects_cpu_debt(client, test_user_and_org):
    """PDT detects CPU performance debt when multiple high-CPU readings are ingested."""
    headers = test_user_and_org["headers"]
    server_id, agent_token = helper_register_server(client, headers, "PDT-CPU-Node")
    agent_headers = {"X-Agent-Token": agent_token, "X-Server-ID": server_id}

    # Ingest 5 metrics with CPU >= 75% (above 70% debt threshold)
    for cpu_val in [75.0, 80.0, 85.0, 78.0, 82.0]:
        client.post("/api/agent/metrics", json=make_sample_payload(server_id, cpu=cpu_val), headers=agent_headers)

    r = client.get(f"/api/pdt/analyze/{server_id}?hours=24", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["debts_detected"] >= 1
    # Find the CPU debt
    cpu_debts = [d for d in data["debts"] if d["category"] == "cpu"]
    assert len(cpu_debts) >= 1
    assert cpu_debts[0]["debt_score"] > 0
    assert cpu_debts[0]["status"] == "open"


def test_pdt_analyze_detects_memory_debt(client, test_user_and_org):
    """PDT detects memory performance debt with sustained high RAM usage."""
    headers = test_user_and_org["headers"]
    server_id, agent_token = helper_register_server(client, headers, "PDT-RAM-Node")
    agent_headers = {"X-Agent-Token": agent_token, "X-Server-ID": server_id}

    # Ingest 4 metrics with RAM >= 80% (above 75% debt threshold)
    for ram_val in [80.0, 85.0, 88.0, 82.0]:
        client.post("/api/agent/metrics", json=make_sample_payload(server_id, ram=ram_val), headers=agent_headers)

    r = client.get(f"/api/pdt/analyze/{server_id}?hours=24", headers=headers)
    assert r.status_code == 200
    data = r.json()
    mem_debts = [d for d in data["debts"] if d["category"] == "memory"]
    assert len(mem_debts) >= 1
    assert mem_debts[0]["estimated_impact"] in ["low", "medium", "high", "critical"]


def test_pdt_list_debts(client, test_user_and_org):
    """Listing debts returns all debt items for the organization."""
    headers = test_user_and_org["headers"]
    server_id, agent_token = helper_register_server(client, headers, "PDT-List-Node")
    agent_headers = {"X-Agent-Token": agent_token, "X-Server-ID": server_id}

    # Create some debts by analyzing high-usage metrics
    for cpu_val in [75.0, 80.0, 85.0, 78.0]:
        client.post("/api/agent/metrics", json=make_sample_payload(server_id, cpu=cpu_val), headers=agent_headers)
    client.get(f"/api/pdt/analyze/{server_id}?hours=24", headers=headers)

    r = client.get("/api/pdt/debts", headers=headers)
    assert r.status_code == 200
    debts = r.json()
    assert isinstance(debts, list)
    assert len(debts) >= 1


def test_pdt_update_debt_status(client, test_user_and_org):
    """Updating a debt status transitions it correctly through the lifecycle."""
    headers = test_user_and_org["headers"]
    server_id, agent_token = helper_register_server(client, headers, "PDT-Update-Node")
    agent_headers = {"X-Agent-Token": agent_token, "X-Server-ID": server_id}

    # Create debt
    for cpu_val in [75.0, 80.0, 85.0, 78.0]:
        client.post("/api/agent/metrics", json=make_sample_payload(server_id, cpu=cpu_val), headers=agent_headers)
    client.get(f"/api/pdt/analyze/{server_id}?hours=24", headers=headers)

    # Get debt list
    list_r = client.get("/api/pdt/debts", headers=headers)
    debt_id = list_r.json()[0]["id"]

    # Update to investigating
    update_r = client.put(f"/api/pdt/debts/{debt_id}", json={
        "status": "investigating",
        "resolution_notes": "Team is investigating the root cause."
    }, headers=headers)
    assert update_r.status_code == 200
    assert update_r.json()["status"] == "investigating"

    # Update to mitigated
    mitigate_r = client.put(f"/api/pdt/debts/{debt_id}", json={
        "status": "mitigated",
        "resolution_notes": "Scaled up CPU cores and optimized worker threads.",
        "resolved_by": "DevOps Team"
    }, headers=headers)
    assert mitigate_r.status_code == 200
    assert mitigate_r.json()["status"] == "mitigated"


def test_pdt_summary(client, test_user_and_org):
    """PDT summary returns correct aggregate statistics."""
    headers = test_user_and_org["headers"]
    server_id, agent_token = helper_register_server(client, headers, "PDT-Summary-Node")
    agent_headers = {"X-Agent-Token": agent_token, "X-Server-ID": server_id}

    for cpu_val in [75.0, 80.0, 85.0, 78.0]:
        client.post("/api/agent/metrics", json=make_sample_payload(server_id, cpu=cpu_val), headers=agent_headers)
    client.get(f"/api/pdt/analyze/{server_id}?hours=24", headers=headers)

    r = client.get("/api/pdt/summary", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert "total_debts" in data
    assert "open_debts" in data
    assert "avg_debt_score" in data
    assert "top_categories" in data
    assert data["total_debts"] >= 1


def test_pdt_debt_detail(client, test_user_and_org):
    """Getting a single debt detail returns all fields correctly."""
    headers = test_user_and_org["headers"]
    server_id, agent_token = helper_register_server(client, headers, "PDT-Detail-Node")
    agent_headers = {"X-Agent-Token": agent_token, "X-Server-ID": server_id}

    for cpu_val in [75.0, 80.0, 85.0, 78.0]:
        client.post("/api/agent/metrics", json=make_sample_payload(server_id, cpu=cpu_val), headers=agent_headers)
    client.get(f"/api/pdt/analyze/{server_id}?hours=24", headers=headers)

    list_r = client.get("/api/pdt/debts", headers=headers)
    debt_id = list_r.json()[0]["id"]

    r = client.get(f"/api/pdt/debts/{debt_id}", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == debt_id
    assert data["category"] == "cpu"
    assert data["debt_score"] > 0
    assert data["server_name"] is not None
    assert data["trend_direction"] in ["improving", "stable", "degrading"]
