import React, { useState, useEffect, useCallback, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  BookOpen,
  Target,
  Heart,
  ChevronRight,
  Sparkles,
  Lock,
  Loader2,
  Crown,
  Palette,
  Dumbbell,
  Leaf,
  Users,
  TrendingUp,
  MessageCircle,
  Brain,
  Rocket,
  User,
  Plus,
} from "lucide-react";
import { toast } from "sonner";
import { API, useAuth, authFetch } from "@/App";
import Sidebar from "@/components/Sidebar";
import CreateActionModal from "@/components/CreateActionModal";

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
  leadership: "text-[#7B8FA1] bg-[#7B8FA1]/20",
  finance: "text-[#2E9B6A] bg-[#2E9B6A]/20",
  relations: "text-[#C4806E] bg-[#C4806E]/20",
  mental_health: "text-[#6EAAA8] bg-[#6EAAA8]/20",
  entrepreneurship: "text-[#E48C75] bg-[#E48C75]/40",
};

const categoryBorderColors = {
  learning: "border-l-[#459492]",
  productivity: "border-l-[#E48C75]",
  well_being: "border-l-[#5DB786]",
  creativity: "border-l-[#55B3AE]",
  fitness: "border-l-[#E48C75]",
  mindfulness: "border-l-[#459492]",
  leadership: "border-l-[#7B8FA1]",
  finance: "border-l-[#2E9B6A]",
  relations: "border-l-[#C4806E]",
  mental_health: "border-l-[#6EAAA8]",
  entrepreneurship: "border-l-[#E48C75]",
};

const categoryLabels = {
  learning: "Apprentissage",
  productivity: "Productivité",
  well_being: "Bien-être",
};

const premiumCategoryLabels = {
  creativity: "Créativité",
  fitness: "Fitness",
  mindfulness: "Mindfulness",
  leadership: "Leadership",
  finance: "Finance",
  relations: "Relations",
  mental_health: "Santé mentale",
  entrepreneurship: "Entrepreneuriat",
};

function SkeletonCard() {
  return (
    <div className="animate-pulse rounded-xl bg-card border border-border p-4">
      <div className="flex items-start gap-4">
        <div className="w-12 h-12 rounded-xl bg-muted flex-shrink-0" />
        <div className="flex-1 space-y-3">
          <div className="h-4 bg-muted rounded-lg w-3/4" />
          <div className="h-3 bg-muted rounded-lg w-full" />
          <div className="h-3 bg-muted rounded-lg w-1/2" />
          <div className="flex gap-3 pt-1">
            <div className="h-3 bg-muted rounded-lg w-16" />
            <div className="h-3 bg-muted rounded-lg w-12" />
          </div>
        </div>
      </div>
    </div>
  );
}

function SkeletonGrid() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {Array.from({ length: 6 }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  );
}

