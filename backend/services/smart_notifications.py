"""
Smart Notifications Service for InFinea.
Handles scheduling and sending notifications for detected free slots.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
import uuid

logger = logging.getLogger(__name__)


async def create_slot_notification(
    db,
    user_id: str,
    slot: Dict,
    suggested_action: Optional[Dict] = None
) -> Dict:
    """
    Create a notification for an upcoming free slot.
    
    Args:
        db: MongoDB database instance
        user_id: User ID
        slot: The detected free slot
        suggested_action: Optional suggested micro-action
    
    Returns:
        Created notification document
    """
    now = datetime.now(timezone.utc)
    slot_start = datetime.fromisoformat(slot['start_time'].replace('Z', '+00:00'))
    
    # Calculate notification time
    prefs = await db.notification_preferences.find_one(
        {"user_id": user_id},
        {"_id": 0}
    )
    advance_minutes = (prefs or {}).get('advance_notification_minutes', 5)
    notification_time = slot_start - timedelta(minutes=advance_minutes)
    
    # Skip if notification time is in the past
    if notification_time < now:
        notification_time = now
    
    # Build notification content
    duration = slot['duration_minutes']
    action_name = suggested_action['title'] if suggested_action else "une micro-action"
    action_id = suggested_action['action_id'] if suggested_action else None
    
    notification = {
        "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
        "user_id": user_id,
        "type": "free_slot",
        "title": f"⏰ Créneau libre dans {advance_minutes} minutes",
        "message": f"Vous avez {duration} min - Suggestion: {action_name}",
        "icon": "clock",
        "read": False,
        "slot_id": slot['slot_id'],
        "suggested_action_id": action_id,
        "scheduled_for": notification_time.isoformat(),
        "created_at": now.isoformat(),
        "sent": False,
        "data": {
            "url": f"/session/start/{action_id}" if action_id else "/dashboard",
            "slot_duration": duration,
            "slot_start": slot['start_time']
        }
    }
    
    await db.notifications.insert_one(notification)
    
    return notification


async def get_pending_notifications(db, user_id: str) -> list:
    """Get pending notifications for a user that haven't been sent yet."""
    now = datetime.now(timezone.utc)
    
    notifications = await db.notifications.find({
        "user_id": user_id,
        "type": "free_slot",
        "sent": False,
        "scheduled_for": {"$lte": now.isoformat()}
    }, {"_id": 0}).to_list(20)
    
    return notifications


async def mark_notification_sent(db, notification_id: str):
    """Mark a notification as sent."""
    await db.notifications.update_one(
        {"notification_id": notification_id},
        {"$set": {
            "sent": True,
            "sent_at": datetime.now(timezone.utc).isoformat()
        }}
    )


async def build_push_payload(notification: Dict) -> Dict:
    """Build the payload for a push notification."""
    return {
        "title": notification['title'],
        "body": notification['message'],
        "icon": "/icons/icon-192x192.png",
        "badge": "/icons/icon-72x72.png",
        "tag": f"slot-{notification.get('slot_id', 'unknown')}",
        "data": notification.get('data', {}),
        "actions": [
            {"action": "start", "title": "Commencer"},
            {"action": "dismiss", "title": "Pas maintenant"}
        ],
        "vibrate": [100, 50, 100],
        "requireInteraction": True
    }


async def schedule_slot_notifications(
    db,
    user_id: str,
    slots: list,
    actions: list,
    user_subscription: str = 'free'
):
    """
    Schedule notifications for detected free slots.
    
    Args:
        db: MongoDB database instance
        user_id: User ID
        slots: List of detected free slots
        actions: List of available micro-actions
        user_subscription: User's subscription tier
    """
    from .slot_detector import match_action_to_slot
    
    for slot in slots:
        # Check if notification already exists for this slot
        existing = await db.notifications.find_one({
            "user_id": user_id,
            "slot_id": slot['slot_id']
        })
        
        if existing:
            continue
        
        # Find matching action
        suggested_action = await match_action_to_slot(
            slot, actions, user_subscription
        )
        
        # Create notification
        await create_slot_notification(
            db, user_id, slot, suggested_action
        )
        
        # Update slot with suggested action
        if suggested_action:
            slot['suggested_action_id'] = suggested_action['action_id']
        
        # Save slot to database
        await db.detected_free_slots.update_one(
            {"slot_id": slot['slot_id']},
            {"$set": {**slot, "user_id": user_id}},
            upsert=True
        )


async def cleanup_old_slots(db, user_id: str):
    """Remove old/expired slots from the database."""
    now = datetime.now(timezone.utc)
    
    await db.detected_free_slots.delete_many({
        "user_id": user_id,
        "end_time": {"$lt": now.isoformat()}
    })
