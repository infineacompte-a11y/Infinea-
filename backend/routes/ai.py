"""InFinea — AI routes. Suggestions, coach, debrief, weekly analysis, streak check, custom action."""

from fastapi import APIRouter, HTTPException, Request, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import json
import os
import uuid
import httpx

from database import db
from auth import get_current_user
from helpers import (
    AI_SYSTEM_MESSAGE, get_ai_model, call_ai, parse_ai_json,
    build_user_context, check_usage_limit, send_push_to_user, track_ai_usage,
)
from config import limiter, logger
from models import AIRequest, CustomActionRequest, DebriefRequest, CoachChatRequest
from services.scoring_engine import rank_actions_for_user, get_next_best_action
from services.event_tracker import track_event
from services.feedback_loop import record_signal
# Vertical AI Phase 1
from services.prompt_builder import build_system_prompt, get_prompt_version
from services.user_model import build_deep_context
from services.knowledge_engine import get_relevant_fragments
from services.ai_feedback import record_feedback
from services.llm_provider import call_llm, get_model_for_user, ModelTier
# Vertical AI Phase 2
from services.coaching_engine import assess_and_get_directives, get_followup_context, detect_behavioral_drift, format_drift_for_prompt
from services.ai_memory import extract_memories, get_user_memories, format_memories_for_prompt

router = APIRouter()


# ── Micro-instants context builder for AI coach ──

async def _build_micro_instants_context(user_id: str) -> str:
    """Aggregate micro-instant stats into a concise context paragraph for the AI coach.
    Returns empty string if no data available (new user)."""
    now = datetime.now(timezone.utc)
    thirty_days_ago = (now - timedelta(days=30)).isoformat()
    seven_days_ago = (now - timedelta(days=7)).isoformat()
    fourteen_days_ago = (now - timedelta(days=14)).isoformat()

    outcomes = await db.micro_instant_outcomes.find(
        {"user_id": user_id, "recorded_at": {"$gte": thirty_days_ago}},
        {"_id": 0, "outcome": 1, "recorded_at": 1, "duration": 1, "source": 1},
    ).to_list(500)

    if not outcomes:
        return ""

    total = len(outcomes)
    exploited = [o for o in outcomes if o.get("outcome") == "exploited"]
    skipped = len([o for o in outcomes if o.get("outcome") == "skipped"])
    exploitation_rate = len(exploited) / total if total > 0 else 0.0
    total_minutes = sum(o.get("duration", 0) for o in exploited)

    # Weekly trend
    this_week = [o for o in outcomes if o.get("recorded_at", "") >= seven_days_ago]
    last_week = [o for o in outcomes
                 if fourteen_days_ago <= o.get("recorded_at", "") < seven_days_ago]
    this_week_exploited = len([o for o in this_week if o.get("outcome") == "exploited"])
    this_week_rate = this_week_exploited / len(this_week) if this_week else 0.0
    last_week_rate = (
        len([o for o in last_week if o.get("outcome") == "exploited"]) / len(last_week)
        if last_week else 0.0
    )
    trend_pct = round((this_week_rate - last_week_rate) * 100)

    # Best hours (top 3 with at least 2 outcomes)
    hourly: Dict[int, Dict[str, int]] = {}
    for o in exploited:
        try:
            dt = datetime.fromisoformat(o["recorded_at"].replace("Z", "+00:00"))
            h = dt.hour
            hourly.setdefault(h, {"exploited": 0, "total": 0})
            hourly[h]["exploited"] += 1
        except (ValueError, TypeError, KeyError):
            continue
    for o in outcomes:
        try:
            dt = datetime.fromisoformat(o["recorded_at"].replace("Z", "+00:00"))
            h = dt.hour
            hourly.setdefault(h, {"exploited": 0, "total": 0})
            hourly[h]["total"] += 1
        except (ValueError, TypeError, KeyError):
            continue

    best_hours = sorted(
        [(h, d["exploited"] / d["total"] if d["total"] >= 2 else 0.0, d["total"])
         for h, d in hourly.items() if d["total"] >= 2],
        key=lambda x: (x[1], x[2]),
        reverse=True,
    )[:3]

    best_slots_str = ", ".join(
        f"{h:02d}h-{h+1:02d}h ({round(rate*100)}%)"
        for h, rate, _ in best_hours
    ) if best_hours else "pas encore assez de données"

    # Source distribution
    sources = {"calendar_gap": 0, "routine_window": 0, "behavioral_pattern": 0}
    for o in outcomes:
        src = o.get("source", "")
        if src in sources:
            sources[src] += 1
    dominant_source = max(sources, key=sources.get) if any(sources.values()) else None
    source_labels = {
        "calendar_gap": "ton agenda",
        "routine_window": "tes routines",
        "behavioral_pattern": "tes habitudes comportementales",
    }

    # Build context paragraph
    trend_str = f"+{trend_pct}%" if trend_pct > 0 else f"{trend_pct}%"
    trend_label = "en progression" if trend_pct > 0 else ("stable" if trend_pct == 0 else "en baisse")

    ctx = f"""Micro-instants (30 derniers jours):
- {total} instants détectés, {len(exploited)} exploités, {skipped} skippés (taux d'exploitation: {round(exploitation_rate*100)}%)
- Tendance hebdo: {trend_str} vs semaine précédente ({trend_label})
- Meilleurs créneaux: {best_slots_str}
- {total_minutes} minutes investies via micro-instants cette semaine: {this_week_exploited} exploités sur {len(this_week)} détectés"""

    if dominant_source and sources[dominant_source] > 0:
        ctx += f"\n- Source principale des instants: {source_labels.get(dominant_source, dominant_source)}"

    return ctx


