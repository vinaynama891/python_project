"""
Tests for Authentication & Authorization APIs
"""
def test_user_registration_success(client):
    payload = {
        "email": "sarah@infra.corp",
        "password": "StrongPassword2026!",
        "full_name": "Sarah Connor",
        "organization_name": "Cyberdyne Ops"
    }
    r = client.post("/api/auth/register", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "sarah@infra.corp"
    assert data["user"]["full_name"] == "Sarah Connor"


def test_user_registration_duplicate_email(client, test_user_and_org):
    payload = {
        "email": "dev@cloudpulse.io",
        "password": "DifferentPassword123!",
        "full_name": "Duplicate Tester"
    }
    r = client.post("/api/auth/register", json=payload)
    assert r.status_code == 400
    assert "already exists" in r.json()["detail"]


def test_user_login_success(client, test_user_and_org):
    payload = {
        "email": "dev@cloudpulse.io",
        "password": "SecretPassword123!"
    }
    r = client.post("/api/auth/login", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["user"]["email"] == "dev@cloudpulse.io"


def test_user_login_invalid_password(client, test_user_and_org):
    payload = {
        "email": "dev@cloudpulse.io",
        "password": "WrongPassword!"
    }
    r = client.post("/api/auth/login", json=payload)
    assert r.status_code == 401


def test_auth_me_endpoint(client, test_user_and_org):
    headers = test_user_and_org["headers"]
    r = client.get("/api/auth/me", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == "dev@cloudpulse.io"
    assert data["role"] == "admin"


def test_refresh_token_flow(client, test_user_and_org):
    # Log in first to obtain refresh token
    login_res = client.post("/api/auth/login", json={
        "email": "dev@cloudpulse.io",
        "password": "SecretPassword123!"
    })
    refresh_token = login_res.json()["refresh_token"]

    r = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert r.status_code == 200
    new_data = r.json()
    assert "access_token" in new_data
