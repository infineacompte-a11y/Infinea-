"""InFinea — Badges, achievements, and premium features routes."""

from fastapi import APIRouter, Depends, Request
from typing import List
from datetime import datetime, timezone, timedelta

from database import db
from auth import get_current_user
from config import logger, limiter

router = APIRouter()

# ============== BADGES & ACHIEVEMENTS ==============

BADGES = [
    {
        "badge_id": "first_action",
        "name": "Premier Pas",
        "description": "Complétez votre première micro-action",
        "icon": "rocket",
        "condition": {"type": "sessions_completed", "value": 1}
    },
    {
        "badge_id": "streak_3",
        "name": "Régularité",
        "description": "Maintenez un streak de 3 jours",
        "icon": "flame",
        "condition": {"type": "streak_days", "value": 3}
    },
    {
        "badge_id": "streak_7",
        "name": "Semaine Parfaite",
        "description": "Maintenez un streak de 7 jours",
        "icon": "star",
        "condition": {"type": "streak_days", "value": 7}
    },
    {
        "badge_id": "streak_30",
        "name": "Mois d'Or",
        "description": "Maintenez un streak de 30 jours",
        "icon": "crown",
        "condition": {"type": "streak_days", "value": 30}
    },
    {
        "badge_id": "time_60",
        "name": "Première Heure",
        "description": "Accumulez 60 minutes de micro-actions",
        "icon": "clock",
        "condition": {"type": "total_time", "value": 60}
    },
    {
        "badge_id": "time_300",
        "name": "5 Heures",
        "description": "Accumulez 5 heures de micro-actions",
        "icon": "timer",
        "condition": {"type": "total_time", "value": 300}
    },
    {
        "badge_id": "time_600",
        "name": "10 Heures",
        "description": "Accumulez 10 heures de micro-actions",
        "icon": "trophy",
        "condition": {"type": "total_time", "value": 600}
    },
    {
        "badge_id": "category_learning",
        "name": "Apprenant",
        "description": "Complétez 10 actions d'apprentissage",
        "icon": "book-open",
        "condition": {"type": "category_sessions", "category": "learning", "value": 10}
    },
    {
        "badge_id": "category_productivity",
        "name": "Productif",
        "description": "Complétez 10 actions de productivité",
        "icon": "target",
        "condition": {"type": "category_sessions", "category": "productivity", "value": 10}
    },
    {
        "badge_id": "category_wellbeing",
        "name": "Zen Master",
        "description": "Complétez 10 actions de bien-être",
        "icon": "heart",
        "condition": {"type": "category_sessions", "category": "well_being", "value": 10}
    },
    {
        "badge_id": "all_categories",
        "name": "Équilibre",
        "description": "Complétez au moins 5 actions dans chaque catégorie",
        "icon": "sparkles",
        "condition": {"type": "all_categories", "value": 5}
    },
    {
        "badge_id": "premium",
        "name": "Investisseur",
        "description": "Passez à Premium",
        "icon": "gem",
        "condition": {"type": "subscription", "value": "premium"}
    },
    # --- Premium-exclusive badges ---
    {
        "badge_id": "streak_60",
        "name": "Discipline de Fer",
        "description": "Maintenez un streak de 60 jours",
        "icon": "shield",
        "condition": {"type": "streak_days", "value": 60},
        "premium_only": True
    },
    {
        "badge_id": "streak_100",
        "name": "Centurion",
        "description": "Maintenez un streak de 100 jours",
        "icon": "award",
        "condition": {"type": "streak_days", "value": 100},
        "premium_only": True
    },
    {
        "badge_id": "time_1500",
        "name": "25 Heures",
        "description": "Accumulez 25 heures de micro-actions",
        "icon": "crown",
        "condition": {"type": "total_time", "value": 1500},
        "premium_only": True
    },
    {
        "badge_id": "category_master",
        "name": "Polymathe",
        "description": "Complétez 20 sessions dans 5 catégories différentes",
        "icon": "layers",
        "condition": {"type": "multi_category_master", "min_categories": 5, "value": 20},
        "premium_only": True
    },
    {
        "badge_id": "challenge_3",
        "name": "Challenger",
        "description": "Complétez 3 défis mensuels",
        "icon": "trophy",
        "condition": {"type": "challenges_completed", "value": 3},
        "premium_only": True
    },
    {
        "badge_id": "challenge_10",
        "name": "Champion",
        "description": "Complétez 10 défis mensuels",
        "icon": "medal",
        "condition": {"type": "challenges_completed", "value": 10},
        "premium_only": True
    },
    {
        "badge_id": "custom_10",
        "name": "Architecte",
        "description": "Créez 10 actions personnalisées",
        "icon": "wrench",
        "condition": {"type": "custom_actions_created", "value": 10},
        "premium_only": True
    },
    {
        "badge_id": "streak_shield_5",
        "name": "Résilient",
        "description": "Utilisez le Bouclier de Streak 5 fois",
        "icon": "heart-handshake",
        "condition": {"type": "streak_shield_uses", "value": 5},
        "premium_only": True
    }
]

