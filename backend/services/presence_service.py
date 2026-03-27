"""
InFinea — Presence Service.
Centralizes online/offline status logic for profiles, feed, and messaging.

Architecture: Passive presence via `last_active` field (no WebSocket).
Users are considered "online" if active within 5 minutes — same threshold
as Instagram, Discord, and WhatsApp Web.

Benchmarked against:
- Discord: green dot (online), amber moon (idle), gray (offline)
- Instagram: "Active now", "Active Xh ago"
- WhatsApp: "online", "last seen today at HH:MM"

Thresholds:
- Online: < 5 min
- Recently active: 5–60 min
- Away: 1–24 hours
- Offline: > 24 hours (no indicator shown)
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from database import db

logger = logging.getLogger(__name__)

# Thresholds (minutes)
ONLINE_THRESHOLD = 5
RECENT_THRESHOLD = 60
AWAY_THRESHOLD = 1440  # 24 hours


def compute_presence(last_active: Optional[str]) -> dict:
    """
    Compute presence status from a last_active ISO timestamp.

    Returns:
        {
            "status": "online" | "recent" | "away" | "offline",
            "label": "En ligne" | "Actif il y a X min" | "Actif il y a Xh" | None,
            "minutes_ago": int | None,
        }
    """
    if not last_active:
        return {"status": "offline", "label": None, "minutes_ago": None}

    try:
        ts = datetime.fromisoformat(last_active.replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        diff = datetime.now(timezone.utc) - ts
        minutes = int(diff.total_seconds() / 60)
    except (ValueError, AttributeError):
        return {"status": "offline", "label": None, "minutes_ago": None}

    if minutes < ONLINE_THRESHOLD:
        return {"status": "online", "label": "En ligne", "minutes_ago": minutes}
    elif minutes < RECENT_THRESHOLD:
        return {"status": "recent", "label": f"Actif il y a {minutes} min", "minutes_ago": minutes}
    elif minutes < AWAY_THRESHOLD:
        hours = minutes // 60
        return {"status": "away", "label": f"Actif il y a {hours}h", "minutes_ago": minutes}
    else:
        return {"status": "offline", "label": None, "minutes_ago": minutes}


async def get_presence_batch(user_ids: list[str]) -> dict:
    """
    Get presence status for a batch of users.

    Args:
        user_ids: List of user IDs.

    Returns:
        Dict mapping user_id → presence dict.
    """
    if not user_ids:
        return {}

    users = await db.users.find(
        {"user_id": {"$in": user_ids}},
        {"_id": 0, "user_id": 1, "last_active": 1,
         "privacy": 1},
    ).to_list(len(user_ids))

    result = {}
    for u in users:
        # Respect privacy: if user hides activity status, show offline
        privacy = u.get("privacy", {})
        if privacy.get("show_activity_status") is False:
            result[u["user_id"]] = {"status": "offline", "label": None, "minutes_ago": None}
        else:
            result[u["user_id"]] = compute_presence(u.get("last_active"))

    # Fill missing users as offline
    for uid in user_ids:
        if uid not in result:
            result[uid] = {"status": "offline", "label": None, "minutes_ago": None}

    return result
