"""Tests for badge system — listing, earning, checking."""

from database import db
from routes.badges import check_and_award_badges, BADGES


class TestBadgeListing:
    async def test_get_all_badges(self, client_unauthenticated):
        resp = await client_unauthenticated.get("/api/badges")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == len(BADGES)
        assert all("badge_id" in b for b in data)

    async def test_get_user_badges_empty(self, client_authenticated):
        resp = await client_authenticated.get("/api/badges/user")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_earned"] == 0
        assert data["total_available"] == len(BADGES)


class TestBadgeAwarding:
    async def test_first_action_badge(self, test_user):
        """Completing 1 session should earn 'first_action' badge."""
        # Insert a completed session
        await db.user_sessions_history.insert_one(
            {
                "session_id": "test_session_1",
                "user_id": test_user["user_id"],
                "action_id": "action_test_1",
                "category": "learning",
                "completed": True,
                "actual_duration": 5,
            }
        )

        new_badges = await check_and_award_badges(test_user["user_id"])
        badge_ids = [b["badge_id"] for b in new_badges]
        assert "first_action" in badge_ids

    async def test_no_duplicate_badges(self, test_user):
        """Running check twice should not duplicate badges."""
        await db.user_sessions_history.insert_one(
            {
                "session_id": "test_session_2",
                "user_id": test_user["user_id"],
                "action_id": "action_test_1",
                "category": "learning",
                "completed": True,
                "actual_duration": 5,
            }
        )

        first_run = await check_and_award_badges(test_user["user_id"])
        second_run = await check_and_award_badges(test_user["user_id"])

        assert len(second_run) == 0  # No new badges on second check

    async def test_streak_badge(self, test_user):
        """User with streak_days >= 3 should earn streak_3."""
        await db.users.update_one(
            {"user_id": test_user["user_id"]},
            {"$set": {"streak_days": 3}},
        )

        new_badges = await check_and_award_badges(test_user["user_id"])
        badge_ids = [b["badge_id"] for b in new_badges]
        assert "streak_3" in badge_ids

    async def test_time_badge(self, test_user):
        """User with 60+ minutes should earn time_60."""
        await db.users.update_one(
            {"user_id": test_user["user_id"]},
            {"$set": {"total_time_invested": 65}},
        )

        new_badges = await check_and_award_badges(test_user["user_id"])
        badge_ids = [b["badge_id"] for b in new_badges]
        assert "time_60" in badge_ids
