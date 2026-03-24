"""InFinea — Social routes. Groups, shares."""

import uuid
import secrets
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, HTTPException, Request, Depends

from database import db
from auth import get_current_user
from models import GroupCreate, GroupInvite, ShareCreate
from config import limiter
from helpers import send_push_to_user
from services.moderation import check_content, sanitize_text
from services.email_service import send_email_to_user, email_group_invite

router = APIRouter()
public_router = APIRouter()

# ============== DUO / GROUPE (D.3) ==============
# Pattern: Duolingo Friends Quest — small bounded groups (2-10), embedded members.
# Single-document design (MongoDB best practice for bounded arrays <50 elements).

GROUP_MAX_MEMBERS = 10
GROUP_CATEGORIES = {"learning", "productivity", "well_being", "creativity", "fitness", "mindfulness"}


async def _refresh_group_member_stats(group_doc: dict) -> dict:
    """Refresh live stats for all members of a group. Lightweight — only reads user docs."""
    user_ids = [m["user_id"] for m in group_doc.get("members", [])]
    if not user_ids:
        return group_doc
    users = await db.users.find(
        {"user_id": {"$in": user_ids}},
        {"_id": 0, "user_id": 1, "streak_days": 1, "total_time_invested": 1}
    ).to_list(GROUP_MAX_MEMBERS)
    user_map = {u["user_id"]: u for u in users}

    now = datetime.now(timezone.utc)
    week_start = (now.date() - timedelta(days=now.weekday())).isoformat()

    # Batch query: week minutes per member
    week_pipeline = [
        {"$match": {"user_id": {"$in": user_ids}, "completed": True, "completed_at": {"$gte": week_start}}},
        {"$group": {"_id": "$user_id", "week_minutes": {"$sum": "$actual_duration"}, "week_sessions": {"$sum": 1}}}
    ]
    week_stats = {s["_id"]: s for s in await db.user_sessions_history.aggregate(week_pipeline).to_list(GROUP_MAX_MEMBERS)}

    for member in group_doc["members"]:
        uid = member["user_id"]
        u = user_map.get(uid, {})
        ws = week_stats.get(uid, {})
        member["stats"] = {
            "streak_days": u.get("streak_days", 0),
            "total_time_invested": u.get("total_time_invested", 0),
            "week_minutes": ws.get("week_minutes", 0),
            "week_sessions": ws.get("week_sessions", 0),
        }
    return group_doc


@router.post("/groups")
@limiter.limit("5/minute")
async def create_group(request: Request, body: GroupCreate, user: dict = Depends(get_current_user)):
    """Create a new duo/group. The creator becomes the owner."""
    # Check user isn't in too many groups (limit: 5 active)
    existing = await db.groups.count_documents(
        {"members.user_id": user["user_id"], "status": "active"}
    )
    if existing >= 5:
        raise HTTPException(status_code=400, detail="Maximum 5 groupes actifs autorisés")

    group_id = f"grp_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()

    # Sanitize + moderate group name
    group_name = sanitize_text(body.name, max_length=50)
    if not group_name:
        raise HTTPException(status_code=400, detail="Le nom du groupe est requis")
    moderation = check_content(group_name)
    if not moderation["allowed"]:
        raise HTTPException(status_code=400, detail=moderation["reason"])

    group_doc = {
        "group_id": group_id,
        "name": group_name,
        "objective_title": sanitize_text(body.objective_title or "", max_length=100) or None,
        "category": body.category if body.category in GROUP_CATEGORIES else None,
        "owner_id": user["user_id"],
        "members": [{
            "user_id": user["user_id"],
            "name": user.get("name", ""),
            "role": "owner",
            "joined_at": now,
            "stats": {
                "streak_days": user.get("streak_days", 0),
                "total_time_invested": user.get("total_time_invested", 0),
                "week_minutes": 0,
                "week_sessions": 0,
            },
        }],
        "invites": [],
        "max_members": GROUP_MAX_MEMBERS,
        "status": "active",
        "created_at": now,
    }
    await db.groups.insert_one(group_doc)
    return {"group_id": group_id, "message": "Groupe créé"}


