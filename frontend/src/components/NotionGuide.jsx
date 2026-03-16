import React, { useState } from "react";
import { useTranslation } from "react-i18next";
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

export default function NotionGuide({ open, onOpenChange, onConnected }) {
  const { t } = useTranslation();
  const [currentStep, setCurrentStep] = useState(0);
  const [token, setToken] = useState("");
  const [isConnecting, setIsConnecting] = useState(false);
  const [isValidToken, setIsValidToken] = useState(false);

  const STEPS = [
    {
      title: t("components.notionGuide.steps.openIntegrations.title"),
      icon: Plus,
      instruction: t("components.notionGuide.steps.openIntegrations.instruction"),
      tip: t("components.notionGuide.steps.openIntegrations.tip"),
      action: {
        label: t("components.notionGuide.steps.openIntegrations.actionLabel"),
        url: "https://www.notion.so/my-integrations",
      },
    },
    {
      title: t("components.notionGuide.steps.createIntegration.title"),
      icon: Settings,
      instruction: t("components.notionGuide.steps.createIntegration.instruction"),
      tip: t("components.notionGuide.steps.createIntegration.tip"),
    },
    {
      title: t("components.notionGuide.steps.copyToken.title"),
      icon: Copy,
      instruction: t("components.notionGuide.steps.copyToken.instruction"),
      tip: t("components.notionGuide.steps.copyToken.tip"),
    },
    {
      title: t("components.notionGuide.steps.pasteToken.title"),
      icon: Link2,
      instruction: t("components.notionGuide.steps.pasteToken.instruction"),
      isInput: true,
    },
  ];

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
        throw new Error(err.detail || t("components.notionGuide.connectionError"));
      }

      toast.success(t("components.notionGuide.connected"));
      onConnected?.();
      handleClose();
    } catch (error) {
      toast.error(error.message || t("components.notionGuide.connectFailed"));
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
            {t("components.notionGuide.title")}
          </DialogTitle>
          <DialogDescription>
            {t("components.notionGuide.description")}
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
              <p className="text-xs text-muted-foreground">{t("common.stepOf", { current: currentStep + 1, total: STEPS.length })}</p>
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
                      {t("components.notionGuide.tokenValidationError")}
                    </p>
                  )}
                  {isValidToken && (
                    <p className="text-xs text-emerald-500 flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" />
                      {t("common.validFormat")}
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
                {t("common.previous")}
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
                    {t("common.connecting")}
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="w-4 h-4" />
                    {t("common.connect")}
                  </>
                )}
              </Button>
            ) : (
              <Button
                onClick={() => setCurrentStep((s) => s + 1)}
                className="gap-1"
              >
                {t("common.next")}
                <ChevronRight className="w-4 h-4" />
              </Button>
            )}
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
