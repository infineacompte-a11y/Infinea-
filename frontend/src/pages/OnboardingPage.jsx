import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Timer,
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

const GOALS = [
  { id: "learn_new_skills", labelKey: "onboarding.goals.learnNewSkills", icon: BookOpen },
  { id: "boost_productivity", labelKey: "onboarding.goals.boostProductivity", icon: Target },
  { id: "reduce_stress", labelKey: "onboarding.goals.reduceStress", icon: Heart },
  { id: "build_habits", labelKey: "onboarding.goals.buildHabits", icon: Sparkles },
];

const TIME_SLOTS = [
  { id: "morning", labelKey: "onboarding.timeSlots.morning", sublabelKey: "onboarding.timeSlots.morningSub", icon: Sunrise },
  { id: "afternoon", labelKey: "onboarding.timeSlots.afternoon", sublabelKey: "onboarding.timeSlots.afternoonSub", icon: Sun },
  { id: "evening", labelKey: "onboarding.timeSlots.evening", sublabelKey: "onboarding.timeSlots.eveningSub", icon: Moon },
];

const ENERGY_LEVELS = [
  { id: "low", labelKey: "onboarding.energy.low", descKey: "onboarding.energy.lowDesc", icon: BatteryLow },
  { id: "medium", labelKey: "onboarding.energy.medium", descKey: "onboarding.energy.mediumDesc", icon: BatteryMedium },
  { id: "high", labelKey: "onboarding.energy.high", descKey: "onboarding.energy.highDesc", icon: BatteryFull },
];

const INTERESTS = [
  { id: "learning", color: "text-blue-500 bg-blue-500/10" },
  { id: "productivity", color: "text-amber-500 bg-amber-500/10" },
  { id: "well_being", color: "text-emerald-500 bg-emerald-500/10" },
  { id: "creativity", color: "text-purple-500 bg-purple-500/10" },
  { id: "fitness", color: "text-red-500 bg-red-500/10" },
  { id: "mindfulness", color: "text-cyan-500 bg-cyan-500/10" },
  { id: "leadership", color: "text-indigo-500 bg-indigo-500/10" },
  { id: "finance", color: "text-green-500 bg-green-500/10" },
  { id: "relations", color: "text-pink-500 bg-pink-500/10" },
  { id: "mental_health", color: "text-teal-500 bg-teal-500/10" },
  { id: "entrepreneurship", color: "text-orange-500 bg-orange-500/10" },
];

