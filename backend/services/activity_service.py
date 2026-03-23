"""
InFinea — Activity Service.
Creates, queries, and manages activity feed items.

Architecture: Fan-out on read (query activities from followed users).
Simpler than fan-out on write, sufficient for InFinea's scale (<10K users),
and trivial to add/remove follows without rebuilding feeds.

Benchmarked against: Strava's activity feed, Duolingo's social layer.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from database import db

logger = logging.getLogger(__name__)

# Activity types emitted by the system
ACTIVITY_TYPES = {
    "session_completed",
    "badge_earned",
    "streak_milestone",
    "challenge_completed",
}

# Streak milestones that generate activities (avoid noise)
STREAK_MILESTONES = {3, 7, 14, 30, 60, 100, 365}

# InFinea-themed reaction types
REACTION_TYPES = {"bravo", "inspire", "fire"}


async def create_activity(
    user_id: str,
    activity_type: str,
    data: dict,
    visibility: str = "followers",
) -> Optional[dict]:
    """
    Create a new activity feed item.

    Args:
        user_id: The user who performed the action.
        activity_type: One of ACTIVITY_TYPES.
        data: Type-specific payload (action title, badge name, etc.).
        visibility: "public", "followers", or "private".

    Returns:
        The created activity doc, or None if skipped.
    """
    if activity_type not in ACTIVITY_TYPES:
        logger.warning(f"Unknown activity type: {activity_type}")
        return None

    # Respect user's default visibility preference
    user = await db.users.find_one({"user_id": user_id}, {"privacy": 1})
    if user and user.get("privacy", {}).get("activity_default_visibility"):
        visibility = user["privacy"]["activity_default_visibility"]

    # If private, don't store — no one will see it
    if visibility == "private":
        return None

    activity_id = f"act_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()

    activity_doc = {
        "activity_id": activity_id,
        "user_id": user_id,
        "type": activity_type,
        "data": data,
        "visibility": visibility,
        "reaction_counts": {"bravo": 0, "inspire": 0, "fire": 0},
        "comment_count": 0,
        "created_at": now,
    }

    await db.activities.insert_one(activity_doc)
    return activity_doc


async def get_feed(
    user_id: str,
    cursor: Optional[str] = None,
    limit: int = 20,
) -> dict:
    """
    Get the user's activity feed (fan-out on read).

    Cursor-based pagination using created_at for consistent results
    even when new activities are inserted (no skipped/duplicate items).

    Returns:
        {activities: [...], next_cursor: str|None, has_more: bool}
    """
    # Get who this user follows
    following_docs = await db.follows.find(
        {"follower_id": user_id, "status": "active"},
        {"following_id": 1},
    ).to_list(1000)

    following_ids = [f["following_id"] for f in following_docs]
    # Include the user's own activities
    following_ids.append(user_id)

    query = {
        "user_id": {"$in": following_ids},
        "visibility": {"$in": ["public", "followers"]},
    }

    if cursor:
        query["created_at"] = {"$lt": cursor}

    activities = (
        await db.activities.find(query, {"_id": 0})
        .sort("created_at", -1)
        .limit(limit + 1)
        .to_list(limit + 1)
    )

    has_more = len(activities) > limit
    if has_more:
        activities = activities[:limit]

    # Enrich with user info — batch query
    if activities:
        enriched_user_ids = list({a["user_id"] for a in activities})
        users = await db.users.find(
            {"user_id": {"$in": enriched_user_ids}},
            {"_id": 0, "user_id": 1, "name": 1, "display_name": 1,
             "username": 1, "avatar_url": 1, "picture": 1},
        ).to_list(len(enriched_user_ids))

        user_map = {u["user_id"]: u for u in users}

        for activity in activities:
            u = user_map.get(activity["user_id"], {})
            activity["user_name"] = u.get("display_name") or u.get("name", "Utilisateur")
            activity["user_username"] = u.get("username")
            activity["user_avatar"] = u.get("avatar_url") or u.get("picture")

        # Check current user's reactions on these activities
        activity_ids = [a["activity_id"] for a in activities]
        user_reactions = await db.reactions.find(
            {"activity_id": {"$in": activity_ids}, "user_id": user_id},
            {"_id": 0, "activity_id": 1, "reaction_type": 1},
        ).to_list(len(activity_ids))

        reaction_map = {r["activity_id"]: r["reaction_type"] for r in user_reactions}
        for activity in activities:
            activity["user_reaction"] = reaction_map.get(activity["activity_id"])

    next_cursor = activities[-1]["created_at"] if activities and has_more else None

    return {
        "activities": activities,
        "next_cursor": next_cursor,
        "has_more": has_more,
    }


# ── Emit helpers (called from other routes, non-blocking) ──

async def emit_session_activity(user_id: str, session_data: dict):
    """Emit activity when a session is completed."""
    try:
        return await create_activity(
            user_id=user_id,
            activity_type="session_completed",
            data={
                "action_title": session_data.get("action_title", "Micro-action"),
                "category": session_data.get("category", ""),
                "duration": session_data.get("actual_duration", 0),
            },
        )
    except Exception:
        logger.exception("Failed to emit session activity")
        return None


async def emit_badge_activity(user_id: str, badge: dict):
    """Emit activity when a badge is earned."""
    try:
        return await create_activity(
            user_id=user_id,
            activity_type="badge_earned",
            data={
                "badge_name": badge.get("name", ""),
                "badge_icon": badge.get("icon", ""),
                "badge_id": badge.get("badge_id", ""),
            },
        )
    except Exception:
        logger.exception("Failed to emit badge activity")
        return None


async def emit_streak_activity(user_id: str, streak_days: int):
    """Emit activity for streak milestones only (not every day)."""
    if streak_days not in STREAK_MILESTONES:
        return None
    try:
        return await create_activity(
            user_id=user_id,
            activity_type="streak_milestone",
            data={"streak_days": streak_days},
        )
    except Exception:
        logger.exception("Failed to emit streak activity")
        return None
