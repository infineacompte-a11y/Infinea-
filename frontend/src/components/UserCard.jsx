import React from "react";
import { Link } from "react-router-dom";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { UserPlus, UserMinus, Loader2 } from "lucide-react";

function getInitials(name) {
  if (!name) return "U";
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

/**
 * Reusable user card — used in search results, follower lists, etc.
 *
 * Props:
 *   user: { user_id, display_name, avatar_url }
 *   isFollowing: boolean (optional)
 *   onFollow: () => void (optional)
 *   onUnfollow: () => void (optional)
 *   loading: boolean (optional — follow action in progress)
 *   subtitle: string (optional — shown below the name)
 */
export default function UserCard({
  user,
  isFollowing,
  onFollow,
  onUnfollow,
  loading = false,
  subtitle,
}) {
  return (
    <div className="flex items-center gap-4 p-4 rounded-xl hover:bg-white/5 transition-colors">
      <Link to={`/users/${user.user_id}`} className="flex items-center gap-4 flex-1 min-w-0">
        <Avatar className="w-12 h-12 shrink-0">
          <AvatarImage src={user.avatar_url} alt={user.display_name} />
          <AvatarFallback className="bg-primary/10 text-primary text-sm">
            {getInitials(user.display_name)}
          </AvatarFallback>
        </Avatar>
        <div className="min-w-0">
          <p className="font-medium truncate">{user.display_name}</p>
          {subtitle && (
            <p className="text-sm text-muted-foreground truncate">{subtitle}</p>
          )}
        </div>
      </Link>

      {(onFollow || onUnfollow) && (
        <Button
          variant={isFollowing ? "outline" : "default"}
          size="sm"
          className="shrink-0 rounded-full"
          disabled={loading}
          onClick={(e) => {
            e.preventDefault();
            isFollowing ? onUnfollow?.() : onFollow?.();
          }}
        >
          {loading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : isFollowing ? (
            <>
              <UserMinus className="w-4 h-4 mr-1" />
              Suivi
            </>
          ) : (
            <>
              <UserPlus className="w-4 h-4 mr-1" />
              Suivre
            </>
          )}
        </Button>
      )}
    </div>
  );
}
