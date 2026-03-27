/**
 * InFinea — Shared social constants and utilities.
 *
 * Single source of truth for activity types, reactions, and time formatting.
 * Used across CommunityFeedPage, ActivityDetailPage, HashtagFeedPage,
 * ConversationPage, SavedPage, and all social components.
 */

import {
  Zap,
  Award,
  Flame,
  Trophy,
  MessageCircle,
  Star,
} from "lucide-react";

// ── Activity type configuration ──
export const ACTIVITY_CONFIG = {
  session_completed: {
    icon: Zap,
    color: "#459492",
    label: "Session",
    getText: (data) =>
      `a terminé "${data.action_title || "une micro-action"}" en ${data.duration || 0} min`,
  },
  badge_earned: {
    icon: Award,
    color: "#E48C75",
    label: "Badge",
    getText: (data) =>
      `a obtenu le badge "${data.badge_name || "nouveau badge"}"`,
  },
  streak_milestone: {
    icon: Flame,
    color: "#E48C75",
    label: "Streak",
    getText: (data) => `a atteint ${data.streak_days} jours de streak !`,
  },
  challenge_completed: {
    icon: Trophy,
    color: "#459492",
    label: "Défi",
    getText: (data) =>
      `a complété le défi "${data.challenge_title || "un défi"}" !`,
  },
  level_up: {
    icon: Star,
    color: "#F5A623",
    label: "Niveau",
    getText: (data) => `a atteint le niveau ${data.level || "?"} !`,
  },
  post: {
    icon: MessageCircle,
    color: "#55B3AE",
    label: "Post",
    isPost: true,
  },
};

// ── Reaction types (domain-specific — not generic likes) ──
export const REACTIONS = [
  { type: "bravo", emoji: "👏", label: "Bravo" },
  { type: "inspire", emoji: "💡", label: "Inspirant" },
  { type: "fire", emoji: "🔥", label: "En feu" },
  { type: "solidaire", emoji: "🤝", label: "Solidaire" },
  { type: "curieux", emoji: "🧠", label: "Curieux" },
];

// ── Message reaction map ──
export const MESSAGE_REACTIONS = {
  bravo: "👏",
  inspire: "✨",
  fire: "🔥",
  solidaire: "🤝",
  curieux: "🧠",
};

// ── Time formatting (French) ──
export function timeAgo(iso) {
  if (!iso) return "";
  const diff = Date.now() - new Date(iso).getTime();
  const min = Math.floor(diff / 60000);
  if (min < 1) return "à l'instant";
  if (min < 60) return `${min}min`;
  const h = Math.floor(min / 60);
  if (h < 24) return `${h}h`;
  const d = Math.floor(h / 24);
  if (d < 7) return `${d}j`;
  return new Date(iso).toLocaleDateString("fr-FR", {
    day: "numeric",
    month: "short",
  });
}

// ── User initials ──
export function getInitials(name) {
  if (!name) return "U";
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

// ── Total reaction count from counts object ──
export function totalReactionCount(reactionCounts) {
  if (!reactionCounts) return 0;
  return Object.values(reactionCounts).reduce((sum, v) => sum + (v || 0), 0);
}
