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

# ============== BADGES & ACHIEVEMENTS ==============

BADGES = [
    {
        "badge_id": "first_action",
        "name": "Premier Pas",
        "description": "Complétez votre première micro-action",
        "icon": "rocket",
        "condition": {"type": "sessions_completed", "value": 1}
    },
    {
        "badge_id": "streak_3",
        "name": "Régularité",
        "description": "Maintenez un streak de 3 jours",
        "icon": "flame",
        "condition": {"type": "streak_days", "value": 3}
    },
    {
        "badge_id": "streak_7",
        "name": "Semaine Parfaite",
        "description": "Maintenez un streak de 7 jours",
        "icon": "star",
        "condition": {"type": "streak_days", "value": 7}
    },
    {
        "badge_id": "streak_30",
        "name": "Mois d'Or",
        "description": "Maintenez un streak de 30 jours",
        "icon": "crown",
        "condition": {"type": "streak_days", "value": 30}
    },
    {
        "badge_id": "time_60",
        "name": "Première Heure",
        "description": "Accumulez 60 minutes de micro-actions",
        "icon": "clock",
        "condition": {"type": "total_time", "value": 60}
    },
    {
        "badge_id": "time_300",
        "name": "5 Heures",
        "description": "Accumulez 5 heures de micro-actions",
        "icon": "timer",
        "condition": {"type": "total_time", "value": 300}
    },
    {
        "badge_id": "time_600",
        "name": "10 Heures",
        "description": "Accumulez 10 heures de micro-actions",
        "icon": "trophy",
        "condition": {"type": "total_time", "value": 600}
    },
    {
        "badge_id": "category_learning",
        "name": "Apprenant",
        "description": "Complétez 10 actions d'apprentissage",
        "icon": "book-open",
        "condition": {"type": "category_sessions", "category": "learning", "value": 10}
    },
    {
        "badge_id": "category_productivity",
        "name": "Productif",
        "description": "Complétez 10 actions de productivité",
        "icon": "target",
        "condition": {"type": "category_sessions", "category": "productivity", "value": 10}
    },
    {
        "badge_id": "category_wellbeing",
        "name": "Zen Master",
        "description": "Complétez 10 actions de bien-être",
        "icon": "heart",
        "condition": {"type": "category_sessions", "category": "well_being", "value": 10}
    },
    {
        "badge_id": "all_categories",
        "name": "Équilibre",
        "description": "Complétez au moins 5 actions dans chaque catégorie",
        "icon": "sparkles",
        "condition": {"type": "all_categories", "value": 5}
    },
    {
        "badge_id": "premium",
        "name": "Investisseur",
        "description": "Passez à Premium",
        "icon": "gem",
        "condition": {"type": "subscription", "value": "premium"}
    },
    # --- Premium-exclusive badges ---
    {
        "badge_id": "streak_60",
        "name": "Discipline de Fer",
        "description": "Maintenez un streak de 60 jours",
        "icon": "shield",
        "condition": {"type": "streak_days", "value": 60},
        "premium_only": True
    },
    {
        "badge_id": "streak_100",
        "name": "Centurion",
        "description": "Maintenez un streak de 100 jours",
        "icon": "award",
        "condition": {"type": "streak_days", "value": 100},
        "premium_only": True
    },
    {
        "badge_id": "time_1500",
        "name": "25 Heures",
        "description": "Accumulez 25 heures de micro-actions",
        "icon": "crown",
        "condition": {"type": "total_time", "value": 1500},
        "premium_only": True
    },
    {
        "badge_id": "category_master",
        "name": "Polymathe",
        "description": "Complétez 20 sessions dans 5 catégories différentes",
        "icon": "layers",
        "condition": {"type": "multi_category_master", "min_categories": 5, "value": 20},
        "premium_only": True
    },
    {
        "badge_id": "challenge_3",
        "name": "Challenger",
        "description": "Complétez 3 défis mensuels",
        "icon": "trophy",
        "condition": {"type": "challenges_completed", "value": 3},
        "premium_only": True
    },
    {
        "badge_id": "challenge_10",
        "name": "Champion",
        "description": "Complétez 10 défis mensuels",
        "icon": "medal",
        "condition": {"type": "challenges_completed", "value": 10},
        "premium_only": True
    },
    {
        "badge_id": "custom_10",
        "name": "Architecte",
        "description": "Créez 10 actions personnalisées",
        "icon": "wrench",
        "condition": {"type": "custom_actions_created", "value": 10},
        "premium_only": True
    },
    {
        "badge_id": "streak_shield_5",
        "name": "Résilient",
        "description": "Utilisez le Bouclier de Streak 5 fois",
        "icon": "heart-handshake",
        "condition": {"type": "streak_shield_uses", "value": 5},
        "premium_only": True
    }
]

async def check_and_award_badges(user_id: str) -> List[dict]:
    """Check user progress and award new badges"""
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not user:
        return []
    
    # Get user's current badges
    user_badges = user.get("badges", [])
    user_badge_ids = [b["badge_id"] for b in user_badges]
    
    # Get session stats
    total_sessions = await db.user_sessions_history.count_documents(
        {"user_id": user_id, "completed": True}
    )
    
    # Get category stats
    pipeline = [
        {"$match": {"user_id": user_id, "completed": True}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}}}
    ]
    category_stats = await db.user_sessions_history.aggregate(pipeline).to_list(10)
    category_counts = {stat["_id"]: stat["count"] for stat in category_stats}
    
    # Get custom actions count
    custom_actions_count = await db.user_custom_actions.count_documents({"created_by": user_id})

    # Get challenges completed count
    challenges_completed = await db.user_challenges.count_documents(
        {"user_id": user_id, "completed": True}
    )

    new_badges = []
    is_premium = user.get("subscription_tier") == "premium"

    for badge in BADGES:
        if badge["badge_id"] in user_badge_ids:
            continue

        # Skip premium-only badges for free users
        if badge.get("premium_only") and not is_premium:
            continue

        condition = badge["condition"]
        earned = False

        if condition["type"] == "sessions_completed":
            earned = total_sessions >= condition["value"]
        elif condition["type"] == "streak_days":
            earned = user.get("streak_days", 0) >= condition["value"]
        elif condition["type"] == "total_time":
            earned = user.get("total_time_invested", 0) >= condition["value"]
        elif condition["type"] == "category_sessions":
            earned = category_counts.get(condition["category"], 0) >= condition["value"]
        elif condition["type"] == "all_categories":
            earned = all(
                category_counts.get(cat, 0) >= condition["value"]
                for cat in ["learning", "productivity", "well_being"]
            )
        elif condition["type"] == "subscription":
            earned = user.get("subscription_tier") == condition["value"]
        elif condition["type"] == "multi_category_master":
            qualifying = sum(1 for c in category_counts.values() if c >= condition["value"])
            earned = qualifying >= condition["min_categories"]
        elif condition["type"] == "challenges_completed":
            earned = challenges_completed >= condition["value"]
        elif condition["type"] == "custom_actions_created":
            earned = custom_actions_count >= condition["value"]
        elif condition["type"] == "streak_shield_uses":
            earned = user.get("streak_shield_count", 0) >= condition["value"]
        
        if earned:
            badge_award = {
                "badge_id": badge["badge_id"],
                "name": badge["name"],
                "icon": badge["icon"],
                "earned_at": datetime.now(timezone.utc).isoformat()
            }
            new_badges.append(badge_award)
    
    # Update user with new badges
    if new_badges:
        await db.users.update_one(
            {"user_id": user_id},
            {"$push": {"badges": {"$each": new_badges}}}
        )
    
    return new_badges

@api_router.get("/badges")
async def get_all_badges():
    """Get all available badges"""
    return BADGES

@api_router.get("/badges/user")
async def get_user_badges(user: dict = Depends(get_current_user)):
    """Get user's earned badges"""
    user_badges = user.get("badges", [])
    
    # Check for new badges
    new_badges = await check_and_award_badges(user["user_id"])
    
    all_earned = user_badges + new_badges
    
    return {
        "earned": all_earned,
        "new_badges": new_badges,
        "total_available": len(BADGES),
        "total_earned": len(all_earned)
    }

# ============== PREMIUM FEATURES ==============

@api_router.get("/premium/streak-shield")
async def get_streak_shield_status(user: dict = Depends(get_current_user)):
    """Get streak shield status for premium users"""
    if user.get("subscription_tier") != "premium":
        return {"available": False, "is_premium": False, "message": "Fonctionnalité Premium"}

    today = datetime.now(timezone.utc).date()
    shield_used_at = user.get("streak_shield_used_at")
    shield_available = True
    cooldown_days = 0

    if shield_used_at:
        if isinstance(shield_used_at, str):
            shield_date = datetime.fromisoformat(shield_used_at).date()
        else:
            shield_date = shield_used_at.date() if hasattr(shield_used_at, 'date') else shield_used_at
        days_since = (today - shield_date).days
        shield_available = days_since >= 7
        cooldown_days = max(0, 7 - days_since)

    return {
        "available": shield_available,
        "is_premium": True,
        "cooldown_days": cooldown_days,
        "total_uses": user.get("streak_shield_count", 0),
        "last_used": shield_used_at
    }

