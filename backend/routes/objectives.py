"""InFinea — Objectives routes. CRUD, curriculum, skill graph, spaced repetition, insights."""

import asyncio
import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Depends

from database import db
from auth import get_current_user
from models import ObjectiveCreate, ObjectiveUpdate
from helpers import call_ai, AI_SYSTEM_MESSAGE
from config import logger, limiter
from services.event_tracker import track_event
from services.email_service import send_email_to_user, email_milestone

router = APIRouter()


# ============== OBJECTIVES (PARCOURS PERSONNALISÉS) ==============

@router.post("/objectives")
@limiter.limit("10/minute")
async def create_objective(request: Request, obj: ObjectiveCreate, user: dict = Depends(get_current_user)):
    """Create a new personal objective with AI-generated curriculum."""
    # Free users: max 2 active objectives. Premium: unlimited.
    active_count = await db.objectives.count_documents({"user_id": user["user_id"], "status": "active"})
    max_objectives = 2 if user.get("subscription_tier") != "premium" else 20
    if active_count >= max_objectives:
        tier_msg = "Passe en Premium pour plus d'objectifs !" if user.get("subscription_tier") != "premium" else "Maximum 20 objectifs actifs."
        raise HTTPException(status_code=400, detail=f"Limite atteinte ({max_objectives} objectifs actifs). {tier_msg}")

    now = datetime.now(timezone.utc).isoformat()
    objective_id = f"obj_{uuid.uuid4().hex[:12]}"

    objective_doc = {
        "objective_id": objective_id,
        "user_id": user["user_id"],
        "title": obj.title.strip(),
        "description": (obj.description or "").strip(),
        "target_duration_days": min(max(obj.target_duration_days or 30, 7), 365),
        "daily_minutes": min(max(obj.daily_minutes or 10, 2), 60),
        "category": obj.category or "learning",
        "status": "active",
        "created_at": now,
        "started_at": now,
        "current_day": 0,
        "total_sessions": 0,
        "total_minutes": 0,
        "streak_days": 0,
        "last_session_date": None,
        "curriculum": [],  # Will be populated by curriculum engine
        "progress_log": [],  # Track what was learned per session
    }

    await db.objectives.insert_one(objective_doc)

    # Generate curriculum in background (non-blocking)
    asyncio.create_task(_generate_curriculum_for_objective(objective_doc, user))

    await track_event(db, user["user_id"], "objective_created", {
        "objective_id": objective_id,
        "title": obj.title,
        "target_days": objective_doc["target_duration_days"],
    })

    # Return without _id
    objective_doc.pop("_id", None)
    return objective_doc


async def _generate_curriculum_for_objective(objective: dict, user: dict):
    """Background task: generate AI curriculum for an objective."""
    try:
        from services.curriculum_engine import generate_curriculum
        curriculum = await generate_curriculum(objective, user)
        if curriculum:
            await db.objectives.update_one(
                {"objective_id": objective["objective_id"]},
                {"$set": {"curriculum": curriculum, "curriculum_generated_at": datetime.now(timezone.utc).isoformat()}}
            )
            logger.info(f"Curriculum generated for {objective['objective_id']}: {len(curriculum)} steps")
    except Exception as e:
        logger.error(f"Curriculum generation failed for {objective['objective_id']}: {e}")


@router.get("/objectives")
@limiter.limit("30/minute")
async def list_objectives(request: Request, status: Optional[str] = None, user: dict = Depends(get_current_user)):
    """List user's objectives, optionally filtered by status."""
    query = {"user_id": user["user_id"]}
    if status:
        query["status"] = status
    objectives = await db.objectives.find(query, {"_id": 0}).sort("created_at", -1).to_list(50)
    return {"objectives": objectives}


