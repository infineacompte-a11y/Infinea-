"""InFinea — Weekly Leaderboards (Duolingo-style).

Three views:
- Global: all users ranked (GET /leaderboard/weekly)
- Friends: only people you follow + yourself (GET /leaderboard/friends)
- Category: ranked by activity in a specific learning domain (GET /leaderboard/category)

Scoring: total_minutes + (sessions × 5) + (streak_days × 2)
Category scoring: total_minutes + (sessions × 5) — no streak (category-agnostic)
Tiers: podium (1-3), elite (4-10), rising (11-30), standard (31+)
Resets every Monday 00:00 UTC.

Benchmarks: Duolingo (language-specific leagues), Strava (segment leaderboard), Fitbit (challenges).
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
            "level": 1,
            "total_xp": 1,
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
                "level": u.get("level", 1),
                "total_xp": u.get("total_xp", 0),
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


# ── Friends Leaderboard (Duolingo Friends League) ──


def _assign_friends_tier(rank: int, total: int) -> str:
    """Relative tier assignment for friends leaderboard.

    Unlike global (fixed thresholds), friends tiers adapt to group size.
    - Top 20% or rank 1-3 → podium
    - Top 40% or rank 4-10 → elite
    - Top 70% → rising
    - Rest → standard

    This ensures meaningful tiers even in small friend groups (3-5 people).
    """
    if total <= 3:
        return "podium"
    if rank <= 3 or rank <= max(1, int(total * 0.2)):
        return "podium"
    if rank <= 10 or rank <= max(2, int(total * 0.4)):
        return "elite"
    if rank <= max(3, int(total * 0.7)):
        return "rising"
    return "standard"


@router.get("/leaderboard/friends")
async def get_friends_leaderboard(
    user: dict = Depends(get_current_user),
):
    """Friends weekly leaderboard — compete with people you follow.

    Same scoring formula as global, but scoped to your social graph.
    Includes yourself + everyone you follow who had activity this week.
    Tiers are relative to group size (not fixed global thresholds).

    Benchmarked: Duolingo Friends League, Strava Following Leaderboard.
    """
    week_start, week_end = _week_bounds()
    my_id = user["user_id"]

    # ── 1. Get friend IDs (people I follow) ──
    follow_docs = await db.follows.find(
        {"follower_id": my_id, "status": "active"},
        {"_id": 0, "following_id": 1},
    ).to_list(1000)

    friend_ids = [d["following_id"] for d in follow_docs]
    # Include self in the leaderboard
    participant_ids = list(set(friend_ids + [my_id]))

    if len(participant_ids) <= 1:
        # User follows nobody — return self-only placeholder
        streak = user.get("streak_days", 0) or 0
        return {
            "leaderboard": [],
            "my_entry": {
                "user_id": my_id,
                "display_name": user.get("display_name", "Toi"),
                "username": user.get("username"),
                "avatar_url": user.get("avatar_url"),
                "total_minutes": 0,
                "sessions_count": 0,
                "streak_days": streak,
                "score": streak * 2,
                "rank": 1,
                "tier": "podium",
            },
            "total_participants": 0,
            "friends_count": 0,
            "week_start": week_start,
            "week_end": week_end,
        }

    # ── 2. Aggregate sessions for friends + self ──
    pipeline = [
        {
            "$match": {
                "user_id": {"$in": participant_ids},
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

    week_stats = await db.user_sessions_history.aggregate(pipeline).to_list(len(participant_ids))

    # ── 3. Enrich with user profiles ──
    # Include ALL participants (even those with 0 activity) for full ranking
    users_cursor = db.users.find(
        {"user_id": {"$in": participant_ids}},
        {
            "_id": 0,
            "user_id": 1,
            "display_name": 1,
            "username": 1,
            "avatar_url": 1,
            "streak_days": 1,
            "level": 1,
            "total_xp": 1,
        },
    )
    users_map = {u["user_id"]: u async for u in users_cursor}

    stats_map = {s["_id"]: s for s in week_stats}

    # ── 4. Build entries for ALL friends (even inactive ones show with score from streak) ──
    entries = []
    for uid in participant_ids:
        u = users_map.get(uid, {})
        s = stats_map.get(uid, {})
        streak = u.get("streak_days", 0) or 0
        minutes = s.get("total_minutes", 0) or 0
        sessions = s.get("sessions_count", 0) or 0

        score = minutes + (sessions * 5) + (streak * 2)

        entries.append({
            "user_id": uid,
            "display_name": u.get("display_name", "Utilisateur"),
            "username": u.get("username"),
            "avatar_url": u.get("avatar_url"),
            "total_minutes": minutes,
            "sessions_count": sessions,
            "streak_days": streak,
            "score": score,
            "is_self": uid == my_id,
            "level": u.get("level", 1),
            "total_xp": u.get("total_xp", 0),
        })

    # ── 5. Rank by score desc, sessions desc (tiebreak) ──
    entries.sort(key=lambda e: (e["score"], e["sessions_count"]), reverse=True)

    total = len(entries)
    for i, entry in enumerate(entries):
        entry["rank"] = i + 1
        entry["tier"] = _assign_friends_tier(i + 1, total)

    my_entry = next((e for e in entries if e["user_id"] == my_id), None)

    return {
        "leaderboard": entries,
        "my_entry": my_entry,
        "total_participants": total,
        "friends_count": len(friend_ids),
        "week_start": week_start,
        "week_end": week_end,
    }


# ── Category Leaderboard (Duolingo per-language leagues) ──

# Category metadata — labels, icons, colors for frontend rendering
CATEGORY_META = {
    "learning": {"label": "Apprentissage", "icon": "book-open", "color": "#459492"},
    "productivity": {"label": "Productivité", "icon": "briefcase", "color": "#55B3AE"},
    "well_being": {"label": "Bien-être", "icon": "heart", "color": "#E48C75"},
}


@router.get("/leaderboard/categories")
async def get_active_categories(
    user: dict = Depends(get_current_user),
):
    """List categories with activity this week.

    Returns categories sorted by participant count (most active first).
    Enables the frontend to show available category tabs dynamically.
    """
    week_start, week_end = _week_bounds()

    # Aggregate distinct categories with at least 1 completed session this week
    pipeline = [
        {
            "$match": {
                "completed": True,
                "completed_at": {"$gte": week_start, "$lt": week_end},
                "category": {"$ne": None},
            }
        },
        {
            "$group": {
                "_id": "$category",
                "participants": {"$addToSet": "$user_id"},
                "total_sessions": {"$sum": 1},
            }
        },
        {"$project": {
            "category": "$_id",
            "participant_count": {"$size": "$participants"},
            "total_sessions": 1,
            "_id": 0,
        }},
        {"$sort": {"participant_count": -1}},
    ]

    results = await db.user_sessions_history.aggregate(pipeline).to_list(20)

    categories = []
    for r in results:
        cat = r["category"]
        meta = CATEGORY_META.get(cat, {"label": cat.replace("_", " ").title(), "icon": "layers", "color": "#888"})
        categories.append({
            "category": cat,
            "label": meta["label"],
            "icon": meta["icon"],
            "color": meta["color"],
            "participant_count": r["participant_count"],
            "total_sessions": r["total_sessions"],
        })

    return {
        "categories": categories,
        "week_start": week_start,
        "week_end": week_end,
    }


@router.get("/leaderboard/category")
async def get_category_leaderboard(
    category: str,
    user: dict = Depends(get_current_user),
    limit: int = 50,
):
    """Category-specific weekly leaderboard.

    Scoring: total_minutes + (sessions × 5) — streak excluded because
    streak is category-agnostic (a user might have a streak from
    a different category). This keeps the ranking pure to the domain.

    Benchmarked: Duolingo per-language leagues.
    """
    week_start, week_end = _week_bounds()

    # Aggregate sessions filtered by category
    pipeline = [
        {
            "$match": {
                "completed": True,
                "completed_at": {"$gte": week_start, "$lt": week_end},
                "category": category,
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
        meta = CATEGORY_META.get(category, {"label": category})
        return {
            "leaderboard": [],
            "my_entry": {
                "user_id": user["user_id"],
                "display_name": user.get("display_name", "Toi"),
                "avatar_url": user.get("avatar_url"),
                "total_minutes": 0,
                "sessions_count": 0,
                "score": 0,
                "rank": None,
                "tier": "standard",
            },
            "category": category,
            "category_label": meta["label"],
            "total_participants": 0,
            "week_start": week_start,
            "week_end": week_end,
        }

    # Enrich with user profiles
    user_ids = [s["_id"] for s in week_stats]
    users_cursor = db.users.find(
        {"user_id": {"$in": user_ids}},
        {"_id": 0, "user_id": 1, "display_name": 1, "username": 1, "avatar_url": 1,
         "level": 1, "total_xp": 1},
    )
    users_map = {u["user_id"]: u async for u in users_cursor}

    # Category score: minutes + (sessions × 5) — NO streak
    entries = []
    for stat in week_stats:
        uid = stat["_id"]
        u = users_map.get(uid, {})
        minutes = stat["total_minutes"] or 0
        sessions = stat["sessions_count"] or 0
        score = minutes + (sessions * 5)

        entries.append({
            "user_id": uid,
            "display_name": u.get("display_name", "Utilisateur"),
            "username": u.get("username"),
            "avatar_url": u.get("avatar_url"),
            "total_minutes": minutes,
            "sessions_count": sessions,
            "score": score,
            "level": u.get("level", 1),
            "total_xp": u.get("total_xp", 0),
        })

    # Rank
    entries.sort(key=lambda e: (e["score"], e["sessions_count"]), reverse=True)
    total = len(entries)
    for i, entry in enumerate(entries):
        entry["rank"] = i + 1
        entry["tier"] = _assign_friends_tier(i + 1, total)

    my_entry = next((e for e in entries if e["user_id"] == user["user_id"]), None)
    if my_entry is None:
        my_entry = {
            "user_id": user["user_id"],
            "display_name": user.get("display_name", "Toi"),
            "avatar_url": user.get("avatar_url"),
            "total_minutes": 0,
            "sessions_count": 0,
            "score": 0,
            "rank": total + 1,
            "tier": "standard",
        }

    meta = CATEGORY_META.get(category, {"label": category.replace("_", " ").title()})
    return {
        "leaderboard": entries[:limit],
        "my_entry": my_entry,
        "category": category,
        "category_label": meta["label"],
        "total_participants": total,
        "week_start": week_start,
        "week_end": week_end,
    }
