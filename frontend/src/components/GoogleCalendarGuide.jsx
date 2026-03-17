import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  CheckCircle2,
  ChevronRight,
  ChevronLeft,
  Settings,
  Share2,
  Link2,
  Loader2,
  ExternalLink,
  Calendar,
} from "lucide-react";
import { toast } from "sonner";
import { API, authFetch } from "@/App";

const STEPS = [
  {
    title: "Ouvrir Google Calendar",
    icon: Calendar,
    instruction: "Rendez-vous sur Google Calendar depuis votre navigateur et connectez-vous avec votre compte Google.",
    tip: "Utilisez un ordinateur pour cette étape, c'est plus simple.",
    action: {
      label: "Ouvrir Google Calendar",
      url: "https://calendar.google.com/calendar/r/settings",
    },
  },
  {
    title: "Accéder aux paramètres du calendrier",
    icon: Settings,
    instruction: "Dans la barre latérale gauche, cliquez sur les trois points (⋮) à droite du calendrier que vous souhaitez connecter, puis sélectionnez « Paramètres et partage ».",
    tip: "Choisissez votre calendrier principal (souvent votre adresse e-mail).",
  },
  {
    title: "Copier l'adresse secrète",
    icon: Share2,
    instruction: "Faites défiler jusqu'à la section « Intégrer le calendrier ». Trouvez « Adresse secrète au format iCal » et cliquez sur l'icône de copie à côté du lien.",
    tip: "Attention : utilisez bien l'adresse « secrète » (pas l'adresse publique). Elle contient vos événements privés.",
  },
  {
    title: "Coller l'URL ici",
    icon: Link2,
    instruction: "Collez le lien copié dans le champ ci-dessous. InFinea vérifiera automatiquement que tout fonctionne.",
    isInput: true,
  },
];

export default function GoogleCalendarGuide({ open, onOpenChange, onConnected }) {
  const [currentStep, setCurrentStep] = useState(0);
  const [url, setUrl] = useState("");
  const [isConnecting, setIsConnecting] = useState(false);
  const [isValidUrl, setIsValidUrl] = useState(false);

  const handleUrlChange = (value) => {
    setUrl(value);
    const trimmed = value.trim();
    setIsValidUrl(
      trimmed.length > 10 &&
      (trimmed.startsWith("https://") || trimmed.startsWith("http://") || trimmed.startsWith("webcal://")) &&
      (trimmed.includes("calendar.google.com") || trimmed.includes("googleapis.com") || trimmed.includes(".ics"))
    );
  };

  const handleConnect = async () => {
    if (!isValidUrl) return;
    setIsConnecting(true);
    try {
      const response = await authFetch(`${API}/integrations/ical/connect`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url.trim(), name: "Google Calendar" }),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Erreur de connexion");
      }

      const data = await response.json();
      toast.success(`${data.calendar_name || "Google Calendar"} connecté ! ${data.events_found || 0} événements trouvés.`);
      onConnected?.();
      handleClose();
    } catch (error) {
      toast.error(error.message || "Impossible de se connecter. Vérifiez l'URL et réessayez.");
    } finally {
      setIsConnecting(false);
    }
  };

  const handleClose = () => {
    setCurrentStep(0);
    setUrl("");
    setIsValidUrl(false);
    onOpenChange(false);
  };

  const step = STEPS[currentStep];
  const StepIcon = step.icon;
  const isLastStep = currentStep === STEPS.length - 1;

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-blue-500/10 flex items-center justify-center">
              <Calendar className="w-4 h-4 text-blue-500" />
            </div>
            Connecter Google Calendar
          </DialogTitle>
          <DialogDescription>
            Suivez ces étapes pour connecter votre calendrier Google à InFinea.
          </DialogDescription>
        </DialogHeader>

        {/* Progress */}
        <div className="flex items-center gap-1 py-2">
          {STEPS.map((_, i) => (
            <div
              key={i}
              className={`h-1.5 flex-1 rounded-full transition-colors ${
                i < currentStep
                  ? "bg-emerald-500"
                  : i === currentStep
                  ? "bg-primary"
                  : "bg-muted"
              }`}
            />
          ))}
        </div>

        {/* Step Content */}
        <div className="py-4 animate-fade-in" key={currentStep}>
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
              <StepIcon className="w-5 h-5 text-primary" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Étape {currentStep + 1}/{STEPS.length}</p>
              <h3 className="font-heading font-semibold">{step.title}</h3>
            </div>
          </div>

          <Card className="bg-muted/30">
            <CardContent className="p-4 space-y-3">
              <p className="text-sm leading-relaxed">{step.instruction}</p>
              {step.tip && (
                <p className="text-xs text-muted-foreground italic">
                  {step.tip}
                </p>
              )}
              {step.action && (
                <Button
                  variant="outline"
                  size="sm"
                  className="gap-2"
                  onClick={() => window.open(step.action.url, "_blank")}
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                  {step.action.label}
                </Button>
              )}
              {step.isInput && (
                <div className="space-y-2 pt-2">
                  <Input
                    type="url"
                    placeholder="https://calendar.google.com/calendar/ical/...basic.ics"
                    value={url}
                    onChange={(e) => handleUrlChange(e.target.value)}
                    className="font-mono text-sm"
                    data-testid="gcal-guide-url-input"
                  />
                  {url && !isValidUrl && (
                    <p className="text-xs text-red-400">
                      L'URL doit provenir de calendar.google.com ou googleapis.com
                    </p>
                  )}
                  {isValidUrl && (
                    <p className="text-xs text-emerald-500 flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" />
                      Format valide
                    </p>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <DialogFooter>
          <div className="flex gap-2 w-full">
            {currentStep > 0 && (
              <Button
                variant="outline"
                onClick={() => setCurrentStep((s) => s - 1)}
                className="gap-1"
              >
                <ChevronLeft className="w-4 h-4" />
                Précédent
              </Button>
            )}
            <div className="flex-1" />
            {isLastStep ? (
              <Button
                onClick={handleConnect}
                disabled={!isValidUrl || isConnecting}
                className="gap-2"
                data-testid="gcal-guide-connect-btn"
              >
                {isConnecting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Connexion...
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="w-4 h-4" />
                    Connecter
                  </>
                )}
              </Button>
            ) : (
              <Button
                onClick={() => setCurrentStep((s) => s + 1)}
                className="gap-1"
              >
                Suivant
                <ChevronRight className="w-4 h-4" />
              </Button>
            )}
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
