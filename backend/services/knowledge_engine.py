"""
InFinea — Knowledge Engine.

Curated domain knowledge fragments organized by category and topic.
Static content, versioned, cached aggressively.

NOT a vector database. NOT RAG. Just expertly curated text fragments
that give the LLM genuine domain expertise instead of generic platitudes.

Each fragment is 80-200 tokens of expert-level insight with academic references.
Fragments are selected per endpoint + user context for targeted injection.

Architecture:
- KNOWLEDGE_BASE: dict of domain → topic → list[str] fragments
- ENDPOINT_TOPICS: mapping endpoint → list of relevant topics
- get_relevant_fragments(): select and format fragments for a specific call
"""

import logging
from typing import Optional

logger = logging.getLogger("infinea")

KNOWLEDGE_VERSION = 1


# ═══════════════════════════════════════════════════════════════════════════
# DOMAIN 1: SCIENCE DE L'APPRENTISSAGE
# ═══════════════════════════════════════════════════════════════════════════

LEARNING_GENERAL = [
    (
        "Courbe d'oubli (Ebbinghaus 1885): sans revision, 70% de l'information est oubliee "
        "en 24h et 90% en 7 jours. La repetition espacee combat cet effet — reviser a J+1, "
        "J+3, J+7, J+14 maximise la retention long terme avec un effort minimal."
    ),
    (
        "Pratique deliberee (Ericsson 1993): la cle de la maitrise n'est pas la repetition "
        "passive mais la concentration sur ses faiblesses specifiques, avec feedback immediat "
        "et ajustement constant. 5 min de pratique deliberee > 30 min de repetition machinale."
    ),
    (
        "Difficulte desirable (Bjork 1994): une session legerement au-dela du niveau confortable "
        "renforce l'encodage en memoire. Trop facile = pas d'apprentissage. Trop dur = abandon. "
        "Le sweet spot est la zone ou l'on echoue ~20% du temps."
    ),
    (
        "Zone proximale de developpement (Vygotsky): l'apprentissage optimal se situe entre "
        "ce que l'on maitrise deja et ce qui est hors de portee. Le role du coach est d'identifier "
        "cette zone et d'y maintenir l'apprenant."
    ),
    (
        "Interleaving (Rohrer & Taylor 2007): alterner les types d'exercices dans une session "
        "(plutot que bloquer un seul type) ameliore la retention de 25-40%. Le cerveau apprend "
        "a discriminer les contextes, ce qui renforce la flexibilite cognitive."
    ),
    (
        "Testing effect (Roediger & Karpicke 2006): se tester activement (recall) est 50% plus "
        "efficace que relire passivement. Chaque auto-test renforce les connexions neuronales, "
        "meme quand la reponse est incorrecte."
    ),
    (
        "Encoding variability: etudier le meme concept dans des contextes differents (lieu, "
        "heure, methode) cree des traces memorielles plus riches et facilite le rappel."
    ),
    (
        "Flow state (Csikszentmihalyi): l'engagement optimal se produit quand le defi est "
        "~4% au-dessus du niveau de competence actuel, avec des objectifs clairs, un feedback "
        "immediat et l'absence de distractions."
    ),
    (
        "Micro-learning (etudes Grovo/LinkedIn 2019): les sessions de 3-7 minutes ont un taux "
        "de completion 2x superieur aux sessions de 30+ minutes, et le contenu est mieux retenu "
        "car il tient dans la memoire de travail (capacite limitee: 4±1 elements)."
    ),
    (
        "Elaboration: expliquer un concept dans ses propres mots (meme a voix haute seul) "
        "double la retention par rapport a la lecture passive. L'effort de reformulation force "
        "une comprehension profonde."
    ),
]

