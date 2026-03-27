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
  Reply,
  ChevronDown,
  ChevronUp,
  Pencil,
  Check,
  X,
  Heart,
  ImagePlus,
  Bookmark,
  Hash,
  TrendingUp,
  Star,
  Share2,
  Pin,
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
import LinkPreviewCard from "@/components/LinkPreviewCard";
import { sanitize } from "@/lib/sanitize";

// ── Reaction config (InFinea DNA) ──
const REACTIONS = [
  { type: "bravo", emoji: "👏", label: "Bravo" },
  { type: "inspire", emoji: "💡", label: "Inspirant" },
  { type: "fire", emoji: "🔥", label: "En feu" },
  { type: "solidaire", emoji: "🤝", label: "Solidaire" },
  { type: "curieux", emoji: "🧠", label: "Curieux" },
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
  level_up: {
    icon: Star,
    color: "#F5A623",
    getText: (data) => `est passé au niveau ${data.new_level} — ${data.title || ""}`,
  },
  post: {
    icon: MessageCircle,
    color: "#55B3AE",
    getText: () => null, // Post content rendered separately (full text, not a one-liner)
    isPost: true,
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

// ── Suggestion reason label (LinkedIn/Instagram benchmark — context matters) ──
function SuggestionReason({ reason, detail }) {
  switch (reason) {
    case "mutual":
      return (
        <span className="text-[9px] text-primary/70 truncate">
          {detail} ami{detail > 1 ? "s" : ""} en commun
        </span>
      );
    case "follows_you":
      return <span className="text-[9px] text-emerald-600/80 truncate">Vous suit</span>;
    case "interacted":
      return (
        <span className="text-[9px] text-[#E48C75]/80 truncate">
          A interagi avec vous
        </span>
      );
    case "objectives":
      return (
        <span className="text-[9px] text-primary/70 truncate">
          {detail} objectif{detail > 1 ? "s" : ""} similaire{detail > 1 ? "s" : ""}
        </span>
      );
    case "same_goal":
      return <span className="text-[9px] text-primary/70 truncate">{detail}</span>;
    case "shared_interests":
      return (
        <span className="text-[9px] text-primary/70 truncate">
          Intérêts similaires
        </span>
      );
    case "group":
      return (
        <span className="text-[9px] text-primary/70 truncate">
          {detail} groupe{detail > 1 ? "s" : ""} en commun
        </span>
      );
    case "active":
      return <span className="text-[9px] text-muted-foreground/60 truncate">Actif récemment</span>;
    default:
      return null;
  }
}

// ── Suggested Users (horizontal scroll — Instagram stories style) ──
function SuggestedUsers({ currentUserId }) {
  const [users, setUsers] = useState([]);
  const [loaded, setLoaded] = useState(false);
  const [dismissed, setDismissed] = useState(new Set());

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

  const visibleUsers = users.filter((u) => !dismissed.has(u.user_id));

  if (!loaded || visibleUsers.length === 0) return null;

  return (
    <div className="mb-5 opacity-0 animate-fade-in" style={{ animationFillMode: "forwards" }}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <UserPlus className="w-4 h-4 text-primary" />
          <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
            Suggestions pour vous
          </span>
        </div>
        <Link to="/search" className="text-xs text-primary hover:underline">
          Voir tout
        </Link>
      </div>
      <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-thin snap-x snap-mandatory">
        {visibleUsers.map((u) => (
          <div
            key={u.user_id}
            className="relative flex flex-col items-center gap-1.5 min-w-[110px] max-w-[110px] snap-start bg-card/50 rounded-xl p-3 border border-border/30"
          >
            {/* Dismiss button */}
            <button
              onClick={() => setDismissed((prev) => new Set(prev).add(u.user_id))}
              className="absolute top-1 right-1 p-0.5 text-muted-foreground/30 hover:text-muted-foreground/60 transition-colors"
              title="Masquer"
            >
              <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 6 6 18M6 6l12 12"/></svg>
            </button>
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
              <SuggestionReason reason={u.reason} detail={u.reason_detail} />
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

// ── Post Image Grid (Instagram-style responsive grid + lightbox) ──
function PostImageGrid({ images }) {
  const [lightboxIdx, setLightboxIdx] = useState(null);

  if (!images || images.length === 0) return null;

  const gridClass =
    images.length === 1
      ? "grid-cols-1"
      : images.length === 2
        ? "grid-cols-2"
        : "grid-cols-2";

  return (
    <>
      <div className={`grid ${gridClass} gap-1 mt-2 rounded-lg overflow-hidden`}>
        {images.map((img, idx) => (
          <button
            key={idx}
            onClick={() => setLightboxIdx(idx)}
            className={`relative bg-muted/20 overflow-hidden ${
              images.length === 1 ? "aspect-video" :
              images.length === 3 && idx === 0 ? "row-span-2 aspect-auto h-full" :
              "aspect-square"
            }`}
          >
            <img
              src={images.length === 1 ? img.image_url : (img.thumbnail_url || img.image_url)}
              alt=""
              className="w-full h-full object-cover transition-transform hover:scale-[1.02]"
              loading="lazy"
            />
          </button>
        ))}
      </div>

      {/* Lightbox — full-screen image viewer */}
      {lightboxIdx !== null && (
        <div
          className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center"
          onClick={() => setLightboxIdx(null)}
        >
          <button
            className="absolute top-4 right-4 w-10 h-10 rounded-full bg-white/10 flex items-center justify-center hover:bg-white/20 transition-colors z-10"
            onClick={() => setLightboxIdx(null)}
          >
            <X className="w-5 h-5 text-white" />
          </button>

          {/* Nav arrows for multi-image */}
          {images.length > 1 && (
            <>
              {lightboxIdx > 0 && (
                <button
                  className="absolute left-4 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-white/10 flex items-center justify-center hover:bg-white/20 transition-colors z-10"
                  onClick={(e) => { e.stopPropagation(); setLightboxIdx(lightboxIdx - 1); }}
                >
                  <ChevronRight className="w-5 h-5 text-white rotate-180" />
                </button>
              )}
              {lightboxIdx < images.length - 1 && (
                <button
                  className="absolute right-4 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-white/10 flex items-center justify-center hover:bg-white/20 transition-colors z-10"
                  onClick={(e) => { e.stopPropagation(); setLightboxIdx(lightboxIdx + 1); }}
                >
                  <ChevronRight className="w-5 h-5 text-white" />
                </button>
              )}
              {/* Dots indicator */}
              <div className="absolute bottom-6 left-1/2 -translate-x-1/2 flex gap-1.5 z-10">
                {images.map((_, i) => (
                  <div
                    key={i}
                    className={`w-2 h-2 rounded-full transition-colors ${
                      i === lightboxIdx ? "bg-white" : "bg-white/30"
                    }`}
                  />
                ))}
              </div>
            </>
          )}

          <img
            src={images[lightboxIdx]?.image_url}
            alt=""
            className="max-w-[90vw] max-h-[85vh] object-contain rounded-lg"
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      )}
    </>
  );
}

// ── Single Activity Card (Instagram-style) ──
function ActivityCard({ activity, currentUserId, onReactionChange, onDelete, onPin, onBookmarkChange }) {
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
  const [bookmarking, setBookmarking] = useState(false);
  // Threading state
  const [replyingTo, setReplyingTo] = useState(null); // comment_id being replied to
  const [replyText, setReplyText] = useState("");
  const [replyMentions, setReplyMentions] = useState([]);
  const [sendingReply, setSendingReply] = useState(false);
  const [expandedReplies, setExpandedReplies] = useState({}); // { comment_id: [replies] }
  const [loadingReplies, setLoadingReplies] = useState({}); // { comment_id: bool }
  // Edit state (15-min window — Discord/Slack benchmark)
  const [editingCommentId, setEditingCommentId] = useState(null);
  const [editText, setEditText] = useState("");
  const [savingEdit, setSavingEdit] = useState(false);

  const totalReactions = Object.values(activity.reaction_counts || {}).reduce((sum, v) => sum + (v || 0), 0);

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

  const loadReplies = useCallback(async (parentId) => {
    setLoadingReplies((prev) => ({ ...prev, [parentId]: true }));
    try {
      const res = await authFetch(
        `${API}/activities/${activity.activity_id}/comments?parent_id=${parentId}`
      );
      if (res.ok) {
        const data = await res.json();
        setExpandedReplies((prev) => ({ ...prev, [parentId]: data.comments || [] }));
      }
    } catch { /* silent */ }
    setLoadingReplies((prev) => ({ ...prev, [parentId]: false }));
  }, [activity.activity_id]);

  const toggleReplies = (parentId) => {
    if (expandedReplies[parentId]) {
      setExpandedReplies((prev) => {
        const next = { ...prev };
        delete next[parentId];
        return next;
      });
    } else {
      loadReplies(parentId);
    }
  };

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

  const handleShare = async () => {
    const url = `${window.location.origin}/community`;
    const text = activity.type === "post"
      ? activity.content?.slice(0, 100) || "Découvre InFinea"
      : `${activity.user_name || "Quelqu'un"} ${ACTIVITY_CONFIG[activity.type]?.getText(activity.data || {}) || "progresse sur InFinea"}`;
    // Native share on mobile, clipboard on desktop
    if (navigator.share) {
      try {
        await navigator.share({ title: "InFinea", text, url });
      } catch { /* cancelled */ }
    } else {
      try {
        await navigator.clipboard.writeText(`${text} — ${url}`);
        toast.success("Lien copié !");
      } catch {
        toast.error("Impossible de copier");
      }
    }
  };

  const handleBookmark = async () => {
    setBookmarking(true);
    try {
      const res = await authFetch(`${API}/activities/${activity.activity_id}/bookmark`, {
        method: "POST",
      });
      if (res.ok) {
        const data = await res.json();
        onBookmarkChange?.(activity.activity_id, data.bookmarked);
        toast.success(data.bookmarked ? "Sauvegardé" : "Retiré des sauvegardés");
      }
    } catch {
      toast.error("Erreur");
    } finally {
      setBookmarking(false);
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

  const handleSendReply = async (e, parentId) => {
    if (e && e.preventDefault) e.preventDefault();
    const text = replyText.trim();
    if (!text) return;
    setSendingReply(true);
    try {
      const res = await authFetch(`${API}/activities/${activity.activity_id}/comments`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: text, parent_id: parentId }),
      });
      if (res.ok) {
        const newReply = await res.json();
        // Add reply to expanded replies (or create the list)
        setExpandedReplies((prev) => ({
          ...prev,
          [parentId]: [...(prev[parentId] || []), newReply],
        }));
        // Increment reply_count on parent
        setComments((prev) =>
          prev.map((c) =>
            c.comment_id === parentId
              ? { ...c, reply_count: (c.reply_count || 0) + 1 }
              : c
          )
        );
        setReplyText("");
        setReplyMentions([]);
        setReplyingTo(null);
      } else {
        toast.error("Erreur lors de l'envoi");
      }
    } catch {
      toast.error("Erreur de connexion");
    } finally {
      setSendingReply(false);
    }
  };

  const handleDeleteComment = async (commentId, parentId = null) => {
    try {
      const res = await authFetch(`${API}/comments/${commentId}`, { method: "DELETE" });
      if (res.ok) {
        if (parentId) {
          // Deleting a reply — remove from expanded replies + decrement parent count
          setExpandedReplies((prev) => ({
            ...prev,
            [parentId]: (prev[parentId] || []).filter((c) => c.comment_id !== commentId),
          }));
          setComments((prev) =>
            prev.map((c) =>
              c.comment_id === parentId
                ? { ...c, reply_count: Math.max(0, (c.reply_count || 0) - 1) }
                : c
            )
          );
        } else {
          // Deleting a top-level comment — remove from list + clear expanded replies
          setComments((prev) => prev.filter((c) => c.comment_id !== commentId));
          setExpandedReplies((prev) => {
            const next = { ...prev };
            delete next[commentId];
            return next;
          });
        }
      }
    } catch { /* silent */ }
  };

  // ── Edit comment (15-min window) ──
  const canEdit = (createdAt) => {
    const created = new Date(createdAt);
    return (Date.now() - created.getTime()) < 15 * 60 * 1000;
  };

  const startEdit = (comment) => {
    setEditingCommentId(comment.comment_id);
    setEditText(comment.content);
  };

  const cancelEdit = () => {
    setEditingCommentId(null);
    setEditText("");
  };

  const handleSaveEdit = async (commentId, parentId = null) => {
    if (!editText.trim() || savingEdit) return;
    setSavingEdit(true);
    try {
      const res = await authFetch(`${API}/comments/${commentId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: editText.trim() }),
      });
      if (res.ok) {
        const data = await res.json();
        const updater = (c) =>
          c.comment_id === commentId
            ? { ...c, content: data.content, mentions: data.mentions, edited_at: data.edited_at }
            : c;
        if (parentId) {
          setExpandedReplies((prev) => ({
            ...prev,
            [parentId]: (prev[parentId] || []).map(updater),
          }));
        } else {
          setComments((prev) => prev.map(updater));
        }
        cancelEdit();
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || "Impossible de modifier");
      }
    } catch {
      toast.error("Erreur de connexion");
    } finally {
      setSavingEdit(false);
    }
  };

  // ── Like comment (Instagram benchmark — heart toggle) ──
  const handleLikeComment = async (commentId, parentId = null) => {
    try {
      const res = await authFetch(`${API}/comments/${commentId}/like`, { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        const updater = (c) =>
          c.comment_id === commentId
            ? { ...c, like_count: data.like_count, liked_by_me: data.liked }
            : c;
        if (parentId) {
          setExpandedReplies((prev) => ({
            ...prev,
            [parentId]: (prev[parentId] || []).map(updater),
          }));
        } else {
          setComments((prev) => prev.map(updater));
        }
      }
    } catch { /* silent */ }
  };

  return (
    <Card className="overflow-hidden hover:shadow-md transition-shadow duration-300">
      <CardContent className="p-4">
        {/* Header: avatar + name + time */}
        <div className="flex items-start gap-3">
          <Link to={`/users/${activity.user_id}`} className="relative shrink-0">
            <Avatar className="w-10 h-10 ring-2 ring-primary/10 ring-offset-1 ring-offset-background">
              <AvatarImage src={activity.user_avatar} alt={activity.user_name} />
              <AvatarFallback className="bg-primary/10 text-primary text-xs">
                {getInitials(activity.user_name)}
              </AvatarFallback>
            </Avatar>
            {activity.user_presence === "online" && (
              <span
                className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full ring-2 ring-background"
                style={{ backgroundColor: "#22c55e" }}
              />
            )}
            {activity.user_level > 1 && (
              <span
                className="absolute -bottom-0.5 -right-0.5 w-4.5 h-4.5 rounded-full flex items-center justify-center text-[8px] font-bold text-white ring-2 ring-background"
                style={{ backgroundColor: "#459492", minWidth: "18px", height: "18px" }}
              >
                {activity.user_level}
              </span>
            )}
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
                <div className="flex items-center gap-0.5">
                  <button
                    onClick={() => onPin?.(activity.activity_id, !activity.pinned)}
                    className={`transition-colors p-1 ${activity.pinned ? "text-primary" : "text-muted-foreground/40 hover:text-primary"}`}
                    title={activity.pinned ? "Désépingler" : "Épingler sur le profil"}
                  >
                    <Pin className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => {
                      if (window.confirm("Supprimer cette activité ?")) onDelete?.(activity.activity_id);
                    }}
                    className="text-muted-foreground/40 hover:text-destructive transition-colors p-1"
                    title="Supprimer"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
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
            {config.isPost ? (
              /* Manual post: text + optional images (Instagram pattern) */
              <div className="mt-2">
                {activity.data?.content && (
                  <p className="text-sm text-foreground/90 whitespace-pre-wrap break-words leading-relaxed">
                    <MentionText
                      content={activity.data.content}
                      mentions={activity.data?.mentions || []}
                      currentUserId={currentUserId}
                    />
                  </p>
                )}
                {/* Post images grid */}
                {activity.data?.images?.length > 0 && (
                  <PostImageGrid images={activity.data.images} />
                )}
                {/* Link preview OG card (Slack/Discord pattern) */}
                {activity.data?.link_preview && (
                  <LinkPreviewCard preview={activity.data.link_preview} />
                )}
              </div>
            ) : (
              <div className="flex items-center gap-1.5 mt-1">
                <div
                  className="w-5 h-5 rounded-md flex items-center justify-center"
                  style={{ backgroundColor: `${config.color}15` }}
                >
                  <Icon className="w-3 h-3" style={{ color: config.color }} />
                </div>
                <p className="text-sm text-foreground/80 flex-1">
                  {config.getText(activity.data || {})}
                </p>
                {activity.data?.xp_awarded > 0 && (
                  <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-md bg-[#F5A623]/10 text-[#F5A623] text-[10px] font-bold shrink-0 tabular-nums">
                    <Star className="w-2.5 h-2.5" fill="#F5A623" />
                    +{activity.data.xp_awarded}
                  </span>
                )}
              </div>
            )}
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

          {/* Share — viral loop */}
          <button
            onClick={handleShare}
            className="flex items-center gap-1 px-2 py-1.5 rounded-full text-xs text-muted-foreground hover:text-foreground hover:bg-muted/60 transition-all duration-200"
            title="Partager"
          >
            <Share2 className="w-3.5 h-3.5" />
          </button>

          {/* Bookmark — Instagram Saved */}
          <button
            onClick={handleBookmark}
            disabled={bookmarking}
            className={`flex items-center gap-1 px-2 py-1.5 rounded-full text-xs transition-all duration-200 ${
              activity.bookmarked
                ? "text-primary"
                : "text-muted-foreground hover:text-foreground hover:bg-muted/60"
            }`}
            title={activity.bookmarked ? "Retirer des sauvegardés" : "Sauvegarder"}
          >
            <Bookmark className="w-3.5 h-3.5" fill={activity.bookmarked ? "currentColor" : "none"} />
          </button>

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

        {/* Comments section — expandable, threaded (Instagram/YouTube pattern) */}
        {showComments && (
          <div className="mt-3 pt-2 border-t border-border/30 space-y-2.5 animate-fade-in" style={{ animationFillMode: "forwards" }}>
            {comments.length === 0 && commentsLoaded && (
              <p className="text-xs text-muted-foreground/50 text-center py-2">
                Aucun commentaire — soyez le premier !
              </p>
            )}

            {comments.map((c) => (
              <div key={c.comment_id}>
                {/* Top-level comment */}
                <div className="flex items-start gap-2 group">
                  <Link to={`/users/${c.user_id}`}>
                    <Avatar className="w-6 h-6 shrink-0">
                      <AvatarImage src={c.user_avatar} />
                      <AvatarFallback className="bg-muted text-[9px]">
                        {getInitials(c.user_name)}
                      </AvatarFallback>
                    </Avatar>
                  </Link>
                  <div className="flex-1 min-w-0">
                    {editingCommentId === c.comment_id ? (
                      /* ── Inline edit mode ── */
                      <div className="flex items-center gap-1.5">
                        <input
                          value={editText}
                          onChange={(e) => setEditText(e.target.value)}
                          maxLength={500}
                          className="flex-1 h-7 text-xs rounded-md border border-primary/30 bg-primary/[0.03] px-2 focus:outline-none focus:ring-1 focus:ring-primary/40"
                          autoFocus
                          onKeyDown={(e) => {
                            if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSaveEdit(c.comment_id); }
                            if (e.key === "Escape") cancelEdit();
                          }}
                        />
                        <button onClick={() => handleSaveEdit(c.comment_id)} disabled={savingEdit || !editText.trim()} className="p-1 text-primary hover:text-primary/80 transition-colors" title="Enregistrer">
                          {savingEdit ? <Loader2 className="w-3 h-3 animate-spin" /> : <Check className="w-3 h-3" />}
                        </button>
                        <button onClick={cancelEdit} className="p-1 text-muted-foreground/50 hover:text-muted-foreground transition-colors" title="Annuler">
                          <X className="w-3 h-3" />
                        </button>
                      </div>
                    ) : (
                      <>
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
                        <div className="flex items-center gap-3 mt-0.5">
                          <span className="text-[10px] text-muted-foreground/50">
                            {timeAgo(c.created_at)}
                            {c.edited_at && <span className="ml-1 italic">(modifié)</span>}
                          </span>
                          <button
                            onClick={() => {
                              if (replyingTo === c.comment_id) {
                                setReplyingTo(null);
                                setReplyText("");
                              } else {
                                setReplyingTo(c.comment_id);
                                const username = c.user_username || c.user_name;
                                setReplyText(c.user_id !== currentUserId ? `@${username} ` : "");
                              }
                            }}
                            className="text-[10px] font-medium text-muted-foreground hover:text-primary transition-colors"
                          >
                            Répondre
                          </button>
                          <button
                            onClick={() => handleLikeComment(c.comment_id)}
                            className={`flex items-center gap-0.5 text-[10px] transition-colors ${
                              c.liked_by_me ? "text-[#E48C75] font-medium" : "text-muted-foreground hover:text-[#E48C75]"
                            }`}
                          >
                            <Heart className={`w-3 h-3 ${c.liked_by_me ? "fill-current" : ""}`} />
                            {(c.like_count || 0) > 0 && <span className="tabular-nums">{c.like_count}</span>}
                          </button>
                        </div>
                      </>
                    )}
                  </div>
                  {c.user_id === currentUserId ? (
                    <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-all">
                      {canEdit(c.created_at) && editingCommentId !== c.comment_id && (
                        <button
                          onClick={() => startEdit(c)}
                          className="text-muted-foreground/40 hover:text-primary transition-all p-1"
                          title="Modifier"
                        >
                          <Pencil className="w-3 h-3" />
                        </button>
                      )}
                      <button
                        onClick={() => handleDeleteComment(c.comment_id)}
                        className="text-muted-foreground/40 hover:text-destructive transition-all p-1"
                        title="Supprimer"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
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

                {/* View replies toggle */}
                {(c.reply_count || 0) > 0 && (
                  <button
                    onClick={() => toggleReplies(c.comment_id)}
                    disabled={loadingReplies[c.comment_id]}
                    className="ml-8 mt-1 flex items-center gap-1 text-[10px] font-medium text-primary/70 hover:text-primary transition-colors"
                  >
                    {loadingReplies[c.comment_id] ? (
                      <Loader2 className="w-3 h-3 animate-spin" />
                    ) : expandedReplies[c.comment_id] ? (
                      <ChevronUp className="w-3 h-3" />
                    ) : (
                      <ChevronDown className="w-3 h-3" />
                    )}
                    {expandedReplies[c.comment_id]
                      ? "Masquer les réponses"
                      : `Voir ${c.reply_count} réponse${c.reply_count > 1 ? "s" : ""}`}
                  </button>
                )}

                {/* Expanded replies */}
                {expandedReplies[c.comment_id] && (
                  <div className="ml-8 mt-1.5 pl-3 border-l-2 border-primary/10 space-y-2">
                    {expandedReplies[c.comment_id].map((reply) => (
                      <div key={reply.comment_id} className="flex items-start gap-2 group">
                        <Link to={`/users/${reply.user_id}`}>
                          <Avatar className="w-5 h-5 shrink-0">
                            <AvatarImage src={reply.user_avatar} />
                            <AvatarFallback className="bg-muted text-[8px]">
                              {getInitials(reply.user_name)}
                            </AvatarFallback>
                          </Avatar>
                        </Link>
                        <div className="flex-1 min-w-0">
                          {editingCommentId === reply.comment_id ? (
                            <div className="flex items-center gap-1.5">
                              <input
                                value={editText}
                                onChange={(e) => setEditText(e.target.value)}
                                maxLength={500}
                                className="flex-1 h-6 text-[11px] rounded-md border border-primary/30 bg-primary/[0.03] px-2 focus:outline-none focus:ring-1 focus:ring-primary/40"
                                autoFocus
                                onKeyDown={(e) => {
                                  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSaveEdit(reply.comment_id, c.comment_id); }
                                  if (e.key === "Escape") cancelEdit();
                                }}
                              />
                              <button onClick={() => handleSaveEdit(reply.comment_id, c.comment_id)} disabled={savingEdit || !editText.trim()} className="p-1 text-primary hover:text-primary/80 transition-colors" title="Enregistrer">
                                {savingEdit ? <Loader2 className="w-3 h-3 animate-spin" /> : <Check className="w-3 h-3" />}
                              </button>
                              <button onClick={cancelEdit} className="p-1 text-muted-foreground/50 hover:text-muted-foreground transition-colors" title="Annuler">
                                <X className="w-3 h-3" />
                              </button>
                            </div>
                          ) : (
                            <>
                              <div className="flex items-baseline gap-1.5">
                                <Link
                                  to={`/users/${reply.user_id}`}
                                  className="font-semibold text-[11px] text-foreground hover:underline"
                                >
                                  {reply.user_name}
                                </Link>
                                <MentionText
                                  content={reply.content}
                                  mentions={reply.mentions}
                                  currentUserId={currentUserId}
                                  className="text-[11px] text-foreground/70 break-words"
                                />
                              </div>
                              <div className="flex items-center gap-3 mt-0.5">
                                <span className="text-[10px] text-muted-foreground/50">
                                  {timeAgo(reply.created_at)}
                                  {reply.edited_at && <span className="ml-1 italic">(modifié)</span>}
                                </span>
                                <button
                                  onClick={() => {
                                    setReplyingTo(c.comment_id);
                                    const username = reply.user_username || reply.user_name;
                                    setReplyText(reply.user_id !== currentUserId ? `@${username} ` : "");
                                  }}
                                  className="text-[10px] font-medium text-muted-foreground hover:text-primary transition-colors"
                                >
                                  Répondre
                                </button>
                                <button
                                  onClick={() => handleLikeComment(reply.comment_id, c.comment_id)}
                                  className={`flex items-center gap-0.5 text-[10px] transition-colors ${
                                    reply.liked_by_me ? "text-[#E48C75] font-medium" : "text-muted-foreground hover:text-[#E48C75]"
                                  }`}
                                >
                                  <Heart className={`w-3 h-3 ${reply.liked_by_me ? "fill-current" : ""}`} />
                                  {(reply.like_count || 0) > 0 && <span className="tabular-nums">{reply.like_count}</span>}
                                </button>
                              </div>
                            </>
                          )}
                        </div>
                        {reply.user_id === currentUserId ? (
                          <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-all">
                            {canEdit(reply.created_at) && editingCommentId !== reply.comment_id && (
                              <button
                                onClick={() => startEdit(reply)}
                                className="text-muted-foreground/40 hover:text-primary transition-all p-1"
                                title="Modifier"
                              >
                                <Pencil className="w-3 h-3" />
                              </button>
                            )}
                            <button
                              onClick={() => handleDeleteComment(reply.comment_id, c.comment_id)}
                              className="text-muted-foreground/40 hover:text-destructive transition-all p-1"
                              title="Supprimer"
                            >
                              <Trash2 className="w-3 h-3" />
                            </button>
                          </div>
                        ) : (
                          <button
                            onClick={() => setReportCommentId(reply.comment_id)}
                            className="opacity-0 group-hover:opacity-100 text-muted-foreground/40 hover:text-destructive transition-all p-1"
                            title="Signaler"
                          >
                            <Flag className="w-3 h-3" />
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {/* Reply input — inline, shown when replying to this comment */}
                {replyingTo === c.comment_id && (
                  <form
                    onSubmit={(e) => handleSendReply(e, c.comment_id)}
                    className="ml-8 mt-2 flex items-center gap-2 animate-fade-in"
                    style={{ animationFillMode: "forwards" }}
                  >
                    <Reply className="w-3 h-3 text-primary/40 shrink-0" />
                    <MentionInput
                      value={replyText}
                      onChange={setReplyText}
                      mentions={replyMentions}
                      onMentionsChange={setReplyMentions}
                      context="comment"
                      contextId={activity.activity_id}
                      placeholder={`Répondre à ${c.user_name}...`}
                      maxLength={500}
                      className="h-7 text-[11px] rounded-full border-primary/20 bg-primary/[0.03] focus:bg-white"
                      onSubmit={(e) => handleSendReply(e, c.comment_id)}
                      autoFocus
                    />
                    <Button
                      type="submit"
                      size="icon"
                      variant="ghost"
                      className="h-7 w-7 shrink-0 rounded-full"
                      disabled={!replyText.trim() || sendingReply}
                    >
                      {sendingReply ? (
                        <Loader2 className="w-3 h-3 animate-spin" />
                      ) : (
                        <Send className="w-3 h-3 text-primary" />
                      )}
                    </Button>
                    <button
                      type="button"
                      onClick={() => { setReplyingTo(null); setReplyText(""); }}
                      className="text-muted-foreground/40 hover:text-muted-foreground p-1 transition-colors"
                    >
                      <span className="text-[10px]">Annuler</span>
                    </button>
                  </form>
                )}
              </div>
            ))}

            {/* Comment input — top-level, with @mention autocomplete */}
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
  { to: "/saved", icon: Bookmark, title: "Mes sauvegardés", color: "#459492" },
];

// ── Trending Hashtags (Twitter/X trending pattern — discover tab) ──
function TrendingHashtags() {
  const [trending, setTrending] = useState([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await authFetch(`${API}/hashtags/trending?limit=12`);
        if (res.ok && !cancelled) {
          const data = await res.json();
          setTrending(data.trending || []);
        }
      } catch { /* silent */ }
      if (!cancelled) setLoaded(true);
    })();
    return () => { cancelled = true; };
  }, []);

  if (!loaded || trending.length === 0) return null;

  return (
    <div className="mb-4 opacity-0 animate-fade-in" style={{ animationFillMode: "forwards", animationDelay: "80ms" }}>
      <div className="flex items-center gap-1.5 mb-2">
        <TrendingUp className="w-3.5 h-3.5 text-[#459492]" />
        <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
          Tendances
        </span>
      </div>
      <div className="flex flex-wrap gap-1.5">
        {trending.map((t) => (
          <Link
            key={t.tag}
            to={`/hashtags/${encodeURIComponent(t.tag)}`}
            className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-[#459492]/8 hover:bg-[#459492]/15 text-xs font-medium text-[#459492] transition-colors"
          >
            <Hash className="w-3 h-3" />
            {t.tag}
            <span className="text-[10px] text-muted-foreground/60 ml-0.5">{t.user_count}</span>
          </Link>
        ))}
      </div>
      <Link
        to="/trending"
        className="inline-flex items-center gap-1 mt-2 text-[11px] text-[#459492] hover:text-[#275255] font-medium transition-colors"
      >
        Voir toutes les tendances
        <ChevronRight className="w-3 h-3" />
      </Link>
    </div>
  );
}

// ── Main Page ──
// ── Post Composer (LinkedIn/Strava benchmark — "What's on your mind?") ──
function PostComposer({ user, onPost }) {
  const [expanded, setExpanded] = useState(false);
  const [text, setText] = useState("");
  const [images, setImages] = useState([]); // [{image_url, thumbnail_url, width, height, uploading?, file?}]
  const [posting, setPosting] = useState(false);
  const fileInputRef = useRef(null);

  const canSubmit =
    !posting &&
    !images.some((img) => img.uploading) &&
    (text.trim().length >= 3 || images.filter((i) => !i.uploading).length > 0);

  const handleImageSelect = async (e) => {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;
    e.target.value = ""; // reset input

    const remaining = 4 - images.length;
    if (remaining <= 0) {
      toast.error("Maximum 4 images par post");
      return;
    }

    const toUpload = files.slice(0, remaining);
    for (const file of toUpload) {
      if (!file.type.startsWith("image/")) {
        toast.error(`${file.name} n'est pas une image`);
        continue;
      }
      if (file.size > 10 * 1024 * 1024) {
        toast.error(`${file.name} dépasse 10 Mo`);
        continue;
      }

      // Add placeholder with local preview
      const localUrl = URL.createObjectURL(file);
      const tempId = `tmp_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`;
      setImages((prev) => [...prev, { tempId, thumbnail_url: localUrl, uploading: true }]);

      // Upload to server
      const formData = new FormData();
      formData.append("file", file);
      try {
        const res = await authFetch(`${API}/feed/upload-image`, {
          method: "POST",
          body: formData,
        });
        if (res.ok) {
          const data = await res.json();
          setImages((prev) =>
            prev.map((img) =>
              img.tempId === tempId
                ? { ...data, tempId, uploading: false }
                : img
            )
          );
        } else {
          const err = await res.json().catch(() => ({}));
          toast.error(err.detail || "Erreur d'upload");
          setImages((prev) => prev.filter((img) => img.tempId !== tempId));
        }
      } catch {
        toast.error("Erreur de connexion pendant l'upload");
        setImages((prev) => prev.filter((img) => img.tempId !== tempId));
      } finally {
        URL.revokeObjectURL(localUrl);
      }
    }
  };

  const removeImage = (tempId) => {
    setImages((prev) => prev.filter((img) => img.tempId !== tempId));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!canSubmit) return;
    setPosting(true);
    const uploadedImages = images
      .filter((i) => !i.uploading && i.image_url)
      .map(({ image_url, thumbnail_url, width, height }) => ({
        image_url, thumbnail_url, width, height,
      }));
    const ok = await onPost(text.trim(), uploadedImages);
    if (ok) {
      setText("");
      setImages([]);
      setExpanded(false);
    }
    setPosting(false);
  };

  const handleCancel = () => {
    setExpanded(false);
    setText("");
    setImages([]);
  };

  // Image preview grid: 1 image full width, 2 side by side, 3-4 grid
  const imageGrid = images.length === 1
    ? "grid-cols-1"
    : images.length === 2
      ? "grid-cols-2"
      : "grid-cols-2";

  return (
    <Card className="mb-4 opacity-0 animate-fade-in" style={{ animationFillMode: "forwards" }}>
      <CardContent className="p-3">
        {!expanded ? (
          <button
            onClick={() => setExpanded(true)}
            className="w-full flex items-center gap-3 text-left"
          >
            <Avatar className="w-9 h-9 shrink-0">
              <AvatarImage src={user?.avatar_url || user?.picture} />
              <AvatarFallback className="bg-primary/10 text-primary text-xs">
                {getInitials(user?.display_name || user?.name)}
              </AvatarFallback>
            </Avatar>
            <span className="text-sm text-muted-foreground/60 flex-1">
              Partagez une réflexion, un progrès, une question...
            </span>
            <ImagePlus className="w-4 h-4 text-primary/30 mr-1" />
            <Send className="w-4 h-4 text-primary/30" />
          </button>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="flex items-start gap-3">
              <Avatar className="w-9 h-9 shrink-0 mt-1">
                <AvatarImage src={user?.avatar_url || user?.picture} />
                <AvatarFallback className="bg-primary/10 text-primary text-xs">
                  {getInitials(user?.display_name || user?.name)}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1">
                <textarea
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder="Qu'avez-vous appris aujourd'hui ? Un défi à partager ?"
                  maxLength={2000}
                  rows={3}
                  className="w-full text-sm resize-none rounded-lg border border-border/50 bg-muted/30 p-2.5 focus:outline-none focus:ring-1 focus:ring-primary/30 focus:bg-background placeholder:text-muted-foreground/40"
                  autoFocus
                />

                {/* Image preview grid */}
                {images.length > 0 && (
                  <div className={`grid ${imageGrid} gap-1.5 mt-2 rounded-lg overflow-hidden`}>
                    {images.map((img) => (
                      <div
                        key={img.tempId}
                        className={`relative bg-muted/30 ${images.length === 1 ? "aspect-video" : "aspect-square"}`}
                      >
                        <img
                          src={img.thumbnail_url || img.image_url}
                          alt=""
                          className="w-full h-full object-cover"
                        />
                        {img.uploading && (
                          <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
                            <Loader2 className="w-5 h-5 text-white animate-spin" />
                          </div>
                        )}
                        <button
                          type="button"
                          onClick={() => removeImage(img.tempId)}
                          className="absolute top-1 right-1 w-6 h-6 rounded-full bg-black/60 flex items-center justify-center hover:bg-black/80 transition-colors"
                        >
                          <X className="w-3.5 h-3.5 text-white" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}

                <div className="flex items-center justify-between mt-2">
                  <div className="flex items-center gap-2">
                    {/* Image upload button */}
                    <button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      disabled={images.length >= 4}
                      className="flex items-center gap-1 text-xs text-muted-foreground/60 hover:text-primary transition-colors disabled:opacity-30"
                    >
                      <ImagePlus className="w-4 h-4" />
                      <span className="hidden sm:inline">{images.length > 0 ? `${images.length}/4` : "Photo"}</span>
                    </button>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/jpeg,image/png,image/webp,image/gif"
                      multiple
                      onChange={handleImageSelect}
                      className="hidden"
                    />
                    <span className="text-[10px] text-muted-foreground/40">
                      {text.length}/2000
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="text-xs h-7"
                      onClick={handleCancel}
                    >
                      Annuler
                    </Button>
                    <Button
                      type="submit"
                      size="sm"
                      className="text-xs h-7 gap-1.5 bg-[#459492] hover:bg-[#3a7d7b]"
                      disabled={!canSubmit}
                    >
                      {posting ? <Loader2 className="w-3 h-3 animate-spin" /> : <Send className="w-3 h-3" />}
                      Publier
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </form>
        )}
      </CardContent>
    </Card>
  );
}

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

  // ── Real-time "new posts" polling ──
  const [newPostCount, setNewPostCount] = useState(0);
  const feedLoadedAtRef = useRef(null);

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
        // Mark when the feed was last loaded (for new-posts polling)
        if (isInitial && feedTab === "feed") {
          feedLoadedAtRef.current = new Date().toISOString();
          setNewPostCount(0);
        }
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

  // ── New posts polling (30s interval, feed tab only) ──
  useEffect(() => {
    if (tab !== "feed") {
      setNewPostCount(0);
      return;
    }
    const poll = async () => {
      if (!feedLoadedAtRef.current) return;
      try {
        const res = await authFetch(
          `${API}/feed/new-count?since=${encodeURIComponent(feedLoadedAtRef.current)}`
        );
        if (res.ok) {
          const data = await res.json();
          setNewPostCount(data.new_count || 0);
        }
      } catch {
        // Silent — polling failure is non-critical
      }
    };
    const id = setInterval(poll, 30_000);
    return () => clearInterval(id);
  }, [tab]);

  // Show new posts: refresh feed and scroll to top
  const handleShowNewPosts = useCallback(() => {
    setNewPostCount(0);
    setActivities([]);
    setCursor(null);
    setHasMore(false);
    fetchFeed(null, "feed");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, [fetchFeed]);

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

  // Pin/unpin own activity
  const handlePinActivity = async (activityId, pin) => {
    try {
      const res = await authFetch(`${API}/activities/${activityId}/pin`, {
        method: pin ? "POST" : "DELETE",
      });
      if (res.ok) {
        setActivities((prev) =>
          prev.map((a) =>
            a.activity_id === activityId ? { ...a, pinned: pin } : a
          )
        );
        toast.success(pin ? "Activité épinglée sur ton profil" : "Activité désépinglée");
      } else {
        const data = await res.json().catch(() => ({}));
        toast.error(data.detail || "Erreur");
      }
    } catch {
      toast.error("Erreur de connexion");
    }
  };

  // Create manual post
  const handleCreatePost = async (content, images = []) => {
    try {
      const payload = { content };
      if (images.length > 0) payload.images = images;
      const res = await authFetch(`${API}/activities`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        const newActivity = await res.json();
        setActivities((prev) => [newActivity, ...prev]);
        toast.success("Post publié !");
        return true;
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || "Impossible de publier");
        return false;
      }
    } catch {
      toast.error("Erreur de connexion");
      return false;
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

  // Bookmark toggle — update local state
  const handleBookmarkChange = (activityId, bookmarked) => {
    setActivities((prev) =>
      prev.map((a) =>
        a.activity_id === activityId ? { ...a, bookmarked } : a
      )
    );
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
            {/* Post composer — feed tab only */}
            {tab === "feed" && <PostComposer user={user} onPost={handleCreatePost} />}

            {/* "New posts" banner — appears when polling detects new content */}
            {tab === "feed" && newPostCount > 0 && (
              <button
                onClick={handleShowNewPosts}
                className="w-full flex items-center justify-center gap-2 py-2.5 mb-4 rounded-xl
                  bg-gradient-to-r from-[#459492] to-[#55B3AE] text-white text-sm font-medium
                  shadow-md hover:shadow-lg transition-shadow duration-200
                  animate-in slide-in-from-top-2 fade-in"
              >
                <RefreshCw className="w-4 h-4" />
                {newPostCount === 1
                  ? "1 nouveau post"
                  : `${newPostCount} nouveaux posts`}
                <span className="text-white/70">— Voir</span>
              </button>
            )}

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

            {/* Trending hashtags — discover tab only */}
            {tab === "discover" && <TrendingHashtags />}

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
                      onBookmarkChange={handleBookmarkChange}
                      onDelete={handleDeleteActivity}
                      onPin={handlePinActivity}
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
