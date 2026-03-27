"""
InFinea — Activity Feed routes.
Feed listing, reactions, comments.

Design:
- Cursor-based pagination (consistent results, no duplicates).
- Fan-out on read (query from followed users' activities).
- Reactions: curated InFinea set (bravo, inspire, fire).
- Comments: lightweight, moderation-ready.
- Benchmarked: Strava's feed UX, LinkedIn's engagement model.
"""

import asyncio
import logging
import math
import os
import uuid
from collections import defaultdict
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, HTTPException, Depends, Request, UploadFile, File
from fastapi.responses import JSONResponse

from database import db
from auth import get_current_user
from services.activity_service import get_feed, REACTION_TYPES
from services.moderation import get_blocked_ids, get_muted_ids, check_content, sanitize_text, extract_mentions
from services.hashtag_service import extract_hashtags, update_hashtag_stats
from helpers import send_push_to_user, create_notification_deduped
from services.email_service import send_email_to_user, email_mention
from config import limiter

logger = logging.getLogger(__name__)
router = APIRouter()

# ============== IMAGE UPLOAD CONFIG ==============
IMAGE_MAX_SIZE = 10 * 1024 * 1024  # 10 MB per image
IMAGE_ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_IMAGES_PER_POST = 4
CLOUDINARY_URL = os.getenv("CLOUDINARY_URL", "")


# ============== FEED ==============

@router.get("/feed/new-count")
async def get_new_post_count(
    since: str,
    user: dict = Depends(get_current_user),
):
    """
    Count new activities in the user's feed since a given ISO timestamp.
    Used by frontend polling to show "X nouveaux posts" banner.
    Lightweight: count only, no document fetch.
    """
    user_id = user["user_id"]

    # Same audience as main feed: followed users + self
    following_docs = await db.follows.find(
        {"follower_id": user_id, "status": "active"},
        {"following_id": 1},
    ).limit(1000).to_list(1000)

    following_ids = [f["following_id"] for f in following_docs]
    following_ids.append(user_id)

    blocked_ids = await get_blocked_ids(user_id)
    if blocked_ids:
        following_ids = [fid for fid in following_ids if fid not in blocked_ids]

    count = await db.activities.count_documents({
        "user_id": {"$in": following_ids},
        "visibility": {"$in": ["public", "followers"]},
        "moderation_status": {"$ne": "hidden"},
        "created_at": {"$gt": since},
    })

    return {"new_count": count}


@router.get("/feed")
@limiter.limit("60/minute")
async def get_activity_feed(
    request: Request,
    user: dict = Depends(get_current_user),
    cursor: str = None,
    limit: int = 20,
):
    """
    Get the user's activity feed.
    Cursor-based: pass `next_cursor` from previous response as `cursor`.
    """
    if limit > 50:
        limit = 50
    return await get_feed(user_id=user["user_id"], cursor=cursor, limit=limit)


@router.get("/feed/discover")
@limiter.limit("60/minute")
async def get_discover_feed(
    request: Request,
    user: dict = Depends(get_current_user),
    cursor: str = None,
    limit: int = 20,
):
    """
    Discover feed: public activities from ALL users, ranked by discover algorithm.
    Instagram Explore equivalent — surfaces trending, high-quality, diverse content.

    Flow:
    1. Fetch a larger pool (DISCOVER_POOL_MULTIPLIER × limit) chronologically.
    2. Rank by 4 signals: quality, trending (velocity), type weight, freshness.
    3. Apply contextual boost (learning journey awareness).
    4. Apply strict diversity (max 2 per author).
    5. Return top `limit` activities.
    """
    from services.feed_ranking_engine import rank_discover, DISCOVER_POOL_MULTIPLIER

    if limit > 50:
        limit = 50

    # Filter out blocked + muted users from discover
    blocked_ids, muted_ids = await asyncio.gather(
        get_blocked_ids(user["user_id"]),
        get_muted_ids(user["user_id"]),
    )
    exclude_ids = blocked_ids | muted_ids

    query = {"visibility": "public", "moderation_status": {"$ne": "hidden"}}
    if exclude_ids:
        query["user_id"] = {"$nin": list(exclude_ids)}
    if cursor:
        query["created_at"] = {"$lt": cursor}

    # Fetch larger pool for ranking depth
    pool_size = limit * DISCOVER_POOL_MULTIPLIER

    pool = (
        await db.activities.find(query, {"_id": 0})
        .sort("created_at", -1)
        .limit(pool_size + 1)
        .to_list(pool_size + 1)
    )

    has_more = len(pool) > pool_size
    if has_more:
        pool = pool[:pool_size]

    # Rank the pool — trending, quality, type, freshness, contextual boost, diversity
    if len(pool) > 1:
        try:
            pool = await rank_discover(pool, viewer_id=user["user_id"])
        except Exception:
            logger.exception("Discover ranking failed — falling back to chronological")

    # Take top `limit` from ranked pool
    activities = pool[:limit]

    # Enrich with user info (including level for social proof)
    if activities:
        enriched_user_ids = list({a["user_id"] for a in activities})
        users = await db.users.find(
            {"user_id": {"$in": enriched_user_ids}},
            {"_id": 0, "user_id": 1, "name": 1, "display_name": 1,
             "username": 1, "avatar_url": 1, "picture": 1,
             "level": 1, "total_xp": 1},
        ).to_list(len(enriched_user_ids))
        user_map = {u["user_id"]: u for u in users}

        for activity in activities:
            u = user_map.get(activity["user_id"], {})
            activity["user_name"] = u.get("display_name") or u.get("name", "Utilisateur")
            activity["user_username"] = u.get("username")
            activity["user_avatar"] = u.get("avatar_url") or u.get("picture")
            activity["user_level"] = u.get("level", 1)

        # Check current user's reactions
        activity_ids = [a["activity_id"] for a in activities]
        user_reactions = await db.reactions.find(
            {"activity_id": {"$in": activity_ids}, "user_id": user["user_id"]},
            {"_id": 0, "activity_id": 1, "reaction_type": 1},
        ).to_list(len(activity_ids))
        reaction_map = {r["activity_id"]: r["reaction_type"] for r in user_reactions}

        # Check current user's bookmarks
        user_bookmarks = await db.bookmarks.find(
            {"user_id": user["user_id"], "activity_id": {"$in": activity_ids}},
            {"_id": 0, "activity_id": 1},
        ).to_list(len(activity_ids))
        bookmark_set = {b["activity_id"] for b in user_bookmarks}

        for activity in activities:
            activity["user_reaction"] = reaction_map.get(activity["activity_id"])
            activity["bookmarked"] = activity["activity_id"] in bookmark_set

    # Cursor = oldest created_at in the FULL pool (advances past all ranked content)
    next_cursor = pool[-1]["created_at"] if pool and has_more else None
    return {"activities": activities, "next_cursor": next_cursor, "has_more": has_more}