# ============== AI SUGGESTIONS ROUTE ==============

@router.post("/suggestions")
async def get_ai_suggestions(
    ai_request: AIRequest,
    user: dict = Depends(get_current_user)
):
    """Get AI-powered micro-action suggestions based on time and energy"""
    # Get matching actions from database
    query = {"duration_min": {"$lte": ai_request.available_time}}
    if ai_request.preferred_category:
        query["category"] = ai_request.preferred_category
    if ai_request.energy_level:
        query["energy_level"] = ai_request.energy_level

    # Filter premium actions for free users
    if user.get("subscription_tier") == "free":
        query["is_premium"] = False

    available_actions = await db.micro_actions.find(query, {"_id": 0}).to_list(50)

    if not available_actions:
        return {
            "suggestion": "Prenez une pause de respiration profonde",
            "reasoning": "Aucune micro-action ne correspond exactement à vos critères. Profitez de ce moment pour vous recentrer.",
            "recommended_actions": []
        }

    # Score and rank actions using behavioral features
    ranked_actions = await rank_actions_for_user(
        db, user["user_id"], available_actions,
        energy_level=ai_request.energy_level or "medium",
        available_time=ai_request.available_time,
    )
    is_scored = any("_score" in a for a in ranked_actions)

    # Get user's recent activity for personalization
    recent_sessions = await db.user_sessions_history.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).sort("started_at", -1).limit(5).to_list(5)

    recent_categories = [s.get("category", "") for s in recent_sessions]

    # Build context for AI — top 10 scored actions
    top_actions = ranked_actions[:10]
    actions_text = "\n".join([
        f"- {a['title']} ({a['category']}, {a['duration_min']}-{a['duration_max']}min, énergie: {a['energy_level']})"
        + (f" [score: {a['_score']:.2f}]" if is_scored else "")
        + f": {a['description']}"
        for a in top_actions
    ])

    is_premium = user.get("subscription_tier") == "premium"

    if is_scored and is_premium:
        # Premium + scored: enrich prompt with behavioral insights for Sonnet
        top = ranked_actions[0] if ranked_actions else {}
        breakdown = top.get("_breakdown", {})
        features_doc = await db.user_features.find_one({"user_id": user["user_id"]}, {"_id": 0})
        consistency = features_doc.get("consistency_index", 0) if features_doc else 0
        best_buckets = features_doc.get("best_performing_buckets", []) if features_doc else []

        prompt = f"""L'utilisateur a {ai_request.available_time} minutes disponibles et un niveau d'énergie {ai_request.energy_level}.
Catégories récentes: {', '.join(recent_categories) if recent_categories else 'Aucune'}
Catégorie préférée: {ai_request.preferred_category or 'Aucune'}

Profil comportemental :
- Indice de régularité : {consistency:.0%}
- Meilleurs créneaux : {', '.join(best_buckets) if best_buckets else 'pas assez de données'}
- Score #1 : {breakdown.get('category_affinity', 0):.0%} affinité catégorie, {breakdown.get('duration_fit', 0):.0%} adéquation durée, {breakdown.get('energy_match', 0):.0%} match énergie

Voici les micro-actions classées par pertinence (score comportemental) :
{actions_text}

La première action est la plus adaptée selon l'historique de l'utilisateur.
Explique en 2-3 phrases pourquoi c'est le meilleur choix, en t'appuyant sur le profil comportemental.
Propose aussi 2 alternatives avec un mot sur pourquoi chacune.
Format JSON :
- "top_pick": titre de la meilleure action
- "reasoning": explication personnalisée (2-3 phrases)
- "alternatives": liste de 2 autres titres"""
    elif is_scored:
        prompt = f"""L'utilisateur a {ai_request.available_time} minutes disponibles et un niveau d'énergie {ai_request.energy_level}.
Catégories récentes: {', '.join(recent_categories) if recent_categories else 'Aucune'}
Catégorie préférée: {ai_request.preferred_category or 'Aucune'}

Voici les micro-actions classées par pertinence (score comportemental) :
{actions_text}

La première action est la plus adaptée selon l'historique de l'utilisateur.
Explique en 1 phrase pourquoi c'est le meilleur choix pour ce moment.
Propose aussi 2 alternatives parmi les suivantes.
Format JSON :
- "top_pick": titre de la meilleure action
- "reasoning": explication courte pourquoi c'est le meilleur choix
- "alternatives": liste de 2 autres titres"""
    else:
        prompt = f"""L'utilisateur a {ai_request.available_time} minutes disponibles et un niveau d'énergie {ai_request.energy_level}.
Catégories récentes: {', '.join(recent_categories) if recent_categories else 'Aucune'}
Catégorie préférée: {ai_request.preferred_category or 'Aucune'}

Voici les micro-actions disponibles:
{actions_text}

Recommande les 3 meilleures micro-actions pour ce moment. Explique brièvement pourquoi chacune est adaptée.
Format ta réponse en JSON avec:
- "top_pick": titre de la meilleure action
- "reasoning": explication courte (1 phrase) pourquoi c'est le meilleur choix
- "alternatives": liste de 2 autres titres d'actions adaptées"""

    # Build vertical AI system prompt with knowledge + deep context
    deep_ctx = await build_deep_context(db, user, endpoint="suggestions")
    user_categories = [g for g in (user.get("user_profile") or {}).get("goals", [])]
    suggestions_system = build_system_prompt(
        endpoint="suggestions",
        user_context=deep_ctx,
        user_categories=user_categories,
    )

    response = await call_llm(
        system_prompt=suggestions_system,
        user_prompt=prompt,
        model=get_model_for_user(user),
        caller=f"suggestion_{user['user_id']}",
        user_id=user["user_id"],
    )
    ai_result = parse_ai_json(response)

    # 3.5 — Deterministic fallback: use top scored action instead of random first
    if not ai_result:
        ai_result = {"top_pick": ranked_actions[0]["title"], "reasoning": "Basé sur votre profil comportemental et le temps disponible.", "alternatives": []}

    # Match recommended actions with full action data
    recommended_actions = []
    for action in ranked_actions:
        if action["title"] == ai_result.get("top_pick"):
            recommended_actions.insert(0, action)
        elif action["title"] in ai_result.get("alternatives", []):
            recommended_actions.append(action)

    # Fill with remaining ranked actions if needed
    if len(recommended_actions) < 3:
        for action in ranked_actions:
            if action not in recommended_actions:
                recommended_actions.append(action)
            if len(recommended_actions) >= 3:
                break

    # Strip internal scoring fields from response
    clean_actions = []
    for a in recommended_actions[:3]:
        clean = {k: v for k, v in a.items() if not k.startswith("_")}
        clean_actions.append(clean)

    await track_event(db, user["user_id"], "suggestion_generated", {
        "available_time": ai_request.available_time,
        "energy_level": ai_request.energy_level,
        "category": ai_request.preferred_category,
        "top_pick": ai_result.get("top_pick"),
        "num_actions_available": len(available_actions),
        "scoring_active": is_scored,
        "top_score": ranked_actions[0].get("_score") if is_scored else None,
    })

    # Record impression signals for all shown actions (feedback loop)
    for shown_action in recommended_actions[:3]:
        aid = shown_action.get("action_id")
        if aid:
            await record_signal(db, user["user_id"], aid, "impression")

    result = {
        "suggestion": ai_result.get("top_pick", ranked_actions[0]["title"]),
        "reasoning": ai_result.get("reasoning", "Cette action est parfaite pour le temps dont vous disposez."),
        "recommended_actions": clean_actions,
    }

    # 3.4 — Scoring metadata (backward-compatible, frontend ignores it)
    if is_scored:
        result["scoring_metadata"] = {
            "scored": True,
            "top_score": ranked_actions[0].get("_score"),
            "actions_scored": len(ranked_actions),
            "feature_version": ranked_actions[0].get("_breakdown") is not None,
        }

    return result

