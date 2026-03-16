import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
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

const NOTES_TABS = [
  { key: "notes", label: "Mes Notes", icon: FileText },
  { key: "analyse", label: "Analyse IA", icon: Brain },
];

export default function NotesPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState("notes");
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

      <main className="lg:ml-64 pt-20 lg:pt-8 px-4 lg:px-8 pb-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="mb-6">
            <h1 className="font-heading text-3xl font-bold mb-1">Mes Notes</h1>
            <p className="text-sm text-muted-foreground">
              Retrouve et exploite toutes les notes de tes sessions
            </p>
          </div>

          {/* Stats Cards — always visible */}
          {!isLoading && stats && (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-6">
              <Card className="p-3 text-center">
                <FileText className="w-4 h-4 text-primary mx-auto mb-1" />
                <div className="text-lg font-bold">{stats.total_notes || 0}</div>
                <div className="text-[10px] text-muted-foreground">Notes totales</div>
              </Card>
              <Card className="p-3 text-center">
                <TrendingUp className="w-4 h-4 text-emerald-500 mx-auto mb-1" />
                <div className="text-lg font-bold">{stats.notes_this_week || 0}</div>
                <div className="text-[10px] text-muted-foreground">Cette semaine</div>
              </Card>
              <Card className="p-3 text-center">
                <Sparkles className="w-4 h-4 text-amber-500 mx-auto mb-1" />
                <div className="text-lg font-bold">{stats.avg_note_length || 0}</div>
                <div className="text-[10px] text-muted-foreground">Car. moyens</div>
              </Card>
            </div>
          )}

          {/* ── Tab Switcher ── */}
          <div className="flex gap-1 p-1 mb-6 bg-muted/30 rounded-xl">
            {NOTES_TABS.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.key;
              return (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-all ${
                    isActive
                      ? "bg-background shadow-sm text-foreground"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                  {tab.key === "notes" && notes.length > 0 && (
                    <span className="text-[10px] bg-muted rounded-full px-1.5 py-0.5">{stats?.total_notes || notes.length}</span>
                  )}
                  {tab.key === "analyse" && analysis?.analysis && (
                    <span className="w-1.5 h-1.5 rounded-full bg-primary" />
                  )}
                </button>
              );
            })}
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : (
            <>
              {/* ══════════ MES NOTES TAB ══════════ */}
              {activeTab === "notes" && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h2 className="font-heading text-lg font-semibold">Toutes mes notes</h2>
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
                          Complète des sessions et ajoute des notes pour les retrouver ici
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
              )}

              {/* ══════════ ANALYSE IA TAB ══════════ */}
              {activeTab === "analyse" && (
                <div className="space-y-4">
                  {/* Header with generate button */}
                  <div className="flex items-center justify-between">
                    <h2 className="font-heading text-lg font-semibold">Analyse de tes notes</h2>
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
                      {analysis?.analysis ? "Actualiser" : "Générer l'analyse"}
                    </Button>
                  </div>

                  {analysis && (
                    <p className="text-xs text-muted-foreground">{analysis.note_count} notes analysées</p>
                  )}

                  {analysisError ? (
                    <Card className="p-8 text-center border-dashed">
                      <Lock className="w-10 h-10 text-muted-foreground mx-auto mb-3 opacity-50" />
                      <p className="text-sm text-muted-foreground mb-3">{analysisError.message}</p>
                      <Link to="/pricing">
                        <Button size="sm">
                          <Crown className="w-4 h-4 mr-2" />
                          Passer Premium
                        </Button>
                      </Link>
                    </Card>
                  ) : analysis?.analysis ? (
                    <div className="space-y-4">
                      {/* Key Insight */}
                      {analysis.analysis.key_insight && (
                        <Card className="p-4 border-amber-500/20 bg-gradient-to-br from-amber-500/5 to-transparent">
                          <div className="flex items-start gap-3">
                            <div className="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center shrink-0">
                              <Lightbulb className="w-4 h-4 text-amber-500" />
                            </div>
                            <div>
                              <span className="text-xs font-semibold text-amber-500 uppercase tracking-wide">Observation clé</span>
                              <p className="text-sm mt-1 text-foreground/80 leading-relaxed">{analysis.analysis.key_insight}</p>
                            </div>
                          </div>
                        </Card>
                      )}

                      {/* Patterns + Strengths side-by-side */}
                      <div className="grid md:grid-cols-2 gap-3">
                        {analysis.analysis.patterns?.length > 0 && (
                          <Card className="p-4">
                            <div className="flex items-center gap-2 mb-3">
                              <TrendingUp className="w-4 h-4 text-blue-500" />
                              <span className="text-sm font-semibold">Patterns identifiés</span>
                            </div>
                            <div className="space-y-2">
                              {analysis.analysis.patterns.map((p, i) => (
                                <p key={i} className="text-xs text-foreground/70 leading-relaxed flex items-start gap-2">
                                  <span className="text-blue-500 mt-0.5 shrink-0">•</span>
                                  {p}
                                </p>
                              ))}
                            </div>
                          </Card>
                        )}

                        {analysis.analysis.strengths?.length > 0 && (
                          <Card className="p-4 border-emerald-500/10">
                            <div className="flex items-center gap-2 mb-3">
                              <Zap className="w-4 h-4 text-emerald-500" />
                              <span className="text-sm font-semibold text-emerald-500">Points forts</span>
                            </div>
                            <div className="space-y-2">
                              {analysis.analysis.strengths.map((s, i) => (
                                <p key={i} className="text-xs text-foreground/70 leading-relaxed flex items-start gap-2">
                                  <span className="text-emerald-500 mt-0.5 shrink-0">•</span>
                                  {s}
                                </p>
                              ))}
                            </div>
                          </Card>
                        )}
                      </div>

                      {/* Growth Areas */}
                      {analysis.analysis.growth_areas?.length > 0 && (
                        <Card className="p-4">
                          <div className="flex items-center gap-2 mb-3">
                            <Target className="w-4 h-4 text-orange-500" />
                            <span className="text-sm font-semibold text-orange-500">Axes de progression</span>
                          </div>
                          <div className="space-y-2">
                            {analysis.analysis.growth_areas.map((g, i) => (
                              <p key={i} className="text-xs text-foreground/70 leading-relaxed flex items-start gap-2">
                                <span className="text-orange-500 mt-0.5 shrink-0">→</span>
                                {g}
                              </p>
                            ))}
                          </div>
                        </Card>
                      )}

                      {/* Personalized Recommendation */}
                      {analysis.analysis.personalized_recommendation && (
                        <Card className="p-4 border-primary/15 bg-gradient-to-br from-primary/5 to-transparent">
                          <div className="flex items-start gap-3">
                            <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                              <Target className="w-4 h-4 text-primary" />
                            </div>
                            <div>
                              <span className="text-xs font-semibold text-primary uppercase tracking-wide">Conseil personnalisé</span>
                              <p className="text-sm mt-1 text-foreground/80 leading-relaxed">{analysis.analysis.personalized_recommendation}</p>
                            </div>
                          </div>
                        </Card>
                      )}

                      {/* Premium-only fields */}
                      {analysis.analysis.emotional_trends && (
                        <Card className="p-4">
                          <div className="flex items-start gap-3">
                            <Heart className="w-4 h-4 text-rose-500 mt-0.5 shrink-0" />
                            <p className="text-sm text-foreground/70 leading-relaxed">{analysis.analysis.emotional_trends}</p>
                          </div>
                        </Card>
                      )}

                      {analysis.analysis.connections && (
                        <Card className="p-4">
                          <div className="flex items-start gap-3">
                            <Sparkles className="w-4 h-4 text-indigo-500 mt-0.5 shrink-0" />
                            <p className="text-sm text-foreground/70 leading-relaxed">{analysis.analysis.connections}</p>
                          </div>
                        </Card>
                      )}

                      {analysis.analysis.focus_suggestion && (
                        <Card className="p-3">
                          <div className="flex items-center gap-3">
                            <Target className="w-4 h-4 text-indigo-500" />
                            <span className="text-sm text-muted-foreground">Focus suggéré :</span>
                            <Badge variant="secondary">{analysis.analysis.focus_suggestion}</Badge>
                          </div>
                        </Card>
                      )}
                    </div>
                  ) : (
                    <Card className="p-12 text-center border-dashed">
                      <Brain className="w-12 h-12 text-muted-foreground/20 mx-auto mb-4" />
                      <h4 className="font-heading font-semibold text-sm mb-2">Analyse non disponible</h4>
                      <p className="text-xs text-muted-foreground mb-4 max-w-sm mx-auto">
                        {stats?.total_notes >= 3
                          ? "Clique sur \"Générer l'analyse\" pour obtenir des insights personnalisés sur tes notes."
                          : `Encore ${3 - (stats?.total_notes || 0)} note(s) avant ta première analyse.`}
                      </p>
                      <Button variant="outline" size="sm" onClick={handleGenerateAnalysis} disabled={isAnalyzing}>
                        {isAnalyzing ? (
                          <Loader2 className="w-4 h-4 animate-spin mr-2" />
                        ) : (
                          <Brain className="w-4 h-4 mr-2" />
                        )}
                        Générer l'analyse
                      </Button>
                    </Card>
                  )}
                </div>
              )}
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
