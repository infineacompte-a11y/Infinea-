"""InFinea — Notifications routes. CRUD, push subscriptions, smart notifications."""

from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, HTTPException, Request, Depends

from database import db
from auth import get_current_user
from config import VAPID_PUBLIC_KEY, logger, limiter
from models import NotificationPreferences

router = APIRouter()


# ============== NOTIFICATIONS ==============

@router.get("/notifications/preferences")
async def get_notification_preferences(user: dict = Depends(get_current_user)):
    """Get user's notification preferences"""
    prefs = await db.notification_preferences.find_one(
        {"user_id": user["user_id"]},
        {"_id": 0}
    )

    if not prefs:
        # Return defaults (must match NotificationPreferences model)
        return {
            "user_id": user["user_id"],
            "daily_reminder": True,
            "reminder_time": "09:00",
            "streak_alerts": True,
            "achievement_alerts": True,
            "weekly_summary": True,
            "email_notifications": True,
            "email_social": True,
            "email_achievements": True,
            "email_streak": True,
            "email_weekly_summary": True,
        }

    return prefs

@router.put("/notifications/preferences")
async def update_notification_preferences(
    prefs: NotificationPreferences,
    user: dict = Depends(get_current_user)
):
    """Update user's notification preferences"""
    prefs_doc = {
        "user_id": user["user_id"],
        **prefs.model_dump(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

    await db.notification_preferences.update_one(
        {"user_id": user["user_id"]},
        {"$set": prefs_doc},
        upsert=True
    )

    return prefs_doc

@router.get("/notifications/vapid-public-key")
async def get_vapid_public_key():
    """Return VAPID public key so the frontend can subscribe to Web Push."""
    if not VAPID_PUBLIC_KEY:
        raise HTTPException(status_code=503, detail="Web Push not configured")
    return {"public_key": VAPID_PUBLIC_KEY}

@router.post("/notifications/subscribe")
async def subscribe_push_notifications(
    request: Request,
    user: dict = Depends(get_current_user)
):
    """Subscribe to push notifications (store push subscription)"""
    body = await request.json()
    subscription = body.get("subscription")

    if not subscription:
        raise HTTPException(status_code=400, detail="Subscription data required")

    await db.push_subscriptions.update_one(
        {"user_id": user["user_id"]},
        {"$set": {
            "user_id": user["user_id"],
            "subscription": subscription,
            "created_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )

    return {"message": "Subscribed to push notifications"}

@router.get("/notifications/unread-count")
async def get_unread_notification_count(
    user: dict = Depends(get_current_user),
):
    """Lightweight endpoint for sidebar badge — returns unread count only."""
    count = await db.notifications.count_documents(
        {"user_id": user["user_id"], "read": {"$ne": True}}
    )
    return {"unread_count": count}

@router.get("/notifications")
async def get_user_notifications(
    user: dict = Depends(get_current_user),
    limit: int = 20
):
    """Get user's notifications"""
    notifications = await db.notifications.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)

    return notifications

@router.post("/notifications/mark-read")
async def mark_notifications_read(
    request: Request,
    user: dict = Depends(get_current_user)
):
    """Mark notifications as read"""
    body = await request.json()
    notification_ids = body.get("notification_ids", [])

    if notification_ids:
        await db.notifications.update_many(
            {"user_id": user["user_id"], "notification_id": {"$in": notification_ids}},
            {"$set": {"read": True}}
        )
    else:
        # Mark all as read
        await db.notifications.update_many(
            {"user_id": user["user_id"]},
            {"$set": {"read": True}}
        )

    return {"message": "Notifications marked as read"}

# ============== SMART NOTIFICATIONS (Proactive Coach) ==============

@router.get("/notifications/smart")
@limiter.limit("10/minute")
async def get_smart_notifications(request: Request, user: dict = Depends(get_current_user)):
    """Generate proactive smart notifications based on user behavior patterns."""
    now = datetime.now(timezone.utc)
    today = now.date()
    today_iso = today.isoformat()
    user_id = user["user_id"]
    smart_notifs = []

    # ── 1. Streak en danger ─────────────────────
    streak = user.get("streak_days", 0)
    last_session_raw = user.get("last_session_date")
    if streak > 0 and last_session_raw:
        if isinstance(last_session_raw, str):
            last_date = datetime.fromisoformat(last_session_raw).date()
        else:
            last_date = last_session_raw.date() if hasattr(last_session_raw, "date") else last_session_raw
        days_since = (today - last_date).days
        if days_since >= 1:
            smart_notifs.append({
                "id": "streak_danger",
                "type": "streak_alert",
                "priority": 1,
                "title": f"Ton streak de {streak} jours est en danger !",
                "message": f"Tu n'as pas pratiqué depuis {days_since} jour{'s' if days_since > 1 else ''}. Un petit 5 min suffit pour garder ta série.",
                "icon": "flame",
                "action_label": "Faire une micro-action",
                "action_url": "/dashboard",
            })

    # ── 2. Objectifs : next step + négligés + progression ───
    objectives = await db.objectives.find(
        {"user_id": user_id, "status": "active", "deleted": {"$ne": True}},
        {"_id": 0, "objective_id": 1, "title": 1, "last_session_at": 1, "streak_days": 1,
         "current_day": 1, "target_duration_days": 1, "daily_minutes": 1,
         "curriculum": 1, "total_sessions": 1}
    ).to_list(20)

    for obj in objectives:
        curriculum = obj.get("curriculum") or []
        completed_steps = [s for s in curriculum if s.get("completed")]
        next_step = next((s for s in curriculum if not s.get("completed")), None)
        total_steps = len(curriculum)
        pct = round((len(completed_steps) / total_steps) * 100) if total_steps > 0 else 0

        # 2a. Prochaine session d'objectif (priorité haute)
        if next_step:
            last_obj_session = obj.get("last_session_at")
            already_today = False
            if last_obj_session:
                ls = last_obj_session if isinstance(last_obj_session, str) else last_obj_session.isoformat()
                already_today = ls.startswith(today_iso)
            if not already_today:
                step_title = next_step.get("title", "Prochaine étape")
                smart_notifs.append({
                    "id": f"obj_next_{obj['objective_id']}",
                    "type": "objective_nudge",
                    "priority": 1,
                    "title": f"Jour {obj.get('current_day', 0) + 1} — {obj['title'][:30]}",
                    "message": f"{step_title} · {obj.get('daily_minutes', 5)} min",
                    "icon": "target",
                    "action_label": "Lancer la session",
                    "action_url": f"/objectives/{obj['objective_id']}",
                })

        # 2b. Objectifs négligés (3+ jours)
        last_obj_session = obj.get("last_session_at")
        if last_obj_session:
            if isinstance(last_obj_session, str):
                last_obj_date = datetime.fromisoformat(last_obj_session).date()
            else:
                last_obj_date = last_obj_session.date() if hasattr(last_obj_session, "date") else today
            days_idle = (today - last_obj_date).days
            if days_idle >= 3:
                smart_notifs.append({
                    "id": f"obj_idle_{obj['objective_id']}",
                    "type": "objective_nudge",
                    "priority": 2,
                    "title": f"Tu n'as pas avancé sur « {obj['title'][:40]} »",
                    "message": f"{days_idle} jours sans session. Reprends avec une micro-session de 5 min !",
                    "icon": "target",
                    "action_label": "Reprendre",
                    "action_url": f"/objectives/{obj['objective_id']}",
                })

        # 2c. Milestones de progression (25%, 50%, 75%)
        if pct in (25, 50, 75):
            smart_notifs.append({
                "id": f"obj_pct_{obj['objective_id']}_{pct}",
                "type": "milestone",
                "priority": 3,
                "title": f"{pct}% de « {obj['title'][:30]} » complété !",
                "message": f"{len(completed_steps)}/{total_steps} sessions terminées. Continue, tu avances bien !",
                "icon": "trophy",
                "action_label": "Voir mon parcours",
                "action_url": f"/objectives/{obj['objective_id']}",
            })

    # ── 3. Routines non faites aujourd'hui ──────
    routines = await db.routines.find(
        {"user_id": user_id, "is_active": True, "deleted": {"$ne": True}},
        {"_id": 0, "routine_id": 1, "name": 1, "time_of_day": 1, "total_minutes": 1, "last_completed_at": 1}
    ).to_list(20)

    hour = now.hour
    current_tod = "morning" if hour < 12 else ("afternoon" if hour < 18 else "evening")
    tod_order = {"morning": 0, "afternoon": 1, "evening": 2, "anytime": 3}

    routines_done_today = 0
    routines_total_active = len(routines)

    for routine in routines:
        last_done = routine.get("last_completed_at", "")
        if last_done and last_done.startswith(today_iso):
            routines_done_today += 1
            continue  # Already done today

        rtod = routine.get("time_of_day", "anytime")
        # Only nudge for current or past time slots (don't nag about evening routine at 8am)
        if rtod != "anytime" and tod_order.get(rtod, 3) > tod_order.get(current_tod, 3):
            continue

        # Enriched: include items count + first item name
        items = routine.get("items") or []
        first_item = items[0]["title"] if items else ""
        detail = f"{len(items)} actions · {routine.get('total_minutes', 0)} min"
        if first_item:
            detail += f" — commence par : {first_item[:35]}"

        smart_notifs.append({
            "id": f"routine_pending_{routine['routine_id']}",
            "type": "routine_reminder",
            "priority": 3 if rtod == current_tod else 4,
            "title": f"Routine « {routine['name'][:40]} » pas encore faite",
            "message": detail,
            "icon": "calendar-clock",
            "action_label": "Lancer",
            "action_url": "/routines",
        })

    # ── 3b. Journée parfaite (toutes routines faites) ──
    if routines_total_active > 0 and routines_done_today >= routines_total_active:
        smart_notifs.append({
            "id": "perfect_day",
            "type": "milestone",
            "priority": 5,
            "title": "Journée parfaite !",
            "message": f"Toutes tes {routines_total_active} habitudes sont complétées. Bravo !",
            "icon": "trophy",
            "action_label": "Voir ma journée",
            "action_url": "/my-day",
        })

    # ── 4. Milestone atteint (celebrate) ────────
    for obj in objectives:
        curr_day = obj.get("current_day", 0)
        if curr_day in (7, 14, 30, 60, 90):
            smart_notifs.append({
                "id": f"milestone_{obj['objective_id']}_{curr_day}",
                "type": "milestone",
                "priority": 2,
                "title": f"Jour {curr_day} sur « {obj['title'][:30]} » !",
                "message": f"Bravo pour ta régularité ! Continue comme ça.",
                "icon": "trophy",
                "action_label": "Voir mon parcours",
                "action_url": f"/objectives/{obj['objective_id']}",
            })

    # ── 5. Conseil énergie (time-based) ─────────
    if hour >= 6 and hour < 10 and not smart_notifs:
        smart_notifs.append({
            "id": "energy_morning",
            "type": "coach_tip",
            "priority": 5,
            "title": "Le matin, ton énergie est à son max",
            "message": "C'est le meilleur moment pour les tâches qui demandent de la concentration.",
            "icon": "zap",
            "action_label": "Ma Journée",
            "action_url": "/my-day",
        })
    elif hour >= 13 and hour < 15 and not smart_notifs:
        smart_notifs.append({
            "id": "energy_afternoon",
            "type": "coach_tip",
            "priority": 5,
            "title": "Début d'après-midi : idéal pour des tâches légères",
            "message": "Profite de ce créneau pour une micro-action créative ou de bien-être.",
            "icon": "zap",
            "action_label": "Ma Journée",
            "action_url": "/my-day",
        })

    # ── 6. Résumé hebdo (affiché 1x par semaine, le lundi ou si pas vu depuis 7j) ──
    if today.weekday() == 0:  # Lundi
        week_ago = (now - timedelta(days=7)).isoformat()
        week_sessions = await db.sessions.count_documents(
            {"user_id": user_id, "completed": True, "completed_at": {"$gte": week_ago}}
        )
        if week_sessions > 0:
            # Aggregate total minutes from last week
            pipeline = [
                {"$match": {"user_id": user_id, "completed": True, "completed_at": {"$gte": week_ago}}},
                {"$group": {"_id": None, "total_min": {"$sum": "$actual_duration"}}},
            ]
            agg = await db.sessions.aggregate(pipeline).to_list(1)
            total_min = agg[0]["total_min"] if agg else 0
            smart_notifs.append({
                "id": f"weekly_recap_{today_iso}",
                "type": "coach_tip",
                "priority": 4,
                "title": f"Ta semaine : {week_sessions} sessions, {total_min} min",
                "message": "Beau travail ! Chaque minute investie compte pour ta progression.",
                "icon": "award",
                "action_label": "Voir ma progression",
                "action_url": "/progress",
            })

    # Sort by priority (lower = more important)
    smart_notifs.sort(key=lambda n: n.get("priority", 99))

    return {"notifications": smart_notifs[:8], "count": len(smart_notifs)}