# ============== PROACTIVE SUGGEST-NOW ROUTE ==============

@router.get("/suggest-now")
async def suggest_now(user: dict = Depends(get_current_user)):
    """
    Proactive suggestion: infer time, energy, and ideal duration from features.
    Returns top 3 actions without any user input required.
    """
    user_id = user["user_id"]
    features = await db.user_features.find_one({"user_id": user_id}, {"_id": 0})

    if not features:
        return {
            "suggestions": [],
            "context": {"scored": False},
            "message": "Pas assez de donnees pour une suggestion proactive. Completez quelques sessions d'abord.",
        }

    # Infer context from features
    from services.scoring_engine import _current_time_bucket
    bucket = _current_time_bucket()

    # Inferred energy from user's pattern at this time
    energy_pref = features.get("energy_preference_by_time", {})
    inferred_energy = energy_pref.get(bucket, "medium")

    # Inferred duration from user's preference
    preferred_duration = features.get("preferred_action_duration", 5.0)
    available_time = max(int(preferred_duration * 1.5), 10)

    # Fetch & score actions
    query = {"duration_min": {"$lte": available_time}}
    if user.get("subscription_tier") == "free":
        query["is_premium"] = False

    actions = await db.micro_actions.find(query, {"_id": 0}).to_list(50)
    if not actions:
        return {
            "suggestions": [],
            "context": {"scored": False},
            "message": "Aucune action disponible pour le moment.",
        }

    ranked = await rank_actions_for_user(
        db, user_id, actions,
        energy_level=inferred_energy,
        available_time=available_time,
    )

    # Top 3, clean internal fields
    top3 = []
    for a in ranked[:3]:
        clean = {k: v for k, v in a.items() if not k.startswith("_")}
        clean["score"] = a.get("_score")
        top3.append(clean)

    return {
        "suggestions": top3,
        "context": {
            "scored": True,
            "time_bucket": bucket,
            "inferred_energy": inferred_energy,
            "available_time": available_time,
            "preferred_duration": preferred_duration,
        },
    }

