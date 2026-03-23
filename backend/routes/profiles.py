"""
InFinea — User Profile & Social routes.
Public profiles, user search, follow/unfollow.

Design:
- Profile data lives ON the user document (no separate collection = no joins).
- Follow relationships stored in a `follows` collection (follower_id, following_id).
- Search matches on name, display_name, and username.
- Benchmarked: Strava athlete profiles, Instagram user search.
"""

import re
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends, Query, Request

from database import db
from auth import get_current_user

router = APIRouter()


# ============== PROFILE EDITING ==============

DISPLAY_NAME_MAX = 50
BIO_MAX = 200
USERNAME_REGEX = re.compile(r"^[a-z0-9][a-z0-9._]{1,28}[a-z0-9]$")


@router.get("/profile/me")
async def get_my_profile(user: dict = Depends(get_current_user)):
    """Get own editable profile fields."""
    doc = await db.users.find_one(
        {"user_id": user["user_id"]},
        {"_id": 0, "user_id": 1, "name": 1, "display_name": 1, "username": 1,
         "bio": 1, "picture": 1, "avatar_url": 1, "email": 1},
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return {
        "user_id": doc["user_id"],
        "display_name": doc.get("display_name") or doc.get("name", ""),
        "username": doc.get("username", ""),
        "bio": doc.get("bio", ""),
        "avatar_url": doc.get("avatar_url") or doc.get("picture", ""),
    }


@router.put("/profile/me")
async def update_my_profile(
    request: Request,
    user: dict = Depends(get_current_user),
):
    """Update own profile (display_name, bio, username)."""
    body = await request.json()
    updates = {}

    # display_name
    if "display_name" in body:
        dn = str(body["display_name"]).strip()
        if not dn or len(dn) > DISPLAY_NAME_MAX:
            raise HTTPException(status_code=400, detail=f"Le nom doit faire entre 1 et {DISPLAY_NAME_MAX} caractères")
        updates["display_name"] = dn

    # bio
    if "bio" in body:
        bio = str(body["bio"]).strip()
        if len(bio) > BIO_MAX:
            raise HTTPException(status_code=400, detail=f"La bio ne doit pas dépasser {BIO_MAX} caractères")
        updates["bio"] = bio

    # username change
    if "username" in body:
        uname = str(body["username"]).strip().lower()
        if not USERNAME_REGEX.match(uname):
            raise HTTPException(
                status_code=400,
                detail="L'identifiant doit contenir 3-30 caractères (lettres minuscules, chiffres, points, underscores)",
            )
        # Check uniqueness (skip if unchanged)
        current = await db.users.find_one({"user_id": user["user_id"]}, {"username": 1})
        if current.get("username") != uname:
            existing = await db.users.find_one({"username": uname}, {"_id": 1})
            if existing:
                raise HTTPException(status_code=409, detail="Cet identifiant est déjà pris")
            updates["username"] = uname

    if not updates:
        raise HTTPException(status_code=400, detail="Aucun champ à mettre à jour")

    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": updates},
    )

    # Return fresh profile
    doc = await db.users.find_one(
        {"user_id": user["user_id"]},
        {"_id": 0, "user_id": 1, "name": 1, "display_name": 1, "username": 1,
         "bio": 1, "picture": 1, "avatar_url": 1},
    )
    return {
        "user_id": doc["user_id"],
        "display_name": doc.get("display_name") or doc.get("name", ""),
        "username": doc.get("username", ""),
        "bio": doc.get("bio", ""),
        "avatar_url": doc.get("avatar_url") or doc.get("picture", ""),
    }


# ============== PRIVACY SETTINGS ==============

PRIVACY_DEFAULTS = {
    "profile_visible": True,
    "show_stats": True,
    "show_badges": True,
    "show_reflections": False,
    "activity_default_visibility": "followers",
}


@router.get("/profile/privacy")
async def get_privacy_settings(user: dict = Depends(get_current_user)):
    """Get current privacy settings."""
    user_doc = await db.users.find_one(
        {"user_id": user["user_id"]}, {"_id": 0, "privacy": 1}
    )
    stored = user_doc.get("privacy", {}) if user_doc else {}
    return {**PRIVACY_DEFAULTS, **stored}


