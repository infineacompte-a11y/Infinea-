"""
InFinea — Weekly Summary Service.
Computes per-user weekly stats and sends branded digest emails.

Architecture:
- compute_user_weekly_stats(): aggregates sessions, XP, social, badges for one user.
- send_weekly_summaries(): iterates eligible users, computes stats, sends emails.
- Rich HTML template: Strava-level weekly recap with trends and social proof.
- Non-blocking, fail-safe — a failure for one user never blocks others.

Benchmarked: Strava Weekly Report, Duolingo Weekly Progress, Spotify Wrapped.
"""

import logging
from datetime import datetime, timezone, timedelta

from database import db
from services.email_service import send_email_to_user, APP_URL
from services.xp_engine import level_from_xp, xp_progress_in_level

logger = logging.getLogger(__name__)


async def compute_user_weekly_stats(user_id: str) -> dict:
    """Compute detailed weekly stats for a single user.

    Returns a rich dict with:
    - sessions (count, minutes, by_day, by_category) + comparison vs previous week
    - xp (gained, level, title, progress)
    - streak
    - social (new_followers, reactions_received, comments_received)
    - badges earned this week
    - leaderboard rank among friends
    """
    now = datetime.now(timezone.utc)
    week_start = now - timedelta(days=7)
    prev_week_start = now - timedelta(days=14)
    week_start_iso = week_start.isoformat()
    prev_week_start_iso = prev_week_start.isoformat()

    user = await db.users.find_one(
        {"user_id": user_id},
        {"_id": 0, "user_id": 1, "display_name": 1, "name": 1, "email": 1,
         "streak_days": 1, "total_xp": 1, "level": 1, "total_time_invested": 1,
         "total_sessions": 1},
    )
    if not user:
        return {}

    display_name = user.get("display_name") or user.get("name", "")

    # ── Sessions this week ──
    sessions_this_week = await db.sessions.find(
        {"user_id": user_id, "completed": True, "completed_at": {"$gte": week_start_iso}},
        {"_id": 0, "actual_duration": 1, "category": 1, "completed_at": 1},
    ).to_list(500)

    sessions_count = len(sessions_this_week)
    total_minutes = sum(s.get("actual_duration", 0) for s in sessions_this_week)

    # By category
    by_category = {}
    for s in sessions_this_week:
        cat = s.get("category", "mixed")
        by_category[cat] = by_category.get(cat, 0) + 1

    # By day (for the activity bar chart)
    by_day = {}
    for s in sessions_this_week:
        day = s.get("completed_at", "")[:10]
        by_day[day] = by_day.get(day, 0) + s.get("actual_duration", 0)

    # ── Previous week comparison (Strava trend arrows) ──
    prev_sessions = await db.sessions.count_documents({
        "user_id": user_id, "completed": True,
        "completed_at": {"$gte": prev_week_start_iso, "$lt": week_start_iso},
    })
    prev_minutes_agg = await db.sessions.aggregate([
        {"$match": {"user_id": user_id, "completed": True,
                     "completed_at": {"$gte": prev_week_start_iso, "$lt": week_start_iso}}},
        {"$group": {"_id": None, "total": {"$sum": "$actual_duration"}}},
    ]).to_list(1)
    prev_minutes = prev_minutes_agg[0]["total"] if prev_minutes_agg else 0

    # Trends: +X% or -X%
    sessions_trend = _compute_trend(sessions_count, prev_sessions)
    minutes_trend = _compute_trend(total_minutes, prev_minutes)

    # ── XP gained this week ──
    xp_entries = await db.xp_history.find(
        {"user_id": user_id, "created_at": {"$gte": week_start_iso}},
        {"_id": 0, "xp": 1},
    ).to_list(500)
    xp_gained = sum(e.get("xp", 0) for e in xp_entries)

    # Level info
    total_xp = user.get("total_xp", 0)
    level = user.get("level", 1)
    xp_info = xp_progress_in_level(total_xp)

    # ── Streak ──
    streak_days = user.get("streak_days", 0)

    # ── Social stats ──
    new_followers = await db.follows.count_documents({
        "following_id": user_id, "status": "active",
        "followed_at": {"$gte": week_start_iso},
    })

    # Reactions received on my activities this week
    my_activity_ids = await db.activities.find(
        {"user_id": user_id, "created_at": {"$gte": week_start_iso}},
        {"_id": 0, "activity_id": 1},
    ).to_list(500)
    my_act_ids = [a["activity_id"] for a in my_activity_ids]
    reactions_received = 0
    comments_received = 0
    if my_act_ids:
        reactions_received = await db.reactions.count_documents({
            "activity_id": {"$in": my_act_ids},
            "user_id": {"$ne": user_id},
        })
        comments_received = await db.comments.count_documents({
            "activity_id": {"$in": my_act_ids},
            "user_id": {"$ne": user_id},
        })

    # ── Badges earned this week ──
    user_doc = await db.users.find_one(
        {"user_id": user_id}, {"badges": 1}
    )
    badges = user_doc.get("badges", []) if user_doc else []
    new_badges = [
        b for b in badges
        if b.get("earned_at", "") >= week_start_iso
    ]

    # ── Top accomplishment (most impressive thing this week) ──
    top_accomplishment = _pick_top_accomplishment(
        sessions_count, total_minutes, streak_days,
        xp_gained, new_badges, new_followers,
    )

    return {
        "user_id": user_id,
        "display_name": display_name,
        "sessions": {
            "count": sessions_count,
            "minutes": total_minutes,
            "by_category": by_category,
            "by_day": by_day,
            "trend_sessions": sessions_trend,
            "trend_minutes": minutes_trend,
            "prev_count": prev_sessions,
            "prev_minutes": prev_minutes,
        },
        "xp": {
            "gained": xp_gained,
            "total": total_xp,
            "level": level,
            "title": xp_info.get("title", "Curieux"),
            "progress": xp_info.get("progress", 0),
        },
        "streak_days": streak_days,
        "social": {
            "new_followers": new_followers,
            "reactions_received": reactions_received,
            "comments_received": comments_received,
        },
        "new_badges": [{"name": b.get("name", ""), "icon": b.get("icon", "")} for b in new_badges],
        "top_accomplishment": top_accomplishment,
    }


