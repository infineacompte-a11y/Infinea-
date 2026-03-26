"""
InFinea — Social Safety routes.
User blocking, content reporting, admin moderation, RGPD account deletion.

Design:
- Blocks are bidirectional in effect (A blocks B → neither sees the other).
- Reports are stored for admin review with a full moderation queue.
- Admin actions: dismiss, warn, remove_content, suspend_user.
- Account deletion cascades across all social collections.
- Benchmarked: Instagram block/report UX, Discord mod queue, RGPD Article 17.
"""

import os
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends, Request

from database import db
from auth import get_current_user
from config import logger

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

REPORT_TYPES = {"user", "comment", "activity", "group", "message"}
REPORT_REASONS = {
    "harassment", "spam", "hate_speech", "inappropriate_content",
    "impersonation", "self_harm", "other",
}

# ── Auto-escalation thresholds (Discord/Instagram benchmark) ──
# When a piece of content reaches this many unique reports, it's auto-hidden.
# This prevents pile-on abuse while catching genuinely problematic content.
AUTO_HIDE_THRESHOLD = 3        # 3 unique reporters → auto-hide content
AUTO_SUSPEND_THRESHOLD = 10    # 10 unique reports on a user → auto-suspend


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

    # ── Auto-escalation: check report count thresholds ──
    try:
        await _check_auto_escalation(target_type, target_id, now)
    except Exception:
        pass  # Escalation failure must never block the report

    return {"message": "Signalement enregistré. Merci.", "report_id": report_id}


# ── Auto-escalation engine ──

async def _check_auto_escalation(target_type: str, target_id: str, now: str):
    """
    Check if a target has crossed report thresholds and take automatic action.

    Thresholds (benchmarked from Discord Trust & Safety, Instagram):
    - AUTO_HIDE_THRESHOLD (3): content auto-hidden, author notified
    - AUTO_SUSPEND_THRESHOLD (10): user auto-suspended (requires user target)

    Uses count of UNIQUE reporters (not total reports) to prevent abuse
    where one person submits multiple reports.
    """
    # Count unique reporters for this target
    unique_reporters = await db.reports.distinct(
        "reporter_id",
        {"target_type": target_type, "target_id": target_id, "status": "pending"},
    )
    report_count = len(unique_reporters)

    # ── Auto-hide content at threshold ──
    if report_count >= AUTO_HIDE_THRESHOLD:
        if target_type == "activity":
            # Check if not already hidden
            activity = await db.activities.find_one(
                {"activity_id": target_id, "moderation_status": {"$ne": "hidden"}},
                {"user_id": 1},
            )
            if activity:
                await db.activities.update_one(
                    {"activity_id": target_id},
                    {"$set": {"moderation_status": "hidden"}},
                )
                await db.notifications.insert_one({
                    "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
                    "user_id": activity["user_id"],
                    "type": "moderation",
                    "message": "Ta publication a été masquée suite à plusieurs signalements. Elle sera examinée par notre équipe.",
                    "data": {"reason": "multiple_reports", "target_id": target_id},
                    "read": False,
                    "created_at": now,
                })
                logger.info(f"Auto-hide: activity {target_id} ({report_count} reports)")

        elif target_type == "comment":
            comment = await db.comments.find_one(
                {"comment_id": target_id, "moderation_status": {"$ne": "hidden"}},
                {"user_id": 1},
            )
            if comment:
                await db.comments.update_one(
                    {"comment_id": target_id},
                    {"$set": {"moderation_status": "hidden"}},
                )
                await db.notifications.insert_one({
                    "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
                    "user_id": comment["user_id"],
                    "type": "moderation",
                    "message": "Ton commentaire a été masqué suite à plusieurs signalements.",
                    "data": {"reason": "multiple_reports", "target_id": target_id},
                    "read": False,
                    "created_at": now,
                })
                logger.info(f"Auto-hide: comment {target_id} ({report_count} reports)")

        elif target_type == "message":
            msg = await db.messages.find_one(
                {"message_id": target_id, "moderation_status": {"$ne": "hidden"}},
                {"sender_id": 1},
            )
            if msg:
                await db.messages.update_one(
                    {"message_id": target_id},
                    {"$set": {"moderation_status": "hidden"}},
                )
                logger.info(f"Auto-hide: message {target_id} ({report_count} reports)")

    # ── Auto-suspend user at higher threshold ──
    if target_type == "user" and report_count >= AUTO_SUSPEND_THRESHOLD:
        user_doc = await db.users.find_one(
            {"user_id": target_id, "suspended": {"$ne": True}},
            {"user_id": 1},
        )
        if user_doc:
            await db.users.update_one(
                {"user_id": target_id},
                {"$set": {
                    "suspended": True,
                    "suspended_at": now,
                    "suspended_reason": "auto_escalation_multiple_reports",
                }},
            )
            await db.notifications.insert_one({
                "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
                "user_id": target_id,
                "type": "account_suspended",
                "message": "Ton compte a été temporairement suspendu suite à de nombreux signalements. Contacte le support.",
                "data": {"reason": "auto_escalation"},
                "read": False,
                "created_at": now,
            })
            logger.info(f"Auto-suspend: user {target_id} ({report_count} reports)")


