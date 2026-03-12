"""InFinea — Reflections, journal, and notes routes."""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends

from database import db
from auth import get_current_user
from models import ReflectionCreate
from config import logger
from helpers import call_ai, parse_ai_json, get_ai_model, build_user_context, check_usage_limit

router = APIRouter()


@router.post("/reflections")
async def create_reflection(
    reflection: ReflectionCreate,
    user: dict = Depends(get_current_user)
):
    """Create a new reflection entry"""
    reflection_id = f"ref_{uuid.uuid4().hex[:12]}"

    reflection_doc = {
        "reflection_id": reflection_id,
        "user_id": user["user_id"],
        "content": reflection.content,
        "mood": reflection.mood,
        "tags": reflection.tags or [],
        "related_session_id": reflection.related_session_id,
        "related_category": reflection.related_category,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    await db.reflections.insert_one(reflection_doc)

    return {**reflection_doc, "_id": None}

@router.get("/reflections")
async def get_reflections(
    user: dict = Depends(get_current_user),
    limit: int = 50,
    skip: int = 0
):
    """Get user's reflections"""
    reflections = await db.reflections.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)

    total = await db.reflections.count_documents({"user_id": user["user_id"]})

    return {"reflections": reflections, "total": total}

@router.get("/reflections/week")
async def get_week_reflections(user: dict = Depends(get_current_user)):
    """Get this week's reflections"""
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

    reflections = await db.reflections.find(
        {"user_id": user["user_id"], "created_at": {"$gte": week_ago}},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)

    return {"reflections": reflections, "count": len(reflections)}

@router.delete("/reflections/{reflection_id}")
async def delete_reflection(
    reflection_id: str,
    user: dict = Depends(get_current_user)
):
    """Delete a reflection"""
    result = await db.reflections.delete_one({
        "reflection_id": reflection_id,
        "user_id": user["user_id"]
    })

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Reflection not found")

    return {"message": "Reflection deleted"}

@router.get("/reflections/summary")
async def get_reflections_summary(user: dict = Depends(get_current_user)):
    """Generate AI-powered weekly summary of reflections"""
    # Get reflections from the last 4 weeks
    month_ago = (datetime.now(timezone.utc) - timedelta(days=28)).isoformat()

    reflections = await db.reflections.find(
        {"user_id": user["user_id"], "created_at": {"$gte": month_ago}},
        {"_id": 0}
    ).sort("created_at", 1).to_list(200)

    if not reflections:
        return {
            "summary": None,
            "message": "Pas encore assez de réflexions pour générer un résumé. Commencez à noter vos pensées!",
            "reflection_count": 0
        }

    # Get sessions data for context
    sessions = await db.user_sessions_history.find(
        {"user_id": user["user_id"], "completed": True, "started_at": {"$gte": month_ago}},
        {"_id": 0}
    ).to_list(100)

    # Build reflection context
    reflections_text = "\n".join([
        f"[{r['created_at'][:10]}] {r.get('mood', 'neutre')}: {r['content']}"
        for r in reflections[-30:]
    ])

    # Session stats
    category_counts = {}
    total_time = 0
    for s in sessions:
        cat = s.get("category", "autre")
        category_counts[cat] = category_counts.get(cat, 0) + 1
        total_time += s.get("actual_duration", 0)

    system_msg = """Tu es le compagnon cognitif InFinea. Ton rôle est d'analyser les réflexions
de l'utilisateur et de fournir un résumé personnalisé, bienveillant et perspicace.
Tu dois identifier les patterns, les progrès et suggérer des axes d'amélioration.
Réponds toujours en français, de manière empathique et constructive."""

    prompt = f"""Analyse les réflexions suivantes de l'utilisateur sur les 4 dernières semaines:

{reflections_text}

Contexte d'activité:
- Sessions complétées: {len(sessions)}
- Temps total investi: {total_time} minutes
- Répartition: {', '.join([f'{k}: {v}' for k, v in category_counts.items()])}

Génère un résumé structuré en JSON avec:
- "weekly_insight": Une observation clé sur les tendances de la semaine (2-3 phrases max)
- "patterns_identified": Liste de 2-3 patterns comportementaux observés
- "strengths": Ce qui fonctionne bien (1-2 points)
- "areas_for_growth": Suggestions d'amélioration bienveillantes (1-2 points)
- "personalized_tip": Un conseil personnalisé basé sur les réflexions
- "mood_trend": Tendance générale de l'humeur (positive, stable, en progression, à surveiller)"""

    response = await call_ai(f"summary_{user['user_id']}", system_msg, prompt, model=get_ai_model(user))
    ai_summary = parse_ai_json(response)

    fallback_summary = {
        "weekly_insight": "Continuez à noter vos réflexions pour un résumé plus détaillé.",
        "patterns_identified": [],
        "strengths": [],
        "areas_for_growth": [],
        "personalized_tip": "Essayez de noter au moins une réflexion par jour.",
        "mood_trend": "stable"
    }

    if not ai_summary:
        ai_summary = fallback_summary

    # Store summary for history
    summary_doc = {
        "summary_id": f"sum_{uuid.uuid4().hex[:12]}",
        "user_id": user["user_id"],
        "summary": ai_summary,
        "reflection_count": len(reflections),
        "period_start": month_ago,
        "period_end": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.reflection_summaries.insert_one(summary_doc)

    return {
        "summary": ai_summary,
        "reflection_count": len(reflections),
        "session_count": len(sessions),
        "total_time": total_time
    }

@router.get("/reflections/summaries")
async def get_past_summaries(
    user: dict = Depends(get_current_user),
    limit: int = 10
):
    """Get past generated summaries"""
    summaries = await db.reflection_summaries.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)

    return {"summaries": summaries}

