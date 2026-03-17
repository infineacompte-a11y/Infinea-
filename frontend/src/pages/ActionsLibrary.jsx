import React, { useState, useEffect } from "react";
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

export default function ActionsLibrary() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [actions, setActions] = useState([]);
  const [customActions, setCustomActions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeCategory, setActiveCategory] = useState("all");
  const [showCreateModal, setShowCreateModal] = useState(false);

  useEffect(() => {
    fetchActions();
  }, []);

  const fetchActions = async () => {
    try {
      const [actionsRes, customRes] = await Promise.all([
        authFetch(`${API}/actions?limit=10000`),
        authFetch(`${API}/actions/custom`).catch(() => null),
      ]);
      if (!actionsRes.ok) throw new Error("Erreur");
      setActions(await actionsRes.json());
      if (customRes?.ok) setCustomActions(await customRes.json());
    } catch (error) {
      toast.error("Impossible de charger les actions");
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
      if (error.message.includes("Premium")) {
        toast.error("Action Premium - Passez à Premium pour débloquer");
        navigate("/pricing");
      } else {
        toast.error(error.message);
      }
    }
  };

  const allActions = [...actions, ...customActions.map(a => ({ ...a, is_custom: true }))];
  const isMyActions = activeCategory === "my_actions";
  const filteredActions = isMyActions
    ? []
    : activeCategory === "all"
      ? allActions
      : allActions.filter(a => a.category === activeCategory);

  // Group custom actions by category for "Mes actions" tab
  const groupedCustomActions = customActions.reduce((groups, action) => {
    const cat = action.category || "productivity";
    if (!groups[cat]) groups[cat] = [];
    groups[cat].push({ ...action, is_custom: true });
    return groups;
  }, {});

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />

      {/* Main Content */}
      <main className="lg:ml-64 pt-20 lg:pt-8 px-4 lg:px-8 pb-8">
        <div className="max-w-5xl mx-auto">
          {/* Header */}
          <div className="mb-8 flex items-start justify-between">
            <div>
              <h1 className="font-heading text-3xl font-semibold mb-2" data-testid="library-title">
                Bibliothèque d'actions
              </h1>
              <p className="text-muted-foreground">
                Explorez toutes les micro-actions disponibles
              </p>
            </div>
            <Button
              onClick={() => setShowCreateModal(true)}
              className="rounded-xl shrink-0"
              data-testid="create-action-btn"
            >
              <Sparkles className="w-4 h-4 mr-2" />
              Créer une action
            </Button>
          </div>

          {/* Category Tabs */}
          <Tabs value={activeCategory} onValueChange={setActiveCategory} className="mb-8">
            <TabsList className="bg-card border border-border p-1 h-auto flex-wrap">
              <TabsTrigger value="all" className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground rounded-lg px-4 py-2">
                Toutes
              </TabsTrigger>
              <TabsTrigger
                value="my_actions"
                className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground rounded-lg px-4 py-2 gap-1"
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
                  className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground rounded-lg px-4 py-2"
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
                    className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground rounded-lg px-4 py-2 gap-1"
                    data-testid={`tab-${key}`}
                  >
                    {isPremium ? (
                      <Lock className="w-3 h-3" />
                    ) : (
                      <Crown className="w-3 h-3 text-amber-500" />
                    )}
                    {label}
                  </TabsTrigger>
                );
              })}
            </TabsList>
          </Tabs>

          {/* Actions Display */}
          {isLoading ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : isMyActions ? (
            /* Mes actions — grouped by category */
            customActions.length === 0 ? (
              <div className="text-center py-20 animate-fade-in">
                <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-4">
                  <Plus className="w-8 h-8 text-primary" />
                </div>
                <h3 className="font-heading text-xl mb-2">Aucune action personnalisée</h3>
                <p className="text-muted-foreground mb-6">
                  Créez votre première action avec l'IA, elle apparaîtra ici.
                </p>
                <Button
                  onClick={() => setShowCreateModal(true)}
                  className="rounded-xl"
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
                        <h2 className="font-heading font-semibold text-lg">{catLabel}</h2>
                        <Badge variant="secondary" className="text-xs">{catActions.length}</Badge>
                      </div>
                      <div className="grid md:grid-cols-2 gap-4">
                        {catActions.map((action) => {
                          const Icon = categoryIcons[action.category] || Sparkles;
                          return (
                            <Card
                              key={action.action_id}
                              className="action-card cursor-pointer"
                              onClick={() => startSession(action.action_id)}
                              data-testid={`action-${action.action_id}`}
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
                                  <ChevronRight className="w-5 h-5 text-muted-foreground flex-shrink-0" />
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
            <div className="grid md:grid-cols-2 gap-4" data-testid="actions-grid">
              {filteredActions.map((action) => {
                const Icon = categoryIcons[action.category] || Sparkles;
                const isPremiumLocked = action.is_premium && user?.subscription_tier !== "premium";

                return (
                  <Card
                    key={action.action_id}
                    className={`action-card cursor-pointer ${isPremiumLocked ? "opacity-80" : ""}`}
                    onClick={() => startSession(action.action_id)}
                    data-testid={`action-${action.action_id}`}
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
                              {action.is_custom && (
                                <Badge className="text-xs bg-primary/20 text-primary border-primary/30">
                                  Custom
                                </Badge>
                              )}
                              {action.is_premium && (
                                <Badge variant="secondary" className="text-xs flex items-center gap-1">
                                  {isPremiumLocked && <Lock className="w-3 h-3" />}
                                  Premium
                                </Badge>
                              )}
                            </div>
                            <p className="text-sm text-muted-foreground mb-2 line-clamp-2">{action.description}</p>
                            <div className="flex items-center gap-3 text-xs text-muted-foreground">
                              <span>{action.duration_min}-{action.duration_max} min</span>
                              <span>•</span>
                              <span className="capitalize">{action.energy_level}</span>
                            </div>
                          </div>
                        </div>
                        <ChevronRight className="w-5 h-5 text-muted-foreground flex-shrink-0" />
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}

          {filteredActions.length === 0 && !isLoading && !isMyActions && (
            <div className="text-center py-20">
              <Sparkles className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="font-heading text-xl mb-2">Aucune action trouvée</h3>
              <p className="text-muted-foreground">Essayez une autre catégorie</p>
            </div>
          )}
        </div>
      </main>

      <CreateActionModal
        open={showCreateModal}
        onOpenChange={setShowCreateModal}
        onActionCreated={fetchActions}
      />
    </div>
  );
}
