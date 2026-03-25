import React, { useState, useEffect, useCallback, useRef } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import Sidebar from "@/components/Sidebar";
import SafetyMenu from "@/components/SafetyMenu";
import MentionInput from "@/components/MentionInput";
import MentionText from "@/components/MentionText";
import { ArrowLeft, Send, Loader2, MessageCircle, Sparkles, Trash2, Pencil, Check, X } from "lucide-react";
import { toast } from "sonner";
import { API, authFetch, useAuth } from "@/App";
import { sanitize } from "@/lib/sanitize";

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

function formatTime(iso) {
  if (!iso) return "";
  return new Date(iso).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
}

function getInitials(name) {
  if (!name) return "U";
  return name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2);
}

export default function ConversationPage() {
  const { conversationId } = useParams();
  const { user: currentUser } = useAuth();
  const navigate = useNavigate();

  const [messages, setMessages] = useState([]);
  const [conversation, setConversation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [messageText, setMessageText] = useState("");
  const [messageMentions, setMessageMentions] = useState([]);
  const [hasMore, setHasMore] = useState(false);
  const [cursor, setCursor] = useState(null);
  const [loadingMore, setLoadingMore] = useState(false);
  // Edit state (15-min window)
  const [editingMessageId, setEditingMessageId] = useState(null);
  const [editText, setEditText] = useState("");
  const [savingEdit, setSavingEdit] = useState(false);

  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);
  const pollRef = useRef(null);

  // Fetch conversation info
  useEffect(() => {
    (async () => {
      try {
        const res = await authFetch(`${API}/conversations`);
        if (res.ok) {
          const data = await res.json();
          const conv = (data.conversations || []).find(
            (c) => c.conversation_id === conversationId
          );
          if (conv) setConversation(conv);
        }
      } catch { /* silent */ }
    })();
  }, [conversationId]);

  // Fetch messages
  const fetchMessages = useCallback(async (cursorVal = null) => {
    const isInitial = !cursorVal;
    if (isInitial) setLoading(true);
    else setLoadingMore(true);

    try {
      const url = cursorVal
        ? `${API}/conversations/${conversationId}/messages?limit=30&cursor=${encodeURIComponent(cursorVal)}`
        : `${API}/conversations/${conversationId}/messages?limit=30`;
      const res = await authFetch(url);
      if (res.ok) {
        const data = await res.json();
        const newMsgs = data.messages || [];
        if (isInitial) {
          setMessages(newMsgs);
        } else {
          // Prepend older messages
          setMessages((prev) => [...newMsgs, ...prev]);
        }
        setCursor(data.next_cursor);
        setHasMore(data.has_more);
      }
    } catch {
      toast.error("Erreur lors du chargement");
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, [conversationId]);

  useEffect(() => {
    fetchMessages();
  }, [fetchMessages]);

  // Mark as read on mount
  useEffect(() => {
    if (conversationId) {
      authFetch(`${API}/conversations/${conversationId}/read`, { method: "PUT" }).catch(() => {});
    }
  }, [conversationId]);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (!loadingMore && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages.length, loadingMore]);

  // Poll for new messages every 10s
  useEffect(() => {
    pollRef.current = setInterval(async () => {
      try {
        const res = await authFetch(
          `${API}/conversations/${conversationId}/messages?limit=30`
        );
        if (res.ok) {
          const data = await res.json();
          setMessages(data.messages || []);
          // Mark as read silently
          authFetch(`${API}/conversations/${conversationId}/read`, { method: "PUT" }).catch(() => {});
        }
      } catch { /* silent */ }
    }, 10000);
    return () => clearInterval(pollRef.current);
  }, [conversationId]);

  // Send message
  const handleSend = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
    const text = messageText.trim();
    if (!text || sending) return;
    setSending(true);

    try {
      const res = await authFetch(`${API}/conversations/${conversationId}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: text }),
      });
      if (res.ok) {
        const newMsg = await res.json();
        setMessages((prev) => [...prev, newMsg]);
        setMessageText("");
        setMessageMentions([]);
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

  // Load older messages
  const handleLoadMore = () => {
    if (hasMore && cursor && !loadingMore) {
      fetchMessages(cursor);
    }
  };

  // Delete own message
  const handleDeleteMessage = async (messageId) => {
    try {
      const res = await authFetch(`${API}/messages/${messageId}`, { method: "DELETE" });
      if (res.ok) {
        setMessages((prev) => prev.filter((m) => m.message_id !== messageId));
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || "Impossible de supprimer");
      }
    } catch {
      toast.error("Erreur de connexion");
    }
  };

  // Edit own message (15-min window)
  const canEditMessage = (createdAt) => {
    const created = new Date(createdAt);
    return (Date.now() - created.getTime()) < 15 * 60 * 1000;
  };

  const startEditMessage = (msg) => {
    setEditingMessageId(msg.message_id);
    setEditText(msg.content);
  };

  const cancelEditMessage = () => {
    setEditingMessageId(null);
    setEditText("");
  };

  const handleSaveEditMessage = async (messageId) => {
    if (!editText.trim() || savingEdit) return;
    setSavingEdit(true);
    try {
      const res = await authFetch(`${API}/messages/${messageId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: editText.trim() }),
      });
      if (res.ok) {
        const data = await res.json();
        setMessages((prev) =>
          prev.map((m) =>
            m.message_id === messageId
              ? { ...m, content: data.content, mentions: data.mentions, edited_at: data.edited_at }
              : m
          )
        );
        cancelEditMessage();
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || "Impossible de modifier");
      }
    } catch {
      toast.error("Erreur de connexion");
    } finally {
      setSavingEdit(false);
    }
  };

  const other = conversation?.other_user || {};
  const myId = currentUser?.user_id;

  // AI suggestions based on other user's profile
  const aiSuggestions = (() => {
    if (!other.user_id) return [];
    const suggestions = [];
    if (other.streak_days > 0) {
      suggestions.push(`Bravo pour ton streak de ${other.streak_days} jour${other.streak_days > 1 ? "s" : ""} !`);
    }
    if (other.display_name) {
      suggestions.push(`Salut ${other.display_name.split(" ")[0]} ! Comment avances-tu ?`);
    }
    if (suggestions.length === 0) {
      suggestions.push("Salut ! Tu travailles sur quoi en ce moment ?");
    }
    return suggestions;
  })();

  return (
    <div className="min-h-screen app-bg-mesh">
      <Sidebar />
      <main className="lg:ml-64 pt-14 lg:pt-0 pb-0 flex flex-col h-screen lg:h-screen">
        {/* Header */}
        <div className="section-dark-header px-4 lg:px-8 py-4 shrink-0">
          <div className="max-w-3xl mx-auto flex items-center gap-3">
            <Link
              to="/messages"
              className="text-white/50 hover:text-white/80 transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <Link to={other.user_id ? `/users/${other.user_id}` : "#"} className="flex items-center gap-3 flex-1 min-w-0">
              <Avatar className="w-10 h-10 ring-2 ring-white/10">
                <AvatarImage src={other.avatar_url} alt={other.display_name} />
                <AvatarFallback className="bg-white/10 text-white text-sm">
                  {getInitials(other.display_name)}
                </AvatarFallback>
              </Avatar>
              <div className="min-w-0">
                <p className="text-white font-semibold text-sm truncate">
                  {other.display_name || "Conversation"}
                </p>
                {other.username && (
                  <p className="text-white/40 text-xs">@{other.username}</p>
                )}
              </div>
            </Link>
            {other.user_id && (
              <SafetyMenu
                userId={other.user_id}
                targetType="user"
                targetId={other.user_id}
                size="sm"
                onBlockChange={(blocked) => {
                  if (blocked) navigate("/messages");
                }}
              />
            )}
          </div>
        </div>

        {/* Messages area */}
        <div
          ref={messagesContainerRef}
          className="flex-1 overflow-y-auto px-4 lg:px-8"
        >
          <div className="max-w-3xl mx-auto py-4 space-y-1">
            {/* Load more */}
            {hasMore && (
              <div className="flex justify-center py-2">
                <button
                  onClick={handleLoadMore}
                  disabled={loadingMore}
                  className="text-xs text-primary hover:underline disabled:opacity-50"
                >
                  {loadingMore ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    "Charger les messages précédents"
                  )}
                </button>
              </div>
            )}

            {loading ? (
              <div className="flex justify-center py-16">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
              </div>
            ) : messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center mb-4 ring-1 ring-primary/10">
                  <MessageCircle className="w-7 h-7 text-primary" />
                </div>
                <p className="text-muted-foreground text-sm mb-4">
                  Envoyez le premier message
                </p>
                {aiSuggestions.length > 0 && (
                  <div className="flex flex-col gap-2 w-full max-w-xs">
                    <div className="flex items-center justify-center gap-1.5 text-xs text-primary/60 mb-1">
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>Suggestions</span>
                    </div>
                    {aiSuggestions.map((s, i) => (
                      <button
                        key={i}
                        onClick={() => setMessageText(s)}
                        className="text-xs text-left px-3 py-2 rounded-xl bg-primary/5 hover:bg-primary/10 text-foreground/70 hover:text-foreground transition-colors border border-primary/10"
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              messages.map((msg, i) => {
                const isMine = msg.sender_id === myId;
                const prevMsg = messages[i - 1];
                const showTime =
                  !prevMsg ||
                  new Date(msg.created_at).getTime() - new Date(prevMsg.created_at).getTime() > 300000;

                return (
                  <React.Fragment key={msg.message_id}>
                    {showTime && (
                      <div className="flex justify-center py-2">
                        <span className="text-[10px] text-muted-foreground/60 bg-muted/50 px-2 py-0.5 rounded-full">
                          {timeAgo(msg.created_at)} · {formatTime(msg.created_at)}
                        </span>
                      </div>
                    )}
                    <div className={`group flex items-end gap-1 ${isMine ? "justify-end" : "justify-start"}`}>
                      {isMine && editingMessageId !== msg.message_id && (
                        <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity duration-150 mb-0.5">
                          {canEditMessage(msg.created_at) && (
                            <button
                              onClick={() => startEditMessage(msg)}
                              className="p-1 rounded-full hover:bg-primary/10 text-muted-foreground/50 hover:text-primary"
                              title="Modifier"
                            >
                              <Pencil className="w-3 h-3" />
                            </button>
                          )}
                          <button
                            onClick={() => handleDeleteMessage(msg.message_id)}
                            className="p-1 rounded-full hover:bg-destructive/10 text-muted-foreground/50 hover:text-destructive"
                            title="Supprimer"
                          >
                            <Trash2 className="w-3 h-3" />
                          </button>
                        </div>
                      )}
                      {editingMessageId === msg.message_id ? (
                        /* ── Inline edit mode ── */
                        <div className="max-w-[75%] flex items-center gap-1.5">
                          <input
                            value={editText}
                            onChange={(e) => setEditText(e.target.value)}
                            maxLength={1000}
                            className="flex-1 h-9 text-sm rounded-xl border border-primary/30 bg-primary/[0.03] px-3 focus:outline-none focus:ring-1 focus:ring-primary/40"
                            autoFocus
                            onKeyDown={(e) => {
                              if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSaveEditMessage(msg.message_id); }
                              if (e.key === "Escape") cancelEditMessage();
                            }}
                          />
                          <button onClick={() => handleSaveEditMessage(msg.message_id)} disabled={savingEdit || !editText.trim()} className="p-1.5 rounded-full bg-primary/10 text-primary hover:bg-primary/20 transition-colors" title="Enregistrer">
                            {savingEdit ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
                          </button>
                          <button onClick={cancelEditMessage} className="p-1.5 rounded-full text-muted-foreground/50 hover:bg-muted/50 hover:text-muted-foreground transition-colors" title="Annuler">
                            <X className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      ) : (
                        <div
                          className={`max-w-[75%] px-3.5 py-2 rounded-2xl text-sm leading-relaxed ${
                            isMine
                              ? "bg-gradient-to-br from-[#459492] to-[#55B3AE] text-white rounded-br-md"
                              : "bg-card border border-border/50 text-foreground rounded-bl-md"
                          }`}
                        >
                          <p className="whitespace-pre-wrap break-words">
                            <MentionText
                              content={msg.content}
                              mentions={msg.mentions}
                              currentUserId={myId}
                              variant={isMine ? "dark" : "light"}
                            />
                          </p>
                          {msg.edited_at && (
                            <span className={`text-[9px] italic mt-0.5 block ${isMine ? "text-white/60" : "text-muted-foreground/50"}`}>
                              (modifié)
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </React.Fragment>
                );
              })
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input bar */}
        <div className="shrink-0 border-t border-border/30 bg-background/80 backdrop-blur-sm px-4 lg:px-8 py-3">
          <div className="max-w-3xl mx-auto">
            {/* AI quick suggestions — visible when input empty and conversation has few messages */}
            {!messageText && messages.length > 0 && messages.length <= 3 && aiSuggestions.length > 0 && (
              <div className="flex items-center gap-2 mb-2 overflow-x-auto scrollbar-thin">
                <Sparkles className="w-3.5 h-3.5 text-primary/50 shrink-0" />
                {aiSuggestions.map((s, i) => (
                  <button
                    key={i}
                    onClick={() => setMessageText(s)}
                    className="text-[11px] whitespace-nowrap px-2.5 py-1 rounded-full bg-primary/5 hover:bg-primary/10 text-foreground/60 hover:text-foreground transition-colors border border-primary/10 shrink-0"
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}
            <form onSubmit={handleSend} className="flex items-center gap-2">
              <MentionInput
                value={messageText}
                onChange={setMessageText}
                mentions={messageMentions}
                onMentionsChange={setMessageMentions}
                context="message"
                contextId={conversationId}
                placeholder="Écris un message..."
                maxLength={1000}
                autoFocus
                className="flex-1 h-10 rounded-full border-border/50 bg-muted/30 focus:bg-white px-4 text-sm"
                onSubmit={handleSend}
              />
              <Button
                type="submit"
                size="icon"
                disabled={!messageText.trim() || sending}
                className="h-10 w-10 rounded-full bg-gradient-to-r from-[#459492] to-[#55B3AE] hover:from-[#275255] hover:to-[#459492] text-white shadow-md shrink-0"
              >
                {sending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
              </Button>
            </form>
          </div>
        </div>
      </main>
    </div>
  );
}