LEARNING_LANGUAGES = [
    (
        "Vocabulaire actif vs passif: viser 80% de vocabulaire actif (production) plutot "
        "que passif (reconnaissance). Un mot n'est 'appris' que quand on l'utilise spontanement. "
        "Technique: forcer la production avec des flashcards recto-verso inversees."
    ),
    (
        "Technique du shadowing (Murphey 2001): ecouter et repeter simultanement un locuteur "
        "natif, en imitant l'intonation et le rythme. Ameliore la prononciation et la fluidite "
        "en 2-3 semaines de pratique quotidienne de 5 min."
    ),
    (
        "Seuil de frequence lexicale: les 1000 mots les plus frequents couvrent ~85% du langage "
        "oral quotidien. Les 3000 premiers couvrent ~95%. Prioritiser par frequence d'usage."
    ),
    (
        "Chunking linguistique: apprendre des expressions entieres ('Qu'est-ce que tu fais?') "
        "plutot que des mots isoles accelere la fluidite. Le cerveau traite les chunks comme "
        "des unites uniques, liberant la memoire de travail."
    ),
    (
        "Immersion micro: 5 min de podcast en langue cible pendant les transports creent une "
        "exposition reguliere qui renforce la comprehension orale sans effort conscient."
    ),
    (
        "Methode Goldlist (Iversen): ecrire 20 mots nouveaux, les relire apres 2 semaines sans "
        "effort de memorisation, et ne re-ecrire que ceux oublies. Exploite la memoire long-terme "
        "inconsciente — zero stress, haute retention."
    ),
]

LEARNING_MUSIC = [
    (
        "Chunking musical: decouper un morceau en phrases de 4-8 mesures et maitriser chaque "
        "chunk separement avant d'assembler. Reduit la charge cognitive et accelere la maitrise."
    ),
    (
        "Slow practice (Kageyama): jouer a 50% du tempo cible pendant 70% du temps de pratique. "
        "Le cerveau encode les sequences motrices plus precisement a vitesse reduite. Accelerer "
        "progressivement de 5 BPM par session."
    ),
    (
        "Pratique mentale (Pascual-Leone 1995): visualiser l'execution d'un passage sans "
        "instrument active les memes circuits neuronaux que la pratique physique. Efficace "
        "pour consolider la memoire musculaire entre les sessions."
    ),
    (
        "Ear training micro: 3 min de reconnaissance d'intervalles par jour. Apres 30 jours, "
        "l'oreille musicale s'ameliore de facon mesurable (etude Trainear 2020)."
    ),
]

LEARNING_PROGRAMMING = [
    (
        "Code kata (Dave Thomas): resoudre un petit probleme de programmation quotidiennement "
        "developpe la fluidite technique. L'objectif n'est pas de resoudre le probleme mais "
        "d'affiner le processus de resolution."
    ),
    (
        "Rubber duck debugging: expliquer son code a haute voix (meme a un canard en plastique) "
        "force l'explicitation de la logique et revele les hypotheses implicites erronees."
    ),
    (
        "Feynman technique pour le code: si tu ne peux pas expliquer un concept en 1 phrase "
        "simple, tu ne le comprends pas encore. Reformuler chaque nouveau concept appris."
    ),
]

LEARNING_READING = [
    (
        "Active reading (Adler & Van Doren): lire avec un objectif precis (une question a "
        "resoudre) augmente la retention de 3x par rapport a la lecture passive lineaire."
    ),
    (
        "Technique SQ3R: Survey, Question, Read, Recite, Review. Structurer chaque session "
        "de lecture en 5 etapes transforme la lecture passive en apprentissage actif."
    ),
    (
        "Micro-reading: 5 pages par jour de non-fiction = 40+ livres par an. La constance "
        "bat l'intensite. Un chapitre par jour vaut mieux qu'un livre en un week-end."
    ),
]

