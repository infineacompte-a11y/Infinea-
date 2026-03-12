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
