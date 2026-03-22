import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import {
  Zap,
  BatteryLow,
  BatteryMedium,
  BatteryFull,
  BookOpen,
  Target,
  Heart,
  ChevronRight,
  TrendingUp,
  Flame,
  Sparkles,
  Loader2,
  Brain,
  Crown,
  Shield,
  Palette,
  Dumbbell,
  Leaf,
  Users,
  MessageCircle,
  Rocket,
  Calendar,
} from "lucide-react";
import { toast } from "sonner";
import { API, useAuth, authFetch } from "@/App";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import SlotCard from "@/components/SlotCard";
import AICoachCard from "@/components/AICoachCard";
import Sidebar from "@/components/Sidebar";
import SmartPredictionCard from "@/components/SmartPredictionCard";
import RecapCard from "@/components/RecapCard";

const categoryIcons = {
  learning: BookOpen,
  productivity: Target,
  well_being: Heart,
  creativity: Palette,
  fitness: Dumbbell,
  mindfulness: Leaf,
  leadership: Users,
  finance: TrendingUp,
  relations: MessageCircle,
  mental_health: Brain,
  entrepreneurship: Rocket,
};

const categoryColors = {
  learning: "text-[#459492] bg-[#459492]/40",
  productivity: "text-[#E48C75] bg-[#E48C75]/40",
  well_being: "text-[#5DB786] bg-[#5DB786]/40",
  creativity: "text-[#55B3AE] bg-[#55B3AE]/40",
  fitness: "text-[#E48C75] bg-[#E48C75]/40",
  mindfulness: "text-[#459492] bg-[#459492]/40",
  leadership: "text-[#7B8FA1] bg-[#7B8FA1]/40",
  finance: "text-[#2E9B6A] bg-[#2E9B6A]/40",
  relations: "text-[#C4806E] bg-[#C4806E]/40",
  mental_health: "text-[#6EAAA8] bg-[#6EAAA8]/40",
  entrepreneurship: "text-[#E48C75] bg-[#E48C75]/40",
};

const categoryLabels = {
  learning: "Apprentissage",
  productivity: "Productivité",
  well_being: "Bien-être",
  creativity: "Créativité",
  fitness: "Fitness",
  mindfulness: "Mindfulness",
  leadership: "Leadership",
  finance: "Finance",
  relations: "Relations",
  mental_health: "Santé mentale",
  entrepreneurship: "Entrepreneuriat",
};

