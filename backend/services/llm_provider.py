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
"""

import os
import logging
from enum import Enum
from typing import Optional
from datetime import datetime, timezone

import httpx

logger = logging.getLogger("infinea")


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

    if provider == LLMProvider.ANTHROPIC:
        return await _call_anthropic(
            system_prompt, user_prompt, resolved_model, max_tokens,
            caller, user_id, cache_system, messages,
        )
    elif provider == LLMProvider.OPENAI:
        return await _call_openai(
            system_prompt, user_prompt, resolved_model, max_tokens,
            caller, user_id, messages,
        )
    else:
        logger.error(f"Unsupported LLM provider: {provider}")
        return None


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
    """Call Anthropic Claude API with correct cache_control placement."""
    api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.warning("No ANTHROPIC_API_KEY set — AI call skipped")
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
            resp.raise_for_status()
            data = resp.json()

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
            )

            return data["content"][0]["text"]
    except Exception as e:
        logger.error(f"Anthropic call error ({caller}): {e}")
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
    """Call OpenAI-compatible API. Ready for migration, not primary."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.warning("No OPENAI_API_KEY set — AI call skipped")
        return None

    api_messages = [{"role": "system", "content": system_prompt}]
    if messages:
        api_messages.extend(messages)
    else:
        api_messages.append({"role": "user", "content": user_prompt})

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
            resp.raise_for_status()
            data = resp.json()

            usage = data.get("usage", {})
            await _track_usage(
                model=model,
                caller=caller,
                user_id=user_id,
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
            )

            return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"OpenAI call error ({caller}): {e}")
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

        await db.ai_usage.insert_one(doc)
    except Exception:
        pass  # Never block on tracking failure
