"""
Adaptive weight learner for InFinea.
Learns per-user scoring weights by analyzing which factors best predict
action completion for each individual user.

Runs inside the feature_computation_loop (every 6h) after features are computed.
Stores learned weights in user_features["adaptive_weights"].

Algorithm:
    For each scoring factor, compute the correlation between the factor's
    score and the actual completion outcome (1 = completed, 0 = abandoned).
    Normalize correlations to get per-user weights that sum to 1.0.

    Minimum 20 sessions required to start learning. Below that threshold,
    global default weights are used.
"""

import math
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List

logger = logging.getLogger("weight_learner")

# Global defaults — 8-factor model (must match scoring_engine.py)
DEFAULT_WEIGHTS = {
    "category_affinity": 0.22,
    "duration_fit": 0.19,
    "energy_match": 0.15,
    "time_performance": 0.12,
    "novelty_bonus": 0.07,
    "feedback_signal": 0.08,
    "objective_alignment": 0.10,
    "session_quality": 0.07,
}

# Temporal decay: half-life ~35 days (lambda = ln(2)/35 ≈ 0.0198)
DECAY_LAMBDA = 0.02

# Minimum sessions before we start adapting weights
MIN_SESSIONS_FOR_LEARNING = 20

# How much we blend learned weights with defaults (0 = all default, 1 = all learned)
# This creates a smooth transition as we gain confidence
LEARNING_RATE = 0.6

# Bounds: no single weight can go below 0.05 or above 0.45
WEIGHT_FLOOR = 0.05
WEIGHT_CEILING = 0.45


def _energy_score(requested: str, action: str) -> float:
    """Reproduce energy scoring logic from scoring_engine."""
    scores = {
        ("low", "low"): 1.0, ("low", "medium"): 0.5, ("low", "high"): 0.1,
        ("medium", "low"): 0.5, ("medium", "medium"): 1.0, ("medium", "high"): 0.5,
        ("high", "low"): 0.1, ("high", "medium"): 0.5, ("high", "high"): 1.0,
    }
    return scores.get((requested, action), 0.5)


def _time_bucket(hour: int) -> str:
    if 6 <= hour < 12:
        return "morning"
    elif 12 <= hour < 18:
        return "afternoon"
    elif 18 <= hour < 24:
        return "evening"
    return "night"


