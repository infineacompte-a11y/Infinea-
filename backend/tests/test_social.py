"""Tests for social graph — follow, unfollow, followers, blocking."""

from database import db


class TestFollow:
    async def test_follow_user(self, client_authenticated, premium_user):
        resp = await client_authenticated.post(
            f"/api/users/{premium_user['user_id']}/follow"
        )
        assert resp.status_code == 200
        assert resp.json()["following"] is True

    async def test_follow_idempotent(self, client_authenticated, premium_user):
        """Following the same user twice should be a no-op."""
        await client_authenticated.post(
            f"/api/users/{premium_user['user_id']}/follow"
        )
        resp = await client_authenticated.post(
            f"/api/users/{premium_user['user_id']}/follow"
        )
        assert resp.status_code == 200
        assert "Already following" in resp.json()["message"]

    async def test_follow_self(self, client_authenticated, test_user):
        resp = await client_authenticated.post(
            f"/api/users/{test_user['user_id']}/follow"
        )
        assert resp.status_code == 400

    async def test_follow_nonexistent(self, client_authenticated):
        resp = await client_authenticated.post("/api/users/fake_id/follow")
        assert resp.status_code == 404

    async def test_follow_creates_notification(self, client_authenticated, premium_user):
        await client_authenticated.post(
            f"/api/users/{premium_user['user_id']}/follow"
        )
        notif = await db.notifications.find_one(
            {"user_id": premium_user["user_id"], "type": "new_follower"}
        )
        assert notif is not None


class TestUnfollow:
    async def test_unfollow_user(self, client_authenticated, premium_user):
        # First follow
        await client_authenticated.post(
            f"/api/users/{premium_user['user_id']}/follow"
        )
        # Then unfollow
        resp = await client_authenticated.delete(
            f"/api/users/{premium_user['user_id']}/follow"
        )
        assert resp.status_code == 200
        assert resp.json()["following"] is False

    async def test_unfollow_not_following(self, client_authenticated, premium_user):
        resp = await client_authenticated.delete(
            f"/api/users/{premium_user['user_id']}/follow"
        )
        assert resp.status_code == 404

    async def test_refollow_after_unfollow(self, client_authenticated, premium_user):
        """Follow → Unfollow → Follow should work."""
        await client_authenticated.post(
            f"/api/users/{premium_user['user_id']}/follow"
        )
        await client_authenticated.delete(
            f"/api/users/{premium_user['user_id']}/follow"
        )
        resp = await client_authenticated.post(
            f"/api/users/{premium_user['user_id']}/follow"
        )
        assert resp.status_code == 200
        assert resp.json()["following"] is True


class TestFollowersList:
    async def test_get_followers(self, client_authenticated, test_user, premium_user):
        # Premium user follows test user
        from auth import create_token
        from httpx import AsyncClient, ASGITransport
        from server import app

        token = create_token(premium_user["user_id"])
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
            headers={"Authorization": f"Bearer {token}"},
        ) as premium_client:
            await premium_client.post(
                f"/api/users/{test_user['user_id']}/follow"
            )

        # Check test user's followers
        resp = await client_authenticated.get(
            f"/api/users/{test_user['user_id']}/followers"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["followers"][0]["user_id"] == premium_user["user_id"]

    async def test_get_following(self, client_authenticated, test_user, premium_user):
        # Test user follows premium user
        await client_authenticated.post(
            f"/api/users/{premium_user['user_id']}/follow"
        )

        resp = await client_authenticated.get(
            f"/api/users/{test_user['user_id']}/following"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["following"][0]["user_id"] == premium_user["user_id"]


class TestBlock:
    async def test_block_user(self, client_authenticated, premium_user):
        resp = await client_authenticated.post(
            f"/api/users/{premium_user['user_id']}/block"
        )
        assert resp.status_code == 200

    async def test_block_removes_follows(self, client_authenticated, premium_user):
        """Blocking should remove mutual follows."""
        # Follow first
        await client_authenticated.post(
            f"/api/users/{premium_user['user_id']}/follow"
        )
        # Then block
        await client_authenticated.post(
            f"/api/users/{premium_user['user_id']}/block"
        )

        # Verify follow is gone
        follow = await db.follows.find_one({
            "follower_id": (await client_authenticated.get("/api/profile/me")).json()["user_id"],
            "following_id": premium_user["user_id"],
            "status": "active",
        })
        assert follow is None

    async def test_blocked_user_cannot_follow(self, client_authenticated, test_user, premium_user):
        """If A blocks B, B cannot follow A."""
        # Test user blocks premium user
        await client_authenticated.post(
            f"/api/users/{premium_user['user_id']}/block"
        )

        # Premium user tries to follow test user
        from auth import create_token
        from httpx import AsyncClient, ASGITransport
        from server import app

        token = create_token(premium_user["user_id"])
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
            headers={"Authorization": f"Bearer {token}"},
        ) as premium_client:
            resp = await premium_client.post(
                f"/api/users/{test_user['user_id']}/follow"
            )
            assert resp.status_code == 403

    async def test_unblock(self, client_authenticated, premium_user):
        await client_authenticated.post(
            f"/api/users/{premium_user['user_id']}/block"
        )
        resp = await client_authenticated.delete(
            f"/api/users/{premium_user['user_id']}/block"
        )
        assert resp.status_code == 200

    async def test_block_self(self, client_authenticated, test_user):
        resp = await client_authenticated.post(
            f"/api/users/{test_user['user_id']}/block"
        )
        assert resp.status_code == 400
