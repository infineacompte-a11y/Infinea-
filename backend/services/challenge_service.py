"""
InFinea — Challenge Service.
Templates, progress tracking, lifecycle management, leaderboard computation.

Architecture:
- Progress updates are triggered by session completions (event-driven).
- No polling, no cron — progress is computed at write time.
- Challenge completion triggers celebration activity in the feed.
- Templates provide curated, one-click challenge creation.

Benchmarked: Strava challenges, Duolingo friend quests, Nike Run Club groups.
"""

import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from database import db

logger = logging.getLogger(__name__)


# ============== CHALLENGE TEMPLATES ==============

CHALLENGE_TEMPLATES = [
    # -- Duo challenges (2 people, short, high accountability) --
    {
        "template_id": "duo_discovery",
        "title": "Duo Découverte",
        "description": "Complétez 5 micro-actions ensemble cette semaine.",
        "challenge_type": "duo",
        "category": "mixed",
        "goal_type": "sessions",
        "goal_value": 5,
        "duration_days": 7,
        "max_participants": 2,
        "icon": "users",
        "difficulty": "easy",
    },
    {
        "template_id": "duo_focus",
        "title": "Duo Focus",
        "description": "30 minutes de productivité à deux en 5 jours.",
        "challenge_type": "duo",
        "category": "productivity",
        "goal_type": "time",
        "goal_value": 30,
        "duration_days": 5,
        "max_participants": 2,
        "icon": "target",
        "difficulty": "medium",
    },
    {
        "template_id": "duo_streak",
        "title": "Duo Régularité",
        "description": "Maintenez un streak de 5 jours ensemble.",
        "challenge_type": "duo",
        "category": "mixed",
        "goal_type": "streak",
        "goal_value": 5,
        "duration_days": 7,
        "max_participants": 2,
        "icon": "flame",
        "difficulty": "hard",
    },
    # -- Group challenges (3-10, team dynamic) --
    {
        "template_id": "group_active_week",
        "title": "Semaine Active",
        "description": "L'équipe accumule 60 minutes de micro-actions en une semaine.",
        "challenge_type": "group",
        "category": "mixed",
        "goal_type": "time",
        "goal_value": 60,
        "duration_days": 7,
        "max_participants": 10,
        "icon": "clock",
        "difficulty": "medium",
    },
    {
        "template_id": "group_productivity_sprint",
        "title": "Sprint Productivité",
        "description": "15 actions de productivité en équipe sur 5 jours.",
        "challenge_type": "group",
        "category": "productivity",
        "goal_type": "sessions",
        "goal_value": 15,
        "duration_days": 5,
        "max_participants": 10,
        "icon": "zap",
        "difficulty": "medium",
    },
    {
        "template_id": "group_learning_marathon",
        "title": "Marathon Apprentissage",
        "description": "20 sessions d'apprentissage en équipe sur 2 semaines.",
        "challenge_type": "group",
        "category": "learning",
        "goal_type": "sessions",
        "goal_value": 20,
        "duration_days": 14,
        "max_participants": 10,
        "icon": "book-open",
        "difficulty": "hard",
    },
    # -- Community challenges (open, viral) --
    {
        "template_id": "community_zen",
        "title": "Zen Challenge",
        "description": "La communauté accumule 100 sessions de bien-être cette semaine.",
        "challenge_type": "community",
        "category": "well_being",
        "goal_type": "sessions",
        "goal_value": 100,
        "duration_days": 7,
        "max_participants": None,
        "icon": "heart",
        "difficulty": "community",
    },
    {
        "template_id": "community_1000_minutes",
        "title": "1000 Minutes",
        "description": "Ensemble, accumulons 1000 minutes de micro-actions ce mois-ci !",
        "challenge_type": "community",
        "category": "mixed",
        "goal_type": "time",
        "goal_value": 1000,
        "duration_days": 30,
        "max_participants": None,
        "icon": "trophy",
        "difficulty": "community",
    },
]


def get_template(template_id: str) -> Optional[dict]:
    """Get a challenge template by ID."""
    return next((t for t in CHALLENGE_TEMPLATES if t["template_id"] == template_id), None)