async def check_and_award_badges(user_id: str) -> List[dict]:
    """Check user progress and award new badges"""
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not user:
        return []

    # Get user's current badges
    user_badges = user.get("badges", [])
    user_badge_ids = [b["badge_id"] for b in user_badges]

    # Get session stats
    total_sessions = await db.user_sessions_history.count_documents(
        {"user_id": user_id, "completed": True}
    )

    # Get category stats
    pipeline = [
        {"$match": {"user_id": user_id, "completed": True}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}}}
    ]
    category_stats = await db.user_sessions_history.aggregate(pipeline).to_list(10)
    category_counts = {stat["_id"]: stat["count"] for stat in category_stats}

    # Get custom actions count
    custom_actions_count = await db.user_custom_actions.count_documents({"created_by": user_id})

    # Get challenges completed count
    challenges_completed = await db.user_challenges.count_documents(
        {"user_id": user_id, "completed": True}
    )

    new_badges = []
    is_premium = user.get("subscription_tier") == "premium"

    for badge in BADGES:
        if badge["badge_id"] in user_badge_ids:
            continue

        # Skip premium-only badges for free users
        if badge.get("premium_only") and not is_premium:
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
        elif condition["type"] == "multi_category_master":
            qualifying = sum(1 for c in category_counts.values() if c >= condition["value"])
            earned = qualifying >= condition["min_categories"]
        elif condition["type"] == "challenges_completed":
            earned = challenges_completed >= condition["value"]
        elif condition["type"] == "custom_actions_created":
            earned = custom_actions_count >= condition["value"]
        elif condition["type"] == "streak_shield_uses":
            earned = user.get("streak_shield_count", 0) >= condition["value"]

        if earned:
            badge_award = {
                "badge_id": badge["badge_id"],
                "name": badge["name"],
                "icon": badge["icon"],
                "earned_at": datetime.now(timezone.utc).isoformat()
            }
            new_badges.append(badge_award)

    # Update user with new badges
    if new_badges:
        await db.users.update_one(
            {"user_id": user_id},
            {"$push": {"badges": {"$each": new_badges}}}
        )

    return new_badges

@router.get("/badges")
@limiter.limit("30/minute")
async def get_all_badges(request: Request):
    """Get all available badges"""
    return BADGES

@router.get("/badges/user")
async def get_user_badges(user: dict = Depends(get_current_user)):
    """Get user's earned badges"""
    user_badges = user.get("badges", [])

    # Check for new badges
    new_badges = await check_and_award_badges(user["user_id"])

    all_earned = user_badges + new_badges

    return {
        "earned": all_earned,
        "new_badges": new_badges,
        "total_available": len(BADGES),
        "total_earned": len(all_earned)
    }

# ============== PREMIUM FEATURES ==============

@router.get("/premium/streak-shield")
async def get_streak_shield_status(user: dict = Depends(get_current_user)):
    """Get streak shield status for premium users"""
    if user.get("subscription_tier") != "premium":
        return {"available": False, "is_premium": False, "message": "Fonctionnalité Premium"}

    today = datetime.now(timezone.utc).date()
    shield_used_at = user.get("streak_shield_used_at")
    shield_available = True
    cooldown_days = 0

    if shield_used_at:
        if isinstance(shield_used_at, str):
            shield_date = datetime.fromisoformat(shield_used_at).date()
        else:
            shield_date = shield_used_at.date() if hasattr(shield_used_at, 'date') else shield_used_at
        days_since = (today - shield_date).days
        shield_available = days_since >= 7
        cooldown_days = max(0, 7 - days_since)

    return {
        "available": shield_available,
        "is_premium": True,
        "cooldown_days": cooldown_days,
        "total_uses": user.get("streak_shield_count", 0),
        "last_used": shield_used_at
    }

