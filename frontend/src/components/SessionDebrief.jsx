import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Sparkles,
  Loader2,
  ArrowRight,
  Brain,
  Heart,
  MessageCircle,
} from "lucide-react";
import { API, authFetch } from "@/App";

export default function SessionDebrief({ sessionId, duration, notes, onStartAction, onContinue }) {
  const { t } = useTranslation();
  const [debrief, setDebrief] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchDebrief();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchDebrief = async () => {
    try {
      const response = await authFetch(`${API}/ai/debrief`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          duration_minutes: duration,
          notes: notes || "",
        }),
      });

      if (!response.ok) throw new Error("Erreur");
      const data = await response.json();
      setDebrief(data);
    } catch (e) {
      setDebrief(null);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="relative mt-8">
        <div className="absolute -inset-px rounded-2xl bg-gradient-to-br from-primary/20 via-primary/5 to-transparent opacity-60" />
        <Card className="relative border-primary/20 bg-card/80 backdrop-blur-sm rounded-2xl">
          <CardContent className="p-5 flex items-center gap-3 justify-center">
            <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center animate-pulse">
              <Brain className="w-5 h-5 text-primary/50" />
            </div>
            <div className="space-y-2 flex-1">
              <div className="h-3 w-24 bg-primary/10 rounded-lg animate-pulse" />
              <div className="h-3 w-full bg-primary/5 rounded-lg animate-pulse" />
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!debrief?.feedback) return null;

  const nextActionId = debrief.next_action_id;
  const nextActionTitle = debrief.next_action_title;

  return (
    <div className="relative mt-8 group" data-testid="session-debrief">
      {/* Gradient glow */}
      <div className="absolute -inset-px rounded-2xl bg-gradient-to-br from-primary/30 via-primary/10 to-transparent opacity-60 group-hover:opacity-100 transition-opacity duration-500" />

      <Card className="relative border-primary/20 bg-card/80 backdrop-blur-sm rounded-2xl overflow-hidden">
        {/* Subtle pattern */}
        <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-bl from-primary/5 to-transparent rounded-bl-full" />

        <CardContent className="relative p-5">
          {/* Header */}
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center ring-1 ring-primary/10">
              <Brain className="w-5 h-5 text-primary" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-heading font-semibold text-sm">{t("components.sessionDebrief.title")}</h3>
                <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full bg-primary/10 text-[10px] font-medium text-primary">
                  <Sparkles className="w-2.5 h-2.5" />
                  {t("components.sessionDebrief.analysisBadge")}
                </span>
              </div>
            </div>
          </div>

          {/* Feedback */}
          <p className="text-[15px] leading-relaxed font-medium text-foreground mb-3">
            {debrief.feedback}
          </p>

          {/* Encouragement */}
          {debrief.encouragement && (
            <div className="flex items-center gap-2 mb-4 px-1">
              <Heart className="w-3 h-3 text-rose-400 shrink-0" />
              <p className="text-xs text-muted-foreground italic">{debrief.encouragement}</p>
            </div>
          )}

          {/* Next action CTA */}
          {debrief.next_suggestion && (
            <div className="p-3.5 rounded-xl bg-primary/5 border border-primary/10">
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center shrink-0 mt-0.5">
                  <Sparkles className="w-4 h-4 text-primary" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-primary mb-0.5">{t("components.sessionDebrief.nextAction")}</p>
                  <p className="text-sm leading-relaxed">{debrief.next_suggestion}</p>
                </div>
              </div>
              {nextActionId && onStartAction && (
                <Button
                  size="sm"
                  className="mt-3 w-full gap-2"
                  onClick={() => onStartAction(nextActionId)}
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  {t("components.sessionDebrief.startAction")}
                  <ArrowRight className="w-3.5 h-3.5" />
                </Button>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
