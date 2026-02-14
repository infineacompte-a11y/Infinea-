"""
InFinea Local Server - Version autonome avec MongoDB en memoire (mongomock)
Pas besoin de MongoDB installe !
"""
from fastapi import FastAPI, APIRouter, HTTPException, Request, Depends, Response
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
import mongomock
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
import json
import re

ROOT_DIR = Path(__file__).parent

# MongoDB en memoire (mongomock)
client = mongomock.MongoClient()
db = client["infinea_local"]

# JWT Config
JWT_SECRET = 'infinea-local-secret-key-2024'
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 168  # 7 days

# Create the main app
app = FastAPI(title="InFinea API - Local")
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============== MODELS ==============

class UserCreate(BaseModel):
    email: str
    password: str
    name: str

class UserLogin(BaseModel):
    email: str
    password: str

class MicroAction(BaseModel):
    action_id: str = Field(default_factory=lambda: f"action_{uuid.uuid4().hex[:12]}")
    title: str
    description: str
    category: str
    duration_min: int
    duration_max: int
    energy_level: str
    instructions: List[str]
    is_premium: bool = False
    icon: str = "sparkles"

class SessionStart(BaseModel):
    action_id: str

class SessionComplete(BaseModel):
    session_id: str
    actual_duration: int
    completed: bool = True
    notes: Optional[str] = None

class AIRequest(BaseModel):
    available_time: int
    energy_level: str
    preferred_category: Optional[str] = None

class CheckoutRequest(BaseModel):
    origin_url: str

class NotificationPreferences(BaseModel):
    daily_reminder: bool = True
    reminder_time: str = "09:00"
    streak_alerts: bool = True
    achievement_alerts: bool = True
    weekly_summary: bool = True

class CompanyCreate(BaseModel):
    name: str
    domain: str

class InviteEmployee(BaseModel):
    email: str

# ============== HELPER FUNCTIONS ==============