# ============== NOTES ROUTES ==============

NOTES_QUERY = {
    "completed": True,
    "notes": {"$exists": True, "$nin": [None, ""]}
}

@router.get("/notes/stats")
async def get_notes_stats(user: dict = Depends(get_current_user)):
    """Quick stats about user's session notes"""
    base_query = {"user_id": user["user_id"], **NOTES_QUERY}

    total_notes = await db.user_sessions_history.count_documents(base_query)

    week_start = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    notes_this_week = await db.user_sessions_history.count_documents({
        **base_query,
        "completed_at": {"$gte": week_start}
    })

    pipeline = [
        {"$match": base_query},
        {"$group": {"_id": "$category", "count": {"$sum": 1}}}
    ]
    category_stats = await db.user_sessions_history.aggregate(pipeline).to_list(15)
    categories = {stat["_id"]: stat["count"] for stat in category_stats if stat["_id"]}

    pipeline_avg = [
        {"$match": base_query},
        {"$project": {"note_length": {"$strLenCP": "$notes"}}},
        {"$group": {"_id": None, "avg_length": {"$avg": "$note_length"}}}
    ]
    avg_result = await db.user_sessions_history.aggregate(pipeline_avg).to_list(1)
    avg_note_length = int(avg_result[0]["avg_length"]) if avg_result else 0

    return {
        "total_notes": total_notes,
        "notes_this_week": notes_this_week,
        "categories": categories,
        "avg_note_length": avg_note_length,
    }

