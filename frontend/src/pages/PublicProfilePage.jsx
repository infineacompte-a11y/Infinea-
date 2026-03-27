import React, { useState, useEffect, useCallback } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import Sidebar from "@/components/Sidebar";
import FollowButton from "@/components/FollowButton";
import UserCard from "@/components/UserCard";
import {
  Crown,
  Flame,
  Clock,
  Users,
  Award,
  CalendarDays,
  ArrowLeft,
  MessageCircle,
  Zap,
  Trophy,
  Activity,
  UserCheck,
  Circle,
  Target,
  Camera,
  X,
  BookOpen,
  Brain,
  Heart,
  Star,
  ImageIcon,
  Share2,
} from "lucide-react";
import { toast } from "sonner";
import { API, authFetch, useAuth } from "@/App";
import XPProgressBar from "@/components/XPProgressBar";
import SafetyMenu from "@/components/SafetyMenu";
import ActivityHeatmap from "@/components/ActivityHeatmap";

// ── Active status helper (Instagram/Discord benchmark) ──
function activeStatus(lastActive) {
  if (!lastActive) return null;
  const diff = Date.now() - new Date(lastActive).getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 5) return { label: "En ligne", color: "#22c55e" };
  if (minutes < 60) return { label: `Actif il y a ${minutes} min`, color: "#f59e0b" };
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return { label: `Actif il y a ${hours}h`, color: null };
  return null; // > 24h — don't show
}

/**
 * PublicProfilePage — View another user's profile.
 * Pattern: Strava athlete profile + Instagram user page.
 *
 * Route: /users/:userId
 */
