"""
InFinea — XP & Levels Engine.

Progression system inspired by Duolingo (XP/leagues), Khan Academy (energy points),
and RPG level curves. Every meaningful action awards XP; accumulated XP unlocks levels.

Design principles:
  - Quick early levels (dopamine), progressively harder (longevity).
  - Multiple XP sources to reward diverse behaviours.
  - Streak multiplier rewards consistency, not just volume.
  - Level-up triggers celebration activity in the social feed.
  - Retroactive migration for existing users (fair onboarding).

Level curve: triangular — xp_for_level(n) = 100 × n
  Level 1→2: 100 XP   |  Level 5→6: 500 XP   |  Level 10→11: 1000 XP
  Total XP for level N: 50 × N × (N − 1)

Titles (InFinea DNA — progression, empowerment):
  1-4: Curieux   |  5-9: Explorateur  |  10-14: Apprenti
  15-19: Praticien  |  20-29: Expert  |  30-39: Maître
  40-49: Virtuose  |  50+: Légende
"""

import logging
import math
from datetime import datetime, timezone

from database import db

logger = logging.getLogger(__name__)


# ── Level curve ──────────────────────────────────────────────────────────

def xp_for_next_level(level: int) -> int:
    """XP required to advance from `level` to `level + 1`."""
    return 100 * level


def total_xp_for_level(level: int) -> int:
    """Cumulative XP required to *reach* a given level (from level 1)."""
    if level <= 1:
        return 0
    return 50 * level * (level - 1)


def level_from_xp(total_xp: int) -> int:
    """Derive level from cumulative XP.  Inverse of total_xp_for_level.
    Solve: 50 × L × (L-1) ≤ total_xp  →  L = floor((1 + √(1 + 4×total_xp/50)) / 2)
    """
    if total_xp <= 0:
        return 1
    discriminant = 1 + (4 * total_xp) / 50
    level = int((1 + math.sqrt(discriminant)) / 2)
    # Clamp: make sure we didn't overshoot due to float precision
    while total_xp_for_level(level + 1) <= total_xp:
        level += 1
    while total_xp_for_level(level) > total_xp:
        level -= 1
    return max(1, level)


def xp_progress_in_level(total_xp: int) -> dict:
    """Return current level, XP earned in current level, and XP needed for next."""
    level = level_from_xp(total_xp)
    current_threshold = total_xp_for_level(level)
    next_threshold = total_xp_for_level(level + 1)
    xp_in_level = total_xp - current_threshold
    xp_needed = next_threshold - current_threshold
    return {
        "level": level,
        "total_xp": total_xp,
        "xp_in_level": xp_in_level,
        "xp_needed": xp_needed,
        "progress": round(xp_in_level / xp_needed, 3) if xp_needed > 0 else 1.0,
        "title": get_title(level),
    }


# ── Titles ───────────────────────────────────────────────────────────────

TITLES = [
    (50, "Légende"),
    (40, "Virtuose"),
    (30, "Maître"),
    (20, "Expert"),
    (15, "Praticien"),
    (10, "Apprenti"),
    (5, "Explorateur"),
    (1, "Curieux"),
]


def get_title(level: int) -> str:
    for threshold, title in TITLES:
        if level >= threshold:
            return title
    return "Curieux"


# ── XP Calculation ───────────────────────────────────────────────────────

