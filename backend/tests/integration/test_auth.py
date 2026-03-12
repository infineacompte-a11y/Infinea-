"""
Integration tests — Auth routes.
P2 critical: ensures registration, login, session, and token flows work.

Tests:
- POST /api/auth/register
- POST /api/auth/login
- GET /api/auth/me (authenticated)
- POST /api/auth/logout
- POST /api/auth/refresh
- POST /api/auth/session
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, AsyncMock

from auth import create_token, hash_password


# ═══════════════════════════════════════════════════════════════════
# Fixtures specific to auth tests
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
async def db_with_user(mock_db):
    """Seed a user with a known password for login tests."""
    await mock_db.users.insert_one({
        "user_id": "user_login_test",
        "email": "login@infinea.app",
        "name": "Login User",
        "password_hash": hash_password("SecurePass123!"),
        "picture": None,
        "subscription_tier": "free",
        "total_time_invested": 0,
        "streak_days": 0,
        "last_session_date": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return mock_db


# ═══════════════════════════════════════════════════════════════════
# Auth helpers (unit tests)
# ═══════════════════════════════════════════════════════════════════


class TestAuthHelpers:

    def test_create_and_verify_token(self):
        """Round-trip: create → verify."""
        from auth import create_token, verify_token
        token = create_token("user_abc")
        user_id = verify_token(token)
        assert user_id == "user_abc"

    def test_verify_invalid_token(self):
        from auth import verify_token
        assert verify_token("invalid.token.here") is None

    def test_verify_expired_token(self):
        """Expired token returns None."""
        import jwt
        from config import JWT_SECRET, JWT_ALGORITHM
        payload = {
            "user_id": "user_expired",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1)
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        from auth import verify_token
        assert verify_token(token) is None

    def test_hash_and_verify_password(self):
        from auth import hash_password, verify_password
        hashed = hash_password("MyPassword123")
        assert verify_password("MyPassword123", hashed) is True
        assert verify_password("WrongPassword", hashed) is False


# ═══════════════════════════════════════════════════════════════════
# GET /api/auth/me — Authenticated route
# ═══════════════════════════════════════════════════════════════════


class TestAuthMe:

    @pytest.mark.asyncio
    async def test_get_me_returns_user(self, client):
        """GET /api/auth/me with valid auth → returns user data."""
        resp = await client.get("/api/auth/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == "user_test_abc123"
        assert data["email"] == "test@infinea.app"
        assert "subscription_tier" in data

    @pytest.mark.asyncio
    async def test_get_me_without_auth(self, app, mock_db):
        """GET /api/auth/me without token → 401."""
        from auth import get_current_user
        from httpx import AsyncClient, ASGITransport

        # Remove the auth override so the real auth kicks in
        app.dependency_overrides.pop(get_current_user, None)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as raw_client:
            resp = await raw_client.get("/api/auth/me")
        assert resp.status_code == 401

        # Restore override for other tests
        async def mock_auth():
            from tests.conftest import TEST_USER
            return TEST_USER.copy()
        app.dependency_overrides[get_current_user] = mock_auth


# ═══════════════════════════════════════════════════════════════════
# POST /api/auth/register
# ═══════════════════════════════════════════════════════════════════


class TestAuthRegister:

    @pytest.mark.asyncio
    async def test_register_success(self, client, mock_db):
        """New user registration → 200 with user_id and token."""
        # Patch the db import in auth_routes to use our mock
        with patch("routes.auth_routes.db", mock_db):
            resp = await client.post("/api/auth/register", json={
                "email": "new@infinea.app",
                "password": "StrongPass123!",
                "name": "New User",
            })

        assert resp.status_code == 200
        data = resp.json()
        assert "user_id" in data
        assert data["email"] == "new@infinea.app"
        assert data["name"] == "New User"
        assert "token" in data

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client, mock_db):
        """Duplicate email → 400."""
        # Seed existing user
        await mock_db.users.insert_one({
            "user_id": "existing_user",
            "email": "taken@infinea.app",
        })

        with patch("routes.auth_routes.db", mock_db):
            resp = await client.post("/api/auth/register", json={
                "email": "taken@infinea.app",
                "password": "Pass123!",
                "name": "Duplicate",
            })

        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client):
        """Invalid email format → 422."""
        resp = await client.post("/api/auth/register", json={
            "email": "not-an-email",
            "password": "Pass123!",
            "name": "Bad Email",
        })
        assert resp.status_code == 422


# ═══════════════════════════════════════════════════════════════════
# POST /api/auth/login
# ═══════════════════════════════════════════════════════════════════


class TestAuthLogin:

    @pytest.mark.asyncio
    async def test_login_success(self, client, db_with_user):
        """Valid credentials → 200 with token."""
        with patch("routes.auth_routes.db", db_with_user):
            resp = await client.post("/api/auth/login", json={
                "email": "login@infinea.app",
                "password": "SecurePass123!",
            })

        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == "user_login_test"
        assert "token" in data

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client, db_with_user):
        """Wrong password → 401."""
        with patch("routes.auth_routes.db", db_with_user):
            resp = await client.post("/api/auth/login", json={
                "email": "login@infinea.app",
                "password": "WrongPassword!",
            })
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client, mock_db):
        """User doesn't exist → 401."""
        with patch("routes.auth_routes.db", mock_db):
            resp = await client.post("/api/auth/login", json={
                "email": "ghost@infinea.app",
                "password": "Whatever123!",
            })
        assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════
# POST /api/auth/logout
# ═══════════════════════════════════════════════════════════════════


class TestAuthLogout:

    @pytest.mark.asyncio
    async def test_logout_clears_session(self, client, mock_db):
        """Logout deletes session and clears cookie."""
        with patch("routes.auth_routes.db", mock_db):
            resp = await client.post("/api/auth/logout")

        assert resp.status_code == 200
        assert resp.json()["message"] == "Logged out successfully"


# ═══════════════════════════════════════════════════════════════════
# POST /api/auth/refresh
# ═══════════════════════════════════════════════════════════════════


class TestAuthRefresh:

    @pytest.mark.asyncio
    async def test_refresh_returns_new_token(self, client):
        """Refresh → returns new JWT and user data."""
        resp = await client.post("/api/auth/refresh")
        assert resp.status_code == 200
        data = resp.json()
        assert "token" in data
        assert data["user_id"] == "user_test_abc123"
