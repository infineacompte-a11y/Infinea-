"""
InFinea — User Profile & Social routes.
Public profiles, user search, follow/unfollow.

Design:
- Profile data lives ON the user document (no separate collection = no joins).
- Follow relationships stored in a `follows` collection (follower_id, following_id).
- Search matches on name, display_name, and username (email excluded for privacy).
- Benchmarked: Strava athlete profiles, Instagram user search.
"""

import asyncio
import logging
import os
import re
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends, Query, Request, UploadFile, File

from database import db
from auth import get_current_user
from helpers import send_push_to_user, create_notification_deduped
from services.moderation import get_blocked_ids, check_content, sanitize_text
from services.email_service import send_email_to_user, email_new_follower
from services.presence_service import get_presence_batch
from config import limiter

logger = logging.getLogger(__name__)

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


@router.get("/profile/xp")
async def get_my_xp(user: dict = Depends(get_current_user)):
    """Get current user's XP progression (level, XP, progress bar data)."""
    from services.xp_engine import xp_progress_in_level

    doc = await db.users.find_one(
        {"user_id": user["user_id"]},
        {"_id": 0, "total_xp": 1, "level": 1},
    )
    total_xp = (doc or {}).get("total_xp", 0)
    return xp_progress_in_level(total_xp)


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


# ============== AVATAR UPLOAD ==============

AVATAR_MAX_SIZE = 5 * 1024 * 1024  # 5 MB
AVATAR_ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
CLOUDINARY_URL = os.getenv("CLOUDINARY_URL", "")


