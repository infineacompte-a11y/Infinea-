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
  Plus,
  Settings,
  Copy,
  Link2,
  Loader2,
  ExternalLink,
  FileText,
} from "lucide-react";
import { toast } from "sonner";
import { API, authFetch } from "@/App";

const STEPS = [
  {
    title: "Ouvrir Notion Integrations",
    icon: Plus,
    instruction: "Rendez-vous sur la page des intégrations Notion et connectez-vous avec votre compte.",
    tip: "Vous allez créer une intégration interne — c'est rapide et gratuit.",
    action: {
      label: "Ouvrir Notion Integrations",
      url: "https://www.notion.so/my-integrations",
    },
  },
  {
    title: "Créer une intégration",
    icon: Settings,
    instruction: "Cliquez sur « + Nouvelle intégration ». Donnez-lui un nom (ex: « InFinea »), sélectionnez votre espace de travail, puis cliquez sur « Envoyer ».",
    tip: "Les capacités par défaut (lecture) suffisent. Pas besoin de modifier les permissions.",
  },
  {
    title: "Copier le token secret",
    icon: Copy,
    instruction: "Sur la page de votre intégration, dans la section « Secrets d'intégration interne », cliquez sur « Afficher » puis « Copier » pour copier le token.",
    tip: "Le token commence par « secret_ » — gardez-le confidentiel.",
  },
  {
    title: "Coller le token ici",
    icon: Link2,
    instruction: "Collez le token copié dans le champ ci-dessous. InFinea vérifiera automatiquement la connexion.",
    isInput: true,
  },
];

export default function NotionGuide({ open, onOpenChange, onConnected }) {
  const [currentStep, setCurrentStep] = useState(0);
  const [token, setToken] = useState("");
  const [isConnecting, setIsConnecting] = useState(false);
  const [isValidToken, setIsValidToken] = useState(false);

  const handleTokenChange = (value) => {
    setToken(value);
    const trimmed = value.trim();
    setIsValidToken(
      trimmed.length > 20 &&
      (trimmed.startsWith("secret_") || trimmed.startsWith("ntn_"))
    );
  };

  const handleConnect = async () => {
    if (!isValidToken) return;
    setIsConnecting(true);
    try {
      const response = await authFetch(`${API}/integrations/token/connect`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ service: "notion", token: token.trim() }),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Erreur de connexion");
      }

      toast.success("Notion connecté avec succès !");
      onConnected?.();
      handleClose();
    } catch (error) {
      toast.error(error.message || "Impossible de se connecter. Vérifiez le token et réessayez.");
    } finally {
      setIsConnecting(false);
    }
  };

  const handleClose = () => {
    setCurrentStep(0);
    setToken("");
    setIsValidToken(false);
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
            <div className="w-8 h-8 rounded-lg bg-zinc-500/10 flex items-center justify-center">
              <FileText className="w-4 h-4 text-zinc-400" />
            </div>
            Connecter Notion
          </DialogTitle>
          <DialogDescription>
            Suivez ces étapes pour connecter votre espace Notion à InFinea.
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
                    type="password"
                    placeholder="secret_abc123..."
                    value={token}
                    onChange={(e) => handleTokenChange(e.target.value)}
                    className="font-mono text-sm"
                    data-testid="notion-guide-token-input"
                  />
                  {token && !isValidToken && (
                    <p className="text-xs text-red-400">
                      Le token doit commencer par « secret_ » ou « ntn_ »
                    </p>
                  )}
                  {isValidToken && (
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
                disabled={!isValidToken || isConnecting}
                className="gap-2"
                data-testid="notion-guide-connect-btn"
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
