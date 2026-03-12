"""
Background notification scheduler for InFinea.
Periodically generates proactive notifications for active users:
- Streak at risk alerts (afternoon, max 1/day)
- Routine reminders (max 1/day)
- Idle objective nudges (max 1/3 days)
- F.3 Micro-instant contextual push notifications (intelligent throttling)

Same asyncio pattern as action_generator and feature_calculator.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger("notification_scheduler")

# ── F.3 Contextual Push Constants ──
MAX_INSTANT_PUSHES_PER_DAY = 3
MIN_PUSH_INTERVAL_MINUTES = 120   # 2 hours minimum between pushes
MIN_PUSH_CONFIDENCE = 0.50        # Only push high-confidence instants
QUIET_HOURS_START = 22            # No push after 22:00
QUIET_HOURS_END = 7               # No push before 07:00
PUSH_ADVANCE_MINUTES = 10         # Push N minutes before the window starts


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
        from helpers import send_push_to_user
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

            # ── 4. Spaced repetition review reminder (max 1/day) ──
            if not await _notif_exists_today(db, user_id, "sr_review_due"):
                try:
                    from services.spaced_repetition import get_review_queue
                    for obj in active_objectives:
                        due = await get_review_queue(db, user_id, obj["objective_id"])
                        if due:
                            skill_name = due[0]["skill"]
                            count = len(due)
                            msg = f"« {skill_name} » a besoin d'être révisé" + (f" (+{count - 1} autres)" if count > 1 else "")
                            await _create_notification(
                                db, user_id, "sr_review_due",
                                title="🧠 Révision recommandée",
                                message=msg,
                                icon="brain"
                            )
                            stats["sr_reviews"] = stats.get("sr_reviews", 0) + 1
                            break  # Max 1 SR notification per user per cycle
                except Exception as e:
                    logger.debug(f"SR review check skipped for {user_id}: {e}")

        except Exception as e:
            logger.warning(f"Notification generation failed for user {user_id}: {e}")
            continue

    total = sum(stats.values())
    if total > 0:
        logger.info(f"Proactive notifications generated: {stats}")
    else:
        logger.debug("No proactive notifications needed this cycle")


# ═══════════════════════════════════════════════════════════════════
# F.3 — Micro-Instant Contextual Push Notifications
# ═══════════════════════════════════════════════════════════════════


async def _count_instant_pushes_today(db, user_id: str) -> int:
    """Count micro-instant push notifications sent today."""
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    return await db.notifications.count_documents({
        "user_id": user_id,
        "type": "micro_instant_push",
        "created_at": {"$gte": today_start.isoformat()}
    })


async def _last_instant_push_time(db, user_id: str) -> Optional[str]:
    """Get the timestamp of the last micro-instant push for this user."""
    doc = await db.notifications.find_one(
        {"user_id": user_id, "type": "micro_instant_push"},
        {"_id": 0, "created_at": 1},
        sort=[("created_at", -1)]
    )
    return doc["created_at"] if doc else None


def _is_quiet_hours(user_tz_offset_hours: Optional[float] = None) -> bool:
    """Check if current time is within quiet hours (22:00 - 07:00 user local time)."""
    now_utc = datetime.now(timezone.utc)
    if user_tz_offset_hours is not None:
        local_hour = (now_utc + timedelta(hours=user_tz_offset_hours)).hour
    else:
        local_hour = now_utc.hour  # fallback to UTC
    return local_hour >= QUIET_HOURS_START or local_hour < QUIET_HOURS_END


async def generate_contextual_instant_notifications(db):
    """
    F.3 — Scan active users, predict micro-instants, and send contextual push
    notifications with intelligent throttling.

    Throttling rules:
    - Max MAX_INSTANT_PUSHES_PER_DAY per user per day
    - Minimum MIN_PUSH_INTERVAL_MINUTES between two pushes for same user
    - Only push instants with confidence >= MIN_PUSH_CONFIDENCE
    - Respect user notification preferences
    - Never push during quiet hours (22:00 - 07:00 user local time)
    - Never re-push the same instant
    """
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()

    # Only process users active in the last 30 days
    cutoff_30d = (now - timedelta(days=30)).isoformat()
    active_users = await db.users.find(
        {"last_session_date": {"$gte": cutoff_30d[:10]}},
        {"_id": 0, "user_id": 1, "timezone_offset": 1, "subscription": 1}
    ).to_list(500)

    stats = {"evaluated": 0, "pushed": 0, "throttled": 0, "quiet_hours": 0}

    for user in active_users:
        user_id = user["user_id"]
        tz_offset = user.get("timezone_offset")  # hours offset from UTC, e.g. 1 for CET
        stats["evaluated"] += 1

        try:
            # ── Check quiet hours ──
            if _is_quiet_hours(tz_offset):
                stats["quiet_hours"] += 1
                continue

            # ── Check user notification preferences ──
            prefs = await db.notification_preferences.find_one(
                {"user_id": user_id}, {"_id": 0}
            )
            if prefs and not prefs.get("micro_instant_push_enabled", True):
                continue

            # ── Check daily push count ──
            pushes_today = await _count_instant_pushes_today(db, user_id)
            if pushes_today >= MAX_INSTANT_PUSHES_PER_DAY:
                stats["throttled"] += 1
                continue

            # ── Check minimum interval ──
            last_push_ts = await _last_instant_push_time(db, user_id)
            if last_push_ts:
                last_push_dt = datetime.fromisoformat(last_push_ts)
                if last_push_dt.tzinfo is None:
                    last_push_dt = last_push_dt.replace(tzinfo=timezone.utc)
                minutes_since = (now - last_push_dt).total_seconds() / 60
                if minutes_since < MIN_PUSH_INTERVAL_MINUTES:
                    stats["throttled"] += 1
                    continue

            # ── Predict micro-instants ──
            from services.micro_instant_engine import predict_micro_instants
            instants = await predict_micro_instants(
                db, user_id,
                user_subscription=user.get("subscription", "free")
            )

            if not instants:
                continue

            # ── Filter: confidence threshold + upcoming windows only ──
            qualifying = []
            for instant in instants:
                if instant.get("confidence_score", 0) < MIN_PUSH_CONFIDENCE:
                    continue

                # Only push for windows starting within the next push-advance window + 1 hour
                window_start = instant.get("window_start", "")
                if window_start:
                    try:
                        ws_dt = datetime.fromisoformat(window_start)
                        if ws_dt.tzinfo is None:
                            ws_dt = ws_dt.replace(tzinfo=timezone.utc)
                        minutes_until = (ws_dt - now).total_seconds() / 60
                        # Push if window starts within -5 to +70 minutes
                        # (slightly before start to PUSH_ADVANCE_MINUTES + 1 hour ahead)
                        if minutes_until < -5 or minutes_until > (PUSH_ADVANCE_MINUTES + 60):
                            continue
                    except (ValueError, TypeError):
                        continue

                # Check if this instant was already pushed
                already_pushed = await db.notifications.find_one({
                    "user_id": user_id,
                    "type": "micro_instant_push",
                    "metadata.instant_id": instant["instant_id"]
                })
                if already_pushed:
                    continue

                qualifying.append(instant)

            if not qualifying:
                continue

            # ── Pick the best qualifying instant (highest confidence) ──
            best = max(qualifying, key=lambda i: i.get("confidence_score", 0))

            # ── Compose message via contextual message composer ──
            from services.contextual_messages import compose_instant_message
            payload = compose_instant_message(best)

            # ── Create notification + push ──
            doc = await _create_notification(
                db, user_id, "micro_instant_push",
                title=payload["title"], message=payload["body"], icon=payload["icon"]
            )
            # Store instant metadata + push payload for deduplication and analytics
            await db.notifications.update_one(
                {"notification_id": doc["notification_id"]},
                {"$set": {
                    "metadata": {
                        "instant_id": best["instant_id"],
                        "confidence_score": best["confidence_score"],
                        "source": best.get("source"),
                        "window_start": best.get("window_start"),
                        "window_end": best.get("window_end"),
                        "duration_minutes": best.get("duration_minutes"),
                    },
                    "data": {
                        "url": payload.get("url", "/micro-instants"),
                        "actions": payload.get("actions", []),
                    }
                }}
            )

            # Track the event
            try:
                from services.event_tracker import track_event
                await track_event(db, user_id, "micro_instant_push_sent", {
                    "instant_id": best["instant_id"],
                    "confidence": best["confidence_score"],
                    "source": best.get("source"),
                })
            except Exception:
                pass

            stats["pushed"] += 1
            logger.debug(
                f"Micro-instant push sent to {user_id}: "
                f"instant={best['instant_id']} conf={best['confidence_score']:.2f}"
            )

        except Exception as e:
            logger.warning(f"Contextual instant notification failed for {user_id}: {e}")
            continue

    if stats["pushed"] > 0 or stats["throttled"] > 0:
        logger.info(f"F.3 contextual instant pushes: {stats}")
    else:
        logger.debug(f"F.3 contextual instant pushes: no pushes this cycle ({stats})")


async def notification_scheduler_loop(db):
    """Background loop that generates proactive + contextual notifications periodically."""
    # Wait 90 seconds after startup before first run
    await asyncio.sleep(90)

    while True:
        try:
            await generate_proactive_notifications(db)
        except Exception as e:
            logger.error(f"Notification scheduler loop error: {e}")

        try:
            await generate_contextual_instant_notifications(db)
        except Exception as e:
            logger.error(f"Contextual instant notification loop error: {e}")

        # Run every 1 hour (micro-instants need more responsive timing)
        await asyncio.sleep(3600)