def create_token(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("user_id")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def get_current_user_sync(request: Request) -> dict:
    """Synchronous version for mongomock (not async)"""
    # Check cookie first
    session_token = request.cookies.get("session_token")

    # Then check Authorization header
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header.split(" ")[1]

    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Check if it's a session
    session_doc = db.user_sessions.find_one(
        {"session_token": session_token},
        {"_id": 0}
    )

    if session_doc:
        expires_at = session_doc.get("expires_at")
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
        if expires_at and hasattr(expires_at, 'tzinfo') and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at and expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="Session expired")

        user = db.users.find_one(
            {"user_id": session_doc["user_id"]},
            {"_id": 0}
        )
        if user:
            return user

    # Try JWT token
    user_id = verify_token(session_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

# ============== AUTH ROUTES ==============

@api_router.post("/auth/register")
async def register(user_data: UserCreate, response: Response):
    existing = db.users.find_one({"email": user_data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = f"user_{uuid.uuid4().hex[:12]}"
    user_doc = {
        "user_id": user_id,
        "email": user_data.email,
        "name": user_data.name,
        "password_hash": hash_password(user_data.password),
        "picture": None,
        "subscription_tier": "free",
        "total_time_invested": 0,
        "streak_days": 0,
        "last_session_date": None,
        "badges": [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    db.users.insert_one(user_doc)

    token = create_token(user_id)
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        secure=False,  # False for localhost
        samesite="lax",
        path="/",
        max_age=JWT_EXPIRATION_HOURS * 3600
    )

    # Create welcome notification
    db.notifications.insert_one({
        "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
        "user_id": user_id,
        "type": "welcome",
        "title": "Bienvenue sur InFinea !",
        "message": "Commencez par explorer nos micro-actions et investissez vos instants perdus.",
        "icon": "sparkles",
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    })

    return {
        "user_id": user_id,
        "email": user_data.email,
        "name": user_data.name,
        "subscription_tier": "free",
        "token": token
    }

@api_router.post("/auth/login")
async def login(user_data: UserLogin, response: Response):
    user = db.users.find_one({"email": user_data.email}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if "password_hash" not in user:
        raise HTTPException(status_code=401, detail="Please login with Google")

    if not verify_password(user_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token(user["user_id"])
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
        max_age=JWT_EXPIRATION_HOURS * 3600
    )

    return {
        "user_id": user["user_id"],
        "email": user["email"],
        "name": user["name"],
        "picture": user.get("picture"),
        "subscription_tier": user.get("subscription_tier", "free"),
        "token": token
    }

@api_router.post("/auth/session")
async def process_oauth_session(request: Request, response: Response):
    """Process Google OAuth - simplified for local dev"""
    body = await request.json()
    session_id = body.get("session_id")

    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")

    # For local dev, try the real endpoint first, fallback to mock
    try:
        import httpx
        async with httpx.AsyncClient() as client_http:
            resp = await client_http.get(
                "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                headers={"X-Session-ID": session_id},
                timeout=5.0
            )
            if resp.status_code == 200:
                data = resp.json()
            else:
                raise Exception("OAuth failed")
    except Exception:
        # Fallback: create a demo user for local testing
        data = {
            "email": "demo@infinea.local",
            "name": "Utilisateur Demo",
            "picture": None,
            "session_token": f"session_{uuid.uuid4().hex}"
        }

    existing_user = db.users.find_one({"email": data["email"]}, {"_id": 0})

    if existing_user:
        user_id = existing_user["user_id"]
        db.users.update_one(
            {"user_id": user_id},
            {"$set": {"name": data["name"], "picture": data.get("picture")}}
        )
    else:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        user_doc = {
            "user_id": user_id,
            "email": data["email"],
            "name": data["name"],
            "picture": data.get("picture"),
            "subscription_tier": "free",
            "total_time_invested": 0,
            "streak_days": 0,
            "last_session_date": None,
            "badges": [],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        db.users.insert_one(user_doc)

    session_token = data.get("session_token", f"session_{uuid.uuid4().hex}")
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    })

    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
        max_age=7 * 24 * 3600
    )

    user = db.users.find_one({"user_id": user_id}, {"_id": 0})
    jwt_token = create_token(user_id)

    return {
        "user_id": user_id,
        "email": user["email"],
        "name": user["name"],
        "picture": user.get("picture"),
        "subscription_tier": user.get("subscription_tier", "free"),
        "token": jwt_token
    }

@api_router.get("/auth/me")
async def get_me(request: Request):
    user = get_current_user_sync(request)
    return {
        "user_id": user["user_id"],
        "email": user["email"],
        "name": user["name"],
        "picture": user.get("picture"),
        "subscription_tier": user.get("subscription_tier", "free"),
        "total_time_invested": user.get("total_time_invested", 0),
        "streak_days": user.get("streak_days", 0)
    }

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    session_token = request.cookies.get("session_token")
    if session_token:
        db.user_sessions.delete_one({"session_token": session_token})

    response.delete_cookie(key="session_token", path="/", samesite="lax")
    return {"message": "Logged out successfully"}

# ============== MICRO-ACTIONS ROUTES ==============

@api_router.get("/actions")
async def get_actions(
    category: Optional[str] = None,
    duration: Optional[int] = None,
    energy: Optional[str] = None
):
    query = {}
    if category:
        query["category"] = category
    if energy:
        query["energy_level"] = energy

    actions = list(db.micro_actions.find(query, {"_id": 0}))

    if duration:
        actions = [a for a in actions if a["duration_min"] <= duration <= a["duration_max"]]

    return actions

@api_router.get("/actions/{action_id}")
async def get_action(action_id: str):
    action = db.micro_actions.find_one({"action_id": action_id}, {"_id": 0})
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    return action

# ============== AI SUGGESTIONS ROUTE ==============

@api_router.post("/suggestions")
async def get_ai_suggestions(ai_request: AIRequest, request: Request):
    """Get AI-powered micro-action suggestions - local fallback version"""
    user = get_current_user_sync(request)

    query = {"duration_min": {"$lte": ai_request.available_time}}
    if ai_request.preferred_category:
        query["category"] = ai_request.preferred_category
    if ai_request.energy_level:
        query["energy_level"] = ai_request.energy_level

    if user.get("subscription_tier") == "free":
        query["is_premium"] = False

    available_actions = list(db.micro_actions.find(query, {"_id": 0}))

    if not available_actions:
        # Broaden search
        query2 = {}
        if ai_request.preferred_category:
            query2["category"] = ai_request.preferred_category
        if user.get("subscription_tier") == "free":
            query2["is_premium"] = False
        available_actions = list(db.micro_actions.find(query2, {"_id": 0}))

    if not available_actions:
        available_actions = list(db.micro_actions.find({"is_premium": False}, {"_id": 0}))

    if not available_actions:
        return {
            "suggestion": "Prenez une pause de respiration profonde",
            "reasoning": "Aucune micro-action ne correspond exactement. Profitez de ce moment pour vous recentrer.",
            "recommended_actions": []
        }

    # Smart rule-based suggestions (no AI needed)
    energy_map = {"low": 1, "medium": 2, "high": 3}
    user_energy = energy_map.get(ai_request.energy_level, 2)

    def score_action(action):
        s = 0
        # Time fit
        if action["duration_min"] <= ai_request.available_time <= action["duration_max"]:
            s += 10
        elif action["duration_min"] <= ai_request.available_time:
            s += 5
        # Energy match
        action_energy = energy_map.get(action["energy_level"], 2)
        if action_energy == user_energy:
            s += 8
        elif abs(action_energy - user_energy) == 1:
            s += 4
        # Category preference
        if ai_request.preferred_category and action["category"] == ai_request.preferred_category:
            s += 6
        return s

    scored = sorted(available_actions, key=score_action, reverse=True)
    top = scored[:3]

    reasoning_map = {
        "low": "Parfait pour un moment de calme. Cette action demande peu d'effort.",
        "medium": "Un bon equilibre entre effort et detente pour ce moment.",
        "high": "Vous avez l'energie, profitons-en pour une action dynamique !"
    }

    return {
        "suggestion": top[0]["title"] if top else "Respiration profonde",
        "reasoning": reasoning_map.get(ai_request.energy_level, "Basee sur vos preferences et le temps disponible."),
        "recommended_actions": top
    }

# ============== SESSION TRACKING ROUTES ==============

@api_router.post("/sessions/start")
async def start_session(session_data: SessionStart, request: Request):
    user = get_current_user_sync(request)
    action = db.micro_actions.find_one({"action_id": session_data.action_id}, {"_id": 0})
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    if action.get("is_premium") and user.get("subscription_tier") == "free":
        raise HTTPException(status_code=403, detail="Premium action - upgrade required")

    session_id = f"session_{uuid.uuid4().hex[:12]}"
    session_doc = {
        "session_id": session_id,
        "user_id": user["user_id"],
        "action_id": session_data.action_id,
        "action_title": action["title"],
        "category": action["category"],
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
        "actual_duration": None,
        "completed": False
    }

    db.user_sessions_history.insert_one(session_doc)

    return {
        "session_id": session_id,
        "action": action,
        "started_at": session_doc["started_at"]
    }

@api_router.post("/sessions/complete")
async def complete_session(completion: SessionComplete, request: Request):
    user = get_current_user_sync(request)
    session = db.user_sessions_history.find_one(
        {"session_id": completion.session_id, "user_id": user["user_id"]},
        {"_id": 0}
    )

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    db.user_sessions_history.update_one(
        {"session_id": completion.session_id},
        {"$set": {
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "actual_duration": completion.actual_duration,
            "completed": completion.completed,
            "notes": completion.notes
        }}
    )

    if completion.completed:
        user_doc = db.users.find_one({"user_id": user["user_id"]}, {"_id": 0})

        today = datetime.now(timezone.utc).date()
        last_session = user_doc.get("last_session_date")

        new_streak = user_doc.get("streak_days", 0)
        if last_session:
            if isinstance(last_session, str):
                last_date = datetime.fromisoformat(last_session.replace('Z', '+00:00')).date()
            else:
                last_date = last_session.date() if hasattr(last_session, 'date') else last_session

            if last_date == today - timedelta(days=1):
                new_streak += 1
            elif last_date != today:
                new_streak = 1
        else:
            new_streak = 1

        new_total_time = user_doc.get("total_time_invested", 0) + completion.actual_duration

        db.users.update_one(
            {"user_id": user["user_id"]},
            {"$set": {
                "total_time_invested": new_total_time,
                "streak_days": new_streak,
                "last_session_date": today.isoformat()
            }}
        )

        # Check for new badges
        new_badges = check_and_award_badges(user["user_id"])

        # Create notifications for new badges
        for badge in new_badges:
            db.notifications.insert_one({
                "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
                "user_id": user["user_id"],
                "type": "badge_earned",
                "title": f"Nouveau badge : {badge['name']}",
                "message": f"Felicitations ! Vous avez obtenu le badge {badge['name']}",
                "icon": badge["icon"],
                "read": False,
                "created_at": datetime.now(timezone.utc).isoformat()
            })

        return {
            "message": "Session completed!",
            "time_added": completion.actual_duration,
            "new_streak": new_streak,
            "total_time": new_total_time,
            "new_badges": new_badges
        }

    return {"message": "Session recorded"}

@api_router.get("/stats")
async def get_user_stats(request: Request):
    user = get_current_user_sync(request)

    completed_sessions = list(db.user_sessions_history.find(
        {"user_id": user["user_id"], "completed": True},
        {"_id": 0}
    ))

    sessions_by_category = {}
    time_by_category = {}
    for s in completed_sessions:
        cat = s.get("category", "other")
        sessions_by_category[cat] = sessions_by_category.get(cat, 0) + 1
        time_by_category[cat] = time_by_category.get(cat, 0) + (s.get("actual_duration") or 0)

    recent = sorted(completed_sessions, key=lambda x: x.get("completed_at", ""), reverse=True)[:10]

    return {
        "total_time_invested": user.get("total_time_invested", 0),
        "total_sessions": len(completed_sessions),
        "streak_days": user.get("streak_days", 0),
        "sessions_by_category": sessions_by_category,
        "time_by_category": time_by_category,
        "recent_sessions": recent
    }

# ============== BADGES & ACHIEVEMENTS ==============

BADGES = [
    {"badge_id": "first_action", "name": "Premier Pas", "description": "Completez votre premiere micro-action", "icon": "rocket", "condition": {"type": "sessions_completed", "value": 1}},
    {"badge_id": "streak_3", "name": "Regularite", "description": "Maintenez un streak de 3 jours", "icon": "flame", "condition": {"type": "streak_days", "value": 3}},
    {"badge_id": "streak_7", "name": "Semaine Parfaite", "description": "Maintenez un streak de 7 jours", "icon": "star", "condition": {"type": "streak_days", "value": 7}},
    {"badge_id": "streak_30", "name": "Mois d'Or", "description": "Maintenez un streak de 30 jours", "icon": "crown", "condition": {"type": "streak_days", "value": 30}},
    {"badge_id": "time_60", "name": "Premiere Heure", "description": "Accumulez 60 minutes de micro-actions", "icon": "clock", "condition": {"type": "total_time", "value": 60}},
    {"badge_id": "time_300", "name": "5 Heures", "description": "Accumulez 5 heures de micro-actions", "icon": "timer", "condition": {"type": "total_time", "value": 300}},
    {"badge_id": "time_600", "name": "10 Heures", "description": "Accumulez 10 heures de micro-actions", "icon": "trophy", "condition": {"type": "total_time", "value": 600}},
    {"badge_id": "category_learning", "name": "Apprenant", "description": "Completez 10 actions d'apprentissage", "icon": "book-open", "condition": {"type": "category_sessions", "category": "learning", "value": 10}},
    {"badge_id": "category_productivity", "name": "Productif", "description": "Completez 10 actions de productivite", "icon": "target", "condition": {"type": "category_sessions", "category": "productivity", "value": 10}},
    {"badge_id": "category_wellbeing", "name": "Zen Master", "description": "Completez 10 actions de bien-etre", "icon": "heart", "condition": {"type": "category_sessions", "category": "well_being", "value": 10}},
    {"badge_id": "all_categories", "name": "Equilibre", "description": "Completez au moins 5 actions dans chaque categorie", "icon": "sparkles", "condition": {"type": "all_categories", "value": 5}},
    {"badge_id": "premium", "name": "Investisseur", "description": "Passez a Premium", "icon": "gem", "condition": {"type": "subscription", "value": "premium"}},
]

def check_and_award_badges(user_id: str) -> list:
    user = db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not user:
        return []

    user_badges = user.get("badges", [])
    user_badge_ids = [b["badge_id"] for b in user_badges]

    completed_sessions = list(db.user_sessions_history.find(
        {"user_id": user_id, "completed": True}, {"_id": 0}
    ))
    total_sessions = len(completed_sessions)

    category_counts = {}
    for s in completed_sessions:
        cat = s.get("category", "")
        category_counts[cat] = category_counts.get(cat, 0) + 1

    new_badges = []

    for badge in BADGES:
        if badge["badge_id"] in user_badge_ids:
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

        if earned:
            badge_award = {
                "badge_id": badge["badge_id"],
                "name": badge["name"],
                "icon": badge["icon"],
                "earned_at": datetime.now(timezone.utc).isoformat()
            }
            new_badges.append(badge_award)

    if new_badges:
        current_badges = user.get("badges", [])
        current_badges.extend(new_badges)
        db.users.update_one(
            {"user_id": user_id},
            {"$set": {"badges": current_badges}}
        )

    return new_badges

@api_router.get("/badges")
async def get_all_badges():
    return BADGES

@api_router.get("/badges/user")
async def get_user_badges(request: Request):
    user = get_current_user_sync(request)
    user_badges = user.get("badges", [])
    new_badges = check_and_award_badges(user["user_id"])
    all_earned = user_badges + new_badges

    return {
        "earned": all_earned,
        "new_badges": new_badges,
        "total_available": len(BADGES),
        "total_earned": len(all_earned)
    }

# ============== NOTIFICATIONS ==============

@api_router.get("/notifications/preferences")
async def get_notification_preferences(request: Request):
    user = get_current_user_sync(request)
    prefs = db.notification_preferences.find_one(
        {"user_id": user["user_id"]}, {"_id": 0}
    )

    if not prefs:
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
async def update_notification_preferences(prefs: NotificationPreferences, request: Request):
    user = get_current_user_sync(request)
    prefs_doc = {
        "user_id": user["user_id"],
        "daily_reminder": prefs.daily_reminder,
        "reminder_time": prefs.reminder_time,
        "streak_alerts": prefs.streak_alerts,
        "achievement_alerts": prefs.achievement_alerts,
        "weekly_summary": prefs.weekly_summary,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

    db.notification_preferences.update_one(
        {"user_id": user["user_id"]},
        {"$set": prefs_doc},
        upsert=True
    )

    return prefs_doc

@api_router.post("/notifications/subscribe")
async def subscribe_push_notifications(request: Request):
    user = get_current_user_sync(request)
    body = await request.json()
    subscription = body.get("subscription")

    if not subscription:
        raise HTTPException(status_code=400, detail="Subscription data required")

    db.push_subscriptions.update_one(
        {"user_id": user["user_id"]},
        {"$set": {
            "user_id": user["user_id"],
            "subscription": subscription,
            "created_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )

    return {"message": "Subscribed to push notifications"}

@api_router.get("/notifications")
async def get_user_notifications(request: Request, limit: int = 20):
    user = get_current_user_sync(request)
    notifications = list(db.notifications.find(
        {"user_id": user["user_id"]}, {"_id": 0}
    ))
    # Sort by created_at descending
    notifications.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return notifications[:limit]

@api_router.post("/notifications/mark-read")
async def mark_notifications_read(request: Request):
    user = get_current_user_sync(request)
    body = await request.json()
    notification_ids = body.get("notification_ids", [])

    if notification_ids:
        for nid in notification_ids:
            db.notifications.update_one(
                {"user_id": user["user_id"], "notification_id": nid},
                {"$set": {"read": True}}
            )
    else:
        db.notifications.update_many(
            {"user_id": user["user_id"]},
            {"$set": {"read": True}}
        )

    return {"message": "Notifications marked as read"}

# ============== PAYMENTS (mock for local) ==============

@api_router.post("/payments/checkout")
async def create_checkout(checkout_data: CheckoutRequest, request: Request):
    user = get_current_user_sync(request)
    # Mock Stripe - auto-upgrade to premium
    session_id = f"cs_mock_{uuid.uuid4().hex[:12]}"

    db.payment_transactions.insert_one({
        "transaction_id": f"txn_{uuid.uuid4().hex[:12]}",
        "session_id": session_id,
        "user_id": user["user_id"],
        "amount": 6.99,
        "currency": "eur",
        "plan": "premium",
        "payment_status": "paid",
        "processed": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    })

    # Auto-upgrade user for local testing
    db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {
            "subscription_tier": "premium",
            "subscription_started_at": datetime.now(timezone.utc).isoformat()
        }}
    )

    return {"url": f"{checkout_data.origin_url}/pricing?session_id={session_id}", "session_id": session_id}

@api_router.get("/payments/status/{session_id}")
async def get_payment_status(session_id: str, request: Request):
    user = get_current_user_sync(request)
    return {
        "status": "complete",
        "payment_status": "paid",
        "amount": 6.99,
        "currency": "eur"
    }

# ============== B2B DASHBOARD ==============

@api_router.post("/b2b/company")
async def create_company(company_data: CompanyCreate, request: Request):
    user = get_current_user_sync(request)
    existing = db.companies.find_one({"admin_user_id": user["user_id"]}, {"_id": 0})

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

    db.companies.insert_one(company_doc)

    db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {"company_id": company_id, "is_company_admin": True}}
    )

    return {"company_id": company_id, "name": company_data.name}

@api_router.get("/b2b/company")
async def get_company(request: Request):
    user = get_current_user_sync(request)
    company_id = user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=404, detail="No company found")

    company = db.companies.find_one({"company_id": company_id}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    return company

@api_router.get("/b2b/dashboard")
async def get_b2b_dashboard(request: Request):
    user = get_current_user_sync(request)
    company_id = user.get("company_id")

    if not company_id or not user.get("is_company_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    company = db.companies.find_one({"company_id": company_id}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    employee_ids = company.get("employees", [])

    completed_sessions = list(db.user_sessions_history.find(
        {"user_id": {"$in": employee_ids}, "completed": True}, {"_id": 0}
    ))

    total_sessions = len(completed_sessions)
    total_time = sum(s.get("actual_duration", 0) for s in completed_sessions)

    category_distribution = {}
    for s in completed_sessions:
        cat = s.get("category", "other")
        if cat not in category_distribution:
            category_distribution[cat] = {"sessions": 0, "time": 0}
        category_distribution[cat]["sessions"] += 1
        category_distribution[cat]["time"] += s.get("actual_duration", 0)

    return {
        "company_name": company["name"],
        "employee_count": len(employee_ids),
        "active_employees_this_week": len(employee_ids),
        "engagement_rate": 100.0 if employee_ids else 0,
        "total_sessions": total_sessions,
        "total_time_minutes": total_time,
        "avg_time_per_employee": round(total_time / len(employee_ids), 1) if employee_ids else 0,
        "avg_sessions_per_employee": round(total_sessions / len(employee_ids), 1) if employee_ids else 0,
        "category_distribution": category_distribution,
        "daily_activity": [],
        "qvt_score": min(100, round(100 + (total_time / max(len(employee_ids), 1) / 10), 1))
    }

@api_router.post("/b2b/invite")
async def invite_employee(invite: InviteEmployee, request: Request):
    user = get_current_user_sync(request)
    company_id = user.get("company_id")

    if not company_id or not user.get("is_company_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    company = db.companies.find_one({"company_id": company_id}, {"_id": 0})

    invite_id = f"invite_{uuid.uuid4().hex[:12]}"
    db.company_invites.insert_one({
        "invite_id": invite_id,
        "company_id": company_id,
        "email": invite.email,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    })

    return {"invite_id": invite_id, "email": invite.email, "status": "pending"}

@api_router.get("/b2b/employees")
async def get_employees(request: Request):
    user = get_current_user_sync(request)
    company_id = user.get("company_id")

    if not company_id or not user.get("is_company_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    company = db.companies.find_one({"company_id": company_id}, {"_id": 0})
    employee_ids = company.get("employees", [])

    employees = []
    for i, emp_id in enumerate(employee_ids):
        emp = db.users.find_one({"user_id": emp_id}, {"_id": 0})
        if emp:
            sessions = db.user_sessions_history.count_documents(
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

# ============== SEED DATA ==============

@api_router.post("/admin/seed")
async def seed_micro_actions():
    actions = [
        {"action_id": "action_learn_vocab", "title": "5 nouveaux mots", "description": "Apprenez 5 nouveaux mots de vocabulaire dans la langue de votre choix.", "category": "learning", "duration_min": 2, "duration_max": 5, "energy_level": "low", "instructions": ["Ouvrez votre application de vocabulaire preferee", "Revisez 5 mots avec leurs definitions", "Prononcez chaque mot a voix haute", "Utilisez chaque mot dans une phrase"], "is_premium": False, "icon": "book-open"},
        {"action_id": "action_learn_article", "title": "Lecture rapide", "description": "Lisez un article court sur un sujet qui vous passionne.", "category": "learning", "duration_min": 5, "duration_max": 10, "energy_level": "low", "instructions": ["Choisissez un article de votre fil d'actualites", "Lisez-le en survol d'abord", "Relisez les passages cles", "Notez une idee a retenir"], "is_premium": False, "icon": "newspaper"},
        {"action_id": "action_learn_concept", "title": "Nouveau concept", "description": "Apprenez un nouveau concept et testez votre comprehension.", "category": "learning", "duration_min": 10, "duration_max": 15, "energy_level": "medium", "instructions": ["Choisissez un sujet qui vous interesse", "Regardez une video explicative courte", "Resumez le concept en 3 points", "Expliquez-le comme si vous l'enseigniez"], "is_premium": False, "icon": "lightbulb"},
        {"action_id": "action_learn_flashcards", "title": "Session Flashcards", "description": "Revisez 20 flashcards pour ancrer vos connaissances.", "category": "learning", "duration_min": 5, "duration_max": 10, "energy_level": "medium", "instructions": ["Ouvrez votre deck de flashcards", "Repondez a 20 cartes", "Marquez celles a revoir", "Celebrez votre score!"], "is_premium": True, "icon": "layers"},
        {"action_id": "action_prod_inbox", "title": "Inbox Zero", "description": "Traitez rapidement 5 emails de votre boite de reception.", "category": "productivity", "duration_min": 3, "duration_max": 7, "energy_level": "low", "instructions": ["Ouvrez votre messagerie", "Archivez ou supprimez les emails non essentiels", "Repondez aux messages rapides", "Marquez les autres pour plus tard"], "is_premium": False, "icon": "mail"},
        {"action_id": "action_prod_plan", "title": "Mini-planification", "description": "Planifiez les 3 taches prioritaires de votre prochaine session de travail.", "category": "productivity", "duration_min": 2, "duration_max": 5, "energy_level": "low", "instructions": ["Identifiez 3 taches importantes", "Estimez le temps necessaire", "Ordonnez par priorite", "Bloquez du temps dans votre agenda"], "is_premium": False, "icon": "list-todo"},
        {"action_id": "action_prod_brainstorm", "title": "Brainstorm eclair", "description": "Generez 10 idees sur un projet ou probleme en cours.", "category": "productivity", "duration_min": 5, "duration_max": 10, "energy_level": "medium", "instructions": ["Definissez votre question/probleme", "Ecrivez toutes les idees sans filtre", "Visez la quantite, pas la qualite", "Identifiez les 2-3 meilleures idees"], "is_premium": False, "icon": "zap"},
        {"action_id": "action_prod_review", "title": "Revue de projet", "description": "Faites le point sur l'avancement d'un projet en cours.", "category": "productivity", "duration_min": 5, "duration_max": 10, "energy_level": "medium", "instructions": ["Choisissez un projet actif", "Listez ce qui a ete accompli", "Identifiez les blocages", "Definissez la prochaine action"], "is_premium": True, "icon": "clipboard-check"},
        {"action_id": "action_well_breath", "title": "Respiration 4-7-8", "description": "Technique de respiration pour reduire le stress instantanement.", "category": "well_being", "duration_min": 2, "duration_max": 5, "energy_level": "low", "instructions": ["Asseyez-vous confortablement", "Inspirez par le nez pendant 4 secondes", "Retenez votre souffle 7 secondes", "Expirez par la bouche pendant 8 secondes", "Repetez 4 cycles"], "is_premium": False, "icon": "wind"},
        {"action_id": "action_well_gratitude", "title": "Moment gratitude", "description": "Notez 3 choses pour lesquelles vous etes reconnaissant aujourd'hui.", "category": "well_being", "duration_min": 2, "duration_max": 5, "energy_level": "low", "instructions": ["Fermez les yeux un instant", "Pensez a 3 moments positifs recents", "Notez-les dans votre journal", "Ressentez la gratitude"], "is_premium": False, "icon": "heart"},
        {"action_id": "action_well_stretch", "title": "Pause etirements", "description": "Seance d'etirements pour delier les tensions du corps.", "category": "well_being", "duration_min": 5, "duration_max": 10, "energy_level": "medium", "instructions": ["Levez-vous et etirez les bras vers le haut", "Penchez-vous vers l'avant, bras pendants", "Faites des rotations de nuque", "Etirez chaque epaule 30 secondes", "Terminez par des rotations de hanches"], "is_premium": False, "icon": "move"},
        {"action_id": "action_well_meditate", "title": "Mini meditation", "description": "Une courte meditation guidee pour recentrer votre esprit.", "category": "well_being", "duration_min": 5, "duration_max": 10, "energy_level": "medium", "instructions": ["Trouvez un endroit calme", "Fermez les yeux", "Concentrez-vous sur votre respiration", "Observez vos pensees sans jugement", "Revenez doucement au present"], "is_premium": True, "icon": "brain"},
        {"action_id": "action_prod_deep", "title": "Deep Work Sprint", "description": "15 minutes de concentration intense sur une tache importante.", "category": "productivity", "duration_min": 10, "duration_max": 15, "energy_level": "high", "instructions": ["Choisissez UNE tache prioritaire", "Eliminez toutes les distractions", "Mettez un timer de 15 minutes", "Travaillez sans interruption", "Notez ou vous en etes pour continuer plus tard"], "is_premium": True, "icon": "target"},
        {"action_id": "action_well_energy", "title": "Boost d'energie", "description": "Exercices rapides pour booster votre energie et votre focus.", "category": "well_being", "duration_min": 5, "duration_max": 10, "energy_level": "high", "instructions": ["20 jumping jacks", "10 squats", "30 secondes de planche", "10 pompes (ou version facilitee)", "Recuperez 30 secondes"], "is_premium": False, "icon": "flame"},
        {"action_id": "action_learn_podcast", "title": "Podcast eclair", "description": "Ecoutez un segment de podcast educatif.", "category": "learning", "duration_min": 10, "duration_max": 15, "energy_level": "high", "instructions": ["Choisissez un podcast de votre liste", "Ecoutez en vitesse 1.25x ou 1.5x", "Notez une idee cle", "Partagez-la ou appliquez-la"], "is_premium": True, "icon": "headphones"},
    ]

    db.micro_actions.delete_many({})
    for action in actions:
        db.micro_actions.insert_one(action)

    return {"message": f"Seeded {len(actions)} micro-actions"}

# ============== ROOT ROUTE ==============

@api_router.get("/")
async def root():
    return {"message": "InFinea API Local - Investissez vos instants perdus"}

# Include router and add middleware
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============== AUTO-SEED ON STARTUP ==============

@app.on_event("startup")
async def startup_event():
    """Auto-seed the database on startup"""
    logger.info("Seeding database with demo micro-actions...")
    await seed_micro_actions()
    logger.info("Database seeded successfully!")
    logger.info("Server ready at http://localhost:8000")
    logger.info("API docs at http://localhost:8000/docs")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
