"""
InFinea — Deep User Model.

Builds rich user context for AI prompts by combining profile data with
behavioral features, objectives, and session history.

Replaces the shallow build_user_context() in helpers.py which only
injected: name, goals, energy, streak, time_invested, tier.

This module reads user_features (computed every 6h, cached in Redis)
and formats them into a structured text that gives the AI genuine
understanding of the user's patterns, strengths, and weaknesses.
"""

import json
import logging
from typing import Optional

logger = logging.getLogger("infinea")


async def build_deep_context(
    db,
    user: dict,
    endpoint: str = "default",
    include_behavioral: bool = True,
    include_objectives: bool = True,
    include_social: bool = False,
) -> dict:
    """Build comprehensive user context for AI prompts.

    Reads from user doc + user_features (Redis/MongoDB). Returns a dict
    with pre-formatted text sections ready for prompt injection.

    Args:
        db: MongoDB database instance.
        user: Full user document.
        endpoint: Which endpoint is calling (controls what data to include).
        include_behavioral: Include behavioral feature analysis.
        include_objectives: Include active objectives and progress.
        include_social: Include social engagement metrics.

    Returns:
        dict with:
        - profile_text: User identity and preferences (~100 tok)
        - behavioral_text: Patterns and trends (~200 tok)
        - journey_text: Objectives and progress (~150 tok)
        - social_text: Social engagement (~50 tok)
        - coaching_signals: Raw data dict for coaching_engine
        - full_text: All sections combined
    """
    user_id = user.get("user_id", "")

    # Build profile text (always included)
    profile_text = _build_profile_text(user)

    # Build behavioral text from user_features
    behavioral_text = ""
    features = {}
    if include_behavioral:
        features = await _get_user_features(db, user_id)
        if features:
            behavioral_text = _build_behavioral_text(features)

    # Build journey text from objectives
    journey_text = ""
    if include_objectives:
        journey_text = await _build_journey_text(db, user_id)

    # Build social text
    social_text = ""
    if include_social:
        social_text = await _build_social_text(db, user_id)

    # Combine all sections
    sections = [s for s in [profile_text, behavioral_text, journey_text, social_text] if s]
    full_text = "\n\n".join(sections)

    return {
        "profile_text": profile_text,
        "behavioral_text": behavioral_text,
        "journey_text": journey_text,
        "social_text": social_text,
        "full_text": full_text,
        "coaching_signals": {
            "total_sessions": features.get("total_sessions", 0),
            "total_completed": features.get("total_completed", 0),
            "consistency_index": features.get("consistency_index", 0),
            "engagement_trend": features.get("engagement_trend", 0),
            "active_days_last_30": features.get("active_days_last_30", 0),
            "streak_days": user.get("streak_days", 0),
            "abandonment_rate": features.get("abandonment_rate", 0),
            "session_momentum": features.get("session_momentum", 0),
        },
    }


def _build_profile_text(user: dict) -> str:
    """Build user profile section from user document."""
    profile = user.get("user_profile") or {}

    name = user.get("name") or user.get("display_name", "Utilisateur")
    streak = user.get("streak_days", 0)
    total_time = user.get("total_time_invested", 0)
    tier = user.get("subscription_tier", "free")

    # Goals
    goals_map = {
        "learning": "apprentissage",
        "productivity": "productivite",
        "well_being": "bien-etre",
    }
    goals = profile.get("goals", [])
    goals_str = ", ".join(goals_map.get(g, g) for g in goals) if goals else "non definis"

    # Interests
    interests = profile.get("interests", [])
    if isinstance(interests, dict):
        interests_str = json.dumps(interests, ensure_ascii=False)
    elif isinstance(interests, list):
        interests_str = ", ".join(interests) if interests else "non definis"
    else:
        interests_str = str(interests) if interests else "non definis"

    # Preferred times and energy
    times = profile.get("preferred_times", profile.get("availability_slots", []))
    times_str = ", ".join(times) if times else "non definis"
    energy = profile.get("energy_level", profile.get("energy_high", "medium"))

    lines = [
        "PROFIL UTILISATEUR:",
        f"- Nom: {name}",
        f"- Objectifs: {goals_str}",
        f"- Interets: {interests_str}",
        f"- Creneaux preferes: {times_str}",
        f"- Niveau d'energie: {energy}",
        f"- Streak actuel: {streak} jours",
        f"- Temps total investi: {total_time} minutes",
        f"- Abonnement: {tier}",
    ]
    return "\n".join(lines)


