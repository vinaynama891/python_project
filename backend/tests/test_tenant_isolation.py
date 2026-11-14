"""
Tests for Multi-Tenant Data Isolation and Credential Revocation
"""
from backend.app.core.security import get_password_hash, create_access_token
from backend.app.models.models import User, Organization, OrganizationMember
from backend.tests.test_metrics_api import helper_register_server, make_sample_payload


def test_cross_organization_data_isolation(client, test_user_and_org, db_session):
    # test_user_and_org belongs to "Test Engineering Org"
    headers_org1 = test_user_and_org["headers"]

    # Create a server in Org 1
    create_res = client.post("/api/servers", json={"name": "Org1-Private-Server"}, headers=headers_org1)
    org1_server_id = create_res.json()["server_id"]

    # Create a second user in a different Organization (Org 2)
    user2 = User(
        email="competitor@enterprise.com",
        hashed_password=get_password_hash("Password456!"),
        full_name="Competitor Lead",
        role="admin"
    )
    db_session.add(user2)
    db_session.flush()

    org2 = Organization(name="Competitor Org", slug="competitor-org")
    db_session.add(org2)
    db_session.flush()

    db_session.add(OrganizationMember(user_id=user2.id, organization_id=org2.id, role="owner"))
    db_session.commit()

    token2 = create_access_token(user2.id, org_id=org2.id, role=user2.role)
    headers_org2 = {"Authorization": f"Bearer {token2}"}

    # 1. User 2 lists servers -> Org 1 server must NOT appear
    r = client.get("/api/servers", headers=headers_org2)
    assert r.status_code == 200
    org2_servers = r.json()
    assert all(s["id"] != org1_server_id for s in org2_servers)

    # 2. User 2 attempts direct access to Org 1 server -> 404 Not Found
    r = client.get(f"/api/servers/{org1_server_id}", headers=headers_org2)
    assert r.status_code == 404


def test_agent_token_revocation(client, test_user_and_org):
    headers = test_user_and_org["headers"]
    server_id, agent_token = helper_register_server(client, headers, "Revoke-Test-Node")
    agent_headers = {"X-Agent-Token": agent_token, "X-Server-ID": server_id}

    # 1. Ingest metric successfully
    r1 = client.post("/api/agent/metrics", json=make_sample_payload(server_id), headers=agent_headers)
    assert r1.status_code == 201

    # 2. Revoke credentials
    revoke_res = client.post(f"/api/agent/revoke?server_id={server_id}")
    assert revoke_res.status_code == 200

    # 3. Subsequent ingestion must be rejected with 401
    r2 = client.post("/api/agent/metrics", json=make_sample_payload(server_id), headers=agent_headers)
    assert r2.status_code == 401
    assert "revoked" in r2.json()["detail"].lower()