LEARNING_CREATIVITY = [
    (
        "Divergent thinking (Guilford): generer un maximum d'idees sans jugement pendant 5 min "
        "(brainstorming solitaire) active les reseaux de creativite. La qualite emerge de la "
        "quantite — les meilleures idees arrivent souvent apres les 15 premieres."
    ),
    (
        "Morning pages (Julia Cameron): 3 pages d'ecriture libre au reveil debloquent la "
        "creativite en vidant le 'bruit mental'. Adaptable en 5 min de free-writing."
    ),
]


# ═══════════════════════════════════════════════════════════════════════════
# DOMAIN 2: PSYCHOLOGIE COMPORTEMENTALE
# ═══════════════════════════════════════════════════════════════════════════

PSYCHOLOGY_HABITS = [
    (
        "Boucle d'habitude (Duhigg 2012): Signal → Routine → Recompense. Pour ancrer une "
        "micro-action: identifier un signal stable (apres le cafe, en attendant le bus), "
        "attacher l'action au signal, et celebrer immediatement apres."
    ),
    (
        "Seuil de 66 jours (Lally 2010, UCL): en moyenne, une habitude se stabilise en 66 jours "
        "(fourchette 18-254j). Les premiers 21 jours sont les plus fragiles. La regularite "
        "compte plus que la perfection — rater 1 jour ne casse pas l'habitude, en rater 2 oui."
    ),
    (
        "Implementation intentions (Gollwitzer 1999): formuler 'Quand [situation], je ferai "
        "[action]' augmente le taux de suivi de 2-3x. Le cerveau pre-encode la decision, "
        "eliminant la friction du choix au moment d'agir."
    ),
    (
        "Temptation bundling (Milkman 2014): associer une action necessaire a une activite "
        "plaisante ('j'ecoute mon podcast prefere uniquement pendant ma session de stretching') "
        "augmente l'adherence de 51%."
    ),
    (
        "Environment design: reduire la friction de l'action souhaitee (poser le livre sur "
        "l'oreiller, preparer l'app la veille) et augmenter la friction des distractions "
        "(phone dans une autre piece) est plus efficace que la volonte pure."
    ),
    (
        "Habit stacking (Clear 2018): attacher une nouvelle habitude a une habitude existante "
        "('Apres m'etre brosse les dents, je fais 3 min de vocabulaire'). Le cerveau utilise "
        "l'habitude existante comme signal automatique."
    ),
]

PSYCHOLOGY_MOTIVATION = [
    (
        "Self-Determination Theory (Deci & Ryan 2000): la motivation durable repose sur 3 besoins: "
        "Autonomie (choisir ses actions), Competence (sentir qu'on progresse), et Lien social "
        "(se sentir connecte a d'autres). InFinea couvre les 3 via choix, progression visible, et communaute."
    ),
    (
        "Variable ratio reinforcement (Skinner): les recompenses imprevisibles (badges surprises, "
        "milestones inattendus) maintiennent l'engagement plus longtemps que les recompenses fixes. "
        "C'est le mecanisme derriere les streaks et les niveaux XP."
    ),
    (
        "Loss aversion (Kahneman & Tversky): perdre une streak de 7 jours est 2x plus douloureux "
        "que la satisfaction de la construire. Utiliser avec ethique: rappeler ce qu'on risque de "
        "perdre est plus motivant que montrer ce qu'on pourrait gagner."
    ),
    (
        "Effet Zeigarnik: les taches inachevees restent en memoire active plus longtemps que les "
        "taches completees. Un objectif a 80% motive plus qu'un objectif a 0%. Montrer la "
        "progression inachevee est un puissant levier d'action."
    ),
    (
        "Motivation intriseque vs extrinseque: les recompenses externes (points, badges) boostent "
        "le demarrage mais nuisent a long terme si elles remplacent le plaisir intrinseque. "
        "Toujours connecter l'action a un objectif personnel significatif."
    ),
]

