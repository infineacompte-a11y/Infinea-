"""
InFinea — AI routes hub.

Split into domain-specific modules for maintainability:
- ai_suggestions.py: /suggestions, /suggest-now, /smart-predict
- ai_coach.py: /ai/coach, /ai/coach/chat, /ai/coach/history, /ai/coach/feedback
- ai_analysis.py: /ai/debrief, /ai/weekly-analysis, /ai/streak-check, /ai/create-action
- ai_helpers.py: shared utilities (micro-instants context builder)

All sub-routers are mounted here and exposed as a single `router` for server.py.
"""

from fastapi import APIRouter

from routes.ai_suggestions import router as suggestions_router
from routes.ai_coach import router as coach_router
from routes.ai_analysis import router as analysis_router

router = APIRouter()
router.include_router(suggestions_router)
router.include_router(coach_router)
router.include_router(analysis_router)
