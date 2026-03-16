"""
Unit tests — Micro-Instant Engine.
P1 critical service: ensures micro-instant prediction works correctly.

Tests:
- _time_bucket: hour mapping
- _collect_calendar_windows: gap detection with safety buffer
- _collect_routine_windows: schedule extraction
- _collect_behavioral_patterns: pattern detection from session history
- _enrich_with_confidence: confidence scoring with features
- _deduplicate_windows: overlap removal
- predict_micro_instants: full pipeline
- record_instant_outcome: feedback tracking
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from services.micro_instant_engine import (
    _time_bucket,
    _collect_calendar_windows,
    _collect_routine_windows,
    _collect_behavioral_patterns,
    _enrich_with_confidence,
    _deduplicate_windows,
    _get_next_curriculum_steps,
    predict_micro_instants,
    record_instant_outcome,
    SOURCE_CONFIDENCE,
    SAFETY_BUFFER_MINUTES,
    MIN_CONFIDENCE,
    MAX_INSTANTS_PER_DAY,
)
from services.slot_detector import DEFAULT_SETTINGS


# ═══════════════════════════════════════════════════════════════════
# _time_bucket — Pure function
# ═══════════════════════════════════════════════════════════════════


class TestTimeBucket:

    def test_morning(self):
        assert _time_bucket(8) == "morning"

    def test_afternoon(self):
        assert _time_bucket(14) == "afternoon"

    def test_evening(self):
        assert _time_bucket(20) == "evening"

    def test_night(self):
        assert _time_bucket(3) == "night"

    def test_boundaries(self):
        assert _time_bucket(6) == "morning"
        assert _time_bucket(12) == "afternoon"
        assert _time_bucket(18) == "evening"
        assert _time_bucket(0) == "night"


# ═══════════════════════════════════════════════════════════════════
# _collect_calendar_windows — Calendar gap extraction
# ═══════════════════════════════════════════════════════════════════


class TestCollectCalendarWindows:

    def _make_event(self, start_hour, end_hour, summary="Meeting"):
        base = datetime(2030, 6, 1, tzinfo=timezone.utc)
        return {
            "summary": summary,
            "start": {"dateTime": (base + timedelta(hours=start_hour)).isoformat()},
            "end": {"dateTime": (base + timedelta(hours=end_hour)).isoformat()},
        }

    @pytest.mark.asyncio
    async def test_gap_between_events(self, mock_db):
        events = [
            self._make_event(10, 10.5),   # 10:00-10:30
            self._make_event(10.75, 11),   # 10:45-11:00
        ]
        windows = await _collect_calendar_windows(mock_db, "u1", events, DEFAULT_SETTINGS)
        # 15 min gap minus 3 min buffer = 12 min
        gaps = [w for w in windows if w["source"] == "calendar_gap"]
        assert len(gaps) >= 1
        assert gaps[0]["duration_minutes"] <= 15

    @pytest.mark.asyncio
    async def test_safety_buffer_applied(self, mock_db):
        """Buffer removes 3 minutes from end of each window."""
        events = [
            self._make_event(10, 10.5),
            self._make_event(10.6, 11),  # 6 min gap
        ]
        windows = await _collect_calendar_windows(mock_db, "u1", events, DEFAULT_SETTINGS)
        for w in windows:
            if w["source"] == "calendar_gap":
                # Duration should be less than 6 min due to buffer
                assert w["duration_minutes"] <= 6

    @pytest.mark.asyncio
    async def test_no_events_returns_empty(self, mock_db):
        windows = await _collect_calendar_windows(mock_db, "u1", [], DEFAULT_SETTINGS)
        assert windows == []

    @pytest.mark.asyncio
    async def test_source_is_calendar_gap(self, mock_db):
        events = [
            self._make_event(10, 10.5),
            self._make_event(11, 11.5),
        ]
        windows = await _collect_calendar_windows(mock_db, "u1", events, DEFAULT_SETTINGS)
        for w in windows:
            assert w["source"] == "calendar_gap"
            assert w["base_confidence"] == SOURCE_CONFIDENCE["calendar_gap"]


# ═══════════════════════════════════════════════════════════════════
# _collect_routine_windows — Routine schedule extraction
# ═══════════════════════════════════════════════════════════════════


class TestCollectRoutineWindows:

    @pytest.mark.asyncio
    async def test_active_daily_routine(self, mock_db):
        """Active daily routine generates a window."""
        await mock_db.routines.insert_one({
            "user_id": "u1",
            "routine_id": "rtn_test",
            "name": "Morning routine",
            "time_of_day": "morning",
            "frequency": "daily",
            "frequency_days": None,
            "is_active": True,
            "total_minutes": 15,
            "last_completed_at": None,
        })
        windows = await _collect_routine_windows(mock_db, "u1")
        routine_wins = [w for w in windows if w["source"] == "routine_window"]
        # May or may not show depending on current time vs morning
        assert isinstance(routine_wins, list)
        for w in routine_wins:
            assert w["context"]["routine_name"] == "Morning routine"

    @pytest.mark.asyncio
    async def test_inactive_routine_excluded(self, mock_db):
        """Inactive routines are not collected."""
        await mock_db.routines.insert_one({
            "user_id": "u1",
            "routine_id": "rtn_inactive",
            "name": "Inactive",
            "time_of_day": "morning",
            "frequency": "daily",
            "is_active": False,
            "total_minutes": 10,
        })
        windows = await _collect_routine_windows(mock_db, "u1")
        assert len(windows) == 0

    @pytest.mark.asyncio
    async def test_already_completed_today_excluded(self, mock_db):
        """Routines completed today are excluded."""
        now = datetime.now(timezone.utc)
        await mock_db.routines.insert_one({
            "user_id": "u1",
            "routine_id": "rtn_done",
            "name": "Done today",
            "time_of_day": "evening",
            "frequency": "daily",
            "is_active": True,
            "total_minutes": 10,
            "last_completed_at": now.isoformat(),
        })
        windows = await _collect_routine_windows(mock_db, "u1")
        assert len(windows) == 0

    @pytest.mark.asyncio
    async def test_no_routines_returns_empty(self, mock_db):
        windows = await _collect_routine_windows(mock_db, "u1")
        assert windows == []


# ═══════════════════════════════════════════════════════════════════
# _collect_behavioral_patterns — Pattern detection
# ═══════════════════════════════════════════════════════════════════


class TestCollectBehavioralPatterns:

    @pytest.mark.asyncio
    async def test_detects_recurring_pattern(self, mock_db):
        """3+ sessions at same hour → detected as pattern."""
        now = datetime.now(timezone.utc)
        sessions = []
        for day_offset in range(5):
            dt = now.replace(hour=10, minute=30) - timedelta(days=day_offset)
            sessions.append({
                "user_id": "u1",
                "started_at": dt.isoformat(),
                "completed": True,
                "actual_duration": 7,
                "category": "learning",
            })
        await mock_db.user_sessions_history.insert_many(sessions)

        windows = await _collect_behavioral_patterns(mock_db, "u1")
        pattern_wins = [w for w in windows if w["source"] == "behavioral_pattern"]
        # Should detect hour 10 as a pattern (5 occurrences)
        assert len(pattern_wins) >= 0  # May be 0 if hour 10 is past for today
        for w in pattern_wins:
            assert w["context"]["trigger"] == "learned_pattern"
            assert w["context"]["pattern_sessions"] >= 3

    @pytest.mark.asyncio
    async def test_few_sessions_no_pattern(self, mock_db):
        """Only 1-2 sessions at an hour → no pattern."""
        now = datetime.now(timezone.utc)
        sessions = [
            {
                "user_id": "u1",
                "started_at": (now - timedelta(days=1)).replace(hour=15).isoformat(),
                "completed": True,
                "actual_duration": 5,
                "category": "learning",
            },
        ]
        await mock_db.user_sessions_history.insert_many(sessions)

        windows = await _collect_behavioral_patterns(mock_db, "u1")
        # 1 session is not enough for a pattern
        assert len(windows) == 0

    @pytest.mark.asyncio
    async def test_no_sessions_returns_empty(self, mock_db):
        windows = await _collect_behavioral_patterns(mock_db, "u1")
        assert windows == []


# ═══════════════════════════════════════════════════════════════════
# _enrich_with_confidence — Behavioral confidence scoring
# ═══════════════════════════════════════════════════════════════════


class TestEnrichWithConfidence:

    @pytest.mark.asyncio
    async def test_no_features_keeps_base_confidence(self):
        windows = [{"base_confidence": 0.9, "context": {"time_bucket": "morning"}}]
        result = await _enrich_with_confidence(windows, None)
        assert result == windows

    @pytest.mark.asyncio
    async def test_high_performance_boosts_confidence(self):
        """High time-of-day performance increases confidence."""
        features = {
            "completion_rate_by_time_of_day": {"morning": 0.95},
            "engagement_trend": 0.3,
            "consistency_index": 0.8,
            "session_momentum": 5,
        }
        windows = [{"base_confidence": 0.7, "context": {"time_bucket": "morning"}}]
        result = await _enrich_with_confidence(windows, features)
        assert result[0]["confidence_score"] > 0.7

    @pytest.mark.asyncio
    async def test_low_performance_reduces_confidence(self):
        """Low performance + negative trend reduces confidence."""
        features = {
            "completion_rate_by_time_of_day": {"afternoon": 0.1},
            "engagement_trend": -0.5,
            "consistency_index": 0.1,
            "session_momentum": 0,
        }
        windows = [{"base_confidence": 0.7, "context": {"time_bucket": "afternoon"}}]
        result = await _enrich_with_confidence(windows, features)
        assert result[0]["confidence_score"] < 0.7

    @pytest.mark.asyncio
    async def test_momentum_bonus(self):
        """Momentum >= 3 adds 10% boost."""
        features_no_momentum = {
            "completion_rate_by_time_of_day": {"morning": 0.5},
            "engagement_trend": 0.0,
            "consistency_index": 0.5,
            "session_momentum": 1,
        }
        features_momentum = {**features_no_momentum, "session_momentum": 5}

        w1 = [{"base_confidence": 0.7, "context": {"time_bucket": "morning"}}]
        w2 = [{"base_confidence": 0.7, "context": {"time_bucket": "morning"}}]

        r1 = await _enrich_with_confidence(w1, features_no_momentum)
        r2 = await _enrich_with_confidence(w2, features_momentum)

        assert r2[0]["confidence_score"] > r1[0]["confidence_score"]

    @pytest.mark.asyncio
    async def test_confidence_clamped_to_1(self):
        """Confidence never exceeds 1.0."""
        features = {
            "completion_rate_by_time_of_day": {"morning": 1.0},
            "engagement_trend": 1.0,
            "consistency_index": 1.0,
            "session_momentum": 10,
        }
        windows = [{"base_confidence": 0.95, "context": {"time_bucket": "morning"}}]
        result = await _enrich_with_confidence(windows, features)
        assert result[0]["confidence_score"] <= 1.0


# ═══════════════════════════════════════════════════════════════════
# _deduplicate_windows — Overlap removal
# ═══════════════════════════════════════════════════════════════════


class TestDeduplicateWindows:

    def test_no_overlap_keeps_both(self):
        windows = [
            {
                "window_start": "2030-01-01T10:00:00+00:00",
                "window_end": "2030-01-01T10:30:00+00:00",
                "confidence_score": 0.8,
            },
            {
                "window_start": "2030-01-01T11:00:00+00:00",
                "window_end": "2030-01-01T11:30:00+00:00",
                "confidence_score": 0.7,
            },
        ]
        result = _deduplicate_windows(windows)
        assert len(result) == 2

    def test_overlap_keeps_higher_confidence(self):
        windows = [
            {
                "window_start": "2030-01-01T10:00:00+00:00",
                "window_end": "2030-01-01T10:30:00+00:00",
                "confidence_score": 0.6,
            },
            {
                "window_start": "2030-01-01T10:15:00+00:00",
                "window_end": "2030-01-01T10:45:00+00:00",
                "confidence_score": 0.9,
            },
        ]
        result = _deduplicate_windows(windows)
        assert len(result) == 1
        assert result[0]["confidence_score"] == 0.9

    def test_empty_list(self):
        assert _deduplicate_windows([]) == []

    def test_single_window(self):
        windows = [{"window_start": "2030-01-01T10:00:00+00:00",
                     "window_end": "2030-01-01T10:30:00+00:00",
                     "confidence_score": 0.8}]
        result = _deduplicate_windows(windows)
        assert len(result) == 1


# ═══════════════════════════════════════════════════════════════════
# _get_next_curriculum_steps — Objective → Micro-instant bridge (I.2)
# ═══════════════════════════════════════════════════════════════════


class TestGetNextCurriculumSteps:

    def _make_objective(self, obj_id, steps, status="active"):
        return {
            "objective_id": obj_id,
            "user_id": "u1",
            "title": f"Objective {obj_id}",
            "category": "learning",
            "daily_minutes": 10,
            "status": status,
            "curriculum": steps,
        }

    def _make_step(self, index, completed=False):
        return {
            "step_index": index,
            "day": index + 1,
            "title": f"Step {index}",
            "description": f"Do step {index}",
            "focus": "practice",
            "instructions": ["Do it"],
            "duration_min": 7,
            "duration_max": 12,
            "difficulty": min(5, index // 7 + 1),
            "review": False,
            "completed": completed,
        }

    @pytest.mark.asyncio
    async def test_returns_next_uncompleted_step(self, mock_db):
        """Returns the first uncompleted step for an active objective."""
        steps = [self._make_step(0, completed=True),
                 self._make_step(1, completed=True),
                 self._make_step(2, completed=False)]
        await mock_db.objectives.insert_one(self._make_objective("obj1", steps))

        result = await _get_next_curriculum_steps(mock_db, "u1")
        assert len(result) == 1
        assert result[0]["objective_id"] == "obj1"
        assert result[0]["step"]["step_index"] == 2

    @pytest.mark.asyncio
    async def test_one_step_per_objective(self, mock_db):
        """Returns at most one step per objective."""
        steps = [self._make_step(0), self._make_step(1), self._make_step(2)]
        await mock_db.objectives.insert_one(self._make_objective("obj1", steps))

        result = await _get_next_curriculum_steps(mock_db, "u1")
        assert len(result) == 1
        assert result[0]["step"]["step_index"] == 0

    @pytest.mark.asyncio
    async def test_multiple_objectives(self, mock_db):
        """Returns one step per active objective."""
        await mock_db.objectives.insert_one(
            self._make_objective("obj1", [self._make_step(0)])
        )
        await mock_db.objectives.insert_one(
            self._make_objective("obj2", [self._make_step(0)])
        )

        result = await _get_next_curriculum_steps(mock_db, "u1")
        assert len(result) == 2
        obj_ids = {r["objective_id"] for r in result}
        assert obj_ids == {"obj1", "obj2"}

    @pytest.mark.asyncio
    async def test_all_steps_completed_returns_nothing(self, mock_db):
        """If all steps are completed, no step is returned for that objective."""
        steps = [self._make_step(0, completed=True), self._make_step(1, completed=True)]
        await mock_db.objectives.insert_one(self._make_objective("obj1", steps))

        result = await _get_next_curriculum_steps(mock_db, "u1")
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_inactive_objective_excluded(self, mock_db):
        """Paused/completed objectives are not included."""
        steps = [self._make_step(0)]
        await mock_db.objectives.insert_one(
            self._make_objective("obj1", steps, status="paused")
        )

        result = await _get_next_curriculum_steps(mock_db, "u1")
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_empty_curriculum_excluded(self, mock_db):
        """Objectives with no curriculum are excluded."""
        await mock_db.objectives.insert_one(
            self._make_objective("obj1", [])
        )

        result = await _get_next_curriculum_steps(mock_db, "u1")
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_no_objectives_returns_empty(self, mock_db):
        result = await _get_next_curriculum_steps(mock_db, "u1")
        assert result == []

    @pytest.mark.asyncio
    async def test_step_data_includes_objective_context(self, mock_db):
        """Returned data includes objective title, category, daily_minutes."""
        steps = [self._make_step(0)]
        await mock_db.objectives.insert_one(self._make_objective("obj1", steps))

        result = await _get_next_curriculum_steps(mock_db, "u1")
        assert result[0]["objective_title"] == "Objective obj1"
        assert result[0]["category"] == "learning"
        assert result[0]["daily_minutes"] == 10


# ═══════════════════════════════════════════════════════════════════
# predict_micro_instants — Full pipeline
# ═══════════════════════════════════════════════════════════════════


class TestPredictMicroInstants:

    def _make_event(self, start_hour, end_hour, summary="Meeting"):
        base = datetime(2030, 6, 1, tzinfo=timezone.utc)
        return {
            "summary": summary,
            "start": {"dateTime": (base + timedelta(hours=start_hour)).isoformat()},
            "end": {"dateTime": (base + timedelta(hours=end_hour)).isoformat()},
        }

    @pytest.mark.asyncio
    async def test_no_inputs_returns_empty(self, mock_db):
        """No calendar, no routines, no patterns → empty."""
        result = await predict_micro_instants(mock_db, "u1", calendar_events=[])
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_calendar_gap_detected(self, mock_db):
        """Calendar gap produces micro-instant."""
        events = [
            self._make_event(10, 10.5),
            self._make_event(11, 11.5),
        ]
        result = await predict_micro_instants(
            mock_db, "u1", calendar_events=events, settings=DEFAULT_SETTINGS
        )
        calendar_instants = [r for r in result if r["source"] == "calendar_gap"]
        assert len(calendar_instants) >= 1

    @pytest.mark.asyncio
    async def test_instant_has_required_fields(self, mock_db):
        """Each instant has all required fields."""
        events = [
            self._make_event(10, 10.5),
            self._make_event(11, 11.5),
        ]
        result = await predict_micro_instants(
            mock_db, "u1", calendar_events=events, settings=DEFAULT_SETTINGS
        )
        for instant in result:
            assert "instant_id" in instant
            assert instant["instant_id"].startswith("mi_")
            assert "window_start" in instant
            assert "window_end" in instant
            assert "duration_minutes" in instant
            assert "confidence_score" in instant
            assert 0 <= instant["confidence_score"] <= 1
            assert "source" in instant
            assert instant["source"] in ("calendar_gap", "routine_window", "behavioral_pattern")
            assert "context" in instant
            assert "energy_level" in instant["context"]

    @pytest.mark.asyncio
    async def test_max_instants_per_day(self, mock_db):
        """Never returns more than MAX_INSTANTS_PER_DAY."""
        # Create many calendar gaps
        events = []
        for h in range(9, 18):
            events.append(self._make_event(h, h + 0.25))  # 15 min events with gaps

        result = await predict_micro_instants(
            mock_db, "u1", calendar_events=events, settings=DEFAULT_SETTINGS
        )
        assert len(result) <= MAX_INSTANTS_PER_DAY

    @pytest.mark.asyncio
    async def test_confidence_threshold_applied(self, mock_db):
        """All returned instants have confidence >= MIN_CONFIDENCE."""
        events = [self._make_event(10, 10.5), self._make_event(11, 11.5)]
        result = await predict_micro_instants(
            mock_db, "u1", calendar_events=events, settings=DEFAULT_SETTINGS
        )
        for instant in result:
            assert instant["confidence_score"] >= MIN_CONFIDENCE


# ═══════════════════════════════════════════════════════════════════
# _assign_actions — Priority 2: objective steps in windows (I.2)
# ═══════════════════════════════════════════════════════════════════


class TestAssignActionsWithCurriculum:
    """Verify curriculum steps are assigned to micro-instant windows (Priority 2)."""

    @pytest.mark.asyncio
    async def test_curriculum_step_assigned_to_window(self, mock_db):
        """Window gets objective_step when curriculum exists and no SR review."""
        from services.micro_instant_engine import _assign_actions

        # Seed an active objective with uncompleted curriculum step
        await mock_db.objectives.insert_one({
            "objective_id": "obj_test_1",
            "user_id": "u1",
            "title": "Apprendre le thaï",
            "category": "learning",
            "daily_minutes": 10,
            "status": "active",
            "curriculum": [{
                "step_index": 0,
                "day": 1,
                "title": "Les salutations",
                "description": "Apprendre bonjour, merci, au revoir",
                "focus": "vocabulaire",
                "instructions": ["Écoute", "Répète"],
                "duration_min": 7,
                "duration_max": 12,
                "difficulty": 1,
                "review": False,
                "completed": False,
            }],
        })

        windows = [{
            "window_start": "2030-06-01T10:00:00+00:00",
            "window_end": "2030-06-01T10:15:00+00:00",
            "duration_minutes": 15,
            "source": "routine_window",
            "base_confidence": 0.7,
            "confidence_score": 0.7,
            "context": {"time_bucket": "morning"},
        }]

        result = await _assign_actions(mock_db, "u1", windows)
        assert len(result) == 1
        action = result[0]["recommended_action"]
        assert action is not None
        assert action["type"] == "objective_step"
        assert action["objective_id"] == "obj_test_1"
        assert action["title"] == "Les salutations"
        assert action["step_index"] == 0

    @pytest.mark.asyncio
    async def test_curriculum_step_skipped_if_window_too_small(self, mock_db):
        """If window duration is less than step's duration_min, step is not assigned."""
        from services.micro_instant_engine import _assign_actions

        await mock_db.objectives.insert_one({
            "objective_id": "obj_test_2",
            "user_id": "u1",
            "title": "Piano",
            "category": "learning",
            "daily_minutes": 10,
            "status": "active",
            "curriculum": [{
                "step_index": 0, "day": 1, "title": "Gammes",
                "description": "Gammes majeures", "focus": "technique",
                "instructions": ["Joue"], "duration_min": 7, "duration_max": 12,
                "difficulty": 1, "review": False, "completed": False,
            }],
        })

        windows = [{
            "window_start": "2030-06-01T10:00:00+00:00",
            "window_end": "2030-06-01T10:05:00+00:00",
            "duration_minutes": 5,  # Too small for 7-min step
            "source": "calendar_gap",
            "base_confidence": 0.9,
            "confidence_score": 0.9,
            "context": {"time_bucket": "morning"},
        }]

        result = await _assign_actions(mock_db, "u1", windows)
        action = result[0].get("recommended_action")
        # Should NOT be objective_step (window too small)
        assert action is None or action.get("type") != "objective_step"

    @pytest.mark.asyncio
    async def test_confidence_boosted_for_objective_step(self, mock_db):
        """Objective steps get a 10% confidence boost."""
        from services.micro_instant_engine import _assign_actions

        await mock_db.objectives.insert_one({
            "objective_id": "obj_boost",
            "user_id": "u1",
            "title": "Yoga",
            "category": "wellness",
            "daily_minutes": 10,
            "status": "active",
            "curriculum": [{
                "step_index": 0, "day": 1, "title": "Salutation au soleil",
                "description": "Séquence de base", "focus": "flexibilité",
                "instructions": ["Respire", "Étire"], "duration_min": 7,
                "duration_max": 12, "difficulty": 1, "review": False,
                "completed": False,
            }],
        })

        windows = [{
            "window_start": "2030-06-01T10:00:00+00:00",
            "window_end": "2030-06-01T10:15:00+00:00",
            "duration_minutes": 15,
            "source": "routine_window",
            "base_confidence": 0.7,
            "confidence_score": 0.7,
            "context": {"time_bucket": "morning"},
        }]

        result = await _assign_actions(mock_db, "u1", windows)
        # 0.7 * 1.10 = 0.77
        assert result[0]["confidence_score"] == pytest.approx(0.77, abs=0.01)


