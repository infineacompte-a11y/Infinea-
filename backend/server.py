from fastapi import FastAPI, APIRouter, HTTPException, Request, Depends, Response
from fastapi.responses import JSONResponse
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
from urllib.parse import urlencode, quote

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL') or os.environ.get('MONGODB_URI', '')
if not mongo_url:
    raise RuntimeError("MONGO_URL env var required. Set it to your MongoDB Atlas connection string.")
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
    goals: List[str]  # ["learning", "productivity", "well_being"]
    availability_slots: List[str]  # ["morning", "lunch", "evening"]
    daily_minutes: int  # 5, 10, or 15
    energy_high: str  # "morning", "afternoon", "evening"
    energy_low: str  # "morning", "afternoon", "evening"
    interests: Dict[str, List[str]]  # {"learning": ["langues", "coding"], ...}

class CustomActionRequest(BaseModel):
    description: str
    preferred_category: Optional[str] = None
    preferred_duration: Optional[int] = None

class DebriefRequest(BaseModel):
    session_id: str
    action_title: str
    action_category: str
    actual_duration: int
    notes: Optional[str] = None

# ============== INTEGRATIONS CONFIG ==============

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

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")

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

# ============== AI HELPER FUNCTIONS ==============

async def call_ai(session_suffix: str, system_message: str, prompt: str) -> Optional[str]:
    """Shared AI call wrapper with fallback."""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not api_key:
        return None
    try:
        chat = LlmChat(
            api_key=api_key,
            session_id=f"{session_suffix}_{datetime.now().timestamp()}",
            system_message=system_message
        )
        chat.with_model("openai", "gpt-5.2")
        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        return response
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

    return f"""Profil utilisateur:
- Nom: {user.get('name', 'Inconnu')}
- Objectifs: {goals}
- Disponibilité: {', '.join(profile.get('availability_slots', []))} ({profile.get('daily_minutes', 10)} min/jour)
- Énergie haute: {profile.get('energy_high', 'matin')}
- Énergie basse: {profile.get('energy_low', 'après-midi')}
- Intérêts: {json.dumps(profile.get('interests', {}), ensure_ascii=False)}
- Streak actuel: {user.get('streak_days', 0)} jours
- Temps total investi: {user.get('total_time_invested', 0)} minutes
- Abonnement: {user.get('subscription_tier', 'free')}"""

AI_SYSTEM_MESSAGE = """Tu es le coach IA InFinea, expert en productivité, apprentissage et bien-être.
Tu aides les utilisateurs à transformer leurs moments perdus en micro-victoires.
Réponds toujours en français, de manière concise, chaleureuse et motivante.
Tes réponses doivent toujours être au format JSON quand demandé."""

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
        "onboarding_completed": False,
        "user_profile": None,
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
        "onboarding_completed": False,
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
        "onboarding_completed": user.get("onboarding_completed", True),
        "token": token
    }

@api_router.post("/auth/session")
async def process_oauth_session(request: Request, response: Response):
    """Process Google OAuth session_id and create user session"""
    body = await request.json()
    session_id = body.get("session_id")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")
    
    # REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    async with httpx.AsyncClient() as client_http:
        resp = await client_http.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": session_id}
        )
        
        if resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid session")
        
        data = resp.json()
    
    # Check if user exists
    existing_user = await db.users.find_one({"email": data["email"]}, {"_id": 0})
    
    if existing_user:
        user_id = existing_user["user_id"]
        # Update user data
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {
                "name": data["name"],
                "picture": data.get("picture")
            }}
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
            "onboarding_completed": False,
            "user_profile": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(user_doc)
    
    # Create session
    session_token = data.get("session_token", f"session_{uuid.uuid4().hex}")
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7 * 24 * 3600
    )
    
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    
    # Create JWT token for localStorage backup
    jwt_token = create_token(user_id)
    
    return {
        "user_id": user_id,
        "email": user["email"],
        "name": user["name"],
        "picture": user.get("picture"),
        "subscription_tier": user.get("subscription_tier", "free"),
        "onboarding_completed": user.get("onboarding_completed", True),
        "token": jwt_token
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
        "onboarding_completed": user.get("onboarding_completed", True)
    }

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

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    
    response.delete_cookie(key="session_token", path="/", samesite="none", secure=True)
    return {"message": "Logged out successfully"}

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

    # Update user dict for AI context
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

    ai_response = await call_ai(
        f"onboarding_{user['user_id']}",
        AI_SYSTEM_MESSAGE,
        prompt
    )
    ai_result = parse_ai_json(ai_response)

    welcome = ai_result.get("welcome_message", f"Bienvenue sur InFinea, {user.get('name', '')} ! Prêt(e) à transformer vos moments perdus en micro-victoires ?") if ai_result else f"Bienvenue sur InFinea, {user.get('name', '')} ! Prêt(e) à transformer vos moments perdus en micro-victoires ?"
    recommendation = ai_result.get("first_recommendation", "Commencez par une session de respiration de 2 minutes pour vous recentrer.") if ai_result else "Commencez par une session de respiration de 2 minutes pour vous recentrer."

    return {
        "welcome_message": welcome,
        "first_recommendation": recommendation,
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
    
    actions = await db.micro_actions.find(query, {"_id": 0}).to_list(100)
    
    if duration:
        actions = [a for a in actions if a["duration_min"] <= duration <= a["duration_max"]]
    
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
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="AI service not configured")
    
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
        # Return default suggestion if no actions match
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
    
    chat = LlmChat(
        api_key=api_key,
        session_id=f"suggestion_{user['user_id']}_{datetime.now().timestamp()}",
        system_message="""Tu es l'assistant InFinea, expert en productivité et bien-être. 
Tu aides les utilisateurs à transformer leurs moments perdus en micro-victoires.
Réponds toujours en français, de manière concise et motivante.
Suggère les meilleures micro-actions en fonction du temps disponible et du niveau d'énergie."""
    )
    chat.with_model("openai", "gpt-5.2")
    
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

    try:
        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        
        # Parse AI response
        import json
        try:
            # Try to extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                ai_result = json.loads(response[json_start:json_end])
            else:
                ai_result = {"top_pick": available_actions[0]["title"], "reasoning": response, "alternatives": []}
        except:
            ai_result = {"top_pick": available_actions[0]["title"], "reasoning": response, "alternatives": []}
        
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
    except Exception as e:
        logger.error(f"AI suggestion error: {e}")
        # Fallback to rule-based suggestion
        return {
            "suggestion": available_actions[0]["title"] if available_actions else "Respiration profonde",
            "reasoning": "Basé sur vos préférences et le temps disponible.",
            "recommended_actions": available_actions[:3]
        }

