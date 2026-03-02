import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Timer,
  Sparkles,
  Award,
  Rocket,
  Flame,
  Star,
  Crown,
  Clock,
  Trophy,
  BookOpen,
  Target,
  Heart,
  Gem,
  Lock,
  Shield,
  Layers,
  Medal,
  Wrench,
  HeartHandshake,
} from "lucide-react";
import { toast } from "sonner";
import { API, useAuth, authFetch } from "@/App";
import AppSidebar from "@/components/AppSidebar";

const badgeIcons = {
  rocket: Rocket,
  flame: Flame,
  star: Star,
  crown: Crown,
  clock: Clock,
  timer: Timer,
  trophy: Trophy,
  "book-open": BookOpen,
  target: Target,
  heart: Heart,
  sparkles: Sparkles,
  gem: Gem,
  shield: Shield,
  award: Award,
  layers: Layers,
  medal: Medal,
  wrench: Wrench,
  "heart-handshake": HeartHandshake,
};

export default function BadgesPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [allBadges, setAllBadges] = useState([]);
  const [userBadges, setUserBadges] = useState({ earned: [], new_badges: [] });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchBadges();
  }, []);

  const fetchBadges = async () => {
    try {
      const [allRes, userRes] = await Promise.all([
        authFetch(`${API}/badges`),
        authFetch(`${API}/badges/user`),
      ]);

      if (allRes.ok && userRes.ok) {
        const allData = await allRes.json();
        const userData = await userRes.json();
        setAllBadges(allData);
        setUserBadges(userData);

        // Show toast for new badges
        if (userData.new_badges?.length > 0) {
          userData.new_badges.forEach((badge) => {
            toast.success(`Nouveau badge obtenu : ${badge.name}!`);
          });
        }
      }
    } catch (error) {
      toast.error("Erreur de chargement des badges");
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  const earnedBadgeIds = userBadges.earned?.map((b) => b.badge_id) || [];
  const progressPercentage = (userBadges.earned?.length / allBadges.length) * 100 || 0;

  return (
    <div className="min-h-screen bg-background">
      <AppSidebar activePage="badges" onLogout={handleLogout} />

      {/* Main Content */}
      <main className="lg:ml-64 pt-20 lg:pt-8 px-4 lg:px-8 pb-8">
        <div className="max-w-5xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="font-heading text-3xl font-semibold mb-2" data-testid="badges-title">
              Vos Badges
            </h1>
            <p className="text-muted-foreground">
              Collectionnez des badges en atteignant vos objectifs
            </p>
          </div>

          {/* Progress Overview */}
          <Card className="mb-8">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-xl bg-amber-500/10 flex items-center justify-center">
                    <Trophy className="w-6 h-6 text-amber-500" />
                  </div>
                  <div>
                    <p className="font-heading text-2xl font-bold">
                      {userBadges.earned?.length || 0} / {allBadges.length}
                    </p>
                    <p className="text-sm text-muted-foreground">badges obtenus</p>
                  </div>
                </div>
                <Badge variant="outline" className="text-lg px-4 py-2">
                  {Math.round(progressPercentage)}%
                </Badge>
              </div>
              <Progress value={progressPercentage} className="h-3" />
            </CardContent>
          </Card>

          {/* Free Badges Grid */}
          {(() => {
            const freeBadges = allBadges.filter((b) => !b.premium_only);
            const premiumBadges = allBadges.filter((b) => b.premium_only);

            const renderBadge = (badge) => {
              const isEarned = earnedBadgeIds.includes(badge.badge_id);
              const Icon = badgeIcons[badge.icon] || Sparkles;
              const earnedData = userBadges.earned?.find((b) => b.badge_id === badge.badge_id);

              return (
                <Card
                  key={badge.badge_id}
                  className={`relative ${
                    isEarned
                      ? "bg-gradient-to-br from-amber-500/10 to-orange-500/10 border-amber-500/30"
                      : "opacity-60"
                  }`}
                  data-testid={`badge-${badge.badge_id}`}
                >
                  <CardContent className="p-4 text-center">
                    <div
                      className={`w-16 h-16 rounded-full mx-auto mb-3 flex items-center justify-center ${
                        isEarned ? "bg-amber-500/20" : "bg-muted"
                      }`}
                    >
                      {isEarned ? (
                        <Icon className="w-8 h-8 text-amber-500" />
                      ) : (
                        <Lock className="w-6 h-6 text-muted-foreground" />
                      )}
                    </div>
                    <h3 className="font-medium mb-1">{badge.name}</h3>
                    <p className="text-xs text-muted-foreground mb-2">{badge.description}</p>
                    {isEarned && earnedData?.earned_at && (
                      <Badge variant="secondary" className="text-xs">
                        {new Date(earnedData.earned_at).toLocaleDateString("fr-FR")}
                      </Badge>
                    )}
                  </CardContent>
                </Card>
              );
            };

            return (
              <>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                  {freeBadges.map(renderBadge)}
                </div>

                {premiumBadges.length > 0 && (
                  <div className="mt-10">
                    <div className="flex items-center gap-3 mb-6">
                      <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500/20 to-orange-500/20 flex items-center justify-center">
                        <Crown className="w-5 h-5 text-amber-500" />
                      </div>
                      <div>
                        <h2 className="font-heading text-xl font-semibold">Badges Premium</h2>
                        <p className="text-sm text-muted-foreground">
                          Badges exclusifs pour les membres Premium
                        </p>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                      {premiumBadges.map(renderBadge)}
                    </div>
                  </div>
                )}
              </>
            );
          })()}
        </div>
      </main>
    </div>
  );
}
