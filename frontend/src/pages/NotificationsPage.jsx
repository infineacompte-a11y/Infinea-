import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Bell,
  BellOff,
  Check,
  Award,
  Flame,
  Clock,
  Loader2,
  Target,
  CalendarClock,
  Trophy,
  Zap,
  ChevronRight,
  Sparkles,
  RefreshCw,
} from "lucide-react";
import { toast } from "sonner";
import { API, useAuth, authFetch } from "@/App";
import Sidebar from "@/components/Sidebar";

const SMART_ICON_MAP = {
  flame: Flame,
  target: Target,
  "calendar-clock": CalendarClock,
  trophy: Trophy,
  zap: Zap,
  clock: Clock,
  award: Award,
};

const SMART_COLOR_MAP = {
  streak_alert: "border-orange-500/30 bg-orange-500/5",
  objective_nudge: "border-blue-500/30 bg-blue-500/5",
  routine_reminder: "border-primary/30 bg-primary/5",
  milestone: "border-amber-500/30 bg-amber-500/5",
  coach_tip: "border-emerald-500/30 bg-emerald-500/5",
};

const SMART_ICON_COLOR_MAP = {
  streak_alert: "text-orange-500 bg-orange-500/10",
  objective_nudge: "text-blue-500 bg-blue-500/10",
  routine_reminder: "text-primary bg-primary/10",
  milestone: "text-amber-500 bg-amber-500/10",
  coach_tip: "text-emerald-500 bg-emerald-500/10",
};

