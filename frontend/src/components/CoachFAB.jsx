import React, { useState, useEffect, useRef, useCallback } from "react";
import { Button } from "@/components/ui/button";
import {
  Brain,
  X,
  Send,
  Sparkles,
  Trash2,
  MessageCircle,
  ArrowDown,
} from "lucide-react";
import { API, authFetch } from "@/App";
import VoiceInput from "@/components/VoiceInput";

const QUICK_REPLIES = [
  { label: "Que faire maintenant ?", message: "Que me conseilles-tu de faire maintenant ?" },
  { label: "Mon bilan", message: "Fais-moi un bilan de ma progression récente." },
  { label: "Motivation", message: "J'ai besoin d'un boost de motivation !" },
];

function CoachMessage({ msg }) {
  const isUser = msg.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-3 animate-fade-in`}>
      {!isUser && (
        <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center shrink-0 mr-2 mt-1 ring-1 ring-primary/10">
          <Brain className="w-3.5 h-3.5 text-primary" />
        </div>
      )}
      <div
        className={`max-w-[80%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed ${
          isUser
            ? "bg-primary text-primary-foreground rounded-br-md"
            : "bg-muted/50 border border-border/50 rounded-bl-md"
        }`}
      >
        {msg.content}
      </div>
    </div>
  );
}

export default function CoachFAB() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [hasNewMessage, setHasNewMessage] = useState(false);
  const [voiceListening, setVoiceListening] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const panelRef = useRef(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  // Load history when panel opens
  useEffect(() => {
    if (isOpen && messages.length === 0) {
      loadHistory();
    }
    if (isOpen) {
      setHasNewMessage(false);
      setTimeout(() => inputRef.current?.focus(), 300);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen]);

  // Scroll on new messages
  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]); // eslint-disable-line react-hooks/exhaustive-deps

  const loadHistory = async () => {
    setIsLoadingHistory(true);
    try {
      const res = await authFetch(`${API}/ai/coach/history`);
      if (res.ok) {
        const data = await res.json();
        if (data.messages?.length > 0) {
          setMessages(data.messages);
        }
      }
    } catch {
      // Silent fail
    } finally {
      setIsLoadingHistory(false);
    }
  };

  const sendMessage = async (text) => {
    const userMsg = (text || input).trim();
    if (!userMsg || isSending) return;

    const userMessage = { role: "user", content: userMsg, created_at: new Date().toISOString() };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsSending(true);

    try {
      const res = await authFetch(`${API}/ai/coach/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsg }),
      });
      if (!res.ok) throw new Error("Erreur");
      const data = await res.json();
      setMessages((prev) => [...prev, data]);
      if (!isOpen) setHasNewMessage(true);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Oups, petit souci technique. Réessaie dans un instant !",
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsSending(false);
    }
  };

  const clearHistory = async () => {
    try {
      await authFetch(`${API}/ai/coach/history`, { method: "DELETE" });
      setMessages([]);
    } catch {
      // Silent
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <>
      {/* Backdrop on mobile when open */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-background/60 backdrop-blur-sm z-40 lg:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Chat Panel */}
      <div
        ref={panelRef}
        className={`fixed z-50 transition-all duration-300 ease-out ${
          isOpen
            ? "opacity-100 translate-y-0 pointer-events-auto"
            : "opacity-0 translate-y-4 pointer-events-none"
        } ${
          // Mobile: bottom sheet style / Desktop: floating panel
          "bottom-0 right-0 left-0 lg:bottom-24 lg:right-6 lg:left-auto"
        }`}
      >
        <div className="lg:w-[380px] h-[70vh] lg:h-[520px] bg-card border border-border/50 lg:rounded-2xl rounded-t-2xl shadow-2xl flex flex-col overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-border/50 bg-card/90 backdrop-blur-sm">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center ring-1 ring-primary/10">
                <Brain className="w-4 h-4 text-primary" />
              </div>
              <div>
                <h3 className="font-heading font-semibold text-sm">Coach IA</h3>
                <div className="flex items-center gap-1">
                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  <span className="text-[10px] text-muted-foreground">En ligne</span>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-1">
              {messages.length > 0 && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7 text-muted-foreground hover:text-destructive"
                  onClick={clearHistory}
                  title="Effacer l'historique"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </Button>
              )}
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7 text-muted-foreground hover:text-foreground"
                onClick={() => setIsOpen(false)}
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
          </div>

          {/* Messages area */}
          <div className="flex-1 overflow-y-auto px-4 py-4 space-y-1">
            {isLoadingHistory ? (
              <div className="flex items-center justify-center h-full">
                <div className="flex items-center gap-2 text-muted-foreground">
                  <div className="w-2 h-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: "0ms" }} />
                  <div className="w-2 h-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: "150ms" }} />
                  <div className="w-2 h-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
              </div>
            ) : messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center px-4">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center mb-4 ring-1 ring-primary/10">
                  <Brain className="w-8 h-8 text-primary" />
                </div>
                <h4 className="font-heading font-semibold text-base mb-1">Ton coach personnel</h4>
                <p className="text-sm text-muted-foreground mb-6 leading-relaxed">
                  Pose-moi une question, demande un conseil, ou dis-moi comment tu te sens.
                </p>
                <div className="flex flex-col gap-2 w-full">
                  {QUICK_REPLIES.map((qr) => (
                    <button
                      key={qr.label}
                      onClick={() => sendMessage(qr.message)}
                      disabled={isSending}
                      className="w-full text-left px-3.5 py-2.5 rounded-xl border border-border/50 bg-muted/30 hover:bg-primary/5 hover:border-primary/20 transition-colors text-sm text-foreground"
                    >
                      <span className="text-primary mr-1.5">
                        <Sparkles className="w-3 h-3 inline-block" />
                      </span>
                      {qr.label}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <>
                {messages.map((msg, i) => (
                  <CoachMessage key={i} msg={msg} />
                ))}
                {isSending && (
                  <div className="flex justify-start mb-3">
                    <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center shrink-0 mr-2 mt-1 ring-1 ring-primary/10">
                      <Brain className="w-3.5 h-3.5 text-primary" />
                    </div>
                    <div className="bg-muted/50 border border-border/50 rounded-2xl rounded-bl-md px-4 py-3">
                      <div className="flex items-center gap-1.5">
                        <div className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce" style={{ animationDelay: "0ms" }} />
                        <div className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce" style={{ animationDelay: "150ms" }} />
                        <div className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce" style={{ animationDelay: "300ms" }} />
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </>
            )}
          </div>

          {/* Quick replies when conversation exists */}
          {messages.length > 0 && !isSending && (
            <div className="px-4 pb-2 flex gap-1.5 overflow-x-auto scrollbar-hide">
              {QUICK_REPLIES.map((qr) => (
                <button
                  key={qr.label}
                  onClick={() => sendMessage(qr.message)}
                  className="shrink-0 px-2.5 py-1 rounded-full border border-border/50 bg-muted/30 hover:bg-primary/5 hover:border-primary/20 transition-colors text-xs text-muted-foreground hover:text-foreground"
                >
                  {qr.label}
                </button>
              ))}
            </div>
          )}

          {/* Listening indicator */}
          {voiceListening && (
            <div className="px-3 py-1.5 border-t border-red-500/10 bg-red-500/5 flex items-center gap-2">
              <div className="flex items-center gap-0.5">
                <span className="w-0.5 h-2 bg-red-500/60 rounded-full animate-pulse" style={{ animationDelay: "0ms" }} />
                <span className="w-0.5 h-3 bg-red-500/80 rounded-full animate-pulse" style={{ animationDelay: "150ms" }} />
                <span className="w-0.5 h-1.5 bg-red-500/50 rounded-full animate-pulse" style={{ animationDelay: "300ms" }} />
                <span className="w-0.5 h-2.5 bg-red-500/70 rounded-full animate-pulse" style={{ animationDelay: "100ms" }} />
              </div>
              <span className="text-[11px] text-red-500/80 font-medium">Écoute en cours...</span>
            </div>
          )}

          {/* Input area */}
          <div className={`px-3 py-3 border-t bg-card/90 ${voiceListening ? "border-red-500/20" : "border-border/50"}`}>
            <div className="flex items-end gap-2">
              <div className="flex-1 relative">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Écris au coach..."
                  rows={1}
                  maxLength={500}
                  className={`w-full resize-none rounded-xl border bg-muted/30 px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/30 placeholder:text-muted-foreground/50 max-h-24 transition-colors ${
                    voiceListening ? "border-red-500/30" : "border-border/50"
                  }`}
                  style={{ minHeight: "40px" }}
                />
              </div>
              <VoiceInput
                variant="icon"
                textValue={input}
                onTextChange={setInput}
                onListeningChange={setVoiceListening}
                disabled={isSending}
              />
              <Button
                size="icon"
                className="h-10 w-10 rounded-xl shrink-0"
                onClick={() => sendMessage()}
                disabled={!input.trim() || isSending}
              >
                <Send className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* FAB Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`fixed z-50 bottom-6 right-6 w-14 h-14 rounded-2xl shadow-lg flex items-center justify-center transition-all duration-300 ${
          isOpen
            ? "bg-muted text-muted-foreground rotate-0 scale-90"
            : "bg-primary text-primary-foreground hover:shadow-xl hover:scale-105 active:scale-95"
        }`}
      >
        {isOpen ? (
          <ArrowDown className="w-5 h-5" />
        ) : (
          <>
            <MessageCircle className="w-6 h-6" />
            {hasNewMessage && (
              <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-rose-500 border-2 border-background animate-pulse" />
            )}
          </>
        )}
      </button>
    </>
  );
}
