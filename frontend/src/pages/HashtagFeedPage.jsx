/**
 * HashtagFeedPage — Feed of activities tagged with a specific #hashtag.
 *
 * Pattern: Instagram /explore/tags/{tag} — header with stats + scrollable feed.
 * Activities are shown with author, content, images, reactions, bookmarks.
 * Cursor-based infinite scroll for seamless browsing.
 *
 * Route: /hashtags/:tag
 */

import React, { useState, useEffect, useCallback, useRef } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  ArrowLeft,
  Hash,
  Loader2,
  Bookmark,
  Zap,
  Award,
  Flame,
  Trophy,
  MessageCircle,
  TrendingUp,
} from "lucide-react";
import { toast } from "sonner";
import Sidebar from "@/components/Sidebar";
import MentionText from "@/components/MentionText";
import LinkPreviewCard from "@/components/LinkPreviewCard";
import { API, authFetch, useAuth } from "@/App";

// ── Activity type config (subset of CommunityFeedPage) ──
const ACTIVITY_CONFIG = {
  session_completed: {
    icon: Zap,
    color: "#459492",
    getText: (data) => `a terminé "${data.action_title || "une micro-action"}" en ${data.duration || 0} min`,
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
  post: {
    icon: MessageCircle,
    color: "#55B3AE",
    isPost: true,
  },
};

const REACTIONS = [
  { type: "bravo", emoji: "👏" },
  { type: "inspire", emoji: "💡" },
  { type: "fire", emoji: "🔥" },
  { type: "solidaire", emoji: "🤝" },
  { type: "curieux", emoji: "🧠" },
];

function getInitials(name) {
  if (!name) return "U";
  return name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2);
}

function timeAgo(iso) {
  if (!iso) return "";
  const diff = Date.now() - new Date(iso).getTime();
  const min = Math.floor(diff / 60000);
  if (min < 1) return "à l'instant";
  if (min < 60) return `${min}min`;
  const h = Math.floor(min / 60);
  if (h < 24) return `${h}h`;
  const d = Math.floor(h / 24);
  if (d < 7) return `${d}j`;
  return new Date(iso).toLocaleDateString("fr-FR", { day: "numeric", month: "short" });
}

/* ── Post image grid (simplified) ── */
function PostImageGrid({ images }) {
  if (!images?.length) return null;
  const gridClass = images.length === 1 ? "grid-cols-1" : "grid-cols-2";
  return (
    <div className={`grid ${gridClass} gap-1 mt-2 rounded-lg overflow-hidden`}>
      {images.slice(0, 4).map((img, i) => (
        <img
          key={i}
          src={img.thumbnail_url || img.image_url}
          alt=""
          className="w-full aspect-square object-cover"
          loading="lazy"
        />
      ))}
    </div>
  );
}

