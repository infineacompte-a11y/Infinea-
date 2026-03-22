"""
InFinea — Social graph routes.
Follow/unfollow, followers & following lists, blocking.

Design:
- Asymmetric follow model (like Instagram/Strava) — no approval needed.
- Blocking prevents follow and hides from search/feed.
- Notifications emitted on new follow.
- Benchmarked: Strava's follow system, Instagram's social graph.
"""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
import uuid

from database import db
from auth import get_current_user

router = APIRouter(prefix="/api")


@router.post("/users/{user_id}/follow")
async def follow_user(
    user_id: str,
    user: dict = Depends(get_current_user),
):
    """Follow a user. Idempotent — following again is a no-op."""
    if user_id == user["user_id"]:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")

    # Check target exists
    target = await db.users.find_one({"user_id": user_id})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if blocked
    block = await db.blocks.find_one(
        {"blocker_id": user_id, "blocked_id": user["user_id"]}
    )
    if block:
        raise HTTPException(status_code=403, detail="Unable to follow this user")

    # Upsert follow (idempotent)
    existing = await db.follows.find_one(
        {"follower_id": user["user_id"], "following_id": user_id}
    )

    if existing and existing.get("status") == "active":
        return {"message": "Already following", "following": True}

    now = datetime.now(timezone.utc).isoformat()

    if existing:
        # Reactivate (was unfollowed before)
        await db.follows.update_one(
            {"_id": existing["_id"]},
            {"$set": {"status": "active", "updated_at": now}},
        )
    else:
        await db.follows.insert_one({
            "follow_id": f"fol_{uuid.uuid4().hex[:12]}",
            "follower_id": user["user_id"],
            "following_id": user_id,
            "status": "active",
            "created_at": now,
        })

    # Emit notification for the followed user
    display = user.get("display_name") or user.get("name", "Quelqu'un")
    await db.notifications.insert_one({
        "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
        "user_id": user_id,
        "type": "new_follower",
        "message": f"{display} vous suit maintenant",
        "data": {"follower_id": user["user_id"]},
        "read": False,
        "created_at": now,
    })

    return {"message": "Following", "following": True}


@router.delete("/users/{user_id}/follow")
async def unfollow_user(
    user_id: str,
    user: dict = Depends(get_current_user),
):
    """Unfollow a user."""
    result = await db.follows.update_one(
        {"follower_id": user["user_id"], "following_id": user_id, "status": "active"},
        {"$set": {"status": "inactive", "updated_at": datetime.now(timezone.utc).isoformat()}},
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Not following this user")

    return {"message": "Unfollowed", "following": False}


@router.get("/users/{user_id}/followers")
async def get_followers(
    user_id: str,
    user: dict = Depends(get_current_user),
    limit: int = 50,
    skip: int = 0,
):
    """Get a user's followers list."""
    follows = (
        await db.follows.find(
            {"following_id": user_id, "status": "active"},
            {"_id": 0, "follower_id": 1},
        )
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
        .to_list(limit)
    )

    follower_ids = [f["follower_id"] for f in follows]

    # Batch fetch user info
    users = await db.users.find(
        {"user_id": {"$in": follower_ids}},
        {"_id": 0, "user_id": 1, "name": 1, "display_name": 1, "avatar_url": 1, "picture": 1},
    ).to_list(len(follower_ids))

    user_map = {u["user_id"]: u for u in users}

    # Check which followers the requesting user is following back
    my_following = set()
    if follower_ids:
        my_follows = await db.follows.find(
            {"follower_id": user["user_id"], "following_id": {"$in": follower_ids}, "status": "active"},
            {"following_id": 1},
        ).to_list(len(follower_ids))
        my_following = {f["following_id"] for f in my_follows}

    total = await db.follows.count_documents(
        {"following_id": user_id, "status": "active"}
    )

    results = []
    for fid in follower_ids:
        u = user_map.get(fid, {})
        results.append({
            "user_id": fid,
            "display_name": u.get("display_name", u.get("name", "Utilisateur")),
            "avatar_url": u.get("avatar_url", u.get("picture")),
            "is_following": fid in my_following,
        })

    return {"followers": results, "total": total}


@router.get("/users/{user_id}/following")
async def get_following(
    user_id: str,
    user: dict = Depends(get_current_user),
    limit: int = 50,
    skip: int = 0,
):
    """Get who a user is following."""
    follows = (
        await db.follows.find(
            {"follower_id": user_id, "status": "active"},
            {"_id": 0, "following_id": 1},
        )
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
        .to_list(limit)
    )

    following_ids = [f["following_id"] for f in follows]

    users = await db.users.find(
        {"user_id": {"$in": following_ids}},
        {"_id": 0, "user_id": 1, "name": 1, "display_name": 1, "avatar_url": 1, "picture": 1},
    ).to_list(len(following_ids))

    user_map = {u["user_id"]: u for u in users}

    # Check which of these users follow back
    followers_back = set()
    if following_ids:
        back_follows = await db.follows.find(
            {"follower_id": {"$in": following_ids}, "following_id": user_id, "status": "active"},
            {"follower_id": 1},
        ).to_list(len(following_ids))
        followers_back = {f["follower_id"] for f in back_follows}

    total = await db.follows.count_documents(
        {"follower_id": user_id, "status": "active"}
    )

    results = []
    for fid in following_ids:
        u = user_map.get(fid, {})
        results.append({
            "user_id": fid,
            "display_name": u.get("display_name", u.get("name", "Utilisateur")),
            "avatar_url": u.get("avatar_url", u.get("picture")),
            "follows_back": fid in followers_back,
        })

    return {"following": results, "total": total}


@router.post("/users/{user_id}/block")
async def block_user(
    user_id: str,
    user: dict = Depends(get_current_user),
):
    """Block a user — removes mutual follows and prevents future interactions."""
    if user_id == user["user_id"]:
        raise HTTPException(status_code=400, detail="Cannot block yourself")

    target = await db.users.find_one({"user_id": user_id})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    now = datetime.now(timezone.utc).isoformat()

    # Upsert block
    await db.blocks.update_one(
        {"blocker_id": user["user_id"], "blocked_id": user_id},
        {"$set": {
            "blocker_id": user["user_id"],
            "blocked_id": user_id,
            "created_at": now,
        }},
        upsert=True,
    )

    # Remove both directions of follow
    await db.follows.update_many(
        {"$or": [
            {"follower_id": user["user_id"], "following_id": user_id},
            {"follower_id": user_id, "following_id": user["user_id"]},
        ]},
        {"$set": {"status": "inactive", "updated_at": now}},
    )

    return {"message": "User blocked"}


@router.delete("/users/{user_id}/block")
async def unblock_user(
    user_id: str,
    user: dict = Depends(get_current_user),
):
    """Unblock a user."""
    result = await db.blocks.delete_one(
        {"blocker_id": user["user_id"], "blocked_id": user_id}
    )

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not blocked")

    return {"message": "User unblocked"}