# ============== SMART PREDICTION ROUTE ==============

@router.get("/smart-predict")
async def smart_predict(user: dict = Depends(get_current_user)):
    """
    Intelligent prediction module: combines integrations data, detected slots,
    and scoring engine to predict next available moments with best actions.
    """
    user_id = user["user_id"]
    now = datetime.now(timezone.utc)

    # 1. Connected integrations (without secrets)
    integrations_raw = await db.user_integrations.find(
        {"user_id": user_id},
        {"_id": 0, "access_token": 0, "refresh_token": 0}
    ).to_list(10)

    integrations = []
    for integ in integrations_raw:
        integrations.append({
            "service": integ.get("service") or integ.get("provider", "unknown"),
            "status": "connected",
            "last_sync": integ.get("last_sync_at") or integ.get("last_synced_at"),
            "connected_at": integ.get("connected_at"),
        })

    # 2. Upcoming free slots (next 24h, max 5)
    end_24h = (now + timedelta(hours=24)).isoformat()
    raw_slots = await db.detected_free_slots.find({
        "user_id": user_id,
        "start_time": {"$gte": now.isoformat(), "$lte": end_24h},
        "dismissed": {"$ne": True},
        "action_taken": {"$ne": True},
    }, {"_id": 0}).sort("start_time", 1).to_list(5)

    # 3. Enrich each slot with scored suggestion
    predictions = []
    total_free_minutes = 0
    for slot in raw_slots:
        duration = slot.get("duration_minutes", 0)
        total_free_minutes += duration

        prediction = {
            "slot_id": slot.get("slot_id"),
            "start_time": slot.get("start_time"),
            "end_time": slot.get("end_time"),
            "duration_minutes": duration,
            "suggested_category": slot.get("suggested_category"),
        }

        # Try to score a suggestion
        if duration > 0:
            try:
                scored = await get_next_best_action(
                    db, user_id,
                    slot_duration=duration,
                    slot_start_time=slot.get("start_time"),
                    min_score=0.4,
                )
                if scored:
                    prediction["suggested_action"] = {
                        "action_id": scored.get("action_id"),
                        "title": scored.get("title"),
                        "category": scored.get("category"),
                        "score": scored.get("_score"),
                        "energy_level": scored.get("energy_level"),
                        "duration_min": scored.get("duration_min"),
                    }
            except Exception:
                pass  # scoring is best-effort

        # Fallback: use the pre-assigned suggestion if no scoring
        if "suggested_action" not in prediction and slot.get("suggested_action_id"):
            action = await db.micro_actions.find_one(
                {"action_id": slot["suggested_action_id"]}, {"_id": 0}
            )
            if action:
                prediction["suggested_action"] = {
                    "action_id": action.get("action_id"),
                    "title": action.get("title"),
                    "category": action.get("category"),
                    "energy_level": action.get("energy_level"),
                    "duration_min": action.get("duration_min"),
                }

        predictions.append(prediction)

    # 4. Proactive best action (from behavioral features)
    proactive = None
    features = await db.user_features.find_one({"user_id": user_id}, {"_id": 0})
    if features:
        try:
            from services.scoring_engine import _current_time_bucket
            bucket = _current_time_bucket()
            energy_pref = features.get("energy_preference_by_time", {})
            inferred_energy = energy_pref.get(bucket, "medium")
            preferred_duration = features.get("preferred_action_duration", 5.0)
            proactive = {
                "time_bucket": bucket,
                "inferred_energy": inferred_energy,
                "preferred_duration": round(preferred_duration, 1),
                "consistency_index": features.get("consistency_index", 0),
            }
        except Exception:
            pass

    return {
        "integrations": integrations,
        "predictions": predictions,
        "next_prediction": predictions[0] if predictions else None,
        "proactive": proactive,
        "context": {
            "has_integrations": len(integrations) > 0,
            "total_slots_today": len(predictions),
            "total_free_minutes": total_free_minutes,
            "scored": features is not None,
        },
    }

