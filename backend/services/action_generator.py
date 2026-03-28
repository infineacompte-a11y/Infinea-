"""
Daily AI-powered action generator for InFinea.
Generates ~30 new actions per category per day, cumulative (never overwrites).
Uses generation_logs collection to prevent duplicate generation.
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from services.llm_provider import call_llm, ModelTier
from services.knowledge_engine import get_category_expertise

logger = logging.getLogger("action_generator")

# All 11 categories with their metadata
CATEGORIES = {
    "learning": {
        "label": "Apprentissage",
        "icon": "book-open",
        "is_premium": False,
        "description": "Vocabulaire, lecture, concepts, apprentissage de nouvelles compétences",
    },
    "productivity": {
        "label": "Productivité",
        "icon": "target",
        "is_premium": False,
        "description": "Planning, emails, brainstorm, organisation, gestion du temps",
    },
    "well_being": {
        "label": "Bien-être",
        "icon": "heart",
        "is_premium": False,
        "description": "Respiration, méditation, étirements, pauses actives, relaxation",
    },
    "creativity": {
        "label": "Créativité",
        "icon": "palette",
        "is_premium": True,
        "description": "Dessin, écriture créative, mind mapping, pensée divergente, innovation",
    },
    "fitness": {
        "label": "Forme physique",
        "icon": "dumbbell",
        "is_premium": True,
        "description": "Étirements, micro-cardio, mobilité, exercices au bureau, posture",
    },
    "mindfulness": {
        "label": "Pleine conscience",
        "icon": "leaf",
        "is_premium": True,
        "description": "Respiration carrée, scan corporel, méditation guidée, ancrage sensoriel",
    },
    "leadership": {
        "label": "Leadership",
        "icon": "users",
        "is_premium": True,
        "description": "Écoute active, prise de décision, feedback, communication d'influence",
    },
    "finance": {
        "label": "Finance personnelle",
        "icon": "trending-up",
        "is_premium": True,
        "description": "Budget express, suivi dépenses, épargne, éducation financière",
    },
    "relations": {
        "label": "Relations",
        "icon": "message-circle",
        "is_premium": True,
        "description": "Communication, empathie, réseau, assertivité, liens sociaux",
    },
    "mental_health": {
        "label": "Santé mentale",
        "icon": "brain",
        "is_premium": True,
        "description": "Gestion du stress, résilience, estime de soi, régulation émotionnelle",
    },
    "entrepreneurship": {
        "label": "Entrepreneuriat",
        "icon": "rocket",
        "is_premium": True,
        "description": "Idéation, pitch, stratégie, networking, validation d'idées",
    },
}

ACTIONS_PER_CATEGORY = 30
BATCH_SIZE = 10  # Generate 10 actions per AI call (3 calls per category)


async def _call_generation_ai(system_message: str, prompt: str) -> Optional[str]:
    """Call LLM for action generation via provider abstraction. Uses FAST tier (Haiku)."""
    return await call_llm(
        system_prompt=system_message,
        user_prompt=prompt,
        model_tier=ModelTier.FAST,
        max_tokens=4000,
        caller="action_generator",
    )


def _parse_actions_json(response: Optional[str]) -> list:
    """Extract JSON array from AI response."""
    if not response:
        return []
    try:
        # Try direct parse
        return json.loads(response)
    except json.JSONDecodeError:
        pass
    # Try extracting from markdown code block
    try:
        start = response.find("[")
        end = response.rfind("]") + 1
        if start >= 0 and end > start:
            return json.loads(response[start:end])
    except (json.JSONDecodeError, ValueError):
        pass
    logger.error(f"Failed to parse AI response as JSON: {response[:200]}")
    return []


async def generate_actions_for_category(
    db, category: str, existing_titles: set, batch_num: int
) -> list:
    """Generate a batch of actions for a specific category using AI."""
    cat_info = CATEGORIES.get(category)
    if not cat_info:
        return []

    # Inject category-specific expertise from knowledge engine
    category_expertise = get_category_expertise(category, max_fragments=2)

    system_message = f"""Tu es Kira, experte en micro-apprentissage d'InFinea.
Tu generes des micro-actions concretes, variees et realisables en 2 a 15 minutes.
Chaque action doit etre unique, precise et immediatement actionnable.
Tu t'appuies sur la science de l'apprentissage (pratique deliberee, interleaving, difficulte desirable).

{category_expertise}

Tu reponds UNIQUEMENT en JSON valide, sans texte autour."""

    # Sample some existing titles for diversity
    sample_titles = list(existing_titles)[:20]
    titles_str = "\n".join(f"- {t}" for t in sample_titles) if sample_titles else "Aucune action existante"

    prompt = f"""Génère exactement {BATCH_SIZE} micro-actions NOUVELLES et UNIQUES pour la catégorie "{cat_info['label']}" ({category}).