@router.get("/groups")
async def list_groups(user: dict = Depends(get_current_user)):
    """List all groups the user belongs to."""
    groups = await db.groups.find(
        {"members.user_id": user["user_id"], "status": "active"},
        {"_id": 0}
    ).sort("created_at", -1).to_list(10)

    # Refresh stats for all groups
    for g in groups:
        await _refresh_group_member_stats(g)
    return {"groups": groups}


@router.get("/groups/{group_id}")
async def get_group(group_id: str, user: dict = Depends(get_current_user)):
    """Get a single group with refreshed member stats."""
    group = await db.groups.find_one(
        {"group_id": group_id, "members.user_id": user["user_id"], "status": "active"},
        {"_id": 0}
    )
    if not group:
        raise HTTPException(status_code=404, detail="Groupe introuvable")
    await _refresh_group_member_stats(group)
    return group


@router.post("/groups/{group_id}/invite")
@limiter.limit("10/minute")
async def invite_to_group(request: Request, group_id: str, body: GroupInvite, user: dict = Depends(get_current_user)):
    """Invite someone to a group by email."""
    group = await db.groups.find_one(
        {"group_id": group_id, "members.user_id": user["user_id"], "status": "active"}
    )
    if not group:
        raise HTTPException(status_code=404, detail="Groupe introuvable")

    if len(group.get("members", [])) + len([i for i in group.get("invites", []) if i["status"] == "pending"]) >= GROUP_MAX_MEMBERS:
        raise HTTPException(status_code=400, detail=f"Maximum {GROUP_MAX_MEMBERS} membres par groupe")

    # Check if already member
    if any(m["user_id"] == body.email for m in group.get("members", [])):
        raise HTTPException(status_code=400, detail="Déjà membre du groupe")

    # Check if already invited (pending)
    if any(i["email"] == body.email and i["status"] == "pending" for i in group.get("invites", [])):
        raise HTTPException(status_code=400, detail="Invitation déjà envoyée")

    now = datetime.now(timezone.utc)
    invite = {
        "invite_id": f"ginv_{uuid.uuid4().hex[:12]}",
        "email": body.email,
        "inviter_name": user.get("name", ""),
        "status": "pending",
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(days=7)).isoformat(),
    }

    await db.groups.update_one(
        {"group_id": group_id},
        {"$push": {"invites": invite}}
    )

    # If the invitee already has an account, create a notification
    invitee = await db.users.find_one({"email": body.email}, {"user_id": 1})
    if invitee:
        await db.notifications.insert_one({
            "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
            "user_id": invitee["user_id"],
            "type": "group_invite",
            "title": "Invitation à un groupe",
            "message": f"""{user.get("name", "Quelqu'un")} t'invite à rejoindre « {group['name']} »""",
            "icon": "users",
            "data": {"group_id": group_id, "invite_id": invite["invite_id"]},
            "read": False,
            "created_at": now.isoformat(),
        })
        try:
            await send_push_to_user(
                invitee["user_id"],
                "Invitation à un groupe",
                f"""{user.get("name", "Quelqu'un")} t'invite à rejoindre « {group['name']} »""",
                url="/groups",
                tag="group-invite",
            )
        except Exception:
            pass  # Push is best-effort, never blocks
        try:
            inviter_name = user.get("display_name") or user.get("name", "Quelqu'un")
            subject, html = email_group_invite(inviter_name, group["name"])
            await send_email_to_user(invitee["user_id"], subject, html, email_category="social")
        except Exception:
            pass

    return {"message": "Invitation envoyée", "invite_id": invite["invite_id"]}


