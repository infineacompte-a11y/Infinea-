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
  positive: { icon: Smile, color: "text-[#5DB786]", bg: "bg-[#5DB786]/40", label: "Positif" },
  neutral: { icon: Meh, color: "text-[#E48C75]", bg: "bg-[#E48C75]/40", label: "Neutre" },
  negative: { icon: Frown, color: "text-[#E48C75]", bg: "bg-[#E48C75]/40", label: "Difficile" },
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
    <div className="min-h-screen app-bg-mesh">
      <Sidebar />
      <main className="lg:ml-64 pt-14 lg:pt-0 pb-8">
        <div className="section-dark-header px-4 lg:px-8 pt-8 lg:pt-10 pb-8">
          <div className="max-w-4xl mx-auto flex items-center justify-between">
            <div>
              <h1 className="text-display text-3xl lg:text-4xl font-semibold text-white opacity-0 animate-fade-in" data-testid="journal-title">
                Journal
              </h1>
              <p className="text-white/60 text-sm mt-1 opacity-0 animate-fade-in" style={{ animationDelay: "50ms" }}>
                Votre espace de réflexion personnelle
              </p>
            </div>
            <Button onClick={() => setShowNewReflection(true)} className="rounded-xl shadow-md hover:shadow-lg transition-all duration-200 btn-press" data-testid="new-reflection-btn">
              <Plus className="w-4 h-4 mr-2" />
              Nouvelle réflexion
            </Button>
          </div>
        </div>
        <div className="px-4 lg:px-8">
        <div className="max-w-4xl mx-auto">

          {/* ── Tab Switcher ── */}
          <div className="opacity-0 animate-fade-in flex gap-1 p-1 mb-6 bg-muted/30 rounded-xl" style={{ animationDelay: "100ms", animationFillMode: "forwards" }}>
            {JOURNAL_TABS.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.key;
              return (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 btn-press ${
                    isActive
                      ? "bg-background shadow-sm shadow-[0_1px_3px_rgba(39,82,85,0.08)] text-foreground scale-[1.01]"
                      : "text-muted-foreground hover:text-foreground hover:bg-background/50"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                  {tab.key === "reflexions" && reflections.length > 0 && (
                    <span className="text-[10px] bg-muted rounded-full px-1.5 py-0.5 tabular-nums">{reflections.length}</span>
                  )}
                  {tab.key === "analyse" && summary?.summary && (
                    <span className="w-1.5 h-1.5 rounded-full bg-primary" />
                  )}
                </button>
              );
            })}
          </div>

          {isLoading ? (
            <div className="opacity-0 animate-fade-in flex flex-col items-center justify-center py-20 gap-3" style={{ animationDelay: "200ms", animationFillMode: "forwards" }}>
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
              <p className="text-sm text-muted-foreground">Chargement...</p>
            </div>
          ) : (
            <>
              {/* REFLEXIONS TAB */}
              {activeTab === "reflexions" && (
                <div className="opacity-0 animate-fade-in space-y-4" style={{ animationDelay: "200ms", animationFillMode: "forwards" }}>
                  <div className="flex items-center justify-between">
                    <h2 className="font-sans font-semibold tracking-tight text-lg font-semibold">Mes réflexions</h2>
                    <Badge variant="secondary" className="rounded-lg tabular-nums">{reflections.length} entrées</Badge>
                  </div>

                  {reflections.length === 0 ? (
                    <Card className="py-12">
                      <div className="text-center">
                        <div className="bg-gradient-to-br from-[#459492]/20 to-transparent rounded-2xl w-16 h-16 flex items-center justify-center mx-auto mb-4">
                          <BookOpen className="w-8 h-8 text-[#459492]" />
                        </div>
                        <p className="text-muted-foreground mb-4">
                          Aucune réflexion pour le moment
                        </p>
                        <Button variant="outline" onClick={() => setShowNewReflection(true)} className="rounded-xl shadow-md hover:shadow-lg transition-all duration-200 btn-press">
                          <Plus className="w-4 h-4 mr-2" />
                          Ajouter ma première réflexion
                        </Button>
                      </div>
                    </Card>
                  ) : (
                    <div className="space-y-3">
                      {reflections.map((reflection, index) => {
                        const MoodIcon = moodIcons[reflection.mood]?.icon || Meh;
                        const moodStyle = moodIcons[reflection.mood] || moodIcons.neutral;

                        return (
                          <Card key={reflection.reflection_id} className="opacity-0 animate-fade-in group hover:shadow-lg hover:border-[#459492]/30 hover:-translate-y-0.5 active:translate-y-px transition-all duration-200" style={{ animationDelay: `${index * 50}ms`, animationFillMode: "forwards" }} data-testid={`reflection-${reflection.reflection_id}`}>
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
                                          <Badge variant="outline" className="text-xs rounded-lg">
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
                                  className="opacity-0 group-hover:opacity-100 transition-all duration-200 shrink-0 hover:bg-muted/80 rounded-xl"
                                  onClick={() => handleDeleteReflection(reflection.reflection_id)}
                                >
                                  <Trash2 className="w-4 h-4 text-[#E48C75]" />
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

              {/* ANALYSE IA TAB */}
              {activeTab === "analyse" && (
                <div className="opacity-0 animate-fade-in space-y-4" style={{ animationDelay: "200ms", animationFillMode: "forwards" }}>
                  {/* Generate button */}
                  <div className="flex items-center justify-between">
                    <h2 className="font-sans font-semibold tracking-tight text-lg font-semibold">Analyse IA</h2>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleGenerateSummary}
                      disabled={isGeneratingSummary}
                      className="rounded-xl transition-all duration-200 hover:bg-muted/80 btn-press"
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
                        <div className="opacity-0 animate-fade-in" style={{ animationDelay: "300ms", animationFillMode: "forwards" }}>
                          <Card className="p-4 border-[#E48C75]/20 bg-gradient-to-br from-[#E48C75]/5 to-transparent hover:shadow-lg hover:border-[#E48C75]/30 transition-all duration-200">
                            <div className="flex items-start gap-3">
                              <div className="w-8 h-8 rounded-lg bg-[#E48C75]/40 flex items-center justify-center shrink-0">
                                <Lightbulb className="w-4 h-4 text-[#E48C75]" />
                              </div>
                              <div>
                                <span className="text-xs font-semibold text-[#E48C75] uppercase tracking-wide">Observation clé</span>
                                <p className="text-sm mt-1 text-foreground/80 leading-relaxed">{summary.summary.weekly_insight}</p>
                              </div>
                            </div>
                          </Card>
                        </div>
                      )}

                      {/* Patterns + Strengths side-by-side */}
                      <div className="opacity-0 animate-fade-in grid md:grid-cols-2 gap-3" style={{ animationDelay: "400ms", animationFillMode: "forwards" }}>
                        {summary.summary.patterns_identified?.length > 0 && (
                          <Card className="p-4 hover:shadow-lg hover:border-[#459492]/30 transition-all duration-200">
                            <div className="flex items-center gap-2 mb-3">
                              <TrendingUp className="w-4 h-4 text-[#459492]" />
                              <span className="text-sm font-semibold">Patterns identifiés</span>
                            </div>
                            <div className="space-y-2">
                              {summary.summary.patterns_identified.map((p, i) => (
                                <p key={i} className="text-xs text-foreground/70 leading-relaxed flex items-start gap-2">
                                  <span className="text-[#459492] mt-0.5 shrink-0">•</span>
                                  {p}
                                </p>
                              ))}
                            </div>
                          </Card>
                        )}

                        {summary.summary.strengths?.length > 0 && (
                          <Card className="p-4 border-[#5DB786]/10 hover:shadow-lg hover:border-[#5DB786]/30 transition-all duration-200">
                            <div className="flex items-center gap-2 mb-3">
                              <Zap className="w-4 h-4 text-[#5DB786]" />
                              <span className="text-sm font-semibold text-[#5DB786]">Points forts</span>
                            </div>
                            <div className="space-y-2">
                              {summary.summary.strengths.map((s, i) => (
                                <p key={i} className="text-xs text-foreground/70 leading-relaxed flex items-start gap-2">
                                  <span className="text-[#5DB786] mt-0.5 shrink-0">•</span>
                                  {s}
                                </p>
                              ))}
                            </div>
                          </Card>
                        )}
                      </div>

                      {/* Personalized Tip */}
                      {summary.summary.personalized_tip && (
                        <div className="opacity-0 animate-fade-in" style={{ animationDelay: "500ms", animationFillMode: "forwards" }}>
                          <Card className="p-4 border-primary/15 bg-gradient-to-br from-primary/5 to-transparent hover:shadow-lg hover:border-primary/30 transition-all duration-200">
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
                        </div>
                      )}

                      {/* Mood Trend */}
                      {summary.summary.mood_trend && (
                        <div className="opacity-0 animate-fade-in" style={{ animationDelay: "600ms", animationFillMode: "forwards" }}>
                          <Card className="p-4 hover:shadow-lg hover:border-[#459492]/30 transition-all duration-200">
                            <div className="flex items-center gap-3">
                              <Heart className="w-4 h-4 text-[#E48C75]" />
                              <span className="text-sm text-muted-foreground">
                                Tendance d'humeur :
                              </span>
                              <Badge variant="secondary" className="rounded-lg">{summary.summary.mood_trend}</Badge>
                            </div>
                          </Card>
                        </div>
                      )}
                    </div>
                  ) : (
                    <Card className="p-12 text-center border-dashed">
                      <div className="bg-gradient-to-br from-[#459492]/20 to-transparent rounded-2xl w-16 h-16 flex items-center justify-center mx-auto mb-4">
                        <Brain className="w-8 h-8 text-[#459492]" />
                      </div>
                      <h3 className="font-sans font-semibold tracking-tight font-semibold text-sm mb-2">Analyse non disponible</h3>
                      <p className="text-xs text-muted-foreground mb-4 max-w-sm mx-auto">
                        Ajoute quelques réflexions dans l'onglet "Réflexions" puis clique sur "Générer l'analyse" pour obtenir des insights personnalisés.
                      </p>
                      <Button variant="outline" size="sm" onClick={handleGenerateSummary} disabled={isGeneratingSummary} className="rounded-xl shadow-md hover:shadow-lg transition-all duration-200 btn-press">
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
                      className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-xl border transition-all duration-200 ${
                        newReflection.mood === key
                          ? `${mood.bg} border-[#459492]/20 ${mood.color}`
                          : "border-border hover:border-[#459492]/30"
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
            <Button variant="outline" onClick={() => setShowNewReflection(false)} className="rounded-xl transition-all duration-200 hover:bg-muted/80">
              Annuler
            </Button>
            <Button onClick={handleCreateReflection} className="rounded-xl shadow-md hover:shadow-lg transition-all duration-200 btn-press" data-testid="save-reflection-btn">
              Enregistrer
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
