"""InFinea — AI Suggestions routes. Smart action recommendations based on behavioral scoring."""

from fastapi import APIRouter, HTTPException, Request, Depends
from typing import Dict
from datetime import datetime, timezone, timedelta

from database import db
from auth import get_current_user
from helpers import parse_ai_json
from config import limiter, logger
from models import AIRequest
from services.scoring_engine import rank_actions_for_user, get_next_best_action, _current_time_bucket
from services.event_tracker import track_event
from services.feedback_loop import record_signal
from services.prompt_builder import build_system_prompt
from services.user_model import build_deep_context
from services.llm_provider import call_llm, get_model_for_user

router = APIRouter()


# ============== AI SUGGESTIONS ROUTE ==============

@router.post("/suggestions")
async def get_ai_suggestions(
    ai_request: AIRequest,
    user: dict = Depends(get_current_user)
):
    """Get AI-powered micro-action suggestions based on time and energy"""
    query = {"duration_min": {"$lte": ai_request.available_time}}
    if ai_request.preferred_category:
        query["category"] = ai_request.preferred_category
    if ai_request.energy_level:
        query["energy_level"] = ai_request.energy_level
    if user.get("subscription_tier") == "free":
        query["is_premium"] = False

    available_actions = await db.micro_actions.find(query, {"_id": 0}).to_list(50)

    if not available_actions:
        return {
            "suggestion": "Prenez une pause de respiration profonde",
            "reasoning": "Aucune micro-action ne correspond exactement à vos critères. Profitez de ce moment pour vous recentrer.",
            "recommended_actions": []
        }

    ranked_actions = await rank_actions_for_user(
        db, user["user_id"], available_actions,
        energy_level=ai_request.energy_level or "medium",
        available_time=ai_request.available_time,
    )
    is_scored = any("_score" in a for a in ranked_actions)

    recent_sessions = await db.user_sessions_history.find(
        {"user_id": user["user_id"]}, {"_id": 0}
    ).sort("started_at", -1).limit(5).to_list(5)
    recent_categories = [s.get("category", "") for s in recent_sessions]

    top_actions = ranked_actions[:10]
    actions_text = "\n".join([
        f"- {a['title']} ({a['category']}, {a['duration_min']}-{a['duration_max']}min, énergie: {a['energy_level']})"
        + (f" [score: {a['_score']:.2f}]" if is_scored else "")
        + f": {a['description']}"
        for a in top_actions
    ])

    is_premium = user.get("subscription_tier") == "premium"

    if is_scored and is_premium:
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

    deep_ctx = await build_deep_context(db, user, endpoint="suggestions")
    user_categories = [g for g in (user.get("user_profile") or {}).get("goals", [])]
    suggestions_system = build_system_prompt(
        endpoint="suggestions", user_context=deep_ctx, user_categories=user_categories,
    )

    response = await call_llm(
        system_prompt=suggestions_system, user_prompt=prompt,
        model=get_model_for_user(user),
        caller=f"suggestion_{user['user_id']}", user_id=user["user_id"],
    )
    ai_result = parse_ai_json(response)

    if not ai_result:
        ai_result = {"top_pick": ranked_actions[0]["title"], "reasoning": "Basé sur votre profil comportemental et le temps disponible.", "alternatives": []}

    recommended_actions = []
    for action in ranked_actions:
        if action["title"] == ai_result.get("top_pick"):
            recommended_actions.insert(0, action)
        elif action["title"] in ai_result.get("alternatives", []):
            recommended_actions.append(action)

    if len(recommended_actions) < 3:
        for action in ranked_actions:
            if action not in recommended_actions:
                recommended_actions.append(action)
            if len(recommended_actions) >= 3:
                break

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

    for shown_action in recommended_actions[:3]:
        aid = shown_action.get("action_id")
        if aid:
            await record_signal(db, user["user_id"], aid, "impression")

    result = {
        "suggestion": ai_result.get("top_pick", ranked_actions[0]["title"]),
        "reasoning": ai_result.get("reasoning", "Cette action est parfaite pour le temps dont vous disposez."),
        "recommended_actions": clean_actions,
    }

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
    """Proactive suggestion: infer time, energy, and ideal duration from features."""
    user_id = user["user_id"]
    features = await db.user_features.find_one({"user_id": user_id}, {"_id": 0})

    if not features:
        return {
            "suggestions": [],
            "context": {"scored": False},
            "message": "Pas assez de donnees pour une suggestion proactive. Completez quelques sessions d'abord.",
        }

    bucket = _current_time_bucket()
    energy_pref = features.get("energy_preference_by_time", {})
    inferred_energy = energy_pref.get(bucket, "medium")
    preferred_duration = features.get("preferred_action_duration", 5.0)
    available_time = max(int(preferred_duration * 1.5), 10)

    query = {"duration_min": {"$lte": available_time}}
    if user.get("subscription_tier") == "free":
        query["is_premium"] = False

    actions = await db.micro_actions.find(query, {"_id": 0}).to_list(50)
    if not actions:
        return {"suggestions": [], "context": {"scored": False}, "message": "Aucune action disponible pour le moment."}

    ranked = await rank_actions_for_user(db, user_id, actions, energy_level=inferred_energy, available_time=available_time)

    top3 = []
    for a in ranked[:3]:
        clean = {k: v for k, v in a.items() if not k.startswith("_")}
        clean["score"] = a.get("_score")
        top3.append(clean)

    return {
        "suggestions": top3,
        "context": {
            "scored": True, "time_bucket": bucket,
            "inferred_energy": inferred_energy,
            "available_time": available_time,
            "preferred_duration": preferred_duration,
        },
    }


