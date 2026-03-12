from fastapi import FastAPI, APIRouter, HTTPException, Request, Depends, Response
from fastapi.responses import JSONResponse, RedirectResponse
import urllib.parse
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
import secrets
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
import httpx
import json
import asyncio
import stripe as stripe_lib
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from services.event_tracker import track_event
from services.feedback_loop import record_signal
from services.scoring_engine import rank_actions_for_user, get_next_best_action
try:
    from icalendar import Calendar as ICalCalendar
    ICAL_AVAILABLE = True
except ImportError:
    ICAL_AVAILABLE = False

from config import (
    JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION_HOURS,
    VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY, VAPID_CLAIMS_EMAIL,
    STRIPE_WEBHOOK_SECRET,
)
from database import db, client

# Create the main app
app = FastAPI(title="InFinea API")
api_router = APIRouter(prefix="/api")

# Rate limiting
from config import limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

from config import logger

# ============== MODELS (imported from models.py) ==============
from models import (
    UserCreate, UserLogin, UserResponse,
    MicroAction, MicroActionCreate,
    SessionStart, SessionComplete,
    AIRequest, CustomActionRequest, DebriefRequest, CoachChatRequest,
    CheckoutRequest, PromoCodeRequest,
    ProgressStats, OnboardingProfile,
    ObjectiveCreate, ObjectiveUpdate,
    RoutineCreate, RoutineUpdate,
    ICalConnectRequest, TokenConnectRequest, SlotSettings,
    NotificationPreferences,
    ShareCreate, GroupCreate, GroupInvite,
    CompanyCreate, InviteEmployee,
    ReflectionCreate, ReflectionResponse,
)

# ============== HELPERS (imported from helpers.py) ==============
from helpers import (
    AI_SYSTEM_MESSAGE, get_ai_model, call_ai, parse_ai_json,
    build_user_context, check_usage_limit, send_push_to_user,
)

# ============== HELPER FUNCTIONS ==============
# ============== HELPER FUNCTIONS ==============

from auth import create_token, verify_token, get_current_user, hash_password, verify_password

# ============== AUTH ROUTES (imported from routes/auth_routes.py) ==============
from routes.auth_routes import router as auth_router
api_router.include_router(auth_router)

# ============== ONBOARDING + ACTIONS ROUTES (imported) ==============
from routes.onboarding import router as onboarding_router
from routes.actions import router as actions_router
api_router.include_router(onboarding_router)
api_router.include_router(actions_router)

# ============== AI ROUTES (imported from routes/ai.py) ==============
from routes.ai import router as ai_router
api_router.include_router(ai_router)

# ============== SESSION + STATS ROUTES (imported from routes/sessions.py) ==============
from routes.sessions import router as sessions_router
api_router.include_router(sessions_router)

# ============== STRIPE PAYMENT ROUTES ==============

SUBSCRIPTION_PRICE = 6.99  # EUR

@api_router.post("/payments/checkout")
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

@api_router.get("/payments/status/{session_id}")
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

@api_router.post("/webhook/stripe")
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

@api_router.post("/premium/portal")
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

# ============== FREE PREMIUM ACTIVATION (temporary — remove when Stripe is ready) ==============

@api_router.post("/premium/activate-free")
async def activate_premium_free(user: dict = Depends(get_current_user)):
    """Temporary route: activate premium for any logged-in user without payment"""
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

@api_router.post("/promo/redeem")
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

# ============== ACTION GENERATION (admin) ==============

@api_router.post("/admin/generate-actions")
async def trigger_action_generation(user: dict = Depends(get_current_user)):
    """Admin-only: trigger daily action generation manually."""
    admin_emails = [e.strip().lower() for e in os.environ.get("ADMIN_EMAILS", "").split(",") if e.strip()]
    if user.get("email", "").lower() not in admin_emails:
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")

    from services.action_generator import check_and_generate_daily_actions
    result = await check_and_generate_daily_actions(db)
    return result

