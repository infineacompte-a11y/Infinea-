"""
InFinea — Onboarding routes.
Save and retrieve user profile during onboarding.
"""

from fastapi import APIRouter, HTTPException, Depends

from database import db
from auth import get_current_user
from models import OnboardingProfile
from helpers import AI_SYSTEM_MESSAGE, call_ai, parse_ai_json, build_user_context

router = APIRouter()


@router.post("/onboarding/profile")
async def save_onboarding_profile(
    profile: OnboardingProfile,
    user: dict = Depends(get_current_user)
):
    """Save user onboarding profile and generate AI welcome message"""
    profile_dict = profile.model_dump()

    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {
            "user_profile": profile_dict,
            "onboarding_completed": True
        }}
    )

    user["user_profile"] = profile_dict
    user_context = await build_user_context(user)

    goals_map = {"learning": "apprentissage", "productivity": "productivité", "well_being": "bien-être"}
    goals_fr = ", ".join([goals_map.get(g, g) for g in profile.goals])

    prompt = f"""{user_context}

L'utilisateur vient de créer son compte et de compléter son profil.
Ses objectifs principaux sont : {goals_fr}.

Génère un message d'accueil personnalisé et chaleureux, puis recommande une première micro-action adaptée à son profil.
Réponds en JSON:
{{
    "welcome_message": "Message d'accueil personnalisé (2-3 phrases)",
    "first_recommendation": "Description de la première action recommandée (1-2 phrases)"
}}"""

    ai_response = await call_ai(f"onboarding_{user['user_id']}", AI_SYSTEM_MESSAGE, prompt)
    ai_result = parse_ai_json(ai_response)

    default_welcome = f"Bienvenue sur InFinea, {user.get('name', '')} ! Prêt(e) à transformer vos moments perdus en micro-victoires ?"
    default_reco = "Commencez par une session de respiration de 2 minutes pour vous recentrer."

    return {
        "welcome_message": ai_result.get("welcome_message", default_welcome) if ai_result else default_welcome,
        "first_recommendation": ai_result.get("first_recommendation", default_reco) if ai_result else default_reco,
        "user_profile": profile_dict
    }

@router.get("/onboarding/profile")
async def get_onboarding_profile(user: dict = Depends(get_current_user)):
    """Get user's onboarding profile"""
    profile = user.get("user_profile")
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile
