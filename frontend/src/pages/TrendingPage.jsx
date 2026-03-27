/**
 * TrendingPage — Discover trending content across InFinea.
 *
 * Pattern: Instagram Explore + Twitter Trending.
 * Shows trending hashtags and popular posts in a single, browsable page.
 *
 * Route: /trending
 */

import React, { useState, useEffect, useCallback, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  TrendingUp,
  Hash,
  Loader2,
  Bookmark,
  Zap,
  Award,
  Flame,
  Trophy,
  MessageCircle,
  Star,
  Compass,
} from "lucide-react";
import { toast } from "sonner";
import Sidebar from "@/components/Sidebar";
import MentionText from "@/components/MentionText";
import LinkPreviewCard from "@/components/LinkPreviewCard";
import { API, authFetch, useAuth } from "@/App";

// ── Activity type config ──
const ACTIVITY_CONFIG = {
  session_completed: { icon: Zap, color: "#459492", getText: (d) => `a terminé "${d.action_title || "une micro-action"}" en ${d.duration || 0} min` },
  badge_earned: { icon: Award, color: "#E48C75", getText: (d) => `a obtenu le badge "${d.badge_name || "nouveau badge"}"` },
  streak_milestone: { icon: Flame, color: "#E48C75", getText: (d) => `a atteint ${d.streak_days} jours de streak !` },
  challenge_completed: { icon: Trophy, color: "#459492", getText: (d) => `a complété le défi "${d.challenge_title || "un défi"}" !` },
  level_up: { icon: Star, color: "#F5A623", getText: (d) => `a atteint le niveau ${d.level || "?"} !` },
  post: { icon: MessageCircle, color: "#55B3AE", isPost: true },
};

const REACTIONS = [
  { type: "bravo", emoji: "👏" },
  { type: "inspire", emoji: "💡" },
  { type: "fire", emoji: "🔥" },
  { type: "solidaire", emoji: "🤝" },
  { type: "curieux", emoji: "🧠" },
];

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

function getInitials(name) {
  if (!name) return "U";
  return name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2);
}

/* ── Post image grid ── */
function PostImageGrid({ images }) {
  if (!images?.length) return null;
  return (
    <div className={`grid ${images.length === 1 ? "grid-cols-1" : "grid-cols-2"} gap-1 mt-2 rounded-lg overflow-hidden`}>
      {images.slice(0, 4).map((img, i) => (
        <img key={i} src={img.thumbnail_url || img.image_url} alt="" className="w-full aspect-square object-cover" loading="lazy" />
      ))}
    </div>
  );
}

