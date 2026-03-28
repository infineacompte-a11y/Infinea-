"""
InFinea — AI Memory Service.

Persistent fact extraction and injection for user-level AI personalization.
After each coach chat exchange, a lightweight Haiku call extracts durable facts
about the user (preferences, goals, obstacles, insights, struggles).

These facts are stored in the ai_memories collection and injected into future
AI conversations, giving the coach persistent knowledge of the user across sessions.

Memory lifecycle:
1. User speaks to coach → extract_memories() fires (async, non-blocking)
2. Facts stored with confidence >= 0.6, categorized, PII-sanitized
3. On next AI call → get_user_memories() retrieves top 10 most relevant
4. Memories formatted as prompt text (~200 tokens max) for injection
5. Stale memories auto-expire via MongoDB TTL (category-dependent)
6. Contradictory memories: newest supersedes oldest (upsert on similar key)

Categories:
- preference: "prefere les sessions courtes le matin"
- goal: "veut parler thai pour un voyage en octobre"
- constraint: "ne peut pas pratiquer le lundi soir"
- insight: "les exercices de respiration l'aident avant les reunions"
- struggle: "a du mal avec la discipline le week-end"

Cost: ~$0.0003 per extraction (Haiku). At 100 conversations/day = $0.03/day.

Benchmarks: Character.ai (persistent persona), ChatGPT Memory (fact extraction),
Notion AI (workspace context), Replika (emotional memory).
"""

import re
import json
import uuid
import logging
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger("infinea")


# ═══════════════════════════════════════════════════════════════════════════
# PII SANITIZATION
# ═══════════════════════════════════════════════════════════════════════════

PII_PATTERNS = [
    re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'),  # Credit cards
    re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),  # Emails
    re.compile(r'\b\d{2,3}[-.\s]?\d{2,3}[-.\s]?\d{2,4}\b'),  # Phone numbers
    re.compile(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b'),  # Birth dates (DD/MM/YYYY)
]


def _sanitize_fact(fact: str) -> str:
    """Remove PII from extracted facts before storage."""
    for pattern in PII_PATTERNS:
        fact = pattern.sub('[info personnelle]', fact)
    return fact.strip()


# ═══════════════════════════════════════════════════════════════════════════
# MEMORY EXTRACTION
# ═══════════════════════════════════════════════════════════════════════════

EXTRACTION_PROMPT = """Analyse cet echange entre un coach et un utilisateur.
Extrais les FAITS NOUVEAUX et IMPORTANTS mentionnes par l'UTILISATEUR (pas le coach).

Categories de faits a extraire:
- preference: habitudes, preferences horaires, types d'activites preferees, style d'apprentissage
- goal: objectifs mentionnes, raisons de motivation, echeances, ambitions
- constraint: limitations, jours/heures impossibles, restrictions physiques ou temporelles
- insight: ce qui fonctionne pour lui, strategies personnelles, declics
- struggle: difficultes, blocages, sources de frustration, patterns d'abandon

Regles strictes:
- N'extrais QUE ce que l'utilisateur a dit explicitement
- Ignore les reponses generiques ("ca va", "ok", "merci", "oui")
- Maximum 3 faits par echange
- Chaque fait doit etre une information DURABLE (pas ephemere)
- Si aucun fait nouveau: reponds {"facts": []}

Reponds en JSON strict:
{"facts": [{"fact": "description courte et claire", "category": "preference|goal|constraint|insight|struggle", "confidence": 0.5-1.0}]}"""


# TTL by category (in days)
MEMORY_TTL = {
    "preference": 180,    # 6 months
    "goal": None,         # Permanent (goals are always relevant)
    "constraint": 90,     # 3 months (constraints can change)
    "insight": 120,       # 4 months
    "struggle": 90,       # 3 months (struggles can be resolved)
}

MIN_MESSAGE_LENGTH = 20  # Skip extraction for very short messages
MIN_CONFIDENCE = 0.6     # Minimum confidence to store a fact
MAX_MEMORIES_PER_USER = 50  # Cap to prevent unbounded growth


