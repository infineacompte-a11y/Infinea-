"""InFinea — Hashtag routes.

Trending, feed by tag, and autocomplete endpoints.

Benchmarks:
- Instagram: /explore/tags/{tag} — top + recent feed
- Twitter/X: /trending — velocity-based trending
- LinkedIn: /feed/hashtag/{tag} — hashtag feed
"""

from fastapi import APIRouter, Depends

from auth import get_current_user
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
    return await get_hashtag_feed(
        tag=tag.lower(),
        viewer_id=user["user_id"],
        cursor=cursor or None,
        limit=limit,
    )
