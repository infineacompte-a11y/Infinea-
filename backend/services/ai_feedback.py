"""
InFinea — AI Response Quality Feedback.

Tracks user ratings on AI responses (thumbs up/down) and correlates
with prompt versions for scientific iteration.

Stores in ai_response_feedback collection, indexed by endpoint + prompt_version.
"""

import logging
from datetime import datetime, timezone

logger = logging.getLogger("infinea")


async def record_feedback(
    db,
    user_id: str,
    endpoint: str,
    rating: int,
    prompt_version: int = None,
    message_id: str = None,
    response_latency_ms: int = None,
) -> bool:
    """Record user feedback on an AI response.

    Args:
        db: MongoDB database instance.
        user_id: User who gave feedback.
        endpoint: Which AI endpoint (coach_chat, coach_dashboard, etc.)
        rating: 1 (not helpful) to 5 (very helpful). Thumbs down=1, up=5.
        prompt_version: Which prompt version generated the response.
        message_id: Optional ID of the specific coach message rated.
        response_latency_ms: Optional response time for performance tracking.

    Returns:
        True if feedback was recorded, False on error.
    """
    try:
        import uuid
        doc = {
            "feedback_id": f"fb_{uuid.uuid4().hex[:12]}",
            "user_id": user_id,
            "endpoint": endpoint,
            "rating": max(1, min(5, rating)),
            "prompt_version": prompt_version,
            "message_id": message_id,
            "response_latency_ms": response_latency_ms,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.ai_response_feedback.insert_one(doc)

        # Also update the coach_message if message_id provided
        if message_id:
            await db.coach_messages.update_one(
                {"_id": message_id} if len(message_id) == 24 else {"message_id": message_id},
                {"$set": {"feedback_rating": rating}},
            )

        return True
    except Exception as e:
        logger.debug(f"Error recording AI feedback: {e}")
        return False
