"""
InFinea — Pydantic models (request/response schemas).
All models centralized here for reuse across routes.
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr


# ── Auth ──

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str = Field(min_length=1)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    user_id: str
    email: str
    name: str
    username: Optional[str] = None
    picture: Optional[str] = None
    subscription_tier: str = "free"
    total_time_invested: int = 0  # in minutes
    streak_days: int = 0
    created_at: datetime


# ── Actions ──

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


# ── Sessions ──

class SessionStart(BaseModel):
    action_id: str

class SessionComplete(BaseModel):
    session_id: str
    actual_duration: int  # in minutes
    completed: bool = True
    notes: Optional[str] = None


# ── AI ──

class AIRequest(BaseModel):
    available_time: int  # in minutes
    energy_level: str  # low, medium, high
    preferred_category: Optional[str] = None

class CustomActionRequest(BaseModel):
    description: str
    preferred_category: Optional[str] = None
    preferred_duration: Optional[int] = None

class DebriefRequest(BaseModel):
    session_id: str
    action_title: Optional[str] = None
    action_category: Optional[str] = None
    actual_duration: Optional[int] = None
    duration_minutes: Optional[int] = None  # Frontend sends this
    notes: Optional[str] = None

class CoachChatRequest(BaseModel):
    message: str


# ── Billing ──

class CheckoutRequest(BaseModel):
    origin_url: str

class PromoCodeRequest(BaseModel):
    code: str


# ── Stats ──

class ProgressStats(BaseModel):
    total_time_invested: int
    total_sessions: int
    streak_days: int
    sessions_by_category: Dict[str, int]
    recent_sessions: List[Dict[str, Any]]


# ── Onboarding ──

class OnboardingProfile(BaseModel):
    goals: List[str] = []  # ["learning", "productivity", "well_being"]
    preferred_times: List[str] = []  # ["morning", "lunch", "evening"]
    energy_level: str = "medium"  # "low", "medium", "high"
    interests: List[str] = []  # ["learning", "productivity", "wellness"]
    # Legacy fields (optional for backward compat)
    availability_slots: Optional[List[str]] = None
    daily_minutes: Optional[int] = None
    energy_high: Optional[str] = None
    energy_low: Optional[str] = None


# ── Objectives ──

class ObjectiveCreate(BaseModel):
    title: str  # "Apprendre le thaï", "Jouer du piano"
    description: Optional[str] = None
    target_duration_days: Optional[int] = 30  # 30, 60, 90 days
    daily_minutes: Optional[int] = 10  # target per day
    category: Optional[str] = None  # learning, productivity, etc.

class ObjectiveUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    target_duration_days: Optional[int] = None
    daily_minutes: Optional[int] = None
    status: Optional[str] = None  # active, paused, completed, abandoned


# ── Routines ──

class RoutineCreate(BaseModel):
    name: str  # "Routine matinale", "Pause déjeuner productive"
    description: Optional[str] = None
    time_of_day: Optional[str] = "morning"  # morning, afternoon, evening, anytime
    frequency: Optional[str] = "daily"  # daily | weekdays | weekends | custom
    frequency_days: Optional[List[int]] = None  # [0=Mon..6=Sun] for custom
    items: Optional[List[dict]] = []  # [{type, ref_id, title, duration_minutes, order}]

class RoutineUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    time_of_day: Optional[str] = None
    frequency: Optional[str] = None
    frequency_days: Optional[List[int]] = None
    items: Optional[List[dict]] = None
    is_active: Optional[bool] = None


# ── Integrations ──

class ICalConnectRequest(BaseModel):
    url: str
    name: Optional[str] = "Mon calendrier iCal"

class TokenConnectRequest(BaseModel):
    token: str
    name: Optional[str] = None

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
        "evening": "well_being"
    }


# ── Notifications ──

class NotificationPreferences(BaseModel):
    daily_reminder: bool = True
    reminder_time: str = "09:00"  # HH:MM format
    streak_alerts: bool = True
    achievement_alerts: bool = True
    weekly_summary: bool = True
    # Email preferences
    email_notifications: bool = True       # Master toggle
    email_social: bool = True              # Follows, mentions
    email_achievements: bool = True        # Badges, milestones
    email_streak: bool = True              # Streak alerts
    email_weekly_summary: bool = True      # Weekly digest


# ── Social ──

class ShareCreate(BaseModel):
    """Request body for creating a share card."""
    share_type: str = Field(default="weekly_recap", description="Type of share: weekly_recap, milestone, badge, objective")
    objective_id: Optional[str] = Field(default=None, description="Objective to highlight (optional)")

class GroupCreate(BaseModel):
    """Request body for creating a duo/group."""
    name: str = Field(min_length=1, max_length=50)
    objective_title: Optional[str] = Field(default=None, max_length=100, description="Shared objective label")
    category: Optional[str] = Field(default=None)

class GroupInvite(BaseModel):
    """Request body for inviting someone to a group."""
    email: EmailStr


# ── B2B ──

class CompanyCreate(BaseModel):
    name: str
    domain: str

class InviteEmployee(BaseModel):
    email: EmailStr


# ── Reflections ──

class ReflectionCreate(BaseModel):
    content: str
    mood: Optional[str] = None  # positive, neutral, negative
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


# ── Messaging ──

class ConversationCreate(BaseModel):
    """Request body for starting a DM conversation."""
    user_id: str = Field(description="User ID of the person to message")

class GroupConversationCreate(BaseModel):
    """Request body for creating a group conversation."""
    name: str = Field(min_length=1, max_length=50)
    member_ids: List[str] = Field(min_length=1, max_length=19)  # + creator = max 20

class GroupUpdate(BaseModel):
    """Request body for updating group name."""
    name: str = Field(min_length=1, max_length=50)

class MessageSend(BaseModel):
    """Request body for sending a message (text and/or images)."""
    content: str = Field(default="", max_length=1000)
    images: list = Field(default_factory=list)  # [{image_url, thumbnail_url, width, height}]
