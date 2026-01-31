import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Timer,
  BookOpen,
  Target,
  Heart,
  Sparkles,
  LayoutGrid,
  BarChart3,
  User,
  LogOut,
  Menu,
  TrendingUp,
  Flame,
  Clock,
  Loader2,
} from "lucide-react";
import { toast } from "sonner";
import { API, useAuth } from "@/App";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
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

const categoryColors = {
  learning: "#3b82f6",
  productivity: "#f59e0b",
  well_being: "#10b981",
};

const categoryLabels = {
  learning: "Apprentissage",
  productivity: "Productivité",
  well_being: "Bien-être",
};

export default function ProgressStats() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API}/stats`, {
        credentials: "include",
      });
      if (!response.ok) throw new Error("Erreur");
      const data = await response.json();
      setStats(data);
    } catch (error) {
      toast.error("Impossible de charger les statistiques");
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  const pieData = stats
    ? Object.entries(stats.sessions_by_category || {}).map(([key, value]) => ({
        name: categoryLabels[key] || key,
        value,
        color: categoryColors[key] || "#6366f1",
      }))
    : [];

  const barData = stats
    ? Object.entries(stats.time_by_category || {}).map(([key, value]) => ({
        name: categoryLabels[key] || key,
        minutes: value,
        fill: categoryColors[key] || "#6366f1",
      }))
    : [];

  const NavLinks = ({ mobile = false }) => (
    <>
      <Link
        to="/dashboard"
        className="nav-item flex items-center gap-3 px-4 py-3 rounded-xl text-muted-foreground hover:text-foreground"
        onClick={() => mobile && setMobileMenuOpen(false)}
      >
        <LayoutGrid className="w-5 h-5" />
        <span>Dashboard</span>
      </Link>
      <Link
        to="/actions"
        className="nav-item flex items-center gap-3 px-4 py-3 rounded-xl text-muted-foreground hover:text-foreground"
        onClick={() => mobile && setMobileMenuOpen(false)}
      >
        <Sparkles className="w-5 h-5" />
        <span>Bibliothèque</span>
      </Link>
      <Link
        to="/progress"
        className="nav-item active flex items-center gap-3 px-4 py-3 rounded-xl"
        onClick={() => mobile && setMobileMenuOpen(false)}
      >
        <BarChart3 className="w-5 h-5" />
        <span>Progression</span>
      </Link>
      <Link
        to="/profile"
        className="nav-item flex items-center gap-3 px-4 py-3 rounded-xl text-muted-foreground hover:text-foreground"
        onClick={() => mobile && setMobileMenuOpen(false)}
      >
        <User className="w-5 h-5" />
        <span>Profil</span>
      </Link>
    </>
  );

  return (
    <div className="min-h-screen bg-background">
      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex fixed left-0 top-0 bottom-0 w-64 flex-col p-6 border-r border-border bg-card/50">
        <div className="flex items-center gap-2 mb-8">
          <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center">
            <Timer className="w-6 h-6 text-primary-foreground" />
          </div>
          <span className="font-heading text-xl font-semibold">InFinea</span>
        </div>

        <nav className="flex flex-col gap-1 flex-1">
          <NavLinks />
        </nav>

        <div className="pt-4 border-t border-border">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-muted-foreground hover:text-foreground hover:bg-white/5 transition-colors"
          >
            <LogOut className="w-5 h-5" />
            <span>Déconnexion</span>
          </button>
        </div>
      </aside>

      {/* Mobile Header */}
      <header className="lg:hidden fixed top-0 left-0 right-0 z-50 glass">
        <div className="flex items-center justify-between px-4 h-16">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
              <Timer className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="font-heading text-lg font-semibold">InFinea</span>
          </div>

          <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon">
                <Menu className="w-6 h-6" />
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-72 bg-card p-6">
              <nav className="flex flex-col gap-1 mt-8">
                <NavLinks mobile />
              </nav>
              <div className="mt-auto pt-4 border-t border-border absolute bottom-6 left-6 right-6">
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-muted-foreground hover:text-foreground"
                >
                  <LogOut className="w-5 h-5" />
                  <span>Déconnexion</span>
                </button>
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </header>

      {/* Main Content */}
      <main className="lg:ml-64 pt-20 lg:pt-8 px-4 lg:px-8 pb-8">
        <div className="max-w-5xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="font-heading text-3xl font-semibold mb-2" data-testid="progress-title">
              Votre Capital-Temps
            </h1>
            <p className="text-muted-foreground">
              Suivez votre progression et vos accomplissements
            </p>
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : (
            <>
              {/* Stats Overview */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                <Card className="stat-card">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
                        <Clock className="w-6 h-6 text-primary" />
                      </div>
                      <div>
                        <p className="text-2xl font-heading font-bold" data-testid="total-time">
                          {stats?.total_time_invested || 0}
                        </p>
                        <p className="text-xs text-muted-foreground">minutes totales</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="stat-card">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 rounded-xl bg-emerald-500/10 flex items-center justify-center">
                        <TrendingUp className="w-6 h-6 text-emerald-500" />
                      </div>
                      <div>
                        <p className="text-2xl font-heading font-bold" data-testid="total-sessions">
                          {stats?.total_sessions || 0}
                        </p>
                        <p className="text-xs text-muted-foreground">sessions</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="stat-card">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 rounded-xl bg-amber-500/10 flex items-center justify-center">
                        <Flame className="w-6 h-6 text-amber-500" />
                      </div>
                      <div>
                        <p className="text-2xl font-heading font-bold" data-testid="streak-days">
                          {stats?.streak_days || 0}
                        </p>
                        <p className="text-xs text-muted-foreground">jours streak</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="stat-card">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 rounded-xl bg-blue-500/10 flex items-center justify-center">
                        <Sparkles className="w-6 h-6 text-blue-500" />
                      </div>
                      <div>
                        <p className="text-2xl font-heading font-bold">
                          {Math.round((stats?.total_time_invested || 0) / 60)}h
                        </p>
                        <p className="text-xs text-muted-foreground">heures investies</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Charts */}
              <div className="grid lg:grid-cols-2 gap-6 mb-8">
                {/* Time by Category */}
                <Card>
                  <CardHeader>
                    <CardTitle className="font-heading text-lg">Temps par catégorie</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {barData.length > 0 ? (
                      <ResponsiveContainer width="100%" height={250}>
                        <BarChart data={barData}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                          <XAxis dataKey="name" tick={{ fill: "#a1a1aa", fontSize: 12 }} />
                          <YAxis tick={{ fill: "#a1a1aa", fontSize: 12 }} />
                          <Tooltip
                            contentStyle={{
                              backgroundColor: "#121212",
                              border: "1px solid #27272a",
                              borderRadius: "8px",
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
                <Card>
                  <CardHeader>
                    <CardTitle className="font-heading text-lg">Répartition des sessions</CardTitle>
                  </CardHeader>
                  <CardContent>
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
                              backgroundColor: "#121212",
                              border: "1px solid #27272a",
                              borderRadius: "8px",
                            }}
                          />
                        </PieChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="h-[250px] flex items-center justify-center text-muted-foreground">
                        <p>Pas encore de données</p>
                      </div>
                    )}
                    <div className="flex justify-center gap-4 mt-4">
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

              {/* Recent Sessions */}
              <Card>
                <CardHeader>
                  <CardTitle className="font-heading text-lg">Sessions récentes</CardTitle>
                </CardHeader>
                <CardContent>
                  {stats?.recent_sessions?.length > 0 ? (
                    <div className="space-y-3">
                      {stats.recent_sessions.map((session, i) => (
                        <div
                          key={i}
                          className="flex items-center justify-between p-3 rounded-lg bg-white/5"
                        >
                          <div className="flex items-center gap-3">
                            <div
                              className="w-10 h-10 rounded-lg flex items-center justify-center"
                              style={{ backgroundColor: `${categoryColors[session.category]}20` }}
                            >
                              {session.category === "learning" && <BookOpen className="w-5 h-5 text-blue-500" />}
                              {session.category === "productivity" && <Target className="w-5 h-5 text-amber-500" />}
                              {session.category === "well_being" && <Heart className="w-5 h-5 text-emerald-500" />}
                            </div>
                            <div>
                              <p className="font-medium">{session.action_title}</p>
                              <p className="text-xs text-muted-foreground">
                                {new Date(session.completed_at).toLocaleDateString("fr-FR")}
                              </p>
                            </div>
                          </div>
                          <span className="text-sm text-muted-foreground">
                            {session.actual_duration} min
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      <Clock className="w-10 h-10 mx-auto mb-2 opacity-50" />
                      <p>Aucune session complétée</p>
                      <Link to="/dashboard">
                        <Button variant="link" className="mt-2">
                          Commencer une session
                        </Button>
                      </Link>
                    </div>
                  )}
                </CardContent>
              </Card>
            </>
          )}
        </div>
      </main>
    </div>
  );
}
