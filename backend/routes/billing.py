"""InFinea — Billing routes. Stripe checkout, webhook, portal, promo codes."""

import os
import uuid
import json
from datetime import datetime, timezone

import httpx
import bcrypt
import stripe as stripe_lib
from fastapi import APIRouter, HTTPException, Request, Depends

from config import STRIPE_WEBHOOK_SECRET, logger, limiter
from database import db
from auth import get_current_user
from models import CheckoutRequest, PromoCodeRequest

router = APIRouter()

# ============== STRIPE PAYMENT ROUTES ==============

SUBSCRIPTION_PRICE = 6.99  # EUR

@router.post("/payments/checkout")
async def create_checkout(
    checkout_data: CheckoutRequest,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """Create Stripe checkout session for Premium subscription (recurring monthly)"""
    stripe_key = os.environ.get('STRIPE_API_KEY')
    if not stripe_key:
        raise HTTPException(status_code=500, detail="Payment service not configured")

    success_url = f"{checkout_data.origin_url}/pricing?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{checkout_data.origin_url}/pricing"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client_http:
            resp = await client_http.post(
                "https://api.stripe.com/v1/checkout/sessions",
                headers={"Authorization": f"Bearer {stripe_key}"},
                data={
                    "mode": "subscription",
                    "success_url": success_url,
                    "cancel_url": cancel_url,
                    "customer_email": user["email"],
                    "line_items[0][price_data][currency]": "eur",
                    "line_items[0][price_data][product_data][name]": "InFinea Premium",
                    "line_items[0][price_data][unit_amount]": int(SUBSCRIPTION_PRICE * 100),
                    "line_items[0][price_data][recurring][interval]": "month",
                    "line_items[0][quantity]": "1",
                    "metadata[user_id]": user["user_id"],
                    "metadata[email]": user["email"],
                    "metadata[plan]": "premium",
                    "subscription_data[metadata][user_id]": user["user_id"],
                }
            )
            resp.raise_for_status()
            session = resp.json()
    except Exception as e:
        logger.error(f"Stripe checkout error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")

    await db.payment_transactions.insert_one({
        "transaction_id": f"txn_{uuid.uuid4().hex[:12]}",
        "session_id": session["id"],
        "user_id": user["user_id"],
        "email": user["email"],
        "amount": SUBSCRIPTION_PRICE,
        "currency": "eur",
        "plan": "premium",
        "payment_status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    })

    return {"url": session["url"], "session_id": session["id"]}

@router.get("/payments/status/{session_id}")
async def get_payment_status(
    session_id: str,
    user: dict = Depends(get_current_user)
):
    """Check payment status and upgrade user if successful"""
    stripe_key = os.environ.get('STRIPE_API_KEY')
    if not stripe_key:
        raise HTTPException(status_code=500, detail="Payment service not configured")

    try:
        async with httpx.AsyncClient(timeout=15.0) as client_http:
            resp = await client_http.get(
                f"https://api.stripe.com/v1/checkout/sessions/{session_id}",
                headers={"Authorization": f"Bearer {stripe_key}"}
            )
            resp.raise_for_status()
            status = resp.json()

        payment_status = status.get("payment_status", "unpaid")
        subscription_id = status.get("subscription")
        customer_id = status.get("customer")

        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": {
                "payment_status": payment_status,
                "status": status.get("status"),
                "subscription_id": subscription_id,
                "customer_id": customer_id,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )

        if payment_status == "paid":
            txn = await db.payment_transactions.find_one(
                {"session_id": session_id, "processed": True}, {"_id": 0}
            )
            if not txn:
                await db.users.update_one(
                    {"user_id": user["user_id"]},
                    {"$set": {
                        "subscription_tier": "premium",
                        "subscription_started_at": datetime.now(timezone.utc).isoformat(),
                        "stripe_subscription_id": subscription_id,
                        "stripe_customer_id": customer_id,
                    }}
                )
                await db.payment_transactions.update_one(
                    {"session_id": session_id},
                    {"$set": {"processed": True}}
                )

        return {
            "status": status.get("status"),
            "payment_status": payment_status,
            "amount": (status.get("amount_total", 0) or 0) / 100,
            "currency": status.get("currency", "eur")
        }
    except Exception as e:
        logger.error(f"Payment status error: {e}")
        raise HTTPException(status_code=400, detail="Failed to get payment status")

@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks for subscription lifecycle.
    Verifies webhook signature using STRIPE_WEBHOOK_SECRET (Stripe standard)."""
    stripe_key = os.environ.get('STRIPE_API_KEY')
    if not stripe_key:
        return {"status": "error", "message": "Not configured"}

    body = await request.body()

    try:
        # Verify webhook signature (Stripe security best practice)
        if STRIPE_WEBHOOK_SECRET:
            sig_header = request.headers.get("stripe-signature", "")
            try:
                event = stripe_lib.Webhook.construct_event(body, sig_header, STRIPE_WEBHOOK_SECRET)
            except stripe_lib.error.SignatureVerificationError:
                logger.warning("Stripe webhook signature verification failed")
                raise HTTPException(status_code=400, detail="Invalid signature")
            except ValueError:
                logger.warning("Stripe webhook invalid payload")
                raise HTTPException(status_code=400, detail="Invalid payload")
        else:
            # Fallback for local dev without webhook secret — log warning
            logger.warning("STRIPE_WEBHOOK_SECRET not set — webhook signature NOT verified")
            event = json.loads(body)

        event_type = event.get("type", "") if isinstance(event, dict) else event["type"]
        event_data = (event.get("data", {}).get("object", {}) if isinstance(event, dict)
                      else event["data"]["object"])

        if event_type == "checkout.session.completed":
            if event_data.get("payment_status") == "paid":
                user_id = event_data.get("metadata", {}).get("user_id")
                subscription_id = event_data.get("subscription")
                customer_id = event_data.get("customer")
                if user_id:
                    await db.users.update_one(
                        {"user_id": user_id},
                        {"$set": {
                            "subscription_tier": "premium",
                            "subscription_started_at": datetime.now(timezone.utc).isoformat(),
                            "stripe_subscription_id": subscription_id,
                            "stripe_customer_id": customer_id,
                        }}
                    )

        elif event_type == "invoice.payment_succeeded":
            subscription_id = event_data.get("subscription")
            if subscription_id:
                await db.users.update_one(
                    {"stripe_subscription_id": subscription_id},
                    {"$set": {"subscription_tier": "premium"}}
                )

        elif event_type == "invoice.payment_failed":
            subscription_id = event_data.get("subscription")
            if subscription_id:
                logger.warning(f"Payment failed for subscription {subscription_id}")

        elif event_type == "customer.subscription.deleted":
            subscription_id = event_data.get("id")
            if subscription_id:
                await db.users.update_one(
                    {"stripe_subscription_id": subscription_id},
                    {"$set": {"subscription_tier": "free", "stripe_subscription_id": None}}
                )
                logger.info(f"Subscription {subscription_id} cancelled — user downgraded to free")

        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error"}

@router.post("/premium/portal")
async def create_customer_portal(
    checkout_data: CheckoutRequest,
    user: dict = Depends(get_current_user)
):
    """Create Stripe Customer Portal session for subscription management"""
    stripe_key = os.environ.get('STRIPE_API_KEY')
    if not stripe_key:
        raise HTTPException(status_code=500, detail="Payment service not configured")

    customer_id = user.get("stripe_customer_id")
    if not customer_id:
        raise HTTPException(status_code=400, detail="No active subscription found")

    try:
        async with httpx.AsyncClient(timeout=15.0) as client_http:
            resp = await client_http.post(
                "https://api.stripe.com/v1/billing_portal/sessions",
                headers={"Authorization": f"Bearer {stripe_key}"},
                data={
                    "customer": customer_id,
                    "return_url": f"{checkout_data.origin_url}/pricing",
                }
            )
            resp.raise_for_status()
            portal = resp.json()
        return {"url": portal["url"]}
    except Exception as e:
        logger.error(f"Portal creation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create portal session")

# ============== FREE PREMIUM ACTIVATION ==============

@router.post("/premium/activate-free")
async def activate_premium_free(user: dict = Depends(get_current_user)):
    """Activate premium for any logged-in user without payment"""
    if user.get("subscription_tier") == "premium":
        return {"status": "already_premium", "message": "Vous êtes déjà Premium"}
    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {
            "subscription_tier": "premium",
            "subscription_started_at": datetime.now(timezone.utc).isoformat(),
        }}
    )
    logger.info(f"Free premium activated for user {user['user_id']} ({user.get('email')})")
    return {"status": "success", "message": "Premium activé avec succès"}

# ============== PROMO CODE ROUTES ==============

@router.post("/promo/redeem")
async def redeem_promo_code(
    promo_data: PromoCodeRequest,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """Redeem admin promo code for permanent Premium access (bypasses Stripe)"""
    client_ip = request.headers.get("x-forwarded-for", "unknown").split(",")[0].strip()

    # 1. Already premium?
    if user.get("subscription_tier") == "premium":
        logger.warning(f"Promo attempt by already-premium user {user['user_id']} from IP {client_ip}")
        raise HTTPException(status_code=400, detail="Vous êtes déjà Premium")

    # 2. Admin check via ADMIN_EMAILS env var
    admin_emails_raw = os.environ.get("ADMIN_EMAILS", "")
    admin_emails = [e.strip().lower() for e in admin_emails_raw.split(",") if e.strip()]
    if not admin_emails or user.get("email", "").lower() not in admin_emails:
        logger.warning(f"Promo attempt by non-admin user {user['user_id']} ({user.get('email')}) from IP {client_ip}")
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")

    # 3. Validate promo code against bcrypt hash
    promo_hash = os.environ.get("PROMO_CODE_HASH")
    if not promo_hash:
        logger.error("PROMO_CODE_HASH not configured in environment")
        raise HTTPException(status_code=500, detail="Code promo non configuré")

    if not bcrypt.checkpw(promo_data.code.encode(), promo_hash.encode()):
        logger.warning(f"Invalid promo code attempt by user {user['user_id']} from IP {client_ip}")
        raise HTTPException(status_code=400, detail="Code promo invalide")

    # 4. Upgrade to permanent premium (no Stripe fields)
    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {
            "subscription_tier": "premium",
            "subscription_started_at": datetime.now(timezone.utc).isoformat(),
            "promo_activated": True,
        }}
    )

    # 5. Audit log
    await db.promo_logs.insert_one({
        "user_id": user["user_id"],
        "email": user["email"],
        "redeemed_at": datetime.now(timezone.utc).isoformat(),
        "ip_address": client_ip,
    })

    logger.info(f"Promo code redeemed by admin {user['user_id']} ({user['email']}) from IP {client_ip}")

    return {"status": "success", "message": "Premium activé avec succès"}
