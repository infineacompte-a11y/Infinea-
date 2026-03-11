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
    <div className="min-h-screen bg-background">
      <Sidebar />
      <main className="lg:ml-16 pb-20">
        <div className="max-w-2xl mx-auto px-4 py-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="font-heading text-2xl font-bold flex items-center gap-2">
                <Trophy className="w-6 h-6 text-primary" />
                Défis
              </h1>
              <p className="text-sm text-muted-foreground mt-0.5">
                Relève des défis et progresse avec la communauté
              </p>
            </div>
            {communityCompleted > 0 && (
              <Badge variant="outline" className="text-[10px] bg-emerald-500/10 text-emerald-500 border-emerald-500/20">
                <CheckCircle2 className="w-2.5 h-2.5 mr-0.5" />
                {communityCompleted}/{communityTotal}
              </Badge>
            )}
          </div>

          {/* Tab switcher */}
          <div className="flex gap-1 p-1 mb-5 bg-muted/30 rounded-xl">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.key;
              return (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 px-3 rounded-lg text-sm font-medium transition-all ${
                    isActive
                      ? "bg-background shadow-sm text-foreground"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </button>
              );
            })}
          </div>

          {/* ─── Community Challenges ─── */}
          {activeTab === "community" && (
            <div>
              {isLoading ? (
                <div className="flex items-center justify-center py-16">
                  <Loader2 className="w-8 h-8 animate-spin text-primary" />
                </div>
              ) : (communityData?.challenges || []).length > 0 ? (
                <div className="space-y-3">
                  {(communityData?.challenges || []).map((ch) => {
                    const Icon = communityIconMap[ch.icon] || Target;
                    const pct = Math.min(Math.round((ch.progress / ch.target) * 100), 100);
                    return (
                      <Card
                        key={ch.id}
                        className={`p-4 transition-all ${ch.completed ? "border-emerald-500/30 bg-emerald-500/3" : ""}`}
                      >
                        <div className="flex items-start gap-3 mb-3">
                          <div className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 ${
                            ch.completed ? "bg-emerald-500/10" : "bg-primary/10"
                          }`}>
                            <Icon className={`w-5 h-5 ${ch.completed ? "text-emerald-500" : "text-primary"}`} />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <h3 className="font-medium text-sm">{ch.title}</h3>
                              {ch.completed && (
                                <Badge variant="outline" className="text-[9px] bg-emerald-500/10 text-emerald-500 border-emerald-500/20">
                                  Complété
                                </Badge>
                              )}
                            </div>
                            <p className="text-xs text-muted-foreground mt-0.5">{ch.description}</p>
                          </div>
                        </div>

                        <div className="space-y-1.5">
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-muted-foreground">{ch.progress}/{ch.target}</span>
                            <span className="font-medium">{pct}%</span>
                          </div>
                          <Progress value={pct} className="h-2" />
                        </div>

                        <div className="flex items-center justify-between mt-3 pt-2 border-t border-border/30">
                          <div className="flex items-center gap-1 text-[11px] text-muted-foreground">
                            <Users className="w-3 h-3" />
                            {ch.participants_completed} participant{ch.participants_completed !== 1 ? "s" : ""} ont réussi
                          </div>
                          <span className="text-[10px] text-muted-foreground">{ch.reward}</span>
                        </div>
                      </Card>
                    );
                  })}
                </div>
              ) : (
                <Card className="p-8 text-center">
                  <Trophy className="w-10 h-10 text-muted-foreground/30 mx-auto mb-2" />
                  <p className="text-sm text-muted-foreground">Aucun défi communautaire ce mois-ci</p>
                </Card>
              )}
            </div>
          )}

          {/* ─── Premium Challenges ─── */}
          {activeTab === "premium" && (
            <div>
              {!isPremium ? (
                <Card className="p-8 text-center border-amber-500/20">
                  <div className="w-16 h-16 rounded-2xl bg-amber-500/10 flex items-center justify-center mx-auto mb-4">
                    <Lock className="w-8 h-8 text-amber-500" />
                  </div>
                  <h3 className="font-heading font-semibold text-lg mb-2">Défis Premium</h3>
                  <p className="text-sm text-muted-foreground mb-6 max-w-sm mx-auto">
                    6 défis mensuels exclusifs avec badges et récompenses. Passe en Premium pour les débloquer.
                  </p>
                  <Link to="/pricing">
                    <Button className="gap-2">
                      <Crown className="w-4 h-4" />
                      Découvrir Premium
                    </Button>
                  </Link>
                </Card>
              ) : isPremiumLoading ? (
                <div className="flex items-center justify-center py-16">
                  <Loader2 className="w-8 h-8 animate-spin text-primary" />
                </div>
              ) : premiumChallenges.length > 0 ? (
                <div className="space-y-3">
                  {premiumChallenges.map((ch) => {
                    const Icon = challengeIcons[ch.challenge_id] || Target;
                    const pct = Math.min(Math.round((ch.progress / ch.target) * 100), 100);
                    return (
                      <Card
                        key={ch.challenge_id}
                        className={`p-4 transition-all ${ch.completed ? "border-amber-500/30 bg-amber-500/3" : ""}`}
                      >
                        <div className="flex items-start gap-3 mb-3">
                          <div className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 ${
                            ch.completed ? "bg-amber-500/10" : "bg-primary/10"
                          }`}>
                            <Icon className={`w-5 h-5 ${ch.completed ? "text-amber-500" : "text-primary"}`} />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <h3 className="font-medium text-sm">{ch.title}</h3>
                              {ch.completed && (
                                <Badge className="text-[9px] bg-amber-500/20 text-amber-500">Complété</Badge>
                              )}
                            </div>
                            <p className="text-xs text-muted-foreground mt-0.5">{ch.description}</p>
                          </div>
                        </div>
                        <div className="space-y-1.5">
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-muted-foreground">{ch.progress}/{ch.target}</span>
                            <span className="font-medium">{pct}%</span>
                          </div>
                          <Progress value={pct} className="h-2" />
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
                  <Trophy className="w-10 h-10 text-muted-foreground/30 mx-auto mb-2" />
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
