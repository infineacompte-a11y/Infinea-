/**
 * MentionInput — Input with @mention autocomplete.
 *
 * UX goals (best-in-class):
 * - Instant suggestions after typing @ (pre-warm on focus).
 * - Context-aware ranking (activity owner > mutuals > follows).
 * - Keyboard navigation (arrows, Enter, Tab, Escape).
 * - 150ms debounce + in-memory cache → near-zero latency.
 * - onMouseDown to prevent focus loss on click.
 * - Dropdown opens upward (comment inputs are at bottom of cards).
 *
 * Benchmarked: Slack (speed), Discord (highlight), Twitter (simplicity).
 */

import React, { useState, useEffect, useRef, useCallback } from "react";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Loader2, UserCheck } from "lucide-react";
import { API, authFetch } from "@/App";

function getInitials(name) {
  if (!name) return "U";
  return name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2);
}

export default function MentionInput({
  value,
  onChange,
  mentions = [],
  onMentionsChange,
  context = "comment",
  contextId = "",
  placeholder,
  maxLength,
  className,
  autoFocus,
  onSubmit,
  disabled,
}) {
  const [showDropdown, setShowDropdown] = useState(false);
  const [results, setResults] = useState([]);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [loading, setLoading] = useState(false);
  const [mentionStartIdx, setMentionStartIdx] = useState(-1);

  const inputRef = useRef(null);
  const cacheRef = useRef(new Map());
  const debounceRef = useRef(null);
  const wrapperRef = useRef(null);

  // ── Pre-warm: fetch suggestions on focus (empty query) ──
  const fetchResults = useCallback(
    async (query) => {
      const cacheKey = `${context}:${contextId}:${query}`;
      if (cacheRef.current.has(cacheKey)) {
        setResults(cacheRef.current.get(cacheKey));
        setLoading(false);
        return;
      }
      setLoading(true);
      try {
        const params = new URLSearchParams({
          q: query,
          context,
          context_id: contextId,
          limit: "6",
        });
        const res = await authFetch(`${API}/users/search-mention?${params}`);
        if (res.ok) {
          const data = await res.json();
          const users = data.users || [];
          cacheRef.current.set(cacheKey, users);
          setResults(users);
        }
      } catch {
        /* silent */
      }
      setLoading(false);
    },
    [context, contextId],
  );

  const handleFocus = useCallback(() => {
    const cacheKey = `${context}:${contextId}:`;
    if (!cacheRef.current.has(cacheKey)) {
      fetchResults("");
    }
  }, [context, contextId, fetchResults]);

  // ── Detect @ mention pattern ──
  const detectMention = useCallback((text, cursorPos) => {
    let i = cursorPos - 1;
    // Scan backward past word chars
    while (i >= 0 && /\w/.test(text[i])) i--;

    if (i >= 0 && text[i] === "@") {
      // @ must be preceded by whitespace or be at start
      if (i === 0 || /\s/.test(text[i - 1])) {
        return { active: true, query: text.substring(i + 1, cursorPos), startIndex: i };
      }
    }
    return { active: false, query: "", startIndex: -1 };
  }, []);

  // ── Handle text input ──
  const handleChange = useCallback(
    (e) => {
      const newText = e.target.value;
      onChange(newText);

      // Prune orphaned mentions
      if (onMentionsChange && mentions.length > 0) {
        const stillPresent = mentions.filter((m) => {
          const pattern = new RegExp(`(?<![\\w])@${m.username}(?![\\w])`);
          return pattern.test(newText);
        });
        if (stillPresent.length !== mentions.length) {
          onMentionsChange(stillPresent);
        }
      }

      // Detect mention
      const cursorPos = e.target.selectionStart;
      const detection = detectMention(newText, cursorPos);

      if (detection.active) {
        setMentionStartIdx(detection.startIndex);
        setSelectedIndex(0);
        setShowDropdown(true);

        // Debounced fetch
        clearTimeout(debounceRef.current);
        debounceRef.current = setTimeout(() => {
          fetchResults(detection.query);
        }, 150);
      } else {
        setShowDropdown(false);
      }
    },
    [onChange, onMentionsChange, mentions, detectMention, fetchResults],
  );

  // ── Select a mention from dropdown ──
  const handleSelectMention = useCallback(
    (user) => {
      const before = value.substring(0, mentionStartIdx);
      const cursorPos = inputRef.current?.selectionStart || value.length;
      const after = value.substring(cursorPos);
      const newText = `${before}@${user.username} ${after}`;
      onChange(newText);

      // Add to mentions array
      if (onMentionsChange && !mentions.find((m) => m.user_id === user.user_id)) {
        onMentionsChange([...mentions, { user_id: user.user_id, username: user.username }]);
      }

      setShowDropdown(false);
      setResults([]);

      // Restore cursor after @username + space
      requestAnimationFrame(() => {
        if (inputRef.current) {
          const newPos = mentionStartIdx + user.username.length + 2;
          inputRef.current.setSelectionRange(newPos, newPos);
          inputRef.current.focus();
        }
      });
    },
    [value, mentionStartIdx, onChange, onMentionsChange, mentions],
  );

  // ── Keyboard navigation ──
  const handleKeyDown = useCallback(
    (e) => {
      if (!showDropdown || results.length === 0) {
        if (e.key === "Enter" && onSubmit) {
          e.preventDefault();
          onSubmit();
        }
        return;
      }

      switch (e.key) {
        case "ArrowDown":
          e.preventDefault();
          setSelectedIndex((prev) => (prev + 1) % results.length);
          break;
        case "ArrowUp":
          e.preventDefault();
          setSelectedIndex((prev) => (prev - 1 + results.length) % results.length);
          break;
        case "Enter":
        case "Tab":
          e.preventDefault();
          handleSelectMention(results[selectedIndex]);
          break;
        case "Escape":
          e.preventDefault();
          setShowDropdown(false);
          break;
        default:
          break;
      }
    },
    [showDropdown, results, selectedIndex, onSubmit, handleSelectMention],
  );

  // ── Close dropdown on outside click ──
  useEffect(() => {
    const handler = (e) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  // ── Cleanup debounce on unmount ──
  useEffect(() => {
    return () => clearTimeout(debounceRef.current);
  }, []);

  return (
    <div ref={wrapperRef} className="relative w-full">
      <Input
        ref={inputRef}
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        onFocus={handleFocus}
        placeholder={placeholder}
        maxLength={maxLength}
        autoFocus={autoFocus}
        disabled={disabled}
        className={className}
        autoComplete="off"
      />

      {/* Mention dropdown — opens upward */}
      {showDropdown && (results.length > 0 || loading) && (
        <div
          className="absolute left-0 right-0 bottom-full mb-1 z-50 bg-popover border border-border/50 rounded-xl shadow-lg overflow-hidden"
          style={{ maxHeight: 280 }}
        >
          {loading && results.length === 0 && (
            <div className="flex items-center justify-center py-3">
              <Loader2 className="w-3.5 h-3.5 animate-spin text-muted-foreground" />
            </div>
          )}

          {results.map((user, i) => (
            <button
              key={user.user_id}
              onMouseDown={(e) => {
                e.preventDefault();
                handleSelectMention(user);
              }}
              className={`w-full flex items-center gap-2.5 px-3 py-2 text-left transition-colors duration-100 ${
                i === selectedIndex
                  ? "bg-primary/8 text-foreground"
                  : "hover:bg-muted/50 text-foreground"
              }`}
            >
              <Avatar className="w-7 h-7 shrink-0">
                <AvatarImage src={user.avatar_url} alt={user.display_name} />
                <AvatarFallback className="bg-primary/10 text-primary text-[10px]">
                  {getInitials(user.display_name)}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5">
                  <span className="text-xs font-medium truncate">{user.display_name}</span>
                  {user.is_mutual && (
                    <span className="text-[9px] text-[#459492] bg-[#459492]/10 px-1 rounded font-medium">
                      mutuel
                    </span>
                  )}
                </div>
                {user.username && (
                  <span className="text-[11px] text-muted-foreground">@{user.username}</span>
                )}
              </div>
              {user.is_following && !user.is_mutual && (
                <UserCheck className="w-3 h-3 text-primary/50 shrink-0" />
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
