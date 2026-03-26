import React, { useState, useEffect, useCallback, useRef } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import Sidebar from "@/components/Sidebar";
import SafetyMenu from "@/components/SafetyMenu";
import MentionInput from "@/components/MentionInput";
import MentionText from "@/components/MentionText";
import { ArrowLeft, Send, Loader2, MessageCircle, Sparkles, Trash2, Pencil, Check, X, SmilePlus, ImagePlus, BellOff, Bell, CheckCheck } from "lucide-react";
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

// ── Reaction config (InFinea curated set — same as feed) ──
const REACTIONS = [
  { type: "bravo", emoji: "👏", label: "Bravo" },
  { type: "inspire", emoji: "✨", label: "Inspire" },
  { type: "fire", emoji: "🔥", label: "Fire" },
];

// Compact reaction picker — appears on hover, iMessage tapback style
function ReactionPicker({ onReact, myReaction }) {
  return (
    <div className="flex items-center gap-0.5 bg-card/95 backdrop-blur-sm border border-border/50 rounded-full px-1 py-0.5 shadow-lg">
      {REACTIONS.map(({ type, emoji, label }) => (
        <button
          key={type}
          onClick={() => onReact(type)}
          className={`w-7 h-7 flex items-center justify-center rounded-full text-sm transition-all duration-150 hover:scale-125 ${
            myReaction === type
              ? "bg-primary/20 ring-1 ring-primary/30 scale-110"
              : "hover:bg-muted/80"
          }`}
          title={label}
        >
          {emoji}
        </button>
      ))}
    </div>
  );
}

// Inline reaction display under a message bubble
function MessageReactionDisplay({ reactions, myId }) {
  if (!reactions || Object.keys(reactions).length === 0) return null;

  // Group by reaction type and count
  const grouped = {};
  for (const [userId, type] of Object.entries(reactions)) {
    if (!grouped[type]) grouped[type] = { count: 0, isMine: false };
    grouped[type].count++;
    if (userId === myId) grouped[type].isMine = true;
  }

  const reactionEmoji = { bravo: "👏", inspire: "✨", fire: "🔥" };

  return (
    <div className="flex items-center gap-1 mt-0.5">
      {Object.entries(grouped).map(([type, { count, isMine }]) => (
        <span
          key={type}
          className={`inline-flex items-center gap-0.5 text-[11px] px-1.5 py-0.5 rounded-full border ${
            isMine
              ? "bg-primary/10 border-primary/20 text-primary"
              : "bg-muted/50 border-border/30 text-muted-foreground"
          }`}
        >
          {reactionEmoji[type] || type}
          {count > 1 && <span className="text-[10px] font-medium">{count}</span>}
        </span>
      ))}
    </div>
  );
}

