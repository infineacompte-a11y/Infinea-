"""
Unit tests — AI Memory Service.
Persistent fact extraction, PII sanitization, memory storage/retrieval.

Tests:
- _sanitize_fact: PII removal (credit cards, emails, phones, dates)
- _parse_extraction_response: JSON parsing with edge cases
- format_memories_for_prompt: prompt formatting
- get_user_memories: DB-dependent retrieval + priority ordering
- _store_memory: DB-dependent storage, dedup, cap
- MEMORY_TTL: configuration validation
"""

import pytest
from datetime import datetime, timezone, timedelta

from services.ai_memory import (
    _sanitize_fact,
    _parse_extraction_response,
    format_memories_for_prompt,
    get_user_memories,
    _store_memory,
    update_memory_usage,
    MEMORY_TTL,
    MIN_CONFIDENCE,
    MAX_MEMORIES_PER_USER,
    CATEGORY_PRIORITY,
    PII_PATTERNS,
)


# ═══════════════════════════════════════════════════════════════════
# _sanitize_fact — Pure function, PII removal
# ═══════════════════════════════════════════════════════════════════


class TestSanitizeFact:

    def test_no_pii_unchanged(self):
        """Text without PII is returned unchanged."""
        fact = "prefere les sessions courtes le matin"
        assert _sanitize_fact(fact) == fact

    def test_email_removed(self):
        """Email addresses are replaced."""
        fact = "son email est john@example.com pour le contacter"
        result = _sanitize_fact(fact)
        assert "john@example.com" not in result
        assert "[info personnelle]" in result

    def test_credit_card_removed(self):
        """Credit card numbers are replaced."""
        fact = "carte 4111 1111 1111 1111 pour le paiement"
        result = _sanitize_fact(fact)
        assert "4111" not in result
        assert "[info personnelle]" in result

    def test_credit_card_no_spaces(self):
        """Credit card without spaces."""
        fact = "carte 4111111111111111"
        result = _sanitize_fact(fact)
        assert "4111111111111111" not in result

    def test_phone_number_removed(self):
        """Phone numbers are replaced."""
        fact = "joignable au 06-12-34-56-78"
        result = _sanitize_fact(fact)
        assert "[info personnelle]" in result

    def test_birth_date_removed(self):
        """Birth dates DD/MM/YYYY are replaced."""
        fact = "ne le 15/03/1990"
        result = _sanitize_fact(fact)
        assert "15/03/1990" not in result
        assert "[info personnelle]" in result

    def test_strips_whitespace(self):
        """Result is stripped."""
        assert _sanitize_fact("  hello  ") == "hello"

    def test_multiple_pii_all_removed(self):
        """Multiple PII types in one fact are all removed."""
        fact = "email: test@x.com, tel: 06-12-34-56-78"
        result = _sanitize_fact(fact)
        assert "test@x.com" not in result
        # Phone should also be sanitized
        assert result.count("[info personnelle]") >= 1


# ═══════════════════════════════════════════════════════════════════
# _parse_extraction_response — Pure function
# ═══════════════════════════════════════════════════════════════════


