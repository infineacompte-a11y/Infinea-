"""
Background notification scheduler for InFinea.
Periodically generates proactive notifications for active users:
- Streak at risk alerts (afternoon, max 1/day)
- Routine reminders (max 1/day)
- Idle objective nudges (max 1/3 days)

Same asyncio pattern as action_generator and feature_calculator.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone, timedelta

logger = logging.getLogger("notification_scheduler")


async def _notif_exists_today(db, user_id: str, notif_type: str) -> bool:
    """Check if a notification of this type was already created today for this user."""
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    return bool(await db.notifications.find_one({
        "user_id": user_id,
        "type": notif_type,
        "created_at": {"$gte": today_start.isoformat()}
    }))


async def _notif_exists_recent(db, user_id: str, notif_type: str, days: int) -> bool:
    """Check if a notification of this type was created in the last N days."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    return bool(await db.notifications.find_one({
        "user_id": user_id,
        "type": notif_type,
        "created_at": {"$gte": cutoff}
    }))


async def _create_notification(db, user_id: str, notif_type: str, title: str, message: str, icon: str = "bell"):
    """Insert a notification into the DB and send a Web Push if subscribed."""
    doc = {
        "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
        "user_id": user_id,
        "type": notif_type,
        "title": title,
        "message": message,
        "icon": icon,
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.notifications.insert_one(doc)
    # Send Web Push (imported here to avoid circular imports)
    try:
        from server import send_push_to_user
        await send_push_to_user(user_id, title, message, url="/notifications", tag=notif_type)
    except Exception as e:
        logger.debug(f"Push send skipped for {user_id}: {e}")
    return doc


async def generate_proactive_notifications(db):
    """
    Scan active users and generate stored notifications where appropriate.
    Called every 2 hours by the background loop.
    """
    now = datetime.now(timezone.utc)
    current_hour = now.hour
    today_str = now.date().isoformat()

    # Only process users active in the last 30 days
    cutoff_30d = (now - timedelta(days=30)).isoformat()
    active_users = await db.users.find(
        {"last_session_date": {"$gte": cutoff_30d[:10]}},
        {"_id": 0, "user_id": 1, "streak_days": 1, "last_session_date": 1}
    ).to_list(500)

    stats = {"streak_alerts": 0, "routine_reminders": 0, "objective_nudges": 0}

    for user in active_users:
        user_id = user["user_id"]
        streak = user.get("streak_days", 0)
        last_session = user.get("last_session_date", "")

        try:
            # ── 1. Streak at risk (after 14:00 UTC, max 1/day) ──
            if streak > 0 and current_hour >= 14 and last_session != today_str:
                if not await _notif_exists_today(db, user_id, "streak_alert"):
                    await _create_notification(
                        db, user_id, "streak_alert",
                        title=f"🔥 Streak de {streak} jours en danger !",
                        message="Vous n'avez pas encore fait de session aujourd'hui. Une micro-action de 5 min suffit pour maintenir votre série.",
                        icon="flame"
                    )
                    stats["streak_alerts"] += 1

            # ── 2. Routine reminder (after 10:00 UTC, max 1/day) ──
            if current_hour >= 10:
                routines = await db.routines.find(
                    {"user_id": user_id, "is_active": True},
                    {"_id": 0, "routine_id": 1, "name": 1}
                ).to_list(10)

                if routines and not await _notif_exists_today(db, user_id, "routine_reminder"):
                    # Check if any routine was executed today
                    today_log = await db.routine_logs.find_one({
                        "user_id": user_id,
                        "completed_at": {"$gte": today_str}
                    })
                    if not today_log:
                        names = ", ".join(r["name"] for r in routines[:3])
                        await _create_notification(
                            db, user_id, "routine_reminder",
                            title="⏰ Vos habitudes vous attendent",
                            message=f"N'oubliez pas : {names}",
                            icon="calendar-clock"
                        )
                        stats["routine_reminders"] += 1

            # ── 3. Idle objective nudge (max 1/3 days) ──
            active_objectives = await db.objectives.find(
                {"user_id": user_id, "status": "active"},
                {"_id": 0, "objective_id": 1, "title": 1}
            ).to_list(5)

            for obj in active_objectives:
                cutoff_3d = (now - timedelta(days=3)).isoformat()
                recent_session = await db.user_sessions_history.find_one({
                    "user_id": user_id,
                    "objective_id": obj["objective_id"],
                    "completed": True,
                    "completed_at": {"$gte": cutoff_3d}
                })
                if not recent_session:
                    if not await _notif_exists_recent(db, user_id, "objective_nudge", days=3):
                        await _create_notification(
                            db, user_id, "objective_nudge",
                            title=f"🎯 Reprenez « {obj['title'][:40]} »",
                            message="Cela fait quelques jours — même 5 minutes comptent pour avancer.",
                            icon="target"
                        )
                        stats["objective_nudges"] += 1
                        break  # Max 1 objective nudge per cycle per user

        except Exception as e:
            logger.warning(f"Notification generation failed for user {user_id}: {e}")
            continue

    total = sum(stats.values())
    if total > 0:
        logger.info(f"Proactive notifications generated: {stats}")
    else:
        logger.debug("No proactive notifications needed this cycle")


async def notification_scheduler_loop(db):
    """Background loop that generates proactive notifications periodically."""
    # Wait 90 seconds after startup before first run
    await asyncio.sleep(90)

    while True:
        try:
            await generate_proactive_notifications(db)
        except Exception as e:
            logger.error(f"Notification scheduler loop error: {e}")

        # Run every 2 hours
        await asyncio.sleep(2 * 3600)
