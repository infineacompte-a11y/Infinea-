# InFinea - Product Requirements Document

## Original Problem Statement
Créer une application SaaS complète "InFinea" qui transforme les temps morts (2-15 minutes) en micro-actions productives.
Slogan: "Investissez vos instants perdus"

## User Personas
1. **Étudiants** - Optimiser le temps entre les cours
2. **Jeunes actifs** - Productivité pendant les trajets
3. **Freelances** - Structure et efficacité dans les temps fragmentés
4. **Entreprises (B2B)** - Outils QVT pour les collaborateurs

## Core Requirements
- Suggestions IA contextuelles (temps disponible + niveau d'énergie)
- 3 catégories: Apprentissage, Productivité, Bien-être
- Modèle Freemium/Premium (6,99€/mois)
- Authentification JWT + Google OAuth
- Thème sombre moderne

## What's Been Implemented (Jan 2026)

### Phase 1 - MVP Core
- ✅ Auth système complet (JWT + Google OAuth via Emergent)
- ✅ CRUD micro-actions (15 actions seedées)
- ✅ Suggestions IA avec OpenAI GPT-5.2
- ✅ Tracking des sessions utilisateurs
- ✅ Statistiques de progression
- ✅ Stripe checkout pour abonnement Premium
- ✅ MongoDB intégration complète

### Phase 2 - New Features (Jan 2026)
- ✅ **PWA Support** - Service Worker, Manifest, Mode offline
- ✅ **Système de Badges** - 12 badges (streaks, temps, catégories)
- ✅ **Notifications** - Préférences configurables (rappels, alertes streak, badges)
- ✅ **Dashboard B2B** - Création entreprise, analytics QVT anonymisés, invitations

### Frontend Pages
- ✅ Landing Page avec hero, features, pricing
- ✅ Pages auth (Login/Register avec Google OAuth)
- ✅ Dashboard avec slider temps, sélecteur énergie
- ✅ Bibliothèque d'actions avec filtres
- ✅ Session active avec timer et instructions
- ✅ Page progression avec graphiques (Recharts)
- ✅ Page pricing avec intégration Stripe
- ✅ Page profil utilisateur
- ✅ **Page Badges** - Collection et progression
- ✅ **Page Notifications** - Préférences et historique
- ✅ **Dashboard B2B** - Analytics entreprise

### Design System
- Font: Outfit (headings) + DM Sans (body)
- Couleurs: Dark theme (#0A0A0A) + Indigo primary (#6366f1)
- Catégories: Blue (learning), Amber (productivity), Emerald (well-being)
- Glassmorphism et animations fluides

## Prioritized Backlog

### P0 - Critical (Done)
- [x] Auth complète
- [x] Micro-actions CRUD
- [x] Suggestions IA
- [x] Paiement Stripe
- [x] PWA/Offline
- [x] Badges/Gamification
- [x] Notifications
- [x] B2B Dashboard

### P1 - Important (Next)
- [ ] Push notifications réelles (VAPID keys)
- [ ] Intégration calendrier (Google Calendar)
- [ ] Actions personnalisées par utilisateur
- [ ] Export données CSV/PDF

### P2 - Nice to have
- [ ] Intégrations Slack/Teams/Notion
- [ ] Gamification avancée (niveaux, classements)
- [ ] Partage social des accomplissements
- [ ] API publique pour partenaires
- [ ] i18n multi-langues

## Tech Stack
- Backend: FastAPI, MongoDB, emergentintegrations
- Frontend: React, TailwindCSS, Shadcn/UI, Recharts
- Auth: JWT + Emergent Google OAuth
- Payments: Stripe
- AI: OpenAI GPT-5.2 via Emergent LLM Key
- PWA: Service Worker + Manifest

## Next Tasks
1. Intégrer VAPID keys pour push notifications réels
2. Ajouter intégration Google Calendar pour planification
3. Système de niveaux/XP pour gamification avancée
4. Export des statistiques en PDF
