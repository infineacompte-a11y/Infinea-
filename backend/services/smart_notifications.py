"""
Smart Notifications Service for InFinea.
Handles scheduling and sending notifications for detected free slots.
Enhanced with knowledge engine for personalized, science-backed copy.
"""
import logging
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
import uuid

logger = logging.getLogger(__name__)

# Knowledge-enriched notification copy (replaces static templates)
# Each message is backed by behavioral science for higher engagement.
SMART_COPY = {
    "morning": [
        "Ton cerveau est au pic de concentration 2-4h apres le reveil — c'est le moment ideal.",
        "Une session de {duration} min maintenant ancre l'habitude pour toute la journee.",
        "Les utilisateurs qui pratiquent le matin ont un taux de completion 23% superieur.",
    ],
    "afternoon": [
        "Micro-pause de {duration} min? Le changement d'activite restaure les ressources attentionnelles.",
        "5 min de pratique deliberee maintenant valent plus que 30 min ce soir distrait.",
        "Ton creneau de l'apres-midi est libre — parfait pour {action_name}.",
    ],
    "evening": [
        "Session du soir: consolide ce que tu as appris aujourd'hui (effet de spacing).",
        "La pratique avant le sommeil renforce la consolidation en memoire long terme.",
        "{duration} min de {action_name} pour terminer la journee sur une micro-victoire?",
    ],
    "default": [
        "Tu as {duration} min de libre — transforme-les en micro-victoire avec {action_name}.",
        "Chaque session courte renforce tes connexions neuronales. {duration} min suffisent.",
        "Ton creneau est detecte: {action_name} est pret pour toi.",
    ],
}


def _get_smart_copy(duration: int, action_name: str, time_bucket: str = "default") -> str:
    """Select a knowledge-enriched notification message."""
    templates = SMART_COPY.get(time_bucket, SMART_COPY["default"])
    template = random.choice(templates)
    return template.format(duration=duration, action_name=action_name)


def _get_time_bucket(iso_time: str) -> str:
    """Extract time bucket from ISO timestamp."""
    try:
        hour = datetime.fromisoformat(iso_time.replace('Z', '+00:00')).hour
        if 6 <= hour < 12:
            return "morning"
        elif 12 <= hour < 18:
            return "afternoon"
        elif 18 <= hour < 24:
            return "evening"
    except (ValueError, TypeError):
        pass
    return "default"


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
    
    # Build notification content with knowledge-enriched copy
    duration = slot['duration_minutes']
    action_name = suggested_action['title'] if suggested_action else "une micro-action"
    action_id = suggested_action['action_id'] if suggested_action else None
    time_bucket = _get_time_bucket(slot.get('start_time', ''))
    smart_message = _get_smart_copy(duration, action_name, time_bucket)

    notification = {
        "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
        "user_id": user_id,
        "type": "free_slot",
        "title": f"Creneau de {duration} min detecte",
        "message": smart_message,
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
        
        # Find matching action (scoring-enhanced when features available)
        suggested_action = await match_action_to_slot(
            slot, actions, user_subscription, db=db, user_id=user_id
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
