"""
InFinea — Admin AI Dashboard Endpoints.

Protected routes for monitoring and piloting the vertical AI system.
Requires ADMIN_EMAILS authentication (same pattern as safety.py).

Provides real-time KPIs across 8 dimensions:
1. Overview: system health, active users, costs
2. Coaching: Prochaska stage distribution, feedback quality
3. Memory: extraction stats, categories, retention
4. Scoring: factor weights, completion by score bracket
5. Knowledge: fragment usage, cache hit rates
6. Collective Intelligence: pattern stats, evolution
7. Costs: AI spend by endpoint, model, cache savings
8. Drift: users at risk, alerts, recovery rates
"""

import os
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends

from database import db
from auth import get_current_user
from config import limiter

router = APIRouter(prefix="/admin/ai", tags=["admin-ai"])


def _require_admin(user: dict):
    """Raise 403 if user is not admin."""
    raw = os.environ.get("ADMIN_EMAILS", "")
    emails = [e.strip().lower() for e in raw.split(",") if e.strip()]
    if user.get("email", "").lower() not in emails:
        raise HTTPException(status_code=403, detail="Admin access required")


# ═══════════════════════════════════════════════════════════════════════════
# 1. OVERVIEW — System health
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/overview")
async def get_ai_overview(user: dict = Depends(get_current_user)):
    """Global AI system health dashboard."""
    _require_admin(user)

    now = datetime.now(timezone.utc)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    week_ago = (now - timedelta(days=7)).isoformat()

    # Active users (session in last 7 days)
    active_users = await db.user_sessions_history.distinct(
        "user_id", {"started_at": {"$gte": week_ago}}
    )

    # AI calls today
    ai_calls_today = await db.ai_usage.count_documents({"created_at": {"$gte": today}})

    # Total cost today
    cost_pipeline = [
        {"$match": {"created_at": {"$gte": today}}},
        {"$group": {"_id": None, "total": {"$sum": "$estimated_cost_usd"}}},
    ]
    cost_result = await db.ai_usage.aggregate(cost_pipeline).to_list(1)
    cost_today = round(cost_result[0]["total"], 4) if cost_result else 0

    # Memories active
    total_memories = await db.ai_memories.count_documents({"superseded_by": None})

    # Feature computation last run
    last_run = await db.feature_computation_logs.find_one(
        {}, sort=[("computed_at", -1)]
    )

    return {
        "active_users_7d": len(active_users),
        "ai_calls_today": ai_calls_today,
        "ai_cost_today_usd": cost_today,
        "total_ai_memories": total_memories,
        "last_feature_computation": last_run.get("computed_at") if last_run else None,
        "last_feature_users_processed": last_run.get("users_processed") if last_run else 0,
        "timestamp": now.isoformat(),
    }


# ═══════════════════════════════════════════════════════════════════════════
# 2. COACHING — Prochaska stage distribution + quality
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/coaching")
async def get_coaching_stats(user: dict = Depends(get_current_user)):
    """Coaching engine stats: stage distribution + feedback quality."""
    _require_admin(user)

    # Stage distribution
    stage_pipeline = [
        {"$match": {"coaching_stage": {"$exists": True}}},
        {"$group": {"_id": "$coaching_stage", "count": {"$sum": 1}}},
    ]
    stages = await db.user_features.aggregate(stage_pipeline).to_list(10)
    stage_distribution = {s["_id"]: s["count"] for s in stages}

    # Average feedback rating
    feedback_pipeline = [
        {"$group": {
            "_id": "$endpoint",
            "avg_rating": {"$avg": "$rating"},
            "total_ratings": {"$sum": 1},
        }},
    ]
    feedback = await db.ai_response_feedback.aggregate(feedback_pipeline).to_list(20)

    # Coach suggestions followed rate
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    followed = await db.event_log.count_documents({
        "event_type": "coach_suggestion_followed",
        "timestamp": {"$gte": week_ago},
    })
    coach_served = await db.event_log.count_documents({
        "event_type": "ai_coach_served",
        "timestamp": {"$gte": week_ago},
    })

    return {
        "stage_distribution": stage_distribution,
        "feedback_by_endpoint": {f["_id"]: {
            "avg_rating": round(f["avg_rating"], 2),
            "total": f["total_ratings"],
        } for f in feedback},
        "suggestion_follow_rate": round(followed / max(coach_served, 1), 3),
        "coach_served_7d": coach_served,
        "suggestions_followed_7d": followed,
    }


