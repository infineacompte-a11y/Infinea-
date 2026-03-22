import React, { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  TrendingUp,
  Flame,
  UserPlus,
  UserMinus,
  Users,
  Award,
  MessageCircle,
  ShieldBan,
  ShieldCheck,
  Loader2,
  AlertTriangle,
} from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api";
import { useAuth } from "@/App";
import AppLayout from "@/components/AppLayout";
import UserCard from "@/components/UserCard";

function getInitials(name) {
  if (!name) return "U";
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

export default function PublicProfilePage() {
  const { userId } = useParams();
  const { user: me } = useAuth();
  const navigate = useNavigate();

  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [followLoading, setFollowLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("about");

  // Followers / following lists
  const [followers, setFollowers] = useState([]);
  const [following, setFollowing] = useState([]);
  const [followersTotal, setFollowersTotal] = useState(0);
  const [followingTotal, setFollowingTotal] = useState(0);

  // If viewing own profile, redirect
  useEffect(() => {
    if (me && userId === me.user_id) {
      navigate("/profile", { replace: true });
    }
  }, [me, userId, navigate]);

  const fetchProfile = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getPublicProfile(userId);
      setProfile(data);
    } catch (err) {
      if (err.status === 403) {
        setError("private");
      } else if (err.status === 404) {
        setError("not_found");
      } else {
        setError("generic");
      }
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  // Load followers/following when tabs change
  useEffect(() => {
    if (activeTab === "followers") {
      api.getFollowers(userId).then((data) => {
        setFollowers(data.followers);
        setFollowersTotal(data.total);
      }).catch(() => {});
    } else if (activeTab === "following") {
      api.getFollowing(userId).then((data) => {
        setFollowing(data.following);
        setFollowingTotal(data.total);
      }).catch(() => {});
    }
  }, [activeTab, userId]);

  const handleFollow = async () => {
    setFollowLoading(true);
    try {
      if (profile.is_following) {
        await api.unfollow(userId);
        setProfile((p) => ({
          ...p,
          is_following: false,
          followers_count: p.followers_count - 1,
        }));
        toast.success("Vous ne suivez plus cet utilisateur");
      } else {
        await api.follow(userId);
        setProfile((p) => ({
          ...p,
          is_following: true,
          followers_count: p.followers_count + 1,
        }));
        toast.success("Vous suivez cet utilisateur");
      }
    } catch (err) {
      toast.error(err.message);
    } finally {
      setFollowLoading(false);
    }
  };

  const handleBlock = async () => {
    try {
      await api.block(userId);
      toast.success("Utilisateur bloqué");
      navigate(-1);
    } catch (err) {
      toast.error(err.message);
    }
  };

  if (loading) {
    return (
      <AppLayout>
        <div className="flex items-center justify-center py-32">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      </AppLayout>
    );
  }

  if (error) {
    return (
      <AppLayout>
        <div className="flex flex-col items-center justify-center py-32 text-center">
          {error === "private" ? (
            <>
              <ShieldCheck className="w-16 h-16 text-muted-foreground mb-4" />
              <h2 className="font-heading text-2xl font-semibold mb-2">Profil privé</h2>
              <p className="text-muted-foreground">Cet utilisateur a rendu son profil privé.</p>
            </>
          ) : error === "not_found" ? (
            <>
              <AlertTriangle className="w-16 h-16 text-muted-foreground mb-4" />
              <h2 className="font-heading text-2xl font-semibold mb-2">Utilisateur introuvable</h2>
              <p className="text-muted-foreground">Ce profil n'existe pas ou a été supprimé.</p>
            </>
          ) : (
            <>
              <AlertTriangle className="w-16 h-16 text-destructive mb-4" />
              <h2 className="font-heading text-2xl font-semibold mb-2">Erreur</h2>
              <p className="text-muted-foreground">Impossible de charger ce profil.</p>
            </>
          )}
          <Button variant="outline" className="mt-6" onClick={() => navigate(-1)}>
            Retour
          </Button>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      {/* Profile Header */}
      <Card className="mb-6">
        <CardContent className="p-6">
          <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6">
            <Avatar className="w-24 h-24">
              <AvatarImage src={profile.avatar_url} alt={profile.display_name} />
              <AvatarFallback className="bg-primary/10 text-primary text-3xl">
                {getInitials(profile.display_name)}
              </AvatarFallback>
            </Avatar>

            <div className="flex-1 text-center sm:text-left">
              <h1 className="font-heading text-2xl font-semibold mb-1">
                {profile.display_name}
              </h1>
              {profile.bio && (
                <p className="text-muted-foreground mb-4 max-w-lg">{profile.bio}</p>
              )}

              {/* Social counts */}
              <div className="flex items-center justify-center sm:justify-start gap-6 mb-4">
                <button
                  onClick={() => setActiveTab("followers")}
                  className="text-center hover:text-primary transition-colors"
                >
                  <span className="font-heading font-bold text-lg block">
                    {profile.followers_count}
                  </span>
                  <span className="text-xs text-muted-foreground">Followers</span>
                </button>
                <button
                  onClick={() => setActiveTab("following")}
                  className="text-center hover:text-primary transition-colors"
                >
                  <span className="font-heading font-bold text-lg block">
                    {profile.following_count}
                  </span>
                  <span className="text-xs text-muted-foreground">Suivis</span>
                </button>
              </div>

              {/* Action buttons */}
              <div className="flex items-center justify-center sm:justify-start gap-3">
                <Button
                  variant={profile.is_following ? "outline" : "default"}
                  className="rounded-full"
                  disabled={followLoading}
                  onClick={handleFollow}
                >
                  {followLoading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : profile.is_following ? (
                    <>
                      <UserMinus className="w-4 h-4 mr-2" />
                      Suivi
                    </>
                  ) : (
                    <>
                      <UserPlus className="w-4 h-4 mr-2" />
                      Suivre
                    </>
                  )}
                </Button>
                <Link to={`/messages/new?to=${userId}`}>
                  <Button variant="outline" className="rounded-full">
                    <MessageCircle className="w-4 h-4 mr-2" />
                    Message
                  </Button>
                </Link>
                <Button
                  variant="ghost"
                  size="icon"
                  className="rounded-full text-muted-foreground hover:text-destructive"
                  onClick={handleBlock}
                  title="Bloquer"
                >
                  <ShieldBan className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Stats */}
      {(profile.streak_days !== undefined || profile.total_time_invested !== undefined) && (
        <div className="grid grid-cols-2 gap-4 mb-6">
          {profile.total_time_invested !== undefined && (
            <Card>
              <CardContent className="p-4 flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                  <TrendingUp className="w-5 h-5 text-primary" />
                </div>
                <div>
                  <p className="text-2xl font-heading font-bold">{profile.total_time_invested}</p>
                  <p className="text-xs text-muted-foreground">min investies</p>
                </div>
              </CardContent>
            </Card>
          )}
          {profile.streak_days !== undefined && (
            <Card>
              <CardContent className="p-4 flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-amber-500/10 flex items-center justify-center">
                  <Flame className="w-5 h-5 text-amber-500" />
                </div>
                <div>
                  <p className="text-2xl font-heading font-bold">{profile.streak_days}</p>
                  <p className="text-xs text-muted-foreground">jours de streak</p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Tabs: About / Badges / Followers / Following */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="w-full grid grid-cols-3 mb-6">
          <TabsTrigger value="about">Badges</TabsTrigger>
          <TabsTrigger value="followers">
            Followers {profile.followers_count > 0 && `(${profile.followers_count})`}
          </TabsTrigger>
          <TabsTrigger value="following">
            Suivis {profile.following_count > 0 && `(${profile.following_count})`}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="about">
          {profile.badges && profile.badges.length > 0 ? (
            <Card>
              <CardHeader>
                <CardTitle className="font-heading text-lg flex items-center gap-2">
                  <Award className="w-5 h-5" />
                  Badges ({profile.badges.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-3">
                  {profile.badges.map((badge) => (
                    <Badge
                      key={badge.badge_id || badge}
                      variant="secondary"
                      className="py-2 px-4 text-sm"
                    >
                      {badge.name || badge}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="text-center py-12 text-muted-foreground">
              <Award className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>Pas encore de badges visibles</p>
            </div>
          )}
        </TabsContent>

        <TabsContent value="followers">
          {followers.length > 0 ? (
            <Card>
              <CardContent className="p-2">
                {followers.map((u) => (
                  <UserCard
                    key={u.user_id}
                    user={u}
                    isFollowing={u.is_following}
                    subtitle={u.is_following ? "Suivi" : undefined}
                  />
                ))}
              </CardContent>
            </Card>
          ) : (
            <div className="text-center py-12 text-muted-foreground">
              <Users className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>Aucun follower pour le moment</p>
            </div>
          )}
        </TabsContent>

        <TabsContent value="following">
          {following.length > 0 ? (
            <Card>
              <CardContent className="p-2">
                {following.map((u) => (
                  <UserCard
                    key={u.user_id}
                    user={u}
                    subtitle={u.follows_back ? "Suit en retour" : undefined}
                  />
                ))}
              </CardContent>
            </Card>
          ) : (
            <div className="text-center py-12 text-muted-foreground">
              <Users className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>Ne suit personne pour le moment</p>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </AppLayout>
  );
}
