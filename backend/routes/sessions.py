"""InFinea — Session tracking + recap routes."""

import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

import httpx
from fastapi import APIRouter, HTTPException, Depends, Request

from database import db
from auth import get_current_user
from config import limiter, logger
from models import SessionStart, SessionComplete
from helpers import send_push_to_user
from services.event_tracker import track_event
from services.feedback_loop import record_signal
from integrations.encryption import decrypt_token

router = APIRouter()


# ============== SESSION TRACKING ROUTES ==============

@router.post("/sessions/start")
async def start_session(
    session_data: SessionStart,
    user: dict = Depends(get_current_user)
):
    """Start a micro-action session"""
    action = await db.micro_actions.find_one({"action_id": session_data.action_id}, {"_id": 0})
    if not action:
        # Fallback to custom actions
        action = await db.user_custom_actions.find_one(
            {"action_id": session_data.action_id, "created_by": user["user_id"]},
            {"_id": 0}
        )
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    # Check premium access
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
        "completed": False
    }

    await db.user_sessions_history.insert_one(session_doc)

    await track_event(db, user["user_id"], "action_started", {
        "session_id": session_id,
        "action_id": session_data.action_id,
        "category": action["category"],
        "action_title": action["title"],
    })

    # Feedback loop: user clicked on this action
    await record_signal(db, user["user_id"], session_data.action_id, "click")

    return {
        "session_id": session_id,
        "action": action,
        "started_at": session_doc["started_at"]
    }

async def _auto_sync_session(user_id: str, session_data: dict):
    """Auto-export a completed session to connected integrations (Todoist, Notion, Slack).
    Runs silently — errors are logged but never block the main flow."""
    try:
        integrations = await db.user_integrations.find(
            {"user_id": user_id, "sync_enabled": True},
            {"_id": 0}
        ).to_list(10)

        if not integrations:
            return

        session_id = session_data.get("session_id")
        title = session_data.get("action_title", "Micro-action")
        duration = session_data.get("actual_duration", 5)
        category = session_data.get("category", "N/A")
        completed_at = session_data.get("completed_at", "")

        async with httpx.AsyncClient(timeout=10.0) as http_client:
            for integration in integrations:
                service = integration.get("service")
                access_token = integration.get("access_token")
                if not access_token:
                    continue

                # Decrypt token
                try:
                    decrypted = decrypt_token(access_token)
                    if decrypted:
                        access_token = decrypted
                except Exception:
                    pass

                # Skip if already synced
                already = await db.synced_events.find_one({
                    "user_id": user_id, "service": service,
                    "session_id": session_id
                })
                if already:
                    continue

                try:
                    if service == "todoist":
                        resp = await http_client.post(
                            "https://api.todoist.com/rest/v2/tasks",
                            json={"content": f"\u2705 {title}", "description": f"Session InFinea compl\u00e9t\u00e9e \u2014 {duration} min"},
                            headers={"Authorization": f"Bearer {access_token}"}
                        )
                        if resp.status_code in (200, 201):
                            task_id = resp.json().get("id")
                            await http_client.post(
                                f"https://api.todoist.com/rest/v2/tasks/{task_id}/close",
                                headers={"Authorization": f"Bearer {access_token}"}
                            )
                            await db.synced_events.insert_one({
                                "user_id": user_id, "service": service,
                                "session_id": session_id,
                                "external_id": str(task_id),
                                "synced_at": datetime.now(timezone.utc).isoformat()
                            })

                    elif service == "notion":
                        # Find parent page
                        search_resp = await http_client.post(
                            "https://api.notion.com/v1/search",
                            json={"query": "InFinea Sessions", "filter": {"property": "object", "value": "page"}},
                            headers={"Authorization": f"Bearer {access_token}", "Notion-Version": "2022-06-28"}
                        )
                        parent_page_id = None
                        if search_resp.status_code == 200:
                            results = search_resp.json().get("results", [])
                            if results:
                                parent_page_id = results[0]["id"]
                        if not parent_page_id:
                            fallback = await http_client.post(
                                "https://api.notion.com/v1/search",
                                json={"filter": {"property": "object", "value": "page"}, "page_size": 1},
                                headers={"Authorization": f"Bearer {access_token}", "Notion-Version": "2022-06-28"}
                            )
                            if fallback.status_code == 200:
                                pages = fallback.json().get("results", [])
                                if pages:
                                    parent_page_id = pages[0]["id"]

                        if parent_page_id:
                            page_data = {
                                "parent": {"page_id": parent_page_id},
                                "properties": {"title": {"title": [{"text": {"content": f"\u2705 {title} \u2014 {duration} min"}}]}},
                                "children": [{"object": "block", "type": "paragraph", "paragraph": {
                                    "rich_text": [{"text": {"content": f"Cat\u00e9gorie: {category}\nDur\u00e9e: {duration} min\nDate: {completed_at[:10] if completed_at else 'N/A'}"}}]
                                }}]
                            }
                            resp = await http_client.post(
                                "https://api.notion.com/v1/pages", json=page_data,
                                headers={"Authorization": f"Bearer {access_token}", "Notion-Version": "2022-06-28"}
                            )
                            if resp.status_code in (200, 201):
                                await db.synced_events.insert_one({
                                    "user_id": user_id, "service": service,
                                    "session_id": session_id,
                                    "external_id": resp.json().get("id"),
                                    "synced_at": datetime.now(timezone.utc).isoformat()
                                })

                    elif service == "slack":
                        cat_map = {"learning": "\ud83d\udcda Apprentissage", "productivity": "\ud83c\udfaf Productivit\u00e9", "well_being": "\ud83d\udc9a Bien-\u00eatre"}
                        message = f"\u2705 *{title}* compl\u00e9t\u00e9e \u2014 {duration} min ({cat_map.get(category, category)})"
                        if access_token.startswith("https://hooks.slack.com/"):
                            await http_client.post(access_token, json={"text": message})
                        else:
                            await http_client.post(
                                "https://slack.com/api/chat.postMessage",
                                json={"channel": "me", "text": message, "mrkdwn": True},
                                headers={"Authorization": f"Bearer {access_token}"}
                            )

                except Exception as e:
                    logger.warning(f"Auto-sync to {service} failed for session {session_id}: {e}")

    except Exception as e:
        logger.warning(f"Auto-sync failed for user {user_id}: {e}")