async def compute_adaptive_weights(
    db,
    user_id: str,
    features: Dict[str, Any],
) -> Optional[Dict[str, float]]:
    """
    Compute personalized scoring weights for a user.

    Analyzes the user's session history to determine which scoring factors
    best correlate with successful completions.

    Returns: dict of {factor_name: weight} summing to 1.0, or None if
    insufficient data.
    """
    # Need enough sessions to learn meaningful patterns
    total_sessions = features.get("total_sessions", 0)
    if total_sessions < MIN_SESSIONS_FOR_LEARNING:
        return None

    # Fetch recent sessions (last 90 days for learning)
    ninety_days_ago = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
    sessions = await db.user_sessions_history.find(
        {"user_id": user_id, "started_at": {"$gte": ninety_days_ago}},
        {"_id": 0, "action_id": 1, "completed": 1, "started_at": 1,
         "category": 1, "actual_duration": 1},
    ).to_list(1000)

    if len(sessions) < MIN_SESSIONS_FOR_LEARNING:
        return None

    # Fetch action metadata for energy levels
    action_ids = list({s.get("action_id", "") for s in sessions if s.get("action_id")})
    actions_docs = await db.micro_actions.find(
        {"action_id": {"$in": action_ids}},
        {"_id": 0, "action_id": 1, "energy_level": 1, "category": 1,
         "duration_min": 1, "duration_max": 1},
    ).to_list(len(action_ids))
    action_map = {a["action_id"]: a for a in actions_docs}

    # Fetch feedback signals
    signals_docs = await db.action_signals.find(
        {"user_id": user_id, "action_id": {"$in": action_ids}},
        {"_id": 0, "action_id": 1, "score": 1},
    ).to_list(500)
    signal_map = {d["action_id"]: d["score"] for d in signals_docs}

    # For each session, compute what each factor's score would have been,
    # and track whether the session was completed.
    # Temporal decay: recent sessions weighted exponentially higher (half-life ~35 days).
    factor_scores = {k: [] for k in DEFAULT_WEIGHTS}
    outcomes = []
    temporal_weights = []  # decay weight per session

    cat_rates = features.get("completion_rate_by_category", {})
    global_rate = features.get("completion_rate_global", 0.5)
    tod_rates = features.get("completion_rate_by_time_of_day", {})
    preferred_duration = features.get("preferred_action_duration", 5.0)
    now = datetime.now(timezone.utc)

    # Fetch active objective categories for alignment factor
    active_obj_cats = set()
    try:
        objectives = await db.objectives.find(
            {"user_id": user_id, "status": "active"},
            {"_id": 0, "category": 1},
        ).to_list(10)
        active_obj_cats = {o["category"] for o in objectives if o.get("category")}
    except Exception:
        pass

    recent_ids = set()  # rolling window for novelty

    for s in sorted(sessions, key=lambda x: x.get("started_at", "")):
        aid = s.get("action_id", "")
        action = action_map.get(aid)
        if not action:
            continue

        completed = 1.0 if s.get("completed") else 0.0
        outcomes.append(completed)

        # Compute temporal decay weight (recent sessions count more)
        try:
            session_dt = datetime.fromisoformat(s["started_at"])
            if session_dt.tzinfo is None:
                session_dt = session_dt.replace(tzinfo=timezone.utc)
            days_ago = max(0, (now - session_dt).days)
        except (ValueError, TypeError):
            days_ago = 45  # fallback to middle of window
        temporal_weights.append(math.exp(-DECAY_LAMBDA * days_ago))

        # 1. Category affinity
        cat = action.get("category", s.get("category", "unknown"))
        factor_scores["category_affinity"].append(cat_rates.get(cat, global_rate))

        # 2. Duration fit
        d_min = action.get("duration_min", 3)
        d_max = action.get("duration_max", 7)
        if d_min <= preferred_duration <= d_max:
            dur_score = 1.0
        elif preferred_duration < d_min:
            dur_score = max(0.0, 1.0 - (d_min - preferred_duration) / 10.0)
        else:
            dur_score = max(0.0, 1.0 - (preferred_duration - d_max) / 10.0)
        factor_scores["duration_fit"].append(dur_score)

        # 3. Energy match — infer from time of session
        try:
            hour = datetime.fromisoformat(s["started_at"]).hour
        except (ValueError, TypeError):
            hour = 12
        bucket = _time_bucket(hour)
        energy_pref = features.get("energy_preference_by_time", {})
        user_energy = energy_pref.get(bucket, "medium")
        action_energy = action.get("energy_level", "medium")
        factor_scores["energy_match"].append(_energy_score(user_energy, action_energy))

        # 4. Time performance
        factor_scores["time_performance"].append(tod_rates.get(bucket, global_rate))

        # 5. Novelty
        novelty = 0.2 if aid in recent_ids else 1.0
        factor_scores["novelty_bonus"].append(novelty)
        recent_ids.add(aid)

        # 6. Feedback signal
        raw = signal_map.get(aid, 0.0)
        factor_scores["feedback_signal"].append((raw + 1.0) / 2.0)

        # 7. Objective alignment (NEW)
        factor_scores["objective_alignment"].append(1.0 if cat in active_obj_cats else 0.3)

        # 8. Session quality (NEW)
        satisfaction = s.get("satisfaction_rating")
        factor_scores["session_quality"].append(satisfaction / 5.0 if satisfaction else 0.5)

    if len(outcomes) < MIN_SESSIONS_FOR_LEARNING:
        return None

    # Compute WEIGHTED correlation between each factor and outcomes.
    # Temporal decay: recent sessions have exponentially higher weight.
    # Weighted Pearson correlation: uses temporal_weights to emphasize recent behavior.
    total_w = sum(temporal_weights)
    if total_w < 0.01:
        return None

    # Weighted means
    w_mean_outcome = sum(temporal_weights[i] * outcomes[i] for i in range(len(outcomes))) / total_w
    correlations = {}

    for factor_name, scores in factor_scores.items():
        if not scores or len(scores) != len(outcomes):
            correlations[factor_name] = 0.0
            continue
        n = len(scores)
        w_mean_score = sum(temporal_weights[i] * scores[i] for i in range(n)) / total_w

        # Weighted covariance
        w_cov = sum(
            temporal_weights[i] * (scores[i] - w_mean_score) * (outcomes[i] - w_mean_outcome)
            for i in range(n)
        ) / total_w

        # Weighted variances
        w_var_s = sum(temporal_weights[i] * (scores[i] - w_mean_score) ** 2 for i in range(n)) / total_w
        w_var_o = sum(temporal_weights[i] * (outcomes[i] - w_mean_outcome) ** 2 for i in range(n)) / total_w

        std_prod = (w_var_s ** 0.5) * (w_var_o ** 0.5)
        if std_prod < 0.001:
            correlations[factor_name] = 0.0
        else:
            correlations[factor_name] = max(0.0, w_cov / std_prod)  # only positive correlations

    # Convert correlations to weights (normalize to sum=1)
    total_corr = sum(correlations.values())
    if total_corr < 0.01:
        # No meaningful correlations found — stick with defaults
        return None

    learned = {k: v / total_corr for k, v in correlations.items()}

    # Blend with defaults for stability
    blended = {}
    for k in DEFAULT_WEIGHTS:
        raw = LEARNING_RATE * learned.get(k, 0.0) + (1 - LEARNING_RATE) * DEFAULT_WEIGHTS[k]
        blended[k] = max(WEIGHT_FLOOR, min(WEIGHT_CEILING, raw))

    # Re-normalize to sum to 1.0
    total = sum(blended.values())
    final = {k: round(v / total, 4) for k, v in blended.items()}

    logger.info(f"Adaptive weights for {user_id}: {final}")
    return final
