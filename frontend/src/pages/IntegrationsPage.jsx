import React, { useState, useEffect } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import {
  Calendar,
  RefreshCw,
  Settings,
  Clock,
  Loader2,
  AlertCircle,
  CheckCircle2,
  Unplug,
  FileText,
  ListTodo,
  MessageSquare,
  Plug,
  ChevronRight,
  Lock,
  Link2,
  Wifi,
} from "lucide-react";
import { toast } from "sonner";
import { API, useAuth, authFetch } from "@/App";
import Sidebar from "@/components/Sidebar";
import IntegrationCard from "@/components/IntegrationCard";
import AppleCalendarGuide from "@/components/AppleCalendarGuide";
import GoogleCalendarGuide from "@/components/GoogleCalendarGuide";
import NotionGuide from "@/components/NotionGuide";
import TodoistGuide from "@/components/TodoistGuide";
import SlackGuide from "@/components/SlackGuide";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";

// Available integrations - easily extendable
// NOTE: name fields are brand names (not translated), descriptions use t() at render time
const AVAILABLE_INTEGRATIONS = [
  {
    id: "google_calendar",
    provider: "google_calendar",
    name: "Google Calendar",
    descriptionKey: "integrations.services.googleCalendar.description",
    icon: Calendar,
    color: "blue",
    categoryKey: "integrations.categories.calendar",
    status: "available",
    type: "url",
    urlLabelKey: "integrations.services.googleCalendar.urlLabel",
    urlPlaceholder: "https://calendar.google.com/calendar/ical/.../basic.ics",
    urlHelpKey: "integrations.services.googleCalendar.urlHelp",
  },
  {
    id: "notion",
    provider: "notion",
    name: "Notion",
    descriptionKey: "integrations.services.notion.description",
    icon: FileText,
    color: "gray",
    categoryKey: "integrations.categories.notes",
    status: "available",
    type: "token",
    tokenLabelKey: "integrations.services.notion.tokenLabel",
    tokenPlaceholder: "secret_...",
    tokenHelpKey: "integrations.services.notion.tokenHelp",
  },
  {
    id: "todoist",
    provider: "todoist",
    name: "Todoist",
    descriptionKey: "integrations.services.todoist.description",
    icon: ListTodo,
    color: "red",
    categoryKey: "integrations.categories.tasks",
    status: "available",
    type: "token",
    tokenLabelKey: "integrations.services.todoist.tokenLabel",
    tokenPlaceholder: "",
    tokenHelpKey: "integrations.services.todoist.tokenHelp",
  },
  {
    id: "slack",
    provider: "slack",
    name: "Slack",
    descriptionKey: "integrations.services.slack.description",
    icon: MessageSquare,
    color: "purple",
    categoryKey: "integrations.categories.communication",
    status: "available",
    type: "token",
    tokenLabelKey: "integrations.services.slack.tokenLabel",
    tokenPlaceholder: "https://hooks.slack.com/services/...",
    tokenHelpKey: "integrations.services.slack.tokenHelp",
  },
  {
    id: "ical",
    provider: "ical",
    name: "iCal",
    descriptionKey: "integrations.services.ical.description",
    icon: Link2,
    color: "orange",
    categoryKey: "integrations.categories.calendar",
    status: "available",
    type: "url",
    urlLabelKey: "integrations.services.ical.urlLabel",
    urlPlaceholder: "https://calendar.example.com/basic.ics",
    urlHelpKey: "integrations.services.ical.urlHelp",
  },
];

const colorClasses = {
  blue: { bg: "bg-blue-500/10", text: "text-blue-500", border: "border-blue-500/30" },
  gray: { bg: "bg-zinc-500/10", text: "text-zinc-400", border: "border-zinc-500/30" },
  red: { bg: "bg-red-500/10", text: "text-red-500", border: "border-red-500/30" },
  purple: { bg: "bg-purple-500/10", text: "text-purple-500", border: "border-purple-500/30" },
  green: { bg: "bg-emerald-500/10", text: "text-emerald-500", border: "border-emerald-500/30" },
  orange: { bg: "bg-orange-500/10", text: "text-orange-500", border: "border-orange-500/30" },
};

// Icon and color maps for backend-driven rendering
const ICON_MAP = {
  google_calendar: Calendar,
  ical: Link2,
  notion: FileText,
  todoist: ListTodo,
  slack: MessageSquare,
};

const COLOR_MAP = {
  google_calendar: "blue",
  ical: "orange",
  notion: "gray",
  todoist: "red",
  slack: "purple",
};

// Service definitions for the unified UI (fallback if status not loaded)
const UNIFIED_SERVICES = [
  {
    id: "google_calendar",
    name: "Google Calendar",
    descriptionKey: "integrations.services.googleCalendar.description",
    icon: Calendar,
    color: "blue",
    categoryKey: "integrations.categories.calendar",
    connectMode: "oauth",
  },
  {
    id: "ical",
    name: "Apple Calendar",
    descriptionKey: "integrations.services.ical.description",
    icon: Link2,
    color: "orange",
    categoryKey: "integrations.categories.calendar",
    connectMode: "guided", // Opens the step-by-step guide
  },
  {
    id: "notion",
    name: "Notion",
    descriptionKey: "integrations.services.notion.description",
    icon: FileText,
    color: "gray",
    categoryKey: "integrations.categories.notes",
    connectMode: "oauth", // Uses OAuth popup
  },
  {
    id: "todoist",
    name: "Todoist",
    descriptionKey: "integrations.services.todoist.description",
    icon: ListTodo,
    color: "red",
    categoryKey: "integrations.categories.tasks",
    connectMode: "token", // Falls back to existing token dialog
  },
  {
    id: "slack",
    name: "Slack",
    descriptionKey: "integrations.services.slack.description",
    icon: MessageSquare,
    color: "purple",
    categoryKey: "integrations.categories.communication",
    connectMode: "token", // Falls back to existing token dialog
  },
];