@router.post("/groups/{group_id}/join")
async def join_group(group_id: str, user: dict = Depends(get_current_user)):
    """Accept an invitation and join a group."""
    group = await db.groups.find_one({"group_id": group_id, "status": "active"})
    if not group:
        raise HTTPException(status_code=404, detail="Groupe introuvable")

    # Check if already a member
    if any(m["user_id"] == user["user_id"] for m in group.get("members", [])):
        raise HTTPException(status_code=400, detail="Déjà membre de ce groupe")

    # Check pending invite for this user
    email = user.get("email", "")
    invite_found = False
    for inv in group.get("invites", []):
        if inv["email"] == email and inv["status"] == "pending":
            invite_found = True
            break

    if not invite_found:
        raise HTTPException(status_code=403, detail="Aucune invitation en attente pour ce compte")

    if len(group.get("members", [])) >= GROUP_MAX_MEMBERS:
        raise HTTPException(status_code=400, detail="Groupe complet")

    now = datetime.now(timezone.utc).isoformat()

    # Add member + mark invite as accepted (atomic)
    await db.groups.update_one(
        {"group_id": group_id, "invites.email": email, "invites.status": "pending"},
        {
            "$push": {"members": {
                "user_id": user["user_id"],
                "name": user.get("name", ""),
                "role": "member",
                "joined_at": now,
                "stats": {
                    "streak_days": user.get("streak_days", 0),
                    "total_time_invested": user.get("total_time_invested", 0),
                    "week_minutes": 0, "week_sessions": 0,
                },
            }},
            "$set": {"invites.$[inv].status": "accepted"},
        },
        array_filters=[{"inv.email": email, "inv.status": "pending"}],
    )

    # Notify group owner
    await db.notifications.insert_one({
        "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
        "user_id": group["owner_id"],
        "type": "group_member_joined",
        "title": "Nouveau membre",
        "message": f"""{user.get("name", "Quelqu'un")} a rejoint « {group['name']} »""",
        "icon": "user-plus",
        "read": False,
        "created_at": now,
    })

    return {"message": f"Bienvenue dans « {group['name']} » !"}


@router.post("/groups/{group_id}/leave")
async def leave_group(group_id: str, user: dict = Depends(get_current_user)):
    """Leave a group. Owner cannot leave — must archive instead."""
    group = await db.groups.find_one(
        {"group_id": group_id, "members.user_id": user["user_id"], "status": "active"}
    )
    if not group:
        raise HTTPException(status_code=404, detail="Groupe introuvable")

    if group["owner_id"] == user["user_id"]:
        raise HTTPException(status_code=400, detail="Le créateur ne peut pas quitter le groupe. Utilisez l'archivage.")

    await db.groups.update_one(
        {"group_id": group_id},
        {"$pull": {"members": {"user_id": user["user_id"]}}}
    )
    return {"message": "Vous avez quitté le groupe"}


