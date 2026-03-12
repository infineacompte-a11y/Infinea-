"""
InFinea — Micro-actions routes.
Browse action library, custom actions, get action details.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends

from database import db
from auth import get_current_user
from models import MicroAction

router = APIRouter()


@router.get("/actions", response_model=List[MicroAction])
async def get_actions(
    category: Optional[str] = None,
    duration: Optional[int] = None,
    energy: Optional[str] = None
):
    query = {}
    if category:
        query["category"] = category
    if energy:
        query["energy_level"] = energy

    actions = await db.micro_actions.find(query, {"_id": 0}).to_list(5000)

    if duration:
        actions = [a for a in actions if a["duration_min"] <= duration <= a["duration_max"]]

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
async def get_action(action_id: str):
    action = await db.micro_actions.find_one({"action_id": action_id}, {"_id": 0})
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    return action