@router.put("/profile/privacy")
async def update_privacy_settings(
    request: Request,
    user: dict = Depends(get_current_user),
):
    """Update privacy settings."""
    request_body = await request.json()
    allowed_keys = set(PRIVACY_DEFAULTS.keys())
    update = {k: v for k, v in request_body.items() if k in allowed_keys}
    if not update:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {f"privacy.{k}": v for k, v in update.items()}},
    )
    # Return updated settings
    user_doc = await db.users.find_one(
        {"user_id": user["user_id"]}, {"_id": 0, "privacy": 1}
    )
    stored = user_doc.get("privacy", {}) if user_doc else {}
    return {**PRIVACY_DEFAULTS, **stored}


# ============== USER SEARCH ==============

@router.get("/users/search")
async def search_users(
    q: str = Query(..., min_length=2),
    user: dict = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=50),
):
    """Search users by name, display_name, username, or email local part."""
    # Strip @ prefix if user searches "@john.doe"
    search_q = q.lstrip("@")
    query = {
        "$or": [
            {"name": {"$regex": search_q, "$options": "i"}},
            {"display_name": {"$regex": search_q, "$options": "i"}},
            {"username": {"$regex": search_q, "$options": "i"}},
            {"email": {"$regex": f"^{search_q}", "$options": "i"}},
        ],
        "user_id": {"$ne": user["user_id"]},
    }

    users = await db.users.find(
        query,
        {"_id": 0, "user_id": 1, "name": 1, "display_name": 1, "username": 1,
         "avatar_url": 1, "picture": 1, "privacy": 1},
    ).limit(limit).to_list(limit)

    # Filter out private profiles
    visible = []
    for u in users:
        privacy = u.get("privacy", {})
        if privacy.get("profile_visible", True) is False:
            continue
        visible.append(u)

    # Check follow status for each result
    my_follows = set()
    if visible:
        follow_docs = await db.follows.find(
            {"follower_id": user["user_id"], "status": "active",
             "following_id": {"$in": [u["user_id"] for u in visible]}},
            {"_id": 0, "following_id": 1},
        ).to_list(limit)
        my_follows = {f["following_id"] for f in follow_docs}

    results = []
    for u in visible:
        results.append({
            "user_id": u["user_id"],
            "display_name": u.get("display_name", u.get("name", "Utilisateur")),
            "username": u.get("username"),
            "avatar_url": u.get("avatar_url") or u.get("picture"),
            "is_following": u["user_id"] in my_follows,
        })

    return {"users": results}


# ============== PUBLIC PROFILE ==============

@router.get("/users/{user_id}/profile")
async def get_user_profile(user_id: str, user: dict = Depends(get_current_user)):
    """Get a user's public profile."""
    target = await db.users.find_one(
        {"user_id": user_id}, {"_id": 0, "password_hash": 0}
    )
    if not target:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    # Privacy check
    privacy = target.get("privacy", {})
    is_self = user["user_id"] == user_id
    if not is_self and privacy.get("profile_visible", True) is False:
        raise HTTPException(status_code=403, detail="Profil privé")

    # Social counts
    followers_count = await db.follows.count_documents(
        {"following_id": user_id, "status": "active"}
    )
    following_count = await db.follows.count_documents(
        {"follower_id": user_id, "status": "active"}
    )

    # Check if current user follows this person
    is_following = False
    if not is_self:
        follow_doc = await db.follows.find_one(
            {"follower_id": user["user_id"], "following_id": user_id, "status": "active"}
        )
        is_following = follow_doc is not None

    show_stats = is_self or privacy.get("show_stats", True)
    show_badges = is_self or privacy.get("show_badges", True)

    return {
        "user_id": target["user_id"],
        "display_name": target.get("display_name", target.get("name", "Utilisateur")),
        "username": target.get("username"),
        "avatar_url": target.get("avatar_url") or target.get("picture"),
        "bio": target.get("bio"),
        "subscription_tier": target.get("subscription_tier", "free"),
        "created_at": target.get("created_at"),
        "followers_count": followers_count,
        "following_count": following_count,
        "is_following": is_following,
        "streak_days": target.get("streak_days", 0) if show_stats else None,
        "total_time_invested": target.get("total_time_invested", 0) if show_stats else None,
        "badges": target.get("badges", []) if show_badges else [],
    }


