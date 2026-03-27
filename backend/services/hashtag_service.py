"""InFinea — Hashtag Service.

Extraction, normalization, trending computation, feed filtering,
and autocomplete for the hashtag system.

Benchmarks:
- Instagram: hashtag pages, top/recent split, follow-a-tag
- Twitter/X: trending topics, velocity-based ranking (breadth > depth)
- LinkedIn: hashtag suggestions, contextual follow
- DEV.to: curated + community tags
- Stack Overflow: tag taxonomy, synonyms, normalization

Architecture:
- Hashtags stored as normalized lowercase array on activity docs (denormalized)
- hashtag_stats collection for fast autocomplete + aggregate counts
- Trending via aggregation pipeline (unique_users × 3 + uses — breadth wins)
- Auto-tagging for system activities (session → category, badge → badge name)
- Explicit extraction for manual posts (#tag regex, Unicode-aware)
"""

import re
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from database import db

logger = logging.getLogger(__name__)

# ── Regex: captures #tag with full Unicode support (French accents) ──
# Min 2 chars, max 30 chars. Supports à, é, è, ê, ç, ô, ù, ü, etc.
HASHTAG_RE = re.compile(r'#([\w\u00C0-\u024F]{2,30})', re.UNICODE)

# Max hashtags per activity (anti-spam)
MAX_HASHTAGS_PER_ACTIVITY = 10

# Category → canonical hashtag mapping (matches backend CATEGORY_META)
CATEGORY_TAG_MAP = {
    "learning": "apprentissage",
    "productivity": "productivité",
    "well_being": "bienêtre",
}


def extract_hashtags(content: str) -> List[str]:
    """Extract and normalize hashtags from text content.

    - Case-insensitive normalization (lowercase)
    - Preserves accented characters (é ≠ e in French)
    - Deduplicates, preserves first-seen order
    - Caps at MAX_HASHTAGS_PER_ACTIVITY

    Examples:
        "#Apprentissage et #productivité" → ["apprentissage", "productivité"]
        "#Go #go #GO" → ["go"]
    """
    if not content:
        return []

    matches = HASHTAG_RE.findall(content)
    seen = set()
    tags = []
    for raw_tag in matches:
        normalized = raw_tag.lower()
        if normalized not in seen and len(normalized) >= 2:
            seen.add(normalized)
            tags.append(normalized)

    return tags[:MAX_HASHTAGS_PER_ACTIVITY]


def generate_auto_tags(activity_type: str, data: dict) -> List[str]:
    """Generate automatic hashtags for system-generated activities.

    Maps activity metadata to relevant tags so system content
    is discoverable via the hashtag system without user effort.

    - session_completed → category tag + cleaned action title
    - badge_earned → #badge + badge name
    - streak_milestone → #streak (+ #régularité if ≥30 days)
    - challenge_completed → #défi
    """
    tags = []

    if activity_type == "session_completed":
        # Category → canonical tag
        category = data.get("category", "")
        if category in CATEGORY_TAG_MAP:
            tags.append(CATEGORY_TAG_MAP[category])

        # Action title → clean tag (if short and usable)
        title = data.get("action_title", "")
        if title and 3 <= len(title) <= 25:
            clean = re.sub(r'[^\w\u00C0-\u024F]', '', title.lower())
            if len(clean) >= 3 and clean not in tags:
                tags.append(clean)

    elif activity_type == "badge_earned":
        tags.append("badge")
        badge_name = data.get("badge_name", "")
        if badge_name:
            clean = re.sub(r'[^\w\u00C0-\u024F]', '', badge_name.lower())
            if len(clean) >= 3 and clean not in tags:
                tags.append(clean)

    elif activity_type == "streak_milestone":
        tags.append("streak")
        days = data.get("streak_days", 0)
        if days >= 30:
            tags.append("régularité")

    elif activity_type == "challenge_completed":
        tags.append("défi")

    return tags[:MAX_HASHTAGS_PER_ACTIVITY]


async def update_hashtag_stats(hashtags: List[str], increment: int = 1):
    """Update hashtag_stats collection (upsert pattern).

    Called on activity create (increment=1) and delete (increment=-1).
    Non-blocking, fail-safe — never blocks the caller.
    """
    if not hashtags:
        return

    now = datetime.now(timezone.utc).isoformat()

    for tag in hashtags:
        try:
            update = {
                "$inc": {"use_count": increment},
                "$setOnInsert": {"tag": tag, "created_at": now},
            }
            if increment > 0:
                update["$set"] = {"last_used_at": now}

            await db.hashtag_stats.update_one(
                {"tag": tag},
                update,
                upsert=True,
            )
        except Exception as e:
            logger.warning(f"Failed to update hashtag stats for #{tag}: {e}")


