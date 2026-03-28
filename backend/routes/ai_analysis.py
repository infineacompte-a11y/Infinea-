"""InFinea — AI Analysis routes. Debrief, weekly analysis, streak check, custom actions."""

from fastapi import APIRouter, HTTPException, Request, Depends
from typing import Optional
from datetime import datetime, timezone, timedelta
import uuid

from database import db
from auth import get_current_user
from helpers import parse_ai_json, send_push_to_user
from config import limiter, logger
from models import CustomActionRequest, DebriefRequest
from services.scoring_engine import rank_actions_for_user
from services.event_tracker import track_event
from services.prompt_builder import build_system_prompt
from services.user_model import build_deep_context
from services.llm_provider import call_llm, get_model_for_user
from services.coaching_engine import assess_and_get_directives
from services.ai_memory import get_user_memories, format_memories_for_prompt

router = APIRouter()


# ============== AI DEBRIEF ROUTE ==============

@router.post("/ai/debrief")
@limiter.limit("10/minute")
async def get_ai_debrief(
    request: Request,
    debrief_req: DebriefRequest,
    user: dict = Depends(get_current_user)
):
    """Get AI debrief after completing a session"""
    deep_ctx = await build_deep_context(db, user, endpoint="debrief")
    user_context = deep_ctx["full_text"]

    duration = debrief_req.duration_minutes or debrief_req.actual_duration or 0
    action_title = debrief_req.action_title or "micro-action"
    action_category = debrief_req.action_category or "productivité"

    if debrief_req.session_id and (not debrief_req.action_title):
        session = await db.sessions.find_one({"session_id": debrief_req.session_id})
        if session:
            action_info = session.get("action", {})
            action_title = action_info.get("title", action_title)
            action_category = action_info.get("category", action_category)
            if not duration:
                duration = session.get("actual_duration", 0)

    notes_info = f"\nNotes de l'utilisateur: {debrief_req.notes}" if debrief_req.notes else ""

    next_query = {}
    if user.get("subscription_tier") == "free":
        next_query["is_premium"] = False
    next_candidates = await db.micro_actions.find(next_query, {"_id": 0}).to_list(20)
    top_next = next_candidates[:5]
    try:
        ranked = await rank_actions_for_user(db, user["user_id"], next_candidates)
        top_next = ranked[:5] if ranked else next_candidates[:5]
    except Exception:
        pass

    actions_menu = ""
    if top_next:
        action_lines = []
        for i, a in enumerate(top_next):
            dur = f"{a.get('duration_min', '?')}-{a.get('duration_max', '?')} min"
            action_lines.append(f"  {i}: \"{a.get('title', 'Action')}\" ({a.get('category', '')}, {dur})")
        actions_menu = "\n\nProchaines actions possibles (classées par pertinence):\n" + "\n".join(action_lines)

    prompt = f"""{user_context}

L'utilisateur vient de terminer une session:
- Action: {action_title} (catégorie: {action_category})
- Durée réelle: {duration} minutes{notes_info}{actions_menu}

Génère un débrief personnalisé et motivant.
Ta next_suggestion DOIT correspondre à une des actions ci-dessus (indique son numéro dans chosen_action).
Réponds en JSON:
{{
    "feedback": "Feedback personnalisé sur la session (1-2 phrases)",
    "encouragement": "Message de motivation (1 phrase)",
    "next_suggestion": "Suggestion pour la prochaine action basée sur l'action choisie (1 phrase)",
    "chosen_action": 0
}}"""

    _stage, coaching_text = await assess_and_get_directives(db, user["user_id"], user)
    memories = await get_user_memories(db, user["user_id"])
    memories_text = await format_memories_for_prompt(memories)

    debrief_system = build_system_prompt(
        endpoint="debrief", user_context=deep_ctx,
        user_categories=[g for g in (user.get("user_profile") or {}).get("goals", [])],
        coaching_stage_text=coaching_text, memories_text=memories_text,
    )
    ai_response = await call_llm(
        system_prompt=debrief_system, user_prompt=prompt,
        model=get_model_for_user(user),
        caller=f"debrief_{user['user_id']}", user_id=user["user_id"],
    )
    ai_result = parse_ai_json(ai_response)

    next_action_id = None
    next_action_title = None
    if ai_result and top_next:
        chosen_idx = ai_result.get("chosen_action", 0)
        if isinstance(chosen_idx, int) and 0 <= chosen_idx < len(top_next):
            next_action_id = top_next[chosen_idx].get("action_id")
            next_action_title = top_next[chosen_idx].get("title")
        else:
            next_action_id = top_next[0].get("action_id")
            next_action_title = top_next[0].get("title")
    elif top_next:
        next_action_id = top_next[0].get("action_id")
        next_action_title = top_next[0].get("title")

    await track_event(db, user["user_id"], "ai_debrief_generated", {
        "action_title": action_title, "category": action_category,
        "duration": duration, "ai_success": ai_result is not None,
        "next_action_id": next_action_id,
    })

    if ai_result:
        return {
            "feedback": ai_result.get("feedback", "Bravo pour cette session !"),
            "encouragement": ai_result.get("encouragement", "Chaque minute compte."),
            "next_suggestion": ai_result.get("next_suggestion", "Continuez sur cette lancée !"),
            "next_action_id": next_action_id, "next_action_title": next_action_title,
        }

    return {
        "feedback": f"Excellente session de {duration} min sur {action_title} !",
        "encouragement": "Chaque micro-action vous rapproche de vos objectifs.",
        "next_suggestion": f"Pour continuer, essayez : {next_action_title}" if next_action_title else "Prenez une pause et revenez quand vous êtes prêt(e).",
        "next_action_id": next_action_id, "next_action_title": next_action_title,
    }