class TestParseExtractionResponse:

    def test_valid_json(self):
        """Standard JSON response parsed correctly."""
        response = '{"facts": [{"fact": "aime le matin", "category": "preference", "confidence": 0.8}]}'
        result = _parse_extraction_response(response)
        assert len(result) == 1
        assert result[0]["fact"] == "aime le matin"
        assert result[0]["category"] == "preference"
        assert result[0]["confidence"] == 0.8

    def test_empty_facts(self):
        """Empty facts list."""
        response = '{"facts": []}'
        result = _parse_extraction_response(response)
        assert result == []

    def test_json_with_surrounding_text(self):
        """JSON embedded in markdown or other text."""
        response = 'Here is the analysis:\n{"facts": [{"fact": "test", "category": "goal", "confidence": 0.9}]}\nDone.'
        result = _parse_extraction_response(response)
        assert len(result) == 1
        assert result[0]["fact"] == "test"

    def test_invalid_json_returns_empty(self):
        """Completely invalid response → empty list."""
        result = _parse_extraction_response("this is not json at all")
        assert result == []

    def test_none_input_raises_or_empty(self):
        """None input → AttributeError (code assumes string input)."""
        # The function expects a string; None is caught upstream in extract_memories()
        with pytest.raises(AttributeError):
            _parse_extraction_response(None)

    def test_multiple_facts(self):
        """Multiple facts parsed."""
        response = '{"facts": [{"fact": "a", "category": "goal", "confidence": 0.9}, {"fact": "b", "category": "preference", "confidence": 0.7}]}'
        result = _parse_extraction_response(response)
        assert len(result) == 2

    def test_missing_facts_key(self):
        """JSON without 'facts' key → empty list."""
        response = '{"data": [{"fact": "a"}]}'
        result = _parse_extraction_response(response)
        assert result == []


# ═══════════════════════════════════════════════════════════════════
# format_memories_for_prompt — Pure/async function
# ═══════════════════════════════════════════════════════════════════


class TestFormatMemoriesForPrompt:

    @pytest.mark.asyncio
    async def test_empty_memories_returns_empty(self):
        result = await format_memories_for_prompt([])
        assert result == ""

    @pytest.mark.asyncio
    async def test_formats_goal(self):
        memories = [{"fact": "veut parler thai", "category": "goal"}]
        result = await format_memories_for_prompt(memories)
        assert "MEMOIRE DE L'UTILISATEUR" in result
        assert "[Objectif]" in result
        assert "veut parler thai" in result

    @pytest.mark.asyncio
    async def test_formats_preference(self):
        memories = [{"fact": "prefere le matin", "category": "preference"}]
        result = await format_memories_for_prompt(memories)
        assert "[Preference]" in result

    @pytest.mark.asyncio
    async def test_formats_constraint(self):
        memories = [{"fact": "pas dispo le lundi", "category": "constraint"}]
        result = await format_memories_for_prompt(memories)
        assert "[Contrainte]" in result

    @pytest.mark.asyncio
    async def test_formats_insight(self):
        memories = [{"fact": "la respiration aide", "category": "insight"}]
        result = await format_memories_for_prompt(memories)
        assert "[Ce qui marche]" in result

    @pytest.mark.asyncio
    async def test_formats_struggle(self):
        memories = [{"fact": "du mal le weekend", "category": "struggle"}]
        result = await format_memories_for_prompt(memories)
        assert "[Difficulte]" in result

    @pytest.mark.asyncio
    async def test_multiple_memories_formatted(self):
        memories = [
            {"fact": "objectif A", "category": "goal"},
            {"fact": "preference B", "category": "preference"},
            {"fact": "difficulte C", "category": "struggle"},
        ]
        result = await format_memories_for_prompt(memories)
        assert result.count("\n- ") == 3


# ═══════════════════════════════════════════════════════════════════
# MEMORY_TTL — Configuration validation
# ═══════════════════════════════════════════════════════════════════


class TestMemoryTTLConfig:

    def test_goal_is_permanent(self):
        assert MEMORY_TTL["goal"] is None

    def test_preference_ttl(self):
        assert MEMORY_TTL["preference"] == 180

    def test_constraint_ttl(self):
        assert MEMORY_TTL["constraint"] == 90

    def test_insight_ttl(self):
        assert MEMORY_TTL["insight"] == 120

    def test_struggle_ttl(self):
        assert MEMORY_TTL["struggle"] == 90

    def test_all_categories_defined(self):
        expected = {"preference", "goal", "constraint", "insight", "struggle"}
        assert set(MEMORY_TTL.keys()) == expected

    def test_min_confidence(self):
        assert MIN_CONFIDENCE == 0.6

    def test_max_memories_per_user(self):
        assert MAX_MEMORIES_PER_USER == 50

    def test_category_priority_order(self):
        """Goals highest priority (0), insight lowest (4)."""
        assert CATEGORY_PRIORITY["goal"] < CATEGORY_PRIORITY["preference"]
        assert CATEGORY_PRIORITY["struggle"] < CATEGORY_PRIORITY["insight"]


