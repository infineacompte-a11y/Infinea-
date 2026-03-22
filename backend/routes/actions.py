"""
InFinea — Micro-actions routes.
Browse and retrieve micro-actions.
"""

from fastapi import APIRouter
from typing import List, Optional

from database import db
from models import MicroAction

router = APIRouter(prefix="/api")


@router.get("/actions", response_model=List[MicroAction])
async def get_actions(
    category: Optional[str] = None,
    duration: Optional[int] = None,
    energy: Optional[str] = None,
):
    query = {}
    if category:
        query["category"] = category
    if energy:
        query["energy_level"] = energy

    actions = await db.micro_actions.find(query, {"_id": 0}).to_list(100)

    if duration:
        actions = [a for a in actions if a["duration_min"] <= duration <= a["duration_max"]]

    return actions


@router.get("/actions/{action_id}")
async def get_action(action_id: str):
    action = await db.micro_actions.find_one({"action_id": action_id}, {"_id": 0})
    if not action:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Action not found")
    return action
