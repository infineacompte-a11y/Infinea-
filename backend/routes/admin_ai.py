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
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query

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


# ═══════════════════════════════════════════════════════════════════════════
# 8. USERS DRILL-DOWN — Individual user AI profiles
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/users")
async def get_ai_users(
    user: dict = Depends(get_current_user),
    sort: str = Query("engagement_trend", description="Sort field"),
    order: str = Query("asc", description="asc or desc"),
    stage: Optional[str] = Query(None, description="Filter by coaching stage"),
    limit: int = Query(20, ge=1, le=100),
):
    """List users with their AI features for drill-down analysis."""
    _require_admin(user)

    query = {}
    if stage:
        query["coaching_stage"] = stage

    sort_dir = 1 if order == "asc" else -1
    users_features = await db.user_features.find(
        query,
        {"_id": 0, "user_id": 1, "completion_rate_global": 1, "consistency_index": 1,
         "engagement_trend": 1, "total_sessions": 1, "total_completed": 1,
         "abandonment_rate": 1, "session_momentum": 1, "coaching_stage": 1,
         "active_days_last_30": 1, "preferred_action_duration": 1, "computed_at": 1},
    ).sort(sort, sort_dir).limit(limit).to_list(limit)

    # Enrich with user names
    user_ids = [f["user_id"] for f in users_features]
    users_docs = await db.users.find(
        {"user_id": {"$in": user_ids}},
        {"_id": 0, "user_id": 1, "name": 1, "display_name": 1, "email": 1, "streak_days": 1},
    ).to_list(len(user_ids))
    user_map = {u["user_id"]: u for u in users_docs}

    # Enrich with memory count
    memory_pipeline = [
        {"$match": {"user_id": {"$in": user_ids}, "superseded_by": None}},
        {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
    ]
    memory_counts = await db.ai_memories.aggregate(memory_pipeline).to_list(len(user_ids))
    mem_map = {m["_id"]: m["count"] for m in memory_counts}

    result = []
    for f in users_features:
        uid = f["user_id"]
        u = user_map.get(uid, {})
        result.append({
            **f,
            "name": u.get("display_name") or u.get("name", "Inconnu"),
            "email": u.get("email", ""),
            "streak_days": u.get("streak_days", 0),
            "memories_count": mem_map.get(uid, 0),
        })

    return {"users": result, "total": len(result)}


# ═══════════════════════════════════════════════════════════════════════════
# 9. WEEK-OVER-WEEK COMPARISON
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/comparison")
async def get_weekly_comparison(user: dict = Depends(get_current_user)):
    """Compare this week vs last week across key metrics."""
    _require_admin(user)

    now = datetime.now(timezone.utc)
    this_week_start = (now - timedelta(days=7)).isoformat()
    last_week_start = (now - timedelta(days=14)).isoformat()
    last_week_end = (now - timedelta(days=7)).isoformat()

    async def count_events(event_type, start, end=None):
        q = {"event_type": event_type, "timestamp": {"$gte": start}}
        if end:
            q["timestamp"]["$lt"] = end
        return await db.event_log.count_documents(q)

    async def sum_costs(start, end=None):
        q = {"created_at": {"$gte": start}}
        if end:
            q["created_at"]["$lt"] = end
        pipeline = [{"$match": q}, {"$group": {"_id": None, "total": {"$sum": "$estimated_cost_usd"}}}]
        r = await db.ai_usage.aggregate(pipeline).to_list(1)
        return round(r[0]["total"], 4) if r else 0

    # This week
    tw_sessions = await count_events("action_completed", this_week_start)
    tw_coach = await count_events("ai_coach_served", this_week_start)
    tw_cost = await sum_costs(this_week_start)
    tw_active = len(await db.user_sessions_history.distinct("user_id", {"started_at": {"$gte": this_week_start}}))

    # Last week
    lw_sessions = await count_events("action_completed", last_week_start, last_week_end)
    lw_coach = await count_events("ai_coach_served", last_week_start, last_week_end)
    lw_cost = await sum_costs(last_week_start, last_week_end)
    lw_active = len(await db.user_sessions_history.distinct("user_id", {"started_at": {"$gte": last_week_start, "$lt": last_week_end}}))

    def delta(current, previous):
        if previous == 0:
            return 100 if current > 0 else 0
        return round(((current - previous) / previous) * 100, 1)

    return {
        "this_week": {"sessions": tw_sessions, "coach_served": tw_coach, "cost_usd": tw_cost, "active_users": tw_active},
        "last_week": {"sessions": lw_sessions, "coach_served": lw_coach, "cost_usd": lw_cost, "active_users": lw_active},
        "deltas": {
            "sessions": delta(tw_sessions, lw_sessions),
            "coach_served": delta(tw_coach, lw_coach),
            "cost_usd": delta(tw_cost, lw_cost),
            "active_users": delta(tw_active, lw_active),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════
# 10. HEALTH CHECK — AI system status
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/health")
async def get_ai_health(user: dict = Depends(get_current_user)):
    """Comprehensive health check for the AI vertical system."""
    _require_admin(user)

    checks = {}
    now = datetime.now(timezone.utc)

    # 1. MongoDB connection
    try:
        await db.command("ping")
        checks["mongodb"] = {"status": "ok", "latency_ms": 0}
    except Exception as e:
        checks["mongodb"] = {"status": "error", "error": str(e)}

    # 2. Redis cache
    try:
        from services.cache import cache_ping
        redis_ok = await cache_ping()
        checks["redis"] = {"status": "ok" if redis_ok else "unavailable"}
    except Exception:
        checks["redis"] = {"status": "unavailable"}

    # 3. Claude API (check last successful call)
    try:
        last_ai = await db.ai_usage.find_one(
            {}, {"_id": 0, "created_at": 1, "model": 1},
            sort=[("created_at", -1)],
        )
        if last_ai:
            last_call_age = (now - datetime.fromisoformat(last_ai["created_at"])).total_seconds()
            checks["claude_api"] = {
                "status": "ok" if last_call_age < 3600 else "stale",
                "last_call_ago_seconds": int(last_call_age),
                "last_model": last_ai.get("model"),
            }
        else:
            checks["claude_api"] = {"status": "no_data"}
    except Exception:
        checks["claude_api"] = {"status": "error"}

    # 4. Feature computation
    try:
        last_run = await db.feature_computation_logs.find_one(
            {}, sort=[("computed_at", -1)]
        )
        if last_run:
            age = (now - datetime.fromisoformat(last_run["computed_at"])).total_seconds()
            checks["feature_computation"] = {
                "status": "ok" if age < 7 * 3600 else "overdue",
                "last_run_ago_hours": round(age / 3600, 1),
                "users_processed": last_run.get("users_processed", 0),
            }
        else:
            checks["feature_computation"] = {"status": "never_run"}
    except Exception:
        checks["feature_computation"] = {"status": "error"}

    # 5. AI memory system
    try:
        total_memories = await db.ai_memories.count_documents({"superseded_by": None})
        checks["ai_memory"] = {"status": "ok", "total_active": total_memories}
    except Exception:
        checks["ai_memory"] = {"status": "error"}

    # 6. Collective intelligence
    try:
        patterns = await db.collective_patterns.count_documents({})
        checks["collective_intelligence"] = {"status": "ok" if patterns > 0 else "no_patterns", "patterns": patterns}
    except Exception:
        checks["collective_intelligence"] = {"status": "error"}

    # Overall status
    all_ok = all(c.get("status") in ("ok", "unavailable", "no_patterns", "no_data") for c in checks.values())
    overall = "healthy" if all_ok else "degraded"

    return {
        "status": overall,
        "checks": checks,
        "timestamp": now.isoformat(),
    }


# ═══════════════════════════════════════════════════════════════════════════
# 11. MEMORY ANALYTICS — Deep analysis of AI memory effectiveness
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/memory-analytics")
async def get_memory_analytics(user: dict = Depends(get_current_user)):
    """Deep analytics on AI memory system effectiveness.

    Aggregates:
    - Category distribution + extraction frequency
    - Correlation between memory usage and coaching outcomes
    - Most common fact patterns
    - Memory lifecycle (creation → usage → expiry)
    """
    _require_admin(user)

    now = datetime.now(timezone.utc)
    month_ago = (now - timedelta(days=30)).isoformat()
    week_ago = (now - timedelta(days=7)).isoformat()

    # 1. Category distribution with extraction frequency
    cat_pipeline = [
        {"$match": {"superseded_by": None}},
        {"$group": {
            "_id": "$category",
            "count": {"$sum": 1},
            "avg_confidence": {"$avg": "$confidence"},
            "oldest": {"$min": "$created_at"},
            "newest": {"$max": "$created_at"},
        }},
        {"$sort": {"count": -1}},
    ]
    categories = await db.ai_memories.aggregate(cat_pipeline).to_list(10)

    # 2. Extraction rate over time (daily for last 30 days)
    daily_pipeline = [
        {"$match": {"created_at": {"$gte": month_ago}}},
        {"$group": {
            "_id": {"$substr": ["$created_at", 0, 10]},  # YYYY-MM-DD
            "extracted": {"$sum": 1},
        }},
        {"$sort": {"_id": 1}},
    ]
    daily_extractions = await db.ai_memories.aggregate(daily_pipeline).to_list(31)

    # 3. Users with most memories (top 10)
    top_users_pipeline = [
        {"$match": {"superseded_by": None}},
        {"$group": {
            "_id": "$user_id",
            "memory_count": {"$sum": 1},
            "categories": {"$addToSet": "$category"},
            "avg_confidence": {"$avg": "$confidence"},
        }},
        {"$sort": {"memory_count": -1}},
        {"$limit": 10},
    ]
    top_users = await db.ai_memories.aggregate(top_users_pipeline).to_list(10)

    # Enrich top users with names
    for u in top_users:
        user_doc = await db.users.find_one(
            {"user_id": u["_id"]}, {"_id": 0, "name": 1}
        )
        u["name"] = user_doc.get("name", "Inconnu") if user_doc else "Inconnu"

    # 4. Superseded memories stats (memory evolution)
    superseded_count = await db.ai_memories.count_documents({
        "superseded_by": {"$ne": None},
    })
    active_count = await db.ai_memories.count_documents({
        "superseded_by": None,
    })

    # 5. Memory usage correlation with coaching feedback
    # Users with memories vs without: compare coaching thumbs up rates
    users_with_mem = await db.ai_memories.distinct("user_id", {"superseded_by": None})

    feedback_with_mem = {"positive": 0, "negative": 0, "total": 0}
    feedback_without_mem = {"positive": 0, "negative": 0, "total": 0}

    try:
        # Get recent feedback
        recent_feedback = await db.ai_response_feedback.find(
            {"created_at": {"$gte": month_ago}},
            {"_id": 0, "user_id": 1, "rating": 1},
        ).to_list(500)

        for fb in recent_feedback:
            bucket = feedback_with_mem if fb.get("user_id") in users_with_mem else feedback_without_mem
            bucket["total"] += 1
            if fb.get("rating") == "up":
                bucket["positive"] += 1
            elif fb.get("rating") == "down":
                bucket["negative"] += 1
    except Exception:
        pass

    # 6. Most common fact patterns (word frequency in facts)
    # Simple top keywords from recent memories
    recent_facts = await db.ai_memories.find(
        {"superseded_by": None, "created_at": {"$gte": month_ago}},
        {"_id": 0, "fact": 1},
    ).to_list(200)

    word_freq = {}
    stop_words = {"le", "la", "les", "de", "du", "des", "un", "une", "a", "et",
                  "en", "est", "il", "elle", "que", "qui", "pour", "pas", "son",
                  "sa", "ses", "ce", "cette", "se", "ne", "au", "aux", "par"}
    for mem in recent_facts:
        words = mem.get("fact", "").lower().split()
        for w in words:
            w = w.strip(".,;:!?()[]")
            if len(w) > 2 and w not in stop_words:
                word_freq[w] = word_freq.get(w, 0) + 1

    top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]

    # 7. Extraction rate by source
    source_pipeline = [
        {"$match": {"created_at": {"$gte": week_ago}}},
        {"$group": {"_id": "$source", "count": {"$sum": 1}}},
    ]
    by_source = await db.ai_memories.aggregate(source_pipeline).to_list(5)

    return {
        "category_distribution": [
            {
                "category": c["_id"],
                "count": c["count"],
                "avg_confidence": round(c["avg_confidence"], 2),
                "oldest": c["oldest"],
                "newest": c["newest"],
            }
            for c in categories
        ],
        "daily_extractions": [
            {"date": d["_id"], "count": d["extracted"]}
            for d in daily_extractions
        ],
        "top_users": [
            {
                "user_id": u["_id"],
                "name": u["name"],
                "memory_count": u["memory_count"],
                "categories": u["categories"],
                "avg_confidence": round(u["avg_confidence"], 2),
            }
            for u in top_users
        ],
        "lifecycle": {
            "active": active_count,
            "superseded": superseded_count,
            "evolution_rate": round(superseded_count / max(active_count + superseded_count, 1), 2),
        },
        "correlation_with_feedback": {
            "users_with_memories": feedback_with_mem,
            "users_without_memories": feedback_without_mem,
            "satisfaction_lift": (
                round(
                    (feedback_with_mem["positive"] / max(feedback_with_mem["total"], 1))
                    - (feedback_without_mem["positive"] / max(feedback_without_mem["total"], 1)),
                    3,
                )
                if feedback_with_mem["total"] > 0
                else None
            ),
        },
        "top_keywords": [{"word": w, "count": c} for w, c in top_keywords],
        "extraction_by_source": {s["_id"]: s["count"] for s in by_source},
    }


# ═══════════════════════════════════════════════════════════════════════════
# 12. LIVE METRICS — Real-time Prometheus metrics for admin dashboard
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/live-metrics")
async def get_live_metrics(user: dict = Depends(get_current_user)):
    """Real-time system metrics from Prometheus collectors.

    Returns current values of all InFinea-specific metrics for display
    in the admin dashboard. No external service needed — reads directly
    from the in-process prometheus_client registry.
    """
    _require_admin(user)

    result = {
        "http": {},
        "llm": {},
        "circuit_breaker": {},
        "business": {},
        "jobs": {},
    }

    try:
        from services.metrics import (
            HTTP_REQUEST_COUNT, HTTP_REQUEST_DURATION,
            LLM_CALL_COUNT, LLM_CALL_DURATION, LLM_TOKENS, LLM_COST_USD, LLM_RETRIES,
            CIRCUIT_BREAKER_STATE,
            ACTIVE_USERS_DAILY, ACTIVE_USERS_WEEKLY,
            MEMORY_EXTRACTIONS, COACHING_SESSIONS,
            FEATURE_COMPUTATION_DURATION, FEATURE_COMPUTATION_USERS,
            BACKGROUND_JOB_STATUS,
        )

        # HTTP metrics — aggregate by endpoint
        http_by_endpoint = {}
        for sample in HTTP_REQUEST_COUNT.collect()[0].samples:
            endpoint = sample.labels.get("endpoint", "unknown")
            status = sample.labels.get("status_code", "0")
            if endpoint not in http_by_endpoint:
                http_by_endpoint[endpoint] = {"total": 0, "errors": 0}
            http_by_endpoint[endpoint]["total"] += int(sample.value)
            if status.startswith(("4", "5")):
                http_by_endpoint[endpoint]["errors"] += int(sample.value)
        result["http"]["by_endpoint"] = http_by_endpoint
        result["http"]["total_requests"] = sum(e["total"] for e in http_by_endpoint.values())

        # LLM metrics
        llm_by_model = {}
        for sample in LLM_CALL_COUNT.collect()[0].samples:
            model = sample.labels.get("model", "unknown")
            success = sample.labels.get("success", "True")
            if model not in llm_by_model:
                llm_by_model[model] = {"calls": 0, "failures": 0}
            llm_by_model[model]["calls"] += int(sample.value)
            if success == "False":
                llm_by_model[model]["failures"] += int(sample.value)
        result["llm"]["by_model"] = llm_by_model

        # LLM tokens
        total_tokens = {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0}
        for sample in LLM_TOKENS.collect()[0].samples:
            token_type = sample.labels.get("token_type", "input")
            total_tokens[token_type] = int(sample.value)
        result["llm"]["tokens"] = total_tokens

        # LLM cost
        total_cost = 0
        for sample in LLM_COST_USD.collect()[0].samples:
            total_cost += sample.value
        result["llm"]["total_cost_usd"] = round(total_cost, 4)

        # LLM retries
        total_retries = 0
        for sample in LLM_RETRIES.collect()[0].samples:
            total_retries += int(sample.value)
        result["llm"]["total_retries"] = total_retries

        # Circuit breaker
        for sample in CIRCUIT_BREAKER_STATE.collect()[0].samples:
            provider = sample.labels.get("provider", "unknown")
            state_val = int(sample.value)
            state_name = {0: "closed", 1: "open", 2: "half_open"}.get(state_val, "unknown")
            result["circuit_breaker"][provider] = state_name

        # Also get detailed CB status from llm_provider
        try:
            from services.llm_provider import get_circuit_breaker_status
            result["circuit_breaker_detail"] = get_circuit_breaker_status()
        except Exception:
            pass

        # Business metrics
        result["business"]["active_users_daily"] = ACTIVE_USERS_DAILY._value.get()
        result["business"]["active_users_weekly"] = ACTIVE_USERS_WEEKLY._value.get()

        # Coaching sessions by endpoint
        coaching_by_endpoint = {}
        for sample in COACHING_SESSIONS.collect()[0].samples:
            ep = sample.labels.get("endpoint", "unknown")
            coaching_by_endpoint[ep] = int(sample.value)
        result["business"]["coaching_sessions"] = coaching_by_endpoint

        # Memory extractions by category
        memory_by_cat = {}
        for sample in MEMORY_EXTRACTIONS.collect()[0].samples:
            cat = sample.labels.get("category", "unknown")
            memory_by_cat[cat] = int(sample.value)
        result["business"]["memory_extractions"] = memory_by_cat

        # Background jobs
        result["jobs"]["feature_computation"] = {
            "users_processed": FEATURE_COMPUTATION_USERS._value.get(),
        }
        job_last_success = {}
        for sample in BACKGROUND_JOB_STATUS.collect()[0].samples:
            job_name = sample.labels.get("job_name", "unknown")
            ts = sample.value
            if ts > 0:
                job_last_success[job_name] = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
        result["jobs"]["last_success"] = job_last_success

    except ImportError:
        result["error"] = "prometheus_client not available"
    except Exception as e:
        result["error"] = str(e)[:200]

    return result