@api_router.get("/admin/actions-stats")
async def get_actions_stats(user: dict = Depends(get_current_user)):
    """Get action library statistics (count per category, generation logs)."""
    pipeline = [
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    category_counts = await db.micro_actions.aggregate(pipeline).to_list(50)

    total = sum(c["count"] for c in category_counts)

    # Recent generation logs
    recent_logs = await db.generation_logs.find(
        {}, {"_id": 0}
    ).sort("generated_at", -1).to_list(30)

    return {
        "total_actions": total,
        "by_category": {c["_id"]: c["count"] for c in category_counts},
        "recent_generations": recent_logs,
    }

@api_router.get("/admin/events")
async def get_event_stats(user: dict = Depends(get_current_user)):
    """Admin-only: get event tracking stats to verify instrumentation works."""
    admin_emails = [e.strip().lower() for e in os.environ.get("ADMIN_EMAILS", "").split(",") if e.strip()]
    if user.get("email", "").lower() not in admin_emails:
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")

    # Count by event_type
    pipeline = [
        {"$group": {"_id": "$event_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    type_counts = await db.event_log.aggregate(pipeline).to_list(50)

    # Total events
    total = sum(c["count"] for c in type_counts)

    # Last 20 events (most recent first)
    recent = await db.event_log.find(
        {}, {"_id": 0}
    ).sort("timestamp", -1).to_list(20)

    # Convert datetime to string for JSON serialization
    for event in recent:
        if hasattr(event.get("timestamp"), "isoformat"):
            event["timestamp"] = event["timestamp"].isoformat()

    return {
        "total_events": total,
        "by_type": {c["_id"]: c["count"] for c in type_counts},
        "recent_events": recent,
    }

@api_router.get("/admin/features")
async def get_feature_stats(
    user: dict = Depends(get_current_user),
    user_id: Optional[str] = None,
):
    """Admin-only: get feature store stats or a specific user's features."""
    admin_emails = [e.strip().lower() for e in os.environ.get("ADMIN_EMAILS", "").split(",") if e.strip()]
    if user.get("email", "").lower() not in admin_emails:
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")

    # If a specific user_id is requested
    if user_id:
        doc = await db.user_features.find_one({"user_id": user_id}, {"_id": 0})
        return {"user_features": doc}

    # Global stats
    total_users = await db.user_features.count_documents({})

    # Last computation log
    last_log = await db.feature_computation_logs.find_one(
        {}, {"_id": 0}, sort=[("computed_at", -1)]
    )

    # 5 sample user features (most recently computed)
    samples = await db.user_features.find(
        {}, {"_id": 0}
    ).sort("computed_at", -1).to_list(5)

    return {
        "total_users_with_features": total_users,
        "last_computation": last_log,
        "sample_features": samples,
    }

@api_router.post("/admin/compute-features")
async def trigger_feature_computation(user: dict = Depends(get_current_user)):
    """Admin-only: trigger feature computation manually."""
    admin_emails = [e.strip().lower() for e in os.environ.get("ADMIN_EMAILS", "").split(",") if e.strip()]
    if user.get("email", "").lower() not in admin_emails:
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")

    from services.feature_calculator import compute_all_users_features
    result = await compute_all_users_features(db)
    return result

# ============== SEED DATA ==============

async def seed_micro_actions():
    """Seed database with micro-actions from seed_actions.py + premium actions.
    Only inserts actions for categories that are missing — never deletes existing data."""
    from seed_actions import SEED_ACTIONS
    try:
        from seed_premium_actions import PREMIUM_ACTIONS
    except ImportError:
        PREMIUM_ACTIONS = []

    all_seed_actions = SEED_ACTIONS + PREMIUM_ACTIONS

    # Check which categories already exist in DB
    existing_categories = await db.micro_actions.distinct("category")
    needed_categories = {a["category"] for a in all_seed_actions} - set(existing_categories)

    if not needed_categories and existing_categories:
        logger.info(f"All seed categories already present: {existing_categories}")
        return {"message": "All categories already seeded"}

    if not existing_categories:
        # Fresh DB — insert everything
        await db.micro_actions.insert_many(all_seed_actions)
        logger.info(f"Fresh seed: inserted {len(all_seed_actions)} actions")
    else:
        # Only insert actions for missing categories
        actions_to_add = [a for a in all_seed_actions if a["category"] in needed_categories]
        if actions_to_add:
            await db.micro_actions.insert_many(actions_to_add)
            logger.info(f"Partial seed: inserted {len(actions_to_add)} actions for categories {needed_categories}")

    return {"message": f"Seeded actions for categories: {needed_categories or 'all'}"}

# ============== GOOGLE CALENDAR INTEGRATION ==============

from integrations.google_calendar import (
    generate_auth_url, exchange_code_for_tokens, encrypt_tokens,
    refresh_access_token, get_calendar_events, get_user_calendars,
    GOOGLE_CLIENT_ID
)
from integrations.encryption import encrypt_token, decrypt_token
from services.slot_detector import detect_free_slots, match_action_to_slot, DEFAULT_SETTINGS
from services.smart_notifications import (
    schedule_slot_notifications, cleanup_old_slots, get_pending_notifications
)

# ============== INTEGRATION HUB CONFIG ==============

INTEGRATION_CONFIGS = {
    "google_calendar": {
        "name": "Google Calendar",
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "scopes": "https://www.googleapis.com/auth/calendar.events",
        "env_client_id": "GOOGLE_CLIENT_ID",
        "env_client_secret": "GOOGLE_CLIENT_SECRET",
    },
    "notion": {
        "name": "Notion",
        "auth_url": "https://api.notion.com/v1/oauth/authorize",
        "token_url": "https://api.notion.com/v1/oauth/token",
        "scopes": "",
        "env_client_id": "NOTION_CLIENT_ID",
        "env_client_secret": "NOTION_CLIENT_SECRET",
    },
    "todoist": {
        "name": "Todoist",
        "auth_url": "https://todoist.com/oauth/authorize",
        "token_url": "https://todoist.com/oauth/access_token",
        "scopes": "data:read_write",
        "env_client_id": "TODOIST_CLIENT_ID",
        "env_client_secret": "TODOIST_CLIENT_SECRET",
    },
    "slack": {
        "name": "Slack",
        "auth_url": "https://slack.com/oauth/v2/authorize",
        "token_url": "https://slack.com/api/oauth.v2.access",
        "scopes": "chat:write,users:read",
        "env_client_id": "SLACK_CLIENT_ID",
        "env_client_secret": "SLACK_CLIENT_SECRET",
    },
}

HUB_FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")

# ============== INTEGRATION HUB ROUTES ==============

@api_router.get("/integrations")
async def get_integrations(user: dict = Depends(get_current_user)):
    """Get user's connected integrations with status for all services."""
    integrations = await db.user_integrations.find(
        {"user_id": user["user_id"]},
        {"_id": 0, "access_token": 0, "refresh_token": 0}
    ).to_list(10)

    # Build response with connection status for all services
    result = {}
    # Support both "provider" (main legacy) and "service" (hub) field names
    connected_map = {}
    for i in integrations:
        key = i.get("service") or i.get("provider")
        if key:
            connected_map[key] = i

    for service_key, config in INTEGRATION_CONFIGS.items():
        client_id = os.environ.get(config["env_client_id"])
        connected = connected_map.get(service_key)
        # Available if OAuth configured, token connect supported, or URL connect (calendars via iCal)
        supports_url = service_key in ("google_calendar",) and ICAL_AVAILABLE
        is_available = bool(client_id) or service_key in TOKEN_CONNECT_VALIDATORS or supports_url
        result[service_key] = {
            "name": config["name"],
            "connected": bool(connected),
            "connected_at": connected.get("connected_at") or connected.get("created_at") if connected else None,
            "account_name": connected.get("account_name") if connected else None,
            "available": is_available,
            "supports_token": service_key in TOKEN_CONNECT_VALIDATORS,
            "supports_url": supports_url,
            "sync_enabled": connected.get("sync_enabled", connected.get("enabled", False)) if connected else False,
        }

    # iCal is non-OAuth, always available
    ical_connected = connected_map.get("ical")
    result["ical"] = {
        "name": "iCal",
        "connected": bool(ical_connected),
        "connected_at": ical_connected.get("connected_at") if ical_connected else None,
        "account_name": ical_connected.get("account_name") if ical_connected else None,
        "available": ICAL_AVAILABLE,
        "sync_enabled": ical_connected.get("sync_enabled", False) if ical_connected else False,
        "type": "url",
    }

    return result

@api_router.get("/integrations/connect/{service}")
async def connect_integration(service: str, request: Request, user: dict = Depends(get_current_user)):
    """Initiate OAuth flow for a service — returns the authorization URL."""
    if service not in INTEGRATION_CONFIGS:
        raise HTTPException(status_code=400, detail=f"Unknown service: {service}")

    config = INTEGRATION_CONFIGS[service]
    client_id = os.environ.get(config["env_client_id"])
    if not client_id:
        raise HTTPException(status_code=503, detail=f"{config['name']} integration not configured")

    base_state = f"{user['user_id']}:{uuid.uuid4().hex[:16]}"
    backend_url = os.environ.get("BACKEND_URL", "https://infinea-api.onrender.com")

    if service == "google_calendar":
        # Reuse the login callback URI (already registered in Google Console)
        state = f"gcal_integrate:{base_state}"
        redirect_uri = f"{backend_url}/api/auth/google/callback"
    else:
        state = base_state
        redirect_uri = f"{backend_url}/api/integrations/callback/{service}"

    await db.integration_states.insert_one({
        "state": state,
        "user_id": user["user_id"],
        "service": service,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    })

    params = {"client_id": client_id, "state": state}

    if service == "google_calendar":
        params.update({
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": config["scopes"],
            "access_type": "offline",
            "prompt": "consent",
        })
    elif service == "notion":
        params.update({
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "owner": "user",
        })
    elif service == "todoist":
        params.update({"scope": config["scopes"]})
    elif service == "slack":
        params.update({
            "scope": config["scopes"],
            "redirect_uri": redirect_uri,
        })

    auth_url = f"{config['auth_url']}?{urllib.parse.urlencode(params)}"
    return {"auth_url": auth_url}

@api_router.get("/integrations/callback/{service}")
async def integration_callback(service: str, code: str = "", state: str = "", error: str = ""):
    """OAuth callback handler — exchanges code for tokens, redirects to frontend."""
    if error:
        return RedirectResponse(f"{HUB_FRONTEND_URL}/integrations?error={urllib.parse.quote(error)}&service={service}")

    if service not in INTEGRATION_CONFIGS:
        return RedirectResponse(f"{HUB_FRONTEND_URL}/integrations?error=unknown_service")

    state_doc = await db.integration_states.find_one_and_delete({"state": state, "service": service})
    if not state_doc:
        return RedirectResponse(f"{HUB_FRONTEND_URL}/integrations?error=invalid_state&service={service}")

    expires_at = datetime.fromisoformat(state_doc["expires_at"])
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        return RedirectResponse(f"{HUB_FRONTEND_URL}/integrations?error=expired&service={service}")

    user_id = state_doc["user_id"]
    config = INTEGRATION_CONFIGS[service]
    client_id = os.environ.get(config["env_client_id"])
    client_secret = os.environ.get(config["env_client_secret"])

    if not client_id or not client_secret:
        return RedirectResponse(f"{HUB_FRONTEND_URL}/integrations?error=not_configured&service={service}")

    try:
        backend_url = os.environ.get("BACKEND_URL", "https://infinea-api.onrender.com")
        redirect_uri = f"{backend_url.rstrip('/')}/api/integrations/callback/{service}"

        async with httpx.AsyncClient() as http_client:
            access_token = None
            refresh_token = None
            expires_in = None
            account_name = config["name"]

            if service == "google_calendar":
                token_resp = await http_client.post(config["token_url"], data={
                    "client_id": client_id, "client_secret": client_secret,
                    "code": code, "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                })
                token_data = token_resp.json()
                access_token = token_data.get("access_token")
                refresh_token = token_data.get("refresh_token")
                expires_in = token_data.get("expires_in", 3600)
                try:
                    info_resp = await http_client.get(
                        "https://www.googleapis.com/oauth2/v2/userinfo",
                        headers={"Authorization": f"Bearer {access_token}"}
                    )
                    if info_resp.status_code == 200:
                        account_name = info_resp.json().get("email", "Google Calendar")
                except Exception:
                    pass

            elif service == "notion":
                auth_header = httpx.BasicAuth(client_id, client_secret)
                token_resp = await http_client.post(config["token_url"], json={
                    "grant_type": "authorization_code", "code": code,
                    "redirect_uri": redirect_uri,
                }, auth=auth_header, headers={"Notion-Version": "2022-06-28"})
                token_data = token_resp.json()
                access_token = token_data.get("access_token")
                account_name = token_data.get("workspace_name", "Notion")

            elif service == "todoist":
                token_resp = await http_client.post(config["token_url"], data={
                    "client_id": client_id, "client_secret": client_secret, "code": code,
                })
                token_data = token_resp.json()
                access_token = token_data.get("access_token")
                account_name = "Todoist"

            elif service == "slack":
                token_resp = await http_client.post(config["token_url"], data={
                    "client_id": client_id, "client_secret": client_secret,
                    "code": code, "redirect_uri": redirect_uri,
                })
                token_data = token_resp.json()
                access_token = token_data.get("access_token")
                if not access_token:
                    access_token = token_data.get("authed_user", {}).get("access_token")
                account_name = token_data.get("team", {}).get("name", "Slack")

            if not access_token:
                logger.error(f"Integration {service} token exchange failed: {token_data}")
                return RedirectResponse(f"{HUB_FRONTEND_URL}/integrations?error=token_failed&service={service}")

            # Encrypt tokens before storage
            encrypted_access = encrypt_token(access_token)
            encrypted_refresh = encrypt_token(refresh_token) if refresh_token else None

            integration_doc = {
                "user_id": user_id,
                "service": service,
                "provider": service,  # backward compat with existing Google Calendar code
                "access_token": encrypted_access,
                "refresh_token": encrypted_refresh,
                "expires_in": expires_in,
                "token_expires_at": (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).isoformat() if expires_in else None,
                "token_obtained_at": datetime.now(timezone.utc).isoformat(),
                "account_name": account_name,
                "connected_at": datetime.now(timezone.utc).isoformat(),
                "enabled": True,
                "sync_enabled": True,
                "integration_id": f"int_{uuid.uuid4().hex[:12]}",
            }

            await db.user_integrations.delete_many({"user_id": user_id, "service": service})
            await db.user_integrations.delete_many({"user_id": user_id, "provider": service})
            await db.user_integrations.insert_one(integration_doc)

            # For Google Calendar, also fetch calendars metadata
            if service == "google_calendar":
                try:
                    calendars = await get_user_calendars(encrypted_access)
                    primary_calendar = next((c for c in calendars if c.get("primary")), None)
                    await db.user_integrations.update_one(
                        {"integration_id": integration_doc["integration_id"]},
                        {"$set": {
                            "metadata": {
                                "calendars": [{"id": c["id"], "summary": c.get("summary", "")} for c in calendars],
                                "primary_calendar": primary_calendar["id"] if primary_calendar else "primary"
                            }
                        }}
                    )
                except Exception as e:
                    logger.warning(f"Failed to fetch calendars: {e}")

            return RedirectResponse(f"{HUB_FRONTEND_URL}/integrations?success=true&service={service}")

    except Exception as e:
        logger.error(f"Integration {service} callback error: {e}")
        return RedirectResponse(f"{HUB_FRONTEND_URL}/integrations?error=callback_failed&service={service}")

@api_router.delete("/integrations/{service}")
async def disconnect_integration(service: str, user: dict = Depends(get_current_user)):
    """Disconnect an integration by service name or integration_id."""
    # Try by service name first, then by integration_id for backward compat
    result = await db.user_integrations.delete_one(
        {"user_id": user["user_id"], "service": service}
    )
    if result.deleted_count == 0:
        result = await db.user_integrations.delete_one(
            {"user_id": user["user_id"], "integration_id": service}
        )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Integration not found")

    # Clean up related data
    await db.detected_free_slots.delete_many({"user_id": user["user_id"]})
    await db.synced_events.delete_many({"user_id": user["user_id"], "service": service})

    return {"message": f"{INTEGRATION_CONFIGS.get(service, {}).get('name', service)} disconnected"}

@api_router.put("/integrations/{service}/sync")
async def toggle_sync(service: str, request: Request, user: dict = Depends(get_current_user)):
    """Toggle sync on/off for an integration."""
    body = await request.json()
    sync_enabled = body.get("sync_enabled", True)

    result = await db.user_integrations.update_one(
        {"user_id": user["user_id"], "$or": [{"service": service}, {"provider": service}]},
        {"$set": {"sync_enabled": sync_enabled, "enabled": sync_enabled}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Integration not found")
    return {"sync_enabled": sync_enabled}

@api_router.post("/integrations/{service}/sync")
async def trigger_sync(service: str, user: dict = Depends(get_current_user)):
    """Trigger a manual sync for a service — syncs recent sessions to external services."""
    integration = await db.user_integrations.find_one(
        {"user_id": user["user_id"], "$or": [{"service": service}, {"provider": service}]},
        {"_id": 0}
    )
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not connected")

    access_token = integration.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="No access token")

    # Decrypt token if encrypted
    try:
        decrypted_token = decrypt_token(access_token)
        if decrypted_token:
            access_token = decrypted_token
    except Exception:
        pass  # Token may not be encrypted (legacy)

    # --- Google Calendar: URL-based (iCal) or OAuth ---
    if service == "google_calendar":
        # Detect if connected via iCal URL (no token_expires_at, URL starts with http)
        is_ical_url = not integration.get("token_expires_at") and access_token.startswith("http")
        if is_ical_url and ICAL_AVAILABLE:
            # Use iCal parsing (same as ical service)
            try:
                async with httpx.AsyncClient(timeout=15.0) as http_client:
                    resp = await http_client.get(access_token, follow_redirects=True)
                    if resp.status_code != 200:
                        raise HTTPException(status_code=502, detail=f"Calendar feed returned HTTP {resp.status_code}")
                    cal = ICalCalendar.from_ical(resp.text)
                    now = datetime.now(timezone.utc)
                    end_time = now + timedelta(hours=24)
                    events = []
                    for component in cal.walk("VEVENT"):
                        dtstart = component.get("dtstart")
                        if not dtstart or not hasattr(dtstart, "dt"):
                            continue
                        start = dtstart.dt
                        if hasattr(start, "hour"):
                            if hasattr(start, "tzinfo") and start.tzinfo:
                                start = start.astimezone(timezone.utc)
                            else:
                                start = start.replace(tzinfo=timezone.utc)
                            if now <= start <= end_time:
                                dtend = component.get("dtend")
                                end = dtend.dt if dtend and hasattr(dtend, "dt") else start + timedelta(hours=1)
                                if hasattr(end, "tzinfo") and end.tzinfo:
                                    end = end.astimezone(timezone.utc)
                                else:
                                    end = end.replace(tzinfo=timezone.utc)
                                events.append({
                                    "summary": str(component.get("summary", "Sans titre")),
                                    "start": {"dateTime": start.isoformat()},
                                    "end": {"dateTime": end.isoformat()},
                                })
                    prefs = await db.notification_preferences.find_one({"user_id": user["user_id"]}, {"_id": 0}) or {}
                    settings = {**DEFAULT_SETTINGS, **prefs}
                    slots = await detect_free_slots(events, settings)
                    await cleanup_old_slots(db, user["user_id"])
                    actions = await db.micro_actions.find({}, {"_id": 0}).to_list(50)
                    await schedule_slot_notifications(db, user["user_id"], slots, actions, user.get("subscription_tier", "free"))
                    await db.user_integrations.update_one(
                        {"user_id": user["user_id"], "$or": [{"service": service}, {"provider": service}]},
                        {"$set": {"last_sync_at": now.isoformat(), "last_synced_at": now.isoformat()}}
                    )
                    return {
                        "message": "Sync completed",
                        "synced_count": len(slots),
                        "events_found": len(events),
                        "slots_detected": len(slots),
                        "service": service,
                        "last_sync": now.isoformat()
                    }
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Google Calendar iCal sync failed: {e}")
                raise HTTPException(status_code=500, detail="Sync failed. Please try again.")

        # OAuth-based sync (legacy)
        try:
            token_expires_str = integration.get("token_expires_at")
            if token_expires_str:
                token_expires = datetime.fromisoformat(token_expires_str.replace('Z', '+00:00'))
                if token_expires < datetime.now(timezone.utc):
                    if not integration.get("refresh_token"):
                        raise HTTPException(status_code=401, detail="Token expired, please reconnect")
                    refresh_tok = integration["refresh_token"]
                    try:
                        refresh_tok = decrypt_token(refresh_tok) or refresh_tok
                    except Exception:
                        pass
                    new_tokens = await refresh_access_token(refresh_tok)
                    encrypted = encrypt_tokens(new_tokens)
                    await db.user_integrations.update_one(
                        {"user_id": user["user_id"], "$or": [{"service": service}, {"provider": service}]},
                        {"$set": {
                            "access_token": encrypted["access_token"],
                            "token_expires_at": (datetime.now(timezone.utc) + timedelta(seconds=new_tokens.get("expires_in", 3600))).isoformat()
                        }}
                    )
                    access_token = encrypted["access_token"]

            now = datetime.now(timezone.utc)
            tomorrow = now + timedelta(hours=24)

            events = await get_calendar_events(
                access_token, now, tomorrow,
                integration.get("metadata", {}).get("primary_calendar", "primary")
            )

            prefs = await db.notification_preferences.find_one(
                {"user_id": user["user_id"]}, {"_id": 0}
            ) or {}
            settings = {**DEFAULT_SETTINGS, **prefs}
            slots = await detect_free_slots(events, settings)
            await cleanup_old_slots(db, user["user_id"])
            actions = await db.micro_actions.find({}, {"_id": 0}).to_list(50)
            await schedule_slot_notifications(
                db, user["user_id"], slots, actions, user.get("subscription_tier", "free")
            )

            await db.user_integrations.update_one(
                {"user_id": user["user_id"], "$or": [{"service": service}, {"provider": service}]},
                {"$set": {"last_sync_at": now.isoformat(), "last_synced_at": now.isoformat()}}
            )

            return {
                "message": "Sync completed",
                "synced_count": len(slots),
                "events_found": len(events),
                "slots_detected": len(slots),
                "service": service,
                "last_sync": now.isoformat()
            }
        except Exception as e:
            logger.error(f"Google Calendar sync failed: {e}")
            raise HTTPException(status_code=500, detail="Sync failed. Please try again.")

    # --- iCal: fetch events and detect free slots ---
    if service == "ical" and ICAL_AVAILABLE:
        try:
            ical_url = access_token  # For iCal, the "token" is the decrypted URL
            async with httpx.AsyncClient(timeout=15.0) as http_client:
                resp = await http_client.get(ical_url, follow_redirects=True)
                if resp.status_code != 200:
                    raise HTTPException(status_code=502, detail=f"iCal feed returned HTTP {resp.status_code}")

                cal = ICalCalendar.from_ical(resp.text)
                now = datetime.now(timezone.utc)
                end_time = now + timedelta(hours=24)
                events = []

                for component in cal.walk("VEVENT"):
                    dtstart = component.get("dtstart")
                    if not dtstart or not hasattr(dtstart, "dt"):
                        continue
                    start = dtstart.dt
                    if hasattr(start, 'hour'):
                        if hasattr(start, "tzinfo") and start.tzinfo:
                            start = start.astimezone(timezone.utc)
                        else:
                            start = start.replace(tzinfo=timezone.utc)
                        if now <= start <= end_time:
                            dtend = component.get("dtend")
                            end = dtend.dt if dtend and hasattr(dtend, "dt") else start + timedelta(hours=1)
                            if hasattr(end, "tzinfo") and end.tzinfo:
                                end = end.astimezone(timezone.utc)
                            else:
                                end = end.replace(tzinfo=timezone.utc)
                            events.append({
                                "summary": str(component.get("summary", "Événement")),
                                "start": {"dateTime": start.isoformat()},
                                "end": {"dateTime": end.isoformat()},
                            })

                prefs = await db.notification_preferences.find_one({"user_id": user["user_id"]}, {"_id": 0}) or {}
                settings = {**DEFAULT_SETTINGS, **prefs}
                slots = await detect_free_slots(events, settings)
                await cleanup_old_slots(db, user["user_id"])
                actions = await db.micro_actions.find({}, {"_id": 0}).to_list(50)
                await schedule_slot_notifications(db, user["user_id"], slots, actions, user.get("subscription_tier", "free"))

                await db.user_integrations.update_one(
                    {"user_id": user["user_id"], "service": "ical"},
                    {"$set": {"last_synced_at": now.isoformat(), "metadata.event_count": len(events)}}
                )
                return {
                    "message": "Sync completed",
                    "synced_count": len(slots), "events_found": len(events),
                    "slots_detected": len(slots), "service": "ical", "last_sync": now.isoformat()
                }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"iCal sync error: {e}")
            raise HTTPException(status_code=500, detail="iCal sync failed. Please check your URL and try again.")

    # --- Other services: sync recent sessions ---
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    recent_sessions = await db.user_sessions_history.find(
        {"user_id": user["user_id"], "completed": True, "completed_at": {"$gte": week_ago}},
        {"_id": 0}
    ).sort("completed_at", -1).to_list(20)

    synced_count = 0

    try:
        async with httpx.AsyncClient() as http_client:
            if service == "notion":
                for session in recent_sessions:
                    already = await db.synced_events.find_one({
                        "user_id": user["user_id"], "service": service,
                        "session_id": session["session_id"]
                    })
                    if already:
                        continue

                    search_resp = await http_client.post(
                        "https://api.notion.com/v1/search",
                        json={"query": "InFinea Sessions", "filter": {"property": "object", "value": "page"}},
                        headers={"Authorization": f"Bearer {access_token}", "Notion-Version": "2022-06-28"}
                    )
                    parent_page_id = None
                    if search_resp.status_code == 200:
                        results = search_resp.json().get("results", [])
                        if results:
                            parent_page_id = results[0]["id"]

                    if not parent_page_id:
                        pages_resp = await http_client.post(
                            "https://api.notion.com/v1/search",
                            json={"filter": {"property": "object", "value": "page"}, "page_size": 1},
                            headers={"Authorization": f"Bearer {access_token}", "Notion-Version": "2022-06-28"}
                        )
                        if pages_resp.status_code == 200:
                            pages = pages_resp.json().get("results", [])
                            if pages:
                                parent_page_id = pages[0]["id"]

                    if parent_page_id:
                        title = session.get("action_title", "Micro-action")
                        duration = session.get("actual_duration", 5)
                        completed_at = session.get("completed_at", "")
                        page_data = {
                            "parent": {"page_id": parent_page_id},
                            "properties": {"title": {"title": [{"text": {"content": f"✅ {title} — {duration} min"}}]}},
                            "children": [{"object": "block", "type": "paragraph", "paragraph": {
                                "rich_text": [{"text": {"content": f"Catégorie: {session.get('category', 'N/A')}\nDurée: {duration} min\nDate: {completed_at[:10] if completed_at else 'N/A'}"}}]
                            }}]
                        }
                        resp = await http_client.post(
                            "https://api.notion.com/v1/pages", json=page_data,
                            headers={"Authorization": f"Bearer {access_token}", "Notion-Version": "2022-06-28"}
                        )
                        if resp.status_code in (200, 201):
                            await db.synced_events.insert_one({
                                "user_id": user["user_id"], "service": service,
                                "session_id": session["session_id"],
                                "external_id": resp.json().get("id"),
                                "synced_at": datetime.now(timezone.utc).isoformat()
                            })
                            synced_count += 1

            elif service == "todoist":
                for session in recent_sessions:
                    already = await db.synced_events.find_one({
                        "user_id": user["user_id"], "service": service,
                        "session_id": session["session_id"]
                    })
                    if already:
                        continue

                    title = session.get("action_title", "Micro-action")
                    duration = session.get("actual_duration", 5)
                    resp = await http_client.post(
                        "https://api.todoist.com/rest/v2/tasks",
                        json={"content": f"✅ {title}", "description": f"Session InFinea complétée — {duration} min"},
                        headers={"Authorization": f"Bearer {access_token}"}
                    )
                    if resp.status_code in (200, 201):
                        task_id = resp.json().get("id")
                        await http_client.post(
                            f"https://api.todoist.com/rest/v2/tasks/{task_id}/close",
                            headers={"Authorization": f"Bearer {access_token}"}
                        )
                        await db.synced_events.insert_one({
                            "user_id": user["user_id"], "service": service,
                            "session_id": session["session_id"],
                            "external_id": str(task_id),
                            "synced_at": datetime.now(timezone.utc).isoformat()
                        })
                        synced_count += 1

            elif service == "slack":
                if recent_sessions:
                    total_time = sum(s.get("actual_duration", 0) for s in recent_sessions)
                    session_count = len(recent_sessions)
                    categories = set(s.get("category", "N/A") for s in recent_sessions)
                    cat_map = {"learning": "📚 Apprentissage", "productivity": "🎯 Productivité", "well_being": "💚 Bien-être"}
                    cats_str = ", ".join([cat_map.get(c, c) for c in categories])

                    message = (
                        f"*📊 Résumé InFinea — 7 derniers jours*\n\n"
                        f"• *{session_count}* sessions complétées\n"
                        f"• *{total_time}* minutes investies\n"
                        f"• Catégories: {cats_str}\n\n"
                        f"Continuez comme ça ! 🚀"
                    )

                    # Support both webhook URLs and OAuth tokens
                    if access_token.startswith("https://hooks.slack.com/"):
                        resp = await http_client.post(access_token, json={"text": message})
                    else:
                        resp = await http_client.post(
                            "https://slack.com/api/chat.postMessage",
                            json={"channel": "me", "text": message, "mrkdwn": True},
                            headers={"Authorization": f"Bearer {access_token}"}
                        )
                    if resp.status_code == 200:
                        resp_data = resp.json() if "application/json" in resp.headers.get("content-type", "") else {}
                        if resp_data.get("ok", True):  # Webhooks return "ok", API returns {"ok": true}
                            synced_count = session_count

    except Exception as e:
        logger.error(f"Sync error for {service}: {e}")
        raise HTTPException(status_code=500, detail="Sync failed. Please try again.")

    await db.user_integrations.update_one(
        {"user_id": user["user_id"], "$or": [{"service": service}, {"provider": service}]},
        {"$set": {"last_synced_at": datetime.now(timezone.utc).isoformat()}}
    )

    return {"synced_count": synced_count, "service": service}

# ============== iCal INTEGRATION (URL-based, non-OAuth) ==============

@api_router.post("/integrations/ical/connect")
async def connect_ical(request: ICalConnectRequest, user: dict = Depends(get_current_user)):
    """Connect an iCal calendar via URL (.ics feed)."""
    # Check integration limit for free users (max 1)
    if user.get("subscription_tier") != "premium":
        existing = await db.user_integrations.count_documents({"user_id": user["user_id"]})
        if existing >= 1:
            raise HTTPException(
                status_code=403,
                detail="Limite atteinte : 1 intégration maximum en mode gratuit. Passez à Premium pour connecter toutes vos intégrations."
            )

    if not ICAL_AVAILABLE:
        raise HTTPException(status_code=503, detail="iCal support not installed (pip install icalendar)")

    url = request.url.strip()
    if not url.startswith(("http://", "https://", "webcal://")):
        raise HTTPException(status_code=400, detail="URL invalide. L'URL doit commencer par http://, https:// ou webcal://")

    # Normalize webcal:// to https://
    if url.startswith("webcal://"):
        url = "https://" + url[len("webcal://"):]

    # Validate the URL by fetching it
    try:
        async with httpx.AsyncClient(timeout=15.0) as http_client:
            resp = await http_client.get(url, follow_redirects=True)
            if resp.status_code != 200:
                raise HTTPException(status_code=400, detail=f"Impossible d'accéder à l'URL (HTTP {resp.status_code})")
            # Try to parse as iCal to validate
            cal = ICalCalendar.from_ical(resp.text)
            cal_name = str(cal.get("X-WR-CALNAME", request.name or "iCal"))
            event_count = sum(1 for _ in cal.walk("VEVENT"))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail="URL invalide ou format iCal non reconnu.")

    # Store as integration (URL encrypted like a token)
    encrypted_url = encrypt_token(url)

    await db.user_integrations.delete_many({"user_id": user["user_id"], "service": "ical"})
    await db.user_integrations.insert_one({
        "user_id": user["user_id"],
        "service": "ical",
        "provider": "ical",
        "access_token": encrypted_url,  # Encrypted iCal URL
        "account_name": cal_name,
        "connected_at": datetime.now(timezone.utc).isoformat(),
        "enabled": True,
        "sync_enabled": True,
        "integration_id": f"int_{uuid.uuid4().hex[:12]}",
        "metadata": {"event_count": event_count, "ical_url_hash": url[:50] + "..."},
    })

    return {"success": True, "calendar_name": cal_name, "events_found": event_count}

# URL-based services that support iCal format
URL_CONNECT_SERVICES = {"ical", "google_calendar"}

@api_router.post("/integrations/{service}/connect-url")
async def connect_url(service: str, request: ICalConnectRequest, user: dict = Depends(get_current_user)):
    """Connect any calendar service via iCal URL (.ics feed)."""
    if service not in URL_CONNECT_SERVICES:
        raise HTTPException(status_code=400, detail=f"Service '{service}' ne supporte pas la connexion par URL")
    if not ICAL_AVAILABLE:
        raise HTTPException(status_code=503, detail="iCal support not installed (pip install icalendar)")

    url = request.url.strip()
    if not url.startswith(("http://", "https://", "webcal://")):
        raise HTTPException(status_code=400, detail="URL invalide. L'URL doit commencer par http://, https:// ou webcal://")

    if url.startswith("webcal://"):
        url = "https://" + url[len("webcal://"):]

    try:
        async with httpx.AsyncClient(timeout=15.0) as http_client:
            resp = await http_client.get(url, follow_redirects=True)
            if resp.status_code != 200:
                raise HTTPException(status_code=400, detail=f"Impossible d'accéder à l'URL (HTTP {resp.status_code})")
            cal = ICalCalendar.from_ical(resp.text)
            cal_name = str(cal.get("X-WR-CALNAME", request.name or service))
            event_count = sum(1 for _ in cal.walk("VEVENT"))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail="URL invalide ou format iCal non reconnu.")

    encrypted_url = encrypt_token(url)

    await db.user_integrations.delete_many({"user_id": user["user_id"], "service": service})
    await db.user_integrations.insert_one({
        "user_id": user["user_id"],
        "service": service,
        "provider": service,
        "access_token": encrypted_url,
        "account_name": cal_name,
        "connected_at": datetime.now(timezone.utc).isoformat(),
        "enabled": True,
        "sync_enabled": True,
        "integration_id": f"int_{uuid.uuid4().hex[:12]}",
        "metadata": {"event_count": event_count, "ical_url_hash": url[:50] + "..."},
    })

    return {"success": True, "calendar_name": cal_name, "events_found": event_count}

@api_router.post("/integrations/ical/sync")
async def sync_ical(user: dict = Depends(get_current_user)):
    """Sync iCal calendar — fetches events and detects free slots."""
    if not ICAL_AVAILABLE:
        raise HTTPException(status_code=503, detail="iCal support not installed")

    integration = await db.user_integrations.find_one(
        {"user_id": user["user_id"], "service": "ical"}, {"_id": 0}
    )
    if not integration:
        raise HTTPException(status_code=404, detail="iCal not connected")

    encrypted_url = integration.get("access_token")
    if not encrypted_url:
        raise HTTPException(status_code=400, detail="No iCal URL stored")

    try:
        ical_url = decrypt_token(encrypted_url)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to decrypt iCal URL")

    try:
        async with httpx.AsyncClient(timeout=15.0) as http_client:
            resp = await http_client.get(ical_url, follow_redirects=True)
            if resp.status_code != 200:
                raise HTTPException(status_code=502, detail=f"iCal feed returned HTTP {resp.status_code}")

            cal = ICalCalendar.from_ical(resp.text)

            now = datetime.now(timezone.utc)
            end_time = now + timedelta(hours=24)
            events = []

            for component in cal.walk("VEVENT"):
                dtstart = component.get("dtstart")
                if not dtstart or not hasattr(dtstart, "dt"):
                    continue
                start = dtstart.dt
                if hasattr(start, 'hour'):
                    if hasattr(start, "tzinfo") and start.tzinfo:
                        start = start.astimezone(timezone.utc)
                    else:
                        start = start.replace(tzinfo=timezone.utc)
                    if now <= start <= end_time:
                        dtend = component.get("dtend")
                        end = dtend.dt if dtend and hasattr(dtend, "dt") else start + timedelta(hours=1)
                        if hasattr(end, "tzinfo") and end.tzinfo:
                            end = end.astimezone(timezone.utc)
                        else:
                            end = end.replace(tzinfo=timezone.utc)
                        events.append({
                            "summary": str(component.get("summary", "Événement")),
                            "start": {"dateTime": start.isoformat()},
                            "end": {"dateTime": end.isoformat()},
                        })

            # Detect free slots using the proper slot detector (keywords, window, categories)
            prefs = await db.notification_preferences.find_one({"user_id": user["user_id"]}, {"_id": 0}) or {}
            settings = {**DEFAULT_SETTINGS, **prefs}
            slots = await detect_free_slots(events, settings)
            await cleanup_old_slots(db, user["user_id"])
            actions = await db.micro_actions.find({}, {"_id": 0}).to_list(50)
            await schedule_slot_notifications(db, user["user_id"], slots, actions, user.get("subscription_tier", "free"))

            await db.user_integrations.update_one(
                {"user_id": user["user_id"], "service": "ical"},
                {"$set": {"last_synced_at": now.isoformat(), "metadata.event_count": len(events)}}
            )

            return {
                "message": "Sync completed",
                "synced_count": len(slots),
                "events_found": len(events),
                "slots_detected": len(slots),
                "service": "ical",
                "last_sync": now.isoformat(),
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"iCal sync error: {e}")
        raise HTTPException(status_code=500, detail="iCal sync failed. Please check your URL and try again.")

# ============== TOKEN/URL CONNECT (Notion, Todoist, Slack) ==============

TOKEN_CONNECT_VALIDATORS = {
    "notion": {
        "name": "Notion",
        "validate_url": "https://api.notion.com/v1/users/me",
        "headers_fn": lambda token: {"Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28"},
        "account_fn": lambda data: data.get("name", "Notion Workspace"),
        "placeholder": "secret_...",
        "description": "Token d'intégration interne Notion",
        "help_url": "https://www.notion.so/my-integrations",
    },
    "todoist": {
        "name": "Todoist",
        "validate_url": "https://api.todoist.com/rest/v2/projects",
        "headers_fn": lambda token: {"Authorization": f"Bearer {token}"},
        "account_fn": lambda data: "Todoist",
        "placeholder": "votre token API Todoist",
        "description": "Token API Todoist",
        "help_url": "https://app.todoist.com/app/settings/integrations/developer",
    },
    "slack": {
        "name": "Slack",
        "validate_url": None,  # Slack uses webhook URL, validated differently
        "placeholder": "https://hooks.slack.com/services/...",
        "description": "URL de webhook Slack",
        "help_url": "https://api.slack.com/messaging/webhooks",
    },
}

@api_router.post("/integrations/{service}/connect-token")
async def connect_via_token(service: str, request: TokenConnectRequest, user: dict = Depends(get_current_user)):
    """Connect an integration via API token or webhook URL (alternative to OAuth)."""
    # Check integration limit for free users (max 1)
    if user.get("subscription_tier") != "premium":
        existing = await db.user_integrations.count_documents({"user_id": user["user_id"]})
        if existing >= 1:
            raise HTTPException(
                status_code=403,
                detail="Limite atteinte : 1 intégration maximum en mode gratuit. Passez à Premium pour connecter toutes vos intégrations."
            )

    if service not in TOKEN_CONNECT_VALIDATORS:
        raise HTTPException(status_code=400, detail=f"Service '{service}' ne supporte pas la connexion par token")

    config = TOKEN_CONNECT_VALIDATORS[service]
    token = request.token.strip()
    if not token:
        raise HTTPException(status_code=400, detail="Token ou URL requis")

    account_name = request.name or config["name"]

    # Validate the token/URL by calling the service API
    try:
        async with httpx.AsyncClient(timeout=10.0) as http_client:
            if service == "slack":
                # Slack: validate webhook URL by sending a test message
                if not token.startswith("https://hooks.slack.com/"):
                    raise HTTPException(status_code=400, detail="URL Slack invalide. Doit commencer par https://hooks.slack.com/")
                resp = await http_client.post(token, json={"text": "✅ InFinea connecté avec succès !"})
                if resp.status_code != 200:
                    raise HTTPException(status_code=400, detail=f"Webhook Slack invalide (HTTP {resp.status_code})")
                account_name = request.name or "Slack Webhook"
            else:
                # Notion/Todoist: validate token via API call
                headers = config["headers_fn"](token)
                resp = await http_client.get(config["validate_url"], headers=headers)
                if resp.status_code == 401:
                    raise HTTPException(status_code=400, detail=f"Token {config['name']} invalide ou expiré")
                if resp.status_code != 200:
                    raise HTTPException(status_code=400, detail=f"Erreur de validation {config['name']} (HTTP {resp.status_code})")
                try:
                    data = resp.json()
                    account_name = config["account_fn"](data) or config["name"]
                except Exception:
                    pass

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail="Impossible de valider le token. V\u00e9rifiez et r\u00e9essayez.")

    # Store encrypted token
    encrypted_token = encrypt_token(token)

    await db.user_integrations.delete_many({"user_id": user["user_id"], "service": service})
    await db.user_integrations.delete_many({"user_id": user["user_id"], "provider": service})
    await db.user_integrations.insert_one({
        "user_id": user["user_id"],
        "service": service,
        "provider": service,
        "access_token": encrypted_token,
        "account_name": account_name,
        "connected_at": datetime.now(timezone.utc).isoformat(),
        "enabled": True,
        "sync_enabled": True,
        "integration_id": f"int_{uuid.uuid4().hex[:12]}",
        "connection_type": "token",  # Distinguish from OAuth connections
    })

    return {"success": True, "account_name": account_name, "service": service}

# ============== FREE SLOTS ENDPOINTS ==============

@api_router.get("/slots/today")
async def get_today_slots(user: dict = Depends(get_current_user)):
    """Get free slots for today."""
    now = datetime.now(timezone.utc)
    end_of_day = now.replace(hour=23, minute=59, second=59)
    
    slots = await db.detected_free_slots.find({
        "user_id": user["user_id"],
        "start_time": {"$gte": now.isoformat(), "$lte": end_of_day.isoformat()}
    }, {"_id": 0}).sort("start_time", 1).to_list(20)
    
    # Enrich with action details
    for slot in slots:
        if slot.get("suggested_action_id"):
            action = await db.micro_actions.find_one(
                {"action_id": slot["suggested_action_id"]},
                {"_id": 0}
            )
            slot["suggested_action"] = action
    
    return {"slots": slots, "count": len(slots)}

@api_router.get("/slots/week")
async def get_week_slots(user: dict = Depends(get_current_user)):
    """Get free slots for the week."""
    now = datetime.now(timezone.utc)
    week_end = now + timedelta(days=7)
    
    slots = await db.detected_free_slots.find({
        "user_id": user["user_id"],
        "start_time": {"$gte": now.isoformat(), "$lte": week_end.isoformat()}
    }, {"_id": 0}).sort("start_time", 1).to_list(50)
    
    return {"slots": slots, "count": len(slots)}

@api_router.get("/slots/next")
async def get_next_slot(user: dict = Depends(get_current_user)):
    """Get the next upcoming free slot, enriched with scored suggestion."""
    now = datetime.now(timezone.utc)

    slot = await db.detected_free_slots.find_one({
        "user_id": user["user_id"],
        "start_time": {"$gte": now.isoformat()},
        "action_taken": False
    }, {"_id": 0}, sort=[("start_time", 1)])

    if slot and slot.get("suggested_action_id"):
        action = await db.micro_actions.find_one(
            {"action_id": slot["suggested_action_id"]},
            {"_id": 0}
        )
        slot["suggested_action"] = action

    # Enrich with scored suggestion if features are available
    if slot and slot.get("duration_minutes"):
        try:
            scored = await get_next_best_action(
                db, user["user_id"],
                slot_duration=slot["duration_minutes"],
                slot_start_time=slot.get("start_time"),
                min_score=0.6,
            )
            if scored:
                slot["scored_suggestion"] = {
                    "action_id": scored.get("action_id"),
                    "title": scored.get("title"),
                    "category": scored.get("category"),
                    "score": scored.get("_score"),
                    "energy_level": scored.get("energy_level"),
                }
        except Exception:
            pass  # scoring is best-effort, never break the route

    return {"slot": slot}

@api_router.post("/slots/{slot_id}/dismiss")
async def dismiss_slot(slot_id: str, user: dict = Depends(get_current_user)):
    """Dismiss/ignore a slot."""
    result = await db.detected_free_slots.update_one(
        {"slot_id": slot_id, "user_id": user["user_id"]},
        {"$set": {"dismissed": True, "dismissed_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Slot not found")

    await track_event(db, user["user_id"], "slot_dismissed", {
        "slot_id": slot_id,
    })

    return {"message": "Slot dismissed"}

@api_router.get("/slots/settings")
async def get_slot_settings(user: dict = Depends(get_current_user)):
    """Get user's slot detection settings."""
    prefs = await db.notification_preferences.find_one(
        {"user_id": user["user_id"]},
        {"_id": 0}
    )
    
    # Merge with defaults
    settings = {**DEFAULT_SETTINGS}
    if prefs:
        for key in DEFAULT_SETTINGS:
            if key in prefs:
                settings[key] = prefs[key]
    
    return settings

@api_router.put("/slots/settings")
async def update_slot_settings(
    settings: SlotSettings,
    user: dict = Depends(get_current_user)
):
    """Update user's slot detection settings."""
    settings_dict = settings.model_dump()
    
    await db.notification_preferences.update_one(
        {"user_id": user["user_id"]},
        {"$set": settings_dict},
        upsert=True
    )
    
    return {"message": "Settings updated", "settings": settings_dict}

# ============== BADGES & ACHIEVEMENTS ==============

BADGES = [
    {
        "badge_id": "first_action",
        "name": "Premier Pas",
        "description": "Complétez votre première micro-action",
        "icon": "rocket",
        "condition": {"type": "sessions_completed", "value": 1}
    },
    {
        "badge_id": "streak_3",
        "name": "Régularité",
        "description": "Maintenez un streak de 3 jours",
        "icon": "flame",
        "condition": {"type": "streak_days", "value": 3}
    },
    {
        "badge_id": "streak_7",
        "name": "Semaine Parfaite",
        "description": "Maintenez un streak de 7 jours",
        "icon": "star",
        "condition": {"type": "streak_days", "value": 7}
    },
    {
        "badge_id": "streak_30",
        "name": "Mois d'Or",
        "description": "Maintenez un streak de 30 jours",
        "icon": "crown",
        "condition": {"type": "streak_days", "value": 30}
    },
    {
        "badge_id": "time_60",
        "name": "Première Heure",
        "description": "Accumulez 60 minutes de micro-actions",
        "icon": "clock",
        "condition": {"type": "total_time", "value": 60}
    },
    {
        "badge_id": "time_300",
        "name": "5 Heures",
        "description": "Accumulez 5 heures de micro-actions",
        "icon": "timer",
        "condition": {"type": "total_time", "value": 300}
    },
    {
        "badge_id": "time_600",
        "name": "10 Heures",
        "description": "Accumulez 10 heures de micro-actions",
        "icon": "trophy",
        "condition": {"type": "total_time", "value": 600}
    },
    {
        "badge_id": "category_learning",
        "name": "Apprenant",
        "description": "Complétez 10 actions d'apprentissage",
        "icon": "book-open",
        "condition": {"type": "category_sessions", "category": "learning", "value": 10}
    },
    {
        "badge_id": "category_productivity",
        "name": "Productif",
        "description": "Complétez 10 actions de productivité",
        "icon": "target",
        "condition": {"type": "category_sessions", "category": "productivity", "value": 10}
    },
    {
        "badge_id": "category_wellbeing",
        "name": "Zen Master",
        "description": "Complétez 10 actions de bien-être",
        "icon": "heart",
        "condition": {"type": "category_sessions", "category": "well_being", "value": 10}
    },
    {
        "badge_id": "all_categories",
        "name": "Équilibre",
        "description": "Complétez au moins 5 actions dans chaque catégorie",
        "icon": "sparkles",
        "condition": {"type": "all_categories", "value": 5}
    },
    {
        "badge_id": "premium",
        "name": "Investisseur",
        "description": "Passez à Premium",
        "icon": "gem",
        "condition": {"type": "subscription", "value": "premium"}
    },
    # --- Premium-exclusive badges ---
    {
        "badge_id": "streak_60",
        "name": "Discipline de Fer",
        "description": "Maintenez un streak de 60 jours",
        "icon": "shield",
        "condition": {"type": "streak_days", "value": 60},
        "premium_only": True
    },
    {
        "badge_id": "streak_100",
        "name": "Centurion",
        "description": "Maintenez un streak de 100 jours",
        "icon": "award",
        "condition": {"type": "streak_days", "value": 100},
        "premium_only": True
    },
    {
        "badge_id": "time_1500",
        "name": "25 Heures",
        "description": "Accumulez 25 heures de micro-actions",
        "icon": "crown",
        "condition": {"type": "total_time", "value": 1500},
        "premium_only": True
    },
    {
        "badge_id": "category_master",
        "name": "Polymathe",
        "description": "Complétez 20 sessions dans 5 catégories différentes",
        "icon": "layers",
        "condition": {"type": "multi_category_master", "min_categories": 5, "value": 20},
        "premium_only": True
    },
    {
        "badge_id": "challenge_3",
        "name": "Challenger",
        "description": "Complétez 3 défis mensuels",
        "icon": "trophy",
        "condition": {"type": "challenges_completed", "value": 3},
        "premium_only": True
    },
    {
        "badge_id": "challenge_10",
        "name": "Champion",
        "description": "Complétez 10 défis mensuels",
        "icon": "medal",
        "condition": {"type": "challenges_completed", "value": 10},
        "premium_only": True
    },
    {
        "badge_id": "custom_10",
        "name": "Architecte",
        "description": "Créez 10 actions personnalisées",
        "icon": "wrench",
        "condition": {"type": "custom_actions_created", "value": 10},
        "premium_only": True
    },
    {
        "badge_id": "streak_shield_5",
        "name": "Résilient",
        "description": "Utilisez le Bouclier de Streak 5 fois",
        "icon": "heart-handshake",
        "condition": {"type": "streak_shield_uses", "value": 5},
        "premium_only": True
    }
]

async def check_and_award_badges(user_id: str) -> List[dict]:
    """Check user progress and award new badges"""
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not user:
        return []
    
    # Get user's current badges
    user_badges = user.get("badges", [])
    user_badge_ids = [b["badge_id"] for b in user_badges]
    
    # Get session stats
    total_sessions = await db.user_sessions_history.count_documents(
        {"user_id": user_id, "completed": True}
    )
    
    # Get category stats
    pipeline = [
        {"$match": {"user_id": user_id, "completed": True}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}}}
    ]
    category_stats = await db.user_sessions_history.aggregate(pipeline).to_list(10)
    category_counts = {stat["_id"]: stat["count"] for stat in category_stats}
    
    # Get custom actions count
    custom_actions_count = await db.user_custom_actions.count_documents({"created_by": user_id})

    # Get challenges completed count
    challenges_completed = await db.user_challenges.count_documents(
        {"user_id": user_id, "completed": True}
    )

    new_badges = []
    is_premium = user.get("subscription_tier") == "premium"

    for badge in BADGES:
        if badge["badge_id"] in user_badge_ids:
            continue

        # Skip premium-only badges for free users
        if badge.get("premium_only") and not is_premium:
            continue

        condition = badge["condition"]
        earned = False

        if condition["type"] == "sessions_completed":
            earned = total_sessions >= condition["value"]
        elif condition["type"] == "streak_days":
            earned = user.get("streak_days", 0) >= condition["value"]
        elif condition["type"] == "total_time":
            earned = user.get("total_time_invested", 0) >= condition["value"]
        elif condition["type"] == "category_sessions":
            earned = category_counts.get(condition["category"], 0) >= condition["value"]
        elif condition["type"] == "all_categories":
            earned = all(
                category_counts.get(cat, 0) >= condition["value"]
                for cat in ["learning", "productivity", "well_being"]
            )
        elif condition["type"] == "subscription":
            earned = user.get("subscription_tier") == condition["value"]
        elif condition["type"] == "multi_category_master":
            qualifying = sum(1 for c in category_counts.values() if c >= condition["value"])
            earned = qualifying >= condition["min_categories"]
        elif condition["type"] == "challenges_completed":
            earned = challenges_completed >= condition["value"]
        elif condition["type"] == "custom_actions_created":
            earned = custom_actions_count >= condition["value"]
        elif condition["type"] == "streak_shield_uses":
            earned = user.get("streak_shield_count", 0) >= condition["value"]
        
        if earned:
            badge_award = {
                "badge_id": badge["badge_id"],
                "name": badge["name"],
                "icon": badge["icon"],
                "earned_at": datetime.now(timezone.utc).isoformat()
            }
            new_badges.append(badge_award)
    
    # Update user with new badges
    if new_badges:
        await db.users.update_one(
            {"user_id": user_id},
            {"$push": {"badges": {"$each": new_badges}}}
        )
    
    return new_badges

@api_router.get("/badges")
async def get_all_badges():
    """Get all available badges"""
    return BADGES

@api_router.get("/badges/user")
async def get_user_badges(user: dict = Depends(get_current_user)):
    """Get user's earned badges"""
    user_badges = user.get("badges", [])
    
    # Check for new badges
    new_badges = await check_and_award_badges(user["user_id"])
    
    all_earned = user_badges + new_badges
    
    return {
        "earned": all_earned,
        "new_badges": new_badges,
        "total_available": len(BADGES),
        "total_earned": len(all_earned)
    }

# ============== PREMIUM FEATURES ==============

@api_router.get("/premium/streak-shield")
async def get_streak_shield_status(user: dict = Depends(get_current_user)):
    """Get streak shield status for premium users"""
    if user.get("subscription_tier") != "premium":
        return {"available": False, "is_premium": False, "message": "Fonctionnalité Premium"}

    today = datetime.now(timezone.utc).date()
    shield_used_at = user.get("streak_shield_used_at")
    shield_available = True
    cooldown_days = 0

    if shield_used_at:
        if isinstance(shield_used_at, str):
            shield_date = datetime.fromisoformat(shield_used_at).date()
        else:
            shield_date = shield_used_at.date() if hasattr(shield_used_at, 'date') else shield_used_at
        days_since = (today - shield_date).days
        shield_available = days_since >= 7
        cooldown_days = max(0, 7 - days_since)

    return {
        "available": shield_available,
        "is_premium": True,
        "cooldown_days": cooldown_days,
        "total_uses": user.get("streak_shield_count", 0),
        "last_used": shield_used_at
    }

# Monthly challenges definitions
MONTHLY_CHALLENGES = [
    {
        "challenge_id": "explorer",
        "title": "Explorateur",
        "description": "Complétez 5 actions dans 3 catégories différentes ce mois-ci",
        "icon": "compass",
        "condition": {"type": "categories_touched", "min_categories": 3, "min_sessions": 5},
        "target": 5
    },
    {
        "challenge_id": "deep_diver",
        "title": "Deep Diver",
        "description": "Complétez 10 actions dans la même catégorie ce mois-ci",
        "icon": "target",
        "condition": {"type": "single_category_sessions", "value": 10},
        "target": 10
    },
    {
        "challenge_id": "early_bird",
        "title": "Matinal",
        "description": "Complétez 5 actions avant 9h ce mois-ci",
        "icon": "sunrise",
        "condition": {"type": "early_sessions", "hour_before": 9, "value": 5},
        "target": 5
    },
    {
        "challenge_id": "consistency",
        "title": "Régulier",
        "description": "Complétez au moins 1 action par jour pendant 15 jours ce mois-ci",
        "icon": "calendar-check",
        "condition": {"type": "active_days", "value": 15},
        "target": 15
    },
    {
        "challenge_id": "time_investor",
        "title": "Investisseur du Temps",
        "description": "Investissez 120 minutes ce mois-ci",
        "icon": "hourglass",
        "condition": {"type": "monthly_time", "value": 120},
        "target": 120
    },
    {
        "challenge_id": "diversifier",
        "title": "Diversificateur",
        "description": "Essayez au moins 5 catégories différentes ce mois-ci",
        "icon": "shuffle",
        "condition": {"type": "unique_categories", "value": 5},
        "target": 5
    },
]

@api_router.get("/premium/challenges")
async def get_premium_challenges(user: dict = Depends(get_current_user)):
    """Get current month's challenges with progress for premium users"""
    if user.get("subscription_tier") != "premium":
        return {"challenges": [], "is_premium": False, "message": "Fonctionnalité Premium"}

    now = datetime.now(timezone.utc)
    month_key = now.strftime("%Y-%m")
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()

    # Get this month's sessions
    sessions = await db.user_sessions_history.find(
        {"user_id": user["user_id"], "completed": True, "started_at": {"$gte": month_start}},
        {"_id": 0}
    ).to_list(500)

    # Calculate stats for challenge evaluation
    category_counts = {}
    total_time = 0
    early_sessions = 0
    active_days = set()
    for s in sessions:
        cat = s.get("category", "unknown")
        category_counts[cat] = category_counts.get(cat, 0) + 1
        total_time += s.get("actual_duration", 0)
        started = s.get("started_at", "")
        if started:
            try:
                dt = datetime.fromisoformat(started)
                if dt.hour < 9:
                    early_sessions += 1
                active_days.add(dt.date().isoformat())
            except (ValueError, TypeError):
                pass

    # Get user challenge records
    user_challenges = await db.user_challenges.find(
        {"user_id": user["user_id"], "month": month_key},
        {"_id": 0}
    ).to_list(20)
    completed_map = {uc["challenge_id"]: uc for uc in user_challenges}

    challenges_with_progress = []
    for ch in MONTHLY_CHALLENGES:
        cond = ch["condition"]
        progress = 0

        if cond["type"] == "categories_touched":
            cats_with_min = sum(1 for c in category_counts.values() if c >= 1)
            progress = min(len(sessions), ch["target"])
            if cats_with_min >= cond["min_categories"] and len(sessions) >= cond["min_sessions"]:
                progress = ch["target"]
        elif cond["type"] == "single_category_sessions":
            progress = max(category_counts.values()) if category_counts else 0
        elif cond["type"] == "early_sessions":
            progress = early_sessions
        elif cond["type"] == "active_days":
            progress = len(active_days)
        elif cond["type"] == "monthly_time":
            progress = total_time
        elif cond["type"] == "unique_categories":
            progress = len(category_counts)

        is_completed = progress >= ch["target"]

        # Auto-complete if newly completed
        if is_completed and ch["challenge_id"] not in completed_map:
            await db.user_challenges.update_one(
                {"user_id": user["user_id"], "challenge_id": ch["challenge_id"], "month": month_key},
                {"$set": {
                    "completed": True,
                    "completed_at": now.isoformat(),
                    "progress": progress
                }},
                upsert=True
            )

        challenges_with_progress.append({
            "challenge_id": ch["challenge_id"],
            "title": ch["title"],
            "description": ch["description"],
            "icon": ch["icon"],
            "target": ch["target"],
            "progress": min(progress, ch["target"]),
            "completed": is_completed,
            "completed_at": completed_map.get(ch["challenge_id"], {}).get("completed_at")
        })

    total_completed = sum(1 for c in challenges_with_progress if c["completed"])

    return {
        "challenges": challenges_with_progress,
        "is_premium": True,
        "month": month_key,
        "total_completed": total_completed,
        "total_challenges": len(MONTHLY_CHALLENGES)
    }

# ── Community Challenges (free for all) ──────────

COMMUNITY_CHALLENGES = [
    {
        "id": "community_7day_streak",
        "title": "Streak Communautaire",
        "description": "Maintiens un streak de 7 jours ce mois-ci",
        "icon": "flame",
        "target": 7,
        "metric": "streak",
        "reward": "Badge Flamme Communautaire",
    },
    {
        "id": "community_30min_week",
        "title": "30 min cette semaine",
        "description": "Investis 30 minutes de micro-actions en une semaine",
        "icon": "clock",
        "target": 30,
        "metric": "week_minutes",
        "reward": "Badge Investisseur",
    },
    {
        "id": "community_5_sessions",
        "title": "5 sessions ce mois",
        "description": "Complète 5 sessions de micro-actions ce mois-ci",
        "icon": "target",
        "target": 5,
        "metric": "month_sessions",
        "reward": "Badge Régulier",
    },
    {
        "id": "community_3_categories",
        "title": "Explorateur",
        "description": "Pratique dans 3 catégories différentes ce mois-ci",
        "icon": "compass",
        "target": 3,
        "metric": "categories",
        "reward": "Badge Explorateur",
    },
]


@api_router.get("/challenges/community")
@limiter.limit("15/minute")
async def get_community_challenges(request: Request, user: dict = Depends(get_current_user)):
    """Get community challenges open to all users with progress + leaderboard."""
    now = datetime.now(timezone.utc)
    today = now.date()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
    week_start = (today - timedelta(days=today.weekday())).isoformat()
    user_id = user["user_id"]

    # Get user's month sessions
    month_sessions = await db.user_sessions_history.find(
        {"user_id": user_id, "completed": True, "started_at": {"$gte": month_start}},
        {"_id": 0, "actual_duration": 1, "category": 1, "started_at": 1}
    ).to_list(200)

    # Get week sessions
    week_sessions = [s for s in month_sessions if s.get("started_at", "") >= week_start]

    # Compute metrics
    streak = user.get("streak_days", 0)
    week_minutes = sum(s.get("actual_duration", 0) for s in week_sessions)
    month_session_count = len(month_sessions)
    categories = len(set(s.get("category", "") for s in month_sessions if s.get("category")))

    metric_values = {
        "streak": streak,
        "week_minutes": week_minutes,
        "month_sessions": month_session_count,
        "categories": categories,
    }

    # Leaderboard: count how many users completed each challenge
    month_key = now.strftime("%Y-%m")
    leaderboard_pipeline = [
        {"$match": {"month": month_key, "completed": True}},
        {"$group": {"_id": "$challenge_id", "count": {"$sum": 1}}},
    ]
    leaderboard_data = await db.user_challenges.aggregate(leaderboard_pipeline).to_list(20)
    leaderboard_map = {item["_id"]: item["count"] for item in leaderboard_data}

    # Build response
    challenges = []
    for ch in COMMUNITY_CHALLENGES:
        progress = min(metric_values.get(ch["metric"], 0), ch["target"])
        is_completed = progress >= ch["target"]

        # Auto-record completion
        if is_completed:
            await db.user_challenges.update_one(
                {"user_id": user_id, "challenge_id": ch["id"], "month": month_key},
                {"$set": {"completed": True, "completed_at": now.isoformat(), "progress": progress}},
                upsert=True,
            )

        challenges.append({
            "id": ch["id"],
            "title": ch["title"],
            "description": ch["description"],
            "icon": ch["icon"],
            "target": ch["target"],
            "progress": progress,
            "completed": is_completed,
            "reward": ch["reward"],
            "participants_completed": leaderboard_map.get(ch["id"], 0),
        })

    return {
        "challenges": challenges,
        "month": month_key,
    }


@api_router.get("/premium/analytics")
async def get_premium_analytics(user: dict = Depends(get_current_user)):
    """Get advanced analytics for premium users"""
    if user.get("subscription_tier") != "premium":
        return {"is_premium": False, "message": "Fonctionnalité Premium"}

    now = datetime.now(timezone.utc)
    thirty_days_ago = (now - timedelta(days=30)).isoformat()

    # Get sessions from last 30 days
    sessions = await db.user_sessions_history.find(
        {"user_id": user["user_id"], "completed": True, "started_at": {"$gte": thirty_days_ago}},
        {"_id": 0}
    ).sort("started_at", 1).to_list(500)

    # Daily activity
    daily_activity = {}
    hour_distribution = {}
    day_distribution = {}
    category_stats = {}
    day_names = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]

    for s in sessions:
        started = s.get("started_at", "")
        duration = s.get("actual_duration", 0)
        category = s.get("category", "unknown")
        try:
            dt = datetime.fromisoformat(started)
            date_key = dt.date().isoformat()
            daily_activity[date_key] = daily_activity.get(date_key, 0) + 1

            hour = dt.hour
            period = "matin" if hour < 12 else "après-midi" if hour < 18 else "soir"
            hour_distribution[period] = hour_distribution.get(period, 0) + 1

            day_name = day_names[dt.weekday()]
            day_distribution[day_name] = day_distribution.get(day_name, 0) + 1
        except (ValueError, TypeError):
            pass

        if category not in category_stats:
            category_stats[category] = {"sessions": 0, "total_duration": 0}
        category_stats[category]["sessions"] += 1
        category_stats[category]["total_duration"] += duration

    # Best time of day
    best_time = max(hour_distribution, key=hour_distribution.get) if hour_distribution else "matin"

    # Most productive day
    best_day = max(day_distribution, key=day_distribution.get) if day_distribution else "lundi"

    # Category deep dive with averages
    for cat, stats in category_stats.items():
        stats["avg_duration"] = round(stats["total_duration"] / max(stats["sessions"], 1), 1)

    # Streak history (from all-time sessions)
    all_sessions = await db.user_sessions_history.find(
        {"user_id": user["user_id"], "completed": True},
        {"_id": 0, "started_at": 1}
    ).sort("started_at", 1).to_list(2000)

    streak_history = []
    if all_sessions:
        dates = set()
        for s in all_sessions:
            try:
                dt = datetime.fromisoformat(s["started_at"]).date()
                dates.add(dt)
            except (ValueError, TypeError):
                pass
        sorted_dates = sorted(dates)
        if sorted_dates:
            current_start = sorted_dates[0]
            current_end = sorted_dates[0]
            for i in range(1, len(sorted_dates)):
                if (sorted_dates[i] - sorted_dates[i - 1]).days <= 1:
                    current_end = sorted_dates[i]
                else:
                    length = (current_end - current_start).days + 1
                    if length >= 2:
                        streak_history.append({
                            "start": current_start.isoformat(),
                            "end": current_end.isoformat(),
                            "length": length
                        })
                    current_start = sorted_dates[i]
                    current_end = sorted_dates[i]
            length = (current_end - current_start).days + 1
            if length >= 2:
                streak_history.append({
                    "start": current_start.isoformat(),
                    "end": current_end.isoformat(),
                    "length": length
                })

    # Milestone prediction
    total_time = user.get("total_time_invested", 0)
    milestones = [60, 300, 600, 1500, 3000]
    next_milestone = None
    for m in milestones:
        if total_time < m:
            next_milestone = m
            break

    eta_days = None
    if next_milestone and sessions:
        time_last_30 = sum(s.get("actual_duration", 0) for s in sessions)
        daily_avg = time_last_30 / 30
        if daily_avg > 0:
            remaining = next_milestone - total_time
            eta_days = round(remaining / daily_avg)

    return {
        "is_premium": True,
        "daily_activity": daily_activity,
        "best_time_of_day": best_time,
        "most_productive_day": best_day,
        "category_deep_dive": category_stats,
        "streak_history": streak_history[-10:],
        "milestones": {
            "current": total_time,
            "next": next_milestone,
            "eta_days": eta_days
        },
        "sessions_last_30_days": len(sessions),
        "time_last_30_days": sum(s.get("actual_duration", 0) for s in sessions)
    }

# ============== NOTIFICATIONS ==============

@api_router.get("/notifications/preferences")
async def get_notification_preferences(user: dict = Depends(get_current_user)):
    """Get user's notification preferences"""
    prefs = await db.notification_preferences.find_one(
        {"user_id": user["user_id"]},
        {"_id": 0}
    )
    
    if not prefs:
        # Return defaults
        return {
            "user_id": user["user_id"],
            "daily_reminder": True,
            "reminder_time": "09:00",
            "streak_alerts": True,
            "achievement_alerts": True,
            "weekly_summary": True
        }
    
    return prefs

@api_router.put("/notifications/preferences")
async def update_notification_preferences(
    prefs: NotificationPreferences,
    user: dict = Depends(get_current_user)
):
    """Update user's notification preferences"""
    prefs_doc = {
        "user_id": user["user_id"],
        **prefs.model_dump(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.notification_preferences.update_one(
        {"user_id": user["user_id"]},
        {"$set": prefs_doc},
        upsert=True
    )
    
    return prefs_doc

@api_router.get("/notifications/vapid-public-key")
async def get_vapid_public_key():
    """Return VAPID public key so the frontend can subscribe to Web Push."""
    if not VAPID_PUBLIC_KEY:
        raise HTTPException(status_code=503, detail="Web Push not configured")
    return {"public_key": VAPID_PUBLIC_KEY}

@api_router.post("/notifications/subscribe")
async def subscribe_push_notifications(
    request: Request,
    user: dict = Depends(get_current_user)
):
    """Subscribe to push notifications (store push subscription)"""
    body = await request.json()
    subscription = body.get("subscription")
    
    if not subscription:
        raise HTTPException(status_code=400, detail="Subscription data required")
    
    await db.push_subscriptions.update_one(
        {"user_id": user["user_id"]},
        {"$set": {
            "user_id": user["user_id"],
            "subscription": subscription,
            "created_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )
    
    return {"message": "Subscribed to push notifications"}

@api_router.get("/notifications/unread-count")
async def get_unread_notification_count(
    user: dict = Depends(get_current_user),
):
    """Lightweight endpoint for sidebar badge — returns unread count only."""
    count = await db.notifications.count_documents(
        {"user_id": user["user_id"], "read": {"$ne": True}}
    )
    return {"unread_count": count}

@api_router.get("/notifications")
async def get_user_notifications(
    user: dict = Depends(get_current_user),
    limit: int = 20
):
    """Get user's notifications"""
    notifications = await db.notifications.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)

    return notifications

@api_router.post("/notifications/mark-read")
async def mark_notifications_read(
    request: Request,
    user: dict = Depends(get_current_user)
):
    """Mark notifications as read"""
    body = await request.json()
    notification_ids = body.get("notification_ids", [])
    
    if notification_ids:
        await db.notifications.update_many(
            {"user_id": user["user_id"], "notification_id": {"$in": notification_ids}},
            {"$set": {"read": True}}
        )
    else:
        # Mark all as read
        await db.notifications.update_many(
            {"user_id": user["user_id"]},
            {"$set": {"read": True}}
        )
    
    return {"message": "Notifications marked as read"}

# ============== SMART NOTIFICATIONS (Proactive Coach) ==============

@api_router.get("/notifications/smart")
@limiter.limit("10/minute")
async def get_smart_notifications(request: Request, user: dict = Depends(get_current_user)):
    """Generate proactive smart notifications based on user behavior patterns."""
    now = datetime.now(timezone.utc)
    today = now.date()
    today_iso = today.isoformat()
    user_id = user["user_id"]
    smart_notifs = []

    # ── 1. Streak en danger ─────────────────────
    streak = user.get("streak_days", 0)
    last_session_raw = user.get("last_session_date")
    if streak > 0 and last_session_raw:
        if isinstance(last_session_raw, str):
            last_date = datetime.fromisoformat(last_session_raw).date()
        else:
            last_date = last_session_raw.date() if hasattr(last_session_raw, "date") else last_session_raw
        days_since = (today - last_date).days
        if days_since >= 1:
            smart_notifs.append({
                "id": "streak_danger",
                "type": "streak_alert",
                "priority": 1,
                "title": f"Ton streak de {streak} jours est en danger !",
                "message": f"Tu n'as pas pratiqué depuis {days_since} jour{'s' if days_since > 1 else ''}. Un petit 5 min suffit pour garder ta série.",
                "icon": "flame",
                "action_label": "Faire une micro-action",
                "action_url": "/dashboard",
            })

    # ── 2. Objectifs : next step + négligés + progression ───
    objectives = await db.objectives.find(
        {"user_id": user_id, "status": "active", "deleted": {"$ne": True}},
        {"_id": 0, "objective_id": 1, "title": 1, "last_session_at": 1, "streak_days": 1,
         "current_day": 1, "target_duration_days": 1, "daily_minutes": 1,
         "curriculum": 1, "total_sessions": 1}
    ).to_list(20)

    for obj in objectives:
        curriculum = obj.get("curriculum") or []
        completed_steps = [s for s in curriculum if s.get("completed")]
        next_step = next((s for s in curriculum if not s.get("completed")), None)
        total_steps = len(curriculum)
        pct = round((len(completed_steps) / total_steps) * 100) if total_steps > 0 else 0

        # 2a. Prochaine session d'objectif (priorité haute)
        if next_step:
            last_obj_session = obj.get("last_session_at")
            already_today = False
            if last_obj_session:
                ls = last_obj_session if isinstance(last_obj_session, str) else last_obj_session.isoformat()
                already_today = ls.startswith(today_iso)
            if not already_today:
                step_title = next_step.get("title", "Prochaine étape")
                smart_notifs.append({
                    "id": f"obj_next_{obj['objective_id']}",
                    "type": "objective_nudge",
                    "priority": 1,
                    "title": f"Jour {obj.get('current_day', 0) + 1} — {obj['title'][:30]}",
                    "message": f"{step_title} · {obj.get('daily_minutes', 5)} min",
                    "icon": "target",
                    "action_label": "Lancer la session",
                    "action_url": f"/objectives/{obj['objective_id']}",
                })

        # 2b. Objectifs négligés (3+ jours)
        last_obj_session = obj.get("last_session_at")
        if last_obj_session:
            if isinstance(last_obj_session, str):
                last_obj_date = datetime.fromisoformat(last_obj_session).date()
            else:
                last_obj_date = last_obj_session.date() if hasattr(last_obj_session, "date") else today
            days_idle = (today - last_obj_date).days
            if days_idle >= 3:
                smart_notifs.append({
                    "id": f"obj_idle_{obj['objective_id']}",
                    "type": "objective_nudge",
                    "priority": 2,
                    "title": f"Tu n'as pas avancé sur « {obj['title'][:40]} »",
                    "message": f"{days_idle} jours sans session. Reprends avec une micro-session de 5 min !",
                    "icon": "target",
                    "action_label": "Reprendre",
                    "action_url": f"/objectives/{obj['objective_id']}",
                })

        # 2c. Milestones de progression (25%, 50%, 75%)
        if pct in (25, 50, 75):
            smart_notifs.append({
                "id": f"obj_pct_{obj['objective_id']}_{pct}",
                "type": "milestone",
                "priority": 3,
                "title": f"{pct}% de « {obj['title'][:30]} » complété !",
                "message": f"{len(completed_steps)}/{total_steps} sessions terminées. Continue, tu avances bien !",
                "icon": "trophy",
                "action_label": "Voir mon parcours",
                "action_url": f"/objectives/{obj['objective_id']}",
            })

    # ── 3. Routines non faites aujourd'hui ──────
    routines = await db.routines.find(
        {"user_id": user_id, "is_active": True, "deleted": {"$ne": True}},
        {"_id": 0, "routine_id": 1, "name": 1, "time_of_day": 1, "total_minutes": 1, "last_completed_at": 1}
    ).to_list(20)

    hour = now.hour
    current_tod = "morning" if hour < 12 else ("afternoon" if hour < 18 else "evening")
    tod_order = {"morning": 0, "afternoon": 1, "evening": 2, "anytime": 3}

    routines_done_today = 0
    routines_total_active = len(routines)

    for routine in routines:
        last_done = routine.get("last_completed_at", "")
        if last_done and last_done.startswith(today_iso):
            routines_done_today += 1
            continue  # Already done today

        rtod = routine.get("time_of_day", "anytime")
        # Only nudge for current or past time slots (don't nag about evening routine at 8am)
        if rtod != "anytime" and tod_order.get(rtod, 3) > tod_order.get(current_tod, 3):
            continue

        # Enriched: include items count + first item name
        items = routine.get("items") or []
        first_item = items[0]["title"] if items else ""
        detail = f"{len(items)} actions · {routine.get('total_minutes', 0)} min"
        if first_item:
            detail += f" — commence par : {first_item[:35]}"

        smart_notifs.append({
            "id": f"routine_pending_{routine['routine_id']}",
            "type": "routine_reminder",
            "priority": 3 if rtod == current_tod else 4,
            "title": f"Routine « {routine['name'][:40]} » pas encore faite",
            "message": detail,
            "icon": "calendar-clock",
            "action_label": "Lancer",
            "action_url": "/routines",
        })

    # ── 3b. Journée parfaite (toutes routines faites) ──
    if routines_total_active > 0 and routines_done_today >= routines_total_active:
        smart_notifs.append({
            "id": "perfect_day",
            "type": "milestone",
            "priority": 5,
            "title": "Journée parfaite !",
            "message": f"Toutes tes {routines_total_active} habitudes sont complétées. Bravo !",
            "icon": "trophy",
            "action_label": "Voir ma journée",
            "action_url": "/my-day",
        })

    # ── 4. Milestone atteint (celebrate) ────────
    for obj in objectives:
        curr_day = obj.get("current_day", 0)
        if curr_day in (7, 14, 30, 60, 90):
            smart_notifs.append({
                "id": f"milestone_{obj['objective_id']}_{curr_day}",
                "type": "milestone",
                "priority": 2,
                "title": f"Jour {curr_day} sur « {obj['title'][:30]} » !",
                "message": f"Bravo pour ta régularité ! Continue comme ça.",
                "icon": "trophy",
                "action_label": "Voir mon parcours",
                "action_url": f"/objectives/{obj['objective_id']}",
            })

    # ── 5. Conseil énergie (time-based) ─────────
    if hour >= 6 and hour < 10 and not smart_notifs:
        smart_notifs.append({
            "id": "energy_morning",
            "type": "coach_tip",
            "priority": 5,
            "title": "Le matin, ton énergie est à son max",
            "message": "C'est le meilleur moment pour les tâches qui demandent de la concentration.",
            "icon": "zap",
            "action_label": "Ma Journée",
            "action_url": "/my-day",
        })
    elif hour >= 13 and hour < 15 and not smart_notifs:
        smart_notifs.append({
            "id": "energy_afternoon",
            "type": "coach_tip",
            "priority": 5,
            "title": "Début d'après-midi : idéal pour des tâches légères",
            "message": "Profite de ce créneau pour une micro-action créative ou de bien-être.",
            "icon": "zap",
            "action_label": "Ma Journée",
            "action_url": "/my-day",
        })

    # ── 6. Résumé hebdo (affiché 1x par semaine, le lundi ou si pas vu depuis 7j) ──
    if today.weekday() == 0:  # Lundi
        week_ago = (now - timedelta(days=7)).isoformat()
        week_sessions = await db.sessions.count_documents(
            {"user_id": user_id, "completed": True, "completed_at": {"$gte": week_ago}}
        )
        if week_sessions > 0:
            # Aggregate total minutes from last week
            pipeline = [
                {"$match": {"user_id": user_id, "completed": True, "completed_at": {"$gte": week_ago}}},
                {"$group": {"_id": None, "total_min": {"$sum": "$actual_duration"}}},
            ]
            agg = await db.sessions.aggregate(pipeline).to_list(1)
            total_min = agg[0]["total_min"] if agg else 0
            smart_notifs.append({
                "id": f"weekly_recap_{today_iso}",
                "type": "coach_tip",
                "priority": 4,
                "title": f"Ta semaine : {week_sessions} sessions, {total_min} min",
                "message": "Beau travail ! Chaque minute investie compte pour ta progression.",
                "icon": "award",
                "action_label": "Voir ma progression",
                "action_url": "/progress",
            })

    # Sort by priority (lower = more important)
    smart_notifs.sort(key=lambda n: n.get("priority", 99))

    return {"notifications": smart_notifs[:8], "count": len(smart_notifs)}


# ============== B2B DASHBOARD ==============

@api_router.post("/b2b/company")
async def create_company(
    company_data: CompanyCreate,
    user: dict = Depends(get_current_user)
):
    """Create a B2B company account"""
    # Check if user already has a company
    existing = await db.companies.find_one(
        {"admin_user_id": user["user_id"]},
        {"_id": 0}
    )
    
    if existing:
        raise HTTPException(status_code=400, detail="You already have a company")
    
    company_id = f"company_{uuid.uuid4().hex[:12]}"
    company_doc = {
        "company_id": company_id,
        "name": company_data.name,
        "domain": company_data.domain,
        "admin_user_id": user["user_id"],
        "employees": [user["user_id"]],
        "employee_count": 1,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.companies.insert_one(company_doc)
    
    # Update user as company admin
    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {
            "company_id": company_id,
            "is_company_admin": True
        }}
    )
    
    return {"company_id": company_id, "name": company_data.name}

@api_router.get("/b2b/company")
async def get_company(user: dict = Depends(get_current_user)):
    """Get company info for admin"""
    company_id = user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=404, detail="No company found")
    
    company = await db.companies.find_one(
        {"company_id": company_id},
        {"_id": 0}
    )
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return company

@api_router.get("/b2b/dashboard")
async def get_b2b_dashboard(user: dict = Depends(get_current_user)):
    """Get B2B analytics dashboard (anonymized QVT data)"""
    company_id = user.get("company_id")
    
    if not company_id or not user.get("is_company_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    company = await db.companies.find_one(
        {"company_id": company_id},
        {"_id": 0}
    )
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    employee_ids = company.get("employees", [])
    
    # Aggregate anonymized stats
    total_sessions = await db.user_sessions_history.count_documents(
        {"user_id": {"$in": employee_ids}, "completed": True}
    )
    
    total_time_pipeline = [
        {"$match": {"user_id": {"$in": employee_ids}, "completed": True}},
        {"$group": {"_id": None, "total": {"$sum": "$actual_duration"}}}
    ]
    total_time_result = await db.user_sessions_history.aggregate(total_time_pipeline).to_list(1)
    total_time = total_time_result[0]["total"] if total_time_result else 0
    
    # Category distribution
    category_pipeline = [
        {"$match": {"user_id": {"$in": employee_ids}, "completed": True}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}, "time": {"$sum": "$actual_duration"}}}
    ]
    category_stats = await db.user_sessions_history.aggregate(category_pipeline).to_list(10)
    
    # Weekly activity (last 4 weeks)
    four_weeks_ago = (datetime.now(timezone.utc) - timedelta(days=28)).isoformat()
    weekly_pipeline = [
        {"$match": {
            "user_id": {"$in": employee_ids},
            "completed": True,
            "completed_at": {"$gte": four_weeks_ago}
        }},
        {"$group": {
            "_id": {"$substr": ["$completed_at", 0, 10]},
            "sessions": {"$sum": 1},
            "time": {"$sum": "$actual_duration"}
        }},
        {"$sort": {"_id": 1}}
    ]
    daily_activity = await db.user_sessions_history.aggregate(weekly_pipeline).to_list(28)
    
    # Active employees (used app this week)
    one_week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    active_employees = await db.user_sessions_history.distinct(
        "user_id",
        {
            "user_id": {"$in": employee_ids},
            "completed_at": {"$gte": one_week_ago}
        }
    )
    
    # Average per employee
    avg_time_per_employee = total_time / len(employee_ids) if employee_ids else 0
    avg_sessions_per_employee = total_sessions / len(employee_ids) if employee_ids else 0
    
    return {
        "company_name": company["name"],
        "employee_count": len(employee_ids),
        "active_employees_this_week": len(active_employees),
        "engagement_rate": round(len(active_employees) / len(employee_ids) * 100, 1) if employee_ids else 0,
        "total_sessions": total_sessions,
        "total_time_minutes": total_time,
        "avg_time_per_employee": round(avg_time_per_employee, 1),
        "avg_sessions_per_employee": round(avg_sessions_per_employee, 1),
        "category_distribution": {
            stat["_id"]: {"sessions": stat["count"], "time": stat["time"]}
            for stat in category_stats
        },
        "daily_activity": daily_activity,
        "qvt_score": min(100, round(len(active_employees) / len(employee_ids) * 100 + (total_time / len(employee_ids) / 10) if employee_ids else 0, 1))
    }

@api_router.post("/b2b/invite")
async def invite_employee(
    invite: InviteEmployee,
    user: dict = Depends(get_current_user)
):
    """Invite an employee to the company"""
    company_id = user.get("company_id")
    
    if not company_id or not user.get("is_company_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Check if email domain matches company domain
    company = await db.companies.find_one(
        {"company_id": company_id},
        {"_id": 0}
    )
    
    email_domain = invite.email.split("@")[1]
    if email_domain != company["domain"]:
        raise HTTPException(
            status_code=400,
            detail=f"Email must be from {company['domain']} domain"
        )
    
    # Create invitation
    invite_id = f"invite_{uuid.uuid4().hex[:12]}"
    invite_doc = {
        "invite_id": invite_id,
        "company_id": company_id,
        "email": invite.email,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    }
    
    await db.company_invites.insert_one(invite_doc)
    
    return {"invite_id": invite_id, "email": invite.email, "status": "pending"}

@api_router.get("/b2b/employees")
async def get_employees(user: dict = Depends(get_current_user)):
    """Get list of company employees (anonymized for privacy)"""
    company_id = user.get("company_id")
    
    if not company_id or not user.get("is_company_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    company = await db.companies.find_one(
        {"company_id": company_id},
        {"_id": 0}
    )
    
    employee_ids = company.get("employees", [])
    
    # Get anonymized employee stats
    employees = []
    for i, emp_id in enumerate(employee_ids):
        emp = await db.users.find_one({"user_id": emp_id}, {"_id": 0})
        if emp:
            sessions = await db.user_sessions_history.count_documents(
                {"user_id": emp_id, "completed": True}
            )
            employees.append({
                "employee_number": i + 1,
                "name": emp.get("name", "Collaborateur"),
                "total_time": emp.get("total_time_invested", 0),
                "streak_days": emp.get("streak_days", 0),
                "total_sessions": sessions,
                "is_admin": emp_id == user["user_id"]
            })
    
    return {"employees": employees, "total": len(employees)}

# ============== OBJECTIVES (PARCOURS PERSONNALISÉS) ==============

@api_router.post("/objectives")
@limiter.limit("10/minute")
async def create_objective(request: Request, obj: ObjectiveCreate, user: dict = Depends(get_current_user)):
    """Create a new personal objective with AI-generated curriculum."""
    # Free users: max 2 active objectives. Premium: unlimited.
    active_count = await db.objectives.count_documents({"user_id": user["user_id"], "status": "active"})
    max_objectives = 2 if user.get("subscription_tier") != "premium" else 20
    if active_count >= max_objectives:
        tier_msg = "Passe en Premium pour plus d'objectifs !" if user.get("subscription_tier") != "premium" else "Maximum 20 objectifs actifs."
        raise HTTPException(status_code=400, detail=f"Limite atteinte ({max_objectives} objectifs actifs). {tier_msg}")

    now = datetime.now(timezone.utc).isoformat()
    objective_id = f"obj_{uuid.uuid4().hex[:12]}"

    objective_doc = {
        "objective_id": objective_id,
        "user_id": user["user_id"],
        "title": obj.title.strip(),
        "description": (obj.description or "").strip(),
        "target_duration_days": min(max(obj.target_duration_days or 30, 7), 365),
        "daily_minutes": min(max(obj.daily_minutes or 10, 2), 60),
        "category": obj.category or "learning",
        "status": "active",
        "created_at": now,
        "started_at": now,
        "current_day": 0,
        "total_sessions": 0,
        "total_minutes": 0,
        "streak_days": 0,
        "last_session_date": None,
        "curriculum": [],  # Will be populated by curriculum engine
        "progress_log": [],  # Track what was learned per session
    }

    await db.objectives.insert_one(objective_doc)

    # Generate curriculum in background (non-blocking)
    asyncio.create_task(_generate_curriculum_for_objective(objective_doc, user))

    await track_event(db, user["user_id"], "objective_created", {
        "objective_id": objective_id,
        "title": obj.title,
        "target_days": objective_doc["target_duration_days"],
    })

    # Return without _id
    objective_doc.pop("_id", None)
    return objective_doc


async def _generate_curriculum_for_objective(objective: dict, user: dict):
    """Background task: generate AI curriculum for an objective."""
    try:
        from services.curriculum_engine import generate_curriculum
        curriculum = await generate_curriculum(objective, user)
        if curriculum:
            await db.objectives.update_one(
                {"objective_id": objective["objective_id"]},
                {"$set": {"curriculum": curriculum, "curriculum_generated_at": datetime.now(timezone.utc).isoformat()}}
            )
            logger.info(f"Curriculum generated for {objective['objective_id']}: {len(curriculum)} steps")
    except Exception as e:
        logger.error(f"Curriculum generation failed for {objective['objective_id']}: {e}")


@api_router.get("/objectives")
@limiter.limit("30/minute")
async def list_objectives(request: Request, status: Optional[str] = None, user: dict = Depends(get_current_user)):
    """List user's objectives, optionally filtered by status."""
    query = {"user_id": user["user_id"]}
    if status:
        query["status"] = status
    objectives = await db.objectives.find(query, {"_id": 0}).sort("created_at", -1).to_list(50)
    return {"objectives": objectives}


@api_router.get("/objectives/{objective_id}")
@limiter.limit("30/minute")
async def get_objective(request: Request, objective_id: str, user: dict = Depends(get_current_user)):
    """Get a single objective with full curriculum and progress."""
    obj = await db.objectives.find_one(
        {"objective_id": objective_id, "user_id": user["user_id"]},
        {"_id": 0}
    )
    if not obj:
        raise HTTPException(status_code=404, detail="Objectif non trouvé")
    return obj


@api_router.put("/objectives/{objective_id}")
@limiter.limit("15/minute")
async def update_objective(request: Request, objective_id: str, updates: ObjectiveUpdate, user: dict = Depends(get_current_user)):
    """Update an objective (title, description, status, etc.)."""
    obj = await db.objectives.find_one({"objective_id": objective_id, "user_id": user["user_id"]})
    if not obj:
        raise HTTPException(status_code=404, detail="Objectif non trouvé")

    update_fields = {}
    if updates.title is not None:
        update_fields["title"] = updates.title.strip()
    if updates.description is not None:
        update_fields["description"] = updates.description.strip()
    if updates.target_duration_days is not None:
        update_fields["target_duration_days"] = min(max(updates.target_duration_days, 7), 365)
    if updates.daily_minutes is not None:
        update_fields["daily_minutes"] = min(max(updates.daily_minutes, 2), 60)
    if updates.status is not None:
        if updates.status not in ("active", "paused", "completed", "abandoned"):
            raise HTTPException(status_code=400, detail="Statut invalide")
        update_fields["status"] = updates.status
        if updates.status == "completed":
            update_fields["completed_at"] = datetime.now(timezone.utc).isoformat()

    if not update_fields:
        raise HTTPException(status_code=400, detail="Aucune modification")

    update_fields["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.objectives.update_one({"objective_id": objective_id}, {"$set": update_fields})

    await track_event(db, user["user_id"], "objective_updated", {
        "objective_id": objective_id,
        "fields": list(update_fields.keys()),
    })

    updated = await db.objectives.find_one({"objective_id": objective_id}, {"_id": 0})
    return updated


@api_router.delete("/objectives/{objective_id}")
@limiter.limit("10/minute")
async def delete_objective(request: Request, objective_id: str, user: dict = Depends(get_current_user)):
    """Delete an objective permanently."""
    result = await db.objectives.delete_one({"objective_id": objective_id, "user_id": user["user_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Objectif non trouvé")

    await track_event(db, user["user_id"], "objective_deleted", {"objective_id": objective_id})
    return {"deleted": True}


@api_router.get("/objectives/{objective_id}/next")
@limiter.limit("20/minute")
async def get_next_objective_session(request: Request, objective_id: str, user: dict = Depends(get_current_user)):
    """Get the next micro-session for an objective based on curriculum progress."""
    obj = await db.objectives.find_one(
        {"objective_id": objective_id, "user_id": user["user_id"]},
        {"_id": 0}
    )
    if not obj:
        raise HTTPException(status_code=404, detail="Objectif non trouvé")
    if obj["status"] != "active":
        raise HTTPException(status_code=400, detail="Objectif non actif")

    curriculum = obj.get("curriculum", [])
    if not curriculum:
        return {"status": "generating", "message": "Le curriculum est en cours de génération..."}

    # ── Spaced repetition: check for overdue reviews ──
    from services.spaced_repetition import get_review_queue, seed_reviews_from_curriculum
    await seed_reviews_from_curriculum(db, user["user_id"], objective_id, curriculum)
    review_queue = await get_review_queue(db, user["user_id"], objective_id)

    if review_queue:
        # Overdue review takes priority over new material
        top_review = review_queue[0]
        # Find a completed step matching this skill to use as review template
        review_step = None
        for step in reversed(curriculum):
            if step.get("completed") and (step.get("focus") or "").strip() == top_review["skill"]:
                review_step = step
                break

        if review_step:
            return {
                "status": "review",
                "objective_id": objective_id,
                "objective_title": obj["title"],
                "step": {
                    **review_step,
                    "completed": False,
                    "title": f"Révision : {review_step.get('title', top_review['skill'])}",
                    "review": True,
                    "review_skill": top_review["skill"],
                    "days_overdue": top_review["days_overdue"],
                },
                "review_info": {
                    "skill": top_review["skill"],
                    "days_overdue": top_review["days_overdue"],
                    "reviews_due": len(review_queue),
                },
                "progress": {
                    "current_day": obj.get("current_day", 0),
                    "total_days": obj["target_duration_days"],
                    "total_sessions": obj.get("total_sessions", 0),
                    "total_minutes": obj.get("total_minutes", 0),
                    "percent": round((obj.get("current_day", 0) / max(obj["target_duration_days"], 1)) * 100, 1),
                },
            }

    # Find next uncompleted step
    current_day = obj.get("current_day", 0)
    next_step = None
    for step in curriculum:
        if step.get("day", 0) >= current_day and not step.get("completed"):
            next_step = step
            break

    if not next_step:
        # All steps completed — generate next batch or mark complete
        return {
            "status": "completed",
            "message": f"Bravo ! Tu as terminé le parcours \"{obj['title']}\" !",
            "total_sessions": obj.get("total_sessions", 0),
            "total_minutes": obj.get("total_minutes", 0),
        }

    # Build session memory: last 5 completed steps with notes
    progress_log = obj.get("progress_log", [])
    recent_sessions = progress_log[-5:] if progress_log else []

    # Build memory context string for the frontend/coach
    memory_context = None
    if recent_sessions:
        lines = []
        for entry in recent_sessions:
            line = f"Jour {entry.get('day', '?')}: {entry.get('step_title', '?')}"
            if entry.get("notes"):
                line += f" — Notes: {entry['notes']}"
            if entry.get("duration"):
                line += f" ({entry['duration']} min)"
            lines.append(line)
        memory_context = "\n".join(lines)

    return {
        "status": "ready",
        "objective_id": objective_id,
        "objective_title": obj["title"],
        "step": next_step,
        "progress": {
            "current_day": current_day,
            "total_days": obj["target_duration_days"],
            "total_sessions": obj.get("total_sessions", 0),
            "total_minutes": obj.get("total_minutes", 0),
            "percent": round((current_day / max(obj["target_duration_days"], 1)) * 100, 1),
        },
        "memory": {
            "recent_sessions": recent_sessions,
            "context": memory_context,
            "last_notes": recent_sessions[-1].get("notes", "") if recent_sessions else "",
            "last_focus": recent_sessions[-1].get("step_title", "") if recent_sessions else "",
        },
    }


@api_router.post("/objectives/{objective_id}/complete-step")
@limiter.limit("15/minute")
async def complete_objective_step(request: Request, objective_id: str, user: dict = Depends(get_current_user)):
    """Mark the current step as completed after a session."""
    body = await request.json()
    step_index = body.get("step_index", 0)
    actual_duration = body.get("actual_duration", 0)
    notes = body.get("notes", "")
    completed = body.get("completed", True)

    obj = await db.objectives.find_one({"objective_id": objective_id, "user_id": user["user_id"]})
    if not obj:
        raise HTTPException(status_code=404, detail="Objectif non trouvé")

    curriculum = obj.get("curriculum", [])
    if step_index < 0 or step_index >= len(curriculum):
        raise HTTPException(status_code=400, detail="Index d'étape invalide")

    now = datetime.now(timezone.utc).isoformat()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Mark step
    update_ops = {
        f"curriculum.{step_index}.completed": completed,
        f"curriculum.{step_index}.completed_at": now,
        f"curriculum.{step_index}.actual_duration": actual_duration,
        f"curriculum.{step_index}.notes": notes,
    }

    # Update objective stats
    inc_ops = {"total_sessions": 1, "total_minutes": actual_duration}

    # Streak for this objective
    last_date = obj.get("last_session_date")
    new_day = obj.get("current_day", 0)
    obj_streak = obj.get("streak_days", 0)
    if last_date != today:
        new_day += 1
        if last_date == (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d"):
            obj_streak += 1
        elif last_date is None:
            obj_streak = 1
        else:
            obj_streak = 1  # streak broken

    update_ops["current_day"] = new_day
    update_ops["streak_days"] = obj_streak
    update_ops["last_session_date"] = today

    # Progress log entry
    progress_entry = {
        "day": new_day,
        "step_index": step_index,
        "step_title": curriculum[step_index].get("title", ""),
        "duration": actual_duration,
        "completed": completed,
        "notes": notes,
        "date": now,
    }

    await db.objectives.update_one(
        {"objective_id": objective_id},
        {
            "$set": update_ops,
            "$inc": inc_ops,
            "$push": {"progress_log": progress_entry},
        }
    )

    await track_event(db, user["user_id"], "objective_step_completed", {
        "objective_id": objective_id,
        "step_index": step_index,
        "day": new_day,
        "duration": actual_duration,
    })

    # ── Adaptive difficulty (C.4) ──────────────
    # Track performance signal for this step
    step = curriculum[step_index]
    expected_min = step.get("duration_min", 5)
    expected_max = step.get("duration_max", 15)
    difficulty = step.get("difficulty", 1)

    performance = "normal"
    if completed and actual_duration > 0:
        if actual_duration < expected_min * 0.8:
            performance = "fast"  # Completed much faster than expected
        elif actual_duration > expected_max * 1.3:
            performance = "slow"  # Took much longer than expected
    elif not completed:
        performance = "abandoned"

    # Store performance signal on the step
    await db.objectives.update_one(
        {"objective_id": objective_id},
        {"$set": {
            f"curriculum.{step_index}.performance": performance,
            f"curriculum.{step_index}.difficulty_feedback": difficulty,
        }}
    )

    # Check if objective is now complete
    completed_steps = sum(1 for s in curriculum if s.get("completed")) + (1 if completed else 0)
    total_steps = len(curriculum)
    is_finished = completed_steps >= total_steps

    # Adaptive hint for frontend
    adaptive_hint = None
    if performance == "fast":
        adaptive_hint = "Tu progresses vite ! Les prochaines sessions seront plus stimulantes."
    elif performance == "abandoned":
        adaptive_hint = "Pas de souci. La prochaine session sera un peu plus douce."

    return {
        "success": True,
        "day": new_day,
        "streak": obj_streak,
        "completed_steps": completed_steps,
        "total_steps": total_steps,
        "is_finished": is_finished,
        "progress_percent": round((completed_steps / max(total_steps, 1)) * 100, 1),
        "performance": performance,
        "adaptive_hint": adaptive_hint,
    }


# ============== SKILL GRAPH + ADAPTIVE DIFFICULTY ==============

@api_router.get("/objectives/{objective_id}/skills")
@limiter.limit("20/minute")
async def get_objective_skills(request: Request, objective_id: str, user: dict = Depends(get_current_user)):
    """Compute skill graph from curriculum focus fields and completion data.

    Returns skills with mastery %, level labels, and spaced repetition flags.
    """
    obj = await db.objectives.find_one(
        {"objective_id": objective_id, "user_id": user["user_id"]},
        {"_id": 0}
    )
    if not obj:
        raise HTTPException(status_code=404, detail="Objectif non trouvé")

    curriculum = obj.get("curriculum", [])
    if not curriculum:
        return {"skills": [], "overall_mastery": 0, "level": "Non démarré"}

    # ── Aggregate by focus (skill) ──────────────
    skill_data = {}
    for step in curriculum:
        focus = (step.get("focus") or "").strip()
        if not focus:
            continue
        if focus not in skill_data:
            skill_data[focus] = {
                "total": 0,
                "completed": 0,
                "total_minutes": 0,
                "max_difficulty": 0,
                "last_practiced": None,
                "steps": [],
            }
        sd = skill_data[focus]
        sd["total"] += 1
        sd["max_difficulty"] = max(sd["max_difficulty"], step.get("difficulty", 1))
        if step.get("completed"):
            sd["completed"] += 1
            sd["total_minutes"] += step.get("actual_duration", step.get("duration_min", 5))
            completed_at = step.get("completed_at")
            if completed_at and (not sd["last_practiced"] or completed_at > sd["last_practiced"]):
                sd["last_practiced"] = completed_at

    # ── Build skill cards ───────────────────────
    now = datetime.now(timezone.utc)
    skills = []
    for name, data in skill_data.items():
        mastery = round((data["completed"] / max(data["total"], 1)) * 100)

        # Level label
        if mastery == 0:
            level = "Non démarré"
        elif mastery < 25:
            level = "Débutant"
        elif mastery < 50:
            level = "En progression"
        elif mastery < 75:
            level = "Intermédiaire"
        elif mastery < 100:
            level = "Avancé"
        else:
            level = "Maîtrisé"

        # Spaced repetition flag: needs review if last practiced >3 days ago
        needs_review = False
        if data["last_practiced"]:
            try:
                last_dt = datetime.fromisoformat(data["last_practiced"])
                if last_dt.tzinfo is None:
                    last_dt = last_dt.replace(tzinfo=timezone.utc)
                days_since = (now - last_dt).days
                needs_review = days_since >= 3 and mastery < 100
            except (ValueError, TypeError):
                pass
        else:
            needs_review = False

        skills.append({
            "name": name,
            "mastery": mastery,
            "level": level,
            "sessions_done": data["completed"],
            "sessions_total": data["total"],
            "total_minutes": data["total_minutes"],
            "max_difficulty": data["max_difficulty"],
            "needs_review": needs_review,
            "last_practiced": data["last_practiced"],
        })

    # Sort by mastery ascending (weakest first — shows where to focus)
    skills.sort(key=lambda s: s["mastery"])

    # ── Overall mastery ─────────────────────────
    total_completed = sum(1 for s in curriculum if s.get("completed"))
    total_steps = len(curriculum)
    overall_mastery = round((total_completed / max(total_steps, 1)) * 100)

    if overall_mastery == 0:
        overall_level = "Non démarré"
    elif overall_mastery < 25:
        overall_level = "Débutant"
    elif overall_mastery < 50:
        overall_level = "En progression"
    elif overall_mastery < 75:
        overall_level = "Intermédiaire"
    elif overall_mastery < 100:
        overall_level = "Avancé"
    else:
        overall_level = "Maîtrisé"

    # Skills needing review count
    review_count = sum(1 for s in skills if s["needs_review"])

    return {
        "skills": skills,
        "skills_count": len(skills),
        "overall_mastery": overall_mastery,
        "level": overall_level,
        "review_needed": review_count,
    }


# ============== SPACED REPETITION FEEDBACK ==============

@api_router.post("/objectives/{objective_id}/review-feedback")
@limiter.limit("30/minute")
async def submit_review_feedback(
    request: Request,
    objective_id: str,
    user: dict = Depends(get_current_user),
):
    """Record the user's recall quality after a review session.

    Body: { "skill": "...", "quality": 1-5 }
    Quality scale:
      1 = total blackout, 2 = wrong but recognized, 3 = correct with difficulty,
      4 = correct with hesitation, 5 = perfect recall
    """
    body = await request.json()
    skill = body.get("skill", "").strip()
    quality = body.get("quality")

    if not skill:
        raise HTTPException(status_code=400, detail="Le champ 'skill' est requis")
    if not isinstance(quality, int) or quality < 1 or quality > 5:
        raise HTTPException(status_code=400, detail="'quality' doit être un entier entre 1 et 5")

    # Verify objective belongs to user
    obj = await db.objectives.find_one(
        {"objective_id": objective_id, "user_id": user["user_id"]},
        {"_id": 0, "objective_id": 1}
    )
    if not obj:
        raise HTTPException(status_code=404, detail="Objectif non trouvé")

    from services.spaced_repetition import record_review
    result = await record_review(db, user["user_id"], objective_id, skill, quality)

    await track_event(db, user["user_id"], "sr_review_submitted", {
        "objective_id": objective_id,
        "skill": skill,
        "quality": quality,
        "next_interval": result["next_interval_days"],
    })

    return result


# ============== OBJECTIVE INSIGHTS ==============

@api_router.get("/objectives/{objective_id}/insights")
@limiter.limit("10/minute")
async def get_objective_insights(request: Request, objective_id: str, user: dict = Depends(get_current_user)):
    """Return structured insights for an objective: timeline, stats, AI analysis."""
    obj = await db.objectives.find_one(
        {"objective_id": objective_id, "user_id": user["user_id"]},
        {"_id": 0}
    )
    if not obj:
        raise HTTPException(status_code=404, detail="Objectif non trouvé")

    progress_log = obj.get("progress_log", [])
    curriculum = obj.get("curriculum", [])

    # ── Computed stats ──
    completed_sessions = [e for e in progress_log if e.get("completed")]
    abandoned_sessions = [e for e in progress_log if not e.get("completed")]
    durations = [e.get("duration", 0) for e in completed_sessions if e.get("duration")]
    notes_entries = [e for e in progress_log if e.get("notes", "").strip()]

    avg_duration = round(sum(durations) / len(durations), 1) if durations else 0
    total_time = sum(durations)
    completion_rate = round(len(completed_sessions) / max(len(progress_log), 1) * 100, 1) if progress_log else 0

    # Session frequency: sessions per active day
    unique_days = set()
    for entry in progress_log:
        date_str = entry.get("date", "")
        if date_str:
            unique_days.add(date_str[:10])
    active_days = len(unique_days)

    # Streak analysis
    streak = obj.get("streak_days", 0)
    best_streak = streak  # simple for now

    # Difficulty curve: map completed steps to their difficulty
    difficulty_curve = []
    for entry in completed_sessions:
        step_idx = entry.get("step_index", 0)
        if step_idx < len(curriculum):
            step = curriculum[step_idx]
            difficulty_curve.append({
                "day": entry.get("day", 0),
                "difficulty": step.get("difficulty", 1),
                "duration": entry.get("duration", 0),
                "title": step.get("title", ""),
            })

    # Weekly activity: group sessions by week
    weekly_activity = {}
    for entry in progress_log:
        date_str = entry.get("date", "")
        if date_str and len(date_str) >= 10:
            try:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                week_key = dt.strftime("%Y-W%W")
                if week_key not in weekly_activity:
                    weekly_activity[week_key] = {"sessions": 0, "minutes": 0, "week": week_key}
                weekly_activity[week_key]["sessions"] += 1
                weekly_activity[week_key]["minutes"] += entry.get("duration", 0)
            except (ValueError, TypeError):
                pass
    weekly_data = sorted(weekly_activity.values(), key=lambda x: x["week"])

    # ── AI analysis (cached in the objective doc, refreshed every 6h) ──
    ai_analysis = obj.get("ai_insights_cache", {})
    cache_age_ok = False
    if ai_analysis.get("generated_at"):
        try:
            gen_time = datetime.fromisoformat(ai_analysis["generated_at"].replace("Z", "+00:00"))
            cache_age_ok = (datetime.now(timezone.utc) - gen_time).total_seconds() < 6 * 3600
        except (ValueError, TypeError):
            pass

    if not cache_age_ok and len(completed_sessions) >= 3:
        # Generate fresh AI analysis
        notes_text = "\n".join(
            f"Jour {e.get('day', '?')} — {e.get('step_title', '?')} ({e.get('duration', '?')}min): {e.get('notes', '')}"
            for e in progress_log[-15:]  # Last 15 sessions max
        )
        analysis_prompt = f"""Analyse la progression d'un utilisateur sur l'objectif "{obj.get('title', '')}".

Données:
- {len(completed_sessions)} sessions complétées, {len(abandoned_sessions)} abandonnées
- Durée moyenne: {avg_duration} min, Total: {total_time} min
- Streak actuel: {streak} jours
- Taux de complétion: {completion_rate}%
- Jour actuel: {obj.get('current_day', 0)}/{obj.get('target_duration_days', 30)}

Journal des sessions récentes:
{notes_text}

Retourne une analyse JSON avec cette structure exacte:
{{
  "summary": "2-3 phrases de bilan global de la progression",
  "strengths": ["point fort 1", "point fort 2"],
  "improvements": ["axe d'amélioration 1", "axe d'amélioration 2"],
  "next_advice": "1 conseil concret et actionnable pour la prochaine session",
  "momentum": "rising" | "stable" | "declining",
  "momentum_label": "En progression" | "Stable" | "En baisse"
}}

Sois bienveillant, concret et motivant. Réponds UNIQUEMENT avec le JSON, rien d'autre."""

        is_premium = user.get("subscription_tier") == "premium"
        ai_model = "claude-sonnet-4-20250514" if is_premium else None
        raw = await call_ai("insights", AI_SYSTEM_MESSAGE, analysis_prompt, model=ai_model)

        if raw:
            try:
                # Extract JSON from response
                import re as _re
                json_match = _re.search(r'\{[\s\S]*\}', raw)
                if json_match:
                    ai_analysis = json.loads(json_match.group())
                    ai_analysis["generated_at"] = datetime.now(timezone.utc).isoformat()
                    # Cache in DB
                    await db.objectives.update_one(
                        {"objective_id": objective_id},
                        {"$set": {"ai_insights_cache": ai_analysis}}
                    )
            except (json.JSONDecodeError, Exception) as e:
                logger.error(f"Insights AI parse error: {e}")
                ai_analysis = {}

    # ── Build response ──
    return {
        "objective_id": objective_id,
        "title": obj.get("title", ""),
        "stats": {
            "total_sessions": len(completed_sessions),
            "abandoned_sessions": len(abandoned_sessions),
            "completion_rate": completion_rate,
            "avg_duration": avg_duration,
            "total_minutes": total_time,
            "active_days": active_days,
            "current_streak": streak,
            "current_day": obj.get("current_day", 0),
            "target_days": obj.get("target_duration_days", 30),
        },
        "timeline": progress_log,
        "notes": [
            {
                "day": e.get("day"),
                "step_title": e.get("step_title", ""),
                "notes": e.get("notes", ""),
                "date": e.get("date", ""),
                "duration": e.get("duration", 0),
            }
            for e in notes_entries
        ],
        "difficulty_curve": difficulty_curve,
        "weekly_activity": weekly_data,
        "ai_analysis": ai_analysis if ai_analysis and ai_analysis.get("summary") else None,
    }


# ============== ROUTINES ==============

@api_router.post("/routines")
@limiter.limit("10/minute")
async def create_routine(request: Request, routine: RoutineCreate, user: dict = Depends(get_current_user)):
    """Create a new routine (ordered sequence of micro-actions / objective steps)."""
    # Free: max 3 routines, Premium: 20
    count = await db.routines.count_documents({"user_id": user["user_id"], "deleted": {"$ne": True}})
    max_routines = 3 if user.get("subscription_tier") != "premium" else 20
    if count >= max_routines:
        raise HTTPException(status_code=400, detail=f"Limite atteinte ({max_routines} routines).")

    now = datetime.now(timezone.utc).isoformat()
    routine_id = f"rtn_{uuid.uuid4().hex[:12]}"

    # Validate and normalize items
    validated_items = []
    for i, item in enumerate(routine.items or []):
        validated_items.append({
            "type": item.get("type", "action"),  # action | objective_step
            "ref_id": item.get("ref_id", ""),
            "title": item.get("title", "Sans titre"),
            "duration_minutes": min(max(int(item.get("duration_minutes", 5)), 1), 120),
            "order": i,
        })

    # Frequency
    freq = routine.frequency if routine.frequency in ("daily", "weekdays", "weekends", "custom") else "daily"
    freq_days = None
    if freq == "custom" and routine.frequency_days:
        freq_days = [d for d in routine.frequency_days if 0 <= d <= 6]
    elif freq == "weekdays":
        freq_days = [0, 1, 2, 3, 4]
    elif freq == "weekends":
        freq_days = [5, 6]

    doc = {
        "routine_id": routine_id,
        "user_id": user["user_id"],
        "name": routine.name.strip()[:100],
        "description": (routine.description or "").strip()[:2000],
        "time_of_day": routine.time_of_day if routine.time_of_day in ("morning", "afternoon", "evening", "anytime") else "morning",
        "frequency": freq,
        "frequency_days": freq_days,
        "items": validated_items,
        "is_active": True,
        "total_minutes": sum(it["duration_minutes"] for it in validated_items),
        "times_completed": 0,
        "streak_current": 0,
        "streak_best": 0,
        "completion_log": [],  # [{date: "2026-03-11", completed_at: "..."}]
        "last_completed_at": None,
        "created_at": now,
        "updated_at": now,
    }
    await db.routines.insert_one(doc)
    doc.pop("_id", None)
    return doc


@api_router.get("/routines")
@limiter.limit("30/minute")
async def list_routines(request: Request, user: dict = Depends(get_current_user)):
    """List all routines for the user."""
    routines = await db.routines.find(
        {"user_id": user["user_id"], "deleted": {"$ne": True}},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    return {"routines": routines, "count": len(routines)}


@api_router.get("/routines/{routine_id}")
@limiter.limit("30/minute")
async def get_routine(request: Request, routine_id: str, user: dict = Depends(get_current_user)):
    """Get a single routine by ID."""
    routine = await db.routines.find_one(
        {"routine_id": routine_id, "user_id": user["user_id"], "deleted": {"$ne": True}},
        {"_id": 0}
    )
    if not routine:
        raise HTTPException(status_code=404, detail="Routine non trouvée.")
    return routine


@api_router.put("/routines/{routine_id}")
@limiter.limit("15/minute")
async def update_routine(request: Request, routine_id: str, update: RoutineUpdate, user: dict = Depends(get_current_user)):
    """Update a routine (name, items, active status, etc.)."""
    routine = await db.routines.find_one(
        {"routine_id": routine_id, "user_id": user["user_id"], "deleted": {"$ne": True}}
    )
    if not routine:
        raise HTTPException(status_code=404, detail="Routine non trouvée.")

    now = datetime.now(timezone.utc).isoformat()
    updates = {"updated_at": now}

    if update.name is not None:
        updates["name"] = update.name.strip()[:100]
    if update.description is not None:
        updates["description"] = update.description.strip()[:2000]
    if update.time_of_day is not None and update.time_of_day in ("morning", "afternoon", "evening", "anytime"):
        updates["time_of_day"] = update.time_of_day
    if update.frequency is not None and update.frequency in ("daily", "weekdays", "weekends", "custom"):
        updates["frequency"] = update.frequency
        if update.frequency == "custom" and update.frequency_days:
            updates["frequency_days"] = [d for d in update.frequency_days if 0 <= d <= 6]
        elif update.frequency == "weekdays":
            updates["frequency_days"] = [0, 1, 2, 3, 4]
        elif update.frequency == "weekends":
            updates["frequency_days"] = [5, 6]
        else:
            updates["frequency_days"] = None
    if update.is_active is not None:
        updates["is_active"] = update.is_active
    if update.items is not None:
        validated_items = []
        for i, item in enumerate(update.items):
            validated_items.append({
                "type": item.get("type", "action"),
                "ref_id": item.get("ref_id", ""),
                "title": item.get("title", "Sans titre"),
                "duration_minutes": min(max(int(item.get("duration_minutes", 5)), 1), 120),
                "order": i,
            })
        updates["items"] = validated_items
        updates["total_minutes"] = sum(it["duration_minutes"] for it in validated_items)

    await db.routines.update_one({"routine_id": routine_id}, {"$set": updates})
    updated = await db.routines.find_one({"routine_id": routine_id}, {"_id": 0})
    return updated


@api_router.delete("/routines/{routine_id}")
@limiter.limit("10/minute")
async def delete_routine(request: Request, routine_id: str, user: dict = Depends(get_current_user)):
    """Soft-delete a routine."""
    result = await db.routines.update_one(
        {"routine_id": routine_id, "user_id": user["user_id"], "deleted": {"$ne": True}},
        {"$set": {"deleted": True, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Routine non trouvée.")
    return {"status": "deleted", "routine_id": routine_id}


@api_router.post("/routines/{routine_id}/complete")
@limiter.limit("20/minute")
async def complete_routine(request: Request, routine_id: str, user: dict = Depends(get_current_user)):
    """Mark a routine as completed — updates streak, completion log, counter."""
    routine = await db.routines.find_one(
        {"routine_id": routine_id, "user_id": user["user_id"], "deleted": {"$ne": True}}
    )
    if not routine:
        raise HTTPException(status_code=404, detail="Routine non trouvée.")

    now = datetime.now(timezone.utc)
    today_str = now.strftime("%Y-%m-%d")

    # Prevent double-completion for same day
    completion_log = routine.get("completion_log", [])
    if any(entry.get("date") == today_str for entry in completion_log):
        return {
            "status": "already_completed",
            "routine_id": routine_id,
            "times_completed": routine.get("times_completed", 0),
            "streak_current": routine.get("streak_current", 0),
        }

    # Calculate streak
    streak = routine.get("streak_current", 0)
    last_completed = routine.get("last_completed_at")
    if last_completed:
        try:
            last_date = datetime.fromisoformat(last_completed.replace("Z", "+00:00")).date()
            today_date = now.date()
            diff = (today_date - last_date).days
            if diff == 1:
                streak += 1  # Consecutive day
            elif diff > 1:
                streak = 1  # Streak broken
            else:
                streak = max(streak, 1)
        except (ValueError, AttributeError):
            streak = 1
    else:
        streak = 1

    best_streak = max(routine.get("streak_best", 0), streak)

    # Add to completion log (keep last 90 entries)
    completion_log.append({"date": today_str, "completed_at": now.isoformat()})
    completion_log = completion_log[-90:]

    # Week completion rate (last 7 days)
    week_ago = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    week_completions = sum(1 for e in completion_log if e["date"] >= week_ago)

    await db.routines.update_one(
        {"routine_id": routine_id},
        {
            "$inc": {"times_completed": 1},
            "$set": {
                "last_completed_at": now.isoformat(),
                "updated_at": now.isoformat(),
                "streak_current": streak,
                "streak_best": best_streak,
                "completion_log": completion_log,
            },
        }
    )

    new_count = routine.get("times_completed", 0) + 1
    return {
        "status": "completed",
        "routine_id": routine_id,
        "times_completed": new_count,
        "streak_current": streak,
        "streak_best": best_streak,
        "week_completions": week_completions,
    }


# ============== iCAL EXPORT ==============

def _ical_escape(text: str) -> str:
    """Escape special characters for iCal format."""
    return text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")

def _fold_line(line: str) -> str:
    """Fold long iCal lines at 75 octets per RFC 5545."""
    result = []
    while len(line.encode("utf-8")) > 75:
        # Find a safe split point
        cut = 75
        while len(line[:cut].encode("utf-8")) > 75:
            cut -= 1
        result.append(line[:cut])
        line = " " + line[cut:]
    result.append(line)
    return "\r\n".join(result)

@api_router.get("/routines/{routine_id}/ical")
async def export_routine_ical(routine_id: str, user: dict = Depends(get_current_user)):
    """Generate a .ics file for a routine — recurring event matching the routine's frequency."""
    routine = await db.routines.find_one(
        {"routine_id": routine_id, "user_id": user["user_id"], "deleted": {"$ne": True}}
    )
    if not routine:
        raise HTTPException(status_code=404, detail="Routine non trouvée.")

    name = _ical_escape(routine.get("name", "Routine InFinea"))
    desc_parts = [routine.get("description", "")]
    items = routine.get("items", [])
    if items:
        desc_parts.append("Actions :")
        for i, item in enumerate(items, 1):
            desc_parts.append(f"{i}. {item.get('title', '')} ({item.get('duration_minutes', 5)} min)")
    description = _ical_escape("\\n".join(p for p in desc_parts if p))

    total_min = routine.get("total_minutes", 15)
    tod = routine.get("time_of_day", "morning")
    start_hour = {"morning": "08", "afternoon": "13", "evening": "19", "anytime": "09"}.get(tod, "09")

    # Frequency mapping
    freq = routine.get("frequency", "daily")
    freq_days = routine.get("frequency_days", [])
    if freq == "daily":
        rrule = "RRULE:FREQ=DAILY"
    elif freq == "weekdays":
        rrule = "RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR"
    elif freq == "weekends":
        rrule = "RRULE:FREQ=WEEKLY;BYDAY=SA,SU"
    elif freq == "custom" and freq_days:
        day_map = {0: "MO", 1: "TU", 2: "WE", 3: "TH", 4: "FR", 5: "SA", 6: "SU"}
        days = ",".join(day_map.get(d, "MO") for d in sorted(freq_days))
        rrule = f"RRULE:FREQ=WEEKLY;BYDAY={days}"
    else:
        rrule = "RRULE:FREQ=DAILY"

    now = datetime.now(timezone.utc)
    # Start tomorrow
    tomorrow = now + timedelta(days=1)
    dtstart = tomorrow.strftime(f"%Y%m%dT{start_hour}0000")
    # End = start + duration
    end_h = int(start_hour) + (total_min // 60)
    end_m = total_min % 60
    dtend = tomorrow.strftime(f"%Y%m%dT{end_h:02d}{end_m:02d}00")
    uid = f"routine-{routine_id}@infinea.app"
    stamp = now.strftime("%Y%m%dT%H%M%SZ")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//InFinea//Routine Export//FR",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{stamp}",
        f"DTSTART:{dtstart}",
        f"DTEND:{dtend}",
        rrule,
        _fold_line(f"SUMMARY:{name}"),
        _fold_line(f"DESCRIPTION:{description}"),
        "BEGIN:VALARM",
        "TRIGGER:-PT5M",
        "ACTION:DISPLAY",
        f"DESCRIPTION:Routine {name} dans 5 minutes",
        "END:VALARM",
        "END:VEVENT",
        "END:VCALENDAR",
    ]
    ics_content = "\r\n".join(lines) + "\r\n"

    filename = f"infinea-routine-{routine_id[:8]}.ics"
    return Response(
        content=ics_content,
        media_type="text/calendar; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

@api_router.get("/objectives/{objective_id}/ical")
async def export_objective_ical(objective_id: str, user: dict = Depends(get_current_user)):
    """Generate a .ics file for an objective — daily session for the duration of the parcours."""
    obj = await db.objectives.find_one(
        {"objective_id": objective_id, "user_id": user["user_id"], "deleted": {"$ne": True}}
    )
    if not obj:
        raise HTTPException(status_code=404, detail="Objectif non trouvé.")

    name = _ical_escape(obj.get("title", "Objectif InFinea"))
    daily_min = obj.get("daily_minutes", 10)
    duration_days = obj.get("target_duration_days", 30)
    description = _ical_escape(f"Parcours InFinea : {name}\\n{daily_min} min/jour pendant {duration_days} jours")

    now = datetime.now(timezone.utc)
    tomorrow = now + timedelta(days=1)
    dtstart = tomorrow.strftime("%Y%m%dT090000")
    end_m = daily_min % 60
    end_h = 9 + (daily_min // 60)
    dtend = tomorrow.strftime(f"%Y%m%dT{end_h:02d}{end_m:02d}00")
    until = (tomorrow + timedelta(days=duration_days)).strftime("%Y%m%dT235959Z")
    uid = f"objective-{objective_id}@infinea.app"
    stamp = now.strftime("%Y%m%dT%H%M%SZ")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//InFinea//Objective Export//FR",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{stamp}",
        f"DTSTART:{dtstart}",
        f"DTEND:{dtend}",
        f"RRULE:FREQ=DAILY;UNTIL={until}",
        _fold_line(f"SUMMARY:{name}"),
        _fold_line(f"DESCRIPTION:{description}"),
        "BEGIN:VALARM",
        "TRIGGER:-PT5M",
        "ACTION:DISPLAY",
        f"DESCRIPTION:Session {name} dans 5 minutes",
        "END:VALARM",
        "END:VEVENT",
        "END:VCALENDAR",
    ]
    ics_content = "\r\n".join(lines) + "\r\n"

    filename = f"infinea-objectif-{objective_id[:8]}.ics"
    return Response(
        content=ics_content,
        media_type="text/calendar; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ============== REFLECTIONS / JOURNAL ==============

@api_router.post("/reflections")
async def create_reflection(
    reflection: ReflectionCreate,
    user: dict = Depends(get_current_user)
):
    """Create a new reflection entry"""
    reflection_id = f"ref_{uuid.uuid4().hex[:12]}"
    
    reflection_doc = {
        "reflection_id": reflection_id,
        "user_id": user["user_id"],
        "content": reflection.content,
        "mood": reflection.mood,
        "tags": reflection.tags or [],
        "related_session_id": reflection.related_session_id,
        "related_category": reflection.related_category,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.reflections.insert_one(reflection_doc)
    
    return {**reflection_doc, "_id": None}

@api_router.get("/reflections")
async def get_reflections(
    user: dict = Depends(get_current_user),
    limit: int = 50,
    skip: int = 0
):
    """Get user's reflections"""
    reflections = await db.reflections.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    total = await db.reflections.count_documents({"user_id": user["user_id"]})
    
    return {"reflections": reflections, "total": total}

@api_router.get("/reflections/week")
async def get_week_reflections(user: dict = Depends(get_current_user)):
    """Get this week's reflections"""
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    
    reflections = await db.reflections.find(
        {"user_id": user["user_id"], "created_at": {"$gte": week_ago}},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return {"reflections": reflections, "count": len(reflections)}

@api_router.delete("/reflections/{reflection_id}")
async def delete_reflection(
    reflection_id: str,
    user: dict = Depends(get_current_user)
):
    """Delete a reflection"""
    result = await db.reflections.delete_one({
        "reflection_id": reflection_id,
        "user_id": user["user_id"]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Reflection not found")
    
    return {"message": "Reflection deleted"}

@api_router.get("/reflections/summary")
async def get_reflections_summary(user: dict = Depends(get_current_user)):
    """Generate AI-powered weekly summary of reflections"""
    # Get reflections from the last 4 weeks
    month_ago = (datetime.now(timezone.utc) - timedelta(days=28)).isoformat()

    reflections = await db.reflections.find(
        {"user_id": user["user_id"], "created_at": {"$gte": month_ago}},
        {"_id": 0}
    ).sort("created_at", 1).to_list(200)

    if not reflections:
        return {
            "summary": None,
            "message": "Pas encore assez de réflexions pour générer un résumé. Commencez à noter vos pensées!",
            "reflection_count": 0
        }

    # Get sessions data for context
    sessions = await db.user_sessions_history.find(
        {"user_id": user["user_id"], "completed": True, "started_at": {"$gte": month_ago}},
        {"_id": 0}
    ).to_list(100)

    # Build reflection context
    reflections_text = "\n".join([
        f"[{r['created_at'][:10]}] {r.get('mood', 'neutre')}: {r['content']}"
        for r in reflections[-30:]
    ])

    # Session stats
    category_counts = {}
    total_time = 0
    for s in sessions:
        cat = s.get("category", "autre")
        category_counts[cat] = category_counts.get(cat, 0) + 1
        total_time += s.get("actual_duration", 0)

    system_msg = """Tu es le compagnon cognitif InFinea. Ton rôle est d'analyser les réflexions
de l'utilisateur et de fournir un résumé personnalisé, bienveillant et perspicace.
Tu dois identifier les patterns, les progrès et suggérer des axes d'amélioration.
Réponds toujours en français, de manière empathique et constructive."""

    prompt = f"""Analyse les réflexions suivantes de l'utilisateur sur les 4 dernières semaines:

{reflections_text}

Contexte d'activité:
- Sessions complétées: {len(sessions)}
- Temps total investi: {total_time} minutes
- Répartition: {', '.join([f'{k}: {v}' for k, v in category_counts.items()])}

Génère un résumé structuré en JSON avec:
- "weekly_insight": Une observation clé sur les tendances de la semaine (2-3 phrases max)
- "patterns_identified": Liste de 2-3 patterns comportementaux observés
- "strengths": Ce qui fonctionne bien (1-2 points)
- "areas_for_growth": Suggestions d'amélioration bienveillantes (1-2 points)
- "personalized_tip": Un conseil personnalisé basé sur les réflexions
- "mood_trend": Tendance générale de l'humeur (positive, stable, en progression, à surveiller)"""

    response = await call_ai(f"summary_{user['user_id']}", system_msg, prompt, model=get_ai_model(user))
    ai_summary = parse_ai_json(response)

    fallback_summary = {
        "weekly_insight": "Continuez à noter vos réflexions pour un résumé plus détaillé.",
        "patterns_identified": [],
        "strengths": [],
        "areas_for_growth": [],
        "personalized_tip": "Essayez de noter au moins une réflexion par jour.",
        "mood_trend": "stable"
    }

    if not ai_summary:
        ai_summary = fallback_summary

    # Store summary for history
    summary_doc = {
        "summary_id": f"sum_{uuid.uuid4().hex[:12]}",
        "user_id": user["user_id"],
        "summary": ai_summary,
        "reflection_count": len(reflections),
        "period_start": month_ago,
        "period_end": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.reflection_summaries.insert_one(summary_doc)

    return {
        "summary": ai_summary,
        "reflection_count": len(reflections),
        "session_count": len(sessions),
        "total_time": total_time
    }

@api_router.get("/reflections/summaries")
async def get_past_summaries(
    user: dict = Depends(get_current_user),
    limit: int = 10
):
    """Get past generated summaries"""
    summaries = await db.reflection_summaries.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return {"summaries": summaries}

# ============== NOTES ROUTES ==============

NOTES_QUERY = {
    "completed": True,
    "notes": {"$exists": True, "$nin": [None, ""]}
}

@api_router.get("/notes/stats")
async def get_notes_stats(user: dict = Depends(get_current_user)):
    """Quick stats about user's session notes"""
    base_query = {"user_id": user["user_id"], **NOTES_QUERY}

    total_notes = await db.user_sessions_history.count_documents(base_query)

    week_start = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    notes_this_week = await db.user_sessions_history.count_documents({
        **base_query,
        "completed_at": {"$gte": week_start}
    })

    pipeline = [
        {"$match": base_query},
        {"$group": {"_id": "$category", "count": {"$sum": 1}}}
    ]
    category_stats = await db.user_sessions_history.aggregate(pipeline).to_list(15)
    categories = {stat["_id"]: stat["count"] for stat in category_stats if stat["_id"]}

    pipeline_avg = [
        {"$match": base_query},
        {"$project": {"note_length": {"$strLenCP": "$notes"}}},
        {"$group": {"_id": None, "avg_length": {"$avg": "$note_length"}}}
    ]
    avg_result = await db.user_sessions_history.aggregate(pipeline_avg).to_list(1)
    avg_note_length = int(avg_result[0]["avg_length"]) if avg_result else 0

    return {
        "total_notes": total_notes,
        "notes_this_week": notes_this_week,
        "categories": categories,
        "avg_note_length": avg_note_length,
    }

@api_router.get("/notes/analysis")
async def get_notes_analysis(
    user: dict = Depends(get_current_user),
    force: bool = False
):
    """AI-powered analysis of user's session notes with caching"""
    user_id = user["user_id"]
    is_premium = user.get("subscription_tier") == "premium"

    # Check cache first (unless force refresh)
    if not force:
        cache_hours = 12 if is_premium else 24
        cache_cutoff = (datetime.now(timezone.utc) - timedelta(hours=cache_hours)).isoformat()
        cached = await db.notes_analysis_cache.find_one(
            {"user_id": user_id, "generated_at": {"$gte": cache_cutoff}},
            {"_id": 0}
        )
        if cached:
            return {
                "analysis": cached["analysis"],
                "generated_at": cached["generated_at"],
                "cached": True,
                "note_count": cached.get("note_count", 0),
            }

    # Usage limit for free users (force refresh only)
    if not is_premium and force:
        usage = await check_usage_limit(user_id, "notes_analysis", 1, "daily")
        if not usage["allowed"]:
            return {
                "analysis": None,
                "error": "limit_reached",
                "message": "Vous avez atteint la limite d'analyses aujourd'hui. Passez Premium pour des analyses illimitées !",
                "usage": usage,
            }

    # Fetch notes
    lookback_days = 90 if is_premium else 30
    cutoff = (datetime.now(timezone.utc) - timedelta(days=lookback_days)).isoformat()

    sessions_with_notes = await db.user_sessions_history.find(
        {"user_id": user_id, **NOTES_QUERY, "completed_at": {"$gte": cutoff}},
        {"_id": 0}
    ).sort("completed_at", -1).to_list(50)

    if len(sessions_with_notes) < 3:
        return {
            "analysis": None,
            "message": "Complétez quelques sessions avec des notes pour générer une analyse.",
            "note_count": len(sessions_with_notes),
            "min_required": 3,
        }

    # Build notes context
    notes_text = "\n".join([
        f"[{s.get('completed_at', '')[:10]}] {s.get('action_title', 'Action')} ({s.get('category', 'autre')}): {s['notes']}"
        for s in sessions_with_notes
    ])

    cat_counts = {}
    for s in sessions_with_notes:
        cat = s.get("category", "autre")
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

    categories_fr = {
        "learning": "apprentissage", "productivity": "productivité",
        "well_being": "bien-être", "creativity": "créativité",
        "fitness": "forme physique", "mindfulness": "pleine conscience",
        "leadership": "leadership", "finance": "finance",
        "relations": "relations", "mental_health": "santé mentale",
        "entrepreneurship": "entrepreneuriat",
    }
    cat_summary = ", ".join([f"{categories_fr.get(k, k)}: {v} notes" for k, v in cat_counts.items()])

    user_context = await build_user_context(user)

    system_msg = """Tu es le compagnon cognitif InFinea. Tu analyses les notes de session de l'utilisateur
pour identifier des patterns d'apprentissage, des progrès, et fournir des insights personnalisés.
Tes analyses sont profondes, bienveillantes et actionables. Réponds toujours en français.
Réponds UNIQUEMENT en JSON valide, sans texte autour."""

    if is_premium:
        prompt = f"""{user_context}

Voici les notes de session de l'utilisateur sur les 3 derniers mois ({len(sessions_with_notes)} notes) :

{notes_text}

Répartition des catégories : {cat_summary}

Fais une analyse approfondie et réponds en JSON :
{{
    "key_insight": "L'observation la plus importante sur le parcours de l'utilisateur (2-3 phrases)",
    "patterns": ["Pattern 1 identifié dans les notes", "Pattern 2", "Pattern 3"],
    "strengths": ["Point fort 1 observé", "Point fort 2"],
    "growth_areas": ["Axe de progression 1", "Axe de progression 2"],
    "emotional_trends": "Analyse de l'évolution émotionnelle à travers les notes (1-2 phrases)",
    "connections": "Liens entre différentes sessions et thèmes (1-2 phrases)",
    "personalized_recommendation": "Conseil personnalisé basé sur l'ensemble des notes (2-3 phrases)",
    "focus_suggestion": "Suggestion de focus pour la semaine à venir (1 phrase)"
}}"""
    else:
        prompt = f"""{user_context}

Voici les notes de session récentes de l'utilisateur ({len(sessions_with_notes)} notes) :

{notes_text}

Répartition : {cat_summary}

Fais une analyse et réponds en JSON :
{{
    "key_insight": "L'observation la plus importante (1-2 phrases)",
    "patterns": ["Pattern 1", "Pattern 2"],
    "strengths": ["Point fort observé"],
    "growth_areas": ["Axe de progression"],
    "personalized_recommendation": "Conseil personnalisé (1-2 phrases)"
}}"""

    ai_response = await call_ai(
        f"notes_analysis_{user_id}",
        system_msg,
        prompt,
        model=get_ai_model(user),
    )
    ai_result = parse_ai_json(ai_response)

    # Fallback if AI fails
    if not ai_result:
        top_category = max(cat_counts, key=cat_counts.get) if cat_counts else "general"
        ai_result = {
            "key_insight": f"Vous avez écrit {len(sessions_with_notes)} notes, principalement en {categories_fr.get(top_category, top_category)}. Continuez à documenter vos sessions !",
            "patterns": [],
            "strengths": ["Régularité dans la prise de notes"],
            "growth_areas": ["Essayez d'approfondir vos réflexions"],
            "personalized_recommendation": "Notez ce que vous avez appris ET ce que vous ressentez pour des analyses plus riches.",
        }

    # Cache the result
    await db.notes_analysis_cache.update_one(
        {"user_id": user_id},
        {"$set": {
            "user_id": user_id,
            "analysis": ai_result,
            "note_count": len(sessions_with_notes),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }},
        upsert=True,
    )

    return {
        "analysis": ai_result,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "cached": False,
        "note_count": len(sessions_with_notes),
    }

@api_router.get("/notes")
async def get_user_notes(
    user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 20,
    category: Optional[str] = None,
):
    """Get all sessions with non-empty notes, paginated"""
    query = {"user_id": user["user_id"], **NOTES_QUERY}
    if category:
        query["category"] = category

    total = await db.user_sessions_history.count_documents(query)

    notes = await db.user_sessions_history.find(
        query,
        {"_id": 0, "session_id": 1, "action_title": 1, "category": 1,
         "notes": 1, "completed_at": 1, "actual_duration": 1}
    ).sort("completed_at", -1).skip(skip).limit(limit).to_list(limit)

    return {
        "notes": notes,
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_more": (skip + limit) < total,
    }

@api_router.delete("/notes/{session_id}")
async def delete_note(session_id: str, user: dict = Depends(get_current_user)):
    """Clear the notes field from a session (does not delete the session itself)"""
    result = await db.user_sessions_history.update_one(
        {"session_id": session_id, "user_id": user["user_id"]},
        {"$set": {"notes": None}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Note non trouvée")
    return {"status": "success", "message": "Note supprimée"}

# ============== FEATURE FLAGS ==============

FEATURE_UNIFIED_INTEGRATIONS = os.environ.get("FEATURE_UNIFIED_INTEGRATIONS", "true") == "true"

@api_router.get("/feature-flags")
async def get_feature_flags():
    """Public feature flags for frontend conditional rendering."""
    return {
        "unified_integrations": FEATURE_UNIFIED_INTEGRATIONS,
    }

# ============== UNIFIED INTEGRATION STATUS ==============

@api_router.get("/integrations/status")
async def get_integrations_status(request: Request, user: dict = Depends(get_current_user)):
    """Unified status with smart connect routing — tells frontend exactly how to connect each service."""
    integrations_docs = await db.user_integrations.find(
        {"user_id": user["user_id"]},
        {"_id": 0, "access_token": 0, "refresh_token": 0}
    ).to_list(20)

    connected_map = {}
    for i in integrations_docs:
        key = i.get("service") or i.get("provider")
        if key:
            connected_map[key] = i

    all_services = {
        "google_calendar": {
            "name": "Google Calendar",
            "category": "calendrier",
            "description": "D\u00e9tecte automatiquement vos cr\u00e9neaux libres entre les r\u00e9unions",
        },
        "ical": {
            "name": "Apple Calendar",
            "category": "calendrier",
            "description": "Importez votre calendrier Apple pour d\u00e9tecter vos cr\u00e9neaux libres",
        },
        "notion": {
            "name": "Notion",
            "category": "notes",
            "description": "Exportez vos sessions comme pages Notion automatiquement",
        },
        "todoist": {
            "name": "Todoist",
            "category": "t\u00e2ches",
            "description": "Loguez vos sessions comme t\u00e2ches compl\u00e9t\u00e9es dans Todoist",
        },
        "slack": {
            "name": "Slack",
            "category": "communication",
            "description": "Recevez vos r\u00e9sum\u00e9s hebdomadaires directement dans Slack",
        },
    }

    # Use BACKEND_URL env var — critical for OAuth redirect_uri to match Google Console config
    backend_url = os.environ.get("BACKEND_URL", "https://infinea-api.onrender.com")

    result = {}
    for service_key, meta in all_services.items():
        connected = connected_map.get(service_key)
        config = INTEGRATION_CONFIGS.get(service_key)
        has_oauth = bool(os.environ.get(config["env_client_id"])) if config else False
        has_token = service_key in TOKEN_CONNECT_VALIDATORS
        has_url = service_key in ("ical", "google_calendar") and ICAL_AVAILABLE

        status = "disconnected"
        if connected:
            status = "error" if connected.get("last_error") else "connected"

        # Smart connect routing: determine the best method and pre-generate URL if OAuth
        preferred_method = None
        connect_url = None
        token_config = None

        if not connected:
            if service_key in ("ical", "google_calendar", "notion", "todoist", "slack"):
                preferred_method = "guided"
            elif has_oauth:
                preferred_method = "oauth"
                # Pre-generate OAuth URL so frontend redirects in one click
                try:
                    client_id = os.environ.get(config["env_client_id"])
                    state = f"{user['user_id']}:{uuid.uuid4().hex[:16]}"
                    await db.integration_states.insert_one({
                        "state": state, "user_id": user["user_id"],
                        "service": service_key,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
                    })
                    if service_key == "google_calendar":
                        # Reuse the login callback URI (already registered in Google Console)
                        redirect_uri = f"{backend_url}/api/auth/google/callback"
                        gcal_state = f"gcal_integrate:{state}"
                        await db.integration_states.update_one(
                            {"state": state}, {"$set": {"state": gcal_state}}
                        )
                        params = {"client_id": client_id, "state": gcal_state}
                        params.update({"redirect_uri": redirect_uri, "response_type": "code",
                                       "scope": config["scopes"], "access_type": "offline", "prompt": "consent"})
                    else:
                        redirect_uri = f"{backend_url}/api/integrations/callback/{service_key}"
                        params = {"client_id": client_id, "state": state}
                        if service_key == "notion":
                            params.update({"redirect_uri": redirect_uri, "response_type": "code", "owner": "user"})
                        elif service_key == "todoist":
                            params.update({"scope": config["scopes"]})
                        elif service_key == "slack":
                            params.update({"scope": config["scopes"], "redirect_uri": redirect_uri})
                    connect_url = f"{config['auth_url']}?{urllib.parse.urlencode(params)}"
                except Exception as e:
                    logger.warning(f"Failed to pre-generate OAuth URL for {service_key}: {e}")
                    if has_token:
                        preferred_method = "token"
            elif has_token:
                preferred_method = "token"
                tc = TOKEN_CONNECT_VALIDATORS.get(service_key, {})
                token_config = {
                    "label": tc.get("description", f"Token {meta['name']}"),
                    "placeholder": tc.get("placeholder", ""),
                    "help_url": tc.get("help_url", ""),
                    "service_name": tc.get("name", meta["name"]),
                }
            elif has_url:
                preferred_method = "url"

        result[service_key] = {
            **meta,
            "status": status,
            "connected": bool(connected),
            "connected_at": connected.get("connected_at") if connected else None,
            "account_name": connected.get("account_name") if connected else None,
            "last_sync": connected.get("last_synced_at") if connected else None,
            "last_error": connected.get("last_error") if connected else None,
            "available": has_oauth or has_token or has_url,
            "connection_type": connected.get("connection_type", "oauth") if connected else None,
            "preferred_method": preferred_method,
            "connect_url": connect_url,
            "token_config": token_config,
        }

    return result

@api_router.post("/integrations/{service}/test")
async def test_integration(service: str, user: dict = Depends(get_current_user)):
    """Test that a connected integration still works."""
    integration = await db.user_integrations.find_one(
        {"user_id": user["user_id"], "service": service}
    )
    if not integration:
        integration = await db.user_integrations.find_one(
            {"user_id": user["user_id"], "provider": service}
        )
    if not integration:
        raise HTTPException(status_code=404, detail="Intégration non connectée")

    encrypted_token = integration.get("access_token")
    if not encrypted_token:
        raise HTTPException(status_code=400, detail="Pas de token stocké")

    try:
        token = decrypt_token(encrypted_token)
    except Exception:
        await db.user_integrations.update_one(
            {"user_id": user["user_id"], "service": service},
            {"$set": {"last_error": "Token corrompu — reconnectez le service"}}
        )
        return {"ok": False, "error": "Token corrompu — reconnectez le service"}

    try:
        async with httpx.AsyncClient(timeout=10.0) as http_client:
            if service == "ical":
                # iCal: test by fetching the URL
                url = token
                if url.startswith("webcal://"):
                    url = "https://" + url[len("webcal://"):]
                resp = await http_client.get(url, follow_redirects=True)
                ok = resp.status_code == 200
            elif service == "google_calendar":
                resp = await http_client.get(
                    "https://www.googleapis.com/calendar/v3/users/me/calendarList?maxResults=1",
                    headers={"Authorization": f"Bearer {token}"}
                )
                ok = resp.status_code == 200
            elif service == "notion":
                resp = await http_client.get(
                    "https://api.notion.com/v1/users/me",
                    headers={"Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28"}
                )
                ok = resp.status_code == 200
            elif service == "todoist":
                resp = await http_client.get(
                    "https://api.todoist.com/rest/v2/projects",
                    headers={"Authorization": f"Bearer {token}"}
                )
                ok = resp.status_code == 200
            elif service == "slack":
                # Slack webhook: can't test without sending a message, just check format
                ok = token.startswith("https://hooks.slack.com/")
            else:
                raise HTTPException(status_code=400, detail="Service inconnu")

        error_msg = None if ok else f"Service {service} a répondu avec une erreur (HTTP {resp.status_code})"
        await db.user_integrations.update_one(
            {"user_id": user["user_id"], "service": service},
            {"$set": {"last_tested_at": datetime.now(timezone.utc).isoformat(), "last_error": error_msg}}
        )
        return {"ok": ok, "error": error_msg}

    except httpx.TimeoutException:
        error_msg = "Timeout — le service ne répond pas"
        await db.user_integrations.update_one(
            {"user_id": user["user_id"], "service": service},
            {"$set": {"last_error": error_msg}}
        )
        return {"ok": False, "error": error_msg}
    except Exception as e:
        error_msg = f"Erreur de connexion : {str(e)[:100]}"
        await db.user_integrations.update_one(
            {"user_id": user["user_id"], "service": service},
            {"$set": {"last_error": error_msg}}
        )
        return {"ok": False, "error": error_msg}

# ============== DUO / GROUPE (D.3) ==============
# Pattern: Duolingo Friends Quest — small bounded groups (2-10), embedded members.
# Single-document design (MongoDB best practice for bounded arrays <50 elements).

GROUP_MAX_MEMBERS = 10
GROUP_CATEGORIES = {"learning", "productivity", "well_being", "creativity", "fitness", "mindfulness"}


async def _refresh_group_member_stats(group_doc: dict) -> dict:
    """Refresh live stats for all members of a group. Lightweight — only reads user docs."""
    user_ids = [m["user_id"] for m in group_doc.get("members", [])]
    if not user_ids:
        return group_doc
    users = await db.users.find(
        {"user_id": {"$in": user_ids}},
        {"_id": 0, "user_id": 1, "streak_days": 1, "total_time_invested": 1}
    ).to_list(GROUP_MAX_MEMBERS)
    user_map = {u["user_id"]: u for u in users}

    now = datetime.now(timezone.utc)
    week_start = (now.date() - timedelta(days=now.weekday())).isoformat()

    # Batch query: week minutes per member
    week_pipeline = [
        {"$match": {"user_id": {"$in": user_ids}, "completed": True, "completed_at": {"$gte": week_start}}},
        {"$group": {"_id": "$user_id", "week_minutes": {"$sum": "$actual_duration"}, "week_sessions": {"$sum": 1}}}
    ]
    week_stats = {s["_id"]: s for s in await db.user_sessions_history.aggregate(week_pipeline).to_list(GROUP_MAX_MEMBERS)}

    for member in group_doc["members"]:
        uid = member["user_id"]
        u = user_map.get(uid, {})
        ws = week_stats.get(uid, {})
        member["stats"] = {
            "streak_days": u.get("streak_days", 0),
            "total_time_invested": u.get("total_time_invested", 0),
            "week_minutes": ws.get("week_minutes", 0),
            "week_sessions": ws.get("week_sessions", 0),
        }
    return group_doc


@api_router.post("/groups")
@limiter.limit("5/minute")
async def create_group(request: Request, body: GroupCreate, user: dict = Depends(get_current_user)):
    """Create a new duo/group. The creator becomes the owner."""
    # Check user isn't in too many groups (limit: 5 active)
    existing = await db.groups.count_documents(
        {"members.user_id": user["user_id"], "status": "active"}
    )
    if existing >= 5:
        raise HTTPException(status_code=400, detail="Maximum 5 groupes actifs autorisés")

    group_id = f"grp_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()

    group_doc = {
        "group_id": group_id,
        "name": body.name.strip(),
        "objective_title": (body.objective_title or "").strip() or None,
        "category": body.category if body.category in GROUP_CATEGORIES else None,
        "owner_id": user["user_id"],
        "members": [{
            "user_id": user["user_id"],
            "name": user.get("name", ""),
            "role": "owner",
            "joined_at": now,
            "stats": {
                "streak_days": user.get("streak_days", 0),
                "total_time_invested": user.get("total_time_invested", 0),
                "week_minutes": 0,
                "week_sessions": 0,
            },
        }],
        "invites": [],
        "max_members": GROUP_MAX_MEMBERS,
        "status": "active",
        "created_at": now,
    }
    await db.groups.insert_one(group_doc)
    return {"group_id": group_id, "message": "Groupe créé"}


@api_router.get("/groups")
async def list_groups(user: dict = Depends(get_current_user)):
    """List all groups the user belongs to."""
    groups = await db.groups.find(
        {"members.user_id": user["user_id"], "status": "active"},
        {"_id": 0}
    ).sort("created_at", -1).to_list(10)

    # Refresh stats for all groups
    for g in groups:
        await _refresh_group_member_stats(g)
    return {"groups": groups}


@api_router.get("/groups/{group_id}")
async def get_group(group_id: str, user: dict = Depends(get_current_user)):
    """Get a single group with refreshed member stats."""
    group = await db.groups.find_one(
        {"group_id": group_id, "members.user_id": user["user_id"], "status": "active"},
        {"_id": 0}
    )
    if not group:
        raise HTTPException(status_code=404, detail="Groupe introuvable")
    await _refresh_group_member_stats(group)
    return group


@api_router.post("/groups/{group_id}/invite")
@limiter.limit("10/minute")
async def invite_to_group(request: Request, group_id: str, body: GroupInvite, user: dict = Depends(get_current_user)):
    """Invite someone to a group by email."""
    group = await db.groups.find_one(
        {"group_id": group_id, "members.user_id": user["user_id"], "status": "active"}
    )
    if not group:
        raise HTTPException(status_code=404, detail="Groupe introuvable")

    if len(group.get("members", [])) + len([i for i in group.get("invites", []) if i["status"] == "pending"]) >= GROUP_MAX_MEMBERS:
        raise HTTPException(status_code=400, detail=f"Maximum {GROUP_MAX_MEMBERS} membres par groupe")

    # Check if already member
    if any(m["user_id"] == body.email for m in group.get("members", [])):
        raise HTTPException(status_code=400, detail="Déjà membre du groupe")

    # Check if already invited (pending)
    if any(i["email"] == body.email and i["status"] == "pending" for i in group.get("invites", [])):
        raise HTTPException(status_code=400, detail="Invitation déjà envoyée")

    now = datetime.now(timezone.utc)
    invite = {
        "invite_id": f"ginv_{uuid.uuid4().hex[:12]}",
        "email": body.email,
        "inviter_name": user.get("name", ""),
        "status": "pending",
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(days=7)).isoformat(),
    }

    await db.groups.update_one(
        {"group_id": group_id},
        {"$push": {"invites": invite}}
    )

    # If the invitee already has an account, create a notification
    invitee = await db.users.find_one({"email": body.email}, {"user_id": 1})
    if invitee:
        await db.notifications.insert_one({
            "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
            "user_id": invitee["user_id"],
            "type": "group_invite",
            "title": "Invitation à un groupe",
            "message": f"{user.get('name', 'Quelqu\'un')} t'invite à rejoindre « {group['name']} »",
            "icon": "users",
            "data": {"group_id": group_id, "invite_id": invite["invite_id"]},
            "read": False,
            "created_at": now.isoformat(),
        })
        try:
            await send_push_to_user(
                invitee["user_id"],
                "Invitation à un groupe",
                f"{user.get('name', 'Quelqu\'un')} t'invite à rejoindre « {group['name']} »",
                url="/groups",
                tag="group-invite",
            )
        except Exception:
            pass  # Push is best-effort, never blocks

    return {"message": "Invitation envoyée", "invite_id": invite["invite_id"]}


@api_router.post("/groups/{group_id}/join")
async def join_group(group_id: str, user: dict = Depends(get_current_user)):
    """Accept an invitation and join a group."""
    group = await db.groups.find_one({"group_id": group_id, "status": "active"})
    if not group:
        raise HTTPException(status_code=404, detail="Groupe introuvable")

    # Check if already a member
    if any(m["user_id"] == user["user_id"] for m in group.get("members", [])):
        raise HTTPException(status_code=400, detail="Déjà membre de ce groupe")

    # Check pending invite for this user
    email = user.get("email", "")
    invite_found = False
    for inv in group.get("invites", []):
        if inv["email"] == email and inv["status"] == "pending":
            invite_found = True
            break

    if not invite_found:
        raise HTTPException(status_code=403, detail="Aucune invitation en attente pour ce compte")

    if len(group.get("members", [])) >= GROUP_MAX_MEMBERS:
        raise HTTPException(status_code=400, detail="Groupe complet")

    now = datetime.now(timezone.utc).isoformat()

    # Add member + mark invite as accepted (atomic)
    await db.groups.update_one(
        {"group_id": group_id, "invites.email": email, "invites.status": "pending"},
        {
            "$push": {"members": {
                "user_id": user["user_id"],
                "name": user.get("name", ""),
                "role": "member",
                "joined_at": now,
                "stats": {
                    "streak_days": user.get("streak_days", 0),
                    "total_time_invested": user.get("total_time_invested", 0),
                    "week_minutes": 0, "week_sessions": 0,
                },
            }},
            "$set": {"invites.$[inv].status": "accepted"},
        },
        array_filters=[{"inv.email": email, "inv.status": "pending"}],
    )

    # Notify group owner
    await db.notifications.insert_one({
        "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
        "user_id": group["owner_id"],
        "type": "group_member_joined",
        "title": "Nouveau membre",
        "message": f"{user.get('name', 'Quelqu\'un')} a rejoint « {group['name']} »",
        "icon": "user-plus",
        "read": False,
        "created_at": now,
    })

    return {"message": f"Bienvenue dans « {group['name']} » !"}


@api_router.post("/groups/{group_id}/leave")
async def leave_group(group_id: str, user: dict = Depends(get_current_user)):
    """Leave a group. Owner cannot leave — must archive instead."""
    group = await db.groups.find_one(
        {"group_id": group_id, "members.user_id": user["user_id"], "status": "active"}
    )
    if not group:
        raise HTTPException(status_code=404, detail="Groupe introuvable")

    if group["owner_id"] == user["user_id"]:
        raise HTTPException(status_code=400, detail="Le créateur ne peut pas quitter le groupe. Utilisez l'archivage.")

    await db.groups.update_one(
        {"group_id": group_id},
        {"$pull": {"members": {"user_id": user["user_id"]}}}
    )
    return {"message": "Vous avez quitté le groupe"}


@api_router.delete("/groups/{group_id}")
async def archive_group(group_id: str, user: dict = Depends(get_current_user)):
    """Archive a group (owner only). Soft delete — never hard delete."""
    group = await db.groups.find_one({"group_id": group_id, "status": "active"})
    if not group:
        raise HTTPException(status_code=404, detail="Groupe introuvable")
    if group["owner_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Seul le créateur peut archiver le groupe")

    await db.groups.update_one(
        {"group_id": group_id},
        {"$set": {"status": "archived", "archived_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "Groupe archivé"}


@api_router.get("/groups/{group_id}/feed")
async def get_group_feed(group_id: str, user: dict = Depends(get_current_user)):
    """Get recent activity feed for a group — last 7 days of sessions from all members.
    Pattern: Strava Club activity feed — chronological, lightweight."""
    group = await db.groups.find_one(
        {"group_id": group_id, "members.user_id": user["user_id"], "status": "active"}
    )
    if not group:
        raise HTTPException(status_code=404, detail="Groupe introuvable")

    member_ids = [m["user_id"] for m in group.get("members", [])]
    member_names = {m["user_id"]: m["name"] for m in group["members"]}
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

    sessions = await db.user_sessions_history.find(
        {"user_id": {"$in": member_ids}, "completed": True, "completed_at": {"$gte": week_ago}},
        {"_id": 0, "user_id": 1, "action_title": 1, "category": 1, "actual_duration": 1, "completed_at": 1}
    ).sort("completed_at", -1).limit(50).to_list(50)

    # Enrich with member name (never expose user_id to frontend)
    feed = []
    for s in sessions:
        feed.append({
            "member_name": member_names.get(s["user_id"], "Membre"),
            "action_title": s.get("action_title", "Session"),
            "category": s.get("category", ""),
            "duration": s.get("actual_duration", 0),
            "completed_at": s.get("completed_at", ""),
        })

    return {"feed": feed, "group_name": group["name"]}


# ============== SHARE PROGRESSION (D.2) ==============

SHARE_TYPES = {"weekly_recap", "milestone", "badge", "objective"}
SHARE_TTL_DAYS = 90  # Auto-cleanup after 90 days

@api_router.post("/share/create")
@limiter.limit("10/minute")
async def create_share(request: Request, body: ShareCreate, user: dict = Depends(get_current_user)):
    """Create an immutable snapshot of user progression for sharing.
    Returns a share_id that can be used to view the public share page.
    Pattern: Spotify Wrapped / Strava Activity Cards — snapshot at creation time."""
    user_id = user["user_id"]

    if body.share_type not in SHARE_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid share_type. Must be one of: {', '.join(SHARE_TYPES)}")

    now = datetime.now(timezone.utc)
    today = now.date()
    today_iso = today.isoformat()
    week_start = (today - timedelta(days=today.weekday())).isoformat()

    # ── Snapshot: core stats ─────────────────────
    total_sessions = await db.user_sessions_history.count_documents(
        {"user_id": user_id, "completed": True}
    )

    week_sessions = await db.user_sessions_history.find(
        {"user_id": user_id, "completed": True, "completed_at": {"$gte": week_start}},
        {"_id": 0, "actual_duration": 1, "category": 1, "completed_at": 1}
    ).to_list(200)

    week_minutes = sum(s.get("actual_duration", 0) for s in week_sessions)
    week_count = len(week_sessions)

    week_by_day = {}
    for s in week_sessions:
        day = s.get("completed_at", "")[:10]
        if day:
            week_by_day[day] = week_by_day.get(day, 0) + s.get("actual_duration", 0)

    # ── Snapshot: objectives ─────────────────────
    obj_filter = {"user_id": user_id, "status": "active", "deleted": {"$ne": True}}
    if body.objective_id:
        obj_filter["objective_id"] = body.objective_id

    objectives = await db.objectives.find(
        obj_filter,
        {"_id": 0, "objective_id": 1, "title": 1, "current_day": 1, "streak_days": 1,
         "total_sessions": 1, "total_minutes": 1, "curriculum": 1, "category": 1}
    ).to_list(20)

    obj_snapshots = []
    for obj in objectives:
        curriculum = obj.get("curriculum", [])
        total_completed = sum(1 for s in curriculum if s.get("completed"))
        total_steps = len(curriculum)
        obj_snapshots.append({
            "objective_id": obj["objective_id"],
            "title": obj["title"],
            "category": obj.get("category", ""),
            "streak_days": obj.get("streak_days", 0),
            "progress_percent": round((total_completed / max(total_steps, 1)) * 100),
            "total_completed": total_completed,
            "total_steps": total_steps,
            "total_minutes": obj.get("total_minutes", 0),
        })

    # ── Snapshot: badges ─────────────────────────
    user_badges = user.get("badges", [])

    # ── Build share document ─────────────────────
    share_id = secrets.token_urlsafe(12)  # 16 chars, 96 bits entropy (Bitly-grade)

    share_doc = {
        "share_id": share_id,
        "user_id": user_id,
        "share_type": body.share_type,
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(days=SHARE_TTL_DAYS)).isoformat(),
        "author": {
            "name": user.get("name", "Utilisateur InFinea"),
            "subscription_tier": user.get("subscription_tier", "free"),
        },
        "snapshot": {
            "streak_days": user.get("streak_days", 0),
            "total_time_invested": user.get("total_time_invested", 0),
            "total_sessions": total_sessions,
            "week": {
                "sessions": week_count,
                "minutes": week_minutes,
                "by_day": week_by_day,
            },
            "objectives": obj_snapshots,
            "badges_count": len(user_badges),
            "recent_badges": user_badges[-3:] if user_badges else [],
        },
    }

    await db.shares.insert_one(share_doc)

    return {
        "share_id": share_id,
        "share_url": f"/p/{share_id}",
        "expires_at": share_doc["expires_at"],
    }


@app.get("/share/{share_id}")
@limiter.limit("30/minute")
async def get_public_share(share_id: str, request: Request):
    """Public endpoint — no auth required. Returns the share snapshot for display.
    Route is on app (not api_router) for clean public URLs."""
    share = await db.shares.find_one(
        {"share_id": share_id},
        {"_id": 0, "user_id": 0}  # Never expose internal user_id publicly
    )
    if not share:
        raise HTTPException(status_code=404, detail="Share not found or expired")

    # Check expiration
    expires_at = share.get("expires_at", "")
    if expires_at and expires_at < datetime.now(timezone.utc).isoformat():
        raise HTTPException(status_code=410, detail="This share has expired")

    return share


# ============== ROOT ROUTE ==============

@api_router.get("/")
async def root():
    return {"message": "InFinea API - Investissez vos instants perdus"}

# Include router and add middleware
app.include_router(api_router)

ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

@app.on_event("startup")
async def startup_event():
    """Auto-seed the database if empty or missing premium categories, then start daily generator"""
    count = await db.micro_actions.count_documents({})
    existing_cats = await db.micro_actions.distinct("category")
    premium_cats = {"creativity", "fitness", "mindfulness", "leadership", "finance", "relations", "mental_health", "entrepreneurship"}
    missing_cats = premium_cats - set(existing_cats)
    if count == 0 or missing_cats:
        logger.info(f"Seeding needed (total={count}, missing categories={missing_cats})")
        await seed_micro_actions()
        logger.info("Database seeded successfully!")

    # Create indexes for event_log collection (idempotent — safe to run every startup)
    await db.event_log.create_index("user_id")
    await db.event_log.create_index([("event_type", 1), ("timestamp", -1)])
    await db.event_log.create_index("timestamp", expireAfterSeconds=90 * 24 * 3600)  # TTL: 90 days auto-cleanup
    logger.info("event_log indexes ensured")

    # Create indexes for user_features collection (idempotent)
    await db.user_features.create_index("user_id", unique=True)
    await db.user_features.create_index("computed_at")
    logger.info("user_features indexes ensured")

    # Create indexes for action_signals collection (feedback loop)
    await db.action_signals.create_index(
        [("user_id", 1), ("action_id", 1)], unique=True
    )
    await db.action_signals.create_index("updated_at")
    logger.info("action_signals indexes ensured")

    # Create indexes for coach_messages collection (persistent chat)
    await db.coach_messages.create_index([("user_id", 1), ("created_at", 1)])
    await db.coach_messages.create_index("created_at", expireAfterSeconds=30 * 24 * 3600)  # TTL: 30 days
    logger.info("coach_messages indexes ensured")

    # Create indexes for objectives collection (parcours personnalisés)
    await db.objectives.create_index([("user_id", 1), ("status", 1)])
    await db.objectives.create_index("objective_id", unique=True)
    logger.info("objectives indexes ensured")

    # Create indexes for routines collection
    await db.routines.create_index([("user_id", 1), ("is_active", 1)])
    await db.routines.create_index("routine_id", unique=True)
    logger.info("routines indexes ensured")

    # Create indexes for shares collection (D.2 share progression)
    await db.shares.create_index("share_id", unique=True)
    await db.shares.create_index([("user_id", 1), ("created_at", -1)])
    await db.shares.create_index("expires_at", expireAfterSeconds=0)  # MongoDB TTL: auto-delete expired docs
    logger.info("shares indexes ensured")

    # Create indexes for groups collection (D.3 duo/groupe)
    await db.groups.create_index("group_id", unique=True)
    await db.groups.create_index([("members.user_id", 1), ("status", 1)])
    logger.info("groups indexes ensured")

    # Start daily action generation background loop
    from services.action_generator import daily_generation_loop
    asyncio.create_task(daily_generation_loop(db))

    # Start feature computation background loop
    from services.feature_calculator import feature_computation_loop
    asyncio.create_task(feature_computation_loop(db))

    # Start proactive notification scheduler (streak alerts, routine reminders, objective nudges)
    from services.notification_scheduler import notification_scheduler_loop
    asyncio.create_task(notification_scheduler_loop(db))

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