# ============== SMART PREDICTION ROUTE ==============

@router.get("/smart-predict")
async def smart_predict(user: dict = Depends(get_current_user)):
    """Intelligent prediction: combines integrations, detected slots, and scoring engine."""
    user_id = user["user_id"]
    now = datetime.now(timezone.utc)

    integrations_raw = await db.user_integrations.find(
        {"user_id": user_id}, {"_id": 0, "access_token": 0, "refresh_token": 0}
    ).to_list(10)
    integrations = [{
        "service": integ.get("service") or integ.get("provider", "unknown"),
        "status": "connected",
        "last_sync": integ.get("last_sync_at") or integ.get("last_synced_at"),
        "connected_at": integ.get("connected_at"),
    } for integ in integrations_raw]

    end_24h = (now + timedelta(hours=24)).isoformat()
    raw_slots = await db.detected_free_slots.find({
        "user_id": user_id,
        "start_time": {"$gte": now.isoformat(), "$lte": end_24h},
        "dismissed": {"$ne": True}, "action_taken": {"$ne": True},
    }, {"_id": 0}).sort("start_time", 1).to_list(5)

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
        if duration > 0:
            try:
                scored = await get_next_best_action(db, user_id, slot_duration=duration, slot_start_time=slot.get("start_time"), min_score=0.4)
                if scored:
                    prediction["suggested_action"] = {
                        "action_id": scored.get("action_id"), "title": scored.get("title"),
                        "category": scored.get("category"), "score": scored.get("_score"),
                        "energy_level": scored.get("energy_level"), "duration_min": scored.get("duration_min"),
                    }
            except Exception:
                pass
        if "suggested_action" not in prediction and slot.get("suggested_action_id"):
            action = await db.micro_actions.find_one({"action_id": slot["suggested_action_id"]}, {"_id": 0})
            if action:
                prediction["suggested_action"] = {
                    "action_id": action.get("action_id"), "title": action.get("title"),
                    "category": action.get("category"), "energy_level": action.get("energy_level"),
                    "duration_min": action.get("duration_min"),
                }
        predictions.append(prediction)

    proactive = None
    features = await db.user_features.find_one({"user_id": user_id}, {"_id": 0})
    if features:
        try:
            bucket = _current_time_bucket()
            energy_pref = features.get("energy_preference_by_time", {})
            proactive = {
                "time_bucket": bucket,
                "inferred_energy": energy_pref.get(bucket, "medium"),
                "preferred_duration": round(features.get("preferred_action_duration", 5.0), 1),
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
