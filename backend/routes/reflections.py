"""
InFinea — Reflections / Journal routes.
CRUD operations and AI-powered summaries.
"""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone, timedelta
import os
import logging
import json
import uuid

from database import db
from auth import get_current_user
from models import ReflectionCreate

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)


@router.post("/reflections")
async def create_reflection(
    reflection: ReflectionCreate,
    user: dict = Depends(get_current_user),
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
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    await db.reflections.insert_one(reflection_doc)

    return {**reflection_doc, "_id": None}


@router.get("/reflections")
async def get_reflections(
    user: dict = Depends(get_current_user),
    limit: int = 50,
    skip: int = 0,
):
    """Get user's reflections"""
    reflections = (
        await db.reflections.find({"user_id": user["user_id"]}, {"_id": 0})
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
        .to_list(limit)
    )

    total = await db.reflections.count_documents({"user_id": user["user_id"]})

    return {"reflections": reflections, "total": total}


@router.get("/reflections/week")
async def get_week_reflections(user: dict = Depends(get_current_user)):
    """Get this week's reflections"""
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

    reflections = (
        await db.reflections.find(
            {"user_id": user["user_id"], "created_at": {"$gte": week_ago}}, {"_id": 0}
        )
        .sort("created_at", -1)
        .to_list(100)
    )

    return {"reflections": reflections, "count": len(reflections)}


@router.delete("/reflections/{reflection_id}")
async def delete_reflection(
    reflection_id: str,
    user: dict = Depends(get_current_user),
):
    """Delete a reflection"""
    result = await db.reflections.delete_one(
        {"reflection_id": reflection_id, "user_id": user["user_id"]}
    )

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Reflection not found")

    return {"message": "Reflection deleted"}


@router.get("/reflections/summary")
async def get_reflections_summary(user: dict = Depends(get_current_user)):
    """Generate AI-powered weekly summary of reflections"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage

    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="AI service not configured")

    month_ago = (datetime.now(timezone.utc) - timedelta(days=28)).isoformat()

    reflections = (
        await db.reflections.find(
            {"user_id": user["user_id"], "created_at": {"$gte": month_ago}}, {"_id": 0}
        )
        .sort("created_at", 1)
        .to_list(200)
    )

    if not reflections:
        return {
            "summary": None,
            "message": "Pas encore assez de réflexions pour générer un résumé. Commencez à noter vos pensées!",
            "reflection_count": 0,
        }

    sessions = await db.user_sessions_history.find(
        {
            "user_id": user["user_id"],
            "completed": True,
            "started_at": {"$gte": month_ago},
        },
        {"_id": 0},
    ).to_list(100)

    reflections_text = "\n".join(
        [
            f"[{r['created_at'][:10]}] {r.get('mood', 'neutre')}: {r['content']}"
            for r in reflections[-30:]
        ]
    )

    category_counts = {}
    total_time = 0
    for s in sessions:
        cat = s.get("category", "autre")
        category_counts[cat] = category_counts.get(cat, 0) + 1
        total_time += s.get("actual_duration", 0)

    chat = LlmChat(
        api_key=api_key,
        session_id=f"summary_{user['user_id']}_{datetime.now().timestamp()}",
        system_message="""Tu es le compagnon cognitif InFinea. Ton rôle est d'analyser les réflexions
de l'utilisateur et de fournir un résumé personnalisé, bienveillant et perspicace.
Tu dois identifier les patterns, les progrès et suggérer des axes d'amélioration.
Réponds toujours en français, de manière empathique et constructive.""",
    )
    chat.with_model("openai", "gpt-5.2")

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

    try:
        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)

        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                ai_summary = json.loads(response[json_start:json_end])
            else:
                ai_summary = {
                    "weekly_insight": response[:300],
                    "patterns_identified": [],
                    "strengths": [],
                    "areas_for_growth": [],
                    "personalized_tip": "",
                    "mood_trend": "stable",
                }
        except Exception:
            ai_summary = {
                "weekly_insight": response[:300],
                "patterns_identified": [],
                "strengths": [],
                "areas_for_growth": [],
                "personalized_tip": "",
                "mood_trend": "stable",
            }

        summary_doc = {
            "summary_id": f"sum_{uuid.uuid4().hex[:12]}",
            "user_id": user["user_id"],
            "summary": ai_summary,
            "reflection_count": len(reflections),
            "period_start": month_ago,
            "period_end": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.reflection_summaries.insert_one(summary_doc)

        return {
            "summary": ai_summary,
            "reflection_count": len(reflections),
            "session_count": len(sessions),
            "total_time": total_time,
        }

    except Exception as e:
        logger.error(f"Summary generation error: {e}")
        raise HTTPException(
            status_code=500, detail="Erreur lors de la génération du résumé"
        )


@router.get("/reflections/summaries")
async def get_past_summaries(
    user: dict = Depends(get_current_user),
    limit: int = 10,
):
    """Get past generated summaries"""
    summaries = (
        await db.reflection_summaries.find(
            {"user_id": user["user_id"]}, {"_id": 0}
        )
        .sort("created_at", -1)
        .limit(limit)
        .to_list(limit)
    )

    return {"summaries": summaries}
