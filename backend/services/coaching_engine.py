"""
InFinea — Coaching Engine.

Implements the Transtheoretical Model (Prochaska & DiClemente) for adaptive coaching.
Detects user's behavior change stage from behavioral features and generates
stage-appropriate coaching directives injected into AI prompts.

5 stages:
1. PRECONTEMPLATION — new user, no sessions (awareness, curiosity)
2. CONTEMPLATION — exploring, inconsistent (reduce barriers, encourage)
3. PREPARATION — building habits (structure, routines, implementation intentions)
4. ACTION — established habits (challenge, diversify, prevent plateaus)
5. MAINTENANCE — expert user (optimize, mentor, analytical depth)

Each stage maps to specific coaching techniques, tone, and strategies.
The coaching directives are injected as Layer 3 (METHODOLOGY) in prompt_builder.

Benchmarks: Noom (health behavior change), BetterUp (executive coaching),
Headspace (meditation progression), Duolingo (gamified learning stages).
"""

import logging
from enum import Enum
from typing import Optional

logger = logging.getLogger("infinea")


class UserStage(str, Enum):
    PRECONTEMPLATION = "precontemplation"
    CONTEMPLATION = "contemplation"
    PREPARATION = "preparation"
    ACTION = "action"
    MAINTENANCE = "maintenance"


# ═══════════════════════════════════════════════════════════════════════════
# STAGE DETECTION
# ═══════════════════════════════════════════════════════════════════════════

def assess_stage(features: dict, user: dict = None) -> UserStage:
    """Determine user's Prochaska behavior change stage from behavioral features.

    Uses a multi-signal approach combining volume, consistency, and trajectory.
    Conservative thresholds — better to underestimate stage than overestimate.

    Signals used:
    - total_sessions: absolute volume of completed sessions
    - consistency_index: regularity over 30 days (0-1)
    - engagement_trend: week-over-week trajectory (-1 to +1)
    - active_days_last_30: days with at least one session
    - streak_days: current consecutive days
    """
    total = features.get("total_sessions", 0) or 0
    consistency = features.get("consistency_index", 0) or 0
    trend = features.get("engagement_trend", 0) or 0
    active_days = features.get("active_days_last_30", 0) or 0
    streak = 0
    if user:
        streak = user.get("streak_days", 0) or 0

    # Stage 1: No sessions at all
    if total == 0:
        return UserStage.PRECONTEMPLATION

    # Stage 2: Exploring but not committed (< 10 sessions OR very low consistency)
    if total < 10 or (consistency < 0.15 and total < 20):
        return UserStage.CONTEMPLATION

    # Stage 3: Building habits but not yet stable
    if total < 30 or consistency < 0.4:
        # Exception: if they have a strong streak despite low total, they're preparing well
        if streak >= 7 and trend > 0:
            return UserStage.PREPARATION
        return UserStage.PREPARATION

    # Stage 4: Active habit, consistent engagement
    if total < 100 or consistency < 0.7:
        return UserStage.ACTION

    # Stage 5: Expert user, deeply established habits
    return UserStage.MAINTENANCE


# ═══════════════════════════════════════════════════════════════════════════
# COACHING DIRECTIVES PER STAGE
# ═══════════════════════════════════════════════════════════════════════════

