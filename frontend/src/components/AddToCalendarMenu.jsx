import React from "react";
import { useTranslation } from "react-i18next";
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

// ─── Helpers (exported for reuse) ───────────────────────

const pad = (n) => String(n).padStart(2, "0");

/**
 * Build a Google Calendar "create event" URL.
 * @param {Object} opts
 * @param {string} opts.title - Event title
 * @param {string} [opts.description] - Event description
 * @param {number} [opts.durationMinutes=10] - Duration in minutes
 * @param {string} [opts.recurrence] - RRULE string (e.g. "RRULE:FREQ=DAILY")
 * @param {Date}   [opts.startDate] - Start date (defaults to tomorrow)
 * @param {string} [opts.startTime="09:00"] - Start time HH:MM
 */
export function buildGoogleCalendarUrl({
  title,
  description,
  durationMinutes = 10,
  recurrence,
  startDate,
  startTime = "09:00",
}) {
  const base = "https://calendar.google.com/calendar/render?action=TEMPLATE";
  const params = new URLSearchParams();
  params.set("text", title);
  if (description) params.set("details", description);

  const start = startDate || new Date(Date.now() + 86400000);
  const [startH, startM] = startTime.split(":").map(Number);
  const startMinTotal = startH * 60 + startM;
  const endMinTotal = startMinTotal + durationMinutes;

  const dateStr = `${start.getFullYear()}${pad(start.getMonth() + 1)}${pad(start.getDate())}`;
  const startStr = `${dateStr}T${pad(startH)}${pad(startM)}00`;
  const endStr = `${dateStr}T${pad(Math.floor(endMinTotal / 60))}${pad(endMinTotal % 60)}00`;
  params.set("dates", `${startStr}/${endStr}`);

  if (recurrence) params.set("recur", recurrence);

  return `${base}&${params.toString()}`;
}

/**
 * Build an RRULE string from a routine's frequency config.
 */
export function frequencyToRRule({ frequency = "daily", frequencyDays = [], untilDate }) {
  const DAY_MAP = { 0: "MO", 1: "TU", 2: "WE", 3: "TH", 4: "FR", 5: "SA", 6: "SU" };
  let rule;
  if (frequency === "weekdays") rule = "RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR";
  else if (frequency === "weekends") rule = "RRULE:FREQ=WEEKLY;BYDAY=SA,SU";
  else if (frequency === "custom" && frequencyDays.length > 0) {
    rule = `RRULE:FREQ=WEEKLY;BYDAY=${frequencyDays.map((d) => DAY_MAP[d]).join(",")}`;
  } else {
    rule = "RRULE:FREQ=DAILY";
  }
  if (untilDate) {
    const u = untilDate;
    rule += `;UNTIL=${u.getFullYear()}${pad(u.getMonth() + 1)}${pad(u.getDate())}T235959Z`;
  }
  return rule;
}

/**
 * Download a .ics file via authenticated fetch.
 * @param {string} endpoint - API path (e.g. "routines/abc123/ical")
 * @param {string} [filename="event.ics"] - Download filename
 * @param {Function} t - i18n translation function
 */
export async function downloadIcs(endpoint, filename = "event.ics", t) {
  try {
    const res = await authFetch(`${API}/${endpoint}`);
    if (!res.ok) throw new Error("Erreur");
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success(t ? t("components.addToCalendar.icsDownloaded") : "Fichier .ics téléchargé");
  } catch {
    toast.error(t ? t("components.addToCalendar.downloadError") : "Erreur lors du téléchargement");
  }
}

// ─── Google Calendar icon SVG ───────────────────────────
function GoogleCalIcon({ className = "w-4 h-4" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none">
      <path d="M18.316 5.684H24v12.632h-5.684V5.684z" fill="#1967D2"/>
      <path d="M5.684 24V18.316H0V24h5.684z" fill="#188038"/>
      <path d="M18.316 24V18.316H5.684V24h12.632z" fill="#34A853"/>
      <path d="M5.684 18.316V5.684H0v12.632h5.684z" fill="#4285F4"/>
      <path d="M18.316 5.684V0H5.684v5.684h12.632z" fill="#FBBC04"/>
      <path d="M24 5.684V0h-5.684v5.684H24z" fill="#EA4335"/>
    </svg>
  );
}