@router.get("/feed/suggested-users")
@limiter.limit("20/minute")
async def get_suggested_users(
    request: Request,
    user: dict = Depends(get_current_user),
    limit: int = 15,
):
    """Multi-signal user recommendation engine (v2 — 8 signals).

    Architecture — 8-signal scoring (benchmarked: LinkedIn PYMK,
    Instagram Suggestions, Twitter Who to Follow, Strava Suggested Athletes,
    Duolingo league grouping):

    Signal 1 — MUTUAL CONNECTIONS (weight: 500/mutual, cap 2500)
        Friends-of-friends. Strongest social signal. LinkedIn PYMK core signal.

    Signal 2 — SHARED OBJECTIVES (weight: 300/category + 200/exact title)
        Users working on same goals. Unique to InFinea.

    Signal 3 — GROUP AFFINITY (weight: 250/shared group, cap 750)
        Users in the same groups. Strong interest signal.

    Signal 4 — ENGAGEMENT QUALITY (weight: 0-400)
        Composite: activity count (log scale), streak days, total time.

    Signal 5 — FOLLOWS YOU (weight: 350)
        High-intent candidate. Instagram surfaces these prominently.

    Signal 6 — INTERACTION AFFINITY (weight: 400/interaction, cap 1200) [NEW]
        Users who reacted to or commented on your activities (or vice versa).
        "Warm connections" — engaged but not yet following.
        Benchmarked: Instagram "Accounts You Interact With".

    Signal 7 — HASHTAG OVERLAP (weight: 200/shared tag, cap 600) [NEW]
        Content affinity — users posting about similar topics.
        Benchmarked: Twitter interest-based suggestions.

    Signal 8 — LEVEL PROXIMITY (weight: 0-200) [NEW]
        Users at similar XP levels get a boost (±3 levels = max).
        Prevents intimidation (newbie vs veteran).
        Benchmarked: Duolingo league grouping.

    Post-scoring:
    - Privacy filter: exclude users with profile_visible=False
    - Graduated recency: 24h → +150, 3 days → +100, 7 days → +50
    - Diversity: cap same-reason users to 60% to prevent filter bubbles
    - Each result includes `reason` + `level` for frontend display
    """
    my_id = user["user_id"]
    if limit > 30:
        limit = 30

    # ── Phase 1: Gather exclusions (parallel) ──
    following_docs, blocked_ids = await asyncio.gather(
        db.follows.find(
            {"follower_id": my_id, "status": "active"}, {"following_id": 1}
        ).limit(500).to_list(500),
        get_blocked_ids(my_id),
    )
    exclude_ids = {f["following_id"] for f in following_docs}
    exclude_ids.add(my_id)
    exclude_ids |= blocked_ids
    exclude_list = list(exclude_ids)

    # ── Phase 2: Gather signals (parallel — 5 queries) ──

    # 2a. Who I follow (for mutual connection calc)
    my_following_ids = {f["following_id"] for f in following_docs}

    # 2b. Who follows me but I don't follow back
    async def fetch_followers_not_followed():
        docs = await db.follows.find(
            {"following_id": my_id, "status": "active", "follower_id": {"$nin": exclude_list}},
            {"follower_id": 1},
        ).to_list(500)
        return {d["follower_id"] for d in docs}

    # 2c. Friends of friends (mutual connections)
    async def fetch_friends_of_friends():
        """For each person I follow, find who they follow (that I don't)."""
        if not my_following_ids:
            return defaultdict(set)
        fof_docs = await db.follows.find(
            {
                "follower_id": {"$in": list(my_following_ids)},
                "following_id": {"$nin": exclude_list},
                "status": "active",
            },
            {"follower_id": 1, "following_id": 1},
        ).limit(1000).to_list(1000)
        # Map: candidate_id → set of mutual connection ids
        mutual_map = defaultdict(set)
        for d in fof_docs:
            mutual_map[d["following_id"]].add(d["follower_id"])
        return mutual_map

    # 2d. My objectives (for category + title matching)
    async def fetch_my_objectives():
        docs = await db.objectives.find(
            {"user_id": my_id, "status": {"$in": ["active", "completed"]}},
            {"category": 1, "title": 1},
        ).to_list(50)
        return docs

    # 2e. My groups (for group affinity)
    async def fetch_my_groups():
        docs = await db.groups.find(
            {"members.user_id": my_id, "status": "active"},
            {"group_id": 1, "members.user_id": 1},
        ).to_list(50)
        return docs

    # 2f. Interaction affinity — users I've interacted with (reactions/comments)
    # Instagram's "Accounts You Interact With" — warm connections without follow
    async def fetch_interaction_affinity():
        """Bidirectional: who reacted/commented on my stuff + who I reacted/commented on."""
        interaction_map = defaultdict(int)  # user_id → interaction count

        # People who reacted to my activities
        my_activity_ids_docs = await db.activities.find(
            {"user_id": my_id}, {"activity_id": 1}
        ).limit(200).to_list(200)
        my_act_ids = [a["activity_id"] for a in my_activity_ids_docs]

        if my_act_ids:
            reactors = await db.reactions.find(
                {"activity_id": {"$in": my_act_ids}, "user_id": {"$nin": exclude_list}},
                {"user_id": 1},
            ).limit(500).to_list(500)
            for r in reactors:
                interaction_map[r["user_id"]] += 1

            commenters = await db.comments.find(
                {"activity_id": {"$in": my_act_ids}, "user_id": {"$nin": exclude_list}},
                {"user_id": 1},
            ).limit(500).to_list(500)
            for c in commenters:
                interaction_map[c["user_id"]] += 1

        # Activities I reacted to or commented on (reverse direction)
        my_reactions = await db.reactions.find(
            {"user_id": my_id}, {"activity_id": 1}
        ).limit(200).to_list(200)
        my_comments = await db.comments.find(
            {"user_id": my_id}, {"activity_id": 1}
        ).limit(200).to_list(200)

        interacted_act_ids = list({
            r["activity_id"] for r in my_reactions
        } | {
            c["activity_id"] for c in my_comments
        })

        if interacted_act_ids:
            owners = await db.activities.find(
                {"activity_id": {"$in": interacted_act_ids}, "user_id": {"$nin": exclude_list}},
                {"user_id": 1},
            ).to_list(len(interacted_act_ids))
            for o in owners:
                interaction_map[o["user_id"]] += 1

        return interaction_map

    # 2g. My hashtags — for content affinity matching
    async def fetch_my_hashtags():
        """Collect hashtags from my recent activities for interest matching."""
        docs = await db.activities.find(
            {"user_id": my_id, "hashtags": {"$exists": True, "$ne": []}},
            {"hashtags": 1},
        ).sort("created_at", -1).limit(50).to_list(50)
        tags = set()
        for d in docs:
            tags.update(d.get("hashtags", []))
        return tags

    # 2h. My level (for level proximity scoring)
    async def fetch_my_level():
        doc = await db.users.find_one({"user_id": my_id}, {"level": 1})
        return (doc or {}).get("level", 1)

    (followers_set, mutual_map, my_objectives, my_groups,
     interaction_map, my_hashtags, my_level) = await asyncio.gather(
        fetch_followers_not_followed(),
        fetch_friends_of_friends(),
        fetch_my_objectives(),
        fetch_my_groups(),
        fetch_interaction_affinity(),
        fetch_my_hashtags(),
        fetch_my_level(),
    )

    # ── Phase 3: Build candidate pool ──
    # Merge candidates from all signal sources
    candidate_ids = set()
    candidate_ids |= set(mutual_map.keys())  # friends of friends
    candidate_ids |= followers_set            # people who follow me

    # Add users with shared objectives
    my_categories = {o.get("category") for o in my_objectives if o.get("category")}
    my_titles = {o.get("title", "").lower().strip() for o in my_objectives if o.get("title")}
    shared_obj_map = defaultdict(lambda: {"categories": set(), "exact_titles": set()})

    if my_categories:
        obj_docs = await db.objectives.find(
            {
                "user_id": {"$nin": exclude_list},
                "category": {"$in": list(my_categories)},
                "status": {"$in": ["active", "completed"]},
            },
            {"user_id": 1, "category": 1, "title": 1},
        ).limit(500).to_list(500)
        for o in obj_docs:
            uid = o["user_id"]
            candidate_ids.add(uid)
            if o.get("category"):
                shared_obj_map[uid]["categories"].add(o["category"])
            if o.get("title") and o["title"].lower().strip() in my_titles:
                shared_obj_map[uid]["exact_titles"].add(o["title"])

    # Add users from shared groups
    my_group_members = defaultdict(int)  # user_id → number of shared groups
    for g in my_groups:
        for m in g.get("members", []):
            mid = m.get("user_id") or m
            if mid not in exclude_ids:
                candidate_ids.add(mid)
                my_group_members[mid] += 1

    # Add users from interaction affinity (reacted/commented on my stuff or vice versa)
    candidate_ids |= set(interaction_map.keys())

    # Add users with shared hashtags (content affinity)
    hashtag_overlap_map = defaultdict(set)  # user_id → set of shared tags
    if my_hashtags:
        tag_docs = await db.activities.find(
            {
                "user_id": {"$nin": exclude_list},
                "hashtags": {"$in": list(my_hashtags)},
            },
            {"user_id": 1, "hashtags": 1},
        ).sort("created_at", -1).limit(500).to_list(500)
        for td in tag_docs:
            uid = td["user_id"]
            shared = set(td.get("hashtags", [])) & my_hashtags
            if shared:
                candidate_ids.add(uid)
                hashtag_overlap_map[uid] |= shared

    # Fallback: intelligent cold-start (level proximity + recent activity)
    # Better than brute "most active" — surfaces users at similar level
    if len(candidate_ids) < limit * 2:
        pipeline = [
            {"$match": {"user_id": {"$nin": exclude_list}, "visibility": "public"}},
            {"$group": {"_id": "$user_id", "count": {"$sum": 1}, "last": {"$max": "$created_at"}}},
            {"$sort": {"last": -1, "count": -1}},
            {"$limit": limit * 4},
        ]
        fallback = await db.activities.aggregate(pipeline).to_list(limit * 4)
        for f in fallback:
            candidate_ids.add(f["_id"])

    candidate_ids -= exclude_ids  # Safety: re-exclude
    if not candidate_ids:
        return {"users": []}

    # ── Phase 4: Fetch candidate user docs + activity stats (parallel) ──
    candidate_list = list(candidate_ids)

    async def fetch_users():
        return await db.users.find(
            {"user_id": {"$in": candidate_list}},
            {
                "_id": 0, "user_id": 1, "name": 1, "display_name": 1,
                "username": 1, "avatar_url": 1, "picture": 1,
                "subscription_tier": 1, "streak_days": 1,
                "total_time_invested": 1, "last_active": 1,
                "privacy": 1, "created_at": 1, "level": 1,
            },
        ).to_list(len(candidate_list))

    async def fetch_activity_stats():
        pipeline = [
            {"$match": {"user_id": {"$in": candidate_list}, "visibility": "public"}},
            {"$group": {
                "_id": "$user_id",
                "activity_count": {"$sum": 1},
                "last_activity": {"$max": "$created_at"},
            }},
        ]
        return await db.activities.aggregate(pipeline).to_list(len(candidate_list))

    async def fetch_follower_counts():
        pipeline = [
            {"$match": {"following_id": {"$in": candidate_list}, "status": "active"}},
            {"$group": {"_id": "$following_id", "count": {"$sum": 1}}},
        ]
        return await db.follows.aggregate(pipeline).to_list(len(candidate_list))

    user_docs, activity_stats, follower_counts = await asyncio.gather(
        fetch_users(), fetch_activity_stats(), fetch_follower_counts(),
    )

    users_by_id = {u["user_id"]: u for u in user_docs}
    activity_by_id = {a["_id"]: a for a in activity_stats}
    followers_by_id = {f["_id"]: f["count"] for f in follower_counts}

    # ── Phase 5: Score each candidate — 8-signal algorithm ──
    #
    # Weights calibrated against LinkedIn PYMK, Instagram Suggestions,
    # Strava Suggested Athletes, Duolingo league grouping.
    #
    # | Signal                | Max weight | Source              |
    # |-----------------------|-----------|---------------------|
    # | 1. Mutual connections | 2500      | LinkedIn PYMK       |
    # | 2. Shared objectives  | ~700      | InFinea-unique      |
    # | 3. Group affinity     | 750       | Discord/Slack       |
    # | 4. Engagement quality | 400       | All platforms       |
    # | 5. Follows you        | 350       | Instagram           |
    # | 6. Interaction aff.   | 1200      | Instagram "interact"|
    # | 7. Hashtag overlap    | 600       | Twitter interests   |
    # | 8. Level proximity    | 200       | Duolingo leagues    |
    # | Recency (graduated)   | 150       | All platforms       |
    #
    now = datetime.now(timezone.utc)
    one_day_ago = (now - timedelta(days=1)).isoformat()
    three_days_ago = (now - timedelta(days=3)).isoformat()
    seven_days_ago = (now - timedelta(days=7)).isoformat()

    scored = []
    for uid in candidate_ids:
        u = users_by_id.get(uid)
        if not u:
            continue

        # Privacy filter
        privacy = u.get("privacy", {})
        if privacy.get("profile_visible") is False:
            continue

        score = 0
        reasons = []

        # Signal 1: Mutual connections (500 per mutual, capped at 2500)
        mutuals = mutual_map.get(uid, set())
        mutual_count = len(mutuals)
        if mutual_count > 0:
            score += min(mutual_count * 500, 2500)
            reasons.append(("mutual", mutual_count))

        # Signal 2: Shared objectives (300 per category match + 200 exact title bonus)
        obj_data = shared_obj_map.get(uid)
        if obj_data:
            shared_cats = obj_data["categories"] & my_categories
            shared_titles = obj_data["exact_titles"]
            if shared_cats:
                score += len(shared_cats) * 300
                reasons.append(("objectives", len(shared_cats)))
            if shared_titles:
                score += len(shared_titles) * 200
                reasons.append(("same_goal", list(shared_titles)[0]))

        # Signal 3: Group affinity (250 per shared group, capped at 750)
        group_count = my_group_members.get(uid, 0)
        if group_count > 0:
            score += min(group_count * 250, 750)
            reasons.append(("group", group_count))

        # Signal 4: Engagement quality (0-400)
        stats = activity_by_id.get(uid, {})
        activity_count = stats.get("activity_count", 0)
        streak = u.get("streak_days", 0)
        total_time = u.get("total_time_invested", 0)

        engagement = min(math.log2(max(activity_count, 1) + 1) * 30, 150)
        engagement += min(streak * 5, 150)
        engagement += min(total_time * 0.1, 100)
        score += engagement

        # Signal 5: Follows you (350)
        if uid in followers_set:
            score += 350
            if not reasons or reasons[0][0] != "mutual":
                reasons.insert(0, ("follows_you", True))

        # Signal 6: Interaction affinity (400 per interaction, capped at 1200)
        # Warm connections — they engaged with my content or I engaged with theirs
        interactions = interaction_map.get(uid, 0)
        if interactions > 0:
            score += min(interactions * 400, 1200)
            if not any(r[0] in ("mutual", "follows_you") for r in reasons):
                reasons.insert(0, ("interacted", interactions))

        # Signal 7: Hashtag overlap (200 per shared tag, capped at 600)
        # Content affinity — similar interests based on activity tags
        shared_tags = hashtag_overlap_map.get(uid, set())
        shared_tag_count = len(shared_tags)
        if shared_tag_count > 0:
            score += min(shared_tag_count * 200, 600)
            if not reasons:
                reasons.append(("shared_interests", shared_tag_count))

        # Signal 8: Level proximity (0-200, Duolingo-style)
        # Users within ±3 levels get max bonus, scales down linearly
        candidate_level = u.get("level", 1)
        level_diff = abs(my_level - candidate_level)
        if level_diff <= 3:
            score += 200 - (level_diff * 30)  # 200, 170, 140, 110
        elif level_diff <= 7:
            score += max(100 - (level_diff - 3) * 25, 0)  # 75, 50, 25, 0

        # Recency bonus — graduated (not binary)
        # Active 24h ago: +150, 3 days: +100, 7 days: +50
        last_activity = stats.get("last_activity", "")
        if last_activity:
            if last_activity > one_day_ago:
                score += 150
            elif last_activity > three_days_ago:
                score += 100
            elif last_activity > seven_days_ago:
                score += 50

        # Determine primary reason for frontend display
        if reasons:
            primary = reasons[0]
        elif activity_count > 0:
            primary = ("active", activity_count)
        else:
            primary = ("new_user", True)

        scored.append({
            "user_id": uid,
            "display_name": u.get("display_name") or u.get("name", "Utilisateur"),
            "username": u.get("username"),
            "avatar_url": u.get("avatar_url") or u.get("picture"),
            "subscription_tier": u.get("subscription_tier", "free"),
            "followers_count": followers_by_id.get(uid, 0),
            "streak_days": streak,
            "mutual_count": mutual_count,
            "level": candidate_level,
            "reason": primary[0],
            "reason_detail": primary[1],
            "_score": score,
        })

    # ── Phase 6: Sort + diversity + limit ──
    scored.sort(key=lambda x: x["_score"], reverse=True)

    # Diversity: prevent filter bubble — cap same reason_type to 60% of results
    max_per_reason = max(int(limit * 0.6), 3)
    reason_counts = defaultdict(int)
    final = []
    overflow = []
    for s in scored:
        r = s["reason"]
        if reason_counts[r] < max_per_reason:
            final.append(s)
            reason_counts[r] += 1
        else:
            overflow.append(s)
        if len(final) >= limit:
            break

    # Fill remaining slots from overflow
    if len(final) < limit:
        for s in overflow:
            final.append(s)
            if len(final) >= limit:
                break

    # Remove internal score from response
    for s in final:
        s.pop("_score", None)

    return {"users": final}


