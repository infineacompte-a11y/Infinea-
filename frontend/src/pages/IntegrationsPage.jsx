import React, { useState, useEffect } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";

// Available integrations - easily extendable
const AVAILABLE_INTEGRATIONS = [
  {
    id: "google_calendar",
    provider: "google_calendar",
    name: "Google Calendar",
    description: "Détecte automatiquement vos créneaux libres entre les réunions",
    icon: Calendar,
    color: "blue",
    category: "calendrier",
    status: "available",
    type: "url",
    urlLabel: "URL secrète iCal de Google Calendar",
    urlPlaceholder: "https://calendar.google.com/calendar/ical/.../basic.ics",
    urlHelp: "Google Calendar → Paramètres → Votre calendrier → Adresse secrète au format iCal. Copiez l'URL et collez-la ici.",
  },
  {
    id: "notion",
    provider: "notion",
    name: "Notion",
    description: "Exportez vos sessions comme pages Notion automatiquement",
    icon: FileText,
    color: "gray",
    category: "notes",
    status: "available",
    type: "token",
    tokenLabel: "Token d'intégration Notion",
    tokenPlaceholder: "secret_...",
    tokenHelp: "Créez une intégration sur notion.so/my-integrations, puis copiez le token.",
  },
  {
    id: "todoist",
    provider: "todoist",
    name: "Todoist",
    description: "Loguez vos sessions comme tâches complétées dans Todoist",
    icon: ListTodo,
    color: "red",
    category: "tâches",
    status: "available",
    type: "token",
    tokenLabel: "Token API Todoist",
    tokenPlaceholder: "votre token API",
    tokenHelp: "Allez dans Paramètres → Intégrations → Développeur pour copier votre token API.",
  },
  {
    id: "slack",
    provider: "slack",
    name: "Slack",
    description: "Recevez vos résumés hebdomadaires directement dans Slack",
    icon: MessageSquare,
    color: "purple",
    category: "communication",
    status: "available",
    type: "token",
    tokenLabel: "URL de webhook Slack",
    tokenPlaceholder: "https://hooks.slack.com/services/...",
    tokenHelp: "Créez un webhook entrant sur api.slack.com/messaging/webhooks.",
  },
  {
    id: "ical",
    provider: "ical",
    name: "iCal",
    description: "Importez votre calendrier iCal/ICS pour détecter vos créneaux libres",
    icon: Link2,
    color: "orange",
    category: "calendrier",
    status: "available",
    type: "url",
    urlLabel: "URL du calendrier iCal",
    urlPlaceholder: "https://calendar.example.com/basic.ics",
    urlHelp: "Collez l'URL .ics de votre application calendrier (Apple, Outlook, etc.).",
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
    description: "Détecte automatiquement vos créneaux libres entre les réunions",
    icon: Calendar,
    color: "blue",
    category: "calendrier",
    connectMode: "oauth",
  },
  {
    id: "ical",
    name: "Apple Calendar",
    description: "Importez votre calendrier Apple pour détecter vos créneaux libres",
    icon: Link2,
    color: "orange",
    category: "calendrier",
    connectMode: "guided", // Opens the step-by-step guide
  },
  {
    id: "notion",
    name: "Notion",
    description: "Exportez vos sessions comme pages Notion automatiquement",
    icon: FileText,
    color: "gray",
    category: "notes",
    connectMode: "oauth", // Uses OAuth popup
  },
  {
    id: "todoist",
    name: "Todoist",
    description: "Loguez vos sessions comme tâches complétées dans Todoist",
    icon: ListTodo,
    color: "red",
    category: "tâches",
    connectMode: "token", // Falls back to existing token dialog
  },
  {
    id: "slack",
    name: "Slack",
    description: "Recevez vos résumés hebdomadaires directement dans Slack",
    icon: MessageSquare,
    color: "purple",
    category: "communication",
    connectMode: "token", // Falls back to existing token dialog
  },
];

