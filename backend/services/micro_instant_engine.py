"""
InFinea — Micro-Instant Engine.
Central intelligence service that predicts exploitable micro-instants
for the next 24 hours by combining calendar signals, behavioral patterns,
routine schedules, and spaced repetition urgency.

Architecture:
    collect_candidate_windows  →  enrich_with_confidence  →  assign_actions  →  rank_and_filter

Three signal sources:
    1. Calendar gaps (from slot_detector) — highest confidence
    2. Routine windows (declared by user) — medium confidence
    3. Behavioral patterns (learned from 14-day history) — variable confidence
"""

import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict

logger = logging.getLogger("micro_instant_engine")

# ── Confidence weights by source ──
SOURCE_CONFIDENCE = {
    "calendar_gap": 0.90,     # Calendar says user is free
    "routine_window": 0.70,   # User declared this time slot
    "behavioral_pattern": 0.50,  # Learned from history (base, adjusted up/down)
}

# ── Pattern analysis window ──
PATTERN_LOOKBACK_DAYS = 14
MIN_PATTERN_OCCURRENCES = 3   # Need 3+ sessions in a time slot to call it a pattern
SAFETY_BUFFER_MINUTES = 3     # Buffer before next event
MAX_INSTANTS_PER_DAY = 8      # Don't overwhelm the user
MIN_CONFIDENCE = 0.30         # Below this, don't suggest


# ═══════════════════════════════════════════════════════════════════
# 1. Collect candidate windows
# ═══════════════════════════════════════════════════════════════════


async def _collect_calendar_windows(
    db, user_id: str, events: List[Dict], settings: Dict
) -> List[Dict]:
    """Extract free time windows from calendar events using existing slot detector."""
    from services.slot_detector import detect_free_slots

    slots = await detect_free_slots(events, settings)

    windows = []
    for slot in slots:
        # Apply safety buffer
        try:
            end_dt = datetime.fromisoformat(slot["end_time"].replace("Z", "+00:00"))
            buffered_end = end_dt - timedelta(minutes=SAFETY_BUFFER_MINUTES)
            start_dt = datetime.fromisoformat(slot["start_time"].replace("Z", "+00:00"))

            if buffered_end <= start_dt:
                continue  # Buffer eats the entire slot

            effective_duration = int((buffered_end - start_dt).total_seconds() / 60)
            if effective_duration < settings.get("min_slot_duration", 5):
                continue
        except (ValueError, KeyError):
            continue

        windows.append({
            "window_start": slot["start_time"],
            "window_end": buffered_end.isoformat(),
            "duration_minutes": effective_duration,
            "source": "calendar_gap",
            "base_confidence": SOURCE_CONFIDENCE["calendar_gap"],
            "context": {
                "time_bucket": _time_bucket(start_dt.hour),
                "trigger": "gap_between_events",
            },
        })

    return windows


async def _collect_routine_windows(db, user_id: str) -> List[Dict]:
    """Extract upcoming routine time windows for today."""
    now = datetime.now(timezone.utc)
    today_weekday = now.weekday()  # 0=Monday

    routines = await db.routines.find({
        "user_id": user_id,
        "is_active": True,
    }, {"_id": 0}).to_list(20)

    windows = []
    for routine in routines:
        # Check frequency
        freq = routine.get("frequency", "daily")
        freq_days = routine.get("frequency_days")

        if freq == "weekdays" and today_weekday >= 5:
            continue
        if freq == "weekends" and today_weekday < 5:
            continue
        if freq == "custom" and freq_days and today_weekday not in freq_days:
            continue

        # Check if already completed today
        last_completed = routine.get("last_completed_at")
        if last_completed:
            try:
                last_dt = datetime.fromisoformat(last_completed.replace("Z", "+00:00"))
                if last_dt.date() == now.date():
                    continue  # Already done today
            except (ValueError, TypeError):
                pass

        # Map time_of_day to approximate window
        tod = routine.get("time_of_day", "anytime")
        duration = routine.get("total_minutes", 15)

        time_maps = {
            "morning": (8, 0),
            "afternoon": (13, 0),
            "evening": (19, 0),
        }

        if tod in time_maps:
            h, m = time_maps[tod]
            window_start = now.replace(hour=h, minute=m, second=0, microsecond=0)
        else:
            # "anytime" — suggest during best performing bucket
            window_start = now.replace(hour=10, minute=0, second=0, microsecond=0)

        # Skip if window is in the past
        if window_start + timedelta(minutes=duration) <= now:
            continue

        # Adjust start if partially past
        if window_start < now:
            window_start = now

        window_end = window_start + timedelta(minutes=duration)

        windows.append({
            "window_start": window_start.isoformat(),
            "window_end": window_end.isoformat(),
            "duration_minutes": duration,
            "source": "routine_window",
            "base_confidence": SOURCE_CONFIDENCE["routine_window"],
            "context": {
                "time_bucket": _time_bucket(window_start.hour),
                "trigger": "routine_scheduled",
                "routine_id": routine.get("routine_id"),
                "routine_name": routine.get("name"),
            },
        })

    return windows