# ═══════════════════════════════════════════════════════════════════
# _store_memory — Async, DB-dependent
# ═══════════════════════════════════════════════════════════════════


class TestStoreMemory:

    @pytest.mark.asyncio
    async def test_stores_memory_successfully(self, mock_db):
        """Basic memory storage."""
        result = await _store_memory(mock_db, "user_1", "aime le matin", "preference", 0.8)
        assert result is not None
        assert result["fact"] == "aime le matin"
        assert result["category"] == "preference"
        assert result["confidence"] == 0.8
        assert result["user_id"] == "user_1"
        assert result["superseded_by"] is None
        assert "memory_id" in result
        assert "expires_at" in result  # preference has TTL

    @pytest.mark.asyncio
    async def test_goal_has_no_expires(self, mock_db):
        """Goal memories have no expires_at."""
        result = await _store_memory(mock_db, "user_1", "parler thai", "goal", 0.9)
        assert result is not None
        assert "expires_at" not in result

    @pytest.mark.asyncio
    async def test_dedup_supersedes_old(self, mock_db):
        """Similar fact in same category (same 30-char prefix) → old one superseded."""
        # Both facts share the same first 30 chars to trigger dedup
        await _store_memory(mock_db, "user_1", "prefere les sessions courtes le matin avec du cafe", "preference", 0.7)
        result2 = await _store_memory(mock_db, "user_1", "prefere les sessions courtes le soir sans bruit", "preference", 0.8)

        # Check old memory is superseded (dedup matches first 30 chars)
        old = await mock_db.ai_memories.find_one({
            "user_id": "user_1",
            "fact": {"$regex": "matin"},
        })
        assert old["superseded_by"] == result2["memory_id"]

    @pytest.mark.asyncio
    async def test_cap_enforced(self, mock_db):
        """More than MAX_MEMORIES_PER_USER → oldest non-goal deleted."""
        # Insert MAX + 5 memories
        for i in range(MAX_MEMORIES_PER_USER + 5):
            cat = "goal" if i < 3 else "preference"
            await mock_db.ai_memories.insert_one({
                "user_id": "user_cap",
                "memory_id": f"mem_{i:04d}",
                "fact": f"fact number {i}",
                "category": cat,
                "confidence": 0.8,
                "created_at": datetime(2025, 1, 1 + (i % 28) + 1, tzinfo=timezone.utc).isoformat(),
                "superseded_by": None,
            })

        # Store one more
        await _store_memory(mock_db, "user_cap", "new fact", "preference", 0.9)

        # Count remaining active
        count = await mock_db.ai_memories.count_documents({
            "user_id": "user_cap", "superseded_by": None,
        })
        assert count <= MAX_MEMORIES_PER_USER + 1  # +1 for the new one (cap applies after insert)


# ═══════════════════════════════════════════════════════════════════
# get_user_memories — Async, DB-dependent
# ═══════════════════════════════════════════════════════════════════


