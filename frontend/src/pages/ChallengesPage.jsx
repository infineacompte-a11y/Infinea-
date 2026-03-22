import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Trophy,
  Target,
  Clock,
  Loader2,
  Crown,
  Lock,
  Compass,
  Layers,
  Sunrise,
  Calendar,
  Zap,
  Flame,
  Users,
  CheckCircle2,
} from "lucide-react";
import { toast } from "sonner";
import { API, useAuth, authFetch } from "@/App";
import Sidebar from "@/components/Sidebar";

const challengeIcons = {
  explorer: Compass,
  deep_diver: Layers,
  early_bird: Sunrise,
  consistency: Calendar,
  time_investor: Clock,
  diversifier: Zap,
};

const communityIconMap = {
  flame: Flame,
  clock: Clock,
  target: Target,
  compass: Compass,
};

export default function ChallengesPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState("community");
  const [communityData, setCommunityData] = useState(null);
  const [premiumChallenges, setPremiumChallenges] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isPremiumLoading, setIsPremiumLoading] = useState(true);

  const isPremium = user?.subscription_tier === "premium";

  useEffect(() => {
    fetchCommunity();
    if (isPremium) fetchPremium();
    else setIsPremiumLoading(false);
  }, [isPremium]);

  const fetchCommunity = async () => {
    try {
      const res = await authFetch(`${API}/challenges/community`);
      if (res.ok) setCommunityData(await res.json());
    } catch {
      // silent
    } finally {
      setIsLoading(false);
    }
  };

  const fetchPremium = async () => {
    try {
      const res = await authFetch(`${API}/premium/challenges`);
      if (res.ok) {
        const data = await res.json();
        setPremiumChallenges(data.challenges || []);
      }
    } catch {
      toast.error("Erreur de chargement");
    } finally {
      setIsPremiumLoading(false);
    }
  };

  const communityCompleted = (communityData?.challenges || []).filter((c) => c.completed).length;
  const communityTotal = (communityData?.challenges || []).length;

  const tabs = [
    { key: "community", label: "Communauté", icon: Users },
    { key: "premium", label: "Premium", icon: Crown },
  ];

  return (
    <div className="min-h-screen app-bg-mesh">
      <Sidebar />
      <main className="lg:ml-64 pt-20 lg:pt-8 px-4 lg:px-8 pb-8">
        <div className="max-w-2xl mx-auto">
          {/* Header */}
          <div className="opacity-0 animate-fade-in flex items-center justify-between mb-6" style={{ animationDelay: "0ms", animationFillMode: "forwards" }}>
            <div>
              <h1 className="font-sans font-semibold tracking-tight text-3xl font-semibold flex items-center gap-2">
                <Trophy className="w-6 h-6 text-primary" />
                Défis
              </h1>
              <p className="text-muted-foreground mt-1">
                Relève des défis et progresse avec la communauté
              </p>
            </div>
            {communityCompleted > 0 && (
              <Badge variant="outline" className="text-[10px] rounded-lg bg-[#5DB786]/15 text-[#5DB786] border-[#5DB786]/20">
                <CheckCircle2 className="w-2.5 h-2.5 mr-0.5" />
                <span className="tabular-nums">{communityCompleted}/{communityTotal}</span>
              </Badge>
            )}
          </div>

          {/* Tab switcher */}
          <div className="opacity-0 animate-fade-in flex gap-1 p-1 mb-6 bg-muted/30 rounded-xl" style={{ animationDelay: "100ms", animationFillMode: "forwards" }}>
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.key;
              return (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 px-3 rounded-lg text-sm font-medium transition-all duration-200 ${
                    isActive
                      ? "bg-background shadow-sm text-foreground"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <Icon className={`w-4 h-4 ${tab.key === "premium" && isActive ? "text-[#E48C75]" : ""}`} />
                  {tab.label}
                </button>
              );
            })}
          </div>

          {/* ─── Community Challenges ─── */}
          {activeTab === "community" && (
            <div className="opacity-0 animate-fade-in" style={{ animationDelay: "200ms", animationFillMode: "forwards" }}>
              {isLoading ? (
                <div className="flex flex-col items-center justify-center py-16 gap-3">
                  <Loader2 className="w-8 h-8 animate-spin text-primary" />
                  <p className="text-sm text-muted-foreground">Chargement...</p>
                </div>
              ) : (communityData?.challenges || []).length > 0 ? (
                <div className="space-y-3">
                  {(communityData?.challenges || []).map((ch, index) => {
                    const Icon = communityIconMap[ch.icon] || Target;
                    const pct = Math.min(Math.round((ch.progress / ch.target) * 100), 100);
                    return (
                      <Card
                        key={ch.id}
                        className={`opacity-0 animate-fade-in p-4 group hover:shadow-lg hover:border-[#459492]/30 hover:-translate-y-0.5 active:translate-y-px transition-all duration-200 ${ch.completed ? "border-[#5DB786]/30 bg-[#5DB786]/3" : ""}`}
                        style={{ animationDelay: `${index * 50}ms`, animationFillMode: "forwards" }}
                      >
                        <div className="flex items-start gap-3 mb-3">
                          <div className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 ${
                            ch.completed ? "bg-[#5DB786]/40" : "bg-primary/10"
                          }`}>
                            <Icon className={`w-5 h-5 ${ch.completed ? "text-[#5DB786]" : "text-primary"}`} />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <h3 className="font-sans font-semibold tracking-tight font-medium text-sm">{ch.title}</h3>
                              {ch.completed && (
                                <Badge variant="outline" className="text-[9px] rounded-lg bg-[#5DB786]/15 text-[#5DB786] border-[#5DB786]/20">
                                  Complété
                                </Badge>
                              )}
                            </div>
                            <p className="text-xs text-muted-foreground mt-0.5">{ch.description}</p>
                          </div>
                        </div>

                        <div className="space-y-1.5">
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-muted-foreground tabular-nums">{ch.progress}/{ch.target}</span>
                            <span className="font-medium text-[#459492] tabular-nums">{pct}%</span>
                          </div>
                          <Progress value={pct} className="h-2 rounded-full [&>div]:rounded-full [&>div]:transition-all [&>div]:duration-500" />
                        </div>

                        <div className="flex items-center justify-between mt-3 pt-2 border-t border-border/30">
                          <div className="flex items-center gap-1 text-[11px] text-muted-foreground">
                            <Users className="w-3 h-3" />
                            <span className="tabular-nums">{ch.participants_completed}</span> participant{ch.participants_completed !== 1 ? "s" : ""} ont réussi
                          </div>
                          <span className="text-[10px] text-muted-foreground">{ch.reward}</span>
                        </div>
                      </Card>
                    );
                  })}
                </div>
              ) : (
                <Card className="p-8 text-center">
                  <div className="bg-gradient-to-br from-[#459492]/20 to-transparent rounded-2xl w-16 h-16 flex items-center justify-center mx-auto mb-4">
                    <Trophy className="w-8 h-8 text-[#459492]" />
                  </div>
                  <p className="text-sm text-muted-foreground">Aucun défi communautaire ce mois-ci</p>
                </Card>
              )}
            </div>
          )}

          {/* ─── Premium Challenges ─── */}
          {activeTab === "premium" && (
            <div className="opacity-0 animate-fade-in" style={{ animationDelay: "200ms", animationFillMode: "forwards" }}>
              {!isPremium ? (
                <Card className="p-8 text-center border-[#E48C75]/20">
                  <div className="bg-gradient-to-br from-[#459492]/20 to-transparent rounded-2xl w-16 h-16 flex items-center justify-center mx-auto mb-4">
                    <Lock className="w-8 h-8 text-[#E48C75]" />
                  </div>
                  <h3 className="font-sans font-semibold tracking-tight font-semibold text-lg mb-2">Défis Premium</h3>
                  <p className="text-sm text-muted-foreground mb-6 max-w-sm mx-auto">
                    6 défis mensuels exclusifs avec badges et récompenses. Passe en Premium pour les débloquer.
                  </p>
                  <Link to="/pricing">
                    <Button className="gap-2 rounded-xl shadow-md hover:shadow-lg transition-all duration-200 btn-press">
                      <Crown className="w-4 h-4 text-[#E48C75]" />
                      Découvrir Premium
                    </Button>
                  </Link>
                </Card>
              ) : isPremiumLoading ? (
                <div className="flex flex-col items-center justify-center py-16 gap-3">
                  <Loader2 className="w-8 h-8 animate-spin text-primary" />
                  <p className="text-sm text-muted-foreground">Chargement...</p>
                </div>
              ) : premiumChallenges.length > 0 ? (
                <div className="space-y-3">
                  {premiumChallenges.map((ch, index) => {
                    const Icon = challengeIcons[ch.challenge_id] || Target;
                    const pct = Math.min(Math.round((ch.progress / ch.target) * 100), 100);
                    return (
                      <Card
                        key={ch.challenge_id}
                        className={`opacity-0 animate-fade-in p-4 group hover:shadow-lg hover:border-[#459492]/30 hover:-translate-y-0.5 active:translate-y-px transition-all duration-200 ${ch.completed ? "border-[#5DB786]/30 bg-[#5DB786]/3" : ""}`}
                        style={{ animationDelay: `${index * 50}ms`, animationFillMode: "forwards" }}
                      >
                        <div className="flex items-start gap-3 mb-3">
                          <div className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 ${
                            ch.completed ? "bg-[#5DB786]/40" : "bg-primary/10"
                          }`}>
                            <Icon className={`w-5 h-5 ${ch.completed ? "text-[#5DB786]" : "text-primary"}`} />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <h3 className="font-sans font-semibold tracking-tight font-medium text-sm">{ch.title}</h3>
                              {ch.completed && (
                                <Badge className="text-[9px] rounded-lg bg-[#5DB786]/15 text-[#5DB786]">Complété</Badge>
                              )}
                            </div>
                            <p className="text-xs text-muted-foreground mt-0.5">{ch.description}</p>
                          </div>
                        </div>
                        <div className="space-y-1.5">
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-muted-foreground tabular-nums">{ch.progress}/{ch.target}</span>
                            <span className="font-medium text-[#459492] tabular-nums">{pct}%</span>
                          </div>
                          <Progress value={pct} className="h-2 rounded-full [&>div]:rounded-full [&>div]:transition-all [&>div]:duration-500" />
                        </div>
                        {ch.completed && ch.completed_at && (
                          <p className="text-[10px] text-muted-foreground mt-2">
                            Complété le {new Date(ch.completed_at).toLocaleDateString("fr-FR")}
                          </p>
                        )}
                      </Card>
                    );
                  })}
                </div>
              ) : (
                <Card className="p-8 text-center">
                  <div className="bg-gradient-to-br from-[#459492]/20 to-transparent rounded-2xl w-16 h-16 flex items-center justify-center mx-auto mb-4">
                    <Trophy className="w-8 h-8 text-[#459492]" />
                  </div>
                  <p className="text-sm text-muted-foreground">Aucun défi premium ce mois-ci</p>
                </Card>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
