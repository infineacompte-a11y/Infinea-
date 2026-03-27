import React, { useState, useRef, useCallback } from "react";
import { toPng } from "html-to-image";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import {
  Download,
  Link2,
  Share2,
  Loader2,
  Check,
  Image as ImageIcon,
} from "lucide-react";
import { toast } from "sonner";
import ShareCard from "@/components/ShareCard";
import { API, authFetch } from "@/App";

// ── Social share helpers — URL-based, no SDK ──
// Exported for reuse in other components (session debrief, level-up, etc.)
export function shareOnTwitter(url, text) {
  window.open(
    `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}`,
    "_blank",
    "noopener,noreferrer,width=600,height=400",
  );
}
export function shareOnLinkedIn(url) {
  window.open(
    `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}`,
    "_blank",
    "noopener,noreferrer,width=600,height=600",
  );
}
export function shareOnWhatsApp(url, text) {
  window.open(
    `https://wa.me/?text=${encodeURIComponent(text + " " + url)}`,
    "_blank",
    "noopener,noreferrer",
  );
}

// ── Inline SVG icons for social platforms (no extra deps) ──
function TwitterIcon({ className }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="currentColor">
      <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
    </svg>
  );
}
function LinkedInIcon({ className }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="currentColor">
      <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
    </svg>
  );
}
function WhatsAppIcon({ className }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="currentColor">
      <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
    </svg>
  );
}

/**
 * ShareDialog — Full share flow: create snapshot → preview card → export.
 * Pattern: Duolingo share modal + Strava activity export + Instagram share sheet.
 *
 * Props:
 *   open — boolean, dialog open state
 *   onOpenChange — function, dialog state setter
 *   shareType — "weekly_recap" | "milestone" | "badge" | "objective"
 *   objectiveId — optional, specific objective to highlight
 *   customText — optional, custom share text (for session/level-up shares)
 *   preloadedUrl — optional, pre-existing share URL (skip snapshot creation)
 */
