import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Sunrise,
  Sun,
  Moon,
  Clock,
  Flame,
  CheckCircle2,
  ChevronRight,
  Target,
  CalendarClock,
  Play,
  Loader2,
  Sparkles,
  Trophy,
  Zap,
  Timer,
  Calendar,
  Repeat,
  TrendingUp,
  SkipForward,
} from "lucide-react";
import Sidebar from "@/components/Sidebar";
import { API, authFetch, useAuth } from "@/App";
import { toast } from "sonner";

// ─── Time of day helpers ──────────────────────────────────
const TIME_SECTIONS = [
  { key: "morning", label: "Matin", icon: Sunrise, color: "text-amber-500", bgColor: "bg-amber-500/10" },
  { key: "afternoon", label: "Après-midi", icon: Sun, color: "text-orange-500", bgColor: "bg-orange-500/10" },
  { key: "evening", label: "Soir", icon: Moon, color: "text-indigo-500", bgColor: "bg-indigo-500/10" },
];

function getCurrentTimeOfDay() {
  const h = new Date().getHours();
  if (h < 12) return "morning";
  if (h < 18) return "afternoon";
  return "evening";
}

function getGreeting(name) {
  const h = new Date().getHours();
  const first = name?.split(" ")[0] || "";
  if (h < 12) return `Bonjour${first ? ` ${first}` : ""} !`;
  if (h < 18) return `Bon après-midi${first ? ` ${first}` : ""} !`;
  return `Bonsoir${first ? ` ${first}` : ""} !`;
}

function formatDate() {
  return new Date().toLocaleDateString("fr-FR", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });
}

function todayISO() {
  return new Date().toISOString().slice(0, 10);
}

// ─── Smart CTAs — contextual actions based on day state ───
function SmartCTAs({ routines, objectives, routinesCompletedToday, todaySessions, navigate }) {
  const allRoutinesDone = routines.length > 0 && routinesCompletedToday.length >= routines.length;
  const hasRoutines = routines.length > 0;
  const hasObjectives = objectives.length > 0;
  const currentTod = getCurrentTimeOfDay();

  // Find the next undone routine for current time of day
  const today = todayISO();
  const nextRoutine = routines.find(
    (r) =>
      !r.last_completed_at?.startsWith(today) &&
      (r.time_of_day === currentTod || r.time_of_day === "anytime")
  ) || routines.find((r) => !r.last_completed_at?.startsWith(today));

  // Find the objective with most momentum (highest streak or most recent activity)
  const priorityObjective = objectives.length > 0
    ? [...objectives].sort((a, b) => (b.streak_days || 0) - (a.streak_days || 0))[0]
    : null;

  // ── Determine smart actions ──────────────
  const actions = [];

  if (allRoutinesDone && todaySessions.length > 0) {
    // Everything done — celebrate
    actions.push({
      label: "Voir ma progression",
      icon: Trophy,
      variant: "default",
      className: "bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white border-0",
      onClick: () => navigate("/progress"),
    });
    if (priorityObjective?.nextStep) {
      actions.push({
        label: `Bonus : ${priorityObjective.nextStep.title}`,
        sublabel: priorityObjective.title,
        icon: Sparkles,
        variant: "outline",
        className: "border-primary/30 text-primary hover:bg-primary/10",
        onClick: () => navigate(`/objectives/${priorityObjective.objective_id}`),
      });
    }
  } else if (!hasRoutines && !hasObjectives) {
    // Nothing set up
    actions.push({
      label: "Créer mon premier objectif",
      icon: Target,
      variant: "default",
      onClick: () => navigate("/objectives"),
    });
    actions.push({
      label: "Créer une routine",
      icon: CalendarClock,
      variant: "outline",
      onClick: () => navigate("/routines"),
    });
  } else {
    // Normal day — smart next action
    if (nextRoutine) {
      actions.push({
        label: `Lancer : ${nextRoutine.name}`,
        sublabel: `${nextRoutine.total_minutes || 0} min · ${(nextRoutine.items || []).length} actions`,
        icon: Play,
        variant: "default",
        onClick: () => navigate("/routines"),
      });
    } else if (!hasRoutines) {
      actions.push({
        label: "Planifier des routines",
        icon: CalendarClock,
        variant: "outline",
        className: "border-primary/30",
        onClick: () => navigate("/routines"),
      });
    }

    if (priorityObjective?.nextStep) {
      actions.push({
        label: `Continuer : ${priorityObjective.title}`,
        sublabel: `Prochaine session — ${priorityObjective.nextStep.title}`,
        icon: Target,
        variant: nextRoutine ? "outline" : "default",
        className: nextRoutine ? "border-primary/30" : "",
        onClick: () => navigate(`/objectives/${priorityObjective.objective_id}`),
      });
    } else if (!hasObjectives) {
      actions.push({
        label: "Définir un objectif",
        icon: Target,
        variant: "outline",
        className: "border-primary/30",
        onClick: () => navigate("/objectives"),
      });
    }
  }

  if (actions.length === 0) return null;

  return (
    <div className="mt-8 pt-5 border-t border-border/30">
      <p className="text-[11px] text-muted-foreground uppercase tracking-wider font-medium mb-3 text-center">
        {allRoutinesDone && todaySessions.length > 0
          ? "Journée accomplie"
          : "Prochaine action recommandée"}
      </p>
      <div className="space-y-2">
        {actions.map((action, i) => {
          const Icon = action.icon;
          return (
            <Button
              key={i}
              variant={action.variant}
              className={`w-full h-auto py-3 px-4 justify-start gap-3 ${action.className || ""}`}
              onClick={action.onClick}
            >
              <div className="w-9 h-9 rounded-xl bg-background/20 flex items-center justify-center shrink-0">
                <Icon className="w-5 h-5" />
              </div>
              <div className="text-left flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{action.label}</p>
                {action.sublabel && (
                  <p className="text-[11px] opacity-70 truncate">{action.sublabel}</p>
                )}
              </div>
              <ChevronRight className="w-4 h-4 opacity-50 shrink-0" />
            </Button>
          );
        })}
      </div>
    </div>
  );
}

