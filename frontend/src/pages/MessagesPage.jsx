import React, { useState, useEffect, useCallback } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import Sidebar from "@/components/Sidebar";
import { MessageCircle, ArrowLeft, Loader2, Sparkles, BellOff, Users, Plus } from "lucide-react";
import { toast } from "sonner";
import { API, authFetch } from "@/App";
import { OnlineDot, OnlineLabel } from "@/components/OnlineIndicator";

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

/* ── Stacked avatar group for group conversations (Discord pattern) ── */
function GroupAvatarStack({ members, size = 12 }) {
  const show = members.slice(0, 3);
  return (
    <div className="relative" style={{ width: size * 4, height: size * 4 }}>
      {show.map((m, i) => (
        <Avatar
          key={m.user_id}
          className="absolute ring-2 ring-background"
          style={{
            width: size * 4 * 0.65,
            height: size * 4 * 0.65,
            left: i * (size * 4 * 0.28),
            top: i % 2 === 0 ? 0 : size * 4 * 0.3,
            zIndex: show.length - i,
          }}
        >
          <AvatarImage src={m.avatar_url} alt={m.display_name} />
          <AvatarFallback className="bg-primary/10 text-primary text-[9px] font-medium">
            {getInitials(m.display_name)}
          </AvatarFallback>
        </Avatar>
      ))}
      {members.length > 3 && (
        <span
          className="absolute flex items-center justify-center rounded-full bg-muted text-muted-foreground text-[9px] font-bold ring-2 ring-background"
          style={{
            width: size * 4 * 0.55,
            height: size * 4 * 0.55,
            right: 0,
            bottom: 0,
            zIndex: 0,
          }}
        >
          +{members.length - 3}
        </span>
      )}
    </div>
  );
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
          <div className="max-w-3xl mx-auto flex items-center justify-between">
            <div>
              <h1 className="text-display text-3xl lg:text-4xl font-semibold text-white opacity-0 animate-fade-in">
                Messages
              </h1>
              <p className="text-white/60 text-sm mt-1 flex items-center gap-1.5 opacity-0 animate-fade-in" style={{ animationDelay: "50ms" }}>
                <Sparkles className="w-3.5 h-3.5 text-white/40" />
                Conversations privées et groupes
              </p>
            </div>
            {/* New group button */}
            <button
              onClick={() => navigate("/messages/new-group")}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-white/10 hover:bg-white/20 text-white text-sm font-medium transition-colors opacity-0 animate-fade-in"
              style={{ animationDelay: "100ms" }}
            >
              <Users className="w-4 h-4" />
              <span className="hidden sm:inline">Nouveau groupe</span>
              <Plus className="w-3.5 h-3.5 sm:hidden" />
            </button>
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
                  <Sparkles className="w-3.5 h-3.5 text-primary/40 inline mr-1" />
                  Envoyez un message depuis le profil d'un utilisateur ou créez un groupe.
                </p>
                <div className="flex items-center gap-3">
                  <Link to="/search">
                    <button className="text-sm text-primary hover:underline">
                      Rechercher des utilisateurs
                    </button>
                  </Link>
                  <button
                    onClick={() => navigate("/messages/new-group")}
                    className="text-sm text-[#459492] hover:underline flex items-center gap-1"
                  >
                    <Users className="w-3.5 h-3.5" />
                    Créer un groupe
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-1.5 opacity-0 animate-fade-in" style={{ animationFillMode: "forwards" }}>
                {conversations.map((conv, i) => {
                  const isGroup = conv.type === "group";
                  const groupInfo = conv.group_info;
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
                          {/* Avatar: group stack or single */}
                          <div className="relative shrink-0">
                            {isGroup ? (
                              groupInfo?.members?.length > 0 ? (
                                <GroupAvatarStack members={groupInfo.members} />
                              ) : (
                                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-[#459492]/20 to-[#55B3AE]/10 flex items-center justify-center ring-2 ring-[#459492]/10 ring-offset-1 ring-offset-background">
                                  <Users className="w-5 h-5 text-[#459492]" />
                                </div>
                              )
                            ) : (
                              <>
                                <Avatar className="w-12 h-12 ring-2 ring-[#459492]/10 ring-offset-1 ring-offset-background">
                                  <AvatarImage src={other.avatar_url} alt={other.display_name} />
                                  <AvatarFallback className="bg-primary/10 text-primary text-sm font-medium">
                                    {getInitials(other.display_name)}
                                  </AvatarFallback>
                                </Avatar>
                                <OnlineDot presence={other.presence} size="md" />
                              </>
                            )}
                            {unread > 0 && (
                              <span className="absolute -top-1 -right-1 min-w-[18px] h-[18px] px-1 flex items-center justify-center rounded-full bg-[#E48C75] text-white text-[9px] font-bold leading-none shadow-sm">
                                {unread > 99 ? "99+" : unread}
                              </span>
                            )}
                          </div>

                          <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between gap-2">
                              <span className={`font-medium text-sm truncate flex items-center gap-1 ${unread > 0 ? "text-foreground font-semibold" : "text-foreground"}`}>
                                {isGroup ? (
                                  <>
                                    {groupInfo?.name || "Groupe"}
                                    <span className="text-[10px] text-muted-foreground/60 font-normal ml-0.5">
                                      · {groupInfo?.member_count || 0}
                                    </span>
                                    {groupInfo?.any_online && (
                                      <span
                                        className="inline-block w-2 h-2 rounded-full ml-1 shrink-0"
                                        style={{ backgroundColor: "#22c55e" }}
                                        title="Membres en ligne"
                                      />
                                    )}
                                  </>
                                ) : (
                                  <>
                                    {other.display_name}
                                    {other.presence?.status === "online" && (
                                      <span
                                        className="inline-block w-2 h-2 rounded-full ml-1 shrink-0"
                                        style={{ backgroundColor: "#22c55e" }}
                                        title="En ligne"
                                      />
                                    )}
                                  </>
                                )}
                                {conv.muted && <BellOff className="w-3 h-3 text-muted-foreground/40 shrink-0" />}
                              </span>
                              {lastMsg && (
                                <span className="text-xs text-muted-foreground shrink-0">
                                  {timeAgo(lastMsg.created_at)}
                                </span>
                              )}
                            </div>
                            {lastMsg ? (
                              <p className={`text-xs truncate mt-0.5 ${unread > 0 ? "text-foreground font-medium" : "text-muted-foreground"}`}>
                                {isGroup && lastMsg.sender_name && (
                                  <span className="font-medium text-foreground/70">{lastMsg.sender_name.split(" ")[0]} : </span>
                                )}
                                {lastMsg.content || (lastMsg.images?.length > 0 ? "📷 Photo" : "")}
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
