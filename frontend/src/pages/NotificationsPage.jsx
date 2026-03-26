import React, { useState, useEffect, useMemo } from "react";
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
  Heart,
  MessageCircle,
  AtSign,
  UserPlus,
  Mail,
  UserCheck,
  Users,
  Trash2,
  Filter,
  X,
  ShieldAlert,
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
  streak_alert: "border-[#E48C75]/30 bg-[#E48C75]/5",
  objective_nudge: "border-[#55B3AE]/30 bg-[#55B3AE]/5",
  routine_reminder: "border-primary/30 bg-primary/5",
  milestone: "border-[#5DB786]/30 bg-[#5DB786]/5",
  coach_tip: "border-[#459492]/30 bg-[#459492]/5",
};

const SMART_ICON_COLOR_MAP = {
  streak_alert: "text-[#E48C75] bg-[#E48C75]/40",
  objective_nudge: "text-[#55B3AE] bg-[#55B3AE]/40",
  routine_reminder: "text-primary bg-primary/10",
  milestone: "text-[#5DB786] bg-[#5DB786]/40",
  coach_tip: "text-[#459492] bg-[#459492]/40",
};

/**
 * Group similar notifications (Instagram pattern: "Sam et 3 autres ont réagi").
 * Groups by type + target within the same day.
 * Only groupable types: reaction, comment, new_follower.
 */
const GROUPABLE_TYPES = new Set(["reaction", "comment", "new_follower"]);

const GROUP_VERBS = {
  reaction: "ont réagi à ton activité",
  comment: "ont commenté ton activité",
  new_follower: "ont commencé à te suivre",
};

function getNotifPrimaryName(notif) {
  const d = notif.data || {};
  return d.reactor_name || d.commenter_name || d.follower_name || d.user_name || "";
}

function groupSimilarNotifications(notifications) {
  const grouped = [];
  const groupMap = new Map();

  for (const notif of notifications) {
    if (!GROUPABLE_TYPES.has(notif.type)) {
      grouped.push(notif);
      continue;
    }

    const day = new Date(notif.created_at).toDateString();
    const targetId = notif.data?.activity_id || "";
    const groupKey = notif.type === "new_follower"
      ? `follower:${day}`
      : `${notif.type}:${targetId}:${day}`;

    if (groupMap.has(groupKey)) {
      const idx = groupMap.get(groupKey);
      grouped[idx]._groupCount = (grouped[idx]._groupCount || 1) + 1;
      const name = getNotifPrimaryName(notif);
      if (name && !grouped[idx]._groupNames.includes(name)) {
        grouped[idx]._groupNames.push(name);
      }
    } else {
      groupMap.set(groupKey, grouped.length);
      const primaryName = getNotifPrimaryName(notif);
      grouped.push({
        ...notif,
        _groupCount: 1,
        _primaryName: primaryName,
        _groupNames: primaryName ? [primaryName] : [],
      });
    }
  }

  return grouped;
}

function getGroupedMessage(notif) {
  if (!notif._groupCount || notif._groupCount <= 1) return notif.message;
  const others = notif._groupCount - 1;
  const verb = GROUP_VERBS[notif.type] || "ont interagi";
  return `${notif._primaryName} et ${others} autre${others > 1 ? "s" : ""} ${verb}`;
}

function getGroupedTitle(notif) {
  if (!notif._groupCount || notif._groupCount <= 1) return notif.title;
  if (notif.type === "reaction") return `${notif._groupCount} réactions`;
  if (notif.type === "comment") return `${notif._groupCount} commentaires`;
  if (notif.type === "new_follower") return `${notif._groupCount} nouveaux followers`;
  return notif.title;
}

