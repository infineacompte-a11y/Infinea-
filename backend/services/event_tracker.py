"""
Event tracking service for InFinea.
Logs structured behavioral events to the event_log collection.
Non-blocking: tracking failures never break the calling route.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# All valid event types — add new ones here as needed
EVENT_TYPES = {
    # Suggestions
    "suggestion_generated",
    "suggestion_viewed",
    "suggestion_clicked",
    # Actions / Sessions
    "action_started",
    "action_completed",
    "action_abandoned",
    # AI
    "ai_coach_served",
    "ai_debrief_generated",
    "ai_weekly_analysis_generated",
    "ai_streak_check_served",
    "ai_action_created",
    # Calendar / Slots
    "calendar_slot_detected",
    "slot_dismissed",
    # Auth
    "user_registered",
    "user_logged_in",
    # Premium
    "premium_activated",
    "premium_checkout_started",
}


async def track_event(
    db,
    user_id: str,
    event_type: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log a behavioral event to MongoDB.

    Usage:
        await track_event(db, user["user_id"], "suggestion_generated", {"category": "productivity"})

    This function is fire-and-forget safe: it catches all exceptions
    so the calling route never fails because of tracking.
    """
    if event_type not in EVENT_TYPES:
        logger.warning(f"Unknown event_type: {event_type} — skipping")
        return

    doc = {
        "user_id": user_id,
        "event_type": event_type,
        "metadata": metadata or {},
        "timestamp": datetime.now(timezone.utc),
    }

    try:
        await db.event_log.insert_one(doc)
    except Exception as e:
        logger.error(f"Event tracking failed for {event_type}: {e}")
