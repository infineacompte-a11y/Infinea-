import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { UserPlus, UserCheck, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { API, authFetch } from "@/App";

/**
 * FollowButton — Follow/Unfollow toggle.
 * Pattern: Instagram follow button (instant toggle, optimistic UI).
 *
 * Props:
 * - userId: string — target user ID
 * - initialFollowing: boolean — whether the current user already follows this user
 * - onToggle?: (isFollowing: boolean) => void — callback after toggle
 * - size?: "sm" | "default" — button size
 */
export default function FollowButton({ userId, initialFollowing = false, onToggle, size = "default" }) {
  const [isFollowing, setIsFollowing] = useState(initialFollowing);
  const [isLoading, setIsLoading] = useState(false);

  const handleToggle = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (isLoading) return;

    const wasFollowing = isFollowing;
    // Optimistic update
    setIsFollowing(!wasFollowing);
    setIsLoading(true);

    try {
      const res = await authFetch(`${API}/users/${userId}/follow`, {
        method: wasFollowing ? "DELETE" : "POST",
      });

      if (!res.ok) {
        // Revert on error
        setIsFollowing(wasFollowing);
        const data = await res.json().catch(() => ({}));
        toast.error(data.detail || "Erreur réseau");
        return;
      }

      onToggle?.(!wasFollowing);
    } catch {
      setIsFollowing(wasFollowing);
      toast.error("Erreur de connexion");
    } finally {
      setIsLoading(false);
    }
  };

  const isSmall = size === "sm";

  if (isFollowing) {
    return (
      <Button
        variant="outline"
        size={isSmall ? "sm" : "default"}
        onClick={handleToggle}
        disabled={isLoading}
        className="gap-1.5 rounded-xl border-[#459492]/30 text-[#459492] hover:text-[#E48C75] hover:border-[#E48C75]/30 hover:bg-[#E48C75]/5 transition-all duration-200"
      >
        {isLoading ? (
          <Loader2 className={`${isSmall ? "w-3.5 h-3.5" : "w-4 h-4"} animate-spin`} />
        ) : (
          <UserCheck className={isSmall ? "w-3.5 h-3.5" : "w-4 h-4"} />
        )}
        <span className={isSmall ? "text-xs" : "text-sm"}>Suivi</span>
      </Button>
    );
  }

  return (
    <Button
      size={isSmall ? "sm" : "default"}
      onClick={handleToggle}
      disabled={isLoading}
      className="gap-1.5 rounded-xl bg-gradient-to-r from-[#459492] to-[#55B3AE] hover:from-[#275255] hover:to-[#459492] text-white border-0 shadow-md hover:shadow-lg transition-all duration-200 btn-press"
    >
      {isLoading ? (
        <Loader2 className={`${isSmall ? "w-3.5 h-3.5" : "w-4 h-4"} animate-spin`} />
      ) : (
        <UserPlus className={isSmall ? "w-3.5 h-3.5" : "w-4 h-4"} />
      )}
      <span className={isSmall ? "text-xs" : "text-sm"}>Suivre</span>
    </Button>
  );
}
