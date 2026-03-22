import React, { useState, useCallback } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Loader2, Users } from "lucide-react";
import { toast } from "sonner";
import { API, authFetch } from "@/App";

/**
 * CreateGroupDialog — Modal to create a new duo/group.
 * Pattern: Strava Club creation + Duolingo Friends Quest invite.
 *
 * Props:
 *   open — boolean
 *   onOpenChange — function
 *   onCreated — callback(group) after successful creation
 */
export default function CreateGroupDialog({ open, onOpenChange, onCreated }) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = useCallback(async (e) => {
    e.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) {
      toast.error("Le nom du groupe est requis");
      return;
    }
    if (trimmed.length > 50) {
      toast.error("50 caractères maximum pour le nom");
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await authFetch(`${API}/groups`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: trimmed,
          ...(description.trim() && { description: description.trim() }),
        }),
      });
      if (res.status === 409) {
        toast.error("Tu as déjà 5 groupes actifs (maximum)");
        return;
      }
      if (!res.ok) throw new Error("Erreur serveur");
      const group = await res.json();
      toast.success("Groupe créé !");
      onCreated?.(group);
      onOpenChange(false);
      setName("");
      setDescription("");
    } catch {
      toast.error("Impossible de créer le groupe");
    } finally {
      setIsSubmitting(false);
    }
  }, [name, description, onCreated, onOpenChange]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md bg-card border-border">
        <DialogHeader>
          <DialogTitle className="font-sans font-semibold tracking-tight flex items-center gap-2">
            <Users className="w-5 h-5 text-primary" />
            Créer un groupe
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4 pt-2">
          <div>
            <label className="text-sm text-muted-foreground mb-1.5 block">
              Nom du groupe
            </label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Ex: Duo du matin, Équipe dev..."
              maxLength={50}
              autoFocus
            />
          </div>

          <div>
            <label className="text-sm text-muted-foreground mb-1.5 block">
              Description <span className="text-muted-foreground/50">(optionnel)</span>
            </label>
            <Input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Objectif du groupe..."
              maxLength={200}
            />
          </div>

          <DialogFooter className="pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isSubmitting}
            >
              Annuler
            </Button>
            <Button type="submit" disabled={isSubmitting || !name.trim()} className="gap-2">
              {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
              Créer
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
