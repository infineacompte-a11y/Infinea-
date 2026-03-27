/**
 * ActivityHeatmap — GitHub-style contribution calendar.
 *
 * Pattern: GitHub contributions + Strava activity chart + Duolingo streak.
 * Shows a 52-week × 7-day grid of session activity with color intensity.
 *
 * Props:
 *   userId: string — whose heatmap to fetch
 *   compact?: boolean — reduced size for inline display (default false)
 */

import { useState, useEffect, useMemo } from "react";
import { Loader2, Flame, Calendar, Clock, Zap } from "lucide-react";
import { API, authFetch } from "@/App";

// ── Color palette (InFinea teal gradient, 5 levels like GitHub) ──
const LEVELS = [
  "bg-muted/40",                    // 0 sessions
  "bg-[#459492]/20",                // 1 session
  "bg-[#459492]/40",                // 2 sessions
  "bg-[#459492]/60",                // 3-4 sessions
  "bg-[#459492]/90",                // 5+ sessions
];

function getLevel(count) {
  if (!count) return 0;
  if (count === 1) return 1;
  if (count === 2) return 2;
  if (count <= 4) return 3;
  return 4;
}

const DAYS_FR = ["Lun", "", "Mer", "", "Ven", "", ""];
const MONTHS_FR = [
  "Jan", "Fév", "Mar", "Avr", "Mai", "Juin",
  "Juil", "Août", "Sep", "Oct", "Nov", "Déc",
];

function buildCalendarGrid(dates) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  // Go back ~52 weeks (364 days) — start from the most recent Monday
  const endDate = new Date(today);
  const startDate = new Date(today);
  startDate.setDate(startDate.getDate() - 363);
  // Align to Monday (ISO week start)
  const startDay = startDate.getDay();
  const mondayOffset = startDay === 0 ? -6 : 1 - startDay;
  startDate.setDate(startDate.getDate() + mondayOffset);

  const weeks = [];
  let currentDate = new Date(startDate);
  let week = [];

  while (currentDate <= endDate) {
    const key = currentDate.toISOString().slice(0, 10);
    const entry = dates[key] || { count: 0, minutes: 0 };
    week.push({
      date: key,
      count: entry.count,
      minutes: entry.minutes,
      level: getLevel(entry.count),
      isFuture: currentDate > today,
    });

    if (week.length === 7) {
      weeks.push(week);
      week = [];
    }
    currentDate.setDate(currentDate.getDate() + 1);
  }
  if (week.length > 0) {
    weeks.push(week);
  }

  return { weeks, startDate: new Date(startDate) };
}

function getMonthLabels(weeks) {
  const labels = [];
  let lastMonth = -1;
  weeks.forEach((week, weekIdx) => {
    const firstDay = week[0];
    if (!firstDay) return;
    const month = new Date(firstDay.date).getMonth();
    if (month !== lastMonth) {
      labels.push({ month, weekIdx });
      lastMonth = month;
    }
  });
  return labels;
}

