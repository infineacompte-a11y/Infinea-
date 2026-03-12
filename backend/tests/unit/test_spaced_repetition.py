"""
Unit tests — Spaced Repetition SM-2 algorithm.
P1 critical service: ensures learning intervals are computed correctly.

Tests:
- compute_next_review: all quality levels, edge cases, ease floor, interval cap
- get_review_queue: overdue sorting, date parsing, empty queue
- record_review: full cycle with mocked DB
- seed_reviews_from_curriculum: bootstrap from curriculum progress
"""

import pytest
from datetime import datetime, timezone, timedelta

from services.spaced_repetition import (
    compute_next_review,
    get_review_queue,
    get_or_init_review,
    record_review,
    seed_reviews_from_curriculum,
    DEFAULT_EASE_FACTOR,
    MIN_EASE_FACTOR,
    INITIAL_INTERVALS,
)


# ═══════════════════════════════════════════════════════════════════
# compute_next_review — Pure function tests (no DB)
# ═══════════════════════════════════════════════════════════════════


class TestComputeNextReview:
    """SM-2 algorithm correctness."""

    def test_first_successful_review(self):
        """First review (rep=0, quality>=3) → interval = 1 day."""
        result = compute_next_review(repetitions=0, ease_factor=2.5, quality=4)
        assert result["next_interval"] == INITIAL_INTERVALS[0]  # 1 day
        assert result["repetitions"] == 1

    def test_second_successful_review(self):
        """Second review (rep=1, quality>=3) → interval = 3 days."""
        result = compute_next_review(repetitions=1, ease_factor=2.5, quality=4)
        assert result["next_interval"] == INITIAL_INTERVALS[1]  # 3 days
        assert result["repetitions"] == 2

    def test_third_review_uses_ease_factor(self):
        """Third+ review multiplies previous interval by ease factor."""
        result = compute_next_review(
            repetitions=2, ease_factor=2.5, quality=4, previous_interval=3
        )
        # 3 * 2.5 = 7.5 → rounds to 8
        assert result["next_interval"] == 8
        assert result["repetitions"] == 3

    def test_failed_review_resets(self):
        """Quality < 3 resets repetitions to 0 and interval to 1."""
        result = compute_next_review(
            repetitions=5, ease_factor=2.5, quality=2, previous_interval=30
        )
        assert result["next_interval"] == INITIAL_INTERVALS[0]  # 1
        assert result["repetitions"] == 0

    def test_quality_1_total_blackout(self):
        """Quality 1 (worst) resets and drops ease factor."""
        result = compute_next_review(repetitions=3, ease_factor=2.5, quality=1)
        assert result["repetitions"] == 0
        assert result["ease_factor"] < 2.5

    def test_quality_5_perfect_recall(self):
        """Quality 5 (best) increases ease factor."""
        result = compute_next_review(repetitions=2, ease_factor=2.5, quality=5)
        assert result["ease_factor"] > 2.5

    def test_ease_factor_floor(self):
        """Ease factor never drops below MIN_EASE_FACTOR (1.3)."""
        # Repeatedly fail → ease should floor at 1.3
        ease = 1.4
        for _ in range(10):
            result = compute_next_review(repetitions=0, ease_factor=ease, quality=1)
            ease = result["ease_factor"]
        assert ease >= MIN_EASE_FACTOR

    def test_interval_cap_180_days(self):
        """Interval capped at 180 days (6 months)."""
        result = compute_next_review(
            repetitions=10, ease_factor=2.5, quality=5, previous_interval=100
        )
        assert result["next_interval"] <= 180

    def test_quality_clamped_to_valid_range(self):
        """Quality outside 1-5 is clamped."""
        # Quality 0 → treated as 1
        result_low = compute_next_review(repetitions=0, ease_factor=2.5, quality=0)
        assert result_low["repetitions"] == 0  # Failed (quality < 3)

        # Quality 10 → treated as 5
        result_high = compute_next_review(repetitions=0, ease_factor=2.5, quality=10)
        assert result_high["repetitions"] == 1  # Success (quality >= 3)

    @pytest.mark.parametrize("quality", [1, 2, 3, 4, 5])
    def test_all_quality_levels_produce_valid_output(self, quality):
        """Every quality level returns a valid result dict."""
        result = compute_next_review(
            repetitions=2, ease_factor=2.5, quality=quality, previous_interval=7
        )
        assert "next_interval" in result
        assert "ease_factor" in result
        assert "repetitions" in result
        assert result["next_interval"] >= 1
        assert result["ease_factor"] >= MIN_EASE_FACTOR
        assert result["repetitions"] >= 0

    def test_ease_factor_progression_quality_3(self):
        """Quality 3 (borderline) slightly decreases ease factor."""
        result = compute_next_review(repetitions=2, ease_factor=2.5, quality=3)
        # SM-2: EF' = EF + (0.1 - (5-3)*(0.08 + (5-3)*0.02)) = 2.5 + 0.1 - 0.24 = 2.36
        assert result["ease_factor"] < 2.5

    def test_long_chain_convergence(self):
        """Simulate 20 successful reviews — interval grows, ease stabilizes."""
        reps = 0
        ease = DEFAULT_EASE_FACTOR
        interval = 0
        for _ in range(20):
            result = compute_next_review(reps, ease, quality=4, previous_interval=interval)
            reps = result["repetitions"]
            ease = result["ease_factor"]
            interval = result["next_interval"]
        # After 20 perfect reviews, interval should be substantial
        assert interval > 30
        assert interval <= 180
        assert ease >= MIN_EASE_FACTOR


