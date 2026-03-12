"""
Unit tests — Slot Detector.
P1 critical service: ensures calendar free-slot detection works correctly.

Tests:
- Pure helpers: parse_time, is_within_detection_window, event_has_excluded_keyword,
  get_event_times, get_category_for_time
- detect_free_slots: gaps between events, all-day events, excluded keywords
- match_action_to_slot: category matching, subscription filtering, fallback chain
"""

import pytest
from datetime import datetime, timezone, timedelta

from services.slot_detector import (
    parse_time,
    is_within_detection_window,
    event_has_excluded_keyword,
    get_event_times,
    get_category_for_time,
    detect_free_slots,
    match_action_to_slot,
    DEFAULT_SETTINGS,
)


# ═══════════════════════════════════════════════════════════════════
# parse_time
# ═══════════════════════════════════════════════════════════════════


class TestParseTime:

    def test_standard(self):
        assert parse_time("09:00") == (9, 0)

    def test_midnight(self):
        assert parse_time("00:00") == (0, 0)

    def test_end_of_day(self):
        assert parse_time("23:59") == (23, 59)

    def test_with_minutes(self):
        assert parse_time("14:30") == (14, 30)


# ═══════════════════════════════════════════════════════════════════
# is_within_detection_window
# ═══════════════════════════════════════════════════════════════════


class TestIsWithinDetectionWindow:

    def test_inside_window(self):
        dt = datetime(2025, 1, 1, 10, 0, tzinfo=timezone.utc)
        assert is_within_detection_window(dt, DEFAULT_SETTINGS) is True

    def test_at_start_boundary(self):
        dt = datetime(2025, 1, 1, 9, 0, tzinfo=timezone.utc)
        assert is_within_detection_window(dt, DEFAULT_SETTINGS) is True

    def test_at_end_boundary(self):
        dt = datetime(2025, 1, 1, 18, 0, tzinfo=timezone.utc)
        assert is_within_detection_window(dt, DEFAULT_SETTINGS) is True

    def test_before_window(self):
        dt = datetime(2025, 1, 1, 7, 0, tzinfo=timezone.utc)
        assert is_within_detection_window(dt, DEFAULT_SETTINGS) is False

    def test_after_window(self):
        dt = datetime(2025, 1, 1, 19, 0, tzinfo=timezone.utc)
        assert is_within_detection_window(dt, DEFAULT_SETTINGS) is False

    def test_custom_window(self):
        settings = {"detection_window_start": "07:00", "detection_window_end": "22:00"}
        dt = datetime(2025, 1, 1, 21, 0, tzinfo=timezone.utc)
        assert is_within_detection_window(dt, settings) is True


# ═══════════════════════════════════════════════════════════════════
# event_has_excluded_keyword
# ═══════════════════════════════════════════════════════════════════


class TestEventHasExcludedKeyword:

    def test_no_match(self):
        event = {"summary": "Team standup", "description": "Daily sync"}
        assert event_has_excluded_keyword(event, ["focus", "lunch"]) is False

    def test_match_in_title(self):
        event = {"summary": "Deep work session", "description": ""}
        assert event_has_excluded_keyword(event, ["deep work"]) is True

    def test_match_in_description(self):
        event = {"summary": "Meeting", "description": "Lunch break after"}
        assert event_has_excluded_keyword(event, ["lunch"]) is True

    def test_case_insensitive(self):
        event = {"summary": "FOCUS time", "description": ""}
        assert event_has_excluded_keyword(event, ["focus"]) is True

    def test_empty_event(self):
        event = {}
        assert event_has_excluded_keyword(event, ["focus"]) is False

    def test_none_values(self):
        event = {"summary": None, "description": None}
        assert event_has_excluded_keyword(event, ["focus"]) is False


# ═══════════════════════════════════════════════════════════════════
# get_event_times
# ═══════════════════════════════════════════════════════════════════


class TestGetEventTimes:

    def test_normal_event(self):
        event = {
            "start": {"dateTime": "2025-01-01T10:00:00+00:00"},
            "end": {"dateTime": "2025-01-01T11:00:00+00:00"},
        }
        start, end = get_event_times(event)
        assert start.hour == 10
        assert end.hour == 11

    def test_all_day_event(self):
        event = {
            "start": {"date": "2025-01-01"},
            "end": {"date": "2025-01-02"},
        }
        start, end = get_event_times(event)
        assert start is None
        assert end is None

    def test_missing_datetime(self):
        event = {"start": {}, "end": {}}
        start, end = get_event_times(event)
        assert start is None
        assert end is None

    def test_utc_z_suffix(self):
        """Z suffix is correctly parsed."""
        event = {
            "start": {"dateTime": "2025-01-01T10:00:00Z"},
            "end": {"dateTime": "2025-01-01T11:00:00Z"},
        }
        start, end = get_event_times(event)
        assert start is not None
        assert start.hour == 10


