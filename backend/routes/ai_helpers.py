"""InFinea — Shared helpers for AI routes."""

from datetime import datetime, timezone, timedelta
from typing import Dict

from database import db


async def _build_micro_instants_context(user_id: str) -> str:
    """Aggregate micro-instant stats into a concise context paragraph for the AI coach."""
    now = datetime.now(timezone.utc)
    thirty_days_ago = (now - timedelta(days=30)).isoformat()
    seven_days_ago = (now - timedelta(days=7)).isoformat()
    fourteen_days_ago = (now - timedelta(days=14)).isoformat()

    outcomes = await db.micro_instant_outcomes.find(
        {"user_id": user_id, "recorded_at": {"$gte": thirty_days_ago}},
        {"_id": 0, "outcome": 1, "recorded_at": 1, "duration": 1, "source": 1},
    ).to_list(500)

    if not outcomes:
        return ""

    total = len(outcomes)
    exploited = [o for o in outcomes if o.get("outcome") == "exploited"]
    skipped = len([o for o in outcomes if o.get("outcome") == "skipped"])
    exploitation_rate = len(exploited) / total if total > 0 else 0.0
    total_minutes = sum(o.get("duration", 0) for o in exploited)

    this_week = [o for o in outcomes if o.get("recorded_at", "") >= seven_days_ago]
    last_week = [o for o in outcomes
                 if fourteen_days_ago <= o.get("recorded_at", "") < seven_days_ago]
    this_week_exploited = len([o for o in this_week if o.get("outcome") == "exploited"])
    this_week_rate = this_week_exploited / len(this_week) if this_week else 0.0
    last_week_rate = (
        len([o for o in last_week if o.get("outcome") == "exploited"]) / len(last_week)
        if last_week else 0.0
    )
    trend_pct = round((this_week_rate - last_week_rate) * 100)

    hourly: Dict[int, Dict[str, int]] = {}
    for o in exploited:
        try:
            dt = datetime.fromisoformat(o["recorded_at"].replace("Z", "+00:00"))
            h = dt.hour
            hourly.setdefault(h, {"exploited": 0, "total": 0})
            hourly[h]["exploited"] += 1
        except (ValueError, TypeError, KeyError):
            continue
    for o in outcomes:
        try:
            dt = datetime.fromisoformat(o["recorded_at"].replace("Z", "+00:00"))
            h = dt.hour
            hourly.setdefault(h, {"exploited": 0, "total": 0})
            hourly[h]["total"] += 1
        except (ValueError, TypeError, KeyError):
            continue

    best_hours = sorted(
        [(h, d["exploited"] / d["total"] if d["total"] >= 2 else 0.0, d["total"])
         for h, d in hourly.items() if d["total"] >= 2],
        key=lambda x: (x[1], x[2]),
        reverse=True,
    )[:3]

    best_slots_str = ", ".join(
        f"{h:02d}h-{h+1:02d}h ({round(rate*100)}%)"
        for h, rate, _ in best_hours
    ) if best_hours else "pas encore assez de données"

    sources = {"calendar_gap": 0, "routine_window": 0, "behavioral_pattern": 0}
    for o in outcomes:
        src = o.get("source", "")
        if src in sources:
            sources[src] += 1
    dominant_source = max(sources, key=sources.get) if any(sources.values()) else None
    source_labels = {
        "calendar_gap": "ton agenda",
        "routine_window": "tes routines",
        "behavioral_pattern": "tes habitudes comportementales",
    }

    trend_str = f"+{trend_pct}%" if trend_pct > 0 else f"{trend_pct}%"
    trend_label = "en progression" if trend_pct > 0 else ("stable" if trend_pct == 0 else "en baisse")

    ctx = f"""Micro-instants (30 derniers jours):
- {total} instants détectés, {len(exploited)} exploités, {skipped} skippés (taux d'exploitation: {round(exploitation_rate*100)}%)
- Tendance hebdo: {trend_str} vs semaine précédente ({trend_label})
- Meilleurs créneaux: {best_slots_str}
- {total_minutes} minutes investies via micro-instants cette semaine: {this_week_exploited} exploités sur {len(this_week)} détectés"""

    if dominant_source and sources[dominant_source] > 0:
        ctx += f"\n- Source principale des instants: {source_labels.get(dominant_source, dominant_source)}"

    return ctx
