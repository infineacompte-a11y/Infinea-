import React from "react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import { CalendarPlus, Download } from "lucide-react";
import { API, authFetch } from "@/App";
import { toast } from "sonner";

// ─── Google Calendar URL builder ────────────────────────
function buildGoogleCalendarUrl({ title, description, durationMinutes, recurrence, startDate }) {
  const base = "https://calendar.google.com/calendar/render?action=TEMPLATE";
  const params = new URLSearchParams();
  params.set("text", title);
  if (description) params.set("details", description);

  // Start date: tomorrow at 09:00 by default
  const start = startDate || new Date(Date.now() + 86400000);
  const pad = (n) => String(n).padStart(2, "0");
  const startStr = `${start.getFullYear()}${pad(start.getMonth() + 1)}${pad(start.getDate())}T090000`;
  const endMin = 9 * 60 + (durationMinutes || 10);
  const endStr = `${start.getFullYear()}${pad(start.getMonth() + 1)}${pad(start.getDate())}T${pad(Math.floor(endMin / 60))}${pad(endMin % 60)}00`;
  params.set("dates", `${startStr}/${endStr}`);

  if (recurrence) params.set("recur", recurrence);

  return `${base}&${params.toString()}`;
}

// ─── .ics download via auth fetch ───────────────────────
async function downloadIcs(endpoint) {
  try {
    const res = await authFetch(`${API}/${endpoint}`);
    if (!res.ok) throw new Error("Erreur");
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = endpoint.includes("routine") ? "routine.ics" : "objectif.ics";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success("Fichier .ics téléchargé");
  } catch {
    toast.error("Erreur lors du téléchargement");
  }
}

// ─── Google Calendar recurrence string builder ──────────
function routineToRecurrence(routine) {
  const freq = routine.frequency || "daily";
  const days = routine.frequency_days || [];
  if (freq === "daily") return "RRULE:FREQ=DAILY";
  if (freq === "weekdays") return "RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR";
  if (freq === "weekends") return "RRULE:FREQ=WEEKLY;BYDAY=SA,SU";
  if (freq === "custom" && days.length > 0) {
    const map = { 0: "MO", 1: "TU", 2: "WE", 3: "TH", 4: "FR", 5: "SA", 6: "SU" };
    return `RRULE:FREQ=WEEKLY;BYDAY=${days.map((d) => map[d]).join(",")}`;
  }
  return "RRULE:FREQ=DAILY";
}

/**
 * AddToCalendarMenu — Eventbrite/Calendly-style dropdown
 *
 * Props:
 * - type: "routine" | "objective"
 * - item: the routine or objective object
 * - className: extra classes for the trigger button
 */
export default function AddToCalendarMenu({ type, item, className = "" }) {
  const isRoutine = type === "routine";
  const id = isRoutine ? item.routine_id : item.objective_id;
  const icalEndpoint = isRoutine ? `routines/${id}/ical` : `objectives/${id}/ical`;

  // Build Google Calendar link
  let googleUrl;
  if (isRoutine) {
    const items = item.items || [];
    const desc = items.length > 0
      ? `InFinea — ${items.map((it, i) => `${i + 1}. ${it.title}`).join(", ")}`
      : "Routine InFinea";
    googleUrl = buildGoogleCalendarUrl({
      title: item.name || "Routine InFinea",
      description: desc,
      durationMinutes: item.total_minutes || 15,
      recurrence: routineToRecurrence(item),
    });
  } else {
    const durationDays = item.target_duration_days || 30;
    const until = new Date(Date.now() + durationDays * 86400000);
    const pad = (n) => String(n).padStart(2, "0");
    const untilStr = `${until.getFullYear()}${pad(until.getMonth() + 1)}${pad(until.getDate())}T235959Z`;
    googleUrl = buildGoogleCalendarUrl({
      title: item.title || "Objectif InFinea",
      description: `Parcours InFinea — ${item.daily_minutes || 10} min/jour`,
      durationMinutes: item.daily_minutes || 10,
      recurrence: `RRULE:FREQ=DAILY;UNTIL=${untilStr}`,
    });
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          onClick={(e) => e.stopPropagation()}
          className={`p-1.5 rounded-lg hover:bg-muted/50 transition-colors ${className}`}
          title="Ajouter au calendrier"
        >
          <CalendarPlus className="w-4 h-4 text-muted-foreground" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-52" onClick={(e) => e.stopPropagation()}>
        <DropdownMenuLabel className="text-[11px] text-muted-foreground font-normal">
          Ajouter au calendrier
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          <a href={googleUrl} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 cursor-pointer">
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none">
              <path d="M18.316 5.684H24v12.632h-5.684V5.684z" fill="#1967D2"/>
              <path d="M5.684 24V18.316H0V24h5.684z" fill="#188038"/>
              <path d="M18.316 24V18.316H5.684V24h12.632z" fill="#34A853"/>
              <path d="M5.684 18.316V5.684H0v12.632h5.684z" fill="#4285F4"/>
              <path d="M18.316 5.684V0H5.684v5.684h12.632z" fill="#FBBC04"/>
              <path d="M24 5.684V0h-5.684v5.684H24z" fill="#EA4335"/>
              <path d="M18.316 18.316H24V5.684h-5.684v12.632z" fill="#1967D2" opacity=".2"/>
            </svg>
            <span>Google Calendar</span>
          </a>
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => downloadIcs(icalEndpoint)} className="flex items-center gap-2 cursor-pointer">
          <Download className="w-4 h-4" />
          <span>Apple / Outlook (.ics)</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
