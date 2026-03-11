import React, { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
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
} from "lucide-react";
import Sidebar from "@/components/Sidebar";
import { VoiceTextArea } from "@/components/VoiceInput";
import { API, authFetch, useAuth } from "@/App";
import { toast } from "sonner";

const TIME_OF_DAY = [
  { value: "morning", label: "Matin", icon: Sunrise, color: "text-amber-500 bg-amber-500/10 border-amber-500/20" },
  { value: "afternoon", label: "Après-midi", icon: Sun, color: "text-orange-500 bg-orange-500/10 border-orange-500/20" },
  { value: "evening", label: "Soir", icon: Moon, color: "text-indigo-500 bg-indigo-500/10 border-indigo-500/20" },
  { value: "anytime", label: "Flexible", icon: Infinity, color: "text-emerald-500 bg-emerald-500/10 border-emerald-500/20" },
];

const DURATION_PRESETS = [5, 10, 15, 20, 30];

function timeLabel(tod) {
  return TIME_OF_DAY.find((t) => t.value === tod) || TIME_OF_DAY[0];
}

// ─── Routine Card ──────────────────────────────────────────
function RoutineCard({ routine, onEdit, onDelete, onToggle, onComplete }) {
  const tod = timeLabel(routine.time_of_day);
  const TodIcon = tod.icon;
  const itemCount = (routine.items || []).length;
  const totalMin = routine.total_minutes || 0;

  return (
    <Card className={`p-5 transition-all ${routine.is_active ? "hover:border-primary/30" : "opacity-60"}`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1.5">
            <Badge variant="outline" className={`text-[10px] ${tod.color}`}>
              <TodIcon className="w-2.5 h-2.5 mr-1" />
              {tod.label}
            </Badge>
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

        {/* Quick actions */}
        <div className="flex items-center gap-1 shrink-0 ml-2">
          <button
            onClick={(e) => { e.stopPropagation(); onToggle(); }}
            className="p-1.5 rounded-lg hover:bg-muted/50 transition-colors"
            title={routine.is_active ? "Mettre en pause" : "Activer"}
          >
            {routine.is_active
              ? <ToggleRight className="w-5 h-5 text-emerald-500" />
              : <ToggleLeft className="w-5 h-5 text-muted-foreground" />
            }
          </button>
          <button
            onClick={(e) => { e.stopPropagation(); onEdit(); }}
            className="p-1.5 rounded-lg hover:bg-muted/50 transition-colors"
            title="Modifier"
          >
            <Pencil className="w-4 h-4 text-muted-foreground" />
          </button>
        </div>
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

      {/* Stats row */}
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
              <Flame className="w-3 h-3 text-orange-500" />
              <span>{routine.times_completed}x complétée</span>
            </div>
          )}
        </div>

        <Button
          size="sm"
          variant="outline"
          className="h-7 text-xs gap-1 border-emerald-500/30 text-emerald-600 hover:bg-emerald-500/10"
          onClick={(e) => { e.stopPropagation(); onComplete(); }}
          disabled={!routine.is_active}
        >
          <CheckCircle2 className="w-3 h-3" />
          Terminée
        </Button>
      </div>
    </Card>
  );
}

