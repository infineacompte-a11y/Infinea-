"""
InFinea — Micro-Instants API routes.
Endpoints for the Micro-Instant Engine (Phase F):
- GET  /micro-instants/today    → predicted micro-instants for today
- POST /micro-instants/{id}/exploit → user starts action in a micro-instant
- POST /micro-instants/{id}/skip    → user skips (negative feedback)
- GET  /micro-instants/stats    → exploitation rate, trends, best slots
- GET  /micro-instants/dashboard → F.5 rich dashboard (hourly distribution, best slots, daily chart)
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
        raise HTTPException(status_code=400, detail="action_id required")

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


# ═══════════════════════════════════════════════════════════════════
# GET /micro-instants/dashboard — F.5 Rich Dashboard
# ═══════════════════════════════════════════════════════════════════


@router.get("/dashboard")
async def get_instant_dashboard(user: dict = Depends(get_current_user)):
    """
    F.5 — Rich micro-instant dashboard.
    Returns comprehensive analytics for the user's micro-instant activity:
    - Summary stats (same as /stats but for current period)
    - Hourly distribution (exploitation rate per hour — for heatmap)
    - Best time slots (top 3 most exploited hours)
    - Daily breakdown (last 7 days — for chart)
    - Source distribution (calendar vs routine vs pattern)
    - Streak & consistency metrics
    - Correlation with objective progression
    """
    user_id = user["user_id"]
    now = datetime.now(timezone.utc)
    seven_days_ago = (now - timedelta(days=7)).isoformat()
    thirty_days_ago = (now - timedelta(days=30)).isoformat()

    # ── Fetch all outcomes (30 days) ──
    outcomes = await db.micro_instant_outcomes.find(
        {"user_id": user_id, "recorded_at": {"$gte": thirty_days_ago}},
        {"_id": 0},
    ).to_list(1000)

    total = len(outcomes)
    exploited = [o for o in outcomes if o.get("outcome") == "exploited"]
    skipped_count = len([o for o in outcomes if o.get("outcome") == "skipped"])
    dismissed_count = len([o for o in outcomes if o.get("outcome") == "dismissed"])

    exploitation_rate = len(exploited) / total if total > 0 else 0.0
    total_minutes = sum(o.get("duration", 0) for o in exploited)

    # ── Hourly distribution (for heatmap) ──
    hourly = {}
    for h in range(24):
        hourly[h] = {"exploited": 0, "skipped": 0, "dismissed": 0, "total": 0}

    for o in outcomes:
        try:
            dt = datetime.fromisoformat(o["recorded_at"].replace("Z", "+00:00"))
            h = dt.hour
        except (ValueError, TypeError, KeyError):
            continue
        hourly[h]["total"] += 1
        outcome = o.get("outcome", "dismissed")
        if outcome in ("exploited", "skipped", "dismissed"):
            hourly[h][outcome] += 1

    hourly_rates = {}
    for h, stats in hourly.items():
        if stats["total"] > 0:
            hourly_rates[str(h)] = {
                "total": stats["total"],
                "exploited": stats["exploited"],
                "rate": round(stats["exploited"] / stats["total"], 3),
            }

    # ── Best time slots (top 3) ──
    ranked_hours = sorted(
        hourly_rates.items(),
        key=lambda x: (x[1]["rate"], x[1]["total"]),
        reverse=True,
    )
    best_slots = []
    for hour_str, data in ranked_hours[:3]:
        if data["total"] >= 2:  # Need at least 2 outcomes to be meaningful
            h = int(hour_str)
            label = f"{h:02d}h00 - {h+1:02d}h00" if h < 23 else "23h00 - 00h00"
            best_slots.append({
                "hour": h,
                "label": label,
                "exploitation_rate": data["rate"],
                "total_outcomes": data["total"],
                "exploited_count": data["exploited"],
            })

    # ── Daily breakdown (last 7 days — for chart) ──
    daily = {}
    for i in range(7):
        day = (now - timedelta(days=i)).date()
        daily[day.isoformat()] = {"exploited": 0, "skipped": 0, "dismissed": 0, "total": 0, "minutes": 0}

    for o in outcomes:
        try:
            dt = datetime.fromisoformat(o["recorded_at"].replace("Z", "+00:00"))
            day_key = dt.date().isoformat()
        except (ValueError, TypeError, KeyError):
            continue
        if day_key not in daily:
            continue
        daily[day_key]["total"] += 1
        outcome = o.get("outcome", "dismissed")
        if outcome in ("exploited", "skipped", "dismissed"):
            daily[day_key][outcome] += 1
        if outcome == "exploited":
            daily[day_key]["minutes"] += o.get("duration", 0)

    # Convert to sorted list (oldest first)
    daily_chart = []
    for day_key in sorted(daily.keys()):
        d = daily[day_key]
        daily_chart.append({
            "date": day_key,
            "exploited": d["exploited"],
            "skipped": d["skipped"],
            "dismissed": d["dismissed"],
            "total": d["total"],
            "minutes": d["minutes"],
            "rate": round(d["exploited"] / d["total"], 3) if d["total"] > 0 else 0.0,
        })

    # ── Source distribution ──
    source_counts = {"calendar_gap": 0, "routine_window": 0, "behavioral_pattern": 0}
    source_exploited = {"calendar_gap": 0, "routine_window": 0, "behavioral_pattern": 0}
    for o in outcomes:
        src = o.get("source", "")
        if src in source_counts:
            source_counts[src] += 1
            if o.get("outcome") == "exploited":
                source_exploited[src] += 1

    source_distribution = {}
    for src in source_counts:
        cnt = source_counts[src]
        source_distribution[src] = {
            "total": cnt,
            "exploited": source_exploited[src],
            "rate": round(source_exploited[src] / cnt, 3) if cnt > 0 else 0.0,
        }

    # ── Weekly trend ──
    fourteen_days_ago = (now - timedelta(days=14)).isoformat()
    this_week = [o for o in outcomes if o.get("recorded_at", "") >= seven_days_ago]
    last_week = [o for o in outcomes
                 if fourteen_days_ago <= o.get("recorded_at", "") < seven_days_ago]

    this_week_exploited = len([o for o in this_week if o.get("outcome") == "exploited"])
    last_week_exploited = len([o for o in last_week if o.get("outcome") == "exploited"])

    this_week_rate = this_week_exploited / len(this_week) if this_week else 0.0
    last_week_rate = last_week_exploited / len(last_week) if last_week else 0.0

    # ── Consistency: streak of days with at least 1 exploited instant ──
    exploit_streak = 0
    for i in range(30):
        day = (now - timedelta(days=i)).date().isoformat()
        day_outcomes = [o for o in outcomes
                        if o.get("recorded_at", "").startswith(day)
                        and o.get("outcome") == "exploited"]
        if day_outcomes:
            exploit_streak += 1
        else:
            break

    # ── Average instants per day (active days only) ──
    active_days = set()
    for o in outcomes:
        try:
            dt = datetime.fromisoformat(o["recorded_at"].replace("Z", "+00:00"))
            active_days.add(dt.date().isoformat())
        except (ValueError, TypeError, KeyError):
            continue

    avg_per_day = round(total / len(active_days), 1) if active_days else 0.0

    # ── Objective progression correlation ──
    objectives = await db.objectives.find(
        {"user_id": user_id, "status": "active"},
        {"_id": 0, "objective_id": 1, "title": 1, "stats": 1},
    ).to_list(10)

    objective_progress = []
    for obj in objectives:
        stats = obj.get("stats", {})
        objective_progress.append({
            "objective_id": obj["objective_id"],
            "title": obj.get("title", ""),
            "total_time_invested": stats.get("total_time_invested", 0),
            "steps_completed": stats.get("total_steps_completed", 0),
            "current_streak": stats.get("current_streak", 0),
        })

    return {
        # ── Summary ──
        "period_days": 30,
        "total_instants": total,
        "exploited": len(exploited),
        "skipped": skipped_count,
        "dismissed": dismissed_count,
        "exploitation_rate": round(exploitation_rate, 3),
        "total_minutes_invested": total_minutes,
        # ── Trend ──
        "this_week_rate": round(this_week_rate, 3),
        "last_week_rate": round(last_week_rate, 3),
        "weekly_trend": round(this_week_rate - last_week_rate, 3),
        "this_week_exploited": this_week_exploited,
        "last_week_exploited": last_week_exploited,
        # ── Distribution ──
        "hourly_rates": hourly_rates,
        "best_slots": best_slots,
        "source_distribution": source_distribution,
        # ── Daily chart (7 days) ──
        "daily_chart": daily_chart,
        # ── Consistency ──
        "exploit_streak_days": exploit_streak,
        "avg_instants_per_active_day": avg_per_day,
        "active_days_count": len(active_days),
        # ── Objective correlation ──
        "objective_progress": objective_progress,
    }
