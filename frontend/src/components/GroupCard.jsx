import React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Users, Crown, Clock, TrendingUp, ChevronRight } from "lucide-react";
import { Link } from "react-router-dom";

/**
 * GroupCard — Summary card for a duo/group.
 * Pattern: Strava Club card + Duolingo League card.
 *
 * Props:
 *   group — group object from GET /api/groups
 */

const statusColors = {
  active: "bg-[#5DB786]/15 text-[#5DB786]",
  archived: "bg-muted text-muted-foreground",
};

function formatMinutes(min) {
  if (!min) return "0 min";
  if (min < 60) return `${min} min`;
  const h = Math.floor(min / 60);
  const m = min % 60;
  return m > 0 ? `${h}h${m.toString().padStart(2, "0")}` : `${h}h`;
}

export default function GroupCard({ group }) {
  if (!group) return null;

  const members = group.members?.filter((m) => m.status === "active") || [];
  const totalWeekMinutes = members.reduce((sum, m) => sum + (m.stats?.week_minutes || 0), 0);
  const totalWeekSessions = members.reduce((sum, m) => sum + (m.stats?.week_sessions || 0), 0);

  return (
    <Link to={`/groups/${group.group_id}`} className="block group/card">
      <Card className="bg-white shadow-sm border border-[#E2E6EA] hover:bg-card/80 hover:border-primary/30 hover:shadow-md transition-all duration-200">
        <CardContent className="p-5">
          {/* Header: name + member count */}
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1 min-w-0">
              <h3 className="text-foreground font-sans font-semibold tracking-tight font-semibold text-base truncate">
                {group.name}
              </h3>
              {group.description && (
                <p className="text-muted-foreground text-sm mt-0.5 truncate">
                  {group.description}
                </p>
              )}
            </div>
            <ChevronRight className="w-4 h-4 text-muted-foreground group-hover/card:text-primary transition-colors shrink-0 mt-1 ml-2" />
          </div>

          {/* Member avatars row */}
          <div className="flex items-center gap-2 mb-4">
            <div className="flex -space-x-2">
              {members.slice(0, 5).map((member, i) => (
                <div
                  key={member.user_id}
                  className="w-7 h-7 rounded-full border-2 border-card flex items-center justify-center text-[10px] font-bold"
                  style={{
                    background: `hsl(${(i * 67 + 200) % 360}, 60%, 45%)`,
                    zIndex: 5 - i,
                  }}
                  title={member.name}
                >
                  {member.role === "owner" ? (
                    <Crown className="w-3 h-3 text-white" />
                  ) : (
                    <span className="text-white">{(member.name || "?")[0].toUpperCase()}</span>
                  )}
                </div>
              ))}
              {members.length > 5 && (
                <div className="w-7 h-7 rounded-full border-2 border-card bg-muted flex items-center justify-center text-[10px] text-muted-foreground font-medium">
                  +{members.length - 5}
                </div>
              )}
            </div>
            <span className="text-muted-foreground text-xs">
              {members.length} membre{members.length > 1 ? "s" : ""}
            </span>
          </div>

          {/* Week stats */}
          <div className="grid grid-cols-2 gap-3">
            <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-muted/30">
              <Clock className="w-3.5 h-3.5 text-[#459492] shrink-0" />
              <div>
                <div className="text-foreground text-sm font-semibold tabular-nums">
                  {formatMinutes(totalWeekMinutes)}
                </div>
                <div className="text-muted-foreground text-[10px]">cette semaine</div>
              </div>
            </div>
            <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-muted/30">
              <TrendingUp className="w-3.5 h-3.5 text-[#5DB786] shrink-0" />
              <div>
                <div className="text-foreground text-sm font-semibold tabular-nums">
                  {totalWeekSessions}
                </div>
                <div className="text-muted-foreground text-[10px]">sessions</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
