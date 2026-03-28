"""
Unit tests — User Model (Deep Context).
Behavioral text builder, profile text, journey/social text.

Tests:
- _build_profile_text: various user profiles
- _build_behavioral_text: all 18 feature dimensions
- build_deep_context: DB-dependent full context build
- build_user_context_legacy: backward compatibility
"""

import pytest
from datetime import datetime, timezone

from services.user_model import (
    _build_profile_text,
    _build_behavioral_text,
    build_deep_context,
    build_user_context_legacy,
)


# ═══════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════

def _make_user(name="Sam", goals=None, streak=5, tier="free",
               total_time=120, interests=None, times=None, energy="medium"):
    return {
        "user_id": "user_test_1",
        "name": name,
        "streak_days": streak,
        "total_time_invested": total_time,
        "subscription_tier": tier,
        "user_profile": {
            "goals": goals or ["learning"],
            "interests": interests or ["thai", "piano"],
            "preferred_times": times or ["matin", "soir"],
            "energy_level": energy,
        },
    }


def _make_features(**overrides):
    base = {
        "completion_rate_global": 0.75,
        "completion_rate_by_category": {"learning": 0.9, "productivity": 0.5},
        "engagement_trend": 0.1,
        "consistency_index": 0.6,
        "active_days_last_30": 18,
        "session_momentum": 4,
        "preferred_action_duration": 7,
        "best_performing_buckets": ["morning", "evening"],
        "category_fatigue": {},
        "abandonment_rate": 0.15,
        "learning_velocity": {},
        "difficulty_calibration": {},
        "coaching_stage": "action",
    }
    base.update(overrides)
    return base


# ═══════════════════════════════════════════════════════════════════
# _build_profile_text — Pure function
# ═══════════════════════════════════════════════════════════════════


class TestBuildProfileText:

    def test_contains_name(self):
        result = _build_profile_text(_make_user(name="Alice"))
        assert "Alice" in result

    def test_contains_goals(self):
        result = _build_profile_text(_make_user(goals=["learning", "well_being"]))
        assert "apprentissage" in result
        assert "bien-etre" in result

    def test_contains_streak(self):
        result = _build_profile_text(_make_user(streak=12))
        assert "12" in result

    def test_contains_tier(self):
        result = _build_profile_text(_make_user(tier="premium"))
        assert "premium" in result

    def test_contains_total_time(self):
        result = _build_profile_text(_make_user(total_time=300))
        assert "300" in result

    def test_contains_interests(self):
        result = _build_profile_text(_make_user(interests=["guitare", "lecture"]))
        assert "guitare" in result

    def test_contains_preferred_times(self):
        result = _build_profile_text(_make_user(times=["matin"]))
        assert "matin" in result

    def test_contains_energy(self):
        result = _build_profile_text(_make_user(energy="high"))
        assert "high" in result

    def test_empty_profile_graceful(self):
        """User without user_profile → graceful defaults."""
        user = {"user_id": "u1", "name": "Test", "streak_days": 0,
                "total_time_invested": 0, "subscription_tier": "free"}
        result = _build_profile_text(user)
        assert "PROFIL UTILISATEUR" in result
        assert "non definis" in result

    def test_interests_as_dict(self):
        """Interests as dict → serialized properly."""
        user = _make_user()
        user["user_profile"]["interests"] = {"lang": "thai", "music": "piano"}
        result = _build_profile_text(user)
        assert "thai" in result

    def test_display_name_fallback(self):
        """If 'name' is missing, fallback to display_name."""
        user = {"user_id": "u1", "display_name": "FallbackName",
                "streak_days": 0, "total_time_invested": 0,
                "subscription_tier": "free"}
        result = _build_profile_text(user)
        assert "FallbackName" in result


# ═══════════════════════════════════════════════════════════════════
# _build_behavioral_text — Pure function
# ═══════════════════════════════════════════════════════════════════


