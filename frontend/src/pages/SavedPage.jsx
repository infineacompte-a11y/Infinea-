import React, { useState, useEffect, useCallback, useRef } from "react";
import { Link } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  Bookmark,
  Loader2,
  ArrowLeft,
  Flame,
  Award,
  Zap,
  Activity,
} from "lucide-react";
import { toast } from "sonner";
import Sidebar from "@/components/Sidebar";
import { API, authFetch, useAuth } from "@/App";

// ── Activity type config (shared with CommunityFeedPage) ──
const ACTIVITY_CONFIG = {
  session_completed: { icon: Zap, color: "#55B3AE", label: "Session" },
  badge_earned: { icon: Award, color: "#F5A623", label: "Badge" },
  streak_milestone: { icon: Flame, color: "#E48C75", label: "Streak" },
  challenge_completed: { icon: Award, color: "#459492", label: "Défi" },
  post: { icon: Activity, color: "#459492", label: "Post" },
};

function formatTimeAgo(dateStr) {
  if (!dateStr) return "";
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "maintenant";
  if (mins < 60) return `${mins}min`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}j`;
  return `${Math.floor(days / 7)}sem`;
}

export default function SavedPage() {
  const { user } = useAuth();
  const [bookmarks, setBookmarks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [nextCursor, setNextCursor] = useState(null);
  const sentinelRef = useRef(null);

  const fetchBookmarks = useCallback(async (cursor) => {
    const isFirst = !cursor;
    if (isFirst) setLoading(true);
    else setLoadingMore(true);

    try {
      const params = new URLSearchParams({ limit: "20" });
      if (cursor) params.set("cursor", cursor);
      const res = await authFetch(`${API}/bookmarks?${params}`);
      if (res.ok) {
        const data = await res.json();
        if (isFirst) {
          setBookmarks(data.bookmarks);
        } else {
          setBookmarks((prev) => [...prev, ...data.bookmarks]);
        }
        setNextCursor(data.next_cursor);
      }
    } catch {
      toast.error("Erreur de chargement");
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, []);

  useEffect(() => {
    fetchBookmarks(null);
  }, [fetchBookmarks]);

  // Infinite scroll
  useEffect(() => {
    if (!sentinelRef.current || !nextCursor) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && nextCursor && !loadingMore) {
          fetchBookmarks(nextCursor);
        }
      },
      { rootMargin: "200px" }
    );
    observer.observe(sentinelRef.current);
    return () => observer.disconnect();
  }, [nextCursor, loadingMore, fetchBookmarks]);

  const handleRemoveBookmark = async (activityId) => {
    try {
      const res = await authFetch(`${API}/activities/${activityId}/bookmark`, {
        method: "POST",
      });
      if (res.ok) {
        setBookmarks((prev) => prev.filter((b) => b.activity_id !== activityId));
        toast.success("Retiré des sauvegardés");
      }
    } catch {
      toast.error("Erreur");
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Sidebar active="community" />
      <main className="md:ml-56 p-4 md:p-6 max-w-2xl mx-auto">
        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <Link
            to="/community"
            className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-muted/60 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div className="flex items-center gap-2">
            <Bookmark className="w-5 h-5 text-primary" fill="currentColor" />
            <h1 className="text-xl font-semibold tracking-tight">Sauvegardés</h1>
          </div>
          {bookmarks.length > 0 && (
            <span className="text-sm text-muted-foreground ml-auto">
              {bookmarks.length} post{bookmarks.length > 1 ? "s" : ""}
            </span>
          )}
        </div>

        {/* Loading state */}
        {loading && (
          <div className="flex justify-center py-16">
            <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
          </div>
        )}

        {/* Empty state */}
        {!loading && bookmarks.length === 0 && (
          <div className="text-center py-16 space-y-3">
            <Bookmark className="w-10 h-10 text-muted-foreground/30 mx-auto" />
            <p className="text-muted-foreground">Aucun post sauvegardé</p>
            <p className="text-sm text-muted-foreground/60">
              Appuie sur l'icône signet sur un post pour le retrouver ici.
            </p>
          </div>
        )}

        {/* Bookmarked activities */}
        <div className="space-y-3">
          {bookmarks.map((activity) => {
            const config = ACTIVITY_CONFIG[activity.type] || ACTIVITY_CONFIG.post;
            const Icon = config.icon;
            return (
              <Card key={activity.activity_id} className="overflow-hidden border-border/40 shadow-sm">
                <CardContent className="p-4">
                  {/* Author row */}
                  <div className="flex items-center gap-3 mb-3">
                    <Link to={`/users/${activity.user_id}`}>
                      <Avatar className="w-9 h-9 ring-2 ring-background">
                        <AvatarImage src={activity.user_avatar} />
                        <AvatarFallback className="text-xs bg-muted">
                          {(activity.user_display_name || activity.user_name || "?")[0]}
                        </AvatarFallback>
                      </Avatar>
                    </Link>
                    <div className="flex-1 min-w-0">
                      <Link
                        to={`/users/${activity.user_id}`}
                        className="text-sm font-medium hover:underline"
                      >
                        {activity.user_display_name || activity.user_name || "Utilisateur"}
                      </Link>
                      <div className="flex items-center gap-2 text-[11px] text-muted-foreground">
                        <span>{formatTimeAgo(activity.created_at)}</span>
                        <span className="flex items-center gap-1" style={{ color: config.color }}>
                          <Icon className="w-3 h-3" />
                          {config.label}
                        </span>
                      </div>
                    </div>
                    <button
                      onClick={() => handleRemoveBookmark(activity.activity_id)}
                      className="text-primary hover:text-primary/70 transition-colors p-1.5"
                      title="Retirer des sauvegardés"
                    >
                      <Bookmark className="w-4 h-4" fill="currentColor" />
                    </button>
                  </div>

                  {/* Content */}
                  {activity.content && (
                    <p className="text-sm text-foreground/90 whitespace-pre-wrap leading-relaxed mb-2">
                      {activity.content}
                    </p>
                  )}

                  {/* Images */}
                  {activity.images?.length > 0 && (
                    <div className={`grid gap-1.5 rounded-xl overflow-hidden mb-2 ${
                      activity.images.length === 1 ? "grid-cols-1" :
                      activity.images.length === 2 ? "grid-cols-2" :
                      activity.images.length === 3 ? "grid-cols-2" : "grid-cols-2"
                    }`}>
                      {activity.images.map((img, i) => (
                        <img
                          key={i}
                          src={img.image_url || img.thumbnail_url}
                          alt=""
                          className="w-full object-cover rounded-lg"
                          style={{ maxHeight: activity.images.length === 1 ? "400px" : "200px" }}
                          loading="lazy"
                        />
                      ))}
                    </div>
                  )}

                  {/* Activity data preview */}
                  {activity.data && activity.type !== "post" && (
                    <div className="flex items-center gap-2 mt-1">
                      <div
                        className="w-6 h-6 rounded-full flex items-center justify-center"
                        style={{ backgroundColor: `${config.color}15` }}
                      >
                        <Icon className="w-3 h-3" style={{ color: config.color }} />
                      </div>
                      <p className="text-sm text-foreground/80">
                        {activity.data.title || activity.data.badge_name || activity.data.streak_days && `${activity.data.streak_days} jours de streak` || ""}
                      </p>
                    </div>
                  )}

                  {/* Bookmarked at */}
                  <p className="text-[10px] text-muted-foreground/40 mt-2">
                    Sauvegardé {formatTimeAgo(activity.bookmarked_at)}
                  </p>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Infinite scroll sentinel */}
        <div ref={sentinelRef} className="h-1" />
        {loadingMore && (
          <div className="flex justify-center py-6">
            <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
          </div>
        )}
      </main>
    </div>
  );
}
