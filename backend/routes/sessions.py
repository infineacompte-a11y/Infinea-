"""
InFinea — Session tracking routes.
Start/complete sessions and view progress stats.
"""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone, timedelta
import uuid

from database import db
from auth import get_current_user
from models import SessionStart, SessionComplete
from routes.badges import check_and_award_badges
from services.activity_service import emit_session_activity, emit_badge_activity, emit_streak_activity
from services.challenge_service import update_challenge_progress

router = APIRouter(prefix="/api")


@router.post("/sessions/start")
async def start_session(
    session_data: SessionStart,
    user: dict = Depends(get_current_user),
):
    """Start a micro-action session"""
    action = await db.micro_actions.find_one(
        {"action_id": session_data.action_id}, {"_id": 0}
    )
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    if action.get("is_premium") and user.get("subscription_tier") == "free":
        raise HTTPException(status_code=403, detail="Premium action - upgrade required")

    session_id = f"session_{uuid.uuid4().hex[:12]}"
    session_doc = {
        "session_id": session_id,
        "user_id": user["user_id"],
        "action_id": session_data.action_id,
        "action_title": action["title"],
        "category": action["category"],
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
        "actual_duration": None,
        "completed": False,
    }

    await db.user_sessions_history.insert_one(session_doc)

    return {
        "session_id": session_id,
        "action": action,
        "started_at": session_doc["started_at"],
    }


@router.post("/sessions/complete")
async def complete_session(
    completion: SessionComplete,
    user: dict = Depends(get_current_user),
):
    """Complete a micro-action session and update stats"""
    session = await db.user_sessions_history.find_one(
        {"session_id": completion.session_id, "user_id": user["user_id"]}, {"_id": 0}
    )

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    await db.user_sessions_history.update_one(
        {"session_id": completion.session_id},
        {
            "$set": {
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "actual_duration": completion.actual_duration,
                "completed": completion.completed,
                "notes": completion.notes,
            }
        },
    )

    if completion.completed:
        user_doc = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0})

        # Calculate streak
        today = datetime.now(timezone.utc).date()
        last_session = user_doc.get("last_session_date")

        new_streak = user_doc.get("streak_days", 0)
        if last_session:
            if isinstance(last_session, str):
                last_date = datetime.fromisoformat(last_session).date()
            else:
                last_date = (
                    last_session.date()
                    if hasattr(last_session, "date")
                    else last_session
                )

            if last_date == today - timedelta(days=1):
                new_streak += 1
            elif last_date != today:
                new_streak = 1
        else:
            new_streak = 1

        await db.users.update_one(
            {"user_id": user["user_id"]},
            {
                "$inc": {"total_time_invested": completion.actual_duration},
                "$set": {
                    "streak_days": new_streak,
                    "last_session_date": today.isoformat(),
                },
            },
        )

        # Check for new badges
        new_badges = await check_and_award_badges(user["user_id"])

        # Create notification for new badges
        for badge in new_badges:
            notification = {
                "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
                "user_id": user["user_id"],
                "type": "badge_earned",
                "title": f"Nouveau badge : {badge['name']}",
                "message": f"Félicitations ! Vous avez obtenu le badge {badge['name']}",
                "icon": badge["icon"],
                "read": False,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            await db.notifications.insert_one(notification)

        # Emit social activities (non-blocking — failures don't affect session)
        await emit_session_activity(user["user_id"], {
            "action_title": session.get("action_title", "Micro-action"),
            "category": session.get("category", ""),
            "actual_duration": completion.actual_duration,
        })

        for badge in new_badges:
            await emit_badge_activity(user["user_id"], badge)

        await emit_streak_activity(user["user_id"], new_streak)

        # Update challenge progress (event-driven — auto-tracks active challenges)
        await update_challenge_progress(user["user_id"], {
            "category": session.get("category", ""),
            "actual_duration": completion.actual_duration,
        })

        return {
            "message": "Session completed!",
            "time_added": completion.actual_duration,
            "new_streak": new_streak,
            "total_time": user_doc.get("total_time_invested", 0)
            + completion.actual_duration,
            "new_badges": new_badges,
        }

    return {"message": "Session recorded"}


@router.get("/stats")
async def get_user_stats(user: dict = Depends(get_current_user)):
    """Get user progress statistics"""
    pipeline = [
        {"$match": {"user_id": user["user_id"], "completed": True}},
        {
            "$group": {
                "_id": "$category",
                "count": {"$sum": 1},
                "total_time": {"$sum": "$actual_duration"},
            }
        },
    ]
    category_stats = await db.user_sessions_history.aggregate(pipeline).to_list(10)

    sessions_by_category = {}
    time_by_category = {}
    for stat in category_stats:
        sessions_by_category[stat["_id"]] = stat["count"]
        time_by_category[stat["_id"]] = stat["total_time"]

    recent = (
        await db.user_sessions_history.find(
            {"user_id": user["user_id"], "completed": True}, {"_id": 0}
        )
        .sort("completed_at", -1)
        .limit(10)
        .to_list(10)
    )

    total_sessions = await db.user_sessions_history.count_documents(
        {"user_id": user["user_id"], "completed": True}
    )

    return {
        "total_time_invested": user.get("total_time_invested", 0),
        "total_sessions": total_sessions,
        "streak_days": user.get("streak_days", 0),
        "sessions_by_category": sessions_by_category,
        "time_by_category": time_by_category,
        "recent_sessions": recent,
    }
