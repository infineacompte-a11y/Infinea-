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
  Globe,
  Share2,
  Copy,
  Link2,
  Loader2,
  ExternalLink,
} from "lucide-react";
import { toast } from "sonner";
import { API, authFetch } from "@/App";

const STEPS = [
  {
    title: "Ouvrir iCloud",
    icon: Globe,
    instruction: "Rendez-vous sur icloud.com/calendar depuis votre navigateur et connectez-vous avec votre identifiant Apple.",
    tip: "Utilisez un ordinateur pour cette étape, c'est plus simple.",
    action: {
      label: "Ouvrir iCloud Calendar",
      url: "https://www.icloud.com/calendar/",
    },
  },
  {
    title: "Partager le calendrier",
    icon: Share2,
    instruction: "Cliquez sur l'icône de partage (👤➕) à droite du nom de votre calendrier dans la barre latérale gauche.",
    tip: "Choisissez le calendrier que vous utilisez le plus (souvent « Domicile » ou « Travail »).",
  },
  {
    title: "Activer le calendrier public",
    icon: Copy,
    instruction: "Cochez « Calendrier public » en bas de la fenêtre de partage. Un lien apparaîtra — cliquez dessus pour le copier.",
    tip: "Le lien commence par webcal:// — c'est normal, InFinea le gère automatiquement.",
  },
  {
    title: "Coller l'URL ici",
    icon: Link2,
    instruction: "Collez le lien copié dans le champ ci-dessous. InFinea vérifiera automatiquement que tout fonctionne.",
    isInput: true,
  },
];

export default function AppleCalendarGuide({ open, onOpenChange, onConnected }) {
  const [currentStep, setCurrentStep] = useState(0);
  const [url, setUrl] = useState("");
  const [isConnecting, setIsConnecting] = useState(false);
  const [isValidUrl, setIsValidUrl] = useState(false);

  const handleUrlChange = (value) => {
    setUrl(value);
    const trimmed = value.trim();
    setIsValidUrl(
      trimmed.length > 10 &&
      (trimmed.startsWith("webcal://") ||
        trimmed.startsWith("https://") ||
        trimmed.startsWith("http://")) &&
      (trimmed.includes(".ics") || trimmed.includes("calendar") || trimmed.includes("icloud"))
    );
  };

  const handleConnect = async () => {
    if (!isValidUrl) return;
    setIsConnecting(true);
    try {
      const response = await authFetch(`${API}/integrations/ical/connect`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url.trim(), name: "Apple Calendar" }),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Erreur de connexion");
      }

      const data = await response.json();
      toast.success(`${data.calendar_name || "Apple Calendar"} connecté ! ${data.events_found || 0} événements trouvés.`);
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
            <div className="w-8 h-8 rounded-lg bg-[#E48C75]/40 flex items-center justify-center">
              <Link2 className="w-4 h-4 text-[#E48C75]" />
            </div>
            Connecter Apple Calendar
          </DialogTitle>
          <DialogDescription>
            Suivez ces étapes pour connecter votre calendrier Apple à InFinea.
          </DialogDescription>
        </DialogHeader>

        {/* Progress */}
        <div className="flex items-center gap-1 py-2">
          {STEPS.map((_, i) => (
            <div
              key={i}
              className={`h-1.5 flex-1 rounded-full transition-colors ${
                i < currentStep
                  ? "bg-[#5DB786]"
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
              <h3 className="font-sans font-semibold tracking-tight font-semibold">{step.title}</h3>
            </div>
          </div>

          <Card className="bg-muted/30">
            <CardContent className="p-4 space-y-3">
              <p className="text-sm leading-relaxed">{step.instruction}</p>
              {step.tip && (
                <p className="text-xs text-muted-foreground italic">
                  💡 {step.tip}
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
                    placeholder="webcal://p123-caldav.icloud.com/published/2/..."
                    value={url}
                    onChange={(e) => handleUrlChange(e.target.value)}
                    className="font-mono text-sm"
                    data-testid="ical-guide-url-input"
                  />
                  {url && !isValidUrl && (
                    <p className="text-xs text-[#E48C75]">
                      L'URL doit commencer par webcal://, https:// ou http://
                    </p>
                  )}
                  {isValidUrl && (
                    <p className="text-xs text-[#5DB786] flex items-center gap-1">
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
                data-testid="ical-guide-connect-btn"
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
