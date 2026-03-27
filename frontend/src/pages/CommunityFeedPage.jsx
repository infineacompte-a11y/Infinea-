import React, { useState, useEffect, useCallback, useRef } from "react";
import { Link } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Input } from "@/components/ui/input";
import {
  Flame,
  Award,
  Zap,
  MessageCircle,
  Send,
  Loader2,
  Trash2,
  Activity,
  Search,
  Users,
  Trophy,
  ChevronRight,
  Compass,
  Crown,
  UserPlus,
  Flag,
  RefreshCw,
} from "lucide-react";
import { toast } from "sonner";
import Sidebar from "@/components/Sidebar";
import FollowButton from "@/components/FollowButton";
import { API, authFetch, useAuth } from "@/App";
import SafetyMenu from "@/components/SafetyMenu";
import ReportDialog from "@/components/ReportDialog";
import MentionInput from "@/components/MentionInput";
import MentionText from "@/components/MentionText";
import ReactionsDetailDialog from "@/components/ReactionsDetailDialog";
import SocialOnboardingCard from "@/components/SocialOnboardingCard";
import { sanitize } from "@/lib/sanitize";

// ── Reaction config (InFinea DNA) ──
const REACTIONS = [
  { type: "bravo", emoji: "👏", label: "Bravo" },
  { type: "inspire", emoji: "💡", label: "Inspirant" },
  { type: "fire", emoji: "🔥", label: "En feu" },
];

// ── Activity type config ──
const ACTIVITY_CONFIG = {
  session_completed: {
    icon: Zap,
    color: "#459492",
    getText: (data) => {
      const d = data.duration || 0;
      return `a terminé "${data.action_title || "une micro-action"}" en ${d} min`;
    },
  },
  badge_earned: {
    icon: Award,
    color: "#E48C75",
    getText: (data) => `a obtenu le badge "${data.badge_name || "nouveau badge"}"`,
  },
  streak_milestone: {
    icon: Flame,
    color: "#E48C75",
    getText: (data) => `a atteint ${data.streak_days} jours de streak !`,
  },
  challenge_completed: {
    icon: Trophy,
    color: "#459492",
    getText: (data) => `a complété le défi "${data.challenge_title || "un défi"}" !`,
  },
};

function timeAgo(iso) {
  if (!iso) return "";
  const diff = Date.now() - new Date(iso).getTime();
  const min = Math.floor(diff / 60000);
  if (min < 1) return "à l'instant";
  if (min < 60) return `il y a ${min} min`;
  const h = Math.floor(min / 60);
  if (h < 24) return `il y a ${h}h`;
  const d = Math.floor(h / 24);
  if (d < 7) return `il y a ${d}j`;
  return new Date(iso).toLocaleDateString("fr-FR", { day: "numeric", month: "short" });
}

function getInitials(name) {
  if (!name) return "U";
  return name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2);
}

