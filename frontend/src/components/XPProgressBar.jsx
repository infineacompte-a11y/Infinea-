import React, { useState, useEffect } from "react";
import { Star } from "lucide-react";
import { API, authFetch } from "@/App";

/**
 * XP Progress Bar — Duolingo-inspired level progression display.
 *
 * Usage:
 *   <XPProgressBar />                           — fetches own XP
 *   <XPProgressBar xpData={profile.xp} />       — uses provided data
 *   <XPProgressBar variant="compact" />          — small inline badge
 *   <XPProgressBar variant="full" />             — full bar with details
 *   <XPProgressBar variant="profile" />          — profile header display
 */

const TITLE_COLORS = {
  "Curieux":      "#55B3AE",
  "Explorateur":  "#459492",
  "Apprenti":     "#5DB786",
  "Praticien":    "#3D8B37",
  "Expert":       "#E48C75",
  "Maître":       "#D4734E",
  "Virtuose":     "#9B59B6",
  "Légende":      "#F5A623",
};

export default function XPProgressBar({ xpData = null, variant = "full" }) {
  const [data, setData] = useState(xpData);
  const [loading, setLoading] = useState(!xpData);

  useEffect(() => {
    if (xpData) {
      setData(xpData);
      setLoading(false);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const res = await authFetch(`${API}/profile/xp`);
        if (res.ok && !cancelled) {
          setData(await res.json());
        }
      } catch {
        // Silent
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [xpData]);

  if (loading || !data) return null;

  const { level, total_xp, xp_in_level, xp_needed, progress, title } = data;
  const titleColor = TITLE_COLORS[title] || "#459492";

  // ── Compact: small level badge ──
  if (variant === "compact") {
    return (
      <span
        className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold text-white"
        style={{ backgroundColor: titleColor }}
        title={`Niveau ${level} — ${title} (${total_xp} XP)`}
      >
        <Star className="w-3 h-3" fill="currentColor" />
        {level}
      </span>
    );
  }

  // ── Profile: level badge + title + XP count ──
  if (variant === "profile") {
    return (
      <div className="flex items-center gap-3">
        {/* Level circle */}
        <div
          className="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold text-sm shadow-md"
          style={{ background: `linear-gradient(135deg, ${titleColor}, ${titleColor}dd)` }}
        >
          {level}
        </div>
        <div className="flex flex-col">
          <div className="flex items-center gap-1.5">
            <span className="text-sm font-semibold" style={{ color: titleColor }}>
              {title}
            </span>
            <span className="text-xs text-muted-foreground">
              Niv. {level}
            </span>
          </div>
          {/* Progress bar */}
          <div className="flex items-center gap-2 mt-1">
            <div className="w-24 h-1.5 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-700 ease-out"
                style={{
                  width: `${Math.max(2, progress * 100)}%`,
                  backgroundColor: titleColor,
                }}
              />
            </div>
            <span className="text-[10px] text-muted-foreground whitespace-nowrap">
              {xp_in_level}/{xp_needed}
            </span>
          </div>
        </div>
      </div>
    );
  }

  // ── Full: detailed progress card ──
  return (
    <div className="flex items-center gap-3 p-3 rounded-xl bg-card border border-border">
      {/* Level badge */}
      <div
        className="w-12 h-12 rounded-xl flex items-center justify-center text-white font-bold text-lg shadow-md flex-shrink-0"
        style={{ background: `linear-gradient(135deg, ${titleColor}, ${titleColor}cc)` }}
      >
        {level}
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center gap-1.5">
            <Star className="w-3.5 h-3.5" style={{ color: titleColor }} fill={titleColor} />
            <span className="text-sm font-semibold" style={{ color: titleColor }}>
              {title}
            </span>
          </div>
          <span className="text-xs text-muted-foreground">
            {total_xp.toLocaleString("fr-FR")} XP
          </span>
        </div>

        {/* Progress bar */}
        <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-700 ease-out"
            style={{
              width: `${Math.max(2, progress * 100)}%`,
              backgroundColor: titleColor,
            }}
          />
        </div>

        <div className="flex items-center justify-between mt-1">
          <span className="text-[11px] text-muted-foreground">
            Niveau {level}
          </span>
          <span className="text-[11px] text-muted-foreground">
            {xp_in_level} / {xp_needed} XP → Niv. {level + 1}
          </span>
        </div>
      </div>
    </div>
  );
}
