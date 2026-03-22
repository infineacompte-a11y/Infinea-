"""
InFinea — User Profile routes.
Public profiles, profile updates, privacy settings.

Design:
- Profile data lives ON the user document (no separate collection = no joins).
- Privacy controls are granular and RGPD-aligned.
- Public profile endpoint doesn't require auth (for sharing).
- Benchmarked: Strava athlete profiles, Duolingo user profiles.
"""

from fastapi import APIRouter, HTTPException, Depends

from database import db
from auth import get_current_user
from models import ProfileUpdate, PrivacySettings

router = APIRouter(prefix="/api")


@router.get("/profile/me")
async def get_my_profile(user: dict = Depends(get_current_user)):
    """Get the authenticated user's full profile (private view)."""
    # Fetch fresh from DB (user from auth may be stale for profile fields)
    profile = await db.users.find_one(
        {"user_id": user["user_id"]}, {"_id": 0, "password": 0}
    )
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")

    # Add social counts
    followers_count = await db.follows.count_documents(
        {"following_id": user["user_id"], "status": "active"}
    )
    following_count = await db.follows.count_documents(
        {"follower_id": user["user_id"], "status": "active"}
    )

    profile["followers_count"] = followers_count
    profile["following_count"] = following_count

    return profile


@router.put("/profile")
async def update_profile(
    update: ProfileUpdate,
    user: dict = Depends(get_current_user),
):
    """Update profile fields (display_name, bio, avatar)."""
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": update_data},
    )

    return {"message": "Profile updated", "updated_fields": list(update_data.keys())}


@router.get("/profile/privacy")
async def get_privacy_settings(user: dict = Depends(get_current_user)):
    """Get current privacy settings."""
    user_doc = await db.users.find_one(
        {"user_id": user["user_id"]}, {"_id": 0, "privacy": 1}
    )
    # Return stored settings or defaults
    defaults = PrivacySettings().model_dump()
    stored = user_doc.get("privacy", {}) if user_doc else {}
    return {**defaults, **stored}


@router.put("/profile/privacy")
async def update_privacy_settings(
    settings: PrivacySettings,
    user: dict = Depends(get_current_user),
):
    """Update privacy settings."""
    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {"privacy": settings.model_dump()}},
    )
    return {"message": "Privacy settings updated", "privacy": settings.model_dump()}


@router.get("/users/{user_id}/profile")
async def get_public_profile(
    user_id: str,
    user: dict = Depends(get_current_user),
):
    """
    Get another user's public profile.
    Respects privacy settings — only returns what the user has allowed.
    """
    target = await db.users.find_one(
        {"user_id": user_id}, {"_id": 0, "password": 0}
    )
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    privacy = target.get("privacy", PrivacySettings().model_dump())

    if not privacy.get("profile_visible", True):
        raise HTTPException(status_code=403, detail="Profile is private")

    # Build public profile based on privacy settings
    profile = {
        "user_id": target["user_id"],
        "display_name": target.get("display_name", target.get("name", "Utilisateur")),
        "bio": target.get("bio"),
        "avatar_url": target.get("avatar_url", target.get("picture")),
        "created_at": target.get("created_at"),
    }

    if privacy.get("show_stats", True):
        profile["streak_days"] = target.get("streak_days", 0)
        profile["total_time_invested"] = target.get("total_time_invested", 0)

    if privacy.get("show_badges", True):
        profile["badges"] = target.get("badges", [])

    # Social counts (always visible if profile is visible)
    profile["followers_count"] = await db.follows.count_documents(
        {"following_id": user_id, "status": "active"}
    )
    profile["following_count"] = await db.follows.count_documents(
        {"follower_id": user_id, "status": "active"}
    )

    # Is the requesting user following this person?
    follow = await db.follows.find_one(
        {"follower_id": user["user_id"], "following_id": user_id, "status": "active"}
    )
    profile["is_following"] = follow is not None

    return profile


@router.get("/users/search")
async def search_users(
    q: str,
    user: dict = Depends(get_current_user),
    limit: int = 20,
):
    """
    Search users by name or display_name.
    Only returns users with visible profiles.
    """
    if len(q) < 2:
        raise HTTPException(status_code=400, detail="Query must be at least 2 characters")

    # Text search on name and display_name
    query = {
        "$or": [
            {"name": {"$regex": q, "$options": "i"}},
            {"display_name": {"$regex": q, "$options": "i"}},
        ],
        "user_id": {"$ne": user["user_id"]},  # Exclude self
    }

    users = await db.users.find(
        query,
        {"_id": 0, "user_id": 1, "name": 1, "display_name": 1, "avatar_url": 1, "picture": 1, "privacy": 1},
    ).limit(limit).to_list(limit)

    # Filter out private profiles and build results
    results = []
    for u in users:
        privacy = u.get("privacy", {})
        if not privacy.get("profile_visible", True):
            continue

        results.append({
            "user_id": u["user_id"],
            "display_name": u.get("display_name", u.get("name", "Utilisateur")),
            "avatar_url": u.get("avatar_url", u.get("picture")),
        })

    return {"users": results, "count": len(results)}
