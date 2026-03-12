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

from config import limiter, logger
from database import db, client

# ── App & Router ──
app = FastAPI(title="InFinea API")
api_router = APIRouter(prefix="/api")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
from routes.objectives import router as objectives_router
from routes.routines import router as routines_router

api_router.include_router(auth_router)
api_router.include_router(onboarding_router)
api_router.include_router(actions_router)
api_router.include_router(ai_router)
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

# Public routes (no /api prefix)
app.include_router(social_public_router)


# ── Root ──
@api_router.get("/")
async def root():
    return {"message": "InFinea API - Investissez vos instants perdus"}


# ── Mount router + CORS ──
app.include_router(api_router)

ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
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
    await db.event_log.create_index("timestamp", expireAfterSeconds=90 * 24 * 3600)
    await db.user_features.create_index("user_id", unique=True)
    await db.user_features.create_index("computed_at")
    await db.action_signals.create_index([("user_id", 1), ("action_id", 1)], unique=True)
    await db.action_signals.create_index("updated_at")
    await db.coach_messages.create_index([("user_id", 1), ("created_at", 1)])
    await db.coach_messages.create_index("created_at", expireAfterSeconds=30 * 24 * 3600)
    await db.objectives.create_index([("user_id", 1), ("status", 1)])
    await db.objectives.create_index("objective_id", unique=True)
    await db.routines.create_index([("user_id", 1), ("is_active", 1)])
    await db.routines.create_index("routine_id", unique=True)
    await db.shares.create_index("share_id", unique=True)
    await db.shares.create_index([("user_id", 1), ("created_at", -1)])
    await db.shares.create_index("expires_at", expireAfterSeconds=0)
    await db.groups.create_index("group_id", unique=True)
    await db.groups.create_index([("members.user_id", 1), ("status", 1)])
    logger.info("All indexes ensured")

    # Start background tasks
    from services.action_generator import daily_generation_loop
    from services.feature_calculator import feature_computation_loop
    from services.notification_scheduler import notification_scheduler_loop
    asyncio.create_task(daily_generation_loop(db))
    asyncio.create_task(feature_computation_loop(db))
    asyncio.create_task(notification_scheduler_loop(db))
    logger.info("Background tasks started")


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
