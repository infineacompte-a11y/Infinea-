"""
Tests for collaborative challenges — templates, creation, join, progress, completion.
Covers the full lifecycle: create → invite → join → progress → complete.
"""

import uuid
from datetime import datetime, timezone, timedelta

from database import db
from auth import create_token
from httpx import AsyncClient, ASGITransport
from services.challenge_service import (
    CHALLENGE_TEMPLATES,
    create_challenge_from_template,
    join_challenge,
    update_challenge_progress,
)


# ---------- Helper to create a second authenticated client ----------

async def _get_client_for_user(app, user_doc):
    token = create_token(user_doc["user_id"])
    transport = ASGITransport(app=app)
    client = AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    )
    return client


class TestTemplates:
    async def test_list_templates(self, client_authenticated):
        resp = await client_authenticated.get("/api/challenges/templates")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["templates"]) == len(CHALLENGE_TEMPLATES)
        assert all("template_id" in t for t in data["templates"])

    async def test_launch_from_template(self, client_authenticated):
        resp = await client_authenticated.post(
            "/api/challenges/from-template",
            json={"template_id": "duo_discovery"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Duo Decouverte"
        assert data["challenge_type"] == "duo"
        assert data["status"] == "pending"
        assert len(data["participants"]) == 1

    async def test_launch_invalid_template(self, client_authenticated):
        resp = await client_authenticated.post(
            "/api/challenges/from-template",
            json={"template_id": "nonexistent"},
        )
        assert resp.status_code == 404

    async def test_launch_with_invitations(
        self, client_authenticated, premium_user
    ):
        resp = await client_authenticated.post(
            "/api/challenges/from-template",
            json={
                "template_id": "duo_focus",
                "invited_user_ids": [premium_user["user_id"]],
            },
        )
        assert resp.status_code == 200

        # Verify invitation was created
        invite = await db.challenge_invites.find_one(
            {"user_id": premium_user["user_id"]}
        )
        assert invite is not None
        assert invite["status"] == "pending"


class TestCustomCreation:
    async def test_create_custom_challenge(self, client_authenticated):
        resp = await client_authenticated.post(
            "/api/challenges",
            json={
                "title": "Mon Challenge Custom",
                "description": "Test custom challenge",
                "challenge_type": "group",
                "category": "learning",
                "goal_type": "sessions",
                "goal_value": 10,
                "duration_days": 7,
                "privacy": "public",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Mon Challenge Custom"
        assert data["challenge_type"] == "group"
        assert data["goal_value"] == 10

    async def test_create_duo_challenge(self, client_authenticated):
        resp = await client_authenticated.post(
            "/api/challenges",
            json={
                "title": "Duo Test",
                "challenge_type": "duo",
                "goal_type": "time",
                "goal_value": 30,
                "duration_days": 5,
            },
        )
        assert resp.status_code == 200
        assert resp.json()["max_participants"] == 2


class TestJoinAndLeave:
    async def test_join_public_challenge(self, app, client_authenticated, premium_user):
        # Create public challenge
        create = await client_authenticated.post(
            "/api/challenges",
            json={
                "title": "Open Challenge",
                "challenge_type": "group",
                "goal_type": "sessions",
                "goal_value": 5,
                "duration_days": 7,
                "privacy": "public",
            },
        )
        challenge_id = create.json()["challenge_id"]

        # Premium user joins
        premium_client = await _get_client_for_user(app, premium_user)
        async with premium_client:
            resp = await premium_client.post(
                f"/api/challenges/{challenge_id}/join"
            )
            assert resp.status_code == 200
            assert resp.json()["joined"] is True
            assert resp.json()["started"] is True  # 2 participants = auto-start

    async def test_join_invite_only_requires_invite(
        self, app, client_authenticated, premium_user
    ):
        create = await client_authenticated.post(
            "/api/challenges",
            json={
                "title": "Private Challenge",
                "challenge_type": "group",
                "goal_type": "sessions",
                "goal_value": 5,
                "duration_days": 7,
                "privacy": "invite_only",
            },
        )
        challenge_id = create.json()["challenge_id"]

        premium_client = await _get_client_for_user(app, premium_user)
        async with premium_client:
            resp = await premium_client.post(
                f"/api/challenges/{challenge_id}/join"
            )
            assert resp.status_code == 400
            assert "Invitation required" in resp.json()["detail"]

    async def test_join_with_invite(self, app, client_authenticated, test_user, premium_user):
        create = await client_authenticated.post(
            "/api/challenges",
            json={
                "title": "Invite Challenge",
                "challenge_type": "group",
                "goal_type": "sessions",
                "goal_value": 5,
                "duration_days": 7,
                "privacy": "invite_only",
            },
        )
        challenge_id = create.json()["challenge_id"]

        # Invite premium user
        await client_authenticated.post(
            f"/api/challenges/{challenge_id}/invite",
            json={"user_ids": [premium_user["user_id"]]},
        )

        # Now premium user can join
        premium_client = await _get_client_for_user(app, premium_user)
        async with premium_client:
            resp = await premium_client.post(
                f"/api/challenges/{challenge_id}/join"
            )
            assert resp.status_code == 200
            assert resp.json()["joined"] is True

    async def test_cannot_join_full_challenge(
        self, app, client_authenticated, test_user, premium_user
    ):
        # Create duo (max 2)
        create = await client_authenticated.post(
            "/api/challenges/from-template",
            json={"template_id": "duo_discovery"},
        )
        challenge_id = create.json()["challenge_id"]

        # Invite and join premium user
        await client_authenticated.post(
            f"/api/challenges/{challenge_id}/invite",
            json={"user_ids": [premium_user["user_id"]]},
        )
        premium_client = await _get_client_for_user(app, premium_user)
        async with premium_client:
            await premium_client.post(f"/api/challenges/{challenge_id}/join")

        # Third user tries to join — should fail
        third_user_id = f"user_{uuid.uuid4().hex[:12]}"
        await db.users.insert_one({
            "user_id": third_user_id,
            "email": f"{third_user_id}@test.com",
            "name": "Third",
            "password": "hashed",
        })
        result = await join_challenge(challenge_id, third_user_id)
        assert result["joined"] is False
        assert "full" in result["message"]

    async def test_leave_challenge(self, app, client_authenticated, premium_user):
        create = await client_authenticated.post(
            "/api/challenges",
            json={
                "title": "Leave Test",
                "challenge_type": "group",
                "goal_type": "sessions",
                "goal_value": 5,
                "duration_days": 7,
                "privacy": "public",
            },
        )
        challenge_id = create.json()["challenge_id"]

        premium_client = await _get_client_for_user(app, premium_user)
        async with premium_client:
            await premium_client.post(f"/api/challenges/{challenge_id}/join")
            resp = await premium_client.post(f"/api/challenges/{challenge_id}/leave")
            assert resp.status_code == 200

    async def test_creator_cannot_leave(self, client_authenticated):
        create = await client_authenticated.post(
            "/api/challenges",
            json={
                "title": "Creator Leave Test",
                "challenge_type": "group",
                "goal_type": "sessions",
                "goal_value": 5,
                "duration_days": 7,
                "privacy": "public",
            },
        )
        challenge_id = create.json()["challenge_id"]

        resp = await client_authenticated.post(
            f"/api/challenges/{challenge_id}/leave"
        )
        assert resp.status_code == 400


class TestProgress:
    async def test_progress_updates_on_session(self, test_user, premium_user):
        """Session completion should update challenge progress automatically."""
        # Create and start a challenge
        challenge = await create_challenge_from_template(
            "group_active_week", test_user["user_id"]
        )
        challenge_id = challenge["challenge_id"]

        result = await join_challenge(challenge_id, premium_user["user_id"])
        assert result["started"] is True

        # Simulate session completion (time-based challenge, 60 min goal)
        await update_challenge_progress(test_user["user_id"], {
            "category": "learning",
            "actual_duration": 15,
        })

        updated = await db.challenges.find_one({"challenge_id": challenge_id})
        test_participant = next(
            p for p in updated["participants"] if p["user_id"] == test_user["user_id"]
        )
        assert test_participant["progress"] == 15
        assert updated["total_progress"] == 15

    async def test_category_filter(self, test_user, premium_user):
        """Category-specific challenges should only count matching sessions."""
        challenge = await create_challenge_from_template(
            "group_productivity_sprint", test_user["user_id"]
        )
        await join_challenge(challenge["challenge_id"], premium_user["user_id"])

        # Learning session should NOT count for productivity challenge
        await update_challenge_progress(test_user["user_id"], {
            "category": "learning",
            "actual_duration": 10,
        })

        updated = await db.challenges.find_one(
            {"challenge_id": challenge["challenge_id"]}
        )
        assert updated["total_progress"] == 0

        # Productivity session SHOULD count
        await update_challenge_progress(test_user["user_id"], {
            "category": "productivity",
            "actual_duration": 10,
        })

        updated = await db.challenges.find_one(
            {"challenge_id": challenge["challenge_id"]}
        )
        assert updated["total_progress"] == 1  # sessions goal, so +1

    async def test_challenge_completion(self, test_user, premium_user):
        """Challenge should auto-complete when goal is reached."""
        challenge = await create_challenge_from_template(
            "duo_discovery", test_user["user_id"]
        )
        challenge_id = challenge["challenge_id"]
        await join_challenge(challenge_id, premium_user["user_id"])

        # Complete 5 sessions (goal = 5 sessions)
        for _ in range(5):
            await update_challenge_progress(test_user["user_id"], {
                "category": "learning",
                "actual_duration": 5,
            })

        updated = await db.challenges.find_one({"challenge_id": challenge_id})
        assert updated["status"] == "completed"
        assert updated["completed_at"] is not None

        # Verify celebration notification was sent
        notif = await db.notifications.find_one({
            "user_id": test_user["user_id"],
            "type": "challenge_completed",
        })
        assert notif is not None


class TestListAndDiscover:
    async def test_list_my_challenges(self, client_authenticated):
        await client_authenticated.post(
            "/api/challenges",
            json={
                "title": "My Challenge",
                "challenge_type": "group",
                "goal_type": "sessions",
                "goal_value": 5,
                "duration_days": 7,
                "privacy": "public",
            },
        )

        resp = await client_authenticated.get("/api/challenges")
        assert resp.status_code == 200
        assert resp.json()["count"] >= 1

    async def test_list_filtered_by_status(self, client_authenticated):
        resp = await client_authenticated.get("/api/challenges?status=active")
        assert resp.status_code == 200

    async def test_discover_public(self, app, client_authenticated, premium_user):
        # Create public challenge as test user
        await client_authenticated.post(
            "/api/challenges",
            json={
                "title": "Discoverable",
                "challenge_type": "community",
                "goal_type": "sessions",
                "goal_value": 50,
                "duration_days": 30,
                "privacy": "public",
            },
        )

        # Premium user discovers it
        premium_client = await _get_client_for_user(app, premium_user)
        async with premium_client:
            resp = await premium_client.get("/api/challenges/discover")
            assert resp.status_code == 200
            titles = [c["title"] for c in resp.json()["challenges"]]
            assert "Discoverable" in titles

    async def test_get_challenge_detail(self, client_authenticated):
        create = await client_authenticated.post(
            "/api/challenges",
            json={
                "title": "Detail Test",
                "challenge_type": "group",
                "goal_type": "time",
                "goal_value": 60,
                "duration_days": 7,
                "privacy": "public",
            },
        )
        challenge_id = create.json()["challenge_id"]

        resp = await client_authenticated.get(f"/api/challenges/{challenge_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Detail Test"
        assert "leaderboard" in data
        assert "progress_percent" in data
        assert data["is_participant"] is True


class TestCancel:
    async def test_cancel_pending(self, client_authenticated):
        create = await client_authenticated.post(
            "/api/challenges",
            json={
                "title": "To Cancel",
                "challenge_type": "group",
                "goal_type": "sessions",
                "goal_value": 5,
                "duration_days": 7,
                "privacy": "public",
            },
        )
        challenge_id = create.json()["challenge_id"]

        resp = await client_authenticated.delete(
            f"/api/challenges/{challenge_id}"
        )
        assert resp.status_code == 200

    async def test_non_creator_cannot_cancel(
        self, app, client_authenticated, premium_user
    ):
        create = await client_authenticated.post(
            "/api/challenges",
            json={
                "title": "No Cancel",
                "challenge_type": "group",
                "goal_type": "sessions",
                "goal_value": 5,
                "duration_days": 7,
                "privacy": "public",
            },
        )
        challenge_id = create.json()["challenge_id"]

        premium_client = await _get_client_for_user(app, premium_user)
        async with premium_client:
            resp = await premium_client.delete(
                f"/api/challenges/{challenge_id}"
            )
            assert resp.status_code == 403


class TestInvitations:
    async def test_get_pending_invites(self, app, client_authenticated, premium_user):
        create = await client_authenticated.post(
            "/api/challenges/from-template",
            json={
                "template_id": "duo_discovery",
                "invited_user_ids": [premium_user["user_id"]],
            },
        )

        premium_client = await _get_client_for_user(app, premium_user)
        async with premium_client:
            resp = await premium_client.get("/api/challenges/invites")
            assert resp.status_code == 200
            data = resp.json()
            assert data["count"] >= 1
            assert "challenge" in data["invites"][0]

    async def test_decline_invite(self, app, client_authenticated, premium_user):
        create = await client_authenticated.post(
            "/api/challenges/from-template",
            json={
                "template_id": "duo_focus",
                "invited_user_ids": [premium_user["user_id"]],
            },
        )

        invite = await db.challenge_invites.find_one(
            {"user_id": premium_user["user_id"], "status": "pending"}
        )

        premium_client = await _get_client_for_user(app, premium_user)
        async with premium_client:
            resp = await premium_client.post(
                f"/api/challenges/invites/{invite['invite_id']}/decline"
            )
            assert resp.status_code == 200

            # Verify invite is declined
            updated = await db.challenge_invites.find_one(
                {"invite_id": invite["invite_id"]}
            )
            assert updated["status"] == "declined"
