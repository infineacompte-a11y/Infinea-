import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Zap,
  Clock,
  Play,
  SkipForward,
  Calendar,
  Repeat,
  TrendingUp,
  Loader2,
  Sparkles,
  CheckCircle2,
  XCircle,
  ChevronRight,
  Flame,
  Target,
  Sun,
  Sunrise,
  Moon,
} from "lucide-react";
import Sidebar from "@/components/Sidebar";
import { API, authFetch, useAuth } from "@/App";
import { toast } from "sonner";

// ─── Source icons & labels ──────────────────────────────────
const SOURCE_CONFIG = {
  calendar_gap: {
    icon: Calendar,
    label: "Calendrier",
    color: "text-blue-400",
    bgColor: "bg-blue-500/10",
  },
  routine_window: {
    icon: Repeat,
    label: "Routine",
    color: "text-emerald-400",
    bgColor: "bg-emerald-500/10",
  },
  behavioral_pattern: {
    icon: TrendingUp,
    label: "Pattern détecté",
    color: "text-purple-400",
    bgColor: "bg-purple-500/10",
  },
};

// ─── Time helpers ───────────────────────────────────────────
function getTimeOfDayIcon(hour) {
  if (hour < 12) return Sunrise;
  if (hour < 18) return Sun;
  return Moon;
}

function formatTime(isoString) {
  if (!isoString) return "";
  const d = new Date(isoString);
  return d.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
}

function formatDuration(minutes) {
  if (!minutes) return "";
  if (minutes < 60) return `${minutes} min`;
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return m > 0 ? `${h}h${m.toString().padStart(2, "0")}` : `${h}h`;
}

function getGreeting(name) {
  const h = new Date().getHours();
  const first = name?.split(" ")[0] || "";
  if (h < 12) return `Bonjour${first ? ` ${first}` : ""} !`;
  if (h < 18) return `Bon après-midi${first ? ` ${first}` : ""} !`;
  return `Bonsoir${first ? ` ${first}` : ""} !`;
}

function isInstantNow(instant) {
  const now = new Date();
  const start = new Date(instant.window_start);
  const end = new Date(instant.window_end);
  return now >= start && now <= end;
}

function isInstantPast(instant) {
  return new Date() > new Date(instant.window_end);
}

function isInstantFuture(instant) {
  return new Date() < new Date(instant.window_start);
}

// ─── Confidence badge ───────────────────────────────────────
function ConfidenceBadge({ score }) {
  const pct = Math.round((score || 0) * 100);
  let variant = "outline";
  let className = "text-muted-foreground border-border/50";
  if (pct >= 70) {
    variant = "default";
    className = "bg-emerald-500/20 text-emerald-400 border-emerald-500/30";
  } else if (pct >= 50) {
    className = "text-amber-400 border-amber-500/30";
  }
  return (
    <Badge variant={variant} className={`text-[10px] ${className}`}>
      {pct}% confiance
    </Badge>
  );
}