def _compute_trend(current: int, previous: int) -> dict:
    """Compute trend percentage and direction."""
    if previous == 0:
        if current > 0:
            return {"direction": "up", "percent": 100, "label": "Nouveau !"}
        return {"direction": "flat", "percent": 0, "label": "—"}
    change = ((current - previous) / previous) * 100
    if change > 5:
        return {"direction": "up", "percent": round(change), "label": f"+{round(change)}%"}
    elif change < -5:
        return {"direction": "down", "percent": round(abs(change)), "label": f"-{round(abs(change))}%"}
    return {"direction": "flat", "percent": 0, "label": "Stable"}


def _pick_top_accomplishment(
    sessions: int, minutes: int, streak: int,
    xp: int, badges: list, followers: int,
) -> str:
    """Pick the single most impressive accomplishment of the week."""
    candidates = []
    if streak >= 7:
        candidates.append((streak * 3, f"Streak de {streak} jours maintenu"))
    if badges:
        candidates.append((50, f"Badge \"{badges[0]['name']}\" débloqué"))
    if sessions >= 10:
        candidates.append((40, f"{sessions} sessions complétées"))
    elif sessions >= 5:
        candidates.append((25, f"{sessions} sessions cette semaine"))
    if minutes >= 60:
        candidates.append((35, f"{minutes} minutes investies"))
    if xp >= 100:
        candidates.append((30, f"+{xp} XP gagnés"))
    if followers >= 3:
        candidates.append((20, f"{followers} nouveaux followers"))
    if not candidates:
        if sessions > 0:
            return f"{sessions} session{'s' if sessions > 1 else ''} — chaque pas compte !"
        return "Reviens cette semaine pour progresser !"
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


# ── Rich weekly email template ──

CATEGORY_LABELS = {
    "learning": "Apprentissage",
    "productivity": "Productivité",
    "well_being": "Bien-être",
    "creativity": "Créativité",
    "mixed": "Général",
}

CATEGORY_COLORS = {
    "learning": "#55B3AE",
    "productivity": "#E48C75",
    "well_being": "#5DB786",
    "creativity": "#9B59B6",
    "mixed": "#459492",
}