@router.post("/profile/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """Upload or replace profile avatar via Cloudinary.

    Accepts JPEG, PNG, or WebP up to 5 MB. Cloudinary auto-crops to face,
    resizes to 400x400, and serves optimized WebP via CDN.

    Benchmarked: Instagram (face-aware crop), LinkedIn (square crop + CDN).
    """
    if not CLOUDINARY_URL:
        raise HTTPException(
            status_code=503,
            detail="Service d'upload non configuré (CLOUDINARY_URL manquant)",
        )

    # Validate content type
    if file.content_type not in AVATAR_ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Format non supporté. Utilisez JPEG, PNG ou WebP.",
        )

    # Read and validate size
    contents = await file.read()
    if len(contents) > AVATAR_MAX_SIZE:
        raise HTTPException(
            status_code=400,
            detail="L'image ne doit pas dépasser 5 Mo",
        )

    if len(contents) < 1024:
        raise HTTPException(
            status_code=400,
            detail="Fichier trop petit ou corrompu",
        )

    # Upload to Cloudinary (run in thread — SDK is synchronous)
    try:
        import cloudinary
        import cloudinary.uploader

        # cloudinary auto-configures from CLOUDINARY_URL env var
        result = await asyncio.to_thread(
            cloudinary.uploader.upload,
            contents,
            folder="infinea/avatars",
            public_id=f"user_{user['user_id']}",
            overwrite=True,
            transformation=[
                {
                    "width": 400,
                    "height": 400,
                    "crop": "fill",
                    "gravity": "face",
                    "quality": "auto",
                    "fetch_format": "auto",
                },
            ],
            resource_type="image",
        )
        avatar_url = result["secure_url"]
    except Exception as e:
        logger.exception(f"Cloudinary upload failed for {user['user_id']}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de l'upload de l'image",
        )

    # Update user document
    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {
            "avatar_url": avatar_url,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }},
    )

    logger.info(f"Avatar updated for {user['user_id']}: {avatar_url[:60]}...")
    return {"avatar_url": avatar_url}


# ============== COVER PHOTO UPLOAD ==============

COVER_MAX_SIZE = 10 * 1024 * 1024  # 10 MB (larger than avatar — banner image)
COVER_ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}


@router.post("/profile/cover-photo")
async def upload_cover_photo(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """Upload or replace profile cover photo via Cloudinary.

    Accepts JPEG, PNG, or WebP up to 10 MB. Cloudinary auto-resizes to
    1500x500 (3:1 ratio, LinkedIn/Twitter benchmark) with quality optimization.
    """
    if not CLOUDINARY_URL:
        raise HTTPException(
            status_code=503,
            detail="Service d'upload non configuré (CLOUDINARY_URL manquant)",
        )

    if file.content_type not in COVER_ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Format non supporté. Utilisez JPEG, PNG ou WebP.",
        )

    contents = await file.read()
    if len(contents) > COVER_MAX_SIZE:
        raise HTTPException(
            status_code=400,
            detail="L'image ne doit pas dépasser 10 Mo",
        )

    if len(contents) < 1024:
        raise HTTPException(
            status_code=400,
            detail="Fichier trop petit ou corrompu",
        )

    try:
        import cloudinary
        import cloudinary.uploader

        result = await asyncio.to_thread(
            cloudinary.uploader.upload,
            contents,
            folder="infinea/covers",
            public_id=f"cover_{user['user_id']}",
            overwrite=True,
            transformation=[
                {
                    "width": 1500,
                    "height": 500,
                    "crop": "fill",
                    "gravity": "auto",
                    "quality": "auto",
                    "fetch_format": "auto",
                },
            ],
            resource_type="image",
        )
        cover_url = result["secure_url"]
    except Exception as e:
        logger.exception(f"Cloudinary cover upload failed for {user['user_id']}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de l'upload de l'image",
        )

    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {
            "cover_photo_url": cover_url,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }},
    )

    logger.info(f"Cover photo updated for {user['user_id']}: {cover_url[:60]}...")
    return {"cover_photo_url": cover_url}


@router.delete("/profile/cover-photo")
async def delete_cover_photo(user: dict = Depends(get_current_user)):
    """Remove profile cover photo."""
    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$unset": {"cover_photo_url": ""}, "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    return {"message": "Photo de couverture supprimée"}


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
@limiter.limit("30/minute")
async def search_users(
    request: Request,
    q: str = Query(..., min_length=2),
    user: dict = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=50),
):
    """Search users by name, display_name, or username.

    Uses MongoDB $text index (French stemming) for quality full-text search.
    Falls back to $regex for short queries or exact username lookup.
    """
    # Strip @ prefix if user searches "@john.doe"
    search_q = q.lstrip("@")

    # Exclude blocked users from search
    blocked_ids = await get_blocked_ids(user["user_id"])
    exclude_ids = list(blocked_ids | {user["user_id"]})

    projection = {
        "_id": 0, "user_id": 1, "name": 1, "display_name": 1, "username": 1,
        "avatar_url": 1, "picture": 1, "privacy": 1,
    }

    # Strategy: try $text index first (better ranking, handles French stemming)
    # Fall back to $regex for very short queries or if text search returns nothing
    users = []
    if len(search_q) >= 3:
        try:
            text_query = {
                "$text": {"$search": search_q},
                "user_id": {"$nin": exclude_ids},
            }
            text_proj = {**projection, "score": {"$meta": "textScore"}}
            users = await db.users.find(text_query, text_proj).sort(
                [("score", {"$meta": "textScore"})]
            ).limit(limit).to_list(limit)
        except Exception:
            pass  # Text index may not exist — fall back to regex

    # Fallback: $regex prefix match (for short queries or empty text results)
    if not users:
        regex_q = re.escape(search_q)
        query = {
            "$or": [
                {"name": {"$regex": regex_q, "$options": "i"}},
                {"display_name": {"$regex": regex_q, "$options": "i"}},
                {"username": {"$regex": regex_q, "$options": "i"}},
            ],
            "user_id": {"$nin": exclude_ids},
        }
        users = await db.users.find(query, projection).limit(limit).to_list(limit)

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

    # Check follow relationship (bidirectional for mutual detection)
    is_following = False
    follows_you = False
    if not is_self:
        i_follow, they_follow = await asyncio.gather(
            db.follows.find_one(
                {"follower_id": user["user_id"], "following_id": user_id, "status": "active"}
            ),
            db.follows.find_one(
                {"follower_id": user_id, "following_id": user["user_id"], "status": "active"}
            ),
        )
        is_following = i_follow is not None
        follows_you = they_follow is not None

    show_stats = is_self or privacy.get("show_stats", True)
    show_badges = is_self or privacy.get("show_badges", True)

    # ── Mutual followers (Instagram "X abonnés en commun") ──
    mutual_followers = {"count": 0, "sample": []}
    if not is_self:
        try:
            # Who does current user follow?
            my_following_docs = await db.follows.find(
                {"follower_id": user["user_id"], "status": "active"},
                {"_id": 0, "following_id": 1},
            ).to_list(500)
            my_following_ids = {d["following_id"] for d in my_following_docs}

            # Who follows the target?
            target_follower_docs = await db.follows.find(
                {"following_id": user_id, "status": "active"},
                {"_id": 0, "follower_id": 1},
            ).to_list(500)
            target_follower_ids = {d["follower_id"] for d in target_follower_docs}

            # Intersection = people I follow who also follow this user
            mutual_ids = list((my_following_ids & target_follower_ids) - {user["user_id"]})
            mutual_followers["count"] = len(mutual_ids)

            # Sample up to 3 names for display
            if mutual_ids:
                sample_ids = mutual_ids[:3]
                sample_users = await db.users.find(
                    {"user_id": {"$in": sample_ids}},
                    {"_id": 0, "user_id": 1, "display_name": 1, "name": 1, "avatar_url": 1, "picture": 1},
                ).to_list(3)
                mutual_followers["sample"] = [
                    {
                        "user_id": u["user_id"],
                        "display_name": u.get("display_name") or u.get("name", "Utilisateur"),
                        "avatar_url": u.get("avatar_url") or u.get("picture"),
                    }
                    for u in sample_users
                ]
        except Exception:
            pass

    # ── Objectives in progress (visible on profile for context) ──
    objectives_in_progress = []
    show_objectives = is_self or privacy.get("show_stats", True)
    if show_objectives:
        try:
            active_objs = await db.objectives.find(
                {"user_id": user_id, "status": "active"},
                {"_id": 0, "objective_id": 1, "title": 1, "category": 1,
                 "current_day": 1, "target_duration_days": 1, "daily_minutes": 1,
                 "total_sessions": 1, "total_minutes": 1, "streak_days": 1},
            ).sort("created_at", -1).limit(3).to_list(3)
            for obj in active_objs:
                target_days = obj.get("target_duration_days", 30)
                current_day = obj.get("current_day", 0)
                progress_pct = min(round((current_day / target_days) * 100), 100) if target_days > 0 else 0
                objectives_in_progress.append({
                    "objective_id": obj["objective_id"],
                    "title": obj["title"],
                    "category": obj.get("category", "learning"),
                    "progress_percent": progress_pct,
                    "current_day": current_day,
                    "target_days": target_days,
                    "streak_days": obj.get("streak_days", 0),
                })
        except Exception:
            pass

    # ── Featured badges (top 5 for vitrine display) ──
    all_badges = target.get("badges", []) if show_badges else []
    featured_badges = []
    if all_badges:
        # Pinned badges first, then most recent
        pinned = [b for b in all_badges if isinstance(b, dict) and b.get("featured")]
        non_pinned = [b for b in all_badges if isinstance(b, dict) and not b.get("featured")]
        featured_badges = (pinned + non_pinned)[:5]

    # ── XP & Level ──
    from services.xp_engine import xp_progress_in_level
    xp_data = xp_progress_in_level(target.get("total_xp", 0)) if show_stats else None

    return {
        "user_id": target["user_id"],
        "display_name": target.get("display_name", target.get("name", "Utilisateur")),
        "username": target.get("username"),
        "avatar_url": target.get("avatar_url") or target.get("picture"),
        "cover_photo_url": target.get("cover_photo_url"),
        "bio": target.get("bio"),
        "subscription_tier": target.get("subscription_tier", "free"),
        "created_at": target.get("created_at"),
        "followers_count": followers_count,
        "following_count": following_count,
        "is_following": is_following,
        "follows_you": follows_you,
        "mutual_followers": mutual_followers,
        "last_active": target.get("last_active") if not is_self else None,
        "streak_days": target.get("streak_days", 0) if show_stats else None,
        "total_time_invested": target.get("total_time_invested", 0) if show_stats else None,
        "xp": xp_data,
        "badges": all_badges if show_badges else [],
        "featured_badges": featured_badges,
        "objectives_in_progress": objectives_in_progress,
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
            query = {"user_id": user_id, "visibility": {"$in": ["public", "followers"]}, "moderation_status": {"$ne": "hidden"}, "deleted": {"$ne": True}}
        else:
            query = {"user_id": user_id, "visibility": "public", "moderation_status": {"$ne": "hidden"}, "deleted": {"$ne": True}}

    activities = (
        await db.activities.find(query, {"_id": 0})
        .sort("created_at", -1)
        .limit(limit)
        .to_list(limit)
    )

    return {"activities": activities}


# ============== FOLLOW / UNFOLLOW ==============

@router.post("/users/{user_id}/follow")
@limiter.limit("20/minute")
async def follow_user(request: Request, user_id: str, user: dict = Depends(get_current_user)):
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

    # Notify the followed user (non-blocking, silent fail, dedup 24h)
    try:
        display = user.get("display_name") or user.get("name", "Quelqu'un")
        created = await create_notification_deduped(
            user_id=user_id,
            notif_type="new_follower",
            message=f"{display} a commencé à te suivre",
            data={
                "follower_id": user["user_id"],
                "follower_name": display,
            },
        )
        if not created:
            return {"message": "Abonné", "is_following": True}
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
async def get_followers(
    user_id: str,
    user: dict = Depends(get_current_user),
    cursor: str = None,
    limit: int = 50,
):
    """List users who follow this user. Cursor-based pagination."""
    limit = min(limit, 100)  # Cap at 100

    query = {"following_id": user_id, "status": "active"}
    if cursor:
        query["followed_at"] = {"$lt": cursor}

    follows = await db.follows.find(
        query, {"_id": 0, "follower_id": 1, "followed_at": 1},
    ).sort("followed_at", -1).to_list(limit + 1)

    has_more = len(follows) > limit
    follows = follows[:limit]
    next_cursor = follows[-1]["followed_at"] if has_more and follows else None

    follower_ids = [f["follower_id"] for f in follows]
    if not follower_ids:
        return {"followers": [], "next_cursor": None, "has_more": False}

    users = await db.users.find(
        {"user_id": {"$in": follower_ids}},
        {"_id": 0, "user_id": 1, "name": 1, "display_name": 1, "username": 1,
         "avatar_url": 1, "picture": 1},
    ).to_list(limit)

    # Check which ones the current user follows back
    follow_docs = await db.follows.find(
        {"follower_id": user["user_id"], "status": "active",
         "following_id": {"$in": follower_ids}},
        {"_id": 0, "following_id": 1},
    ).to_list(limit)
    my_follows = {f["following_id"] for f in follow_docs}

    # Check which ones follow the current user back
    if user["user_id"] == user_id:
        follows_me = set(follower_ids)
    else:
        follows_me_docs = await db.follows.find(
            {"following_id": user["user_id"], "status": "active",
             "follower_id": {"$in": follower_ids}},
            {"_id": 0, "follower_id": 1},
        ).to_list(limit)
        follows_me = {f["follower_id"] for f in follows_me_docs}

    user_map = {u["user_id"]: u for u in users}
    results = []
    for f in follows:
        u = user_map.get(f["follower_id"])
        if not u:
            continue
        results.append({
            "user_id": u["user_id"],
            "display_name": u.get("display_name", u.get("name", "Utilisateur")),
            "username": u.get("username"),
            "avatar_url": u.get("avatar_url") or u.get("picture"),
            "is_following": u["user_id"] in my_follows,
            "follows_back": u["user_id"] in follows_me,
        })

    return {"followers": results, "next_cursor": next_cursor, "has_more": has_more}


@router.get("/users/{user_id}/following")
async def get_following(
    user_id: str,
    user: dict = Depends(get_current_user),
    cursor: str = None,
    limit: int = 50,
):
    """List users this user follows. Cursor-based pagination."""
    limit = min(limit, 100)

    query = {"follower_id": user_id, "status": "active"}
    if cursor:
        query["followed_at"] = {"$lt": cursor}

    follows = await db.follows.find(
        query, {"_id": 0, "following_id": 1, "followed_at": 1},
    ).sort("followed_at", -1).to_list(limit + 1)

    has_more = len(follows) > limit
    follows = follows[:limit]
    next_cursor = follows[-1]["followed_at"] if has_more and follows else None

    following_ids = [f["following_id"] for f in follows]
    if not following_ids:
        return {"following": [], "next_cursor": None, "has_more": False}

    users = await db.users.find(
        {"user_id": {"$in": following_ids}},
        {"_id": 0, "user_id": 1, "name": 1, "display_name": 1, "username": 1,
         "avatar_url": 1, "picture": 1},
    ).to_list(limit)

    # Check which ones the current user follows
    if user["user_id"] != user_id:
        follow_docs = await db.follows.find(
            {"follower_id": user["user_id"], "status": "active",
             "following_id": {"$in": following_ids}},
            {"_id": 0, "following_id": 1},
        ).to_list(limit)
        my_follows = {f["following_id"] for f in follow_docs}
    else:
        my_follows = set(following_ids)

    # Check which ones follow the profile owner back
    follows_back_docs = await db.follows.find(
        {"follower_id": {"$in": following_ids}, "following_id": user_id, "status": "active"},
        {"_id": 0, "follower_id": 1},
    ).to_list(limit)
    follows_back_set = {f["follower_id"] for f in follows_back_docs}

    user_map = {u["user_id"]: u for u in users}
    results = []
    for f in follows:
        u = user_map.get(f["following_id"])
        if not u:
            continue
        results.append({
            "user_id": u["user_id"],
            "display_name": u.get("display_name", u.get("name", "Utilisateur")),
            "username": u.get("username"),
            "avatar_url": u.get("avatar_url") or u.get("picture"),
            "is_following": u["user_id"] in my_follows,
            "follows_back": u["user_id"] in follows_back_set,
        })

    return {"following": results, "next_cursor": next_cursor, "has_more": has_more}


# ============== SOCIAL ONBOARDING STATUS ==============

SOCIAL_ONBOARDING_TARGET_FOLLOWS = 5


@router.get("/social/onboarding-status")
async def get_social_onboarding_status(user: dict = Depends(get_current_user)):
    """Return social onboarding status for the current user.

    Computes profile completion score, social connection progress,
    and whether the user has shared any activity.
    Benchmarked: LinkedIn (profile meter), Instagram (follow gate),
    Strava (connection step).
    """
    user_id = user["user_id"]

    # Parallel queries for speed
    async def get_user_doc():
        return await db.users.find_one(
            {"user_id": user_id},
            {"_id": 0, "display_name": 1, "name": 1, "username": 1,
             "bio": 1, "avatar_url": 1, "picture": 1, "cover_photo_url": 1,
             "social_onboarding_dismissed": 1},
        )

    async def get_following_count():
        return await db.follows.count_documents(
            {"follower_id": user_id, "status": "active"}
        )

    async def get_followers_count():
        return await db.follows.count_documents(
            {"following_id": user_id, "status": "active"}
        )

    async def get_post_count():
        return await db.activities.count_documents({"user_id": user_id})

    user_doc, following_count, followers_count, post_count = await asyncio.gather(
        get_user_doc(), get_following_count(), get_followers_count(), get_post_count()
    )

    if not user_doc:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    # ── Profile completion (LinkedIn meter pattern) ──
    has_avatar = bool(user_doc.get("avatar_url") or user_doc.get("picture"))
    has_bio = bool(user_doc.get("bio"))
    has_username = bool(user_doc.get("username"))
    has_display_name = bool(user_doc.get("display_name"))
    has_cover = bool(user_doc.get("cover_photo_url"))

    profile_items = [
        ("avatar", has_avatar, 30),
        ("display_name", has_display_name, 20),
        ("username", has_username, 20),
        ("bio", has_bio, 20),
        ("cover_photo", has_cover, 10),
    ]
    profile_score = sum(weight for _, done, weight in profile_items if done)
    missing_fields = [name for name, done, _ in profile_items if not done]

    # ── Social progress ──
    has_posted = post_count > 0
    follows_target_reached = following_count >= SOCIAL_ONBOARDING_TARGET_FOLLOWS
    dismissed = user_doc.get("social_onboarding_dismissed", False)

    # Onboarding is needed if profile < 70% OR follows < target OR never posted
    needs_onboarding = (
        not dismissed
        and (profile_score < 70 or not follows_target_reached or not has_posted)
    )

    return {
        "needs_onboarding": needs_onboarding,
        "profile": {
            "score": profile_score,
            "has_avatar": has_avatar,
            "has_bio": has_bio,
            "has_username": has_username,
            "has_display_name": has_display_name,
            "has_cover": has_cover,
            "missing_fields": missing_fields,
        },
        "social": {
            "following_count": following_count,
            "followers_count": followers_count,
            "has_posted": has_posted,
            "target_follows": SOCIAL_ONBOARDING_TARGET_FOLLOWS,
        },
        "dismissed": dismissed,
    }


@router.post("/social/onboarding-dismiss")
async def dismiss_social_onboarding(user: dict = Depends(get_current_user)):
    """Dismiss social onboarding card. Can be re-shown from settings."""
    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {"social_onboarding_dismissed": True}},
    )
    return {"dismissed": True}


# ============== ACTIVITY HEATMAP (GitHub contributions pattern) ==============

@router.get("/users/{user_id}/activity-heatmap")
async def get_activity_heatmap(
    user_id: str,
    user: dict = Depends(get_current_user),
    days: int = Query(365, ge=30, le=400),
):
    """
    GitHub-style activity heatmap — date-level session aggregation.

    Returns a dict of dates → {count, minutes} for the past N days.
    Respects privacy: only returns data if stats are visible.
    """
    target = await db.users.find_one(
        {"user_id": user_id},
        {"_id": 0, "privacy": 1, "user_id": 1},
    )
    if not target:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    is_self = user["user_id"] == user_id

    # Privacy: respect show_stats setting
    if not is_self:
        privacy = target.get("privacy", {})
        if not privacy.get("profile_visible", True):
            raise HTTPException(status_code=403, detail="Profil privé")
        if not privacy.get("show_stats", True):
            return {"dates": {}, "summary": {"total_sessions": 0, "total_minutes": 0, "active_days": 0, "longest_streak": 0}}

        # Block check
        blocked_ids = await get_blocked_ids(user["user_id"])
        if user_id in blocked_ids:
            raise HTTPException(status_code=403, detail="Profil indisponible")

    from_date = (datetime.now(timezone.utc) - __import__("datetime").timedelta(days=days)).isoformat()

    pipeline = [
        {"$match": {
            "user_id": user_id,
            "completed": True,
            "completed_at": {"$gte": from_date},
        }},
        {"$addFields": {
            "date_key": {"$substr": ["$completed_at", 0, 10]},
        }},
        {"$group": {
            "_id": "$date_key",
            "count": {"$sum": 1},
            "minutes": {"$sum": {"$ifNull": ["$actual_duration", 0]}},
        }},
        {"$sort": {"_id": 1}},
    ]

    results = await db.user_sessions_history.aggregate(pipeline).to_list(400)

    dates = {}
    total_sessions = 0
    total_minutes = 0
    for r in results:
        dates[r["_id"]] = {"count": r["count"], "minutes": r["minutes"]}
        total_sessions += r["count"]
        total_minutes += r["minutes"]

    # Compute longest streak from the date data
    active_dates = sorted(dates.keys())
    longest_streak = 0
    current_streak = 0
    prev_date = None
    for d in active_dates:
        if prev_date:
            diff = (datetime.fromisoformat(d) - datetime.fromisoformat(prev_date)).days
            if diff == 1:
                current_streak += 1
            else:
                current_streak = 1
        else:
            current_streak = 1
        longest_streak = max(longest_streak, current_streak)
        prev_date = d

    return {
        "dates": dates,
        "summary": {
            "total_sessions": total_sessions,
            "total_minutes": total_minutes,
            "active_days": len(active_dates),
            "longest_streak": longest_streak,
        },
    }


# ============== PRESENCE / ONLINE STATUS ==============

@router.post("/presence/batch")
async def get_presence_status(request: Request, user: dict = Depends(get_current_user)):
    """
    Batch presence check for multiple users.

    Body: {"user_ids": ["uid1", "uid2", ...]}
    Returns: {"presence": {"uid1": {"status": "online", "label": "En ligne"}, ...}}

    Respects privacy — users with show_activity_status=False appear offline.
    Max 50 users per request.
    """
    body = await request.json()
    user_ids = body.get("user_ids", [])
    if not user_ids or len(user_ids) > 50:
        return {"presence": {}}

    presence = await get_presence_batch(user_ids)
    return {"presence": presence}


# ============== PUBLIC SHARE PAGE (no auth — virality) ==============

public_router = APIRouter(tags=["share"])


@public_router.get("/share/profile/{user_id}")
async def public_share_profile(user_id: str):
    """
    Public profile share page data — NO auth required.
    Returns limited profile info for share cards / social previews.

    Pattern: Strava share, Spotify Wrapped, Duolingo streak share.
    Only exposes data the user has set to public.
    """
    user = await db.users.find_one(
        {"user_id": user_id},
        {"_id": 0, "user_id": 1, "display_name": 1, "name": 1, "username": 1,
         "avatar_url": 1, "picture": 1, "bio": 1, "privacy": 1,
         "streak_days": 1, "total_time_invested": 1, "total_xp": 1,
         "level": 1, "badges": 1, "created_at": 1, "subscription_tier": 1},
    )
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    # Respect privacy
    privacy = user.get("privacy", {})
    if not privacy.get("profile_visible", True):
        raise HTTPException(status_code=403, detail="Profil privé")

    # Build public profile
    show_stats = privacy.get("show_stats", True)
    show_badges = privacy.get("show_badges", True)

    # Badge vitrine (only featured ones, capped)
    badges = user.get("badges", []) if show_badges else []
    featured = [b for b in badges if b.get("featured")][:5]
    if not featured and badges:
        featured = badges[:3]

    # Social counts
    followers_count = await db.follows.count_documents(
        {"following_id": user_id, "status": "active"}
    )

    result = {
        "user_id": user_id,
        "display_name": user.get("display_name") or user.get("name", "Utilisateur"),
        "username": user.get("username"),
        "avatar_url": user.get("avatar_url") or user.get("picture"),
        "bio": user.get("bio", ""),
        "subscription_tier": user.get("subscription_tier", "free"),
        "created_at": user.get("created_at"),
        "followers_count": followers_count,
    }

    if show_stats:
        result["streak_days"] = user.get("streak_days", 0)
        result["total_time_invested"] = user.get("total_time_invested", 0)
        result["level"] = user.get("level", 1)

    if featured:
        result["badges"] = [
            {"name": b.get("name", ""), "icon": b.get("icon", "")}
            for b in featured
        ]

    return result
