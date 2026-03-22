"""
InFinea — AI Suggestions route.
AI-powered micro-action recommendations.
"""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
import os
import logging
import json

from database import db
from auth import get_current_user
from models import AIRequest

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)


@router.post("/suggestions")
async def get_ai_suggestions(
    ai_request: AIRequest,
    user: dict = Depends(get_current_user),
):
    """Get AI-powered micro-action suggestions based on time and energy"""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
    except ImportError:
        raise HTTPException(status_code=503, detail="AI service not available")

    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="AI service not configured")

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
            "recommended_actions": [],
        }

    # Get user's recent activity for personalization
    recent_sessions = (
        await db.user_sessions_history.find({"user_id": user["user_id"]}, {"_id": 0})
        .sort("started_at", -1)
        .limit(5)
        .to_list(5)
    )

    recent_categories = [s.get("category", "") for s in recent_sessions]

    # Build context for AI
    actions_text = "\n".join(
        [
            f"- {a['title']} ({a['category']}, {a['duration_min']}-{a['duration_max']}min, énergie: {a['energy_level']}): {a['description']}"
            for a in available_actions[:10]
        ]
    )

    chat = LlmChat(
        api_key=api_key,
        session_id=f"suggestion_{user['user_id']}_{datetime.now().timestamp()}",
        system_message="""Tu es l'assistant InFinea, expert en productivité et bien-être.
Tu aides les utilisateurs à transformer leurs moments perdus en micro-victoires.
Réponds toujours en français, de manière concise et motivante.
Suggère les meilleures micro-actions en fonction du temps disponible et du niveau d'énergie.""",
    )
    chat.with_model("openai", "gpt-5.2")

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

    try:
        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)

        # Parse AI response
        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                ai_result = json.loads(response[json_start:json_end])
            else:
                ai_result = {
                    "top_pick": available_actions[0]["title"],
                    "reasoning": response,
                    "alternatives": [],
                }
        except Exception:
            ai_result = {
                "top_pick": available_actions[0]["title"],
                "reasoning": response,
                "alternatives": [],
            }

        # Match recommended actions with full action data
        recommended_actions = []
        for action in available_actions:
            if action["title"] == ai_result.get("top_pick"):
                recommended_actions.insert(0, action)
            elif action["title"] in ai_result.get("alternatives", []):
                recommended_actions.append(action)

        # Fill with remaining actions if needed
        if len(recommended_actions) < 3:
            for action in available_actions:
                if action not in recommended_actions:
                    recommended_actions.append(action)
                if len(recommended_actions) >= 3:
                    break

        return {
            "suggestion": ai_result.get("top_pick", available_actions[0]["title"]),
            "reasoning": ai_result.get(
                "reasoning",
                "Cette action est parfaite pour le temps dont vous disposez.",
            ),
            "recommended_actions": recommended_actions[:3],
        }
    except Exception as e:
        logger.error(f"AI suggestion error: {e}")
        return {
            "suggestion": available_actions[0]["title"]
            if available_actions
            else "Respiration profonde",
            "reasoning": "Basé sur vos préférences et le temps disponible.",
            "recommended_actions": available_actions[:3],
        }
