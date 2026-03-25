"""
InFinea — Auth routes.
Registration, login, Google OAuth, session management, logout.
"""

import os
import uuid
import urllib.parse
from datetime import datetime, timezone, timedelta

import httpx
from fastapi import APIRouter, HTTPException, Request, Response, Depends

from config import JWT_EXPIRATION_HOURS, ACCESS_TOKEN_EXPIRATION_HOURS, logger, limiter
from database import db
from auth import (
    create_token, verify_token, get_current_user,
    hash_password, verify_password,
    create_refresh_token, rotate_refresh_token, revoke_refresh_tokens,
)
from models import UserCreate, UserLogin

try:
    from integrations.encryption import encrypt_token
except ImportError:
    encrypt_token = None

router = APIRouter()


async def generate_username(email: str) -> str:
    """Derive a unique username from an email address.
    john.doe@gmail.com → john.doe (or john.doe.1 if taken)."""
    import re
    local = email.split("@")[0].lower()
    # Normalize: keep alphanumeric and dots, replace everything else with dot
    base = re.sub(r"[^a-z0-9.]", ".", local)
    # Remove consecutive dots and leading/trailing dots
    base = re.sub(r"\.{2,}", ".", base).strip(".")
    if not base:
        base = "user"

    # Check uniqueness
    candidate = base
    suffix = 0
    while await db.users.find_one({"username": candidate}, {"_id": 1}):
        suffix += 1
        candidate = f"{base}.{suffix}"
    return candidate


@router.post("/auth/register")
@limiter.limit("3/minute")
async def register(request: Request, user_data: UserCreate, response: Response):
    # Check if user exists
    existing = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = f"user_{uuid.uuid4().hex[:12]}"
    username = await generate_username(user_data.email)
    user_doc = {
        "user_id": user_id,
        "email": user_data.email,
        "name": user_data.name,
        "username": username,
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
    refresh = await create_refresh_token(user_id)
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=ACCESS_TOKEN_EXPIRATION_HOURS * 3600,
    )

    return {
        "user_id": user_id,
        "email": user_data.email,
        "name": user_data.name,
        "username": username,
        "subscription_tier": "free",
        "token": token,
        "refresh_token": refresh,
    }

@router.post("/auth/login")
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
    refresh = await create_refresh_token(user["user_id"])
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=ACCESS_TOKEN_EXPIRATION_HOURS * 3600,
    )

    return {
        "user_id": user["user_id"],
        "email": user["email"],
        "name": user["name"],
        "username": user.get("username"),
        "picture": user.get("picture"),
        "subscription_tier": user.get("subscription_tier", "free"),
        "user_profile": user.get("user_profile"),
        "token": token,
        "refresh_token": refresh,
    }

@router.get("/auth/google")
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


