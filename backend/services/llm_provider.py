"""
InFinea — LLM Provider Abstraction.

Provider-agnostic interface for AI calls. Currently wraps Anthropic Claude API.
Designed for zero-friction migration to any provider (OpenAI, Mistral, Groq).

Key design decisions:
- No SDK dependency (uses httpx directly)
- Provider config via LLM_PROVIDER env var (default: anthropic)
- Unified ModelTier system (FAST/SMART/EXTRACT) instead of model IDs
- Correct cache_control placement on system content blocks
- Unified token tracking regardless of provider
- Retry with exponential backoff + jitter (AWS SDK pattern)
- Circuit breaker with half-open recovery (Netflix Hystrix pattern)
"""

import os
import time
import random
import asyncio
import logging
from enum import Enum
from typing import Optional
from datetime import datetime, timezone

import httpx

logger = logging.getLogger("infinea")


# ═══════════════════════════════════════════════════════════════════════════
# RETRY + CIRCUIT BREAKER
# Benchmarks: AWS SDK (exponential backoff + jitter), Netflix Hystrix
# (circuit breaker), Stripe (idempotent retries)
# ═══════════════════════════════════════════════════════════════════════════

# Retry config
MAX_RETRIES = 3
BASE_DELAY_S = 1.0       # 1s base delay
MAX_DELAY_S = 8.0        # Cap at 8s
JITTER_FACTOR = 0.5      # ±50% randomization (decorrelated jitter)

# HTTP status codes that warrant a retry (transient errors)
RETRYABLE_STATUS_CODES = {
    429,  # Rate limited
    500,  # Internal server error
    502,  # Bad gateway
    503,  # Service unavailable
    529,  # Anthropic overloaded
}

# Circuit breaker config (Hystrix-inspired)
CB_FAILURE_THRESHOLD = 5     # Consecutive failures to trip
CB_RECOVERY_TIMEOUT_S = 30   # Seconds before half-open probe
CB_HALF_OPEN_MAX = 1         # Probes allowed in half-open state


class CircuitState(str, Enum):
    CLOSED = "closed"          # Normal operation
    OPEN = "open"              # All calls rejected, waiting for recovery
    HALF_OPEN = "half_open"    # One probe allowed to test recovery