# ============== AI WEEKLY ANALYSIS ROUTE ==============

@router.get("/ai/weekly-analysis")
@limiter.limit("10/minute")
async def get_weekly_analysis(request: Request, user: dict = Depends(get_current_user)):
    """Get AI-powered weekly progress analysis"""
    deep_ctx = await build_deep_context(db, user, endpoint="weekly_analysis", include_social=True)
    user_context = deep_ctx["full_text"]

    all_sessions = await db.user_sessions_history.find(
        {"user_id": user["user_id"], "completed": True}, {"_id": 0}
    ).sort("started_at", -1).to_list(100)

    if len(all_sessions) < 2:
        return {
            "summary": "Pas encore assez de données pour une analyse complète. Continuez vos micro-actions !",
            "strengths": [], "improvement_areas": [],
            "trends": "Commencez à accumuler des sessions pour voir vos tendances.",
            "personalized_tips": ["Essayez de faire au moins une micro-action par jour pour créer une habitude."]
        }

    category_counts = {}
    total_duration = 0
    for s in all_sessions:
        cat = s.get("category", "unknown")
        category_counts[cat] = category_counts.get(cat, 0) + 1
        total_duration += s.get("actual_duration", 0)

    categories_fr = {
        "learning": "apprentissage", "productivity": "productivité", "well_being": "bien-être",
        "creativity": "créativité", "fitness": "forme physique", "mindfulness": "pleine conscience",
    }
    cat_summary = ", ".join([f"{categories_fr.get(k, k)}: {v} sessions" for k, v in category_counts.items()])

    prompt = f"""{user_context}

Statistiques de l'utilisateur:
- Total sessions: {len(all_sessions)}
- Temps total: {total_duration} minutes
- Répartition: {cat_summary}
- Streak: {user.get('streak_days', 0)} jours

Analyse les progrès et génère un bilan personnalisé.
Réponds en JSON:
{{
    "summary": "Résumé global (2-3 phrases)",
    "strengths": ["Point fort 1", "Point fort 2"],
    "improvement_areas": ["Axe d'amélioration 1"],
    "trends": "Description des tendances (1-2 phrases)",
    "personalized_tips": ["Conseil personnalisé 1", "Conseil personnalisé 2"]
}}"""

    weekly_system = build_system_prompt(
        endpoint="weekly_analysis", user_context=deep_ctx,
        user_categories=[g for g in (user.get("user_profile") or {}).get("goals", [])],
    )
    ai_response = await call_llm(
        system_prompt=weekly_system, user_prompt=prompt,
        model=get_model_for_user(user),
        caller=f"analysis_{user['user_id']}", user_id=user["user_id"],
    )
    ai_result = parse_ai_json(ai_response)

    await track_event(db, user["user_id"], "ai_weekly_analysis_generated", {
        "total_sessions": len(all_sessions), "total_duration": total_duration,
        "ai_success": ai_result is not None,
    })

    if ai_result:
        return {
            "summary": ai_result.get("summary", "Bonne progression globale."),
            "strengths": ai_result.get("strengths", []),
            "improvement_areas": ai_result.get("improvement_areas", []),
            "trends": ai_result.get("trends", ""),
            "personalized_tips": ai_result.get("personalized_tips", [])
        }

    return {
        "summary": f"Vous avez complété {len(all_sessions)} sessions pour un total de {total_duration} minutes. Continuez ainsi !",
        "strengths": [f"Régularité avec {user.get('streak_days', 0)} jours de streak"],
        "improvement_areas": ["Diversifiez vos catégories d'actions"],
        "trends": f"Vous investissez en moyenne {total_duration // max(len(all_sessions), 1)} min par session.",
        "personalized_tips": ["Essayez une nouvelle catégorie cette semaine."]
    }


# ============== AI STREAK CHECK ROUTE ==============

