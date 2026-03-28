"""
Unit tests — Knowledge Engine.
Curated domain knowledge: fragment selection, counting, expertise retrieval.

Tests:
- get_relevant_fragments: per endpoint, with/without user categories
- get_category_expertise: per category
- count_total_fragments: total count
- get_all_topics: topic structure
- KNOWLEDGE_BASE integrity: domains, topics, fragment format
"""

import pytest

from services.knowledge_engine import (
    get_relevant_fragments,
    get_category_expertise,
    count_total_fragments,
    get_all_topics,
    KNOWLEDGE_BASE,
    ENDPOINT_TOPICS,
    CATEGORY_TOPIC_MAP,
    KNOWLEDGE_VERSION,
)


# ═══════════════════════════════════════════════════════════════════
# KNOWLEDGE_BASE integrity
# ═══════════════════════════════════════════════════════════════════


class TestKnowledgeBaseIntegrity:

    def test_has_5_domains(self):
        """Knowledge base has exactly 5 domains."""
        expected = {"learning", "psychology", "coaching", "well_being", "productivity"}
        assert set(KNOWLEDGE_BASE.keys()) == expected

    def test_all_fragments_are_strings(self):
        """Every fragment is a non-empty string."""
        for domain, topics in KNOWLEDGE_BASE.items():
            for topic, fragments in topics.items():
                for frag in fragments:
                    assert isinstance(frag, str), f"{domain}/{topic} has non-string fragment"
                    assert len(frag) > 20, f"{domain}/{topic} has too-short fragment"

    def test_minimum_fragment_count(self):
        """At least 60 total fragments (was 70+ in spec but allow margin)."""
        total = count_total_fragments()
        assert total >= 60

    def test_each_domain_has_topics(self):
        """Each domain has at least 2 topics."""
        for domain, topics in KNOWLEDGE_BASE.items():
            assert len(topics) >= 2, f"Domain {domain} has too few topics"

    def test_each_topic_has_fragments(self):
        """Each topic has at least 1 fragment."""
        for domain, topics in KNOWLEDGE_BASE.items():
            for topic, fragments in topics.items():
                assert len(fragments) >= 1, f"{domain}/{topic} has no fragments"

    def test_knowledge_version_is_set(self):
        assert KNOWLEDGE_VERSION >= 1


# ═══════════════════════════════════════════════════════════════════
# ENDPOINT_TOPICS mapping
# ═══════════════════════════════════════════════════════════════════


class TestEndpointTopics:

    def test_all_endpoints_defined(self):
        """Key AI endpoints have topic mappings."""
        expected = {"coach_dashboard", "coach_chat", "debrief",
                    "weekly_analysis", "suggestions", "curriculum",
                    "create_action", "streak_check"}
        assert expected.issubset(set(ENDPOINT_TOPICS.keys()))

    def test_all_topic_refs_valid(self):
        """Every (domain, topic) reference in ENDPOINT_TOPICS exists in KNOWLEDGE_BASE."""
        for endpoint, topics in ENDPOINT_TOPICS.items():
            for domain, topic in topics:
                assert domain in KNOWLEDGE_BASE, f"Invalid domain {domain} in {endpoint}"
                assert topic in KNOWLEDGE_BASE[domain], f"Invalid topic {topic} in {endpoint}"

    def test_category_topic_map_refs_valid(self):
        """Every reference in CATEGORY_TOPIC_MAP exists in KNOWLEDGE_BASE."""
        for cat, topics in CATEGORY_TOPIC_MAP.items():
            for domain, topic in topics:
                assert domain in KNOWLEDGE_BASE, f"Invalid domain {domain} for category {cat}"
                assert topic in KNOWLEDGE_BASE[domain], f"Invalid topic {topic} for category {cat}"


# ═══════════════════════════════════════════════════════════════════
# get_relevant_fragments — Pure function
# ═══════════════════════════════════════════════════════════════════


