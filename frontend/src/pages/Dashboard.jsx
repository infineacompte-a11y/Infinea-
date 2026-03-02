import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import {
  Timer,
  Zap,
  Battery,
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
  LayoutGrid,
  BarChart3,
  User,
  LogOut,
  X,
  Loader2,
  Award,
  Bell,
  Building2,
  Calendar,
  Brain,
  Crown,
  Shield,
  Palette,
  Dumbbell,
  Leaf,
  Users,
  MessageCircle,
  Rocket,
  Trophy,
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
import AppSidebar from "@/components/AppSidebar";
import AICoachCard from "@/components/AICoachCard";

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
  learning: "text-blue-500 bg-blue-500/10",
  productivity: "text-amber-500 bg-amber-500/10",
  well_being: "text-emerald-500 bg-emerald-500/10",
  creativity: "text-purple-500 bg-purple-500/10",
  fitness: "text-red-500 bg-red-500/10",
  mindfulness: "text-cyan-500 bg-cyan-500/10",
  leadership: "text-indigo-500 bg-indigo-500/10",
  finance: "text-green-500 bg-green-500/10",
  relations: "text-pink-500 bg-pink-500/10",
  mental_health: "text-teal-500 bg-teal-500/10",
  entrepreneurship: "text-orange-500 bg-orange-500/10",
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
  const { user, logout } = useAuth();
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

  const handleLogout = async () => {
    await logout();
    navigate("/login");
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
    <div className="min-h-screen bg-background">
      <AppSidebar activePage="dashboard" onLogout={handleLogout} />

      {/* Main Content */}
      <main className="lg:ml-64 pt-20 lg:pt-8 px-4 lg:px-8 pb-8">
        <div className="max-w-5xl mx-auto">
          {/* Welcome Header */}
          <div className="mb-8">
            <div className="flex items-center gap-3 mb-2">
              <h1 className="font-heading text-3xl font-semibold" data-testid="dashboard-welcome">
                Bonjour, {user?.name?.split(" ")[0] || "Utilisateur"} 👋
              </h1>
              {user?.subscription_tier === "premium" && (
                <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-gradient-to-r from-amber-500/20 to-orange-500/20 text-amber-500 text-sm font-medium">
                  <Crown className="w-4 h-4" />
                  Premium
                </span>
              )}
            </div>
            <p className="text-muted-foreground">
              Que pouvez-vous accomplir maintenant ?
            </p>
          </div>

          {/* Next Slot Card */}
          {nextSlot && (
            <div className="mb-8">
              <h2 className="text-sm font-medium text-muted-foreground mb-3">
                📅 Prochain créneau libre détecté
              </h2>
              <SlotCard 
                slot={nextSlot} 
                onDismiss={() => setNextSlot(null)} 
                onRefresh={fetchNextSlot} 
              />
            </div>
          )}

          {/* Stats Overview */}
          <div className="grid grid-cols-3 gap-4 mb-8">
            <Card className="stat-card">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                    <TrendingUp className="w-5 h-5 text-primary" />
                  </div>
                  <div>
                    <p className="text-2xl font-heading font-bold">{user?.total_time_invested || 0}</p>
                    <p className="text-xs text-muted-foreground">min investies</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="stat-card">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-amber-500/10 flex items-center justify-center">
                    <Flame className="w-5 h-5 text-amber-500" />
                  </div>
                  <div>
                    <div className="flex items-center gap-1.5">
                      <p className="text-2xl font-heading font-bold">{user?.streak_days || 0}</p>
                      {user?.subscription_tier === "premium" && (
                        <Shield className="w-4 h-4 text-emerald-500" title="Streak Shield actif" />
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground">jours streak</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="stat-card">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center">
                    <Sparkles className="w-5 h-5 text-emerald-500" />
                  </div>
                  <div>
                    <p className="text-2xl font-heading font-bold">
                      {user?.subscription_tier === "premium" ? "Pro" : "Free"}
                    </p>
                    <p className="text-xs text-muted-foreground">abonnement</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* AI Coach */}
          <AICoachCard />

          {/* Main Action Card */}
          <Card className="mb-8 bento-item">
            <CardHeader>
              <CardTitle className="font-heading text-xl flex items-center gap-2">
                <Zap className="w-5 h-5 text-primary" />
                Configurez votre micro-action
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Time Slider */}
              <div>
                <div className="flex items-center justify-between mb-4">
                  <span className="text-sm text-muted-foreground">Temps disponible</span>
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
                <div className="flex justify-between text-xs text-muted-foreground mt-2">
                  <span>2 min</span>
                  <span>15 min</span>
                </div>
              </div>

              {/* Energy Level */}
              <div>
                <span className="text-sm text-muted-foreground block mb-4">Niveau d'énergie</span>
                <div className="flex gap-3">
                  {[
                    { value: "low", label: "Basse", icon: BatteryLow },
                    { value: "medium", label: "Moyenne", icon: BatteryMedium },
                    { value: "high", label: "Haute", icon: BatteryFull },
                  ].map((level) => (
                    <button
                      key={level.value}
                      onClick={() => setEnergyLevel(level.value)}
                      className={`flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-xl border transition-colors ${
                        energyLevel === level.value
                          ? "border-primary bg-primary/10 text-primary"
                          : "border-border hover:border-primary/50"
                      }`}
                      data-testid={`energy-${level.value}-btn`}
                    >
                      <level.icon className="w-5 h-5" />
                      <span className="text-sm">{level.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Category Filter */}
              <div>
                <span className="text-sm text-muted-foreground block mb-4">Catégorie (optionnel)</span>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(categoryLabels).map(([key, label]) => {
                    const Icon = categoryIcons[key];
                    return (
                      <button
                        key={key}
                        onClick={() => setSelectedCategory(selectedCategory === key ? null : key)}
                        className={`flex items-center gap-2 py-2 px-4 rounded-full border transition-colors ${
                          selectedCategory === key
                            ? `${categoryColors[key]} border-transparent`
                            : "border-border hover:border-primary/50"
                        }`}
                        data-testid={`category-${key}-btn`}
                      >
                        <Icon className="w-4 h-4" />
                        <span className="text-sm">{label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Get Suggestions Button */}
              <Button
                onClick={getSuggestions}
                className="w-full h-12 rounded-xl"
                disabled={isLoading}
                data-testid="get-suggestions-btn"
              >
                {isLoading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
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
            <div className="space-y-4 animate-fade-in" data-testid="suggestions-container">
              <div className="flex items-center justify-between">
                <h2 className="font-heading text-xl font-semibold">Suggestions pour vous</h2>
                <span className="text-sm text-muted-foreground">{availableTime} min • Énergie {energyLevel}</span>
              </div>

              {suggestions.reasoning && (
                <Card className="bg-primary/5 border-primary/20">
                  <CardContent className="p-4 flex items-start gap-3">
                    <Sparkles className="w-5 h-5 text-primary mt-0.5" />
                    <p className="text-sm">{suggestions.reasoning}</p>
                  </CardContent>
                </Card>
              )}

              <div className="grid gap-4">
                {suggestions.recommended_actions?.map((action, i) => {
                  const Icon = categoryIcons[action.category] || Sparkles;
                  return (
                    <Card
                      key={action.action_id}
                      className={`action-card cursor-pointer ${i === 0 ? "border-primary/30" : ""}`}
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
                              <div className="flex items-center gap-2 mb-1">
                                <h3 className="font-medium">{action.title}</h3>
                                {action.is_premium && (
                                  <Badge variant="secondary" className="text-xs">Premium</Badge>
                                )}
                                {i === 0 && (
                                  <Badge className="text-xs bg-primary">Recommandé</Badge>
                                )}
                              </div>
                              <p className="text-sm text-muted-foreground mb-2">{action.description}</p>
                              <div className="flex items-center gap-3 text-xs text-muted-foreground">
                                <span>{action.duration_min}-{action.duration_max} min</span>
                                <span>•</span>
                                <span>{categoryLabels[action.category]}</span>
                              </div>
                            </div>
                          </div>
                          <ChevronRight className="w-5 h-5 text-muted-foreground" />
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
            <div className="grid md:grid-cols-3 gap-4">
              {Object.entries(categoryLabels).map(([key, label]) => {
                const Icon = categoryIcons[key];
                return (
                  <Card
                    key={key}
                    className={`${categoryColors[key].replace("text-", "").split(" ")[0]} bg-opacity-5 cursor-pointer action-card`}
                    onClick={() => {
                      setSelectedCategory(key);
                      getSuggestions();
                    }}
                    data-testid={`quick-action-${key}`}
                  >
                    <CardContent className="p-6">
                      <Icon className={`w-10 h-10 ${categoryColors[key].split(" ")[0]} mb-4`} />
                      <h3 className="font-heading text-lg font-medium mb-2">{label}</h3>
                      <p className="text-sm text-muted-foreground">
                        {key === "learning" && "Vocabulaire, lecture, concepts..."}
                        {key === "productivity" && "Planning, emails, brainstorm..."}
                        {key === "well_being" && "Respiration, méditation, étirements..."}
                      </p>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