PSYCHOLOGY_STREAKS = [
    (
        "Psychologie des streaks: une streak n'est pas un objectif mais un outil. Une streak "
        "brisee n'est pas un echec — c'est normal (meme les meilleurs athletes ont des jours off). "
        "L'important est le ratio de jours actifs sur 30, pas la continuite parfaite."
    ),
    (
        "Streak recovery: apres une interruption, le cerveau sur-evalue le cout de recommencer "
        "(biais du cout irrecuperable inverse). Rappeler que revenir le jour meme est le facteur "
        "#1 de succes a long terme."
    ),
    (
        "Consistency beats intensity: 5 min par jour pendant 30 jours > 2h30 en un seul week-end. "
        "Les connexions neuronales se renforcent par la frequence de la stimulation, pas par "
        "sa duree."
    ),
]

PSYCHOLOGY_CHOICE = [
    (
        "Paradoxe du choix (Schwartz 2004): plus de 5 options paralyse la decision. Presenter "
        "3 actions recommandees (pas 20) augmente le taux de selection de 2x."
    ),
    (
        "Default effect: l'option presentee en premier est choisie 60-70% du temps. Placer la "
        "meilleure action recommandee en premier avec un badge 'Recommandee' exploite ce biais."
    ),
    (
        "Commitment device: demander a l'utilisateur de choisir sa prochaine session a l'avance "
        "(implementation intention) augmente le taux de suivi de 2-3x vs choix au moment."
    ),
]

PSYCHOLOGY_REINFORCEMENT = [
    (
        "Renforcement positif immediat: celebrer une micro-victoire dans les 3 secondes apres "
        "la completion (animation, son, message) ancre le comportement. Le delai critique est "
        "< 5 secondes (conditionnement operant classique)."
    ),
    (
        "Progress principle (Amabile & Kramer 2011): le facteur #1 de motivation au travail est "
        "le sentiment de progresser. Rendre la progression visible (barre, pourcentage, palier) "
        "est plus motivant que n'importe quelle recompense externe."
    ),
]


# ═══════════════════════════════════════════════════════════════════════════
# DOMAIN 3: METHODOLOGIE COACHING
# ═══════════════════════════════════════════════════════════════════════════

COACHING_GREETING = [
    (
        "Premiere impression coaching: la salutation du coach pose le ton de la session. "
        "Reconnaitre specifiquement ce que l'utilisateur a fait recemment (pas un generique "
        "'Bonjour') cree un sentiment d'etre vu et compris."
    ),
    (
        "Technique du 'build-up': commencer par une reconnaissance concrete (fait ou chiffre), "
        "puis ouvrir une opportunite ('Tu as enchaine 3 sessions cette semaine — et si on "
        "montait d'un cran?'). Jamais de flatterie vide."
    ),
]

COACHING_CONVERSATION = [
    (
        "Questionnement socratique: poser des questions ouvertes qui amenent l'utilisateur a "
        "trouver ses propres solutions. 'Qu'est-ce qui a rendu cette session difficile?' > "
        "'C'etait trop dur, essaie plus facile'. L'insight personnel est 3x plus durable."
    ),
    (
        "Scaling questions (SFBT): 'Sur une echelle de 1 a 10, a quel point te sens-tu "
        "confiant pour maintenir cette habitude?' puis 'Qu'est-ce qui te ferait monter d'un "
        "point?'. Donne du controle a l'utilisateur sur sa propre progression."
    ),
    (
        "Motivational interviewing (Miller & Rollnick): explorer l'ambivalence sans la juger. "
        "Si l'utilisateur hesite: 'D'un cote tu aimerais progresser, de l'autre c'est dur de "
        "trouver le temps — c'est normal de ressentir les deux.'"
    ),
    (
        "Exception question: 'Quand est-ce que ca a bien marche pour toi?' Identifier les "
        "moments ou l'utilisateur a reussi naturellement revele ses forces et ses meilleurs "
        "creneaux — plus utile que d'analyser les echecs."
    ),
]

