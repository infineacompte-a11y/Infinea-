"""
Unit tests — Scoring Engine.
P1 critical service: ensures action ranking is computed correctly.

Tests:
- score_action: all 6 factors individually, combined scoring, adaptive weights
- _time_bucket_from_iso: time parsing for all buckets
- rank_actions_for_user: DB-dependent ranking
- get_next_best_action: slot matching
"""

import pytest
from datetime import datetime, timezone, timedelta

from services.scoring_engine import (
    score_action,
    _time_bucket_from_iso,
    _current_time_bucket,
    rank_actions_for_user,
    get_next_best_action,
    W_CATEGORY_AFFINITY,
    W_DURATION_FIT,
    W_ENERGY_MATCH,
    W_TIME_PERFORMANCE,
    W_NOVELTY_BONUS,
    W_FEEDBACK_SIGNAL,
)


# ═══════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════

def _make_action(category="learning", duration_min=5, duration_max=10,
                 energy="medium", action_id="action_001"):
    return {
        "action_id": action_id,
        "category": category,
        "duration_min": duration_min,
        "duration_max": duration_max,
        "energy_level": energy,
    }


def _make_features(completion_rate=0.8, category_rates=None, tod_rates=None,
                   preferred_duration=7, energy_by_time=None, fatigue=None,
                   adaptive_weights=None):
    return {
        "completion_rate_global": completion_rate,
        "completion_rate_by_category": category_rates or {"learning": 0.9, "productivity": 0.7},
        "completion_rate_by_time_of_day": tod_rates or {"morning": 0.85, "afternoon": 0.75},
        "preferred_action_duration": preferred_duration,
        "energy_preference_by_time": energy_by_time or {},
        "category_fatigue": fatigue or {},
        "adaptive_weights": adaptive_weights,
    }


def _make_context(energy="medium", time=15, bucket="morning",
                  recent_ids=None, feedback=None):
    return {
        "energy_level": energy,
        "available_time": time,
        "time_bucket": bucket,
        "recent_action_ids": recent_ids or set(),
        "feedback_signals": feedback or {},
    }


# ═══════════════════════════════════════════════════════════════════
# score_action — Pure function tests
# ═══════════════════════════════════════════════════════════════════