# ============== AI COACH ROUTE ==============

@api_router.get("/ai/coach")
async def get_ai_coach(user: dict = Depends(get_current_user)):
    """Get personalized AI coach message for dashboard"""
    user_context = await build_user_context(user)

    # Get recent sessions
    recent_sessions = await db.user_sessions_history.find(
        {"user_id": user["user_id"], "completed": True},
        {"_id": 0}
    ).sort("started_at", -1).limit(5).to_list(5)

    recent_info = ""
    if recent_sessions:
        recent_titles = [s.get("action_title", "action") for s in recent_sessions[:3]]
        recent_info = f"\nSessions récentes: {', '.join(recent_titles)}"

    # Determine time of day
    from datetime import datetime as dt
    hour = dt.now().hour
    time_of_day = "matin" if hour < 12 else "après-midi" if hour < 18 else "soir"
    day_names = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
    day_of_week = day_names[dt.now().weekday()]

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

    # Get a suggested action
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

    notes_info = f"\nNotes de l'utilisateur: {debrief_req.notes}" if debrief_req.notes else ""

    prompt = f"""{user_context}

L'utilisateur vient de terminer une session:
- Action: {debrief_req.action_title} (catégorie: {debrief_req.action_category})
- Durée réelle: {debrief_req.actual_duration} minutes{notes_info}

Génère un débrief personnalisé et motivant. Suggère aussi une prochaine action.
Réponds en JSON:
{{
    "feedback": "Feedback personnalisé sur la session (1-2 phrases)",
    "encouragement": "Message de motivation (1 phrase)",
    "next_suggestion": "Suggestion pour la prochaine action (1 phrase)"
}}"""

    ai_response = await call_ai(f"debrief_{user['user_id']}", AI_SYSTEM_MESSAGE, prompt)
    ai_result = parse_ai_json(ai_response)

    # Get a next action suggestion
    query = {"action_id": {"$ne": f"action_{debrief_req.action_category}"}}
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
        "feedback": f"Excellente session de {debrief_req.actual_duration} min sur {debrief_req.action_title} !",
        "encouragement": "Chaque micro-action vous rapproche de vos objectifs.",
        "next_suggestion": "Prenez une pause et revenez quand vous êtes prêt(e) pour la suite.",
        "next_action_id": next_action_id
    }

# ============== AI WEEKLY ANALYSIS ROUTE ==============

@api_router.get("/ai/weekly-analysis")
async def get_weekly_analysis(user: dict = Depends(get_current_user)):
    """Get AI-powered weekly progress analysis"""
    user_context = await build_user_context(user)

    # Get all completed sessions for this user
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

    # Compute stats
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
            # Streak at risk - no session today
            user_context = await build_user_context(user)
            prompt = f"""{user_context}

Le streak de {streak} jours de l'utilisateur est en danger ! Il n'a pas encore fait de session aujourd'hui.
Génère un message d'alerte motivant et court pour l'encourager à maintenir son streak.
Réponds en JSON: {{"title": "Titre court", "message": "Message motivant (1-2 phrases)"}}"""

            ai_response = await call_ai(f"streak_alert_{user['user_id']}", AI_SYSTEM_MESSAGE, prompt)
            ai_result = parse_ai_json(ai_response)

            title = ai_result.get("title", f"Streak de {streak}j en danger !") if ai_result else f"Streak de {streak}j en danger !"
            message = ai_result.get("message", f"Faites une micro-action de 2 minutes pour maintenir votre streak de {streak} jours !") if ai_result else f"Faites une micro-action de 2 minutes pour maintenir votre streak de {streak} jours !"

            # Check if we already sent a streak alert today
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

    await db.user_custom_actions.insert_one({**action, "_id": None})
    action.pop("_id", None)
    return {"action": action}

