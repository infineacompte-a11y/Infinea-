"""
InFinea — Collaborative Challenge routes.
Duo, group, and community challenges with real-time progress.

Design:
- Templates for one-click launch (curated, proven engagement patterns).
- Custom challenge creation for power users.
- Auto-start when minimum participants join.
- Progress updates event-driven from session completions.
- Leaderboard computed per challenge.
- Feed integration: challenge milestones appear in activity feed.

Benchmarked: Strava challenges, Duolingo friend quests, Nike Run Club.
"""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from typing import Optional

from database import db
from auth import get_current_user
from models import ChallengeCreate, ChallengeFromTemplate, ChallengeInvite
from services.challenge_service import (
    CHALLENGE_TEMPLATES,
    get_template,
    create_challenge_from_template,
    create_custom_challenge,
    join_challenge,
    get_leaderboard,
    _send_challenge_invite,
)

router = APIRouter(prefix="/api")


# ============== TEMPLATES ==============


@router.get("/challenges/templates")
async def list_templates(user: dict = Depends(get_current_user)):
    """Get all available challenge templates."""
    return {"templates": CHALLENGE_TEMPLATES}


@router.post("/challenges/from-template")
async def launch_from_template(
    data: ChallengeFromTemplate,
    user: dict = Depends(get_current_user),
):
    """Launch a challenge from a curated template."""
    template = get_template(data.template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    challenge = await create_challenge_from_template(
        template_id=data.template_id,
        creator_id=user["user_id"],
        invited_user_ids=data.invited_user_ids,
    )

    if not challenge:
        raise HTTPException(status_code=500, detail="Failed to create challenge")

    challenge.pop("_id", None)
    return challenge


# ============== CUSTOM CREATION ==============


@router.post("/challenges")
async def create_challenge(
    data: ChallengeCreate,
    user: dict = Depends(get_current_user),
):
    """Create a fully custom challenge."""
    challenge = await create_custom_challenge(
        creator_id=user["user_id"],
        title=data.title,
        description=data.description,
        challenge_type=data.challenge_type,
        category=data.category,
        goal_type=data.goal_type,
        goal_value=data.goal_value,
        duration_days=data.duration_days,
        max_participants=data.max_participants,
        privacy=data.privacy,
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
        raise HTTPException(status_code=404, detail="Challenge not found")

    if challenge["created_by"] == user["user_id"]:
        raise HTTPException(
            status_code=400,
            detail="Creator cannot leave. Cancel the challenge instead.",
        )

    result = await db.challenges.update_one(
        {
            "challenge_id": challenge_id,
            "participants.user_id": user["user_id"],
        },
        {"$set": {"participants.$.status": "left"}},
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Not a participant")

    return {"message": "Left challenge"}


# ============== INVITATIONS ==============


@router.post("/challenges/{challenge_id}/invite")
async def invite_to_challenge(
    challenge_id: str,
    invite: ChallengeInvite,
    user: dict = Depends(get_current_user),
):
    """Invite users to a challenge."""
    challenge = await db.challenges.find_one({"challenge_id": challenge_id})
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    if challenge["status"] not in ("pending", "active"):
        raise HTTPException(status_code=400, detail="Challenge is not open")

    # Only creator or participants can invite
    participant_ids = [p["user_id"] for p in challenge["participants"]]
    if user["user_id"] not in participant_ids:
        raise HTTPException(status_code=403, detail="Only participants can invite")

    sent = 0
    for uid in invite.user_ids:
        if uid in participant_ids:
            continue  # Skip existing participants
        await _send_challenge_invite(challenge_id, user["user_id"], uid)
        sent += 1

    return {"message": f"Sent {sent} invitation(s)", "sent": sent}


@router.get("/challenges/invites")
async def get_my_invites(user: dict = Depends(get_current_user)):
    """Get pending challenge invitations for the current user."""
    invites = (
        await db.challenge_invites.find(
            {"user_id": user["user_id"], "status": "pending"},
            {"_id": 0},
        )
        .sort("created_at", -1)
        .to_list(50)
    )

    # Enrich with challenge info
    for inv in invites:
        challenge = await db.challenges.find_one(
            {"challenge_id": inv["challenge_id"]},
            {"_id": 0, "title": 1, "description": 1, "challenge_type": 1,
             "category": 1, "goal_type": 1, "goal_value": 1, "icon": 1,
             "participants": 1, "duration_days": 1},
        )
        if challenge:
            inv["challenge"] = challenge
            inv["challenge"]["participant_count"] = len(challenge.get("participants", []))
            inv["challenge"].pop("participants", None)

    return {"invites": invites, "count": len(invites)}


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
        raise HTTPException(status_code=404, detail="Invite not found")

    return {"message": "Invite declined"}


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
        "participants.user_id": {"$ne": user["user_id"]},  # Exclude already joined
    }
    if category and category != "all":
        query["category"] = category

    challenges = (
        await db.challenges.find(query, {"_id": 0})
        .sort("created_at", -1)
        .limit(limit)
        .to_list(limit)
    )

    # Add participant count without exposing full participant list
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
        raise HTTPException(status_code=404, detail="Challenge not found")

    # Check access: participants can see everything, others see public only
    participant_ids = [p["user_id"] for p in challenge["participants"]]
    is_participant = user["user_id"] in participant_ids

    if not is_participant and challenge["privacy"] == "invite_only":
        raise HTTPException(status_code=403, detail="This challenge is invite-only")

    # Enrich participants with user info
    user_ids = [p["user_id"] for p in challenge["participants"]]
    users = await db.users.find(
        {"user_id": {"$in": user_ids}},
        {"_id": 0, "user_id": 1, "name": 1, "display_name": 1, "avatar_url": 1, "picture": 1},
    ).to_list(len(user_ids))
    user_map = {u["user_id"]: u for u in users}

    for p in challenge["participants"]:
        u = user_map.get(p["user_id"], {})
        p["display_name"] = u.get("display_name", u.get("name", "Utilisateur"))
        p["avatar_url"] = u.get("avatar_url", u.get("picture"))

    # Compute leaderboard
    challenge["leaderboard"] = get_leaderboard(challenge["participants"])

    # Progress percentage
    goal = challenge["goal_value"]
    if goal > 0:
        challenge["progress_percent"] = min(
            100, round(challenge.get("total_progress", 0) / goal * 100, 1)
        )
    else:
        challenge["progress_percent"] = 0

    challenge["is_participant"] = is_participant

    return challenge


# ============== CANCEL ==============


@router.delete("/challenges/{challenge_id}")
async def cancel_challenge(
    challenge_id: str,
    user: dict = Depends(get_current_user),
):
    """Cancel a challenge (creator only, only if pending)."""
    challenge = await db.challenges.find_one({"challenge_id": challenge_id})
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    if challenge["created_by"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Only the creator can cancel")

    if challenge["status"] not in ("pending",):
        raise HTTPException(
            status_code=400,
            detail="Can only cancel pending challenges",
        )

    await db.challenges.update_one(
        {"challenge_id": challenge_id},
        {"$set": {"status": "cancelled"}},
    )

    # Clean up invites
    await db.challenge_invites.update_many(
        {"challenge_id": challenge_id, "status": "pending"},
        {"$set": {"status": "cancelled"}},
    )

    return {"message": "Challenge cancelled"}
