"""
Unit tests — F.4 Feedback Loop & Apprentissage.
Tests _compute_slot_reliability() and the reliability-aware
_enrich_with_confidence() from services/micro_instant_engine.

Tests:
- Slot reliability computation from outcomes
- Auto-suppression of systematically ignored slots
- Confidence boost for high-exploitation slots
- Confidence penalty for low-exploitation slots
- Neutral behavior when insufficient data
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from services.micro_instant_engine import (
    _compute_slot_reliability,
    _enrich_with_confidence,
    RELIABILITY_LOOKBACK_DAYS,
    MIN_OUTCOMES_FOR_RELIABILITY,
    SUPPRESS_THRESHOLD,
    BOOST_THRESHOLD,
    RELIABILITY_BOOST_FACTOR,
    RELIABILITY_PENALTY_FACTOR,
    MIN_CONFIDENCE,
)


# ── Helpers ──

TEST_USER_ID = "user_test_abc123"


async def _seed_outcomes(db, user_id, outcomes_by_hour):
    """
    Seed micro_instant_outcomes for testing.
    outcomes_by_hour: {hour: [("exploited", 3), ("skipped", 7)]}
    """
    now = datetime.now(timezone.utc)
    for hour, outcome_list in outcomes_by_hour.items():
        for outcome, count in outcome_list:
            for i in range(count):
                ts = now.replace(hour=hour, minute=i, second=0, microsecond=0)
                await db.micro_instant_outcomes.insert_one({
                    "user_id": user_id,
                    "instant_id": f"mi_test_{hour}_{outcome}_{i}",
                    "outcome": outcome,
                    "recorded_at": ts.isoformat(),
                })


def _make_window(hour, source="calendar_gap", base_confidence=0.90):
    """Build a test window at a specific hour."""
    now = datetime.now(timezone.utc)
    start = now.replace(hour=hour, minute=0, second=0, microsecond=0)
    if start <= now:
        start += timedelta(days=1)
    end = start + timedelta(minutes=15)
    return {
        "window_start": start.isoformat(),
        "window_end": end.isoformat(),
        "duration_minutes": 15,
        "source": source,
        "base_confidence": base_confidence,
        "context": {
            "time_bucket": "afternoon" if 12 <= hour < 18 else "morning",
            "trigger": "gap_between_events",
        },
    }


# ═══════════════════════════════════════════════════════════════════
# TestComputeSlotReliability
# ═══════════════════════════════════════════════════════════════════


class TestComputeSlotReliability:

    @pytest.mark.asyncio
    async def test_empty_outcomes(self, mock_db):
        """No outcomes → empty dict."""
        result = await _compute_slot_reliability(mock_db, TEST_USER_ID)
        assert result == {}

    @pytest.mark.asyncio
    async def test_high_exploitation_slot(self, mock_db):
        """Slot with 8/10 exploited → reliability 0.80, not suppressed."""
        await _seed_outcomes(mock_db, TEST_USER_ID, {
            14: [("exploited", 8), ("skipped", 2)],
        })
        result = await _compute_slot_reliability(mock_db, TEST_USER_ID)

        assert 14 in result
        assert result[14]["reliability"] == 0.8
        assert result[14]["suppress"] is False
        assert result[14]["total"] == 10

    @pytest.mark.asyncio
    async def test_low_exploitation_suppressed(self, mock_db):
        """Slot with 0/10 exploited → reliability 0.0, suppressed."""
        await _seed_outcomes(mock_db, TEST_USER_ID, {
            9: [("skipped", 7), ("dismissed", 3)],
        })
        result = await _compute_slot_reliability(mock_db, TEST_USER_ID)

        assert 9 in result
        assert result[9]["reliability"] == 0.0
        assert result[9]["suppress"] is True

    @pytest.mark.asyncio
    async def test_insufficient_data_neutral(self, mock_db):
        """Slot with only 3 outcomes → reliability 0.5 (neutral), not suppressed."""
        await _seed_outcomes(mock_db, TEST_USER_ID, {
            11: [("exploited", 1), ("skipped", 2)],
        })
        result = await _compute_slot_reliability(mock_db, TEST_USER_ID)

        assert 11 in result
        assert result[11]["reliability"] == 0.5
        assert result[11]["suppress"] is False

    @pytest.mark.asyncio
    async def test_multiple_slots(self, mock_db):
        """Multiple slots computed independently."""
        await _seed_outcomes(mock_db, TEST_USER_ID, {
            8: [("exploited", 9), ("skipped", 1)],   # 90% → reliable
            15: [("skipped", 8), ("dismissed", 2)],   # 0% → suppress
        })
        result = await _compute_slot_reliability(mock_db, TEST_USER_ID)

        assert result[8]["reliability"] == 0.9
        assert result[8]["suppress"] is False
        assert result[15]["reliability"] == 0.0
        assert result[15]["suppress"] is True

    @pytest.mark.asyncio
    async def test_ignores_old_outcomes(self, mock_db):
        """Outcomes older than RELIABILITY_LOOKBACK_DAYS are ignored."""
        old_ts = (datetime.now(timezone.utc) - timedelta(days=RELIABILITY_LOOKBACK_DAYS + 1))
        for i in range(10):
            await mock_db.micro_instant_outcomes.insert_one({
                "user_id": TEST_USER_ID,
                "instant_id": f"mi_old_{i}",
                "outcome": "exploited",
                "recorded_at": old_ts.replace(hour=14, minute=i).isoformat(),
            })
        result = await _compute_slot_reliability(mock_db, TEST_USER_ID)
        assert result == {}


# ═══════════════════════════════════════════════════════════════════
# TestEnrichWithReliability
# ═══════════════════════════════════════════════════════════════════


class TestEnrichWithReliability:

    @pytest.mark.asyncio
    async def test_boost_reliable_slot(self):
        """Slot with reliability > 0.70 gets RELIABILITY_BOOST_FACTOR."""
        windows = [_make_window(14)]
        features = {
            "completion_rate_by_time_of_day": {"afternoon": 0.8},
            "engagement_trend": 0.0,
            "consistency_index": 1.0,
            "session_momentum": 0,
        }
        slot_rel = {14: {"exploited": 8, "skipped": 2, "dismissed": 0, "total": 10,
                         "reliability": 0.80, "suppress": False}}

        result = await _enrich_with_confidence(windows, features, slot_rel)

        # Without reliability: base * tod * trend * consistency
        # With reliability: * RELIABILITY_BOOST_FACTOR
        assert result[0]["context"].get("feedback_boosted") is True
        assert result[0]["context"]["slot_reliability"] == 0.80

    @pytest.mark.asyncio
    async def test_suppress_ignored_slot(self):
        """Slot with suppress=True gets confidence forced to 0."""
        windows = [_make_window(9, base_confidence=0.90)]
        features = {
            "completion_rate_by_time_of_day": {"morning": 0.9},
            "engagement_trend": 0.5,
            "consistency_index": 1.0,
            "session_momentum": 5,
        }
        slot_rel = {9: {"exploited": 0, "skipped": 10, "dismissed": 0, "total": 10,
                        "reliability": 0.0, "suppress": True}}

        result = await _enrich_with_confidence(windows, features, slot_rel)

        assert result[0]["confidence_score"] == 0.0
        assert result[0]["context"].get("feedback_suppressed") is True

    @pytest.mark.asyncio
    async def test_penalty_low_exploitation(self):
        """Slot with reliability < 0.30 (but not suppressed) gets penalty."""
        windows = [_make_window(14)]
        features = {
            "completion_rate_by_time_of_day": {"afternoon": 0.5},
            "engagement_trend": 0.0,
            "consistency_index": 0.5,
            "session_momentum": 0,
        }
        slot_rel = {14: {"exploited": 1, "skipped": 6, "dismissed": 0, "total": 7,
                         "reliability": 0.143, "suppress": False}}

        result_with = await _enrich_with_confidence(
            [_make_window(14)], features, slot_rel
        )
        result_without = await _enrich_with_confidence(
            [_make_window(14)], features, None
        )

        # With penalty should be lower
        assert result_with[0]["confidence_score"] < result_without[0]["confidence_score"]

    @pytest.mark.asyncio
    async def test_no_reliability_data_unchanged(self):
        """No slot_reliability → confidence is same as before F.4."""
        windows = [_make_window(14)]
        features = {
            "completion_rate_by_time_of_day": {"afternoon": 0.7},
            "engagement_trend": 0.0,
            "consistency_index": 0.5,
            "session_momentum": 0,
        }

        result_none = await _enrich_with_confidence(
            [_make_window(14)], features, None
        )
        result_empty = await _enrich_with_confidence(
            [_make_window(14)], features, {}
        )

        assert result_none[0]["confidence_score"] == result_empty[0]["confidence_score"]

    @pytest.mark.asyncio
    async def test_neutral_when_insufficient_outcomes(self):
        """Slot with < MIN_OUTCOMES_FOR_RELIABILITY → reliability 0.5, no boost/penalty."""
        windows = [_make_window(14)]
        features = {
            "completion_rate_by_time_of_day": {"afternoon": 0.7},
            "engagement_trend": 0.0,
            "consistency_index": 0.5,
            "session_momentum": 0,
        }
        slot_rel = {14: {"exploited": 2, "skipped": 1, "dismissed": 0, "total": 3,
                         "reliability": 0.5, "suppress": False}}

        result_with = await _enrich_with_confidence(
            [_make_window(14)], features, slot_rel
        )
        result_without = await _enrich_with_confidence(
            [_make_window(14)], features, None
        )

        # Reliability 0.5 is between 0.30 and 0.70 → no boost, no penalty
        assert result_with[0]["confidence_score"] == result_without[0]["confidence_score"]