/** Group notifications by date label */
function groupByDate(notifications) {
  const groups = {};
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);

  notifications.forEach((n) => {
    const d = new Date(n.created_at);
    const dDate = new Date(d.getFullYear(), d.getMonth(), d.getDate());
    let label;
    if (dDate >= today) label = "Aujourd'hui";
    else if (dDate >= yesterday) label = "Hier";
    else label = d.toLocaleDateString("fr-FR", { day: "numeric", month: "long" });
    if (!groups[label]) groups[label] = [];
    groups[label].push(n);
  });
  return groups;
}

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
  const [filterType, setFilterType] = useState(null);

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

  const handleDeleteNotification = async (notificationId) => {
    try {
      const res = await authFetch(`${API}/notifications/${notificationId}`, {
        method: "DELETE",
      });
      if (res.ok) {
        setNotifications((prev) => prev.filter((n) => n.notification_id !== notificationId));
        toast.success("Notification supprimée");
      }
    } catch {
      toast.error("Erreur de suppression");
    }
  };

  const handleDeleteRead = async () => {
    try {
      const res = await authFetch(`${API}/notifications/read`, {
        method: "DELETE",
      });
      if (res.ok) {
        setNotifications((prev) => prev.filter((n) => !n.read));
        toast.success("Notifications lues supprimées");
      }
    } catch {
      toast.error("Erreur de suppression");
    }
  };

  const unreadCount = notifications.filter((n) => !n.read).length;
  const readCount = notifications.filter((n) => n.read).length;

  const filteredNotifications = useMemo(
    () => (filterType ? notifications.filter((n) => n.type === filterType) : notifications),
    [notifications, filterType]
  );
  const groupedNotifications = useMemo(
    () => groupByDate(groupSimilarNotifications(filteredNotifications)),
    [filteredNotifications]
  );

  const FILTER_CHIPS = [
    { key: null, label: "Tout" },
    { key: "reaction", label: "Réactions", icon: Heart },
    { key: "comment", label: "Commentaires", icon: MessageCircle },
    { key: "mention", label: "Mentions", icon: AtSign },
    { key: "new_follower", label: "Followers", icon: UserPlus },
  ];

  const NOTIF_TYPE_MAP = {
    reaction:              { icon: Heart,          color: "#E48C75" },
    comment:               { icon: MessageCircle,  color: "#55B3AE" },
    reply:                 { icon: MessageCircle,  color: "#55B3AE" },
    mention:               { icon: AtSign,         color: "#459492" },
    new_follower:          { icon: UserPlus,       color: "#5DB786" },
    new_message:           { icon: Mail,           color: "#55B3AE" },
    badge_earned:          { icon: Award,          color: "#F5A623" },
    streak_alert:          { icon: Flame,          color: "#E48C75" },
    group_invite:          { icon: Users,          color: "#459492" },
    group_member_joined:   { icon: UserCheck,      color: "#5DB786" },
    reminder:              { icon: Clock,          color: null },
    comment_like:          { icon: Heart,          color: "#E48C75" },
    moderation:            { icon: ShieldAlert,    color: "#E48C75" },
  };

  const getNotifMeta = (type) => NOTIF_TYPE_MAP[type] || { icon: Bell, color: null };

  const tabs = [
    { key: "smart", label: "Coach", icon: Sparkles, badge: smartNotifs.length || null },
    { key: "history", label: "Historique", icon: Bell, badge: unreadCount || null },
    { key: "settings", label: "Réglages", icon: Clock },
  ];

  return (
    <div className="min-h-screen app-bg-mesh">
      <Sidebar />
      <main className="lg:ml-64 pt-14 lg:pt-0 pb-8">
        {/* Dark Header */}
        <div className="section-dark-header px-4 lg:px-8 pt-8 lg:pt-10 pb-8">
          <div className="max-w-5xl mx-auto">
            <h1 className="text-display text-3xl lg:text-4xl font-semibold text-white opacity-0 animate-fade-in">
              Notifications
            </h1>
            <p className="text-white/60 text-sm mt-1 opacity-0 animate-fade-in" style={{ animationDelay: "50ms" }}>
              Restez informé de votre activité
            </p>
          </div>
        </div>

        <div className="px-4 lg:px-8">
        <div className="max-w-2xl mx-auto">
          {/* Tab switcher */}
          <div className="opacity-0 animate-fade-in flex gap-1 p-1 mb-5 bg-muted/30 rounded-xl" style={{ animationDelay: "200ms", animationFillMode: "forwards" }}>
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
                  <Icon className="w-4 h-4" />
                  {tab.label}
                  {tab.badge && (
                    <Badge className="h-4 px-1.5 text-[9px] bg-[#459492]/40 text-[#459492] border-[#459492]/20 ml-0.5">
                      {tab.badge}
                    </Badge>
                  )}
                </button>
              );
            })}
          </div>

          {/* ─── Tab: Smart Coach Notifications ─── */}
          {activeTab === "smart" && (
            <div className="opacity-0 animate-fade-in" style={{ animationDelay: "300ms", animationFillMode: "forwards" }}>
              <div className="flex items-center justify-between mb-3">
                <p className="text-xs text-muted-foreground">
                  Suggestions personnalisées basées sur ton activité
                </p>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 text-xs gap-1 text-muted-foreground rounded-xl transition-all duration-200 btn-press"
                  onClick={fetchSmartNotifs}
                  disabled={isSmartLoading}
                >
                  <RefreshCw className={`w-3 h-3 ${isSmartLoading ? "animate-spin" : ""}`} />
                  Actualiser
                </Button>
              </div>

              {isSmartLoading ? (
                <div className="space-y-3">
                  {[...Array(3)].map((_, i) => (
                    <div key={i} className="rounded-xl border border-border bg-card p-4 animate-pulse">
                      <div className="flex items-start gap-3">
                        <div className="w-10 h-10 rounded-xl bg-muted" />
                        <div className="flex-1 space-y-2">
                          <div className="h-4 w-1/3 rounded bg-muted" />
                          <div className="h-3 w-2/3 rounded bg-muted" />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : smartNotifs.length > 0 ? (
                <div className="space-y-2.5">
                  {smartNotifs.map((notif, idx) => {
                    const Icon = SMART_ICON_MAP[notif.icon] || Sparkles;
                    const colorClass = SMART_COLOR_MAP[notif.type] || "border-border bg-muted/20";
                    const iconColorClass = SMART_ICON_COLOR_MAP[notif.type] || "text-primary bg-primary/10";

                    return (
                      <Card
                        key={notif.id}
                        className={`opacity-0 animate-fade-in group p-4 border cursor-pointer hover:shadow-lg hover:border-[#459492]/30 hover:-translate-y-0.5 active:translate-y-px transition-all duration-200 rounded-xl ${colorClass}`}
                        style={{ animationDelay: `${idx * 30}ms`, animationFillMode: "forwards" }}
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
                              className="shrink-0 h-8 text-xs gap-1 rounded-xl transition-all duration-200 btn-press"
                              onClick={(e) => {
                                e.stopPropagation();
                                navigate(notif.action_url);
                              }}
                            >
                              {notif.action_label}
                              <ChevronRight className="w-3 h-3 group-hover:translate-x-1 transition-transform duration-200" />
                            </Button>
                          )}
                        </div>
                      </Card>
                    );
                  })}
                </div>
              ) : (
                <Card className="p-8 text-center rounded-xl">
                  <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[#5DB786]/20 to-[#5DB786]/5 flex items-center justify-center mx-auto mb-3">
                    <Check className="w-8 h-8 text-[#5DB786]" />
                  </div>
                  <h3 className="font-sans font-semibold tracking-tight font-semibold mb-1">Tout est en ordre !</h3>
                  <p className="text-sm text-muted-foreground">
                    Aucune suggestion pour le moment. Continue comme ça !
                  </p>
                </Card>
              )}
            </div>
          )}

          {/* ─── Tab: Notification History ─── */}
          {activeTab === "history" && (
            <div className="opacity-0 animate-fade-in" style={{ animationDelay: "300ms", animationFillMode: "forwards" }}>
              {/* Filter chips */}
              <div className="flex items-center gap-1.5 mb-3 overflow-x-auto pb-1 scrollbar-hide">
                <Filter className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
                {FILTER_CHIPS.map((chip) => {
                  const ChipIcon = chip.icon;
                  const isActive = filterType === chip.key;
                  return (
                    <button
                      key={chip.key ?? "all"}
                      onClick={() => setFilterType(chip.key)}
                      className={`flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium whitespace-nowrap transition-all duration-200 ${
                        isActive
                          ? "bg-[#459492] text-white shadow-sm"
                          : "bg-muted/40 text-muted-foreground hover:bg-muted/60"
                      }`}
                    >
                      {ChipIcon && <ChipIcon className="w-3 h-3" />}
                      {chip.label}
                    </button>
                  );
                })}
              </div>

              {/* Action buttons */}
              {(unreadCount > 0 || readCount > 0) && (
                <div className="flex justify-end gap-2 mb-3">
                  {unreadCount > 0 && (
                    <Button variant="outline" size="sm" onClick={handleMarkAllRead} className="gap-1.5 text-xs rounded-xl transition-all duration-200 btn-press">
                      <Check className="w-3.5 h-3.5" />
                      Tout marquer lu
                    </Button>
                  )}
                  {readCount > 0 && (
                    <Button variant="outline" size="sm" onClick={handleDeleteRead} className="gap-1.5 text-xs rounded-xl transition-all duration-200 btn-press text-muted-foreground hover:text-destructive hover:border-destructive/30">
                      <Trash2 className="w-3.5 h-3.5" />
                      Supprimer les lues
                    </Button>
                  )}
                </div>
              )}

              {isLoading ? (
                <div className="space-y-3">
                  {[...Array(4)].map((_, i) => (
                    <div key={i} className="rounded-xl border border-border bg-card p-4 animate-pulse">
                      <div className="flex items-start gap-3">
                        <div className="w-9 h-9 rounded-lg bg-muted" />
                        <div className="flex-1 space-y-2">
                          <div className="h-4 w-2/5 rounded bg-muted" />
                          <div className="h-3 w-3/5 rounded bg-muted" />
                          <div className="h-2 w-1/4 rounded bg-muted" />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : notifications.length > 0 ? (
                <div className="space-y-4">
                  {Object.entries(groupedNotifications).map(([dateLabel, items]) => (
                    <div key={dateLabel}>
                      {/* Date separator */}
                      <div className="flex items-center gap-3 mb-2">
                        <span className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">{dateLabel}</span>
                        <div className="flex-1 h-px bg-border" />
                      </div>
                      <div className="space-y-2">
                        {items.map((notif, i) => {
                          const { icon: Icon, color } = getNotifMeta(notif.type);
                          const accent = color || "#E48C75";
                          return (
                            <div
                              key={i}
                              className={`opacity-0 animate-fade-in group p-4 rounded-xl border transition-all duration-200 hover:bg-muted/30 ${
                                notif.read
                                  ? "opacity-60 border-border bg-card"
                                  : "border-l-2"
                              }`}
                              style={{
                                animationDelay: `${i * 30}ms`,
                                animationFillMode: "forwards",
                                ...(!notif.read ? {
                                  borderLeftColor: accent,
                                  borderTopColor: `${accent}33`,
                                  borderRightColor: `${accent}33`,
                                  borderBottomColor: `${accent}33`,
                                  backgroundColor: `${accent}0D`,
                                } : {}),
                              }}
                            >
                              <div className="flex items-start gap-3">
                                <div
                                  className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0"
                                  style={notif.read
                                    ? { backgroundColor: "hsl(var(--muted))" }
                                    : { backgroundColor: `${accent}66` }
                                  }
                                >
                                  <Icon
                                    className="w-4 h-4"
                                    style={notif.read
                                      ? { color: "hsl(var(--muted-foreground))" }
                                      : { color: accent }
                                    }
                                  />
                                </div>
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-1.5">
                                    <p className="font-medium text-sm">{getGroupedTitle(notif)}</p>
                                    {notif._groupCount > 1 && (
                                      <span
                                        className="text-[9px] font-semibold px-1.5 py-0.5 rounded-full tabular-nums"
                                        style={{ backgroundColor: `${accent}20`, color: accent }}
                                      >
                                        {notif._groupCount}
                                      </span>
                                    )}
                                  </div>
                                  <p className="text-xs text-muted-foreground mt-0.5">{getGroupedMessage(notif)}</p>
                                  <p className="text-[10px] text-muted-foreground/60 mt-1 tabular-nums">
                                    {new Date(notif.created_at).toLocaleString("fr-FR")}
                                  </p>
                                </div>
                                <div className="flex items-center gap-1.5 shrink-0">
                                  {!notif.read && (
                                    <div
                                      className="w-2 h-2 rounded-full animate-pulse"
                                      style={{ backgroundColor: accent }}
                                    />
                                  )}
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleDeleteNotification(notif.notification_id);
                                    }}
                                    className="opacity-0 group-hover:opacity-100 p-1 rounded-md hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-all duration-200"
                                    title="Supprimer"
                                  >
                                    <X className="w-3.5 h-3.5" />
                                  </button>
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <Card className="p-8 text-center rounded-xl">
                  <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-muted/40 to-transparent flex items-center justify-center mx-auto mb-3">
                    <Bell className="w-8 h-8 text-muted-foreground/30" />
                  </div>
                  <h3 className="font-sans font-semibold tracking-tight font-semibold mb-1">Aucune notification</h3>
                  <p className="text-sm text-muted-foreground">
                    Tes notifications apparaîtront ici
                  </p>
                </Card>
              )}
            </div>
          )}

          {/* ─── Tab: Settings ─── */}
          {activeTab === "settings" && (
            <div className="opacity-0 animate-fade-in" style={{ animationDelay: "300ms", animationFillMode: "forwards" }}>
              <Card className="rounded-xl">
                <CardHeader>
                  <CardTitle className="font-sans font-semibold tracking-tight text-lg">Préférences</CardTitle>
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

              {/* Email Preferences */}
              <Card className="rounded-xl mt-4">
                <CardHeader>
                  <CardTitle className="font-sans font-semibold tracking-tight text-lg flex items-center gap-2">
                    <Mail className="w-5 h-5 text-primary" />
                    Notifications email
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-5">
                  {preferences && (
                    <>
                      <div className="flex items-center justify-between">
                        <div>
                          <Label>Emails activés</Label>
                          <p className="text-xs text-muted-foreground">
                            Recevoir des emails pour les événements importants
                          </p>
                        </div>
                        <Switch
                          checked={preferences.email_notifications ?? true}
                          onCheckedChange={(v) => handleUpdatePreferences("email_notifications", v)}
                        />
                      </div>

                      {(preferences.email_notifications ?? true) && (
                        <>
                          <div className="flex items-center justify-between pl-8">
                            <div>
                              <Label>Social</Label>
                              <p className="text-xs text-muted-foreground">
                                Nouveaux followers, mentions
                              </p>
                            </div>
                            <Switch
                              checked={preferences.email_social ?? true}
                              onCheckedChange={(v) => handleUpdatePreferences("email_social", v)}
                            />
                          </div>

                          <div className="flex items-center justify-between pl-8">
                            <div>
                              <Label>Accomplissements</Label>
                              <p className="text-xs text-muted-foreground">
                                Badges, milestones
                              </p>
                            </div>
                            <Switch
                              checked={preferences.email_achievements ?? true}
                              onCheckedChange={(v) => handleUpdatePreferences("email_achievements", v)}
                            />
                          </div>

                          <div className="flex items-center justify-between pl-8">
                            <div>
                              <Label>Alertes streak</Label>
                              <p className="text-xs text-muted-foreground">
                                Email quand ton streak est en danger
                              </p>
                            </div>
                            <Switch
                              checked={preferences.email_streak ?? true}
                              onCheckedChange={(v) => handleUpdatePreferences("email_streak", v)}
                            />
                          </div>

                          <div className="flex items-center justify-between pl-8">
                            <div>
                              <Label>Résumé hebdomadaire</Label>
                              <p className="text-xs text-muted-foreground">
                                Récap de ta semaine par email
                              </p>
                            </div>
                            <Switch
                              checked={preferences.email_weekly_summary ?? true}
                              onCheckedChange={(v) => handleUpdatePreferences("email_weekly_summary", v)}
                            />
                          </div>
                        </>
                      )}
                    </>
                  )}
                </CardContent>
              </Card>
            </div>
          )}
        </div>
        </div>
      </main>
    </div>
  );
}
