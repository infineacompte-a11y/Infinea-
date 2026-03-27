/**
 * OnlineIndicator — Reusable presence status component.
 *
 * Displays a colored dot (Discord-style) and/or a text label
 * indicating the user's online status.
 *
 * Supports two modes:
 * 1. From `presence` object (backend-computed): { status, label }
 * 2. From `lastActive` timestamp (client-computed, legacy compat)
 *
 * Benchmarked: Discord (green dot), Instagram (Active now), WhatsApp (online).
 */

// ── Presence computation (client-side, mirrors backend logic) ──
export function computePresence(lastActive) {
  if (!lastActive) return { status: "offline", label: null };
  const diff = Date.now() - new Date(lastActive).getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 5) return { status: "online", label: "En ligne" };
  if (minutes < 60) return { status: "recent", label: `Actif il y a ${minutes} min` };
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return { status: "away", label: `Actif il y a ${hours}h` };
  return { status: "offline", label: null };
}

// ── Dot colors by status ──
const DOT_COLORS = {
  online: "#22c55e",   // green-500
  recent: "#f59e0b",   // amber-500
  away: "#9ca3af",     // gray-400
  offline: null,       // no dot
};

/**
 * OnlineDot — Small colored dot overlay for avatars.
 *
 * Props:
 *   presence: { status, label } — from backend or computePresence()
 *   lastActive: string — ISO timestamp (fallback if no presence prop)
 *   size: "sm" | "md" | "lg" — dot size (default: "sm")
 *   className: string — additional CSS classes
 */
export function OnlineDot({ presence, lastActive, size = "sm", className = "" }) {
  const p = presence || computePresence(lastActive);
  const color = DOT_COLORS[p.status];
  if (!color) return null;

  const sizes = {
    sm: "w-2.5 h-2.5 ring-1.5",
    md: "w-3 h-3 ring-2",
    lg: "w-3.5 h-3.5 ring-2",
  };

  return (
    <span
      className={`absolute bottom-0 right-0 rounded-full ring-background ${sizes[size] || sizes.sm} ${className}`}
      style={{ backgroundColor: color }}
      aria-label={p.label || "Hors ligne"}
    />
  );
}

/**
 * OnlineLabel — Text label showing presence status.
 *
 * Props:
 *   presence: { status, label } — from backend or computePresence()
 *   lastActive: string — ISO timestamp (fallback if no presence prop)
 *   className: string — additional CSS classes
 */
export function OnlineLabel({ presence, lastActive, className = "" }) {
  const p = presence || computePresence(lastActive);
  if (!p.label) return null;

  const textColor = p.status === "online"
    ? "text-emerald-600"
    : p.status === "recent"
      ? "text-amber-600"
      : "text-muted-foreground";

  return (
    <span className={`text-[10px] ${textColor} ${className}`}>
      {p.status === "online" && (
        <span
          className="inline-block w-1.5 h-1.5 rounded-full mr-1 align-middle"
          style={{ backgroundColor: "#22c55e" }}
        />
      )}
      {p.label}
    </span>
  );
}