class CircuitBreaker:
    """Per-provider circuit breaker.

    State machine:
    CLOSED → (failures >= threshold) → OPEN
    OPEN → (recovery_timeout elapsed) → HALF_OPEN
    HALF_OPEN → (probe succeeds) → CLOSED
    HALF_OPEN → (probe fails) → OPEN
    """

    def __init__(self, name: str):
        self.name = name
        self.state = CircuitState.CLOSED
        self.consecutive_failures = 0
        self.last_failure_time = 0.0
        self.half_open_probes = 0

    def can_execute(self) -> bool:
        """Check if a call is allowed through the breaker."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has elapsed
            if time.monotonic() - self.last_failure_time >= CB_RECOVERY_TIMEOUT_S:
                self.state = CircuitState.HALF_OPEN
                self.half_open_probes = 0
                logger.info(f"Circuit breaker [{self.name}]: OPEN → HALF_OPEN")
                return True
            return False

        if self.state == CircuitState.HALF_OPEN:
            # Allow limited probes
            return self.half_open_probes < CB_HALF_OPEN_MAX

        return False

    def record_success(self):
        """Record a successful call — reset breaker if needed."""
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            logger.info(f"Circuit breaker [{self.name}]: HALF_OPEN → CLOSED (recovered)")
            # Fire-and-forget Slack alert on recovery
            try:
                import asyncio
                from services.alerts import alert_circuit_breaker_recovered
                asyncio.create_task(alert_circuit_breaker_recovered(self.name))
            except Exception:
                pass
        self.consecutive_failures = 0

    def record_failure(self):
        """Record a failed call — trip breaker if threshold reached."""
        self.consecutive_failures += 1
        self.last_failure_time = time.monotonic()

        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker [{self.name}]: HALF_OPEN → OPEN (probe failed)")
        elif (self.state == CircuitState.CLOSED
              and self.consecutive_failures >= CB_FAILURE_THRESHOLD):
            self.state = CircuitState.OPEN
            logger.warning(
                f"Circuit breaker [{self.name}]: CLOSED → OPEN "
                f"({self.consecutive_failures} consecutive failures)"
            )
            # Fire-and-forget Slack alert
            try:
                import asyncio
                from services.alerts import alert_circuit_breaker_opened
                asyncio.create_task(alert_circuit_breaker_opened(self.name, self.consecutive_failures))
            except Exception:
                pass

        if self.state == CircuitState.HALF_OPEN:
            self.half_open_probes += 1


# One breaker per provider
_circuit_breakers: dict[str, CircuitBreaker] = {}


def _get_breaker(provider: str) -> CircuitBreaker:
    if provider not in _circuit_breakers:
        _circuit_breakers[provider] = CircuitBreaker(provider)
    return _circuit_breakers[provider]


def _compute_delay(attempt: int) -> float:
    """Exponential backoff with decorrelated jitter (AWS pattern).
    attempt 0 → ~1s, attempt 1 → ~2s, attempt 2 → ~4s
    """
    base = min(BASE_DELAY_S * (2 ** attempt), MAX_DELAY_S)
    jitter = base * JITTER_FACTOR * (2 * random.random() - 1)
    return max(0.1, base + jitter)


# ── Provider & Model Configuration ──

class LLMProvider(str, Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"


class ModelTier(str, Enum):
    FAST = "fast"        # Haiku / GPT-4o-mini — cheap, fast
    SMART = "smart"      # Sonnet / GPT-4o — better reasoning
    EXTRACT = "extract"  # Cheapest available — for memory extraction


MODEL_MAP = {
    LLMProvider.ANTHROPIC: {
        ModelTier.FAST: "claude-haiku-4-5-20251001",
        ModelTier.SMART: "claude-sonnet-4-20250514",
        ModelTier.EXTRACT: "claude-haiku-4-5-20251001",
    },
    LLMProvider.OPENAI: {
        ModelTier.FAST: "gpt-4o-mini",
        ModelTier.SMART: "gpt-4o",
        ModelTier.EXTRACT: "gpt-4o-mini",
    },
}

# Pricing per million tokens (USD)
PRICING = {
    "claude-haiku-4-5-20251001": {
        "input": 1.00, "output": 5.00,
        "cache_write": 1.25, "cache_read": 0.10,
    },
    "claude-sonnet-4-20250514": {
        "input": 3.00, "output": 15.00,
        "cache_write": 3.75, "cache_read": 0.30,
    },
    "gpt-4o-mini": {
        "input": 0.15, "output": 0.60,
        "cache_write": 0, "cache_read": 0,
    },
    "gpt-4o": {
        "input": 2.50, "output": 10.00,
        "cache_write": 0, "cache_read": 0,
    },
}


def _get_provider() -> LLMProvider:
    """Read LLM_PROVIDER from environment. Default: anthropic."""
    raw = os.environ.get("LLM_PROVIDER", "anthropic").lower()
    try:
        return LLMProvider(raw)
    except ValueError:
        logger.warning(f"Unknown LLM_PROVIDER '{raw}', falling back to anthropic")
        return LLMProvider.ANTHROPIC


def get_model_for_tier(tier: ModelTier, provider: LLMProvider = None) -> str:
    """Resolve a ModelTier to a concrete model ID for the current provider."""
    provider = provider or _get_provider()
    return MODEL_MAP[provider][tier]


def get_model_for_user(user: dict = None) -> str:
    """Return model ID based on user subscription tier.
    Premium → SMART, Free → FAST."""
    tier = ModelTier.SMART if (user and user.get("subscription_tier") == "premium") else ModelTier.FAST
    return get_model_for_tier(tier)


# ── Core LLM Call ──

async def call_llm(
    system_prompt: str,
    user_prompt: str,
    model: str = None,
    model_tier: ModelTier = ModelTier.FAST,
    max_tokens: int = 1000,
    caller: str = "",
    user_id: str = None,
    cache_system: bool = True,
    messages: list = None,
) -> Optional[str]:
    """Provider-agnostic LLM call.

    Args:
        system_prompt: System message text.
        user_prompt: User message text (ignored if messages is provided).
        model: Explicit model ID. If None, resolved from model_tier.
        model_tier: FAST/SMART/EXTRACT. Used only if model is None.
        max_tokens: Maximum output tokens.
        caller: Identifier for usage tracking (e.g. "coach_chat").
        user_id: For usage tracking.
        cache_system: Whether to cache the system prompt (Anthropic only).
        messages: Full conversation history. If provided, user_prompt is ignored.

    Returns:
        Response text or None on failure.
    """
    provider = _get_provider()
    resolved_model = model or get_model_for_tier(model_tier, provider)

    # Instrument with Prometheus timing
    start = time.monotonic()
    result = None

    if provider == LLMProvider.ANTHROPIC:
        result = await _call_anthropic(
            system_prompt, user_prompt, resolved_model, max_tokens,
            caller, user_id, cache_system, messages,
        )
    elif provider == LLMProvider.OPENAI:
        result = await _call_openai(
            system_prompt, user_prompt, resolved_model, max_tokens,
            caller, user_id, messages,
        )
    else:
        logger.error(f"Unsupported LLM provider: {provider}")
        return None

    # Record Prometheus metrics (non-blocking, never fails)
    try:
        from services.metrics import record_llm_call
        duration = time.monotonic() - start
        record_llm_call(
            model=resolved_model, caller=caller,
            success=result is not None, duration=duration,
        )
    except Exception:
        pass

    return result


# ── Anthropic Implementation ──

async def _call_anthropic(
    system_prompt: str,
    user_prompt: str,
    model: str,
    max_tokens: int,
    caller: str,
    user_id: str,
    cache_system: bool,
    messages: list,
) -> Optional[str]:
    """Call Anthropic Claude API with retry, circuit breaker, and cache_control."""
    api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.warning("No ANTHROPIC_API_KEY set — AI call skipped")
        return None

    breaker = _get_breaker("anthropic")
    if not breaker.can_execute():
        logger.warning(f"Circuit breaker OPEN for anthropic — skipping {caller}")
        return None

    # Build system content block with cache_control on the content block itself
    system_block = [{"type": "text", "text": system_prompt}]
    if cache_system:
        system_block[0]["cache_control"] = {"type": "ephemeral"}

    # Build messages
    if messages:
        api_messages = messages
    else:
        api_messages = [{"role": "user", "content": user_prompt}]

    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client_http:
                resp = await client_http.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": model,
                        "max_tokens": max_tokens,
                        "system": system_block,
                        "messages": api_messages,
                    },
                )

                # Retryable status → wait and retry
                if resp.status_code in RETRYABLE_STATUS_CODES and attempt < MAX_RETRIES:
                    delay = _compute_delay(attempt)
                    logger.warning(
                        f"Anthropic {resp.status_code} ({caller}), "
                        f"retry {attempt + 1}/{MAX_RETRIES} in {delay:.1f}s"
                    )
                    await asyncio.sleep(delay)
                    continue

                resp.raise_for_status()
                data = resp.json()

                # Success — reset circuit breaker
                breaker.record_success()

                # Track usage
                usage = data.get("usage", {})
                await _track_usage(
                    model=model,
                    caller=caller,
                    user_id=user_id,
                    input_tokens=usage.get("input_tokens", 0),
                    output_tokens=usage.get("output_tokens", 0),
                    cache_read=usage.get("cache_read_input_tokens", 0),
                    cache_write=usage.get("cache_creation_input_tokens", 0),
                    retries=attempt,
                )

                return data["content"][0]["text"]

        except httpx.TimeoutException as e:
            last_error = e
            if attempt < MAX_RETRIES:
                delay = _compute_delay(attempt)
                logger.warning(
                    f"Anthropic timeout ({caller}), "
                    f"retry {attempt + 1}/{MAX_RETRIES} in {delay:.1f}s"
                )
                await asyncio.sleep(delay)
                continue

        except httpx.HTTPStatusError as e:
            last_error = e
            # Non-retryable HTTP error (400, 401, etc.) — fail immediately
            if e.response.status_code not in RETRYABLE_STATUS_CODES:
                logger.error(f"Anthropic {e.response.status_code} ({caller}): {e}")
                breaker.record_failure()
                return None
            # Retryable but exhausted retries
            if attempt >= MAX_RETRIES:
                break

        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES:
                delay = _compute_delay(attempt)
                logger.warning(
                    f"Anthropic error ({caller}): {e}, "
                    f"retry {attempt + 1}/{MAX_RETRIES} in {delay:.1f}s"
                )
                await asyncio.sleep(delay)
                continue

    # All retries exhausted
    breaker.record_failure()
    logger.error(
        f"Anthropic call failed after {MAX_RETRIES + 1} attempts ({caller}): {last_error}"
    )
    return None


# ── OpenAI Implementation (future-ready) ──

async def _call_openai(
    system_prompt: str,
    user_prompt: str,
    model: str,
    max_tokens: int,
    caller: str,
    user_id: str,
    messages: list,
) -> Optional[str]:
    """Call OpenAI-compatible API with retry + circuit breaker."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.warning("No OPENAI_API_KEY set — AI call skipped")
        return None

    breaker = _get_breaker("openai")
    if not breaker.can_execute():
        logger.warning(f"Circuit breaker OPEN for openai — skipping {caller}")
        return None

    api_messages = [{"role": "system", "content": system_prompt}]
    if messages:
        api_messages.extend(messages)
    else:
        api_messages.append({"role": "user", "content": user_prompt})

    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client_http:
                resp = await client_http.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "max_tokens": max_tokens,
                        "messages": api_messages,
                    },
                )

                if resp.status_code in RETRYABLE_STATUS_CODES and attempt < MAX_RETRIES:
                    delay = _compute_delay(attempt)
                    logger.warning(
                        f"OpenAI {resp.status_code} ({caller}), "
                        f"retry {attempt + 1}/{MAX_RETRIES} in {delay:.1f}s"
                    )
                    await asyncio.sleep(delay)
                    continue

                resp.raise_for_status()
                data = resp.json()

                breaker.record_success()

                usage = data.get("usage", {})
                await _track_usage(
                    model=model,
                    caller=caller,
                    user_id=user_id,
                    input_tokens=usage.get("prompt_tokens", 0),
                    output_tokens=usage.get("completion_tokens", 0),
                    retries=attempt,
                )

                return data["choices"][0]["message"]["content"]

        except httpx.TimeoutException as e:
            last_error = e
            if attempt < MAX_RETRIES:
                delay = _compute_delay(attempt)
                logger.warning(
                    f"OpenAI timeout ({caller}), "
                    f"retry {attempt + 1}/{MAX_RETRIES} in {delay:.1f}s"
                )
                await asyncio.sleep(delay)
                continue

        except httpx.HTTPStatusError as e:
            last_error = e
            if e.response.status_code not in RETRYABLE_STATUS_CODES:
                logger.error(f"OpenAI {e.response.status_code} ({caller}): {e}")
                breaker.record_failure()
                return None
            if attempt >= MAX_RETRIES:
                break

        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES:
                delay = _compute_delay(attempt)
                logger.warning(
                    f"OpenAI error ({caller}): {e}, "
                    f"retry {attempt + 1}/{MAX_RETRIES} in {delay:.1f}s"
                )
                await asyncio.sleep(delay)
                continue

    breaker.record_failure()
    logger.error(
        f"OpenAI call failed after {MAX_RETRIES + 1} attempts ({caller}): {last_error}"
    )
    return None