@router.post("/ai/streak-check")
@limiter.limit("10/minute")
async def check_streak_risk(request: Request, user: dict = Depends(get_current_user)):
    """Check if user's streak is at risk and send AI notification"""
    streak = user.get("streak_days", 0)
    if streak == 0:
        return {"at_risk": False, "notification_sent": False, "message": None}

    last_session_date = user.get("last_session_date")
    today = datetime.now(timezone.utc).date()

    if last_session_date:
        if isinstance(last_session_date, str):
            last_date = datetime.fromisoformat(last_session_date).date()
        else:
            last_date = last_session_date.date() if hasattr(last_session_date, 'date') else last_session_date

        if last_date == today:
            return {"at_risk": False, "notification_sent": False, "message": None}

        if last_date == today - timedelta(days=1):
            deep_ctx = await build_deep_context(db, user, endpoint="streak_check")
            streak_system = build_system_prompt(endpoint="streak_check", user_context=deep_ctx)
            prompt = f"""Le streak de {streak} jours de l'utilisateur est en danger ! Il n'a pas encore fait de session aujourd'hui.
Genere un message d'alerte motivant et court.
Reponds en JSON: {{"title": "Titre court", "message": "Message motivant (1-2 phrases)"}}"""

            ai_response = await call_llm(
                system_prompt=streak_system, user_prompt=prompt,
                model=get_model_for_user(user),
                caller=f"streak_alert_{user['user_id']}", user_id=user["user_id"],
            )
            ai_result = parse_ai_json(ai_response)

            title = ai_result.get("title", f"Streak de {streak}j en danger !") if ai_result else f"Streak de {streak}j en danger !"
            message = ai_result.get("message", f"Faites une micro-action de 2 minutes pour maintenir votre streak de {streak} jours !") if ai_result else f"Faites une micro-action de 2 minutes pour maintenir votre streak de {streak} jours !"

            existing = await db.notifications.find_one({
                "user_id": user["user_id"], "type": "streak_alert",
                "created_at": {"$gte": datetime.combine(today, datetime.min.time()).isoformat()}
            })

            if not existing:
                notification = {
                    "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
                    "user_id": user["user_id"], "type": "streak_alert",
                    "title": title, "message": message, "icon": "flame",
                    "read": False, "created_at": datetime.now(timezone.utc).isoformat()
                }
                await db.notifications.insert_one(notification)
                await send_push_to_user(user["user_id"], title, message, url="/notifications", tag="streak")
                await track_event(db, user["user_id"], "ai_streak_check_served", {
                    "streak_days": streak, "at_risk": True, "notification_sent": True,
                })
                return {"at_risk": True, "notification_sent": True, "message": message}

            return {"at_risk": True, "notification_sent": False, "message": message}

    return {"at_risk": False, "notification_sent": False, "message": None}


# ============== AI CUSTOM ACTION ROUTES ==============

@router.post("/ai/create-action")
@limiter.limit("10/minute")
async def create_custom_action(
    request: Request,
    action_req: CustomActionRequest,
    user: dict = Depends(get_current_user)
):
    """Create a custom micro-action using AI"""
    deep_ctx = await build_deep_context(db, user, endpoint="create_action", include_objectives=False)
    cat_hint = f"\nCategorie preferee: {action_req.preferred_category}" if action_req.preferred_category else ""
    dur_hint = f"\nDuree souhaitee: {action_req.preferred_duration} minutes" if action_req.preferred_duration else ""

    create_system = build_system_prompt(
        endpoint="create_action", user_context=deep_ctx,
        user_categories=[action_req.preferred_category] if action_req.preferred_category else None,
    )

    prompt = f"""L'utilisateur souhaite creer une micro-action personnalisee.
Sa description: "{action_req.description}"{cat_hint}{dur_hint}"""

    ai_response = await call_llm(
        system_prompt=create_system, user_prompt=prompt,
        model=get_model_for_user(user),
        caller=f"create_action_{user['user_id']}", user_id=user["user_id"],
    )
    ai_result = parse_ai_json(ai_response)

    action_id = f"custom_{uuid.uuid4().hex[:12]}"

    if ai_result:
        action = {
            "action_id": action_id,
            "title": ai_result.get("title", action_req.description[:50]),
            "description": ai_result.get("description", action_req.description),
            "category": ai_result.get("category", action_req.preferred_category or "productivity"),
            "duration_min": ai_result.get("duration_min", 2),
            "duration_max": ai_result.get("duration_max", action_req.preferred_duration or 10),
            "energy_level": ai_result.get("energy_level", "medium"),
            "instructions": ai_result.get("instructions", [action_req.description]),
            "icon": ai_result.get("icon", "sparkles"),
            "is_premium": False, "is_custom": True,
            "created_by": user["user_id"],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    else:
        action = {
            "action_id": action_id,
            "title": action_req.description[:50],
            "description": action_req.description,
            "category": action_req.preferred_category or "productivity",
            "duration_min": 2,
            "duration_max": action_req.preferred_duration or 10,
            "energy_level": "medium",
            "instructions": [action_req.description],
            "icon": "sparkles",
            "is_premium": False, "is_custom": True,
            "created_by": user["user_id"],
            "created_at": datetime.now(timezone.utc).isoformat()
        }

    await db.user_custom_actions.insert_one({**action})

    await track_event(db, user["user_id"], "ai_action_created", {
        "action_id": action_id, "category": action["category"],
        "ai_success": ai_result is not None,
    })

    return {"action": action}
