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
  ChevronDown,
  Activity,
  Search,
  Users,
  Trophy,
  ChevronRight,
} from "lucide-react";
import { toast } from "sonner";
import Sidebar from "@/components/Sidebar";
import { API, authFetch, useAuth } from "@/App";

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

// ── Single Activity Card ──
function ActivityCard({ activity, currentUserId, onReactionChange }) {
  const config = ACTIVITY_CONFIG[activity.type] || ACTIVITY_CONFIG.session_completed;
  const Icon = config.icon;
  const [showComments, setShowComments] = useState(false);
  const [comments, setComments] = useState([]);
  const [commentsLoaded, setCommentsLoaded] = useState(false);
  const [commentText, setCommentText] = useState("");
  const [sendingComment, setSendingComment] = useState(false);
  const [reactingType, setReactingType] = useState(null);

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
    e.preventDefault();
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
    <Card className="overflow-hidden">
      <CardContent className="p-4">
        {/* Header: avatar + name + time */}
        <div className="flex items-start gap-3">
          <Link to={`/users/${activity.user_id}`}>
            <Avatar className="w-10 h-10 shrink-0">
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
            </div>
            <div className="flex items-center gap-1.5 mt-0.5">
              <div
                className="w-4 h-4 rounded flex items-center justify-center"
                style={{ backgroundColor: `${config.color}20` }}
              >
                <Icon className="w-2.5 h-2.5" style={{ color: config.color }} />
              </div>
              <p className="text-sm text-muted-foreground">
                {config.getText(activity.data || {})}
              </p>
            </div>
            <p className="text-[11px] text-muted-foreground/60 mt-1">
              {timeAgo(activity.created_at)}
            </p>
          </div>
        </div>

        {/* Reaction bar */}
        <div className="flex items-center gap-1 mt-3 pt-3 border-t border-border/40">
          {REACTIONS.map((r) => {
            const count = activity.reaction_counts?.[r.type] || 0;
            const isActive = activity.user_reaction === r.type;
            return (
              <button
                key={r.type}
                onClick={() => handleReact(r.type)}
                disabled={reactingType !== null}
                className={`flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs transition-all duration-200 ${
                  isActive
                    ? "bg-primary/10 text-primary font-medium ring-1 ring-primary/20"
                    : "text-muted-foreground hover:bg-muted/50"
                }`}
                title={r.label}
              >
                <span className="text-sm">{r.emoji}</span>
                {count > 0 && <span className="tabular-nums">{count}</span>}
              </button>
            );
          })}

          <div className="flex-1" />

          {/* Comment toggle */}
          <button
            onClick={handleToggleComments}
            className={`flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs transition-colors ${
              showComments
                ? "bg-muted text-foreground"
                : "text-muted-foreground hover:bg-muted/50"
            }`}
          >
            <MessageCircle className="w-3.5 h-3.5" />
            {activity.comment_count > 0 && (
              <span className="tabular-nums">{activity.comment_count}</span>
            )}
          </button>
        </div>

        {/* Comments section */}
        {showComments && (
          <div className="mt-3 pt-2 border-t border-border/30 space-y-2.5">
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
                      className="font-medium text-xs text-foreground hover:underline"
                    >
                      {c.user_name}
                    </Link>
                    <span className="text-[10px] text-muted-foreground/60">
                      {timeAgo(c.created_at)}
                    </span>
                  </div>
                  <p className="text-xs text-foreground/80 mt-0.5 break-words">{c.content}</p>
                </div>
                {c.user_id === currentUserId && (
                  <button
                    onClick={() => handleDeleteComment(c.comment_id)}
                    className="opacity-0 group-hover:opacity-100 text-muted-foreground/40 hover:text-destructive transition-all p-1"
                    title="Supprimer"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                )}
              </div>
            ))}

            {/* Comment input */}
            <form onSubmit={handleSendComment} className="flex items-center gap-2">
              <Input
                value={commentText}
                onChange={(e) => setCommentText(e.target.value)}
                placeholder="Écrire un commentaire..."
                maxLength={500}
                className="h-8 text-xs rounded-lg"
              />
              <Button
                type="submit"
                size="icon"
                variant="ghost"
                className="h-8 w-8 shrink-0"
                disabled={!commentText.trim() || sendingComment}
              >
                {sendingComment ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Send className="w-3.5 h-3.5" />
                )}
              </Button>
            </form>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ── Quick links (kept from original, below the feed) ──
