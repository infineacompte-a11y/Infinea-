import React, { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Sparkles,
  Loader2,
  RefreshCw,
  ArrowRight,
  Brain,
  MessageCircle,
} from "lucide-react";
import { API, authFetch } from "@/App";

export default function AICoachCard({ onStartAction }) {
  const [coaching, setCoaching] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    fetchCoaching();
  }, []);

  const fetchCoaching = async () => {
    if (coaching) {
      setIsRefreshing(true);
    } else {
      setIsLoading(true);
    }
    setError(false);
    try {
      const response = await authFetch(`${API}/ai/coach`);
      if (!response.ok) throw new Error("Erreur");
      const data = await response.json();
      setCoaching(data);
    } catch (e) {
      setError(true);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  if (error) return null;

  if (isLoading) {
    return (
      <div className="relative mb-8 rounded-2xl overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-primary/5 to-transparent" />
        <Card className="border-primary/20 bg-transparent backdrop-blur-sm">
          <CardContent className="p-6 flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center animate-pulse">
              <Brain className="w-6 h-6 text-primary/50" />
            </div>
            <div className="space-y-2 flex-1">
              <div className="h-4 w-32 bg-primary/10 rounded-lg animate-pulse" />
              <div className="h-3 w-full bg-primary/5 rounded-lg animate-pulse" />
              <div className="h-3 w-3/4 bg-primary/5 rounded-lg animate-pulse" />
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Backend returns: greeting, suggestion, context_note, suggested_action_id
  const greeting = coaching?.greeting;
  const suggestion = coaching?.suggestion;
  const contextNote = coaching?.context_note;
  const actionId = coaching?.suggested_action_id;

  if (!greeting && !suggestion) return null;

  return (
    <div className="relative mb-8 group" data-testid="ai-coach-card">
      {/* Gradient background glow */}
      <div className="absolute -inset-px rounded-2xl bg-gradient-to-br from-primary/30 via-primary/10 to-transparent opacity-60 group-hover:opacity-100 transition-opacity duration-500" />

      <Card className="relative border-primary/20 bg-card/80 backdrop-blur-sm rounded-2xl overflow-hidden">
        {/* Subtle pattern overlay */}
        <div className="absolute top-0 right-0 w-48 h-48 bg-gradient-to-bl from-primary/5 to-transparent rounded-bl-full" />

        <CardContent className="relative p-6">
          {/* Header row */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center ring-1 ring-primary/10">
                <Brain className="w-5 h-5 text-primary" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-heading font-semibold text-sm">Coach IA</h3>
                  <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full bg-primary/10 text-[10px] font-medium text-primary">
                    <Sparkles className="w-2.5 h-2.5" />
                    Personnalisé
                  </span>
                </div>
                <p className="text-[11px] text-muted-foreground">Adapté à votre profil</p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-muted-foreground hover:text-primary"
              onClick={fetchCoaching}
              disabled={isRefreshing}
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? "animate-spin" : ""}`} />
            </Button>
          </div>

          {/* Greeting — the main coaching message */}
          {greeting && (
            <div className="mb-4">
              <p className="text-[15px] leading-relaxed font-medium text-foreground">
                {greeting}
              </p>
            </div>
          )}

          {/* Suggestion + Context note row */}
          <div className="flex flex-col gap-3">
            {suggestion && (
              <div
                className={`flex items-start gap-3 p-3.5 rounded-xl bg-primary/5 border border-primary/10 ${
                  actionId && onStartAction ? "cursor-pointer hover:bg-primary/10 transition-colors" : ""
                }`}
                onClick={() => actionId && onStartAction?.(actionId)}
              >
                <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center shrink-0 mt-0.5">
                  <Sparkles className="w-4 h-4 text-primary" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-primary mb-0.5">Suggestion pour vous</p>
                  <p className="text-sm leading-relaxed">{suggestion}</p>
                </div>
                {actionId && onStartAction && (
                  <ArrowRight className="w-4 h-4 text-primary shrink-0 mt-1" />
                )}
              </div>
            )}

            {contextNote && (
              <div className="flex items-center gap-2 px-1">
                <MessageCircle className="w-3 h-3 text-muted-foreground shrink-0" />
                <p className="text-xs text-muted-foreground italic leading-relaxed">
                  {contextNote}
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
