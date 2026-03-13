"""
InFinea — Centralized configuration.
All environment variables, secrets, and constants loaded once here.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# ── Load .env ──
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

# ── MongoDB ──
MONGO_URL = os.environ.get("MONGO_URL") or os.environ.get("MONGODB_URI", "")
DB_NAME = os.environ.get("DB_NAME", "infinea")

# ── JWT ──
JWT_SECRET = os.environ.get("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET environment variable is required. Server cannot start without it.")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRATION_HOURS = 1  # Short-lived access token
REFRESH_TOKEN_EXPIRATION_DAYS = 30  # Long-lived refresh token
JWT_EXPIRATION_HOURS = ACCESS_TOKEN_EXPIRATION_HOURS  # Backward compat alias

# ── VAPID (Web Push) ──
VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY", "")
VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY", "")
VAPID_CLAIMS_EMAIL = os.environ.get("VAPID_CLAIMS_EMAIL", "mailto:contact@infinea.app")

# ── Stripe ──
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

# ── Redis (Cache) ──
REDIS_URL = os.environ.get("REDIS_URL", "")

# ── Rate Limiting ──
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

# ── Logging ──
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("infinea")