@router.get("/feed/own")
async def get_own_activities(
    user: dict = Depends(get_current_user),
    cursor: str = None,
    limit: int = 20,
):
    """Get only the authenticated user's own activities."""
    if limit > 50:
        limit = 50

    query = {"user_id": user["user_id"], "moderation_status": {"$ne": "hidden"}}
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

    next_cursor = activities[-1]["created_at"] if activities and has_more else None

    return {
        "activities": activities,
        "next_cursor": next_cursor,
        "has_more": has_more,
    }


# ============== IMAGE UPLOAD FOR POSTS ==============

@router.post("/feed/upload-image")
async def upload_post_image(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """Upload an image for a post. Returns the image URL for client-side preview.

    The client uploads images first, collects URLs, then submits the post
    with image_urls in the body. This pattern is used by Instagram, Twitter,
    and LinkedIn — upload-then-attach for instant previews and retry on failure.

    Accepts JPEG, PNG, WebP, GIF up to 10 MB.
    Cloudinary auto-optimizes (quality, format, responsive breakpoints).
    Moderation: Cloudinary AI moderation (rejects NSFW if enabled).

    Returns:
        {image_url, thumbnail_url, width, height, public_id}
    """
    if not CLOUDINARY_URL:
        raise HTTPException(
            status_code=503,
            detail="Service d'upload non configuré (CLOUDINARY_URL manquant)",
        )

    if file.content_type not in IMAGE_ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Format non supporté. Utilisez JPEG, PNG, WebP ou GIF.",
        )

    contents = await file.read()
    if len(contents) > IMAGE_MAX_SIZE:
        raise HTTPException(status_code=400, detail="L'image ne doit pas dépasser 10 Mo")
    if len(contents) < 1024:
        raise HTTPException(status_code=400, detail="Fichier trop petit ou corrompu")

    try:
        import cloudinary
        import cloudinary.uploader

        image_id = f"post_{uuid.uuid4().hex[:12]}"
        result = await asyncio.to_thread(
            cloudinary.uploader.upload,
            contents,
            folder="infinea/posts",
            public_id=image_id,
            transformation=[
                {
                    "width": 1200,
                    "height": 1200,
                    "crop": "limit",       # Preserve aspect ratio, cap at 1200px
                    "quality": "auto:good",
                    "fetch_format": "auto",
                },
            ],
            resource_type="image",
            # Eager: generate thumbnail for feed cards
            eager=[
                {
                    "width": 600,
                    "height": 600,
                    "crop": "fill",
                    "gravity": "auto",
                    "quality": "auto:eco",
                    "fetch_format": "auto",
                },
            ],
        )

        # Full-size URL (max 1200px, auto quality)
        image_url = result["secure_url"]
        # Thumbnail URL (600px square crop for feed grid)
        thumbnail_url = (
            result.get("eager", [{}])[0].get("secure_url", image_url)
            if result.get("eager")
            else image_url
        )

        return {
            "image_url": image_url,
            "thumbnail_url": thumbnail_url,
            "width": result.get("width", 0),
            "height": result.get("height", 0),
            "public_id": result.get("public_id", ""),
        }

    except Exception as e:
        logger.exception(f"Image upload failed for {user['user_id']}: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de l'upload de l'image")


