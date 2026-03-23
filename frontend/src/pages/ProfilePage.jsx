import React, { useState, useEffect, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Switch } from "@/components/ui/switch";
import Sidebar from "@/components/Sidebar";
import {
  BarChart3,
  LogOut,
  Crown,
  Mail,
  ChevronRight,
  Settings,
  CreditCard,
  Users,
  AtSign,
  User,
  Flame,
  Clock,
  Eye,
  EyeOff,
  Copy,
  Check,
} from "lucide-react";
import { toast } from "sonner";
import { API, useAuth, authFetch } from "@/App";

export default function ProfilePage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [socialStats, setSocialStats] = useState(null);
  const [privacySettings, setPrivacySettings] = useState(null);
  const [copiedUsername, setCopiedUsername] = useState(false);

  // Fetch social stats (followers/following counts)
  const fetchSocialStats = useCallback(async () => {
    if (!user?.user_id) return;
    try {
      const res = await authFetch(`${API}/users/${user.user_id}/profile`);
      if (res.ok) {
        const data = await res.json();
        setSocialStats({
          followers_count: data.followers_count || 0,
          following_count: data.following_count || 0,
        });
      }
    } catch { /* silent */ }
  }, [user?.user_id]);

  // Fetch privacy settings
  const fetchPrivacy = useCallback(async () => {
    try {
      const res = await authFetch(`${API}/profile/privacy`);
      if (res.ok) {
        const data = await res.json();
        setPrivacySettings(data);
      }
    } catch { /* silent */ }
  }, []);

  useEffect(() => {
    fetchSocialStats();
    fetchPrivacy();
  }, [fetchSocialStats, fetchPrivacy]);

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  const handlePrivacyToggle = async (field, value) => {
    const prev = { ...privacySettings };
    setPrivacySettings((s) => ({ ...s, [field]: value }));
    try {
      const res = await authFetch(`${API}/profile/privacy`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...privacySettings, [field]: value }),
      });
      if (!res.ok) {
        setPrivacySettings(prev);
        toast.error("Erreur lors de la mise à jour");
      }
    } catch {
      setPrivacySettings(prev);
      toast.error("Erreur de connexion");
    }
  };

  const copyUsername = () => {
    if (user?.username) {
      navigator.clipboard.writeText(`@${user.username}`);
      setCopiedUsername(true);
      setTimeout(() => setCopiedUsername(false), 2000);
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

  return (
    <div className="min-h-screen app-bg-mesh">
      <Sidebar />
      <main className="lg:ml-64 pt-14 lg:pt-0 pb-8">
        {/* Dark Header */}
        <div className="section-dark-header px-4 lg:px-8 pt-8 lg:pt-10 pb-8">
          <div className="max-w-3xl mx-auto">
            <div className="flex items-center gap-5">
              <div className="avatar-gradient-ring relative flex items-center justify-center opacity-0 animate-fade-in">
                <Avatar className="w-20 h-20 lg:w-24 lg:h-24 ring-offset-2 ring-offset-[#275255]">
                  <AvatarImage src={user?.picture} alt={user?.name} />
                  <AvatarFallback className="bg-white/10 text-white text-2xl">
                    {getInitials(user?.name)}
                  </AvatarFallback>
                </Avatar>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-3 mb-1 opacity-0 animate-fade-in" style={{ animationDelay: "50ms" }}>
                  <h1 className="text-display text-2xl lg:text-3xl font-semibold text-white truncate">
                    {user?.name || "Utilisateur"}
                  </h1>
                  {user?.subscription_tier === "premium" && (
                    <Badge className="bg-gradient-to-r from-[#E48C75] to-[#459492] text-white border-0 shrink-0">
                      <Crown className="w-3 h-3 mr-1" />
                      Premium
                    </Badge>
                  )}
                </div>
                {user?.username && (
                  <button
                    onClick={copyUsername}
                    className="flex items-center gap-1.5 text-white/50 hover:text-white/80 transition-colors opacity-0 animate-fade-in"
                    style={{ animationDelay: "75ms" }}
                    title="Copier l'identifiant"
                  >
                    <AtSign className="w-3.5 h-3.5" />
                    <span className="text-sm">{user.username}</span>
                    {copiedUsername ? (
                      <Check className="w-3 h-3 text-[#5DB786]" />
                    ) : (
                      <Copy className="w-3 h-3 opacity-50" />
                    )}
                  </button>
                )}
                <p className="text-white/40 text-xs mt-1 flex items-center gap-1 opacity-0 animate-fade-in" style={{ animationDelay: "100ms" }}>
                  <Mail className="w-3 h-3" />
                  {user?.email}
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="px-4 lg:px-8">
          <div className="max-w-3xl mx-auto">
            {/* Social stats — prominent */}
            <Card className="mb-6 opacity-0 animate-fade-in" style={{ animationDelay: "150ms", animationFillMode: "forwards" }}>
              <CardContent className="p-5">
                <div className="flex items-center justify-between">
                  <div className="flex gap-8">
                    <Link
                      to={`/users/${user?.user_id}`}
                      className="text-center hover:opacity-70 transition-opacity"
                    >
                      <p className="text-2xl font-semibold tabular-nums text-foreground">
                        {socialStats?.followers_count ?? "—"}
                      </p>
                      <p className="text-xs text-muted-foreground mt-0.5">Abonnés</p>
                    </Link>
                    <Link
                      to={`/users/${user?.user_id}`}
                      className="text-center hover:opacity-70 transition-opacity"
                    >
                      <p className="text-2xl font-semibold tabular-nums text-foreground">
                        {socialStats?.following_count ?? "—"}
                      </p>
                      <p className="text-xs text-muted-foreground mt-0.5">Abonnements</p>
                    </Link>
                  </div>
                  <Link to={`/users/${user?.user_id}`}>
                    <Button variant="outline" className="rounded-xl gap-2">
                      <Eye className="w-4 h-4" />
                      Voir mon profil public
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>

            {/* Stats Summary */}
            <Card className="mb-6 opacity-0 animate-fade-in" style={{ animationDelay: "200ms", animationFillMode: "forwards" }}>
              <CardContent className="p-5">
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 rounded-xl bg-gradient-to-br from-[#459492]/20 to-transparent border border-border/50">
                    <div className="flex items-center gap-2 mb-1">
                      <Clock className="w-4 h-4 text-[#459492]" />
                      <span className="text-xs text-muted-foreground">Temps investi</span>
                    </div>
                    <p className="text-2xl font-semibold text-primary tabular-nums">
                      {user?.total_time_invested || 0}
                      <span className="text-sm font-normal ml-1">min</span>
                    </p>
                  </div>
                  <div className="p-3 rounded-xl bg-gradient-to-br from-[#E48C75]/20 to-transparent border border-border/50">
                    <div className="flex items-center gap-2 mb-1">
                      <Flame className="w-4 h-4 text-[#E48C75]" />
                      <span className="text-xs text-muted-foreground">Streak</span>
                    </div>
                    <p className="text-2xl font-semibold text-[#E48C75] tabular-nums">
                      {user?.streak_days || 0}
                      <span className="text-sm font-normal ml-1">jours</span>
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Privacy settings */}
            {privacySettings && (
              <Card className="mb-6 opacity-0 animate-fade-in" style={{ animationDelay: "250ms", animationFillMode: "forwards" }}>
                <CardHeader>
                  <CardTitle className="font-sans font-semibold tracking-tight text-lg flex items-center gap-2">
                    {privacySettings.profile_visible ? (
                      <Eye className="w-5 h-5 text-[#459492]" />
                    ) : (
                      <EyeOff className="w-5 h-5 text-muted-foreground" />
                    )}
                    Visibilité du compte
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium">Compte public</p>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {privacySettings.profile_visible
                          ? "Tout le monde peut voir votre profil"
                          : "Seuls vos abonnés peuvent voir votre profil"}
                      </p>
                    </div>
                    <Switch
                      checked={privacySettings.profile_visible}
                      onCheckedChange={(v) => handlePrivacyToggle("profile_visible", v)}
                    />
                  </div>
                  <div className="h-px bg-border/50" />
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium">Afficher les statistiques</p>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        Streak et temps investi visibles sur votre profil public
                      </p>
                    </div>
                    <Switch
                      checked={privacySettings.show_stats}
                      onCheckedChange={(v) => handlePrivacyToggle("show_stats", v)}
                    />
                  </div>
                  <div className="h-px bg-border/50" />
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium">Afficher les badges</p>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        Vos badges sont visibles sur votre profil public
                      </p>
                    </div>
                    <Switch
                      checked={privacySettings.show_badges}
                      onCheckedChange={(v) => handlePrivacyToggle("show_badges", v)}
                    />
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Subscription Card */}
            <Card className="mb-6 opacity-0 animate-fade-in" style={{ animationDelay: "300ms", animationFillMode: "forwards" }}>
              <CardHeader>
                <CardTitle className="font-sans font-semibold tracking-tight text-lg flex items-center gap-2">
                  <CreditCard className="w-5 h-5" />
                  Abonnement
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between p-4 rounded-xl bg-gradient-to-br from-[#459492]/20 to-transparent border border-border/50 mb-4">
                  <div>
                    <p className="font-medium mb-1">
                      {user?.subscription_tier === "premium" ? "Plan Premium" : "Plan Gratuit"}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {user?.subscription_tier === "premium"
                        ? "Accès illimité à toutes les fonctionnalités"
                        : "Fonctionnalités de base"}
                    </p>
                  </div>
                  <Badge
                    variant={user?.subscription_tier === "premium" ? "default" : "secondary"}
                    className={user?.subscription_tier === "premium" ? "bg-[#5DB786]/40 text-[#5DB786] border-0" : ""}
                  >
                    {user?.subscription_tier === "premium" ? "Actif" : "Gratuit"}
                  </Badge>
                </div>

                {user?.subscription_tier === "premium" ? (
                  <Button
                    variant="outline"
                    className="w-full rounded-xl shadow-md"
                    onClick={async () => {
                      try {
                        const res = await authFetch(`${API}/premium/portal`, { method: "POST" });
                        if (res.ok) {
                          const data = await res.json();
                          window.open(data.url, "_blank");
                        } else {
                          toast.error("Erreur lors de l'ouverture du portail");
                        }
                      } catch {
                        toast.error("Erreur de connexion");
                      }
                    }}
                  >
                    <Settings className="w-5 h-5 mr-2" />
                    Gérer mon abonnement
                  </Button>
                ) : (
                  <Link to="/pricing">
                    <Button className="btn-premium-shimmer w-full rounded-xl shadow-md hover:shadow-lg transition-shadow" data-testid="upgrade-btn">
                      <Crown className="w-5 h-5 mr-2" />
                      Passer à Premium
                      <ChevronRight className="w-5 h-5 ml-2" />
                    </Button>
                  </Link>
                )}
              </CardContent>
            </Card>

            {/* Actions */}
            <Card className="opacity-0 animate-fade-in" style={{ animationDelay: "350ms", animationFillMode: "forwards" }}>
              <CardContent className="p-4 space-y-1">
                <Link to="/progress">
                  <Button
                    variant="ghost"
                    className="group w-full justify-start gap-3 h-12 rounded-xl"
                  >
                    <BarChart3 className="w-5 h-5 text-muted-foreground" />
                    <span className="flex-1 text-left">Voir mes statistiques</span>
                    <ChevronRight className="w-5 h-5 text-muted-foreground group-hover:translate-x-1 transition-transform" />
                  </Button>
                </Link>
                <Button
                  variant="ghost"
                  onClick={handleLogout}
                  className="group w-full justify-start gap-3 h-12 rounded-xl text-destructive hover:bg-destructive/10"
                  data-testid="profile-logout-btn"
                >
                  <LogOut className="w-5 h-5" />
                  <span className="flex-1 text-left">Se déconnecter</span>
                  <ChevronRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