async def _collect_behavioral_patterns(db, user_id: str) -> List[Dict]:
    """
    Detect recurring session patterns from the last 14 days.
    Groups sessions by hour-of-day and finds time slots where the user
    consistently engages. Each pattern gets a confidence proportional
    to its frequency and completion rate.
    """
    now = datetime.now(timezone.utc)
    lookback = (now - timedelta(days=PATTERN_LOOKBACK_DAYS)).isoformat()

    sessions = await db.user_sessions_history.find(
        {"user_id": user_id, "started_at": {"$gte": lookback}},
        {"_id": 0, "started_at": 1, "completed": 1, "actual_duration": 1, "category": 1},
    ).to_list(500)

    if not sessions:
        return []

    # Group sessions by hour-of-day
    hour_stats = defaultdict(lambda: {"total": 0, "completed": 0, "durations": []})

    for s in sessions:
        try:
            dt = datetime.fromisoformat(s["started_at"].replace("Z", "+00:00"))
            hour = dt.hour
        except (ValueError, TypeError, KeyError):
            continue

        hour_stats[hour]["total"] += 1
        if s.get("completed"):
            hour_stats[hour]["completed"] += 1
        dur = s.get("actual_duration")
        if dur:
            hour_stats[hour]["durations"].append(dur)

    # Find pattern hours (enough occurrences to be meaningful)
    windows = []
    for hour, stats in hour_stats.items():
        if stats["total"] < MIN_PATTERN_OCCURRENCES:
            continue

        completion_rate = stats["completed"] / stats["total"] if stats["total"] > 0 else 0
        avg_duration = (
            sum(stats["durations"]) / len(stats["durations"])
            if stats["durations"]
            else 7  # default 7 min
        )

        # Confidence = base × frequency_factor × completion_rate
        frequency_factor = min(stats["total"] / (PATTERN_LOOKBACK_DAYS * 0.7), 1.0)
        confidence = SOURCE_CONFIDENCE["behavioral_pattern"] * frequency_factor * max(completion_rate, 0.3)

        if confidence < MIN_CONFIDENCE:
            continue

        # Create window for today at this hour
        window_start = now.replace(hour=hour, minute=0, second=0, microsecond=0)

        # Skip past windows
        if window_start + timedelta(minutes=int(avg_duration)) <= now:
            continue

        if window_start < now:
            window_start = now

        window_end = window_start + timedelta(minutes=int(avg_duration))

        windows.append({
            "window_start": window_start.isoformat(),
            "window_end": window_end.isoformat(),
            "duration_minutes": int(avg_duration),
            "source": "behavioral_pattern",
            "base_confidence": round(confidence, 3),
            "context": {
                "time_bucket": _time_bucket(hour),
                "trigger": "learned_pattern",
                "pattern_sessions": stats["total"],
                "pattern_completion_rate": round(completion_rate, 2),
            },
        })

    return windows


# ═══════════════════════════════════════════════════════════════════
# 2. Enrich with confidence score
# ═══════════════════════════════════════════════════════════════════


