import React, { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Sparkles,
  RefreshCw,
  ArrowRight,
  Brain,
  MessageCircle,
  Trophy,
  Heart,
  Flame,
  Sunrise,
  HandHeart,
} from "lucide-react";
import { API, authFetch } from "@/App";

// Mode-specific configuration
const COACH_MODES = {
  post_completion: {
    icon: Trophy,
    badge: "Bravo !",
    badgeColor: "bg-emerald-500/10 text-emerald-500",
    glowFrom: "from-emerald-500/30",
    iconBg: "from-emerald-500/20 to-emerald-500/5",
    iconRing: "ring-emerald-500/10",
    iconColor: "text-emerald-500",
    subtitle: "Après ta session",
  },
  post_abandon: {
    icon: HandHeart,
    badge: "On continue",
    badgeColor: "bg-amber-500/10 text-amber-500",
    glowFrom: "from-amber-500/30",
    iconBg: "from-amber-500/20 to-amber-500/5",
    iconRing: "ring-amber-500/10",
    iconColor: "text-amber-500",
    subtitle: "Pas de pression",
  },
  streak_milestone: {
    icon: Flame,
    badge: "Milestone !",
    badgeColor: "bg-orange-500/10 text-orange-500",
    glowFrom: "from-orange-500/30",
    iconBg: "from-orange-500/20 to-orange-500/5",
    iconRing: "ring-orange-500/10",
    iconColor: "text-orange-500",
    subtitle: "Exploit débloqué",
  },
  comeback: {
    icon: Sunrise,
    badge: "Bon retour",
    badgeColor: "bg-sky-500/10 text-sky-500",
    glowFrom: "from-sky-500/30",
    iconBg: "from-sky-500/20 to-sky-500/5",
    iconRing: "ring-sky-500/10",
    iconColor: "text-sky-500",
    subtitle: "Content de te revoir",
  },
  first_visit: {
    icon: Heart,
    badge: "Bienvenue",
    badgeColor: "bg-rose-500/10 text-rose-500",
    glowFrom: "from-rose-500/30",
    iconBg: "from-rose-500/20 to-rose-500/5",
    iconRing: "ring-rose-500/10",
    iconColor: "text-rose-500",
    subtitle: "Ta première micro-action",
  },
  default: {
    icon: Brain,
    badge: "Personnalisé",
    badgeColor: "bg-primary/10 text-primary",
    glowFrom: "from-primary/30",
    iconBg: "from-primary/20 to-primary/5",
    iconRing: "ring-primary/10",
    iconColor: "text-primary",
    subtitle: "Adapté à ton profil",
  },
};

export default function AICoachCard({ onStartAction }) {
  const [coaching, setCoaching] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    fetchCoaching();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchCoaching = async () => {
    if (coaching) {
      setIsRefreshing(true);
    } else {
      setIsLoading(true);
    }
    setError(false);
    try {
      const response = await authFetch(`${API}/ai/coach`);
      if (!response.ok) throw new Error("Erreur");
      const data = await response.json();
      setCoaching(data);
    } catch (e) {
      setError(true);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  if (error) return null;

  if (isLoading) {
    return (
      <div className="relative mb-8 rounded-2xl overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-primary/5 to-transparent" />
        <Card className="border-primary/20 bg-transparent backdrop-blur-sm">
          <CardContent className="p-6 flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center animate-pulse">
              <Brain className="w-6 h-6 text-primary/50" />
            </div>
            <div className="space-y-2 flex-1">
              <div className="h-4 w-32 bg-primary/10 rounded-lg animate-pulse" />
              <div className="h-3 w-full bg-primary/5 rounded-lg animate-pulse" />
              <div className="h-3 w-3/4 bg-primary/5 rounded-lg animate-pulse" />
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const greeting = coaching?.greeting;
  const suggestion = coaching?.suggestion;
  const contextNote = coaching?.context_note;
  const actionId = coaching?.suggested_action_id;
  const coachMode = coaching?.coach_mode || "default";

  if (!greeting && !suggestion) return null;

  const mode = COACH_MODES[coachMode] || COACH_MODES.default;
  const ModeIcon = mode.icon;

  return (
    <div className="relative mb-8 group" data-testid="ai-coach-card">
      {/* Gradient background glow — color changes by mode */}
      <div className={`absolute -inset-px rounded-2xl bg-gradient-to-br ${mode.glowFrom} via-primary/10 to-transparent opacity-60 group-hover:opacity-100 transition-opacity duration-500`} />

      <Card className="relative border-primary/20 bg-card/80 backdrop-blur-sm rounded-2xl overflow-hidden">
        <div className="absolute top-0 right-0 w-48 h-48 bg-gradient-to-bl from-primary/5 to-transparent rounded-bl-full" />

        <CardContent className="relative p-6">
          {/* Header row */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className={`w-11 h-11 rounded-2xl bg-gradient-to-br ${mode.iconBg} flex items-center justify-center ring-1 ${mode.iconRing}`}>
                <ModeIcon className={`w-5 h-5 ${mode.iconColor}`} />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-heading font-semibold text-sm">Coach IA</h3>
                  <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[10px] font-medium ${mode.badgeColor}`}>
                    <Sparkles className="w-2.5 h-2.5" />
                    {mode.badge}
                  </span>
                </div>
                <p className="text-[11px] text-muted-foreground">{mode.subtitle}</p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-muted-foreground hover:text-primary"
              onClick={fetchCoaching}
              disabled={isRefreshing}
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? "animate-spin" : ""}`} />
            </Button>
          </div>

          {/* Greeting */}
          {greeting && (
            <div className="mb-4">
              <p className="text-[15px] leading-relaxed font-medium text-foreground">
                {greeting}
              </p>
            </div>
          )}

          {/* Suggestion + CTA */}
          <div className="flex flex-col gap-3">
            {suggestion && (
              <div className="p-3.5 rounded-xl bg-primary/5 border border-primary/10">
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center shrink-0 mt-0.5">
                    <Sparkles className="w-4 h-4 text-primary" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-primary mb-0.5">
                      {coachMode === "post_completion" ? "Enchaîne avec" :
                       coachMode === "post_abandon" ? "Essaie plutôt" :
                       coachMode === "first_visit" ? "Pour commencer" :
                       "Suggestion pour toi"}
                    </p>
                    <p className="text-sm leading-relaxed">{suggestion}</p>
                  </div>
                </div>
                {actionId && onStartAction && (
                  <Button
                    size="sm"
                    className="mt-3 w-full gap-2"
                    onClick={() => onStartAction(actionId)}
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    {coachMode === "post_completion" ? "Continuer sur ma lancée" :
                     coachMode === "first_visit" ? "Faire ma première action" :
                     "Commencer cette action"}
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Button>
                )}
              </div>
            )}

            {contextNote && (
              <div className="flex items-center gap-2 px-1">
                <MessageCircle className="w-3 h-3 text-muted-foreground shrink-0" />
                <p className="text-xs text-muted-foreground italic leading-relaxed">
                  {contextNote}
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