export default function NotificationsPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState("smart");
  const [notifications, setNotifications] = useState([]);
  const [smartNotifs, setSmartNotifs] = useState([]);
  const [preferences, setPreferences] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSmartLoading, setIsSmartLoading] = useState(true);
  const [isPushSupported, setIsPushSupported] = useState(false);
  const [isPushEnabled, setIsPushEnabled] = useState(false);

  useEffect(() => {
    if ("serviceWorker" in navigator && "PushManager" in window) {
      setIsPushSupported(true);
      checkPushStatus();
    }
    fetchData();
    fetchSmartNotifs();
  }, []);

  const checkPushStatus = async () => {
    try {
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.getSubscription();
      setIsPushEnabled(!!subscription);
    } catch (error) {
      console.error("Push status check error:", error);
    }
  };

  const fetchData = async () => {
    try {
      const [notifRes, prefRes] = await Promise.all([
        authFetch(`${API}/notifications`),
        authFetch(`${API}/notifications/preferences`),
      ]);
      if (notifRes.ok) setNotifications(await notifRes.json());
      if (prefRes.ok) setPreferences(await prefRes.json());
    } catch {
      toast.error("Erreur de chargement");
    } finally {
      setIsLoading(false);
    }
  };

  const fetchSmartNotifs = async () => {
    setIsSmartLoading(true);
    try {
      const res = await authFetch(`${API}/notifications/smart`);
      if (res.ok) {
        const data = await res.json();
        setSmartNotifs(data.notifications || []);
      }
    } catch {
      // Silently fail — smart notifs are optional
    } finally {
      setIsSmartLoading(false);
    }
  };

  const handleTogglePush = async () => {
    if (!isPushSupported) {
      toast.error("Les notifications push ne sont pas supportées");
      return;
    }
    try {
      if (isPushEnabled) {
        const registration = await navigator.serviceWorker.ready;
        const subscription = await registration.pushManager.getSubscription();
        if (subscription) await subscription.unsubscribe();
        setIsPushEnabled(false);
        toast.success("Notifications push désactivées");
      } else {
        const permission = await Notification.requestPermission();
        if (permission !== "granted") {
          toast.error("Permission refusée");
          return;
        }
        // Fetch VAPID public key from backend
        const vapidRes = await authFetch(`${API}/notifications/vapid-public-key`);
        if (!vapidRes.ok) throw new Error("VAPID key unavailable");
        const { public_key } = await vapidRes.json();
        // Convert base64url to Uint8Array for PushManager
        const padding = "=".repeat((4 - (public_key.length % 4)) % 4);
        const raw = atob(public_key.replace(/-/g, "+").replace(/_/g, "/") + padding);
        const applicationServerKey = new Uint8Array(raw.length);
        for (let i = 0; i < raw.length; i++) applicationServerKey[i] = raw.charCodeAt(i);

        const registration = await navigator.serviceWorker.ready;
        const subscription = await registration.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey,
        });
        await authFetch(`${API}/notifications/subscribe`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ subscription: subscription.toJSON() }),
        });
        setIsPushEnabled(true);
        toast.success("Notifications push activées !");
      }
    } catch {
      toast.error("Erreur lors de l'activation");
    }
  };

  const handleUpdatePreferences = async (key, value) => {
    const newPrefs = { ...preferences, [key]: value };
    setPreferences(newPrefs);
    try {
      await authFetch(`${API}/notifications/preferences`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newPrefs),
      });
      toast.success("Préférences mises à jour");
    } catch {
      toast.error("Erreur de mise à jour");
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await authFetch(`${API}/notifications/mark-read`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ notification_ids: [] }),
      });
      setNotifications(notifications.map((n) => ({ ...n, read: true })));
      toast.success("Notifications marquées comme lues");
    } catch {
      toast.error("Erreur");
    }
  };

  const unreadCount = notifications.filter((n) => !n.read).length;

  const getNotificationIcon = (type) => {
    switch (type) {
      case "badge_earned": return Award;
      case "streak_alert": return Flame;
      case "reminder": return Clock;
      default: return Bell;
    }
  };

  const tabs = [
    { key: "smart", label: "Coach", icon: Sparkles, badge: smartNotifs.length || null },
    { key: "history", label: "Historique", icon: Bell, badge: unreadCount || null },
    { key: "settings", label: "Réglages", icon: Clock },
  ];

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <main className="lg:ml-64 pt-20 lg:pt-8 px-4 lg:px-8 pb-8">
        <div className="max-w-2xl mx-auto">
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="font-heading text-2xl font-bold flex items-center gap-2">
                <Bell className="w-6 h-6 text-primary" />
                Notifications
              </h1>
              <p className="text-sm text-muted-foreground mt-0.5">
                Alertes intelligentes et rappels proactifs
              </p>
            </div>
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
                  {tab.badge && (
                    <Badge className="h-4 px-1.5 text-[9px] bg-primary/10 text-primary border-primary/20 ml-0.5">
                      {tab.badge}
                    </Badge>
                  )}
                </button>
              );
            })}
          </div>

          {/* ─── Tab: Smart Coach Notifications ─── */}
          {activeTab === "smart" && (
            <div>
              <div className="flex items-center justify-between mb-3">
                <p className="text-xs text-muted-foreground">
                  Suggestions personnalisées basées sur ton activité
                </p>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 text-xs gap-1 text-muted-foreground"
                  onClick={fetchSmartNotifs}
                  disabled={isSmartLoading}
                >
                  <RefreshCw className={`w-3 h-3 ${isSmartLoading ? "animate-spin" : ""}`} />
                  Actualiser
                </Button>
              </div>

              {isSmartLoading ? (
                <div className="flex items-center justify-center py-16">
                  <Loader2 className="w-8 h-8 animate-spin text-primary" />
                </div>
              ) : smartNotifs.length > 0 ? (
                <div className="space-y-2.5">
                  {smartNotifs.map((notif) => {
                    const Icon = SMART_ICON_MAP[notif.icon] || Sparkles;
                    const colorClass = SMART_COLOR_MAP[notif.type] || "border-border bg-muted/20";
                    const iconColorClass = SMART_ICON_COLOR_MAP[notif.type] || "text-primary bg-primary/10";

                    return (
                      <Card
                        key={notif.id}
                        className={`p-4 border cursor-pointer hover:shadow-md transition-all ${colorClass}`}
                        onClick={() => notif.action_url && navigate(notif.action_url)}
                      >
                        <div className="flex items-start gap-3">
                          <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${iconColorClass}`}>
                            <Icon className="w-5 h-5" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <h3 className="font-medium text-sm">{notif.title}</h3>
                            <p className="text-xs text-muted-foreground mt-0.5 leading-relaxed">
                              {notif.message}
                            </p>
                          </div>
                          {notif.action_label && (
                            <Button
                              size="sm"
                              variant="ghost"
                              className="shrink-0 h-8 text-xs gap-1"
                              onClick={(e) => {
                                e.stopPropagation();
                                navigate(notif.action_url);
                              }}
                            >
                              {notif.action_label}
                              <ChevronRight className="w-3 h-3" />
                            </Button>
                          )}
                        </div>
                      </Card>
                    );
                  })}
                </div>
              ) : (
                <Card className="p-8 text-center">
                  <div className="w-16 h-16 rounded-2xl bg-emerald-500/10 flex items-center justify-center mx-auto mb-3">
                    <Check className="w-8 h-8 text-emerald-500" />
                  </div>
                  <h3 className="font-heading font-semibold mb-1">Tout est en ordre !</h3>
                  <p className="text-sm text-muted-foreground">
                    Aucune suggestion pour le moment. Continue comme ça !
                  </p>
                </Card>
              )}
            </div>
          )}

          {/* ─── Tab: Notification History ─── */}
          {activeTab === "history" && (
            <div>
              {unreadCount > 0 && (
                <div className="flex justify-end mb-3">
                  <Button variant="outline" size="sm" onClick={handleMarkAllRead} className="gap-1.5 text-xs">
                    <Check className="w-3.5 h-3.5" />
                    Tout marquer lu
                  </Button>
                </div>
              )}

              {isLoading ? (
                <div className="flex items-center justify-center py-16">
                  <Loader2 className="w-8 h-8 animate-spin text-primary" />
                </div>
              ) : notifications.length > 0 ? (
                <div className="space-y-2">
                  {notifications.map((notif, i) => {
                    const Icon = getNotificationIcon(notif.type);
                    return (
                      <Card
                        key={i}
                        className={`p-4 transition-all ${
                          notif.read ? "opacity-60" : "border-primary/20 bg-primary/5"
                        }`}
                      >
                        <div className="flex items-start gap-3">
                          <div className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${
                            notif.read ? "bg-muted" : "bg-primary/10"
                          }`}>
                            <Icon className={`w-4 h-4 ${notif.read ? "text-muted-foreground" : "text-primary"}`} />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-sm">{notif.title}</p>
                            <p className="text-xs text-muted-foreground mt-0.5">{notif.message}</p>
                            <p className="text-[10px] text-muted-foreground/60 mt-1">
                              {new Date(notif.created_at).toLocaleString("fr-FR")}
                            </p>
                          </div>
                          {!notif.read && (
                            <div className="w-2 h-2 rounded-full bg-primary shrink-0 mt-2" />
                          )}
                        </div>
                      </Card>
                    );
                  })}
                </div>
              ) : (
                <Card className="p-8 text-center">
                  <Bell className="w-10 h-10 mx-auto mb-2 text-muted-foreground/30" />
                  <p className="text-sm text-muted-foreground">Aucune notification</p>
                </Card>
              )}
            </div>
          )}

          {/* ─── Tab: Settings ─── */}
          {activeTab === "settings" && (
            <Card>
              <CardHeader>
                <CardTitle className="font-heading text-lg">Préférences</CardTitle>
              </CardHeader>
              <CardContent className="space-y-5">
                {/* Push Notifications */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {isPushEnabled ? (
                      <Bell className="w-5 h-5 text-primary" />
                    ) : (
                      <BellOff className="w-5 h-5 text-muted-foreground" />
                    )}
                    <div>
                      <Label>Notifications Push</Label>
                      <p className="text-xs text-muted-foreground">
                        {isPushSupported
                          ? "Alertes même quand l'app est fermée"
                          : "Non supporté sur ce navigateur"}
                      </p>
                    </div>
                  </div>
                  <Switch
                    checked={isPushEnabled}
                    onCheckedChange={handleTogglePush}
                    disabled={!isPushSupported}
                  />
                </div>

                {preferences && (
                  <>
                    <div className="flex items-center justify-between">
                      <div>
                        <Label>Rappel quotidien</Label>
                        <p className="text-xs text-muted-foreground">
                          Un rappel pour ta micro-action du jour
                        </p>
                      </div>
                      <Switch
                        checked={preferences.daily_reminder}
                        onCheckedChange={(v) => handleUpdatePreferences("daily_reminder", v)}
                      />
                    </div>

                    {preferences.daily_reminder && (
                      <div className="flex items-center justify-between pl-8">
                        <Label>Heure du rappel</Label>
                        <Input
                          type="time"
                          value={preferences.reminder_time}
                          onChange={(e) => handleUpdatePreferences("reminder_time", e.target.value)}
                          className="w-32"
                        />
                      </div>
                    )}

                    <div className="flex items-center justify-between">
                      <div>
                        <Label>Alertes streak</Label>
                        <p className="text-xs text-muted-foreground">
                          Alerte si ton streak est en danger
                        </p>
                      </div>
                      <Switch
                        checked={preferences.streak_alerts}
                        onCheckedChange={(v) => handleUpdatePreferences("streak_alerts", v)}
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <div>
                        <Label>Nouveaux badges</Label>
                        <p className="text-xs text-muted-foreground">
                          Notification quand tu obtiens un badge
                        </p>
                      </div>
                      <Switch
                        checked={preferences.achievement_alerts}
                        onCheckedChange={(v) => handleUpdatePreferences("achievement_alerts", v)}
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <div>
                        <Label>Résumé hebdomadaire</Label>
                        <p className="text-xs text-muted-foreground">
                          Résumé de ta progression chaque semaine
                        </p>
                      </div>
                      <Switch
                        checked={preferences.weekly_summary}
                        onCheckedChange={(v) => handleUpdatePreferences("weekly_summary", v)}
                      />
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </main>
    </div>
  );
}