STAGE_DIRECTIVES = {
    UserStage.PRECONTEMPLATION: {
        "tone": "curieux, non-directif, bienveillant",
        "techniques": [
            "psychoeducation",
            "curiosite_spark",
            "micro_wins_stories",
        ],
        "prompt_fragment": (
            "METHODOLOGIE COACHING (stade: decouverte):\n"
            "L'utilisateur est au stade de decouverte. Il n'a pas encore fait de session.\n"
            "TON APPROCHE:\n"
            "- Sois curieuse et non-directive. Ne pousse JAMAIS a l'action directement.\n"
            "- Partage des faits interessants sur le micro-apprentissage "
            "(ex: '5 minutes par jour suffisent pour creer un changement mesurable').\n"
            "- Pose des questions ouvertes: 'Qu'est-ce qui t'interesse le plus?'\n"
            "- Montre les micro-victoires possibles sans pression.\n"
            "- Reduis la friction: suggere l'action la plus courte et la plus simple possible.\n"
            "- Celebre meme l'intention ('Le fait que tu sois la, c'est deja un premier pas')."
        ),
    },
    UserStage.CONTEMPLATION: {
        "tone": "encourageant, orienté possibilités, patient",
        "techniques": [
            "motivational_interviewing",
            "scaling_questions",
            "barrier_reduction",
        ],
        "prompt_fragment": (
            "METHODOLOGIE COACHING (stade: exploration):\n"
            "L'utilisateur explore mais n'a pas encore d'habitude reguliere.\n"
            "TON APPROCHE:\n"
            "- Reduis les obstacles. Suggere les actions les plus courtes (3-5 min).\n"
            "- Celebre chaque petite victoire sincerement ('Bravo, tu as pris le temps!').\n"
            "- Utilise des scaling questions: 'Sur 1 a 10, a quel point es-tu satisfait "
            "de ta semaine?' puis 'Qu'est-ce qui te ferait monter d'un point?'\n"
            "- Explore l'ambivalence sans juger: 'C'est normal d'hesiter — qu'est-ce qui "
            "te motiverait le plus?'\n"
            "- Montre le chemin sans pression. Propose, ne prescris pas.\n"
            "- Identifie SON meilleur creneau: 'Quand est-ce que c'est le plus facile pour toi?'"
        ),
    },
    UserStage.PREPARATION: {
        "tone": "structurant, supportif, orienté action",
        "techniques": [
            "implementation_intentions",
            "temptation_bundling",
            "habit_stacking",
            "goal_setting",
        ],
        "prompt_fragment": (
            "METHODOLOGIE COACHING (stade: construction):\n"
            "L'utilisateur construit une habitude. Il a de l'experience mais pas encore "
            "de regularite solide.\n"
            "TON APPROCHE:\n"
            "- Aide a structurer. Propose des routines et des objectifs precis.\n"
            "- Utilise les implementation intentions: 'Quand [situation], je ferai [action]' "
            "(augmente le suivi de 2-3x selon Gollwitzer).\n"
            "- Propose le temptation bundling: associer l'action a quelque chose de plaisant.\n"
            "- Renforce les patterns qui fonctionnent: utilise les donnees comportementales "
            "pour montrer ses meilleurs creneaux et ses forces.\n"
            "- Previens le decouragement: 'Rater un jour ne casse pas l'habitude — "
            "l'important c'est de revenir demain.'\n"
            "- Fixe des micro-objectifs: 'Cette semaine, vise 4 sessions sur 7.'"
        ),
    },
    UserStage.ACTION: {
        "tone": "stimulant, orienté croissance, challengeant",
        "techniques": [
            "positive_reinforcement",
            "difficulty_calibration",
            "diversification",
            "socratic_questioning",
        ],
        "prompt_fragment": (
            "METHODOLOGIE COACHING (stade: action):\n"
            "L'utilisateur a une habitude etablie et reguliere. Il est engage.\n"
            "TON APPROCHE:\n"
            "- Pousse a progresser. Augmente la difficulte graduellement.\n"
            "- Propose de nouvelles categories ou des actions plus longues.\n"
            "- Previens les plateaux: 'Tu maitrises bien cette zone — et si on montait "
            "d'un cran?'\n"
            "- Utilise le questionnement socratique: 'Qu'est-ce que tu as appris de "
            "cette session?' plutot que donner des reponses.\n"
            "- Celebre les milestones avec des donnees: 'Tu es dans le top 10% de regularite.'\n"
            "- Encourage le partage communautaire: 'Ton experience pourrait inspirer "
            "d'autres apprenants.'"
        ),
    },
    UserStage.MAINTENANCE: {
        "tone": "collegial, analytique, orienté maîtrise",
        "techniques": [
            "relapse_prevention",
            "identity_reinforcement",
            "mastery_orientation",
            "teaching_others",
        ],
        "prompt_fragment": (
            "METHODOLOGIE COACHING (stade: maitrise):\n"
            "L'utilisateur est un utilisateur avance avec des habitudes solides.\n"
            "TON APPROCHE:\n"
            "- Parle-lui comme a un pair. Ton ton est collegial, pas paternaliste.\n"
            "- Propose des analyses approfondies de ses patterns comportementaux.\n"
            "- Renforce son identite: 'Tu es quelqu'un qui investit dans sa progression "
            "— c'est devenu qui tu es.'\n"
            "- Encourage le mentorat: 'Ton parcours pourrait aider les nouveaux membres.'\n"
            "- Optimise les details: ajustements fins de creneaux, durees, categories.\n"
            "- Prevention de rechute: 'Les pauses sont normales — ton habitude est "
            "profondement ancree, elle reviendra.'\n"
            "- Explore la maitrise: 'Tu maitrises les bases — quel aspect veux-tu "
            "approfondir?'"
        ),
    },
}


