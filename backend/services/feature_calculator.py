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

FEATURE_VERSION = 1


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


async def compute_user_features(db, user_id: str) -> Dict[str, Any]:
    """
    Compute all behavioral features for a single user.
    Returns a dict ready to upsert into user_features collection.
    """
    sessions = await db.user_sessions_history.find(
        {"user_id": user_id},
        {"_id": 0, "completed": 1, "category": 1, "started_at": 1, "actual_duration": 1}
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

    return {
        "user_id": user_id,
        "completion_rate_global": round(completion_rate_global, 3),
        "completion_rate_by_category": {k: round(v, 3) for k, v in completion_rate_by_category.items()},
        "completion_rate_by_time_of_day": {k: round(v, 3) for k, v in completion_rate_by_time_of_day.items()},
        "avg_session_duration": round(avg_session_duration, 1),
        "consistency_index": round(consistency_index, 3),
        "preferred_action_duration": round(preferred_action_duration, 1),
        "active_days_last_30": active_days_last_30,
        "total_sessions": total,
        "total_completed": completed_count,
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "feature_version": FEATURE_VERSION,
    }


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
        "total_sessions": 0,
        "total_completed": 0,
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "feature_version": FEATURE_VERSION,
    }


async def compute_all_users_features(db) -> Dict[str, Any]:
    """Compute features for all users who have at least 1 session."""
    user_ids = await db.user_sessions_history.distinct("user_id")
    processed = 0
    errors = 0

    for uid in user_ids:
        try:
            features = await compute_user_features(db, uid)
            await db.user_features.update_one(
                {"user_id": uid},
                {"$set": features},
                upsert=True,
            )
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