export default function ActionsLibrary() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [actions, setActions] = useState([]);
  const [customActions, setCustomActions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeCategory, setActiveCategory] = useState("all");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const actionsCache = useRef({});

  const fetchActions = useCallback(async (category) => {
    const cacheKey = category || "all";
    // Return cached results instantly if available
    if (actionsCache.current[cacheKey]) {
      setActions(actionsCache.current[cacheKey]);
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    try {
      const params = new URLSearchParams({ limit: "500" });
      if (category && category !== "all" && category !== "my_actions") {
        params.set("category", category);
      }
      const [actionsRes, customRes] = await Promise.all([
        authFetch(`${API}/actions?${params}`),
        actionsCache.current._custom !== undefined
          ? Promise.resolve(null)
          : authFetch(`${API}/actions/custom`).catch(() => null),
      ]);
      if (!actionsRes.ok) throw new Error("Erreur");
      const data = await actionsRes.json();
      actionsCache.current[cacheKey] = data;
      setActions(data);
      if (customRes?.ok) {
        const customData = await customRes.json();
        actionsCache.current._custom = customData;
        setCustomActions(customData);
      } else if (actionsCache.current._custom) {
        setCustomActions(actionsCache.current._custom);
      }
    } catch (error) {
      toast.error("Impossible de charger les actions");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchActions(activeCategory);
  }, [activeCategory, fetchActions]);

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
      if (error.message.includes("Premium")) {
        toast.error("Action Premium - Passez à Premium pour débloquer");
        navigate("/pricing");
      } else {
        toast.error(error.message);
      }
    }
  };

  const allActions = [...actions, ...customActions.filter(a => activeCategory === "all" || a.category === activeCategory).map(a => ({ ...a, is_custom: true }))];
  const isMyActions = activeCategory === "my_actions";
  const filteredActions = isMyActions ? [] : allActions;

  // Group custom actions by category for "Mes actions" tab
  const groupedCustomActions = customActions.reduce((groups, action) => {
    const cat = action.category || "productivity";
    if (!groups[cat]) groups[cat] = [];
    groups[cat].push({ ...action, is_custom: true });
    return groups;
  }, {});

  return (
    <div className="min-h-screen app-bg-mesh">
      <Sidebar />

      {/* Main Content */}
      <main className="lg:ml-64 pt-14 lg:pt-0 pb-8">
        {/* Dark Header */}
        <div className="section-dark-header px-4 lg:px-8 pt-8 lg:pt-10 pb-8">
          <div className="max-w-6xl mx-auto">
            <div className="flex items-start justify-between">
              <div>
                <h1 className="text-display text-3xl lg:text-4xl font-semibold text-white opacity-0 animate-fade-in" data-testid="library-title">
                  Bibliothèque
                </h1>
                <p className="text-white/60 text-sm mt-1 opacity-0 animate-fade-in" style={{ animationDelay: "50ms" }}>
                  Explorez plus de 700 micro-actions
                </p>
              </div>
              <Button
                onClick={() => setShowCreateModal(true)}
                className="btn-premium rounded-xl shrink-0 text-white border-0 opacity-0 animate-fade-in"
                style={{ animationDelay: "100ms" }}
                data-testid="create-action-btn"
              >
                <Sparkles className="w-4 h-4 mr-2" />
                Créer une action
              </Button>
            </div>
          </div>
        </div>

        <div className="px-4 lg:px-8">
          <div className="max-w-6xl mx-auto space-y-6 pt-6">
          {/* Category Tabs — entrance animation with delay */}
          <Tabs value={activeCategory} onValueChange={setActiveCategory} className="mb-8">
            <TabsList
              className="bg-card border border-border p-1 h-auto flex-wrap opacity-0 animate-fade-in"
              style={{ animationDelay: "100ms", animationFillMode: "forwards" }}
            >
              <TabsTrigger
                value="all"
                className="data-[state=active]:tab-active-premium rounded-lg px-4 py-2 transition-[background,box-shadow] duration-200 hover:bg-muted/60"
              >
                Toutes
              </TabsTrigger>
              <TabsTrigger
                value="my_actions"
                className="data-[state=active]:tab-active-premium rounded-lg px-4 py-2 gap-1 transition-[background,box-shadow] duration-200 hover:bg-muted/60"
                data-testid="tab-my-actions"
              >
                <User className="w-3.5 h-3.5" />
                Mes actions
                {customActions.length > 0 && (
                  <span className="ml-1 text-xs opacity-70">({customActions.length})</span>
                )}
              </TabsTrigger>
              {Object.entries(categoryLabels).map(([key, label]) => (
                <TabsTrigger
                  key={key}
                  value={key}
                  className="data-[state=active]:tab-active-premium rounded-lg px-4 py-2 transition-[background,box-shadow] duration-200 hover:bg-muted/60"
                  data-testid={`tab-${key}`}
                >
                  {label}
                </TabsTrigger>
              ))}
              {Object.entries(premiumCategoryLabels).map(([key, label]) => {
                const isPremium = user?.subscription_tier !== "premium";
                return (
                  <TabsTrigger
                    key={key}
                    value={key}
                    className="data-[state=active]:tab-active-premium rounded-lg px-4 py-2 gap-1 transition-[background,box-shadow] duration-200 hover:bg-muted/60"
                    data-testid={`tab-${key}`}
                  >
                    {isPremium ? (
                      <Lock className="w-3 h-3" />
                    ) : (
                      <Crown className="w-5 h-5 text-[#E48C75]" />
                    )}
                    {label}
                  </TabsTrigger>
                );
              })}
            </TabsList>
          </Tabs>

          {/* Actions Display */}
          {isLoading ? (
            /* Skeleton loading — replaces spinner */
            <SkeletonGrid />
          ) : isMyActions ? (
            /* Mes actions — grouped by category */
            customActions.length === 0 ? (
              <div className="text-center py-20 animate-fade-in">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[#459492]/20 to-transparent flex items-center justify-center mx-auto mb-4">
                  <Plus className="w-8 h-8 text-primary animate-pulse" />
                </div>
                <h3 className="font-sans font-semibold tracking-tight text-xl mb-2">Aucune action personnalisée</h3>
                <p className="text-muted-foreground mb-6">
                  Créez votre première action avec l'IA, elle apparaîtra ici.
                </p>
                <Button
                  onClick={() => setShowCreateModal(true)}
                  className="btn-premium rounded-xl text-white border-0"
                >
                  <Sparkles className="w-4 h-4 mr-2" />
                  Créer une action
                </Button>
              </div>
            ) : (
              <div className="space-y-8 animate-fade-in" data-testid="my-actions-grouped">
                {Object.entries(groupedCustomActions).map(([cat, catActions]) => {
                  const CatIcon = categoryIcons[cat] || Sparkles;
                  const catLabel = categoryLabels[cat] || premiumCategoryLabels[cat] || cat;
                  return (
                    <div key={cat}>
                      <div className="flex items-center gap-2 mb-4">
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${categoryColors[cat] || "bg-muted"}`}>
                          <CatIcon className="w-4 h-4" />
                        </div>
                        <h2 className="font-sans font-semibold tracking-tight font-semibold text-lg">{catLabel}</h2>
                        <Badge variant="secondary" className="text-xs">{catActions.length}</Badge>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {catActions.map((action, i) => {
                          const Icon = categoryIcons[action.category] || Sparkles;
                          return (
                            <Card
                              key={action.action_id}
                              className={`group action-card cursor-pointer border-l-[3px] ${categoryBorderColors[action.category] || "border-l-border"} hover:shadow-lg hover:border-[#459492]/30 hover:-translate-y-0.5 active:translate-y-px transition-all duration-200 opacity-0 animate-fade-in`}
                              style={{ animationDelay: `${i * 50}ms`, animationFillMode: "forwards" }}
                              onClick={() => startSession(action.action_id)}
                              data-testid={`action-${action.action_id}`}
                            >
                              <CardContent className="p-4">
                                <div className="flex items-start justify-between gap-4">
                                  <div className="flex items-start gap-4">
                                    <div className={`w-12 h-12 rounded-xl flex items-center justify-center group-hover:shadow-md transition-shadow duration-200 ${categoryColors[action.category]}`}>
                                      <Icon className="w-6 h-6" />
                                    </div>
                                    <div>
                                      <div className="flex items-center gap-2 mb-1">
                                        <h3 className="font-medium">{action.title}</h3>
                                        <Badge className="text-xs bg-primary/20 text-primary border-primary/30">
                                          Custom
                                        </Badge>
                                      </div>
                                      <p className="text-sm text-muted-foreground mb-2 line-clamp-2">{action.description}</p>
                                      <div className="flex items-center gap-3 text-xs text-muted-foreground">
                                        <span>{action.duration_min}-{action.duration_max} min</span>
                                        <span>•</span>
                                        <span className="capitalize">{action.energy_level}</span>
                                      </div>
                                    </div>
                                  </div>
                                  <ChevronRight className="w-5 h-5 text-muted-foreground flex-shrink-0 group-hover:translate-x-1 transition-transform duration-200" />
                                </div>
                              </CardContent>
                            </Card>
                          );
                        })}
                      </div>
                    </div>
                  );
                })}
              </div>
            )
          ) : (
            /* Standard grid — all or filtered by category */
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4" data-testid="actions-grid">
              {filteredActions.map((action, i) => {
                const Icon = categoryIcons[action.category] || Sparkles;
                const isPremiumLocked = action.is_premium && user?.subscription_tier !== "premium";

                return (
                  <Card
                    key={action.action_id}
                    className={`group action-card cursor-pointer border-l-[3px] ${categoryBorderColors[action.category] || "border-l-border"} hover:shadow-md hover:border-border/80 hover:-translate-y-0.5 active:translate-y-px transition-all duration-300 ease-out ${i < 8 ? "opacity-0 animate-fade-in" : ""} ${isPremiumLocked ? "opacity-75" : ""}`}
                    style={i < 8 ? { animationDelay: `${i * 50}ms`, animationFillMode: "forwards" } : undefined}
                    onClick={() => startSession(action.action_id)}
                    data-testid={`action-${action.action_id}`}
                  >
                    <CardContent className="p-4 relative">
                      {/* Premium locked overlay hint */}
                      {isPremiumLocked && (
                        <div className="absolute inset-0 rounded-xl bg-background/30 pointer-events-none z-10" />
                      )}
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex items-start gap-4">
                          <div className={`w-12 h-12 rounded-xl flex items-center justify-center group-hover:shadow-md transition-shadow duration-200 ${categoryColors[action.category]}`}>
                            <Icon className="w-6 h-6" />
                          </div>
                          <div>
                            <div className="flex items-center gap-2 mb-1">
                              <h3 className="font-medium">{action.title}</h3>
                              {action.is_custom && (
                                <Badge className="text-xs bg-primary/20 text-primary border-primary/30">
                                  Custom
                                </Badge>
                              )}
                              {action.is_premium && (
                                <Badge
                                  variant="secondary"
                                  className={`text-xs flex items-center gap-1 ${isPremiumLocked ? "premium-badge text-white border-0" : ""}`}
                                >
                                  {isPremiumLocked && <Lock className="w-3 h-3 relative z-10" />}
                                  <span className="relative z-10">Premium</span>
                                </Badge>
                              )}
                            </div>
                            <p className="text-sm text-muted-foreground mb-2 line-clamp-2">{action.description}</p>
                            <div className="flex items-center gap-3 text-xs text-muted-foreground">
                              <span>{action.duration_min}-{action.duration_max} min</span>
                              <span>•</span>
                              <span className="capitalize">{action.energy_level}</span>
                            </div>
                            {/* Premium locked hover message */}
                            {isPremiumLocked && (
                              <p className="text-xs text-[#E48C75] mt-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                                Passez Premium pour débloquer
                              </p>
                            )}
                          </div>
                        </div>
                        <ChevronRight className="w-5 h-5 text-muted-foreground flex-shrink-0 group-hover:translate-x-1 transition-transform duration-200" />
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}

          {filteredActions.length === 0 && !isLoading && !isMyActions && (
            <div className="text-center py-20 animate-fade-in">
              <div className="bg-gradient-to-br from-[#459492]/20 to-transparent rounded-2xl p-4 w-fit mx-auto mb-4">
                <Sparkles className="w-12 h-12 text-muted-foreground animate-pulse" />
              </div>
              <h3 className="font-sans font-semibold tracking-tight text-xl mb-2">Aucune action trouvée</h3>
              <p className="text-muted-foreground">Essayez une autre catégorie</p>
            </div>
          )}
          </div>
        </div>
      </main>

      <CreateActionModal
        open={showCreateModal}
        onOpenChange={setShowCreateModal}
        onActionCreated={(newAction) => {
          if (newAction) {
            setCustomActions(prev => [newAction, ...prev]);
            actionsCache.current._custom = undefined;
          } else {
            actionsCache.current = {};
            fetchActions(activeCategory);
          }
        }}
      />
    </div>
  );
}