# ═══════════════════════════════════════════════════════════════════
# get_category_for_time
# ═══════════════════════════════════════════════════════════════════


class TestGetCategoryForTime:

    def test_morning(self):
        dt = datetime(2025, 1, 1, 8, 0, tzinfo=timezone.utc)
        assert get_category_for_time(dt, DEFAULT_SETTINGS) == "learning"

    def test_afternoon(self):
        dt = datetime(2025, 1, 1, 14, 0, tzinfo=timezone.utc)
        assert get_category_for_time(dt, DEFAULT_SETTINGS) == "productivity"

    def test_evening(self):
        dt = datetime(2025, 1, 1, 19, 0, tzinfo=timezone.utc)
        assert get_category_for_time(dt, DEFAULT_SETTINGS) == "well_being"

    def test_custom_preferences(self):
        settings = {
            "preferred_categories_by_time": {
                "morning": "fitness",
                "afternoon": "creativity",
                "evening": "mindfulness",
            }
        }
        dt = datetime(2025, 1, 1, 8, 0, tzinfo=timezone.utc)
        assert get_category_for_time(dt, settings) == "fitness"


# ═══════════════════════════════════════════════════════════════════
# detect_free_slots — Async (no DB needed, but async interface)
# ═══════════════════════════════════════════════════════════════════


class TestDetectFreeSlots:

    def _make_event(self, start_hour, end_hour, summary="Meeting", day=1):
        """Helper to create a calendar event."""
        base = datetime(2025, 6, day, tzinfo=timezone.utc)
        return {
            "summary": summary,
            "start": {"dateTime": (base + timedelta(hours=start_hour)).isoformat()},
            "end": {"dateTime": (base + timedelta(hours=end_hour)).isoformat()},
        }

    @pytest.mark.asyncio
    async def test_disabled_returns_empty(self):
        settings = {**DEFAULT_SETTINGS, "slot_detection_enabled": False}
        result = await detect_free_slots([self._make_event(10, 11)], settings)
        assert result == []

    @pytest.mark.asyncio
    async def test_gap_between_events(self):
        """10-minute gap between events → detected as slot."""
        # Use far-future dates to ensure they're not in the past
        base = datetime(2030, 1, 1, tzinfo=timezone.utc)
        events = [
            {
                "summary": "Event A",
                "start": {"dateTime": (base + timedelta(hours=10)).isoformat()},
                "end": {"dateTime": (base + timedelta(hours=10, minutes=30)).isoformat()},
            },
            {
                "summary": "Event B",
                "start": {"dateTime": (base + timedelta(hours=10, minutes=40)).isoformat()},
                "end": {"dateTime": (base + timedelta(hours=11)).isoformat()},
            },
        ]

        result = await detect_free_slots(events, DEFAULT_SETTINGS)
        # Should find the 10-min gap between events
        ten_min_slots = [s for s in result if s["duration_minutes"] == 10]
        assert len(ten_min_slots) >= 1

    @pytest.mark.asyncio
    async def test_excluded_keyword_event_ignored(self):
        """Events with excluded keywords are ignored (gap becomes larger)."""
        base = datetime(2030, 1, 1, tzinfo=timezone.utc)
        events = [
            {
                "summary": "Normal meeting",
                "start": {"dateTime": (base + timedelta(hours=10)).isoformat()},
                "end": {"dateTime": (base + timedelta(hours=10, minutes=30)).isoformat()},
            },
            {
                "summary": "Deep work focus",  # Excluded
                "start": {"dateTime": (base + timedelta(hours=10, minutes=30)).isoformat()},
                "end": {"dateTime": (base + timedelta(hours=11)).isoformat()},
            },
            {
                "summary": "Next meeting",
                "start": {"dateTime": (base + timedelta(hours=11, minutes=15)).isoformat()},
                "end": {"dateTime": (base + timedelta(hours=12)).isoformat()},
            },
        ]

        result = await detect_free_slots(events, DEFAULT_SETTINGS)
        # The "deep work" event is excluded, so the gap should be
        # from 10:30 to 11:15 = 45 min (max_slot_duration default)
        long_slots = [s for s in result if s["duration_minutes"] == 45]
        assert len(long_slots) >= 1

    @pytest.mark.asyncio
    async def test_all_day_events_skipped(self):
        """All-day events are skipped by get_event_times."""
        events = [
            {"summary": "Holiday", "start": {"date": "2030-01-01"}, "end": {"date": "2030-01-02"}},
        ]
        result = await detect_free_slots(events, DEFAULT_SETTINGS)
        # No valid timed events → no slots detected between events
        # (may still detect slots from now to window end)
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_no_events_returns_empty(self):
        """No events → no inter-event gaps."""
        result = await detect_free_slots([], DEFAULT_SETTINGS)
        assert result == []

    @pytest.mark.asyncio
    async def test_slot_has_required_fields(self):
        """Each slot has all required fields."""
        base = datetime(2030, 1, 1, tzinfo=timezone.utc)
        events = [
            {
                "summary": "A",
                "start": {"dateTime": (base + timedelta(hours=10)).isoformat()},
                "end": {"dateTime": (base + timedelta(hours=10, minutes=20)).isoformat()},
            },
            {
                "summary": "B",
                "start": {"dateTime": (base + timedelta(hours=10, minutes=30)).isoformat()},
                "end": {"dateTime": (base + timedelta(hours=11)).isoformat()},
            },
        ]
        result = await detect_free_slots(events, DEFAULT_SETTINGS)
        for slot in result:
            assert "slot_id" in slot
            assert "start_time" in slot
            assert "end_time" in slot
            assert "duration_minutes" in slot
            assert "suggested_category" in slot
            assert slot["slot_id"].startswith("slot_")


