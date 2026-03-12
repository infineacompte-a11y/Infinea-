"""
Scoring engine for InFinea.
Scores and ranks actions by predicted completion probability
using per-user behavioral features from user_features collection.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

from services.feedback_loop import get_user_signals

logger = logging.getLogger("scoring_engine")

# Scoring weights (sum = 1.0)
# Feedback signal takes 0.15 from the original budget,
# other weights scaled down proportionally to preserve relative ordering.
W_CATEGORY_AFFINITY = 0.25
W_DURATION_FIT = 0.22
W_ENERGY_MATCH = 0.17
W_TIME_PERFORMANCE = 0.13
W_NOVELTY_BONUS = 0.08
W_FEEDBACK_SIGNAL = 0.15

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
            "feedback_signals": dict {action_id: score} from action_signals,
        }

    Returns:
        {"score": float 0-1, "breakdown": {...component scores...}}
    """
    # --- 1. Category affinity (0.25) ---
    cat = action.get("category", "unknown")
    cat_rates = features.get("completion_rate_by_category", {})
    global_rate = features.get("completion_rate_global", 0.5)
    category_affinity = cat_rates.get(cat, global_rate)

    # Apply category fatigue penalty: if this category has rising abandonment,
    # reduce affinity proportionally. Fatigue value is 0.1-1.0 (delta in abandon rate).
    # Penalty: multiply affinity by (1 - fatigue), so fatigue=0.3 → affinity * 0.7
    fatigue_map = features.get("category_fatigue", {})
    fatigue_penalty = fatigue_map.get(cat, 0.0)
    if fatigue_penalty > 0:
        category_affinity *= (1.0 - min(fatigue_penalty, 0.8))  # cap at 80% reduction

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

    # --- 5. Novelty bonus (0.08) ---
    recent_ids = context.get("recent_action_ids", set())
    action_id = action.get("action_id", "")
    novelty_bonus = 0.2 if action_id in recent_ids else 1.0

    # --- 6. Feedback signal (0.15) ---
    # Maps signal score from [-1, +1] to [0, 1] range for weighted sum.
    # Default 0.5 (neutral) when no signal exists for this action.
    feedback_signals = context.get("feedback_signals", {})
    raw_signal = feedback_signals.get(action_id, 0.0)
    feedback_score = (raw_signal + 1.0) / 2.0  # -1→0, 0→0.5, +1→1.0

    # --- Weighted total ---
    # Use per-user adaptive weights if available, otherwise global defaults
    aw = features.get("adaptive_weights")
    w_cat = aw["category_affinity"] if aw else W_CATEGORY_AFFINITY
    w_dur = aw["duration_fit"] if aw else W_DURATION_FIT
    w_ene = aw["energy_match"] if aw else W_ENERGY_MATCH
    w_tim = aw["time_performance"] if aw else W_TIME_PERFORMANCE
    w_nov = aw["novelty_bonus"] if aw else W_NOVELTY_BONUS
    w_fb = aw["feedback_signal"] if aw else W_FEEDBACK_SIGNAL

    total = (
        w_cat * category_affinity
        + w_dur * duration_fit
        + w_ene * energy_match
        + w_tim * time_performance
        + w_nov * novelty_bonus
        + w_fb * feedback_score
    )

    return {
        "score": round(total, 4),
        "adaptive": aw is not None,
        "breakdown": {
            "category_affinity": round(category_affinity, 3),
            "duration_fit": round(duration_fit, 3),
            "energy_match": round(energy_match, 3),
            "time_performance": round(time_performance, 3),
            "novelty_bonus": round(novelty_bonus, 3),
            "feedback_signal": round(feedback_score, 3),
        },
        "weights_used": {
            "category_affinity": round(w_cat, 4),
            "duration_fit": round(w_dur, 4),
            "energy_match": round(w_ene, 4),
            "time_performance": round(w_tim, 4),
            "novelty_bonus": round(w_nov, 4),
            "feedback_signal": round(w_fb, 4),
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

    # Fetch user features (cache-first, fallback to MongoDB)
    from services.cache import cache_get, cache_set, TTL_USER_FEATURES
    features = await cache_get(f"user_features:{user_id}")
    if not features:
        features = await db.user_features.find_one(
            {"user_id": user_id}, {"_id": 0}
        )
        if features:
            await cache_set(f"user_features:{user_id}", features, ttl=TTL_USER_FEATURES)
    if not features:
        logger.info(f"No features for user {user_id}, skipping scoring")
        return actions

    # Fetch recent action_ids (last 7 days) for novelty
    seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    recent_sessions = await db.user_sessions_history.find(
        {"user_id": user_id, "started_at": {"$gte": seven_days_ago}},
        {"_id": 0, "action_id": 1},
    ).to_list(200)
    recent_action_ids = {s["action_id"] for s in recent_sessions if s.get("action_id")}

    # Fetch feedback signals for candidate actions
    candidate_ids = [a.get("action_id", "") for a in actions if a.get("action_id")]
    feedback_signals = await get_user_signals(db, user_id, candidate_ids)

    # Build context
    context = {
        "energy_level": energy_level,
        "available_time": available_time,
        "time_bucket": _current_time_bucket(),
        "recent_action_ids": recent_action_ids,
        "feedback_signals": feedback_signals,
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


def _time_bucket_from_iso(iso_timestamp: str) -> str:
    """Extract time bucket from an ISO timestamp."""
    try:
        dt = datetime.fromisoformat(iso_timestamp)
        hour = dt.hour
    except (ValueError, TypeError):
        return _current_time_bucket()
    if 6 <= hour < 12:
        return "morning"
    elif 12 <= hour < 18:
        return "afternoon"
    elif 18 <= hour < 24:
        return "evening"
    return "night"


async def get_next_best_action(
    db,
    user_id: str,
    slot_duration: int,
    slot_start_time: Optional[str] = None,
    min_score: float = 0.0,
) -> Optional[Dict[str, Any]]:
    """
    Find the best action for a given slot using behavioral scoring.

    Parameters:
        db: database handle
        user_id: user identifier
        slot_duration: available minutes in the slot
        slot_start_time: ISO timestamp of slot start (for time bucket inference)
        min_score: minimum score threshold (actions below are excluded)

    Returns:
        Best action dict with _score and _breakdown, or None.
    """
    features = await db.user_features.find_one(
        {"user_id": user_id}, {"_id": 0}
    )
    if not features:
        return None

    # Fetch actions that fit in the slot
    actions = await db.micro_actions.find(
        {"duration_min": {"$lte": slot_duration}},
        {"_id": 0},
    ).to_list(100)
    if not actions:
        return None

    # Infer energy from features contextual data
    bucket = _time_bucket_from_iso(slot_start_time) if slot_start_time else _current_time_bucket()
    energy_pref = features.get("energy_preference_by_time", {})
    inferred_energy = energy_pref.get(bucket, "medium")

    # Fetch recent action_ids for novelty
    seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    recent_sessions = await db.user_sessions_history.find(
        {"user_id": user_id, "started_at": {"$gte": seven_days_ago}},
        {"_id": 0, "action_id": 1},
    ).to_list(200)
    recent_action_ids = {s["action_id"] for s in recent_sessions if s.get("action_id")}

    # Fetch feedback signals
    candidate_ids = [a.get("action_id", "") for a in actions if a.get("action_id")]
    feedback_signals = await get_user_signals(db, user_id, candidate_ids)

    context = {
        "energy_level": inferred_energy,
        "available_time": slot_duration,
        "time_bucket": bucket,
        "recent_action_ids": recent_action_ids,
        "feedback_signals": feedback_signals,
    }

    # Score all actions, pick the best
    best = None
    best_score = -1
    for action in actions:
        result = score_action(action, features, context)
        if result["score"] > best_score and result["score"] >= min_score:
            best_score = result["score"]
            best = dict(action)
            best["_score"] = result["score"]
            best["_breakdown"] = result["breakdown"]

    return best