def render_weekly_summary_email(stats: dict) -> tuple:
    """Render a rich weekly summary email. Returns (subject, html).

    Design reference: Strava Weekly Report + Duolingo Progress Email.
    Table-based layout, inline CSS, compatible with all email clients.
    """
    s = stats["sessions"]
    xp = stats["xp"]
    social = stats["social"]
    name = stats["display_name"] or "là"

    # Subject line with key stat (Duolingo pattern: personalized, urgent)
    if s["count"] == 0:
        subject = f"{name}, ta progression t'attend — InFinea"
    elif s["count"] >= 5:
        subject = f"Semaine record ! {s['count']} sessions — InFinea"
    else:
        subject = f"Ton récap : {s['count']} sessions, +{xp['gained']} XP — InFinea"

    # ── Trend arrows ──
    def trend_html(trend):
        if trend["direction"] == "up":
            return f'<span style="color: #5DB786; font-weight: 600;">▲ {trend["label"]}</span>'
        elif trend["direction"] == "down":
            return f'<span style="color: #E48C75; font-weight: 600;">▼ {trend["label"]}</span>'
        return f'<span style="color: #9ca3af;">{trend["label"]}</span>'

    sessions_trend_html = trend_html(s["trend_sessions"])
    minutes_trend_html = trend_html(s["trend_minutes"])

    # ── Activity bar chart (7 days, CSS-only) ──
    by_day = s.get("by_day", {})
    now = datetime.now(timezone.utc)
    day_labels = ["L", "M", "M", "J", "V", "S", "D"]
    bars_html = ""
    max_min = max(by_day.values()) if by_day else 1
    for i in range(7):
        d = now - timedelta(days=6 - i)
        key = d.strftime("%Y-%m-%d")
        minutes_val = by_day.get(key, 0)
        height = max(4, int((minutes_val / max(max_min, 1)) * 40))
        color = "#459492" if minutes_val > 0 else "#e5e7eb"
        weekday_idx = d.weekday()  # 0=Monday
        label = day_labels[weekday_idx]
        bars_html += f"""
            <td style="vertical-align: bottom; text-align: center; padding: 0 3px;">
              <div style="width: 24px; height: {height}px; background: {color}; border-radius: 4px; margin: 0 auto;"></div>
              <div style="font-size: 9px; color: #9ca3af; margin-top: 4px;">{label}</div>
            </td>"""

    # ── Category breakdown ──
    by_cat = s.get("by_category", {})
    cat_html = ""
    for cat, count in sorted(by_cat.items(), key=lambda x: x[1], reverse=True)[:3]:
        label = CATEGORY_LABELS.get(cat, cat)
        color = CATEGORY_COLORS.get(cat, "#459492")
        cat_html += f"""
            <tr>
              <td style="padding: 4px 0;">
                <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: {color}; margin-right: 8px; vertical-align: middle;"></span>
                <span style="font-size: 13px; color: #374151;">{label}</span>
              </td>
              <td style="text-align: right; padding: 4px 0;">
                <span style="font-size: 13px; font-weight: 600; color: #374151;">{count} session{'s' if count > 1 else ''}</span>
              </td>
            </tr>"""

    # ── Badges earned ──
    badges_html = ""
    if stats["new_badges"]:
        badges_list = ", ".join(f'<strong>{b["name"]}</strong>' for b in stats["new_badges"][:3])
        badges_html = f"""
        <tr>
          <td style="padding: 20px 0 0 0;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background: #FEF3C7; border-radius: 12px; padding: 16px;">
              <tr><td style="padding: 12px 16px;">
                <span style="font-size: 16px; margin-right: 8px;">🏆</span>
                <span style="font-size: 13px; color: #92400E;">Badge{'s' if len(stats['new_badges']) > 1 else ''} débloqué{'s' if len(stats['new_badges']) > 1 else ''} : {badges_list}</span>
              </td></tr>
            </table>
          </td>
        </tr>"""

    # ── Social stats row ──
    social_html = ""
    social_items = []
    if social["new_followers"] > 0:
        social_items.append(f'{social["new_followers"]} nouveau{"x" if social["new_followers"] > 1 else ""} follower{"s" if social["new_followers"] > 1 else ""}')
    if social["reactions_received"] > 0:
        social_items.append(f'{social["reactions_received"]} réaction{"s" if social["reactions_received"] > 1 else ""}')
    if social["comments_received"] > 0:
        social_items.append(f'{social["comments_received"]} commentaire{"s" if social["comments_received"] > 1 else ""}')
    if social_items:
        social_text = " · ".join(social_items)
        social_html = f"""
        <tr>
          <td style="padding: 16px 0 0 0;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background: #EEF8F7; border-radius: 12px;">
              <tr><td style="padding: 12px 16px;">
                <span style="font-size: 13px; color: #459492; font-weight: 600;">Social</span>
                <span style="font-size: 13px; color: #374151; margin-left: 8px;">{social_text}</span>
              </td></tr>
            </table>
          </td>
        </tr>"""

    # ── XP progress bar ──
    xp_bar_width = max(4, int(xp["progress"] * 100))
    xp_html = f"""
    <tr>
      <td style="padding: 20px 0 0 0;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
          <tr>
            <td style="font-size: 13px; color: #374151;">
              <strong style="color: #F5A623;">Niv. {xp['level']}</strong> — {xp['title']}
            </td>
            <td style="text-align: right; font-size: 12px; color: #9ca3af;">
              +{xp['gained']} XP cette semaine
            </td>
          </tr>
          <tr>
            <td colspan="2" style="padding-top: 8px;">
              <div style="width: 100%; height: 8px; background: #e5e7eb; border-radius: 4px; overflow: hidden;">
                <div style="width: {xp_bar_width}%; height: 100%; background: linear-gradient(90deg, #F5A623, #E48C75); border-radius: 4px;"></div>
              </div>
            </td>
          </tr>
        </table>
      </td>
    </tr>"""

    # ── Inactive user variant (0 sessions) ──
    if s["count"] == 0:
        body_content = f"""
        <tr>
          <td>
            <h1 style="margin: 0 0 12px; font-size: 20px; font-weight: 700; color: #275255;">
              {name}, tu nous manques !
            </h1>
            <p style="margin: 0 0 20px; font-size: 15px; color: #374151; line-height: 1.6;">
              Pas de session cette semaine — mais chaque jour est une nouvelle chance.
              {'Ta série de ' + str(stats['streak_days']) + ' jours attend ton retour !' if stats['streak_days'] > 0 else 'Une micro-session de 5 min suffit pour relancer ta progression.'}
            </p>
          </td>
        </tr>
        {xp_html}"""
    else:
        body_content = f"""
        <tr>
          <td>
            <h1 style="margin: 0 0 8px; font-size: 20px; font-weight: 700; color: #275255;">
              Bravo {name} !
            </h1>
            <p style="margin: 0 0 4px; font-size: 14px; color: #6b7280;">Ta semaine en un coup d'œil</p>
          </td>
        </tr>
        <!-- Top accomplishment banner -->
        <tr>
          <td style="padding: 12px 0 20px;">
            <div style="background: linear-gradient(135deg, #275255, #459492); border-radius: 12px; padding: 14px 18px; color: white;">
              <span style="font-size: 14px; font-weight: 600;">⭐ {stats['top_accomplishment']}</span>
            </div>
          </td>
        </tr>
        <!-- Key stats: 3-column grid -->
        <tr>
          <td>
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td style="width: 33%; text-align: center; padding: 12px 4px; background: #f9fafb; border-radius: 12px 0 0 12px;">
                  <div style="font-size: 24px; font-weight: 700; color: #459492;">{s['count']}</div>
                  <div style="font-size: 11px; color: #6b7280; margin-top: 2px;">sessions</div>
                  <div style="font-size: 10px; margin-top: 4px;">{sessions_trend_html}</div>
                </td>
                <td style="width: 33%; text-align: center; padding: 12px 4px; background: #f9fafb;">
                  <div style="font-size: 24px; font-weight: 700; color: #E48C75;">{s['minutes']}</div>
                  <div style="font-size: 11px; color: #6b7280; margin-top: 2px;">minutes</div>
                  <div style="font-size: 10px; margin-top: 4px;">{minutes_trend_html}</div>
                </td>
                <td style="width: 33%; text-align: center; padding: 12px 4px; background: #f9fafb; border-radius: 0 12px 12px 0;">
                  <div style="font-size: 24px; font-weight: 700; color: #F5A623;">{stats['streak_days']}</div>
                  <div style="font-size: 11px; color: #6b7280; margin-top: 2px;">streak</div>
                  <div style="font-size: 10px; color: #9ca3af;">jours</div>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <!-- Weekly activity chart -->
        <tr>
          <td style="padding: 20px 0;">
            <div style="font-size: 11px; color: #9ca3af; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">Activité cette semaine</div>
            <table role="presentation" cellpadding="0" cellspacing="0" style="margin: 0 auto;">
              <tr>{bars_html}</tr>
            </table>
          </td>
        </tr>
        <!-- Category breakdown -->
        {'<tr><td><table role="presentation" width="100%" cellpadding="0" cellspacing="0">' + cat_html + '</table></td></tr>' if cat_html else ''}
        {xp_html}
        {badges_html}
        {social_html}"""

    # ── CTA ──
    cta_text = "Faire ma session" if s["count"] == 0 else "Continuer ma progression"
    cta_url = f"{APP_URL}/today" if s["count"] == 0 else f"{APP_URL}/dashboard"

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin: 0; padding: 0; background-color: #f4f4f5; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color: #f4f4f5;">
    <tr>
      <td align="center" style="padding: 32px 16px;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width: 520px; background: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.08);">
          <!-- Header -->
          <tr>
            <td style="background: linear-gradient(135deg, #275255, #459492); padding: 24px 32px; text-align: center;">
              <span style="font-size: 20px; font-weight: 700; color: #ffffff; letter-spacing: -0.3px;">InFinea</span>
              <br>
              <span style="font-size: 12px; color: rgba(255,255,255,0.7);">Ton récap hebdomadaire</span>
            </td>
          </tr>
          <!-- Content -->
          <tr>
            <td style="padding: 28px 32px;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                {body_content}
                <!-- CTA -->
                <tr>
                  <td style="padding: 24px 0 0 0; text-align: center;">
                    <a href="{cta_url}"
                       style="display: inline-block; padding: 14px 32px; background: linear-gradient(135deg, #459492, #55B3AE);
                              color: #ffffff; text-decoration: none; border-radius: 10px; font-weight: 600; font-size: 15px;">
                      {cta_text}
                    </a>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="padding: 20px 32px; border-top: 1px solid #e5e7eb; text-align: center;">
              <p style="margin: 0; font-size: 11px; color: #9ca3af; line-height: 1.5;">
                Tu reçois cet email chaque semaine pour suivre ta progression.<br>
                <a href="{APP_URL}/notifications" style="color: #459492; text-decoration: underline;">Gérer mes préférences email</a>
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    return subject, html


