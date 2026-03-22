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

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from typing import Optional
import uuid

from database import db
from auth import get_current_user
from models import ReactionCreate, CommentCreate
from services.activity_service import get_feed

router = APIRouter(prefix="/api")


@router.get("/feed")
async def get_activity_feed(
    user: dict = Depends(get_current_user),
    cursor: Optional[str] = None,
    limit: int = 20,
):
    """
    Get the user's activity feed.

    Cursor-based: pass `next_cursor` from previous response as `cursor`
    to get the next page. First request: omit cursor.
    """
    if limit > 50:
        limit = 50

    return await get_feed(
        user_id=user["user_id"],
        cursor=cursor,
        limit=limit,
    )


@router.get("/feed/own")
async def get_own_activities(
    user: dict = Depends(get_current_user),
    cursor: Optional[str] = None,
    limit: int = 20,
):
    """Get only the authenticated user's own activities (for profile view)."""
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


@router.get("/users/{user_id}/activities")
async def get_user_activities(
    user_id: str,
    user: dict = Depends(get_current_user),
    cursor: Optional[str] = None,
    limit: int = 20,
):
    """Get a specific user's public activities (for their profile page)."""
    # Check visibility
    target = await db.users.find_one({"user_id": user_id}, {"privacy": 1})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    privacy = target.get("privacy", {})
    if not privacy.get("profile_visible", True):
        raise HTTPException(status_code=403, detail="Profile is private")

    # Determine visibility level based on relationship
    is_following = await db.follows.find_one(
        {"follower_id": user["user_id"], "following_id": user_id, "status": "active"}
    )

    visible_levels = ["public"]
    if is_following or user_id == user["user_id"]:
        visible_levels.append("followers")

    query = {
        "user_id": user_id,
        "visibility": {"$in": visible_levels},
    }
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
    reaction: ReactionCreate,
    user: dict = Depends(get_current_user),
):
    """
    React to an activity. One reaction per user per activity.
    Reacting again with the same type removes it (toggle).
    Reacting with a different type changes it.
    """
    activity = await db.activities.find_one({"activity_id": activity_id})
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    existing = await db.reactions.find_one(
        {"activity_id": activity_id, "user_id": user["user_id"]}
    )

    now = datetime.now(timezone.utc).isoformat()

    if existing:
        if existing["reaction_type"] == reaction.reaction_type:
            # Toggle off — remove reaction
            await db.reactions.delete_one({"_id": existing["_id"]})
            await db.activities.update_one(
                {"activity_id": activity_id},
                {"$inc": {f"reaction_counts.{reaction.reaction_type}": -1}},
            )
            return {"message": "Reaction removed", "reacted": False}
        else:
            # Change reaction type
            old_type = existing["reaction_type"]
            await db.reactions.update_one(
                {"_id": existing["_id"]},
                {"$set": {"reaction_type": reaction.reaction_type, "updated_at": now}},
            )
            await db.activities.update_one(
                {"activity_id": activity_id},
                {"$inc": {
                    f"reaction_counts.{old_type}": -1,
                    f"reaction_counts.{reaction.reaction_type}": 1,
                }},
            )
            return {
                "message": "Reaction updated",
                "reacted": True,
                "reaction_type": reaction.reaction_type,
            }
    else:
        # New reaction
        await db.reactions.insert_one({
            "reaction_id": f"react_{uuid.uuid4().hex[:12]}",
            "activity_id": activity_id,
            "user_id": user["user_id"],
            "reaction_type": reaction.reaction_type,
            "created_at": now,
        })
        await db.activities.update_one(
            {"activity_id": activity_id},
            {"$inc": {f"reaction_counts.{reaction.reaction_type}": 1}},
        )

        # Notify activity owner (if not self-reacting)
        if activity["user_id"] != user["user_id"]:
            display = user.get("display_name") or user.get("name", "Quelqu'un")
            await db.notifications.insert_one({
                "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
                "user_id": activity["user_id"],
                "type": "reaction",
                "message": f"{display} a réagi à votre activité",
                "data": {
                    "activity_id": activity_id,
                    "reaction_type": reaction.reaction_type,
                    "reactor_id": user["user_id"],
                },
                "read": False,
                "created_at": now,
            })

        return {
            "message": "Reaction added",
            "reacted": True,
            "reaction_type": reaction.reaction_type,
        }


# ============== COMMENTS ==============


@router.post("/activities/{activity_id}/comments")
async def add_comment(
    activity_id: str,
    comment: CommentCreate,
    user: dict = Depends(get_current_user),
):
    """Add a comment to an activity."""
    activity = await db.activities.find_one({"activity_id": activity_id})
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    now = datetime.now(timezone.utc).isoformat()
    comment_id = f"com_{uuid.uuid4().hex[:12]}"

    comment_doc = {
        "comment_id": comment_id,
        "activity_id": activity_id,
        "user_id": user["user_id"],
        "user_name": user.get("display_name", user.get("name", "Utilisateur")),
        "user_avatar": user.get("avatar_url", user.get("picture")),
        "content": comment.content,
        "created_at": now,
    }

    await db.comments.insert_one(comment_doc)
    await db.activities.update_one(
        {"activity_id": activity_id},
        {"$inc": {"comment_count": 1}},
    )

    # Notify activity owner (if not self-commenting)
    if activity["user_id"] != user["user_id"]:
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

    comment_doc.pop("_id", None)
    return comment_doc


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
        raise HTTPException(status_code=404, detail="Activity not found")

    comments = (
        await db.comments.find(
            {"activity_id": activity_id}, {"_id": 0}
        )
        .sort("created_at", 1)  # Oldest first (chronological)
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
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment["user_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Can only delete your own comments")

    await db.comments.delete_one({"comment_id": comment_id})
    await db.activities.update_one(
        {"activity_id": comment["activity_id"]},
        {"$inc": {"comment_count": -1}},
    )

    return {"message": "Comment deleted"}
