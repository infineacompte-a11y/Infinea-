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

const categoryIcons = {
  learning: BookOpen,
  productivity: Target,
  well_being: Heart,
};

const categoryColors = {
  learning: "text-blue-500 bg-blue-500/10",
  productivity: "text-amber-500 bg-amber-500/10",
  well_being: "text-emerald-500 bg-emerald-500/10",
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
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <Timer className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
          <p className="text-muted-foreground">Session non trouvée</p>
          <Button onClick={() => navigate("/dashboard")} className="mt-4">
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
  const strokeDashoffset = circumference - (progress / 100) * circumference;

  if (showCompletion) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <div className="max-w-md w-full text-center animate-fade-in">
          <div className="w-24 h-24 rounded-full bg-emerald-500/10 flex items-center justify-center mx-auto mb-6">
            <Trophy className="w-12 h-12 text-emerald-500" />
          </div>
          <h1 className="font-heading text-3xl font-bold mb-2" data-testid="completion-title">
            Félicitations ! 🎉
          </h1>
          <p className="text-muted-foreground mb-8">
            Vous avez transformé {Math.ceil(elapsedTime / 60)} minutes en progrès !
          </p>

          <div className="grid grid-cols-2 gap-4 mb-8">
            <Card className="stat-card">
              <CardContent className="p-4 text-center">
                <p className="text-2xl font-heading font-bold text-primary">
                  +{completionData?.time_added || Math.ceil(elapsedTime / 60)}
                </p>
                <p className="text-xs text-muted-foreground">minutes ajoutées</p>
              </CardContent>
            </Card>
            <Card className="stat-card">
              <CardContent className="p-4 text-center">
                <p className="text-2xl font-heading font-bold text-amber-500">
                  {completionData?.new_streak || 1}
                </p>
                <p className="text-xs text-muted-foreground">jours de streak</p>
              </CardContent>
            </Card>
          </div>

          <div className="space-y-3">
            <Button
              onClick={() => navigate("/dashboard")}
              className="w-full rounded-xl h-12"
              data-testid="back-dashboard-btn"
            >
              Continuer ma progression
            </Button>
            <Button
              variant="outline"
              onClick={() => navigate("/actions")}
              className="w-full rounded-xl h-12"
            >
              Nouvelle action
            </Button>
          </div>

          {/* AI Debrief */}
          <SessionDebrief
            sessionId={sessionId}
            duration={Math.ceil(elapsedTime / 60)}
            notes={notes}
            onContinue={() => navigate("/dashboard")}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 glass">
        <div className="flex items-center justify-between px-4 h-16">
          <button
            onClick={handleAbandon}
            className="flex items-center gap-2 text-muted-foreground hover:text-foreground"
            data-testid="abandon-btn"
          >
            <X className="w-5 h-5" />
            <span>Abandonner</span>
          </button>
          <Badge variant="outline" className="font-mono text-lg">
            {formatTime(elapsedTime)}
          </Badge>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex flex-col items-center justify-center p-4 pt-20">
        <div className="max-w-md w-full">
          {/* Timer Circle */}
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
                className="fill-none stroke-primary"
                strokeWidth="8"
                strokeLinecap="round"
                style={{
                  strokeDasharray: circumference,
                  strokeDashoffset: strokeDashoffset,
                  transition: "stroke-dashoffset 1s linear",
                }}
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="font-mono text-4xl font-bold" data-testid="timer-display">
                {formatTime(elapsedTime)}
              </span>
              <span className="text-sm text-muted-foreground">
                / {action.duration_max} min
              </span>
            </div>
          </div>

          {/* Action Info */}
          <Card className="mb-6">
            <CardContent className="p-4">
              <div className="flex items-center gap-4">
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${categoryColors[action.category]}`}>
                  <Icon className="w-6 h-6" />
                </div>
                <div>
                  <h2 className="font-heading text-xl font-semibold">{action.title}</h2>
                  <p className="text-sm text-muted-foreground">{action.description}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Instructions */}
          <Card className="mb-6">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-muted-foreground">Instructions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {action.instructions.map((instruction, i) => (
                <div
                  key={i}
                  className={`flex items-start gap-3 p-3 rounded-lg transition-colors ${
                    i === currentStep ? "bg-primary/10 border border-primary/30" : ""
                  } ${i < currentStep ? "opacity-50" : ""}`}
                  onClick={() => setCurrentStep(i)}
                >
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${
                    i < currentStep
                      ? "bg-emerald-500 text-white"
                      : i === currentStep
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-muted-foreground"
                  }`}>
                    {i < currentStep ? <Check className="w-4 h-4" /> : i + 1}
                  </div>
                  <span className={`text-sm ${i === currentStep ? "" : "text-muted-foreground"}`}>
                    {instruction}
                  </span>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Notes */}
          <Card className="mb-6">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-muted-foreground">Notes (optionnel)</CardTitle>
            </CardHeader>
            <CardContent>
              <Textarea
                placeholder="Notez vos réflexions..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="min-h-20 resize-none"
                data-testid="session-notes"
              />
            </CardContent>
          </Card>

          {/* Controls */}
          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={() => setIsRunning(!isRunning)}
              className="flex-1 h-12 rounded-xl"
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
              className="flex-1 h-12 rounded-xl"
              disabled={isCompleting}
              data-testid="complete-btn"
            >
              <Check className="w-5 h-5 mr-2" />
              Terminer
            </Button>
          </div>
        </div>
      </main>
    </div>
  );
}