export default function ActivityHeatmap({ userId, compact = false }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tooltip, setTooltip] = useState(null);

  useEffect(() => {
    if (!userId) return;
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const res = await authFetch(`${API}/users/${userId}/activity-heatmap?days=365`);
        if (res.ok && !cancelled) {
          setData(await res.json());
        }
      } catch { /* silent */ }
      if (!cancelled) setLoading(false);
    })();
    return () => { cancelled = true; };
  }, [userId]);

  const { weeks, monthLabels, summary } = useMemo(() => {
    if (!data) return { weeks: [], monthLabels: [], summary: null };
    const { weeks } = buildCalendarGrid(data.dates || {});
    const monthLabels = getMonthLabels(weeks);
    return { weeks, monthLabels, summary: data.summary };
  }, [data]);

  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <Loader2 className="w-5 h-5 animate-spin text-primary" />
      </div>
    );
  }

  if (!data || !summary || summary.total_sessions === 0) {
    return null; // No data — hide the component entirely
  }

  const cellSize = compact ? 10 : 12;
  const gap = 2;

  return (
    <div className="space-y-3">
      {/* Summary stats row */}
      <div className="grid grid-cols-4 gap-2">
        <div className="flex items-center gap-1.5 p-2 rounded-lg bg-[#459492]/10 border border-[#459492]/20">
          <Zap className="w-3.5 h-3.5 text-[#459492]" />
          <div>
            <p className="text-xs font-semibold text-[#459492] tabular-nums">{summary.total_sessions}</p>
            <p className="text-[9px] text-muted-foreground">sessions</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5 p-2 rounded-lg bg-[#55B3AE]/10 border border-[#55B3AE]/20">
          <Clock className="w-3.5 h-3.5 text-[#55B3AE]" />
          <div>
            <p className="text-xs font-semibold text-[#55B3AE] tabular-nums">
              {summary.total_minutes >= 60
                ? `${Math.floor(summary.total_minutes / 60)}h${summary.total_minutes % 60 > 0 ? summary.total_minutes % 60 : ""}`
                : `${summary.total_minutes}m`}
            </p>
            <p className="text-[9px] text-muted-foreground">investies</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5 p-2 rounded-lg bg-[#5DB786]/10 border border-[#5DB786]/20">
          <Calendar className="w-3.5 h-3.5 text-[#5DB786]" />
          <div>
            <p className="text-xs font-semibold text-[#5DB786] tabular-nums">{summary.active_days}</p>
            <p className="text-[9px] text-muted-foreground">jours actifs</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5 p-2 rounded-lg bg-[#E48C75]/10 border border-[#E48C75]/20">
          <Flame className="w-3.5 h-3.5 text-[#E48C75]" />
          <div>
            <p className="text-xs font-semibold text-[#E48C75] tabular-nums">{summary.longest_streak}</p>
            <p className="text-[9px] text-muted-foreground">meilleur streak</p>
          </div>
        </div>
      </div>

      {/* Heatmap grid */}
      <div className="overflow-x-auto pb-1 scrollbar-hide">
        <div className="relative" style={{ minWidth: weeks.length * (cellSize + gap) + 30 }}>
          {/* Month labels */}
          <div className="flex ml-7 mb-1" style={{ gap: `${gap}px` }}>
            {weeks.map((_, weekIdx) => {
              const label = monthLabels.find((m) => m.weekIdx === weekIdx);
              return (
                <div
                  key={weekIdx}
                  className="text-[9px] text-muted-foreground/60"
                  style={{ width: cellSize, textAlign: "left" }}
                >
                  {label ? MONTHS_FR[label.month] : ""}
                </div>
              );
            })}
          </div>

          {/* Grid: 7 rows (Mon-Sun) × N weeks */}
          <div className="flex">
            {/* Day labels */}
            <div className="flex flex-col mr-1" style={{ gap: `${gap}px` }}>
              {DAYS_FR.map((label, i) => (
                <div
                  key={i}
                  className="text-[9px] text-muted-foreground/60 flex items-center justify-end pr-0.5"
                  style={{ height: cellSize, width: 24 }}
                >
                  {label}
                </div>
              ))}
            </div>

            {/* Cells */}
            <div className="flex" style={{ gap: `${gap}px` }}>
              {weeks.map((week, weekIdx) => (
                <div key={weekIdx} className="flex flex-col" style={{ gap: `${gap}px` }}>
                  {week.map((day, dayIdx) => (
                    <div
                      key={dayIdx}
                      className={`rounded-[3px] transition-all duration-150 ${
                        day.isFuture
                          ? "bg-transparent"
                          : LEVELS[day.level]
                      } ${!day.isFuture && day.count > 0 ? "hover:ring-1 hover:ring-[#459492]/50 cursor-default" : ""}`}
                      style={{ width: cellSize, height: cellSize }}
                      onMouseEnter={() => {
                        if (!day.isFuture && day.count > 0) {
                          setTooltip({ date: day.date, count: day.count, minutes: day.minutes });
                        }
                      }}
                      onMouseLeave={() => setTooltip(null)}
                    />
                  ))}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Tooltip (floating, attached to mouse area conceptually) */}
      {tooltip && (
        <div className="text-[10px] text-muted-foreground text-center -mt-1">
          {new Date(tooltip.date).toLocaleDateString("fr-FR", { day: "numeric", month: "long", year: "numeric" })}
          {" — "}
          <span className="font-semibold text-foreground">
            {tooltip.count} session{tooltip.count > 1 ? "s" : ""}
          </span>
          {tooltip.minutes > 0 && ` · ${tooltip.minutes} min`}
        </div>
      )}

      {/* Legend */}
      <div className="flex items-center justify-end gap-1.5 text-[9px] text-muted-foreground/60">
        <span>Moins</span>
        {LEVELS.map((cls, i) => (
          <div key={i} className={`rounded-[2px] ${cls}`} style={{ width: cellSize - 2, height: cellSize - 2 }} />
        ))}
        <span>Plus</span>
      </div>
    </div>
  );
}
