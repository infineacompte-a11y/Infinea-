import React, { useState, useCallback, useRef, useEffect } from "react";
import { Link } from "react-router-dom";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  Search,
  Users,
  Loader2,
  FileText,
  Flame,
  Award,
  Zap,
  Activity,
  Bookmark,
} from "lucide-react";
import { toast } from "sonner";
import { API, authFetch, useAuth } from "@/App";
import Sidebar from "@/components/Sidebar";
import UserCard from "@/components/UserCard";

// ── Activity type config (lightweight — same as CommunityFeedPage) ──
const ACTIVITY_CONFIG = {
  session_completed: { icon: Zap, color: "#55B3AE", label: "Session" },
  badge_earned: { icon: Award, color: "#F5A623", label: "Badge" },
  streak_milestone: { icon: Flame, color: "#E48C75", label: "Streak" },
  challenge_completed: { icon: Award, color: "#459492", label: "Défi" },
  post: { icon: Activity, color: "#459492", label: "Post" },
};

function timeAgo(iso) {
  if (!iso) return "";
  const diff = Date.now() - new Date(iso).getTime();
  const min = Math.floor(diff / 60000);
  if (min < 1) return "maintenant";
  if (min < 60) return `${min}min`;
  const h = Math.floor(min / 60);
  if (h < 24) return `${h}h`;
  const d = Math.floor(h / 24);
  if (d < 7) return `${d}j`;
  return `${Math.floor(d / 7)}sem`;
}

/**
 * SearchPage — Discover users + search content.
 * Tabs: Membres | Contenu (Instagram search pattern).
 */
