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
JWT_SECRET = os.environ.get('JWT_SECRET', 'infinea-secret-key-change-in-production')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 168  # 7 days

# Create the main app
app = FastAPI(title="InFinea API")
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============== MODELS ==============

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

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

class ICalConnectRequest(BaseModel):
    url: str
    name: Optional[str] = "Mon calendrier iCal"

class TokenConnectRequest(BaseModel):
    token: str
    name: Optional[str] = None

# ============== AI HELPER FUNCTIONS ==============

AI_SYSTEM_MESSAGE = """Tu es le coach IA InFinea, expert en productivité, apprentissage et bien-être.
Tu aides les utilisateurs à transformer leurs moments perdus en micro-victoires.
Réponds toujours en français, de manière concise, chaleureuse et motivante.
Tes réponses doivent toujours être au format JSON quand demandé."""

async def call_ai(session_suffix: str, system_message: str, prompt: str) -> Optional[str]:
    """Shared AI call wrapper using Anthropic Claude API via httpx."""
    api_key = os.environ.get('ANTHROPIC_API_KEY') or os.environ.get('OPENAI_API_KEY')
    if not api_key:
        return None
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
                    "model": "claude-3-haiku-20240307",
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
async def register(user_data: UserCreate, response: Response):
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
async def login(user_data: UserLogin, response: Response):
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
async def google_oauth_callback(request: Request, response: Response, code: str = None, error: str = None):
    """Reçoit le code Google OAuth, échange contre les tokens et crée la session"""
    frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")

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
        "streak_days": user.get("streak_days", 0)
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
    
    actions = await db.micro_actions.find(query, {"_id": 0}).to_list(500)
    
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

    # Get user's recent activity for personalization
    recent_sessions = await db.user_sessions_history.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).sort("started_at", -1).limit(5).to_list(5)

    recent_categories = [s.get("category", "") for s in recent_sessions]

    # Build context for AI
    actions_text = "\n".join([
        f"- {a['title']} ({a['category']}, {a['duration_min']}-{a['duration_max']}min, énergie: {a['energy_level']}): {a['description']}"
        for a in available_actions[:10]
    ])

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

    response = await call_ai(f"suggestion_{user['user_id']}", system_msg, prompt)
    ai_result = parse_ai_json(response)

    if not ai_result:
        ai_result = {"top_pick": available_actions[0]["title"], "reasoning": "Basé sur vos préférences et le temps disponible.", "alternatives": []}

    # Match recommended actions with full action data
    recommended_actions = []
    for action in available_actions:
        if action["title"] == ai_result.get("top_pick"):
            recommended_actions.insert(0, action)
        elif action["title"] in ai_result.get("alternatives", []):
            recommended_actions.append(action)

    # Fill with remaining actions if needed
    if len(recommended_actions) < 3:
        for action in available_actions:
            if action not in recommended_actions:
                recommended_actions.append(action)
            if len(recommended_actions) >= 3:
                break

    return {
        "suggestion": ai_result.get("top_pick", available_actions[0]["title"]),
        "reasoning": ai_result.get("reasoning", "Cette action est parfaite pour le temps dont vous disposez."),
        "recommended_actions": recommended_actions[:3]
    }

# ============== AI COACH ROUTE ==============