# ============== FOLLOW / UNFOLLOW ==============

@router.post("/users/{user_id}/follow")
async def follow_user(user_id: str, user: dict = Depends(get_current_user)):
    """Follow a user."""
    if user["user_id"] == user_id:
        raise HTTPException(status_code=400, detail="Impossible de se suivre soi-même")

    target = await db.users.find_one({"user_id": user_id}, {"_id": 1})
    if not target:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    existing = await db.follows.find_one(
        {"follower_id": user["user_id"], "following_id": user_id}
    )
    if existing and existing.get("status") == "active":
        raise HTTPException(status_code=400, detail="Déjà abonné")

    now = datetime.now(timezone.utc).isoformat()
    if existing:
        await db.follows.update_one(
            {"_id": existing["_id"]},
            {"$set": {"status": "active", "followed_at": now}},
        )
    else:
        await db.follows.insert_one({
            "follower_id": user["user_id"],
            "following_id": user_id,
            "status": "active",
            "followed_at": now,
        })

    return {"message": "Abonné", "is_following": True}


@router.delete("/users/{user_id}/follow")
async def unfollow_user(user_id: str, user: dict = Depends(get_current_user)):
    """Unfollow a user."""
    result = await db.follows.update_one(
        {"follower_id": user["user_id"], "following_id": user_id, "status": "active"},
        {"$set": {"status": "inactive"}},
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Pas abonné à cet utilisateur")

    return {"message": "Désabonné", "is_following": False}


# ============== FOLLOWERS / FOLLOWING LISTS ==============

@router.get("/users/{user_id}/followers")
async def get_followers(user_id: str, user: dict = Depends(get_current_user)):
    """List users who follow this user."""
    follows = await db.follows.find(
        {"following_id": user_id, "status": "active"},
        {"_id": 0, "follower_id": 1},
    ).to_list(200)

    follower_ids = [f["follower_id"] for f in follows]
    if not follower_ids:
        return {"followers": []}

    users = await db.users.find(
        {"user_id": {"$in": follower_ids}},
        {"_id": 0, "user_id": 1, "name": 1, "display_name": 1, "username": 1,
         "avatar_url": 1, "picture": 1},
    ).to_list(200)

    # Check which ones the current user follows back
    my_follows = set()
    follow_docs = await db.follows.find(
        {"follower_id": user["user_id"], "status": "active",
         "following_id": {"$in": follower_ids}},
        {"_id": 0, "following_id": 1},
    ).to_list(200)
    my_follows = {f["following_id"] for f in follow_docs}

    results = []
    for u in users:
        results.append({
            "user_id": u["user_id"],
            "display_name": u.get("display_name", u.get("name", "Utilisateur")),
            "username": u.get("username"),
            "avatar_url": u.get("avatar_url") or u.get("picture"),
            "is_following": u["user_id"] in my_follows,
        })

    return {"followers": results}


@router.get("/users/{user_id}/following")
async def get_following(user_id: str, user: dict = Depends(get_current_user)):
    """List users this user follows."""
    follows = await db.follows.find(
        {"follower_id": user_id, "status": "active"},
        {"_id": 0, "following_id": 1},
    ).to_list(200)

    following_ids = [f["following_id"] for f in follows]
    if not following_ids:
        return {"following": []}

    users = await db.users.find(
        {"user_id": {"$in": following_ids}},
        {"_id": 0, "user_id": 1, "name": 1, "display_name": 1, "username": 1,
         "avatar_url": 1, "picture": 1},
    ).to_list(200)

    # Check which ones the current user follows
    my_follows = set()
    if user["user_id"] != user_id:
        follow_docs = await db.follows.find(
            {"follower_id": user["user_id"], "status": "active",
             "following_id": {"$in": following_ids}},
            {"_id": 0, "following_id": 1},
        ).to_list(200)
        my_follows = {f["following_id"] for f in follow_docs}
    else:
        my_follows = set(following_ids)

    results = []
    for u in users:
        results.append({
            "user_id": u["user_id"],
            "display_name": u.get("display_name", u.get("name", "Utilisateur")),
            "username": u.get("username"),
            "avatar_url": u.get("avatar_url") or u.get("picture"),
            "is_following": u["user_id"] in my_follows,
        })

    return {"following": results}
