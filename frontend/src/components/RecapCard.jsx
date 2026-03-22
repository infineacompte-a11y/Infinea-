import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
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
  streak: "text-[#E48C75] bg-[#E48C75]/40",
  productive: "text-[#5DB786] bg-[#5DB786]/40",
  milestone: "text-[#459492] bg-[#459492]/40",
  focus: "text-primary bg-primary/10",
};

const DAY_LABELS = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"];

export default function RecapCard() {
  const navigate = useNavigate();
  const [recap, setRecap] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

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
      <Card className="p-6 mb-6 shadow-sm shadow-[#459492]/5 border border-[#E2E6EA] rounded-2xl">
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
    <Card className="mb-6 shadow-sm shadow-[#459492]/5 border border-[#E2E6EA] rounded-2xl overflow-hidden">
      {/* Premium gradient header */}
      <div className="px-5 pt-5 pb-4 bg-gradient-to-r from-[#459492]/[0.04] via-[#55B3AE]/[0.02] to-transparent">
        <div className="flex items-center justify-between">
          <h2 className="font-sans font-semibold tracking-tight font-semibold text-base flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-[#459492]" />
            Mon récap
          </h2>
          <Badge variant="outline" className="text-[10px] border-[#E48C75]/30 bg-[#E48C75]/5">
            <Flame className="w-2.5 h-2.5 mr-0.5 text-[#E48C75]" />
            {streak}j streak
          </Badge>
        </div>
      </div>

      <div className="px-5 pb-5">

      {/* Today stats row */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-4">
        <div className="text-center p-2.5 rounded-xl bg-gradient-to-b from-[#5DB786]/[0.06] to-[#5DB786]/[0.02] border border-[#5DB786]/10">
          <CheckCircle2 className="w-4 h-4 text-[#5DB786] mx-auto mb-1" />
          <div className="text-lg font-bold tabular-nums">{today.sessions}</div>
          <div className="text-[10px] text-muted-foreground">Sessions</div>
        </div>
        <div className="text-center p-2.5 rounded-xl bg-gradient-to-b from-[#459492]/[0.06] to-[#459492]/[0.02] border border-[#459492]/10">
          <Clock className="w-4 h-4 text-[#459492] mx-auto mb-1" />
          <div className="text-lg font-bold tabular-nums">{today.minutes}</div>
          <div className="text-[10px] text-muted-foreground">Minutes</div>
        </div>
        <div className="text-center p-2.5 rounded-xl bg-gradient-to-b from-[#275255]/[0.04] to-transparent border border-[#275255]/[0.06]">
          <CalendarClock className="w-4 h-4 text-primary mx-auto mb-1" />
          <div className="text-lg font-bold tabular-nums">{today.routines_done}/{today.routines_total}</div>
          <div className="text-[10px] text-muted-foreground">Routines</div>
        </div>
      </div>

      {/* Week mini bar chart */}
      <div className="mb-4 p-3 rounded-xl bg-[#F8FAFB] border border-[#E2E6EA]/60" style={{ backgroundImage: 'radial-gradient(circle, #E2E6EA 0.5px, transparent 0.5px)', backgroundSize: '12px 12px' }}>
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-muted-foreground">Cette semaine</span>
          <span className="text-xs text-muted-foreground">{week.minutes} min · {week.sessions} sessions</span>
        </div>
        <div className="flex items-end gap-1.5 h-12">
          {weekDays.map((day, i) => (
            <div key={i} className="flex-1 flex flex-col items-center gap-0.5">
              <div
                className={`w-full rounded-md transition-all ${
                  day.isToday ? "bg-[#459492] shadow-sm shadow-[#459492]/30" : day.minutes > 0 ? "bg-[#459492]/35" : "bg-[#E2E6EA]/60"
                }`}
                style={{ height: `${Math.max(day.minutes > 0 ? 4 : 2, (day.minutes / maxMin) * 40)}px` }}
              />
              <span className={`text-[9px] ${day.isToday ? "text-[#459492] font-bold" : "text-muted-foreground/60"}`}>
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
              className="flex items-center gap-3 p-2 rounded-xl hover:bg-[#459492]/[0.04] cursor-pointer btn-press transition-all duration-200"
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
      </div>
    </Card>
  );
}