@api_router.get("/ai/coach")
async def get_ai_coach(user: dict = Depends(get_current_user)):
    """Get personalized AI coach message for dashboard"""
    user_context = await build_user_context(user)

    recent_sessions = await db.user_sessions_history.find(
        {"user_id": user["user_id"], "completed": True},
        {"_id": 0}
    ).sort("started_at", -1).limit(5).to_list(5)

    recent_info = ""
    if recent_sessions:
        recent_titles = [s.get("action_title", "action") for s in recent_sessions[:3]]
        recent_info = f"\nSessions récentes: {', '.join(recent_titles)}"

    hour = datetime.now().hour
    time_of_day = "matin" if hour < 12 else "après-midi" if hour < 18 else "soir"
    day_names = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
    day_of_week = day_names[datetime.now().weekday()]

    prompt = f"""{user_context}{recent_info}

Il est actuellement le {time_of_day} ({day_of_week}).
Le streak actuel est de {user.get('streak_days', 0)} jours.

Génère un message de coach personnalisé pour l'accueillir sur son dashboard.
Propose proactivement une action adaptée au moment de la journée et à son profil.
Réponds en JSON:
{{
    "greeting": "Message d'accueil personnalisé (1-2 phrases)",
    "suggestion": "Suggestion d'action concrète (1 phrase)",
    "context_note": "Note contextuelle courte liée au moment/streak (1 phrase)"
}}"""

    ai_response = await call_ai(f"coach_{user['user_id']}", AI_SYSTEM_MESSAGE, prompt)
    ai_result = parse_ai_json(ai_response)

    profile = user.get("user_profile", {}) or {}
    goals = profile.get("goals", [])
    query = {}
    if goals:
        query["category"] = {"$in": goals}
    if user.get("subscription_tier") == "free":
        query["is_premium"] = False
    actions = await db.micro_actions.find(query, {"_id": 0}).to_list(5)
    suggested_action_id = actions[0]["action_id"] if actions else None

    if ai_result:
        return {
            "greeting": ai_result.get("greeting", f"Bonjour {user.get('name', '')} !"),
            "suggestion": ai_result.get("suggestion", "Commencez une micro-action pour avancer."),
            "suggested_action_id": suggested_action_id,
            "context_note": ai_result.get("context_note", f"C'est le {time_of_day}, bon moment pour progresser.")
        }

    return {
        "greeting": f"Bonjour {user.get('name', '').split(' ')[0]} ! Prêt(e) pour une micro-victoire ?",
        "suggestion": "Profitez de quelques minutes pour progresser vers vos objectifs.",
        "suggested_action_id": suggested_action_id,
        "context_note": f"C'est le {time_of_day}, idéal pour une micro-action."
    }

# ============== AI DEBRIEF ROUTE ==============

@api_router.post("/ai/debrief")
async def get_ai_debrief(
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

    prompt = f"""{user_context}

L'utilisateur vient de terminer une session:
- Action: {action_title} (catégorie: {action_category})
- Durée réelle: {duration} minutes{notes_info}

Génère un débrief personnalisé et motivant. Suggère aussi une prochaine action.
Réponds en JSON:
{{
    "feedback": "Feedback personnalisé sur la session (1-2 phrases)",
    "encouragement": "Message de motivation (1 phrase)",
    "next_suggestion": "Suggestion pour la prochaine action (1 phrase)"
}}"""

    ai_response = await call_ai(f"debrief_{user['user_id']}", AI_SYSTEM_MESSAGE, prompt)
    ai_result = parse_ai_json(ai_response)

    query = {}
    if user.get("subscription_tier") == "free":
        query["is_premium"] = False
    next_actions = await db.micro_actions.find(query, {"_id": 0}).to_list(5)
    next_action_id = next_actions[0]["action_id"] if next_actions else None

    if ai_result:
        return {
            "feedback": ai_result.get("feedback", "Bravo pour cette session !"),
            "encouragement": ai_result.get("encouragement", "Chaque minute compte."),
            "next_suggestion": ai_result.get("next_suggestion", "Continuez sur cette lancée !"),
            "next_action_id": next_action_id
        }

    return {
        "feedback": f"Excellente session de {duration} min sur {action_title} !",
        "encouragement": "Chaque micro-action vous rapproche de vos objectifs.",
        "next_suggestion": "Prenez une pause et revenez quand vous êtes prêt(e) pour la suite.",
        "next_action_id": next_action_id
    }

# ============== AI WEEKLY ANALYSIS ROUTE ==============

@api_router.get("/ai/weekly-analysis")
async def get_weekly_analysis(user: dict = Depends(get_current_user)):
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

    categories_fr = {"learning": "apprentissage", "productivity": "productivité", "well_being": "bien-être"}
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

    ai_response = await call_ai(f"analysis_{user['user_id']}", AI_SYSTEM_MESSAGE, prompt)
    ai_result = parse_ai_json(ai_response)

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
async def check_streak_risk(user: dict = Depends(get_current_user)):
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

            ai_response = await call_ai(f"streak_alert_{user['user_id']}", AI_SYSTEM_MESSAGE, prompt)
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
                return {"at_risk": True, "notification_sent": True, "message": message}

            return {"at_risk": True, "notification_sent": False, "message": message}

    return {"at_risk": False, "notification_sent": False, "message": None}

# ============== AI CUSTOM ACTION ROUTES ==============

@api_router.post("/ai/create-action")
async def create_custom_action(
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

    ai_response = await call_ai(f"create_action_{user['user_id']}", AI_SYSTEM_MESSAGE, prompt)
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
    
    if completion.completed:
        # Update user stats
        user_doc = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0})
        
        # Calculate streak
        today = datetime.now(timezone.utc).date()
        last_session = user_doc.get("last_session_date")
        
        new_streak = user_doc.get("streak_days", 0)
        if last_session:
            if isinstance(last_session, str):
                last_date = datetime.fromisoformat(last_session).date()
            else:
                last_date = last_session.date() if hasattr(last_session, 'date') else last_session
            
            if last_date == today - timedelta(days=1):
                new_streak += 1
            elif last_date != today:
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
    """Create Stripe checkout session for Premium subscription"""
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
                    "mode": "payment",
                    "success_url": success_url,
                    "cancel_url": cancel_url,
                    "line_items[0][price_data][currency]": "eur",
                    "line_items[0][price_data][product_data][name]": "InFinea Premium",
                    "line_items[0][price_data][unit_amount]": int(SUBSCRIPTION_PRICE * 100),
                    "line_items[0][quantity]": "1",
                    "metadata[user_id]": user["user_id"],
                    "metadata[email]": user["email"],
                    "metadata[plan]": "premium",
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
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": {
                "payment_status": payment_status,
                "status": status.get("status"),
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
                        "subscription_started_at": datetime.now(timezone.utc).isoformat()
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
    """Handle Stripe webhooks"""
    stripe_key = os.environ.get('STRIPE_API_KEY')
    if not stripe_key:
        return {"status": "error", "message": "Not configured"}

    body = await request.body()

    try:
        event = json.loads(body)
        event_type = event.get("type", "")
        if event_type == "checkout.session.completed":
            session_data = event.get("data", {}).get("object", {})
            if session_data.get("payment_status") == "paid":
                user_id = session_data.get("metadata", {}).get("user_id")
                if user_id:
                    await db.users.update_one(
                        {"user_id": user_id},
                        {"$set": {"subscription_tier": "premium"}}
                    )
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error"}