# Streak multiplier: base 1.0, +0.1 per 7-day block, capped at 2.0
def _streak_multiplier(streak_days: int) -> float:
    return min(2.0, 1.0 + (streak_days // 7) * 0.1)


def calculate_session_xp(
    duration_minutes: int,
    streak_days: int = 0,
    is_first_session_today: bool = False,
) -> dict:
    """Calculate XP earned from completing a session.

    Returns:
        {total_xp, breakdown: {base, duration_bonus, streak_bonus, first_today_bonus}}
    """
    base = 10
    duration_bonus = min(30, duration_minutes)  # +1 XP per minute, cap 30
    subtotal = base + duration_bonus

    multiplier = _streak_multiplier(streak_days)
    streak_bonus = round(subtotal * (multiplier - 1.0))

    first_today_bonus = 5 if is_first_session_today else 0

    total = subtotal + streak_bonus + first_today_bonus

    return {
        "total_xp": total,
        "breakdown": {
            "base": base,
            "duration_bonus": duration_bonus,
            "streak_bonus": streak_bonus,
            "streak_multiplier": multiplier,
            "first_today_bonus": first_today_bonus,
        },
    }


STREAK_MILESTONE_XP = {
    3: 10,
    7: 25,
    14: 50,
    30: 100,
    60: 150,
    100: 200,
    365: 500,
}

BADGE_XP = 20
CHALLENGE_XP = 30
POST_XP = 5  # Max 1 per day


# ── Award XP (write to DB) ──────────────────────────────────────────────

async def award_xp(
    user_id: str,
    amount: int,
    source: str,
    details: dict | None = None,
) -> dict:
    """Award XP to a user and handle level-up detection.

    Args:
        user_id: target user
        amount: XP to add (positive int)
        source: e.g. "session", "badge", "challenge", "post", "streak_milestone"
        details: optional context (session_id, badge_id, etc.)

    Returns:
        {new_total_xp, old_level, new_level, leveled_up, xp_awarded, progress}
    """
    if amount <= 0:
        return {"xp_awarded": 0, "leveled_up": False}

    user = await db.users.find_one(
        {"user_id": user_id},
        {"total_xp": 1, "level": 1},
    )
    old_total = (user or {}).get("total_xp", 0)
    old_level = (user or {}).get("level", 1)

    new_total = old_total + amount
    new_level = level_from_xp(new_total)
    leveled_up = new_level > old_level

    # Atomic update
    update_fields = {
        "total_xp": new_total,
        "level": new_level,
        "xp_updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": update_fields},
    )

    # Log XP gain for analytics/history
    await db.xp_history.insert_one({
        "user_id": user_id,
        "amount": amount,
        "source": source,
        "details": details or {},
        "total_after": new_total,
        "level_after": new_level,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    progress = xp_progress_in_level(new_total)

    # Level-up: emit activity + notification
    if leveled_up:
        try:
            from services.activity_service import emit_activity
            await emit_activity(
                user_id=user_id,
                activity_type="level_up",
                data={
                    "old_level": old_level,
                    "new_level": new_level,
                    "title": get_title(new_level),
                    "total_xp": new_total,
                },
                visibility="public",
            )
        except Exception:
            logger.exception("Failed to emit level_up activity")

        try:
            from helpers import send_push_to_user
            title_name = get_title(new_level)
            await send_push_to_user(
                user_id,
                "Niveau supérieur !",
                f"Tu es passé au niveau {new_level} — {title_name}",
                url="/profile",
                tag="level_up",
            )
        except Exception:
            logger.exception("Failed to send level_up push")

        try:
            await db.notifications.insert_one({
                "notification_id": f"notif_lvl_{new_level}_{user_id[:8]}",
                "user_id": user_id,
                "type": "level_up",
                "message": f"Niveau {new_level} atteint — {get_title(new_level)} !",
                "data": {
                    "old_level": old_level,
                    "new_level": new_level,
                    "title": get_title(new_level),
                },
                "read": False,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
        except Exception:
            logger.exception("Failed to create level_up notification")

    return {
        "xp_awarded": amount,
        "new_total_xp": new_total,
        "old_level": old_level,
        "new_level": new_level,
        "leveled_up": leveled_up,
        **progress,
    }


# ── Retroactive XP Migration ────────────────────────────────────────────

async def migrate_user_xp(user: dict) -> int:
    """Calculate retroactive XP for an existing user based on their history.

    Formula:
      sessions × 10 (base) + total_time_invested (duration proxy) + badges × 20
    """
    user_id = user["user_id"]

    # Count completed sessions
    session_count = await db.user_sessions_history.count_documents({
        "user_id": user_id,
        "completed": True,
    })

    total_time = user.get("total_time_invested", 0)
    badge_count = len(user.get("badges", []))
    streak_days = user.get("streak_days", 0)

    # Streak milestone retroactive bonus
    streak_bonus = sum(
        xp for threshold, xp in STREAK_MILESTONE_XP.items()
        if streak_days >= threshold
    )

    total_xp = (
        session_count * 10          # Base XP per session
        + int(total_time)           # 1 XP per minute invested
        + badge_count * BADGE_XP    # Badge bonuses
        + streak_bonus              # Streak milestone bonuses
    )

    level = level_from_xp(total_xp)

    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {
            "total_xp": total_xp,
            "level": level,
            "xp_updated_at": datetime.now(timezone.utc).isoformat(),
        }},
    )

    return total_xp
