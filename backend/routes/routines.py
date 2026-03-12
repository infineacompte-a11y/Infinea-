"""InFinea — Routines routes. CRUD, completion, iCal export."""

import uuid
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, HTTPException, Request, Response, Depends

from database import db
from auth import get_current_user
from models import RoutineCreate, RoutineUpdate
from config import limiter

router = APIRouter()


# ============== ROUTINES ==============

@router.post("/routines")
@limiter.limit("10/minute")
async def create_routine(request: Request, routine: RoutineCreate, user: dict = Depends(get_current_user)):
    """Create a new routine (ordered sequence of micro-actions / objective steps)."""
    # Free: max 3 routines, Premium: 20
    count = await db.routines.count_documents({"user_id": user["user_id"], "deleted": {"$ne": True}})
    max_routines = 3 if user.get("subscription_tier") != "premium" else 20
    if count >= max_routines:
        raise HTTPException(status_code=400, detail=f"Limite atteinte ({max_routines} routines).")

    now = datetime.now(timezone.utc).isoformat()
    routine_id = f"rtn_{uuid.uuid4().hex[:12]}"

    # Validate and normalize items
    validated_items = []
    for i, item in enumerate(routine.items or []):
        validated_items.append({
            "type": item.get("type", "action"),  # action | objective_step
            "ref_id": item.get("ref_id", ""),
            "title": item.get("title", "Sans titre"),
            "duration_minutes": min(max(int(item.get("duration_minutes", 5)), 1), 120),
            "order": i,
        })

    # Frequency
    freq = routine.frequency if routine.frequency in ("daily", "weekdays", "weekends", "custom") else "daily"
    freq_days = None
    if freq == "custom" and routine.frequency_days:
        freq_days = [d for d in routine.frequency_days if 0 <= d <= 6]
    elif freq == "weekdays":
        freq_days = [0, 1, 2, 3, 4]
    elif freq == "weekends":
        freq_days = [5, 6]

    doc = {
        "routine_id": routine_id,
        "user_id": user["user_id"],
        "name": routine.name.strip()[:100],
        "description": (routine.description or "").strip()[:2000],
        "time_of_day": routine.time_of_day if routine.time_of_day in ("morning", "afternoon", "evening", "anytime") else "morning",
        "frequency": freq,
        "frequency_days": freq_days,
        "items": validated_items,
        "is_active": True,
        "total_minutes": sum(it["duration_minutes"] for it in validated_items),
        "times_completed": 0,
        "streak_current": 0,
        "streak_best": 0,
        "completion_log": [],  # [{date: "2026-03-11", completed_at: "..."}]
        "last_completed_at": None,
        "created_at": now,
        "updated_at": now,
    }
    await db.routines.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.get("/routines")