Contexte de la catégorie : {cat_info['description']}

Actions DÉJÀ existantes (NE PAS dupliquer ni paraphraser) :
{titles_str}

Règles :
- Chaque action dure entre 2 et 15 minutes
- energy_level : "low", "medium" ou "high"
- 3 à 5 instructions concrètes par action
- Varier les thèmes, niveaux d'énergie et durées
- Titres courts (3-6 mots), descriptions en 1 phrase
- Batch {batch_num}/3 : sois créatif et explore des angles différents

Réponds avec un tableau JSON uniquement :
[
  {{
    "title": "Titre court",
    "description": "Description claire en une phrase.",
    "duration_min": 3,
    "duration_max": 7,
    "energy_level": "low",
    "instructions": ["Étape 1", "Étape 2", "Étape 3"]
  }}
]"""

    response = await _call_generation_ai(system_message, prompt)
    raw_actions = _parse_actions_json(response)

    # Validate and format actions
    valid_actions = []
    for action in raw_actions:
        title = action.get("title", "").strip()
        if not title or title in existing_titles:
            continue  # Skip duplicates

        # Validate required fields
        if not all(k in action for k in ("description", "duration_min", "duration_max", "energy_level", "instructions")):
            continue
        if not isinstance(action["instructions"], list) or len(action["instructions"]) < 2:
            continue
        if action["energy_level"] not in ("low", "medium", "high"):
            continue

        valid_actions.append({
            "action_id": f"action_{category}_{uuid.uuid4().hex[:8]}",
            "title": title,
            "description": action["description"],
            "category": category,
            "duration_min": max(2, min(15, int(action["duration_min"]))),
            "duration_max": max(2, min(15, int(action["duration_max"]))),
            "energy_level": action["energy_level"],
            "instructions": action["instructions"][:5],
            "is_premium": cat_info["is_premium"],
            "icon": cat_info["icon"],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generated": True,
        })
        existing_titles.add(title)

    return valid_actions


async def check_and_generate_daily_actions(db):
    """Check which categories need generation today and generate actions."""
    today = datetime.now(timezone.utc).date().isoformat()

    # Check which categories already generated today
    existing_logs = await db.generation_logs.find(
        {"date": today}, {"category": 1}
    ).to_list(50)
    done_categories = {log["category"] for log in existing_logs}

    categories_to_generate = [
        cat for cat in CATEGORIES if cat not in done_categories
    ]

    if not categories_to_generate:
        logger.info(f"Daily generation already complete for {today}")
        return {"status": "already_done", "date": today}

    logger.info(
        f"Generating actions for {len(categories_to_generate)} categories: {categories_to_generate}"
    )

    total_generated = 0

    for category in categories_to_generate:
        try:
            # Get existing titles for this category to avoid duplicates
            existing_docs = await db.micro_actions.find(
                {"category": category}, {"title": 1}
            ).to_list(5000)
            existing_titles = {doc["title"] for doc in existing_docs}

            category_actions = []

            # Generate in 3 batches of 10
            for batch_num in range(1, 4):
                batch = await generate_actions_for_category(
                    db, category, existing_titles, batch_num
                )
                category_actions.extend(batch)
                # Small delay between batches to avoid rate limiting
                if batch_num < 3:
                    await asyncio.sleep(2)

            # Insert all new actions for this category
            if category_actions:
                await db.micro_actions.insert_many(category_actions)
                total_generated += len(category_actions)

            # Log successful generation
            await db.generation_logs.insert_one({
                "date": today,
                "category": category,
                "count": len(category_actions),
                "generated_at": datetime.now(timezone.utc).isoformat(),
            })

            logger.info(
                f"Generated {len(category_actions)} actions for {category}"
            )

            # Small delay between categories to spread load
            await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Failed to generate actions for {category}: {e}")
            continue

    logger.info(f"Daily generation complete: {total_generated} new actions")
    return {
        "status": "completed",
        "date": today,
        "total_generated": total_generated,
        "categories": len(categories_to_generate),
    }


async def daily_generation_loop(db):
    """Background loop that checks and generates actions periodically."""
    # Wait 30 seconds after startup before first check
    await asyncio.sleep(30)

    while True:
        try:
            await check_and_generate_daily_actions(db)
        except Exception as e:
            logger.error(f"Daily generation loop error: {e}")

        # Check every 6 hours (4 times per day)
        await asyncio.sleep(6 * 3600)