@router.post("/sessions/complete")
async def complete_session(
    completion: SessionComplete,
    user: dict = Depends(get_current_user)
):
    """Complete a micro-action session and update stats"""
    # Lazy import to avoid circular dependency
    from routes.badges import check_and_award_badges

    session = await db.user_sessions_history.find_one(
        {"session_id": completion.session_id, "user_id": user["user_id"]},
        {"_id": 0}
    )

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Update session
    await db.user_sessions_history.update_one(
        {"session_id": completion.session_id},
        {"$set": {
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "actual_duration": completion.actual_duration,
            "completed": completion.completed,
            "notes": completion.notes
        }}
    )

    event_type = "action_completed" if completion.completed else "action_abandoned"
    await track_event(db, user["user_id"], event_type, {
        "session_id": completion.session_id,
        "category": session.get("category"),
        "action_title": session.get("action_title"),
        "actual_duration": completion.actual_duration,
    })

    # Feedback loop: completion or abandonment signal
    action_id = session.get("action_id")
    if action_id:
        signal = "completion" if completion.completed else "abandonment"
        await record_signal(db, user["user_id"], action_id, signal)

    if completion.completed:
        # Update user stats
        user_doc = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0})

        # Calculate streak
        today = datetime.now(timezone.utc).date()
        last_session = user_doc.get("last_session_date")

        new_streak = user_doc.get("streak_days", 0)
        streak_shield_used = False
        if last_session:
            if isinstance(last_session, str):
                last_date = datetime.fromisoformat(last_session).date()
            else:
                last_date = last_session.date() if hasattr(last_session, 'date') else last_session

            if last_date == today - timedelta(days=1):
                new_streak += 1
            elif last_date != today:
                # Streak would break — check for Premium Streak Shield
                gap_days = (today - last_date).days
                if (user_doc.get("subscription_tier") == "premium"
                    and gap_days <= 2):
                    # Check if shield is available (once per 7 days)
                    shield_used_at = user_doc.get("streak_shield_used_at")
                    shield_available = True
                    if shield_used_at:
                        if isinstance(shield_used_at, str):
                            shield_date = datetime.fromisoformat(shield_used_at).date()
                        else:
                            shield_date = shield_used_at.date() if hasattr(shield_used_at, 'date') else shield_used_at
                        shield_available = (today - shield_date).days >= 7

                    if shield_available:
                        # Shield activated — preserve streak
                        new_streak += 1
                        streak_shield_used = True
                        await db.users.update_one(
                            {"user_id": user["user_id"]},
                            {"$set": {"streak_shield_used_at": today.isoformat()},
                             "$inc": {"streak_shield_count": 1}}
                        )
                        logger.info(f"Streak shield activated for user {user['user_id']}")
                    else:
                        new_streak = 1
                else:
                    new_streak = 1
        else:
            new_streak = 1

        await db.users.update_one(
            {"user_id": user["user_id"]},
            {
                "$inc": {"total_time_invested": completion.actual_duration},
                "$set": {
                    "streak_days": new_streak,
                    "last_session_date": today.isoformat()
                }
            }
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
                "message": f"F\u00e9licitations ! Vous avez obtenu le badge {badge['name']}",
                "icon": badge["icon"],
                "read": False,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.notifications.insert_one(notification)
            await send_push_to_user(user["user_id"], notification["title"], notification["message"], url="/notifications", tag="badge")

        # Invalidate cached features (session data changed)
        from services.cache import cache_delete
        await cache_delete(f"user_features:{user['user_id']}")

        # Auto-export to connected integrations (non-blocking)
        session_data = {
            "session_id": completion.session_id,
            "action_title": session.get("action_title"),
            "actual_duration": completion.actual_duration,
            "category": session.get("category"),
            "completed_at": datetime.now(timezone.utc).isoformat()
        }
        await _auto_sync_session(user["user_id"], session_data)

        # Emit activity feed items (non-blocking — never break session flow)
        try:
            from services.activity_service import emit_session_activity, emit_badge_activity, emit_streak_activity
            await emit_session_activity(user["user_id"], {
                "action_title": session.get("action_title"),
                "category": session.get("category"),
                "actual_duration": completion.actual_duration,
            })
            for badge in new_badges:
                await emit_badge_activity(user["user_id"], badge)
            await emit_streak_activity(user["user_id"], new_streak)
        except Exception:
            pass  # Feed emission must never block session completion

        return {
            "message": "Session completed!",
            "time_added": completion.actual_duration,
            "new_streak": new_streak,
            "total_time": user_doc.get("total_time_invested", 0) + completion.actual_duration,
            "new_badges": new_badges
        }

    return {"message": "Session recorded"}

@router.get("/stats")
async def get_user_stats(user: dict = Depends(get_current_user)):
    """Get user progress statistics"""
    # Get sessions by category
    pipeline = [
        {"$match": {"user_id": user["user_id"], "completed": True}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}, "total_time": {"$sum": "$actual_duration"}}}
    ]
    category_stats = await db.user_sessions_history.aggregate(pipeline).to_list(10)

    sessions_by_category = {}
    time_by_category = {}
    for stat in category_stats:
        sessions_by_category[stat["_id"]] = stat["count"]
        time_by_category[stat["_id"]] = stat["total_time"]

    # Get recent sessions
    recent = await db.user_sessions_history.find(
        {"user_id": user["user_id"], "completed": True},
        {"_id": 0}
    ).sort("completed_at", -1).limit(10).to_list(10)

    # Get total sessions count
    total_sessions = await db.user_sessions_history.count_documents(
        {"user_id": user["user_id"], "completed": True}
    )

    return {
        "total_time_invested": user.get("total_time_invested", 0),
        "total_sessions": total_sessions,
        "streak_days": user.get("streak_days", 0),
        "sessions_by_category": sessions_by_category,
        "time_by_category": time_by_category,
        "recent_sessions": recent
    }