# ============== AI COACH ROUTE ==============

@router.get("/ai/coach")
@limiter.limit("10/minute")
async def get_ai_coach(request: Request, user: dict = Depends(get_current_user)):
    """Get personalized AI coach message for dashboard — context-aware"""
    # Build deep user context (injects behavioral features + objectives)
    deep_ctx = await build_deep_context(db, user, endpoint="coach_dashboard")
    # Get user's active categories for knowledge selection
    user_categories = [g for g in (user.get("user_profile") or {}).get("goals", [])]
    now = datetime.now(timezone.utc)

    # --- 1. Context detection: what just happened? ---
    # Fetch last 5 sessions (completed OR abandoned) for context
    all_recent = await db.user_sessions_history.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).sort("started_at", -1).limit(5).to_list(5)

    recent_completed = [s for s in all_recent if s.get("completed")]
    recent_abandoned = [s for s in all_recent if not s.get("completed") and s.get("completed_at")]

    # Detect immediate context (what happened in the last minutes)
    coach_mode = "default"  # default | post_completion | post_abandon | streak_milestone | comeback | first_visit
    context_detail = ""

    if not all_recent:
        # No sessions at all — first time user
        coach_mode = "first_visit"
        context_detail = "\nCONTEXTE: Première visite de l'utilisateur ! Il n'a encore fait aucune session. Sois chaleureux, explique le concept des micro-actions, et encourage à faire la première."
    else:
        # Check for recent completion (< 10 min ago)
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

        # Check for recent abandonment (< 30 min ago)
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

        # Check for streak milestones
        streak = user.get("streak_days", 0)
        if coach_mode == "default" and streak in (3, 7, 14, 21, 30, 50, 100):
            coach_mode = "streak_milestone"
            context_detail = f"\nCONTEXTE: L'utilisateur vient d'atteindre un STREAK de {streak} jours ! C'est un accomplissement majeur. Célèbre chaleureusement et motive à continuer."

        # Check for inactivity (> 3 days since last session)
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

    # --- 2. Engagement features for coaching tone ---
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

    # --- 2b. Fetch active objectives for context ---
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
    # Post-abandon: prioritize short/easy actions
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
        from services.scoring_engine import rank_actions_for_user
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
    # Phase 2: coaching stage + memories + drift detection
    _stage, coaching_text = await assess_and_get_directives(db, user["user_id"], user)
    memories = await get_user_memories(db, user["user_id"])
    memories_text = await format_memories_for_prompt(memories)
    # Detect behavioral drift and inject alert into coaching context
    drift = await detect_behavioral_drift(db, user["user_id"], deep_ctx.get("coaching_signals", {}))
    drift_text = format_drift_for_prompt(drift)
    if drift_text:
        coaching_text = f"{coaching_text}\n\n{drift_text}"

    system_prompt = build_system_prompt(
        endpoint="coach_dashboard",
        user_context=deep_ctx,
        user_categories=user_categories,
        coaching_stage_text=coaching_text,
        memories_text=memories_text,
    )

    prompt = f"""{recent_info}{engagement_context}{context_detail}

Il est actuellement le {time_of_day} ({day_of_week}).
Le streak actuel est de {user.get('streak_days', 0)} jours.{actions_menu}

Ta suggestion DOIT correspondre a une des actions disponibles (indique son numero dans chosen_action)."""

    ai_response = await call_llm(
        system_prompt=system_prompt,
        user_prompt=prompt,
        model=get_model_for_user(user),
        caller=f"coach_{user['user_id']}",
        user_id=user["user_id"],
    )
    ai_result = parse_ai_json(ai_response)

    # Resolve suggested_action_id from AI choice
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
        "ai_success": ai_result is not None,
        "time_of_day": time_of_day,
        "coach_mode": coach_mode,
        "suggested_action_id": suggested_action_id,
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