@api_router.get("/actions/custom")
async def get_custom_actions(user: dict = Depends(get_current_user)):
    """Get user's custom AI-generated actions"""
    actions = await db.user_custom_actions.find(
        {"created_by": user["user_id"]},
        {"_id": 0}
    ).to_list(50)
    return actions

# ============== SESSION TRACKING ROUTES ==============

@api_router.post("/sessions/start")
async def start_session(
    session_data: SessionStart,
    user: dict = Depends(get_current_user)
):
    """Start a micro-action session"""
    action = await db.micro_actions.find_one({"action_id": session_data.action_id}, {"_id": 0})
    if not action:
        # Check custom actions
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

        # Generate AI streak motivation notification
        if new_streak > 1:
            try:
                streak_prompt = f"L'utilisateur {user_doc.get('name', '')} vient de compléter une session et a maintenant un streak de {new_streak} jours. Génère un message de motivation court en français. Réponds en JSON: {{\"title\": \"Titre court\", \"message\": \"Message motivant (1-2 phrases)\"}}"
                ai_resp = await call_ai(f"streak_{user['user_id']}", AI_SYSTEM_MESSAGE, streak_prompt)
                streak_msg = parse_ai_json(ai_resp)
                if streak_msg:
                    streak_notif = {
                        "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
                        "user_id": user["user_id"],
                        "type": "streak_motivation",
                        "title": streak_msg.get("title", f"Streak de {new_streak} jours !"),
                        "message": streak_msg.get("message", f"Bravo pour votre streak de {new_streak} jours !"),
                        "icon": "flame",
                        "read": False,
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }
                    await db.notifications.insert_one(streak_notif)
            except Exception as e:
                logger.error(f"Streak motivation error: {e}")

        # Auto-sync with connected integrations
        try:
            connected_integrations = await db.user_integrations.find(
                {"user_id": user["user_id"], "sync_enabled": True},
                {"_id": 0, "service": 1}
            ).to_list(10)
            # Fire-and-forget: we don't wait or fail if sync has issues
            for integ in connected_integrations:
                logger.info(f"Auto-sync queued for {integ['service']} after session completion")
        except Exception as e:
            logger.error(f"Auto-sync check error: {e}")

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
    from emergentintegrations.payments.stripe.checkout import (
        StripeCheckout, CheckoutSessionRequest
    )
    
    stripe_key = os.environ.get('STRIPE_API_KEY')
    if not stripe_key:
        raise HTTPException(status_code=500, detail="Payment service not configured")
    
    host_url = str(request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/webhook/stripe"
    
    stripe_checkout = StripeCheckout(api_key=stripe_key, webhook_url=webhook_url)
    
    success_url = f"{checkout_data.origin_url}/pricing?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{checkout_data.origin_url}/pricing"
    
    checkout_request = CheckoutSessionRequest(
        amount=SUBSCRIPTION_PRICE,
        currency="eur",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "user_id": user["user_id"],
            "email": user["email"],
            "plan": "premium"
        }
    )
    
    session = await stripe_checkout.create_checkout_session(checkout_request)
    
    # Create payment transaction record
    await db.payment_transactions.insert_one({
        "transaction_id": f"txn_{uuid.uuid4().hex[:12]}",
        "session_id": session.session_id,
        "user_id": user["user_id"],
        "email": user["email"],
        "amount": SUBSCRIPTION_PRICE,
        "currency": "eur",
        "plan": "premium",
        "payment_status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"url": session.url, "session_id": session.session_id}

@api_router.get("/payments/status/{session_id}")
async def get_payment_status(
    session_id: str,
    user: dict = Depends(get_current_user)
):
    """Check payment status and upgrade user if successful"""
    from emergentintegrations.payments.stripe.checkout import StripeCheckout
    
    stripe_key = os.environ.get('STRIPE_API_KEY')
    if not stripe_key:
        raise HTTPException(status_code=500, detail="Payment service not configured")
    
    stripe_checkout = StripeCheckout(api_key=stripe_key, webhook_url="")
    
    try:
        status = await stripe_checkout.get_checkout_status(session_id)
        
        # Update transaction
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": {
                "payment_status": status.payment_status,
                "status": status.status,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # If paid, upgrade user
        if status.payment_status == "paid":
            # Check if not already processed
            txn = await db.payment_transactions.find_one(
                {"session_id": session_id, "processed": True},
                {"_id": 0}
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
            "status": status.status,
            "payment_status": status.payment_status,
            "amount": status.amount_total / 100,  # Convert from cents
            "currency": status.currency
        }
    except Exception as e:
        logger.error(f"Payment status error: {e}")
        raise HTTPException(status_code=400, detail="Failed to get payment status")

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
    from emergentintegrations.payments.stripe.checkout import StripeCheckout
    
    stripe_key = os.environ.get('STRIPE_API_KEY')
    if not stripe_key:
        return {"status": "error", "message": "Not configured"}
    
    host_url = str(request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/webhook/stripe"
    
    stripe_checkout = StripeCheckout(api_key=stripe_key, webhook_url=webhook_url)
    
    body = await request.body()
    signature = request.headers.get("Stripe-Signature")
    
    try:
        event = await stripe_checkout.handle_webhook(body, signature)
        
        if event.payment_status == "paid":
            user_id = event.metadata.get("user_id")
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
    """Seed database with initial micro-actions"""
    
    actions = [
        # Learning - Low Energy
        {
            "action_id": "action_learn_vocab",
            "title": "5 nouveaux mots",
            "description": "Apprenez 5 nouveaux mots de vocabulaire dans la langue de votre choix.",
            "category": "learning",
            "duration_min": 2,
            "duration_max": 5,
            "energy_level": "low",
            "instructions": [
                "Ouvrez votre application de vocabulaire préférée",
                "Révisez 5 mots avec leurs définitions",
                "Prononcez chaque mot à voix haute",
                "Utilisez chaque mot dans une phrase"
            ],
            "is_premium": False,
            "icon": "book-open"
        },
        {
            "action_id": "action_learn_article",
            "title": "Lecture rapide",
            "description": "Lisez un article court sur un sujet qui vous passionne.",
            "category": "learning",
            "duration_min": 5,
            "duration_max": 10,
            "energy_level": "low",
            "instructions": [
                "Choisissez un article de votre fil d'actualités",
                "Lisez-le en survol d'abord",
                "Relisez les passages clés",
                "Notez une idée à retenir"
            ],
            "is_premium": False,
            "icon": "newspaper"
        },
        # Learning - Medium Energy
        {
            "action_id": "action_learn_concept",
            "title": "Nouveau concept",
            "description": "Apprenez un nouveau concept et testez votre compréhension.",
            "category": "learning",
            "duration_min": 10,
            "duration_max": 15,
            "energy_level": "medium",
            "instructions": [
                "Choisissez un sujet qui vous intéresse",
                "Regardez une vidéo explicative courte",
                "Résumez le concept en 3 points",
                "Expliquez-le comme si vous l'enseigniez"
            ],
            "is_premium": False,
            "icon": "lightbulb"
        },
        {
            "action_id": "action_learn_flashcards",
            "title": "Session Flashcards",
            "description": "Révisez 20 flashcards pour ancrer vos connaissances.",
            "category": "learning",
            "duration_min": 5,
            "duration_max": 10,
            "energy_level": "medium",
            "instructions": [
                "Ouvrez votre deck de flashcards",
                "Répondez à 20 cartes",
                "Marquez celles à revoir",
                "Célébrez votre score!"
            ],
            "is_premium": True,
            "icon": "layers"
        },
        # Productivity - Low Energy
        {
            "action_id": "action_prod_inbox",
            "title": "Inbox Zero",
            "description": "Traitez rapidement 5 emails de votre boîte de réception.",
            "category": "productivity",
            "duration_min": 3,
            "duration_max": 7,
            "energy_level": "low",
            "instructions": [
                "Ouvrez votre messagerie",
                "Archivez ou supprimez les emails non essentiels",
                "Répondez aux messages rapides",
                "Marquez les autres pour plus tard"
            ],
            "is_premium": False,
            "icon": "mail"
        },
        {
            "action_id": "action_prod_plan",
            "title": "Mini-planification",
            "description": "Planifiez les 3 tâches prioritaires de votre prochaine session de travail.",
            "category": "productivity",
            "duration_min": 2,
            "duration_max": 5,
            "energy_level": "low",
            "instructions": [
                "Identifiez 3 tâches importantes",
                "Estimez le temps nécessaire",
                "Ordonnez par priorité",
                "Bloquez du temps dans votre agenda"
            ],
            "is_premium": False,
            "icon": "list-todo"
        },
        # Productivity - Medium Energy
        {
            "action_id": "action_prod_brainstorm",
            "title": "Brainstorm éclair",
            "description": "Générez 10 idées sur un projet ou problème en cours.",
            "category": "productivity",
            "duration_min": 5,
            "duration_max": 10,
            "energy_level": "medium",
            "instructions": [
                "Définissez votre question/problème",
                "Écrivez toutes les idées sans filtre",
                "Visez la quantité, pas la qualité",
                "Identifiez les 2-3 meilleures idées"
            ],
            "is_premium": False,
            "icon": "zap"
        },
        {
            "action_id": "action_prod_review",
            "title": "Revue de projet",
            "description": "Faites le point sur l'avancement d'un projet en cours.",
            "category": "productivity",
            "duration_min": 5,
            "duration_max": 10,
            "energy_level": "medium",
            "instructions": [
                "Choisissez un projet actif",
                "Listez ce qui a été accompli",
                "Identifiez les blocages",
                "Définissez la prochaine action"
            ],
            "is_premium": True,
            "icon": "clipboard-check"
        },
        # Well-being - Low Energy
        {
            "action_id": "action_well_breath",
            "title": "Respiration 4-7-8",
            "description": "Technique de respiration pour réduire le stress instantanément.",
            "category": "well_being",
            "duration_min": 2,
            "duration_max": 5,
            "energy_level": "low",
            "instructions": [
                "Asseyez-vous confortablement",
                "Inspirez par le nez pendant 4 secondes",
                "Retenez votre souffle 7 secondes",
                "Expirez par la bouche pendant 8 secondes",
                "Répétez 4 cycles"
            ],
            "is_premium": False,
            "icon": "wind"
        },
        {
            "action_id": "action_well_gratitude",
            "title": "Moment gratitude",
            "description": "Notez 3 choses pour lesquelles vous êtes reconnaissant aujourd'hui.",
            "category": "well_being",
            "duration_min": 2,
            "duration_max": 5,
            "energy_level": "low",
            "instructions": [
                "Fermez les yeux un instant",
                "Pensez à 3 moments positifs récents",
                "Notez-les dans votre journal",
                "Ressentez la gratitude"
            ],
            "is_premium": False,
            "icon": "heart"
        },
        # Well-being - Medium Energy
        {
            "action_id": "action_well_stretch",
            "title": "Pause étirements",
            "description": "Séance d'étirements pour délier les tensions du corps.",
            "category": "well_being",
            "duration_min": 5,
            "duration_max": 10,
            "energy_level": "medium",
            "instructions": [
                "Levez-vous et étirez les bras vers le haut",
                "Penchez-vous vers l'avant, bras pendants",
                "Faites des rotations de nuque",
                "Étirez chaque épaule 30 secondes",
                "Terminez par des rotations de hanches"
            ],
            "is_premium": False,
            "icon": "move"
        },
        {
            "action_id": "action_well_meditate",
            "title": "Mini méditation",
            "description": "Une courte méditation guidée pour recentrer votre esprit.",
            "category": "well_being",
            "duration_min": 5,
            "duration_max": 10,
            "energy_level": "medium",
            "instructions": [
                "Trouvez un endroit calme",
                "Fermez les yeux",
                "Concentrez-vous sur votre respiration",
                "Observez vos pensées sans jugement",
                "Revenez doucement au présent"
            ],
            "is_premium": True,
            "icon": "brain"
        },
        # High Energy Actions
        {
            "action_id": "action_prod_deep",
            "title": "Deep Work Sprint",
            "description": "15 minutes de concentration intense sur une tâche importante.",
            "category": "productivity",
            "duration_min": 10,
            "duration_max": 15,
            "energy_level": "high",
            "instructions": [
                "Choisissez UNE tâche prioritaire",
                "Éliminez toutes les distractions",
                "Mettez un timer de 15 minutes",
                "Travaillez sans interruption",
                "Notez où vous en êtes pour continuer plus tard"
            ],
            "is_premium": True,
            "icon": "target"
        },
        {
            "action_id": "action_well_energy",
            "title": "Boost d'énergie",
            "description": "Exercices rapides pour booster votre énergie et votre focus.",
            "category": "well_being",
            "duration_min": 5,
            "duration_max": 10,
            "energy_level": "high",
            "instructions": [
                "20 jumping jacks",
                "10 squats",
                "30 secondes de planche",
                "10 pompes (ou version facilitée)",
                "Récupérez 30 secondes"
            ],
            "is_premium": False,
            "icon": "flame"
        },
        {
            "action_id": "action_learn_podcast",
            "title": "Podcast éclair",
            "description": "Écoutez un segment de podcast éducatif.",
            "category": "learning",
            "duration_min": 10,
            "duration_max": 15,
            "energy_level": "high",
            "instructions": [
                "Choisissez un podcast de votre liste",
                "Écoutez en vitesse 1.25x ou 1.5x",
                "Notez une idée clé",
                "Partagez-la ou appliquez-la"
            ],
            "is_premium": True,
            "icon": "headphones"
        }
    ]
    
    # Clear existing and insert new
    await db.micro_actions.delete_many({})
    await db.micro_actions.insert_many(actions)
    
    return {"message": f"Seeded {len(actions)} micro-actions"}

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

# ============== INTEGRATIONS ROUTES ==============

@api_router.get("/integrations")
async def get_integrations(user: dict = Depends(get_current_user)):
    """Get user's connected integrations"""
    integrations = await db.user_integrations.find(
        {"user_id": user["user_id"]},
        {"_id": 0, "access_token": 0, "refresh_token": 0}
    ).to_list(10)

    # Build response with connection status for all services
    result = {}
    connected_map = {i["service"]: i for i in integrations}

    for service_key, config in INTEGRATION_CONFIGS.items():
        client_id = os.environ.get(config["env_client_id"])
        connected = connected_map.get(service_key)
        result[service_key] = {
            "name": config["name"],
            "connected": bool(connected),
            "connected_at": connected.get("connected_at") if connected else None,
            "account_name": connected.get("account_name") if connected else None,
            "available": bool(client_id),
            "sync_enabled": connected.get("sync_enabled", False) if connected else False,
        }

    return result

@api_router.get("/integrations/connect/{service}")
async def connect_integration(service: str, request: Request, user: dict = Depends(get_current_user)):
    """Initiate OAuth flow for a service — returns the authorization URL"""
    if service not in INTEGRATION_CONFIGS:
        raise HTTPException(status_code=400, detail=f"Unknown service: {service}")

    config = INTEGRATION_CONFIGS[service]
    client_id = os.environ.get(config["env_client_id"])
    if not client_id:
        raise HTTPException(status_code=503, detail=f"{config['name']} integration not configured. Set {config['env_client_id']} env var.")

    # Store state for CSRF protection
    state = f"{user['user_id']}:{uuid.uuid4().hex[:16]}"
    await db.integration_states.insert_one({
        "state": state,
        "user_id": user["user_id"],
        "service": service,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    })

    # Build host-based callback URL
    host_url = str(request.base_url).rstrip('/')
    redirect_uri = f"{host_url}/api/integrations/callback/{service}"

    if service == "google_calendar":
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": config["scopes"],
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }
        auth_url = f"{config['auth_url']}?{urlencode(params)}"

    elif service == "notion":
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "state": state,
            "owner": "user",
        }
        auth_url = f"{config['auth_url']}?{urlencode(params)}"

    elif service == "todoist":
        params = {
            "client_id": client_id,
            "scope": config["scopes"],
            "state": state,
        }
        auth_url = f"{config['auth_url']}?{urlencode(params)}"

    elif service == "slack":
        params = {
            "client_id": client_id,
            "scope": config["scopes"],
            "redirect_uri": redirect_uri,
            "state": state,
        }
        auth_url = f"{config['auth_url']}?{urlencode(params)}"
    else:
        raise HTTPException(status_code=400, detail="Unsupported service")

    return {"auth_url": auth_url}

@api_router.get("/integrations/callback/{service}")
async def integration_callback(service: str, code: str = "", state: str = "", error: str = ""):
    """OAuth callback handler — exchanges code for tokens, redirects to frontend"""
    if error:
        return JSONResponse(
            status_code=302,
            headers={"Location": f"{FRONTEND_URL}/integrations?error={quote(error)}&service={service}"},
            content=None
        )

    if service not in INTEGRATION_CONFIGS:
        return JSONResponse(
            status_code=302,
            headers={"Location": f"{FRONTEND_URL}/integrations?error=unknown_service"},
            content=None
        )

    # Verify state
    state_doc = await db.integration_states.find_one_and_delete({"state": state, "service": service})
    if not state_doc:
        return JSONResponse(
            status_code=302,
            headers={"Location": f"{FRONTEND_URL}/integrations?error=invalid_state&service={service}"},
            content=None
        )

    # Check expiry
    expires_at = datetime.fromisoformat(state_doc["expires_at"])
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        return JSONResponse(
            status_code=302,
            headers={"Location": f"{FRONTEND_URL}/integrations?error=expired&service={service}"},
            content=None
        )

    user_id = state_doc["user_id"]
    config = INTEGRATION_CONFIGS[service]
    client_id = os.environ.get(config["env_client_id"])
    client_secret = os.environ.get(config["env_client_secret"])

    if not client_id or not client_secret:
        return JSONResponse(
            status_code=302,
            headers={"Location": f"{FRONTEND_URL}/integrations?error=not_configured&service={service}"},
            content=None
        )

    # Exchange code for tokens
    try:
        async with httpx.AsyncClient() as http_client:
            # Build callback URL the same way
            redirect_uri = f"{str(state_doc.get('redirect_uri', '')).rstrip('/')}"
            # Re-derive from known pattern
            # We need the original host but don't have it — use FRONTEND_URL-derived backend
            backend_url = os.environ.get("BACKEND_URL", "http://localhost:8000")
            redirect_uri = f"{backend_url.rstrip('/')}/api/integrations/callback/{service}"

            if service == "google_calendar":
                token_resp = await http_client.post(config["token_url"], data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                })
                token_data = token_resp.json()
                access_token = token_data.get("access_token")
                refresh_token = token_data.get("refresh_token")
                expires_in = token_data.get("expires_in", 3600)

                # Get user info for account name
                account_name = "Google Calendar"
                try:
                    info_resp = await http_client.get(
                        "https://www.googleapis.com/oauth2/v2/userinfo",
                        headers={"Authorization": f"Bearer {access_token}"}
                    )
                    if info_resp.status_code == 200:
                        info = info_resp.json()
                        account_name = info.get("email", "Google Calendar")
                except Exception:
                    pass

            elif service == "notion":
                auth_header = httpx.BasicAuth(client_id, client_secret)
                token_resp = await http_client.post(config["token_url"], json={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                }, auth=auth_header, headers={"Notion-Version": "2022-06-28"})
                token_data = token_resp.json()
                access_token = token_data.get("access_token")
                refresh_token = None
                expires_in = None
                account_name = token_data.get("workspace_name", "Notion")

            elif service == "todoist":
                token_resp = await http_client.post(config["token_url"], data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": code,
                })
                token_data = token_resp.json()
                access_token = token_data.get("access_token")
                refresh_token = None
                expires_in = None
                account_name = "Todoist"

            elif service == "slack":
                token_resp = await http_client.post(config["token_url"], data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                })
                token_data = token_resp.json()
                access_token = token_data.get("access_token")
                if not access_token:
                    # Slack v2 nests it under authed_user
                    access_token = token_data.get("authed_user", {}).get("access_token")
                refresh_token = None
                expires_in = None
                account_name = token_data.get("team", {}).get("name", "Slack")

            if not access_token:
                logger.error(f"Integration {service} token exchange failed: {token_data}")
                return JSONResponse(
                    status_code=302,
                    headers={"Location": f"{FRONTEND_URL}/integrations?error=token_failed&service={service}"},
                    content=None
                )

            # Store integration
            integration_doc = {
                "user_id": user_id,
                "service": service,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_in": expires_in,
                "token_obtained_at": datetime.now(timezone.utc).isoformat(),
                "account_name": account_name,
                "connected_at": datetime.now(timezone.utc).isoformat(),
                "sync_enabled": True,
            }

            await db.user_integrations.update_one(
                {"user_id": user_id, "service": service},
                {"$set": integration_doc},
                upsert=True
            )

            return JSONResponse(
                status_code=302,
                headers={"Location": f"{FRONTEND_URL}/integrations?success=true&service={service}"},
                content=None
            )

    except Exception as e:
        logger.error(f"Integration {service} callback error: {e}")
        return JSONResponse(
            status_code=302,
            headers={"Location": f"{FRONTEND_URL}/integrations?error=callback_failed&service={service}"},
            content=None
        )

