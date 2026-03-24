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
} from "lucide-react";
import { toast } from "sonner";
import { API, authFetch, useAuth } from "@/App";
import SafetyMenu from "@/components/SafetyMenu";

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
        {/* Dark header */}
        <div className="section-dark-header px-4 lg:px-8 pt-8 lg:pt-10 pb-8">
          <div className="max-w-3xl mx-auto">
            <Link
              to="/search"
              className="inline-flex items-center gap-1.5 text-white/50 hover:text-white/80 text-sm mb-4 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Rechercher
            </Link>
            <div className="flex items-center gap-5">
              <div className="avatar-gradient-ring relative flex items-center justify-center opacity-0 animate-fade-in">
                <Avatar className="w-20 h-20 lg:w-24 lg:h-24 ring-offset-2 ring-offset-[#275255]">
                  <AvatarImage
                    src={profile.avatar_url}
                    alt={profile.display_name}
                  />
                  <AvatarFallback className="bg-white/10 text-white text-2xl">
                    {getInitials(profile.display_name)}
                  </AvatarFallback>
                </Avatar>
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-3 mb-1 opacity-0 animate-fade-in" style={{ animationDelay: "50ms" }}>
                  <h1 className="text-display text-2xl lg:text-3xl font-semibold text-white truncate">
                    {profile.display_name}
                  </h1>
                  {profile.subscription_tier === "premium" && (
                    <Badge className="bg-gradient-to-r from-[#E48C75] to-[#459492] text-white border-0 shrink-0">
                      <Crown className="w-3 h-3 mr-1" />
                      Premium
                    </Badge>
                  )}
                </div>
                {profile.username && (
                  <p className="text-white/50 text-sm opacity-0 animate-fade-in" style={{ animationDelay: "75ms" }}>
                    @{profile.username}
                  </p>
                )}
                {profile.bio && (
                  <p className="text-white/60 text-sm mt-1 opacity-0 animate-fade-in" style={{ animationDelay: "100ms" }}>
                    {profile.bio}
                  </p>
                )}
                {profile.created_at && (
                  <p className="text-white/40 text-xs mt-2 flex items-center gap-1 opacity-0 animate-fade-in" style={{ animationDelay: "150ms" }}>
                    <CalendarDays className="w-3 h-3" />
                    Membre depuis {formatDate(profile.created_at)}
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="px-4 lg:px-8">
          <div className="max-w-3xl mx-auto">
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

            {/* Badges */}
            {profile.badges && profile.badges.length > 0 && (
              <Card className="opacity-0 animate-fade-in" style={{ animationDelay: "400ms", animationFillMode: "forwards" }}>
                <CardHeader>
                  <CardTitle className="font-sans font-semibold tracking-tight text-lg flex items-center gap-2">
                    <Award className="w-5 h-5 text-[#E48C75]" />
                    Badges
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
                    is_following: u.is_following || u.follows_back || false,
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