async def get_trending_hashtags(limit: int = 15) -> List[dict]:
    """Get trending hashtags for the current week.

    Trending algorithm (Twitter/X-inspired, adapted for InFinea scale):

    Score = unique_users × 3 + total_uses × 1

    Why breadth > depth:
    - 15 people using #productivité once each (score = 15×3 + 15 = 60)
      ranks higher than
    - 1 person using #monjournal 15 times (score = 1×3 + 15 = 18)

    This surfaces genuinely trending topics, not prolific individuals.

    Returns: [{tag, use_count, user_count, score}]
    """
    now = datetime.now(timezone.utc)
    week_ago = (now - timedelta(days=7)).isoformat()

    pipeline = [
        {
            "$match": {
                "created_at": {"$gte": week_ago},
                "hashtags": {"$exists": True, "$ne": []},
                "moderation_status": {"$ne": "hidden"},
                "deleted": {"$ne": True},
            }
        },
        {"$unwind": "$hashtags"},
        {
            "$group": {
                "_id": "$hashtags",
                "use_count": {"$sum": 1},
                "unique_users": {"$addToSet": "$user_id"},
            }
        },
        {
            "$project": {
                "tag": "$_id",
                "use_count": 1,
                "user_count": {"$size": "$unique_users"},
                "score": {
                    "$add": [
                        {"$multiply": [{"$size": "$unique_users"}, 3]},
                        "$use_count",
                    ]
                },
                "_id": 0,
            }
        },
        {"$sort": {"score": -1}},
        {"$limit": limit},
    ]

    return await db.activities.aggregate(pipeline).to_list(limit)


async def get_hashtag_feed(
    tag: str,
    viewer_id: str,
    cursor: Optional[str] = None,
    limit: int = 20,
) -> dict:
    """Get activities tagged with a specific hashtag.

    Cursor-paginated, enriched with user info, reactions, bookmarks.
    Respects block list and moderation status.
    Pattern: Instagram hashtag page (recent tab).
    """
    from services.moderation import get_blocked_ids

    blocked_ids = await get_blocked_ids(viewer_id)
    normalized = tag.lower()

    query = {
        "hashtags": normalized,
        "visibility": "public",
        "moderation_status": {"$ne": "hidden"},
        "deleted": {"$ne": True},
    }
    if blocked_ids:
        query["user_id"] = {"$nin": list(blocked_ids)}
    if cursor:
        query["created_at"] = {"$lt": cursor}

    activities = await db.activities.find(
        query, {"_id": 0}
    ).sort("created_at", -1).limit(limit + 1).to_list(limit + 1)

    has_more = len(activities) > limit
    activities = activities[:limit]

    if not activities:
        stats = await db.hashtag_stats.find_one({"tag": normalized}, {"_id": 0})
        return {
            "tag": normalized,
            "activities": [],
            "total_uses": stats.get("use_count", 0) if stats else 0,
            "next_cursor": None,
            "has_more": False,
        }

    # ── Enrich with user info ──
    user_ids = list({a["user_id"] for a in activities})
    users_cursor = db.users.find(
        {"user_id": {"$in": user_ids}},
        {"_id": 0, "user_id": 1, "display_name": 1, "name": 1,
         "username": 1, "avatar_url": 1, "picture": 1},
    )
    users_map = {u["user_id"]: u async for u in users_cursor}

    # ── Reactions + bookmarks for viewer ──
    activity_ids = [a["activity_id"] for a in activities]

    user_reactions = await db.reactions.find(
        {"user_id": viewer_id, "activity_id": {"$in": activity_ids}},
        {"_id": 0, "activity_id": 1, "reaction_type": 1},
    ).to_list(len(activity_ids))
    reaction_map = {r["activity_id"]: r["reaction_type"] for r in user_reactions}

    user_bookmarks = await db.bookmarks.find(
        {"user_id": viewer_id, "activity_id": {"$in": activity_ids}},
        {"_id": 0, "activity_id": 1},
    ).to_list(len(activity_ids))
    bookmark_set = {b["activity_id"] for b in user_bookmarks}

    for a in activities:
        u = users_map.get(a["user_id"], {})
        a["user_name"] = u.get("display_name") or u.get("name", "Utilisateur")
        a["user_username"] = u.get("username")
        a["user_avatar"] = u.get("avatar_url") or u.get("picture")
        a["user_reaction"] = reaction_map.get(a["activity_id"])
        a["bookmarked"] = a["activity_id"] in bookmark_set

    stats = await db.hashtag_stats.find_one({"tag": normalized}, {"_id": 0})
    next_cursor = activities[-1]["created_at"] if has_more else None

    return {
        "tag": normalized,
        "activities": activities,
        "total_uses": stats.get("use_count", 0) if stats else len(activities),
        "next_cursor": next_cursor,
        "has_more": has_more,
    }


async def autocomplete_hashtags(query: str, limit: int = 8) -> List[dict]:
    """Prefix search on hashtag_stats for autocomplete.

    Empty query returns most popular tags (for suggestion chips).
    Otherwise prefix-match, sorted by popularity.
    """
    filter_query = {"use_count": {"$gt": 0}}

    if query and len(query) >= 1:
        normalized = query.lower()
        filter_query["tag"] = {
            "$regex": f"^{re.escape(normalized)}",
            "$options": "i",
        }

    results = await db.hashtag_stats.find(
        filter_query,
        {"_id": 0, "tag": 1, "use_count": 1},
    ).sort("use_count", -1).limit(limit).to_list(limit)

    return results