async def extract_memories(
    db,
    user_id: str,
    user_message: str,
    coach_response: str,
) -> list:
    """Extract memorable facts from a coach conversation exchange.

    Uses Haiku (EXTRACT tier) for cost efficiency. Fire-and-forget safe.
    Called after every coach_chat response via asyncio.create_task().

    Returns list of stored memory dicts, or empty list on failure.
    """
    # Skip very short messages (acknowledgments, greetings)
    if not user_message or len(user_message.strip()) < MIN_MESSAGE_LENGTH:
        return []

    try:
        from services.llm_provider import call_llm, ModelTier

        exchange = f"Utilisateur: {user_message}\nCoach: {coach_response}"
        response = await call_llm(
            system_prompt=EXTRACTION_PROMPT,
            user_prompt=exchange,
            model_tier=ModelTier.EXTRACT,
            max_tokens=200,
            caller="memory_extraction",
            user_id=user_id,
            cache_system=True,
        )

        if not response:
            return []

        # Parse JSON response
        parsed = _parse_extraction_response(response)
        if not parsed:
            return []

        # Store valid facts
        stored = []
        for fact_data in parsed:
            fact_text = fact_data.get("fact", "").strip()
            category = fact_data.get("category", "")
            confidence = fact_data.get("confidence", 0.5)

            if not fact_text or category not in MEMORY_TTL or confidence < MIN_CONFIDENCE:
                continue

            # Sanitize PII
            fact_text = _sanitize_fact(fact_text)
            if not fact_text or fact_text == '[info personnelle]':
                continue

            memory = await _store_memory(db, user_id, fact_text, category, confidence)
            if memory:
                stored.append(memory)

        return stored

    except Exception as e:
        logger.debug(f"Memory extraction error for {user_id}: {e}")
        return []


def _parse_extraction_response(response: str) -> list:
    """Parse the AI extraction response into a list of fact dicts."""
    try:
        data = json.loads(response)
        return data.get("facts", [])
    except (json.JSONDecodeError, TypeError):
        pass
    # Try extracting JSON from response
    try:
        start = response.find('{')
        end = response.rfind('}') + 1
        if start >= 0 and end > start:
            data = json.loads(response[start:end])
            return data.get("facts", [])
    except (json.JSONDecodeError, TypeError):
        pass
    return []


