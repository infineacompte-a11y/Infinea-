/**
 * WeeklyDigestCard — In-app weekly summary (Strava/Duolingo pattern).
 *
 * Shows a rich recap of the user's week: sessions, XP, streak, social,
 * badges, trends. Complements the weekly email digest.
 *
 * Data source: GET /notifications/weekly-summary/preview
 *
 * Props:
 *   stats: object — the stats from compute_user_weekly_stats()
 *   onDismiss?: () => void — callback when user closes the card
 */

import {
  Zap,
  Clock,
  Flame,
  TrendingUp,
  TrendingDown,
  Minus,
  Users,
  MessageCircle,
  Heart,
  Award,
  ChevronRight,
  X,
  Star,
  Sparkles,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

const CATEGORY_LABELS = {
  learning: "Apprentissage",
  productivity: "Productivité",
  well_being: "Bien-être",
  creativity: "Créativité",
  fitness: "Fitness",
  mixed: "Mixte",
};

const CATEGORY_COLORS = {
  learning: "#459492",
  productivity: "#55B3AE",
  well_being: "#5DB786",
  creativity: "#F5A623",
  fitness: "#E48C75",
  mixed: "#8B8B8B",
};

function TrendBadge({ trend }) {
  if (!trend || trend.direction === "flat") {
    return (
      <span className="inline-flex items-center gap-0.5 text-[10px] text-muted-foreground">
        <Minus className="w-3 h-3" /> Stable
      </span>
    );
  }
  if (trend.direction === "up") {
    return (
      <span className="inline-flex items-center gap-0.5 text-[10px] text-[#5DB786] font-medium">
        <TrendingUp className="w-3 h-3" /> {trend.label}
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-0.5 text-[10px] text-[#E48C75] font-medium">
      <TrendingDown className="w-3 h-3" /> {trend.label}
    </span>
  );
}

function MiniBarChart({ byDay }) {
  if (!byDay || Object.keys(byDay).length === 0) return null;

  // Get last 7 days
  const days = [];
  const now = new Date();
  for (let i = 6; i >= 0; i--) {
    const d = new Date(now);
    d.setDate(d.getDate() - i);
    const key = d.toISOString().slice(0, 10);
    days.push({ key, minutes: byDay[key] || 0, label: d.toLocaleDateString("fr-FR", { weekday: "narrow" }) });
  }

  const max = Math.max(...days.map((d) => d.minutes), 1);

  return (
    <div className="flex items-end gap-1 h-10">
      {days.map((d) => (
        <div key={d.key} className="flex flex-col items-center flex-1 gap-0.5">
          <div
            className="w-full rounded-t-sm transition-all duration-300"
            style={{
              height: `${Math.max((d.minutes / max) * 100, d.minutes > 0 ? 8 : 2)}%`,
              backgroundColor: d.minutes > 0 ? "#459492" : "hsl(var(--muted))",
              opacity: d.minutes > 0 ? 0.7 + (d.minutes / max) * 0.3 : 0.3,
              minHeight: 2,
            }}
          />
          <span className="text-[8px] text-muted-foreground/50">{d.label}</span>
        </div>
      ))}
    </div>
  );
}

export default function WeeklyDigestCard({ stats, onDismiss }) {
  const navigate = useNavigate();

  if (!stats || !stats.sessions) return null;

  const { sessions, xp, streak_days, social, new_badges, top_accomplishment } = stats;
  const hasActivity = sessions.count > 0 || xp.gained > 0;

  if (!hasActivity) return null;

  const totalSocial = (social?.new_followers || 0) + (social?.reactions_received || 0) + (social?.comments_received || 0);

  return (
    <div className="relative rounded-xl border border-[#459492]/30 bg-gradient-to-br from-[#459492]/5 via-transparent to-[#55B3AE]/5 p-4 space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-[#459492]/20 flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-[#459492]" />
          </div>
          <div>
            <h3 className="text-sm font-semibold">Récap de ta semaine</h3>
            <p className="text-[10px] text-muted-foreground">7 derniers jours</p>
          </div>
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="p-1 rounded-md hover:bg-muted/50 text-muted-foreground/40 hover:text-muted-foreground transition-colors"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* Top accomplishment */}
      {top_accomplishment && (
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-[#F5A623]/10 border border-[#F5A623]/20">
          <Star className="w-4 h-4 text-[#F5A623] shrink-0" />
          <p className="text-xs font-medium text-[#F5A623]">{top_accomplishment}</p>
        </div>
      )}

      {/* Stats grid */}
      <div className="grid grid-cols-3 gap-2">
        <div className="p-2 rounded-lg bg-card border border-border/50">
          <div className="flex items-center gap-1 mb-0.5">
            <Zap className="w-3 h-3 text-[#459492]" />
            <span className="text-[9px] text-muted-foreground">Sessions</span>
          </div>
          <p className="text-lg font-semibold tabular-nums">{sessions.count}</p>
          <TrendBadge trend={sessions.trend_sessions} />
        </div>
        <div className="p-2 rounded-lg bg-card border border-border/50">
          <div className="flex items-center gap-1 mb-0.5">
            <Clock className="w-3 h-3 text-[#55B3AE]" />
            <span className="text-[9px] text-muted-foreground">Minutes</span>
          </div>
          <p className="text-lg font-semibold tabular-nums">{sessions.minutes}</p>
          <TrendBadge trend={sessions.trend_minutes} />
        </div>
        <div className="p-2 rounded-lg bg-card border border-border/50">
          <div className="flex items-center gap-1 mb-0.5">
            <Flame className="w-3 h-3 text-[#E48C75]" />
            <span className="text-[9px] text-muted-foreground">Streak</span>
          </div>
          <p className="text-lg font-semibold tabular-nums">{streak_days}<span className="text-xs font-normal ml-0.5">j</span></p>
        </div>
      </div>

      {/* Activity chart */}
      {sessions.by_day && Object.keys(sessions.by_day).length > 0 && (
        <div className="px-1">
          <p className="text-[9px] text-muted-foreground mb-1">Minutes par jour</p>
          <MiniBarChart byDay={sessions.by_day} />
        </div>
      )}

      {/* XP gained */}
      {xp.gained > 0 && (
        <div className="flex items-center gap-2 text-xs">
          <div className="flex items-center gap-1 text-[#F5A623]">
            <Award className="w-3.5 h-3.5" />
            <span className="font-semibold">+{xp.gained} XP</span>
          </div>
          <span className="text-muted-foreground">·</span>
          <span className="text-muted-foreground">Niveau {xp.level} — {xp.title}</span>
        </div>
      )}

      {/* Social row */}
      {totalSocial > 0 && (
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          {social.new_followers > 0 && (
            <span className="flex items-center gap-1">
              <Users className="w-3 h-3 text-[#5DB786]" />
              +{social.new_followers} follower{social.new_followers > 1 ? "s" : ""}
            </span>
          )}
          {social.reactions_received > 0 && (
            <span className="flex items-center gap-1">
              <Heart className="w-3 h-3 text-[#E48C75]" />
              {social.reactions_received} réaction{social.reactions_received > 1 ? "s" : ""}
            </span>
          )}
          {social.comments_received > 0 && (
            <span className="flex items-center gap-1">
              <MessageCircle className="w-3 h-3 text-[#55B3AE]" />
              {social.comments_received} commentaire{social.comments_received > 1 ? "s" : ""}
            </span>
          )}
        </div>
      )}

      {/* New badges */}
      {new_badges && new_badges.length > 0 && (
        <div className="flex items-center gap-2 text-xs">
          <Award className="w-3.5 h-3.5 text-[#F5A623]" />
          <span className="text-muted-foreground">
            {new_badges.length === 1
              ? `Badge obtenu : ${new_badges[0].name}`
              : `${new_badges.length} badges obtenus cette semaine`}
          </span>
        </div>
      )}

      {/* CTA */}
      <button
        onClick={() => navigate("/progress")}
        className="flex items-center justify-center gap-1.5 w-full py-2 rounded-lg bg-[#459492]/10 hover:bg-[#459492]/20 text-xs font-medium text-[#459492] transition-colors"
      >
        Voir ma progression
        <ChevronRight className="w-3 h-3" />
      </button>
    </div>
  );
}
