"""
Unit tests — Billing routes.
Tests activate-free, payment status, webhook handling, promo code.
Stripe API calls are mocked (no real Stripe calls).
"""

import os
import json
import pytest
from datetime import datetime, timezone
from unittest.mock import patch, AsyncMock, MagicMock

pytestmark = pytest.mark.asyncio


# ═══════════════════════════════════════════════════════════════
# ACTIVATE FREE
# ═══════════════════════════════════════════════════════════════

class TestActivateFree:
    async def test_activate_free_success(self, client, mock_db):
        from tests.conftest import TEST_USER
        await mock_db.users.insert_one({**TEST_USER})

        resp = await client.post("/api/premium/activate-free")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"

        # Verify user is now premium
        user = await mock_db.users.find_one({"user_id": TEST_USER["user_id"]})
        assert user["subscription_tier"] == "premium"

    async def test_activate_free_already_premium(self, premium_client, mock_db):
        from tests.conftest import TEST_USER_PREMIUM
        await mock_db.users.insert_one({**TEST_USER_PREMIUM})

        resp = await premium_client.post("/api/premium/activate-free")
        assert resp.status_code == 200
        assert resp.json()["status"] == "already_premium"


# ═══════════════════════════════════════════════════════════════
# CHECKOUT (Stripe mocked)
# ═══════════════════════════════════════════════════════════════

class TestCheckout:
    async def test_checkout_no_stripe_key(self, client, mock_db):
        """Without STRIPE_API_KEY, checkout should return 500."""
        with patch.dict(os.environ, {"STRIPE_API_KEY": ""}, clear=False):
            resp = await client.post("/api/payments/checkout", json={
                "origin_url": "https://infinea.vercel.app"
            })
            assert resp.status_code == 500

    async def test_checkout_requires_origin_url(self, client, mock_db):
        """Checkout without origin_url should fail validation."""
        with patch.dict(os.environ, {"STRIPE_API_KEY": "sk_test_fake"}, clear=False):
            resp = await client.post("/api/payments/checkout", json={})
            assert resp.status_code == 422  # Pydantic validation error


# ═══════════════════════════════════════════════════════════════
# PAYMENT STATUS
# ═══════════════════════════════════════════════════════════════

class TestPaymentStatus:
    async def test_status_no_stripe_key(self, client, mock_db):
        with patch.dict(os.environ, {"STRIPE_API_KEY": ""}, clear=False):
            resp = await client.get("/api/payments/status/cs_test_123")
            assert resp.status_code == 500


# ═══════════════════════════════════════════════════════════════
# WEBHOOK
# ═══════════════════════════════════════════════════════════════

class TestStripeWebhook:
    async def test_webhook_no_stripe_key(self, client, mock_db):
        with patch.dict(os.environ, {"STRIPE_API_KEY": ""}, clear=False):
            resp = await client.post("/api/webhook/stripe", content=b"{}")
            assert resp.status_code == 200
            assert resp.json()["status"] == "error"

    async def test_webhook_checkout_completed(self, client, mock_db):
        """Simulate checkout.session.completed webhook → user upgraded to premium."""
        from tests.conftest import TEST_USER
        await mock_db.users.insert_one({**TEST_USER})

        event = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "payment_status": "paid",
                    "metadata": {"user_id": TEST_USER["user_id"]},
                    "subscription": "sub_test_123",
                    "customer": "cus_test_123",
                }
            }
        }

        with patch.dict(os.environ, {"STRIPE_API_KEY": "sk_test_fake"}, clear=False), \
             patch("routes.billing.STRIPE_WEBHOOK_SECRET", ""):
            resp = await client.post(
                "/api/webhook/stripe",
                content=json.dumps(event).encode(),
            )

        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

        # Verify upgrade
        user = await mock_db.users.find_one({"user_id": TEST_USER["user_id"]})
        assert user["subscription_tier"] == "premium"
        assert user["stripe_subscription_id"] == "sub_test_123"

    async def test_webhook_subscription_deleted(self, client, mock_db):
        """Simulate customer.subscription.deleted → user downgraded."""
        from tests.conftest import TEST_USER_PREMIUM
        await mock_db.users.insert_one({
            **TEST_USER_PREMIUM,
            "stripe_subscription_id": "sub_to_cancel",
        })

        event = {
            "type": "customer.subscription.deleted",
            "data": {
                "object": {
                    "id": "sub_to_cancel",
                }
            }
        }

        with patch.dict(os.environ, {"STRIPE_API_KEY": "sk_test_fake"}, clear=False), \
             patch("routes.billing.STRIPE_WEBHOOK_SECRET", ""):
            resp = await client.post(
                "/api/webhook/stripe",
                content=json.dumps(event).encode(),
            )

        assert resp.status_code == 200

        # Verify downgrade
        user = await mock_db.users.find_one({"user_id": TEST_USER_PREMIUM["user_id"]})
        assert user["subscription_tier"] == "free"


# ═══════════════════════════════════════════════════════════════
# PROMO CODE
# ═══════════════════════════════════════════════════════════════

class TestPromoCode:
    async def test_promo_non_admin_rejected(self, client, mock_db):
        """Non-admin user should be rejected (403)."""
        resp = await client.post("/api/promo/redeem", json={"code": "anything"})
        assert resp.status_code == 403

    async def test_promo_already_premium(self, premium_client, mock_db):
        resp = await premium_client.post("/api/promo/redeem", json={"code": "anything"})
        assert resp.status_code == 400
        assert "déjà Premium" in resp.json()["detail"]
