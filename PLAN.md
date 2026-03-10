# InFinea — Plan Phase 0 + Phase 1
## Méthode : étape par étape, validation CEO avant chaque exécution

---

## PHASE 0 — Sécurité (Fondations non-négociables)

### Étape 0.1 — JWT Secret : supprimer le fallback en dur
- **Problème** : ligne 34 de server.py → `JWT_SECRET = os.environ.get('JWT_SECRET', 'infinea-secret-key-change-in-production')` — si la variable d'env manque, n'importe qui peut forger des tokens
- **Fix** : crasher au démarrage si JWT_SECRET est absent (mieux vaut ne pas démarrer que démarrer en mode passoire)
- **Impact** : 1 ligne modifiée
- **Risque** : zéro si la var d'env est bien configurée sur Render (à vérifier avant)

### Étape 0.2 — Supprimer /premium/activate-free
- **Problème** : ligne 1550 → n'importe quel utilisateur connecté peut s'activer Premium gratuitement
- **Fix** : supprimer la route entière (Stripe fonctionne, le promo code aussi)
- **Impact** : ~14 lignes supprimées
- **Risque** : zéro (route temporaire, Stripe est opérationnel)

### Étape 0.3 — Restreindre les headers CORS
- **Problème** : ligne 4140 → `allow_headers=["*"]` accepte n'importe quel header
- **Fix** : remplacer par `["Content-Type", "Authorization"]`
- **Impact** : 1 ligne modifiée
- **Risque** : faible (tester que le frontend fonctionne toujours)

### Étape 0.4 — Validation mot de passe
- **Problème** : `UserCreate.password` n'a aucune contrainte — un mot de passe "a" est accepté
- **Fix** : ajouter `min_length=8` au champ password du modèle Pydantic
- **Impact** : 1 ligne modifiée
- **Risque** : zéro (n'affecte que les nouveaux comptes)

### Étape 0.5 — Rate limiting sur auth + AI
- **Problème** : aucune protection brute-force sur /auth/login, /auth/register, routes AI
- **Fix** : ajouter `slowapi` avec des limites raisonnables (ex: 5 login/min, 10 register/h)
- **Impact** : ~20 lignes ajoutées + 1 dépendance
- **Risque** : faible (limites généreuses pour ne pas bloquer les vrais utilisateurs)

### Étape 0.6 — Rotation des secrets exposés
- **Problème** : le fichier .env a été commité dans le passé (3 commits trouvés) — les secrets MongoDB et Anthropic sont potentiellement compromis
- **Fix** : rotation du mot de passe MongoDB Atlas + régénération clé Anthropic
- **Impact** : action manuelle sur les dashboards Atlas + Anthropic + mise à jour Render
- **Risque** : downtime si on oublie de mettre à jour Render

---

## PHASE 1 — Event Tracking (Fondation Data)

### Étape 1.1 — Créer le service event_tracker.py
- **Objectif** : un module simple `track_event(user_id, event_type, metadata)` qui écrit dans une collection `event_log`
- **Impact** : 1 nouveau fichier (~30 lignes)
- **Risque** : zéro (aucun code existant modifié)

### Étape 1.2 — Instrumenter les routes auth
- **Events** : `user_registered`, `user_logged_in`, `user_logged_out`
- **Impact** : 3 lignes ajoutées (1 par route)

### Étape 1.3 — Instrumenter les routes suggestions/actions
- **Events** : `suggestion_generated`, `suggestion_viewed`, `action_started`, `action_completed`, `action_abandoned`
- **Impact** : ~5 lignes ajoutées

### Étape 1.4 — Instrumenter les routes AI
- **Events** : `ai_coach_called`, `ai_debrief_called`, `ai_analysis_called`
- **Impact** : ~3 lignes ajoutées

### Étape 1.5 — Instrumenter les routes premium/paiement
- **Events** : `checkout_started`, `premium_activated`, `premium_cancelled`
- **Impact** : ~3 lignes ajoutées

### Étape 1.6 — Index MongoDB + endpoint admin de vérification
- **Objectif** : index sur (user_id, timestamp) + route `/admin/events-stats` pour vérifier que les events arrivent
- **Impact** : ~15 lignes

---

## Méthode de travail

À chaque étape :
1. Je te montre le code AVANT de le modifier
2. Je te propose le fix exact
3. Tu valides → j'exécute
4. On vérifie ensemble que rien n'est cassé
5. On passe à l'étape suivante
