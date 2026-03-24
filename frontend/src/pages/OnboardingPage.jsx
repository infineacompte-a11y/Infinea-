import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { track } from "@/lib/analytics";
import {
  ChevronRight,
  ChevronLeft,
  Target,
  BookOpen,
  Heart,
  Sparkles,
  Loader2,
  Sun,
  Moon,
  Sunrise,
  BatteryLow,
  BatteryMedium,
  BatteryFull,
  Check,
} from "lucide-react";
import { toast } from "sonner";
import { API, useAuth, authFetch } from "@/App";
import InFineaLogo from "@/components/InFineaLogo";

const STEPS = [
  { id: "goals", title: "Vos objectifs", subtitle: "Qu'aimeriez-vous améliorer ?" },
  { id: "availability", title: "Disponibilités", subtitle: "Quand êtes-vous le plus disponible ?" },
  { id: "energy", title: "Votre énergie", subtitle: "Comment décririez-vous votre énergie typique ?" },
  { id: "interests", title: "Vos intérêts", subtitle: "Quels domaines vous intéressent ?" },
];

const GOALS = [
  { id: "learn_new_skills", label: "Apprendre de nouvelles compétences", icon: BookOpen },
  { id: "boost_productivity", label: "Booster ma productivité", icon: Target },
  { id: "reduce_stress", label: "Réduire mon stress", icon: Heart },
  { id: "build_habits", label: "Construire de bonnes habitudes", icon: Sparkles },
];

const TIME_SLOTS = [
  { id: "morning", label: "Matin", sublabel: "6h - 12h", icon: Sunrise },
  { id: "afternoon", label: "Après-midi", sublabel: "12h - 18h", icon: Sun },
  { id: "evening", label: "Soir", sublabel: "18h - 23h", icon: Moon },
];

const ENERGY_LEVELS = [
  { id: "low", label: "Plutôt basse", description: "Je préfère des activités calmes", icon: BatteryLow },
  { id: "medium", label: "Moyenne", description: "Un bon équilibre effort/repos", icon: BatteryMedium },
  { id: "high", label: "Élevée", description: "Je suis prêt pour des défis", icon: BatteryFull },
];

const INTERESTS = [
  { id: "learning", label: "Apprentissage", color: "text-[#459492] bg-[#459492]/40" },
  { id: "productivity", label: "Productivité", color: "text-[#E48C75] bg-[#E48C75]/40" },
  { id: "well_being", label: "Bien-être", color: "text-[#5DB786] bg-[#5DB786]/40" },
  { id: "creativity", label: "Créativité", color: "text-[#55B3AE] bg-[#55B3AE]/40" },
  { id: "fitness", label: "Forme physique", color: "text-[#E48C75] bg-[#E48C75]/40" },
  { id: "mindfulness", label: "Pleine conscience", color: "text-[#459492] bg-[#459492]/40" },
  { id: "leadership", label: "Leadership", color: "text-[#7B8FA1] bg-[#7B8FA1]/10" },
  { id: "finance", label: "Finance", color: "text-[#2E9B6A] bg-[#2E9B6A]/10" },
  { id: "relations", label: "Relations", color: "text-[#C4806E] bg-[#C4806E]/10" },
  { id: "mental_health", label: "Santé mentale", color: "text-[#6EAAA8] bg-[#6EAAA8]/10" },
  { id: "entrepreneurship", label: "Entrepreneuriat", color: "text-[#E48C75] bg-[#E48C75]/40" },
];

