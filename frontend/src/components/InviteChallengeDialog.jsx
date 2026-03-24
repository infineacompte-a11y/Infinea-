import React, { useState, useEffect, useCallback, useRef } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  UserPlus,
  Search,
  Loader2,
  Send,
  Check,
  X,
} from "lucide-react";
import { toast } from "sonner";
import { API, authFetch, useAuth } from "@/App";

/**
 * InviteChallengeDialog — Friend picker to invite users to a challenge.
 * Pattern: Strava challenge invite (followers list + search + multi-select).
 *
 * Props:
 *   open — boolean
 *   onOpenChange — function
 *   challengeId — string
 *   challengeTitle — string
 *   existingParticipantIds — string[] (user_ids already in challenge)
 *   onInvited — () => void (callback after invites sent)
 */
export default function InviteChallengeDialog({
  open,
  onOpenChange,
  challengeId,
  challengeTitle,
  existingParticipantIds = [],
  onInvited,
}) {
  const { user } = useAuth();
  const [following, setFollowing] = useState([]);
  const [searchResults, setSearchResults] = useState(null);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState([]);
  const [loadingList, setLoadingList] = useState(false);
  const [searching, setSearching] = useState(false);
  const [sending, setSending] = useState(false);
  const debounceRef = useRef(null);

  // Fetch user's following list on open
  useEffect(() => {
    if (!open || !user?.user_id) return;
    setLoadingList(true);
    setSelected([]);
    setQuery("");
    setSearchResults(null);

    authFetch(`${API}/users/${user.user_id}/following`)
      .then(async (res) => {
        if (res.ok) {
          const data = await res.json();
          setFollowing(data.users || data.following || []);
        }
      })
      .catch(() => {})
      .finally(() => setLoadingList(false));
  }, [open, user?.user_id]);

  // Debounced search
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (!query.trim() || query.trim().length < 2) {
      setSearchResults(null);
      setSearching(false);
      return;
    }
    setSearching(true);
    debounceRef.current = setTimeout(async () => {
      try {
        const res = await authFetch(
          `${API}/users/search?q=${encodeURIComponent(query.trim())}&limit=20`
        );
        if (res.ok) {
          const data = await res.json();
          setSearchResults(data.users || []);
        }
      } catch {
        /* silent */
      } finally {
        setSearching(false);
      }
    }, 300);
    return () => clearTimeout(debounceRef.current);
  }, [query]);

  const toggleUser = useCallback((u) => {
    setSelected((prev) => {
      const exists = prev.find((s) => s.user_id === u.user_id);
      if (exists) return prev.filter((s) => s.user_id !== u.user_id);
      return [...prev, u];
    });
  }, []);

  const removeSelected = useCallback((userId) => {
    setSelected((prev) => prev.filter((s) => s.user_id !== userId));
  }, []);

  const handleSend = async () => {
    if (selected.length === 0) return;
    setSending(true);
    try {
      const res = await authFetch(`${API}/challenges/${challengeId}/invite`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_ids: selected.map((s) => s.user_id) }),
      });
      if (res.ok) {
        const data = await res.json();
        toast.success(`${data.sent || selected.length} invitation${(data.sent || selected.length) > 1 ? "s" : ""} envoyée${(data.sent || selected.length) > 1 ? "s" : ""}`);
        setSelected([]);
        onInvited?.();
        onOpenChange(false);
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || "Erreur lors de l'envoi");
      }
    } catch {
      toast.error("Erreur de connexion");
    } finally {
      setSending(false);
    }
  };

  const handleClose = (isOpen) => {
    onOpenChange(isOpen);
    if (!isOpen) {
      setSelected([]);
      setQuery("");
      setSearchResults(null);
    }
  };

  function getInitials(name) {
    if (!name) return "U";
    return name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2);
  }

  // Build display list: search results if searching, otherwise following
  const existingSet = new Set(existingParticipantIds);
  const displayList = (searchResults || following).filter(
    (u) => u.user_id !== user?.user_id && !existingSet.has(u.user_id)
  );
  const selectedSet = new Set(selected.map((s) => s.user_id));

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-md bg-card border-border">
        <DialogHeader>
          <DialogTitle className="font-sans font-semibold tracking-tight flex items-center gap-2">
            <UserPlus className="w-5 h-5 text-primary" />
            Inviter au défi
          </DialogTitle>
          <p className="text-xs text-muted-foreground mt-0.5">
            {challengeTitle}
          </p>
        </DialogHeader>

        <div className="space-y-3 pt-1">
          {/* Selected chips */}
          {selected.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {selected.map((u) => (
                <span
                  key={u.user_id}
                  className="inline-flex items-center gap-1 pl-1 pr-1.5 py-0.5 rounded-full bg-primary/10 text-primary text-xs"
                >
                  <Avatar className="w-4 h-4">
                    <AvatarImage src={u.picture || u.avatar_url} />
                    <AvatarFallback className="text-[7px] bg-primary/20">
                      {getInitials(u.display_name || u.name)}
                    </AvatarFallback>
                  </Avatar>
                  <span className="max-w-[80px] truncate">
                    {u.display_name || u.name}
                  </span>
                  <button
                    onClick={() => removeSelected(u.user_id)}
                    className="ml-0.5 hover:text-foreground transition-colors"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
            </div>
          )}

          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Rechercher un utilisateur..."
              className="pl-9"
              autoFocus
            />
            {searching && (
              <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground animate-spin" />
            )}
          </div>

          {/* User list */}
          <div className="max-h-[280px] overflow-y-auto -mx-1 px-1 space-y-1">
            {loadingList ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-5 h-5 text-primary animate-spin" />
              </div>
            ) : displayList.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-6 text-center">
                <p className="text-sm text-muted-foreground">
                  {query.trim().length >= 2
                    ? "Aucun utilisateur trouvé"
                    : "Suivez des utilisateurs pour les inviter ici"}
                </p>
              </div>
            ) : (
              <>
                {!searchResults && (
                  <p className="text-[11px] text-muted-foreground font-medium uppercase tracking-wider mb-1">
                    Personnes que tu suis
                  </p>
                )}
                {searchResults && (
                  <p className="text-[11px] text-muted-foreground font-medium uppercase tracking-wider mb-1">
                    Résultats
                  </p>
                )}
                {displayList.map((u) => {
                  const isSelected = selectedSet.has(u.user_id);
                  return (
                    <button
                      key={u.user_id}
                      onClick={() => toggleUser(u)}
                      className={`w-full flex items-center gap-3 p-2 rounded-lg transition-all duration-150 text-left ${
                        isSelected
                          ? "bg-primary/8 ring-1 ring-primary/20"
                          : "hover:bg-muted/50"
                      }`}
                    >
                      <Avatar className="w-9 h-9 shrink-0">
                        <AvatarImage src={u.picture || u.avatar_url} />
                        <AvatarFallback className="text-[11px] bg-primary/10">
                          {getInitials(u.display_name || u.name)}
                        </AvatarFallback>
                      </Avatar>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">
                          {u.display_name || u.name}
                        </p>
                        {u.username && (
                          <p className="text-[11px] text-muted-foreground truncate">
                            @{u.username}
                          </p>
                        )}
                      </div>
                      <div
                        className={`w-5 h-5 rounded-full border-2 flex items-center justify-center shrink-0 transition-all duration-150 ${
                          isSelected
                            ? "bg-primary border-primary"
                            : "border-border"
                        }`}
                      >
                        {isSelected && <Check className="w-3 h-3 text-white" />}
                      </div>
                    </button>
                  );
                })}
              </>
            )}
          </div>
        </div>

        <DialogFooter className="pt-2">
          <Button
            type="button"
            variant="outline"
            onClick={() => handleClose(false)}
            disabled={sending}
          >
            Fermer
          </Button>
          <Button
            onClick={handleSend}
            disabled={sending || selected.length === 0}
            className="gap-2"
          >
            {sending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
            Inviter{selected.length > 0 ? ` (${selected.length})` : ""}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