async def _store_memory(
    db,
    user_id: str,
    fact: str,
    category: str,
    confidence: float,
) -> Optional[dict]:
    """Store a memory fact, handling dedup and TTL."""
    try:
        now = datetime.now(timezone.utc)
        memory_id = f"mem_{uuid.uuid4().hex[:12]}"

        # Check for existing similar memory (same category, similar text)
        # Simple dedup: if a memory in the same category starts with the same 30 chars
        existing = await db.ai_memories.find_one({
            "user_id": user_id,
            "category": category,
            "fact": {"$regex": f"^{re.escape(fact[:30])}"},
            "superseded_by": None,
        })

        if existing:
            # Supersede the old memory
            await db.ai_memories.update_one(
                {"_id": existing["_id"]},
                {"$set": {"superseded_by": memory_id, "updated_at": now.isoformat()}},
            )

        # Compute expiry
        ttl_days = MEMORY_TTL.get(category)
        expires_at = (now + timedelta(days=ttl_days)).isoformat() if ttl_days else None

        doc = {
            "user_id": user_id,
            "memory_id": memory_id,
            "fact": fact,
            "category": category,
            "source": "coach_chat",
            "confidence": round(confidence, 2),
            "created_at": now.isoformat(),
            "last_used_at": now.isoformat(),
            "superseded_by": None,
        }
        if expires_at:
            doc["expires_at"] = expires_at

        await db.ai_memories.insert_one(doc)

        # Enforce per-user cap
        count = await db.ai_memories.count_documents({
            "user_id": user_id, "superseded_by": None,
        })
        if count > MAX_MEMORIES_PER_USER:
            # Delete oldest non-goal memories
            oldest = await db.ai_memories.find(
                {"user_id": user_id, "superseded_by": None, "category": {"$ne": "goal"}},
            ).sort("created_at", 1).limit(count - MAX_MEMORIES_PER_USER).to_list(10)
            if oldest:
                ids = [m["_id"] for m in oldest]
                await db.ai_memories.delete_many({"_id": {"$in": ids}})

        # Invalidate cache
        try:
            from services.cache import cache_delete
            await cache_delete(f"user_memories:{user_id}")
        except Exception:
            pass

        return doc

    except Exception as e:
        logger.debug(f"Memory store error: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════════════
# MEMORY RETRIEVAL
# ═══════════════════════════════════════════════════════════════════════════

# Priority order for memory categories (most important first)
CATEGORY_PRIORITY = {
    "goal": 0,
    "struggle": 1,
    "preference": 2,
    "constraint": 3,
    "insight": 4,
}


async def get_user_memories(db, user_id: str, limit: int = 10) -> list:
    """Retrieve the most relevant active memories for prompt injection.

    Priority: goals > struggles > preferences > constraints > insights.
    Excludes expired and superseded memories.
    Caches result in Redis for 1 hour.

    Returns list of memory dicts.
    """
    # Try cache first
    try:
        from services.cache import cache_get, cache_set
        cached = await cache_get(f"user_memories:{user_id}")
        if cached:
            return cached
    except Exception:
        pass

    try:
        memories = await db.ai_memories.find(
            {
                "user_id": user_id,
                "superseded_by": None,
                "confidence": {"$gte": MIN_CONFIDENCE},
            },
            {"_id": 0, "fact": 1, "category": 1, "confidence": 1, "created_at": 1},
        ).sort("created_at", -1).limit(30).to_list(30)

        # Sort by category priority, then by confidence descending
        memories.sort(key=lambda m: (
            CATEGORY_PRIORITY.get(m.get("category", "insight"), 5),
            -m.get("confidence", 0),
        ))

        result = memories[:limit]

        # Cache for 1 hour
        try:
            from services.cache import cache_set
            await cache_set(f"user_memories:{user_id}", result, ttl=3600)
        except Exception:
            pass

        return result

    except Exception as e:
        logger.debug(f"Memory retrieval error for {user_id}: {e}")
        return []


async def format_memories_for_prompt(memories: list) -> str:
    """Format memories into a prompt-ready text block (~200 tokens max).

    Returns empty string if no memories.
    """
    if not memories:
        return ""

    lines = ["MEMOIRE DE L'UTILISATEUR (faits appris lors de conversations precedentes):"]
    for mem in memories:
        category_label = {
            "goal": "Objectif",
            "preference": "Preference",
            "constraint": "Contrainte",
            "insight": "Ce qui marche",
            "struggle": "Difficulte",
        }.get(mem.get("category", ""), "Info")

        lines.append(f"- [{category_label}] {mem['fact']}")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
# MEMORY LIFECYCLE
# ═══════════════════════════════════════════════════════════════════════════

async def update_memory_usage(db, user_id: str, memory_ids: list = None):
    """Update last_used_at for memories that were injected into a prompt.

    Memories not used for 60+ days (except goals) will be cleaned up.
    """
    if not memory_ids:
        return
    try:
        now = datetime.now(timezone.utc).isoformat()
        await db.ai_memories.update_many(
            {"user_id": user_id, "memory_id": {"$in": memory_ids}},
            {"$set": {"last_used_at": now}},
        )
    except Exception:
        pass


async def memory_cleanup_loop(db):
    """Background loop that cleans up stale memories.

    Runs every 24 hours. Deletes:
    - Superseded memories older than 30 days
    - Non-goal memories not used in 60 days
    """
    import asyncio
    await asyncio.sleep(120)  # Wait 2 min after startup
    while True:
        try:
            now = datetime.now(timezone.utc)
            cutoff_30d = (now - timedelta(days=30)).isoformat()
            cutoff_60d = (now - timedelta(days=60)).isoformat()

            # Delete old superseded memories
            result1 = await db.ai_memories.delete_many({
                "superseded_by": {"$ne": None},
                "created_at": {"$lt": cutoff_30d},
            })

            # Delete stale non-goal memories (not used in 60 days)
            result2 = await db.ai_memories.delete_many({
                "category": {"$ne": "goal"},
                "last_used_at": {"$lt": cutoff_60d},
                "superseded_by": None,
            })

            if result1.deleted_count or result2.deleted_count:
                logger.info(
                    f"Memory cleanup: {result1.deleted_count} superseded + "
                    f"{result2.deleted_count} stale memories removed"
                )

        except Exception as e:
            logger.error(f"Memory cleanup error: {e}")

        await asyncio.sleep(24 * 3600)  # Run every 24 hours
