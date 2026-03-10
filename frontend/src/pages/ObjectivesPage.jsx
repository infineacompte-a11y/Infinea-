import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
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
  Target,
  Plus,
  Flame,
  Clock,
  Calendar,
  ChevronRight,
  Sparkles,
  Play,
  Pause,
  CheckCircle2,
  Trophy,
  Loader2,
  ArrowLeft,
} from "lucide-react";
import Sidebar from "@/components/Sidebar";
import { API, authFetch, useAuth } from "@/App";
import { toast } from "sonner";

const CATEGORY_MAP = {
  learning: { label: "Apprentissage", color: "bg-blue-500/10 text-blue-500 border-blue-500/20" },
  productivity: { label: "Productivité", color: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20" },
  well_being: { label: "Bien-être", color: "bg-purple-500/10 text-purple-500 border-purple-500/20" },
  creativity: { label: "Créativité", color: "bg-amber-500/10 text-amber-500 border-amber-500/20" },
  fitness: { label: "Fitness", color: "bg-rose-500/10 text-rose-500 border-rose-500/20" },
  mindfulness: { label: "Pleine conscience", color: "bg-sky-500/10 text-sky-500 border-sky-500/20" },
};

const STATUS_MAP = {
  active: { label: "En cours", color: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20", icon: Play },
  paused: { label: "En pause", color: "bg-amber-500/10 text-amber-500 border-amber-500/20", icon: Pause },
  completed: { label: "Terminé", color: "bg-blue-500/10 text-blue-500 border-blue-500/20", icon: CheckCircle2 },
  abandoned: { label: "Abandonné", color: "bg-red-500/10 text-red-500 border-red-500/20", icon: Target },
};

function ObjectiveCard({ objective, onClick }) {
  const status = STATUS_MAP[objective.status] || STATUS_MAP.active;
  const category = CATEGORY_MAP[objective.category] || CATEGORY_MAP.learning;
  const StatusIcon = status.icon;

  const totalSteps = (objective.curriculum || []).length;
  const completedSteps = (objective.curriculum || []).filter((s) => s.completed).length;
  const percent = totalSteps > 0 ? Math.round((completedSteps / totalSteps) * 100) : 0;

  return (
    <Card
      className="p-5 cursor-pointer hover:border-primary/30 transition-all group"
      onClick={onClick}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <Badge variant="outline" className={`text-[10px] ${category.color}`}>
              {category.label}
            </Badge>
            <Badge variant="outline" className={`text-[10px] ${status.color}`}>
              <StatusIcon className="w-2.5 h-2.5 mr-1" />
              {status.label}
            </Badge>
          </div>
          <h3 className="font-heading font-semibold text-base truncate group-hover:text-primary transition-colors">
            {objective.title}
          </h3>
          {objective.description && (
            <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">{objective.description}</p>
          )}
        </div>
        <ChevronRight className="w-5 h-5 text-muted-foreground group-hover:text-primary transition-colors shrink-0 mt-1" />
      </div>

      {/* Progress bar */}
      <div className="mb-3">
        <div className="flex items-center justify-between text-xs text-muted-foreground mb-1.5">
          <span>{completedSteps}/{totalSteps} sessions</span>
          <span className="font-medium">{percent}%</span>
        </div>
        <Progress value={percent} className="h-2" />
      </div>

      {/* Stats row */}
      <div className="flex items-center gap-4 text-xs text-muted-foreground">
        <div className="flex items-center gap-1">
          <Flame className="w-3 h-3 text-orange-500" />
          <span>{objective.streak_days || 0}j streak</span>
        </div>
        <div className="flex items-center gap-1">
          <Clock className="w-3 h-3" />
          <span>{objective.total_minutes || 0} min</span>
        </div>
        <div className="flex items-center gap-1">
          <Calendar className="w-3 h-3" />
          <span>Jour {objective.current_day || 0}/{objective.target_duration_days}</span>
        </div>
      </div>
    </Card>
  );
}

export default function ObjectivesPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [objectives, setObjectives] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [form, setForm] = useState({
    title: "",
    description: "",
    category: "learning",
    target_duration_days: 30,
    daily_minutes: 10,
  });

  const loadObjectives = useCallback(async () => {
    try {
      const res = await authFetch(`${API}/objectives`);
      if (res.ok) {
        const data = await res.json();
        setObjectives(data.objectives || []);
      }
    } catch {
      toast.error("Erreur de chargement");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadObjectives();
  }, [loadObjectives]);

  const handleCreate = async () => {
    if (!form.title.trim()) {
      toast.error("Donne un titre à ton objectif");
      return;
    }
    setIsCreating(true);
    try {
      const res = await authFetch(`${API}/objectives`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Erreur");
      }
      const created = await res.json();
      toast.success("Objectif créé ! Le curriculum se génère...");
      setShowCreate(false);
      setForm({ title: "", description: "", category: "learning", target_duration_days: 30, daily_minutes: 10 });
      navigate(`/objectives/${created.objective_id}`);
    } catch (err) {
      toast.error(err.message);
    } finally {
      setIsCreating(false);
    }
  };

  const activeObjectives = objectives.filter((o) => o.status === "active");
  const otherObjectives = objectives.filter((o) => o.status !== "active");
  const isPremium = user?.subscription_tier === "premium";
  const canCreate = activeObjectives.length < (isPremium ? 20 : 2);

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <main className="lg:ml-16 pb-20">
        <div className="max-w-2xl mx-auto px-4 py-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="font-heading text-2xl font-bold flex items-center gap-2">
                <Target className="w-6 h-6 text-primary" />
                Mes Objectifs
              </h1>
              <p className="text-sm text-muted-foreground mt-0.5">
                Tes parcours de progression personnalisés
              </p>
            </div>
            <Button
              onClick={() => setShowCreate(true)}
              disabled={!canCreate}
              className="gap-1.5"
              size="sm"
            >
              <Plus className="w-4 h-4" />
              Nouvel objectif
            </Button>
          </div>

          {/* Loading */}
          {isLoading ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : objectives.length === 0 ? (
            /* Empty state */
            <Card className="p-8 text-center">
              <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center mx-auto mb-4 ring-1 ring-primary/10">
                <Target className="w-10 h-10 text-primary" />
              </div>
              <h3 className="font-heading font-semibold text-lg mb-2">
                Définis ton premier objectif
              </h3>
              <p className="text-sm text-muted-foreground mb-6 max-w-sm mx-auto leading-relaxed">
                Apprendre une langue, jouer d'un instrument, méditer chaque jour...
                L'IA crée un parcours progressif adapté à toi.
              </p>
              <Button onClick={() => setShowCreate(true)} className="gap-2">
                <Sparkles className="w-4 h-4" />
                Créer mon premier parcours
              </Button>
            </Card>
          ) : (
            <>
              {/* Active objectives */}
              {activeObjectives.length > 0 && (
                <div className="space-y-3 mb-6">
                  <h2 className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    En cours ({activeObjectives.length})
                  </h2>
                  {activeObjectives.map((obj) => (
                    <ObjectiveCard
                      key={obj.objective_id}
                      objective={obj}
                      onClick={() => navigate(`/objectives/${obj.objective_id}`)}
                    />
                  ))}
                </div>
              )}

              {/* Other objectives */}
              {otherObjectives.length > 0 && (
                <div className="space-y-3">
                  <h2 className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    Archivés ({otherObjectives.length})
                  </h2>
                  {otherObjectives.map((obj) => (
                    <ObjectiveCard
                      key={obj.objective_id}
                      objective={obj}
                      onClick={() => navigate(`/objectives/${obj.objective_id}`)}
                    />
                  ))}
                </div>
              )}

              {/* Premium upsell if at limit */}
              {!canCreate && !isPremium && (
                <Card className="p-4 mt-4 border-amber-500/20 bg-amber-500/5 text-center">
                  <p className="text-sm text-amber-600 mb-2">
                    Tu as atteint la limite de 2 objectifs actifs
                  </p>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => navigate("/pricing")}
                    className="border-amber-500/30 text-amber-600 hover:bg-amber-500/10"
                  >
                    <Trophy className="w-3.5 h-3.5 mr-1.5" />
                    Passer en Premium
                  </Button>
                </Card>
              )}
            </>
          )}

          {/* Create Dialog */}
          <Dialog open={showCreate} onOpenChange={setShowCreate}>
            <DialogContent className="max-w-md">
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-primary" />
                  Nouvel objectif
                </DialogTitle>
              </DialogHeader>

              <div className="space-y-4 py-2">
                {/* Title */}
                <div>
                  <label className="text-sm font-medium mb-1.5 block">
                    Quel est ton objectif ?
                  </label>
                  <input
                    className="w-full rounded-lg border border-border bg-muted/30 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
                    placeholder="Ex: Apprendre le thaï, Jouer du piano..."
                    value={form.title}
                    onChange={(e) => setForm({ ...form, title: e.target.value })}
                    maxLength={100}
                    autoFocus
                  />
                </div>

                {/* Description (optional) */}
                <div>
                  <label className="text-sm font-medium mb-1.5 block">
                    Détails <span className="text-muted-foreground">(optionnel)</span>
                  </label>
                  <textarea
                    className="w-full rounded-lg border border-border bg-muted/30 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 resize-none"
                    placeholder="Niveau actuel, objectif précis, ressources..."
                    value={form.description}
                    onChange={(e) => setForm({ ...form, description: e.target.value })}
                    rows={2}
                    maxLength={300}
                  />
                </div>

                {/* Category */}
                <div>
                  <label className="text-sm font-medium mb-1.5 block">Catégorie</label>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(CATEGORY_MAP).map(([key, cat]) => (
                      <button
                        key={key}
                        onClick={() => setForm({ ...form, category: key })}
                        className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                          form.category === key
                            ? "bg-primary text-primary-foreground border-primary"
                            : "bg-muted/30 border-border hover:border-primary/30"
                        }`}
                      >
                        {cat.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Duration */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-sm font-medium mb-1.5 block">Durée du parcours</label>
                    <select
                      className="w-full rounded-lg border border-border bg-muted/30 px-3 py-2.5 text-sm"
                      value={form.target_duration_days}
                      onChange={(e) => setForm({ ...form, target_duration_days: parseInt(e.target.value) })}
                    >
                      <option value={14}>2 semaines</option>
                      <option value={30}>1 mois</option>
                      <option value={60}>2 mois</option>
                      <option value={90}>3 mois</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-1.5 block">Minutes / jour</label>
                    <select
                      className="w-full rounded-lg border border-border bg-muted/30 px-3 py-2.5 text-sm"
                      value={form.daily_minutes}
                      onChange={(e) => setForm({ ...form, daily_minutes: parseInt(e.target.value) })}
                    >
                      <option value={5}>5 min</option>
                      <option value={10}>10 min</option>
                      <option value={15}>15 min</option>
                      <option value={20}>20 min</option>
                    </select>
                  </div>
                </div>
              </div>

              <DialogFooter>
                <Button variant="outline" onClick={() => setShowCreate(false)}>
                  Annuler
                </Button>
                <Button onClick={handleCreate} disabled={!form.title.trim() || isCreating} className="gap-2">
                  {isCreating ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Sparkles className="w-4 h-4" />
                  )}
                  Générer mon parcours
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </main>
    </div>
  );
}