# Monthly challenges definitions
MONTHLY_CHALLENGES = [
    {
        "challenge_id": "explorer",
        "title": "Explorateur",
        "description": "Complétez 5 actions dans 3 catégories différentes ce mois-ci",
        "icon": "compass",
        "condition": {"type": "categories_touched", "min_categories": 3, "min_sessions": 5},
        "target": 5
    },
    {
        "challenge_id": "deep_diver",
        "title": "Deep Diver",
        "description": "Complétez 10 actions dans la même catégorie ce mois-ci",
        "icon": "target",
        "condition": {"type": "single_category_sessions", "value": 10},
        "target": 10
    },
    {
        "challenge_id": "early_bird",
        "title": "Matinal",
        "description": "Complétez 5 actions avant 9h ce mois-ci",
        "icon": "sunrise",
        "condition": {"type": "early_sessions", "hour_before": 9, "value": 5},
        "target": 5
    },
    {
        "challenge_id": "consistency",
        "title": "Régulier",
        "description": "Complétez au moins 1 action par jour pendant 15 jours ce mois-ci",
        "icon": "calendar-check",
        "condition": {"type": "active_days", "value": 15},
        "target": 15
    },
    {
        "challenge_id": "time_investor",
        "title": "Investisseur du Temps",
        "description": "Investissez 120 minutes ce mois-ci",
        "icon": "hourglass",
        "condition": {"type": "monthly_time", "value": 120},
        "target": 120
    },
    {
        "challenge_id": "diversifier",
        "title": "Diversificateur",
        "description": "Essayez au moins 5 catégories différentes ce mois-ci",
        "icon": "shuffle",
        "condition": {"type": "unique_categories", "value": 5},
        "target": 5
    },
]

@router.get("/premium/challenges")
async def get_premium_challenges(user: dict = Depends(get_current_user)):
    """Get current month's challenges with progress for premium users"""
    if user.get("subscription_tier") != "premium":
        return {"challenges": [], "is_premium": False, "message": "Fonctionnalité Premium"}

    now = datetime.now(timezone.utc)
    month_key = now.strftime("%Y-%m")
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()

    # Get this month's sessions
    sessions = await db.user_sessions_history.find(
        {"user_id": user["user_id"], "completed": True, "started_at": {"$gte": month_start}},
        {"_id": 0}
    ).to_list(500)

    # Calculate stats for challenge evaluation
    category_counts = {}
    total_time = 0
    early_sessions = 0
    active_days = set()
    for s in sessions:
        cat = s.get("category", "unknown")
        category_counts[cat] = category_counts.get(cat, 0) + 1
        total_time += s.get("actual_duration", 0)
        started = s.get("started_at", "")
        if started:
            try:
                dt = datetime.fromisoformat(started)
                if dt.hour < 9:
                    early_sessions += 1
                active_days.add(dt.date().isoformat())
            except (ValueError, TypeError):
                pass

    # Get user challenge records
    user_challenges = await db.user_challenges.find(
        {"user_id": user["user_id"], "month": month_key},
        {"_id": 0}
    ).to_list(20)
    completed_map = {uc["challenge_id"]: uc for uc in user_challenges}

    challenges_with_progress = []
    for ch in MONTHLY_CHALLENGES:
        cond = ch["condition"]
        progress = 0

        if cond["type"] == "categories_touched":
            cats_with_min = sum(1 for c in category_counts.values() if c >= 1)
            progress = min(len(sessions), ch["target"])
            if cats_with_min >= cond["min_categories"] and len(sessions) >= cond["min_sessions"]:
                progress = ch["target"]
        elif cond["type"] == "single_category_sessions":
            progress = max(category_counts.values()) if category_counts else 0
        elif cond["type"] == "early_sessions":
            progress = early_sessions
        elif cond["type"] == "active_days":
            progress = len(active_days)
        elif cond["type"] == "monthly_time":
            progress = total_time
        elif cond["type"] == "unique_categories":
            progress = len(category_counts)

        is_completed = progress >= ch["target"]

        # Auto-complete if newly completed
        if is_completed and ch["challenge_id"] not in completed_map:
            await db.user_challenges.update_one(
                {"user_id": user["user_id"], "challenge_id": ch["challenge_id"], "month": month_key},
                {"$set": {
                    "completed": True,
                    "completed_at": now.isoformat(),
                    "progress": progress
                }},
                upsert=True
            )

        challenges_with_progress.append({
            "challenge_id": ch["challenge_id"],
            "title": ch["title"],
            "description": ch["description"],
            "icon": ch["icon"],
            "target": ch["target"],
            "progress": min(progress, ch["target"]),
            "completed": is_completed,
            "completed_at": completed_map.get(ch["challenge_id"], {}).get("completed_at")
        })

    total_completed = sum(1 for c in challenges_with_progress if c["completed"])

    return {
        "challenges": challenges_with_progress,
        "is_premium": True,
        "month": month_key,
        "total_completed": total_completed,
        "total_challenges": len(MONTHLY_CHALLENGES)
    }