export default function IntegrationsPage() {
  const { user } = useAuth();
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [integrations, setIntegrations] = useState({});
  const [slotSettings, setSlotSettings] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncingService, setSyncingService] = useState(null);
  const [showSettings, setShowSettings] = useState(false);
  const [selectedIntegration, setSelectedIntegration] = useState(null);
  const [urlDialogService, setUrlDialogService] = useState(null);
  const [urlValue, setUrlValue] = useState("");
  const [isConnectingUrl, setIsConnectingUrl] = useState(false);
  const [tokenDialogService, setTokenDialogService] = useState(null);
  const [tokenValue, setTokenValue] = useState("");
  const [isConnectingToken, setIsConnectingToken] = useState(false);
  const [useUnifiedUI, setUseUnifiedUI] = useState(false);
  const [showAppleGuide, setShowAppleGuide] = useState(false);
  const [showGoogleGuide, setShowGoogleGuide] = useState(false);
  const [showNotionGuide, setShowNotionGuide] = useState(false);
  const [showTodoistGuide, setShowTodoistGuide] = useState(false);
  const [showSlackGuide, setShowSlackGuide] = useState(false);
  const [unifiedStatus, setUnifiedStatus] = useState({});
  const [testingService, setTestingService] = useState(null);

  useEffect(() => {
    // Check for OAuth callback results (supports all services)
    const success = searchParams.get("success");
    const error = searchParams.get("error");
    const service = searchParams.get("service") || success;
    const serviceName = AVAILABLE_INTEGRATIONS.find((i) => i.id === service)?.name ||
      UNIFIED_SERVICES.find((i) => i.id === service)?.name || service;

    if (success) {
      toast.success(t("integrations.toasts.connectedSuccess", { name: serviceName || t("integrations.defaultService") }));
      navigate("/integrations", { replace: true });
    } else if (error) {
      const errorMessages = {
        oauth_error: t("integrations.errors.oauthError"),
        missing_params: t("integrations.errors.missingParams"),
        invalid_state: t("integrations.errors.invalidState"),
        connection_failed: t("integrations.errors.connectionFailed"),
        not_configured: t("integrations.errors.notConfigured", { name: serviceName }),
        token_failed: t("integrations.errors.tokenFailed"),
        expired: t("integrations.errors.expired"),
        unknown_service: t("integrations.errors.unknownService"),
        callback_failed: t("integrations.errors.callbackFailed"),
      };
      toast.error(errorMessages[error] || t("integrations.errors.generic"));
      navigate("/integrations", { replace: true });
    }

    // Fetch feature flag
    authFetch(`${API}/feature-flags`)
      .then((res) => res.ok ? res.json() : { unified_integrations: false })
      .then((flags) => setUseUnifiedUI(flags.unified_integrations))
      .catch(() => {});

    fetchData();
  }, [searchParams, navigate]);

  const fetchData = async () => {
    try {
      const [intRes, settingsRes] = await Promise.all([
        authFetch(`${API}/integrations`),
        authFetch(`${API}/slots/settings`),
      ]);

      if (intRes.ok) {
        const data = await intRes.json();
        setIntegrations(data);
      }
      if (settingsRes.ok) setSlotSettings(await settingsRes.json());

      // Also fetch unified status if available
      try {
        const statusRes = await authFetch(`${API}/integrations/status`);
        if (statusRes.ok) setUnifiedStatus(await statusRes.json());
      } catch {}
    } catch (error) {
      toast.error(t("integrations.toasts.loadError"));
    } finally {
      setIsLoading(false);
    }
  };

  const handleConnect = async (service) => {
    try {
      const response = await authFetch(`${API}/integrations/connect/${service}`);

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || t("common.error"));
      }

      const data = await response.json();
      window.location.href = data.auth_url;
    } catch (error) {
      toast.error(error.message);
    }
  };

  const handleConnectUrl = async () => {
    if (!urlValue.trim() || !urlDialogService) return;
    setIsConnectingUrl(true);
    try {
      const serviceId = urlDialogService.id;
      const response = await authFetch(`${API}/integrations/${serviceId}/connect-url`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: urlValue.trim(), name: urlDialogService.name }),
      });
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || t("common.error"));
      }
      const data = await response.json();
      toast.success(t("integrations.toasts.urlConnected", { name: data.calendar_name || urlDialogService.name, count: data.events_found || 0 }));
      setUrlDialogService(null);
      setUrlValue("");
      fetchData();
    } catch (error) {
      toast.error(error.message || t("integrations.toasts.connectionError"));
    } finally {
      setIsConnectingUrl(false);
    }
  };

  const handleConnectToken = async () => {
    if (!tokenValue.trim() || !tokenDialogService) return;
    setIsConnectingToken(true);
    try {
      const response = await authFetch(`${API}/integrations/${tokenDialogService.id}/connect-token`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: tokenValue.trim() }),
      });
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || t("common.error"));
      }
      const data = await response.json();
      toast.success(t("integrations.toasts.tokenConnected", { name: data.account_name || tokenDialogService.name }));
      setTokenDialogService(null);
      setTokenValue("");
      fetchData();
    } catch (error) {
      toast.error(error.message || t("integrations.toasts.connectionError"));
    } finally {
      setIsConnectingToken(false);
    }
  };

  const handleDisconnect = async (service) => {
    try {
      const response = await authFetch(`${API}/integrations/${service}`, {
        method: "DELETE",
      });

      if (!response.ok) throw new Error(t("common.error"));

      toast.success(t("integrations.toasts.disconnected"));
      setSelectedIntegration(null);
      fetchData();
    } catch (error) {
      toast.error(t("integrations.toasts.disconnectError"));
    }
  };

  const handleSync = async (service) => {
    setIsSyncing(true);
    setSyncingService(service);
    try {
      const response = await authFetch(`${API}/integrations/${service}/sync`, {
        method: "POST",
      });

      if (!response.ok) throw new Error(t("common.error"));

      const data = await response.json();
      const msg = data.slots_detected != null
        ? t("integrations.toasts.slotsDetected", { count: data.slots_detected })
        : t("integrations.toasts.itemsSynced", { count: data.synced_count || 0 });
      toast.success(t("integrations.toasts.syncComplete", { details: msg }));
      fetchData();
    } catch (error) {
      toast.error(t("integrations.toasts.syncError"));
    } finally {
      setIsSyncing(false);
      setSyncingService(null);
    }
  };

  const handleUnifiedConnect = async (service) => {
    const status = unifiedStatus[service];
    if (!status) return;

    const method = status.preferred_method;

    if (method === "guided") {
      if (service === "google_calendar") setShowGoogleGuide(true);
      else if (service === "notion") setShowNotionGuide(true);
      else if (service === "todoist") setShowTodoistGuide(true);
      else if (service === "slack") setShowSlackGuide(true);
      else setShowAppleGuide(true);
    } else if (method === "oauth" && status.connect_url) {
      // OAuth — redirect instantly using pre-generated URL (one click!)
      window.location.href = status.connect_url;
    } else if (method === "oauth") {
      // OAuth without pre-generated URL — fetch it
      try {
        const response = await authFetch(`${API}/integrations/connect/${service}`);
        if (!response.ok) {
          const err = await response.json();
          throw new Error(err.detail || t("common.error"));
        }
        const data = await response.json();
        window.location.href = data.auth_url;
      } catch (error) {
        toast.error(error.message || t("integrations.toasts.connectionError"));
      }
    } else if (method === "token") {
      // Token/webhook — open smart token dialog with backend config
      const tc = status.token_config || {};
      setTokenDialogService({
        id: service,
        name: status.name,
        icon: ICON_MAP[service] || Plug,
        color: COLOR_MAP[service] || "blue",
        tokenLabel: tc.label || t("integrations.dialogs.tokenDefault", { name: status.name }),
        tokenPlaceholder: tc.placeholder || "",
        tokenHelp: tc.help_url
          ? t("integrations.dialogs.tokenHelpWithUrl", { name: tc.service_name || status.name })
          : t("integrations.dialogs.tokenHelpGeneric", { name: status.name }),
        type: "token",
      });
    } else if (method === "url") {
      // URL — open URL dialog
      const legacyService = AVAILABLE_INTEGRATIONS.find((i) => i.id === service);
      if (legacyService) setUrlDialogService(legacyService);
    } else {
      toast.error(t("integrations.errors.serviceUnavailable"));
    }
  };

  const handleTestConnection = async (service) => {
    setTestingService(service);
    try {
      const response = await authFetch(`${API}/integrations/${service}/test`, {
        method: "POST",
      });
      const data = await response.json();
      if (data.ok) {
        toast.success(t("integrations.toasts.testSuccess"));
      } else {
        toast.error(data.error || t("integrations.toasts.testFailed"));
      }
      fetchData();
    } catch (error) {
      toast.error(t("integrations.toasts.testError"));
    } finally {
      setTestingService(null);
    }
  };

  const handleUpdateSettings = async (newSettings) => {
    try {
      const response = await authFetch(`${API}/slots/settings`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(newSettings),
      });

      if (!response.ok) throw new Error(t("common.error"));

      setSlotSettings(newSettings);
      toast.success(t("integrations.toasts.settingsUpdated"));
    } catch (error) {
      toast.error(t("integrations.toasts.settingsError"));
    }
  };

  const getConnectedIntegration = (service) => {
    const info = integrations[service];
    return info?.connected ? info : null;
  };

  const isIntegrationAvailable = (service) => {
    const info = integrations[service];
    return info?.available !== false;
  };

  // Group integrations by category
  const groupedIntegrations = AVAILABLE_INTEGRATIONS.reduce((acc, int) => {
    const cat = t(int.categoryKey);
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(int);
    return acc;
  }, {});

  // ==================== UNIFIED UI ====================
  if (useUnifiedUI) {
    const serviceEntries = Object.entries(unifiedStatus);
    const connectedCount = serviceEntries.filter(([, s]) => s.connected).length;
    const totalCount = serviceEntries.length || UNIFIED_SERVICES.length;
    const isFreeUser = user?.subscription_tier !== "premium";
    const isLimitReached = isFreeUser && connectedCount >= 1;

    // Group by category from backend data
    const categories = {};
    serviceEntries.forEach(([id, svc]) => {
      const cat = svc.category || "autre";
      if (!categories[cat]) categories[cat] = [];
      categories[cat].push({ id, ...svc });
    });

    return (
      <div className="min-h-screen bg-background">
        <Sidebar />
        <main className="lg:ml-64 pt-20 lg:pt-8 px-4 lg:px-8 pb-8">
          <div className="max-w-4xl mx-auto">
            {/* Header */}
            <div className="mb-8">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
                  <Plug className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <h1 className="font-heading text-3xl font-semibold" data-testid="integrations-title">
                    {t("integrations.title")}
                  </h1>
                  <p className="text-muted-foreground">
                    {t("integrations.subtitle")}
                  </p>
                </div>
              </div>
              {/* Connection summary */}
              <div className="flex items-center gap-3 mt-4">
                <Badge variant="secondary" className="text-xs">
                  {t("integrations.connectedCount", { connected: connectedCount, total: totalCount })}
                </Badge>
              </div>
            </div>

            {isLoading ? (
              <div className="flex items-center justify-center py-20">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
              </div>
            ) : (
              <div className="space-y-8">
                {/* Free tier limit banner */}
                {isLimitReached && (
                  <Card className="border-amber-500/30 bg-amber-500/5">
                    <CardContent className="p-4 flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Lock className="w-5 h-5 text-amber-500" />
                        <p className="text-sm">
                          {t("integrations.freeTierBanner")}
                        </p>
                      </div>
                      <Link to="/pricing">
                        <Button size="sm" variant="outline" className="shrink-0">
                          {t("integrations.seePremium")}
                        </Button>
                      </Link>
                    </CardContent>
                  </Card>
                )}

                {/* Integration cards by category */}
                {Object.entries(categories).map(([category, services]) => (
                  <div key={category}>
                    <h2 className="text-sm font-medium text-muted-foreground mb-4 capitalize">
                      {category}
                    </h2>
                    <div className="grid gap-4">
                      {services.map((svc) => (
                        <IntegrationCard
                          key={svc.id}
                          service={svc.id}
                          name={svc.name}
                          description={svc.description}
                          icon={ICON_MAP[svc.id] || Plug}
                          color={COLOR_MAP[svc.id] || "blue"}
                          status={svc.status || "disconnected"}
                          accountName={svc.account_name}
                          connectedAt={svc.connected_at}
                          lastSync={svc.last_sync}
                          lastError={svc.last_error}
                          isSyncing={isSyncing && syncingService === svc.id}
                          isLimitReached={isLimitReached && !svc.connected}
                          onConnect={handleUnifiedConnect}
                          onDisconnect={(s) => {
                            setSelectedIntegration({ service: s, ...svc });
                          }}
                          onSync={handleSync}
                          onSettings={(s) => {
                            setSelectedIntegration({ service: s, ...svc });
                          }}
                          onTest={svc.connected ? handleTestConnection : undefined}
                        />
                      ))}
                    </div>
                  </div>
                ))}

                {/* Slot Detection Settings */}
                {slotSettings && (unifiedStatus.google_calendar?.connected || unifiedStatus.ical?.connected) && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="font-heading text-lg flex items-center gap-2">
                        <Clock className="w-5 h-5" />
                        {t("integrations.slotDetection.title")}
                      </CardTitle>
                      <CardDescription>
                        {t("integrations.slotDetection.description")}
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <Label>{t("integrations.slotDetection.enableAutoDetection")}</Label>
                          <p className="text-xs text-muted-foreground">
                            {t("integrations.slotDetection.enableAutoDetectionHelp")}
                          </p>
                        </div>
                        <Switch
                          checked={slotSettings.slot_detection_enabled}
                          onCheckedChange={(v) =>
                            handleUpdateSettings({ ...slotSettings, slot_detection_enabled: v })
                          }
                        />
                      </div>
                      {slotSettings.slot_detection_enabled && (
                        <>
                          <div>
                            <Label className="mb-3 block">
                              {t("integrations.slotDetection.slotDuration", { min: slotSettings.min_slot_duration, max: slotSettings.max_slot_duration })}
                            </Label>
                            <div className="flex items-center gap-4">
                              <Input
                                type="number"
                                value={slotSettings.min_slot_duration}
                                onChange={(e) =>
                                  handleUpdateSettings({
                                    ...slotSettings,
                                    min_slot_duration: parseInt(e.target.value) || 5,
                                  })
                                }
                                className="w-20" min={2} max={15}
                              />
                              <span className="text-muted-foreground">{t("integrations.slotDetection.to")}</span>
                              <Input
                                type="number"
                                value={slotSettings.max_slot_duration}
                                onChange={(e) =>
                                  handleUpdateSettings({
                                    ...slotSettings,
                                    max_slot_duration: parseInt(e.target.value) || 20,
                                  })
                                }
                                className="w-20" min={5} max={30}
                              />
                              <span className="text-muted-foreground">{t("common.minutes")}</span>
                            </div>
                          </div>
                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <Label>{t("integrations.slotDetection.windowStart")}</Label>
                              <Input
                                type="time"
                                value={slotSettings.detection_window_start}
                                onChange={(e) =>
                                  handleUpdateSettings({ ...slotSettings, detection_window_start: e.target.value })
                                }
                              />
                            </div>
                            <div>
                              <Label>{t("integrations.slotDetection.windowEnd")}</Label>
                              <Input
                                type="time"
                                value={slotSettings.detection_window_end}
                                onChange={(e) =>
                                  handleUpdateSettings({ ...slotSettings, detection_window_end: e.target.value })
                                }
                              />
                            </div>
                          </div>
                          <div>
                            <Label>{t("integrations.slotDetection.advanceNotification")}</Label>
                            <Input
                              type="number"
                              value={slotSettings.advance_notification_minutes}
                              onChange={(e) =>
                                handleUpdateSettings({
                                  ...slotSettings,
                                  advance_notification_minutes: parseInt(e.target.value) || 5,
                                })
                              }
                              className="w-24 mt-2" min={1} max={30}
                            />
                          </div>
                        </>
                      )}
                    </CardContent>
                  </Card>
                )}
              </div>
            )}
          </div>
        </main>

        {/* Reuse existing dialogs for fallback */}
        {/* Integration Settings Dialog */}
        <Dialog open={!!selectedIntegration} onOpenChange={() => setSelectedIntegration(null)}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{t("integrations.dialogs.settingsTitle")}</DialogTitle>
              <DialogDescription>
                {selectedIntegration && (
                  unifiedStatus[selectedIntegration.service]?.name ||
                  selectedIntegration.service
                )}
              </DialogDescription>
            </DialogHeader>
            <div className="py-4">
              {selectedIntegration && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 rounded-xl bg-white/5">
                    <div>
                      <p className="text-sm text-muted-foreground">{t("integrations.dialogs.connectedOn")}</p>
                      <p className="font-medium">
                        {selectedIntegration.connected_at
                          ? new Date(selectedIntegration.connected_at).toLocaleString(i18n.language)
                          : "—"}
                      </p>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleSync(selectedIntegration.service)}
                      disabled={isSyncing}
                    >
                      {isSyncing ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4 mr-2" />}
                      {t("integrations.actions.sync")}
                    </Button>
                  </div>
                </div>
              )}
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setSelectedIntegration(null)}>
                {t("common.close")}
              </Button>
              <Button
                variant="destructive"
                onClick={() => handleDisconnect(selectedIntegration?.service)}
              >
                <Unplug className="w-4 h-4 mr-2" />
                {t("integrations.actions.disconnect")}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* URL Connect Dialog (fallback for Google Calendar) */}
        <Dialog open={!!urlDialogService} onOpenChange={() => { setUrlDialogService(null); setUrlValue(""); }}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                {urlDialogService && (() => {
                  const Icon = urlDialogService.icon;
                  const colors = colorClasses[urlDialogService.color];
                  return <div className={`w-8 h-8 rounded-lg ${colors?.bg} flex items-center justify-center`}>
                    <Icon className={`w-4 h-4 ${colors?.text}`} />
                  </div>;
                })()}
                {t("integrations.actions.connect")} {urlDialogService?.name}
              </DialogTitle>
              <DialogDescription>{urlDialogService && t(urlDialogService.urlHelpKey)}</DialogDescription>
            </DialogHeader>
            <div className="py-4">
              <Label htmlFor="url-input">{urlDialogService ? t(urlDialogService.urlLabelKey) : t("integrations.dialogs.calendarUrl")}</Label>
              <Input
                id="url-input" type="url"
                placeholder={urlDialogService?.urlPlaceholder || "https://..."}
                value={urlValue} onChange={(e) => setUrlValue(e.target.value)}
                className="mt-2" data-testid="url-connect-input"
              />
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => { setUrlDialogService(null); setUrlValue(""); }}>{t("common.cancel")}</Button>
              <Button onClick={handleConnectUrl} disabled={isConnectingUrl || !urlValue.trim()}>
                {isConnectingUrl ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Link2 className="w-4 h-4 mr-2" />}
                {t("integrations.actions.connect")}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Token Connect Dialog (fallback for Todoist, Slack) */}
        <Dialog open={!!tokenDialogService} onOpenChange={() => { setTokenDialogService(null); setTokenValue(""); }}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                {tokenDialogService && (() => {
                  const Icon = tokenDialogService.icon;
                  const colors = colorClasses[tokenDialogService.color];
                  return <div className={`w-8 h-8 rounded-lg ${colors?.bg} flex items-center justify-center`}>
                    <Icon className={`w-4 h-4 ${colors?.text}`} />
                  </div>;
                })()}
                {t("integrations.actions.connect")} {tokenDialogService?.name}
              </DialogTitle>
              <DialogDescription>{tokenDialogService?.tokenHelp}</DialogDescription>
            </DialogHeader>
            <div className="py-4">
              <Label htmlFor="token-input">{tokenDialogService?.tokenLabel}</Label>
              <Input
                id="token-input" type="text"
                placeholder={tokenDialogService?.tokenPlaceholder}
                value={tokenValue} onChange={(e) => setTokenValue(e.target.value)}
                className="mt-2 font-mono text-sm" data-testid="token-input"
              />
              <p className="text-xs text-muted-foreground mt-2">
                {t("integrations.dialogs.tokenSecure")}
              </p>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => { setTokenDialogService(null); setTokenValue(""); }}>{t("common.cancel")}</Button>
              <Button onClick={handleConnectToken} disabled={isConnectingToken || !tokenValue.trim()}>
                {isConnectingToken ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Plug className="w-4 h-4 mr-2" />}
                {t("integrations.actions.connect")}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Apple Calendar Guide */}
        <AppleCalendarGuide
          open={showAppleGuide}
          onOpenChange={setShowAppleGuide}
          onConnected={fetchData}
        />

        {/* Google Calendar Guide */}
        <GoogleCalendarGuide
          open={showGoogleGuide}
          onOpenChange={setShowGoogleGuide}
          onConnected={fetchData}
        />

        {/* Notion Guide */}
        <NotionGuide
          open={showNotionGuide}
          onOpenChange={setShowNotionGuide}
          onConnected={fetchData}
        />

        {/* Todoist Guide */}
        <TodoistGuide
          open={showTodoistGuide}
          onOpenChange={setShowTodoistGuide}
          onConnected={fetchData}
        />

        {/* Slack Guide */}
        <SlackGuide
          open={showSlackGuide}
          onOpenChange={setShowSlackGuide}
          onConnected={fetchData}
        />
      </div>
    );
  }

  // ==================== LEGACY UI (flag off) ====================
  return (
    <div className="min-h-screen bg-background">
      <Sidebar />

      {/* Main Content */}
      <main className="lg:ml-64 pt-20 lg:pt-8 px-4 lg:px-8 pb-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
                <Plug className="w-6 h-6 text-primary" />
              </div>
              <div>
                <h1 className="font-heading text-3xl font-semibold" data-testid="integrations-title">
                  {t("integrations.title")}
                </h1>
                <p className="text-muted-foreground">
                  {t("integrations.subtitle")}
                </p>
              </div>
            </div>
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : (
            <div className="space-y-8">
              {/* Free tier limit banner */}
              {user?.subscription_tier !== "premium" && (() => {
                const connectedCount = AVAILABLE_INTEGRATIONS.filter(
                  (a) => integrations[a.id]?.connected
                ).length;
                return connectedCount >= 1 ? (
                  <Card className="border-amber-500/30 bg-amber-500/5">
                    <CardContent className="p-4 flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Lock className="w-5 h-5 text-amber-500" />
                        <p className="text-sm">
                          {t("integrations.freeTierBanner")}
                        </p>
                      </div>
                      <Link to="/pricing">
                        <Button size="sm" variant="outline" className="shrink-0">
                          {t("integrations.seePremium")}
                        </Button>
                      </Link>
                    </CardContent>
                  </Card>
                ) : null;
              })()}

              {/* Connected Integrations */}
              {(() => {
                const connectedServices = AVAILABLE_INTEGRATIONS.filter(
                  (a) => integrations[a.id]?.connected
                );
                if (connectedServices.length === 0) return null;

                return (
                  <div>
                    <h2 className="text-sm font-medium text-muted-foreground mb-4 flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                      {t("integrations.connectedSection", { count: connectedServices.length })}
                    </h2>
                    <div className="grid gap-4">
                      {connectedServices.map((config) => {
                        const info = integrations[config.id];
                        const Icon = config.icon;
                        const colors = colorClasses[config.color];

                        return (
                          <Card key={config.id} className={`${colors.border} border`}>
                            <CardContent className="p-4">
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-4">
                                  <div className={`w-12 h-12 rounded-xl ${colors.bg} flex items-center justify-center`}>
                                    <Icon className={`w-6 h-6 ${colors.text}`} />
                                  </div>
                                  <div>
                                    <div className="flex items-center gap-2 mb-1">
                                      <h3 className="font-heading font-semibold">{config.name}</h3>
                                      <Badge className="bg-emerald-500/20 text-emerald-500 border-emerald-500/30">
                                        <CheckCircle2 className="w-3 h-3 mr-1" />
                                        {t("integrations.status.connected")}
                                      </Badge>
                                    </div>
                                    <p className="text-sm text-muted-foreground">
                                      {info.account_name && <span className="mr-2">{info.account_name}</span>}
                                      {t("integrations.dialogs.connectedOn")}: {info.connected_at ? new Date(info.connected_at).toLocaleString(i18n.language) : "—"}
                                    </p>
                                  </div>
                                </div>
                                <div className="flex gap-2">
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => handleSync(config.id)}
                                    disabled={isSyncing}
                                    data-testid="sync-btn"
                                  >
                                    {isSyncing ? (
                                      <Loader2 className="w-4 h-4 animate-spin" />
                                    ) : (
                                      <RefreshCw className="w-4 h-4" />
                                    )}
                                  </Button>
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => setSelectedIntegration({ service: config.id, ...info })}
                                  >
                                    <Settings className="w-4 h-4" />
                                  </Button>
                                </div>
                              </div>
                            </CardContent>
                          </Card>
                        );
                      })}
                    </div>
                  </div>
                );
              })()}

              {/* Available Integrations by Category */}
              {(() => {
                const connectedCount = AVAILABLE_INTEGRATIONS.filter(
                  (a) => integrations[a.id]?.connected
                ).length;
                const isFreeUser = user?.subscription_tier !== "premium";
                const isLimitReached = isFreeUser && connectedCount >= 1;

                return Object.entries(groupedIntegrations).map(([category, ints]) => {
                  const availableInts = ints.filter(
                    (int) => !integrations[int.id]?.connected
                  );

                  if (availableInts.length === 0) return null;

                  return (
                    <div key={category}>
                      <h2 className="text-sm font-medium text-muted-foreground mb-4 capitalize">
                        {category}
                      </h2>
                      <div className="grid md:grid-cols-2 gap-4">
                        {availableInts.map((int) => {
                          const Icon = int.icon;
                          const colors = colorClasses[int.color];
                          const isAvailable = int.status === "available" && isIntegrationAvailable(int.provider);

                          return (
                            <Card
                              key={int.id}
                              className={`transition-all ${
                                int.status === "coming_soon" || isLimitReached ? "opacity-60" : "hover:border-primary/50"
                              }`}
                              data-testid={`integration-${int.id}`}
                            >
                              <CardContent className="p-4">
                                <div className="flex items-start gap-4">
                                  <div className={`w-12 h-12 rounded-xl ${colors.bg} flex items-center justify-center shrink-0`}>
                                    <Icon className={`w-6 h-6 ${colors.text}`} />
                                  </div>
                                  <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2 mb-1">
                                      <h3 className="font-heading font-semibold">{int.name}</h3>
                                      {int.status === "coming_soon" && (
                                        <Badge variant="secondary" className="text-xs">
                                          {t("integrations.status.comingSoon")}
                                        </Badge>
                                      )}
                                      {int.status === "premium" && (
                                        <Badge className="bg-amber-500/20 text-amber-500 text-xs">
                                          Premium
                                        </Badge>
                                      )}
                                    </div>
                                    <p className="text-sm text-muted-foreground mb-3">
                                      {t(int.descriptionKey)}
                                    </p>
                                    {isLimitReached ? (
                                      <Link to="/pricing">
                                        <Button size="sm" variant="outline" className="text-amber-500 border-amber-500/30">
                                          <Lock className="w-4 h-4 mr-2" />
                                          {t("integrations.premiumRequired")}
                                        </Button>
                                      </Link>
                                    ) : int.status === "available" ? (
                                      isAvailable ? (
                                        <Button
                                          size="sm"
                                          onClick={() => {
                                            if (int.type === "url") setUrlDialogService(int);
                                            else if (int.type === "token") setTokenDialogService(int);
                                            else handleConnect(int.provider);
                                          }}
                                          data-testid={`connect-${int.id}-btn`}
                                        >
                                          {t("integrations.actions.connect")}
                                          <ChevronRight className="w-4 h-4 ml-1" />
                                        </Button>
                                      ) : (
                                        <div className="flex items-center gap-2 text-amber-500 text-sm">
                                          <AlertCircle className="w-4 h-4" />
                                          <span>{t("integrations.notConfiguredOnServer")}</span>
                                        </div>
                                      )
                                    ) : (
                                      <Button size="sm" variant="secondary" disabled>
                                        <Lock className="w-4 h-4 mr-2" />
                                        {t("integrations.status.comingSoonFull")}
                                      </Button>
                                    )}
                                  </div>
                                </div>
                              </CardContent>
                            </Card>
                          );
                        })}
                      </div>
                    </div>
                  );
                });
              })()}

              {/* Slot Detection Settings */}
              {slotSettings && (integrations.google_calendar?.connected || integrations.ical?.connected) && (
                <Card>
                  <CardHeader>
                    <CardTitle className="font-heading text-lg flex items-center gap-2">
                      <Clock className="w-5 h-5" />
                      {t("integrations.slotDetection.title")}
                    </CardTitle>
                    <CardDescription>
                      {t("integrations.slotDetection.description")}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <Label>{t("integrations.slotDetection.enableAutoDetection")}</Label>
                        <p className="text-xs text-muted-foreground">
                          {t("integrations.slotDetection.enableAutoDetectionHelp")}
                        </p>
                      </div>
                      <Switch
                        checked={slotSettings.slot_detection_enabled}
                        onCheckedChange={(v) =>
                          handleUpdateSettings({ ...slotSettings, slot_detection_enabled: v })
                        }
                        data-testid="toggle-detection"
                      />
                    </div>

                    {slotSettings.slot_detection_enabled && (
                      <>
                        <div>
                          <Label className="mb-3 block">
                            {t("integrations.slotDetection.slotDuration", { min: slotSettings.min_slot_duration, max: slotSettings.max_slot_duration })}
                          </Label>
                          <div className="flex items-center gap-4">
                            <Input
                              type="number"
                              value={slotSettings.min_slot_duration}
                              onChange={(e) =>
                                handleUpdateSettings({
                                  ...slotSettings,
                                  min_slot_duration: parseInt(e.target.value) || 5,
                                })
                              }
                              className="w-20"
                              min={2}
                              max={15}
                            />
                            <span className="text-muted-foreground">{t("integrations.slotDetection.to")}</span>
                            <Input
                              type="number"
                              value={slotSettings.max_slot_duration}
                              onChange={(e) =>
                                handleUpdateSettings({
                                  ...slotSettings,
                                  max_slot_duration: parseInt(e.target.value) || 20,
                                })
                              }
                              className="w-20"
                              min={5}
                              max={30}
                            />
                            <span className="text-muted-foreground">{t("common.minutes")}</span>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <Label>{t("integrations.slotDetection.windowStart")}</Label>
                            <Input
                              type="time"
                              value={slotSettings.detection_window_start}
                              onChange={(e) =>
                                handleUpdateSettings({
                                  ...slotSettings,
                                  detection_window_start: e.target.value,
                                })
                              }
                            />
                          </div>
                          <div>
                            <Label>{t("integrations.slotDetection.windowEnd")}</Label>
                            <Input
                              type="time"
                              value={slotSettings.detection_window_end}
                              onChange={(e) =>
                                handleUpdateSettings({
                                  ...slotSettings,
                                  detection_window_end: e.target.value,
                                })
                              }
                            />
                          </div>
                        </div>

                        <div>
                          <Label>{t("integrations.slotDetection.advanceNotification")}</Label>
                          <Input
                            type="number"
                            value={slotSettings.advance_notification_minutes}
                            onChange={(e) =>
                              handleUpdateSettings({
                                ...slotSettings,
                                advance_notification_minutes: parseInt(e.target.value) || 5,
                              })
                            }
                            className="w-24 mt-2"
                            min={1}
                            max={30}
                          />
                        </div>
                      </>
                    )}
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </div>
      </main>

      {/* Integration Settings Dialog */}
      <Dialog open={!!selectedIntegration} onOpenChange={() => setSelectedIntegration(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t("integrations.dialogs.settingsTitle")}</DialogTitle>
            <DialogDescription>
              {selectedIntegration && (AVAILABLE_INTEGRATIONS.find((a) => a.id === selectedIntegration.service)?.name || selectedIntegration.service)}
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            {selectedIntegration && (
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 rounded-xl bg-white/5">
                  <div>
                    <p className="text-sm text-muted-foreground">{t("integrations.dialogs.connectedOn")}</p>
                    <p className="font-medium">
                      {selectedIntegration.connected_at
                        ? new Date(selectedIntegration.connected_at).toLocaleString(i18n.language)
                        : "—"}
                    </p>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleSync(selectedIntegration.service)}
                    disabled={isSyncing}
                  >
                    {isSyncing ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <RefreshCw className="w-4 h-4 mr-2" />
                    )}
                    {t("integrations.actions.sync")}
                  </Button>
                </div>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setSelectedIntegration(null)}>
              {t("common.close")}
            </Button>
            <Button
              variant="destructive"
              onClick={() => handleDisconnect(selectedIntegration?.service)}
            >
              <Unplug className="w-4 h-4 mr-2" />
              {t("integrations.actions.disconnect")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* URL Connect Dialog (iCal, Google Calendar) */}
      <Dialog open={!!urlDialogService} onOpenChange={() => { setUrlDialogService(null); setUrlValue(""); }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {urlDialogService && (() => {
                const Icon = urlDialogService.icon;
                const colors = colorClasses[urlDialogService.color];
                return <div className={`w-8 h-8 rounded-lg ${colors?.bg} flex items-center justify-center`}>
                  <Icon className={`w-4 h-4 ${colors?.text}`} />
                </div>;
              })()}
              {t("integrations.actions.connect")} {urlDialogService?.name}
            </DialogTitle>
            <DialogDescription>
              {urlDialogService && t(urlDialogService.urlHelpKey)}
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Label htmlFor="url-input">{urlDialogService ? t(urlDialogService.urlLabelKey) : t("integrations.dialogs.calendarUrl")}</Label>
            <Input
              id="url-input"
              type="url"
              placeholder={urlDialogService?.urlPlaceholder || "https://..."}
              value={urlValue}
              onChange={(e) => setUrlValue(e.target.value)}
              className="mt-2"
              data-testid="url-connect-input"
            />
            <p className="text-xs text-muted-foreground mt-2">
              {t("integrations.dialogs.supportedFormats")}
            </p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => { setUrlDialogService(null); setUrlValue(""); }}>
              {t("common.cancel")}
            </Button>
            <Button
              onClick={handleConnectUrl}
              disabled={isConnectingUrl || !urlValue.trim()}
            >
              {isConnectingUrl ? (
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
              ) : (
                <Link2 className="w-4 h-4 mr-2" />
              )}
              {t("integrations.actions.connect")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Token/URL Connect Dialog (Notion, Todoist, Slack) */}
      <Dialog open={!!tokenDialogService} onOpenChange={() => { setTokenDialogService(null); setTokenValue(""); }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {tokenDialogService && (() => {
                const Icon = tokenDialogService.icon;
                const colors = colorClasses[tokenDialogService.color];
                return <div className={`w-8 h-8 rounded-lg ${colors?.bg} flex items-center justify-center`}>
                  <Icon className={`w-4 h-4 ${colors?.text}`} />
                </div>;
              })()}
              {t("integrations.actions.connect")} {tokenDialogService?.name}
            </DialogTitle>
            <DialogDescription>
              {tokenDialogService?.tokenHelp}
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Label htmlFor="token-input">{tokenDialogService?.tokenLabel}</Label>
            <Input
              id="token-input"
              type="text"
              placeholder={tokenDialogService?.tokenPlaceholder}
              value={tokenValue}
              onChange={(e) => setTokenValue(e.target.value)}
              className="mt-2 font-mono text-sm"
              data-testid="token-input"
            />
            <p className="text-xs text-muted-foreground mt-2">
              {t("integrations.dialogs.tokenSecure")}
            </p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => { setTokenDialogService(null); setTokenValue(""); }}>
              {t("common.cancel")}
            </Button>
            <Button
              onClick={handleConnectToken}
              disabled={isConnectingToken || !tokenValue.trim()}
            >
              {isConnectingToken ? (
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
              ) : (
                <Plug className="w-4 h-4 mr-2" />
              )}
              {t("integrations.actions.connect")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
