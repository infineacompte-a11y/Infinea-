import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import Sidebar from "@/components/Sidebar";
import {
  BarChart3,
  LogOut,
  Crown,
  Mail,
  ChevronRight,
  Settings,
  CreditCard,
} from "lucide-react";
import { toast } from "sonner";
import { API, useAuth, authFetch } from "@/App";

export default function ProfilePage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/login");
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

      {/* Main Content */}
      <main className="lg:ml-64 pt-14 lg:pt-0 pb-8">
        {/* Dark Header */}
        <div className="section-dark-header px-4 lg:px-8 pt-8 lg:pt-10 pb-8">
          <div className="max-w-5xl mx-auto">
            <h1 className="text-display text-3xl lg:text-4xl font-semibold text-white opacity-0 animate-fade-in" data-testid="profile-title">
              Profil
            </h1>
            <p className="text-white/60 text-sm mt-1 opacity-0 animate-fade-in" style={{ animationDelay: "50ms" }}>
              Gérez votre compte et vos préférences
            </p>
          </div>
        </div>

        <div className="px-4 lg:px-8">
        <div className="max-w-3xl mx-auto">
          {/* Profile Card */}
          <Card className="mb-6 hover:border-[#459492]/20 hover:shadow-md hover:-translate-y-0.5 transition-all duration-300 opacity-0 animate-fade-in" style={{ animationFillMode: "forwards" }}>
            <CardContent className="p-6">
              <div className="flex items-center gap-6">
                <div className="avatar-gradient-ring relative flex items-center justify-center">
                  <Avatar className="w-20 h-20 ring-offset-2 ring-offset-background">
                    <AvatarImage src={user?.picture} alt={user?.name} />
                    <AvatarFallback className="bg-primary/10 text-primary text-2xl">
                      {getInitials(user?.name)}
                    </AvatarFallback>
                  </Avatar>
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-1">
                    <h2 className="font-sans font-semibold tracking-tight text-2xl font-semibold" data-testid="profile-name">
                      {user?.name || "Utilisateur"}
                    </h2>
                    {user?.subscription_tier === "premium" && (
                      <Badge className="bg-gradient-to-r from-[#E48C75] to-[#459492] text-white border-0">
                        <Crown className="w-3 h-3 mr-1 text-white" />
                        Premium
                      </Badge>
                    )}
                  </div>
                  <p className="text-muted-foreground flex items-center gap-2">
                    <Mail className="w-4 h-4" />
                    {user?.email}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Subscription Card */}
          <Card className="mb-6 hover:border-[#459492]/20 hover:shadow-md hover:-translate-y-0.5 transition-all duration-300 opacity-0 animate-fade-in" style={{ animationDelay: "100ms", animationFillMode: "forwards" }}>
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

          {/* Stats Summary */}
          <Card className="mb-6 hover:border-[#459492]/20 hover:shadow-md hover:-translate-y-0.5 transition-all duration-300 opacity-0 animate-fade-in" style={{ animationDelay: "200ms", animationFillMode: "forwards" }}>
            <CardHeader>
              <CardTitle className="font-sans font-semibold tracking-tight text-lg">Résumé</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-3 sm:gap-4">
                <div className="stat-card-teal p-3 sm:p-4 rounded-xl bg-gradient-to-br from-[#459492]/20 to-transparent border border-border/50 hover:-translate-y-0.5 transition-all duration-300">
                  <p className="text-2xl font-sans font-semibold tracking-tight font-bold text-primary tabular-nums">
                    {user?.total_time_invested || 0}
                  </p>
                  <p className="text-xs sm:text-sm text-muted-foreground">minutes investies</p>
                </div>
                <div className="stat-card-coral p-3 sm:p-4 rounded-xl bg-gradient-to-br from-[#E48C75]/20 to-transparent border border-border/50 hover:-translate-y-0.5 transition-all duration-300">
                  <p className="text-2xl font-sans font-semibold tracking-tight font-bold text-[#E48C75] tabular-nums">
                    {user?.streak_days || 0}
                  </p>
                  <p className="text-xs sm:text-sm text-muted-foreground">jours de streak</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Actions */}
          <Card className="hover:border-[#459492]/20 hover:shadow-md hover:-translate-y-0.5 transition-all duration-300 opacity-0 animate-fade-in" style={{ animationDelay: "300ms", animationFillMode: "forwards" }}>
            <CardHeader>
              <CardTitle className="font-sans font-semibold tracking-tight text-lg">Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
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
