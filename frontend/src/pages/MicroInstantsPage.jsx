import React, { useState, useEffect, useCallback, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
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
  BarChart3,
  Award,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
  Undo2,
  Timer,
  BriefcaseBusiness,
  Clock3,
  Ban,
  MessageSquare,
} from "lucide-react";
import Sidebar from "@/components/Sidebar";
import { CardsSkeleton } from "@/components/PageSkeleton";
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

// ─── Skip reasons ────────────────────────────────────────────
const SKIP_REASONS = [
  { value: "busy", label: "Occupé en ce moment", icon: BriefcaseBusiness },
  { value: "wrong_time", label: "Mauvais moment", icon: Clock3 },
  { value: "not_interested", label: "Pas intéressé", icon: Ban },
  { value: "other", label: "Autre raison", icon: MessageSquare },
];

// ─── Skip Dialog ─────────────────────────────────────────────
function SkipDialog({ open, onOpenChange, onConfirm, isLoading }) {
  const [reason, setReason] = useState(null);

  const handleConfirm = () => {
    onConfirm(reason || "not_interested");
    setReason(null);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-sm">
        <DialogHeader>
          <DialogTitle className="text-base">Passer ce micro-instant ?</DialogTitle>
        </DialogHeader>
        <p className="text-sm text-muted-foreground -mt-1">
          Ton feedback améliore les prochaines prédictions.
        </p>
        <div className="grid grid-cols-2 gap-2 mt-2">
          {SKIP_REASONS.map((r) => {
            const Icon = r.icon;
            const selected = reason === r.value;
            return (
              <button
                key={r.value}
                onClick={() => setReason(r.value)}
                className={`flex items-center gap-2 p-2.5 rounded-lg border text-left text-sm transition-all ${
                  selected
                    ? "border-primary bg-primary/10 text-foreground"
                    : "border-border/40 text-muted-foreground hover:border-border hover:text-foreground"
                }`}
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span className="text-xs leading-tight">{r.label}</span>
              </button>
            );
          })}
        </div>
        <div className="flex gap-2 mt-3">
          <Button
            variant="ghost"
            className="flex-1"
            onClick={() => onOpenChange(false)}
          >
            Annuler
          </Button>
          <Button
            variant="default"
            className="flex-1"
            disabled={isLoading}
            onClick={handleConfirm}
          >
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Passer"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// ─── Countdown timer for active instants ─────────────────────
function CountdownBadge({ windowEnd }) {
  const [remaining, setRemaining] = useState("");

  useEffect(() => {
    function calc() {
      const diff = new Date(windowEnd) - new Date();
      if (diff <= 0) {
        setRemaining("");
        return;
      }
      const mins = Math.floor(diff / 60000);
      const secs = Math.floor((diff % 60000) / 1000);
      if (mins > 30) {
        setRemaining(`${mins} min`);
      } else {
        setRemaining(`${mins}:${secs.toString().padStart(2, "0")}`);
      }
    }
    calc();
    const id = setInterval(calc, 1000);
    return () => clearInterval(id);
  }, [windowEnd]);

  if (!remaining) return null;

  return (
    <Badge variant="outline" className="text-[10px] text-amber-400 border-amber-500/30 animate-pulse gap-1">
      <Timer className="w-3 h-3" />
      {remaining}
    </Badge>
  );
}

// ═══════════════════════════════════════════════════════════════
// Instant Card — the core interaction unit
// ═══════════════════════════════════════════════════════════════
function InstantCard({ instant, onExploit, onSkip, onUndoSkip, isLoading }) {
  const [skipDialogOpen, setSkipDialogOpen] = useState(false);
  const [undoCountdown, setUndoCountdown] = useState(0);
  const undoTimerRef = useRef(null);

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

  const handleSkipConfirm = (reason) => {
    setSkipDialogOpen(false);
    onSkip(instant.instant_id, reason);
    // Start undo countdown (5 seconds)
    setUndoCountdown(5);
    undoTimerRef.current = setInterval(() => {
      setUndoCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(undoTimerRef.current);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  const handleUndo = () => {
    clearInterval(undoTimerRef.current);
    setUndoCountdown(0);
    onUndoSkip(instant.instant_id);
  };

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (undoTimerRef.current) clearInterval(undoTimerRef.current);
    };
  }, []);

  return (
    <>
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
          <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
            <div className="flex items-center gap-2">
              <div className={`w-7 h-7 rounded-lg ${source.bgColor} flex items-center justify-center shrink-0`}>
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

            <div className="flex items-center gap-1.5 flex-wrap">
              {/* Countdown for active instants */}
              {now && <CountdownBadge windowEnd={instant.window_end} />}
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

          {/* Action buttons — active state */}
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
                onClick={() => setSkipDialogOpen(true)}
              >
                <SkipForward className="w-4 h-4" />
              </Button>
            </div>
          )}

          {/* Exploited state — enriched feedback */}
          {exploited && (
            <div className="flex items-center gap-3 p-2.5 rounded-lg bg-emerald-500/5 border border-emerald-500/20">
              <div className="w-8 h-8 rounded-full bg-emerald-500/20 flex items-center justify-center shrink-0">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-emerald-400">Exploité</p>
                {action.title && (
                  <p className="text-[11px] text-muted-foreground">{action.title}</p>
                )}
              </div>
            </div>
          )}

          {/* Skipped state — with undo option */}
          {skipped && (
            <div className="flex items-center gap-3 p-2.5 rounded-lg bg-muted/5 border border-border/20">
              <div className="w-8 h-8 rounded-full bg-muted/20 flex items-center justify-center shrink-0">
                <XCircle className="w-4 h-4 text-muted-foreground" />
              </div>
              <div className="flex-1">
                <p className="text-sm text-muted-foreground">Passé</p>
                {instant._skipReason && (
                  <p className="text-[11px] text-muted-foreground/60">
                    {SKIP_REASONS.find((r) => r.value === instant._skipReason)?.label || instant._skipReason}
                  </p>
                )}
              </div>
              {undoCountdown > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-xs text-primary hover:text-primary gap-1.5 shrink-0"
                  onClick={handleUndo}
                >
                  <Undo2 className="w-3.5 h-3.5" />
                  Annuler ({undoCountdown}s)
                </Button>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Skip confirmation dialog */}
      <SkipDialog
        open={skipDialogOpen}
        onOpenChange={setSkipDialogOpen}
        onConfirm={handleSkipConfirm}
        isLoading={isLoading}
      />
    </>
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
    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
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
// Analytics Dashboard — G.3
// ═══════════════════════════════════════════════════════════════

function WeeklyTrendBadge({ trend, thisWeekRate, lastWeekRate }) {
  if (thisWeekRate === 0 && lastWeekRate === 0) return null;
  const pct = Math.round(trend * 100);
  const isUp = pct > 0;
  const isFlat = pct === 0;
  const Icon = isUp ? ArrowUpRight : isFlat ? Minus : ArrowDownRight;
  const color = isUp
    ? "text-emerald-400 bg-emerald-500/10"
    : isFlat
    ? "text-muted-foreground bg-muted/10"
    : "text-red-400 bg-red-500/10";

  return (
    <div className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${color}`}>
      <Icon className="w-3 h-3" />
      {isUp ? "+" : ""}
      {pct}% vs semaine dernière
    </div>
  );
}

function DailyChart({ dailyChart }) {
  if (!dailyChart || dailyChart.length === 0) return null;
  const maxTotal = Math.max(...dailyChart.map((d) => d.total), 1);

  const dayNames = ["Dim", "Lun", "Mar", "Mer", "Jeu", "Ven", "Sam"];

  return (
    <Card className="border-border/30">
      <CardContent className="p-4">
        <div className="flex items-center gap-2 mb-4">
          <BarChart3 className="w-4 h-4 text-primary" />
          <span className="text-sm font-medium text-foreground">7 derniers jours</span>
        </div>
        <div className="flex items-end gap-1.5 h-28">
          {dailyChart.map((day) => {
            const dt = new Date(day.date + "T12:00:00");
            const dayName = dayNames[dt.getDay()];
            const dayNum = dt.getDate();
            const exploitedH = day.total > 0 ? (day.exploited / maxTotal) * 100 : 0;
            const skippedH = day.total > 0 ? (day.skipped / maxTotal) * 100 : 0;
            const rate = Math.round(day.rate * 100);

            return (
              <div key={day.date} className="flex-1 flex flex-col items-center gap-1 group relative">
                {/* Tooltip */}
                <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-popover border border-border rounded-md px-2 py-1 text-[10px] text-foreground whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10 shadow-md">
                  {day.exploited}/{day.total} · {rate}%
                </div>
                {/* Bars */}
                <div className="w-full flex flex-col justify-end h-20 gap-0.5">
                  {day.total === 0 ? (
                    <div className="w-full rounded-sm bg-muted/20" style={{ height: "4px" }} />
                  ) : (
                    <>
                      <div
                        className="w-full rounded-t-sm bg-emerald-500/70 transition-all"
                        style={{ height: `${Math.max(exploitedH, 4)}%` }}
                      />
                      {skippedH > 0 && (
                        <div
                          className="w-full bg-muted-foreground/20 transition-all"
                          style={{ height: `${skippedH}%` }}
                        />
                      )}
                    </>
                  )}
                </div>
                {/* Label */}
                <div className="text-center">
                  <p className="text-[10px] font-medium text-muted-foreground">{dayName}</p>
                  <p className="text-[9px] text-muted-foreground/60">{dayNum}</p>
                </div>
              </div>
            );
          })}
        </div>
        {/* Legend */}
        <div className="flex items-center gap-4 mt-3 justify-center">
          <div className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-sm bg-emerald-500/70" />
            <span className="text-[10px] text-muted-foreground">Exploités</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-sm bg-muted-foreground/20" />
            <span className="text-[10px] text-muted-foreground">Passés</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function HourlyHeatmap({ hourlyRates }) {
  if (!hourlyRates || Object.keys(hourlyRates).length === 0) return null;

  // Group hours into time blocks
  const blocks = [
    { label: "Matin", range: [6, 12], icon: Sunrise },
    { label: "Après-midi", range: [12, 18], icon: Sun },
    { label: "Soir", range: [18, 24], icon: Moon },
  ];

  return (
    <Card className="border-border/30">
      <CardContent className="p-4">
        <div className="flex items-center gap-2 mb-4">
          <Clock className="w-4 h-4 text-primary" />
          <span className="text-sm font-medium text-foreground">Heures d'exploitation</span>
        </div>
        <div className="space-y-3">
          {blocks.map((block) => {
            const BlockIcon = block.icon;
            return (
              <div key={block.label}>
                <div className="flex items-center gap-1.5 mb-1.5">
                  <BlockIcon className="w-3 h-3 text-muted-foreground" />
                  <span className="text-[11px] text-muted-foreground">{block.label}</span>
                </div>
                <div className="grid grid-cols-3 sm:grid-cols-6 gap-1">
                  {Array.from({ length: block.range[1] - block.range[0] }, (_, i) => {
                    const h = block.range[0] + i;
                    const data = hourlyRates[String(h)];
                    const rate = data ? data.rate : 0;
                    const total = data ? data.total : 0;

                    // Intensity based on rate
                    let bg = "bg-muted/20";
                    if (total > 0) {
                      if (rate >= 0.7) bg = "bg-emerald-500/70";
                      else if (rate >= 0.4) bg = "bg-emerald-500/40";
                      else if (rate > 0) bg = "bg-emerald-500/20";
                      else bg = "bg-red-500/15";
                    }

                    return (
                      <div
                        key={h}
                        className={`group relative h-7 rounded-md ${bg} flex items-center justify-center transition-all hover:ring-1 hover:ring-primary/30 cursor-default`}
                      >
                        <span className="text-[9px] font-medium text-foreground/60">{h}h</span>
                        {total > 0 && (
                          <div className="absolute -top-7 left-1/2 -translate-x-1/2 bg-popover border border-border rounded-md px-2 py-0.5 text-[10px] text-foreground whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10 shadow-md">
                            {Math.round(rate * 100)}% ({data.exploited}/{total})
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
        {/* Heatmap legend */}
        <div className="flex items-center gap-1.5 mt-3 justify-center">
          <span className="text-[9px] text-muted-foreground">0%</span>
          <div className="flex gap-0.5">
            <div className="w-4 h-2.5 rounded-sm bg-muted/20" />
            <div className="w-4 h-2.5 rounded-sm bg-emerald-500/20" />
            <div className="w-4 h-2.5 rounded-sm bg-emerald-500/40" />
            <div className="w-4 h-2.5 rounded-sm bg-emerald-500/70" />
          </div>
          <span className="text-[9px] text-muted-foreground">100%</span>
        </div>
      </CardContent>
    </Card>
  );
}

function BestSlotsCard({ bestSlots }) {
  if (!bestSlots || bestSlots.length === 0) return null;

  const medals = ["🥇", "🥈", "🥉"];

  return (
    <Card className="border-border/30">
      <CardContent className="p-4">
        <div className="flex items-center gap-2 mb-3">
          <Award className="w-4 h-4 text-amber-400" />
          <span className="text-sm font-medium text-foreground">Meilleurs créneaux</span>
        </div>
        <div className="space-y-2">
          {bestSlots.map((slot, i) => (
            <div
              key={slot.hour}
              className="flex items-center gap-3 p-2.5 rounded-lg bg-card/50 border border-border/20"
            >
              <span className="text-lg">{medals[i]}</span>
              <div className="flex-1">
                <p className="text-sm font-medium text-foreground">{slot.label}</p>
                <p className="text-[11px] text-muted-foreground">
                  {slot.exploited_count}/{slot.total_outcomes} exploités
                </p>
              </div>
              <Badge
                className={`text-xs ${
                  slot.exploitation_rate >= 0.7
                    ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                    : slot.exploitation_rate >= 0.4
                    ? "bg-amber-500/20 text-amber-400 border-amber-500/30"
                    : "text-muted-foreground border-border/50"
                }`}
                variant="outline"
              >
                {Math.round(slot.exploitation_rate * 100)}%
              </Badge>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function SourceBreakdown({ sourceDistribution }) {
  if (!sourceDistribution) return null;
  const sources = Object.entries(sourceDistribution).filter(([, d]) => d.total > 0);
  if (sources.length === 0) return null;

  const totalAll = sources.reduce((s, [, d]) => s + d.total, 0);

  return (
    <Card className="border-border/30">
      <CardContent className="p-4">
        <div className="flex items-center gap-2 mb-3">
          <Sparkles className="w-4 h-4 text-primary" />
          <span className="text-sm font-medium text-foreground">Sources de détection</span>
        </div>
        <div className="space-y-3">
          {sources.map(([src, data]) => {
            const config = SOURCE_CONFIG[src] || SOURCE_CONFIG.behavioral_pattern;
            const SrcIcon = config.icon;
            const pct = totalAll > 0 ? Math.round((data.total / totalAll) * 100) : 0;
            const rate = Math.round(data.rate * 100);

            return (
              <div key={src}>
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <div className={`w-6 h-6 rounded-md ${config.bgColor} flex items-center justify-center`}>
                      <SrcIcon className={`w-3 h-3 ${config.color}`} />
                    </div>
                    <span className="text-sm text-foreground">{config.label}</span>
                  </div>
                  <div className="text-right">
                    <span className="text-xs text-muted-foreground">{pct}%</span>
                    <span className="text-[10px] text-muted-foreground/60 ml-1">
                      ({rate}% exploités)
                    </span>
                  </div>
                </div>
                <div className="h-1.5 rounded-full bg-muted/30 overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${
                      src === "calendar_gap"
                        ? "bg-blue-500/60"
                        : src === "routine_window"
                        ? "bg-emerald-500/60"
                        : "bg-purple-500/60"
                    }`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

function StreakConsistencyCard({ streak, avgPerDay, activeDays, totalMinutes }) {
  return (
    <Card className="border-border/30">
      <CardContent className="p-4">
        <div className="grid grid-cols-2 gap-3">
          <div className="text-center p-3 rounded-xl bg-gradient-to-br from-amber-500/10 to-orange-500/10 border border-amber-500/20">
            <Flame className="w-5 h-5 text-amber-400 mx-auto mb-1" />
            <p className="text-2xl font-bold text-foreground">{streak}</p>
            <p className="text-[10px] text-muted-foreground">Jours consécutifs</p>
          </div>
          <div className="text-center p-3 rounded-xl bg-card border border-border/20">
            <Target className="w-5 h-5 text-primary mx-auto mb-1" />
            <p className="text-2xl font-bold text-foreground">{avgPerDay}</p>
            <p className="text-[10px] text-muted-foreground">Moy. / jour actif</p>
          </div>
          <div className="text-center p-3 rounded-xl bg-card border border-border/20">
            <Calendar className="w-5 h-5 text-blue-400 mx-auto mb-1" />
            <p className="text-2xl font-bold text-foreground">{activeDays}</p>
            <p className="text-[10px] text-muted-foreground">Jours actifs (30j)</p>
          </div>
          <div className="text-center p-3 rounded-xl bg-card border border-border/20">
            <Clock className="w-5 h-5 text-emerald-400 mx-auto mb-1" />
            <p className="text-2xl font-bold text-foreground">{formatDuration(totalMinutes)}</p>
            <p className="text-[10px] text-muted-foreground">Temps investi</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function AnalyticsDashboard() {
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const res = await authFetch(`${API}/micro-instants/dashboard`);
        if (res.ok) {
          setDashboard(await res.json());
        }
      } catch {
        /* silent */
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!dashboard || dashboard.total_instants === 0) return null;

  const summaryRate = Math.round(dashboard.exploitation_rate * 100);

  return (
    <div className="space-y-4">
      {/* Analytics header + toggle */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-3 rounded-xl bg-card border border-border/30 hover:border-primary/20 transition-colors group"
      >
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center">
            <BarChart3 className="w-4.5 h-4.5 text-primary" />
          </div>
          <div className="text-left">
            <p className="text-sm font-medium text-foreground">Analytics (30 jours)</p>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="text-xs text-muted-foreground">
                {dashboard.total_instants} instants · {summaryRate}% exploités
              </span>
              <WeeklyTrendBadge
                trend={dashboard.weekly_trend}
                thisWeekRate={dashboard.this_week_rate}
                lastWeekRate={dashboard.last_week_rate}
              />
            </div>
          </div>
        </div>
        <ChevronRight
          className={`w-4 h-4 text-muted-foreground transition-transform ${
            expanded ? "rotate-90" : ""
          }`}
        />
      </button>

      {expanded && (
        <div className="space-y-4 animate-in fade-in slide-in-from-top-2 duration-300">
          {/* Streak & consistency */}
          <StreakConsistencyCard
            streak={dashboard.exploit_streak_days}
            avgPerDay={dashboard.avg_instants_per_active_day}
            activeDays={dashboard.active_days_count}
            totalMinutes={dashboard.total_minutes_invested}
          />

          {/* 7-day chart */}
          <DailyChart dailyChart={dashboard.daily_chart} />

          {/* Hourly heatmap */}
          <HourlyHeatmap hourlyRates={dashboard.hourly_rates} />

          {/* Best slots + Source breakdown side by side on desktop */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <BestSlotsCard bestSlots={dashboard.best_slots} />
            <SourceBreakdown sourceDistribution={dashboard.source_distribution} />
          </div>
        </div>
      )}
    </div>
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
        setInstants((prev) =>
          prev.map((i) =>
            i.instant_id === instantId ? { ...i, _exploited: true } : i
          )
        );
        // Enriched success feedback
        const actionTitle = data.action?.title || "Action lancée";
        toast.success(`${actionTitle}`, {
          description: "Micro-instant exploité — bravo !",
        });

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

  // ── Skip action (with reason from dialog) ──
  const handleSkip = async (instantId, reason) => {
    setActionLoading(instantId);
    try {
      const res = await authFetch(`${API}/micro-instants/${instantId}/skip`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason }),
      });

      if (res.ok) {
        setInstants((prev) =>
          prev.map((i) =>
            i.instant_id === instantId
              ? { ...i, _skipped: true, _skipReason: reason }
              : i
          )
        );
      }
    } catch {
      /* silent */
    } finally {
      setActionLoading(null);
    }
  };

  // ── Undo skip (local only — reverts optimistic state) ──
  const handleUndoSkip = (instantId) => {
    setInstants((prev) =>
      prev.map((i) =>
        i.instant_id === instantId
          ? { ...i, _skipped: false, _skipReason: null }
          : i
      )
    );
    toast("Micro-instant restauré", { description: "Tu peux encore l'exploiter." });
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
            <CardsSkeleton count={3} />
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
                        onUndoSkip={handleUndoSkip}
                        isLoading={actionLoading === instant.instant_id}
                      />
                    ))}
                </div>
              </div>

              {/* Analytics Dashboard — G.3 */}
              <AnalyticsDashboard />
            </>
          )}
        </div>
      </main>
    </div>
  );
}
