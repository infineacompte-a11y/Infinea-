import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Timer,
  Sparkles,
  LayoutGrid,
  BarChart3,
  User,
  LogOut,
  Menu,
  Bell,
  BellOff,
  Check,
  Award,
  Flame,
  Clock,
  Loader2,
  Trash2,
} from "lucide-react";
import { toast } from "sonner";
import { API, useAuth, authFetch } from "@/App";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";

export default function NotificationsPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState([]);
  const [preferences, setPreferences] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isPushSupported, setIsPushSupported] = useState(false);
  const [isPushEnabled, setIsPushEnabled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    // Check if push notifications are supported
    if ("serviceWorker" in navigator && "PushManager" in window) {
      setIsPushSupported(true);
      checkPushStatus();
    }
    fetchData();
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
    } catch (error) {
      toast.error("Erreur de chargement");
    } finally {
      setIsLoading(false);
    }
  };

  const handleTogglePush = async () => {
    if (!isPushSupported) {
      toast.error("Les notifications push ne sont pas supportées");
      return;
    }

    try {
      if (isPushEnabled) {
        // Unsubscribe
        const registration = await navigator.serviceWorker.ready;
        const subscription = await registration.pushManager.getSubscription();
        if (subscription) {
          await subscription.unsubscribe();
        }
        setIsPushEnabled(false);
        toast.success("Notifications push désactivées");
      } else {
        // Subscribe
        const permission = await Notification.requestPermission();
        if (permission !== "granted") {
          toast.error("Permission refusée");
          return;
        }

        const registration = await navigator.serviceWorker.ready;
        const subscription = await registration.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: null, // Would need VAPID key in production
        });

        // Send subscription to server
        await authFetch(`${API}/notifications/subscribe`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ subscription: subscription.toJSON() }),
        });

        setIsPushEnabled(true);
        toast.success("Notifications push activées!");
      }
    } catch (error) {
      console.error("Push toggle error:", error);
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
    } catch (error) {
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
    } catch (error) {
      toast.error("Erreur");
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  const unreadCount = notifications.filter((n) => !n.read).length;

  const getNotificationIcon = (type) => {
    switch (type) {
      case "badge_earned":
        return Award;
      case "streak_alert":
        return Flame;
      case "reminder":
        return Clock;
      default:
        return Bell;
    }
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
        to="/notifications"
        className="nav-item active flex items-center gap-3 px-4 py-3 rounded-xl"
        onClick={() => mobile && setMobileMenuOpen(false)}
      >
        <Bell className="w-5 h-5" />
        <span>Notifications</span>
        {unreadCount > 0 && (
          <Badge variant="destructive" className="ml-auto">
            {unreadCount}
          </Badge>
        )}
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
        <div className="max-w-3xl mx-auto">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="font-heading text-3xl font-semibold mb-2" data-testid="notifications-title">
                Notifications
              </h1>
              <p className="text-muted-foreground">
                Gérez vos alertes et rappels
              </p>
            </div>
            {unreadCount > 0 && (
              <Button variant="outline" onClick={handleMarkAllRead}>
                <Check className="w-4 h-4 mr-2" />
                Tout marquer lu
              </Button>
            )}
          </div>

          {/* Notification Preferences */}
          <Card className="mb-8">
            <CardHeader>
              <CardTitle className="font-heading text-lg">Préférences</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
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
                        ? "Recevez des alertes même quand l'app est fermée"
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
                        Un rappel pour votre micro-action du jour
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
                        onChange={(e) =>
                          handleUpdatePreferences("reminder_time", e.target.value)
                        }
                        className="w-32"
                      />
                    </div>
                  )}

                  <div className="flex items-center justify-between">
                    <div>
                      <Label>Alertes streak</Label>
                      <p className="text-xs text-muted-foreground">
                        Soyez alerté si votre streak est en danger
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
                        Notification quand vous obtenez un badge
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
                        Recevez un résumé de votre progression
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

          {/* Notifications List */}
          <Card>
            <CardHeader>
              <CardTitle className="font-heading text-lg">
                Récentes
                {unreadCount > 0 && (
                  <Badge variant="secondary" className="ml-2">
                    {unreadCount} non lues
                  </Badge>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-6 h-6 animate-spin text-primary" />
                </div>
              ) : notifications.length > 0 ? (
                <div className="space-y-3">
                  {notifications.map((notif, i) => {
                    const Icon = getNotificationIcon(notif.type);
                    return (
                      <div
                        key={i}
                        className={`flex items-start gap-4 p-4 rounded-xl ${
                          notif.read ? "bg-white/5" : "bg-primary/10 border border-primary/20"
                        }`}
                      >
                        <div
                          className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                            notif.read ? "bg-muted" : "bg-primary/20"
                          }`}
                        >
                          <Icon
                            className={`w-5 h-5 ${
                              notif.read ? "text-muted-foreground" : "text-primary"
                            }`}
                          />
                        </div>
                        <div className="flex-1">
                          <p className={`font-medium ${notif.read ? "" : "text-foreground"}`}>
                            {notif.title}
                          </p>
                          <p className="text-sm text-muted-foreground">{notif.message}</p>
                          <p className="text-xs text-muted-foreground mt-1">
                            {new Date(notif.created_at).toLocaleString("fr-FR")}
                          </p>
                        </div>
                        {!notif.read && (
                          <div className="w-2 h-2 rounded-full bg-primary" />
                        )}
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <Bell className="w-10 h-10 mx-auto mb-2 opacity-50" />
                  <p>Aucune notification</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
