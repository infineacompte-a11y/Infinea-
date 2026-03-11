from fastapi import FastAPI, APIRouter, HTTPException, Request, Depends, Response
from fastapi.responses import JSONResponse, RedirectResponse
import urllib.parse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
import httpx
import json
import asyncio
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

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL') or os.environ.get('MONGODB_URI', '')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'infinea')]

# JWT Config
JWT_SECRET = os.environ.get('JWT_SECRET')
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET environment variable is required. Server cannot start without it.")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 168  # 7 days

# Create the main app
app = FastAPI(title="InFinea API")
api_router = APIRouter(prefix="/api")

# Rate limiting
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============== MODELS ==============

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=1)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    subscription_tier: str = "free"
    total_time_invested: int = 0  # in minutes
    streak_days: int = 0
    created_at: datetime

class MicroAction(BaseModel):
    action_id: str = Field(default_factory=lambda: f"action_{uuid.uuid4().hex[:12]}")
    title: str
    description: str
    category: str  # learning, productivity, well_being
    duration_min: int  # 2-15 minutes
    duration_max: int
    energy_level: str  # low, medium, high
    instructions: List[str]
    is_premium: bool = False
    icon: str = "sparkles"

class MicroActionCreate(BaseModel):
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
    actual_duration: int  # in minutes
    completed: bool = True
    notes: Optional[str] = None

class AIRequest(BaseModel):
    available_time: int  # in minutes
    energy_level: str  # low, medium, high
    preferred_category: Optional[str] = None

class CheckoutRequest(BaseModel):
    origin_url: str

class ProgressStats(BaseModel):
    total_time_invested: int
    total_sessions: int
    streak_days: int
    sessions_by_category: Dict[str, int]
    recent_sessions: List[Dict[str, Any]]

class OnboardingProfile(BaseModel):
    goals: List[str] = []  # ["learning", "productivity", "well_being"]
    preferred_times: List[str] = []  # ["morning", "lunch", "evening"]
    energy_level: str = "medium"  # "low", "medium", "high"
    interests: List[str] = []  # ["learning", "productivity", "wellness"]
    # Legacy fields (optional for backward compat)
    availability_slots: Optional[List[str]] = None
    daily_minutes: Optional[int] = None
    energy_high: Optional[str] = None
    energy_low: Optional[str] = None

class CustomActionRequest(BaseModel):
    description: str
    preferred_category: Optional[str] = None
    preferred_duration: Optional[int] = None

class DebriefRequest(BaseModel):
    session_id: str
    action_title: Optional[str] = None
    action_category: Optional[str] = None
    actual_duration: Optional[int] = None
    duration_minutes: Optional[int] = None  # Frontend sends this
    notes: Optional[str] = None

class CoachChatRequest(BaseModel):
    message: str

class ObjectiveCreate(BaseModel):
    title: str  # "Apprendre le thaï", "Jouer du piano"
    description: Optional[str] = None
    target_duration_days: Optional[int] = 30  # 30, 60, 90 days
    daily_minutes: Optional[int] = 10  # target per day
    category: Optional[str] = None  # learning, productivity, etc.

class ObjectiveUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    target_duration_days: Optional[int] = None
    daily_minutes: Optional[int] = None
    status: Optional[str] = None  # active, paused, completed, abandoned

class ICalConnectRequest(BaseModel):
    url: str
    name: Optional[str] = "Mon calendrier iCal"

class TokenConnectRequest(BaseModel):
    token: str
    name: Optional[str] = None

class PromoCodeRequest(BaseModel):
    code: str

# ============== AI HELPER FUNCTIONS ==============

AI_SYSTEM_MESSAGE = """Tu es le coach IA InFinea, expert en productivité, apprentissage et bien-être.
Tu aides les utilisateurs à transformer leurs moments perdus en micro-victoires.
Réponds toujours en français, de manière concise, chaleureuse et motivante.
Tes réponses doivent toujours être au format JSON quand demandé."""

def get_ai_model(user: dict = None) -> str:
    """Return AI model based on user subscription tier."""
    if user and user.get("subscription_tier") == "premium":
        return "claude-sonnet-4-20250514"
    return "claude-haiku-4-5-20251001"

async def check_usage_limit(user_id: str, feature: str, limit: int, period: str = "daily") -> dict:
    """Check and increment usage counter for free-tier AI limits.
    Returns {"allowed": bool, "used": int, "limit": int, "remaining": int}
    """
    today = datetime.now(timezone.utc).date().isoformat()
    week = datetime.now(timezone.utc).strftime("%Y-W%W")

    if period == "daily":
        doc = await db.usage_limits.find_one({"user_id": user_id, "date": today})
        used = (doc or {}).get(feature, 0)
        if used >= limit:
            return {"allowed": False, "used": used, "limit": limit, "remaining": 0}
        await db.usage_limits.update_one(
            {"user_id": user_id, "date": today},
            {"$inc": {feature: 1}, "$setOnInsert": {"created_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True
        )
        return {"allowed": True, "used": used + 1, "limit": limit, "remaining": limit - used - 1}

    elif period == "weekly":
        doc = await db.usage_limits.find_one({"user_id": user_id, "date": today})
        last_week = (doc or {}).get(f"{feature}_week", "")
        if last_week == week:
            return {"allowed": False, "used": 1, "limit": limit, "remaining": 0}
        await db.usage_limits.update_one(
            {"user_id": user_id, "date": today},
            {"$set": {f"{feature}_week": week}, "$setOnInsert": {"created_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True
        )
        return {"allowed": True, "used": 1, "limit": limit, "remaining": 0}

    elif period == "total":
        count = await db.usage_limits.find_one({"user_id": user_id, "type": "lifetime"})
        used = (count or {}).get(feature, 0)
        if used >= limit:
            return {"allowed": False, "used": used, "limit": limit, "remaining": 0}
        await db.usage_limits.update_one(
            {"user_id": user_id, "type": "lifetime"},
            {"$inc": {feature: 1}, "$setOnInsert": {"created_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True
        )
        return {"allowed": True, "used": used + 1, "limit": limit, "remaining": limit - used - 1}

    return {"allowed": True, "used": 0, "limit": limit, "remaining": limit}

async def call_ai(session_suffix: str, system_message: str, prompt: str, model: str = None) -> Optional[str]:
    """Shared AI call wrapper using Anthropic Claude API via httpx."""
    api_key = os.environ.get('ANTHROPIC_API_KEY') or os.environ.get('OPENAI_API_KEY')
    if not api_key:
        return None
    ai_model = model or "claude-haiku-4-5-20251001"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client_http:
            resp = await client_http.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": ai_model,
                    "max_tokens": 1000,
                    "system": system_message,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ]
                }
            )
            resp.raise_for_status()
            data = resp.json()
            return data["content"][0]["text"]
    except Exception as e:
        logger.error(f"AI call error ({session_suffix}): {e}")
        return None

def parse_ai_json(response: Optional[str]) -> Optional[dict]:
    """Extract JSON from AI response."""
    if not response:
        return None
    try:
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            return json.loads(response[json_start:json_end])
    except Exception:
        pass
    return None

async def build_user_context(user: dict) -> str:
    """Build a context string from user profile for AI prompts."""
    profile = user.get("user_profile")
    if not profile:
        return f"Utilisateur: {user.get('name', 'Inconnu')}, streak: {user.get('streak_days', 0)} jours, temps total: {user.get('total_time_invested', 0)} min"

    goals_map = {"learning": "apprentissage", "productivity": "productivité", "well_being": "bien-être"}
    goals = ", ".join([goals_map.get(g, g) for g in profile.get("goals", [])])

    # Handle both new format (preferred_times, energy_level, interests as list)
    # and legacy format (availability_slots, energy_high/low, interests as dict)
    interests = profile.get('interests', [])
    if isinstance(interests, dict):
        interests_str = json.dumps(interests, ensure_ascii=False)
    elif isinstance(interests, list):
        interests_str = ", ".join(interests) if interests else "non définis"
    else:
        interests_str = str(interests)

    times = profile.get('preferred_times', profile.get('availability_slots', []))
    energy = profile.get('energy_level', profile.get('energy_high', 'medium'))

    return f"""Profil utilisateur:
- Nom: {user.get('name', 'Inconnu')}
- Objectifs: {goals}
- Créneaux préférés: {', '.join(times) if times else 'non définis'}
- Niveau d'énergie: {energy}
- Intérêts: {interests_str}
- Streak actuel: {user.get('streak_days', 0)} jours
- Temps total investi: {user.get('total_time_invested', 0)} minutes
- Abonnement: {user.get('subscription_tier', 'free')}"""

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

async def get_current_user(request: Request) -> dict:
    # Check cookie first
    session_token = request.cookies.get("session_token")
    
    # Then check Authorization header
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header.split(" ")[1]
    
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Check if it's a Google OAuth session
    session_doc = await db.user_sessions.find_one(
        {"session_token": session_token},
        {"_id": 0}
    )
    
    if session_doc:
        # Check expiry
        expires_at = session_doc.get("expires_at")
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="Session expired")
        
        user = await db.users.find_one(
            {"user_id": session_doc["user_id"]},
            {"_id": 0}
        )
        if user:
            return user
    
    # Try JWT token
    user_id = verify_token(session_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

# ============== AUTH ROUTES ==============

@api_router.post("/auth/register")
@limiter.limit("3/minute")
async def register(request: Request, user_data: UserCreate, response: Response):
    # Check if user exists
    existing = await db.users.find_one({"email": user_data.email}, {"_id": 0})
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
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user_doc)
    
    token = create_token(user_id)
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=JWT_EXPIRATION_HOURS * 3600
    )
    
    return {
        "user_id": user_id,
        "email": user_data.email,
        "name": user_data.name,
        "subscription_tier": "free",
        "token": token
    }

@api_router.post("/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, user_data: UserLogin, response: Response):
    user = await db.users.find_one({"email": user_data.email}, {"_id": 0})
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
        secure=True,
        samesite="none",
        path="/",
        max_age=JWT_EXPIRATION_HOURS * 3600
    )
    
    return {
        "user_id": user["user_id"],
        "email": user["email"],
        "name": user["name"],
        "picture": user.get("picture"),
        "subscription_tier": user.get("subscription_tier", "free"),
        "user_profile": user.get("user_profile"),
        "token": token
    }

@api_router.get("/auth/google")
async def google_oauth_start():
    """Retourne l'URL de redirection Google OAuth"""
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code=500, detail="Google OAuth non configuré (GOOGLE_CLIENT_ID manquant)")

    backend_url = os.environ.get("BACKEND_URL", "http://localhost:8001")
    redirect_uri = f"{backend_url}/api/auth/google/callback"

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
    }
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
    return {"auth_url": auth_url}