// ═══════════════════════════════════════════════════════════════
// Instant Card — the core interaction unit
// ═══════════════════════════════════════════════════════════════
function InstantCard({ instant, onExploit, onSkip, isLoading }) {
  const navigate = useNavigate();
  const source = SOURCE_CONFIG[instant.source] || SOURCE_CONFIG.behavioral_pattern;
  const SourceIcon = source.icon;
  const now = isInstantNow(instant);
  const past = isInstantPast(instant);
  const exploited = instant._exploited;
  const skipped = instant._skipped;

  const action = instant.recommended_action || {};
  const startTime = formatTime(instant.window_start);
  const endTime = formatTime(instant.window_end);
  const duration = instant.duration_minutes || 0;

  const handleExploit = () => {
    if (action.action_id) {
      onExploit(instant.instant_id, action.action_id);
    }
  };

  return (
    <Card
      className={`transition-all duration-300 ${
        now
          ? "border-primary/50 shadow-lg shadow-primary/5 ring-1 ring-primary/20"
          : past
          ? "opacity-50"
          : "border-border/30"
      } ${exploited ? "border-emerald-500/40 bg-emerald-500/5" : ""} ${
        skipped ? "border-muted/40 bg-muted/5" : ""
      }`}
    >
      <CardContent className="p-4">
        {/* Header: time window + source */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className={`w-7 h-7 rounded-lg ${source.bgColor} flex items-center justify-center`}>
              <SourceIcon className={`w-3.5 h-3.5 ${source.color}`} />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="text-sm font-medium text-foreground">
                  {startTime} – {endTime}
                </span>
                {now && (
                  <Badge className="bg-primary/20 text-primary text-[9px] px-1.5 py-0 animate-pulse">
                    MAINTENANT
                  </Badge>
                )}
              </div>
              <span className="text-[11px] text-muted-foreground">{source.label}</span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-[10px] text-muted-foreground border-border/50">
              <Clock className="w-3 h-3 mr-1" />
              {formatDuration(duration)}
            </Badge>
            <ConfidenceBadge score={instant.confidence_score} />
          </div>
        </div>

        {/* Recommended action */}
        {action.title && (
          <div className="mb-3 p-3 rounded-lg bg-card/50 border border-border/20">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center shrink-0 mt-0.5">
                <Sparkles className="w-4 h-4 text-primary" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground leading-tight">
                  {action.title}
                </p>
                {action.category && (
                  <p className="text-[11px] text-muted-foreground mt-0.5 capitalize">
                    {action.category.replace("_", " ")}
                    {action.duration_min && action.duration_max && (
                      <span> · {action.duration_min}–{action.duration_max} min</span>
                    )}
                  </p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Action buttons */}
        {!exploited && !skipped && !past && (
          <div className="flex gap-2">
            <Button
              className={`flex-1 gap-2 ${
                now
                  ? "bg-gradient-to-r from-primary to-primary/80 hover:from-primary/90 hover:to-primary/70 shadow-md"
                  : ""
              }`}
              variant={now ? "default" : "outline"}
              disabled={isLoading || !action.action_id}
              onClick={handleExploit}
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Play className="w-4 h-4" />
              )}
              {now ? "Commencer" : "Lancer"}
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="text-muted-foreground hover:text-foreground shrink-0"
              disabled={isLoading}
              onClick={() => onSkip(instant.instant_id)}
            >
              <SkipForward className="w-4 h-4" />
            </Button>
          </div>
        )}

        {/* Status badges for completed instants */}
        {exploited && (
          <div className="flex items-center gap-2 text-emerald-400 text-sm">
            <CheckCircle2 className="w-4 h-4" />
            <span>Exploité</span>
          </div>
        )}
        {skipped && (
          <div className="flex items-center gap-2 text-muted-foreground text-sm">
            <XCircle className="w-4 h-4" />
            <span>Passé</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ═══════════════════════════════════════════════════════════════
// Hero Card — the big CTA for the current/next instant
// ═══════════════════════════════════════════════════════════════
function HeroInstant({ instant, onExploit, isLoading }) {
  if (!instant) return null;

  const action = instant.recommended_action || {};
  const duration = instant.duration_minutes || 0;
  const now = isInstantNow(instant);
  const startTime = formatTime(instant.window_start);

  return (
    <Card className="border-primary/30 bg-gradient-to-br from-primary/5 to-primary/10 shadow-xl shadow-primary/5 overflow-hidden">
      <CardContent className="p-6">
        <div className="flex items-center gap-2 mb-1">
          <Zap className="w-5 h-5 text-primary" />
          <span className="text-xs text-primary font-medium uppercase tracking-wider">
            {now ? "Micro-instant disponible" : `Prochain à ${startTime}`}
          </span>
        </div>

        <h2 className="text-xl font-semibold text-foreground mt-2 mb-1">
          {action.title || "Action recommandée"}
        </h2>

        <p className="text-sm text-muted-foreground mb-4">
          {duration > 0 && `${duration} min`}
          {action.category && ` · ${action.category.replace("_", " ")}`}
        </p>

        <Button
          size="lg"
          className="w-full gap-2 bg-gradient-to-r from-primary to-primary/80 hover:from-primary/90 hover:to-primary/70 shadow-lg text-base h-12"
          disabled={isLoading || !action.action_id}
          onClick={() => onExploit(instant.instant_id, action.action_id)}
        >
          {isLoading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Play className="w-5 h-5" />
          )}
          {now ? "Commencer maintenant" : "Lancer cette action"}
        </Button>
      </CardContent>
    </Card>
  );
}

// ═══════════════════════════════════════════════════════════════
// Stats Summary — quick metrics row
// ═══════════════════════════════════════════════════════════════
function StatsSummary({ instants, stats }) {
  const total = instants.length;
  const exploited = instants.filter((i) => i._exploited).length;
  const available = instants.filter((i) => !isInstantPast(i) && !i._exploited && !i._skipped).length;

  return (
    <div className="grid grid-cols-3 gap-3">
      <div className="text-center p-3 rounded-xl bg-card border border-border/20">
        <p className="text-2xl font-bold text-foreground">{total}</p>
        <p className="text-[11px] text-muted-foreground">Détectés</p>
      </div>
      <div className="text-center p-3 rounded-xl bg-card border border-border/20">
        <p className="text-2xl font-bold text-emerald-400">{exploited}</p>
        <p className="text-[11px] text-muted-foreground">Exploités</p>
      </div>
      <div className="text-center p-3 rounded-xl bg-card border border-border/20">
        <p className="text-2xl font-bold text-primary">{available}</p>
        <p className="text-[11px] text-muted-foreground">Disponibles</p>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// Empty State
// ═══════════════════════════════════════════════════════════════
function EmptyState() {
  return (
    <Card className="border-dashed border-border/50">
      <CardContent className="p-8 text-center">
        <div className="w-14 h-14 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-4">
          <Zap className="w-7 h-7 text-primary/60" />
        </div>
        <h3 className="text-lg font-medium text-foreground mb-2">
          Pas de micro-instants détectés
        </h3>
        <p className="text-sm text-muted-foreground max-w-sm mx-auto">
          Le moteur apprend tes patterns d'usage. Continue d'utiliser InFinea et les
          micro-instants apparaîtront automatiquement.
        </p>
        <div className="mt-4 flex flex-col gap-2 max-w-xs mx-auto">
          <p className="text-[11px] text-muted-foreground">Pour accélérer la détection :</p>
          <ul className="text-[11px] text-muted-foreground text-left space-y-1">
            <li>• Connecte ton calendrier Google</li>
            <li>• Crée des routines quotidiennes</li>
            <li>• Complète quelques sessions</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
}

// ═══════════════════════════════════════════════════════════════
// Main Page
// ═══════════════════════════════════════════════════════════════
export default function MicroInstantsPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [instants, setInstants] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(null);

  // ── Fetch today's micro-instants ──
  const fetchInstants = useCallback(async () => {
    try {
      const res = await authFetch(`${API}/micro-instants/today`);
      if (res.ok) {
        const data = await res.json();
        setInstants(data.instants || []);
      }
    } catch {
      toast.error("Impossible de charger les micro-instants");
    } finally {
      setLoading(false);
    }
  }, []);

  // ── Fetch stats ──
  const fetchStats = useCallback(async () => {
    try {
      const res = await authFetch(`${API}/micro-instants/stats`);
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch {
      /* silent */
    }
  }, []);

  useEffect(() => {
    fetchInstants();
    fetchStats();
  }, [fetchInstants, fetchStats]);

  // ── Exploit action ──
  const handleExploit = async (instantId, actionId) => {
    setActionLoading(instantId);
    try {
      const res = await authFetch(`${API}/micro-instants/${instantId}/exploit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action_id: actionId }),
      });

      if (res.ok) {
        const data = await res.json();
        // Mark instant as exploited locally
        setInstants((prev) =>
          prev.map((i) =>
            i.instant_id === instantId ? { ...i, _exploited: true } : i
          )
        );
        toast.success("Micro-instant exploité !");

        // Navigate to active session if available
        if (data.action?.action_id) {
          navigate(`/actions`);
        }
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || "Erreur lors de l'exploitation");
      }
    } catch {
      toast.error("Erreur réseau");
    } finally {
      setActionLoading(null);
    }
  };

  // ── Skip action ──
  const handleSkip = async (instantId) => {
    setActionLoading(instantId);
    try {
      const res = await authFetch(`${API}/micro-instants/${instantId}/skip`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason: "not_interested" }),
      });

      if (res.ok) {
        setInstants((prev) =>
          prev.map((i) =>
            i.instant_id === instantId ? { ...i, _skipped: true } : i
          )
        );
      }
    } catch {
      /* silent */
    } finally {
      setActionLoading(null);
    }
  };

  // ── Determine hero instant (current or next available) ──
  const activeInstants = instants.filter(
    (i) => !i._exploited && !i._skipped && !isInstantPast(i)
  );
  const heroInstant =
    activeInstants.find((i) => isInstantNow(i)) || activeInstants[0] || null;
  const otherInstants = instants.filter(
    (i) => i.instant_id !== heroInstant?.instant_id
  );

  // ── Stats from API ──
  const exploitRate = stats?.exploitation_rate
    ? Math.round(stats.exploitation_rate * 100)
    : null;

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <main className="lg:ml-64 pt-20 lg:pt-8 pb-8 px-4 lg:px-8">
        <div className="max-w-2xl mx-auto space-y-6">
          {/* Header */}
          <div>
            <h1 className="text-2xl font-bold text-foreground">
              {getGreeting(user?.name)}
            </h1>
            <p className="text-sm text-muted-foreground mt-1 flex items-center gap-2">
              <Zap className="w-4 h-4 text-primary" />
              Tes micro-instants du jour
              {exploitRate !== null && (
                <Badge
                  variant="outline"
                  className="text-[10px] ml-1 text-primary border-primary/30"
                >
                  <Flame className="w-3 h-3 mr-1" />
                  {exploitRate}% exploités
                </Badge>
              )}
            </p>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : instants.length === 0 ? (
            <EmptyState />
          ) : (
            <>
              {/* Stats summary */}
              <StatsSummary instants={instants} stats={stats} />

              {/* Hero CTA */}
              {heroInstant && (
                <HeroInstant
                  instant={heroInstant}
                  onExploit={handleExploit}
                  isLoading={actionLoading === heroInstant.instant_id}
                />
              )}

              {/* All instants list */}
              <div>
                <h3 className="text-xs text-muted-foreground uppercase tracking-wider font-medium mb-3">
                  Tous les instants
                </h3>
                <div className="space-y-3">
                  {[heroInstant, ...otherInstants]
                    .filter(Boolean)
                    .map((instant) => (
                      <InstantCard
                        key={instant.instant_id}
                        instant={instant}
                        onExploit={handleExploit}
                        onSkip={handleSkip}
                        isLoading={actionLoading === instant.instant_id}
                      />
                    ))}
                </div>
              </div>

              {/* Link to full dashboard */}
              <Button
                variant="ghost"
                className="w-full text-muted-foreground hover:text-foreground gap-2"
                onClick={() => navigate("/progress")}
              >
                <Target className="w-4 h-4" />
                Voir le dashboard complet
                <ChevronRight className="w-4 h-4" />
              </Button>
            </>
          )}
        </div>
      </main>
    </div>
  );
}
