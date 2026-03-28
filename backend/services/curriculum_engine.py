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


# ═══════════════════════════════════════════════════════════════════════════
# ADAPTIVE CURRICULUM — Performance-based week generation
# ═══════════════════════════════════════════════════════════════════════════

def analyze_week_performance(curriculum: list, current_day: int) -> dict:
    """Analyze performance of the completed week to calibrate next week.

    Looks at the last 7 completed steps and computes:
    - avg_completion_rate: % of steps completed
    - avg_actual_vs_expected: ratio of actual duration to expected
    - difficulty_feedback: weighted average difficulty of completed steps
    - fast_count: steps completed much faster than expected
    - abandoned_count: steps not completed
    - performance_signals: list of (performance, difficulty) tuples

    Returns a dict with analysis results + recommended adjustments.
    """
    # Get the last week's steps (steps with day <= current_day, last 7)
    past_steps = [s for s in curriculum if s.get("day", 0) <= current_day]
    last_week = past_steps[-7:] if len(past_steps) >= 7 else past_steps

    if not last_week:
        return {"adjustment": "none", "reason": "no_data"}

    completed = [s for s in last_week if s.get("completed")]
    completion_rate = len(completed) / len(last_week) if last_week else 0

    # Performance distribution
    fast_count = sum(1 for s in last_week if s.get("performance") == "fast")
    slow_count = sum(1 for s in last_week if s.get("performance") == "slow")
    abandoned_count = sum(1 for s in last_week if s.get("performance") == "abandoned")

    # Average difficulty of completed steps
    difficulties = [s.get("difficulty", 1) for s in completed]
    avg_difficulty = sum(difficulties) / len(difficulties) if difficulties else 1

    # Average actual vs expected duration
    duration_ratios = []
    for s in completed:
        actual = s.get("actual_duration", 0)
        expected_mid = (s.get("duration_min", 5) + s.get("duration_max", 10)) / 2
        if actual > 0 and expected_mid > 0:
            duration_ratios.append(actual / expected_mid)
    avg_duration_ratio = sum(duration_ratios) / len(duration_ratios) if duration_ratios else 1.0

    # Decision logic
    analysis = {
        "completion_rate": round(completion_rate, 2),
        "avg_difficulty": round(avg_difficulty, 1),
        "avg_duration_ratio": round(avg_duration_ratio, 2),
        "fast_count": fast_count,
        "slow_count": slow_count,
        "abandoned_count": abandoned_count,
        "steps_analyzed": len(last_week),
    }

    # Determine adjustment (order matters — check problems first, then improvements)
    if completion_rate < 0.5 or abandoned_count >= 3:
        # Struggling — decrease difficulty, add more reviews
        analysis["adjustment"] = "decrease"
        analysis["difficulty_delta"] = -1
        analysis["reason"] = "low_completion_high_abandonment"
        analysis["coach_note"] = (
            "L'utilisateur a des difficultes. Reduis la difficulte, "
            "propose des sessions plus courtes et plus de revisions."
        )
    elif slow_count >= 3:
        # Sessions take too long — simplify
        analysis["adjustment"] = "simplify"
        analysis["difficulty_delta"] = 0
        analysis["reason"] = "sessions_too_long"
        analysis["coach_note"] = (
            "Les sessions prennent trop de temps. Reduis le contenu "
            "par session et propose des micro-objectifs plus cibles."
        )
    elif completion_rate >= 0.85 and fast_count >= 3:
        # User is crushing it — increase difficulty
        analysis["adjustment"] = "increase"
        analysis["difficulty_delta"] = 1
        analysis["reason"] = "high_completion_fast_pace"
        analysis["coach_note"] = (
            "L'utilisateur complete rapidement et facilement. "
            "Augmente la difficulte et propose des exercices plus ambitieux."
        )
    elif completion_rate >= 0.7 and avg_duration_ratio <= 1.1:
        # Good pace, slight increase
        analysis["adjustment"] = "slight_increase"
        analysis["difficulty_delta"] = 0
        analysis["reason"] = "good_pace"
        analysis["coach_note"] = (
            "Bon rythme. Maintiens la difficulte actuelle avec "
            "quelques exercices legerement plus avances."
        )
    else:
        # Maintain current pace
        analysis["adjustment"] = "maintain"
        analysis["difficulty_delta"] = 0
        analysis["reason"] = "stable"
        analysis["coach_note"] = "Rythme stable. Continue avec la progression prevue."

    return analysis