export default function IntegrationsPage() {
  const { user } = useAuth();
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
      toast.success(`${serviceName || "Service"} connecté avec succès!`);
      navigate("/integrations", { replace: true });
    } else if (error) {
      const errorMessages = {
        oauth_error: "Erreur lors de l'authentification",
        missing_params: "Paramètres manquants",
        invalid_state: "Session expirée, veuillez réessayer",
        connection_failed: "Échec de la connexion",
        not_configured: `${serviceName} n'est pas configuré sur ce serveur`,
        token_failed: "Échec de l'obtention du token",
        expired: "Lien expiré, veuillez réessayer",
        unknown_service: "Service inconnu",
        callback_failed: "Échec du callback OAuth",
      };
      toast.error(errorMessages[error] || "Une erreur est survenue");
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
      toast.error("Erreur de chargement");
    } finally {
      setIsLoading(false);
    }
  };

  const handleConnect = async (service) => {
    try {
      const response = await authFetch(`${API}/integrations/connect/${service}`);

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Erreur");
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
        throw new Error(err.detail || "Erreur");
      }
      const data = await response.json();
      toast.success(`${data.calendar_name || urlDialogService.name} connecté ! ${data.events_found || 0} événements trouvés.`);
      setUrlDialogService(null);
      setUrlValue("");
      fetchData();
    } catch (error) {
      toast.error(error.message || "Erreur de connexion");
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
        throw new Error(err.detail || "Erreur");
      }
      const data = await response.json();
      toast.success(`${data.account_name || tokenDialogService.name} connecté avec succès !`);
      setTokenDialogService(null);
      setTokenValue("");
      fetchData();
    } catch (error) {
      toast.error(error.message || "Erreur de connexion");
    } finally {
      setIsConnectingToken(false);
    }
  };

  const handleDisconnect = async (service) => {
    try {
      const response = await authFetch(`${API}/integrations/${service}`, {
        method: "DELETE",
      });

      if (!response.ok) throw new Error("Erreur");

      toast.success("Intégration déconnectée");
      setSelectedIntegration(null);
      fetchData();
    } catch (error) {
      toast.error("Erreur lors de la déconnexion");
    }
  };

  const handleSync = async (service) => {
    setIsSyncing(true);
    setSyncingService(service);
    try {
      const response = await authFetch(`${API}/integrations/${service}/sync`, {
        method: "POST",
      });

      if (!response.ok) throw new Error("Erreur");

      const data = await response.json();
      const msg = data.slots_detected != null
        ? `${data.slots_detected} créneaux détectés`
        : `${data.synced_count || 0} éléments synchronisés`;
      toast.success(`Synchronisation terminée: ${msg}`);
      fetchData();
    } catch (error) {
      toast.error("Erreur lors de la synchronisation");
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
      if (service === "google_calendar") {
        setShowGoogleGuide(true);
      } else {
        setShowAppleGuide(true);
      }
    } else if (method === "oauth" && status.connect_url) {
      // OAuth — redirect instantly using pre-generated URL (one click!)
      window.location.href = status.connect_url;
    } else if (method === "oauth") {
      // OAuth without pre-generated URL — fetch it
      try {
        const response = await authFetch(`${API}/integrations/connect/${service}`);
        if (!response.ok) {
          const err = await response.json();
          throw new Error(err.detail || "Erreur");
        }
        const data = await response.json();
        window.location.href = data.auth_url;
      } catch (error) {
        toast.error(error.message || "Erreur de connexion");
      }
    } else if (method === "token") {
      // Token/webhook — open smart token dialog with backend config
      const tc = status.token_config || {};
      setTokenDialogService({
        id: service,
        name: status.name,
        icon: ICON_MAP[service] || Plug,
        color: COLOR_MAP[service] || "blue",
        tokenLabel: tc.label || `Token ${status.name}`,
        tokenPlaceholder: tc.placeholder || "",
        tokenHelp: tc.help_url
          ? `Obtenez votre token sur ${tc.service_name || status.name}. `
          : `Entrez votre token ${status.name}.`,
        type: "token",
      });
    } else if (method === "url") {
      // URL — open URL dialog
      const legacyService = AVAILABLE_INTEGRATIONS.find((i) => i.id === service);
      if (legacyService) setUrlDialogService(legacyService);
    } else {
      toast.error("Ce service n'est pas disponible actuellement");
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
        toast.success("Connexion vérifiée — tout fonctionne !");
      } else {
        toast.error(data.error || "La connexion ne fonctionne plus");
      }
      fetchData();
    } catch (error) {
      toast.error("Impossible de tester la connexion");
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

      if (!response.ok) throw new Error("Erreur");

      setSlotSettings(newSettings);
      toast.success("Paramètres mis à jour");
    } catch (error) {
      toast.error("Erreur lors de la mise à jour");
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
    if (!acc[int.category]) acc[int.category] = [];
    acc[int.category].push(int);
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
                    Hub d'Intégrations
                  </h1>
                  <p className="text-muted-foreground">
                    Connectez vos outils pour des suggestions plus intelligentes
                  </p>
                </div>
              </div>
              {/* Connection summary */}
              <div className="flex items-center gap-3 mt-4">
                <Badge variant="secondary" className="text-xs">
                  {connectedCount}/{totalCount} connectés
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
                          Plan gratuit : 1 intégration max. Passez à Premium pour connecter tous vos outils.
                        </p>
                      </div>
                      <Link to="/pricing">
                        <Button size="sm" variant="outline" className="shrink-0">
                          Voir Premium
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
                        Détection des créneaux
                      </CardTitle>
                      <CardDescription>
                        Configurez comment InFinea détecte vos moments libres
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <Label>Activer la détection automatique</Label>
                          <p className="text-xs text-muted-foreground">
                            Analyse votre calendrier pour trouver des créneaux libres
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
                              Durée des créneaux : {slotSettings.min_slot_duration} - {slotSettings.max_slot_duration} min
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
                              <span className="text-muted-foreground">à</span>
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
                              <span className="text-muted-foreground">minutes</span>
                            </div>
                          </div>
                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <Label>Début de la fenêtre</Label>
                              <Input
                                type="time"
                                value={slotSettings.detection_window_start}
                                onChange={(e) =>
                                  handleUpdateSettings({ ...slotSettings, detection_window_start: e.target.value })
                                }
                              />
                            </div>
                            <div>
                              <Label>Fin de la fenêtre</Label>
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
                            <Label>Minutes d'avance pour la notification</Label>
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
              <DialogTitle>Paramètres de l'intégration</DialogTitle>
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
                      <p className="text-sm text-muted-foreground">Connecté le</p>
                      <p className="font-medium">
                        {selectedIntegration.connected_at
                          ? new Date(selectedIntegration.connected_at).toLocaleString("fr-FR")
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
                      Synchroniser
                    </Button>
                  </div>
                </div>
              )}
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setSelectedIntegration(null)}>
                Fermer
              </Button>
              <Button
                variant="destructive"
                onClick={() => handleDisconnect(selectedIntegration?.service)}
              >
                <Unplug className="w-4 h-4 mr-2" />
                Déconnecter
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
                Connecter {urlDialogService?.name}
              </DialogTitle>
              <DialogDescription>{urlDialogService?.urlHelp}</DialogDescription>
            </DialogHeader>
            <div className="py-4">
              <Label htmlFor="url-input">{urlDialogService?.urlLabel || "URL du calendrier"}</Label>
              <Input
                id="url-input" type="url"
                placeholder={urlDialogService?.urlPlaceholder || "https://..."}
                value={urlValue} onChange={(e) => setUrlValue(e.target.value)}
                className="mt-2" data-testid="url-connect-input"
              />
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => { setUrlDialogService(null); setUrlValue(""); }}>Annuler</Button>
              <Button onClick={handleConnectUrl} disabled={isConnectingUrl || !urlValue.trim()}>
                {isConnectingUrl ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Link2 className="w-4 h-4 mr-2" />}
                Connecter
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
                Connecter {tokenDialogService?.name}
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
                Votre token est chiffré et stocké de manière sécurisée.
              </p>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => { setTokenDialogService(null); setTokenValue(""); }}>Annuler</Button>
              <Button onClick={handleConnectToken} disabled={isConnectingToken || !tokenValue.trim()}>
                {isConnectingToken ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Plug className="w-4 h-4 mr-2" />}
                Connecter
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
                  Hub d'Intégrations
                </h1>
                <p className="text-muted-foreground">
                  Connectez vos outils pour des suggestions plus intelligentes
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
                          Plan gratuit : 1 intégration max. Passez à Premium pour connecter tous vos outils.
                        </p>
                      </div>
                      <Link to="/pricing">
                        <Button size="sm" variant="outline" className="shrink-0">
                          Voir Premium
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
                      Connectés ({connectedServices.length})
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
                                        Connecté
                                      </Badge>
                                    </div>
                                    <p className="text-sm text-muted-foreground">
                                      {info.account_name && <span className="mr-2">{info.account_name}</span>}
                                      Connecté le: {info.connected_at ? new Date(info.connected_at).toLocaleString("fr-FR") : "—"}
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
                                          Bientôt
                                        </Badge>
                                      )}
                                      {int.status === "premium" && (
                                        <Badge className="bg-amber-500/20 text-amber-500 text-xs">
                                          Premium
                                        </Badge>
                                      )}
                                    </div>
                                    <p className="text-sm text-muted-foreground mb-3">
                                      {int.description}
                                    </p>
                                    {isLimitReached ? (
                                      <Link to="/pricing">
                                        <Button size="sm" variant="outline" className="text-amber-500 border-amber-500/30">
                                          <Lock className="w-4 h-4 mr-2" />
                                          Premium requis
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
                                          Connecter
                                          <ChevronRight className="w-4 h-4 ml-1" />
                                        </Button>
                                      ) : (
                                        <div className="flex items-center gap-2 text-amber-500 text-sm">
                                          <AlertCircle className="w-4 h-4" />
                                          <span>Non configuré sur ce serveur</span>
                                        </div>
                                      )
                                    ) : (
                                      <Button size="sm" variant="secondary" disabled>
                                        <Lock className="w-4 h-4 mr-2" />
                                        Bientôt disponible
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
                      Détection des créneaux
                    </CardTitle>
                    <CardDescription>
                      Configurez comment InFinea détecte vos moments libres
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <Label>Activer la détection automatique</Label>
                        <p className="text-xs text-muted-foreground">
                          Analyse votre calendrier pour trouver des créneaux libres
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
                            Durée des créneaux : {slotSettings.min_slot_duration} - {slotSettings.max_slot_duration} min
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
                            <span className="text-muted-foreground">à</span>
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
                            <span className="text-muted-foreground">minutes</span>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <Label>Début de la fenêtre</Label>
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
                            <Label>Fin de la fenêtre</Label>
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
                          <Label>Minutes d'avance pour la notification</Label>
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
            <DialogTitle>Paramètres de l'intégration</DialogTitle>
            <DialogDescription>
              {selectedIntegration && (AVAILABLE_INTEGRATIONS.find((a) => a.id === selectedIntegration.service)?.name || selectedIntegration.service)}
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            {selectedIntegration && (
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 rounded-xl bg-white/5">
                  <div>
                    <p className="text-sm text-muted-foreground">Connecté le</p>
                    <p className="font-medium">
                      {selectedIntegration.connected_at
                        ? new Date(selectedIntegration.connected_at).toLocaleString("fr-FR")
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
                    Synchroniser
                  </Button>
                </div>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setSelectedIntegration(null)}>
              Fermer
            </Button>
            <Button
              variant="destructive"
              onClick={() => handleDisconnect(selectedIntegration?.service)}
            >
              <Unplug className="w-4 h-4 mr-2" />
              Déconnecter
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
              Connecter {urlDialogService?.name}
            </DialogTitle>
            <DialogDescription>
              {urlDialogService?.urlHelp}
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Label htmlFor="url-input">{urlDialogService?.urlLabel || "URL du calendrier"}</Label>
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
              Formats supportés : .ics, webcal://, https://
            </p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => { setUrlDialogService(null); setUrlValue(""); }}>
              Annuler
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
              Connecter
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
              Connecter {tokenDialogService?.name}
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
              Votre token est chiffré et stocké de manière sécurisée.
            </p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => { setTokenDialogService(null); setTokenValue(""); }}>
              Annuler
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
              Connecter
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
