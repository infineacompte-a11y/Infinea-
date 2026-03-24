"""
InFinea — User Profile & Social routes.
Public profiles, user search, follow/unfollow.

Design:
- Profile data lives ON the user document (no separate collection = no joins).
- Follow relationships stored in a `follows` collection (follower_id, following_id).
- Search matches on name, display_name, and username.
- Benchmarked: Strava athlete profiles, Instagram user search.
"""

import asyncio
import re
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends, Query, Request

from database import db
from auth import get_current_user
from helpers import send_push_to_user
from services.moderation import get_blocked_ids, check_content, sanitize_text
from services.email_service import send_email_to_user, email_new_follower

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
        dn = sanitize_text(str(body["display_name"]), max_length=DISPLAY_NAME_MAX)
        if not dn:
            raise HTTPException(status_code=400, detail=f"Le nom doit faire entre 1 et {DISPLAY_NAME_MAX} caractères")
        moderation = check_content(dn)
        if not moderation["allowed"]:
            raise HTTPException(status_code=400, detail=moderation["reason"])
        updates["display_name"] = dn

    # bio
    if "bio" in body:
        bio = sanitize_text(str(body["bio"]), max_length=BIO_MAX)
        moderation = check_content(bio)
        if not moderation["allowed"]:
            raise HTTPException(status_code=400, detail=moderation["reason"])
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

    # Exclude blocked users from search
    blocked_ids = await get_blocked_ids(user["user_id"])
    exclude_ids = list(blocked_ids | {user["user_id"]})

    query = {
        "$or": [
            {"name": {"$regex": search_q, "$options": "i"}},
            {"display_name": {"$regex": search_q, "$options": "i"}},
            {"username": {"$regex": search_q, "$options": "i"}},
            {"email": {"$regex": f"^{search_q}", "$options": "i"}},
        ],
        "user_id": {"$nin": exclude_ids},
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


# ============== MENTION AUTOCOMPLETE ==============

@router.get("/users/search-mention")
async def search_mention(
    user: dict = Depends(get_current_user),
    q: str = Query("", max_length=50),
    context: str = Query("comment"),
    context_id: str = Query(""),
    limit: int = Query(6, ge=1, le=15),
):
    """
    Context-aware mention autocomplete.
    Ranking: activity owner > mutual follows > following > followers > any user.
    Empty query returns ranked suggestions instantly.
    Benchmarked: Slack (speed), Discord (context), Twitter (simplicity).
    """
    my_id = user["user_id"]
    q_clean = q.strip().lstrip("@").lower()

    # ── Parallel queries: follows + context owner ──
    async def fetch_i_follow():
        docs = await db.follows.find(
            {"follower_id": my_id, "status": "active"},
            {"_id": 0, "following_id": 1},
        ).to_list(1000)
        return {d["following_id"] for d in docs}

    async def fetch_follow_me():
        docs = await db.follows.find(
            {"following_id": my_id, "status": "active"},
            {"_id": 0, "follower_id": 1},
        ).to_list(1000)
        return {d["follower_id"] for d in docs}

    async def fetch_context_owner():
        if context == "comment" and context_id:
            act = await db.activities.find_one(
                {"activity_id": context_id}, {"_id": 0, "user_id": 1}
            )
            return act["user_id"] if act else None
        if context == "message" and context_id:
            conv = await db.conversations.find_one(
                {"conversation_id": context_id}, {"_id": 0, "participants": 1}
            )
            if conv:
                others = [p for p in conv["participants"] if p != my_id]
                return others[0] if others else None
        return None

    i_follow_set, follow_me_set, context_owner_id = await asyncio.gather(
        fetch_i_follow(), fetch_follow_me(), fetch_context_owner()
    )
    mutual_set = i_follow_set & follow_me_set
    blocked_ids = await get_blocked_ids(my_id)
    exclude_ids = blocked_ids | {my_id}

    # ── Build candidate pool ──
    if q_clean:
        # Text search: prefix + contains on username and display_name
        regex_prefix = re.compile(f"^{re.escape(q_clean)}", re.IGNORECASE)
        regex_contains = re.compile(re.escape(q_clean), re.IGNORECASE)
        candidates = await db.users.find(
            {
                "$or": [
                    {"username": {"$regex": q_clean, "$options": "i"}},
                    {"display_name": {"$regex": q_clean, "$options": "i"}},
                    {"name": {"$regex": q_clean, "$options": "i"}},
                ],
                "user_id": {"$nin": list(exclude_ids)},
            },
            {"_id": 0, "user_id": 1, "name": 1, "display_name": 1,
             "username": 1, "avatar_url": 1, "picture": 1, "privacy": 1},
        ).limit(30).to_list(30)
    else:
        # No text filter — pull from social graph
        social_ids = list((mutual_set | i_follow_set | follow_me_set) - exclude_ids)
        if context_owner_id and context_owner_id not in exclude_ids:
            if context_owner_id not in social_ids:
                social_ids.insert(0, context_owner_id)
        social_ids = social_ids[:30]
        if not social_ids:
            return {"users": []}
        candidates = await db.users.find(
            {"user_id": {"$in": social_ids}},
            {"_id": 0, "user_id": 1, "name": 1, "display_name": 1,
             "username": 1, "avatar_url": 1, "picture": 1, "privacy": 1},
        ).to_list(len(social_ids))

    # ── Filter private profiles ──
    visible = [
        u for u in candidates
        if u.get("privacy", {}).get("profile_visible", True) is not False
    ]

    # ── Score & rank ──
    scored = []
    for u in visible:
        uid = u["user_id"]
        score = 0

        # Tier 0: context owner
        if uid == context_owner_id:
            score += 1000
        # Tier 1-3: follow relationship
        if uid in mutual_set:
            score += 300
        elif uid in i_follow_set:
            score += 200
        elif uid in follow_me_set:
            score += 100
        else:
            score += 50

        # Text match bonuses
        if q_clean:
            uname = (u.get("username") or "").lower()
            dname = (u.get("display_name") or u.get("name") or "").lower()
            if uname.startswith(q_clean):
                score += 100
            elif dname.startswith(q_clean):
                score += 80
            else:
                score += 40  # contains match (already filtered by query)

        scored.append((score, u))

    scored.sort(key=lambda x: -x[0])
    top = scored[:limit]

    # ── Format response ──
    results = []
    for _, u in top:
        uid = u["user_id"]
        results.append({
            "user_id": uid,
            "display_name": u.get("display_name") or u.get("name", "Utilisateur"),
            "username": u.get("username"),
            "avatar_url": u.get("avatar_url") or u.get("picture"),
            "is_following": uid in i_follow_set,
            "is_mutual": uid in mutual_set,
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

    # Block check: if either party blocked the other, deny access
    if not is_self:
        blocked_ids = await get_blocked_ids(user["user_id"])
        if user_id in blocked_ids:
            raise HTTPException(status_code=403, detail="Profil indisponible")

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


# ============== USER ACTIVITY TIMELINE ==============

@router.get("/users/{user_id}/activities")
async def get_user_activities(
    user_id: str,
    user: dict = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=30),
):
    """Get a user's recent public activities for their profile timeline."""
    target = await db.users.find_one({"user_id": user_id}, {"_id": 1, "privacy": 1})
    if not target:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    is_self = user["user_id"] == user_id

    # Block check
    if not is_self:
        blocked_ids = await get_blocked_ids(user["user_id"])
        if user_id in blocked_ids:
            raise HTTPException(status_code=403, detail="Profil indisponible")

    # Visibility filter: self sees all, others see public + followers (if following)
    if is_self:
        query = {"user_id": user_id}
    else:
        # Check if current user follows the target
        is_follower = await db.follows.find_one(
            {"follower_id": user["user_id"], "following_id": user_id, "status": "active"}
        )
        if is_follower:
            query = {"user_id": user_id, "visibility": {"$in": ["public", "followers"]}}
        else:
            query = {"user_id": user_id, "visibility": "public"}

    activities = (
        await db.activities.find(query, {"_id": 0})
        .sort("created_at", -1)
        .limit(limit)
        .to_list(limit)
    )

    return {"activities": activities}


# ============== FOLLOW / UNFOLLOW ==============

@router.post("/users/{user_id}/follow")
async def follow_user(user_id: str, user: dict = Depends(get_current_user)):
    """Follow a user."""
    if user["user_id"] == user_id:
        raise HTTPException(status_code=400, detail="Impossible de se suivre soi-même")

    target = await db.users.find_one({"user_id": user_id}, {"_id": 1})
    if not target:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    # Cannot follow a blocked/blocking user
    blocked_ids = await get_blocked_ids(user["user_id"])
    if user_id in blocked_ids:
        raise HTTPException(status_code=403, detail="Action impossible")

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

    # Notify the followed user (non-blocking, silent fail)
    try:
        display = user.get("display_name") or user.get("name", "Quelqu'un")
        await db.notifications.insert_one({
            "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
            "user_id": user_id,
            "type": "new_follower",
            "message": f"{display} a commencé à te suivre",
            "data": {
                "follower_id": user["user_id"],
                "follower_name": display,
            },
            "read": False,
            "created_at": now,
        })
        await send_push_to_user(
            user_id,
            "Nouveau follower",
            f"{display} te suit maintenant",
            url=f"/users/{user['user_id']}",
            tag="new_follower",
        )
        # Email notification
        subject, html = email_new_follower(display, f"/users/{user['user_id']}")
        await send_email_to_user(user_id, subject, html, email_category="social")
    except Exception:
        pass

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

    # Check which ones follow the current user back (for "te suit" indicator)
    follows_me = set()
    if user["user_id"] == user_id:
        # Viewing own followers — they all follow me by definition
        follows_me = set(follower_ids)
    else:
        follows_me_docs = await db.follows.find(
            {"following_id": user["user_id"], "status": "active",
             "follower_id": {"$in": follower_ids}},
            {"_id": 0, "follower_id": 1},
        ).to_list(200)
        follows_me = {f["follower_id"] for f in follows_me_docs}

    results = []
    for u in users:
        results.append({
            "user_id": u["user_id"],
            "display_name": u.get("display_name", u.get("name", "Utilisateur")),
            "username": u.get("username"),
            "avatar_url": u.get("avatar_url") or u.get("picture"),
            "is_following": u["user_id"] in my_follows,
            "follows_back": u["user_id"] in follows_me,
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

    # Check which ones follow the profile owner back
    follows_back_docs = await db.follows.find(
        {"follower_id": {"$in": following_ids}, "following_id": user_id, "status": "active"},
        {"_id": 0, "follower_id": 1},
    ).to_list(200)
    follows_back_set = {f["follower_id"] for f in follows_back_docs}

    results = []
    for u in users:
        results.append({
            "user_id": u["user_id"],
            "display_name": u.get("display_name", u.get("name", "Utilisateur")),
            "username": u.get("username"),
            "avatar_url": u.get("avatar_url") or u.get("picture"),
            "is_following": u["user_id"] in my_follows,
            "follows_back": u["user_id"] in follows_back_set,
        })

    return {"following": results}
