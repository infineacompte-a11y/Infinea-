"""
InFinea — Contextual Message Composer (F.3 Push Contextuel Intelligent).
Generates contextual notification content for micro-instant push notifications.

Pure template engine — no DB access, no async. Takes a micro-instant dict
from predict_micro_instants() and produces a Web Push payload with
tone-adapted French copy.

Tone benchmarks: Duolingo smart reminders + Calm adaptive notifications.
"""

import random
from typing import Dict, Optional


# ═══════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════

MAX_TITLE_CHARS = 50
MAX_BODY_CHARS = 120
DEFAULT_MAX_DAILY_PUSHES = 3

# Icons by action type
ICON_MAP = {
    "spaced_repetition": "brain",
    "micro_action": "zap",
    "routine": "target",
    "calendar_gap": "clock",
    "default": "book",
}


# ═══════════════════════════════════════════════════════════════════
# Templates — source × time_bucket → list of (title, body) variants
# Variables: {duration}, {action_title}, {action_category},
#            {routine_name}, {skill_name}
# ═══════════════════════════════════════════════════════════════════

TEMPLATES: Dict[str, Dict[str, list]] = {
    # ── Calendar gap ──
    "calendar_gap": {
        "morning": [
            (
                "⏳ {duration} min avant ta réunion",
                "Un créneau idéal pour {action_title}. C'est le moment !",
            ),
            (
                "☀️ {duration} min libres ce matin",
                "Entre deux rendez-vous, avance sur {action_title}.",
            ),
            (
                "📅 Créneau de {duration} min détecté",
                "Profite de ce moment calme pour progresser.",
            ),
        ],
        "afternoon": [
            (
                "⏳ {duration} min avant ton prochain RDV",
                "Créneau parfait pour {action_title} — vite fait, bien fait.",
            ),
            (
                "📅 {duration} min libres cet après-midi",
                "Entre deux réunions, avance sur {action_title}.",
            ),
        ],
        "evening": [
            (
                "🌙 {duration} min de libre ce soir",
                "Un petit moment pour toi avant la fin de journée.",
            ),
            (
                "✨ Créneau de {duration} min détecté",
                "Profite de ce créneau pour {action_title}.",
            ),
        ],
        "night": [
            (
                "🌙 {duration} min disponibles",
                "Un créneau s'est libéré — à toi de voir.",
            ),
        ],
    },

    # ── Routine window ──
    "routine_window": {
        "morning": [
            (
                "🎯 C'est l'heure de {routine_name}",
                "Ta routine du matin t'attend. {duration} min suffisent !",
            ),
            (
                "☀️ {routine_name} — c'est maintenant",
                "Lance ta routine matinale, {duration} min max.",
            ),
        ],
        "afternoon": [
            (
                "🎯 {routine_name} — c'est le moment",
                "Ta routine de l'après-midi est prête. {duration} min.",
            ),
            (
                "⚡ Routine prévue : {routine_name}",
                "Le bon moment pour {duration} min de pratique.",
            ),
        ],
        "evening": [
            (
                "🎯 {routine_name} ce soir",
                "Un petit moment pour ta routine du soir.",
            ),
            (
                "✨ C'est l'heure de {routine_name}",
                "Prends {duration} min pour ta routine — tu le mérites.",
            ),
        ],
        "night": [
            (
                "🎯 {routine_name} en attente",
                "Ta routine n'a pas encore été faite aujourd'hui.",
            ),
        ],
    },

    # ── Behavioral pattern ──
    "behavioral_pattern": {
        "morning": [
            (
                "💡 Tu es souvent actif à cette heure",
                "{duration} min pour {action_title} ? C'est ton créneau.",
            ),
            (
                "☀️ Ton moment productif du matin",
                "D'habitude tu en profites — {duration} min dispo.",
            ),
        ],
        "afternoon": [
            (
                "💡 C'est ton créneau habituel",
                "Tu es souvent productif maintenant. {duration} min ?",
            ),
            (
                "⚡ {duration} min — ton rythme le dit",
                "Tu pratiques souvent à cette heure. On y va ?",
            ),
        ],
        "evening": [
            (
                "💡 Ton moment du soir",
                "Tu apprends souvent à cette heure. {duration} min ?",
            ),
            (
                "✨ Un petit moment pour progresser",
                "D'habitude tu en profites le soir — {duration} min.",
            ),
        ],
        "night": [
            (
                "💡 {duration} min disponibles",
                "Un créneau basé sur tes habitudes récentes.",
            ),
        ],
    },
}