@router.get("/auth/google/callback")
async def google_oauth_callback(request: Request, response: Response, code: str = None, error: str = None, state: str = None):
    """Reçoit le code Google OAuth, échange contre les tokens et crée la session.
    Also handles Google Calendar integration OAuth when state starts with 'gcal_integrate:'."""
    frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")

    # --- Google Calendar integration flow ---
    if state and state.startswith("gcal_integrate:"):
        if error or not code:
            return Response(status_code=302, headers={"Location": f"{frontend_url}/integrations?error=oauth_annulé&service=google_calendar"})

        state_doc = await db.integration_states.find_one_and_delete({"state": state, "service": "google_calendar"})
        if not state_doc:
            return Response(status_code=302, headers={"Location": f"{frontend_url}/integrations?error=invalid_state&service=google_calendar"})

        expires_at = datetime.fromisoformat(state_doc["expires_at"])
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            return Response(status_code=302, headers={"Location": f"{frontend_url}/integrations?error=expired&service=google_calendar"})

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
                    return Response(status_code=302, headers={"Location": f"{frontend_url}/integrations?error=token_failed&service=google_calendar"})

                token_data = token_resp.json()
                access_token = token_data.get("access_token")
                refresh_token = token_data.get("refresh_token")
                expires_in = token_data.get("expires_in", 3600)

                if not access_token:
                    logger.error(f"Google Calendar: no access_token in response: {token_data}")
                    return Response(status_code=302, headers={"Location": f"{frontend_url}/integrations?error=token_failed&service=google_calendar"})

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

                encrypted_access = encrypt_token(access_token) if encrypt_token else access_token
                encrypted_refresh = (encrypt_token(refresh_token) if encrypt_token else refresh_token) if refresh_token else None

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
                return Response(status_code=302, headers={"Location": f"{frontend_url}/integrations?success=google_calendar"})

        except Exception as e:
            logger.error(f"Google Calendar integration error: {e}")
            return Response(status_code=302, headers={"Location": f"{frontend_url}/integrations?error=connection_failed&service=google_calendar"})

    # --- Normal login flow ---
    if error or not code:
        return Response(status_code=302, headers={"Location": f"{frontend_url}/login?error=oauth_annulé"})

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
            return Response(status_code=302, headers={"Location": f"{frontend_url}/login?error=auth_échouée"})

        tokens = token_resp.json()

        # Récupération des infos utilisateur
        userinfo_resp = await http_client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        if userinfo_resp.status_code != 200:
            return Response(status_code=302, headers={"Location": f"{frontend_url}/login?error=profil_inaccessible"})

        user_info = userinfo_resp.json()

    email = user_info.get("email")
    name = user_info.get("name", email)
    picture = user_info.get("picture")

    # Création ou mise à jour de l'utilisateur
    existing_user = await db.users.find_one({"email": email}, {"_id": 0})
    if existing_user:
        user_id = existing_user["user_id"]
        update_fields = {"name": name, "picture": picture}
        # Generate username for existing users who don't have one yet
        if not existing_user.get("username"):
            update_fields["username"] = await generate_username(email)
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": update_fields},
        )
    else:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        username = await generate_username(email)
        user_doc = {
            "user_id": user_id,
            "email": email,
            "name": name,
            "username": username,
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
    return Response(status_code=302, headers={"Location": f"{frontend_url}/auth/callback#session_id={session_token}"})


@router.post("/auth/session")
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

    # JWT access token + refresh token
    jwt_token = create_token(user_id)
    refresh = await create_refresh_token(user_id)

    return {
        "user_id": user_id,
        "email": user["email"],
        "name": user["name"],
        "username": user.get("username"),
        "picture": user.get("picture"),
        "subscription_tier": user.get("subscription_tier", "free"),
        "user_profile": user.get("user_profile"),
        "token": jwt_token,
        "refresh_token": refresh,
    }

@router.get("/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    return {
        "user_id": user["user_id"],
        "email": user["email"],
        "name": user["name"],
        "display_name": user.get("display_name"),
        "username": user.get("username"),
        "bio": user.get("bio"),
        "picture": user.get("picture"),
        "avatar_url": user.get("avatar_url"),
        "subscription_tier": user.get("subscription_tier", "free"),
        "total_time_invested": user.get("total_time_invested", 0),
        "streak_days": user.get("streak_days", 0),
        "user_profile": user.get("user_profile"),
        "is_admin": _is_admin(user),
    }


def _is_admin(user: dict) -> bool:
    """Check if user email is in ADMIN_EMAILS env var."""
    raw = os.environ.get("ADMIN_EMAILS", "")
    emails = [e.strip().lower() for e in raw.split(",") if e.strip()]
    return user.get("email", "").lower() in emails

@router.post("/auth/logout")
async def logout(request: Request, response: Response):
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})

    # Revoke refresh tokens if user is authenticated
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        user_id = verify_token(token)
        if user_id:
            await revoke_refresh_tokens(user_id)

    response.delete_cookie(key="session_token", path="/", samesite="none", secure=True)
    return {"message": "Logged out successfully"}

@router.post("/auth/refresh")
async def refresh_token_endpoint(request: Request, response: Response):
    """
    Rotate refresh token — no access token required.
    Accepts { refresh_token: "..." } in body.
    Returns new access token + new refresh token (rotation).
    Old refresh token is invalidated. Reuse = family revocation.
    """
    body = await request.json()
    old_refresh = body.get("refresh_token")
    if not old_refresh:
        raise HTTPException(status_code=400, detail="refresh_token required")

    new_access, new_refresh, user_id = await rotate_refresh_token(old_refresh)

    response.set_cookie(
        key="session_token",
        value=new_access,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=ACCESS_TOKEN_EXPIRATION_HOURS * 3600,
    )

    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})

    return {
        "token": new_access,
        "refresh_token": new_refresh,
        "user_id": user_id,
        "email": user.get("email", "") if user else "",
        "name": user.get("name", "") if user else "",
    }
