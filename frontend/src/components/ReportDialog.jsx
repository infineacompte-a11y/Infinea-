import React, { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Loader2, Flag } from "lucide-react";
import { toast } from "sonner";
import { API, authFetch } from "@/App";

const REASONS = [
  { value: "harassment", label: "Harcèlement" },
  { value: "spam", label: "Spam" },
  { value: "hate_speech", label: "Discours haineux" },
  { value: "inappropriate_content", label: "Contenu inapproprié" },
  { value: "impersonation", label: "Usurpation d'identité" },
  { value: "self_harm", label: "Automutilation / Mise en danger" },
  { value: "other", label: "Autre" },
];

/**
 * ReportDialog — Signaler un contenu (user, comment, activity, group).
 *
 * Props:
 *   open: boolean
 *   onOpenChange: (open) => void
 *   targetType: "user" | "comment" | "activity" | "group" | "message"
 *   targetId: string
 */
export default function ReportDialog({ open, onOpenChange, targetType, targetId }) {
  const [reason, setReason] = useState("");
  const [details, setDetails] = useState("");
  const [sending, setSending] = useState(false);

  const handleSubmit = async () => {
    if (!reason) {
      toast.error("Veuillez sélectionner une raison");
      return;
    }
    setSending(true);
    try {
      const res = await authFetch(`${API}/report`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target_type: targetType,
          target_id: targetId,
          reason,
          details: details.trim(),
        }),
      });
      if (res.ok) {
        toast.success("Signalement enregistré. Merci.");
        onOpenChange(false);
        setReason("");
        setDetails("");
      } else {
        const data = await res.json().catch(() => ({}));
        toast.error(data.detail || "Erreur lors du signalement");
      }
    } catch {
      toast.error("Erreur de connexion");
    } finally {
      setSending(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="font-sans font-semibold tracking-tight flex items-center gap-2">
            <Flag className="w-5 h-5 text-destructive" />
            Signaler
          </DialogTitle>
        </DialogHeader>
        <div className="space-y-4 pt-2">
          <p className="text-sm text-muted-foreground">
            Pourquoi signalez-vous ce contenu ?
          </p>
          <div className="grid gap-2">
            {REASONS.map((r) => (
              <button
                key={r.value}
                onClick={() => setReason(r.value)}
                className={`text-left px-3 py-2.5 rounded-xl text-sm transition-all ${
                  reason === r.value
                    ? "bg-destructive/10 text-destructive font-medium ring-1 ring-destructive/20"
                    : "bg-muted/30 text-foreground hover:bg-muted/60"
                }`}
              >
                {r.label}
              </button>
            ))}
          </div>
          <Textarea
            value={details}
            onChange={(e) => setDetails(e.target.value)}
            placeholder="Détails supplémentaires (optionnel)..."
            maxLength={500}
            rows={2}
            className="resize-none"
          />
          <div className="flex gap-3">
            <Button
              variant="outline"
              className="flex-1 rounded-xl"
              onClick={() => onOpenChange(false)}
            >
              Annuler
            </Button>
            <Button
              variant="destructive"
              className="flex-1 rounded-xl"
              onClick={handleSubmit}
              disabled={sending || !reason}
            >
              {sending ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
              Envoyer
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
