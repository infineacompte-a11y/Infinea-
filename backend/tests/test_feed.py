"""Tests for activity feed — feed listing, reactions, comments."""

import uuid
from datetime import datetime, timezone

from database import db
from services.activity_service import create_activity


# ---------- Helpers ----------

async def _create_test_activity(user_id: str, activity_type: str = "session_completed"):
    """Helper to create an activity directly in DB."""
    activity_id = f"act_{uuid.uuid4().hex[:12]}"
    doc = {
        "activity_id": activity_id,
        "user_id": user_id,
        "type": activity_type,
        "data": {"action_title": "Test Action", "category": "learning", "duration": 5},
        "visibility": "public",
        "reaction_counts": {"bravo": 0, "inspire": 0, "fire": 0},
        "comment_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.activities.insert_one(doc)
    return doc


class TestFeed:
    async def test_empty_feed(self, client_authenticated):
        resp = await client_authenticated.get("/api/feed")
        assert resp.status_code == 200
        data = resp.json()
        assert data["activities"] == []
        assert data["has_more"] is False

    async def test_feed_shows_own_activities(self, client_authenticated, test_user):
        await _create_test_activity(test_user["user_id"])

        resp = await client_authenticated.get("/api/feed")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["activities"]) == 1
        assert data["activities"][0]["type"] == "session_completed"

    async def test_feed_shows_followed_activities(
        self, client_authenticated, test_user, premium_user
    ):
        # Test user follows premium user
        await client_authenticated.post(
            f"/api/users/{premium_user['user_id']}/follow"
        )

        # Premium user has an activity
        await _create_test_activity(premium_user["user_id"])

        resp = await client_authenticated.get("/api/feed")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["activities"]) >= 1
        assert any(
            a["user_id"] == premium_user["user_id"] for a in data["activities"]
        )

    async def test_feed_excludes_unfollowed(
        self, client_authenticated, premium_user
    ):
        # Premium user has activity but test user doesn't follow
        await _create_test_activity(premium_user["user_id"])

        resp = await client_authenticated.get("/api/feed")
        assert resp.status_code == 200
        data = resp.json()
        assert all(
            a["user_id"] != premium_user["user_id"] for a in data["activities"]
        )

    async def test_feed_cursor_pagination(self, client_authenticated, test_user):
        # Create 5 activities
        for _ in range(5):
            await _create_test_activity(test_user["user_id"])

        # First page (limit 2)
        resp = await client_authenticated.get("/api/feed?limit=2")
        data = resp.json()
        assert len(data["activities"]) == 2
        assert data["has_more"] is True
        assert data["next_cursor"] is not None

        # Second page
        resp2 = await client_authenticated.get(
            f"/api/feed?limit=2&cursor={data['next_cursor']}"
        )
        data2 = resp2.json()
        assert len(data2["activities"]) == 2

        # No overlap
        ids1 = {a["activity_id"] for a in data["activities"]}
        ids2 = {a["activity_id"] for a in data2["activities"]}
        assert ids1.isdisjoint(ids2)


class TestOwnActivities:
    async def test_get_own_activities(self, client_authenticated, test_user):
        await _create_test_activity(test_user["user_id"])

        resp = await client_authenticated.get("/api/feed/own")
        assert resp.status_code == 200
        assert len(resp.json()["activities"]) == 1


