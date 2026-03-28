"""InFinea — AI Coach routes. Dashboard coach, persistent chat, history, feedback."""

from fastapi import APIRouter, HTTPException, Request, Depends
from typing import Optional, Dict
from datetime import datetime, timezone, timedelta
import asyncio as _asyncio

from database import db
from auth import get_current_user
from helpers import parse_ai_json
from config import limiter, logger
from models import CoachChatRequest
from services.scoring_engine import rank_actions_for_user
from services.event_tracker import track_event
from services.prompt_builder import build_system_prompt, get_prompt_version
from services.user_model import build_deep_context
from services.llm_provider import call_llm, get_model_for_user
from services.coaching_engine import assess_and_get_directives, get_followup_context, detect_behavioral_drift, format_drift_for_prompt
from services.ai_memory import extract_memories, get_user_memories, format_memories_for_prompt
from services.ai_feedback import record_feedback
from services.collective_intelligence import get_collective_insights
from routes.ai_helpers import _build_micro_instants_context

router = APIRouter()


# ============== AI COACH ROUTE ==============

@router.get("/ai/coach")
@limiter.limit("10/minute")
async def get_ai_coach(request: Request, user: dict = Depends(get_current_user)):
    """Get personalized AI coach message for dashboard — context-aware"""
    deep_ctx = await build_deep_context(db, user, endpoint="coach_dashboard")
    user_categories = [g for g in (user.get("user_profile") or {}).get("goals", [])]
    now = datetime.now(timezone.utc)

    # --- 1. Context detection ---
    all_recent = await db.user_sessions_history.find(
        {"user_id": user["user_id"]}, {"_id": 0}
    ).sort("started_at", -1).limit(5).to_list(5)

    recent_completed = [s for s in all_recent if s.get("completed")]
    recent_abandoned = [s for s in all_recent if not s.get("completed") and s.get("completed_at")]

    coach_mode = "default"
    context_detail = ""

    if not all_recent:
        coach_mode = "first_visit"
        context_detail = "\nCONTEXTE: Première visite de l'utilisateur ! Il n'a encore fait aucune session. Sois chaleureux, explique le concept des micro-actions, et encourage à faire la première."
    else:
        if recent_completed:
            last_completed = recent_completed[0]
            try:
                completed_at = datetime.fromisoformat(last_completed.get("completed_at", ""))
                if completed_at.tzinfo is None:
                    completed_at = completed_at.replace(tzinfo=timezone.utc)
                minutes_ago = (now - completed_at).total_seconds() / 60
                if minutes_ago < 10:
                    coach_mode = "post_completion"
                    title = last_completed.get("action_title", "micro-action")
                    dur = last_completed.get("actual_duration", "?")
                    context_detail = f"\nCONTEXTE: L'utilisateur vient de TERMINER '{title}' ({dur} min) il y a {int(minutes_ago)} min ! Célèbre cette victoire et propose d'enchaîner."
            except (ValueError, TypeError):
                pass

        if coach_mode == "default" and recent_abandoned:
            last_abandoned = recent_abandoned[0]
            try:
                abandoned_at = datetime.fromisoformat(last_abandoned.get("completed_at", ""))
                if abandoned_at.tzinfo is None:
                    abandoned_at = abandoned_at.replace(tzinfo=timezone.utc)
                minutes_ago = (now - abandoned_at).total_seconds() / 60
                if minutes_ago < 30:
                    coach_mode = "post_abandon"
                    title = last_abandoned.get("action_title", "micro-action")
                    context_detail = f"\nCONTEXTE: L'utilisateur a ABANDONNÉ '{title}' il y a {int(minutes_ago)} min. Sois bienveillant, ne culpabilise pas, et propose une action PLUS COURTE et PLUS FACILE."
            except (ValueError, TypeError):
                pass

        streak = user.get("streak_days", 0)
        if coach_mode == "default" and streak in (3, 7, 14, 21, 30, 50, 100):
            coach_mode = "streak_milestone"
            context_detail = f"\nCONTEXTE: L'utilisateur vient d'atteindre un STREAK de {streak} jours ! C'est un accomplissement majeur. Célèbre chaleureusement et motive à continuer."

        if coach_mode == "default" and all_recent:
            try:
                last_session_at = datetime.fromisoformat(all_recent[0].get("started_at", ""))
                if last_session_at.tzinfo is None:
                    last_session_at = last_session_at.replace(tzinfo=timezone.utc)
                days_inactive = (now - last_session_at).days
                if days_inactive >= 3:
                    coach_mode = "comeback"
                    context_detail = f"\nCONTEXTE: L'utilisateur n'a pas fait de session depuis {days_inactive} jours. C'est un RETOUR ! Accueille-le chaleureusement, sans culpabiliser, et propose quelque chose de très accessible."
            except (ValueError, TypeError):
                pass

    recent_info = ""
    if recent_completed:
        recent_titles = [s.get("action_title", "action") for s in recent_completed[:3]]
        recent_info = f"\nSessions récentes complétées: {', '.join(recent_titles)}"

    hour = datetime.now().hour
    time_of_day = "matin" if hour < 12 else "après-midi" if hour < 18 else "soir"
    day_names = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
    day_of_week = day_names[datetime.now().weekday()]

    # --- 2. Engagement features ---
    user_features_doc = await db.user_features.find_one(
        {"user_id": user["user_id"]}, {"_id": 0, "engagement_trend": 1, "session_momentum": 1, "abandonment_rate": 1}
    )
    engagement_context = ""
    if user_features_doc:
        trend = user_features_doc.get("engagement_trend", 0.0)
        momentum = user_features_doc.get("session_momentum", 0)
        abandon = user_features_doc.get("abandonment_rate", 0.0)
        if trend > 0.1:
            engagement_context = f"\nL'utilisateur est en progression (+{trend:.0%} cette semaine). Encourage et félicite."
        elif trend < -0.1:
            engagement_context = f"\nL'utilisateur est en baisse ({trend:.0%} cette semaine). Sois bienveillant et motivant, propose quelque chose de léger."
        if momentum >= 5:
            engagement_context += f"\nIl a enchaîné {momentum} sessions d'affilée récemment — souligne cet exploit."
        if abandon > 0.4:
            engagement_context += "\nIl abandonne souvent ses sessions — propose des actions courtes et faciles."

    # --- 2b. Active objectives ---
    active_objs = await db.objectives.find(
        {"user_id": user["user_id"], "status": "active"},
        {"_id": 0, "title": 1, "current_day": 1, "target_duration_days": 1, "streak_days": 1, "progress_log": {"$slice": -2}}
    ).to_list(5)
    objectives_context = ""
    if active_objs:
        obj_lines = []
        for o in active_objs:
            pct = round((o.get("current_day", 0) / max(o.get("target_duration_days", 1), 1)) * 100)
            line = f"- \"{o['title']}\" (Jour {o.get('current_day',0)}/{o.get('target_duration_days')}, {pct}%)"
            log = o.get("progress_log", [])
            if log and log[-1].get("step_title"):
                line += f" — dernier: {log[-1]['step_title']}"
            obj_lines.append(line)
        objectives_context = "\n\nParcours actifs (l'utilisateur travaille ces objectifs — mentionne-les !):\n" + "\n".join(obj_lines)

    # --- 3. Fetch & rank candidate actions ---
    profile = user.get("user_profile", {}) or {}
    goals = profile.get("goals", [])
    act_query = {}
    if goals:
        act_query["category"] = {"$in": goals}
    if user.get("subscription_tier") == "free":
        act_query["is_premium"] = False
    if coach_mode == "post_abandon":
        act_query["duration_max"] = {"$lte": 5}
    candidate_actions = await db.micro_actions.find(act_query, {"_id": 0}).to_list(20)
    if not candidate_actions and (goals or coach_mode == "post_abandon"):
        fallback_query = {}
        if user.get("subscription_tier") == "free":
            fallback_query["is_premium"] = False
        candidate_actions = await db.micro_actions.find(fallback_query, {"_id": 0}).to_list(20)

    top_actions = candidate_actions[:5]
    try:
        ranked = await rank_actions_for_user(db, user["user_id"], candidate_actions)
        top_actions = ranked[:5] if ranked else candidate_actions[:5]
    except Exception:
        pass

    actions_menu = ""
    if top_actions:
        action_lines = []
        for i, a in enumerate(top_actions):
            dur = f"{a.get('duration_min', '?')}-{a.get('duration_max', '?')} min"
            energy = a.get("energy_level", "medium")
            action_lines.append(f"  {i}: \"{a.get('title', 'Action')}\" ({a.get('category', '')}, {dur}, énergie: {energy})")
        actions_menu = "\n\nActions disponibles (classées par pertinence):\n" + "\n".join(action_lines)

    # --- 4. Build prompt with vertical AI system ---
    _stage, coaching_text = await assess_and_get_directives(db, user["user_id"], user)
    memories = await get_user_memories(db, user["user_id"])
    memories_text = await format_memories_for_prompt(memories)
    drift = await detect_behavioral_drift(db, user["user_id"], deep_ctx.get("coaching_signals", {}))
    drift_text = format_drift_for_prompt(drift)
    if drift_text:
        coaching_text = f"{coaching_text}\n\n{drift_text}"
    user_segment = deep_ctx.get("coaching_signals", {}).get("coaching_stage", "beginner")
    segment_map = {"precontemplation": "beginner", "contemplation": "beginner",
                   "preparation": "intermediate", "action": "intermediate", "maintenance": "advanced"}
    collective = await get_collective_insights(db, segment_map.get(user_segment, "all"))
    if collective:
        memories_text = f"{memories_text}\n\n{collective}" if memories_text else collective

    system_prompt = build_system_prompt(
        endpoint="coach_dashboard", user_context=deep_ctx,
        user_categories=user_categories,
        coaching_stage_text=coaching_text, memories_text=memories_text,
    )

    prompt = f"""{recent_info}{engagement_context}{context_detail}

Il est actuellement le {time_of_day} ({day_of_week}).
Le streak actuel est de {user.get('streak_days', 0)} jours.{actions_menu}

Ta suggestion DOIT correspondre a une des actions disponibles (indique son numero dans chosen_action)."""

    ai_response = await call_llm(
        system_prompt=system_prompt, user_prompt=prompt,
        model=get_model_for_user(user),
        caller=f"coach_{user['user_id']}", user_id=user["user_id"],
    )
    ai_result = parse_ai_json(ai_response)

    suggested_action_id = None
    suggested_title = None
    if ai_result and top_actions:
        chosen_idx = ai_result.get("chosen_action", 0)
        if isinstance(chosen_idx, int) and 0 <= chosen_idx < len(top_actions):
            suggested_action_id = top_actions[chosen_idx].get("action_id")
            suggested_title = top_actions[chosen_idx].get("title")
        else:
            suggested_action_id = top_actions[0].get("action_id")
            suggested_title = top_actions[0].get("title")
    elif top_actions:
        suggested_action_id = top_actions[0].get("action_id")
        suggested_title = top_actions[0].get("title")

    await track_event(db, user["user_id"], "ai_coach_served", {
        "ai_success": ai_result is not None, "time_of_day": time_of_day,
        "coach_mode": coach_mode, "suggested_action_id": suggested_action_id,
    })

    if ai_result:
        return {
            "greeting": ai_result.get("greeting", f"Bonjour {user.get('name', '')} !"),
            "suggestion": ai_result.get("suggestion", "Commencez une micro-action pour avancer."),
            "suggested_action_id": suggested_action_id,
            "suggested_action_title": suggested_title,
            "coach_mode": coach_mode,
            "context_note": ai_result.get("context_note", f"C'est le {time_of_day}, bon moment pour progresser.")
        }

    return {
        "greeting": f"Bonjour {user.get('name', '').split(' ')[0]} ! Prêt(e) pour une micro-victoire ?",
        "suggestion": f"Que dirais-tu de : {suggested_title}" if suggested_title else "Profitez de quelques minutes pour progresser vers vos objectifs.",
        "suggested_action_id": suggested_action_id,
        "suggested_action_title": suggested_title,
        "coach_mode": coach_mode,
        "context_note": f"C'est le {time_of_day}, idéal pour une micro-action."
    }