export default function ShareDialog({ open, onOpenChange, shareType = "weekly_recap", objectiveId = null, customText = null, preloadedUrl = null }) {
  const [snapshot, setSnapshot] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [linkCopied, setLinkCopied] = useState(false);
  const [shareUrl, setShareUrl] = useState("");
  const cardRef = useRef(null);

  const shareText = customText || "Investis tes instants perdus avec InFinea";

  // Fetch snapshot when dialog opens
  const handleOpenChange = useCallback(async (isOpen) => {
    onOpenChange(isOpen);
    if (isOpen && !snapshot) {
      // If we have a preloaded URL, skip snapshot creation (used for quick shares)
      if (preloadedUrl) {
        setShareUrl(preloadedUrl);
        setIsLoading(false);
        return;
      }
      setIsLoading(true);
      try {
        const res = await authFetch(`${API}/share/create`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            share_type: shareType,
            ...(objectiveId && { objective_id: objectiveId }),
          }),
        });
        if (!res.ok) throw new Error("Erreur lors de la création du partage");
        const data = await res.json();
        setShareUrl(`${window.location.origin}/p/${data.share_id}`);

        // Fetch the full snapshot for the card
        const shareRes = await fetch(`${API.replace('/api', '')}/share/${data.share_id}`);
        if (!shareRes.ok) throw new Error("Erreur lors du chargement");
        const shareData = await shareRes.json();
        setSnapshot(shareData.snapshot || shareData);
      } catch (err) {
        toast.error("Impossible de créer le partage");
        onOpenChange(false);
      } finally {
        setIsLoading(false);
      }
    }
    if (!isOpen) {
      // Reset state on close
      setSnapshot(null);
      setLinkCopied(false);
      setShareUrl("");
    }
  }, [onOpenChange, snapshot, shareType, objectiveId, preloadedUrl]);

  // Export card as PNG image
  const handleExportImage = useCallback(async () => {
    if (!cardRef.current) return;
    setIsExporting(true);
    try {
      // html-to-image: generate high-res PNG (2x for retina)
      const dataUrl = await toPng(cardRef.current, {
        pixelRatio: 2,
        cacheBust: true,
        style: {
          transform: "scale(1)",
          transformOrigin: "top left",
        },
      });

      // Try native share with image (mobile)
      if (navigator.share && navigator.canShare) {
        const blob = await (await fetch(dataUrl)).blob();
        const file = new File([blob], "infinea-progression.png", { type: "image/png" });
        if (navigator.canShare({ files: [file] })) {
          await navigator.share({
            title: "Ma progression InFinea",
            text: "Investis tes instants perdus",
            files: [file],
          });
          return;
        }
      }

      // Fallback: download image
      const link = document.createElement("a");
      link.download = "infinea-progression.png";
      link.href = dataUrl;
      link.click();
      toast.success("Image sauvegardée !");
    } catch (err) {
      if (err.name !== "AbortError") {
        toast.error("Erreur lors de l'export de l'image");
      }
    } finally {
      setIsExporting(false);
    }
  }, []);

  // Copy share link to clipboard
  const handleCopyLink = useCallback(async () => {
    if (!shareUrl) return;
    try {
      await navigator.clipboard.writeText(shareUrl);
      setLinkCopied(true);
      toast.success("Lien copié !");
      setTimeout(() => setLinkCopied(false), 2500);
    } catch {
      toast.error("Impossible de copier le lien");
    }
  }, [shareUrl]);

  // Native share (text + link)
  const handleNativeShare = useCallback(async () => {
    if (!navigator.share) return;
    try {
      await navigator.share({
        title: "Ma progression InFinea",
        text: "Investis tes instants perdus",
        url: shareUrl,
      });
    } catch {
      // User cancelled — silent
    }
  }, [shareUrl]);

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-[460px] p-0 gap-0 overflow-hidden bg-card border-border">
        <DialogHeader className="px-6 pt-6 pb-0">
          <DialogTitle className="font-sans font-semibold tracking-tight text-lg">Partager ma progression</DialogTitle>
        </DialogHeader>

        <div className="px-6 py-5">
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-12 gap-3">
              <Loader2 className="w-6 h-6 animate-spin text-primary" />
              <span className="text-sm text-muted-foreground">Génération de la carte...</span>
            </div>
          ) : (snapshot || preloadedUrl) ? (
            <>
              {/* Card preview (only when snapshot exists) */}
              {snapshot && (
                <div className="flex justify-center mb-5 -mx-2">
                  <div className="transform scale-[0.85] origin-top">
                    <ShareCard ref={cardRef} snapshot={snapshot} shareType={shareType} />
                  </div>
                </div>
              )}

              {/* Action buttons */}
              <div className="space-y-3">
                {/* Primary: save image (only with card preview) */}
                {snapshot && (
                  <Button
                    className="w-full gap-2"
                    onClick={handleExportImage}
                    disabled={isExporting}
                  >
                    {isExporting ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <ImageIcon className="w-4 h-4" />
                    )}
                    {isExporting ? "Export en cours..." : "Sauvegarder l'image"}
                  </Button>
                )}

                {/* Social share row — Twitter/X, LinkedIn, WhatsApp */}
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => shareOnTwitter(shareUrl, shareText)}
                    className="flex-1 flex items-center justify-center gap-2 h-10 rounded-xl border border-border bg-card hover:bg-muted/60 transition-colors text-sm font-medium"
                    title="Partager sur X"
                  >
                    <TwitterIcon className="w-4 h-4" />
                    <span className="hidden sm:inline">X</span>
                  </button>
                  <button
                    onClick={() => shareOnLinkedIn(shareUrl)}
                    className="flex-1 flex items-center justify-center gap-2 h-10 rounded-xl border border-border bg-card hover:bg-muted/60 transition-colors text-sm font-medium text-[#0A66C2]"
                    title="Partager sur LinkedIn"
                  >
                    <LinkedInIcon className="w-4 h-4" />
                    <span className="hidden sm:inline">LinkedIn</span>
                  </button>
                  <button
                    onClick={() => shareOnWhatsApp(shareUrl, shareText)}
                    className="flex-1 flex items-center justify-center gap-2 h-10 rounded-xl border border-border bg-card hover:bg-muted/60 transition-colors text-sm font-medium text-[#25D366]"
                    title="Partager sur WhatsApp"
                  >
                    <WhatsAppIcon className="w-4 h-4" />
                    <span className="hidden sm:inline">WhatsApp</span>
                  </button>
                </div>

                {/* Copy link + native share */}
                <div className="grid grid-cols-2 gap-2.5">
                  <Button
                    variant="outline"
                    className="gap-2"
                    onClick={handleCopyLink}
                  >
                    {linkCopied ? (
                      <Check className="w-4 h-4 text-[#5DB786]" />
                    ) : (
                      <Link2 className="w-4 h-4" />
                    )}
                    {linkCopied ? "Copié !" : "Copier le lien"}
                  </Button>

                  {typeof navigator !== "undefined" && navigator.share && (
                    <Button
                      variant="outline"
                      className="gap-2"
                      onClick={handleNativeShare}
                    >
                      <Share2 className="w-4 h-4" />
                      Partager
                    </Button>
                  )}
                </div>
              </div>
            </>
          ) : null}
        </div>
      </DialogContent>
    </Dialog>
  );
}