@api_router.get("/auth/google/callback")
async def google_oauth_callback(request: Request, response: Response, code: str = None, error: str = None, state: str = None):
    """Reçoit le code Google OAuth, échange contre les tokens et crée la session.
    Also handles Google Calendar integration OAuth when state starts with 'gcal_integrate:'."""
    frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")

    # --- Google Calendar integration flow ---
    if state and state.startswith("gcal_integrate:"):
        if error or not code:
            return RedirectResponse(f"{frontend_url}/integrations?error=oauth_annulé&service=google_calendar")

        state_doc = await db.integration_states.find_one_and_delete({"state": state, "service": "google_calendar"})
        if not state_doc:
            return RedirectResponse(f"{frontend_url}/integrations?error=invalid_state&service=google_calendar")

        expires_at = datetime.fromisoformat(state_doc["expires_at"])
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            return RedirectResponse(f"{frontend_url}/integrations?error=expired&service=google_calendar")

        user_id = state_doc["user_id"]
        backend_url = os.environ.get("BACKEND_URL", "http://localhost:8001")
        redirect_uri = f"{backend_url}/api/auth/google/callback"

        try:
            async with httpx.AsyncClient() as http_client:
                token_resp = await http_client.post("https://oauth2.googleapis.com/token", data={
                    "client_id": os.environ.get("GOOGLE_CLIENT_ID"),
                    "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET"),
                    "code": code, "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                })
                if token_resp.status_code != 200:
                    logger.error(f"Google Calendar token exchange failed: {token_resp.text}")
                    return RedirectResponse(f"{frontend_url}/integrations?error=token_failed&service=google_calendar")

                token_data = token_resp.json()
                access_token = token_data.get("access_token")
                refresh_token = token_data.get("refresh_token")
                expires_in = token_data.get("expires_in", 3600)

                if not access_token:
                    logger.error(f"Google Calendar: no access_token in response: {token_data}")
                    return RedirectResponse(f"{frontend_url}/integrations?error=token_failed&service=google_calendar")

                # Get account email
                account_name = "Google Calendar"
                try:
                    info_resp = await http_client.get(
                        "https://www.googleapis.com/oauth2/v2/userinfo",
                        headers={"Authorization": f"Bearer {access_token}"}
                    )
                    if info_resp.status_code == 200:
                        account_name = info_resp.json().get("email", "Google Calendar")
                except Exception:
                    pass

                encrypted_access = encrypt_token(access_token)
                encrypted_refresh = encrypt_token(refresh_token) if refresh_token else None

                integration_doc = {
                    "user_id": user_id,
                    "service": "google_calendar",
                    "provider": "google_calendar",
                    "access_token": encrypted_access,
                    "refresh_token": encrypted_refresh,
                    "expires_in": expires_in,
                    "token_expires_at": (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).isoformat(),
                    "token_obtained_at": datetime.now(timezone.utc).isoformat(),
                    "account_name": account_name,
                    "connected_at": datetime.now(timezone.utc).isoformat(),
                    "enabled": True,
                    "sync_enabled": True,
                }
                await db.integrations.update_one(
                    {"user_id": user_id, "service": "google_calendar"},
                    {"$set": integration_doc},
                    upsert=True,
                )
                logger.info(f"Google Calendar integration connected for user {user_id} ({account_name})")
                return RedirectResponse(f"{frontend_url}/integrations?success=google_calendar")

        except Exception as e:
            logger.error(f"Google Calendar integration error: {e}")
            return RedirectResponse(f"{frontend_url}/integrations?error=connection_failed&service=google_calendar")

    # --- Normal login flow ---
    if error or not code:
        return RedirectResponse(url=f"{frontend_url}/login?error=oauth_annulé")

    backend_url = os.environ.get("BACKEND_URL", "http://localhost:8001")
    redirect_uri = f"{backend_url}/api/auth/google/callback"

    async with httpx.AsyncClient() as http_client:
        # Échange du code contre les tokens
        token_resp = await http_client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": os.environ.get("GOOGLE_CLIENT_ID"),
                "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET"),
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if token_resp.status_code != 200:
            logger.error(f"Google token exchange failed: {token_resp.text}")
            return RedirectResponse(url=f"{frontend_url}/login?error=auth_échouée")

        tokens = token_resp.json()

        # Récupération des infos utilisateur
        userinfo_resp = await http_client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        if userinfo_resp.status_code != 200:
            return RedirectResponse(url=f"{frontend_url}/login?error=profil_inaccessible")

        user_info = userinfo_resp.json()

    email = user_info.get("email")
    name = user_info.get("name", email)
    picture = user_info.get("picture")

    # Création ou mise à jour de l'utilisateur
    existing_user = await db.users.find_one({"email": email}, {"_id": 0})
    if existing_user:
        user_id = existing_user["user_id"]
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"name": name, "picture": picture}},
        )
    else:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        user_doc = {
            "user_id": user_id,
            "email": email,
            "name": name,
            "picture": picture,
            "subscription_tier": "free",
            "total_time_invested": 0,
            "streak_days": 0,
            "last_session_date": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.users.insert_one(user_doc)

    # Création de la session locale
    session_token = f"session_{uuid.uuid4().hex}"
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    # Redirection vers le frontend avec le session_id dans le hash (compatible AuthCallback)
    return RedirectResponse(url=f"{frontend_url}/auth/callback#session_id={session_token}")


@api_router.post("/auth/session")
async def process_oauth_session(request: Request, response: Response):
    """Valide un session_id local (créé par /auth/google/callback) et retourne l'utilisateur"""
    body = await request.json()
    session_id = body.get("session_id")

    if not session_id:
        raise HTTPException(status_code=400, detail="session_id requis")

    # Recherche de la session dans la base locale
    session_doc = await db.user_sessions.find_one({"session_token": session_id}, {"_id": 0})
    if not session_doc:
        raise HTTPException(status_code=401, detail="Session invalide")

    # Vérification de l'expiration
    expires_at = session_doc.get("expires_at")
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expirée")

    user = await db.users.find_one({"user_id": session_doc["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    user_id = user["user_id"]

    response.set_cookie(
        key="session_token",
        value=session_id,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7 * 24 * 3600,
    )

    # JWT en backup pour localStorage
    jwt_token = create_token(user_id)

    return {
        "user_id": user_id,
        "email": user["email"],
        "name": user["name"],
        "picture": user.get("picture"),
        "subscription_tier": user.get("subscription_tier", "free"),
        "user_profile": user.get("user_profile"),
        "token": jwt_token,
    }

@api_router.get("/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    return {
        "user_id": user["user_id"],
        "email": user["email"],
        "name": user["name"],
        "picture": user.get("picture"),
        "subscription_tier": user.get("subscription_tier", "free"),
        "total_time_invested": user.get("total_time_invested", 0),
        "streak_days": user.get("streak_days", 0),
        "user_profile": user.get("user_profile")
    }

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    
    response.delete_cookie(key="session_token", path="/", samesite="none", secure=True)
    return {"message": "Logged out successfully"}

@api_router.post("/auth/refresh")
async def refresh_token(request: Request, response: Response, user: dict = Depends(get_current_user)):
    """Refresh JWT token for active users - extends session by 7 days"""
    new_token = create_token(user["user_id"])
    response.set_cookie(
        key="session_token",
        value=new_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=JWT_EXPIRATION_HOURS * 3600
    )
    return {
        "token": new_token,
        "user_id": user["user_id"],
        "email": user["email"],
        "name": user["name"],
        "picture": user.get("picture"),
        "subscription_tier": user.get("subscription_tier", "free"),
        "total_time_invested": user.get("total_time_invested", 0),
        "streak_days": user.get("streak_days", 0)
    }

# ============== ONBOARDING ROUTES ==============

@api_router.post("/onboarding/profile")
async def save_onboarding_profile(
    profile: OnboardingProfile,
    user: dict = Depends(get_current_user)
):
    """Save user onboarding profile and generate AI welcome message"""
    profile_dict = profile.model_dump()

    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {
            "user_profile": profile_dict,
            "onboarding_completed": True
        }}
    )

    user["user_profile"] = profile_dict
    user_context = await build_user_context(user)

    goals_map = {"learning": "apprentissage", "productivity": "productivité", "well_being": "bien-être"}
    goals_fr = ", ".join([goals_map.get(g, g) for g in profile.goals])

    prompt = f"""{user_context}

L'utilisateur vient de créer son compte et de compléter son profil.
Ses objectifs principaux sont : {goals_fr}.

Génère un message d'accueil personnalisé et chaleureux, puis recommande une première micro-action adaptée à son profil.
Réponds en JSON:
{{
    "welcome_message": "Message d'accueil personnalisé (2-3 phrases)",
    "first_recommendation": "Description de la première action recommandée (1-2 phrases)"
}}"""

    ai_response = await call_ai(f"onboarding_{user['user_id']}", AI_SYSTEM_MESSAGE, prompt)
    ai_result = parse_ai_json(ai_response)

    default_welcome = f"Bienvenue sur InFinea, {user.get('name', '')} ! Prêt(e) à transformer vos moments perdus en micro-victoires ?"
    default_reco = "Commencez par une session de respiration de 2 minutes pour vous recentrer."

    return {
        "welcome_message": ai_result.get("welcome_message", default_welcome) if ai_result else default_welcome,
        "first_recommendation": ai_result.get("first_recommendation", default_reco) if ai_result else default_reco,
        "user_profile": profile_dict
    }

@api_router.get("/onboarding/profile")
async def get_onboarding_profile(user: dict = Depends(get_current_user)):
    """Get user's onboarding profile"""
    profile = user.get("user_profile")
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

# ============== MICRO-ACTIONS ROUTES ==============

@api_router.get("/actions", response_model=List[MicroAction])
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
    
    actions = await db.micro_actions.find(query, {"_id": 0}).to_list(5000)
    
    if duration:
        actions = [a for a in actions if a["duration_min"] <= duration <= a["duration_max"]]
    
    return actions

@api_router.get("/actions/custom")
async def get_custom_actions(user: dict = Depends(get_current_user)):
    """Get user's custom AI-generated actions"""
    actions = await db.user_custom_actions.find(
        {"created_by": user["user_id"]},
        {"_id": 0}
    ).to_list(50)
    return actions

@api_router.get("/actions/{action_id}")
async def get_action(action_id: str):
    action = await db.micro_actions.find_one({"action_id": action_id}, {"_id": 0})
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    return action

# ============== AI SUGGESTIONS ROUTE ==============

@api_router.post("/suggestions")
async def get_ai_suggestions(
    ai_request: AIRequest,
    user: dict = Depends(get_current_user)
):
    """Get AI-powered micro-action suggestions based on time and energy"""
    # Get matching actions from database
    query = {"duration_min": {"$lte": ai_request.available_time}}
    if ai_request.preferred_category:
        query["category"] = ai_request.preferred_category
    if ai_request.energy_level:
        query["energy_level"] = ai_request.energy_level

    # Filter premium actions for free users
    if user.get("subscription_tier") == "free":
        query["is_premium"] = False

    available_actions = await db.micro_actions.find(query, {"_id": 0}).to_list(50)

    if not available_actions:
        return {
            "suggestion": "Prenez une pause de respiration profonde",
            "reasoning": "Aucune micro-action ne correspond exactement à vos critères. Profitez de ce moment pour vous recentrer.",
            "recommended_actions": []
        }

    # Score and rank actions using behavioral features
    ranked_actions = await rank_actions_for_user(
        db, user["user_id"], available_actions,
        energy_level=ai_request.energy_level or "medium",
        available_time=ai_request.available_time,
    )
    is_scored = any("_score" in a for a in ranked_actions)

    # Get user's recent activity for personalization
    recent_sessions = await db.user_sessions_history.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).sort("started_at", -1).limit(5).to_list(5)

    recent_categories = [s.get("category", "") for s in recent_sessions]

    # Build context for AI — top 10 scored actions
    top_actions = ranked_actions[:10]
    actions_text = "\n".join([
        f"- {a['title']} ({a['category']}, {a['duration_min']}-{a['duration_max']}min, énergie: {a['energy_level']})"
        + (f" [score: {a['_score']:.2f}]" if is_scored else "")
        + f": {a['description']}"
        for a in top_actions
    ])

    is_premium = user.get("subscription_tier") == "premium"

    if is_scored and is_premium:
        # Premium + scored: enrich prompt with behavioral insights for Sonnet
        top = ranked_actions[0] if ranked_actions else {}
        breakdown = top.get("_breakdown", {})
        features_doc = await db.user_features.find_one({"user_id": user["user_id"]}, {"_id": 0})
        consistency = features_doc.get("consistency_index", 0) if features_doc else 0
        best_buckets = features_doc.get("best_performing_buckets", []) if features_doc else []

        prompt = f"""L'utilisateur a {ai_request.available_time} minutes disponibles et un niveau d'énergie {ai_request.energy_level}.
Catégories récentes: {', '.join(recent_categories) if recent_categories else 'Aucune'}
Catégorie préférée: {ai_request.preferred_category or 'Aucune'}

Profil comportemental :
- Indice de régularité : {consistency:.0%}
- Meilleurs créneaux : {', '.join(best_buckets) if best_buckets else 'pas assez de données'}
- Score #1 : {breakdown.get('category_affinity', 0):.0%} affinité catégorie, {breakdown.get('duration_fit', 0):.0%} adéquation durée, {breakdown.get('energy_match', 0):.0%} match énergie

Voici les micro-actions classées par pertinence (score comportemental) :
{actions_text}

La première action est la plus adaptée selon l'historique de l'utilisateur.
Explique en 2-3 phrases pourquoi c'est le meilleur choix, en t'appuyant sur le profil comportemental.
Propose aussi 2 alternatives avec un mot sur pourquoi chacune.
Format JSON :
- "top_pick": titre de la meilleure action
- "reasoning": explication personnalisée (2-3 phrases)
- "alternatives": liste de 2 autres titres"""
    elif is_scored:
        prompt = f"""L'utilisateur a {ai_request.available_time} minutes disponibles et un niveau d'énergie {ai_request.energy_level}.
Catégories récentes: {', '.join(recent_categories) if recent_categories else 'Aucune'}
Catégorie préférée: {ai_request.preferred_category or 'Aucune'}

Voici les micro-actions classées par pertinence (score comportemental) :
{actions_text}

La première action est la plus adaptée selon l'historique de l'utilisateur.
Explique en 1 phrase pourquoi c'est le meilleur choix pour ce moment.
Propose aussi 2 alternatives parmi les suivantes.
Format JSON :
- "top_pick": titre de la meilleure action
- "reasoning": explication courte pourquoi c'est le meilleur choix
- "alternatives": liste de 2 autres titres"""
    else:
        prompt = f"""L'utilisateur a {ai_request.available_time} minutes disponibles et un niveau d'énergie {ai_request.energy_level}.
Catégories récentes: {', '.join(recent_categories) if recent_categories else 'Aucune'}
Catégorie préférée: {ai_request.preferred_category or 'Aucune'}

Voici les micro-actions disponibles:
{actions_text}

Recommande les 3 meilleures micro-actions pour ce moment. Explique brièvement pourquoi chacune est adaptée.
Format ta réponse en JSON avec:
- "top_pick": titre de la meilleure action
- "reasoning": explication courte (1 phrase) pourquoi c'est le meilleur choix
- "alternatives": liste de 2 autres titres d'actions adaptées"""

    system_msg = """Tu es l'assistant InFinea, expert en productivité et bien-être.
Tu aides les utilisateurs à transformer leurs moments perdus en micro-victoires.
Réponds toujours en français, de manière concise et motivante.
Suggère les meilleures micro-actions en fonction du temps disponible et du niveau d'énergie."""

    response = await call_ai(f"suggestion_{user['user_id']}", system_msg, prompt, model=get_ai_model(user))
    ai_result = parse_ai_json(response)

    # 3.5 — Deterministic fallback: use top scored action instead of random first
    if not ai_result:
        ai_result = {"top_pick": ranked_actions[0]["title"], "reasoning": "Basé sur votre profil comportemental et le temps disponible.", "alternatives": []}

    # Match recommended actions with full action data
    recommended_actions = []
    for action in ranked_actions:
        if action["title"] == ai_result.get("top_pick"):
            recommended_actions.insert(0, action)
        elif action["title"] in ai_result.get("alternatives", []):
            recommended_actions.append(action)

    # Fill with remaining ranked actions if needed
    if len(recommended_actions) < 3:
        for action in ranked_actions:
            if action not in recommended_actions:
                recommended_actions.append(action)
            if len(recommended_actions) >= 3:
                break

    # Strip internal scoring fields from response
    clean_actions = []
    for a in recommended_actions[:3]:
        clean = {k: v for k, v in a.items() if not k.startswith("_")}
        clean_actions.append(clean)

    await track_event(db, user["user_id"], "suggestion_generated", {
        "available_time": ai_request.available_time,
        "energy_level": ai_request.energy_level,
        "category": ai_request.preferred_category,
        "top_pick": ai_result.get("top_pick"),
        "num_actions_available": len(available_actions),
        "scoring_active": is_scored,
        "top_score": ranked_actions[0].get("_score") if is_scored else None,
    })

    # Record impression signals for all shown actions (feedback loop)
    for shown_action in recommended_actions[:3]:
        aid = shown_action.get("action_id")
        if aid:
            await record_signal(db, user["user_id"], aid, "impression")

    result = {
        "suggestion": ai_result.get("top_pick", ranked_actions[0]["title"]),
        "reasoning": ai_result.get("reasoning", "Cette action est parfaite pour le temps dont vous disposez."),
        "recommended_actions": clean_actions,
    }

    # 3.4 — Scoring metadata (backward-compatible, frontend ignores it)
    if is_scored:
        result["scoring_metadata"] = {
            "scored": True,
            "top_score": ranked_actions[0].get("_score"),
            "actions_scored": len(ranked_actions),
            "feature_version": ranked_actions[0].get("_breakdown") is not None,
        }

    return result

# ============== PROACTIVE SUGGEST-NOW ROUTE ==============

@api_router.get("/suggest-now")
async def suggest_now(user: dict = Depends(get_current_user)):
    """
    Proactive suggestion: infer time, energy, and ideal duration from features.
    Returns top 3 actions without any user input required.
    """
    user_id = user["user_id"]
    features = await db.user_features.find_one({"user_id": user_id}, {"_id": 0})

    if not features:
        return {
            "suggestions": [],
            "context": {"scored": False},
            "message": "Pas assez de donnees pour une suggestion proactive. Completez quelques sessions d'abord.",
        }

    # Infer context from features
    from services.scoring_engine import _current_time_bucket
    bucket = _current_time_bucket()

    # Inferred energy from user's pattern at this time
    energy_pref = features.get("energy_preference_by_time", {})
    inferred_energy = energy_pref.get(bucket, "medium")

    # Inferred duration from user's preference
    preferred_duration = features.get("preferred_action_duration", 5.0)
    available_time = max(int(preferred_duration * 1.5), 10)

    # Fetch & score actions
    query = {"duration_min": {"$lte": available_time}}
    if user.get("subscription_tier") == "free":
        query["is_premium"] = False

    actions = await db.micro_actions.find(query, {"_id": 0}).to_list(50)
    if not actions:
        return {
            "suggestions": [],
            "context": {"scored": False},
            "message": "Aucune action disponible pour le moment.",
        }

    ranked = await rank_actions_for_user(
        db, user_id, actions,
        energy_level=inferred_energy,
        available_time=available_time,
    )

    # Top 3, clean internal fields
    top3 = []
    for a in ranked[:3]:
        clean = {k: v for k, v in a.items() if not k.startswith("_")}
        clean["score"] = a.get("_score")
        top3.append(clean)

    return {
        "suggestions": top3,
        "context": {
            "scored": True,
            "time_bucket": bucket,
            "inferred_energy": inferred_energy,
            "available_time": available_time,
            "preferred_duration": preferred_duration,
        },
    }

# ============== SMART PREDICTION ROUTE ==============

@api_router.get("/smart-predict")
async def smart_predict(user: dict = Depends(get_current_user)):
    """
    Intelligent prediction module: combines integrations data, detected slots,
    and scoring engine to predict next available moments with best actions.
    """
    user_id = user["user_id"]
    now = datetime.now(timezone.utc)

    # 1. Connected integrations (without secrets)
    integrations_raw = await db.user_integrations.find(
        {"user_id": user_id},
        {"_id": 0, "access_token": 0, "refresh_token": 0}
    ).to_list(10)

    integrations = []
    for integ in integrations_raw:
        integrations.append({
            "service": integ.get("service") or integ.get("provider", "unknown"),
            "status": "connected",
            "last_sync": integ.get("last_sync_at") or integ.get("last_synced_at"),
            "connected_at": integ.get("connected_at"),
        })

    # 2. Upcoming free slots (next 24h, max 5)
    end_24h = (now + timedelta(hours=24)).isoformat()
    raw_slots = await db.detected_free_slots.find({
        "user_id": user_id,
        "start_time": {"$gte": now.isoformat(), "$lte": end_24h},
        "dismissed": {"$ne": True},
        "action_taken": {"$ne": True},
    }, {"_id": 0}).sort("start_time", 1).to_list(5)

    # 3. Enrich each slot with scored suggestion
    predictions = []
    total_free_minutes = 0
    for slot in raw_slots:
        duration = slot.get("duration_minutes", 0)
        total_free_minutes += duration

        prediction = {
            "slot_id": slot.get("slot_id"),
            "start_time": slot.get("start_time"),
            "end_time": slot.get("end_time"),
            "duration_minutes": duration,
            "suggested_category": slot.get("suggested_category"),
        }

        # Try to score a suggestion
        if duration > 0:
            try:
                scored = await get_next_best_action(
                    db, user_id,
                    slot_duration=duration,
                    slot_start_time=slot.get("start_time"),
                    min_score=0.4,
                )
                if scored:
                    prediction["suggested_action"] = {
                        "action_id": scored.get("action_id"),
                        "title": scored.get("title"),
                        "category": scored.get("category"),
                        "score": scored.get("_score"),
                        "energy_level": scored.get("energy_level"),
                        "duration_min": scored.get("duration_min"),
                    }
            except Exception:
                pass  # scoring is best-effort

        # Fallback: use the pre-assigned suggestion if no scoring
        if "suggested_action" not in prediction and slot.get("suggested_action_id"):
            action = await db.micro_actions.find_one(
                {"action_id": slot["suggested_action_id"]}, {"_id": 0}
            )
            if action:
                prediction["suggested_action"] = {
                    "action_id": action.get("action_id"),
                    "title": action.get("title"),
                    "category": action.get("category"),
                    "energy_level": action.get("energy_level"),
                    "duration_min": action.get("duration_min"),
                }

        predictions.append(prediction)

    # 4. Proactive best action (from behavioral features)
    proactive = None
    features = await db.user_features.find_one({"user_id": user_id}, {"_id": 0})
    if features:
        try:
            from services.scoring_engine import _current_time_bucket
            bucket = _current_time_bucket()
            energy_pref = features.get("energy_preference_by_time", {})
            inferred_energy = energy_pref.get(bucket, "medium")
            preferred_duration = features.get("preferred_action_duration", 5.0)
            proactive = {
                "time_bucket": bucket,
                "inferred_energy": inferred_energy,
                "preferred_duration": round(preferred_duration, 1),
                "consistency_index": features.get("consistency_index", 0),
            }
        except Exception:
            pass

    return {
        "integrations": integrations,
        "predictions": predictions,
        "next_prediction": predictions[0] if predictions else None,
        "proactive": proactive,
        "context": {
            "has_integrations": len(integrations) > 0,
            "total_slots_today": len(predictions),
            "total_free_minutes": total_free_minutes,
            "scored": features is not None,
        },
    }

# ============== AI COACH ROUTE ==============

@api_router.get("/ai/coach")
@limiter.limit("10/minute")
async def get_ai_coach(request: Request, user: dict = Depends(get_current_user)):
    """Get personalized AI coach message for dashboard — context-aware"""
    user_context = await build_user_context(user)
    now = datetime.now(timezone.utc)

    # --- 1. Context detection: what just happened? ---
    # Fetch last 5 sessions (completed OR abandoned) for context
    all_recent = await db.user_sessions_history.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).sort("started_at", -1).limit(5).to_list(5)

    recent_completed = [s for s in all_recent if s.get("completed")]
    recent_abandoned = [s for s in all_recent if not s.get("completed") and s.get("completed_at")]

    # Detect immediate context (what happened in the last minutes)
    coach_mode = "default"  # default | post_completion | post_abandon | streak_milestone | comeback | first_visit
    context_detail = ""

    if not all_recent:
        # No sessions at all — first time user
        coach_mode = "first_visit"
        context_detail = "\nCONTEXTE: Première visite de l'utilisateur ! Il n'a encore fait aucune session. Sois chaleureux, explique le concept des micro-actions, et encourage à faire la première."
    else:
        # Check for recent completion (< 10 min ago)
        if recent_completed:
            last_completed = recent_completed[0]
            try:
                completed_at = datetime.fromisoformat(last_completed.get("completed_at", ""))
                if completed_at.tzinfo is None:
                    completed_at = completed_at.replace(tzinfo=timezone.utc)
                minutes_ago = (now - completed_at).total_seconds() / 60
                if minutes_ago < 10:
                    coach_mode = "post_completion"
                    title = last_completed.get("action_title", "micro-action")
                    dur = last_completed.get("actual_duration", "?")
                    context_detail = f"\nCONTEXTE: L'utilisateur vient de TERMINER '{title}' ({dur} min) il y a {int(minutes_ago)} min ! Célèbre cette victoire et propose d'enchaîner."
            except (ValueError, TypeError):
                pass

        # Check for recent abandonment (< 30 min ago)
        if coach_mode == "default" and recent_abandoned:
            last_abandoned = recent_abandoned[0]
            try:
                abandoned_at = datetime.fromisoformat(last_abandoned.get("completed_at", ""))
                if abandoned_at.tzinfo is None:
                    abandoned_at = abandoned_at.replace(tzinfo=timezone.utc)
                minutes_ago = (now - abandoned_at).total_seconds() / 60
                if minutes_ago < 30:
                    coach_mode = "post_abandon"
                    title = last_abandoned.get("action_title", "micro-action")
                    context_detail = f"\nCONTEXTE: L'utilisateur a ABANDONNÉ '{title}' il y a {int(minutes_ago)} min. Sois bienveillant, ne culpabilise pas, et propose une action PLUS COURTE et PLUS FACILE."
            except (ValueError, TypeError):
                pass

        # Check for streak milestones
        streak = user.get("streak_days", 0)
        if coach_mode == "default" and streak in (3, 7, 14, 21, 30, 50, 100):
            coach_mode = "streak_milestone"
            context_detail = f"\nCONTEXTE: L'utilisateur vient d'atteindre un STREAK de {streak} jours ! C'est un accomplissement majeur. Célèbre chaleureusement et motive à continuer."

        # Check for inactivity (> 3 days since last session)
        if coach_mode == "default" and all_recent:
            try:
                last_session_at = datetime.fromisoformat(all_recent[0].get("started_at", ""))
                if last_session_at.tzinfo is None:
                    last_session_at = last_session_at.replace(tzinfo=timezone.utc)
                days_inactive = (now - last_session_at).days
                if days_inactive >= 3:
                    coach_mode = "comeback"
                    context_detail = f"\nCONTEXTE: L'utilisateur n'a pas fait de session depuis {days_inactive} jours. C'est un RETOUR ! Accueille-le chaleureusement, sans culpabiliser, et propose quelque chose de très accessible."
            except (ValueError, TypeError):
                pass

    recent_info = ""
    if recent_completed:
        recent_titles = [s.get("action_title", "action") for s in recent_completed[:3]]
        recent_info = f"\nSessions récentes complétées: {', '.join(recent_titles)}"

    hour = datetime.now().hour
    time_of_day = "matin" if hour < 12 else "après-midi" if hour < 18 else "soir"
    day_names = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
    day_of_week = day_names[datetime.now().weekday()]

    # --- 2. Engagement features for coaching tone ---
    user_features_doc = await db.user_features.find_one(
        {"user_id": user["user_id"]}, {"_id": 0, "engagement_trend": 1, "session_momentum": 1, "abandonment_rate": 1}
    )
    engagement_context = ""
    if user_features_doc:
        trend = user_features_doc.get("engagement_trend", 0.0)
        momentum = user_features_doc.get("session_momentum", 0)
        abandon = user_features_doc.get("abandonment_rate", 0.0)
        if trend > 0.1:
            engagement_context = f"\nL'utilisateur est en progression (+{trend:.0%} cette semaine). Encourage et félicite."
        elif trend < -0.1:
            engagement_context = f"\nL'utilisateur est en baisse ({trend:.0%} cette semaine). Sois bienveillant et motivant, propose quelque chose de léger."
        if momentum >= 5:
            engagement_context += f"\nIl a enchaîné {momentum} sessions d'affilée récemment — souligne cet exploit."
        if abandon > 0.4:
            engagement_context += "\nIl abandonne souvent ses sessions — propose des actions courtes et faciles."

    # --- 2b. Fetch active objectives for context ---
    active_objs = await db.objectives.find(
        {"user_id": user["user_id"], "status": "active"},
        {"_id": 0, "title": 1, "current_day": 1, "target_duration_days": 1, "streak_days": 1, "progress_log": {"$slice": -2}}
    ).to_list(5)
    objectives_context = ""
    if active_objs:
        obj_lines = []
        for o in active_objs:
            pct = round((o.get("current_day", 0) / max(o.get("target_duration_days", 1), 1)) * 100)
            line = f"- \"{o['title']}\" (Jour {o.get('current_day',0)}/{o.get('target_duration_days')}, {pct}%)"
            log = o.get("progress_log", [])
            if log and log[-1].get("step_title"):
                line += f" — dernier: {log[-1]['step_title']}"
            obj_lines.append(line)
        objectives_context = "\n\nParcours actifs (l'utilisateur travaille ces objectifs — mentionne-les !):\n" + "\n".join(obj_lines)

    # --- 3. Fetch & rank candidate actions ---
    profile = user.get("user_profile", {}) or {}
    goals = profile.get("goals", [])
    act_query = {}
    if goals:
        act_query["category"] = {"$in": goals}
    if user.get("subscription_tier") == "free":
        act_query["is_premium"] = False
    # Post-abandon: prioritize short/easy actions
    if coach_mode == "post_abandon":
        act_query["duration_max"] = {"$lte": 5}
    candidate_actions = await db.micro_actions.find(act_query, {"_id": 0}).to_list(20)
    if not candidate_actions and (goals or coach_mode == "post_abandon"):
        fallback_query = {}
        if user.get("subscription_tier") == "free":
            fallback_query["is_premium"] = False
        candidate_actions = await db.micro_actions.find(fallback_query, {"_id": 0}).to_list(20)

    top_actions = candidate_actions[:5]
    try:
        from services.scoring_engine import rank_actions_for_user
        ranked = await rank_actions_for_user(db, user["user_id"], candidate_actions)
        top_actions = ranked[:5] if ranked else candidate_actions[:5]
    except Exception:
        pass

    actions_menu = ""
    if top_actions:
        action_lines = []
        for i, a in enumerate(top_actions):
            dur = f"{a.get('duration_min', '?')}-{a.get('duration_max', '?')} min"
            energy = a.get("energy_level", "medium")
            action_lines.append(f"  {i}: \"{a.get('title', 'Action')}\" ({a.get('category', '')}, {dur}, énergie: {energy})")
        actions_menu = "\n\nActions disponibles (classées par pertinence):\n" + "\n".join(action_lines)

    # --- 4. Build prompt with context ---
    prompt = f"""{user_context}{recent_info}{engagement_context}{objectives_context}{context_detail}

Il est actuellement le {time_of_day} ({day_of_week}).
Le streak actuel est de {user.get('streak_days', 0)} jours.{actions_menu}

Génère un message de coach personnalisé adapté au CONTEXTE ci-dessus.
Ta suggestion DOIT correspondre à une des actions disponibles (indique son numéro dans chosen_action).
Réponds en JSON:
{{
    "greeting": "Message d'accueil personnalisé, adapté au contexte (1-2 phrases)",
    "suggestion": "Suggestion basée sur l'action choisie — explique POURQUOI cette action est idéale MAINTENANT vu le contexte (1-2 phrases)",
    "chosen_action": 0,
    "context_note": "Note contextuelle courte (1 phrase)"
}}"""

    ai_response = await call_ai(f"coach_{user['user_id']}", AI_SYSTEM_MESSAGE, prompt, model=get_ai_model(user))
    ai_result = parse_ai_json(ai_response)

    # Resolve suggested_action_id from AI choice
    suggested_action_id = None
    suggested_title = None
    if ai_result and top_actions:
        chosen_idx = ai_result.get("chosen_action", 0)
        if isinstance(chosen_idx, int) and 0 <= chosen_idx < len(top_actions):
            suggested_action_id = top_actions[chosen_idx].get("action_id")
            suggested_title = top_actions[chosen_idx].get("title")
        else:
            suggested_action_id = top_actions[0].get("action_id")
            suggested_title = top_actions[0].get("title")
    elif top_actions:
        suggested_action_id = top_actions[0].get("action_id")
        suggested_title = top_actions[0].get("title")

    await track_event(db, user["user_id"], "ai_coach_served", {
        "ai_success": ai_result is not None,
        "time_of_day": time_of_day,
        "coach_mode": coach_mode,
        "suggested_action_id": suggested_action_id,
    })

    if ai_result:
        return {
            "greeting": ai_result.get("greeting", f"Bonjour {user.get('name', '')} !"),
            "suggestion": ai_result.get("suggestion", "Commencez une micro-action pour avancer."),
            "suggested_action_id": suggested_action_id,
            "suggested_action_title": suggested_title,
            "coach_mode": coach_mode,
            "context_note": ai_result.get("context_note", f"C'est le {time_of_day}, bon moment pour progresser.")
        }

    return {
        "greeting": f"Bonjour {user.get('name', '').split(' ')[0]} ! Prêt(e) pour une micro-victoire ?",
        "suggestion": f"Que dirais-tu de : {suggested_title}" if suggested_title else "Profitez de quelques minutes pour progresser vers vos objectifs.",
        "suggested_action_id": suggested_action_id,
        "suggested_action_title": suggested_title,
        "coach_mode": coach_mode,
        "context_note": f"C'est le {time_of_day}, idéal pour une micro-action."
    }

