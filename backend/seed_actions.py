"""
InFinea — Bibliothèque de 300 micro-actions
100 par catégorie (learning, productivity, well_being)
Distribution énergie : 40 low / 35 medium / 25 high
~70% gratuites, ~30% premium
"""

SEED_ACTIONS = [
    # =========================================================================
    # LEARNING (100 actions) — action_learn_001 to action_learn_100
    # Low energy: 001-040 | Medium energy: 041-075 | High energy: 076-100
    # =========================================================================

    # --- LEARNING / LOW ENERGY (40) ---

    # Languages (001-004)
    {
        "action_id": "action_learn_001",
        "title": "5 mots du jour",
        "description": "Apprenez 5 nouveaux mots de vocabulaire dans la langue de votre choix et utilisez-les dans une phrase.",
        "category": "learning",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Choisissez une langue cible",
            "Sélectionnez 5 mots utiles au quotidien",
            "Écrivez chaque mot avec sa traduction",
            "Créez une phrase simple pour chaque mot"
        ],
        "is_premium": False,
        "icon": "languages"
    },
    {
        "action_id": "action_learn_002",
        "title": "Prononciation express",
        "description": "Entraînez votre prononciation en répétant à voix haute 10 mots difficiles dans une langue étrangère.",
        "category": "learning",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Choisissez 10 mots que vous avez du mal à prononcer",
            "Écoutez la prononciation correcte en ligne",
            "Répétez chaque mot 3 fois lentement",
            "Enregistrez-vous et comparez"
        ],
        "is_premium": False,
        "icon": "mic"
    },
    {
        "action_id": "action_learn_003",
        "title": "Grammaire en 5 min",
        "description": "Révisez une règle de grammaire étrangère et faites 3 exercices rapides d'application.",
        "category": "learning",
        "duration_min": 4,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Choisissez une règle grammaticale à revoir",
            "Lisez un résumé clair de la règle",
            "Écrivez 3 phrases appliquant cette règle",
            "Vérifiez vos réponses et notez les erreurs"
        ],
        "is_premium": False,
        "icon": "spell-check"
    },
    {
        "action_id": "action_learn_004",
        "title": "Shadowing linguistique",
        "description": "Imitez un locuteur natif en répétant simultanément ce qu'il dit pour améliorer votre fluidité.",
        "category": "learning",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "low",
        "instructions": [
            "Trouvez un extrait audio court (30-60s) dans la langue cible",
            "Écoutez une première fois sans parler",
            "Relancez et répétez en même temps que l'audio",
            "Recommencez 3 fois en améliorant le rythme",
            "Notez les mots encore difficiles"
        ],
        "is_premium": True,
        "icon": "headphones"
    },

    # Science & Tech (005-008)
    {
        "action_id": "action_learn_005",
        "title": "Concept scientifique",
        "description": "Découvrez un concept scientifique fascinant et expliquez-le simplement en 3 phrases.",
        "category": "learning",
        "duration_min": 3,
        "duration_max": 8,
        "energy_level": "low",
        "instructions": [
            "Choisissez un concept : physique, chimie ou biologie",
            "Lisez une explication vulgarisée en ligne",
            "Résumez le concept en 3 phrases simples",
            "Trouvez un exemple concret dans la vie quotidienne"
        ],
        "is_premium": False,
        "icon": "atom"
    },
    {
        "action_id": "action_learn_006",
        "title": "Tendance tech du jour",
        "description": "Informez-vous sur une tendance technologique actuelle et notez son impact potentiel.",
        "category": "learning",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Parcourez un site tech de référence",
            "Choisissez une tendance qui vous intrigue",
            "Notez en 2 phrases ce que c'est",
            "Écrivez un impact possible sur votre quotidien"
        ],
        "is_premium": False,
        "icon": "cpu"
    },
    {
        "action_id": "action_learn_007",
        "title": "Fait spatial étonnant",
        "description": "Apprenez un fait surprenant sur l'univers et partagez-le avec quelqu'un aujourd'hui.",
        "category": "learning",
        "duration_min": 2,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Recherchez un fait étonnant sur l'espace",
            "Vérifiez sa véracité avec une source fiable",
            "Mémorisez-le en créant une image mentale",
            "Préparez-vous à le raconter à quelqu'un"
        ],
        "is_premium": False,
        "icon": "rocket"
    },
    {
        "action_id": "action_learn_008",
        "title": "Bio express",
        "description": "Explorez un processus biologique fascinant comme la photosynthèse ou l'ADN en 5 minutes.",
        "category": "learning",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "low",
        "instructions": [
            "Choisissez un processus biologique",
            "Lisez une explication vulgarisée",
            "Dessinez un schéma simple du processus",
            "Identifiez pourquoi ce processus est essentiel"
        ],
        "is_premium": False,
        "icon": "dna"
    },

    # History & Culture (009-012)
    {
        "action_id": "action_learn_009",
        "title": "Minute historique",
        "description": "Découvrez un événement historique marquant et comprenez son influence sur le monde actuel.",
        "category": "learning",
        "duration_min": 3,
        "duration_max": 8,
        "energy_level": "low",
        "instructions": [
            "Choisissez une date ou un événement historique",
            "Lisez un résumé de 200 mots maximum",
            "Notez les causes et les conséquences principales",
            "Reliez cet événement à une réalité d'aujourd'hui"
        ],
        "is_premium": False,
        "icon": "landmark"
    },
    {
        "action_id": "action_learn_010",
        "title": "Culture du monde",
        "description": "Explorez une tradition culturelle d'un pays que vous ne connaissez pas encore.",
        "category": "learning",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Choisissez un pays au hasard sur une carte",
            "Recherchez une tradition ou coutume locale",
            "Notez ce qui vous surprend ou vous inspire",
            "Comparez avec une tradition de votre propre culture"
        ],
        "is_premium": False,
        "icon": "globe"
    },
    {
        "action_id": "action_learn_011",
        "title": "Mouvement artistique",
        "description": "Découvrez un mouvement artistique en 5 minutes : ses principes, ses artistes clés et une œuvre emblématique.",
        "category": "learning",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "low",
        "instructions": [
            "Choisissez un mouvement : impressionnisme, cubisme, etc.",
            "Identifiez 2-3 artistes majeurs du mouvement",
            "Observez une œuvre emblématique pendant 1 minute",
            "Notez les 3 caractéristiques visuelles principales"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    {
        "action_id": "action_learn_012",
        "title": "Architecture éclair",
        "description": "Apprenez à reconnaître un style architectural en observant ses éléments distinctifs.",
        "category": "learning",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Choisissez un style : gothique, art déco, brutalisme…",
            "Identifiez 3 éléments architecturaux distinctifs",
            "Trouvez un bâtiment célèbre de ce style",
            "Cherchez un exemple près de chez vous"
        ],
        "is_premium": False,
        "icon": "building"
    },

    # Philosophy & Psychology (013-016)
    {
        "action_id": "action_learn_013",
        "title": "Exercice stoïcien",
        "description": "Pratiquez un exercice stoïcien pour renforcer votre résilience mentale au quotidien.",
        "category": "learning",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Lisez une citation stoïcienne (Marc Aurèle, Épictète…)",
            "Réfléchissez à sa signification dans votre vie",
            "Identifiez une situation récente où l'appliquer",
            "Écrivez une intention pour la journée basée dessus"
        ],
        "is_premium": False,
        "icon": "scroll"
    },
    {
        "action_id": "action_learn_014",
        "title": "Biais cognitif",
        "description": "Identifiez un biais cognitif courant et repérez comment il influence vos décisions.",
        "category": "learning",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Choisissez un biais : confirmation, ancrage, disponibilité…",
            "Lisez sa définition et un exemple",
            "Rappelez-vous une décision où ce biais a pu jouer",
            "Notez comment le détecter à l'avenir"
        ],
        "is_premium": False,
        "icon": "brain"
    },
    {
        "action_id": "action_learn_015",
        "title": "Expérience de pensée",
        "description": "Explorez une expérience de pensée philosophique et développez votre réflexion critique.",
        "category": "learning",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "low",
        "instructions": [
            "Choisissez : le trolley, la caverne de Platon, le cerveau dans une cuve…",
            "Lisez le scénario complet",
            "Écrivez votre position et vos arguments",
            "Imaginez le contre-argument le plus fort",
            "Révisez votre position si nécessaire"
        ],
        "is_premium": True,
        "icon": "lightbulb"
    },
    {
        "action_id": "action_learn_016",
        "title": "Psycho du quotidien",
        "description": "Découvrez un concept de psychologie applicable immédiatement dans votre vie.",
        "category": "learning",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Choisissez : effet Zeigarnik, flow, dissonance cognitive…",
            "Lisez une explication simple du concept",
            "Identifiez un moment où vous l'avez vécu",
            "Notez comment l'utiliser à votre avantage"
        ],
        "is_premium": False,
        "icon": "brain"
    },

    # Music & Art (017-020)
    {
        "action_id": "action_learn_017",
        "title": "Théorie musicale mini",
        "description": "Apprenez un concept de théorie musicale : gamme, accord ou rythme en quelques minutes.",
        "category": "learning",
        "duration_min": 3,
        "duration_max": 8,
        "energy_level": "low",
        "instructions": [
            "Choisissez : gammes, accords, rythme ou tempo",
            "Lisez une explication simple avec exemples audio",
            "Essayez de reconnaître ce concept dans une chanson connue",
            "Fredonnez ou tapez le rythme pour l'ancrer"
        ],
        "is_premium": False,
        "icon": "music"
    },
    {
        "action_id": "action_learn_018",
        "title": "Croquis en 5 min",
        "description": "Dessinez un objet devant vous en utilisant une technique de croquis rapide.",
        "category": "learning",
        "duration_min": 4,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Choisissez un objet simple devant vous",
            "Observez-le pendant 30 secondes sans dessiner",
            "Dessinez les contours sans lever le crayon (dessin continu)",
            "Ajoutez les ombres principales en 1 minute"
        ],
        "is_premium": False,
        "icon": "pencil"
    },
    {
        "action_id": "action_learn_019",
        "title": "Cercle chromatique",
        "description": "Explorez la théorie des couleurs : apprenez à créer des combinaisons harmonieuses.",
        "category": "learning",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Regardez un cercle chromatique en ligne",
            "Identifiez les couleurs complémentaires",
            "Choisissez 3 couleurs pour une palette harmonieuse",
            "Repérez cette combinaison dans votre environnement"
        ],
        "is_premium": False,
        "icon": "palette"
    },
    {
        "action_id": "action_learn_020",
        "title": "Chef-d'œuvre décrypté",
        "description": "Analysez une œuvre d'art célèbre en observant ses détails cachés et sa symbolique.",
        "category": "learning",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "low",
        "instructions": [
            "Choisissez une œuvre célèbre à regarder en haute résolution",
            "Observez-la en silence pendant 2 minutes",
            "Notez 3 détails que vous n'aviez jamais remarqués",
            "Recherchez la symbolique ou l'histoire derrière l'œuvre",
            "Résumez ce que l'artiste voulait transmettre"
        ],
        "is_premium": True,
        "icon": "image"
    },

    # Code & Digital (021-024)
    {
        "action_id": "action_learn_021",
        "title": "HTML en 5 min",
        "description": "Apprenez une balise HTML et créez un mini exemple fonctionnel.",
        "category": "learning",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "low",
        "instructions": [
            "Choisissez une balise : <table>, <form>, <details>…",
            "Lisez sa documentation avec un exemple",
            "Écrivez votre propre code avec cette balise",
            "Testez-le dans votre navigateur"
        ],
        "is_premium": False,
        "icon": "code"
    },
    {
        "action_id": "action_learn_022",
        "title": "Astuce Excel/Sheets",
        "description": "Maîtrisez une nouvelle formule ou fonctionnalité Excel pour gagner du temps.",
        "category": "learning",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Choisissez : RECHERCHEV, tableau croisé, mise en forme conditionnelle…",
            "Regardez un tutoriel rapide de 2 minutes",
            "Reproduisez l'exemple dans un fichier test",
            "Identifiez où l'utiliser dans votre travail"
        ],
        "is_premium": False,
        "icon": "table"
    },
    {
        "action_id": "action_learn_023",
        "title": "Raccourci clavier ninja",
        "description": "Apprenez 5 raccourcis clavier qui vont accélérer votre travail quotidien.",
        "category": "learning",
        "duration_min": 2,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Choisissez une application que vous utilisez souvent",
            "Recherchez ses 5 raccourcis les plus utiles",
            "Pratiquez chaque raccourci 3 fois",
            "Collez un post-it aide-mémoire sur votre écran"
        ],
        "is_premium": False,
        "icon": "keyboard"
    },
    {
        "action_id": "action_learn_024",
        "title": "Regex pour débutants",
        "description": "Découvrez les expressions régulières avec un exemple pratique de recherche de texte.",
        "category": "learning",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "low",
        "instructions": [
            "Rendez-vous sur un testeur de regex en ligne",
            "Apprenez les bases : . * + ? [] ()",
            "Écrivez une regex pour trouver tous les emails dans un texte",
            "Testez avec différents exemples",
            "Notez les patterns les plus utiles"
        ],
        "is_premium": True,
        "icon": "regex"
    },

    # Writing & Communication (025-028)
    {
        "action_id": "action_learn_025",
        "title": "Haïku du moment",
        "description": "Composez un haïku (5-7-5 syllabes) inspiré par ce que vous ressentez maintenant.",
        "category": "learning",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Observez votre environnement ou votre état d'esprit",
            "Choisissez un thème : nature, émotion, instant présent",
            "Écrivez 3 vers : 5 syllabes / 7 syllabes / 5 syllabes",
            "Relisez et ajustez pour plus de poésie"
        ],
        "is_premium": False,
        "icon": "pen-tool"
    },
    {
        "action_id": "action_learn_026",
        "title": "Elevator pitch",
        "description": "Entraînez-vous à présenter une idée de façon percutante en moins de 60 secondes.",
        "category": "learning",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "low",
        "instructions": [
            "Choisissez un projet ou une idée à présenter",
            "Structurez : problème → solution → bénéfice",
            "Écrivez votre pitch en 3-4 phrases maximum",
            "Récitez-le à voix haute en moins de 60 secondes",
            "Affinez jusqu'à ce que ce soit fluide"
        ],
        "is_premium": False,
        "icon": "presentation"
    },
    {
        "action_id": "action_learn_027",
        "title": "Technique narrative",
        "description": "Apprenez une technique de storytelling et appliquez-la à une anecdote personnelle.",
        "category": "learning",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "low",
        "instructions": [
            "Choisissez : in medias res, cliffhanger, règle de 3…",
            "Lisez une explication avec un exemple",
            "Reprenez une anecdote personnelle",
            "Réécrivez-la en utilisant cette technique"
        ],
        "is_premium": True,
        "icon": "book-open"
    },
    {
        "action_id": "action_learn_028",
        "title": "Écriture libre 5 min",
        "description": "Écrivez sans vous arrêter pendant 5 minutes pour libérer votre créativité.",
        "category": "learning",
        "duration_min": 5,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Prenez un papier ou ouvrez un document vide",
            "Lancez un minuteur de 5 minutes",
            "Écrivez sans vous arrêter, sans corriger, sans réfléchir",
            "Relisez et surlignez une idée intéressante"
        ],
        "is_premium": False,
        "icon": "pen-tool"
    },

    # Math & Logic (029-032)
    {
        "action_id": "action_learn_029",
        "title": "Calcul mental express",
        "description": "Entraînez votre calcul mental avec 10 opérations de difficulté croissante.",
        "category": "learning",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Commencez par 5 multiplications simples (ex : 17×8)",
            "Passez à 3 divisions (ex : 144÷12)",
            "Terminez avec 2 calculs complexes (ex : 25% de 340)",
            "Vérifiez vos réponses avec une calculatrice"
        ],
        "is_premium": False,
        "icon": "calculator"
    },
    {
        "action_id": "action_learn_030",
        "title": "Énigme logique",
        "description": "Résolvez une énigme de logique pour aiguiser votre raisonnement déductif.",
        "category": "learning",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "low",
        "instructions": [
            "Trouvez une énigme logique en ligne",
            "Lisez l'énoncé 2 fois attentivement",
            "Essayez de résoudre sans indice pendant 5 min",
            "Si bloqué, notez vos hypothèses et éliminez",
            "Vérifiez la solution et comprenez le raisonnement"
        ],
        "is_premium": False,
        "icon": "puzzle"
    },
    {
        "action_id": "action_learn_031",
        "title": "Probabilité intuitive",
        "description": "Découvrez un concept de probabilité qui défie l'intuition et comprenez pourquoi.",
        "category": "learning",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "low",
        "instructions": [
            "Choisissez : Monty Hall, paradoxe des anniversaires, gambler's fallacy…",
            "Lisez l'explication du paradoxe",
            "Essayez de l'expliquer avec vos propres mots",
            "Identifiez une situation réelle où il s'applique"
        ],
        "is_premium": True,
        "icon": "dice-5"
    },
    {
        "action_id": "action_learn_032",
        "title": "Sudoku stratégique",
        "description": "Résolvez un sudoku en appliquant des techniques avancées de déduction.",
        "category": "learning",
        "duration_min": 5,
        "duration_max": 12,
        "energy_level": "low",
        "instructions": [
            "Choisissez un sudoku de niveau intermédiaire",
            "Commencez par les lignes/colonnes les plus remplies",
            "Utilisez l'élimination par blocs",
            "Notez les candidats possibles dans les cases vides"
        ],
        "is_premium": False,
        "icon": "grid-3x3"
    },

    # Finance & Business (033-036)
    {
        "action_id": "action_learn_033",
        "title": "Concept investissement",
        "description": "Apprenez un concept d'investissement essentiel pour mieux gérer votre argent.",
        "category": "learning",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "low",
        "instructions": [
            "Choisissez : intérêts composés, diversification, ETF, DCA…",
            "Lisez une explication vulgarisée",
            "Faites un calcul simple d'exemple",
            "Notez comment l'appliquer à votre situation"
        ],
        "is_premium": False,
        "icon": "trending-up"
    },
    {
        "action_id": "action_learn_034",
        "title": "Business model canvas",
        "description": "Analysez le modèle économique d'une entreprise que vous admirez en 5 minutes.",
        "category": "learning",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "low",
        "instructions": [
            "Choisissez une entreprise : Netflix, Airbnb, Decathlon…",
            "Identifiez sa proposition de valeur principale",
            "Notez ses sources de revenus",
            "Listez ses ressources clés et partenaires",
            "Résumez son avantage compétitif en une phrase"
        ],
        "is_premium": True,
        "icon": "briefcase"
    },
    {
        "action_id": "action_learn_035",
        "title": "Astuce de négociation",
        "description": "Découvrez une technique de négociation et préparez-vous à l'utiliser.",
        "category": "learning",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Choisissez : ancrage, BATNA, miroir, étiquetage…",
            "Lisez comment appliquer cette technique",
            "Imaginez un scénario concret d'utilisation",
            "Répétez mentalement votre approche"
        ],
        "is_premium": False,
        "icon": "handshake"
    },
    {
        "action_id": "action_learn_036",
        "title": "Vocabulaire financier",
        "description": "Maîtrisez 5 termes financiers que tout adulte devrait connaître.",
        "category": "learning",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Choisissez 5 termes : ROI, marge brute, cash-flow…",
            "Lisez la définition de chacun",
            "Écrivez un exemple concret pour chaque terme",
            "Testez-vous en cachant les définitions"
        ],
        "is_premium": False,
        "icon": "coins"
    },

    # Reading & Memory (037-040)
    {
        "action_id": "action_learn_037",
        "title": "Lecture rapide",
        "description": "Pratiquez une technique de lecture rapide pour doubler votre vitesse de lecture.",
        "category": "learning",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "low",
        "instructions": [
            "Choisissez un article de 500 mots",
            "Lisez-le normalement et chronométrez-vous",
            "Relisez en utilisant votre doigt comme guide",
            "Élargissez votre vision périphérique sur chaque ligne",
            "Chronométrez à nouveau et comparez"
        ],
        "is_premium": True,
        "icon": "book-open"
    },
    {
        "action_id": "action_learn_038",
        "title": "Palais de mémoire",
        "description": "Construisez un palais de mémoire pour mémoriser une liste de 10 éléments.",
        "category": "learning",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "low",
        "instructions": [
            "Choisissez un lieu que vous connaissez parfaitement",
            "Identifiez 10 points d'ancrage dans ce lieu",
            "Associez chaque élément à mémoriser à un point",
            "Créez des images mentales vivantes et absurdes",
            "Parcourez mentalement votre palais pour vérifier"
        ],
        "is_premium": True,
        "icon": "castle"
    },
    {
        "action_id": "action_learn_039",
        "title": "Rappel actif",
        "description": "Utilisez la technique du rappel actif pour ancrer durablement vos connaissances récentes.",
        "category": "learning",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Fermez vos notes ou votre livre",
            "Écrivez tout ce dont vous vous souvenez du sujet étudié",
            "Comparez avec vos notes pour identifier les lacunes",
            "Révisez uniquement les points oubliés"
        ],
        "is_premium": False,
        "icon": "brain"
    },
    {
        "action_id": "action_learn_040",
        "title": "Résumé en 1 page",
        "description": "Synthétisez un chapitre ou un article en une seule page structurée.",
        "category": "learning",
        "duration_min": 5,
        "duration_max": 12,
        "energy_level": "low",
        "instructions": [
            "Relisez rapidement le contenu à résumer",
            "Identifiez les 3-5 idées principales",
            "Écrivez un résumé structuré en bullet points",
            "Ajoutez votre avis personnel en une phrase"
        ],
        "is_premium": False,
        "icon": "file-text"
    },

    # --- LEARNING / MEDIUM ENERGY (35) ---

    # Languages (041-044)
    {
        "action_id": "action_learn_041",
        "title": "Dialogue imaginaire",
        "description": "Simulez une conversation dans une langue étrangère sur un thème du quotidien.",
        "category": "learning",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Choisissez un scénario : au restaurant, à l'aéroport…",
            "Écrivez les répliques des deux interlocuteurs",
            "Lisez le dialogue à voix haute en jouant les deux rôles",
            "Identifiez les mots que vous avez dû chercher",
            "Révisez ces mots demain"
        ],
        "is_premium": False,
        "icon": "message-circle"
    },
    {
        "action_id": "action_learn_042",
        "title": "Chanson en VO",
        "description": "Traduisez le refrain d'une chanson étrangère pour enrichir votre vocabulaire.",
        "category": "learning",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Choisissez une chanson que vous aimez en langue étrangère",
            "Écoutez-la une fois en entier",
            "Écrivez les paroles du refrain de mémoire",
            "Traduisez chaque ligne mot à mot puis en sens naturel"
        ],
        "is_premium": False,
        "icon": "music"
    },
    {
        "action_id": "action_learn_043",
        "title": "Mini-dictée audio",
        "description": "Écoutez un extrait en langue étrangère et transcrivez ce que vous entendez.",
        "category": "learning",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Trouvez un extrait audio de 30 secondes dans la langue cible",
            "Écoutez 3 fois et transcrivez ce que vous comprenez",
            "Vérifiez avec la transcription officielle",
            "Surlignez les mots que vous avez manqués"
        ],
        "is_premium": True,
        "icon": "headphones"
    },
    {
        "action_id": "action_learn_044",
        "title": "Faux-amis piège",
        "description": "Apprenez 5 faux-amis courants pour éviter les erreurs embarrassantes.",
        "category": "learning",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "medium",
        "instructions": [
            "Choisissez une paire de langues",
            "Listez 5 faux-amis fréquents",
            "Écrivez la vraie traduction de chacun",
            "Créez une phrase correcte pour chaque mot"
        ],
        "is_premium": False,
        "icon": "alert-triangle"
    },

    # Science & Tech (045-048)
    {
        "action_id": "action_learn_045",
        "title": "Expérience maison",
        "description": "Réalisez une mini expérience scientifique avec des objets du quotidien.",
        "category": "learning",
        "duration_min": 5,
        "duration_max": 12,
        "energy_level": "medium",
        "instructions": [
            "Choisissez une expérience simple (densité, réaction acide-base…)",
            "Rassemblez les matériaux nécessaires",
            "Formulez une hypothèse avant de commencer",
            "Réalisez l'expérience et observez",
            "Notez si votre hypothèse était correcte"
        ],
        "is_premium": True,
        "icon": "flask-conical"
    },
    {
        "action_id": "action_learn_046",
        "title": "Veille IA en 7 min",
        "description": "Explorez une avancée récente en intelligence artificielle et ses implications.",
        "category": "learning",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Consultez un site de veille IA",
            "Choisissez une actualité des 7 derniers jours",
            "Résumez l'avancée en 3 phrases",
            "Identifiez un impact concret sur votre domaine",
            "Partagez votre découverte avec un collègue"
        ],
        "is_premium": False,
        "icon": "bot"
    },
    {
        "action_id": "action_learn_047",
        "title": "Anatomie express",
        "description": "Apprenez le fonctionnement d'un organe ou système du corps humain.",
        "category": "learning",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Choisissez : cœur, cerveau, système immunitaire…",
            "Regardez un schéma anatomique",
            "Notez les 3 fonctions principales",
            "Identifiez un geste santé pour cet organe"
        ],
        "is_premium": True,
        "icon": "heart-pulse"
    },
    {
        "action_id": "action_learn_048",
        "title": "Défi mathématique",
        "description": "Résolvez un problème mathématique stimulant qui sort de l'ordinaire.",
        "category": "learning",
        "duration_min": 5,
        "duration_max": 12,
        "energy_level": "medium",
        "instructions": [
            "Trouvez un problème de niveau intermédiaire en ligne",
            "Identifiez les données et l'inconnue",
            "Testez au moins 2 approches de résolution",
            "Vérifiez votre réponse et comprenez la méthode optimale"
        ],
        "is_premium": False,
        "icon": "sigma"
    },

    # History & Culture (049-051)
    {
        "action_id": "action_learn_049",
        "title": "Cartographie mentale",
        "description": "Créez une carte mentale reliant 5 événements historiques entre eux.",
        "category": "learning",
        "duration_min": 7,
        "duration_max": 12,
        "energy_level": "medium",
        "instructions": [
            "Choisissez une période : Renaissance, Guerres mondiales…",
            "Listez 5 événements majeurs de cette période",
            "Dessinez les liens de cause à effet entre eux",
            "Ajoutez les personnages clés à chaque événement",
            "Identifiez le fil conducteur principal"
        ],
        "is_premium": False,
        "icon": "map"
    },
    {
        "action_id": "action_learn_050",
        "title": "Cuisine du monde",
        "description": "Découvrez l'histoire d'un plat traditionnel et ce qu'il révèle sur sa culture.",
        "category": "learning",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Choisissez un plat : sushi, couscous, pad thaï…",
            "Recherchez son origine historique",
            "Notez les ingrédients et leur signification culturelle",
            "Identifiez comment le plat a évolué avec le temps"
        ],
        "is_premium": False,
        "icon": "utensils"
    },
    {
        "action_id": "action_learn_051",
        "title": "Mythologie comparée",
        "description": "Comparez un mythe de deux cultures différentes et trouvez les points communs.",
        "category": "learning",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Choisissez un thème : création du monde, héros, déluge…",
            "Trouvez ce mythe dans 2 cultures différentes",
            "Listez les similitudes et les différences",
            "Réfléchissez à pourquoi ces thèmes sont universels"
        ],
        "is_premium": True,
        "icon": "book-open"
    },

    # Philosophy & Psychology (052-054)
    {
        "action_id": "action_learn_052",
        "title": "Débat intérieur",
        "description": "Argumentez pour ET contre une idée controversée pour muscler votre esprit critique.",
        "category": "learning",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Choisissez un sujet de débat",
            "Écrivez 3 arguments POUR en 2 minutes",
            "Écrivez 3 arguments CONTRE en 2 minutes",
            "Identifiez l'argument le plus fort de chaque côté",
            "Formulez votre position nuancée"
        ],
        "is_premium": False,
        "icon": "scale"
    },
    {
        "action_id": "action_learn_053",
        "title": "Philosophe du jour",
        "description": "Découvrez la pensée d'un philosophe en lisant et analysant une de ses citations.",
        "category": "learning",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Choisissez un philosophe que vous ne connaissez pas",
            "Lisez sa biographie en 1 minute",
            "Trouvez une citation marquante",
            "Analysez-la en la reliant à votre vie actuelle"
        ],
        "is_premium": False,
        "icon": "quote"
    },
    {
        "action_id": "action_learn_054",
        "title": "Test de pensée critique",
        "description": "Évaluez une info virale récente avec une méthode de vérification en 5 étapes.",
        "category": "learning",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Trouvez une info partagée sur les réseaux sociaux",
            "Vérifiez la source originale",
            "Cherchez des sources contradictoires",
            "Identifiez les biais potentiels de l'auteur",
            "Formulez votre conclusion argumentée"
        ],
        "is_premium": False,
        "icon": "search"
    },

    # Music & Art (055-057)
    {
        "action_id": "action_learn_055",
        "title": "Écoute active musicale",
        "description": "Écoutez un morceau en identifiant chaque instrument et son rôle dans l'arrangement.",
        "category": "learning",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Choisissez un morceau avec plusieurs instruments",
            "Première écoute : identifiez tous les instruments",
            "Deuxième écoute : suivez un seul instrument",
            "Notez comment les instruments interagissent",
            "Identifiez le moment le plus intense du morceau"
        ],
        "is_premium": False,
        "icon": "headphones"
    },
    {
        "action_id": "action_learn_056",
        "title": "Dessin de mémoire",
        "description": "Observez un objet pendant 30 secondes puis dessinez-le de mémoire.",
        "category": "learning",
        "duration_min": 5,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Choisissez un objet avec des détails intéressants",
            "Observez-le attentivement pendant 30 secondes",
            "Cachez l'objet et dessinez-le de mémoire",
            "Comparez votre dessin avec l'original",
            "Notez les détails que vous avez oubliés"
        ],
        "is_premium": True,
        "icon": "pencil"
    },
    {
        "action_id": "action_learn_057",
        "title": "Composition photo",
        "description": "Apprenez une règle de composition photographique et prenez 3 photos l'appliquant.",
        "category": "learning",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Choisissez : règle des tiers, lignes directrices, cadre dans le cadre…",
            "Lisez une explication avec exemples visuels",
            "Prenez 3 photos appliquant cette règle",
            "Comparez vos photos et choisissez la meilleure"
        ],
        "is_premium": False,
        "icon": "camera"
    },

    # Code & Digital (058-061)
    {
        "action_id": "action_learn_058",
        "title": "CSS créatif",
        "description": "Créez une animation CSS simple pour comprendre les transitions et keyframes.",
        "category": "learning",
        "duration_min": 7,
        "duration_max": 12,
        "energy_level": "medium",
        "instructions": [
            "Ouvrez un éditeur en ligne (CodePen, JSFiddle…)",
            "Créez un élément HTML simple (bouton, div…)",
            "Ajoutez une animation CSS avec @keyframes",
            "Expérimentez avec les durées et les courbes de timing",
            "Sauvegardez votre création"
        ],
        "is_premium": False,
        "icon": "code"
    },
    {
        "action_id": "action_learn_059",
        "title": "Terminal en 5 min",
        "description": "Apprenez 5 commandes terminal essentielles pour naviguer comme un pro.",
        "category": "learning",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Ouvrez votre terminal",
            "Pratiquez : ls, cd, mkdir, cp, mv",
            "Créez un dossier, déplacez un fichier dedans",
            "Essayez les options courantes (-la, -r, -v)"
        ],
        "is_premium": False,
        "icon": "terminal"
    },
    {
        "action_id": "action_learn_060",
        "title": "API pour débutants",
        "description": "Comprenez ce qu'est une API en faisant votre premier appel à une API publique.",
        "category": "learning",
        "duration_min": 7,
        "duration_max": 12,
        "energy_level": "medium",
        "instructions": [
            "Comprenez le concept : requête → réponse",
            "Trouvez une API publique gratuite (météo, blagues…)",
            "Faites un appel GET dans votre navigateur",
            "Lisez la réponse JSON et identifiez les données",
            "Imaginez une utilisation concrète de cette API"
        ],
        "is_premium": True,
        "icon": "cloud"
    },
    {
        "action_id": "action_learn_061",
        "title": "Git essentiel",
        "description": "Maîtrisez les commandes Git de base pour versionner vos projets.",
        "category": "learning",
        "duration_min": 7,
        "duration_max": 12,
        "energy_level": "medium",
        "instructions": [
            "Créez un dossier test et initialisez git init",
            "Créez un fichier et faites git add + git commit",
            "Modifiez le fichier et observez git diff",
            "Créez une branche et fusionnez-la"
        ],
        "is_premium": False,
        "icon": "git-branch"
    },

    # Writing (062-064)
    {
        "action_id": "action_learn_062",
        "title": "Micro-fiction 100 mots",
        "description": "Écrivez une histoire complète en exactement 100 mots — un exercice de concision.",
        "category": "learning",
        "duration_min": 7,
        "duration_max": 12,
        "energy_level": "medium",
        "instructions": [
            "Choisissez un thème ou un premier mot au hasard",
            "Écrivez un premier jet sans compter les mots",
            "Comptez et ajustez pour atteindre exactement 100 mots",
            "Assurez-vous que l'histoire a un début, un milieu et une fin",
            "Relisez à voix haute pour vérifier le rythme"
        ],
        "is_premium": False,
        "icon": "file-text"
    },
    {
        "action_id": "action_learn_063",
        "title": "Métaphore créative",
        "description": "Inventez 5 métaphores originales pour décrire des émotions ou des situations.",
        "category": "learning",
        "duration_min": 5,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Listez 5 émotions ou situations (joie, stress, attente…)",
            "Pour chacune, trouvez une comparaison inattendue",
            "Développez la métaphore en une phrase complète",
            "Choisissez votre préférée et intégrez-la dans un texte court"
        ],
        "is_premium": False,
        "icon": "sparkles"
    },
    {
        "action_id": "action_learn_064",
        "title": "Réécriture de style",
        "description": "Réécrivez un texte simple dans le style d'un auteur célèbre.",
        "category": "learning",
        "duration_min": 7,
        "duration_max": 12,
        "energy_level": "medium",
        "instructions": [
            "Écrivez 3 phrases décrivant votre petit-déjeuner",
            "Choisissez un auteur : Proust, Hemingway, Camus…",
            "Réécrivez les phrases dans son style",
            "Comparez les deux versions et notez les différences"
        ],
        "is_premium": True,
        "icon": "pen-tool"
    },

    # Finance & Business (065-067)
    {
        "action_id": "action_learn_065",
        "title": "Analyse SWOT express",
        "description": "Réalisez une analyse SWOT rapide de votre projet ou de votre carrière.",
        "category": "learning",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Dessinez un tableau 2×2 : Forces / Faiblesses / Opportunités / Menaces",
            "Listez 3 éléments par case",
            "Identifiez les liens entre forces et opportunités",
            "Définissez une action prioritaire basée sur l'analyse"
        ],
        "is_premium": False,
        "icon": "target"
    },
    {
        "action_id": "action_learn_066",
        "title": "Lecture de bilan",
        "description": "Apprenez à lire un bilan financier simplifié et comprendre la santé d'une entreprise.",
        "category": "learning",
        "duration_min": 7,
        "duration_max": 12,
        "energy_level": "medium",
        "instructions": [
            "Trouvez un bilan simplifié d'une entreprise cotée",
            "Identifiez : actifs, passifs, capitaux propres",
            "Calculez le ratio d'endettement",
            "Comparez avec une entreprise du même secteur",
            "Formulez un avis sur la santé financière"
        ],
        "is_premium": True,
        "icon": "bar-chart-3"
    },
    {
        "action_id": "action_learn_067",
        "title": "Pitch de startup",
        "description": "Analysez le pitch deck d'une startup célèbre et identifiez ce qui le rend efficace.",
        "category": "learning",
        "duration_min": 7,
        "duration_max": 12,
        "energy_level": "medium",
        "instructions": [
            "Trouvez un pitch deck célèbre en ligne (Airbnb, Buffer…)",
            "Identifiez la structure : problème, solution, marché, équipe",
            "Notez les 3 slides les plus convaincantes",
            "Identifiez ce que vous réutiliseriez dans vos présentations"
        ],
        "is_premium": False,
        "icon": "presentation"
    },

    # Reading & Memory (068-071)
    {
        "action_id": "action_learn_068",
        "title": "Technique Feynman",
        "description": "Expliquez un concept complexe comme si vous l'enseigniez à un enfant de 10 ans.",
        "category": "learning",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Choisissez un concept que vous pensez comprendre",
            "Expliquez-le par écrit en termes très simples",
            "Identifiez les passages où vous bloquez",
            "Retournez aux sources pour combler les lacunes",
            "Réécrivez l'explication simplifiée"
        ],
        "is_premium": False,
        "icon": "graduation-cap"
    },
    {
        "action_id": "action_learn_069",
        "title": "Flashcards express",
        "description": "Créez 10 flashcards sur un sujet et testez-vous avec la répétition espacée.",
        "category": "learning",
        "duration_min": 7,
        "duration_max": 12,
        "energy_level": "medium",
        "instructions": [
            "Choisissez un sujet que vous étudiez",
            "Créez 10 questions-réponses sur des cartes ou une app",
            "Testez-vous une première fois",
            "Séparez les cartes : acquis / à revoir",
            "Planifiez une révision dans 24h pour les cartes difficiles"
        ],
        "is_premium": False,
        "icon": "layers"
    },
    {
        "action_id": "action_learn_070",
        "title": "Sketchnote",
        "description": "Résumez un concept en sketchnote : un mélange de dessins et de mots-clés.",
        "category": "learning",
        "duration_min": 7,
        "duration_max": 12,
        "energy_level": "medium",
        "instructions": [
            "Choisissez un concept à synthétiser",
            "Dessinez un titre au centre de la page",
            "Ajoutez des branches avec des mots-clés",
            "Illustrez chaque branche avec un petit dessin",
            "Utilisez des flèches pour montrer les connexions"
        ],
        "is_premium": True,
        "icon": "pencil"
    },
    {
        "action_id": "action_learn_071",
        "title": "Mnémotechnique inventif",
        "description": "Créez un moyen mnémotechnique original pour retenir une information complexe.",
        "category": "learning",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Choisissez une liste ou un concept à mémoriser",
            "Créez un acronyme, une phrase ou une histoire",
            "Rendez-le drôle ou absurde pour mieux retenir",
            "Testez-vous 3 fois de suite sans regarder"
        ],
        "is_premium": False,
        "icon": "lightbulb"
    },

    # Mixed medium (072-075)
    {
        "action_id": "action_learn_072",
        "title": "Podcast résumé",
        "description": "Écoutez 10 minutes d'un podcast éducatif et résumez les points clés.",
        "category": "learning",
        "duration_min": 10,
        "duration_max": 15,
        "energy_level": "medium",
        "instructions": [
            "Choisissez un podcast éducatif dans vos abonnements",
            "Écoutez 10 minutes activement avec un carnet",
            "Notez les 3 idées principales",
            "Formulez une question que l'épisode soulève",
            "Partagez une idée avec quelqu'un"
        ],
        "is_premium": False,
        "icon": "podcast"
    },
    {
        "action_id": "action_learn_073",
        "title": "Carte mentale rapide",
        "description": "Créez une carte mentale sur un sujet qui vous passionne pour organiser vos idées.",
        "category": "learning",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Écrivez le sujet central au milieu d'une feuille",
            "Ajoutez 4-6 branches principales",
            "Développez chaque branche avec 2-3 sous-idées",
            "Utilisez des couleurs et des symboles",
            "Identifiez les connexions entre les branches"
        ],
        "is_premium": True,
        "icon": "network"
    },
    {
        "action_id": "action_learn_074",
        "title": "TED Talk express",
        "description": "Regardez un TED Talk de moins de 10 minutes et extrayez une leçon applicable.",
        "category": "learning",
        "duration_min": 8,
        "duration_max": 15,
        "energy_level": "medium",
        "instructions": [
            "Choisissez un TED Talk de moins de 10 minutes",
            "Regardez-le sans distraction",
            "Notez la thèse principale de l'orateur",
            "Identifiez une action concrète que vous pouvez appliquer aujourd'hui"
        ],
        "is_premium": False,
        "icon": "play-circle"
    },
    {
        "action_id": "action_learn_075",
        "title": "Débat avec soi-même",
        "description": "Écrivez un dialogue entre deux versions de vous-même avec des opinions opposées.",
        "category": "learning",
        "duration_min": 7,
        "duration_max": 12,
        "energy_level": "medium",
        "instructions": [
            "Choisissez un dilemme personnel ou professionnel",
            "Version A : écrivez 3 arguments pour",
            "Version B : répondez avec 3 contre-arguments",
            "Trouvez un compromis ou une synthèse",
            "Notez votre décision finale et pourquoi"
        ],
        "is_premium": True,
        "icon": "message-square"
    },

    # --- LEARNING / HIGH ENERGY (25) ---

    # Languages (076-078)
    {
        "action_id": "action_learn_076",
        "title": "Immersion totale 10 min",
        "description": "Plongez-vous dans une langue étrangère : pensez, lisez et parlez uniquement dans cette langue.",
        "category": "learning",
        "duration_min": 8,
        "duration_max": 12,
        "energy_level": "high",
        "instructions": [
            "Choisissez votre langue cible",
            "Réglez votre téléphone dans cette langue",
            "Lisez un article court dans cette langue",
            "Décrivez à voix haute ce que vous voyez autour de vous",
            "Résumez votre journée dans cette langue"
        ],
        "is_premium": True,
        "icon": "globe"
    },
    {
        "action_id": "action_learn_077",
        "title": "Traduction express",
        "description": "Traduisez un paragraphe court dans les deux sens pour maîtriser les nuances.",
        "category": "learning",
        "duration_min": 7,
        "duration_max": 12,
        "energy_level": "high",
        "instructions": [
            "Choisissez un paragraphe de 50 mots en français",
            "Traduisez-le dans la langue cible",
            "Attendez 5 minutes puis retraduisez en français",
            "Comparez avec l'original et notez les différences"
        ],
        "is_premium": False,
        "icon": "repeat"
    },
    {
        "action_id": "action_learn_078",
        "title": "Discours improvisé",
        "description": "Parlez pendant 3 minutes en langue étrangère sur un sujet tiré au hasard.",
        "category": "learning",
        "duration_min": 5,
        "duration_max": 8,
        "energy_level": "high",
        "instructions": [
            "Tirez un sujet au hasard (générateur en ligne)",
            "Prenez 30 secondes pour structurer vos idées",
            "Parlez pendant 3 minutes sans vous arrêter",
            "Enregistrez-vous pour réécouter ensuite"
        ],
        "is_premium": False,
        "icon": "mic"
    },

    # Science & Tech (079-081)
    {
        "action_id": "action_learn_079",
        "title": "Teach-back scientifique",
        "description": "Expliquez un phénomène scientifique à voix haute comme si vous étiez prof.",
        "category": "learning",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "high",
        "instructions": [
            "Choisissez un phénomène : gravité, évolution, magnétisme…",
            "Préparez une explication en 2 minutes",
            "Expliquez à voix haute en marchant",
            "Utilisez des objets autour de vous comme supports visuels",
            "Identifiez les zones de flou et approfondissez"
        ],
        "is_premium": False,
        "icon": "presentation"
    },
    {
        "action_id": "action_learn_080",
        "title": "Prototype rapide",
        "description": "Construisez un prototype simple en papier ou digital pour tester une idée.",
        "category": "learning",
        "duration_min": 10,
        "duration_max": 15,
        "energy_level": "high",
        "instructions": [
            "Définissez une idée simple à prototyper",
            "Dessinez l'interface ou le mécanisme en 3 minutes",
            "Construisez un prototype papier ou wireframe",
            "Testez-le en simulant l'utilisation",
            "Notez 3 améliorations possibles"
        ],
        "is_premium": True,
        "icon": "box"
    },
    {
        "action_id": "action_learn_081",
        "title": "Coding challenge",
        "description": "Résolvez un défi de programmation de niveau débutant en moins de 15 minutes.",
        "category": "learning",
        "duration_min": 10,
        "duration_max": 15,
        "energy_level": "high",
        "instructions": [
            "Rendez-vous sur un site de challenges (Codewars, LeetCode…)",
            "Choisissez un défi de niveau facile",
            "Lisez l'énoncé et planifiez votre approche",
            "Codez votre solution",
            "Testez et optimisez si possible"
        ],
        "is_premium": False,
        "icon": "code"
    },

    # Philosophy (082-083)
    {
        "action_id": "action_learn_082",
        "title": "Dialogue socratique",
        "description": "Pratiquez la méthode socratique en questionnant vos propres croyances profondes.",
        "category": "learning",
        "duration_min": 7,
        "duration_max": 12,
        "energy_level": "high",
        "instructions": [
            "Choisissez une croyance forte que vous avez",
            "Posez-vous : 'Pourquoi je crois cela ?'",
            "Pour chaque réponse, demandez encore 'Pourquoi ?'",
            "Continuez 5 niveaux de profondeur",
            "Notez si votre croyance a évolué"
        ],
        "is_premium": False,
        "icon": "help-circle"
    },
    {
        "action_id": "action_learn_083",
        "title": "Dilemme éthique",
        "description": "Confrontez-vous à un dilemme éthique réel et structurez votre raisonnement moral.",
        "category": "learning",
        "duration_min": 7,
        "duration_max": 12,
        "energy_level": "high",
        "instructions": [
            "Choisissez un dilemme : IA et emploi, vie privée vs sécurité…",
            "Listez les parties prenantes concernées",
            "Appliquez 2 cadres éthiques : utilitariste et déontologique",
            "Formulez votre position avec ses limites",
            "Imaginez comment quelqu'un en désaccord répondrait"
        ],
        "is_premium": True,
        "icon": "scale"
    },

    # Music & Art (084-086)
    {
        "action_id": "action_learn_084",
        "title": "Composition musicale mini",
        "description": "Créez une mélodie de 8 mesures en chantant ou en tapant un rythme.",
        "category": "learning",
        "duration_min": 7,
        "duration_max": 12,
        "energy_level": "high",
        "instructions": [
            "Choisissez une gamme simple (do majeur)",
            "Chantez ou fredonnez 4 notes pour le thème",
            "Développez en 8 mesures avec répétition et variation",
            "Enregistrez votre création sur votre téléphone",
            "Écoutez et ajustez ce qui sonne faux"
        ],
        "is_premium": False,
        "icon": "music"
    },
    {
        "action_id": "action_learn_085",
        "title": "Art en 10 min",
        "description": "Créez une œuvre d'art complète en 10 minutes avec les moyens du bord.",
        "category": "learning",
        "duration_min": 8,
        "duration_max": 12,
        "energy_level": "high",
        "instructions": [
            "Rassemblez ce que vous avez : stylo, papier, couleurs…",
            "Choisissez un thème ou une émotion",
            "Mettez un minuteur de 10 minutes",
            "Créez sans vous censurer ni effacer",
            "Signez et datez votre création"
        ],
        "is_premium": False,
        "icon": "palette"
    },
    {
        "action_id": "action_learn_086",
        "title": "Critique d'art",
        "description": "Analysez une œuvre d'art avec la méthode DCAF : Décrire, Contextualiser, Analyser, Formuler.",
        "category": "learning",
        "duration_min": 7,
        "duration_max": 12,
        "energy_level": "high",
        "instructions": [
            "Choisissez une œuvre que vous ne connaissez pas",
            "Décrivez objectivement ce que vous voyez",
            "Recherchez le contexte de création",
            "Analysez les choix artistiques (couleur, composition…)",
            "Formulez votre interprétation personnelle"
        ],
        "is_premium": True,
        "icon": "eye"
    },

    # Code (087-089)
    {
        "action_id": "action_learn_087",
        "title": "Mini projet web",
        "description": "Créez une page web interactive simple avec HTML, CSS et JavaScript.",
        "category": "learning",
        "duration_min": 10,
        "duration_max": 15,
        "energy_level": "high",
        "instructions": [
            "Choisissez un micro-projet : compteur, quiz, liste de tâches…",
            "Créez la structure HTML en 3 minutes",
            "Ajoutez le style CSS en 3 minutes",
            "Programmez l'interactivité JavaScript",
            "Testez et déboguez"
        ],
        "is_premium": False,
        "icon": "globe"
    },
    {
        "action_id": "action_learn_088",
        "title": "Automatisation perso",
        "description": "Créez un petit script pour automatiser une tâche répétitive de votre quotidien.",
        "category": "learning",
        "duration_min": 10,
        "duration_max": 15,
        "energy_level": "high",
        "instructions": [
            "Identifiez une tâche que vous faites souvent manuellement",
            "Choisissez un outil : script bash, Python, Automator…",
            "Écrivez les étapes en pseudo-code",
            "Codez et testez votre automatisation",
            "Mesurez le temps gagné"
        ],
        "is_premium": True,
        "icon": "zap"
    },
    {
        "action_id": "action_learn_089",
        "title": "Debug challenge",
        "description": "Trouvez et corrigez les bugs dans un code volontairement erroné.",
        "category": "learning",
        "duration_min": 7,
        "duration_max": 12,
        "energy_level": "high",
        "instructions": [
            "Trouvez un exercice de debug en ligne",
            "Lisez le code et identifiez les erreurs",
            "Corrigez chaque bug un par un",
            "Vérifiez que le programme fonctionne correctement"
        ],
        "is_premium": False,
        "icon": "bug"
    },

    # Writing (090-092)
    {
        "action_id": "action_learn_090",
        "title": "Écriture contrainte",
        "description": "Écrivez un texte en vous imposant une contrainte oulipienne stimulante.",
        "category": "learning",
        "duration_min": 7,
        "duration_max": 12,
        "energy_level": "high",
        "instructions": [
            "Choisissez une contrainte : lipogramme (sans 'e'), monovocalisme…",
            "Choisissez un thème pour votre texte",
            "Écrivez un paragraphe en respectant la contrainte",
            "Relisez et vérifiez que la contrainte est respectée",
            "Admirez la créativité que la contrainte a générée"
        ],
        "is_premium": False,
        "icon": "pen-tool"
    },
    {
        "action_id": "action_learn_091",
        "title": "Article d'opinion",
        "description": "Rédigez un article d'opinion structuré de 200 mots sur un sujet d'actualité.",
        "category": "learning",
        "duration_min": 10,
        "duration_max": 15,
        "energy_level": "high",
        "instructions": [
            "Choisissez un sujet d'actualité qui vous tient à cœur",
            "Structurez : accroche, thèse, 2 arguments, conclusion",
            "Rédigez votre article en 200 mots",
            "Relisez pour la clarté et la persuasion",
            "Demandez un avis à quelqu'un"
        ],
        "is_premium": True,
        "icon": "file-text"
    },
    {
        "action_id": "action_learn_092",
        "title": "Poésie express",
        "description": "Composez un poème de 8 vers avec des rimes sur un thème choisi.",
        "category": "learning",
        "duration_min": 7,
        "duration_max": 12,
        "energy_level": "high",
        "instructions": [
            "Choisissez un thème et un schéma de rimes (ABAB…)",
            "Écrivez les 4 premiers vers en trouvant les rimes",
            "Complétez avec 4 vers qui approfondissent le thème",
            "Relisez à voix haute pour vérifier le rythme"
        ],
        "is_premium": False,
        "icon": "feather"
    },

    # Finance (093-094)
    {
        "action_id": "action_learn_093",
        "title": "Simulation budget",
        "description": "Créez un mini budget prévisionnel pour un projet personnel ou professionnel.",
        "category": "learning",
        "duration_min": 8,
        "duration_max": 15,
        "energy_level": "high",
        "instructions": [
            "Choisissez un projet : vacances, formation, side project…",
            "Listez tous les postes de dépenses",
            "Estimez chaque coût de manière réaliste",
            "Calculez le total et comparez à votre budget disponible",
            "Identifiez les postes à optimiser"
        ],
        "is_premium": False,
        "icon": "wallet"
    },
    {
        "action_id": "action_learn_094",
        "title": "Étude de cas business",
        "description": "Analysez la stratégie d'une entreprise à travers une étude de cas rapide.",
        "category": "learning",
        "duration_min": 10,
        "duration_max": 15,
        "energy_level": "high",
        "instructions": [
            "Choisissez une entreprise : Tesla, Spotify, LVMH…",
            "Identifiez son modèle de revenus principal",
            "Analysez ses 3 décisions stratégiques récentes",
            "Évaluez ses forces et faiblesses face à la concurrence",
            "Formulez une recommandation stratégique"
        ],
        "is_premium": True,
        "icon": "briefcase"
    },

    # Memory & mixed (095-100)
    {
        "action_id": "action_learn_095",
        "title": "Enseignez à quelqu'un",
        "description": "Expliquez quelque chose que vous avez appris récemment à une personne autour de vous.",
        "category": "learning",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "high",
        "instructions": [
            "Choisissez un concept appris cette semaine",
            "Préparez une explication en 2 minutes",
            "Enseignez-le à quelqu'un (ou à votre chat)",
            "Répondez à ses questions",
            "Notez ce que l'exercice vous a appris sur votre compréhension"
        ],
        "is_premium": False,
        "icon": "users"
    },
    {
        "action_id": "action_learn_096",
        "title": "Quiz personnel",
        "description": "Créez et passez un quiz de 10 questions sur vos apprentissages de la semaine.",
        "category": "learning",
        "duration_min": 7,
        "duration_max": 12,
        "energy_level": "high",
        "instructions": [
            "Listez les sujets appris cette semaine",
            "Rédigez 10 questions variées (QCM, vrai/faux, ouvertes)",
            "Attendez 2 minutes puis répondez sans notes",
            "Corrigez-vous et notez votre score",
            "Révisez les réponses incorrectes"
        ],
        "is_premium": False,
        "icon": "clipboard-check"
    },
    {
        "action_id": "action_learn_097",
        "title": "Synthèse de la semaine",
        "description": "Rédigez une synthèse structurée de tout ce que vous avez appris cette semaine.",
        "category": "learning",
        "duration_min": 10,
        "duration_max": 15,
        "energy_level": "high",
        "instructions": [
            "Parcourez vos notes de la semaine",
            "Identifiez les 5 apprentissages les plus importants",
            "Rédigez un paragraphe pour chacun",
            "Créez des liens entre les différents apprentissages",
            "Définissez 3 objectifs d'apprentissage pour la semaine prochaine"
        ],
        "is_premium": False,
        "icon": "notebook"
    },
    {
        "action_id": "action_learn_098",
        "title": "Présentation éclair",
        "description": "Préparez et donnez une présentation de 3 minutes sur un sujet maîtrisé.",
        "category": "learning",
        "duration_min": 8,
        "duration_max": 15,
        "energy_level": "high",
        "instructions": [
            "Choisissez un sujet que vous connaissez bien",
            "Structurez en 3 parties avec une accroche",
            "Préparez 3 slides mentales maximum",
            "Présentez debout pendant 3 minutes chrono",
            "Enregistrez-vous pour vous améliorer"
        ],
        "is_premium": True,
        "icon": "presentation"
    },
    {
        "action_id": "action_learn_099",
        "title": "Exploration Wikipedia",
        "description": "Partez d'un article Wikipedia et suivez 5 liens pour découvrir des sujets inattendus.",
        "category": "learning",
        "duration_min": 8,
        "duration_max": 15,
        "energy_level": "high",
        "instructions": [
            "Cliquez sur 'Article au hasard' sur Wikipedia",
            "Lisez l'introduction de l'article",
            "Cliquez sur un lien qui vous intrigue dans le texte",
            "Répétez 4 fois de plus",
            "Notez la chaîne de sujets et ce que vous avez appris"
        ],
        "is_premium": False,
        "icon": "compass"
    },
    {
        "action_id": "action_learn_100",
        "title": "Création de cours mini",
        "description": "Concevez un mini-cours de 5 minutes sur un sujet que vous maîtrisez.",
        "category": "learning",
        "duration_min": 10,
        "duration_max": 15,
        "energy_level": "high",
        "instructions": [
            "Choisissez un sujet et définissez l'objectif du cours",
            "Créez un plan : intro, 3 points clés, conclusion",
            "Préparez un exemple ou exercice pour chaque point",
            "Enregistrez votre cours de 5 minutes",
            "Réécoutez et notez les améliorations"
        ],
        "is_premium": True,
        "icon": "graduation-cap"
    },

    # =========================================================================
    # PRODUCTIVITY (100 actions) — action_prod_001 to action_prod_100
    # Low energy: 001-040 | Medium energy: 041-075 | High energy: 076-100
    # =========================================================================

    # --- PRODUCTIVITY / LOW ENERGY (40) ---

    # GTD & Organization (001-004)
    {
        "action_id": "action_prod_001",
        "title": "Inbox zéro express",
        "description": "Videz votre boîte de réception en triant chaque message en moins de 5 secondes.",
        "category": "productivity",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "low",
        "instructions": [
            "Ouvrez votre boîte de réception principale",
            "Pour chaque email : répondre (<2min), déléguer, planifier ou supprimer",
            "Archivez tout ce qui est traité",
            "Visez 0 message non traité dans l'inbox"
        ],
        "is_premium": False,
        "icon": "inbox"
    },
    {
        "action_id": "action_prod_002",
        "title": "Revue hebdo rapide",
        "description": "Passez en revue votre semaine écoulée et préparez la suivante en 10 minutes.",
        "category": "productivity",
        "duration_min": 7,
        "duration_max": 12,
        "energy_level": "low",
        "instructions": [
            "Listez les 3 accomplissements de la semaine",
            "Identifiez ce qui n'a pas avancé et pourquoi",
            "Définissez 3 priorités pour la semaine prochaine",
            "Bloquez du temps dans votre agenda pour chacune"
        ],
        "is_premium": False,
        "icon": "calendar-check"
    },
    {
        "action_id": "action_prod_003",
        "title": "Règle des 2 minutes",
        "description": "Identifiez et exécutez immédiatement toutes les micro-tâches de moins de 2 minutes.",
        "category": "productivity",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "low",
        "instructions": [
            "Parcourez votre liste de tâches en attente",
            "Identifiez celles qui prennent moins de 2 minutes",
            "Exécutez-les immédiatement une par une",
            "Rayez-les de votre liste avec satisfaction"
        ],
        "is_premium": False,
        "icon": "timer"
    },
    {
        "action_id": "action_prod_004",
        "title": "Mise à jour projets",
        "description": "Mettez à jour l'état de vos projets en cours et identifiez les prochaines actions.",
        "category": "productivity",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "low",
        "instructions": [
            "Listez tous vos projets actifs",
            "Pour chacun, notez le statut actuel",
            "Identifiez la prochaine action concrète",
            "Marquez les projets bloqués et notez le blocage"
        ],
        "is_premium": False,
        "icon": "folder-check"
    },

    # Deep Work (005-008)
    {
        "action_id": "action_prod_005",
        "title": "Pomodoro solo",
        "description": "Lancez un sprint de concentration de 10 minutes sur votre tâche la plus importante.",
        "category": "productivity",
        "duration_min": 10,
        "duration_max": 12,
        "energy_level": "low",
        "instructions": [
            "Choisissez votre tâche la plus importante",
            "Fermez toutes les distractions (notifications, onglets…)",
            "Lancez un minuteur de 10 minutes",
            "Travaillez sans interruption jusqu'à la sonnerie",
            "Notez ce que vous avez accompli"
        ],
        "is_premium": False,
        "icon": "clock"
    },
    {
        "action_id": "action_prod_006",
        "title": "Audit distractions",
        "description": "Identifiez vos 3 principales sources de distraction et créez un plan pour les neutraliser.",
        "category": "productivity",
        "duration_min": 5,
        "duration_max": 8,
        "energy_level": "low",
        "instructions": [
            "Réfléchissez aux moments où vous perdez le focus",
            "Listez vos 3 distractions les plus fréquentes",
            "Pour chacune, trouvez une parade concrète",
            "Mettez en place la première parade maintenant"
        ],
        "is_premium": True,
        "icon": "shield"
    },
    {
        "action_id": "action_prod_007",
        "title": "Single-tasking",
        "description": "Pratiquez le mono-tâche en vous concentrant sur une seule chose pendant 10 minutes.",
        "category": "productivity",
        "duration_min": 10,
        "duration_max": 12,
        "energy_level": "low",
        "instructions": [
            "Choisissez UNE seule tâche",
            "Fermez tout le reste : onglets, apps, notifications",
            "Posez votre téléphone face cachée dans une autre pièce",
            "Travaillez uniquement sur cette tâche pendant 10 min"
        ],
        "is_premium": False,
        "icon": "focus"
    },
    {
        "action_id": "action_prod_008",
        "title": "Préparation deep work",
        "description": "Préparez votre environnement pour une session de travail profond à venir.",
        "category": "productivity",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Choisissez le créneau pour votre prochaine session deep work",
            "Préparez votre bureau : rangez, eau, matériel prêt",
            "Listez exactement ce que vous accomplirez",
            "Prévenez vos collègues/proches que vous serez indisponible"
        ],
        "is_premium": True,
        "icon": "layout"
    },

    # Planning & Strategy (009-012)
    {
        "action_id": "action_prod_009",
        "title": "Matrice Eisenhower",
        "description": "Classez vos tâches par urgence et importance pour prioriser intelligemment.",
        "category": "productivity",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "low",
        "instructions": [
            "Dessinez la matrice 2×2 : Urgent/Important",
            "Listez toutes vos tâches en attente",
            "Placez chaque tâche dans le bon quadrant",
            "Commencez par Important + Urgent, planifiez Important + Non-urgent"
        ],
        "is_premium": False,
        "icon": "grid-2x2"
    },
    {
        "action_id": "action_prod_010",
        "title": "Time-blocking 1 jour",
        "description": "Planifiez votre journée de demain en blocs de temps dédiés à chaque activité.",
        "category": "productivity",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "low",
        "instructions": [
            "Ouvrez votre agenda pour demain",
            "Identifiez vos 3 priorités du jour",
            "Bloquez des créneaux spécifiques pour chaque priorité",
            "Ajoutez des tampons de 15 min entre les blocs",
            "Incluez un bloc pour l'imprévu"
        ],
        "is_premium": True,
        "icon": "calendar"
    },
    {
        "action_id": "action_prod_011",
        "title": "Objectif SMART",
        "description": "Transformez un objectif vague en objectif SMART : Spécifique, Mesurable, Atteignable, Réaliste, Temporel.",
        "category": "productivity",
        "duration_min": 5,
        "duration_max": 8,
        "energy_level": "low",
        "instructions": [
            "Choisissez un objectif que vous voulez atteindre",
            "Rendez-le Spécifique : que voulez-vous exactement ?",
            "Rendez-le Mesurable : quel indicateur de succès ?",
            "Vérifiez qu'il est Atteignable et fixez une date limite",
            "Écrivez l'objectif SMART final en une phrase"
        ],
        "is_premium": False,
        "icon": "target"
    },
    {
        "action_id": "action_prod_012",
        "title": "Check OKR rapide",
        "description": "Vérifiez l'avancement de vos objectifs et résultats clés du trimestre.",
        "category": "productivity",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "low",
        "instructions": [
            "Relisez vos OKR du trimestre",
            "Évaluez chaque résultat clé en pourcentage",
            "Identifiez ceux qui sont en retard",
            "Définissez une action corrective pour chaque retard"
        ],
        "is_premium": True,
        "icon": "bar-chart"
    },

    # Communication (013-016)
    {
        "action_id": "action_prod_013",
        "title": "Template email",
        "description": "Créez un modèle d'email réutilisable pour une situation fréquente.",
        "category": "productivity",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "low",
        "instructions": [
            "Identifiez un type d'email que vous envoyez souvent",
            "Rédigez un modèle avec des espaces à personnaliser",
            "Testez-le en l'adaptant à un cas réel",
            "Sauvegardez-le dans vos brouillons ou un outil de templates"
        ],
        "is_premium": False,
        "icon": "mail"
    },
    {
        "action_id": "action_prod_014",
        "title": "Préparer une réunion",
        "description": "Préparez votre prochaine réunion en 5 minutes pour la rendre efficace.",
        "category": "productivity",
        "duration_min": 4,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Identifiez l'objectif précis de la réunion",
            "Listez les 3 points à aborder absolument",
            "Préparez une question pour chaque participant",
            "Définissez les décisions attendues en sortie"
        ],
        "is_premium": False,
        "icon": "users"
    },
    {
        "action_id": "action_prod_015",
        "title": "Feedback constructif",
        "description": "Préparez un feedback constructif en utilisant la méthode SBI (Situation-Comportement-Impact).",
        "category": "productivity",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "low",
        "instructions": [
            "Identifiez la situation précise à aborder",
            "Décrivez le comportement observé (factuel)",
            "Expliquez l'impact concret de ce comportement",
            "Formulez une suggestion d'amélioration positive"
        ],
        "is_premium": False,
        "icon": "message-circle"
    },
    {
        "action_id": "action_prod_016",
        "title": "Message réseau pro",
        "description": "Rédigez un message de networking personnalisé pour élargir votre réseau professionnel.",
        "category": "productivity",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "low",
        "instructions": [
            "Choisissez une personne que vous souhaitez contacter",
            "Trouvez un point commun ou un sujet d'intérêt partagé",
            "Rédigez un message court et personnalisé",
            "Proposez une valeur ajoutée avant de demander quoi que ce soit"
        ],
        "is_premium": True,
        "icon": "link"
    },

    # Creativity & Ideas (017-020)
    {
        "action_id": "action_prod_017",
        "title": "Mind-map flash",
        "description": "Créez une carte mentale rapide pour explorer un problème sous tous les angles.",
        "category": "productivity",
        "duration_min": 5,
        "duration_max": 8,
        "energy_level": "low",
        "instructions": [
            "Écrivez votre problème au centre d'une feuille",
            "Ajoutez toutes les idées qui vous viennent en branches",
            "Ne censurez rien pendant 3 minutes",
            "Relisez et entourez les 2-3 pistes les plus prometteuses"
        ],
        "is_premium": False,
        "icon": "network"
    },
    {
        "action_id": "action_prod_018",
        "title": "Méthode SCAMPER",
        "description": "Utilisez SCAMPER pour générer des idées innovantes à partir d'un produit existant.",
        "category": "productivity",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "low",
        "instructions": [
            "Choisissez un produit, service ou processus à améliorer",
            "Appliquez chaque lettre : Substituer, Combiner, Adapter, Modifier, Proposer, Éliminer, Réorganiser",
            "Notez au moins une idée par lettre",
            "Sélectionnez les 2 meilleures idées à explorer"
        ],
        "is_premium": False,
        "icon": "lightbulb"
    },
    {
        "action_id": "action_prod_019",
        "title": "Brainstorm inversé",
        "description": "Trouvez des solutions en vous demandant comment AGGRAVER le problème.",
        "category": "productivity",
        "duration_min": 5,
        "duration_max": 8,
        "energy_level": "low",
        "instructions": [
            "Définissez clairement votre problème",
            "Listez 5 façons de rendre ce problème PIRE",
            "Inversez chaque idée pour trouver une solution",
            "Classez les solutions par faisabilité"
        ],
        "is_premium": False,
        "icon": "rotate-ccw"
    },
    {
        "action_id": "action_prod_020",
        "title": "Mot aléatoire créatif",
        "description": "Utilisez un mot tiré au hasard pour trouver des connexions créatives avec votre projet.",
        "category": "productivity",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Ouvrez un dictionnaire à une page au hasard et choisissez un mot",
            "Listez 5 caractéristiques de ce mot",
            "Forcez des connexions entre ces caractéristiques et votre projet",
            "Notez les idées inattendues qui émergent"
        ],
        "is_premium": True,
        "icon": "shuffle"
    },

    # Digital Cleanup (021-024)
    {
        "action_id": "action_prod_021",
        "title": "Bureau numérique propre",
        "description": "Rangez votre bureau d'ordinateur en moins de 5 minutes pour un espace mental clair.",
        "category": "productivity",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Supprimez les fichiers inutiles du bureau",
            "Classez les fichiers restants dans des dossiers",
            "Créez un dossier 'À trier' pour le reste",
            "Vérifiez que votre fond d'écran est visible"
        ],
        "is_premium": False,
        "icon": "monitor"
    },
    {
        "action_id": "action_prod_022",
        "title": "Favoris nettoyage",
        "description": "Triez vos favoris de navigateur pour retrouver instantanément vos ressources.",
        "category": "productivity",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "low",
        "instructions": [
            "Ouvrez votre gestionnaire de favoris",
            "Supprimez les liens morts ou obsolètes",
            "Créez des dossiers thématiques",
            "Classez les favoris restants par catégorie"
        ],
        "is_premium": False,
        "icon": "bookmark"
    },
    {
        "action_id": "action_prod_023",
        "title": "Audit mots de passe",
        "description": "Vérifiez la sécurité de vos 5 comptes les plus importants et renforcez les mots de passe faibles.",
        "category": "productivity",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "low",
        "instructions": [
            "Listez vos 5 comptes les plus sensibles",
            "Vérifiez que chaque mot de passe est unique",
            "Changez ceux qui sont faibles ou réutilisés",
            "Activez l'authentification à 2 facteurs si possible"
        ],
        "is_premium": False,
        "icon": "lock"
    },
    {
        "action_id": "action_prod_024",
        "title": "App détox",
        "description": "Désinstallez les applications que vous n'utilisez plus et désactivez les notifications inutiles.",
        "category": "productivity",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "low",
        "instructions": [
            "Parcourez toutes les apps de votre téléphone",
            "Supprimez celles que vous n'avez pas ouvertes depuis 1 mois",
            "Désactivez les notifications non essentielles",
            "Réorganisez votre écran d'accueil par usage"
        ],
        "is_premium": False,
        "icon": "smartphone"
    },

    # Habits & Systems (025-028)
    {
        "action_id": "action_prod_025",
        "title": "Habit stacking",
        "description": "Attachez une nouvelle habitude à une habitude existante pour l'ancrer naturellement.",
        "category": "productivity",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Choisissez une habitude que vous voulez créer",
            "Identifiez une habitude existante bien ancrée",
            "Formulez : 'Après [habitude existante], je fais [nouvelle habitude]'",
            "Écrivez cette formule et affichez-la"
        ],
        "is_premium": True,
        "icon": "layers"
    },
    {
        "action_id": "action_prod_026",
        "title": "Design d'environnement",
        "description": "Modifiez votre espace physique pour faciliter vos bonnes habitudes.",
        "category": "productivity",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "low",
        "instructions": [
            "Choisissez une habitude à renforcer",
            "Rendez le déclencheur visible (ex : livre sur l'oreiller)",
            "Supprimez les frictions (préparez vos affaires la veille)",
            "Rendez les mauvaises habitudes plus difficiles d'accès"
        ],
        "is_premium": False,
        "icon": "home"
    },
    {
        "action_id": "action_prod_027",
        "title": "Réduction fatigue décision",
        "description": "Éliminez 3 décisions quotidiennes en les automatisant ou en les planifiant.",
        "category": "productivity",
        "duration_min": 4,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Listez les décisions que vous prenez chaque jour",
            "Identifiez les 3 plus récurrentes et moins importantes",
            "Automatisez-les : menu fixe, tenue pré-choisie, routine…",
            "Mettez en place ces automatismes dès aujourd'hui"
        ],
        "is_premium": True,
        "icon": "settings"
    },
    {
        "action_id": "action_prod_028",
        "title": "Tracker d'habitudes",
        "description": "Mettez en place un tracker visuel pour suivre vos habitudes clés du mois.",
        "category": "productivity",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "low",
        "instructions": [
            "Choisissez 3-5 habitudes à suivre ce mois",
            "Créez un tableau : habitudes en lignes, jours en colonnes",
            "Cochez les jours réussis (l'effet visuel motive)",
            "Affichez le tracker dans un endroit que vous voyez chaque jour"
        ],
        "is_premium": False,
        "icon": "check-square"
    },

    # Review & Reflection (029-032)
    {
        "action_id": "action_prod_029",
        "title": "3 victoires du jour",
        "description": "Notez vos 3 victoires de la journée, même les plus petites, pour renforcer votre motivation.",
        "category": "productivity",
        "duration_min": 2,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Repensez à votre journée",
            "Identifiez 3 choses que vous avez accomplies",
            "Écrivez-les dans un carnet ou une note",
            "Ressentez la satisfaction de ces accomplissements"
        ],
        "is_premium": False,
        "icon": "trophy"
    },
    {
        "action_id": "action_prod_030",
        "title": "Leçon apprise",
        "description": "Identifiez une leçon tirée d'un échec ou d'une difficulté récente.",
        "category": "productivity",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Pensez à un moment difficile ou un échec récent",
            "Décrivez factuellement ce qui s'est passé",
            "Identifiez ce que vous feriez différemment",
            "Formulez la leçon en une phrase que vous retiendrez"
        ],
        "is_premium": False,
        "icon": "lightbulb"
    },
    {
        "action_id": "action_prod_031",
        "title": "Gratitude pro",
        "description": "Notez 3 choses pour lesquelles vous êtes reconnaissant dans votre travail.",
        "category": "productivity",
        "duration_min": 2,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Pensez à votre environnement professionnel",
            "Trouvez 3 éléments positifs (collègue, outil, opportunité…)",
            "Écrivez pourquoi chacun compte pour vous",
            "Envoyez un merci à l'une de ces personnes si possible"
        ],
        "is_premium": False,
        "icon": "heart"
    },
    {
        "action_id": "action_prod_032",
        "title": "Rétro mini semaine",
        "description": "Faites une mini-rétrospective de votre semaine avec la méthode Start/Stop/Continue.",
        "category": "productivity",
        "duration_min": 5,
        "duration_max": 8,
        "energy_level": "low",
        "instructions": [
            "Start : qu'allez-vous commencer à faire ?",
            "Stop : qu'allez-vous arrêter de faire ?",
            "Continue : que devez-vous continuer ?",
            "Choisissez une action concrète dans chaque catégorie"
        ],
        "is_premium": False,
        "icon": "refresh-cw"
    },

    # Automation (033-036)
    {
        "action_id": "action_prod_033",
        "title": "Tâche répétitive repérée",
        "description": "Identifiez une tâche que vous faites manuellement et qui pourrait être automatisée.",
        "category": "productivity",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Listez les tâches que vous répétez chaque semaine",
            "Identifiez celle qui prend le plus de temps",
            "Recherchez un outil d'automatisation adapté",
            "Planifiez un créneau pour mettre en place l'automatisation"
        ],
        "is_premium": False,
        "icon": "repeat"
    },
    {
        "action_id": "action_prod_034",
        "title": "Créer un template",
        "description": "Transformez un document que vous recréez souvent en modèle réutilisable.",
        "category": "productivity",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "low",
        "instructions": [
            "Identifiez un document que vous recréez régulièrement",
            "Extrayez la structure commune",
            "Créez un modèle avec des champs à compléter",
            "Sauvegardez-le dans un endroit facilement accessible"
        ],
        "is_premium": True,
        "icon": "file-plus"
    },
    {
        "action_id": "action_prod_035",
        "title": "Raccourci découverte",
        "description": "Découvrez 3 raccourcis ou fonctionnalités cachées de votre outil de travail principal.",
        "category": "productivity",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Choisissez l'outil que vous utilisez le plus",
            "Recherchez 'astuces cachées' ou 'raccourcis avancés'",
            "Testez 3 fonctionnalités que vous ne connaissiez pas",
            "Intégrez la plus utile dans votre routine"
        ],
        "is_premium": False,
        "icon": "zap"
    },
    {
        "action_id": "action_prod_036",
        "title": "Snippet de texte",
        "description": "Créez des raccourcis de texte pour vos phrases les plus fréquentes.",
        "category": "productivity",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "low",
        "instructions": [
            "Listez 5 phrases que vous tapez régulièrement",
            "Créez un raccourci texte pour chacune",
            "Configurez-les dans les paramètres de votre OS ou un outil dédié",
            "Testez chaque raccourci pour vérifier"
        ],
        "is_premium": False,
        "icon": "type"
    },

    # Focus & Energy (037-040)
    {
        "action_id": "action_prod_037",
        "title": "Rythme ultradien",
        "description": "Identifiez votre rythme naturel d'énergie pour planifier vos tâches au bon moment.",
        "category": "productivity",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Notez votre niveau d'énergie actuel (1-10)",
            "Repensez à vos pics d'énergie dans la journée",
            "Identifiez vos 2 créneaux de haute énergie",
            "Planifiez vos tâches les plus difficiles pendant ces créneaux"
        ],
        "is_premium": False,
        "icon": "activity"
    },
    {
        "action_id": "action_prod_038",
        "title": "Pause stratégique",
        "description": "Prenez une pause régénérante avec une technique prouvée pour restaurer votre concentration.",
        "category": "productivity",
        "duration_min": 5,
        "duration_max": 8,
        "energy_level": "low",
        "instructions": [
            "Éloignez-vous de votre écran",
            "Regardez par la fenêtre ou un point à plus de 6 mètres pendant 20 secondes",
            "Faites 5 respirations profondes",
            "Marchez 2 minutes avant de reprendre"
        ],
        "is_premium": True,
        "icon": "coffee"
    },
    {
        "action_id": "action_prod_039",
        "title": "Sieste flash",
        "description": "Faites une micro-sieste de 10 minutes pour recharger vos batteries cognitives.",
        "category": "productivity",
        "duration_min": 8,
        "duration_max": 12,
        "energy_level": "low",
        "instructions": [
            "Trouvez un endroit calme et confortable",
            "Réglez une alarme à 10 minutes",
            "Fermez les yeux et détendez vos muscles un par un",
            "Même si vous ne dormez pas, le repos est bénéfique",
            "Levez-vous doucement à l'alarme"
        ],
        "is_premium": False,
        "icon": "moon"
    },
    {
        "action_id": "action_prod_040",
        "title": "Power pose 2 min",
        "description": "Adoptez une posture de puissance pendant 2 minutes pour booster votre confiance.",
        "category": "productivity",
        "duration_min": 2,
        "duration_max": 4,
        "energy_level": "low",
        "instructions": [
            "Levez-vous et prenez de l'espace",
            "Adoptez une posture expansive : mains sur les hanches ou bras levés",
            "Maintenez la posture pendant 2 minutes",
            "Respirez profondément et ressentez la confiance"
        ],
        "is_premium": False,
        "icon": "star"
    },

    # --- PRODUCTIVITY / MEDIUM ENERGY (35) ---

    # GTD & Organization (041-044)
    {
        "action_id": "action_prod_041",
        "title": "Brain dump complet",
        "description": "Videz votre cerveau en écrivant absolument tout ce qui vous encombre l'esprit.",
        "category": "productivity",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Prenez une feuille blanche ou un document vide",
            "Écrivez TOUT ce qui vous vient en tête sans filtrer",
            "Continuez pendant 5 minutes sans pause",
            "Relisez et classez : à faire, à planifier, à oublier",
            "Transférez les actions dans votre système de tâches"
        ],
        "is_premium": False,
        "icon": "brain"
    },
    {
        "action_id": "action_prod_042",
        "title": "Système de classement",
        "description": "Créez ou améliorez votre système de classement de fichiers numériques.",
        "category": "productivity",
        "duration_min": 7,
        "duration_max": 12,
        "energy_level": "medium",
        "instructions": [
            "Évaluez votre système de classement actuel",
            "Identifiez les catégories manquantes",
            "Créez une arborescence de dossiers claire",
            "Déplacez 10 fichiers mal rangés dans le bon dossier"
        ],
        "is_premium": False,
        "icon": "folder-tree"
    },
    {
        "action_id": "action_prod_043",
        "title": "Purge des engagements",
        "description": "Identifiez les engagements que vous avez pris et qui ne sont plus alignés avec vos priorités.",
        "category": "productivity",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Listez tous vos engagements actuels (pro et perso)",
            "Évaluez chacun : est-il toujours aligné avec vos objectifs ?",
            "Identifiez ceux à abandonner ou déléguer",
            "Préparez un message poli pour vous désengager"
        ],
        "is_premium": True,
        "icon": "scissors"
    },
    {
        "action_id": "action_prod_044",
        "title": "Processus documenté",
        "description": "Documentez un processus que vous faites souvent pour pouvoir le déléguer.",
        "category": "productivity",
        "duration_min": 7,
        "duration_max": 12,
        "energy_level": "medium",
        "instructions": [
            "Choisissez un processus récurrent",
            "Listez chaque étape dans l'ordre chronologique",
            "Ajoutez les détails et les pièges à éviter",
            "Testez en suivant la documentation comme un novice"
        ],
        "is_premium": False,
        "icon": "file-text"
    },

    # Deep Work (045-047)
    {
        "action_id": "action_prod_045",
        "title": "Sprint focus 15 min",
        "description": "Plongez dans un sprint de concentration maximale de 15 minutes chrono.",
        "category": "productivity",
        "duration_min": 13,
        "duration_max": 15,
        "energy_level": "medium",
        "instructions": [
            "Définissez un livrable précis à produire",
            "Activez le mode 'Ne pas déranger' partout",
            "Lancez le minuteur et travaillez intensément",
            "À la fin, évaluez votre productivité sur 10",
            "Notez les interruptions que vous avez résistées"
        ],
        "is_premium": False,
        "icon": "flame"
    },
    {
        "action_id": "action_prod_046",
        "title": "Rituel de concentration",
        "description": "Créez un rituel personnel qui signale à votre cerveau de passer en mode focus.",
        "category": "productivity",
        "duration_min": 5,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Choisissez 3 actions qui composent votre rituel (musique, thé, rangement…)",
            "Exécutez-les dans le même ordre à chaque fois",
            "Enchaînez immédiatement avec du travail concentré",
            "Pratiquez ce rituel pendant une semaine pour l'ancrer"
        ],
        "is_premium": True,
        "icon": "coffee"
    },
    {
        "action_id": "action_prod_047",
        "title": "Batch processing",
        "description": "Regroupez des tâches similaires et traitez-les toutes d'un coup pour gagner du temps.",
        "category": "productivity",
        "duration_min": 10,
        "duration_max": 15,
        "energy_level": "medium",
        "instructions": [
            "Identifiez des tâches similaires dans votre liste",
            "Regroupez-les : emails, appels, rédaction, admin…",
            "Traitez un lot complet sans interruption",
            "Mesurez le temps gagné par rapport au traitement dispersé"
        ],
        "is_premium": True,
        "icon": "layers"
    },

    # Planning (048-050)
    {
        "action_id": "action_prod_048",
        "title": "Planification inversée",
        "description": "Planifiez un projet en partant de la deadline et en remontant vers aujourd'hui.",
        "category": "productivity",
        "duration_min": 7,
        "duration_max": 12,
        "energy_level": "medium",
        "instructions": [
            "Choisissez un projet avec une deadline",
            "Notez la date de fin et le livrable attendu",
            "Identifiez les étapes intermédiaires en remontant",
            "Placez chaque étape dans votre calendrier",
            "Vérifiez que c'est réaliste avec vos autres engagements"
        ],
        "is_premium": False,
        "icon": "calendar"
    },
    {
        "action_id": "action_prod_049",
        "title": "Analyse Pareto rapide",
        "description": "Identifiez les 20% de vos actions qui produisent 80% de vos résultats.",
        "category": "productivity",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Listez vos 10 activités principales de la semaine",
            "Évaluez l'impact de chacune sur vos objectifs",
            "Identifiez les 2-3 qui ont le plus d'impact",
            "Planifiez plus de temps pour ces activités à fort impact"
        ],
        "is_premium": False,
        "icon": "pie-chart"
    },
    {
        "action_id": "action_prod_050",
        "title": "Prémortem projet",
        "description": "Imaginez que votre projet a échoué et identifiez les causes pour les prévenir.",
        "category": "productivity",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Choisissez un projet en cours",
            "Imaginez que dans 3 mois, il a échoué",
            "Listez toutes les raisons possibles de cet échec",
            "Pour chaque risque, définissez une action préventive",
            "Intégrez ces actions dans votre plan"
        ],
        "is_premium": True,
        "icon": "alert-triangle"
    },

    # Communication (051-054)
    {
        "action_id": "action_prod_051",
        "title": "Email percutant",
        "description": "Rédigez un email important en appliquant la structure BLUF (Bottom Line Up Front).",
        "category": "productivity",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Identifiez le message essentiel de votre email",
            "Commencez par la conclusion ou la demande",
            "Ajoutez le contexte nécessaire en 2-3 phrases",
            "Terminez par un appel à l'action clair",
            "Relisez et supprimez tout ce qui est superflu"
        ],
        "is_premium": False,
        "icon": "mail"
    },
    {
        "action_id": "action_prod_052",
        "title": "Écoute active drill",
        "description": "Pratiquez l'écoute active en reformulant ce que dit votre interlocuteur.",
        "category": "productivity",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Lors de votre prochaine conversation, écoutez sans interrompre",
            "Reformulez ce que vous avez compris : 'Si je comprends bien…'",
            "Posez une question ouverte pour approfondir",
            "Notez les moments où vous vouliez couper la parole"
        ],
        "is_premium": False,
        "icon": "ear"
    },
    {
        "action_id": "action_prod_053",
        "title": "Pitch de projet",
        "description": "Préparez un pitch de 2 minutes pour convaincre quelqu'un de soutenir votre projet.",
        "category": "productivity",
        "duration_min": 7,
        "duration_max": 12,
        "energy_level": "medium",
        "instructions": [
            "Commencez par le problème que vous résolvez",
            "Présentez votre solution en une phrase",
            "Donnez un chiffre ou un fait marquant",
            "Terminez par ce que vous demandez à votre interlocuteur",
            "Répétez à voix haute en chronomètrant"
        ],
        "is_premium": False,
        "icon": "presentation"
    },
    {
        "action_id": "action_prod_054",
        "title": "Gestion de conflit",
        "description": "Préparez une conversation difficile avec la méthode DESC : Décrire, Exprimer, Spécifier, Conséquences.",
        "category": "productivity",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Décrivez la situation objectivement (faits)",
            "Exprimez ce que vous ressentez (en 'je')",
            "Spécifiez ce que vous souhaitez",
            "Indiquez les conséquences positives du changement",
            "Répétez votre approche mentalement"
        ],
        "is_premium": True,
        "icon": "handshake"
    },

    # Creativity (055-057)
    {
        "action_id": "action_prod_055",
        "title": "6 chapeaux de Bono",
        "description": "Analysez un problème sous 6 angles différents avec la méthode des chapeaux.",
        "category": "productivity",
        "duration_min": 7,
        "duration_max": 12,
        "energy_level": "medium",
        "instructions": [
            "Définissez votre problème clairement",
            "Blanc : quels sont les faits ? Jaune : les avantages ?",
            "Noir : les risques ? Rouge : que ressentez-vous ?",
            "Vert : quelles alternatives créatives ? Bleu : quelle décision ?",
            "Synthétisez en une recommandation"
        ],
        "is_premium": False,
        "icon": "lightbulb"
    },
    {
        "action_id": "action_prod_056",
        "title": "Idéation rapide",
        "description": "Générez 20 idées en 5 minutes sur un défi spécifique, sans filtre ni jugement.",
        "category": "productivity",
        "duration_min": 5,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Définissez le défi en une question 'Comment pourrions-nous…?'",
            "Lancez un minuteur de 5 minutes",
            "Écrivez 20 idées sans les juger ni les censurer",
            "Relisez et marquez les 3 plus prometteuses"
        ],
        "is_premium": False,
        "icon": "sparkles"
    },
    {
        "action_id": "action_prod_057",
        "title": "Analogie forcée",
        "description": "Résolvez un problème en le comparant à un domaine complètement différent.",
        "category": "productivity",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Définissez votre problème en une phrase",
            "Choisissez un domaine éloigné : cuisine, sport, nature…",
            "Décrivez comment ce domaine résout des problèmes similaires",
            "Transposez ces solutions à votre contexte",
            "Sélectionnez l'idée la plus applicable"
        ],
        "is_premium": True,
        "icon": "link-2"
    },

    # Digital & Systems (058-061)
    {
        "action_id": "action_prod_058",
        "title": "Boîte mail organisée",
        "description": "Créez des filtres et labels pour que votre boîte mail se trie automatiquement.",
        "category": "productivity",
        "duration_min": 7,
        "duration_max": 12,
        "energy_level": "medium",
        "instructions": [
            "Identifiez vos 5 types d'emails les plus fréquents",
            "Créez un label/dossier pour chaque type",
            "Configurez un filtre automatique pour chacun",
            "Testez avec les emails récents"
        ],
        "is_premium": False,
        "icon": "filter"
    },
    {
        "action_id": "action_prod_059",
        "title": "Dashboard personnel",
        "description": "Créez un tableau de bord personnel pour suivre vos métriques importantes.",
        "category": "productivity",
        "duration_min": 10,
        "duration_max": 15,
        "energy_level": "medium",
        "instructions": [
            "Identifiez 3-5 métriques clés de votre vie pro/perso",
            "Choisissez un outil : Notion, Excel, papier…",
            "Créez un dashboard avec ces métriques",
            "Planifiez une mise à jour hebdomadaire"
        ],
        "is_premium": True,
        "icon": "layout-dashboard"
    },
    {
        "action_id": "action_prod_060",
        "title": "Workflow optimisé",
        "description": "Cartographiez un workflow quotidien et trouvez les étapes à éliminer ou simplifier.",
        "category": "productivity",
        "duration_min": 7,
        "duration_max": 12,
        "energy_level": "medium",
        "instructions": [
            "Choisissez un processus que vous faites souvent",
            "Listez chaque étape du début à la fin",
            "Pour chaque étape, demandez : est-ce nécessaire ?",
            "Identifiez les goulots d'étranglement",
            "Réécrivez le processus optimisé"
        ],
        "is_premium": False,
        "icon": "workflow"
    },
    {
        "action_id": "action_prod_061",
        "title": "Désabonnement mass",
        "description": "Désabonnez-vous de toutes les newsletters que vous ne lisez jamais.",
        "category": "productivity",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Parcourez vos emails de la dernière semaine",
            "Identifiez les newsletters jamais ouvertes",
            "Désabonnez-vous de chacune (lien en bas de l'email)",
            "Gardez uniquement celles que vous lisez vraiment"
        ],
        "is_premium": False,
        "icon": "mail-minus"
    },

    # Habits (062-064)
    {
        "action_id": "action_prod_062",
        "title": "Routine matinale check",
        "description": "Évaluez et optimisez votre routine matinale pour mieux démarrer la journée.",
        "category": "productivity",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Notez votre routine matinale actuelle étape par étape",
            "Identifiez les pertes de temps (scrolling, hésitations…)",
            "Ajoutez un élément énergisant (mouvement, intention…)",
            "Chronométrez votre nouvelle routine demain matin"
        ],
        "is_premium": True,
        "icon": "sunrise"
    },
    {
        "action_id": "action_prod_063",
        "title": "Déclencheur de succès",
        "description": "Identifiez les conditions qui déclenchent votre meilleure productivité.",
        "category": "productivity",
        "duration_min": 5,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Rappelez-vous vos 3 meilleures journées productives",
            "Identifiez les points communs : lieu, heure, état d'esprit…",
            "Listez vos déclencheurs de productivité",
            "Planifiez comment recréer ces conditions régulièrement"
        ],
        "is_premium": False,
        "icon": "zap"
    },
    {
        "action_id": "action_prod_064",
        "title": "Règle des 5 secondes",
        "description": "Pratiquez la règle des 5 secondes de Mel Robbins pour vaincre la procrastination.",
        "category": "productivity",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "medium",
        "instructions": [
            "Identifiez une tâche que vous repoussez",
            "Comptez 5-4-3-2-1 et agissez immédiatement",
            "Faites au moins les 2 premières minutes de la tâche",
            "Notez comment vous vous sentez après avoir commencé"
        ],
        "is_premium": False,
        "icon": "rocket"
    },

    # Review (065-067)
    {
        "action_id": "action_prod_065",
        "title": "Audit temps 1 jour",
        "description": "Analysez comment vous avez réellement passé votre temps aujourd'hui.",
        "category": "productivity",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Listez vos activités d'aujourd'hui heure par heure",
            "Catégorisez : productif, nécessaire, distraction",
            "Calculez le pourcentage de temps réellement productif",
            "Identifiez le plus gros voleur de temps",
            "Planifiez comment le réduire demain"
        ],
        "is_premium": False,
        "icon": "clock"
    },
    {
        "action_id": "action_prod_066",
        "title": "Journaling productivité",
        "description": "Écrivez dans votre journal de productivité pour identifier vos patterns.",
        "category": "productivity",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Qu'avez-vous accompli aujourd'hui ?",
            "Qu'est-ce qui vous a empêché d'être plus productif ?",
            "Quel est votre niveau d'énergie actuel (1-10) ?",
            "Que ferez-vous différemment demain ?",
            "Quelle est votre intention pour demain ?"
        ],
        "is_premium": False,
        "icon": "notebook"
    },
    {
        "action_id": "action_prod_067",
        "title": "Bilan des objectifs",
        "description": "Faites le point sur vos objectifs du mois et ajustez votre trajectoire.",
        "category": "productivity",
        "duration_min": 7,
        "duration_max": 12,
        "energy_level": "medium",
        "instructions": [
            "Relisez vos objectifs du mois",
            "Évaluez votre avancement pour chacun (en %)",
            "Identifiez les obstacles rencontrés",
            "Ajustez vos objectifs si nécessaire",
            "Définissez les prochaines actions concrètes"
        ],
        "is_premium": True,
        "icon": "target"
    },

    # Focus & Energy (068-071)
    {
        "action_id": "action_prod_068",
        "title": "Liste anti-procrastination",
        "description": "Créez une liste de micro-tâches pour les moments de faible motivation.",
        "category": "productivity",
        "duration_min": 5,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Listez 10 tâches utiles qui prennent moins de 5 minutes",
            "Classez-les par niveau d'énergie requis",
            "Gardez cette liste accessible sur votre bureau",
            "La prochaine fois que vous procrastinez, piochez dans la liste"
        ],
        "is_premium": False,
        "icon": "list-checks"
    },
    {
        "action_id": "action_prod_069",
        "title": "Intention du jour",
        "description": "Définissez UNE intention claire qui guidera toutes vos décisions de la journée.",
        "category": "productivity",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "medium",
        "instructions": [
            "Réfléchissez à ce qui compte le plus aujourd'hui",
            "Formulez une intention en une phrase courte",
            "Écrivez-la et placez-la bien en vue",
            "Avant chaque décision, vérifiez si elle sert votre intention"
        ],
        "is_premium": False,
        "icon": "compass"
    },
    {
        "action_id": "action_prod_070",
        "title": "Musique de concentration",
        "description": "Créez une playlist de concentration personnalisée pour vos sessions de travail.",
        "category": "productivity",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Identifiez le type de musique qui vous aide à vous concentrer",
            "Sélectionnez 5-10 morceaux sans paroles",
            "Créez une playlist dédiée au travail",
            "Testez-la pendant votre prochaine session de focus"
        ],
        "is_premium": False,
        "icon": "music"
    },
    {
        "action_id": "action_prod_071",
        "title": "Technique Ivy Lee",
        "description": "Listez vos 6 tâches les plus importantes de demain, classées par priorité.",
        "category": "productivity",
        "duration_min": 5,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "En fin de journée, listez les 6 tâches les plus importantes de demain",
            "Classez-les par ordre de priorité stricte",
            "Demain, commencez par la tâche n°1 sans toucher aux autres",
            "Ne passez à la suivante que quand la précédente est finie"
        ],
        "is_premium": False,
        "icon": "list-ordered"
    },

    # Mixed medium (072-075)
    {
        "action_id": "action_prod_072",
        "title": "Délégation check",
        "description": "Identifiez 3 tâches que vous pourriez déléguer pour vous concentrer sur l'essentiel.",
        "category": "productivity",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Listez vos tâches de la semaine",
            "Identifiez celles que quelqu'un d'autre pourrait faire",
            "Pour chacune, identifiez la personne idéale",
            "Rédigez un brief clair pour la délégation"
        ],
        "is_premium": True,
        "icon": "share-2"
    },
    {
        "action_id": "action_prod_073",
        "title": "Checklist projet",
        "description": "Créez une checklist complète pour un projet en cours afin de ne rien oublier.",
        "category": "productivity",
        "duration_min": 7,
        "duration_max": 12,
        "energy_level": "medium",
        "instructions": [
            "Choisissez un projet en cours",
            "Listez TOUTES les étapes de A à Z",
            "Ajoutez les dépendances entre les étapes",
            "Vérifiez avec un collègue si rien ne manque"
        ],
        "is_premium": False,
        "icon": "clipboard-list"
    },
    {
        "action_id": "action_prod_074",
        "title": "Journée idéale design",
        "description": "Concevez votre journée idéale parfaitement structurée et comparez avec la réalité.",
        "category": "productivity",
        "duration_min": 7,
        "duration_max": 12,
        "energy_level": "medium",
        "instructions": [
            "Imaginez votre journée idéale heure par heure",
            "Incluez travail, repos, sport, relations, loisirs",
            "Comparez avec votre journée typique actuelle",
            "Identifiez 2 changements faisables cette semaine"
        ],
        "is_premium": True,
        "icon": "star"
    },
    {
        "action_id": "action_prod_075",
        "title": "Matrice impact/effort",
        "description": "Classez vos idées ou tâches par impact et effort pour prioriser efficacement.",
        "category": "productivity",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Dessinez un graphique : axe X = effort, axe Y = impact",
            "Placez chaque tâche ou idée sur le graphique",
            "Priorisez : fort impact + faible effort = quick wins",
            "Planifiez : fort impact + fort effort = projets stratégiques",
            "Éliminez : faible impact + fort effort"
        ],
        "is_premium": False,
        "icon": "scatter-chart"
    },

    # --- PRODUCTIVITY / HIGH ENERGY (25) ---

    # GTD & Deep Work (076-079)
    {
        "action_id": "action_prod_076",
        "title": "Revue mensuelle profonde",
        "description": "Faites un bilan complet de votre mois : réalisations, apprentissages et plan d'action.",
        "category": "productivity",
        "duration_min": 10,
        "duration_max": 15,
        "energy_level": "high",
        "instructions": [
            "Listez toutes vos réalisations du mois",
            "Identifiez les 3 plus grands apprentissages",
            "Évaluez vos objectifs : atteints, en cours, abandonnés",
            "Fixez 3 objectifs pour le mois prochain",
            "Définissez la première action pour chacun"
        ],
        "is_premium": False,
        "icon": "calendar-check"
    },
    {
        "action_id": "action_prod_077",
        "title": "Deep work marathon",
        "description": "Lancez une session de travail profond de 15 minutes avec préparation et débriefing.",
        "category": "productivity",
        "duration_min": 13,
        "duration_max": 15,
        "energy_level": "high",
        "instructions": [
            "Définissez un objectif clair et mesurable pour cette session",
            "Préparez tout votre matériel à portée de main",
            "Coupez TOUTES les sources de distraction",
            "Travaillez 15 minutes sans aucune pause",
            "Débrief : qu'avez-vous accompli ? Quel était votre flow ?"
        ],
        "is_premium": False,
        "icon": "flame"
    },
    {
        "action_id": "action_prod_078",
        "title": "Système GTD setup",
        "description": "Mettez en place ou réorganisez votre système GTD avec les 5 étapes clés.",
        "category": "productivity",
        "duration_min": 10,
        "duration_max": 15,
        "energy_level": "high",
        "instructions": [
            "Capturez : videz tout ce qui encombre votre esprit",
            "Clarifiez : pour chaque item, définissez l'action suivante",
            "Organisez : classez par projet et contexte",
            "Révisez : vérifiez que tout est à jour",
            "Engagez : choisissez votre prochaine action et commencez"
        ],
        "is_premium": True,
        "icon": "inbox"
    },
    {
        "action_id": "action_prod_079",
        "title": "Vision board digital",
        "description": "Créez un tableau de vision numérique pour visualiser vos objectifs du trimestre.",
        "category": "productivity",
        "duration_min": 10,
        "duration_max": 15,
        "energy_level": "high",
        "instructions": [
            "Listez vos 5 objectifs du trimestre",
            "Trouvez une image inspirante pour chacun",
            "Assemblez-les dans un document ou un fond d'écran",
            "Ajoutez une phrase motivante pour chaque objectif",
            "Placez-le comme fond d'écran ou dans un endroit visible"
        ],
        "is_premium": True,
        "icon": "image"
    },

    # Planning & Strategy (080-083)
    {
        "action_id": "action_prod_080",
        "title": "Plan 90 jours",
        "description": "Élaborez un plan d'action sur 90 jours avec des jalons clairs et mesurables.",
        "category": "productivity",
        "duration_min": 10,
        "duration_max": 15,
        "energy_level": "high",
        "instructions": [
            "Définissez votre objectif principal à 90 jours",
            "Découpez en 3 jalons mensuels",
            "Pour chaque jalon, listez les actions nécessaires",
            "Identifiez les ressources et le soutien nécessaires",
            "Planifiez un check-in hebdomadaire"
        ],
        "is_premium": False,
        "icon": "map"
    },
    {
        "action_id": "action_prod_081",
        "title": "Carte stratégique perso",
        "description": "Créez votre carte stratégique personnelle alignant vision, objectifs et actions.",
        "category": "productivity",
        "duration_min": 10,
        "duration_max": 15,
        "energy_level": "high",
        "instructions": [
            "Écrivez votre vision à 1 an en une phrase",
            "Identifiez les 3 domaines clés pour y arriver",
            "Pour chaque domaine, fixez un objectif mesurable",
            "Déclinez en actions mensuelles et hebdomadaires",
            "Affichez cette carte sur votre bureau"
        ],
        "is_premium": True,
        "icon": "compass"
    },
    {
        "action_id": "action_prod_082",
        "title": "Decision matrix",
        "description": "Prenez une décision difficile avec une matrice de décision pondérée.",
        "category": "productivity",
        "duration_min": 7,
        "duration_max": 12,
        "energy_level": "high",
        "instructions": [
            "Définissez la décision à prendre et les options",
            "Listez les critères importants et pondérez-les",
            "Notez chaque option sur chaque critère (1-10)",
            "Calculez le score pondéré de chaque option",
            "Vérifiez que le résultat vous semble juste intuitivement"
        ],
        "is_premium": False,
        "icon": "scale"
    },
    {
        "action_id": "action_prod_083",
        "title": "Audit compétences",
        "description": "Évaluez vos compétences actuelles et identifiez les lacunes à combler.",
        "category": "productivity",
        "duration_min": 10,
        "duration_max": 15,
        "energy_level": "high",
        "instructions": [
            "Listez les compétences requises pour votre objectif",
            "Auto-évaluez chaque compétence de 1 à 5",
            "Identifiez les 3 compétences les plus faibles",
            "Trouvez une ressource d'apprentissage pour chacune",
            "Planifiez du temps d'apprentissage cette semaine"
        ],
        "is_premium": False,
        "icon": "bar-chart"
    },

    # Communication (084-086)
    {
        "action_id": "action_prod_084",
        "title": "Présentation structurée",
        "description": "Préparez le plan d'une présentation percutante avec la structure Problème-Solution-Bénéfice.",
        "category": "productivity",
        "duration_min": 10,
        "duration_max": 15,
        "energy_level": "high",
        "instructions": [
            "Définissez votre audience et son besoin",
            "Structurez : accroche, problème, solution, bénéfices, appel à l'action",
            "Préparez un slide par section (max 5)",
            "Répétez à voix haute en chronomètrant",
            "Ajustez le timing et les transitions"
        ],
        "is_premium": False,
        "icon": "presentation"
    },
    {
        "action_id": "action_prod_085",
        "title": "Négociation simulée",
        "description": "Simulez une négociation en préparant vos arguments et anticipant les objections.",
        "category": "productivity",
        "duration_min": 7,
        "duration_max": 12,
        "energy_level": "high",
        "instructions": [
            "Choisissez une négociation à venir",
            "Listez vos arguments principaux et votre BATNA",
            "Anticipez les 3 objections les plus probables",
            "Préparez une réponse pour chaque objection",
            "Simulez la conversation à voix haute"
        ],
        "is_premium": True,
        "icon": "swords"
    },
    {
        "action_id": "action_prod_086",
        "title": "Rédaction persuasive",
        "description": "Rédigez un texte persuasif en utilisant les principes de Cialdini.",
        "category": "productivity",
        "duration_min": 10,
        "duration_max": 15,
        "energy_level": "high",
        "instructions": [
            "Choisissez un message à rendre persuasif",
            "Intégrez la réciprocité : offrez quelque chose d'abord",
            "Ajoutez la preuve sociale : d'autres l'ont fait",
            "Créez un sentiment d'urgence raisonnable",
            "Relisez et vérifiez que le ton reste authentique"
        ],
        "is_premium": False,
        "icon": "pen-tool"
    },

    # Creativity & Ideas (087-090)
    {
        "action_id": "action_prod_087",
        "title": "Design thinking sprint",
        "description": "Appliquez les 5 étapes du design thinking en mode accéléré sur un problème.",
        "category": "productivity",
        "duration_min": 10,
        "duration_max": 15,
        "energy_level": "high",
        "instructions": [
            "Empathie : mettez-vous à la place de l'utilisateur (2 min)",
            "Définition : reformulez le problème en une question (1 min)",
            "Idéation : générez 10 solutions (3 min)",
            "Prototype : dessinez la meilleure solution (3 min)",
            "Test : imaginez les retours et ajustez (2 min)"
        ],
        "is_premium": True,
        "icon": "lightbulb"
    },
    {
        "action_id": "action_prod_088",
        "title": "Création de système",
        "description": "Transformez une routine manuelle en un système reproductible et documenté.",
        "category": "productivity",
        "duration_min": 10,
        "duration_max": 15,
        "energy_level": "high",
        "instructions": [
            "Choisissez une tâche récurrente à systématiser",
            "Listez chaque étape avec précision",
            "Identifiez ce qui peut être automatisé",
            "Créez une checklist ou un template",
            "Testez le système et notez les ajustements nécessaires"
        ],
        "is_premium": False,
        "icon": "cog"
    },
    {
        "action_id": "action_prod_089",
        "title": "Storytelling business",
        "description": "Transformez des données ennuyeuses en une histoire captivante pour votre prochain rapport.",
        "category": "productivity",
        "duration_min": 10,
        "duration_max": 15,
        "energy_level": "high",
        "instructions": [
            "Identifiez le message clé de vos données",
            "Trouvez le conflit ou la tension dans l'histoire",
            "Structurez : situation initiale, défi, résolution",
            "Ajoutez des éléments visuels ou des analogies",
            "Pratiquez le récit à voix haute"
        ],
        "is_premium": False,
        "icon": "book-open"
    },
    {
        "action_id": "action_prod_090",
        "title": "Innovation challenge",
        "description": "Lancez-vous un défi d'innovation : trouvez 3 façons d'améliorer un processus familier.",
        "category": "productivity",
        "duration_min": 7,
        "duration_max": 12,
        "energy_level": "high",
        "instructions": [
            "Choisissez un processus que vous faites tous les jours",
            "Remettez en question chaque étape : pourquoi fait-on comme ça ?",
            "Imaginez 3 améliorations radicales",
            "Évaluez chacune en termes d'effort et d'impact",
            "Mettez en place la plus prometteuse"
        ],
        "is_premium": True,
        "icon": "rocket"
    },

    # Automation & Systems (091-094)
    {
        "action_id": "action_prod_091",
        "title": "Automatisation Zapier/IFTTT",
        "description": "Créez une automatisation qui connecte deux de vos outils pour gagner du temps.",
        "category": "productivity",
        "duration_min": 10,
        "duration_max": 15,
        "energy_level": "high",
        "instructions": [
            "Identifiez une action manuelle entre deux outils",
            "Ouvrez Zapier, IFTTT ou Make",
            "Créez un Zap : déclencheur → action",
            "Testez l'automatisation avec un exemple réel",
            "Activez et vérifiez qu'elle fonctionne"
        ],
        "is_premium": True,
        "icon": "zap"
    },
    {
        "action_id": "action_prod_092",
        "title": "Routine soirée optimale",
        "description": "Concevez une routine de fin de journée qui prépare efficacement le lendemain.",
        "category": "productivity",
        "duration_min": 7,
        "duration_max": 12,
        "energy_level": "high",
        "instructions": [
            "Définissez l'heure de fin de travail fixe",
            "Créez un rituel de clôture : revue, planification demain, rangement",
            "Ajoutez une activité de transition (marche, lecture…)",
            "Préparez tout pour le lendemain matin",
            "Testez cette routine pendant 5 jours"
        ],
        "is_premium": False,
        "icon": "sunset"
    },
    {
        "action_id": "action_prod_093",
        "title": "Knowledge base perso",
        "description": "Créez votre base de connaissances personnelle pour ne plus jamais réapprendre la même chose.",
        "category": "productivity",
        "duration_min": 10,
        "duration_max": 15,
        "energy_level": "high",
        "instructions": [
            "Choisissez un outil : Notion, Obsidian, Google Docs…",
            "Créez des catégories pour vos domaines de connaissance",
            "Migrez 5 notes ou apprentissages récents",
            "Ajoutez des tags et des liens entre les notes",
            "Planifiez l'habitude d'ajouter une note par jour"
        ],
        "is_premium": False,
        "icon": "database"
    },
    {
        "action_id": "action_prod_094",
        "title": "Audit outils tech",
        "description": "Auditez votre stack d'outils pour éliminer les doublons et les abonnements inutiles.",
        "category": "productivity",
        "duration_min": 10,
        "duration_max": 15,
        "energy_level": "high",
        "instructions": [
            "Listez tous les outils et abonnements que vous payez",
            "Identifiez les doublons et les outils sous-utilisés",
            "Calculez le coût total mensuel",
            "Résiliez les abonnements inutiles",
            "Identifiez un outil manquant qui vous ferait gagner du temps"
        ],
        "is_premium": True,
        "icon": "wrench"
    },

    # Focus & Energy (095-098)
    {
        "action_id": "action_prod_095",
        "title": "Journée thématique",
        "description": "Planifiez une journée entière autour d'un seul thème pour une productivité maximale.",
        "category": "productivity",
        "duration_min": 7,
        "duration_max": 12,
        "energy_level": "high",
        "instructions": [
            "Choisissez un thème : création, admin, stratégie, apprentissage…",
            "Regroupez toutes les tâches de ce thème",
            "Bloquez une journée entière dans votre agenda",
            "Préparez tout le matériel nécessaire la veille",
            "Protégez cette journée de toute interruption"
        ],
        "is_premium": False,
        "icon": "calendar"
    },
    {
        "action_id": "action_prod_096",
        "title": "Sprint productivité 3x5",
        "description": "Faites 3 sprints de 5 minutes sur 3 tâches différentes pour un maximum d'élan.",
        "category": "productivity",
        "duration_min": 13,
        "duration_max": 15,
        "energy_level": "high",
        "instructions": [
            "Choisissez 3 tâches courtes et différentes",
            "Sprint 1 : travaillez 5 minutes sur la tâche 1",
            "Sprint 2 : enchaînez 5 minutes sur la tâche 2",
            "Sprint 3 : terminez 5 minutes sur la tâche 3",
            "Notez votre progression sur chaque tâche"
        ],
        "is_premium": False,
        "icon": "timer"
    },
    {
        "action_id": "action_prod_097",
        "title": "Challenge zéro distraction",
        "description": "Tentez un record personnel de concentration sans aucune distraction.",
        "category": "productivity",
        "duration_min": 10,
        "duration_max": 15,
        "energy_level": "high",
        "instructions": [
            "Mettez votre téléphone dans une autre pièce",
            "Fermez toutes les applications sauf celle de travail",
            "Lancez un chronomètre et travaillez",
            "Notez l'heure exacte si vous vous laissez distraire",
            "Essayez de battre votre record demain"
        ],
        "is_premium": False,
        "icon": "shield"
    },
    {
        "action_id": "action_prod_098",
        "title": "Énergie mapping",
        "description": "Cartographiez votre énergie sur 24h pour optimiser l'ordre de vos activités.",
        "category": "productivity",
        "duration_min": 7,
        "duration_max": 12,
        "energy_level": "high",
        "instructions": [
            "Dessinez un graphique : X = heures (6h-22h), Y = énergie (1-10)",
            "Tracez votre courbe d'énergie typique",
            "Identifiez vos pics et creux d'énergie",
            "Alignez tâches créatives avec les pics, admin avec les creux",
            "Réorganisez votre planning en conséquence"
        ],
        "is_premium": False,
        "icon": "activity"
    },

    # Mixed (099-100)
    {
        "action_id": "action_prod_099",
        "title": "Mentorat inversé",
        "description": "Identifiez quelque chose qu'un junior pourrait vous apprendre et demandez-lui.",
        "category": "productivity",
        "duration_min": 7,
        "duration_max": 12,
        "energy_level": "high",
        "instructions": [
            "Identifiez un domaine où un collègue plus jeune excelle",
            "Préparez une question spécifique à lui poser",
            "Écoutez activement sa réponse sans juger",
            "Notez ce que vous avez appris",
            "Remerciez-le et proposez un échange de compétences"
        ],
        "is_premium": True,
        "icon": "users"
    },
    {
        "action_id": "action_prod_100",
        "title": "Lettre à soi futur",
        "description": "Écrivez une lettre à votre vous de dans 6 mois avec vos objectifs et espoirs.",
        "category": "productivity",
        "duration_min": 7,
        "duration_max": 12,
        "energy_level": "high",
        "instructions": [
            "Décrivez votre situation actuelle",
            "Listez ce que vous espérez avoir accompli dans 6 mois",
            "Écrivez des encouragements à votre futur vous",
            "Programmez un rappel pour relire dans 6 mois",
            "Scellez la lettre (physiquement ou numériquement)"
        ],
        "is_premium": False,
        "icon": "mail"
    },

    # =========================================================================
    # WELL-BEING (100 actions) — action_well_001 to action_well_100
    # Low energy: 001-040 | Medium energy: 041-075 | High energy: 076-100
    # =========================================================================

    # --- WELL-BEING / LOW ENERGY (40) ---

    # Breathing (001-005)
    {
        "action_id": "action_well_001",
        "title": "Respiration 4-7-8",
        "description": "Pratiquez la technique 4-7-8 pour calmer votre système nerveux en quelques minutes.",
        "category": "well_being",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Asseyez-vous confortablement et fermez les yeux",
            "Inspirez par le nez pendant 4 secondes",
            "Retenez votre souffle pendant 7 secondes",
            "Expirez par la bouche pendant 8 secondes",
            "Répétez 4 cycles complets"
        ],
        "is_premium": False,
        "icon": "wind"
    },
    {
        "action_id": "action_well_002",
        "title": "Respiration carrée",
        "description": "Utilisez le box breathing pour retrouver un calme profond en 4 minutes.",
        "category": "well_being",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Inspirez pendant 4 secondes",
            "Retenez pendant 4 secondes",
            "Expirez pendant 4 secondes",
            "Retenez poumons vides pendant 4 secondes",
            "Répétez 6 cycles"
        ],
        "is_premium": False,
        "icon": "square"
    },
    {
        "action_id": "action_well_003",
        "title": "Wim Hof débutant",
        "description": "Découvrez la technique respiratoire Wim Hof avec une version simplifiée pour débutants.",
        "category": "well_being",
        "duration_min": 5,
        "duration_max": 8,
        "energy_level": "low",
        "instructions": [
            "Allongez-vous confortablement",
            "Faites 20 respirations profondes et rapides (inspire max, expire relâché)",
            "Après la 20e expiration, retenez votre souffle aussi longtemps que possible",
            "Inspirez profondément et retenez 15 secondes",
            "Répétez 2 cycles"
        ],
        "is_premium": True,
        "icon": "wind"
    },
    {
        "action_id": "action_well_004",
        "title": "Cohérence cardiaque",
        "description": "Synchronisez votre respiration à 6 cycles par minute pour harmoniser votre rythme cardiaque.",
        "category": "well_being",
        "duration_min": 5,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Asseyez-vous et posez les mains sur vos genoux",
            "Inspirez pendant 5 secondes",
            "Expirez pendant 5 secondes",
            "Maintenez ce rythme pendant 5 minutes",
            "Ressentez votre cœur se calmer progressivement"
        ],
        "is_premium": False,
        "icon": "heart"
    },
    {
        "action_id": "action_well_005",
        "title": "Narine alternée",
        "description": "Pratiquez la respiration alternée pour équilibrer vos deux hémisphères cérébraux.",
        "category": "well_being",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Bouchez la narine droite avec le pouce",
            "Inspirez par la narine gauche pendant 4 secondes",
            "Bouchez les deux narines et retenez 4 secondes",
            "Libérez la narine droite et expirez 4 secondes",
            "Alternez et répétez 8 cycles"
        ],
        "is_premium": False,
        "icon": "wind"
    },

    # Meditation (006-010)
    {
        "action_id": "action_well_006",
        "title": "Body scan express",
        "description": "Scannez votre corps de la tête aux pieds pour relâcher les tensions cachées.",
        "category": "well_being",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "low",
        "instructions": [
            "Allongez-vous ou asseyez-vous confortablement",
            "Portez attention au sommet de votre crâne",
            "Descendez lentement : front, mâchoire, cou, épaules…",
            "À chaque zone, relâchez consciemment la tension",
            "Terminez par les pieds et ressentez votre corps entier"
        ],
        "is_premium": True,
        "icon": "scan"
    },
    {
        "action_id": "action_well_007",
        "title": "Bienveillance aimante",
        "description": "Pratiquez la méditation de bienveillance aimante (metta) pour cultiver la compassion.",
        "category": "well_being",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "low",
        "instructions": [
            "Fermez les yeux et respirez calmement",
            "Envoyez de la bienveillance à vous-même : 'Que je sois heureux, en paix'",
            "Étendez à un proche : 'Que tu sois heureux, en paix'",
            "Étendez à une personne neutre, puis à une personne difficile",
            "Terminez en envoyant de la bienveillance à tous les êtres"
        ],
        "is_premium": True,
        "icon": "heart"
    },
    {
        "action_id": "action_well_008",
        "title": "Visualisation apaisante",
        "description": "Visualisez un lieu de paix intérieur pour vous ressourcer mentalement.",
        "category": "well_being",
        "duration_min": 5,
        "duration_max": 8,
        "energy_level": "low",
        "instructions": [
            "Fermez les yeux et prenez 3 respirations profondes",
            "Imaginez un lieu où vous vous sentez parfaitement en paix",
            "Ajoutez les détails sensoriels : sons, odeurs, textures",
            "Restez dans ce lieu mental pendant 3-5 minutes",
            "Revenez doucement en ouvrant les yeux"
        ],
        "is_premium": False,
        "icon": "image"
    },
    {
        "action_id": "action_well_009",
        "title": "Mantra apaisant",
        "description": "Répétez un mantra personnel pour ancrer votre esprit dans le moment présent.",
        "category": "well_being",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Choisissez un mantra : 'Je suis calme', 'Tout va bien', ou un mot simple",
            "Asseyez-vous et fermez les yeux",
            "Répétez le mantra silencieusement à chaque expiration",
            "Si votre esprit divague, revenez doucement au mantra"
        ],
        "is_premium": False,
        "icon": "repeat"
    },
    {
        "action_id": "action_well_010",
        "title": "Méditation minute",
        "description": "Faites une micro-méditation d'une minute pour retrouver votre centre instantanément.",
        "category": "well_being",
        "duration_min": 2,
        "duration_max": 3,
        "energy_level": "low",
        "instructions": [
            "Arrêtez ce que vous faites",
            "Fermez les yeux et prenez une grande inspiration",
            "Observez 3 sensations dans votre corps",
            "Écoutez 3 sons autour de vous",
            "Ouvrez les yeux avec une attention renouvelée"
        ],
        "is_premium": False,
        "icon": "timer"
    },

    # Movement (011-014)
    {
        "action_id": "action_well_011",
        "title": "Yoga du bureau",
        "description": "Faites 5 postures de yoga adaptées à votre bureau pour soulager les tensions.",
        "category": "well_being",
        "duration_min": 5,
        "duration_max": 8,
        "energy_level": "low",
        "instructions": [
            "Étirement du cou : inclinez la tête de chaque côté (30s)",
            "Torsion assise : tournez le buste à droite puis à gauche (30s)",
            "Étirement des poignets : tendez le bras et pliez la main (30s)",
            "Ouverture de poitrine : entrelacez les doigts derrière le dos",
            "Flexion avant assise : penchez-vous vers l'avant (30s)"
        ],
        "is_premium": False,
        "icon": "stretch-horizontal"
    },
    {
        "action_id": "action_well_012",
        "title": "Stretching express",
        "description": "Étirez les 5 zones les plus tendues quand on travaille assis toute la journée.",
        "category": "well_being",
        "duration_min": 4,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Étirez le cou en inclinant doucement la tête de chaque côté",
            "Étirez les épaules en croisant un bras devant vous",
            "Étirez le dos en arrondissant puis en cambrant",
            "Étirez les hanches avec une fente basse",
            "Étirez les mollets contre un mur"
        ],
        "is_premium": False,
        "icon": "move"
    },
    {
        "action_id": "action_well_013",
        "title": "Exercice d'équilibre",
        "description": "Améliorez votre équilibre et votre concentration avec des postures simples.",
        "category": "well_being",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Tenez-vous debout les pieds joints",
            "Levez un pied et tenez 30 secondes",
            "Changez de pied",
            "Fermez les yeux et réessayez (plus difficile)",
            "Notez l'amélioration au fil des jours"
        ],
        "is_premium": True,
        "icon": "person-standing"
    },
    {
        "action_id": "action_well_014",
        "title": "Détente de la nuque",
        "description": "Libérez les tensions de votre nuque avec une série de mouvements doux.",
        "category": "well_being",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Inclinez la tête vers la droite, maintenez 15 secondes",
            "Inclinez vers la gauche, maintenez 15 secondes",
            "Rentrez le menton vers la poitrine, maintenez 15 secondes",
            "Faites 5 rotations lentes dans chaque sens"
        ],
        "is_premium": False,
        "icon": "circle"
    },

    # Mindfulness (015-018)
    {
        "action_id": "action_well_015",
        "title": "Manger en conscience",
        "description": "Transformez votre prochain encas en expérience de pleine conscience sensorielle.",
        "category": "well_being",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "low",
        "instructions": [
            "Choisissez un aliment (fruit, chocolat, noix…)",
            "Observez-le comme si c'était la première fois",
            "Sentez son odeur avant de le porter à votre bouche",
            "Mâchez très lentement en notant chaque saveur",
            "Remarquez le moment exact où le goût change"
        ],
        "is_premium": False,
        "icon": "apple"
    },
    {
        "action_id": "action_well_016",
        "title": "Éveil sensoriel",
        "description": "Activez vos 5 sens pour revenir pleinement dans le moment présent.",
        "category": "well_being",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Nommez 5 choses que vous voyez autour de vous",
            "Identifiez 4 choses que vous pouvez toucher",
            "Écoutez 3 sons distincts dans votre environnement",
            "Remarquez 2 odeurs autour de vous",
            "Identifiez 1 goût dans votre bouche"
        ],
        "is_premium": False,
        "icon": "eye"
    },
    {
        "action_id": "action_well_017",
        "title": "Ancrage présent",
        "description": "Utilisez vos pieds comme point d'ancrage pour revenir dans l'instant présent.",
        "category": "well_being",
        "duration_min": 2,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Posez vos pieds bien à plat sur le sol",
            "Ressentez le contact avec le sol (chaussures ou pieds nus)",
            "Imaginez des racines qui partent de vos pieds vers la terre",
            "Respirez profondément en maintenant cette sensation"
        ],
        "is_premium": False,
        "icon": "anchor"
    },
    {
        "action_id": "action_well_018",
        "title": "Méditation sonore",
        "description": "Fermez les yeux et explorez tous les sons autour de vous sans les juger.",
        "category": "well_being",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Fermez les yeux et écoutez",
            "Identifiez les sons les plus lointains",
            "Rapprochez-vous progressivement des sons proches",
            "Écoutez le son de votre propre respiration",
            "Ouvrez les yeux doucement en gardant cette attention"
        ],
        "is_premium": True,
        "icon": "volume-2"
    },

    # Emotional (019-022)
    {
        "action_id": "action_well_019",
        "title": "Journal émotionnel",
        "description": "Écrivez pendant 5 minutes ce que vous ressentez sans filtrer ni juger.",
        "category": "well_being",
        "duration_min": 5,
        "duration_max": 8,
        "energy_level": "low",
        "instructions": [
            "Prenez un carnet ou ouvrez une note",
            "Écrivez comment vous vous sentez en ce moment",
            "Décrivez les sensations physiques associées",
            "Ne cherchez pas de solution, juste l'expression",
            "Relisez avec bienveillance"
        ],
        "is_premium": False,
        "icon": "notebook"
    },
    {
        "action_id": "action_well_020",
        "title": "Lettre de compassion",
        "description": "Écrivez-vous une lettre de compassion comme vous le feriez pour un ami cher.",
        "category": "well_being",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "low",
        "instructions": [
            "Identifiez une situation qui vous fait souffrir",
            "Imaginez qu'un ami traverse la même chose",
            "Écrivez-lui une lettre bienveillante et encourageante",
            "Relisez la lettre comme si elle vous était adressée"
        ],
        "is_premium": True,
        "icon": "heart"
    },
    {
        "action_id": "action_well_021",
        "title": "Nommer ses émotions",
        "description": "Identifiez et nommez précisément vos émotions actuelles pour mieux les gérer.",
        "category": "well_being",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Fermez les yeux et scannez ce que vous ressentez",
            "Trouvez le mot exact : anxieux, nostalgique, enthousiaste…",
            "Localisez l'émotion dans votre corps",
            "Dites intérieurement : 'Je ressens de la [émotion] et c'est ok'"
        ],
        "is_premium": False,
        "icon": "smile"
    },
    {
        "action_id": "action_well_022",
        "title": "Sourire intérieur",
        "description": "Pratiquez la technique taoïste du sourire intérieur pour détendre chaque organe.",
        "category": "well_being",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Fermez les yeux et esquissez un léger sourire",
            "Imaginez ce sourire descendre vers vos yeux, votre gorge",
            "Envoyez ce sourire à votre cœur, vos poumons, votre ventre",
            "Ressentez la détente qui se propage dans tout votre corps"
        ],
        "is_premium": False,
        "icon": "smile"
    },

    # Social (023-026)
    {
        "action_id": "action_well_023",
        "title": "Message de gratitude",
        "description": "Envoyez un message de remerciement sincère à quelqu'un qui compte pour vous.",
        "category": "well_being",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Pensez à une personne qui vous a aidé récemment",
            "Rédigez un message spécifique : pas juste 'merci' mais pourquoi",
            "Envoyez-le maintenant (SMS, email, vocale…)",
            "Savourez le sentiment positif que cela génère"
        ],
        "is_premium": False,
        "icon": "send"
    },
    {
        "action_id": "action_well_024",
        "title": "Compliment sincère",
        "description": "Faites un compliment sincère et spécifique à la prochaine personne que vous croisez.",
        "category": "well_being",
        "duration_min": 2,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Pensez à quelqu'un dans votre entourage",
            "Identifiez une qualité ou une action que vous appréciez",
            "Formulez un compliment spécifique et sincère",
            "Offrez-le directement, sans attendre quelque chose en retour"
        ],
        "is_premium": True,
        "icon": "heart-handshake"
    },
    {
        "action_id": "action_well_025",
        "title": "Écoute profonde",
        "description": "Lors de votre prochaine interaction, pratiquez l'écoute sans penser à votre réponse.",
        "category": "well_being",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "low",
        "instructions": [
            "Choisissez votre prochaine conversation",
            "Écoutez sans préparer votre réponse mentalement",
            "Observez le langage corporel de l'autre",
            "Posez une question qui montre que vous avez vraiment écouté"
        ],
        "is_premium": False,
        "icon": "ear"
    },
    {
        "action_id": "action_well_026",
        "title": "Pardon silencieux",
        "description": "Pratiquez le pardon intérieur pour vous libérer d'une rancœur qui vous pèse.",
        "category": "well_being",
        "duration_min": 5,
        "duration_max": 8,
        "energy_level": "low",
        "instructions": [
            "Identifiez une situation ou une personne qui vous cause de la rancœur",
            "Reconnaissez la douleur que cela vous cause",
            "Dites intérieurement : 'Je choisis de lâcher prise pour me libérer'",
            "Respirez profondément et imaginez cette charge s'alléger"
        ],
        "is_premium": True,
        "icon": "heart"
    },

    # Nature & Senses (027-030)
    {
        "action_id": "action_well_027",
        "title": "Observation nature",
        "description": "Observez un élément naturel pendant 3 minutes avec une attention totale.",
        "category": "well_being",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Trouvez un élément naturel : arbre, nuage, plante, ciel…",
            "Observez-le pendant 3 minutes sans penser à rien d'autre",
            "Notez les détails que vous n'aviez jamais remarqués",
            "Ressentez la connexion avec la nature"
        ],
        "is_premium": False,
        "icon": "tree-pine"
    },
    {
        "action_id": "action_well_028",
        "title": "Contemplation des nuages",
        "description": "Allongez-vous et observez les nuages pendant 5 minutes pour apaiser votre esprit.",
        "category": "well_being",
        "duration_min": 5,
        "duration_max": 8,
        "energy_level": "low",
        "instructions": [
            "Trouvez un endroit où vous pouvez voir le ciel",
            "Allongez-vous ou installez-vous confortablement",
            "Observez les nuages sans chercher de formes",
            "Laissez vos pensées passer comme les nuages"
        ],
        "is_premium": False,
        "icon": "cloud"
    },
    {
        "action_id": "action_well_029",
        "title": "Grounding pieds nus",
        "description": "Marchez pieds nus sur un sol naturel pour vous reconnecter à la terre.",
        "category": "well_being",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Trouvez une surface naturelle : herbe, sable, terre",
            "Retirez vos chaussures et marchez lentement",
            "Ressentez chaque texture sous vos pieds",
            "Respirez profondément en appréciant cette connexion"
        ],
        "is_premium": False,
        "icon": "footprints"
    },
    {
        "action_id": "action_well_030",
        "title": "Pause aromathérapie",
        "description": "Utilisez une huile essentielle ou un parfum naturel pour stimuler votre bien-être.",
        "category": "well_being",
        "duration_min": 2,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Choisissez une huile essentielle ou un parfum naturel",
            "Déposez une goutte sur vos poignets ou un mouchoir",
            "Inspirez profondément 5 fois en fermant les yeux",
            "Associez ce parfum à une intention positive"
        ],
        "is_premium": False,
        "icon": "flower-2"
    },

    # Sleep & Recovery (031-034)
    {
        "action_id": "action_well_031",
        "title": "Relaxation progressive",
        "description": "Relâchez chaque groupe musculaire un par un pour atteindre une détente totale.",
        "category": "well_being",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "low",
        "instructions": [
            "Allongez-vous confortablement",
            "Contractez les pieds pendant 5 secondes, puis relâchez",
            "Remontez : mollets, cuisses, ventre, mains, bras, épaules, visage",
            "Pour chaque groupe, contractez 5s puis relâchez 10s",
            "Terminez en ressentant la détente totale"
        ],
        "is_premium": False,
        "icon": "bed"
    },
    {
        "action_id": "action_well_032",
        "title": "Hygiène sommeil check",
        "description": "Évaluez vos habitudes de sommeil et identifiez un point d'amélioration.",
        "category": "well_being",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Notez votre heure de coucher et de lever cette semaine",
            "Évaluez : écrans avant le coucher ? Caféine après 14h ?",
            "Identifiez le facteur qui nuit le plus à votre sommeil",
            "Choisissez une amélioration à tester cette semaine"
        ],
        "is_premium": False,
        "icon": "moon"
    },
    {
        "action_id": "action_well_033",
        "title": "Coucher de soleil digital",
        "description": "Instaurez un rituel de déconnexion digitale 30 minutes avant le coucher.",
        "category": "well_being",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Définissez votre heure de coucher idéale",
            "30 minutes avant, éteignez tous les écrans",
            "Remplacez par une activité apaisante : lecture, étirements, journal",
            "Activez le mode nuit sur tous vos appareils dès 20h"
        ],
        "is_premium": True,
        "icon": "sunset"
    },
    {
        "action_id": "action_well_034",
        "title": "Exercice du bâillement",
        "description": "Provoquez des bâillements volontaires pour détendre votre mâchoire et votre cerveau.",
        "category": "well_being",
        "duration_min": 2,
        "duration_max": 4,
        "energy_level": "low",
        "instructions": [
            "Ouvrez grand la bouche comme pour bâiller",
            "Feignez un bâillement même si ce n'est pas naturel",
            "Après 2-3 faux bâillements, les vrais suivront",
            "Bâillez 5-10 fois en étirant votre mâchoire",
            "Ressentez la détente dans votre visage et votre tête"
        ],
        "is_premium": False,
        "icon": "moon"
    },

    # Nutrition (035-037)
    {
        "action_id": "action_well_035",
        "title": "Check hydratation",
        "description": "Évaluez votre hydratation et mettez en place un système pour boire plus d'eau.",
        "category": "well_being",
        "duration_min": 2,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Comptez combien de verres d'eau vous avez bus aujourd'hui",
            "L'objectif est 8 verres (2L) par jour",
            "Remplissez un verre ou une bouteille maintenant",
            "Programmez un rappel toutes les heures pour boire"
        ],
        "is_premium": False,
        "icon": "droplets"
    },
    {
        "action_id": "action_well_036",
        "title": "Snack en conscience",
        "description": "Prenez un encas sain en pleine conscience pour nourrir corps et esprit.",
        "category": "well_being",
        "duration_min": 5,
        "duration_max": 8,
        "energy_level": "low",
        "instructions": [
            "Choisissez un encas sain : fruits, noix, légumes…",
            "Avant de manger, évaluez votre faim réelle (1-10)",
            "Mangez lentement en posant votre aliment entre chaque bouchée",
            "Arrêtez quand vous n'avez plus faim, pas quand c'est fini"
        ],
        "is_premium": False,
        "icon": "apple"
    },
    {
        "action_id": "action_well_037",
        "title": "Vitamine du jour",
        "description": "Découvrez une vitamine ou un nutriment essentiel et identifiez comment l'intégrer à votre alimentation.",
        "category": "well_being",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Choisissez : vitamine D, magnésium, omega-3, zinc…",
            "Lisez ses bienfaits principaux",
            "Identifiez 3 aliments qui en contiennent",
            "Prévoyez d'en intégrer un dans votre prochain repas"
        ],
        "is_premium": True,
        "icon": "pill"
    },

    # Joy & Play (038-040)
    {
        "action_id": "action_well_038",
        "title": "Gribouillage libre",
        "description": "Gribouuillez librement pendant 3 minutes pour libérer votre esprit des tensions.",
        "category": "well_being",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Prenez un stylo et une feuille",
            "Dessinez sans réfléchir : lignes, formes, spirales…",
            "Ne cherchez pas à créer quelque chose de beau",
            "Laissez votre main bouger librement pendant 3 minutes"
        ],
        "is_premium": False,
        "icon": "pencil"
    },
    {
        "action_id": "action_well_039",
        "title": "Fredonnement apaisant",
        "description": "Fredonnez une mélodie pendant 3 minutes pour activer votre nerf vague et vous apaiser.",
        "category": "well_being",
        "duration_min": 2,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Choisissez une mélodie que vous aimez",
            "Fredonnez bouche fermée pendant 3 minutes",
            "Ressentez les vibrations dans votre poitrine et votre crâne",
            "Variez la hauteur des sons et observez les sensations"
        ],
        "is_premium": False,
        "icon": "music"
    },
    {
        "action_id": "action_well_040",
        "title": "Micro-pause joyeuse",
        "description": "Faites quelque chose qui vous fait sourire pendant 2 minutes : photo drôle, souvenir heureux.",
        "category": "well_being",
        "duration_min": 2,
        "duration_max": 4,
        "energy_level": "low",
        "instructions": [
            "Pensez à un souvenir qui vous fait sourire",
            "Fermez les yeux et revivez ce moment en détail",
            "Ou regardez une photo qui vous rend heureux",
            "Laissez le sourire se former naturellement"
        ],
        "is_premium": False,
        "icon": "smile"
    },

    # --- WELL-BEING / MEDIUM ENERGY (35) ---

    # Breathing & Meditation (041-045)
    {
        "action_id": "action_well_041",
        "title": "Respiration énergisante",
        "description": "Pratiquez une respiration dynamisante pour booster votre énergie en 3 minutes.",
        "category": "well_being",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "medium",
        "instructions": [
            "Asseyez-vous le dos droit",
            "Inspirez rapidement par le nez (1 seconde)",
            "Expirez rapidement par le nez (1 seconde)",
            "Faites 20 cycles rapides puis 1 inspiration profonde",
            "Retenez 10 secondes et relâchez. Répétez 3 fois"
        ],
        "is_premium": False,
        "icon": "wind"
    },
    {
        "action_id": "action_well_042",
        "title": "Méditation marchée",
        "description": "Méditez en marchant lentement avec une attention totale sur chaque pas.",
        "category": "well_being",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Trouvez un espace de 5-10 mètres pour marcher",
            "Marchez très lentement en observant chaque mouvement",
            "Ressentez le contact de chaque pied avec le sol",
            "Si votre esprit divague, ramenez l'attention aux pieds",
            "Faites 5-10 allers-retours"
        ],
        "is_premium": True,
        "icon": "footprints"
    },
    {
        "action_id": "action_well_043",
        "title": "Scan des émotions",
        "description": "Scannez et cartographiez vos émotions actuelles pour mieux vous comprendre.",
        "category": "well_being",
        "duration_min": 5,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Fermez les yeux et respirez 3 fois",
            "Identifiez l'émotion dominante",
            "Localisez-la dans votre corps (gorge serrée, ventre noué…)",
            "Observez-la sans essayer de la changer",
            "Notez comment elle évolue juste en l'observant"
        ],
        "is_premium": False,
        "icon": "heart"
    },
    {
        "action_id": "action_well_044",
        "title": "Gratitude profonde",
        "description": "Pratiquez une gratitude approfondie en explorant vraiment pourquoi vous êtes reconnaissant.",
        "category": "well_being",
        "duration_min": 5,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Choisissez une personne ou une chose pour laquelle vous êtes reconnaissant",
            "Écrivez 5 raisons spécifiques de cette gratitude",
            "Pour chaque raison, décrivez l'impact sur votre vie",
            "Ressentez physiquement la chaleur de cette reconnaissance"
        ],
        "is_premium": False,
        "icon": "heart"
    },
    {
        "action_id": "action_well_045",
        "title": "Respiration 3 étages",
        "description": "Respirez en remplissant successivement le ventre, les côtes et la poitrine.",
        "category": "well_being",
        "duration_min": 4,
        "duration_max": 7,
        "energy_level": "medium",
        "instructions": [
            "Posez une main sur le ventre, l'autre sur la poitrine",
            "Inspirez d'abord dans le ventre (main du bas se soulève)",
            "Continuez en remplissant les côtes latéralement",
            "Terminez en gonflant la poitrine (main du haut se soulève)",
            "Expirez dans l'ordre inverse. Répétez 8 cycles"
        ],
        "is_premium": True,
        "icon": "wind"
    },

    # Movement (046-050)
    {
        "action_id": "action_well_046",
        "title": "Micro-workout 5 min",
        "description": "Faites un mini-entraînement de 5 minutes pour réveiller votre corps et votre esprit.",
        "category": "well_being",
        "duration_min": 5,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "20 secondes de montées de genoux",
            "20 secondes de squats",
            "20 secondes de pompes (ou pompes murales)",
            "20 secondes de planche",
            "Répétez 3 cycles avec 10 secondes de repos entre chaque"
        ],
        "is_premium": False,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_well_047",
        "title": "Salutation au soleil",
        "description": "Enchaînez une salutation au soleil complète pour dynamiser votre corps et votre esprit.",
        "category": "well_being",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Debout, bras le long du corps, inspirez",
            "Bras au ciel, légère cambrure arrière",
            "Flexion avant, mains vers le sol",
            "Fente arrière, puis planche, chaturanga, cobra",
            "Chien tête en bas, fente avant, remontez. Répétez 3 fois"
        ],
        "is_premium": False,
        "icon": "sun"
    },
    {
        "action_id": "action_well_048",
        "title": "Étirements profonds",
        "description": "Maintenez 5 étirements profonds pendant 30 secondes chacun pour une flexibilité durable.",
        "category": "well_being",
        "duration_min": 5,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Étirement du pigeon (hanches) : 30 secondes chaque côté",
            "Étirement du psoas en fente : 30 secondes chaque côté",
            "Torsion au sol : 30 secondes chaque côté",
            "Papillon (aines) : 30 secondes",
            "Flexion avant jambes tendues : 30 secondes"
        ],
        "is_premium": True,
        "icon": "stretch-horizontal"
    },
    {
        "action_id": "action_well_049",
        "title": "Mobilité articulaire",
        "description": "Faites des cercles avec chaque articulation pour maintenir votre mobilité.",
        "category": "well_being",
        "duration_min": 5,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Cercles de la tête : 5 dans chaque sens",
            "Cercles des épaules : 10 en avant, 10 en arrière",
            "Cercles des poignets : 10 dans chaque sens",
            "Cercles des hanches : 10 dans chaque sens",
            "Cercles des chevilles : 10 dans chaque sens"
        ],
        "is_premium": False,
        "icon": "rotate-cw"
    },
    {
        "action_id": "action_well_050",
        "title": "Massage des mains",
        "description": "Auto-massez vos mains et vos doigts pour relâcher les tensions accumulées.",
        "category": "well_being",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "medium",
        "instructions": [
            "Frottez vos paumes l'une contre l'autre pour les réchauffer",
            "Massez chaque doigt en pressant et en tournant",
            "Pétrissez la paume avec le pouce de l'autre main",
            "Étirez doucement chaque doigt vers l'arrière",
            "Secouez vos mains pour libérer la tension restante"
        ],
        "is_premium": False,
        "icon": "hand"
    },

    # Mindfulness & Emotional (051-055)
    {
        "action_id": "action_well_051",
        "title": "Marche consciente",
        "description": "Transformez une marche ordinaire en exercice de pleine conscience sensorielle.",
        "category": "well_being",
        "duration_min": 7,
        "duration_max": 12,
        "energy_level": "medium",
        "instructions": [
            "Sortez marcher sans téléphone (ou en mode avion)",
            "Concentrez-vous sur les sensations de vos pieds",
            "Observez votre environnement comme si c'était la première fois",
            "Notez 5 choses que vous n'aviez jamais remarquées",
            "Revenez en vous sentant rafraîchi"
        ],
        "is_premium": False,
        "icon": "footprints"
    },
    {
        "action_id": "action_well_052",
        "title": "Thé en pleine conscience",
        "description": "Préparez et buvez une tasse de thé en pleine conscience, comme un rituel.",
        "category": "well_being",
        "duration_min": 7,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Faites chauffer l'eau en observant les bulles se former",
            "Sentez le thé sec avant de l'infuser",
            "Versez l'eau et observez la couleur se diffuser",
            "Tenez la tasse entre vos mains et ressentez la chaleur",
            "Buvez lentement en savourant chaque gorgée"
        ],
        "is_premium": True,
        "icon": "coffee"
    },
    {
        "action_id": "action_well_053",
        "title": "Auto-massage visage",
        "description": "Massez votre visage pour relâcher les tensions de la mâchoire et du front.",
        "category": "well_being",
        "duration_min": 5,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Frottez vos paumes pour les réchauffer",
            "Posez-les sur vos yeux fermés pendant 30 secondes",
            "Massez vos tempes en cercles doux",
            "Pétrissez les muscles de la mâchoire",
            "Lissez votre front du centre vers les tempes"
        ],
        "is_premium": False,
        "icon": "smile"
    },
    {
        "action_id": "action_well_054",
        "title": "Dessin de son émotion",
        "description": "Dessinez votre émotion actuelle de façon abstraite pour mieux la comprendre.",
        "category": "well_being",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Identifiez l'émotion que vous ressentez maintenant",
            "Choisissez des couleurs qui la représentent",
            "Dessinez des formes abstraites qui expriment cette émotion",
            "Observez votre dessin et notez ce qu'il révèle",
            "Remarquez si l'émotion a changé après le dessin"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    {
        "action_id": "action_well_055",
        "title": "Rituel de lâcher-prise",
        "description": "Écrivez ce qui vous pèse sur un papier et symboliquement lâchez-le.",
        "category": "well_being",
        "duration_min": 5,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Écrivez sur un papier ce qui vous tracasse",
            "Relisez-le une fois à voix haute",
            "Froissez le papier en boule",
            "Jetez-le (ou déchirez-le) en décidant de lâcher prise",
            "Respirez profondément et passez à autre chose"
        ],
        "is_premium": False,
        "icon": "trash-2"
    },

    # Social & Nature (056-060)
    {
        "action_id": "action_well_056",
        "title": "Appel bienveillant",
        "description": "Appelez quelqu'un juste pour prendre de ses nouvelles, sans raison particulière.",
        "category": "well_being",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Pensez à quelqu'un que vous n'avez pas contacté depuis longtemps",
            "Appelez-le juste pour prendre de ses nouvelles",
            "Écoutez vraiment comment il/elle va",
            "Partagez un souvenir positif que vous avez ensemble"
        ],
        "is_premium": False,
        "icon": "phone"
    },
    {
        "action_id": "action_well_057",
        "title": "Acte de bonté aléatoire",
        "description": "Faites un geste de gentillesse inattendu pour quelqu'un, même un inconnu.",
        "category": "well_being",
        "duration_min": 3,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Choisissez un acte de bonté : tenir la porte, offrir un café, aider à porter…",
            "Cherchez une opportunité dans votre environnement immédiat",
            "Agissez sans attendre de remerciement",
            "Savourez la sensation positive que cela procure"
        ],
        "is_premium": False,
        "icon": "heart-handshake"
    },
    {
        "action_id": "action_well_058",
        "title": "Bain de nature mini",
        "description": "Faites un mini bain de forêt en passant 10 minutes en connexion avec la nature.",
        "category": "well_being",
        "duration_min": 8,
        "duration_max": 12,
        "energy_level": "medium",
        "instructions": [
            "Trouvez un espace vert même petit (parc, jardin…)",
            "Marchez lentement en laissant vos sens s'ouvrir",
            "Touchez l'écorce d'un arbre, sentez une fleur",
            "Asseyez-vous et écoutez les sons de la nature pendant 3 min"
        ],
        "is_premium": False,
        "icon": "tree-pine"
    },
    {
        "action_id": "action_well_059",
        "title": "Photo nature mindful",
        "description": "Prenez 5 photos de la nature en vous concentrant sur les détails que personne ne voit.",
        "category": "well_being",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Sortez avec votre téléphone en mode appareil photo",
            "Cherchez des détails minuscules : gouttelette, texture, insecte…",
            "Prenez 5 photos en vous approchant au maximum",
            "Observez chaque sujet pendant 30 secondes avant de photographier"
        ],
        "is_premium": True,
        "icon": "camera"
    },
    {
        "action_id": "action_well_060",
        "title": "Écoute musicale active",
        "description": "Écoutez un morceau de musique en ressentant les émotions qu'il suscite dans votre corps.",
        "category": "well_being",
        "duration_min": 5,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Choisissez un morceau qui vous touche émotionnellement",
            "Fermez les yeux et mettez un casque",
            "Laissez la musique traverser votre corps",
            "Notez où vous ressentez des émotions physiquement",
            "Laissez-vous aller à ce que la musique provoque"
        ],
        "is_premium": False,
        "icon": "headphones"
    },

    # Sleep & Recovery (061-063)
    {
        "action_id": "action_well_061",
        "title": "Rituel pré-sommeil",
        "description": "Créez un rituel de 10 minutes pour signaler à votre corps qu'il est temps de dormir.",
        "category": "well_being",
        "duration_min": 8,
        "duration_max": 12,
        "energy_level": "medium",
        "instructions": [
            "Baissez les lumières de votre chambre",
            "Faites 3 minutes d'étirements doux",
            "Écrivez 3 gratitudes de la journée",
            "Faites 2 minutes de respiration cohérence cardiaque",
            "Fermez les yeux et visualisez un lieu apaisant"
        ],
        "is_premium": False,
        "icon": "moon"
    },
    {
        "action_id": "action_well_062",
        "title": "Yoga nidra express",
        "description": "Pratiquez un yoga nidra guidé de 10 minutes pour une relaxation profonde consciente.",
        "category": "well_being",
        "duration_min": 8,
        "duration_max": 12,
        "energy_level": "medium",
        "instructions": [
            "Allongez-vous dans un endroit calme",
            "Formulez une intention (sankalpa) en une phrase positive",
            "Scannez votre corps de droite à gauche, des pieds à la tête",
            "Observez votre respiration naturelle pendant 2 minutes",
            "Répétez votre intention et revenez doucement"
        ],
        "is_premium": True,
        "icon": "bed"
    },
    {
        "action_id": "action_well_063",
        "title": "Inventaire bien-être",
        "description": "Évaluez votre bien-être global sur 5 dimensions et identifiez un axe d'amélioration.",
        "category": "well_being",
        "duration_min": 5,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Notez sur 10 : énergie physique, clarté mentale, humeur, relations, sommeil",
            "Identifiez la dimension la plus basse",
            "Trouvez une action concrète pour l'améliorer",
            "Planifiez cette action dans votre semaine"
        ],
        "is_premium": False,
        "icon": "clipboard-check"
    },

    # Nutrition & Joy (064-068)
    {
        "action_id": "action_well_064",
        "title": "Meal prep réflexion",
        "description": "Planifiez 3 repas sains pour la semaine en vous inspirant de ce dont votre corps a besoin.",
        "category": "well_being",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Écoutez ce dont votre corps a envie cette semaine",
            "Choisissez 3 recettes équilibrées et faciles",
            "Listez les ingrédients nécessaires",
            "Identifiez les préparations que vous pouvez anticiper"
        ],
        "is_premium": True,
        "icon": "utensils"
    },
    {
        "action_id": "action_well_065",
        "title": "Pause danse",
        "description": "Mettez votre chanson préférée et dansez librement pendant 3-5 minutes.",
        "category": "well_being",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "medium",
        "instructions": [
            "Mettez une chanson qui vous donne envie de bouger",
            "Levez-vous et laissez votre corps bouger librement",
            "Ne vous souciez pas de bien danser, bougez avec joie",
            "Laissez le sourire venir naturellement"
        ],
        "is_premium": False,
        "icon": "music"
    },
    {
        "action_id": "action_well_066",
        "title": "Yoga du rire",
        "description": "Pratiquez le yoga du rire : commencez par un faux rire qui devient vrai.",
        "category": "well_being",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "medium",
        "instructions": [
            "Commencez par un rire simulé : ha ha ha ho ho ho",
            "Ajoutez des gestes : tapez dans vos mains, levez les bras",
            "Le faux rire va naturellement devenir un vrai rire",
            "Continuez pendant 3 minutes et terminez par une respiration calme"
        ],
        "is_premium": False,
        "icon": "laugh"
    },
    {
        "action_id": "action_well_067",
        "title": "Playlist bonheur",
        "description": "Créez une playlist de 5 chansons qui vous rendent instantanément heureux.",
        "category": "well_being",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Pensez aux chansons liées à vos meilleurs souvenirs",
            "Sélectionnez 5 morceaux qui vous font sourire à coup sûr",
            "Créez une playlist 'SOS Bonheur' sur votre app de musique",
            "Écoutez le premier morceau maintenant et ressentez la joie"
        ],
        "is_premium": False,
        "icon": "music"
    },
    {
        "action_id": "action_well_068",
        "title": "Mouvement ludique",
        "description": "Bougez votre corps de manière ludique comme quand vous étiez enfant.",
        "category": "well_being",
        "duration_min": 5,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Pensez à un mouvement d'enfant : sautiller, tourner, sauter…",
            "Faites-le pendant 1 minute sans vous soucier du regard des autres",
            "Enchaînez avec un autre mouvement ludique",
            "Terminez en riant de votre propre jeu"
        ],
        "is_premium": True,
        "icon": "smile"
    },

    # Mixed medium (069-075)
    {
        "action_id": "action_well_069",
        "title": "Posture de gratitude",
        "description": "Adoptez une posture ouverte et exprimez physiquement votre gratitude.",
        "category": "well_being",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "medium",
        "instructions": [
            "Debout, ouvrez grand les bras vers le ciel",
            "Inspirez profondément en levant le visage",
            "Dites à voix haute 3 choses dont vous êtes reconnaissant",
            "Posez les mains sur votre cœur et ressentez la gratitude"
        ],
        "is_premium": False,
        "icon": "heart"
    },
    {
        "action_id": "action_well_070",
        "title": "Douche en conscience",
        "description": "Transformez votre prochaine douche en moment de méditation sensorielle.",
        "category": "well_being",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Pendant votre douche, focalisez-vous uniquement sur les sensations",
            "Ressentez l'eau sur chaque partie de votre corps",
            "Variez la température et observez les changements",
            "Imaginez que l'eau emporte vos tensions et votre stress"
        ],
        "is_premium": False,
        "icon": "droplets"
    },
    {
        "action_id": "action_well_071",
        "title": "Contemplation artistique",
        "description": "Regardez une belle image ou photo pendant 5 minutes en laissant les émotions monter.",
        "category": "well_being",
        "duration_min": 5,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Trouvez une image qui vous inspire : paysage, art, photo…",
            "Regardez-la pendant 5 minutes en silence",
            "Notez les émotions qui surgissent sans les juger",
            "Écrivez un mot ou une phrase que cette image vous inspire"
        ],
        "is_premium": False,
        "icon": "image"
    },
    {
        "action_id": "action_well_072",
        "title": "Écriture de libération",
        "description": "Écrivez tout ce qui vous stresse puis transformez-le en affirmations positives.",
        "category": "well_being",
        "duration_min": 7,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Écrivez tout ce qui vous stresse en ce moment",
            "Relisez chaque élément",
            "Transformez chaque stress en affirmation positive opposée",
            "Relisez les affirmations à voix haute",
            "Respirez et ressentez le changement de perspective"
        ],
        "is_premium": True,
        "icon": "pen-tool"
    },
    {
        "action_id": "action_well_073",
        "title": "Scan de posture",
        "description": "Corrigez votre posture actuelle et prenez conscience de vos habitudes posturales.",
        "category": "well_being",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "medium",
        "instructions": [
            "Scannez votre posture actuelle : épaules ? Dos ? Tête ?",
            "Redressez-vous : pieds à plat, dos droit, épaules basses et arrière",
            "Imaginez un fil qui tire le sommet de votre crâne vers le ciel",
            "Programmez un rappel pour vérifier votre posture dans 2h"
        ],
        "is_premium": False,
        "icon": "person-standing"
    },
    {
        "action_id": "action_well_074",
        "title": "Réservoir d'énergie",
        "description": "Identifiez ce qui remplit et ce qui vide votre réservoir d'énergie.",
        "category": "well_being",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Dessinez un réservoir avec un niveau d'énergie actuel",
            "Listez 5 activités qui remplissent votre réservoir",
            "Listez 5 activités qui le vident",
            "Planifiez plus d'activités remplissantes cette semaine",
            "Identifiez un videur d'énergie à limiter"
        ],
        "is_premium": False,
        "icon": "battery-charging"
    },
    {
        "action_id": "action_well_075",
        "title": "Connexion avec soi",
        "description": "Répondez à 3 questions profondes pour vous reconnecter avec vos valeurs.",
        "category": "well_being",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Qu'est-ce qui m'a rendu vraiment vivant cette semaine ?",
            "Qu'est-ce que j'évite en ce moment et pourquoi ?",
            "Si je n'avais peur de rien, que ferais-je demain ?",
            "Notez vos réponses et identifiez un fil conducteur"
        ],
        "is_premium": True,
        "icon": "compass"
    },

    # --- WELL-BEING / HIGH ENERGY (25) ---

    # Movement & Exercise (076-082)
    {
        "action_id": "action_well_076",
        "title": "HIIT 7 minutes",
        "description": "Faites un entraînement HIIT de 7 minutes pour booster vos endorphines.",
        "category": "well_being",
        "duration_min": 7,
        "duration_max": 10,
        "energy_level": "high",
        "instructions": [
            "30s jumping jacks + 10s repos",
            "30s squats + 10s repos",
            "30s montées de genoux + 10s repos",
            "30s pompes + 10s repos",
            "30s burpees + 10s repos. Répétez 2 cycles"
        ],
        "is_premium": False,
        "icon": "flame"
    },
    {
        "action_id": "action_well_077",
        "title": "Flow yoga énergisant",
        "description": "Enchaînez un flow yoga dynamique pour éveiller chaque partie de votre corps.",
        "category": "well_being",
        "duration_min": 8,
        "duration_max": 12,
        "energy_level": "high",
        "instructions": [
            "Commencez par 3 salutations au soleil",
            "Enchaînez : guerrier 1, guerrier 2, triangle (chaque côté)",
            "Ajoutez : chien tête en bas, cobra, enfant",
            "Terminez par une posture d'équilibre : arbre ou guerrier 3",
            "Relaxation finale en savasana 1 minute"
        ],
        "is_premium": True,
        "icon": "sun"
    },
    {
        "action_id": "action_well_078",
        "title": "Circuit abdos express",
        "description": "Renforcez votre ceinture abdominale avec un circuit de 5 exercices ciblés.",
        "category": "well_being",
        "duration_min": 7,
        "duration_max": 10,
        "energy_level": "high",
        "instructions": [
            "Planche classique : 30 secondes",
            "Crunchs : 15 répétitions",
            "Planche latérale : 20 secondes chaque côté",
            "Mountain climbers : 20 répétitions",
            "Dead bug : 10 répétitions. Repos 30s et répétez"
        ],
        "is_premium": False,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_well_079",
        "title": "Cardio danse",
        "description": "Dansez sur 3 chansons énergiques pour faire du cardio tout en vous amusant.",
        "category": "well_being",
        "duration_min": 8,
        "duration_max": 12,
        "energy_level": "high",
        "instructions": [
            "Créez une mini-playlist de 3 chansons énergiques",
            "Chanson 1 : échauffement en bougeant librement",
            "Chanson 2 : intensifiez les mouvements, sautez, tournez",
            "Chanson 3 : donnez tout puis ralentissez progressivement",
            "Terminez par 1 minute de marche sur place"
        ],
        "is_premium": False,
        "icon": "music"
    },
    {
        "action_id": "action_well_080",
        "title": "Gainage challenge",
        "description": "Testez votre temps maximum de gainage et essayez de battre votre record.",
        "category": "well_being",
        "duration_min": 5,
        "duration_max": 8,
        "energy_level": "high",
        "instructions": [
            "Échauffement : 1 minute de mouvements doux",
            "Planche sur les avant-bras : tenez le plus longtemps possible",
            "Chronométrez et notez votre temps",
            "Repos 1 minute",
            "Essayez une deuxième fois et comparez"
        ],
        "is_premium": False,
        "icon": "timer"
    },
    {
        "action_id": "action_well_081",
        "title": "Tabata express",
        "description": "Faites un Tabata de 4 minutes : 20 secondes d'effort, 10 secondes de repos, 8 cycles.",
        "category": "well_being",
        "duration_min": 5,
        "duration_max": 8,
        "energy_level": "high",
        "instructions": [
            "Choisissez un exercice : squats sautés, burpees, mountain climbers…",
            "20 secondes d'effort MAXIMUM",
            "10 secondes de repos COMPLET",
            "Répétez 8 cycles (4 minutes total)",
            "Terminez par 1 minute de récupération active"
        ],
        "is_premium": False,
        "icon": "flame"
    },
    {
        "action_id": "action_well_082",
        "title": "Stretching profond",
        "description": "Faites un stretching profond de 10 minutes en maintenant chaque posture 1 minute.",
        "category": "well_being",
        "duration_min": 10,
        "duration_max": 15,
        "energy_level": "high",
        "instructions": [
            "Commencez par le haut du corps : cou, épaules, bras",
            "Passez au tronc : torsions, flexions latérales",
            "Terminez par le bas : hanches, jambes, mollets",
            "Maintenez chaque position 1 minute en respirant profondément",
            "Ne forcez jamais, allez jusqu'à la sensation, pas la douleur"
        ],
        "is_premium": True,
        "icon": "stretch-horizontal"
    },

    # Emotional & Deep (083-087)
    {
        "action_id": "action_well_083",
        "title": "Méditation corporelle",
        "description": "Méditez en portant une attention profonde aux sensations de chaque partie du corps.",
        "category": "well_being",
        "duration_min": 10,
        "duration_max": 15,
        "energy_level": "high",
        "instructions": [
            "Allongez-vous et fermez les yeux",
            "Portez votre attention sur la plante des pieds pendant 1 min",
            "Remontez lentement : chevilles, genoux, hanches…",
            "Passez 30 secondes minimum sur chaque zone",
            "Ressentez votre corps entier vibrer d'attention"
        ],
        "is_premium": True,
        "icon": "scan"
    },
    {
        "action_id": "action_well_084",
        "title": "Journaling profond",
        "description": "Explorez une question profonde par écrit pour gagner en clarté intérieure.",
        "category": "well_being",
        "duration_min": 10,
        "duration_max": 15,
        "energy_level": "high",
        "instructions": [
            "Choisissez une question : 'Qu'est-ce que j'évite ?', 'De quoi ai-je besoin ?'",
            "Écrivez sans vous arrêter pendant 10 minutes",
            "Ne censurez rien, laissez couler la plume",
            "Relisez et surlignez les phrases qui résonnent",
            "Identifiez une action concrète inspirée de votre écriture"
        ],
        "is_premium": False,
        "icon": "notebook"
    },
    {
        "action_id": "action_well_085",
        "title": "Rituel de libération",
        "description": "Libérez-vous symboliquement d'une charge émotionnelle avec un rituel personnel.",
        "category": "well_being",
        "duration_min": 7,
        "duration_max": 12,
        "energy_level": "high",
        "instructions": [
            "Écrivez sur un papier ce que vous voulez lâcher",
            "Lisez-le à voix haute avec intention",
            "Déchirez le papier en petits morceaux",
            "Jetez les morceaux en disant 'Je me libère'",
            "Prenez 3 grandes respirations de renouveau"
        ],
        "is_premium": True,
        "icon": "wind"
    },
    {
        "action_id": "action_well_086",
        "title": "Visualisation d'avenir",
        "description": "Visualisez en détail votre vie idéale dans 5 ans pour clarifier vos aspirations.",
        "category": "well_being",
        "duration_min": 7,
        "duration_max": 12,
        "energy_level": "high",
        "instructions": [
            "Fermez les yeux et projetez-vous dans 5 ans",
            "Où êtes-vous ? Avec qui ? Que faites-vous ?",
            "Ajoutez des détails sensoriels : sons, odeurs, émotions",
            "Ressentez les émotions comme si c'était réel",
            "Écrivez les 3 éléments les plus importants de cette vision"
        ],
        "is_premium": False,
        "icon": "eye"
    },
    {
        "action_id": "action_well_087",
        "title": "Cercle de valeurs",
        "description": "Identifiez vos 5 valeurs fondamentales et vérifiez si votre vie est alignée.",
        "category": "well_being",
        "duration_min": 7,
        "duration_max": 12,
        "energy_level": "high",
        "instructions": [
            "Listez 10 valeurs qui vous parlent (liberté, famille, créativité…)",
            "Réduisez à vos 5 valeurs essentielles",
            "Pour chaque valeur, évaluez sur 10 à quel point votre vie l'honore",
            "Identifiez la valeur la moins honorée",
            "Planifiez une action concrète pour mieux la vivre"
        ],
        "is_premium": True,
        "icon": "compass"
    },

    # Social & Connection (088-091)
    {
        "action_id": "action_well_088",
        "title": "Lettre de gratitude",
        "description": "Rédigez et envoyez une vraie lettre de gratitude à quelqu'un qui a marqué votre vie.",
        "category": "well_being",
        "duration_min": 10,
        "duration_max": 15,
        "energy_level": "high",
        "instructions": [
            "Choisissez quelqu'un qui a eu un impact positif sur votre vie",
            "Écrivez une lettre détaillée expliquant pourquoi",
            "Soyez spécifique : racontez un moment précis",
            "Envoyez-la ou mieux : lisez-la à la personne",
            "Savourez l'émotion partagée"
        ],
        "is_premium": False,
        "icon": "mail"
    },
    {
        "action_id": "action_well_089",
        "title": "Conversation profonde",
        "description": "Lancez une conversation profonde avec quelqu'un en posant une question inhabituelle.",
        "category": "well_being",
        "duration_min": 10,
        "duration_max": 15,
        "energy_level": "high",
        "instructions": [
            "Choisissez une question profonde : 'Quel moment a changé ta vie ?'",
            "Posez-la à quelqu'un de confiance",
            "Écoutez avec toute votre attention, sans interrompre",
            "Partagez votre propre réponse",
            "Remerciez la personne pour ce moment de partage"
        ],
        "is_premium": False,
        "icon": "message-circle"
    },
    {
        "action_id": "action_well_090",
        "title": "Carte mentale de vie",
        "description": "Cartographiez les domaines de votre vie et évaluez votre satisfaction globale.",
        "category": "well_being",
        "duration_min": 10,
        "duration_max": 15,
        "energy_level": "high",
        "instructions": [
            "Dessinez une roue avec 8 sections : santé, carrière, relations, finances, loisirs, croissance, environnement, contribution",
            "Notez chaque section sur 10",
            "Coloriez jusqu'au niveau de satisfaction",
            "Identifiez la section la plus basse",
            "Définissez 3 actions pour l'améliorer ce mois"
        ],
        "is_premium": False,
        "icon": "pie-chart"
    },
    {
        "action_id": "action_well_091",
        "title": "Méditation compassion",
        "description": "Pratiquez une méditation de compassion avancée pour vous et pour les autres.",
        "category": "well_being",
        "duration_min": 10,
        "duration_max": 15,
        "energy_level": "high",
        "instructions": [
            "Asseyez-vous confortablement et fermez les yeux",
            "Envoyez de la compassion à vous-même pendant 2 min",
            "Envoyez de la compassion à un être cher pendant 2 min",
            "Envoyez de la compassion à quelqu'un de neutre pendant 2 min",
            "Envoyez de la compassion à quelqu'un de difficile pendant 2 min"
        ],
        "is_premium": True,
        "icon": "heart"
    },

    # Joy, Play & Nature (092-097)
    {
        "action_id": "action_well_092",
        "title": "Danse libre totale",
        "description": "Dansez pendant 10 minutes en exprimant chaque émotion par le mouvement.",
        "category": "well_being",
        "duration_min": 8,
        "duration_max": 12,
        "energy_level": "high",
        "instructions": [
            "Mettez une playlist variée : lent, rapide, tribal, doux…",
            "Commencez par des mouvements lents et fluides",
            "Laissez votre corps exprimer ce qu'il ressent",
            "Intensifiez progressivement",
            "Terminez par des mouvements doux et une respiration"
        ],
        "is_premium": False,
        "icon": "music"
    },
    {
        "action_id": "action_well_093",
        "title": "Marche consciente nature",
        "description": "Marchez 10 minutes dans la nature en activant tous vos sens pleinement.",
        "category": "well_being",
        "duration_min": 10,
        "duration_max": 15,
        "energy_level": "high",
        "instructions": [
            "Trouvez un espace vert et laissez votre téléphone",
            "Marchez lentement en regardant la nature en détail",
            "Touchez des éléments naturels : feuilles, écorce, pierres",
            "Écoutez les sons de la nature pendant 2 minutes immobile",
            "Inspirez profondément les odeurs naturelles"
        ],
        "is_premium": False,
        "icon": "tree-pine"
    },
    {
        "action_id": "action_well_094",
        "title": "Jeu créatif libre",
        "description": "Jouez librement pendant 10 minutes comme un enfant, sans but ni règle.",
        "category": "well_being",
        "duration_min": 8,
        "duration_max": 12,
        "energy_level": "high",
        "instructions": [
            "Choisissez une activité ludique : construire, dessiner, jouer avec un objet…",
            "Fixez un minuteur de 10 minutes",
            "Jouez sans but, sans évaluation, sans résultat attendu",
            "Laissez votre imagination guider vos actions",
            "Remarquez comment vous vous sentez après"
        ],
        "is_premium": True,
        "icon": "puzzle"
    },
    {
        "action_id": "action_well_095",
        "title": "Défi sportif mini",
        "description": "Lancez-vous un mini défi sportif et essayez de vous dépasser en 10 minutes.",
        "category": "well_being",
        "duration_min": 8,
        "duration_max": 12,
        "energy_level": "high",
        "instructions": [
            "Choisissez un défi : max de pompes, squat hold, sprint…",
            "Échauffez-vous pendant 2 minutes",
            "Donnez votre maximum pendant l'exercice",
            "Notez votre performance",
            "Étirez-vous et planifiez quand retenter le défi"
        ],
        "is_premium": False,
        "icon": "trophy"
    },
    {
        "action_id": "action_well_096",
        "title": "Chant libre expressif",
        "description": "Chantez à pleine voix une chanson qui vous fait vibrer, sans retenue.",
        "category": "well_being",
        "duration_min": 5,
        "duration_max": 8,
        "energy_level": "high",
        "instructions": [
            "Choisissez une chanson que vous adorez chanter",
            "Mettez la musique à bon volume",
            "Chantez à pleins poumons sans vous soucier de la justesse",
            "Mettez-y toute l'émotion que vous pouvez",
            "Terminez par un silence et ressentez les vibrations"
        ],
        "is_premium": False,
        "icon": "mic"
    },
    {
        "action_id": "action_well_097",
        "title": "Course consciente",
        "description": "Courez pendant 10 minutes en pleine conscience de votre corps et de votre respiration.",
        "category": "well_being",
        "duration_min": 10,
        "duration_max": 15,
        "energy_level": "high",
        "instructions": [
            "Commencez par 2 minutes de marche rapide",
            "Passez au jogging léger en synchronisant respiration et pas",
            "Focalisez-vous sur le contact de vos pieds avec le sol",
            "Accélérez pendant 2 minutes puis ralentissez",
            "Terminez par 2 minutes de marche de récupération"
        ],
        "is_premium": True,
        "icon": "footprints"
    },

    # Deep wellness (098-100)
    {
        "action_id": "action_well_098",
        "title": "Bilan émotionnel semaine",
        "description": "Faites un bilan émotionnel complet de votre semaine pour gagner en intelligence émotionnelle.",
        "category": "well_being",
        "duration_min": 10,
        "duration_max": 15,
        "energy_level": "high",
        "instructions": [
            "Listez les 3 moments les plus positifs de la semaine",
            "Listez les 3 moments les plus difficiles",
            "Identifiez les émotions dominantes de chaque moment",
            "Trouvez un pattern : qu'est-ce qui déclenche vos meilleures émotions ?",
            "Planifiez plus de ces déclencheurs la semaine prochaine"
        ],
        "is_premium": False,
        "icon": "heart"
    },
    {
        "action_id": "action_well_099",
        "title": "Rituel de renouveau",
        "description": "Créez un rituel personnel de renouveau pour démarrer un nouveau cycle avec intention.",
        "category": "well_being",
        "duration_min": 10,
        "duration_max": 15,
        "energy_level": "high",
        "instructions": [
            "Choisissez ce que vous voulez laisser derrière vous",
            "Choisissez ce que vous voulez accueillir",
            "Créez un geste symbolique : allumer une bougie, écrire et déchirer…",
            "Formulez une intention pour le nouveau cycle",
            "Terminez par 3 grandes respirations d'ouverture"
        ],
        "is_premium": True,
        "icon": "sunrise"
    },
    {
        "action_id": "action_well_100",
        "title": "Plan bien-être perso",
        "description": "Concevez votre plan de bien-être personnalisé pour les 30 prochains jours.",
        "category": "well_being",
        "duration_min": 10,
        "duration_max": 15,
        "energy_level": "high",
        "instructions": [
            "Évaluez votre bien-être actuel sur 5 dimensions",
            "Choisissez 3 habitudes de bien-être à intégrer",
            "Planifiez quand et comment les pratiquer chaque jour",
            "Créez un tracker visuel pour les 30 jours",
            "Fixez un rendez-vous avec vous-même pour le bilan dans 30 jours"
        ],
        "is_premium": False,
        "icon": "calendar-heart"
    },
]
