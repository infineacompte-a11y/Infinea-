"""
InFinea — Redis cache layer.
Provides async get/set/delete with JSON serialization and TTL.
Graceful fallback: if Redis is unavailable, all operations return None
and the app falls back to MongoDB reads transparently.
"""

import json
from config import logger
from database import redis_client

# ── Default TTLs (seconds) ──
TTL_USER_FEATURES = 6 * 3600      # 6 hours (matches background computation loop)
TTL_REVIEW_QUEUE = 10 * 60        # 10 minutes (reviews change on record_review)
TTL_RANKED_ACTIONS = 3600         # 1 hour
TTL_HEALTH = 30                   # 30 seconds (health check ping)


async def cache_get(key: str):
    """Get a cached value. Returns deserialized Python object or None."""
    if not redis_client:
        return None
    try:
        raw = await redis_client.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as e:
        logger.warning(f"Cache GET failed for {key}: {e}")
        return None


async def cache_set(key: str, value, ttl: int = 3600):
    """Set a cached value with TTL in seconds."""
    if not redis_client:
        return
    try:
        await redis_client.set(key, json.dumps(value, default=str), ex=ttl)
    except Exception as e:
        logger.warning(f"Cache SET failed for {key}: {e}")


async def cache_delete(key: str):
    """Delete a single cached key."""
    if not redis_client:
        return
    try:
        await redis_client.delete(key)
    except Exception as e:
        logger.warning(f"Cache DELETE failed for {key}: {e}")


async def cache_delete_pattern(pattern: str):
    """Delete all keys matching a pattern (e.g., 'user_features:*')."""
    if not redis_client:
        return
    try:
        cursor = None
        while cursor != 0:
            cursor, keys = await redis_client.scan(
                cursor=cursor or 0, match=pattern, count=100
            )
            if keys:
                await redis_client.delete(*keys)
    except Exception as e:
        logger.warning(f"Cache DELETE PATTERN failed for {pattern}: {e}")


async def cache_ping() -> bool:
    """Check if Redis is reachable. Used by health check."""
    if not redis_client:
        return False
    try:
        return await redis_client.ping()
    except Exception:
        return False