# ============== COACH CHAT (PERSISTENT) ==============

COACH_CHAT_SYSTEM = """Tu es le coach IA InFinea, un compagnon bienveillant et expert en productivité, apprentissage et bien-être.
Tu discutes naturellement avec l'utilisateur pour l'aider à progresser.
Tu es concis (2-3 phrases max par réponse), chaleureux, et tu tutoies l'utilisateur.
Tu connais son profil, ses sessions récentes, ses objectifs, et ses micro-instants (créneaux exploitables détectés automatiquement).
Quand tu as des données sur ses micro-instants, utilise-les naturellement pour donner des conseils personnalisés (meilleurs créneaux, tendances, progression).
Quand tu suggères une action, mentionne son nom exact pour que l'utilisateur puisse la lancer.
Ne réponds JAMAIS en JSON — réponds en texte naturel conversationnel."""


@router.get("/ai/coach/history")
@limiter.limit("20/minute")
async def get_coach_history(request: Request, user: dict = Depends(get_current_user)):
    """Get coach conversation history for the current user."""
    messages = await db.coach_messages.find(
        {"user_id": user["user_id"]},
        {"_id": 0, "role": 1, "content": 1, "created_at": 1, "suggested_action_id": 1}
    ).sort("created_at", 1).limit(50).to_list(50)

    return {"messages": messages}


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

    # Save user message
    await db.coach_messages.insert_one({
        "user_id": user["user_id"],
        "role": "user",
        "content": user_message,
        "created_at": now,
    })

    # Build deep context with behavioral features + objectives
    user_categories = [g for g in (user.get("user_profile") or {}).get("goals", [])]
    deep_ctx = await build_deep_context(
        db, user, endpoint="coach_chat",
        include_behavioral=True, include_objectives=True, include_social=True,
    )

    # Fetch available actions for suggestions
    act_query = {}
    if user.get("subscription_tier") == "free":
        act_query["is_premium"] = False
    available = await db.micro_actions.find(act_query, {"_id": 0, "action_id": 1, "title": 1, "category": 1, "duration_min": 1, "duration_max": 1}).to_list(10)
    actions_ctx = ""
    if available:
        lines = [f"- \"{a.get('title')}\" ({a.get('category')}, {a.get('duration_min')}-{a.get('duration_max')} min)" for a in available[:8]]
        actions_ctx = "\n\nActions disponibles que tu peux suggerer:\n" + "\n".join(lines)

    # Fetch micro-instants context
    micro_instants_ctx = await _build_micro_instants_context(user["user_id"])
    if micro_instants_ctx:
        micro_instants_ctx = "\n\n" + micro_instants_ctx

    # Build conversation history (last 20 messages)
    history_docs = await db.coach_messages.find(
        {"user_id": user["user_id"]},
        {"_id": 0, "role": 1, "content": 1}
    ).sort("created_at", -1).limit(20).to_list(20)
    history_docs.reverse()

    # Phase 2: coaching stage + memories + followup + drift
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

    # Build system prompt with vertical AI layers
    system_prompt = build_system_prompt(
        endpoint="coach_chat",
        user_context=deep_ctx,
        user_categories=user_categories,
        coaching_stage_text=coaching_text,
        memories_text=memories_text,
    )
    # Append dynamic context (actions, micro-instants) to system prompt
    system_prompt += f"{actions_ctx}{micro_instants_ctx}"

    api_messages = []
    for msg in history_docs:
        role = msg["role"]
        if role in ("user", "assistant"):
            api_messages.append({"role": role, "content": msg["content"]})

    # Ensure conversation starts with user message (Anthropic requirement)
    if not api_messages or api_messages[0]["role"] != "user":
        api_messages = [m for m in api_messages if m["role"] in ("user", "assistant")]
        if not api_messages:
            api_messages = [{"role": "user", "content": user_message}]

    # Call AI with vertical AI system + full conversation history
    assistant_content = await call_llm(
        system_prompt=system_prompt,
        user_prompt="",
        model=get_model_for_user(user),
        max_tokens=300,
        caller="coach_chat",
        user_id=user["user_id"],
        messages=api_messages,
    )

    if not assistant_content:
        assistant_content = "Je suis là pour t'aider ! Malheureusement j'ai un petit souci technique. Réessaie dans un instant."

    # Save assistant response
    await db.coach_messages.insert_one({
        "user_id": user["user_id"],
        "role": "assistant",
        "content": assistant_content,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    await track_event(db, user["user_id"], "coach_chat_message", {
        "message_length": len(user_message),
    })

    # Phase 2: fire-and-forget memory extraction from this exchange
    import asyncio as _asyncio
    _asyncio.create_task(extract_memories(db, user["user_id"], user_message, assistant_content))

    return {
        "role": "assistant",
        "content": assistant_content,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


@router.delete("/ai/coach/history")
@limiter.limit("5/minute")
async def clear_coach_history(request: Request, user: dict = Depends(get_current_user)):
    """Clear coach conversation history."""
    result = await db.coach_messages.delete_many({"user_id": user["user_id"]})
    return {"deleted": result.deleted_count}


# ============== AI COACH FEEDBACK (Vertical AI Phase 1) ==============

from pydantic import BaseModel as _BaseModel


class CoachFeedbackRequest(_BaseModel):
    message_id: Optional[str] = None
    rating: int  # 1 (not helpful) or 5 (very helpful)


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
        db=db,
        user_id=user["user_id"],
        endpoint="coach_chat",
        rating=rating,
        prompt_version=get_prompt_version(),
        message_id=feedback_req.message_id,
    )
    await track_event(db, user["user_id"], "coach_response_rated", {
        "rating": rating,
        "message_id": feedback_req.message_id,
    })
    return {"success": success, "rating": rating}


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

    # Support both frontend format (duration_minutes) and legacy (actual_duration)
    duration = debrief_req.duration_minutes or debrief_req.actual_duration or 0
    action_title = debrief_req.action_title or "micro-action"
    action_category = debrief_req.action_category or "productivité"

    # Try to get session info from DB if we have session_id
    if debrief_req.session_id and (not debrief_req.action_title):
        session = await db.sessions.find_one({"session_id": debrief_req.session_id})
        if session:
            action_info = session.get("action", {})
            action_title = action_info.get("title", action_title)
            action_category = action_info.get("category", action_category)
            if not duration:
                duration = session.get("actual_duration", 0)

    notes_info = f"\nNotes de l'utilisateur: {debrief_req.notes}" if debrief_req.notes else ""

    # --- Fetch & rank next actions BEFORE AI call ---
    next_query = {}
    if user.get("subscription_tier") == "free":
        next_query["is_premium"] = False
    next_candidates = await db.micro_actions.find(next_query, {"_id": 0}).to_list(20)
    top_next = next_candidates[:5]
    try:
        from services.scoring_engine import rank_actions_for_user
        ranked = await rank_actions_for_user(db, user["user_id"], next_candidates)
        top_next = ranked[:5] if ranked else next_candidates[:5]
    except Exception:
        pass

    # Build action menu for AI
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
        endpoint="debrief",
        user_context=deep_ctx,
        user_categories=[g for g in (user.get("user_profile") or {}).get("goals", [])],
        coaching_stage_text=coaching_text,
        memories_text=memories_text,
    )
    ai_response = await call_llm(
        system_prompt=debrief_system,
        user_prompt=prompt,
        model=get_model_for_user(user),
        caller=f"debrief_{user['user_id']}",
        user_id=user["user_id"],
    )
    ai_result = parse_ai_json(ai_response)

    # Resolve next_action_id from AI choice
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
        "action_title": action_title,
        "category": action_category,
        "duration": duration,
        "ai_success": ai_result is not None,
        "next_action_id": next_action_id,
    })

    if ai_result:
        return {
            "feedback": ai_result.get("feedback", "Bravo pour cette session !"),
            "encouragement": ai_result.get("encouragement", "Chaque minute compte."),
            "next_suggestion": ai_result.get("next_suggestion", "Continuez sur cette lancée !"),
            "next_action_id": next_action_id,
            "next_action_title": next_action_title,
        }

    return {
        "feedback": f"Excellente session de {duration} min sur {action_title} !",
        "encouragement": "Chaque micro-action vous rapproche de vos objectifs.",
        "next_suggestion": f"Pour continuer, essayez : {next_action_title}" if next_action_title else "Prenez une pause et revenez quand vous êtes prêt(e).",
        "next_action_id": next_action_id,
        "next_action_title": next_action_title,
    }

