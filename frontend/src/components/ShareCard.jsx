import React, { forwardRef } from "react";
import { Flame, Clock, Target, TrendingUp, Award, Zap } from "lucide-react";
import { Progress } from "@/components/ui/progress";

/**
 * ShareCard — Visual share card for progression snapshots.
 * Design reference: Duolingo Share Cards + Strava Activity Cards + Spotify Wrapped.
 *
 * This component renders a self-contained, fixed-dimension card designed to be
 * captured as a PNG image (via html-to-image in D.2c). No scroll dependencies,
 * opaque background, integrated branding.
 *
 * Props:
 *   snapshot — the share snapshot data from the API (POST /share/create response body
 *              or GET /share/{id} response)
 *   shareType — "weekly_recap" | "milestone" | "badge" | "objective"
 *   compact — boolean, if true renders a smaller card (for inline preview)
 */

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

const DAY_LABELS = ["L", "M", "M", "J", "V", "S", "D"];

function formatMinutes(min) {
  if (min < 60) return `${min} min`;
  const h = Math.floor(min / 60);
  const m = min % 60;
  return m > 0 ? `${h}h${m.toString().padStart(2, "0")}` : `${h}h`;
}

const ShareCard = forwardRef(function ShareCard({ snapshot, shareType = "weekly_recap", compact = false }, ref) {
  if (!snapshot) return null;

  const { streak_days, total_time_invested, total_sessions, week, objectives, badges_count, recent_badges } = snapshot;
  const author = snapshot.author || snapshot._author || {};

  // Build week bars data
  const weekByDay = week?.by_day || {};
  const now = new Date();
  const monday = new Date(now);
  monday.setDate(now.getDate() - now.getDay() + (now.getDay() === 0 ? -6 : 1));
  const weekDays = [];
  for (let i = 0; i < 7; i++) {
    const d = new Date(monday);
    d.setDate(monday.getDate() + i);
    const key = d.toISOString().slice(0, 10);
    weekDays.push({ label: DAY_LABELS[i], minutes: weekByDay[key] || 0, isToday: key === now.toISOString().slice(0, 10) });
  }
  const maxMin = Math.max(...weekDays.map((d) => d.minutes), 1);

  // Featured objective (first one, or the one with highest progress)
  const featuredObj = objectives?.length > 0
    ? objectives.reduce((best, obj) => (obj.progress_percent > (best?.progress_percent || 0) ? obj : best), objectives[0])
    : null;

  const cardWidth = compact ? "w-[320px]" : "w-[400px]";
  const cardPadding = compact ? "p-5" : "p-7";

  return (
    <div
      ref={ref}
      className={`${cardWidth} rounded-2xl overflow-hidden select-none`}
      style={{
        background: "linear-gradient(145deg, #0a0a1a 0%, #111128 40%, #0f0f23 100%)",
        fontFamily: "'DM Sans', 'Outfit', system-ui, sans-serif",
      }}
    >
      <div className={cardPadding}>
        {/* ── Header: branding + author ── */}
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-[hsl(239,84%,67%)] flex items-center justify-center">
              <Zap className="w-4 h-4 text-white" />
            </div>
            <div>
              <div className="text-white/90 text-sm font-semibold tracking-tight">InFinea</div>
              <div className="text-white/40 text-[10px]">Micro-instants, macro-progrès</div>
            </div>
          </div>
          {streak_days > 0 && (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-orange-500/15">
              <Flame className="w-3.5 h-3.5 text-orange-400" />
              <span className="text-orange-300 text-xs font-bold tabular-nums">{streak_days}j</span>
            </div>
          )}
        </div>

        {/* ── Author name ── */}
        {author.name && (
          <div className="mb-5">
            <div className="text-white/50 text-[10px] uppercase tracking-widest mb-1">Progression de</div>
            <div className="text-white text-lg font-bold tracking-tight">{author.name}</div>
          </div>
        )}

        {/* ── Key stats row ── */}
        <div className="grid grid-cols-3 gap-3 mb-5">
          <div className="text-center p-3 rounded-xl bg-white/[0.04] border border-white/[0.06]">
            <Clock className="w-4 h-4 text-blue-400 mx-auto mb-1.5" />
            <div className="text-white text-xl font-bold tabular-nums leading-none">
              {formatMinutes(total_time_invested || 0)}
            </div>
            <div className="text-white/40 text-[10px] mt-1">investies</div>
          </div>
          <div className="text-center p-3 rounded-xl bg-white/[0.04] border border-white/[0.06]">
            <TrendingUp className="w-4 h-4 text-emerald-400 mx-auto mb-1.5" />
            <div className="text-white text-xl font-bold tabular-nums leading-none">
              {total_sessions || 0}
            </div>
            <div className="text-white/40 text-[10px] mt-1">sessions</div>
          </div>
          <div className="text-center p-3 rounded-xl bg-white/[0.04] border border-white/[0.06]">
            <Award className="w-4 h-4 text-amber-400 mx-auto mb-1.5" />
            <div className="text-white text-xl font-bold tabular-nums leading-none">
              {badges_count || 0}
            </div>
            <div className="text-white/40 text-[10px] mt-1">badges</div>
          </div>
        </div>

        {/* ── Week activity chart ── */}
        {week && (
          <div className="mb-5 p-3.5 rounded-xl bg-white/[0.03] border border-white/[0.05]">
            <div className="flex items-center justify-between mb-2.5">
              <span className="text-white/50 text-[10px] uppercase tracking-widest">Cette semaine</span>
              <span className="text-white/60 text-[11px] tabular-nums">
                {week.minutes || 0} min · {week.sessions || 0} sessions
              </span>
            </div>
            <div className="flex items-end gap-1.5 h-10">
              {weekDays.map((day, i) => (
                <div key={i} className="flex-1 flex flex-col items-center gap-0.5">
                  <div
                    className="w-full rounded-sm transition-all"
                    style={{
                      height: `${Math.max(day.minutes > 0 ? 4 : 2, (day.minutes / maxMin) * 32)}px`,
                      background: day.isToday
                        ? "hsl(239, 84%, 67%)"
                        : day.minutes > 0
                          ? "rgba(99, 102, 241, 0.4)"
                          : "rgba(255, 255, 255, 0.06)",
                    }}
                  />
                  <span
                    className="text-[8px] tabular-nums"
                    style={{ color: day.isToday ? "hsl(239, 84%, 67%)" : "rgba(255,255,255,0.3)" }}
                  >
                    {day.label}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Featured objective ── */}
        {featuredObj && (
          <div className="mb-5 p-3.5 rounded-xl bg-white/[0.03] border border-white/[0.05]">
            <div className="flex items-center gap-2 mb-2">
              <Target className="w-3.5 h-3.5 text-[hsl(239,84%,67%)]" />
              <span className="text-white/50 text-[10px] uppercase tracking-widest">Objectif en cours</span>
            </div>
            <div className="text-white text-sm font-semibold mb-2 truncate">{featuredObj.title}</div>
            <div className="flex items-center gap-3">
              <div className="flex-1">
                <div className="w-full h-1.5 rounded-full bg-white/10 overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: `${featuredObj.progress_percent}%`,
                      background: "linear-gradient(90deg, hsl(239, 84%, 67%), hsl(280, 80%, 60%))",
                    }}
                  />
                </div>
              </div>
              <span className="text-white/70 text-xs font-bold tabular-nums shrink-0">
                {featuredObj.progress_percent}%
              </span>
            </div>
            {featuredObj.category && (
              <div className="mt-2">
                <span className="text-[10px] text-white/30 px-2 py-0.5 rounded-full bg-white/[0.05]">
                  {categoryLabels[featuredObj.category] || featuredObj.category}
                </span>
              </div>
            )}
          </div>
        )}

        {/* ── Additional objectives (compact list) ── */}
        {objectives?.length > 1 && !compact && (
          <div className="mb-5 space-y-1.5">
            {objectives
              .filter((o) => o.objective_id !== featuredObj?.objective_id)
              .slice(0, 2)
              .map((obj) => (
                <div key={obj.objective_id} className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/[0.02]">
                  <Target className="w-3 h-3 text-white/30 shrink-0" />
                  <span className="text-white/60 text-xs truncate flex-1">{obj.title}</span>
                  <span className="text-white/40 text-[10px] tabular-nums shrink-0">{obj.progress_percent}%</span>
                </div>
              ))}
          </div>
        )}

        {/* ── Footer: CTA ── */}
        <div className="flex items-center justify-between pt-4 border-t border-white/[0.06]">
          <span className="text-white/25 text-[10px]">infinea.app</span>
          <span className="text-[10px] text-white/30">Investis tes instants perdus</span>
        </div>
      </div>
    </div>
  );
});

export default ShareCard;
