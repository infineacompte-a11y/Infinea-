import React, { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Sparkles, Loader2, ChevronRight } from "lucide-react";
import { API, authFetch } from "@/App";

export default function SessionDebrief({ sessionId, duration, notes, onContinue }) {
  const [debrief, setDebrief] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchDebrief();
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
      // Silently fail — debrief is optional
      setDebrief(null);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <Card className="mt-6 border-primary/20 bg-primary/5">
        <CardContent className="p-5 flex items-center gap-3 justify-center">
          <Loader2 className="w-5 h-5 animate-spin text-primary" />
          <span className="text-sm text-muted-foreground">Analyse IA en cours...</span>
        </CardContent>
      </Card>
    );
  }

  if (!debrief?.feedback) return null;

  return (
    <Card className="mt-6 border-primary/20 bg-primary/5 animate-fade-in" data-testid="session-debrief">
      <CardContent className="p-5">
        <div className="flex items-start gap-3 mb-4">
          <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
            <Sparkles className="w-4 h-4 text-primary" />
          </div>
          <div>
            <h3 className="font-heading font-semibold text-sm mb-1">Debrief IA</h3>
            <p className="text-sm leading-relaxed">{debrief.feedback}</p>
          </div>
        </div>

        {debrief.next_suggestion && (
          <Button
            variant="outline"
            size="sm"
            className="w-full mt-2"
            onClick={onContinue}
          >
            {debrief.next_suggestion}
            <ChevronRight className="w-4 h-4 ml-1" />
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
