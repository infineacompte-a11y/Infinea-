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
# Curated challenges users can launch with one click.
# Each template is designed around proven engagement patterns.

CHALLENGE_TEMPLATES = [
    # -- Duo challenges (2 people, short, high accountability) --
    {
        "template_id": "duo_discovery",
        "title": "Duo Decouverte",
        "description": "Completez 5 micro-actions ensemble cette semaine. Un duo, un objectif!",
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
        "description": "30 minutes de productivite a deux en 5 jours. Qui sera le plus assidu?",
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
        "title": "Duo Regularite",
        "description": "Maintenez un streak de 5 jours ensemble. La regularite a deux!",
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
        "description": "L'equipe accumule 60 minutes de micro-actions en une semaine.",
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
        "title": "Sprint Productivite",
        "description": "15 actions de productivite en equipe sur 5 jours. Go!",
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
        "description": "20 sessions d'apprentissage en equipe sur 2 semaines.",
        "challenge_type": "group",
        "category": "learning",
        "goal_type": "sessions",
        "goal_value": 20,
        "duration_days": 14,
        "max_participants": 10,
        "icon": "book-open",
        "difficulty": "hard",
    },
    # -- Community challenges (open, viral, event-driven) --
    {
        "template_id": "community_zen",
        "title": "Zen Challenge",
        "description": "La communaute accumule 100 sessions de bien-etre cette semaine.",
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
        "description": "Ensemble, accumulons 1000 minutes de micro-actions ce mois-ci!",
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
    invited_user_ids: list[str] = None,
) -> dict:
    """Create a challenge from a template."""
    template = get_template(template_id)
    if not template:
        return None

    now = datetime.now(timezone.utc)
    challenge_id = f"chal_{uuid.uuid4().hex[:12]}"

    challenge_doc = {
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
        "start_date": None,  # Set when enough participants join
        "end_date": None,
        "duration_days": template["duration_days"],
        "participants": [
            {
                "user_id": creator_id,
                "joined_at": now.isoformat(),
                "progress": 0,
                "status": "active",
            }
        ],
        "total_progress": 0,
        "created_at": now.isoformat(),
        "completed_at": None,
    }

    await db.challenges.insert_one(challenge_doc)

    # Send invitations
    if invited_user_ids:
        for uid in invited_user_ids:
            if uid == creator_id:
                continue
            await _send_challenge_invite(challenge_id, creator_id, uid)

    return challenge_doc


async def create_custom_challenge(
    creator_id: str,
    title: str,
    description: str,
    challenge_type: str,
    category: str,
    goal_type: str,
    goal_value: int,
    duration_days: int,
    max_participants: int = None,
    privacy: str = "invite_only",
) -> dict:
    """Create a fully custom challenge."""
    now = datetime.now(timezone.utc)
    challenge_id = f"chal_{uuid.uuid4().hex[:12]}"

    # Set defaults for max_participants based on type
    if max_participants is None:
        if challenge_type == "duo":
            max_participants = 2
        elif challenge_type == "group":
            max_participants = 10
        # community = None (unlimited)

    challenge_doc = {
        "challenge_id": challenge_id,
        "template_id": None,
        "title": title,
        "description": description,
        "challenge_type": challenge_type,
        "category": category,
        "goal_type": goal_type,
        "goal_value": goal_value,
        "icon": _get_category_icon(category),
        "created_by": creator_id,
        "max_participants": max_participants,
        "privacy": privacy,
        "status": "pending",
        "start_date": None,
        "end_date": None,
        "duration_days": duration_days,
        "participants": [
            {
                "user_id": creator_id,
                "joined_at": now.isoformat(),
                "progress": 0,
                "status": "active",
            }
        ],
        "total_progress": 0,
        "created_at": now.isoformat(),
        "completed_at": None,
    }

    await db.challenges.insert_one(challenge_doc)
    return challenge_doc


async def join_challenge(challenge_id: str, user_id: str) -> dict:
    """
    Join a challenge. Auto-starts the challenge when minimum participants are met.
    Returns: {"joined": bool, "started": bool, "message": str}
    """
    challenge = await db.challenges.find_one({"challenge_id": challenge_id})
    if not challenge:
        return {"joined": False, "message": "Challenge not found"}

    if challenge["status"] not in ("pending", "active"):
        return {"joined": False, "message": "Challenge is not open for joining"}

    # Check if already a participant
    participant_ids = [p["user_id"] for p in challenge["participants"]]
    if user_id in participant_ids:
        return {"joined": False, "message": "Already participating"}

    # Check max participants
    max_p = challenge.get("max_participants")
    if max_p and len(challenge["participants"]) >= max_p:
        return {"joined": False, "message": "Challenge is full"}

    # Check privacy
    if challenge["privacy"] == "invite_only":
        invite = await db.challenge_invites.find_one({
            "challenge_id": challenge_id,
            "user_id": user_id,
            "status": "pending",
        })
        if not invite:
            return {"joined": False, "message": "Invitation required"}
        # Mark invite as accepted
        await db.challenge_invites.update_one(
            {"_id": invite["_id"]},
            {"$set": {"status": "accepted"}},
        )

    now = datetime.now(timezone.utc)
    new_participant = {
        "user_id": user_id,
        "joined_at": now.isoformat(),
        "progress": 0,
        "status": "active",
    }

    await db.challenges.update_one(
        {"challenge_id": challenge_id},
        {"$push": {"participants": new_participant}},
    )

    # Auto-start logic
    started = False
    updated_challenge = await db.challenges.find_one({"challenge_id": challenge_id})
    min_participants = 2 if challenge["challenge_type"] == "duo" else 2

    if (
        updated_challenge["status"] == "pending"
        and len(updated_challenge["participants"]) >= min_participants
    ):
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

    return {"joined": True, "started": started, "message": "Joined challenge"}


async def update_challenge_progress(user_id: str, session_data: dict):
    """
    Called after a session is completed.
    Updates progress for ALL active challenges the user participates in.
    This is the core event-driven mechanism — no polling needed.
    """
    # Find all active challenges this user participates in
    active_challenges = await db.challenges.find({
        "status": "active",
        "participants.user_id": user_id,
        "participants.status": "active",
    }).to_list(50)

    for challenge in active_challenges:
        # Check category match
        if challenge["category"] != "mixed":
            if session_data.get("category") != challenge["category"]:
                continue

        # Compute increment based on goal type
        increment = 0
        if challenge["goal_type"] == "sessions":
            increment = 1
        elif challenge["goal_type"] == "time":
            increment = session_data.get("actual_duration", 0)
        elif challenge["goal_type"] == "streak":
            # Streak is special — it's the user's current streak, not cumulative
            # We set progress to the current streak value instead of incrementing
            user = await db.users.find_one({"user_id": user_id}, {"streak_days": 1})
            streak = user.get("streak_days", 0) if user else 0
            await db.challenges.update_one(
                {
                    "challenge_id": challenge["challenge_id"],
                    "participants.user_id": user_id,
                },
                {"$set": {"participants.$.progress": streak}},
            )
            await _recompute_total_progress(challenge["challenge_id"])
            await _check_challenge_completion(challenge["challenge_id"])
            continue

        if increment <= 0:
            continue

        # Update participant's progress
        await db.challenges.update_one(
            {
                "challenge_id": challenge["challenge_id"],
                "participants.user_id": user_id,
            },
            {
                "$inc": {
                    "participants.$.progress": increment,
                    "total_progress": increment,
                },
            },
        )

        await _check_challenge_completion(challenge["challenge_id"])


async def _recompute_total_progress(challenge_id: str):
    """Recompute total progress from all participants."""
    challenge = await db.challenges.find_one({"challenge_id": challenge_id})
    if not challenge:
        return
    total = sum(p.get("progress", 0) for p in challenge["participants"])
    await db.challenges.update_one(
        {"challenge_id": challenge_id},
        {"$set": {"total_progress": total}},
    )


async def _check_challenge_completion(challenge_id: str):
    """Check if a challenge has been completed and handle celebration."""
    challenge = await db.challenges.find_one({"challenge_id": challenge_id})
    if not challenge or challenge["status"] != "active":
        return

    goal = challenge["goal_value"]
    completed = False

    if challenge["goal_type"] == "streak":
        # For streak: any participant reaching the goal completes it for all
        completed = any(
            p.get("progress", 0) >= goal
            for p in challenge["participants"]
            if p["status"] == "active"
        )
    else:
        # For sessions/time: total progress across all participants
        completed = challenge.get("total_progress", 0) >= goal

    if completed:
        now = datetime.now(timezone.utc).isoformat()
        await db.challenges.update_one(
            {"challenge_id": challenge_id},
            {"$set": {"status": "completed", "completed_at": now}},
        )

        # Emit celebration: notify all participants + create feed activities
        from services.activity_service import create_activity

        for participant in challenge["participants"]:
            if participant["status"] != "active":
                continue

            uid = participant["user_id"]

            # Notification
            await db.notifications.insert_one({
                "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
                "user_id": uid,
                "type": "challenge_completed",
                "message": f"Challenge \"{challenge['title']}\" reussi! Bravo a toute l'equipe!",
                "data": {"challenge_id": challenge_id},
                "read": False,
                "created_at": now,
            })

            # Feed activity
            await create_activity(
                user_id=uid,
                activity_type="challenge_completed",
                data={
                    "challenge_title": challenge["title"],
                    "challenge_type": challenge["challenge_type"],
                    "challenge_id": challenge_id,
                    "participant_count": len(challenge["participants"]),
                },
                visibility="followers",
            )


async def _send_challenge_invite(challenge_id: str, sender_id: str, target_id: str):
    """Send a challenge invitation."""
    # Don't send duplicate invites
    existing = await db.challenge_invites.find_one({
        "challenge_id": challenge_id,
        "user_id": target_id,
        "status": "pending",
    })
    if existing:
        return

    sender = await db.users.find_one({"user_id": sender_id}, {"name": 1, "display_name": 1})
    sender_name = sender.get("display_name") or sender.get("name", "Quelqu'un") if sender else "Quelqu'un"

    challenge = await db.challenges.find_one(
        {"challenge_id": challenge_id}, {"title": 1}
    )
    title = challenge.get("title", "un challenge") if challenge else "un challenge"

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
        "message": f"{sender_name} vous invite a rejoindre \"{title}\"",
        "data": {"challenge_id": challenge_id, "sender_id": sender_id},
        "read": False,
        "created_at": now,
    })


def get_leaderboard(participants: list[dict]) -> list[dict]:
    """Compute leaderboard from participant progress."""
    ranked = sorted(
        [p for p in participants if p.get("status") == "active"],
        key=lambda p: p.get("progress", 0),
        reverse=True,
    )
    for i, p in enumerate(ranked):
        p["rank"] = i + 1
    return ranked


def _get_category_icon(category: str) -> str:
    return {
        "learning": "book-open",
        "productivity": "target",
        "well_being": "heart",
        "mixed": "sparkles",
    }.get(category, "sparkles")