# ── Spaced-repetition urgency overrides ──
SR_TEMPLATES: Dict[str, list] = {
    "morning": [
        (
            "🧠 Révision de {skill_name} à faire",
            "N'oublie pas ta révision ! {duration} min suffisent.",
        ),
        (
            "☀️ {skill_name} — révision du matin",
            "Ta mémoire est fraîche, c'est le moment idéal.",
        ),
    ],
    "afternoon": [
        (
            "🧠 Révise {skill_name} maintenant",
            "N'oublie pas ta révision de {skill_name} — {duration} min.",
        ),
        (
            "📖 Révision en attente : {skill_name}",
            "Un rappel espacé t'attend. {duration} min max.",
        ),
    ],
    "evening": [
        (
            "🧠 {skill_name} à réviser ce soir",
            "Quelques minutes avant de décrocher ?",
        ),
    ],
    "night": [
        (
            "🧠 Révision en retard : {skill_name}",
            "Ta révision est en attente depuis un moment.",
        ),
    ],
}

# High-urgency SR overrides (days_overdue >= 3)
SR_URGENT_TEMPLATES: Dict[str, list] = {
    "morning": [
        (
            "🔴 {skill_name} — révision urgente",
            "Ta révision a du retard. {duration} min ce matin ?",
        ),
    ],
    "afternoon": [
        (
            "🔴 Révision urgente : {skill_name}",
            "Ça fait plusieurs jours — {duration} min maintenant ?",
        ),
    ],
    "evening": [
        (
            "🔴 {skill_name} en retard",
            "N'attends pas demain — quelques minutes suffisent.",
        ),
    ],
    "night": [
        (
            "🔴 {skill_name} — révision en retard",
            "Ta révision attend depuis trop longtemps.",
        ),
    ],
}


# ═══════════════════════════════════════════════════════════════════
# Main composer
# ═══════════════════════════════════════════════════════════════════


