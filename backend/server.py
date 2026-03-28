"""
InFinea — Application factory.
Creates the FastAPI app, mounts all route modules, configures middleware,
and manages startup/shutdown lifecycle.
"""

import os
import asyncio
from fastapi import FastAPI, APIRouter
from starlette.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest

from config import limiter, logger
from database import db, client


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses (OWASP best practices)."""

    async def dispatch(self, request: StarletteRequest, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' https://res.cloudinary.com data:; "
            "connect-src 'self' https://*.anthropic.com https://*.stripe.com https://*.resend.com; "
            "frame-ancestors 'none'"
        )
        return response

# ── App & Router ──
app = FastAPI(title="InFinea API")
api_router = APIRouter(prefix="/api")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SecurityHeadersMiddleware)

# ── Route Modules ──
from routes.auth_routes import router as auth_router
from routes.onboarding import router as onboarding_router
from routes.actions import router as actions_router
from routes.ai import router as ai_router
from routes.sessions import router as sessions_router
from routes.billing import router as billing_router
from routes.integrations import router as integrations_router
from routes.badges import router as badges_router
from routes.notifications import router as notifications_router
from routes.b2b import router as b2b_router
from routes.reflections import router as reflections_router
from routes.features import router as features_router
from routes.social import router as social_router, public_router as social_public_router
from routes.profiles import public_router as profiles_public_router
from routes.profiles import router as profiles_router
from routes.feed import router as feed_router
from routes.objectives import router as objectives_router
from routes.admin_ai import router as admin_ai_router
from routes.routines import router as routines_router
from routes.micro_instants import router as micro_instants_router
from routes.profiles import router as profiles_router
from routes.feed import router as feed_router
from routes.challenges import router as challenges_router
from routes.safety import router as safety_router
from routes.messaging import router as messaging_router
from routes.leaderboard import router as leaderboard_router
from routes.hashtags import router as hashtags_router

api_router.include_router(auth_router)
api_router.include_router(onboarding_router)
api_router.include_router(actions_router)
api_router.include_router(ai_router)
api_router.include_router(admin_ai_router)
api_router.include_router(sessions_router)
api_router.include_router(billing_router)
api_router.include_router(integrations_router)
api_router.include_router(badges_router)
api_router.include_router(notifications_router)
api_router.include_router(b2b_router)
api_router.include_router(reflections_router)
api_router.include_router(features_router)
api_router.include_router(social_router)
api_router.include_router(objectives_router)
api_router.include_router(routines_router)
api_router.include_router(micro_instants_router)
api_router.include_router(profiles_router)
api_router.include_router(feed_router)
api_router.include_router(challenges_router)
api_router.include_router(safety_router)
api_router.include_router(messaging_router)
api_router.include_router(leaderboard_router)
api_router.include_router(hashtags_router)

# Public routes (no /api prefix)
app.include_router(social_public_router)
app.include_router(profiles_public_router)


# ── Root ──
@api_router.get("/")
async def root():
    return {"message": "InFinea API - Investissez vos instants perdus"}


# ── Health Check (no auth, no /api prefix — for Render/uptime monitors) ──
@app.get("/health")
async def health_check():
    """Structured health check: MongoDB + Redis + background task status."""
    from datetime import datetime, timezone
    from services.cache import cache_ping

    checks = {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}

    # MongoDB connectivity
    try:
        await db.command("ping")
        checks["mongo"] = "connected"
    except Exception as e:
        checks["mongo"] = f"error: {e}"
        checks["status"] = "degraded"

    # Redis connectivity
    redis_ok = await cache_ping()
    checks["redis"] = "connected" if redis_ok else "unavailable"
    if not redis_ok:
        checks["status"] = "degraded" if checks["status"] == "ok" else checks["status"]

    # Last feature computation (background job health indicator)
    try:
        last_comp = await db.feature_computation_logs.find_one(
            sort=[("computed_at", -1)]
        )
        if last_comp:
            checks["last_feature_computation"] = last_comp.get("computed_at", "unknown")
            checks["last_computation_users"] = last_comp.get("users_processed", 0)
        else:
            checks["last_feature_computation"] = "never"
    except Exception:
        checks["last_feature_computation"] = "error"

    return checks


# ── Mount router + CORS ──
app.include_router(api_router)

ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

# Security: reject wildcard or insecure origins in production
_is_prod = os.environ.get("RENDER", "") or os.environ.get("PRODUCTION", "")
if _is_prod:
    for origin in ALLOWED_ORIGINS:
        if origin.strip() == "*":
            raise RuntimeError("CORS wildcard '*' is not allowed in production")
        if origin.strip().startswith("http://") and "localhost" not in origin:
            logger.warning(f"CORS: insecure origin in production: {origin}")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


# ── Lifecycle ──
@app.on_event("startup")
async def startup_event():
    """Auto-seed database, ensure indexes, start background tasks."""
    from routes.integrations import seed_micro_actions

    count = await db.micro_actions.count_documents({})
    existing_cats = await db.micro_actions.distinct("category")
    premium_cats = {"creativity", "fitness", "mindfulness", "leadership", "finance", "relations", "mental_health", "entrepreneurship"}
    missing_cats = premium_cats - set(existing_cats)
    if count == 0 or missing_cats:
        logger.info(f"Seeding needed (total={count}, missing categories={missing_cats})")
        await seed_micro_actions()
        logger.info("Database seeded successfully!")

    # Create indexes (idempotent — safe to run every startup)
    await db.event_log.create_index("user_id")
    await db.event_log.create_index([("event_type", 1), ("timestamp", -1)])
    # Migrate TTL: drop old 90-day index, create 365-day index
    try:
        await db.event_log.drop_index("timestamp_1")
    except Exception:
        pass  # Index may not exist yet
    await db.event_log.create_index("timestamp", expireAfterSeconds=365 * 24 * 3600)  # 12 months for long-term learning
    # Stripe webhook idempotency — auto-cleanup after 90 days
    await db.webhook_events.create_index("event_id", unique=True)
    await db.webhook_events.create_index("processed_at", expireAfterSeconds=90 * 24 * 3600)
    # Vertical AI Phase 1 — response feedback tracking
    await db.ai_response_feedback.create_index([("endpoint", 1), ("prompt_version", 1), ("created_at", -1)])
    await db.ai_response_feedback.create_index("user_id")
    # Vertical AI Phase 2 — persistent AI memories
    await db.ai_memories.create_index([("user_id", 1), ("category", 1)])
    await db.ai_memories.create_index([("user_id", 1), ("created_at", -1)])
    await db.ai_memories.create_index("expires_at", expireAfterSeconds=0)  # TTL auto-cleanup
    # Vertical AI Phase 3 — collective intelligence patterns
    await db.collective_patterns.create_index([("pattern_type", 1), ("segment", 1)])
    # Collective patterns history (append, never overwrite — trend analysis)
    await db.collective_patterns_history.create_index([("pattern_type", 1), ("week", -1)])
    await db.collective_patterns_history.create_index("computed_at", expireAfterSeconds=365 * 24 * 3600)
    # Data enrichment layer — feature history for trend analysis
    await db.user_features_history.create_index([("user_id", 1), ("snapshot_date", -1)])
    await db.user_features_history.create_index("snapshot_date", expireAfterSeconds=365 * 24 * 3600)  # 12 months
    # Analytics indexes
    await db.ai_usage.create_index([("user_id", 1), ("created_at", -1)])
    await db.ai_usage.create_index([("model", 1), ("created_at", -1)])
    await db.user_features.create_index("user_id", unique=True)
    await db.user_features.create_index("computed_at")
    await db.action_signals.create_index([("user_id", 1), ("action_id", 1)], unique=True)
    await db.action_signals.create_index("updated_at")
    await db.coach_messages.create_index([("user_id", 1), ("created_at", 1)])
    # Migrate TTL: drop old 30-day index, create 180-day index
    try:
        await db.coach_messages.drop_index("created_at_1")
    except Exception:
        pass
    await db.coach_messages.create_index("created_at", expireAfterSeconds=180 * 24 * 3600)  # 6 months for coaching quality analysis
    await db.objectives.create_index([("user_id", 1), ("status", 1)])
    await db.objectives.create_index("objective_id", unique=True)
    await db.routines.create_index([("user_id", 1), ("is_active", 1)])
    await db.routines.create_index("routine_id", unique=True)
    await db.shares.create_index("share_id", unique=True)
    await db.shares.create_index([("user_id", 1), ("created_at", -1)])
    await db.shares.create_index("expires_at", expireAfterSeconds=0)
    await db.groups.create_index("group_id", unique=True)
    await db.groups.create_index([("members.user_id", 1), ("status", 1)])
    await db.micro_instant_outcomes.create_index([("user_id", 1), ("recorded_at", -1)])
    await db.micro_instant_outcomes.create_index("instant_id")
    # Micro-actions library — fast category/filter lookups
    await db.micro_actions.create_index("category")
    await db.micro_actions.create_index([("category", 1), ("energy_level", 1)])

    # Indexes identifiés par audit CTO — collections à fort trafic
    await db.notifications.create_index([("user_id", 1), ("type", 1), ("created_at", -1)])
    await db.notifications.create_index("created_at", expireAfterSeconds=90 * 24 * 3600)
    await db.user_sessions_history.create_index([("user_id", 1), ("started_at", -1)])
    await db.user_sessions_history.create_index("session_id", unique=True)
    await db.users.create_index("user_id", unique=True)
    await db.users.create_index("username", unique=True, sparse=True)
    await db.follows.create_index([("follower_id", 1), ("following_id", 1)], unique=True)
    await db.follows.create_index([("following_id", 1), ("status", 1)])
    # Activity feed
    await db.activities.create_index([("user_id", 1), ("created_at", -1)])
    await db.activities.create_index([("visibility", 1), ("created_at", -1)])
    await db.activities.create_index("activity_id", unique=True)
    await db.reactions.create_index([("activity_id", 1), ("user_id", 1)], unique=True)
    await db.comments.create_index([("activity_id", 1), ("created_at", 1)])
    await db.comments.create_index("comment_id", unique=True)
    # Challenges
    await db.challenges.create_index("challenge_id", unique=True)
    await db.challenges.create_index([("participants.user_id", 1), ("status", 1)])
    await db.challenges.create_index([("privacy", 1), ("status", 1), ("created_at", -1)])
    await db.challenge_invites.create_index([("user_id", 1), ("status", 1)])
    await db.challenge_invites.create_index("invite_id", unique=True)
    # H.2 — Refresh tokens (rotation, family tracking, TTL auto-cleanup)
    await db.refresh_tokens.create_index("token", unique=True)
    await db.refresh_tokens.create_index("user_id")
    await db.refresh_tokens.create_index("family_id")
    # Social safety — blocks & reports
    await db.blocks.create_index([("blocker_id", 1), ("blocked_id", 1)], unique=True)
    await db.blocks.create_index("blocked_id")
    await db.reports.create_index("report_id", unique=True)
    await db.reports.create_index([("reporter_id", 1), ("target_type", 1), ("target_id", 1)])

    # Messaging
    await db.conversations.create_index("conversation_id", unique=True)
    await db.conversations.create_index("participants")
    await db.conversations.create_index("updated_at")
    await db.messages.create_index("message_id", unique=True)
    await db.messages.create_index([("conversation_id", 1), ("created_at", 1)])

    # Mutes (unidirectional — Instagram Restrict pattern)
    await db.mutes.create_index([("muter_id", 1), ("muted_id", 1)], unique=True)
    await db.mutes.create_index("muter_id")

    # Typing indicators (TTL auto-expire after 6 seconds)
    await db.typing_indicators.create_index(
        "expires_at", expireAfterSeconds=6
    )
    await db.typing_indicators.create_index(
        [("conversation_id", 1), ("user_id", 1)], unique=True
    )

    # AI usage monitoring (cost tracking)
    await db.ai_usage.create_index("created_at")
    await db.ai_usage.create_index("caller")
    await db.ai_usage.create_index("user_id")

    # Mentions (for "who mentioned me" queries)
    await db.comments.create_index("mentions.user_id")
    await db.messages.create_index("mentions.user_id")

    # ── P0 Missing indexes (social MVP audit) ──

    # Bookmarks — was ZERO indexes, used on every feed page load
    await db.bookmarks.create_index([("user_id", 1), ("activity_id", 1)], unique=True)
    await db.bookmarks.create_index([("user_id", 1), ("created_at", -1)])

    # Hashtag stats — was ZERO indexes, used on every post create + autocomplete
    await db.hashtag_stats.create_index("tag", unique=True)
    await db.hashtag_stats.create_index([("use_count", -1)])

    # Followed hashtags — user + tag unique, list by user
    await db.followed_hashtags.create_index([("user_id", 1), ("tag", 1)], unique=True)
    await db.followed_hashtags.create_index([("user_id", 1), ("followed_at", -1)])

    # Reactions — missing (user_id, created_at) for affinity computation
    await db.reactions.create_index([("user_id", 1), ("created_at", -1)])

    # Comments — missing (user_id, created_at) for affinity computation
    await db.comments.create_index([("user_id", 1), ("created_at", -1)])

    # Activities — missing hashtag + created_at for hashtag feed queries
    await db.activities.create_index([("hashtags", 1), ("created_at", -1)])
    # Activities — missing (user_id, pinned) for pinned activities query
    await db.activities.create_index([("user_id", 1), ("pinned", 1)])

    # Link previews — URL cache for OG card extraction
    await db.link_previews.create_index("url", unique=True)

    # Poll votes — one vote per user per poll, query by activity
    await db.poll_votes.create_index([("activity_id", 1), ("user_id", 1)], unique=True)
    await db.poll_votes.create_index([("user_id", 1), ("voted_at", -1)])

    # Moderation actions — was ZERO indexes
    await db.moderation_actions.create_index("content_id")
    await db.moderation_actions.create_index([("author_id", 1), ("created_at", -1)])

    # Follows — missing (follower_id, status, followed_at) for paginated following list
    await db.follows.create_index([("follower_id", 1), ("status", 1), ("followed_at", -1)])
    await db.follows.create_index([("following_id", 1), ("status", 1), ("followed_at", -1)])

    # Text search indexes (full-text search — much faster than $regex)
    try:
        await db.activities.create_index(
            [("content", "text"), ("data.action_title", "text")],
            default_language="french",
            name="activities_text_search",
        )
    except Exception:
        pass  # Index may already exist with different config — safe to skip

    try:
        await db.users.create_index(
            [("display_name", "text"), ("name", "text"), ("username", "text"), ("bio", "text")],
            default_language="french",
            name="users_text_search",
        )
    except Exception:
        pass

    logger.info("All indexes ensured")

    # One-time migration: generate usernames for existing users who don't have one
    from routes.auth_routes import generate_username
    users_without_username = await db.users.find(
        {"$or": [{"username": None}, {"username": {"$exists": False}}]},
        {"_id": 0, "user_id": 1, "email": 1},
    ).to_list(None)
    if users_without_username:
        logger.info(f"Migrating usernames for {len(users_without_username)} users")
        for u in users_without_username:
            email = u.get("email", "")
            if not email:
                continue
            username = await generate_username(email)
            await db.users.update_one(
                {"user_id": u["user_id"]},
                {"$set": {"username": username}},
            )
        logger.info("Username migration complete")

    # One-time migration: set existing activities to public visibility for Discover feed
    migrated = await db.activities.update_many(
        {"visibility": "followers"},
        {"$set": {"visibility": "public"}},
    )
    if migrated.modified_count > 0:
        logger.info(f"Migrated {migrated.modified_count} activities to public visibility")

    # One-time migration: retroactive XP for users who don't have it yet
    users_without_xp = await db.users.find(
        {"$or": [{"total_xp": {"$exists": False}}, {"level": {"$exists": False}}]},
        {"_id": 0, "user_id": 1, "total_time_invested": 1, "badges": 1, "streak_days": 1},
    ).to_list(None)
    if users_without_xp:
        from services.xp_engine import migrate_user_xp
        logger.info(f"XP migration: {len(users_without_xp)} users need retroactive XP")
        for u in users_without_xp:
            total = await migrate_user_xp(u)
            logger.info(f"  {u['user_id'][:8]}... → {total} XP")
        logger.info("XP migration complete")

    # XP history index (for analytics)
    await db.xp_history.create_index([("user_id", 1), ("created_at", -1)])
    await db.xp_history.create_index("source")

    # Start background tasks
    from services.action_generator import daily_generation_loop
    from services.feature_calculator import feature_computation_loop
    from services.notification_scheduler import notification_scheduler_loop
    from services.ai_memory import memory_cleanup_loop
    from services.collective_intelligence import collective_pattern_loop
    asyncio.create_task(daily_generation_loop(db))
    asyncio.create_task(feature_computation_loop(db))
    asyncio.create_task(notification_scheduler_loop(db))
    asyncio.create_task(memory_cleanup_loop(db))
    asyncio.create_task(collective_pattern_loop(db))
    logger.info("Background tasks started (including AI memory cleanup + collective intelligence)")


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
