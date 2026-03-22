"""
InFinea API — Main application orchestrator.
Mounts all route modules, configures middleware, health checks.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from pathlib import Path
import os
import logging

# Load environment before anything else
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

from database import client, db  # noqa: E402

from routes.auth_routes import router as auth_router  # noqa: E402
from routes.actions import router as actions_router  # noqa: E402
from routes.suggestions import router as suggestions_router  # noqa: E402
from routes.sessions import router as sessions_router  # noqa: E402
from routes.payments import router as payments_router  # noqa: E402
from routes.integrations import router as integrations_router  # noqa: E402
from routes.badges import router as badges_router  # noqa: E402
from routes.notifications import router as notifications_router  # noqa: E402
from routes.b2b import router as b2b_router  # noqa: E402
from routes.reflections import router as reflections_router  # noqa: E402
from routes.seed import router as seed_router  # noqa: E402
from routes.profiles import router as profiles_router  # noqa: E402
from routes.social import router as social_router  # noqa: E402
from routes.feed import router as feed_router  # noqa: E402

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------- Lifespan (startup + shutdown) ----------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Modern lifespan handler — replaces deprecated on_event."""
    # Startup: verify MongoDB connectivity
    try:
        await client.admin.command("ping")
        logger.info("MongoDB connection verified")
    except Exception as e:
        logger.error(f"MongoDB connection failed: {e}")
        raise

    yield

    # Shutdown: clean close
    client.close()
    logger.info("MongoDB connection closed")


# ---------- App ----------

app = FastAPI(
    title="InFinea API",
    version="1.2.0",
    lifespan=lifespan,
)

# Mount all route modules
app.include_router(auth_router)
app.include_router(actions_router)
app.include_router(suggestions_router)
app.include_router(sessions_router)
app.include_router(payments_router)
app.include_router(integrations_router)
app.include_router(badges_router)
app.include_router(notifications_router)
app.include_router(b2b_router)
app.include_router(reflections_router)
app.include_router(seed_router)

# Phase 1 — Social
app.include_router(profiles_router)
app.include_router(social_router)
app.include_router(feed_router)


# ---------- CORS ----------

def _get_allowed_origins() -> list[str]:
    """Parse ALLOWED_ORIGINS from env. Falls back to wildcard in dev only."""
    raw = os.environ.get("ALLOWED_ORIGINS", "")
    env = os.environ.get("ENVIRONMENT", "development")

    if raw:
        return [o.strip() for o in raw.split(",") if o.strip()]

    if env == "production":
        logger.warning("ALLOWED_ORIGINS not set in production — defaulting to empty")
        return []

    return ["*"]


app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=_get_allowed_origins(),
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)


# ---------- Health & Root ----------

@app.get("/api/health")
async def health_check():
    """
    Health check endpoint for Docker, load balancers, and monitoring.
    Verifies actual database connectivity — not just "server is up".
    """
    try:
        await db.command("ping")
        return {
            "status": "healthy",
            "service": "infinea-api",
            "database": "connected",
        }
    except Exception:
        return {
            "status": "degraded",
            "service": "infinea-api",
            "database": "disconnected",
        }


@app.get("/api/")
async def root():
    return {"message": "InFinea API - Investissez vos instants perdus"}
