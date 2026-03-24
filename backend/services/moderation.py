"""
InFinea — Moderation Service.
Content filtering, sanitization, and block-list helpers.

Architecture:
- Layer 1: Regex-based instant filter (slurs, spam, dangerous patterns).
- sanitize_text(): Strip HTML, normalize whitespace.
- get_blocked_ids(): Bidirectional block lookup (shared helper for feed/search/profiles).

Benchmarked: Discord AutoMod (regex layer), Slack content filtering.
"""

import re
import logging
from typing import Optional, Set

from database import db

logger = logging.getLogger(__name__)

# ── Regex patterns for Layer 1 moderation ──
# French + English obvious toxicity, spam, and dangerous content.
# Deliberately conservative — catches clear violations only, no false positives on normal speech.

_SLUR_PATTERNS = [
    # French insults / hate speech
    r"\b(connard|connasse|enculé|enculée|nique\s*ta\s*mère|ntm|fdp|fils\s*de\s*pute|pute|salope|pd|tapette|négro|nègre|bougnoule|youpin|bicot|bamboula|crouille)\b",
    # English slurs
    r"\b(nigger|nigga|faggot|retard|kike|spic|chink|wetback|tranny)\b",
    # Self-harm / violence incitement
    r"\b(suicide[\-\s]?toi|tue[\-\s]?toi|kill\s*yourself|kys)\b",
]

_SPAM_PATTERNS = [
    # Repeated characters (5+)
    r"(.)\1{5,}",
    # Excessive caps (10+ consecutive uppercase, not acronyms)
    r"[A-Z]{10,}",
    # Suspicious URLs (common spam TLDs)
    r"https?://[^\s]*(\.ru|\.cn|\.tk|\.ml|\.ga|\.cf|bit\.ly|tinyurl|shorturl)[^\s]*",
]

# Compiled for performance
_COMPILED_SLURS = [re.compile(p, re.IGNORECASE) for p in _SLUR_PATTERNS]
_COMPILED_SPAM = [re.compile(p) for p in _SPAM_PATTERNS]


def check_content(text: str) -> dict:
    """
    Layer 1 moderation: instant regex check on user-generated content.

    Returns:
        {"allowed": True} or {"allowed": False, "reason": str}
    """
    if not text:
        return {"allowed": True}

    # Check slurs
    for pattern in _COMPILED_SLURS:
        if pattern.search(text):
            return {"allowed": False, "reason": "Contenu inapproprié détecté"}

    # Check spam patterns
    for pattern in _COMPILED_SPAM:
        if pattern.search(text):
            return {"allowed": False, "reason": "Contenu identifié comme spam"}

    return {"allowed": True}


def sanitize_text(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize user input: strip HTML tags, normalize whitespace.
    No dependency needed — HTML tags are stripped via regex since
    all UGC is rendered as plain text in React (no dangerouslySetInnerHTML).

    Args:
        text: Raw user input.
        max_length: Optional truncation limit.

    Returns:
        Cleaned plain text.
    """
    if not text:
        return ""

    # Strip HTML tags
    cleaned = re.sub(r"<[^>]+>", "", text)

    # Strip common HTML entities
    cleaned = cleaned.replace("&lt;", "<").replace("&gt;", ">")
    cleaned = cleaned.replace("&amp;", "&").replace("&quot;", '"')

    # Normalize whitespace (collapse multiple spaces/newlines)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    cleaned = cleaned.strip()

    if max_length and len(cleaned) > max_length:
        cleaned = cleaned[:max_length]

    return cleaned


async def get_blocked_ids(user_id: str) -> Set[str]:
    """
    Get all user IDs involved in a block relationship with user_id.
    Bidirectional: if A blocks B, both A and B are filtered from each other's views.

    Used by: feed, search, suggestions, profile access, comments.
    """
    blocks = await db.blocks.find(
        {"$or": [{"blocker_id": user_id}, {"blocked_id": user_id}]},
        {"_id": 0, "blocker_id": 1, "blocked_id": 1},
    ).to_list(1000)

    blocked_ids = set()
    for b in blocks:
        if b["blocker_id"] == user_id:
            blocked_ids.add(b["blocked_id"])
        else:
            blocked_ids.add(b["blocker_id"])

    return blocked_ids