/* ── Activity card for hashtag feed ── */
function HashtagActivityCard({ activity, currentUserId, onBookmarkChange }) {
  const navigate = useNavigate();
  const config = ACTIVITY_CONFIG[activity.type] || ACTIVITY_CONFIG.post;
  const Icon = config.icon;
  const [bookmarked, setBookmarked] = useState(activity.bookmarked || false);
  const [bookmarking, setBookmarking] = useState(false);

  const handleBookmark = async (e) => {
    e.stopPropagation();
    if (bookmarking) return;
    setBookmarking(true);
    try {
      const res = await authFetch(`${API}/activities/${activity.activity_id}/bookmark`, {
        method: "POST",
      });
      if (res.ok) {
        const data = await res.json();
        setBookmarked(data.bookmarked);
        if (onBookmarkChange) onBookmarkChange(activity.activity_id, data.bookmarked);
      }
    } catch { /* silent */ }
    setBookmarking(false);
  };

  // Total reaction count
  const totalReactions = REACTIONS.reduce(
    (sum, r) => sum + (activity.reaction_counts?.[r.type] || 0),
    0,
  );

  return (
    <Card className="hover:border-[#459492]/20 hover:shadow-sm transition-all duration-200">
      <CardContent className="p-4">
        {/* Author header */}
        <div className="flex items-center gap-2.5 mb-2">
          <Avatar
            className="w-9 h-9 cursor-pointer"
            onClick={() => navigate(`/users/${activity.user_id}`)}
          >
            <AvatarImage src={activity.user_avatar} alt={activity.user_name} />
            <AvatarFallback className="bg-primary/10 text-primary text-xs">
              {getInitials(activity.user_name)}
            </AvatarFallback>
          </Avatar>
          <div className="flex-1 min-w-0">
            <Link
              to={`/users/${activity.user_id}`}
              className="text-sm font-semibold hover:underline truncate block"
            >
              {activity.user_name}
              {activity.user_id === currentUserId && (
                <span className="text-[10px] text-[#459492] ml-1 font-normal">(toi)</span>
              )}
            </Link>
            <span className="text-[10px] text-muted-foreground">{timeAgo(activity.created_at)}</span>
          </div>

          {/* Bookmark */}
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
        </div>

        {/* Content */}
        {config.isPost ? (
          <div>
            {activity.data?.content && (
              <p className="text-sm text-foreground/90 whitespace-pre-wrap break-words leading-relaxed">
                <MentionText
                  content={activity.data.content}
                  mentions={activity.data?.mentions || []}
                  currentUserId={currentUserId}
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
          <div className="flex items-center gap-1.5">
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
        )}

        {/* Hashtag pills */}
        {activity.hashtags?.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-2">
            {activity.hashtags.map((tag) => (
              <Link
                key={tag}
                to={`/hashtags/${encodeURIComponent(tag)}`}
                className="text-[11px] font-medium text-[#459492] bg-[#459492]/8 px-2 py-0.5 rounded-md hover:bg-[#459492]/15 transition-colors"
                onClick={(e) => e.stopPropagation()}
              >
                #{tag}
              </Link>
            ))}
          </div>
        )}

        {/* Engagement stats */}
        {(totalReactions > 0 || activity.comment_count > 0) && (
          <div className="flex items-center gap-3 mt-2.5 text-[11px] text-muted-foreground">
            {totalReactions > 0 && (
              <span className="flex items-center gap-1">
                {REACTIONS.filter((r) => activity.reaction_counts?.[r.type] > 0)
                  .map((r) => r.emoji)
                  .join("")}{" "}
                {totalReactions}
              </span>
            )}
            {activity.comment_count > 0 && (
              <span>{activity.comment_count} commentaire{activity.comment_count > 1 ? "s" : ""}</span>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

/* ── Main page ── */
export default function HashtagFeedPage() {
  const { tag } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [nextCursor, setNextCursor] = useState(null);
  const [hasMore, setHasMore] = useState(false);
  const [totalUses, setTotalUses] = useState(0);
  const [following, setFollowing] = useState(false);
  const [togglingFollow, setTogglingFollow] = useState(false);
  const observerRef = useRef(null);
  const sentinelRef = useRef(null);

  const decodedTag = decodeURIComponent(tag || "");

  const fetchFeed = useCallback(
    async (cursor = null) => {
      if (!decodedTag) return;
      if (cursor) setLoadingMore(true);
      else setLoading(true);

      try {
        const params = new URLSearchParams({ limit: "20" });
        if (cursor) params.set("cursor", cursor);
        const res = await authFetch(
          `${API}/hashtags/${encodeURIComponent(decodedTag)}/feed?${params}`,
        );
        if (res.ok) {
          const data = await res.json();
          if (cursor) {
            setActivities((prev) => [...prev, ...(data.activities || [])]);
          } else {
            setActivities(data.activities || []);
          }
          setNextCursor(data.next_cursor);
          setHasMore(data.has_more);
          setTotalUses(data.total_uses || 0);
          if (!cursor && data.following !== undefined) setFollowing(data.following);
        }
      } catch {
        toast.error("Erreur de chargement");
      } finally {
        setLoading(false);
        setLoadingMore(false);
      }
    },
    [decodedTag],
  );

  useEffect(() => {
    setActivities([]);
    setNextCursor(null);
    fetchFeed();
  }, [decodedTag, fetchFeed]);

  // ── Infinite scroll observer ──
  useEffect(() => {
    if (!hasMore || loadingMore || !sentinelRef.current) return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && nextCursor) {
          fetchFeed(nextCursor);
        }
      },
      { rootMargin: "200px" },
    );
    observer.observe(sentinelRef.current);
    observerRef.current = observer;
    return () => observer.disconnect();
  }, [hasMore, loadingMore, nextCursor, fetchFeed]);

  const handleToggleFollow = async () => {
    if (togglingFollow) return;
    setTogglingFollow(true);
    try {
      const res = await authFetch(
        `${API}/hashtags/${encodeURIComponent(decodedTag)}/follow`,
        { method: "POST" },
      );
      if (res.ok) {
        const data = await res.json();
        if (data.error) {
          toast.error(data.error);
        } else {
          setFollowing(data.followed);
          toast.success(data.followed ? `Tu suis #${decodedTag}` : `Tu ne suis plus #${decodedTag}`);
        }
      }
    } catch {
      toast.error("Erreur");
    } finally {
      setTogglingFollow(false);
    }
  };

  return (
    <div className="min-h-screen app-bg-mesh">
      <Sidebar />
      <main className="lg:ml-64 pt-14 lg:pt-0 pb-8">
        {/* Dark header */}
        <div className="section-dark-header px-4 lg:px-8 pt-8 lg:pt-10 pb-8">
          <div className="max-w-2xl mx-auto">
            <div className="flex items-center gap-3 mb-3">
              <button
                onClick={() => navigate(-1)}
                className="w-8 h-8 rounded-lg bg-white/10 hover:bg-white/20 flex items-center justify-center transition-colors"
              >
                <ArrowLeft className="w-4 h-4 text-white" />
              </button>
              <div className="w-10 h-10 rounded-xl bg-[#459492]/20 flex items-center justify-center">
                <Hash className="w-5 h-5 text-[#55B3AE]" />
              </div>
              <div className="flex-1">
                <h1 className="text-display text-2xl lg:text-3xl font-semibold text-white opacity-0 animate-fade-in">
                  #{decodedTag}
                </h1>
                <p
                  className="text-white/60 text-sm mt-0.5 flex items-center gap-1.5 opacity-0 animate-fade-in"
                  style={{ animationDelay: "50ms" }}
                >
                  <TrendingUp className="w-3 h-3 text-white/40" />
                  {totalUses} publication{totalUses > 1 ? "s" : ""}
                </p>
              </div>
              <button
                onClick={handleToggleFollow}
                disabled={togglingFollow || loading}
                className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all duration-200 opacity-0 animate-fade-in ${
                  following
                    ? "bg-white/15 text-white hover:bg-white/25 border border-white/20"
                    : "bg-[#55B3AE] text-white hover:bg-[#459492] shadow-md"
                }`}
                style={{ animationDelay: "100ms" }}
              >
                {togglingFollow ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : following ? (
                  "Suivi"
                ) : (
                  "Suivre"
                )}
              </button>
            </div>
          </div>
        </div>

        <div className="px-4 lg:px-8">
          <div className="max-w-2xl mx-auto mt-4">
            {loading ? (
              <div className="flex flex-col items-center justify-center py-16">
                <Loader2 className="w-6 h-6 text-primary animate-spin" />
                <p className="text-sm text-muted-foreground mt-3">Chargement...</p>
              </div>
            ) : activities.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-16 text-center opacity-0 animate-fade-in" style={{ animationFillMode: "forwards" }}>
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-[#459492]/20 to-[#459492]/5 flex items-center justify-center mb-4 ring-1 ring-[#459492]/10">
                  <Hash className="w-7 h-7 text-[#459492]" />
                </div>
                <h2 className="text-base font-semibold mb-1">Aucune publication</h2>
                <p className="text-sm text-muted-foreground max-w-xs mb-4">
                  Soyez le premier à utiliser #{decodedTag} dans un post !
                </p>
                <Button
                  onClick={() => navigate("/community")}
                  className="rounded-xl gap-1.5 btn-press"
                >
                  Aller au feed
                </Button>
              </div>
            ) : (
              <div className="space-y-3 opacity-0 animate-fade-in" style={{ animationFillMode: "forwards" }}>
                {activities.map((activity, i) => (
                  <div
                    key={activity.activity_id}
                    className="opacity-0 animate-fade-in"
                    style={{
                      animationDelay: `${i * 40}ms`,
                      animationFillMode: "forwards",
                    }}
                  >
                    <HashtagActivityCard
                      activity={activity}
                      currentUserId={user?.user_id}
                    />
                  </div>
                ))}

                {/* Infinite scroll sentinel */}
                <div ref={sentinelRef} className="h-1" />
                {loadingMore && (
                  <div className="flex justify-center py-4">
                    <Loader2 className="w-5 h-5 animate-spin text-primary" />
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
