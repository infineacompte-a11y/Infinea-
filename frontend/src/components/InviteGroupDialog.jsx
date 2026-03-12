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
import { Loader2, UserPlus, Send, Check } from "lucide-react";
import { toast } from "sonner";
import { API, authFetch } from "@/App";

/**
 * InviteGroupDialog — Invite members to a group by email.
 * Pattern: Strava Club invite + Notion workspace invite.
 *
 * Props:
 *   open — boolean
 *   onOpenChange — function
 *   groupId — string
 *   groupName — string
 */
export default function InviteGroupDialog({ open, onOpenChange, groupId, groupName }) {
  const [email, setEmail] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [sent, setSent] = useState(false);

  const handleInvite = useCallback(async (e) => {
    e.preventDefault();
    const trimmed = email.trim().toLowerCase();
    if (!trimmed || !trimmed.includes("@")) {
      toast.error("Email invalide");
      return;
    }

    setIsSending(true);
    try {
      const res = await authFetch(`${API}/groups/${groupId}/invite`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: trimmed }),
      });
      if (res.status === 404) {
        toast.error("Aucun compte InFinea avec cet email");
        return;
      }
      if (res.status === 409) {
        toast.error("Cette personne est déjà membre ou invitée");
        return;
      }
      if (res.status === 400) {
        const data = await res.json().catch(() => ({}));
        toast.error(data.detail || "Invitation impossible");
        return;
      }
      if (!res.ok) throw new Error();
      setSent(true);
      toast.success(`Invitation envoyée !`);
      setTimeout(() => {
        setSent(false);
        setEmail("");
      }, 2000);
    } catch {
      toast.error("Erreur lors de l'envoi");
    } finally {
      setIsSending(false);
    }
  }, [email, groupId]);

  const handleClose = useCallback((isOpen) => {
    onOpenChange(isOpen);
    if (!isOpen) {
      setEmail("");
      setSent(false);
    }
  }, [onOpenChange]);

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-md bg-card border-border">
        <DialogHeader>
          <DialogTitle className="font-heading flex items-center gap-2">
            <UserPlus className="w-5 h-5 text-primary" />
            Inviter dans {groupName}
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={handleInvite} className="space-y-4 pt-2">
          <div>
            <label className="text-sm text-muted-foreground mb-1.5 block">
              Email du membre à inviter
            </label>
            <Input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="ami@email.com"
              autoFocus
              disabled={isSending}
            />
            <p className="text-muted-foreground text-xs mt-1.5">
              L'invité doit avoir un compte InFinea. Il recevra une notification.
            </p>
          </div>

          <DialogFooter className="pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => handleClose(false)}
              disabled={isSending}
            >
              Fermer
            </Button>
            <Button type="submit" disabled={isSending || !email.trim()} className="gap-2">
              {isSending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : sent ? (
                <Check className="w-4 h-4" />
              ) : (
                <Send className="w-4 h-4" />
              )}
              {sent ? "Envoyé !" : "Inviter"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
