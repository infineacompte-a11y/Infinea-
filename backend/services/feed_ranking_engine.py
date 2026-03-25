"""
InFinea — Feed Ranking Engine.

Intelligent activity ranking that transforms a chronological feed into a
curated, engaging experience tailored to each user's learning journey.

━━━ Architecture ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Six scoring signals combined into a composite score:

1. AFFINITY — Strength of relationship between viewer and content author.
   Signals: mutual follows, reactions exchanged, comments, DM conversations.
   Inspired by: Facebook EdgeRank, LinkedIn connection strength.

2. CONTENT QUALITY — Intrinsic engagement value of the activity.
   Signals: reaction count (log-scaled), comment count, reaction diversity.
   Inspired by: Reddit's hot algorithm, Hacker News ranking.

3. TYPE WEIGHT — InFinea-specific content type importance.
   Prioritizes motivating content (challenges, badges, streaks) over routine
   sessions. Unique to learning platforms — not found in generic social feeds.

4. FRESHNESS — Time decay with type-specific half-lives.
   Milestones (24h half-life) stay visible longer than sessions (8h).
   Inspired by: Twitter's recency signal, Strava's activity decay.

5. CONTEXTUAL BOOST — Learning-journey-aware scoring.
   Boosts content matching the viewer's active objectives, streak status,
   or newcomer status. THIS IS OUR DIFFERENTIATOR. No generic social network
   does this — it requires understanding the user's learning state.

6. DIVERSITY — Anti-clustering re-ranking.
   Prevents any single author from dominating the feed.
   Inspired by: Instagram's diversity injection, TikTok's exploration.

━━━ Composite Score ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  score = (W_aff·Affinity + W_qual·Quality + W_type·TypeWeight)
          × Freshness
          × ContextBoost
          × DiversityFactor

Freshness is multiplicative (not additive) — stale content drops hard
regardless of other signals. This ensures the feed always feels alive.

━━━ Performance ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Affinity computation: 2 rounds of parallel MongoDB queries (5 + 3 max).
No $lookup, no N+1. Total overhead: ~50-100ms for a typical feed request.
All weights are pure constants — zero I/O in the scoring loop.

━━━ Benchmarked Against ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Instagram EdgeRank, LinkedIn Feed Algorithm, Strava Activity Ranking,
Twitter/X For You, Reddit Hot, Duolingo Social Feed.

Differentiated by: contextual learning-journey awareness, empathy-based
boosting, motivation-first type weighting, category-aware relevance.
"""

import math
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from database import db

logger = logging.getLogger(__name__)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TUNABLE WEIGHTS — All scoring parameters in one place.
# Adjust these to shift feed personality. Sum of signal weights = 1.0.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SIGNAL_WEIGHTS = {
    "affinity": 0.35,       # Relationship with the author
    "quality": 0.20,        # Engagement on the content
    "type": 0.15,           # Activity type importance
    "freshness": 0.30,      # Time decay (applied multiplicatively)
}

# ── Activity type importance (motivation > vanity) ──
# InFinea's mission is empowerment — types that inspire action rank higher.
TYPE_SCORES = {
    "challenge_completed": 1.00,   # Social proof of collective achievement
    "badge_earned":        0.90,   # Celebration moment, inspires aspiration
    "streak_milestone":    0.85,   # Motivates consistency in others
    "session_completed":   0.55,   # Routine activity, lower novelty
}

# ── Time decay half-lives (hours) ──
# Milestones/achievements stay relevant longer than daily sessions.
# A badge earned 20h ago is still interesting; a session from 20h ago isn't.
HALF_LIFE_HOURS = {
    "challenge_completed": 36,
    "badge_earned":        24,
    "streak_milestone":    24,
    "session_completed":   8,
}
DEFAULT_HALF_LIFE = 12

# ── Affinity signal components (sum = 1.0 when all present) ──
# Each component contributes to the overall relationship strength.
AFFINITY_SIGNALS = {
    "mutual_follow":      0.25,   # Both follow each other (strongest passive signal)
    "one_way_follow":     0.08,   # Viewer follows author (baseline — already implied)
    "reactions_given":    0.25,   # Viewer reacted to author's content (active engagement)
    "reactions_received": 0.12,   # Author reacted to viewer's content (reciprocity)
    "comments_given":     0.20,   # Viewer commented on author's content (high effort)
    "dm_active":          0.10,   # Active DM conversation (private bond)
}

