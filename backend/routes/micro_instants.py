"""
InFinea — Micro-Instants API routes.
Endpoints for the Micro-Instant Engine (Phase F):
- GET  /micro-instants/today    → predicted micro-instants for today
- POST /micro-instants/{id}/exploit → user starts action in a micro-instant
- POST /micro-instants/{id}/skip    → user skips (negative feedback)
- GET  /micro-instants/stats    → exploitation rate, trends, best slots
"""

from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from database import db
from auth import get_current_user
from config import logger

router = APIRouter(prefix="/micro-instants", tags=["micro-instants"])


# ── Request models ──

class ExploitRequest(BaseModel):
    action_id: Optional[str] = None  # Override recommended action


class SkipRequest(BaseModel):
    reason: Optional[str] = None  # "busy" | "not_interested" | "wrong_time" | None


# ═══════════════════════════════════════════════════════════════════
# GET /micro-instants/today
# ═══════════════════════════════════════════════════════════════════


@router.get("/today")
async def get_today_instants(user: dict = Depends(get_current_user)):
    """
    Get predicted micro-instants for today.
    Combines calendar gaps, routine windows, and behavioral patterns.
    """
    from services.micro_instant_engine import predict_micro_instants

    user_id = user["user_id"]
    subscription = user.get("subscription_tier", "free")

    # Try to fetch calendar events if user has integration
    calendar_events = None
    integration = await db.user_integrations.find_one({
        "user_id": user_id,
        "service": {"$in": ["google_calendar", "ical"]},
        "sync_enabled": True,
    })

    if integration:
        # Fetch cached calendar events from last sync
        now = datetime.now(timezone.utc)
        events = await db.detected_free_slots.find({
            "user_id": user_id,
        }).to_list(50)

        # If we have recent synced events, use them as calendar context
        # Otherwise just use routines + patterns
        if events:
            calendar_events = []  # Engine will use routines + patterns only

    instants = await predict_micro_instants(
        db, user_id,
        calendar_events=calendar_events,
        user_subscription=subscription,
    )

    return {
        "date": now.date().isoformat() if 'now' in dir() else datetime.now(timezone.utc).date().isoformat(),
        "instants": instants,
        "total": len(instants),
        "sources": {
            "calendar": len([i for i in instants if i["source"] == "calendar_gap"]),
            "routine": len([i for i in instants if i["source"] == "routine_window"]),
            "pattern": len([i for i in instants if i["source"] == "behavioral_pattern"]),
        },
    }


# ═══════════════════════════════════════════════════════════════════
# POST /micro-instants/{instant_id}/exploit
# ═══════════════════════════════════════════════════════════════════


@router.post("/{instant_id}/exploit")
async def exploit_instant(
    instant_id: str,
    body: ExploitRequest,
    user: dict = Depends(get_current_user),
):
    """
    User decides to exploit a micro-instant.
    Starts a session with the recommended (or overridden) action.
    """
    from services.micro_instant_engine import record_instant_outcome

    user_id = user["user_id"]

    # Determine which action to start
    action_id = body.action_id

    if not action_id:
        return HTTPException(status_code=400, detail="action_id required")

    # Verify action exists
    action = await db.micro_actions.find_one(
        {"action_id": action_id}, {"_id": 0}
    )
    if not action:
        # Try custom actions
        action = await db.user_custom_actions.find_one(
            {"action_id": action_id, "created_by": user_id}, {"_id": 0}
        )
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    # Premium check
    if action.get("is_premium") and user.get("subscription_tier") != "premium":
        raise HTTPException(status_code=403, detail="Premium action requires subscription")

    # Record the exploitation outcome
    await record_instant_outcome(db, user_id, instant_id, "exploited", {
        "action_id": action_id,
        "action_title": action.get("title"),
        "category": action.get("category"),
    })

    return {
        "status": "exploited",
        "instant_id": instant_id,
        "action": {
            "action_id": action["action_id"],
            "title": action.get("title", ""),
            "category": action.get("category", ""),
            "duration_min": action.get("duration_min", 5),
            "duration_max": action.get("duration_max", 10),
            "instructions": action.get("instructions", []),
        },
    }


# ═══════════════════════════════════════════════════════════════════
# POST /micro-instants/{instant_id}/skip
# ═══════════════════════════════════════════════════════════════════


@router.post("/{instant_id}/skip")
async def skip_instant(
    instant_id: str,
    body: SkipRequest,
    user: dict = Depends(get_current_user),
):
    """
    User skips a micro-instant. Records negative feedback
    to improve future predictions.
    """
    from services.micro_instant_engine import record_instant_outcome

    await record_instant_outcome(db, user["user_id"], instant_id, "skipped", {
        "reason": body.reason,
    })

    return {"status": "skipped", "instant_id": instant_id}


# ═══════════════════════════════════════════════════════════════════
# GET /micro-instants/stats
# ═══════════════════════════════════════════════════════════════════


@router.get("/stats")
async def get_instant_stats(user: dict = Depends(get_current_user)):
    """
    Micro-instant exploitation stats:
    - exploitation_rate: exploited / (exploited + skipped + dismissed)
    - total counts by outcome
    - best time slots (highest exploitation rate)
    - trend (this week vs last week)
    """
    user_id = user["user_id"]
    now = datetime.now(timezone.utc)

    # Fetch outcomes from last 30 days
    thirty_days_ago = (now - timedelta(days=30)).isoformat()
    outcomes = await db.micro_instant_outcomes.find({
        "user_id": user_id,
        "recorded_at": {"$gte": thirty_days_ago},
    }, {"_id": 0}).to_list(500)

    total = len(outcomes)
    exploited = len([o for o in outcomes if o.get("outcome") == "exploited"])
    skipped = len([o for o in outcomes if o.get("outcome") == "skipped"])
    dismissed = len([o for o in outcomes if o.get("outcome") == "dismissed"])

    exploitation_rate = exploited / total if total > 0 else 0.0

    # Weekly trend
    seven_days_ago = (now - timedelta(days=7)).isoformat()
    fourteen_days_ago = (now - timedelta(days=14)).isoformat()

    this_week = [o for o in outcomes if o.get("recorded_at", "") >= seven_days_ago]
    last_week = [o for o in outcomes
                 if fourteen_days_ago <= o.get("recorded_at", "") < seven_days_ago]

    this_week_rate = (
        len([o for o in this_week if o.get("outcome") == "exploited"]) / len(this_week)
        if this_week else 0.0
    )
    last_week_rate = (
        len([o for o in last_week if o.get("outcome") == "exploited"]) / len(last_week)
        if last_week else 0.0
    )

    trend = round(this_week_rate - last_week_rate, 3)

    # Total minutes invested via micro-instants
    total_minutes = 0
    for o in outcomes:
        if o.get("outcome") == "exploited":
            total_minutes += o.get("duration", 0)

    return {
        "period_days": 30,
        "total_instants": total,
        "exploited": exploited,
        "skipped": skipped,
        "dismissed": dismissed,
        "exploitation_rate": round(exploitation_rate, 3),
        "total_minutes_invested": total_minutes,
        "weekly_trend": trend,
        "this_week_rate": round(this_week_rate, 3),
        "last_week_rate": round(last_week_rate, 3),
    }
