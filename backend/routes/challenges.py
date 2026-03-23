"""
InFinea — Collaborative Challenge routes.
Templates, duo/group/community challenges, invitations, leaderboard.

Design:
- Templates for one-click launch (curated engagement patterns).
- Custom challenge creation for power users.
- Auto-start when minimum participants join.
- Progress updates event-driven from session completions.
- Leaderboard computed per challenge.

Benchmarked: Strava challenges, Duolingo friend quests, Nike Run Club.
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Optional

from database import db
from auth import get_current_user
from services.challenge_service import (
    CHALLENGE_TEMPLATES,
    get_template,
    create_challenge_from_template,
    create_custom_challenge,
    join_challenge,
    get_leaderboard,
    send_challenge_invite,
)

router = APIRouter()

VALID_TYPES = {"duo", "group", "community"}
VALID_CATEGORIES = {"learning", "productivity", "well_being", "mixed"}
VALID_GOALS = {"sessions", "time", "streak"}


# ============== TEMPLATES ==============

@router.get("/challenges/templates")
async def list_templates(user: dict = Depends(get_current_user)):
    """Get all available challenge templates."""
    return {"templates": CHALLENGE_TEMPLATES}


@router.post("/challenges/from-template")
async def launch_from_template(
    request: Request,
    user: dict = Depends(get_current_user),
):
    """Launch a challenge from a curated template."""
    body = await request.json()
    template_id = body.get("template_id")
    if not template_id or not get_template(template_id):
        raise HTTPException(status_code=404, detail="Template introuvable")

    invited = body.get("invited_user_ids", [])
    challenge = await create_challenge_from_template(
        template_id=template_id,
        creator_id=user["user_id"],
        invited_user_ids=invited,
    )
    if not challenge:
        raise HTTPException(status_code=500, detail="Erreur de création")

    challenge.pop("_id", None)
    return challenge


# ============== CUSTOM CREATION ==============

@router.post("/challenges")
async def create_challenge(
    request: Request,
    user: dict = Depends(get_current_user),
):
    """Create a fully custom challenge."""
    body = await request.json()

    title = str(body.get("title", "")).strip()
    if not title or len(title) > 100:
        raise HTTPException(status_code=400, detail="Titre requis (max 100 car.)")

    challenge_type = body.get("challenge_type")
    if challenge_type not in VALID_TYPES:
        raise HTTPException(status_code=400, detail=f"Type invalide : {', '.join(VALID_TYPES)}")

    category = body.get("category", "mixed")
    if category not in VALID_CATEGORIES:
        category = "mixed"

    goal_type = body.get("goal_type")
    if goal_type not in VALID_GOALS:
        raise HTTPException(status_code=400, detail=f"Objectif invalide : {', '.join(VALID_GOALS)}")

    goal_value = int(body.get("goal_value", 0))
    if goal_value <= 0 or goal_value > 10000:
        raise HTTPException(status_code=400, detail="Valeur objectif entre 1 et 10000")

    duration_days = int(body.get("duration_days", 7))
    if duration_days <= 0 or duration_days > 90:
        raise HTTPException(status_code=400, detail="Durée entre 1 et 90 jours")

    challenge = await create_custom_challenge(
        creator_id=user["user_id"],
        title=title,
        description=str(body.get("description", "")).strip()[:500],
        challenge_type=challenge_type,
        category=category,
        goal_type=goal_type,
        goal_value=goal_value,
        duration_days=duration_days,
        max_participants=body.get("max_participants"),
        privacy=body.get("privacy", "invite_only"),
    )

    challenge.pop("_id", None)
    return challenge


# ============== JOIN & LEAVE ==============

@router.post("/challenges/{challenge_id}/join")
async def join_challenge_route(
    challenge_id: str,
    user: dict = Depends(get_current_user),
):
    """Join a challenge."""
    result = await join_challenge(challenge_id, user["user_id"])
    if not result["joined"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/challenges/{challenge_id}/leave")
async def leave_challenge(
    challenge_id: str,
    user: dict = Depends(get_current_user),
):
    """Leave a challenge (mark participant as inactive)."""
    challenge = await db.challenges.find_one({"challenge_id": challenge_id})
    if not challenge:
        raise HTTPException(status_code=404, detail="Défi introuvable")

    if challenge["created_by"] == user["user_id"]:
        raise HTTPException(status_code=400, detail="Le créateur ne peut pas quitter. Annulez le défi à la place.")

    result = await db.challenges.update_one(
        {"challenge_id": challenge_id, "participants.user_id": user["user_id"]},
        {"$set": {"participants.$.status": "left"}},
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Vous ne participez pas à ce défi")

    return {"message": "Vous avez quitté le défi"}


# ============== INVITATIONS ==============

@router.post("/challenges/{challenge_id}/invite")
async def invite_to_challenge(
    challenge_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    """Invite users to a challenge."""
    body = await request.json()
    user_ids = body.get("user_ids", [])
    if not user_ids:
        raise HTTPException(status_code=400, detail="Aucun utilisateur à inviter")

    challenge = await db.challenges.find_one({"challenge_id": challenge_id})
    if not challenge:
        raise HTTPException(status_code=404, detail="Défi introuvable")
    if challenge["status"] not in ("pending", "active"):
        raise HTTPException(status_code=400, detail="Ce défi n'est plus ouvert")

    participant_ids = [p["user_id"] for p in challenge["participants"]]
    if user["user_id"] not in participant_ids:
        raise HTTPException(status_code=403, detail="Seuls les participants peuvent inviter")

    sent = 0
    for uid in user_ids:
        if uid in participant_ids or uid == user["user_id"]:
            continue
        await send_challenge_invite(challenge_id, user["user_id"], uid)
        sent += 1

    return {"message": f"{sent} invitation(s) envoyée(s)", "sent": sent}


@router.get("/challenges/invites")
async def get_my_invites(user: dict = Depends(get_current_user)):
    """Get pending challenge invitations."""
    invites = (
        await db.challenge_invites.find(
            {"user_id": user["user_id"], "status": "pending"}, {"_id": 0}
        ).sort("created_at", -1).to_list(50)
    )

    for inv in invites:
        ch = await db.challenges.find_one(
            {"challenge_id": inv["challenge_id"]},
            {"_id": 0, "title": 1, "description": 1, "challenge_type": 1,
             "category": 1, "goal_type": 1, "goal_value": 1, "icon": 1,
             "participants": 1, "duration_days": 1},
        )
        if ch:
            inv["challenge"] = {
                **{k: v for k, v in ch.items() if k != "participants"},
                "participant_count": len(ch.get("participants", [])),
            }

    return {"invites": invites, "count": len(invites)}


@router.post("/challenges/invites/{invite_id}/accept")
async def accept_invite(
    invite_id: str,
    user: dict = Depends(get_current_user),
):
    """Accept an invitation and join the challenge."""
    invite = await db.challenge_invites.find_one({
        "invite_id": invite_id, "user_id": user["user_id"], "status": "pending",
    })
    if not invite:
        raise HTTPException(status_code=404, detail="Invitation introuvable")

    result = await join_challenge(invite["challenge_id"], user["user_id"])
    if not result["joined"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.post("/challenges/invites/{invite_id}/decline")
async def decline_invite(
    invite_id: str,
    user: dict = Depends(get_current_user),
):
    """Decline a challenge invitation."""
    result = await db.challenge_invites.update_one(
        {"invite_id": invite_id, "user_id": user["user_id"], "status": "pending"},
        {"$set": {"status": "declined"}},
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Invitation introuvable")
    return {"message": "Invitation déclinée"}


# ============== READ & LIST ==============

@router.get("/challenges")
async def list_my_challenges(
    user: dict = Depends(get_current_user),
    status: Optional[str] = None,
):
    """Get challenges the current user participates in."""
    query = {"participants.user_id": user["user_id"]}
    if status:
        query["status"] = status

    challenges = (
        await db.challenges.find(query, {"_id": 0})
        .sort("created_at", -1)
        .to_list(50)
    )

    # Enrich with user info
    for ch in challenges:
        await _enrich_participants(ch)

    return {"challenges": challenges, "count": len(challenges)}


@router.get("/challenges/discover")
async def discover_challenges(
    user: dict = Depends(get_current_user),
    category: Optional[str] = None,
    limit: int = 20,
):
    """Discover public challenges to join."""
    query = {
        "privacy": "public",
        "status": {"$in": ["pending", "active"]},
        "participants.user_id": {"$ne": user["user_id"]},
    }
    if category and category != "all":
        query["category"] = category

    challenges = (
        await db.challenges.find(query, {"_id": 0})
        .sort("created_at", -1)
        .limit(limit)
        .to_list(limit)
    )

    for c in challenges:
        c["participant_count"] = len(c.get("participants", []))
        c.pop("participants", None)

    return {"challenges": challenges, "count": len(challenges)}


@router.get("/challenges/{challenge_id}")
async def get_challenge(
    challenge_id: str,
    user: dict = Depends(get_current_user),
):
    """Get full challenge details with leaderboard."""
    challenge = await db.challenges.find_one(
        {"challenge_id": challenge_id}, {"_id": 0}
    )
    if not challenge:
        raise HTTPException(status_code=404, detail="Défi introuvable")

    participant_ids = [p["user_id"] for p in challenge["participants"]]
    is_participant = user["user_id"] in participant_ids

    if not is_participant and challenge["privacy"] == "invite_only":
        raise HTTPException(status_code=403, detail="Ce défi est sur invitation uniquement")

    await _enrich_participants(challenge)
    challenge["leaderboard"] = get_leaderboard(challenge["participants"])

    goal = challenge["goal_value"]
    challenge["progress_percent"] = (
        min(100, round(challenge.get("total_progress", 0) / goal * 100, 1))
        if goal > 0 else 0
    )
    challenge["is_participant"] = is_participant

    return challenge


# ============== CANCEL ==============

@router.delete("/challenges/{challenge_id}")
async def cancel_challenge(
    challenge_id: str,
    user: dict = Depends(get_current_user),
):
    """Cancel a challenge (creator only, pending only)."""
    challenge = await db.challenges.find_one({"challenge_id": challenge_id})
    if not challenge:
        raise HTTPException(status_code=404, detail="Défi introuvable")
    if challenge["created_by"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Seul le créateur peut annuler")
    if challenge["status"] != "pending":
        raise HTTPException(status_code=400, detail="Seuls les défis en attente peuvent être annulés")

    await db.challenges.update_one(
        {"challenge_id": challenge_id}, {"$set": {"status": "cancelled"}}
    )
    await db.challenge_invites.update_many(
        {"challenge_id": challenge_id, "status": "pending"},
        {"$set": {"status": "cancelled"}},
    )

    return {"message": "Défi annulé"}


# ── Helper ──

async def _enrich_participants(challenge: dict):
    """Enrich participant entries with display info."""
    ids = [p["user_id"] for p in challenge.get("participants", [])]
    if not ids:
        return
    users = await db.users.find(
        {"user_id": {"$in": ids}},
        {"_id": 0, "user_id": 1, "name": 1, "display_name": 1,
         "username": 1, "avatar_url": 1, "picture": 1},
    ).to_list(len(ids))
    user_map = {u["user_id"]: u for u in users}
    for p in challenge["participants"]:
        u = user_map.get(p["user_id"], {})
        p["display_name"] = u.get("display_name") or u.get("name", "Utilisateur")
        p["username"] = u.get("username")
        p["avatar_url"] = u.get("avatar_url") or u.get("picture")
