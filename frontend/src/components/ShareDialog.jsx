import React, { useState, useRef, useCallback } from "react";
import { useTranslation } from "react-i18next";
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

/**
 * ShareDialog — Full share flow: create snapshot → preview card → export.
 * Pattern: Duolingo share modal + Strava activity export.
 *
 * Props:
 *   open — boolean, dialog open state
 *   onOpenChange — function, dialog state setter
 *   shareType — "weekly_recap" | "milestone" | "badge" | "objective"
 *   objectiveId — optional, specific objective to highlight
 */
export default function ShareDialog({ open, onOpenChange, shareType = "weekly_recap", objectiveId = null }) {
  const { t } = useTranslation();
  const [snapshot, setSnapshot] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [linkCopied, setLinkCopied] = useState(false);
  const [shareUrl, setShareUrl] = useState("");
  const cardRef = useRef(null);

  // Fetch snapshot when dialog opens
  const handleOpenChange = useCallback(async (isOpen) => {
    onOpenChange(isOpen);
    if (isOpen && !snapshot) {
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
        toast.error(t("components.shareDialog.errorCreate"));
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
  }, [onOpenChange, snapshot, shareType, objectiveId, t]);

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
            title: t("components.shareDialog.shareTitle"),
            text: t("components.shareDialog.shareText"),
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
      toast.success(t("components.shareDialog.imageSaved"));
    } catch (err) {
      if (err.name !== "AbortError") {
        toast.error(t("components.shareDialog.errorExport"));
      }
    } finally {
      setIsExporting(false);
    }
  }, [t]);

  // Copy share link to clipboard
  const handleCopyLink = useCallback(async () => {
    if (!shareUrl) return;
    try {
      await navigator.clipboard.writeText(shareUrl);
      setLinkCopied(true);
      toast.success(t("components.shareDialog.linkCopied"));
      setTimeout(() => setLinkCopied(false), 2500);
    } catch {
      toast.error(t("components.shareDialog.errorCopy"));
    }
  }, [shareUrl, t]);

  // Native share (text + link)
  const handleNativeShare = useCallback(async () => {
    if (!navigator.share) return;
    try {
      await navigator.share({
        title: t("components.shareDialog.shareTitle"),
        text: t("components.shareDialog.shareText"),
        url: shareUrl,
      });
    } catch {
      // User cancelled — silent
    }
  }, [shareUrl, t]);

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-[460px] p-0 gap-0 overflow-hidden bg-card border-border">
        <DialogHeader className="px-6 pt-6 pb-0">
          <DialogTitle className="font-heading text-lg">{t("components.shareDialog.title")}</DialogTitle>
        </DialogHeader>

        <div className="px-6 py-5">
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-12 gap-3">
              <Loader2 className="w-6 h-6 animate-spin text-primary" />
              <span className="text-sm text-muted-foreground">{t("components.shareDialog.generating")}</span>
            </div>
          ) : snapshot ? (
            <>
              {/* Card preview */}
              <div className="flex justify-center mb-5 -mx-2">
                <div className="transform scale-[0.85] origin-top">
                  <ShareCard ref={cardRef} snapshot={snapshot} shareType={shareType} />
                </div>
              </div>

              {/* Action buttons */}
              <div className="space-y-2.5">
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
                  {isExporting ? t("components.shareDialog.exporting") : t("components.shareDialog.saveImage")}
                </Button>

                <div className="grid grid-cols-2 gap-2.5">
                  <Button
                    variant="outline"
                    className="gap-2"
                    onClick={handleCopyLink}
                  >
                    {linkCopied ? (
                      <Check className="w-4 h-4 text-emerald-500" />
                    ) : (
                      <Link2 className="w-4 h-4" />
                    )}
                    {linkCopied ? t("components.shareDialog.copied") : t("components.shareDialog.copyLink")}
                  </Button>

                  {typeof navigator !== "undefined" && navigator.share && (
                    <Button
                      variant="outline"
                      className="gap-2"
                      onClick={handleNativeShare}
                    >
                      <Share2 className="w-4 h-4" />
                      {t("components.shareDialog.share")}
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