# ── Community Challenges (free for all) ──────────

COMMUNITY_CHALLENGES = [
    {
        "id": "community_7day_streak",
        "title": "Streak Communautaire",
        "description": "Maintiens un streak de 7 jours ce mois-ci",
        "icon": "flame",
        "target": 7,
        "metric": "streak",
        "reward": "Badge Flamme Communautaire",
    },
    {
        "id": "community_30min_week",
        "title": "30 min cette semaine",
        "description": "Investis 30 minutes de micro-actions en une semaine",
        "icon": "clock",
        "target": 30,
        "metric": "week_minutes",
        "reward": "Badge Investisseur",
    },
    {
        "id": "community_5_sessions",
        "title": "5 sessions ce mois",
        "description": "Complète 5 sessions de micro-actions ce mois-ci",
        "icon": "target",
        "target": 5,
        "metric": "month_sessions",
        "reward": "Badge Régulier",
    },
    {
        "id": "community_3_categories",
        "title": "Explorateur",
        "description": "Pratique dans 3 catégories différentes ce mois-ci",
        "icon": "compass",
        "target": 3,
        "metric": "categories",
        "reward": "Badge Explorateur",
    },
]


@router.get("/challenges/community")
@limiter.limit("15/minute")
async def get_community_challenges(request: Request, user: dict = Depends(get_current_user)):
    """Get community challenges open to all users with progress + leaderboard."""
    now = datetime.now(timezone.utc)
    today = now.date()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
    week_start = (today - timedelta(days=today.weekday())).isoformat()
    user_id = user["user_id"]

    # Get user's month sessions
    month_sessions = await db.user_sessions_history.find(
        {"user_id": user_id, "completed": True, "started_at": {"$gte": month_start}},
        {"_id": 0, "actual_duration": 1, "category": 1, "started_at": 1}
    ).to_list(200)

    # Get week sessions
    week_sessions = [s for s in month_sessions if s.get("started_at", "") >= week_start]

    # Compute metrics
    streak = user.get("streak_days", 0)
    week_minutes = sum(s.get("actual_duration", 0) for s in week_sessions)
    month_session_count = len(month_sessions)
    categories = len(set(s.get("category", "") for s in month_sessions if s.get("category")))

    metric_values = {
        "streak": streak,
        "week_minutes": week_minutes,
        "month_sessions": month_session_count,
        "categories": categories,
    }

    # Leaderboard: count how many users completed each challenge
    month_key = now.strftime("%Y-%m")
    leaderboard_pipeline = [
        {"$match": {"month": month_key, "completed": True}},
        {"$group": {"_id": "$challenge_id", "count": {"$sum": 1}}},
    ]
    leaderboard_data = await db.user_challenges.aggregate(leaderboard_pipeline).to_list(20)
    leaderboard_map = {item["_id"]: item["count"] for item in leaderboard_data}

    # Build response
    challenges = []
    for ch in COMMUNITY_CHALLENGES:
        progress = min(metric_values.get(ch["metric"], 0), ch["target"])
        is_completed = progress >= ch["target"]

        # Auto-record completion
        if is_completed:
            await db.user_challenges.update_one(
                {"user_id": user_id, "challenge_id": ch["id"], "month": month_key},
                {"$set": {"completed": True, "completed_at": now.isoformat(), "progress": progress}},
                upsert=True,
            )

        challenges.append({
            "id": ch["id"],
            "title": ch["title"],
            "description": ch["description"],
            "icon": ch["icon"],
            "target": ch["target"],
            "progress": progress,
            "completed": is_completed,
            "reward": ch["reward"],
            "participants_completed": leaderboard_map.get(ch["id"], 0),
        })

    return {
        "challenges": challenges,
        "month": month_key,
    }