class TestScoreAction:

    def test_returns_valid_structure(self):
        """Score returns score, breakdown, weights_used."""
        result = score_action(_make_action(), _make_features(), _make_context())
        assert "score" in result
        assert "breakdown" in result
        assert "weights_used" in result
        assert 0 <= result["score"] <= 1

    def test_category_affinity_high(self):
        """High completion rate in category → high affinity score."""
        features = _make_features(category_rates={"learning": 0.95})
        result = score_action(_make_action(category="learning"), features, _make_context())
        assert result["breakdown"]["category_affinity"] == 0.95

    def test_category_affinity_unknown_falls_back_to_global(self):
        """Unknown category → falls back to global completion rate."""
        features = _make_features(completion_rate=0.6, category_rates={})
        result = score_action(_make_action(category="unknown_cat"), features, _make_context())
        assert result["breakdown"]["category_affinity"] == 0.6

    def test_category_fatigue_penalty(self):
        """Category with rising abandonment → reduced affinity."""
        features = _make_features(
            category_rates={"learning": 1.0},
            fatigue={"learning": 0.5}  # 50% fatigue
        )
        result = score_action(_make_action(category="learning"), features, _make_context())
        # 1.0 * (1 - 0.5) = 0.5
        assert result["breakdown"]["category_affinity"] == 0.5

    def test_duration_fit_perfect(self):
        """Preferred duration within action range → 1.0."""
        features = _make_features(preferred_duration=7)
        action = _make_action(duration_min=5, duration_max=10)
        result = score_action(action, features, _make_context())
        assert result["breakdown"]["duration_fit"] == 1.0

    def test_duration_fit_too_long(self):
        """Action doesn't fit in available time → 0.0."""
        action = _make_action(duration_min=20, duration_max=30)
        result = score_action(action, _make_features(), _make_context(time=10))
        assert result["breakdown"]["duration_fit"] == 0.0

    def test_duration_fit_decay(self):
        """Preferred duration outside range → decays by distance."""
        features = _make_features(preferred_duration=15)
        action = _make_action(duration_min=3, duration_max=5)  # range 3-5
        result = score_action(action, features, _make_context())
        # distance = 15 - 5 = 10, fit = max(0, 1 - 10/10) = 0
        assert result["breakdown"]["duration_fit"] == 0.0

    def test_energy_match_exact(self):
        """Exact energy match → 1.0."""
        result = score_action(
            _make_action(energy="low"),
            _make_features(),
            _make_context(energy="low"),
        )
        assert result["breakdown"]["energy_match"] == 1.0

    def test_energy_match_adjacent(self):
        """Adjacent energy → 0.5."""
        result = score_action(
            _make_action(energy="high"),
            _make_features(),
            _make_context(energy="medium"),
        )
        assert result["breakdown"]["energy_match"] == 0.5

    def test_energy_match_opposite(self):
        """Opposite energy → 0.1."""
        result = score_action(
            _make_action(energy="high"),
            _make_features(),
            _make_context(energy="low"),
        )
        assert result["breakdown"]["energy_match"] == 0.1

    def test_time_performance_morning(self):
        """Morning bucket with high rate → high time performance."""
        features = _make_features(tod_rates={"morning": 0.95})
        result = score_action(_make_action(), features, _make_context(bucket="morning"))
        assert result["breakdown"]["time_performance"] == 0.95

    def test_novelty_bonus_new_action(self):
        """Action not in recent history → full novelty bonus (1.0)."""
        result = score_action(
            _make_action(action_id="new_one"),
            _make_features(),
            _make_context(recent_ids={"old_one"}),
        )
        assert result["breakdown"]["novelty_bonus"] == 1.0

    def test_novelty_bonus_recent_action(self):
        """Recently done action → reduced novelty (0.2)."""
        result = score_action(
            _make_action(action_id="done_recently"),
            _make_features(),
            _make_context(recent_ids={"done_recently"}),
        )
        assert result["breakdown"]["novelty_bonus"] == 0.2

    def test_feedback_positive(self):
        """Positive feedback signal (+1) → score 1.0."""
        result = score_action(
            _make_action(action_id="good_action"),
            _make_features(),
            _make_context(feedback={"good_action": 1.0}),
        )
        assert result["breakdown"]["feedback_signal"] == 1.0

    def test_feedback_negative(self):
        """Negative feedback signal (-1) → score 0.0."""
        result = score_action(
            _make_action(action_id="bad_action"),
            _make_features(),
            _make_context(feedback={"bad_action": -1.0}),
        )
        assert result["breakdown"]["feedback_signal"] == 0.0

    def test_feedback_neutral(self):
        """No feedback signal → neutral 0.5."""
        result = score_action(
            _make_action(action_id="unknown"),
            _make_features(),
            _make_context(feedback={}),
        )
        assert result["breakdown"]["feedback_signal"] == 0.5

    def test_adaptive_weights_used(self):
        """When adaptive_weights present, they override defaults."""
        adaptive = {
            "category_affinity": 0.40,
            "duration_fit": 0.15,
            "energy_match": 0.15,
            "time_performance": 0.10,
            "novelty_bonus": 0.05,
            "feedback_signal": 0.15,
        }
        features = _make_features(adaptive_weights=adaptive)
        result = score_action(_make_action(), features, _make_context())
        assert result["adaptive"] is True
        assert result["weights_used"]["category_affinity"] == 0.40

    def test_default_weights_sum_to_one(self):
        """Default weight constants sum to 1.0."""
        total = (W_CATEGORY_AFFINITY + W_DURATION_FIT + W_ENERGY_MATCH
                 + W_TIME_PERFORMANCE + W_NOVELTY_BONUS + W_FEEDBACK_SIGNAL)
        assert abs(total - 1.0) < 0.01

    def test_score_range_0_to_1(self):
        """Score is always between 0 and 1."""
        # Best case: everything maxed
        features = _make_features(
            completion_rate=1.0,
            category_rates={"learning": 1.0},
            tod_rates={"morning": 1.0},
            preferred_duration=7,
        )
        context = _make_context(
            energy="medium", bucket="morning",
            recent_ids=set(),
            feedback={"action_001": 1.0},
        )
        result = score_action(_make_action(), features, context)
        assert 0 <= result["score"] <= 1.0

        # Worst case: everything minimized
        features_bad = _make_features(
            completion_rate=0.0,
            category_rates={"learning": 0.0},
            tod_rates={"morning": 0.0},
            preferred_duration=100,
            fatigue={"learning": 0.8},
        )
        context_bad = _make_context(
            energy="low",
            time=1,
            bucket="morning",
            recent_ids={"action_001"},
            feedback={"action_001": -1.0},
        )
        result_bad = score_action(
            _make_action(duration_min=50, energy="high"),
            features_bad,
            context_bad,
        )
        assert 0 <= result_bad["score"] <= 1.0


# ═══════════════════════════════════════════════════════════════════
# _time_bucket_from_iso — Pure function
# ═══════════════════════════════════════════════════════════════════


