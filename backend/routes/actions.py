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
    # Cap limit to prevent abuse (library grows daily via AI generator)
    limit = min(max(limit, 1), 10000)
    skip = max(skip, 0)

    query = {}
    if category:
        query["category"] = category
    if energy:
        query["energy_level"] = energy
    if duration:
        query["duration_min"] = {"$lte": duration}
        query["duration_max"] = {"$gte": duration}

    actions = await db.micro_actions.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)

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
