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
  Crown,
  Loader2,
  ArrowLeft,
} from "lucide-react";
import Sidebar from "@/components/Sidebar";
import { CardsSkeleton } from "@/components/PageSkeleton";
import AddToCalendarMenu from "@/components/AddToCalendarMenu";
import { VoiceTextArea } from "@/components/VoiceInput";
import { API, authFetch, useAuth } from "@/App";
import { toast } from "sonner";

const CATEGORY_MAP = {
  learning: { label: "Apprentissage", color: "bg-[#459492]/40 text-[#459492] border-[#459492]/20" },
  productivity: { label: "Productivité", color: "bg-[#E48C75]/40 text-[#E48C75] border-[#E48C75]/20" },
  well_being: { label: "Bien-être", color: "bg-[#5DB786]/40 text-[#5DB786] border-[#5DB786]/20" },
  creativity: { label: "Créativité", color: "bg-[#55B3AE]/40 text-[#55B3AE] border-[#55B3AE]/20" },
  fitness: { label: "Fitness", color: "bg-[#E48C75]/40 text-[#E48C75] border-[#E48C75]/20" },
  mindfulness: { label: "Pleine conscience", color: "bg-[#459492]/40 text-[#459492] border-[#459492]/20" },
  leadership: { label: "Leadership", color: "bg-[#7B8FA1]/15 text-[#7B8FA1] border-[#7B8FA1]/20" },
  finance: { label: "Finance", color: "bg-[#2E9B6A]/15 text-[#2E9B6A] border-[#2E9B6A]/20" },
  relations: { label: "Relations", color: "bg-[#C4806E]/15 text-[#C4806E] border-[#C4806E]/20" },
  mental_health: { label: "Santé mentale", color: "bg-[#6EAAA8]/15 text-[#6EAAA8] border-[#6EAAA8]/20" },
  entrepreneurship: { label: "Entrepreneuriat", color: "bg-[#E48C75]/40 text-[#E48C75] border-[#E48C75]/20" },
};

// Duration presets: 2 weeks to 12 months
const DURATION_STEPS = [
  { value: 14, label: "2 sem." },
  { value: 30, label: "1 mois" },
  { value: 45, label: "1.5 mois" },
  { value: 60, label: "2 mois" },
  { value: 75, label: "2.5 mois" },
  { value: 90, label: "3 mois" },
  { value: 120, label: "4 mois" },
  { value: 150, label: "5 mois" },
  { value: 180, label: "6 mois" },
  { value: 210, label: "7 mois" },
  { value: 240, label: "8 mois" },
  { value: 270, label: "9 mois" },
  { value: 300, label: "10 mois" },
  { value: 330, label: "11 mois" },
  { value: 365, label: "12 mois" },
];

function durationToLabel(days) {
  const match = DURATION_STEPS.find((s) => s.value === days);
  if (match) return match.label;
  if (days < 30) return `${days} jours`;
  const m = Math.round(days / 30);
  return `${m} mois`;
}

function durationSliderToValue(sliderPos) {
  const idx = Math.round(sliderPos);
  return DURATION_STEPS[Math.min(idx, DURATION_STEPS.length - 1)]?.value || 30;
}

function durationValueToSlider(days) {
  let closest = 0;
  let minDist = Infinity;
  DURATION_STEPS.forEach((s, i) => {
    const dist = Math.abs(s.value - days);
    if (dist < minDist) { minDist = dist; closest = i; }
  });
  return closest;
}

const STATUS_MAP = {
  active: { label: "En cours", color: "bg-[#5DB786]/40 text-[#5DB786] border-[#5DB786]/20", icon: Play },
  paused: { label: "En pause", color: "bg-[#E48C75]/40 text-[#E48C75] border-[#E48C75]/20", icon: Pause },
  completed: { label: "Terminé", color: "bg-[#459492]/40 text-[#459492] border-[#459492]/20", icon: CheckCircle2 },
  abandoned: { label: "Abandonné", color: "bg-[#E48C75]/40 text-[#E48C75] border-[#E48C75]/20", icon: Target },
};

