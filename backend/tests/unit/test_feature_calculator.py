"""
Unit tests — Feature Calculator.
P1 critical service: ensures user behavioral features are computed correctly.

Tests:
- _time_of_day_bucket: all 4 buckets + edge cases
- _median: empty, odd, even, single value
- _compute_engagement_features: CTR, abandonment, trend, momentum, fatigue
- compute_user_features: full feature computation
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from services.feature_calculator import (
    _time_of_day_bucket,
    _median,
    _compute_engagement_features,
    compute_user_features,
)


def _naive_utcnow():
    """Return naive UTC datetime (matches mongomock behavior)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ═══════════════════════════════════════════════════════════════════
# _time_of_day_bucket — Pure function
# ═══════════════════════════════════════════════════════════════════


class TestTimeOfDayBucket:

    def test_morning(self):
        assert _time_of_day_bucket("2025-01-01T08:30:00") == "morning"

    def test_afternoon(self):
        assert _time_of_day_bucket("2025-01-01T14:00:00") == "afternoon"

    def test_evening(self):
        assert _time_of_day_bucket("2025-01-01T20:00:00") == "evening"

    def test_night(self):
        assert _time_of_day_bucket("2025-01-01T03:00:00") == "night"

    def test_boundary_morning_6am(self):
        assert _time_of_day_bucket("2025-01-01T06:00:00") == "morning"

    def test_boundary_afternoon_12pm(self):
        assert _time_of_day_bucket("2025-01-01T12:00:00") == "afternoon"

    def test_boundary_evening_18pm(self):
        assert _time_of_day_bucket("2025-01-01T18:00:00") == "evening"

    def test_boundary_night_midnight(self):
        assert _time_of_day_bucket("2025-01-01T00:00:00") == "night"

    def test_boundary_5_59am_is_night(self):
        assert _time_of_day_bucket("2025-01-01T05:59:00") == "night"

    def test_invalid_timestamp(self):
        """Invalid timestamp → default 'afternoon'."""
        assert _time_of_day_bucket("not-a-date") == "afternoon"

    def test_empty_string(self):
        assert _time_of_day_bucket("") == "afternoon"

    def test_none(self):
        assert _time_of_day_bucket(None) == "afternoon"


# ═══════════════════════════════════════════════════════════════════
# _median — Pure function
# ═══════════════════════════════════════════════════════════════════


class TestMedian:

    def test_empty_list(self):
        """Empty list → default 5.0."""
        assert _median([]) == 5.0

    def test_single_value(self):
        assert _median([7]) == 7

    def test_odd_count(self):
        assert _median([1, 3, 5]) == 3

    def test_even_count(self):
        assert _median([1, 3, 5, 7]) == 4.0

    def test_unsorted_input(self):
        """Handles unsorted input."""
        assert _median([5, 1, 3]) == 3

    def test_duplicate_values(self):
        assert _median([5, 5, 5]) == 5

    def test_two_values(self):
        assert _median([2, 8]) == 5.0


# ═══════════════════════════════════════════════════════════════════
# _compute_engagement_features — DB-dependent
# ═══════════════════════════════════════════════════════════════════


