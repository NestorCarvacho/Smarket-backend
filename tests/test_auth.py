import pytest

pytestmark = pytest.mark.asyncio


async def test_register_and_login(client):
    register_resp = await client.post(
        "/api/v1/auth/register", json={"email": "user@example.com", "password": "supersecret1"}
    )
    assert register_resp.status_code == 201
    assert register_resp.json()["email"] == "user@example.com"

    duplicate_resp = await client.post(
        "/api/v1/auth/register", json={"email": "user@example.com", "password": "supersecret1"}
    )
    assert duplicate_resp.status_code == 409

    login_resp = await client.post(
        "/api/v1/auth/login", json={"email": "user@example.com", "password": "supersecret1"}
    )
    assert login_resp.status_code == 200
    tokens = login_resp.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens


async def test_login_with_wrong_password_fails(client):
    await client.post(
        "/api/v1/auth/register", json={"email": "user2@example.com", "password": "supersecret1"}
    )
    login_resp = await client.post(
        "/api/v1/auth/login", json={"email": "user2@example.com", "password": "wrongpassword"}
    )
    assert login_resp.status_code == 401
    assert "intento" in login_resp.json()["detail"].lower()


async def test_lock_after_three_failures_and_unlock_via_reset(client):
    email = "locked@example.com"
    await client.post("/api/v1/auth/register", json={"email": email, "password": "supersecret1"})

    for _ in range(2):
        resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": "wrongpassword"}
        )
        assert resp.status_code == 401

    third = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "wrongpassword"}
    )
    assert third.status_code == 403
    assert third.json()["code"] == "account_locked"

    even_correct = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "supersecret1"}
    )
    assert even_correct.status_code == 403

    recover = await client.post(
        "/api/v1/auth/recover-password",
        json={"email": email, "new_password": "newsecret99"},
    )
    assert recover.status_code == 200

    login_ok = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "newsecret99"}
    )
    assert login_ok.status_code == 200


async def test_protected_route_requires_token(client):
    resp = await client.get("/api/v1/lists")
    assert resp.status_code == 401