// ─── Main Page ─────────────────────────────────────────────
export default function RoutinesPage() {
  const { user } = useAuth();
  const [routines, setRoutines] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [editingRoutine, setEditingRoutine] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState(null);

  const emptyForm = {
    name: "",
    description: "",
    time_of_day: "morning",
    items: [],
  };
  const [form, setForm] = useState(emptyForm);

  // Item being added
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
      toast.error("Erreur de chargement des routines");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => { loadRoutines(); }, [loadRoutines]);

  // ── Create / Update ─────────────────────────
  const handleSave = async () => {
    if (!form.name.trim()) {
      toast.error("Donne un nom à ta routine");
      return;
    }
    if (form.items.length === 0) {
      toast.error("Ajoute au moins une action à ta routine");
      return;
    }
    setIsSaving(true);
    try {
      const url = editingRoutine
        ? `${API}/routines/${editingRoutine.routine_id}`
        : `${API}/routines`;
      const method = editingRoutine ? "PUT" : "POST";

      const res = await authFetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Erreur");
      }
      toast.success(editingRoutine ? "Routine mise à jour" : "Routine créée !");
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
        prev.map((r) =>
          r.routine_id === routine.routine_id ? { ...r, is_active: !r.is_active } : r
        )
      );
      toast.success(routine.is_active ? "Routine en pause" : "Routine activée");
    } catch {
      toast.error("Erreur");
    }
  };

  // ── Complete ────────────────────────────────
  const handleComplete = async (routine) => {
    try {
      const res = await authFetch(`${API}/routines/${routine.routine_id}/complete`, {
        method: "POST",
      });
      if (res.ok) {
        const data = await res.json();
        setRoutines((prev) =>
          prev.map((r) =>
            r.routine_id === routine.routine_id
              ? { ...r, times_completed: data.times_completed, last_completed_at: new Date().toISOString() }
              : r
          )
        );
        toast.success("Routine complétée ! Bravo !");
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
      toast.success("Routine supprimée");
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

  // ── Add item to form ────────────────────────
  const addItem = () => {
    if (!newItem.title.trim()) return;
    setForm((f) => ({
      ...f,
      items: [
        ...f.items,
        {
          type: "action",
          ref_id: "",
          title: newItem.title.trim(),
          duration_minutes: newItem.duration_minutes,
          order: f.items.length,
        },
      ],
    }));
    setNewItem({ title: "", duration_minutes: 5 });
  };

  const removeItem = (idx) => {
    setForm((f) => ({
      ...f,
      items: f.items.filter((_, i) => i !== idx).map((it, i) => ({ ...it, order: i })),
    }));
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

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <main className="lg:ml-16 pb-20">
        <div className="max-w-2xl mx-auto px-4 py-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="font-heading text-2xl font-bold flex items-center gap-2">
                <CalendarClock className="w-6 h-6 text-primary" />
                Mes Routines
              </h1>
              <p className="text-sm text-muted-foreground mt-0.5">
                Structure ta journée idéale en micro-sessions
              </p>
            </div>
            <Button
              onClick={() => {
                setEditingRoutine(null);
                setForm(emptyForm);
                setNewItem({ title: "", duration_minutes: 5 });
                setShowDialog(true);
              }}
              disabled={!canCreate}
              className="gap-1.5"
              size="sm"
            >
              <Plus className="w-4 h-4" />
              Nouvelle routine
            </Button>
          </div>

          {/* Loading */}
          {isLoading ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : routines.length === 0 ? (
            /* Empty state */
            <Card className="p-8 text-center">
              <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center mx-auto mb-4 ring-1 ring-primary/10">
                <CalendarClock className="w-10 h-10 text-primary" />
              </div>
              <h3 className="font-heading font-semibold text-lg mb-2">
                Crée ta première routine
              </h3>
              <p className="text-sm text-muted-foreground mb-6 max-w-sm mx-auto leading-relaxed">
                Organise tes micro-sessions en séquences : routine matinale, pause déjeuner productive, rituel du soir...
              </p>
              <Button
                onClick={() => {
                  setEditingRoutine(null);
                  setForm(emptyForm);
                  setShowDialog(true);
                }}
                className="gap-2"
              >
                <Plus className="w-4 h-4" />
                Créer une routine
              </Button>
            </Card>
          ) : (
            <>
              {/* Active routines */}
              {activeRoutines.length > 0 && (
                <div className="space-y-3 mb-6">
                  <h2 className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    Actives ({activeRoutines.length})
                  </h2>
                  {activeRoutines.map((r) => (
                    <RoutineCard
                      key={r.routine_id}
                      routine={r}
                      onEdit={() => openEdit(r)}
                      onDelete={() => setDeleteConfirm(r.routine_id)}
                      onToggle={() => handleToggle(r)}
                      onComplete={() => handleComplete(r)}
                    />
                  ))}
                </div>
              )}

              {/* Paused routines */}
              {pausedRoutines.length > 0 && (
                <div className="space-y-3">
                  <h2 className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    En pause ({pausedRoutines.length})
                  </h2>
                  {pausedRoutines.map((r) => (
                    <RoutineCard
                      key={r.routine_id}
                      routine={r}
                      onEdit={() => openEdit(r)}
                      onDelete={() => setDeleteConfirm(r.routine_id)}
                      onToggle={() => handleToggle(r)}
                      onComplete={() => handleComplete(r)}
                    />
                  ))}
                </div>
              )}

              {/* Premium upsell */}
              {!canCreate && !isPremium && (
                <Card className="p-4 mt-4 border-amber-500/20 bg-amber-500/5 text-center">
                  <p className="text-sm text-amber-600 mb-2">
                    Limite de {maxRoutines} routines atteinte
                  </p>
                  <Button
                    variant="outline"
                    size="sm"
                    className="border-amber-500/30 text-amber-600 hover:bg-amber-500/10"
                    onClick={() => window.location.href = "/pricing"}
                  >
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
                  {editingRoutine ? "Modifier la routine" : "Nouvelle routine"}
                </DialogTitle>
              </DialogHeader>

              <div className="space-y-4 py-2">
                {/* Name */}
                <div>
                  <label className="text-sm font-medium mb-1.5 block">Nom de la routine</label>
                  <input
                    className="w-full rounded-lg border border-border bg-muted/30 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
                    placeholder="Ex: Routine matinale, Pause productive..."
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    maxLength={100}
                    autoFocus
                  />
                </div>

                {/* Description */}
                <div>
                  <label className="text-sm font-medium mb-1.5 block">
                    Description <span className="text-muted-foreground">(optionnel)</span>
                  </label>
                  <VoiceTextArea
                    value={form.description}
                    onChange={(val) => setForm((f) => ({ ...f, description: val }))}
                    placeholder="Décris ta routine..."
                    rows={2}
                    maxLength={500}
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
                        <button
                          key={tod.value}
                          type="button"
                          onClick={() => setForm({ ...form, time_of_day: tod.value })}
                          className={`flex flex-col items-center gap-1 py-2.5 px-2 rounded-xl text-xs font-medium border transition-all ${
                            isActive
                              ? "bg-primary text-primary-foreground border-primary scale-105"
                              : "bg-muted/30 border-border hover:border-primary/30"
                          }`}
                        >
                          <Icon className="w-4 h-4" />
                          {tod.label}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Items list */}
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    Actions de la routine ({form.items.length})
                  </label>

                  {form.items.length > 0 && (
                    <div className="space-y-1.5 mb-3">
                      {form.items.map((item, idx) => (
                        <div
                          key={idx}
                          className="flex items-center gap-2 p-2 rounded-lg bg-muted/30 border border-border/50 group"
                        >
                          <div className="flex flex-col gap-0.5 shrink-0">
                            <button
                              type="button"
                              onClick={() => moveItem(idx, -1)}
                              className="text-muted-foreground hover:text-foreground transition-colors p-0.5"
                              disabled={idx === 0}
                            >
                              <GripVertical className="w-3 h-3 rotate-180" />
                            </button>
                            <button
                              type="button"
                              onClick={() => moveItem(idx, 1)}
                              className="text-muted-foreground hover:text-foreground transition-colors p-0.5"
                              disabled={idx === form.items.length - 1}
                            >
                              <GripVertical className="w-3 h-3" />
                            </button>
                          </div>
                          <span className="w-5 h-5 rounded-md bg-primary/10 text-primary flex items-center justify-center text-[10px] font-bold shrink-0">
                            {idx + 1}
                          </span>
                          <span className="flex-1 text-sm truncate">{item.title}</span>
                          <span className="text-xs text-muted-foreground shrink-0">{item.duration_minutes} min</span>
                          <button
                            type="button"
                            onClick={() => removeItem(idx)}
                            className="p-1 rounded hover:bg-red-500/10 text-muted-foreground hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100"
                          >
                            <X className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      ))}

                      {/* Total */}
                      <div className="flex items-center justify-end gap-1 text-xs text-muted-foreground pt-1">
                        <Clock className="w-3 h-3" />
                        <span>Total : {form.items.reduce((s, it) => s + it.duration_minutes, 0)} min</span>
                      </div>
                    </div>
                  )}

                  {/* Add item form */}
                  <div className="flex gap-2">
                    <input
                      className="flex-1 rounded-lg border border-border bg-muted/30 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
                      placeholder="Nom de l'action..."
                      value={newItem.title}
                      onChange={(e) => setNewItem({ ...newItem, title: e.target.value })}
                      maxLength={100}
                      onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); addItem(); } }}
                    />
                    <select
                      className="w-20 rounded-lg border border-border bg-muted/30 px-2 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
                      value={newItem.duration_minutes}
                      onChange={(e) => setNewItem({ ...newItem, duration_minutes: parseInt(e.target.value) })}
                    >
                      {DURATION_PRESETS.map((d) => (
                        <option key={d} value={d}>{d} min</option>
                      ))}
                    </select>
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      onClick={addItem}
                      disabled={!newItem.title.trim()}
                      className="shrink-0"
                    >
                      <Plus className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </div>

              <DialogFooter className="flex-col sm:flex-row gap-2">
                {editingRoutine && (
                  <Button
                    variant="outline"
                    className="text-red-500 border-red-500/30 hover:bg-red-500/10 sm:mr-auto"
                    onClick={() => {
                      setDeleteConfirm(editingRoutine.routine_id);
                      setShowDialog(false);
                    }}
                  >
                    <Trash2 className="w-4 h-4 mr-1.5" />
                    Supprimer
                  </Button>
                )}
                <Button variant="outline" onClick={() => setShowDialog(false)}>
                  Annuler
                </Button>
                <Button
                  onClick={handleSave}
                  disabled={!form.name.trim() || form.items.length === 0 || isSaving}
                  className="gap-2"
                >
                  {isSaving ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <CheckCircle2 className="w-4 h-4" />
                  )}
                  {editingRoutine ? "Enregistrer" : "Créer la routine"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          {/* ─── Delete Confirmation Dialog ────────────── */}
          <Dialog open={!!deleteConfirm} onOpenChange={() => setDeleteConfirm(null)}>
            <DialogContent className="max-w-sm">
              <DialogHeader>
                <DialogTitle>Supprimer cette routine ?</DialogTitle>
              </DialogHeader>
              <p className="text-sm text-muted-foreground py-2">
                Cette action est irréversible. La routine et toutes ses données seront supprimées.
              </p>
              <DialogFooter>
                <Button variant="outline" onClick={() => setDeleteConfirm(null)}>
                  Annuler
                </Button>
                <Button
                  variant="destructive"
                  onClick={() => handleDelete(deleteConfirm)}
                  className="gap-1.5"
                >
                  <Trash2 className="w-4 h-4" />
                  Supprimer
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </main>
    </div>
  );
}
