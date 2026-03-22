"""
InFinea API — Main application orchestrator.
Mounts all route modules and configures middleware.
"""

from fastapi import FastAPI
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from pathlib import Path
import logging

# Load environment before anything else
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

from database import client  # noqa: E402

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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the main app
app = FastAPI(title="InFinea API")

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

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/")
async def root():
    return {"message": "InFinea API - Investissez vos instants perdus"}


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
