import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
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
  const { t } = useTranslation();
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
    <div className="min-h-screen bg-background">
      <Sidebar />

      {/* Main Content */}
      <main className="lg:ml-64 pt-20 lg:pt-8 px-4 lg:px-8 pb-8">
        <div className="max-w-3xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="font-heading text-3xl font-semibold mb-2" data-testid="profile-title">
              {t("profile.title")}
            </h1>
            <p className="text-muted-foreground">
              {t("profile.subtitle")}
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
                      {user?.name || t("profile.defaultUser")}
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
                {t("profile.subscription.title")}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between p-4 rounded-xl bg-white/5 mb-4">
                <div>
                  <p className="font-medium mb-1">
                    {user?.subscription_tier === "premium" ? t("profile.subscription.premiumPlan") : t("profile.subscription.freePlan")}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {user?.subscription_tier === "premium"
                      ? t("profile.subscription.premiumDesc")
                      : t("profile.subscription.freeDesc")}
                  </p>
                </div>
                <Badge variant={user?.subscription_tier === "premium" ? "default" : "secondary"}>
                  {user?.subscription_tier === "premium" ? t("profile.subscription.active") : t("profile.subscription.free")}
                </Badge>
              </div>

              {user?.subscription_tier === "premium" ? (
                <Button
                  variant="outline"
                  className="w-full rounded-xl"
                  onClick={async () => {
                    try {
                      const res = await authFetch(`${API}/premium/portal`, { method: "POST" });
                      if (res.ok) {
                        const data = await res.json();
                        window.open(data.url, "_blank");
                      } else {
                        toast.error(t("profile.errors.portalError"));
                      }
                    } catch {
                      toast.error(t("profile.errors.connectionError"));
                    }
                  }}
                >
                  <Settings className="w-5 h-5 mr-2" />
                  {t("profile.subscription.manage")}
                </Button>
              ) : (
                <Link to="/pricing">
                  <Button className="w-full rounded-xl" data-testid="upgrade-btn">
                    <Crown className="w-5 h-5 mr-2" />
                    {t("profile.subscription.upgrade")}
                    <ChevronRight className="w-5 h-5 ml-2" />
                  </Button>
                </Link>
              )}
            </CardContent>
          </Card>

          {/* Stats Summary */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="font-heading text-lg">{t("profile.summary.title")}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-white/5">
                  <p className="text-2xl font-heading font-bold text-primary">
                    {user?.total_time_invested || 0}
                  </p>
                  <p className="text-sm text-muted-foreground">{t("profile.summary.minutesInvested")}</p>
                </div>
                <div className="p-4 rounded-xl bg-white/5">
                  <p className="text-2xl font-heading font-bold text-amber-500">
                    {user?.streak_days || 0}
                  </p>
                  <p className="text-sm text-muted-foreground">{t("profile.summary.streakDays")}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Actions */}
          <Card>
            <CardHeader>
              <CardTitle className="font-heading text-lg">{t("profile.actions.title")}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Link to="/progress">
                <button className="w-full flex items-center justify-between p-4 rounded-xl hover:bg-white/5 transition-colors">
                  <div className="flex items-center gap-3">
                    <BarChart3 className="w-5 h-5 text-muted-foreground" />
                    <span>{t("profile.actions.viewStats")}</span>
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
                  <span>{t("profile.actions.logout")}</span>
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