@limiter.limit("30/minute")
async def list_routines(request: Request, user: dict = Depends(get_current_user)):
    """List all routines for the user."""
    routines = await db.routines.find(
        {"user_id": user["user_id"], "deleted": {"$ne": True}},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    return {"routines": routines, "count": len(routines)}


@router.get("/routines/{routine_id}")
@limiter.limit("30/minute")
async def get_routine(request: Request, routine_id: str, user: dict = Depends(get_current_user)):
    """Get a single routine by ID."""
    routine = await db.routines.find_one(
        {"routine_id": routine_id, "user_id": user["user_id"], "deleted": {"$ne": True}},
        {"_id": 0}
    )
    if not routine:
        raise HTTPException(status_code=404, detail="Routine non trouvée.")
    return routine


@router.put("/routines/{routine_id}")
@limiter.limit("15/minute")
async def update_routine(request: Request, routine_id: str, update: RoutineUpdate, user: dict = Depends(get_current_user)):
    """Update a routine (name, items, active status, etc.)."""
    routine = await db.routines.find_one(
        {"routine_id": routine_id, "user_id": user["user_id"], "deleted": {"$ne": True}}
    )
    if not routine:
        raise HTTPException(status_code=404, detail="Routine non trouvée.")

    now = datetime.now(timezone.utc).isoformat()
    updates = {"updated_at": now}

    if update.name is not None:
        updates["name"] = update.name.strip()[:100]
    if update.description is not None:
        updates["description"] = update.description.strip()[:2000]
    if update.time_of_day is not None and update.time_of_day in ("morning", "afternoon", "evening", "anytime"):
        updates["time_of_day"] = update.time_of_day
    if update.frequency is not None and update.frequency in ("daily", "weekdays", "weekends", "custom"):
        updates["frequency"] = update.frequency
        if update.frequency == "custom" and update.frequency_days:
            updates["frequency_days"] = [d for d in update.frequency_days if 0 <= d <= 6]
        elif update.frequency == "weekdays":
            updates["frequency_days"] = [0, 1, 2, 3, 4]
        elif update.frequency == "weekends":
            updates["frequency_days"] = [5, 6]
        else:
            updates["frequency_days"] = None
    if update.is_active is not None:
        updates["is_active"] = update.is_active
    if update.items is not None:
        validated_items = []
        for i, item in enumerate(update.items):
            validated_items.append({
                "type": item.get("type", "action"),
                "ref_id": item.get("ref_id", ""),
                "title": item.get("title", "Sans titre"),
                "duration_minutes": min(max(int(item.get("duration_minutes", 5)), 1), 120),
                "order": i,
            })
        updates["items"] = validated_items
        updates["total_minutes"] = sum(it["duration_minutes"] for it in validated_items)

    await db.routines.update_one({"routine_id": routine_id}, {"$set": updates})
    updated = await db.routines.find_one({"routine_id": routine_id}, {"_id": 0})
    return updated


@router.delete("/routines/{routine_id}")
@limiter.limit("10/minute")
async def delete_routine(request: Request, routine_id: str, user: dict = Depends(get_current_user)):
    """Soft-delete a routine."""
    result = await db.routines.update_one(
        {"routine_id": routine_id, "user_id": user["user_id"], "deleted": {"$ne": True}},
        {"$set": {"deleted": True, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Routine non trouvée.")
    return {"status": "deleted", "routine_id": routine_id}


@router.post("/routines/{routine_id}/complete")
@limiter.limit("20/minute")
async def complete_routine(request: Request, routine_id: str, user: dict = Depends(get_current_user)):
    """Mark a routine as completed — updates streak, completion log, counter."""
    routine = await db.routines.find_one(
        {"routine_id": routine_id, "user_id": user["user_id"], "deleted": {"$ne": True}}
    )
    if not routine:
        raise HTTPException(status_code=404, detail="Routine non trouvée.")

    now = datetime.now(timezone.utc)
    today_str = now.strftime("%Y-%m-%d")

    # Prevent double-completion for same day
    completion_log = routine.get("completion_log", [])
    if any(entry.get("date") == today_str for entry in completion_log):
        return {
            "status": "already_completed",
            "routine_id": routine_id,
            "times_completed": routine.get("times_completed", 0),
            "streak_current": routine.get("streak_current", 0),
        }

    # Calculate streak
    streak = routine.get("streak_current", 0)
    last_completed = routine.get("last_completed_at")
    if last_completed:
        try:
            last_date = datetime.fromisoformat(last_completed.replace("Z", "+00:00")).date()
            today_date = now.date()
            diff = (today_date - last_date).days
            if diff == 1:
                streak += 1  # Consecutive day
            elif diff > 1:
                streak = 1  # Streak broken
            else:
                streak = max(streak, 1)
        except (ValueError, AttributeError):
            streak = 1
    else:
        streak = 1

    best_streak = max(routine.get("streak_best", 0), streak)

    # Add to completion log (keep last 90 entries)
    completion_log.append({"date": today_str, "completed_at": now.isoformat()})
    completion_log = completion_log[-90:]

    # Week completion rate (last 7 days)
    week_ago = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    week_completions = sum(1 for e in completion_log if e["date"] >= week_ago)

    await db.routines.update_one(
        {"routine_id": routine_id},
        {
            "$inc": {"times_completed": 1},
            "$set": {
                "last_completed_at": now.isoformat(),
                "updated_at": now.isoformat(),
                "streak_current": streak,
                "streak_best": best_streak,
                "completion_log": completion_log,
            },
        }
    )

    new_count = routine.get("times_completed", 0) + 1
    return {
        "status": "completed",
        "routine_id": routine_id,
        "times_completed": new_count,
        "streak_current": streak,
        "streak_best": best_streak,
        "week_completions": week_completions,
    }


# ============== iCAL EXPORT ==============

def _ical_escape(text: str) -> str:
    """Escape special characters for iCal format."""
    return text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")

def _fold_line(line: str) -> str:
    """Fold long iCal lines at 75 octets per RFC 5545."""
    result = []
    while len(line.encode("utf-8")) > 75:
        # Find a safe split point
        cut = 75
        while len(line[:cut].encode("utf-8")) > 75:
            cut -= 1
        result.append(line[:cut])
        line = " " + line[cut:]
    result.append(line)
    return "\r\n".join(result)

@router.get("/routines/{routine_id}/ical")
async def export_routine_ical(routine_id: str, user: dict = Depends(get_current_user)):
    """Generate a .ics file for a routine — recurring event matching the routine's frequency."""
    routine = await db.routines.find_one(
        {"routine_id": routine_id, "user_id": user["user_id"], "deleted": {"$ne": True}}
    )
    if not routine:
        raise HTTPException(status_code=404, detail="Routine non trouvée.")

    name = _ical_escape(routine.get("name", "Routine InFinea"))
    desc_parts = [routine.get("description", "")]
    items = routine.get("items", [])
    if items:
        desc_parts.append("Actions :")
        for i, item in enumerate(items, 1):
            desc_parts.append(f"{i}. {item.get('title', '')} ({item.get('duration_minutes', 5)} min)")
    description = _ical_escape("\\n".join(p for p in desc_parts if p))

    total_min = routine.get("total_minutes", 15)
    tod = routine.get("time_of_day", "morning")
    start_hour = {"morning": "08", "afternoon": "13", "evening": "19", "anytime": "09"}.get(tod, "09")

    # Frequency mapping
    freq = routine.get("frequency", "daily")
    freq_days = routine.get("frequency_days", [])
    if freq == "daily":
        rrule = "RRULE:FREQ=DAILY"
    elif freq == "weekdays":
        rrule = "RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR"
    elif freq == "weekends":
        rrule = "RRULE:FREQ=WEEKLY;BYDAY=SA,SU"
    elif freq == "custom" and freq_days:
        day_map = {0: "MO", 1: "TU", 2: "WE", 3: "TH", 4: "FR", 5: "SA", 6: "SU"}
        days = ",".join(day_map.get(d, "MO") for d in sorted(freq_days))
        rrule = f"RRULE:FREQ=WEEKLY;BYDAY={days}"
    else:
        rrule = "RRULE:FREQ=DAILY"

    now = datetime.now(timezone.utc)
    # Start tomorrow
    tomorrow = now + timedelta(days=1)
    dtstart = tomorrow.strftime(f"%Y%m%dT{start_hour}0000")
    # End = start + duration
    end_h = int(start_hour) + (total_min // 60)
    end_m = total_min % 60
    dtend = tomorrow.strftime(f"%Y%m%dT{end_h:02d}{end_m:02d}00")
    uid = f"routine-{routine_id}@infinea.app"
    stamp = now.strftime("%Y%m%dT%H%M%SZ")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//InFinea//Routine Export//FR",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{stamp}",
        f"DTSTART:{dtstart}",
        f"DTEND:{dtend}",
        rrule,
        _fold_line(f"SUMMARY:{name}"),
        _fold_line(f"DESCRIPTION:{description}"),
        "BEGIN:VALARM",
        "TRIGGER:-PT5M",
        "ACTION:DISPLAY",
        f"DESCRIPTION:Routine {name} dans 5 minutes",
        "END:VALARM",
        "END:VEVENT",
        "END:VCALENDAR",
    ]
    ics_content = "\r\n".join(lines) + "\r\n"

    filename = f"infinea-routine-{routine_id[:8]}.ics"
    return Response(
        content=ics_content,
        media_type="text/calendar; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

@router.get("/objectives/{objective_id}/ical")
async def export_objective_ical(objective_id: str, user: dict = Depends(get_current_user)):
    """Generate a .ics file for an objective — daily session for the duration of the parcours."""
    obj = await db.objectives.find_one(
        {"objective_id": objective_id, "user_id": user["user_id"], "deleted": {"$ne": True}}
    )
    if not obj:
        raise HTTPException(status_code=404, detail="Objectif non trouvé.")

    name = _ical_escape(obj.get("title", "Objectif InFinea"))
    daily_min = obj.get("daily_minutes", 10)
    duration_days = obj.get("target_duration_days", 30)
    description = _ical_escape(f"Parcours InFinea : {name}\\n{daily_min} min/jour pendant {duration_days} jours")

    now = datetime.now(timezone.utc)
    tomorrow = now + timedelta(days=1)
    dtstart = tomorrow.strftime("%Y%m%dT090000")
    end_m = daily_min % 60
    end_h = 9 + (daily_min // 60)
    dtend = tomorrow.strftime(f"%Y%m%dT{end_h:02d}{end_m:02d}00")
    until = (tomorrow + timedelta(days=duration_days)).strftime("%Y%m%dT235959Z")
    uid = f"objective-{objective_id}@infinea.app"
    stamp = now.strftime("%Y%m%dT%H%M%SZ")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//InFinea//Objective Export//FR",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{stamp}",
        f"DTSTART:{dtstart}",
        f"DTEND:{dtend}",
        f"RRULE:FREQ=DAILY;UNTIL={until}",
        _fold_line(f"SUMMARY:{name}"),
        _fold_line(f"DESCRIPTION:{description}"),
        "BEGIN:VALARM",
        "TRIGGER:-PT5M",
        "ACTION:DISPLAY",
        f"DESCRIPTION:Session {name} dans 5 minutes",
        "END:VALARM",
        "END:VEVENT",
        "END:VCALENDAR",
    ]
    ics_content = "\r\n".join(lines) + "\r\n"

    filename = f"infinea-objectif-{objective_id[:8]}.ics"
    return Response(
        content=ics_content,
        media_type="text/calendar; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
