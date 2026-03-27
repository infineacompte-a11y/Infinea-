"""
InFinea — Activity Service.
Creates, queries, and manages activity feed items.

Architecture: Fan-out on read (query activities from followed users).
Simpler than fan-out on write, sufficient for InFinea's scale (<10K users),
and trivial to add/remove follows without rebuilding feeds.

Benchmarked against: Strava's activity feed, Duolingo's social layer.
"""

import asyncio
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from database import db
from services.moderation import get_blocked_ids, get_muted_ids
from services.hashtag_service import generate_auto_tags, update_hashtag_stats

logger = logging.getLogger(__name__)

# Activity types emitted by the system
ACTIVITY_TYPES = {
    "session_completed",
    "badge_earned",
    "streak_milestone",
    "challenge_completed",
    "level_up",  # XP level progression
    "post",  # Manual user post (text, reflections, questions)
}

# Streak milestones that generate activities (avoid noise)
STREAK_MILESTONES = {3, 7, 14, 30, 60, 100, 365}

# InFinea-themed reaction types
REACTION_TYPES = {"bravo", "inspire", "fire", "solidaire", "curieux"}


async def create_activity(
    user_id: str,
    activity_type: str,
    data: dict,
    visibility: str = "public",
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

    # Auto-generate hashtags based on activity type + data
    auto_tags = generate_auto_tags(activity_type, data)

    activity_doc = {
        "activity_id": activity_id,
        "user_id": user_id,
        "type": activity_type,
        "data": data,
        "visibility": visibility,
        "reaction_counts": {"bravo": 0, "inspire": 0, "fire": 0, "solidaire": 0, "curieux": 0},
        "comment_count": 0,
        "created_at": now,
    }
    if auto_tags:
        activity_doc["hashtags"] = auto_tags

    await db.activities.insert_one(activity_doc)

    # Fire-and-forget: update hashtag stats
    if auto_tags:
        asyncio.create_task(update_hashtag_stats(auto_tags))

    return activity_doc


async def get_feed(
    user_id: str,
    cursor: Optional[str] = None,
    limit: int = 20,
) -> dict:
    """
    Get the user's ranked activity feed (fan-out on read + intelligent ranking).

    Flow:
    1. Fetch a larger pool of chronological activities (POOL_MULTIPLIER × limit).
    2. Pass the pool through the feed ranking engine (affinity, quality,
       type weight, freshness, contextual boost, diversity).
    3. Return the top `limit` activities, ranked by composite score.
    4. Cursor advances past the full pool (not just returned items), so
       the next page ranks a fresh window of content.

    This transforms a simple chronological feed into a curated experience
    where the most engaging, relevant, and motivating content surfaces first.

    Returns:
        {activities: [...], next_cursor: str|None, has_more: bool}
    """
    from services.feed_ranking_engine import rank_feed, POOL_MULTIPLIER

    # Get who this user follows
    following_docs = await db.follows.find(
        {"follower_id": user_id, "status": "active"},
        {"following_id": 1},
    ).to_list(1000)

    following_ids = [f["following_id"] for f in following_docs]
    # Include the user's own activities
    following_ids.append(user_id)

    # Filter out blocked + muted users
    blocked_ids, muted_ids = await asyncio.gather(
        get_blocked_ids(user_id),
        get_muted_ids(user_id),
    )
    exclude_ids = blocked_ids | muted_ids
    if exclude_ids:
        following_ids = [fid for fid in following_ids if fid not in exclude_ids]

    query = {
        "user_id": {"$in": following_ids},
        "visibility": {"$in": ["public", "followers"]},
        "moderation_status": {"$ne": "hidden"},
    }

    if cursor:
        query["created_at"] = {"$lt": cursor}

    # Fetch a larger pool for ranking depth.
    # We fetch POOL_MULTIPLIER × limit, rank the pool, then return top `limit`.
    pool_size = limit * POOL_MULTIPLIER

    pool = (
        await db.activities.find(query, {"_id": 0})
        .sort("created_at", -1)
        .limit(pool_size + 1)
        .to_list(pool_size + 1)
    )

    has_more = len(pool) > pool_size
    if has_more:
        pool = pool[:pool_size]

    # ── Followed-hashtag injection (Instagram/LinkedIn pattern) ──
    # Content from hashtags the user follows appears in main feed,
    # even if the author isn't followed. Capped to avoid overwhelming.
    try:
        followed_tags_docs = await db.followed_hashtags.find(
            {"user_id": user_id}, {"_id": 0, "tag": 1}
        ).to_list(30)
        if followed_tags_docs:
            followed_tags = [d["tag"] for d in followed_tags_docs]
            existing_ids = {a["activity_id"] for a in pool}
            ht_query = {
                "hashtags": {"$in": followed_tags},
                "visibility": "public",
                "moderation_status": {"$ne": "hidden"},
                "user_id": {"$nin": list(exclude_ids)},
                "activity_id": {"$nin": list(existing_ids)},
            }
            if cursor:
                ht_query["created_at"] = {"$lt": cursor}
            ht_pool = (
                await db.activities.find(ht_query, {"_id": 0})
                .sort("created_at", -1)
                .limit(limit)
                .to_list(limit)
            )
            for act in ht_pool:
                act["_from_hashtag"] = True
            pool.extend(ht_pool)
            if ht_pool:
                has_more = True
    except Exception:
        logger.warning("Followed-hashtag feed injection failed")

    # ── Cold-start injection (TikTok/Instagram bootstrap pattern) ──
    # If user follows very few people and pool is sparse, inject discover content
    # so the feed never feels empty on first visit.
    real_follow_count = len(following_ids) - 1  # Exclude self
    if len(pool) < limit and real_follow_count < 5 and not cursor:
        # Inject public activities from outside the user's network
        fill_needed = limit - len(pool)
        existing_ids = {a["activity_id"] for a in pool}
        discover_query = {
            "visibility": "public",
            "moderation_status": {"$ne": "hidden"},
            "user_id": {"$nin": list(exclude_ids | {user_id})},
            "activity_id": {"$nin": list(existing_ids)},
        }
        discover_pool = (
            await db.activities.find(discover_query, {"_id": 0})
            .sort("created_at", -1)
            .limit(fill_needed * 2)
            .to_list(fill_needed * 2)
        )
        # Mark injected content so frontend can optionally show "Suggestions pour toi"
        for act in discover_pool:
            act["_injected"] = True
        pool.extend(discover_pool)
        if discover_pool:
            has_more = True  # There's always more discover content

    # Rank the pool — the engine scores each activity on 6 signals
    # and returns them sorted by composite score.
    if len(pool) > 1:
        try:
            pool = await rank_feed(pool, viewer_id=user_id)
        except Exception:
            logger.exception("Feed ranking failed — falling back to chronological")
            # Graceful degradation: if ranking fails, chronological still works

    # Take top `limit` activities from the ranked pool
    activities = pool[:limit]

    # Enrich with user info — batch query
    if activities:
        enriched_user_ids = list({a["user_id"] for a in activities})
        users = await db.users.find(
            {"user_id": {"$in": enriched_user_ids}},
            {"_id": 0, "user_id": 1, "name": 1, "display_name": 1,
             "username": 1, "avatar_url": 1, "picture": 1,
             "last_active": 1, "privacy": 1},
        ).to_list(len(enriched_user_ids))

        user_map = {u["user_id"]: u for u in users}

        # Compute presence for feed authors
        from services.presence_service import compute_presence

        for activity in activities:
            u = user_map.get(activity["user_id"], {})
            activity["user_name"] = u.get("display_name") or u.get("name", "Utilisateur")
            activity["user_username"] = u.get("username")
            activity["user_avatar"] = u.get("avatar_url") or u.get("picture")
            # Presence: respect privacy
            privacy = u.get("privacy", {})
            if privacy.get("show_activity_status") is False:
                activity["user_presence"] = "offline"
            else:
                p = compute_presence(u.get("last_active"))
                activity["user_presence"] = p["status"]

        # Check current user's reactions on these activities
        activity_ids = [a["activity_id"] for a in activities]
        user_reactions = await db.reactions.find(
            {"activity_id": {"$in": activity_ids}, "user_id": user_id},
            {"_id": 0, "activity_id": 1, "reaction_type": 1},
        ).to_list(len(activity_ids))

        reaction_map = {r["activity_id"]: r["reaction_type"] for r in user_reactions}

        # Check current user's bookmarks on these activities
        user_bookmarks = await db.bookmarks.find(
            {"user_id": user_id, "activity_id": {"$in": activity_ids}},
            {"_id": 0, "activity_id": 1},
        ).to_list(len(activity_ids))
        bookmark_set = {b["activity_id"] for b in user_bookmarks}

        # Check poll votes for poll activities
        poll_activity_ids = [
            a["activity_id"] for a in activities
            if a.get("data", {}).get("poll")
        ]
        poll_vote_map = {}
        if poll_activity_ids:
            user_poll_votes = await db.poll_votes.find(
                {"user_id": user_id, "activity_id": {"$in": poll_activity_ids}},
                {"_id": 0, "activity_id": 1, "option_index": 1},
            ).to_list(len(poll_activity_ids))
            poll_vote_map = {v["activity_id"]: v["option_index"] for v in user_poll_votes}

        for activity in activities:
            activity["user_reaction"] = reaction_map.get(activity["activity_id"])
            activity["bookmarked"] = activity["activity_id"] in bookmark_set
            # Inject user's poll vote if applicable
            if activity.get("data", {}).get("poll"):
                vote = poll_vote_map.get(activity["activity_id"])
                if vote is not None:
                    activity["data"]["poll"]["my_vote"] = vote

    # Cursor = oldest created_at in the FULL pool (not just returned items).
    # This advances the window past all ranked content, so the next page
    # gets a fresh pool to rank independently.
    next_cursor = pool[-1]["created_at"] if pool and has_more else None

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
                "xp_awarded": session_data.get("xp_awarded", 0),
            },
        )
    except Exception:
        logger.exception("Failed to emit session activity")
        return None


async def patch_activity_xp(activity_id: str, xp_awarded: int):
    """Patch XP data onto an existing activity (called after XP calculation)."""
    if not activity_id or xp_awarded <= 0:
        return
    try:
        await db.activities.update_one(
            {"activity_id": activity_id},
            {"$set": {"data.xp_awarded": xp_awarded}},
        )
    except Exception:
        logger.warning(f"Failed to patch XP on activity {activity_id}")


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