# ============== CREATE MANUAL POST ==============

@router.post("/activities")
@limiter.limit("10/minute")
async def create_manual_post(
    request: Request,
    user: dict = Depends(get_current_user),
):
    """Create a manual post in the community feed (text + optional images).

    Benchmarked: Instagram (images + caption), Strava (activity + photos),
    LinkedIn (text + media), Twitter (multi-image posts).

    Body:
        content (str): Post text, 1-2000 chars (can be empty if images provided).
        images (list, optional): Up to 4 image objects from upload-image endpoint.
            Each: {image_url, thumbnail_url, width, height}
        visibility (str, optional): "public" | "followers". Default: user preference.
        category (str, optional): "learning" | "productivity" | "well_being" | "general".
    """
    body = await request.json()
    content = sanitize_text(str(body.get("content", "")), max_length=2000)
    images = body.get("images", [])

    # Validate: need either text or images
    has_text = content and len(content.strip()) >= 3
    has_images = isinstance(images, list) and len(images) > 0

    if not has_text and not has_images:
        raise HTTPException(status_code=400, detail="Le post doit contenir du texte (min 3 car.) ou des images")

    if has_images and len(images) > MAX_IMAGES_PER_POST:
        raise HTTPException(status_code=400, detail=f"Maximum {MAX_IMAGES_PER_POST} images par post")

    # Validate image objects
    validated_images = []
    if has_images:
        for img in images[:MAX_IMAGES_PER_POST]:
            if not isinstance(img, dict) or not img.get("image_url"):
                continue
            validated_images.append({
                "image_url": str(img["image_url"]),
                "thumbnail_url": str(img.get("thumbnail_url", img["image_url"])),
                "width": int(img.get("width", 0)),
                "height": int(img.get("height", 0)),
            })

    # Moderation (text only — images moderated at upload time by Cloudinary)
    if has_text:
        moderation = check_content(content)
        if not moderation["allowed"]:
            raise HTTPException(status_code=400, detail=moderation["reason"])

    # Visibility: respect user preference or explicit choice
    visibility = body.get("visibility")
    if visibility not in ("public", "followers"):
        privacy = user.get("privacy", {})
        visibility = privacy.get("activity_default_visibility", "public")
        if visibility == "private":
            visibility = "public"

    # Category (optional — enriches feed ranking via contextual boost)
    category = body.get("category", "general")
    if category not in ("learning", "productivity", "well_being", "general"):
        category = "general"

    # Extract @mentions
    blocked_ids = await get_blocked_ids(user["user_id"])
    mentions = await extract_mentions(content, user["user_id"], blocked_ids) if has_text else []

    # Extract #hashtags from content
    hashtags = extract_hashtags(content) if has_text else []

    now = datetime.now(timezone.utc).isoformat()
    activity_id = f"act_{uuid.uuid4().hex[:12]}"

    activity_data = {
        "content": content if has_text else "",
        "category": category,
        "mentions": mentions,
    }
    if validated_images:
        activity_data["images"] = validated_images

    activity_doc = {
        "activity_id": activity_id,
        "user_id": user["user_id"],
        "type": "post",
        "data": activity_data,
        "visibility": visibility,
        "reaction_counts": {"bravo": 0, "inspire": 0, "fire": 0, "solidaire": 0, "curieux": 0},
        "comment_count": 0,
        "created_at": now,
    }
    if hashtags:
        activity_doc["hashtags"] = hashtags

    await db.activities.insert_one(activity_doc)

    # Fire-and-forget: update hashtag stats
    if hashtags:
        asyncio.create_task(update_hashtag_stats(hashtags))

    # Fire-and-forget: extract link preview (OG card — Slack/Discord/iMessage pattern)
    if has_text:
        try:
            from services.link_preview_service import extract_first_url, fetch_link_preview

            first_url = extract_first_url(content)
            if first_url:
                async def _fetch_and_store_preview(act_id, url):
                    preview = await fetch_link_preview(url)
                    if preview:
                        await db.activities.update_one(
                            {"activity_id": act_id},
                            {"$set": {"data.link_preview": preview}},
                        )
                asyncio.create_task(_fetch_and_store_preview(activity_id, first_url))
        except Exception:
            pass

    # Layer 2: async AI moderation (fire-and-forget, never blocks)
    try:
        from services.ai_moderation import moderate_content_async
        image_urls = [img["image_url"] for img in validated_images] if validated_images else None
        asyncio.create_task(moderate_content_async(
            content_id=activity_id,
            content_type="post",
            author_id=user["user_id"],
            text=content if has_text else "",
            image_urls=image_urls,
        ))
    except Exception:
        pass  # Moderation failure must never block post creation

    # Notify mentioned users
    display = user.get("display_name") or user.get("name", "Quelqu'un")
    for m in mentions:
        try:
            await db.notifications.insert_one({
                "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
                "user_id": m["user_id"],
                "type": "mention",
                "message": f"{display} vous a mentionné dans un post",
                "data": {
                    "activity_id": activity_id,
                    "mentioner_id": user["user_id"],
                },
                "read": False,
                "created_at": now,
            })
            await send_push_to_user(
                m["user_id"],
                f"{display} vous a mentionné",
                content[:80],
                url=f"/activity/{activity_id}",
                tag="mention",
            )
            subject, html = email_mention(display, content, f"/activity/{activity_id}")
            await send_email_to_user(m["user_id"], subject, html, email_category="social")
        except Exception:
            pass

    # Award post XP (5 XP, max 1 per day — anti-spam)
    try:
        from services.xp_engine import award_xp, POST_XP
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0).isoformat()
        already_earned = await db.xp_history.count_documents({
            "user_id": user["user_id"],
            "source": "post",
            "created_at": {"$gte": today_start},
        })
        if already_earned == 0:
            await award_xp(user["user_id"], POST_XP, source="post", details={"activity_id": activity_id})
    except Exception:
        pass  # XP must never block post creation

    # Return enriched activity for immediate frontend display
    return {
        "activity_id": activity_id,
        "user_id": user["user_id"],
        "type": "post",
        "data": activity_doc["data"],
        "visibility": visibility,
        "reaction_counts": {"bravo": 0, "inspire": 0, "fire": 0, "solidaire": 0, "curieux": 0},
        "comment_count": 0,
        "created_at": now,
        "user_name": user.get("display_name") or user.get("name", "Utilisateur"),
        "user_username": user.get("username"),
        "user_avatar": user.get("avatar_url") or user.get("picture"),
        "user_level": user.get("level", 1),
    }


