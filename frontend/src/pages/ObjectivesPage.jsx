import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
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
import { CardsSkeleton } from "@/components/PageSkeleton";
import AddToCalendarMenu from "@/components/AddToCalendarMenu";
import { VoiceTextArea } from "@/components/VoiceInput";
import { API, authFetch, useAuth } from "@/App";
import { toast } from "sonner";

const CATEGORY_COLORS = {
  learning: "bg-blue-500/10 text-blue-500 border-blue-500/20",
  productivity: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
  well_being: "bg-purple-500/10 text-purple-500 border-purple-500/20",
  creativity: "bg-amber-500/10 text-amber-500 border-amber-500/20",
  fitness: "bg-rose-500/10 text-rose-500 border-rose-500/20",
  mindfulness: "bg-sky-500/10 text-sky-500 border-sky-500/20",
  leadership: "bg-indigo-500/10 text-indigo-500 border-indigo-500/20",
  finance: "bg-teal-500/10 text-teal-500 border-teal-500/20",
  relations: "bg-pink-500/10 text-pink-500 border-pink-500/20",
  mental_health: "bg-cyan-500/10 text-cyan-500 border-cyan-500/20",
  entrepreneurship: "bg-orange-500/10 text-orange-500 border-orange-500/20",
};

const STATUS_COLORS = {
  active: { color: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20", icon: Play },
  paused: { color: "bg-amber-500/10 text-amber-500 border-amber-500/20", icon: Pause },
  completed: { color: "bg-blue-500/10 text-blue-500 border-blue-500/20", icon: CheckCircle2 },
  abandoned: { color: "bg-red-500/10 text-red-500 border-red-500/20", icon: Target },
};

// Duration presets: 2 weeks to 12 months
const DURATION_STEPS = [
  { value: 14 },
  { value: 30 },
  { value: 45 },
  { value: 60 },
  { value: 75 },
  { value: 90 },
  { value: 120 },
  { value: 150 },
  { value: 180 },
  { value: 210 },
  { value: 240 },
  { value: 270 },
  { value: 300 },
  { value: 330 },
  { value: 365 },
];

function durationToLabel(days, t) {
  if (days === 14) return t("objectives.duration.2weeks");
  if (days < 30) return t("objectives.duration.nDays", { count: days });
  const m = Math.round(days / 30);
  if (days === 45) return t("objectives.duration.nMonths", { count: 1.5 });
  if (days === 75) return t("objectives.duration.nMonths", { count: 2.5 });
  return t("objectives.duration.nMonths", { count: m });
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

function ObjectiveCard({ objective, onClick, t }) {
  const status = STATUS_COLORS[objective.status] || STATUS_COLORS.active;
  const categoryColor = CATEGORY_COLORS[objective.category] || CATEGORY_COLORS.learning;
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
            <Badge variant="outline" className={`text-[10px] ${categoryColor}`}>
              {t(`categories.${objective.category}`)}
            </Badge>
            <Badge variant="outline" className={`text-[10px] ${status.color}`}>
              <StatusIcon className="w-2.5 h-2.5 mr-1" />
              {t(`objectives.status.${objective.status}`)}
            </Badge>
          </div>
          <h3 className="font-heading font-semibold text-base truncate group-hover:text-primary transition-colors">
            {objective.title}
          </h3>
          {objective.description && (
            <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">{objective.description}</p>
          )}
        </div>
        <div className="flex items-center gap-1 shrink-0 ml-2">
          <AddToCalendarMenu type="objective" item={objective} className="opacity-0 group-hover:opacity-100" />
          <ChevronRight className="w-5 h-5 text-muted-foreground group-hover:text-primary transition-colors" />
        </div>
      </div>

      {/* Progress bar */}
      <div className="mb-3">
        <div className="flex items-center justify-between text-xs text-muted-foreground mb-1.5">
          <span>{t("objectives.sessionsCount", { completed: completedSteps, total: totalSteps })}</span>
          <span className="font-medium">{percent}%</span>
        </div>
        <Progress value={percent} className="h-2" />
      </div>

      {/* Stats row */}
      <div className="flex items-center gap-4 text-xs text-muted-foreground">
        <div className="flex items-center gap-1">
          <Flame className="w-3 h-3 text-orange-500" />
          <span>{t("objectives.streakDays", { count: objective.streak_days || 0 })}</span>
        </div>
        <div className="flex items-center gap-1">
          <Clock className="w-3 h-3" />
          <span>{t("objectives.totalMinutes", { count: objective.total_minutes || 0 })}</span>
        </div>
        <div className="flex items-center gap-1">
          <Calendar className="w-3 h-3" />
          <span>{t("objectives.dayProgress", { current: objective.current_day || 0, total: objective.target_duration_days })}</span>
        </div>
      </div>
    </Card>
  );
}

export default function ObjectivesPage() {
  const navigate = useNavigate();
  const { t } = useTranslation();
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
      toast.error(t("objectives.errors.loadFailed"));
    } finally {
      setIsLoading(false);
    }
  }, [t]);

  useEffect(() => {
    loadObjectives();
  }, [loadObjectives]);

  const handleCreate = async () => {
    if (!form.title.trim()) {
      toast.error(t("objectives.errors.titleRequired"));
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
        throw new Error(err.detail || t("common.error"));
      }
      const created = await res.json();
      toast.success(t("objectives.createSuccess"));
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

  const CATEGORY_KEYS = [
    "learning", "productivity", "well_being", "creativity", "fitness",
    "mindfulness", "leadership", "finance", "relations", "mental_health", "entrepreneurship",
  ];

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <main className="lg:ml-64 pt-20 lg:pt-8 px-4 lg:px-8 pb-8">
        <div className="max-w-2xl mx-auto">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="font-heading text-2xl font-bold flex items-center gap-2">
                <Target className="w-6 h-6 text-primary" />
                {t("objectives.title")}
              </h1>
              <p className="text-sm text-muted-foreground mt-0.5">
                {t("objectives.subtitle")}
              </p>
            </div>
            <Button
              onClick={() => setShowCreate(true)}
              disabled={!canCreate}
              className="gap-1.5"
              size="sm"
            >
              <Plus className="w-4 h-4" />
              {t("objectives.newObjective")}
            </Button>
          </div>

          {/* Loading */}
          {isLoading ? (
            <CardsSkeleton count={3} />
          ) : objectives.length === 0 ? (
            /* Empty state */
            <Card className="p-8 text-center">
              <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center mx-auto mb-4 ring-1 ring-primary/10">
                <Target className="w-10 h-10 text-primary" />
              </div>
              <h3 className="font-heading font-semibold text-lg mb-2">
                {t("objectives.empty.title")}
              </h3>
              <p className="text-sm text-muted-foreground mb-6 max-w-sm mx-auto leading-relaxed">
                {t("objectives.empty.description")}
              </p>
              <Button onClick={() => setShowCreate(true)} className="gap-2">
                <Sparkles className="w-4 h-4" />
                {t("objectives.empty.cta")}
              </Button>
            </Card>
          ) : (
            <>
              {/* Active objectives */}
              {activeObjectives.length > 0 && (
                <div className="space-y-3 mb-6">
                  <h2 className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    {t("objectives.activeSection", { count: activeObjectives.length })}
                  </h2>
                  {activeObjectives.map((obj) => (
                    <ObjectiveCard
                      key={obj.objective_id}
                      objective={obj}
                      onClick={() => navigate(`/objectives/${obj.objective_id}`)}
                      t={t}
                    />
                  ))}
                </div>
              )}

              {/* Other objectives */}
              {otherObjectives.length > 0 && (
                <div className="space-y-3">
                  <h2 className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    {t("objectives.archivedSection", { count: otherObjectives.length })}
                  </h2>
                  {otherObjectives.map((obj) => (
                    <ObjectiveCard
                      key={obj.objective_id}
                      objective={obj}
                      onClick={() => navigate(`/objectives/${obj.objective_id}`)}
                      t={t}
                    />
                  ))}
                </div>
              )}

              {/* Premium upsell if at limit */}
              {!canCreate && !isPremium && (
                <Card className="p-4 mt-4 border-amber-500/20 bg-amber-500/5 text-center">
                  <p className="text-sm text-amber-600 mb-2">
                    {t("objectives.limitReached")}
                  </p>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => navigate("/pricing")}
                    className="border-amber-500/30 text-amber-600 hover:bg-amber-500/10"
                  >
                    <Trophy className="w-3.5 h-3.5 mr-1.5" />
                    {t("objectives.upgradePremium")}
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
                  {t("objectives.newObjective")}
                </DialogTitle>
              </DialogHeader>

              <div className="space-y-4 py-2">
                {/* Title */}
                <div>
                  <label className="text-sm font-medium mb-1.5 block">
                    {t("objectives.form.titleLabel")}
                  </label>
                  <input
                    className="w-full rounded-lg border border-border bg-muted/30 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
                    placeholder={t("objectives.form.titlePlaceholder")}
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
                      {t("objectives.form.descriptionLabel")} <span className="text-muted-foreground">({t("common.optional")})</span>
                    </label>
                    <p className="text-[11px] text-muted-foreground mt-0.5">
                      {t("objectives.form.descriptionHint")}
                    </p>
                  </div>
                  <VoiceTextArea
                    value={form.description}
                    onChange={(val) => setForm((f) => ({ ...f, description: val }))}
                    placeholder={t("objectives.form.descriptionPlaceholder")}
                    rows={4}
                    maxLength={1500}
                  />
                </div>

                {/* Category — all 11 categories */}
                <div>
                  <label className="text-sm font-medium mb-1.5 block">{t("objectives.form.categoryLabel")}</label>
                  <div className="flex flex-wrap gap-1.5">
                    {CATEGORY_KEYS.map((key) => (
                      <button
                        key={key}
                        onClick={() => setForm({ ...form, category: key })}
                        className={`px-2.5 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                          form.category === key
                            ? "bg-primary text-primary-foreground border-primary scale-105"
                            : "bg-muted/30 border-border hover:border-primary/30"
                        }`}
                      >
                        {t(`categories.${key}`)}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Minutes per day — smooth slider */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-medium">{t("objectives.form.minutesPerDay")}</label>
                    <span className="text-lg font-bold text-primary tabular-nums">{t("objectives.form.minutesValue", { count: form.daily_minutes })}</span>
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
                    <span>{t("objectives.form.minutesValue", { count: 2 })}</span>
                    <span>{t("objectives.form.minutesValue", { count: 10 })}</span>
                    <span>{t("objectives.form.minutesValue", { count: 25 })}</span>
                  </div>
                </div>

                {/* Duration — smooth slider with snap points */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-medium">{t("objectives.form.durationLabel")}</label>
                    <span className="text-lg font-bold text-primary">{durationToLabel(form.target_duration_days, t)}</span>
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
                    <span>{t("objectives.duration.2weeks")}</span>
                    <span>{t("objectives.duration.nMonths", { count: 3 })}</span>
                    <span>{t("objectives.duration.nMonths", { count: 6 })}</span>
                    <span>{t("objectives.duration.nMonths", { count: 12 })}</span>
                  </div>
                </div>
              </div>

              <DialogFooter>
                <Button variant="outline" onClick={() => setShowCreate(false)}>
                  {t("common.cancel")}
                </Button>
                <Button onClick={handleCreate} disabled={!form.title.trim() || isCreating} className="gap-2">
                  {isCreating ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Sparkles className="w-4 h-4" />
                  )}
                  {t("objectives.form.generateCta")}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </main>
    </div>
  );
}
