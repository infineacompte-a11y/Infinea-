/**
 * MentionText — Render @username mentions as clickable links.
 *
 * - Sanitizes content first (DOMPurify, strips ALL HTML).
 * - Only usernames present in the `mentions` array become links.
 * - Self-mentions get a subtle highlight.
 * - Unknown @text renders as plain text (safe fallback).
 * - `variant="light"` (default): teal links on light backgrounds.
 * - `variant="dark"`: white/bold links on teal/dark backgrounds.
 */

import React from "react";
import { Link } from "react-router-dom";
import { sanitize } from "@/lib/sanitize";

const MENTION_RE = /(@\w{3,20})/g;

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

  // No mentions to resolve — fast path
  if (!mentions.length) {
    return <span className={className}>{clean}</span>;
  }

  const mentionMap = new Map(mentions.map((m) => [m.username, m.user_id]));

  // Split on @username tokens, keeping delimiters
  const parts = clean.split(MENTION_RE);

  return (
    <span className={className}>
      {parts.map((part, i) => {
        if (part.startsWith("@")) {
          const username = part.slice(1);
          const userId = mentionMap.get(username);

          if (userId) {
            const isSelf = userId === currentUserId;

            // Dark variant: for teal message bubbles — white text, underline
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

            // Light variant (default): teal links on light backgrounds
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
        return <React.Fragment key={i}>{part}</React.Fragment>;
      })}
    </span>
  );
}