# ============== DELETE ACTIVITY ==============

@router.delete("/activities/{activity_id}")
async def delete_activity(activity_id: str, user: dict = Depends(get_current_user)):
    """Delete own activity and cascade-delete associated reactions and comments."""
    activity = await db.activities.find_one({"activity_id": activity_id})
    if not activity:
        raise HTTPException(status_code=404, detail="Activité introuvable")

    if activity["user_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Vous ne pouvez supprimer que vos propres activités")

    # Cascade delete: reactions + comments + bookmarks
    await db.reactions.delete_many({"activity_id": activity_id})
    await db.comments.delete_many({"activity_id": activity_id})
    await db.bookmarks.delete_many({"activity_id": activity_id})
    await db.activities.delete_one({"activity_id": activity_id})

    # Decrement hashtag stats (fire-and-forget)
    deleted_tags = activity.get("hashtags", [])
    if deleted_tags:
        asyncio.create_task(update_hashtag_stats(deleted_tags, increment=-1))

    return {"message": "Activité supprimée"}


# ============== PIN ACTIVITY (LinkedIn Featured / Twitter Pinned) ==============

MAX_PINS = 3  # LinkedIn allows 5, Twitter 1, we allow 3


@router.post("/activities/{activity_id}/pin")
async def pin_activity(activity_id: str, user: dict = Depends(get_current_user)):
    """Pin an activity to your profile (max 3, LinkedIn Featured pattern).
    Pinned activities appear in a highlighted section on your profile."""
    my_id = user["user_id"]
    activity = await db.activities.find_one({"activity_id": activity_id})
    if not activity:
        raise HTTPException(status_code=404, detail="Activité introuvable")
    if activity["user_id"] != my_id:
        raise HTTPException(status_code=403, detail="Vous ne pouvez épingler que vos propres activités")
    if activity.get("pinned"):
        raise HTTPException(status_code=400, detail="Activité déjà épinglée")

    # Check max pins
    pin_count = await db.activities.count_documents({"user_id": my_id, "pinned": True})
    if pin_count >= MAX_PINS:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {MAX_PINS} activités épinglées. Désépinglez-en une d'abord.",
        )

    now = datetime.now(timezone.utc).isoformat()
    await db.activities.update_one(
        {"activity_id": activity_id},
        {"$set": {"pinned": True, "pinned_at": now}},
    )
    return {"message": "Activité épinglée", "pinned": True}


@router.delete("/activities/{activity_id}/pin")
async def unpin_activity(activity_id: str, user: dict = Depends(get_current_user)):
    """Unpin an activity from your profile."""
    activity = await db.activities.find_one({"activity_id": activity_id})
    if not activity:
        raise HTTPException(status_code=404, detail="Activité introuvable")
    if activity["user_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Vous ne pouvez modifier que vos propres activités")

    await db.activities.update_one(
        {"activity_id": activity_id},
        {"$set": {"pinned": False}, "$unset": {"pinned_at": ""}},
    )
    return {"message": "Activité désépinglée", "pinned": False}


@router.get("/users/{user_id}/pinned")
async def get_pinned_activities(
    user_id: str,
    user: dict = Depends(get_current_user),
):
    """Get a user's pinned activities (for profile display)."""
    blocked_ids = await get_blocked_ids(user["user_id"])
    if user_id in blocked_ids:
        return {"activities": []}

    activities = await db.activities.find(
        {
            "user_id": user_id,
            "pinned": True,
            "moderation_status": {"$ne": "hidden"},
        },
        {"_id": 0},
    ).sort("pinned_at", -1).limit(MAX_PINS).to_list(MAX_PINS)

    # Enrich with user info
    if activities:
        u = await db.users.find_one(
            {"user_id": user_id},
            {"_id": 0, "user_id": 1, "display_name": 1, "name": 1,
             "username": 1, "avatar_url": 1, "picture": 1, "level": 1},
        )
        for a in activities:
            a["user_name"] = u.get("display_name") or u.get("name", "Utilisateur") if u else "Utilisateur"
            a["user_username"] = u.get("username", "") if u else ""
            a["user_avatar"] = (u.get("avatar_url") or u.get("picture", "")) if u else ""
            a["user_level"] = u.get("level", 1) if u else 1

    return {"activities": activities}


# ============== ACTIVITY DETAIL ==============

@router.get("/activities/{activity_id}")
async def get_activity_detail(
    activity_id: str,
    user: dict = Depends(get_current_user),
):
    """Get a single activity with full enrichment.

    Returns the activity with author info, viewer's reaction, bookmark status,
    and top-level comments with replies. Used for permalink pages and
    notification deep links.

    Benchmarked: Instagram post detail, Twitter/X tweet detail, Strava activity.
    """
    activity = await db.activities.find_one(
        {"activity_id": activity_id, "moderation_status": {"$ne": "hidden"}},
        {"_id": 0},
    )
    if not activity:
        raise HTTPException(status_code=404, detail="Activité introuvable")

    my_id = user["user_id"]

    # ── Enrich with author info ──
    author = await db.users.find_one(
        {"user_id": activity["user_id"]},
        {"_id": 0, "user_id": 1, "name": 1, "display_name": 1,
         "username": 1, "avatar_url": 1, "picture": 1, "level": 1},
    )
    if author:
        activity["user_name"] = author.get("display_name") or author.get("name", "Utilisateur")
        activity["user_username"] = author.get("username")
        activity["user_avatar"] = author.get("avatar_url") or author.get("picture")
        activity["user_level"] = author.get("level", 1)

    # ── Viewer's reaction ──
    my_reaction = await db.reactions.find_one(
        {"activity_id": activity_id, "user_id": my_id},
        {"_id": 0, "reaction_type": 1},
    )
    activity["user_reaction"] = my_reaction["reaction_type"] if my_reaction else None

    # ── Bookmark status ──
    bm = await db.bookmarks.find_one(
        {"user_id": my_id, "activity_id": activity_id},
        {"_id": 0},
    )
    activity["bookmarked"] = bm is not None

    # ── Comments (top-level + replies, Instagram pattern) ──
    comments = await db.comments.find(
        {"activity_id": activity_id, "moderation_status": {"$ne": "hidden"}},
        {"_id": 0},
    ).sort("created_at", 1).limit(100).to_list(100)

    # Check viewer's likes on these comments
    comment_ids = [c["comment_id"] for c in comments]
    my_likes = set()
    if comment_ids:
        liked = await db.comment_likes.find(
            {"comment_id": {"$in": comment_ids}, "user_id": my_id},
            {"comment_id": 1},
        ).to_list(len(comment_ids))
        my_likes = {l["comment_id"] for l in liked}

    for c in comments:
        c["liked_by_me"] = c["comment_id"] in my_likes

    # Structure: top-level comments with nested replies
    top_level = [c for c in comments if not c.get("parent_id")]
    reply_map = defaultdict(list)
    for c in comments:
        if c.get("parent_id"):
            reply_map[c["parent_id"]].append(c)

    for c in top_level:
        c["replies"] = reply_map.get(c["comment_id"], [])

    activity["comments"] = top_level
    activity["total_comments"] = len(comments)

    return activity


# ============== REACTIONS ==============