@router.get("/notes/analysis")
async def get_notes_analysis(
    user: dict = Depends(get_current_user),
    force: bool = False
):
    """AI-powered analysis of user's session notes with caching"""
    user_id = user["user_id"]
    is_premium = user.get("subscription_tier") == "premium"

    # Check cache first (unless force refresh)
    if not force:
        cache_hours = 12 if is_premium else 24
        cache_cutoff = (datetime.now(timezone.utc) - timedelta(hours=cache_hours)).isoformat()
        cached = await db.notes_analysis_cache.find_one(
            {"user_id": user_id, "generated_at": {"$gte": cache_cutoff}},
            {"_id": 0}
        )
        if cached:
            return {
                "analysis": cached["analysis"],
                "generated_at": cached["generated_at"],
                "cached": True,
                "note_count": cached.get("note_count", 0),
            }

    # Usage limit for free users (force refresh only)
    if not is_premium and force:
        usage = await check_usage_limit(user_id, "notes_analysis", 1, "daily")
        if not usage["allowed"]:
            return {
                "analysis": None,
                "error": "limit_reached",
                "message": "Vous avez atteint la limite d'analyses aujourd'hui. Passez Premium pour des analyses illimitées !",
                "usage": usage,
            }

    # Fetch notes
    lookback_days = 90 if is_premium else 30
    cutoff = (datetime.now(timezone.utc) - timedelta(days=lookback_days)).isoformat()

    sessions_with_notes = await db.user_sessions_history.find(
        {"user_id": user_id, **NOTES_QUERY, "completed_at": {"$gte": cutoff}},
        {"_id": 0}
    ).sort("completed_at", -1).to_list(50)

    if len(sessions_with_notes) < 3:
        return {
            "analysis": None,
            "message": "Complétez quelques sessions avec des notes pour générer une analyse.",
            "note_count": len(sessions_with_notes),
            "min_required": 3,
        }

    # Build notes context
    notes_text = "\n".join([
        f"[{s.get('completed_at', '')[:10]}] {s.get('action_title', 'Action')} ({s.get('category', 'autre')}): {s['notes']}"
        for s in sessions_with_notes
    ])

    cat_counts = {}
    for s in sessions_with_notes:
        cat = s.get("category", "autre")
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

    categories_fr = {
        "learning": "apprentissage", "productivity": "productivité",
        "well_being": "bien-être", "creativity": "créativité",
        "fitness": "forme physique", "mindfulness": "pleine conscience",
        "leadership": "leadership", "finance": "finance",
        "relations": "relations", "mental_health": "santé mentale",
        "entrepreneurship": "entrepreneuriat",
    }
    cat_summary = ", ".join([f"{categories_fr.get(k, k)}: {v} notes" for k, v in cat_counts.items()])

    user_context = await build_user_context(user)

    system_msg = """Tu es le compagnon cognitif InFinea. Tu analyses les notes de session de l'utilisateur
pour identifier des patterns d'apprentissage, des progrès, et fournir des insights personnalisés.
Tes analyses sont profondes, bienveillantes et actionables. Réponds toujours en français.
Réponds UNIQUEMENT en JSON valide, sans texte autour."""

    if is_premium:
        prompt = f"""{user_context}

Voici les notes de session de l'utilisateur sur les 3 derniers mois ({len(sessions_with_notes)} notes) :

{notes_text}

Répartition des catégories : {cat_summary}

Fais une analyse approfondie et réponds en JSON :
{{
    "key_insight": "L'observation la plus importante sur le parcours de l'utilisateur (2-3 phrases)",
    "patterns": ["Pattern 1 identifié dans les notes", "Pattern 2", "Pattern 3"],
    "strengths": ["Point fort 1 observé", "Point fort 2"],
    "growth_areas": ["Axe de progression 1", "Axe de progression 2"],
    "emotional_trends": "Analyse de l'évolution émotionnelle à travers les notes (1-2 phrases)",
    "connections": "Liens entre différentes sessions et thèmes (1-2 phrases)",
    "personalized_recommendation": "Conseil personnalisé basé sur l'ensemble des notes (2-3 phrases)",
    "focus_suggestion": "Suggestion de focus pour la semaine à venir (1 phrase)"
}}"""
    else:
        prompt = f"""{user_context}

Voici les notes de session récentes de l'utilisateur ({len(sessions_with_notes)} notes) :

{notes_text}

Répartition : {cat_summary}

Fais une analyse et réponds en JSON :
{{
    "key_insight": "L'observation la plus importante (1-2 phrases)",
    "patterns": ["Pattern 1", "Pattern 2"],
    "strengths": ["Point fort observé"],
    "growth_areas": ["Axe de progression"],
    "personalized_recommendation": "Conseil personnalisé (1-2 phrases)"
}}"""

    ai_response = await call_ai(
        f"notes_analysis_{user_id}",
        system_msg,
        prompt,
        model=get_ai_model(user),
    )
    ai_result = parse_ai_json(ai_response)

    # Fallback if AI fails
    if not ai_result:
        top_category = max(cat_counts, key=cat_counts.get) if cat_counts else "general"
        ai_result = {
            "key_insight": f"Vous avez écrit {len(sessions_with_notes)} notes, principalement en {categories_fr.get(top_category, top_category)}. Continuez à documenter vos sessions !",
            "patterns": [],
            "strengths": ["Régularité dans la prise de notes"],
            "growth_areas": ["Essayez d'approfondir vos réflexions"],
            "personalized_recommendation": "Notez ce que vous avez appris ET ce que vous ressentez pour des analyses plus riches.",
        }

    # Cache the result
    await db.notes_analysis_cache.update_one(
        {"user_id": user_id},
        {"$set": {
            "user_id": user_id,
            "analysis": ai_result,
            "note_count": len(sessions_with_notes),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }},
        upsert=True,
    )

    return {
        "analysis": ai_result,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "cached": False,
        "note_count": len(sessions_with_notes),
    }

@router.get("/notes")
async def get_user_notes(
    user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 20,
    category: Optional[str] = None,
):
    """Get all sessions with non-empty notes, paginated"""
    query = {"user_id": user["user_id"], **NOTES_QUERY}
    if category:
        query["category"] = category

    total = await db.user_sessions_history.count_documents(query)

    notes = await db.user_sessions_history.find(
        query,
        {"_id": 0, "session_id": 1, "action_title": 1, "category": 1,
         "notes": 1, "completed_at": 1, "actual_duration": 1}
    ).sort("completed_at", -1).skip(skip).limit(limit).to_list(limit)

    return {
        "notes": notes,
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_more": (skip + limit) < total,
    }

@router.delete("/notes/{session_id}")
async def delete_note(session_id: str, user: dict = Depends(get_current_user)):
    """Clear the notes field from a session (does not delete the session itself)"""
    result = await db.user_sessions_history.update_one(
        {"session_id": session_id, "user_id": user["user_id"]},
        {"$set": {"notes": None}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Note non trouvée")
    return {"status": "success", "message": "Note supprimée"}
