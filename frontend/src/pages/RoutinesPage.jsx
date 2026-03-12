import React, { useState, useEffect, useCallback, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  CalendarClock,
  Plus,
  Clock,
  Sunrise,
  Sun,
  Moon,
  Infinity,
  Trash2,
  Pencil,
  CheckCircle2,
  ToggleLeft,
  ToggleRight,
  Loader2,
  GripVertical,
  X,
  Trophy,
  Flame,
  Play,
  Repeat,
  Calendar,
  ChevronRight,
  Sparkles,
  Timer,
  SkipForward,
  CalendarPlus,
} from "lucide-react";
import Sidebar from "@/components/Sidebar";
import { VoiceTextArea } from "@/components/VoiceInput";
import { API, authFetch, useAuth } from "@/App";
import { toast } from "sonner";

// ─── Constants ──────────────────────────────────────────
const TIME_OF_DAY = [
  { value: "morning", label: "Matin", icon: Sunrise, color: "text-amber-500 bg-amber-500/10 border-amber-500/20" },
  { value: "afternoon", label: "Après-midi", icon: Sun, color: "text-orange-500 bg-orange-500/10 border-orange-500/20" },
  { value: "evening", label: "Soir", icon: Moon, color: "text-indigo-500 bg-indigo-500/10 border-indigo-500/20" },
  { value: "anytime", label: "Flexible", icon: Infinity, color: "text-emerald-500 bg-emerald-500/10 border-emerald-500/20" },
];

const FREQUENCY_OPTIONS = [
  { value: "daily", label: "Chaque jour", short: "Quotidien" },
  { value: "weekdays", label: "Semaine (Lun-Ven)", short: "Semaine" },
  { value: "weekends", label: "Week-end (Sam-Dim)", short: "Week-end" },
  { value: "custom", label: "Jours spécifiques", short: "Personnalisé" },
];

const DAY_LABELS = ["L", "M", "M", "J", "V", "S", "D"];

function timeLabel(tod) {
  return TIME_OF_DAY.find((t) => t.value === tod) || TIME_OF_DAY[0];
}

function freqLabel(freq) {
  return FREQUENCY_OPTIONS.find((f) => f.value === freq)?.short || "Quotidien";
}

// ─── Duration Scroll Picker ─────────────────────────────
function DurationPicker({ value, onChange, className = "" }) {
  const handleWheel = (e) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? -1 : 1;
    const next = Math.max(1, Math.min(120, value + delta));
    if (next !== value) {
      onChange(next);
      if (navigator.vibrate) navigator.vibrate(8);
    }
  };

  const touchRef = useRef({ startY: 0, lastVal: value });

  return (
    <div
      className={`flex items-center gap-1 rounded-lg border border-border bg-muted/30 select-none ${className}`}
      onWheel={handleWheel}
      onTouchStart={(e) => { touchRef.current = { startY: e.touches[0].clientY, lastVal: value }; }}
      onTouchMove={(e) => {
        e.preventDefault();
        const diff = touchRef.current.startY - e.touches[0].clientY;
        const next = Math.max(1, Math.min(120, touchRef.current.lastVal + Math.round(diff / 12)));
        if (next !== value) { onChange(next); if (navigator.vibrate) navigator.vibrate(8); }
      }}
    >
      <button type="button" className="px-2 py-2 text-muted-foreground hover:text-foreground transition-colors text-sm font-medium"
        onClick={() => { const n = Math.max(1, value - 1); onChange(n); if (navigator.vibrate) navigator.vibrate(8); }}>−</button>
      <input type="number" min={1} max={120} value={value}
        onChange={(e) => onChange(Math.max(1, Math.min(120, parseInt(e.target.value) || 1)))}
        className="w-8 text-center text-sm font-medium bg-transparent focus:outline-none tabular-nums [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
      />
      <span className="text-xs text-muted-foreground pr-1">min</span>
      <button type="button" className="px-2 py-2 text-muted-foreground hover:text-foreground transition-colors text-sm font-medium"
        onClick={() => { const n = Math.min(120, value + 1); onChange(n); if (navigator.vibrate) navigator.vibrate(8); }}>+</button>
    </div>
  );
}

