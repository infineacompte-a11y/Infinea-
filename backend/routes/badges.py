"""
InFinea — Badges & achievements routes.
Badge definitions, checking, and awarding.
"""

from fastapi import APIRouter, Depends
from typing import List
from datetime import datetime, timezone

from database import db
from auth import get_current_user

router = APIRouter(prefix="/api")

BADGES = [
    {
        "badge_id": "first_action",
        "name": "Premier Pas",
        "description": "Complétez votre première micro-action",
        "icon": "rocket",
        "condition": {"type": "sessions_completed", "value": 1},
    },
    {
        "badge_id": "streak_3",
        "name": "Régularité",
        "description": "Maintenez un streak de 3 jours",
        "icon": "flame",
        "condition": {"type": "streak_days", "value": 3},
    },
    {
        "badge_id": "streak_7",
        "name": "Semaine Parfaite",
        "description": "Maintenez un streak de 7 jours",
        "icon": "star",
        "condition": {"type": "streak_days", "value": 7},
    },
    {
        "badge_id": "streak_30",
        "name": "Mois d'Or",
        "description": "Maintenez un streak de 30 jours",
        "icon": "crown",
        "condition": {"type": "streak_days", "value": 30},
    },
    {
        "badge_id": "time_60",
        "name": "Première Heure",
        "description": "Accumulez 60 minutes de micro-actions",
        "icon": "clock",
        "condition": {"type": "total_time", "value": 60},
    },
    {
        "badge_id": "time_300",
        "name": "5 Heures",
        "description": "Accumulez 5 heures de micro-actions",
        "icon": "timer",
        "condition": {"type": "total_time", "value": 300},
    },
    {
        "badge_id": "time_600",
        "name": "10 Heures",
        "description": "Accumulez 10 heures de micro-actions",
        "icon": "trophy",
        "condition": {"type": "total_time", "value": 600},
    },
    {
        "badge_id": "category_learning",
        "name": "Apprenant",
        "description": "Complétez 10 actions d'apprentissage",
        "icon": "book-open",
        "condition": {"type": "category_sessions", "category": "learning", "value": 10},
    },
    {
        "badge_id": "category_productivity",
        "name": "Productif",
        "description": "Complétez 10 actions de productivité",
        "icon": "target",
        "condition": {
            "type": "category_sessions",
            "category": "productivity",
            "value": 10,
        },
    },
    {
        "badge_id": "category_wellbeing",
        "name": "Zen Master",
        "description": "Complétez 10 actions de bien-être",
        "icon": "heart",
        "condition": {
            "type": "category_sessions",
            "category": "well_being",
            "value": 10,
        },
    },
    {
        "badge_id": "all_categories",
        "name": "Équilibre",
        "description": "Complétez au moins 5 actions dans chaque catégorie",
        "icon": "sparkles",
        "condition": {"type": "all_categories", "value": 5},
    },
    {
        "badge_id": "premium",
        "name": "Investisseur",
        "description": "Passez à Premium",
        "icon": "gem",
        "condition": {"type": "subscription", "value": "premium"},
    },
]


async def check_and_award_badges(user_id: str) -> List[dict]:
    """Check user progress and award new badges"""
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not user:
        return []

    user_badges = user.get("badges", [])
    user_badge_ids = [b["badge_id"] for b in user_badges]

    total_sessions = await db.user_sessions_history.count_documents(
        {"user_id": user_id, "completed": True}
    )

    pipeline = [
        {"$match": {"user_id": user_id, "completed": True}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
    ]
    category_stats = await db.user_sessions_history.aggregate(pipeline).to_list(10)
    category_counts = {stat["_id"]: stat["count"] for stat in category_stats}

    new_badges = []

    for badge in BADGES:
        if badge["badge_id"] in user_badge_ids:
            continue

        condition = badge["condition"]
        earned = False

        if condition["type"] == "sessions_completed":
            earned = total_sessions >= condition["value"]
        elif condition["type"] == "streak_days":
            earned = user.get("streak_days", 0) >= condition["value"]
        elif condition["type"] == "total_time":
            earned = user.get("total_time_invested", 0) >= condition["value"]
        elif condition["type"] == "category_sessions":
            earned = category_counts.get(condition["category"], 0) >= condition["value"]
        elif condition["type"] == "all_categories":
            earned = all(
                category_counts.get(cat, 0) >= condition["value"]
                for cat in ["learning", "productivity", "well_being"]
            )
        elif condition["type"] == "subscription":
            earned = user.get("subscription_tier") == condition["value"]

        if earned:
            badge_award = {
                "badge_id": badge["badge_id"],
                "name": badge["name"],
                "icon": badge["icon"],
                "earned_at": datetime.now(timezone.utc).isoformat(),
            }
            new_badges.append(badge_award)

    if new_badges:
        await db.users.update_one(
            {"user_id": user_id}, {"$push": {"badges": {"$each": new_badges}}}
        )

    return new_badges


@router.get("/badges")
async def get_all_badges():
    """Get all available badges"""
    return BADGES


@router.get("/badges/user")
async def get_user_badges(user: dict = Depends(get_current_user)):
    """Get user's earned badges"""
    user_badges = user.get("badges", [])

    new_badges = await check_and_award_badges(user["user_id"])

    all_earned = user_badges + new_badges

    return {
        "earned": all_earned,
        "new_badges": new_badges,
        "total_available": len(BADGES),
        "total_earned": len(all_earned),
    }