export default function OnboardingPage() {
  const { t } = useTranslation();
  const { user, setUser } = useAuth();
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [welcomeMessage, setWelcomeMessage] = useState(null);

  const STEPS = [
    { id: "goals", title: t("onboarding.steps.goalsTitle"), subtitle: t("onboarding.steps.goalsSubtitle") },
    { id: "availability", title: t("onboarding.steps.availabilityTitle"), subtitle: t("onboarding.steps.availabilitySubtitle") },
    { id: "energy", title: t("onboarding.steps.energyTitle"), subtitle: t("onboarding.steps.energySubtitle") },
    { id: "interests", title: t("onboarding.steps.interestsTitle"), subtitle: t("onboarding.steps.interestsSubtitle") },
  ];

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
      setWelcomeMessage(data.welcome_message || data.first_recommendation || t("onboarding.defaultWelcome"));
    } catch (error) {
      toast.error(t("onboarding.errorSave"));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFinish = () => {
    navigate("/dashboard");
  };

  // Welcome screen after onboarding complete
  if (welcomeMessage) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <div className="max-w-md w-full text-center animate-fade-in">
          <div className="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-6">
            <Sparkles className="w-10 h-10 text-primary" />
          </div>
          <h1 className="font-heading text-3xl font-bold mb-4">
            {t("onboarding.welcomeTitle", { name: user?.name?.split(" ")[0] || t("onboarding.defaultUser") })}
          </h1>
          <Card className="mb-8 text-left">
            <CardContent className="p-6">
              <p className="text-sm leading-relaxed">{welcomeMessage}</p>
            </CardContent>
          </Card>
          <Button onClick={handleFinish} className="w-full h-12 rounded-xl">
            {t("onboarding.startActions")}
            <ChevronRight className="w-5 h-5 ml-2" />
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 glass">
        <div className="flex items-center justify-between px-4 h-16">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
              <Timer className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="font-heading text-lg font-semibold">InFinea</span>
          </div>
          <Button variant="ghost" size="sm" onClick={() => navigate("/dashboard")}>
            {t("onboarding.skip")}
          </Button>
        </div>
      </header>

      {/* Progress Bar */}
      <div className="fixed top-16 left-0 right-0 z-40 h-1 bg-border">
        <div
          className="h-full bg-primary transition-all duration-300"
          style={{ width: `${((currentStep + 1) / STEPS.length) * 100}%` }}
        />
      </div>

      {/* Main Content */}
      <main className="flex-1 flex items-center justify-center p-4 pt-24 pb-32">
        <div className="max-w-lg w-full animate-fade-in">
          {/* Step Header */}
          <div className="text-center mb-8">
            <Badge variant="secondary" className="mb-4">
              {currentStep + 1} / {STEPS.length}
            </Badge>
            <h1 className="font-heading text-2xl font-bold mb-2">
              {STEPS[currentStep].title}
            </h1>
            <p className="text-muted-foreground">{STEPS[currentStep].subtitle}</p>
          </div>

          {/* Step Content */}
          {STEPS[currentStep].id === "goals" && (
            <div className="grid gap-3">
              {GOALS.map((goal) => {
                const Icon = goal.icon;
                const selected = profile.goals.includes(goal.id);
                return (
                  <Card
                    key={goal.id}
                    className={`cursor-pointer transition-all ${
                      selected ? "border-primary bg-primary/5" : "hover:border-primary/50"
                    }`}
                    onClick={() => toggleArrayItem("goals", goal.id)}
                  >
                    <CardContent className="p-4 flex items-center gap-4">
                      <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                        selected ? "bg-primary text-primary-foreground" : "bg-muted"
                      }`}>
                        <Icon className="w-5 h-5" />
                      </div>
                      <span className="flex-1 font-medium">{t(goal.labelKey)}</span>
                      {selected && <Check className="w-5 h-5 text-primary" />}
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}

          {STEPS[currentStep].id === "availability" && (
            <div className="grid gap-3">
              {TIME_SLOTS.map((slot) => {
                const Icon = slot.icon;
                const selected = profile.preferred_times.includes(slot.id);
                return (
                  <Card
                    key={slot.id}
                    className={`cursor-pointer transition-all ${
                      selected ? "border-primary bg-primary/5" : "hover:border-primary/50"
                    }`}
                    onClick={() => toggleArrayItem("preferred_times", slot.id)}
                  >
                    <CardContent className="p-4 flex items-center gap-4">
                      <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                        selected ? "bg-primary text-primary-foreground" : "bg-muted"
                      }`}>
                        <Icon className="w-5 h-5" />
                      </div>
                      <div className="flex-1">
                        <p className="font-medium">{t(slot.labelKey)}</p>
                        <p className="text-sm text-muted-foreground">{t(slot.sublabelKey)}</p>
                      </div>
                      {selected && <Check className="w-5 h-5 text-primary" />}
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}

          {STEPS[currentStep].id === "energy" && (
            <div className="grid gap-3">
              {ENERGY_LEVELS.map((level) => {
                const Icon = level.icon;
                const selected = profile.energy_level === level.id;
                return (
                  <Card
                    key={level.id}
                    className={`cursor-pointer transition-all ${
                      selected ? "border-primary bg-primary/5" : "hover:border-primary/50"
                    }`}
                    onClick={() => setProfile((p) => ({ ...p, energy_level: level.id }))}
                  >
                    <CardContent className="p-4 flex items-center gap-4">
                      <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                        selected ? "bg-primary text-primary-foreground" : "bg-muted"
                      }`}>
                        <Icon className="w-5 h-5" />
                      </div>
                      <div className="flex-1">
                        <p className="font-medium">{t(level.labelKey)}</p>
                        <p className="text-sm text-muted-foreground">{t(level.descKey)}</p>
                      </div>
                      {selected && <Check className="w-5 h-5 text-primary" />}
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}

          {STEPS[currentStep].id === "interests" && (
            <div className="grid grid-cols-2 gap-3">
              {INTERESTS.map((interest) => {
                const selected = profile.interests.includes(interest.id);
                return (
                  <Card
                    key={interest.id}
                    className={`cursor-pointer transition-all ${
                      selected ? "border-primary bg-primary/5" : "hover:border-primary/50"
                    }`}
                    onClick={() => toggleArrayItem("interests", interest.id)}
                  >
                    <CardContent className="p-4 text-center">
                      <div className={`w-10 h-10 rounded-xl flex items-center justify-center mx-auto mb-2 ${interest.color}`}>
                        {selected ? <Check className="w-5 h-5" /> : <Sparkles className="w-5 h-5" />}
                      </div>
                      <p className="text-sm font-medium">{t(`categories.${interest.id}`)}</p>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </div>
      </main>

      {/* Footer Navigation */}
      <div className="fixed bottom-0 left-0 right-0 glass p-4">
        <div className="max-w-lg mx-auto flex gap-3">
          {currentStep > 0 && (
            <Button variant="outline" onClick={handleBack} className="h-12 rounded-xl px-6">
              <ChevronLeft className="w-5 h-5 mr-1" />
              {t("common.back")}
            </Button>
          )}
          <Button
            onClick={handleNext}
            className="flex-1 h-12 rounded-xl"
            disabled={!canAdvance() || isSubmitting}
          >
            {isSubmitting ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : currentStep === STEPS.length - 1 ? (
              <>
                {t("onboarding.finish")}
                <Check className="w-5 h-5 ml-2" />
              </>
            ) : (
              <>
                {t("common.next")}
                <ChevronRight className="w-5 h-5 ml-2" />
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