COACHING_CONSOLIDATION = [
    (
        "Consolidation post-session: les 2 minutes apres une session sont critiques pour "
        "l'encodage. Demander 'Qu'est-ce que tu retiens de cette session?' active le rappel "
        "et multiplie par 2 la retention (testing effect)."
    ),
    (
        "Spacing effect applique au debrief: ne pas tout analyser immediatement. Un bref feedback "
        "post-session + une reflexion 24h plus tard est plus efficace qu'une analyse detaillee "
        "immediate qui surcharge la memoire de travail."
    ),
]

COACHING_CURRICULUM = [
    (
        "Design de curriculum micro-learning: chaque session doit avoir UN objectif clair, "
        "mesurable en 5 minutes. 'Apprendre 10 mots' > 'Progresser en vocabulaire'. "
        "L'objectif specifique focalise l'attention et permet le feedback."
    ),
    (
        "Spirale de competence: revenir sur un concept maitriser mais a un niveau plus eleve "
        "(spiraling). Ex: vocabulaire basique → memes mots en contexte → memes mots en production. "
        "Approfondit sans ennuyer."
    ),
]


# ═══════════════════════════════════════════════════════════════════════════
# DOMAIN 4: EXPERTISE PAR CATEGORIE (WELL-BEING)
# ═══════════════════════════════════════════════════════════════════════════

WELLBEING_GENERAL = [
    (
        "Micro-pauses (etudes neurosciences): 2-3 min de respiration profonde entre deux taches "
        "reduit le cortisol de 25% et restaure les ressources attentionnelles. Impact maximal "
        "quand la pause inclut un changement sensoriel (fermer les yeux, marcher)."
    ),
    (
        "Coherence cardiaque (5-5-5): 5 min de respiration a 6 cycles/minute (inspir 5s, expir 5s) "
        "synchronise le systeme nerveux autonome. Effets mesurables sur la variabilite cardiaque "
        "des la premiere session, cumuls sur 30 jours."
    ),
]

WELLBEING_MEDITATION = [
    (
        "Body scan progressif: scanner le corps de la tete aux pieds en 5 min, en portant "
        "attention a chaque zone sans la modifier. Developpe l'interoception (conscience des "
        "sensations internes), base de la regulation emotionnelle."
    ),
    (
        "Meditation micro (2-3 min): fermer les yeux et compter 10 respirations. Quand l'esprit "
        "divague (il le fera), revenir au comptage sans jugement. Ce retour EST la pratique — "
        "c'est un bicep curl pour l'attention."
    ),
]

WELLBEING_STRETCHING = [
    (
        "Micro-stretching au bureau: 3 etirements de 30s (cou, epaules, hanches) toutes les 90 min "
        "previennent 80% des tensions posturales (etude ergonomie Corlett 2009). Plus efficace "
        "que 30 min de yoga le soir pour les sedentaires."
    ),
]

WELLBEING_SLEEP = [
    (
        "Hygiene du sommeil en 1 action: la temperature de la chambre (18-19°C) est le facteur "
        "#1 de qualite de sommeil, devant la duree. Conseil actionnable > lecture sur le sommeil."
    ),
]


# ═══════════════════════════════════════════════════════════════════════════
# DOMAIN 5: PRODUCTIVITE
# ═══════════════════════════════════════════════════════════════════════════

PRODUCTIVITY_GENERAL = [
    (
        "2-Minute Rule (David Allen): si une tache prend moins de 2 minutes, la faire "
        "immediatement plutot que de la planifier. Elimine le cout cognitif de la gestion "
        "et reduit la charge mentale accumulee."
    ),
    (
        "Batching (Newport 2016): regrouper les taches similaires (emails, appels, admin) "
        "reduit le context-switching de 40%. Le cerveau met ~23 min a retrouver la concentration "
        "apres une interruption (etude Mark/Gonzalez)."
    ),
    (
        "Eat the frog (Brian Tracy): faire la tache la plus difficile en premier quand l'energie "
        "est maximale. Les etudes sur le rythme circadien montrent un pic de concentration "
        "2-4h apres le reveil pour 75% des gens."
    ),
]