# Monthly challenges definitions
MONTHLY_CHALLENGES = [
    {
        "challenge_id": "explorer",
        "title": "Explorateur",
        "description": "Complétez 5 actions dans 3 catégories différentes ce mois-ci",
        "icon": "compass",
        "condition": {"type": "categories_touched", "min_categories": 3, "min_sessions": 5},
        "target": 5
    },
    {
        "challenge_id": "deep_diver",
        "title": "Deep Diver",
        "description": "Complétez 10 actions dans la même catégorie ce mois-ci",
        "icon": "target",
        "condition": {"type": "single_category_sessions", "value": 10},
        "target": 10
    },
    {
        "challenge_id": "early_bird",
        "title": "Matinal",
        "description": "Complétez 5 actions avant 9h ce mois-ci",
        "icon": "sunrise",
        "condition": {"type": "early_sessions", "hour_before": 9, "value": 5},
        "target": 5
    },
    {
        "challenge_id": "consistency",
        "title": "Régulier",
        "description": "Complétez au moins 1 action par jour pendant 15 jours ce mois-ci",
        "icon": "calendar-check",
        "condition": {"type": "active_days", "value": 15},
        "target": 15
    },
    {
        "challenge_id": "time_investor",
        "title": "Investisseur du Temps",
        "description": "Investissez 120 minutes ce mois-ci",
        "icon": "hourglass",
        "condition": {"type": "monthly_time", "value": 120},
        "target": 120
    },
    {
        "challenge_id": "diversifier",
        "title": "Diversificateur",
        "description": "Essayez au moins 5 catégories différentes ce mois-ci",
        "icon": "shuffle",
        "condition": {"type": "unique_categories", "value": 5},
        "target": 5
    },
]

@api_router.get("/premium/challenges")
async def get_premium_challenges(user: dict = Depends(get_current_user)):
    """Get current month's challenges with progress for premium users"""
    if user.get("subscription_tier") != "premium":
        return {"challenges": [], "is_premium": False, "message": "Fonctionnalité Premium"}

    now = datetime.now(timezone.utc)
    month_key = now.strftime("%Y-%m")
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()

    # Get this month's sessions
    sessions = await db.user_sessions_history.find(
        {"user_id": user["user_id"], "completed": True, "started_at": {"$gte": month_start}},
        {"_id": 0}
    ).to_list(500)

    # Calculate stats for challenge evaluation
    category_counts = {}
    total_time = 0
    early_sessions = 0
    active_days = set()
    for s in sessions:
        cat = s.get("category", "unknown")
        category_counts[cat] = category_counts.get(cat, 0) + 1
        total_time += s.get("actual_duration", 0)
        started = s.get("started_at", "")
        if started:
            try:
                dt = datetime.fromisoformat(started)
                if dt.hour < 9:
                    early_sessions += 1
                active_days.add(dt.date().isoformat())
            except (ValueError, TypeError):
                pass

    # Get user challenge records
    user_challenges = await db.user_challenges.find(
        {"user_id": user["user_id"], "month": month_key},
        {"_id": 0}
    ).to_list(20)
    completed_map = {uc["challenge_id"]: uc for uc in user_challenges}

    challenges_with_progress = []
    for ch in MONTHLY_CHALLENGES:
        cond = ch["condition"]
        progress = 0

        if cond["type"] == "categories_touched":
            cats_with_min = sum(1 for c in category_counts.values() if c >= 1)
            progress = min(len(sessions), ch["target"])
            if cats_with_min >= cond["min_categories"] and len(sessions) >= cond["min_sessions"]:
                progress = ch["target"]
        elif cond["type"] == "single_category_sessions":
            progress = max(category_counts.values()) if category_counts else 0
        elif cond["type"] == "early_sessions":
            progress = early_sessions
        elif cond["type"] == "active_days":
            progress = len(active_days)
        elif cond["type"] == "monthly_time":
            progress = total_time
        elif cond["type"] == "unique_categories":
            progress = len(category_counts)

        is_completed = progress >= ch["target"]

        # Auto-complete if newly completed
        if is_completed and ch["challenge_id"] not in completed_map:
            await db.user_challenges.update_one(
                {"user_id": user["user_id"], "challenge_id": ch["challenge_id"], "month": month_key},
                {"$set": {
                    "completed": True,
                    "completed_at": now.isoformat(),
                    "progress": progress
                }},
                upsert=True
            )

        challenges_with_progress.append({
            "challenge_id": ch["challenge_id"],
            "title": ch["title"],
            "description": ch["description"],
            "icon": ch["icon"],
            "target": ch["target"],
            "progress": min(progress, ch["target"]),
            "completed": is_completed,
            "completed_at": completed_map.get(ch["challenge_id"], {}).get("completed_at")
        })

    total_completed = sum(1 for c in challenges_with_progress if c["completed"])

    return {
        "challenges": challenges_with_progress,
        "is_premium": True,
        "month": month_key,
        "total_completed": total_completed,
        "total_challenges": len(MONTHLY_CHALLENGES)
    }

# ── Community Challenges (free for all) ──────────

COMMUNITY_CHALLENGES = [
    {
        "id": "community_7day_streak",
        "title": "Streak Communautaire",
        "description": "Maintiens un streak de 7 jours ce mois-ci",
        "icon": "flame",
        "target": 7,
        "metric": "streak",
        "reward": "Badge Flamme Communautaire",
    },
    {
        "id": "community_30min_week",
        "title": "30 min cette semaine",
        "description": "Investis 30 minutes de micro-actions en une semaine",
        "icon": "clock",
        "target": 30,
        "metric": "week_minutes",
        "reward": "Badge Investisseur",
    },
    {
        "id": "community_5_sessions",
        "title": "5 sessions ce mois",
        "description": "Complète 5 sessions de micro-actions ce mois-ci",
        "icon": "target",
        "target": 5,
        "metric": "month_sessions",
        "reward": "Badge Régulier",
    },
    {
        "id": "community_3_categories",
        "title": "Explorateur",
        "description": "Pratique dans 3 catégories différentes ce mois-ci",
        "icon": "compass",
        "target": 3,
        "metric": "categories",
        "reward": "Badge Explorateur",
    },
]


@api_router.get("/challenges/community")
@limiter.limit("15/minute")
async def get_community_challenges(request: Request, user: dict = Depends(get_current_user)):
    """Get community challenges open to all users with progress + leaderboard."""
    now = datetime.now(timezone.utc)
    today = now.date()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
    week_start = (today - timedelta(days=today.weekday())).isoformat()
    user_id = user["user_id"]

    # Get user's month sessions
    month_sessions = await db.user_sessions_history.find(
        {"user_id": user_id, "completed": True, "started_at": {"$gte": month_start}},
        {"_id": 0, "actual_duration": 1, "category": 1, "started_at": 1}
    ).to_list(200)

    # Get week sessions
    week_sessions = [s for s in month_sessions if s.get("started_at", "") >= week_start]

    # Compute metrics
    streak = user.get("streak_days", 0)
    week_minutes = sum(s.get("actual_duration", 0) for s in week_sessions)
    month_session_count = len(month_sessions)
    categories = len(set(s.get("category", "") for s in month_sessions if s.get("category")))

    metric_values = {
        "streak": streak,
        "week_minutes": week_minutes,
        "month_sessions": month_session_count,
        "categories": categories,
    }

    # Leaderboard: count how many users completed each challenge
    month_key = now.strftime("%Y-%m")
    leaderboard_pipeline = [
        {"$match": {"month": month_key, "completed": True}},
        {"$group": {"_id": "$challenge_id", "count": {"$sum": 1}}},
    ]
    leaderboard_data = await db.user_challenges.aggregate(leaderboard_pipeline).to_list(20)
    leaderboard_map = {item["_id"]: item["count"] for item in leaderboard_data}

    # Build response
    challenges = []
    for ch in COMMUNITY_CHALLENGES:
        progress = min(metric_values.get(ch["metric"], 0), ch["target"])
        is_completed = progress >= ch["target"]

        # Auto-record completion
        if is_completed:
            await db.user_challenges.update_one(
                {"user_id": user_id, "challenge_id": ch["id"], "month": month_key},
                {"$set": {"completed": True, "completed_at": now.isoformat(), "progress": progress}},
                upsert=True,
            )

        challenges.append({
            "id": ch["id"],
            "title": ch["title"],
            "description": ch["description"],
            "icon": ch["icon"],
            "target": ch["target"],
            "progress": progress,
            "completed": is_completed,
            "reward": ch["reward"],
            "participants_completed": leaderboard_map.get(ch["id"], 0),
        })

    return {
        "challenges": challenges,
        "month": month_key,
    }


