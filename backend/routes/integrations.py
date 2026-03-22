"""
InFinea — Calendar integration & free slots routes.
Google Calendar OAuth, sync, and slot detection.
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from datetime import datetime, timezone, timedelta
import uuid
import logging

from database import db
from auth import get_current_user
from models import SlotSettings

from integrations.google_calendar import (
    generate_auth_url,
    exchange_code_for_tokens,
    encrypt_tokens,
    refresh_access_token,
    get_calendar_events,
    get_user_calendars,
    GOOGLE_CLIENT_ID,
)
from integrations.encryption import encrypt_token, decrypt_token
from services.slot_detector import detect_free_slots, match_action_to_slot, DEFAULT_SETTINGS
from services.smart_notifications import (
    schedule_slot_notifications,
    cleanup_old_slots,
    get_pending_notifications,
)

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)


@router.get("/integrations")
async def get_integrations(user: dict = Depends(get_current_user)):
    """Get user's connected integrations."""
    integrations = await db.user_integrations.find(
        {"user_id": user["user_id"]},
        {"_id": 0, "access_token": 0, "refresh_token": 0},
    ).to_list(10)

    google_available = bool(GOOGLE_CLIENT_ID)

    return {
        "integrations": integrations,
        "available": [
            {
                "provider": "google_calendar",
                "name": "Google Calendar",
                "description": "Détecte automatiquement vos créneaux libres",
                "icon": "calendar",
                "available": google_available,
                "connected": any(
                    i["provider"] == "google_calendar" for i in integrations
                ),
            }
        ],
    }


