/**
 * ActivityDetailPage — Permalink page for a single activity.
 *
 * Pattern: Instagram post detail, Twitter/X tweet page.
 * Shows full activity with author info, reactions, all comments (threaded),
 * comment input, bookmarks. Used as notification deep link target.
 *
 * Route: /activity/:activityId
 */

import React, { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  ArrowLeft, Zap, Award, Flame, Trophy, MessageCircle, Loader2,
  Bookmark, Send, Heart, Reply, ChevronDown, ChevronUp, Pencil,
  Check, X, Trash2, Hash,
} from "lucide-react";
import { toast } from "sonner";
import Sidebar from "@/components/Sidebar";
import SafetyMenu from "@/components/SafetyMenu";
import FollowButton from "@/components/FollowButton";
import MentionInput from "@/components/MentionInput";
import MentionText from "@/components/MentionText";
import LinkPreviewCard from "@/components/LinkPreviewCard";
import ReactionsDetailDialog from "@/components/ReactionsDetailDialog";
import ReportDialog from "@/components/ReportDialog";
import { API, authFetch, useAuth } from "@/App";

// ── Configs (same as CommunityFeedPage for consistency) ──
const REACTIONS = [
  { type: "bravo", emoji: "👏", label: "Bravo" },
  { type: "inspire", emoji: "💡", label: "Inspirant" },
  { type: "fire", emoji: "🔥", label: "En feu" },
  { type: "solidaire", emoji: "🤝", label: "Solidaire" },
  { type: "curieux", emoji: "🧠", label: "Curieux" },
];