// ─── Micro-Instants Section ───────────────────────────────
const MI_SOURCE_CONFIG = {
  calendar_gap: { icon: Calendar, label: "Calendrier", color: "text-blue-400", bgColor: "bg-blue-500/10" },
  routine_window: { icon: Repeat, label: "Routine", color: "text-emerald-400", bgColor: "bg-emerald-500/10" },
  behavioral_pattern: { icon: TrendingUp, label: "Pattern", color: "text-purple-400", bgColor: "bg-purple-500/10" },
};

function formatInstantTime(isoString) {
  if (!isoString) return "";
  return new Date(isoString).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
}

function isInstantActive(instant) {
  const now = new Date();
  return now >= new Date(instant.window_start) && now <= new Date(instant.window_end);
}

function isInstantPast(instant) {
  return new Date() > new Date(instant.window_end);
}

function MicroInstantsSection({ instants, onExploit, onSkip, loadingId, navigate }) {
  // Only show active (now) or future instants that haven't been acted on
  const visible = instants.filter(
    (i) => !i._exploited && !i._skipped && !isInstantPast(i)
  );
  const acted = instants.filter((i) => i._exploited);

  if (visible.length === 0 && acted.length === 0) return null;

  return (
    <div className="mb-6">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Timer className="w-5 h-5 text-primary" />
          <h2 className="text-sm font-semibold">Micro-instants</h2>
          {visible.length > 0 && (
            <Badge className="text-[9px] bg-primary/10 text-primary border-primary/20 h-4 px-1.5">
              {visible.length} dispo
            </Badge>
          )}
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="text-xs text-muted-foreground h-7 gap-1"
          onClick={() => navigate("/micro-instants")}
        >
          Tout voir
          <ChevronRight className="w-3 h-3" />
        </Button>
      </div>

      <div className="space-y-2">
        {visible.slice(0, 3).map((instant) => {
          const source = MI_SOURCE_CONFIG[instant.source] || MI_SOURCE_CONFIG.behavioral_pattern;
          const SourceIcon = source.icon;
          const action = instant.recommended_action || {};
          const isNow = isInstantActive(instant);

          return (
            <Card
              key={instant.instant_id}
              className={`p-3.5 transition-all ${
                isNow
                  ? "border-primary/40 shadow-md shadow-primary/5 ring-1 ring-primary/15"
                  : "hover:border-primary/30"
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <div className={`w-8 h-8 rounded-lg ${source.bgColor} flex items-center justify-center shrink-0`}>
                    <SourceIcon className={`w-4 h-4 ${source.color}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5">
                      <p className="text-sm font-medium truncate">
                        {action.title || "Action recommandée"}
                      </p>
                      {isNow && (
                        <Badge className="bg-primary/20 text-primary text-[8px] px-1 py-0 shrink-0 animate-pulse">
                          NOW
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground mt-0.5">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatInstantTime(instant.window_start)} – {formatInstantTime(instant.window_end)}
                      </span>
                      {instant.duration_minutes && (
                        <span>{instant.duration_minutes} min</span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-1.5 shrink-0 ml-2">
                  <Button
                    size="sm"
                    className={`h-8 text-xs gap-1 ${isNow ? "bg-primary shadow-sm" : ""}`}
                    variant={isNow ? "default" : "outline"}
                    disabled={loadingId === instant.instant_id || !action.action_id}
                    onClick={() => onExploit(instant.instant_id, action.action_id)}
                  >
                    {loadingId === instant.instant_id ? (
                      <Loader2 className="w-3 h-3 animate-spin" />
                    ) : (
                      <Play className="w-3 h-3" />
                    )}
                    Go
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    className="h-8 w-8 p-0 text-muted-foreground"
                    disabled={loadingId === instant.instant_id}
                    onClick={() => onSkip(instant.instant_id)}
                  >
                    <SkipForward className="w-3.5 h-3.5" />
                  </Button>
                </div>
              </div>
            </Card>
          );
        })}

        {/* Exploited count */}
        {acted.length > 0 && (
          <p className="text-[11px] text-emerald-500 flex items-center gap-1 pl-1 pt-1">
            <CheckCircle2 className="w-3 h-3" />
            {acted.length} micro-instant{acted.length > 1 ? "s" : ""} exploité{acted.length > 1 ? "s" : ""} aujourd'hui
          </p>
        )}
      </div>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────
export default function MyDayPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [routines, setRoutines] = useState([]);
  const [objectives, setObjectives] = useState([]);
  const [stats, setStats] = useState(null);
  const [microInstants, setMicroInstants] = useState([]);
  const [miActionLoading, setMiActionLoading] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const loadData = useCallback(async () => {
    try {
      const [routinesRes, objectivesRes, statsRes, miRes] = await Promise.all([
        authFetch(`${API}/routines`),
        authFetch(`${API}/objectives`),
        authFetch(`${API}/stats`),
        authFetch(`${API}/micro-instants/today`),
      ]);

      if (routinesRes.ok) {
        const data = await routinesRes.json();
        setRoutines((data.routines || []).filter((r) => r.is_active));
      }
      if (objectivesRes.ok) {
        const data = await objectivesRes.json();
        setObjectives((data.objectives || []).filter((o) => o.status === "active"));
      }
      if (statsRes.ok) {
        const data = await statsRes.json();
        setStats(data);
      }
      if (miRes.ok) {
        const data = await miRes.json();
        setMicroInstants(data.instants || []);
      }
    } catch {
      toast.error("Erreur de chargement");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  // ── Complete routine ─────────────────────────
  const handleCompleteRoutine = async (routine) => {
    try {
      const res = await authFetch(`${API}/routines/${routine.routine_id}/complete`, {
        method: "POST",
      });
      if (res.ok) {
        setRoutines((prev) =>
          prev.map((r) =>
            r.routine_id === routine.routine_id
              ? { ...r, times_completed: (r.times_completed || 0) + 1, last_completed_at: new Date().toISOString() }
              : r
          )
        );
        toast.success("Routine complétée !");
      }
    } catch {
      toast.error("Erreur");
    }
  };

  // ── Micro-instant handlers ──────────────────
  const handleMiExploit = async (instantId, actionId) => {
    setMiActionLoading(instantId);
    try {
      const res = await authFetch(`${API}/micro-instants/${instantId}/exploit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action_id: actionId }),
      });
      if (res.ok) {
        setMicroInstants((prev) =>
          prev.map((i) => i.instant_id === instantId ? { ...i, _exploited: true } : i)
        );
        toast.success("Micro-instant exploité !");
      }
    } catch {
      toast.error("Erreur réseau");
    } finally {
      setMiActionLoading(null);
    }
  };

  const handleMiSkip = async (instantId) => {
    setMiActionLoading(instantId);
    try {
      await authFetch(`${API}/micro-instants/${instantId}/skip`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason: "not_interested" }),
      });
      setMicroInstants((prev) =>
        prev.map((i) => i.instant_id === instantId ? { ...i, _skipped: true } : i)
      );
    } catch { /* silent */ }
    finally { setMiActionLoading(null); }
  };

  // ── Computed data ────────────────────────────
  const today = todayISO();
  const currentTod = getCurrentTimeOfDay();

  // Sessions completed today from recent_sessions
  const todaySessions = (stats?.recent_sessions || []).filter(
    (s) => s.completed && s.completed_at?.startsWith(today)
  );
  const todayMinutes = todaySessions.reduce((sum, s) => sum + (s.actual_duration || 0), 0);

  // Routines completed today
  const routinesCompletedToday = routines.filter(
    (r) => r.last_completed_at?.startsWith(today)
  );

  // Group routines by time of day
  const routinesByTime = {
    morning: routines.filter((r) => r.time_of_day === "morning" || r.time_of_day === "anytime"),
    afternoon: routines.filter((r) => r.time_of_day === "afternoon"),
    evening: routines.filter((r) => r.time_of_day === "evening"),
  };

  // Total planned minutes
  const totalPlannedMin = routines.reduce((s, r) => s + (r.total_minutes || 0), 0);

  // Next objective steps
  const objectivesWithNext = objectives.map((obj) => {
    const curriculum = obj.curriculum || [];
    const nextStep = curriculum.find((s) => !s.completed);
    const completedSteps = curriculum.filter((s) => s.completed).length;
    const percent = curriculum.length > 0 ? Math.round((completedSteps / curriculum.length) * 100) : 0;
    return { ...obj, nextStep, completedSteps, totalSteps: curriculum.length, percent };
  });

  const hasContent = routines.length > 0 || objectives.length > 0;

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <main className="lg:ml-16 pb-20">
        <div className="max-w-2xl mx-auto px-4 py-6">
          {/* Header */}
          <div className="mb-6">
            <h1 className="font-heading text-2xl font-bold">
              {getGreeting(user?.name)}
            </h1>
            <p className="text-sm text-muted-foreground mt-0.5 capitalize">
              {formatDate()}
            </p>
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : !hasContent ? (
            /* Empty state */
            <Card className="p-8 text-center">
              <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center mx-auto mb-4 ring-1 ring-primary/10">
                <Zap className="w-10 h-10 text-primary" />
              </div>
              <h3 className="font-heading font-semibold text-lg mb-2">
                Ta journée est vide
              </h3>
              <p className="text-sm text-muted-foreground mb-6 max-w-sm mx-auto leading-relaxed">
                Crée un objectif ou une routine pour structurer ta journée et suivre tes micro-avancements.
              </p>
              <div className="flex items-center justify-center gap-3">
                <Button onClick={() => navigate("/objectives")} variant="outline" className="gap-2">
                  <Target className="w-4 h-4" />
                  Objectifs
                </Button>
                <Button onClick={() => navigate("/routines")} className="gap-2">
                  <CalendarClock className="w-4 h-4" />
                  Routines
                </Button>
              </div>
            </Card>
          ) : (
            <>
              {/* ── Stats du jour ─────────────────── */}
              <div className="grid grid-cols-3 gap-3 mb-6">
                <Card className="p-3 text-center">
                  <div className="flex items-center justify-center gap-1.5 mb-1">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                  </div>
                  <p className="text-xl font-bold tabular-nums">{todaySessions.length}</p>
                  <p className="text-[10px] text-muted-foreground">Sessions</p>
                </Card>
                <Card className="p-3 text-center">
                  <div className="flex items-center justify-center gap-1.5 mb-1">
                    <Clock className="w-4 h-4 text-blue-500" />
                  </div>
                  <p className="text-xl font-bold tabular-nums">{todayMinutes}</p>
                  <p className="text-[10px] text-muted-foreground">Minutes</p>
                </Card>
                <Card className="p-3 text-center">
                  <div className="flex items-center justify-center gap-1.5 mb-1">
                    <Flame className="w-4 h-4 text-orange-500" />
                  </div>
                  <p className="text-xl font-bold tabular-nums">{stats?.streak_days || 0}</p>
                  <p className="text-[10px] text-muted-foreground">Streak</p>
                </Card>
              </div>

              {/* ── Micro-instants disponibles ──────── */}
              <MicroInstantsSection
                instants={microInstants}
                onExploit={handleMiExploit}
                onSkip={handleMiSkip}
                loadingId={miActionLoading}
                navigate={navigate}
              />

              {/* ── Progression du jour ───────────── */}
              {totalPlannedMin > 0 && (
                <Card className="p-4 mb-6">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">Progression du jour</span>
                    <span className="text-xs text-muted-foreground">
                      {routinesCompletedToday.length}/{routines.length} routines
                    </span>
                  </div>
                  <Progress
                    value={routines.length > 0 ? Math.round((routinesCompletedToday.length / routines.length) * 100) : 0}
                    className="h-2.5"
                  />
                  <div className="flex items-center justify-between mt-1.5 text-[11px] text-muted-foreground">
                    <span>{todayMinutes} min investies</span>
                    <span>{totalPlannedMin} min planifiées</span>
                  </div>
                </Card>
              )}

              {/* ── Timeline par moment ───────────── */}
              <div className="space-y-5 mb-6">
                {TIME_SECTIONS.map((section) => {
                  const sectionRoutines = routinesByTime[section.key] || [];
                  if (sectionRoutines.length === 0) return null;

                  const SectionIcon = section.icon;
                  const isCurrent = currentTod === section.key;

                  return (
                    <div key={section.key}>
                      <div className="flex items-center gap-2 mb-2.5">
                        <div className={`w-7 h-7 rounded-lg ${section.bgColor} flex items-center justify-center`}>
                          <SectionIcon className={`w-4 h-4 ${section.color}`} />
                        </div>
                        <h2 className="text-sm font-semibold">{section.label}</h2>
                        {isCurrent && (
                          <Badge className="text-[9px] bg-primary/10 text-primary border-primary/20 h-4 px-1.5">
                            Maintenant
                          </Badge>
                        )}
                      </div>

                      <div className="space-y-2 pl-3 border-l-2 border-border/50 ml-3.5">
                        {sectionRoutines.map((routine) => {
                          const isDoneToday = routine.last_completed_at?.startsWith(today);
                          return (
                            <Card
                              key={routine.routine_id}
                              className={`p-3.5 transition-all ${isDoneToday ? "opacity-60 bg-muted/20" : "hover:border-primary/30"}`}
                            >
                              <div className="flex items-center justify-between">
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-2">
                                    {isDoneToday && <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />}
                                    <h3 className={`font-medium text-sm truncate ${isDoneToday ? "line-through text-muted-foreground" : ""}`}>
                                      {routine.name}
                                    </h3>
                                  </div>
                                  <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                                    <span className="flex items-center gap-1">
                                      <Clock className="w-3 h-3" />
                                      {routine.total_minutes || 0} min
                                    </span>
                                    <span className="flex items-center gap-1">
                                      <Play className="w-3 h-3" />
                                      {(routine.items || []).length} actions
                                    </span>
                                  </div>
                                </div>

                                {!isDoneToday ? (
                                  <Button
                                    size="sm"
                                    className="h-8 text-xs gap-1.5 shrink-0"
                                    onClick={() => handleCompleteRoutine(routine)}
                                  >
                                    <CheckCircle2 className="w-3.5 h-3.5" />
                                    Fait
                                  </Button>
                                ) : (
                                  <Badge variant="outline" className="text-[10px] bg-emerald-500/10 text-emerald-500 border-emerald-500/20 shrink-0">
                                    Complétée
                                  </Badge>
                                )}
                              </div>

                              {/* Items preview (collapsed) */}
                              {!isDoneToday && (routine.items || []).length > 0 && (
                                <div className="mt-2 pt-2 border-t border-border/50 space-y-1">
                                  {(routine.items || []).slice(0, 3).map((item, i) => (
                                    <div key={i} className="flex items-center gap-2 text-xs text-muted-foreground">
                                      <span className="w-4 h-4 rounded bg-muted/50 flex items-center justify-center text-[9px] font-bold shrink-0">
                                        {i + 1}
                                      </span>
                                      <span className="truncate">{item.title}</span>
                                      <span className="shrink-0 ml-auto">{item.duration_minutes} min</span>
                                    </div>
                                  ))}
                                  {(routine.items || []).length > 3 && (
                                    <p className="text-[10px] text-muted-foreground/60 pl-6">
                                      +{(routine.items || []).length - 3} autres
                                    </p>
                                  )}
                                </div>
                              )}
                            </Card>
                          );
                        })}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* ── Objectifs actifs ──────────────── */}
              {objectivesWithNext.length > 0 && (
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <Target className="w-5 h-5 text-primary" />
                    <h2 className="text-sm font-semibold">Mes objectifs en cours</h2>
                  </div>

                  <div className="space-y-2.5">
                    {objectivesWithNext.map((obj) => (
                      <Card
                        key={obj.objective_id}
                        className="p-4 cursor-pointer hover:border-primary/30 transition-all group"
                        onClick={() => navigate(`/objectives/${obj.objective_id}`)}
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex-1 min-w-0">
                            <h3 className="font-medium text-sm truncate group-hover:text-primary transition-colors">
                              {obj.title}
                            </h3>
                            <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                              <span>Jour {obj.current_day || 0}/{obj.target_duration_days}</span>
                              <span className="flex items-center gap-1">
                                <Flame className="w-3 h-3 text-orange-500" />
                                {obj.streak_days || 0}j
                              </span>
                            </div>
                          </div>
                          <ChevronRight className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors shrink-0 mt-1" />
                        </div>

                        {/* Progress */}
                        <div className="mb-2">
                          <div className="flex items-center justify-between text-[11px] text-muted-foreground mb-1">
                            <span>{obj.completedSteps}/{obj.totalSteps} sessions</span>
                            <span className="font-medium">{obj.percent}%</span>
                          </div>
                          <Progress value={obj.percent} className="h-1.5" />
                        </div>

                        {/* Next step */}
                        {obj.nextStep && (
                          <div className="flex items-center gap-2 p-2 rounded-lg bg-primary/5 border border-primary/10">
                            <Sparkles className="w-3.5 h-3.5 text-primary shrink-0" />
                            <div className="flex-1 min-w-0">
                              <p className="text-[11px] text-muted-foreground">Prochaine session</p>
                              <p className="text-xs font-medium truncate">{obj.nextStep.title}</p>
                            </div>
                            <Button
                              size="sm"
                              variant="ghost"
                              className="h-7 text-xs text-primary hover:bg-primary/10 shrink-0"
                              onClick={(e) => {
                                e.stopPropagation();
                                navigate(`/objectives/${obj.objective_id}`);
                              }}
                            >
                              Lancer
                            </Button>
                          </div>
                        )}
                      </Card>
                    ))}
                  </div>
                </div>
              )}

              {/* ── Smart CTAs — contextual based on day state ─── */}
              <SmartCTAs
                routines={routines}
                objectives={objectivesWithNext}
                routinesCompletedToday={routinesCompletedToday}
                todaySessions={todaySessions}
                navigate={navigate}
              />
            </>
          )}
        </div>
      </main>
    </div>
  );
}
