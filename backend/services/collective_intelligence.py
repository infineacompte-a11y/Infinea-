"""
InFinea — Collective Intelligence Service.

Aggregates anonymized behavioral patterns across all users to generate
system-level insights that enhance individual coaching.

Runs as a weekly background job. Computes patterns with minimum sample
size of 50 users to ensure statistical significance and privacy.

Pattern types:
1. optimal_sequences: "Users who completed X often succeed at Y next"
2. category_affinities: "Users who engage in learning also do well in creativity"
3. time_effectiveness: "Morning sessions have 23% higher completion globally"
4. streak_builders: "Users who hit 7-day streaks most often start with well_being"
5. difficulty_sweet_spots: "Optimal difficulty level 2-3 for beginners, 3-4 for advanced"

All data is aggregated (min 50 users). No individual user_ids stored.
Segments: beginner (0-30 sessions), intermediate (30-100), advanced (100+).

Benchmarks: Spotify Discover Weekly (collaborative filtering), Duolingo (course
optimization from aggregate data), Netflix (content recommendation from viewing patterns).
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from collections import defaultdict

logger = logging.getLogger("infinea")

MIN_SAMPLE_SIZE = 50  # Never report patterns from fewer than 50 users
SEGMENTS = {
    "beginner": (0, 30),
    "intermediate": (30, 100),
    "advanced": (100, float("inf")),
}


def _get_segment(total_sessions: int) -> str:
    """Classify user into segment based on total sessions."""
    for seg, (low, high) in SEGMENTS.items():
        if low <= total_sessions < high:
            return seg
    return "advanced"


async def compute_collective_patterns(db) -> dict:
    """Compute all collective patterns from aggregate user data.

    Returns summary of what was computed.
    """
    now = datetime.now(timezone.utc)
    results = {"computed_at": now.isoformat(), "patterns": 0}

    try:
        # 1. Time effectiveness patterns
        time_patterns = await _compute_time_effectiveness(db)
        for p in time_patterns:
            await _store_pattern(db, p, now)
            results["patterns"] += 1

        # 2. Category affinity patterns
        cat_patterns = await _compute_category_affinities(db)
        for p in cat_patterns:
            await _store_pattern(db, p, now)
            results["patterns"] += 1

        # 3. Streak builder patterns
        streak_patterns = await _compute_streak_builders(db)
        for p in streak_patterns:
            await _store_pattern(db, p, now)
            results["patterns"] += 1

        # 4. Difficulty sweet spots
        diff_patterns = await _compute_difficulty_sweet_spots(db)
        for p in diff_patterns:
            await _store_pattern(db, p, now)
            results["patterns"] += 1

        logger.info(f"Collective intelligence: {results['patterns']} patterns computed")

    except Exception as e:
        logger.error(f"Collective intelligence computation error: {e}")

    return results


async def _compute_time_effectiveness(db) -> list:
    """Compute completion rates by time of day across all users."""
    patterns = []
    try:
        # Get all user features with time-of-day data
        features = await db.user_features.find(
            {"completion_rate_by_time_of_day": {"$exists": True, "$ne": {}}},
            {"_id": 0, "completion_rate_by_time_of_day": 1, "total_sessions": 1},
        ).to_list(5000)

        if len(features) < MIN_SAMPLE_SIZE:
            return []

        # Aggregate by time bucket
        bucket_rates = defaultdict(list)
        for f in features:
            for bucket, rate in f.get("completion_rate_by_time_of_day", {}).items():
                if rate > 0:
                    bucket_rates[bucket].append(rate)

        # Compute averages
        bucket_avgs = {}
        for bucket, rates in bucket_rates.items():
            if len(rates) >= MIN_SAMPLE_SIZE:
                bucket_avgs[bucket] = round(sum(rates) / len(rates), 3)

        if bucket_avgs:
            best_bucket = max(bucket_avgs, key=bucket_avgs.get)
            worst_bucket = min(bucket_avgs, key=bucket_avgs.get)
            diff_pct = round((bucket_avgs[best_bucket] - bucket_avgs[worst_bucket]) * 100)

            patterns.append({
                "pattern_type": "time_effectiveness",
                "segment": "all",
                "data": {
                    "completion_by_time": bucket_avgs,
                    "best_time": best_bucket,
                    "worst_time": worst_bucket,
                    "difference_pct": diff_pct,
                },
                "sample_size": len(features),
                "confidence": min(1.0, len(features) / 200),
            })

    except Exception as e:
        logger.debug(f"Time effectiveness error: {e}")

    return patterns


async def _compute_category_affinities(db) -> list:
    """Compute which categories tend to co-occur in successful users."""
    patterns = []
    try:
        features = await db.user_features.find(
            {"completion_rate_by_category": {"$exists": True, "$ne": {}}},
            {"_id": 0, "completion_rate_by_category": 1, "total_sessions": 1},
        ).to_list(5000)

        if len(features) < MIN_SAMPLE_SIZE:
            return []

        # Count co-occurrences of high-performing categories
        co_occurrences = defaultdict(int)
        total_users = 0

        for f in features:
            cats = f.get("completion_rate_by_category", {})
            strong_cats = [c for c, r in cats.items() if r >= 0.6]
            if len(strong_cats) >= 2:
                total_users += 1
                for i, c1 in enumerate(strong_cats):
                    for c2 in strong_cats[i + 1:]:
                        pair = tuple(sorted([c1, c2]))
                        co_occurrences[pair] += 1

        if total_users >= MIN_SAMPLE_SIZE:
            # Find strongest affinities
            for pair, count in co_occurrences.items():
                if count >= MIN_SAMPLE_SIZE // 2:
                    patterns.append({
                        "pattern_type": "category_affinity",
                        "segment": "all",
                        "data": {
                            "categories": list(pair),
                            "co_occurrence_count": count,
                            "co_occurrence_rate": round(count / total_users, 3),
                        },
                        "sample_size": total_users,
                        "confidence": min(1.0, count / 100),
                    })

    except Exception as e:
        logger.debug(f"Category affinity error: {e}")

    return patterns


async def _compute_streak_builders(db) -> list:
    """Analyze which categories successful streak builders start with."""
    patterns = []
    try:
        # Users with streaks >= 7 days
        streak_users = await db.users.find(
            {"streak_days": {"$gte": 7}},
            {"_id": 0, "user_id": 1, "streak_days": 1},
        ).to_list(5000)

        if len(streak_users) < MIN_SAMPLE_SIZE:
            return []

        # Get their first few sessions
        first_categories = defaultdict(int)
        for u in streak_users:
            first_sessions = await db.user_sessions_history.find(
                {"user_id": u["user_id"], "completed": True},
                {"_id": 0, "category": 1},
            ).sort("started_at", 1).limit(3).to_list(3)

            for s in first_sessions:
                cat = s.get("category")
                if cat:
                    first_categories[cat] += 1

        if first_categories:
            total = sum(first_categories.values())
            cat_rates = {c: round(count / total, 3) for c, count in first_categories.items()}

            patterns.append({
                "pattern_type": "streak_builder",
                "segment": "all",
                "data": {
                    "first_session_categories": cat_rates,
                    "most_common_start": max(cat_rates, key=cat_rates.get),
                },
                "sample_size": len(streak_users),
                "confidence": min(1.0, len(streak_users) / 200),
            })

    except Exception as e:
        logger.debug(f"Streak builder error: {e}")

    return patterns


async def _compute_difficulty_sweet_spots(db) -> list:
    """Compute optimal difficulty by user segment."""
    patterns = []
    try:
        features = await db.user_features.find(
            {"difficulty_calibration.completion_by_difficulty": {"$exists": True, "$ne": {}}},
            {"_id": 0, "difficulty_calibration": 1, "total_sessions": 1},
        ).to_list(5000)

        if len(features) < MIN_SAMPLE_SIZE:
            return []

        for segment, (low, high) in SEGMENTS.items():
            segment_features = [f for f in features if low <= f.get("total_sessions", 0) < high]
            if len(segment_features) < MIN_SAMPLE_SIZE // 2:
                continue

            # Aggregate difficulty rates
            agg_rates = defaultdict(list)
            for f in segment_features:
                for diff, rate in f.get("difficulty_calibration", {}).get("completion_by_difficulty", {}).items():
                    agg_rates[diff].append(float(rate))

            avg_rates = {}
            for diff, rates in agg_rates.items():
                if len(rates) >= 10:
                    avg_rates[diff] = round(sum(rates) / len(rates), 3)

            if avg_rates:
                # Find sweet spot: highest completion that's not trivially easy
                sweet_spots = [int(d) for d, r in avg_rates.items() if 0.4 <= r <= 0.90]
                if not sweet_spots:
                    sweet_spots = [2, 3]

                patterns.append({
                    "pattern_type": "difficulty_sweet_spot",
                    "segment": segment,
                    "data": {
                        "completion_by_difficulty": avg_rates,
                        "sweet_spot": sorted(sweet_spots)[:2],
                    },
                    "sample_size": len(segment_features),
                    "confidence": min(1.0, len(segment_features) / 100),
                })

    except Exception as e:
        logger.debug(f"Difficulty sweet spot error: {e}")

    return patterns


async def _store_pattern(db, pattern: dict, computed_at: datetime):
    """Store a collective pattern: upsert current + append to history."""
    try:
        pattern_doc = {**pattern, "computed_at": computed_at.isoformat()}

        # Upsert current (for fast reads by get_collective_insights)
        await db.collective_patterns.update_one(
            {"pattern_type": pattern["pattern_type"], "segment": pattern["segment"]},
            {"$set": pattern_doc},
            upsert=True,
        )

        # Append to history (for trend analysis — never overwrite)
        await db.collective_patterns_history.insert_one({
            **pattern_doc,
            "week": computed_at.strftime("%Y-W%W"),
        })
    except Exception as e:
        logger.debug(f"Pattern store error: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# PUBLIC API — Read patterns for prompt injection
# ═══════════════════════════════════════════════════════════════════════════

async def get_collective_insights(db, user_segment: str = "all") -> str:
    """Get formatted collective insights for prompt injection.

    Returns a text block (~100-200 tokens) with relevant patterns
    for the user's segment. Empty string if no patterns available.
    """
    try:
        patterns = await db.collective_patterns.find(
            {"segment": {"$in": [user_segment, "all"]}, "sample_size": {"$gte": MIN_SAMPLE_SIZE}},
            {"_id": 0},
        ).to_list(20)

        if not patterns:
            return ""

        lines = ["INSIGHTS COLLECTIFS (tendances observees chez les utilisateurs InFinea):"]

        for p in patterns:
            ptype = p.get("pattern_type")
            data = p.get("data", {})

            if ptype == "time_effectiveness":
                best = data.get("best_time", "")
                diff = data.get("difference_pct", 0)
                bucket_labels = {"morning": "matin", "afternoon": "apres-midi",
                                "evening": "soir", "night": "nuit"}
                if best and diff > 5:
                    lines.append(
                        f"- Les sessions du {bucket_labels.get(best, best)} ont un taux de "
                        f"completion {diff}% plus eleve que les autres creneaux."
                    )

            elif ptype == "category_affinity":
                cats = data.get("categories", [])
                rate = data.get("co_occurrence_rate", 0)
                cat_labels = {"learning": "apprentissage", "productivity": "productivite",
                             "well_being": "bien-etre"}
                if len(cats) == 2 and rate > 0.3:
                    c1 = cat_labels.get(cats[0], cats[0])
                    c2 = cat_labels.get(cats[1], cats[1])
                    lines.append(
                        f"- Les utilisateurs qui progressent en {c1} reussissent aussi "
                        f"bien en {c2} ({round(rate*100)}% de correlation)."
                    )

            elif ptype == "streak_builder":
                most_common = data.get("most_common_start", "")
                cat_labels = {"learning": "apprentissage", "productivity": "productivite",
                             "well_being": "bien-etre"}
                if most_common:
                    lines.append(
                        f"- Les utilisateurs qui maintiennent des streaks longues commencent "
                        f"souvent par des sessions de {cat_labels.get(most_common, most_common)}."
                    )

            elif ptype == "difficulty_sweet_spot":
                sweet = data.get("sweet_spot", [])
                seg = p.get("segment", "all")
                seg_labels = {"beginner": "debutants", "intermediate": "intermediaires",
                             "advanced": "avances"}
                if sweet:
                    lines.append(
                        f"- Zone de difficulte optimale pour les {seg_labels.get(seg, seg)}: "
                        f"niveau {'-'.join(str(s) for s in sweet)}."
                    )

        if len(lines) <= 1:
            return ""

        return "\n".join(lines[:6])  # Max 5 insights

    except Exception:
        return ""


# ═══════════════════════════════════════════════════════════════════════════
# BACKGROUND LOOP
# ═══════════════════════════════════════════════════════════════════════════

async def collective_pattern_loop(db):
    """Background loop: recompute collective patterns weekly."""
    await asyncio.sleep(300)  # Wait 5 min after startup
    while True:
        try:
            result = await compute_collective_patterns(db)
            logger.info(f"Collective patterns computed: {result}")
        except Exception as e:
            logger.error(f"Collective pattern loop error: {e}")

        await asyncio.sleep(7 * 24 * 3600)  # Run weekly
