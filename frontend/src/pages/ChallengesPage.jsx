import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Timer,
  Sparkles,
  LayoutGrid,
  BarChart3,
  User,
  LogOut,
  Menu,
  Trophy,
  Target,
  Clock,
  Flame,
  Loader2,
  Crown,
  Lock,
  Compass,
  Layers,
  Sunrise,
  Calendar,
  Zap,
} from "lucide-react";
import { toast } from "sonner";
import { API, useAuth, authFetch } from "@/App";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";

const challengeIcons = {
  explorer: Compass,
  deep_diver: Layers,
  early_bird: Sunrise,
  consistency: Calendar,
  time_investor: Clock,
  diversifier: Zap,
};

export default function ChallengesPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [challenges, setChallenges] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const isPremium = user?.subscription_tier === "premium";

  useEffect(() => {
    if (isPremium) {
      fetchChallenges();
    } else {
      setIsLoading(false);
    }
  }, [isPremium]);

  const fetchChallenges = async () => {
    try {
      const response = await authFetch(`${API}/premium/challenges`);
      if (response.ok) {
        const data = await response.json();
        setChallenges(data);
      }
    } catch (error) {
      toast.error("Erreur de chargement des défis");
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate("/login");
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
        to="/challenges"
        className="nav-item active flex items-center gap-3 px-4 py-3 rounded-xl"
        onClick={() => mobile && setMobileMenuOpen(false)}
      >
        <Trophy className="w-5 h-5" />
        <span>Défis</span>
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
        className="nav-item flex items-center gap-3 px-4 py-3 rounded-xl text-muted-foreground hover:text-foreground"
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
            </SheetContent>
          </Sheet>
        </div>
      </header>

      {/* Main Content */}
      <main className="lg:ml-64 pt-20 lg:pt-8 px-4 lg:px-8 pb-8">
        <div className="max-w-5xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center gap-3 mb-2">
              <h1 className="font-heading text-3xl font-semibold">
                Défis Mensuels
              </h1>
              <Badge className="bg-gradient-to-r from-amber-500 to-orange-500 text-white">
                <Crown className="w-3 h-3 mr-1" />
                Premium
              </Badge>
            </div>
            <p className="text-muted-foreground">
              Relevez des défis chaque mois pour gagner des badges exclusifs
            </p>
          </div>

          {!isPremium ? (
            <Card className="border-amber-500/30">
              <CardContent className="p-8 text-center">
                <div className="w-16 h-16 rounded-full bg-amber-500/10 flex items-center justify-center mx-auto mb-4">
                  <Lock className="w-8 h-8 text-amber-500" />
                </div>
                <h2 className="font-heading text-2xl font-semibold mb-2">
                  Fonctionnalité Premium
                </h2>
                <p className="text-muted-foreground mb-6 max-w-md mx-auto">
                  Les défis mensuels sont exclusifs aux membres Premium. Relevez des défis,
                  gagnez des badges et progressez encore plus vite.
                </p>
                <Link to="/pricing">
                  <Button className="rounded-xl">
                    <Crown className="w-5 h-5 mr-2" />
                    Découvrir Premium
                  </Button>
                </Link>
              </CardContent>
            </Card>
          ) : isLoading ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : (
            <div className="grid md:grid-cols-2 gap-4">
              {challenges.map((challenge) => {
                const Icon = challengeIcons[challenge.challenge_id] || Target;
                const progressPct = Math.min(
                  (challenge.progress / challenge.target) * 100,
                  100
                );
                const isCompleted = challenge.completed;

                return (
                  <Card
                    key={challenge.challenge_id}
                    className={`${
                      isCompleted
                        ? "bg-gradient-to-br from-amber-500/10 to-orange-500/10 border-amber-500/30"
                        : ""
                    }`}
                  >
                    <CardContent className="p-5">
                      <div className="flex items-start gap-4 mb-4">
                        <div
                          className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                            isCompleted
                              ? "bg-amber-500/20"
                              : "bg-primary/10"
                          }`}
                        >
                          <Icon
                            className={`w-6 h-6 ${
                              isCompleted ? "text-amber-500" : "text-primary"
                            }`}
                          />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <h3 className="font-heading font-semibold">
                              {challenge.title}
                            </h3>
                            {isCompleted && (
                              <Badge className="bg-amber-500/20 text-amber-500 text-xs">
                                Complété
                              </Badge>
                            )}
                          </div>
                          <p className="text-sm text-muted-foreground">
                            {challenge.description}
                          </p>
                        </div>
                      </div>

                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">Progression</span>
                          <span className="font-medium">
                            {challenge.progress} / {challenge.target}
                          </span>
                        </div>
                        <Progress value={progressPct} className="h-2" />
                      </div>

                      {isCompleted && challenge.completed_at && (
                        <p className="text-xs text-muted-foreground mt-3">
                          Complété le{" "}
                          {new Date(challenge.completed_at).toLocaleDateString("fr-FR")}
                        </p>
                      )}
                    </CardContent>
                  </Card>
                );
              })}

              {challenges.length === 0 && (
                <div className="col-span-2 text-center py-12">
                  <Trophy className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                  <h3 className="font-heading text-xl mb-2">Aucun défi ce mois</h3>
                  <p className="text-muted-foreground">
                    Les défis du mois seront bientôt disponibles
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
