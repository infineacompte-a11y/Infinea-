import React, { useState, useEffect, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import FollowButton from "@/components/FollowButton";
import {
  UserPlus,
  Camera,
  PenLine,
  AtSign,
  CheckCircle2,
  ChevronRight,
  Sparkles,
  X,
  Users,
  Crown,
  Flame,
  Target,
  Zap,
} from "lucide-react";
import { API, authFetch } from "@/App";

/**
 * SocialOnboardingCard — Progressive social onboarding.
 *
 * Benchmarked:
 * - LinkedIn: profile completion meter (progressive, non-punitive)
 * - Instagram: follow 5+ accounts during onboarding (grid, context reasons)
 * - Strava: connection step with activity-based suggestions
 * - Duolingo: immediate engagement + celebration on milestones
 *
 * Architecture:
 * - Fetches onboarding status + suggested users in parallel
 * - 3 sections: Profile completion → Follow suggestions → First post
 * - Each section dismisses independently as completed
 * - Celebrates milestones (3 follows, 5 follows, profile complete)
 * - Full card dismissible, but state persisted server-side
 */

// ── Reason tags for suggested users ──
const REASON_CONFIG = {
  mutual:     { label: "Amis en commun",    color: "#5DB786" },
  follows_you:{ label: "Te suit",           color: "#459492" },
  objectives: { label: "Même objectif",     color: "#459492" },
  same_goal:  { label: "Objectif identique",color: "#55B3AE" },
  group:      { label: "Même groupe",       color: "#459492" },
  active:     { label: "Très actif",        color: "#E48C75" },
  new_user:   { label: "Nouveau membre",    color: "#55B3AE" },
};

// ── Profile completion items ──
const PROFILE_STEPS = [
  { key: "avatar",       label: "Photo de profil", icon: Camera,  link: "/profile", weight: 30 },
  { key: "display_name", label: "Nom d'affichage", icon: PenLine, link: "/profile", weight: 20 },
  { key: "username",     label: "Identifiant @",   icon: AtSign,  link: "/profile", weight: 20 },
  { key: "bio",          label: "Bio",             icon: PenLine, link: "/profile", weight: 20 },
  { key: "cover_photo",  label: "Couverture",      icon: Camera,  link: null,       weight: 10 },
];

function getInitials(name) {
  if (!name) return "U";
  return name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2);
}