PRODUCTIVITY_FOCUS = [
    (
        "Pomodoro micro: 5 min de focus intense sans aucune distraction, suivi de 1 min de pause. "
        "Adapte le Pomodoro classique (25/5) au micro-apprentissage. La contrainte de temps "
        "cree une urgence artificielle qui booste la concentration."
    ),
    (
        "Digital minimalism (Cal Newport): un seul onglet ouvert, telephone en mode avion. "
        "Chaque notification non desactivee coute ~15 min de concentration cumulee par jour."
    ),
]

PRODUCTIVITY_PLANNING = [
    (
        "Pre-commitment (Odysseus strategy): choisir sa prochaine session la veille elimine la "
        "decision-fatigue du matin. Ecrire 'Demain a 8h: 5 min vocabulaire thai' augmente le "
        "suivi de 2-3x (implementation intention + pre-engagement)."
    ),
    (
        "Rule of 3 (Chris Bailey): choisir 3 priorites par jour maximum. Au-dela, la dilution "
        "de l'attention annule les gains. Pour le micro-learning: 1 objectif principal par jour."
    ),
]


# ═══════════════════════════════════════════════════════════════════════════
# KNOWLEDGE BASE — STRUCTURE INDEXEE
# ═══════════════════════════════════════════════════════════════════════════

KNOWLEDGE_BASE = {
    "learning": {
        "general": LEARNING_GENERAL,
        "languages": LEARNING_LANGUAGES,
        "music": LEARNING_MUSIC,
        "programming": LEARNING_PROGRAMMING,
        "reading": LEARNING_READING,
        "creativity": LEARNING_CREATIVITY,
    },
    "psychology": {
        "habits": PSYCHOLOGY_HABITS,
        "motivation": PSYCHOLOGY_MOTIVATION,
        "streaks": PSYCHOLOGY_STREAKS,
        "choice": PSYCHOLOGY_CHOICE,
        "reinforcement": PSYCHOLOGY_REINFORCEMENT,
    },
    "coaching": {
        "greeting": COACHING_GREETING,
        "conversation": COACHING_CONVERSATION,
        "consolidation": COACHING_CONSOLIDATION,
        "curriculum": COACHING_CURRICULUM,
    },
    "well_being": {
        "general": WELLBEING_GENERAL,
        "meditation": WELLBEING_MEDITATION,
        "stretching": WELLBEING_STRETCHING,
        "sleep": WELLBEING_SLEEP,
    },
    "productivity": {
        "general": PRODUCTIVITY_GENERAL,
        "focus": PRODUCTIVITY_FOCUS,
        "planning": PRODUCTIVITY_PLANNING,
    },
}


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINT → TOPICS MAPPING
# ═══════════════════════════════════════════════════════════════════════════

ENDPOINT_TOPICS = {
    "coach_dashboard": [
        ("coaching", "greeting"),
        ("psychology", "motivation"),
    ],
    "coach_chat": [
        ("coaching", "conversation"),
        ("psychology", "habits"),
        ("learning", "general"),
    ],
    "debrief": [
        ("coaching", "consolidation"),
        ("psychology", "reinforcement"),
    ],
    "weekly_analysis": [
        ("learning", "general"),
        ("psychology", "habits"),
    ],
    "suggestions": [
        ("psychology", "choice"),
        ("learning", "general"),
    ],
    "curriculum": [
        ("coaching", "curriculum"),
        ("learning", "general"),
    ],
    "create_action": [
        ("learning", "general"),
    ],
    "streak_check": [
        ("psychology", "streaks"),
    ],
}

