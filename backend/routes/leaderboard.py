"""InFinea — Global Weekly Leaderboard (Duolingo-style).

Scoring: total_minutes + (sessions × 5) + (streak_days × 2)
Tiers: podium (1-3), elite (4-10), rising (11-30), standard (31+)
Resets every Monday 00:00 UTC.
"""

from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends

from database import db
from auth import get_current_user

router = APIRouter()


def _week_bounds():
    """Return (monday_00:00, next_monday_00:00) as ISO strings for the current week."""
    now = datetime.now(timezone.utc)
    monday = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    next_monday = monday + timedelta(days=7)
    return monday.isoformat(), next_monday.isoformat()


def _assign_tier(rank: int) -> str:
    if rank <= 3:
        return "podium"
    if rank <= 10:
        return "elite"
    if rank <= 30:
        return "rising"
    return "standard"


@router.get("/leaderboard/weekly")
async def get_weekly_leaderboard(
    user: dict = Depends(get_current_user),
    limit: int = 50,
):
    """Global weekly leaderboard ranked by composite score."""
    week_start, week_end = _week_bounds()

    # ── 1. Aggregate completed sessions this week per user ──
    pipeline = [
        {
            "$match": {
                "completed": True,
                "completed_at": {"$gte": week_start, "$lt": week_end},
            }
        },
        {
            "$group": {
                "_id": "$user_id",
                "total_minutes": {"$sum": {"$ifNull": ["$actual_duration", 0]}},
                "sessions_count": {"$sum": 1},
            }
        },
    ]

    week_stats = await db.user_sessions_history.aggregate(pipeline).to_list(500)

    if not week_stats:
        # No activity this week — return empty with user's placeholder entry
        return {
            "leaderboard": [],
            "my_entry": {
                "user_id": user["user_id"],
                "display_name": user.get("display_name", "Toi"),
                "avatar_url": user.get("avatar_url"),
                "total_minutes": 0,
                "sessions_count": 0,
                "streak_days": user.get("streak_days", 0),
                "score": 0,
                "rank": None,
                "tier": "standard",
            },
            "total_participants": 0,
            "week_start": week_start,
            "week_end": week_end,
        }

    # ── 2. Enrich with user profile data ──
    user_ids = [s["_id"] for s in week_stats]
    users_cursor = db.users.find(
        {"user_id": {"$in": user_ids}},
        {
            "_id": 0,
            "user_id": 1,
            "display_name": 1,
            "username": 1,
            "avatar_url": 1,
            "streak_days": 1,
        },
    )
    users_map = {u["user_id"]: u async for u in users_cursor}

    # ── 3. Compute composite score ──
    entries = []
    for stat in week_stats:
        uid = stat["_id"]
        u = users_map.get(uid, {})
        streak = u.get("streak_days", 0) or 0
        minutes = stat["total_minutes"] or 0
        sessions = stat["sessions_count"] or 0

        score = minutes + (sessions * 5) + (streak * 2)

        entries.append(
            {
                "user_id": uid,
                "display_name": u.get("display_name", "Utilisateur"),
                "username": u.get("username"),
                "avatar_url": u.get("avatar_url"),
                "total_minutes": minutes,
                "sessions_count": sessions,
                "streak_days": streak,
                "score": score,
            }
        )

    # ── 4. Rank by score desc, then by sessions desc (tiebreak) ──
    entries.sort(key=lambda e: (e["score"], e["sessions_count"]), reverse=True)

    for i, entry in enumerate(entries):
        entry["rank"] = i + 1
        entry["tier"] = _assign_tier(i + 1)

    # ── 5. Find current user's entry ──
    my_entry = next((e for e in entries if e["user_id"] == user["user_id"]), None)

    if my_entry is None:
        # User has no activity this week
        my_entry = {
            "user_id": user["user_id"],
            "display_name": user.get("display_name", "Toi"),
            "avatar_url": user.get("avatar_url"),
            "total_minutes": 0,
            "sessions_count": 0,
            "streak_days": user.get("streak_days", 0) or 0,
            "score": 0,
            "rank": len(entries) + 1,
            "tier": "standard",
        }

    return {
        "leaderboard": entries[:limit],
        "my_entry": my_entry,
        "total_participants": len(entries),
        "week_start": week_start,
        "week_end": week_end,
    }