// Image display in message bubble (WhatsApp/iMessage style)
function MessageImages({ images, isMine }) {
  const [lightboxIdx, setLightboxIdx] = useState(null);
  if (!images || images.length === 0) return null;

  return (
    <>
      <div className={`flex flex-wrap gap-1 ${images.length === 1 ? "" : "max-w-[280px]"}`}>
        {images.map((img, i) => (
          <img
            key={i}
            src={img.thumbnail_url || img.image_url}
            alt=""
            onClick={() => setLightboxIdx(i)}
            className={`rounded-lg cursor-pointer object-cover ${
              images.length === 1
                ? "max-w-[280px] max-h-[300px] w-auto"
                : "w-[136px] h-[136px]"
            }`}
          />
        ))}
      </div>
      {/* Lightbox */}
      {lightboxIdx !== null && (
        <div
          className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center"
          onClick={() => setLightboxIdx(null)}
        >
          <img
            src={images[lightboxIdx].image_url}
            alt=""
            className="max-w-[90vw] max-h-[90vh] object-contain rounded-lg"
            onClick={(e) => e.stopPropagation()}
          />
          <button
            onClick={() => setLightboxIdx(null)}
            className="absolute top-4 right-4 text-white/70 hover:text-white p-2"
          >
            <X className="w-6 h-6" />
          </button>
        </div>
      )}
    </>
  );
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
  // Image upload state
  const [pendingImages, setPendingImages] = useState([]);  // [{file, preview, uploading, uploaded: {image_url, ...}}]
  const imageInputRef = useRef(null);
  // Mute state
  const [muted, setMuted] = useState(false);
  const [togglingMute, setTogglingMute] = useState(false);

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
          if (conv) {
            setConversation(conv);
            setMuted(conv.muted || false);
          }
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

  // Image selection + async upload (upload-then-attach, same as feed posts)
  const handleImageSelect = async (e) => {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;
    // Max 4 images total
    const remaining = 4 - pendingImages.length;
    const toUpload = files.slice(0, remaining);

    for (const file of toUpload) {
      if (file.size > 10 * 1024 * 1024) {
        toast.error("Image trop lourde (max 10 MB)");
        continue;
      }
      const preview = URL.createObjectURL(file);
      const idx = pendingImages.length;
      setPendingImages((prev) => [...prev, { file, preview, uploading: true, uploaded: null }]);

      // Upload to Cloudinary via existing endpoint
      try {
        const formData = new FormData();
        formData.append("file", file);
        const res = await authFetch(`${API}/feed/upload-image`, {
          method: "POST",
          body: formData,
        });
        if (res.ok) {
          const data = await res.json();
          setPendingImages((prev) =>
            prev.map((img, i) =>
              img.preview === preview
                ? { ...img, uploading: false, uploaded: data }
                : img
            )
          );
        } else {
          toast.error("Échec de l'upload");
          setPendingImages((prev) => prev.filter((img) => img.preview !== preview));
        }
      } catch {
        toast.error("Erreur d'upload");
        setPendingImages((prev) => prev.filter((img) => img.preview !== preview));
      }
    }
    // Reset input
    if (imageInputRef.current) imageInputRef.current.value = "";
  };

  const removeImage = (preview) => {
    setPendingImages((prev) => prev.filter((img) => img.preview !== preview));
  };

  // Send message (text and/or images)
  const handleSend = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
    const text = messageText.trim();
    const uploadedImages = pendingImages
      .filter((img) => img.uploaded)
      .map((img) => img.uploaded);
    const hasText = text.length > 0;
    const hasImages = uploadedImages.length > 0;

    if ((!hasText && !hasImages) || sending) return;
    // Wait for all uploads to complete
    if (pendingImages.some((img) => img.uploading)) {
      toast.info("Upload en cours, un instant...");
      return;
    }
    setSending(true);

    try {
      const payload = { content: text };
      if (hasImages) payload.images = uploadedImages;

      const res = await authFetch(`${API}/conversations/${conversationId}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        const newMsg = await res.json();
        setMessages((prev) => [...prev, newMsg]);
        setMessageText("");
        setMessageMentions([]);
        setPendingImages([]);
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

  // React to a message (toggle)
  const handleReactMessage = async (messageId, reactionType) => {
    try {
      const res = await authFetch(`${API}/messages/${messageId}/reactions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reaction_type: reactionType }),
      });
      if (res.ok) {
        const data = await res.json();
        setMessages((prev) =>
          prev.map((m) =>
            m.message_id === messageId
              ? { ...m, reactions: data.reactions }
              : m
          )
        );
      }
    } catch {
      // Silent — reaction is non-critical UX
    }
  };

  const handleToggleMute = async () => {
    setTogglingMute(true);
    try {
      const res = await authFetch(`${API}/conversations/${conversationId}/mute`, { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        setMuted(data.muted);
        toast.success(data.muted ? "Conversation muette" : "Notifications réactivées");
      }
    } catch {
      toast.error("Erreur");
    } finally {
      setTogglingMute(false);
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
            {/* Mute toggle */}
            <button
              onClick={handleToggleMute}
              disabled={togglingMute}
              className={`w-8 h-8 flex items-center justify-center rounded-full transition-all ${
                muted
                  ? "text-white/90 bg-white/15"
                  : "text-white/40 hover:text-white/70 hover:bg-white/10"
              }`}
              title={muted ? "Réactiver les notifications" : "Couper les notifications"}
            >
              {muted ? <BellOff className="w-4 h-4" /> : <Bell className="w-4 h-4" />}
            </button>
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
                      {/* Actions: edit/delete (own messages) + reaction picker */}
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
                      {/* Reaction picker — appears on hover for received messages, left side for own */}
                      {!isMine && editingMessageId !== msg.message_id && (
                        <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-150 mb-0.5 order-last ml-1">
                          <ReactionPicker
                            onReact={(type) => handleReactMessage(msg.message_id, type)}
                            myReaction={msg.reactions?.[myId]}
                          />
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
                        <div className="max-w-[75%] flex flex-col">
                          {/* Images above text bubble */}
                          {msg.images && msg.images.length > 0 && (
                            <div className={`mb-1 ${isMine ? "self-end" : "self-start"}`}>
                              <MessageImages images={msg.images} isMine={isMine} />
                            </div>
                          )}
                          {/* Text bubble (skip if image-only with no text) */}
                          {msg.content && (
                          <div
                            className={`relative px-3.5 py-2 rounded-2xl text-sm leading-relaxed ${
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
                          {/* Reaction display under bubble */}
                          <div className={`${isMine ? "self-end" : "self-start"}`}>
                            <MessageReactionDisplay reactions={msg.reactions} myId={myId} />
                          </div>
                          {/* Read receipt — iMessage double-check */}
                          {isMine && (
                            <div className="self-end flex items-center gap-1 mt-0.5">
                              <span className="text-[9px] text-muted-foreground/40">
                                {formatTime(msg.created_at)}
                              </span>
                              <CheckCheck
                                className={`w-3 h-3 ${
                                  msg.read_at
                                    ? "text-[#459492]"
                                    : "text-muted-foreground/30"
                                }`}
                              />
                            </div>
                          )}
                        </div>
                      )}
                      {/* Reaction picker for own messages — right side */}
                      {isMine && editingMessageId !== msg.message_id && (
                        <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-150 mb-0.5 order-first mr-1">
                          <ReactionPicker
                            onReact={(type) => handleReactMessage(msg.message_id, type)}
                            myReaction={msg.reactions?.[myId]}
                          />
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
            {/* Pending image previews */}
            {pendingImages.length > 0 && (
              <div className="flex items-center gap-2 mb-2 overflow-x-auto scrollbar-thin pb-1">
                {pendingImages.map((img, i) => (
                  <div key={i} className="relative shrink-0">
                    <img
                      src={img.preview}
                      alt=""
                      className="w-16 h-16 object-cover rounded-lg border border-border/50"
                    />
                    {img.uploading && (
                      <div className="absolute inset-0 bg-black/40 rounded-lg flex items-center justify-center">
                        <Loader2 className="w-4 h-4 animate-spin text-white" />
                      </div>
                    )}
                    <button
                      onClick={() => removeImage(img.preview)}
                      className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-destructive text-white rounded-full flex items-center justify-center text-[10px] shadow"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>
            )}
            <form onSubmit={handleSend} className="flex items-center gap-2">
              {/* Image upload button */}
              <input
                ref={imageInputRef}
                type="file"
                accept="image/jpeg,image/png,image/webp,image/gif"
                multiple
                className="hidden"
                onChange={handleImageSelect}
              />
              <button
                type="button"
                onClick={() => imageInputRef.current?.click()}
                disabled={pendingImages.length >= 4}
                className="h-10 w-10 rounded-full flex items-center justify-center text-muted-foreground hover:text-primary hover:bg-primary/10 transition-colors shrink-0 disabled:opacity-40"
                title="Ajouter une image"
              >
                <ImagePlus className="w-5 h-5" />
              </button>
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
                disabled={(!messageText.trim() && pendingImages.filter(i => i.uploaded).length === 0) || sending}
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
