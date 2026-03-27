/**
 * PollDisplay — Interactive poll card for feed posts.
 *
 * Pattern: Twitter/LinkedIn polls.
 * - Before voting: clickable option buttons
 * - After voting: results bars with percentages + "Tu as voté" badge
 * - After expiry: results for everyone
 *
 * Props:
 *   poll: { question, options: [{text, votes}], total_votes, ends_at, my_vote? }
 *   activityId: string (for vote API call)
 *   onVote: (updatedPoll) => void (callback to update parent state)
 */

import { useState } from "react";
import { BarChart3, Check, Clock, Loader2 } from "lucide-react";
import { API, authFetch } from "@/App";
import { toast } from "sonner";

function timeRemaining(endsAt) {
  if (!endsAt) return "";
  const diff = new Date(endsAt).getTime() - Date.now();
  if (diff <= 0) return "Terminé";
  const hours = Math.floor(diff / 3600000);
  if (hours < 1) return `${Math.ceil(diff / 60000)} min restantes`;
  if (hours < 24) return `${hours}h restantes`;
  const days = Math.floor(hours / 24);
  return `${days}j restant${days > 1 ? "s" : ""}`;
}

export default function PollDisplay({ poll, activityId, onVote }) {
  const [voting, setVoting] = useState(false);

  if (!poll || !poll.options) return null;

  const hasVoted = poll.my_vote !== undefined && poll.my_vote !== null;
  const isExpired = poll.ends_at && new Date(poll.ends_at).getTime() < Date.now();
  const showResults = hasVoted || isExpired;
  const total = poll.total_votes || 0;

  const handleVote = async (optionIndex) => {
    if (voting || showResults) return;
    setVoting(true);
    try {
      const res = await authFetch(`${API}/activities/${activityId}/poll/vote`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ option_index: optionIndex }),
      });
      if (res.ok) {
        const data = await res.json();
        if (onVote) onVote(data.poll);
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || "Erreur");
      }
    } catch {
      toast.error("Erreur de connexion");
    } finally {
      setVoting(false);
    }
  };

  return (
    <div className="mt-3 space-y-2">
      {/* Question */}
      {poll.question && (
        <p className="text-sm font-semibold text-foreground">{poll.question}</p>
      )}

      {/* Options */}
      <div className="space-y-1.5">
        {poll.options.map((option, i) => {
          const pct = total > 0 ? Math.round((option.votes / total) * 100) : 0;
          const isMyVote = hasVoted && poll.my_vote === i;
          const isWinner = showResults && total > 0 &&
            option.votes === Math.max(...poll.options.map((o) => o.votes));

          if (showResults) {
            // Results view — animated bar
            return (
              <div key={i} className="relative">
                <div
                  className={`h-10 rounded-xl overflow-hidden transition-all duration-500 ${
                    isMyVote
                      ? "bg-[#459492]/10 ring-1 ring-[#459492]/30"
                      : "bg-muted/30"
                  }`}
                >
                  <div
                    className={`h-full rounded-xl transition-all duration-700 ease-out ${
                      isMyVote ? "bg-[#459492]/20" : "bg-muted/50"
                    }`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
                <div className="absolute inset-0 flex items-center px-3">
                  <div className="flex items-center gap-1.5 flex-1 min-w-0">
                    {isMyVote && <Check className="w-3.5 h-3.5 text-[#459492] shrink-0" />}
                    <span className={`text-sm truncate ${isWinner ? "font-semibold" : ""} ${isMyVote ? "text-[#459492]" : "text-foreground/80"}`}>
                      {option.text}
                    </span>
                  </div>
                  <span className={`text-sm font-semibold shrink-0 ml-2 ${isMyVote ? "text-[#459492]" : "text-foreground/60"}`}>
                    {pct}%
                  </span>
                </div>
              </div>
            );
          }

          // Voting view — clickable buttons
          return (
            <button
              key={i}
              onClick={() => handleVote(i)}
              disabled={voting}
              className="w-full h-10 rounded-xl border border-border/50 bg-card hover:border-[#459492]/40 hover:bg-[#459492]/5 text-sm font-medium text-foreground/80 hover:text-[#459492] transition-all duration-200 px-3 text-left disabled:opacity-50"
            >
              {voting ? (
                <Loader2 className="w-4 h-4 animate-spin inline" />
              ) : (
                option.text
              )}
            </button>
          );
        })}
      </div>

      {/* Footer: total votes + time remaining */}
      <div className="flex items-center gap-3 text-[11px] text-muted-foreground pt-0.5">
        <span className="flex items-center gap-1">
          <BarChart3 className="w-3 h-3" />
          {total} vote{total !== 1 ? "s" : ""}
        </span>
        <span className="flex items-center gap-1">
          <Clock className="w-3 h-3" />
          {timeRemaining(poll.ends_at)}
        </span>
      </div>
    </div>
  );
}
