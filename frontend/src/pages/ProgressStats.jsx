import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  BookOpen,
  Target,
  Heart,
  Sparkles,
  TrendingUp,
  Flame,
  Clock,
  Loader2,
  Palette,
  Dumbbell,
  Leaf,
  Users,
  MessageCircle,
  Brain,
  Rocket,
  Share2,
  ChevronRight,
} from "lucide-react";
import { toast } from "sonner";
import { API, authFetch } from "@/App";
import Sidebar from "@/components/Sidebar";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import PremiumAnalytics from "@/components/PremiumAnalytics";
import ShareDialog from "@/components/ShareDialog";

const categoryColors = {
  learning: "#459492",
  productivity: "#E48C75",
  well_being: "#5DB786",
  creativity: "#55B3AE",
  fitness: "#E48C75",
  mindfulness: "#459492",
  leadership: "#7B8FA1",
  finance: "#2E9B6A",
  relations: "#C4806E",
  mental_health: "#6EAAA8",
  entrepreneurship: "#E48C75",
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

export default function ProgressStats() {
  const [stats, setStats] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [shareOpen, setShareOpen] = useState(false);
  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await authFetch(`${API}/stats`);
      if (!response.ok) throw new Error("Erreur");
      const data = await response.json();
      setStats(data);
    } catch (error) {
      toast.error("Impossible de charger les statistiques");
    } finally {
      setIsLoading(false);
    }
  };

  const pieData = stats
    ? Object.entries(stats.sessions_by_category || {}).map(([key, value]) => ({
        name: categoryLabels[key] || key,
        value,
        color: categoryColors[key] || "#459492",
      }))
    : [];

  const barData = stats
    ? Object.entries(stats.time_by_category || {}).map(([key, value]) => ({
        name: categoryLabels[key] || key,
        minutes: value,
        fill: categoryColors[key] || "#459492",
      }))
    : [];

  return (
    <div className="min-h-screen app-bg-mesh">
      <Sidebar />

      {/* Main Content */}
      <main className="lg:ml-64 pt-14 lg:pt-0 pb-8">
        {/* Dark Header */}
        <div className="section-dark-header px-4 lg:px-8 pt-8 lg:pt-10 pb-8">
          <div className="max-w-5xl mx-auto flex items-start justify-between">
            <div>
              <h1 className="text-display text-3xl lg:text-4xl font-semibold text-white opacity-0 animate-fade-in" data-testid="progress-title">
                Progression
              </h1>
              <p className="text-white/60 text-sm mt-1 opacity-0 animate-fade-in" style={{ animationDelay: "50ms" }}>
                Suivez vos statistiques et votre évolution
              </p>
            </div>
            {stats && (
              <Button
                variant="outline"
                size="sm"
                className="gap-1.5 shrink-0 rounded-xl bg-white/10 hover:bg-white/20 border-white/20 hover:border-white/30 text-white transition-all"
                onClick={() => setShareOpen(true)}
              >
                <Share2 className="w-4 h-4" />
                Partager
              </Button>
            )}
            <ShareDialog open={shareOpen} onOpenChange={setShareOpen} shareType="weekly_recap" />
          </div>
        </div>

        <div className="px-4 lg:px-8">
        <div className="max-w-5xl mx-auto space-y-6 pt-6">

          {isLoading ? (
            <div className="space-y-6">
              {/* Skeleton Stats Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {[0, 1, 2, 3].map((i) => (
                  <div key={i} className="animate-pulse rounded-xl bg-muted h-24" />
                ))}
              </div>
              {/* Skeleton Chart Cards */}
              <div className="grid md:grid-cols-2 gap-6">
                <div className="animate-pulse rounded-xl bg-muted h-64" />
                <div className="animate-pulse rounded-xl bg-muted h-64" />
              </div>
            </div>
          ) : (
            <div>
              {/* Stats Overview */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                <Card className="stat-card stat-card-accent bg-gradient-to-br from-[#5DB786]/40 to-[#5DB786]/5 hover:shadow-md hover:border-[#5DB786]/30 transition-all duration-300 opacity-0 animate-fade-in" style={{ "--stat-accent-color": "#5DB786", animationDelay: "0ms", animationFillMode: "forwards" }}>
                  <CardContent className="p-4">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 rounded-xl bg-[#5DB786]/40 flex items-center justify-center">
                        <TrendingUp className="w-6 h-6 text-[#5DB786]" />
                      </div>
                      <div>
                        <p className="text-2xl font-sans font-semibold tracking-tight font-bold tabular-nums" data-testid="total-sessions">
                          {stats?.total_sessions || 0}
                        </p>
                        <p className="text-xs text-muted-foreground">sessions</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="stat-card stat-card-accent bg-gradient-to-br from-[#459492]/40 to-[#459492]/5 hover:shadow-md hover:border-[#459492]/30 transition-all duration-300 opacity-0 animate-fade-in" style={{ "--stat-accent-color": "#459492", animationDelay: "50ms", animationFillMode: "forwards" }}>
                  <CardContent className="p-4">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 rounded-xl bg-primary/20 flex items-center justify-center">
                        <Clock className="w-6 h-6 text-primary" />
                      </div>
                      <div>
                        <p className="text-2xl font-sans font-semibold tracking-tight font-bold tabular-nums" data-testid="total-time">
                          {stats?.total_time_invested || 0}
                        </p>
                        <p className="text-xs text-muted-foreground">minutes totales</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="stat-card stat-card-accent bg-gradient-to-br from-[#E48C75]/40 to-[#E48C75]/5 hover:shadow-md hover:border-[#E48C75]/30 transition-all duration-300 opacity-0 animate-fade-in" style={{ "--stat-accent-color": "#E48C75", animationDelay: "100ms", animationFillMode: "forwards" }}>
                  <CardContent className="p-4">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 rounded-xl bg-[#E48C75]/40 flex items-center justify-center">
                        <Flame className="w-6 h-6 text-[#E48C75]" />
                      </div>
                      <div>
                        <p className="text-2xl font-sans font-semibold tracking-tight font-bold tabular-nums" data-testid="streak-days">
                          {stats?.streak_days || 0}
                        </p>
                        <p className="text-xs text-muted-foreground">jours streak</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="stat-card stat-card-accent bg-gradient-to-br from-[#55B3AE]/40 to-[#55B3AE]/5 hover:shadow-md hover:border-[#55B3AE]/30 transition-all duration-300 opacity-0 animate-fade-in" style={{ "--stat-accent-color": "#55B3AE", animationDelay: "150ms", animationFillMode: "forwards" }}>
                  <CardContent className="p-4">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 rounded-xl bg-[#459492]/40 flex items-center justify-center">
                        <Sparkles className="w-6 h-6 text-[#459492]" />
                      </div>
                      <div>
                        <p className="text-2xl font-sans font-semibold tracking-tight font-bold tabular-nums">
                          {Math.round((stats?.total_time_invested || 0) / 60)}h
                        </p>
                        <p className="text-xs text-muted-foreground">heures investies</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Charts */}
              <div className="grid md:grid-cols-2 gap-6 mb-8 opacity-0 animate-fade-in" style={{ animationDelay: "300ms", animationFillMode: "forwards" }}>
                {/* Time by Category */}
                <Card className="chart-card hover:border-[#459492]/20 hover:shadow-md transition-all duration-300">
                  <CardHeader>
                    <CardTitle className="font-sans font-semibold tracking-tight text-lg section-header-accent">Temps par catégorie</CardTitle>
                  </CardHeader>
                  <CardContent className="relative z-[1]">
                    {barData.length > 0 ? (
                      <ResponsiveContainer width="100%" height={250}>
                        <BarChart data={barData}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#E2E6EA" />
                          <XAxis dataKey="name" tick={{ fill: "#9A9A9A", fontSize: 12 }} />
                          <YAxis tick={{ fill: "#9A9A9A", fontSize: 12 }} />
                          <Tooltip
                            contentStyle={{
                              backgroundColor: "#FFFFFF",
                              border: "1px solid #E2E6EA",
                              borderRadius: "12px",
                              boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
                            }}
                          />
                          <Bar dataKey="minutes" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="h-[250px] flex items-center justify-center text-muted-foreground">
                        <p>Pas encore de données</p>
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Sessions Distribution */}
                <Card className="chart-card hover:border-[#459492]/20 hover:shadow-md transition-all duration-300">
                  <CardHeader>
                    <CardTitle className="font-sans font-semibold tracking-tight text-lg section-header-accent">Répartition des sessions</CardTitle>
                  </CardHeader>
                  <CardContent className="relative z-[1]">
                    {pieData.length > 0 ? (
                      <ResponsiveContainer width="100%" height={250}>
                        <PieChart>
                          <Pie
                            data={pieData}
                            cx="50%"
                            cy="50%"
                            innerRadius={60}
                            outerRadius={90}
                            paddingAngle={5}
                            dataKey="value"
                          >
                            {pieData.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                          </Pie>
                          <Tooltip
                            contentStyle={{
                              backgroundColor: "#FFFFFF",
                              border: "1px solid #E2E6EA",
                              borderRadius: "12px",
                              boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
                            }}
                          />
                        </PieChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="h-[250px] flex items-center justify-center text-muted-foreground">
                        <p>Pas encore de données</p>
                      </div>
                    )}
                    <div className="flex justify-center flex-wrap gap-x-4 gap-y-1 mt-4">
                      {pieData.map((entry, i) => (
                        <div key={i} className="flex items-center gap-2">
                          <div
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: entry.color }}
                          />
                          <span className="text-sm text-muted-foreground">{entry.name}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Premium Analytics */}
              <PremiumAnalytics />

              {/* Recent Sessions */}
              <Card className="hover:border-[#459492]/20 hover:shadow-md transition-all duration-300 opacity-0 animate-fade-in" style={{ animationDelay: "400ms", animationFillMode: "forwards" }}>
                <CardHeader>
                  <CardTitle className="font-sans font-semibold tracking-tight text-lg section-header-accent">Sessions récentes</CardTitle>
                </CardHeader>
                <CardContent>
                  {stats?.recent_sessions?.length > 0 ? (
                    <div className="space-y-3">
                      {stats.recent_sessions.map((session, i) => (
                        <div
                          key={i}
                          className="group flex items-center justify-between p-3 rounded-xl bg-card/50 border border-border/50 hover:bg-muted/50 hover:shadow-sm hover:border-[#459492]/20 transition-all duration-200 opacity-0 animate-fade-in"
                          style={{ animationDelay: `${450 + i * 30}ms`, animationFillMode: "forwards" }}
                        >
                          <div className="flex items-center gap-3">
                            <div
                              className="w-10 h-10 rounded-lg flex items-center justify-center"
                              style={{ backgroundColor: `${categoryColors[session.category]}20` }}
                            >
                              {(() => {
                                const iconMap = {
                                  learning: <BookOpen className="w-5 h-5 text-[#459492]" />,
                                  productivity: <Target className="w-5 h-5 text-[#E48C75]" />,
                                  well_being: <Heart className="w-5 h-5 text-[#5DB786]" />,
                                  creativity: <Palette className="w-5 h-5 text-[#55B3AE]" />,
                                  fitness: <Dumbbell className="w-5 h-5 text-[#E48C75]" />,
                                  mindfulness: <Leaf className="w-5 h-5 text-[#459492]" />,
                                  leadership: <Users className="w-5 h-5 text-[#7B8FA1]" />,
                                  finance: <TrendingUp className="w-5 h-5 text-[#2E9B6A]" />,
                                  relations: <MessageCircle className="w-5 h-5 text-[#C4806E]" />,
                                  mental_health: <Brain className="w-5 h-5 text-[#6EAAA8]" />,
                                  entrepreneurship: <Rocket className="w-5 h-5 text-[#E48C75]" />,
                                };
                                return iconMap[session.category] || <Sparkles className="w-5 h-5 text-primary" />;
                              })()}
                            </div>
                            <div>
                              <p className="font-medium">{session.action_title}</p>
                              <p className="text-xs text-muted-foreground">
                                {new Date(session.completed_at).toLocaleDateString("fr-FR")}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-sm text-muted-foreground tabular-nums">
                              {session.actual_duration} min
                            </span>
                            <ChevronRight className="w-4 h-4 text-muted-foreground group-hover:translate-x-1 transition-transform" />
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[#459492]/25 to-[#55B3AE]/15 flex items-center justify-center mx-auto mb-3">
                        <Clock className="w-8 h-8 text-[#459492]" />
                      </div>
                      <p>Aucune session complétée</p>
                      <Link to="/dashboard">
                        <Button className="mt-3 rounded-xl shadow-md">
                          Commencer une session
                        </Button>
                      </Link>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}
        </div>
        </div>
      </main>
    </div>
  );
}
