from fastapi import FastAPI, APIRouter, HTTPException, Request, Depends, Response
from fastapi.responses import JSONResponse, RedirectResponse
import urllib.parse
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
import secrets
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
import httpx
import json
import asyncio
import stripe as stripe_lib
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from services.event_tracker import track_event
from services.feedback_loop import record_signal
from services.scoring_engine import rank_actions_for_user, get_next_best_action
try:
    from icalendar import Calendar as ICalCalendar
    ICAL_AVAILABLE = True
except ImportError:
    ICAL_AVAILABLE = False

from config import (
    JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION_HOURS,
    VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY, VAPID_CLAIMS_EMAIL,
    STRIPE_WEBHOOK_SECRET,
)
from database import db, client

# Create the main app
app = FastAPI(title="InFinea API")
api_router = APIRouter(prefix="/api")

# Rate limiting
from config import limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

from config import logger

# ============== MODELS (imported from models.py) ==============
from models import (
    UserCreate, UserLogin, UserResponse,
    MicroAction, MicroActionCreate,
    SessionStart, SessionComplete,
    AIRequest, CustomActionRequest, DebriefRequest, CoachChatRequest,
    CheckoutRequest, PromoCodeRequest,
    ProgressStats, OnboardingProfile,
    ObjectiveCreate, ObjectiveUpdate,
    RoutineCreate, RoutineUpdate,
    ICalConnectRequest, TokenConnectRequest, SlotSettings,
    NotificationPreferences,
    ShareCreate, GroupCreate, GroupInvite,
    CompanyCreate, InviteEmployee,
    ReflectionCreate, ReflectionResponse,
)

# ============== HELPERS (imported from helpers.py) ==============
from helpers import (
    AI_SYSTEM_MESSAGE, get_ai_model, call_ai, parse_ai_json,
    build_user_context, check_usage_limit, send_push_to_user,
)

# ============== HELPER FUNCTIONS ==============
# ============== HELPER FUNCTIONS ==============

from auth import create_token, verify_token, get_current_user, hash_password, verify_password

# ============== AUTH ROUTES (imported from routes/auth_routes.py) ==============
from routes.auth_routes import router as auth_router
api_router.include_router(auth_router)

# ============== ONBOARDING + ACTIONS ROUTES (imported) ==============
from routes.onboarding import router as onboarding_router
from routes.actions import router as actions_router
api_router.include_router(onboarding_router)
api_router.include_router(actions_router)

# ============== AI ROUTES (imported from routes/ai.py) ==============
from routes.ai import router as ai_router
api_router.include_router(ai_router)

# ============== SESSION + STATS ROUTES (imported from routes/sessions.py) ==============
from routes.sessions import router as sessions_router
api_router.include_router(sessions_router)

# ============== BILLING ROUTES (imported from routes/billing.py) ==============
from routes.billing import router as billing_router
api_router.include_router(billing_router)

# ============== INTEGRATIONS ROUTES (imported from routes/integrations.py) ==============
from routes.integrations import router as integrations_router
api_router.include_router(integrations_router)

# ============== ROUTE MODULES (imported) ==============
from routes.badges import router as badges_router
from routes.notifications import router as notifications_router
from routes.b2b import router as b2b_router
from routes.reflections import router as reflections_router
from routes.features import router as features_router
from routes.social import router as social_router

api_router.include_router(badges_router)
api_router.include_router(notifications_router)
api_router.include_router(b2b_router)
api_router.include_router(reflections_router)
api_router.include_router(features_router)
api_router.include_router(social_router)

# Public share route (no /api prefix)
from routes.social import public_router as social_public_router
app.include_router(social_public_router)

# Import seed function for startup
from routes.integrations import seed_micro_actions

# ============== ROOT ROUTE ==============

@api_router.get("/")
async def root():
    return {"message": "InFinea API - Investissez vos instants perdus"}

# Include router and add middleware
app.include_router(api_router)

ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

@app.on_event("startup")
async def startup_event():
    """Auto-seed the database if empty or missing premium categories, then start daily generator"""
    count = await db.micro_actions.count_documents({})
    existing_cats = await db.micro_actions.distinct("category")
    premium_cats = {"creativity", "fitness", "mindfulness", "leadership", "finance", "relations", "mental_health", "entrepreneurship"}
    missing_cats = premium_cats - set(existing_cats)
    if count == 0 or missing_cats:
        logger.info(f"Seeding needed (total={count}, missing categories={missing_cats})")
        await seed_micro_actions()
        logger.info("Database seeded successfully!")

    # Create indexes for event_log collection (idempotent — safe to run every startup)
    await db.event_log.create_index("user_id")
    await db.event_log.create_index([("event_type", 1), ("timestamp", -1)])
    await db.event_log.create_index("timestamp", expireAfterSeconds=90 * 24 * 3600)  # TTL: 90 days auto-cleanup
    logger.info("event_log indexes ensured")

    # Create indexes for user_features collection (idempotent)
    await db.user_features.create_index("user_id", unique=True)
    await db.user_features.create_index("computed_at")
    logger.info("user_features indexes ensured")

    # Create indexes for action_signals collection (feedback loop)
    await db.action_signals.create_index(
        [("user_id", 1), ("action_id", 1)], unique=True
    )
    await db.action_signals.create_index("updated_at")
    logger.info("action_signals indexes ensured")

    # Create indexes for coach_messages collection (persistent chat)
    await db.coach_messages.create_index([("user_id", 1), ("created_at", 1)])
    await db.coach_messages.create_index("created_at", expireAfterSeconds=30 * 24 * 3600)  # TTL: 30 days
    logger.info("coach_messages indexes ensured")

    # Create indexes for objectives collection (parcours personnalisés)
    await db.objectives.create_index([("user_id", 1), ("status", 1)])
    await db.objectives.create_index("objective_id", unique=True)
    logger.info("objectives indexes ensured")

    # Create indexes for routines collection
    await db.routines.create_index([("user_id", 1), ("is_active", 1)])
    await db.routines.create_index("routine_id", unique=True)
    logger.info("routines indexes ensured")

    # Create indexes for shares collection (D.2 share progression)
    await db.shares.create_index("share_id", unique=True)
    await db.shares.create_index([("user_id", 1), ("created_at", -1)])
    await db.shares.create_index("expires_at", expireAfterSeconds=0)  # MongoDB TTL: auto-delete expired docs
    logger.info("shares indexes ensured")

    # Create indexes for groups collection (D.3 duo/groupe)
    await db.groups.create_index("group_id", unique=True)
    await db.groups.create_index([("members.user_id", 1), ("status", 1)])
    logger.info("groups indexes ensured")

    # Start daily action generation background loop
    from services.action_generator import daily_generation_loop
    asyncio.create_task(daily_generation_loop(db))

    # Start feature computation background loop
    from services.feature_calculator import feature_computation_loop
    asyncio.create_task(feature_computation_loop(db))

    # Start proactive notification scheduler (streak alerts, routine reminders, objective nudges)
    from services.notification_scheduler import notification_scheduler_loop
    asyncio.create_task(notification_scheduler_loop(db))

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
