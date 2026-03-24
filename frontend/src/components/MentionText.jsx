/**
 * MentionText — Render @username mentions as clickable teal links.
 *
 * - Sanitizes content first (DOMPurify, strips ALL HTML).
 * - Only usernames present in the `mentions` array become links.
 * - Self-mentions get a subtle teal highlight (Discord-style).
 * - Unknown @text renders as plain text (safe fallback).
 */

import React from "react";
import { Link } from "react-router-dom";
import { sanitize } from "@/lib/sanitize";

const MENTION_RE = /(@\w{3,20})/g;

export default function MentionText({ content, mentions = [], currentUserId, className }) {
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
            return (
              <Link
                key={i}
                to={`/users/${userId}`}
                className={`font-medium transition-colors ${
                  isSelf
                    ? "text-[#459492] bg-[#459492]/10 rounded px-0.5"
                    : "text-[#459492] hover:text-[#275255] hover:underline"
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
