/**
 * ShareProfilePage — Public share card for user profiles.
 *
 * Pattern: Strava share, Spotify Wrapped, Duolingo streak share.
 * No auth required — designed for social media sharing.
 *
 * Route: /share/profile/:userId
 */

import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import {
  Flame,
  Clock,
  Users,
  Award,
  Star,
  Loader2,
  Share2,
  Copy,
  Check,
  ExternalLink,
  Crown,
} from "lucide-react";

const API = import.meta?.env?.VITE_API_URL || process.env.REACT_APP_API_URL || "";

// Resolve to absolute backend URL for public endpoints (no /api prefix)
function getShareApiUrl() {
  if (API.endsWith("/api")) return API.replace(/\/api$/, "");
  return API;
}

const TIER_LABELS = {
  free: null,
  pro: { label: "Pro", color: "#459492" },
  premium: { label: "Premium", color: "#F5A623" },
};

function getInitials(name) {
  if (!name) return "U";
  return name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2);
}

export default function ShareProfilePage() {
  const { userId } = useParams();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!userId) return;
    (async () => {
      try {
        const base = getShareApiUrl();
        const res = await fetch(`${base}/share/profile/${userId}`);
        if (res.status === 404) { setError("not_found"); return; }
        if (res.status === 403) { setError("private"); return; }
        if (!res.ok) throw new Error();
        setProfile(await res.json());
      } catch {
        setError("network");
      } finally {
        setLoading(false);
      }
    })();
  }, [userId]);

  const shareUrl = window.location.href;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch { /* fallback: do nothing */ }
  };

  const shareTwitter = () => {
    const text = profile
      ? `Découvrez le profil de ${profile.display_name} sur InFinea ! 🚀`
      : "Découvrez InFinea !";
    window.open(
      `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(shareUrl)}`,
      "_blank",
    );
  };

  const shareLinkedIn = () => {
    window.open(
      `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(shareUrl)}`,
      "_blank",
    );
  };

  const shareWhatsApp = () => {
    const text = profile
      ? `Regarde le profil de ${profile.display_name} sur InFinea 🚀 ${shareUrl}`
      : `Découvre InFinea ${shareUrl}`;
    window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, "_blank");
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#0F1419] via-[#1A2332] to-[#0F1419] flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-[#459492]" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#0F1419] via-[#1A2332] to-[#0F1419] flex items-center justify-center px-4">
        <div className="text-center">
          <div className="w-16 h-16 rounded-2xl bg-[#459492]/20 flex items-center justify-center mx-auto mb-4">
            <Users className="w-8 h-8 text-[#459492]" />
          </div>
          <h1 className="text-xl font-semibold text-white mb-2">
            {error === "not_found" ? "Profil introuvable" : error === "private" ? "Profil privé" : "Erreur de chargement"}
          </h1>
          <p className="text-white/50 text-sm mb-6">
            {error === "private"
              ? "Ce profil n'est pas visible publiquement."
              : "Ce lien n'est plus valide."}
          </p>
          <a
            href="/"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-[#459492] text-white text-sm font-medium hover:bg-[#3a7d7b] transition-colors"
          >
            Découvrir InFinea
            <ExternalLink className="w-4 h-4" />
          </a>
        </div>
      </div>
    );
  }

  const tier = TIER_LABELS[profile.subscription_tier];
  const memberSince = profile.created_at
    ? new Date(profile.created_at).toLocaleDateString("fr-FR", { month: "long", year: "numeric" })
    : null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0F1419] via-[#1A2332] to-[#0F1419] flex flex-col items-center justify-center px-4 py-8">
      {/* Profile card */}
      <div className="w-full max-w-sm">
        <div className="relative rounded-2xl bg-gradient-to-br from-[#1E2D3D] to-[#162230] border border-white/10 overflow-hidden shadow-2xl">
          {/* Top accent */}
          <div className="h-1.5 bg-gradient-to-r from-[#459492] via-[#55B3AE] to-[#5DB786]" />

          <div className="p-6 text-center">
            {/* Avatar */}
            <div className="relative inline-block mb-4">
              {profile.avatar_url ? (
                <img
                  src={profile.avatar_url}
                  alt={profile.display_name}
                  className="w-20 h-20 rounded-full object-cover ring-3 ring-[#459492]/30"
                />
              ) : (
                <div className="w-20 h-20 rounded-full bg-[#459492]/20 flex items-center justify-center ring-3 ring-[#459492]/30">
                  <span className="text-2xl font-semibold text-[#459492]">
                    {getInitials(profile.display_name)}
                  </span>
                </div>
              )}
              {tier && (
                <div
                  className="absolute -bottom-1 -right-1 px-2 py-0.5 rounded-full text-[9px] font-bold text-white flex items-center gap-0.5"
                  style={{ backgroundColor: tier.color }}
                >
                  <Crown className="w-2.5 h-2.5" />
                  {tier.label}
                </div>
              )}
            </div>

            {/* Name + username */}
            <h1 className="text-xl font-semibold text-white">{profile.display_name}</h1>
            {profile.username && (
              <p className="text-sm text-white/40 mt-0.5">@{profile.username}</p>
            )}
            {profile.bio && (
              <p className="text-sm text-white/60 mt-2 leading-relaxed">{profile.bio}</p>
            )}

            {/* Stats */}
            <div className="grid grid-cols-3 gap-3 mt-5">
              {profile.streak_days != null && (
                <div className="p-3 rounded-xl bg-white/5 border border-white/5">
                  <Flame className="w-4 h-4 text-[#E48C75] mx-auto mb-1" />
                  <p className="text-lg font-semibold text-white tabular-nums">{profile.streak_days}</p>
                  <p className="text-[10px] text-white/40">streak</p>
                </div>
              )}
              {profile.total_time_invested != null && (
                <div className="p-3 rounded-xl bg-white/5 border border-white/5">
                  <Clock className="w-4 h-4 text-[#459492] mx-auto mb-1" />
                  <p className="text-lg font-semibold text-white tabular-nums">
                    {profile.total_time_invested >= 60
                      ? `${Math.floor(profile.total_time_invested / 60)}h`
                      : `${profile.total_time_invested}m`}
                  </p>
                  <p className="text-[10px] text-white/40">investies</p>
                </div>
              )}
              <div className="p-3 rounded-xl bg-white/5 border border-white/5">
                <Users className="w-4 h-4 text-[#5DB786] mx-auto mb-1" />
                <p className="text-lg font-semibold text-white tabular-nums">{profile.followers_count || 0}</p>
                <p className="text-[10px] text-white/40">followers</p>
              </div>
            </div>

            {/* Level */}
            {profile.level && (
              <div className="flex items-center justify-center gap-1.5 mt-4 text-sm">
                <Star className="w-4 h-4 text-[#F5A623]" />
                <span className="text-white/70">Niveau <span className="font-semibold text-white">{profile.level}</span></span>
              </div>
            )}

            {/* Badges */}
            {profile.badges && profile.badges.length > 0 && (
              <div className="mt-4">
                <div className="flex items-center justify-center gap-1 mb-2">
                  <Award className="w-3.5 h-3.5 text-[#F5A623]" />
                  <span className="text-[10px] text-white/40 uppercase tracking-wider">Badges</span>
                </div>
                <div className="flex justify-center gap-2 flex-wrap">
                  {profile.badges.map((badge, i) => (
                    <div
                      key={i}
                      className="px-3 py-1.5 rounded-full bg-[#F5A623]/10 border border-[#F5A623]/20"
                    >
                      <span className="text-xs text-[#F5A623] font-medium">
                        {badge.icon && `${badge.icon} `}{badge.name}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Member since */}
            {memberSince && (
              <p className="text-[10px] text-white/20 mt-4">
                Membre depuis {memberSince}
              </p>
            )}
          </div>

          {/* Footer: InFinea branding */}
          <div className="px-6 py-3 bg-white/3 border-t border-white/5 flex items-center justify-center gap-2">
            <div className="w-5 h-5 rounded-md bg-[#459492]/30 flex items-center justify-center">
              <span className="text-[10px] font-bold text-[#459492]">iF</span>
            </div>
            <span className="text-[11px] text-white/30 font-medium">InFinea — Investissez vos instants perdus</span>
          </div>
        </div>

        {/* Share actions */}
        <div className="mt-6 flex items-center justify-center gap-2">
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-white/10 hover:bg-white/15 text-white/70 hover:text-white text-sm transition-all"
          >
            {copied ? <Check className="w-4 h-4 text-[#5DB786]" /> : <Copy className="w-4 h-4" />}
            {copied ? "Copié !" : "Copier"}
          </button>
          <button
            onClick={shareTwitter}
            className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-[#1DA1F2]/10 hover:bg-[#1DA1F2]/20 text-[#1DA1F2] text-sm transition-all"
          >
            <Share2 className="w-4 h-4" />
            Twitter
          </button>
          <button
            onClick={shareLinkedIn}
            className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-[#0A66C2]/10 hover:bg-[#0A66C2]/20 text-[#0A66C2] text-sm transition-all"
          >
            <Share2 className="w-4 h-4" />
            LinkedIn
          </button>
          <button
            onClick={shareWhatsApp}
            className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-[#25D366]/10 hover:bg-[#25D366]/20 text-[#25D366] text-sm transition-all"
          >
            <Share2 className="w-4 h-4" />
            WhatsApp
          </button>
        </div>

        {/* CTA */}
        <div className="mt-6 text-center">
          <a
            href="/"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-[#459492] text-white text-sm font-medium hover:bg-[#3a7d7b] transition-colors shadow-lg shadow-[#459492]/20"
          >
            Rejoindre InFinea
            <ExternalLink className="w-4 h-4" />
          </a>
        </div>
      </div>
    </div>
  );
}