function ObjectiveCard({ objective, onClick, index = 0 }) {
  const status = STATUS_MAP[objective.status] || STATUS_MAP.active;
  const category = CATEGORY_MAP[objective.category] || CATEGORY_MAP.learning;
  const StatusIcon = status.icon;

  const totalSteps = (objective.curriculum || []).length;
  const completedSteps = (objective.curriculum || []).filter((s) => s.completed).length;
  const percent = totalSteps > 0 ? Math.round((completedSteps / totalSteps) * 100) : 0;

  return (
    <Card
      className="p-5 cursor-pointer group hover:shadow-lg hover:border-[#459492]/30 hover:-translate-y-0.5 transition-all duration-200 active:translate-y-px"
      onClick={onClick}
      style={{ animationDelay: `${index * 30}ms` }}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <Badge variant="outline" className={`text-[10px] rounded-lg font-medium ${category.color}`}>
              {category.label}
            </Badge>
            <Badge variant="outline" className={`text-[10px] rounded-lg font-medium ${status.color}`}>
              <StatusIcon className="w-2.5 h-2.5 mr-1" />
              {status.label}
            </Badge>
          </div>
          <h3 className="font-sans font-semibold tracking-tight font-semibold text-base truncate group-hover:text-primary transition-colors">
            {objective.title}
          </h3>
          {objective.description && (
            <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">{objective.description}</p>
          )}
        </div>
        <div className="flex items-center gap-1 shrink-0 ml-2">
          <AddToCalendarMenu type="objective" item={objective} className="opacity-0 group-hover:opacity-100" />
          <ChevronRight className="w-5 h-5 text-muted-foreground group-hover:text-primary group-hover:translate-x-1 transition-all duration-200" />
        </div>
      </div>

      {/* Progress bar */}
      <div className="mb-3">
        <div className="flex items-center justify-between text-xs text-muted-foreground mb-1.5">
          <span className="tabular-nums">{completedSteps}/{totalSteps} sessions</span>
          <span className="font-medium tabular-nums">{percent}%</span>
        </div>
        <Progress value={percent} className="h-2 rounded-full [&>div]:rounded-full [&>div]:transition-all [&>div]:duration-500" />
      </div>

      {/* Stats row */}
      <div className="flex items-center gap-4 text-xs text-muted-foreground">
        <div className="flex items-center gap-1">
          <Flame className="w-3 h-3 text-[#E48C75]" />
          <span className="tabular-nums">{objective.streak_days || 0}j streak</span>
        </div>
        <div className="flex items-center gap-1">
          <Clock className="w-3 h-3" />
          <span className="tabular-nums">{objective.total_minutes || 0} min</span>
        </div>
        <div className="flex items-center gap-1">
          <Calendar className="w-3 h-3" />
          <span className="tabular-nums">Jour {objective.current_day || 0}/{objective.target_duration_days}</span>
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
    <div className="min-h-screen app-bg-mesh">
      <Sidebar />
      <main className="lg:ml-64 pt-14 lg:pt-0 pb-8">
        <div className="section-dark-header px-4 lg:px-8 pt-8 lg:pt-10 pb-8">
          <div className="max-w-2xl mx-auto flex items-center justify-between">
            <div>
              <h1 className="text-display text-3xl lg:text-4xl font-semibold text-white opacity-0 animate-fade-in">
                Objectifs
              </h1>
              <p className="text-white/60 text-sm mt-1 opacity-0 animate-fade-in" style={{ animationDelay: "50ms" }}>
                Définissez et suivez vos objectifs
              </p>
            </div>
            <Button
              onClick={() => setShowCreate(true)}
              disabled={!canCreate}
              className="gap-1.5 rounded-xl shadow-md hover:shadow-lg transition-all duration-200"
              size="sm"
            >
              <Plus className="w-4 h-4" />
              Nouvel objectif
            </Button>
          </div>
        </div>
        <div className="px-4 lg:px-8">
        <div className="max-w-2xl mx-auto">

          {/* Loading */}
          {isLoading ? (
            <CardsSkeleton count={3} />
          ) : objectives.length === 0 ? (
            /* Empty state */
            <Card className="p-8 text-center opacity-0 animate-fade-in" style={{ animationDelay: "100ms" }}>
              <div className="bg-gradient-to-br from-[#459492]/20 to-transparent rounded-2xl w-16 h-16 flex items-center justify-center mx-auto mb-4">
                <Target className="w-8 h-8 text-[#459492]" />
              </div>
              <h3 className="font-sans font-semibold tracking-tight font-semibold text-lg mb-2">
                Définis ton premier objectif
              </h3>
              <p className="text-sm text-muted-foreground mb-6 max-w-sm mx-auto leading-relaxed">
                Apprendre une langue, jouer d'un instrument, méditer chaque jour...
                L'IA crée un parcours progressif adapté à toi.
              </p>
              <Button onClick={() => setShowCreate(true)} className="gap-2 rounded-xl shadow-md hover:shadow-lg transition-all duration-200">
                <Sparkles className="w-4 h-4" />
                Créer mon premier parcours
              </Button>
            </Card>
          ) : (
            <>
              {/* Active objectives */}
              {activeObjectives.length > 0 && (
                <div className="space-y-3 mb-6 opacity-0 animate-fade-in" style={{ animationDelay: "100ms" }}>
                  <h2 className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    En cours ({activeObjectives.length})
                  </h2>
                  {activeObjectives.map((obj, i) => (
                    <ObjectiveCard
                      key={obj.objective_id}
                      objective={obj}
                      index={i}
                      onClick={() => navigate(`/objectives/${obj.objective_id}`)}
                    />
                  ))}
                </div>
              )}

              {/* Other objectives */}
              {otherObjectives.length > 0 && (
                <div className="space-y-3 opacity-0 animate-fade-in" style={{ animationDelay: "200ms" }}>
                  <h2 className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    Archivés ({otherObjectives.length})
                  </h2>
                  {otherObjectives.map((obj, i) => (
                    <ObjectiveCard
                      key={obj.objective_id}
                      objective={obj}
                      index={i}
                      onClick={() => navigate(`/objectives/${obj.objective_id}`)}
                    />
                  ))}
                </div>
              )}

              {/* Premium upsell if at limit */}
              {!canCreate && !isPremium && (
                <Card className="p-4 mt-4 border-[#E48C75]/20 bg-[#E48C75]/5 text-center opacity-0 animate-fade-in" style={{ animationDelay: "300ms" }}>
                  <p className="text-sm text-muted-foreground mb-2">
                    Tu as atteint la limite de 2 objectifs actifs
                  </p>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => navigate("/pricing")}
                    className="border-[#E48C75]/30 text-[#E48C75] hover:bg-[#E48C75]/40 rounded-xl transition-all duration-200"
                  >
                    <Crown className="w-3.5 h-3.5 mr-1.5 text-[#E48C75]" />
                    Passer en Premium
                  </Button>
                </Card>
              )}
            </>
          )}

          {/* Create Dialog */}
          <Dialog open={showCreate} onOpenChange={setShowCreate}>
            <DialogContent className="max-w-md max-h-[90vh] overflow-y-auto">
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
                    className="w-full rounded-xl border border-border bg-muted/30 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 transition-all duration-200"
                    placeholder="Ex: Apprendre le thaï, Jouer du piano..."
                    value={form.title}
                    onChange={(e) => setForm({ ...form, title: e.target.value })}
                    maxLength={100}
                    autoFocus
                  />
                </div>

                {/* Description (optional — rich context for AI) */}
                <div>
                  <div className="mb-1.5">
                    <label className="text-sm font-medium">
                      Contexte & détails <span className="text-muted-foreground">(optionnel)</span>
                    </label>
                    <p className="text-[11px] text-muted-foreground mt-0.5">
                      Plus tu donnes de détails, meilleur sera ton parcours.
                    </p>
                  </div>
                  <VoiceTextArea
                    value={form.description}
                    onChange={(val) => setForm((f) => ({ ...f, description: val }))}
                    placeholder="Niveau actuel, objectif précis, contraintes, ressources disponibles, ce que tu veux atteindre à la fin du parcours..."
                    rows={4}
                    maxLength={1500}
                  />
                </div>

                {/* Category — all 11 categories */}
                <div>
                  <label className="text-sm font-medium mb-1.5 block">Catégorie</label>
                  <div className="flex flex-wrap gap-1.5">
                    {Object.entries(CATEGORY_MAP).map(([key, cat]) => (
                      <button
                        key={key}
                        onClick={() => setForm({ ...form, category: key })}
                        className={`px-2.5 py-1.5 rounded-xl text-xs font-medium border transition-all duration-200 ${
                          form.category === key
                            ? "bg-primary text-primary-foreground border-primary scale-105"
                            : "bg-muted/30 border-border hover:border-primary/30"
                        }`}
                      >
                        {cat.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Minutes per day — smooth slider */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-medium">Minutes / jour</label>
                    <span className="text-lg font-bold text-primary tabular-nums">{form.daily_minutes} min</span>
                  </div>
                  <input
                    type="range"
                    min={2}
                    max={25}
                    step={1}
                    value={form.daily_minutes}
                    onChange={(e) => setForm({ ...form, daily_minutes: parseInt(e.target.value) })}
                    className="w-full h-2 bg-muted rounded-full appearance-none cursor-pointer accent-primary [&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:h-5 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-primary [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:shadow-md [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-background"
                  />
                  <div className="flex justify-between text-[10px] text-muted-foreground mt-1">
                    <span>2 min</span>
                    <span>10 min</span>
                    <span>25 min</span>
                  </div>
                </div>

                {/* Duration — smooth slider with snap points */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-medium">Durée du parcours</label>
                    <span className="text-lg font-bold text-primary">{durationToLabel(form.target_duration_days)}</span>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={DURATION_STEPS.length - 1}
                    step={1}
                    value={durationValueToSlider(form.target_duration_days)}
                    onChange={(e) => setForm({ ...form, target_duration_days: durationSliderToValue(parseInt(e.target.value)) })}
                    className="w-full h-2 bg-muted rounded-full appearance-none cursor-pointer accent-primary [&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:h-5 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-primary [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:shadow-md [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-background"
                  />
                  <div className="flex justify-between text-[10px] text-muted-foreground mt-1">
                    <span>2 sem.</span>
                    <span>3 mois</span>
                    <span>6 mois</span>
                    <span>12 mois</span>
                  </div>
                </div>
              </div>

              <DialogFooter>
                <Button variant="outline" onClick={() => setShowCreate(false)} className="rounded-xl transition-all duration-200 hover:bg-muted/80">
                  Annuler
                </Button>
                <Button onClick={handleCreate} disabled={!form.title.trim() || isCreating} className="gap-2 rounded-xl shadow-md hover:shadow-lg transition-all duration-200">
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
        </div>
      </main>
    </div>
  );
}