# ── Usage Tracking ──

async def _track_usage(
    model: str,
    caller: str,
    user_id: str = None,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cache_read: int = 0,
    cache_write: int = 0,
    prompt_version: int = None,
    retries: int = 0,
):
    """Log token usage to MongoDB. Non-blocking, silent fail."""
    try:
        from database import db

        pricing = PRICING.get(model, PRICING["claude-haiku-4-5-20251001"])
        cost = (
            input_tokens * pricing["input"]
            + output_tokens * pricing["output"]
            + cache_write * pricing["cache_write"]
            + cache_read * pricing["cache_read"]
        ) / 1_000_000

        doc = {
            "user_id": user_id,
            "model": model,
            "caller": caller,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "estimated_cost_usd": round(cost, 6),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        if cache_read or cache_write:
            doc["cache_read_input_tokens"] = cache_read
            doc["cache_creation_input_tokens"] = cache_write
            doc["cache_hit"] = cache_read > 0
        if prompt_version is not None:
            doc["prompt_version"] = prompt_version
        if retries > 0:
            doc["retries"] = retries

        await db.ai_usage.insert_one(doc)
    except Exception:
        pass  # Never block on tracking failure


def get_circuit_breaker_status() -> dict:
    """Return circuit breaker states for all providers. Used by admin dashboard."""
    result = {}
    for name, cb in _circuit_breakers.items():
        result[name] = {
            "state": cb.state.value,
            "consecutive_failures": cb.consecutive_failures,
            "last_failure_ago_s": (
                round(time.monotonic() - cb.last_failure_time, 1)
                if cb.last_failure_time > 0 else None
            ),
        }
    return result
