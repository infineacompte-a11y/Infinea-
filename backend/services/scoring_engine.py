"""
Scoring engine for InFinea.
Scores and ranks actions by predicted completion probability
using per-user behavioral features from user_features collection.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

logger = logging.getLogger("scoring_engine")

# Scoring weights
W_CATEGORY_AFFINITY = 0.30
W_DURATION_FIT = 0.25
W_ENERGY_MATCH = 0.20
W_TIME_PERFORMANCE = 0.15
W_NOVELTY_BONUS = 0.10

# Energy adjacency map (exact=1.0, adjacent=0.5, opposite=0.1)
_ENERGY_SCORES = {
    ("low", "low"): 1.0,
    ("low", "medium"): 0.5,
    ("low", "high"): 0.1,
    ("medium", "low"): 0.5,
    ("medium", "medium"): 1.0,
    ("medium", "high"): 0.5,
    ("high", "low"): 0.1,
    ("high", "medium"): 0.5,
    ("high", "high"): 1.0,
}


def _current_time_bucket() -> str:
    """Return current time-of-day bucket."""
    hour = datetime.now(timezone.utc).hour
    if 6 <= hour < 12:
        return "morning"
    elif 12 <= hour < 18:
        return "afternoon"
    elif 18 <= hour < 24:
        return "evening"
    return "night"


def score_action(
    action: Dict[str, Any],
    features: Dict[str, Any],
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Score a single action for a user.

    Parameters:
        action: action document from micro_actions collection
        features: user features from user_features collection
        context: {
            "energy_level": "low"|"medium"|"high",
            "available_time": int (minutes),
            "time_bucket": "morning"|"afternoon"|"evening"|"night",
            "recent_action_ids": set of action_ids done in last 7 days,
        }

    Returns:
        {"score": float 0-1, "breakdown": {...component scores...}}
    """
    # --- 1. Category affinity (0.30) ---
    cat = action.get("category", "unknown")
    cat_rates = features.get("completion_rate_by_category", {})
    global_rate = features.get("completion_rate_global", 0.5)
    category_affinity = cat_rates.get(cat, global_rate)

    # --- 2. Duration fit (0.25) ---
    preferred = features.get("preferred_action_duration", 5.0)
    d_min = action.get("duration_min", 3)
    d_max = action.get("duration_max", 7)
    available = context.get("available_time", 15)

    # Hard penalty: action doesn't fit in available time
    if d_min > available:
        duration_fit = 0.0
    elif d_min <= preferred <= d_max:
        # Preferred duration falls within action range: perfect
        duration_fit = 1.0
    else:
        # Decay based on distance from range
        if preferred < d_min:
            distance = d_min - preferred
        else:
            distance = preferred - d_max
        duration_fit = max(0.0, 1.0 - (distance / 10.0))

    # --- 3. Energy match (0.20) ---
    requested_energy = context.get("energy_level", "medium")
    action_energy = action.get("energy_level", "medium")
    energy_match = _ENERGY_SCORES.get(
        (requested_energy, action_energy), 0.5
    )

    # --- 4. Time performance (0.15) ---
    bucket = context.get("time_bucket", _current_time_bucket())
    tod_rates = features.get("completion_rate_by_time_of_day", {})
    time_performance = tod_rates.get(bucket, global_rate)

    # --- 5. Novelty bonus (0.10) ---
    recent_ids = context.get("recent_action_ids", set())
    action_id = action.get("action_id", "")
    novelty_bonus = 0.2 if action_id in recent_ids else 1.0

    # --- Weighted total ---
    total = (
        W_CATEGORY_AFFINITY * category_affinity
        + W_DURATION_FIT * duration_fit
        + W_ENERGY_MATCH * energy_match
        + W_TIME_PERFORMANCE * time_performance
        + W_NOVELTY_BONUS * novelty_bonus
    )

    return {
        "score": round(total, 4),
        "breakdown": {
            "category_affinity": round(category_affinity, 3),
            "duration_fit": round(duration_fit, 3),
            "energy_match": round(energy_match, 3),
            "time_performance": round(time_performance, 3),
            "novelty_bonus": round(novelty_bonus, 3),
        },
    }


async def rank_actions_for_user(
    db,
    user_id: str,
    actions: List[Dict[str, Any]],
    energy_level: str = "medium",
    available_time: int = 15,
) -> List[Dict[str, Any]]:
    """
    Score and rank a list of actions for a specific user.
    Returns actions sorted by score descending, each enriched with _score and _breakdown.

    Graceful fallback: if no user features exist, returns actions as-is (no scoring).
    """
    if not actions:
        return []

    # Fetch user features
    features = await db.user_features.find_one(
        {"user_id": user_id}, {"_id": 0}
    )
    if not features:
        logger.info(f"No features for user {user_id}, skipping scoring")
        return actions

    # Fetch recent action_ids (last 7 days) for novelty
    from datetime import timedelta
    seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    recent_sessions = await db.user_sessions_history.find(
        {"user_id": user_id, "started_at": {"$gte": seven_days_ago}},
        {"_id": 0, "action_id": 1},
    ).to_list(200)
    recent_action_ids = {s["action_id"] for s in recent_sessions if s.get("action_id")}

    # Build context
    context = {
        "energy_level": energy_level,
        "available_time": available_time,
        "time_bucket": _current_time_bucket(),
        "recent_action_ids": recent_action_ids,
    }

    # Score each action
    scored = []
    for action in actions:
        result = score_action(action, features, context)
        enriched = dict(action)
        enriched["_score"] = result["score"]
        enriched["_breakdown"] = result["breakdown"]
        scored.append(enriched)

    # Sort by score descending
    scored.sort(key=lambda a: a["_score"], reverse=True)
    return scored