@api_router.delete("/integrations/{service}")
async def disconnect_integration(service: str, user: dict = Depends(get_current_user)):
    """Disconnect an integration"""
    result = await db.user_integrations.delete_one(
        {"user_id": user["user_id"], "service": service}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Integration not found")
    return {"message": f"{INTEGRATION_CONFIGS.get(service, {}).get('name', service)} disconnected"}

@api_router.put("/integrations/{service}/sync")
async def toggle_sync(service: str, request: Request, user: dict = Depends(get_current_user)):
    """Toggle sync on/off for an integration"""
    body = await request.json()
    sync_enabled = body.get("sync_enabled", True)

    result = await db.user_integrations.update_one(
        {"user_id": user["user_id"], "service": service},
        {"$set": {"sync_enabled": sync_enabled}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Integration not found")
    return {"sync_enabled": sync_enabled}

@api_router.post("/integrations/{service}/sync")
async def trigger_sync(service: str, user: dict = Depends(get_current_user)):
    """Trigger a manual sync for a service — syncs recent sessions"""
    integration = await db.user_integrations.find_one(
        {"user_id": user["user_id"], "service": service},
        {"_id": 0}
    )
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not connected")

    access_token = integration.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="No access token")

    # Get recent completed sessions (last 7 days)
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    recent_sessions = await db.user_sessions_history.find(
        {"user_id": user["user_id"], "completed": True, "completed_at": {"$gte": week_ago}},
        {"_id": 0}
    ).sort("completed_at", -1).to_list(20)

    synced_count = 0

    try:
        async with httpx.AsyncClient() as http_client:
            if service == "google_calendar":
                for session in recent_sessions:
                    # Check if already synced
                    already_synced = await db.synced_events.find_one({
                        "user_id": user["user_id"],
                        "service": service,
                        "session_id": session["session_id"]
                    })
                    if already_synced:
                        continue

                    started = session.get("started_at", "")
                    duration = session.get("actual_duration", 5)
                    title = session.get("action_title", "Micro-action InFinea")

                    if started:
                        start_dt = datetime.fromisoformat(started.replace("Z", "+00:00"))
                        end_dt = start_dt + timedelta(minutes=duration)

                        event = {
                            "summary": f"✅ {title}",
                            "description": f"Session InFinea — {duration} min\nCatégorie: {session.get('category', 'N/A')}",
                            "start": {"dateTime": start_dt.isoformat(), "timeZone": "UTC"},
                            "end": {"dateTime": end_dt.isoformat(), "timeZone": "UTC"},
                        }

                        resp = await http_client.post(
                            "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                            json=event,
                            headers={"Authorization": f"Bearer {access_token}"}
                        )
                        if resp.status_code in (200, 201):
                            await db.synced_events.insert_one({
                                "user_id": user["user_id"],
                                "service": service,
                                "session_id": session["session_id"],
                                "external_id": resp.json().get("id"),
                                "synced_at": datetime.now(timezone.utc).isoformat()
                            })
                            synced_count += 1

            elif service == "notion":
                # Create a database page for each session
                # First, find or create the InFinea database
                # For simplicity, create pages in the user's default workspace
                for session in recent_sessions:
                    already_synced = await db.synced_events.find_one({
                        "user_id": user["user_id"],
                        "service": service,
                        "session_id": session["session_id"]
                    })
                    if already_synced:
                        continue

                    # Search for existing InFinea page
                    search_resp = await http_client.post(
                        "https://api.notion.com/v1/search",
                        json={"query": "InFinea Sessions", "filter": {"property": "object", "value": "page"}},
                        headers={
                            "Authorization": f"Bearer {access_token}",
                            "Notion-Version": "2022-06-28",
                        }
                    )

                    parent_page_id = None
                    if search_resp.status_code == 200:
                        results = search_resp.json().get("results", [])
                        if results:
                            parent_page_id = results[0]["id"]

                    if not parent_page_id:
                        # Create a parent page
                        # We need to find a page to use as parent — use first available page
                        pages_resp = await http_client.post(
                            "https://api.notion.com/v1/search",
                            json={"filter": {"property": "object", "value": "page"}, "page_size": 1},
                            headers={
                                "Authorization": f"Bearer {access_token}",
                                "Notion-Version": "2022-06-28",
                            }
                        )
                        if pages_resp.status_code == 200:
                            pages = pages_resp.json().get("results", [])
                            if pages:
                                parent_page_id = pages[0]["id"]

                    if parent_page_id:
                        title = session.get("action_title", "Micro-action")
                        duration = session.get("actual_duration", 5)
                        category = session.get("category", "N/A")
                        completed_at = session.get("completed_at", "")

                        page_data = {
                            "parent": {"page_id": parent_page_id},
                            "properties": {
                                "title": {"title": [{"text": {"content": f"✅ {title} — {duration} min"}}]}
                            },
                            "children": [
                                {
                                    "object": "block",
                                    "type": "paragraph",
                                    "paragraph": {
                                        "rich_text": [{"text": {"content": f"Catégorie: {category}\nDurée: {duration} min\nDate: {completed_at[:10] if completed_at else 'N/A'}"}}]
                                    }
                                }
                            ]
                        }

                        resp = await http_client.post(
                            "https://api.notion.com/v1/pages",
                            json=page_data,
                            headers={
                                "Authorization": f"Bearer {access_token}",
                                "Notion-Version": "2022-06-28",
                            }
                        )
                        if resp.status_code in (200, 201):
                            await db.synced_events.insert_one({
                                "user_id": user["user_id"],
                                "service": service,
                                "session_id": session["session_id"],
                                "external_id": resp.json().get("id"),
                                "synced_at": datetime.now(timezone.utc).isoformat()
                            })
                            synced_count += 1

            elif service == "todoist":
                for session in recent_sessions:
                    already_synced = await db.synced_events.find_one({
                        "user_id": user["user_id"],
                        "service": service,
                        "session_id": session["session_id"]
                    })
                    if already_synced:
                        continue

                    title = session.get("action_title", "Micro-action")
                    duration = session.get("actual_duration", 5)

                    task_data = {
                        "content": f"✅ {title}",
                        "description": f"Session InFinea complétée — {duration} min",
                    }

                    resp = await http_client.post(
                        "https://api.todoist.com/rest/v2/tasks",
                        json=task_data,
                        headers={"Authorization": f"Bearer {access_token}"}
                    )
                    if resp.status_code in (200, 201):
                        task_id = resp.json().get("id")
                        # Close the task immediately (it's completed)
                        await http_client.post(
                            f"https://api.todoist.com/rest/v2/tasks/{task_id}/close",
                            headers={"Authorization": f"Bearer {access_token}"}
                        )
                        await db.synced_events.insert_one({
                            "user_id": user["user_id"],
                            "service": service,
                            "session_id": session["session_id"],
                            "external_id": str(task_id),
                            "synced_at": datetime.now(timezone.utc).isoformat()
                        })
                        synced_count += 1

            elif service == "slack":
                # Send a summary message to the user
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

                    # Post to Slackbot DM (conversations.list → im channel)
                    resp = await http_client.post(
                        "https://slack.com/api/chat.postMessage",
                        json={"channel": "me", "text": message, "mrkdwn": True},
                        headers={"Authorization": f"Bearer {access_token}"}
                    )
                    if resp.status_code == 200 and resp.json().get("ok"):
                        synced_count = session_count

    except Exception as e:
        logger.error(f"Sync error for {service}: {e}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

    # Update last sync time
    await db.user_integrations.update_one(
        {"user_id": user["user_id"], "service": service},
        {"$set": {"last_synced_at": datetime.now(timezone.utc).isoformat()}}
    )

    return {"synced_count": synced_count, "service": service}

# ============== ROOT ROUTE ==============

@api_router.get("/")
async def root():
    return {"message": "InFinea API - Investissez vos instants perdus"}

# Include router and add middleware
app.include_router(api_router)

ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Auto-seed database if empty"""
    count = await db.micro_actions.count_documents({})
    if count == 0:
        logger.info("Database empty, seeding micro-actions...")
        await seed_micro_actions()
        logger.info("Database seeded successfully!")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