async def _enrich_with_confidence(
    windows: List[Dict], features: Optional[Dict]
) -> List[Dict]:
    """
    Adjust confidence based on user behavioral features.
    Multipliers:
    - Time-of-day performance (strong signal)
    - Engagement trend (momentum indicator)
    - Consistency index (reliability indicator)
    """
    if not features:
        return windows

    for w in windows:
        confidence = w["base_confidence"]
        bucket = w["context"].get("time_bucket", "afternoon")

        # Time performance multiplier: how well user performs at this time
        tod_rates = features.get("completion_rate_by_time_of_day", {})
        tod_rate = tod_rates.get(bucket, 0.5)
        confidence *= (0.5 + tod_rate * 0.5)  # Range: 0.5x to 1.0x

        # Engagement trend boost/penalty
        trend = features.get("engagement_trend", 0.0)
        confidence *= (1.0 + trend * 0.2)  # Range: 0.8x to 1.2x

        # Consistency multiplier
        consistency = features.get("consistency_index", 0.3)
        confidence *= (0.7 + consistency * 0.3)  # Range: 0.7x to 1.0x

        # Momentum bonus: if user is on a streak, boost confidence
        momentum = features.get("session_momentum", 0)
        if momentum >= 3:
            confidence *= 1.1  # 10% boost for active streaks

        # Clamp to [0, 1]
        w["confidence_score"] = round(min(max(confidence, 0.0), 1.0), 3)

    return windows


# ═══════════════════════════════════════════════════════════════════
# 3. Assign best action to each window
# ═══════════════════════════════════════════════════════════════════


async def _assign_actions(
    db, user_id: str, windows: List[Dict], user_subscription: str = "free"
) -> List[Dict]:
    """
    For each window, find the best action using the scoring engine.
    Incorporates SR urgency: if a review is due, it takes priority.
    """
    from services.scoring_engine import get_next_best_action
    from services.spaced_repetition import get_review_queue

    # Check if any SR reviews are due (across all objectives)
    objectives = await db.objectives.find(
        {"user_id": user_id, "status": "active"},
        {"_id": 0, "objective_id": 1, "title": 1, "category": 1},
    ).to_list(20)

    sr_urgent = []
    for obj in objectives:
        queue = await get_review_queue(db, user_id, obj["objective_id"])
        for review in queue:
            sr_urgent.append({
                "skill": review["skill"],
                "days_overdue": review["days_overdue"],
                "objective_id": obj["objective_id"],
                "objective_title": obj.get("title", ""),
                "category": obj.get("category", "learning"),
            })

    # Sort SR by urgency (most overdue first)
    sr_urgent.sort(key=lambda r: r["days_overdue"], reverse=True)

    assigned_action_ids = set()  # Track to avoid duplicates across windows

    for w in windows:
        # Priority 1: SR review if overdue and fits the window
        if sr_urgent:
            top_review = sr_urgent[0]
            w["recommended_action"] = {
                "type": "spaced_repetition",
                "skill": top_review["skill"],
                "objective_id": top_review["objective_id"],
                "objective_title": top_review["objective_title"],
                "category": top_review["category"],
                "days_overdue": top_review["days_overdue"],
                "urgency": "high" if top_review["days_overdue"] >= 3 else "normal",
            }
            # Boost confidence for SR reviews (they're urgent by nature)
            w["confidence_score"] = min(w.get("confidence_score", 0.5) * 1.15, 1.0)
            sr_urgent.pop(0)  # Consume this review
            continue

        # Priority 2: Scoring engine picks the best action
        try:
            best = await get_next_best_action(
                db, user_id,
                slot_duration=w["duration_minutes"],
                slot_start_time=w.get("window_start"),
            )
            if best:
                action_id = best.get("action_id")
                # Avoid recommending the same action in multiple windows
                if action_id in assigned_action_ids:
                    best = await _get_alternative_action(
                        db, user_id, w["duration_minutes"],
                        w.get("window_start"), assigned_action_ids
                    )
                if best:
                    assigned_action_ids.add(best.get("action_id"))
                    w["recommended_action"] = {
                        "type": "micro_action",
                        "action_id": best["action_id"],
                        "title": best.get("title", ""),
                        "category": best.get("category", ""),
                        "duration_min": best.get("duration_min", 5),
                        "duration_max": best.get("duration_max", 10),
                        "energy_level": best.get("energy_level", "medium"),
                        "score": best.get("_score", 0),
                    }
                    continue
        except Exception as e:
            logger.warning(f"Scoring failed for window: {e}")

        # Priority 3: No action found — mark window as available
        w["recommended_action"] = None

    return windows


