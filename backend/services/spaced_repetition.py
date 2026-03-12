"""
Spaced Repetition Engine for InFinea — SM-2 inspired algorithm.

Determines which skills/steps need review based on:
- Time since last practice (interval scheduling)
- User recall quality (ease factor adjustment)
- Mastery level (completion-weighted priority)

Reference: SuperMemo SM-2 algorithm adapted for micro-session learning.

Core concepts:
- Each skill tracks: ease_factor, interval_days, next_review_date, repetitions
- After each review, quality (1-5) adjusts the ease factor and next interval
- Priority queue: overdue reviews sorted by urgency (most overdue first)
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# SM-2 defaults
DEFAULT_EASE_FACTOR = 2.5
MIN_EASE_FACTOR = 1.3
INITIAL_INTERVALS = [1, 3]  # First review after 1 day, second after 3 days


def compute_next_review(
    repetitions: int,
    ease_factor: float,
    quality: int,
    previous_interval: int = 0,
) -> dict:
    """SM-2 algorithm: compute next interval and updated ease factor.

    Args:
        repetitions: number of consecutive successful reviews (quality >= 3)
        ease_factor: current ease factor (starts at 2.5)
        quality: user self-assessed recall quality (1-5)
            1 = total blackout, 2 = wrong but recognized, 3 = correct with difficulty,
            4 = correct with hesitation, 5 = perfect recall
        previous_interval: last interval in days

    Returns:
        dict with next_interval, new_ease_factor, new_repetitions
    """
    # Clamp quality to valid range
    quality = max(1, min(5, quality))

    if quality >= 3:
        # Successful recall — increase interval
        if repetitions == 0:
            next_interval = INITIAL_INTERVALS[0]
        elif repetitions == 1:
            next_interval = INITIAL_INTERVALS[1]
        else:
            next_interval = round(previous_interval * ease_factor)
        new_repetitions = repetitions + 1
    else:
        # Failed recall — reset to beginning
        next_interval = INITIAL_INTERVALS[0]
        new_repetitions = 0

    # Update ease factor (SM-2 formula)
    new_ease = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    new_ease = max(MIN_EASE_FACTOR, round(new_ease, 2))

    # Cap interval at 180 days (6 months) for micro-learning context
    next_interval = min(next_interval, 180)

    return {
        "next_interval": next_interval,
        "ease_factor": new_ease,
        "repetitions": new_repetitions,
    }


async def get_review_queue(db, user_id: str, objective_id: str) -> list:
    """Get skills due for review, sorted by urgency (most overdue first).

    Reads from the sr_reviews collection which tracks per-skill review state.
    Falls back to curriculum-based detection if no review data exists.
    """
    now = datetime.now(timezone.utc)

    # Fetch all review records for this objective
    reviews = await db.sr_reviews.find({
        "user_id": user_id,
        "objective_id": objective_id,
    }).to_list(200)

    due_reviews = []
    for review in reviews:
        next_date_str = review.get("next_review_date")
        if not next_date_str:
            continue
        try:
            next_date = datetime.fromisoformat(next_date_str)
            if next_date.tzinfo is None:
                next_date = next_date.replace(tzinfo=timezone.utc)
            if next_date <= now:
                days_overdue = (now - next_date).days
                due_reviews.append({
                    "skill": review["skill"],
                    "days_overdue": days_overdue,
                    "ease_factor": review.get("ease_factor", DEFAULT_EASE_FACTOR),
                    "repetitions": review.get("repetitions", 0),
                    "interval": review.get("interval_days", 0),
                    "last_quality": review.get("last_quality"),
                })
        except (ValueError, TypeError):
            continue

    # Sort by most overdue first
    due_reviews.sort(key=lambda r: r["days_overdue"], reverse=True)
    return due_reviews


async def get_or_init_review(db, user_id: str, objective_id: str, skill: str) -> dict:
    """Get or create a review record for a skill."""
    existing = await db.sr_reviews.find_one({
        "user_id": user_id,
        "objective_id": objective_id,
        "skill": skill,
    })
    if existing:
        return existing

    now = datetime.now(timezone.utc)
    doc = {
        "user_id": user_id,
        "objective_id": objective_id,
        "skill": skill,
        "ease_factor": DEFAULT_EASE_FACTOR,
        "interval_days": 0,
        "repetitions": 0,
        "next_review_date": now.isoformat(),  # Due immediately
        "last_reviewed": None,
        "last_quality": None,
        "created_at": now.isoformat(),
    }
    await db.sr_reviews.insert_one(doc)
    return doc


async def record_review(db, user_id: str, objective_id: str, skill: str, quality: int) -> dict:
    """Record a review result and compute next review date.

    Args:
        quality: 1-5 recall quality rating

    Returns:
        Updated review state with next_review_date
    """
    review = await get_or_init_review(db, user_id, objective_id, skill)
    now = datetime.now(timezone.utc)

    result = compute_next_review(
        repetitions=review.get("repetitions", 0),
        ease_factor=review.get("ease_factor", DEFAULT_EASE_FACTOR),
        quality=quality,
        previous_interval=review.get("interval_days", 0),
    )

    next_review_date = now + timedelta(days=result["next_interval"])

    await db.sr_reviews.update_one(
        {
            "user_id": user_id,
            "objective_id": objective_id,
            "skill": skill,
        },
        {"$set": {
            "ease_factor": result["ease_factor"],
            "interval_days": result["next_interval"],
            "repetitions": result["repetitions"],
            "next_review_date": next_review_date.isoformat(),
            "last_reviewed": now.isoformat(),
            "last_quality": quality,
        }},
        upsert=True,
    )

    return {
        "skill": skill,
        "quality": quality,
        "next_interval_days": result["next_interval"],
        "next_review_date": next_review_date.isoformat(),
        "ease_factor": result["ease_factor"],
        "repetitions": result["repetitions"],
    }


async def seed_reviews_from_curriculum(db, user_id: str, objective_id: str, curriculum: list):
    """Initialize review records for completed curriculum steps.

    Called when a user first accesses spaced repetition for an objective,
    to bootstrap review data from existing progress.
    """
    now = datetime.now(timezone.utc)
    completed_skills = {}

    for step in curriculum:
        if not step.get("completed"):
            continue
        focus = (step.get("focus") or "").strip()
        if not focus:
            continue
        completed_at = step.get("completed_at", now.isoformat())
        # Track latest completion per skill
        if focus not in completed_skills or completed_at > completed_skills[focus]:
            completed_skills[focus] = completed_at

    seeded = 0
    for skill, last_completed in completed_skills.items():
        existing = await db.sr_reviews.find_one({
            "user_id": user_id,
            "objective_id": objective_id,
            "skill": skill,
        })
        if existing:
            continue  # Already tracked

        try:
            last_dt = datetime.fromisoformat(last_completed)
            if last_dt.tzinfo is None:
                last_dt = last_dt.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            last_dt = now

        # Set next review based on time since last practice
        days_since = (now - last_dt).days
        if days_since >= 3:
            next_review = now  # Overdue — review now
        else:
            next_review = last_dt + timedelta(days=INITIAL_INTERVALS[1])

        await db.sr_reviews.insert_one({
            "user_id": user_id,
            "objective_id": objective_id,
            "skill": skill,
            "ease_factor": DEFAULT_EASE_FACTOR,
            "interval_days": INITIAL_INTERVALS[1],
            "repetitions": 1,  # Assume first practice was successful
            "next_review_date": next_review.isoformat(),
            "last_reviewed": last_completed,
            "last_quality": 4,  # Assume decent recall from initial learning
            "created_at": now.isoformat(),
        })
        seeded += 1

    if seeded:
        logger.info(f"Seeded {seeded} SR reviews for objective {objective_id}")
    return seeded
