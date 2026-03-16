import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Flame,
  Clock,
  CheckCircle2,
  Target,
  CalendarClock,
  TrendingUp,
  Sparkles,
  ChevronRight,
  Loader2,
} from "lucide-react";
import { API, authFetch } from "@/App";

const HIGHLIGHT_ICONS = {
  streak: Flame,
  productive: CheckCircle2,
  milestone: TrendingUp,
  focus: Target,
};

const HIGHLIGHT_COLORS = {
  streak: "text-orange-500 bg-orange-500/10",
  productive: "text-emerald-500 bg-emerald-500/10",
  milestone: "text-blue-500 bg-blue-500/10",
  focus: "text-primary bg-primary/10",
};

export default function RecapCard() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [recap, setRecap] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const DAY_LABELS = [
    t("components.recapCard.days.mon"),
    t("components.recapCard.days.tue"),
    t("components.recapCard.days.wed"),
    t("components.recapCard.days.thu"),
    t("components.recapCard.days.fri"),
    t("components.recapCard.days.sat"),
    t("components.recapCard.days.sun"),
  ];

  useEffect(() => {
    (async () => {
      try {
        const res = await authFetch(`${API}/recap`);
        if (res.ok) setRecap(await res.json());
      } catch {
        // silent
      } finally {
        setIsLoading(false);
      }
    })();
  }, []);

  if (isLoading) {
    return (
      <Card className="p-6 mb-6">
        <div className="flex items-center justify-center py-4">
          <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
        </div>
      </Card>
    );
  }

  if (!recap) return null;

  const { today, week, streak, objectives, highlights } = recap;

  // Build week mini chart
  const now = new Date();
  const mondayDate = new Date(now);
  mondayDate.setDate(now.getDate() - now.getDay() + (now.getDay() === 0 ? -6 : 1));
  const weekDays = [];
  for (let i = 0; i < 7; i++) {
    const d = new Date(mondayDate);
    d.setDate(mondayDate.getDate() + i);
    const key = d.toISOString().slice(0, 10);
    weekDays.push({
      label: DAY_LABELS[i],
      minutes: (week.by_day || {})[key] || 0,
      isToday: key === now.toISOString().slice(0, 10),
    });
  }
  const maxMin = Math.max(...weekDays.map((d) => d.minutes), 1);

  return (
    <Card className="p-5 mb-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-heading font-semibold text-base flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-primary" />
          {t("components.recapCard.title")}
        </h2>
        <Badge variant="outline" className="text-[10px]">
          <Flame className="w-2.5 h-2.5 mr-0.5 text-orange-500" />
          {t("components.recapCard.streakDays", { count: streak })}
        </Badge>
      </div>

      {/* Today stats row */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-4">
        <div className="text-center p-2.5 rounded-lg bg-muted/30">
          <CheckCircle2 className="w-4 h-4 text-emerald-500 mx-auto mb-1" />
          <div className="text-lg font-bold tabular-nums">{today.sessions}</div>
          <div className="text-[10px] text-muted-foreground">{t("common.sessions")}</div>
        </div>
        <div className="text-center p-2.5 rounded-lg bg-muted/30">
          <Clock className="w-4 h-4 text-blue-500 mx-auto mb-1" />
          <div className="text-lg font-bold tabular-nums">{today.minutes}</div>
          <div className="text-[10px] text-muted-foreground">{t("common.minutes")}</div>
        </div>
        <div className="text-center p-2.5 rounded-lg bg-muted/30">
          <CalendarClock className="w-4 h-4 text-primary mx-auto mb-1" />
          <div className="text-lg font-bold tabular-nums">{today.routines_done}/{today.routines_total}</div>
          <div className="text-[10px] text-muted-foreground">{t("components.recapCard.routines")}</div>
        </div>
      </div>

      {/* Week mini bar chart */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-muted-foreground">{t("components.recapCard.thisWeek")}</span>
          <span className="text-xs text-muted-foreground">
            {t("components.recapCard.weekSummary", { minutes: week.minutes, sessions: week.sessions })}
          </span>
        </div>
        <div className="flex items-end gap-1 h-12">
          {weekDays.map((day, i) => (
            <div key={i} className="flex-1 flex flex-col items-center gap-0.5">
              <div
                className={`w-full rounded-t transition-all ${
                  day.isToday ? "bg-primary" : day.minutes > 0 ? "bg-primary/40" : "bg-muted/50"
                }`}
                style={{ height: `${Math.max(day.minutes > 0 ? 4 : 2, (day.minutes / maxMin) * 40)}px` }}
              />
              <span className={`text-[9px] ${day.isToday ? "text-primary font-bold" : "text-muted-foreground/60"}`}>
                {day.label}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Objectives progress */}
      {objectives.length > 0 && (
        <div className="mb-4 space-y-2">
          {objectives.slice(0, 3).map((obj) => (
            <div
              key={obj.objective_id}
              className="flex items-center gap-3 p-2 rounded-lg hover:bg-muted/30 cursor-pointer transition-colors"
              onClick={() => navigate(`/objectives/${obj.objective_id}`)}
            >
              <Target className="w-4 h-4 text-primary shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium truncate">{obj.title}</span>
                  <span className="text-[10px] text-muted-foreground ml-2 shrink-0">{obj.progress_percent}%</span>
                </div>
                <Progress value={obj.progress_percent} className="h-1 mt-1" />
              </div>
              <ChevronRight className="w-3 h-3 text-muted-foreground shrink-0" />
            </div>
          ))}
        </div>
      )}

      {/* Highlights */}
      {highlights.length > 0 && (
        <div className="space-y-1.5 pt-3 border-t border-border/50">
          {highlights.slice(0, 3).map((h, i) => {
            const Icon = HIGHLIGHT_ICONS[h.type] || Sparkles;
            const color = HIGHLIGHT_COLORS[h.type] || "text-primary bg-primary/10";
            return (
              <div key={i} className="flex items-center gap-2">
                <div className={`w-6 h-6 rounded-md flex items-center justify-center shrink-0 ${color}`}>
                  <Icon className="w-3 h-3" />
                </div>
                <span className="text-xs text-muted-foreground">{h.text}</span>
              </div>
            );
          })}
        </div>
      )}
    </Card>
  );
}
