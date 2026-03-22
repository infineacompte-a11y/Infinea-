import React, { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Loader2, ArrowRight, Zap } from "lucide-react";
import ShareCard from "@/components/ShareCard";
import InFineaLogo from "@/components/InFineaLogo";

/**
 * PublicSharePage — Public page displaying a shared progression card.
 * No authentication required. Accessible at /p/:shareId.
 *
 * Includes OpenGraph-friendly structure for social media link previews.
 * CTA "Essaie InFinea" drives acquisition from shared links.
 *
 * Pattern: Strava public activity page + Duolingo profile share.
 */

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL ?? "http://localhost:8000";

export default function PublicSharePage() {
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
      <div className="min-h-screen app-bg-mesh flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-[#459492]" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen app-bg-mesh flex flex-col items-center justify-center px-4 text-center animate-fade-in">
        <div className="w-14 h-14 rounded-2xl bg-[#459492]/40 flex items-center justify-center mb-5">
          <Zap className="w-7 h-7 text-[#459492]" />
        </div>
        <h1 className="font-sans font-semibold tracking-tight text-[#141E24] text-xl font-bold mb-2">
          {error === "expired" ? "Ce partage a expiré" : "Partage introuvable"}
        </h1>
        <p className="text-[#667085] text-sm mb-6 max-w-xs">
          {error === "expired"
            ? "Les liens de partage expirent après 90 jours."
            : "Ce lien n'existe pas ou a été supprimé."}
        </p>
        <Link to="/">
          <Button className="gap-2 transition-all hover:shadow-lg">
            <Zap className="w-4 h-4" />
            Découvrir InFinea
          </Button>
        </Link>
      </div>
    );
  }

  const snapshot = share?.snapshot || share;
  const authorName = share?.author?.name || "Un utilisateur InFinea";

  return (
    <div className="min-h-screen app-bg-mesh flex flex-col items-center justify-center px-4 py-12 animate-fade-in">
      {/* Brand header */}
      <div className="mb-8">
        <InFineaLogo size={40} withText animate />
      </div>

      {/* Card */}
      <div className="mb-8">
        <ShareCard snapshot={snapshot} shareType={share?.share_type || "weekly_recap"} />
      </div>

      {/* CTA */}
      <div className="text-center max-w-sm">
        <p className="text-[#667085] text-sm mb-4">
          {authorName} investit ses micro-instants avec InFinea.
        </p>
        <Link to="/register">
          <Button size="lg" className="gap-2 px-8 transition-all hover:shadow-lg">
            Essaie InFinea gratuitement
            <ArrowRight className="w-4 h-4" />
          </Button>
        </Link>
        <p className="text-[#667085]/50 text-[10px] mt-4">
          Transforme tes instants perdus en micro-victoires
        </p>
      </div>
    </div>
  );
}
