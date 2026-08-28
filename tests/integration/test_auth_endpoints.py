import pytest

@pytest.mark.asyncio
async def test_register_login_flow(client):
    r = await client.post("/api/v1/auth/register", json={"name": "Ana", "email": "ana_int@upeu.edu.pe", "password": "Ana12345", "role": "FIELD_TECH"})
    assert r.status_code in (201, 409)  # puede ya existir de otro test si scope session
    # login
    r = await client.post("/api/v1/auth/login", json={"email": "ana_int@upeu.edu.pe", "password": "Ana12345"})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data and "refresh_token" in data
    token = data["access_token"]
    # me
    r = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "ana_int@upeu.edu.pe"

@pytest.mark.asyncio
async def test_login_invalid(client):
    r = await client.post("/api/v1/auth/login", json={"email": "ana_int@upeu.edu.pe", "password": "wrongpass1"})
    assert r.status_code == 401

@pytest.mark.asyncio
async def test_register_duplicate(client):
    await client.post("/api/v1/auth/register", json={"name": "Dup", "email": "dup@upeu.edu.pe", "password": "Dup12345"})
    r = await client.post("/api/v1/auth/register", json={"name": "Dup2", "email": "dup@upeu.edu.pe", "password": "Dup12345"})
    assert r.status_code == 409

@pytest.mark.asyncio
async def test_rbac_admin_only(client, admin_token, user_token):
    r = await client.get("/api/v1/users", headers={"Authorization": f"Bearer {user_token}"})
    assert r.status_code == 403
    r = await client.get("/api/v1/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    assert isinstance(r.json(), list)

@pytest.mark.asyncio
async def test_refresh_and_logout(client):
    await client.post("/api/v1/auth/register", json={"name": "Ref", "email": "ref@upeu.edu.pe", "password": "Ref12345"})
    r = await client.post("/api/v1/auth/login", json={"email": "ref@upeu.edu.pe", "password": "Ref12345"})
    refresh = r.json()["refresh_token"]
    token = r.json()["access_token"]
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert r.status_code == 200
    assert "access_token" in r.json()
    r = await client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200

@pytest.mark.asyncio
async def test_lockout(client):
    email = "lock@upeu.edu.pe"
    await client.post("/api/v1/auth/register", json={"name": "Lock", "email": email, "password": "Lock1234"})
    for _ in range(5):
        await client.post("/api/v1/auth/login", json={"email": email, "password": "wrongpass1"})
    r = await client.post("/api/v1/auth/login", json={"email": email, "password": "wrongpass1"})
    assert r.status_code == 423
    assert "retry_after" in str(r.text)
