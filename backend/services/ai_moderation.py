"""
InFinea — AI Moderation Service (Layer 2).

Async post-publication content moderation powered by Claude Haiku (multimodal).
Analyzes text AND images for toxicity, harassment, spam, and policy violations.

━━━ Architecture ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Layer 1 (existing): Regex-based instant filter — catches obvious slurs/spam.
Layer 2 (this):     Claude Haiku semantic analysis — catches subtle toxicity,
                    context-aware harassment, image violations, sarcasm, dog-
                    whistles, and content that regex can't catch.

Pattern: async post-publication (Instagram/Twitter model).
Content passes L1 → published immediately → L2 runs in background →
if flagged → content hidden + author notified + audit log created.

This gives zero perceived latency while maintaining strong moderation.

━━━ Moderation Categories ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Six categories scored 0.0-1.0, benchmarked from:
- OpenAI Moderation API (category taxonomy)
- Google Perspective API (toxicity scoring)
- Discord AutoMod (action thresholds)
- Meta Integrity systems (context-aware analysis)

━━━ Decision Thresholds ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Score < 0.4   → ALLOW (no action)
  0.4 ≤ score < 0.75 → FLAG (published, logged for review)
  Score ≥ 0.75  → AUTO-HIDE (content hidden, author notified)

Conservative by design: false positives are worse than false negatives
in a learning community. Legitimate content must never be silenced.

━━━ Performance ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- Claude Haiku: ~200-400ms per request
- Cost: ~$0.80/MTok input, $4/MTok output (Haiku 4.5)
- Typical moderation call: ~300 input tokens + ~80 output tokens ≈ $0.0006
- At 1000 posts/day: ~$0.60/day — trivial cost for production moderation
- Fail-safe: if AI call fails, content stays published (no silent censorship)
"""

import os
import json
import uuid
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx

from database import db

logger = logging.getLogger(__name__)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONFIGURATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MODERATION_MODEL = "claude-haiku-4-5-20251001"
MODERATION_TIMEOUT = 15.0  # seconds — generous for multimodal

# Decision thresholds
THRESHOLD_FLAG = 0.4       # Score >= 0.4 → logged for admin review
THRESHOLD_HIDE = 0.75      # Score >= 0.75 → auto-hidden