export default function TrendingPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [trendingTags, setTrendingTags] = useState([]);
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [nextCursor, setNextCursor] = useState(null);
  const [hasMore, setHasMore] = useState(false);
  const sentinelRef = useRef(null);

  // Fetch trending hashtags + discover feed in parallel
  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const [tagsRes, feedRes] = await Promise.all([
          authFetch(`${API}/hashtags/trending?limit=15`),
          authFetch(`${API}/feed/discover?limit=20`),
        ]);
        if (cancelled) return;
        if (tagsRes.ok) {
          const data = await tagsRes.json();
          setTrendingTags(data.trending || []);
        }
        if (feedRes.ok) {
          const data = await feedRes.json();
          setActivities(data.activities || []);
          setNextCursor(data.next_cursor);
          setHasMore(data.has_more);
        }
      } catch {
        toast.error("Erreur de chargement");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const loadMore = useCallback(async () => {
    if (!nextCursor || loadingMore) return;
    setLoadingMore(true);
    try {
      const res = await authFetch(`${API}/feed/discover?limit=20&cursor=${nextCursor}`);
      if (res.ok) {
        const data = await res.json();
        setActivities((prev) => [...prev, ...(data.activities || [])]);
        setNextCursor(data.next_cursor);
        setHasMore(data.has_more);
      }
    } catch { /* silent */ }
    setLoadingMore(false);
  }, [nextCursor, loadingMore]);

  // Infinite scroll
  useEffect(() => {
    if (!hasMore || loadingMore || !sentinelRef.current) return;
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) loadMore(); },
      { rootMargin: "200px" },
    );
    observer.observe(sentinelRef.current);
    return () => observer.disconnect();
  }, [hasMore, loadingMore, loadMore]);

  // Bookmark toggle
  const handleBookmark = async (activityId) => {
    try {
      const res = await authFetch(`${API}/activities/${activityId}/bookmark`, { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        setActivities((prev) =>
          prev.map((a) => a.activity_id === activityId ? { ...a, bookmarked: data.bookmarked } : a),
        );
      }
    } catch { /* silent */ }
  };

  return (
    <div className="min-h-screen app-bg-mesh">
      <Sidebar active="community" />
      <main className="lg:ml-64 pt-14 lg:pt-0 pb-8">
        {/* Dark header */}
        <div className="section-dark-header px-4 lg:px-8 pt-8 lg:pt-10 pb-8">
          <div className="max-w-2xl mx-auto">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-[#459492]/20 flex items-center justify-center">
                <Compass className="w-5 h-5 text-[#55B3AE]" />
              </div>
              <div>
                <h1 className="text-display text-2xl lg:text-3xl font-semibold text-white opacity-0 animate-fade-in">
                  Tendances
                </h1>
                <p className="text-white/60 text-sm mt-0.5 opacity-0 animate-fade-in" style={{ animationDelay: "50ms" }}>
                  Ce qui buzz sur InFinea
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="px-4 lg:px-8">
          <div className="max-w-2xl mx-auto mt-4">
            {loading ? (
              <div className="flex justify-center py-16">
                <Loader2 className="w-6 h-6 animate-spin text-primary" />
              </div>
            ) : (
              <>
                {/* Trending hashtags section */}
                {trendingTags.length > 0 && (
                  <div className="mb-6 opacity-0 animate-fade-in" style={{ animationFillMode: "forwards" }}>
                    <div className="flex items-center gap-2 mb-3">
                      <TrendingUp className="w-4 h-4 text-primary" />
                      <h2 className="text-sm font-semibold text-foreground">Hashtags tendance</h2>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {trendingTags.map((tag, i) => (
                        <Link
                          key={tag.tag}
                          to={`/hashtags/${encodeURIComponent(tag.tag)}`}
                          className="group flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-card border border-border/50 hover:border-[#459492]/30 hover:bg-[#459492]/5 transition-all duration-200 opacity-0 animate-fade-in"
                          style={{ animationDelay: `${i * 30}ms`, animationFillMode: "forwards" }}
                        >
                          <Hash className="w-3 h-3 text-[#459492] group-hover:text-[#275255]" />
                          <span className="text-sm font-medium text-foreground/80 group-hover:text-[#459492]">
                            {tag.tag}
                          </span>
                          <span className="text-[10px] text-muted-foreground/50">
                            {tag.use_count}
                          </span>
                        </Link>
                      ))}
                    </div>
                  </div>
                )}

                {/* Trending posts */}
                <div className="mb-3 flex items-center gap-2">
                  <Star className="w-4 h-4 text-primary" />
                  <h2 className="text-sm font-semibold text-foreground">Posts populaires</h2>
                </div>

                {activities.length === 0 ? (
                  <div className="text-center py-12">
                    <Compass className="w-10 h-10 text-muted-foreground/30 mx-auto mb-3" />
                    <p className="text-muted-foreground">Aucun contenu tendance pour le moment</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {activities.map((activity, i) => {
                      const config = ACTIVITY_CONFIG[activity.type] || ACTIVITY_CONFIG.post;
                      const Icon = config.icon;
                      const totalReactions = Object.values(activity.reaction_counts || {}).reduce((s, v) => s + (v || 0), 0);

                      return (
                        <Card
                          key={activity.activity_id}
                          className="hover:border-[#459492]/20 hover:shadow-sm transition-all duration-200 cursor-pointer opacity-0 animate-fade-in"
                          style={{ animationDelay: `${i * 40}ms`, animationFillMode: "forwards" }}
                          onClick={() => navigate(`/activity/${activity.activity_id}`)}
                        >
                          <CardContent className="p-4">
                            {/* Author header */}
                            <div className="flex items-center gap-2.5 mb-2">
                              <Avatar
                                className="w-9 h-9 cursor-pointer"
                                onClick={(e) => { e.stopPropagation(); navigate(`/users/${activity.user_id}`); }}
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
                                  onClick={(e) => e.stopPropagation()}
                                >
                                  {activity.user_name}
                                </Link>
                                <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground">
                                  <span>{timeAgo(activity.created_at)}</span>
                                  <span className="flex items-center gap-0.5" style={{ color: config.color }}>
                                    <Icon className="w-3 h-3" />
                                  </span>
                                </div>
                              </div>
                              <button
                                onClick={(e) => { e.stopPropagation(); handleBookmark(activity.activity_id); }}
                                className="p-1.5 rounded-lg hover:bg-muted/50 transition-colors"
                              >
                                <Bookmark className={`w-4 h-4 transition-colors ${activity.bookmarked ? "fill-[#459492] text-[#459492]" : "text-muted-foreground/40"}`} />
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
                                      currentUserId={user?.user_id}
                                    />
                                  </p>
                                )}
                                {activity.data?.images?.length > 0 && <PostImageGrid images={activity.data.images} />}
                                {activity.data?.link_preview && <LinkPreviewCard preview={activity.data.link_preview} />}
                              </div>
                            ) : (
                              <div className="flex items-center gap-1.5">
                                <div className="w-5 h-5 rounded-md flex items-center justify-center" style={{ backgroundColor: `${config.color}15` }}>
                                  <Icon className="w-3 h-3" style={{ color: config.color }} />
                                </div>
                                <p className="text-sm text-foreground/80">{config.getText(activity.data || {})}</p>
                              </div>
                            )}

                            {/* Hashtags */}
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
                                    {REACTIONS.filter((r) => activity.reaction_counts?.[r.type] > 0).map((r) => r.emoji).join("")} {totalReactions}
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
                    })}

                    <div ref={sentinelRef} className="h-1" />
                    {loadingMore && (
                      <div className="flex justify-center py-4">
                        <Loader2 className="w-5 h-5 animate-spin text-primary" />
                      </div>
                    )}
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
