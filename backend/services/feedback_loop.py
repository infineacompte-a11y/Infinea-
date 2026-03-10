"""
Feedback loop service for InFinea.
Accumulates positive/negative signals per (user_id, action_id) pair
based on user behavior (ignored, clicked, completed, abandoned).

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
"""

import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("feedback_loop")

# Signal weights — how much each event moves the score
SIGNAL_WEIGHTS = {
    "impression": -0.02,     # shown but no click = mild negative
    "click": +0.05,          # clicked = moderate positive
    "completion": +0.15,     # completed = strong positive
    "abandonment": -0.10,    # started then abandoned = moderate negative
}

# Score bounds
MIN_SCORE = -1.0
MAX_SCORE = 1.0


async def record_signal(
    db,
    user_id: str,
    action_id: str,
    signal_type: str,
) -> None:
    """
    Record a behavioral signal for a (user_id, action_id) pair.

    signal_type: "impression" | "click" | "completion" | "abandonment"

    Fire-and-forget safe: catches all exceptions.
    """
    if signal_type not in SIGNAL_WEIGHTS:
        logger.warning(f"Unknown signal_type: {signal_type}")
        return

    weight = SIGNAL_WEIGHTS[signal_type]

    # Map signal_type to counter field
    counter_field = {
        "impression": "impressions",
        "click": "clicks",
        "completion": "completions",
        "abandonment": "abandonments",
    }[signal_type]

    try:
        # Fetch current signal doc (or default)
        doc = await db.action_signals.find_one(
            {"user_id": user_id, "action_id": action_id},
            {"_id": 0, "score": 1},
        )
        current_score = doc["score"] if doc else 0.0
        new_score = max(MIN_SCORE, min(MAX_SCORE, current_score + weight))

        await db.action_signals.update_one(
            {"user_id": user_id, "action_id": action_id},
            {
                "$set": {
                    "score": round(new_score, 4),
                    "updated_at": datetime.now(timezone.utc),
                },
                "$inc": {counter_field: 1},
                "$setOnInsert": {
                    "user_id": user_id,
                    "action_id": action_id,
                    # Initialize other counters to 0 on first insert
                    **{
                        k: 0 for k in
                        ["impressions", "clicks", "completions", "abandonments"]
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
