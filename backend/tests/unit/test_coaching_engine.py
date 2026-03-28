"""
Unit tests — Coaching Engine.
Transtheoretical Model (Prochaska): stage detection, directives, drift detection.

Tests:
- assess_stage: 5 stages with boundary conditions
- get_coaching_directives: prompt fragment per stage
- get_stage_info: full stage info dict
- detect_behavioral_drift: 4 drift triggers
- format_drift_for_prompt: formatting
- assess_and_get_directives: DB-dependent convenience
- get_followup_context: DB-dependent followup check
"""

import pytest
from datetime import datetime, timezone

from services.coaching_engine import (
    UserStage,
    assess_stage,
    get_coaching_directives,
    get_stage_info,
    detect_behavioral_drift,
    format_drift_for_prompt,
    assess_and_get_directives,
    get_followup_context,
    STAGE_DIRECTIVES,
)


# ═══════════════════════════════════════════════════════════════════
# assess_stage — Pure function tests
# ═══════════════════════════════════════════════════════════════════


class TestAssessStage:

    def test_precontemplation_zero_sessions(self):
        """0 sessions → PRECONTEMPLATION."""
        assert assess_stage({"total_sessions": 0}) == UserStage.PRECONTEMPLATION

    def test_precontemplation_none_sessions(self):
        """None sessions → PRECONTEMPLATION."""
        assert assess_stage({}) == UserStage.PRECONTEMPLATION

    def test_contemplation_few_sessions(self):
        """< 10 sessions → CONTEMPLATION."""
        assert assess_stage({"total_sessions": 5}) == UserStage.CONTEMPLATION

    def test_contemplation_low_consistency_low_total(self):
        """Low consistency + < 20 sessions → CONTEMPLATION."""
        features = {"total_sessions": 15, "consistency_index": 0.1}
        assert assess_stage(features) == UserStage.CONTEMPLATION

    def test_contemplation_boundary_at_9(self):
        """9 sessions → still CONTEMPLATION."""
        assert assess_stage({"total_sessions": 9}) == UserStage.CONTEMPLATION

    def test_preparation_moderate_sessions(self):
        """10-29 sessions → PREPARATION."""
        features = {"total_sessions": 20, "consistency_index": 0.2}
        assert assess_stage(features) == UserStage.PREPARATION

    def test_preparation_low_consistency(self):
        """30+ sessions but low consistency → PREPARATION."""
        features = {"total_sessions": 35, "consistency_index": 0.3}
        assert assess_stage(features) == UserStage.PREPARATION

    def test_action_moderate_consistency(self):
        """30-99 sessions with consistency >= 0.4 → ACTION."""
        features = {"total_sessions": 50, "consistency_index": 0.5}
        assert assess_stage(features) == UserStage.ACTION

    def test_action_high_sessions_moderate_consistency(self):
        """100+ sessions but consistency < 0.7 → ACTION."""
        features = {"total_sessions": 120, "consistency_index": 0.6}
        assert assess_stage(features) == UserStage.ACTION

    def test_maintenance_high_everything(self):
        """100+ sessions + consistency >= 0.7 → MAINTENANCE."""
        features = {"total_sessions": 150, "consistency_index": 0.8}
        assert assess_stage(features) == UserStage.MAINTENANCE

    def test_maintenance_boundary(self):
        """Exactly 100 sessions + 0.7 consistency → MAINTENANCE."""
        features = {"total_sessions": 100, "consistency_index": 0.7}
        assert assess_stage(features) == UserStage.MAINTENANCE

    def test_streak_does_not_change_stage_without_user(self):
        """Without user dict, streak is not considered."""
        features = {"total_sessions": 20, "consistency_index": 0.2}
        stage = assess_stage(features)
        assert stage == UserStage.PREPARATION

    def test_user_streak_included(self):
        """User streak_days is read from user dict."""
        features = {"total_sessions": 20, "consistency_index": 0.2,
                     "engagement_trend": 0.1}
        user = {"streak_days": 10}
        stage = assess_stage(features, user)
        assert stage == UserStage.PREPARATION

    def test_none_values_treated_as_zero(self):
        """None feature values treated as 0."""
        features = {
            "total_sessions": None,
            "consistency_index": None,
            "engagement_trend": None,
        }
        assert assess_stage(features) == UserStage.PRECONTEMPLATION

    def test_all_stages_covered(self):
        """All 5 stages are reachable."""
        stages_reached = set()
        test_cases = [
            {"total_sessions": 0},
            {"total_sessions": 5},
            {"total_sessions": 20, "consistency_index": 0.2},
            {"total_sessions": 50, "consistency_index": 0.5},
            {"total_sessions": 150, "consistency_index": 0.8},
        ]
        for features in test_cases:
            stages_reached.add(assess_stage(features))
        assert stages_reached == set(UserStage)