# ============== COACH CHAT (PERSISTENT) ==============

COACH_CHAT_SYSTEM = """Tu es le coach IA InFinea, un compagnon bienveillant et expert en productivité, apprentissage et bien-être.
Tu discutes naturellement avec l'utilisateur pour l'aider à progresser.
Tu es concis (2-3 phrases max par réponse), chaleureux, et tu tutoies l'utilisateur.
Tu connais son profil, ses sessions récentes, et tu peux suggérer des actions concrètes.
Quand tu suggères une action, mentionne son nom exact pour que l'utilisateur puisse la lancer.
Ne réponds JAMAIS en JSON — réponds en texte naturel conversationnel."""


@api_router.get("/ai/coach/history")
@limiter.limit("20/minute")
async def get_coach_history(request: Request, user: dict = Depends(get_current_user)):
    """Get coach conversation history for the current user."""
    messages = await db.coach_messages.find(
        {"user_id": user["user_id"]},
        {"_id": 0, "role": 1, "content": 1, "created_at": 1, "suggested_action_id": 1}
    ).sort("created_at", 1).limit(50).to_list(50)

    return {"messages": messages}


@api_router.post("/ai/coach/chat")
@limiter.limit("15/minute")
async def coach_chat(
    request: Request,
    chat_req: CoachChatRequest,
    user: dict = Depends(get_current_user),
):
    """Send a message to the coach and get a response."""
    user_message = chat_req.message.strip()
    if not user_message or len(user_message) > 500:
        raise HTTPException(status_code=400, detail="Message vide ou trop long (max 500 caractères)")

    now = datetime.now(timezone.utc).isoformat()

    # Save user message
    await db.coach_messages.insert_one({
        "user_id": user["user_id"],
        "role": "user",
        "content": user_message,
        "created_at": now,
    })

    # Build context for the AI
    user_context = await build_user_context(user)

    # Fetch recent sessions for context
    recent_sessions = await db.user_sessions_history.find(
        {"user_id": user["user_id"]},
        {"_id": 0, "action_title": 1, "completed": 1, "started_at": 1, "actual_duration": 1}
    ).sort("started_at", -1).limit(5).to_list(5)

    sessions_ctx = ""
    if recent_sessions:
        lines = []
        for s in recent_sessions:
            status = "terminée" if s.get("completed") else "abandonnée"
            lines.append(f"- {s.get('action_title', '?')} ({status}, {s.get('actual_duration', '?')} min)")
        sessions_ctx = "\n\nDernières sessions:\n" + "\n".join(lines)

    # Fetch available actions for suggestions
    act_query = {}
    if user.get("subscription_tier") == "free":
        act_query["is_premium"] = False
    available = await db.micro_actions.find(act_query, {"_id": 0, "action_id": 1, "title": 1, "category": 1, "duration_min": 1, "duration_max": 1}).to_list(10)
    actions_ctx = ""
    if available:
        lines = [f"- \"{a.get('title')}\" ({a.get('category')}, {a.get('duration_min')}-{a.get('duration_max')} min)" for a in available[:8]]
        actions_ctx = "\n\nActions disponibles que tu peux suggérer:\n" + "\n".join(lines)

    # Fetch active objectives for context
    active_objectives = await db.objectives.find(
        {"user_id": user["user_id"], "status": "active"},
        {"_id": 0, "title": 1, "category": 1, "current_day": 1, "target_duration_days": 1,
         "total_sessions": 1, "total_minutes": 1, "streak_days": 1, "progress_log": {"$slice": -3}}
    ).to_list(5)

    objectives_ctx = ""
    if active_objectives:
        lines = []
        for o in active_objectives:
            pct = round((o.get("current_day", 0) / max(o.get("target_duration_days", 1), 1)) * 100)
            line = f"- \"{o.get('title')}\" (Jour {o.get('current_day', 0)}/{o.get('target_duration_days')}, {pct}%, streak {o.get('streak_days', 0)}j)"
            # Add last session notes for continuity
            log = o.get("progress_log", [])
            if log:
                last = log[-1]
                if last.get("notes"):
                    line += f"\n  Dernière note: \"{last['notes']}\""
                if last.get("step_title"):
                    line += f"\n  Dernier focus: {last['step_title']}"
            lines.append(line)
        objectives_ctx = "\n\nObjectifs actifs de l'utilisateur (IMPORTANT — réfère-toi à ces parcours):\n" + "\n".join(lines)

    # Build conversation history (last 20 messages for context window)
    history_docs = await db.coach_messages.find(
        {"user_id": user["user_id"]},
        {"_id": 0, "role": 1, "content": 1}
    ).sort("created_at", -1).limit(20).to_list(20)
    history_docs.reverse()

    # Build messages array for Anthropic API (system + history)
    system_prompt = f"""{COACH_CHAT_SYSTEM}

{user_context}{sessions_ctx}{objectives_ctx}{actions_ctx}

Streak actuel: {user.get('streak_days', 0)} jours.
Temps total investi: {user.get('total_time_invested', 0)} minutes."""

    api_messages = []
    for msg in history_docs:
        role = msg["role"]
        if role in ("user", "assistant"):
            api_messages.append({"role": role, "content": msg["content"]})

    # Ensure conversation starts with user message (Anthropic requirement)
    if not api_messages or api_messages[0]["role"] != "user":
        api_messages = [m for m in api_messages if m["role"] in ("user", "assistant")]
        if not api_messages:
            api_messages = [{"role": "user", "content": user_message}]

    # Call AI with full conversation
    api_key = os.environ.get('ANTHROPIC_API_KEY') or os.environ.get('OPENAI_API_KEY')
    ai_model = get_ai_model(user)
    assistant_content = None

    if api_key:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client_http:
                resp = await client_http.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    },
                    json={
                        "model": ai_model,
                        "max_tokens": 300,
                        "system": system_prompt,
                        "messages": api_messages,
                    }
                )
                resp.raise_for_status()
                data = resp.json()
                assistant_content = data["content"][0]["text"]
        except Exception as e:
            logger.error(f"Coach chat AI error: {e}")

    if not assistant_content:
        assistant_content = "Je suis là pour t'aider ! Malheureusement j'ai un petit souci technique. Réessaie dans un instant."

    # Save assistant response
    await db.coach_messages.insert_one({
        "user_id": user["user_id"],
        "role": "assistant",
        "content": assistant_content,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    await track_event(db, user["user_id"], "coach_chat_message", {
        "message_length": len(user_message),
    })

    return {
        "role": "assistant",
        "content": assistant_content,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


@api_router.delete("/ai/coach/history")
@limiter.limit("5/minute")
async def clear_coach_history(request: Request, user: dict = Depends(get_current_user)):
    """Clear coach conversation history."""
    result = await db.coach_messages.delete_many({"user_id": user["user_id"]})
    return {"deleted": result.deleted_count}


# ============== AI DEBRIEF ROUTE ==============

@api_router.post("/ai/debrief")
@limiter.limit("10/minute")
async def get_ai_debrief(
    request: Request,
    debrief_req: DebriefRequest,
    user: dict = Depends(get_current_user)
):
    """Get AI debrief after completing a session"""
    user_context = await build_user_context(user)

    # Support both frontend format (duration_minutes) and legacy (actual_duration)
    duration = debrief_req.duration_minutes or debrief_req.actual_duration or 0
    action_title = debrief_req.action_title or "micro-action"
    action_category = debrief_req.action_category or "productivité"

    # Try to get session info from DB if we have session_id
    if debrief_req.session_id and (not debrief_req.action_title):
        session = await db.sessions.find_one({"session_id": debrief_req.session_id})
        if session:
            action_info = session.get("action", {})
            action_title = action_info.get("title", action_title)
            action_category = action_info.get("category", action_category)
            if not duration:
                duration = session.get("actual_duration", 0)

    notes_info = f"\nNotes de l'utilisateur: {debrief_req.notes}" if debrief_req.notes else ""

    # --- Fetch & rank next actions BEFORE AI call ---
    next_query = {}
    if user.get("subscription_tier") == "free":
        next_query["is_premium"] = False
    next_candidates = await db.micro_actions.find(next_query, {"_id": 0}).to_list(20)
    top_next = next_candidates[:5]
    try:
        from services.scoring_engine import rank_actions_for_user
        ranked = await rank_actions_for_user(db, user["user_id"], next_candidates)
        top_next = ranked[:5] if ranked else next_candidates[:5]
    except Exception:
        pass

    # Build action menu for AI
    actions_menu = ""
    if top_next:
        action_lines = []
        for i, a in enumerate(top_next):
            dur = f"{a.get('duration_min', '?')}-{a.get('duration_max', '?')} min"
            action_lines.append(f"  {i}: \"{a.get('title', 'Action')}\" ({a.get('category', '')}, {dur})")
        actions_menu = "\n\nProchaines actions possibles (classées par pertinence):\n" + "\n".join(action_lines)

    prompt = f"""{user_context}

L'utilisateur vient de terminer une session:
- Action: {action_title} (catégorie: {action_category})
- Durée réelle: {duration} minutes{notes_info}{actions_menu}

Génère un débrief personnalisé et motivant.
Ta next_suggestion DOIT correspondre à une des actions ci-dessus (indique son numéro dans chosen_action).
Réponds en JSON:
{{
    "feedback": "Feedback personnalisé sur la session (1-2 phrases)",
    "encouragement": "Message de motivation (1 phrase)",
    "next_suggestion": "Suggestion pour la prochaine action basée sur l'action choisie (1 phrase)",
    "chosen_action": 0
}}"""

    ai_response = await call_ai(f"debrief_{user['user_id']}", AI_SYSTEM_MESSAGE, prompt, model=get_ai_model(user))
    ai_result = parse_ai_json(ai_response)

    # Resolve next_action_id from AI choice
    next_action_id = None
    next_action_title = None
    if ai_result and top_next:
        chosen_idx = ai_result.get("chosen_action", 0)
        if isinstance(chosen_idx, int) and 0 <= chosen_idx < len(top_next):
            next_action_id = top_next[chosen_idx].get("action_id")
            next_action_title = top_next[chosen_idx].get("title")
        else:
            next_action_id = top_next[0].get("action_id")
            next_action_title = top_next[0].get("title")
    elif top_next:
        next_action_id = top_next[0].get("action_id")
        next_action_title = top_next[0].get("title")

    await track_event(db, user["user_id"], "ai_debrief_generated", {
        "action_title": action_title,
        "category": action_category,
        "duration": duration,
        "ai_success": ai_result is not None,
        "next_action_id": next_action_id,
    })

    if ai_result:
        return {
            "feedback": ai_result.get("feedback", "Bravo pour cette session !"),
            "encouragement": ai_result.get("encouragement", "Chaque minute compte."),
            "next_suggestion": ai_result.get("next_suggestion", "Continuez sur cette lancée !"),
            "next_action_id": next_action_id,
            "next_action_title": next_action_title,
        }

    return {
        "feedback": f"Excellente session de {duration} min sur {action_title} !",
        "encouragement": "Chaque micro-action vous rapproche de vos objectifs.",
        "next_suggestion": f"Pour continuer, essayez : {next_action_title}" if next_action_title else "Prenez une pause et revenez quand vous êtes prêt(e).",
        "next_action_id": next_action_id,
        "next_action_title": next_action_title,
    }

# ============== AI WEEKLY ANALYSIS ROUTE ==============

@api_router.get("/ai/weekly-analysis")
@limiter.limit("10/minute")
async def get_weekly_analysis(request: Request, user: dict = Depends(get_current_user)):
    """Get AI-powered weekly progress analysis"""
    user_context = await build_user_context(user)

    all_sessions = await db.user_sessions_history.find(
        {"user_id": user["user_id"], "completed": True},
        {"_id": 0}
    ).sort("started_at", -1).to_list(100)

    if len(all_sessions) < 2:
        return {
            "summary": "Pas encore assez de données pour une analyse complète. Continuez vos micro-actions !",
            "strengths": [],
            "improvement_areas": [],
            "trends": "Commencez à accumuler des sessions pour voir vos tendances.",
            "personalized_tips": ["Essayez de faire au moins une micro-action par jour pour créer une habitude."]
        }

    category_counts = {}
    total_duration = 0
    for s in all_sessions:
        cat = s.get("category", "unknown")
        category_counts[cat] = category_counts.get(cat, 0) + 1
        total_duration += s.get("actual_duration", 0)

    categories_fr = {
        "learning": "apprentissage", "productivity": "productivité", "well_being": "bien-être",
        "creativity": "créativité", "fitness": "forme physique", "mindfulness": "pleine conscience",
        "leadership": "leadership", "finance": "finance", "relations": "relations",
        "mental_health": "santé mentale", "entrepreneurship": "entrepreneuriat"
    }
    cat_summary = ", ".join([f"{categories_fr.get(k, k)}: {v} sessions" for k, v in category_counts.items()])

    prompt = f"""{user_context}

Statistiques de l'utilisateur:
- Total sessions: {len(all_sessions)}
- Temps total: {total_duration} minutes
- Répartition: {cat_summary}
- Streak: {user.get('streak_days', 0)} jours

Analyse les progrès et génère un bilan personnalisé.
Réponds en JSON:
{{
    "summary": "Résumé global (2-3 phrases)",
    "strengths": ["Point fort 1", "Point fort 2"],
    "improvement_areas": ["Axe d'amélioration 1"],
    "trends": "Description des tendances (1-2 phrases)",
    "personalized_tips": ["Conseil personnalisé 1", "Conseil personnalisé 2"]
}}"""

    ai_response = await call_ai(f"analysis_{user['user_id']}", AI_SYSTEM_MESSAGE, prompt, model=get_ai_model(user))
    ai_result = parse_ai_json(ai_response)

    await track_event(db, user["user_id"], "ai_weekly_analysis_generated", {
        "total_sessions": len(all_sessions),
        "total_duration": total_duration,
        "ai_success": ai_result is not None,
    })

    if ai_result:
        return {
            "summary": ai_result.get("summary", "Bonne progression globale."),
            "strengths": ai_result.get("strengths", []),
            "improvement_areas": ai_result.get("improvement_areas", []),
            "trends": ai_result.get("trends", ""),
            "personalized_tips": ai_result.get("personalized_tips", [])
        }

    return {
        "summary": f"Vous avez complété {len(all_sessions)} sessions pour un total de {total_duration} minutes. Continuez ainsi !",
        "strengths": [f"Régularité avec {user.get('streak_days', 0)} jours de streak"],
        "improvement_areas": ["Diversifiez vos catégories d'actions"],
        "trends": f"Vous investissez en moyenne {total_duration // max(len(all_sessions), 1)} min par session.",
        "personalized_tips": ["Essayez une nouvelle catégorie cette semaine."]
    }

# ============== AI STREAK CHECK ROUTE ==============

@api_router.post("/ai/streak-check")
@limiter.limit("10/minute")
async def check_streak_risk(request: Request, user: dict = Depends(get_current_user)):
    """Check if user's streak is at risk and send AI notification"""
    streak = user.get("streak_days", 0)
    if streak == 0:
        return {"at_risk": False, "notification_sent": False, "message": None}

    last_session_date = user.get("last_session_date")
    today = datetime.now(timezone.utc).date()

    if last_session_date:
        if isinstance(last_session_date, str):
            last_date = datetime.fromisoformat(last_session_date).date()
        else:
            last_date = last_session_date.date() if hasattr(last_session_date, 'date') else last_session_date

        if last_date == today:
            return {"at_risk": False, "notification_sent": False, "message": None}

        if last_date == today - timedelta(days=1):
            user_context = await build_user_context(user)
            prompt = f"""{user_context}

Le streak de {streak} jours de l'utilisateur est en danger ! Il n'a pas encore fait de session aujourd'hui.
Génère un message d'alerte motivant et court pour l'encourager à maintenir son streak.
Réponds en JSON: {{"title": "Titre court", "message": "Message motivant (1-2 phrases)"}}"""

            ai_response = await call_ai(f"streak_alert_{user['user_id']}", AI_SYSTEM_MESSAGE, prompt, model=get_ai_model(user))
            ai_result = parse_ai_json(ai_response)

            title = ai_result.get("title", f"Streak de {streak}j en danger !") if ai_result else f"Streak de {streak}j en danger !"
            message = ai_result.get("message", f"Faites une micro-action de 2 minutes pour maintenir votre streak de {streak} jours !") if ai_result else f"Faites une micro-action de 2 minutes pour maintenir votre streak de {streak} jours !"

            existing = await db.notifications.find_one({
                "user_id": user["user_id"],
                "type": "streak_alert",
                "created_at": {"$gte": datetime.combine(today, datetime.min.time()).isoformat()}
            })

            if not existing:
                notification = {
                    "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
                    "user_id": user["user_id"],
                    "type": "streak_alert",
                    "title": title,
                    "message": message,
                    "icon": "flame",
                    "read": False,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                await db.notifications.insert_one(notification)
                await track_event(db, user["user_id"], "ai_streak_check_served", {
                    "streak_days": streak,
                    "at_risk": True,
                    "notification_sent": True,
                })
                return {"at_risk": True, "notification_sent": True, "message": message}

            return {"at_risk": True, "notification_sent": False, "message": message}

    return {"at_risk": False, "notification_sent": False, "message": None}

# ============== AI CUSTOM ACTION ROUTES ==============

@api_router.post("/ai/create-action")
@limiter.limit("10/minute")
async def create_custom_action(
    request: Request,
    action_req: CustomActionRequest,
    user: dict = Depends(get_current_user)
):
    """Create a custom micro-action using AI"""
    user_context = await build_user_context(user)

    cat_hint = f"\nCatégorie préférée: {action_req.preferred_category}" if action_req.preferred_category else ""
    dur_hint = f"\nDurée souhaitée: {action_req.preferred_duration} minutes" if action_req.preferred_duration else ""

    prompt = f"""{user_context}

L'utilisateur souhaite créer une micro-action personnalisée.
Sa description: "{action_req.description}"{cat_hint}{dur_hint}

Génère une micro-action complète et structurée.
Réponds en JSON:
{{
    "title": "Titre court et accrocheur",
    "description": "Description en 1-2 phrases",
    "category": "learning|productivity|well_being",
    "duration_min": 2,
    "duration_max": 10,
    "energy_level": "low|medium|high",
    "instructions": ["Étape 1", "Étape 2", "Étape 3", "Étape 4"],
    "icon": "sparkles"
}}"""

    ai_response = await call_ai(f"create_action_{user['user_id']}", AI_SYSTEM_MESSAGE, prompt, model=get_ai_model(user))
    ai_result = parse_ai_json(ai_response)

    action_id = f"custom_{uuid.uuid4().hex[:12]}"

    if ai_result:
        action = {
            "action_id": action_id,
            "title": ai_result.get("title", action_req.description[:50]),
            "description": ai_result.get("description", action_req.description),
            "category": ai_result.get("category", action_req.preferred_category or "productivity"),
            "duration_min": ai_result.get("duration_min", 2),
            "duration_max": ai_result.get("duration_max", action_req.preferred_duration or 10),
            "energy_level": ai_result.get("energy_level", "medium"),
            "instructions": ai_result.get("instructions", [action_req.description]),
            "icon": ai_result.get("icon", "sparkles"),
            "is_premium": False,
            "is_custom": True,
            "created_by": user["user_id"],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    else:
        action = {
            "action_id": action_id,
            "title": action_req.description[:50],
            "description": action_req.description,
            "category": action_req.preferred_category or "productivity",
            "duration_min": 2,
            "duration_max": action_req.preferred_duration or 10,
            "energy_level": "medium",
            "instructions": [action_req.description],
            "icon": "sparkles",
            "is_premium": False,
            "is_custom": True,
            "created_by": user["user_id"],
            "created_at": datetime.now(timezone.utc).isoformat()
        }

    doc = {**action}
    await db.user_custom_actions.insert_one(doc)

    await track_event(db, user["user_id"], "ai_action_created", {
        "action_id": action_id,
        "category": action["category"],
        "ai_success": ai_result is not None,
    })

    return {"action": action}

# ============== SESSION TRACKING ROUTES ==============

@api_router.post("/sessions/start")
async def start_session(
    session_data: SessionStart,
    user: dict = Depends(get_current_user)
):
    """Start a micro-action session"""
    action = await db.micro_actions.find_one({"action_id": session_data.action_id}, {"_id": 0})
    if not action:
        # Fallback to custom actions
        action = await db.user_custom_actions.find_one(
            {"action_id": session_data.action_id, "created_by": user["user_id"]},
            {"_id": 0}
        )
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    
    # Check premium access
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
    
    await db.user_sessions_history.insert_one(session_doc)

    await track_event(db, user["user_id"], "action_started", {
        "session_id": session_id,
        "action_id": session_data.action_id,
        "category": action["category"],
        "action_title": action["title"],
    })

    # Feedback loop: user clicked on this action
    await record_signal(db, user["user_id"], session_data.action_id, "click")

    return {
        "session_id": session_id,
        "action": action,
        "started_at": session_doc["started_at"]
    }

@api_router.post("/sessions/complete")
async def complete_session(
    completion: SessionComplete,
    user: dict = Depends(get_current_user)
):
    """Complete a micro-action session and update stats"""
    session = await db.user_sessions_history.find_one(
        {"session_id": completion.session_id, "user_id": user["user_id"]},
        {"_id": 0}
    )
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Update session
    await db.user_sessions_history.update_one(
        {"session_id": completion.session_id},
        {"$set": {
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "actual_duration": completion.actual_duration,
            "completed": completion.completed,
            "notes": completion.notes
        }}
    )
    
    event_type = "action_completed" if completion.completed else "action_abandoned"
    await track_event(db, user["user_id"], event_type, {
        "session_id": completion.session_id,
        "category": session.get("category"),
        "action_title": session.get("action_title"),
        "actual_duration": completion.actual_duration,
    })

    # Feedback loop: completion or abandonment signal
    action_id = session.get("action_id")
    if action_id:
        signal = "completion" if completion.completed else "abandonment"
        await record_signal(db, user["user_id"], action_id, signal)

    if completion.completed:
        # Update user stats
        user_doc = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0})

        # Calculate streak
        today = datetime.now(timezone.utc).date()
        last_session = user_doc.get("last_session_date")

        new_streak = user_doc.get("streak_days", 0)
        streak_shield_used = False
        if last_session:
            if isinstance(last_session, str):
                last_date = datetime.fromisoformat(last_session).date()
            else:
                last_date = last_session.date() if hasattr(last_session, 'date') else last_session

            if last_date == today - timedelta(days=1):
                new_streak += 1
            elif last_date != today:
                # Streak would break — check for Premium Streak Shield
                gap_days = (today - last_date).days
                if (user_doc.get("subscription_tier") == "premium"
                    and gap_days <= 2):
                    # Check if shield is available (once per 7 days)
                    shield_used_at = user_doc.get("streak_shield_used_at")
                    shield_available = True
                    if shield_used_at:
                        if isinstance(shield_used_at, str):
                            shield_date = datetime.fromisoformat(shield_used_at).date()
                        else:
                            shield_date = shield_used_at.date() if hasattr(shield_used_at, 'date') else shield_used_at
                        shield_available = (today - shield_date).days >= 7

                    if shield_available:
                        # Shield activated — preserve streak
                        new_streak += 1
                        streak_shield_used = True
                        await db.users.update_one(
                            {"user_id": user["user_id"]},
                            {"$set": {"streak_shield_used_at": today.isoformat()},
                             "$inc": {"streak_shield_count": 1}}
                        )
                        logger.info(f"Streak shield activated for user {user['user_id']}")
                    else:
                        new_streak = 1
                else:
                    new_streak = 1
        else:
            new_streak = 1

        await db.users.update_one(
            {"user_id": user["user_id"]},
            {
                "$inc": {"total_time_invested": completion.actual_duration},
                "$set": {
                    "streak_days": new_streak,
                    "last_session_date": today.isoformat()
                }
            }
        )
        
        # Check for new badges
        new_badges = await check_and_award_badges(user["user_id"])
        
        # Create notification for new badges
        for badge in new_badges:
            notification = {
                "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
                "user_id": user["user_id"],
                "type": "badge_earned",
                "title": f"Nouveau badge : {badge['name']}",
                "message": f"Félicitations ! Vous avez obtenu le badge {badge['name']}",
                "icon": badge["icon"],
                "read": False,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.notifications.insert_one(notification)
        
        return {
            "message": "Session completed!",
            "time_added": completion.actual_duration,
            "new_streak": new_streak,
            "total_time": user_doc.get("total_time_invested", 0) + completion.actual_duration,
            "new_badges": new_badges
        }
    
    return {"message": "Session recorded"}

@api_router.get("/stats")
async def get_user_stats(user: dict = Depends(get_current_user)):
    """Get user progress statistics"""
    # Get sessions by category
    pipeline = [
        {"$match": {"user_id": user["user_id"], "completed": True}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}, "total_time": {"$sum": "$actual_duration"}}}
    ]
    category_stats = await db.user_sessions_history.aggregate(pipeline).to_list(10)
    
    sessions_by_category = {}
    time_by_category = {}
    for stat in category_stats:
        sessions_by_category[stat["_id"]] = stat["count"]
        time_by_category[stat["_id"]] = stat["total_time"]
    
    # Get recent sessions
    recent = await db.user_sessions_history.find(
        {"user_id": user["user_id"], "completed": True},
        {"_id": 0}
    ).sort("completed_at", -1).limit(10).to_list(10)
    
    # Get total sessions count
    total_sessions = await db.user_sessions_history.count_documents(
        {"user_id": user["user_id"], "completed": True}
    )
    
    return {
        "total_time_invested": user.get("total_time_invested", 0),
        "total_sessions": total_sessions,
        "streak_days": user.get("streak_days", 0),
        "sessions_by_category": sessions_by_category,
        "time_by_category": time_by_category,
        "recent_sessions": recent
    }

# ============== STRIPE PAYMENT ROUTES ==============

SUBSCRIPTION_PRICE = 6.99  # EUR

@api_router.post("/payments/checkout")
async def create_checkout(
    checkout_data: CheckoutRequest,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """Create Stripe checkout session for Premium subscription (recurring monthly)"""
    stripe_key = os.environ.get('STRIPE_API_KEY')
    if not stripe_key:
        raise HTTPException(status_code=500, detail="Payment service not configured")

    success_url = f"{checkout_data.origin_url}/pricing?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{checkout_data.origin_url}/pricing"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client_http:
            resp = await client_http.post(
                "https://api.stripe.com/v1/checkout/sessions",
                headers={"Authorization": f"Bearer {stripe_key}"},
                data={
                    "mode": "subscription",
                    "success_url": success_url,
                    "cancel_url": cancel_url,
                    "customer_email": user["email"],
                    "line_items[0][price_data][currency]": "eur",
                    "line_items[0][price_data][product_data][name]": "InFinea Premium",
                    "line_items[0][price_data][unit_amount]": int(SUBSCRIPTION_PRICE * 100),
                    "line_items[0][price_data][recurring][interval]": "month",
                    "line_items[0][quantity]": "1",
                    "metadata[user_id]": user["user_id"],
                    "metadata[email]": user["email"],
                    "metadata[plan]": "premium",
                    "subscription_data[metadata][user_id]": user["user_id"],
                }
            )
            resp.raise_for_status()
            session = resp.json()
    except Exception as e:
        logger.error(f"Stripe checkout error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")

    await db.payment_transactions.insert_one({
        "transaction_id": f"txn_{uuid.uuid4().hex[:12]}",
        "session_id": session["id"],
        "user_id": user["user_id"],
        "email": user["email"],
        "amount": SUBSCRIPTION_PRICE,
        "currency": "eur",
        "plan": "premium",
        "payment_status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    })

    return {"url": session["url"], "session_id": session["id"]}

@api_router.get("/payments/status/{session_id}")
async def get_payment_status(
    session_id: str,
    user: dict = Depends(get_current_user)
):
    """Check payment status and upgrade user if successful"""
    stripe_key = os.environ.get('STRIPE_API_KEY')
    if not stripe_key:
        raise HTTPException(status_code=500, detail="Payment service not configured")

    try:
        async with httpx.AsyncClient(timeout=15.0) as client_http:
            resp = await client_http.get(
                f"https://api.stripe.com/v1/checkout/sessions/{session_id}",
                headers={"Authorization": f"Bearer {stripe_key}"}
            )
            resp.raise_for_status()
            status = resp.json()

        payment_status = status.get("payment_status", "unpaid")
        subscription_id = status.get("subscription")
        customer_id = status.get("customer")

        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": {
                "payment_status": payment_status,
                "status": status.get("status"),
                "subscription_id": subscription_id,
                "customer_id": customer_id,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )

        if payment_status == "paid":
            txn = await db.payment_transactions.find_one(
                {"session_id": session_id, "processed": True}, {"_id": 0}
            )
            if not txn:
                await db.users.update_one(
                    {"user_id": user["user_id"]},
                    {"$set": {
                        "subscription_tier": "premium",
                        "subscription_started_at": datetime.now(timezone.utc).isoformat(),
                        "stripe_subscription_id": subscription_id,
                        "stripe_customer_id": customer_id,
                    }}
                )
                await db.payment_transactions.update_one(
                    {"session_id": session_id},
                    {"$set": {"processed": True}}
                )

        return {
            "status": status.get("status"),
            "payment_status": payment_status,
            "amount": (status.get("amount_total", 0) or 0) / 100,
            "currency": status.get("currency", "eur")
        }
    except Exception as e:
        logger.error(f"Payment status error: {e}")
        raise HTTPException(status_code=400, detail="Failed to get payment status")

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks for subscription lifecycle"""
    stripe_key = os.environ.get('STRIPE_API_KEY')
    if not stripe_key:
        return {"status": "error", "message": "Not configured"}

    body = await request.body()

    try:
        event = json.loads(body)
        event_type = event.get("type", "")
        event_data = event.get("data", {}).get("object", {})

        if event_type == "checkout.session.completed":
            if event_data.get("payment_status") == "paid":
                user_id = event_data.get("metadata", {}).get("user_id")
                subscription_id = event_data.get("subscription")
                customer_id = event_data.get("customer")
                if user_id:
                    await db.users.update_one(
                        {"user_id": user_id},
                        {"$set": {
                            "subscription_tier": "premium",
                            "subscription_started_at": datetime.now(timezone.utc).isoformat(),
                            "stripe_subscription_id": subscription_id,
                            "stripe_customer_id": customer_id,
                        }}
                    )

        elif event_type == "invoice.payment_succeeded":
            subscription_id = event_data.get("subscription")
            if subscription_id:
                await db.users.update_one(
                    {"stripe_subscription_id": subscription_id},
                    {"$set": {"subscription_tier": "premium"}}
                )

        elif event_type == "invoice.payment_failed":
            subscription_id = event_data.get("subscription")
            if subscription_id:
                logger.warning(f"Payment failed for subscription {subscription_id}")

        elif event_type == "customer.subscription.deleted":
            subscription_id = event_data.get("id")
            if subscription_id:
                await db.users.update_one(
                    {"stripe_subscription_id": subscription_id},
                    {"$set": {"subscription_tier": "free", "stripe_subscription_id": None}}
                )
                logger.info(f"Subscription {subscription_id} cancelled — user downgraded to free")

        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error"}

@api_router.post("/premium/portal")
async def create_customer_portal(
    checkout_data: CheckoutRequest,
    user: dict = Depends(get_current_user)
):
    """Create Stripe Customer Portal session for subscription management"""
    stripe_key = os.environ.get('STRIPE_API_KEY')
    if not stripe_key:
        raise HTTPException(status_code=500, detail="Payment service not configured")

    customer_id = user.get("stripe_customer_id")
    if not customer_id:
        raise HTTPException(status_code=400, detail="No active subscription found")

    try:
        async with httpx.AsyncClient(timeout=15.0) as client_http:
            resp = await client_http.post(
                "https://api.stripe.com/v1/billing_portal/sessions",
                headers={"Authorization": f"Bearer {stripe_key}"},
                data={
                    "customer": customer_id,
                    "return_url": f"{checkout_data.origin_url}/pricing",
                }
            )
            resp.raise_for_status()
            portal = resp.json()
        return {"url": portal["url"]}
    except Exception as e:
        logger.error(f"Portal creation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create portal session")

# ============== FREE PREMIUM ACTIVATION (temporary — remove when Stripe is ready) ==============

@api_router.post("/premium/activate-free")
async def activate_premium_free(user: dict = Depends(get_current_user)):
    """Temporary route: activate premium for any logged-in user without payment"""
    if user.get("subscription_tier") == "premium":
        return {"status": "already_premium", "message": "Vous êtes déjà Premium"}
    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {
            "subscription_tier": "premium",
            "subscription_started_at": datetime.now(timezone.utc).isoformat(),
        }}
    )
    logger.info(f"Free premium activated for user {user['user_id']} ({user.get('email')})")
    return {"status": "success", "message": "Premium activé avec succès"}

# ============== PROMO CODE ROUTES ==============

@api_router.post("/promo/redeem")
async def redeem_promo_code(
    promo_data: PromoCodeRequest,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """Redeem admin promo code for permanent Premium access (bypasses Stripe)"""
    client_ip = request.headers.get("x-forwarded-for", "unknown").split(",")[0].strip()

    # 1. Already premium?
    if user.get("subscription_tier") == "premium":
        logger.warning(f"Promo attempt by already-premium user {user['user_id']} from IP {client_ip}")
        raise HTTPException(status_code=400, detail="Vous êtes déjà Premium")

    # 2. Admin check via ADMIN_EMAILS env var
    admin_emails_raw = os.environ.get("ADMIN_EMAILS", "")
    admin_emails = [e.strip().lower() for e in admin_emails_raw.split(",") if e.strip()]
    if not admin_emails or user.get("email", "").lower() not in admin_emails:
        logger.warning(f"Promo attempt by non-admin user {user['user_id']} ({user.get('email')}) from IP {client_ip}")
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")

    # 3. Validate promo code against bcrypt hash
    promo_hash = os.environ.get("PROMO_CODE_HASH")
    if not promo_hash:
        logger.error("PROMO_CODE_HASH not configured in environment")
        raise HTTPException(status_code=500, detail="Code promo non configuré")

    if not bcrypt.checkpw(promo_data.code.encode(), promo_hash.encode()):
        logger.warning(f"Invalid promo code attempt by user {user['user_id']} from IP {client_ip}")
        raise HTTPException(status_code=400, detail="Code promo invalide")

    # 4. Upgrade to permanent premium (no Stripe fields)
    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {
            "subscription_tier": "premium",
            "subscription_started_at": datetime.now(timezone.utc).isoformat(),
            "promo_activated": True,
        }}
    )

    # 5. Audit log
    await db.promo_logs.insert_one({
        "user_id": user["user_id"],
        "email": user["email"],
        "redeemed_at": datetime.now(timezone.utc).isoformat(),
        "ip_address": client_ip,
    })

    logger.info(f"Promo code redeemed by admin {user['user_id']} ({user['email']}) from IP {client_ip}")

    return {"status": "success", "message": "Premium activé avec succès"}

# ============== ACTION GENERATION (admin) ==============

@api_router.post("/admin/generate-actions")
async def trigger_action_generation(user: dict = Depends(get_current_user)):
    """Admin-only: trigger daily action generation manually."""
    admin_emails = [e.strip().lower() for e in os.environ.get("ADMIN_EMAILS", "").split(",") if e.strip()]
    if user.get("email", "").lower() not in admin_emails:
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")

    from services.action_generator import check_and_generate_daily_actions
    result = await check_and_generate_daily_actions(db)
    return result

@api_router.get("/admin/actions-stats")
async def get_actions_stats(user: dict = Depends(get_current_user)):
    """Get action library statistics (count per category, generation logs)."""
    pipeline = [
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    category_counts = await db.micro_actions.aggregate(pipeline).to_list(50)

    total = sum(c["count"] for c in category_counts)

    # Recent generation logs
    recent_logs = await db.generation_logs.find(
        {}, {"_id": 0}
    ).sort("generated_at", -1).to_list(30)

    return {
        "total_actions": total,
        "by_category": {c["_id"]: c["count"] for c in category_counts},
        "recent_generations": recent_logs,
    }

@api_router.get("/admin/events")
async def get_event_stats(user: dict = Depends(get_current_user)):
    """Admin-only: get event tracking stats to verify instrumentation works."""
    admin_emails = [e.strip().lower() for e in os.environ.get("ADMIN_EMAILS", "").split(",") if e.strip()]
    if user.get("email", "").lower() not in admin_emails:
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")

    # Count by event_type
    pipeline = [
        {"$group": {"_id": "$event_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    type_counts = await db.event_log.aggregate(pipeline).to_list(50)

    # Total events
    total = sum(c["count"] for c in type_counts)

    # Last 20 events (most recent first)
    recent = await db.event_log.find(
        {}, {"_id": 0}
    ).sort("timestamp", -1).to_list(20)

    # Convert datetime to string for JSON serialization
    for event in recent:
        if hasattr(event.get("timestamp"), "isoformat"):
            event["timestamp"] = event["timestamp"].isoformat()

    return {
        "total_events": total,
        "by_type": {c["_id"]: c["count"] for c in type_counts},
        "recent_events": recent,
    }

@api_router.get("/admin/features")
async def get_feature_stats(
    user: dict = Depends(get_current_user),
    user_id: Optional[str] = None,
):
    """Admin-only: get feature store stats or a specific user's features."""
    admin_emails = [e.strip().lower() for e in os.environ.get("ADMIN_EMAILS", "").split(",") if e.strip()]
    if user.get("email", "").lower() not in admin_emails:
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")

    # If a specific user_id is requested
    if user_id:
        doc = await db.user_features.find_one({"user_id": user_id}, {"_id": 0})
        return {"user_features": doc}

    # Global stats
    total_users = await db.user_features.count_documents({})

    # Last computation log
    last_log = await db.feature_computation_logs.find_one(
        {}, {"_id": 0}, sort=[("computed_at", -1)]
    )

    # 5 sample user features (most recently computed)
    samples = await db.user_features.find(
        {}, {"_id": 0}
    ).sort("computed_at", -1).to_list(5)

    return {
        "total_users_with_features": total_users,
        "last_computation": last_log,
        "sample_features": samples,
    }

@api_router.post("/admin/compute-features")
async def trigger_feature_computation(user: dict = Depends(get_current_user)):
    """Admin-only: trigger feature computation manually."""
    admin_emails = [e.strip().lower() for e in os.environ.get("ADMIN_EMAILS", "").split(",") if e.strip()]
    if user.get("email", "").lower() not in admin_emails:
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")

    from services.feature_calculator import compute_all_users_features
    result = await compute_all_users_features(db)
    return result

# ============== SEED DATA ==============

async def seed_micro_actions():
    """Seed database with micro-actions from seed_actions.py + premium actions.
    Only inserts actions for categories that are missing — never deletes existing data."""
    from seed_actions import SEED_ACTIONS
    try:
        from seed_premium_actions import PREMIUM_ACTIONS
    except ImportError:
        PREMIUM_ACTIONS = []

    all_seed_actions = SEED_ACTIONS + PREMIUM_ACTIONS

    # Check which categories already exist in DB
    existing_categories = await db.micro_actions.distinct("category")
    needed_categories = {a["category"] for a in all_seed_actions} - set(existing_categories)

    if not needed_categories and existing_categories:
        logger.info(f"All seed categories already present: {existing_categories}")
        return {"message": "All categories already seeded"}

    if not existing_categories:
        # Fresh DB — insert everything
        await db.micro_actions.insert_many(all_seed_actions)
        logger.info(f"Fresh seed: inserted {len(all_seed_actions)} actions")
    else:
        # Only insert actions for missing categories
        actions_to_add = [a for a in all_seed_actions if a["category"] in needed_categories]
        if actions_to_add:
            await db.micro_actions.insert_many(actions_to_add)
            logger.info(f"Partial seed: inserted {len(actions_to_add)} actions for categories {needed_categories}")

    return {"message": f"Seeded actions for categories: {needed_categories or 'all'}"}

# ============== GOOGLE CALENDAR INTEGRATION ==============

from integrations.google_calendar import (
    generate_auth_url, exchange_code_for_tokens, encrypt_tokens,
    refresh_access_token, get_calendar_events, get_user_calendars,
    GOOGLE_CLIENT_ID
)
from integrations.encryption import encrypt_token, decrypt_token
from services.slot_detector import detect_free_slots, match_action_to_slot, DEFAULT_SETTINGS
from services.smart_notifications import (
    schedule_slot_notifications, cleanup_old_slots, get_pending_notifications
)

class SlotSettings(BaseModel):
    slot_detection_enabled: bool = True
    min_slot_duration: int = 5
    max_slot_duration: int = 20
    detection_window_start: str = "09:00"
    detection_window_end: str = "18:00"
    excluded_keywords: List[str] = ["focus", "deep work", "lunch", "break"]
    advance_notification_minutes: int = 5
    preferred_categories_by_time: Dict[str, str] = {
        "morning": "learning",
        "afternoon": "productivity",
        "evening": "well_being"
    }

# ============== INTEGRATION HUB CONFIG ==============

INTEGRATION_CONFIGS = {
    "google_calendar": {
        "name": "Google Calendar",
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "scopes": "https://www.googleapis.com/auth/calendar.events",
        "env_client_id": "GOOGLE_CLIENT_ID",
        "env_client_secret": "GOOGLE_CLIENT_SECRET",
    },
    "notion": {
        "name": "Notion",
        "auth_url": "https://api.notion.com/v1/oauth/authorize",
        "token_url": "https://api.notion.com/v1/oauth/token",
        "scopes": "",
        "env_client_id": "NOTION_CLIENT_ID",
        "env_client_secret": "NOTION_CLIENT_SECRET",
    },
    "todoist": {
        "name": "Todoist",
        "auth_url": "https://todoist.com/oauth/authorize",
        "token_url": "https://todoist.com/oauth/access_token",
        "scopes": "data:read_write",
        "env_client_id": "TODOIST_CLIENT_ID",
        "env_client_secret": "TODOIST_CLIENT_SECRET",
    },
    "slack": {
        "name": "Slack",
        "auth_url": "https://slack.com/oauth/v2/authorize",
        "token_url": "https://slack.com/api/oauth.v2.access",
        "scopes": "chat:write,users:read",
        "env_client_id": "SLACK_CLIENT_ID",
        "env_client_secret": "SLACK_CLIENT_SECRET",
    },
}

HUB_FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")

# ============== INTEGRATION HUB ROUTES ==============

@api_router.get("/integrations")
async def get_integrations(user: dict = Depends(get_current_user)):
    """Get user's connected integrations with status for all services."""
    integrations = await db.user_integrations.find(
        {"user_id": user["user_id"]},
        {"_id": 0, "access_token": 0, "refresh_token": 0}
    ).to_list(10)

    # Build response with connection status for all services
    result = {}
    # Support both "provider" (main legacy) and "service" (hub) field names
    connected_map = {}
    for i in integrations:
        key = i.get("service") or i.get("provider")
        if key:
            connected_map[key] = i

    for service_key, config in INTEGRATION_CONFIGS.items():
        client_id = os.environ.get(config["env_client_id"])
        connected = connected_map.get(service_key)
        # Available if OAuth configured, token connect supported, or URL connect (calendars via iCal)
        supports_url = service_key in ("google_calendar",) and ICAL_AVAILABLE
        is_available = bool(client_id) or service_key in TOKEN_CONNECT_VALIDATORS or supports_url
        result[service_key] = {
            "name": config["name"],
            "connected": bool(connected),
            "connected_at": connected.get("connected_at") or connected.get("created_at") if connected else None,
            "account_name": connected.get("account_name") if connected else None,
            "available": is_available,
            "supports_token": service_key in TOKEN_CONNECT_VALIDATORS,
            "supports_url": supports_url,
            "sync_enabled": connected.get("sync_enabled", connected.get("enabled", False)) if connected else False,
        }

    # iCal is non-OAuth, always available
    ical_connected = connected_map.get("ical")
    result["ical"] = {
        "name": "iCal",
        "connected": bool(ical_connected),
        "connected_at": ical_connected.get("connected_at") if ical_connected else None,
        "account_name": ical_connected.get("account_name") if ical_connected else None,
        "available": ICAL_AVAILABLE,
        "sync_enabled": ical_connected.get("sync_enabled", False) if ical_connected else False,
        "type": "url",
    }

    return result

@api_router.get("/integrations/connect/{service}")
async def connect_integration(service: str, request: Request, user: dict = Depends(get_current_user)):
    """Initiate OAuth flow for a service — returns the authorization URL."""
    if service not in INTEGRATION_CONFIGS:
        raise HTTPException(status_code=400, detail=f"Unknown service: {service}")

    config = INTEGRATION_CONFIGS[service]
    client_id = os.environ.get(config["env_client_id"])
    if not client_id:
        raise HTTPException(status_code=503, detail=f"{config['name']} integration not configured")

    base_state = f"{user['user_id']}:{uuid.uuid4().hex[:16]}"
    backend_url = os.environ.get("BACKEND_URL", "https://infinea-api.onrender.com")

    if service == "google_calendar":
        # Reuse the login callback URI (already registered in Google Console)
        state = f"gcal_integrate:{base_state}"
        redirect_uri = f"{backend_url}/api/auth/google/callback"
    else:
        state = base_state
        redirect_uri = f"{backend_url}/api/integrations/callback/{service}"

    await db.integration_states.insert_one({
        "state": state,
        "user_id": user["user_id"],
        "service": service,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    })

    params = {"client_id": client_id, "state": state}

    if service == "google_calendar":
        params.update({
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": config["scopes"],
            "access_type": "offline",
            "prompt": "consent",
        })
    elif service == "notion":
        params.update({
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "owner": "user",
        })
    elif service == "todoist":
        params.update({"scope": config["scopes"]})
    elif service == "slack":
        params.update({
            "scope": config["scopes"],
            "redirect_uri": redirect_uri,
        })

    auth_url = f"{config['auth_url']}?{urllib.parse.urlencode(params)}"
    return {"auth_url": auth_url}

@api_router.get("/integrations/callback/{service}")
async def integration_callback(service: str, code: str = "", state: str = "", error: str = ""):
    """OAuth callback handler — exchanges code for tokens, redirects to frontend."""
    if error:
        return RedirectResponse(f"{HUB_FRONTEND_URL}/integrations?error={urllib.parse.quote(error)}&service={service}")

    if service not in INTEGRATION_CONFIGS:
        return RedirectResponse(f"{HUB_FRONTEND_URL}/integrations?error=unknown_service")

    state_doc = await db.integration_states.find_one_and_delete({"state": state, "service": service})
    if not state_doc:
        return RedirectResponse(f"{HUB_FRONTEND_URL}/integrations?error=invalid_state&service={service}")

    expires_at = datetime.fromisoformat(state_doc["expires_at"])
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        return RedirectResponse(f"{HUB_FRONTEND_URL}/integrations?error=expired&service={service}")

    user_id = state_doc["user_id"]
    config = INTEGRATION_CONFIGS[service]
    client_id = os.environ.get(config["env_client_id"])
    client_secret = os.environ.get(config["env_client_secret"])

    if not client_id or not client_secret:
        return RedirectResponse(f"{HUB_FRONTEND_URL}/integrations?error=not_configured&service={service}")

    try:
        backend_url = os.environ.get("BACKEND_URL", "https://infinea-api.onrender.com")
        redirect_uri = f"{backend_url.rstrip('/')}/api/integrations/callback/{service}"

        async with httpx.AsyncClient() as http_client:
            access_token = None
            refresh_token = None
            expires_in = None
            account_name = config["name"]

            if service == "google_calendar":
                token_resp = await http_client.post(config["token_url"], data={
                    "client_id": client_id, "client_secret": client_secret,
                    "code": code, "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                })
                token_data = token_resp.json()
                access_token = token_data.get("access_token")
                refresh_token = token_data.get("refresh_token")
                expires_in = token_data.get("expires_in", 3600)
                try:
                    info_resp = await http_client.get(
                        "https://www.googleapis.com/oauth2/v2/userinfo",
                        headers={"Authorization": f"Bearer {access_token}"}
                    )
                    if info_resp.status_code == 200:
                        account_name = info_resp.json().get("email", "Google Calendar")
                except Exception:
                    pass

            elif service == "notion":
                auth_header = httpx.BasicAuth(client_id, client_secret)
                token_resp = await http_client.post(config["token_url"], json={
                    "grant_type": "authorization_code", "code": code,
                    "redirect_uri": redirect_uri,
                }, auth=auth_header, headers={"Notion-Version": "2022-06-28"})
                token_data = token_resp.json()
                access_token = token_data.get("access_token")
                account_name = token_data.get("workspace_name", "Notion")

            elif service == "todoist":
                token_resp = await http_client.post(config["token_url"], data={
                    "client_id": client_id, "client_secret": client_secret, "code": code,
                })
                token_data = token_resp.json()
                access_token = token_data.get("access_token")
                account_name = "Todoist"

            elif service == "slack":
                token_resp = await http_client.post(config["token_url"], data={
                    "client_id": client_id, "client_secret": client_secret,
                    "code": code, "redirect_uri": redirect_uri,
                })
                token_data = token_resp.json()
                access_token = token_data.get("access_token")
                if not access_token:
                    access_token = token_data.get("authed_user", {}).get("access_token")
                account_name = token_data.get("team", {}).get("name", "Slack")

            if not access_token:
                logger.error(f"Integration {service} token exchange failed: {token_data}")
                return RedirectResponse(f"{HUB_FRONTEND_URL}/integrations?error=token_failed&service={service}")

            # Encrypt tokens before storage
            encrypted_access = encrypt_token(access_token)
            encrypted_refresh = encrypt_token(refresh_token) if refresh_token else None

            integration_doc = {
                "user_id": user_id,
                "service": service,
                "provider": service,  # backward compat with existing Google Calendar code
                "access_token": encrypted_access,
                "refresh_token": encrypted_refresh,
                "expires_in": expires_in,
                "token_expires_at": (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).isoformat() if expires_in else None,
                "token_obtained_at": datetime.now(timezone.utc).isoformat(),
                "account_name": account_name,
                "connected_at": datetime.now(timezone.utc).isoformat(),
                "enabled": True,
                "sync_enabled": True,
                "integration_id": f"int_{uuid.uuid4().hex[:12]}",
            }

            await db.user_integrations.delete_many({"user_id": user_id, "service": service})
            await db.user_integrations.delete_many({"user_id": user_id, "provider": service})
            await db.user_integrations.insert_one(integration_doc)

            # For Google Calendar, also fetch calendars metadata
            if service == "google_calendar":
                try:
                    calendars = await get_user_calendars(encrypted_access)
                    primary_calendar = next((c for c in calendars if c.get("primary")), None)
                    await db.user_integrations.update_one(
                        {"integration_id": integration_doc["integration_id"]},
                        {"$set": {
                            "metadata": {
                                "calendars": [{"id": c["id"], "summary": c.get("summary", "")} for c in calendars],
                                "primary_calendar": primary_calendar["id"] if primary_calendar else "primary"
                            }
                        }}
                    )
                except Exception as e:
                    logger.warning(f"Failed to fetch calendars: {e}")

            return RedirectResponse(f"{HUB_FRONTEND_URL}/integrations?success=true&service={service}")

    except Exception as e:
        logger.error(f"Integration {service} callback error: {e}")
        return RedirectResponse(f"{HUB_FRONTEND_URL}/integrations?error=callback_failed&service={service}")

@api_router.delete("/integrations/{service}")
async def disconnect_integration(service: str, user: dict = Depends(get_current_user)):
    """Disconnect an integration by service name or integration_id."""
    # Try by service name first, then by integration_id for backward compat
    result = await db.user_integrations.delete_one(
        {"user_id": user["user_id"], "service": service}
    )
    if result.deleted_count == 0:
        result = await db.user_integrations.delete_one(
            {"user_id": user["user_id"], "integration_id": service}
        )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Integration not found")

    # Clean up related data
    await db.detected_free_slots.delete_many({"user_id": user["user_id"]})
    await db.synced_events.delete_many({"user_id": user["user_id"], "service": service})

    return {"message": f"{INTEGRATION_CONFIGS.get(service, {}).get('name', service)} disconnected"}

@api_router.put("/integrations/{service}/sync")
async def toggle_sync(service: str, request: Request, user: dict = Depends(get_current_user)):
    """Toggle sync on/off for an integration."""
    body = await request.json()
    sync_enabled = body.get("sync_enabled", True)

    result = await db.user_integrations.update_one(
        {"user_id": user["user_id"], "$or": [{"service": service}, {"provider": service}]},
        {"$set": {"sync_enabled": sync_enabled, "enabled": sync_enabled}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Integration not found")
    return {"sync_enabled": sync_enabled}

@api_router.post("/integrations/{service}/sync")
async def trigger_sync(service: str, user: dict = Depends(get_current_user)):
    """Trigger a manual sync for a service — syncs recent sessions to external services."""
    integration = await db.user_integrations.find_one(
        {"user_id": user["user_id"], "$or": [{"service": service}, {"provider": service}]},
        {"_id": 0}
    )
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not connected")

    access_token = integration.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="No access token")

    # Decrypt token if encrypted
    try:
        decrypted_token = decrypt_token(access_token)
        if decrypted_token:
            access_token = decrypted_token
    except Exception:
        pass  # Token may not be encrypted (legacy)

    # --- Google Calendar: URL-based (iCal) or OAuth ---
    if service == "google_calendar":
        # Detect if connected via iCal URL (no token_expires_at, URL starts with http)
        is_ical_url = not integration.get("token_expires_at") and access_token.startswith("http")
        if is_ical_url and ICAL_AVAILABLE:
            # Use iCal parsing (same as ical service)
            try:
                async with httpx.AsyncClient(timeout=15.0) as http_client:
                    resp = await http_client.get(access_token, follow_redirects=True)
                    if resp.status_code != 200:
                        raise HTTPException(status_code=502, detail=f"Calendar feed returned HTTP {resp.status_code}")
                    cal = ICalCalendar.from_ical(resp.text)
                    now = datetime.now(timezone.utc)
                    end_time = now + timedelta(hours=24)
                    events = []
                    for component in cal.walk("VEVENT"):
                        dtstart = component.get("dtstart")
                        if not dtstart or not hasattr(dtstart, "dt"):
                            continue
                        start = dtstart.dt
                        if hasattr(start, "hour"):
                            if hasattr(start, "tzinfo") and start.tzinfo:
                                start = start.astimezone(timezone.utc)
                            else:
                                start = start.replace(tzinfo=timezone.utc)
                            if now <= start <= end_time:
                                dtend = component.get("dtend")
                                end = dtend.dt if dtend and hasattr(dtend, "dt") else start + timedelta(hours=1)
                                if hasattr(end, "tzinfo") and end.tzinfo:
                                    end = end.astimezone(timezone.utc)
                                else:
                                    end = end.replace(tzinfo=timezone.utc)
                                events.append({
                                    "summary": str(component.get("summary", "Sans titre")),
                                    "start": {"dateTime": start.isoformat()},
                                    "end": {"dateTime": end.isoformat()},
                                })
                    prefs = await db.notification_preferences.find_one({"user_id": user["user_id"]}, {"_id": 0}) or {}
                    settings = {**DEFAULT_SETTINGS, **prefs}
                    slots = await detect_free_slots(events, settings)
                    await cleanup_old_slots(db, user["user_id"])
                    actions = await db.micro_actions.find({}, {"_id": 0}).to_list(50)
                    await schedule_slot_notifications(db, user["user_id"], slots, actions, user.get("subscription_tier", "free"))
                    await db.user_integrations.update_one(
                        {"user_id": user["user_id"], "$or": [{"service": service}, {"provider": service}]},
                        {"$set": {"last_sync_at": now.isoformat(), "last_synced_at": now.isoformat()}}
                    )
                    return {
                        "message": "Sync completed",
                        "synced_count": len(slots),
                        "events_found": len(events),
                        "slots_detected": len(slots),
                        "service": service,
                        "last_sync": now.isoformat()
                    }
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Google Calendar iCal sync failed: {e}")
                raise HTTPException(status_code=500, detail="Sync failed. Please try again.")

        # OAuth-based sync (legacy)
        try:
            token_expires_str = integration.get("token_expires_at")
            if token_expires_str:
                token_expires = datetime.fromisoformat(token_expires_str.replace('Z', '+00:00'))
                if token_expires < datetime.now(timezone.utc):
                    if not integration.get("refresh_token"):
                        raise HTTPException(status_code=401, detail="Token expired, please reconnect")
                    refresh_tok = integration["refresh_token"]
                    try:
                        refresh_tok = decrypt_token(refresh_tok) or refresh_tok
                    except Exception:
                        pass
                    new_tokens = await refresh_access_token(refresh_tok)
                    encrypted = encrypt_tokens(new_tokens)
                    await db.user_integrations.update_one(
                        {"user_id": user["user_id"], "$or": [{"service": service}, {"provider": service}]},
                        {"$set": {
                            "access_token": encrypted["access_token"],
                            "token_expires_at": (datetime.now(timezone.utc) + timedelta(seconds=new_tokens.get("expires_in", 3600))).isoformat()
                        }}
                    )
                    access_token = encrypted["access_token"]

            now = datetime.now(timezone.utc)
            tomorrow = now + timedelta(hours=24)

            events = await get_calendar_events(
                access_token, now, tomorrow,
                integration.get("metadata", {}).get("primary_calendar", "primary")
            )

            prefs = await db.notification_preferences.find_one(
                {"user_id": user["user_id"]}, {"_id": 0}
            ) or {}
            settings = {**DEFAULT_SETTINGS, **prefs}
            slots = await detect_free_slots(events, settings)
            await cleanup_old_slots(db, user["user_id"])
            actions = await db.micro_actions.find({}, {"_id": 0}).to_list(50)
            await schedule_slot_notifications(
                db, user["user_id"], slots, actions, user.get("subscription_tier", "free")
            )

            await db.user_integrations.update_one(
                {"user_id": user["user_id"], "$or": [{"service": service}, {"provider": service}]},
                {"$set": {"last_sync_at": now.isoformat(), "last_synced_at": now.isoformat()}}
            )

            return {
                "message": "Sync completed",
                "synced_count": len(slots),
                "events_found": len(events),
                "slots_detected": len(slots),
                "service": service,
                "last_sync": now.isoformat()
            }
        except Exception as e:
            logger.error(f"Google Calendar sync failed: {e}")
            raise HTTPException(status_code=500, detail="Sync failed. Please try again.")

    # --- iCal: fetch events and detect free slots ---
    if service == "ical" and ICAL_AVAILABLE:
        try:
            ical_url = access_token  # For iCal, the "token" is the decrypted URL
            async with httpx.AsyncClient(timeout=15.0) as http_client:
                resp = await http_client.get(ical_url, follow_redirects=True)
                if resp.status_code != 200:
                    raise HTTPException(status_code=502, detail=f"iCal feed returned HTTP {resp.status_code}")

                cal = ICalCalendar.from_ical(resp.text)
                now = datetime.now(timezone.utc)
                end_time = now + timedelta(hours=24)
                events = []

                for component in cal.walk("VEVENT"):
                    dtstart = component.get("dtstart")
                    if not dtstart or not hasattr(dtstart, "dt"):
                        continue
                    start = dtstart.dt
                    if hasattr(start, 'hour'):
                        if hasattr(start, "tzinfo") and start.tzinfo:
                            start = start.astimezone(timezone.utc)
                        else:
                            start = start.replace(tzinfo=timezone.utc)
                        if now <= start <= end_time:
                            dtend = component.get("dtend")
                            end = dtend.dt if dtend and hasattr(dtend, "dt") else start + timedelta(hours=1)
                            if hasattr(end, "tzinfo") and end.tzinfo:
                                end = end.astimezone(timezone.utc)
                            else:
                                end = end.replace(tzinfo=timezone.utc)
                            events.append({
                                "summary": str(component.get("summary", "Événement")),
                                "start": {"dateTime": start.isoformat()},
                                "end": {"dateTime": end.isoformat()},
                            })

                prefs = await db.notification_preferences.find_one({"user_id": user["user_id"]}, {"_id": 0}) or {}
                settings = {**DEFAULT_SETTINGS, **prefs}
                slots = await detect_free_slots(events, settings)
                await cleanup_old_slots(db, user["user_id"])
                actions = await db.micro_actions.find({}, {"_id": 0}).to_list(50)
                await schedule_slot_notifications(db, user["user_id"], slots, actions, user.get("subscription_tier", "free"))

                await db.user_integrations.update_one(
                    {"user_id": user["user_id"], "service": "ical"},
                    {"$set": {"last_synced_at": now.isoformat(), "metadata.event_count": len(events)}}
                )
                return {
                    "message": "Sync completed",
                    "synced_count": len(slots), "events_found": len(events),
                    "slots_detected": len(slots), "service": "ical", "last_sync": now.isoformat()
                }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"iCal sync error: {e}")
            raise HTTPException(status_code=500, detail="iCal sync failed. Please check your URL and try again.")

    # --- Other services: sync recent sessions ---
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    recent_sessions = await db.user_sessions_history.find(
        {"user_id": user["user_id"], "completed": True, "completed_at": {"$gte": week_ago}},
        {"_id": 0}
    ).sort("completed_at", -1).to_list(20)

    synced_count = 0

    try:
        async with httpx.AsyncClient() as http_client:
            if service == "notion":
                for session in recent_sessions:
                    already = await db.synced_events.find_one({
                        "user_id": user["user_id"], "service": service,
                        "session_id": session["session_id"]
                    })
                    if already:
                        continue

                    search_resp = await http_client.post(
                        "https://api.notion.com/v1/search",
                        json={"query": "InFinea Sessions", "filter": {"property": "object", "value": "page"}},
                        headers={"Authorization": f"Bearer {access_token}", "Notion-Version": "2022-06-28"}
                    )
                    parent_page_id = None
                    if search_resp.status_code == 200:
                        results = search_resp.json().get("results", [])
                        if results:
                            parent_page_id = results[0]["id"]

                    if not parent_page_id:
                        pages_resp = await http_client.post(
                            "https://api.notion.com/v1/search",
                            json={"filter": {"property": "object", "value": "page"}, "page_size": 1},
                            headers={"Authorization": f"Bearer {access_token}", "Notion-Version": "2022-06-28"}
                        )
                        if pages_resp.status_code == 200:
                            pages = pages_resp.json().get("results", [])
                            if pages:
                                parent_page_id = pages[0]["id"]

                    if parent_page_id:
                        title = session.get("action_title", "Micro-action")
                        duration = session.get("actual_duration", 5)
                        completed_at = session.get("completed_at", "")
                        page_data = {
                            "parent": {"page_id": parent_page_id},
                            "properties": {"title": {"title": [{"text": {"content": f"✅ {title} — {duration} min"}}]}},
                            "children": [{"object": "block", "type": "paragraph", "paragraph": {
                                "rich_text": [{"text": {"content": f"Catégorie: {session.get('category', 'N/A')}\nDurée: {duration} min\nDate: {completed_at[:10] if completed_at else 'N/A'}"}}]
                            }}]
                        }
                        resp = await http_client.post(
                            "https://api.notion.com/v1/pages", json=page_data,
                            headers={"Authorization": f"Bearer {access_token}", "Notion-Version": "2022-06-28"}
                        )
                        if resp.status_code in (200, 201):
                            await db.synced_events.insert_one({
                                "user_id": user["user_id"], "service": service,
                                "session_id": session["session_id"],
                                "external_id": resp.json().get("id"),
                                "synced_at": datetime.now(timezone.utc).isoformat()
                            })
                            synced_count += 1

            elif service == "todoist":
                for session in recent_sessions:
                    already = await db.synced_events.find_one({
                        "user_id": user["user_id"], "service": service,
                        "session_id": session["session_id"]
                    })
                    if already:
                        continue

                    title = session.get("action_title", "Micro-action")
                    duration = session.get("actual_duration", 5)
                    resp = await http_client.post(
                        "https://api.todoist.com/rest/v2/tasks",
                        json={"content": f"✅ {title}", "description": f"Session InFinea complétée — {duration} min"},
                        headers={"Authorization": f"Bearer {access_token}"}
                    )
                    if resp.status_code in (200, 201):
                        task_id = resp.json().get("id")
                        await http_client.post(
                            f"https://api.todoist.com/rest/v2/tasks/{task_id}/close",
                            headers={"Authorization": f"Bearer {access_token}"}
                        )
                        await db.synced_events.insert_one({
                            "user_id": user["user_id"], "service": service,
                            "session_id": session["session_id"],
                            "external_id": str(task_id),
                            "synced_at": datetime.now(timezone.utc).isoformat()
                        })
                        synced_count += 1

            elif service == "slack":
                if recent_sessions:
                    total_time = sum(s.get("actual_duration", 0) for s in recent_sessions)
                    session_count = len(recent_sessions)
                    categories = set(s.get("category", "N/A") for s in recent_sessions)
                    cat_map = {"learning": "📚 Apprentissage", "productivity": "🎯 Productivité", "well_being": "💚 Bien-être"}
                    cats_str = ", ".join([cat_map.get(c, c) for c in categories])

                    message = (
                        f"*📊 Résumé InFinea — 7 derniers jours*\n\n"
                        f"• *{session_count}* sessions complétées\n"
                        f"• *{total_time}* minutes investies\n"
                        f"• Catégories: {cats_str}\n\n"
                        f"Continuez comme ça ! 🚀"
                    )

                    # Support both webhook URLs and OAuth tokens
                    if access_token.startswith("https://hooks.slack.com/"):
                        resp = await http_client.post(access_token, json={"text": message})
                    else:
                        resp = await http_client.post(
                            "https://slack.com/api/chat.postMessage",
                            json={"channel": "me", "text": message, "mrkdwn": True},
                            headers={"Authorization": f"Bearer {access_token}"}
                        )
                    if resp.status_code == 200:
                        resp_data = resp.json() if "application/json" in resp.headers.get("content-type", "") else {}
                        if resp_data.get("ok", True):  # Webhooks return "ok", API returns {"ok": true}
                            synced_count = session_count

    except Exception as e:
        logger.error(f"Sync error for {service}: {e}")
        raise HTTPException(status_code=500, detail="Sync failed. Please try again.")

    await db.user_integrations.update_one(
        {"user_id": user["user_id"], "$or": [{"service": service}, {"provider": service}]},
        {"$set": {"last_synced_at": datetime.now(timezone.utc).isoformat()}}
    )

    return {"synced_count": synced_count, "service": service}

# ============== iCal INTEGRATION (URL-based, non-OAuth) ==============

@api_router.post("/integrations/ical/connect")
async def connect_ical(request: ICalConnectRequest, user: dict = Depends(get_current_user)):
    """Connect an iCal calendar via URL (.ics feed)."""
    # Check integration limit for free users (max 1)
    if user.get("subscription_tier") != "premium":
        existing = await db.user_integrations.count_documents({"user_id": user["user_id"]})
        if existing >= 1:
            raise HTTPException(
                status_code=403,
                detail="Limite atteinte : 1 intégration maximum en mode gratuit. Passez à Premium pour connecter toutes vos intégrations."
            )

    if not ICAL_AVAILABLE:
        raise HTTPException(status_code=503, detail="iCal support not installed (pip install icalendar)")

    url = request.url.strip()
    if not url.startswith(("http://", "https://", "webcal://")):
        raise HTTPException(status_code=400, detail="URL invalide. L'URL doit commencer par http://, https:// ou webcal://")

    # Normalize webcal:// to https://
    if url.startswith("webcal://"):
        url = "https://" + url[len("webcal://"):]

    # Validate the URL by fetching it
    try:
        async with httpx.AsyncClient(timeout=15.0) as http_client:
            resp = await http_client.get(url, follow_redirects=True)
            if resp.status_code != 200:
                raise HTTPException(status_code=400, detail=f"Impossible d'accéder à l'URL (HTTP {resp.status_code})")
            # Try to parse as iCal to validate
            cal = ICalCalendar.from_ical(resp.text)
            cal_name = str(cal.get("X-WR-CALNAME", request.name or "iCal"))
            event_count = sum(1 for _ in cal.walk("VEVENT"))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail="URL invalide ou format iCal non reconnu.")

    # Store as integration (URL encrypted like a token)
    encrypted_url = encrypt_token(url)

    await db.user_integrations.delete_many({"user_id": user["user_id"], "service": "ical"})
    await db.user_integrations.insert_one({
        "user_id": user["user_id"],
        "service": "ical",
        "provider": "ical",
        "access_token": encrypted_url,  # Encrypted iCal URL
        "account_name": cal_name,
        "connected_at": datetime.now(timezone.utc).isoformat(),
        "enabled": True,
        "sync_enabled": True,
        "integration_id": f"int_{uuid.uuid4().hex[:12]}",
        "metadata": {"event_count": event_count, "ical_url_hash": url[:50] + "..."},
    })

    return {"success": True, "calendar_name": cal_name, "events_found": event_count}

# URL-based services that support iCal format
URL_CONNECT_SERVICES = {"ical", "google_calendar"}

@api_router.post("/integrations/{service}/connect-url")
async def connect_url(service: str, request: ICalConnectRequest, user: dict = Depends(get_current_user)):
    """Connect any calendar service via iCal URL (.ics feed)."""
    if service not in URL_CONNECT_SERVICES:
        raise HTTPException(status_code=400, detail=f"Service '{service}' ne supporte pas la connexion par URL")
    if not ICAL_AVAILABLE:
        raise HTTPException(status_code=503, detail="iCal support not installed (pip install icalendar)")

    url = request.url.strip()
    if not url.startswith(("http://", "https://", "webcal://")):
        raise HTTPException(status_code=400, detail="URL invalide. L'URL doit commencer par http://, https:// ou webcal://")

    if url.startswith("webcal://"):
        url = "https://" + url[len("webcal://"):]

    try:
        async with httpx.AsyncClient(timeout=15.0) as http_client:
            resp = await http_client.get(url, follow_redirects=True)
            if resp.status_code != 200:
                raise HTTPException(status_code=400, detail=f"Impossible d'accéder à l'URL (HTTP {resp.status_code})")
            cal = ICalCalendar.from_ical(resp.text)
            cal_name = str(cal.get("X-WR-CALNAME", request.name or service))
            event_count = sum(1 for _ in cal.walk("VEVENT"))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail="URL invalide ou format iCal non reconnu.")

    encrypted_url = encrypt_token(url)

    await db.user_integrations.delete_many({"user_id": user["user_id"], "service": service})
    await db.user_integrations.insert_one({
        "user_id": user["user_id"],
        "service": service,
        "provider": service,
        "access_token": encrypted_url,
        "account_name": cal_name,
        "connected_at": datetime.now(timezone.utc).isoformat(),
        "enabled": True,
        "sync_enabled": True,
        "integration_id": f"int_{uuid.uuid4().hex[:12]}",
        "metadata": {"event_count": event_count, "ical_url_hash": url[:50] + "..."},
    })

    return {"success": True, "calendar_name": cal_name, "events_found": event_count}

@api_router.post("/integrations/ical/sync")
async def sync_ical(user: dict = Depends(get_current_user)):
    """Sync iCal calendar — fetches events and detects free slots."""
    if not ICAL_AVAILABLE:
        raise HTTPException(status_code=503, detail="iCal support not installed")

    integration = await db.user_integrations.find_one(
        {"user_id": user["user_id"], "service": "ical"}, {"_id": 0}
    )
    if not integration:
        raise HTTPException(status_code=404, detail="iCal not connected")

    encrypted_url = integration.get("access_token")
    if not encrypted_url:
        raise HTTPException(status_code=400, detail="No iCal URL stored")

    try:
        ical_url = decrypt_token(encrypted_url)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to decrypt iCal URL")

    try:
        async with httpx.AsyncClient(timeout=15.0) as http_client:
            resp = await http_client.get(ical_url, follow_redirects=True)
            if resp.status_code != 200:
                raise HTTPException(status_code=502, detail=f"iCal feed returned HTTP {resp.status_code}")

            cal = ICalCalendar.from_ical(resp.text)

            now = datetime.now(timezone.utc)
            end_time = now + timedelta(hours=24)
            events = []

            for component in cal.walk("VEVENT"):
                dtstart = component.get("dtstart")
                if not dtstart or not hasattr(dtstart, "dt"):
                    continue
                start = dtstart.dt
                if hasattr(start, 'hour'):
                    if hasattr(start, "tzinfo") and start.tzinfo:
                        start = start.astimezone(timezone.utc)
                    else:
                        start = start.replace(tzinfo=timezone.utc)
                    if now <= start <= end_time:
                        dtend = component.get("dtend")
                        end = dtend.dt if dtend and hasattr(dtend, "dt") else start + timedelta(hours=1)
                        if hasattr(end, "tzinfo") and end.tzinfo:
                            end = end.astimezone(timezone.utc)
                        else:
                            end = end.replace(tzinfo=timezone.utc)
                        events.append({
                            "summary": str(component.get("summary", "Événement")),
                            "start": {"dateTime": start.isoformat()},
                            "end": {"dateTime": end.isoformat()},
                        })

            # Detect free slots using the proper slot detector (keywords, window, categories)
            prefs = await db.notification_preferences.find_one({"user_id": user["user_id"]}, {"_id": 0}) or {}
            settings = {**DEFAULT_SETTINGS, **prefs}
            slots = await detect_free_slots(events, settings)
            await cleanup_old_slots(db, user["user_id"])
            actions = await db.micro_actions.find({}, {"_id": 0}).to_list(50)
            await schedule_slot_notifications(db, user["user_id"], slots, actions, user.get("subscription_tier", "free"))

            await db.user_integrations.update_one(
                {"user_id": user["user_id"], "service": "ical"},
                {"$set": {"last_synced_at": now.isoformat(), "metadata.event_count": len(events)}}
            )

            return {
                "message": "Sync completed",
                "synced_count": len(slots),
                "events_found": len(events),
                "slots_detected": len(slots),
                "service": "ical",
                "last_sync": now.isoformat(),
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"iCal sync error: {e}")
        raise HTTPException(status_code=500, detail="iCal sync failed. Please check your URL and try again.")

# ============== TOKEN/URL CONNECT (Notion, Todoist, Slack) ==============

TOKEN_CONNECT_VALIDATORS = {
    "notion": {
        "name": "Notion",
        "validate_url": "https://api.notion.com/v1/users/me",
        "headers_fn": lambda token: {"Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28"},
        "account_fn": lambda data: data.get("name", "Notion Workspace"),
        "placeholder": "secret_...",
        "description": "Token d'intégration interne Notion",
        "help_url": "https://www.notion.so/my-integrations",
    },
    "todoist": {
        "name": "Todoist",
        "validate_url": "https://api.todoist.com/rest/v2/projects",
        "headers_fn": lambda token: {"Authorization": f"Bearer {token}"},
        "account_fn": lambda data: "Todoist",
        "placeholder": "votre token API Todoist",
        "description": "Token API Todoist",
        "help_url": "https://app.todoist.com/app/settings/integrations/developer",
    },
    "slack": {
        "name": "Slack",
        "validate_url": None,  # Slack uses webhook URL, validated differently
        "placeholder": "https://hooks.slack.com/services/...",
        "description": "URL de webhook Slack",
        "help_url": "https://api.slack.com/messaging/webhooks",
    },
}

@api_router.post("/integrations/{service}/connect-token")
async def connect_via_token(service: str, request: TokenConnectRequest, user: dict = Depends(get_current_user)):
    """Connect an integration via API token or webhook URL (alternative to OAuth)."""
    # Check integration limit for free users (max 1)
    if user.get("subscription_tier") != "premium":
        existing = await db.user_integrations.count_documents({"user_id": user["user_id"]})
        if existing >= 1:
            raise HTTPException(
                status_code=403,
                detail="Limite atteinte : 1 intégration maximum en mode gratuit. Passez à Premium pour connecter toutes vos intégrations."
            )

    if service not in TOKEN_CONNECT_VALIDATORS:
        raise HTTPException(status_code=400, detail=f"Service '{service}' ne supporte pas la connexion par token")

    config = TOKEN_CONNECT_VALIDATORS[service]
    token = request.token.strip()
    if not token:
        raise HTTPException(status_code=400, detail="Token ou URL requis")

    account_name = request.name or config["name"]

    # Validate the token/URL by calling the service API
    try:
        async with httpx.AsyncClient(timeout=10.0) as http_client:
            if service == "slack":
                # Slack: validate webhook URL by sending a test message
                if not token.startswith("https://hooks.slack.com/"):
                    raise HTTPException(status_code=400, detail="URL Slack invalide. Doit commencer par https://hooks.slack.com/")
                resp = await http_client.post(token, json={"text": "✅ InFinea connecté avec succès !"})
                if resp.status_code != 200:
                    raise HTTPException(status_code=400, detail=f"Webhook Slack invalide (HTTP {resp.status_code})")
                account_name = request.name or "Slack Webhook"
            else:
                # Notion/Todoist: validate token via API call
                headers = config["headers_fn"](token)
                resp = await http_client.get(config["validate_url"], headers=headers)
                if resp.status_code == 401:
                    raise HTTPException(status_code=400, detail=f"Token {config['name']} invalide ou expiré")
                if resp.status_code != 200:
                    raise HTTPException(status_code=400, detail=f"Erreur de validation {config['name']} (HTTP {resp.status_code})")
                try:
                    data = resp.json()
                    account_name = config["account_fn"](data) or config["name"]
                except Exception:
                    pass

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail="Impossible de valider le token. V\u00e9rifiez et r\u00e9essayez.")

    # Store encrypted token
    encrypted_token = encrypt_token(token)

    await db.user_integrations.delete_many({"user_id": user["user_id"], "service": service})
    await db.user_integrations.delete_many({"user_id": user["user_id"], "provider": service})
    await db.user_integrations.insert_one({
        "user_id": user["user_id"],
        "service": service,
        "provider": service,
        "access_token": encrypted_token,
        "account_name": account_name,
        "connected_at": datetime.now(timezone.utc).isoformat(),
        "enabled": True,
        "sync_enabled": True,
        "integration_id": f"int_{uuid.uuid4().hex[:12]}",
        "connection_type": "token",  # Distinguish from OAuth connections
    })

    return {"success": True, "account_name": account_name, "service": service}

# ============== FREE SLOTS ENDPOINTS ==============

@api_router.get("/slots/today")
async def get_today_slots(user: dict = Depends(get_current_user)):
    """Get free slots for today."""
    now = datetime.now(timezone.utc)
    end_of_day = now.replace(hour=23, minute=59, second=59)
    
    slots = await db.detected_free_slots.find({
        "user_id": user["user_id"],
        "start_time": {"$gte": now.isoformat(), "$lte": end_of_day.isoformat()}
    }, {"_id": 0}).sort("start_time", 1).to_list(20)
    
    # Enrich with action details
    for slot in slots:
        if slot.get("suggested_action_id"):
            action = await db.micro_actions.find_one(
                {"action_id": slot["suggested_action_id"]},
                {"_id": 0}
            )
            slot["suggested_action"] = action
    
    return {"slots": slots, "count": len(slots)}

@api_router.get("/slots/week")
async def get_week_slots(user: dict = Depends(get_current_user)):
    """Get free slots for the week."""
    now = datetime.now(timezone.utc)
    week_end = now + timedelta(days=7)
    
    slots = await db.detected_free_slots.find({
        "user_id": user["user_id"],
        "start_time": {"$gte": now.isoformat(), "$lte": week_end.isoformat()}
    }, {"_id": 0}).sort("start_time", 1).to_list(50)
    
    return {"slots": slots, "count": len(slots)}

@api_router.get("/slots/next")
async def get_next_slot(user: dict = Depends(get_current_user)):
    """Get the next upcoming free slot, enriched with scored suggestion."""
    now = datetime.now(timezone.utc)

    slot = await db.detected_free_slots.find_one({
        "user_id": user["user_id"],
        "start_time": {"$gte": now.isoformat()},
        "action_taken": False
    }, {"_id": 0}, sort=[("start_time", 1)])

    if slot and slot.get("suggested_action_id"):
        action = await db.micro_actions.find_one(
            {"action_id": slot["suggested_action_id"]},
            {"_id": 0}
        )
        slot["suggested_action"] = action

    # Enrich with scored suggestion if features are available
    if slot and slot.get("duration_minutes"):
        try:
            scored = await get_next_best_action(
                db, user["user_id"],
                slot_duration=slot["duration_minutes"],
                slot_start_time=slot.get("start_time"),
                min_score=0.6,
            )
            if scored:
                slot["scored_suggestion"] = {
                    "action_id": scored.get("action_id"),
                    "title": scored.get("title"),
                    "category": scored.get("category"),
                    "score": scored.get("_score"),
                    "energy_level": scored.get("energy_level"),
                }
        except Exception:
            pass  # scoring is best-effort, never break the route

    return {"slot": slot}

@api_router.post("/slots/{slot_id}/dismiss")
async def dismiss_slot(slot_id: str, user: dict = Depends(get_current_user)):
    """Dismiss/ignore a slot."""
    result = await db.detected_free_slots.update_one(
        {"slot_id": slot_id, "user_id": user["user_id"]},
        {"$set": {"dismissed": True, "dismissed_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Slot not found")

    await track_event(db, user["user_id"], "slot_dismissed", {
        "slot_id": slot_id,
    })

    return {"message": "Slot dismissed"}

@api_router.get("/slots/settings")
async def get_slot_settings(user: dict = Depends(get_current_user)):
    """Get user's slot detection settings."""
    prefs = await db.notification_preferences.find_one(
        {"user_id": user["user_id"]},
        {"_id": 0}
    )
    
    # Merge with defaults
    settings = {**DEFAULT_SETTINGS}
    if prefs:
        for key in DEFAULT_SETTINGS:
            if key in prefs:
                settings[key] = prefs[key]
    
    return settings

@api_router.put("/slots/settings")
async def update_slot_settings(
    settings: SlotSettings,
    user: dict = Depends(get_current_user)
):
    """Update user's slot detection settings."""
    settings_dict = settings.model_dump()
    
    await db.notification_preferences.update_one(
        {"user_id": user["user_id"]},
        {"$set": settings_dict},
        upsert=True
    )
    
    return {"message": "Settings updated", "settings": settings_dict}

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

class NotificationPreferences(BaseModel):
    daily_reminder: bool = True
    reminder_time: str = "09:00"  # HH:MM format
    streak_alerts: bool = True
    achievement_alerts: bool = True
    weekly_summary: bool = True

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

# ============== B2B DASHBOARD ==============

class CompanyCreate(BaseModel):
    name: str
    domain: str

class InviteEmployee(BaseModel):
    email: EmailStr

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

# ============== OBJECTIVES (PARCOURS PERSONNALISÉS) ==============

@api_router.post("/objectives")
@limiter.limit("10/minute")
async def create_objective(request: Request, obj: ObjectiveCreate, user: dict = Depends(get_current_user)):
    """Create a new personal objective with AI-generated curriculum."""
    # Free users: max 2 active objectives. Premium: unlimited.
    active_count = await db.objectives.count_documents({"user_id": user["user_id"], "status": "active"})
    max_objectives = 2 if user.get("subscription_tier") != "premium" else 20
    if active_count >= max_objectives:
        tier_msg = "Passe en Premium pour plus d'objectifs !" if user.get("subscription_tier") != "premium" else "Maximum 20 objectifs actifs."
        raise HTTPException(status_code=400, detail=f"Limite atteinte ({max_objectives} objectifs actifs). {tier_msg}")

    now = datetime.now(timezone.utc).isoformat()
    objective_id = f"obj_{uuid.uuid4().hex[:12]}"

    objective_doc = {
        "objective_id": objective_id,
        "user_id": user["user_id"],
        "title": obj.title.strip(),
        "description": (obj.description or "").strip(),
        "target_duration_days": min(max(obj.target_duration_days or 30, 7), 365),
        "daily_minutes": min(max(obj.daily_minutes or 10, 2), 60),
        "category": obj.category or "learning",
        "status": "active",
        "created_at": now,
        "started_at": now,
        "current_day": 0,
        "total_sessions": 0,
        "total_minutes": 0,
        "streak_days": 0,
        "last_session_date": None,
        "curriculum": [],  # Will be populated by curriculum engine
        "progress_log": [],  # Track what was learned per session
    }

    await db.objectives.insert_one(objective_doc)

    # Generate curriculum in background (non-blocking)
    asyncio.create_task(_generate_curriculum_for_objective(objective_doc, user))

    await track_event(db, user["user_id"], "objective_created", {
        "objective_id": objective_id,
        "title": obj.title,
        "target_days": objective_doc["target_duration_days"],
    })

    # Return without _id
    objective_doc.pop("_id", None)
    return objective_doc


async def _generate_curriculum_for_objective(objective: dict, user: dict):
    """Background task: generate AI curriculum for an objective."""
    try:
        from services.curriculum_engine import generate_curriculum
        curriculum = await generate_curriculum(objective, user)
        if curriculum:
            await db.objectives.update_one(
                {"objective_id": objective["objective_id"]},
                {"$set": {"curriculum": curriculum, "curriculum_generated_at": datetime.now(timezone.utc).isoformat()}}
            )
            logger.info(f"Curriculum generated for {objective['objective_id']}: {len(curriculum)} steps")
    except Exception as e:
        logger.error(f"Curriculum generation failed for {objective['objective_id']}: {e}")


@api_router.get("/objectives")
@limiter.limit("30/minute")
async def list_objectives(request: Request, status: Optional[str] = None, user: dict = Depends(get_current_user)):
    """List user's objectives, optionally filtered by status."""
    query = {"user_id": user["user_id"]}
    if status:
        query["status"] = status
    objectives = await db.objectives.find(query, {"_id": 0}).sort("created_at", -1).to_list(50)
    return {"objectives": objectives}


@api_router.get("/objectives/{objective_id}")
@limiter.limit("30/minute")
async def get_objective(request: Request, objective_id: str, user: dict = Depends(get_current_user)):
    """Get a single objective with full curriculum and progress."""
    obj = await db.objectives.find_one(
        {"objective_id": objective_id, "user_id": user["user_id"]},
        {"_id": 0}
    )
    if not obj:
        raise HTTPException(status_code=404, detail="Objectif non trouvé")
    return obj


@api_router.put("/objectives/{objective_id}")
@limiter.limit("15/minute")
async def update_objective(request: Request, objective_id: str, updates: ObjectiveUpdate, user: dict = Depends(get_current_user)):
    """Update an objective (title, description, status, etc.)."""
    obj = await db.objectives.find_one({"objective_id": objective_id, "user_id": user["user_id"]})
    if not obj:
        raise HTTPException(status_code=404, detail="Objectif non trouvé")

    update_fields = {}
    if updates.title is not None:
        update_fields["title"] = updates.title.strip()
    if updates.description is not None:
        update_fields["description"] = updates.description.strip()
    if updates.target_duration_days is not None:
        update_fields["target_duration_days"] = min(max(updates.target_duration_days, 7), 365)
    if updates.daily_minutes is not None:
        update_fields["daily_minutes"] = min(max(updates.daily_minutes, 2), 60)
    if updates.status is not None:
        if updates.status not in ("active", "paused", "completed", "abandoned"):
            raise HTTPException(status_code=400, detail="Statut invalide")
        update_fields["status"] = updates.status
        if updates.status == "completed":
            update_fields["completed_at"] = datetime.now(timezone.utc).isoformat()

    if not update_fields:
        raise HTTPException(status_code=400, detail="Aucune modification")

    update_fields["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.objectives.update_one({"objective_id": objective_id}, {"$set": update_fields})

    await track_event(db, user["user_id"], "objective_updated", {
        "objective_id": objective_id,
        "fields": list(update_fields.keys()),
    })

    updated = await db.objectives.find_one({"objective_id": objective_id}, {"_id": 0})
    return updated


@api_router.delete("/objectives/{objective_id}")
@limiter.limit("10/minute")
async def delete_objective(request: Request, objective_id: str, user: dict = Depends(get_current_user)):
    """Delete an objective permanently."""
    result = await db.objectives.delete_one({"objective_id": objective_id, "user_id": user["user_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Objectif non trouvé")

    await track_event(db, user["user_id"], "objective_deleted", {"objective_id": objective_id})
    return {"deleted": True}


@api_router.get("/objectives/{objective_id}/next")
@limiter.limit("20/minute")
async def get_next_objective_session(request: Request, objective_id: str, user: dict = Depends(get_current_user)):
    """Get the next micro-session for an objective based on curriculum progress."""
    obj = await db.objectives.find_one(
        {"objective_id": objective_id, "user_id": user["user_id"]},
        {"_id": 0}
    )
    if not obj:
        raise HTTPException(status_code=404, detail="Objectif non trouvé")
    if obj["status"] != "active":
        raise HTTPException(status_code=400, detail="Objectif non actif")

    curriculum = obj.get("curriculum", [])
    if not curriculum:
        return {"status": "generating", "message": "Le curriculum est en cours de génération..."}

    # Find next uncompleted step
    current_day = obj.get("current_day", 0)
    next_step = None
    for step in curriculum:
        if step.get("day", 0) >= current_day and not step.get("completed"):
            next_step = step
            break

    if not next_step:
        # All steps completed — generate next batch or mark complete
        return {
            "status": "completed",
            "message": f"Bravo ! Tu as terminé le parcours \"{obj['title']}\" !",
            "total_sessions": obj.get("total_sessions", 0),
            "total_minutes": obj.get("total_minutes", 0),
        }

    # Build session memory: last 5 completed steps with notes
    progress_log = obj.get("progress_log", [])
    recent_sessions = progress_log[-5:] if progress_log else []

    # Build memory context string for the frontend/coach
    memory_context = None
    if recent_sessions:
        lines = []
        for entry in recent_sessions:
            line = f"Jour {entry.get('day', '?')}: {entry.get('step_title', '?')}"
            if entry.get("notes"):
                line += f" — Notes: {entry['notes']}"
            if entry.get("duration"):
                line += f" ({entry['duration']} min)"
            lines.append(line)
        memory_context = "\n".join(lines)

    return {
        "status": "ready",
        "objective_id": objective_id,
        "objective_title": obj["title"],
        "step": next_step,
        "progress": {
            "current_day": current_day,
            "total_days": obj["target_duration_days"],
            "total_sessions": obj.get("total_sessions", 0),
            "total_minutes": obj.get("total_minutes", 0),
            "percent": round((current_day / max(obj["target_duration_days"], 1)) * 100, 1),
        },
        "memory": {
            "recent_sessions": recent_sessions,
            "context": memory_context,
            "last_notes": recent_sessions[-1].get("notes", "") if recent_sessions else "",
            "last_focus": recent_sessions[-1].get("step_title", "") if recent_sessions else "",
        },
    }


@api_router.post("/objectives/{objective_id}/complete-step")
@limiter.limit("15/minute")
async def complete_objective_step(request: Request, objective_id: str, user: dict = Depends(get_current_user)):
    """Mark the current step as completed after a session."""
    body = await request.json()
    step_index = body.get("step_index", 0)
    actual_duration = body.get("actual_duration", 0)
    notes = body.get("notes", "")
    completed = body.get("completed", True)

    obj = await db.objectives.find_one({"objective_id": objective_id, "user_id": user["user_id"]})
    if not obj:
        raise HTTPException(status_code=404, detail="Objectif non trouvé")

    curriculum = obj.get("curriculum", [])
    if step_index < 0 or step_index >= len(curriculum):
        raise HTTPException(status_code=400, detail="Index d'étape invalide")

    now = datetime.now(timezone.utc).isoformat()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Mark step
    update_ops = {
        f"curriculum.{step_index}.completed": completed,
        f"curriculum.{step_index}.completed_at": now,
        f"curriculum.{step_index}.actual_duration": actual_duration,
        f"curriculum.{step_index}.notes": notes,
    }

    # Update objective stats
    inc_ops = {"total_sessions": 1, "total_minutes": actual_duration}

    # Streak for this objective
    last_date = obj.get("last_session_date")
    new_day = obj.get("current_day", 0)
    obj_streak = obj.get("streak_days", 0)
    if last_date != today:
        new_day += 1
        if last_date == (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d"):
            obj_streak += 1
        elif last_date is None:
            obj_streak = 1
        else:
            obj_streak = 1  # streak broken

    update_ops["current_day"] = new_day
    update_ops["streak_days"] = obj_streak
    update_ops["last_session_date"] = today

    # Progress log entry
    progress_entry = {
        "day": new_day,
        "step_index": step_index,
        "step_title": curriculum[step_index].get("title", ""),
        "duration": actual_duration,
        "completed": completed,
        "notes": notes,
        "date": now,
    }

    await db.objectives.update_one(
        {"objective_id": objective_id},
        {
            "$set": update_ops,
            "$inc": inc_ops,
            "$push": {"progress_log": progress_entry},
        }
    )

    await track_event(db, user["user_id"], "objective_step_completed", {
        "objective_id": objective_id,
        "step_index": step_index,
        "day": new_day,
        "duration": actual_duration,
    })

    # Check if objective is now complete
    completed_steps = sum(1 for s in curriculum if s.get("completed")) + (1 if completed else 0)
    total_steps = len(curriculum)
    is_finished = completed_steps >= total_steps

    return {
        "success": True,
        "day": new_day,
        "streak": obj_streak,
        "completed_steps": completed_steps,
        "total_steps": total_steps,
        "is_finished": is_finished,
        "progress_percent": round((completed_steps / max(total_steps, 1)) * 100, 1),
    }


# ============== REFLECTIONS / JOURNAL ==============

class ReflectionCreate(BaseModel):
    content: str
    mood: Optional[str] = None  # positive, neutral, negative
    tags: Optional[List[str]] = []
    related_session_id: Optional[str] = None
    related_category: Optional[str] = None

class ReflectionResponse(BaseModel):
    reflection_id: str
    user_id: str
    content: str
    mood: Optional[str]
    tags: List[str]
    related_session_id: Optional[str]
    related_category: Optional[str]
    created_at: str

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

    # Start daily action generation background loop
    from services.action_generator import daily_generation_loop
    asyncio.create_task(daily_generation_loop(db))

    # Start feature computation background loop
    from services.feature_calculator import feature_computation_loop
    asyncio.create_task(feature_computation_loop(db))

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
