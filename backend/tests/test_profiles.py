"""Tests for user profiles — view, update, privacy, search."""

from database import db


class TestMyProfile:
    async def test_get_own_profile(self, client_authenticated, test_user):
        resp = await client_authenticated.get("/api/profile/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == test_user["user_id"]
        assert "password" not in data
        assert "followers_count" in data
        assert "following_count" in data

    async def test_get_profile_unauthenticated(self, client_unauthenticated):
        resp = await client_unauthenticated.get("/api/profile/me")
        assert resp.status_code == 401


class TestUpdateProfile:
    async def test_update_display_name(self, client_authenticated):
        resp = await client_authenticated.put(
            "/api/profile",
            json={"display_name": "Sam InFinea"},
        )
        assert resp.status_code == 200
        assert "display_name" in resp.json()["updated_fields"]

        # Verify persistence
        profile = await client_authenticated.get("/api/profile/me")
        assert profile.json()["display_name"] == "Sam InFinea"

    async def test_update_bio(self, client_authenticated):
        resp = await client_authenticated.put(
            "/api/profile",
            json={"bio": "Investir chaque instant perdu."},
        )
        assert resp.status_code == 200

    async def test_update_empty_body(self, client_authenticated):
        resp = await client_authenticated.put("/api/profile", json={})
        assert resp.status_code == 400


class TestPrivacySettings:
    async def test_get_default_privacy(self, client_authenticated):
        resp = await client_authenticated.get("/api/profile/privacy")
        assert resp.status_code == 200
        data = resp.json()
        assert data["profile_visible"] is True
        assert data["show_reflections"] is False  # Private by default

    async def test_update_privacy(self, client_authenticated):
        resp = await client_authenticated.put(
            "/api/profile/privacy",
            json={
                "profile_visible": True,
                "show_stats": False,
                "show_badges": True,
                "show_reflections": False,
                "activity_default_visibility": "public",
            },
        )
        assert resp.status_code == 200

        # Verify persistence
        get_resp = await client_authenticated.get("/api/profile/privacy")
        assert get_resp.json()["show_stats"] is False
        assert get_resp.json()["activity_default_visibility"] == "public"


class TestPublicProfile:
    async def test_view_public_profile(self, client_authenticated, premium_user):
        resp = await client_authenticated.get(
            f"/api/users/{premium_user['user_id']}/profile"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == premium_user["user_id"]
        assert "is_following" in data
        assert "password" not in data

    async def test_view_private_profile(self, client_authenticated, premium_user):
        # Make premium user's profile private
        await db.users.update_one(
            {"user_id": premium_user["user_id"]},
            {"$set": {"privacy": {"profile_visible": False}}},
        )
        resp = await client_authenticated.get(
            f"/api/users/{premium_user['user_id']}/profile"
        )
        assert resp.status_code == 403

    async def test_view_nonexistent_user(self, client_authenticated):
        resp = await client_authenticated.get("/api/users/fake_user_id/profile")
        assert resp.status_code == 404


class TestSearch:
    async def test_search_users(self, client_authenticated, premium_user):
        resp = await client_authenticated.get(
            f"/api/users/search?q={premium_user['name'][:4]}"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 1

    async def test_search_excludes_self(self, client_authenticated, test_user):
        resp = await client_authenticated.get(
            f"/api/users/search?q={test_user['name'][:4]}"
        )
        assert resp.status_code == 200
        user_ids = [u["user_id"] for u in resp.json()["users"]]
        assert test_user["user_id"] not in user_ids

    async def test_search_too_short(self, client_authenticated):
        resp = await client_authenticated.get("/api/users/search?q=a")
        assert resp.status_code == 400