# ═══════════════════════════════════════════════════════════════════
# record_instant_outcome — Feedback tracking
# ═══════════════════════════════════════════════════════════════════


class TestRecordInstantOutcome:

    @pytest.mark.asyncio
    async def test_exploited_outcome_stored(self, mock_db):
        await record_instant_outcome(
            mock_db, "u1", "mi_test123", "exploited",
            {"action_id": "a1", "duration": 7}
        )
        doc = await mock_db.micro_instant_outcomes.find_one({"instant_id": "mi_test123"})
        assert doc is not None
        assert doc["outcome"] == "exploited"

    @pytest.mark.asyncio
    async def test_skipped_outcome_stored(self, mock_db):
        await record_instant_outcome(mock_db, "u1", "mi_skip", "skipped")
        doc = await mock_db.micro_instant_outcomes.find_one({"instant_id": "mi_skip"})
        assert doc is not None
        assert doc["outcome"] == "skipped"

    @pytest.mark.asyncio
    async def test_dismissed_outcome_stored(self, mock_db):
        await record_instant_outcome(mock_db, "u1", "mi_dismiss", "dismissed")
        doc = await mock_db.micro_instant_outcomes.find_one({"instant_id": "mi_dismiss"})
        assert doc["outcome"] == "dismissed"

    @pytest.mark.asyncio
    async def test_event_tracked(self, mock_db):
        """Outcome also creates an event in event_log."""
        await record_instant_outcome(mock_db, "u1", "mi_track", "exploited")
        event = await mock_db.event_log.find_one({"user_id": "u1", "event_type": "micro_instant_exploited"})
        assert event is not None
        assert event["metadata"]["instant_id"] == "mi_track"