export default function OnboardingPage() {
  const { user, setUser } = useAuth();
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [welcomeMessage, setWelcomeMessage] = useState(null);

  const [profile, setProfile] = useState({
    goals: [],
    preferred_times: [],
    energy_level: "medium",
    interests: [],
  });

  const toggleArrayItem = (field, item) => {
    setProfile((prev) => ({
      ...prev,
      [field]: prev[field].includes(item)
        ? prev[field].filter((i) => i !== item)
        : [...prev[field], item],
    }));
  };

  const canAdvance = () => {
    switch (STEPS[currentStep].id) {
      case "goals":
        return profile.goals.length > 0;
      case "availability":
        return profile.preferred_times.length > 0;
      case "energy":
        return true;
      case "interests":
        return profile.interests.length > 0;
      default:
        return true;
    }
  };

  const handleNext = () => {
    if (currentStep < STEPS.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      handleSubmit();
    }
  };

  const handleBack = () => {
    if (currentStep > 0) setCurrentStep(currentStep - 1);
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      const response = await authFetch(`${API}/onboarding/profile`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(profile),
      });

      if (!response.ok) throw new Error("Erreur");

      const data = await response.json();
      // Update auth context so ProtectedRoute knows onboarding is done
      setUser((prev) => ({ ...prev, user_profile: data.user_profile || profile, onboarding_completed: true }));
      setWelcomeMessage(data.welcome_message || data.first_recommendation || "Bienvenue sur InFinea ! Prêt(e) à transformer vos moments perdus en micro-victoires ?");
    } catch (error) {
      toast.error("Erreur lors de la sauvegarde du profil");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFinish = () => {
    track("onboarding_completed");
    navigate("/dashboard");
  };

  // Welcome screen after onboarding complete
  if (welcomeMessage) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#F8FAFB] via-white to-[#F0F7F7] flex items-center justify-center p-4">
        <div className="max-w-md w-full text-center animate-fade-in">
          <div className="w-20 h-20 rounded-full bg-[#459492]/40 flex items-center justify-center mx-auto mb-6">
            <Sparkles className="w-10 h-10 text-[#459492]" />
          </div>
          <h1 className="font-sans font-semibold tracking-tight text-3xl font-bold text-[#141E24] mb-4">
            Bienvenue, {user?.name?.split(" ")[0] || "Utilisateur"} !
          </h1>
          <Card className="mb-8 text-left rounded-2xl shadow-xl bg-white border border-[#E2E6EA]/50">
            <CardContent className="p-6">
              <p className="text-sm leading-relaxed text-[#141E24]">{welcomeMessage}</p>
            </CardContent>
          </Card>
          <Button
            onClick={handleFinish}
            className="w-full h-12 rounded-xl shadow-md bg-gradient-to-r from-[#459492] to-[#55B3AE] text-white hover:shadow-lg hover:brightness-105 transition-all duration-200 btn-press"
          >
            Commencer mes micro-actions
            <ChevronRight className="w-5 h-5 ml-2" />
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen app-bg-mesh flex flex-col">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md shadow-sm border-b border-[#E2E6EA]">
        <div className="flex items-center justify-between px-4 h-16">
          <InFineaLogo size={32} withText animate />
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate("/dashboard")}
            className="rounded-xl text-[#667085] hover:text-[#459492] hover:bg-[#F0F7F7] transition-all duration-200"
          >
            Passer
          </Button>
        </div>
      </header>

      {/* Progress Bar */}
      <div className="fixed top-16 left-0 right-0 z-40 h-1.5 bg-[#E2E6EA] overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-[#459492] to-[#55B3AE] rounded-full transition-all duration-500 ease-out"
          style={{ width: `${((currentStep + 1) / STEPS.length) * 100}%` }}
        />
      </div>

      {/* Main Content */}
      <main className="flex-1 flex items-center justify-center p-4 pt-24 pb-32">
        <div className="max-w-lg w-full animate-fade-in" key={currentStep}>
          {/* Step Header */}
          <div className="text-center mb-8 opacity-0 animate-fade-in" style={{ animationDelay: "0ms", animationFillMode: "forwards" }}>
            <Badge className="mb-4 bg-[#F0F7F7] text-[#459492] border-[#459492]/20 hover:bg-[#F0F7F7] font-medium">
              {currentStep + 1} / {STEPS.length}
            </Badge>
            <h1 className="font-sans font-semibold tracking-tight text-2xl font-bold text-[#141E24] mb-2">
              {STEPS[currentStep].title}
            </h1>
            <p className="text-[#667085]">{STEPS[currentStep].subtitle}</p>
          </div>

          {/* Step Content */}
          {STEPS[currentStep].id === "goals" && (
            <div className="grid gap-3">
              {GOALS.map((goal, index) => {
                const Icon = goal.icon;
                const selected = profile.goals.includes(goal.id);
                return (
                  <Card
                    key={goal.id}
                    className={`cursor-pointer transition-all duration-200 opacity-0 animate-fade-in rounded-xl btn-press ${
                      selected
                        ? "bg-[#F0F7F7] border-[#459492] shadow-md ring-1 ring-[#459492]/20 scale-[1.01]"
                        : "bg-white border-[#E2E6EA] shadow-sm hover:border-[#459492]/30 hover:shadow-md hover:scale-[1.01]"
                    }`}
                    style={{ animationDelay: `${100 + index * 50}ms`, animationFillMode: "forwards" }}
                    onClick={() => toggleArrayItem("goals", goal.id)}
                  >
                    <CardContent className="p-4 flex items-center gap-4">
                      <div className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-200 ${
                        selected ? "bg-[#459492] text-white" : "bg-[#F0F7F7] text-[#459492]"
                      }`}>
                        <Icon className="w-5 h-5" />
                      </div>
                      <span className="flex-1 font-medium text-[#141E24]">{goal.label}</span>
                      {selected && <Check className="w-5 h-5 text-[#459492]" />}
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}

          {STEPS[currentStep].id === "availability" && (
            <div className="grid gap-3">
              {TIME_SLOTS.map((slot, index) => {
                const Icon = slot.icon;
                const selected = profile.preferred_times.includes(slot.id);
                return (
                  <Card
                    key={slot.id}
                    className={`cursor-pointer transition-all duration-200 opacity-0 animate-fade-in rounded-xl btn-press ${
                      selected
                        ? "bg-[#F0F7F7] border-[#459492] shadow-md ring-1 ring-[#459492]/20 scale-[1.01]"
                        : "bg-white border-[#E2E6EA] shadow-sm hover:border-[#459492]/30 hover:shadow-md hover:scale-[1.01]"
                    }`}
                    style={{ animationDelay: `${100 + index * 50}ms`, animationFillMode: "forwards" }}
                    onClick={() => toggleArrayItem("preferred_times", slot.id)}
                  >
                    <CardContent className="p-4 flex items-center gap-4">
                      <div className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-200 ${
                        selected ? "bg-[#459492] text-white" : "bg-[#F0F7F7] text-[#459492]"
                      }`}>
                        <Icon className="w-5 h-5" />
                      </div>
                      <div className="flex-1">
                        <p className="font-medium text-[#141E24]">{slot.label}</p>
                        <p className="text-sm text-[#667085]">{slot.sublabel}</p>
                      </div>
                      {selected && <Check className="w-5 h-5 text-[#459492]" />}
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}

          {STEPS[currentStep].id === "energy" && (
            <div className="grid gap-3">
              {ENERGY_LEVELS.map((level, index) => {
                const Icon = level.icon;
                const selected = profile.energy_level === level.id;
                return (
                  <Card
                    key={level.id}
                    className={`cursor-pointer transition-all duration-200 opacity-0 animate-fade-in rounded-xl btn-press ${
                      selected
                        ? "bg-[#F0F7F7] border-[#459492] shadow-md ring-1 ring-[#459492]/20 scale-[1.01]"
                        : "bg-white border-[#E2E6EA] shadow-sm hover:border-[#459492]/30 hover:shadow-md hover:scale-[1.01]"
                    }`}
                    style={{ animationDelay: `${100 + index * 50}ms`, animationFillMode: "forwards" }}
                    onClick={() => setProfile((p) => ({ ...p, energy_level: level.id }))}
                  >
                    <CardContent className="p-4 flex items-center gap-4">
                      <div className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-200 ${
                        selected ? "bg-[#459492] text-white" : "bg-[#F0F7F7] text-[#459492]"
                      }`}>
                        <Icon className="w-5 h-5" />
                      </div>
                      <div className="flex-1">
                        <p className="font-medium text-[#141E24]">{level.label}</p>
                        <p className="text-sm text-[#667085]">{level.description}</p>
                      </div>
                      {selected && <Check className="w-5 h-5 text-[#459492]" />}
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}

          {STEPS[currentStep].id === "interests" && (
            <div className="grid grid-cols-2 gap-3">
              {INTERESTS.map((interest, index) => {
                const selected = profile.interests.includes(interest.id);
                return (
                  <Card
                    key={interest.id}
                    className={`cursor-pointer transition-all duration-200 opacity-0 animate-fade-in rounded-xl btn-press ${
                      selected
                        ? "bg-[#F0F7F7] border-[#459492] shadow-md ring-1 ring-[#459492]/20 scale-[1.01]"
                        : "bg-white border-[#E2E6EA] shadow-sm hover:border-[#459492]/30 hover:shadow-md hover:scale-[1.01]"
                    }`}
                    style={{ animationDelay: `${100 + index * 50}ms`, animationFillMode: "forwards" }}
                    onClick={() => toggleArrayItem("interests", interest.id)}
                  >
                    <CardContent className="p-4 text-center">
                      <div className={`w-10 h-10 rounded-xl flex items-center justify-center mx-auto mb-2 transition-all duration-200 ${interest.color}`}>
                        {selected ? <Check className="w-5 h-5" /> : <Sparkles className="w-5 h-5" />}
                      </div>
                      <p className="text-sm font-medium text-[#141E24]">{interest.label}</p>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </div>
      </main>

      {/* Footer Navigation */}
      <div className="fixed bottom-0 left-0 right-0 bg-white/80 backdrop-blur-md border-t border-[#E2E6EA] p-4">
        <div className="max-w-lg mx-auto flex gap-3">
          {currentStep > 0 && (
            <Button
              variant="outline"
              onClick={handleBack}
              className="h-12 rounded-xl px-6 bg-white border-[#E2E6EA] text-[#141E24] hover:bg-[#F8FAFB] shadow-sm hover:shadow-md transition-all duration-200 btn-press"
            >
              <ChevronLeft className="w-5 h-5 mr-1" />
              Retour
            </Button>
          )}
          <Button
            onClick={handleNext}
            className="flex-1 h-12 rounded-xl shadow-md bg-gradient-to-r from-[#459492] to-[#55B3AE] text-white hover:shadow-lg hover:brightness-105 transition-all duration-200 btn-press"
            disabled={!canAdvance() || isSubmitting}
          >
            {isSubmitting ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : currentStep === STEPS.length - 1 ? (
              <>
                Terminer
                <Check className="w-5 h-5 ml-2" />
              </>
            ) : (
              <>
                Suivant
                <ChevronRight className="w-5 h-5 ml-2" />
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
