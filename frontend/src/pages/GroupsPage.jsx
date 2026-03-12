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
    <div className="min-h-screen bg-background">
      <Sidebar />
      <main className="lg:ml-64 pt-20 lg:pt-8 px-4 lg:px-8 pb-8">
        <div className="max-w-5xl mx-auto">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-2xl font-heading font-bold text-foreground flex items-center gap-2">
                <Users className="w-6 h-6 text-primary" />
                Mes Groupes
              </h1>
              <p className="text-muted-foreground text-sm mt-1">
                Progresse avec tes proches, duo ou en équipe.
              </p>
            </div>
            <Button onClick={() => setCreateOpen(true)} className="gap-2">
              <Plus className="w-4 h-4" />
              <span className="hidden sm:inline">Créer un groupe</span>
            </Button>
          </div>

          {/* Content */}
          {isLoading ? (
            <div className="flex justify-center py-20">
              <Loader2 className="w-6 h-6 animate-spin text-primary" />
            </div>
          ) : groups.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mb-4">
                <UsersRound className="w-8 h-8 text-primary" />
              </div>
              <h2 className="text-lg font-heading font-semibold text-foreground mb-2">
                Aucun groupe pour l'instant
              </h2>
              <p className="text-muted-foreground text-sm max-w-sm mb-6">
                Crée un duo ou un groupe pour progresser ensemble.
                Invite tes amis et suivez vos progressions mutuelles.
              </p>
              <Button onClick={() => setCreateOpen(true)} className="gap-2">
                <Plus className="w-4 h-4" />
                Créer mon premier groupe
              </Button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {groups.map((group) => (
                <GroupCard key={group.group_id} group={group} />
              ))}
            </div>
          )}
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