# ═══════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════

def get_coaching_directives(stage: UserStage) -> str:
    """Get the coaching methodology prompt fragment for a given stage.

    Returns a ~200 token text block ready to inject as Layer 3 in prompt_builder.
    """
    directive = STAGE_DIRECTIVES.get(stage)
    if not directive:
        return ""
    return directive["prompt_fragment"]


def get_stage_info(stage: UserStage) -> dict:
    """Get full stage information (tone, techniques, prompt fragment)."""
    return STAGE_DIRECTIVES.get(stage, {})


async def assess_and_get_directives(
    db,
    user_id: str,
    user: dict,
) -> tuple:
    """Convenience: detect stage + return coaching directives in one call.

    Reads user_features from DB, assesses stage, returns (stage, directives_text).
    Falls back to CONTEMPLATION if features unavailable.
    """
    features = {}
    try:
        from services.cache import cache_get
        features = await cache_get(f"user_features:{user_id}") or {}
    except Exception:
        pass

    if not features:
        try:
            features = await db.user_features.find_one(
                {"user_id": user_id}, {"_id": 0}
            ) or {}
        except Exception:
            features = {}

    stage = assess_stage(features, user)
    directives = get_coaching_directives(stage)

    return stage, directives


async def get_followup_context(db, user_id: str) -> str:
    """Check if the user followed through on previous coach suggestions.

    Reads the last assistant message with a suggested_action_id,
    then checks if the user completed that action since.

    Returns a context string for prompt injection, or empty string.
    """
    try:
        # Find last coach message with a suggestion
        last_suggestion = await db.coach_messages.find_one(
            {"user_id": user_id, "role": "assistant", "suggested_action_id": {"$exists": True}},
            {"_id": 0, "suggested_action_id": 1, "created_at": 1},
            sort=[("created_at", -1)],
        )
        if not last_suggestion or not last_suggestion.get("suggested_action_id"):
            return ""

        action_id = last_suggestion["suggested_action_id"]
        suggested_at = last_suggestion.get("created_at", "")

        # Check if user completed this action since
        completed = await db.user_sessions_history.find_one({
            "user_id": user_id,
            "action_id": action_id,
            "completed": True,
            "started_at": {"$gte": suggested_at},
        })

        if completed:
            title = completed.get("action_title", "l'action suggeree")
            return (
                f"SUIVI: Tu avais suggere '{title}' lors de la derniere conversation. "
                f"L'utilisateur l'a completee ! Felicite-le et construis sur cet elan."
            )
        else:
            # Find what the action title is
            action = await db.micro_actions.find_one(
                {"action_id": action_id}, {"_id": 0, "title": 1}
            )
            title = action.get("title", "l'action suggeree") if action else "l'action suggeree"
            return (
                f"SUIVI: Tu avais suggere '{title}' lors de la derniere conversation. "
                f"L'utilisateur ne l'a pas encore faite. Ne culpabilise pas — "
                f"propose-la a nouveau subtilement ou suggere une alternative plus accessible."
            )
    except Exception:
        return ""
