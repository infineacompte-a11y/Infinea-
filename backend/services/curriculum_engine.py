"""
Curriculum Engine — Generates progressive micro-session plans for user-defined objectives.

Given an objective like "Apprendre le thaï" or "Jouer du piano 10 min/jour",
generates a structured curriculum of daily micro-sessions that build on each other.

Each step includes:
- day: which day in the curriculum
- title: session title
- description: what to do
- focus: the skill/concept being practiced
- duration_min / duration_max: time range
- difficulty: 1-5 scale, progressively increasing
- prerequisites: what previous steps enable this one
- review: whether this is a review/reinforcement session
"""

import os
import json
import logging
from typing import Optional

from services.llm_provider import call_llm, get_model_for_user
from services.knowledge_engine import get_category_expertise

logger = logging.getLogger(__name__)

BATCH_SIZE = 7  # Generate 7 days at a time (one week)


async def generate_curriculum(objective: dict, user: dict) -> list:
    """Generate a full curriculum for an objective using AI.

    Returns a list of step dicts, each representing one micro-session.
    Generates in weekly batches for quality, then concatenates.
    """
    total_days = objective.get("target_duration_days", 30)
    daily_minutes = objective.get("daily_minutes", 10)
    title = objective.get("title", "Objectif")
    description = objective.get("description", "")
    category = objective.get("category", "learning")

    # User context for personalization
    profile = user.get("user_profile", {}) or {}
    energy = profile.get("energy_level", "medium")
    user_name = user.get("name", "l'utilisateur")

    # Inject category-specific expertise from knowledge engine
    category_expertise = get_category_expertise(category, max_fragments=3)

    system_prompt = f"""Tu es Kira, experte pedagogique d'InFinea. Tu concois des parcours d'apprentissage progressifs en micro-sessions.
Chaque micro-session dure entre {max(2, daily_minutes - 3)} et {daily_minutes + 2} minutes.

EXPERTISE PEDAGOGIQUE:
- Zone proximale de developpement (Vygotsky): chaque session doit etre legerement au-dessus du niveau actuel
- Difficulte desirable (Bjork): une session un peu difficile renforce l'encodage memoire
- Interleaving: varier les types d'exercices dans une semaine ameliore la retention de 25-40%
- Repetition espacee: integrer des revisions a J+3, J+7, J+14 combat la courbe de l'oubli

{category_expertise}

Regles :
- Commence par les fondamentaux, augmente progressivement la difficulte
- Integre des sessions de revision (spaced repetition) tous les 3-4 jours
- Chaque session doit etre autonome et realisable en {daily_minutes} minutes
- Varie les approches (theorie, pratique, revision, mini-defi)
- Adapte au niveau d'energie prefere : {energy}
- Sois concret et actionnable (pas de sessions vagues)
- Reponds UNIQUEMENT en JSON valide, sans markdown"""

    all_steps = []
    weeks = max(1, (total_days + 6) // 7)
    weeks = min(weeks, 13)  # Cap at 13 weeks (91 days) per generation

    for week_num in range(weeks):
        start_day = week_num * 7 + 1
        end_day = min(start_day + 6, total_days)
        if start_day > total_days:
            break

        # Build context of what was generated so far
        prev_context = ""
        if all_steps:
            last_3 = all_steps[-3:]
            prev_context = f"\n\nDernières sessions générées :\n" + "\n".join(
                f"- Jour {s['day']}: {s['title']} (difficulté {s.get('difficulty', 1)})" for s in last_3
            )

        prompt = f"""Objectif de {user_name} : "{title}"
{f'Description : {description}' if description else ''}
Catégorie : {category}
Durée du parcours : {total_days} jours
Minutes par session : {daily_minutes}
{prev_context}

Génère les sessions pour les jours {start_day} à {end_day} (semaine {week_num + 1}/{weeks}).

Réponds avec un JSON array. Chaque élément :
{{
  "day": {start_day},
  "title": "Titre court et accrocheur",
  "description": "Ce que l'utilisateur va faire concrètement (2-3 phrases)",
  "focus": "Compétence ou concept travaillé",
  "instructions": ["Étape 1", "Étape 2", "Étape 3"],
  "duration_min": {max(2, daily_minutes - 3)},
  "duration_max": {daily_minutes + 2},
  "difficulty": 1,
  "review": false,
  "tip": "Un conseil pratique pour cette session"
}}

Difficulté : 1 (semaine 1) → progressivement jusqu'à {min(5, weeks)} (dernière semaine).
Intègre 1-2 sessions de révision par semaine (review: true) à partir de la semaine 2."""

        try:
            text = await call_llm(
                system_prompt=system_prompt,
                user_prompt=prompt,
                model=get_model_for_user(user),
                max_tokens=2000,
                caller="curriculum_engine",
                user_id=user.get("user_id"),
            )

            if text:
                # Parse JSON from response
                steps = _parse_curriculum_json(text)
                if steps:
                    for i, step in enumerate(steps):
                        step["step_index"] = len(all_steps) + i
                        step["completed"] = False
                        step.setdefault("day", start_day + i)
                        step.setdefault("difficulty", min(5, week_num + 1))
                        step.setdefault("review", False)
                        step.setdefault("duration_min", max(2, daily_minutes - 3))
                        step.setdefault("duration_max", daily_minutes + 2)
                    all_steps.extend(steps)
                    logger.info(f"Curriculum week {week_num + 1}: {len(steps)} steps generated")

        except Exception as e:
            logger.error(f"Curriculum generation error (week {week_num + 1}): {e}")
            # Fill remaining days with fallback
            for d in range(start_day, end_day + 1):
                all_steps.append(_make_fallback_step(objective, d, len(all_steps)))

    if not all_steps:
        return _fallback_curriculum(objective)

    return all_steps


def _parse_curriculum_json(text: str) -> Optional[list]:
    """Extract a JSON array from AI response text."""
    try:
        # Try direct parse
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass
    try:
        # Find array in text
        start = text.find('[')
        end = text.rfind(']') + 1
        if start != -1 and end > start:
            return json.loads(text[start:end])
    except (json.JSONDecodeError, TypeError):
        pass
    return None


def _make_fallback_step(objective: dict, day: int, index: int) -> dict:
    """Create a simple fallback step when AI is unavailable."""
    daily_min = objective.get("daily_minutes", 10)
    is_review = day > 3 and day % 4 == 0
    return {
        "day": day,
        "step_index": index,
        "title": f"Session Jour {day}" + (" (Révision)" if is_review else ""),
        "description": f"Pratique de {daily_min} minutes pour \"{objective['title']}\"",
        "focus": objective["title"],
        "instructions": [
            "Reprends là où tu t'es arrêté",
            f"Pratique pendant {daily_min} minutes",
            "Note ce que tu as appris",
        ],
        "duration_min": max(2, daily_min - 3),
        "duration_max": daily_min + 2,
        "difficulty": min(5, (day // 7) + 1),
        "review": is_review,
        "completed": False,
        "tip": "La régularité est plus importante que la perfection !",
    }


def _fallback_curriculum(objective: dict) -> list:
    """Generate a full deterministic curriculum when AI is unavailable."""
    total_days = objective.get("target_duration_days", 30)
    steps = []
    for day in range(1, total_days + 1):
        steps.append(_make_fallback_step(objective, day, day - 1))
    return steps
