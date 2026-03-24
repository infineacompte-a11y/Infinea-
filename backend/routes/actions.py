"""
InFinea — Micro-actions routes.
Browse action library, custom actions, get action details.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Request

from database import db
from auth import get_current_user
from models import MicroAction
from config import limiter
from services.cache import cache_get, cache_set, TTL_RANKED_ACTIONS

router = APIRouter()


@router.get("/actions", response_model=List[MicroAction])
@limiter.limit("30/minute")
async def get_actions(
    request: Request,
    category: Optional[str] = None,
    duration: Optional[int] = None,
    energy: Optional[str] = None,
    skip: int = 0,
    limit: int = 50
):
    limit = min(max(limit, 1), 500)
    skip = max(skip, 0)

    query = {}
    if category:
        query["category"] = category
    if energy:
        query["energy_level"] = energy
    if duration:
        query["duration_min"] = {"$lte": duration}
        query["duration_max"] = {"$gte": duration}

    # Redis cache for simple category-only queries (most common path)
    cache_key = None
    if category and not energy and not duration and skip == 0 and limit >= 200:
        cache_key = f"actions:cat:{category}:{limit}"
        cached = await cache_get(cache_key)
        if cached is not None:
            return cached

    actions = await db.micro_actions.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)

    if cache_key:
        await cache_set(cache_key, actions, ttl=TTL_RANKED_ACTIONS)

    return actions

@router.get("/actions/custom")
async def get_custom_actions(user: dict = Depends(get_current_user)):
    """Get user's custom AI-generated actions"""
    actions = await db.user_custom_actions.find(
        {"created_by": user["user_id"]},
        {"_id": 0}
    ).to_list(50)
    return actions

@router.get("/actions/{action_id}")
@limiter.limit("60/minute")
async def get_action(request: Request, action_id: str):
    action = await db.micro_actions.find_one({"action_id": action_id}, {"_id": 0})
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    return action
