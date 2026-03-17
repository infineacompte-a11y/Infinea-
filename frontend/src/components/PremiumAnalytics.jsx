import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Crown,
  Lock,
  TrendingUp,
  Clock,
  Calendar,
  Target,
  Flame,
  Loader2,
  Sparkles,
  Sunrise,
  Sun,
  Moon,
} from "lucide-react";
import { API, useAuth, authFetch } from "@/App";

const dayLabels = {
  monday: "Lundi",
  tuesday: "Mardi",
  wednesday: "Mercredi",
  thursday: "Jeudi",
  friday: "Vendredi",
  saturday: "Samedi",
  sunday: "Dimanche",
};

const timeLabels = {
  morning: "Matin",
  afternoon: "Après-midi",
  evening: "Soir",
};

const timeIcons = {
  morning: Sunrise,
  afternoon: Sun,
  evening: Moon,
};

export default function PremiumAnalytics() {
  const { user } = useAuth();
  const [analytics, setAnalytics] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const isPremium = user?.subscription_tier === "premium";

  useEffect(() => {
    if (isPremium) {
      fetchAnalytics();
    }
  }, [isPremium]);

  const fetchAnalytics = async () => {
    setIsLoading(true);
    try {
      const response = await authFetch(`${API}/premium/analytics`);
      if (response.ok) {
        const data = await response.json();
        setAnalytics(data);
      }
    } catch (error) {
      console.error("Analytics fetch error:", error);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isPremium) {
    return (
      <Card className="border-amber-500/30 bg-gradient-to-br from-amber-500/5 to-orange-500/5">
        <CardContent className="p-6 text-center">
          <div className="w-14 h-14 rounded-full bg-amber-500/10 flex items-center justify-center mx-auto mb-4">
            <Lock className="w-7 h-7 text-amber-500" />
          </div>
          <h3 className="font-heading text-lg font-semibold mb-2">
            Analytics Avancées
          </h3>
          <p className="text-sm text-muted-foreground mb-4">
            Découvrez vos habitudes, votre meilleur moment de la journée,
            et des insights personnalisés avec Premium.
          </p>
          <Link to="/pricing">
            <Button variant="outline" className="border-amber-500/30 text-amber-500 hover:bg-amber-500/10">
              <Crown className="w-4 h-4 mr-2" />
              Découvrir Premium
            </Button>
          </Link>
        </CardContent>
      </Card>
    );
  }

  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-6 flex items-center justify-center">
          <Loader2 className="w-6 h-6 animate-spin text-primary" />
        </CardContent>
      </Card>
    );
  }

  if (!analytics) return null;

  const TimeIcon = timeIcons[analytics.best_time_of_day] || Clock;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500/20 to-orange-500/20 flex items-center justify-center">
          <Crown className="w-5 h-5 text-amber-500" />
        </div>
        <div>
          <h2 className="font-heading text-xl font-semibold">Analytics Premium</h2>
          <p className="text-sm text-muted-foreground">Insights avancés sur vos habitudes</p>
        </div>
      </div>

      {/* Insights Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                <TimeIcon className="w-5 h-5 text-primary" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Meilleur moment</p>
                <p className="font-heading font-bold">
                  {timeLabels[analytics.best_time_of_day] || analytics.best_time_of_day || "—"}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center">
                <Calendar className="w-5 h-5 text-emerald-500" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Jour le + productif</p>
                <p className="font-heading font-bold">
                  {dayLabels[analytics.most_productive_day] || analytics.most_productive_day || "—"}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {analytics.milestones?.next && (
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-amber-500/10 flex items-center justify-center">
                  <Target className="w-5 h-5 text-amber-500" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Prochain palier</p>
                  <p className="font-heading font-bold">{analytics.milestones.next}</p>
                  {analytics.milestones.eta_days && (
                    <p className="text-xs text-muted-foreground">
                      ~{analytics.milestones.eta_days}j restants
                    </p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Activity Heatmap (last 30 days) */}
      {analytics.daily_activity?.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="font-heading text-lg flex items-center gap-2">
              <Flame className="w-5 h-5 text-amber-500" />
              Activité des 30 derniers jours
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-1">
              {analytics.daily_activity.map((day, i) => (
                <div
                  key={i}
                  className={`w-8 h-8 rounded-sm flex items-center justify-center text-xs ${
                    day.sessions > 0
                      ? day.sessions >= 3
                        ? "bg-primary text-primary-foreground"
                        : day.sessions >= 2
                        ? "bg-primary/60 text-primary-foreground"
                        : "bg-primary/30"
                      : "bg-muted"
                  }`}
                  title={`${day.date}: ${day.sessions} session(s), ${day.minutes}min`}
                >
                  {day.sessions > 0 ? day.sessions : ""}
                </div>
              ))}
            </div>
            <div className="flex items-center gap-4 mt-3 text-xs text-muted-foreground">
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 rounded-sm bg-muted" /> 0
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 rounded-sm bg-primary/30" /> 1
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 rounded-sm bg-primary/60" /> 2
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 rounded-sm bg-primary" /> 3+
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Streak History */}
      {analytics.streak_history?.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="font-heading text-lg flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-emerald-500" />
              Historique des streaks
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {analytics.streak_history.slice(0, 5).map((streak, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between p-3 rounded-lg bg-white/5"
                >
                  <div className="flex items-center gap-3">
                    <Flame className={`w-5 h-5 ${i === 0 ? "text-amber-500" : "text-muted-foreground"}`} />
                    <div>
                      <p className="font-medium">{streak.days} jours</p>
                      <p className="text-xs text-muted-foreground">
                        {streak.start_date && new Date(streak.start_date).toLocaleDateString("fr-FR")}
                        {streak.end_date && ` — ${new Date(streak.end_date).toLocaleDateString("fr-FR")}`}
                      </p>
                    </div>
                  </div>
                  {i === 0 && (
                    <Badge className="bg-amber-500/20 text-amber-500 text-xs">Meilleur</Badge>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
