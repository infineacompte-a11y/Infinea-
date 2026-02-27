import React, { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Sparkles, Loader2, RefreshCw } from "lucide-react";
import { API, authFetch } from "@/App";

export default function AICoachCard() {
  const [coaching, setCoaching] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    fetchCoaching();
  }, []);

  const fetchCoaching = async () => {
    setIsLoading(true);
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
    }
  };

  if (error) {
    return null; // Silently hide if AI not available
  }

  if (isLoading) {
    return (
      <Card className="mb-8 border-primary/20 bg-primary/5">
        <CardContent className="p-5 flex items-center gap-3">
          <Loader2 className="w-5 h-5 animate-spin text-primary" />
          <span className="text-sm text-muted-foreground">Chargement du coaching IA...</span>
        </CardContent>
      </Card>
    );
  }

  if (!coaching?.message) return null;

  return (
    <Card className="mb-8 border-primary/20 bg-primary/5" data-testid="ai-coach-card">
      <CardContent className="p-5">
        <div className="flex items-start gap-4">
          <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
            <Sparkles className="w-5 h-5 text-primary" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-heading font-semibold text-sm">Coach IA</h3>
              <Button variant="ghost" size="icon" className="h-7 w-7" onClick={fetchCoaching}>
                <RefreshCw className="w-3.5 h-3.5" />
              </Button>
            </div>
            <p className="text-sm leading-relaxed">{coaching.message}</p>
            {coaching.suggested_action && (
              <div className="mt-3 p-3 rounded-lg bg-background/50 border border-border">
                <p className="text-xs text-muted-foreground mb-1">Action suggérée</p>
                <p className="text-sm font-medium">{coaching.suggested_action}</p>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
