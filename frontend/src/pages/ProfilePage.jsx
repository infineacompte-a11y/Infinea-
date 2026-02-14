import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  Timer,
  Sparkles,
  LayoutGrid,
  BarChart3,
  User,
  LogOut,
  Menu,
  Crown,
  Mail,
  Calendar,
  ChevronRight,
  Settings,
  CreditCard,
  Plug,
} from "lucide-react";
import { toast } from "sonner";
import { API, useAuth } from "@/App";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";

export default function ProfilePage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

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

  const NavLinks = ({ mobile = false }) => (
    <>
      <Link
        to="/dashboard"
        className="nav-item flex items-center gap-3 px-4 py-3 rounded-xl text-muted-foreground hover:text-foreground"
        onClick={() => mobile && setMobileMenuOpen(false)}
      >
        <LayoutGrid className="w-5 h-5" />
        <span>Dashboard</span>
      </Link>
      <Link
        to="/actions"
        className="nav-item flex items-center gap-3 px-4 py-3 rounded-xl text-muted-foreground hover:text-foreground"
        onClick={() => mobile && setMobileMenuOpen(false)}
      >
        <Sparkles className="w-5 h-5" />
        <span>Bibliothèque</span>
      </Link>
      <Link
        to="/progress"
        className="nav-item flex items-center gap-3 px-4 py-3 rounded-xl text-muted-foreground hover:text-foreground"
        onClick={() => mobile && setMobileMenuOpen(false)}
      >
        <BarChart3 className="w-5 h-5" />
        <span>Progression</span>
      </Link>
      <Link
        to="/profile"
        className="nav-item active flex items-center gap-3 px-4 py-3 rounded-xl"
        onClick={() => mobile && setMobileMenuOpen(false)}
      >
        <User className="w-5 h-5" />
        <span>Profil</span>
      </Link>
    </>
  );

  return (
    <div className="min-h-screen bg-background">
      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex fixed left-0 top-0 bottom-0 w-64 flex-col p-6 border-r border-border bg-card/50">
        <div className="flex items-center gap-2 mb-8">
          <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center">
            <Timer className="w-6 h-6 text-primary-foreground" />
          </div>
          <span className="font-heading text-xl font-semibold">InFinea</span>
        </div>

        <nav className="flex flex-col gap-1 flex-1">
          <NavLinks />
        </nav>

        <div className="pt-4 border-t border-border">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-muted-foreground hover:text-foreground hover:bg-white/5 transition-colors"
          >
            <LogOut className="w-5 h-5" />
            <span>Déconnexion</span>
          </button>
        </div>
      </aside>

      {/* Mobile Header */}
      <header className="lg:hidden fixed top-0 left-0 right-0 z-50 glass">
        <div className="flex items-center justify-between px-4 h-16">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
              <Timer className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="font-heading text-lg font-semibold">InFinea</span>
          </div>

          <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon">
                <Menu className="w-6 h-6" />
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-72 bg-card p-6">
              <nav className="flex flex-col gap-1 mt-8">
                <NavLinks mobile />
              </nav>
              <div className="mt-auto pt-4 border-t border-border absolute bottom-6 left-6 right-6">
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-muted-foreground hover:text-foreground"
                >
                  <LogOut className="w-5 h-5" />
                  <span>Déconnexion</span>
                </button>
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </header>

      {/* Main Content */}
      <main className="lg:ml-64 pt-20 lg:pt-8 px-4 lg:px-8 pb-8">
        <div className="max-w-3xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="font-heading text-3xl font-semibold mb-2" data-testid="profile-title">
              Mon profil
            </h1>
            <p className="text-muted-foreground">
              Gérez vos informations et votre abonnement
            </p>
          </div>

          {/* Profile Card */}
          <Card className="mb-6">
            <CardContent className="p-6">
              <div className="flex items-center gap-6">
                <Avatar className="w-20 h-20">
                  <AvatarImage src={user?.picture} alt={user?.name} />
                  <AvatarFallback className="bg-primary/10 text-primary text-2xl">
                    {getInitials(user?.name)}
                  </AvatarFallback>
                </Avatar>
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-1">
                    <h2 className="font-heading text-2xl font-semibold" data-testid="profile-name">
                      {user?.name || "Utilisateur"}
                    </h2>
                    {user?.subscription_tier === "premium" && (
                      <Badge className="bg-gradient-to-r from-amber-500 to-orange-500 text-white">
                        <Crown className="w-3 h-3 mr-1" />
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
                    {user?.subscription_tier === "premium" ? "Plan Premium" : "Plan Gratuit"}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {user?.subscription_tier === "premium"
                      ? "Accès illimité à toutes les fonctionnalités"
                      : "Fonctionnalités de base"}
                  </p>
                </div>
                <Badge variant={user?.subscription_tier === "premium" ? "default" : "secondary"}>
                  {user?.subscription_tier === "premium" ? "Actif" : "Gratuit"}
                </Badge>
              </div>

              {user?.subscription_tier !== "premium" && (
                <Link to="/pricing">
                  <Button className="w-full rounded-xl" data-testid="upgrade-btn">
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
                    {user?.total_time_invested || 0}
                  </p>
                  <p className="text-sm text-muted-foreground">minutes investies</p>
                </div>
                <div className="p-4 rounded-xl bg-white/5">
                  <p className="text-2xl font-heading font-bold text-amber-500">
                    {user?.streak_days || 0}
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
              <Link to="/integrations">
                <button className="w-full flex items-center justify-between p-4 rounded-xl hover:bg-white/5 transition-colors">
                  <div className="flex items-center gap-3">
                    <Plug className="w-5 h-5 text-primary" />
                    <span>Hub d'Intégrations</span>
                  </div>
                  <ChevronRight className="w-5 h-5 text-muted-foreground" />
                </button>
              </Link>
              <Link to="/progress">
                <button className="w-full flex items-center justify-between p-4 rounded-xl hover:bg-white/5 transition-colors">
                  <div className="flex items-center gap-3">
                    <BarChart3 className="w-5 h-5 text-muted-foreground" />
                    <span>Voir mes statistiques</span>
                  </div>
                  <ChevronRight className="w-5 h-5 text-muted-foreground" />
                </button>
              </Link>
              
              <button
                onClick={handleLogout}
                className="w-full flex items-center justify-between p-4 rounded-xl hover:bg-white/5 transition-colors text-destructive"
                data-testid="profile-logout-btn"
              >
                <div className="flex items-center gap-3">
                  <LogOut className="w-5 h-5" />
                  <span>Se déconnecter</span>
                </div>
                <ChevronRight className="w-5 h-5" />
              </button>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
