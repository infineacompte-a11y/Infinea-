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
  Settings,
  Copy,
  Link2,
  Loader2,
  ExternalLink,
  ListTodo,
} from "lucide-react";
import { toast } from "sonner";
import { API, authFetch } from "@/App";

export default function TodoistGuide({ open, onOpenChange, onConnected }) {
  const { t } = useTranslation();
  const [currentStep, setCurrentStep] = useState(0);
  const [token, setToken] = useState("");
  const [isConnecting, setIsConnecting] = useState(false);
  const [isValidToken, setIsValidToken] = useState(false);

  const STEPS = [
    {
      title: t("components.todoistGuide.steps.openSettings.title"),
      icon: Settings,
      instruction: t("components.todoistGuide.steps.openSettings.instruction"),
      tip: t("components.todoistGuide.steps.openSettings.tip"),
      action: {
        label: t("components.todoistGuide.steps.openSettings.actionLabel"),
        url: "https://app.todoist.com/app/settings/integrations/developer",
      },
    },
    {
      title: t("components.todoistGuide.steps.copyToken.title"),
      icon: Copy,
      instruction: t("components.todoistGuide.steps.copyToken.instruction"),
      tip: t("components.todoistGuide.steps.copyToken.tip"),
    },
    {
      title: t("components.todoistGuide.steps.pasteToken.title"),
      icon: Link2,
      instruction: t("components.todoistGuide.steps.pasteToken.instruction"),
      isInput: true,
    },
  ];

  const handleTokenChange = (value) => {
    setToken(value);
    const trimmed = value.trim();
    setIsValidToken(trimmed.length > 20);
  };

  const handleConnect = async () => {
    if (!isValidToken) return;
    setIsConnecting(true);
    try {
      const response = await authFetch(`${API}/integrations/token/connect`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ service: "todoist", token: token.trim() }),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || t("components.todoistGuide.connectionError"));
      }

      toast.success(t("components.todoistGuide.connected"));
      onConnected?.();
      handleClose();
    } catch (error) {
      toast.error(error.message || t("components.todoistGuide.connectFailed"));
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
            <div className="w-8 h-8 rounded-lg bg-red-500/10 flex items-center justify-center">
              <ListTodo className="w-4 h-4 text-red-500" />
            </div>
            {t("components.todoistGuide.title")}
          </DialogTitle>
          <DialogDescription>
            {t("components.todoistGuide.description")}
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
                    placeholder={t("components.todoistGuide.tokenPlaceholder")}
                    value={token}
                    onChange={(e) => handleTokenChange(e.target.value)}
                    className="font-mono text-sm"
                    data-testid="todoist-guide-token-input"
                  />
                  {token && !isValidToken && (
                    <p className="text-xs text-red-400">
                      {t("components.todoistGuide.tokenTooShort")}
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
                data-testid="todoist-guide-connect-btn"
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
