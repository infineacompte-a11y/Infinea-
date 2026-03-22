"""Tests for B2B — company creation, dashboard, employees, invites."""

from database import db


class TestCompanyCreation:
    async def test_create_company(self, client_authenticated, test_user):
        resp = await client_authenticated.post(
            "/api/b2b/company",
            json={"name": "Acme Corp", "domain": "acme.com"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Acme Corp"
        assert "company_id" in data

    async def test_create_duplicate_company(self, client_authenticated, company_admin):
        """Admin who already has a company cannot create another."""
        resp = await client_authenticated.post(
            "/api/b2b/company",
            json={"name": "Second Corp", "domain": "second.com"},
        )
        assert resp.status_code == 400


class TestCompanyInfo:
    async def test_get_company(self, client_authenticated, company_admin):
        resp = await client_authenticated.get("/api/b2b/company")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Test Corp"

    async def test_get_company_no_company(self, client_authenticated):
        resp = await client_authenticated.get("/api/b2b/company")
        assert resp.status_code == 404


class TestDashboard:
    async def test_dashboard_as_admin(self, client_authenticated, company_admin):
        resp = await client_authenticated.get("/api/b2b/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert data["company_name"] == "Test Corp"
        assert data["employee_count"] == 1
        assert "total_sessions" in data
        assert "engagement_rate" in data
        assert "qvt_score" in data

    async def test_dashboard_non_admin(self, client_authenticated):
        """Non-admin user should be denied."""
        resp = await client_authenticated.get("/api/b2b/dashboard")
        assert resp.status_code == 403


class TestEmployees:
    async def test_list_employees(self, client_authenticated, company_admin):
        resp = await client_authenticated.get("/api/b2b/employees")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["employees"][0]["is_admin"] is True


class TestInvite:
    async def test_invite_matching_domain(self, client_authenticated, company_admin):
        resp = await client_authenticated.post(
            "/api/b2b/invite",
            json={"email": "colleague@test.infinea.app"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "pending"

    async def test_invite_wrong_domain(self, client_authenticated, company_admin):
        resp = await client_authenticated.post(
            "/api/b2b/invite",
            json={"email": "outsider@other.com"},
        )
        assert resp.status_code == 400

    async def test_invite_non_admin(self, client_authenticated):
        resp = await client_authenticated.post(
            "/api/b2b/invite",
            json={"email": "someone@test.com"},
        )
        assert resp.status_code == 403