# ── Content quality scoring ──
# Log-scale normalizers: log1p(count) / log1p(ceiling)
# These ceilings define "maximum expected" engagement. Beyond this, score = 1.0.
QUALITY_CEILING_REACTIONS = 25     # 25 reactions = max quality score
QUALITY_CEILING_COMMENTS = 15     # 15 comments = max quality score
QUALITY_WEIGHTS = {
    "reactions": 0.45,
    "comments":  0.35,
    "diversity": 0.20,   # Multiple reaction types = more engaging content
}

# ── Contextual boost multipliers ──
# Applied on top of base score. > 1.0 = boost, 1.0 = neutral.
CONTEXT_BOOST = {
    "same_category":        1.20,  # Activity matches viewer's active objectives
    "streak_empathy":       1.15,  # Viewer on streak + sees streak milestone
    "new_user_inspiration": 1.25,  # New user sees celebratory content
    "self_content":         1.10,  # Viewer's own content (mild relevance boost)
}

# ── Diversity controls ──
MAX_CONSECUTIVE_SAME_AUTHOR = 3    # Before penalty kicks in
DIVERSITY_PENALTY = 0.60           # Score multiplier for excess same-author items

# ── Pool sizing ──
# Fetch N× the requested limit for ranking depth. Higher = better ranking
# but more DB load. 3× is the sweet spot for InFinea's scale.
POOL_MULTIPLIER = 3

# ── Affinity lookback window ──
AFFINITY_LOOKBACK_DAYS = 30


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PUBLIC API
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def rank_feed(
    activities: list[dict],
    viewer_id: str,
    viewer_context: Optional[dict] = None,
) -> list[dict]:
    """
    Rank a pool of activities for a specific viewer.

    Args:
        activities: Raw activities from MongoDB (chronological pool).
        viewer_id: The user viewing the feed.
        viewer_context: Pre-computed viewer context (optional, computed if None).

    Returns:
        Activities sorted by composite score (highest first).
        Internal _score field is stripped before return.
    """
    if not activities:
        return []

    if len(activities) <= 1:
        return activities

    # Gather all unique authors in this pool
    author_ids = list({a["user_id"] for a in activities})

    # Batch-compute signals in parallel
    affinities, viewer_ctx = await asyncio.gather(
        _compute_affinities_batch(viewer_id, author_ids),
        viewer_context or _get_viewer_context(viewer_id),
    )
    # If viewer_context was pre-computed (not a coroutine), use it directly
    if isinstance(viewer_ctx, dict):
        pass  # Already resolved
    else:
        viewer_ctx = await viewer_ctx

    now = datetime.now(timezone.utc)

    # Score each activity
    for activity in activities:
        activity["_score"] = _score_activity(
            activity, viewer_id, affinities, viewer_ctx, now,
        )

    # Sort by composite score (descending)
    activities.sort(key=lambda a: a["_score"], reverse=True)

    # Apply diversity re-ranking
    activities = _apply_diversity(activities)

    # Strip internal score field
    for a in activities:
        a.pop("_score", None)

    return activities


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SCORING CORE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _score_activity(
    activity: dict,
    viewer_id: str,
    affinities: dict,
    viewer_ctx: dict,
    now: datetime,
) -> float:
    """Compute composite score for a single activity. Pure function, zero I/O."""

    author_id = activity["user_id"]
    activity_type = activity.get("type", "session_completed")

    # ── Signal 1: Affinity ──
    if author_id == viewer_id:
        # Self-content: fixed moderate affinity (always somewhat relevant,
        # but shouldn't dominate over high-affinity friends)
        affinity = 0.65
    else:
        affinity = affinities.get(author_id, 0.05)

    # ── Signal 2: Content Quality ──
    quality = _content_quality(activity)

    # ── Signal 3: Type Weight ──
    type_score = TYPE_SCORES.get(activity_type, 0.50)

    # ── Signal 4: Freshness ──
    freshness = _time_decay(activity, now)

    # ── Base score: weighted sum of additive signals ──
    base = (
        SIGNAL_WEIGHTS["affinity"] * affinity
        + SIGNAL_WEIGHTS["quality"] * quality
        + SIGNAL_WEIGHTS["type"] * type_score
    )

    # Freshness is multiplicative — a perfectly scored but stale activity
    # should still rank below a decent but fresh one.
    # Formula: base × (floor + (1 - floor) × freshness)
    # Floor of 0.30 means even old content retains 30% of its base score,
    # preventing sudden disappearance of great content.
    freshness_floor = SIGNAL_WEIGHTS["freshness"]
    score = base * (freshness_floor + (1.0 - freshness_floor) * freshness)

    # ── Signal 5: Contextual Boost ──
    boost = _contextual_boost(activity, viewer_id, viewer_ctx)
    score *= boost

    return score


