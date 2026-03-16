"""
Unit tests — Routines routes.
Tests CRUD, completion logic, streak calculation, double-completion guard, free-tier limits.
Uses mongomock-motor via conftest fixtures.
"""

import pytest
from datetime import datetime, timezone, timedelta

pytestmark = pytest.mark.asyncio


# ═══════════════════════════════════════════════════════════════
# CREATE
# ═══════════════════════════════════════════════════════════════

class TestCreateRoutine:
    async def test_create_success(self, client, mock_db):
        resp = await client.post("/api/routines", json={
            "name": "Morning Routine",
            "time_of_day": "morning",
            "frequency": "daily",
            "items": [
                {"title": "Méditation", "duration_minutes": 10},
                {"title": "Lecture", "duration_minutes": 15},
            ],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Morning Routine"
        assert data["routine_id"].startswith("rtn_")
        assert data["is_active"] is True
        assert data["total_minutes"] == 25
        assert len(data["items"]) == 2
        assert data["items"][0]["order"] == 0
        assert data["items"][1]["order"] == 1

    async def test_create_clamps_item_duration(self, client, mock_db):
        resp = await client.post("/api/routines", json={
            "name": "Test Clamp",
            "items": [{"title": "Too long", "duration_minutes": 999}],
        })
        assert resp.status_code == 200
        assert resp.json()["items"][0]["duration_minutes"] == 120  # Max 120

    async def test_free_user_limited_to_3(self, client, mock_db):
        for i in range(3):
            resp = await client.post("/api/routines", json={"name": f"R{i}", "items": []})
            assert resp.status_code == 200

        resp = await client.post("/api/routines", json={"name": "R4", "items": []})
        assert resp.status_code == 400
        assert "Limite" in resp.json()["detail"]

    async def test_premium_user_more_routines(self, premium_client, mock_db):
        for i in range(5):
            resp = await premium_client.post("/api/routines", json={"name": f"R{i}", "items": []})
            assert resp.status_code == 200

    async def test_create_with_frequency_weekdays(self, client, mock_db):
        resp = await client.post("/api/routines", json={
            "name": "Weekday",
            "frequency": "weekdays",
            "items": [],
        })
        assert resp.status_code == 200
        assert resp.json()["frequency"] == "weekdays"
        assert resp.json()["frequency_days"] == [0, 1, 2, 3, 4]


# ═══════════════════════════════════════════════════════════════
# READ
# ═══════════════════════════════════════════════════════════════

class TestListRoutines:
    async def test_list_empty(self, client, mock_db):
        resp = await client.get("/api/routines")
        assert resp.status_code == 200
        assert resp.json()["routines"] == []
        assert resp.json()["count"] == 0

    async def test_list_after_create(self, client, mock_db):
        await client.post("/api/routines", json={"name": "R1", "items": []})
        await client.post("/api/routines", json={"name": "R2", "items": []})
        resp = await client.get("/api/routines")
        assert resp.status_code == 200
        assert resp.json()["count"] == 2


class TestGetRoutine:
    async def test_get_existing(self, client, mock_db):
        create_resp = await client.post("/api/routines", json={"name": "Test", "items": []})
        rid = create_resp.json()["routine_id"]
        resp = await client.get(f"/api/routines/{rid}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Test"

    async def test_get_nonexistent(self, client, mock_db):
        resp = await client.get("/api/routines/rtn_nope")
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════
# UPDATE
# ═══════════════════════════════════════════════════════════════

class TestUpdateRoutine:
    async def test_update_name(self, client, mock_db):
        create_resp = await client.post("/api/routines", json={"name": "Old", "items": []})
        rid = create_resp.json()["routine_id"]
        resp = await client.put(f"/api/routines/{rid}", json={"name": "New"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "New"

    async def test_update_items_recalculates_total(self, client, mock_db):
        create_resp = await client.post("/api/routines", json={
            "name": "Test",
            "items": [{"title": "A", "duration_minutes": 5}],
        })
        rid = create_resp.json()["routine_id"]
        resp = await client.put(f"/api/routines/{rid}", json={
            "items": [
                {"title": "A", "duration_minutes": 10},
                {"title": "B", "duration_minutes": 20},
            ],
        })
        assert resp.status_code == 200
        assert resp.json()["total_minutes"] == 30

    async def test_update_nonexistent(self, client, mock_db):
        resp = await client.put("/api/routines/rtn_nope", json={"name": "X"})
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════
# DELETE
# ═══════════════════════════════════════════════════════════════

class TestDeleteRoutine:
    async def test_soft_delete(self, client, mock_db):
        create_resp = await client.post("/api/routines", json={"name": "Del", "items": []})
        rid = create_resp.json()["routine_id"]
        resp = await client.delete(f"/api/routines/{rid}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "deleted"

        # Should be invisible in list
        list_resp = await client.get("/api/routines")
        assert list_resp.json()["count"] == 0

        # Should 404 on direct get
        resp = await client.get(f"/api/routines/{rid}")
        assert resp.status_code == 404

    async def test_delete_nonexistent(self, client, mock_db):
        resp = await client.delete("/api/routines/rtn_nope")
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════
# COMPLETE
# ═══════════════════════════════════════════════════════════════

class TestCompleteRoutine:
    async def test_complete_success(self, client, mock_db):
        create_resp = await client.post("/api/routines", json={"name": "Daily", "items": []})
        rid = create_resp.json()["routine_id"]
        resp = await client.post(f"/api/routines/{rid}/complete")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert data["times_completed"] == 1
        assert data["streak_current"] == 1

    async def test_double_complete_same_day(self, client, mock_db):
        """Completing the same routine twice on the same day should be idempotent."""
        create_resp = await client.post("/api/routines", json={"name": "Daily", "items": []})
        rid = create_resp.json()["routine_id"]

        resp1 = await client.post(f"/api/routines/{rid}/complete")
        assert resp1.json()["status"] == "completed"

        resp2 = await client.post(f"/api/routines/{rid}/complete")
        assert resp2.json()["status"] == "already_completed"
        assert resp2.json()["times_completed"] == 1  # Not incremented

    async def test_complete_nonexistent(self, client, mock_db):
        resp = await client.post("/api/routines/rtn_nope/complete")
        assert resp.status_code == 404

    async def test_streak_consecutive_days(self, mock_db):
        """Streak should increment when completing on consecutive days."""
        from tests.conftest import TEST_USER
        rid = "rtn_streak_test"
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1))
        yesterday_str = yesterday.strftime("%Y-%m-%d")

        await mock_db.routines.insert_one({
            "routine_id": rid,
            "user_id": TEST_USER["user_id"],
            "name": "Streak Test",
            "items": [],
            "is_active": True,
            "total_minutes": 0,
            "times_completed": 1,
            "streak_current": 1,
            "streak_best": 1,
            "completion_log": [{"date": yesterday_str, "completed_at": yesterday.isoformat()}],
            "last_completed_at": yesterday.isoformat(),
            "created_at": yesterday.isoformat(),
            "updated_at": yesterday.isoformat(),
        })

        # Import app with patched DB to make the request
        from unittest.mock import patch
        from mongomock_motor import AsyncMongoMockClient
        from httpx import AsyncClient, ASGITransport

        with patch("database.db", mock_db), patch("database.client", AsyncMongoMockClient()):
            from server import app
            from auth import get_current_user

            async def mock_auth():
                return TEST_USER.copy()
            app.dependency_overrides[get_current_user] = mock_auth

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.post(f"/api/routines/{rid}/complete")

            app.dependency_overrides.clear()

        assert resp.status_code == 200
        assert resp.json()["streak_current"] == 2
