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
} from "lucide-react";
import { toast } from "sonner";
import { API, useAuth } from "@/App";
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
    status: "available", // available, coming_soon, premium
  },
  {
    id: "notion",
    provider: "notion",
    name: "Notion",
    description: "Synchronisez vos tâches et notes pour des suggestions contextuelles",
    icon: FileText,
    color: "gray",
    category: "notes",
    status: "coming_soon",
  },
  {
    id: "todoist",
    provider: "todoist",
    name: "Todoist",
    description: "Connectez vos tâches pour prioriser vos micro-actions",
    icon: ListTodo,
    color: "red",
    category: "tâches",
    status: "coming_soon",
  },
  {
    id: "slack",
    provider: "slack",
    name: "Slack",
    description: "Recevez des rappels de micro-actions directement dans Slack",
    icon: MessageSquare,
    color: "purple",
    category: "communication",
    status: "coming_soon",
  },
];

const colorClasses = {
  blue: { bg: "bg-blue-500/10", text: "text-blue-500", border: "border-blue-500/30" },
  gray: { bg: "bg-zinc-500/10", text: "text-zinc-400", border: "border-zinc-500/30" },
  red: { bg: "bg-red-500/10", text: "text-red-500", border: "border-red-500/30" },
  purple: { bg: "bg-purple-500/10", text: "text-purple-500", border: "border-purple-500/30" },
  green: { bg: "bg-emerald-500/10", text: "text-emerald-500", border: "border-emerald-500/30" },
};

export default function IntegrationsPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [integrations, setIntegrations] = useState({ integrations: [], available: [] });
  const [slotSettings, setSlotSettings] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSyncing, setIsSyncing] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [selectedIntegration, setSelectedIntegration] = useState(null);

  useEffect(() => {
    // Check for OAuth callback results
    const success = searchParams.get("success");
    const error = searchParams.get("error");

    if (success) {
      toast.success("Google Calendar connecté avec succès!");
      navigate("/integrations", { replace: true });
    } else if (error) {
      const errorMessages = {
        oauth_error: "Erreur lors de l'authentification Google",
        missing_params: "Paramètres manquants",
        invalid_state: "Session expirée, veuillez réessayer",
        connection_failed: "Échec de la connexion",
      };
      toast.error(errorMessages[error] || "Une erreur est survenue");
      navigate("/integrations", { replace: true });
    }

    fetchData();
  }, [searchParams, navigate]);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem("infinea_token");
      const headers = { Authorization: `Bearer ${token}` };

      const [intRes, settingsRes] = await Promise.all([
        fetch(`${API}/integrations`, { credentials: "include", headers }),
        fetch(`${API}/slots/settings`, { credentials: "include", headers }),
      ]);

      if (intRes.ok) setIntegrations(await intRes.json());
      if (settingsRes.ok) setSlotSettings(await settingsRes.json());
    } catch (error) {
      toast.error("Erreur de chargement");
    } finally {
      setIsLoading(false);
    }
  };

  const handleConnect = async (provider) => {
    try {
      const response = await fetch(`${API}/integrations/${provider}/connect`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("infinea_token")}`,
        },
        credentials: "include",
        body: JSON.stringify({ origin_url: window.location.origin }),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Erreur");
      }

      const data = await response.json();
      window.location.href = data.authorization_url;
    } catch (error) {
      toast.error(error.message);
    }
  };

  const handleDisconnect = async (integrationId) => {
    try {
      const response = await fetch(`${API}/integrations/${integrationId}`, {
        method: "DELETE",
        credentials: "include",
        headers: { Authorization: `Bearer ${localStorage.getItem("infinea_token")}` },
      });

      if (!response.ok) throw new Error("Erreur");

      toast.success("Intégration déconnectée");
      setSelectedIntegration(null);
      fetchData();
    } catch (error) {
      toast.error("Erreur lors de la déconnexion");
    }
  };

  const handleSync = async (integrationId) => {
    setIsSyncing(true);
    try {
      const response = await fetch(`${API}/integrations/${integrationId}/sync`, {
        method: "POST",
        credentials: "include",
        headers: { Authorization: `Bearer ${localStorage.getItem("infinea_token")}` },
      });

      if (!response.ok) throw new Error("Erreur");

      const data = await response.json();
      toast.success(`Synchronisation terminée: ${data.slots_detected} créneaux détectés`);
      fetchData();
    } catch (error) {
      toast.error("Erreur lors de la synchronisation");
    } finally {
      setIsSyncing(false);
    }
  };

  const handleUpdateSettings = async (newSettings) => {
    try {
      const response = await fetch(`${API}/slots/settings`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("infinea_token")}`,
        },
        credentials: "include",
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

  const getConnectedIntegration = (provider) => {
    return integrations.integrations.find((i) => i.provider === provider);
  };

  const isIntegrationAvailable = (provider) => {
    const available = integrations.available?.find((a) => a.provider === provider);
    return available?.available !== false;
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
              {/* Connected Integrations */}
              {integrations.integrations.length > 0 && (
                <div>
                  <h2 className="text-sm font-medium text-muted-foreground mb-4 flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                    Connectés ({integrations.integrations.length})
                  </h2>
                  <div className="grid gap-4">
                    {integrations.integrations.map((int) => {
                      const config = AVAILABLE_INTEGRATIONS.find((a) => a.provider === int.provider);
                      if (!config) return null;
                      const Icon = config.icon;
                      const colors = colorClasses[config.color];

                      return (
                        <Card key={int.integration_id} className={`${colors.border} border`}>
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
                                    Dernière sync: {int.last_sync_at ? new Date(int.last_sync_at).toLocaleString("fr-FR") : "Jamais"}
                                  </p>
                                </div>
                              </div>
                              <div className="flex gap-2">
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => handleSync(int.integration_id)}
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
                                  onClick={() => setSelectedIntegration(int)}
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
              )}

              {/* Available Integrations by Category */}
              {Object.entries(groupedIntegrations).map(([category, ints]) => {
                // Filter out already connected integrations
                const availableInts = ints.filter(
                  (int) => !integrations.integrations.some((c) => c.provider === int.provider)
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
                              int.status === "coming_soon" ? "opacity-60" : "hover:border-primary/50"
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
                                  {int.status === "available" ? (
                                    isAvailable ? (
                                      <Button
                                        size="sm"
                                        onClick={() => handleConnect(int.provider)}
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
              })}

              {/* Slot Detection Settings */}
              {slotSettings && integrations.integrations.some((i) => i.provider === "google_calendar") && (
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
              {selectedIntegration?.provider === "google_calendar" && "Google Calendar"}
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            {selectedIntegration && (
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 rounded-xl bg-white/5">
                  <div>
                    <p className="text-sm text-muted-foreground">Dernière synchronisation</p>
                    <p className="font-medium">
                      {selectedIntegration.last_sync_at
                        ? new Date(selectedIntegration.last_sync_at).toLocaleString("fr-FR")
                        : "Jamais"}
                    </p>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleSync(selectedIntegration.integration_id)}
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
              onClick={() => handleDisconnect(selectedIntegration?.integration_id)}
            >
              <Unplug className="w-4 h-4 mr-2" />
              Déconnecter
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