async def generate_adaptive_week(
    objective: dict,
    user: dict,
    week_number: int,
    performance_analysis: dict,
) -> list:
    """Generate next week's curriculum adapted to user's performance.

    Uses performance_analysis from analyze_week_performance() to calibrate
    difficulty, review frequency, and session complexity.

    Args:
        objective: full objective document
        user: user document
        week_number: 1-indexed week number to generate
        performance_analysis: output of analyze_week_performance()

    Returns:
        list of step dicts for the next 7 days
    """
    total_days = objective.get("target_duration_days", 30)
    daily_minutes = objective.get("daily_minutes", 10)
    title = objective.get("title", "Objectif")
    description = objective.get("description", "")
    category = objective.get("category", "learning")
    curriculum = objective.get("curriculum", [])

    start_day = (week_number - 1) * 7 + 1
    end_day = min(start_day + 6, total_days)
    if start_day > total_days:
        return []

    # User context
    profile = user.get("user_profile", {}) or {}
    energy = profile.get("energy_level", "medium")
    user_name = user.get("name", "l'utilisateur")

    # Performance-based adjustments
    adjustment = performance_analysis.get("adjustment", "maintain")
    coach_note = performance_analysis.get("coach_note", "")
    avg_difficulty = performance_analysis.get("avg_difficulty", 1)
    difficulty_delta = performance_analysis.get("difficulty_delta", 0)
    target_difficulty = max(1, min(5, round(avg_difficulty + difficulty_delta)))
    completion_rate = performance_analysis.get("completion_rate", 0.7)

    # Review frequency based on performance
    if adjustment == "decrease":
        review_instruction = "Integre 3 sessions de revision cette semaine (revision des fondamentaux)."
        duration_adjust = "Reduis la duree de chaque session de 20%."
    elif adjustment == "increase":
        review_instruction = "1 seule session de revision, les autres doivent etre stimulantes et nouvelles."
        duration_adjust = ""
    else:
        review_instruction = "Integre 1-2 sessions de revision."
        duration_adjust = ""

    # Inject category expertise
    category_expertise = get_category_expertise(category, max_fragments=3)

    # Build context from last completed steps
    completed_steps = [s for s in curriculum if s.get("completed")][-5:]
    prev_context = ""
    if completed_steps:
        prev_context = "\n\nDernieres sessions completees par l'utilisateur :\n" + "\n".join(
            f"- Jour {s['day']}: {s.get('title', '')} (difficulte {s.get('difficulty', 1)}, "
            f"perf: {s.get('performance', 'normal')})"
            for s in completed_steps
        )

    system_prompt = f"""Tu es Kira, experte pedagogique d'InFinea. Tu concois des parcours d'apprentissage ADAPTATIFS.

ANALYSE DE LA SEMAINE PRECEDENTE:
- Taux de completion: {round(completion_rate * 100)}%
- Ajustement: {adjustment}
- {coach_note}

CALIBRATION POUR CETTE SEMAINE:
- Difficulte cible: {target_difficulty}/5
- {review_instruction}
- {duration_adjust}

{category_expertise}

Regles :
- Adapte la difficulte au niveau {target_difficulty}/5
- Sessions de {max(2, daily_minutes - 3)} a {daily_minutes + 2} minutes
- Sois concret et actionnable
- Integre la repetition espacee sur les concepts des semaines precedentes
- Adapte au niveau d'energie : {energy}
- Reponds UNIQUEMENT en JSON valide, sans markdown"""

    prompt = f"""Objectif de {user_name} : "{title}"
{f'Description : {description}' if description else ''}
Categorie : {category}
Duree totale : {total_days} jours
{prev_context}

Genere les sessions ADAPTEES pour les jours {start_day} a {end_day} (semaine {week_number}).

Reponds avec un JSON array. Chaque element :
{{
  "day": {start_day},
  "title": "Titre court et accrocheur",
  "description": "Ce que l'utilisateur va faire (2-3 phrases adaptees a son niveau)",
  "focus": "Competence ou concept travaille",
  "instructions": ["Etape 1", "Etape 2", "Etape 3"],
  "duration_min": {max(2, daily_minutes - 3)},
  "duration_max": {daily_minutes + 2},
  "difficulty": {target_difficulty},
  "review": false,
  "tip": "Conseil pratique adapte"
}}"""

    try:
        text = await call_llm(
            system_prompt=system_prompt,
            user_prompt=prompt,
            model=get_model_for_user(user),
            max_tokens=2000,
            caller="curriculum_adaptive",
            user_id=user.get("user_id"),
        )

        if text:
            steps = _parse_curriculum_json(text)
            if steps:
                step_offset = len(curriculum)
                for i, step in enumerate(steps):
                    step["step_index"] = step_offset + i
                    step["completed"] = False
                    step["adaptive"] = True
                    step["week_adjustment"] = adjustment
                    step.setdefault("day", start_day + i)
                    step.setdefault("difficulty", target_difficulty)
                    step.setdefault("review", False)
                    step.setdefault("duration_min", max(2, daily_minutes - 3))
                    step.setdefault("duration_max", daily_minutes + 2)
                return steps

    except Exception as e:
        logger.error(f"Adaptive curriculum error (week {week_number}): {e}")

    # Fallback: generate basic steps with adjusted difficulty
    fallback_steps = []
    for d in range(start_day, end_day + 1):
        step = _make_fallback_step(objective, d, len(curriculum) + len(fallback_steps))
        step["difficulty"] = target_difficulty
        step["adaptive"] = True
        step["week_adjustment"] = adjustment
        fallback_steps.append(step)
    return fallback_steps
