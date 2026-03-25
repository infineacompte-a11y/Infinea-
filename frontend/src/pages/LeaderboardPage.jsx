import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  Trophy,
  Medal,
  Flame,
  Clock,
  Zap,
  RefreshCw,
  Crown,
  ChevronRight,
  Timer,
} from "lucide-react";
import { toast } from "sonner";
import { API, useAuth, authFetch } from "@/App";
import Sidebar from "@/components/Sidebar";

/* ── Tier config (Duolingo-inspired) ── */
const TIER_STYLES = {
  podium: "bg-gradient-to-br from-[#F5A623]/15 to-[#F5A623]/5 border-[#F5A623]/30",
  elite: "bg-gradient-to-br from-[#459492]/10 to-[#459492]/5 border-[#459492]/30",
  rising: "border-border bg-card",
  standard: "border-border bg-card opacity-70",
};

const RANK_COLORS = {
  1: { bg: "bg-gradient-to-br from-[#F5A623] to-[#E8960F]", text: "text-white", label: "1er" },
  2: { bg: "bg-gradient-to-br from-[#C0C0C0] to-[#A8A8A8]", text: "text-white", label: "2e" },
  3: { bg: "bg-gradient-to-br from-[#CD7F32] to-[#B56E28]", text: "text-white", label: "3e" },
};

/* ── Countdown to next Monday 00:00 UTC ── */
function useWeekCountdown(weekEnd) {
  const [remaining, setRemaining] = useState("");

  useEffect(() => {
    if (!weekEnd) return;
    const update = () => {
      const diff = new Date(weekEnd) - new Date();
      if (diff <= 0) {
        setRemaining("Nouveau classement !");
        return;
      }
      const d = Math.floor(diff / 86400000);
      const h = Math.floor((diff % 86400000) / 3600000);
      const m = Math.floor((diff % 3600000) / 60000);
      setRemaining(d > 0 ? `${d}j ${h}h` : `${h}h ${m}min`);
    };
    update();
    const id = setInterval(update, 60000);
    return () => clearInterval(id);
  }, [weekEnd]);

  return remaining;
}

/* ── Podium card for top 3 ── */
function PodiumCard({ entry, position }) {
  const navigate = useNavigate();
  const heights = { 1: "h-28", 2: "h-20", 3: "h-16" };
  const sizes = { 1: "w-16 h-16", 2: "w-13 h-13", 3: "w-12 h-12" };
  const ringColors = { 1: "ring-[#F5A623]", 2: "ring-[#C0C0C0]", 3: "ring-[#CD7F32]" };
  const icons = { 1: Crown, 2: Medal, 3: Medal };
  const Icon = icons[position];
  const initials = (entry.display_name || "?").slice(0, 2).toUpperCase();

  return (
    <div
      className="flex flex-col items-center cursor-pointer group"
      onClick={() => navigate(`/users/${entry.user_id}`)}
    >
      {/* Avatar + crown/medal */}
      <div className="relative mb-1">
        <Avatar
          className={`${sizes[position]} ring-2 ${ringColors[position]} transition-transform duration-200 group-hover:scale-105`}
        >
          <AvatarImage src={entry.avatar_url} alt={entry.display_name} />
          <AvatarFallback className="text-xs font-semibold">{initials}</AvatarFallback>
        </Avatar>
        {position === 1 && (
          <div className="absolute -top-3 left-1/2 -translate-x-1/2">
            <Crown className="w-5 h-5 text-[#F5A623] drop-shadow-sm" />
          </div>
        )}
      </div>
      <p className="text-xs font-medium truncate max-w-[80px] text-center">
        {entry.display_name}
      </p>
      <p className="text-[10px] text-muted-foreground font-semibold tabular-nums">
        {entry.score} pts
      </p>
      {/* Podium bar */}
      <div
        className={`${heights[position]} w-16 mt-1 rounded-t-lg flex items-center justify-center ${
          position === 1
            ? "bg-gradient-to-t from-[#F5A623]/40 to-[#F5A623]/20"
            : position === 2
            ? "bg-gradient-to-t from-[#C0C0C0]/30 to-[#C0C0C0]/15"
            : "bg-gradient-to-t from-[#CD7F32]/30 to-[#CD7F32]/15"
        }`}
      >
        <span className="font-bold text-lg tabular-nums opacity-60">{position}</span>
      </div>
    </div>
  );
}

