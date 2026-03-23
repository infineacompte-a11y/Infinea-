import React from "react";
import { Link } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Crown, Flame } from "lucide-react";
import FollowButton from "@/components/FollowButton";

/**
 * UserCard — Compact user preview card for search results and suggestions.
 * Pattern: Instagram user suggestion card + Strava athlete summary.
 *
 * Props:
 * - user: { user_id, name, picture?, bio?, subscription_tier?, streak_days?, is_following? }
 * - showFollow?: boolean — show follow/unfollow button (default true)
 * - currentUserId?: string — to hide follow button on own card
 */
export default function UserCard({ user, showFollow = true, currentUserId }) {
  const getInitials = (name) => {
    if (!name) return "U";
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  const isOwnCard = currentUserId && currentUserId === user.user_id;

  return (
    <Card className="hover:border-[#459492]/20 hover:shadow-md hover:-translate-y-0.5 transition-all duration-300">
      <CardContent className="p-4">
        <div className="flex items-center gap-3">
          <Link to={`/users/${user.user_id}`} className="shrink-0">
            <Avatar className="w-12 h-12 ring-2 ring-[#459492]/10 ring-offset-1 ring-offset-background">
              <AvatarImage src={user.picture} alt={user.name} />
              <AvatarFallback className="bg-primary/10 text-primary text-sm font-medium">
                {getInitials(user.name)}
              </AvatarFallback>
            </Avatar>
          </Link>

          <div className="flex-1 min-w-0">
            <Link to={`/users/${user.user_id}`} className="hover:underline">
              <div className="flex items-center gap-2">
                <span className="font-medium text-sm text-foreground truncate">
                  {user.name}
                </span>
                {user.subscription_tier === "premium" && (
                  <Crown className="w-3.5 h-3.5 text-[#E48C75] shrink-0" />
                )}
              </div>
            </Link>
            {user.username ? (
              <p className="text-xs text-muted-foreground truncate mt-0.5">
                @{user.username}
              </p>
            ) : user.bio ? (
              <p className="text-xs text-muted-foreground truncate mt-0.5">
                {user.bio}
              </p>
            ) : user.streak_days > 0 ? (
              <div className="flex items-center gap-1 mt-0.5">
                <Flame className="w-3 h-3 text-[#E48C75]" />
                <span className="text-xs text-muted-foreground">
                  {user.streak_days}j de streak
                </span>
              </div>
            ) : null}
          </div>

          {showFollow && !isOwnCard && (
            <div className="shrink-0">
              <FollowButton
                userId={user.user_id}
                initialFollowing={user.is_following || false}
                size="sm"
              />
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