# Content types that can be moderated
CONTENT_TYPES = {"post", "comment", "message", "profile", "group"}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SYSTEM PROMPT — The heart of the moderation engine
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MODERATION_SYSTEM_PROMPT = """Tu es le système de modération d'InFinea, une plateforme de micro-apprentissage progressif.

Ta mission : analyser le contenu soumis et évaluer s'il enfreint les règles de la communauté.

CONTEXTE INFINEA :
- Communauté d'apprentissage bienveillante (langues, musique, sport, etc.)
- Les utilisateurs partagent leurs progrès, s'encouragent, posent des questions
- Le ton est positif, motivant, entre pairs qui apprennent
- Contenu attendu : réflexions sur l'apprentissage, célébrations, questions, entraide

CATÉGORIES D'ÉVALUATION (score 0.0 à 1.0 chacune) :

1. toxicity — Insultes, discours haineux, menaces, déshumanisation.
   0.0 = neutre/positif, 0.3 = ton sec mais acceptable, 0.5 = agressif, 0.8 = clairement toxique, 1.0 = menace/haine

2. harassment — Harcèlement ciblé, intimidation, moquerie répétée, doxxing.
   0.0 = pas de cible, 0.4 = moquerie légère, 0.7 = harcèlement ciblé, 1.0 = doxxing/menace personnelle

3. sexual — Contenu sexuellement explicite ou suggestif inapproprié.
   0.0 = rien, 0.3 = sous-entendu léger, 0.6 = contenu suggestif, 0.9 = explicite

4. violence — Violence graphique, gore, automutilation, incitation à la violence.
   0.0 = rien, 0.4 = mention contextuelle, 0.7 = description graphique, 1.0 = incitation directe

5. spam — Contenu promotionnel, répétitif, hors-sujet, tentative de manipulation.
   0.0 = authentique, 0.4 = légèrement hors-sujet, 0.7 = promotionnel évident, 1.0 = spam pur

6. harmful — Désinformation dangereuse, conseils médicaux dangereux, manipulation psychologique.
   0.0 = informatif/neutre, 0.4 = approximatif, 0.7 = potentiellement dangereux, 1.0 = danger immédiat

RÈGLES D'ÉVALUATION :
- Sois tolérant avec l'humour, l'argot, et les expressions familières entre pairs
- Le contexte d'apprentissage rend certaines discussions légitimes (ex: "je galère" n'est pas toxique)
- L'autocritique sur son propre apprentissage est toujours acceptable
- L'émoji et le ton informel ne sont PAS des indicateurs de toxicité
- Un désaccord respectueux n'est PAS du harcèlement
- CONSERVATEUR : en cas de doute, favorise la liberté d'expression
- Les faux positifs sont PIRES que les faux négatifs dans une communauté d'apprentissage

RÉPONSE — Format JSON strict, rien d'autre :
{
  "scores": {
    "toxicity": 0.0,
    "harassment": 0.0,
    "sexual": 0.0,
    "violence": 0.0,
    "spam": 0.0,
    "harmful": 0.0
  },
  "max_score": 0.0,
  "max_category": "none",
  "summary": "Description courte en français de l'évaluation"
}"""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PUBLIC API
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def moderate_content_async(
    content_id: str,
    content_type: str,
    author_id: str,
    text: str = "",
    image_urls: list[str] | None = None,
):
    """
    Fire-and-forget AI moderation. Call via asyncio.create_task().

    This function:
    1. Sends text + images to Claude Haiku for analysis
    2. If score >= THRESHOLD_FLAG → logs a moderation action
    3. If score >= THRESHOLD_HIDE → hides the content + notifies author
    4. Never raises — all errors are logged and swallowed

    Args:
        content_id: activity_id, comment_id, or message_id
        content_type: "post", "comment", "message"
        author_id: user_id of the content author
        text: text content to moderate
        image_urls: optional list of image URLs to analyze
    """
    try:
        result = await _call_moderation_ai(text, image_urls)
        if not result:
            return  # AI call failed — fail open (content stays)

        max_score = result.get("max_score", 0.0)

        # ── Below flag threshold → clean content, no action ──
        if max_score < THRESHOLD_FLAG:
            return

        # ── Flag threshold → log for admin review ──
        action = "flagged" if max_score < THRESHOLD_HIDE else "auto_hidden"

        moderation_doc = {
            "moderation_id": f"mod_{uuid.uuid4().hex[:12]}",
            "content_id": content_id,
            "content_type": content_type,
            "author_id": author_id,
            "action": action,
            "scores": result.get("scores", {}),
            "max_score": max_score,
            "max_category": result.get("max_category", "unknown"),
            "summary": result.get("summary", ""),
            "text_snippet": text[:200] if text else "",
            "image_urls": image_urls or [],
            "reviewed": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        await db.moderation_actions.insert_one(moderation_doc)

        # ── Auto-hide threshold → hide content + notify author ──
        if action == "auto_hidden":
            await _hide_content(content_id, content_type)
            await _notify_author(
                author_id,
                content_type,
                result.get("max_category", ""),
            )

        logger.info(
            f"Moderation {action}: {content_type} {content_id} "
            f"(max={max_score:.2f}, cat={result.get('max_category')})"
        )

    except Exception:
        logger.exception(f"AI moderation error for {content_type} {content_id}")
        # Fail open — content stays published


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AI CALL — Claude Haiku multimodal
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _call_moderation_ai(
    text: str,
    image_urls: list[str] | None = None,
) -> Optional[dict]:
    """
    Call Claude Haiku with text and/or images for moderation analysis.
    Returns parsed JSON scores or None on failure.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    # Build multimodal content array
    content_parts = []

    # Add images first (vision context)
    if image_urls:
        for url in image_urls[:4]:  # Max 4 images
            content_parts.append({
                "type": "image",
                "source": {"type": "url", "url": url},
            })

    # Add text
    if text:
        content_parts.append({
            "type": "text",
            "text": f"Contenu à modérer :\n\n{text[:2000]}",
        })
    elif not content_parts:
        return None  # Nothing to moderate

    # If only images, add instruction
    if not text and image_urls:
        content_parts.append({
            "type": "text",
            "text": "Analyse les images ci-dessus pour la modération.",
        })

    try:
        async with httpx.AsyncClient(timeout=MODERATION_TIMEOUT) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": MODERATION_MODEL,
                    "max_tokens": 200,
                    "system": MODERATION_SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": content_parts}],
                },
            )
            resp.raise_for_status()
            data = resp.json()

            raw_text = data["content"][0]["text"]
            return _parse_moderation_response(raw_text)

    except httpx.TimeoutException:
        logger.warning("Moderation AI timeout — failing open")
        return None
    except Exception as e:
        logger.warning(f"Moderation AI error: {e}")
        return None


def _parse_moderation_response(raw: str) -> Optional[dict]:
    """Parse JSON from Claude's response, handling markdown code blocks."""
    if not raw:
        return None

    # Strip markdown code block if present
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON object in the response
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                result = json.loads(text[start:end])
            except json.JSONDecodeError:
                logger.warning(f"Could not parse moderation response: {raw[:200]}")
                return None
        else:
            return None

    # Validate structure
    scores = result.get("scores", {})
    if not isinstance(scores, dict):
        return None

    # Compute max_score from scores if not provided
    score_values = [
        float(v) for v in scores.values()
        if isinstance(v, (int, float))
    ]
    if score_values:
        result["max_score"] = max(score_values)
        result["max_category"] = max(
            scores, key=lambda k: float(scores.get(k, 0))
        )

    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONTENT ACTIONS — Hide + Notify
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _hide_content(content_id: str, content_type: str):
    """
    Hide content by setting moderation_status = 'hidden'.
    The content remains in DB (audit trail) but is excluded from queries.
    """
    if content_type == "post":
        await db.activities.update_one(
            {"activity_id": content_id},
            {"$set": {"moderation_status": "hidden"}},
        )
    elif content_type == "comment":
        await db.comments.update_one(
            {"comment_id": content_id},
            {"$set": {"moderation_status": "hidden"}},
        )
    elif content_type == "message":
        await db.messages.update_one(
            {"message_id": content_id},
            {"$set": {"moderation_status": "hidden"}},
        )


async def _notify_author(
    author_id: str,
    content_type: str,
    category: str,
):
    """Notify the content author that their content was moderated."""
    type_labels = {
        "post": "publication",
        "comment": "commentaire",
        "message": "message",
    }
    category_labels = {
        "toxicity": "langage inapproprié",
        "harassment": "harcèlement",
        "sexual": "contenu inapproprié",
        "violence": "contenu violent",
        "spam": "spam",
        "harmful": "contenu potentiellement dangereux",
    }

    content_label = type_labels.get(content_type, "contenu")
    reason_label = category_labels.get(category, "violation des règles")

    try:
        await db.notifications.insert_one({
            "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
            "user_id": author_id,
            "type": "moderation",
            "message": (
                f"Ton {content_label} a été masqué pour {reason_label}. "
                f"Si tu penses que c'est une erreur, contacte le support."
            ),
            "data": {
                "content_type": content_type,
                "category": category,
            },
            "read": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    except Exception:
        logger.exception("Failed to notify author of moderation action")
