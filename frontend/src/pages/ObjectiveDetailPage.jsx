import React, { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
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
  ArrowLeft,
  Flame,
  Clock,
  Calendar,
  Play,
  CheckCircle2,
  Circle,
  Sparkles,
  Loader2,
  Pause,
  Trash2,
  RotateCcw,
  ChevronDown,
  ChevronUp,
  BookOpen,
  Lightbulb,
  Trophy,
} from "lucide-react";
import Sidebar from "@/components/Sidebar";
import { API, authFetch } from "@/App";
import { toast } from "sonner";

const DIFFICULTY_LABELS = ["", "Fondamental", "Débutant", "Intermédiaire", "Avancé", "Expert"];
const DIFFICULTY_COLORS = ["", "text-emerald-500", "text-blue-500", "text-amber-500", "text-orange-500", "text-rose-500"];

function CurriculumStep({ step, index, isNext, onStart }) {
  const [expanded, setExpanded] = useState(isNext);
  const completed = step.completed;

  return (
    <div
      className={`border rounded-xl transition-all ${
        isNext
          ? "border-primary/40 bg-primary/5 shadow-sm"
          : completed
          ? "border-border/30 bg-muted/20"
          : "border-border/50"
      }`}
    >
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3 px-4 py-3 text-left"
      >
        {/* Status icon */}
        <div className="shrink-0">
          {completed ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-500" />
          ) : isNext ? (
            <div className="w-5 h-5 rounded-full bg-primary flex items-center justify-center">
              <Play className="w-2.5 h-2.5 text-primary-foreground ml-0.5" />
            </div>
          ) : (
            <Circle className="w-5 h-5 text-muted-foreground/40" />
          )}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-medium text-muted-foreground">JOUR {step.day}</span>
            {step.review && (
              <Badge variant="outline" className="text-[9px] bg-sky-500/10 text-sky-500 border-sky-500/20">
                Révision
              </Badge>
            )}
            {step.difficulty && (
              <span className={`text-[10px] ${DIFFICULTY_COLORS[step.difficulty] || ""}`}>
                {DIFFICULTY_LABELS[step.difficulty] || ""}
              </span>
            )}
          </div>
          <h4 className={`text-sm font-medium truncate ${completed ? "text-muted-foreground line-through" : ""}`}>
            {step.title}
          </h4>
        </div>

        {/* Duration + expand */}
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-xs text-muted-foreground">
            {step.duration_min}-{step.duration_max}m
          </span>
          {expanded ? (
            <ChevronUp className="w-4 h-4 text-muted-foreground" />
          ) : (
            <ChevronDown className="w-4 h-4 text-muted-foreground" />
          )}
        </div>
      </button>

      {/* Expanded content */}
      {expanded && (
        <div className="px-4 pb-4 pt-0 space-y-3 border-t border-border/30 mt-0">
          <p className="text-sm text-muted-foreground leading-relaxed pt-3">{step.description}</p>

          {step.focus && (
            <div className="flex items-center gap-1.5 text-xs">
              <BookOpen className="w-3 h-3 text-primary" />
              <span className="text-muted-foreground">Focus :</span>
              <span className="font-medium">{step.focus}</span>
            </div>
          )}

          {step.instructions && step.instructions.length > 0 && (
            <div className="space-y-1.5">
              {step.instructions.map((inst, i) => (
                <div key={i} className="flex items-start gap-2 text-sm">
                  <span className="text-primary font-medium shrink-0">{i + 1}.</span>
                  <span className="text-muted-foreground">{inst}</span>
                </div>
              ))}
            </div>
          )}

          {step.tip && (
            <div className="flex items-start gap-2 bg-amber-500/5 rounded-lg px-3 py-2 border border-amber-500/10">
              <Lightbulb className="w-3.5 h-3.5 text-amber-500 shrink-0 mt-0.5" />
              <span className="text-xs text-amber-600">{step.tip}</span>
            </div>
          )}

          {/* Completed info */}
          {completed && step.actual_duration && (
            <div className="flex items-center gap-3 text-xs text-muted-foreground">
              <span>Durée : {step.actual_duration} min</span>
              {step.notes && <span className="truncate">Note : {step.notes}</span>}
            </div>
          )}

          {/* Start button for next step */}
          {isNext && !completed && (
            <Button onClick={() => onStart(step, index)} className="w-full gap-2 mt-2">
              <Play className="w-4 h-4" />
              Commencer cette session
            </Button>
          )}
        </div>
      )}
    </div>
  );
}