async def create_challenge_from_template(
    template_id: str,
    creator_id: str,
    invited_user_ids: list = None,
) -> Optional[dict]:
    """Create a challenge from a template."""
    template = get_template(template_id)
    if not template:
        return None

    now = datetime.now(timezone.utc)
    challenge_id = f"chal_{uuid.uuid4().hex[:12]}"

    doc = {
        "challenge_id": challenge_id,
        "template_id": template_id,
        "title": template["title"],
        "description": template["description"],
        "challenge_type": template["challenge_type"],
        "category": template["category"],
        "goal_type": template["goal_type"],
        "goal_value": template["goal_value"],
        "icon": template["icon"],
        "created_by": creator_id,
        "max_participants": template["max_participants"],
        "privacy": "invite_only" if template["challenge_type"] == "duo" else "public",
        "status": "pending",
        "start_date": None,
        "end_date": None,
        "duration_days": template["duration_days"],
        "participants": [{
            "user_id": creator_id,
            "joined_at": now.isoformat(),
            "progress": 0,
            "status": "active",
        }],
        "total_progress": 0,
        "created_at": now.isoformat(),
        "completed_at": None,
    }

    await db.challenges.insert_one(doc)

    if invited_user_ids:
        for uid in invited_user_ids:
            if uid != creator_id:
                await send_challenge_invite(challenge_id, creator_id, uid)

    return doc


async def create_custom_challenge(
    creator_id: str, title: str, description: str,
    challenge_type: str, category: str,
    goal_type: str, goal_value: int, duration_days: int,
    max_participants: int = None, privacy: str = "invite_only",
) -> dict:
    """Create a fully custom challenge."""
    now = datetime.now(timezone.utc)
    challenge_id = f"chal_{uuid.uuid4().hex[:12]}"

    if max_participants is None:
        if challenge_type == "duo":
            max_participants = 2
        elif challenge_type == "group":
            max_participants = 10

    icon_map = {"learning": "book-open", "productivity": "target",
                "well_being": "heart", "mixed": "sparkles"}

    doc = {
        "challenge_id": challenge_id,
        "template_id": None,
        "title": title,
        "description": description,
        "challenge_type": challenge_type,
        "category": category,
        "goal_type": goal_type,
        "goal_value": goal_value,
        "icon": icon_map.get(category, "sparkles"),
        "created_by": creator_id,
        "max_participants": max_participants,
        "privacy": privacy,
        "status": "pending",
        "start_date": None,
        "end_date": None,
        "duration_days": duration_days,
        "participants": [{
            "user_id": creator_id,
            "joined_at": now.isoformat(),
            "progress": 0,
            "status": "active",
        }],
        "total_progress": 0,
        "created_at": now.isoformat(),
        "completed_at": None,
    }

    await db.challenges.insert_one(doc)
    return doc


async def join_challenge(challenge_id: str, user_id: str) -> dict:
    """Join a challenge. Auto-starts when minimum participants are met."""
    challenge = await db.challenges.find_one({"challenge_id": challenge_id})
    if not challenge:
        return {"joined": False, "message": "Défi introuvable"}

    if challenge["status"] not in ("pending", "active"):
        return {"joined": False, "message": "Ce défi n'est plus ouvert"}

    participant_ids = [p["user_id"] for p in challenge["participants"]]
    if user_id in participant_ids:
        return {"joined": False, "message": "Vous participez déjà"}

    max_p = challenge.get("max_participants")
    if max_p and len(challenge["participants"]) >= max_p:
        return {"joined": False, "message": "Ce défi est complet"}

    # Check invitation requirement
    if challenge["privacy"] == "invite_only":
        invite = await db.challenge_invites.find_one({
            "challenge_id": challenge_id,
            "user_id": user_id,
            "status": "pending",
        })
        if not invite:
            return {"joined": False, "message": "Invitation requise"}
        await db.challenge_invites.update_one(
            {"_id": invite["_id"]}, {"$set": {"status": "accepted"}}
        )

    now = datetime.now(timezone.utc)
    await db.challenges.update_one(
        {"challenge_id": challenge_id},
        {"$push": {"participants": {
            "user_id": user_id,
            "joined_at": now.isoformat(),
            "progress": 0,
            "status": "active",
        }}},
    )

    # Auto-start logic
    started = False
    updated = await db.challenges.find_one({"challenge_id": challenge_id})
    if updated["status"] == "pending" and len(updated["participants"]) >= 2:
        end_date = now + timedelta(days=challenge["duration_days"])
        await db.challenges.update_one(
            {"challenge_id": challenge_id},
            {"$set": {
                "status": "active",
                "start_date": now.isoformat(),
                "end_date": end_date.isoformat(),
            }},
        )
        started = True

    return {"joined": True, "started": started, "message": "Vous avez rejoint le défi !"}