const ACTIVITY_CONFIG = {
  session_completed: { icon: Zap, color: "#459492", getText: (d) => `a terminé "${d.action_title || "une micro-action"}" en ${d.duration || 0} min` },
  badge_earned: { icon: Award, color: "#E48C75", getText: (d) => `a obtenu le badge "${d.badge_name || "nouveau badge"}"` },
  streak_milestone: { icon: Flame, color: "#E48C75", getText: (d) => `a atteint ${d.streak_days} jours de streak !` },
  challenge_completed: { icon: Trophy, color: "#459492", getText: (d) => `a complété le défi "${d.challenge_title || "un défi"}" !` },
  post: { icon: MessageCircle, color: "#55B3AE", isPost: true },
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

/* ── Image grid ── */
function PostImageGrid({ images }) {
  const [lightboxIdx, setLightboxIdx] = useState(null);
  if (!images?.length) return null;
  const gridClass = images.length === 1 ? "grid-cols-1" : "grid-cols-2";
  return (
    <>
      <div className={`grid ${gridClass} gap-1 mt-3 rounded-xl overflow-hidden`}>
        {images.slice(0, 4).map((img, i) => (
          <img
            key={i}
            src={img.thumbnail_url || img.image_url}
            alt=""
            className="w-full aspect-square object-cover cursor-pointer hover:opacity-90 transition-opacity"
            loading="lazy"
            onClick={() => setLightboxIdx(i)}
          />
        ))}
      </div>
      {lightboxIdx !== null && (
        <div className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center" onClick={() => setLightboxIdx(null)}>
          <img src={images[lightboxIdx].image_url} alt="" className="max-w-[90vw] max-h-[90vh] object-contain rounded-lg" onClick={(e) => e.stopPropagation()} />
          <button onClick={() => setLightboxIdx(null)} className="absolute top-4 right-4 text-white/70 hover:text-white p-2"><X className="w-6 h-6" /></button>
        </div>
      )}
    </>
  );
}

/* ── Comment component (with replies) ── */
function CommentItem({ comment, activityId, currentUserId, onCommentUpdate }) {
  const navigate = useNavigate();
  const [liked, setLiked] = useState(comment.liked_by_me || false);
  const [likeCount, setLikeCount] = useState(comment.like_count || 0);
  const [replyText, setReplyText] = useState("");
  const [replyMentions, setReplyMentions] = useState([]);
  const [showReplyInput, setShowReplyInput] = useState(false);
  const [sendingReply, setSendingReply] = useState(false);
  const [showReplies, setShowReplies] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [editText, setEditText] = useState("");
  const [savingEdit, setSavingEdit] = useState(false);
  const replies = comment.replies || [];
  const isMine = comment.user_id === currentUserId;

  const handleLike = async () => {
    try {
      const res = await authFetch(`${API}/comments/${comment.comment_id}/like`, { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        setLiked(data.liked);
        setLikeCount(data.like_count);
      }
    } catch { /* silent */ }
  };

  const handleReply = async () => {
    if (!replyText.trim() || sendingReply) return;
    setSendingReply(true);
    try {
      const res = await authFetch(`${API}/activities/${activityId}/comments`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: replyText.trim(), parent_id: comment.comment_id }),
      });
      if (res.ok) {
        setReplyText("");
        setReplyMentions([]);
        setShowReplyInput(false);
        if (onCommentUpdate) onCommentUpdate();
      }
    } catch { toast.error("Erreur"); }
    setSendingReply(false);
  };

  const handleDelete = async (commentId) => {
    try {
      const res = await authFetch(`${API}/comments/${commentId}`, { method: "DELETE" });
      if (res.ok && onCommentUpdate) onCommentUpdate();
    } catch { toast.error("Erreur"); }
  };

  const handleSaveEdit = async (commentId) => {
    if (!editText.trim() || savingEdit) return;
    setSavingEdit(true);
    try {
      const res = await authFetch(`${API}/comments/${commentId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: editText.trim() }),
      });
      if (res.ok) {
        setEditingId(null);
        setEditText("");
        if (onCommentUpdate) onCommentUpdate();
      }
    } catch { toast.error("Erreur"); }
    setSavingEdit(false);
  };

  const canEdit = (createdAt) => (Date.now() - new Date(createdAt).getTime()) < 15 * 60 * 1000;

  const renderComment = (c, isReply = false) => {
    const cIsMine = c.user_id === currentUserId;
    return (
      <div key={c.comment_id} className={`flex gap-2.5 ${isReply ? "ml-8 mt-2" : ""}`}>
        <Avatar
          className="w-7 h-7 shrink-0 cursor-pointer"
          onClick={() => navigate(`/users/${c.user_id}`)}
        >
          <AvatarImage src={c.user_avatar} alt={c.user_name} />
          <AvatarFallback className="bg-primary/10 text-primary text-[9px]">
            {getInitials(c.user_name)}
          </AvatarFallback>
        </Avatar>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5">
            <Link to={`/users/${c.user_id}`} className="text-xs font-semibold hover:underline">
              {c.user_name}
              {c.user_id === currentUserId && <span className="text-[9px] text-[#459492] ml-0.5 font-normal">(toi)</span>}
            </Link>
            <span className="text-[10px] text-muted-foreground">{timeAgo(c.created_at)}</span>
            {c.edited_at && <span className="text-[9px] text-muted-foreground/50 italic">(modifié)</span>}
          </div>

          {editingId === c.comment_id ? (
            <div className="flex items-center gap-1.5 mt-1">
              <input value={editText} onChange={(e) => setEditText(e.target.value)} maxLength={500} className="flex-1 h-7 text-xs rounded-lg border border-primary/30 bg-primary/[0.03] px-2 focus:outline-none focus:ring-1 focus:ring-primary/40" autoFocus onKeyDown={(e) => { if (e.key === "Enter") handleSaveEdit(c.comment_id); if (e.key === "Escape") setEditingId(null); }} />
              <button onClick={() => handleSaveEdit(c.comment_id)} disabled={savingEdit} className="p-1 rounded text-primary"><Check className="w-3 h-3" /></button>
              <button onClick={() => setEditingId(null)} className="p-1 rounded text-muted-foreground"><X className="w-3 h-3" /></button>
            </div>
          ) : (
            <p className="text-xs text-foreground/80 mt-0.5 whitespace-pre-wrap break-words leading-relaxed">
              <MentionText content={c.content} mentions={c.mentions} currentUserId={currentUserId} />
            </p>
          )}

          {/* Actions */}
          <div className="flex items-center gap-3 mt-1">
            {!isReply && (
              <button onClick={() => setShowReplyInput(!showReplyInput)} className="text-[10px] text-muted-foreground hover:text-primary flex items-center gap-0.5">
                <Reply className="w-3 h-3" /> Répondre
              </button>
            )}
            <button onClick={handleLike} className={`text-[10px] flex items-center gap-0.5 ${liked ? "text-[#E48C75]" : "text-muted-foreground hover:text-[#E48C75]"}`}>
              <Heart className={`w-3 h-3 ${liked ? "fill-current" : ""}`} />
              {likeCount > 0 && likeCount}
            </button>
            {cIsMine && canEdit(c.created_at) && editingId !== c.comment_id && (
              <button onClick={() => { setEditingId(c.comment_id); setEditText(c.content); }} className="text-[10px] text-muted-foreground/50 hover:text-primary">
                <Pencil className="w-3 h-3" />
              </button>
            )}
            {cIsMine && (
              <button onClick={() => handleDelete(c.comment_id)} className="text-[10px] text-muted-foreground/50 hover:text-destructive">
                <Trash2 className="w-3 h-3" />
              </button>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="py-2">
      {renderComment(comment)}

      {/* Replies toggle */}
      {replies.length > 0 && (
        <button
          onClick={() => setShowReplies(!showReplies)}
          className="ml-10 mt-1 text-[10px] text-primary/70 hover:text-primary flex items-center gap-0.5"
        >
          {showReplies ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          {replies.length} réponse{replies.length > 1 ? "s" : ""}
        </button>
      )}
      {showReplies && replies.map((r) => renderComment(r, true))}

      {/* Reply input */}
      {showReplyInput && (
        <div className="ml-10 mt-2 flex items-center gap-1.5">
          <MentionInput
            value={replyText}
            onChange={setReplyText}
            mentions={replyMentions}
            onMentionsChange={setReplyMentions}
            placeholder={`Répondre à ${comment.user_name?.split(" ")[0]}...`}
            maxLength={500}
            className="flex-1 h-8 text-xs rounded-lg border-border/50 bg-muted/30 px-2.5"
            onSubmit={handleReply}
          />
          <button onClick={handleReply} disabled={!replyText.trim() || sendingReply} className="p-1.5 rounded-lg bg-primary/10 text-primary hover:bg-primary/20 disabled:opacity-40">
            {sendingReply ? <Loader2 className="w-3 h-3 animate-spin" /> : <Send className="w-3 h-3" />}
          </button>
        </div>
      )}
    </div>
  );
}

/* ── Main page ── */
export default function ActivityDetailPage() {
  const { activityId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const myId = user?.user_id;

  const [activity, setActivity] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  // Reaction state
  const [userReaction, setUserReaction] = useState(null);
  const [reactionCounts, setReactionCounts] = useState({});
  const [reactingType, setReactingType] = useState(null);
  const [reactionsDetailOpen, setReactionsDetailOpen] = useState(false);

  // Bookmark
  const [bookmarked, setBookmarked] = useState(false);
  const [bookmarking, setBookmarking] = useState(false);

  // Comment input
  const [commentText, setCommentText] = useState("");
  const [commentMentions, setCommentMentions] = useState([]);
  const [sendingComment, setSendingComment] = useState(false);

  const fetchActivity = useCallback(async () => {
    try {
      const res = await authFetch(`${API}/activities/${activityId}`);
      if (res.ok) {
        const data = await res.json();
        setActivity(data);
        setUserReaction(data.user_reaction);
        setReactionCounts(data.reaction_counts || {});
        setBookmarked(data.bookmarked || false);
      } else if (res.status === 404) {
        setNotFound(true);
      }
    } catch {
      toast.error("Erreur de chargement");
    } finally {
      setLoading(false);
    }
  }, [activityId]);

  useEffect(() => { fetchActivity(); }, [fetchActivity]);

  const handleReact = async (type) => {
    if (reactingType) return;
    setReactingType(type);
    try {
      const res = await authFetch(`${API}/activities/${activityId}/react`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reaction_type: type }),
      });
      if (res.ok) {
        const data = await res.json();
        const oldType = userReaction;
        setUserReaction(data.reacted ? data.reaction_type : null);
        setReactionCounts((prev) => {
          const next = { ...prev };
          if (oldType) next[oldType] = Math.max((next[oldType] || 0) - 1, 0);
          if (data.reacted) next[data.reaction_type] = (next[data.reaction_type] || 0) + 1;
          return next;
        });
      }
    } catch { /* silent */ }
    setReactingType(null);
  };

  const handleBookmark = async () => {
    if (bookmarking) return;
    setBookmarking(true);
    try {
      const res = await authFetch(`${API}/activities/${activityId}/bookmark`, { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        setBookmarked(data.bookmarked);
      }
    } catch { /* silent */ }
    setBookmarking(false);
  };

  const handleAddComment = async () => {
    if (!commentText.trim() || sendingComment) return;
    setSendingComment(true);
    try {
      const res = await authFetch(`${API}/activities/${activityId}/comments`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: commentText.trim() }),
      });
      if (res.ok) {
        setCommentText("");
        setCommentMentions([]);
        fetchActivity(); // Refresh to get new comment
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || "Erreur");
      }
    } catch { toast.error("Erreur de connexion"); }
    setSendingComment(false);
  };

  const totalReactions = REACTIONS.reduce((s, r) => s + (reactionCounts[r.type] || 0), 0);
  const config = activity ? (ACTIVITY_CONFIG[activity.type] || ACTIVITY_CONFIG.post) : ACTIVITY_CONFIG.post;
  const Icon = config?.icon || MessageCircle;

  if (loading) {
    return (
      <div className="min-h-screen app-bg-mesh">
        <Sidebar />
        <main className="lg:ml-64 pt-14 lg:pt-0 flex items-center justify-center min-h-[60vh]">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </main>
      </div>
    );
  }

  if (notFound || !activity) {
    return (
      <div className="min-h-screen app-bg-mesh">
        <Sidebar />
        <main className="lg:ml-64 pt-14 lg:pt-0 pb-8">
          <div className="px-4 lg:px-8 py-16 text-center">
            <div className="w-16 h-16 rounded-2xl bg-muted/50 flex items-center justify-center mx-auto mb-4">
              <MessageCircle className="w-8 h-8 text-muted-foreground" />
            </div>
            <h2 className="text-lg font-semibold mb-2">Activité introuvable</h2>
            <p className="text-sm text-muted-foreground mb-4">Cette activité a été supprimée ou n'existe pas.</p>
            <Button onClick={() => navigate("/community")} className="rounded-xl">
              Retour au feed
            </Button>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen app-bg-mesh">
      <Sidebar />
      <main className="lg:ml-64 pt-14 lg:pt-0 pb-8">
        {/* Dark header */}
        <div className="section-dark-header px-4 lg:px-8 pt-8 lg:pt-10 pb-6">
          <div className="max-w-2xl mx-auto">
            <button
              onClick={() => navigate(-1)}
              className="w-8 h-8 rounded-lg bg-white/10 hover:bg-white/20 flex items-center justify-center transition-colors mb-3"
            >
              <ArrowLeft className="w-4 h-4 text-white" />
            </button>
            <div className="flex items-center gap-3">
              <Avatar
                className="w-11 h-11 ring-2 ring-white/10 cursor-pointer"
                onClick={() => navigate(`/users/${activity.user_id}`)}
              >
                <AvatarImage src={activity.user_avatar} alt={activity.user_name} />
                <AvatarFallback className="bg-white/10 text-white text-sm">
                  {getInitials(activity.user_name)}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1 min-w-0">
                <Link to={`/users/${activity.user_id}`} className="text-white font-semibold text-sm hover:underline truncate block">
                  {activity.user_name}
                  {activity.user_id === myId && <span className="text-[10px] text-[#55B3AE] ml-1 font-normal">(toi)</span>}
                </Link>
                <p className="text-white/50 text-xs">{timeAgo(activity.created_at)}</p>
              </div>
              {activity.user_id !== myId && (
                <FollowButton userId={activity.user_id} size="sm" />
              )}
            </div>
          </div>
        </div>

        <div className="px-4 lg:px-8">
          <div className="max-w-2xl mx-auto mt-4 space-y-4 opacity-0 animate-fade-in" style={{ animationFillMode: "forwards" }}>
            {/* ── Activity content ── */}
            <Card>
              <CardContent className="p-5">
                {config.isPost ? (
                  <div>
                    {activity.data?.content && (
                      <p className="text-sm text-foreground/90 whitespace-pre-wrap break-words leading-relaxed">
                        <MentionText
                          content={activity.data.content}
                          mentions={activity.data?.mentions || []}
                          currentUserId={myId}
                        />
                      </p>
                    )}
                    {activity.data?.images?.length > 0 && (
                      <PostImageGrid images={activity.data.images} />
                    )}
                    {activity.data?.link_preview && (
                      <LinkPreviewCard preview={activity.data.link_preview} />
                    )}
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <div
                      className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0"
                      style={{ backgroundColor: `${config.color}15` }}
                    >
                      <Icon className="w-5 h-5" style={{ color: config.color }} />
                    </div>
                    <p className="text-sm text-foreground/80">
                      {config.getText?.(activity.data || {})}
                    </p>
                  </div>
                )}

                {/* Hashtag pills */}
                {activity.hashtags?.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-3">
                    {activity.hashtags.map((tag) => (
                      <Link
                        key={tag}
                        to={`/hashtags/${encodeURIComponent(tag)}`}
                        className="text-[11px] font-medium text-[#459492] bg-[#459492]/8 px-2 py-0.5 rounded-md hover:bg-[#459492]/15 transition-colors"
                      >
                        #{tag}
                      </Link>
                    ))}
                  </div>
                )}

                {/* ── Reaction bar ── */}
                <div className="flex items-center justify-between mt-4 pt-3 border-t border-border/30">
                  <div className="flex items-center gap-1">
                    {REACTIONS.map(({ type, emoji, label }) => {
                      const count = reactionCounts[type] || 0;
                      const isActive = userReaction === type;
                      return (
                        <button
                          key={type}
                          onClick={() => handleReact(type)}
                          disabled={!!reactingType}
                          className={`flex items-center gap-1 px-2.5 py-1.5 rounded-full text-xs transition-all duration-200 ${
                            isActive
                              ? "bg-primary/15 ring-1 ring-primary/25 font-semibold scale-105"
                              : "hover:bg-muted/50"
                          }`}
                          title={label}
                        >
                          <span className="text-sm">{emoji}</span>
                          {count > 0 && <span className={`text-[11px] ${isActive ? "text-primary" : "text-muted-foreground"}`}>{count}</span>}
                        </button>
                      );
                    })}
                    {totalReactions > 0 && (
                      <button
                        onClick={() => setReactionsDetailOpen(true)}
                        className="text-[10px] text-muted-foreground/60 hover:text-muted-foreground ml-1"
                      >
                        · Voir tout
                      </button>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] text-muted-foreground">
                      {activity.total_comments || 0} commentaire{(activity.total_comments || 0) > 1 ? "s" : ""}
                    </span>
                    <button
                      onClick={handleBookmark}
                      disabled={bookmarking}
                      className="p-1.5 rounded-lg hover:bg-muted/50 transition-colors"
                    >
                      <Bookmark
                        className={`w-4 h-4 transition-colors ${
                          bookmarked ? "fill-[#459492] text-[#459492]" : "text-muted-foreground/40"
                        }`}
                      />
                    </button>
                    {activity.user_id !== myId && (
                      <SafetyMenu
                        userId={activity.user_id}
                        targetType="activity"
                        targetId={activity.activity_id}
                        size="sm"
                      />
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* ── Comment input ── */}
            <div className="flex items-center gap-2">
              <MentionInput
                value={commentText}
                onChange={setCommentText}
                mentions={commentMentions}
                onMentionsChange={setCommentMentions}
                placeholder="Écrire un commentaire..."
                maxLength={500}
                className="flex-1 h-10 rounded-xl border-border/50 bg-card px-3.5 text-sm"
                onSubmit={handleAddComment}
              />
              <Button
                onClick={handleAddComment}
                disabled={!commentText.trim() || sendingComment}
                size="icon"
                className="h-10 w-10 rounded-xl bg-gradient-to-r from-[#459492] to-[#55B3AE] hover:from-[#275255] hover:to-[#459492] text-white shadow-md shrink-0"
              >
                {sendingComment ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              </Button>
            </div>

            {/* ── Comments list (all visible by default — detail page pattern) ── */}
            {activity.comments?.length > 0 && (
              <Card>
                <CardContent className="p-4 divide-y divide-border/20">
                  {activity.comments.map((comment) => (
                    <CommentItem
                      key={comment.comment_id}
                      comment={comment}
                      activityId={activityId}
                      currentUserId={myId}
                      onCommentUpdate={fetchActivity}
                    />
                  ))}
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </main>

      {/* Reactions detail dialog */}
      {reactionsDetailOpen && (
        <ReactionsDetailDialog
          activityId={activityId}
          open={reactionsDetailOpen}
          onOpenChange={setReactionsDetailOpen}
        />
      )}
    </div>
  );
}