async def _get_user_features(db, user_id: str) -> dict:
    """Fetch user_features from Redis cache, fallback to MongoDB."""
    try:
        # Try Redis cache first
        from services.cache import cache_get
        cached = await cache_get(f"user_features:{user_id}")
        if cached:
            return cached
    except Exception:
        pass

    try:
        doc = await db.user_features.find_one({"user_id": user_id}, {"_id": 0})
        return doc or {}
    except Exception:
        return {}


def _build_behavioral_text(features: dict) -> str:
    """Build behavioral analysis text from computed features.

    This is the KEY innovation: these 15 features are computed every 6h
    by feature_calculator.py but were NEVER injected into AI prompts.
    """
    lines = ["PROFIL COMPORTEMENTAL:"]

    # Completion rate
    cr = features.get("completion_rate_global")
    if cr is not None:
        pct = round(cr * 100)
        if pct >= 80:
            lines.append(f"- Taux de completion: {pct}% (excellent)")
        elif pct >= 60:
            lines.append(f"- Taux de completion: {pct}% (bon)")
        elif pct >= 40:
            lines.append(f"- Taux de completion: {pct}% (a ameliorer — proposer des actions plus courtes)")
        else:
            lines.append(f"- Taux de completion: {pct}% (faible — privilegier des micro-actions de 3-5 min)")

    # Category strengths/weaknesses
    cr_by_cat = features.get("completion_rate_by_category", {})
    if cr_by_cat:
        cat_map = {"learning": "apprentissage", "productivity": "productivite", "well_being": "bien-etre"}
        sorted_cats = sorted(cr_by_cat.items(), key=lambda x: x[1], reverse=True)
        strengths = [f"{cat_map.get(c, c)} ({round(r*100)}%)" for c, r in sorted_cats if r >= 0.6]
        weaknesses = [f"{cat_map.get(c, c)} ({round(r*100)}%)" for c, r in sorted_cats if r < 0.4]
        if strengths:
            lines.append(f"- Points forts: {', '.join(strengths[:3])}")
        if weaknesses:
            lines.append(f"- Points faibles: {', '.join(weaknesses[:2])}")

    # Engagement trend
    trend = features.get("engagement_trend", 0)
    if trend > 0.05:
        lines.append(f"- Tendance: en progression (+{round(trend*100)}% cette semaine)")
    elif trend < -0.05:
        lines.append(f"- Tendance: en baisse ({round(trend*100)}% cette semaine)")
    else:
        lines.append("- Tendance: stable")

    # Consistency
    consistency = features.get("consistency_index", 0)
    active_days = features.get("active_days_last_30", 0)
    lines.append(f"- Regularite: {round(consistency*100)}% ({active_days} jours actifs sur 30)")

    # Session momentum
    momentum = features.get("session_momentum", 0)
    if momentum >= 5:
        lines.append(f"- Momentum: {momentum} sessions consecutives (excellent rythme)")
    elif momentum >= 3:
        lines.append(f"- Momentum: {momentum} sessions consecutives (bon rythme)")

    # Preferred duration
    pref_duration = features.get("preferred_action_duration")
    if pref_duration:
        lines.append(f"- Duree preferee: {round(pref_duration)} min")

    # Best time slots
    best_buckets = features.get("best_performing_buckets", [])
    if best_buckets:
        bucket_map = {
            "morning": "matin", "afternoon": "apres-midi",
            "evening": "soir", "night": "nuit",
        }
        translated = [bucket_map.get(b, b) for b in best_buckets[:3]]
        lines.append(f"- Meilleurs creneaux: {', '.join(translated)}")

    # Category fatigue
    fatigue = features.get("category_fatigue", {})
    if fatigue:
        cat_map = {"learning": "apprentissage", "productivity": "productivite", "well_being": "bien-etre"}
        fatigued = [cat_map.get(c, c) for c, delta in fatigue.items() if delta > 0.15]
        if fatigued:
            lines.append(f"- Fatigue detectee en: {', '.join(fatigued)} (varier les categories)")

    # Abandonment rate
    abandon = features.get("abandonment_rate", 0)
    if abandon and abandon > 0.3:
        lines.append(f"- Taux d'abandon: {round(abandon*100)}% (eleve — proposer des actions plus courtes et faciles)")

    # Learning velocity (Phase 2)
    velocity = features.get("learning_velocity", {})
    if velocity:
        fast = [f"{k}" for k, v in velocity.items() if v > 1.2]
        slow = [f"{k}" for k, v in velocity.items() if v < 0.7]
        if fast:
            lines.append(f"- Progression rapide sur: {', '.join(fast[:2])}")
        if slow:
            lines.append(f"- Progression lente sur: {', '.join(slow[:2])} (adapter le rythme)")

    # Difficulty calibration (Phase 2)
    diff_cal = features.get("difficulty_calibration", {})
    optimal = diff_cal.get("optimal_zone", [])
    if optimal and diff_cal.get("completion_by_difficulty"):
        lines.append(f"- Zone de difficulte optimale: niveau {'-'.join(str(d) for d in optimal)}")

    # Coaching stage (Phase 2)
    stage = features.get("coaching_stage", "")
    stage_labels = {
        "precontemplation": "decouverte",
        "contemplation": "exploration",
        "preparation": "construction",
        "action": "action",
        "maintenance": "maitrise",
    }
    if stage and stage in stage_labels:
        lines.append(f"- Stade de coaching: {stage_labels[stage]}")

    return "\n".join(lines)


