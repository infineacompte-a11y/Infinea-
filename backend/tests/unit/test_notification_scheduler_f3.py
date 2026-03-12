"""
Unit tests — Notification Scheduler F.3 helpers.
Tests _count_instant_pushes_today(), _last_instant_push_time(), _is_quiet_hours(),
and generate_contextual_instant_notifications() from services/notification_scheduler.py.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, AsyncMock

from services.notification_scheduler import (
    _count_instant_pushes_today,
    _last_instant_push_time,
    _is_quiet_hours,
    generate_contextual_instant_notifications,
    MAX_INSTANT_PUSHES_PER_DAY,
)


# ── Shared test data ──

TEST_USER_ID = "user_test_abc123"


def _make_test_instant(confidence=0.80, minutes_ahead=15):
    """Build a test micro-instant matching predict_micro_instants output."""
    now = datetime.now(timezone.utc)
    return {
        "instant_id": "mi_test_push_001",
        "window_start": (now + timedelta(minutes=minutes_ahead)).isoformat(),
        "window_end": (now + timedelta(minutes=minutes_ahead + 15)).isoformat(),
        "duration_minutes": 15,
        "confidence_score": confidence,
        "source": "calendar_gap",
        "recommended_action": {
            "type": "micro_action",
            "action_id": "action_test_001",
            "title": "Apprendre 5 mots",
            "category": "learning",
            "duration_min": 5,
            "duration_max": 10,
            "energy_level": "medium",
            "score": 0.75,
        },
        "context": {
            "time_bucket": "afternoon",
            "energy_level": "medium",
            "trigger": "gap_between_events",
        },
    }


# ═══════════════════════════════════════════════════════════════════
# TestCountInstantPushesToday
# ═══════════════════════════════════════════════════════════════════


class TestCountInstantPushesToday:

    @pytest.mark.asyncio
    async def test_count_zero(self, mock_db):
        """No notifications → returns 0."""
        count = await _count_instant_pushes_today(mock_db, TEST_USER_ID)
        assert count == 0

    @pytest.mark.asyncio
    async def test_count_with_pushes(self, mock_db):
        """Insert 2 micro_instant_push notifs today → returns 2."""
        now_iso = datetime.now(timezone.utc).isoformat()
        for i in range(2):
            await mock_db.notifications.insert_one({
                "notification_id": f"notif_test_{i}",
                "user_id": TEST_USER_ID,
                "type": "micro_instant_push",
                "title": f"Test push {i}",
                "message": "Test body",
                "read": False,
                "created_at": now_iso,
            })

        count = await _count_instant_pushes_today(mock_db, TEST_USER_ID)
        assert count == 2


# ═══════════════════════════════════════════════════════════════════
# TestLastInstantPushTime
# ═══════════════════════════════════════════════════════════════════


class TestLastInstantPushTime:

    @pytest.mark.asyncio
    async def test_no_previous_push(self, mock_db):
        """Empty DB → returns None."""
        result = await _last_instant_push_time(mock_db, TEST_USER_ID)
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_latest(self, mock_db):
        """Insert 2 pushes at different times → returns most recent."""
        older_ts = (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat()
        newer_ts = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()

        await mock_db.notifications.insert_one({
            "notification_id": "notif_old",
            "user_id": TEST_USER_ID,
            "type": "micro_instant_push",
            "created_at": older_ts,
        })
        await mock_db.notifications.insert_one({
            "notification_id": "notif_new",
            "user_id": TEST_USER_ID,
            "type": "micro_instant_push",
            "created_at": newer_ts,
        })

        result = await _last_instant_push_time(mock_db, TEST_USER_ID)
        assert result == newer_ts


# ═══════════════════════════════════════════════════════════════════
# TestIsQuietHours
# ═══════════════════════════════════════════════════════════════════


class TestIsQuietHours:

    @patch("services.notification_scheduler.datetime")
    def test_quiet_at_23h(self, mock_datetime):
        """23:00 UTC, no offset → True."""
        mock_now = datetime(2026, 3, 12, 23, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *a, **kw: datetime(*a, **kw)

        assert _is_quiet_hours(None) is True

    @patch("services.notification_scheduler.datetime")
    def test_not_quiet_at_10h(self, mock_datetime):
        """10:00 UTC, no offset → False."""
        mock_now = datetime(2026, 3, 12, 10, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *a, **kw: datetime(*a, **kw)

        assert _is_quiet_hours(None) is False

    @patch("services.notification_scheduler.datetime")
    def test_quiet_with_offset(self, mock_datetime):
        """15:00 UTC + offset 8 = 23:00 local → True."""
        mock_now = datetime(2026, 3, 12, 15, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *a, **kw: datetime(*a, **kw)

        assert _is_quiet_hours(8) is True

    @patch("services.notification_scheduler.datetime")
    def test_not_quiet_with_offset(self, mock_datetime):
        """23:00 UTC + offset -6 = 17:00 local → False."""
        mock_now = datetime(2026, 3, 12, 23, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *a, **kw: datetime(*a, **kw)

        assert _is_quiet_hours(-6) is False


# ═══════════════════════════════════════════════════════════════════
# TestGenerateContextualInstantNotifications
# ═══════════════════════════════════════════════════════════════════


class TestGenerateContextualInstantNotifications:

    async def _seed_active_user(self, db, user_id=TEST_USER_ID, tz_offset=None):
        """Insert an active user with recent session date."""
        await db.users.insert_one({
            "user_id": user_id,
            "email": "test@infinea.app",
            "name": "Test User",
            "subscription": "free",
            "last_session_date": datetime.now(timezone.utc).date().isoformat(),
            "timezone_offset": tz_offset,
        })

    @pytest.mark.asyncio
    @patch("services.notification_scheduler._is_quiet_hours", return_value=False)
    @patch("services.notification_scheduler._create_notification")
    async def test_sends_push_for_qualifying_instant(
        self, mock_create_notif, mock_quiet, mock_db
    ):
        """User with predicted instant, confidence 0.80 → push sent."""
        await self._seed_active_user(mock_db)

        test_instant = _make_test_instant(confidence=0.80, minutes_ahead=15)

        mock_create_notif.return_value = {
            "notification_id": "notif_test_new",
            "user_id": TEST_USER_ID,
            "type": "micro_instant_push",
            "title": "Test",
            "message": "Test",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        with patch(
            "services.micro_instant_engine.predict_micro_instants",
            new_callable=AsyncMock,
            return_value=[test_instant],
        ), patch(
            "services.event_tracker.track_event",
            new_callable=AsyncMock,
        ):
            await generate_contextual_instant_notifications(mock_db)

        mock_create_notif.assert_called_once()
        call_args = mock_create_notif.call_args
        assert call_args[0][1] == TEST_USER_ID
        assert call_args[0][2] == "micro_instant_push"

    @pytest.mark.asyncio
    @patch("services.notification_scheduler._is_quiet_hours", return_value=False)
    @patch("services.notification_scheduler._create_notification")
    async def test_throttled_by_daily_limit(
        self, mock_create_notif, mock_quiet, mock_db
    ):
        """User already has 3 pushes today → no new push."""
        await self._seed_active_user(mock_db)

        now_iso = datetime.now(timezone.utc).isoformat()
        for i in range(MAX_INSTANT_PUSHES_PER_DAY):
            await mock_db.notifications.insert_one({
                "notification_id": f"notif_existing_{i}",
                "user_id": TEST_USER_ID,
                "type": "micro_instant_push",
                "title": f"Existing push {i}",
                "message": "Body",
                "read": False,
                "created_at": now_iso,
            })

        await generate_contextual_instant_notifications(mock_db)

        mock_create_notif.assert_not_called()

    @pytest.mark.asyncio
    @patch("services.notification_scheduler._is_quiet_hours", return_value=False)
    @patch("services.notification_scheduler._create_notification")
    async def test_throttled_by_interval(
        self, mock_create_notif, mock_quiet, mock_db
    ):
        """Last push was 30 min ago → no new push (needs 120 min interval)."""
        await self._seed_active_user(mock_db)

        recent_ts = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()
        await mock_db.notifications.insert_one({
            "notification_id": "notif_recent",
            "user_id": TEST_USER_ID,
            "type": "micro_instant_push",
            "title": "Recent push",
            "message": "Body",
            "read": False,
            "created_at": recent_ts,
        })

        await generate_contextual_instant_notifications(mock_db)

        mock_create_notif.assert_not_called()

    @pytest.mark.asyncio
    @patch("services.notification_scheduler._is_quiet_hours", return_value=True)
    @patch("services.notification_scheduler._create_notification")
    async def test_quiet_hours_skip(
        self, mock_create_notif, mock_quiet, mock_db
    ):
        """Current time in quiet hours → no push."""
        await self._seed_active_user(mock_db)

        await generate_contextual_instant_notifications(mock_db)

        mock_create_notif.assert_not_called()

    @pytest.mark.asyncio
    @patch("services.notification_scheduler._is_quiet_hours", return_value=False)
    @patch("services.notification_scheduler._create_notification")
    async def test_skips_low_confidence(
        self, mock_create_notif, mock_quiet, mock_db
    ):
        """Only instants with confidence 0.20 → no push (threshold is 0.50)."""
        await self._seed_active_user(mock_db)

        low_conf_instant = _make_test_instant(confidence=0.20, minutes_ahead=15)

        with patch(
            "services.micro_instant_engine.predict_micro_instants",
            new_callable=AsyncMock,
            return_value=[low_conf_instant],
        ):
            await generate_contextual_instant_notifications(mock_db)

        mock_create_notif.assert_not_called()