def compose_instant_message(instant: dict) -> dict:
    """
    Generate contextual title + body for a micro-instant push notification.

    Args:
        instant: A micro-instant dict from predict_micro_instants() containing:
            - instant_id: str
            - window_start: ISO timestamp
            - window_end: ISO timestamp
            - duration_minutes: int
            - confidence_score: float
            - source: str ("calendar_gap" | "routine_window" | "behavioral_pattern")
            - recommended_action: dict or None
            - context: dict with time_bucket, energy_level, trigger, etc.

    Returns:
        dict with: title, body, icon, tag, url, actions (Web Push action buttons)
    """
    source = instant.get("source", "calendar_gap")
    context = instant.get("context", {})
    time_bucket = context.get("time_bucket", "afternoon")
    duration = instant.get("duration_minutes", 5)
    action = instant.get("recommended_action")
    confidence = instant.get("confidence_score", 0.5)
    instant_id = instant.get("instant_id", "unknown")

    # ── Build template variables ──
    variables = {
        "duration": str(duration),
        "action_title": "une micro-action",
        "action_category": "",
        "routine_name": context.get("routine_name", "ta routine"),
        "skill_name": "",
    }

    icon = ICON_MAP.get(source, ICON_MAP["default"])
    url = "/micro-instants"
    action_type = None

    if action:
        action_type = action.get("type")
        variables["action_title"] = action.get("title") or action.get("skill", "une micro-action")
        variables["action_category"] = action.get("category", "")
        variables["skill_name"] = action.get("skill", "")

        if action_type == "spaced_repetition":
            icon = ICON_MAP["spaced_repetition"]
            url = f"/session/start/{action.get('objective_id', '')}"
        elif action_type == "micro_action":
            icon = ICON_MAP["micro_action"]
            action_id = action.get("action_id", "")
            if action_id:
                url = f"/session/start/{action_id}"

    # ── Select template ──
    title_tpl, body_tpl = _select_template(
        source=source,
        time_bucket=time_bucket,
        action_type=action_type,
        confidence=confidence,
        days_overdue=action.get("days_overdue", 0) if action else 0,
    )

    # ── Render ──
    title = _render(title_tpl, variables)
    body = _render(body_tpl, variables)

    # ── Enforce length limits ──
    title = title[:MAX_TITLE_CHARS]
    body = body[:MAX_BODY_CHARS]

    # ── Action buttons ──
    if action:
        actions = [
            {"action": "start", "title": "C'est parti"},
            {"action": "skip", "title": "Pas maintenant"},
        ]
    else:
        actions = [
            {"action": "explore", "title": "Voir les options"},
            {"action": "skip", "title": "Ignorer"},
        ]

    return {
        "title": title,
        "body": body,
        "icon": icon,
        "tag": f"micro_instant_{instant_id}",
        "url": url,
        "actions": actions,
    }


# ═══════════════════════════════════════════════════════════════════
# Throttle summary
# ═══════════════════════════════════════════════════════════════════


def compose_throttle_summary(
    sent_today: int, max_daily: int = DEFAULT_MAX_DAILY_PUSHES
) -> Optional[dict]:
    """
    If user has had all daily pushes, return None. Otherwise return count context.

    Args:
        sent_today: Number of push notifications sent today.
        max_daily: Maximum daily push limit.

    Returns:
        dict with remaining count info, or None if quota exhausted.
    """
    if sent_today >= max_daily:
        return None

    remaining = max_daily - sent_today
    return {
        "sent_today": sent_today,
        "max_daily": max_daily,
        "remaining": remaining,
        "is_last": remaining == 1,
    }


# ═══════════════════════════════════════════════════════════════════
# Internal helpers
# ═══════════════════════════════════════════════════════════════════


def _select_template(
    source: str,
    time_bucket: str,
    action_type: Optional[str],
    confidence: float,
    days_overdue: int = 0,
) -> tuple:
    """
    Pick the right (title, body) template tuple based on context.

    Priority:
        1. SR urgent (days_overdue >= 3)
        2. SR normal
        3. Source × time_bucket standard templates
    """
    # SR overrides
    if action_type == "spaced_repetition":
        if days_overdue >= 3:
            pool = SR_URGENT_TEMPLATES.get(time_bucket, SR_URGENT_TEMPLATES["afternoon"])
        else:
            pool = SR_TEMPLATES.get(time_bucket, SR_TEMPLATES["afternoon"])
        return random.choice(pool)

    # Standard templates
    source_templates = TEMPLATES.get(source, TEMPLATES["calendar_gap"])
    pool = source_templates.get(time_bucket, source_templates.get("afternoon", []))

    if not pool:
        # Ultimate fallback
        pool = [("📱 {duration} min disponibles", "Un moment pour progresser.")]

    return random.choice(pool)


def _render(template: str, variables: Dict[str, str]) -> str:
    """
    Safe template rendering with fallback for missing keys.
    Uses str.format_map with a defaultdict-like approach to avoid KeyError.
    """
    try:
        return template.format_map(_SafeDict(variables))
    except (KeyError, ValueError, IndexError):
        return template


class _SafeDict(dict):
    """Dict subclass that returns the key placeholder for missing keys."""

    def __missing__(self, key: str) -> str:
        return f"{{{key}}}"