@api_router.get("/premium/analytics")
async def get_premium_analytics(user: dict = Depends(get_current_user)):
    """Get advanced analytics for premium users"""
    if user.get("subscription_tier") != "premium":
        return {"is_premium": False, "message": "Fonctionnalité Premium"}

    now = datetime.now(timezone.utc)
    thirty_days_ago = (now - timedelta(days=30)).isoformat()

    # Get sessions from last 30 days
    sessions = await db.user_sessions_history.find(
        {"user_id": user["user_id"], "completed": True, "started_at": {"$gte": thirty_days_ago}},
        {"_id": 0}
    ).sort("started_at", 1).to_list(500)

    # Daily activity
    daily_activity = {}
    hour_distribution = {}
    day_distribution = {}
    category_stats = {}
    day_names = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]

    for s in sessions:
        started = s.get("started_at", "")
        duration = s.get("actual_duration", 0)
        category = s.get("category", "unknown")
        try:
            dt = datetime.fromisoformat(started)
            date_key = dt.date().isoformat()
            daily_activity[date_key] = daily_activity.get(date_key, 0) + 1

            hour = dt.hour
            period = "matin" if hour < 12 else "après-midi" if hour < 18 else "soir"
            hour_distribution[period] = hour_distribution.get(period, 0) + 1

            day_name = day_names[dt.weekday()]
            day_distribution[day_name] = day_distribution.get(day_name, 0) + 1
        except (ValueError, TypeError):
            pass

        if category not in category_stats:
            category_stats[category] = {"sessions": 0, "total_duration": 0}
        category_stats[category]["sessions"] += 1
        category_stats[category]["total_duration"] += duration

    # Best time of day
    best_time = max(hour_distribution, key=hour_distribution.get) if hour_distribution else "matin"

    # Most productive day
    best_day = max(day_distribution, key=day_distribution.get) if day_distribution else "lundi"

    # Category deep dive with averages
    for cat, stats in category_stats.items():
        stats["avg_duration"] = round(stats["total_duration"] / max(stats["sessions"], 1), 1)

    # Streak history (from all-time sessions)
    all_sessions = await db.user_sessions_history.find(
        {"user_id": user["user_id"], "completed": True},
        {"_id": 0, "started_at": 1}
    ).sort("started_at", 1).to_list(2000)

    streak_history = []
    if all_sessions:
        dates = set()
        for s in all_sessions:
            try:
                dt = datetime.fromisoformat(s["started_at"]).date()
                dates.add(dt)
            except (ValueError, TypeError):
                pass
        sorted_dates = sorted(dates)
        if sorted_dates:
            current_start = sorted_dates[0]
            current_end = sorted_dates[0]
            for i in range(1, len(sorted_dates)):
                if (sorted_dates[i] - sorted_dates[i - 1]).days <= 1:
                    current_end = sorted_dates[i]
                else:
                    length = (current_end - current_start).days + 1
                    if length >= 2:
                        streak_history.append({
                            "start": current_start.isoformat(),
                            "end": current_end.isoformat(),
                            "length": length
                        })
                    current_start = sorted_dates[i]
                    current_end = sorted_dates[i]
            length = (current_end - current_start).days + 1
            if length >= 2:
                streak_history.append({
                    "start": current_start.isoformat(),
                    "end": current_end.isoformat(),
                    "length": length
                })

    # Milestone prediction
    total_time = user.get("total_time_invested", 0)
    milestones = [60, 300, 600, 1500, 3000]
    next_milestone = None
    for m in milestones:
        if total_time < m:
            next_milestone = m
            break

    eta_days = None
    if next_milestone and sessions:
        time_last_30 = sum(s.get("actual_duration", 0) for s in sessions)
        daily_avg = time_last_30 / 30
        if daily_avg > 0:
            remaining = next_milestone - total_time
            eta_days = round(remaining / daily_avg)

    return {
        "is_premium": True,
        "daily_activity": daily_activity,
        "best_time_of_day": best_time,
        "most_productive_day": best_day,
        "category_deep_dive": category_stats,
        "streak_history": streak_history[-10:],
        "milestones": {
            "current": total_time,
            "next": next_milestone,
            "eta_days": eta_days
        },
        "sessions_last_30_days": len(sessions),
        "time_last_30_days": sum(s.get("actual_duration", 0) for s in sessions)
    }

# ============== NOTIFICATIONS ==============

@api_router.get("/notifications/preferences")
async def get_notification_preferences(user: dict = Depends(get_current_user)):
    """Get user's notification preferences"""
    prefs = await db.notification_preferences.find_one(
        {"user_id": user["user_id"]},
        {"_id": 0}
    )
    
    if not prefs:
        # Return defaults
        return {
            "user_id": user["user_id"],
            "daily_reminder": True,
            "reminder_time": "09:00",
            "streak_alerts": True,
            "achievement_alerts": True,
            "weekly_summary": True
        }
    
    return prefs