@router.post("/integrations/google/connect")
async def connect_google_calendar(
    request: Request, user: dict = Depends(get_current_user)
):
    """Initiate Google Calendar OAuth flow."""
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=503, detail="Google Calendar integration not configured"
        )

    state = f"{user['user_id']}:{uuid.uuid4().hex[:16]}"

    await db.oauth_states.insert_one(
        {
            "state": state,
            "user_id": user["user_id"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (
                datetime.now(timezone.utc) + timedelta(minutes=10)
            ).isoformat(),
        }
    )

    body = (
        await request.json()
        if request.headers.get("content-type") == "application/json"
        else {}
    )
    origin_url = body.get("origin_url", str(request.base_url).rstrip("/"))
    redirect_uri = f"{origin_url}/api/integrations/google/callback"

    auth_url = generate_auth_url(redirect_uri, state)

    return {"authorization_url": auth_url, "state": state}


@router.get("/integrations/google/callback")
async def google_calendar_callback(
    request: Request,
    code: str = None,
    state: str = None,
    error: str = None,
):
    """Handle Google OAuth callback."""
    from fastapi.responses import RedirectResponse

    origin = (
        str(request.base_url)
        .rstrip("/")
        .replace("/api/integrations/google/callback", "")
    )

    if error:
        logger.error(f"Google OAuth error: {error}")
        return RedirectResponse(f"{origin}/integrations?error=oauth_error")

    if not code or not state:
        return RedirectResponse(f"{origin}/integrations?error=missing_params")

    state_doc = await db.oauth_states.find_one_and_delete({"state": state})
    if not state_doc:
        return RedirectResponse(f"{origin}/integrations?error=invalid_state")

    user_id = state_doc["user_id"]

    try:
        redirect_uri = f"{origin}/api/integrations/google/callback"
        tokens = await exchange_code_for_tokens(code, redirect_uri)

        encrypted_tokens = encrypt_tokens(tokens)

        integration_id = f"int_{uuid.uuid4().hex[:12]}"
        integration_doc = {
            "integration_id": integration_id,
            "user_id": user_id,
            "provider": "google_calendar",
            "access_token": encrypted_tokens["access_token"],
            "refresh_token": encrypted_tokens.get("refresh_token", ""),
            "token_expires_at": (
                datetime.now(timezone.utc)
                + timedelta(seconds=tokens.get("expires_in", 3600))
            ).isoformat(),
            "scopes": tokens.get("scope", "").split(" "),
            "enabled": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_sync_at": None,
            "metadata": {},
        }

        await db.user_integrations.delete_many(
            {"user_id": user_id, "provider": "google_calendar"}
        )

        await db.user_integrations.insert_one(integration_doc)

        try:
            calendars = await get_user_calendars(encrypted_tokens["access_token"])
            primary_calendar = next(
                (c for c in calendars if c.get("primary")), None
            )

            await db.user_integrations.update_one(
                {"integration_id": integration_id},
                {
                    "$set": {
                        "metadata.calendars": [
                            {"id": c["id"], "summary": c.get("summary", "")}
                            for c in calendars
                        ],
                        "metadata.primary_calendar": primary_calendar["id"]
                        if primary_calendar
                        else "primary",
                    }
                },
            )
        except Exception as e:
            logger.warning(f"Failed to fetch calendars: {e}")

        return RedirectResponse(f"{origin}/integrations?success=true")

    except Exception as e:
        logger.error(f"Google Calendar connection failed: {e}")
        return RedirectResponse(f"{origin}/integrations?error=connection_failed")


@router.delete("/integrations/{integration_id}")
async def disconnect_integration(
    integration_id: str,
    user: dict = Depends(get_current_user),
):
    """Disconnect an integration."""
    result = await db.user_integrations.delete_one(
        {"integration_id": integration_id, "user_id": user["user_id"]}
    )

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Integration not found")

    await db.detected_free_slots.delete_many({"user_id": user["user_id"]})

    return {"message": "Integration disconnected"}


@router.post("/integrations/{integration_id}/sync")
async def sync_integration(
    integration_id: str,
    user: dict = Depends(get_current_user),
):
    """Force synchronization of an integration."""
    integration = await db.user_integrations.find_one(
        {"integration_id": integration_id, "user_id": user["user_id"]}, {"_id": 0}
    )

    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    if integration["provider"] != "google_calendar":
        raise HTTPException(
            status_code=400, detail="Sync not supported for this integration"
        )

    try:
        token_expires = datetime.fromisoformat(
            integration["token_expires_at"].replace("Z", "+00:00")
        )

        if token_expires < datetime.now(timezone.utc):
            if not integration.get("refresh_token"):
                raise HTTPException(
                    status_code=401, detail="Token expired, please reconnect"
                )

            new_tokens = await refresh_access_token(integration["refresh_token"])
            encrypted = encrypt_tokens(new_tokens)

            await db.user_integrations.update_one(
                {"integration_id": integration_id},
                {
                    "$set": {
                        "access_token": encrypted["access_token"],
                        "token_expires_at": (
                            datetime.now(timezone.utc)
                            + timedelta(
                                seconds=new_tokens.get("expires_in", 3600)
                            )
                        ).isoformat(),
                    }
                },
            )
            integration["access_token"] = encrypted["access_token"]

        now = datetime.now(timezone.utc)
        tomorrow = now + timedelta(hours=24)

        events = await get_calendar_events(
            integration["access_token"],
            now,
            tomorrow,
            integration.get("metadata", {}).get("primary_calendar", "primary"),
        )

        prefs = (
            await db.notification_preferences.find_one(
                {"user_id": user["user_id"]}, {"_id": 0}
            )
            or {}
        )

        settings = {**DEFAULT_SETTINGS, **prefs}

        slots = await detect_free_slots(events, settings)

        await cleanup_old_slots(db, user["user_id"])

        actions = await db.micro_actions.find({}, {"_id": 0}).to_list(50)

        await schedule_slot_notifications(
            db,
            user["user_id"],
            slots,
            actions,
            user.get("subscription_tier", "free"),
        )

        await db.user_integrations.update_one(
            {"integration_id": integration_id},
            {"$set": {"last_sync_at": now.isoformat()}},
        )

        return {
            "message": "Sync completed",
            "events_found": len(events),
            "slots_detected": len(slots),
            "last_sync": now.isoformat(),
        }

    except Exception as e:
        logger.error(f"Sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


# ============== FREE SLOTS ENDPOINTS ==============


@router.get("/slots/today")
async def get_today_slots(user: dict = Depends(get_current_user)):
    """Get free slots for today."""
    now = datetime.now(timezone.utc)
    end_of_day = now.replace(hour=23, minute=59, second=59)

    slots = (
        await db.detected_free_slots.find(
            {
                "user_id": user["user_id"],
                "start_time": {
                    "$gte": now.isoformat(),
                    "$lte": end_of_day.isoformat(),
                },
            },
            {"_id": 0},
        )
        .sort("start_time", 1)
        .to_list(20)
    )

    for slot in slots:
        if slot.get("suggested_action_id"):
            action = await db.micro_actions.find_one(
                {"action_id": slot["suggested_action_id"]}, {"_id": 0}
            )
            slot["suggested_action"] = action

    return {"slots": slots, "count": len(slots)}


@router.get("/slots/week")
async def get_week_slots(user: dict = Depends(get_current_user)):
    """Get free slots for the week."""
    now = datetime.now(timezone.utc)
    week_end = now + timedelta(days=7)

    slots = (
        await db.detected_free_slots.find(
            {
                "user_id": user["user_id"],
                "start_time": {
                    "$gte": now.isoformat(),
                    "$lte": week_end.isoformat(),
                },
            },
            {"_id": 0},
        )
        .sort("start_time", 1)
        .to_list(50)
    )

    return {"slots": slots, "count": len(slots)}


@router.get("/slots/next")
async def get_next_slot(user: dict = Depends(get_current_user)):
    """Get the next upcoming free slot."""
    now = datetime.now(timezone.utc)

    slot = await db.detected_free_slots.find_one(
        {
            "user_id": user["user_id"],
            "start_time": {"$gte": now.isoformat()},
            "action_taken": False,
        },
        {"_id": 0},
        sort=[("start_time", 1)],
    )

    if slot and slot.get("suggested_action_id"):
        action = await db.micro_actions.find_one(
            {"action_id": slot["suggested_action_id"]}, {"_id": 0}
        )
        slot["suggested_action"] = action

    return {"slot": slot}


@router.post("/slots/{slot_id}/dismiss")
async def dismiss_slot(slot_id: str, user: dict = Depends(get_current_user)):
    """Dismiss/ignore a slot."""
    result = await db.detected_free_slots.update_one(
        {"slot_id": slot_id, "user_id": user["user_id"]},
        {
            "$set": {
                "dismissed": True,
                "dismissed_at": datetime.now(timezone.utc).isoformat(),
            }
        },
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Slot not found")

    return {"message": "Slot dismissed"}


@router.get("/slots/settings")
async def get_slot_settings(user: dict = Depends(get_current_user)):
    """Get user's slot detection settings."""
    prefs = await db.notification_preferences.find_one(
        {"user_id": user["user_id"]}, {"_id": 0}
    )

    settings = {**DEFAULT_SETTINGS}
    if prefs:
        for key in DEFAULT_SETTINGS:
            if key in prefs:
                settings[key] = prefs[key]

    return settings


@router.put("/slots/settings")
async def update_slot_settings(
    settings: SlotSettings,
    user: dict = Depends(get_current_user),
):
    """Update user's slot detection settings."""
    settings_dict = settings.model_dump()

    await db.notification_preferences.update_one(
        {"user_id": user["user_id"]}, {"$set": settings_dict}, upsert=True
    )

    return {"message": "Settings updated", "settings": settings_dict}
