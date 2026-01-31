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

### Backend (FastAPI)
- ✅ Auth système complet (JWT + Google OAuth via Emergent)
- ✅ CRUD micro-actions (15 actions seedées)
- ✅ Suggestions IA avec OpenAI GPT-5.2
- ✅ Tracking des sessions utilisateurs
- ✅ Statistiques de progression
- ✅ Stripe checkout pour abonnement Premium
- ✅ MongoDB intégration complète

### Frontend (React)
- ✅ Landing Page moderne avec hero, features, pricing
- ✅ Pages auth (Login/Register avec Google OAuth)
- ✅ Dashboard avec slider temps, sélecteur énergie
- ✅ Bibliothèque d'actions avec filtres par catégorie
- ✅ Session active avec timer et instructions
- ✅ Page progression avec graphiques (Recharts)
- ✅ Page pricing avec intégration Stripe
- ✅ Page profil utilisateur

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

### P1 - Important (Next)
- [ ] Notifications push
- [ ] Mode hors-ligne
- [ ] Actions personnalisées utilisateur
- [ ] Dashboard B2B admin

### P2 - Nice to have
- [ ] Intégrations Slack/Teams/Notion
- [ ] Gamification avancée (badges, niveaux)
- [ ] Partage social des accomplissements
- [ ] API publique pour partenaires

## Tech Stack
- Backend: FastAPI, MongoDB, emergentintegrations
- Frontend: React, TailwindCSS, Shadcn/UI, Recharts
- Auth: JWT + Emergent Google OAuth
- Payments: Stripe
- AI: OpenAI GPT-5.2 via Emergent LLM Key

## Next Tasks
1. Ajouter notifications pour rappels de micro-actions
2. Implémenter mode offline avec service worker
3. Créer système de badges/achievements
4. Dashboard analytics pour admins B2B
