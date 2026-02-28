import React, { useState, useEffect } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import {
  Timer,
  Sparkles,
  LayoutGrid,
  BarChart3,
  User,
  LogOut,
  Menu,
  Calendar,
  Check,
  RefreshCw,
  ExternalLink,
  Settings,
  Clock,
  Loader2,
  AlertCircle,
  CheckCircle2,
  Unplug,
  Brain,
  FileText,
  ListTodo,
  MessageSquare,
  Plug,
  ChevronRight,
  Lock,
  Award,
  Link2,
} from "lucide-react";
import { toast } from "sonner";
import { API, useAuth, authFetch } from "@/App";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
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

export default function IntegrationsPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [integrations, setIntegrations] = useState({});
  const [slotSettings, setSlotSettings] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSyncing, setIsSyncing] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [selectedIntegration, setSelectedIntegration] = useState(null);
  const [urlDialogService, setUrlDialogService] = useState(null);
  const [urlValue, setUrlValue] = useState("");
  const [isConnectingUrl, setIsConnectingUrl] = useState(false);
  const [tokenDialogService, setTokenDialogService] = useState(null);
  const [tokenValue, setTokenValue] = useState("");
  const [isConnectingToken, setIsConnectingToken] = useState(false);

  useEffect(() => {
    // Check for OAuth callback results (supports all services)
    const success = searchParams.get("success");
    const error = searchParams.get("error");
    const service = searchParams.get("service");
    const serviceName = AVAILABLE_INTEGRATIONS.find((i) => i.id === service)?.name || service;

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
        // Backend returns { google_calendar: { connected, available, ... }, notion: {...}, ... }
        setIntegrations(data);
      }
      if (settingsRes.ok) setSlotSettings(await settingsRes.json());
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

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  const getConnectedIntegration = (service) => {
    const info = integrations[service];
    return info?.connected ? info : null;
  };

  const isIntegrationAvailable = (service) => {
    const info = integrations[service];
    return info?.available !== false;
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
        to="/journal"
        className="nav-item flex items-center gap-3 px-4 py-3 rounded-xl text-muted-foreground hover:text-foreground"
        onClick={() => mobile && setMobileMenuOpen(false)}
      >
        <Brain className="w-5 h-5" />
        <span>Journal</span>
      </Link>
      <Link
        to="/integrations"
        className="nav-item active flex items-center gap-3 px-4 py-3 rounded-xl"
        onClick={() => mobile && setMobileMenuOpen(false)}
      >
        <Plug className="w-5 h-5" />
        <span>Intégrations</span>
      </Link>
      <Link
        to="/badges"
        className="nav-item flex items-center gap-3 px-4 py-3 rounded-xl text-muted-foreground hover:text-foreground"
        onClick={() => mobile && setMobileMenuOpen(false)}
      >
        <Award className="w-5 h-5" />
        <span>Badges</span>
      </Link>
      <Link
        to="/progress"
        className="nav-item flex items-center gap-3 px-4 py-3 rounded-xl text-muted-foreground hover:text-foreground"
        onClick={() => mobile && setMobileMenuOpen(false)}
      >
        <BarChart3 className="w-5 h-5" />
        <span>Progression</span>
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

  // Group integrations by category
  const groupedIntegrations = AVAILABLE_INTEGRATIONS.reduce((acc, int) => {
    if (!acc[int.category]) acc[int.category] = [];
    acc[int.category].push(int);
    return acc;
  }, {});

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
