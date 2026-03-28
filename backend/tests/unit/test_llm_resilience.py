"""
Unit tests — LLM Provider Resilience.
Retry logic, circuit breaker, backoff computation.

Tests:
- CircuitBreaker: state transitions (CLOSED → OPEN → HALF_OPEN → CLOSED)
- _compute_delay: exponential backoff with jitter
- Retry config: constants validation
"""

import time
import pytest

from services.llm_provider import (
    CircuitBreaker,
    CircuitState,
    _compute_delay,
    get_circuit_breaker_status,
    MAX_RETRIES,
    BASE_DELAY_S,
    MAX_DELAY_S,
    RETRYABLE_STATUS_CODES,
    CB_FAILURE_THRESHOLD,
    CB_RECOVERY_TIMEOUT_S,
)


# ═══════════════════════════════════════════════════════════════════
# CircuitBreaker — State machine tests
# ═══════════════════════════════════════════════════════════════════


class TestCircuitBreaker:

    def test_initial_state_is_closed(self):
        cb = CircuitBreaker("test")
        assert cb.state == CircuitState.CLOSED
        assert cb.consecutive_failures == 0

    def test_can_execute_when_closed(self):
        cb = CircuitBreaker("test")
        assert cb.can_execute() is True

    def test_stays_closed_below_threshold(self):
        cb = CircuitBreaker("test")
        for _ in range(CB_FAILURE_THRESHOLD - 1):
            cb.record_failure()
        assert cb.state == CircuitState.CLOSED
        assert cb.can_execute() is True

    def test_trips_open_at_threshold(self):
        cb = CircuitBreaker("test")
        for _ in range(CB_FAILURE_THRESHOLD):
            cb.record_failure()
        assert cb.state == CircuitState.OPEN
        assert cb.can_execute() is False

    def test_open_rejects_calls(self):
        cb = CircuitBreaker("test")
        for _ in range(CB_FAILURE_THRESHOLD):
            cb.record_failure()
        assert cb.can_execute() is False

    def test_open_to_half_open_after_timeout(self):
        cb = CircuitBreaker("test")
        for _ in range(CB_FAILURE_THRESHOLD):
            cb.record_failure()
        assert cb.state == CircuitState.OPEN

        # Simulate timeout elapsed
        cb.last_failure_time = time.monotonic() - CB_RECOVERY_TIMEOUT_S - 1
        assert cb.can_execute() is True
        assert cb.state == CircuitState.HALF_OPEN

    def test_half_open_success_resets_to_closed(self):
        cb = CircuitBreaker("test")
        cb.state = CircuitState.HALF_OPEN
        cb.consecutive_failures = CB_FAILURE_THRESHOLD
        cb.record_success()
        assert cb.state == CircuitState.CLOSED
        assert cb.consecutive_failures == 0

    def test_half_open_failure_trips_back_to_open(self):
        cb = CircuitBreaker("test")
        cb.state = CircuitState.HALF_OPEN
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

    def test_success_resets_failure_count(self):
        cb = CircuitBreaker("test")
        cb.record_failure()
        cb.record_failure()
        assert cb.consecutive_failures == 2
        cb.record_success()
        assert cb.consecutive_failures == 0

    def test_closed_success_stays_closed(self):
        cb = CircuitBreaker("test")
        cb.record_success()
        assert cb.state == CircuitState.CLOSED


# ═══════════════════════════════════════════════════════════════════
# _compute_delay — Backoff computation
# ═══════════════════════════════════════════════════════════════════


class TestComputeDelay:

    def test_first_attempt_near_base(self):
        """Attempt 0 → delay around BASE_DELAY_S (±jitter)."""
        delays = [_compute_delay(0) for _ in range(20)]
        avg = sum(delays) / len(delays)
        assert 0.3 < avg < 2.0

    def test_increases_with_attempts(self):
        """Higher attempts → higher average delay."""
        avg_0 = sum(_compute_delay(0) for _ in range(50)) / 50
        avg_2 = sum(_compute_delay(2) for _ in range(50)) / 50
        assert avg_2 > avg_0

    def test_capped_at_max(self):
        """Delay never exceeds MAX_DELAY_S + jitter."""
        for _ in range(100):
            d = _compute_delay(10)  # Very high attempt
            assert d <= MAX_DELAY_S * 1.6  # Max + max jitter

    def test_always_positive(self):
        """Delay is always > 0."""
        for attempt in range(10):
            for _ in range(20):
                assert _compute_delay(attempt) > 0

    def test_jitter_produces_variation(self):
        """Same attempt → different delays (jitter working)."""
        delays = {_compute_delay(1) for _ in range(10)}
        assert len(delays) >= 5  # Should be mostly unique


# ═══════════════════════════════════════════════════════════════════
# Configuration validation
# ═══════════════════════════════════════════════════════════════════


class TestRetryConfig:

    def test_max_retries_reasonable(self):
        assert 1 <= MAX_RETRIES <= 5

    def test_base_delay_reasonable(self):
        assert 0.5 <= BASE_DELAY_S <= 3.0

    def test_max_delay_capped(self):
        assert MAX_DELAY_S <= 30.0

    def test_retryable_codes_include_overload(self):
        assert 429 in RETRYABLE_STATUS_CODES
        assert 529 in RETRYABLE_STATUS_CODES
        assert 503 in RETRYABLE_STATUS_CODES

    def test_retryable_codes_exclude_client_errors(self):
        assert 400 not in RETRYABLE_STATUS_CODES
        assert 401 not in RETRYABLE_STATUS_CODES
        assert 403 not in RETRYABLE_STATUS_CODES
        assert 404 not in RETRYABLE_STATUS_CODES

    def test_circuit_breaker_threshold_reasonable(self):
        assert 3 <= CB_FAILURE_THRESHOLD <= 10

    def test_recovery_timeout_reasonable(self):
        assert 10 <= CB_RECOVERY_TIMEOUT_S <= 120


# ═══════════════════════════════════════════════════════════════════
# get_circuit_breaker_status — Admin endpoint support
# ═══════════════════════════════════════════════════════════════════


class TestGetCircuitBreakerStatus:

    def test_returns_dict(self):
        result = get_circuit_breaker_status()
        assert isinstance(result, dict)

    def test_status_has_expected_fields(self):
        # Trigger creation of a breaker
        cb = CircuitBreaker("test_status")
        from services.llm_provider import _circuit_breakers
        _circuit_breakers["test_status"] = cb

        result = get_circuit_breaker_status()
        assert "test_status" in result
        status = result["test_status"]
        assert "state" in status
        assert "consecutive_failures" in status
        assert status["state"] == "closed"

        # Cleanup
        del _circuit_breakers["test_status"]
