"""
InFinea — Auth routes.
Registration, login, Google OAuth 2.0 (native), profile, and logout.
"""

from fastapi import APIRouter, HTTPException, Request, Response, Depends
from fastapi.responses import RedirectResponse
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode
import uuid
import secrets
import httpx
import os
import logging

from database import db
from config import JWT_EXPIRATION_HOURS
from auth import create_token, get_current_user, hash_password, verify_password
from models import UserCreate, UserLogin

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)

# --------------- Google OAuth 2.0 (native) ---------------

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://infinea.vercel.app").rstrip("/")
BACKEND_URL = os.environ.get("BACKEND_URL", "https://infinea-api.onrender.com").rstrip("/")

GOOGLE_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_ENDPOINT = "https://www.googleapis.com/oauth2/v2/userinfo"


@router.get("/auth/google")
async def get_google_auth_url():
    """Return the Google OAuth 2.0 authorization URL."""
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google OAuth non configuré")

    state = secrets.token_urlsafe(32)
    await db.oauth_states.insert_one({
        "state": state,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
    })

    params = urlencode({
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": f"{BACKEND_URL}/api/auth/google/callback",
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "state": state,
        "prompt": "select_account",
    })

    return {"auth_url": f"{GOOGLE_AUTH_ENDPOINT}?{params}"}


@router.get("/auth/google/callback")
async def google_oauth_callback(
    code: str = None,
    state: str = None,
    error: str = None,
):
    """Handle Google OAuth 2.0 callback — exchange code, store session, redirect to frontend."""
    if error:
        logger.warning(f"Google OAuth denied: {error}")
        return RedirectResponse(url=f"{FRONTEND_URL}/login?error=oauth_denied")

    if not code or not state:
        return RedirectResponse(url=f"{FRONTEND_URL}/login?error=missing_params")

    # Validate CSRF state
    state_doc = await db.oauth_states.find_one_and_delete({"state": state})
    if not state_doc:
        return RedirectResponse(url=f"{FRONTEND_URL}/login?error=invalid_state")

    if state_doc.get("expires_at", "") < datetime.now(timezone.utc).isoformat():
        return RedirectResponse(url=f"{FRONTEND_URL}/login?error=state_expired")

    # Exchange authorization code for tokens
    callback_url = f"{BACKEND_URL}/api/auth/google/callback"

    try:
        async with httpx.AsyncClient() as http:
            token_resp = await http.post(GOOGLE_TOKEN_ENDPOINT, data={
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": callback_url,
            })

            if token_resp.status_code != 200:
                logger.error(f"Google token exchange failed: {token_resp.text}")
                return RedirectResponse(url=f"{FRONTEND_URL}/login?error=token_failed")

            access_token = token_resp.json().get("access_token")
            if not access_token:
                return RedirectResponse(url=f"{FRONTEND_URL}/login?error=no_token")

            # Fetch Google user profile
            userinfo_resp = await http.get(
                GOOGLE_USERINFO_ENDPOINT,
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if userinfo_resp.status_code != 200:
                logger.error(f"Google userinfo failed: {userinfo_resp.text}")
                return RedirectResponse(url=f"{FRONTEND_URL}/login?error=profile_failed")

            google_user = userinfo_resp.json()

    except Exception as e:
        logger.error(f"Google OAuth callback error: {e}")
        return RedirectResponse(url=f"{FRONTEND_URL}/login?error=server_error")

    # Store pending session for the frontend to pick up via POST /api/auth/session
    session_id = f"gauth_{secrets.token_urlsafe(32)}"
    await db.oauth_pending_sessions.insert_one({
        "session_id": session_id,
        "email": google_user.get("email"),
        "name": google_user.get("name", ""),
        "picture": google_user.get("picture"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
    })

    return RedirectResponse(url=f"{FRONTEND_URL}/dashboard#session_id={session_id}")


# --------------- Registration & Login ---------------

@router.post("/auth/register")
async def register(user_data: UserCreate, response: Response):
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
        "created_at": datetime.now(timezone.utc).isoformat(),
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
        max_age=JWT_EXPIRATION_HOURS * 3600,
    )

    return {
        "user_id": user_id,
        "email": user_data.email,
        "name": user_data.name,
        "subscription_tier": "free",
        "token": token,
    }


@router.post("/auth/login")
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
        max_age=JWT_EXPIRATION_HOURS * 3600,
    )

    return {
        "user_id": user["user_id"],
        "email": user["email"],
        "name": user["name"],
        "picture": user.get("picture"),
        "subscription_tier": user.get("subscription_tier", "free"),
        "token": token,
    }


# --------------- OAuth Session Validation ---------------

@router.post("/auth/session")
async def process_oauth_session(request: Request, response: Response):
    """Validate OAuth session_id and create/login user."""
    body = await request.json()
    session_id = body.get("session_id")

    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")

    # Look up pending session from our own database (no external dependency)
    data = await db.oauth_pending_sessions.find_one_and_delete(
        {"session_id": session_id}
    )

    if not data:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    if data.get("expires_at", "") < datetime.now(timezone.utc).isoformat():
        raise HTTPException(status_code=401, detail="Session expired")

    # Create or update user
    existing_user = await db.users.find_one({"email": data["email"]}, {"_id": 0})

    if existing_user:
        user_id = existing_user["user_id"]
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"name": data["name"], "picture": data.get("picture")}},
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
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.users.insert_one(user_doc)

    # Create session
    session_token = f"session_{uuid.uuid4().hex}"
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    await db.user_sessions.insert_one(
        {
            "user_id": user_id,
            "session_token": session_token,
            "expires_at": expires_at.isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )

    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7 * 24 * 3600,
    )

    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    jwt_token = create_token(user_id)

    return {
        "user_id": user_id,
        "email": user["email"],
        "name": user["name"],
        "picture": user.get("picture"),
        "subscription_tier": user.get("subscription_tier", "free"),
        "token": jwt_token,
    }


# --------------- Profile & Logout ---------------

@router.get("/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    return {
        "user_id": user["user_id"],
        "email": user["email"],
        "name": user["name"],
        "picture": user.get("picture"),
        "subscription_tier": user.get("subscription_tier", "free"),
        "total_time_invested": user.get("total_time_invested", 0),
        "streak_days": user.get("streak_days", 0),
    }


@router.post("/auth/logout")
async def logout(request: Request, response: Response):
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})

    response.delete_cookie(key="session_token", path="/", samesite="none", secure=True)
    return {"message": "Logged out successfully"}
