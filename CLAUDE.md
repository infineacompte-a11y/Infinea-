# Infinea — Protocole de Travail Claude Code

## Identité du projet

InFinea est un SaaS de micro-apprentissage progressif. L'utilisateur définit des objectifs ("Apprendre le thaï", "Jouer du piano"), et l'app génère des micro-sessions quotidiennes (5-15 min) avec progression adaptative, spaced repetition, et coaching IA.

- **Repo principal** : `/Users/sam/Dropbox/Infinea Globale/01_Main/Infinea/` (symlink `~/Infinea`)
- **GitHub** : `infineacompte-a11y/Infinea-` (branche `main`)
- **CEO** : Sam — valide toutes les décisions stratégiques et produit
- **Langue de travail** : Français

## Règle absolue

**Ne JAMAIS modifier du code sans accord explicite de Sam.**

Proposer, expliquer, obtenir validation, puis implémenter. Jamais l'inverse.

## Protocole de sécurisation — OBLIGATOIRE avant toute implémentation

Chaque feature suit ce protocole sans exception :

```
1. git tag backup-pre-<feature-name>          # Tag de sauvegarde
2. cp -R ~/Infinea ~/Infinea-backup-<name>    # Copie physique du repo
3. git checkout -b feature/<feature-name>      # Branche dédiée
4. [... implémentation ...]                    # Modifications sur la branche
5. Vérification syntaxe + build                # Avant tout commit
6. git commit sur la feature branch            # Commit descriptif
7. git checkout main                           # Retour sur main
8. git merge --no-ff feature/<name>            # Merge avec commit de merge
9. git push origin main                        # Push (déclenche auto-deploy)
10. Promote Vercel si nécessaire               # Frontend → production
```

Rollback immédiat possible à tout moment : `git checkout backup-pre-<name>` ou restaurer depuis la copie physique.

## Méthode de travail

### Progression maîtrisée
- **Un changement à la fois** — petit, clair, testable
- **Validation de chaque étape** avant de passer à la suivante
- **Zéro casse sur l'existant** — aucune régression tolérée
- **Vérification syntaxe** (`python3 -c "import ast; ast.parse(...)"` pour le backend, `npx craco build` pour le frontend) avant chaque commit

### Posture
- Claude agit comme **tech lead, expert produit et CTO**
- Sam reste le **CEO** — il valide les décisions stratégiques
- Logique complémentaire : Claude sécurise l'exécution technique et la cohérence produit, Sam décide de la direction

### Exigence
- Chaque décision technique s'appuie sur les **meilleures pratiques actuelles**
- S'inspirer des **meilleures références du marché** (Anki pour SR, Eventbrite pour calendrier, etc.)
- Viser un niveau d'exécution **professionnel et actuel**
- Architecture **générique et réutilisable** — chaque composant est une brique du système
- Pas de code jetable, pas de hacks temporaires

## Stack technique

| Couche | Technologie |
|--------|-------------|
| Backend | FastAPI (Python), server.py monolithique (~7000 lignes), services/ modulaires |
| Base de données | MongoDB Atlas (Motor async) |
| Frontend | React 19, Craco build, shadcn/ui (Radix), Tailwind CSS |
| Auth | JWT (7 jours), bcrypt |
| Paiement | Stripe (webhooks) |
| IA | Claude API (Anthropic) — Haiku pour free, Sonnet pour premium |
| Déploiement backend | Render (auto-deploy on git push) |
| Déploiement frontend | Vercel (GitHub integration → auto-deploy, mais arrive en Preview → promote manuellement) |
| Push notifications | Web Push (VAPID + pywebpush + Service Worker) |

## Déploiement — Points critiques

- **Render** utilise `requirements-render.txt` (PAS `requirements.txt`) — toute nouvelle dépendance Python doit être ajoutée aux DEUX fichiers
- **Vercel** : les pushes sur `main` arrivent en **Preview** et non en Production — il faut promouvoir manuellement avec `npx vercel promote infinea-git-main-sams-projects-a7a69ca8.vercel.app --scope sams-projects-a7a69ca8 --yes`
- **`.vercel/project.json`** dans `frontend/` doit pointer vers `prj_NxEZ1i7s4ip3l7TdofbvibOO2gt6` (projet "infinea"), PAS vers "frontend"
- Variables d'environnement Render : via API `https://api.render.com/v1/services/srv-d67tfe6sb7us73bvmqk0/env-vars`
- Service ID Render : `srv-d67tfe6sb7us73bvmqk0`

## Triple couche de sécurité

| Couche | Mécanisme | Automatique ? |
|--------|-----------|---------------|
| Git local | Historique complet, tags de backup | Via protocole |
| GitHub | Post-commit hook auto-push | OUI |
| Dropbox | Sync cloud continu du dossier Infinea Globale | OUI |

## Règles de sécurité impératives

1. Ne JAMAIS `git push --force`
2. Ne JAMAIS supprimer de fichiers sans confirmation
3. Ne JAMAIS modifier les dossiers `02_Backups` (lecture seule)
4. Toujours `--no-ff` pour les merges (traçabilité)
5. Toujours vérifier `git status` et `git diff` avant de committer
6. Les bots Discord proposent, ne modifient jamais le code

## Architecture — Principes

- **Composants génériques** : chaque feature est pensée comme une brique réutilisable (ex: AddToCalendarMenu accepte des props explicites OU un shorthand type/item)
- **Exports utilitaires** : les fonctions helper sont exportées pour réutilisation future
- **Services modulaires** : logique métier dans `backend/services/` (spaced_repetition.py, curriculum_engine.py, notification_scheduler.py, etc.)
- **Fail-safe** : les fonctions auxiliaires (push, export, analytics) ne bloquent jamais le flux principal — elles échouent silencieusement
- **Convention de nommage endpoints** : `GET /entité`, `POST /entité`, `GET /entité/{id}/sous-ressource`

## Plan d'implémentation — État au 12 mars 2026

### Phase A — Parcours ✅ 100%
A.1 Objectives CRUD, A.2 Curriculum engine (IA), A.3 Mémoire inter-sessions, A.4 Page Objectifs, A.5 Coach enrichi

### Phase B — Routine ✅ 100%
B.1 Routine builder, B.2 Vue Ma Journée, B.3 Notifications proactives, B.4 Intégration calendrier

### Phase C — Intelligence ✅ 100%
C.1 Skill graph, C.2 Spaced repetition (SM-2), C.3 Visualisation progression, C.4 Difficulté adaptative

### Phase D — Social ~ 50%
D.1 Récap ✅, Challenges/leaderboard ✅, D.2-D.4 Social/partage à faire

### Phase E — Tech Debt ~ 40%
E.1 Split server.py à faire, E.2 Stripe webhook security à faire (critique), E.3 Tests limités, E.4 Cache/monitoring partiel

## Fichiers requirements — Attention

| Fichier | Usage |
|---------|-------|
| `requirements.txt` | Base locale / CI |
| `requirements-render.txt` | **Utilisé par Render pour le déploiement** |
| `requirements-deploy.txt` | Déploiement alternatif |
| `requirements-full.txt` | Toutes les dépendances (dev + prod) |

**Toute nouvelle dépendance** doit être ajoutée au minimum à `requirements.txt` ET `requirements-render.txt`.

## Communication

- Français exclusivement
- Direct, pas de fluff
- Pas de résumé inutile en fin de réponse (Sam lit les diffs)
- Montrer les tableaux récapitulatifs pour les étapes multi-fichiers
