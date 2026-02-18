import React, { useState, useEffect } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import {
  Timer,
  Sparkles,
  LayoutGrid,
  BarChart3,
  User,
  LogOut,
  Menu,
  Calendar,
  BookOpen,
  CheckSquare,
  MessageSquare,
  ChevronRight,
  ExternalLink,
  RefreshCw,
  Unplug,
  Check,
  AlertCircle,
  Loader2,
} from "lucide-react";
import { toast } from "sonner";
import { API, authFetch, useAuth } from "@/App";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";

const SERVICE_META = {
  google_calendar: {
    name: "Google Calendar",
    description: "Synchronisez vos sessions comme des événements dans votre agenda Google.",
    icon: Calendar,
    color: "text-blue-500 bg-blue-500/10",
    features: ["Sessions ajoutées automatiquement", "Visualisez votre progression dans l'agenda"],
  },
  notion: {
    name: "Notion",
    description: "Exportez vos sessions dans une page Notion pour un suivi détaillé.",
    icon: BookOpen,
    color: "text-gray-800 dark:text-gray-200 bg-gray-500/10",
    features: ["Pages créées pour chaque session", "Organisation par catégorie"],
  },
  todoist: {
    name: "Todoist",
    description: "Créez des tâches complétées dans Todoist pour suivre vos micro-actions.",
    icon: CheckSquare,
    color: "text-red-500 bg-red-500/10",
    features: ["Tâches marquées comme complétées", "Historique de productivité"],
  },
  slack: {
    name: "Slack",
    description: "Recevez un résumé hebdomadaire de vos sessions directement dans Slack.",
    icon: MessageSquare,
    color: "text-purple-500 bg-purple-500/10",
    features: ["Résumé hebdomadaire automatique", "Notifications de streak"],
  },
};

