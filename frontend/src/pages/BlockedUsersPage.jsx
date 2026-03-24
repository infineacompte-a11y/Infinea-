import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import Sidebar from "@/components/Sidebar";
import { Ban, ArrowLeft, ShieldOff, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { API, authFetch } from "@/App";

export default function BlockedUsersPage() {
  const [blockedUsers, setBlockedUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [unblocking, setUnblocking] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const res = await authFetch(`${API}/users/blocked`);
        if (res.ok) {
          const data = await res.json();
          setBlockedUsers(data.blocked_users || []);
        }
      } catch { /* silent */ }
      setLoading(false);
    })();
  }, []);

  const handleUnblock = async (userId) => {
    setUnblocking(userId);
    try {
      const res = await authFetch(`${API}/users/${userId}/block`, {
        method: "DELETE",
      });
      if (res.ok) {
        setBlockedUsers((prev) => prev.filter((u) => u.user_id !== userId));
        toast.success("Utilisateur débloqué");
      } else {
        toast.error("Erreur lors du déblocage");
      }
    } catch {
      toast.error("Erreur de connexion");
    } finally {
      setUnblocking(null);
    }
  };

  const getInitials = (name) => {
    if (!name) return "U";
    return name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2);
  };

  return (
    <div className="min-h-screen app-bg-mesh">
      <Sidebar />
      <main className="lg:ml-64 pt-14 lg:pt-0 pb-8">
        <div className="section-dark-header px-4 lg:px-8 pt-8 lg:pt-10 pb-8">
          <div className="max-w-3xl mx-auto">
            <Link
              to="/profile"
              className="inline-flex items-center gap-1.5 text-white/50 hover:text-white/80 text-sm mb-4 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Profil
            </Link>
            <div className="flex items-center gap-3 opacity-0 animate-fade-in" style={{ animationFillMode: "forwards" }}>
              <div className="w-10 h-10 rounded-xl bg-white/10 flex items-center justify-center">
                <Ban className="w-5 h-5 text-white/70" />
              </div>
              <div>
                <h1 className="text-display text-xl font-semibold text-white">
                  Utilisateurs bloqués
                </h1>
                <p className="text-white/50 text-sm">
                  Les utilisateurs bloqués ne peuvent ni voir votre profil ni interagir avec vous.
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="px-4 lg:px-8">
          <div className="max-w-3xl mx-auto">
            {loading ? (
              <div className="flex justify-center py-16">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
              </div>
            ) : blockedUsers.length === 0 ? (
              <div className="text-center py-16 opacity-0 animate-fade-in" style={{ animationFillMode: "forwards" }}>
                <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-4">
                  <Ban className="w-8 h-8 text-primary/50" />
                </div>
                <p className="text-muted-foreground text-sm">
                  Aucun utilisateur bloqué
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                {blockedUsers.map((u) => (
                  <Card key={u.user_id} className="opacity-0 animate-fade-in" style={{ animationFillMode: "forwards" }}>
                    <CardContent className="p-4">
                      <div className="flex items-center gap-3">
                        <Link to={`/users/${u.user_id}`}>
                          <Avatar className="w-10 h-10">
                            <AvatarImage src={u.avatar_url} alt={u.display_name} />
                            <AvatarFallback className="bg-muted text-sm">
                              {getInitials(u.display_name)}
                            </AvatarFallback>
                          </Avatar>
                        </Link>
                        <div className="flex-1 min-w-0">
                          <p className="font-semibold text-sm truncate">
                            {u.display_name}
                          </p>
                          {u.username && (
                            <p className="text-xs text-muted-foreground">@{u.username}</p>
                          )}
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          className="rounded-xl gap-1.5 text-xs"
                          onClick={() => handleUnblock(u.user_id)}
                          disabled={unblocking === u.user_id}
                        >
                          {unblocking === u.user_id ? (
                            <Loader2 className="w-3 h-3 animate-spin" />
                          ) : (
                            <ShieldOff className="w-3 h-3" />
                          )}
                          Débloquer
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
