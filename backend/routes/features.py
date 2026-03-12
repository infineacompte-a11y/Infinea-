"""InFinea — Feature flags and integration status routes."""

import os
import uuid
import urllib.parse
from datetime import datetime, timezone, timedelta

import httpx
from fastapi import APIRouter, HTTPException, Request, Depends

from database import db
from auth import get_current_user
from config import logger, limiter
from routes.integrations import INTEGRATION_CONFIGS, TOKEN_CONNECT_VALIDATORS

try:
    from integrations.encryption import decrypt_token
except ImportError:
    decrypt_token = None

try:
    from icalendar import Calendar as ICalCalendar
    ICAL_AVAILABLE = True
except ImportError:
    ICAL_AVAILABLE = False

router = APIRouter()

FEATURE_UNIFIED_INTEGRATIONS = os.environ.get("FEATURE_UNIFIED_INTEGRATIONS", "true") == "true"


@router.get("/feature-flags")
async def get_feature_flags():
    """Public feature flags for frontend conditional rendering."""
    return {
        "unified_integrations": FEATURE_UNIFIED_INTEGRATIONS,
    }

# ============== UNIFIED INTEGRATION STATUS ==============

@router.get("/integrations/status")
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
            "description": "Détecte automatiquement vos créneaux libres entre les réunions",
        },
        "ical": {
            "name": "Apple Calendar",
            "category": "calendrier",
            "description": "Importez votre calendrier Apple pour détecter vos créneaux libres",
        },
        "notion": {
            "name": "Notion",
            "category": "notes",
            "description": "Exportez vos sessions comme pages Notion automatiquement",
        },
        "todoist": {
            "name": "Todoist",
            "category": "tâches",
            "description": "Loguez vos sessions comme tâches complétées dans Todoist",
        },
        "slack": {
            "name": "Slack",
            "category": "communication",
            "description": "Recevez vos résumés hebdomadaires directement dans Slack",
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

@router.post("/integrations/{service}/test")
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
