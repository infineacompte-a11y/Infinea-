"""
Integration tests — Micro-Instants API routes.
P1: ensures micro-instant detection, exploitation, and stats work end-to-end.

Tests:
- GET  /api/micro-instants/today
- POST /api/micro-instants/{id}/exploit
- POST /api/micro-instants/{id}/skip
- GET  /api/micro-instants/stats
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, AsyncMock


# ═══════════════════════════════════════════════════════════════════
# GET /api/micro-instants/today
# ═══════════════════════════════════════════════════════════════════


class TestMicroInstantsToday:

    @pytest.mark.asyncio
    async def test_today_no_data(self, client, mock_db):
        """No routines, no patterns → empty or minimal instants."""
        with patch("routes.micro_instants.db", mock_db):
            resp = await client.get("/api/micro-instants/today")

        assert resp.status_code == 200
        data = resp.json()
        assert "instants" in data
        assert "total" in data
        assert "sources" in data
        assert isinstance(data["instants"], list)

    @pytest.mark.asyncio
    async def test_today_with_routine(self, client, mock_db):
        """Active routine generates a window."""
        await mock_db.routines.insert_one({
            "user_id": "user_test_abc123",
            "routine_id": "rtn_test_001",
            "name": "Routine du soir",
            "time_of_day": "evening",
            "frequency": "daily",
            "frequency_days": None,
            "is_active": True,
            "total_minutes": 10,
            "last_completed_at": None,
        })

        with patch("routes.micro_instants.db", mock_db):
            resp = await client.get("/api/micro-instants/today")

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["instants"], list)

    @pytest.mark.asyncio
    async def test_today_returns_date(self, client, mock_db):
        """Response includes today's date."""
        with patch("routes.micro_instants.db", mock_db):
            resp = await client.get("/api/micro-instants/today")

        data = resp.json()
        assert "date" in data
        today = datetime.now(timezone.utc).date().isoformat()
        assert data["date"] == today


# ═══════════════════════════════════════════════════════════════════
# POST /api/micro-instants/{id}/exploit
# ═══════════════════════════════════════════════════════════════════


class TestExploitInstant:

    @pytest.fixture
    async def db_with_action(self, mock_db):
        """Seed a micro-action for exploitation."""
        await mock_db.micro_actions.insert_one({
            "action_id": "action_exploit_001",
            "title": "Apprendre 5 mots",
            "description": "Flashcards vocabulaire",
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
    async def test_exploit_success(self, client, db_with_action):
        """Exploit a micro-instant with valid action."""
        with patch("routes.micro_instants.db", db_with_action):
            resp = await client.post("/api/micro-instants/mi_test123/exploit", json={
                "action_id": "action_exploit_001",
            })

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "exploited"
        assert data["instant_id"] == "mi_test123"
        assert data["action"]["title"] == "Apprendre 5 mots"

    @pytest.mark.asyncio
    async def test_exploit_action_not_found(self, client, mock_db):
        """Exploit with nonexistent action → 404."""
        with patch("routes.micro_instants.db", mock_db):
            resp = await client.post("/api/micro-instants/mi_test/exploit", json={
                "action_id": "nonexistent_action",
            })

        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_exploit_premium_blocked_for_free(self, client, mock_db):
        """Free user exploiting premium action → 403."""
        await mock_db.micro_actions.insert_one({
            "action_id": "premium_action",
            "title": "Premium Focus",
            "category": "mindfulness",
            "duration_min": 10,
            "duration_max": 15,
            "energy_level": "low",
            "instructions": ["Breathe"],
            "is_premium": True,
            "icon": "brain",
        })

        with patch("routes.micro_instants.db", mock_db):
            resp = await client.post("/api/micro-instants/mi_test/exploit", json={
                "action_id": "premium_action",
            })

        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_exploit_records_outcome(self, client, db_with_action):
        """Exploitation creates an outcome record."""
        with patch("routes.micro_instants.db", db_with_action):
            await client.post("/api/micro-instants/mi_outcome_test/exploit", json={
                "action_id": "action_exploit_001",
            })

        outcome = await db_with_action.micro_instant_outcomes.find_one({
            "instant_id": "mi_outcome_test",
        })
        assert outcome is not None
        assert outcome["outcome"] == "exploited"


# ═══════════════════════════════════════════════════════════════════
# POST /api/micro-instants/{id}/skip
# ═══════════════════════════════════════════════════════════════════


class TestSkipInstant:

    @pytest.mark.asyncio
    async def test_skip_success(self, client, mock_db):
        """Skip a micro-instant with reason."""
        with patch("routes.micro_instants.db", mock_db):
            resp = await client.post("/api/micro-instants/mi_skip_test/skip", json={
                "reason": "busy",
            })

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "skipped"
        assert data["instant_id"] == "mi_skip_test"

    @pytest.mark.asyncio
    async def test_skip_without_reason(self, client, mock_db):
        """Skip without reason is valid."""
        with patch("routes.micro_instants.db", mock_db):
            resp = await client.post("/api/micro-instants/mi_skip2/skip", json={})

        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_skip_records_outcome(self, client, mock_db):
        """Skip creates an outcome record."""
        with patch("routes.micro_instants.db", mock_db):
            await client.post("/api/micro-instants/mi_skip_record/skip", json={
                "reason": "not_interested",
            })

        outcome = await mock_db.micro_instant_outcomes.find_one({
            "instant_id": "mi_skip_record",
        })
        assert outcome is not None
        assert outcome["outcome"] == "skipped"


# ═══════════════════════════════════════════════════════════════════
# GET /api/micro-instants/stats
# ═══════════════════════════════════════════════════════════════════


class TestMicroInstantStats:

    @pytest.mark.asyncio
    async def test_stats_empty(self, client, mock_db):
        """No outcomes → zero stats."""
        with patch("routes.micro_instants.db", mock_db):
            resp = await client.get("/api/micro-instants/stats")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total_instants"] == 0
        assert data["exploitation_rate"] == 0.0
        assert data["exploited"] == 0

    @pytest.mark.asyncio
    async def test_stats_with_data(self, client, mock_db):
        """Stats computed from outcome data."""
        now = datetime.now(timezone.utc)
        outcomes = [
            {"user_id": "user_test_abc123", "instant_id": "mi_1", "outcome": "exploited",
             "recorded_at": (now - timedelta(days=1)).isoformat(), "duration": 7},
            {"user_id": "user_test_abc123", "instant_id": "mi_2", "outcome": "exploited",
             "recorded_at": (now - timedelta(days=2)).isoformat(), "duration": 5},
            {"user_id": "user_test_abc123", "instant_id": "mi_3", "outcome": "skipped",
             "recorded_at": (now - timedelta(days=3)).isoformat()},
        ]
        await mock_db.micro_instant_outcomes.insert_many(outcomes)

        with patch("routes.micro_instants.db", mock_db):
            resp = await client.get("/api/micro-instants/stats")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total_instants"] == 3
        assert data["exploited"] == 2
        assert data["skipped"] == 1
        # 2/3 = 0.667
        assert abs(data["exploitation_rate"] - 0.667) < 0.01

    @pytest.mark.asyncio
    async def test_stats_has_required_fields(self, client, mock_db):
        """Stats response has all required fields."""
        with patch("routes.micro_instants.db", mock_db):
            resp = await client.get("/api/micro-instants/stats")

        data = resp.json()
        required = [
            "period_days", "total_instants", "exploited", "skipped",
            "dismissed", "exploitation_rate", "total_minutes_invested",
            "weekly_trend", "this_week_rate", "last_week_rate",
        ]
        for key in required:
            assert key in data, f"Missing key: {key}"
