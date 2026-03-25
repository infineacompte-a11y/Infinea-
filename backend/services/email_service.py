"""
InFinea — Email Notification Service.
Sends transactional emails via Resend.

Architecture:
- send_email_to_user(): fail-safe helper (same pattern as send_push_to_user).
- render_email(): branded HTML template with inline CSS for email clients.
- Per-type templates: email_new_follower, email_mention, email_badge_earned, etc.
- Preferences check: respects user email_notifications + granular toggles.

Benchmarked: Duolingo (streak urgency), Strava (social celebration), Notion (clean layout).
"""

import os
import logging

from database import db

logger = logging.getLogger(__name__)

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
FROM_EMAIL = os.getenv("EMAIL_FROM", "InFinea <noreply@infinea.app>")
APP_URL = os.getenv("APP_URL", "https://infinea.app")

if not RESEND_API_KEY:
    logger.warning("⚠ RESEND_API_KEY not set — all emails will be silently skipped")
else:
    logger.info("✓ Email service ready (Resend)")


# ── Core send helper ──

async def send_email_to_user(
    user_id: str,
    subject: str,
    html: str,
    email_category: str = "social",
):
    """Send email to user. Silently fails — never blocks the caller.

    Args:
        user_id: Target user ID.
        subject: Email subject line.
        html: Rendered HTML body.
        email_category: One of 'social', 'achievements', 'streak', 'weekly_summary'.
            Used to check granular preferences.
    """
    if not RESEND_API_KEY:
        return

    try:
        user = await db.users.find_one(
            {"user_id": user_id},
            {"_id": 0, "email": 1, "display_name": 1},
        )
        if not user or not user.get("email"):
            return

        # Check email preferences
        prefs = await db.notification_preferences.find_one({"user_id": user_id})
        if prefs:
            # Master toggle
            if not prefs.get("email_notifications", True):
                return
            # Granular toggles
            category_key = f"email_{email_category}"
            if not prefs.get(category_key, True):
                return

        import resend
        resend.api_key = RESEND_API_KEY
        resend.Emails.send({
            "from": FROM_EMAIL,
            "to": [user["email"]],
            "subject": subject,
            "html": html,
        })
        logger.info(f"Email sent to {user_id}: {subject}")

    except Exception as e:
        logger.warning(f"Email failed for {user_id}: {e}")


# ── Branded HTML template ──