async def _get_alternative_action(
    db, user_id: str, duration: int, start_time: str, exclude_ids: set
) -> Optional[Dict]:
    """Find an alternative action excluding already-assigned ones."""
    from services.scoring_engine import get_next_best_action

    # Fetch candidates, then manually filter
    features = await db.user_features.find_one({"user_id": user_id}, {"_id": 0})
    if not features:
        return None

    actions = await db.micro_actions.find(
        {"duration_min": {"$lte": duration}, "action_id": {"$nin": list(exclude_ids)}},
        {"_id": 0},
    ).to_list(50)

    if not actions:
        return None

    # Score the first few manually
    from services.scoring_engine import score_action, _time_bucket_from_iso, _current_time_bucket

    bucket = _time_bucket_from_iso(start_time) if start_time else _current_time_bucket()
    energy_pref = features.get("energy_preference_by_time", {})

    context = {
        "energy_level": energy_pref.get(bucket, "medium"),
        "available_time": duration,
        "time_bucket": bucket,
        "recent_action_ids": exclude_ids,
        "feedback_signals": {},
    }

    best = None
    best_score = -1
    for action in actions[:30]:
        result = score_action(action, features, context)
        if result["score"] > best_score:
            best_score = result["score"]
            best = dict(action)
            best["_score"] = result["score"]

    return best


# ═══════════════════════════════════════════════════════════════════
# 4. Rank and deduplicate
# ═══════════════════════════════════════════════════════════════════


def _deduplicate_windows(windows: List[Dict]) -> List[Dict]:
    """
    Remove overlapping windows, keeping the one with highest confidence.
    Two windows overlap if one starts before the other ends.
    """
    if not windows:
        return []

    # Sort by confidence descending
    windows.sort(key=lambda w: w.get("confidence_score", 0), reverse=True)

    kept = []
    for w in windows:
        try:
            w_start = datetime.fromisoformat(w["window_start"].replace("Z", "+00:00"))
            w_end = datetime.fromisoformat(w["window_end"].replace("Z", "+00:00"))
        except (ValueError, KeyError):
            continue

        overlaps = False
        for k in kept:
            try:
                k_start = datetime.fromisoformat(k["window_start"].replace("Z", "+00:00"))
                k_end = datetime.fromisoformat(k["window_end"].replace("Z", "+00:00"))
            except (ValueError, KeyError):
                continue

            # Overlap check
            if w_start < k_end and w_end > k_start:
                overlaps = True
                break

        if not overlaps:
            kept.append(w)

    return kept


# ═══════════════════════════════════════════════════════════════════
# Public API — Main entry point
# ═══════════════════════════════════════════════════════════════════


