"""Tests for health check and root endpoints."""


async def test_root(client_unauthenticated):
    resp = await client_unauthenticated.get("/api/")
    assert resp.status_code == 200
    data = resp.json()
    assert "InFinea" in data["message"]


async def test_health_check(client_unauthenticated):
    resp = await client_unauthenticated.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