class TestComputeEngagementFeatures:

    @pytest.mark.asyncio
    async def test_no_events_returns_defaults(self, mock_db):
        """No events → all zeros."""
        result = await _compute_engagement_features(mock_db, "user_1")
        assert result["suggestion_ctr"] == 0.0
        assert result["abandonment_rate"] == 0.0
        assert result["engagement_trend"] == 0.0
        assert result["session_momentum"] == 0
        assert result["category_fatigue"] == {}

    @pytest.mark.asyncio
    async def test_suggestion_ctr(self, mock_db):
        """CTR = clicks / impressions."""
        now = datetime.now(timezone.utc)
        events = [
            {"user_id": "u1", "event_type": "suggestion_generated", "timestamp": now, "metadata": {}},
            {"user_id": "u1", "event_type": "suggestion_generated", "timestamp": now, "metadata": {}},
            {"user_id": "u1", "event_type": "suggestion_clicked", "timestamp": now, "metadata": {}},
        ]
        await mock_db.event_log.insert_many(events)
        result = await _compute_engagement_features(mock_db, "u1")
        assert result["suggestion_ctr"] == 0.5  # 1/2

    @pytest.mark.asyncio
    async def test_abandonment_rate(self, mock_db):
        """Abandonment rate = abandonments / starts.
        Note: mongomock strips tzinfo from stored datetimes (like real MongoDB).
        We patch datetime.now in the module to return naive UTC for compatibility.
        """
        now = _naive_utcnow()
        events = [
            {"user_id": "u1", "event_type": "action_started", "timestamp": now - timedelta(hours=1), "metadata": {}},
            {"user_id": "u1", "event_type": "action_started", "timestamp": now - timedelta(minutes=30), "metadata": {}},
            {"user_id": "u1", "event_type": "action_abandoned", "timestamp": now - timedelta(minutes=15), "metadata": {}},
        ]
        await mock_db.event_log.insert_many(events)

        # Patch datetime.now in the feature_calculator module to return naive datetimes
        # so comparisons with mongomock-stored (naive) timestamps don't fail
        import services.feature_calculator as fc_mod
        _original_now = datetime.now

        def _patched_now(tz=None):
            if tz is not None:
                return _original_now(tz).replace(tzinfo=None)
            return _original_now()

        with patch.object(fc_mod, "datetime", wraps=datetime) as mock_dt:
            mock_dt.now = _patched_now
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            result = await _compute_engagement_features(mock_db, "u1")
        assert result["abandonment_rate"] == 0.5  # 1/2

    @pytest.mark.asyncio
    async def test_session_momentum(self, mock_db):
        """Max consecutive completed sessions."""
        now = _naive_utcnow()
        events = [
            {"user_id": "u1", "event_type": "action_completed", "timestamp": now - timedelta(hours=5), "metadata": {}},
            {"user_id": "u1", "event_type": "action_completed", "timestamp": now - timedelta(hours=4), "metadata": {}},
            {"user_id": "u1", "event_type": "action_completed", "timestamp": now - timedelta(hours=3), "metadata": {}},
            {"user_id": "u1", "event_type": "action_abandoned", "timestamp": now - timedelta(hours=2), "metadata": {}},
            {"user_id": "u1", "event_type": "action_completed", "timestamp": now - timedelta(hours=1), "metadata": {}},
        ]
        await mock_db.event_log.insert_many(events)

        import services.feature_calculator as fc_mod
        _original_now = datetime.now

        def _patched_now(tz=None):
            if tz is not None:
                return _original_now(tz).replace(tzinfo=None)
            return _original_now()

        with patch.object(fc_mod, "datetime", wraps=datetime) as mock_dt:
            mock_dt.now = _patched_now
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            result = await _compute_engagement_features(mock_db, "u1")
        assert result["session_momentum"] == 3  # 3 consecutive before the abandon


# ═══════════════════════════════════════════════════════════════════
# compute_user_features — Full integration (DB-dependent)
# ═══════════════════════════════════════════════════════════════════


class TestComputeUserFeatures:

    @pytest.mark.asyncio
    async def test_no_sessions_returns_empty(self, mock_db):
        """No sessions → empty features with defaults."""
        result = await compute_user_features(mock_db, "user_1")
        assert result["user_id"] == "user_1"
        assert result["completion_rate_global"] == 0.5  # neutral default for no data
        assert result["total_sessions"] == 0

    @pytest.mark.asyncio
    async def test_basic_features(self, mock_db):
        """Computes basic features from session history."""
        now = datetime.now(timezone.utc)
        sessions = [
            {
                "user_id": "u1",
                "completed": True,
                "category": "learning",
                "started_at": (now - timedelta(hours=2)).isoformat(),
                "actual_duration": 7,
                "action_id": "a1",
            },
            {
                "user_id": "u1",
                "completed": True,
                "category": "learning",
                "started_at": (now - timedelta(hours=1)).isoformat(),
                "actual_duration": 10,
                "action_id": "a2",
            },
            {
                "user_id": "u1",
                "completed": False,
                "category": "productivity",
                "started_at": now.isoformat(),
                "actual_duration": 3,
                "action_id": "a3",
            },
        ]
        await mock_db.user_sessions_history.insert_many(sessions)

        result = await compute_user_features(mock_db, "u1")

        # Global completion: 2/3
        assert abs(result["completion_rate_global"] - 2 / 3) < 0.01
        assert result["total_sessions"] == 3

        # By category
        assert result["completion_rate_by_category"]["learning"] == 1.0  # 2/2
        assert result["completion_rate_by_category"]["productivity"] == 0.0  # 0/1

    @pytest.mark.asyncio
    async def test_features_have_required_keys(self, mock_db):
        """Verify all expected feature keys are present."""
        sessions = [
            {
                "user_id": "u1",
                "completed": True,
                "category": "learning",
                "started_at": datetime.now(timezone.utc).isoformat(),
                "actual_duration": 5,
                "action_id": "a1",
            },
        ]
        await mock_db.user_sessions_history.insert_many(sessions)

        result = await compute_user_features(mock_db, "u1")

        expected_keys = [
            "user_id",
            "completion_rate_global",
            "completion_rate_by_category",
            "completion_rate_by_time_of_day",
            "preferred_action_duration",
            "total_sessions",
        ]
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"
