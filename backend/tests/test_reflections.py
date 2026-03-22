"""Tests for reflections / journal — CRUD operations."""

from database import db


class TestCreateReflection:
    async def test_create_reflection(self, client_authenticated):
        resp = await client_authenticated.post(
            "/api/reflections",
            json={
                "content": "Today was a great day for learning.",
                "mood": "positive",
                "tags": ["learning", "motivation"],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "reflection_id" in data
        assert data["content"] == "Today was a great day for learning."
        assert data["mood"] == "positive"
        assert data["tags"] == ["learning", "motivation"]

    async def test_create_reflection_minimal(self, client_authenticated):
        resp = await client_authenticated.post(
            "/api/reflections",
            json={"content": "Quick thought."},
        )
        assert resp.status_code == 200

    async def test_create_reflection_unauthenticated(self, client_unauthenticated):
        resp = await client_unauthenticated.post(
            "/api/reflections",
            json={"content": "Should fail."},
        )
        assert resp.status_code == 401


class TestGetReflections:
    async def test_list_reflections_empty(self, client_authenticated):
        resp = await client_authenticated.get("/api/reflections")
        assert resp.status_code == 200
        data = resp.json()
        assert data["reflections"] == []
        assert data["total"] == 0

    async def test_list_reflections_with_data(self, client_authenticated):
        # Create two reflections
        await client_authenticated.post(
            "/api/reflections", json={"content": "First thought."}
        )
        await client_authenticated.post(
            "/api/reflections", json={"content": "Second thought."}
        )

        resp = await client_authenticated.get("/api/reflections")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["reflections"]) == 2

    async def test_list_reflections_pagination(self, client_authenticated):
        for i in range(5):
            await client_authenticated.post(
                "/api/reflections", json={"content": f"Thought {i}"}
            )

        resp = await client_authenticated.get("/api/reflections?limit=2&skip=0")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["reflections"]) == 2
        assert data["total"] == 5


class TestDeleteReflection:
    async def test_delete_own_reflection(self, client_authenticated):
        create = await client_authenticated.post(
            "/api/reflections", json={"content": "To delete."}
        )
        ref_id = create.json()["reflection_id"]

        resp = await client_authenticated.delete(f"/api/reflections/{ref_id}")
        assert resp.status_code == 200

        # Verify it's gone
        listing = await client_authenticated.get("/api/reflections")
        assert listing.json()["total"] == 0

    async def test_delete_nonexistent(self, client_authenticated):
        resp = await client_authenticated.delete("/api/reflections/fake_id")
        assert resp.status_code == 404


class TestWeekReflections:
    async def test_week_reflections(self, client_authenticated):
        await client_authenticated.post(
            "/api/reflections", json={"content": "This week."}
        )
        resp = await client_authenticated.get("/api/reflections/week")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 1
