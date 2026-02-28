"""
Premium micro-actions for InFinea - Part 1
Categories: creativity, fitness, mindfulness, leadership (50 each = 200 total)
"""

PREMIUM_ACTIONS_PART1 = [
    # =====================================================================
    # CREATIVITY (50 actions) - icon: "palette"
    # =====================================================================
    # --- Visual creativity ---
    {
        "action_id": "action_creativity_001",
        "title": "Croquis rapide",
        "description": "Dessinez un objet de votre environnement en 5 minutes pour stimuler votre créativité visuelle.",
        "category": "creativity",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Choisissez un objet simple autour de vous",
            "Prenez un crayon et du papier (ou votre tablette)",
            "Dessinez l'objet sans lever le crayon pendant 3 minutes",
            "Ajoutez des détails pendant les 2 minutes restantes"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    {
        "action_id": "action_creativity_002",
        "title": "Palette émotionnelle",
        "description": "Associez des couleurs à vos émotions actuelles pour développer votre sensibilité chromatique.",
        "category": "creativity",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Identifiez 3 émotions que vous ressentez en ce moment",
            "Attribuez une couleur à chaque émotion instinctivement",
            "Dessinez ou coloriez une forme abstraite avec ces couleurs",
            "Notez pourquoi ces associations vous semblent justes"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    {
        "action_id": "action_creativity_003",
        "title": "Cadrage insolite",
        "description": "Prenez 5 photos du même objet sous des angles radicalement différents.",
        "category": "creativity",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Choisissez un objet banal (tasse, chaise, plante)",
            "Photographiez-le en plongée, contre-plongée et macro",
            "Essayez un cadrage avec un premier plan flou",
            "Comparez vos 5 photos et identifiez la plus surprenante"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    {
        "action_id": "action_creativity_004",
        "title": "Moodboard express",
        "description": "Créez un moodboard de 9 images en 5 minutes pour clarifier une idée ou un projet.",
        "category": "creativity",
        "duration_min": 4,
        "duration_max": 7,
        "energy_level": "medium",
        "instructions": [
            "Définissez un thème ou un projet en une phrase",
            "Cherchez 9 images qui évoquent l'ambiance souhaitée",
            "Disposez-les en grille 3x3 sur un document ou une table",
            "Identifiez le fil conducteur visuel qui émerge"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    {
        "action_id": "action_creativity_005",
        "title": "Dessin inversé",
        "description": "Dessinez un objet en commençant par les ombres pour entraîner votre perception visuelle.",
        "category": "creativity",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "low",
        "instructions": [
            "Choisissez un objet bien éclairé devant vous",
            "Commencez par dessiner uniquement les zones d'ombre",
            "Ajoutez ensuite les contours principaux",
            "Observez comment cette approche change votre perception"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    {
        "action_id": "action_creativity_006",
        "title": "Texture tactile",
        "description": "Reproduisez 5 textures différentes au crayon pour affiner votre sens du détail.",
        "category": "creativity",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "low",
        "instructions": [
            "Touchez 5 surfaces différentes autour de vous (bois, tissu, métal...)",
            "Divisez une feuille en 5 zones égales",
            "Reproduisez chaque texture au crayon avec des hachures adaptées",
            "Comparez vos dessins aux vraies textures pour évaluer la ressemblance"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    {
        "action_id": "action_creativity_007",
        "title": "Collage mental",
        "description": "Combinez mentalement 3 images aléatoires pour créer un concept visuel original.",
        "category": "creativity",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "medium",
        "instructions": [
            "Ouvrez 3 images aléatoires sur votre téléphone ou un magazine",
            "Imaginez comment fusionner ces 3 images en une seule scène",
            "Esquissez rapidement le résultat sur papier",
            "Donnez un titre à votre création hybride"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    {
        "action_id": "action_creativity_008",
        "title": "Symétrie brisée",
        "description": "Dessinez un motif symétrique puis cassez volontairement la symétrie pour créer du dynamisme.",
        "category": "creativity",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "high",
        "instructions": [
            "Tracez un axe vertical au centre d'une feuille",
            "Dessinez un motif géométrique symétrique des deux côtés",
            "Modifiez un seul élément d'un côté pour briser la symétrie",
            "Observez comment ce déséquilibre crée un point focal"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    {
        "action_id": "action_creativity_009",
        "title": "Nuancier naturel",
        "description": "Identifiez et cataloguez 10 nuances de couleur dans votre environnement immédiat.",
        "category": "creativity",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Choisissez une couleur de base (vert, bleu, brun...)",
            "Repérez 10 variantes de cette couleur autour de vous",
            "Notez chaque nuance avec un nom inventé (ex: bleu lundi matin)",
            "Classez-les du plus clair au plus foncé"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    {
        "action_id": "action_creativity_010",
        "title": "Zoom abstrait",
        "description": "Photographiez un détail minuscule d'un objet pour révéler sa beauté abstraite.",
        "category": "creativity",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Activez le mode macro de votre téléphone",
            "Approchez-vous au maximum d'une surface texturée",
            "Prenez 3 photos en variant légèrement l'angle",
            "Choisissez celle qui ressemble le plus à une œuvre abstraite"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    # --- Writing creativity ---
    {
        "action_id": "action_creativity_011",
        "title": "Micro-fiction 50 mots",
        "description": "Écrivez une histoire complète en exactement 50 mots pour muscler votre concision.",
        "category": "creativity",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Choisissez un mot au hasard dans un livre ou dictionnaire",
            "Écrivez une histoire avec un début, un milieu et une fin",
            "Comptez les mots et ajustez pour arriver à exactement 50",
            "Relisez à voix haute pour vérifier le rythme"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    {
        "action_id": "action_creativity_012",
        "title": "Haïku du moment",
        "description": "Composez un haïku (5-7-5 syllabes) capturant l'instant présent.",
        "category": "creativity",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Observez ce qui se passe autour de vous pendant 1 minute",
            "Identifiez une image, un son ou une sensation qui vous frappe",
            "Écrivez 3 vers : 5 syllabes, 7 syllabes, 5 syllabes",
            "Affinez les mots pour maximiser l'impact en minimum de syllabes"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    {
        "action_id": "action_creativity_013",
        "title": "Journal sensoriel",
        "description": "Décrivez votre moment présent en utilisant les 5 sens pour enrichir votre écriture.",
        "category": "creativity",
        "duration_min": 4,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Notez ce que vous voyez en ce moment en une phrase",
            "Ajoutez une phrase pour chaque sens : ouïe, odorat, toucher, goût",
            "Reliez ces 5 phrases en un paragraphe fluide",
            "Soulignez les mots les plus évocateurs"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    {
        "action_id": "action_creativity_014",
        "title": "Dialogue imaginaire",
        "description": "Écrivez un dialogue entre deux objets de votre bureau pour libérer votre imagination.",
        "category": "creativity",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Choisissez 2 objets sur votre bureau et donnez-leur un caractère",
            "Imaginez un sujet de désaccord entre eux",
            "Écrivez 6 à 8 répliques alternées",
            "Terminez par une résolution surprenante"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    {
        "action_id": "action_creativity_015",
        "title": "Copywriting éclair",
        "description": "Rédigez 5 accroches différentes pour un produit imaginaire en 5 minutes.",
        "category": "creativity",
        "duration_min": 4,
        "duration_max": 7,
        "energy_level": "medium",
        "instructions": [
            "Inventez un produit absurde (ex: parapluie pour chats)",
            "Écrivez une accroche émotionnelle, une humoristique, une factuelle",
            "Ajoutez une accroche provocante et une poétique",
            "Identifiez celle qui vous ferait acheter le produit"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    {
        "action_id": "action_creativity_016",
        "title": "Contrainte Oulipo",
        "description": "Écrivez un paragraphe sans utiliser la lettre E pour stimuler votre inventivité linguistique.",
        "category": "creativity",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "high",
        "instructions": [
            "Choisissez un sujet simple (votre journée, un souvenir)",
            "Écrivez 4 à 5 phrases sans jamais utiliser la lettre E",
            "Remplacez chaque mot contenant un E par un synonyme valide",
            "Relisez pour vérifier la cohérence et la fluidité"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    {
        "action_id": "action_creativity_017",
        "title": "Lettre au futur",
        "description": "Écrivez une courte lettre à vous-même dans 6 mois pour ancrer vos aspirations.",
        "category": "creativity",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "low",
        "instructions": [
            "Commencez par décrire où vous êtes et comment vous vous sentez",
            "Mentionnez un défi actuel que vous espérez avoir surmonté",
            "Partagez un conseil que vous aimeriez vous rappeler",
            "Terminez par une question à laquelle votre futur vous répondra"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    {
        "action_id": "action_creativity_018",
        "title": "Réécriture de titre",
        "description": "Prenez un titre d'article et réécrivez-le de 5 façons différentes.",
        "category": "creativity",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Trouvez un titre d'article sur votre fil d'actualité",
            "Réécrivez-le en version mystérieuse, drôle et dramatique",
            "Ajoutez une version minimaliste (3 mots max) et une version question",
            "Analysez quel style capte le mieux l'attention"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    {
        "action_id": "action_creativity_019",
        "title": "Monologue intérieur",
        "description": "Transcrivez votre flux de pensées brut pendant 3 minutes sans filtre ni censure.",
        "category": "creativity",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Mettez un minuteur de 3 minutes",
            "Écrivez tout ce qui vous passe par la tête sans vous arrêter",
            "Ne corrigez ni l'orthographe ni la grammaire",
            "Relisez et surlignez une idée surprenante à explorer"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    {
        "action_id": "action_creativity_020",
        "title": "Métaphore vivante",
        "description": "Décrivez votre journée actuelle comme un phénomène météo pour enrichir votre langage figuré.",
        "category": "creativity",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Choisissez un phénomène météo qui représente votre journée",
            "Écrivez 3 phrases utilisant cette métaphore de façon concrète",
            "Étendez la métaphore à vos émotions et interactions",
            "Trouvez une deuxième métaphore opposée pour le contraste"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    # --- Musical / Audio ---
    {
        "action_id": "action_creativity_021",
        "title": "Rythme corporel",
        "description": "Créez un rythme percussif avec votre corps pour réveiller votre musicalité naturelle.",
        "category": "creativity",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "high",
        "instructions": [
            "Tapez un rythme simple avec vos mains sur vos cuisses",
            "Ajoutez un claquement de doigts sur les temps faibles",
            "Intégrez un tapement de pied pour la basse",
            "Variez le tempo : lent, rapide, puis revenez au rythme initial"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    {
        "action_id": "action_creativity_022",
        "title": "Écoute architecturale",
        "description": "Analysez la structure d'un morceau de musique comme un architecte analyserait un bâtiment.",
        "category": "creativity",
        "duration_min": 4,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Choisissez un morceau que vous connaissez bien",
            "Écoutez en identifiant les blocs (intro, couplet, refrain, pont)",
            "Notez quels instruments apparaissent ou disparaissent à chaque transition",
            "Dessinez un schéma visuel de la structure du morceau"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    {
        "action_id": "action_creativity_023",
        "title": "Mélodie de rue",
        "description": "Écoutez les sons ambiants et transformez-les mentalement en mélodie.",
        "category": "creativity",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Fermez les yeux et écoutez votre environnement pendant 1 minute",
            "Identifiez 3 sons récurrents et attribuez-leur une note musicale",
            "Fredonnez la mélodie que ces sons créent ensemble",
            "Ajoutez un rythme en tapant du pied pour accompagner"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    {
        "action_id": "action_creativity_024",
        "title": "Bain sonore actif",
        "description": "Plongez dans un morceau instrumental en vous concentrant sur un seul instrument.",
        "category": "creativity",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "low",
        "instructions": [
            "Lancez un morceau avec plusieurs instruments",
            "Premier passage : suivez uniquement la ligne de basse",
            "Deuxième passage : concentrez-vous sur la batterie ou les percussions",
            "Notez comment chaque instrument change votre perception du morceau"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    {
        "action_id": "action_creativity_025",
        "title": "Fredonnement inventif",
        "description": "Inventez une mélodie de 8 notes et développez-la en variations successives.",
        "category": "creativity",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "medium",
        "instructions": [
            "Fredonnez 8 notes au hasard et mémorisez la séquence",
            "Répétez en changeant le rythme (plus lent, syncopé)",
            "Inversez l'ordre des notes pour créer une variation",
            "Combinez la version originale et inversée en une phrase musicale"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    # --- Sound meditation ---
    {
        "action_id": "action_creativity_026",
        "title": "Silence cartographié",
        "description": "Cartographiez tous les micro-sons dans un moment de silence apparent.",
        "category": "creativity",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Installez-vous dans un endroit calme et fermez les yeux",
            "Pendant 2 minutes, comptez chaque son distinct que vous percevez",
            "Classez-les par distance : proche, moyen, lointain",
            "Dessinez une carte sonore avec vous au centre"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    {
        "action_id": "action_creativity_027",
        "title": "Beatbox minimal",
        "description": "Apprenez 3 sons de beatbox basiques pour explorer la percussion vocale.",
        "category": "creativity",
        "duration_min": 4,
        "duration_max": 7,
        "energy_level": "high",
        "instructions": [
            "Pratiquez le kick : dites 'B' en expirant fort avec les lèvres",
            "Ajoutez le hi-hat : dites 'Ts' entre les dents serrées",
            "Intégrez la caisse claire : dites 'Pf' en soufflant sur le côté",
            "Combinez les 3 sons en un pattern répétitif de 4 temps"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    {
        "action_id": "action_creativity_028",
        "title": "Playlist émotionnelle",
        "description": "Créez une mini-playlist de 3 morceaux qui racontent une histoire émotionnelle.",
        "category": "creativity",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "low",
        "instructions": [
            "Choisissez une émotion de départ et une émotion d'arrivée",
            "Trouvez un morceau qui représente le point de départ",
            "Sélectionnez un morceau de transition et un d'arrivée",
            "Écoutez les 3 enchaînés et notez le voyage émotionnel ressenti"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    {
        "action_id": "action_creativity_029",
        "title": "Tempo quotidien",
        "description": "Identifiez le tempo naturel de vos activités pour prendre conscience de votre rythme interne.",
        "category": "creativity",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Tapez du pied au rythme de votre pas naturel",
            "Comptez les battements par minute (votre tempo personnel)",
            "Cherchez un morceau de musique au même tempo",
            "Notez comment ce tempo reflète votre état d'énergie actuel"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    {
        "action_id": "action_creativity_030",
        "title": "Voix transformée",
        "description": "Lisez un texte court en variant radicalement votre voix pour explorer l'expressivité vocale.",
        "category": "creativity",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "high",
        "instructions": [
            "Choisissez une phrase de 10 à 15 mots",
            "Dites-la d'abord en chuchotant, puis en voix grave théâtrale",
            "Répétez en imitant un présentateur TV, puis un poète",
            "Identifiez quelle version transmet le mieux le sens de la phrase"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    # --- Problem-solving ---
    {
        "action_id": "action_creativity_031",
        "title": "Pensée inversée",
        "description": "Résolvez un problème en cherchant d'abord comment l'aggraver.",
        "category": "creativity",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Identifiez un problème actuel simple à résoudre",
            "Listez 5 façons de rendre ce problème encore pire",
            "Inversez chaque idée pour obtenir une solution potentielle",
            "Choisissez la solution inversée la plus prometteuse"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    {
        "action_id": "action_creativity_032",
        "title": "Brainstorm solo",
        "description": "Générez 20 idées en 5 minutes sans filtre pour dépasser vos premières évidences.",
        "category": "creativity",
        "duration_min": 4,
        "duration_max": 7,
        "energy_level": "high",
        "instructions": [
            "Définissez un défi ou une question en une phrase",
            "Écrivez 20 idées en 5 minutes sans juger leur qualité",
            "Encerclez les 3 idées les plus surprenantes de la liste",
            "Combinez 2 idées surprenantes en une solution hybride"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    {
        "action_id": "action_creativity_033",
        "title": "Carte mentale flash",
        "description": "Créez une carte mentale en 4 minutes pour organiser vos idées visuellement.",
        "category": "creativity",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "medium",
        "instructions": [
            "Écrivez un thème central au milieu d'une feuille",
            "Tracez 4 branches principales avec des sous-thèmes",
            "Ajoutez 2 à 3 mots-clés par branche en 2 minutes",
            "Reliez les idées qui se connectent entre différentes branches"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    {
        "action_id": "action_creativity_034",
        "title": "Contrainte créative",
        "description": "Résolvez un problème avec une contrainte absurde pour forcer l'innovation.",
        "category": "creativity",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "high",
        "instructions": [
            "Choisissez un problème quotidien à résoudre",
            "Ajoutez une contrainte absurde (sans utiliser d'argent, en 30 secondes, avec les yeux fermés)",
            "Trouvez 3 solutions qui respectent cette contrainte",
            "Évaluez si une de ces solutions fonctionne aussi sans la contrainte"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    {
        "action_id": "action_creativity_035",
        "title": "Analogie forcée",
        "description": "Trouvez des solutions à un problème en l'analogisant avec un domaine complètement différent.",
        "category": "creativity",
        "duration_min": 4,
        "duration_max": 7,
        "energy_level": "medium",
        "instructions": [
            "Formulez votre problème en une question claire",
            "Choisissez un domaine au hasard (cuisine, sport, nature, musique)",
            "Demandez-vous comment ce domaine résout des problèmes similaires",
            "Transposez la solution trouvée à votre problème original"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    {
        "action_id": "action_creativity_036",
        "title": "Six chapeaux express",
        "description": "Analysez une idée sous 6 angles différents en changeant de perspective toutes les minutes.",
        "category": "creativity",
        "duration_min": 5,
        "duration_max": 8,
        "energy_level": "high",
        "instructions": [
            "Choisissez une idée ou décision à évaluer",
            "Minute 1-2 : listez les faits objectifs, puis les émotions ressenties",
            "Minute 3-4 : notez les risques potentiels, puis les bénéfices possibles",
            "Minute 5-6 : proposez des alternatives créatives, puis une conclusion structurée"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    {
        "action_id": "action_creativity_037",
        "title": "SCAMPER rapide",
        "description": "Appliquez la méthode SCAMPER à un objet quotidien pour générer des innovations.",
        "category": "creativity",
        "duration_min": 5,
        "duration_max": 9,
        "energy_level": "high",
        "instructions": [
            "Choisissez un objet du quotidien (stylo, tasse, sac)",
            "Substituer : par quoi remplacer un composant ? Combiner : fusionner avec un autre objet ?",
            "Adapter : comment l'utiliser autrement ? Modifier : changer la taille ou la forme ?",
            "Éliminer : que supprimer pour simplifier ? Réorganiser : inverser un processus ?"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    {
        "action_id": "action_creativity_038",
        "title": "Question naïve",
        "description": "Posez-vous 5 questions d'enfant sur un sujet que vous croyez bien connaître.",
        "category": "creativity",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "medium",
        "instructions": [
            "Choisissez un sujet de votre domaine d'expertise",
            "Posez 5 questions commençant par 'Pourquoi' comme un enfant de 5 ans",
            "Essayez de répondre simplement à chaque question",
            "Notez les questions auxquelles vous ne pouvez pas répondre simplement"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    {
        "action_id": "action_creativity_039",
        "title": "Connexion improbable",
        "description": "Reliez deux concepts sans rapport pour créer une idée originale.",
        "category": "creativity",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "medium",
        "instructions": [
            "Ouvrez un dictionnaire et pointez 2 mots au hasard",
            "Trouvez 3 points communs entre ces mots, même tirés par les cheveux",
            "Imaginez un produit ou service qui combine les deux concepts",
            "Décrivez votre invention en une phrase accrocheuse"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    {
        "action_id": "action_creativity_040",
        "title": "Défi des limites",
        "description": "Listez toutes les hypothèses derrière un problème puis remettez-les en question une par une.",
        "category": "creativity",
        "duration_min": 4,
        "duration_max": 7,
        "energy_level": "medium",
        "instructions": [
            "Formulez un problème ou objectif en une phrase",
            "Listez 5 hypothèses implicites dans cette formulation",
            "Pour chaque hypothèse, demandez-vous : et si c'était faux ?",
            "Reformulez le problème en éliminant l'hypothèse la plus limitante"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    # --- Design thinking ---
    {
        "action_id": "action_creativity_041",
        "title": "Empathie éclair",
        "description": "Imaginez la journée d'une personne très différente de vous pour élargir votre perspective.",
        "category": "creativity",
        "duration_min": 4,
        "duration_max": 7,
        "energy_level": "medium",
        "instructions": [
            "Pensez à un utilisateur type de votre produit ou service",
            "Imaginez son réveil : quels sont ses 3 premiers soucis ?",
            "Décrivez un moment frustrant dans sa journée lié à votre domaine",
            "Notez une idée pour améliorer ce moment spécifique"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    {
        "action_id": "action_creativity_042",
        "title": "Prototype papier",
        "description": "Esquissez une interface ou un objet en 5 minutes avec du papier et un crayon.",
        "category": "creativity",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "high",
        "instructions": [
            "Identifiez une fonctionnalité à concevoir ou améliorer",
            "Dessinez 3 versions grossières sur des post-its séparés",
            "Choisissez les meilleurs éléments de chaque version",
            "Combinez-les en un prototype final sur une feuille A4"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    {
        "action_id": "action_creativity_043",
        "title": "Feedback fictif",
        "description": "Imaginez le retour de 3 utilisateurs différents sur votre dernier travail.",
        "category": "creativity",
        "duration_min": 4,
        "duration_max": 7,
        "energy_level": "medium",
        "instructions": [
            "Choisissez votre dernier livrable ou projet",
            "Inventez 3 personas : un enthousiaste, un sceptique, un novice",
            "Écrivez un retour de 2 phrases pour chaque persona",
            "Identifiez le point commun dans les critiques des 3 personas"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    {
        "action_id": "action_creativity_044",
        "title": "Parcours utilisateur",
        "description": "Tracez le parcours émotionnel d'un utilisateur à travers votre produit ou service.",
        "category": "creativity",
        "duration_min": 5,
        "duration_max": 9,
        "energy_level": "high",
        "instructions": [
            "Listez les 5 étapes principales de l'expérience utilisateur",
            "Pour chaque étape, notez l'émotion dominante ressentie",
            "Tracez une courbe émotionnelle (hauts et bas) sur un graphique",
            "Identifiez le point le plus bas et proposez une amélioration"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    {
        "action_id": "action_creativity_045",
        "title": "Design sprint solo",
        "description": "Appliquez les 5 étapes d'un design sprint en version micro sur un problème simple.",
        "category": "creativity",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "high",
        "instructions": [
            "Minute 1 : comprenez le problème et définissez l'objectif",
            "Minute 2 : esquissez 3 solutions rapides en croquis",
            "Minute 3 : choisissez la meilleure et détaillez-la",
            "Minutes 4-5 : imaginez comment la tester avec un utilisateur réel"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    {
        "action_id": "action_creativity_046",
        "title": "Point de friction",
        "description": "Identifiez et documentez un point de friction dans un outil que vous utilisez chaque jour.",
        "category": "creativity",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Pensez à un outil ou app que vous utilisez quotidiennement",
            "Identifiez le moment exact où vous ressentez de la frustration",
            "Décrivez le problème en termes d'action utilisateur et de résultat attendu",
            "Proposez une solution en un croquis ou une phrase"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    {
        "action_id": "action_creativity_047",
        "title": "Itération visuelle",
        "description": "Redessinez 3 fois le même concept en améliorant un aspect à chaque itération.",
        "category": "creativity",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "high",
        "instructions": [
            "Dessinez une première version rapide d'une idée visuelle",
            "Identifiez le point faible principal de ce premier dessin",
            "Redessinez en corrigeant ce défaut, puis répétez une troisième fois",
            "Comparez les 3 versions et notez la progression"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    {
        "action_id": "action_creativity_048",
        "title": "Test des 5 secondes",
        "description": "Montrez un visuel 5 secondes à quelqu'un et demandez ce qu'il a retenu.",
        "category": "creativity",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "medium",
        "instructions": [
            "Préparez un visuel (slide, design, affiche) à tester",
            "Montrez-le 5 secondes à un collègue ou ami",
            "Demandez : quel est le message principal retenu ?",
            "Notez les écarts entre votre intention et la perception réelle"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    {
        "action_id": "action_creativity_049",
        "title": "Audit sensoriel",
        "description": "Évaluez une expérience avec les 5 sens pour découvrir des améliorations cachées.",
        "category": "creativity",
        "duration_min": 4,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Choisissez une expérience quotidienne (café du matin, trajet, réunion)",
            "Évaluez-la sur chaque sens : vue, son, toucher, goût, odorat",
            "Identifiez le sens le plus négligé dans cette expérience",
            "Proposez une amélioration ciblant ce sens spécifique"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    {
        "action_id": "action_creativity_050",
        "title": "Contrainte matérielle",
        "description": "Redesignez un objet en vous limitant à un seul matériau pour stimuler l'ingéniosité.",
        "category": "creativity",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Choisissez un objet complexe (lampe, rangement, outil)",
            "Choisissez un seul matériau (papier, bois, métal, tissu)",
            "Dessinez une version de l'objet entièrement dans ce matériau",
            "Notez les compromis et innovations que la contrainte a générés"
        ],
        "is_premium": True,
        "icon": "palette"
    },
    # =====================================================================
    # FITNESS (50 actions) - icon: "dumbbell"
    # =====================================================================
    # --- Desk stretching ---
    {
        "action_id": "action_fitness_001",
        "title": "Libération cervicale",
        "description": "Relâchez les tensions du cou avec 4 étirements doux en position assise.",
        "category": "fitness",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Inclinez lentement la tête vers l'épaule droite, maintenez 15 secondes",
            "Répétez de l'autre côté en respirant profondément",
            "Faites 5 rotations lentes du cou dans le sens horaire",
            "Terminez par 5 rotations dans le sens anti-horaire"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_fitness_002",
        "title": "Poignets détendus",
        "description": "Soulagez vos poignets fatigués par le clavier avec des étirements ciblés.",
        "category": "fitness",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Tendez le bras droit, paume vers le haut, tirez les doigts vers le bas",
            "Maintenez 15 secondes puis retournez la main paume vers le bas",
            "Répétez avec le bras gauche",
            "Faites 10 rotations de chaque poignet dans chaque direction"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_fitness_003",
        "title": "Ouverture des hanches",
        "description": "Déverrouillez vos hanches après une longue période assise avec des mouvements doux.",
        "category": "fitness",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Assis, posez la cheville droite sur le genou gauche en figure 4",
            "Penchez-vous doucement vers l'avant, maintenez 20 secondes",
            "Répétez de l'autre côté",
            "Terminez debout avec 10 cercles de hanches dans chaque direction"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_fitness_004",
        "title": "Reset posture",
        "description": "Corrigez votre posture assise en 3 minutes avec des ajustements simples.",
        "category": "fitness",
        "duration_min": 2,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Levez-vous et secouez tout le corps pendant 15 secondes",
            "Rasseyez-vous en plaçant les pieds à plat, genoux à 90 degrés",
            "Roulez les épaules en arrière 10 fois et alignez les oreilles au-dessus des épaules",
            "Contractez les abdominaux 5 secondes, relâchez, répétez 5 fois"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_fitness_005",
        "title": "Étirement papillon",
        "description": "Ouvrez le haut du dos et les épaules avec l'étirement du papillon debout.",
        "category": "fitness",
        "duration_min": 2,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Debout, placez les mains derrière la tête, coudes écartés",
            "Rapprochez les coudes devant votre visage en expirant",
            "Ouvrez grand les coudes en arrière en inspirant",
            "Répétez 10 fois lentement en synchronisant avec la respiration"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_fitness_006",
        "title": "Torsion assise",
        "description": "Mobilisez votre colonne vertébrale avec des torsions douces depuis votre chaise.",
        "category": "fitness",
        "duration_min": 2,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Assis bien droit, croisez la jambe droite sur la gauche",
            "Placez la main gauche sur le genou droit et tournez le buste à droite",
            "Maintenez 20 secondes en respirant profondément",
            "Répétez de l'autre côté, en allant un peu plus loin à chaque expiration"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_fitness_007",
        "title": "Doigts de pianiste",
        "description": "Renforcez et assouplissez vos doigts pour prévenir les douleurs liées à la frappe.",
        "category": "fitness",
        "duration_min": 2,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Écartez tous les doigts au maximum pendant 5 secondes, puis fermez le poing",
            "Répétez 10 fois en alternant ouverture et fermeture",
            "Tapotez chaque doigt contre le pouce rapidement pendant 15 secondes",
            "Étirez chaque doigt individuellement en le tirant doucement vers l'arrière"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_fitness_008",
        "title": "Épaules fondantes",
        "description": "Dissolvez les tensions dans les épaules avec des mouvements progressifs.",
        "category": "fitness",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Montez les épaules vers les oreilles en inspirant, maintenez 5 secondes",
            "Relâchez d'un coup en expirant, répétez 5 fois",
            "Faites 10 roulements d'épaules vers l'arrière en grands cercles",
            "Terminez en serrant les omoplates ensemble 5 secondes, 5 répétitions"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_fitness_009",
        "title": "Mollets au bureau",
        "description": "Activez vos mollets sous le bureau pour relancer la circulation sanguine.",
        "category": "fitness",
        "duration_min": 2,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Assis, pieds à plat au sol, montez sur la pointe des pieds",
            "Maintenez 3 secondes en haut, redescendez lentement",
            "Répétez 15 fois, puis inversez : talons au sol, orteils levés",
            "Terminez par 10 flexions alternées rapides pointe-talon"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_fitness_010",
        "title": "Étirement chat-vache",
        "description": "Reproduisez le mouvement yoga chat-vache assis pour mobiliser votre dos.",
        "category": "fitness",
        "duration_min": 2,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Assis au bord de la chaise, mains sur les genoux",
            "Inspirez en creusant le dos et levant le menton (vache)",
            "Expirez en arrondissant le dos et rentrant le menton (chat)",
            "Alternez 10 fois en synchronisant avec une respiration lente"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    # --- Micro-cardio ---
    {
        "action_id": "action_fitness_011",
        "title": "Jumping jacks express",
        "description": "Boostez votre fréquence cardiaque avec des jumping jacks par intervalles.",
        "category": "fitness",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "high",
        "instructions": [
            "Faites 20 jumping jacks à rythme modéré pour vous échauffer",
            "Repos 15 secondes, puis 20 jumping jacks à intensité maximale",
            "Repos 15 secondes, puis 15 jumping jacks au rythme modéré",
            "Terminez par 30 secondes de marche sur place pour récupérer"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_fitness_012",
        "title": "Montée de marches",
        "description": "Utilisez un escalier pour un mini-cardio intense et efficace.",
        "category": "fitness",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "high",
        "instructions": [
            "Trouvez un escalier d'au moins un étage",
            "Montez à allure rapide, redescendez en marchant",
            "Répétez 3 à 5 fois selon votre forme",
            "Terminez par 1 minute de marche lente pour récupérer"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_fitness_013",
        "title": "Power walk 5 min",
        "description": "Marchez rapidement autour du bâtiment pour oxygéner votre cerveau.",
        "category": "fitness",
        "duration_min": 4,
        "duration_max": 7,
        "energy_level": "medium",
        "instructions": [
            "Sortez ou marchez dans un couloir à un rythme soutenu",
            "Balancez activement les bras pour augmenter l'intensité",
            "Accélérez pendant 30 secondes toutes les 2 minutes",
            "Ralentissez progressivement pendant la dernière minute"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_fitness_014",
        "title": "Danse libre",
        "description": "Dansez librement sur un morceau énergique pour libérer les endorphines.",
        "category": "fitness",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "high",
        "instructions": [
            "Mettez votre morceau préféré avec un bon tempo",
            "Dansez sans réfléchir, bougez tout le corps",
            "Changez de niveau : au sol, accroupi, debout, en sautant",
            "Terminez par un étirement des bras vers le plafond"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_fitness_015",
        "title": "Course sur place",
        "description": "Courez sur place avec des variations pour un cardio sans espace.",
        "category": "fitness",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "high",
        "instructions": [
            "Commencez par 30 secondes de jogging léger sur place",
            "Montez les genoux le plus haut possible pendant 20 secondes",
            "Passez aux talons-fesses pendant 20 secondes",
            "Alternez entre les deux pendant 2 minutes puis récupérez"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_fitness_016",
        "title": "Burpees allégés",
        "description": "Réalisez des burpees modifiés accessibles à tous les niveaux.",
        "category": "fitness",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "high",
        "instructions": [
            "Debout, descendez en squat puis posez les mains au sol",
            "Reculez un pied puis l'autre en position de planche",
            "Ramenez les pieds vers les mains et remontez debout",
            "Faites 5 à 10 répétitions à votre rythme avec 10 secondes de repos entre chaque"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_fitness_017",
        "title": "Shadow boxing",
        "description": "Enchaînez des combinaisons de boxe dans le vide pour un cardio fun et complet.",
        "category": "fitness",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "high",
        "instructions": [
            "Adoptez une garde de boxeur : pieds décalés, poings au menton",
            "Enchaînez jab-cross (gauche-droite) pendant 30 secondes",
            "Ajoutez des esquives en fléchissant les genoux entre les coups",
            "Terminez par 30 secondes de combinaisons libres à haute intensité"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_fitness_018",
        "title": "Skip dynamique",
        "description": "Sautillez avec des variations pour un cardio doux et joyeux.",
        "category": "fitness",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "medium",
        "instructions": [
            "Sautillez sur place en levant les genoux alternativement",
            "Ajoutez des mouvements de bras : bras au ciel, sur les côtés",
            "Variez : petits sauts rapides puis grands sauts lents",
            "Terminez par 20 secondes de marche rapide sur place"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_fitness_019",
        "title": "Corde invisible",
        "description": "Sautez à la corde sans corde pour un cardio discret et efficace.",
        "category": "fitness",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "high",
        "instructions": [
            "Mimez le mouvement de rotation de la corde avec les poignets",
            "Sautez légèrement sur la pointe des pieds à un rythme régulier",
            "Après 30 secondes, passez au saut pied alterné",
            "Alternez 30 secondes d'effort et 15 secondes de repos, 4 fois"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_fitness_020",
        "title": "Sprint couloir",
        "description": "Faites des allers-retours rapides dans un couloir pour un HIIT improvisé.",
        "category": "fitness",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "high",
        "instructions": [
            "Choisissez un couloir ou un espace de 10 à 15 mètres",
            "Sprintez d'un bout à l'autre en touchant le sol à chaque extrémité",
            "Faites 4 allers-retours avec 20 secondes de pause entre chaque",
            "Terminez par 1 minute de marche lente et d'étirements debout"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    # --- Strength micro-sets ---
    {
        "action_id": "action_fitness_021",
        "title": "Pompes murales",
        "description": "Renforcez le haut du corps avec des pompes contre le mur, adaptées à tous.",
        "category": "fitness",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "medium",
        "instructions": [
            "Placez-vous face à un mur, bras tendus, mains à hauteur d'épaules",
            "Fléchissez les bras pour rapprocher la poitrine du mur",
            "Repoussez lentement, contractez les abdominaux",
            "Faites 3 séries de 10 répétitions avec 15 secondes de repos"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_fitness_022",
        "title": "Planche défi",
        "description": "Tenez la planche en progressant vers votre record personnel.",
        "category": "fitness",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "medium",
        "instructions": [
            "Mettez-vous en position de planche sur les avant-bras",
            "Alignez tête, dos et talons en une ligne droite",
            "Contractez les abdominaux et les fessiers, respirez normalement",
            "Tenez le plus longtemps possible et notez votre temps pour la prochaine fois"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_fitness_023",
        "title": "Squats progressifs",
        "description": "Enchaînez des squats avec des variations de tempo pour cibler différents muscles.",
        "category": "fitness",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "medium",
        "instructions": [
            "Faites 10 squats classiques à rythme normal, pieds largeur d'épaules",
            "Enchaînez avec 5 squats très lents (4 secondes à la descente)",
            "Ajoutez 5 squats avec pause de 3 secondes en bas",
            "Terminez par 5 squats sautés si votre niveau le permet"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_fitness_024",
        "title": "Chaise imaginaire",
        "description": "Renforcez vos cuisses avec l'exercice de la chaise contre le mur.",
        "category": "fitness",
        "duration_min": 2,
        "duration_max": 5,
        "energy_level": "medium",
        "instructions": [
            "Adossez-vous à un mur et descendez en position assise (cuisses parallèles au sol)",
            "Les genoux sont à 90 degrés, les pieds écartés largeur d'épaules",
            "Tenez la position en respirant régulièrement",
            "Essayez 30 secondes, repos 15 secondes, répétez 3 fois"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_fitness_025",
        "title": "Dips sur chaise",
        "description": "Travaillez les triceps en utilisant une chaise stable comme support.",
        "category": "fitness",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "medium",
        "instructions": [
            "Asseyez-vous au bord d'une chaise stable, mains agrippant le rebord",
            "Avancez les fesses devant la chaise, jambes tendues ou pliées",
            "Descendez en fléchissant les coudes à 90 degrés puis remontez",
            "Faites 3 séries de 8 répétitions avec 15 secondes de repos"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_fitness_026",
        "title": "Gainage latéral",
        "description": "Renforcez vos obliques avec le gainage latéral en alternant les côtés.",
        "category": "fitness",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "medium",
        "instructions": [
            "Allongez-vous sur le côté droit, en appui sur l'avant-bras",
            "Soulevez les hanches pour aligner le corps en ligne droite",
            "Tenez 20 secondes puis changez de côté",
            "Faites 3 séries de chaque côté avec 10 secondes de repos"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_fitness_027",
        "title": "Fentes alternées",
        "description": "Sculptez vos jambes avec des fentes avant en alternant les côtés.",
        "category": "fitness",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "medium",
        "instructions": [
            "Debout, faites un grand pas en avant avec la jambe droite",
            "Descendez le genou arrière vers le sol sans le toucher",
            "Revenez en position initiale et changez de jambe",
            "Alternez 10 fentes de chaque côté, 2 séries avec repos entre"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_fitness_028",
        "title": "Pompes diamant",
        "description": "Variez vos pompes avec la position diamant pour cibler les triceps.",
        "category": "fitness",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "high",
        "instructions": [
            "En position de pompe, rapprochez les mains en formant un losange",
            "Descendez lentement en gardant les coudes le long du corps",
            "Remontez en expirant, contractez les triceps en haut",
            "Faites 3 séries de 5 à 8 répétitions (genoux au sol si nécessaire)"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_fitness_029",
        "title": "Pont fessier",
        "description": "Activez et renforcez les fessiers avec le hip bridge au sol.",
        "category": "fitness",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "medium",
        "instructions": [
            "Allongez-vous sur le dos, genoux pliés, pieds à plat au sol",
            "Soulevez les hanches en contractant les fessiers jusqu'à former une ligne droite",
            "Tenez 3 secondes en haut, redescendez sans toucher le sol",
            "Faites 15 répétitions, puis 10 avec un pied levé de chaque côté"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_fitness_030",
        "title": "Superman express",
        "description": "Renforcez le bas du dos et les muscles posturaux avec le superman.",
        "category": "fitness",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "medium",
        "instructions": [
            "Allongez-vous face au sol, bras tendus devant vous",
            "Soulevez simultanément bras et jambes de quelques centimètres",
            "Tenez 5 secondes en contractant le bas du dos et les fessiers",
            "Relâchez et répétez 10 fois avec une pause de 3 secondes"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    # --- Mobility & flexibility ---
    {
        "action_id": "action_fitness_031",
        "title": "Flow matinal",
        "description": "Enchaînez 5 mouvements dynamiques pour réveiller toutes les articulations.",
        "category": "fitness",
        "duration_min": 4,
        "duration_max": 7,
        "energy_level": "medium",
        "instructions": [
            "Faites 10 cercles de bras vers l'avant puis vers l'arrière",
            "Enchaînez 10 rotations du tronc, bras détendus",
            "Ajoutez 10 cercles de hanches dans chaque direction",
            "Terminez par 10 flexions de chevilles en montant sur la pointe"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_fitness_032",
        "title": "Cercles articulaires",
        "description": "Mobilisez chaque articulation du corps de la tête aux pieds.",
        "category": "fitness",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "high",
        "instructions": [
            "Commencez par 5 rotations lentes de la tête dans chaque sens",
            "Descendez : épaules, coudes, poignets (5 rotations chaque)",
            "Continuez : hanches, genoux, chevilles (5 rotations chaque)",
            "Remontez avec des mouvements plus amples pour la deuxième série"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_fitness_033",
        "title": "Yoga du bureau",
        "description": "Réalisez une mini-séquence de yoga adaptée à l'espace réduit d'un bureau.",
        "category": "fitness",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "high",
        "instructions": [
            "Debout, levez les bras en inspirant (posture de la montagne)",
            "Pliez-vous en avant en expirant, touchez vos tibias ou le sol",
            "Remontez vertèbre par vertèbre en déroulant lentement le dos",
            "Répétez 5 fois puis terminez en posture de l'arbre (30 secondes par jambe)"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_fitness_034",
        "title": "Ouverture thoracique",
        "description": "Ouvrez la cage thoracique et corrigez le dos voûté avec des rotations.",
        "category": "fitness",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "medium",
        "instructions": [
            "À quatre pattes, placez la main droite derrière la tête",
            "Tournez le buste pour amener le coude vers le plafond en inspirant",
            "Redescendez le coude vers le sol en expirant",
            "Faites 10 répétitions de chaque côté en cherchant plus d'amplitude"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_fitness_035",
        "title": "Grenouille profonde",
        "description": "Étirez profondément les adducteurs avec la posture de la grenouille.",
        "category": "fitness",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "high",
        "instructions": [
            "À quatre pattes, écartez progressivement les genoux",
            "Gardez les pieds alignés avec les genoux, orteils vers l'extérieur",
            "Descendez doucement les hanches vers le sol en contrôlant",
            "Maintenez la position 30 secondes, respirez profondément et relâchez"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_fitness_036",
        "title": "Salutation express",
        "description": "Réalisez une demi-salutation au soleil adaptée en 3 minutes.",
        "category": "fitness",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "medium",
        "instructions": [
            "Debout, inspirez en levant les bras au ciel, paumes jointes",
            "Expirez en pliant vers l'avant, mains vers le sol",
            "Inspirez en relevant le buste à mi-chemin, dos plat",
            "Expirez en repliant complètement, puis remontez bras au ciel. Répétez 5 fois"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_fitness_037",
        "title": "Étirement piriforme",
        "description": "Soulagez les tensions dans le muscle piriforme pour prévenir la sciatique.",
        "category": "fitness",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Allongé sur le dos, croisez la cheville droite sur le genou gauche",
            "Tirez le genou gauche vers votre poitrine avec les deux mains",
            "Maintenez 30 secondes en respirant calmement",
            "Changez de côté et répétez, en allant un peu plus profondément"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_fitness_038",
        "title": "Vague spinale",
        "description": "Articulez votre colonne vertèbre par vertèbre pour une mobilité optimale.",
        "category": "fitness",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "high",
        "instructions": [
            "Debout, pieds joints, laissez tomber le menton vers la poitrine",
            "Déroulez le dos vertèbre par vertèbre vers le sol en expirant",
            "Arrivé en bas, laissez les bras pendre, respirez 3 fois",
            "Remontez vertèbre par vertèbre en inspirant lentement"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_fitness_039",
        "title": "Fente du coureur",
        "description": "Étirez profondément les fléchisseurs de hanche avec la fente basse.",
        "category": "fitness",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "medium",
        "instructions": [
            "Depuis debout, faites un grand pas en avant, genou arrière au sol",
            "Poussez les hanches vers l'avant en gardant le buste droit",
            "Levez le bras du côté du genou arrière au-dessus de la tête",
            "Maintenez 30 secondes puis changez de côté"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_fitness_040",
        "title": "Rotation monde",
        "description": "Réalisez des rotations du monde entier pour mobiliser hanches et épaules.",
        "category": "fitness",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "medium",
        "instructions": [
            "Debout, pieds écartés, faites de grands cercles avec les bras tendus",
            "Suivez les mains du regard pour inclure la rotation du tronc",
            "Agrandissez les cercles en ajoutant une flexion de hanches",
            "Faites 5 rotations dans chaque sens en augmentant l'amplitude"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    # --- Active recovery ---
    {
        "action_id": "action_fitness_041",
        "title": "Respiration carrée",
        "description": "Utilisez la respiration carrée pour récupérer entre deux efforts.",
        "category": "fitness",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Inspirez par le nez pendant 4 secondes",
            "Retenez l'air pendant 4 secondes",
            "Expirez par la bouche pendant 4 secondes",
            "Retenez poumons vides 4 secondes, répétez 6 à 8 cycles"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_fitness_042",
        "title": "Scan post-effort",
        "description": "Scannez votre corps après un effort pour identifier les zones de tension.",
        "category": "fitness",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Allongez-vous ou asseyez-vous confortablement, yeux fermés",
            "Scannez mentalement des pieds à la tête en notant chaque sensation",
            "Identifiez les zones de tension ou d'inconfort",
            "Envoyez mentalement votre respiration vers ces zones pour les détendre"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_fitness_043",
        "title": "Douche froide mentale",
        "description": "Préparez-vous mentalement à l'exposition au froid avec une visualisation guidée.",
        "category": "fitness",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Asseyez-vous confortablement et fermez les yeux",
            "Visualisez une cascade d'eau fraîche tombant sur vos épaules",
            "Imaginez le froid se transformer en énergie revigorante",
            "Pratiquez 5 respirations profondes en imaginant l'eau froide sur votre peau"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_fitness_044",
        "title": "Auto-massage cou",
        "description": "Massez les points de tension du cou et des trapèzes avec vos doigts.",
        "category": "fitness",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "high",
        "instructions": [
            "Placez les doigts à la base du crâne, pressez et faites des petits cercles",
            "Descendez le long des muscles du cou en maintenant la pression",
            "Insistez sur les points douloureux avec une pression constante de 10 secondes",
            "Terminez par des pétrissages doux des trapèzes pendant 1 minute"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_fitness_045",
        "title": "Récupération jambes",
        "description": "Allégez vos jambes avec la posture jambes contre le mur.",
        "category": "fitness",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Allongez-vous et posez les jambes à la verticale contre un mur",
            "Rapprochez les fesses le plus possible du mur",
            "Respirez lentement et laissez le sang circuler en retour",
            "Restez 3 à 5 minutes pour un drainage complet"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_fitness_046",
        "title": "Rouleau improvise",
        "description": "Utilisez une balle de tennis pour masser les points de tension des pieds.",
        "category": "fitness",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "high",
        "instructions": [
            "Placez une balle de tennis sous votre pied droit",
            "Roulez lentement de l'avant du pied vers le talon avec pression",
            "Insistez sur les zones sensibles avec une pression circulaire",
            "Changez de pied après 2 minutes"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_fitness_047",
        "title": "Bras en croix",
        "description": "Étirez les pectoraux et les épaules pour ouvrir votre posture après l'effort.",
        "category": "fitness",
        "duration_min": 2,
        "duration_max": 5,
        "energy_level": "high",
        "instructions": [
            "Debout dans l'encadrement d'une porte, bras en T contre les montants",
            "Avancez un pied et penchez le buste vers l'avant doucement",
            "Sentez l'étirement dans les pectoraux, maintenez 20 secondes",
            "Variez la hauteur des bras (en Y puis en L) pour cibler des fibres différentes"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_fitness_048",
        "title": "Marche consciente",
        "description": "Marchez très lentement en pleine conscience de chaque mouvement musculaire.",
        "category": "fitness",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "high",
        "instructions": [
            "Debout, sentez le poids de votre corps sur vos pieds",
            "Faites un pas au ralenti en décomposant : talon, plante, orteils",
            "Percevez chaque muscle qui s'active dans la jambe et la hanche",
            "Continuez pendant 3 minutes en gardant une attention totale"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_fitness_049",
        "title": "Shakeout total",
        "description": "Secouez chaque partie du corps pour libérer les tensions accumulées.",
        "category": "fitness",
        "duration_min": 2,
        "duration_max": 5,
        "energy_level": "medium",
        "instructions": [
            "Secouez vigoureusement les mains pendant 15 secondes",
            "Ajoutez les bras, puis les épaules, laissez tout vibrer",
            "Secouez chaque jambe alternativement pendant 15 secondes",
            "Terminez en sautillant légèrement en secouant tout le corps 30 secondes"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    {
        "action_id": "action_fitness_050",
        "title": "Étirement global",
        "description": "Étirez la chaîne postérieure complète en un seul mouvement fluide.",
        "category": "fitness",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "medium",
        "instructions": [
            "Debout, inspirez en levant les bras puis expirez en vous pliant vers le sol",
            "Marchez les mains vers l'avant jusqu'à la position de planche",
            "Poussez les hanches vers le haut en V inversé (chien tête en bas)",
            "Marchez les pieds vers les mains et remontez lentement. Répétez 3 fois"
        ],
        "is_premium": True,
        "icon": "dumbbell"
    },
    # =====================================================================
    # MINDFULNESS (50 actions) - icon: "leaf"
    # =====================================================================
    # --- Breathing techniques ---
    {
        "action_id": "action_mindfulness_001",
        "title": "Box breathing",
        "description": "Pratiquez la respiration carrée utilisée par les Navy SEALs pour calmer le stress.",
        "category": "mindfulness",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Inspirez par le nez en comptant jusqu'à 4",
            "Retenez l'air en comptant jusqu'à 4",
            "Expirez lentement par la bouche en comptant jusqu'à 4",
            "Retenez poumons vides en comptant jusqu'à 4, répétez 8 cycles"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    {
        "action_id": "action_mindfulness_002",
        "title": "Respiration 4-7-8",
        "description": "Utilisez le ratio 4-7-8 pour activer votre système nerveux parasympathique.",
        "category": "mindfulness",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Asseyez-vous confortablement et placez la langue derrière les incisives",
            "Inspirez silencieusement par le nez pendant 4 secondes",
            "Retenez votre souffle pendant 7 secondes",
            "Expirez complètement par la bouche en 8 secondes, répétez 4 cycles"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    {
        "action_id": "action_mindfulness_003",
        "title": "Narine alternée",
        "description": "Équilibrez vos hémisphères cérébraux avec la respiration narine alternée.",
        "category": "mindfulness",
        "duration_min": 4,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Fermez la narine droite avec le pouce et inspirez par la gauche",
            "Fermez les deux narines et retenez 2 secondes",
            "Relâchez la droite et expirez par la narine droite",
            "Inspirez par la droite, fermez, expirez par la gauche. Répétez 8 cycles"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    {
        "action_id": "action_mindfulness_004",
        "title": "Souffle du lion",
        "description": "Libérez les tensions faciales et mentales avec cette respiration énergisante.",
        "category": "mindfulness",
        "duration_min": 2,
        "duration_max": 5,
        "energy_level": "high",
        "instructions": [
            "Inspirez profondément par le nez en ouvrant grand les yeux",
            "Expirez fortement par la bouche en tirant la langue et en grognant",
            "Écarquillez les yeux et tendez les doigts pendant l'expiration",
            "Répétez 5 fois en augmentant l'intensité à chaque fois"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    {
        "action_id": "action_mindfulness_005",
        "title": "Respiration ventrale",
        "description": "Apprenez la respiration diaphragmatique pour un calme profond et durable.",
        "category": "mindfulness",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Placez une main sur le ventre et l'autre sur la poitrine",
            "Inspirez en gonflant le ventre (la main du haut ne bouge pas)",
            "Expirez en laissant le ventre se dégonfler naturellement",
            "Pratiquez 10 respirations en allongeant progressivement l'expiration"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    {
        "action_id": "action_mindfulness_006",
        "title": "Cohérence cardiaque",
        "description": "Synchronisez votre respiration à 6 cycles par minute pour harmoniser le rythme cardiaque.",
        "category": "mindfulness",
        "duration_min": 4,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Réglez un minuteur de 5 minutes",
            "Inspirez pendant 5 secondes en suivant un rythme régulier",
            "Expirez pendant 5 secondes sans pause entre les deux",
            "Maintenez ce rythme de 6 respirations par minute pendant toute la durée"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    {
        "action_id": "action_mindfulness_007",
        "title": "Souffle rafraîchissant",
        "description": "Utilisez la respiration Sitali pour refroidir votre corps et calmer l'agitation.",
        "category": "mindfulness",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Roulez votre langue en forme de tube (ou serrez les dents si impossible)",
            "Inspirez lentement par la bouche en sentant l'air frais sur la langue",
            "Fermez la bouche et expirez par le nez",
            "Répétez 10 cycles en vous concentrant sur la sensation de fraîcheur"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    {
        "action_id": "action_mindfulness_008",
        "title": "Expiration prolongée",
        "description": "Allongez votre expiration pour activer le nerf vague et réduire l'anxiété.",
        "category": "mindfulness",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Inspirez naturellement pendant 3 secondes",
            "Expirez très lentement pendant 6 secondes en contrôlant le flux",
            "À chaque cycle, essayez d'allonger l'expiration d'une seconde",
            "Continuez pendant 8 cycles en observant la détente qui s'installe"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    {
        "action_id": "action_mindfulness_009",
        "title": "Respiration comptée",
        "description": "Comptez vos respirations de 1 à 10 pour entraîner votre concentration.",
        "category": "mindfulness",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Respirez naturellement et comptez 1 à la première expiration",
            "Continuez de compter chaque expiration jusqu'à 10",
            "Si vous perdez le compte, recommencez à 1 sans vous juger",
            "Essayez d'atteindre 10 trois fois de suite sans interruption"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    {
        "action_id": "action_mindfulness_010",
        "title": "Vague respiratoire",
        "description": "Respirez en imaginant une vague qui monte et descend le long de votre corps.",
        "category": "mindfulness",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Allongez-vous ou asseyez-vous les yeux fermés",
            "À l'inspiration, imaginez une vague chaude montant des pieds à la tête",
            "À l'expiration, la vague redescend de la tête aux pieds",
            "Ralentissez progressivement la vague à chaque cycle pendant 8 respirations"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    # --- Body awareness ---
    {
        "action_id": "action_mindfulness_011",
        "title": "Scan corporel flash",
        "description": "Scannez votre corps de la tête aux pieds pour détecter les tensions cachées.",
        "category": "mindfulness",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "high",
        "instructions": [
            "Fermez les yeux et portez attention au sommet de votre crâne",
            "Descendez lentement : front, mâchoire, cou, épaules, bras",
            "Continuez : poitrine, ventre, hanches, cuisses, mollets, pieds",
            "Notez mentalement chaque zone de tension ou de confort"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    {
        "action_id": "action_mindfulness_012",
        "title": "Relaxation progressive",
        "description": "Contractez puis relâchez chaque groupe musculaire pour une détente profonde.",
        "category": "mindfulness",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "high",
        "instructions": [
            "Commencez par les pieds : contractez fort 5 secondes, relâchez 10 secondes",
            "Remontez aux mollets, cuisses, fessiers avec le même principe",
            "Continuez avec le ventre, les poings, les bras, les épaules",
            "Terminez par le visage : contractez tous les muscles faciaux puis relâchez"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    {
        "action_id": "action_mindfulness_013",
        "title": "Radar intérieur",
        "description": "Développez votre intéroception en écoutant les signaux subtils de votre corps.",
        "category": "mindfulness",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "high",
        "instructions": [
            "Asseyez-vous les yeux fermés et concentrez-vous sur votre cœur",
            "Essayez de percevoir vos battements cardiaques sans toucher votre pouls",
            "Déplacez votre attention vers votre estomac : que ressentez-vous ?",
            "Notez 3 sensations internes que vous n'aviez pas remarquées"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    {
        "action_id": "action_mindfulness_014",
        "title": "Ancrage gravitaire",
        "description": "Ressentez la gravité sur chaque partie de votre corps pour un ancrage profond.",
        "category": "mindfulness",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Assis ou allongé, concentrez-vous sur le poids de votre tête",
            "Sentez comment la gravité attire vos épaules, vos bras, vos mains",
            "Percevez le poids de votre bassin, vos jambes, vos pieds",
            "Imaginez que vous devenez plus lourd à chaque expiration"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    {
        "action_id": "action_mindfulness_015",
        "title": "Micro-mouvement conscient",
        "description": "Bougez un seul doigt avec une attention totale pour entraîner la pleine conscience.",
        "category": "mindfulness",
        "duration_min": 2,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Posez vos mains sur vos cuisses, paumes vers le bas",
            "Levez très lentement l'index droit en observant chaque micro-mouvement",
            "Remarquez les muscles qui s'activent, les tendons qui bougent",
            "Reposez-le aussi lentement et faites de même avec chaque doigt"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    {
        "action_id": "action_mindfulness_016",
        "title": "Température corporelle",
        "description": "Scannez les variations de température dans votre corps pour affiner votre perception.",
        "category": "mindfulness",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Fermez les yeux et portez attention à la température de vos mains",
            "Comparez : sont-elles plus chaudes ou plus froides que vos pieds ?",
            "Cherchez les zones les plus chaudes et les plus froides de votre corps",
            "Notez comment votre respiration affecte la température ressentie au niveau des narines"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    {
        "action_id": "action_mindfulness_017",
        "title": "Posture alignée",
        "description": "Trouvez votre alignement parfait en empilant consciemment chaque partie du corps.",
        "category": "mindfulness",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "medium",
        "instructions": [
            "Debout, pieds parallèles, sentez le contact de vos pieds au sol",
            "Montez l'attention : chevilles alignées, genoux déverrouillés, bassin neutre",
            "Continuez : ventre tonique, épaules basses, tête droite comme tirée par un fil",
            "Respirez 5 fois dans cette posture en observant la stabilité gagnée"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    {
        "action_id": "action_mindfulness_018",
        "title": "Contact terre",
        "description": "Reconnectez-vous physiquement à la surface sous vos pieds.",
        "category": "mindfulness",
        "duration_min": 2,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Retirez vos chaussures si possible",
            "Sentez le contact de chaque partie du pied avec le sol",
            "Transférez doucement le poids d'un pied à l'autre",
            "Imaginez des racines qui poussent de vos pieds dans la terre"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    {
        "action_id": "action_mindfulness_019",
        "title": "Mains présentes",
        "description": "Explorez la sensibilité de vos mains avec une attention minutieuse.",
        "category": "mindfulness",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "high",
        "instructions": [
            "Frottez vos paumes ensemble pendant 10 secondes rapidement",
            "Séparez-les de 2 centimètres et sentez la chaleur ou le picotement",
            "Rapprochez et éloignez vos mains très lentement, percevez le champ de chaleur",
            "Posez vos mains sur votre visage et absorbez la sensation de chaleur"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    {
        "action_id": "action_mindfulness_020",
        "title": "Respiration localisée",
        "description": "Dirigez votre respiration vers une zone précise du corps pour la détendre.",
        "category": "mindfulness",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "high",
        "instructions": [
            "Identifiez une zone de tension dans votre corps (nuque, épaules, dos)",
            "À l'inspiration, imaginez l'air se diriger vers cette zone",
            "À l'expiration, visualisez la tension qui se dissout et s'évacue",
            "Répétez 10 respirations en sentant la zone se relâcher progressivement"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    # --- Emotional intelligence ---
    {
        "action_id": "action_mindfulness_021",
        "title": "Météo émotionnelle",
        "description": "Identifiez votre climat émotionnel actuel pour mieux vous connaître.",
        "category": "mindfulness",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Fermez les yeux et demandez-vous : quel temps fait-il en moi ?",
            "Nommez votre état : ensoleillé, nuageux, orageux, brumeux...",
            "Identifiez la cause principale de cette météo intérieure",
            "Acceptez ce climat sans chercher à le changer, observez simplement"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    {
        "action_id": "action_mindfulness_022",
        "title": "Gratitude précise",
        "description": "Pratiquez une gratitude ciblée en identifiant le détail exact qui vous touche.",
        "category": "mindfulness",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Pensez à 3 moments positifs de votre journée, même minuscules",
            "Pour chacun, identifiez le détail précis qui l'a rendu agréable",
            "Revivez la sensation physique associée à chaque moment",
            "Écrivez une phrase de gratitude pour le détail le plus marquant"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    {
        "action_id": "action_mindfulness_023",
        "title": "Auto-compassion douce",
        "description": "Adressez-vous à vous-même avec la bienveillance que vous offririez à un ami.",
        "category": "mindfulness",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Identifiez une difficulté ou un échec récent qui vous pèse",
            "Posez la main sur le cœur et dites-vous : c'est un moment difficile",
            "Rappelez-vous que tout le monde traverse des difficultés similaires",
            "Formulez un message de soutien comme vous le feriez pour un ami cher"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    {
        "action_id": "action_mindfulness_024",
        "title": "Roue des émotions",
        "description": "Affinez votre vocabulaire émotionnel en nommant précisément ce que vous ressentez.",
        "category": "mindfulness",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "high",
        "instructions": [
            "Identifiez l'émotion de base : joie, tristesse, colère, peur, dégoût, surprise",
            "Affinez : si c'est de la joie, est-ce de l'excitation, de la sérénité ou de la fierté ?",
            "Localisez cette émotion dans votre corps : où la ressentez-vous physiquement ?",
            "Notez l'intensité de 1 à 10 et comment elle évolue pendant l'exercice"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    {
        "action_id": "action_mindfulness_025",
        "title": "Lettre de pardon",
        "description": "Écrivez mentalement une courte lettre de pardon pour libérer une rancœur.",
        "category": "mindfulness",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Pensez à une personne envers qui vous gardez du ressentiment",
            "Formulez intérieurement ce qui vous a blessé en une phrase",
            "Imaginez que vous écrivez : je choisis de lâcher cette douleur",
            "Respirez profondément et visualisez le poids qui se libère de vos épaules"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    {
        "action_id": "action_mindfulness_026",
        "title": "Sourire intérieur",
        "description": "Envoyez un sourire mental à chaque organe pour cultiver la bienveillance envers vous-même.",
        "category": "mindfulness",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Fermez les yeux et souriez doucement",
            "Dirigez ce sourire vers votre cœur et sentez-le se réchauffer",
            "Envoyez le sourire vers votre estomac, vos poumons, votre foie",
            "Terminez en envoyant le sourire vers l'ensemble de votre corps"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    {
        "action_id": "action_mindfulness_027",
        "title": "Journal d'irritations",
        "description": "Transformez vos irritations quotidiennes en leçons de connaissance de soi.",
        "category": "mindfulness",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "medium",
        "instructions": [
            "Notez une irritation récente aussi précisément que possible",
            "Demandez-vous quel besoin non satisfait cette irritation révèle",
            "Identifiez si cette réaction est proportionnelle à la situation",
            "Formulez une stratégie pour répondre à ce besoin la prochaine fois"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    {
        "action_id": "action_mindfulness_028",
        "title": "Bilan émotionnel",
        "description": "Faites le point sur votre palette émotionnelle des dernières 24 heures.",
        "category": "mindfulness",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "medium",
        "instructions": [
            "Listez les 5 émotions dominantes que vous avez ressenties aujourd'hui",
            "Pour chacune, notez le déclencheur et l'intensité sur 10",
            "Identifiez l'émotion qui a duré le plus longtemps et pourquoi",
            "Choisissez une émotion que vous aimeriez cultiver davantage demain"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    {
        "action_id": "action_mindfulness_029",
        "title": "Compassion universelle",
        "description": "Envoyez des pensées bienveillantes à des cercles de plus en plus larges.",
        "category": "mindfulness",
        "duration_min": 4,
        "duration_max": 7,
        "energy_level": "medium",
        "instructions": [
            "Commencez par vous souhaiter paix et bonheur silencieusement",
            "Étendez ce souhait à un proche que vous aimez",
            "Élargissez à une personne neutre (un voisin, un commerçant)",
            "Terminez en envoyant de la bienveillance à tous les êtres vivants"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    {
        "action_id": "action_mindfulness_030",
        "title": "Émotion observée",
        "description": "Observez une émotion forte sans y réagir pour développer votre régulation.",
        "category": "mindfulness",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "medium",
        "instructions": [
            "Identifiez une émotion présente en ce moment, même légère",
            "Observez-la comme un nuage qui passe : elle est là, elle passera",
            "Notez comment elle se manifeste physiquement sans la repousser",
            "Respirez 5 fois en laissant l'émotion exister sans l'alimenter"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    # --- Sensory attention ---
    {
        "action_id": "action_mindfulness_031",
        "title": "Bouchée consciente",
        "description": "Mangez un aliment en pleine conscience pour transformer votre rapport à la nourriture.",
        "category": "mindfulness",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Prenez un petit aliment (raisin, noix, carré de chocolat)",
            "Observez-le pendant 20 secondes : couleur, texture, forme",
            "Portez-le à la bouche sans croquer, sentez la texture sur la langue",
            "Mâchez très lentement en comptant les saveurs qui apparaissent"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    {
        "action_id": "action_mindfulness_032",
        "title": "Écoute profonde",
        "description": "Écoutez les sons ambiants par couches pour affiner votre attention auditive.",
        "category": "mindfulness",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Fermez les yeux et identifiez le son le plus lointain que vous percevez",
            "Rapprochez votre attention : trouvez un son à distance moyenne",
            "Concentrez-vous sur le son le plus proche de vous",
            "Essayez d'écouter les trois couches sonores simultanément pendant 1 minute"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    {
        "action_id": "action_mindfulness_033",
        "title": "Toucher exploratoire",
        "description": "Explorez un objet uniquement par le toucher pour réveiller ce sens sous-utilisé.",
        "category": "mindfulness",
        "duration_min": 2,
        "duration_max": 5,
        "energy_level": "high",
        "instructions": [
            "Choisissez un objet familier et fermez les yeux",
            "Explorez-le lentement avec le bout des doigts pendant 1 minute",
            "Notez chaque détail : température, rugosité, bords, poids",
            "Ouvrez les yeux et voyez si l'objet vous semble différent maintenant"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    {
        "action_id": "action_mindfulness_034",
        "title": "Palette olfactive",
        "description": "Identifiez et nommez les odeurs autour de vous pour réveiller votre sens olfactif.",
        "category": "mindfulness",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "high",
        "instructions": [
            "Inspirez profondément par le nez et identifiez l'odeur dominante",
            "Cherchez des odeurs plus subtiles en respirant délicatement",
            "Essayez de nommer chaque odeur avec précision (bois sec, café froid...)",
            "Identifiez l'émotion ou le souvenir que chaque odeur évoque"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    {
        "action_id": "action_mindfulness_035",
        "title": "Vision périphérique",
        "description": "Élargissez votre champ de vision pour détendre votre regard et calmer le mental.",
        "category": "mindfulness",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "medium",
        "instructions": [
            "Fixez un point droit devant vous sans bouger les yeux",
            "Sans tourner la tête, élargissez votre attention aux côtés gauche et droit",
            "Essayez de percevoir le haut et le bas de votre champ visuel",
            "Maintenez cette vision panoramique pendant 1 minute en respirant calmement"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    {
        "action_id": "action_mindfulness_036",
        "title": "Gorgée attentive",
        "description": "Buvez une gorgée d'eau ou de thé avec une attention totale à chaque sensation.",
        "category": "mindfulness",
        "duration_min": 2,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Prenez votre tasse ou verre et sentez sa température dans vos mains",
            "Approchez-le de votre bouche et sentez l'odeur du liquide",
            "Prenez une petite gorgée et gardez-la en bouche 3 secondes",
            "Avalez lentement en suivant la sensation de la gorge à l'estomac"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    {
        "action_id": "action_mindfulness_037",
        "title": "Observation colorée",
        "description": "Repérez toutes les occurrences d'une couleur dans votre environnement.",
        "category": "mindfulness",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "medium",
        "instructions": [
            "Choisissez une couleur au hasard (rouge, vert, bleu...)",
            "Scannez votre environnement pendant 2 minutes pour trouver cette couleur",
            "Comptez chaque occurrence en notant l'objet associé",
            "Observez comment ce focus change votre perception de l'espace"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    {
        "action_id": "action_mindfulness_038",
        "title": "Silence gustatif",
        "description": "Identifiez le goût résiduel dans votre bouche pour entraîner votre palais.",
        "category": "mindfulness",
        "duration_min": 2,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Fermez les yeux et concentrez-vous sur l'intérieur de votre bouche",
            "Essayez d'identifier tout goût résiduel : sucré, salé, acide, amer, umami",
            "Buvez une gorgée d'eau et notez comment le goût change",
            "Comparez la sensation avant et après l'eau en vous concentrant sur les papilles"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    {
        "action_id": "action_mindfulness_039",
        "title": "Concert naturel",
        "description": "Écoutez les sons de la nature comme un concert pour reconnecter avec votre environnement.",
        "category": "mindfulness",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "medium",
        "instructions": [
            "Approchez-vous d'une fenêtre ou sortez un instant",
            "Identifiez les sons naturels : oiseaux, vent, pluie, insectes",
            "Suivez un seul son pendant 30 secondes comme une ligne mélodique",
            "Imaginez que tous ces sons forment un orchestre et écoutez l'ensemble"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    {
        "action_id": "action_mindfulness_040",
        "title": "Texture vestimentaire",
        "description": "Percevez consciemment le contact de vos vêtements sur votre peau.",
        "category": "mindfulness",
        "duration_min": 2,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Portez attention au contact de votre chemise sur vos épaules",
            "Descendez : sentez la ceinture ou l'élastique à votre taille",
            "Notez la texture du pantalon sur vos cuisses et le tissu des chaussettes",
            "Observez comment ces sensations normalement ignorées deviennent vivantes"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    # --- Present-moment ---
    {
        "action_id": "action_mindfulness_041",
        "title": "Marche méditative",
        "description": "Transformez une courte marche en méditation en mouvement.",
        "category": "mindfulness",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Marchez très lentement sur une distance de 5 à 10 mètres",
            "Décomposez chaque pas : lever, avancer, poser le pied",
            "Synchronisez votre respiration avec vos pas",
            "Au bout du parcours, faites demi-tour et recommencez en sens inverse"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    {
        "action_id": "action_mindfulness_042",
        "title": "Micro-méditation",
        "description": "Méditez pendant exactement 60 secondes pour prouver que la pleine conscience tient dans une minute.",
        "category": "mindfulness",
        "duration_min": 2,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Mettez un minuteur d'une minute",
            "Fermez les yeux et portez toute votre attention sur votre respiration",
            "Quand une pensée survient, remarquez-la et revenez au souffle",
            "Quand la minute sonne, notez combien de fois vos pensées ont dérivé"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    {
        "action_id": "action_mindfulness_043",
        "title": "Attention focalisée",
        "description": "Fixez un objet simple pendant 3 minutes pour entraîner votre concentration.",
        "category": "mindfulness",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "medium",
        "instructions": [
            "Choisissez un objet simple : une bougie, un crayon, une fleur",
            "Observez-le avec une attention totale pendant 3 minutes",
            "Quand votre esprit divague, ramenez doucement l'attention à l'objet",
            "Notez des détails que vous n'aviez jamais remarqués auparavant"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    {
        "action_id": "action_mindfulness_044",
        "title": "Pause STOP",
        "description": "Appliquez la technique STOP pour revenir au présent en 4 étapes.",
        "category": "mindfulness",
        "duration_min": 2,
        "duration_max": 5,
        "energy_level": "medium",
        "instructions": [
            "S - Stop : arrêtez ce que vous faites complètement",
            "T - Take a breath : prenez 3 respirations profondes",
            "O - Observe : que ressentez-vous physiquement et émotionnellement ?",
            "P - Proceed : reprenez votre activité avec cette conscience renouvelée"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    {
        "action_id": "action_mindfulness_045",
        "title": "Présent 5-4-3-2-1",
        "description": "Utilisez la technique d'ancrage sensoriel 5-4-3-2-1 pour revenir au moment présent.",
        "category": "mindfulness",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "medium",
        "instructions": [
            "Nommez 5 choses que vous voyez en ce moment",
            "Identifiez 4 choses que vous pouvez toucher",
            "Écoutez et nommez 3 sons différents autour de vous",
            "Trouvez 2 odeurs et 1 goût pour compléter l'ancrage"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    {
        "action_id": "action_mindfulness_046",
        "title": "Instant photographique",
        "description": "Prenez une photo mentale de l'instant présent pour entraîner votre mémoire attentive.",
        "category": "mindfulness",
        "duration_min": 2,
        "duration_max": 5,
        "energy_level": "medium",
        "instructions": [
            "Observez votre environnement pendant 30 secondes avec attention",
            "Fermez les yeux et essayez de recréer mentalement la scène",
            "Notez les détails que vous avez retenus et ceux que vous avez oubliés",
            "Ouvrez les yeux et comparez votre image mentale à la réalité"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    {
        "action_id": "action_mindfulness_047",
        "title": "Contemplation du ciel",
        "description": "Regardez le ciel pendant 3 minutes pour élargir votre perspective et calmer le mental.",
        "category": "mindfulness",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Trouvez un endroit où vous pouvez voir le ciel",
            "Observez les nuages, leur mouvement, leurs formes changeantes",
            "Imaginez que vos pensées sont comme ces nuages : elles passent",
            "Respirez profondément en gardant les yeux sur l'immensité du ciel"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    {
        "action_id": "action_mindfulness_048",
        "title": "Rituel de transition",
        "description": "Créez un micro-rituel pour marquer consciemment la transition entre deux activités.",
        "category": "mindfulness",
        "duration_min": 2,
        "duration_max": 5,
        "energy_level": "medium",
        "instructions": [
            "Avant de changer d'activité, posez vos mains à plat sur le bureau",
            "Prenez 3 respirations profondes pour clore mentalement l'activité précédente",
            "Formulez une intention claire pour l'activité suivante en une phrase",
            "Commencez la nouvelle activité avec cette intention fraîche en tête"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    {
        "action_id": "action_mindfulness_049",
        "title": "Pensées nuages",
        "description": "Observez vos pensées défiler comme des nuages sans vous y accrocher.",
        "category": "mindfulness",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Asseyez-vous confortablement et fermez les yeux",
            "Imaginez un ciel bleu et laissez chaque pensée devenir un nuage",
            "Observez chaque nuage-pensée apparaître, traverser le ciel et disparaître",
            "Ne retenez aucun nuage, laissez-les tous passer pendant 3 à 5 minutes"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    {
        "action_id": "action_mindfulness_050",
        "title": "Gratitude corporelle",
        "description": "Remerciez chaque partie de votre corps pour ancrer l'appréciation de soi.",
        "category": "mindfulness",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Portez attention à vos pieds et remerciez-les de vous porter chaque jour",
            "Remontez aux jambes, au tronc, aux bras en remerciant chaque fonction",
            "Remerciez vos poumons pour chaque respiration, votre cœur pour chaque battement",
            "Terminez en envoyant de la gratitude à votre corps dans son ensemble"
        ],
        "is_premium": True,
        "icon": "leaf"
    },
    # =====================================================================
    # LEADERSHIP (50 actions) - icon: "users"
    # =====================================================================
    # --- Communication ---
    {
        "action_id": "action_leadership_001",
        "title": "Écoute miroir",
        "description": "Pratiquez l'écoute active en reformulant les propos de votre interlocuteur.",
        "category": "leadership",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "medium",
        "instructions": [
            "Lors de votre prochaine conversation, écoutez sans préparer votre réponse",
            "Reformulez ce que l'autre a dit : si je comprends bien, tu penses que...",
            "Observez la réaction : correction, confirmation ou approfondissement",
            "Notez mentalement la différence entre ce que vous pensiez et ce qui a été dit"
        ],
        "is_premium": True,
        "icon": "users"
    },
    {
        "action_id": "action_leadership_002",
        "title": "Feedback sandwich",
        "description": "Structurez un retour constructif en 3 couches pour qu'il soit entendu et utile.",
        "category": "leadership",
        "duration_min": 4,
        "duration_max": 7,
        "energy_level": "medium",
        "instructions": [
            "Pensez à un feedback que vous devez donner à quelqu'un",
            "Écrivez d'abord un point positif sincère et spécifique",
            "Formulez l'axe d'amélioration comme une opportunité, pas une critique",
            "Terminez par un encouragement ou une expression de confiance"
        ],
        "is_premium": True,
        "icon": "users"
    },
    {
        "action_id": "action_leadership_003",
        "title": "Assertivité express",
        "description": "Formulez une demande assertive avec la méthode DESC en 4 étapes.",
        "category": "leadership",
        "duration_min": 4,
        "duration_max": 7,
        "energy_level": "medium",
        "instructions": [
            "D - Décrivez la situation factuellement sans jugement",
            "E - Exprimez votre ressenti avec un message 'je'",
            "S - Spécifiez ce que vous souhaitez concrètement",
            "C - Concluez par les conséquences positives si la demande est satisfaite"
        ],
        "is_premium": True,
        "icon": "users"
    },
    {
        "action_id": "action_leadership_004",
        "title": "Pitch 30 secondes",
        "description": "Entraînez-vous à présenter une idée de façon percutante en 30 secondes.",
        "category": "leadership",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "high",
        "instructions": [
            "Choisissez un projet ou une idée que vous devez défendre",
            "Structurez en 3 temps : problème, solution, bénéfice",
            "Chronométrez votre pitch et ajustez pour tenir en 30 secondes",
            "Répétez 3 fois en améliorant la clarté et l'impact à chaque fois"
        ],
        "is_premium": True,
        "icon": "users"
    },
    {
        "action_id": "action_leadership_005",
        "title": "Storytelling minute",
        "description": "Transformez un fait banal en histoire captivante pour renforcer votre impact.",
        "category": "leadership",
        "duration_min": 4,
        "duration_max": 7,
        "energy_level": "medium",
        "instructions": [
            "Choisissez un événement récent de votre vie professionnelle",
            "Identifiez le héros, le défi et la transformation",
            "Racontez l'histoire en commençant par le moment de tension",
            "Terminez par la leçon apprise en une phrase mémorable"
        ],
        "is_premium": True,
        "icon": "users"
    },
    {
        "action_id": "action_leadership_006",
        "title": "Question puissante",
        "description": "Préparez 3 questions ouvertes qui ouvrent vraiment la réflexion.",
        "category": "leadership",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Pensez à un sujet de discussion ou de réunion à venir",
            "Formulez 3 questions commençant par Comment ou Qu'est-ce qui",
            "Vérifiez que chaque question ne peut pas être répondue par oui ou non",
            "Testez mentalement chaque question : provoque-t-elle une réflexion profonde ?"
        ],
        "is_premium": True,
        "icon": "users"
    },
    {
        "action_id": "action_leadership_007",
        "title": "Silence stratégique",
        "description": "Utilisez le silence comme outil de communication pour amplifier votre message.",
        "category": "leadership",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Identifiez un moment dans une conversation où vous parlez trop vite",
            "Pratiquez : après une affirmation importante, marquez 3 secondes de silence",
            "Observez comment le silence donne du poids à vos mots",
            "Lors de votre prochaine réunion, essayez de laisser 2 secondes avant de répondre"
        ],
        "is_premium": True,
        "icon": "users"
    },
    {
        "action_id": "action_leadership_008",
        "title": "Message clair",
        "description": "Réécrivez un message complexe en version limpide pour votre audience.",
        "category": "leadership",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "medium",
        "instructions": [
            "Prenez un email ou message récent que vous avez envoyé",
            "Identifiez le message essentiel en une seule phrase",
            "Réécrivez le message en plaçant cette phrase en premier",
            "Supprimez tout ce qui n'aide pas directement à comprendre le message principal"
        ],
        "is_premium": True,
        "icon": "users"
    },
    {
        "action_id": "action_leadership_009",
        "title": "Langage corporel",
        "description": "Analysez et ajustez votre langage corporel pour projeter plus de confiance.",
        "category": "leadership",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "medium",
        "instructions": [
            "Debout devant un miroir, adoptez votre posture naturelle",
            "Corrigez : pieds ancrés, épaules ouvertes, menton parallèle au sol",
            "Pratiquez un contact visuel avec votre reflet pendant 30 secondes",
            "Répétez une phrase clé en maintenant cette posture assurée"
        ],
        "is_premium": True,
        "icon": "users"
    },
    {
        "action_id": "action_leadership_010",
        "title": "Résumé percutant",
        "description": "Résumez une réunion ou un document complexe en 3 points clés maximum.",
        "category": "leadership",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Repensez à votre dernière réunion ou lecture importante",
            "Identifiez les 3 points essentiels que quelqu'un devrait retenir",
            "Formulez chaque point en une phrase de 15 mots maximum",
            "Vérifiez : si quelqu'un ne lisait que ces 3 points, comprendrait-il l'essentiel ?"
        ],
        "is_premium": True,
        "icon": "users"
    },
    # --- Decision-making ---
    {
        "action_id": "action_leadership_011",
        "title": "Matrice 2x2",
        "description": "Utilisez la matrice urgence/importance pour prioriser vos décisions en 5 minutes.",
        "category": "leadership",
        "duration_min": 4,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Dessinez un carré divisé en 4 : urgent/non urgent x important/non important",
            "Listez vos 8 tâches ou décisions actuelles les plus pressantes",
            "Placez chacune dans le quadrant approprié sans hésiter",
            "Commencez par le quadrant important + urgent, planifiez l'important + non urgent"
        ],
        "is_premium": True,
        "icon": "users"
    },
    {
        "action_id": "action_leadership_012",
        "title": "Biais checker",
        "description": "Identifiez les biais cognitifs qui influencent votre décision actuelle.",
        "category": "leadership",
        "duration_min": 4,
        "duration_max": 7,
        "energy_level": "medium",
        "instructions": [
            "Pensez à une décision que vous devez prendre prochainement",
            "Vérifiez le biais de confirmation : cherchez-vous seulement ce qui confirme votre choix ?",
            "Vérifiez le biais du statu quo : restez-vous dans votre zone de confort ?",
            "Demandez-vous : que conseillerais-je à un ami dans la même situation ?"
        ],
        "is_premium": True,
        "icon": "users"
    },
    {
        "action_id": "action_leadership_013",
        "title": "Priorisation rapide",
        "description": "Classez 5 tâches par impact et effort en 3 minutes pour agir sur la plus rentable.",
        "category": "leadership",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "medium",
        "instructions": [
            "Listez vos 5 tâches les plus importantes du moment",
            "Notez chacune sur 2 axes : impact potentiel (1-5) et effort requis (1-5)",
            "Calculez le ratio impact/effort pour chaque tâche",
            "Commencez par la tâche avec le meilleur ratio"
        ],
        "is_premium": True,
        "icon": "users"
    },
    {
        "action_id": "action_leadership_014",
        "title": "Pré-mortem express",
        "description": "Imaginez que votre projet a échoué et identifiez les causes pour les prévenir.",
        "category": "leadership",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "high",
        "instructions": [
            "Choisissez un projet ou une décision en cours",
            "Imaginez que c'est dans 6 mois et que le projet a échoué",
            "Listez 5 raisons plausibles de cet échec",
            "Pour les 2 risques les plus probables, définissez une action préventive"
        ],
        "is_premium": True,
        "icon": "users"
    },
    {
        "action_id": "action_leadership_015",
        "title": "Règle des 10-10-10",
        "description": "Évaluez l'impact d'une décision à 10 minutes, 10 mois et 10 ans.",
        "category": "leadership",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Formulez la décision que vous hésitez à prendre",
            "Demandez-vous : comment je me sentirai dans 10 minutes si je choisis X ?",
            "Comment je me sentirai dans 10 mois ? Et dans 10 ans ?",
            "Notez si la perspective temporelle change votre inclination"
        ],
        "is_premium": True,
        "icon": "users"
    },
    {
        "action_id": "action_leadership_016",
        "title": "Décision inversée",
        "description": "Envisagez le choix opposé à votre instinct pour tester la solidité de votre décision.",
        "category": "leadership",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "medium",
        "instructions": [
            "Identifiez votre choix instinctif face à une décision",
            "Forcez-vous à défendre le choix exactement opposé pendant 2 minutes",
            "Notez les arguments valides que vous trouvez pour ce choix opposé",
            "Décidez si votre instinct initial résiste à ces contre-arguments"
        ],
        "is_premium": True,
        "icon": "users"
    },
    {
        "action_id": "action_leadership_017",
        "title": "Coût d'inaction",
        "description": "Calculez ce que vous coûte le fait de ne pas agir pour briser la procrastination décisionnelle.",
        "category": "leadership",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Identifiez une décision que vous reportez depuis trop longtemps",
            "Listez ce que cette indécision vous coûte : temps, énergie, opportunités",
            "Estimez le coût cumulé si vous attendez encore 1 mois",
            "Fixez une deadline ferme et un premier micro-pas à faire aujourd'hui"
        ],
        "is_premium": True,
        "icon": "users"
    },
    {
        "action_id": "action_leadership_018",
        "title": "Conseil du sage",
        "description": "Imaginez le conseil que vous donnerait un mentor respecté face à votre dilemme.",
        "category": "leadership",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Pensez à une personne que vous admirez profondément (mentor, leader, figure historique)",
            "Présentez-lui mentalement votre dilemme en une phrase",
            "Imaginez sa réponse : que dirait cette personne ?",
            "Notez le conseil imaginé et évaluez s'il résonne avec vos valeurs"
        ],
        "is_premium": True,
        "icon": "users"
    },
    {
        "action_id": "action_leadership_019",
        "title": "Décision à rebours",
        "description": "Partez du résultat souhaité et remontez les étapes pour clarifier votre choix.",
        "category": "leadership",
        "duration_min": 4,
        "duration_max": 7,
        "energy_level": "medium",
        "instructions": [
            "Décrivez le résultat idéal que vous visez dans 3 mois",
            "Identifiez la dernière étape juste avant ce résultat",
            "Remontez 3 étapes en arrière jusqu'à aujourd'hui",
            "La première étape identifiée est votre prochaine action prioritaire"
        ],
        "is_premium": True,
        "icon": "users"
    },
    {
        "action_id": "action_leadership_020",
        "title": "Filtre des valeurs",
        "description": "Passez une décision difficile au filtre de vos 3 valeurs fondamentales.",
        "category": "leadership",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Identifiez vos 3 valeurs les plus importantes (ex: intégrité, créativité, famille)",
            "Pour chaque option de votre décision, vérifiez l'alignement avec chaque valeur",
            "Notez un score d'alignement de 1 à 5 pour chaque combinaison option-valeur",
            "L'option avec le meilleur score total est probablement la bonne"
        ],
        "is_premium": True,
        "icon": "users"
    },
    # --- Emotional intelligence (leadership) ---
    {
        "action_id": "action_leadership_021",
        "title": "Carte d'empathie",
        "description": "Cartographiez ce que pense, ressent et vit un membre de votre équipe.",
        "category": "leadership",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "high",
        "instructions": [
            "Choisissez un collaborateur avec qui vous avez une interaction importante à venir",
            "Notez ce qu'il pense et dit probablement de la situation",
            "Imaginez ce qu'il ressent et ce qui le préoccupe en profondeur",
            "Identifiez comment cette compréhension change votre approche"
        ],
        "is_premium": True,
        "icon": "users"
    },
    {
        "action_id": "action_leadership_022",
        "title": "Désamorçage conflit",
        "description": "Préparez une stratégie de désescalade pour un conflit en cours ou à venir.",
        "category": "leadership",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "high",
        "instructions": [
            "Identifiez le conflit ou la tension et le besoin de chaque partie",
            "Trouvez un point d'accord commun, même minime",
            "Formulez une phrase d'ouverture qui reconnaît la perspective de l'autre",
            "Préparez une proposition qui répond partiellement aux besoins de chacun"
        ],
        "is_premium": True,
        "icon": "users"
    },
    {
        "action_id": "action_leadership_023",
        "title": "Régulation émotionnelle",
        "description": "Appliquez la technique RAIN pour gérer une émotion intense au travail.",
        "category": "leadership",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "medium",
        "instructions": [
            "R - Reconnaissez l'émotion : nommez-la précisément",
            "A - Acceptez-la : ne la combattez pas, elle est légitime",
            "I - Investiguez : où la ressentez-vous dans votre corps ?",
            "N - Non-identification : cette émotion n'est pas vous, elle passera"
        ],
        "is_premium": True,
        "icon": "users"
    },
    {
        "action_id": "action_leadership_024",
        "title": "Journal de triggers",
        "description": "Identifiez vos déclencheurs émotionnels récurrents pour mieux les anticiper.",
        "category": "leadership",
        "duration_min": 4,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Repensez à un moment récent où vous avez eu une réaction émotionnelle forte",
            "Identifiez le déclencheur précis : mot, ton, situation, comportement",
            "Cherchez un schéma : est-ce la première fois ou un pattern récurrent ?",
            "Préparez une réponse alternative pour la prochaine occurrence"
        ],
        "is_premium": True,
        "icon": "users"
    },
    {
        "action_id": "action_leadership_025",
        "title": "Écoute empathique",
        "description": "Entraînez-vous à écouter les émotions derrière les mots plutôt que les mots eux-mêmes.",
        "category": "leadership",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "medium",
        "instructions": [
            "Rappelez-vous une conversation récente où quelqu'un vous a parlé d'un problème",
            "Au-delà des mots, quelle émotion cette personne exprimait-elle vraiment ?",
            "Formulez une réponse qui aurait adressé l'émotion plutôt que le problème",
            "Lors de votre prochaine conversation, essayez cette approche"
        ],
        "is_premium": True,
        "icon": "users"
    },
    {
        "action_id": "action_leadership_026",
        "title": "Température d'équipe",
        "description": "Évaluez rapidement le moral de votre équipe avec 3 questions ciblées.",
        "category": "leadership",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "medium",
        "instructions": [
            "Préparez 3 questions rapides : énergie (1-5), clarté des priorités (1-5), soutien ressenti (1-5)",
            "Imaginez les réponses de chaque membre de votre équipe",
            "Identifiez la personne qui pourrait être en difficulté",
            "Planifiez un check-in informel avec cette personne aujourd'hui"
        ],
        "is_premium": True,
        "icon": "users"
    },
    {
        "action_id": "action_leadership_027",
        "title": "Vulnérabilité calculée",
        "description": "Préparez un partage authentique pour renforcer la confiance avec votre équipe.",
        "category": "leadership",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "high",
        "instructions": [
            "Identifiez une erreur ou un apprentissage récent que vous pourriez partager",
            "Formulez-le de façon honnête : voici ce que j'ai appris en me trompant",
            "Assurez-vous que le partage est approprié au contexte professionnel",
            "Prévoyez de terminer par ce que vous faites différemment maintenant"
        ],
        "is_premium": True,
        "icon": "users"
    },
    {
        "action_id": "action_leadership_028",
        "title": "Pause avant réaction",
        "description": "Entraînez le réflexe de marquer une pause avant de réagir sous pression.",
        "category": "leadership",
        "duration_min": 2,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Pensez à une situation récente où vous avez réagi trop vite",
            "Visualisez la scène et imaginez-vous prenant 3 respirations avant de répondre",
            "Formulez la réponse que vous auriez donnée après cette pause",
            "Ancrez le réflexe : prochaine pression = 3 respirations avant de parler"
        ],
        "is_premium": True,
        "icon": "users"
    },
    {
        "action_id": "action_leadership_029",
        "title": "Feedback émotionnel",
        "description": "Donnez un retour qui adresse l'émotion autant que le comportement.",
        "category": "leadership",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "medium",
        "instructions": [
            "Pensez à un feedback que vous devez donner",
            "Commencez par reconnaître l'effort ou l'intention positive",
            "Décrivez l'impact émotionnel du comportement sur vous ou l'équipe",
            "Proposez une alternative en exprimant votre confiance dans la capacité de la personne"
        ],
        "is_premium": True,
        "icon": "users"
    },
    {
        "action_id": "action_leadership_030",
        "title": "Check-in personnel",
        "description": "Faites un point honnête sur votre état émotionnel de leader en ce moment.",
        "category": "leadership",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Évaluez votre niveau d'énergie, de motivation et de stress sur 10",
            "Identifiez ce qui draine le plus votre énergie en ce moment",
            "Identifiez ce qui vous donne le plus d'énergie",
            "Définissez un petit ajustement pour augmenter le positif ou réduire le négatif"
        ],
        "is_premium": True,
        "icon": "users"
    },
    # --- Strategic thinking ---
    {
        "action_id": "action_leadership_031",
        "title": "Vision 3 mots",
        "description": "Clarifiez votre vision en la résumant en exactement 3 mots essentiels.",
        "category": "leadership",
        "duration_min": 4,
        "duration_max": 7,
        "energy_level": "medium",
        "instructions": [
            "Pensez à votre projet ou équipe et à ce que vous voulez accomplir",
            "Listez 10 mots qui décrivent votre vision",
            "Éliminez jusqu'à n'en garder que 3 qui capturent l'essence",
            "Testez : ces 3 mots guideraient-ils une décision difficile ?"
        ],
        "is_premium": True,
        "icon": "users"
    },
    {
        "action_id": "action_leadership_032",
        "title": "SWOT personnel",
        "description": "Réalisez une micro-analyse SWOT de votre situation professionnelle actuelle.",
        "category": "leadership",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Forces : listez vos 3 atouts principaux en ce moment",
            "Faiblesses : identifiez 2 points à améliorer honnêtement",
            "Opportunités : repérez 2 tendances ou ouvertures dans votre environnement",
            "Menaces : nommez 1 risque externe à anticiper"
        ],
        "is_premium": True,
        "icon": "users"
    },
    {
        "action_id": "action_leadership_033",
        "title": "Veille tendances",
        "description": "Identifiez 3 tendances émergentes dans votre secteur en 5 minutes de réflexion.",
        "category": "leadership",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "high",
        "instructions": [
            "Pensez aux 3 dernières actualités de votre secteur qui vous ont marqué",
            "Identifiez le fil conducteur entre ces actualités",
            "Projetez cette tendance à 12 mois : que va-t-il se passer ?",
            "Notez une action concrète pour vous positionner face à cette tendance"
        ],
        "is_premium": True,
        "icon": "users"
    },
    {
        "action_id": "action_leadership_034",
        "title": "Horizon élargi",
        "description": "Sortez de votre bulle en explorant un domaine complètement étranger au vôtre.",
        "category": "leadership",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "high",
        "instructions": [
            "Choisissez un domaine que vous ne connaissez pas (biotechnologie, art contemporain, agriculture...)",
            "Lisez un titre d'article dans ce domaine et identifiez le défi principal",
            "Trouvez un parallèle avec un défi de votre propre secteur",
            "Notez une idée transposable de ce domaine vers le vôtre"
        ],
        "is_premium": True,
        "icon": "users"
    },
    {
        "action_id": "action_leadership_035",
        "title": "Scénario extrême",
        "description": "Imaginez le meilleur et le pire scénario pour préparer une stratégie résiliente.",
        "category": "leadership",
        "duration_min": 4,
        "duration_max": 7,
        "energy_level": "high",
        "instructions": [
            "Choisissez un projet en cours et imaginez le meilleur scénario possible",
            "Puis imaginez le pire scénario réaliste",
            "Pour le pire scénario, listez 3 actions qui limiteraient les dégâts",
            "Vérifiez si ces actions préventives sont réalisables dès maintenant"
        ],
        "is_premium": True,
        "icon": "users"
    },
    {
        "action_id": "action_leadership_036",
        "title": "Client fantôme",
        "description": "Vivez l'expérience de votre produit ou service comme un nouveau client.",
        "category": "leadership",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "high",
        "instructions": [
            "Naviguez votre site ou service comme si vous le découvriez pour la première fois",
            "Notez chaque moment de confusion ou de friction",
            "Identifiez l'étape qui ferait abandonner un client pressé",
            "Proposez une amélioration pour le point de friction le plus critique"
        ],
        "is_premium": True,
        "icon": "users"
    },
    {
        "action_id": "action_leadership_037",
        "title": "Stratégie soustractive",
        "description": "Identifiez ce que vous devriez arrêter de faire pour libérer de la valeur.",
        "category": "leadership",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "medium",
        "instructions": [
            "Listez 5 activités qui consomment votre temps chaque semaine",
            "Pour chacune, demandez-vous : que se passerait-il si j'arrêtais ?",
            "Identifiez celle dont l'arrêt aurait le moins de conséquences négatives",
            "Planifiez de la supprimer ou la déléguer cette semaine"
        ],
        "is_premium": True,
        "icon": "users"
    },
    {
        "action_id": "action_leadership_038",
        "title": "Indicateur clé unique",
        "description": "Identifiez la métrique unique qui résume le mieux la santé de votre projet.",
        "category": "leadership",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Listez toutes les métriques que vous suivez pour votre projet",
            "Demandez-vous : si je ne pouvais en garder qu'une seule, laquelle ?",
            "Vérifiez que cette métrique est actionnable et mesurable",
            "Définissez un seuil d'alerte au-dessus ou en dessous duquel vous devez agir"
        ],
        "is_premium": True,
        "icon": "users"
    },
    {
        "action_id": "action_leadership_039",
        "title": "Analyse concurrentielle",
        "description": "Analysez rapidement un concurrent pour identifier une opportunité différenciante.",
        "category": "leadership",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "high",
        "instructions": [
            "Choisissez un concurrent et identifiez son point fort principal",
            "Identifiez un besoin client que ce concurrent néglige",
            "Évaluez si ce besoin négligé est une opportunité pour vous",
            "Notez une action pour explorer cette opportunité cette semaine"
        ],
        "is_premium": True,
        "icon": "users"
    },
    {
        "action_id": "action_leadership_040",
        "title": "Rétrospective flash",
        "description": "Faites une rétrospective de 5 minutes sur votre dernière semaine de travail.",
        "category": "leadership",
        "duration_min": 4,
        "duration_max": 7,
        "energy_level": "high",
        "instructions": [
            "Listez 3 choses qui ont bien fonctionné cette semaine",
            "Identifiez 1 chose que vous feriez différemment",
            "Nommez la surprise de la semaine : quelque chose d'inattendu",
            "Définissez votre priorité numéro 1 pour la semaine prochaine"
        ],
        "is_premium": True,
        "icon": "users"
    },
    # --- Team dynamics ---
    {
        "action_id": "action_leadership_041",
        "title": "Délégation inversée",
        "description": "Identifiez une tâche que vous faites par habitude mais qu'un autre ferait mieux.",
        "category": "leadership",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "medium",
        "instructions": [
            "Listez vos tâches de la semaine et identifiez celle qui ne nécessite pas vos compétences uniques",
            "Identifiez la personne de votre équipe qui pourrait la faire aussi bien ou mieux",
            "Formulez la délégation : contexte, résultat attendu, deadline, autonomie",
            "Prévoyez un point de suivi sans micro-management"
        ],
        "is_premium": True,
        "icon": "users"
    },
    {
        "action_id": "action_leadership_042",
        "title": "Reconnaissance ciblée",
        "description": "Préparez un message de reconnaissance spécifique pour un membre de votre équipe.",
        "category": "leadership",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Pensez à un collaborateur qui a fait quelque chose de bien récemment",
            "Identifiez le comportement précis et son impact positif",
            "Formulez un message spécifique : j'ai remarqué que tu as... et ça a permis de...",
            "Envoyez-le par le canal le plus approprié (en personne, email, message)"
        ],
        "is_premium": True,
        "icon": "users"
    },
    {
        "action_id": "action_leadership_043",
        "title": "Confiance progressive",
        "description": "Identifiez un domaine où vous pouvez donner plus d'autonomie à votre équipe.",
        "category": "leadership",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Identifiez une décision que vous prenez seul mais qui pourrait être partagée",
            "Évaluez le risque réel si vous laissez quelqu'un d'autre décider",
            "Choisissez une personne prête pour cette responsabilité",
            "Formulez le cadre : tu peux décider tant que... (limites claires)"
        ],
        "is_premium": True,
        "icon": "users"
    },
    {
        "action_id": "action_leadership_044",
        "title": "Rôles clarifiés",
        "description": "Vérifiez que chaque membre de votre équipe connaît précisément ses responsabilités.",
        "category": "leadership",
        "duration_min": 4,
        "duration_max": 7,
        "energy_level": "medium",
        "instructions": [
            "Listez les 3 responsabilités clés de chaque membre de votre équipe",
            "Identifiez les zones de chevauchement ou les trous entre les rôles",
            "Pour chaque zone grise, décidez qui est le propriétaire principal",
            "Planifiez de communiquer ces clarifications lors de votre prochain point d'équipe"
        ],
        "is_premium": True,
        "icon": "users"
    },
    {
        "action_id": "action_leadership_045",
        "title": "Onboarding mental",
        "description": "Préparez l'accueil d'un nouveau membre en listant ce qu'il doit savoir en priorité.",
        "category": "leadership",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Imaginez qu'un nouveau membre rejoint votre équipe demain",
            "Listez les 5 choses qu'il doit absolument savoir la première semaine",
            "Identifiez les 3 personnes clés qu'il doit rencontrer en priorité",
            "Notez le piège ou malentendu courant que vous aimeriez lui épargner"
        ],
        "is_premium": True,
        "icon": "users"
    },
    {
        "action_id": "action_leadership_046",
        "title": "Énergie d'équipe",
        "description": "Cartographiez l'énergie de votre équipe pour optimiser la répartition des tâches.",
        "category": "leadership",
        "duration_min": 4,
        "duration_max": 7,
        "energy_level": "high",
        "instructions": [
            "Pour chaque membre, notez ce qui le dynamise vs ce qui l'épuise",
            "Identifiez les tâches assignées qui vont contre l'énergie naturelle de chacun",
            "Cherchez des réassignations possibles où les forces des uns compensent les faiblesses des autres",
            "Planifiez une conversation informelle pour valider vos observations"
        ],
        "is_premium": True,
        "icon": "users"
    },
    {
        "action_id": "action_leadership_047",
        "title": "Cercle de parole",
        "description": "Préparez un format de tour de table inclusif pour votre prochaine réunion.",
        "category": "leadership",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "high",
        "instructions": [
            "Choisissez une question ouverte pour lancer le tour de table",
            "Définissez un format clair : 1 minute par personne, pas d'interruption",
            "Prévoyez de commencer vous-même pour donner l'exemple du ton souhaité",
            "Préparez une question de relance pour les personnes qui répondent brièvement"
        ],
        "is_premium": True,
        "icon": "users"
    },
    {
        "action_id": "action_leadership_048",
        "title": "Mentorat inversé",
        "description": "Identifiez ce que vous pourriez apprendre d'un junior de votre équipe.",
        "category": "leadership",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "high",
        "instructions": [
            "Pensez à un membre junior de votre équipe et ses compétences uniques",
            "Identifiez un domaine où il est meilleur que vous (outil, technologie, approche)",
            "Formulez une demande d'apprentissage sincère et non condescendante",
            "Planifiez 15 minutes pour lui demander de vous montrer son expertise"
        ],
        "is_premium": True,
        "icon": "users"
    },
    {
        "action_id": "action_leadership_049",
        "title": "Célébration micro",
        "description": "Trouvez une petite victoire d'équipe à célébrer pour renforcer la cohésion.",
        "category": "leadership",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "high",
        "instructions": [
            "Identifiez une petite victoire récente que l'équipe n'a pas célébrée",
            "Choisissez un format de célébration adapté (message, mention en réunion, café offert)",
            "Formulez pourquoi cette victoire compte pour l'objectif global",
            "Partagez-le avec l'équipe en nommant les contributeurs spécifiques"
        ],
        "is_premium": True,
        "icon": "users"
    },
    {
        "action_id": "action_leadership_050",
        "title": "Héritage quotidien",
        "description": "Réfléchissez à l'impact que vous voulez laisser sur votre équipe chaque jour.",
        "category": "leadership",
        "duration_min": 3,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Demandez-vous : si je quittais cette équipe demain, de quoi se souviendrait-on ?",
            "Identifiez l'écart entre cette réponse et ce que vous aimeriez laisser",
            "Choisissez un comportement quotidien qui réduirait cet écart",
            "Engagez-vous à pratiquer ce comportement aujourd'hui dans une interaction"
        ],
        "is_premium": True,
        "icon": "users"
    },
]