export default function SocialOnboardingCard({ currentUserId, onFollowChange }) {
  const navigate = useNavigate();
  const [status, setStatus] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dismissed, setDismissed] = useState(false);
  const [followedIds, setFollowedIds] = useState(new Set());
  const [celebration, setCelebration] = useState(null); // "profile" | "follows" | "complete" | null

  const fetchData = useCallback(async () => {
    try {
      const [statusRes, suggestRes] = await Promise.all([
        authFetch(`${API}/social/onboarding-status`),
        authFetch(`${API}/feed/suggested-users?limit=12`),
      ]);
      if (statusRes.ok) {
        const data = await statusRes.json();
        setStatus(data);
        if (data.dismissed) setDismissed(true);
      }
      if (suggestRes.ok) {
        const data = await suggestRes.json();
        setSuggestions(data.users || []);
      }
    } catch { /* silent */ }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleDismiss = async () => {
    setDismissed(true);
    try {
      await authFetch(`${API}/social/onboarding-dismiss`, { method: "POST" });
    } catch { /* silent */ }
  };

  const handleFollowInCard = useCallback((userId, isFollowing) => {
    setFollowedIds((prev) => {
      const next = new Set(prev);
      if (isFollowing) next.add(userId);
      else next.delete(userId);
      return next;
    });
    onFollowChange?.(userId, isFollowing);

    // Check milestone celebrations
    setStatus((prev) => {
      if (!prev) return prev;
      const newCount = prev.social.following_count + (isFollowing ? 1 : -1);
      const updated = {
        ...prev,
        social: { ...prev.social, following_count: newCount },
      };
      // Celebrate at target
      if (isFollowing && newCount >= prev.social.target_follows && prev.social.following_count < prev.social.target_follows) {
        setCelebration("follows");
        setTimeout(() => setCelebration(null), 3000);
      }
      return updated;
    });
  }, [onFollowChange]);

  // Don't render if dismissed, loading, or no onboarding needed
  if (loading || dismissed || !status || !status.needs_onboarding) return null;

  const { profile, social } = status;
  const effectiveFollowing = social.following_count + followedIds.size;
  const followProgress = Math.min(effectiveFollowing / social.target_follows, 1);
  const profileComplete = profile.score >= 70;
  const followsComplete = effectiveFollowing >= social.target_follows;

  // Filter out already-followed users from suggestions
  const availableSuggestions = suggestions.filter(
    (u) => !followedIds.has(u.user_id)
  );

  return (
    <div className="mb-6 opacity-0 animate-fade-in" style={{ animationFillMode: "forwards" }}>
      {/* Celebration overlay */}
      {celebration && (
        <div className="mb-3 p-4 rounded-2xl bg-gradient-to-r from-[#459492] to-[#55B3AE] text-white text-center animate-fade-in">
          <Sparkles className="w-6 h-6 mx-auto mb-1" />
          <p className="font-semibold text-sm">
            {celebration === "follows"
              ? `Bravo ! Tu suis ${social.target_follows} personnes !`
              : celebration === "profile"
              ? "Profil complété !"
              : "Onboarding terminé !"}
          </p>
          <p className="text-white/70 text-xs mt-0.5">
            {celebration === "follows"
              ? "Ton fil va se remplir d'activités inspirantes"
              : "Les autres membres peuvent maintenant te découvrir"}
          </p>
        </div>
      )}

      <Card className="overflow-hidden border-[#459492]/15 shadow-lg shadow-[#459492]/5">
        {/* Header */}
        <div className="bg-gradient-to-r from-[#275255] to-[#459492] px-5 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-white/15 flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-white font-semibold text-sm">
                Bienvenue dans la communauté
              </h3>
              <p className="text-white/60 text-xs">
                {profileComplete && followsComplete
                  ? "Plus qu'un pas !"
                  : `Quelques étapes pour bien démarrer`}
              </p>
            </div>
          </div>
          <button
            onClick={handleDismiss}
            className="text-white/40 hover:text-white/70 transition-colors p-1"
            title="Masquer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <CardContent className="p-0">
          {/* ── Section 1: Profile Completion ── */}
          {!profileComplete && (
            <div className="px-5 py-4 border-b border-border/30">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-medium text-foreground flex items-center gap-2">
                  <Target className="w-4 h-4 text-[#459492]" />
                  Complète ton profil
                </h4>
                <span className="text-xs font-medium text-[#459492] tabular-nums">
                  {profile.score}%
                </span>
              </div>

              {/* Progress bar */}
              <div className="h-2 bg-muted rounded-full overflow-hidden mb-3">
                <div
                  className="h-full bg-gradient-to-r from-[#459492] to-[#55B3AE] rounded-full transition-all duration-700 ease-out"
                  style={{ width: `${profile.score}%` }}
                />
              </div>

              {/* Missing items as chips */}
              <div className="flex flex-wrap gap-2">
                {PROFILE_STEPS.map((step) => {
                  const isDone = !profile.missing_fields.includes(step.key);
                  const StepIcon = step.icon;
                  if (isDone) return null;
                  return (
                    <button
                      key={step.key}
                      onClick={() => step.link && navigate(step.link)}
                      className="inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-[#459492]/8 text-[#459492] hover:bg-[#459492]/15 transition-colors border border-[#459492]/10"
                    >
                      <StepIcon className="w-3 h-3" />
                      {step.label}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* ── Section 2: Follow Suggestions ── */}
          {!followsComplete && availableSuggestions.length > 0 && (
            <div className="px-5 py-4 border-b border-border/30">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-medium text-foreground flex items-center gap-2">
                  <Users className="w-4 h-4 text-[#459492]" />
                  Suis des membres
                </h4>
                <span className="text-xs text-muted-foreground tabular-nums">
                  {effectiveFollowing}/{social.target_follows}
                </span>
              </div>

              {/* Follow progress */}
              <div className="h-1.5 bg-muted rounded-full overflow-hidden mb-4">
                <div
                  className="h-full bg-gradient-to-r from-[#459492] to-[#5DB786] rounded-full transition-all duration-500 ease-out"
                  style={{ width: `${followProgress * 100}%` }}
                />
              </div>

              {/* Suggestion cards — 2-column grid (richer than horizontal scroll) */}
              <div className="grid grid-cols-2 gap-2.5">
                {availableSuggestions.slice(0, 6).map((user) => {
                  const reason = REASON_CONFIG[user.reason] || REASON_CONFIG.active;
                  return (
                    <div
                      key={user.user_id}
                      className="flex flex-col items-center text-center p-3 rounded-xl bg-muted/40 border border-border/30 hover:border-[#459492]/20 hover:shadow-sm transition-all duration-200"
                    >
                      <Link to={`/users/${user.user_id}`}>
                        <Avatar className="w-12 h-12 mb-2 ring-2 ring-offset-2 ring-offset-background ring-primary/10">
                          <AvatarImage src={user.avatar_url} alt={user.display_name} />
                          <AvatarFallback className="bg-primary/10 text-primary text-sm">
                            {getInitials(user.display_name)}
                          </AvatarFallback>
                        </Avatar>
                      </Link>
                      <Link
                        to={`/users/${user.user_id}`}
                        className="text-xs font-medium text-foreground truncate w-full hover:text-primary transition-colors"
                      >
                        {user.display_name}
                      </Link>
                      {user.username && (
                        <span className="text-[10px] text-muted-foreground truncate w-full">
                          @{user.username}
                        </span>
                      )}
                      {/* Reason tag */}
                      <span
                        className="text-[9px] font-medium mt-1 px-2 py-0.5 rounded-full"
                        style={{
                          backgroundColor: `${reason.color}12`,
                          color: reason.color,
                        }}
                      >
                        {reason.label}
                        {user.reason === "mutual" && user.mutual_count
                          ? ` (${user.mutual_count})`
                          : ""}
                      </span>
                      {/* Context stats */}
                      <div className="flex items-center gap-2 mt-1.5 text-[10px] text-muted-foreground">
                        {user.streak_days > 0 && (
                          <span className="flex items-center gap-0.5">
                            <Flame className="w-2.5 h-2.5 text-[#E48C75]" />
                            {user.streak_days}j
                          </span>
                        )}
                        {user.followers_count > 0 && (
                          <span>{user.followers_count} abonné{user.followers_count > 1 ? "s" : ""}</span>
                        )}
                      </div>
                      {/* Follow button */}
                      <div className="mt-2 w-full">
                        <FollowButton
                          userId={user.user_id}
                          initialFollowing={false}
                          size="xs"
                          onToggle={(isFollowing) =>
                            handleFollowInCard(user.user_id, isFollowing)
                          }
                        />
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* See more link */}
              {availableSuggestions.length > 6 && (
                <Link
                  to="/search"
                  className="flex items-center justify-center gap-1 text-xs text-[#459492] hover:text-[#275255] mt-3 transition-colors"
                >
                  Voir plus de suggestions
                  <ChevronRight className="w-3.5 h-3.5" />
                </Link>
              )}
            </div>
          )}

          {/* ── Section 3: First Post Nudge ── */}
          {!social.has_posted && (
            <div className="px-5 py-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#E48C75]/15 to-[#459492]/10 flex items-center justify-center shrink-0">
                  <Zap className="w-5 h-5 text-[#E48C75]" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-foreground">
                    Partage ta première activité
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Complète une session pour apparaître dans le fil
                  </p>
                </div>
                <Link to="/my-day">
                  <Button
                    size="sm"
                    variant="outline"
                    className="rounded-xl gap-1.5 text-xs border-[#459492]/30 text-[#459492] hover:bg-[#459492]/5"
                  >
                    <Zap className="w-3.5 h-3.5" />
                    C'est parti
                  </Button>
                </Link>
              </div>
            </div>
          )}

          {/* All steps complete but card not dismissed yet */}
          {profileComplete && followsComplete && social.has_posted && (
            <div className="px-5 py-4 text-center">
              <CheckCircle2 className="w-8 h-8 text-[#5DB786] mx-auto mb-2" />
              <p className="text-sm font-medium text-foreground">
                Tu es prêt !
              </p>
              <p className="text-xs text-muted-foreground mb-3">
                Ton profil est complet et tu suis assez de membres pour un fil riche.
              </p>
              <Button
                size="sm"
                variant="ghost"
                className="text-xs text-muted-foreground"
                onClick={handleDismiss}
              >
                Fermer définitivement
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