class TestReactions:
    async def test_add_reaction(self, client_authenticated, test_user):
        activity = await _create_test_activity(test_user["user_id"])

        resp = await client_authenticated.post(
            f"/api/activities/{activity['activity_id']}/react",
            json={"reaction_type": "bravo"},
        )
        assert resp.status_code == 200
        assert resp.json()["reacted"] is True

        # Verify count updated
        act = await db.activities.find_one(
            {"activity_id": activity["activity_id"]}
        )
        assert act["reaction_counts"]["bravo"] == 1

    async def test_toggle_reaction_off(self, client_authenticated, test_user):
        activity = await _create_test_activity(test_user["user_id"])

        # React
        await client_authenticated.post(
            f"/api/activities/{activity['activity_id']}/react",
            json={"reaction_type": "fire"},
        )
        # Toggle off (same type again)
        resp = await client_authenticated.post(
            f"/api/activities/{activity['activity_id']}/react",
            json={"reaction_type": "fire"},
        )
        assert resp.json()["reacted"] is False

        act = await db.activities.find_one(
            {"activity_id": activity["activity_id"]}
        )
        assert act["reaction_counts"]["fire"] == 0

    async def test_change_reaction_type(self, client_authenticated, test_user):
        activity = await _create_test_activity(test_user["user_id"])

        # React with bravo
        await client_authenticated.post(
            f"/api/activities/{activity['activity_id']}/react",
            json={"reaction_type": "bravo"},
        )
        # Change to inspire
        resp = await client_authenticated.post(
            f"/api/activities/{activity['activity_id']}/react",
            json={"reaction_type": "inspire"},
        )
        assert resp.json()["reaction_type"] == "inspire"

        act = await db.activities.find_one(
            {"activity_id": activity["activity_id"]}
        )
        assert act["reaction_counts"]["bravo"] == 0
        assert act["reaction_counts"]["inspire"] == 1

    async def test_invalid_reaction_type(self, client_authenticated, test_user):
        activity = await _create_test_activity(test_user["user_id"])
        resp = await client_authenticated.post(
            f"/api/activities/{activity['activity_id']}/react",
            json={"reaction_type": "invalid"},
        )
        assert resp.status_code == 422


class TestComments:
    async def test_add_comment(self, client_authenticated, test_user):
        activity = await _create_test_activity(test_user["user_id"])

        resp = await client_authenticated.post(
            f"/api/activities/{activity['activity_id']}/comments",
            json={"content": "Bravo, super effort!"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["content"] == "Bravo, super effort!"
        assert "comment_id" in data

    async def test_get_comments(self, client_authenticated, test_user):
        activity = await _create_test_activity(test_user["user_id"])

        await client_authenticated.post(
            f"/api/activities/{activity['activity_id']}/comments",
            json={"content": "Comment 1"},
        )
        await client_authenticated.post(
            f"/api/activities/{activity['activity_id']}/comments",
            json={"content": "Comment 2"},
        )

        resp = await client_authenticated.get(
            f"/api/activities/{activity['activity_id']}/comments"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        # Chronological order (oldest first)
        assert data["comments"][0]["content"] == "Comment 1"

    async def test_delete_own_comment(self, client_authenticated, test_user):
        activity = await _create_test_activity(test_user["user_id"])

        create = await client_authenticated.post(
            f"/api/activities/{activity['activity_id']}/comments",
            json={"content": "To delete"},
        )
        comment_id = create.json()["comment_id"]

        resp = await client_authenticated.delete(f"/api/comments/{comment_id}")
        assert resp.status_code == 200

    async def test_cannot_delete_others_comment(
        self, client_authenticated, client_premium, premium_user
    ):
        activity = await _create_test_activity(premium_user["user_id"])

        # Premium user adds a comment
        create = await client_premium.post(
            f"/api/activities/{activity['activity_id']}/comments",
            json={"content": "My comment"},
        )
        comment_id = create.json()["comment_id"]

        # Test user tries to delete it
        resp = await client_authenticated.delete(f"/api/comments/{comment_id}")
        assert resp.status_code == 403

    async def test_comment_on_nonexistent_activity(self, client_authenticated):
        resp = await client_authenticated.post(
            "/api/activities/fake_id/comments",
            json={"content": "Should fail"},
        )
        assert resp.status_code == 404

    async def test_comment_updates_count(self, client_authenticated, test_user):
        activity = await _create_test_activity(test_user["user_id"])

        await client_authenticated.post(
            f"/api/activities/{activity['activity_id']}/comments",
            json={"content": "Count test"},
        )

        act = await db.activities.find_one(
            {"activity_id": activity["activity_id"]}
        )
        assert act["comment_count"] == 1


class TestActivityService:
    async def test_create_activity(self, test_user):
        """Test the activity service directly."""
        activity = await create_activity(
            user_id=test_user["user_id"],
            activity_type="session_completed",
            data={"action_title": "Test", "category": "learning", "duration": 5},
        )
        assert activity is not None
        assert activity["type"] == "session_completed"

    async def test_private_activity_not_stored(self, test_user):
        """Activities with private visibility should not be stored."""
        await db.users.update_one(
            {"user_id": test_user["user_id"]},
            {"$set": {"privacy": {"activity_default_visibility": "private"}}},
        )

        activity = await create_activity(
            user_id=test_user["user_id"],
            activity_type="session_completed",
            data={"action_title": "Secret"},
        )
        assert activity is None