async def send_weekly_summaries(dry_run: bool = False) -> dict:
    """Send weekly summary emails to all eligible users.

    Eligible = has email, email_notifications enabled, email_weekly_summary not disabled.
    Processes users in batches to avoid memory issues.

    Returns: {"sent": int, "skipped": int, "errors": int}
    """
    BATCH_SIZE = 100
    sent = 0
    skipped = 0
    errors = 0

    # Find all users with an email address
    cursor = db.users.find(
        {"email": {"$exists": True, "$ne": ""}},
        {"_id": 0, "user_id": 1},
    )

    batch = []
    async for user_doc in cursor:
        batch.append(user_doc["user_id"])
        if len(batch) >= BATCH_SIZE:
            result = await _process_batch(batch, dry_run)
            sent += result["sent"]
            skipped += result["skipped"]
            errors += result["errors"]
            batch = []

    # Process remaining
    if batch:
        result = await _process_batch(batch, dry_run)
        sent += result["sent"]
        skipped += result["skipped"]
        errors += result["errors"]

    logger.info(f"Weekly summary complete: sent={sent}, skipped={skipped}, errors={errors}")
    return {"sent": sent, "skipped": skipped, "errors": errors}


async def _process_batch(user_ids: list, dry_run: bool) -> dict:
    """Process a batch of users for weekly summary."""
    sent = 0
    skipped = 0
    errors = 0

    for uid in user_ids:
        try:
            stats = await compute_user_weekly_stats(uid)
            if not stats:
                skipped += 1
                continue

            subject, html = render_weekly_summary_email(stats)

            if dry_run:
                logger.info(f"[DRY RUN] Would send to {uid}: {subject}")
                sent += 1
                continue

            await send_email_to_user(
                uid, subject, html,
                email_category="weekly_summary",
            )
            sent += 1

        except Exception:
            logger.exception(f"Weekly summary failed for {uid}")
            errors += 1

    return {"sent": sent, "skipped": skipped, "errors": errors}
