import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Loader2 } from "lucide-react";
import { API, authFetch } from "@/App";

/**
 * ReactionsDetailDialog — Shows who reacted to an activity.
 * Pattern: Instagram reaction list (tabs per type, user list with avatars).
 *
 * Props:
 *   open — boolean
 *   onOpenChange — function
 *   activityId — string
 *   reactionCounts — { bravo: number, inspire: number, fire: number }
 */

const REACTION_TABS = [
  { key: "all", label: "Tous", emoji: null },
  { key: "bravo", label: "Bravo", emoji: "👏" },
  { key: "inspire", label: "Inspirant", emoji: "💡" },
  { key: "fire", label: "En feu", emoji: "🔥" },
  { key: "solidaire", label: "Solidaire", emoji: "🤝" },
  { key: "curieux", label: "Curieux", emoji: "🧠" },
];

const REACTION_EMOJI = {
  bravo: "👏",
  inspire: "💡",
  fire: "🔥",
  solidaire: "🤝",
  curieux: "🧠",
};

function getInitials(name) {
  if (!name) return "U";
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

export default function ReactionsDetailDialog({
  open,
  onOpenChange,
  activityId,
  reactionCounts,
}) {
  const [reactions, setReactions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("all");

  useEffect(() => {
    if (!open || !activityId) return;
    setLoading(true);
    setActiveTab("all");

    authFetch(`${API}/activities/${activityId}/reactions`)
      .then(async (res) => {
        if (res.ok) {
          const data = await res.json();
          setReactions(data.reactions || []);
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [open, activityId]);

  const totalCount = Object.values(reactionCounts || {}).reduce(
    (a, b) => a + b,
    0
  );

  const filtered =
    activeTab === "all"
      ? reactions
      : reactions.filter((r) => r.reaction_type === activeTab);

  // Only show tabs that have reactions
  const visibleTabs = REACTION_TABS.filter(
    (tab) =>
      tab.key === "all" || (reactionCounts?.[tab.key] || 0) > 0
  );

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-sm max-h-[70vh] bg-card border-border p-0 overflow-hidden">
        <DialogHeader className="px-5 pt-5 pb-0">
          <DialogTitle className="font-sans font-semibold tracking-tight text-base">
            Réactions
            {totalCount > 0 && (
              <span className="text-muted-foreground font-normal ml-1.5 text-sm">
                {totalCount}
              </span>
            )}
          </DialogTitle>
        </DialogHeader>

        {/* Tabs */}
        {visibleTabs.length > 1 && (
          <div className="flex gap-1 px-5 pt-3 pb-1 border-b border-border/50">
            {visibleTabs.map((tab) => {
              const count =
                tab.key === "all"
                  ? totalCount
                  : reactionCounts?.[tab.key] || 0;
              const isActive = activeTab === tab.key;
              return (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-200 ${
                    isActive
                      ? "bg-primary/10 text-primary"
                      : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
                  }`}
                >
                  {tab.emoji && <span className="text-sm">{tab.emoji}</span>}
                  {!tab.emoji && tab.label}
                  {tab.emoji && (
                    <span className="tabular-nums">{count}</span>
                  )}
                  {!tab.emoji && (
                    <span className="tabular-nums ml-0.5">{count}</span>
                  )}
                </button>
              );
            })}
          </div>
        )}

        {/* User list */}
        <div className="overflow-y-auto max-h-[50vh] px-2 pb-4">
          {loading ? (
            <div className="flex items-center justify-center py-10">
              <Loader2 className="w-5 h-5 text-primary animate-spin" />
            </div>
          ) : filtered.length === 0 ? (
            <div className="flex items-center justify-center py-10 text-sm text-muted-foreground">
              Aucune réaction
            </div>
          ) : (
            <div className="space-y-0.5 pt-2">
              {filtered.map((r) => (
                <Link
                  key={`${r.user_id}-${r.reaction_type}`}
                  to={`/users/${r.user_id}`}
                  onClick={() => onOpenChange(false)}
                  className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-muted/50 transition-colors"
                >
                  <Avatar className="w-9 h-9 shrink-0">
                    <AvatarImage src={r.avatar_url} />
                    <AvatarFallback className="text-[11px] bg-primary/10">
                      {getInitials(r.display_name)}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">
                      {r.display_name}
                    </p>
                    {r.username && (
                      <p className="text-[11px] text-muted-foreground truncate">
                        @{r.username}
                      </p>
                    )}
                  </div>
                  <span className="text-base shrink-0" title={r.reaction_type}>
                    {REACTION_EMOJI[r.reaction_type] || "\ud83d\udc4f"}
                  </span>
                </Link>
              ))}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