@router.post("/activities/{activity_id}/react")
@limiter.limit("30/minute")
async def react_to_activity(
    activity_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    """
    React to an activity. One reaction per user per activity.
    Same type → toggle off. Different type → change.
    """
    body = await request.json()
    reaction_type = body.get("reaction_type", "")
    if reaction_type not in REACTION_TYPES:
        raise HTTPException(status_code=400, detail=f"Type invalide. Choix : {', '.join(REACTION_TYPES)}")

    activity = await db.activities.find_one({"activity_id": activity_id})
    if not activity:
        raise HTTPException(status_code=404, detail="Activité introuvable")

    existing = await db.reactions.find_one(
        {"activity_id": activity_id, "user_id": user["user_id"]}
    )

    now = datetime.now(timezone.utc).isoformat()

    if existing:
        if existing["reaction_type"] == reaction_type:
            # Toggle off
            await db.reactions.delete_one({"_id": existing["_id"]})
            await db.activities.update_one(
                {"activity_id": activity_id},
                {"$inc": {f"reaction_counts.{reaction_type}": -1}},
            )
            return {"reacted": False, "reaction_type": None}
        else:
            # Switch type
            old_type = existing["reaction_type"]
            await db.reactions.update_one(
                {"_id": existing["_id"]},
                {"$set": {"reaction_type": reaction_type, "updated_at": now}},
            )
            await db.activities.update_one(
                {"activity_id": activity_id},
                {"$inc": {
                    f"reaction_counts.{old_type}": -1,
                    f"reaction_counts.{reaction_type}": 1,
                }},
            )
            return {"reacted": True, "reaction_type": reaction_type}
    else:
        # New reaction
        await db.reactions.insert_one({
            "reaction_id": f"react_{uuid.uuid4().hex[:12]}",
            "activity_id": activity_id,
            "user_id": user["user_id"],
            "reaction_type": reaction_type,
            "created_at": now,
        })
        await db.activities.update_one(
            {"activity_id": activity_id},
            {"$inc": {f"reaction_counts.{reaction_type}": 1}},
        )

        # Notify activity owner (non-blocking, silent fail, dedup 1h)
        if activity["user_id"] != user["user_id"]:
            try:
                display = user.get("display_name") or user.get("name", "Quelqu'un")
                created = await create_notification_deduped(
                    user_id=activity["user_id"],
                    notif_type="reaction",
                    message=f"{display} a réagi à votre activité",
                    data={
                        "activity_id": activity_id,
                        "reaction_type": reaction_type,
                        "reactor_id": user["user_id"],
                        "reactor_name": display,
                    },
                    dedup_hours=1,
                )
                if created:
                    await send_push_to_user(
                        activity["user_id"],
                        "Nouvelle réaction",
                        f"{display} a réagi à ton activité",
                        url=f"/activity/{activity_id}",
                        tag="reaction",
                    )
            except Exception:
                pass  # Non-blocking

        return {"reacted": True, "reaction_type": reaction_type}


@router.get("/activities/{activity_id}/reactions")
async def get_activity_reactions(
    activity_id: str,
    user: dict = Depends(get_current_user),
):
    """List all reactions on an activity with user details."""
    activity = await db.activities.find_one({"activity_id": activity_id})
    if not activity:
        raise HTTPException(status_code=404, detail="Activit\u00e9 introuvable")

    reactions = await db.reactions.find(
        {"activity_id": activity_id}, {"_id": 0}
    ).sort("created_at", -1).to_list(200)

    if not reactions:
        return {"reactions": [], "count": 0}

    # Batch-fetch user details for all reactors
    user_ids = list({r["user_id"] for r in reactions})
    users_cursor = db.users.find(
        {"user_id": {"$in": user_ids}},
        {"_id": 0, "user_id": 1, "display_name": 1, "name": 1,
         "username": 1, "avatar_url": 1, "picture": 1},
    )
    users_map = {u["user_id"]: u async for u in users_cursor}

    result = []
    for r in reactions:
        u = users_map.get(r["user_id"], {})
        result.append({
            "user_id": r["user_id"],
            "reaction_type": r["reaction_type"],
            "display_name": u.get("display_name") or u.get("name", "Utilisateur"),
            "username": u.get("username"),
            "avatar_url": u.get("avatar_url") or u.get("picture"),
            "created_at": r.get("created_at"),
        })

    return {"reactions": result, "count": len(result)}


# ============== COMMENTS ==============

@router.post("/activities/{activity_id}/comments")
@limiter.limit("20/minute")
async def add_comment(
    activity_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    """Add a comment (or reply) to an activity.

    Threaded comments — benchmarked: Instagram (2-level), YouTube (2-level),
    Reddit (deep nesting). InFinea uses 2-level threading (top-level + replies)
    for clarity and engagement without complexity.

    Body:
        content (str): Comment text, 1-500 chars.
        parent_id (str, optional): If set, this is a reply to an existing comment.
    """
    body = await request.json()
    content = sanitize_text(str(body.get("content", "")), max_length=500)
    if not content:
        raise HTTPException(status_code=400, detail="Le commentaire doit faire entre 1 et 500 caractères")

    # Moderation check
    moderation = check_content(content)
    if not moderation["allowed"]:
        raise HTTPException(status_code=400, detail=moderation["reason"])

    activity = await db.activities.find_one({"activity_id": activity_id})
    if not activity:
        raise HTTPException(status_code=404, detail="Activité introuvable")

    # ── Threading: validate parent_id if provided ──
    parent_id = body.get("parent_id")
    parent_comment = None
    if parent_id:
        parent_comment = await db.comments.find_one(
            {"comment_id": parent_id, "activity_id": activity_id}
        )
        if not parent_comment:
            raise HTTPException(status_code=404, detail="Commentaire parent introuvable")
        # Enforce 2-level max: if parent is itself a reply, attach to its parent instead
        if parent_comment.get("parent_id"):
            parent_id = parent_comment["parent_id"]
            parent_comment = await db.comments.find_one({"comment_id": parent_id})

    # Extract @mentions
    blocked_ids = await get_blocked_ids(user["user_id"])
    mentions = await extract_mentions(content, user["user_id"], blocked_ids)

    now = datetime.now(timezone.utc).isoformat()
    comment_id = f"com_{uuid.uuid4().hex[:12]}"

    comment_doc = {
        "comment_id": comment_id,
        "activity_id": activity_id,
        "user_id": user["user_id"],
        "user_name": user.get("display_name") or user.get("name", "Utilisateur"),
        "user_username": user.get("username"),
        "user_avatar": user.get("avatar_url") or user.get("picture"),
        "content": content,
        "mentions": mentions,
        "parent_id": parent_id,  # None for top-level, comment_id for replies
        "reply_count": 0,
        "created_at": now,
    }

    await db.comments.insert_one(comment_doc)
    await db.activities.update_one(
        {"activity_id": activity_id},
        {"$inc": {"comment_count": 1}},
    )

    # Layer 2: async AI moderation on comment
    try:
        from services.ai_moderation import moderate_content_async
        asyncio.create_task(moderate_content_async(
            content_id=comment_id,
            content_type="comment",
            author_id=user["user_id"],
            text=content,
        ))
    except Exception:
        pass

    # Increment reply_count on parent comment
    if parent_id:
        await db.comments.update_one(
            {"comment_id": parent_id},
            {"$inc": {"reply_count": 1}},
        )

    display = user.get("display_name") or user.get("name", "Quelqu'un")

    # ── Notifications (non-blocking, silent fail) ──
    already_notified = set()

    # 1. Notify parent comment author (reply notification — highest priority)
    if parent_comment and parent_comment["user_id"] != user["user_id"]:
        try:
            parent_author = parent_comment.get("user_name", "quelqu'un")
            await db.notifications.insert_one({
                "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
                "user_id": parent_comment["user_id"],
                "type": "reply",
                "message": f"{display} a répondu à ton commentaire",
                "data": {
                    "activity_id": activity_id,
                    "comment_id": comment_id,
                    "parent_id": parent_id,
                    "replier_id": user["user_id"],
                    "commenter_name": display,
                },
                "read": False,
                "created_at": now,
            })
            await send_push_to_user(
                parent_comment["user_id"],
                "Nouvelle réponse",
                f"{display} a répondu à ton commentaire",
                url=f"/activity/{activity_id}",
                tag="reply",
            )
            already_notified.add(parent_comment["user_id"])
        except Exception:
            pass

    # 2. Notify activity owner (skip if already notified as parent author, or if self)
    if activity["user_id"] != user["user_id"] and activity["user_id"] not in already_notified:
        try:
            notif_type = "comment" if not parent_id else "reply"
            notif_msg = (
                f"{display} a commenté votre activité"
                if not parent_id
                else f"{display} a répondu dans les commentaires"
            )
            await db.notifications.insert_one({
                "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
                "user_id": activity["user_id"],
                "type": notif_type,
                "message": notif_msg,
                "data": {
                    "activity_id": activity_id,
                    "comment_id": comment_id,
                    "commenter_id": user["user_id"],
                    "commenter_name": display,
                },
                "read": False,
                "created_at": now,
            })
            await send_push_to_user(
                activity["user_id"],
                "Nouveau commentaire" if not parent_id else "Nouvelle réponse",
                notif_msg,
                url=f"/activity/{activity_id}",
                tag="comment",
            )
            already_notified.add(activity["user_id"])
        except Exception:
            pass

    # 3. Notify mentioned users (skip already notified)
    for m in mentions:
        if m["user_id"] in already_notified or m["user_id"] == user["user_id"]:
            continue
        try:
            await db.notifications.insert_one({
                "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
                "user_id": m["user_id"],
                "type": "mention",
                "message": f"{display} vous a mentionné dans un commentaire",
                "data": {
                    "activity_id": activity_id,
                    "comment_id": comment_id,
                    "mentioner_id": user["user_id"],
                    "user_name": display,
                },
                "read": False,
                "created_at": now,
            })
            await send_push_to_user(
                m["user_id"],
                f"{display} vous a mentionné",
                content[:80],
                url=f"/activity/{activity_id}",
                tag="mention",
            )
            # Email for mentions
            subject, html = email_mention(display, content, f"/activity/{activity_id}")
            await send_email_to_user(m["user_id"], subject, html, email_category="social")
            already_notified.add(m["user_id"])
        except Exception:
            pass

    response = {
        "comment_id": comment_id,
        "activity_id": activity_id,
        "user_id": user["user_id"],
        "user_name": comment_doc["user_name"],
        "user_username": comment_doc["user_username"],
        "user_avatar": comment_doc["user_avatar"],
        "content": content,
        "mentions": mentions,
        "parent_id": parent_id,
        "reply_count": 0,
        "created_at": now,
    }
    return response


@router.get("/activities/{activity_id}/comments")
async def get_comments(
    activity_id: str,
    user: dict = Depends(get_current_user),
    limit: int = 30,
    skip: int = 0,
    parent_id: str = None,
):
    """Get threaded comments on an activity.

    Benchmarked: Instagram (top-level + "View replies" expand), YouTube (same pattern).

    Default (no parent_id): returns top-level comments with reply_count.
    With parent_id: returns replies to that specific comment.

    This 2-request pattern is efficient — only loads replies on demand,
    keeping initial payload small for fast feed rendering.
    """
    activity = await db.activities.find_one({"activity_id": activity_id})
    if not activity:
        raise HTTPException(status_code=404, detail="Activité introuvable")

    # Filter out comments from blocked users
    blocked_ids = await get_blocked_ids(user["user_id"])
    comment_query = {"activity_id": activity_id, "moderation_status": {"$ne": "hidden"}}
    if blocked_ids:
        comment_query["user_id"] = {"$nin": list(blocked_ids)}

    if parent_id:
        # Fetch replies to a specific comment
        comment_query["parent_id"] = parent_id
    else:
        # Fetch top-level comments only (parent_id is null or missing)
        comment_query["$or"] = [
            {"parent_id": None},
            {"parent_id": {"$exists": False}},
        ]

    comments = (
        await db.comments.find(comment_query, {"_id": 0})
        .sort("created_at", 1)
        .skip(skip)
        .limit(limit)
        .to_list(limit)
    )

    # Ensure reply_count, parent_id, like_count fields exist in response
    # + check which comments the current user has liked
    comment_ids = [c["comment_id"] for c in comments]
    my_likes = set()
    if comment_ids:
        liked_docs = await db.comment_likes.find(
            {"comment_id": {"$in": comment_ids}, "user_id": user["user_id"]},
            {"comment_id": 1},
        ).to_list(len(comment_ids))
        my_likes = {d["comment_id"] for d in liked_docs}

    for c in comments:
        c.setdefault("reply_count", 0)
        c.setdefault("parent_id", None)
        c.setdefault("like_count", 0)
        c["liked_by_me"] = c["comment_id"] in my_likes

    total = await db.comments.count_documents(comment_query)
    return {"comments": comments, "total": total}


# ── Edit window constant (15 minutes — Discord/Slack benchmark) ──
EDIT_WINDOW_SECONDS = 15 * 60


@router.put("/comments/{comment_id}")
async def edit_comment(
    comment_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    """Edit own comment within 15-minute window.

    Benchmarked: Discord (unlimited), Slack (unlimited), Instagram (no edit).
    InFinea uses 15-minute window — encourages thoughtful posting while allowing
    quick fixes. Shows "(modifié)" badge after edit.
    """
    comment = await db.comments.find_one({"comment_id": comment_id})
    if not comment:
        raise HTTPException(status_code=404, detail="Commentaire introuvable")

    if comment["user_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Vous ne pouvez modifier que vos propres commentaires")

    # Enforce 15-minute edit window
    created = datetime.fromisoformat(comment["created_at"])
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    elapsed = (datetime.now(timezone.utc) - created).total_seconds()
    if elapsed > EDIT_WINDOW_SECONDS:
        raise HTTPException(status_code=403, detail="La fenêtre de modification de 15 minutes est expirée")

    body = await request.json()
    content = sanitize_text(str(body.get("content", "")), max_length=500)
    if not content:
        raise HTTPException(status_code=400, detail="Le commentaire doit faire entre 1 et 500 caractères")

    moderation = check_content(content)
    if not moderation["allowed"]:
        raise HTTPException(status_code=400, detail=moderation["reason"])

    # Re-extract @mentions
    blocked_ids = await get_blocked_ids(user["user_id"])
    mentions = await extract_mentions(content, user["user_id"], blocked_ids)

    now = datetime.now(timezone.utc).isoformat()
    await db.comments.update_one(
        {"comment_id": comment_id},
        {"$set": {
            "content": content,
            "mentions": mentions,
            "edited_at": now,
        }},
    )

    return {
        "comment_id": comment_id,
        "content": content,
        "mentions": mentions,
        "edited_at": now,
    }


@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: str,
    user: dict = Depends(get_current_user),
):
    """Delete own comment. Cascade-deletes replies if top-level."""
    comment = await db.comments.find_one({"comment_id": comment_id})
    if not comment:
        raise HTTPException(status_code=404, detail="Commentaire introuvable")

    if comment["user_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Vous ne pouvez supprimer que vos propres commentaires")

    deleted_count = 1  # The comment itself

    if comment.get("parent_id"):
        # This is a reply — decrement parent's reply_count
        await db.comments.update_one(
            {"comment_id": comment["parent_id"]},
            {"$inc": {"reply_count": -1}},
        )
    else:
        # This is a top-level comment — cascade-delete all its replies
        reply_result = await db.comments.delete_many({"parent_id": comment_id})
        deleted_count += reply_result.deleted_count

    await db.comments.delete_one({"comment_id": comment_id})
    await db.activities.update_one(
        {"activity_id": comment["activity_id"]},
        {"$inc": {"comment_count": -deleted_count}},
    )

    return {"message": "Commentaire supprimé"}


# ============== COMMENT LIKES ==============

@router.post("/comments/{comment_id}/like")
async def toggle_comment_like(
    comment_id: str,
    user: dict = Depends(get_current_user),
):
    """Toggle like on a comment. One like per user per comment.

    Benchmarked: Instagram (heart on comment), YouTube (thumbs up on comment).
    Simple toggle — no reaction types, just like/unlike.
    """
    comment = await db.comments.find_one({"comment_id": comment_id})
    if not comment:
        raise HTTPException(status_code=404, detail="Commentaire introuvable")

    existing = await db.comment_likes.find_one(
        {"comment_id": comment_id, "user_id": user["user_id"]}
    )

    if existing:
        # Unlike
        await db.comment_likes.delete_one({"_id": existing["_id"]})
        await db.comments.update_one(
            {"comment_id": comment_id},
            {"$inc": {"like_count": -1}},
        )
        return {"liked": False, "like_count": max(0, (comment.get("like_count", 0)) - 1)}
    else:
        # Like
        now = datetime.now(timezone.utc).isoformat()
        await db.comment_likes.insert_one({
            "comment_id": comment_id,
            "user_id": user["user_id"],
            "created_at": now,
        })
        new_count = (comment.get("like_count", 0)) + 1
        await db.comments.update_one(
            {"comment_id": comment_id},
            {"$inc": {"like_count": 1}},
        )

        # Notify comment author (non-blocking)
        if comment["user_id"] != user["user_id"]:
            try:
                display = user.get("display_name") or user.get("name", "Quelqu'un")
                await db.notifications.insert_one({
                    "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
                    "user_id": comment["user_id"],
                    "type": "comment_like",
                    "message": f"{display} a aimé ton commentaire",
                    "data": {
                        "comment_id": comment_id,
                        "liker_id": user["user_id"],
                        "activity_id": comment.get("activity_id"),
                    },
                    "read": False,
                    "created_at": now,
                })
                await send_push_to_user(
                    comment["user_id"],
                    "Commentaire aimé",
                    f"{display} a aimé ton commentaire",
                    url=f"/activity/{comment.get('activity_id', '')}",
                    tag="comment_like",
                )
            except Exception:
                pass

        return {"liked": True, "like_count": new_count}


# ============== CONTENT SEARCH ==============


@router.get("/feed/search")
@limiter.limit("30/minute")
async def search_activities(
    request: Request,
    q: str = "",
    cursor: str = "",
    limit: int = 20,
    user: dict = Depends(get_current_user),
):
    """Search public activities by text content (Instagram Explore search pattern).

    Uses MongoDB regex for text matching across content field.
    Only returns public, non-hidden activities from non-blocked users.
    Results ranked by relevance (exact match > partial) then recency.
    """
    if len(q) < 2:
        raise HTTPException(status_code=400, detail="Minimum 2 caractères")

    limit = min(max(limit, 1), 50)
    user_id = user["user_id"]
    blocked_ids = await get_blocked_ids(user_id)

    # Use MongoDB text index for search (French language, much faster than $regex)
    # Text search returns results scored by relevance — combine with recency
    muted_ids = await get_muted_ids(user_id)
    exclude_ids = list(blocked_ids | muted_ids)

    query = {
        "$text": {"$search": q},
        "visibility": "public",
        "moderation_status": {"$ne": "hidden"},
    }
    if exclude_ids:
        query["user_id"] = {"$nin": exclude_ids}
    if cursor:
        query["created_at"] = {"$lt": cursor}

    activities = await db.activities.find(
        query, {"_id": 0, "score": {"$meta": "textScore"}}
    ).sort([("score", {"$meta": "textScore"}), ("created_at", -1)]).limit(limit + 1).to_list(limit + 1)

    has_more = len(activities) > limit
    activities = activities[:limit]

    if not activities:
        return {"activities": [], "next_cursor": None, "has_more": False}

    # Enrich with user info
    enriched_user_ids = list({a["user_id"] for a in activities})
    users_cursor = db.users.find(
        {"user_id": {"$in": enriched_user_ids}},
        {"_id": 0, "user_id": 1, "display_name": 1, "name": 1,
         "username": 1, "avatar_url": 1, "picture": 1, "level": 1},
    )
    users_map = {u["user_id"]: u async for u in users_cursor}

    # Check bookmarks + reactions
    activity_ids = [a["activity_id"] for a in activities]
    user_reactions = await db.reactions.find(
        {"user_id": user_id, "activity_id": {"$in": activity_ids}},
        {"_id": 0, "activity_id": 1, "reaction_type": 1},
    ).to_list(len(activity_ids))
    reaction_map = {r["activity_id"]: r["reaction_type"] for r in user_reactions}

    user_bookmarks = await db.bookmarks.find(
        {"user_id": user_id, "activity_id": {"$in": activity_ids}},
        {"_id": 0, "activity_id": 1},
    ).to_list(len(activity_ids))
    bookmark_set = {b["activity_id"] for b in user_bookmarks}

    for a in activities:
        u = users_map.get(a["user_id"], {})
        a["user_name"] = u.get("display_name") or u.get("name", "Utilisateur")
        a["user_username"] = u.get("username", "")
        a["user_avatar"] = u.get("avatar_url") or u.get("picture", "")
        a["user_level"] = u.get("level", 1)
        a["user_reaction"] = reaction_map.get(a["activity_id"])
        a["bookmarked"] = a["activity_id"] in bookmark_set

    next_cursor = activities[-1]["created_at"] if has_more else None
    return {"activities": activities, "next_cursor": next_cursor, "has_more": has_more}


# ============== BOOKMARKS ==============


@router.post("/activities/{activity_id}/bookmark")
@limiter.limit("30/minute")
async def toggle_bookmark(
    activity_id: str,
    user: dict = Depends(get_current_user),
):
    """Toggle bookmark on an activity (Instagram Saved pattern).

    First call bookmarks, second call un-bookmarks.
    Collection: bookmarks {user_id, activity_id, created_at}
    """
    activity = await db.activities.find_one(
        {"activity_id": activity_id, "moderation_status": {"$ne": "hidden"}},
        {"activity_id": 1},
    )
    if not activity:
        raise HTTPException(status_code=404, detail="Activité introuvable")

    user_id = user["user_id"]
    existing = await db.bookmarks.find_one(
        {"user_id": user_id, "activity_id": activity_id}
    )

    if existing:
        await db.bookmarks.delete_one({"_id": existing["_id"]})
        return {"bookmarked": False}

    await db.bookmarks.insert_one({
        "user_id": user_id,
        "activity_id": activity_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"bookmarked": True}


@router.get("/bookmarks")
async def get_bookmarks(
    cursor: str = "",
    limit: int = 20,
    user: dict = Depends(get_current_user),
):
    """List user's bookmarked activities (newest first, cursor-based).

    Returns full activity data enriched the same way as the main feed.
    """
    user_id = user["user_id"]
    limit = min(max(limit, 1), 50)

    # Build query for bookmarks
    query = {"user_id": user_id}
    if cursor:
        query["created_at"] = {"$lt": cursor}

    bookmarks = await db.bookmarks.find(
        query, {"_id": 0, "activity_id": 1, "created_at": 1}
    ).sort("created_at", -1).limit(limit + 1).to_list(limit + 1)

    has_more = len(bookmarks) > limit
    bookmarks = bookmarks[:limit]

    if not bookmarks:
        return {"bookmarks": [], "next_cursor": None}

    # Fetch the actual activities
    activity_ids = [b["activity_id"] for b in bookmarks]
    blocked_ids = await get_blocked_ids(user_id)

    activities = await db.activities.find(
        {
            "activity_id": {"$in": activity_ids},
            "moderation_status": {"$ne": "hidden"},
            "user_id": {"$nin": blocked_ids},
        },
        {"_id": 0},
    ).to_list(len(activity_ids))

    # Index by activity_id for ordering
    act_map = {a["activity_id"]: a for a in activities}

    # Enrich with user info + bookmark metadata
    enriched_user_ids = list({a["user_id"] for a in activities})
    users_cursor = db.users.find(
        {"user_id": {"$in": enriched_user_ids}},
        {"_id": 0, "user_id": 1, "display_name": 1, "name": 1,
         "username": 1, "avatar_url": 1, "picture": 1, "level": 1},
    )
    users_map = {u["user_id"]: u async for u in users_cursor}

    # Check which activities the user has reacted to
    user_reactions = await db.reactions.find(
        {"user_id": user_id, "activity_id": {"$in": activity_ids}},
        {"_id": 0, "activity_id": 1, "reaction_type": 1},
    ).to_list(len(activity_ids))
    reaction_map = {r["activity_id"]: r["reaction_type"] for r in user_reactions}

    result = []
    for bk in bookmarks:
        act = act_map.get(bk["activity_id"])
        if not act:
            continue  # Activity deleted or hidden since bookmark
        u = users_map.get(act["user_id"], {})
        act["user_display_name"] = u.get("display_name") or u.get("name", "")
        act["user_avatar"] = u.get("avatar_url") or u.get("picture", "")
        act["user_username"] = u.get("username", "")
        act["user_level"] = u.get("level", 1)
        act["user_reaction"] = reaction_map.get(act["activity_id"])
        act["bookmarked"] = True
        act["bookmarked_at"] = bk["created_at"]
        result.append(act)

    next_cursor = bookmarks[-1]["created_at"] if has_more else None
    return {"bookmarks": result, "next_cursor": next_cursor}