# ═══════════════════════════════════════════════════════════════════
# get_coaching_directives — Pure function
# ═══════════════════════════════════════════════════════════════════


class TestGetCoachingDirectives:

    def test_returns_string_for_each_stage(self):
        """Each stage has a non-empty prompt fragment."""
        for stage in UserStage:
            result = get_coaching_directives(stage)
            assert isinstance(result, str)
            assert len(result) > 50

    def test_precontemplation_mentions_decouverte(self):
        result = get_coaching_directives(UserStage.PRECONTEMPLATION)
        assert "decouverte" in result.lower()

    def test_contemplation_mentions_exploration(self):
        result = get_coaching_directives(UserStage.CONTEMPLATION)
        assert "exploration" in result.lower() or "explore" in result.lower()

    def test_action_mentions_progresser(self):
        result = get_coaching_directives(UserStage.ACTION)
        assert "progresser" in result.lower() or "action" in result.lower()

    def test_maintenance_mentions_maitrise(self):
        result = get_coaching_directives(UserStage.MAINTENANCE)
        assert "maitrise" in result.lower()


# ═══════════════════════════════════════════════════════════════════
# get_stage_info — Pure function
# ═══════════════════════════════════════════════════════════════════


class TestGetStageInfo:

    def test_returns_tone_techniques_prompt(self):
        """Stage info contains tone, techniques, prompt_fragment."""
        for stage in UserStage:
            info = get_stage_info(stage)
            assert "tone" in info
            assert "techniques" in info
            assert "prompt_fragment" in info
            assert isinstance(info["techniques"], list)
            assert len(info["techniques"]) >= 2

    def test_all_stages_have_directives(self):
        """All 5 stages exist in STAGE_DIRECTIVES."""
        for stage in UserStage:
            assert stage in STAGE_DIRECTIVES


# ═══════════════════════════════════════════════════════════════════
# detect_behavioral_drift — Async, DB-optional
# ═══════════════════════════════════════════════════════════════════


class TestDetectBehavioralDrift:

    @pytest.mark.asyncio
    async def test_no_drift_stable_user(self, mock_db):
        """Stable user → no drift."""
        features = {
            "engagement_trend": 0.1,
            "category_fatigue": {},
            "consistency_index": 0.6,
            "active_days_last_30": 15,
            "session_momentum": 5,
            "total_completed": 20,
        }
        result = await detect_behavioral_drift(mock_db, "user_1", features)
        assert result is None

    @pytest.mark.asyncio
    async def test_engagement_drop_high_severity(self, mock_db):
        """Engagement trend < -0.5 → high severity drift."""
        features = {"engagement_trend": -0.6, "category_fatigue": {},
                     "consistency_index": 0.5, "active_days_last_30": 10,
                     "session_momentum": 3, "total_completed": 20}
        result = await detect_behavioral_drift(mock_db, "user_1", features)
        assert result is not None
        assert result["type"] == "engagement_drop"
        assert result["severity"] == "high"

    @pytest.mark.asyncio
    async def test_engagement_drop_medium_severity(self, mock_db):
        """Engagement trend between -0.5 and -0.3 → medium severity."""
        features = {"engagement_trend": -0.4, "category_fatigue": {},
                     "consistency_index": 0.5, "active_days_last_30": 10,
                     "session_momentum": 3, "total_completed": 20}
        result = await detect_behavioral_drift(mock_db, "user_1", features)
        assert result is not None
        assert result["type"] == "engagement_drop"
        assert result["severity"] == "medium"

    @pytest.mark.asyncio
    async def test_category_fatigue_detected(self, mock_db):
        """Category with > 0.2 fatigue → category_fatigue drift."""
        features = {"engagement_trend": 0, "category_fatigue": {"learning": 0.3},
                     "consistency_index": 0.5, "active_days_last_30": 10,
                     "session_momentum": 3, "total_completed": 20}
        result = await detect_behavioral_drift(mock_db, "user_1", features)
        assert result is not None
        assert result["type"] == "category_fatigue"

    @pytest.mark.asyncio
    async def test_consistency_drop_detected(self, mock_db):
        """Low consistency + some active days → consistency_drop."""
        features = {"engagement_trend": 0, "category_fatigue": {},
                     "consistency_index": 0.1, "active_days_last_30": 5,
                     "session_momentum": 3, "total_completed": 20}
        result = await detect_behavioral_drift(mock_db, "user_1", features)
        assert result is not None
        assert result["type"] == "consistency_drop"

    @pytest.mark.asyncio
    async def test_momentum_lost_detected(self, mock_db):
        """Zero momentum with history → momentum_lost."""
        features = {"engagement_trend": 0, "category_fatigue": {},
                     "consistency_index": 0.5, "active_days_last_30": 2,
                     "session_momentum": 0, "total_completed": 15}
        result = await detect_behavioral_drift(mock_db, "user_1", features)
        assert result is not None
        assert result["type"] == "momentum_lost"

    @pytest.mark.asyncio
    async def test_highest_severity_returned_first(self, mock_db):
        """Multiple drifts → highest severity returned."""
        features = {"engagement_trend": -0.6, "category_fatigue": {"learning": 0.3},
                     "consistency_index": 0.1, "active_days_last_30": 5,
                     "session_momentum": 0, "total_completed": 15}
        result = await detect_behavioral_drift(mock_db, "user_1", features)
        assert result is not None
        assert result["severity"] == "high"


