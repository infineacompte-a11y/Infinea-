/**
 * LinkPreviewCard — Rich OG card for URLs shared in posts.
 *
 * Pattern: Slack / Discord / iMessage / WhatsApp link previews.
 * Shows title, description, image, and domain in a compact card.
 *
 * Props:
 *   preview: { url, title, description, image, site_name, domain }
 */

import { ExternalLink } from "lucide-react";

export default function LinkPreviewCard({ preview }) {
  if (!preview || !preview.title) return null;

  return (
    <a
      href={preview.url}
      target="_blank"
      rel="noopener noreferrer"
      className="block mt-2 rounded-xl border border-border/50 bg-card hover:border-[#459492]/30 hover:shadow-sm transition-all duration-200 overflow-hidden group"
    >
      {preview.image && (
        <div className="w-full h-[160px] overflow-hidden bg-muted">
          <img
            src={preview.image}
            alt=""
            className="w-full h-full object-cover group-hover:scale-[1.02] transition-transform duration-300"
            loading="lazy"
            onError={(e) => { e.target.style.display = "none"; }}
          />
        </div>
      )}
      <div className="px-3 py-2.5">
        <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground mb-1">
          <ExternalLink className="w-3 h-3 shrink-0" />
          <span className="truncate">{preview.site_name || preview.domain}</span>
        </div>
        <h4 className="text-sm font-semibold text-foreground leading-snug line-clamp-2 group-hover:text-[#459492] transition-colors">
          {preview.title}
        </h4>
        {preview.description && (
          <p className="text-xs text-muted-foreground line-clamp-2 mt-0.5 leading-relaxed">
            {preview.description}
          </p>
        )}
      </div>
    </a>
  );
}
