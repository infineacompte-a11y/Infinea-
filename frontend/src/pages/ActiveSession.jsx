import React, { useState, useEffect, useCallback } from "react";
import { useParams, useLocation, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import {
  Timer,
  Play,
  Pause,
  Check,
  X,
  ChevronRight,
  BookOpen,
  Target,
  Heart,
  Sparkles,
  Trophy,
} from "lucide-react";
import { toast } from "sonner";
import { API, authFetch } from "@/App";
import SessionDebrief from "@/components/SessionDebrief";
import VoiceNoteButton from "@/components/VoiceNoteButton";

const categoryIcons = {
  learning: BookOpen,
  productivity: Target,
  well_being: Heart,
};

const categoryColors = {
  learning: "text-[#55B3AE] bg-[#55B3AE]/40",
  productivity: "text-[#E48C75] bg-[#E48C75]/40",
  well_being: "text-[#5DB786] bg-[#5DB786]/40",
};

export default function ActiveSession() {
  const { sessionId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();

  const [session, setSession] = useState(location.state?.session || null);
  const [isRunning, setIsRunning] = useState(false);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [currentStep, setCurrentStep] = useState(0);
  const [notes, setNotes] = useState("");
  const [isCompleting, setIsCompleting] = useState(false);
  const [showCompletion, setShowCompletion] = useState(false);
  const [completionData, setCompletionData] = useState(null);

  // Timer effect
  useEffect(() => {
    let interval;
    if (isRunning) {
      interval = setInterval(() => {
        setElapsedTime((prev) => prev + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isRunning]);

  // Auto-start timer
  useEffect(() => {
    if (session) {
      setIsRunning(true);
    }
  }, [session]);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  const handleComplete = async (completed = true) => {
    setIsCompleting(true);
    try {
      const response = await authFetch(`${API}/sessions/complete`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          actual_duration: Math.ceil(elapsedTime / 60),
          completed,
          notes: notes || null,
        }),
      });

      if (!response.ok) throw new Error("Erreur");

      const data = await response.json();
      setCompletionData(data);
      setShowCompletion(true);
      setIsRunning(false);

      if (completed) {
        toast.success("Bravo ! Session terminée avec succès !");
      }
    } catch (error) {
      toast.error("Erreur lors de la sauvegarde");
    } finally {
      setIsCompleting(false);
    }
  };

  const handleAbandon = () => {
    handleComplete(false);
  };

  if (!session) {
    return (
      <div className="min-h-screen app-bg-mesh flex items-center justify-center">
        <div className="text-center opacity-0 animate-fade-in" style={{ animationDelay: "100ms", animationFillMode: "forwards" }}>
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-muted/20 to-muted/5 flex items-center justify-center mx-auto mb-4 ring-1 ring-border/10">
            <Timer className="w-8 h-8 text-muted-foreground" />
          </div>
          <p className="text-muted-foreground mb-4">Session non trouvée</p>
          <Button onClick={() => navigate("/dashboard")} className="rounded-xl shadow-md hover:shadow-lg transition-all duration-200 btn-press">
            Retour au dashboard
          </Button>
        </div>
      </div>
    );
  }

  const action = session.action;
  const Icon = categoryIcons[action.category] || Sparkles;
  const progress = (elapsedTime / (action.duration_max * 60)) * 100;
  const circumference = 2 * Math.PI * 45;
  const strokeDashoffset = circumference - (Math.min(progress, 100) / 100) * circumference;

  if (showCompletion) {
    return (
      <div className="min-h-screen app-bg-mesh flex items-center justify-center p-4">
        <div className="max-w-md w-full text-center">
          {/* Celebration icon with scale animation */}
          <div className="opacity-0 animate-fade-in" style={{ animationDelay: "100ms", animationFillMode: "forwards" }}>
            <div className="w-24 h-24 rounded-full bg-gradient-to-br from-[#5DB786]/20 to-[#5DB786]/5 flex items-center justify-center mx-auto mb-6 ring-2 ring-[#5DB786]/20 success-celebrate">
              <Trophy className="w-12 h-12 text-[#5DB786] animate-success-pop" />
            </div>
          </div>

          <div className="opacity-0 animate-fade-in" style={{ animationDelay: "300ms", animationFillMode: "forwards" }}>
            <h1 className="font-sans font-semibold tracking-tight text-3xl font-bold mb-2" data-testid="completion-title">
              Félicitations ! 🎉
            </h1>
            <p className="text-muted-foreground mb-8">
              Vous avez transformé <span className="tabular-nums">{Math.ceil(elapsedTime / 60)}</span> minutes en progrès !
            </p>
          </div>

          <div className="opacity-0 animate-fade-in" style={{ animationDelay: "500ms", animationFillMode: "forwards" }}>
            <div className="grid grid-cols-2 gap-4 mb-8">
              <Card className="stat-card hover:shadow-md transition-all duration-200">
                <CardContent className="p-4 text-center">
                  <p className="text-2xl font-sans font-semibold tracking-tight font-bold text-primary tabular-nums">
                    +{completionData?.time_added || Math.ceil(elapsedTime / 60)}
                  </p>
                  <p className="text-xs text-muted-foreground">minutes ajoutées</p>
                </CardContent>
              </Card>
              <Card className="stat-card hover:shadow-md transition-all duration-200">
                <CardContent className="p-4 text-center">
                  <p className="text-2xl font-sans font-semibold tracking-tight font-bold text-[#E48C75] tabular-nums">
                    {completionData?.new_streak || 1}
                  </p>
                  <p className="text-xs text-muted-foreground">jours de streak</p>
                </CardContent>
              </Card>
            </div>
          </div>

          <div className="opacity-0 animate-fade-in" style={{ animationDelay: "700ms", animationFillMode: "forwards" }}>
            <div className="space-y-3">
              <Button
                onClick={() => navigate("/dashboard")}
                className="w-full rounded-xl h-12 shadow-md hover:shadow-lg bg-gradient-to-r from-[#459492] to-[#55B3AE] hover:from-[#275255] hover:to-[#459492] text-white border-0 transition-all duration-200 btn-press"
                data-testid="back-dashboard-btn"
              >
                Continuer ma progression
              </Button>
              <Button
                variant="outline"
                onClick={() => navigate("/actions")}
                className="w-full rounded-xl h-12 transition-all duration-200 btn-press"
              >
                Nouvelle action
              </Button>
            </div>
          </div>

          {/* AI Debrief */}
          <div className="opacity-0 animate-fade-in" style={{ animationDelay: "900ms", animationFillMode: "forwards" }}>
            <SessionDebrief
              sessionId={sessionId}
              duration={Math.ceil(elapsedTime / 60)}
              notes={notes}
              onStartAction={async (actionId) => {
                try {
                  const res = await authFetch(`${API}/sessions/start`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ action_id: actionId }),
                  });
                  if (!res.ok) throw new Error("Erreur");
                  const data = await res.json();
                  // Navigate away first, then to new session — forces React to remount
                  navigate("/dashboard", { replace: true });
                  setTimeout(() => {
                    navigate(`/session/${data.session_id}`, { state: { session: data }, replace: true });
                  }, 50);
                } catch {
                  navigate("/dashboard");
                }
              }}
              onContinue={() => navigate("/dashboard")}
            />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen app-bg-mesh flex flex-col">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 glass">
        <div className="flex items-center justify-between px-4 h-16">
          <button
            onClick={handleAbandon}
            className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors duration-200"
            data-testid="abandon-btn"
          >
            <X className="w-5 h-5" />
            <span>Abandonner</span>
          </button>
          <Badge variant="outline" className="font-mono text-lg tabular-nums px-3 py-1">
            {formatTime(elapsedTime)}
          </Badge>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex flex-col items-center justify-center p-4 pt-20">
        <div className="max-w-md w-full">
          {/* Timer Circle */}
          <div className="opacity-0 animate-fade-in" style={{ animationDelay: "100ms", animationFillMode: "forwards" }}>
            <div className="relative w-48 h-48 mx-auto mb-8">
              <svg className="w-full h-full transform -rotate-90">
                <circle
                  cx="96"
                  cy="96"
                  r="45"
                  className="fill-none stroke-border"
                  strokeWidth="8"
                />
                <circle
                  cx="96"
                  cy="96"
                  r="45"
                  className="fill-none"
                  stroke="#459492"
                  strokeWidth="8"
                  strokeLinecap="round"
                  style={{
                    strokeDasharray: circumference,
                    strokeDashoffset: strokeDashoffset,
                    transition: "stroke-dashoffset 1s linear",
                    filter: "drop-shadow(0 0 6px rgba(69, 148, 146, 0.3))",
                  }}
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="tabular-nums text-4xl font-bold font-mono text-foreground" data-testid="timer-display">
                  {formatTime(elapsedTime)}
                </span>
                <span className="text-sm text-muted-foreground tabular-nums">
                  / {action.duration_max} min
                </span>
              </div>
            </div>
          </div>

          {/* Action Info */}
          <div className="opacity-0 animate-fade-in" style={{ animationDelay: "200ms", animationFillMode: "forwards" }}>
            <Card className="mb-6 rounded-xl bg-card border-border hover:shadow-md transition-all duration-200">
              <CardContent className="p-4">
                <div className="flex items-center gap-4">
                  <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${categoryColors[action.category]}`}>
                    <Icon className="w-6 h-6" />
                  </div>
                  <div>
                    <h2 className="font-sans font-semibold tracking-tight text-xl font-semibold">{action.title}</h2>
                    <p className="text-sm text-muted-foreground">{action.description}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Instructions */}
          <div className="opacity-0 animate-fade-in" style={{ animationDelay: "300ms", animationFillMode: "forwards" }}>
            <Card className="mb-6 rounded-xl bg-card border-border">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-muted-foreground">Instructions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {action.instructions.map((instruction, i) => (
                  <div
                    key={i}
                    className={`flex items-start gap-3 p-3 rounded-lg transition-all duration-300 cursor-pointer ${
                      i === currentStep ? "bg-[#459492]/40 border border-[#459492]/30 shadow-sm scale-[1.01]" : ""
                    } ${i < currentStep ? "opacity-50 scale-[0.99]" : ""} ${
                      i > currentStep ? "hover:bg-muted/20 hover:scale-[1.005]" : ""
                    }`}
                    onClick={() => setCurrentStep(i)}
                  >
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium transition-all duration-200 shrink-0 tabular-nums ${
                      i < currentStep
                        ? "bg-[#5DB786] text-white"
                        : i === currentStep
                        ? "bg-[#459492] text-white ring-2 ring-[#459492]/30"
                        : "bg-muted text-muted-foreground"
                    }`}>
                      {i < currentStep ? <Check className="w-4 h-4" /> : i + 1}
                    </div>
                    <span className={`text-sm ${i === currentStep ? "text-foreground font-medium" : "text-muted-foreground"}`}>
                      {instruction}
                    </span>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Notes */}
          <div className="opacity-0 animate-fade-in" style={{ animationDelay: "400ms", animationFillMode: "forwards" }}>
            <Card className="mb-6 rounded-xl bg-card border-border">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-muted-foreground">Notes (optionnel)</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Textarea
                  placeholder="Notez vos réflexions..."
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="min-h-20 resize-none rounded-xl"
                  data-testid="session-notes"
                />
                <VoiceNoteButton
                  onTranscript={(text) =>
                    setNotes((prev) => (prev ? prev + " " + text : text))
                  }
                  disabled={isCompleting}
                />
              </CardContent>
            </Card>
          </div>

          {/* Controls */}
          <div className="opacity-0 animate-fade-in" style={{ animationDelay: "500ms", animationFillMode: "forwards" }}>
            <div className="flex gap-3">
              <Button
                variant="outline"
                onClick={() => setIsRunning(!isRunning)}
                className="flex-1 h-14 rounded-xl transition-all duration-200 btn-press"
                data-testid="pause-btn"
              >
                {isRunning ? (
                  <>
                    <Pause className="w-5 h-5 mr-2" />
                    Pause
                  </>
                ) : (
                  <>
                    <Play className="w-5 h-5 mr-2" />
                    Reprendre
                  </>
                )}
              </Button>
              <Button
                onClick={() => handleComplete(true)}
                className="flex-1 h-14 rounded-xl shadow-md hover:shadow-lg bg-gradient-to-r from-[#459492] to-[#55B3AE] hover:from-[#275255] hover:to-[#459492] text-white border-0 transition-all duration-200 btn-press"
                disabled={isCompleting}
                data-testid="complete-btn"
              >
                <Check className="w-5 h-5 mr-2" />
                Terminer
              </Button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
