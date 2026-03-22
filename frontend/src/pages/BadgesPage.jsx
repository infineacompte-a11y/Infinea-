import React, { useState, useEffect } from "react";
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
  Loader2,
} from "lucide-react";
import { toast } from "sonner";
import { API, useAuth, authFetch } from "@/App";
import Sidebar from "@/components/Sidebar";

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
  const { user } = useAuth();
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

  const earnedBadgeIds = userBadges.earned?.map((b) => b.badge_id) || [];
  const progressPercentage = (userBadges.earned?.length / allBadges.length) * 100 || 0;

  return (
    <div className="min-h-screen app-bg-mesh">
      <Sidebar />

      {/* Main Content */}
      <main className="lg:ml-64 pt-14 lg:pt-0 pb-8">
        {/* Dark Header */}
        <div className="section-dark-header px-4 lg:px-8 pt-8 lg:pt-10 pb-8">
          <div className="max-w-5xl mx-auto">
            <h1 className="text-display text-3xl lg:text-4xl font-semibold text-white opacity-0 animate-fade-in" data-testid="badges-title">
              Badges
            </h1>
            <p className="text-white/60 text-sm mt-1 opacity-0 animate-fade-in" style={{ animationDelay: "50ms" }}>
              Vos récompenses et accomplissements
            </p>
          </div>
        </div>

        <div className="px-4 lg:px-8">
        <div className="max-w-5xl mx-auto space-y-6 pt-6">

          {isLoading ? (
            <div className="opacity-0 animate-fade-in flex flex-col items-center justify-center py-20 gap-3" style={{ animationDelay: "100ms", animationFillMode: "forwards" }}>
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
              <p className="text-sm text-muted-foreground">Chargement...</p>
            </div>
          ) : (
            <>
              {/* Progress Overview */}
              <div className="opacity-0 animate-fade-in" style={{ animationDelay: "100ms", animationFillMode: "forwards" }}>
                <Card className="mb-8 hover:shadow-lg hover:border-[#459492]/30 hover:-translate-y-0.5 transition-all duration-300">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-xl bg-[#5DB786]/40 flex items-center justify-center">
                          <Trophy className="w-6 h-6 text-[#5DB786]" />
                        </div>
                        <div>
                          <p className="font-sans font-semibold tracking-tight text-2xl font-bold tabular-nums">
                            {userBadges.earned?.length || 0} / {allBadges.length}
                          </p>
                          <p className="text-sm text-muted-foreground">badges obtenus</p>
                        </div>
                      </div>
                      <Badge variant="outline" className="text-lg px-4 py-2 rounded-lg tabular-nums">
                        {Math.round(progressPercentage)}%
                      </Badge>
                    </div>
                    <Progress value={progressPercentage} className="h-3 rounded-full [&>div]:rounded-full [&>div]:transition-all [&>div]:duration-500 [&>div]:bg-gradient-to-r [&>div]:from-[#459492] [&>div]:to-[#55B3AE]" />
                  </CardContent>
                </Card>
              </div>

              {/* Free Badges Grid */}
              {(() => {
                const freeBadges = allBadges.filter((b) => !b.premium_only);
                const premiumBadges = allBadges.filter((b) => b.premium_only);

                const renderBadge = (badge, index) => {
                  const isEarned = earnedBadgeIds.includes(badge.badge_id);
                  const Icon = badgeIcons[badge.icon] || Sparkles;
                  const earnedData = userBadges.earned?.find((b) => b.badge_id === badge.badge_id);

                  return (
                    <Card
                      key={badge.badge_id}
                      className={`opacity-0 animate-fade-in relative group hover:-translate-y-1 btn-press transition-all duration-300 ${
                        isEarned
                          ? "badge-unlocked-glow bg-gradient-to-br from-[#5DB786]/15 to-[#459492]/10 border-[#5DB786]/30 hover:border-[#5DB786]/50"
                          : "badge-locked opacity-60 hover:border-[#459492]/30 border-dashed"
                      }`}
                      style={{ animationDelay: `${index * 50}ms`, animationFillMode: "forwards" }}
                      data-testid={`badge-${badge.badge_id}`}
                    >
                      <CardContent className="p-4 text-center">
                        <div
                          className={`w-16 h-16 rounded-full mx-auto mb-3 flex items-center justify-center transition-all duration-300 ${
                            isEarned
                              ? "badge-icon-pulse bg-[#5DB786]/25 group-hover:bg-[#5DB786]/35"
                              : "bg-muted group-hover:bg-muted/80"
                          }`}
                        >
                          {isEarned ? (
                            <Icon className="w-8 h-8 text-[#5DB786] group-hover:scale-110 transition-transform duration-300" />
                          ) : (
                            <Lock className="w-6 h-6 text-muted-foreground/60" />
                          )}
                        </div>
                        <h3 className={`font-sans font-semibold tracking-tight font-medium mb-1 ${!isEarned ? "text-muted-foreground" : ""}`}>{badge.name}</h3>
                        <p className="text-xs text-muted-foreground mb-2">{badge.description}</p>
                        {isEarned && earnedData?.earned_at && (
                          <Badge variant="secondary" className="text-xs rounded-lg bg-[#5DB786]/40 text-[#5DB786] border-0">
                            {new Date(earnedData.earned_at).toLocaleDateString("fr-FR")}
                          </Badge>
                        )}
                      </CardContent>
                    </Card>
                  );
                };

                return (
                  <>
                    <div className="opacity-0 animate-fade-in grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4" style={{ animationDelay: "200ms", animationFillMode: "forwards" }}>
                      {freeBadges.map((badge, index) => renderBadge(badge, index))}
                    </div>

                    {premiumBadges.length > 0 && (
                      <div className="opacity-0 animate-fade-in mt-10" style={{ animationDelay: "300ms", animationFillMode: "forwards" }}>
                        <div className="premium-section-border">
                          <div className="premium-section-inner">
                            <div className="flex items-center gap-3 mb-6">
                              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#E48C75]/25 to-[#459492]/15 flex items-center justify-center shadow-sm">
                                <Crown className="w-5 h-5 text-[#E48C75]" />
                              </div>
                              <div>
                                <h2 className="font-sans font-semibold tracking-tight text-xl font-semibold flex items-center gap-2">
                                  Badges Premium
                                  <Sparkles className="w-4 h-4 text-[#E48C75]/60" />
                                </h2>
                                <p className="text-sm text-muted-foreground">
                                  Badges exclusifs pour les membres Premium
                                </p>
                              </div>
                            </div>
                            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                              {premiumBadges.map((badge, index) => renderBadge(badge, index))}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </>
                );
              })()}
            </>
          )}
        </div>
        </div>
      </main>
    </div>
  );
}
