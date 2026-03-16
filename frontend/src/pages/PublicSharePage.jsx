import React, { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Loader2, ArrowRight, Zap } from "lucide-react";
import ShareCard from "@/components/ShareCard";
import { useTranslation } from "react-i18next";

/**
 * PublicSharePage — Public page displaying a shared progression card.
 * No authentication required. Accessible at /p/:shareId.
 *
 * Includes OpenGraph-friendly structure for social media link previews.
 * CTA "Essaie InFinea" drives acquisition from shared links.
 *
 * Pattern: Strava public activity page + Duolingo profile share.
 */

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "http://localhost:8000";

export default function PublicSharePage() {
  const { t } = useTranslation();
  const { shareId } = useParams();
  const [share, setShare] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!shareId) return;
    (async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/share/${shareId}`);
        if (res.status === 404) {
          setError("not_found");
          return;
        }
        if (res.status === 410) {
          setError("expired");
          return;
        }
        if (!res.ok) throw new Error("Erreur serveur");
        const data = await res.json();
        setShare(data);
      } catch {
        setError("server");
      } finally {
        setIsLoading(false);
      }
    })();
  }, [shareId]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-[hsl(239,84%,67%)]" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] flex flex-col items-center justify-center px-4 text-center">
        <div className="w-14 h-14 rounded-2xl bg-[hsl(239,84%,67%)]/10 flex items-center justify-center mb-5">
          <Zap className="w-7 h-7 text-[hsl(239,84%,67%)]" />
        </div>
        <h1 className="text-white text-xl font-bold mb-2">
          {error === "expired" ? t("publicShare.expired") : t("publicShare.notFound")}
        </h1>
        <p className="text-white/50 text-sm mb-6 max-w-xs">
          {error === "expired"
            ? t("publicShare.expiredDescription")
            : t("publicShare.notFoundDescription")}
        </p>
        <Link to="/">
          <Button className="gap-2">
            <Zap className="w-4 h-4" />
            {t("publicShare.discoverInfinea")}
          </Button>
        </Link>
      </div>
    );
  }

  const snapshot = share?.snapshot || share;
  const authorName = share?.author?.name || t("publicShare.defaultAuthor");

  return (
    <div className="min-h-screen bg-[#0a0a0f] flex flex-col items-center justify-center px-4 py-12">
      {/* Card */}
      <div className="mb-8">
        <ShareCard snapshot={snapshot} shareType={share?.share_type || "weekly_recap"} />
      </div>

      {/* CTA */}
      <div className="text-center max-w-sm">
        <p className="text-white/40 text-sm mb-4">
          {t("publicShare.authorInvests", { name: authorName })}
        </p>
        <Link to="/register">
          <Button size="lg" className="gap-2 px-8">
            {t("publicShare.tryFree")}
            <ArrowRight className="w-4 h-4" />
          </Button>
        </Link>
        <p className="text-white/20 text-[10px] mt-4">
          {t("publicShare.tagline")}
        </p>
      </div>
    </div>
  );
}