@router.get("/objectives/{objective_id}")
@limiter.limit("30/minute")
async def get_objective(request: Request, objective_id: str, user: dict = Depends(get_current_user)):
    """Get a single objective with full curriculum and progress."""
    obj = await db.objectives.find_one(
        {"objective_id": objective_id, "user_id": user["user_id"]},
        {"_id": 0}
    )
    if not obj:
        raise HTTPException(status_code=404, detail="Objectif non trouvé")
    return obj


@router.put("/objectives/{objective_id}")
@limiter.limit("15/minute")
async def update_objective(request: Request, objective_id: str, updates: ObjectiveUpdate, user: dict = Depends(get_current_user)):
    """Update an objective (title, description, status, etc.)."""
    obj = await db.objectives.find_one({"objective_id": objective_id, "user_id": user["user_id"]})
    if not obj:
        raise HTTPException(status_code=404, detail="Objectif non trouvé")

    update_fields = {}
    if updates.title is not None:
        update_fields["title"] = updates.title.strip()
    if updates.description is not None:
        update_fields["description"] = updates.description.strip()
    if updates.target_duration_days is not None:
        update_fields["target_duration_days"] = min(max(updates.target_duration_days, 7), 365)
    if updates.daily_minutes is not None:
        update_fields["daily_minutes"] = min(max(updates.daily_minutes, 2), 60)
    if updates.status is not None:
        if updates.status not in ("active", "paused", "completed", "abandoned"):
            raise HTTPException(status_code=400, detail="Statut invalide")
        update_fields["status"] = updates.status
        if updates.status == "completed":
            update_fields["completed_at"] = datetime.now(timezone.utc).isoformat()

    if not update_fields:
        raise HTTPException(status_code=400, detail="Aucune modification")

    update_fields["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.objectives.update_one({"objective_id": objective_id}, {"$set": update_fields})

    await track_event(db, user["user_id"], "objective_updated", {
        "objective_id": objective_id,
        "fields": list(update_fields.keys()),
    })

    updated = await db.objectives.find_one({"objective_id": objective_id}, {"_id": 0})
    return updated


@router.delete("/objectives/{objective_id}")
@limiter.limit("10/minute")
async def delete_objective(request: Request, objective_id: str, user: dict = Depends(get_current_user)):
    """Delete an objective permanently."""
    result = await db.objectives.delete_one({"objective_id": objective_id, "user_id": user["user_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Objectif non trouvé")

    await track_event(db, user["user_id"], "objective_deleted", {"objective_id": objective_id})
    return {"deleted": True}


@router.get("/objectives/{objective_id}/next")
@limiter.limit("20/minute")
async def get_next_objective_session(request: Request, objective_id: str, user: dict = Depends(get_current_user)):
    """Get the next micro-session for an objective based on curriculum progress."""
    obj = await db.objectives.find_one(
        {"objective_id": objective_id, "user_id": user["user_id"]},
        {"_id": 0}
    )
    if not obj:
        raise HTTPException(status_code=404, detail="Objectif non trouvé")
    if obj["status"] != "active":
        raise HTTPException(status_code=400, detail="Objectif non actif")

    curriculum = obj.get("curriculum", [])
    if not curriculum:
        return {"status": "generating", "message": "Le curriculum est en cours de génération..."}

    # ── Spaced repetition: check for overdue reviews ──
    from services.spaced_repetition import get_review_queue, seed_reviews_from_curriculum
    await seed_reviews_from_curriculum(db, user["user_id"], objective_id, curriculum)
    review_queue = await get_review_queue(db, user["user_id"], objective_id)

    if review_queue:
        # Overdue review takes priority over new material
        top_review = review_queue[0]
        # Find a completed step matching this skill to use as review template
        review_step = None
        for step in reversed(curriculum):
            if step.get("completed") and (step.get("focus") or "").strip() == top_review["skill"]:
                review_step = step
                break

        if review_step:
            return {
                "status": "review",
                "objective_id": objective_id,
                "objective_title": obj["title"],
                "step": {
                    **review_step,
                    "completed": False,
                    "title": f"Révision : {review_step.get('title', top_review['skill'])}",
                    "review": True,
                    "review_skill": top_review["skill"],
                    "days_overdue": top_review["days_overdue"],
                },
                "review_info": {
                    "skill": top_review["skill"],
                    "days_overdue": top_review["days_overdue"],
                    "reviews_due": len(review_queue),
                },
                "progress": {
                    "current_day": obj.get("current_day", 0),
                    "total_days": obj["target_duration_days"],
                    "total_sessions": obj.get("total_sessions", 0),
                    "total_minutes": obj.get("total_minutes", 0),
                    "percent": round((obj.get("current_day", 0) / max(obj["target_duration_days"], 1)) * 100, 1),
                },
            }

    # Find next uncompleted step
    current_day = obj.get("current_day", 0)
    next_step = None
    for step in curriculum:
        if step.get("day", 0) >= current_day and not step.get("completed"):
            next_step = step
            break

    if not next_step:
        # All steps completed — generate next batch or mark complete
        return {
            "status": "completed",
            "message": f"Bravo ! Tu as terminé le parcours \"{obj['title']}\" !",
            "total_sessions": obj.get("total_sessions", 0),
            "total_minutes": obj.get("total_minutes", 0),
        }

    # Build session memory: last 5 completed steps with notes
    progress_log = obj.get("progress_log", [])
    recent_sessions = progress_log[-5:] if progress_log else []

    # Build memory context string for the frontend/coach
    memory_context = None
    if recent_sessions:
        lines = []
        for entry in recent_sessions:
            line = f"Jour {entry.get('day', '?')}: {entry.get('step_title', '?')}"
            if entry.get("notes"):
                line += f" — Notes: {entry['notes']}"
            if entry.get("duration"):
                line += f" ({entry['duration']} min)"
            lines.append(line)
        memory_context = "\n".join(lines)

    return {
        "status": "ready",
        "objective_id": objective_id,
        "objective_title": obj["title"],
        "step": next_step,
        "progress": {
            "current_day": current_day,
            "total_days": obj["target_duration_days"],
            "total_sessions": obj.get("total_sessions", 0),
            "total_minutes": obj.get("total_minutes", 0),
            "percent": round((current_day / max(obj["target_duration_days"], 1)) * 100, 1),
        },
        "memory": {
            "recent_sessions": recent_sessions,
            "context": memory_context,
            "last_notes": recent_sessions[-1].get("notes", "") if recent_sessions else "",
            "last_focus": recent_sessions[-1].get("step_title", "") if recent_sessions else "",
        },
    }


@router.post("/objectives/{objective_id}/complete-step")
@limiter.limit("15/minute")
async def complete_objective_step(request: Request, objective_id: str, user: dict = Depends(get_current_user)):
    """Mark the current step as completed after a session."""
    body = await request.json()
    step_index = body.get("step_index", 0)
    actual_duration = body.get("actual_duration", 0)
    notes = body.get("notes", "")
    completed = body.get("completed", True)

    obj = await db.objectives.find_one({"objective_id": objective_id, "user_id": user["user_id"]})
    if not obj:
        raise HTTPException(status_code=404, detail="Objectif non trouvé")

    curriculum = obj.get("curriculum", [])
    if step_index < 0 or step_index >= len(curriculum):
        raise HTTPException(status_code=400, detail="Index d'étape invalide")

    now = datetime.now(timezone.utc).isoformat()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Mark step
    update_ops = {
        f"curriculum.{step_index}.completed": completed,
        f"curriculum.{step_index}.completed_at": now,
        f"curriculum.{step_index}.actual_duration": actual_duration,
        f"curriculum.{step_index}.notes": notes,
    }

    # Update objective stats
    inc_ops = {"total_sessions": 1, "total_minutes": actual_duration}

    # Streak for this objective
    last_date = obj.get("last_session_date")
    new_day = obj.get("current_day", 0)
    obj_streak = obj.get("streak_days", 0)
    if last_date != today:
        new_day += 1
        if last_date == (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d"):
            obj_streak += 1
        elif last_date is None:
            obj_streak = 1
        else:
            obj_streak = 1  # streak broken

    update_ops["current_day"] = new_day
    update_ops["streak_days"] = obj_streak
    update_ops["last_session_date"] = today

    # Progress log entry
    progress_entry = {
        "day": new_day,
        "step_index": step_index,
        "step_title": curriculum[step_index].get("title", ""),
        "duration": actual_duration,
        "completed": completed,
        "notes": notes,
        "date": now,
    }

    await db.objectives.update_one(
        {"objective_id": objective_id},
        {
            "$set": update_ops,
            "$inc": inc_ops,
            "$push": {"progress_log": progress_entry},
        }
    )

    await track_event(db, user["user_id"], "objective_step_completed", {
        "objective_id": objective_id,
        "step_index": step_index,
        "day": new_day,
        "duration": actual_duration,
    })

    # ── Adaptive difficulty (C.4) ──────────────
    # Track performance signal for this step
    step = curriculum[step_index]
    expected_min = step.get("duration_min", 5)
    expected_max = step.get("duration_max", 15)
    difficulty = step.get("difficulty", 1)

    performance = "normal"
    if completed and actual_duration > 0:
        if actual_duration < expected_min * 0.8:
            performance = "fast"  # Completed much faster than expected
        elif actual_duration > expected_max * 1.3:
            performance = "slow"  # Took much longer than expected
    elif not completed:
        performance = "abandoned"

    # Store performance signal on the step
    await db.objectives.update_one(
        {"objective_id": objective_id},
        {"$set": {
            f"curriculum.{step_index}.performance": performance,
            f"curriculum.{step_index}.difficulty_feedback": difficulty,
        }}
    )

    # Check if objective is now complete
    completed_steps = sum(1 for s in curriculum if s.get("completed")) + (1 if completed else 0)
    total_steps = len(curriculum)
    is_finished = completed_steps >= total_steps

    # Adaptive hint for frontend
    adaptive_hint = None
    if performance == "fast":
        adaptive_hint = "Tu progresses vite ! Les prochaines sessions seront plus stimulantes."
    elif performance == "abandoned":
        adaptive_hint = "Pas de souci. La prochaine session sera un peu plus douce."

    # Email milestone — day milestones (7, 14, 30, 60, 90) + progress milestones (25%, 50%, 75%)
    try:
        obj_title = obj.get("title", "ton objectif")
        progress_pct = round((completed_steps / max(total_steps, 1)) * 100)

        if new_day in (7, 14, 30, 60, 90):
            milestone_text = f"Jour {new_day} sur « {obj_title[:40]} » !"
            subject, html = email_milestone(milestone_text)
            await send_email_to_user(user["user_id"], subject, html, email_category="achievements")
        elif progress_pct in (25, 50, 75):
            milestone_text = f"{progress_pct}% de « {obj_title[:40]} » complété !"
            subject, html = email_milestone(milestone_text)
            await send_email_to_user(user["user_id"], subject, html, email_category="achievements")
    except Exception:
        pass

    return {
        "success": True,
        "day": new_day,
        "streak": obj_streak,
        "completed_steps": completed_steps,
        "total_steps": total_steps,
        "is_finished": is_finished,
        "progress_percent": round((completed_steps / max(total_steps, 1)) * 100, 1),
        "performance": performance,
        "adaptive_hint": adaptive_hint,
    }


# ============== SKILL GRAPH + ADAPTIVE DIFFICULTY ==============

@router.get("/objectives/{objective_id}/skills")
@limiter.limit("20/minute")
async def get_objective_skills(request: Request, objective_id: str, user: dict = Depends(get_current_user)):
    """Compute skill graph from curriculum focus fields and completion data.

    Returns skills with mastery %, level labels, and spaced repetition flags.
    """
    obj = await db.objectives.find_one(
        {"objective_id": objective_id, "user_id": user["user_id"]},
        {"_id": 0}
    )
    if not obj:
        raise HTTPException(status_code=404, detail="Objectif non trouvé")

    curriculum = obj.get("curriculum", [])
    if not curriculum:
        return {"skills": [], "overall_mastery": 0, "level": "Non démarré"}

    # ── Aggregate by focus (skill) ──────────────
    skill_data = {}
    for step in curriculum:
        focus = (step.get("focus") or "").strip()
        if not focus:
            continue
        if focus not in skill_data:
            skill_data[focus] = {
                "total": 0,
                "completed": 0,
                "total_minutes": 0,
                "max_difficulty": 0,
                "last_practiced": None,
                "steps": [],
            }
        sd = skill_data[focus]
        sd["total"] += 1
        sd["max_difficulty"] = max(sd["max_difficulty"], step.get("difficulty", 1))
        if step.get("completed"):
            sd["completed"] += 1
            sd["total_minutes"] += step.get("actual_duration", step.get("duration_min", 5))
            completed_at = step.get("completed_at")
            if completed_at and (not sd["last_practiced"] or completed_at > sd["last_practiced"]):
                sd["last_practiced"] = completed_at

    # ── Build skill cards ───────────────────────
    now = datetime.now(timezone.utc)
    skills = []
    for name, data in skill_data.items():
        mastery = round((data["completed"] / max(data["total"], 1)) * 100)

        # Level label
        if mastery == 0:
            level = "Non démarré"
        elif mastery < 25:
            level = "Débutant"
        elif mastery < 50:
            level = "En progression"
        elif mastery < 75:
            level = "Intermédiaire"
        elif mastery < 100:
            level = "Avancé"
        else:
            level = "Maîtrisé"

        # Spaced repetition flag: needs review if last practiced >3 days ago
        needs_review = False
        if data["last_practiced"]:
            try:
                last_dt = datetime.fromisoformat(data["last_practiced"])
                if last_dt.tzinfo is None:
                    last_dt = last_dt.replace(tzinfo=timezone.utc)
                days_since = (now - last_dt).days
                needs_review = days_since >= 3 and mastery < 100
            except (ValueError, TypeError):
                pass
        else:
            needs_review = False

        skills.append({
            "name": name,
            "mastery": mastery,
            "level": level,
            "sessions_done": data["completed"],
            "sessions_total": data["total"],
            "total_minutes": data["total_minutes"],
            "max_difficulty": data["max_difficulty"],
            "needs_review": needs_review,
            "last_practiced": data["last_practiced"],
        })

    # Sort by mastery ascending (weakest first — shows where to focus)
    skills.sort(key=lambda s: s["mastery"])

    # ── Overall mastery ─────────────────────────
    total_completed = sum(1 for s in curriculum if s.get("completed"))
    total_steps = len(curriculum)
    overall_mastery = round((total_completed / max(total_steps, 1)) * 100)

    if overall_mastery == 0:
        overall_level = "Non démarré"
    elif overall_mastery < 25:
        overall_level = "Débutant"
    elif overall_mastery < 50:
        overall_level = "En progression"
    elif overall_mastery < 75:
        overall_level = "Intermédiaire"
    elif overall_mastery < 100:
        overall_level = "Avancé"
    else:
        overall_level = "Maîtrisé"

    # Skills needing review count
    review_count = sum(1 for s in skills if s["needs_review"])

    return {
        "skills": skills,
        "skills_count": len(skills),
        "overall_mastery": overall_mastery,
        "level": overall_level,
        "review_needed": review_count,
    }


# ============== SPACED REPETITION FEEDBACK ==============

@router.post("/objectives/{objective_id}/review-feedback")
@limiter.limit("30/minute")
async def submit_review_feedback(
    request: Request,
    objective_id: str,
    user: dict = Depends(get_current_user),
):
    """Record the user's recall quality after a review session.

    Body: { "skill": "...", "quality": 1-5 }
    Quality scale:
      1 = total blackout, 2 = wrong but recognized, 3 = correct with difficulty,
      4 = correct with hesitation, 5 = perfect recall
    """
    body = await request.json()
    skill = body.get("skill", "").strip()
    quality = body.get("quality")

    if not skill:
        raise HTTPException(status_code=400, detail="Le champ 'skill' est requis")
    if not isinstance(quality, int) or quality < 1 or quality > 5:
        raise HTTPException(status_code=400, detail="'quality' doit être un entier entre 1 et 5")

    # Verify objective belongs to user
    obj = await db.objectives.find_one(
        {"objective_id": objective_id, "user_id": user["user_id"]},
        {"_id": 0, "objective_id": 1}
    )
    if not obj:
        raise HTTPException(status_code=404, detail="Objectif non trouvé")

    from services.spaced_repetition import record_review
    result = await record_review(db, user["user_id"], objective_id, skill, quality)

    await track_event(db, user["user_id"], "sr_review_submitted", {
        "objective_id": objective_id,
        "skill": skill,
        "quality": quality,
        "next_interval": result["next_interval_days"],
    })

    return result


# ============== OBJECTIVE INSIGHTS ==============

@router.get("/objectives/{objective_id}/insights")
@limiter.limit("10/minute")
async def get_objective_insights(request: Request, objective_id: str, user: dict = Depends(get_current_user)):
    """Return structured insights for an objective: timeline, stats, AI analysis."""
    obj = await db.objectives.find_one(
        {"objective_id": objective_id, "user_id": user["user_id"]},
        {"_id": 0}
    )
    if not obj:
        raise HTTPException(status_code=404, detail="Objectif non trouvé")

    progress_log = obj.get("progress_log", [])
    curriculum = obj.get("curriculum", [])

    # ── Computed stats ──
    completed_sessions = [e for e in progress_log if e.get("completed")]
    abandoned_sessions = [e for e in progress_log if not e.get("completed")]
    durations = [e.get("duration", 0) for e in completed_sessions if e.get("duration")]
    notes_entries = [e for e in progress_log if e.get("notes", "").strip()]

    avg_duration = round(sum(durations) / len(durations), 1) if durations else 0
    total_time = sum(durations)
    completion_rate = round(len(completed_sessions) / max(len(progress_log), 1) * 100, 1) if progress_log else 0

    # Session frequency: sessions per active day
    unique_days = set()
    for entry in progress_log:
        date_str = entry.get("date", "")
        if date_str:
            unique_days.add(date_str[:10])
    active_days = len(unique_days)

    # Streak analysis
    streak = obj.get("streak_days", 0)
    best_streak = streak  # simple for now

    # Difficulty curve: map completed steps to their difficulty
    difficulty_curve = []
    for entry in completed_sessions:
        step_idx = entry.get("step_index", 0)
        if step_idx < len(curriculum):
            step = curriculum[step_idx]
            difficulty_curve.append({
                "day": entry.get("day", 0),
                "difficulty": step.get("difficulty", 1),
                "duration": entry.get("duration", 0),
                "title": step.get("title", ""),
            })

    # Weekly activity: group sessions by week
    weekly_activity = {}
    for entry in progress_log:
        date_str = entry.get("date", "")
        if date_str and len(date_str) >= 10:
            try:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                week_key = dt.strftime("%Y-W%W")
                if week_key not in weekly_activity:
                    weekly_activity[week_key] = {"sessions": 0, "minutes": 0, "week": week_key}
                weekly_activity[week_key]["sessions"] += 1
                weekly_activity[week_key]["minutes"] += entry.get("duration", 0)
            except (ValueError, TypeError):
                pass
    weekly_data = sorted(weekly_activity.values(), key=lambda x: x["week"])

    # ── AI analysis (cached in the objective doc, refreshed every 6h) ──
    ai_analysis = obj.get("ai_insights_cache", {})
    cache_age_ok = False
    if ai_analysis.get("generated_at"):
        try:
            gen_time = datetime.fromisoformat(ai_analysis["generated_at"].replace("Z", "+00:00"))
            cache_age_ok = (datetime.now(timezone.utc) - gen_time).total_seconds() < 6 * 3600
        except (ValueError, TypeError):
            pass

    if not cache_age_ok and len(completed_sessions) >= 3:
        # Generate fresh AI analysis
        notes_text = "\n".join(
            f"Jour {e.get('day', '?')} — {e.get('step_title', '?')} ({e.get('duration', '?')}min): {e.get('notes', '')}"
            for e in progress_log[-15:]  # Last 15 sessions max
        )
        analysis_prompt = f"""Analyse la progression d'un utilisateur sur l'objectif "{obj.get('title', '')}".

Données:
- {len(completed_sessions)} sessions complétées, {len(abandoned_sessions)} abandonnées
- Durée moyenne: {avg_duration} min, Total: {total_time} min
- Streak actuel: {streak} jours
- Taux de complétion: {completion_rate}%
- Jour actuel: {obj.get('current_day', 0)}/{obj.get('target_duration_days', 30)}

Journal des sessions récentes:
{notes_text}

Retourne une analyse JSON avec cette structure exacte:
{{
  "summary": "2-3 phrases de bilan global de la progression",
  "strengths": ["point fort 1", "point fort 2"],
  "improvements": ["axe d'amélioration 1", "axe d'amélioration 2"],
  "next_advice": "1 conseil concret et actionnable pour la prochaine session",
  "momentum": "rising" | "stable" | "declining",
  "momentum_label": "En progression" | "Stable" | "En baisse"
}}

Sois bienveillant, concret et motivant. Réponds UNIQUEMENT avec le JSON, rien d'autre."""

        is_premium = user.get("subscription_tier") == "premium"
        ai_model = "claude-sonnet-4-20250514" if is_premium else None
        raw = await call_ai("insights", AI_SYSTEM_MESSAGE, analysis_prompt, model=ai_model)

        if raw:
            try:
                # Extract JSON from response
                import re as _re
                json_match = _re.search(r'\{[\s\S]*\}', raw)
                if json_match:
                    ai_analysis = json.loads(json_match.group())
                    ai_analysis["generated_at"] = datetime.now(timezone.utc).isoformat()
                    # Cache in DB
                    await db.objectives.update_one(
                        {"objective_id": objective_id},
                        {"$set": {"ai_insights_cache": ai_analysis}}
                    )
            except (json.JSONDecodeError, Exception) as e:
                logger.error(f"Insights AI parse error: {e}")
                ai_analysis = {}

    # ── Build response ──
    return {
        "objective_id": objective_id,
        "title": obj.get("title", ""),
        "stats": {
            "total_sessions": len(completed_sessions),
            "abandoned_sessions": len(abandoned_sessions),
            "completion_rate": completion_rate,
            "avg_duration": avg_duration,
            "total_minutes": total_time,
            "active_days": active_days,
            "current_streak": streak,
            "current_day": obj.get("current_day", 0),
            "target_days": obj.get("target_duration_days", 30),
        },
        "timeline": progress_log,
        "notes": [
            {
                "day": e.get("day"),
                "step_title": e.get("step_title", ""),
                "notes": e.get("notes", ""),
                "date": e.get("date", ""),
                "duration": e.get("duration", 0),
            }
            for e in notes_entries
        ],
        "difficulty_curve": difficulty_curve,
        "weekly_activity": weekly_data,
        "ai_analysis": ai_analysis if ai_analysis and ai_analysis.get("summary") else None,
    }