/**
 * AddToCalendarMenu — Generic, Eventbrite/Calendly-style dropdown.
 *
 * Usage (any page/component):
 *   <AddToCalendarMenu
 *     googleUrl={buildGoogleCalendarUrl({ title: "...", ... })}
 *     icalEndpoint="routines/abc123/ical"
 *     icalFilename="ma-routine.ics"
 *     className="opacity-0 group-hover:opacity-100"
 *   />
 *
 * Props:
 * @param {string} googleUrl - Pre-built Google Calendar URL
 * @param {string} [icalEndpoint] - Backend path for .ics download (optional — hides option if absent)
 * @param {string} [icalFilename="event.ics"] - Download filename
 * @param {string} [className] - Extra classes on the trigger button
 *
 * Convenience shorthand (for backward compat):
 * @param {"routine"|"objective"} [type] - Auto-builds googleUrl + icalEndpoint from item
 * @param {Object} [item] - The routine or objective object
 */
export default function AddToCalendarMenu({
  googleUrl: googleUrlProp,
  icalEndpoint: icalEndpointProp,
  icalFilename = "event.ics",
  className = "",
  // Convenience shorthand
  type,
  item,
}) {
  const { t } = useTranslation();

  // Resolve props: either explicit or built from type+item shorthand
  let googleUrl = googleUrlProp;
  let icalEndpoint = icalEndpointProp;

  if (!googleUrl && type && item) {
    if (type === "routine") {
      const items = item.items || [];
      const desc = items.length > 0
        ? `InFinea — ${items.map((it, i) => `${i + 1}. ${it.title}`).join(", ")}`
        : "Routine InFinea";
      const tod = item.time_of_day || "morning";
      const startTime = { morning: "08:00", afternoon: "13:00", evening: "19:00", anytime: "09:00" }[tod] || "09:00";
      googleUrl = buildGoogleCalendarUrl({
        title: item.name || "Routine InFinea",
        description: desc,
        durationMinutes: item.total_minutes || 15,
        recurrence: frequencyToRRule({ frequency: item.frequency, frequencyDays: item.frequency_days }),
        startTime,
      });
      icalEndpoint = icalEndpoint || `routines/${item.routine_id}/ical`;
      icalFilename = `routine-${(item.name || "infinea").slice(0, 20).replace(/\s+/g, "-")}.ics`;
    } else if (type === "objective") {
      const durationDays = item.target_duration_days || 30;
      googleUrl = buildGoogleCalendarUrl({
        title: item.title || "Objectif InFinea",
        description: `Parcours InFinea — ${item.daily_minutes || 10} min/jour`,
        durationMinutes: item.daily_minutes || 10,
        recurrence: frequencyToRRule({ untilDate: new Date(Date.now() + durationDays * 86400000) }),
      });
      icalEndpoint = icalEndpoint || `objectives/${item.objective_id}/ical`;
      icalFilename = `objectif-${(item.title || "infinea").slice(0, 20).replace(/\s+/g, "-")}.ics`;
    }
  }

  if (!googleUrl) return null; // Nothing to render without a URL

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          onClick={(e) => e.stopPropagation()}
          className={`p-1.5 rounded-lg hover:bg-muted/50 transition-colors ${className}`}
          title={t("components.addToCalendar.title")}
        >
          <CalendarPlus className="w-4 h-4 text-muted-foreground" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-52" onClick={(e) => e.stopPropagation()}>
        <DropdownMenuLabel className="text-[11px] text-muted-foreground font-normal">
          {t("components.addToCalendar.title")}
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          <a href={googleUrl} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 cursor-pointer">
            <GoogleCalIcon />
            <span>Google Calendar</span>
          </a>
        </DropdownMenuItem>
        {icalEndpoint && (
          <DropdownMenuItem
            onClick={() => downloadIcs(icalEndpoint, icalFilename, t)}
            className="flex items-center gap-2 cursor-pointer"
          >
            <Download className="w-4 h-4" />
            <span>{t("components.addToCalendar.appleOutlook")}</span>
          </DropdownMenuItem>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
