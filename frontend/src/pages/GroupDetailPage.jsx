import React, { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Users,
  Crown,
  Clock,
  TrendingUp,
  Flame,
  ArrowLeft,
  UserPlus,
  LogOut,
  Trash2,
  Loader2,
  Activity,
} from "lucide-react";
import { toast } from "sonner";
import { API, authFetch, useAuth } from "@/App";
import Sidebar from "@/components/Sidebar";
import InviteGroupDialog from "@/components/InviteGroupDialog";

/**
 * GroupDetailPage — Detailed group view with leaderboard + activity feed.
 * Pattern: Strava Club detail + Duolingo League leaderboard.
 *
 * Route: /groups/:groupId
 */

function formatMinutes(min) {
  if (!min) return "0 min";
  if (min < 60) return `${min} min`;
  const h = Math.floor(min / 60);
  const m = min % 60;
  return m > 0 ? `${h}h${m.toString().padStart(2, "0")}` : `${h}h`;
}

function timeAgo(dateStr) {
  if (!dateStr) return "";
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "à l'instant";
  if (mins < 60) return `il y a ${mins} min`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `il y a ${hours}h`;
  const days = Math.floor(hours / 24);
  return `il y a ${days}j`;
}

export default function GroupDetailPage() {
  const { groupId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [group, setGroup] = useState(null);
  const [feed, setFeed] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [inviteOpen, setInviteOpen] = useState(false);
  const [isLeaving, setIsLeaving] = useState(false);

  const fetchGroup = useCallback(async () => {
    try {
      const [groupRes, feedRes] = await Promise.all([
        authFetch(`${API}/groups/${groupId}`),
        authFetch(`${API}/groups/${groupId}/feed`),
      ]);
      if (groupRes.status === 404) {
        toast.error("Groupe introuvable");
        navigate("/groups");
        return;
      }
      if (!groupRes.ok) throw new Error("Erreur");
      const groupData = await groupRes.json();
      setGroup(groupData);

      if (feedRes.ok) {
        const feedData = await feedRes.json();
        setFeed(feedData.feed || []);
      }
    } catch {
      toast.error("Impossible de charger le groupe");
    } finally {
      setIsLoading(false);
    }
  }, [groupId, navigate]);

  useEffect(() => {
    fetchGroup();
  }, [fetchGroup]);

  const handleLeave = useCallback(async () => {
    if (!confirm("Quitter ce groupe ?")) return;
    setIsLeaving(true);
    try {
      const res = await authFetch(`${API}/groups/${groupId}/leave`, { method: "POST" });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        toast.error(data.detail || "Impossible de quitter le groupe");
        return;
      }
      toast.success("Tu as quitté le groupe");
      navigate("/groups");
    } catch {
      toast.error("Erreur réseau");
    } finally {
      setIsLeaving(false);
    }
  }, [groupId, navigate]);

  const handleDelete = useCallback(async () => {
    if (!confirm("Archiver ce groupe ? Cette action est irréversible.")) return;
    try {
      const res = await authFetch(`${API}/groups/${groupId}`, { method: "DELETE" });
      if (!res.ok) throw new Error();
      toast.success("Groupe archivé");
      navigate("/groups");
    } catch {
      toast.error("Impossible d'archiver le groupe");
    }
  }, [groupId, navigate]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background">
        <Sidebar />
        <main className="lg:ml-64 pt-20 lg:pt-8 px-4 lg:px-8 pb-8">
          <div className="flex justify-center py-20">
            <Loader2 className="w-6 h-6 animate-spin text-primary" />
          </div>
        </main>
      </div>
    );
  }

  if (!group) return null;

  const members = group.members?.filter((m) => m.status === "active") || [];
  const currentUserId = user?.user_id || user?.id;
  const isOwner = members.some((m) => m.user_id === currentUserId && m.role === "owner");

  // Leaderboard: sorted by week_minutes descending
  const leaderboard = [...members].sort(
    (a, b) => (b.stats?.week_minutes || 0) - (a.stats?.week_minutes || 0)
  );

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <main className="lg:ml-64 pt-20 lg:pt-8 px-4 lg:px-8 pb-8">
        <div className="max-w-3xl mx-auto">
          {/* Back + header */}
          <div className="mb-6">
            <Link
              to="/groups"
              className="inline-flex items-center gap-1.5 text-muted-foreground hover:text-foreground text-sm mb-4 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Mes Groupes
            </Link>

            <div className="flex items-start justify-between">
              <div>
                <h1 className="text-2xl font-heading font-bold text-foreground">
                  {group.name}
                </h1>
                {group.description && (
                  <p className="text-muted-foreground text-sm mt-1">{group.description}</p>
                )}
                <p className="text-muted-foreground text-xs mt-2">
                  {members.length} membre{members.length > 1 ? "s" : ""} · Créé le{" "}
                  {new Date(group.created_at).toLocaleDateString("fr-FR", {
                    day: "numeric",
                    month: "long",
                  })}
                </p>
              </div>

              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setInviteOpen(true)}
                  className="gap-1.5"
                >
                  <UserPlus className="w-4 h-4" />
                  <span className="hidden sm:inline">Inviter</span>
                </Button>
                {isOwner ? (
                  <Button variant="ghost" size="sm" onClick={handleDelete}>
                    <Trash2 className="w-4 h-4 text-destructive" />
                  </Button>
                ) : (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleLeave}
                    disabled={isLeaving}
                  >
                    <LogOut className="w-4 h-4 text-muted-foreground" />
                  </Button>
                )}
              </div>
            </div>
          </div>

          {/* Leaderboard */}
          <div className="mb-6">
            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-3 flex items-center gap-2">
              <Users className="w-4 h-4" />
              Classement cette semaine
            </h2>
            <div className="space-y-2">
              {leaderboard.map((member, i) => (
                <Card
                  key={member.user_id}
                  className={`border-border ${
                    member.user_id === currentUserId
                      ? "bg-primary/5 border-primary/20"
                      : "bg-card"
                  }`}
                >
                  <CardContent className="p-4 flex items-center gap-4">
                    {/* Rank */}
                    <div
                      className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
                        i === 0
                          ? "bg-amber-500/20 text-amber-400"
                          : i === 1
                            ? "bg-gray-400/20 text-gray-300"
                            : i === 2
                              ? "bg-orange-600/20 text-orange-400"
                              : "bg-white/5 text-white/40"
                      }`}
                    >
                      {i + 1}
                    </div>

                    {/* Avatar */}
                    <div
                      className="w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold shrink-0"
                      style={{ background: `hsl(${(i * 67 + 200) % 360}, 60%, 45%)` }}
                    >
                      {member.role === "owner" ? (
                        <Crown className="w-4 h-4 text-white" />
                      ) : (
                        <span className="text-white">
                          {(member.name || "?")[0].toUpperCase()}
                        </span>
                      )}
                    </div>

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <div className="text-foreground text-sm font-medium truncate flex items-center gap-1.5">
                        {member.name || "Membre"}
                        {member.role === "owner" && (
                          <Crown className="w-3 h-3 text-amber-400" />
                        )}
                      </div>
                      <div className="flex items-center gap-3 text-muted-foreground text-xs mt-0.5">
                        {member.stats?.streak_days > 0 && (
                          <span className="flex items-center gap-1">
                            <Flame className="w-3 h-3 text-orange-400" />
                            {member.stats.streak_days}j
                          </span>
                        )}
                        <span className="flex items-center gap-1">
                          <TrendingUp className="w-3 h-3" />
                          {member.stats?.week_sessions || 0} sessions
                        </span>
                      </div>
                    </div>

                    {/* Week time */}
                    <div className="text-right shrink-0">
                      <div className="text-foreground text-sm font-bold tabular-nums">
                        {formatMinutes(member.stats?.week_minutes || 0)}
                      </div>
                      <div className="text-muted-foreground text-[10px]">cette semaine</div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          {/* Activity feed */}
          {feed.length > 0 && (
            <div>
              <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-3 flex items-center gap-2">
                <Activity className="w-4 h-4" />
                Activité récente
              </h2>
              <div className="space-y-1.5">
                {feed.map((entry, i) => (
                  <div
                    key={i}
                    className="flex items-center gap-3 px-4 py-2.5 rounded-lg bg-card border border-border"
                  >
                    <div
                      className="w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0"
                      style={{
                        background: `hsl(${(entry.user_name?.charCodeAt(0) * 37 || 200) % 360}, 60%, 45%)`,
                      }}
                    >
                      <span className="text-white">
                        {(entry.user_name || "?")[0].toUpperCase()}
                      </span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <span className="text-foreground text-sm">
                        <span className="font-medium">{entry.user_name || "Membre"}</span>
                        {" — "}
                        <span className="text-muted-foreground">
                          {entry.action_title || "session complétée"}
                        </span>
                      </span>
                    </div>
                    <span className="text-muted-foreground text-xs shrink-0">
                      {timeAgo(entry.completed_at)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </main>

      <InviteGroupDialog
        open={inviteOpen}
        onOpenChange={setInviteOpen}
        groupId={groupId}
        groupName={group.name}
      />
    </div>
  );
}