// ─── Mini Week Heatmap ──────────────────────────────────
function WeekHeatmap({ completionLog = [] }) {
  const today = new Date();
  const days = [];
  for (let i = 6; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(today.getDate() - i);
    const key = d.toISOString().slice(0, 10);
    const done = completionLog.some((e) => e.date === key);
    days.push({ key, done, isToday: i === 0, label: DAY_LABELS[d.getDay() === 0 ? 6 : d.getDay() - 1] });
  }

  return (
    <div className="flex items-center gap-1">
      {days.map((day) => (
        <div key={day.key} className="flex flex-col items-center gap-0.5">
          <div className={`w-4 h-4 rounded-sm transition-colors ${
            day.done ? "bg-emerald-500" : day.isToday ? "bg-muted border border-border" : "bg-muted/50"
          }`} />
          <span className={`text-[8px] ${day.isToday ? "text-foreground font-bold" : "text-muted-foreground/50"}`}>
            {day.label}
          </span>
        </div>
      ))}
    </div>
  );
}

// ─── Step-by-Step Execution Dialog ──────────────────────
function ExecutionDialog({ routine, open, onClose, onComplete }) {
  const [currentStep, setCurrentStep] = useState(0);
  const [timer, setTimer] = useState(0);
  const [isRunning, setIsRunning] = useState(false);
  const intervalRef = useRef(null);
  const items = routine?.items || [];
  const current = items[currentStep];
  const totalSteps = items.length;

  useEffect(() => {
    if (open) { setCurrentStep(0); setTimer(0); setIsRunning(false); }
    return () => clearInterval(intervalRef.current);
  }, [open]);

  useEffect(() => {
    if (isRunning) {
      intervalRef.current = setInterval(() => setTimer((t) => t + 1), 1000);
    } else {
      clearInterval(intervalRef.current);
    }
    return () => clearInterval(intervalRef.current);
  }, [isRunning]);

  const formatTime = (seconds) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, "0")}`;
  };

  const nextStep = () => {
    if (currentStep < totalSteps - 1) {
      setCurrentStep((s) => s + 1);
      setTimer(0);
      setIsRunning(true);
      if (navigator.vibrate) navigator.vibrate([50, 30, 50]);
    } else {
      setIsRunning(false);
      onComplete();
      if (navigator.vibrate) navigator.vibrate([100, 50, 100, 50, 100]);
    }
  };

  if (!routine || !current) return null;

  const targetSeconds = (current.duration_minutes || 5) * 60;
  const progress = Math.min((timer / targetSeconds) * 100, 100);
  const isOvertime = timer > targetSeconds;

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) { setIsRunning(false); onClose(); } }}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-base">
            <Play className="w-5 h-5 text-primary" />
            {routine.name}
          </DialogTitle>
        </DialogHeader>

        <div className="py-4">
          {/* Step progress */}
          <div className="flex items-center gap-1.5 mb-4">
            {items.map((_, i) => (
              <div key={i} className={`flex-1 h-1.5 rounded-full transition-colors ${
                i < currentStep ? "bg-emerald-500" : i === currentStep ? "bg-primary" : "bg-muted"
              }`} />
            ))}
          </div>

          {/* Current step */}
          <div className="text-center mb-6">
            <Badge variant="outline" className="text-[10px] mb-3">
              Étape {currentStep + 1}/{totalSteps}
            </Badge>
            <h3 className="font-heading font-semibold text-lg mb-1">{current.title}</h3>
            <p className="text-xs text-muted-foreground">{current.duration_minutes} min prévues</p>
          </div>

          {/* Timer */}
          <div className="text-center mb-4">
            <p className={`text-4xl font-bold tabular-nums ${isOvertime ? "text-orange-500" : "text-foreground"}`}>
              {formatTime(timer)}
            </p>
            <Progress value={progress} className={`h-2 mt-3 ${isOvertime ? "[&>div]:bg-orange-500" : ""}`} />
          </div>

          {/* Controls */}
          <div className="flex items-center justify-center gap-3">
            {!isRunning ? (
              <Button onClick={() => setIsRunning(true)} className="gap-2 px-8">
                <Play className="w-4 h-4" />
                {timer === 0 ? "Démarrer" : "Reprendre"}
              </Button>
            ) : (
              <>
                <Button variant="outline" onClick={() => setIsRunning(false)} className="gap-2">
                  <Timer className="w-4 h-4" />
                  Pause
                </Button>
                <Button onClick={nextStep} className="gap-2">
                  {currentStep < totalSteps - 1 ? (
                    <><SkipForward className="w-4 h-4" />Suivant</>
                  ) : (
                    <><CheckCircle2 className="w-4 h-4" />Terminer</>
                  )}
                </Button>
              </>
            )}
          </div>

          {/* Skip (when paused) */}
          {!isRunning && timer > 0 && (
            <div className="text-center mt-3">
              <button onClick={nextStep} className="text-xs text-muted-foreground hover:text-foreground transition-colors">
                {currentStep < totalSteps - 1 ? "Passer à l'étape suivante" : "Terminer la routine"}
              </button>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

// ─── iCal download helper ────────────────────────────────
async function downloadIcal(endpoint) {
  try {
    const res = await authFetch(`${API}/${endpoint}`);
    if (!res.ok) throw new Error("Erreur");
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = endpoint.includes("routine") ? "routine.ics" : "objectif.ics";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success("Fichier .ics téléchargé — ouvre-le pour l'ajouter à ton calendrier");
  } catch {
    toast.error("Erreur lors du téléchargement");
  }
}

// ─── Habit Card ─────────────────────────────────────────
function HabitCard({ routine, onEdit, onToggle, onComplete, onLaunch }) {
  const tod = timeLabel(routine.time_of_day);
  const TodIcon = tod.icon;
  const itemCount = (routine.items || []).length;
  const totalMin = routine.total_minutes || 0;
  const streak = routine.streak_current || 0;
  const today = new Date().toISOString().slice(0, 10);
  const isDoneToday = routine.last_completed_at?.startsWith(today);

  // Week completion count
  const completionLog = routine.completion_log || [];
  const weekAgo = new Date();
  weekAgo.setDate(weekAgo.getDate() - 7);
  const weekAgoStr = weekAgo.toISOString().slice(0, 10);
  const weekDone = completionLog.filter((e) => e.date >= weekAgoStr).length;

  return (
    <Card className={`p-5 transition-all ${
      isDoneToday ? "border-emerald-500/30 bg-emerald-500/3" :
      routine.is_active ? "hover:border-primary/30" : "opacity-60"
    }`}>
      {/* Header row */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
            <Badge variant="outline" className={`text-[10px] ${tod.color}`}>
              <TodIcon className="w-2.5 h-2.5 mr-1" />
              {tod.label}
            </Badge>
            <Badge variant="outline" className="text-[10px] bg-muted/50 text-muted-foreground border-border">
              <Repeat className="w-2.5 h-2.5 mr-1" />
              {freqLabel(routine.frequency)}
            </Badge>
            {isDoneToday && (
              <Badge variant="outline" className="text-[10px] bg-emerald-500/10 text-emerald-500 border-emerald-500/20">
                <CheckCircle2 className="w-2.5 h-2.5 mr-0.5" />
                Fait
              </Badge>
            )}
            {!routine.is_active && (
              <Badge variant="outline" className="text-[10px] bg-muted/50 text-muted-foreground border-border">
                En pause
              </Badge>
            )}
          </div>
          <h3 className="font-heading font-semibold text-base">{routine.name}</h3>
          {routine.description && (
            <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">{routine.description}</p>
          )}
        </div>

        <div className="flex items-center gap-1 shrink-0 ml-2">
          <button onClick={(e) => { e.stopPropagation(); downloadIcal(`routines/${routine.routine_id}/ical`); }}
            className="p-1.5 rounded-lg hover:bg-muted/50 transition-colors" title="Ajouter au calendrier">
            <CalendarPlus className="w-4 h-4 text-muted-foreground" />
          </button>
          <button onClick={(e) => { e.stopPropagation(); onToggle(); }}
            className="p-1.5 rounded-lg hover:bg-muted/50 transition-colors"
            title={routine.is_active ? "Mettre en pause" : "Activer"}>
            {routine.is_active
              ? <ToggleRight className="w-5 h-5 text-emerald-500" />
              : <ToggleLeft className="w-5 h-5 text-muted-foreground" />}
          </button>
          <button onClick={(e) => { e.stopPropagation(); onEdit(); }}
            className="p-1.5 rounded-lg hover:bg-muted/50 transition-colors" title="Modifier">
            <Pencil className="w-4 h-4 text-muted-foreground" />
          </button>
        </div>
      </div>

      {/* Streak + Week heatmap row */}
      <div className="flex items-center justify-between mb-3 p-2.5 rounded-lg bg-muted/20">
        <div className="flex items-center gap-3">
          {streak > 0 && (
            <div className="flex items-center gap-1">
              <Flame className={`w-4 h-4 ${streak >= 7 ? "text-orange-500" : "text-orange-400"}`} />
              <span className="text-sm font-bold tabular-nums">{streak}</span>
              <span className="text-[10px] text-muted-foreground">jours</span>
            </div>
          )}
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <Calendar className="w-3 h-3" />
            <span>{weekDone}/7 cette sem.</span>
          </div>
        </div>
        <WeekHeatmap completionLog={completionLog} />
      </div>

      {/* Items preview */}
      {itemCount > 0 && (
        <div className="space-y-1.5 mb-3">
          {(routine.items || []).slice(0, 4).map((item, i) => (
            <div key={i} className="flex items-center gap-2 text-xs">
              <span className="w-5 h-5 rounded-md bg-primary/10 text-primary flex items-center justify-center text-[10px] font-bold shrink-0">
                {i + 1}
              </span>
              <span className="truncate flex-1">{item.title}</span>
              <span className="text-muted-foreground shrink-0">{item.duration_minutes} min</span>
            </div>
          ))}
          {itemCount > 4 && (
            <p className="text-[11px] text-muted-foreground pl-7">+{itemCount - 4} autres actions</p>
          )}
        </div>
      )}

      {/* Bottom row */}
      <div className="flex items-center justify-between pt-3 border-t border-border/50">
        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          <div className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            <span>{totalMin} min</span>
          </div>
          <div className="flex items-center gap-1">
            <Play className="w-3 h-3" />
            <span>{itemCount} action{itemCount !== 1 ? "s" : ""}</span>
          </div>
          {routine.times_completed > 0 && (
            <div className="flex items-center gap-1">
              <Trophy className="w-3 h-3 text-amber-500" />
              <span>{routine.times_completed}x</span>
            </div>
          )}
        </div>

        <div className="flex items-center gap-1.5">
          {!isDoneToday && routine.is_active && (
            <Button size="sm" variant="default" className="h-7 text-xs gap-1"
              onClick={(e) => { e.stopPropagation(); onLaunch(); }}>
              <Play className="w-3 h-3" />
              Lancer
            </Button>
          )}
          {!isDoneToday && routine.is_active && (
            <Button size="sm" variant="outline"
              className="h-7 text-xs gap-1 border-emerald-500/30 text-emerald-600 hover:bg-emerald-500/10"
              onClick={(e) => { e.stopPropagation(); onComplete(); }}>
              <CheckCircle2 className="w-3 h-3" />
              Fait
            </Button>
          )}
        </div>
      </div>
    </Card>
  );
}

// ─── Main Page ──────────────────────────────────────────
export default function RoutinesPage() {
  const { user } = useAuth();
  const [routines, setRoutines] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [editingRoutine, setEditingRoutine] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [executingRoutine, setExecutingRoutine] = useState(null);

  const emptyForm = {
    name: "",
    description: "",
    time_of_day: "morning",
    frequency: "daily",
    frequency_days: [],
    items: [],
  };
  const [form, setForm] = useState(emptyForm);
  const [newItem, setNewItem] = useState({ title: "", duration_minutes: 5 });

  const isPremium = user?.subscription_tier === "premium";
  const maxRoutines = isPremium ? 20 : 3;

  // ── Load ────────────────────────────────────
  const loadRoutines = useCallback(async () => {
    try {
      const res = await authFetch(`${API}/routines`);
      if (res.ok) {
        const data = await res.json();
        setRoutines(data.routines || []);
      }
    } catch {
      toast.error("Erreur de chargement");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => { loadRoutines(); }, [loadRoutines]);

  // ── Create / Update ─────────────────────────
  const handleSave = async () => {
    if (!form.name.trim()) { toast.error("Donne un nom à ton habitude"); return; }
    if (form.items.length === 0) { toast.error("Ajoute au moins une action"); return; }
    setIsSaving(true);
    try {
      const url = editingRoutine ? `${API}/routines/${editingRoutine.routine_id}` : `${API}/routines`;
      const method = editingRoutine ? "PUT" : "POST";
      const res = await authFetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      if (!res.ok) { const err = await res.json(); throw new Error(err.detail || "Erreur"); }
      toast.success(editingRoutine ? "Habitude mise à jour" : "Habitude créée !");
      setShowDialog(false);
      setEditingRoutine(null);
      setForm(emptyForm);
      setNewItem({ title: "", duration_minutes: 5 });
      loadRoutines();
    } catch (err) {
      toast.error(err.message);
    } finally {
      setIsSaving(false);
    }
  };

  // ── Toggle active ───────────────────────────
  const handleToggle = async (routine) => {
    try {
      await authFetch(`${API}/routines/${routine.routine_id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ is_active: !routine.is_active }),
      });
      setRoutines((prev) =>
        prev.map((r) => r.routine_id === routine.routine_id ? { ...r, is_active: !r.is_active } : r)
      );
      toast.success(routine.is_active ? "Habitude en pause" : "Habitude activée");
    } catch {
      toast.error("Erreur");
    }
  };

  // ── Complete ────────────────────────────────
  const handleComplete = async (routine) => {
    try {
      const res = await authFetch(`${API}/routines/${routine.routine_id}/complete`, { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        if (data.status === "already_completed") {
          toast.info("Déjà complétée aujourd'hui");
          return;
        }
        setRoutines((prev) =>
          prev.map((r) =>
            r.routine_id === routine.routine_id ? {
              ...r,
              times_completed: data.times_completed,
              streak_current: data.streak_current,
              streak_best: data.streak_best,
              last_completed_at: new Date().toISOString(),
              completion_log: [...(r.completion_log || []), { date: new Date().toISOString().slice(0, 10), completed_at: new Date().toISOString() }],
            } : r
          )
        );
        if (data.streak_current >= 7) {
          toast.success(`Habitude complétée ! Streak de ${data.streak_current} jours !`);
        } else {
          toast.success("Habitude complétée !");
        }
      }
    } catch {
      toast.error("Erreur");
    }
  };

  // ── Delete ──────────────────────────────────
  const handleDelete = async (routineId) => {
    try {
      await authFetch(`${API}/routines/${routineId}`, { method: "DELETE" });
      setRoutines((prev) => prev.filter((r) => r.routine_id !== routineId));
      setDeleteConfirm(null);
      toast.success("Habitude supprimée");
    } catch {
      toast.error("Erreur");
    }
  };

  // ── Open edit dialog ────────────────────────
  const openEdit = (routine) => {
    setEditingRoutine(routine);
    setForm({
      name: routine.name,
      description: routine.description || "",
      time_of_day: routine.time_of_day || "morning",
      frequency: routine.frequency || "daily",
      frequency_days: routine.frequency_days || [],
      items: (routine.items || []).map((it, i) => ({
        title: it.title,
        duration_minutes: it.duration_minutes,
        type: it.type || "action",
        ref_id: it.ref_id || "",
        order: i,
      })),
    });
    setNewItem({ title: "", duration_minutes: 5 });
    setShowDialog(true);
  };

  // ── Item management ─────────────────────────
  const addItem = () => {
    if (!newItem.title.trim()) return;
    setForm((f) => ({
      ...f,
      items: [...f.items, { type: "action", ref_id: "", title: newItem.title.trim(), duration_minutes: newItem.duration_minutes, order: f.items.length }],
    }));
    setNewItem({ title: "", duration_minutes: 5 });
  };

  const removeItem = (idx) => {
    setForm((f) => ({ ...f, items: f.items.filter((_, i) => i !== idx).map((it, i) => ({ ...it, order: i })) }));
  };

  const moveItem = (idx, direction) => {
    setForm((f) => {
      const items = [...f.items];
      const targetIdx = idx + direction;
      if (targetIdx < 0 || targetIdx >= items.length) return f;
      [items[idx], items[targetIdx]] = [items[targetIdx], items[idx]];
      return { ...f, items: items.map((it, i) => ({ ...it, order: i })) };
    });
  };

  const canCreate = routines.length < maxRoutines;
  const activeRoutines = routines.filter((r) => r.is_active);
  const pausedRoutines = routines.filter((r) => !r.is_active);

  // Summary stats
  const today = new Date().toISOString().slice(0, 10);
  const doneToday = activeRoutines.filter((r) => r.last_completed_at?.startsWith(today)).length;
  const totalStreak = activeRoutines.reduce((max, r) => Math.max(max, r.streak_current || 0), 0);

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <main className="lg:ml-16 pb-20">
        <div className="max-w-2xl mx-auto px-4 py-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="font-heading text-2xl font-bold flex items-center gap-2">
                <CalendarClock className="w-6 h-6 text-primary" />
                Mes Habitudes
              </h1>
              <p className="text-sm text-muted-foreground mt-0.5">
                Construis des habitudes durables, jour après jour
              </p>
            </div>
            <Button onClick={() => { setEditingRoutine(null); setForm(emptyForm); setNewItem({ title: "", duration_minutes: 5 }); setShowDialog(true); }}
              disabled={!canCreate} className="gap-1.5" size="sm">
              <Plus className="w-4 h-4" />
              Nouvelle
            </Button>
          </div>

          {/* Summary bar (when habits exist) */}
          {!isLoading && activeRoutines.length > 0 && (
            <Card className="p-3 mb-5 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-1.5 text-sm">
                  <CheckCircle2 className={`w-4 h-4 ${doneToday === activeRoutines.length ? "text-emerald-500" : "text-muted-foreground"}`} />
                  <span className="font-medium tabular-nums">{doneToday}/{activeRoutines.length}</span>
                  <span className="text-xs text-muted-foreground">aujourd'hui</span>
                </div>
                {totalStreak > 0 && (
                  <div className="flex items-center gap-1.5 text-sm">
                    <Flame className="w-4 h-4 text-orange-500" />
                    <span className="font-medium tabular-nums">{totalStreak}</span>
                    <span className="text-xs text-muted-foreground">meilleur streak</span>
                  </div>
                )}
              </div>
              {doneToday === activeRoutines.length && activeRoutines.length > 0 && (
                <Badge className="text-[10px] bg-emerald-500/10 text-emerald-500 border-emerald-500/20">
                  <Sparkles className="w-2.5 h-2.5 mr-0.5" />
                  Journée parfaite
                </Badge>
              )}
            </Card>
          )}

          {/* Loading */}
          {isLoading ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : routines.length === 0 ? (
            <Card className="p-8 text-center">
              <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center mx-auto mb-4 ring-1 ring-primary/10">
                <CalendarClock className="w-10 h-10 text-primary" />
              </div>
              <h3 className="font-heading font-semibold text-lg mb-2">
                Crée ta première habitude
              </h3>
              <p className="text-sm text-muted-foreground mb-6 max-w-sm mx-auto leading-relaxed">
                Définis des micro-routines quotidiennes avec un suivi de progression et de streak. Routine matinale, pause productive, rituel du soir...
              </p>
              <Button onClick={() => { setEditingRoutine(null); setForm(emptyForm); setShowDialog(true); }} className="gap-2">
                <Plus className="w-4 h-4" />
                Créer une habitude
              </Button>
            </Card>
          ) : (
            <>
              {activeRoutines.length > 0 && (
                <div className="space-y-3 mb-6">
                  <h2 className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    Actives ({activeRoutines.length})
                  </h2>
                  {activeRoutines.map((r) => (
                    <HabitCard key={r.routine_id} routine={r}
                      onEdit={() => openEdit(r)}
                      onToggle={() => handleToggle(r)}
                      onComplete={() => handleComplete(r)}
                      onLaunch={() => setExecutingRoutine(r)}
                    />
                  ))}
                </div>
              )}

              {pausedRoutines.length > 0 && (
                <div className="space-y-3">
                  <h2 className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    En pause ({pausedRoutines.length})
                  </h2>
                  {pausedRoutines.map((r) => (
                    <HabitCard key={r.routine_id} routine={r}
                      onEdit={() => openEdit(r)}
                      onToggle={() => handleToggle(r)}
                      onComplete={() => handleComplete(r)}
                      onLaunch={() => setExecutingRoutine(r)}
                    />
                  ))}
                </div>
              )}

              {!canCreate && !isPremium && (
                <Card className="p-4 mt-4 border-amber-500/20 bg-amber-500/5 text-center">
                  <p className="text-sm text-amber-600 mb-2">Limite de {maxRoutines} habitudes atteinte</p>
                  <Button variant="outline" size="sm"
                    className="border-amber-500/30 text-amber-600 hover:bg-amber-500/10"
                    onClick={() => window.location.href = "/pricing"}>
                    <Trophy className="w-3.5 h-3.5 mr-1.5" />
                    Passer en Premium
                  </Button>
                </Card>
              )}
            </>
          )}

          {/* ─── Create / Edit Dialog ─────────────────── */}
          <Dialog open={showDialog} onOpenChange={(open) => {
            if (!open) { setEditingRoutine(null); setForm(emptyForm); }
            setShowDialog(open);
          }}>
            <DialogContent className="max-w-md max-h-[85vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  <CalendarClock className="w-5 h-5 text-primary" />
                  {editingRoutine ? "Modifier l'habitude" : "Nouvelle habitude"}
                </DialogTitle>
              </DialogHeader>

              <div className="space-y-4 py-2">
                {/* Name */}
                <div>
                  <label className="text-sm font-medium mb-1.5 block">Nom de l'habitude</label>
                  <input
                    className="w-full rounded-lg border border-border bg-muted/30 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
                    placeholder="Ex: Routine matinale, Pause productive..."
                    value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
                    maxLength={100} autoFocus
                  />
                </div>

                {/* Description */}
                <div>
                  <label className="text-sm font-medium mb-1.5 block">
                    Description <span className="text-muted-foreground">(optionnel — plus c'est détaillé, mieux le coach peut t'aider)</span>
                  </label>
                  <VoiceTextArea
                    value={form.description}
                    onChange={(val) => setForm((f) => ({ ...f, description: val }))}
                    placeholder="Décris ta routine en détail : objectifs, contexte, ce que tu veux accomplir, pourquoi c'est important pour toi..."
                    rows={4} maxLength={2000}
                  />
                </div>

                {/* Time of day */}
                <div>
                  <label className="text-sm font-medium mb-1.5 block">Moment de la journée</label>
                  <div className="grid grid-cols-4 gap-1.5">
                    {TIME_OF_DAY.map((tod) => {
                      const Icon = tod.icon;
                      const isActive = form.time_of_day === tod.value;
                      return (
                        <button key={tod.value} type="button"
                          onClick={() => setForm({ ...form, time_of_day: tod.value })}
                          className={`flex flex-col items-center gap-1 py-2.5 px-2 rounded-xl text-xs font-medium border transition-all ${
                            isActive ? "bg-primary text-primary-foreground border-primary scale-105" : "bg-muted/30 border-border hover:border-primary/30"
                          }`}>
                          <Icon className="w-4 h-4" />
                          {tod.label}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Frequency */}
                <div>
                  <label className="text-sm font-medium mb-1.5 block">Fréquence</label>
                  <div className="grid grid-cols-2 gap-1.5">
                    {FREQUENCY_OPTIONS.map((opt) => {
                      const isActive = form.frequency === opt.value;
                      return (
                        <button key={opt.value} type="button"
                          onClick={() => setForm({ ...form, frequency: opt.value, frequency_days: opt.value === "custom" ? form.frequency_days : [] })}
                          className={`py-2 px-3 rounded-xl text-xs font-medium border transition-all ${
                            isActive ? "bg-primary text-primary-foreground border-primary" : "bg-muted/30 border-border hover:border-primary/30"
                          }`}>
                          {opt.label}
                        </button>
                      );
                    })}
                  </div>

                  {/* Custom days picker */}
                  {form.frequency === "custom" && (
                    <div className="flex items-center gap-1.5 mt-2">
                      {DAY_LABELS.map((label, i) => {
                        const isSelected = (form.frequency_days || []).includes(i);
                        return (
                          <button key={i} type="button"
                            onClick={() => {
                              const days = form.frequency_days || [];
                              setForm({ ...form, frequency_days: isSelected ? days.filter((d) => d !== i) : [...days, i] });
                            }}
                            className={`w-9 h-9 rounded-lg text-xs font-medium border transition-all ${
                              isSelected ? "bg-primary text-primary-foreground border-primary" : "bg-muted/30 border-border hover:border-primary/30"
                            }`}>
                            {label}
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>

                {/* Items list */}
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    Actions de l'habitude ({form.items.length})
                  </label>

                  {form.items.length > 0 && (
                    <div className="space-y-1.5 mb-3">
                      {form.items.map((item, idx) => (
                        <div key={idx} className="flex items-center gap-2 p-2 rounded-lg bg-muted/30 border border-border/50 group">
                          <div className="flex flex-col gap-0.5 shrink-0">
                            <button type="button" onClick={() => moveItem(idx, -1)}
                              className="text-muted-foreground hover:text-foreground transition-colors p-0.5" disabled={idx === 0}>
                              <GripVertical className="w-3 h-3 rotate-180" />
                            </button>
                            <button type="button" onClick={() => moveItem(idx, 1)}
                              className="text-muted-foreground hover:text-foreground transition-colors p-0.5"
                              disabled={idx === form.items.length - 1}>
                              <GripVertical className="w-3 h-3" />
                            </button>
                          </div>
                          <span className="w-5 h-5 rounded-md bg-primary/10 text-primary flex items-center justify-center text-[10px] font-bold shrink-0">
                            {idx + 1}
                          </span>
                          <span className="flex-1 text-sm truncate">{item.title}</span>
                          <span className="text-xs text-muted-foreground shrink-0">{item.duration_minutes} min</span>
                          <button type="button" onClick={() => removeItem(idx)}
                            className="p-1 rounded hover:bg-red-500/10 text-muted-foreground hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100">
                            <X className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      ))}
                      <div className="flex items-center justify-end gap-1 text-xs text-muted-foreground pt-1">
                        <Clock className="w-3 h-3" />
                        <span>Total : {form.items.reduce((s, it) => s + it.duration_minutes, 0)} min</span>
                      </div>
                    </div>
                  )}

                  {/* Add item form */}
                  <div className="flex gap-2">
                    <input className="flex-1 rounded-lg border border-border bg-muted/30 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
                      placeholder="Nom de l'action..." value={newItem.title}
                      onChange={(e) => setNewItem({ ...newItem, title: e.target.value })}
                      maxLength={100}
                      onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); addItem(); } }}
                    />
                    <DurationPicker value={newItem.duration_minutes} onChange={(v) => setNewItem({ ...newItem, duration_minutes: v })} />
                    <Button type="button" size="sm" variant="outline" onClick={addItem} disabled={!newItem.title.trim()} className="shrink-0">
                      <Plus className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </div>

              <DialogFooter className="flex-col sm:flex-row gap-2">
                {editingRoutine && (
                  <Button variant="outline" className="text-red-500 border-red-500/30 hover:bg-red-500/10 sm:mr-auto"
                    onClick={() => { setDeleteConfirm(editingRoutine.routine_id); setShowDialog(false); }}>
                    <Trash2 className="w-4 h-4 mr-1.5" />
                    Supprimer
                  </Button>
                )}
                <Button variant="outline" onClick={() => setShowDialog(false)}>Annuler</Button>
                <Button onClick={handleSave} disabled={!form.name.trim() || form.items.length === 0 || isSaving} className="gap-2">
                  {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
                  {editingRoutine ? "Enregistrer" : "Créer l'habitude"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          {/* ─── Delete Confirmation Dialog ────────────── */}
          <Dialog open={!!deleteConfirm} onOpenChange={() => setDeleteConfirm(null)}>
            <DialogContent className="max-w-sm">
              <DialogHeader>
                <DialogTitle>Supprimer cette habitude ?</DialogTitle>
              </DialogHeader>
              <p className="text-sm text-muted-foreground py-2">
                Cette action est irréversible. L'habitude et tout son historique seront supprimés.
              </p>
              <DialogFooter>
                <Button variant="outline" onClick={() => setDeleteConfirm(null)}>Annuler</Button>
                <Button variant="destructive" onClick={() => handleDelete(deleteConfirm)} className="gap-1.5">
                  <Trash2 className="w-4 h-4" />
                  Supprimer
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          {/* ─── Execution Dialog ─────────────────────── */}
          <ExecutionDialog
            routine={executingRoutine}
            open={!!executingRoutine}
            onClose={() => setExecutingRoutine(null)}
            onComplete={() => {
              handleComplete(executingRoutine);
              setExecutingRoutine(null);
            }}
          />
        </div>
      </main>
    </div>
  );
}