# ============== SEED DATA ==============

@api_router.post("/admin/seed")
async def seed_micro_actions():
    """Seed database with 300 micro-actions from seed_actions.py"""
    from seed_actions import SEED_ACTIONS

    # Clear existing and insert new
    await db.micro_actions.delete_many({})
    await db.micro_actions.insert_many(SEED_ACTIONS)

    return {"message": f"Seeded {len(SEED_ACTIONS)} micro-actions"}

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

    state = f"{user['user_id']}:{uuid.uuid4().hex[:16]}"
    await db.integration_states.insert_one({
        "state": state,
        "user_id": user["user_id"],
        "service": service,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    })

    backend_url = os.environ.get("BACKEND_URL", str(request.base_url).rstrip('/'))
    redirect_uri = f"{backend_url}/api/integrations/callback/{service}"

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
        backend_url = os.environ.get("BACKEND_URL", "http://localhost:8000")
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
                raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

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
            raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

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
                    dtend = component.get("dtend")
                    if dtstart and dtend:
                        start = dtstart.dt
                        end = dtend.dt
                        if hasattr(start, 'hour'):
                            if start.tzinfo is None:
                                start = start.replace(tzinfo=timezone.utc)
                            if end.tzinfo is None:
                                end = end.replace(tzinfo=timezone.utc)
                            if start < end_time and end > now:
                                events.append({"start": start.isoformat(), "end": end.isoformat()})

                events.sort(key=lambda e: e["start"])
                slots = []
                settings = await db.notification_preferences.find_one(
                    {"user_id": user["user_id"]}, {"_id": 0}
                )
                min_dur = (settings or {}).get("min_slot_duration", 5)
                max_dur = (settings or {}).get("max_slot_duration", 20)

                prev_end = now
                for event in events:
                    event_start = datetime.fromisoformat(event["start"])
                    gap_minutes = (event_start - prev_end).total_seconds() / 60
                    if min_dur <= gap_minutes <= max_dur:
                        slots.append({
                            "user_id": user["user_id"],
                            "start_time": prev_end.isoformat(),
                            "end_time": event_start.isoformat(),
                            "duration_minutes": int(gap_minutes),
                            "source": "ical",
                            "detected_at": now.isoformat(),
                        })
                    prev_end = max(prev_end, datetime.fromisoformat(event["end"]))

                if slots:
                    await db.detected_free_slots.delete_many({"user_id": user["user_id"], "source": "ical"})
                    await db.detected_free_slots.insert_many(slots)

                await db.user_integrations.update_one(
                    {"user_id": user["user_id"], "service": "ical"},
                    {"$set": {"last_synced_at": now.isoformat(), "metadata.event_count": len(events)}}
                )
                return {
                    "synced_count": len(events), "events_found": len(events),
                    "slots_detected": len(slots), "service": "ical", "last_sync": now.isoformat()
                }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"iCal sync error: {e}")
            raise HTTPException(status_code=500, detail=f"iCal sync failed: {str(e)[:200]}")

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
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

    await db.user_integrations.update_one(
        {"user_id": user["user_id"], "$or": [{"service": service}, {"provider": service}]},
        {"$set": {"last_synced_at": datetime.now(timezone.utc).isoformat()}}
    )

    return {"synced_count": synced_count, "service": service}

