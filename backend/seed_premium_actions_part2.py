"""
InFinea Premium Micro-Actions — Part 2
Categories: finance, relations, mental_health, entrepreneurship
200 actions total (50 per category)
"""

PREMIUM_ACTIONS_PART2 = [
    # =========================================================================
    # FINANCE (50 actions) — icon: trending-up
    # =========================================================================
    # --- Budgeting (10) ---
    {
        "action_id": "action_finance_001",
        "title": "Audit express",
        "description": "Passez en revue vos 3 dernières dépenses pour identifier un schéma de consommation.",
        "category": "finance",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Ouvrez votre app bancaire ou relevé récent",
            "Notez les 3 dernières dépenses non essentielles",
            "Classez-les par nécessité (1 à 5)",
            "Identifiez une dépense que vous pourriez réduire"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    {
        "action_id": "action_finance_002",
        "title": "Chasse aux abonnements",
        "description": "Repérez un abonnement oublié ou sous-utilisé que vous pourriez résilier.",
        "category": "finance",
        "duration_min": 4,
        "duration_max": 10,
        "energy_level": "low",
        "instructions": [
            "Listez tous vos abonnements actifs (streaming, apps, box)",
            "Notez la dernière fois que vous avez utilisé chacun",
            "Marquez ceux utilisés moins d'une fois par mois",
            "Résiliez ou mettez en pause celui qui a le moins de valeur"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    {
        "action_id": "action_finance_003",
        "title": "Défi zéro dépense",
        "description": "Planifiez une journée sans aucune dépense non essentielle.",
        "category": "finance",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Choisissez un jour cette semaine pour le défi",
            "Préparez ce dont vous aurez besoin la veille (repas, transport)",
            "Notez les tentations de dépense que vous ressentez ce jour-là",
            "Calculez combien vous avez économisé en fin de journée"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    {
        "action_id": "action_finance_004",
        "title": "Comparateur minute",
        "description": "Comparez le prix d'un achat récurrent pour trouver une alternative moins chère.",
        "category": "finance",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Choisissez un produit que vous achetez chaque semaine",
            "Cherchez 3 alternatives (marque distributeur, vrac, autre enseigne)",
            "Comparez le prix au kilo ou à l'unité",
            "Calculez l'économie annuelle si vous changiez"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    {
        "action_id": "action_finance_005",
        "title": "Enveloppe mentale",
        "description": "Définissez un budget plafond pour une catégorie de dépenses cette semaine.",
        "category": "finance",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Choisissez une catégorie (resto, café, sorties, vêtements)",
            "Calculez votre dépense moyenne hebdomadaire dans cette catégorie",
            "Fixez un plafond 20% inférieur à cette moyenne",
            "Notez ce plafond dans votre téléphone avec un rappel quotidien"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    {
        "action_id": "action_finance_006",
        "title": "Épargne automatique",
        "description": "Mettez en place un virement automatique vers votre épargne, même minime.",
        "category": "finance",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Calculez 5% de vos revenus mensuels",
            "Ouvrez votre app bancaire et allez dans les virements programmés",
            "Créez un virement récurrent vers un compte épargne",
            "Programmez-le le lendemain de la réception de votre salaire"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    {
        "action_id": "action_finance_007",
        "title": "Ticket de caisse",
        "description": "Photographiez et analysez votre dernier ticket pour repérer les achats impulsifs.",
        "category": "finance",
        "duration_min": 2,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Prenez votre dernier ticket de caisse en photo",
            "Surlignez les achats non planifiés",
            "Calculez le pourcentage d'achats impulsifs",
            "Écrivez une règle personnelle pour réduire ces achats (ex: attendre 24h)"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    {
        "action_id": "action_finance_008",
        "title": "Règle des 48h",
        "description": "Appliquez un délai de réflexion avant tout achat non essentiel.",
        "category": "finance",
        "duration_min": 2,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Identifiez un achat que vous envisagez en ce moment",
            "Notez-le avec la date et le prix dans une note dédiée",
            "Programmez un rappel dans 48 heures",
            "Si vous en avez toujours envie après 48h, autorisez-vous l'achat"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    {
        "action_id": "action_finance_009",
        "title": "Bilan du mois",
        "description": "Faites un bilan financier rapide de votre mois en 5 minutes.",
        "category": "finance",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Notez vos revenus totaux du mois",
            "Additionnez vos dépenses fixes (loyer, assurance, abonnements)",
            "Estimez vos dépenses variables (courses, sorties, transport)",
            "Calculez votre taux d'épargne (revenus - dépenses) / revenus × 100"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    {
        "action_id": "action_finance_010",
        "title": "Défi tirelire",
        "description": "Lancez un micro-défi d'épargne progressif sur 7 jours.",
        "category": "finance",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Jour 1 : mettez 1€ de côté, Jour 2 : 2€, etc.",
            "Utilisez un bocal physique ou un compte séparé",
            "Notez chaque jour le montant cumulé",
            "À la fin de la semaine, vous aurez 28€ — décidez de leur usage"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    # --- Investment basics (10) ---
    {
        "action_id": "action_finance_011",
        "title": "Lecture de marché",
        "description": "Consultez un indicateur boursier majeur et comprenez sa tendance actuelle.",
        "category": "finance",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Recherchez le CAC 40 ou le S&P 500 du jour",
            "Notez s'il est en hausse ou en baisse et de combien (%)",
            "Lisez un titre d'actualité qui explique ce mouvement",
            "Écrivez en une phrase ce que vous en retenez"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    {
        "action_id": "action_finance_012",
        "title": "Check portfolio",
        "description": "Vérifiez la performance de vos placements et notez un point d'attention.",
        "category": "finance",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Connectez-vous à votre app de placements (PEA, assurance-vie, etc.)",
            "Notez la performance globale depuis le début de l'année",
            "Identifiez votre meilleur et votre pire placement",
            "Décidez si une action est nécessaire (rééquilibrage, versement)"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    {
        "action_id": "action_finance_013",
        "title": "Intérêts composés",
        "description": "Simulez l'effet des intérêts composés sur une petite épargne régulière.",
        "category": "finance",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "medium",
        "instructions": [
            "Choisissez un montant mensuel que vous pourriez investir (même 50€)",
            "Utilisez un simulateur en ligne d'intérêts composés",
            "Testez avec un rendement de 7% sur 10, 20 et 30 ans",
            "Notez les résultats — la différence entre 20 et 30 ans va vous surprendre"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    {
        "action_id": "action_finance_014",
        "title": "Veille financière",
        "description": "Lisez un article financier et extrayez-en une idée applicable à votre situation.",
        "category": "finance",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Choisissez une source fiable (Les Échos, BFM Bourse, Maddyness)",
            "Lisez un article sur un sujet d'investissement qui vous intéresse",
            "Résumez l'idée principale en 2 phrases",
            "Notez une action concrète que cela vous inspire pour vos finances"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    {
        "action_id": "action_finance_015",
        "title": "Risque & rendement",
        "description": "Évaluez votre profil de risque en répondant à 4 questions simples.",
        "category": "finance",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Demandez-vous : si mon placement perdait 20%, je vendrais ou j'attendrais ?",
            "Notez votre horizon de placement (quand aurez-vous besoin de cet argent ?)",
            "Évaluez votre capacité d'épargne mensuelle",
            "Déduisez si votre profil est prudent, équilibré ou dynamique"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    {
        "action_id": "action_finance_016",
        "title": "ETF découverte",
        "description": "Découvrez ce qu'est un ETF et pourquoi c'est un outil d'investissement populaire.",
        "category": "finance",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Cherchez la définition d'un ETF (Exchange Traded Fund)",
            "Identifiez 3 ETF populaires en France (ex: Lyxor MSCI World)",
            "Comparez les frais de gestion d'un ETF vs un fonds classique",
            "Notez si cet outil correspond à votre profil de risque"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    {
        "action_id": "action_finance_017",
        "title": "Dividende express",
        "description": "Comprenez le mécanisme des dividendes en analysant un exemple réel.",
        "category": "finance",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Choisissez une entreprise du CAC 40 que vous connaissez",
            "Recherchez son dernier dividende par action",
            "Calculez le rendement : dividende / prix de l'action × 100",
            "Comparez ce rendement avec le taux de votre livret A"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    {
        "action_id": "action_finance_018",
        "title": "Inflation check",
        "description": "Calculez l'impact réel de l'inflation sur votre épargne non investie.",
        "category": "finance",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Notez le montant de votre épargne sur compte courant ou livret",
            "Recherchez le taux d'inflation actuel en France",
            "Calculez la perte de pouvoir d'achat annuelle (épargne × taux d'inflation)",
            "Réfléchissez à un placement qui pourrait battre l'inflation"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    {
        "action_id": "action_finance_019",
        "title": "PEA ou assurance-vie",
        "description": "Comparez les deux enveloppes fiscales principales pour choisir la vôtre.",
        "category": "finance",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "high",
        "instructions": [
            "Listez les avantages du PEA (fiscalité après 5 ans, actions européennes)",
            "Listez les avantages de l'assurance-vie (diversification, transmission)",
            "Comparez les plafonds et les conditions de retrait",
            "Déterminez laquelle correspond le mieux à votre objectif principal"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    {
        "action_id": "action_finance_020",
        "title": "Watchlist perso",
        "description": "Créez une liste de suivi de 5 actifs qui vous intéressent.",
        "category": "finance",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Choisissez 5 actifs (actions, ETF, crypto) qui vous intriguent",
            "Notez leur prix actuel dans une note ou un tableur",
            "Ajoutez une raison pour chacun (pourquoi cet actif ?)",
            "Programmez un rappel hebdo pour suivre leur évolution"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    # --- Money mindset (10) ---
    {
        "action_id": "action_finance_021",
        "title": "Journal d'abondance",
        "description": "Notez 3 choses pour lesquelles vous êtes financièrement reconnaissant aujourd'hui.",
        "category": "finance",
        "duration_min": 2,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Prenez une feuille ou ouvrez une note",
            "Écrivez 3 choses que votre argent vous permet de faire ou d'avoir",
            "Pour chacune, notez l'émotion positive associée",
            "Relisez cette liste à voix haute pour ancrer le sentiment de gratitude"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    {
        "action_id": "action_finance_022",
        "title": "Croyance limitante",
        "description": "Identifiez et remettez en question une croyance négative sur l'argent.",
        "category": "finance",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "medium",
        "instructions": [
            "Complétez la phrase : 'L'argent, c'est...' avec la première idée qui vient",
            "Demandez-vous d'où vient cette croyance (famille, éducation, société)",
            "Cherchez un contre-exemple dans votre vie ou celle de quelqu'un",
            "Reformulez cette croyance en version positive et réaliste"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    {
        "action_id": "action_finance_023",
        "title": "Vision board financier",
        "description": "Visualisez un objectif financier en le rendant concret et mesurable.",
        "category": "finance",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Choisissez un objectif financier à 1 an (voyage, fonds d'urgence, achat)",
            "Trouvez une image qui le représente et enregistrez-la sur votre téléphone",
            "Écrivez le montant exact nécessaire et la date cible",
            "Calculez le montant mensuel à épargner pour y arriver"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    {
        "action_id": "action_finance_024",
        "title": "Relation à l'argent",
        "description": "Explorez votre rapport émotionnel à l'argent en répondant à 4 questions.",
        "category": "finance",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "low",
        "instructions": [
            "Quel est votre premier souvenir lié à l'argent ?",
            "Quand vous dépensez, ressentez-vous plutôt de la culpabilité ou du plaisir ?",
            "Parlez-vous d'argent facilement avec vos proches ? Pourquoi ?",
            "Écrivez une intention pour améliorer votre relation à l'argent"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    {
        "action_id": "action_finance_025",
        "title": "Micro-objectif épargne",
        "description": "Fixez un objectif d'épargne atteignable dans les 30 prochains jours.",
        "category": "finance",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Choisissez un montant réaliste à économiser ce mois-ci (50€, 100€, 200€)",
            "Identifiez précisément d'où viendra cette économie",
            "Notez cet objectif quelque part de visible (fond d'écran, post-it)",
            "Créez un tracker simple pour cocher chaque jour sans dépense inutile"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    {
        "action_id": "action_finance_026",
        "title": "Richesse intérieure",
        "description": "Listez vos richesses non financières pour élargir votre vision de la prospérité.",
        "category": "finance",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Écrivez 5 richesses non monétaires (santé, relations, compétences, temps, liberté)",
            "Pour chacune, notez comment elle contribue à votre bien-être",
            "Identifiez celle que vous négligez le plus en ce moment",
            "Décidez d'une action pour la cultiver cette semaine"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    {
        "action_id": "action_finance_027",
        "title": "Mentor financier",
        "description": "Identifiez une personne dont vous admirez la gestion financière et analysez ses habitudes.",
        "category": "finance",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Pensez à quelqu'un (proche ou public) qui gère bien son argent",
            "Listez 3 habitudes financières que cette personne semble avoir",
            "Choisissez une habitude que vous pourriez adopter",
            "Planifiez un premier pas concret pour la mettre en pratique"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    {
        "action_id": "action_finance_028",
        "title": "Détox achat",
        "description": "Analysez votre dernier achat impulsif pour comprendre le déclencheur émotionnel.",
        "category": "finance",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Rappelez-vous votre dernier achat impulsif",
            "Notez votre état émotionnel au moment de l'achat (ennui, stress, euphorie)",
            "Évaluez honnêtement si cet achat a comblé le besoin ressenti",
            "Écrivez une alternative gratuite pour gérer cette émotion la prochaine fois"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    {
        "action_id": "action_finance_029",
        "title": "Futur moi",
        "description": "Écrivez une lettre de votre futur vous financièrement libre à votre vous actuel.",
        "category": "finance",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Imaginez-vous dans 10 ans, financièrement serein",
            "Décrivez votre journée type dans cette situation",
            "Écrivez un conseil que ce futur vous donnerait au vous d'aujourd'hui",
            "Identifiez la première action à faire dès maintenant vers ce futur"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    {
        "action_id": "action_finance_030",
        "title": "Valeurs & dépenses",
        "description": "Vérifiez si vos dépenses reflètent réellement vos valeurs profondes.",
        "category": "finance",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Listez vos 5 valeurs les plus importantes (famille, liberté, santé, etc.)",
            "Regardez vos 10 dernières dépenses significatives",
            "Associez chaque dépense à une valeur (ou notez 'aucune')",
            "Identifiez le décalage et ajustez un poste de dépense"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    # --- Financial literacy (10) ---
    {
        "action_id": "action_finance_031",
        "title": "Mot du jour",
        "description": "Apprenez un terme financier et utilisez-le dans une phrase de votre quotidien.",
        "category": "finance",
        "duration_min": 2,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Choisissez un terme financier que vous ne maîtrisez pas (ex: EBITDA, P/E ratio, hedge)",
            "Recherchez sa définition simple en 2 minutes",
            "Écrivez une phrase qui l'applique à votre situation personnelle",
            "Expliquez-le à quelqu'un ou notez-le dans un carnet dédié"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    {
        "action_id": "action_finance_032",
        "title": "Ratio vital",
        "description": "Calculez votre ratio dépenses fixes / revenus pour évaluer votre flexibilité.",
        "category": "finance",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Additionnez toutes vos charges fixes mensuelles",
            "Divisez par vos revenus nets mensuels",
            "Multipliez par 100 pour obtenir le pourcentage",
            "Objectif : rester sous 50%. Notez votre résultat et une piste d'amélioration"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    {
        "action_id": "action_finance_033",
        "title": "Bilan patrimonial",
        "description": "Faites un snapshot de votre patrimoine net en 5 minutes.",
        "category": "finance",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "high",
        "instructions": [
            "Listez tous vos actifs (épargne, investissements, biens immobiliers)",
            "Listez toutes vos dettes (crédit immobilier, conso, étudiant)",
            "Calculez : actifs - dettes = patrimoine net",
            "Comparez avec l'an dernier — la tendance est-elle positive ?"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    {
        "action_id": "action_finance_034",
        "title": "Lecture de bilan",
        "description": "Apprenez à lire les 3 lignes clés d'un bilan d'entreprise.",
        "category": "finance",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "high",
        "instructions": [
            "Trouvez le bilan d'une entreprise cotée (ex: rapport annuel en ligne)",
            "Repérez le chiffre d'affaires, le résultat net et la dette totale",
            "Calculez la marge nette : résultat net / chiffre d'affaires × 100",
            "Comparez avec un concurrent du même secteur"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    {
        "action_id": "action_finance_035",
        "title": "Fiscalité express",
        "description": "Identifiez une niche fiscale ou déduction dont vous ne profitez pas encore.",
        "category": "finance",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "high",
        "instructions": [
            "Recherchez les principales réductions d'impôt en France (dons, emploi à domicile, PER)",
            "Identifiez celles auxquelles vous pourriez prétendre",
            "Estimez l'économie potentielle sur votre prochaine déclaration",
            "Notez les pièces justificatives à rassembler"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    {
        "action_id": "action_finance_036",
        "title": "Taux réel",
        "description": "Calculez le coût réel d'un crédit que vous avez ou que vous envisagez.",
        "category": "finance",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Prenez un crédit en cours ou une offre de prêt",
            "Notez le montant total remboursé (mensualité × nombre de mois)",
            "Soustrayez le montant emprunté pour obtenir le coût total du crédit",
            "Divisez par le montant emprunté pour obtenir le surcoût en pourcentage"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    {
        "action_id": "action_finance_037",
        "title": "Cash flow perso",
        "description": "Cartographiez vos flux de trésorerie pour savoir où va votre argent.",
        "category": "finance",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "high",
        "instructions": [
            "Dessinez deux colonnes : entrées et sorties",
            "Listez chaque source de revenu avec son montant",
            "Listez chaque catégorie de dépense avec son montant estimé",
            "Identifiez votre cash flow net et les 2 postes de sortie les plus gros"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    {
        "action_id": "action_finance_038",
        "title": "Fonds d'urgence",
        "description": "Évaluez si votre fonds d'urgence est suffisant et planifiez son renforcement.",
        "category": "finance",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Calculez vos dépenses mensuelles incompressibles",
            "Multipliez par 3 (minimum) ou 6 (recommandé) mois",
            "Comparez avec votre épargne disponible actuelle",
            "Si insuffisant, calculez combien épargner chaque mois pour atteindre l'objectif en 1 an"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    {
        "action_id": "action_finance_039",
        "title": "Benchmark salaire",
        "description": "Vérifiez si votre rémunération est alignée avec le marché.",
        "category": "finance",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "high",
        "instructions": [
            "Recherchez le salaire médian de votre poste sur Glassdoor ou LinkedIn Salary",
            "Comparez avec votre rémunération totale (fixe + variable + avantages)",
            "Identifiez les facteurs qui justifient un écart (expérience, localisation)",
            "Si sous-évalué, notez 3 arguments pour une négociation future"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    {
        "action_id": "action_finance_040",
        "title": "Retraite rapide",
        "description": "Estimez rapidement votre future pension de retraite et le gap à combler.",
        "category": "finance",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "high",
        "instructions": [
            "Connectez-vous à info-retraite.fr ou estimez 50-60% de votre salaire actuel",
            "Calculez le manque à gagner mensuel vs votre train de vie souhaité",
            "Multipliez ce gap par 12 mois × 25 ans de retraite estimée",
            "Divisez par le nombre d'années avant votre retraite — c'est votre objectif d'épargne annuelle"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    # --- Side income (10) ---
    {
        "action_id": "action_finance_041",
        "title": "Inventaire talents",
        "description": "Listez vos compétences monétisables que vous sous-exploitez actuellement.",
        "category": "finance",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Listez 10 compétences que vous possédez (techniques, créatives, sociales)",
            "Pour chacune, demandez-vous si quelqu'un paierait pour ce savoir",
            "Marquez les 3 plus monétisables avec un potentiel horaire estimé",
            "Choisissez celle que vous pourriez proposer dès cette semaine"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    {
        "action_id": "action_finance_042",
        "title": "Audit de temps",
        "description": "Identifiez des créneaux sous-utilisés que vous pourriez convertir en revenus.",
        "category": "finance",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Listez vos activités sur une journée type heure par heure",
            "Identifiez les créneaux de temps passif (scrolling, attente, trajet)",
            "Calculez le total d'heures récupérables par semaine",
            "Imaginez une activité productive que vous pourriez y glisser"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    {
        "action_id": "action_finance_043",
        "title": "Scan d'opportunités",
        "description": "Explorez 3 plateformes de freelance pour repérer une mission à votre portée.",
        "category": "finance",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "high",
        "instructions": [
            "Visitez Malt, Fiverr ou Upwork",
            "Recherchez des missions correspondant à vos compétences",
            "Notez 3 missions faisables avec leur tarif proposé",
            "Évaluez le temps nécessaire et calculez votre taux horaire potentiel"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    {
        "action_id": "action_finance_044",
        "title": "Micro-business canvas",
        "description": "Esquissez une idée de micro-business en répondant à 4 questions clés.",
        "category": "finance",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "high",
        "instructions": [
            "Quel problème résolvez-vous ? (pour qui exactement ?)",
            "Quelle est votre solution en une phrase ?",
            "Combien les gens paieraient-ils ? (recherchez des prix existants)",
            "Comment attireriez-vous vos 10 premiers clients ?"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    {
        "action_id": "action_finance_045",
        "title": "Vente éclair",
        "description": "Identifiez un objet chez vous que vous pourriez vendre aujourd'hui.",
        "category": "finance",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "low",
        "instructions": [
            "Faites le tour d'une pièce et repérez un objet inutilisé depuis 6 mois",
            "Recherchez son prix de vente moyen sur Leboncoin ou Vinted",
            "Prenez 2-3 photos attractives avec bonne lumière",
            "Rédigez une annonce courte et publiez-la"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    {
        "action_id": "action_finance_046",
        "title": "Revenu passif idée",
        "description": "Brainstormez une source de revenu passif adaptée à vos ressources actuelles.",
        "category": "finance",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "high",
        "instructions": [
            "Listez vos atouts : compétences, réseau, capital disponible, temps",
            "Explorez 3 pistes : contenu digital, investissement locatif, affiliation",
            "Évaluez chaque piste : investissement initial, temps avant premier revenu",
            "Sélectionnez la plus réaliste et notez 3 premières étapes"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    {
        "action_id": "action_finance_047",
        "title": "Pricing stratégique",
        "description": "Fixez le juste prix pour un service ou produit que vous pourriez proposer.",
        "category": "finance",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Choisissez un service que vous pourriez vendre",
            "Recherchez les prix pratiqués par 5 concurrents",
            "Calculez votre prix plancher (coût horaire × temps + charges)",
            "Positionnez-vous : entrée de gamme, milieu ou premium, et justifiez"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    {
        "action_id": "action_finance_048",
        "title": "Skill stacking",
        "description": "Combinez deux de vos compétences pour créer une offre unique sur le marché.",
        "category": "finance",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "high",
        "instructions": [
            "Listez vos 5 meilleures compétences",
            "Testez des combinaisons de 2 compétences (ex: design + psychologie)",
            "Pour chaque combinaison, imaginez un service ou produit concret",
            "Identifiez la combinaison la plus rare et la plus demandée"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    {
        "action_id": "action_finance_049",
        "title": "Premier client",
        "description": "Préparez un plan d'action pour décrocher votre tout premier client.",
        "category": "finance",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "high",
        "instructions": [
            "Définissez précisément votre offre en une phrase",
            "Listez 10 personnes dans votre réseau qui pourraient être intéressées",
            "Rédigez un message court et personnalisé pour chacune",
            "Envoyez les 3 premiers messages aujourd'hui"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    {
        "action_id": "action_finance_050",
        "title": "Cashback optimisé",
        "description": "Activez ou optimisez vos programmes de cashback pour gagner sur vos achats courants.",
        "category": "finance",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Listez vos 5 enseignes ou sites d'achat les plus fréquents",
            "Vérifiez si votre banque offre du cashback sur ces enseignes",
            "Explorez une app de cashback (iGraal, Poulpeo, Widilo)",
            "Activez le cashback pour votre prochain achat prévu"
        ],
        "is_premium": True,
        "icon": "trending-up"
    },
    # =========================================================================
    # RELATIONS (50 actions) — icon: message-circle
    # =========================================================================
    # --- Active communication (10) ---
    {
        "action_id": "action_relations_001",
        "title": "Écoute profonde",
        "description": "Pratiquez l'écoute active lors de votre prochaine conversation en appliquant 4 règles.",
        "category": "relations",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Lors de votre prochaine conversation, ne coupez pas la parole pendant 3 minutes",
            "Reformulez ce que l'autre a dit avant de répondre",
            "Posez une question ouverte qui approfondit le sujet",
            "Notez après coup : qu'avez-vous appris que vous auriez manqué autrement ?"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    {
        "action_id": "action_relations_002",
        "title": "Message CNV",
        "description": "Rédigez un message en Communication Non Violente sur un sujet qui vous tient à cœur.",
        "category": "relations",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Choisissez une situation récente qui vous a frustré avec quelqu'un",
            "Décrivez les faits objectifs (sans jugement ni interprétation)",
            "Exprimez votre sentiment et le besoin non satisfait derrière",
            "Formulez une demande claire et réalisable"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    {
        "action_id": "action_relations_003",
        "title": "Assertivité minute",
        "description": "Entraînez-vous à exprimer un besoin de manière claire et respectueuse.",
        "category": "relations",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "medium",
        "instructions": [
            "Identifiez un besoin que vous n'osez pas exprimer en ce moment",
            "Écrivez votre demande en utilisant le 'je' plutôt que le 'tu'",
            "Ajoutez le contexte et la raison de votre demande",
            "Entraînez-vous à le dire à voix haute devant un miroir"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    {
        "action_id": "action_relations_004",
        "title": "Silence éloquent",
        "description": "Utilisez le pouvoir du silence dans une conversation pour créer de l'espace.",
        "category": "relations",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Lors de votre prochaine discussion, après que l'autre ait fini de parler, attendez 3 secondes",
            "Observez ce qui se passe : souvent, l'autre approfondit sa pensée",
            "Résistez à l'envie de combler chaque silence",
            "Notez ensuite si la conversation a semblé plus riche ou plus profonde"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    {
        "action_id": "action_relations_005",
        "title": "Question puissante",
        "description": "Préparez 3 questions ouvertes qui transforment une conversation banale en échange profond.",
        "category": "relations",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Écrivez 3 questions qui commencent par 'Comment' ou 'Qu'est-ce qui'",
            "Évitez les questions fermées (oui/non) et les 'pourquoi' accusateurs",
            "Testez-en une lors de votre prochain échange",
            "Observez comment la qualité de la conversation change"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    {
        "action_id": "action_relations_006",
        "title": "Feedback sandwich",
        "description": "Pratiquez l'art de donner un retour constructif en 3 couches.",
        "category": "relations",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Pensez à un feedback que vous devez donner à quelqu'un",
            "Commencez par un point positif sincère et spécifique",
            "Formulez le point d'amélioration avec un exemple et une suggestion",
            "Terminez par un encouragement ou une expression de confiance"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    {
        "action_id": "action_relations_007",
        "title": "Miroir verbal",
        "description": "Entraînez-vous à refléter les émotions de votre interlocuteur pour créer de la connexion.",
        "category": "relations",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "medium",
        "instructions": [
            "Lors de votre prochaine conversation, identifiez l'émotion sous-jacente",
            "Nommez-la doucement : 'On dirait que ça te frustre / te passionne'",
            "Observez la réaction — souvent l'autre se sent compris et s'ouvre davantage",
            "Notez l'effet que cette technique a eu sur l'échange"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    {
        "action_id": "action_relations_008",
        "title": "Dire non avec grâce",
        "description": "Formulez un refus respectueux pour une situation où vous avez du mal à dire non.",
        "category": "relations",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "medium",
        "instructions": [
            "Identifiez une demande récente à laquelle vous avez dit oui à contrecœur",
            "Reformulez un refus en 3 parties : remerciement, raison brève, alternative",
            "Exemple : 'Merci de penser à moi. Je ne suis pas disponible, mais je connais quelqu'un qui…'",
            "Entraînez-vous à le dire naturellement"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    {
        "action_id": "action_relations_009",
        "title": "Clarification express",
        "description": "Vérifiez que vous comprenez bien un message ambigu avant de réagir.",
        "category": "relations",
        "duration_min": 2,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Repensez à un message récent (texte, email) qui vous a semblé ambigu",
            "Identifiez au moins 2 interprétations possibles",
            "Rédigez une question de clarification neutre et bienveillante",
            "Envoyez-la ou gardez-la pour la prochaine situation ambiguë"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    {
        "action_id": "action_relations_010",
        "title": "Conversation courageuse",
        "description": "Préparez-vous à aborder un sujet difficile avec bienveillance et structure.",
        "category": "relations",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "high",
        "instructions": [
            "Identifiez une conversation que vous repoussez",
            "Écrivez votre intention positive pour cet échange (pas de blâmer, mais résoudre)",
            "Préparez votre phrase d'ouverture en 'je' avec un ton calme",
            "Anticipez 2 réactions possibles et préparez vos réponses"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    # --- Empathy & understanding (10) ---
    {
        "action_id": "action_relations_011",
        "title": "Dans ses chaussures",
        "description": "Prenez la perspective d'une personne avec qui vous êtes en désaccord.",
        "category": "relations",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Choisissez une personne avec qui vous avez un désaccord récent",
            "Imaginez sa journée, ses contraintes, ses peurs et ses motivations",
            "Écrivez 3 raisons valables pour lesquelles elle pense différemment",
            "Notez si votre ressenti envers cette personne a évolué"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    {
        "action_id": "action_relations_012",
        "title": "Lecture émotionnelle",
        "description": "Aiguisez votre capacité à détecter les émotions non exprimées chez les autres.",
        "category": "relations",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Lors de votre prochain échange, observez le langage corporel de l'autre",
            "Notez mentalement : posture, ton de voix, rythme, expressions faciales",
            "Essayez de deviner l'émotion dominante (même si elle n'est pas verbalisée)",
            "Vérifiez doucement : 'Tu as l'air [émotion], tout va bien ?'"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    {
        "action_id": "action_relations_013",
        "title": "Pont culturel",
        "description": "Apprenez un usage ou une valeur d'une culture différente de la vôtre.",
        "category": "relations",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "low",
        "instructions": [
            "Choisissez une culture qui vous intrigue ou que vous côtoyez",
            "Recherchez un usage social ou une valeur fondamentale de cette culture",
            "Identifiez un point commun avec vos propres valeurs",
            "Réfléchissez à comment intégrer cet apprentissage dans vos interactions"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    {
        "action_id": "action_relations_014",
        "title": "Carte d'empathie",
        "description": "Créez une carte d'empathie pour mieux comprendre un proche.",
        "category": "relations",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Choisissez un proche que vous aimeriez mieux comprendre",
            "Notez ce qu'il/elle pense et ressent en ce moment (selon vous)",
            "Notez ce qu'il/elle dit et fait au quotidien",
            "Identifiez ses frustrations et ses aspirations profondes"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    {
        "action_id": "action_relations_015",
        "title": "Bénéfice du doute",
        "description": "Réinterprétez une action qui vous a blessé en imaginant une intention positive.",
        "category": "relations",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Repensez à un comportement récent qui vous a agacé ou blessé",
            "Imaginez 3 raisons bienveillantes qui pourraient expliquer ce comportement",
            "Choisissez l'explication la plus charitable et plausible",
            "Observez si votre frustration diminue avec ce changement de perspective"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    {
        "action_id": "action_relations_016",
        "title": "Journal d'impact",
        "description": "Notez comment vos paroles et actions ont affecté les autres aujourd'hui.",
        "category": "relations",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "En fin de journée, repensez à 3 interactions significatives",
            "Pour chacune, notez l'impact probable de vos mots sur l'autre",
            "Identifiez un moment où vous auriez pu être plus attentif",
            "Formulez une intention pour demain basée sur cette réflexion"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    {
        "action_id": "action_relations_017",
        "title": "Compassion active",
        "description": "Transformez votre empathie en action concrète pour quelqu'un qui traverse un moment difficile.",
        "category": "relations",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "high",
        "instructions": [
            "Pensez à quelqu'un dans votre entourage qui traverse une difficulté",
            "Demandez-vous ce dont cette personne a le plus besoin (écoute, aide, espace)",
            "Choisissez un geste simple et faisable aujourd'hui",
            "Réalisez ce geste sans attendre de reconnaissance en retour"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    {
        "action_id": "action_relations_018",
        "title": "Écoute sans conseil",
        "description": "Entraînez-vous à écouter quelqu'un sans essayer de résoudre son problème.",
        "category": "relations",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Lors de la prochaine confidence d'un proche, retenez-vous de donner des conseils",
            "Utilisez des phrases comme 'Je comprends' ou 'Ça a dû être dur'",
            "Posez des questions pour l'aider à trouver sa propre solution",
            "Demandez : 'Tu as besoin que je t'écoute ou que je t'aide à trouver une solution ?'"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    {
        "action_id": "action_relations_019",
        "title": "Détecteur de besoins",
        "description": "Identifiez le besoin caché derrière le comportement irritant de quelqu'un.",
        "category": "relations",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "high",
        "instructions": [
            "Pensez à un comportement récurrent qui vous agace chez quelqu'un",
            "Demandez-vous quel besoin fondamental se cache derrière (reconnaissance, sécurité, connexion)",
            "Réfléchissez à comment vous pourriez répondre à ce besoin autrement",
            "Testez cette approche lors de votre prochain échange avec cette personne"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    {
        "action_id": "action_relations_020",
        "title": "Curiosité sincère",
        "description": "Posez une question que vous n'avez jamais osé poser à un proche pour mieux le connaître.",
        "category": "relations",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "high",
        "instructions": [
            "Choisissez un proche que vous fréquentez souvent mais connaissez peu en profondeur",
            "Préparez une question sincère et inhabituelle (ex: 'Quel est ton plus beau souvenir d'enfance ?')",
            "Posez-la au bon moment, quand l'ambiance est détendue",
            "Écoutez la réponse avec toute votre attention, sans interrompre"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    # --- Relationship maintenance (10) ---
    {
        "action_id": "action_relations_021",
        "title": "Message gratitude",
        "description": "Envoyez un message de remerciement sincère à quelqu'un qui compte pour vous.",
        "category": "relations",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Pensez à une personne qui a eu un impact positif sur votre vie récemment",
            "Rédigez un message spécifique : dites exactement ce qu'elle a fait et l'effet sur vous",
            "Évitez les formules génériques — soyez précis et personnel",
            "Envoyez-le maintenant, sans attendre une occasion spéciale"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    {
        "action_id": "action_relations_022",
        "title": "Check-in amical",
        "description": "Reprenez contact avec un ami que vous n'avez pas vu depuis longtemps.",
        "category": "relations",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Scrollez vos contacts et trouvez un ami que vous n'avez pas contacté depuis 3+ mois",
            "Envoyez un message court et chaleureux qui montre que vous pensez à lui/elle",
            "Faites référence à un souvenir commun ou un intérêt partagé",
            "Proposez un créneau pour se voir ou s'appeler"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    {
        "action_id": "action_relations_023",
        "title": "Moment qualité",
        "description": "Planifiez un micro-moment de qualité avec un proche dans les prochaines 48h.",
        "category": "relations",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Choisissez un proche avec qui vous passez du temps, mais rarement du temps de qualité",
            "Identifiez une activité courte qui vous ferait plaisir à tous les deux (15-30 min)",
            "Bloquez un créneau dans les 48h et proposez-le",
            "Pendant ce moment : téléphone en mode avion, 100% présent"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    {
        "action_id": "action_relations_024",
        "title": "Rituel de couple",
        "description": "Créez ou renforcez un micro-rituel quotidien avec votre partenaire.",
        "category": "relations",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Identifiez un moment de la journée que vous partagez toujours (matin, soir)",
            "Proposez un rituel de 5 minutes : café ensemble, question du jour, marche rapide",
            "Discutez-en avec votre partenaire et ajustez selon ses préférences",
            "Testez-le pendant 7 jours et évaluez l'impact sur votre connexion"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    {
        "action_id": "action_relations_025",
        "title": "Anniversaire préparé",
        "description": "Vérifiez les dates importantes à venir et préparez un geste personnalisé.",
        "category": "relations",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "low",
        "instructions": [
            "Consultez les anniversaires et dates importantes du mois prochain",
            "Choisissez une personne et réfléchissez à un geste qui lui correspondrait",
            "Préparez-le à l'avance (cadeau, message, surprise)",
            "Ajoutez un rappel 3 jours avant pour ne pas oublier"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    {
        "action_id": "action_relations_026",
        "title": "Compliment précis",
        "description": "Offrez un compliment ultra-spécifique à quelqu'un aujourd'hui.",
        "category": "relations",
        "duration_min": 2,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Choisissez quelqu'un que vous verrez ou contacterez aujourd'hui",
            "Observez ou rappelez-vous quelque chose de spécifique qu'il/elle fait bien",
            "Formulez un compliment précis : 'J'admire ta façon de [action spécifique]'",
            "Délivrez-le en personne ou par message avec sincérité"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    {
        "action_id": "action_relations_027",
        "title": "Carte relationnelle",
        "description": "Cartographiez votre cercle social pour identifier les relations à nourrir.",
        "category": "relations",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Dessinez 3 cercles concentriques : intime, proche, connaissance",
            "Placez vos relations dans chaque cercle",
            "Identifiez les relations que vous négligez et celles qui vous drainent",
            "Choisissez 2 relations à nourrir activement ce mois-ci"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    {
        "action_id": "action_relations_028",
        "title": "Pardon libérateur",
        "description": "Faites un exercice de pardon intérieur pour une rancœur qui vous pèse.",
        "category": "relations",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "high",
        "instructions": [
            "Identifiez une rancœur que vous portez encore envers quelqu'un",
            "Écrivez une lettre de pardon (que vous n'enverrez pas forcément)",
            "Exprimez la blessure, puis la décision de lâcher prise",
            "Terminez par : 'Je choisis de me libérer de ce poids pour avancer'"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    {
        "action_id": "action_relations_029",
        "title": "Tradition familiale",
        "description": "Créez ou ravivez une petite tradition familiale pour renforcer les liens.",
        "category": "relations",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Repensez à une tradition familiale que vous aimiez enfant",
            "Adaptez-la à votre vie actuelle ou inventez-en une nouvelle",
            "Proposez-la à votre famille (dîner du dimanche, jeu du vendredi, etc.)",
            "Planifiez la première occurrence cette semaine"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    {
        "action_id": "action_relations_030",
        "title": "Acte de service",
        "description": "Faites quelque chose d'utile pour un proche sans qu'il ne le demande.",
        "category": "relations",
        "duration_min": 3,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Observez un proche et identifiez une tâche qui le soulagerait",
            "Réalisez cette tâche discrètement et sans rien attendre en retour",
            "Notez sa réaction quand il/elle découvre ce que vous avez fait",
            "Réfléchissez : quel est le langage de l'amour de cette personne ?"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    # --- Networking & social skills (10) ---
    {
        "action_id": "action_relations_031",
        "title": "Pitch 30 secondes",
        "description": "Préparez votre elevator pitch personnel pour vous présenter avec impact.",
        "category": "relations",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "high",
        "instructions": [
            "Répondez en 1 phrase : qui êtes-vous et que faites-vous d'unique ?",
            "Ajoutez la valeur que vous apportez aux autres",
            "Terminez par un hook : quelque chose qui donne envie d'en savoir plus",
            "Chronométrez et réduisez à 30 secondes maximum"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    {
        "action_id": "action_relations_032",
        "title": "Small talk pro",
        "description": "Maîtrisez l'art de la conversation légère avec la technique FORD.",
        "category": "relations",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "medium",
        "instructions": [
            "Mémorisez FORD : Family, Occupation, Recreation, Dreams",
            "Préparez 2 questions par catégorie (ex: 'Qu'est-ce qui te passionne en dehors du travail ?')",
            "Lors de votre prochain échange informel, utilisez 2 questions FORD",
            "Notez celles qui ont le mieux fonctionné pour votre répertoire personnel"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    {
        "action_id": "action_relations_033",
        "title": "Introduction mémorable",
        "description": "Créez une présentation professionnelle qui marque les esprits.",
        "category": "relations",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "high",
        "instructions": [
            "Au lieu de 'Je suis [titre]', formulez : 'J'aide [qui] à [résultat]'",
            "Ajoutez une anecdote courte qui illustre votre expertise",
            "Préparez une variante formelle et une décontractée",
            "Testez-les sur un proche et demandez laquelle est la plus marquante"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    {
        "action_id": "action_relations_034",
        "title": "Follow-up stratégique",
        "description": "Relancez un contact professionnel intéressant en apportant de la valeur.",
        "category": "relations",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Identifiez un contact pro récent que vous aimeriez revoir",
            "Trouvez un article, un événement ou une ressource pertinente pour cette personne",
            "Envoyez un message personnalisé avec cette valeur ajoutée",
            "Proposez un café ou un appel de 15 minutes pour approfondir"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    {
        "action_id": "action_relations_035",
        "title": "Réseau invisible",
        "description": "Identifiez les liens dormants dans votre réseau qui pourraient créer des opportunités.",
        "category": "relations",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Scrollez vos contacts LinkedIn ou votre carnet d'adresses",
            "Repérez 5 personnes que vous avez perdues de vue mais qui vous inspirent",
            "Classez-les par potentiel de synergie avec vos projets actuels",
            "Envoyez un message à la personne en tête de liste"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    {
        "action_id": "action_relations_036",
        "title": "Langage corporel",
        "description": "Améliorez votre communication non verbale pour projeter confiance et ouverture.",
        "category": "relations",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "high",
        "instructions": [
            "Devant un miroir, observez votre posture naturelle debout",
            "Ajustez : pieds écartés largeur d'épaules, épaules en arrière, menton légèrement levé",
            "Pratiquez un sourire naturel (pensez à quelque chose de drôle)",
            "Maintenez cette posture 2 minutes — observez l'effet sur votre état intérieur"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    {
        "action_id": "action_relations_037",
        "title": "Connecteur humain",
        "description": "Présentez deux personnes de votre réseau qui gagneraient à se connaître.",
        "category": "relations",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "high",
        "instructions": [
            "Pensez à deux personnes ayant des intérêts ou besoins complémentaires",
            "Rédigez un email de mise en relation avec contexte pour chacune",
            "Expliquez pourquoi vous pensez que la rencontre serait bénéfique",
            "Envoyez-le en mettant les deux en copie"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    {
        "action_id": "action_relations_038",
        "title": "Écoute de groupe",
        "description": "Lors d'une prochaine réunion, observez les dynamiques de groupe sans intervenir.",
        "category": "relations",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "low",
        "instructions": [
            "Lors de votre prochaine réunion, restez volontairement silencieux les 10 premières minutes",
            "Observez qui parle le plus, qui écoute, qui est ignoré",
            "Notez les alliances informelles et les tensions visibles",
            "Après la réunion, notez 2 insights sur la dynamique du groupe"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    {
        "action_id": "action_relations_039",
        "title": "Networking event prep",
        "description": "Préparez-vous efficacement pour un prochain événement de networking.",
        "category": "relations",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "high",
        "instructions": [
            "Identifiez un événement professionnel à venir (même virtuel)",
            "Listez 3 personnes que vous aimeriez rencontrer et pourquoi",
            "Préparez une question intéressante pour chacune",
            "Définissez votre objectif : apprendre quoi ? Initier quel type de relation ?"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    {
        "action_id": "action_relations_040",
        "title": "Mémoire des noms",
        "description": "Entraînez votre mémoire pour retenir les prénoms des gens que vous rencontrez.",
        "category": "relations",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "medium",
        "instructions": [
            "Apprenez la technique : répétez le prénom 3 fois dans les 30 premières secondes",
            "Associez le prénom à une image mentale ou un trait distinctif de la personne",
            "Testez-vous : fermez les yeux et rappelez les prénoms des 5 dernières personnes rencontrées",
            "Utilisez cette technique lors de votre prochaine rencontre"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    # --- Conflict resolution (10) ---
    {
        "action_id": "action_relations_041",
        "title": "Désescalade rapide",
        "description": "Apprenez une technique de désescalade pour calmer un échange tendu.",
        "category": "relations",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "high",
        "instructions": [
            "Mémorisez la technique : baisser le volume, ralentir le débit, descendre en tonalité",
            "Entraînez-vous à dire : 'Je comprends que ce soit frustrant, trouvons une solution ensemble'",
            "Pratiquez la respiration 4-7-8 pour rester calme sous pression",
            "Notez cette technique sur votre téléphone pour la retrouver en cas de besoin"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    {
        "action_id": "action_relations_042",
        "title": "Terrain d'entente",
        "description": "Trouvez un compromis gagnant-gagnant pour un désaccord actuel.",
        "category": "relations",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "high",
        "instructions": [
            "Identifiez un désaccord en cours avec quelqu'un",
            "Listez ce qui est non négociable pour vous ET pour l'autre",
            "Identifiez les zones de flexibilité de chaque côté",
            "Proposez un compromis qui respecte les non-négociables des deux parties"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    {
        "action_id": "action_relations_043",
        "title": "Feedback constructif",
        "description": "Donnez un retour honnête mais bienveillant à un collègue ou proche.",
        "category": "relations",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "high",
        "instructions": [
            "Utilisez la structure SBI : Situation, Comportement, Impact",
            "Ex: 'Lors de la réunion (S), quand tu as interrompu Marie (B), elle semblait frustrée (I)'",
            "Ajoutez une suggestion d'alternative positive",
            "Terminez en demandant le point de vue de l'autre"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    {
        "action_id": "action_relations_044",
        "title": "Recevoir le feedback",
        "description": "Pratiquez l'art de recevoir un feedback négatif avec grâce et ouverture.",
        "category": "relations",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "medium",
        "instructions": [
            "Rappelez-vous le dernier feedback négatif que vous avez reçu",
            "Séparez le message de l'émotion : qu'y a-t-il d'objectivement vrai ?",
            "Formulez une réponse type : 'Merci pour ce retour, je vais y réfléchir'",
            "Identifiez une action concrète d'amélioration que ce feedback inspire"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    {
        "action_id": "action_relations_045",
        "title": "Excuse sincère",
        "description": "Apprenez la structure d'une excuse efficace et préparez-en une si nécessaire.",
        "category": "relations",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "high",
        "instructions": [
            "Une bonne excuse contient : reconnaissance du tort, empathie, responsabilité, réparation",
            "Identifiez une situation où vous devez des excuses (même petite)",
            "Rédigez vos excuses en suivant cette structure, sans 'mais'",
            "Présentez-les en personne si possible, ou par un message personnel"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    {
        "action_id": "action_relations_046",
        "title": "Limites saines",
        "description": "Définissez et communiquez une limite personnelle que vous avez du mal à maintenir.",
        "category": "relations",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "high",
        "instructions": [
            "Identifiez une situation récurrente où vos limites sont franchies",
            "Définissez clairement votre limite en une phrase",
            "Préparez la conséquence si cette limite n'est pas respectée",
            "Communiquez-la calmement à la personne concernée"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    {
        "action_id": "action_relations_047",
        "title": "Médiation intérieure",
        "description": "Jouez le rôle de médiateur entre deux parties en conflit (même intérieurement).",
        "category": "relations",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Pensez à un conflit entre deux personnes (ou deux parties de vous-même)",
            "Écrivez le point de vue de chaque partie en étant équitable",
            "Identifiez le besoin commun sous-jacent des deux parties",
            "Proposez une solution qui honore les deux besoins"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    {
        "action_id": "action_relations_048",
        "title": "Désamorcer l'humour",
        "description": "Utilisez l'humour bienveillant pour désamorcer une tension relationnelle.",
        "category": "relations",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "medium",
        "instructions": [
            "Pensez à une tension légère dans une relation",
            "Trouvez un angle humoristique qui ne blesse personne (autodérision recommandée)",
            "Préparez une phrase drôle qui pourrait détendre l'atmosphère",
            "L'humour doit rapprocher, jamais humilier — vérifiez que votre blague passe ce test"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    {
        "action_id": "action_relations_049",
        "title": "Bilan de conflit",
        "description": "Analysez un conflit passé pour en tirer des leçons relationnelles.",
        "category": "relations",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Choisissez un conflit résolu (ou non) des derniers mois",
            "Identifiez le déclencheur, l'escalade et la résolution (ou l'impasse)",
            "Notez ce que vous feriez différemment avec le recul",
            "Formulez une 'règle personnelle' pour éviter un scénario similaire"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    {
        "action_id": "action_relations_050",
        "title": "Paix intérieure",
        "description": "Lâchez prise sur un conflit qui ne se résoudra probablement jamais.",
        "category": "relations",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "low",
        "instructions": [
            "Identifiez un conflit ou une situation qui vous ronge sans issue possible",
            "Écrivez sur papier tout ce que vous ressentez, sans filtre",
            "Demandez-vous : 'Quel est le coût de porter cette charge chaque jour ?'",
            "Décidez consciemment de lâcher prise — non pas pardonner, mais vous libérer"
        ],
        "is_premium": True,
        "icon": "message-circle"
    },
    # =========================================================================
    # MENTAL HEALTH (50 actions) — icon: brain
    # =========================================================================
    # --- Stress management (10) ---
    {
        "action_id": "action_mental_health_001",
        "title": "Relâchement musculaire",
        "description": "Pratiquez la relaxation musculaire progressive pour dissoudre le stress accumulé.",
        "category": "mental_health",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "low",
        "instructions": [
            "Asseyez-vous confortablement et fermez les yeux",
            "Contractez fort les muscles du visage pendant 5 secondes, puis relâchez",
            "Descendez progressivement : cou, épaules, bras, ventre, jambes, pieds",
            "Terminez par 3 respirations profondes en savourant la détente"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    {
        "action_id": "action_mental_health_002",
        "title": "Vidange mentale",
        "description": "Déversez toutes vos inquiétudes sur papier pour libérer de l'espace mental.",
        "category": "mental_health",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "low",
        "instructions": [
            "Prenez une feuille et écrivez tout ce qui vous préoccupe, sans filtre",
            "Ne vous censurez pas, même les inquiétudes absurdes ou petites",
            "Relisez la liste et classez chaque élément : actionnable ou non",
            "Pour les actionnables, notez le plus petit pas possible. Pour les autres, lâchez prise"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    {
        "action_id": "action_mental_health_003",
        "title": "Ancrage 5-4-3-2-1",
        "description": "Utilisez vos 5 sens pour revenir au moment présent en cas de stress.",
        "category": "mental_health",
        "duration_min": 2,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Nommez 5 choses que vous voyez autour de vous",
            "Nommez 4 choses que vous pouvez toucher",
            "Nommez 3 sons que vous entendez, 2 odeurs que vous percevez",
            "Nommez 1 goût dans votre bouche — observez comment votre anxiété a diminué"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    {
        "action_id": "action_mental_health_004",
        "title": "Respiration carrée",
        "description": "Calmez votre système nerveux avec la technique de respiration en carré.",
        "category": "mental_health",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Inspirez par le nez pendant 4 secondes",
            "Retenez votre souffle pendant 4 secondes",
            "Expirez lentement par la bouche pendant 4 secondes",
            "Maintenez les poumons vides 4 secondes, puis répétez 6 fois"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    {
        "action_id": "action_mental_health_005",
        "title": "Scan corporel",
        "description": "Parcourez mentalement votre corps pour détecter et relâcher les tensions cachées.",
        "category": "mental_health",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "low",
        "instructions": [
            "Allongez-vous ou asseyez-vous confortablement, fermez les yeux",
            "Portez votre attention du sommet du crâne jusqu'aux pieds, lentement",
            "À chaque zone tendue, imaginez que votre souffle la traverse et la détend",
            "Notez les 2 zones les plus tendues — massez-les doucement après l'exercice"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    {
        "action_id": "action_mental_health_006",
        "title": "Pause nature",
        "description": "Accordez-vous 5 minutes de connexion avec la nature pour réinitialiser votre stress.",
        "category": "mental_health",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "low",
        "instructions": [
            "Sortez dehors ou regardez par une fenêtre avec de la verdure",
            "Observez un élément naturel en détail pendant 2 minutes (arbre, ciel, oiseau)",
            "Respirez profondément en imaginant absorber l'énergie de la nature",
            "Notez 3 détails que vous n'aviez jamais remarqués"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    {
        "action_id": "action_mental_health_007",
        "title": "Thermomètre de stress",
        "description": "Évaluez votre niveau de stress actuel et identifiez ses sources principales.",
        "category": "mental_health",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Notez votre niveau de stress de 1 à 10 en ce moment",
            "Listez les 3 principales sources de ce stress",
            "Pour chacune, évaluez : est-ce sous votre contrôle ou non ?",
            "Pour ce qui est contrôlable, identifiez une action immédiate pour réduire d'un point"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    {
        "action_id": "action_mental_health_008",
        "title": "Sas de décompression",
        "description": "Créez un rituel de transition entre travail et vie personnelle.",
        "category": "mental_health",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Choisissez un signal de fin de travail (fermer le laptop, changer de vêtements)",
            "Ajoutez une activité de 5 min qui marque la transition (marche, musique, étirement)",
            "Pendant cette activité, faites un 'brain dump' mental de ce qui reste au bureau",
            "Décidez consciemment d'être présent pour votre soirée"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    {
        "action_id": "action_mental_health_009",
        "title": "Pleine présence",
        "description": "Faites une activité quotidienne en pleine conscience pendant 5 minutes.",
        "category": "mental_health",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "low",
        "instructions": [
            "Choisissez une activité banale : boire un thé, marcher, se doucher",
            "Faites-la en portant toute votre attention sur chaque sensation",
            "Quand votre esprit vagabonde, ramenez-le doucement à l'activité",
            "Notez la différence de qualité quand vous êtes pleinement présent"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    {
        "action_id": "action_mental_health_010",
        "title": "Détox digitale",
        "description": "Offrez-vous une pause écran de 30 minutes pour régénérer votre attention.",
        "category": "mental_health",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Mettez tous vos appareils en mode avion ou dans une autre pièce",
            "Choisissez une activité sans écran : lire, dessiner, cuisiner, marcher",
            "Observez votre envie de vérifier votre téléphone — notez sa fréquence",
            "Après 30 min, évaluez comment vous vous sentez vs avant la pause"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    # --- Resilience building (10) ---
    {
        "action_id": "action_mental_health_011",
        "title": "Échec comme école",
        "description": "Transformez un échec récent en apprentissage concret et positif.",
        "category": "mental_health",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Choisissez un échec ou une déception récente",
            "Listez 3 choses que cette expérience vous a appris",
            "Identifiez une compétence que vous avez renforcée grâce à cet échec",
            "Reformulez l'expérience : 'Ce n'était pas un échec, c'était un…'"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    {
        "action_id": "action_mental_health_012",
        "title": "Mentalité de croissance",
        "description": "Remplacez une pensée fixe par une pensée de croissance.",
        "category": "mental_health",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "medium",
        "instructions": [
            "Identifiez une pensée 'fixe' récente : 'Je suis nul en…' ou 'Je ne peux pas…'",
            "Reformulez avec 'pas encore' : 'Je ne maîtrise pas encore…'",
            "Identifiez une étape concrète pour progresser dans ce domaine",
            "Rappelez-vous une compétence que vous maîtrisez aujourd'hui mais pas il y a 5 ans"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    {
        "action_id": "action_mental_health_013",
        "title": "Journal d'adversité",
        "description": "Documentez comment vous avez surmonté une difficulté pour renforcer votre confiance.",
        "category": "mental_health",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Choisissez un moment difficile de votre passé que vous avez surmonté",
            "Décrivez la situation, ce que vous avez ressenti et les actions que vous avez prises",
            "Identifiez les forces personnelles que vous avez mobilisées",
            "Écrivez : 'Si j'ai surmonté ça, je peux aussi gérer [défi actuel]'"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    {
        "action_id": "action_mental_health_014",
        "title": "Lettre de résilience",
        "description": "Écrivez à votre futur vous pour ancrer votre capacité à rebondir.",
        "category": "mental_health",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Écrivez une lettre à votre vous du futur qui traversera un moment dur",
            "Rappelez-lui ses forces, ses victoires passées et ses ressources",
            "Incluez un conseil pratique basé sur votre expérience",
            "Conservez cette lettre dans un endroit accessible pour les jours difficiles"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    {
        "action_id": "action_mental_health_015",
        "title": "Zone de confort +1",
        "description": "Identifiez et franchissez un micro-pas en dehors de votre zone de confort.",
        "category": "mental_health",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "high",
        "instructions": [
            "Identifiez quelque chose que vous évitez par peur ou inconfort",
            "Choisissez la version la plus petite et la plus sûre de cette action",
            "Faites-la aujourd'hui en acceptant l'inconfort temporaire",
            "Notez comment vous vous sentez après — la fierté dépasse-t-elle la peur ?"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    {
        "action_id": "action_mental_health_016",
        "title": "Recadrage positif",
        "description": "Transformez une situation négative en trouvant son bénéfice caché.",
        "category": "mental_health",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Choisissez une situation actuelle qui vous frustre ou vous déplaît",
            "Demandez-vous : 'Qu'est-ce que cette situation m'enseigne ?'",
            "Trouvez au moins un avantage inattendu ou une opportunité cachée",
            "Reformulez la situation en incluant cet avantage"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    {
        "action_id": "action_mental_health_017",
        "title": "Routine anti-fragile",
        "description": "Créez un plan B pour vos routines essentielles en cas de journée chaotique.",
        "category": "mental_health",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Listez vos 3 routines les plus importantes (sport, méditation, travail profond)",
            "Pour chacune, créez une version minimale faisable en 5 minutes",
            "Décidez du déclencheur : 'Si ma routine est perturbée, je fais la version mini'",
            "Testez une version mini aujourd'hui pour ancrer l'habitude"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    {
        "action_id": "action_mental_health_018",
        "title": "Inventaire de force",
        "description": "Recensez vos ressources intérieures pour faire face aux défis.",
        "category": "mental_health",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Listez 5 qualités personnelles qui vous aident dans les moments durs",
            "Pour chacune, trouvez un exemple concret où elle vous a servi",
            "Identifiez aussi 3 personnes-ressources dans votre entourage",
            "Gardez cette liste comme 'kit de survie émotionnelle' accessible"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    {
        "action_id": "action_mental_health_019",
        "title": "Acceptation radicale",
        "description": "Pratiquez l'acceptation d'une réalité que vous ne pouvez pas changer.",
        "category": "mental_health",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Identifiez une situation que vous ne pouvez pas contrôler et qui vous pèse",
            "Répétez doucement : 'C'est ainsi, et je choisis de ne plus lutter contre cette réalité'",
            "Distinguez acceptation (reconnaître) et résignation (abandonner)",
            "Redirigez votre énergie vers ce que vous POUVEZ influencer dans cette situation"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    {
        "action_id": "action_mental_health_020",
        "title": "Gratitude de crise",
        "description": "Trouvez de la gratitude même dans une période difficile pour renforcer votre résilience.",
        "category": "mental_health",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Pensez à votre plus grand défi actuel",
            "Trouvez 3 éléments positifs dans cette situation (même minimes)",
            "Notez une personne ou ressource qui vous aide à traverser cette période",
            "Exprimez votre gratitude à cette personne ou pour cette ressource"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    # --- Self-esteem (10) ---
    {
        "action_id": "action_mental_health_021",
        "title": "Affirmation puissante",
        "description": "Créez et intériorisez une affirmation positive personnalisée.",
        "category": "mental_health",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Identifiez un doute récurrent sur vous-même",
            "Formulez son opposé positif au présent : 'Je suis [qualité]'",
            "Rendez-la spécifique et crédible (pas 'Je suis parfait' mais 'Je progresse chaque jour')",
            "Répétez-la 10 fois à voix haute devant un miroir en vous regardant dans les yeux"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    {
        "action_id": "action_mental_health_022",
        "title": "Inventaire de forces",
        "description": "Identifiez vos 5 forces de caractère principales et comment les utiliser davantage.",
        "category": "mental_health",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Listez 5 qualités que vos proches vous reconnaissent",
            "Pour chacune, notez un moment récent où vous l'avez utilisée",
            "Identifiez celle que vous sous-exploitez le plus",
            "Planifiez une situation cette semaine où vous pourriez l'exercer davantage"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    {
        "action_id": "action_mental_health_023",
        "title": "Mur de fierté",
        "description": "Rappelez-vous 5 accomplissements dont vous êtes fier pour booster votre confiance.",
        "category": "mental_health",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Listez 5 réalisations dont vous êtes fier (toutes tailles confondues)",
            "Pour chacune, notez la difficulté que vous avez surmontée",
            "Identifiez le point commun : quelle force revient à chaque fois ?",
            "Gardez cette liste sur votre téléphone pour les jours de doute"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    {
        "action_id": "action_mental_health_024",
        "title": "Dialogue intérieur",
        "description": "Transformez votre voix intérieure critique en coach bienveillant.",
        "category": "mental_health",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Notez la dernière pensée autocritique que vous avez eue",
            "Imaginez qu'un ami vous dit cette même chose — que lui répondriez-vous ?",
            "Réécrivez cette pensée avec la bienveillance que vous accorderiez à cet ami",
            "La prochaine fois que cette voix critique surgit, utilisez cette nouvelle version"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    {
        "action_id": "action_mental_health_025",
        "title": "Victoires du jour",
        "description": "Notez 3 petites victoires de votre journée, même minuscules.",
        "category": "mental_health",
        "duration_min": 2,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "En fin de journée, notez 3 choses que vous avez bien faites aujourd'hui",
            "Incluez même les plus petites (s'être levé à l'heure, avoir dit merci, avoir tenu un engagement)",
            "Pour chacune, savourez le sentiment de compétence pendant 10 secondes",
            "Faites cet exercice chaque soir pendant 7 jours et observez l'effet cumulé"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    {
        "action_id": "action_mental_health_026",
        "title": "Comparaison saine",
        "description": "Remplacez la comparaison toxique aux autres par une comparaison à votre ancien vous.",
        "category": "mental_health",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Identifiez un domaine où vous vous comparez souvent aux autres",
            "Comparez-vous plutôt à votre version d'il y a 1 an dans ce domaine",
            "Listez 3 progrès concrets que vous avez réalisés depuis",
            "Remplacez 'Il/Elle est meilleur(e)' par 'Je progresse à mon rythme'"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    {
        "action_id": "action_mental_health_027",
        "title": "Qualité unique",
        "description": "Identifiez ce qui vous rend unique et apprenez à le valoriser.",
        "category": "mental_health",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Demandez à 3 proches : 'Qu'est-ce qui me rend unique selon toi ?'",
            "Notez les réponses et cherchez les thèmes communs",
            "Identifiez comment cette unicité est un atout dans votre vie",
            "Écrivez une phrase qui résume votre 'superpouvoir' personnel"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    {
        "action_id": "action_mental_health_028",
        "title": "Détox critique",
        "description": "Identifiez et désarmez votre critique intérieur pendant une journée.",
        "category": "mental_health",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "medium",
        "instructions": [
            "Aujourd'hui, comptez chaque pensée autocritique que vous avez",
            "Pour chacune, notez-la brièvement et ajoutez 'Intéressant, merci pour ton avis'",
            "En fin de journée, comptez le total — vous serez probablement surpris",
            "Choisissez 3 pensées critiques à remplacer par des alternatives factuelles"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    {
        "action_id": "action_mental_health_029",
        "title": "Corps allié",
        "description": "Renforcez votre estime corporelle en appréciant ce que votre corps fait pour vous.",
        "category": "mental_health",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Listez 5 choses incroyables que votre corps fait chaque jour automatiquement",
            "Remerciez votre corps pour une capacité spécifique (marcher, voir, sentir)",
            "Faites un geste de soin envers votre corps aujourd'hui (étirement, hydratation, repos)",
            "Remplacez un jugement physique par une appréciation fonctionnelle"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    {
        "action_id": "action_mental_health_030",
        "title": "Mantra personnel",
        "description": "Créez un mantra court et puissant pour les moments de doute.",
        "category": "mental_health",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Pensez à votre plus grande insécurité actuelle",
            "Créez une phrase courte (5-8 mots) qui la contrebalance",
            "Elle doit être vraie, pas idéaliste (ex: 'Je fais de mon mieux et c'est suffisant')",
            "Écrivez-la en fond d'écran ou sur un post-it, et répétez-la 3 fois par jour"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    # --- Anxiety management (10) ---
    {
        "action_id": "action_mental_health_031",
        "title": "Restructuration cognitive",
        "description": "Identifiez et corrigez une distorsion de pensée qui alimente votre anxiété.",
        "category": "mental_health",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Notez une pensée anxieuse récurrente (ex: 'Tout va mal se passer')",
            "Identifiez la distorsion : catastrophisation, généralisation, lecture de pensée ?",
            "Cherchez des preuves POUR et CONTRE cette pensée",
            "Reformulez de manière plus équilibrée et réaliste"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    {
        "action_id": "action_mental_health_032",
        "title": "Micro-exposition",
        "description": "Affrontez une petite peur en faisant un pas minuscule vers elle.",
        "category": "mental_health",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "high",
        "instructions": [
            "Choisissez une situation qui vous génère de l'anxiété (appeler, parler en public, etc.)",
            "Identifiez la version la plus légère de cette situation",
            "Faites-la aujourd'hui en acceptant l'inconfort sans fuir",
            "Notez votre niveau d'anxiété avant (1-10) et après — il a probablement baissé"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    {
        "action_id": "action_mental_health_033",
        "title": "Lieu sûr intérieur",
        "description": "Créez un espace mental de sécurité que vous pouvez visiter à tout moment.",
        "category": "mental_health",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "high",
        "instructions": [
            "Fermez les yeux et imaginez un lieu où vous vous sentez parfaitement en sécurité",
            "Ajoutez des détails sensoriels : couleurs, sons, odeurs, textures, température",
            "Restez dans cet espace 3 minutes en respirant calmement",
            "Associez ce lieu à un geste discret (toucher le poignet) pour y accéder rapidement"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    {
        "action_id": "action_mental_health_034",
        "title": "Pire scénario",
        "description": "Dédramatisez une inquiétude en analysant rationnellement le pire scénario possible.",
        "category": "mental_health",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Écrivez votre inquiétude principale du moment",
            "Imaginez le pire scénario réaliste (pas fantasmé)",
            "Demandez-vous : pourriez-vous survivre et vous adapter ? (Probablement oui)",
            "Planifiez votre réaction si ce scénario arrivait — avoir un plan réduit l'anxiété"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    {
        "action_id": "action_mental_health_035",
        "title": "Défusion cognitive",
        "description": "Apprenez à observer vos pensées anxieuses sans vous identifier à elles.",
        "category": "mental_health",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Notez une pensée anxieuse en commençant par 'J'ai la pensée que…'",
            "Au lieu de 'Je suis nul', dites 'J'ai la pensée que je suis nul'",
            "Imaginez cette pensée comme un nuage qui passe dans le ciel de votre esprit",
            "Observez : vous êtes le ciel, pas le nuage. La pensée n'est pas la réalité"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    {
        "action_id": "action_mental_health_036",
        "title": "Heure d'inquiétude",
        "description": "Programmez un créneau dédié aux inquiétudes pour ne pas les laisser envahir votre journée.",
        "category": "mental_health",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "high",
        "instructions": [
            "Choisissez un créneau de 15 minutes dédié aux inquiétudes (pas le soir)",
            "Quand une inquiétude surgit en dehors de ce créneau, notez-la et reportez-la",
            "Pendant le créneau, inquiétez-vous autant que vous voulez — sans culpabilité",
            "Souvent, les inquiétudes ont perdu leur intensité quand le créneau arrive"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    {
        "action_id": "action_mental_health_037",
        "title": "Ancrage physique",
        "description": "Utilisez votre corps pour calmer une montée d'anxiété en moins de 2 minutes.",
        "category": "mental_health",
        "duration_min": 2,
        "duration_max": 5,
        "energy_level": "high",
        "instructions": [
            "Plongez vos mains dans l'eau froide pendant 30 secondes",
            "Ou tenez un glaçon dans votre main et concentrez-vous sur la sensation",
            "La stimulation physique intense interrompt le circuit de l'anxiété",
            "Après, respirez lentement 5 fois en expirant plus long que l'inspiration"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    {
        "action_id": "action_mental_health_038",
        "title": "Journal d'anxiété",
        "description": "Tracez vos épisodes d'anxiété pour identifier des patterns et déclencheurs.",
        "category": "mental_health",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Créez un tableau : date, heure, situation, niveau d'anxiété (1-10), pensée",
            "Remplissez-le pour votre dernier épisode d'anxiété",
            "Si vous en avez plusieurs entrées, cherchez des patterns (heure, lieu, personne)",
            "Identifiez un déclencheur commun et préparez une stratégie préventive"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    {
        "action_id": "action_mental_health_039",
        "title": "Auto-compassion",
        "description": "Traitez-vous avec la même compassion que vous accorderiez à un ami anxieux.",
        "category": "mental_health",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Posez une main sur votre cœur et une sur votre ventre",
            "Dites-vous : 'C'est un moment difficile. La souffrance fait partie de la vie'",
            "Ajoutez : 'Que puis-je faire pour prendre soin de moi en ce moment ?'",
            "Faites cette chose de soin immédiatement, même petite"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    {
        "action_id": "action_mental_health_040",
        "title": "Probabilités réelles",
        "description": "Évaluez la probabilité réelle de vos peurs pour remettre l'anxiété en perspective.",
        "category": "mental_health",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "high",
        "instructions": [
            "Écrivez votre peur principale en ce moment",
            "Estimez sa probabilité de survenir (0-100%)",
            "Combien de fois cette peur s'est-elle réalisée par le passé ?",
            "Calculez votre 'taux de prédiction' — l'anxiété surestime presque toujours le danger"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    # --- Emotional regulation (10) ---
    {
        "action_id": "action_mental_health_041",
        "title": "Météo intérieure",
        "description": "Identifiez et nommez votre état émotionnel avec précision pour mieux le gérer.",
        "category": "mental_health",
        "duration_min": 2,
        "duration_max": 5,
        "energy_level": "low",
        "instructions": [
            "Fermez les yeux et scannez votre état intérieur",
            "Nommez votre émotion avec précision (pas 'mal' mais 'frustré', 'déçu', 'inquiet')",
            "Évaluez son intensité de 1 à 10",
            "Notez où vous la ressentez physiquement dans votre corps"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    {
        "action_id": "action_mental_health_042",
        "title": "Carte des déclencheurs",
        "description": "Identifiez les situations qui déclenchent vos réactions émotionnelles les plus fortes.",
        "category": "mental_health",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Listez vos 5 réactions émotionnelles les plus intenses du mois",
            "Pour chacune, identifiez le déclencheur exact (personne, situation, pensée)",
            "Cherchez le pattern : y a-t-il un thème commun (rejet, contrôle, injustice) ?",
            "Préparez un plan de réponse pour la prochaine fois que ce déclencheur apparaît"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    {
        "action_id": "action_mental_health_043",
        "title": "Boîte à outils émotions",
        "description": "Créez votre kit de stratégies de coping personnalisé pour chaque émotion difficile.",
        "category": "mental_health",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "high",
        "instructions": [
            "Listez 3 émotions que vous trouvez les plus difficiles à gérer",
            "Pour chacune, identifiez 3 stratégies qui fonctionnent pour vous",
            "Classez-les : rapide (2 min), moyenne (10 min), profonde (30+ min)",
            "Créez une note 'SOS émotions' sur votre téléphone avec ce plan"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    {
        "action_id": "action_mental_health_044",
        "title": "Pause entre stimulus",
        "description": "Entraînez-vous à créer un espace entre un événement déclencheur et votre réaction.",
        "category": "mental_health",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "high",
        "instructions": [
            "Rappelez-vous une situation récente où vous avez réagi impulsivement",
            "Imaginez que vous insérez un espace de 10 secondes entre l'événement et votre réaction",
            "Pendant ces 10 secondes : respirez, nommez l'émotion, choisissez consciemment",
            "Pratiquez la technique STOP : Stop, Take a breath, Observe, Proceed"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    {
        "action_id": "action_mental_health_045",
        "title": "Roue des émotions",
        "description": "Enrichissez votre vocabulaire émotionnel pour une meilleure autorégulation.",
        "category": "mental_health",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Recherchez la 'roue des émotions' de Plutchik en ligne",
            "Identifiez votre émotion actuelle au niveau le plus précis possible",
            "Comparez avec l'émotion que vous avez ressentie hier à la même heure",
            "Plus votre vocabulaire émotionnel est riche, mieux vous gérez vos émotions"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    {
        "action_id": "action_mental_health_046",
        "title": "Émotion messagère",
        "description": "Décodez le message que votre émotion essaie de vous transmettre.",
        "category": "mental_health",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "medium",
        "instructions": [
            "Identifiez l'émotion dominante en ce moment",
            "Demandez-vous : si cette émotion pouvait parler, que dirait-elle ?",
            "La colère signale souvent une limite franchie, la tristesse une perte, la peur un danger",
            "Répondez au besoin sous-jacent plutôt que de combattre l'émotion"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    {
        "action_id": "action_mental_health_047",
        "title": "Régulation par le corps",
        "description": "Utilisez le mouvement pour transformer une émotion stagnante.",
        "category": "mental_health",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "high",
        "instructions": [
            "Identifiez l'émotion que vous ressentez et son intensité",
            "Choisissez un mouvement correspondant : marche rapide pour la frustration, danse pour la tristesse",
            "Bougez pendant 5 minutes en laissant l'émotion s'exprimer par le corps",
            "Réévaluez l'intensité de l'émotion après — elle a probablement diminué"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    {
        "action_id": "action_mental_health_048",
        "title": "Courbe émotionnelle",
        "description": "Tracez votre courbe émotionnelle de la journée pour repérer les patterns.",
        "category": "mental_health",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Tracez un axe temporel de votre journée (matin, midi, après-midi, soir)",
            "Pour chaque période, notez votre humeur de -5 à +5",
            "Reliez les points pour voir la courbe",
            "Identifiez les moments de creux et de pic — qu'est-ce qui les cause ?"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    {
        "action_id": "action_mental_health_049",
        "title": "Soupape créative",
        "description": "Canalisez une émotion intense dans une expression créative libre.",
        "category": "mental_health",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "high",
        "instructions": [
            "Prenez du papier et des couleurs (ou un instrument, ou votre voix)",
            "Sans réfléchir, exprimez votre émotion actuelle : dessinez, chantez, écrivez",
            "Ne jugez pas le résultat — l'objectif est l'expression, pas la performance",
            "Observez comment l'intensité émotionnelle change après cette catharsis"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    {
        "action_id": "action_mental_health_050",
        "title": "Check-in du soir",
        "description": "Faites un bilan émotionnel de votre journée pour mieux dormir.",
        "category": "mental_health",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Notez les 3 émotions principales que vous avez ressenties aujourd'hui",
            "Pour chacune, identifiez ce qui l'a déclenchée et comment vous l'avez gérée",
            "Évaluez globalement votre journée émotionnelle de 1 à 10",
            "Écrivez une intention pour demain : 'Demain, je choisis de cultiver [émotion positive]'"
        ],
        "is_premium": True,
        "icon": "brain"
    },
    # =========================================================================
    # ENTREPRENEURSHIP (50 actions) — icon: rocket
    # =========================================================================
    # --- Ideation & validation (10) ---
    {
        "action_id": "action_entrepreneurship_001",
        "title": "Chasseur de problèmes",
        "description": "Repérez 3 problèmes concrets autour de vous qui pourraient devenir des opportunités business.",
        "category": "entrepreneurship",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Observez votre journée et notez 3 frustrations ou inefficacités",
            "Pour chacune, estimez combien de personnes partagent ce problème",
            "Classez-les par intensité de la douleur (gêne légère vs vrai blocage)",
            "Le meilleur problème à résoudre est fréquent, intense et mal servi"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    {
        "action_id": "action_entrepreneurship_002",
        "title": "Brainstorm solutions",
        "description": "Générez 10 solutions pour un problème identifié, sans filtre ni autocensure.",
        "category": "entrepreneurship",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "high",
        "instructions": [
            "Choisissez un problème que vous avez identifié",
            "Réglez un timer de 5 minutes et écrivez 10 solutions, même absurdes",
            "Ne jugez aucune idée pendant le brainstorm — la quantité prime",
            "Relisez et marquez les 3 plus réalistes et les 3 plus originales"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    {
        "action_id": "action_entrepreneurship_003",
        "title": "Interview utilisateur",
        "description": "Préparez un guide d'entretien pour valider un problème avec de vrais utilisateurs.",
        "category": "entrepreneurship",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "high",
        "instructions": [
            "Formulez votre hypothèse principale : 'Je crois que [persona] a le problème de [X]'",
            "Préparez 5 questions ouvertes qui ne biaisent pas les réponses",
            "Incluez : 'Racontez-moi la dernière fois que…' et 'Comment gérez-vous actuellement…'",
            "Identifiez 3 personnes cibles que vous pourriez interviewer cette semaine"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    {
        "action_id": "action_entrepreneurship_004",
        "title": "Test de la mère",
        "description": "Apprenez à valider une idée sans biais grâce à la technique du Mom Test.",
        "category": "entrepreneurship",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Règle 1 : ne parlez jamais de votre idée, parlez du problème de l'autre",
            "Règle 2 : posez des questions sur le passé, pas sur le futur hypothétique",
            "Règle 3 : cherchez des preuves d'engagement (temps, argent déjà dépensé)",
            "Préparez 3 questions 'Mom Test' pour votre idée actuelle"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    {
        "action_id": "action_entrepreneurship_005",
        "title": "Smoke test",
        "description": "Validez l'intérêt pour votre idée avant de construire quoi que ce soit.",
        "category": "entrepreneurship",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "high",
        "instructions": [
            "Créez une landing page fictive pour votre produit en 30 minutes (Carrd, Notion)",
            "Décrivez le problème, la solution et un bouton 'Je suis intéressé'",
            "Partagez le lien avec 20 personnes de votre cible",
            "Mesurez le taux de clic — au-dessus de 10%, l'idée mérite d'être creusée"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    {
        "action_id": "action_entrepreneurship_006",
        "title": "Observation terrain",
        "description": "Allez observer votre utilisateur cible dans son environnement naturel.",
        "category": "entrepreneurship",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "low",
        "instructions": [
            "Identifiez un lieu où se trouvent vos utilisateurs cibles",
            "Passez 15-30 minutes à observer silencieusement leur comportement",
            "Notez les frustrations, les solutions de contournement, les moments de friction",
            "Identifiez un insight que vous n'auriez pas trouvé par la réflexion seule"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    {
        "action_id": "action_entrepreneurship_007",
        "title": "Copier-améliorer",
        "description": "Analysez une solution existante et identifiez comment la rendre 10x meilleure.",
        "category": "entrepreneurship",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "low",
        "instructions": [
            "Choisissez un produit existant dans votre domaine d'intérêt",
            "Lisez les avis négatifs (1-2 étoiles) pour identifier les frustrations",
            "Listez 5 améliorations que vous pourriez apporter",
            "Identifiez la plus impactante et la plus faisable"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    {
        "action_id": "action_entrepreneurship_008",
        "title": "Tendance radar",
        "description": "Repérez une tendance émergente qui pourrait créer de nouvelles opportunités.",
        "category": "entrepreneurship",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "low",
        "instructions": [
            "Consultez Product Hunt, Hacker News ou Google Trends",
            "Identifiez 3 tendances dans votre domaine d'intérêt",
            "Pour chacune, demandez-vous : quel nouveau problème cette tendance crée ?",
            "Notez une idée de produit ou service qui surfe sur cette tendance"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    {
        "action_id": "action_entrepreneurship_009",
        "title": "Niche finder",
        "description": "Identifiez une niche de marché sous-exploitée grâce à la méthode de l'intersection.",
        "category": "entrepreneurship",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Listez 3 de vos passions ou expertises",
            "Listez 3 marchés en croissance",
            "Cherchez les intersections entre vos compétences et ces marchés",
            "L'intersection la plus niche et spécifique est souvent la meilleure opportunité"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    {
        "action_id": "action_entrepreneurship_010",
        "title": "Pré-vente test",
        "description": "Testez la volonté de payer avant de construire en proposant une pré-vente.",
        "category": "entrepreneurship",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "high",
        "instructions": [
            "Décrivez votre offre en 3 phrases : problème, solution, prix",
            "Contactez 5 personnes de votre cible avec cette proposition",
            "Proposez une remise early bird en échange d'un paiement anticipé",
            "Si personne ne paie, pivotez. Si 2+ paient, vous tenez quelque chose"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    # --- Business model (10) ---
    {
        "action_id": "action_entrepreneurship_011",
        "title": "Canvas proposition",
        "description": "Clarifiez votre proposition de valeur avec le Value Proposition Canvas.",
        "category": "entrepreneurship",
        "duration_min": 5,
        "duration_max": 12,
        "energy_level": "high",
        "instructions": [
            "Divisez une feuille en 2 : à droite le client, à gauche votre offre",
            "Client : listez ses jobs-to-do, ses douleurs et ses gains souhaités",
            "Offre : listez vos produits/services, vos antidouleurs et vos créateurs de gains",
            "Vérifiez l'alignement : chaque douleur a-t-elle un antidouleur correspondant ?"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    {
        "action_id": "action_entrepreneurship_012",
        "title": "Modèle de revenus",
        "description": "Explorez différents modèles de monétisation pour votre idée.",
        "category": "entrepreneurship",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Listez 5 modèles possibles : abonnement, freemium, commission, licence, pub",
            "Pour chaque modèle, estimez le prix et le nombre de clients nécessaires",
            "Calculez le chiffre d'affaires potentiel annuel pour chaque modèle",
            "Sélectionnez celui qui maximise la valeur pour le client ET pour vous"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    {
        "action_id": "action_entrepreneurship_013",
        "title": "Mapping concurrence",
        "description": "Cartographiez vos concurrents pour trouver votre positionnement unique.",
        "category": "entrepreneurship",
        "duration_min": 5,
        "duration_max": 12,
        "energy_level": "high",
        "instructions": [
            "Listez 5-10 concurrents directs et indirects",
            "Créez une matrice 2x2 avec 2 critères clés (ex: prix/qualité, simple/complexe)",
            "Placez chaque concurrent sur la matrice",
            "Identifiez le quadrant vide ou sous-occupé — c'est votre opportunité"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    {
        "action_id": "action_entrepreneurship_014",
        "title": "Lean Canvas",
        "description": "Résumez votre business model en 1 page avec le Lean Canvas.",
        "category": "entrepreneurship",
        "duration_min": 8,
        "duration_max": 15,
        "energy_level": "high",
        "instructions": [
            "Complétez les 9 cases : problème, solution, métriques clés, avantage unique",
            "Ajoutez : segments clients, canaux, structure de coûts, flux de revenus",
            "Soyez brutal : si une case est floue, c'est un point faible à travailler",
            "Partagez avec un ami entrepreneur et demandez son avis honnête"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    {
        "action_id": "action_entrepreneurship_015",
        "title": "Unit economics",
        "description": "Calculez la rentabilité unitaire de votre offre pour valider sa viabilité.",
        "category": "entrepreneurship",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Estimez votre coût d'acquisition client (CAC) : marketing / nombre de clients",
            "Estimez la valeur vie client (LTV) : revenu par client × durée moyenne",
            "Calculez le ratio LTV/CAC — il doit être supérieur à 3",
            "Si le ratio est trop bas, cherchez comment réduire le CAC ou augmenter la LTV"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    {
        "action_id": "action_entrepreneurship_016",
        "title": "Pricing power",
        "description": "Testez votre capacité à fixer un prix premium pour votre offre.",
        "category": "entrepreneurship",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Listez les 5 éléments de valeur perçue de votre offre",
            "Identifiez ceux que vos concurrents n'offrent pas",
            "Testez mentalement : si vous doubliez votre prix, garderiez-vous vos clients ?",
            "Identifiez ce que vous devriez ajouter pour justifier un prix 50% plus élevé"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    {
        "action_id": "action_entrepreneurship_017",
        "title": "Moat builder",
        "description": "Identifiez votre avantage compétitif durable — votre 'moat'.",
        "category": "entrepreneurship",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "low",
        "instructions": [
            "Passez en revue les 7 types de moats : réseau, données, marque, coûts, switching, tech, réglementation",
            "Identifiez lequel est le plus applicable à votre projet",
            "Évaluez sa solidité actuelle de 1 à 10",
            "Planifiez 2 actions pour renforcer votre moat dans les 3 prochains mois"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    {
        "action_id": "action_entrepreneurship_018",
        "title": "Pivot rapide",
        "description": "Si votre idée ne fonctionne pas, identifiez 3 pivots possibles.",
        "category": "entrepreneurship",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "high",
        "instructions": [
            "Listez les signaux que votre idée actuelle ne fonctionne pas",
            "Pivot de client : même solution, différent segment",
            "Pivot de problème : même client, différent problème",
            "Pivot de solution : même problème, différente approche. Choisissez le plus prometteur"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    {
        "action_id": "action_entrepreneurship_019",
        "title": "Partenariat stratégique",
        "description": "Identifiez un partenaire potentiel qui pourrait accélérer votre croissance.",
        "category": "entrepreneurship",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Listez les acteurs qui touchent vos clients avant ou après vous",
            "Identifiez ceux dont l'offre est complémentaire (pas concurrente)",
            "Imaginez une collaboration win-win pour les deux parties",
            "Rédigez un pitch de partenariat en 5 lignes et identifiez le bon interlocuteur"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    {
        "action_id": "action_entrepreneurship_020",
        "title": "Scalabilité test",
        "description": "Évaluez si votre modèle peut passer à l'échelle sans exploser en complexité.",
        "category": "entrepreneurship",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Imaginez 10x plus de clients demain — que se casserait en premier ?",
            "Identifiez les tâches qui nécessitent votre temps personnel (non délégable)",
            "Listez les processus automatisables vs ceux qui nécessitent de l'humain",
            "Notez votre bottleneck principal et une piste pour le résoudre"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    # --- Pitch & communication (10) ---
    {
        "action_id": "action_entrepreneurship_021",
        "title": "Elevator pitch",
        "description": "Résumez votre projet en 60 secondes de manière convaincante.",
        "category": "entrepreneurship",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "high",
        "instructions": [
            "Structure : Problème (10s), Solution (15s), Marché (10s), Traction (10s), Ask (15s)",
            "Chaque partie doit être claire sans jargon technique",
            "Enregistrez-vous et chronométrez — maximum 60 secondes",
            "Faites écouter à quelqu'un hors de votre domaine et demandez s'il a compris"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    {
        "action_id": "action_entrepreneurship_022",
        "title": "Storytelling fondateur",
        "description": "Créez votre histoire de fondateur pour donner de l'âme à votre projet.",
        "category": "entrepreneurship",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Répondez : quel moment déclic vous a poussé à créer ce projet ?",
            "Décrivez le problème que vous avez vécu personnellement",
            "Racontez votre premier pas et l'obstacle que vous avez surmonté",
            "Terminez par votre vision : à quoi ressemble le monde si vous réussissez ?"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    {
        "action_id": "action_entrepreneurship_023",
        "title": "FAQ investisseur",
        "description": "Préparez vos réponses aux 5 questions les plus fréquentes des investisseurs.",
        "category": "entrepreneurship",
        "duration_min": 5,
        "duration_max": 12,
        "energy_level": "high",
        "instructions": [
            "Préparez : Quelle est la taille du marché ? Pourquoi maintenant ?",
            "Ajoutez : Quel est votre avantage unfair ? Comment vous monétisez ?",
            "Terminez par : Quelle est votre traction actuelle ?",
            "Pour chaque réponse, commencez par le chiffre ou le fait le plus fort"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    {
        "action_id": "action_entrepreneurship_024",
        "title": "Pitch deck express",
        "description": "Structurez les 10 slides essentielles de votre pitch deck.",
        "category": "entrepreneurship",
        "duration_min": 8,
        "duration_max": 15,
        "energy_level": "low",
        "instructions": [
            "Slide 1-3 : Problème, Solution, Produit (avec démo ou screenshot)",
            "Slide 4-6 : Marché (TAM/SAM/SOM), Business model, Traction",
            "Slide 7-9 : Concurrence, Équipe, Roadmap",
            "Slide 10 : Ask (montant, utilisation des fonds, prochaines étapes)"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    {
        "action_id": "action_entrepreneurship_025",
        "title": "One-liner viral",
        "description": "Créez une phrase d'accroche qui résume votre projet et donne envie d'en savoir plus.",
        "category": "entrepreneurship",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Testez la formule : '[Produit] est le [Analogie connue] pour [Marché cible]'",
            "Ex: 'Uber pour les dog-sitters' ou 'Duolingo pour la finance'",
            "Créez 5 variantes et testez-les sur 3 personnes",
            "Gardez celle qui génère le plus de 'Ah, intéressant, dis-m'en plus'"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    {
        "action_id": "action_entrepreneurship_026",
        "title": "Objection killer",
        "description": "Anticipez et préparez des réponses aux objections courantes sur votre projet.",
        "category": "entrepreneurship",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Listez les 5 objections les plus fréquentes que vous entendez",
            "Pour chacune, préparez une réponse en 2-3 phrases maximum",
            "Incluez un fait, un chiffre ou un témoignage pour appuyer chaque réponse",
            "Entraînez-vous à les délivrer avec calme et conviction"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    {
        "action_id": "action_entrepreneurship_027",
        "title": "Démo percutante",
        "description": "Préparez une démonstration de votre produit qui impressionne en 3 minutes.",
        "category": "entrepreneurship",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "high",
        "instructions": [
            "Identifiez le moment 'wow' de votre produit — celui qui fait la différence",
            "Construisez votre démo autour de ce moment : contexte rapide → problème → magie",
            "Préparez un scénario réaliste avec de vraies données (pas 'John Doe')",
            "Testez la démo 3 fois pour vous assurer qu'elle fonctionne sans accroc"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    {
        "action_id": "action_entrepreneurship_028",
        "title": "Pitch en 1 tweet",
        "description": "Résumez votre projet en 280 caractères maximum pour affûter votre message.",
        "category": "entrepreneurship",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Écrivez votre pitch en un tweet : problème + solution + bénéfice",
            "Comptez les caractères — maximum 280",
            "Chaque mot doit être indispensable, supprimez le superflu",
            "Testez : si un inconnu lit ce tweet, comprend-il et est-il intéressé ?"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    {
        "action_id": "action_entrepreneurship_029",
        "title": "Témoignage client",
        "description": "Collectez un témoignage client percutant pour renforcer votre crédibilité.",
        "category": "entrepreneurship",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Identifiez votre client le plus satisfait",
            "Demandez-lui 3 questions : Quel problème aviez-vous ? Comment notre solution l'a résolu ? Quel résultat concret ?",
            "Reformulez ses réponses en un témoignage concis avec un chiffre clé",
            "Demandez la permission de l'utiliser publiquement"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    {
        "action_id": "action_entrepreneurship_030",
        "title": "Confiance scénique",
        "description": "Développez votre présence et votre aisance pour pitcher devant un public.",
        "category": "entrepreneurship",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "high",
        "instructions": [
            "Enregistrez-vous en vidéo pendant que vous pitchez (même seul)",
            "Regardez la vidéo et notez : posture, regard, rythme, tics de langage",
            "Identifiez un point à améliorer et répétez 3 fois en vous concentrant dessus",
            "Power pose 2 minutes avant chaque pitch : mains sur les hanches, tête haute"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    # --- Growth & marketing (10) ---
    {
        "action_id": "action_entrepreneurship_031",
        "title": "Idée de contenu",
        "description": "Générez 10 idées de contenu qui attireront votre audience cible.",
        "category": "entrepreneurship",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Listez les 5 questions que vos clients posent le plus souvent",
            "Pour chaque question, créez 2 formats de contenu (post, vidéo, article, infographie)",
            "Priorisez par facilité de production et impact potentiel",
            "Planifiez la création du premier contenu cette semaine"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    {
        "action_id": "action_entrepreneurship_032",
        "title": "Persona précis",
        "description": "Créez un portrait détaillé de votre client idéal pour mieux cibler vos efforts.",
        "category": "entrepreneurship",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Donnez un prénom à votre client idéal et décrivez sa journée type",
            "Identifiez ses 3 plus grandes frustrations liées à votre domaine",
            "Notez où il/elle passe du temps en ligne (réseaux, forums, médias)",
            "Résumez en une phrase : '[Prénom] veut [objectif] mais [obstacle]'"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    {
        "action_id": "action_entrepreneurship_033",
        "title": "Conversion audit",
        "description": "Analysez votre funnel de conversion et identifiez le plus gros point de fuite.",
        "category": "entrepreneurship",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "high",
        "instructions": [
            "Dessinez votre funnel : Découverte → Intérêt → Considération → Achat → Rétention",
            "Estimez le taux de conversion à chaque étape",
            "Identifiez l'étape avec la plus grosse perte de prospects",
            "Brainstormez 3 actions pour améliorer cette étape spécifique"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    {
        "action_id": "action_entrepreneurship_034",
        "title": "Growth hack",
        "description": "Identifiez un levier de croissance rapide et peu coûteux pour votre projet.",
        "category": "entrepreneurship",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "high",
        "instructions": [
            "Listez vos 3 canaux d'acquisition actuels et leur coût",
            "Identifiez un canal inexploité : partenariats, communautés, referral",
            "Concevez un test à lancer cette semaine avec un budget de 0€",
            "Définissez la métrique de succès et la date d'évaluation"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    {
        "action_id": "action_entrepreneurship_035",
        "title": "Email qui convertit",
        "description": "Rédigez un email de prospection qui obtient des réponses.",
        "category": "entrepreneurship",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Objet : 6 mots max, personnalisé, qui pique la curiosité",
            "Ligne 1 : montrez que vous connaissez le destinataire (recherche préalable)",
            "Corps : un insight ou une valeur, pas un pitch produit",
            "CTA : une question simple qui demande un oui/non, pas un engagement"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    {
        "action_id": "action_entrepreneurship_036",
        "title": "Social proof",
        "description": "Créez 3 éléments de preuve sociale pour rassurer vos prospects.",
        "category": "entrepreneurship",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "low",
        "instructions": [
            "Collectez un chiffre impressionnant (utilisateurs, avis, économies réalisées)",
            "Obtenez un logo ou nom d'un client/partenaire reconnu",
            "Trouvez ou demandez un témoignage spécifique avec un résultat mesurable",
            "Intégrez ces 3 éléments sur votre site, profil LinkedIn ou pitch"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    {
        "action_id": "action_entrepreneurship_037",
        "title": "Communauté cible",
        "description": "Identifiez et infiltrez 3 communautés où se trouvent vos clients idéaux.",
        "category": "entrepreneurship",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Recherchez des groupes Facebook, subreddits, Discord, Slack dans votre niche",
            "Rejoignez les 3 plus actifs sans vendre — observez d'abord",
            "Contribuez avec des réponses utiles et du contenu de valeur pendant 2 semaines",
            "Une fois reconnu, partagez subtilement votre solution quand c'est pertinent"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    {
        "action_id": "action_entrepreneurship_038",
        "title": "Referral engine",
        "description": "Créez un mécanisme simple pour que vos clients vous recommandent.",
        "category": "entrepreneurship",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Identifiez le moment où vos clients sont le plus satisfaits (juste après un succès)",
            "Créez une demande de recommandation pour ce moment précis",
            "Ajoutez une incitation : réduction, bonus, contenu exclusif",
            "Rendez le partage ultra simple : un lien, un message pré-rédigé"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    {
        "action_id": "action_entrepreneurship_039",
        "title": "AB test mental",
        "description": "Préparez un test A/B simple pour optimiser un élément clé de votre marketing.",
        "category": "entrepreneurship",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "low",
        "instructions": [
            "Choisissez un élément à tester : titre, CTA, image, prix",
            "Créez 2 variantes avec une seule différence",
            "Définissez la métrique de succès (clics, conversions, réponses)",
            "Lancez les deux versions et mesurez les résultats sur 7 jours"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    {
        "action_id": "action_entrepreneurship_040",
        "title": "Rétention boost",
        "description": "Identifiez pourquoi vos clients partent et créez une stratégie de rétention.",
        "category": "entrepreneurship",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "low",
        "instructions": [
            "Listez les 3 principales raisons pour lesquelles les clients partent",
            "Pour chaque raison, identifiez un signal prédictif (baisse d'usage, silence)",
            "Créez une action préventive pour chaque signal",
            "Implémentez un 'check-in' proactif avant que le client ne parte"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    # --- Execution & habits (10) ---
    {
        "action_id": "action_entrepreneurship_041",
        "title": "Planning MIT",
        "description": "Identifiez vos 3 Most Important Tasks du jour pour maximiser votre impact.",
        "category": "entrepreneurship",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "low",
        "instructions": [
            "Listez tout ce que vous devez faire aujourd'hui",
            "Demandez-vous : si je ne pouvais faire que 3 choses, lesquelles auraient le plus d'impact ?",
            "Placez ces 3 MIT en premier dans votre agenda, avant les emails et réunions",
            "Ne passez aux tâches secondaires qu'après avoir terminé au moins 2 MIT"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    {
        "action_id": "action_entrepreneurship_042",
        "title": "Journal de décision",
        "description": "Documentez une décision importante pour pouvoir l'évaluer rétrospectivement.",
        "category": "entrepreneurship",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "low",
        "instructions": [
            "Décrivez la décision à prendre et les options envisagées",
            "Notez les critères de décision et leur poids relatif",
            "Écrivez votre décision et les raisons qui l'ont motivée",
            "Programmez un rappel dans 30 jours pour évaluer le résultat"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    {
        "action_id": "action_entrepreneurship_043",
        "title": "Énergie cartographiée",
        "description": "Identifiez vos pics et creux d'énergie pour optimiser votre emploi du temps.",
        "category": "entrepreneurship",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "Sur les 3 derniers jours, notez votre niveau d'énergie par tranche de 2h",
            "Identifiez vos 2 pics d'énergie et vos 2 creux",
            "Assignez vos tâches créatives et stratégiques aux pics",
            "Réservez les tâches administratives et routinières pour les creux"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    {
        "action_id": "action_entrepreneurship_044",
        "title": "Rétrospective solo",
        "description": "Faites un bilan de votre semaine entrepreneuriale en 3 questions.",
        "category": "entrepreneurship",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "low",
        "instructions": [
            "Qu'est-ce qui a bien fonctionné cette semaine ? (Continuez)",
            "Qu'est-ce qui n'a pas fonctionné ? (Changez)",
            "Qu'est-ce que vous n'avez pas fait mais auriez dû ? (Commencez)",
            "Définissez votre priorité #1 pour la semaine prochaine"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    {
        "action_id": "action_entrepreneurship_045",
        "title": "Délégation test",
        "description": "Identifiez une tâche que vous devriez déléguer et préparez sa passation.",
        "category": "entrepreneurship",
        "duration_min": 5,
        "duration_max": 10,
        "energy_level": "medium",
        "instructions": [
            "Listez vos tâches de la semaine et évaluez : valeur ajoutée haute/basse × urgence",
            "Identifiez les tâches à faible valeur ajoutée qui prennent du temps",
            "Choisissez une tâche à déléguer et documentez le processus en 5 étapes",
            "Identifiez à qui vous pourriez la confier (freelance, assistant, outil)"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    {
        "action_id": "action_entrepreneurship_046",
        "title": "Deep work bloc",
        "description": "Protégez un bloc de travail profond pour avancer sur votre projet stratégique.",
        "category": "entrepreneurship",
        "duration_min": 3,
        "duration_max": 6,
        "energy_level": "medium",
        "instructions": [
            "Bloquez 2 heures dans votre agenda cette semaine — non négociable",
            "Définissez un seul objectif pour ce bloc (ex: finir la landing page)",
            "Préparez votre environnement : notifications off, porte fermée, eau",
            "Commencez par la tâche la plus difficile — votre énergie est au max au début"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    {
        "action_id": "action_entrepreneurship_047",
        "title": "Automatisation chasse",
        "description": "Identifiez une tâche répétitive que vous pouvez automatiser dès maintenant.",
        "category": "entrepreneurship",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "medium",
        "instructions": [
            "Listez les tâches que vous faites plus de 3 fois par semaine",
            "Identifiez celles qui suivent toujours le même processus",
            "Recherchez un outil d'automatisation (Zapier, Make, IFTTT, ou un simple template)",
            "Mettez en place l'automatisation pour la tâche la plus chronophage"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    {
        "action_id": "action_entrepreneurship_048",
        "title": "Mentor minute",
        "description": "Formulez une question précise à poser à un mentor ou expert de votre domaine.",
        "category": "entrepreneurship",
        "duration_min": 4,
        "duration_max": 8,
        "energy_level": "low",
        "instructions": [
            "Identifiez votre plus gros blocage entrepreneurial du moment",
            "Formulez-le en une question précise et spécifique",
            "Identifiez 3 personnes qui pourraient y répondre (réseau, LinkedIn, communauté)",
            "Envoyez un message court et respectueux à la plus accessible"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    {
        "action_id": "action_entrepreneurship_049",
        "title": "Rituel du fondateur",
        "description": "Créez un rituel matinal de 15 minutes dédié à votre posture de fondateur.",
        "category": "entrepreneurship",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "low",
        "instructions": [
            "5 min : relisez votre vision et votre objectif trimestriel",
            "5 min : vérifiez vos métriques clés (revenus, utilisateurs, trafic)",
            "5 min : identifiez votre MIT du jour et bloquez-le dans l'agenda",
            "Faites ce rituel chaque matin pendant 7 jours et observez l'impact"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
    {
        "action_id": "action_entrepreneurship_050",
        "title": "Anti-procrastination",
        "description": "Vainquez la procrastination sur une tâche entrepreneuriale que vous repoussez.",
        "category": "entrepreneurship",
        "duration_min": 3,
        "duration_max": 7,
        "energy_level": "high",
        "instructions": [
            "Identifiez LA tâche que vous repoussez depuis le plus longtemps",
            "Demandez-vous : quelle est la vraie raison ? (peur de l'échec, perfectionnisme, ennui)",
            "Réduisez-la à une version faisable en 15 minutes maximum",
            "Faites-la MAINTENANT — la motivation vient après l'action, pas avant"
        ],
        "is_premium": True,
        "icon": "rocket"
    },
]