# ═══════════════════════════════════════════════════════════════════
# format_drift_for_prompt — Pure function
# ═══════════════════════════════════════════════════════════════════


class TestFormatDriftForPrompt:

    def test_none_returns_empty(self):
        assert format_drift_for_prompt(None) == ""

    def test_drift_returns_message(self):
        drift = {"type": "engagement_drop", "severity": "high",
                 "message": "ALERTE DRIFT: test message"}
        assert format_drift_for_prompt(drift) == "ALERTE DRIFT: test message"


# ═══════════════════════════════════════════════════════════════════
# assess_and_get_directives — Async, DB-dependent
# ═══════════════════════════════════════════════════════════════════


class TestAssessAndGetDirectives:

    @pytest.mark.asyncio
    async def test_no_features_defaults_to_contemplation(self, mock_db):
        """No features in DB → falls back (0 sessions = PRECONTEMPLATION)."""
        user = {"user_id": "user_1", "streak_days": 0}
        stage, directives = await assess_and_get_directives(mock_db, "user_1", user)
        assert stage == UserStage.PRECONTEMPLATION
        assert len(directives) > 0

    @pytest.mark.asyncio
    async def test_with_features_returns_correct_stage(self, mock_db):
        """Features in DB → correct stage detected."""
        await mock_db.user_features.insert_one({
            "user_id": "user_1",
            "total_sessions": 50,
            "consistency_index": 0.6,
            "engagement_trend": 0.1,
            "active_days_last_30": 15,
        })
        user = {"user_id": "user_1", "streak_days": 10}
        stage, directives = await assess_and_get_directives(mock_db, "user_1", user)
        assert stage == UserStage.ACTION
        assert "action" in directives.lower()


# ═══════════════════════════════════════════════════════════════════
# get_followup_context — Async, DB-dependent
# ═══════════════════════════════════════════════════════════════════


class TestGetFollowupContext:

    @pytest.mark.asyncio
    async def test_no_suggestions_returns_empty(self, mock_db):
        """No previous suggestion → empty string."""
        result = await get_followup_context(mock_db, "user_1")
        assert result == ""

    @pytest.mark.asyncio
    async def test_suggestion_completed(self, mock_db):
        """User completed the suggested action → congratulatory context."""
        now = datetime.now(timezone.utc).isoformat()
        await mock_db.coach_messages.insert_one({
            "user_id": "user_1",
            "role": "assistant",
            "suggested_action_id": "action_x",
            "created_at": now,
        })
        await mock_db.user_sessions_history.insert_one({
            "user_id": "user_1",
            "action_id": "action_x",
            "action_title": "Vocabulaire thai",
            "completed": True,
            "started_at": now,
        })
        result = await get_followup_context(mock_db, "user_1")
        assert "Vocabulaire thai" in result
        assert "completee" in result.lower() or "Felicite" in result

    @pytest.mark.asyncio
    async def test_suggestion_not_completed(self, mock_db):
        """User did not complete the suggested action → gentle nudge context."""
        now = datetime.now(timezone.utc).isoformat()
        await mock_db.coach_messages.insert_one({
            "user_id": "user_1",
            "role": "assistant",
            "suggested_action_id": "action_y",
            "created_at": now,
        })
        await mock_db.micro_actions.insert_one({
            "action_id": "action_y",
            "title": "Meditation 3 min",
        })
        result = await get_followup_context(mock_db, "user_1")
        assert "Meditation 3 min" in result
        assert "pas encore" in result.lower()