async def _build_journey_text(db, user_id: str) -> str:
    """Build learning journey text from active objectives."""
    try:
        objectives = await db.objectives.find(
            {"user_id": user_id, "status": "active"},
            {"_id": 0, "title": 1, "current_day": 1, "target_duration_days": 1,
             "progress_log": {"$slice": -1}},
        ).to_list(5)

        if not objectives:
            return ""

        lines = ["PARCOURS D'APPRENTISSAGE:"]
        for obj in objectives:
            title = obj.get("title", "Sans titre")
            current = obj.get("current_day", 0)
            target = obj.get("target_duration_days", 30)
            pct = min(round(current / target * 100), 100) if target else 0
            line = f"- {title}: jour {current}/{target} ({pct}%)"

            # Last progress note
            progress_log = obj.get("progress_log", [])
            if progress_log:
                last_entry = progress_log[-1]
                notes = last_entry.get("notes") or last_entry.get("focus", "")
                if notes:
                    line += f" — dernier focus: {notes[:60]}"

            lines.append(line)

        return "\n".join(lines)
    except Exception as e:
        logger.debug(f"Error building journey text: {e}")
        return ""


async def _build_social_text(db, user_id: str) -> str:
    """Build social engagement text."""
    try:
        followers = await db.follows.count_documents({"following_id": user_id, "status": "accepted"})
        following = await db.follows.count_documents({"follower_id": user_id, "status": "accepted"})

        if followers == 0 and following == 0:
            return ""

        lines = ["ENGAGEMENT SOCIAL:"]
        lines.append(f"- Abonnes: {followers}, Abonnements: {following}")

        return "\n".join(lines)
    except Exception:
        return ""


# ── Backward Compatibility ──

async def build_user_context_legacy(user: dict) -> str:
    """Legacy wrapper matching the old build_user_context() signature.
    Returns a simple formatted string instead of the rich dict.
    Used during migration — will be removed once all endpoints use build_deep_context().
    """
    return _build_profile_text(user)