export default function IntegrationsPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [integrations, setIntegrations] = useState({});
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(null);
  const [syncing, setSyncing] = useState(null);
  const [disconnecting, setDisconnecting] = useState(null);

  useEffect(() => {
    fetchIntegrations();
  }, []);

  // Handle OAuth callback params
  useEffect(() => {
    const success = searchParams.get("success");
    const error = searchParams.get("error");
    const service = searchParams.get("service");
    const serviceName = SERVICE_META[service]?.name || service;

    if (success === "true" && service) {
      toast.success(`${serviceName} connecté avec succès !`);
      fetchIntegrations();
      // Clean URL
      window.history.replaceState({}, "", "/integrations");
    } else if (error && service) {
      const errorMessages = {
        invalid_state: "Session expirée, veuillez réessayer.",
        expired: "La demande a expiré, veuillez réessayer.",
        token_failed: "Échec de l'authentification. Veuillez réessayer.",
        callback_failed: "Erreur de connexion. Veuillez réessayer.",
        not_configured: `${serviceName} n'est pas encore configuré.`,
      };
      toast.error(errorMessages[error] || `Erreur de connexion à ${serviceName}`);
      window.history.replaceState({}, "", "/integrations");
    }
  }, [searchParams]);

  const fetchIntegrations = async () => {
    try {
      const response = await authFetch(`${API}/integrations`);
      if (response.ok) {
        const data = await response.json();
        setIntegrations(data);
      }
    } catch (e) {
      console.error("Failed to fetch integrations:", e);
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = async (service) => {
    setConnecting(service);
    try {
      const response = await authFetch(`${API}/integrations/connect/${service}`);
      if (response.ok) {
        const data = await response.json();
        // Redirect to OAuth provider
        window.location.href = data.auth_url;
      } else {
        const err = await response.json();
        toast.error(err.detail || "Erreur de connexion");
      }
    } catch (e) {
      toast.error("Erreur de connexion au service");
    } finally {
      setConnecting(null);
    }
  };

  const handleDisconnect = async (service) => {
    const serviceName = SERVICE_META[service]?.name || service;
    setDisconnecting(service);
    try {
      const response = await authFetch(`${API}/integrations/${service}`, {
        method: "DELETE",
      });
      if (response.ok) {
        toast.success(`${serviceName} déconnecté`);
        fetchIntegrations();
      }
    } catch (e) {
      toast.error("Erreur lors de la déconnexion");
    } finally {
      setDisconnecting(null);
    }
  };

  const handleSync = async (service) => {
    const serviceName = SERVICE_META[service]?.name || service;
    setSyncing(service);
    try {
      const response = await authFetch(`${API}/integrations/${service}/sync`, {
        method: "POST",
      });
      if (response.ok) {
        const data = await response.json();
        toast.success(`${data.synced_count} sessions synchronisées avec ${serviceName}`);
      } else {
        const err = await response.json();
        toast.error(err.detail || "Erreur de synchronisation");
      }
    } catch (e) {
      toast.error("Erreur de synchronisation");
    } finally {
      setSyncing(null);
    }
  };

  const handleToggleSync = async (service, enabled) => {
    try {
      await authFetch(`${API}/integrations/${service}/sync`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sync_enabled: enabled }),
      });
      setIntegrations((prev) => ({
        ...prev,
        [service]: { ...prev[service], sync_enabled: enabled },
      }));
    } catch (e) {
      toast.error("Erreur");
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate("/login");
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
              <div className="mt-auto pt-4 border-t border-border absolute bottom-6 left-6 right-6">
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-muted-foreground hover:text-foreground"
                >
                  <LogOut className="w-5 h-5" />
                  <span>Déconnexion</span>
                </button>
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </header>

      {/* Main Content */}
      <main className="lg:ml-64 pt-20 lg:pt-8 px-4 lg:px-8 pb-8">
        <div className="max-w-3xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="font-heading text-3xl font-semibold mb-2">
              Hub d'Intégrations
            </h1>
            <p className="text-muted-foreground">
              Connectez vos outils pour synchroniser vos micro-actions et maximiser votre productivité.
            </p>
          </div>

          {loading ? (
            <div className="space-y-4">
              {[1, 2, 3, 4].map((i) => (
                <Card key={i} className="animate-pulse">
                  <CardContent className="p-6">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-xl bg-muted" />
                      <div className="flex-1 space-y-2">
                        <div className="h-4 bg-muted rounded w-1/3" />
                        <div className="h-3 bg-muted rounded w-2/3" />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <div className="space-y-4">
              {Object.entries(SERVICE_META).map(([serviceKey, meta]) => {
                const integration = integrations[serviceKey] || {};
                const Icon = meta.icon;
                const isConnected = integration.connected;
                const isAvailable = integration.available !== false;

                return (
                  <Card key={serviceKey} className={`transition-all ${isConnected ? "border-primary/30" : ""}`}>
                    <CardContent className="p-6">
                      <div className="flex items-start gap-4">
                        {/* Icon */}
                        <div className={`w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 ${meta.color}`}>
                          <Icon className="w-6 h-6" />
                        </div>

                        {/* Info */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-3 mb-1">
                            <h3 className="font-heading text-lg font-semibold">{meta.name}</h3>
                            {isConnected ? (
                              <Badge className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20">
                                <Check className="w-3 h-3 mr-1" />
                                Connecté
                              </Badge>
                            ) : !isAvailable ? (
                              <Badge variant="outline" className="text-muted-foreground">
                                Bientôt disponible
                              </Badge>
                            ) : null}
                          </div>

                          <p className="text-sm text-muted-foreground mb-3">
                            {meta.description}
                          </p>

                          {/* Features */}
                          <div className="flex flex-wrap gap-2 mb-4">
                            {meta.features.map((feature, i) => (
                              <span
                                key={i}
                                className="text-xs px-2 py-1 rounded-full bg-white/5 text-muted-foreground"
                              >
                                {feature}
                              </span>
                            ))}
                          </div>

                          {/* Connected state — account info + controls */}
                          {isConnected && (
                            <div className="flex items-center gap-4 pt-3 border-t border-border">
                              <span className="text-sm text-muted-foreground">
                                {integration.account_name}
                              </span>
                              <div className="flex items-center gap-2 ml-auto">
                                <label className="flex items-center gap-2 text-sm text-muted-foreground">
                                  Sync auto
                                  <Switch
                                    checked={integration.sync_enabled}
                                    onCheckedChange={(checked) => handleToggleSync(serviceKey, checked)}
                                  />
                                </label>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => handleSync(serviceKey)}
                                  disabled={syncing === serviceKey}
                                  className="rounded-lg"
                                >
                                  {syncing === serviceKey ? (
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                  ) : (
                                    <RefreshCw className="w-4 h-4" />
                                  )}
                                  <span className="ml-1 hidden sm:inline">Synchroniser</span>
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleDisconnect(serviceKey)}
                                  disabled={disconnecting === serviceKey}
                                  className="rounded-lg text-destructive hover:text-destructive"
                                >
                                  {disconnecting === serviceKey ? (
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                  ) : (
                                    <Unplug className="w-4 h-4" />
                                  )}
                                  <span className="ml-1 hidden sm:inline">Déconnecter</span>
                                </Button>
                              </div>
                            </div>
                          )}
                        </div>

                        {/* Connect button */}
                        {!isConnected && (
                          <div className="flex-shrink-0">
                            <Button
                              onClick={() => handleConnect(serviceKey)}
                              disabled={connecting === serviceKey || !isAvailable}
                              className="rounded-xl"
                              variant={isAvailable ? "default" : "outline"}
                            >
                              {connecting === serviceKey ? (
                                <Loader2 className="w-4 h-4 animate-spin mr-2" />
                              ) : (
                                <ExternalLink className="w-4 h-4 mr-2" />
                              )}
                              Connecter
                            </Button>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}

          {/* Info card */}
          <Card className="mt-8 border-primary/20 bg-primary/5">
            <CardContent className="p-6">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-primary mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-medium mb-1">Comment ça marche ?</p>
                  <p className="text-sm text-muted-foreground">
                    Connectez vos outils favoris pour synchroniser automatiquement vos sessions InFinea.
                    Chaque fois que vous complétez une micro-action, elle sera automatiquement enregistrée
                    dans vos outils connectés. Vos données restent privées et vous pouvez vous déconnecter à tout moment.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
