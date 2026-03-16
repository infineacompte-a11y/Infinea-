"""
Unit tests — Objectives routes.
Tests CRUD, free-tier limits, step completion, streak logic, deletion.
Uses mongomock-motor via conftest fixtures.
"""

import pytest
from datetime import datetime, timezone, timedelta

pytestmark = pytest.mark.asyncio


# ═══════════════════════════════════════════════════════════════
# CREATE
# ═══════════════════════════════════════════════════════════════

class TestCreateObjective:
    async def test_create_objective_success(self, client, mock_db):
        resp = await client.post("/api/objectives", json={
            "title": "Apprendre le thaï",
            "target_duration_days": 30,
            "daily_minutes": 10,
            "category": "learning",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Apprendre le thaï"
        assert data["status"] == "active"
        assert data["objective_id"].startswith("obj_")
        assert data["target_duration_days"] == 30
        assert data["daily_minutes"] == 10
        assert data["current_day"] == 0
        assert data["total_sessions"] == 0

    async def test_create_objective_clamps_values(self, client, mock_db):
        resp = await client.post("/api/objectives", json={
            "title": "Test clamp",
            "target_duration_days": 1,  # Below min 7
            "daily_minutes": 120,       # Above max 60
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["target_duration_days"] == 7
        assert data["daily_minutes"] == 60

    async def test_create_objective_strips_whitespace(self, client, mock_db):
        resp = await client.post("/api/objectives", json={
            "title": "  Padded Title  ",
        })
        assert resp.status_code == 200
        assert resp.json()["title"] == "Padded Title"

    async def test_free_user_limited_to_2_objectives(self, client, mock_db):
        # Create 2 objectives (should succeed)
        for i in range(2):
            resp = await client.post("/api/objectives", json={"title": f"Obj {i}"})
            assert resp.status_code == 200

        # 3rd should fail
        resp = await client.post("/api/objectives", json={"title": "Obj 3"})
        assert resp.status_code == 400
        assert "Limite" in resp.json()["detail"]

    async def test_premium_user_can_create_more(self, premium_client, mock_db):
        for i in range(5):
            resp = await premium_client.post("/api/objectives", json={"title": f"Obj {i}"})
            assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════
# READ
# ═══════════════════════════════════════════════════════════════

class TestListObjectives:
    async def test_list_empty(self, client, mock_db):
        resp = await client.get("/api/objectives")
        assert resp.status_code == 200
        assert resp.json()["objectives"] == []

    async def test_list_after_create(self, client, mock_db):
        await client.post("/api/objectives", json={"title": "Obj A"})
        await client.post("/api/objectives", json={"title": "Obj B"})
        resp = await client.get("/api/objectives")
        assert resp.status_code == 200
        assert len(resp.json()["objectives"]) == 2

    async def test_filter_by_status(self, client, mock_db):
        await client.post("/api/objectives", json={"title": "Active"})
        resp = await client.get("/api/objectives?status=completed")
        assert resp.status_code == 200
        assert len(resp.json()["objectives"]) == 0


class TestGetObjective:
    async def test_get_existing(self, client, mock_db):
        create_resp = await client.post("/api/objectives", json={"title": "Test Get"})
        obj_id = create_resp.json()["objective_id"]
        resp = await client.get(f"/api/objectives/{obj_id}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "Test Get"

    async def test_get_nonexistent(self, client, mock_db):
        resp = await client.get("/api/objectives/obj_doesnotexist")
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════
# UPDATE
# ═══════════════════════════════════════════════════════════════

class TestUpdateObjective:
    async def test_update_title(self, client, mock_db):
        create_resp = await client.post("/api/objectives", json={"title": "Original"})
        obj_id = create_resp.json()["objective_id"]
        resp = await client.put(f"/api/objectives/{obj_id}", json={"title": "Updated"})
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated"

    async def test_update_status_to_completed(self, client, mock_db):
        create_resp = await client.post("/api/objectives", json={"title": "To Complete"})
        obj_id = create_resp.json()["objective_id"]
        resp = await client.put(f"/api/objectives/{obj_id}", json={"status": "completed"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"
        assert "completed_at" in resp.json()

    async def test_update_invalid_status(self, client, mock_db):
        create_resp = await client.post("/api/objectives", json={"title": "Test"})
        obj_id = create_resp.json()["objective_id"]
        resp = await client.put(f"/api/objectives/{obj_id}", json={"status": "invalid"})
        assert resp.status_code == 400

    async def test_update_nonexistent(self, client, mock_db):
        resp = await client.put("/api/objectives/obj_nope", json={"title": "X"})
        assert resp.status_code == 404

    async def test_update_empty_body(self, client, mock_db):
        create_resp = await client.post("/api/objectives", json={"title": "Test"})
        obj_id = create_resp.json()["objective_id"]
        resp = await client.put(f"/api/objectives/{obj_id}", json={})
        assert resp.status_code == 400


# ═══════════════════════════════════════════════════════════════
# DELETE
# ═══════════════════════════════════════════════════════════════

class TestDeleteObjective:
    async def test_delete_success(self, client, mock_db):
        create_resp = await client.post("/api/objectives", json={"title": "To Delete"})
        obj_id = create_resp.json()["objective_id"]
        resp = await client.delete(f"/api/objectives/{obj_id}")
        assert resp.status_code == 200
        assert resp.json()["deleted"] is True

        # Verify it's gone
        resp = await client.get(f"/api/objectives/{obj_id}")
        assert resp.status_code == 404

    async def test_delete_nonexistent(self, client, mock_db):
        resp = await client.delete("/api/objectives/obj_nope")
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════
# COMPLETE STEP
# ═══════════════════════════════════════════════════════════════

class TestCompleteStep:
    async def _create_obj_with_curriculum(self, mock_db):
        """Helper: insert objective with a 3-step curriculum directly in DB."""
        from tests.conftest import TEST_USER
        obj_id = "obj_test_steps"
        await mock_db.objectives.insert_one({
            "objective_id": obj_id,
            "user_id": TEST_USER["user_id"],
            "title": "Test Steps",
            "status": "active",
            "target_duration_days": 30,
            "daily_minutes": 10,
            "category": "learning",
            "current_day": 0,
            "total_sessions": 0,
            "total_minutes": 0,
            "streak_days": 0,
            "last_session_date": None,
            "progress_log": [],
            "curriculum": [
                {"title": "Step 1", "day": 1, "completed": False, "focus": "bases", "difficulty": 1, "duration_min": 5, "duration_max": 15},
                {"title": "Step 2", "day": 2, "completed": False, "focus": "grammaire", "difficulty": 2, "duration_min": 5, "duration_max": 15},
                {"title": "Step 3", "day": 3, "completed": False, "focus": "vocabulaire", "difficulty": 3, "duration_min": 5, "duration_max": 15},
            ],
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        return obj_id

    async def test_complete_first_step(self, client, mock_db):
        obj_id = await self._create_obj_with_curriculum(mock_db)
        resp = await client.post(f"/api/objectives/{obj_id}/complete-step", json={
            "step_index": 0,
            "actual_duration": 8,
            "notes": "Bien compris les bases",
            "completed": True,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["day"] == 1
        assert data["streak"] == 1
        assert data["completed_steps"] == 1
        assert data["total_steps"] == 3
        assert data["is_finished"] is False

    async def test_complete_invalid_step_index(self, client, mock_db):
        obj_id = await self._create_obj_with_curriculum(mock_db)
        resp = await client.post(f"/api/objectives/{obj_id}/complete-step", json={
            "step_index": 99,
            "actual_duration": 5,
        })
        assert resp.status_code == 400

    async def test_complete_nonexistent_objective(self, client, mock_db):
        resp = await client.post("/api/objectives/obj_nope/complete-step", json={
            "step_index": 0,
            "actual_duration": 5,
        })
        assert resp.status_code == 404

    async def test_performance_fast(self, client, mock_db):
        """Completing much faster than expected → performance='fast'."""
        obj_id = await self._create_obj_with_curriculum(mock_db)
        resp = await client.post(f"/api/objectives/{obj_id}/complete-step", json={
            "step_index": 0,
            "actual_duration": 2,  # < 5 * 0.8 = 4
            "completed": True,
        })
        assert resp.status_code == 200
        assert resp.json()["performance"] == "fast"

    async def test_performance_abandoned(self, client, mock_db):
        obj_id = await self._create_obj_with_curriculum(mock_db)
        resp = await client.post(f"/api/objectives/{obj_id}/complete-step", json={
            "step_index": 0,
            "actual_duration": 3,
            "completed": False,
        })
        assert resp.status_code == 200
        assert resp.json()["performance"] == "abandoned"