export default function PublicProfilePage() {
  const { userId } = useParams();
  const { user: currentUser } = useAuth();
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Followers/Following dialog
  const [listDialog, setListDialog] = useState(null); // "followers" | "following" | null
  const [listData, setListData] = useState([]);
  const [listLoading, setListLoading] = useState(false);

  // Activity timeline
  const [activities, setActivities] = useState([]);
  const [activitiesLoaded, setActivitiesLoaded] = useState(false);

  // Cover photo upload (own profile only)
  const [coverUploading, setCoverUploading] = useState(false);

  const fetchProfile = useCallback(async () => {
    try {
      const res = await authFetch(`${API}/users/${userId}/profile`);
      if (res.status === 404) {
        setError("not_found");
        return;
      }
      if (res.status === 403) {
        setError("private");
        return;
      }
      if (!res.ok) throw new Error("Erreur");
      const data = await res.json();
      setProfile(data);
    } catch {
      toast.error("Impossible de charger le profil");
      setError("network");
    } finally {
      setIsLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  // Fetch activities for timeline
  useEffect(() => {
    if (!userId) return;
    (async () => {
      try {
        const res = await authFetch(`${API}/users/${userId}/activities?limit=10`);
        if (res.ok) {
          const data = await res.json();
          setActivities(data.activities || []);
        }
      } catch { /* silent */ }
      setActivitiesLoaded(true);
    })();
  }, [userId]);

  const handleFollowToggle = (isFollowing) => {
    setProfile((prev) =>
      prev
        ? {
            ...prev,
            is_following: isFollowing,
            followers_count: prev.followers_count + (isFollowing ? 1 : -1),
          }
        : prev
    );
  };

  const handleCoverUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!["image/jpeg", "image/png", "image/webp"].includes(file.type)) {
      toast.error("Format non supporté. Utilisez JPEG, PNG ou WebP.");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      toast.error("L'image ne doit pas dépasser 10 Mo");
      return;
    }
    setCoverUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await authFetch(`${API}/profile/cover-photo`, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) throw new Error("Upload failed");
      const data = await res.json();
      setProfile((prev) => prev ? { ...prev, cover_photo_url: data.cover_photo_url } : prev);
      toast.success("Photo de couverture mise à jour");
    } catch {
      toast.error("Erreur lors de l'upload");
    } finally {
      setCoverUploading(false);
    }
  };

  const handleCoverDelete = async () => {
    try {
      const res = await authFetch(`${API}/profile/cover-photo`, { method: "DELETE" });
      if (!res.ok) throw new Error("Delete failed");
      setProfile((prev) => prev ? { ...prev, cover_photo_url: null } : prev);
      toast.success("Photo de couverture supprimée");
    } catch {
      toast.error("Erreur lors de la suppression");
    }
  };

  const openList = async (type) => {
    setListDialog(type);
    setListLoading(true);
    try {
      const res = await authFetch(`${API}/users/${userId}/${type}`);
      if (!res.ok) throw new Error("Erreur");
      const data = await res.json();
      setListData(data[type] || []);
    } catch {
      toast.error("Impossible de charger la liste");
      setListData([]);
    } finally {
      setListLoading(false);
    }
  };

  const getInitials = (name) => {
    if (!name) return "U";
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  const formatDate = (iso) => {
    if (!iso) return "";
    return new Date(iso).toLocaleDateString("fr-FR", {
      month: "long",
      year: "numeric",
    });
  };

  const timeAgo = (iso) => {
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
  };

  const ACTIVITY_CONFIG = {
    session_completed: { icon: Zap, color: "#459492", getText: (d) => `a terminé "${d.action_title || "une micro-action"}" en ${d.duration || 0} min` },
    badge_earned: { icon: Award, color: "#E48C75", getText: (d) => `a obtenu le badge "${d.badge_name || "nouveau badge"}"` },
    streak_milestone: { icon: Flame, color: "#E48C75", getText: (d) => `a atteint ${d.streak_days} jours de streak !` },
    challenge_completed: { icon: Trophy, color: "#459492", getText: (d) => `a complété le défi "${d.challenge_title || "un défi"}" !` },
  };

  const OBJECTIVE_CATEGORY = {
    learning: { icon: BookOpen, color: "#459492", label: "Apprentissage" },
    productivity: { icon: Target, color: "#E48C75", label: "Productivité" },
    well_being: { icon: Heart, color: "#5DB786", label: "Bien-être" },
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen app-bg-mesh">
        <Sidebar />
        <main className="lg:ml-64 pt-14 lg:pt-0 pb-8">
          <div className="section-dark-header px-4 lg:px-8 pt-8 lg:pt-10 pb-8">
            <div className="max-w-3xl mx-auto">
              <div className="h-8 w-48 bg-white/10 rounded animate-pulse" />
            </div>
          </div>
          <div className="px-4 lg:px-8">
            <div className="max-w-3xl mx-auto space-y-4">
              <div className="h-32 bg-card border border-border/30 rounded-xl animate-pulse" />
              <div className="h-24 bg-card border border-border/30 rounded-xl animate-pulse" />
            </div>
          </div>
        </main>
      </div>
    );
  }

  // Error states
  if (error) {
    return (
      <div className="min-h-screen app-bg-mesh">
        <Sidebar />
        <main className="lg:ml-64 pt-14 lg:pt-0 pb-8">
          <div className="section-dark-header px-4 lg:px-8 pt-8 lg:pt-10 pb-24">
            <div className="max-w-3xl mx-auto" />
          </div>
          <div className="px-4 lg:px-8">
            <div className="max-w-3xl mx-auto">
              <div className="flex flex-col items-center justify-center py-20 text-center">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center mb-4 ring-1 ring-primary/10">
                  <Users className="w-8 h-8 text-primary" />
                </div>
                <h2 className="text-lg font-semibold text-foreground mb-2">
                  {error === "not_found"
                    ? "Utilisateur introuvable"
                    : error === "private"
                    ? "Profil privé"
                    : "Erreur de chargement"}
                </h2>
                <p className="text-muted-foreground text-sm max-w-sm mb-6">
                  {error === "private"
                    ? "Cet utilisateur a choisi de garder son profil privé."
                    : "Vérifiez le lien ou réessayez plus tard."}
                </p>
                <Link to="/search">
                  <Button variant="outline" className="gap-2 rounded-xl">
                    <ArrowLeft className="w-4 h-4" />
                    Retour à la recherche
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </main>
      </div>
    );
  }

  const isOwnProfile = currentUser?.user_id === userId;

  return (
    <div className="min-h-screen app-bg-mesh">
      <Sidebar />
      <main className="lg:ml-64 pt-14 lg:pt-0 pb-8">
        {/* Cover photo banner (Twitter/LinkedIn pattern) */}
        <div className="relative">
          <div className="h-32 sm:h-40 lg:h-48 w-full bg-gradient-to-br from-[#275255] via-[#459492]/60 to-[#275255] relative overflow-hidden">
            {profile.cover_photo_url && (
              <img
                src={profile.cover_photo_url}
                alt=""
                className="absolute inset-0 w-full h-full object-cover"
              />
            )}
            <div className="absolute inset-0 bg-gradient-to-t from-black/30 via-transparent to-black/10" />

            {/* Back button */}
            <div className="absolute top-3 left-3 lg:left-8 z-10">
              <Link
                to="/search"
                className="inline-flex items-center gap-1.5 text-white/70 hover:text-white text-sm bg-black/20 backdrop-blur-sm px-3 py-1.5 rounded-full transition-colors"
              >
                <ArrowLeft className="w-4 h-4" />
                Rechercher
              </Link>
            </div>

            {/* Cover photo actions (own profile only) */}
            {isOwnProfile && (
              <div className="absolute top-3 right-3 lg:right-8 z-10 flex items-center gap-2">
                <label className="cursor-pointer inline-flex items-center gap-1.5 text-white/70 hover:text-white text-xs bg-black/20 backdrop-blur-sm px-3 py-1.5 rounded-full transition-colors">
                  <Camera className="w-3.5 h-3.5" />
                  {coverUploading ? "Upload..." : profile.cover_photo_url ? "Changer" : "Ajouter une couverture"}
                  <input
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    className="hidden"
                    onChange={handleCoverUpload}
                    disabled={coverUploading}
                  />
                </label>
                {profile.cover_photo_url && (
                  <button
                    onClick={handleCoverDelete}
                    className="text-white/50 hover:text-white bg-black/20 backdrop-blur-sm p-1.5 rounded-full transition-colors"
                    title="Supprimer la couverture"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Profile info — avatar overlapping cover bottom edge (Twitter pattern) */}
        <div className="px-4 lg:px-8">
          <div className="max-w-3xl mx-auto">
            {/* Avatar row — pulled up to overlap cover */}
            <div className="-mt-12 mb-3 opacity-0 animate-fade-in" style={{ animationFillMode: "forwards" }}>
              <Avatar className="w-24 h-24 ring-4 ring-background shadow-lg">
                <AvatarImage
                  src={profile.avatar_url}
                  alt={profile.display_name}
                />
                <AvatarFallback className="bg-primary/10 text-primary text-2xl">
                  {getInitials(profile.display_name)}
                </AvatarFallback>
              </Avatar>
            </div>

            {/* Name + info */}
            <div className="mb-4">
              <div className="flex items-center gap-3 mb-0.5 opacity-0 animate-fade-in" style={{ animationDelay: "50ms", animationFillMode: "forwards" }}>
                <h1 className="text-2xl lg:text-3xl font-semibold text-foreground truncate">
                  {profile.display_name}
                </h1>
                {profile.xp && (
                  <XPProgressBar xpData={profile.xp} variant="compact" />
                )}
                {profile.subscription_tier === "premium" && (
                  <Badge className="bg-gradient-to-r from-[#E48C75] to-[#459492] text-white border-0 shrink-0">
                    <Crown className="w-3 h-3 mr-1" />
                    Premium
                  </Badge>
                )}
              </div>
              {profile.username && (
                <p className="text-muted-foreground text-sm opacity-0 animate-fade-in" style={{ animationDelay: "75ms", animationFillMode: "forwards" }}>
                  @{profile.username}
                </p>
              )}
              {/* Mutual follow badge + active status */}
              {!isOwnProfile && (
                <div className="flex items-center gap-2 mt-1.5 flex-wrap opacity-0 animate-fade-in" style={{ animationDelay: "88ms", animationFillMode: "forwards" }}>
                  {profile.is_following && profile.follows_you && (
                    <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-600 bg-emerald-500/10 px-2 py-0.5 rounded-full">
                      <UserCheck className="w-3 h-3" />
                      Suivi mutuel
                    </span>
                  )}
                  {!profile.is_following && profile.follows_you && (
                    <span className="text-[11px] text-muted-foreground">
                      Vous suit
                    </span>
                  )}
                  {(() => {
                    const status = activeStatus(profile.last_active);
                    if (!status) return null;
                    return (
                      <span className="inline-flex items-center gap-1 text-[11px] text-muted-foreground">
                        {status.color && <Circle className="w-2 h-2 fill-current" style={{ color: status.color }} />}
                        {status.label}
                      </span>
                    );
                  })()}
                </div>
              )}
              {profile.bio && (
                <p className="text-muted-foreground text-sm mt-2 opacity-0 animate-fade-in" style={{ animationDelay: "100ms", animationFillMode: "forwards" }}>
                  {profile.bio}
                </p>
              )}
              {/* Mutual followers (Instagram "Suivi par X, Y et Z de tes abonnements") */}
              {!isOwnProfile && profile.mutual_followers?.count > 0 && (
                <div className="flex items-center gap-2 mt-2 opacity-0 animate-fade-in" style={{ animationDelay: "120ms", animationFillMode: "forwards" }}>
                  <div className="flex -space-x-2">
                    {profile.mutual_followers.sample.map((u) => (
                      <Avatar key={u.user_id} className="w-5 h-5 ring-1 ring-background">
                        <AvatarImage src={u.avatar_url} alt={u.display_name} />
                        <AvatarFallback className="bg-muted text-[8px]">
                          {u.display_name?.[0]}
                        </AvatarFallback>
                      </Avatar>
                    ))}
                  </div>
                  <p className="text-[11px] text-muted-foreground">
                    Suivi par{" "}
                    {profile.mutual_followers.sample
                      .map((u) => u.display_name)
                      .join(", ")}
                    {profile.mutual_followers.count > 3 &&
                      ` et ${profile.mutual_followers.count - 3} autre${profile.mutual_followers.count - 3 > 1 ? "s" : ""}`}
                    {" "}que tu suis
                  </p>
                </div>
              )}
              {profile.created_at && (
                <p className="text-muted-foreground/60 text-xs mt-2 flex items-center gap-1 opacity-0 animate-fade-in" style={{ animationDelay: "150ms", animationFillMode: "forwards" }}>
                  <CalendarDays className="w-3 h-3" />
                  Membre depuis {formatDate(profile.created_at)}
                </p>
              )}
            </div>

            {/* Social stats + Follow */}
            <Card className="mb-6 opacity-0 animate-fade-in" style={{ animationDelay: "200ms", animationFillMode: "forwards" }}>
              <CardContent className="p-5">
                <div className="flex items-center justify-between">
                  <div className="flex gap-6">
                    <button
                      onClick={() => openList("followers")}
                      className="text-center hover:opacity-70 transition-opacity"
                    >
                      <p className="text-xl font-semibold tabular-nums text-foreground">
                        {profile.followers_count || 0}
                      </p>
                      <p className="text-xs text-muted-foreground">Abonnés</p>
                    </button>
                    <button
                      onClick={() => openList("following")}
                      className="text-center hover:opacity-70 transition-opacity"
                    >
                      <p className="text-xl font-semibold tabular-nums text-foreground">
                        {profile.following_count || 0}
                      </p>
                      <p className="text-xs text-muted-foreground">Abonnements</p>
                    </button>
                  </div>
                  {!isOwnProfile && (
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        className="gap-1.5 rounded-xl"
                        onClick={() => navigate(`/messages?user=${userId}`)}
                      >
                        <MessageCircle className="w-4 h-4" />
                        Message
                      </Button>
                      <FollowButton
                        userId={userId}
                        initialFollowing={profile.is_following}
                        onToggle={handleFollowToggle}
                      />
                      <Button
                        variant="outline"
                        size="sm"
                        className="gap-1.5 rounded-xl"
                        onClick={() => {
                          const url = `${window.location.origin}/share/profile/${userId}`;
                          navigator.clipboard.writeText(url).then(() => toast.success("Lien copié !")).catch(() => {});
                        }}
                      >
                        <Share2 className="w-4 h-4" />
                      </Button>
                      <SafetyMenu
                        userId={userId}
                        targetType="user"
                        targetId={userId}
                        onBlockChange={(blocked) => {
                          if (blocked) {
                            window.location.href = "/community";
                          }
                        }}
                      />
                    </div>
                  )}
                  {isOwnProfile && (
                    <Link to="/profile">
                      <Button variant="outline" className="rounded-xl">
                        Modifier mon profil
                      </Button>
                    </Link>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* XP & Level — Duolingo-inspired progression */}
            {profile.xp && (
              <div className="mb-6 opacity-0 animate-fade-in" style={{ animationDelay: "250ms", animationFillMode: "forwards" }}>
                <XPProgressBar xpData={profile.xp} variant="full" />
              </div>
            )}

            {/* Stats */}
            {(profile.streak_days != null || profile.total_time_invested != null) && (
              <Card className="mb-6 opacity-0 animate-fade-in" style={{ animationDelay: "300ms", animationFillMode: "forwards" }}>
                <CardHeader>
                  <CardTitle className="font-sans font-semibold tracking-tight text-lg">
                    Statistiques
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-3">
                    {profile.streak_days != null && (
                      <div className="stat-card-coral p-3 rounded-xl bg-gradient-to-br from-[#E48C75]/20 to-transparent border border-border/50">
                        <div className="flex items-center gap-2 mb-1">
                          <Flame className="w-4 h-4 text-[#E48C75]" />
                          <span className="text-xs text-muted-foreground">Streak</span>
                        </div>
                        <p className="text-2xl font-semibold text-[#E48C75] tabular-nums">
                          {profile.streak_days}
                          <span className="text-sm font-normal ml-1">jours</span>
                        </p>
                      </div>
                    )}
                    {profile.total_time_invested != null && (
                      <div className="stat-card-teal p-3 rounded-xl bg-gradient-to-br from-[#459492]/20 to-transparent border border-border/50">
                        <div className="flex items-center gap-2 mb-1">
                          <Clock className="w-4 h-4 text-[#459492]" />
                          <span className="text-xs text-muted-foreground">Temps investi</span>
                        </div>
                        <p className="text-2xl font-semibold text-primary tabular-nums">
                          {profile.total_time_invested}
                          <span className="text-sm font-normal ml-1">min</span>
                        </p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Activity Heatmap (GitHub contributions pattern) */}
            <Card className="mb-6 opacity-0 animate-fade-in" style={{ animationDelay: "320ms", animationFillMode: "forwards" }}>
              <CardHeader className="pb-2">
                <CardTitle className="font-sans font-semibold tracking-tight text-lg flex items-center gap-2">
                  <Activity className="w-5 h-5 text-[#459492]" />
                  Activité
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ActivityHeatmap userId={userId} />
              </CardContent>
            </Card>

            {/* Featured Badges Vitrine (Duolingo/Xbox pattern) */}
            {profile.featured_badges && profile.featured_badges.length > 0 && (
              <Card className="mb-6 opacity-0 animate-fade-in" style={{ animationDelay: "350ms", animationFillMode: "forwards" }}>
                <CardHeader className="pb-3">
                  <CardTitle className="font-sans font-semibold tracking-tight text-lg flex items-center gap-2">
                    <Star className="w-5 h-5 text-[#F5A623]" />
                    Badges en vitrine
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-5 gap-3">
                    {profile.featured_badges.map((badge, i) => (
                      <div
                        key={i}
                        className="flex flex-col items-center text-center gap-1.5"
                        title={badge.description || badge.name}
                      >
                        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#F5A623]/15 to-[#E48C75]/10 border border-[#F5A623]/20 flex items-center justify-center text-xl shadow-sm">
                          {badge.emoji || "🏅"}
                        </div>
                        <span className="text-[10px] text-muted-foreground leading-tight line-clamp-2">
                          {badge.name || badge}
                        </span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* All Badges (if more than featured) */}
            {profile.badges && profile.badges.length > 0 && profile.badges.length > (profile.featured_badges?.length || 0) && (
              <Card className="mb-6 opacity-0 animate-fade-in" style={{ animationDelay: "400ms", animationFillMode: "forwards" }}>
                <CardHeader>
                  <CardTitle className="font-sans font-semibold tracking-tight text-lg flex items-center gap-2">
                    <Award className="w-5 h-5 text-[#E48C75]" />
                    Tous les badges ({profile.badges.length})
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {profile.badges.map((badge, i) => (
                      <Badge
                        key={i}
                        variant="secondary"
                        className="rounded-lg px-3 py-1.5 text-xs"
                      >
                        {badge.emoji || "🏅"} {badge.name || badge}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Objectives in Progress (Strava/Duolingo active goals pattern) */}
            {profile.objectives_in_progress && profile.objectives_in_progress.length > 0 && (
              <Card className="mb-6 opacity-0 animate-fade-in" style={{ animationDelay: "420ms", animationFillMode: "forwards" }}>
                <CardHeader>
                  <CardTitle className="font-sans font-semibold tracking-tight text-lg flex items-center gap-2">
                    <Target className="w-5 h-5 text-[#459492]" />
                    Objectifs en cours
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {profile.objectives_in_progress.map((obj) => {
                      const cat = OBJECTIVE_CATEGORY[obj.category] || OBJECTIVE_CATEGORY.learning;
                      const CatIcon = cat.icon;
                      return (
                        <div
                          key={obj.objective_id}
                          className="flex items-center gap-3 p-3 rounded-xl bg-gradient-to-r from-muted/50 to-transparent border border-border/30"
                        >
                          <div
                            className="w-10 h-10 rounded-lg flex items-center justify-center shrink-0"
                            style={{ backgroundColor: `${cat.color}15` }}
                          >
                            <CatIcon className="w-5 h-5" style={{ color: cat.color }} />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-foreground truncate">
                              {obj.title}
                            </p>
                            <div className="flex items-center gap-2 mt-1">
                              <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
                                <div
                                  className="h-full rounded-full transition-all duration-500"
                                  style={{
                                    width: `${obj.progress_percent}%`,
                                    backgroundColor: cat.color,
                                  }}
                                />
                              </div>
                              <span className="text-[11px] text-muted-foreground tabular-nums shrink-0">
                                {obj.progress_percent}%
                              </span>
                            </div>
                            <div className="flex items-center gap-3 mt-1">
                              <span className="text-[10px] text-muted-foreground">
                                Jour {obj.current_day}/{obj.target_days}
                              </span>
                              {obj.streak_days > 0 && (
                                <span className="text-[10px] text-[#E48C75] flex items-center gap-0.5">
                                  <Flame className="w-3 h-3" />
                                  {obj.streak_days}j
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Activity Timeline */}
            {activitiesLoaded && activities.length > 0 && (
              <Card className="opacity-0 animate-fade-in" style={{ animationDelay: "500ms", animationFillMode: "forwards" }}>
                <CardHeader>
                  <CardTitle className="font-sans font-semibold tracking-tight text-lg flex items-center gap-2">
                    <Activity className="w-5 h-5 text-[#459492]" />
                    Activité récente
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {activities.map((act) => {
                      const cfg = ACTIVITY_CONFIG[act.type] || ACTIVITY_CONFIG.session_completed;
                      const ActIcon = cfg.icon;
                      return (
                        <div key={act.activity_id} className="flex items-start gap-3">
                          <div
                            className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 mt-0.5"
                            style={{ backgroundColor: `${cfg.color}15` }}
                          >
                            <ActIcon className="w-4 h-4" style={{ color: cfg.color }} />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm text-foreground/80">
                              {cfg.getText(act.data || {})}
                            </p>
                            <p className="text-[11px] text-muted-foreground/50 mt-0.5">
                              {timeAgo(act.created_at)}
                            </p>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </main>

      {/* Followers/Following dialog */}
      <Dialog open={listDialog !== null} onOpenChange={() => setListDialog(null)}>
        <DialogContent className="max-w-md max-h-[70vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle>
              {listDialog === "followers" ? "Abonnés" : "Abonnements"}
            </DialogTitle>
          </DialogHeader>
          <div className="flex-1 overflow-y-auto space-y-2 py-2">
            {listLoading ? (
              <div className="flex items-center justify-center py-10">
                <div className="w-8 h-8 border-3 border-primary border-t-transparent rounded-full animate-spin" />
              </div>
            ) : listData.length === 0 ? (
              <p className="text-center text-muted-foreground text-sm py-10">
                {listDialog === "followers"
                  ? "Aucun abonné pour l'instant"
                  : "Ne suit personne pour l'instant"}
              </p>
            ) : (
              listData.map((u) => (
                <UserCard
                  key={u.user_id}
                  user={{
                    user_id: u.user_id,
                    name: u.display_name,
                    username: u.username,
                    picture: u.avatar_url,
                    is_following: u.is_following || false,
                    follows_back: u.follows_back || false,
                  }}
                  currentUserId={currentUser?.user_id}
                  showFollow
                />
              ))
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
