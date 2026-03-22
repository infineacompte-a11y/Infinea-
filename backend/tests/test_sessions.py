"""Tests for session tracking — start, complete, stats, streaks."""

from database import db


class TestStartSession:
    async def test_start_session(self, client_authenticated, seeded_actions):
        resp = await client_authenticated.post(
            "/api/sessions/start",
            json={"action_id": "action_test_1", "planned_duration": 5},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "session_id" in data
        assert data["action_id"] == "action_test_1"

    async def test_start_session_unauthenticated(self, client_unauthenticated):
        resp = await client_unauthenticated.post(
            "/api/sessions/start",
            json={"action_id": "action_test_1", "planned_duration": 5},
        )
        assert resp.status_code == 401


class TestCompleteSession:
    async def test_complete_session(self, client_authenticated, test_user, seeded_actions):
        # Start a session
        start = await client_authenticated.post(
            "/api/sessions/start",
            json={"action_id": "action_test_1", "planned_duration": 5},
        )
        session_id = start.json()["session_id"]

        # Complete it
        resp = await client_authenticated.post(
            "/api/sessions/complete",
            json={
                "session_id": session_id,
                "actual_duration": 4,
                "feedback": "great",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["completed"] is True

    async def test_complete_nonexistent_session(self, client_authenticated):
        resp = await client_authenticated.post(
            "/api/sessions/complete",
            json={
                "session_id": "fake_session_id",
                "actual_duration": 5,
            },
        )
        assert resp.status_code == 404


class TestUserStats:
    async def test_get_stats_empty(self, client_authenticated):
        resp = await client_authenticated.get("/api/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_sessions"] == 0

    async def test_stats_after_session(self, client_authenticated, seeded_actions):
        # Start and complete a session
        start = await client_authenticated.post(
            "/api/sessions/start",
            json={"action_id": "action_test_1", "planned_duration": 5},
        )
        session_id = start.json()["session_id"]
        await client_authenticated.post(
            "/api/sessions/complete",
            json={"session_id": session_id, "actual_duration": 5},
        )

        resp = await client_authenticated.get("/api/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_sessions"] >= 1
