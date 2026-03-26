/**
 * NewGroupPage — Create a group conversation.
 *
 * Pattern: Discord "New Group DM" — search users, select chips, name group, create.
 * Route: /messages/new-group
 */

import React, { useState, useCallback, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import Sidebar from "@/components/Sidebar";
import { ArrowLeft, Users, Search, X, Loader2, Plus } from "lucide-react";
import { toast } from "sonner";
import { API, authFetch } from "@/App";

function getInitials(name) {
  if (!name) return "U";
  return name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2);
}

const MAX_MEMBERS = 19; // + creator = 20 total

export default function NewGroupPage() {
  const navigate = useNavigate();
  const [groupName, setGroupName] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [selectedMembers, setSelectedMembers] = useState([]);
  const [creating, setCreating] = useState(false);
  const searchInputRef = useRef(null);
  const debounceRef = useRef(null);

  const handleSearch = useCallback((q) => {
    setSearchQuery(q);
    if (debounceRef.current) clearTimeout(debounceRef.current);

    if (q.length < 2) {
      setSearchResults([]);
      return;
    }

    debounceRef.current = setTimeout(async () => {
      setSearching(true);
      try {
        const res = await authFetch(`${API}/search/users?q=${encodeURIComponent(q)}&limit=15`);
        if (res.ok) {
          const data = await res.json();
          const selectedIds = new Set(selectedMembers.map((m) => m.user_id));
          setSearchResults(
            (data.users || []).filter((u) => !selectedIds.has(u.user_id))
          );
        }
      } catch { /* silent */ }
      setSearching(false);
    }, 300);
  }, [selectedMembers]);

  const addMember = (user) => {
    if (selectedMembers.length >= MAX_MEMBERS) {
      toast.error(`Maximum ${MAX_MEMBERS} membres (+ vous = 20)`);
      return;
    }
    setSelectedMembers((prev) => [...prev, user]);
    setSearchResults((prev) => prev.filter((u) => u.user_id !== user.user_id));
    setSearchQuery("");
    searchInputRef.current?.focus();
  };

  const removeMember = (userId) => {
    setSelectedMembers((prev) => prev.filter((m) => m.user_id !== userId));
  };

  const handleCreate = async () => {
    const name = groupName.trim();
    if (!name) {
      toast.error("Donnez un nom au groupe");
      return;
    }
    if (selectedMembers.length === 0) {
      toast.error("Ajoutez au moins un membre");
      return;
    }

    setCreating(true);
    try {
      const res = await authFetch(`${API}/conversations/group`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          member_ids: selectedMembers.map((m) => m.user_id),
        }),
      });
      if (res.ok) {
        const conv = await res.json();
        toast.success("Groupe créé !");
        navigate(`/messages/${conv.conversation_id}`, { replace: true });
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || "Erreur lors de la création");
      }
    } catch {
      toast.error("Erreur de connexion");
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="min-h-screen app-bg-mesh">
      <Sidebar />
      <main className="lg:ml-64 pt-14 lg:pt-0 pb-8">
        {/* Dark header */}
        <div className="section-dark-header px-4 lg:px-8 pt-8 lg:pt-10 pb-8">
          <div className="max-w-2xl mx-auto">
            <div className="flex items-center gap-3 mb-1">
              <button
                onClick={() => navigate("/messages")}
                className="w-8 h-8 rounded-lg bg-white/10 hover:bg-white/20 flex items-center justify-center transition-colors"
              >
                <ArrowLeft className="w-4 h-4 text-white" />
              </button>
              <div className="w-10 h-10 rounded-xl bg-[#459492]/20 flex items-center justify-center">
                <Users className="w-5 h-5 text-[#55B3AE]" />
              </div>
              <div>
                <h1 className="text-display text-2xl font-semibold text-white opacity-0 animate-fade-in">
                  Nouveau groupe
                </h1>
                <p className="text-white/50 text-xs mt-0.5 opacity-0 animate-fade-in" style={{ animationDelay: "50ms" }}>
                  Max 20 membres · Messages privés de groupe
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="px-4 lg:px-8">
          <div className="max-w-2xl mx-auto mt-4 space-y-5 opacity-0 animate-fade-in" style={{ animationFillMode: "forwards" }}>
            {/* Group name */}
            <div>
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1.5 block">
                Nom du groupe
              </label>
              <input
                value={groupName}
                onChange={(e) => setGroupName(e.target.value)}
                placeholder="Ex : Groupe d'étude, Club de lecture..."
                maxLength={50}
                className="w-full h-11 rounded-xl border border-border/50 bg-card px-4 text-sm focus:outline-none focus:ring-2 focus:ring-[#459492]/30 focus:border-[#459492]/50 transition-all"
                autoFocus
              />
            </div>

            {/* Member selection */}
            <div>
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1.5 block">
                Membres ({selectedMembers.length}/{MAX_MEMBERS})
              </label>

              {/* Selected chips */}
              {selectedMembers.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mb-2">
                  {selectedMembers.map((m) => (
                    <span
                      key={m.user_id}
                      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#459492]/10 border border-[#459492]/20 text-sm"
                    >
                      <Avatar className="w-5 h-5">
                        <AvatarImage src={m.avatar_url || m.picture} alt={m.display_name || m.name} />
                        <AvatarFallback className="bg-primary/10 text-primary text-[8px]">
                          {getInitials(m.display_name || m.name)}
                        </AvatarFallback>
                      </Avatar>
                      <span className="text-xs font-medium truncate max-w-[100px]">
                        {(m.display_name || m.name || "").split(" ")[0]}
                      </span>
                      <button
                        onClick={() => removeMember(m.user_id)}
                        className="p-0.5 rounded-full hover:bg-destructive/20 text-muted-foreground/60 hover:text-destructive transition-colors"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                </div>
              )}

              {/* Search input */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground/40" />
                <input
                  ref={searchInputRef}
                  value={searchQuery}
                  onChange={(e) => handleSearch(e.target.value)}
                  placeholder="Rechercher un utilisateur..."
                  className="w-full h-10 rounded-xl border border-border/50 bg-card pl-9 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-[#459492]/30 focus:border-[#459492]/50 transition-all"
                />
                {searching && (
                  <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 animate-spin text-primary" />
                )}
              </div>

              {/* Search results */}
              {searchResults.length > 0 && (
                <div className="mt-2 space-y-0.5 max-h-60 overflow-y-auto rounded-xl border border-border/50 bg-card">
                  {searchResults.map((u) => (
                    <button
                      key={u.user_id}
                      onClick={() => addMember(u)}
                      className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-muted/30 transition-colors text-left"
                    >
                      <Avatar className="w-9 h-9">
                        <AvatarImage src={u.avatar_url || u.picture} alt={u.display_name || u.name} />
                        <AvatarFallback className="bg-primary/10 text-primary text-xs">
                          {getInitials(u.display_name || u.name)}
                        </AvatarFallback>
                      </Avatar>
                      <div className="flex-1 min-w-0">
                        <span className="text-sm font-medium truncate block">
                          {u.display_name || u.name}
                        </span>
                        {u.username && (
                          <span className="text-xs text-muted-foreground">@{u.username}</span>
                        )}
                      </div>
                      <Plus className="w-4 h-4 text-[#459492]" />
                    </button>
                  ))}
                </div>
              )}

              {searchQuery.length >= 2 && !searching && searchResults.length === 0 && (
                <p className="text-xs text-muted-foreground mt-2 text-center py-3">
                  Aucun utilisateur trouvé
                </p>
              )}
            </div>

            {/* Create button */}
            <Button
              onClick={handleCreate}
              disabled={creating || !groupName.trim() || selectedMembers.length === 0}
              className="w-full h-11 rounded-xl bg-gradient-to-r from-[#459492] to-[#55B3AE] hover:from-[#275255] hover:to-[#459492] text-white font-medium shadow-md btn-press"
            >
              {creating ? (
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
              ) : (
                <Users className="w-4 h-4 mr-2" />
              )}
              Créer le groupe ({selectedMembers.length + 1} membres)
            </Button>
          </div>
        </div>
      </main>
    </div>
  );
}
