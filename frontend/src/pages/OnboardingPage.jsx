import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Timer,
  BookOpen,
  Target,
  Heart,
  Sun,
  Moon,
  Coffee,
  Sunrise,
  Sunset,
  Sparkles,
  ChevronRight,
  ChevronLeft,
  Loader2,
  Check,
  Zap,
  Brain,
  Dumbbell,
  Languages,
  Code,
  Palette,
  Music,
  PenTool,
  ListTodo,
  Mail,
  Lightbulb,
  Wind,
  Flower2,
  Smile,
  Clock,
} from "lucide-react";
import { toast } from "sonner";
import { API, useAuth, authFetch } from "@/App";

const STEPS = [
  { title: "Vos objectifs", subtitle: "Que souhaitez-vous développer ?" },
  { title: "Votre disponibilité", subtitle: "Quand êtes-vous le plus disponible ?" },
  { title: "Votre énergie", subtitle: "Quand êtes-vous au top de votre forme ?" },
  { title: "Vos centres d'intérêt", subtitle: "Personnalisez votre expérience" },
  { title: "Votre coach IA", subtitle: "Votre parcours personnalisé est prêt" },
];

const GOALS = [
  { key: "learning", label: "Apprentissage", icon: BookOpen, color: "text-blue-500 bg-blue-500/10 border-blue-500/30", desc: "Langues, lecture, nouvelles compétences" },
  { key: "productivity", label: "Productivité", icon: Target, color: "text-amber-500 bg-amber-500/10 border-amber-500/30", desc: "Organisation, focus, planification" },
  { key: "well_being", label: "Bien-être", icon: Heart, color: "text-emerald-500 bg-emerald-500/10 border-emerald-500/30", desc: "Méditation, respiration, étirements" },
];

const TIME_SLOTS = [
  { key: "morning", label: "Matin", icon: Sunrise, desc: "6h - 12h" },
  { key: "lunch", label: "Midi", icon: Sun, desc: "12h - 14h" },
  { key: "evening", label: "Soir", icon: Sunset, desc: "18h - 22h" },
];

const DAILY_MINUTES = [
  { value: 5, label: "5 min/jour", desc: "Parfait pour débuter" },
  { value: 10, label: "10 min/jour", desc: "Équilibre idéal" },
  { value: 15, label: "15 min/jour", desc: "Maximum d'impact" },
];

const ENERGY_PERIODS = [
  { key: "morning", label: "Le matin", icon: Sunrise },
  { key: "afternoon", label: "L'après-midi", icon: Sun },
  { key: "evening", label: "Le soir", icon: Moon },
];

const INTERESTS = {
  learning: [
    { key: "langues", label: "Langues", icon: Languages },
    { key: "coding", label: "Programmation", icon: Code },
    { key: "culture", label: "Culture générale", icon: Brain },
    { key: "creativite", label: "Créativité", icon: Palette },
    { key: "musique", label: "Musique", icon: Music },
    { key: "ecriture", label: "Écriture", icon: PenTool },
  ],
  productivity: [
    { key: "planning", label: "Planning", icon: ListTodo },
    { key: "emails", label: "Emails", icon: Mail },
    { key: "brainstorm", label: "Brainstorm", icon: Lightbulb },
    { key: "organisation", label: "Organisation", icon: Target },
    { key: "focus", label: "Concentration", icon: Zap },
    { key: "objectifs", label: "Objectifs", icon: Clock },
  ],
  well_being: [
    { key: "respiration", label: "Respiration", icon: Wind },
    { key: "meditation", label: "Méditation", icon: Flower2 },
    { key: "etirements", label: "Étirements", icon: Dumbbell },
    { key: "gratitude", label: "Gratitude", icon: Smile },
    { key: "relaxation", label: "Relaxation", icon: Coffee },
    { key: "mindfulness", label: "Pleine conscience", icon: Sparkles },
  ],
};