// ── Suggested Users (horizontal scroll — Instagram stories style) ──
function SuggestedUsers({ currentUserId }) {
  const [users, setUsers] = useState([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const res = await authFetch(`${API}/feed/suggested-users?limit=15`);
        if (res.ok) {
          const data = await res.json();
          setUsers(data.users || []);
        }
      } catch { /* silent */ }
      setLoaded(true);
    })();
  }, []);

  if (!loaded || users.length === 0) return null;

  return (
    <div className="mb-5 opacity-0 animate-fade-in" style={{ animationFillMode: "forwards" }}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <UserPlus className="w-4 h-4 text-primary" />
          <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
            Suggestions
          </span>
        </div>
        <Link to="/search" className="text-xs text-primary hover:underline">
          Voir tout
        </Link>
      </div>
      <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-thin snap-x snap-mandatory">
        {users.map((u) => (
          <div
            key={u.user_id}
            className="flex flex-col items-center gap-2 min-w-[100px] max-w-[100px] snap-start"
          >
            <Link to={`/users/${u.user_id}`}>
              <Avatar className="w-14 h-14 ring-2 ring-primary/15 ring-offset-2 ring-offset-background">
                <AvatarImage src={u.avatar_url} alt={u.display_name} />
                <AvatarFallback className="bg-primary/10 text-primary text-sm font-medium">
                  {getInitials(u.display_name)}
                </AvatarFallback>
              </Avatar>
            </Link>
            <div className="text-center w-full">
              <Link to={`/users/${u.user_id}`}>
                <p className="text-xs font-medium text-foreground truncate">
                  {u.display_name}
                </p>
              </Link>
              {u.username && (
                <p className="text-[10px] text-muted-foreground truncate">@{u.username}</p>
              )}
              {u.subscription_tier === "premium" && (
                <Crown className="w-3 h-3 text-[#E48C75] mx-auto mt-0.5" />
              )}
            </div>
            <FollowButton userId={u.user_id} initialFollowing={false} size="xs" />
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Single Activity Card (Instagram-style) ──
function ActivityCard({ activity, currentUserId, onReactionChange, onDelete }) {
  const config = ACTIVITY_CONFIG[activity.type] || ACTIVITY_CONFIG.session_completed;
  const Icon = config.icon;
  const [showComments, setShowComments] = useState(false);
  const [comments, setComments] = useState([]);
  const [commentsLoaded, setCommentsLoaded] = useState(false);
  const [commentText, setCommentText] = useState("");
  const [commentMentions, setCommentMentions] = useState([]);
  const [sendingComment, setSendingComment] = useState(false);
  const [reportCommentId, setReportCommentId] = useState(null);
  const [reactingType, setReactingType] = useState(null);
  const [reactionsDetailOpen, setReactionsDetailOpen] = useState(false);

  const totalReactions =
    (activity.reaction_counts?.bravo || 0) +
    (activity.reaction_counts?.inspire || 0) +
    (activity.reaction_counts?.fire || 0);

  const loadComments = useCallback(async () => {
    if (commentsLoaded) return;
    try {
      const res = await authFetch(`${API}/activities/${activity.activity_id}/comments`);
      if (res.ok) {
        const data = await res.json();
        setComments(data.comments || []);
        setCommentsLoaded(true);
      }
    } catch { /* silent */ }
  }, [activity.activity_id, commentsLoaded]);

  const handleToggleComments = () => {
    const next = !showComments;
    setShowComments(next);
    if (next) loadComments();
  };

  const handleReact = async (type) => {
    setReactingType(type);
    try {
      const res = await authFetch(`${API}/activities/${activity.activity_id}/react`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reaction_type: type }),
      });
      if (res.ok) {
        const data = await res.json();
        onReactionChange(activity.activity_id, type, data);
      }
    } catch {
      toast.error("Erreur");
    } finally {
      setReactingType(null);
    }
  };

  const handleSendComment = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
    const text = commentText.trim();
    if (!text) return;
    setSendingComment(true);
    try {
      const res = await authFetch(`${API}/activities/${activity.activity_id}/comments`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: text }),
      });
      if (res.ok) {
        const newComment = await res.json();
        setComments((prev) => [...prev, newComment]);
        setCommentText("");
        setCommentMentions([]);
      } else {
        toast.error("Erreur lors de l'envoi");
      }
    } catch {
      toast.error("Erreur de connexion");
    } finally {
      setSendingComment(false);
    }
  };

  const handleDeleteComment = async (commentId) => {
    try {
      const res = await authFetch(`${API}/comments/${commentId}`, { method: "DELETE" });
      if (res.ok) {
        setComments((prev) => prev.filter((c) => c.comment_id !== commentId));
      }
    } catch { /* silent */ }
  };

  return (
    <Card className="overflow-hidden hover:shadow-md transition-shadow duration-300">
      <CardContent className="p-4">
        {/* Header: avatar + name + time */}
        <div className="flex items-start gap-3">
          <Link to={`/users/${activity.user_id}`}>
            <Avatar className="w-10 h-10 shrink-0 ring-2 ring-primary/10 ring-offset-1 ring-offset-background">
              <AvatarImage src={activity.user_avatar} alt={activity.user_name} />
              <AvatarFallback className="bg-primary/10 text-primary text-xs">
                {getInitials(activity.user_name)}
              </AvatarFallback>
            </Avatar>
          </Link>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <Link
                to={`/users/${activity.user_id}`}
                className="font-semibold text-sm text-foreground hover:underline"
              >
                {activity.user_name}
              </Link>
              {activity.user_username && (
                <span className="text-xs text-muted-foreground">@{activity.user_username}</span>
              )}
              <span className="text-[11px] text-muted-foreground/50 ml-auto shrink-0">
                {timeAgo(activity.created_at)}
              </span>
              {activity.user_id === currentUserId ? (
                <button
                  onClick={() => {
                    if (window.confirm("Supprimer cette activité ?")) onDelete?.(activity.activity_id);
                  }}
                  className="text-muted-foreground/40 hover:text-destructive transition-colors p-1"
                  title="Supprimer"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              ) : (
                <SafetyMenu
                  userId={activity.user_id}
                  targetType="activity"
                  targetId={activity.activity_id}
                  size="sm"
                  onBlockChange={(blocked) => {
                    if (blocked) window.location.reload();
                  }}
                />
              )}
            </div>
            <div className="flex items-center gap-1.5 mt-1">
              <div
                className="w-5 h-5 rounded-md flex items-center justify-center"
                style={{ backgroundColor: `${config.color}15` }}
              >
                <Icon className="w-3 h-3" style={{ color: config.color }} />
              </div>
              <p className="text-sm text-foreground/80">
                {config.getText(activity.data || {})}
              </p>
            </div>
          </div>
        </div>

        {/* Reaction bar — Instagram style */}
        <div className="flex items-center gap-1 mt-3 pt-3 border-t border-border/40">
          {REACTIONS.map((r) => {
            const count = activity.reaction_counts?.[r.type] || 0;
            const isActive = activity.user_reaction === r.type;
            return (
              <button
                key={r.type}
                onClick={() => handleReact(r.type)}
                disabled={reactingType !== null}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs transition-all duration-200 ${
                  isActive
                    ? "bg-primary/10 text-primary font-medium ring-1 ring-primary/20 scale-105"
                    : "text-muted-foreground hover:bg-muted/60 hover:scale-105"
                }`}
                title={r.label}
              >
                <span className={`text-sm ${isActive ? "animate-bounce-once" : ""}`}>{r.emoji}</span>
                {count > 0 && <span className="tabular-nums">{count}</span>}
              </button>
            );
          })}

          <div className="flex-1" />

          {/* Reactions total — clickable to see who reacted */}
          {totalReactions > 0 && (
            <button
              onClick={() => setReactionsDetailOpen(true)}
              className="text-[11px] text-muted-foreground/50 hover:text-muted-foreground transition-colors mr-1"
            >
              {totalReactions} réaction{totalReactions > 1 ? "s" : ""}
            </button>
          )}

          {/* Comment toggle */}
          <button
            onClick={handleToggleComments}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs transition-all duration-200 ${
              showComments
                ? "bg-muted text-foreground"
                : "text-muted-foreground hover:bg-muted/60"
            }`}
          >
            <MessageCircle className="w-3.5 h-3.5" />
            {activity.comment_count > 0 && (
              <span className="tabular-nums">{activity.comment_count}</span>
            )}
          </button>
        </div>

        {/* "View comments" teaser — always visible if comments exist */}
        {!showComments && activity.comment_count > 0 && (
          <button
            onClick={handleToggleComments}
            className="text-xs text-muted-foreground/60 hover:text-muted-foreground mt-2 transition-colors"
          >
            Voir {activity.comment_count > 1 ? `les ${activity.comment_count} commentaires` : "le commentaire"}
          </button>
        )}

        {/* Comments section — expandable */}
        {showComments && (
          <div className="mt-3 pt-2 border-t border-border/30 space-y-2.5 animate-fade-in" style={{ animationFillMode: "forwards" }}>
            {comments.length === 0 && commentsLoaded && (
              <p className="text-xs text-muted-foreground/50 text-center py-2">
                Aucun commentaire — soyez le premier !
              </p>
            )}

            {comments.map((c) => (
              <div key={c.comment_id} className="flex items-start gap-2 group">
                <Link to={`/users/${c.user_id}`}>
                  <Avatar className="w-6 h-6 shrink-0">
                    <AvatarImage src={c.user_avatar} />
                    <AvatarFallback className="bg-muted text-[9px]">
                      {getInitials(c.user_name)}
                    </AvatarFallback>
                  </Avatar>
                </Link>
                <div className="flex-1 min-w-0">
                  <div className="flex items-baseline gap-1.5">
                    <Link
                      to={`/users/${c.user_id}`}
                      className="font-semibold text-xs text-foreground hover:underline"
                    >
                      {c.user_name}
                    </Link>
                    <MentionText
                      content={c.content}
                      mentions={c.mentions}
                      currentUserId={currentUserId}
                      className="text-xs text-foreground/70 break-words"
                    />
                  </div>
                  <span className="text-[10px] text-muted-foreground/50">
                    {timeAgo(c.created_at)}
                  </span>
                </div>
                {c.user_id === currentUserId ? (
                  <button
                    onClick={() => handleDeleteComment(c.comment_id)}
                    className="opacity-0 group-hover:opacity-100 text-muted-foreground/40 hover:text-destructive transition-all p-1"
                    title="Supprimer"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                ) : (
                  <button
                    onClick={() => setReportCommentId(c.comment_id)}
                    className="opacity-0 group-hover:opacity-100 text-muted-foreground/40 hover:text-destructive transition-all p-1"
                    title="Signaler"
                  >
                    <Flag className="w-3 h-3" />
                  </button>
                )}
              </div>
            ))}

            {/* Comment input — with @mention autocomplete */}
            <form onSubmit={handleSendComment} className="flex items-center gap-2 pt-1">
              <MentionInput
                value={commentText}
                onChange={setCommentText}
                mentions={commentMentions}
                onMentionsChange={setCommentMentions}
                context="comment"
                contextId={activity.activity_id}
                placeholder="Ajouter un commentaire..."
                maxLength={500}
                className="h-8 text-xs rounded-full border-border/50 bg-muted/30 focus:bg-white"
                onSubmit={handleSendComment}
              />
              <Button
                type="submit"
                size="icon"
                variant="ghost"
                className="h-8 w-8 shrink-0 rounded-full"
                disabled={!commentText.trim() || sendingComment}
              >
                {sendingComment ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Send className="w-3.5 h-3.5 text-primary" />
                )}
              </Button>
            </form>
          </div>
        )}

        {/* Report comment dialog */}
        {reportCommentId && (
          <ReportDialog
            open={!!reportCommentId}
            onOpenChange={(open) => { if (!open) setReportCommentId(null); }}
            targetType="comment"
            targetId={reportCommentId}
          />
        )}

        {/* Reactions detail dialog */}
        <ReactionsDetailDialog
          open={reactionsDetailOpen}
          onOpenChange={setReactionsDetailOpen}
          activityId={activity.activity_id}
          reactionCounts={activity.reaction_counts}
        />
      </CardContent>
    </Card>
  );
}

// ── Quick links ──
const quickLinks = [
  { to: "/search", icon: Search, title: "Rechercher des membres", color: "#459492" },
  { to: "/groups", icon: Users, title: "Mes groupes", color: "#459492" },
  { to: "/challenges", icon: Trophy, title: "Défis communautaires", color: "#E48C75" },
];

// ── Main Page ──
export default function CommunityFeedPage() {
  const { user } = useAuth();
  const [tab, setTab] = useState("feed"); // "feed" | "discover"
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [cursor, setCursor] = useState(null);
  const [hasMore, setHasMore] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const sentinelRef = useRef(null);

  const fetchFeed = useCallback(async (cursorVal = null, feedTab = "feed") => {
    const isInitial = !cursorVal;
    if (isInitial) setLoading(true);
    else setLoadingMore(true);

    try {
      const endpoint = feedTab === "discover" ? "feed/discover" : "feed";
      const url = cursorVal
        ? `${API}/${endpoint}?limit=15&cursor=${encodeURIComponent(cursorVal)}`
        : `${API}/${endpoint}?limit=15`;
      const res = await authFetch(url);
      if (res.ok) {
        const data = await res.json();
        setActivities((prev) =>
          isInitial ? data.activities : [...prev, ...data.activities]
        );
        setCursor(data.next_cursor);
        setHasMore(data.has_more);
      }
    } catch {
      toast.error("Erreur lors du chargement");
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, []);

  // Load on mount and tab change
  useEffect(() => {
    setActivities([]);
    setCursor(null);
    setHasMore(false);
    fetchFeed(null, tab);
  }, [tab, fetchFeed]);

  // Infinite scroll
  useEffect(() => {
    if (!sentinelRef.current || !hasMore || loadingMore) return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !loadingMore && cursor) {
          fetchFeed(cursor, tab);
        }
      },
      { threshold: 0.1 }
    );
    observer.observe(sentinelRef.current);
    return () => observer.disconnect();
  }, [hasMore, loadingMore, cursor, tab, fetchFeed]);

  // Delete own activity
  const handleDeleteActivity = async (activityId) => {
    try {
      const res = await authFetch(`${API}/activities/${activityId}`, { method: "DELETE" });
      if (res.ok) {
        setActivities((prev) => prev.filter((a) => a.activity_id !== activityId));
        toast.success("Activité supprimée");
      } else {
        toast.error("Erreur lors de la suppression");
      }
    } catch {
      toast.error("Erreur de connexion");
    }
  };

  // Manual refresh
  const handleRefresh = async () => {
    setRefreshing(true);
    setActivities([]);
    setCursor(null);
    setHasMore(false);
    await fetchFeed(null, tab);
    setRefreshing(false);
  };

  // Optimistic reaction update
  const handleReactionChange = (activityId, reactionType, serverData) => {
    setActivities((prev) =>
      prev.map((a) => {
        if (a.activity_id !== activityId) return a;
        const counts = { ...a.reaction_counts };
        if (serverData.reacted) {
          if (a.user_reaction && a.user_reaction !== reactionType) {
            counts[a.user_reaction] = Math.max(0, (counts[a.user_reaction] || 0) - 1);
          }
          if (a.user_reaction !== reactionType) {
            counts[reactionType] = (counts[reactionType] || 0) + 1;
          }
          return { ...a, reaction_counts: counts, user_reaction: reactionType };
        } else {
          counts[reactionType] = Math.max(0, (counts[reactionType] || 0) - 1);
          return { ...a, reaction_counts: counts, user_reaction: null };
        }
      })
    );
  };

  return (
    <div className="min-h-screen app-bg-mesh">
      <Sidebar />
      <main className="lg:ml-64 pt-14 lg:pt-0 pb-8">
        {/* Dark Header */}
        <div className="section-dark-header px-4 lg:px-8 pt-8 lg:pt-10 pb-4">
          <div className="max-w-2xl mx-auto">
            <div className="flex items-center justify-between opacity-0 animate-fade-in" style={{ animationFillMode: "forwards" }}>
              <div>
                <h1 className="text-display text-3xl lg:text-4xl font-semibold text-white">
                  Communauté
                </h1>
                <p className="text-white/60 text-sm mt-1">
                  Suivez la progression de vos amis et découvrez la communauté
                </p>
              </div>
              <button
                onClick={handleRefresh}
                disabled={refreshing || loading}
                className="w-9 h-9 rounded-xl bg-white/10 hover:bg-white/20 flex items-center justify-center transition-all duration-200 disabled:opacity-40 shrink-0"
                title="Actualiser le fil"
              >
                <RefreshCw className={`w-4 h-4 text-white ${refreshing ? "animate-spin" : ""}`} />
              </button>
            </div>

            {/* Tab bar — Instagram style */}
            <div className="flex gap-1 mt-5 bg-white/10 rounded-xl p-1 opacity-0 animate-fade-in" style={{ animationDelay: "100ms" }}>
              <button
                onClick={() => setTab("feed")}
                className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                  tab === "feed"
                    ? "bg-white text-[#275255] shadow-sm"
                    : "text-white/60 hover:text-white/80"
                }`}
              >
                <Activity className="w-4 h-4" />
                Fil
              </button>
              <button
                onClick={() => setTab("discover")}
                className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                  tab === "discover"
                    ? "bg-white text-[#275255] shadow-sm"
                    : "text-white/60 hover:text-white/80"
                }`}
              >
                <Compass className="w-4 h-4" />
                Découvrir
              </button>
            </div>
          </div>
        </div>

        <div className="px-4 lg:px-8">
          <div className="max-w-2xl mx-auto mt-5">
            {/* Social onboarding card — shown on feed tab when onboarding needed */}
            {tab === "feed" && (
              <SocialOnboardingCard
                currentUserId={user?.user_id}
                onFollowChange={() => {
                  // Refresh feed after a follow to potentially show new content
                  setTimeout(() => fetchFeed(null, "feed"), 1500);
                }}
              />
            )}

            {/* Suggested users — show on discover tab or feed tab when empty */}
            {(tab === "discover" || (tab === "feed" && !loading && activities.length === 0)) && (
              <SuggestedUsers currentUserId={user?.user_id} />
            )}

            {/* Loading state */}
            {loading && (
              <div className="flex flex-col items-center justify-center py-16">
                <Loader2 className="w-6 h-6 text-primary animate-spin" />
                <p className="text-sm text-muted-foreground mt-3">Chargement...</p>
              </div>
            )}

            {/* Empty state — Feed tab */}
            {!loading && activities.length === 0 && tab === "feed" && (
              <div className="opacity-0 animate-fade-in" style={{ animationFillMode: "forwards" }}>
                <div className="flex flex-col items-center justify-center py-10 text-center mb-6">
                  <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center mb-4 ring-1 ring-primary/10">
                    <Activity className="w-7 h-7 text-primary" />
                  </div>
                  <h2 className="text-base font-semibold text-foreground mb-1">
                    Votre fil est vide
                  </h2>
                  <p className="text-muted-foreground text-sm max-w-xs mb-4">
                    Suivez des utilisateurs pour voir leur activité ici, ou explorez la communauté !
                  </p>
                  <div className="flex gap-3">
                    <Link to="/search">
                      <Button variant="outline" className="rounded-xl gap-2">
                        <Search className="w-4 h-4" />
                        Trouver des membres
                      </Button>
                    </Link>
                    <Button
                      variant="default"
                      className="rounded-xl gap-2"
                      onClick={() => setTab("discover")}
                    >
                      <Compass className="w-4 h-4" />
                      Découvrir
                    </Button>
                  </div>
                </div>

                {/* Quick links */}
                <div className="space-y-2.5">
                  {quickLinks.map((link, i) => (
                    <Link key={link.to} to={link.to}>
                      <Card
                        className="hover:border-[#459492]/20 hover:shadow-md hover:-translate-y-0.5 transition-all duration-300 cursor-pointer opacity-0 animate-fade-in"
                        style={{ animationDelay: `${200 + i * 80}ms`, animationFillMode: "forwards" }}
                      >
                        <CardContent className="p-4 flex items-center gap-4">
                          <div
                            className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                            style={{ backgroundColor: `${link.color}15` }}
                          >
                            <link.icon className="w-5 h-5" style={{ color: link.color }} />
                          </div>
                          <span className="font-sans font-semibold tracking-tight text-sm flex-1">
                            {link.title}
                          </span>
                          <ChevronRight className="w-5 h-5 text-muted-foreground" />
                        </CardContent>
                      </Card>
                    </Link>
                  ))}
                </div>
              </div>
            )}

            {/* Empty state — Discover tab */}
            {!loading && activities.length === 0 && tab === "discover" && (
              <div className="flex flex-col items-center justify-center py-10 text-center opacity-0 animate-fade-in" style={{ animationFillMode: "forwards" }}>
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center mb-4 ring-1 ring-primary/10">
                  <Compass className="w-7 h-7 text-primary" />
                </div>
                <h2 className="text-base font-semibold text-foreground mb-1">
                  La communauté démarre
                </h2>
                <p className="text-muted-foreground text-sm max-w-xs mb-4">
                  Complétez des sessions pour être le premier à partager votre progression !
                </p>
                <Link to="/dashboard">
                  <Button variant="default" className="rounded-xl gap-2">
                    <Zap className="w-4 h-4" />
                    Commencer une session
                  </Button>
                </Link>
              </div>
            )}

            {/* Feed */}
            {!loading && activities.length > 0 && (
              <div className="space-y-3 opacity-0 animate-fade-in" style={{ animationFillMode: "forwards" }}>
                {activities.map((activity, i) => (
                  <div
                    key={activity.activity_id}
                    className={i < 15 ? "opacity-0 animate-fade-in" : ""}
                    style={i < 15 ? { animationDelay: `${50 + i * 40}ms`, animationFillMode: "forwards" } : undefined}
                  >
                    <ActivityCard
                      activity={activity}
                      currentUserId={user?.user_id}
                      onReactionChange={handleReactionChange}
                      onDelete={handleDeleteActivity}
                    />
                  </div>
                ))}

                {/* Infinite scroll sentinel */}
                <div ref={sentinelRef} className="h-1" />

                {loadingMore && (
                  <div className="flex justify-center py-6">
                    <Loader2 className="w-5 h-5 text-primary animate-spin" />
                  </div>
                )}

                {!hasMore && activities.length > 5 && (
                  <p className="text-center text-xs text-muted-foreground py-4">
                    Vous êtes à jour !
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
