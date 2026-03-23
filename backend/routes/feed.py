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

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends, Request

from database import db
from auth import get_current_user
from services.activity_service import get_feed, REACTION_TYPES

router = APIRouter()


# ============== FEED ==============

@router.get("/feed")
async def get_activity_feed(
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


@router.get("/feed/own")
async def get_own_activities(
    user: dict = Depends(get_current_user),
    cursor: str = None,
    limit: int = 20,
):
    """Get only the authenticated user's own activities."""
    if limit > 50:
        limit = 50

    query = {"user_id": user["user_id"]}
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


# ============== REACTIONS ==============

@router.post("/activities/{activity_id}/react")
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

        # Notify activity owner (non-blocking, silent fail)
        if activity["user_id"] != user["user_id"]:
            try:
                display = user.get("display_name") or user.get("name", "Quelqu'un")
                await db.notifications.insert_one({
                    "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
                    "user_id": activity["user_id"],
                    "type": "reaction",
                    "message": f"{display} a réagi à votre activité",
                    "data": {
                        "activity_id": activity_id,
                        "reaction_type": reaction_type,
                        "reactor_id": user["user_id"],
                    },
                    "read": False,
                    "created_at": now,
                })
            except Exception:
                pass  # Non-blocking

        return {"reacted": True, "reaction_type": reaction_type}


# ============== COMMENTS ==============

@router.post("/activities/{activity_id}/comments")
async def add_comment(
    activity_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    """Add a comment to an activity."""
    body = await request.json()
    content = str(body.get("content", "")).strip()
    if not content or len(content) > 500:
        raise HTTPException(status_code=400, detail="Le commentaire doit faire entre 1 et 500 caractères")

    activity = await db.activities.find_one({"activity_id": activity_id})
    if not activity:
        raise HTTPException(status_code=404, detail="Activité introuvable")

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
        "created_at": now,
    }

    await db.comments.insert_one(comment_doc)
    await db.activities.update_one(
        {"activity_id": activity_id},
        {"$inc": {"comment_count": 1}},
    )

    # Notify activity owner (non-blocking)
    if activity["user_id"] != user["user_id"]:
        try:
            display = user.get("display_name") or user.get("name", "Quelqu'un")
            await db.notifications.insert_one({
                "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
                "user_id": activity["user_id"],
                "type": "comment",
                "message": f"{display} a commenté votre activité",
                "data": {
                    "activity_id": activity_id,
                    "comment_id": comment_id,
                    "commenter_id": user["user_id"],
                },
                "read": False,
                "created_at": now,
            })
        except Exception:
            pass

    return {
        "comment_id": comment_id,
        "activity_id": activity_id,
        "user_id": user["user_id"],
        "user_name": comment_doc["user_name"],
        "user_username": comment_doc["user_username"],
        "user_avatar": comment_doc["user_avatar"],
        "content": content,
        "created_at": now,
    }


@router.get("/activities/{activity_id}/comments")
async def get_comments(
    activity_id: str,
    user: dict = Depends(get_current_user),
    limit: int = 30,
    skip: int = 0,
):
    """Get comments on an activity."""
    activity = await db.activities.find_one({"activity_id": activity_id})
    if not activity:
        raise HTTPException(status_code=404, detail="Activité introuvable")

    comments = (
        await db.comments.find({"activity_id": activity_id}, {"_id": 0})
        .sort("created_at", 1)
        .skip(skip)
        .limit(limit)
        .to_list(limit)
    )

    total = await db.comments.count_documents({"activity_id": activity_id})
    return {"comments": comments, "total": total}


@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: str,
    user: dict = Depends(get_current_user),
):
    """Delete own comment."""
    comment = await db.comments.find_one({"comment_id": comment_id})
    if not comment:
        raise HTTPException(status_code=404, detail="Commentaire introuvable")

    if comment["user_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Vous ne pouvez supprimer que vos propres commentaires")

    await db.comments.delete_one({"comment_id": comment_id})
    await db.activities.update_one(
        {"activity_id": comment["activity_id"]},
        {"$inc": {"comment_count": -1}},
    )

    return {"message": "Commentaire supprimé"}
