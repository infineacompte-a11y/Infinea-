"""
InFinea — Pydantic models.
All request/response models used across routes.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid


# ============== AUTH MODELS ==============

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
    total_time_invested: int = 0
    streak_days: int = 0
    created_at: datetime


# ============== MICRO-ACTIONS MODELS ==============

class MicroAction(BaseModel):
    action_id: str = Field(default_factory=lambda: f"action_{uuid.uuid4().hex[:12]}")
    title: str
    description: str
    category: str
    duration_min: int
    duration_max: int
    energy_level: str
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


# ============== SESSION MODELS ==============

class SessionStart(BaseModel):
    action_id: str


class SessionComplete(BaseModel):
    session_id: str
    actual_duration: int
    completed: bool = True
    notes: Optional[str] = None


# ============== AI MODELS ==============

class AIRequest(BaseModel):
    available_time: int
    energy_level: str
    preferred_category: Optional[str] = None


# ============== PAYMENT MODELS ==============

class CheckoutRequest(BaseModel):
    origin_url: str


# ============== STATS MODELS ==============

class ProgressStats(BaseModel):
    total_time_invested: int
    total_sessions: int
    streak_days: int
    sessions_by_category: Dict[str, int]
    recent_sessions: List[Dict[str, Any]]


# ============== INTEGRATION MODELS ==============

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
        "evening": "well_being",
    }


# ============== NOTIFICATION MODELS ==============

class NotificationPreferences(BaseModel):
    daily_reminder: bool = True
    reminder_time: str = "09:00"
    streak_alerts: bool = True
    achievement_alerts: bool = True
    weekly_summary: bool = True


# ============== B2B MODELS ==============

class CompanyCreate(BaseModel):
    name: str
    domain: str


class InviteEmployee(BaseModel):
    email: EmailStr


# ============== REFLECTION MODELS ==============

class ReflectionCreate(BaseModel):
    content: str
    mood: Optional[str] = None
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


# ============== SOCIAL MODELS (Phase 1) ==============


class ProfileUpdate(BaseModel):
    """Profile update — all fields optional, update only what's provided."""
    display_name: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=280)
    avatar_url: Optional[str] = None


class PrivacySettings(BaseModel):
    """Granular privacy controls — RGPD-aligned defaults."""
    profile_visible: bool = True
    show_stats: bool = True
    show_badges: bool = True
    show_reflections: bool = False  # Reflections private by default
    activity_default_visibility: str = Field(
        default="followers",
        pattern="^(public|followers|private)$",
    )


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=500)


class ReactionCreate(BaseModel):
    """InFinea-themed reactions — aligned with product DNA."""
    reaction_type: str = Field(
        ...,
        pattern="^(bravo|inspire|fire)$",
        description="bravo=kudos, inspire=this motivates me, fire=on fire",
    )


# ============== CHALLENGE MODELS (Phase 2) ==============


class ChallengeCreate(BaseModel):
    """Create a custom challenge."""
    title: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    challenge_type: str = Field(
        ...,
        pattern="^(duo|group|community)$",
    )
    category: str = Field(
        default="mixed",
        pattern="^(learning|productivity|well_being|mixed)$",
    )
    goal_type: str = Field(
        ...,
        pattern="^(sessions|time|streak)$",
        description="sessions=count, time=minutes, streak=consecutive days",
    )
    goal_value: int = Field(..., gt=0, le=1000)
    duration_days: int = Field(..., gt=0, le=90)
    max_participants: Optional[int] = Field(None, gt=1, le=100)
    privacy: str = Field(
        default="invite_only",
        pattern="^(public|invite_only)$",
    )


class ChallengeFromTemplate(BaseModel):
    """Launch a challenge from a predefined template."""
    template_id: str
    invited_user_ids: Optional[List[str]] = []


class ChallengeInvite(BaseModel):
    """Invite users to a challenge."""
    user_ids: List[str] = Field(..., min_length=1, max_length=20)