@router.delete("/groups/{group_id}")
async def archive_group(group_id: str, user: dict = Depends(get_current_user)):
    """Archive a group (owner only). Soft delete — never hard delete."""
    group = await db.groups.find_one({"group_id": group_id, "status": "active"})
    if not group:
        raise HTTPException(status_code=404, detail="Groupe introuvable")
    if group["owner_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Seul le créateur peut archiver le groupe")

    await db.groups.update_one(
        {"group_id": group_id},
        {"$set": {"status": "archived", "archived_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "Groupe archivé"}


@router.get("/groups/{group_id}/feed")
async def get_group_feed(group_id: str, user: dict = Depends(get_current_user)):
    """Get recent activity feed for a group — last 7 days of sessions from all members.
    Pattern: Strava Club activity feed — chronological, lightweight."""
    group = await db.groups.find_one(
        {"group_id": group_id, "members.user_id": user["user_id"], "status": "active"}
    )
    if not group:
        raise HTTPException(status_code=404, detail="Groupe introuvable")

    member_ids = [m["user_id"] for m in group.get("members", [])]
    member_names = {m["user_id"]: m["name"] for m in group["members"]}
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

    sessions = await db.user_sessions_history.find(
        {"user_id": {"$in": member_ids}, "completed": True, "completed_at": {"$gte": week_ago}},
        {"_id": 0, "user_id": 1, "action_title": 1, "category": 1, "actual_duration": 1, "completed_at": 1}
    ).sort("completed_at", -1).limit(50).to_list(50)

    # Enrich with member name (never expose user_id to frontend)
    feed = []
    for s in sessions:
        feed.append({
            "member_name": member_names.get(s["user_id"], "Membre"),
            "action_title": s.get("action_title", "Session"),
            "category": s.get("category", ""),
            "duration": s.get("actual_duration", 0),
            "completed_at": s.get("completed_at", ""),
        })

    return {"feed": feed, "group_name": group["name"]}


# ============== SHARE PROGRESSION (D.2) ==============

SHARE_TYPES = {"weekly_recap", "milestone", "badge", "objective"}
SHARE_TTL_DAYS = 90  # Auto-cleanup after 90 days

@router.post("/share/create")
@limiter.limit("10/minute")
async def create_share(request: Request, body: ShareCreate, user: dict = Depends(get_current_user)):
    """Create an immutable snapshot of user progression for sharing.
    Returns a share_id that can be used to view the public share page.
    Pattern: Spotify Wrapped / Strava Activity Cards — snapshot at creation time."""
    user_id = user["user_id"]

    if body.share_type not in SHARE_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid share_type. Must be one of: {', '.join(SHARE_TYPES)}")

    now = datetime.now(timezone.utc)
    today = now.date()
    today_iso = today.isoformat()
    week_start = (today - timedelta(days=today.weekday())).isoformat()

    # -- Snapshot: core stats --
    total_sessions = await db.user_sessions_history.count_documents(
        {"user_id": user_id, "completed": True}
    )

    week_sessions = await db.user_sessions_history.find(
        {"user_id": user_id, "completed": True, "completed_at": {"$gte": week_start}},
        {"_id": 0, "actual_duration": 1, "category": 1, "completed_at": 1}
    ).to_list(200)

    week_minutes = sum(s.get("actual_duration", 0) for s in week_sessions)
    week_count = len(week_sessions)

    week_by_day = {}
    for s in week_sessions:
        day = s.get("completed_at", "")[:10]
        if day:
            week_by_day[day] = week_by_day.get(day, 0) + s.get("actual_duration", 0)

    # -- Snapshot: objectives --
    obj_filter = {"user_id": user_id, "status": "active", "deleted": {"$ne": True}}
    if body.objective_id:
        obj_filter["objective_id"] = body.objective_id

    objectives = await db.objectives.find(
        obj_filter,
        {"_id": 0, "objective_id": 1, "title": 1, "current_day": 1, "streak_days": 1,
         "total_sessions": 1, "total_minutes": 1, "curriculum": 1, "category": 1}
    ).to_list(20)

    obj_snapshots = []
    for obj in objectives:
        curriculum = obj.get("curriculum", [])
        total_completed = sum(1 for s in curriculum if s.get("completed"))
        total_steps = len(curriculum)
        obj_snapshots.append({
            "objective_id": obj["objective_id"],
            "title": obj["title"],
            "category": obj.get("category", ""),
            "streak_days": obj.get("streak_days", 0),
            "progress_percent": round((total_completed / max(total_steps, 1)) * 100),
            "total_completed": total_completed,
            "total_steps": total_steps,
            "total_minutes": obj.get("total_minutes", 0),
        })

    # -- Snapshot: badges --
    user_badges = user.get("badges", [])

    # -- Build share document --
    share_id = secrets.token_urlsafe(12)  # 16 chars, 96 bits entropy (Bitly-grade)

    share_doc = {
        "share_id": share_id,
        "user_id": user_id,
        "share_type": body.share_type,
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(days=SHARE_TTL_DAYS)).isoformat(),
        "author": {
            "name": user.get("name", "Utilisateur InFinea"),
            "subscription_tier": user.get("subscription_tier", "free"),
        },
        "snapshot": {
            "streak_days": user.get("streak_days", 0),
            "total_time_invested": user.get("total_time_invested", 0),
            "total_sessions": total_sessions,
            "week": {
                "sessions": week_count,
                "minutes": week_minutes,
                "by_day": week_by_day,
            },
            "objectives": obj_snapshots,
            "badges_count": len(user_badges),
            "recent_badges": user_badges[-3:] if user_badges else [],
        },
    }

    await db.shares.insert_one(share_doc)

    return {
        "share_id": share_id,
        "share_url": f"/p/{share_id}",
        "expires_at": share_doc["expires_at"],
    }


@public_router.get("/share/{share_id}")
@limiter.limit("30/minute")
async def get_public_share(share_id: str, request: Request):
    """Public endpoint — no auth required. Returns the share snapshot for display.
    Route is on public_router (not router) for clean public URLs."""
    share = await db.shares.find_one(
        {"share_id": share_id},
        {"_id": 0, "user_id": 0}  # Never expose internal user_id publicly
    )
    if not share:
        raise HTTPException(status_code=404, detail="Share not found or expired")

    # Check expiration
    expires_at = share.get("expires_at", "")
    if expires_at and expires_at < datetime.now(timezone.utc).isoformat():
        raise HTTPException(status_code=410, detail="This share has expired")

    return share
