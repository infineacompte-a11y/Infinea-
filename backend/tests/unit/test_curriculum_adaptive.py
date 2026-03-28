"""
Unit tests — Adaptive Curriculum.
Performance analysis and difficulty calibration for weekly curriculum generation.

Tests:
- analyze_week_performance: all adjustment types
- Edge cases: empty curriculum, no completed steps, partial data
"""

import pytest

from services.curriculum_engine import analyze_week_performance


# ═══════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════

def _make_step(day, completed=True, difficulty=2, performance="normal",
               actual_duration=7, duration_min=5, duration_max=10):
    return {
        "day": day,
        "completed": completed,
        "difficulty": difficulty,
        "performance": performance,
        "actual_duration": actual_duration,
        "duration_min": duration_min,
        "duration_max": duration_max,
        "title": f"Session jour {day}",
    }


# ═══════════════════════════════════════════════════════════════════
# analyze_week_performance — Pure function
# ═══════════════════════════════════════════════════════════════════


class TestAnalyzeWeekPerformance:

    def test_no_data_returns_none_adjustment(self):
        """Empty curriculum → no adjustment."""
        result = analyze_week_performance([], 0)
        assert result["adjustment"] == "none"

    def test_increase_when_high_completion_fast(self):
        """High completion + many fast steps → increase difficulty."""
        curriculum = [
            _make_step(d, completed=True, performance="fast")
            for d in range(1, 8)
        ]
        result = analyze_week_performance(curriculum, 7)
        assert result["adjustment"] == "increase"
        assert result["difficulty_delta"] == 1

    def test_decrease_when_low_completion(self):
        """Low completion rate → decrease difficulty."""
        curriculum = [
            _make_step(1, completed=True),
            _make_step(2, completed=True),
            _make_step(3, completed=False, performance="abandoned"),
            _make_step(4, completed=False, performance="abandoned"),
            _make_step(5, completed=False, performance="abandoned"),
            _make_step(6, completed=False, performance="abandoned"),
            _make_step(7, completed=True),
        ]
        result = analyze_week_performance(curriculum, 7)
        assert result["adjustment"] == "decrease"
        assert result["difficulty_delta"] == -1

    def test_simplify_when_sessions_too_long(self):
        """Many slow sessions → simplify."""
        curriculum = [
            _make_step(d, completed=True, performance="slow")
            for d in range(1, 8)
        ]
        result = analyze_week_performance(curriculum, 7)
        assert result["adjustment"] == "simplify"

    def test_maintain_stable_performance(self):
        """Normal performance → maintain."""
        curriculum = [
            _make_step(d, completed=True, performance="normal")
            for d in range(1, 8)
        ]
        result = analyze_week_performance(curriculum, 7)
        assert result["adjustment"] in ("maintain", "slight_increase")

    def test_good_pace_slight_increase(self):
        """Good completion, normal duration → slight_increase or maintain."""
        curriculum = [
            _make_step(d, completed=True, performance="normal", actual_duration=7)
            for d in range(1, 8)
        ]
        result = analyze_week_performance(curriculum, 7)
        assert result["adjustment"] in ("slight_increase", "maintain")

    def test_analysis_fields_present(self):
        """Result has all expected fields."""
        curriculum = [_make_step(d) for d in range(1, 8)]
        result = analyze_week_performance(curriculum, 7)
        assert "completion_rate" in result
        assert "avg_difficulty" in result
        assert "avg_duration_ratio" in result
        assert "fast_count" in result
        assert "slow_count" in result
        assert "abandoned_count" in result
        assert "steps_analyzed" in result
        assert "adjustment" in result
        assert "coach_note" in result

    def test_only_analyzes_last_7(self):
        """With > 7 steps, only last 7 are analyzed."""
        curriculum = [_make_step(d) for d in range(1, 15)]
        result = analyze_week_performance(curriculum, 14)
        assert result["steps_analyzed"] == 7

    def test_partial_week(self):
        """Fewer than 7 steps → still works."""
        curriculum = [_make_step(d) for d in range(1, 4)]
        result = analyze_week_performance(curriculum, 3)
        assert result["steps_analyzed"] == 3
        assert result["adjustment"] != "none"

    def test_completion_rate_calculation(self):
        """Completion rate is correctly computed."""
        curriculum = [
            _make_step(1, completed=True),
            _make_step(2, completed=True),
            _make_step(3, completed=False),
            _make_step(4, completed=True),
        ]
        result = analyze_week_performance(curriculum, 4)
        assert result["completion_rate"] == 0.75

    def test_difficulty_average(self):
        """Average difficulty computed from completed steps only."""
        curriculum = [
            _make_step(1, completed=True, difficulty=2),
            _make_step(2, completed=True, difficulty=4),
            _make_step(3, completed=False, difficulty=5),  # not counted
        ]
        result = analyze_week_performance(curriculum, 3)
        assert result["avg_difficulty"] == 3.0