# ============== RECAP INTELLIGENT (D.1) ==============

@router.get("/recap")
@limiter.limit("20/minute")
async def get_user_recap(request: Request, user: dict = Depends(get_current_user)):
    """Generate daily + weekly recap from sessions, objectives, and routines."""
    now = datetime.now(timezone.utc)
    today = now.date()
    today_iso = today.isoformat()
    week_start = (today - timedelta(days=today.weekday())).isoformat()
    user_id = user["user_id"]

    # -- Today's sessions
    today_sessions = await db.user_sessions_history.find(
        {"user_id": user_id, "completed": True, "completed_at": {"$gte": today_iso}},
        {"_id": 0, "actual_duration": 1, "action_title": 1, "category": 1, "completed_at": 1}
    ).to_list(50)

    today_minutes = sum(s.get("actual_duration", 0) for s in today_sessions)
    today_count = len(today_sessions)
    today_categories = list(set(s.get("category", "") for s in today_sessions if s.get("category")))

    # -- This week's sessions
    week_sessions = await db.user_sessions_history.find(
        {"user_id": user_id, "completed": True, "completed_at": {"$gte": week_start}},
        {"_id": 0, "actual_duration": 1, "category": 1, "completed_at": 1}
    ).to_list(200)

    week_minutes = sum(s.get("actual_duration", 0) for s in week_sessions)
    week_count = len(week_sessions)

    # Week sessions by day (for mini bar chart)
    week_by_day = {}
    for s in week_sessions:
        day = s.get("completed_at", "")[:10]
        if day:
            week_by_day[day] = week_by_day.get(day, 0) + s.get("actual_duration", 0)

    # -- Objectives progress this week
    objectives = await db.objectives.find(
        {"user_id": user_id, "status": "active", "deleted": {"$ne": True}},
        {"_id": 0, "objective_id": 1, "title": 1, "current_day": 1, "streak_days": 1,
         "total_sessions": 1, "total_minutes": 1, "curriculum": 1}
    ).to_list(20)

    obj_summaries = []
    for obj in objectives:
        curriculum = obj.get("curriculum", [])
        completed_this_week = sum(
            1 for s in curriculum
            if s.get("completed") and s.get("completed_at", "") >= week_start
        )
        total_completed = sum(1 for s in curriculum if s.get("completed"))
        total_steps = len(curriculum)
        percent = round((total_completed / max(total_steps, 1)) * 100)

        obj_summaries.append({
            "objective_id": obj["objective_id"],
            "title": obj["title"],
            "streak_days": obj.get("streak_days", 0),
            "sessions_this_week": completed_this_week,
            "progress_percent": percent,
            "total_completed": total_completed,
            "total_steps": total_steps,
        })

    # -- Routines today
    routines = await db.routines.find(
        {"user_id": user_id, "is_active": True, "deleted": {"$ne": True}},
        {"_id": 0, "name": 1, "last_completed_at": 1, "times_completed": 1}
    ).to_list(20)

    routines_done_today = sum(1 for r in routines if (r.get("last_completed_at") or "").startswith(today_iso))
    routines_total = len(routines)

    # -- Highlights
    highlights = []
    streak = user.get("streak_days", 0)
    if streak >= 7:
        highlights.append({"type": "streak", "text": f"Streak de {streak} jours ! Continue comme \u00e7a."})
    if today_count >= 3:
        highlights.append({"type": "productive", "text": f"{today_count} sessions aujourd'hui, journ\u00e9e productive !"})
    if week_minutes >= 60:
        highlights.append({"type": "milestone", "text": f"Plus d'une heure investie cette semaine ({week_minutes} min)."})

    best_obj = max(obj_summaries, key=lambda o: o["sessions_this_week"], default=None)
    if best_obj and best_obj["sessions_this_week"] > 0:
        highlights.append({
            "type": "focus",
            "text": f"Focus de la semaine : \u00ab {best_obj['title'][:30]} \u00bb ({best_obj['sessions_this_week']} sessions)."
        })

    return {
        "today": {
            "sessions": today_count,
            "minutes": today_minutes,
            "categories": today_categories,
            "routines_done": routines_done_today,
            "routines_total": routines_total,
        },
        "week": {
            "sessions": week_count,
            "minutes": week_minutes,
            "by_day": week_by_day,
        },
        "streak": streak,
        "objectives": obj_summaries,
        "highlights": highlights,
    }
