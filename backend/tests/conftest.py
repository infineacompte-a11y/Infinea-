"""
InFinea — Test infrastructure.
Isolated async test client, per-test database, reusable fixtures.
"""

import os
import uuid

# Set test environment BEFORE any app imports
os.environ["MONGO_URL"] = "mongodb://localhost:27017"
os.environ["DB_NAME"] = f"infinea_test_{uuid.uuid4().hex[:8]}"
os.environ["JWT_SECRET"] = "test-secret-key-not-for-production"
os.environ["ENVIRONMENT"] = "test"

import pytest
from httpx import AsyncClient, ASGITransport

from database import client, db
from auth import create_token, hash_password


# ---------- App ----------

@pytest.fixture(scope="session")
def app():
    """FastAPI app instance, created once per test session."""
    from server import app as _app
    return _app


# ---------- Database lifecycle ----------

@pytest.fixture(autouse=True)
async def clean_db():
    """Drop all collections before each test — full isolation."""
    collections = await db.list_collection_names()
    for col in collections:
        await db[col].delete_many({})
    yield
    # Post-test cleanup handled by drop_test_db


@pytest.fixture(scope="session", autouse=True)
async def drop_test_db():
    """Drop entire test database after all tests complete."""
    yield
    await client.drop_database(db.name)
    client.close()


# ---------- HTTP Client ----------

@pytest.fixture
async def client_unauthenticated(app):
    """Async HTTP client without auth — for public endpoints and auth flows."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
async def test_user():
    """Create and return a test user in the database."""
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    user_doc = {
        "user_id": user_id,
        "email": f"{user_id}@test.infinea.app",
        "name": "Test User",
        "password": hash_password("TestPassword123!"),
        "subscription_tier": "free",
        "streak_days": 0,
        "total_time_invested": 0,
        "badges": [],
        "created_at": "2025-01-01T00:00:00+00:00",
    }
    await db.users.insert_one(user_doc)
    # Return without _id (matches API behavior)
    user_doc.pop("_id", None)
    return user_doc


@pytest.fixture
async def auth_token(test_user):
    """JWT token for the test user."""
    return create_token(test_user["user_id"])


@pytest.fixture
async def client_authenticated(app, auth_token):
    """Async HTTP client with Bearer auth — for protected endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": f"Bearer {auth_token}"},
    ) as c:
        yield c


# ---------- Premium user ----------

@pytest.fixture
async def premium_user():
    """Create a premium-tier test user."""
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    user_doc = {
        "user_id": user_id,
        "email": f"{user_id}@test.infinea.app",
        "name": "Premium User",
        "password": hash_password("PremiumPass123!"),
        "subscription_tier": "premium",
        "streak_days": 5,
        "total_time_invested": 120,
        "badges": [],
        "created_at": "2025-01-01T00:00:00+00:00",
    }
    await db.users.insert_one(user_doc)
    user_doc.pop("_id", None)
    return user_doc


@pytest.fixture
async def client_premium(app, premium_user):
    """Authenticated client for a premium user."""
    token = create_token(premium_user["user_id"])
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as c:
        yield c


# ---------- B2B fixtures ----------

@pytest.fixture
async def company_admin(test_user):
    """Upgrade test user to company admin."""
    company_id = f"company_{uuid.uuid4().hex[:12]}"
    company_doc = {
        "company_id": company_id,
        "name": "Test Corp",
        "domain": "test.infinea.app",
        "admin_user_id": test_user["user_id"],
        "employees": [test_user["user_id"]],
        "employee_count": 1,
        "created_at": "2025-01-01T00:00:00+00:00",
    }
    await db.companies.insert_one(company_doc)

    await db.users.update_one(
        {"user_id": test_user["user_id"]},
        {"$set": {"company_id": company_id, "is_company_admin": True}},
    )

    test_user["company_id"] = company_id
    test_user["is_company_admin"] = True
    return test_user


# ---------- Seed actions helper ----------

@pytest.fixture
async def seeded_actions():
    """Insert a small set of micro-actions for testing."""
    actions = [
        {
            "action_id": "action_test_1",
            "title": "Test Action Low",
            "description": "A test action",
            "category": "learning",
            "duration_min": 2,
            "duration_max": 5,
            "energy_level": "low",
            "instructions": ["Step 1", "Step 2"],
            "is_premium": False,
            "icon": "book-open",
        },
        {
            "action_id": "action_test_2",
            "title": "Test Action Medium",
            "description": "Another test action",
            "category": "productivity",
            "duration_min": 5,
            "duration_max": 10,
            "energy_level": "medium",
            "instructions": ["Step 1"],
            "is_premium": False,
            "icon": "zap",
        },
        {
            "action_id": "action_test_premium",
            "title": "Premium Action",
            "description": "Premium only",
            "category": "well_being",
            "duration_min": 5,
            "duration_max": 10,
            "energy_level": "high",
            "instructions": ["Step 1"],
            "is_premium": True,
            "icon": "star",
        },
    ]
    await db.micro_actions.insert_many(actions)
    return actions
