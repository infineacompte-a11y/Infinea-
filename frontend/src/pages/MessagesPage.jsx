import React, { useState, useEffect, useCallback } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import Sidebar from "@/components/Sidebar";
import { MessageCircle, ArrowLeft, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { API, authFetch } from "@/App";

function timeAgo(iso) {
  if (!iso) return "";
  const diff = Date.now() - new Date(iso).getTime();
  const min = Math.floor(diff / 60000);
  if (min < 1) return "à l'instant";
  if (min < 60) return `${min} min`;
  const h = Math.floor(min / 60);
  if (h < 24) return `${h}h`;
  const d = Math.floor(h / 24);
  if (d < 7) return `${d}j`;
  return new Date(iso).toLocaleDateString("fr-FR", { day: "numeric", month: "short" });
}

function getInitials(name) {
  if (!name) return "U";
  return name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2);
}

export default function MessagesPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchConversations = useCallback(async () => {
    try {
      const res = await authFetch(`${API}/conversations`);
      if (res.ok) {
        const data = await res.json();
        setConversations(data.conversations || []);
      }
    } catch {
      toast.error("Erreur lors du chargement des messages");
    } finally {
      setLoading(false);
    }
  }, []);

  // If ?user=xxx query param, auto-create/open conversation
  useEffect(() => {
    const targetUser = searchParams.get("user");
    if (targetUser) {
      (async () => {
        try {
          const res = await authFetch(`${API}/conversations`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id: targetUser }),
          });
          if (res.ok) {
            const conv = await res.json();
            navigate(`/messages/${conv.conversation_id}`, { replace: true });
            return;
          }
        } catch { /* fallthrough to normal list */ }
        fetchConversations();
      })();
    } else {
      fetchConversations();
    }
  }, [searchParams, navigate, fetchConversations]);

  return (
    <div className="min-h-screen app-bg-mesh">
      <Sidebar />
      <main className="lg:ml-64 pt-14 lg:pt-0 pb-8">
        {/* Dark header */}
        <div className="section-dark-header px-4 lg:px-8 pt-8 lg:pt-10 pb-8">
          <div className="max-w-3xl mx-auto">
            <h1 className="text-display text-3xl lg:text-4xl font-semibold text-white opacity-0 animate-fade-in">
              Messages
            </h1>
            <p className="text-white/60 text-sm mt-1 opacity-0 animate-fade-in" style={{ animationDelay: "50ms" }}>
              Vos conversations privées
            </p>
          </div>
        </div>

        <div className="px-4 lg:px-8">
          <div className="max-w-3xl mx-auto">
            {loading ? (
              <div className="flex justify-center py-16">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
              </div>
            ) : conversations.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-16 text-center opacity-0 animate-fade-in" style={{ animationFillMode: "forwards" }}>
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center mb-4 ring-1 ring-primary/10">
                  <MessageCircle className="w-8 h-8 text-primary" />
                </div>
                <h2 className="text-lg font-semibold text-foreground mb-2">
                  Aucun message
                </h2>
                <p className="text-muted-foreground text-sm max-w-xs mb-4">
                  Envoyez un message depuis le profil d'un utilisateur pour démarrer une conversation.
                </p>
                <Link to="/search">
                  <button className="text-sm text-primary hover:underline">
                    Rechercher des utilisateurs
                  </button>
                </Link>
              </div>
            ) : (
              <div className="space-y-1.5 opacity-0 animate-fade-in" style={{ animationFillMode: "forwards" }}>
                {conversations.map((conv, i) => {
                  const other = conv.other_user || {};
                  const lastMsg = conv.last_message;
                  const unread = conv.my_unread_count || 0;

                  return (
                    <Card
                      key={conv.conversation_id}
                      className="cursor-pointer hover:border-[#459492]/20 hover:shadow-md hover:-translate-y-0.5 transition-all duration-300 opacity-0 animate-fade-in"
                      style={{ animationDelay: `${i * 50}ms`, animationFillMode: "forwards" }}
                      onClick={() => navigate(`/messages/${conv.conversation_id}`)}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-center gap-3">
                          <div className="relative shrink-0">
                            <Avatar className="w-12 h-12 ring-2 ring-[#459492]/10 ring-offset-1 ring-offset-background">
                              <AvatarImage src={other.avatar_url} alt={other.display_name} />
                              <AvatarFallback className="bg-primary/10 text-primary text-sm font-medium">
                                {getInitials(other.display_name)}
                              </AvatarFallback>
                            </Avatar>
                            {unread > 0 && (
                              <span className="absolute -top-1 -right-1 min-w-[18px] h-[18px] px-1 flex items-center justify-center rounded-full bg-[#E48C75] text-white text-[9px] font-bold leading-none shadow-sm">
                                {unread > 99 ? "99+" : unread}
                              </span>
                            )}
                          </div>

                          <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between gap-2">
                              <span className={`font-medium text-sm truncate ${unread > 0 ? "text-foreground font-semibold" : "text-foreground"}`}>
                                {other.display_name}
                              </span>
                              {lastMsg && (
                                <span className="text-xs text-muted-foreground shrink-0">
                                  {timeAgo(lastMsg.created_at)}
                                </span>
                              )}
                            </div>
                            {lastMsg ? (
                              <p className={`text-xs truncate mt-0.5 ${unread > 0 ? "text-foreground font-medium" : "text-muted-foreground"}`}>
                                {lastMsg.content}
                              </p>
                            ) : (
                              <p className="text-xs text-muted-foreground/50 mt-0.5 italic">
                                Aucun message
                              </p>
                            )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
