"""
Feature calculator for InFinea.
Computes per-user behavioral features from session history.
Stores results in user_features collection, recalculated periodically.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

logger = logging.getLogger("feature_calculator")

FEATURE_VERSION = 4  # v4: added learning_velocity, difficulty_calibration, coaching_stage


def _time_of_day_bucket(iso_timestamp: str) -> str:
    """Bucket an ISO timestamp into morning/afternoon/evening/night."""
    try:
        dt = datetime.fromisoformat(iso_timestamp)
        hour = dt.hour
    except (ValueError, TypeError):
        return "afternoon"  # safe default

    if 6 <= hour < 12:
        return "morning"
    elif 12 <= hour < 18:
        return "afternoon"
    elif 18 <= hour < 24:
        return "evening"
    return "night"


def _median(values: list) -> float:
    """Compute median without numpy."""
    if not values:
        return 5.0  # default
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    mid = n // 2
    if n % 2 == 0:
        return (sorted_vals[mid - 1] + sorted_vals[mid]) / 2
    return sorted_vals[mid]


async def _compute_engagement_features(db, user_id: str) -> Dict[str, Any]:
    """
    Compute engagement features from event_log collection.
    These complement session-based features with behavioral signals.

    Returns dict with:
        - suggestion_ctr: click-through rate (clicks / impressions)
        - abandonment_rate: abandonments / starts
        - engagement_trend: completion rate last 7d vs previous 7d (-1 to +1)
        - session_momentum: max consecutive completed sessions (last 30d)
        - category_fatigue: {category: abandonment trend} for declining categories
    """
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

    events = await db.event_log.find(
        {"user_id": user_id, "timestamp": {"$gte": thirty_days_ago}},
        {"_id": 0, "event_type": 1, "timestamp": 1, "metadata": 1},
    ).to_list(5000)

    if not events:
        return {
            "suggestion_ctr": 0.0,
            "abandonment_rate": 0.0,
            "engagement_trend": 0.0,
            "session_momentum": 0,
            "category_fatigue": {},
        }

    # --- 1. Suggestion click-through rate ---
    impressions = sum(1 for e in events if e["event_type"] == "suggestion_generated")
    clicks = sum(1 for e in events if e["event_type"] == "suggestion_clicked")
    suggestion_ctr = clicks / impressions if impressions > 0 else 0.0

    # --- 2. Abandonment rate ---
    starts = sum(1 for e in events if e["event_type"] == "action_started")
    abandonments = sum(1 for e in events if e["event_type"] == "action_abandoned")
    abandonment_rate = abandonments / starts if starts > 0 else 0.0

    # --- 3. Engagement trend (last 7d vs previous 7d) ---
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    fourteen_days_ago = datetime.now(timezone.utc) - timedelta(days=14)

    recent_completed = sum(
        1 for e in events
        if e["event_type"] == "action_completed" and e["timestamp"] >= seven_days_ago
    )
    recent_started = sum(
        1 for e in events
        if e["event_type"] == "action_started" and e["timestamp"] >= seven_days_ago
    )
    prev_completed = sum(
        1 for e in events
        if e["event_type"] == "action_completed"
        and fourteen_days_ago <= e["timestamp"] < seven_days_ago
    )
    prev_started = sum(
        1 for e in events
        if e["event_type"] == "action_started"
        and fourteen_days_ago <= e["timestamp"] < seven_days_ago
    )

    recent_rate = recent_completed / recent_started if recent_started > 0 else 0.0
    prev_rate = prev_completed / prev_started if prev_started > 0 else 0.0
    # Trend: positive = improving, negative = declining, clamped to [-1, +1]
    engagement_trend = max(-1.0, min(1.0, recent_rate - prev_rate))

    # --- 4. Session momentum (max consecutive completions, last 30d) ---
    completion_events = sorted(
        [e for e in events if e["event_type"] in ("action_completed", "action_abandoned")],
        key=lambda e: e["timestamp"],
    )
    max_streak = 0
    current_streak = 0
    for e in completion_events:
        if e["event_type"] == "action_completed":
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0

    # --- 5. Category fatigue (abandonment trend per category) ---
    # For each category: compare recent vs older abandonment rate
    cat_recent_starts = {}
    cat_recent_abandons = {}
    cat_older_starts = {}
    cat_older_abandons = {}

    for e in events:
        cat = (e.get("metadata") or {}).get("category")
        if not cat:
            continue
        is_recent = e["timestamp"] >= seven_days_ago

        if e["event_type"] == "action_started":
            bucket = cat_recent_starts if is_recent else cat_older_starts
            bucket[cat] = bucket.get(cat, 0) + 1
        elif e["event_type"] == "action_abandoned":
            bucket = cat_recent_abandons if is_recent else cat_older_abandons
            bucket[cat] = bucket.get(cat, 0) + 1

    category_fatigue = {}
    all_cats = set(cat_recent_starts) | set(cat_older_starts)
    for cat in all_cats:
        r_starts = cat_recent_starts.get(cat, 0)
        r_abandons = cat_recent_abandons.get(cat, 0)
        o_starts = cat_older_starts.get(cat, 0)
        o_abandons = cat_older_abandons.get(cat, 0)

        r_rate = r_abandons / r_starts if r_starts >= 3 else 0.0
        o_rate = o_abandons / o_starts if o_starts >= 3 else 0.0

        # Only flag if abandonment is rising and recent sample is meaningful
        if r_starts >= 3 and r_rate > o_rate + 0.1:
            category_fatigue[cat] = round(r_rate - o_rate, 3)

    return {
        "suggestion_ctr": round(suggestion_ctr, 3),
        "abandonment_rate": round(abandonment_rate, 3),
        "engagement_trend": round(engagement_trend, 3),
        "session_momentum": max_streak,
        "category_fatigue": category_fatigue,
    }


async def compute_user_features(db, user_id: str) -> Dict[str, Any]:
    """
    Compute all behavioral features for a single user.
    Returns a dict ready to upsert into user_features collection.
    """
    sessions = await db.user_sessions_history.find(
        {"user_id": user_id},
        {"_id": 0, "completed": 1, "category": 1, "started_at": 1, "actual_duration": 1, "action_id": 1}
    ).to_list(5000)

    if not sessions:
        return _empty_features(user_id)

    total = len(sessions)
    completed = [s for s in sessions if s.get("completed")]
    completed_count = len(completed)

    # 1. completion_rate_global
    completion_rate_global = completed_count / total if total > 0 else 0.0

    # 2. completion_rate_by_category
    cat_total = {}
    cat_completed = {}
    for s in sessions:
        cat = s.get("category", "unknown")
        cat_total[cat] = cat_total.get(cat, 0) + 1
        if s.get("completed"):
            cat_completed[cat] = cat_completed.get(cat, 0) + 1

    completion_rate_by_category = {
        cat: cat_completed.get(cat, 0) / count
        for cat, count in cat_total.items()
    }

    # 3. completion_rate_by_time_of_day
    tod_total = {}
    tod_completed = {}
    for s in sessions:
        bucket = _time_of_day_bucket(s.get("started_at", ""))
        tod_total[bucket] = tod_total.get(bucket, 0) + 1
        if s.get("completed"):
            tod_completed[bucket] = tod_completed.get(bucket, 0) + 1

    completion_rate_by_time_of_day = {
        bucket: tod_completed.get(bucket, 0) / count
        for bucket, count in tod_total.items()
    }

    # 4. avg_session_duration
    durations = [s["actual_duration"] for s in completed if s.get("actual_duration")]
    avg_session_duration = sum(durations) / len(durations) if durations else 5.0

    # 5. active_days_last_30
    thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    recent_completed = [
        s for s in completed
        if s.get("started_at", "") >= thirty_days_ago
    ]
    active_dates = set()
    for s in recent_completed:
        try:
            dt = datetime.fromisoformat(s["started_at"])
            active_dates.add(dt.date().isoformat())
        except (ValueError, TypeError):
            pass

    active_days_last_30 = len(active_dates)

    # 6. consistency_index
    consistency_index = min(active_days_last_30 / 30.0, 1.0)

    # 7. preferred_action_duration
    preferred_action_duration = _median(durations)

    # 8. energy_preference_by_time — which energy level the user completes best per bucket
    action_ids = list({s["action_id"] for s in completed if s.get("action_id")})
    energy_map = {}
    if action_ids:
        actions_docs = await db.micro_actions.find(
            {"action_id": {"$in": action_ids}},
            {"_id": 0, "action_id": 1, "energy_level": 1}
        ).to_list(len(action_ids))
        energy_map = {a["action_id"]: a.get("energy_level", "medium") for a in actions_docs}

    # Count completions by (bucket, energy)
    bucket_energy_counts = {}
    for s in completed:
        bucket = _time_of_day_bucket(s.get("started_at", ""))
        energy = energy_map.get(s.get("action_id", ""), "medium")
        key = (bucket, energy)
        bucket_energy_counts[key] = bucket_energy_counts.get(key, 0) + 1

    # For each bucket, pick the energy with most completions
    energy_preference_by_time = {}
    buckets_seen = {k[0] for k in bucket_energy_counts}
    for bucket in buckets_seen:
        best_energy = "medium"
        best_count = 0
        for energy in ("low", "medium", "high"):
            count = bucket_energy_counts.get((bucket, energy), 0)
            if count > best_count:
                best_count = count
                best_energy = energy
        energy_preference_by_time[bucket] = best_energy

    # 9. best_performing_buckets — time buckets sorted by completion rate (above global)
    best_performing_buckets = sorted(
        [b for b, r in completion_rate_by_time_of_day.items() if r >= completion_rate_global],
        key=lambda b: completion_rate_by_time_of_day[b],
        reverse=True,
    )

    # 10. avg_sessions_per_active_day
    avg_sessions_per_active_day = (
        len(recent_completed) / active_days_last_30
        if active_days_last_30 > 0 else 0.0
    )

    # 11. Engagement features from event_log
    engagement = await _compute_engagement_features(db, user_id)

    return {
        "user_id": user_id,
        "completion_rate_global": round(completion_rate_global, 3),
        "completion_rate_by_category": {k: round(v, 3) for k, v in completion_rate_by_category.items()},
        "completion_rate_by_time_of_day": {k: round(v, 3) for k, v in completion_rate_by_time_of_day.items()},
        "avg_session_duration": round(avg_session_duration, 1),
        "consistency_index": round(consistency_index, 3),
        "preferred_action_duration": round(preferred_action_duration, 1),
        "active_days_last_30": active_days_last_30,
        "energy_preference_by_time": energy_preference_by_time,
        "best_performing_buckets": best_performing_buckets,
        "avg_sessions_per_active_day": round(avg_sessions_per_active_day, 1),
        "total_sessions": total,
        "total_completed": completed_count,
        # Engagement features (from event_log)
        "suggestion_ctr": engagement["suggestion_ctr"],
        "abandonment_rate": engagement["abandonment_rate"],
        "engagement_trend": engagement["engagement_trend"],
        "session_momentum": engagement["session_momentum"],
        "category_fatigue": engagement["category_fatigue"],
        # Vertical AI Phase 2 features
        "learning_velocity": await _compute_learning_velocity(db, user_id),
        "difficulty_calibration": await _compute_difficulty_calibration(db, user_id, sessions),
        "coaching_stage": _compute_coaching_stage(completed_count, consistency_index, engagement["engagement_trend"]),
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "feature_version": FEATURE_VERSION,
    }


async def _compute_learning_velocity(db, user_id: str) -> dict:
    """Compute progression speed per active objective.

    Compares current_day vs expected pace (target_duration_days).
    velocity > 1.0 = faster than planned, < 1.0 = slower.
    """
    try:
        objectives = await db.objectives.find(
            {"user_id": user_id, "status": "active"},
            {"_id": 0, "objective_id": 1, "title": 1, "current_day": 1,
             "target_duration_days": 1, "created_at": 1},
        ).to_list(10)

        velocities = {}
        for obj in objectives:
            target = obj.get("target_duration_days", 30) or 30
            current = obj.get("current_day", 0) or 0
            # Calculate expected day based on calendar time since creation
            try:
                created = datetime.fromisoformat(obj.get("created_at", ""))
                if created.tzinfo is None:
                    created = created.replace(tzinfo=timezone.utc)
                elapsed_days = max(1, (datetime.now(timezone.utc) - created).days)
            except (ValueError, TypeError):
                elapsed_days = max(1, current)

            expected_day = min(target, elapsed_days)
            velocity = current / expected_day if expected_day > 0 else 1.0
            velocities[obj.get("objective_id", obj.get("title", "unknown"))] = round(velocity, 2)

        return velocities
    except Exception:
        return {}


async def _compute_difficulty_calibration(db, user_id: str, sessions: list) -> dict:
    """Compute completion rate by difficulty level.

    Returns optimal difficulty zone where completion is highest
    without being trivially easy (> 0.9 = too easy).
    """
    try:
        # Count completion by difficulty rating
        by_difficulty = {}
        for s in sessions:
            diff = s.get("difficulty_rating")
            if diff and isinstance(diff, (int, float)) and 1 <= diff <= 5:
                key = str(int(diff))
                if key not in by_difficulty:
                    by_difficulty[key] = {"completed": 0, "total": 0}
                by_difficulty[key]["total"] += 1
                if s.get("completed"):
                    by_difficulty[key]["completed"] += 1

        if not by_difficulty:
            return {"optimal_zone": [2, 3], "completion_by_difficulty": {}}

        rates = {}
        for diff, counts in by_difficulty.items():
            rates[diff] = round(counts["completed"] / counts["total"], 2) if counts["total"] > 0 else 0

        # Find optimal zone: highest completion that's not trivially easy (< 0.95)
        optimal = [int(d) for d, r in rates.items() if 0.4 <= r <= 0.95]
        if not optimal:
            optimal = [2, 3]  # Default zone

        return {
            "optimal_zone": sorted(optimal)[:2],
            "completion_by_difficulty": rates,
        }
    except Exception:
        return {"optimal_zone": [2, 3], "completion_by_difficulty": {}}


def _compute_coaching_stage(total_completed: int, consistency: float, trend: float) -> str:
    """Determine Prochaska TTM stage from behavioral signals.

    Mirrors coaching_engine.assess_stage() but computed in batch
    and stored in user_features for injection into prompts.
    """
    if total_completed == 0:
        return "precontemplation"
    elif total_completed < 10 or consistency < 0.15:
        return "contemplation"
    elif total_completed < 30 or consistency < 0.4:
        return "preparation"
    elif total_completed < 100 or consistency < 0.7:
        return "action"
    else:
        return "maintenance"


def _empty_features(user_id: str) -> Dict[str, Any]:
    """Default features for a user with no session history."""
    return {
        "user_id": user_id,
        "completion_rate_global": 0.5,
        "completion_rate_by_category": {},
        "completion_rate_by_time_of_day": {},
        "avg_session_duration": 5.0,
        "consistency_index": 0.0,
        "preferred_action_duration": 5.0,
        "active_days_last_30": 0,
        "energy_preference_by_time": {},
        "best_performing_buckets": [],
        "avg_sessions_per_active_day": 0.0,
        "total_sessions": 0,
        "total_completed": 0,
        # Engagement features defaults
        "suggestion_ctr": 0.0,
        "abandonment_rate": 0.0,
        "engagement_trend": 0.0,
        "session_momentum": 0,
        "category_fatigue": {},
        # Vertical AI Phase 2 features
        "learning_velocity": {},
        "difficulty_calibration": {"optimal_zone": [2, 3], "completion_by_difficulty": {}},
        "coaching_stage": "precontemplation",
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "feature_version": FEATURE_VERSION,
    }


async def compute_all_users_features(db) -> Dict[str, Any]:
    """Compute features for all users who have at least 1 session."""
    user_ids = await db.user_sessions_history.distinct("user_id")
    processed = 0
    errors = 0

    from services.weight_learner import compute_adaptive_weights

    for uid in user_ids:
        try:
            features = await compute_user_features(db, uid)

            # Learn adaptive weights if enough data
            adaptive = await compute_adaptive_weights(db, uid, features)
            if adaptive:
                features["adaptive_weights"] = adaptive
            else:
                features["adaptive_weights"] = None  # signals: use global defaults

            await db.user_features.update_one(
                {"user_id": uid},
                {"$set": features},
                upsert=True,
            )

            # Cache in Redis for fast reads by scoring engine
            from services.cache import cache_set, TTL_USER_FEATURES
            await cache_set(f"user_features:{uid}", features, ttl=TTL_USER_FEATURES)

            processed += 1
        except Exception as e:
            logger.error(f"Feature computation failed for user {uid}: {e}")
            errors += 1

    # Log the computation run
    today = datetime.now(timezone.utc).date().isoformat()
    await db.feature_computation_logs.insert_one({
        "date": today,
        "users_processed": processed,
        "errors": errors,
        "computed_at": datetime.now(timezone.utc).isoformat(),
    })

    logger.info(f"Feature computation complete: {processed} users processed, {errors} errors")
    return {
        "status": "completed",
        "date": today,
        "users_processed": processed,
        "errors": errors,
    }


async def feature_computation_loop(db):
    """Background loop that recomputes features periodically."""
    # Wait 60 seconds after startup before first computation
    await asyncio.sleep(60)

    while True:
        try:
            await compute_all_users_features(db)
        except Exception as e:
            logger.error(f"Feature computation loop error: {e}")

        # Recompute every 6 hours
        await asyncio.sleep(6 * 3600)