async def update_challenge_progress(user_id: str, session_data: dict):
    """
    Called after a session is completed.
    Updates progress for ALL active challenges the user participates in.
    Event-driven — no polling needed.
    """
    active_challenges = await db.challenges.find({
        "status": "active",
        "participants": {"$elemMatch": {"user_id": user_id, "status": "active"}},
    }).to_list(50)

    for challenge in active_challenges:
        # Check category match
        if challenge["category"] != "mixed":
            if session_data.get("category") != challenge["category"]:
                continue

        if challenge["goal_type"] == "streak":
            user = await db.users.find_one({"user_id": user_id}, {"streak_days": 1})
            streak = user.get("streak_days", 0) if user else 0
            await db.challenges.update_one(
                {"challenge_id": challenge["challenge_id"], "participants.user_id": user_id},
                {"$set": {"participants.$.progress": streak}},
            )
            await _recompute_total(challenge["challenge_id"])
            await _check_completion(challenge["challenge_id"])
            continue

        increment = 0
        if challenge["goal_type"] == "sessions":
            increment = 1
        elif challenge["goal_type"] == "time":
            increment = session_data.get("actual_duration", 0)

        if increment <= 0:
            continue

        await db.challenges.update_one(
            {"challenge_id": challenge["challenge_id"], "participants.user_id": user_id},
            {"$inc": {"participants.$.progress": increment, "total_progress": increment}},
        )
        await _check_completion(challenge["challenge_id"])


async def _recompute_total(challenge_id: str):
    """Recompute total progress from all participants."""
    ch = await db.challenges.find_one({"challenge_id": challenge_id})
    if not ch:
        return
    total = sum(p.get("progress", 0) for p in ch["participants"])
    await db.challenges.update_one(
        {"challenge_id": challenge_id}, {"$set": {"total_progress": total}}
    )


async def _check_completion(challenge_id: str):
    """Check if a challenge has been completed and handle celebration."""
    ch = await db.challenges.find_one({"challenge_id": challenge_id})
    if not ch or ch["status"] != "active":
        return

    goal = ch["goal_value"]
    if ch["goal_type"] == "streak":
        completed = any(
            p.get("progress", 0) >= goal
            for p in ch["participants"] if p["status"] == "active"
        )
    else:
        completed = ch.get("total_progress", 0) >= goal

    if not completed:
        return

    now = datetime.now(timezone.utc).isoformat()
    await db.challenges.update_one(
        {"challenge_id": challenge_id},
        {"$set": {"status": "completed", "completed_at": now}},
    )

    # Celebrate: notify all participants + feed activities
    try:
        from services.activity_service import create_activity
    except ImportError:
        return

    for p in ch["participants"]:
        if p["status"] != "active":
            continue
        uid = p["user_id"]

        try:
            await db.notifications.insert_one({
                "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
                "user_id": uid,
                "type": "challenge_completed",
                "message": f"Défi \"{ch['title']}\" réussi ! Bravo à toute l'équipe !",
                "data": {"challenge_id": challenge_id},
                "read": False,
                "created_at": now,
            })
            await create_activity(
                user_id=uid,
                activity_type="challenge_completed",
                data={
                    "challenge_title": ch["title"],
                    "challenge_type": ch["challenge_type"],
                    "challenge_id": challenge_id,
                    "participant_count": len([pp for pp in ch["participants"] if pp["status"] == "active"]),
                },
                visibility="followers",
            )
        except Exception:
            logger.exception(f"Failed to celebrate challenge for {uid}")


async def send_challenge_invite(challenge_id: str, sender_id: str, target_id: str):
    """Send a challenge invitation with notification."""
    existing = await db.challenge_invites.find_one({
        "challenge_id": challenge_id, "user_id": target_id, "status": "pending",
    })
    if existing:
        return

    sender = await db.users.find_one({"user_id": sender_id}, {"name": 1, "display_name": 1})
    sender_name = (sender.get("display_name") or sender.get("name", "Quelqu'un")) if sender else "Quelqu'un"
    challenge = await db.challenges.find_one({"challenge_id": challenge_id}, {"title": 1})
    title = challenge.get("title", "un défi") if challenge else "un défi"

    now = datetime.now(timezone.utc).isoformat()

    await db.challenge_invites.insert_one({
        "invite_id": f"chinv_{uuid.uuid4().hex[:12]}",
        "challenge_id": challenge_id,
        "sender_id": sender_id,
        "user_id": target_id,
        "status": "pending",
        "created_at": now,
    })

    await db.notifications.insert_one({
        "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
        "user_id": target_id,
        "type": "challenge_invite",
        "message": f"{sender_name} vous invite à rejoindre \"{title}\"",
        "data": {"challenge_id": challenge_id, "sender_id": sender_id},
        "read": False,
        "created_at": now,
    })


def get_leaderboard(participants: list) -> list:
    """Compute leaderboard from participant progress."""
    ranked = sorted(
        [p for p in participants if p.get("status") == "active"],
        key=lambda p: p.get("progress", 0),
        reverse=True,
    )
    for i, p in enumerate(ranked):
        p["rank"] = i + 1
    return ranked
