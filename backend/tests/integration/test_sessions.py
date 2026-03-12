"""
Integration tests — Session routes.
P3: ensures session start, complete, and stats flows work.

Tests:
- POST /api/sessions/start
- POST /api/sessions/complete
- GET /api/stats
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, AsyncMock


# ═══════════════════════════════════════════════════════════════════
# POST /api/sessions/start
# ═══════════════════════════════════════════════════════════════════


class TestSessionStart:

    @pytest.fixture
    async def db_with_action(self, mock_db):
        """Seed a micro-action for session start."""
        await mock_db.micro_actions.insert_one({
            "action_id": "action_test_001",
            "title": "Apprendre 5 mots",
            "description": "Flashcards de vocabulaire",
            "category": "learning",
            "duration_min": 5,
            "duration_max": 10,
            "energy_level": "medium",
            "instructions": ["Ouvre l'app", "Mémorise"],
            "is_premium": False,
            "icon": "book",
        })
        return mock_db

    @pytest.mark.asyncio
    async def test_start_session_success(self, client, db_with_action):
        """Start a session with valid action → 200."""
        with patch("routes.sessions.db", db_with_action), \
             patch("routes.sessions.track_event", new_callable=AsyncMock), \
             patch("routes.sessions.record_signal", new_callable=AsyncMock):
            resp = await client.post("/api/sessions/start", json={
                "action_id": "action_test_001",
            })

        assert resp.status_code == 200
        data = resp.json()
        assert "session_id" in data
        assert data["session_id"].startswith("session_")
        assert data["action"]["title"] == "Apprendre 5 mots"
        assert "started_at" in data

    @pytest.mark.asyncio
    async def test_start_session_action_not_found(self, client, mock_db):
        """Start with nonexistent action → 404."""
        with patch("routes.sessions.db", mock_db), \
             patch("routes.sessions.track_event", new_callable=AsyncMock), \
             patch("routes.sessions.record_signal", new_callable=AsyncMock):
            resp = await client.post("/api/sessions/start", json={
                "action_id": "nonexistent_action",
            })

        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_start_premium_action_free_user(self, client, mock_db):
        """Free user starting premium action → 403."""
        await mock_db.micro_actions.insert_one({
            "action_id": "premium_action",
            "title": "Premium Focus",
            "description": "Deep focus session",
            "category": "mindfulness",
            "duration_min": 10,
            "duration_max": 15,
            "energy_level": "low",
            "instructions": ["Breathe"],
            "is_premium": True,
            "icon": "brain",
        })

        with patch("routes.sessions.db", mock_db), \
             patch("routes.sessions.track_event", new_callable=AsyncMock), \
             patch("routes.sessions.record_signal", new_callable=AsyncMock):
            resp = await client.post("/api/sessions/start", json={
                "action_id": "premium_action",
            })

        assert resp.status_code == 403


# ═══════════════════════════════════════════════════════════════════
# POST /api/sessions/complete
# ═══════════════════════════════════════════════════════════════════


class TestSessionComplete:

    @pytest.fixture
    async def db_with_session(self, mock_db):
        """Seed an active session + user for completion."""
        await mock_db.user_sessions_history.insert_one({
            "session_id": "sess_active_001",
            "user_id": "user_test_abc123",
            "action_id": "action_test_001",
            "action_title": "Apprendre 5 mots",
            "category": "learning",
            "started_at": (datetime.now(timezone.utc) - timedelta(minutes=7)).isoformat(),
            "completed_at": None,
            "actual_duration": None,
            "completed": False,
        })
        await mock_db.users.insert_one({
            "user_id": "user_test_abc123",
            "email": "test@infinea.app",
            "name": "Test User",
            "subscription_tier": "free",
            "total_time_invested": 100,
            "streak_days": 3,
            "last_session_date": (datetime.now(timezone.utc) - timedelta(days=1)).date().isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        return mock_db

    @pytest.mark.asyncio
    async def test_complete_session_success(self, client, db_with_session):
        """Complete a session → 200 with stats."""
        with patch("routes.sessions.db", db_with_session), \
             patch("routes.sessions.track_event", new_callable=AsyncMock), \
             patch("routes.sessions.record_signal", new_callable=AsyncMock), \
             patch("routes.sessions.send_push_to_user", new_callable=AsyncMock), \
             patch("routes.sessions._auto_sync_session", new_callable=AsyncMock):
            resp = await client.post("/api/sessions/complete", json={
                "session_id": "sess_active_001",
                "actual_duration": 7,
                "completed": True,
            })

        assert resp.status_code == 200
        data = resp.json()
        assert "total_time" in data
        assert "new_streak" in data
        assert data["time_added"] == 7

    @pytest.mark.asyncio
    async def test_complete_nonexistent_session(self, client, mock_db):
        """Complete nonexistent session → 404."""
        with patch("routes.sessions.db", mock_db), \
             patch("routes.sessions.track_event", new_callable=AsyncMock), \
             patch("routes.sessions.record_signal", new_callable=AsyncMock):
            resp = await client.post("/api/sessions/complete", json={
                "session_id": "nonexistent_session",
                "actual_duration": 5,
                "completed": True,
            })

        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════════
# GET /api/stats
# ═══════════════════════════════════════════════════════════════════


class TestStats:

    @pytest.mark.asyncio
    async def test_stats_empty_user(self, client, mock_db):
        """User with no sessions → default stats."""
        await mock_db.users.insert_one({
            "user_id": "user_test_abc123",
            "total_time_invested": 0,
            "streak_days": 0,
        })

        with patch("routes.sessions.db", mock_db):
            resp = await client.get("/api/stats")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total_sessions"] == 0
        assert "total_time_invested" in data
        assert "streak_days" in data
        assert "sessions_by_category" in data

    @pytest.mark.asyncio
    async def test_stats_with_sessions(self, client, mock_db):
        """User with sessions → computed stats."""
        await mock_db.users.insert_one({
            "user_id": "user_test_abc123",
            "total_time_invested": 42,
            "streak_days": 5,
        })
        await mock_db.user_sessions_history.insert_many([
            {
                "user_id": "user_test_abc123",
                "session_id": "s1",
                "category": "learning",
                "completed": True,
                "actual_duration": 7,
                "started_at": datetime.now(timezone.utc).isoformat(),
            },
            {
                "user_id": "user_test_abc123",
                "session_id": "s2",
                "category": "productivity",
                "completed": True,
                "actual_duration": 5,
                "started_at": datetime.now(timezone.utc).isoformat(),
            },
        ])

        with patch("routes.sessions.db", mock_db):
            resp = await client.get("/api/stats")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total_sessions"] == 2
        assert "learning" in data["sessions_by_category"]