@api_router.put("/notifications/preferences")
async def update_notification_preferences(
    prefs: NotificationPreferences,
    user: dict = Depends(get_current_user)
):
    """Update user's notification preferences"""
    prefs_doc = {
        "user_id": user["user_id"],
        **prefs.model_dump(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.notification_preferences.update_one(
        {"user_id": user["user_id"]},
        {"$set": prefs_doc},
        upsert=True
    )
    
    return prefs_doc

@api_router.get("/notifications/vapid-public-key")
async def get_vapid_public_key():
    """Return VAPID public key so the frontend can subscribe to Web Push."""
    if not VAPID_PUBLIC_KEY:
        raise HTTPException(status_code=503, detail="Web Push not configured")
    return {"public_key": VAPID_PUBLIC_KEY}

@api_router.post("/notifications/subscribe")
async def subscribe_push_notifications(
    request: Request,
    user: dict = Depends(get_current_user)
):
    """Subscribe to push notifications (store push subscription)"""
    body = await request.json()
    subscription = body.get("subscription")
    
    if not subscription:
        raise HTTPException(status_code=400, detail="Subscription data required")
    
    await db.push_subscriptions.update_one(
        {"user_id": user["user_id"]},
        {"$set": {
            "user_id": user["user_id"],
            "subscription": subscription,
            "created_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )
    
    return {"message": "Subscribed to push notifications"}

@api_router.get("/notifications/unread-count")
async def get_unread_notification_count(
    user: dict = Depends(get_current_user),
):
    """Lightweight endpoint for sidebar badge — returns unread count only."""
    count = await db.notifications.count_documents(
        {"user_id": user["user_id"], "read": {"$ne": True}}
    )
    return {"unread_count": count}

@api_router.get("/notifications")
async def get_user_notifications(
    user: dict = Depends(get_current_user),
    limit: int = 20
):
    """Get user's notifications"""
    notifications = await db.notifications.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)

    return notifications

@api_router.post("/notifications/mark-read")
async def mark_notifications_read(
    request: Request,
    user: dict = Depends(get_current_user)
):
    """Mark notifications as read"""
    body = await request.json()
    notification_ids = body.get("notification_ids", [])
    
    if notification_ids:
        await db.notifications.update_many(
            {"user_id": user["user_id"], "notification_id": {"$in": notification_ids}},
            {"$set": {"read": True}}
        )
    else:
        # Mark all as read
        await db.notifications.update_many(
            {"user_id": user["user_id"]},
            {"$set": {"read": True}}
        )
    
    return {"message": "Notifications marked as read"}

# ============== SMART NOTIFICATIONS (Proactive Coach) ==============

@api_router.get("/notifications/smart")
@limiter.limit("10/minute")
async def get_smart_notifications(request: Request, user: dict = Depends(get_current_user)):
    """Generate proactive smart notifications based on user behavior patterns."""
    now = datetime.now(timezone.utc)
    today = now.date()
    today_iso = today.isoformat()
    user_id = user["user_id"]
    smart_notifs = []

    # ── 1. Streak en danger ─────────────────────
    streak = user.get("streak_days", 0)
    last_session_raw = user.get("last_session_date")
    if streak > 0 and last_session_raw:
        if isinstance(last_session_raw, str):
            last_date = datetime.fromisoformat(last_session_raw).date()
        else:
            last_date = last_session_raw.date() if hasattr(last_session_raw, "date") else last_session_raw
        days_since = (today - last_date).days
        if days_since >= 1:
            smart_notifs.append({
                "id": "streak_danger",
                "type": "streak_alert",
                "priority": 1,
                "title": f"Ton streak de {streak} jours est en danger !",
                "message": f"Tu n'as pas pratiqué depuis {days_since} jour{'s' if days_since > 1 else ''}. Un petit 5 min suffit pour garder ta série.",
                "icon": "flame",
                "action_label": "Faire une micro-action",
                "action_url": "/dashboard",
            })

    # ── 2. Objectifs : next step + négligés + progression ───
    objectives = await db.objectives.find(
        {"user_id": user_id, "status": "active", "deleted": {"$ne": True}},
        {"_id": 0, "objective_id": 1, "title": 1, "last_session_at": 1, "streak_days": 1,
         "current_day": 1, "target_duration_days": 1, "daily_minutes": 1,
         "curriculum": 1, "total_sessions": 1}
    ).to_list(20)

    for obj in objectives:
        curriculum = obj.get("curriculum") or []
        completed_steps = [s for s in curriculum if s.get("completed")]
        next_step = next((s for s in curriculum if not s.get("completed")), None)
        total_steps = len(curriculum)
        pct = round((len(completed_steps) / total_steps) * 100) if total_steps > 0 else 0

        # 2a. Prochaine session d'objectif (priorité haute)
        if next_step:
            last_obj_session = obj.get("last_session_at")
            already_today = False
            if last_obj_session:
                ls = last_obj_session if isinstance(last_obj_session, str) else last_obj_session.isoformat()
                already_today = ls.startswith(today_iso)
            if not already_today:
                step_title = next_step.get("title", "Prochaine étape")
                smart_notifs.append({
                    "id": f"obj_next_{obj['objective_id']}",
                    "type": "objective_nudge",
                    "priority": 1,
                    "title": f"Jour {obj.get('current_day', 0) + 1} — {obj['title'][:30]}",
                    "message": f"{step_title} · {obj.get('daily_minutes', 5)} min",
                    "icon": "target",
                    "action_label": "Lancer la session",
                    "action_url": f"/objectives/{obj['objective_id']}",
                })

        # 2b. Objectifs négligés (3+ jours)
        last_obj_session = obj.get("last_session_at")
        if last_obj_session:
            if isinstance(last_obj_session, str):
                last_obj_date = datetime.fromisoformat(last_obj_session).date()
            else:
                last_obj_date = last_obj_session.date() if hasattr(last_obj_session, "date") else today
            days_idle = (today - last_obj_date).days
            if days_idle >= 3:
                smart_notifs.append({
                    "id": f"obj_idle_{obj['objective_id']}",
                    "type": "objective_nudge",
                    "priority": 2,
                    "title": f"Tu n'as pas avancé sur « {obj['title'][:40]} »",
                    "message": f"{days_idle} jours sans session. Reprends avec une micro-session de 5 min !",
                    "icon": "target",
                    "action_label": "Reprendre",
                    "action_url": f"/objectives/{obj['objective_id']}",
                })

        # 2c. Milestones de progression (25%, 50%, 75%)
        if pct in (25, 50, 75):
            smart_notifs.append({
                "id": f"obj_pct_{obj['objective_id']}_{pct}",
                "type": "milestone",
                "priority": 3,
                "title": f"{pct}% de « {obj['title'][:30]} » complété !",
                "message": f"{len(completed_steps)}/{total_steps} sessions terminées. Continue, tu avances bien !",
                "icon": "trophy",
                "action_label": "Voir mon parcours",
                "action_url": f"/objectives/{obj['objective_id']}",
            })

    # ── 3. Routines non faites aujourd'hui ──────
    routines = await db.routines.find(
        {"user_id": user_id, "is_active": True, "deleted": {"$ne": True}},
        {"_id": 0, "routine_id": 1, "name": 1, "time_of_day": 1, "total_minutes": 1, "last_completed_at": 1}
    ).to_list(20)

    hour = now.hour
    current_tod = "morning" if hour < 12 else ("afternoon" if hour < 18 else "evening")
    tod_order = {"morning": 0, "afternoon": 1, "evening": 2, "anytime": 3}

    routines_done_today = 0
    routines_total_active = len(routines)

    for routine in routines:
        last_done = routine.get("last_completed_at", "")
        if last_done and last_done.startswith(today_iso):
            routines_done_today += 1
            continue  # Already done today

        rtod = routine.get("time_of_day", "anytime")
        # Only nudge for current or past time slots (don't nag about evening routine at 8am)
        if rtod != "anytime" and tod_order.get(rtod, 3) > tod_order.get(current_tod, 3):
            continue

        # Enriched: include items count + first item name
        items = routine.get("items") or []
        first_item = items[0]["title"] if items else ""
        detail = f"{len(items)} actions · {routine.get('total_minutes', 0)} min"
        if first_item:
            detail += f" — commence par : {first_item[:35]}"

        smart_notifs.append({
            "id": f"routine_pending_{routine['routine_id']}",
            "type": "routine_reminder",
            "priority": 3 if rtod == current_tod else 4,
            "title": f"Routine « {routine['name'][:40]} » pas encore faite",
            "message": detail,
            "icon": "calendar-clock",
            "action_label": "Lancer",
            "action_url": "/routines",
        })

    # ── 3b. Journée parfaite (toutes routines faites) ──
    if routines_total_active > 0 and routines_done_today >= routines_total_active:
        smart_notifs.append({
            "id": "perfect_day",
            "type": "milestone",
            "priority": 5,
            "title": "Journée parfaite !",
            "message": f"Toutes tes {routines_total_active} habitudes sont complétées. Bravo !",
            "icon": "trophy",
            "action_label": "Voir ma journée",
            "action_url": "/my-day",
        })

    # ── 4. Milestone atteint (celebrate) ────────
    for obj in objectives:
        curr_day = obj.get("current_day", 0)
        if curr_day in (7, 14, 30, 60, 90):
            smart_notifs.append({
                "id": f"milestone_{obj['objective_id']}_{curr_day}",
                "type": "milestone",
                "priority": 2,
                "title": f"Jour {curr_day} sur « {obj['title'][:30]} » !",
                "message": f"Bravo pour ta régularité ! Continue comme ça.",
                "icon": "trophy",
                "action_label": "Voir mon parcours",
                "action_url": f"/objectives/{obj['objective_id']}",
            })

    # ── 5. Conseil énergie (time-based) ─────────
    if hour >= 6 and hour < 10 and not smart_notifs:
        smart_notifs.append({
            "id": "energy_morning",
            "type": "coach_tip",
            "priority": 5,
            "title": "Le matin, ton énergie est à son max",
            "message": "C'est le meilleur moment pour les tâches qui demandent de la concentration.",
            "icon": "zap",
            "action_label": "Ma Journée",
            "action_url": "/my-day",
        })
    elif hour >= 13 and hour < 15 and not smart_notifs:
        smart_notifs.append({
            "id": "energy_afternoon",
            "type": "coach_tip",
            "priority": 5,
            "title": "Début d'après-midi : idéal pour des tâches légères",
            "message": "Profite de ce créneau pour une micro-action créative ou de bien-être.",
            "icon": "zap",
            "action_label": "Ma Journée",
            "action_url": "/my-day",
        })

    # ── 6. Résumé hebdo (affiché 1x par semaine, le lundi ou si pas vu depuis 7j) ──
    if today.weekday() == 0:  # Lundi
        week_ago = (now - timedelta(days=7)).isoformat()
        week_sessions = await db.sessions.count_documents(
            {"user_id": user_id, "completed": True, "completed_at": {"$gte": week_ago}}
        )
        if week_sessions > 0:
            # Aggregate total minutes from last week
            pipeline = [
                {"$match": {"user_id": user_id, "completed": True, "completed_at": {"$gte": week_ago}}},
                {"$group": {"_id": None, "total_min": {"$sum": "$actual_duration"}}},
            ]
            agg = await db.sessions.aggregate(pipeline).to_list(1)
            total_min = agg[0]["total_min"] if agg else 0
            smart_notifs.append({
                "id": f"weekly_recap_{today_iso}",
                "type": "coach_tip",
                "priority": 4,
                "title": f"Ta semaine : {week_sessions} sessions, {total_min} min",
                "message": "Beau travail ! Chaque minute investie compte pour ta progression.",
                "icon": "award",
                "action_label": "Voir ma progression",
                "action_url": "/progress",
            })

    # Sort by priority (lower = more important)
    smart_notifs.sort(key=lambda n: n.get("priority", 99))

    return {"notifications": smart_notifs[:8], "count": len(smart_notifs)}


# ============== B2B DASHBOARD ==============

@api_router.post("/b2b/company")
async def create_company(
    company_data: CompanyCreate,
    user: dict = Depends(get_current_user)
):
    """Create a B2B company account"""
    # Check if user already has a company
    existing = await db.companies.find_one(
        {"admin_user_id": user["user_id"]},
        {"_id": 0}
    )
    
    if existing:
        raise HTTPException(status_code=400, detail="You already have a company")
    
    company_id = f"company_{uuid.uuid4().hex[:12]}"
    company_doc = {
        "company_id": company_id,
        "name": company_data.name,
        "domain": company_data.domain,
        "admin_user_id": user["user_id"],
        "employees": [user["user_id"]],
        "employee_count": 1,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.companies.insert_one(company_doc)
    
    # Update user as company admin
    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {
            "company_id": company_id,
            "is_company_admin": True
        }}
    )
    
    return {"company_id": company_id, "name": company_data.name}

@api_router.get("/b2b/company")
async def get_company(user: dict = Depends(get_current_user)):
    """Get company info for admin"""
    company_id = user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=404, detail="No company found")
    
    company = await db.companies.find_one(
        {"company_id": company_id},
        {"_id": 0}
    )
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return company

@api_router.get("/b2b/dashboard")
async def get_b2b_dashboard(user: dict = Depends(get_current_user)):
    """Get B2B analytics dashboard (anonymized QVT data)"""
    company_id = user.get("company_id")
    
    if not company_id or not user.get("is_company_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    company = await db.companies.find_one(
        {"company_id": company_id},
        {"_id": 0}
    )
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    employee_ids = company.get("employees", [])
    
    # Aggregate anonymized stats
    total_sessions = await db.user_sessions_history.count_documents(
        {"user_id": {"$in": employee_ids}, "completed": True}
    )
    
    total_time_pipeline = [
        {"$match": {"user_id": {"$in": employee_ids}, "completed": True}},
        {"$group": {"_id": None, "total": {"$sum": "$actual_duration"}}}
    ]
    total_time_result = await db.user_sessions_history.aggregate(total_time_pipeline).to_list(1)
    total_time = total_time_result[0]["total"] if total_time_result else 0
    
    # Category distribution
    category_pipeline = [
        {"$match": {"user_id": {"$in": employee_ids}, "completed": True}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}, "time": {"$sum": "$actual_duration"}}}
    ]
    category_stats = await db.user_sessions_history.aggregate(category_pipeline).to_list(10)
    
    # Weekly activity (last 4 weeks)
    four_weeks_ago = (datetime.now(timezone.utc) - timedelta(days=28)).isoformat()
    weekly_pipeline = [
        {"$match": {
            "user_id": {"$in": employee_ids},
            "completed": True,
            "completed_at": {"$gte": four_weeks_ago}
        }},
        {"$group": {
            "_id": {"$substr": ["$completed_at", 0, 10]},
            "sessions": {"$sum": 1},
            "time": {"$sum": "$actual_duration"}
        }},
        {"$sort": {"_id": 1}}
    ]
    daily_activity = await db.user_sessions_history.aggregate(weekly_pipeline).to_list(28)
    
    # Active employees (used app this week)
    one_week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    active_employees = await db.user_sessions_history.distinct(
        "user_id",
        {
            "user_id": {"$in": employee_ids},
            "completed_at": {"$gte": one_week_ago}
        }
    )
    
    # Average per employee
    avg_time_per_employee = total_time / len(employee_ids) if employee_ids else 0
    avg_sessions_per_employee = total_sessions / len(employee_ids) if employee_ids else 0
    
    return {
        "company_name": company["name"],
        "employee_count": len(employee_ids),
        "active_employees_this_week": len(active_employees),
        "engagement_rate": round(len(active_employees) / len(employee_ids) * 100, 1) if employee_ids else 0,
        "total_sessions": total_sessions,
        "total_time_minutes": total_time,
        "avg_time_per_employee": round(avg_time_per_employee, 1),
        "avg_sessions_per_employee": round(avg_sessions_per_employee, 1),
        "category_distribution": {
            stat["_id"]: {"sessions": stat["count"], "time": stat["time"]}
            for stat in category_stats
        },
        "daily_activity": daily_activity,
        "qvt_score": min(100, round(len(active_employees) / len(employee_ids) * 100 + (total_time / len(employee_ids) / 10) if employee_ids else 0, 1))
    }