@router.get("/premium/analytics")
async def get_premium_analytics(user: dict = Depends(get_current_user)):
    """Get advanced analytics for premium users"""
    if user.get("subscription_tier") != "premium":
        return {"is_premium": False, "message": "Fonctionnalité Premium"}

    now = datetime.now(timezone.utc)
    thirty_days_ago = (now - timedelta(days=30)).isoformat()

    # Get sessions from last 30 days
    sessions = await db.user_sessions_history.find(
        {"user_id": user["user_id"], "completed": True, "started_at": {"$gte": thirty_days_ago}},
        {"_id": 0}
    ).sort("started_at", 1).to_list(500)

    # Daily activity
    daily_activity = {}
    hour_distribution = {}
    day_distribution = {}
    category_stats = {}
    day_names = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]

    for s in sessions:
        started = s.get("started_at", "")
        duration = s.get("actual_duration", 0)
        category = s.get("category", "unknown")
        try:
            dt = datetime.fromisoformat(started)
            date_key = dt.date().isoformat()
            daily_activity[date_key] = daily_activity.get(date_key, 0) + 1

            hour = dt.hour
            period = "matin" if hour < 12 else "après-midi" if hour < 18 else "soir"
            hour_distribution[period] = hour_distribution.get(period, 0) + 1

            day_name = day_names[dt.weekday()]
            day_distribution[day_name] = day_distribution.get(day_name, 0) + 1
        except (ValueError, TypeError):
            pass

        if category not in category_stats:
            category_stats[category] = {"sessions": 0, "total_duration": 0}
        category_stats[category]["sessions"] += 1
        category_stats[category]["total_duration"] += duration

    # Best time of day
    best_time = max(hour_distribution, key=hour_distribution.get) if hour_distribution else "matin"

    # Most productive day
    best_day = max(day_distribution, key=day_distribution.get) if day_distribution else "lundi"

    # Category deep dive with averages
    for cat, stats in category_stats.items():
        stats["avg_duration"] = round(stats["total_duration"] / max(stats["sessions"], 1), 1)

    # Streak history (from all-time sessions)
    all_sessions = await db.user_sessions_history.find(
        {"user_id": user["user_id"], "completed": True},
        {"_id": 0, "started_at": 1}
    ).sort("started_at", 1).to_list(2000)

    streak_history = []
    if all_sessions:
        dates = set()
        for s in all_sessions:
            try:
                dt = datetime.fromisoformat(s["started_at"]).date()
                dates.add(dt)
            except (ValueError, TypeError):
                pass
        sorted_dates = sorted(dates)
        if sorted_dates:
            current_start = sorted_dates[0]
            current_end = sorted_dates[0]
            for i in range(1, len(sorted_dates)):
                if (sorted_dates[i] - sorted_dates[i - 1]).days <= 1:
                    current_end = sorted_dates[i]
                else:
                    length = (current_end - current_start).days + 1
                    if length >= 2:
                        streak_history.append({
                            "start": current_start.isoformat(),
                            "end": current_end.isoformat(),
                            "length": length
                        })
                    current_start = sorted_dates[i]
                    current_end = sorted_dates[i]
            length = (current_end - current_start).days + 1
            if length >= 2:
                streak_history.append({
                    "start": current_start.isoformat(),
                    "end": current_end.isoformat(),
                    "length": length
                })

    # Milestone prediction
    total_time = user.get("total_time_invested", 0)
    milestones = [60, 300, 600, 1500, 3000]
    next_milestone = None
    for m in milestones:
        if total_time < m:
            next_milestone = m
            break

    eta_days = None
    if next_milestone and sessions:
        time_last_30 = sum(s.get("actual_duration", 0) for s in sessions)
        daily_avg = time_last_30 / 30
        if daily_avg > 0:
            remaining = next_milestone - total_time
            eta_days = round(remaining / daily_avg)

    return {
        "is_premium": True,
        "daily_activity": daily_activity,
        "best_time_of_day": best_time,
        "most_productive_day": best_day,
        "category_deep_dive": category_stats,
        "streak_history": streak_history[-10:],
        "milestones": {
            "current": total_time,
            "next": next_milestone,
            "eta_days": eta_days
        },
        "sessions_last_30_days": len(sessions),
        "time_last_30_days": sum(s.get("actual_duration", 0) for s in sessions)
    }
