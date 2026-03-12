"""
InFinea — Shared helper functions.
AI calls, usage limits, push notifications, context builders.
"""

import os
import json
import logging
from typing import Optional
from datetime import datetime, timezone

import httpx
from pywebpush import webpush, WebPushException

from config import VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY, VAPID_CLAIMS_EMAIL, logger
from database import db


# ── AI ──

AI_SYSTEM_MESSAGE = """Tu es le coach IA InFinea, expert en productivité, apprentissage et bien-être.
Tu aides les utilisateurs à transformer leurs moments perdus en micro-victoires.
Réponds toujours en français, de manière concise, chaleureuse et motivante.
Tes réponses doivent toujours être au format JSON quand demandé."""


def get_ai_model(user: dict = None) -> str:
    """Return AI model based on user subscription tier."""
    if user and user.get("subscription_tier") == "premium":
        return "claude-sonnet-4-20250514"
    return "claude-haiku-4-5-20251001"


async def call_ai(session_suffix: str, system_message: str, prompt: str, model: str = None) -> Optional[str]:
    """Shared AI call wrapper using Anthropic Claude API via httpx."""
    api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    ai_model = model or "claude-haiku-4-5-20251001"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client_http:
            resp = await client_http.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": ai_model,
                    "max_tokens": 1000,
                    "system": system_message,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ]
                }
            )
            resp.raise_for_status()
            data = resp.json()
            return data["content"][0]["text"]
    except Exception as e:
        logger.error(f"AI call error ({session_suffix}): {e}")
        return None


def parse_ai_json(response: Optional[str]) -> Optional[dict]:
    """Extract JSON from AI response."""
    if not response:
        return None
    try:
        json_start = response.find("{")
        json_end = response.rfind("}") + 1
        if json_start != -1 and json_end > json_start:
            return json.loads(response[json_start:json_end])
    except Exception:
        pass
    return None


# ── User Context ──

async def build_user_context(user: dict) -> str:
    """Build a context string from user profile for AI prompts."""
    profile = user.get("user_profile")
    if not profile:
        return f"Utilisateur: {user.get('name', 'Inconnu')}, streak: {user.get('streak_days', 0)} jours, temps total: {user.get('total_time_invested', 0)} min"

    goals_map = {"learning": "apprentissage", "productivity": "productivité", "well_being": "bien-être"}
    goals = ", ".join([goals_map.get(g, g) for g in profile.get("goals", [])])

    # Handle both new format (preferred_times, energy_level, interests as list)
    # and legacy format (availability_slots, energy_high/low, interests as dict)
    interests = profile.get("interests", [])
    if isinstance(interests, dict):
        interests_str = json.dumps(interests, ensure_ascii=False)
    elif isinstance(interests, list):
        interests_str = ", ".join(interests) if interests else "non définis"
    else:
        interests_str = str(interests)

    times = profile.get("preferred_times", profile.get("availability_slots", []))
    energy = profile.get("energy_level", profile.get("energy_high", "medium"))

    return f"""Profil utilisateur:
- Nom: {user.get('name', 'Inconnu')}
- Objectifs: {goals}
- Créneaux préférés: {', '.join(times) if times else 'non définis'}
- Niveau d'énergie: {energy}
- Intérêts: {interests_str}
- Streak actuel: {user.get('streak_days', 0)} jours
- Temps total investi: {user.get('total_time_invested', 0)} minutes
- Abonnement: {user.get('subscription_tier', 'free')}"""


# ── Usage Limits ──

async def check_usage_limit(user_id: str, feature: str, limit: int, period: str = "daily") -> dict:
    """Check and increment usage counter for free-tier AI limits.
    Returns {"allowed": bool, "used": int, "limit": int, "remaining": int}
    """
    today = datetime.now(timezone.utc).date().isoformat()
    week = datetime.now(timezone.utc).strftime("%Y-W%W")

    if period == "daily":
        doc = await db.usage_limits.find_one({"user_id": user_id, "date": today})
        used = (doc or {}).get(feature, 0)
        if used >= limit:
            return {"allowed": False, "used": used, "limit": limit, "remaining": 0}
        await db.usage_limits.update_one(
            {"user_id": user_id, "date": today},
            {"$inc": {feature: 1}, "$setOnInsert": {"created_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True
        )
        return {"allowed": True, "used": used + 1, "limit": limit, "remaining": limit - used - 1}

    elif period == "weekly":
        doc = await db.usage_limits.find_one({"user_id": user_id, "date": today})
        last_week = (doc or {}).get(f"{feature}_week", "")
        if last_week == week:
            return {"allowed": False, "used": 1, "limit": limit, "remaining": 0}
        await db.usage_limits.update_one(
            {"user_id": user_id, "date": today},
            {"$set": {f"{feature}_week": week}, "$setOnInsert": {"created_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True
        )
        return {"allowed": True, "used": 1, "limit": limit, "remaining": 0}

    elif period == "total":
        count = await db.usage_limits.find_one({"user_id": user_id, "type": "lifetime"})
        used = (count or {}).get(feature, 0)
        if used >= limit:
            return {"allowed": False, "used": used, "limit": limit, "remaining": 0}
        await db.usage_limits.update_one(
            {"user_id": user_id, "type": "lifetime"},
            {"$inc": {feature: 1}, "$setOnInsert": {"created_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True
        )
        return {"allowed": True, "used": used + 1, "limit": limit, "remaining": limit - used - 1}

    return {"allowed": True, "used": 0, "limit": limit, "remaining": limit}


# ── Push Notifications ──

async def send_push_to_user(user_id: str, title: str, body: str, url: str = "/notifications", tag: str = "infinea"):
    """Send a Web Push notification to a user if they have an active subscription.
    Silently fails if no subscription or VAPID not configured — never blocks the caller."""
    if not VAPID_PRIVATE_KEY or not VAPID_PUBLIC_KEY:
        return
    sub_doc = await db.push_subscriptions.find_one({"user_id": user_id})
    if not sub_doc or not sub_doc.get("subscription"):
        return
    try:
        webpush(
            subscription_info=sub_doc["subscription"],
            data=json.dumps({"title": title, "body": body, "url": url, "tag": tag}),
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims={"sub": VAPID_CLAIMS_EMAIL},
        )
    except WebPushException as e:
        # 410 Gone = subscription expired, clean up
        if "410" in str(e):
            await db.push_subscriptions.delete_one({"user_id": user_id})
        else:
            logging.warning(f"Web Push failed for {user_id}: {e}")
    except Exception as e:
        logging.warning(f"Web Push unexpected error for {user_id}: {e}")
