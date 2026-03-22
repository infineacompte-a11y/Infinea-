"""Tests for authentication — register, login, profile, token validation."""

import pytest
from database import db


class TestRegister:
    async def test_register_success(self, client_unauthenticated):
        resp = await client_unauthenticated.post(
            "/api/auth/register",
            json={
                "email": "new@example.com",
                "password": "StrongPass123!",
                "name": "New User",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "new@example.com"
        assert data["name"] == "New User"
        assert "user_id" in data
        assert "token" in data
        assert "password" not in data

    async def test_register_duplicate_email(self, client_unauthenticated, test_user):
        resp = await client_unauthenticated.post(
            "/api/auth/register",
            json={
                "email": test_user["email"],
                "password": "AnotherPass123!",
                "name": "Duplicate",
            },
        )
        assert resp.status_code == 400

    async def test_register_invalid_email(self, client_unauthenticated):
        resp = await client_unauthenticated.post(
            "/api/auth/register",
            json={
                "email": "not-an-email",
                "password": "StrongPass123!",
                "name": "Bad Email",
            },
        )
        assert resp.status_code == 422


class TestLogin:
    async def test_login_success(self, client_unauthenticated, test_user):
        resp = await client_unauthenticated.post(
            "/api/auth/login",
            json={
                "email": test_user["email"],
                "password": "TestPassword123!",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "token" in data
        assert data["user_id"] == test_user["user_id"]

    async def test_login_wrong_password(self, client_unauthenticated, test_user):
        resp = await client_unauthenticated.post(
            "/api/auth/login",
            json={
                "email": test_user["email"],
                "password": "WrongPassword!",
            },
        )
        assert resp.status_code == 401

    async def test_login_nonexistent_user(self, client_unauthenticated):
        resp = await client_unauthenticated.post(
            "/api/auth/login",
            json={
                "email": "nobody@example.com",
                "password": "Whatever123!",
            },
        )
        assert resp.status_code == 401


class TestProfile:
    async def test_get_me_authenticated(self, client_authenticated, test_user):
        resp = await client_authenticated.get("/api/auth/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == test_user["user_id"]
        assert data["email"] == test_user["email"]

    async def test_get_me_unauthenticated(self, client_unauthenticated):
        resp = await client_unauthenticated.get("/api/auth/me")
        assert resp.status_code == 401

    async def test_invalid_token(self, client_unauthenticated):
        resp = await client_unauthenticated.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert resp.status_code == 401


class TestLogout:
    async def test_logout(self, client_authenticated):
        resp = await client_authenticated.post("/api/auth/logout")
        assert resp.status_code == 200