# ============== iCal INTEGRATION (URL-based, non-OAuth) ==============

@api_router.post("/integrations/ical/connect")
async def connect_ical(request: ICalConnectRequest, user: dict = Depends(get_current_user)):
    """Connect an iCal calendar via URL (.ics feed)."""
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
        raise HTTPException(status_code=400, detail=f"URL invalide ou format iCal non reconnu: {str(e)[:100]}")

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
        raise HTTPException(status_code=400, detail=f"URL invalide ou format iCal non reconnu: {str(e)[:100]}")

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
                dtend = component.get("dtend")
                if dtstart and dtend:
                    start = dtstart.dt
                    end = dtend.dt
                    # Handle date vs datetime
                    if hasattr(start, 'hour'):
                        if start.tzinfo is None:
                            start = start.replace(tzinfo=timezone.utc)
                        if end.tzinfo is None:
                            end = end.replace(tzinfo=timezone.utc)
                        if start < end_time and end > now:
                            events.append({
                                "summary": str(component.get("summary", "Événement")),
                                "start": start.isoformat(),
                                "end": end.isoformat(),
                            })

            # Detect free slots between events (same logic as Google Calendar)
            events.sort(key=lambda e: e["start"])
            slots = []
            settings = await db.notification_preferences.find_one(
                {"user_id": user["user_id"]}, {"_id": 0}
            )
            min_dur = (settings or {}).get("min_slot_duration", 5)
            max_dur = (settings or {}).get("max_slot_duration", 20)

            prev_end = now
            for event in events:
                event_start = datetime.fromisoformat(event["start"])
                gap_minutes = (event_start - prev_end).total_seconds() / 60
                if min_dur <= gap_minutes <= max_dur:
                    slots.append({
                        "user_id": user["user_id"],
                        "start_time": prev_end.isoformat(),
                        "end_time": event_start.isoformat(),
                        "duration_minutes": int(gap_minutes),
                        "source": "ical",
                        "detected_at": now.isoformat(),
                    })
                prev_end = max(prev_end, datetime.fromisoformat(event["end"]))

            # Store detected slots
            if slots:
                await db.detected_free_slots.delete_many({"user_id": user["user_id"], "source": "ical"})
                await db.detected_free_slots.insert_many(slots)

            await db.user_integrations.update_one(
                {"user_id": user["user_id"], "service": "ical"},
                {"$set": {"last_synced_at": now.isoformat(), "metadata.event_count": len(events)}}
            )

            return {
                "synced_count": len(events),
                "events_found": len(events),
                "slots_detected": len(slots),
                "service": "ical",
                "last_sync": now.isoformat(),
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"iCal sync error: {e}")
        raise HTTPException(status_code=500, detail=f"iCal sync failed: {str(e)[:200]}")

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
        raise HTTPException(status_code=400, detail=f"Impossible de valider le token: {str(e)[:100]}")

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
    """Get the next upcoming free slot."""
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

    response = await call_ai(f"summary_{user['user_id']}", system_msg, prompt)
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
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Auto-seed the database if empty"""
    count = await db.micro_actions.count_documents({})
    if count == 0:
        logger.info("Database empty, seeding micro-actions...")
        await seed_micro_actions()
        logger.info("Database seeded successfully!")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