export default function ObjectiveDetailPage() {
  const { objectiveId } = useParams();
  const navigate = useNavigate();
  const [objective, setObjective] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showSession, setShowSession] = useState(false);
  const [activeStep, setActiveStep] = useState(null);
  const [activeStepIndex, setActiveStepIndex] = useState(null);
  const [sessionTimer, setSessionTimer] = useState(0);
  const [sessionRunning, setSessionRunning] = useState(false);
  const [sessionNotes, setSessionNotes] = useState("");
  const [isCompleting, setIsCompleting] = useState(false);
  const [showConfirmDelete, setShowConfirmDelete] = useState(false);

  const loadObjective = useCallback(async () => {
    try {
      const res = await authFetch(`${API}/objectives/${objectiveId}`);
      if (res.ok) {
        setObjective(await res.json());
      } else {
        toast.error("Objectif non trouvé");
        navigate("/objectives");
      }
    } catch {
      toast.error("Erreur de chargement");
    } finally {
      setIsLoading(false);
    }
  }, [objectiveId, navigate]);

  useEffect(() => {
    loadObjective();
  }, [loadObjective]);

  // Timer
  useEffect(() => {
    let interval;
    if (sessionRunning) {
      interval = setInterval(() => setSessionTimer((t) => t + 1), 1000);
    }
    return () => clearInterval(interval);
  }, [sessionRunning]);

  const startSession = (step, index) => {
    setActiveStep(step);
    setActiveStepIndex(index);
    setSessionTimer(0);
    setSessionNotes("");
    setSessionRunning(true);
    setShowSession(true);
  };

  const completeStep = async (completed) => {
    if (isCompleting) return;
    setIsCompleting(true);
    setSessionRunning(false);
    const actualDuration = Math.max(1, Math.round(sessionTimer / 60));

    try {
      const res = await authFetch(`${API}/objectives/${objectiveId}/complete-step`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          step_index: activeStep.step_index,
          actual_duration: actualDuration,
          notes: sessionNotes,
          completed,
        }),
      });
      if (!res.ok) throw new Error("Erreur");
      const result = await res.json();

      if (completed) {
        toast.success(
          result.is_finished
            ? "Parcours terminé ! Bravo !"
            : `Session terminée ! ${result.progress_percent}% du parcours`
        );
      }

      setShowSession(false);
      loadObjective();
    } catch {
      toast.error("Erreur lors de la sauvegarde");
    } finally {
      setIsCompleting(false);
    }
  };

  const updateStatus = async (status) => {
    try {
      const res = await authFetch(`${API}/objectives/${objectiveId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
      });
      if (res.ok) {
        toast.success(status === "paused" ? "Objectif mis en pause" : "Objectif repris !");
        loadObjective();
      }
    } catch {
      toast.error("Erreur");
    }
  };

  const deleteObjective = async () => {
    try {
      const res = await authFetch(`${API}/objectives/${objectiveId}`, { method: "DELETE" });
      if (res.ok) {
        toast.success("Objectif supprimé");
        navigate("/objectives");
      }
    } catch {
      toast.error("Erreur");
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!objective) return null;

  const curriculum = objective.curriculum || [];
  const completedSteps = curriculum.filter((s) => s.completed).length;
  const totalSteps = curriculum.length;
  const percent = totalSteps > 0 ? Math.round((completedSteps / totalSteps) * 100) : 0;
  const nextStepIndex = curriculum.findIndex((s) => !s.completed);
  const isGenerating = totalSteps === 0;

  const formatTime = (s) => `${Math.floor(s / 60).toString().padStart(2, "0")}:${(s % 60).toString().padStart(2, "0")}`;

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <main className="lg:ml-16 pb-20">
        <div className="max-w-2xl mx-auto px-4 py-6">
          {/* Back */}
          <button
            onClick={() => navigate("/objectives")}
            className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground mb-4 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Mes Objectifs
          </button>

          {/* Header card */}
          <Card className="p-5 mb-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h1 className="font-heading text-xl font-bold">{objective.title}</h1>
                {objective.description && (
                  <p className="text-sm text-muted-foreground mt-1">{objective.description}</p>
                )}
              </div>
              <div className="flex items-center gap-1.5">
                {objective.status === "active" ? (
                  <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => updateStatus("paused")}>
                    <Pause className="w-4 h-4" />
                  </Button>
                ) : objective.status === "paused" ? (
                  <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => updateStatus("active")}>
                    <RotateCcw className="w-4 h-4" />
                  </Button>
                ) : null}
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 text-muted-foreground hover:text-destructive"
                  onClick={() => setShowConfirmDelete(true)}
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            </div>

            {/* Progress */}
            <div className="mb-4">
              <div className="flex items-center justify-between text-sm mb-2">
                <span className="text-muted-foreground">Progression</span>
                <span className="font-semibold">{percent}%</span>
              </div>
              <Progress value={percent} className="h-3" />
            </div>

            {/* Stats */}
            <div className="grid grid-cols-4 gap-3">
              <div className="text-center p-2 rounded-lg bg-muted/30">
                <Flame className="w-4 h-4 text-orange-500 mx-auto mb-1" />
                <div className="text-lg font-bold">{objective.streak_days || 0}</div>
                <div className="text-[10px] text-muted-foreground">Streak</div>
              </div>
              <div className="text-center p-2 rounded-lg bg-muted/30">
                <Clock className="w-4 h-4 text-blue-500 mx-auto mb-1" />
                <div className="text-lg font-bold">{objective.total_minutes || 0}</div>
                <div className="text-[10px] text-muted-foreground">Minutes</div>
              </div>
              <div className="text-center p-2 rounded-lg bg-muted/30">
                <CheckCircle2 className="w-4 h-4 text-emerald-500 mx-auto mb-1" />
                <div className="text-lg font-bold">{completedSteps}</div>
                <div className="text-[10px] text-muted-foreground">Sessions</div>
              </div>
              <div className="text-center p-2 rounded-lg bg-muted/30">
                <Calendar className="w-4 h-4 text-purple-500 mx-auto mb-1" />
                <div className="text-lg font-bold">J{objective.current_day || 0}</div>
                <div className="text-[10px] text-muted-foreground">/{objective.target_duration_days}j</div>
              </div>
            </div>
          </Card>

          {/* Curriculum */}
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-heading font-semibold text-base">
              {isGenerating ? "Génération en cours..." : "Mon parcours"}
            </h2>
            {!isGenerating && (
              <span className="text-xs text-muted-foreground">
                {completedSteps}/{totalSteps} sessions
              </span>
            )}
          </div>

          {isGenerating ? (
            <Card className="p-8 text-center">
              <Loader2 className="w-8 h-8 animate-spin text-primary mx-auto mb-3" />
              <p className="text-sm text-muted-foreground">
                L'IA génère ton parcours personnalisé...
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                Reviens dans quelques secondes !
              </p>
              <Button variant="outline" size="sm" className="mt-4" onClick={loadObjective}>
                Rafraîchir
              </Button>
            </Card>
          ) : (
            <div className="space-y-2">
              {curriculum.map((step, i) => (
                <CurriculumStep
                  key={step.step_index ?? i}
                  step={step}
                  index={i}
                  isNext={i === nextStepIndex && objective.status === "active"}
                  onStart={startSession}
                />
              ))}
            </div>
          )}

          {/* Completed celebration */}
          {percent >= 100 && (
            <Card className="p-6 mt-6 text-center border-amber-500/20 bg-gradient-to-br from-amber-500/10 to-amber-500/5">
              <Trophy className="w-12 h-12 text-amber-500 mx-auto mb-3" />
              <h3 className="font-heading font-bold text-lg">Parcours terminé !</h3>
              <p className="text-sm text-muted-foreground mt-1">
                Tu as complété {completedSteps} sessions et investi {objective.total_minutes || 0} minutes.
              </p>
              <Button className="mt-4" onClick={() => navigate("/objectives")}>
                Voir mes objectifs
              </Button>
            </Card>
          )}
        </div>
      </main>

      {/* Session Modal */}
      <Dialog open={showSession} onOpenChange={(open) => { if (!open) { setSessionRunning(false); setShowSession(false); } }}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-base">
              <Sparkles className="w-5 h-5 text-primary" />
              {activeStep?.title}
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4 py-2">
            {/* Timer */}
            <div className="text-center">
              <div className="text-4xl font-mono font-bold tabular-nums">{formatTime(sessionTimer)}</div>
              <p className="text-xs text-muted-foreground mt-1">
                Objectif : {activeStep?.duration_min}-{activeStep?.duration_max} min
              </p>
            </div>

            {/* Description */}
            <p className="text-sm text-muted-foreground leading-relaxed">{activeStep?.description}</p>

            {/* Instructions */}
            {activeStep?.instructions?.length > 0 && (
              <div className="space-y-2 bg-muted/30 rounded-lg p-3">
                {activeStep.instructions.map((inst, i) => (
                  <div key={i} className="flex items-start gap-2 text-sm">
                    <span className="text-primary font-semibold shrink-0">{i + 1}.</span>
                    <span>{inst}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Tip */}
            {activeStep?.tip && (
              <div className="flex items-start gap-2 bg-amber-500/5 rounded-lg px-3 py-2 border border-amber-500/10">
                <Lightbulb className="w-3.5 h-3.5 text-amber-500 shrink-0 mt-0.5" />
                <span className="text-xs text-amber-600">{activeStep.tip}</span>
              </div>
            )}

            {/* Notes */}
            <textarea
              className="w-full rounded-lg border border-border bg-muted/30 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 resize-none"
              placeholder="Notes sur cette session..."
              value={sessionNotes}
              onChange={(e) => setSessionNotes(e.target.value)}
              rows={2}
            />
          </div>

          <DialogFooter className="flex-col sm:flex-row gap-2">
            <Button
              variant="outline"
              onClick={() => completeStep(false)}
              disabled={isCompleting}
              className="text-muted-foreground"
            >
              Abandonner
            </Button>
            <Button
              onClick={() => completeStep(true)}
              disabled={isCompleting}
              className="gap-2"
            >
              {isCompleting ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <CheckCircle2 className="w-4 h-4" />
              )}
              Terminer la session
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete confirmation */}
      <Dialog open={showConfirmDelete} onOpenChange={setShowConfirmDelete}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Supprimer cet objectif ?</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground">
            Cette action est irréversible. Toute la progression sera perdue.
          </p>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowConfirmDelete(false)}>
              Annuler
            </Button>
            <Button variant="destructive" onClick={deleteObjective}>
              Supprimer
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
