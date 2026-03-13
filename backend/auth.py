"""
InFinea — Authentication helpers.
JWT token management, refresh token rotation, password hashing,
and user extraction from requests.

Refresh token rotation pattern (benchmark: Auth0 / Supabase):
- Access token: short-lived JWT (1h)
- Refresh token: opaque, long-lived (30d), stored in DB
- Rotation: each refresh invalidates the old token and issues a new pair
- Family tracking: reuse of a consumed refresh token invalidates the
  entire family (compromise detection)
"""

from datetime import datetime, timezone, timedelta
from typing import Optional
import secrets
import jwt
import bcrypt
from fastapi import HTTPException, Request

from config import (
    JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION_HOURS,
    ACCESS_TOKEN_EXPIRATION_HOURS, REFRESH_TOKEN_EXPIRATION_DAYS,
)
from database import db


# ═══════════════════════════════════════════════════════════════
# Access token (JWT, short-lived)
# ═══════════════════════════════════════════════════════════════

def create_token(user_id: str) -> str:
    """Create a short-lived access token (JWT)."""
    payload = {
        "user_id": user_id,
        "type": "access",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRATION_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> Optional[str]:
    """Verify access token. Returns user_id or None."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("user_id")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ═══════════════════════════════════════════════════════════════
# Refresh token (opaque, DB-backed, rotated on each use)
# ═══════════════════════════════════════════════════════════════

async def create_refresh_token(user_id: str) -> str:
    """Generate an opaque refresh token, store it in DB, return the token string."""
    token = secrets.token_urlsafe(48)  # 64-char opaque string
    family_id = secrets.token_urlsafe(16)  # Token family for reuse detection

    await db.refresh_tokens.insert_one({
        "token": token,
        "user_id": user_id,
        "family_id": family_id,
        "used": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRATION_DAYS)).isoformat(),
    })
    return token


async def rotate_refresh_token(old_token: str):
    """
    Validate and rotate a refresh token.
    Returns (new_access_token, new_refresh_token, user_id) or raises HTTPException.

    Security: if a consumed token is replayed, the entire family is invalidated
    (indicates token theft — Auth0 rotation pattern).
    """
    doc = await db.refresh_tokens.find_one({"token": old_token}, {"_id": 0})

    if not doc:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = doc["user_id"]
    family_id = doc["family_id"]

    # Check if already used → compromise detected, nuke the family
    if doc.get("used"):
        await db.refresh_tokens.delete_many({"family_id": family_id})
        raise HTTPException(
            status_code=401,
            detail="Refresh token reuse detected — all sessions revoked for security",
        )

    # Check expiry
    expires_at = datetime.fromisoformat(doc["expires_at"])
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        await db.refresh_tokens.delete_one({"token": old_token})
        raise HTTPException(status_code=401, detail="Refresh token expired")

    # Mark old token as used (not deleted — kept for reuse detection)
    await db.refresh_tokens.update_one(
        {"token": old_token},
        {"$set": {"used": True, "used_at": datetime.now(timezone.utc).isoformat()}},
    )

    # Issue new refresh token in the same family
    new_refresh = secrets.token_urlsafe(48)
    await db.refresh_tokens.insert_one({
        "token": new_refresh,
        "user_id": user_id,
        "family_id": family_id,
        "used": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRATION_DAYS)).isoformat(),
    })

    # Issue new access token
    new_access = create_token(user_id)

    return new_access, new_refresh, user_id


async def revoke_refresh_tokens(user_id: str):
    """Revoke all refresh tokens for a user (logout everywhere)."""
    await db.refresh_tokens.delete_many({"user_id": user_id})

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