async def predict_micro_instants(
    db,
    user_id: str,
    calendar_events: Optional[List[Dict]] = None,
    settings: Optional[Dict] = None,
    user_subscription: str = "free",
) -> List[Dict]:
    """
    Predict exploitable micro-instants for the next 24 hours.

    This is the main entry point of the Micro-Instant Engine.
    Combines calendar gaps, routine windows, and behavioral patterns
    to produce a ranked list of time windows with recommended actions.

    Args:
        db: MongoDB database handle
        user_id: User identifier
        calendar_events: Optional calendar events (if not provided, only
                         routines and patterns are used)
        settings: Slot detection settings (uses defaults if None)
        user_subscription: "free" or "premium"

    Returns:
        List of micro-instant predictions, sorted by confidence descending.
        Each item contains:
        - instant_id: unique identifier
        - window_start/end: ISO timestamps
        - duration_minutes: available time
        - confidence_score: 0-1 probability of exploitation
        - source: "calendar_gap" | "routine_window" | "behavioral_pattern"
        - recommended_action: action details or None
        - context: time_bucket, energy_level, trigger
    """
    from services.slot_detector import DEFAULT_SETTINGS
    from services.cache import cache_get, cache_set

    if settings is None:
        # Try user-specific settings, fallback to defaults
        user_prefs = await db.notification_preferences.find_one(
            {"user_id": user_id}, {"_id": 0}
        )
        settings = {**DEFAULT_SETTINGS, **(user_prefs or {})}

    # ── Step 1: Collect candidate windows from all sources ──
    all_windows = []

    if calendar_events is not None:
        calendar_windows = await _collect_calendar_windows(
            db, user_id, calendar_events, settings
        )
        all_windows.extend(calendar_windows)

    routine_windows = await _collect_routine_windows(db, user_id)
    all_windows.extend(routine_windows)

    pattern_windows = await _collect_behavioral_patterns(db, user_id)
    all_windows.extend(pattern_windows)

    if not all_windows:
        return []

    # ── Step 2: Enrich with user behavioral confidence ──
    features = await cache_get(f"user_features:{user_id}")
    if not features:
        features = await db.user_features.find_one(
            {"user_id": user_id}, {"_id": 0}
        )

    all_windows = await _enrich_with_confidence(all_windows, features)

    # ── Step 3: Deduplicate overlapping windows ──
    unique_windows = _deduplicate_windows(all_windows)

    # ── Step 4: Assign best action to each window ──
    enriched = await _assign_actions(db, user_id, unique_windows, user_subscription)

    # ── Step 5: Final ranking and limiting ──
    # Filter out windows below minimum confidence
    enriched = [w for w in enriched if w.get("confidence_score", 0) >= MIN_CONFIDENCE]

    # Sort by confidence descending
    enriched.sort(key=lambda w: w.get("confidence_score", 0), reverse=True)

    # Limit to max per day
    enriched = enriched[:MAX_INSTANTS_PER_DAY]

    # ── Step 6: Assign stable IDs and infer energy ──
    energy_prefs = (features or {}).get("energy_preference_by_time", {})

    result = []
    for w in enriched:
        bucket = w.get("context", {}).get("time_bucket", "afternoon")
        instant = {
            "instant_id": f"mi_{uuid.uuid4().hex[:12]}",
            "window_start": w["window_start"],
            "window_end": w["window_end"],
            "duration_minutes": w["duration_minutes"],
            "confidence_score": w["confidence_score"],
            "source": w["source"],
            "recommended_action": w.get("recommended_action"),
            "context": {
                **w.get("context", {}),
                "energy_level": energy_prefs.get(bucket, "medium"),
            },
        }
        result.append(instant)

    logger.info(
        f"Micro-instant prediction for {user_id}: "
        f"{len(result)} instants from {len(all_windows)} candidates "
        f"(calendar={len([w for w in all_windows if w['source'] == 'calendar_gap'])}, "
        f"routine={len([w for w in all_windows if w['source'] == 'routine_window'])}, "
        f"pattern={len([w for w in all_windows if w['source'] == 'behavioral_pattern'])})"
    )

    return result


# ═══════════════════════════════════════════════════════════════════
# Event tracking — Feedback for learning
# ═══════════════════════════════════════════════════════════════════


async def record_instant_outcome(
    db, user_id: str, instant_id: str, outcome: str, metadata: Optional[Dict] = None
):
    """
    Record whether a micro-instant was exploited, skipped, or dismissed.
    This feeds back into the behavioral pattern detection.

    Args:
        outcome: "exploited" | "skipped" | "dismissed"
    """
    from services.event_tracker import track_event

    event_type = {
        "exploited": "micro_instant_exploited",
        "skipped": "micro_instant_skipped",
        "dismissed": "micro_instant_dismissed",
    }.get(outcome, "micro_instant_skipped")

    await track_event(db, user_id, event_type, {
        "instant_id": instant_id,
        **(metadata or {}),
    })

    # Store outcome for future pattern analysis
    await db.micro_instant_outcomes.update_one(
        {"user_id": user_id, "instant_id": instant_id},
        {"$set": {
            "outcome": outcome,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            **(metadata or {}),
        }},
        upsert=True,
    )


# ═══════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════


def _time_bucket(hour: int) -> str:
    """Map hour to time-of-day bucket."""
    if 6 <= hour < 12:
        return "morning"
    elif 12 <= hour < 18:
        return "afternoon"
    elif 18 <= hour < 24:
        return "evening"
    return "night"
