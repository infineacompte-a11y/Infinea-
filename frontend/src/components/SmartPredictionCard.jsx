import React, { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Brain,
  Calendar,
  Clock,
  Play,
  ChevronRight,
  Loader2,
  RefreshCw,
  BookOpen,
  Target,
  Heart,
  Sparkles,
  Plug,
  Zap,
} from "lucide-react";
import { toast } from "sonner";
import { API, authFetch } from "@/App";

const categoryIcons = {
  learning: BookOpen,
  productivity: Target,
  well_being: Heart,
};

const categoryColors = {
  learning: "text-blue-500 bg-blue-500/10",
  productivity: "text-amber-500 bg-amber-500/10",
  well_being: "text-emerald-500 bg-emerald-500/10",
};

const serviceLabels = {
  google_calendar: "Google Calendar",
  ical: "iCal",
  notion: "Notion",
  todoist: "Todoist",
  slack: "Slack",
};

export default function SmartPredictionCard() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    fetchPredictions();
  }, []);

  const formatCountdown = (isoTime) => {
    const now = new Date();
    const target = new Date(isoTime);
    const diff = target - now;

    if (diff <= 0) return t("components.smartPrediction.now");

    const minutes = Math.floor(diff / 60000);
    if (minutes > 60) {
      const hours = Math.floor(minutes / 60);
      const mins = minutes % 60;
      return mins > 0
        ? t("components.smartPrediction.countdownHoursMin", { hours, minutes: mins })
        : t("components.smartPrediction.countdownHours", { hours });
    }
    return t("components.smartPrediction.countdownMinutes", { minutes });
  };

  const fetchPredictions = async () => {
    setIsLoading(true);
    setError(false);
    try {
      const response = await authFetch(`${API}/smart-predict`);
      if (!response.ok) throw new Error("Erreur");
      const result = await response.json();
      setData(result);
    } catch (e) {
      setError(true);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStartAction = async (actionId) => {
    if (!actionId) return;
    try {
      const response = await authFetch(`${API}/sessions/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action_id: actionId }),
      });
      if (!response.ok) throw new Error("Erreur");
      const session = await response.json();
      navigate(`/session/${session.session_id}`, { state: { session } });
    } catch (e) {
      toast.error(t("components.smartPrediction.errorStart"));
    }
  };

  if (error) return null;

  if (isLoading) {
    return (
      <Card className="mb-8 border-indigo-500/20 bg-gradient-to-br from-indigo-500/5 to-purple-500/5">
        <CardContent className="p-5 flex items-center gap-3">
          <Loader2 className="w-5 h-5 animate-spin text-indigo-500" />
          <span className="text-sm text-muted-foreground">{t("components.smartPrediction.analyzing")}</span>
        </CardContent>
      </Card>
    );
  }

  if (!data) return null;

  const { integrations, predictions, next_prediction, proactive, context } = data;
  const hasIntegrations = context?.has_integrations;
  const hasPredictions = predictions && predictions.length > 0;

  // No integrations connected — show CTA
  if (!hasIntegrations) {
    return (
      <Card className="mb-8 border-dashed border-muted-foreground/30" data-testid="smart-predict-empty">
        <CardContent className="p-5">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 rounded-xl bg-muted flex items-center justify-center shrink-0">
              <Plug className="w-5 h-5 text-muted-foreground" />
            </div>
            <div className="flex-1">
              <h3 className="font-heading font-semibold text-sm mb-1">{t("components.smartPrediction.title")}</h3>
              <p className="text-sm text-muted-foreground mb-3">
                {t("components.smartPrediction.connectDescription")}
              </p>
              <Link to="/integrations">
                <Button variant="outline" size="sm" className="rounded-xl">
                  <Calendar className="w-4 h-4 mr-2" />
                  {t("components.smartPrediction.connectCalendar")}
                </Button>
              </Link>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // No predictions but integrations exist — waiting for sync
  if (!hasPredictions) {
    return (
      <Card className="mb-8 border-indigo-500/20 bg-gradient-to-br from-indigo-500/5 to-purple-500/5" data-testid="smart-predict-waiting">
        <CardContent className="p-5">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/10 flex items-center justify-center shrink-0">
              <Brain className="w-5 h-5 text-indigo-500" />
            </div>
            <div className="flex-1">
              <div className="flex items-center justify-between mb-1">
                <h3 className="font-heading font-semibold text-sm">{t("components.smartPrediction.title")}</h3>
                <Button variant="ghost" size="icon" className="h-7 w-7" onClick={fetchPredictions}>
                  <RefreshCw className="w-3.5 h-3.5" />
                </Button>
              </div>
              <p className="text-sm text-muted-foreground">
                {t("components.smartPrediction.noSlotsDetected")}
              </p>
              <div className="flex gap-2 mt-3">
                {integrations.map((integ) => (
                  <Badge key={integ.service} variant="secondary" className="text-xs">
                    <Calendar className="w-3 h-3 mr-1" />
                    {serviceLabels[integ.service] || integ.service}
                  </Badge>
                ))}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Main card: predictions available
  return (
    <Card className="mb-8 border-indigo-500/20 bg-gradient-to-br from-indigo-500/5 to-purple-500/5" data-testid="smart-predict-card">
      <CardContent className="p-5">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/10 flex items-center justify-center">
              <Brain className="w-5 h-5 text-indigo-500" />
            </div>
            <div>
              <h3 className="font-heading font-semibold text-sm">{t("components.smartPrediction.title")}</h3>
              <p className="text-xs text-muted-foreground">
                {t("components.smartPrediction.slotsAvailable", { count: context.total_slots_today, minutes: context.total_free_minutes })}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {integrations.map((integ) => (
              <Badge key={integ.service} variant="secondary" className="text-xs hidden sm:flex">
                <Calendar className="w-3 h-3 mr-1" />
                {serviceLabels[integ.service] || integ.service}
              </Badge>
            ))}
            <Button variant="ghost" size="icon" className="h-7 w-7" onClick={fetchPredictions}>
              <RefreshCw className="w-3.5 h-3.5" />
            </Button>
          </div>
        </div>

        {/* Next prediction (highlighted) */}
        {next_prediction && (
          <div className="p-3 rounded-xl bg-background/60 border border-indigo-500/20 mb-3">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-indigo-500" />
                <span className="text-sm font-medium text-indigo-600 dark:text-indigo-400">
                  {t("components.smartPrediction.nextMoment", { countdown: formatCountdown(next_prediction.start_time) })}
                </span>
              </div>
              <Badge variant="secondary" className="font-mono text-xs">
                {next_prediction.duration_minutes} min
              </Badge>
            </div>
            {next_prediction.suggested_action ? (
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {(() => {
                    const cat = next_prediction.suggested_action.category;
                    const Icon = categoryIcons[cat] || Sparkles;
                    return (
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${categoryColors[cat] || "bg-muted"}`}>
                        <Icon className="w-4 h-4" />
                      </div>
                    );
                  })()}
                  <div>
                    <p className="text-sm font-medium">{next_prediction.suggested_action.title}</p>
                    <p className="text-xs text-muted-foreground">
                      {t(`categories.${next_prediction.suggested_action.category}`, { defaultValue: t("components.smartPrediction.action") })}
                      {next_prediction.suggested_action.score && (
                        <span className="ml-2 text-indigo-500">
                          {t("components.smartPrediction.score", { score: Math.round(next_prediction.suggested_action.score * 100) })}
                        </span>
                      )}
                    </p>
                  </div>
                </div>
                <Button
                  size="sm"
                  className="rounded-xl"
                  onClick={() => handleStartAction(next_prediction.suggested_action.action_id)}
                >
                  <Play className="w-3.5 h-3.5 mr-1" />
                  Go
                </Button>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                {t(`categories.${next_prediction.suggested_category}`, { defaultValue: t("components.smartPrediction.freeSlotDetected") })}
              </p>
            )}
          </div>
        )}

        {/* Additional slots (compact) */}
        {predictions.length > 1 && (
          <div className="space-y-2">
            {predictions.slice(1).map((pred) => {
              const cat = pred.suggested_action?.category || pred.suggested_category;
              const Icon = categoryIcons[cat] || Sparkles;
              return (
                <div
                  key={pred.slot_id}
                  className="flex items-center justify-between p-2 rounded-lg hover:bg-background/40 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-7 h-7 rounded-md flex items-center justify-center ${categoryColors[cat] || "bg-muted"}`}>
                      <Icon className="w-3.5 h-3.5" />
                    </div>
                    <div>
                      <p className="text-sm">
                        <span className="text-muted-foreground">{formatCountdown(pred.start_time)}</span>
                        {pred.suggested_action && (
                          <span className="ml-2 font-medium">{pred.suggested_action.title}</span>
                        )}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="text-xs font-mono">
                      {pred.duration_minutes} min
                    </Badge>
                    {pred.suggested_action && (
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7"
                        onClick={() => handleStartAction(pred.suggested_action.action_id)}
                      >
                        <ChevronRight className="w-4 h-4" />
                      </Button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Proactive insight */}
        {proactive && (
          <div className="mt-3 pt-3 border-t border-border/50 flex items-center gap-2 text-xs text-muted-foreground">
            <Zap className="w-3.5 h-3.5 text-indigo-400" />
            <span>
              {t("components.smartPrediction.rhythm", { duration: proactive.preferred_duration })}
              {", "}
              {t(`dashboard.energy.${proactive.inferred_energy === "high" ? "high" : proactive.inferred_energy === "low" ? "low" : "medium"}`).toLowerCase()}
              {proactive.consistency_index > 0.5 && ` \u2022 ${t("components.smartPrediction.solidConsistency")}`}
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