export default function SearchPage() {
  const { user } = useAuth();
  const [tab, setTab] = useState("users"); // "users" | "content"
  const [query, setQuery] = useState("");

  // Users search state
  const [userResults, setUserResults] = useState([]);
  const [isSearchingUsers, setIsSearchingUsers] = useState(false);
  const [hasSearchedUsers, setHasSearchedUsers] = useState(false);

  // Content search state
  const [contentResults, setContentResults] = useState([]);
  const [isSearchingContent, setIsSearchingContent] = useState(false);
  const [hasSearchedContent, setHasSearchedContent] = useState(false);
  const [contentCursor, setContentCursor] = useState(null);
  const [contentHasMore, setContentHasMore] = useState(false);

  const debounceRef = useRef(null);

  const searchUsers = useCallback(async (q) => {
    if (q.length < 2) {
      setUserResults([]);
      setHasSearchedUsers(false);
      return;
    }
    setIsSearchingUsers(true);
    try {
      const res = await authFetch(`${API}/users/search?q=${encodeURIComponent(q)}&limit=20`);
      if (res.ok) {
        const data = await res.json();
        setUserResults(data.users || []);
        setHasSearchedUsers(true);
      }
    } catch {
      toast.error("Erreur lors de la recherche");
    } finally {
      setIsSearchingUsers(false);
    }
  }, []);

  const searchContent = useCallback(async (q, cursorVal = null) => {
    if (q.length < 2) {
      setContentResults([]);
      setHasSearchedContent(false);
      return;
    }
    if (!cursorVal) setIsSearchingContent(true);
    try {
      const params = new URLSearchParams({ q, limit: "20" });
      if (cursorVal) params.set("cursor", cursorVal);
      const res = await authFetch(`${API}/feed/search?${params}`);
      if (res.ok) {
        const data = await res.json();
        if (cursorVal) {
          setContentResults((prev) => [...prev, ...(data.activities || [])]);
        } else {
          setContentResults(data.activities || []);
        }
        setContentCursor(data.next_cursor);
        setContentHasMore(data.has_more);
        setHasSearchedContent(true);
      }
    } catch {
      toast.error("Erreur lors de la recherche");
    } finally {
      setIsSearchingContent(false);
    }
  }, []);

  const doSearch = useCallback((q) => {
    if (tab === "users") searchUsers(q);
    else searchContent(q);
  }, [tab, searchUsers, searchContent]);

  const handleInputChange = (e) => {
    const val = e.target.value;
    setQuery(val);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => doSearch(val.trim()), 350);
  };

  const handleTabChange = (newTab) => {
    if (newTab === tab) return;
    setTab(newTab);
    // Re-search with current query in the new tab
    if (query.trim().length >= 2) {
      if (newTab === "users" && !hasSearchedUsers) searchUsers(query.trim());
      if (newTab === "content" && !hasSearchedContent) searchContent(query.trim());
    }
  };

  const handleBookmark = async (activityId) => {
    try {
      const res = await authFetch(`${API}/activities/${activityId}/bookmark`, { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        setContentResults((prev) =>
          prev.map((a) =>
            a.activity_id === activityId ? { ...a, bookmarked: data.bookmarked } : a
          )
        );
        toast.success(data.bookmarked ? "Sauvegardé" : "Retiré des sauvegardés");
      }
    } catch {
      toast.error("Erreur");
    }
  };

  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, []);

  const isSearching = tab === "users" ? isSearchingUsers : isSearchingContent;
  const hasSearched = tab === "users" ? hasSearchedUsers : hasSearchedContent;

  return (
    <div className="min-h-screen app-bg-mesh">
      <Sidebar />
      <main className="lg:ml-64 pt-14 lg:pt-0 pb-8">
        {/* Dark header */}
        <div className="section-dark-header px-4 lg:px-8 pt-8 lg:pt-10 pb-8">
          <div className="max-w-3xl mx-auto">
            <h1 className="text-display text-3xl lg:text-4xl font-semibold text-white opacity-0 animate-fade-in">
              Rechercher
            </h1>
            <p className="text-white/60 text-sm mt-1 opacity-0 animate-fade-in" style={{ animationDelay: "50ms" }}>
              {tab === "users"
                ? "Trouvez des utilisateurs et suivez leur progression"
                : "Cherchez dans les publications de la communauté"}
            </p>

            {/* Search input */}
            <div className="relative mt-5 opacity-0 animate-fade-in" style={{ animationDelay: "100ms" }}>
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40" />
              <Input
                type="text"
                value={query}
                onChange={handleInputChange}
                placeholder={tab === "users" ? "Nom ou @identifiant..." : "Rechercher dans les posts..."}
                autoComplete="off"
                autoFocus
                className="pl-10 h-12 rounded-xl bg-[#1a3a3d] border-white/15 text-white placeholder:text-white/40 focus:bg-[#1f4447] focus:border-white/30 caret-white transition-all"
              />
              {isSearching && (
                <Loader2 className="absolute right-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40 animate-spin" />
              )}
            </div>

            {/* Tab switcher */}
            <div
              className="opacity-0 animate-fade-in flex mt-4 bg-white/10 rounded-xl p-1 gap-1"
              style={{ animationDelay: "120ms", animationFillMode: "forwards" }}
            >
              <button
                onClick={() => handleTabChange("users")}
                className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                  tab === "users"
                    ? "bg-white text-[#275255] shadow-sm"
                    : "text-white/70 hover:text-white hover:bg-white/10"
                }`}
              >
                <Users className="w-3.5 h-3.5" />
                Membres
              </button>
              <button
                onClick={() => handleTabChange("content")}
                className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                  tab === "content"
                    ? "bg-white text-[#275255] shadow-sm"
                    : "text-white/70 hover:text-white hover:bg-white/10"
                }`}
              >
                <FileText className="w-3.5 h-3.5" />
                Contenu
              </button>
            </div>
          </div>
        </div>

        <div className="px-4 lg:px-8">
          <div className="max-w-3xl mx-auto">

            {/* ── Users tab ── */}
            {tab === "users" && (
              <>
                {hasSearchedUsers && userResults.length === 0 && !isSearchingUsers && (
                  <div className="flex flex-col items-center justify-center py-16 text-center opacity-0 animate-fade-in" style={{ animationFillMode: "forwards" }}>
                    <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center mb-4 ring-1 ring-primary/10">
                      <Users className="w-7 h-7 text-primary" />
                    </div>
                    <h2 className="text-base font-semibold text-foreground mb-1">Aucun résultat</h2>
                    <p className="text-muted-foreground text-sm max-w-xs">
                      Essayez un autre nom ou vérifiez l'orthographe.
                    </p>
                  </div>
                )}

                {!hasSearchedUsers && !isSearchingUsers && (
                  <div className="flex flex-col items-center justify-center py-16 text-center opacity-0 animate-fade-in" style={{ animationDelay: "200ms", animationFillMode: "forwards" }}>
                    <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center mb-4 ring-1 ring-primary/10">
                      <Search className="w-7 h-7 text-primary" />
                    </div>
                    <h2 className="text-base font-semibold text-foreground mb-1">Découvrez la communauté</h2>
                    <p className="text-muted-foreground text-sm max-w-xs">
                      Tapez au moins 2 caractères pour rechercher des utilisateurs.
                    </p>
                  </div>
                )}

                {userResults.length > 0 && (
                  <div className="space-y-2 opacity-0 animate-fade-in" style={{ animationFillMode: "forwards" }}>
                    <p className="text-xs text-muted-foreground mb-3">
                      {userResults.length} résultat{userResults.length > 1 ? "s" : ""}
                    </p>
                    {userResults.map((u, index) => (
                      <div
                        key={u.user_id}
                        className="opacity-0 animate-fade-in"
                        style={{ animationDelay: `${index * 50}ms`, animationFillMode: "forwards" }}
                      >
                        <UserCard
                          user={{
                            user_id: u.user_id,
                            name: u.display_name,
                            username: u.username,
                            picture: u.avatar_url,
                            is_following: u.is_following || false,
                          }}
                          currentUserId={user?.user_id}
                        />
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}

            {/* ── Content tab ── */}
            {tab === "content" && (
              <>
                {hasSearchedContent && contentResults.length === 0 && !isSearchingContent && (
                  <div className="flex flex-col items-center justify-center py-16 text-center opacity-0 animate-fade-in" style={{ animationFillMode: "forwards" }}>
                    <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center mb-4 ring-1 ring-primary/10">
                      <FileText className="w-7 h-7 text-primary" />
                    </div>
                    <h2 className="text-base font-semibold text-foreground mb-1">Aucun résultat</h2>
                    <p className="text-muted-foreground text-sm max-w-xs">
                      Aucun post ne correspond à votre recherche.
                    </p>
                  </div>
                )}

                {!hasSearchedContent && !isSearchingContent && (
                  <div className="flex flex-col items-center justify-center py-16 text-center opacity-0 animate-fade-in" style={{ animationDelay: "200ms", animationFillMode: "forwards" }}>
                    <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center mb-4 ring-1 ring-primary/10">
                      <FileText className="w-7 h-7 text-primary" />
                    </div>
                    <h2 className="text-base font-semibold text-foreground mb-1">Rechercher du contenu</h2>
                    <p className="text-muted-foreground text-sm max-w-xs">
                      Tapez au moins 2 caractères pour chercher dans les publications.
                    </p>
                  </div>
                )}

                {contentResults.length > 0 && (
                  <div className="space-y-2 opacity-0 animate-fade-in" style={{ animationFillMode: "forwards" }}>
                    <p className="text-xs text-muted-foreground mb-3">
                      {contentResults.length} résultat{contentResults.length > 1 ? "s" : ""}
                      {contentHasMore && "+"}
                    </p>
                    {contentResults.map((activity, index) => {
                      const config = ACTIVITY_CONFIG[activity.type] || ACTIVITY_CONFIG.post;
                      const Icon = config.icon;

                      return (
                        <Card
                          key={activity.activity_id}
                          className="opacity-0 animate-fade-in overflow-hidden border-border/40 shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-300"
                          style={{ animationDelay: `${index * 40}ms`, animationFillMode: "forwards" }}
                        >
                          <CardContent className="p-4">
                            {/* Author row */}
                            <div className="flex items-center gap-3 mb-2">
                              <Link to={`/users/${activity.user_id}`}>
                                <Avatar className="w-8 h-8 ring-2 ring-background">
                                  <AvatarImage src={activity.user_avatar} />
                                  <AvatarFallback className="text-[10px] bg-muted">
                                    {(activity.user_name || "?")[0]}
                                  </AvatarFallback>
                                </Avatar>
                              </Link>
                              <div className="flex-1 min-w-0">
                                <Link
                                  to={`/users/${activity.user_id}`}
                                  className="text-sm font-medium hover:underline"
                                >
                                  {activity.user_name}
                                </Link>
                                <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
                                  <span>{timeAgo(activity.created_at)}</span>
                                  <span className="flex items-center gap-0.5" style={{ color: config.color }}>
                                    <Icon className="w-2.5 h-2.5" />
                                    {config.label}
                                  </span>
                                </div>
                              </div>
                              <button
                                onClick={(e) => { e.stopPropagation(); handleBookmark(activity.activity_id); }}
                                className={`p-1.5 rounded-full transition-colors ${
                                  activity.bookmarked
                                    ? "text-primary"
                                    : "text-muted-foreground hover:text-foreground"
                                }`}
                              >
                                <Bookmark className="w-3.5 h-3.5" fill={activity.bookmarked ? "currentColor" : "none"} />
                              </button>
                            </div>

                            {/* Content with highlighted search match */}
                            {activity.content && (
                              <p className="text-sm text-foreground/90 whitespace-pre-wrap leading-relaxed line-clamp-3">
                                {activity.content}
                              </p>
                            )}

                            {/* Images preview */}
                            {activity.images?.length > 0 && (
                              <div className="flex gap-1 mt-2">
                                {activity.images.slice(0, 3).map((img, i) => (
                                  <img
                                    key={i}
                                    src={img.thumbnail_url || img.image_url}
                                    alt=""
                                    className="w-16 h-16 object-cover rounded-lg"
                                    loading="lazy"
                                  />
                                ))}
                                {activity.images.length > 3 && (
                                  <div className="w-16 h-16 rounded-lg bg-muted flex items-center justify-center text-xs text-muted-foreground">
                                    +{activity.images.length - 3}
                                  </div>
                                )}
                              </div>
                            )}

                            {/* Engagement stats */}
                            <div className="flex items-center gap-3 mt-2 text-[10px] text-muted-foreground">
                              {activity.reaction_counts && Object.values(activity.reaction_counts).some(v => v > 0) && (
                                <span>{Object.values(activity.reaction_counts).reduce((a, b) => a + b, 0)} réactions</span>
                              )}
                              {activity.comment_count > 0 && (
                                <span>{activity.comment_count} commentaire{activity.comment_count > 1 ? "s" : ""}</span>
                              )}
                            </div>
                          </CardContent>
                        </Card>
                      );
                    })}

                    {/* Load more */}
                    {contentHasMore && (
                      <button
                        onClick={() => searchContent(query.trim(), contentCursor)}
                        className="w-full py-3 text-sm text-primary hover:text-primary/80 transition-colors"
                      >
                        Charger plus de résultats
                      </button>
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
