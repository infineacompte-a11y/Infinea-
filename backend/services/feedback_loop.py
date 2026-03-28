"""
Feedback loop service for InFinea.
Accumulates positive/negative signals per (user_id, action_id) pair
based on user behavior (ignored, clicked, completed, abandoned).

Features:
- 6-signal model with calibrated weights
- Temporal decay: old signals decay toward neutral (half-life 30 days)
- Server-side validation: completion/abandonment require matching sessions
- Dedup: identical signals within 60s are ignored
- Score clamping: bounded [-1, +1]

Stored in the `action_signals` collection:
{
    "user_id": str,
    "action_id": str,
    "score": float,          # accumulated signal (-1 to +1 range, clamped)
    "impressions": int,       # times shown
    "clicks": int,            # times clicked
    "completions": int,       # times completed
    "abandonments": int,      # times abandoned
    "updated_at": datetime,
}

The scoring_engine reads `score` to adjust action ranking per user.

Benchmark: Spotify Discover Weekly (implicit feedback decay),
YouTube recommendations (watch time decay), Netflix (temporal weighting).
"""

import math
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("feedback_loop")

# Signal weights — how much each event moves the score
# 6-signal model: original 4 + 2 new vertical AI signals
SIGNAL_WEIGHTS = {
    "impression": -0.02,     # shown but no click = mild negative
    "click": +0.05,          # clicked = moderate positive
    "completion": +0.15,     # completed = strong positive
    "abandonment": -0.10,    # started then abandoned = moderate negative
    "coach_followed": +0.08, # user followed coach's suggestion for this action
    "highly_rated": +0.10,   # user rated session 4-5/5 satisfaction
}

# Score bounds
MIN_SCORE = -1.0
MAX_SCORE = 1.0

# Temporal decay: scores decay toward 0 over time (half-life in days)
# Benchmark: Spotify (14-day decay), YouTube (28-day decay)
# InFinea uses 30 days — preferences evolve but not as fast as music taste
DECAY_HALF_LIFE_DAYS = 30
DECAY_LAMBDA = math.log(2) / DECAY_HALF_LIFE_DAYS  # ~0.0231


def _apply_decay(current_score: float, last_updated: datetime) -> float:
    """Apply exponential decay to a score based on time since last update.

    score(t) = score_0 * e^(-lambda * days_elapsed)
    At half-life (30 days), score is halved. At 60 days, quartered.
    """
    if not last_updated or current_score == 0:
        return current_score
    try:
        if isinstance(last_updated, str):
            last_updated = datetime.fromisoformat(last_updated)
        days_elapsed = (datetime.now(timezone.utc) - last_updated).total_seconds() / 86400
        if days_elapsed < 1:
            return current_score  # No decay within a day
        decay_factor = math.exp(-DECAY_LAMBDA * days_elapsed)
        return current_score * decay_factor
    except Exception:
        return current_score


async def record_signal(
    db,
    user_id: str,
    action_id: str,
    signal_type: str,
    session_id: str = None,
) -> None:
    """
    Record a behavioral signal for a (user_id, action_id) pair.

    signal_type: "impression" | "click" | "completion" | "abandonment"
                 | "coach_followed" | "highly_rated"

    Server-side validation:
    - completion/abandonment require a matching session in user_sessions_history
    - Duplicate signals for same (user, action, type) within 60s are ignored
    - Unknown signal types are rejected

    Fire-and-forget safe: catches all exceptions.
    """
    if signal_type not in SIGNAL_WEIGHTS:
        logger.warning(f"Unknown signal_type: {signal_type}")
        return

    # ── Server-side validation for high-impact signals ──
    # Prevents signal poisoning from rogue clients or frontend bugs
    if signal_type in ("completion", "abandonment"):
        try:
            # Verify a real session exists for this user + action
            session_query = {"user_id": user_id, "action_id": action_id}
            if signal_type == "completion":
                session_query["completed"] = True
            recent_session = await db.user_sessions_history.find_one(
                session_query,
                {"_id": 1},
                sort=[("started_at", -1)],
            )
            if not recent_session:
                logger.debug(
                    f"Signal {signal_type} rejected: no matching session "
                    f"for user={user_id} action={action_id}"
                )
                return
        except Exception:
            pass  # On validation error, allow signal through (fail-open)

    # ── Dedup: ignore duplicate signals within 60s ──
    try:
        existing = await db.action_signals.find_one(
            {"user_id": user_id, "action_id": action_id},
            {"_id": 0, "updated_at": 1, f"last_{signal_type}_at": 1},
        )
        if existing:
            last_signal_at = existing.get(f"last_{signal_type}_at")
            if last_signal_at:
                from datetime import timedelta
                if isinstance(last_signal_at, str):
                    last_signal_at = datetime.fromisoformat(last_signal_at)
                if (datetime.now(timezone.utc) - last_signal_at).total_seconds() < 60:
                    return  # Duplicate within 60s — skip
    except Exception:
        pass  # On dedup check error, allow signal through

    weight = SIGNAL_WEIGHTS[signal_type]

    # Map signal_type to counter field
    counter_field = {
        "impression": "impressions",
        "click": "clicks",
        "completion": "completions",
        "abandonment": "abandonments",
        "coach_followed": "coach_follows",
        "highly_rated": "high_ratings",
    }[signal_type]

    try:
        # Fetch current signal doc, apply temporal decay before adding new signal
        doc = await db.action_signals.find_one(
            {"user_id": user_id, "action_id": action_id},
            {"_id": 0, "score": 1, "updated_at": 1},
        )
        current_score = doc["score"] if doc else 0.0
        # Apply decay: old signals fade toward 0 (half-life 30 days)
        if doc and doc.get("updated_at"):
            current_score = _apply_decay(current_score, doc["updated_at"])
        new_score = max(MIN_SCORE, min(MAX_SCORE, current_score + weight))

        now = datetime.now(timezone.utc)
        await db.action_signals.update_one(
            {"user_id": user_id, "action_id": action_id},
            {
                "$set": {
                    "score": round(new_score, 4),
                    "updated_at": now,
                    f"last_{signal_type}_at": now,
                },
                "$inc": {counter_field: 1},
                "$setOnInsert": {
                    "user_id": user_id,
                    "action_id": action_id,
                    # Initialize other counters to 0 on first insert
                    **{
                        k: 0 for k in
                        ["impressions", "clicks", "completions", "abandonments",
                         "coach_follows", "high_ratings"]
                        if k != counter_field
                    },
                },
            },
            upsert=True,
        )
    except Exception as e:
        logger.error(f"Feedback signal failed ({signal_type} for {action_id}): {e}")


async def get_user_signals(
    db,
    user_id: str,
    action_ids: Optional[list] = None,
) -> dict:
    """
    Fetch feedback signals for a user.

    Returns: {action_id: score} dict.
    If action_ids is provided, only fetches those.
    """
    query = {"user_id": user_id}
    if action_ids:
        query["action_id"] = {"$in": action_ids}

    try:
        docs = await db.action_signals.find(
            query, {"_id": 0, "action_id": 1, "score": 1}
        ).to_list(500)
        return {d["action_id"]: d["score"] for d in docs}
    except Exception as e:
        logger.error(f"Failed to fetch signals for {user_id}: {e}")
        return {}