# ============== AI WEEKLY ANALYSIS ROUTE ==============

@router.get("/ai/weekly-analysis")
@limiter.limit("10/minute")
async def get_weekly_analysis(request: Request, user: dict = Depends(get_current_user)):
    """Get AI-powered weekly progress analysis"""
    deep_ctx = await build_deep_context(db, user, endpoint="weekly_analysis", include_social=True)
    user_context = deep_ctx["full_text"]

    all_sessions = await db.user_sessions_history.find(
        {"user_id": user["user_id"], "completed": True},
        {"_id": 0}
    ).sort("started_at", -1).to_list(100)

    if len(all_sessions) < 2:
        return {
            "summary": "Pas encore assez de données pour une analyse complète. Continuez vos micro-actions !",
            "strengths": [],
            "improvement_areas": [],
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
        "leadership": "leadership", "finance": "finance", "relations": "relations",
        "mental_health": "santé mentale", "entrepreneurship": "entrepreneuriat"
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
        endpoint="weekly_analysis",
        user_context=deep_ctx,
        user_categories=[g for g in (user.get("user_profile") or {}).get("goals", [])],
    )
    ai_response = await call_llm(
        system_prompt=weekly_system,
        user_prompt=prompt,
        model=get_model_for_user(user),
        caller=f"analysis_{user['user_id']}",
        user_id=user["user_id"],
    )
    ai_result = parse_ai_json(ai_response)

    await track_event(db, user["user_id"], "ai_weekly_analysis_generated", {
        "total_sessions": len(all_sessions),
        "total_duration": total_duration,
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
            streak_system = build_system_prompt(
                endpoint="streak_check",
                user_context=deep_ctx,
            )
            prompt = f"""Le streak de {streak} jours de l'utilisateur est en danger ! Il n'a pas encore fait de session aujourd'hui.
Genere un message d'alerte motivant et court.
Reponds en JSON: {{"title": "Titre court", "message": "Message motivant (1-2 phrases)"}}"""

            ai_response = await call_llm(
                system_prompt=streak_system,
                user_prompt=prompt,
                model=get_model_for_user(user),
                caller=f"streak_alert_{user['user_id']}",
                user_id=user["user_id"],
            )
            ai_result = parse_ai_json(ai_response)

            title = ai_result.get("title", f"Streak de {streak}j en danger !") if ai_result else f"Streak de {streak}j en danger !"
            message = ai_result.get("message", f"Faites une micro-action de 2 minutes pour maintenir votre streak de {streak} jours !") if ai_result else f"Faites une micro-action de 2 minutes pour maintenir votre streak de {streak} jours !"

            existing = await db.notifications.find_one({
                "user_id": user["user_id"],
                "type": "streak_alert",
                "created_at": {"$gte": datetime.combine(today, datetime.min.time()).isoformat()}
            })

            if not existing:
                notification = {
                    "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
                    "user_id": user["user_id"],
                    "type": "streak_alert",
                    "title": title,
                    "message": message,
                    "icon": "flame",
                    "read": False,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                await db.notifications.insert_one(notification)
                await send_push_to_user(user["user_id"], title, message, url="/notifications", tag="streak")
                await track_event(db, user["user_id"], "ai_streak_check_served", {
                    "streak_days": streak,
                    "at_risk": True,
                    "notification_sent": True,
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
        endpoint="create_action",
        user_context=deep_ctx,
        user_categories=[action_req.preferred_category] if action_req.preferred_category else None,
    )

    prompt = f"""L'utilisateur souhaite creer une micro-action personnalisee.
Sa description: "{action_req.description}"{cat_hint}{dur_hint}"""

    ai_response = await call_llm(
        system_prompt=create_system,
        user_prompt=prompt,
        model=get_model_for_user(user),
        caller=f"create_action_{user['user_id']}",
        user_id=user["user_id"],
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
            "is_premium": False,
            "is_custom": True,
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
            "is_premium": False,
            "is_custom": True,
            "created_by": user["user_id"],
            "created_at": datetime.now(timezone.utc).isoformat()
        }

    doc = {**action}
    await db.user_custom_actions.insert_one(doc)

    await track_event(db, user["user_id"], "ai_action_created", {
        "action_id": action_id,
        "category": action["category"],
        "ai_success": ai_result is not None,
    })

    return {"action": action}
