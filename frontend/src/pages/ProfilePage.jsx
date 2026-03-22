import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  BarChart3,
  Crown,
  Mail,
  ChevronRight,
  CreditCard,
  LogOut,
  Pencil,
  Users,
  Loader2,
} from "lucide-react";
import { useAuth } from "@/App";
import api from "@/lib/api";
import AppLayout from "@/components/AppLayout";

function getInitials(name) {
  if (!name) return "U";
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

export default function ProfilePage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getMyProfile()
      .then(setProfile)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  const p = profile || user || {};

  return (
    <AppLayout>
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="font-heading text-3xl font-semibold">Mon profil</h1>
          <p className="text-muted-foreground">
            Gérez vos informations et votre abonnement
          </p>
        </div>
        <Link to="/profile/edit">
          <Button variant="outline" className="rounded-full">
            <Pencil className="w-4 h-4 mr-2" />
            Modifier
          </Button>
        </Link>
      </div>

      {/* Profile Card */}
      <Card className="mb-6">
        <CardContent className="p-6">
          <div className="flex items-center gap-6">
            <Avatar className="w-20 h-20">
              <AvatarImage src={p.avatar_url || p.picture} alt={p.display_name || p.name} />
              <AvatarFallback className="bg-primary/10 text-primary text-2xl">
                {getInitials(p.display_name || p.name)}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-1">
                <h2 className="font-heading text-2xl font-semibold">
                  {p.display_name || p.name || "Utilisateur"}
                </h2>
                {p.subscription_tier === "premium" && (
                  <Badge className="bg-gradient-to-r from-amber-500 to-orange-500 text-white">
                    <Crown className="w-3 h-3 mr-1" />
                    Premium
                  </Badge>
                )}
              </div>
              {p.bio && <p className="text-muted-foreground mb-2">{p.bio}</p>}
              <p className="text-muted-foreground flex items-center gap-2 text-sm">
                <Mail className="w-4 h-4" />
                {p.email}
              </p>
            </div>
          </div>

          {/* Social counts */}
          {!loading && profile && (
            <div className="flex items-center gap-6 mt-6 pt-6 border-t border-border">
              <Link
                to={`/users/${p.user_id}/followers`}
                className="text-center hover:text-primary transition-colors"
              >
                <span className="font-heading font-bold text-lg block">
                  {profile.followers_count || 0}
                </span>
                <span className="text-xs text-muted-foreground">Followers</span>
              </Link>
              <Link
                to={`/users/${p.user_id}/following`}
                className="text-center hover:text-primary transition-colors"
              >
                <span className="font-heading font-bold text-lg block">
                  {profile.following_count || 0}
                </span>
                <span className="text-xs text-muted-foreground">Suivis</span>
              </Link>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Subscription Card */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="font-heading text-lg flex items-center gap-2">
            <CreditCard className="w-5 h-5" />
            Abonnement
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between p-4 rounded-xl bg-white/5 mb-4">
            <div>
              <p className="font-medium mb-1">
                {p.subscription_tier === "premium" ? "Plan Premium" : "Plan Gratuit"}
              </p>
              <p className="text-sm text-muted-foreground">
                {p.subscription_tier === "premium"
                  ? "Accès illimité à toutes les fonctionnalités"
                  : "Fonctionnalités de base"}
              </p>
            </div>
            <Badge variant={p.subscription_tier === "premium" ? "default" : "secondary"}>
              {p.subscription_tier === "premium" ? "Actif" : "Gratuit"}
            </Badge>
          </div>

          {p.subscription_tier !== "premium" && (
            <Link to="/pricing">
              <Button className="w-full rounded-xl">
                <Crown className="w-5 h-5 mr-2" />
                Passer à Premium
                <ChevronRight className="w-5 h-5 ml-2" />
              </Button>
            </Link>
          )}
        </CardContent>
      </Card>

      {/* Stats Summary */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="font-heading text-lg">Résumé</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-white/5">
              <p className="text-2xl font-heading font-bold text-primary">
                {p.total_time_invested || 0}
              </p>
              <p className="text-sm text-muted-foreground">minutes investies</p>
            </div>
            <div className="p-4 rounded-xl bg-white/5">
              <p className="text-2xl font-heading font-bold text-amber-500">
                {p.streak_days || 0}
              </p>
              <p className="text-sm text-muted-foreground">jours de streak</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Actions */}
      <Card>
        <CardHeader>
          <CardTitle className="font-heading text-lg">Actions</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <Link to="/progress">
            <button className="w-full flex items-center justify-between p-4 rounded-xl hover:bg-white/5 transition-colors">
              <div className="flex items-center gap-3">
                <BarChart3 className="w-5 h-5 text-muted-foreground" />
                <span>Voir mes statistiques</span>
              </div>
              <ChevronRight className="w-5 h-5 text-muted-foreground" />
            </button>
          </Link>
          <Link to="/search">
            <button className="w-full flex items-center justify-between p-4 rounded-xl hover:bg-white/5 transition-colors">
              <div className="flex items-center gap-3">
                <Users className="w-5 h-5 text-muted-foreground" />
                <span>Trouver des utilisateurs</span>
              </div>
              <ChevronRight className="w-5 h-5 text-muted-foreground" />
            </button>
          </Link>
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-between p-4 rounded-xl hover:bg-white/5 transition-colors text-destructive"
          >
            <div className="flex items-center gap-3">
              <LogOut className="w-5 h-5" />
              <span>Se déconnecter</span>
            </div>
            <ChevronRight className="w-5 h-5" />
          </button>
        </CardContent>
      </Card>
    </AppLayout>
  );
}
