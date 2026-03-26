/**
 * MentionText — Render @username mentions and #hashtags as clickable links.
 *
 * - Sanitizes content first (DOMPurify, strips ALL HTML).
 * - @mentions: only usernames in the `mentions` array become profile links.
 * - #hashtags: all #tag patterns become links to /hashtags/:tag.
 * - Self-mentions get a subtle highlight.
 * - Unknown @text renders as plain text (safe fallback).
 * - `variant="light"` (default): teal links on light backgrounds.
 * - `variant="dark"`: white/bold links on teal/dark backgrounds.
 *
 * Benchmarked: Instagram (mentions + hashtags), Twitter (clickable entities).
 */

import React from "react";
import { Link } from "react-router-dom";
import { sanitize } from "@/lib/sanitize";

// Matches @username (3-20 word chars) or #hashtag (2-30 word chars + accents)
const TOKEN_RE = /(@\w{3,20}|#[\w\u00C0-\u024F]{2,30})/g;

export default function MentionText({
  content,
  mentions = [],
  currentUserId,
  className,
  variant = "light",
}) {
  if (!content) return null;

  const clean = sanitize(content);
  if (!clean) return null;

  // No tokens to resolve — fast path
  const hasTokens = /@\w{3,20}|#[\w\u00C0-\u024F]{2,30}/.test(clean);
  if (!hasTokens && !mentions.length) {
    return <span className={className}>{clean}</span>;
  }

  const mentionMap = new Map(mentions.map((m) => [m.username, m.user_id]));

  // Split on @username and #hashtag tokens, keeping delimiters
  const parts = clean.split(TOKEN_RE);

  return (
    <span className={className}>
      {parts.map((part, i) => {
        // ── @mention ──
        if (part.startsWith("@")) {
          const username = part.slice(1);
          const userId = mentionMap.get(username);

          if (userId) {
            const isSelf = userId === currentUserId;

            if (variant === "dark") {
              return (
                <Link
                  key={i}
                  to={`/users/${userId}`}
                  className={`font-semibold underline decoration-white/40 underline-offset-2 transition-colors hover:decoration-white/80 ${
                    isSelf ? "bg-white/15 rounded px-0.5" : ""
                  }`}
                  onClick={(e) => e.stopPropagation()}
                >
                  @{username}
                </Link>
              );
            }

            return (
              <Link
                key={i}
                to={`/users/${userId}`}
                className={`font-semibold transition-colors ${
                  isSelf
                    ? "text-[#275255] bg-[#459492]/10 rounded px-0.5"
                    : "text-[#275255] hover:text-[#459492] hover:underline"
                }`}
                onClick={(e) => e.stopPropagation()}
              >
                @{username}
              </Link>
            );
          }
        }

        // ── #hashtag ──
        if (part.startsWith("#")) {
          const tag = part.slice(1);

          if (variant === "dark") {
            return (
              <Link
                key={i}
                to={`/hashtags/${encodeURIComponent(tag.toLowerCase())}`}
                className="font-semibold underline decoration-white/40 underline-offset-2 transition-colors hover:decoration-white/80"
                onClick={(e) => e.stopPropagation()}
              >
                #{tag}
              </Link>
            );
          }

          return (
            <Link
              key={i}
              to={`/hashtags/${encodeURIComponent(tag.toLowerCase())}`}
              className="font-semibold text-[#459492] hover:text-[#275255] hover:underline transition-colors"
              onClick={(e) => e.stopPropagation()}
            >
              #{tag}
            </Link>
          );
        }

        return <React.Fragment key={i}>{part}</React.Fragment>;
      })}
    </span>
  );
}