# ═══════════════════════════════════════════════════════════════════════════
# 3. MEMORY — AI memory stats
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/memory")
async def get_memory_stats(user: dict = Depends(get_current_user)):
    """AI memory extraction and retention stats."""
    _require_admin(user)

    # Category distribution
    cat_pipeline = [
        {"$match": {"superseded_by": None}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
    ]
    categories = await db.ai_memories.aggregate(cat_pipeline).to_list(10)

    # Extraction rate (last 7 days)
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    recent_memories = await db.ai_memories.count_documents({
        "created_at": {"$gte": week_ago},
    })

    # Users with memories
    users_with_memories = len(await db.ai_memories.distinct("user_id", {"superseded_by": None}))

    # Avg memories per user
    total = await db.ai_memories.count_documents({"superseded_by": None})

    return {
        "total_active_memories": total,
        "users_with_memories": users_with_memories,
        "avg_memories_per_user": round(total / max(users_with_memories, 1), 1),
        "memories_extracted_7d": recent_memories,
        "category_distribution": {c["_id"]: c["count"] for c in categories},
    }


# ═══════════════════════════════════════════════════════════════════════════
# 4. COSTS — AI spending breakdown
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/costs")
async def get_cost_stats(user: dict = Depends(get_current_user)):
    """AI cost breakdown by endpoint, model, and cache savings."""
    _require_admin(user)

    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

    # Cost by endpoint
    by_endpoint = await db.ai_usage.aggregate([
        {"$match": {"created_at": {"$gte": week_ago}}},
        {"$group": {
            "_id": "$caller",
            "total_cost": {"$sum": "$estimated_cost_usd"},
            "total_calls": {"$sum": 1},
            "avg_input_tokens": {"$avg": "$input_tokens"},
            "avg_output_tokens": {"$avg": "$output_tokens"},
        }},
        {"$sort": {"total_cost": -1}},
    ]).to_list(20)

    # Cost by model
    by_model = await db.ai_usage.aggregate([
        {"$match": {"created_at": {"$gte": week_ago}}},
        {"$group": {
            "_id": "$model",
            "total_cost": {"$sum": "$estimated_cost_usd"},
            "total_calls": {"$sum": 1},
        }},
    ]).to_list(10)

    # Cache hit rate
    cache_pipeline = await db.ai_usage.aggregate([
        {"$match": {"created_at": {"$gte": week_ago}, "cache_hit": {"$exists": True}}},
        {"$group": {
            "_id": None,
            "total": {"$sum": 1},
            "hits": {"$sum": {"$cond": ["$cache_hit", 1, 0]}},
            "cache_read_tokens": {"$sum": {"$ifNull": ["$cache_read_input_tokens", 0]}},
            "cache_write_tokens": {"$sum": {"$ifNull": ["$cache_creation_input_tokens", 0]}},
        }},
    ]).to_list(1)
    cache_stats = cache_pipeline[0] if cache_pipeline else {"total": 0, "hits": 0}

    return {
        "cost_by_endpoint_7d": [{
            "endpoint": e["_id"],
            "cost_usd": round(e["total_cost"], 4),
            "calls": e["total_calls"],
            "avg_input_tokens": round(e.get("avg_input_tokens", 0)),
            "avg_output_tokens": round(e.get("avg_output_tokens", 0)),
        } for e in by_endpoint],
        "cost_by_model_7d": [{
            "model": m["_id"],
            "cost_usd": round(m["total_cost"], 4),
            "calls": m["total_calls"],
        } for m in by_model],
        "cache_hit_rate": round(cache_stats.get("hits", 0) / max(cache_stats.get("total", 1), 1), 3),
        "cache_read_tokens_7d": cache_stats.get("cache_read_tokens", 0),
    }


# ═══════════════════════════════════════════════════════════════════════════
# 5. COLLECTIVE — Pattern stats
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/collective")
async def get_collective_stats(user: dict = Depends(get_current_user)):
    """Collective intelligence pattern stats."""
    _require_admin(user)

    patterns = await db.collective_patterns.find(
        {}, {"_id": 0}
    ).to_list(50)

    # History count (trend tracking)
    history_count = await db.collective_patterns_history.count_documents({})

    return {
        "active_patterns": len(patterns),
        "patterns": patterns,
        "history_versions": history_count,
    }


# ═══════════════════════════════════════════════════════════════════════════
# 6. DRIFT — Users at risk
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/drift")
async def get_drift_stats(user: dict = Depends(get_current_user)):
    """Behavioral drift detection stats."""
    _require_admin(user)

    # Users with negative engagement trend
    drifting = await db.user_features.count_documents({
        "engagement_trend": {"$lt": -0.3},
        "total_sessions": {"$gte": 5},
    })

    # Users with high abandonment
    high_abandon = await db.user_features.count_documents({
        "abandonment_rate": {"$gt": 0.4},
        "total_sessions": {"$gte": 5},
    })

    # Users with category fatigue
    fatigued_pipeline = [
        {"$match": {"category_fatigue": {"$ne": {}}}},
        {"$count": "total"},
    ]
    fatigued = await db.user_features.aggregate(fatigued_pipeline).to_list(1)

    return {
        "users_drifting": drifting,
        "users_high_abandonment": high_abandon,
        "users_category_fatigued": fatigued[0]["total"] if fatigued else 0,
    }


# ═══════════════════════════════════════════════════════════════════════════
# 7. FEATURE TRENDS — Historical evolution
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/feature-trends")
async def get_feature_trends(user: dict = Depends(get_current_user)):
    """Feature evolution trends from historical snapshots."""
    _require_admin(user)

    # Aggregate daily averages from user_features_history (last 30 days)
    month_ago = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
    pipeline = [
        {"$match": {"snapshot_date": {"$gte": month_ago}}},
        {"$group": {
            "_id": "$snapshot_date",
            "avg_completion": {"$avg": "$completion_rate_global"},
            "avg_consistency": {"$avg": "$consistency_index"},
            "avg_engagement": {"$avg": "$engagement_trend"},
            "user_count": {"$sum": 1},
        }},
        {"$sort": {"_id": 1}},
    ]
    trends = await db.user_features_history.aggregate(pipeline).to_list(31)

    return {
        "daily_trends": [{
            "date": t["_id"],
            "avg_completion_rate": round(t["avg_completion"], 3) if t["avg_completion"] else None,
            "avg_consistency": round(t["avg_consistency"], 3) if t["avg_consistency"] else None,
            "avg_engagement_trend": round(t["avg_engagement"], 3) if t["avg_engagement"] else None,
            "users_computed": t["user_count"],
        } for t in trends],
    }
