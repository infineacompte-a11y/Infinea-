import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import {
  Timer,
  Sparkles,
  LayoutGrid,
  BarChart3,
  User,
  LogOut,
  Menu,
  BookOpen,
  Brain,
  Lightbulb,
  TrendingUp,
  Heart,
  Smile,
  Meh,
  Frown,
  Plus,
  RefreshCw,
  Trash2,
  Calendar,
  Award,
  Bell,
  Building2,
  Loader2,
  ChevronRight,
  Target,
  Zap,
} from "lucide-react";
import { toast } from "sonner";
import { API, useAuth } from "@/App";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const moodIcons = {
  positive: { icon: Smile, color: "text-emerald-500", bg: "bg-emerald-500/10", label: "Positif" },
  neutral: { icon: Meh, color: "text-amber-500", bg: "bg-amber-500/10", label: "Neutre" },
  negative: { icon: Frown, color: "text-red-500", bg: "bg-red-500/10", label: "Difficile" },
};

const categoryLabels = {
  learning: "Apprentissage",
  productivity: "Productivité",
  well_being: "Bien-être",
};

export default function JournalPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [reflections, setReflections] = useState([]);
  const [summary, setSummary] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isGeneratingSummary, setIsGeneratingSummary] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [showNewReflection, setShowNewReflection] = useState(false);
  const [newReflection, setNewReflection] = useState({
    content: "",
    mood: "neutral",
    category: null,
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem("infinea_token");
      const headers = { Authorization: `Bearer ${token}` };

      const [refRes, sumRes] = await Promise.all([
        fetch(`${API}/reflections?limit=30`, { credentials: "include", headers }),
        fetch(`${API}/reflections/summaries?limit=1`, { credentials: "include", headers }),
      ]);

      if (refRes.ok) {
        const data = await refRes.json();
        setReflections(data.reflections);
      }

      if (sumRes.ok) {
        const data = await sumRes.json();
        if (data.summaries?.length > 0) {
          setSummary(data.summaries[0]);
        }
      }
    } catch (error) {
      toast.error("Erreur de chargement");
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateReflection = async () => {
    if (!newReflection.content.trim()) {
      toast.error("Écrivez quelque chose d'abord!");
      return;
    }

    try {
      const token = localStorage.getItem("infinea_token");
      const response = await fetch(`${API}/reflections`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        credentials: "include",
        body: JSON.stringify({
          content: newReflection.content,
          mood: newReflection.mood,
          related_category: newReflection.category,
        }),
      });

      if (!response.ok) throw new Error("Erreur");

      toast.success("Réflexion enregistrée!");
      setNewReflection({ content: "", mood: "neutral", category: null });
      setShowNewReflection(false);
      fetchData();
    } catch (error) {
      toast.error("Erreur lors de l'enregistrement");
    }
  };

  const handleDeleteReflection = async (reflectionId) => {
    try {
      const token = localStorage.getItem("infinea_token");
      const response = await fetch(`${API}/reflections/${reflectionId}`, {
        method: "DELETE",
        credentials: "include",
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!response.ok) throw new Error("Erreur");

      toast.success("Réflexion supprimée");
      setReflections(reflections.filter((r) => r.reflection_id !== reflectionId));
    } catch (error) {
      toast.error("Erreur lors de la suppression");
    }
  };

  const handleGenerateSummary = async () => {
    setIsGeneratingSummary(true);
    try {
      const token = localStorage.getItem("infinea_token");
      const response = await fetch(`${API}/reflections/summary`, {
        credentials: "include",
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!response.ok) throw new Error("Erreur");

      const data = await response.json();
      if (data.summary) {
        setSummary({ summary: data.summary, created_at: new Date().toISOString() });
        toast.success("Résumé généré!");
      } else {
        toast.info(data.message);
      }
    } catch (error) {
      toast.error("Erreur lors de la génération");
    } finally {
      setIsGeneratingSummary(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now - date;
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) return "Aujourd'hui";
    if (days === 1) return "Hier";
    if (days < 7) return `Il y a ${days} jours`;
    return date.toLocaleDateString("fr-FR", { day: "numeric", month: "short" });
  };

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
        to="/journal"
        className="nav-item active flex items-center gap-3 px-4 py-3 rounded-xl"
        onClick={() => mobile && setMobileMenuOpen(false)}
      >
        <Brain className="w-5 h-5" />
        <span>Journal</span>
      </Link>
      <Link
        to="/integrations"
        className="nav-item flex items-center gap-3 px-4 py-3 rounded-xl text-muted-foreground hover:text-foreground"
        onClick={() => mobile && setMobileMenuOpen(false)}
      >
        <Calendar className="w-5 h-5" />
        <span>Intégrations</span>
      </Link>
      <Link
        to="/badges"
        className="nav-item flex items-center gap-3 px-4 py-3 rounded-xl text-muted-foreground hover:text-foreground"
        onClick={() => mobile && setMobileMenuOpen(false)}
      >
        <Award className="w-5 h-5" />
        <span>Badges</span>
      </Link>
      <Link
        to="/progress"
        className="nav-item flex items-center gap-3 px-4 py-3 rounded-xl text-muted-foreground hover:text-foreground"
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
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="font-heading text-3xl font-semibold mb-2" data-testid="journal-title">
                Mon Journal
              </h1>
              <p className="text-muted-foreground">
                Votre compagnon cognitif pour suivre vos réflexions
              </p>
            </div>
            <Button onClick={() => setShowNewReflection(true)} data-testid="new-reflection-btn">
              <Plus className="w-4 h-4 mr-2" />
              Nouvelle réflexion
            </Button>
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : (
            <>
              {/* AI Summary Card */}
              <Card className="mb-8 bg-gradient-to-br from-primary/5 to-purple-500/5 border-primary/20">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
                        <Brain className="w-6 h-6 text-primary" />
                      </div>
                      <div>
                        <CardTitle className="font-heading text-xl">Insights IA</CardTitle>
                        <CardDescription>
                          {summary
                            ? `Dernière analyse: ${formatDate(summary.created_at)}`
                            : "Générez votre premier résumé"}
                        </CardDescription>
                      </div>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleGenerateSummary}
                      disabled={isGeneratingSummary}
                      data-testid="generate-summary-btn"
                    >
                      {isGeneratingSummary ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <RefreshCw className="w-4 h-4 mr-2" />
                      )}
                      Analyser
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  {summary?.summary ? (
                    <div className="space-y-4">
                      {/* Weekly Insight */}
                      {summary.summary.weekly_insight && (
                        <div className="p-4 rounded-xl bg-white/5">
                          <div className="flex items-center gap-2 mb-2">
                            <Lightbulb className="w-4 h-4 text-amber-500" />
                            <span className="text-sm font-medium text-amber-500">Observation clé</span>
                          </div>
                          <p className="text-sm">{summary.summary.weekly_insight}</p>
                        </div>
                      )}

                      <div className="grid md:grid-cols-2 gap-4">
                        {/* Patterns */}
                        {summary.summary.patterns_identified?.length > 0 && (
                          <div className="p-4 rounded-xl bg-white/5">
                            <div className="flex items-center gap-2 mb-2">
                              <TrendingUp className="w-4 h-4 text-blue-500" />
                              <span className="text-sm font-medium">Patterns identifiés</span>
                            </div>
                            <ul className="space-y-1">
                              {summary.summary.patterns_identified.map((p, i) => (
                                <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                                  <span className="text-primary">•</span>
                                  {p}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* Strengths */}
                        {summary.summary.strengths?.length > 0 && (
                          <div className="p-4 rounded-xl bg-emerald-500/5 border border-emerald-500/10">
                            <div className="flex items-center gap-2 mb-2">
                              <Zap className="w-4 h-4 text-emerald-500" />
                              <span className="text-sm font-medium text-emerald-500">Points forts</span>
                            </div>
                            <ul className="space-y-1">
                              {summary.summary.strengths.map((s, i) => (
                                <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                                  <span className="text-emerald-500">✓</span>
                                  {s}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>

                      {/* Personalized Tip */}
                      {summary.summary.personalized_tip && (
                        <div className="p-4 rounded-xl bg-primary/10 border border-primary/20">
                          <div className="flex items-center gap-2 mb-2">
                            <Target className="w-4 h-4 text-primary" />
                            <span className="text-sm font-medium">Conseil personnalisé</span>
                          </div>
                          <p className="text-sm">{summary.summary.personalized_tip}</p>
                        </div>
                      )}

                      {/* Mood Trend */}
                      {summary.summary.mood_trend && (
                        <div className="flex items-center gap-2">
                          <Heart className="w-4 h-4 text-rose-500" />
                          <span className="text-sm text-muted-foreground">
                            Tendance d'humeur:{" "}
                            <Badge variant="secondary" className="ml-1">
                              {summary.summary.mood_trend}
                            </Badge>
                          </span>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <Brain className="w-12 h-12 text-muted-foreground mx-auto mb-4 opacity-50" />
                      <p className="text-muted-foreground mb-4">
                        Ajoutez quelques réflexions puis cliquez sur "Analyser" pour obtenir des insights personnalisés
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Reflections List */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h2 className="font-heading text-xl font-semibold">Mes réflexions</h2>
                  <Badge variant="secondary">{reflections.length} entrées</Badge>
                </div>

                {reflections.length === 0 ? (
                  <Card className="py-12">
                    <div className="text-center">
                      <BookOpen className="w-12 h-12 text-muted-foreground mx-auto mb-4 opacity-50" />
                      <p className="text-muted-foreground mb-4">
                        Aucune réflexion pour le moment
                      </p>
                      <Button variant="outline" onClick={() => setShowNewReflection(true)}>
                        <Plus className="w-4 h-4 mr-2" />
                        Ajouter ma première réflexion
                      </Button>
                    </div>
                  </Card>
                ) : (
                  <div className="space-y-3">
                    {reflections.map((reflection) => {
                      const MoodIcon = moodIcons[reflection.mood]?.icon || Meh;
                      const moodStyle = moodIcons[reflection.mood] || moodIcons.neutral;

                      return (
                        <Card key={reflection.reflection_id} className="group" data-testid={`reflection-${reflection.reflection_id}`}>
                          <CardContent className="p-4">
                            <div className="flex items-start justify-between gap-4">
                              <div className="flex items-start gap-3 flex-1">
                                <div className={`w-10 h-10 rounded-xl ${moodStyle.bg} flex items-center justify-center shrink-0`}>
                                  <MoodIcon className={`w-5 h-5 ${moodStyle.color}`} />
                                </div>
                                <div className="flex-1 min-w-0">
                                  <p className="text-sm mb-2">{reflection.content}</p>
                                  <div className="flex items-center gap-3 text-xs text-muted-foreground">
                                    <span>{formatDate(reflection.created_at)}</span>
                                    {reflection.related_category && (
                                      <>
                                        <span>•</span>
                                        <Badge variant="outline" className="text-xs">
                                          {categoryLabels[reflection.related_category] || reflection.related_category}
                                        </Badge>
                                      </>
                                    )}
                                  </div>
                                </div>
                              </div>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
                                onClick={() => handleDeleteReflection(reflection.reflection_id)}
                              >
                                <Trash2 className="w-4 h-4 text-destructive" />
                              </Button>
                            </div>
                          </CardContent>
                        </Card>
                      );
                    })}
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </main>

      {/* New Reflection Dialog */}
      <Dialog open={showNewReflection} onOpenChange={setShowNewReflection}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Brain className="w-5 h-5 text-primary" />
              Nouvelle réflexion
            </DialogTitle>
            <DialogDescription>
              Notez vos pensées, idées ou observations du moment
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <Textarea
              placeholder="Qu'avez-vous en tête? Comment vous sentez-vous après cette session?"
              value={newReflection.content}
              onChange={(e) => setNewReflection({ ...newReflection, content: e.target.value })}
              className="min-h-[120px] resize-none"
              data-testid="reflection-textarea"
            />

            <div className="space-y-2">
              <label className="text-sm text-muted-foreground">Comment vous sentez-vous?</label>
              <div className="flex gap-2">
                {Object.entries(moodIcons).map(([key, mood]) => {
                  const Icon = mood.icon;
                  return (
                    <button
                      key={key}
                      onClick={() => setNewReflection({ ...newReflection, mood: key })}
                      className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-xl border transition-colors ${
                        newReflection.mood === key
                          ? `${mood.bg} border-transparent ${mood.color}`
                          : "border-border hover:border-primary/50"
                      }`}
                      data-testid={`mood-${key}-btn`}
                    >
                      <Icon className="w-5 h-5" />
                      <span className="text-sm">{mood.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm text-muted-foreground">Catégorie associée (optionnel)</label>
              <Select
                value={newReflection.category || "none"}
                onValueChange={(v) => setNewReflection({ ...newReflection, category: v === "none" ? null : v })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Choisir une catégorie" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">Aucune</SelectItem>
                  <SelectItem value="learning">Apprentissage</SelectItem>
                  <SelectItem value="productivity">Productivité</SelectItem>
                  <SelectItem value="well_being">Bien-être</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowNewReflection(false)}>
              Annuler
            </Button>
            <Button onClick={handleCreateReflection} data-testid="save-reflection-btn">
              Enregistrer
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
