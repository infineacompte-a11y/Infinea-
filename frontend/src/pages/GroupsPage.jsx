import React, { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Users, Plus, Loader2, UsersRound } from "lucide-react";
import { toast } from "sonner";
import { API, authFetch } from "@/App";
import Sidebar from "@/components/Sidebar";
import GroupCard from "@/components/GroupCard";
import CreateGroupDialog from "@/components/CreateGroupDialog";

/**
 * GroupsPage — Main groups listing page.
 * Pattern: Strava Clubs list + Duolingo Leaderboard hub.
 *
 * Route: /groups
 */
export default function GroupsPage() {
  const [groups, setGroups] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [createOpen, setCreateOpen] = useState(false);

  const fetchGroups = useCallback(async () => {
    try {
      const res = await authFetch(`${API}/groups`);
      if (!res.ok) throw new Error("Erreur");
      const data = await res.json();
      setGroups(data.groups || []);
    } catch {
      toast.error("Impossible de charger les groupes");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchGroups();
  }, [fetchGroups]);

  const handleCreated = useCallback((newGroup) => {
    setGroups((prev) => [newGroup, ...prev]);
  }, []);

  return (
    <div className="min-h-screen app-bg-mesh">
      <Sidebar />
      <main className="lg:ml-64 pt-14 lg:pt-0 pb-8">
        {/* Dark teal header */}
        <div className="section-dark-header px-4 lg:px-8 pt-8 lg:pt-10 pb-8">
          <div className="max-w-5xl mx-auto flex items-center justify-between">
            <div>
              <h1 className="text-display text-3xl lg:text-4xl font-semibold text-white opacity-0 animate-fade-in">
                Groupes
              </h1>
              <p className="text-white/60 text-sm mt-1 opacity-0 animate-fade-in" style={{ animationDelay: "50ms" }}>
                Progressez ensemble
              </p>
            </div>
            <Button
              onClick={() => setCreateOpen(true)}
              className="gap-2 rounded-xl shadow-md hover:shadow-lg bg-white/10 hover:bg-white/20 text-white border-0 transition-all duration-200 btn-press opacity-0 animate-fade-in"
              style={{ animationDelay: "100ms" }}
            >
              <Plus className="w-4 h-4" />
              <span className="hidden sm:inline">Créer un groupe</span>
            </Button>
          </div>
        </div>
        <div className="px-4 lg:px-8">
          <div className="max-w-5xl mx-auto">

          {/* Content */}
          {isLoading ? (
            <div className="opacity-0 animate-fade-in" style={{ animationDelay: "200ms", animationFillMode: "forwards" }}>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-40 rounded-xl bg-card border border-border/30 animate-pulse" />
                ))}
              </div>
            </div>
          ) : groups.length === 0 ? (
            <div className="opacity-0 animate-fade-in" style={{ animationDelay: "200ms", animationFillMode: "forwards" }}>
              <div className="flex flex-col items-center justify-center py-20 text-center">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center mb-4 ring-1 ring-primary/10">
                  <UsersRound className="w-8 h-8 text-primary" />
                </div>
                <h2 className="text-lg font-sans font-semibold tracking-tight font-semibold text-foreground mb-2">
                  Aucun groupe pour l'instant
                </h2>
                <p className="text-muted-foreground text-sm max-w-sm mb-6">
                  Crée un duo ou un groupe pour progresser ensemble.
                  Invite tes amis et suivez vos progressions mutuelles.
                </p>
                <Button
                  onClick={() => setCreateOpen(true)}
                  className="gap-2 rounded-xl shadow-md hover:shadow-lg bg-gradient-to-r from-[#459492] to-[#55B3AE] hover:from-[#275255] hover:to-[#459492] text-white border-0 transition-all duration-200 btn-press"
                >
                  <Plus className="w-4 h-4" />
                  Créer mon premier groupe
                </Button>
              </div>
            </div>
          ) : (
            <div className="opacity-0 animate-fade-in" style={{ animationDelay: "200ms", animationFillMode: "forwards" }}>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {groups.map((group, index) => (
                  <div
                    key={group.group_id}
                    className="opacity-0 animate-fade-in hover:shadow-xl hover:-translate-y-1 transition-all duration-300"
                    style={{ animationDelay: `${300 + index * 80}ms`, animationFillMode: "forwards" }}
                  >
                    <GroupCard group={group} />
                  </div>
                ))}
              </div>
            </div>
          )}
          </div>
        </div>
      </main>

      <CreateGroupDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        onCreated={handleCreated}
      />
    </div>
  );
}
