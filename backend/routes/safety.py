"""
InFinea — Social Safety routes.
User blocking, content reporting, RGPD account deletion.

Design:
- Blocks are bidirectional in effect (A blocks B → neither sees the other).
- Reports are stored for admin review (no auto-action beyond logging).
- Account deletion cascades across all social collections.
- Benchmarked: Instagram block/report UX, RGPD Article 17.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends, Request

from database import db
from auth import get_current_user

router = APIRouter()


# ============== BLOCK / UNBLOCK ==============

@router.post("/users/{user_id}/block")
async def block_user(user_id: str, user: dict = Depends(get_current_user)):
    """Block a user. Bidirectional filtering: neither party sees the other."""
    if user["user_id"] == user_id:
        raise HTTPException(status_code=400, detail="Impossible de se bloquer soi-même")

    target = await db.users.find_one({"user_id": user_id}, {"_id": 1})
    if not target:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    existing = await db.blocks.find_one(
        {"blocker_id": user["user_id"], "blocked_id": user_id}
    )
    if existing:
        raise HTTPException(status_code=400, detail="Utilisateur déjà bloqué")

    now = datetime.now(timezone.utc).isoformat()

    await db.blocks.insert_one({
        "blocker_id": user["user_id"],
        "blocked_id": user_id,
        "created_at": now,
    })

    # Auto-unfollow in both directions (silent, non-blocking)
    await db.follows.update_many(
        {"$or": [
            {"follower_id": user["user_id"], "following_id": user_id},
            {"follower_id": user_id, "following_id": user["user_id"]},
        ]},
        {"$set": {"status": "inactive"}},
    )

    return {"message": "Utilisateur bloqué", "blocked": True}


@router.delete("/users/{user_id}/block")
async def unblock_user(user_id: str, user: dict = Depends(get_current_user)):
    """Unblock a user."""
    result = await db.blocks.delete_one(
        {"blocker_id": user["user_id"], "blocked_id": user_id}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=400, detail="Utilisateur non bloqué")

    return {"message": "Utilisateur débloqué", "blocked": False}


@router.get("/users/blocked")
async def get_blocked_users(user: dict = Depends(get_current_user)):
    """List users blocked by the current user."""
    blocks = await db.blocks.find(
        {"blocker_id": user["user_id"]},
        {"_id": 0, "blocked_id": 1, "created_at": 1},
    ).to_list(200)

    if not blocks:
        return {"blocked_users": []}

    blocked_ids = [b["blocked_id"] for b in blocks]
    users = await db.users.find(
        {"user_id": {"$in": blocked_ids}},
        {"_id": 0, "user_id": 1, "name": 1, "display_name": 1, "username": 1,
         "avatar_url": 1, "picture": 1},
    ).to_list(len(blocked_ids))

    user_map = {u["user_id"]: u for u in users}
    results = []
    for b in blocks:
        u = user_map.get(b["blocked_id"], {})
        results.append({
            "user_id": b["blocked_id"],
            "display_name": u.get("display_name") or u.get("name", "Utilisateur"),
            "username": u.get("username"),
            "avatar_url": u.get("avatar_url") or u.get("picture"),
            "blocked_at": b["created_at"],
        })

    return {"blocked_users": results}


# ============== REPORT ==============

REPORT_TYPES = {"user", "comment", "activity", "group"}
REPORT_REASONS = {
    "harassment", "spam", "hate_speech", "inappropriate_content",
    "impersonation", "self_harm", "other",
}


@router.post("/report")
async def report_content(
    request: Request,
    user: dict = Depends(get_current_user),
):
    """
    Report a user, comment, activity, or group.
    Stored for admin review.
    """
    body = await request.json()

    target_type = body.get("target_type", "")
    target_id = body.get("target_id", "")
    reason = body.get("reason", "")
    details = str(body.get("details", "")).strip()[:500]

    if target_type not in REPORT_TYPES:
        raise HTTPException(status_code=400, detail=f"Type invalide. Choix : {', '.join(REPORT_TYPES)}")

    if reason not in REPORT_REASONS:
        raise HTTPException(status_code=400, detail=f"Raison invalide. Choix : {', '.join(REPORT_REASONS)}")

    if not target_id:
        raise HTTPException(status_code=400, detail="target_id requis")

    # Prevent duplicate reports
    existing = await db.reports.find_one({
        "reporter_id": user["user_id"],
        "target_type": target_type,
        "target_id": target_id,
        "status": {"$in": ["pending", "reviewed"]},
    })
    if existing:
        raise HTTPException(status_code=400, detail="Vous avez déjà signalé ce contenu")

    now = datetime.now(timezone.utc).isoformat()
    report_id = f"report_{uuid.uuid4().hex[:12]}"

    await db.reports.insert_one({
        "report_id": report_id,
        "reporter_id": user["user_id"],
        "target_type": target_type,
        "target_id": target_id,
        "reason": reason,
        "details": details,
        "status": "pending",
        "created_at": now,
    })

    return {"message": "Signalement enregistré. Merci.", "report_id": report_id}


# ============== CHECK BLOCK STATUS ==============

@router.get("/users/{user_id}/block-status")
async def get_block_status(user_id: str, user: dict = Depends(get_current_user)):
    """Check if a user is blocked by the current user."""
    block = await db.blocks.find_one(
        {"blocker_id": user["user_id"], "blocked_id": user_id}
    )
    return {"blocked": block is not None}


# ============== RGPD — ACCOUNT DELETION ==============

@router.delete("/account")
async def delete_account(
    request: Request,
    user: dict = Depends(get_current_user),
):
    """
    RGPD Article 17 — Right to erasure.
    Cascade delete all user data across all collections.
    Requires confirmation field in body.
    """
    body = await request.json()
    if body.get("confirm") != "DELETE_MY_ACCOUNT":
        raise HTTPException(
            status_code=400,
            detail="Confirmation requise : envoyez {\"confirm\": \"DELETE_MY_ACCOUNT\"}"
        )

    uid = user["user_id"]

    # Cascade delete across all collections
    # Order matters: dependent data first, then the user document last.

    # Social
    await db.follows.delete_many(
        {"$or": [{"follower_id": uid}, {"following_id": uid}]}
    )
    await db.blocks.delete_many(
        {"$or": [{"blocker_id": uid}, {"blocked_id": uid}]}
    )
    await db.reactions.delete_many({"user_id": uid})
    await db.comments.delete_many({"user_id": uid})
    await db.activities.delete_many({"user_id": uid})

    # Anonymize comments by others on user's activities (don't delete others' comments)
    user_activity_ids = await db.activities.find(
        {"user_id": uid}, {"activity_id": 1}
    ).to_list(None)
    # Activities already deleted above, but comments on them from others should be cleaned
    # (they reference activity_ids that no longer exist)

    # Groups: remove from member arrays, delete groups owned alone
    groups = await db.groups.find(
        {"members.user_id": uid}, {"group_id": 1, "members": 1}
    ).to_list(None)
    for g in groups:
        remaining = [m for m in g.get("members", []) if m.get("user_id") != uid]
        if not remaining:
            await db.groups.delete_one({"group_id": g["group_id"]})
        else:
            await db.groups.update_one(
                {"group_id": g["group_id"]},
                {"$pull": {"members": {"user_id": uid}}},
            )

    # Challenges: remove from participants
    await db.challenges.update_many(
        {"participants.user_id": uid},
        {"$pull": {"participants": {"user_id": uid}}},
    )
    await db.challenge_invites.delete_many(
        {"$or": [{"user_id": uid}, {"invited_by": uid}]}
    )

    # Content
    await db.user_sessions_history.delete_many({"user_id": uid})
    await db.objectives.delete_many({"user_id": uid})
    await db.routines.delete_many({"user_id": uid})
    await db.reflections.delete_many({"user_id": uid})
    await db.shares.delete_many({"user_id": uid})
    await db.notifications.delete_many({"user_id": uid})
    await db.coach_messages.delete_many({"user_id": uid})

    # Analytics / features
    await db.event_log.delete_many({"user_id": uid})
    await db.user_features.delete_many({"user_id": uid})
    await db.action_signals.delete_many({"user_id": uid})
    await db.micro_instant_outcomes.delete_many({"user_id": uid})

    # Auth
    await db.refresh_tokens.delete_many({"user_id": uid})

    # Reports: keep reporter_id for moderation history (30-day legal retention)
    # but anonymize
    await db.reports.update_many(
        {"reporter_id": uid},
        {"$set": {"reporter_id": "deleted_user"}},
    )

    # Finally: delete the user document
    await db.users.delete_one({"user_id": uid})

    return {"message": "Compte supprimé. Toutes vos données ont été effacées."}