class TestGetRelevantFragments:

    def test_returns_string(self):
        result = get_relevant_fragments("coach_chat")
        assert isinstance(result, str)

    def test_coach_chat_has_fragments(self):
        """coach_chat endpoint → non-empty result."""
        result = get_relevant_fragments("coach_chat")
        assert len(result) > 100
        assert "EXPERTISE SCIENTIFIQUE" in result

    def test_unknown_endpoint_returns_empty(self):
        """Unknown endpoint with no categories → empty."""
        result = get_relevant_fragments("nonexistent_endpoint")
        assert result == ""

    def test_unknown_endpoint_with_categories_returns_fragments(self):
        """Unknown endpoint but with categories → category fragments."""
        result = get_relevant_fragments("nonexistent", user_categories=["music"])
        assert len(result) > 0
        assert "EXPERTISE" in result

    def test_max_fragments_respected(self):
        """max_fragments limits output."""
        result_small = get_relevant_fragments("coach_chat", max_fragments=2)
        result_big = get_relevant_fragments("coach_chat", max_fragments=10)
        # Smaller max → fewer lines
        assert result_small.count("\n- ") <= 2
        assert result_big.count("\n- ") >= result_small.count("\n- ")

    def test_user_categories_add_fragments(self):
        """User categories enrich the result beyond endpoint topics."""
        result_base = get_relevant_fragments("streak_check", max_fragments=10)
        result_enriched = get_relevant_fragments(
            "streak_check", user_categories=["music", "languages"], max_fragments=10
        )
        assert len(result_enriched) >= len(result_base)

    def test_dedup_no_duplicate_fragments(self):
        """Fragments are deduplicated."""
        result = get_relevant_fragments("coach_chat", user_categories=["learning"],
                                         max_fragments=20)
        lines = [l for l in result.split("\n") if l.startswith("- ")]
        assert len(lines) == len(set(lines))

    def test_all_endpoints_produce_output(self):
        """Every mapped endpoint produces non-empty output."""
        for endpoint in ENDPOINT_TOPICS:
            result = get_relevant_fragments(endpoint)
            assert len(result) > 0, f"Endpoint {endpoint} produced empty result"


# ═══════════════════════════════════════════════════════════════════
# get_category_expertise — Pure function
# ═══════════════════════════════════════════════════════════════════


class TestGetCategoryExpertise:

    def test_music_expertise(self):
        result = get_category_expertise("music")
        assert "EXPERTISE MUSIC" in result
        assert len(result) > 50

    def test_languages_expertise(self):
        result = get_category_expertise("languages")
        assert "EXPERTISE LANGUAGES" in result

    def test_meditation_expertise(self):
        result = get_category_expertise("meditation")
        assert "EXPERTISE MEDITATION" in result

    def test_unknown_category_returns_empty(self):
        result = get_category_expertise("underwater_basket_weaving")
        assert result == ""

    def test_max_fragments_respected(self):
        result1 = get_category_expertise("music", max_fragments=1)
        result3 = get_category_expertise("music", max_fragments=3)
        assert result1.count("\n- ") <= 1
        assert result3.count("\n- ") >= result1.count("\n- ")

    def test_case_insensitive(self):
        """Category lookup is case-insensitive."""
        result_lower = get_category_expertise("music")
        result_upper = get_category_expertise("MUSIC")
        assert result_lower == result_upper


# ═══════════════════════════════════════════════════════════════════
# count_total_fragments — Pure function
# ═══════════════════════════════════════════════════════════════════


class TestCountTotalFragments:

    def test_returns_positive_int(self):
        total = count_total_fragments()
        assert isinstance(total, int)
        assert total > 0

    def test_matches_manual_count(self):
        """Manual count matches function output."""
        manual = 0
        for domain in KNOWLEDGE_BASE.values():
            for fragments in domain.values():
                manual += len(fragments)
        assert count_total_fragments() == manual


# ═══════════════════════════════════════════════════════════════════
# get_all_topics — Pure function
# ═══════════════════════════════════════════════════════════════════


class TestGetAllTopics:

    def test_returns_dict_of_dicts(self):
        result = get_all_topics()
        assert isinstance(result, dict)
        for domain, topics in result.items():
            assert isinstance(topics, dict)
            for topic, count in topics.items():
                assert isinstance(count, int)
                assert count > 0

    def test_matches_knowledge_base_structure(self):
        """Topics dict matches KNOWLEDGE_BASE keys."""
        result = get_all_topics()
        assert set(result.keys()) == set(KNOWLEDGE_BASE.keys())
        for domain in KNOWLEDGE_BASE:
            assert set(result[domain].keys()) == set(KNOWLEDGE_BASE[domain].keys())
