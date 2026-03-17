import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Clock,
  Play,
  X,
  BookOpen,
  Target,
  Heart,
  Sparkles,
  ChevronRight,
} from "lucide-react";
import { toast } from "sonner";
import { API } from "@/App";

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

const categoryLabels = {
  learning: "Apprentissage",
  productivity: "Productivité",
  well_being: "Bien-être",
};

export default function SlotCard({ slot, onDismiss, onRefresh }) {
  const navigate = useNavigate();
  const [countdown, setCountdown] = useState("");
  const [isDismissing, setIsDismissing] = useState(false);

  useEffect(() => {
    if (!slot) return;

    const updateCountdown = () => {
      const now = new Date();
      const slotStart = new Date(slot.start_time);
      const diff = slotStart - now;

      if (diff <= 0) {
        setCountdown("Maintenant!");
        return;
      }

      const minutes = Math.floor(diff / 60000);
      const seconds = Math.floor((diff % 60000) / 1000);

      if (minutes > 60) {
        const hours = Math.floor(minutes / 60);
        setCountdown(`dans ${hours}h ${minutes % 60}min`);
      } else if (minutes > 0) {
        setCountdown(`dans ${minutes}min ${seconds}s`);
      } else {
        setCountdown(`dans ${seconds}s`);
      }
    };

    updateCountdown();
    const interval = setInterval(updateCountdown, 1000);

    return () => clearInterval(interval);
  }, [slot]);

  const handleStart = async () => {
    if (!slot?.suggested_action?.action_id) {
      navigate("/actions");
      return;
    }

    try {
      const response = await fetch(`${API}/sessions/start`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("infinea_token")}`,
        },
        credentials: "include",
        body: JSON.stringify({ action_id: slot.suggested_action.action_id }),
      });

      if (!response.ok) throw new Error("Erreur");

      const data = await response.json();
      navigate(`/session/${data.session_id}`, { state: { session: data } });
    } catch (error) {
      toast.error("Erreur lors du démarrage");
    }
  };

  const handleDismiss = async () => {
    if (!slot) return;

    setIsDismissing(true);
    try {
      const response = await fetch(`${API}/slots/${slot.slot_id}/dismiss`, {
        method: "POST",
        credentials: "include",
        headers: { Authorization: `Bearer ${localStorage.getItem("infinea_token")}` },
      });

      if (!response.ok) throw new Error("Erreur");

      toast.success("Créneau ignoré");
      if (onDismiss) onDismiss();
      if (onRefresh) onRefresh();
    } catch (error) {
      toast.error("Erreur");
    } finally {
      setIsDismissing(false);
    }
  };

  if (!slot) return null;

  const action = slot.suggested_action;
  const category = action?.category || slot.suggested_category;
  const Icon = categoryIcons[category] || Sparkles;

  return (
    <Card className="bg-gradient-to-br from-primary/10 to-purple-500/10 border-primary/30 animate-fade-in" data-testid="slot-card">
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-primary" />
            <span className="text-sm font-medium text-primary">{countdown}</span>
          </div>
          <Badge variant="secondary" className="font-mono">
            {slot.duration_minutes} min
          </Badge>
        </div>

        {action ? (
          <div className="flex items-start gap-3 mb-4">
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${categoryColors[category]}`}>
              <Icon className="w-5 h-5" />
            </div>
            <div className="flex-1">
              <h4 className="font-medium mb-1">{action.title}</h4>
              <p className="text-sm text-muted-foreground line-clamp-1">
                {action.description}
              </p>
            </div>
          </div>
        ) : (
          <div className="mb-4">
            <p className="text-sm text-muted-foreground">
              Créneau libre détecté • Catégorie suggérée: {categoryLabels[category] || category}
            </p>
          </div>
        )}

        <div className="flex gap-2">
          <Button
            onClick={handleStart}
            className="flex-1 rounded-xl"
            data-testid="start-slot-btn"
          >
            <Play className="w-4 h-4 mr-2" />
            Commencer
          </Button>
          <Button
            variant="outline"
            size="icon"
            onClick={handleDismiss}
            disabled={isDismissing}
            className="rounded-xl"
            data-testid="dismiss-slot-btn"
          >
            <X className="w-4 h-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