class TestTimeBucketFromIso:

    def test_morning(self):
        assert _time_bucket_from_iso("2025-01-01T08:30:00") == "morning"

    def test_afternoon(self):
        assert _time_bucket_from_iso("2025-01-01T14:00:00") == "afternoon"

    def test_evening(self):
        assert _time_bucket_from_iso("2025-01-01T20:00:00") == "evening"

    def test_night(self):
        assert _time_bucket_from_iso("2025-01-01T03:00:00") == "night"

    def test_boundary_morning_start(self):
        assert _time_bucket_from_iso("2025-01-01T06:00:00") == "morning"

    def test_boundary_afternoon_start(self):
        assert _time_bucket_from_iso("2025-01-01T12:00:00") == "afternoon"

    def test_boundary_evening_start(self):
        assert _time_bucket_from_iso("2025-01-01T18:00:00") == "evening"

    def test_boundary_night_midnight(self):
        assert _time_bucket_from_iso("2025-01-01T00:00:00") == "night"

    def test_invalid_timestamp_fallback(self):
        """Invalid ISO string → falls back to current bucket."""
        result = _time_bucket_from_iso("not-a-date")
        assert result in {"morning", "afternoon", "evening", "night"}


# ═══════════════════════════════════════════════════════════════════
# rank_actions_for_user — DB-dependent
# ═══════════════════════════════════════════════════════════════════


class TestRankActionsForUser:

    @pytest.mark.asyncio
    async def test_empty_actions_returns_empty(self, mock_db):
        result = await rank_actions_for_user(mock_db, "user_1", [])
        assert result == []

    @pytest.mark.asyncio
    async def test_no_features_returns_actions_as_is(self, mock_db):
        """No user features → returns actions unsorted (graceful fallback)."""
        actions = [_make_action(action_id="a"), _make_action(action_id="b")]
        result = await rank_actions_for_user(mock_db, "user_1", actions)
        assert len(result) == 2
        # No _score added
        assert "_score" not in result[0]

    @pytest.mark.asyncio
    async def test_with_features_returns_scored_and_sorted(self, mock_db):
        """With features, actions are scored and sorted descending."""
        await mock_db.user_features.insert_one({
            "user_id": "user_1",
            "completion_rate_global": 0.7,
            "completion_rate_by_category": {"learning": 0.9, "fitness": 0.3},
            "completion_rate_by_time_of_day": {},
            "preferred_action_duration": 7,
            "energy_preference_by_time": {},
            "category_fatigue": {},
            "adaptive_weights": None,
        })

        actions = [
            _make_action(category="fitness", action_id="fit_1"),  # lower affinity
            _make_action(category="learning", action_id="learn_1"),  # higher affinity
        ]

        result = await rank_actions_for_user(mock_db, "user_1", actions)
        assert len(result) == 2
        assert "_score" in result[0]
        # Learning should rank higher due to higher category affinity
        assert result[0]["action_id"] == "learn_1"
        assert result[0]["_score"] >= result[1]["_score"]


# ═══════════════════════════════════════════════════════════════════
# get_next_best_action — DB-dependent
# ═══════════════════════════════════════════════════════════════════


class TestGetNextBestAction:

    @pytest.mark.asyncio
    async def test_no_features_returns_none(self, mock_db):
        result = await get_next_best_action(mock_db, "user_1", slot_duration=10)
        assert result is None

    @pytest.mark.asyncio
    async def test_no_fitting_actions_returns_none(self, mock_db):
        """All actions too long for slot → None."""
        await mock_db.user_features.insert_one({
            "user_id": "user_1",
            "completion_rate_global": 0.5,
            "completion_rate_by_category": {},
            "completion_rate_by_time_of_day": {},
            "preferred_action_duration": 5,
            "energy_preference_by_time": {},
            "category_fatigue": {},
            "adaptive_weights": None,
        })
        await mock_db.micro_actions.insert_one({
            "action_id": "long_action",
            "duration_min": 30,
            "duration_max": 45,
            "category": "learning",
            "energy_level": "medium",
        })

        result = await get_next_best_action(mock_db, "user_1", slot_duration=5)
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_best_action(self, mock_db):
        """Returns the highest-scored action that fits."""
        await mock_db.user_features.insert_one({
            "user_id": "user_1",
            "completion_rate_global": 0.5,
            "completion_rate_by_category": {"learning": 0.9},
            "completion_rate_by_time_of_day": {},
            "preferred_action_duration": 7,
            "energy_preference_by_time": {},
            "category_fatigue": {},
            "adaptive_weights": None,
        })
        await mock_db.micro_actions.insert_many([
            {"action_id": "good", "duration_min": 5, "duration_max": 10,
             "category": "learning", "energy_level": "medium"},
            {"action_id": "ok", "duration_min": 5, "duration_max": 10,
             "category": "fitness", "energy_level": "medium"},
        ])

        result = await get_next_best_action(mock_db, "user_1", slot_duration=10)
        assert result is not None
        assert result["action_id"] == "good"
        assert "_score" in result