export default function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [availableTime, setAvailableTime] = useState(5);
  const [energyLevel, setEnergyLevel] = useState("medium");
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [suggestions, setSuggestions] = useState(null);
  const [nextSlot, setNextSlot] = useState(null);

  useEffect(() => {
    fetchNextSlot();
  }, []);

  const fetchNextSlot = async () => {
    try {
      const response = await authFetch(`${API}/slots/next`);
      if (response.ok) {
        const data = await response.json();
        setNextSlot(data.slot);
      }
    } catch (error) {
      console.log("No slot available");
    }
  };

  const getSuggestions = async () => {
    setIsLoading(true);
    try {
      const response = await authFetch(`${API}/suggestions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          available_time: availableTime,
          energy_level: energyLevel,
          preferred_category: selectedCategory,
        }),
      });

      if (!response.ok) throw new Error("Erreur de suggestion");

      const data = await response.json();
      setSuggestions(data);
    } catch (error) {
      toast.error("Impossible de charger les suggestions");
    } finally {
      setIsLoading(false);
    }
  };

  const startSession = async (actionId) => {
    try {
      const response = await authFetch(`${API}/sessions/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action_id: actionId }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Erreur");
      }

      const data = await response.json();
      navigate(`/session/${data.session_id}`, { state: { session: data } });
    } catch (error) {
      toast.error(error.message);
    }
  };

  const EnergyIcon = energyLevel === "low" ? BatteryLow : energyLevel === "medium" ? BatteryMedium : BatteryFull;

  return (
    <div className="min-h-screen app-bg-mesh">
      <Sidebar />

      {/* Main Content */}
      <main className="lg:ml-64 pt-14 lg:pt-0 pb-8">
        {/* === Dark Teal Header Section — Revolut-style contrast === */}
        <div className="section-dark-header px-4 lg:px-8 pt-8 lg:pt-10 pb-8">
          <div className="max-w-5xl mx-auto">
            {/* Welcome */}
            <div className="opacity-0 animate-fade-in" style={{ animationDelay: "0ms" }}>
              <div className="flex items-center gap-3 mb-1">
                <h1 className="text-display text-3xl lg:text-4xl font-semibold text-white" data-testid="dashboard-welcome">
                  Bonjour, {user?.name?.split(" ")[0] || "Utilisateur"}
                </h1>
                {user?.subscription_tier === "premium" && (
                  <span className="pill-badge bg-white/10 border border-white/20 text-white text-sm">
                    <Crown className="w-4 h-4 text-[#55B3AE]" />
                    Premium
                  </span>
                )}
              </div>
              <p className="text-white/60 text-sm">
                Que pouvez-vous accomplir maintenant ?
              </p>
            </div>

            {/* Stats on dark — glass cards */}
            <div className="grid grid-cols-3 gap-3 mt-6">
              <div className="card-on-dark rounded-xl p-3 opacity-0 animate-fade-in" style={{ animationDelay: "100ms" }}>
                <div className="flex items-center gap-2.5">
                  <div className="w-9 h-9 rounded-lg bg-[#5DB786]/40 flex items-center justify-center">
                    <TrendingUp className="w-4 h-4 text-[#5DB786]" />
                  </div>
                  <div>
                    <p className="text-xl font-sans font-semibold tracking-tight font-bold tabular-nums text-white">{user?.total_time_invested || 0}</p>
                    <p className="text-[10px] text-white/50 uppercase tracking-wider">min investies</p>
                  </div>
                </div>
              </div>
              <div className="card-on-dark rounded-xl p-3 opacity-0 animate-fade-in" style={{ animationDelay: "150ms" }}>
                <div className="flex items-center gap-2.5">
                  <div className="w-9 h-9 rounded-lg bg-[#E48C75]/40 flex items-center justify-center">
                    <Flame className="w-4 h-4 text-[#E48C75]" />
                  </div>
                  <div>
                    <div className="flex items-center gap-1.5">
                      <p className="text-xl font-sans font-semibold tracking-tight font-bold tabular-nums text-white">{user?.streak_days || 0}</p>
                      {user?.subscription_tier === "premium" && (
                        <Shield className="w-3.5 h-3.5 text-[#5DB786]" title="Streak Shield actif" />
                      )}
                    </div>
                    <p className="text-[10px] text-white/50 uppercase tracking-wider">jours streak</p>
                  </div>
                </div>
              </div>
              <div className="card-on-dark rounded-xl p-3 opacity-0 animate-fade-in" style={{ animationDelay: "200ms" }}>
                <div className="flex items-center gap-2.5">
                  <div className="w-9 h-9 rounded-lg bg-[#459492]/40 flex items-center justify-center">
                    <Sparkles className="w-4 h-4 text-[#55B3AE]" />
                  </div>
                  <div>
                    <p className="text-xl font-sans font-semibold tracking-tight font-bold tabular-nums text-white">
                      {user?.subscription_tier === "premium" ? "Pro" : "Free"}
                    </p>
                    <p className="text-[10px] text-white/50 uppercase tracking-wider">abonnement</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* === Content below header === */}
        <div className="px-4 lg:px-8 -mt-4">
          <div className="max-w-5xl mx-auto space-y-6 pt-2">

          {/* Recap Card */}
          <div className="opacity-0 animate-fade-in" style={{ animationDelay: "50ms" }}>
            <RecapCard />
          </div>

          {/* AI Coach — first thing the user sees */}
          <div className="opacity-0 animate-fade-in relative" style={{ animationDelay: "250ms" }}>
            <div className="absolute -inset-6 rounded-3xl bg-gradient-to-r from-[#459492]/30 via-[#55B3AE]/20 to-[#5DB786]/24 blur-2xl pointer-events-none animate-pulse-glow" />
            <div className="relative">
              <AICoachCard onStartAction={startSession} />
            </div>
          </div>

          {/* Smart Prediction Module */}
          <div className="opacity-0 animate-fade-in" style={{ animationDelay: "300ms" }}>
            <SmartPredictionCard />
          </div>

          {/* Next Slot Card */}
          {nextSlot && (
            <div className="opacity-0 animate-fade-in" style={{ animationDelay: "350ms" }}>
              <h2 className="text-sm font-medium text-[#667085] mb-3">
                📅 Prochain créneau libre détecté
              </h2>
              <SlotCard
                slot={nextSlot}
                onDismiss={() => setNextSlot(null)}
                onRefresh={fetchNextSlot}
              />
            </div>
          )}

          {/* Main Action Card */}
          <Card
            className="opacity-0 animate-fade-in rounded-2xl bg-white shadow-sm shadow-[#275255]/5 border border-[#E2E6EA] overflow-hidden"
            style={{ animationDelay: "400ms" }}
          >
            <CardHeader className="relative">
              <div className="absolute inset-0 bg-gradient-to-r from-[#459492]/[0.14] via-[#55B3AE]/[0.06] to-transparent pointer-events-none" />
              <CardTitle className="relative font-sans font-semibold tracking-tight text-xl flex items-center gap-2 text-[#141E24]">
                <Zap className="w-5 h-5 text-[#459492]" />
                Configurez votre micro-action
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-5">
              {/* Time Slider */}
              <div>
                <div className="flex items-center justify-between mb-4">
                  <span className="font-sans font-semibold tracking-tight text-sm font-semibold uppercase tracking-wider text-[#667085]">Temps disponible</span>
                  <Badge variant="secondary" className="font-mono">
                    {availableTime} min
                  </Badge>
                </div>
                <Slider
                  value={[availableTime]}
                  onValueChange={(v) => setAvailableTime(v[0])}
                  min={2}
                  max={15}
                  step={1}
                  className="w-full"
                  data-testid="time-slider"
                />
                <div className="flex justify-between text-xs text-[#667085] mt-2">
                  <span>2 min</span>
                  <span>15 min</span>
                </div>
              </div>

              {/* Energy Level */}
              <div>
                <span className="font-sans font-semibold tracking-tight text-sm font-semibold uppercase tracking-wider text-[#667085] block mb-4">Niveau d'énergie</span>
                <div className="flex gap-2 sm:gap-3">
                  {[
                    { value: "low", label: "Basse", icon: BatteryLow, color: "text-[#459492]", bg: "bg-[#459492]/40", border: "border-[#459492]", ring: "ring-[#459492]" },
                    { value: "medium", label: "Moyenne", icon: BatteryMedium, color: "text-[#E48C75]", bg: "bg-[#E48C75]/40", border: "border-[#E48C75]", ring: "ring-[#E48C75]" },
                    { value: "high", label: "Haute", icon: BatteryFull, color: "text-[#5DB786]", bg: "bg-[#5DB786]/40", border: "border-[#5DB786]", ring: "ring-[#5DB786]" },
                  ].map((level) => (
                    <button
                      key={level.value}
                      onClick={() => setEnergyLevel(level.value)}
                      className={`flex-1 flex items-center justify-center gap-1.5 sm:gap-2 py-3 px-2 sm:px-4 rounded-xl border btn-press transition-all duration-200 ${
                        energyLevel === level.value
                          ? `${level.border} ${level.bg} ${level.color} ring-2 ring-offset-2 ring-offset-white ${level.ring} shadow-md scale-[1.02]`
                          : "border-[#E2E6EA] text-[#667085] hover:border-[#459492]/50 hover:bg-[#F8FAFB] hover:scale-[1.02]"
                      }`}
                      data-testid={`energy-${level.value}-btn`}
                    >
                      <level.icon className="w-4 h-4 sm:w-5 sm:h-5 shrink-0" />
                      <span className="text-xs sm:text-sm">{level.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Category Filter */}
              <div>
                <span className="font-sans font-semibold tracking-tight text-sm font-semibold uppercase tracking-wider text-[#667085] block mb-4">Catégorie (optionnel)</span>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
                  {Object.entries(categoryLabels).map(([key, label]) => {
                    const Icon = categoryIcons[key];
                    return (
                      <button
                        key={key}
                        onClick={() => setSelectedCategory(selectedCategory === key ? null : key)}
                        className={`flex items-center gap-2 py-2 px-3 rounded-xl border hover:scale-[1.02] btn-press transition-all duration-200 ${
                          selectedCategory === key
                            ? `${categoryColors[key]} border-[#459492] ring-2 ring-[#459492]/50 shadow-md`
                            : "bg-[#F8FAFB] border-[#E2E6EA] text-[#667085] hover:border-[#459492]/50 hover:bg-[#F0F7F7]"
                        }`}
                        data-testid={`category-${key}-btn`}
                      >
                        <Icon className="w-4 h-4 shrink-0" />
                        <span className="text-sm truncate">{label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Get Suggestions Button */}
              <Button
                onClick={getSuggestions}
                className="w-full h-12 text-base font-semibold rounded-xl bg-gradient-to-r from-[#459492] to-[#55B3AE] hover:from-[#55B3AE] hover:to-[#459492] text-white shadow-md shadow-[#459492]/20 btn-press transition-all duration-300"
                disabled={isLoading}
                data-testid="get-suggestions-btn"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin mr-2" />
                    Chargement...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-5 h-5 mr-2" />
                    Obtenir des suggestions IA
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Suggestions Results */}
          {suggestions && (
            <div
              className="opacity-0 animate-fade-in space-y-4"
              style={{ animationDelay: "450ms" }}
              data-testid="suggestions-container"
            >
              <div className="flex items-center justify-between">
                <h2 className="font-sans font-semibold tracking-tight text-xl font-semibold text-[#141E24]">Suggestions pour vous</h2>
                <span className="text-sm text-[#667085]">{availableTime} min • Énergie {energyLevel}</span>
              </div>

              {suggestions.reasoning && (
                <Card className="bg-gradient-to-r from-[#459492]/[0.18] to-[#55B3AE]/[0.08] border-[#459492]/25 rounded-2xl">
                  <CardContent className="p-4 flex items-start gap-3">
                    <Sparkles className="w-5 h-5 text-[#459492] mt-0.5" />
                    <p className="text-sm text-[#141E24]">{suggestions.reasoning}</p>
                  </CardContent>
                </Card>
              )}

              {user?.subscription_tier !== "premium" && (
                <Link to="/pricing" className="block">
                  <Card className="bg-gradient-to-r from-[#459492]/5 to-[#55B3AE]/5 border-[#459492]/20 hover:border-[#459492]/40 btn-press transition-all cursor-pointer rounded-2xl">
                    <CardContent className="p-3 flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Crown className="w-5 h-5 text-[#459492]" />
                        <p className="text-sm">
                          <span className="font-medium text-[#141E24]">Passez Premium</span>
                          <span className="text-[#667085]"> — IA avancée qui apprend de vos habitudes</span>
                        </p>
                      </div>
                      <ChevronRight className="w-4 h-4 text-[#667085]" />
                    </CardContent>
                  </Card>
                </Link>
              )}

              <div className="grid gap-4 stagger-enter">
                {suggestions.recommended_actions?.map((action, i) => {
                  const Icon = categoryIcons[action.category] || Sparkles;
                  return (
                    <Card
                      key={action.action_id}
                      className={`group cursor-pointer rounded-2xl bg-white shadow-sm border border-[#E2E6EA] border-l-[3px] border-l-transparent hover:border-l-[#459492] hover:shadow-md hover:shadow-[#459492]/8 hover:border-[#459492]/30 hover:-translate-y-0.5 btn-press transition-all duration-200 ${i === 0 ? "border-[#459492]/30 border-l-[#459492] shadow-md shadow-[#459492]/8" : ""}`}
                      onClick={() => startSession(action.action_id)}
                      data-testid={`action-card-${action.action_id}`}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex items-start gap-4">
                            <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${categoryColors[action.category]}`}>
                              <Icon className="w-6 h-6" />
                            </div>
                            <div>
                              <div className="flex items-center gap-2 mb-1 flex-wrap">
                                <h3 className="font-medium text-[#141E24]">{action.title}</h3>
                                {action.is_premium && (
                                  <Badge variant="secondary" className="text-xs">Premium</Badge>
                                )}
                                {i === 0 && (
                                  <Badge className="text-xs bg-[#459492]/40 text-[#275255] border border-[#459492]/30 shadow-sm">Recommandé</Badge>
                                )}
                                {suggestions.scoring_metadata?.scored && (
                                  <Badge variant="outline" className="text-xs border-[#459492]/40 text-[#459492]">Personnalisé</Badge>
                                )}
                              </div>
                              <p className="text-sm text-[#667085] mb-2">{action.description}</p>
                              <div className="flex items-center gap-3 text-xs text-[#667085]">
                                <span className="bg-[#F8FAFB] border border-[#E2E6EA] rounded-lg px-2 py-0.5">{action.duration_min}-{action.duration_max} min</span>
                                <span>•</span>
                                <span className="bg-[#F8FAFB] border border-[#E2E6EA] rounded-lg px-2 py-0.5">{categoryLabels[action.category]}</span>
                              </div>
                            </div>
                          </div>
                          <ChevronRight className="w-5 h-5 text-[#667085] shrink-0 group-hover:translate-x-1 transition-transform" />
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </div>
          )}

          {/* Quick Actions */}
          {!suggestions && (
            <div className="opacity-0 animate-fade-in" style={{ animationDelay: "450ms" }}>
              <h2 className="font-sans font-semibold tracking-tight text-lg font-semibold text-[#667085] mb-4">Explorez nos catégories</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 stagger-enter">
                {Object.entries(categoryLabels).map(([key, label]) => {
                  const Icon = categoryIcons[key];
                  return (
                    <Card
                      key={key}
                      className="bg-white cursor-pointer rounded-2xl shadow-sm border border-[#E2E6EA] border-l-[3px] border-l-transparent hover:border-l-[#459492] hover:border-[#459492]/30 hover:shadow-md hover:shadow-[#459492]/5 hover:-translate-y-0.5 btn-press transition-all duration-200"
                      onClick={() => {
                        setSelectedCategory(key);
                        getSuggestions();
                      }}
                      data-testid={`quick-action-${key}`}
                    >
                      <CardContent className="p-6">
                        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${categoryColors[key]} mb-4`}>
                          <Icon className="w-5 h-5" />
                        </div>
                        <h3 className="font-sans font-semibold tracking-tight text-lg font-medium mb-2 text-[#141E24]">{label}</h3>
                        <p className="text-sm text-[#667085]">
                          {key === "learning" && "Vocabulaire, lecture, concepts..."}
                          {key === "productivity" && "Planning, emails, brainstorm..."}
                          {key === "well_being" && "Respiration, méditation, étirements..."}
                        </p>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </div>
          )}
          </div>
        </div>
      </main>
    </div>
  );
}
