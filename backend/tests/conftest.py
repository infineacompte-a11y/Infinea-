"""
InFinea — Test fixtures.
Central conftest: mock DB, mock auth, async client, test user.

Architecture:
- mongomock-motor replaces real MongoDB (full async compat)
- get_current_user is overridden to return a test user
- Rate limiter is disabled in tests
- Environment variables are set before any app import
"""

import os

# ── Set test env BEFORE any app import ──
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-pytest")
os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017/infinea_test")
os.environ.setdefault("DB_NAME", "infinea_test")
os.environ.setdefault("VAPID_PUBLIC_KEY", "")
os.environ.setdefault("VAPID_PRIVATE_KEY", "")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_test")
os.environ.setdefault("ANTHROPIC_API_KEY", "")

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from mongomock_motor import AsyncMongoMockClient
from httpx import AsyncClient, ASGITransport


# ── Test Data ──

TEST_USER = {
    "user_id": "user_test_abc123",
    "email": "test@infinea.app",
    "name": "Test User",
    "picture": None,
    "subscription_tier": "free",
    "total_time_invested": 120,
    "streak_days": 5,
    "last_session_date": None,
    "created_at": datetime.now(timezone.utc).isoformat(),
}

TEST_USER_PREMIUM = {
    **TEST_USER,
    "user_id": "user_test_premium",
    "email": "premium@infinea.app",
    "name": "Premium User",
    "subscription_tier": "premium",
}


# ── Database Fixture ──
# Single shared mock client so route modules' `from database import db`
# binding always points to the same object. Collections are dropped
# between tests to guarantee isolation.

_mock_client = AsyncMongoMockClient()
_mock_db = _mock_client["infinea_test"]


@pytest.fixture
async def mock_db():
    """Shared mongomock-motor database, cleaned between tests."""
    for name in await _mock_db.list_collection_names():
        await _mock_db.drop_collection(name)
    yield _mock_db


@pytest.fixture
async def mock_db_with_user(mock_db):
    """Database pre-seeded with a test user."""
    await mock_db.users.insert_one({**TEST_USER, "_id": None})
    yield mock_db


# ── App & Client Fixture ──

@pytest.fixture
async def app(mock_db):
    """FastAPI app with mocked DB, disabled limiter, overridden auth."""
    with patch("database.db", mock_db), \
         patch("database.client", _mock_client):

        # Re-import to pick up patched db
        from server import app as _app
        from auth import get_current_user
        from config import limiter

        # Disable rate limiter in tests
        limiter.enabled = False

        # Override auth dependency → always return test user
        async def mock_auth():
            return TEST_USER.copy()

        _app.dependency_overrides[get_current_user] = mock_auth

        yield _app

        # Cleanup
        _app.dependency_overrides.clear()


@pytest.fixture
async def client(app):
    """Async HTTP client for route testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def premium_client(app):
    """Client authenticated as premium user."""
    from auth import get_current_user

    async def mock_premium_auth():
        return TEST_USER_PREMIUM.copy()

    app.dependency_overrides[get_current_user] = mock_premium_auth

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ── Auth Helpers ──

@pytest.fixture
def test_token():
    """Valid JWT token for test user."""
    from auth import create_token
    return create_token(TEST_USER["user_id"])


@pytest.fixture
def premium_token():
    """Valid JWT token for premium test user."""
    from auth import create_token
    return create_token(TEST_USER_PREMIUM["user_id"])


# ── Sample Data Factories ──

@pytest.fixture
def sample_action():
    """A sample micro-action document."""
    return {
        "action_id": "action_test_001",
        "title": "Apprendre 5 mots de vocabulaire",
        "description": "Mémorise 5 nouveaux mots avec la technique des flashcards",
        "category": "learning",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": ["Ouvre l'app", "Choisis un thème", "Mémorise 5 mots"],
        "is_premium": False,
        "icon": "book",
    }


@pytest.fixture
def sample_objective():
    """A sample objective document."""
    return {
        "objective_id": "obj_test_001",
        "user_id": TEST_USER["user_id"],
        "title": "Apprendre le thaï",
        "description": "Maîtriser les bases du thaï en 30 jours",
        "target_duration_days": 30,
        "daily_minutes": 10,
        "category": "learning",
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "curriculum": [],
        "stats": {
            "total_steps_completed": 0,
            "total_time_invested": 0,
            "current_streak": 0,
        },
    }


@pytest.fixture
def sample_session():
    """A sample session history document."""
    return {
        "session_id": "sess_test_001",
        "user_id": TEST_USER["user_id"],
        "action_id": "action_test_001",
        "action_title": "Apprendre 5 mots de vocabulaire",
        "action_category": "learning",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "actual_duration": 7,
        "completed": True,
        "notes": None,
    }
