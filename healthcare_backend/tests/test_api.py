"""
tests/test_api.py
Integration tests using httpx + pytest-asyncio.
Run with:  pytest tests/ -v
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app

# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def client():
    """Async HTTP test client backed by the FastAPI app directly (no network)."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def analyst_token(client):
    """Registers an analyst and returns its JWT."""
    await client.post("/api/v1/auth/register", json={
        "email":    "analyst@test.com",
        "password": "testpass123",
        "role":     "analyst",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email":    "analyst@test.com",
        "password": "testpass123",
    })
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def admin_token(client):
    """Registers an admin and returns its JWT."""
    await client.post("/api/v1/auth/register", json={
        "email":    "admin@test.com",
        "password": "testpass123",
        "role":     "admin",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email":    "admin@test.com",
        "password": "testpass123",
    })
    return resp.json()["access_token"]


# ─── Health ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ─── Auth ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_and_login(client):
    r = await client.post("/api/v1/auth/register", json={
        "email": "newuser@test.com", "password": "secure123"
    })
    assert r.status_code == 201
    assert r.json()["role"] == "public"

    r2 = await client.post("/api/v1/auth/login", json={
        "email": "newuser@test.com", "password": "secure123"
    })
    assert r2.status_code == 200
    assert "access_token" in r2.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    r = await client.post("/api/v1/auth/login", json={
        "email": "nobody@test.com", "password": "wrong"
    })
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me_endpoint(client, analyst_token):
    r = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert r.status_code == 200
    assert r.json()["role"] == "analyst"


# ─── Districts ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_districts_public(client):
    """Districts endpoint is public — no auth needed."""
    r = await client.get("/api/v1/districts?year=2023&size=10")
    assert r.status_code == 200
    body = r.json()
    assert "results" in body
    assert "total" in body


@pytest.mark.asyncio
async def test_map_endpoint(client):
    r = await client.get("/api/v1/map?year=2023")
    assert r.status_code == 200
    assert r.json()["type"] == "FeatureCollection"


# ─── Predict (analyst required) ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_predict_without_auth(client):
    r = await client.post("/api/v1/predict", json={
        "district_id": "IND_0001", "year": 2023,
        "population": 500000, "number_of_doctors": 300,
        "number_of_hospitals": 20, "hospital_beds": 600,
        "primary_health_centers": 15, "disease_burden_index": 0.4,
    })
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_predict_public_user_blocked(client):
    """Public role should be denied."""
    await client.post("/api/v1/auth/register", json={
        "email": "pub@test.com", "password": "testpass123", "role": "public"
    })
    login = await client.post("/api/v1/auth/login", json={
        "email": "pub@test.com", "password": "testpass123"
    })
    token = login.json()["access_token"]
    r = await client.post(
        "/api/v1/predict",
        json={"district_id": "IND_0001", "year": 2023, "population": 500000,
              "number_of_doctors": 300, "number_of_hospitals": 20,
              "hospital_beds": 600, "primary_health_centers": 15,
              "disease_burden_index": 0.4},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403


# ─── Reports (analyst required) ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_reports_analyst(client, analyst_token):
    r = await client.get(
        "/api/v1/reports?year=2023",
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert r.status_code == 200
    assert "results" in r.json()