# ============== COACH HISTORY ==============

@router.get("/ai/coach/history")
@limiter.limit("20/minute")
async def get_coach_history(request: Request, user: dict = Depends(get_current_user)):
    """Get coach conversation history for the current user."""
    messages = await db.coach_messages.find(
        {"user_id": user["user_id"]},
        {"_id": 0, "role": 1, "content": 1, "created_at": 1, "suggested_action_id": 1}
    ).sort("created_at", 1).limit(50).to_list(50)
    return {"messages": messages}


# ============== COACH CHAT (PERSISTENT) ==============

@router.post("/ai/coach/chat")
@limiter.limit("15/minute")
async def coach_chat(
    request: Request,
    chat_req: CoachChatRequest,
    user: dict = Depends(get_current_user),
):
    """Send a message to the coach and get a response."""
    user_message = chat_req.message.strip()
    if not user_message or len(user_message) > 500:
        raise HTTPException(status_code=400, detail="Message vide ou trop long (max 500 caractères)")

    now = datetime.now(timezone.utc).isoformat()

    await db.coach_messages.insert_one({
        "user_id": user["user_id"], "role": "user",
        "content": user_message, "created_at": now,
    })

    user_categories = [g for g in (user.get("user_profile") or {}).get("goals", [])]
    deep_ctx = await build_deep_context(
        db, user, endpoint="coach_chat",
        include_behavioral=True, include_objectives=True, include_social=True,
    )

    act_query = {}
    if user.get("subscription_tier") == "free":
        act_query["is_premium"] = False
    available = await db.micro_actions.find(act_query, {"_id": 0, "action_id": 1, "title": 1, "category": 1, "duration_min": 1, "duration_max": 1}).to_list(10)
    actions_ctx = ""
    if available:
        lines = [f"- \"{a.get('title')}\" ({a.get('category')}, {a.get('duration_min')}-{a.get('duration_max')} min)" for a in available[:8]]
        actions_ctx = "\n\nActions disponibles que tu peux suggerer:\n" + "\n".join(lines)

    micro_instants_ctx = await _build_micro_instants_context(user["user_id"])
    if micro_instants_ctx:
        micro_instants_ctx = "\n\n" + micro_instants_ctx

    # ── Sliding window: keep last 10 messages, summarize older context ──
    WINDOW_SIZE = 10
    history_docs = await db.coach_messages.find(
        {"user_id": user["user_id"]},
        {"_id": 0, "role": 1, "content": 1, "created_at": 1}
    ).sort("created_at", -1).limit(WINDOW_SIZE + 20).to_list(WINDOW_SIZE + 20)
    history_docs.reverse()

    older_summary = ""
    if len(history_docs) > WINDOW_SIZE:
        older_msgs = history_docs[:-WINDOW_SIZE]
        user_topics = []
        for m in older_msgs:
            if m["role"] == "user" and len(m.get("content", "")) > 15:
                user_topics.append(m["content"][:80].strip())
        if user_topics:
            topics_str = " | ".join(user_topics[-5:])
            older_summary = (
                f"CONTEXTE CONVERSATIONS PRECEDENTES "
                f"(resume des {len(older_msgs)} messages anterieurs):\n"
                f"Sujets abordes: {topics_str}\n"
                f"Total echanges precedents: {len(older_msgs)} messages.\n"
                f"Concentre-toi sur la conversation recente ci-dessous."
            )
        history_docs = history_docs[-WINDOW_SIZE:]

    _stage, coaching_text = await assess_and_get_directives(db, user["user_id"], user)
    memories = await get_user_memories(db, user["user_id"])
    memories_text = await format_memories_for_prompt(memories)
    followup = await get_followup_context(db, user["user_id"])
    if followup:
        coaching_text = f"{coaching_text}\n\n{followup}"
    drift = await detect_behavioral_drift(db, user["user_id"], deep_ctx.get("coaching_signals", {}))
    drift_text = format_drift_for_prompt(drift)
    if drift_text:
        coaching_text = f"{coaching_text}\n\n{drift_text}"
    user_segment = deep_ctx.get("coaching_signals", {}).get("coaching_stage", "beginner")
    segment_map = {"precontemplation": "beginner", "contemplation": "beginner",
                   "preparation": "intermediate", "action": "intermediate", "maintenance": "advanced"}
    collective = await get_collective_insights(db, segment_map.get(user_segment, "all"))
    if collective:
        memories_text = f"{memories_text}\n\n{collective}" if memories_text else collective

    system_prompt = build_system_prompt(
        endpoint="coach_chat", user_context=deep_ctx,
        user_categories=user_categories,
        coaching_stage_text=coaching_text, memories_text=memories_text,
    )
    if older_summary:
        system_prompt += f"\n\n{older_summary}"
    system_prompt += f"{actions_ctx}{micro_instants_ctx}"

    api_messages = []
    for msg in history_docs:
        role = msg["role"]
        if role in ("user", "assistant"):
            api_messages.append({"role": role, "content": msg["content"]})

    if not api_messages or api_messages[0]["role"] != "user":
        api_messages = [m for m in api_messages if m["role"] in ("user", "assistant")]
        if not api_messages:
            api_messages = [{"role": "user", "content": user_message}]

    assistant_content = await call_llm(
        system_prompt=system_prompt, user_prompt="",
        model=get_model_for_user(user), max_tokens=300,
        caller="coach_chat", user_id=user["user_id"],
        messages=api_messages,
    )

    if not assistant_content:
        assistant_content = "Je suis là pour t'aider ! Malheureusement j'ai un petit souci technique. Réessaie dans un instant."

    await db.coach_messages.insert_one({
        "user_id": user["user_id"], "role": "assistant",
        "content": assistant_content,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    await track_event(db, user["user_id"], "coach_chat_message", {"message_length": len(user_message)})
    _asyncio.create_task(extract_memories(db, user["user_id"], user_message, assistant_content))

    return {
        "role": "assistant",
        "content": assistant_content,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


# ============== CLEAR HISTORY ==============

@router.delete("/ai/coach/history")
@limiter.limit("5/minute")
async def clear_coach_history(request: Request, user: dict = Depends(get_current_user)):
    """Clear coach conversation history."""
    result = await db.coach_messages.delete_many({"user_id": user["user_id"]})
    return {"deleted": result.deleted_count}


# ============== AI COACH FEEDBACK ==============

from pydantic import BaseModel as _BaseModel


class CoachFeedbackRequest(_BaseModel):
    message_id: Optional[str] = None
    rating: int


@router.post("/ai/coach/feedback")
@limiter.limit("30/minute")
async def submit_coach_feedback(
    request: Request,
    feedback_req: CoachFeedbackRequest,
    user: dict = Depends(get_current_user),
):
    """Submit feedback on an AI coach response (thumbs up/down)."""
    rating = max(1, min(5, feedback_req.rating))
    success = await record_feedback(
        db=db, user_id=user["user_id"],
        endpoint="coach_chat", rating=rating,
        prompt_version=get_prompt_version(),
        message_id=feedback_req.message_id,
    )
    await track_event(db, user["user_id"], "coach_response_rated", {
        "rating": rating, "message_id": feedback_req.message_id,
    })
    return {"success": success, "rating": rating}
