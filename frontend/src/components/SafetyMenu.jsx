import React, { useState } from "react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { MoreHorizontal, Flag, Ban, ShieldOff, EyeOff, Eye } from "lucide-react";
import { toast } from "sonner";
import { API, authFetch } from "@/App";
import ReportDialog from "@/components/ReportDialog";

/**
 * SafetyMenu — "..." dropdown with mute + block + report actions.
 *
 * Props:
 *   userId: string — the user to mute/block/report
 *   targetType: "user" | "activity" | "comment" | "group" | "message"
 *   targetId: string — the content ID to report
 *   isBlocked: boolean
 *   isMuted: boolean
 *   onBlockChange: (blocked: boolean) => void
 *   onMuteChange: (muted: boolean) => void
 *   size: "sm" | "default"
 */
export default function SafetyMenu({
  userId,
  targetType = "user",
  targetId,
  isBlocked = false,
  isMuted = false,
  onBlockChange,
  onMuteChange,
  size = "default",
}) {
  const [reportOpen, setReportOpen] = useState(false);
  const [blocking, setBlocking] = useState(false);
  const [muting, setMuting] = useState(false);

  const handleMute = async () => {
    setMuting(true);
    try {
      if (isMuted) {
        const res = await authFetch(`${API}/users/${userId}/mute`, { method: "DELETE" });
        if (res.ok) {
          onMuteChange?.(false);
          toast.success("Utilisateur démasqué");
        } else {
          const data = await res.json().catch(() => ({}));
          toast.error(data.detail || "Erreur");
        }
      } else {
        const res = await authFetch(`${API}/users/${userId}/mute`, { method: "POST" });
        if (res.ok) {
          onMuteChange?.(true);
          toast.success("Utilisateur masqué — ses publications n'apparaîtront plus dans votre feed");
        } else {
          const data = await res.json().catch(() => ({}));
          toast.error(data.detail || "Erreur");
        }
      }
    } catch {
      toast.error("Erreur de connexion");
    } finally {
      setMuting(false);
    }
  };

  const handleBlock = async () => {
    setBlocking(true);
    try {
      if (isBlocked) {
        const res = await authFetch(`${API}/users/${userId}/block`, {
          method: "DELETE",
        });
        if (res.ok) {
          onBlockChange?.(false);
          toast.success("Utilisateur débloqué");
        } else {
          const data = await res.json().catch(() => ({}));
          toast.error(data.detail || "Erreur");
        }
      } else {
        const res = await authFetch(`${API}/users/${userId}/block`, {
          method: "POST",
        });
        if (res.ok) {
          onBlockChange?.(true);
          toast.success("Utilisateur bloqué");
        } else {
          const data = await res.json().catch(() => ({}));
          toast.error(data.detail || "Erreur");
        }
      }
    } catch {
      toast.error("Erreur de connexion");
    } finally {
      setBlocking(false);
    }
  };

  const iconSize = size === "sm" ? "w-3.5 h-3.5" : "w-4 h-4";
  const btnSize = size === "sm" ? "w-7 h-7" : "w-8 h-8";

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button
            className={`${btnSize} flex items-center justify-center rounded-full text-muted-foreground hover:text-foreground hover:bg-muted/60 transition-all`}
          >
            <MoreHorizontal className={iconSize} />
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="min-w-[180px]">
          <DropdownMenuItem
            onClick={handleMute}
            disabled={muting}
            className="gap-2 text-sm"
          >
            {isMuted ? (
              <>
                <Eye className="w-4 h-4 text-muted-foreground" />
                Démasquer
              </>
            ) : (
              <>
                <EyeOff className="w-4 h-4 text-muted-foreground" />
                Masquer cet utilisateur
              </>
            )}
          </DropdownMenuItem>
          <DropdownMenuItem
            onClick={() => setReportOpen(true)}
            className="gap-2 text-sm"
          >
            <Flag className="w-4 h-4 text-destructive" />
            Signaler
          </DropdownMenuItem>
          <DropdownMenuItem
            onClick={handleBlock}
            disabled={blocking}
            className="gap-2 text-sm text-destructive focus:text-destructive"
          >
            {isBlocked ? (
              <>
                <ShieldOff className="w-4 h-4" />
                Débloquer
              </>
            ) : (
              <>
                <Ban className="w-4 h-4" />
                Bloquer cet utilisateur
              </>
            )}
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <ReportDialog
        open={reportOpen}
        onOpenChange={setReportOpen}
        targetType={targetType}
        targetId={targetId || userId}
      />
    </>
  );
}