# ═══════════════════════════════════════════════════════════════════
# get_review_queue — DB-dependent (mock)
# ═══════════════════════════════════════════════════════════════════


class TestGetReviewQueue:
    """Review queue retrieval and sorting."""

    @pytest.mark.asyncio
    async def test_empty_queue(self, mock_db):
        """No reviews → empty queue."""
        queue = await get_review_queue(mock_db, "user_1", "obj_1")
        assert queue == []

    @pytest.mark.asyncio
    async def test_overdue_reviews_sorted(self, mock_db):
        """Overdue reviews sorted by most overdue first."""
        now = datetime.now(timezone.utc)
        await mock_db.sr_reviews.insert_many([
            {
                "user_id": "user_1",
                "objective_id": "obj_1",
                "skill": "vocabulary",
                "next_review_date": (now - timedelta(days=5)).isoformat(),
                "ease_factor": 2.5,
                "repetitions": 2,
                "interval_days": 3,
            },
            {
                "user_id": "user_1",
                "objective_id": "obj_1",
                "skill": "grammar",
                "next_review_date": (now - timedelta(days=1)).isoformat(),
                "ease_factor": 2.3,
                "repetitions": 1,
                "interval_days": 1,
            },
        ])

        queue = await get_review_queue(mock_db, "user_1", "obj_1")
        assert len(queue) == 2
        assert queue[0]["skill"] == "vocabulary"  # 5 days overdue
        assert queue[1]["skill"] == "grammar"  # 1 day overdue
        assert queue[0]["days_overdue"] >= 5

    @pytest.mark.asyncio
    async def test_future_reviews_excluded(self, mock_db):
        """Reviews not yet due are excluded from queue."""
        future = datetime.now(timezone.utc) + timedelta(days=5)
        await mock_db.sr_reviews.insert_one({
            "user_id": "user_1",
            "objective_id": "obj_1",
            "skill": "reading",
            "next_review_date": future.isoformat(),
        })

        queue = await get_review_queue(mock_db, "user_1", "obj_1")
        assert len(queue) == 0

    @pytest.mark.asyncio
    async def test_missing_next_review_date_skipped(self, mock_db):
        """Reviews without next_review_date are skipped."""
        await mock_db.sr_reviews.insert_one({
            "user_id": "user_1",
            "objective_id": "obj_1",
            "skill": "writing",
            # No next_review_date
        })

        queue = await get_review_queue(mock_db, "user_1", "obj_1")
        assert len(queue) == 0

    @pytest.mark.asyncio
    async def test_different_objective_isolated(self, mock_db):
        """Reviews for different objectives don't mix."""
        now = datetime.now(timezone.utc) - timedelta(days=1)
        await mock_db.sr_reviews.insert_many([
            {
                "user_id": "user_1",
                "objective_id": "obj_1",
                "skill": "skill_a",
                "next_review_date": now.isoformat(),
            },
            {
                "user_id": "user_1",
                "objective_id": "obj_2",
                "skill": "skill_b",
                "next_review_date": now.isoformat(),
            },
        ])

        queue = await get_review_queue(mock_db, "user_1", "obj_1")
        assert len(queue) == 1
        assert queue[0]["skill"] == "skill_a"


# ═══════════════════════════════════════════════════════════════════
# get_or_init_review — DB-dependent
# ═══════════════════════════════════════════════════════════════════


class TestGetOrInitReview:

    @pytest.mark.asyncio
    async def test_creates_new_review(self, mock_db):
        """Creates a new review if none exists."""
        review = await get_or_init_review(mock_db, "user_1", "obj_1", "vocabulary")
        assert review["skill"] == "vocabulary"
        assert review["ease_factor"] == DEFAULT_EASE_FACTOR
        assert review["repetitions"] == 0

        # Should be persisted
        stored = await mock_db.sr_reviews.find_one({"skill": "vocabulary"})
        assert stored is not None

    @pytest.mark.asyncio
    async def test_returns_existing_review(self, mock_db):
        """Returns existing review without creating duplicate."""
        await mock_db.sr_reviews.insert_one({
            "user_id": "user_1",
            "objective_id": "obj_1",
            "skill": "grammar",
            "ease_factor": 2.0,
            "repetitions": 3,
        })

        review = await get_or_init_review(mock_db, "user_1", "obj_1", "grammar")
        assert review["ease_factor"] == 2.0
        assert review["repetitions"] == 3

        # No duplicate created
        count = await mock_db.sr_reviews.count_documents({"skill": "grammar"})
        assert count == 1


