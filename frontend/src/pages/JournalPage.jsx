import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { VoiceTextArea } from "@/components/VoiceInput";
import {
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
  Loader2,
  Target,
  Zap,
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

const JOURNAL_TABS = [
  { key: "reflexions", label: "Réflexions", icon: BookOpen },
  { key: "analyse", label: "Analyse IA", icon: Brain },
];

export default function JournalPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState("reflexions");
  const [reflections, setReflections] = useState([]);
  const [summary, setSummary] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isGeneratingSummary, setIsGeneratingSummary] = useState(false);
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
      const [refRes, sumRes] = await Promise.all([
        authFetch(`${API}/reflections?limit=30`),
        authFetch(`${API}/reflections/summaries?limit=1`),
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
      const response = await authFetch(`${API}/reflections`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
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
      const response = await authFetch(`${API}/reflections/${reflectionId}`, {
        method: "DELETE",
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
      const response = await authFetch(`${API}/reflections/summary`);

      if (!response.ok) throw new Error("Erreur");

      const data = await response.json();
      if (data.summary) {
        setSummary({ summary: data.summary, created_at: new Date().toISOString() });
        toast.success("Analyse générée!");
      } else {
        toast.info(data.message);
      }
    } catch (error) {
      toast.error("Erreur lors de la génération");
    } finally {
      setIsGeneratingSummary(false);
    }
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

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />

      <main className="lg:ml-64 pt-20 lg:pt-8 px-4 lg:px-8 pb-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="font-heading text-3xl font-semibold mb-1" data-testid="journal-title">
                Mon Journal
              </h1>
              <p className="text-sm text-muted-foreground">
                Suivi de tes réflexions et analyse intelligente
              </p>
            </div>
            <Button onClick={() => setShowNewReflection(true)} data-testid="new-reflection-btn">
              <Plus className="w-4 h-4 mr-2" />
              Nouvelle réflexion
            </Button>
          </div>

          {/* ── Tab Switcher ── */}
          <div className="flex gap-1 p-1 mb-6 bg-muted/30 rounded-xl">
            {JOURNAL_TABS.map((tab) => {
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
                  {tab.key === "reflexions" && reflections.length > 0 && (
                    <span className="text-[10px] bg-muted rounded-full px-1.5 py-0.5">{reflections.length}</span>
                  )}
                  {tab.key === "analyse" && summary?.summary && (
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
              {/* ══════════ RÉFLEXIONS TAB ══════════ */}
              {activeTab === "reflexions" && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h2 className="font-heading text-lg font-semibold">Mes réflexions</h2>
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
              )}

              {/* ══════════ ANALYSE IA TAB ══════════ */}
              {activeTab === "analyse" && (
                <div className="space-y-4">
                  {/* Generate button */}
                  <div className="flex items-center justify-between">
                    <h2 className="font-heading text-lg font-semibold">Analyse IA</h2>
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
                      {summary?.summary ? "Actualiser" : "Générer l'analyse"}
                    </Button>
                  </div>

                  {summary?.summary ? (
                    <div className="space-y-4">
                      {/* Last analysis date */}
                      <p className="text-xs text-muted-foreground">
                        Dernière analyse : {formatDate(summary.created_at)}
                      </p>

                      {/* Weekly Insight */}
                      {summary.summary.weekly_insight && (
                        <Card className="p-4 border-amber-500/20 bg-gradient-to-br from-amber-500/5 to-transparent">
                          <div className="flex items-start gap-3">
                            <div className="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center shrink-0">
                              <Lightbulb className="w-4 h-4 text-amber-500" />
                            </div>
                            <div>
                              <span className="text-xs font-semibold text-amber-500 uppercase tracking-wide">Observation clé</span>
                              <p className="text-sm mt-1 text-foreground/80 leading-relaxed">{summary.summary.weekly_insight}</p>
                            </div>
                          </div>
                        </Card>
                      )}

                      {/* Patterns + Strengths side-by-side */}
                      <div className="grid md:grid-cols-2 gap-3">
                        {summary.summary.patterns_identified?.length > 0 && (
                          <Card className="p-4">
                            <div className="flex items-center gap-2 mb-3">
                              <TrendingUp className="w-4 h-4 text-blue-500" />
                              <span className="text-sm font-semibold">Patterns identifiés</span>
                            </div>
                            <div className="space-y-2">
                              {summary.summary.patterns_identified.map((p, i) => (
                                <p key={i} className="text-xs text-foreground/70 leading-relaxed flex items-start gap-2">
                                  <span className="text-blue-500 mt-0.5 shrink-0">•</span>
                                  {p}
                                </p>
                              ))}
                            </div>
                          </Card>
                        )}

                        {summary.summary.strengths?.length > 0 && (
                          <Card className="p-4 border-emerald-500/10">
                            <div className="flex items-center gap-2 mb-3">
                              <Zap className="w-4 h-4 text-emerald-500" />
                              <span className="text-sm font-semibold text-emerald-500">Points forts</span>
                            </div>
                            <div className="space-y-2">
                              {summary.summary.strengths.map((s, i) => (
                                <p key={i} className="text-xs text-foreground/70 leading-relaxed flex items-start gap-2">
                                  <span className="text-emerald-500 mt-0.5 shrink-0">•</span>
                                  {s}
                                </p>
                              ))}
                            </div>
                          </Card>
                        )}
                      </div>

                      {/* Personalized Tip */}
                      {summary.summary.personalized_tip && (
                        <Card className="p-4 border-primary/15 bg-gradient-to-br from-primary/5 to-transparent">
                          <div className="flex items-start gap-3">
                            <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                              <Target className="w-4 h-4 text-primary" />
                            </div>
                            <div>
                              <span className="text-xs font-semibold text-primary uppercase tracking-wide">Conseil personnalisé</span>
                              <p className="text-sm mt-1 text-foreground/80 leading-relaxed">{summary.summary.personalized_tip}</p>
                            </div>
                          </div>
                        </Card>
                      )}

                      {/* Mood Trend */}
                      {summary.summary.mood_trend && (
                        <Card className="p-4">
                          <div className="flex items-center gap-3">
                            <Heart className="w-4 h-4 text-rose-500" />
                            <span className="text-sm text-muted-foreground">
                              Tendance d'humeur :
                            </span>
                            <Badge variant="secondary">{summary.summary.mood_trend}</Badge>
                          </div>
                        </Card>
                      )}
                    </div>
                  ) : (
                    <Card className="p-12 text-center border-dashed">
                      <Brain className="w-12 h-12 text-muted-foreground/20 mx-auto mb-4" />
                      <h4 className="font-heading font-semibold text-sm mb-2">Analyse non disponible</h4>
                      <p className="text-xs text-muted-foreground mb-4 max-w-sm mx-auto">
                        Ajoute quelques réflexions dans l'onglet "Réflexions" puis clique sur "Générer l'analyse" pour obtenir des insights personnalisés.
                      </p>
                      <Button variant="outline" size="sm" onClick={handleGenerateSummary} disabled={isGeneratingSummary}>
                        {isGeneratingSummary ? (
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
            <VoiceTextArea
              value={newReflection.content}
              onChange={(val) => setNewReflection((prev) => ({ ...prev, content: val }))}
              placeholder="Qu'avez-vous en tête? Comment vous sentez-vous après cette session?"
              rows={4}
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
