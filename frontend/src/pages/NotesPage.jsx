import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Sparkles,
  Brain,
  Lightbulb,
  TrendingUp,
  Heart,
  FileText,
  RefreshCw,
  Loader2,
  Target,
  Zap,
  Crown,
  Lock,
  ChevronDown,
  Trash2,
} from "lucide-react";
import { toast } from "sonner";
import { API, useAuth, authFetch } from "@/App";
import Sidebar from "@/components/Sidebar";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

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

export default function NotesPage() {
  const { user } = useAuth();
  const [notes, setNotes] = useState([]);
  const [stats, setStats] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [analysisError, setAnalysisError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [hasMore, setHasMore] = useState(false);
  const [skip, setSkip] = useState(0);
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [deleteTarget, setDeleteTarget] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [notesRes, statsRes, analysisRes] = await Promise.all([
        authFetch(`${API}/notes?limit=20`),
        authFetch(`${API}/notes/stats`),
        authFetch(`${API}/notes/analysis`),
      ]);

      if (notesRes.ok) {
        const data = await notesRes.json();
        setNotes(data.notes);
        setHasMore(data.has_more);
      }
      if (statsRes.ok) {
        setStats(await statsRes.json());
      }
      if (analysisRes.ok) {
        const data = await analysisRes.json();
        if (data.analysis) {
          setAnalysis(data);
        } else if (data.error === "limit_reached") {
          setAnalysisError(data);
        }
      }
    } catch (error) {
      toast.error("Erreur de chargement");
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateAnalysis = async () => {
    setIsAnalyzing(true);
    setAnalysisError(null);
    try {
      const response = await authFetch(`${API}/notes/analysis?force=true`);
      const data = await response.json();
      if (data.analysis) {
        setAnalysis(data);
        toast.success("Analyse générée !");
      } else if (data.error === "limit_reached") {
        setAnalysisError(data);
        toast.error("Limite d'analyses atteinte aujourd'hui");
      } else if (data.message) {
        toast.info(data.message);
      }
    } catch (error) {
      toast.error("Erreur lors de l'analyse");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleCategoryFilter = async (value) => {
    setCategoryFilter(value);
    setSkip(0);
    try {
      const catParam = value === "all" ? "" : `&category=${value}`;
      const res = await authFetch(`${API}/notes?limit=20${catParam}`);
      if (res.ok) {
        const data = await res.json();
        setNotes(data.notes);
        setHasMore(data.has_more);
      }
    } catch (error) {
      toast.error("Erreur de filtrage");
    }
  };

  const loadMore = async () => {
    const newSkip = skip + 20;
    const catParam = categoryFilter === "all" ? "" : `&category=${categoryFilter}`;
    try {
      const res = await authFetch(`${API}/notes?skip=${newSkip}&limit=20${catParam}`);
      if (res.ok) {
        const data = await res.json();
        setNotes((prev) => [...prev, ...data.notes]);
        setHasMore(data.has_more);
        setSkip(newSkip);
      }
    } catch (error) {
      toast.error("Erreur de chargement");
    }
  };

  const handleDeleteNote = async () => {
    if (!deleteTarget) return;
    try {
      const res = await authFetch(`${API}/notes/${deleteTarget}`, { method: "DELETE" });
      if (!res.ok) throw new Error();
      setNotes((prev) => prev.filter((n) => n.session_id !== deleteTarget));
      setStats((prev) => prev ? { ...prev, total_notes: Math.max(0, prev.total_notes - 1) } : prev);
      toast.success("Note supprimée");
    } catch {
      toast.error("Erreur lors de la suppression");
    } finally {
      setDeleteTarget(null);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "";
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now - date;
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    if (days === 0) return "Aujourd'hui";
    if (days === 1) return "Hier";
    if (days < 7) return `Il y a ${days} jours`;
    return date.toLocaleDateString("fr-FR", { day: "numeric", month: "short" });
  };

  const isPremium = user?.subscription_tier === "premium";

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />

      {/* Main Content */}
      <main className="lg:ml-64 pt-20 lg:pt-8 px-4 lg:px-8 pb-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="font-heading text-3xl font-bold mb-2">Mes Notes</h1>
            <p className="text-muted-foreground">
              Retrouvez et exploitez toutes les notes de vos sessions
            </p>
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : (
            <>
              {/* Stats Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                <Card>
                  <CardContent className="p-4 flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
                      <FileText className="w-6 h-6 text-primary" />
                    </div>
                    <div>
                      <p className="text-2xl font-heading font-bold">{stats?.total_notes || 0}</p>
                      <p className="text-sm text-muted-foreground">Notes totales</p>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4 flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-emerald-500/10 flex items-center justify-center">
                      <TrendingUp className="w-6 h-6 text-emerald-500" />
                    </div>
                    <div>
                      <p className="text-2xl font-heading font-bold">{stats?.notes_this_week || 0}</p>
                      <p className="text-sm text-muted-foreground">Cette semaine</p>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4 flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-amber-500/10 flex items-center justify-center">
                      <Sparkles className="w-6 h-6 text-amber-500" />
                    </div>
                    <div>
                      <p className="text-2xl font-heading font-bold">{stats?.avg_note_length || 0}</p>
                      <p className="text-sm text-muted-foreground">Caractères moy.</p>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* AI Analysis Card */}
              <Card className="mb-8 bg-gradient-to-br from-primary/5 to-purple-500/5 border-primary/20">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
                        <Brain className="w-6 h-6 text-primary" />
                      </div>
                      <div>
                        <CardTitle className="font-heading text-xl">Analyse de vos notes</CardTitle>
                        <CardDescription>
                          {analysis
                            ? `${analysis.note_count} notes analysées`
                            : "Générez votre première analyse personnalisée"}
                        </CardDescription>
                      </div>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleGenerateAnalysis}
                      disabled={isAnalyzing}
                    >
                      {isAnalyzing ? (
                        <Loader2 className="w-4 h-4 animate-spin mr-2" />
                      ) : (
                        <RefreshCw className="w-4 h-4 mr-2" />
                      )}
                      Analyser
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  {analysisError ? (
                    <div className="text-center py-6">
                      <Lock className="w-10 h-10 text-muted-foreground mx-auto mb-3 opacity-50" />
                      <p className="text-muted-foreground mb-3">{analysisError.message}</p>
                      <Link to="/pricing">
                        <Button size="sm">
                          <Crown className="w-4 h-4 mr-2" />
                          Passer Premium
                        </Button>
                      </Link>
                    </div>
                  ) : analysis?.analysis ? (
                    <div className="space-y-4">
                      {/* Key Insight */}
                      {analysis.analysis.key_insight && (
                        <div className="p-4 rounded-xl bg-white/5">
                          <div className="flex items-center gap-2 mb-2">
                            <Lightbulb className="w-4 h-4 text-amber-500" />
                            <span className="text-sm font-medium text-amber-500">Observation clé</span>
                          </div>
                          <p className="text-sm leading-relaxed">{analysis.analysis.key_insight}</p>
                        </div>
                      )}

                      <div className="grid md:grid-cols-2 gap-4">
                        {/* Patterns */}
                        {analysis.analysis.patterns?.length > 0 && (
                          <div className="p-4 rounded-xl bg-white/5">
                            <div className="flex items-center gap-2 mb-2">
                              <TrendingUp className="w-4 h-4 text-blue-500" />
                              <span className="text-sm font-medium text-blue-500">Patterns identifiés</span>
                            </div>
                            <ul className="space-y-1">
                              {analysis.analysis.patterns.map((p, i) => (
                                <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                                  <span className="text-blue-500 mt-0.5">•</span>
                                  <span>{p}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* Strengths */}
                        {analysis.analysis.strengths?.length > 0 && (
                          <div className="p-4 rounded-xl bg-emerald-500/5 border border-emerald-500/10">
                            <div className="flex items-center gap-2 mb-2">
                              <Zap className="w-4 h-4 text-emerald-500" />
                              <span className="text-sm font-medium text-emerald-500">Points forts</span>
                            </div>
                            <ul className="space-y-1">
                              {analysis.analysis.strengths.map((s, i) => (
                                <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                                  <span className="text-emerald-500 mt-0.5">+</span>
                                  <span>{s}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>

                      {/* Growth Areas */}
                      {analysis.analysis.growth_areas?.length > 0 && (
                        <div className="p-4 rounded-xl bg-white/5">
                          <div className="flex items-center gap-2 mb-2">
                            <Target className="w-4 h-4 text-orange-500" />
                            <span className="text-sm font-medium text-orange-500">Axes de progression</span>
                          </div>
                          <ul className="space-y-1">
                            {analysis.analysis.growth_areas.map((g, i) => (
                              <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                                <span className="text-orange-500 mt-0.5">→</span>
                                <span>{g}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Personalized Recommendation */}
                      {analysis.analysis.personalized_recommendation && (
                        <div className="p-4 rounded-xl bg-primary/10 border border-primary/20">
                          <div className="flex items-center gap-2 mb-2">
                            <Target className="w-4 h-4 text-primary" />
                            <span className="text-sm font-medium text-primary">Conseil personnalisé</span>
                          </div>
                          <p className="text-sm leading-relaxed">{analysis.analysis.personalized_recommendation}</p>
                        </div>
                      )}

                      {/* Premium-only fields */}
                      {analysis.analysis.emotional_trends && (
                        <div className="flex items-start gap-3 p-3 rounded-xl bg-white/5">
                          <Heart className="w-4 h-4 text-rose-500 mt-0.5 shrink-0" />
                          <p className="text-sm text-muted-foreground">{analysis.analysis.emotional_trends}</p>
                        </div>
                      )}

                      {analysis.analysis.connections && (
                        <div className="flex items-start gap-3 p-3 rounded-xl bg-white/5">
                          <Sparkles className="w-4 h-4 text-indigo-500 mt-0.5 shrink-0" />
                          <p className="text-sm text-muted-foreground">{analysis.analysis.connections}</p>
                        </div>
                      )}

                      {analysis.analysis.focus_suggestion && (
                        <div className="flex items-center gap-2 pt-2">
                          <Target className="w-4 h-4 text-indigo-500" />
                          <span className="text-sm text-muted-foreground">Focus :</span>
                          <Badge variant="secondary">{analysis.analysis.focus_suggestion}</Badge>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <Brain className="w-12 h-12 text-muted-foreground mx-auto mb-4 opacity-50" />
                      <p className="text-muted-foreground mb-2">
                        {stats?.total_notes >= 3
                          ? "Cliquez sur \"Analyser\" pour générer votre analyse personnalisée"
                          : `Encore ${3 - (stats?.total_notes || 0)} note(s) avant votre première analyse`}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        L'IA analyse vos notes pour identifier patterns, forces et axes de progression
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Notes Timeline */}
              <div className="mb-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <h2 className="font-heading text-xl font-semibold">Toutes mes notes</h2>
                    <Badge variant="secondary">{stats?.total_notes || 0}</Badge>
                  </div>
                  {stats?.categories && Object.keys(stats.categories).length > 1 && (
                    <Select value={categoryFilter} onValueChange={handleCategoryFilter}>
                      <SelectTrigger className="w-[180px]">
                        <SelectValue placeholder="Catégorie" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">Toutes</SelectItem>
                        {Object.keys(stats.categories).map((cat) => (
                          <SelectItem key={cat} value={cat}>
                            {categoryLabels[cat] || cat} ({stats.categories[cat]})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                </div>

                {notes.length > 0 ? (
                  <div className="space-y-3">
                    {notes.map((note) => (
                      <Card key={note.session_id} className="group hover:border-primary/30 transition-colors">
                        <CardContent className="p-4">
                          <div className="flex items-start gap-3">
                            <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${categoryColors[note.category] || "bg-primary/10 text-primary"}`}>
                              <FileText className="w-5 h-5" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm leading-relaxed mb-2">{note.notes}</p>
                              <div className="flex items-center gap-3 text-xs text-muted-foreground flex-wrap">
                                <span>{formatDate(note.completed_at)}</span>
                                <span className="opacity-30">•</span>
                                <span className="font-medium text-foreground">{note.action_title}</span>
                                <Badge variant="outline" className="text-xs">
                                  {categoryLabels[note.category] || note.category}
                                </Badge>
                                <span>{note.actual_duration} min</span>
                              </div>
                            </div>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="opacity-0 group-hover:opacity-100 transition-opacity shrink-0 text-muted-foreground hover:text-red-500"
                              onClick={() => setDeleteTarget(note.session_id)}
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    ))}

                    {hasMore && (
                      <div className="text-center pt-4">
                        <Button variant="outline" onClick={loadMore}>
                          <ChevronDown className="w-4 h-4 mr-2" />
                          Charger plus
                        </Button>
                      </div>
                    )}
                  </div>
                ) : (
                  <Card className="py-12">
                    <div className="text-center">
                      <FileText className="w-12 h-12 text-muted-foreground mx-auto mb-4 opacity-50" />
                      <p className="text-muted-foreground mb-2">Aucune note pour le moment</p>
                      <p className="text-xs text-muted-foreground mb-4">
                        Complétez des sessions et ajoutez des notes pour les retrouver ici
                      </p>
                      <Link to="/actions">
                        <Button variant="outline" size="sm">
                          <Sparkles className="w-4 h-4 mr-2" />
                          Commencer une action
                        </Button>
                      </Link>
                    </div>
                  </Card>
                )}
              </div>
            </>
          )}
        </div>
      </main>

      {/* Delete Confirmation Dialog */}
      <Dialog open={!!deleteTarget} onOpenChange={(open) => !open && setDeleteTarget(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Supprimer cette note ?</DialogTitle>
            <DialogDescription>
              Cette action est irréversible. La note sera définitivement supprimée.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setDeleteTarget(null)}>
              Annuler
            </Button>
            <Button variant="destructive" onClick={handleDeleteNote}>
              <Trash2 className="w-4 h-4 mr-2" />
              Supprimer
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