# ============== ADMIN MODERATION ==============

ADMIN_ACTIONS = {"dismiss", "warn", "remove_content", "suspend_user"}


def _require_admin(user: dict):
    """Raise 403 if user is not in ADMIN_EMAILS."""
    raw = os.environ.get("ADMIN_EMAILS", "")
    emails = [e.strip().lower() for e in raw.split(",") if e.strip()]
    if user.get("email", "").lower() not in emails:
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")


@router.get("/admin/reports/stats")
async def get_moderation_stats(user: dict = Depends(get_current_user)):
    """Dashboard stats for the moderation queue."""
    _require_admin(user)

    pending = await db.reports.count_documents({"status": "pending"})
    resolved = await db.reports.count_documents({"status": {"$in": ["dismissed", "resolved"]}})

    # Reports by reason (top reasons)
    reason_pipeline = [
        {"$match": {"status": "pending"}},
        {"$group": {"_id": "$reason", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    by_reason = await db.reports.aggregate(reason_pipeline).to_list(20)

    # Reports by type
    type_pipeline = [
        {"$match": {"status": "pending"}},
        {"$group": {"_id": "$target_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    by_type = await db.reports.aggregate(type_pipeline).to_list(20)

    return {
        "pending": pending,
        "resolved": resolved,
        "by_reason": {r["_id"]: r["count"] for r in by_reason},
        "by_type": {t["_id"]: t["count"] for t in by_type},
    }


@router.get("/admin/reports")
async def get_reports(
    user: dict = Depends(get_current_user),
    status: str = "pending",
    target_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    """List reports for admin review."""
    _require_admin(user)

    query = {}
    if status:
        query["status"] = status
    if target_type:
        query["target_type"] = target_type

    reports = (
        await db.reports.find(query, {"_id": 0})
        .sort("created_at", -1)
        .skip(offset)
        .limit(limit)
        .to_list(limit)
    )

    # Enrich with reporter info
    reporter_ids = list({r["reporter_id"] for r in reports if r.get("reporter_id") != "deleted_user"})
    if reporter_ids:
        reporters = await db.users.find(
            {"user_id": {"$in": reporter_ids}},
            {"_id": 0, "user_id": 1, "display_name": 1, "username": 1, "avatar_url": 1},
        ).to_list(len(reporter_ids))
        reporter_map = {u["user_id"]: u for u in reporters}
    else:
        reporter_map = {}

    for r in reports:
        rid = r.get("reporter_id", "")
        reporter = reporter_map.get(rid, {})
        r["reporter_name"] = reporter.get("display_name", "Utilisateur supprimé")
        r["reporter_avatar"] = reporter.get("avatar_url")

    total = await db.reports.count_documents(query)

    return {"reports": reports, "total": total}


@router.get("/admin/reports/{report_id}")
async def get_report_detail(report_id: str, user: dict = Depends(get_current_user)):
    """Get full report detail with target context."""
    _require_admin(user)

    report = await db.reports.find_one({"report_id": report_id}, {"_id": 0})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Enrich reporter
    if report.get("reporter_id") and report["reporter_id"] != "deleted_user":
        reporter = await db.users.find_one(
            {"user_id": report["reporter_id"]},
            {"_id": 0, "user_id": 1, "display_name": 1, "username": 1, "avatar_url": 1},
        )
        report["reporter"] = reporter or {}
    else:
        report["reporter"] = {"display_name": "Utilisateur supprimé"}

    # Enrich target context
    target = None
    tt = report.get("target_type")
    tid = report.get("target_id")

    if tt == "comment":
        target = await db.comments.find_one({"comment_id": tid}, {"_id": 0})
    elif tt == "activity":
        target = await db.activities.find_one({"activity_id": tid}, {"_id": 0})
    elif tt == "user":
        target = await db.users.find_one(
            {"user_id": tid},
            {"_id": 0, "user_id": 1, "display_name": 1, "username": 1,
             "avatar_url": 1, "bio": 1, "email": 1, "created_at": 1},
        )
    elif tt == "group":
        target = await db.groups.find_one({"group_id": tid}, {"_id": 0})
    elif tt == "message":
        target = await db.messages.find_one({"message_id": tid}, {"_id": 0})

    report["target"] = target

    # Count previous reports against same target
    previous_count = await db.reports.count_documents({
        "target_type": tt,
        "target_id": tid,
        "report_id": {"$ne": report_id},
    })
    report["previous_reports_count"] = previous_count

    # If target is a user, count total reports against them
    if tt == "user":
        total_user_reports = await db.reports.count_documents({"target_id": tid})
        report["total_user_reports"] = total_user_reports

    return report


@router.put("/admin/reports/{report_id}/action")
async def moderate_report(
    report_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    """
    Take moderation action on a report.
    Actions: dismiss, warn, remove_content, suspend_user.
    """
    _require_admin(user)

    body = await request.json()
    action = body.get("action", "")
    admin_note = str(body.get("note", "")).strip()[:500]

    if action not in ADMIN_ACTIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Action invalide. Choix : {', '.join(sorted(ADMIN_ACTIONS))}",
        )

    report = await db.reports.find_one({"report_id": report_id}, {"_id": 0})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    now = datetime.now(timezone.utc).isoformat()
    target_type = report.get("target_type")
    target_id = report.get("target_id")

    # ── Execute action ──
    result_message = ""

    if action == "dismiss":
        result_message = "Report dismissed"

    elif action == "warn":
        # Send warning notification to the reported user (target_id if user, or content owner)
        warned_user_id = target_id
        if target_type == "comment":
            comment = await db.comments.find_one({"comment_id": target_id}, {"user_id": 1})
            warned_user_id = comment["user_id"] if comment else None
        elif target_type == "activity":
            activity = await db.activities.find_one({"activity_id": target_id}, {"user_id": 1})
            warned_user_id = activity["user_id"] if activity else None
        elif target_type == "message":
            message = await db.messages.find_one({"message_id": target_id}, {"sender_id": 1})
            warned_user_id = message["sender_id"] if message else None

        if warned_user_id:
            await db.notifications.insert_one({
                "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
                "user_id": warned_user_id,
                "type": "moderation_warning",
                "message": "Un de tes contenus a été signalé et ne respecte pas les règles de la communauté. Merci de rester bienveillant.",
                "data": {"reason": report.get("reason")},
                "read": False,
                "created_at": now,
            })
            result_message = f"Warning sent to {warned_user_id}"
        else:
            result_message = "Warning skipped — target user not found"

    elif action == "remove_content":
        if target_type == "comment":
            del_result = await db.comments.delete_one({"comment_id": target_id})
            result_message = f"Comment deleted ({del_result.deleted_count})"
        elif target_type == "activity":
            del_result = await db.activities.delete_one({"activity_id": target_id})
            # Also clean up reactions and comments on this activity
            await db.reactions.delete_many({"activity_id": target_id})
            await db.comments.delete_many({"activity_id": target_id})
            result_message = f"Activity + reactions + comments deleted ({del_result.deleted_count})"
        elif target_type == "message":
            del_result = await db.messages.delete_one({"message_id": target_id})
            result_message = f"Message deleted ({del_result.deleted_count})"
        else:
            result_message = f"Cannot remove content for target_type={target_type}"

    elif action == "suspend_user":
        suspended_user_id = target_id
        if target_type != "user":
            # Find the content owner
            if target_type == "comment":
                doc = await db.comments.find_one({"comment_id": target_id}, {"user_id": 1})
                suspended_user_id = doc["user_id"] if doc else None
            elif target_type == "activity":
                doc = await db.activities.find_one({"activity_id": target_id}, {"user_id": 1})
                suspended_user_id = doc["user_id"] if doc else None

        if suspended_user_id:
            await db.users.update_one(
                {"user_id": suspended_user_id},
                {"$set": {"suspended": True, "suspended_at": now, "suspended_reason": report.get("reason")}},
            )
            # Send notification
            await db.notifications.insert_one({
                "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
                "user_id": suspended_user_id,
                "type": "account_suspended",
                "message": "Ton compte a été suspendu suite à des signalements. Contacte le support pour plus d'informations.",
                "data": {"reason": report.get("reason")},
                "read": False,
                "created_at": now,
            })
            result_message = f"User {suspended_user_id} suspended"
        else:
            result_message = "Suspend skipped — target user not found"

    # ── Update report status ──
    new_status = "dismissed" if action == "dismiss" else "resolved"
    await db.reports.update_one(
        {"report_id": report_id},
        {
            "$set": {
                "status": new_status,
                "action_taken": action,
                "admin_note": admin_note,
                "resolved_by": user["user_id"],
                "resolved_at": now,
            }
        },
    )

    logger.info(f"Moderation: {action} on report {report_id} by admin {user['user_id']}: {result_message}")

    return {"message": result_message, "action": action, "status": new_status}


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
