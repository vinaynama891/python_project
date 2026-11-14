"""
Tests for Scikit-Learn Isolation Forest Anomaly Detection
"""
from backend.tests.test_metrics_api import helper_register_server, make_sample_payload


def test_anomaly_model_cold_start_handling(client, test_user_and_org):
    headers = test_user_and_org["headers"]

    # 1. Model status before training
    status_res = client.get("/api/ai/model-status", headers=headers)
    assert status_res.status_code == 200
    assert status_res.json()["is_trained"] is False
    assert "Insufficient historical data" in status_res.json()["status_message"]

    # 2. Attempt training with 0 metrics
    train_res = client.post("/api/ai/train", headers=headers)
    assert train_res.status_code == 200
    assert train_res.json()["success"] is False
    assert "Insufficient historical data" in train_res.json()["message"] or "No registered servers" in train_res.json()["message"]


def test_anomaly_model_training_and_detection(client, test_user_and_org):
    headers = test_user_and_org["headers"]
    server_id, agent_token = helper_register_server(client, headers, "ML-Train-Node")
    agent_headers = {"X-Agent-Token": agent_token, "X-Server-ID": server_id}

    # Ingest 20 standard metrics to satisfy ML_MIN_TRAINING_SAMPLES
    for i in range(20):
        client.post(
            "/api/agent/metrics",
            json=make_sample_payload(server_id, cpu=30.0 + (i % 5), ram=50.0 + (i % 3)),
            headers=agent_headers
        )

    # Train model
    train_res = client.post("/api/ai/train?contamination=0.1", headers=headers)
    assert train_res.status_code == 200
    train_data = train_res.json()
    assert train_data["success"] is True
    assert train_data["training_samples"] >= 15

    # Check model status
    status_res = client.get("/api/ai/model-status", headers=headers)
    assert status_res.status_code == 200
    assert status_res.json()["is_trained"] is True
    assert status_res.json()["algorithm"] == "Isolation Forest (Scikit-learn)"

    # Now ingest an extreme multi-dimensional anomaly (CPU 99%, RAM 98%)
    anomaly_res = client.post(
        "/api/agent/metrics",
        json=make_sample_payload(server_id, cpu=99.0, ram=98.0),
        headers=agent_headers
    )
    assert anomaly_res.status_code == 201

    # Check anomaly logs
    anom_list = client.get("/api/ai/anomalies", headers=headers)
    assert anom_list.status_code == 200
