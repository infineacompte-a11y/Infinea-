import React, { useState, useEffect, useCallback } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import {
  Zap,
  Play,
  X,
  Clock,
  Calendar,
  Repeat,
  TrendingUp,
} from "lucide-react";
import { API, authFetch, useAuth } from "@/App";

// ─── Source config (compact) ─────────────────────────────────
const SOURCE_ICON = {
  calendar_gap: Calendar,
  routine_window: Repeat,
  behavioral_pattern: TrendingUp,
};

const SOURCE_COLOR = {
  calendar_gap: "text-[#459492]",
  routine_window: "text-[#5DB786]",
  behavioral_pattern: "text-brand-secondary",
};

// ─── Helpers ─────────────────────────────────────────────────
function minutesUntil(isoString) {
  return Math.round((new Date(isoString) - new Date()) / 60000);
}

function isWithinWindow(instant) {
  const now = new Date();
  return now >= new Date(instant.window_start) && now <= new Date(instant.window_end);
}

function isApproaching(instant, thresholdMin = 10) {
  const mins = minutesUntil(instant.window_start);
  return mins > 0 && mins <= thresholdMin;
}

// ═══════════════════════════════════════════════════════════════
// MicroInstantBanner — global contextual notification banner
// Shows when a micro-instant is imminent (≤10min) or active.
// Renders as a slim, animated bar at the top of the viewport.
// ═══════════════════════════════════════════════════════════════
export default function MicroInstantBanner() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [instant, setInstant] = useState(null);
  const [dismissed, setDismissed] = useState(new Set());
  const [visible, setVisible] = useState(false);

  // Don't show on the micro-instants page itself (avoid redundancy)
  const onMicroInstantsPage = location.pathname === "/micro-instants";

  const checkInstants = useCallback(async () => {
    if (!user) return;
    try {
      const res = await authFetch(`${API}/micro-instants/today`);
      if (!res.ok) return;
      const data = await res.json();
      const instants = data.instants || [];

      // Find the most relevant instant: active NOW > approaching soon
      const active = instants.find(
        (i) => isWithinWindow(i) && !dismissed.has(i.instant_id)
      );
      const approaching = instants.find(
        (i) => isApproaching(i) && !dismissed.has(i.instant_id)
      );

      const best = active || approaching || null;
      setInstant(best);
      setVisible(!!best);
    } catch {
      /* silent — banner is non-critical */
    }
  }, [user, dismissed]);

  // Poll every 5 minutes + check on mount
  useEffect(() => {
    if (!user) return;
    checkInstants();
    const id = setInterval(checkInstants, 5 * 60 * 1000);
    return () => clearInterval(id);
  }, [user, checkInstants]);

  // Re-evaluate visibility every 30s (for approaching → active transitions)
  useEffect(() => {
    if (!instant) return;
    const id = setInterval(() => {
      if (isWithinWindow(instant)) {
        setVisible(true);
      } else if (!isApproaching(instant)) {
        setVisible(false);
      }
    }, 30000);
    return () => clearInterval(id);
  }, [instant]);

  const handleDismiss = () => {
    if (instant) {
      setDismissed((prev) => new Set(prev).add(instant.instant_id));
    }
    setVisible(false);
  };

  const handleAction = () => {
    navigate("/micro-instants");
    // Don't dismiss — let the user interact on the full page
  };

  // ── Don't render ──
  if (!user || !visible || !instant || onMicroInstantsPage) return null;

  const isNow = isWithinWindow(instant);
  const minsLeft = isNow
    ? Math.max(0, minutesUntil(instant.window_end))
    : minutesUntil(instant.window_start);
  const action = instant.recommended_action || {};
  const SourceIcon = SOURCE_ICON[instant.source] || Zap;
  const sourceColor = SOURCE_COLOR[instant.source] || "text-primary";

  return (
    <div
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ease-out ${
        visible ? "translate-y-0 opacity-100 animate-slide-in-down" : "-translate-y-full opacity-0"
      }`}
    >
      <div
        className={`${
          isNow
            ? "bg-gradient-to-r from-[#459492] to-[#55B3AE]"
            : "bg-white shadow-md border-b border-[#E2E6EA]"
        } backdrop-blur-md shadow-lg`}
      >
        <div className="max-w-4xl mx-auto px-4 py-2.5 flex items-center gap-3">
          {/* Icon */}
          <div
            className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
              isNow ? "bg-white/20" : "bg-primary/10"
            }`}
          >
            {isNow ? (
              <Zap className="w-4 h-4 text-white" />
            ) : (
              <SourceIcon className={`w-4 h-4 ${sourceColor}`} />
            )}
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <p
              className={`text-sm font-medium leading-tight truncate ${
                isNow ? "text-white" : "text-[#141E24]"
              }`}
            >
              {isNow ? "Micro-instant disponible" : "Micro-instant dans"}
              {!isNow && (
                <span className="font-semibold"> {minsLeft} min</span>
              )}
            </p>
            {action.title && (
              <p
                className={`text-xs truncate mt-0.5 ${
                  isNow ? "text-white/70" : "text-[#667085]"
                }`}
              >
                {action.title}
                {instant.duration_minutes && (
                  <span> · {instant.duration_minutes} min</span>
                )}
              </p>
            )}
          </div>

          {/* Timer badge */}
          {isNow && minsLeft > 0 && (
            <div className="hidden sm:flex items-center gap-1 px-2 py-1 rounded-full bg-white/15 text-white text-xs shrink-0">
              <Clock className="w-3 h-3" />
              {minsLeft} min
            </div>
          )}

          {/* CTA */}
          <Button
            size="sm"
            variant={isNow ? "secondary" : "default"}
            className={`shrink-0 gap-1.5 text-xs h-8 rounded-xl hover:scale-105 active:translate-y-0.5 transition-all duration-200 ${
              isNow
                ? "bg-white/20 hover:bg-white/30 text-white border-white/20"
                : ""
            }`}
            onClick={handleAction}
          >
            <Play className="w-3 h-3" />
            {isNow ? "Commencer" : "Voir"}
          </Button>

          {/* Dismiss */}
          <button
            onClick={handleDismiss}
            className={`p-1 rounded-md transition-all duration-200 shrink-0 ${
              isNow
                ? "text-white/50 hover:text-white hover:bg-white/10"
                : "text-[#667085] hover:text-[#141E24] hover:bg-[#F8FAFB]"
            }`}
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
