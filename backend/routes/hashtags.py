"""InFinea — Hashtag routes.

Trending, feed by tag, autocomplete, and follow/unfollow endpoints.

Benchmarks:
- Instagram: /explore/tags/{tag} — top + recent feed, follow hashtag
- Twitter/X: /trending — velocity-based trending
- LinkedIn: /feed/hashtag/{tag} — hashtag feed + follow
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from auth import get_current_user
from database import db
from services.hashtag_service import (
    get_trending_hashtags,
    get_hashtag_feed,
    autocomplete_hashtags,
)

router = APIRouter()


@router.get("/hashtags/trending")
async def trending_hashtags(
    user: dict = Depends(get_current_user),
    limit: int = 15,
):
    """Top trending hashtags this week.

    Scored by: unique_users × 3 + total_uses × 1.
    Breadth (many users) weighted higher than depth (many posts by few users).
    """
    limit = min(max(limit, 1), 30)
    trending = await get_trending_hashtags(limit=limit)
    return {"trending": trending}


@router.get("/hashtags/autocomplete")
async def hashtag_autocomplete(
    q: str = "",
    user: dict = Depends(get_current_user),
    limit: int = 8,
):
    """Autocomplete hashtag search for post composer.

    Empty query returns most popular tags.
    Prefix match, sorted by popularity.
    """
    limit = min(max(limit, 1), 20)
    results = await autocomplete_hashtags(query=q, limit=limit)
    return {"suggestions": results}


@router.get("/hashtags/{tag}/feed")
async def hashtag_feed(
    tag: str,
    user: dict = Depends(get_current_user),
    cursor: str = "",
    limit: int = 20,
):
    """Feed of activities tagged with a specific hashtag.

    Cursor-paginated, enriched with user info, reactions, bookmarks.
    Respects block list and moderation.
    Instagram pattern: hashtag → feed page.
    """
    limit = min(max(limit, 1), 50)
    result = await get_hashtag_feed(
        tag=tag.lower(),
        viewer_id=user["user_id"],
        cursor=cursor or None,
        limit=limit,
    )
    # Add follow status for the viewer
    followed = await db.followed_hashtags.find_one(
        {"user_id": user["user_id"], "tag": tag.lower()}, {"_id": 1}
    )
    result["following"] = bool(followed)
    return result


@router.post("/hashtags/{tag}/follow")
async def toggle_follow_hashtag(
    tag: str,
    user: dict = Depends(get_current_user),
):
    """Toggle follow on a hashtag (Instagram/LinkedIn pattern).

    Following a hashtag injects its content into your main feed.
    Cap at 30 followed hashtags to prevent feed noise.
    """
    tag = tag.lower().strip()
    if len(tag) < 2 or len(tag) > 30:
        return {"error": "Tag invalide", "followed": False}

    my_id = user["user_id"]
    existing = await db.followed_hashtags.find_one(
        {"user_id": my_id, "tag": tag}, {"_id": 1}
    )

    if existing:
        await db.followed_hashtags.delete_one({"_id": existing["_id"]})
        return {"followed": False, "tag": tag}

    # Cap at 30 followed hashtags
    count = await db.followed_hashtags.count_documents({"user_id": my_id})
    if count >= 30:
        return {"error": "Limite de 30 hashtags suivis atteinte", "followed": False}

    await db.followed_hashtags.insert_one({
        "user_id": my_id,
        "tag": tag,
        "followed_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"followed": True, "tag": tag}


@router.get("/hashtags/followed")
async def get_followed_hashtags(
    user: dict = Depends(get_current_user),
):
    """List hashtags the current user follows.

    Returns followed tags with their stats (use_count) for display.
    """
    my_id = user["user_id"]
    follows = await db.followed_hashtags.find(
        {"user_id": my_id}, {"_id": 0, "tag": 1, "followed_at": 1}
    ).sort("followed_at", -1).to_list(30)

    # Enrich with stats
    if follows:
        tags = [f["tag"] for f in follows]
        stats = await db.hashtag_stats.find(
            {"tag": {"$in": tags}}, {"_id": 0, "tag": 1, "use_count": 1}
        ).to_list(len(tags))
        stats_map = {s["tag"]: s.get("use_count", 0) for s in stats}
        for f in follows:
            f["use_count"] = stats_map.get(f["tag"], 0)

    return {"followed_hashtags": follows}