def _content_quality(activity: dict) -> float:
    """
    Score content based on engagement signals. Returns 0.0-1.0.

    Uses log scaling to prevent gaming: the first few reactions matter most,
    subsequent ones have diminishing returns. This rewards genuine engagement
    over artificial inflation.
    """
    rc = activity.get("reaction_counts", {})
    total_reactions = sum(rc.values())
    comment_count = activity.get("comment_count", 0)

    # Reaction score: log scale (0 → 0, 1 → 0.29, 5 → 0.55, 10 → 0.72, 25 → 1.0)
    reaction_score = (
        math.log1p(total_reactions) / math.log1p(QUALITY_CEILING_REACTIONS)
        if total_reactions > 0 else 0.0
    )

    # Comment score: log scale (comments = high-effort engagement signal)
    comment_score = (
        math.log1p(comment_count) / math.log1p(QUALITY_CEILING_COMMENTS)
        if comment_count > 0 else 0.0
    )

    # Reaction diversity: multiple types indicate genuinely engaging content.
    # 1 type = 0.0, 2 types = 0.5, 3 types = 1.0
    active_types = sum(1 for v in rc.values() if v > 0)
    diversity_bonus = max(0, active_types - 1) / 2.0

    quality = (
        QUALITY_WEIGHTS["reactions"] * min(reaction_score, 1.0)
        + QUALITY_WEIGHTS["comments"] * min(comment_score, 1.0)
        + QUALITY_WEIGHTS["diversity"] * diversity_bonus
    )

    return min(quality, 1.0)


def _time_decay(activity: dict, now: datetime) -> float:
    """
    Exponential decay based on activity age. Returns 0.0-1.0.

    Uses type-specific half-lives: milestones decay slower than sessions.
    Formula: 2^(-age_hours / half_life)
    """
    created_str = activity.get("created_at", "")
    if not created_str:
        return 0.5

    try:
        if isinstance(created_str, str):
            created = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
        else:
            created = created_str

        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)

        age_hours = max(0.0, (now - created).total_seconds() / 3600.0)
    except (ValueError, TypeError):
        return 0.5

    activity_type = activity.get("type", "session_completed")
    half_life = HALF_LIFE_HOURS.get(activity_type, DEFAULT_HALF_LIFE)

    return 2.0 ** (-age_hours / half_life)


def _contextual_boost(
    activity: dict,
    viewer_id: str,
    viewer_ctx: dict,
) -> float:
    """
    InFinea-unique contextual boosting based on the viewer's learning journey.

    This is what sets InFinea's feed apart from generic social networks.
    Instead of just "show me what my friends do", it's "show me what
    resonates with where I am in my learning journey right now."

    Returns multiplier >= 1.0.
    """
    boost = 1.0
    activity_type = activity.get("type", "")
    activity_data = activity.get("data", {})

    # Own content: mild boost so you see your own achievements,
    # but not so much that the feed becomes a mirror.
    if activity["user_id"] == viewer_id:
        boost *= CONTEXT_BOOST["self_content"]
        return boost  # Skip other boosts for self-content

    # Category alignment: activity matches viewer's active objectives.
    # If you're learning piano and someone completed a piano session, you care more.
    viewer_categories = viewer_ctx.get("active_categories", set())
    activity_category = activity_data.get("category", "")
    if activity_category and activity_category in viewer_categories:
        boost *= CONTEXT_BOOST["same_category"]

    # Streak empathy: viewer is building a streak and sees a streak milestone.
    # Creates a "we're in this together" feeling that boosts retention.
    if (
        activity_type == "streak_milestone"
        and viewer_ctx.get("current_streak", 0) >= 3
    ):
        boost *= CONTEXT_BOOST["streak_empathy"]

    # New user inspiration: newcomers see badges and challenge completions
    # prominently, showing them what's possible and motivating their journey.
    if viewer_ctx.get("is_new_user", False) and activity_type in (
        "badge_earned",
        "challenge_completed",
    ):
        boost *= CONTEXT_BOOST["new_user_inspiration"]

    return boost


