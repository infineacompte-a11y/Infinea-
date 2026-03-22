"""
InFinea — Notification routes.
Preferences, push subscription, listing, and marking as read.
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from datetime import datetime, timezone

from database import db
from auth import get_current_user
from models import NotificationPreferences

router = APIRouter(prefix="/api")


@router.get("/notifications/preferences")
async def get_notification_preferences(user: dict = Depends(get_current_user)):
    """Get user's notification preferences"""
    prefs = await db.notification_preferences.find_one(
        {"user_id": user["user_id"]}, {"_id": 0}
    )

    if not prefs:
        return {
            "user_id": user["user_id"],
            "daily_reminder": True,
            "reminder_time": "09:00",
            "streak_alerts": True,
            "achievement_alerts": True,
            "weekly_summary": True,
        }

    return prefs


@router.put("/notifications/preferences")
async def update_notification_preferences(
    prefs: NotificationPreferences,
    user: dict = Depends(get_current_user),
):
    """Update user's notification preferences"""
    prefs_doc = {
        "user_id": user["user_id"],
        **prefs.model_dump(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    await db.notification_preferences.update_one(
        {"user_id": user["user_id"]}, {"$set": prefs_doc}, upsert=True
    )

    return prefs_doc


@router.post("/notifications/subscribe")
async def subscribe_push_notifications(
    request: Request,
    user: dict = Depends(get_current_user),
):
    """Subscribe to push notifications (store push subscription)"""
    body = await request.json()
    subscription = body.get("subscription")

    if not subscription:
        raise HTTPException(status_code=400, detail="Subscription data required")

    await db.push_subscriptions.update_one(
        {"user_id": user["user_id"]},
        {
            "$set": {
                "user_id": user["user_id"],
                "subscription": subscription,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        },
        upsert=True,
    )

    return {"message": "Subscribed to push notifications"}


@router.get("/notifications")
async def get_user_notifications(
    user: dict = Depends(get_current_user),
    limit: int = 20,
):
    """Get user's notifications"""
    notifications = (
        await db.notifications.find({"user_id": user["user_id"]}, {"_id": 0})
        .sort("created_at", -1)
        .limit(limit)
        .to_list(limit)
    )

    return notifications


@router.post("/notifications/mark-read")
async def mark_notifications_read(
    request: Request,
    user: dict = Depends(get_current_user),
):
    """Mark notifications as read"""
    body = await request.json()
    notification_ids = body.get("notification_ids", [])

    if notification_ids:
        await db.notifications.update_many(
            {
                "user_id": user["user_id"],
                "notification_id": {"$in": notification_ids},
            },
            {"$set": {"read": True}},
        )
    else:
        await db.notifications.update_many(
            {"user_id": user["user_id"]}, {"$set": {"read": True}}
        )

    return {"message": "Notifications marked as read"}