# ═══════════════════════════════════════════════════════════════════
# record_review — Full cycle (DB-dependent)
# ═══════════════════════════════════════════════════════════════════


class TestRecordReview:

    @pytest.mark.asyncio
    async def test_successful_review_updates_state(self, mock_db):
        """Quality 4 review updates interval and next review date."""
        result = await record_review(mock_db, "user_1", "obj_1", "vocab", quality=4)

        assert result["skill"] == "vocab"
        assert result["quality"] == 4
        assert result["next_interval_days"] == INITIAL_INTERVALS[0]  # First review
        assert result["repetitions"] == 1
        assert "next_review_date" in result

    @pytest.mark.asyncio
    async def test_two_consecutive_reviews(self, mock_db):
        """Two successful reviews → increasing intervals."""
        r1 = await record_review(mock_db, "user_1", "obj_1", "vocab", quality=4)
        assert r1["next_interval_days"] == 1  # First

        r2 = await record_review(mock_db, "user_1", "obj_1", "vocab", quality=4)
        assert r2["next_interval_days"] == 3  # Second
        assert r2["repetitions"] == 2

    @pytest.mark.asyncio
    async def test_failed_review_resets_progress(self, mock_db):
        """After several successes, a failure resets."""
        # Build up
        await record_review(mock_db, "user_1", "obj_1", "vocab", quality=5)
        await record_review(mock_db, "user_1", "obj_1", "vocab", quality=5)

        # Fail
        r = await record_review(mock_db, "user_1", "obj_1", "vocab", quality=1)
        assert r["repetitions"] == 0
        assert r["next_interval_days"] == 1


# ═══════════════════════════════════════════════════════════════════
# seed_reviews_from_curriculum — Bootstrap
# ═══════════════════════════════════════════════════════════════════


class TestSeedReviewsFromCurriculum:

    @pytest.mark.asyncio
    async def test_seeds_completed_steps(self, mock_db):
        """Completed curriculum steps with focus are seeded."""
        now = datetime.now(timezone.utc)
        curriculum = [
            {"focus": "vocabulary", "completed": True, "completed_at": (now - timedelta(days=1)).isoformat()},
            {"focus": "grammar", "completed": True, "completed_at": (now - timedelta(days=2)).isoformat()},
            {"focus": "reading", "completed": False},  # Not completed
        ]

        count = await seed_reviews_from_curriculum(mock_db, "user_1", "obj_1", curriculum)
        assert count == 2

        reviews = await mock_db.sr_reviews.find({"user_id": "user_1"}).to_list(10)
        skills = {r["skill"] for r in reviews}
        assert skills == {"vocabulary", "grammar"}

    @pytest.mark.asyncio
    async def test_skips_existing_reviews(self, mock_db):
        """Does not duplicate already-tracked skills."""
        await mock_db.sr_reviews.insert_one({
            "user_id": "user_1",
            "objective_id": "obj_1",
            "skill": "vocabulary",
            "ease_factor": 2.5,
        })

        curriculum = [
            {"focus": "vocabulary", "completed": True, "completed_at": datetime.now(timezone.utc).isoformat()},
        ]

        count = await seed_reviews_from_curriculum(mock_db, "user_1", "obj_1", curriculum)
        assert count == 0

    @pytest.mark.asyncio
    async def test_empty_curriculum(self, mock_db):
        """Empty curriculum seeds nothing."""
        count = await seed_reviews_from_curriculum(mock_db, "user_1", "obj_1", [])
        assert count == 0

    @pytest.mark.asyncio
    async def test_overdue_seeds_review_now(self, mock_db):
        """Steps completed >3 days ago are marked for immediate review."""
        old_date = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
        curriculum = [
            {"focus": "old_skill", "completed": True, "completed_at": old_date},
        ]

        await seed_reviews_from_curriculum(mock_db, "user_1", "obj_1", curriculum)

        review = await mock_db.sr_reviews.find_one({"skill": "old_skill"})
        next_date = datetime.fromisoformat(review["next_review_date"])
        if next_date.tzinfo is None:
            next_date = next_date.replace(tzinfo=timezone.utc)
        # Should be due now or in the past (immediate review)
        assert next_date <= datetime.now(timezone.utc) + timedelta(seconds=5)

    @pytest.mark.asyncio
    async def test_steps_without_focus_skipped(self, mock_db):
        """Steps with empty or missing focus are skipped."""
        curriculum = [
            {"focus": "", "completed": True, "completed_at": datetime.now(timezone.utc).isoformat()},
            {"focus": None, "completed": True, "completed_at": datetime.now(timezone.utc).isoformat()},
            {"completed": True, "completed_at": datetime.now(timezone.utc).isoformat()},
        ]

        count = await seed_reviews_from_curriculum(mock_db, "user_1", "obj_1", curriculum)
        assert count == 0
