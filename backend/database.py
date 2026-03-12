"""
InFinea — Database connections.
MongoDB client + Redis cache client (optional).
"""

from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URL, DB_NAME, REDIS_URL, logger

# ── MongoDB ──
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# ── Redis (optional — graceful fallback if not configured) ──
redis_client = None

if REDIS_URL:
    try:
        import redis.asyncio as aioredis
        redis_client = aioredis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
        )
        logger.info("Redis client configured")
    except Exception as e:
        logger.warning(f"Redis unavailable, running without cache: {e}")
        redis_client = None
else:
    logger.info("No REDIS_URL configured, running without cache")