# Map user objective categories to knowledge sub-topics
CATEGORY_TOPIC_MAP = {
    "learning": [("learning", "general")],
    "language_learning": [("learning", "languages")],
    "languages": [("learning", "languages")],
    "music": [("learning", "music")],
    "programming": [("learning", "programming")],
    "coding": [("learning", "programming")],
    "reading": [("learning", "reading")],
    "creativity": [("learning", "creativity")],
    "art": [("learning", "creativity")],
    "productivity": [("productivity", "general"), ("productivity", "focus")],
    "well_being": [("well_being", "general")],
    "meditation": [("well_being", "meditation")],
    "mindfulness": [("well_being", "meditation")],
    "fitness": [("well_being", "stretching")],
    "stretching": [("well_being", "stretching")],
    "sleep": [("well_being", "sleep")],
}


# ═══════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════

def get_relevant_fragments(
    endpoint: str,
    user_categories: list = None,
    max_fragments: int = 6,
) -> str:
    """Select the most relevant knowledge fragments for an AI call.

    Combines endpoint-specific topics with user's active categories
    to produce targeted expertise injection.

    Args:
        endpoint: AI endpoint name (coach_dashboard, coach_chat, etc.)
        user_categories: User's active objective categories (e.g. ["learning", "music"])
        max_fragments: Maximum fragments to include (controls token budget)

    Returns:
        Formatted string ready to inject into system prompt (~300-500 tokens).
    """
    selected = []

    # 1. Get endpoint-specific fragments (always included)
    endpoint_topics = ENDPOINT_TOPICS.get(endpoint, [])
    for domain, topic in endpoint_topics:
        fragments = KNOWLEDGE_BASE.get(domain, {}).get(topic, [])
        if fragments:
            # Pick 1-2 most relevant per topic
            selected.extend(fragments[:2])

    # 2. Add category-specific fragments if user has active categories
    if user_categories:
        for cat in user_categories[:3]:  # Max 3 categories
            topics = CATEGORY_TOPIC_MAP.get(cat.lower(), [])
            for domain, topic in topics:
                fragments = KNOWLEDGE_BASE.get(domain, {}).get(topic, [])
                for frag in fragments[:2]:
                    if frag not in selected:
                        selected.append(frag)

    # 3. Deduplicate and limit
    seen = set()
    unique = []
    for frag in selected:
        if frag not in seen:
            seen.add(frag)
            unique.append(frag)

    final = unique[:max_fragments]

    if not final:
        return ""

    # 4. Format as prompt text
    lines = ["EXPERTISE SCIENTIFIQUE (utilise ces connaissances pour personnaliser tes conseils):"]
    for i, fragment in enumerate(final, 1):
        lines.append(f"- {fragment}")

    return "\n".join(lines)


def get_category_expertise(category: str, max_fragments: int = 3) -> str:
    """Get expertise fragments for a specific content category.

    Used by curriculum_engine and action_generator for category-specific knowledge.

    Args:
        category: Content category (e.g. "music", "languages", "meditation")
        max_fragments: Maximum fragments to return

    Returns:
        Formatted expertise text or empty string.
    """
    topics = CATEGORY_TOPIC_MAP.get(category.lower(), [])
    fragments = []
    for domain, topic in topics:
        domain_fragments = KNOWLEDGE_BASE.get(domain, {}).get(topic, [])
        fragments.extend(domain_fragments)

    if not fragments:
        return ""

    lines = [f"EXPERTISE {category.upper()}:"]
    for frag in fragments[:max_fragments]:
        lines.append(f"- {frag}")

    return "\n".join(lines)


def get_all_topics() -> dict:
    """Return all available topics for debugging/admin."""
    result = {}
    for domain, topics in KNOWLEDGE_BASE.items():
        result[domain] = {topic: len(fragments) for topic, fragments in topics.items()}
    return result


def count_total_fragments() -> int:
    """Count total knowledge fragments in the engine."""
    total = 0
    for domain in KNOWLEDGE_BASE.values():
        for fragments in domain.values():
            total += len(fragments)
    return total