class TestBuildBehavioralText:

    def test_contains_header(self):
        result = _build_behavioral_text(_make_features())
        assert "PROFIL COMPORTEMENTAL" in result

    def test_completion_rate_excellent(self):
        result = _build_behavioral_text(_make_features(completion_rate_global=0.85))
        assert "excellent" in result

    def test_completion_rate_bon(self):
        result = _build_behavioral_text(_make_features(completion_rate_global=0.65))
        assert "bon" in result

    def test_completion_rate_low(self):
        result = _build_behavioral_text(_make_features(completion_rate_global=0.35))
        assert "micro-actions" in result or "ameliorer" in result

    def test_category_strengths(self):
        features = _make_features(
            completion_rate_by_category={"learning": 0.9, "productivity": 0.3}
        )
        result = _build_behavioral_text(features)
        assert "Points forts" in result
        assert "apprentissage" in result

    def test_category_weaknesses(self):
        features = _make_features(
            completion_rate_by_category={"productivity": 0.2}
        )
        result = _build_behavioral_text(features)
        assert "Points faibles" in result

    def test_engagement_trend_up(self):
        result = _build_behavioral_text(_make_features(engagement_trend=0.15))
        assert "progression" in result

    def test_engagement_trend_down(self):
        result = _build_behavioral_text(_make_features(engagement_trend=-0.15))
        assert "baisse" in result

    def test_engagement_trend_stable(self):
        result = _build_behavioral_text(_make_features(engagement_trend=0.02))
        assert "stable" in result

    def test_consistency_shown(self):
        result = _build_behavioral_text(_make_features(
            consistency_index=0.7, active_days_last_30=21
        ))
        assert "70%" in result
        assert "21" in result

    def test_momentum_high(self):
        result = _build_behavioral_text(_make_features(session_momentum=6))
        assert "excellent rythme" in result

    def test_momentum_moderate(self):
        result = _build_behavioral_text(_make_features(session_momentum=3))
        assert "bon rythme" in result

    def test_preferred_duration_shown(self):
        result = _build_behavioral_text(_make_features(preferred_action_duration=10))
        assert "10" in result and "min" in result

    def test_best_buckets_translated(self):
        result = _build_behavioral_text(_make_features(
            best_performing_buckets=["morning", "evening"]
        ))
        assert "matin" in result
        assert "soir" in result

    def test_category_fatigue_shown(self):
        result = _build_behavioral_text(_make_features(
            category_fatigue={"learning": 0.25}
        ))
        assert "Fatigue" in result

    def test_high_abandonment_shown(self):
        result = _build_behavioral_text(_make_features(abandonment_rate=0.45))
        assert "abandon" in result.lower()

    def test_learning_velocity_fast(self):
        result = _build_behavioral_text(_make_features(
            learning_velocity={"thai": 1.5}
        ))
        assert "rapide" in result.lower()

    def test_learning_velocity_slow(self):
        result = _build_behavioral_text(_make_features(
            learning_velocity={"piano": 0.5}
        ))
        assert "lente" in result.lower()

    def test_difficulty_calibration_shown(self):
        result = _build_behavioral_text(_make_features(
            difficulty_calibration={"optimal_zone": [2, 3], "completion_by_difficulty": {2: 0.9}}
        ))
        assert "difficulte" in result.lower()

    def test_coaching_stage_shown(self):
        result = _build_behavioral_text(_make_features(coaching_stage="maintenance"))
        assert "maitrise" in result

    def test_empty_features_minimal_output(self):
        """Empty features dict → just header + trend + consistency."""
        result = _build_behavioral_text({})
        assert "PROFIL COMPORTEMENTAL" in result

    def test_none_completion_rate_skipped(self):
        """None completion rate → line not included."""
        result = _build_behavioral_text(_make_features(completion_rate_global=None))
        assert "completion" not in result.lower() or "Taux" not in result


# ═══════════════════════════════════════════════════════════════════
# build_deep_context — Async, DB-dependent
# ═══════════════════════════════════════════════════════════════════


class TestBuildDeepContext:

    @pytest.mark.asyncio
    async def test_returns_expected_keys(self, mock_db):
        user = _make_user()
        result = await build_deep_context(mock_db, user)
        assert "profile_text" in result
        assert "behavioral_text" in result
        assert "journey_text" in result
        assert "social_text" in result
        assert "full_text" in result
        assert "coaching_signals" in result

    @pytest.mark.asyncio
    async def test_profile_always_included(self, mock_db):
        user = _make_user()
        result = await build_deep_context(mock_db, user)
        assert "PROFIL UTILISATEUR" in result["profile_text"]
        assert "PROFIL UTILISATEUR" in result["full_text"]

    @pytest.mark.asyncio
    async def test_behavioral_excluded_when_disabled(self, mock_db):
        user = _make_user()
        result = await build_deep_context(mock_db, user, include_behavioral=False)
        assert result["behavioral_text"] == ""

    @pytest.mark.asyncio
    async def test_objectives_excluded_when_disabled(self, mock_db):
        user = _make_user()
        result = await build_deep_context(mock_db, user, include_objectives=False)
        assert result["journey_text"] == ""

    @pytest.mark.asyncio
    async def test_social_excluded_by_default(self, mock_db):
        user = _make_user()
        result = await build_deep_context(mock_db, user)
        assert result["social_text"] == ""

    @pytest.mark.asyncio
    async def test_coaching_signals_populated(self, mock_db):
        """coaching_signals has expected keys even without features."""
        user = _make_user()
        result = await build_deep_context(mock_db, user)
        signals = result["coaching_signals"]
        assert "total_sessions" in signals
        assert "consistency_index" in signals
        assert "engagement_trend" in signals
        assert "streak_days" in signals

    @pytest.mark.asyncio
    async def test_with_features_in_db(self, mock_db):
        """When features exist in DB, behavioral_text is populated."""
        user = _make_user()
        await mock_db.user_features.insert_one({
            "user_id": "user_test_1",
            **_make_features(),
        })
        result = await build_deep_context(mock_db, user)
        assert "PROFIL COMPORTEMENTAL" in result["behavioral_text"]

    @pytest.mark.asyncio
    async def test_with_objectives_in_db(self, mock_db):
        """Active objectives → journey_text populated."""
        user = _make_user()
        await mock_db.objectives.insert_one({
            "user_id": "user_test_1",
            "title": "Apprendre le thai",
            "status": "active",
            "current_day": 10,
            "target_duration_days": 30,
        })
        result = await build_deep_context(mock_db, user)
        assert "thai" in result["journey_text"].lower()
        assert "PARCOURS" in result["journey_text"]

    @pytest.mark.asyncio
    async def test_with_social_in_db(self, mock_db):
        """Social data → social_text populated when include_social=True."""
        user = _make_user()
        await mock_db.follows.insert_one({
            "follower_id": "other_user",
            "following_id": "user_test_1",
            "status": "accepted",
        })
        result = await build_deep_context(mock_db, user, include_social=True)
        assert "SOCIAL" in result["social_text"]


# ═══════════════════════════════════════════════════════════════════
# build_user_context_legacy — Backward compat
# ═══════════════════════════════════════════════════════════════════


class TestBuildUserContextLegacy:

    @pytest.mark.asyncio
    async def test_returns_profile_string(self):
        user = _make_user()
        result = await build_user_context_legacy(user)
        assert isinstance(result, str)
        assert "PROFIL UTILISATEUR" in result
        assert "Sam" in result