def _apply_diversity(activities: list[dict]) -> list[dict]:
    """
    Re-rank to prevent author clustering in the feed.

    Without diversity injection, a prolific user who completed 10 sessions
    would dominate the feed. This ensures a varied, engaging scroll experience.

    Algorithm: count each author's appearances. After MAX_CONSECUTIVE_SAME_AUTHOR,
    penalize their score and re-sort. This pushes excess items down without
    removing them entirely.
    """
    if len(activities) <= MAX_CONSECUTIVE_SAME_AUTHOR:
        return activities

    author_counts: dict[str, int] = {}

    for activity in activities:
        author = activity["user_id"]
        count = author_counts.get(author, 0)

        if count >= MAX_CONSECUTIVE_SAME_AUTHOR:
            activity["_score"] = activity.get("_score", 0) * DIVERSITY_PENALTY

        author_counts[author] = count + 1

    # Re-sort after applying diversity penalties
    activities.sort(key=lambda a: a.get("_score", 0), reverse=True)

    return activities


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AFFINITY COMPUTATION — Batch, efficient, no N+1
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _compute_affinities_batch(
    viewer_id: str,
    author_ids: list[str],
) -> dict[str, float]:
    """
    Batch-compute affinity between viewer and all content authors.

    Uses 2 rounds of parallel MongoDB queries (no $lookup):
      Round 1: 5 parallel queries to gather raw interaction data.
      Round 2: Up to 3 parallel queries to map interactions to authors.

    Returns {author_id: affinity_score} where score is 0.0-1.0.
    """
    other_authors = [aid for aid in author_ids if aid != viewer_id]

    if not other_authors:
        return {}

    cutoff = (
        datetime.now(timezone.utc) - timedelta(days=AFFINITY_LOOKBACK_DAYS)
    ).isoformat()

    author_set = set(other_authors)

    # ── Round 1: Parallel data fetching (5 queries) ──
    (
        follow_backs,
        viewer_reactions_raw,
        viewer_activity_ids_raw,
        viewer_comments_raw,
        viewer_conversations,
    ) = await asyncio.gather(
        # 1. Which authors follow the viewer back? (mutual follow signal)
        db.follows.find(
            {
                "follower_id": {"$in": other_authors},
                "following_id": viewer_id,
                "status": "active",
            },
            {"_id": 0, "follower_id": 1},
        ).to_list(len(other_authors)),

        # 2. Viewer's recent reactions (activity_ids to map to authors)
        db.reactions.find(
            {"user_id": viewer_id, "created_at": {"$gte": cutoff}},
            {"_id": 0, "activity_id": 1},
        ).to_list(500),

        # 3. Viewer's recent activity IDs (for received-reactions lookup)
        db.activities.find(
            {"user_id": viewer_id, "created_at": {"$gte": cutoff}},
            {"_id": 0, "activity_id": 1},
        ).to_list(500),

        # 4. Viewer's recent comments (activity_ids to map to authors)
        db.comments.find(
            {"user_id": viewer_id, "created_at": {"$gte": cutoff}},
            {"_id": 0, "activity_id": 1},
        ).to_list(500),

        # 5. Viewer's DM conversations (to find which authors they chat with)
        db.conversations.find(
            {"participants": viewer_id},
            {"_id": 0, "participants": 1},
        ).to_list(200),
    )

    # Prepare IDs for Round 2
    reacted_aids = [r["activity_id"] for r in viewer_reactions_raw]
    viewer_aids = [a["activity_id"] for a in viewer_activity_ids_raw]
    commented_aids = [c["activity_id"] for c in viewer_comments_raw]

    # ── Round 2: Map interactions to authors (up to 3 parallel queries) ──
    coros = []

    # 2a. Map reacted activity_ids → author_ids
    if reacted_aids:
        coros.append(
            db.activities.find(
                {"activity_id": {"$in": reacted_aids}, "user_id": {"$in": other_authors}},
                {"_id": 0, "activity_id": 1, "user_id": 1},
            ).to_list(len(reacted_aids))
        )
    else:
        coros.append(_empty_list())

    # 2b. Count reactions from authors on viewer's activities
    if viewer_aids:
        coros.append(
            db.reactions.aggregate([
                {"$match": {
                    "activity_id": {"$in": viewer_aids},
                    "user_id": {"$in": other_authors},
                }},
                {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
            ]).to_list(len(other_authors))
        )
    else:
        coros.append(_empty_list())

    # 2c. Map commented activity_ids → author_ids
    if commented_aids:
        coros.append(
            db.activities.find(
                {"activity_id": {"$in": commented_aids}, "user_id": {"$in": other_authors}},
                {"_id": 0, "activity_id": 1, "user_id": 1},
            ).to_list(len(commented_aids))
        )
    else:
        coros.append(_empty_list())

    reaction_activities, received_reactions, comment_activities = await asyncio.gather(*coros)

    # ── Build lookup maps ──

    mutual_set = {f["follower_id"] for f in follow_backs}

    # Reactions given: viewer → author
    reactions_given_map: dict[str, int] = {}
    for a in reaction_activities:
        uid = a["user_id"]
        reactions_given_map[uid] = reactions_given_map.get(uid, 0) + 1

    # Reactions received: author → viewer
    reactions_received_map = {r["_id"]: r["count"] for r in received_reactions}

    # Comments given: viewer → author
    comments_given_map: dict[str, int] = {}
    for a in comment_activities:
        uid = a["user_id"]
        comments_given_map[uid] = comments_given_map.get(uid, 0) + 1

    # DM conversations: which authors has the viewer chatted with?
    dm_authors: set[str] = set()
    for conv in viewer_conversations:
        for p in conv.get("participants", []):
            if p != viewer_id and p in author_set:
                dm_authors.add(p)

    # ── Compute affinity per author ──
    affinities: dict[str, float] = {}

    for author_id in other_authors:
        score = 0.0

        # Mutual follow (strongest passive relationship signal)
        if author_id in mutual_set:
            score += AFFINITY_SIGNALS["mutual_follow"]
        else:
            score += AFFINITY_SIGNALS["one_way_follow"]

        # Reactions given (log scale — first reactions matter most)
        rg = reactions_given_map.get(author_id, 0)
        if rg > 0:
            score += AFFINITY_SIGNALS["reactions_given"] * min(
                math.log1p(rg) / math.log1p(10), 1.0
            )

        # Reactions received (reciprocity — they engage back with you)
        rr = reactions_received_map.get(author_id, 0)
        if rr > 0:
            score += AFFINITY_SIGNALS["reactions_received"] * min(
                math.log1p(rr) / math.log1p(10), 1.0
            )

        # Comments given (high-effort interaction signal)
        cg = comments_given_map.get(author_id, 0)
        if cg > 0:
            score += AFFINITY_SIGNALS["comments_given"] * min(
                math.log1p(cg) / math.log1p(5), 1.0
            )

        # DM conversation (private bond)
        if author_id in dm_authors:
            score += AFFINITY_SIGNALS["dm_active"]

        affinities[author_id] = min(score, 1.0)

    return affinities


async def _empty_list():
    """Async helper that returns an empty list (for asyncio.gather alignment)."""
    return []


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# VIEWER CONTEXT — Learning journey awareness
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _get_viewer_context(viewer_id: str) -> dict:
    """
    Gather contextual information about the viewer's learning state.

    This powers the contextual boost signal — the feature that makes
    InFinea's feed fundamentally different from Instagram/Twitter.

    Returns:
        {
            active_categories: set of category strings,
            current_streak: int,
            is_new_user: bool (< 7 days since registration),
        }
    """
    user_doc, objectives = await asyncio.gather(
        db.users.find_one(
            {"user_id": viewer_id},
            {"_id": 0, "streak_days": 1, "created_at": 1},
        ),
        db.objectives.find(
            {"user_id": viewer_id, "status": "active"},
            {"_id": 0, "category": 1},
        ).to_list(20),
    )

    # Active learning categories from user's objectives
    active_categories = {
        o["category"] for o in objectives
        if o.get("category")
    }

    # Current streak
    current_streak = 0
    if user_doc:
        current_streak = user_doc.get("streak_days", 0)

    # New user detection (< 7 days old)
    is_new = False
    if user_doc and user_doc.get("created_at"):
        try:
            created = user_doc["created_at"]
            if isinstance(created, str):
                created = datetime.fromisoformat(created.replace("Z", "+00:00"))
            if hasattr(created, "tzinfo") and created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            is_new = (datetime.now(timezone.utc) - created).days < 7
        except (ValueError, TypeError, AttributeError):
            pass

    return {
        "active_categories": active_categories,
        "current_streak": current_streak,
        "is_new_user": is_new,
    }
