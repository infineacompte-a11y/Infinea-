"""Tests for micro-actions — listing, filtering, detail."""


class TestGetActions:
    async def test_list_actions(self, client_unauthenticated, seeded_actions):
        resp = await client_unauthenticated.get("/api/actions")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == len(seeded_actions)

    async def test_filter_by_category(self, client_unauthenticated, seeded_actions):
        resp = await client_unauthenticated.get("/api/actions?category=learning")
        assert resp.status_code == 200
        data = resp.json()
        assert all(a["category"] == "learning" for a in data)

    async def test_filter_by_energy(self, client_unauthenticated, seeded_actions):
        resp = await client_unauthenticated.get("/api/actions?energy_level=low")
        assert resp.status_code == 200
        data = resp.json()
        assert all(a["energy_level"] == "low" for a in data)

    async def test_filter_by_duration(self, client_unauthenticated, seeded_actions):
        resp = await client_unauthenticated.get("/api/actions?max_duration=5")
        assert resp.status_code == 200
        data = resp.json()
        assert all(a["duration_min"] <= 5 for a in data)


class TestGetActionDetail:
    async def test_get_existing_action(self, client_unauthenticated, seeded_actions):
        resp = await client_unauthenticated.get("/api/actions/action_test_1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["action_id"] == "action_test_1"
        assert data["title"] == "Test Action Low"

    async def test_get_nonexistent_action(self, client_unauthenticated):
        resp = await client_unauthenticated.get("/api/actions/nonexistent_id")
        assert resp.status_code == 404
