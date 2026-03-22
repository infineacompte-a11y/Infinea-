"""Tests for notifications — preferences, listing, mark-read."""

from database import db


class TestPreferences:
    async def test_get_default_preferences(self, client_authenticated):
        resp = await client_authenticated.get("/api/notifications/preferences")
        assert resp.status_code == 200
        data = resp.json()
        assert data["daily_reminder"] is True
        assert data["reminder_time"] == "09:00"

    async def test_update_preferences(self, client_authenticated):
        resp = await client_authenticated.put(
            "/api/notifications/preferences",
            json={
                "daily_reminder": False,
                "reminder_time": "10:30",
                "streak_alerts": True,
                "achievement_alerts": False,
                "weekly_summary": True,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["daily_reminder"] is False
        assert data["reminder_time"] == "10:30"

        # Verify persistence
        get_resp = await client_authenticated.get("/api/notifications/preferences")
        assert get_resp.json()["daily_reminder"] is False


class TestNotificationsList:
    async def test_empty_notifications(self, client_authenticated):
        resp = await client_authenticated.get("/api/notifications")
        assert resp.status_code == 200
        data = resp.json()
        assert data == []

    async def test_get_notifications(self, client_authenticated, test_user):
        # Insert test notifications directly
        await db.notifications.insert_many(
            [
                {
                    "notification_id": "notif_1",
                    "user_id": test_user["user_id"],
                    "type": "achievement",
                    "message": "Badge earned!",
                    "read": False,
                    "created_at": "2025-01-15T10:00:00+00:00",
                },
                {
                    "notification_id": "notif_2",
                    "user_id": test_user["user_id"],
                    "type": "streak",
                    "message": "3 day streak!",
                    "read": False,
                    "created_at": "2025-01-15T11:00:00+00:00",
                },
            ]
        )

        resp = await client_authenticated.get("/api/notifications")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2


class TestMarkRead:
    async def test_mark_specific_read(self, client_authenticated, test_user):
        await db.notifications.insert_one(
            {
                "notification_id": "notif_mark",
                "user_id": test_user["user_id"],
                "type": "info",
                "message": "Test",
                "read": False,
                "created_at": "2025-01-15T10:00:00+00:00",
            }
        )

        resp = await client_authenticated.post(
            "/api/notifications/mark-read",
            json={"notification_ids": ["notif_mark"]},
        )
        assert resp.status_code == 200

        # Verify
        notif = await db.notifications.find_one({"notification_id": "notif_mark"})
        assert notif["read"] is True

    async def test_mark_all_read(self, client_authenticated, test_user):
        await db.notifications.insert_many(
            [
                {
                    "notification_id": f"notif_all_{i}",
                    "user_id": test_user["user_id"],
                    "type": "info",
                    "message": f"Test {i}",
                    "read": False,
                    "created_at": "2025-01-15T10:00:00+00:00",
                }
                for i in range(3)
            ]
        )

        resp = await client_authenticated.post(
            "/api/notifications/mark-read",
            json={},
        )
        assert resp.status_code == 200

        unread = await db.notifications.count_documents(
            {"user_id": test_user["user_id"], "read": False}
        )
        assert unread == 0
