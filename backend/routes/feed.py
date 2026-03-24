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
from services.moderation import get_blocked_ids, check_content, sanitize_text, extract_mentions
from helpers import send_push_to_user
from services.email_service import send_email_to_user, email_mention

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


@router.get("/feed/discover")
async def get_discover_feed(
    user: dict = Depends(get_current_user),
    cursor: str = None,
    limit: int = 20,
):
    """
    Discover feed: public activities from ALL users.
    Instagram Explore equivalent — always has content, even for new users.
    """
    if limit > 50:
        limit = 50

    # Filter out blocked users from discover
    blocked_ids = await get_blocked_ids(user["user_id"])

    query = {"visibility": "public"}
    if blocked_ids:
        query["user_id"] = {"$nin": list(blocked_ids)}
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

    # Enrich with user info
    if activities:
        enriched_user_ids = list({a["user_id"] for a in activities})
        users = await db.users.find(
            {"user_id": {"$in": enriched_user_ids}},
            {"_id": 0, "user_id": 1, "name": 1, "display_name": 1,
             "username": 1, "avatar_url": 1, "picture": 1},
        ).to_list(len(enriched_user_ids))
        user_map = {u["user_id"]: u for u in users}

        for activity in activities:
            u = user_map.get(activity["user_id"], {})
            activity["user_name"] = u.get("display_name") or u.get("name", "Utilisateur")
            activity["user_username"] = u.get("username")
            activity["user_avatar"] = u.get("avatar_url") or u.get("picture")

        # Check current user's reactions
        activity_ids = [a["activity_id"] for a in activities]
        user_reactions = await db.reactions.find(
            {"activity_id": {"$in": activity_ids}, "user_id": user["user_id"]},
            {"_id": 0, "activity_id": 1, "reaction_type": 1},
        ).to_list(len(activity_ids))
        reaction_map = {r["activity_id"]: r["reaction_type"] for r in user_reactions}
        for activity in activities:
            activity["user_reaction"] = reaction_map.get(activity["activity_id"])

    next_cursor = activities[-1]["created_at"] if activities and has_more else None
    return {"activities": activities, "next_cursor": next_cursor, "has_more": has_more}


@router.get("/feed/suggested-users")
async def get_suggested_users(
    user: dict = Depends(get_current_user),
    limit: int = 15,
):
    """
    Suggest users to follow. Prioritizes users with recent activity
    and most followers. Instagram-style suggestions.
    """
    # Get who the user already follows + blocked users
    following_docs = await db.follows.find(
        {"follower_id": user["user_id"], "status": "active"},
        {"following_id": 1},
    ).to_list(1000)
    following_ids = {f["following_id"] for f in following_docs}
    following_ids.add(user["user_id"])  # exclude self

    # Also exclude blocked users from suggestions
    blocked_ids = await get_blocked_ids(user["user_id"])
    following_ids |= blocked_ids

    # Get users with recent activities (most active)
    pipeline = [
        {"$match": {"user_id": {"$nin": list(following_ids)}, "visibility": "public"}},
        {"$group": {
            "_id": "$user_id",
            "activity_count": {"$sum": 1},
            "last_active": {"$max": "$created_at"},
        }},
        {"$sort": {"activity_count": -1, "last_active": -1}},
        {"$limit": limit},
    ]
    active_users = await db.activities.aggregate(pipeline).to_list(limit)

    if not active_users:
        # Fallback: recent users who aren't followed
        users = await db.users.find(
            {"user_id": {"$nin": list(following_ids)}},
            {"_id": 0, "user_id": 1, "name": 1, "display_name": 1,
             "username": 1, "avatar_url": 1, "picture": 1, "subscription_tier": 1},
        ).sort("created_at", -1).limit(limit).to_list(limit)
    else:
        user_ids = [u["_id"] for u in active_users]
        users = await db.users.find(
            {"user_id": {"$in": user_ids}},
            {"_id": 0, "user_id": 1, "name": 1, "display_name": 1,
             "username": 1, "avatar_url": 1, "picture": 1, "subscription_tier": 1},
        ).to_list(len(user_ids))

    # Get follower counts
    result = []
    for u in users:
        fc = await db.follows.count_documents({"following_id": u["user_id"], "status": "active"})
        result.append({
            "user_id": u["user_id"],
            "display_name": u.get("display_name") or u.get("name", "Utilisateur"),
            "username": u.get("username"),
            "avatar_url": u.get("avatar_url") or u.get("picture"),
            "subscription_tier": u.get("subscription_tier", "free"),
            "followers_count": fc,
        })

    return {"users": result}


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


# ============== DELETE ACTIVITY ==============

@router.delete("/activities/{activity_id}")
async def delete_activity(activity_id: str, user: dict = Depends(get_current_user)):
    """Delete own activity and cascade-delete associated reactions and comments."""
    activity = await db.activities.find_one({"activity_id": activity_id})
    if not activity:
        raise HTTPException(status_code=404, detail="Activité introuvable")

    if activity["user_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Vous ne pouvez supprimer que vos propres activités")

    # Cascade delete: reactions + comments
    await db.reactions.delete_many({"activity_id": activity_id})
    await db.comments.delete_many({"activity_id": activity_id})
    await db.activities.delete_one({"activity_id": activity_id})

    return {"message": "Activité supprimée"}


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
                await send_push_to_user(
                    activity["user_id"],
                    "Nouvelle réaction",
                    f"{display} a réagi à ton activité",
                    url="/community",
                    tag="reaction",
                )
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
        "created_at": now,
    }

    await db.comments.insert_one(comment_doc)
    await db.activities.update_one(
        {"activity_id": activity_id},
        {"$inc": {"comment_count": 1}},
    )

    display = user.get("display_name") or user.get("name", "Quelqu'un")

    # Notify activity owner (non-blocking)
    if activity["user_id"] != user["user_id"]:
        try:
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
            await send_push_to_user(
                activity["user_id"],
                "Nouveau commentaire",
                f"{display} a commenté ton activité",
                url="/community",
                tag="comment",
            )
        except Exception:
            pass

    # Notify mentioned users (non-blocking, skip activity owner — already notified)
    for m in mentions:
        if m["user_id"] == activity["user_id"]:
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
                },
                "read": False,
                "created_at": now,
            })
            await send_push_to_user(
                m["user_id"],
                f"{display} vous a mentionné",
                content[:80],
                url="/community",
                tag="mention",
            )
            # Email for mentions
            subject, html = email_mention(display, content, "/community")
            await send_email_to_user(m["user_id"], subject, html, email_category="social")
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
        "mentions": mentions,
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

    # Filter out comments from blocked users
    blocked_ids = await get_blocked_ids(user["user_id"])
    comment_query = {"activity_id": activity_id}
    if blocked_ids:
        comment_query["user_id"] = {"$nin": list(blocked_ids)}

    comments = (
        await db.comments.find(comment_query, {"_id": 0})
        .sort("created_at", 1)
        .skip(skip)
        .limit(limit)
        .to_list(limit)
    )

    total = await db.comments.count_documents(comment_query)
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