export default function LeaderboardPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const countdown = useWeekCountdown(data?.week_end);

  const fetchLeaderboard = async () => {
    setIsLoading(true);
    try {
      const res = await authFetch(`${API}/leaderboard/weekly`);
      if (res.ok) {
        setData(await res.json());
      } else {
        toast.error("Erreur de chargement");
      }
    } catch {
      toast.error("Erreur réseau");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchLeaderboard();
  }, []);

  const leaderboard = data?.leaderboard || [];
  const myEntry = data?.my_entry;
  const top3 = leaderboard.slice(0, 3);
  const rest = leaderboard.slice(3);

  return (
    <div className="min-h-screen app-bg-mesh">
      <Sidebar />
      <main className="lg:ml-64 pt-14 lg:pt-0 pb-8">
        {/* Dark Header */}
        <div className="section-dark-header px-4 lg:px-8 pt-8 lg:pt-10 pb-8">
          <div className="max-w-3xl mx-auto">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-display text-3xl lg:text-4xl font-semibold text-white opacity-0 animate-fade-in">
                  Classement
                </h1>
                <p
                  className="text-white/60 text-sm mt-1 opacity-0 animate-fade-in"
                  style={{ animationDelay: "50ms" }}
                >
                  Classement hebdomadaire global
                </p>
              </div>
              {countdown && (
                <Badge
                  className="opacity-0 animate-fade-in bg-white/10 text-white/80 border-white/20 gap-1"
                  style={{ animationDelay: "100ms" }}
                >
                  <Timer className="w-3 h-3" />
                  {countdown}
                </Badge>
              )}
            </div>
          </div>
        </div>

        <div className="px-4 lg:px-8">
          <div className="max-w-3xl mx-auto">
            {/* Score breakdown legend */}
            <div
              className="opacity-0 animate-fade-in flex flex-wrap gap-3 mb-5 text-[11px] text-muted-foreground"
              style={{ animationDelay: "150ms", animationFillMode: "forwards" }}
            >
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" /> Minutes
              </span>
              <span className="flex items-center gap-1">
                <Zap className="w-3 h-3" /> Sessions x5
              </span>
              <span className="flex items-center gap-1">
                <Flame className="w-3 h-3" /> Streak x2
              </span>
              <span className="ml-auto">
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 text-xs gap-1 text-muted-foreground rounded-xl btn-press"
                  onClick={fetchLeaderboard}
                  disabled={isLoading}
                >
                  <RefreshCw className={`w-3 h-3 ${isLoading ? "animate-spin" : ""}`} />
                  Actualiser
                </Button>
              </span>
            </div>

            {isLoading ? (
              /* Skeleton */
              <div className="space-y-3">
                <div className="flex justify-center gap-4 mb-6">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="flex flex-col items-center gap-2 animate-pulse">
                      <div className="w-14 h-14 rounded-full bg-muted" />
                      <div className="h-3 w-12 rounded bg-muted" />
                      <div className={`w-16 ${i === 1 ? "h-28" : i === 2 ? "h-20" : "h-16"} rounded-t-lg bg-muted`} />
                    </div>
                  ))}
                </div>
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="rounded-xl border border-border bg-card p-3 animate-pulse">
                    <div className="flex items-center gap-3">
                      <div className="w-7 h-7 rounded-full bg-muted" />
                      <div className="w-8 h-8 rounded-full bg-muted" />
                      <div className="flex-1 space-y-1.5">
                        <div className="h-3 w-1/3 rounded bg-muted" />
                        <div className="h-2 w-1/4 rounded bg-muted" />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : leaderboard.length === 0 ? (
              /* Empty state */
              <Card className="p-8 text-center rounded-xl">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[#F5A623]/20 to-[#F5A623]/5 flex items-center justify-center mx-auto mb-3">
                  <Trophy className="w-8 h-8 text-[#F5A623]/60" />
                </div>
                <h3 className="font-semibold mb-1">Pas encore d'activité cette semaine</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Complete une session pour apparaître au classement !
                </p>
                <Button
                  onClick={() => navigate("/dashboard")}
                  className="rounded-xl gap-1.5 btn-press"
                >
                  Commencer une session
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </Card>
            ) : (
              <>
                {/* ── Podium (top 3) ── */}
                {top3.length >= 2 && (
                  <div
                    className="opacity-0 animate-fade-in flex items-end justify-center gap-3 mb-6 pt-4"
                    style={{ animationDelay: "200ms", animationFillMode: "forwards" }}
                  >
                    {/* 2nd place (left) */}
                    {top3[1] && <PodiumCard entry={top3[1]} position={2} />}
                    {/* 1st place (center, tallest) */}
                    {top3[0] && <PodiumCard entry={top3[0]} position={1} />}
                    {/* 3rd place (right) */}
                    {top3[2] && <PodiumCard entry={top3[2]} position={3} />}
                  </div>
                )}

                {/* Separator */}
                {rest.length > 0 && (
                  <div className="flex items-center gap-3 mb-3">
                    <div className="flex-1 h-px bg-border" />
                    <span className="text-[10px] text-muted-foreground uppercase tracking-wider">
                      Classement complet
                    </span>
                    <div className="flex-1 h-px bg-border" />
                  </div>
                )}

                {/* ── Ranked list (4+) ── */}
                <div className="space-y-1.5">
                  {rest.map((entry, idx) => {
                    const isMe = entry.user_id === user?.user_id;
                    const tierStyle = TIER_STYLES[entry.tier] || TIER_STYLES.standard;
                    const initials = (entry.display_name || "?").slice(0, 2).toUpperCase();

                    return (
                      <div
                        key={entry.user_id}
                        className={`opacity-0 animate-fade-in group flex items-center gap-3 p-3 rounded-xl border transition-all duration-200 hover:shadow-sm cursor-pointer ${tierStyle} ${
                          isMe ? "ring-1 ring-[#459492]/40 !bg-[#459492]/8" : ""
                        }`}
                        style={{
                          animationDelay: `${250 + idx * 25}ms`,
                          animationFillMode: "forwards",
                        }}
                        onClick={() => navigate(`/users/${entry.user_id}`)}
                      >
                        {/* Rank */}
                        <span className="w-7 text-center font-bold text-sm tabular-nums text-muted-foreground">
                          {entry.rank}
                        </span>

                        {/* Avatar */}
                        <Avatar className="w-8 h-8">
                          <AvatarImage src={entry.avatar_url} alt={entry.display_name} />
                          <AvatarFallback className="text-[10px] font-semibold">
                            {initials}
                          </AvatarFallback>
                        </Avatar>

                        {/* Name + stats */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-1.5">
                            <p className="font-medium text-sm truncate">
                              {entry.display_name}
                              {isMe && (
                                <span className="text-[10px] text-[#459492] ml-1 font-normal">
                                  (toi)
                                </span>
                              )}
                            </p>
                          </div>
                          <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
                            <span className="flex items-center gap-0.5">
                              <Clock className="w-2.5 h-2.5" />
                              {entry.total_minutes}min
                            </span>
                            <span className="flex items-center gap-0.5">
                              <Zap className="w-2.5 h-2.5" />
                              {entry.sessions_count} sessions
                            </span>
                            {entry.streak_days > 0 && (
                              <span className="flex items-center gap-0.5">
                                <Flame className="w-2.5 h-2.5" />
                                {entry.streak_days}j
                              </span>
                            )}
                          </div>
                        </div>

                        {/* Score */}
                        <span className="font-bold text-sm tabular-nums">{entry.score}</span>
                        <span className="text-[10px] text-muted-foreground">pts</span>
                      </div>
                    );
                  })}
                </div>

                {/* ── My position (sticky footer if not in top visible) ── */}
                {myEntry && myEntry.rank && myEntry.rank > 3 && (
                  <div
                    className="opacity-0 animate-fade-in sticky bottom-4 mt-4"
                    style={{ animationDelay: "400ms", animationFillMode: "forwards" }}
                  >
                    <Card className="p-3 rounded-xl border-[#459492]/30 bg-[#459492]/8 backdrop-blur-sm shadow-lg">
                      <div className="flex items-center gap-3">
                        <span className="w-7 text-center font-bold text-sm tabular-nums text-[#459492]">
                          {myEntry.rank}
                        </span>
                        <Avatar className="w-8 h-8 ring-1 ring-[#459492]/30">
                          <AvatarImage src={myEntry.avatar_url} />
                          <AvatarFallback className="text-[10px] font-semibold">
                            {(myEntry.display_name || "?").slice(0, 2).toUpperCase()}
                          </AvatarFallback>
                        </Avatar>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-sm">Ta position</p>
                          <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
                            <span>{myEntry.total_minutes}min</span>
                            <span>{myEntry.sessions_count} sessions</span>
                            {myEntry.streak_days > 0 && (
                              <span className="flex items-center gap-0.5">
                                <Flame className="w-2.5 h-2.5" />
                                {myEntry.streak_days}j
                              </span>
                            )}
                          </div>
                        </div>
                        <span className="font-bold text-sm tabular-nums">{myEntry.score}</span>
                        <span className="text-[10px] text-muted-foreground">pts</span>
                      </div>
                    </Card>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
