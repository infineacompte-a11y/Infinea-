"""
Unit tests — Contextual Message Composer (F.3 Push Contextuel Intelligent).
Tests compose_instant_message() and compose_throttle_summary() from
services/contextual_messages.py.

Pure function tests — no DB, no async.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from services.contextual_messages import (
    compose_instant_message,
    compose_throttle_summary,
    MAX_TITLE_CHARS,
    MAX_BODY_CHARS,
)


# ── Helpers ──

def _make_instant(
    source="calendar_gap",
    time_bucket="afternoon",
    duration=15,
    action_type="micro_action",
    action_title="Apprendre 5 mots",
    action_id="action_test_001",
    confidence=0.80,
    days_overdue=0,
    routine_name=None,
    skill_name=None,
    recommended_action=True,
):
    """Build a test micro-instant dict with sensible defaults."""
    now = datetime.now(timezone.utc)
    context = {
        "time_bucket": time_bucket,
        "energy_level": "medium",
        "trigger": "gap_between_events",
    }
    if routine_name:
        context["routine_name"] = routine_name

    action = None
    if recommended_action:
        action = {
            "type": action_type,
            "action_id": action_id,
            "title": action_title,
            "category": "learning",
            "duration_min": 5,
            "duration_max": 10,
            "energy_level": "medium",
            "score": 0.75,
        }
        if days_overdue:
            action["days_overdue"] = days_overdue
        if skill_name:
            action["skill"] = skill_name

    return {
        "instant_id": "mi_test_001",
        "window_start": (now + timedelta(minutes=15)).isoformat(),
        "window_end": (now + timedelta(minutes=30)).isoformat(),
        "duration_minutes": duration,
        "confidence_score": confidence,
        "source": source,
        "recommended_action": action,
        "context": context,
    }


# ═══════════════════════════════════════════════════════════════════
# TestComposeInstantMessage
# ═══════════════════════════════════════════════════════════════════


class TestComposeInstantMessage:

    @patch("services.contextual_messages.random.choice", side_effect=lambda pool: pool[0])
    def test_calendar_gap_morning(self, _mock_choice):
        """calendar_gap + morning → title contains duration, body mentions action."""
        instant = _make_instant(source="calendar_gap", time_bucket="morning", duration=20)
        result = compose_instant_message(instant)

        assert "20" in result["title"]
        assert "body" in result
        assert result["icon"] == "zap"  # micro_action icon
        assert result["tag"] == "micro_instant_mi_test_001"
        assert len(result["actions"]) == 2

    @patch("services.contextual_messages.random.choice", side_effect=lambda pool: pool[0])
    def test_routine_window_evening(self, _mock_choice):
        """routine_window + evening → title contains routine_name."""
        instant = _make_instant(
            source="routine_window",
            time_bucket="evening",
            routine_name="Meditation",
            action_title="Meditation du soir",
        )
        result = compose_instant_message(instant)

        assert "Meditation" in result["title"]

    @patch("services.contextual_messages.random.choice", side_effect=lambda pool: pool[0])
    def test_behavioral_pattern_afternoon(self, _mock_choice):
        """behavioral_pattern + afternoon → mentions habitual behavior."""
        instant = _make_instant(source="behavioral_pattern", time_bucket="afternoon")
        result = compose_instant_message(instant)

        assert "habituel" in result["title"] or "créneau" in result["title"]
        assert "souvent" in result["body"] or "productif" in result["body"]

    @patch("services.contextual_messages.random.choice", side_effect=lambda pool: pool[0])
    def test_sr_normal_priority(self, _mock_choice):
        """action type=spaced_repetition, days_overdue=1 → SR template used."""
        instant = _make_instant(
            source="calendar_gap",
            time_bucket="morning",
            action_type="spaced_repetition",
            days_overdue=1,
            skill_name="Thai basics",
        )
        result = compose_instant_message(instant)

        assert "vision" in result["title"] or "\U0001f9e0" in result["title"]
        assert result["icon"] == "brain"

    @patch("services.contextual_messages.random.choice", side_effect=lambda pool: pool[0])
    def test_sr_urgent_priority(self, _mock_choice):
        """action type=spaced_repetition, days_overdue=5 → urgent SR template (🔴)."""
        instant = _make_instant(
            source="calendar_gap",
            time_bucket="afternoon",
            action_type="spaced_repetition",
            days_overdue=5,
            skill_name="Vocabulaire",
        )
        result = compose_instant_message(instant)

        assert "\U0001f534" in result["title"]  # 🔴
        assert result["icon"] == "brain"

    @patch("services.contextual_messages.random.choice", side_effect=lambda pool: pool[0])
    def test_no_action(self, _mock_choice):
        """recommended_action=None → generic message with 'explore' button."""
        instant = _make_instant(recommended_action=False)
        instant["recommended_action"] = None
        result = compose_instant_message(instant)

        action_names = [a["action"] for a in result["actions"]]
        assert "explore" in action_names
        assert "skip" in action_names
        assert result["url"] == "/micro-instants"

    @patch("services.contextual_messages.random.choice", side_effect=lambda pool: pool[0])
    def test_title_length_limit(self, _mock_choice):
        """Very long values → title capped at MAX_TITLE_CHARS."""
        instant = _make_instant(
            source="routine_window",
            time_bucket="morning",
            routine_name="A" * 200,
        )
        result = compose_instant_message(instant)
        assert len(result["title"]) <= MAX_TITLE_CHARS

    @patch("services.contextual_messages.random.choice", side_effect=lambda pool: pool[0])
    def test_body_length_limit(self, _mock_choice):
        """Very long values → body capped at MAX_BODY_CHARS."""
        instant = _make_instant(action_title="B" * 200)
        result = compose_instant_message(instant)
        assert len(result["body"]) <= MAX_BODY_CHARS


# ═══════════════════════════════════════════════════════════════════
# TestComposeThrottleSummary
# ═══════════════════════════════════════════════════════════════════


class TestComposeThrottleSummary:

    def test_quota_exhausted(self):
        """sent_today=3, max=3 → returns None."""
        result = compose_throttle_summary(sent_today=3, max_daily=3)
        assert result is None

    def test_has_remaining(self):
        """sent_today=1, max=3 → returns dict with remaining=2."""
        result = compose_throttle_summary(sent_today=1, max_daily=3)
        assert result is not None
        assert result["remaining"] == 2
        assert result["sent_today"] == 1
        assert result["max_daily"] == 3
        assert result["is_last"] is False

    def test_last_push(self):
        """sent_today=2, max=3 → is_last=True."""
        result = compose_throttle_summary(sent_today=2, max_daily=3)
        assert result is not None
        assert result["remaining"] == 1
        assert result["is_last"] is True