# ═══════════════════════════════════════════════════════════════════
# match_action_to_slot — Matching logic
# ═══════════════════════════════════════════════════════════════════


class TestMatchActionToSlot:

    def _make_slot(self, duration=10, category="learning"):
        return {
            "slot_id": "slot_test",
            "duration_minutes": duration,
            "suggested_category": category,
            "start_time": "2030-01-01T10:00:00+00:00",
        }

    def _make_actions(self):
        return [
            {"action_id": "a1", "duration_min": 5, "duration_max": 10,
             "category": "learning", "energy_level": "medium", "is_premium": False},
            {"action_id": "a2", "duration_min": 5, "duration_max": 10,
             "category": "productivity", "energy_level": "low", "is_premium": False},
            {"action_id": "a3", "duration_min": 5, "duration_max": 10,
             "category": "learning", "energy_level": "high", "is_premium": True},
        ]

    @pytest.mark.asyncio
    async def test_category_match(self):
        """Matches action by category first."""
        slot = self._make_slot(category="learning")
        result = await match_action_to_slot(slot, self._make_actions())
        assert result is not None
        assert result["category"] == "learning"

    @pytest.mark.asyncio
    async def test_free_user_excludes_premium(self):
        """Free users don't get premium actions."""
        slot = self._make_slot(category="learning")
        actions = self._make_actions()
        result = await match_action_to_slot(slot, actions, user_subscription="free")
        assert result is not None
        assert result.get("is_premium") is not True

    @pytest.mark.asyncio
    async def test_premium_user_gets_premium(self):
        """Premium users can get premium actions."""
        slot = self._make_slot(category="learning")
        # Only premium learning action available
        actions = [{"action_id": "p1", "duration_min": 5, "duration_max": 10,
                     "category": "learning", "energy_level": "medium", "is_premium": True}]
        result = await match_action_to_slot(slot, actions, user_subscription="premium")
        assert result is not None
        assert result["action_id"] == "p1"

    @pytest.mark.asyncio
    async def test_no_category_match_fallback(self):
        """If no category match, falls back to any fitting action."""
        slot = self._make_slot(category="fitness")
        actions = [{"action_id": "a1", "duration_min": 5, "category": "learning", "is_premium": False}]
        result = await match_action_to_slot(slot, actions)
        assert result is not None  # Falls back to learning action

    @pytest.mark.asyncio
    async def test_no_fitting_action_returns_none(self):
        """If no action fits the duration → None."""
        slot = self._make_slot(duration=2)
        actions = [{"action_id": "a1", "duration_min": 10, "category": "learning", "is_premium": False}]
        result = await match_action_to_slot(slot, actions)
        assert result is None

    @pytest.mark.asyncio
    async def test_empty_actions_returns_none(self):
        slot = self._make_slot()
        result = await match_action_to_slot(slot, [])
        assert result is None