const quickLinks = [
  { to: "/search", icon: Search, title: "Rechercher des membres", color: "#459492" },
  { to: "/groups", icon: Users, title: "Mes groupes", color: "#459492" },
  { to: "/challenges", icon: Trophy, title: "Défis communautaires", color: "#E48C75" },
];

// ── Main Page ──
export default function CommunityFeedPage() {
  const { user } = useAuth();
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [cursor, setCursor] = useState(null);
  const [hasMore, setHasMore] = useState(false);
  const sentinelRef = useRef(null);

  const fetchFeed = useCallback(async (cursorVal = null) => {
    const isInitial = !cursorVal;
    if (isInitial) setLoading(true);
    else setLoadingMore(true);

    try {
      const url = cursorVal
        ? `${API}/feed?limit=15&cursor=${encodeURIComponent(cursorVal)}`
        : `${API}/feed?limit=15`;
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
      toast.error("Erreur lors du chargement du fil");
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, []);

  useEffect(() => {
    fetchFeed();
  }, [fetchFeed]);

  // Infinite scroll via IntersectionObserver
  useEffect(() => {
    if (!sentinelRef.current || !hasMore || loadingMore) return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !loadingMore && cursor) {
          fetchFeed(cursor);
        }
      },
      { threshold: 0.1 }
    );
    observer.observe(sentinelRef.current);
    return () => observer.disconnect();
  }, [hasMore, loadingMore, cursor, fetchFeed]);

  // Update local state after reaction toggle
  const handleReactionChange = (activityId, reactionType, serverData) => {
    setActivities((prev) =>
      prev.map((a) => {
        if (a.activity_id !== activityId) return a;
        const counts = { ...a.reaction_counts };
        if (serverData.reacted) {
          // If switching from another type, decrement old
          if (a.user_reaction && a.user_reaction !== reactionType) {
            counts[a.user_reaction] = Math.max(0, (counts[a.user_reaction] || 0) - 1);
          }
          // Only increment if we weren't already reacting with this type
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
        <div className="section-dark-header px-4 lg:px-8 pt-8 lg:pt-10 pb-8">
          <div className="max-w-3xl mx-auto">
            <h1 className="text-display text-3xl lg:text-4xl font-semibold text-white opacity-0 animate-fade-in">
              Communauté
            </h1>
            <p className="text-white/60 text-sm mt-1 opacity-0 animate-fade-in" style={{ animationDelay: "50ms" }}>
              Suivez la progression de vos amis
            </p>
          </div>
        </div>

        <div className="px-4 lg:px-8">
          <div className="max-w-3xl mx-auto">
            {/* Loading state */}
            {loading && (
              <div className="flex flex-col items-center justify-center py-16">
                <Loader2 className="w-6 h-6 text-primary animate-spin" />
                <p className="text-sm text-muted-foreground mt-3">Chargement du fil...</p>
              </div>
            )}

            {/* Empty state */}
            {!loading && activities.length === 0 && (
              <div className="opacity-0 animate-fade-in" style={{ animationFillMode: "forwards" }}>
                <div className="flex flex-col items-center justify-center py-12 text-center mb-8">
                  <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center mb-4 ring-1 ring-primary/10">
                    <Activity className="w-7 h-7 text-primary" />
                  </div>
                  <h2 className="text-base font-semibold text-foreground mb-1">
                    Votre fil est vide
                  </h2>
                  <p className="text-muted-foreground text-sm max-w-xs mb-4">
                    Suivez des utilisateurs pour voir leur activité ici. Complétez des sessions pour partager votre progression !
                  </p>
                  <Link to="/search">
                    <Button variant="outline" className="rounded-xl gap-2">
                      <Search className="w-4 h-4" />
                      Trouver des membres
                    </Button>
                  </Link>
                </div>

                {/* Quick links in empty state */}
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

            {/* Feed */}
            {!loading && activities.length > 0 && (
              <div className="space-y-3 opacity-0 animate-fade-in" style={{ animationFillMode: "forwards" }}>
                {activities.map((activity, i) => (
                  <div
                    key={activity.activity_id}
                    className={i < 15 ? "opacity-0 animate-fade-in" : ""}
                    style={i < 15 ? { animationDelay: `${100 + i * 40}ms`, animationFillMode: "forwards" } : undefined}
                  >
                    <ActivityCard
                      activity={activity}
                      currentUserId={user?.user_id}
                      onReactionChange={handleReactionChange}
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