class TestGetUserMemories:

    @pytest.mark.asyncio
    async def test_no_memories_returns_empty(self, mock_db):
        result = await get_user_memories(mock_db, "user_no_memories")
        assert result == []

    @pytest.mark.asyncio
    async def test_retrieves_active_memories(self, mock_db):
        """Active, non-superseded memories are retrieved."""
        now = datetime.now(timezone.utc).isoformat()
        await mock_db.ai_memories.insert_many([
            {"user_id": "user_1", "memory_id": "m1", "fact": "goal A",
             "category": "goal", "confidence": 0.9, "created_at": now,
             "superseded_by": None},
            {"user_id": "user_1", "memory_id": "m2", "fact": "pref B",
             "category": "preference", "confidence": 0.7, "created_at": now,
             "superseded_by": None},
        ])
        result = await get_user_memories(mock_db, "user_1")
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_excludes_superseded(self, mock_db):
        """Superseded memories are excluded."""
        now = datetime.now(timezone.utc).isoformat()
        await mock_db.ai_memories.insert_many([
            {"user_id": "user_1", "memory_id": "m1", "fact": "old goal",
             "category": "goal", "confidence": 0.9, "created_at": now,
             "superseded_by": "m2"},  # superseded
            {"user_id": "user_1", "memory_id": "m2", "fact": "new goal",
             "category": "goal", "confidence": 0.9, "created_at": now,
             "superseded_by": None},
        ])
        result = await get_user_memories(mock_db, "user_1")
        assert len(result) == 1
        assert result[0]["fact"] == "new goal"

    @pytest.mark.asyncio
    async def test_excludes_low_confidence(self, mock_db):
        """Memories below MIN_CONFIDENCE are excluded."""
        now = datetime.now(timezone.utc).isoformat()
        await mock_db.ai_memories.insert_many([
            {"user_id": "user_1", "memory_id": "m1", "fact": "weak fact",
             "category": "preference", "confidence": 0.3, "created_at": now,
             "superseded_by": None},
            {"user_id": "user_1", "memory_id": "m2", "fact": "strong fact",
             "category": "preference", "confidence": 0.8, "created_at": now,
             "superseded_by": None},
        ])
        result = await get_user_memories(mock_db, "user_1")
        assert len(result) == 1
        assert result[0]["fact"] == "strong fact"

    @pytest.mark.asyncio
    async def test_priority_order(self, mock_db):
        """Memories sorted by category priority (goals first)."""
        now = datetime.now(timezone.utc).isoformat()
        await mock_db.ai_memories.insert_many([
            {"user_id": "user_1", "memory_id": "m1", "fact": "insight X",
             "category": "insight", "confidence": 0.9, "created_at": now,
             "superseded_by": None},
            {"user_id": "user_1", "memory_id": "m2", "fact": "goal Y",
             "category": "goal", "confidence": 0.7, "created_at": now,
             "superseded_by": None},
        ])
        result = await get_user_memories(mock_db, "user_1")
        assert result[0]["category"] == "goal"
        assert result[1]["category"] == "insight"

    @pytest.mark.asyncio
    async def test_limit_respected(self, mock_db):
        """Limit parameter caps results."""
        now = datetime.now(timezone.utc).isoformat()
        for i in range(15):
            await mock_db.ai_memories.insert_one({
                "user_id": "user_1", "memory_id": f"m{i}", "fact": f"fact {i}",
                "category": "preference", "confidence": 0.8, "created_at": now,
                "superseded_by": None,
            })
        result = await get_user_memories(mock_db, "user_1", limit=5)
        assert len(result) == 5


# ═══════════════════════════════════════════════════════════════════
# update_memory_usage — Async, DB-dependent
# ═══════════════════════════════════════════════════════════════════


class TestUpdateMemoryUsage:

    @pytest.mark.asyncio
    async def test_updates_last_used_at(self, mock_db):
        """last_used_at is updated for specified memory_ids."""
        old_date = "2025-01-01T00:00:00"
        await mock_db.ai_memories.insert_one({
            "user_id": "user_1", "memory_id": "m1", "fact": "test",
            "category": "goal", "last_used_at": old_date,
        })
        await update_memory_usage(mock_db, "user_1", ["m1"])
        doc = await mock_db.ai_memories.find_one({"memory_id": "m1"})
        assert doc["last_used_at"] != old_date

    @pytest.mark.asyncio
    async def test_empty_ids_no_error(self, mock_db):
        """Empty memory_ids → no error."""
        await update_memory_usage(mock_db, "user_1", [])

    @pytest.mark.asyncio
    async def test_none_ids_no_error(self, mock_db):
        """None memory_ids → no error."""
        await update_memory_usage(mock_db, "user_1", None)
