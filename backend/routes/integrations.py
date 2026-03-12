"""InFinea — Integration routes. Google Calendar, iCal, OAuth hub, slots, admin."""

import os
import json
import uuid
import asyncio
import urllib.parse
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any

import httpx
from fastapi import APIRouter, HTTPException, Request, Response, Depends
from fastapi.responses import RedirectResponse

from database import db
from auth import get_current_user
from models import ICalConnectRequest, TokenConnectRequest, SlotSettings
from config import logger, limiter
from helpers import send_push_to_user

try:
    from integrations.google_calendar import (
        generate_auth_url, exchange_code_for_tokens, encrypt_tokens,
        refresh_access_token, get_calendar_events, get_user_calendars,
        GOOGLE_CLIENT_ID,
    )
except ImportError:
    generate_auth_url = exchange_code_for_tokens = encrypt_tokens = None
    refresh_access_token = get_calendar_events = get_user_calendars = None
    GOOGLE_CLIENT_ID = None

try:
    from integrations.encryption import encrypt_token, decrypt_token
except ImportError:
    encrypt_token = decrypt_token = None

try:
    from services.slot_detector import detect_free_slots, match_action_to_slot, DEFAULT_SETTINGS
except ImportError:
    detect_free_slots = match_action_to_slot = None
    DEFAULT_SETTINGS = {}

try:
    from services.smart_notifications import (
        schedule_slot_notifications, cleanup_old_slots, get_pending_notifications,
    )
except ImportError:
    schedule_slot_notifications = cleanup_old_slots = get_pending_notifications = None

from seed_actions import SEED_ACTIONS

try:
    from seed_premium_actions import PREMIUM_ACTIONS
except ImportError:
    PREMIUM_ACTIONS = []

try:
    from icalendar import Calendar as ICalCalendar
    ICAL_AVAILABLE = True
except ImportError:
    ICAL_AVAILABLE = False

router = APIRouter()

# ============== ACTION GENERATION (admin) ==============

@router.post("/admin/generate-actions")
async def trigger_action_generation(user: dict = Depends(get_current_user)):
    """Admin-only: trigger daily action generation manually."""
    admin_emails = [e.strip().lower() for e in os.environ.get("ADMIN_EMAILS", "").split(",") if e.strip()]
    if user.get("email", "").lower() not in admin_emails:
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")

    from services.action_generator import check_and_generate_daily_actions
    result = await check_and_generate_daily_actions(db)
    return result

@router.get("/admin/actions-stats")
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

@router.get("/admin/events")
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

@router.get("/admin/features")
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

@router.post("/admin/compute-features")
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

# (imports handled at module level with try/except)

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

@router.get("/integrations")
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

@router.get("/integrations/connect/{service}")
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

@router.get("/integrations/callback/{service}")
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

@router.delete("/integrations/{service}")
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

@router.put("/integrations/{service}/sync")
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

@router.post("/integrations/{service}/sync")
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

@router.post("/integrations/ical/connect")
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

@router.post("/integrations/{service}/connect-url")
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

@router.post("/integrations/ical/sync")
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

@router.post("/integrations/{service}/connect-token")
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
        raise HTTPException(status_code=400, detail="Impossible de valider le token. Vérifiez et réessayez.")

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
