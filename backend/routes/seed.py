"""
InFinea — Seed data route.
Initial micro-actions database seeding.
"""

from fastapi import APIRouter

from database import db

router = APIRouter(prefix="/api")


SEED_ACTIONS = [
    # Learning - Low Energy
    {
        "action_id": "action_learn_vocab",
        "title": "5 nouveaux mots",
        "description": "Apprenez 5 nouveaux mots de vocabulaire dans la langue de votre choix.",
        "category": "learning",
        "duration_min": 2,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Ouvrez votre application de vocabulaire préférée",
            "Révisez 5 mots avec leurs définitions",
            "Prononcez chaque mot à voix haute",
            "Utilisez chaque mot dans une phrase",
        ],
        "is_premium": False,
        "icon": "book-open",
    },
    {
        "action_id": "action_learn_article",
        "title": "Lecture rapide",
        "description": "Lisez un article court sur un sujet qui vous passionne.",
        "category": "learning",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "low",
        "instructions": [
            "Choisissez un article de votre fil d'actualités",
            "Lisez-le en survol d'abord",
            "Relisez les passages clés",
            "Notez une idée à retenir",
        ],
        "is_premium": False,
        "icon": "newspaper",
    },
    # Learning - Medium Energy
    {
        "action_id": "action_learn_concept",
        "title": "Nouveau concept",
        "description": "Apprenez un nouveau concept et testez votre compréhension.",
        "category": "learning",
        "duration_min": 10,
        "duration_max": 15,
        "energy_level": "medium",
        "instructions": [
            "Choisissez un sujet qui vous intéresse",
            "Regardez une vidéo explicative courte",
            "Résumez le concept en 3 points",
            "Expliquez-le comme si vous l'enseigniez",
        ],
        "is_premium": False,
        "icon": "lightbulb",
    },
    {
        "action_id": "action_learn_flashcards",
        "title": "Session Flashcards",
        "description": "Révisez 20 flashcards pour ancrer vos connaissances.",
        "category": "learning",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Ouvrez votre deck de flashcards",
            "Répondez à 20 cartes",
            "Marquez celles à revoir",
            "Célébrez votre score!",
        ],
        "is_premium": True,
        "icon": "layers",
    },
    # Productivity - Low Energy
    {
        "action_id": "action_prod_inbox",
        "title": "Inbox Zero",
        "description": "Traitez rapidement 5 emails de votre boîte de réception.",
        "category": "productivity",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Ouvrez votre messagerie",
            "Archivez ou supprimez les emails non essentiels",
            "Répondez aux messages rapides",
            "Marquez les autres pour plus tard",
        ],
        "is_premium": False,
        "icon": "mail",
    },
    {
        "action_id": "action_prod_plan",
        "title": "Mini-planification",
        "description": "Planifiez les 3 tâches prioritaires de votre prochaine session de travail.",
        "category": "productivity",
        "duration_min": 2,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Identifiez 3 tâches importantes",
            "Estimez le temps nécessaire",
            "Ordonnez par priorité",
            "Bloquez du temps dans votre agenda",
        ],
        "is_premium": False,
        "icon": "list-todo",
    },
    # Productivity - Medium Energy
    {
        "action_id": "action_prod_brainstorm",
        "title": "Brainstorm éclair",
        "description": "Générez 10 idées sur un projet ou problème en cours.",
        "category": "productivity",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Définissez votre question/problème",
            "Écrivez toutes les idées sans filtre",
            "Visez la quantité, pas la qualité",
            "Identifiez les 2-3 meilleures idées",
        ],
        "is_premium": False,
        "icon": "zap",
    },
    {
        "action_id": "action_prod_review",
        "title": "Revue de projet",
        "description": "Faites le point sur l'avancement d'un projet en cours.",
        "category": "productivity",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Choisissez un projet actif",
            "Listez ce qui a été accompli",
            "Identifiez les blocages",
            "Définissez la prochaine action",
        ],
        "is_premium": True,
        "icon": "clipboard-check",
    },
    # Well-being - Low Energy
    {
        "action_id": "action_well_breath",
        "title": "Respiration 4-7-8",
        "description": "Technique de respiration pour réduire le stress instantanément.",
        "category": "well_being",
        "duration_min": 2,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Asseyez-vous confortablement",
            "Inspirez par le nez pendant 4 secondes",
            "Retenez votre souffle 7 secondes",
            "Expirez par la bouche pendant 8 secondes",
            "Répétez 4 cycles",
        ],
        "is_premium": False,
        "icon": "wind",
    },
    {
        "action_id": "action_well_gratitude",
        "title": "Moment gratitude",
        "description": "Notez 3 choses pour lesquelles vous êtes reconnaissant aujourd'hui.",
        "category": "well_being",
        "duration_min": 2,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Fermez les yeux un instant",
            "Pensez à 3 moments positifs récents",
            "Notez-les dans votre journal",
            "Ressentez la gratitude",
        ],
        "is_premium": False,
        "icon": "heart",
    },
    # Well-being - Medium Energy
    {
        "action_id": "action_well_stretch",
        "title": "Pause étirements",
        "description": "Séance d'étirements pour délier les tensions du corps.",
        "category": "well_being",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Levez-vous et étirez les bras vers le haut",
            "Penchez-vous vers l'avant, bras pendants",
            "Faites des rotations de nuque",
            "Étirez chaque épaule 30 secondes",
            "Terminez par des rotations de hanches",
        ],
        "is_premium": False,
        "icon": "move",
    },
    {
        "action_id": "action_well_meditate",
        "title": "Mini méditation",
        "description": "Une courte méditation guidée pour recentrer votre esprit.",
        "category": "well_being",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Trouvez un endroit calme",
            "Fermez les yeux",
            "Concentrez-vous sur votre respiration",
            "Observez vos pensées sans jugement",
            "Revenez doucement au présent",
        ],
        "is_premium": True,
        "icon": "brain",
    },
    # High Energy Actions
    {
        "action_id": "action_prod_deep",
        "title": "Deep Work Sprint",
        "description": "15 minutes de concentration intense sur une tâche importante.",
        "category": "productivity",
        "duration_min": 10,
        "duration_max": 15,
        "energy_level": "high",
        "instructions": [
            "Choisissez UNE tâche prioritaire",
            "Éliminez toutes les distractions",
            "Mettez un timer de 15 minutes",
            "Travaillez sans interruption",
            "Notez où vous en êtes pour continuer plus tard",
        ],
        "is_premium": True,
        "icon": "target",
    },
    {
        "action_id": "action_well_energy",
        "title": "Boost d'énergie",
        "description": "Exercices rapides pour booster votre énergie et votre focus.",
        "category": "well_being",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "high",
        "instructions": [
            "20 jumping jacks",
            "10 squats",
            "30 secondes de planche",
            "10 pompes (ou version facilitée)",
            "Récupérez 30 secondes",
        ],
        "is_premium": False,
        "icon": "flame",
    },
    {
        "action_id": "action_learn_podcast",
        "title": "Podcast éclair",
        "description": "Écoutez un segment de podcast éducatif.",
        "category": "learning",
        "duration_min": 10,
        "duration_max": 15,
        "energy_level": "high",
        "instructions": [
            "Choisissez un podcast de votre liste",
            "Écoutez en vitesse 1.25x ou 1.5x",
            "Notez une idée clé",
            "Partagez-la ou appliquez-la",
        ],
        "is_premium": True,
        "icon": "headphones",
    },
]


@router.post("/admin/seed")
async def seed_micro_actions():
    """Seed database with initial micro-actions"""
    await db.micro_actions.delete_many({})
    await db.micro_actions.insert_many(SEED_ACTIONS)
    return {"message": f"Seeded {len(SEED_ACTIONS)} micro-actions"}