export default function OnboardingPage() {
  const navigate = useNavigate();
  const { user, setUser } = useAuth();
  const [step, setStep] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [aiResult, setAiResult] = useState(null);

  const [profile, setProfile] = useState({
    goals: [],
    availability_slots: [],
    daily_minutes: 10,
    energy_high: "",
    energy_low: "",
    interests: {},
  });

  const toggleArrayItem = (field, item) => {
    setProfile((prev) => {
      const arr = prev[field];
      return {
        ...prev,
        [field]: arr.includes(item) ? arr.filter((i) => i !== item) : [...arr, item],
      };
    });
  };

  const toggleInterest = (category, interest) => {
    setProfile((prev) => {
      const current = prev.interests[category] || [];
      const updated = current.includes(interest)
        ? current.filter((i) => i !== interest)
        : [...current, interest];
      return {
        ...prev,
        interests: { ...prev.interests, [category]: updated },
      };
    });
  };

  const canProceed = () => {
    switch (step) {
      case 0: return profile.goals.length > 0;
      case 1: return profile.availability_slots.length > 0;
      case 2: return profile.energy_high && profile.energy_low;
      case 3: return Object.values(profile.interests).some((arr) => arr.length > 0);
      case 4: return true;
      default: return false;
    }
  };

  const handleNext = async () => {
    if (step < 3) {
      setStep(step + 1);
    } else if (step === 3) {
      // Submit profile to backend
      setStep(4);
      setIsLoading(true);
      try {
        const response = await authFetch(`${API}/onboarding/profile`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(profile),
        });
        if (!response.ok) throw new Error("Erreur");
        const data = await response.json();
        setAiResult(data);
        setUser({ ...user, onboarding_completed: true, user_profile: data.user_profile });
      } catch (error) {
        toast.error("Erreur lors de la sauvegarde du profil");
        setAiResult({
          welcome_message: `Bienvenue sur InFinea, ${user?.name?.split(" ")[0]} ! Prêt(e) à transformer vos instants perdus en micro-victoires ?`,
          first_recommendation: "Commencez par une session de respiration de 2 minutes pour vous recentrer.",
        });
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleFinish = () => {
    navigate("/dashboard");
  };

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <header className="p-6">
        <div className="flex items-center gap-2 justify-center">
          <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center">
            <Timer className="w-6 h-6 text-primary-foreground" />
          </div>
          <span className="font-heading text-xl font-semibold">InFinea</span>
        </div>
      </header>

      {/* Progress */}
      <div className="px-6 max-w-lg mx-auto w-full">
        <div className="flex gap-2 mb-2">
          {STEPS.map((_, i) => (
            <div
              key={i}
              className={`h-1.5 flex-1 rounded-full transition-colors ${
                i <= step ? "bg-primary" : "bg-muted"
              }`}
            />
          ))}
        </div>
        <p className="text-xs text-muted-foreground text-center mb-6">
          {step + 1} / {STEPS.length}
        </p>
      </div>

      {/* Content */}
      <main className="flex-1 px-6 pb-8 max-w-lg mx-auto w-full">
        <div className="text-center mb-8">
          <h1 className="font-heading text-2xl font-semibold mb-2">{STEPS[step].title}</h1>
          <p className="text-muted-foreground">{STEPS[step].subtitle}</p>
        </div>

        {/* Step 0: Goals */}
        {step === 0 && (
          <div className="space-y-3">
            {GOALS.map((goal) => {
              const Icon = goal.icon;
              const selected = profile.goals.includes(goal.key);
              return (
                <Card
                  key={goal.key}
                  className={`cursor-pointer transition-all ${
                    selected ? `border-2 ${goal.color}` : "border hover:border-primary/50"
                  }`}
                  onClick={() => toggleArrayItem("goals", goal.key)}
                >
                  <CardContent className="p-4 flex items-center gap-4">
                    <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${goal.color}`}>
                      <Icon className="w-6 h-6" />
                    </div>
                    <div className="flex-1">
                      <h3 className="font-medium">{goal.label}</h3>
                      <p className="text-sm text-muted-foreground">{goal.desc}</p>
                    </div>
                    {selected && (
                      <div className="w-6 h-6 rounded-full bg-primary flex items-center justify-center">
                        <Check className="w-4 h-4 text-primary-foreground" />
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            })}
            <p className="text-xs text-center text-muted-foreground mt-2">
              Sélectionnez un ou plusieurs objectifs
            </p>
          </div>
        )}

        {/* Step 1: Availability */}
        {step === 1 && (
          <div className="space-y-6">
            <div>
              <h3 className="text-sm font-medium mb-3">Créneaux disponibles</h3>
              <div className="grid grid-cols-3 gap-3">
                {TIME_SLOTS.map((slot) => {
                  const Icon = slot.icon;
                  const selected = profile.availability_slots.includes(slot.key);
                  return (
                    <button
                      key={slot.key}
                      onClick={() => toggleArrayItem("availability_slots", slot.key)}
                      className={`p-4 rounded-xl border text-center transition-all ${
                        selected
                          ? "border-primary bg-primary/10 text-primary"
                          : "border-border hover:border-primary/50"
                      }`}
                    >
                      <Icon className="w-6 h-6 mx-auto mb-2" />
                      <p className="text-sm font-medium">{slot.label}</p>
                      <p className="text-xs text-muted-foreground">{slot.desc}</p>
                    </button>
                  );
                })}
              </div>
            </div>

            <div>
              <h3 className="text-sm font-medium mb-3">Temps quotidien</h3>
              <div className="space-y-2">
                {DAILY_MINUTES.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => setProfile({ ...profile, daily_minutes: opt.value })}
                    className={`w-full p-4 rounded-xl border text-left transition-all flex items-center justify-between ${
                      profile.daily_minutes === opt.value
                        ? "border-primary bg-primary/10"
                        : "border-border hover:border-primary/50"
                    }`}
                  >
                    <div>
                      <p className="font-medium">{opt.label}</p>
                      <p className="text-sm text-muted-foreground">{opt.desc}</p>
                    </div>
                    {profile.daily_minutes === opt.value && (
                      <Check className="w-5 h-5 text-primary" />
                    )}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Step 2: Energy Patterns */}
        {step === 2 && (
          <div className="space-y-8">
            <div>
              <h3 className="text-sm font-medium mb-3 flex items-center gap-2">
                <Zap className="w-4 h-4 text-amber-500" />
                Quand avez-vous le plus d'énergie ?
              </h3>
              <div className="space-y-2">
                {ENERGY_PERIODS.map((period) => {
                  const Icon = period.icon;
                  return (
                    <button
                      key={period.key}
                      onClick={() => setProfile({ ...profile, energy_high: period.key })}
                      className={`w-full p-4 rounded-xl border text-left transition-all flex items-center gap-3 ${
                        profile.energy_high === period.key
                          ? "border-amber-500 bg-amber-500/10"
                          : "border-border hover:border-amber-500/50"
                      }`}
                    >
                      <Icon className="w-5 h-5" />
                      <span>{period.label}</span>
                      {profile.energy_high === period.key && (
                        <Check className="w-5 h-5 text-amber-500 ml-auto" />
                      )}
                    </button>
                  );
                })}
              </div>
            </div>

            <div>
              <h3 className="text-sm font-medium mb-3 flex items-center gap-2">
                <Moon className="w-4 h-4 text-blue-400" />
                Quand avez-vous le moins d'énergie ?
              </h3>
              <div className="space-y-2">
                {ENERGY_PERIODS.map((period) => {
                  const Icon = period.icon;
                  return (
                    <button
                      key={period.key}
                      onClick={() => setProfile({ ...profile, energy_low: period.key })}
                      className={`w-full p-4 rounded-xl border text-left transition-all flex items-center gap-3 ${
                        profile.energy_low === period.key
                          ? "border-blue-400 bg-blue-400/10"
                          : "border-border hover:border-blue-400/50"
                      }`}
                    >
                      <Icon className="w-5 h-5" />
                      <span>{period.label}</span>
                      {profile.energy_low === period.key && (
                        <Check className="w-5 h-5 text-blue-400 ml-auto" />
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* Step 3: Interests */}
        {step === 3 && (
          <div className="space-y-6">
            {profile.goals.map((goalKey) => {
              const goal = GOALS.find((g) => g.key === goalKey);
              const interests = INTERESTS[goalKey] || [];
              if (!goal) return null;
              return (
                <div key={goalKey}>
                  <h3 className="text-sm font-medium mb-3 flex items-center gap-2">
                    <goal.icon className={`w-4 h-4 ${goal.color.split(" ")[0]}`} />
                    {goal.label}
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {interests.map((interest) => {
                      const Icon = interest.icon;
                      const selected = (profile.interests[goalKey] || []).includes(interest.key);
                      return (
                        <button
                          key={interest.key}
                          onClick={() => toggleInterest(goalKey, interest.key)}
                          className={`flex items-center gap-2 px-3 py-2 rounded-full border text-sm transition-all ${
                            selected
                              ? "border-primary bg-primary/10 text-primary"
                              : "border-border hover:border-primary/50"
                          }`}
                        >
                          <Icon className="w-3.5 h-3.5" />
                          {interest.label}
                        </button>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Step 4: AI Welcome */}
        {step === 4 && (
          <div className="text-center">
            {isLoading ? (
              <div className="py-12">
                <div className="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-6">
                  <Sparkles className="w-10 h-10 text-primary animate-pulse" />
                </div>
                <p className="text-muted-foreground mb-2">Votre coach IA prépare votre parcours...</p>
                <Loader2 className="w-6 h-6 animate-spin mx-auto text-primary" />
              </div>
            ) : aiResult ? (
              <div className="space-y-6 animate-fade-in">
                <div className="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center mx-auto">
                  <Sparkles className="w-10 h-10 text-primary" />
                </div>

                <Card className="border-primary/20 bg-primary/5">
                  <CardContent className="p-6">
                    <p className="text-lg leading-relaxed">{aiResult.welcome_message}</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-start gap-3">
                      <div className="w-10 h-10 rounded-xl bg-amber-500/10 flex items-center justify-center flex-shrink-0">
                        <Zap className="w-5 h-5 text-amber-500" />
                      </div>
                      <div className="text-left">
                        <p className="text-sm font-medium mb-1">Première recommandation</p>
                        <p className="text-sm text-muted-foreground">{aiResult.first_recommendation}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <div className="flex flex-wrap gap-2 justify-center">
                  {profile.goals.map((g) => {
                    const goal = GOALS.find((x) => x.key === g);
                    return goal ? (
                      <Badge key={g} variant="secondary" className={goal.color}>
                        <goal.icon className="w-3 h-3 mr-1" />
                        {goal.label}
                      </Badge>
                    ) : null;
                  })}
                  <Badge variant="secondary">
                    <Clock className="w-3 h-3 mr-1" />
                    {profile.daily_minutes} min/jour
                  </Badge>
                </div>
              </div>
            ) : null}
          </div>
        )}

        {/* Navigation */}
        <div className="flex gap-3 mt-8">
          {step > 0 && step < 4 && (
            <Button
              variant="outline"
              onClick={() => setStep(step - 1)}
              className="flex-1 h-12 rounded-xl"
            >
              <ChevronLeft className="w-5 h-5 mr-2" />
              Retour
            </Button>
          )}

          {step < 4 ? (
            <Button
              onClick={handleNext}
              disabled={!canProceed()}
              className="flex-1 h-12 rounded-xl"
            >
              {step === 3 ? "Terminer" : "Suivant"}
              <ChevronRight className="w-5 h-5 ml-2" />
            </Button>
          ) : (
            !isLoading && aiResult && (
              <Button
                onClick={handleFinish}
                className="w-full h-12 rounded-xl"
              >
                <Sparkles className="w-5 h-5 mr-2" />
                Commencer mon parcours
              </Button>
            )
          )}
        </div>
      </main>
    </div>
  );
}
