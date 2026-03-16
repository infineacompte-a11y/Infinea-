import React, { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Target,
  ArrowLeft,
  Flame,
  Clock,
  Calendar,
  Play,
  CheckCircle2,
  Circle,
  Sparkles,
  Loader2,
  Pause,
  Trash2,
  RotateCcw,
  ChevronDown,
  ChevronUp,
  BookOpen,
  Lightbulb,
  Trophy,
  BarChart3,
  Brain,
  TrendingUp,
  TrendingDown,
  Minus,
  MessageSquare,
  Activity,
  Zap,
  AlertTriangle,
  Share2,
} from "lucide-react";
import Sidebar from "@/components/Sidebar";
import { VoiceTextArea } from "@/components/VoiceInput";
import { API, authFetch } from "@/App";
import { toast } from "sonner";

const DIFFICULTY_LABELS = ["", "Fondamental", "Débutant", "Intermédiaire", "Avancé", "Expert"];
const DIFFICULTY_COLORS = ["", "text-emerald-500", "text-blue-500", "text-amber-500", "text-orange-500", "text-rose-500"];

// ─── CurriculumStep (unchanged) ───

function CurriculumStep({ step, index, isNext, onStart }) {
  const [expanded, setExpanded] = useState(isNext);
  const completed = step.completed;

  return (
    <div
      className={`border rounded-xl transition-all ${
        isNext
          ? "border-primary/40 bg-primary/5 shadow-sm"
          : completed
          ? "border-border/30 bg-muted/20"
          : "border-border/50"
      }`}
    >
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3 px-4 py-3 text-left"
      >
        <div className="shrink-0">
          {completed ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-500" />
          ) : isNext ? (
            <div className="w-5 h-5 rounded-full bg-primary flex items-center justify-center">
              <Play className="w-2.5 h-2.5 text-primary-foreground ml-0.5" />
            </div>
          ) : (
            <Circle className="w-5 h-5 text-muted-foreground/40" />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-medium text-muted-foreground">JOUR {step.day}</span>
            {step.review && (
              <Badge variant="outline" className="text-[9px] bg-sky-500/10 text-sky-500 border-sky-500/20">
                Révision
              </Badge>
            )}
            {step.difficulty && (
              <span className={`text-[10px] ${DIFFICULTY_COLORS[step.difficulty] || ""}`}>
                {DIFFICULTY_LABELS[step.difficulty] || ""}
              </span>
            )}
          </div>
          <h4 className={`text-sm font-medium truncate ${completed ? "text-muted-foreground line-through" : ""}`}>
            {step.title}
          </h4>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-xs text-muted-foreground">
            {step.duration_min}-{step.duration_max}m
          </span>
          {expanded ? (
            <ChevronUp className="w-4 h-4 text-muted-foreground" />
          ) : (
            <ChevronDown className="w-4 h-4 text-muted-foreground" />
          )}
        </div>
      </button>

      {expanded && (
        <div className="px-4 pb-4 pt-0 space-y-3 border-t border-border/30 mt-0">
          <p className="text-sm text-muted-foreground leading-relaxed pt-3">{step.description}</p>
          {step.focus && (
            <div className="flex items-center gap-1.5 text-xs">
              <BookOpen className="w-3 h-3 text-primary" />
              <span className="text-muted-foreground">Focus :</span>
              <span className="font-medium">{step.focus}</span>
            </div>
          )}
          {step.instructions && step.instructions.length > 0 && (
            <div className="space-y-1.5">
              {step.instructions.map((inst, i) => (
                <div key={i} className="flex items-start gap-2 text-sm">
                  <span className="text-primary font-medium shrink-0">{i + 1}.</span>
                  <span className="text-muted-foreground">{inst}</span>
                </div>
              ))}
            </div>
          )}
          {step.tip && (
            <div className="flex items-start gap-2 bg-amber-500/5 rounded-lg px-3 py-2 border border-amber-500/10">
              <Lightbulb className="w-3.5 h-3.5 text-amber-500 shrink-0 mt-0.5" />
              <span className="text-xs text-amber-600">{step.tip}</span>
            </div>
          )}
          {completed && step.actual_duration && (
            <div className="flex items-center gap-3 text-xs text-muted-foreground">
              <span>Durée : {step.actual_duration} min</span>
              {step.notes && <span className="truncate">Note : {step.notes}</span>}
            </div>
          )}
          {isNext && !completed && (
            <Button onClick={() => onStart(step, index)} className="w-full gap-2 mt-2">
              <Play className="w-4 h-4" />
              Commencer cette session
            </Button>
          )}
        </div>
      )}
    </div>
  );
}

// ─── SkillsTab (C.3 — Skill Graph Visualization) ───

const MASTERY_COLORS = {
  "Non démarré": { bar: "bg-muted", text: "text-muted-foreground", bg: "bg-muted/20" },
  "Débutant": { bar: "bg-blue-500", text: "text-blue-500", bg: "bg-blue-500/10" },
  "En progression": { bar: "bg-emerald-500", text: "text-emerald-500", bg: "bg-emerald-500/10" },
  "Intermédiaire": { bar: "bg-amber-500", text: "text-amber-500", bg: "bg-amber-500/10" },
  "Avancé": { bar: "bg-orange-500", text: "text-orange-500", bg: "bg-orange-500/10" },
  "Maîtrisé": { bar: "bg-primary", text: "text-primary", bg: "bg-primary/10" },
};

function SkillsTab({ objectiveId }) {
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const res = await authFetch(`${API}/objectives/${objectiveId}/skills`);
        if (res.ok) setData(await res.json());
      } catch {
        // silent
      } finally {
        setIsLoading(false);
      }
    })();
  }, [objectiveId]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="w-6 h-6 animate-spin text-primary" />
      </div>
    );
  }

  if (!data || !data.skills?.length) {
    return (
      <Card className="p-8 text-center">
        <Brain className="w-10 h-10 text-muted-foreground/30 mx-auto mb-2" />
        <h3 className="font-heading font-semibold mb-1">Pas encore de compétences</h3>
        <p className="text-sm text-muted-foreground">
          Complète quelques sessions pour voir ta carte de compétences.
        </p>
      </Card>
    );
  }

  const { skills, overall_mastery, level, review_needed } = data;
  const overallColor = MASTERY_COLORS[level] || MASTERY_COLORS["Non démarré"];

  return (
    <div className="space-y-4">
      {/* Overall mastery card */}
      <Card className="p-4">
        <div className="flex items-center justify-between mb-3">
          <div>
            <p className="text-xs text-muted-foreground uppercase tracking-wider font-medium">Maîtrise globale</p>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-2xl font-bold tabular-nums">{overall_mastery}%</span>
              <Badge variant="outline" className={`text-[10px] ${overallColor.text} ${overallColor.bg} border-current/20`}>
                {level}
              </Badge>
            </div>
          </div>
          {review_needed > 0 && (
            <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/20">
              <RotateCcw className="w-3.5 h-3.5 text-amber-500" />
              <span className="text-xs font-medium text-amber-600">{review_needed} à réviser</span>
            </div>
          )}
        </div>
        <Progress value={overall_mastery} className="h-2.5" />
      </Card>

      {/* Skills grid */}
      <div className="space-y-2">
        {skills.map((skill) => {
          const mc = MASTERY_COLORS[skill.level] || MASTERY_COLORS["Non démarré"];
          return (
            <Card key={skill.name} className={`p-4 transition-all ${skill.needs_review ? "border-amber-500/30 bg-amber-500/3" : ""}`}>
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="font-medium text-sm truncate">{skill.name}</h3>
                    {skill.needs_review && (
                      <Badge variant="outline" className="text-[9px] bg-amber-500/10 text-amber-600 border-amber-500/20 shrink-0">
                        <RotateCcw className="w-2.5 h-2.5 mr-0.5" />
                        Révision
                      </Badge>
                    )}
                  </div>
                  <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                    <span>{skill.sessions_done}/{skill.sessions_total} sessions</span>
                    <span>{skill.total_minutes} min</span>
                    <Badge variant="outline" className={`text-[9px] ${mc.text} ${mc.bg} border-current/20`}>
                      {skill.level}
                    </Badge>
                  </div>
                </div>
                <span className={`text-lg font-bold tabular-nums ${mc.text}`}>{skill.mastery}%</span>
              </div>
              <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${mc.bar}`}
                  style={{ width: `${skill.mastery}%` }}
                />
              </div>
            </Card>
          );
        })}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-2 pt-2">
        {["Débutant", "En progression", "Intermédiaire", "Avancé", "Maîtrisé"].map((lvl) => {
          const mc = MASTERY_COLORS[lvl];
          return (
            <div key={lvl} className="flex items-center gap-1.5 text-[10px] text-muted-foreground">
              <div className={`w-2 h-2 rounded-full ${mc.bar}`} />
              {lvl}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── InsightsTab ───

const MOMENTUM_CONFIG = {
  rising: { icon: TrendingUp, color: "text-emerald-500", bg: "bg-emerald-500/10", border: "border-emerald-500/20" },
  stable: { icon: Minus, color: "text-blue-500", bg: "bg-blue-500/10", border: "border-blue-500/20" },
  declining: { icon: TrendingDown, color: "text-amber-500", bg: "bg-amber-500/10", border: "border-amber-500/20" },
};

const DIFFICULTY_BAR_COLORS = [
  "",
  "bg-emerald-500",   // 1 — Fondamental
  "bg-blue-500",      // 2 — Débutant
  "bg-amber-500",     // 3 — Intermédiaire
  "bg-orange-500",    // 4 — Avancé
  "bg-rose-500",      // 5 — Expert
];

const INSIGHT_TABS = [
  { key: "analyse", label: "Analyse", icon: Brain },
  { key: "activite", label: "Activité", icon: BarChart3 },
  { key: "journal", label: "Journal", icon: MessageSquare },
];

function InsightsTab({ objectiveId }) {
  const [insights, setInsights] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [subTab, setSubTab] = useState("analyse");

  useEffect(() => {
    (async () => {
      try {
        const res = await authFetch(`${API}/objectives/${objectiveId}/insights`);
        if (res.ok) setInsights(await res.json());
      } catch {
        // silent
      } finally {
        setIsLoading(false);
      }
    })();
  }, [objectiveId]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="w-6 h-6 animate-spin text-primary" />
      </div>
    );
  }

  if (!insights || (!insights.timeline?.length && !insights.ai_analysis)) {
    return (
      <Card className="p-8 text-center">
        <BarChart3 className="w-10 h-10 text-muted-foreground/30 mx-auto mb-3" />
        <h4 className="font-heading font-semibold text-sm mb-1">Pas encore d'insights</h4>
        <p className="text-xs text-muted-foreground">
          Complète quelques sessions pour débloquer l'analyse de ta progression.
        </p>
      </Card>
    );
  }

  const { stats, ai_analysis, notes, difficulty_curve, weekly_activity } = insights;

  return (
    <div className="space-y-4">

      {/* ── Sub-tab navigation ── */}
      <div className="flex border-b border-border/50">
        {INSIGHT_TABS.map((tab) => {
          const Icon = tab.icon;
          const isActive = subTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setSubTab(tab.key)}
              className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 transition-all -mb-px ${
                isActive
                  ? "border-primary text-foreground"
                  : "border-transparent text-muted-foreground hover:text-foreground hover:border-border"
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              {tab.label}
              {tab.key === "journal" && notes?.length > 0 && (
                <span className="text-[9px] bg-muted rounded-full px-1.5 py-0.5">{notes.length}</span>
              )}
            </button>
          );
        })}
      </div>

      {/* ══════════ ANALYSE TAB ══════════ */}
      {subTab === "analyse" && (
        <div className="space-y-4">
          {/* Stats Grid — always visible */}
          {stats && (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              <Card className="p-3 text-center">
                <Activity className="w-4 h-4 text-blue-500 mx-auto mb-1" />
                <div className="text-lg font-bold">{stats.completion_rate}%</div>
                <div className="text-[10px] text-muted-foreground">Complétion</div>
              </Card>
              <Card className="p-3 text-center">
                <Clock className="w-4 h-4 text-purple-500 mx-auto mb-1" />
                <div className="text-lg font-bold">{stats.avg_duration}<span className="text-xs font-normal">m</span></div>
                <div className="text-[10px] text-muted-foreground">Moy. / session</div>
              </Card>
              <Card className="p-3 text-center">
                <Calendar className="w-4 h-4 text-emerald-500 mx-auto mb-1" />
                <div className="text-lg font-bold">{stats.active_days}</div>
                <div className="text-[10px] text-muted-foreground">Jours actifs</div>
              </Card>
            </div>
          )}

          {/* AI Analysis Card */}
          {ai_analysis ? (
            <Card className="p-4 border-primary/15 bg-gradient-to-br from-primary/5 to-transparent">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-7 h-7 rounded-lg bg-primary/15 flex items-center justify-center">
                  <Brain className="w-4 h-4 text-primary" />
                </div>
                <h3 className="font-heading font-semibold text-sm">Analyse IA</h3>
                {ai_analysis.momentum && (() => {
                  const mc = MOMENTUM_CONFIG[ai_analysis.momentum] || MOMENTUM_CONFIG.stable;
                  const Icon = mc.icon;
                  return (
                    <Badge variant="outline" className={`ml-auto text-[10px] ${mc.color} ${mc.bg} ${mc.border}`}>
                      <Icon className="w-3 h-3 mr-1" />
                      {ai_analysis.momentum_label || ai_analysis.momentum}
                    </Badge>
                  );
                })()}
              </div>

              <p className="text-sm text-foreground/80 leading-relaxed mb-3">
                {ai_analysis.summary}
              </p>

              <div className="grid grid-cols-2 gap-3 mb-3">
                {ai_analysis.strengths?.length > 0 && (
                  <div className="bg-emerald-500/5 rounded-xl p-3 border border-emerald-500/10">
                    <div className="flex items-center gap-1.5 mb-2">
                      <Zap className="w-3.5 h-3.5 text-emerald-500" />
                      <span className="text-xs font-semibold text-emerald-500">Points forts</span>
                    </div>
                    <div className="space-y-1.5">
                      {ai_analysis.strengths.map((s, i) => (
                        <p key={i} className="text-[11px] text-foreground/70 leading-relaxed flex items-start gap-1.5">
                          <span className="text-emerald-500 mt-0.5 shrink-0">•</span>
                          {s}
                        </p>
                      ))}
                    </div>
                  </div>
                )}

                {ai_analysis.improvements?.length > 0 && (
                  <div className="bg-amber-500/5 rounded-xl p-3 border border-amber-500/10">
                    <div className="flex items-center gap-1.5 mb-2">
                      <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
                      <span className="text-xs font-semibold text-amber-500">À améliorer</span>
                    </div>
                    <div className="space-y-1.5">
                      {ai_analysis.improvements.map((s, i) => (
                        <p key={i} className="text-[11px] text-foreground/70 leading-relaxed flex items-start gap-1.5">
                          <span className="text-amber-500 mt-0.5 shrink-0">•</span>
                          {s}
                        </p>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {ai_analysis.next_advice && (
                <div className="bg-primary/5 rounded-xl px-3.5 py-2.5 border border-primary/10">
                  <div className="flex items-start gap-2">
                    <Lightbulb className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                    <div>
                      <span className="text-[10px] font-semibold text-primary uppercase tracking-wide">Conseil</span>
                      <p className="text-xs text-foreground/70 leading-relaxed mt-0.5">{ai_analysis.next_advice}</p>
                    </div>
                  </div>
                </div>
              )}
            </Card>
          ) : (
            <Card className="p-6 text-center border-dashed">
              <Brain className="w-8 h-8 text-muted-foreground/20 mx-auto mb-2" />
              <p className="text-xs text-muted-foreground">
                L'analyse IA se débloque après 3 sessions complétées.
              </p>
            </Card>
          )}
        </div>
      )}

      {/* ══════════ ACTIVITÉ TAB ══════════ */}
      {subTab === "activite" && (
        <div className="space-y-4">
          {/* Weekly Activity */}
          {weekly_activity?.length > 0 && (
            <Card className="p-4">
              <h4 className="font-heading font-semibold text-sm mb-3 flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-primary" />
                Activité hebdomadaire
              </h4>
              <div className="space-y-2.5">
                {weekly_activity.slice(-8).map((week, i) => {
                  const maxMinutes = Math.max(...weekly_activity.map((w) => w.minutes), 1);
                  const barWidth = Math.max(8, (week.minutes / maxMinutes) * 100);
                  return (
                    <div key={i} className="flex items-center gap-3">
                      <span className="text-[10px] text-muted-foreground w-16 shrink-0 font-mono">
                        {week.week}
                      </span>
                      <div className="flex-1 h-6 bg-muted/30 rounded-lg overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-primary/60 to-primary rounded-lg flex items-center justify-end pr-2 transition-all duration-500"
                          style={{ width: `${barWidth}%` }}
                        >
                          {week.minutes >= 5 && (
                            <span className="text-[9px] text-primary-foreground font-medium">{week.minutes}m</span>
                          )}
                        </div>
                      </div>
                      <span className="text-[10px] text-muted-foreground w-12 text-right">{week.sessions} sess.</span>
                    </div>
                  );
                })}
              </div>
            </Card>
          )}

          {/* Difficulty Progression */}
          {difficulty_curve?.length > 1 && (
            <Card className="p-4">
              <h4 className="font-heading font-semibold text-sm mb-3 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-primary" />
                Progression de difficulté
              </h4>
              <div className="flex items-end gap-1.5 h-28 px-1">
                {difficulty_curve.map((point, i) => {
                  const heightPct = Math.max(15, (point.difficulty / 5) * 100);
                  const barColor = DIFFICULTY_BAR_COLORS[point.difficulty] || "bg-primary";
                  return (
                    <div key={i} className="flex-1 flex flex-col items-center justify-end gap-1.5 group" title={`${point.title} — ${DIFFICULTY_LABELS[point.difficulty]}`}>
                      <div className="opacity-0 group-hover:opacity-100 transition-opacity text-[8px] text-center text-muted-foreground leading-tight max-w-[60px] truncate">
                        {point.title}
                      </div>
                      <div
                        className={`w-full rounded-t-md ${barColor} transition-all duration-300 min-h-[8px]`}
                        style={{ height: `${heightPct}%` }}
                      />
                      <span className="text-[9px] text-muted-foreground font-medium">J{point.day}</span>
                    </div>
                  );
                })}
              </div>
              <div className="flex items-center justify-between mt-3 px-1">
                {DIFFICULTY_LABELS.slice(1).map((label, i) => (
                  <div key={i} className="flex items-center gap-1">
                    <div className={`w-2 h-2 rounded-sm ${DIFFICULTY_BAR_COLORS[i + 1]}`} />
                    <span className="text-[8px] text-muted-foreground">{label}</span>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Full Timeline */}
          {insights.timeline?.length > 0 && (
            <Card className="p-4">
              <h4 className="font-heading font-semibold text-sm mb-3 flex items-center gap-2">
                <Clock className="w-4 h-4 text-primary" />
                Historique des sessions
                <span className="text-[10px] text-muted-foreground font-normal ml-auto">{insights.timeline.length} sessions</span>
              </h4>
              <div className="space-y-1.5 max-h-[350px] overflow-y-auto pr-1">
                {insights.timeline.slice().reverse().map((entry, i) => (
                  <div key={i} className={`flex items-center gap-3 px-3 py-2 rounded-lg text-xs ${
                    entry.completed ? "bg-muted/20" : "bg-red-500/5"
                  }`}>
                    {entry.completed ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                    ) : (
                      <AlertTriangle className="w-3.5 h-3.5 text-red-400 shrink-0" />
                    )}
                    <span className="font-semibold text-muted-foreground w-8 shrink-0">J{entry.day}</span>
                    <span className="flex-1 truncate">{entry.step_title}</span>
                    <span className="text-muted-foreground/50 shrink-0">{entry.duration}m</span>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>
      )}

      {/* ══════════ JOURNAL TAB ══════════ */}
      {subTab === "journal" && (
        <div className="space-y-4">
          {notes?.length > 0 ? (
            <div className="space-y-3">
              {notes.slice().reverse().map((entry, i) => (
                <Card key={i} className="p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Badge variant="outline" className="text-[10px] bg-primary/5 border-primary/15 text-primary">
                      Jour {entry.day}
                    </Badge>
                    <span className="text-xs text-muted-foreground flex-1 truncate">{entry.step_title}</span>
                    <div className="flex items-center gap-1.5 shrink-0">
                      {entry.duration > 0 && (
                        <span className="text-[10px] text-muted-foreground flex items-center gap-0.5">
                          <Clock className="w-2.5 h-2.5" />
                          {entry.duration}m
                        </span>
                      )}
                      {entry.date && (
                        <span className="text-[10px] text-muted-foreground/50">
                          {new Date(entry.date).toLocaleDateString("fr-FR", { day: "numeric", month: "short" })}
                        </span>
                      )}
                    </div>
                  </div>
                  <p className="text-sm text-foreground/80 leading-relaxed">{entry.notes}</p>
                </Card>
              ))}
            </div>
          ) : (
            <Card className="p-8 text-center border-dashed">
              <MessageSquare className="w-8 h-8 text-muted-foreground/20 mx-auto mb-2" />
              <h4 className="font-heading font-semibold text-sm mb-1">Aucune note pour l'instant</h4>
              <p className="text-xs text-muted-foreground">
                Ajoute des notes lors de tes sessions pour les retrouver ici.
              </p>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Main Page ───

export default function ObjectiveDetailPage() {
  const { objectiveId } = useParams();
  const navigate = useNavigate();
  const [objective, setObjective] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("parcours");
  const [showSession, setShowSession] = useState(false);
  const [activeStep, setActiveStep] = useState(null);
  const [activeStepIndex, setActiveStepIndex] = useState(null);
  const [sessionTimer, setSessionTimer] = useState(0);
  const [sessionRunning, setSessionRunning] = useState(false);
  const [sessionNotes, setSessionNotes] = useState("");
  const [isCompleting, setIsCompleting] = useState(false);
  const [showConfirmDelete, setShowConfirmDelete] = useState(false);

  const loadObjective = useCallback(async () => {
    try {
      const res = await authFetch(`${API}/objectives/${objectiveId}`);
      if (res.ok) {
        setObjective(await res.json());
      } else {
        toast.error("Objectif non trouvé");
        navigate("/objectives");
      }
    } catch {
      toast.error("Erreur de chargement");
    } finally {
      setIsLoading(false);
    }
  }, [objectiveId, navigate]);

  useEffect(() => {
    loadObjective();
  }, [loadObjective]);

  // Timer
  useEffect(() => {
    let interval;
    if (sessionRunning) {
      interval = setInterval(() => setSessionTimer((t) => t + 1), 1000);
    }
    return () => clearInterval(interval);
  }, [sessionRunning]);

  const startSession = (step, index) => {
    setActiveStep(step);
    setActiveStepIndex(index);
    setSessionTimer(0);
    setSessionNotes("");
    setSessionRunning(true);
    setShowSession(true);
  };

  const completeStep = async (completed) => {
    if (isCompleting) return;
    setIsCompleting(true);
    setSessionRunning(false);
    const actualDuration = Math.max(1, Math.round(sessionTimer / 60));

    try {
      const res = await authFetch(`${API}/objectives/${objectiveId}/complete-step`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          step_index: activeStep.step_index,
          actual_duration: actualDuration,
          notes: sessionNotes,
          completed,
        }),
      });
      if (!res.ok) throw new Error("Erreur");
      const result = await res.json();

      if (completed) {
        toast.success(
          result.is_finished
            ? "Parcours terminé ! Bravo !"
            : `Session terminée ! ${result.progress_percent}% du parcours`
        );
      }

      setShowSession(false);
      loadObjective();
    } catch {
      toast.error("Erreur lors de la sauvegarde");
    } finally {
      setIsCompleting(false);
    }
  };

  const updateStatus = async (status) => {
    try {
      const res = await authFetch(`${API}/objectives/${objectiveId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
      });
      if (res.ok) {
        toast.success(status === "paused" ? "Objectif mis en pause" : "Objectif repris !");
        loadObjective();
      }
    } catch {
      toast.error("Erreur");
    }
  };

  const deleteObjective = async () => {
    try {
      const res = await authFetch(`${API}/objectives/${objectiveId}`, { method: "DELETE" });
      if (res.ok) {
        toast.success("Objectif supprimé");
        navigate("/objectives");
      }
    } catch {
      toast.error("Erreur");
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!objective) return null;

  const curriculum = objective.curriculum || [];
  const completedSteps = curriculum.filter((s) => s.completed).length;
  const totalSteps = curriculum.length;
  const percent = totalSteps > 0 ? Math.round((completedSteps / totalSteps) * 100) : 0;
  const nextStepIndex = curriculum.findIndex((s) => !s.completed);
  const isGenerating = totalSteps === 0;

  const formatTime = (s) => `${Math.floor(s / 60).toString().padStart(2, "0")}:${(s % 60).toString().padStart(2, "0")}`;

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <main className="lg:ml-16 pb-20">
        <div className="max-w-2xl mx-auto px-4 py-6">
          {/* Back */}
          <button
            onClick={() => navigate("/objectives")}
            className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground mb-4 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Mes Objectifs
          </button>

          {/* Header card */}
          <Card className="p-5 mb-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h1 className="font-heading text-xl font-bold">{objective.title}</h1>
                {objective.description && (
                  <p className="text-sm text-muted-foreground mt-1">{objective.description}</p>
                )}
              </div>
              <div className="flex items-center gap-1.5">
                {objective.status === "active" ? (
                  <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => updateStatus("paused")}>
                    <Pause className="w-4 h-4" />
                  </Button>
                ) : objective.status === "paused" ? (
                  <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => updateStatus("active")}>
                    <RotateCcw className="w-4 h-4" />
                  </Button>
                ) : null}
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={async () => {
                    const text = [
                      `Jour ${objective.current_day || 0} sur « ${objective.title} »`,
                      `${percent}% complété · ${objective.streak_days || 0}j de streak · ${objective.total_minutes || 0} min investies`,
                      ``,
                      `Mon parcours sur InFinea !`,
                    ].join("\n");
                    if (navigator.share) {
                      try { await navigator.share({ title: objective.title, text }); } catch {}
                    } else {
                      await navigator.clipboard.writeText(text);
                      toast.success("Copié !");
                    }
                  }}
                  title="Partager"
                >
                  <Share2 className="w-4 h-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 text-muted-foreground hover:text-destructive"
                  onClick={() => setShowConfirmDelete(true)}
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            </div>

            {/* Progress */}
            <div className="mb-4">
              <div className="flex items-center justify-between text-sm mb-2">
                <span className="text-muted-foreground">Progression</span>
                <span className="font-semibold">{percent}%</span>
              </div>
              <Progress value={percent} className="h-3" />
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="text-center p-2 rounded-lg bg-muted/30">
                <Flame className="w-4 h-4 text-orange-500 mx-auto mb-1" />
                <div className="text-lg font-bold">{objective.streak_days || 0}</div>
                <div className="text-[10px] text-muted-foreground">Streak</div>
              </div>
              <div className="text-center p-2 rounded-lg bg-muted/30">
                <Clock className="w-4 h-4 text-blue-500 mx-auto mb-1" />
                <div className="text-lg font-bold">{objective.total_minutes || 0}</div>
                <div className="text-[10px] text-muted-foreground">Minutes</div>
              </div>
              <div className="text-center p-2 rounded-lg bg-muted/30">
                <CheckCircle2 className="w-4 h-4 text-emerald-500 mx-auto mb-1" />
                <div className="text-lg font-bold">{completedSteps}</div>
                <div className="text-[10px] text-muted-foreground">Sessions</div>
              </div>
              <div className="text-center p-2 rounded-lg bg-muted/30">
                <Calendar className="w-4 h-4 text-purple-500 mx-auto mb-1" />
                <div className="text-lg font-bold">J{objective.current_day || 0}</div>
                <div className="text-[10px] text-muted-foreground">/{objective.target_duration_days}j</div>
              </div>
            </div>
          </Card>

          {/* ── Tab Switcher ── */}
          <div className="flex gap-1 p-1 mb-4 bg-muted/30 rounded-xl">
            <button
              onClick={() => setActiveTab("parcours")}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === "parcours"
                  ? "bg-background shadow-sm text-foreground"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <BookOpen className="w-4 h-4" />
              Parcours
            </button>
            <button
              onClick={() => setActiveTab("skills")}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === "skills"
                  ? "bg-background shadow-sm text-foreground"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Brain className="w-4 h-4" />
              Skills
            </button>
            <button
              onClick={() => setActiveTab("insights")}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === "insights"
                  ? "bg-background shadow-sm text-foreground"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <BarChart3 className="w-4 h-4" />
              Insights
              {completedSteps >= 3 && (
                <span className="w-1.5 h-1.5 rounded-full bg-primary" />
              )}
            </button>
          </div>

          {/* ── Tab Content ── */}
          {activeTab === "skills" ? (
            <SkillsTab objectiveId={objectiveId} />
          ) : activeTab === "parcours" ? (
            <>
              {/* Curriculum header */}
              <div className="mb-4 flex items-center justify-between">
                <h2 className="font-heading font-semibold text-base">
                  {isGenerating ? "Génération en cours..." : "Mon parcours"}
                </h2>
                {!isGenerating && (
                  <span className="text-xs text-muted-foreground">
                    {completedSteps}/{totalSteps} sessions
                  </span>
                )}
              </div>

              {isGenerating ? (
                <Card className="p-8 text-center">
                  <Loader2 className="w-8 h-8 animate-spin text-primary mx-auto mb-3" />
                  <p className="text-sm text-muted-foreground">
                    L'IA génère ton parcours personnalisé...
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Reviens dans quelques secondes !
                  </p>
                  <Button variant="outline" size="sm" className="mt-4" onClick={loadObjective}>
                    Rafraîchir
                  </Button>
                </Card>
              ) : (
                <div className="space-y-2">
                  {curriculum.map((step, i) => (
                    <CurriculumStep
                      key={step.step_index ?? i}
                      step={step}
                      index={i}
                      isNext={i === nextStepIndex && objective.status === "active"}
                      onStart={startSession}
                    />
                  ))}
                </div>
              )}

              {/* Completed celebration */}
              {percent >= 100 && (
                <Card className="p-6 mt-6 text-center border-amber-500/20 bg-gradient-to-br from-amber-500/10 to-amber-500/5">
                  <Trophy className="w-12 h-12 text-amber-500 mx-auto mb-3" />
                  <h3 className="font-heading font-bold text-lg">Parcours terminé !</h3>
                  <p className="text-sm text-muted-foreground mt-1">
                    Tu as complété {completedSteps} sessions et investi {objective.total_minutes || 0} minutes.
                  </p>
                  <Button className="mt-4" onClick={() => navigate("/objectives")}>
                    Voir mes objectifs
                  </Button>
                </Card>
              )}
            </>
          ) : (
            <InsightsTab objectiveId={objectiveId} />
          )}
        </div>
      </main>

      {/* Session Modal */}
      <Dialog open={showSession} onOpenChange={(open) => { if (!open) { setSessionRunning(false); setShowSession(false); } }}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-base">
              <Sparkles className="w-5 h-5 text-primary" />
              {activeStep?.title}
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4 py-2">
            {/* Memory: last session context */}
            {(() => {
              const log = objective?.progress_log || [];
              const last = log.length > 0 ? log[log.length - 1] : null;
              if (!last) return null;
              return (
                <div className="flex items-start gap-2 bg-blue-500/5 rounded-lg px-3 py-2 border border-blue-500/10">
                  <BookOpen className="w-3.5 h-3.5 text-blue-500 shrink-0 mt-0.5" />
                  <div className="text-xs text-blue-400">
                    <span className="font-medium">Dernière session :</span> {last.step_title}
                    {last.notes && <span className="block text-blue-400/70 mt-0.5">"{last.notes}"</span>}
                  </div>
                </div>
              );
            })()}

            {/* Timer */}
            <div className="text-center">
              <div className="text-4xl font-mono font-bold tabular-nums">{formatTime(sessionTimer)}</div>
              <p className="text-xs text-muted-foreground mt-1">
                Objectif : {activeStep?.duration_min}-{activeStep?.duration_max} min
              </p>
            </div>

            {/* Description */}
            <p className="text-sm text-muted-foreground leading-relaxed">{activeStep?.description}</p>

            {/* Instructions */}
            {activeStep?.instructions?.length > 0 && (
              <div className="space-y-2 bg-muted/30 rounded-lg p-3">
                {activeStep.instructions.map((inst, i) => (
                  <div key={i} className="flex items-start gap-2 text-sm">
                    <span className="text-primary font-semibold shrink-0">{i + 1}.</span>
                    <span>{inst}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Tip */}
            {activeStep?.tip && (
              <div className="flex items-start gap-2 bg-amber-500/5 rounded-lg px-3 py-2 border border-amber-500/10">
                <Lightbulb className="w-3.5 h-3.5 text-amber-500 shrink-0 mt-0.5" />
                <span className="text-xs text-amber-600">{activeStep.tip}</span>
              </div>
            )}

            {/* Notes with voice input */}
            <VoiceTextArea
              value={sessionNotes}
              onChange={setSessionNotes}
              placeholder="Notes sur cette session..."
              rows={2}
            />
          </div>

          <DialogFooter className="flex-col sm:flex-row gap-2">
            <Button
              variant="outline"
              onClick={() => completeStep(false)}
              disabled={isCompleting}
              className="text-muted-foreground"
            >
              Abandonner
            </Button>
            <Button
              onClick={() => completeStep(true)}
              disabled={isCompleting}
              className="gap-2"
            >
              {isCompleting ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <CheckCircle2 className="w-4 h-4" />
              )}
              Terminer la session
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete confirmation */}
      <Dialog open={showConfirmDelete} onOpenChange={setShowConfirmDelete}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Supprimer cet objectif ?</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground">
            Cette action est irréversible. Toute la progression sera perdue.
          </p>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowConfirmDelete(false)}>
              Annuler
            </Button>
            <Button variant="destructive" onClick={deleteObjective}>
              Supprimer
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