def render_email(title: str, body: str, cta_text: str = "", cta_url: str = "") -> str:
    """Render a branded InFinea email with inline CSS.

    Compatible with all major email clients (Gmail, Outlook, Apple Mail).
    Uses table-based layout for maximum compatibility.
    """
    cta_block = ""
    if cta_text and cta_url:
        full_url = cta_url if cta_url.startswith("http") else f"{APP_URL}{cta_url}"
        cta_block = f"""
        <tr>
          <td style="padding: 24px 0 0 0;">
            <a href="{full_url}"
               style="display: inline-block; padding: 12px 28px; background: linear-gradient(135deg, #459492, #55B3AE);
                      color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 14px;">
              {cta_text}
            </a>
          </td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin: 0; padding: 0; background-color: #f4f4f5; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color: #f4f4f5;">
    <tr>
      <td align="center" style="padding: 32px 16px;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width: 520px; background: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.08);">
          <!-- Header -->
          <tr>
            <td style="background: linear-gradient(135deg, #275255, #459492); padding: 28px 32px; text-align: center;">
              <span style="font-size: 20px; font-weight: 700; color: #ffffff; letter-spacing: -0.3px;">InFinea</span>
            </td>
          </tr>
          <!-- Content -->
          <tr>
            <td style="padding: 32px;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td>
                    <h1 style="margin: 0 0 16px 0; font-size: 20px; font-weight: 700; color: #275255; line-height: 1.3;">
                      {title}
                    </h1>
                    <p style="margin: 0; font-size: 15px; color: #374151; line-height: 1.6;">
                      {body}
                    </p>
                  </td>
                </tr>
                {cta_block}
              </table>
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="padding: 20px 32px; border-top: 1px solid #e5e7eb; text-align: center;">
              <p style="margin: 0; font-size: 11px; color: #9ca3af; line-height: 1.5;">
                Tu reçois cet email car tu utilises InFinea.<br>
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


# ── Per-type email templates ──

def email_new_follower(follower_name: str, profile_url: str = "") -> tuple:
    """Returns (subject, html) for a new follower notification."""
    subject = f"{follower_name} te suit sur InFinea"
    html = render_email(
        title="Nouveau follower !",
        body=f"<strong>{follower_name}</strong> a commencé à te suivre. Découvre son profil et connectez-vous !",
        cta_text="Voir le profil",
        cta_url=profile_url or "/community",
    )
    return subject, html


def email_mention(mentioner_name: str, content_preview: str, context_url: str = "") -> tuple:
    """Returns (subject, html) for a mention notification."""
    preview = content_preview[:100] + ("..." if len(content_preview) > 100 else "")
    subject = f"{mentioner_name} t'a mentionné sur InFinea"
    html = render_email(
        title="Tu as été mentionné !",
        body=f"<strong>{mentioner_name}</strong> t'a mentionné :<br><br>"
             f"<span style='color: #6b7280; font-style: italic;'>\"{preview}\"</span>",
        cta_text="Voir le message",
        cta_url=context_url or "/community",
    )
    return subject, html


def email_badge_earned(badge_name: str) -> tuple:
    """Returns (subject, html) for a badge earned notification."""
    subject = f"Bravo ! Tu as obtenu le badge \"{badge_name}\""
    html = render_email(
        title=f"Badge débloqué : {badge_name} !",
        body="Félicitations ! Ton travail régulier porte ses fruits. Continue comme ça pour débloquer encore plus de badges.",
        cta_text="Voir mes badges",
        cta_url="/profile",
    )
    return subject, html


def email_streak_alert(streak_days: int) -> tuple:
    """Returns (subject, html) for a streak alert notification."""
    subject = f"Ton streak de {streak_days} jours est en danger !"
    html = render_email(
        title=f"Streak en danger — {streak_days} jours",
        body=f"Tu as un streak de <strong>{streak_days} jour{'s' if streak_days > 1 else ''}</strong> ! "
             "Ne le perds pas — une micro-session de 5 minutes suffit pour le maintenir.",
        cta_text="Faire ma session",
        cta_url="/today",
    )
    return subject, html


def email_milestone(milestone_text: str) -> tuple:
    """Returns (subject, html) for a milestone notification."""
    subject = f"Félicitations ! {milestone_text}"
    html = render_email(
        title=milestone_text,
        body="Un cap important franchi dans ton parcours d'apprentissage. "
             "Continue sur cette lancée !",
        cta_text="Voir ma progression",
        cta_url="/progression",
    )
    return subject, html


def email_group_invite(inviter_name: str, group_name: str) -> tuple:
    """Returns (subject, html) for a group invite notification."""
    subject = f"{inviter_name} t'invite à rejoindre \"{group_name}\""
    html = render_email(
        title="Invitation à un groupe",
        body=f"<strong>{inviter_name}</strong> t'a invité à rejoindre le groupe "
             f"<strong>{group_name}</strong>. Apprends ensemble avec ta communauté !",
        cta_text="Voir l'invitation",
        cta_url="/groups",
    )
    return subject, html


def email_weekly_summary(
    sessions_count: int,
    streak_days: int,
    total_minutes: int,
) -> tuple:
    """Returns (subject, html) for a weekly summary email."""
    subject = "Ton résumé de la semaine — InFinea"
    html = render_email(
        title="Ta semaine en un coup d'œil",
        body=f"<strong>{sessions_count}</strong> session{'s' if sessions_count > 1 else ''} complétée{'s' if sessions_count > 1 else ''}<br>"
             f"<strong>{total_minutes}</strong> minutes d'apprentissage<br>"
             f"<strong>{streak_days}</strong> jour{'s' if streak_days > 1 else ''} de streak<br><br>"
             "Continue comme ça, chaque petit pas compte !",
        cta_text="Voir ma progression",
        cta_url="/progression",
    )
    return subject, html
