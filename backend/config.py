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
JWT_EXPIRATION_HOURS = 168  # 7 days

# ── VAPID (Web Push) ──
VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY", "")
VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY", "")
VAPID_CLAIMS_EMAIL = os.environ.get("VAPID_CLAIMS_EMAIL", "mailto:contact@infinea.app")

# ── Stripe ──
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

# ── Logging ──
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("infinea")