@api_router.post("/b2b/invite")
async def invite_employee(
    invite: InviteEmployee,
    user: dict = Depends(get_current_user)
):
    """Invite an employee to the company"""
    company_id = user.get("company_id")
    
    if not company_id or not user.get("is_company_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Check if email domain matches company domain
    company = await db.companies.find_one(
        {"company_id": company_id},
        {"_id": 0}
    )
    
    email_domain = invite.email.split("@")[1]
    if email_domain != company["domain"]:
        raise HTTPException(
            status_code=400,
            detail=f"Email must be from {company['domain']} domain"
        )
    
    # Create invitation
    invite_id = f"invite_{uuid.uuid4().hex[:12]}"
    invite_doc = {
        "invite_id": invite_id,
        "company_id": company_id,
        "email": invite.email,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    }
    
    await db.company_invites.insert_one(invite_doc)
    
    return {"invite_id": invite_id, "email": invite.email, "status": "pending"}

@api_router.get("/b2b/employees")
async def get_employees(user: dict = Depends(get_current_user)):
    """Get list of company employees (anonymized for privacy)"""
    company_id = user.get("company_id")
    
    if not company_id or not user.get("is_company_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    company = await db.companies.find_one(
        {"company_id": company_id},
        {"_id": 0}
    )
    
    employee_ids = company.get("employees", [])
    
    # Get anonymized employee stats
    employees = []
    for i, emp_id in enumerate(employee_ids):
        emp = await db.users.find_one({"user_id": emp_id}, {"_id": 0})
        if emp:
            sessions = await db.user_sessions_history.count_documents(
                {"user_id": emp_id, "completed": True}
            )
            employees.append({
                "employee_number": i + 1,
                "name": emp.get("name", "Collaborateur"),
                "total_time": emp.get("total_time_invested", 0),
                "streak_days": emp.get("streak_days", 0),
                "total_sessions": sessions,
                "is_admin": emp_id == user["user_id"]
            })
    
    return {"employees": employees, "total": len(employees)}

# ============== OBJECTIVES + ROUTINES ROUTES (imported) ==============
from routes.objectives import router as objectives_router
from routes.routines import router as routines_router
api_router.include_router(objectives_router)
api_router.include_router(routines_router)

# ============== REFLECTIONS / JOURNAL ==============

@api_router.post("/reflections")
async def create_reflection(
    reflection: ReflectionCreate,
    user: dict = Depends(get_current_user)
):
    """Create a new reflection entry"""
    reflection_id = f"ref_{uuid.uuid4().hex[:12]}"
    
    reflection_doc = {
        "reflection_id": reflection_id,
        "user_id": user["user_id"],
        "content": reflection.content,
        "mood": reflection.mood,
        "tags": reflection.tags or [],
        "related_session_id": reflection.related_session_id,
        "related_category": reflection.related_category,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.reflections.insert_one(reflection_doc)
    
    return {**reflection_doc, "_id": None}

@api_router.get("/reflections")
async def get_reflections(
    user: dict = Depends(get_current_user),
    limit: int = 50,
    skip: int = 0
):
    """Get user's reflections"""
    reflections = await db.reflections.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    total = await db.reflections.count_documents({"user_id": user["user_id"]})
    
    return {"reflections": reflections, "total": total}

@api_router.get("/reflections/week")
async def get_week_reflections(user: dict = Depends(get_current_user)):
    """Get this week's reflections"""
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    
    reflections = await db.reflections.find(
        {"user_id": user["user_id"], "created_at": {"$gte": week_ago}},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return {"reflections": reflections, "count": len(reflections)}

@api_router.delete("/reflections/{reflection_id}")
async def delete_reflection(
    reflection_id: str,
    user: dict = Depends(get_current_user)
):
    """Delete a reflection"""
    result = await db.reflections.delete_one({
        "reflection_id": reflection_id,
        "user_id": user["user_id"]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Reflection not found")
    
    return {"message": "Reflection deleted"}

@api_router.get("/reflections/summary")
async def get_reflections_summary(user: dict = Depends(get_current_user)):
    """Generate AI-powered weekly summary of reflections"""
    # Get reflections from the last 4 weeks
    month_ago = (datetime.now(timezone.utc) - timedelta(days=28)).isoformat()

    reflections = await db.reflections.find(
        {"user_id": user["user_id"], "created_at": {"$gte": month_ago}},
        {"_id": 0}
    ).sort("created_at", 1).to_list(200)

    if not reflections:
        return {
            "summary": None,
            "message": "Pas encore assez de réflexions pour générer un résumé. Commencez à noter vos pensées!",
            "reflection_count": 0
        }

    # Get sessions data for context
    sessions = await db.user_sessions_history.find(
        {"user_id": user["user_id"], "completed": True, "started_at": {"$gte": month_ago}},
        {"_id": 0}
    ).to_list(100)

    # Build reflection context
    reflections_text = "\n".join([
        f"[{r['created_at'][:10]}] {r.get('mood', 'neutre')}: {r['content']}"
        for r in reflections[-30:]
    ])

    # Session stats
    category_counts = {}
    total_time = 0
    for s in sessions:
        cat = s.get("category", "autre")
        category_counts[cat] = category_counts.get(cat, 0) + 1
        total_time += s.get("actual_duration", 0)

    system_msg = """Tu es le compagnon cognitif InFinea. Ton rôle est d'analyser les réflexions
de l'utilisateur et de fournir un résumé personnalisé, bienveillant et perspicace.
Tu dois identifier les patterns, les progrès et suggérer des axes d'amélioration.
Réponds toujours en français, de manière empathique et constructive."""

    prompt = f"""Analyse les réflexions suivantes de l'utilisateur sur les 4 dernières semaines:

{reflections_text}

Contexte d'activité:
- Sessions complétées: {len(sessions)}
- Temps total investi: {total_time} minutes
- Répartition: {', '.join([f'{k}: {v}' for k, v in category_counts.items()])}

Génère un résumé structuré en JSON avec:
- "weekly_insight": Une observation clé sur les tendances de la semaine (2-3 phrases max)
- "patterns_identified": Liste de 2-3 patterns comportementaux observés
- "strengths": Ce qui fonctionne bien (1-2 points)
- "areas_for_growth": Suggestions d'amélioration bienveillantes (1-2 points)
- "personalized_tip": Un conseil personnalisé basé sur les réflexions
- "mood_trend": Tendance générale de l'humeur (positive, stable, en progression, à surveiller)"""

    response = await call_ai(f"summary_{user['user_id']}", system_msg, prompt, model=get_ai_model(user))
    ai_summary = parse_ai_json(response)

    fallback_summary = {
        "weekly_insight": "Continuez à noter vos réflexions pour un résumé plus détaillé.",
        "patterns_identified": [],
        "strengths": [],
        "areas_for_growth": [],
        "personalized_tip": "Essayez de noter au moins une réflexion par jour.",
        "mood_trend": "stable"
    }

    if not ai_summary:
        ai_summary = fallback_summary

    # Store summary for history
    summary_doc = {
        "summary_id": f"sum_{uuid.uuid4().hex[:12]}",
        "user_id": user["user_id"],
        "summary": ai_summary,
        "reflection_count": len(reflections),
        "period_start": month_ago,
        "period_end": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.reflection_summaries.insert_one(summary_doc)

    return {
        "summary": ai_summary,
        "reflection_count": len(reflections),
        "session_count": len(sessions),
        "total_time": total_time
    }

@api_router.get("/reflections/summaries")
async def get_past_summaries(
    user: dict = Depends(get_current_user),
    limit: int = 10
):
    """Get past generated summaries"""
    summaries = await db.reflection_summaries.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return {"summaries": summaries}

# ============== NOTES ROUTES ==============

NOTES_QUERY = {
    "completed": True,
    "notes": {"$exists": True, "$nin": [None, ""]}
}

@api_router.get("/notes/stats")
async def get_notes_stats(user: dict = Depends(get_current_user)):
    """Quick stats about user's session notes"""
    base_query = {"user_id": user["user_id"], **NOTES_QUERY}

    total_notes = await db.user_sessions_history.count_documents(base_query)

    week_start = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    notes_this_week = await db.user_sessions_history.count_documents({
        **base_query,
        "completed_at": {"$gte": week_start}
    })

    pipeline = [
        {"$match": base_query},
        {"$group": {"_id": "$category", "count": {"$sum": 1}}}
    ]
    category_stats = await db.user_sessions_history.aggregate(pipeline).to_list(15)
    categories = {stat["_id"]: stat["count"] for stat in category_stats if stat["_id"]}

    pipeline_avg = [
        {"$match": base_query},
        {"$project": {"note_length": {"$strLenCP": "$notes"}}},
        {"$group": {"_id": None, "avg_length": {"$avg": "$note_length"}}}
    ]
    avg_result = await db.user_sessions_history.aggregate(pipeline_avg).to_list(1)
    avg_note_length = int(avg_result[0]["avg_length"]) if avg_result else 0

    return {
        "total_notes": total_notes,
        "notes_this_week": notes_this_week,
        "categories": categories,
        "avg_note_length": avg_note_length,
    }

@api_router.get("/notes/analysis")
async def get_notes_analysis(
    user: dict = Depends(get_current_user),
    force: bool = False
):
    """AI-powered analysis of user's session notes with caching"""
    user_id = user["user_id"]
    is_premium = user.get("subscription_tier") == "premium"

    # Check cache first (unless force refresh)
    if not force:
        cache_hours = 12 if is_premium else 24
        cache_cutoff = (datetime.now(timezone.utc) - timedelta(hours=cache_hours)).isoformat()
        cached = await db.notes_analysis_cache.find_one(
            {"user_id": user_id, "generated_at": {"$gte": cache_cutoff}},
            {"_id": 0}
        )
        if cached:
            return {
                "analysis": cached["analysis"],
                "generated_at": cached["generated_at"],
                "cached": True,
                "note_count": cached.get("note_count", 0),
            }

    # Usage limit for free users (force refresh only)
    if not is_premium and force:
        usage = await check_usage_limit(user_id, "notes_analysis", 1, "daily")
        if not usage["allowed"]:
            return {
                "analysis": None,
                "error": "limit_reached",
                "message": "Vous avez atteint la limite d'analyses aujourd'hui. Passez Premium pour des analyses illimitées !",
                "usage": usage,
            }

    # Fetch notes
    lookback_days = 90 if is_premium else 30
    cutoff = (datetime.now(timezone.utc) - timedelta(days=lookback_days)).isoformat()

    sessions_with_notes = await db.user_sessions_history.find(
        {"user_id": user_id, **NOTES_QUERY, "completed_at": {"$gte": cutoff}},
        {"_id": 0}
    ).sort("completed_at", -1).to_list(50)

    if len(sessions_with_notes) < 3:
        return {
            "analysis": None,
            "message": "Complétez quelques sessions avec des notes pour générer une analyse.",
            "note_count": len(sessions_with_notes),
            "min_required": 3,
        }

    # Build notes context
    notes_text = "\n".join([
        f"[{s.get('completed_at', '')[:10]}] {s.get('action_title', 'Action')} ({s.get('category', 'autre')}): {s['notes']}"
        for s in sessions_with_notes
    ])

    cat_counts = {}
    for s in sessions_with_notes:
        cat = s.get("category", "autre")
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

    categories_fr = {
        "learning": "apprentissage", "productivity": "productivité",
        "well_being": "bien-être", "creativity": "créativité",
        "fitness": "forme physique", "mindfulness": "pleine conscience",
        "leadership": "leadership", "finance": "finance",
        "relations": "relations", "mental_health": "santé mentale",
        "entrepreneurship": "entrepreneuriat",
    }
    cat_summary = ", ".join([f"{categories_fr.get(k, k)}: {v} notes" for k, v in cat_counts.items()])

    user_context = await build_user_context(user)

    system_msg = """Tu es le compagnon cognitif InFinea. Tu analyses les notes de session de l'utilisateur
pour identifier des patterns d'apprentissage, des progrès, et fournir des insights personnalisés.
Tes analyses sont profondes, bienveillantes et actionables. Réponds toujours en français.
Réponds UNIQUEMENT en JSON valide, sans texte autour."""

    if is_premium:
        prompt = f"""{user_context}

Voici les notes de session de l'utilisateur sur les 3 derniers mois ({len(sessions_with_notes)} notes) :

{notes_text}

Répartition des catégories : {cat_summary}

Fais une analyse approfondie et réponds en JSON :
{{
    "key_insight": "L'observation la plus importante sur le parcours de l'utilisateur (2-3 phrases)",
    "patterns": ["Pattern 1 identifié dans les notes", "Pattern 2", "Pattern 3"],
    "strengths": ["Point fort 1 observé", "Point fort 2"],
    "growth_areas": ["Axe de progression 1", "Axe de progression 2"],
    "emotional_trends": "Analyse de l'évolution émotionnelle à travers les notes (1-2 phrases)",
    "connections": "Liens entre différentes sessions et thèmes (1-2 phrases)",
    "personalized_recommendation": "Conseil personnalisé basé sur l'ensemble des notes (2-3 phrases)",
    "focus_suggestion": "Suggestion de focus pour la semaine à venir (1 phrase)"
}}"""
    else:
        prompt = f"""{user_context}

Voici les notes de session récentes de l'utilisateur ({len(sessions_with_notes)} notes) :

{notes_text}

Répartition : {cat_summary}

Fais une analyse et réponds en JSON :
{{
    "key_insight": "L'observation la plus importante (1-2 phrases)",
    "patterns": ["Pattern 1", "Pattern 2"],
    "strengths": ["Point fort observé"],
    "growth_areas": ["Axe de progression"],
    "personalized_recommendation": "Conseil personnalisé (1-2 phrases)"
}}"""

    ai_response = await call_ai(
        f"notes_analysis_{user_id}",
        system_msg,
        prompt,
        model=get_ai_model(user),
    )
    ai_result = parse_ai_json(ai_response)

    # Fallback if AI fails
    if not ai_result:
        top_category = max(cat_counts, key=cat_counts.get) if cat_counts else "general"
        ai_result = {
            "key_insight": f"Vous avez écrit {len(sessions_with_notes)} notes, principalement en {categories_fr.get(top_category, top_category)}. Continuez à documenter vos sessions !",
            "patterns": [],
            "strengths": ["Régularité dans la prise de notes"],
            "growth_areas": ["Essayez d'approfondir vos réflexions"],
            "personalized_recommendation": "Notez ce que vous avez appris ET ce que vous ressentez pour des analyses plus riches.",
        }

    # Cache the result
    await db.notes_analysis_cache.update_one(
        {"user_id": user_id},
        {"$set": {
            "user_id": user_id,
            "analysis": ai_result,
            "note_count": len(sessions_with_notes),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }},
        upsert=True,
    )

    return {
        "analysis": ai_result,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "cached": False,
        "note_count": len(sessions_with_notes),
    }

@api_router.get("/notes")
async def get_user_notes(
    user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 20,
    category: Optional[str] = None,
):
    """Get all sessions with non-empty notes, paginated"""
    query = {"user_id": user["user_id"], **NOTES_QUERY}
    if category:
        query["category"] = category

    total = await db.user_sessions_history.count_documents(query)

    notes = await db.user_sessions_history.find(
        query,
        {"_id": 0, "session_id": 1, "action_title": 1, "category": 1,
         "notes": 1, "completed_at": 1, "actual_duration": 1}
    ).sort("completed_at", -1).skip(skip).limit(limit).to_list(limit)

    return {
        "notes": notes,
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_more": (skip + limit) < total,
    }

@api_router.delete("/notes/{session_id}")
async def delete_note(session_id: str, user: dict = Depends(get_current_user)):
    """Clear the notes field from a session (does not delete the session itself)"""
    result = await db.user_sessions_history.update_one(
        {"session_id": session_id, "user_id": user["user_id"]},
        {"$set": {"notes": None}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Note non trouvée")
    return {"status": "success", "message": "Note supprimée"}

# ============== FEATURE FLAGS ==============

FEATURE_UNIFIED_INTEGRATIONS = os.environ.get("FEATURE_UNIFIED_INTEGRATIONS", "true") == "true"

@api_router.get("/feature-flags")
async def get_feature_flags():
    """Public feature flags for frontend conditional rendering."""
    return {
        "unified_integrations": FEATURE_UNIFIED_INTEGRATIONS,
    }

# ============== UNIFIED INTEGRATION STATUS ==============

@api_router.get("/integrations/status")
async def get_integrations_status(request: Request, user: dict = Depends(get_current_user)):
    """Unified status with smart connect routing — tells frontend exactly how to connect each service."""
    integrations_docs = await db.user_integrations.find(
        {"user_id": user["user_id"]},
        {"_id": 0, "access_token": 0, "refresh_token": 0}
    ).to_list(20)

    connected_map = {}
    for i in integrations_docs:
        key = i.get("service") or i.get("provider")
        if key:
            connected_map[key] = i

    all_services = {
        "google_calendar": {
            "name": "Google Calendar",
            "category": "calendrier",
            "description": "D\u00e9tecte automatiquement vos cr\u00e9neaux libres entre les r\u00e9unions",
        },
        "ical": {
            "name": "Apple Calendar",
            "category": "calendrier",
            "description": "Importez votre calendrier Apple pour d\u00e9tecter vos cr\u00e9neaux libres",
        },
        "notion": {
            "name": "Notion",
            "category": "notes",
            "description": "Exportez vos sessions comme pages Notion automatiquement",
        },
        "todoist": {
            "name": "Todoist",
            "category": "t\u00e2ches",
            "description": "Loguez vos sessions comme t\u00e2ches compl\u00e9t\u00e9es dans Todoist",
        },
        "slack": {
            "name": "Slack",
            "category": "communication",
            "description": "Recevez vos r\u00e9sum\u00e9s hebdomadaires directement dans Slack",
        },
    }

    # Use BACKEND_URL env var — critical for OAuth redirect_uri to match Google Console config
    backend_url = os.environ.get("BACKEND_URL", "https://infinea-api.onrender.com")

    result = {}
    for service_key, meta in all_services.items():
        connected = connected_map.get(service_key)
        config = INTEGRATION_CONFIGS.get(service_key)
        has_oauth = bool(os.environ.get(config["env_client_id"])) if config else False
        has_token = service_key in TOKEN_CONNECT_VALIDATORS
        has_url = service_key in ("ical", "google_calendar") and ICAL_AVAILABLE

        status = "disconnected"
        if connected:
            status = "error" if connected.get("last_error") else "connected"

        # Smart connect routing: determine the best method and pre-generate URL if OAuth
        preferred_method = None
        connect_url = None
        token_config = None

        if not connected:
            if service_key in ("ical", "google_calendar", "notion", "todoist", "slack"):
                preferred_method = "guided"
            elif has_oauth:
                preferred_method = "oauth"
                # Pre-generate OAuth URL so frontend redirects in one click
                try:
                    client_id = os.environ.get(config["env_client_id"])
                    state = f"{user['user_id']}:{uuid.uuid4().hex[:16]}"
                    await db.integration_states.insert_one({
                        "state": state, "user_id": user["user_id"],
                        "service": service_key,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
                    })
                    if service_key == "google_calendar":
                        # Reuse the login callback URI (already registered in Google Console)
                        redirect_uri = f"{backend_url}/api/auth/google/callback"
                        gcal_state = f"gcal_integrate:{state}"
                        await db.integration_states.update_one(
                            {"state": state}, {"$set": {"state": gcal_state}}
                        )
                        params = {"client_id": client_id, "state": gcal_state}
                        params.update({"redirect_uri": redirect_uri, "response_type": "code",
                                       "scope": config["scopes"], "access_type": "offline", "prompt": "consent"})
                    else:
                        redirect_uri = f"{backend_url}/api/integrations/callback/{service_key}"
                        params = {"client_id": client_id, "state": state}
                        if service_key == "notion":
                            params.update({"redirect_uri": redirect_uri, "response_type": "code", "owner": "user"})
                        elif service_key == "todoist":
                            params.update({"scope": config["scopes"]})
                        elif service_key == "slack":
                            params.update({"scope": config["scopes"], "redirect_uri": redirect_uri})
                    connect_url = f"{config['auth_url']}?{urllib.parse.urlencode(params)}"
                except Exception as e:
                    logger.warning(f"Failed to pre-generate OAuth URL for {service_key}: {e}")
                    if has_token:
                        preferred_method = "token"
            elif has_token:
                preferred_method = "token"
                tc = TOKEN_CONNECT_VALIDATORS.get(service_key, {})
                token_config = {
                    "label": tc.get("description", f"Token {meta['name']}"),
                    "placeholder": tc.get("placeholder", ""),
                    "help_url": tc.get("help_url", ""),
                    "service_name": tc.get("name", meta["name"]),
                }
            elif has_url:
                preferred_method = "url"

        result[service_key] = {
            **meta,
            "status": status,
            "connected": bool(connected),
            "connected_at": connected.get("connected_at") if connected else None,
            "account_name": connected.get("account_name") if connected else None,
            "last_sync": connected.get("last_synced_at") if connected else None,
            "last_error": connected.get("last_error") if connected else None,
            "available": has_oauth or has_token or has_url,
            "connection_type": connected.get("connection_type", "oauth") if connected else None,
            "preferred_method": preferred_method,
            "connect_url": connect_url,
            "token_config": token_config,
        }

    return result

@api_router.post("/integrations/{service}/test")
async def test_integration(service: str, user: dict = Depends(get_current_user)):
    """Test that a connected integration still works."""
    integration = await db.user_integrations.find_one(
        {"user_id": user["user_id"], "service": service}
    )
    if not integration:
        integration = await db.user_integrations.find_one(
            {"user_id": user["user_id"], "provider": service}
        )
    if not integration:
        raise HTTPException(status_code=404, detail="Intégration non connectée")

    encrypted_token = integration.get("access_token")
    if not encrypted_token:
        raise HTTPException(status_code=400, detail="Pas de token stocké")

    try:
        token = decrypt_token(encrypted_token)
    except Exception:
        await db.user_integrations.update_one(
            {"user_id": user["user_id"], "service": service},
            {"$set": {"last_error": "Token corrompu — reconnectez le service"}}
        )
        return {"ok": False, "error": "Token corrompu — reconnectez le service"}

    try:
        async with httpx.AsyncClient(timeout=10.0) as http_client:
            if service == "ical":
                # iCal: test by fetching the URL
                url = token
                if url.startswith("webcal://"):
                    url = "https://" + url[len("webcal://"):]
                resp = await http_client.get(url, follow_redirects=True)
                ok = resp.status_code == 200
            elif service == "google_calendar":
                resp = await http_client.get(
                    "https://www.googleapis.com/calendar/v3/users/me/calendarList?maxResults=1",
                    headers={"Authorization": f"Bearer {token}"}
                )
                ok = resp.status_code == 200
            elif service == "notion":
                resp = await http_client.get(
                    "https://api.notion.com/v1/users/me",
                    headers={"Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28"}
                )
                ok = resp.status_code == 200
            elif service == "todoist":
                resp = await http_client.get(
                    "https://api.todoist.com/rest/v2/projects",
                    headers={"Authorization": f"Bearer {token}"}
                )
                ok = resp.status_code == 200
            elif service == "slack":
                # Slack webhook: can't test without sending a message, just check format
                ok = token.startswith("https://hooks.slack.com/")
            else:
                raise HTTPException(status_code=400, detail="Service inconnu")

        error_msg = None if ok else f"Service {service} a répondu avec une erreur (HTTP {resp.status_code})"
        await db.user_integrations.update_one(
            {"user_id": user["user_id"], "service": service},
            {"$set": {"last_tested_at": datetime.now(timezone.utc).isoformat(), "last_error": error_msg}}
        )
        return {"ok": ok, "error": error_msg}

    except httpx.TimeoutException:
        error_msg = "Timeout — le service ne répond pas"
        await db.user_integrations.update_one(
            {"user_id": user["user_id"], "service": service},
            {"$set": {"last_error": error_msg}}
        )
        return {"ok": False, "error": error_msg}
    except Exception as e:
        error_msg = f"Erreur de connexion : {str(e)[:100]}"
        await db.user_integrations.update_one(
            {"user_id": user["user_id"], "service": service},
            {"$set": {"last_error": error_msg}}
        )
        return {"ok": False, "error": error_msg}

# ============== DUO / GROUPE (D.3) ==============
# Pattern: Duolingo Friends Quest — small bounded groups (2-10), embedded members.
# Single-document design (MongoDB best practice for bounded arrays <50 elements).

GROUP_MAX_MEMBERS = 10
GROUP_CATEGORIES = {"learning", "productivity", "well_being", "creativity", "fitness", "mindfulness"}


async def _refresh_group_member_stats(group_doc: dict) -> dict:
    """Refresh live stats for all members of a group. Lightweight — only reads user docs."""
    user_ids = [m["user_id"] for m in group_doc.get("members", [])]
    if not user_ids:
        return group_doc
    users = await db.users.find(
        {"user_id": {"$in": user_ids}},
        {"_id": 0, "user_id": 1, "streak_days": 1, "total_time_invested": 1}
    ).to_list(GROUP_MAX_MEMBERS)
    user_map = {u["user_id"]: u for u in users}

    now = datetime.now(timezone.utc)
    week_start = (now.date() - timedelta(days=now.weekday())).isoformat()

    # Batch query: week minutes per member
    week_pipeline = [
        {"$match": {"user_id": {"$in": user_ids}, "completed": True, "completed_at": {"$gte": week_start}}},
        {"$group": {"_id": "$user_id", "week_minutes": {"$sum": "$actual_duration"}, "week_sessions": {"$sum": 1}}}
    ]
    week_stats = {s["_id"]: s for s in await db.user_sessions_history.aggregate(week_pipeline).to_list(GROUP_MAX_MEMBERS)}

    for member in group_doc["members"]:
        uid = member["user_id"]
        u = user_map.get(uid, {})
        ws = week_stats.get(uid, {})
        member["stats"] = {
            "streak_days": u.get("streak_days", 0),
            "total_time_invested": u.get("total_time_invested", 0),
            "week_minutes": ws.get("week_minutes", 0),
            "week_sessions": ws.get("week_sessions", 0),
        }
    return group_doc


@api_router.post("/groups")
@limiter.limit("5/minute")
async def create_group(request: Request, body: GroupCreate, user: dict = Depends(get_current_user)):
    """Create a new duo/group. The creator becomes the owner."""
    # Check user isn't in too many groups (limit: 5 active)
    existing = await db.groups.count_documents(
        {"members.user_id": user["user_id"], "status": "active"}
    )
    if existing >= 5:
        raise HTTPException(status_code=400, detail="Maximum 5 groupes actifs autorisés")

    group_id = f"grp_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()

    group_doc = {
        "group_id": group_id,
        "name": body.name.strip(),
        "objective_title": (body.objective_title or "").strip() or None,
        "category": body.category if body.category in GROUP_CATEGORIES else None,
        "owner_id": user["user_id"],
        "members": [{
            "user_id": user["user_id"],
            "name": user.get("name", ""),
            "role": "owner",
            "joined_at": now,
            "stats": {
                "streak_days": user.get("streak_days", 0),
                "total_time_invested": user.get("total_time_invested", 0),
                "week_minutes": 0,
                "week_sessions": 0,
            },
        }],
        "invites": [],
        "max_members": GROUP_MAX_MEMBERS,
        "status": "active",
        "created_at": now,
    }
    await db.groups.insert_one(group_doc)
    return {"group_id": group_id, "message": "Groupe créé"}


@api_router.get("/groups")
async def list_groups(user: dict = Depends(get_current_user)):
    """List all groups the user belongs to."""
    groups = await db.groups.find(
        {"members.user_id": user["user_id"], "status": "active"},
        {"_id": 0}
    ).sort("created_at", -1).to_list(10)

    # Refresh stats for all groups
    for g in groups:
        await _refresh_group_member_stats(g)
    return {"groups": groups}


@api_router.get("/groups/{group_id}")
async def get_group(group_id: str, user: dict = Depends(get_current_user)):
    """Get a single group with refreshed member stats."""
    group = await db.groups.find_one(
        {"group_id": group_id, "members.user_id": user["user_id"], "status": "active"},
        {"_id": 0}
    )
    if not group:
        raise HTTPException(status_code=404, detail="Groupe introuvable")
    await _refresh_group_member_stats(group)
    return group


@api_router.post("/groups/{group_id}/invite")
@limiter.limit("10/minute")
async def invite_to_group(request: Request, group_id: str, body: GroupInvite, user: dict = Depends(get_current_user)):
    """Invite someone to a group by email."""
    group = await db.groups.find_one(
        {"group_id": group_id, "members.user_id": user["user_id"], "status": "active"}
    )
    if not group:
        raise HTTPException(status_code=404, detail="Groupe introuvable")

    if len(group.get("members", [])) + len([i for i in group.get("invites", []) if i["status"] == "pending"]) >= GROUP_MAX_MEMBERS:
        raise HTTPException(status_code=400, detail=f"Maximum {GROUP_MAX_MEMBERS} membres par groupe")

    # Check if already member
    if any(m["user_id"] == body.email for m in group.get("members", [])):
        raise HTTPException(status_code=400, detail="Déjà membre du groupe")

    # Check if already invited (pending)
    if any(i["email"] == body.email and i["status"] == "pending" for i in group.get("invites", [])):
        raise HTTPException(status_code=400, detail="Invitation déjà envoyée")

    now = datetime.now(timezone.utc)
    invite = {
        "invite_id": f"ginv_{uuid.uuid4().hex[:12]}",
        "email": body.email,
        "inviter_name": user.get("name", ""),
        "status": "pending",
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(days=7)).isoformat(),
    }

    await db.groups.update_one(
        {"group_id": group_id},
        {"$push": {"invites": invite}}
    )

    # If the invitee already has an account, create a notification
    invitee = await db.users.find_one({"email": body.email}, {"user_id": 1})
    if invitee:
        await db.notifications.insert_one({
            "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
            "user_id": invitee["user_id"],
            "type": "group_invite",
            "title": "Invitation à un groupe",
            "message": f"{user.get('name', 'Quelqu\'un')} t'invite à rejoindre « {group['name']} »",
            "icon": "users",
            "data": {"group_id": group_id, "invite_id": invite["invite_id"]},
            "read": False,
            "created_at": now.isoformat(),
        })
        try:
            await send_push_to_user(
                invitee["user_id"],
                "Invitation à un groupe",
                f"{user.get('name', 'Quelqu\'un')} t'invite à rejoindre « {group['name']} »",
                url="/groups",
                tag="group-invite",
            )
        except Exception:
            pass  # Push is best-effort, never blocks

    return {"message": "Invitation envoyée", "invite_id": invite["invite_id"]}


@api_router.post("/groups/{group_id}/join")
async def join_group(group_id: str, user: dict = Depends(get_current_user)):
    """Accept an invitation and join a group."""
    group = await db.groups.find_one({"group_id": group_id, "status": "active"})
    if not group:
        raise HTTPException(status_code=404, detail="Groupe introuvable")

    # Check if already a member
    if any(m["user_id"] == user["user_id"] for m in group.get("members", [])):
        raise HTTPException(status_code=400, detail="Déjà membre de ce groupe")

    # Check pending invite for this user
    email = user.get("email", "")
    invite_found = False
    for inv in group.get("invites", []):
        if inv["email"] == email and inv["status"] == "pending":
            invite_found = True
            break

    if not invite_found:
        raise HTTPException(status_code=403, detail="Aucune invitation en attente pour ce compte")

    if len(group.get("members", [])) >= GROUP_MAX_MEMBERS:
        raise HTTPException(status_code=400, detail="Groupe complet")

    now = datetime.now(timezone.utc).isoformat()

    # Add member + mark invite as accepted (atomic)
    await db.groups.update_one(
        {"group_id": group_id, "invites.email": email, "invites.status": "pending"},
        {
            "$push": {"members": {
                "user_id": user["user_id"],
                "name": user.get("name", ""),
                "role": "member",
                "joined_at": now,
                "stats": {
                    "streak_days": user.get("streak_days", 0),
                    "total_time_invested": user.get("total_time_invested", 0),
                    "week_minutes": 0, "week_sessions": 0,
                },
            }},
            "$set": {"invites.$[inv].status": "accepted"},
        },
        array_filters=[{"inv.email": email, "inv.status": "pending"}],
    )

    # Notify group owner
    await db.notifications.insert_one({
        "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
        "user_id": group["owner_id"],
        "type": "group_member_joined",
        "title": "Nouveau membre",
        "message": f"{user.get('name', 'Quelqu\'un')} a rejoint « {group['name']} »",
        "icon": "user-plus",
        "read": False,
        "created_at": now,
    })

    return {"message": f"Bienvenue dans « {group['name']} » !"}


@api_router.post("/groups/{group_id}/leave")
async def leave_group(group_id: str, user: dict = Depends(get_current_user)):
    """Leave a group. Owner cannot leave — must archive instead."""
    group = await db.groups.find_one(
        {"group_id": group_id, "members.user_id": user["user_id"], "status": "active"}
    )
    if not group:
        raise HTTPException(status_code=404, detail="Groupe introuvable")

    if group["owner_id"] == user["user_id"]:
        raise HTTPException(status_code=400, detail="Le créateur ne peut pas quitter le groupe. Utilisez l'archivage.")

    await db.groups.update_one(
        {"group_id": group_id},
        {"$pull": {"members": {"user_id": user["user_id"]}}}
    )
    return {"message": "Vous avez quitté le groupe"}


@api_router.delete("/groups/{group_id}")
async def archive_group(group_id: str, user: dict = Depends(get_current_user)):
    """Archive a group (owner only). Soft delete — never hard delete."""
    group = await db.groups.find_one({"group_id": group_id, "status": "active"})
    if not group:
        raise HTTPException(status_code=404, detail="Groupe introuvable")
    if group["owner_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Seul le créateur peut archiver le groupe")

    await db.groups.update_one(
        {"group_id": group_id},
        {"$set": {"status": "archived", "archived_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "Groupe archivé"}


@api_router.get("/groups/{group_id}/feed")
async def get_group_feed(group_id: str, user: dict = Depends(get_current_user)):
    """Get recent activity feed for a group — last 7 days of sessions from all members.
    Pattern: Strava Club activity feed — chronological, lightweight."""
    group = await db.groups.find_one(
        {"group_id": group_id, "members.user_id": user["user_id"], "status": "active"}
    )
    if not group:
        raise HTTPException(status_code=404, detail="Groupe introuvable")

    member_ids = [m["user_id"] for m in group.get("members", [])]
    member_names = {m["user_id"]: m["name"] for m in group["members"]}
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

    sessions = await db.user_sessions_history.find(
        {"user_id": {"$in": member_ids}, "completed": True, "completed_at": {"$gte": week_ago}},
        {"_id": 0, "user_id": 1, "action_title": 1, "category": 1, "actual_duration": 1, "completed_at": 1}
    ).sort("completed_at", -1).limit(50).to_list(50)

    # Enrich with member name (never expose user_id to frontend)
    feed = []
    for s in sessions:
        feed.append({
            "member_name": member_names.get(s["user_id"], "Membre"),
            "action_title": s.get("action_title", "Session"),
            "category": s.get("category", ""),
            "duration": s.get("actual_duration", 0),
            "completed_at": s.get("completed_at", ""),
        })

    return {"feed": feed, "group_name": group["name"]}


# ============== SHARE PROGRESSION (D.2) ==============

SHARE_TYPES = {"weekly_recap", "milestone", "badge", "objective"}
SHARE_TTL_DAYS = 90  # Auto-cleanup after 90 days

@api_router.post("/share/create")
@limiter.limit("10/minute")
async def create_share(request: Request, body: ShareCreate, user: dict = Depends(get_current_user)):
    """Create an immutable snapshot of user progression for sharing.
    Returns a share_id that can be used to view the public share page.
    Pattern: Spotify Wrapped / Strava Activity Cards — snapshot at creation time."""
    user_id = user["user_id"]

    if body.share_type not in SHARE_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid share_type. Must be one of: {', '.join(SHARE_TYPES)}")

    now = datetime.now(timezone.utc)
    today = now.date()
    today_iso = today.isoformat()
    week_start = (today - timedelta(days=today.weekday())).isoformat()

    # ── Snapshot: core stats ─────────────────────
    total_sessions = await db.user_sessions_history.count_documents(
        {"user_id": user_id, "completed": True}
    )

    week_sessions = await db.user_sessions_history.find(
        {"user_id": user_id, "completed": True, "completed_at": {"$gte": week_start}},
        {"_id": 0, "actual_duration": 1, "category": 1, "completed_at": 1}
    ).to_list(200)

    week_minutes = sum(s.get("actual_duration", 0) for s in week_sessions)
    week_count = len(week_sessions)

    week_by_day = {}
    for s in week_sessions:
        day = s.get("completed_at", "")[:10]
        if day:
            week_by_day[day] = week_by_day.get(day, 0) + s.get("actual_duration", 0)

    # ── Snapshot: objectives ─────────────────────
    obj_filter = {"user_id": user_id, "status": "active", "deleted": {"$ne": True}}
    if body.objective_id:
        obj_filter["objective_id"] = body.objective_id

    objectives = await db.objectives.find(
        obj_filter,
        {"_id": 0, "objective_id": 1, "title": 1, "current_day": 1, "streak_days": 1,
         "total_sessions": 1, "total_minutes": 1, "curriculum": 1, "category": 1}
    ).to_list(20)

    obj_snapshots = []
    for obj in objectives:
        curriculum = obj.get("curriculum", [])
        total_completed = sum(1 for s in curriculum if s.get("completed"))
        total_steps = len(curriculum)
        obj_snapshots.append({
            "objective_id": obj["objective_id"],
            "title": obj["title"],
            "category": obj.get("category", ""),
            "streak_days": obj.get("streak_days", 0),
            "progress_percent": round((total_completed / max(total_steps, 1)) * 100),
            "total_completed": total_completed,
            "total_steps": total_steps,
            "total_minutes": obj.get("total_minutes", 0),
        })

    # ── Snapshot: badges ─────────────────────────
    user_badges = user.get("badges", [])

    # ── Build share document ─────────────────────
    share_id = secrets.token_urlsafe(12)  # 16 chars, 96 bits entropy (Bitly-grade)

    share_doc = {
        "share_id": share_id,
        "user_id": user_id,
        "share_type": body.share_type,
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(days=SHARE_TTL_DAYS)).isoformat(),
        "author": {
            "name": user.get("name", "Utilisateur InFinea"),
            "subscription_tier": user.get("subscription_tier", "free"),
        },
        "snapshot": {
            "streak_days": user.get("streak_days", 0),
            "total_time_invested": user.get("total_time_invested", 0),
            "total_sessions": total_sessions,
            "week": {
                "sessions": week_count,
                "minutes": week_minutes,
                "by_day": week_by_day,
            },
            "objectives": obj_snapshots,
            "badges_count": len(user_badges),
            "recent_badges": user_badges[-3:] if user_badges else [],
        },
    }

    await db.shares.insert_one(share_doc)

    return {
        "share_id": share_id,
        "share_url": f"/p/{share_id}",
        "expires_at": share_doc["expires_at"],
    }


@app.get("/share/{share_id}")
@limiter.limit("30/minute")
async def get_public_share(share_id: str, request: Request):
    """Public endpoint — no auth required. Returns the share snapshot for display.
    Route is on app (not api_router) for clean public URLs."""
    share = await db.shares.find_one(
        {"share_id": share_id},
        {"_id": 0, "user_id": 0}  # Never expose internal user_id publicly
    )
    if not share:
        raise HTTPException(status_code=404, detail="Share not found or expired")

    # Check expiration
    expires_at = share.get("expires_at", "")
    if expires_at and expires_at < datetime.now(timezone.utc).isoformat():
        raise HTTPException(status_code=410, detail="This share has expired")

    return share


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
