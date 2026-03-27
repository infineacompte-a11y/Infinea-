import React, { useState, useEffect, useRef } from "react";
import { Star, Share2 } from "lucide-react";
import { Button } from "@/components/ui/button";

/**
 * Level-Up Celebration Overlay — Duolingo-inspired.
 *
 * Full-screen overlay with confetti particles, level badge animation,
 * and title reveal. Auto-dismissed after 4s or on click.
 *
 * Props:
 *   newLevel (number) — the level just reached
 *   title (string) — "Explorateur", "Apprenti", etc.
 *   onDismiss (function) — called when overlay closes
 */

const TITLE_COLORS = {
  "Curieux":      "#55B3AE",
  "Explorateur":  "#459492",
  "Apprenti":     "#5DB786",
  "Praticien":    "#3D8B37",
  "Expert":       "#E48C75",
  "Maître":       "#D4734E",
  "Virtuose":     "#9B59B6",
  "Légende":      "#F5A623",
};

const CONFETTI_COLORS = ["#459492", "#55B3AE", "#E48C75", "#F5A623", "#5DB786", "#9B59B6", "#275255"];

function Confetti() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const particles = Array.from({ length: 80 }, () => ({
      x: Math.random() * canvas.width,
      y: -20 - Math.random() * 200,
      w: 4 + Math.random() * 6,
      h: 8 + Math.random() * 12,
      color: CONFETTI_COLORS[Math.floor(Math.random() * CONFETTI_COLORS.length)],
      vx: (Math.random() - 0.5) * 4,
      vy: 2 + Math.random() * 4,
      rotation: Math.random() * 360,
      rotSpeed: (Math.random() - 0.5) * 10,
      opacity: 1,
    }));

    let animId;
    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      let alive = false;
      for (const p of particles) {
        if (p.opacity <= 0) continue;
        alive = true;

        p.x += p.vx;
        p.y += p.vy;
        p.vy += 0.08; // gravity
        p.rotation += p.rotSpeed;

        // Fade out when near bottom
        if (p.y > canvas.height * 0.7) {
          p.opacity -= 0.02;
        }

        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate((p.rotation * Math.PI) / 180);
        ctx.globalAlpha = Math.max(0, p.opacity);
        ctx.fillStyle = p.color;
        ctx.fillRect(-p.w / 2, -p.h / 2, p.w, p.h);
        ctx.restore();
      }

      if (alive) {
        animId = requestAnimationFrame(animate);
      }
    };

    animate();
    return () => cancelAnimationFrame(animId);
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 pointer-events-none"
      style={{ zIndex: 1 }}
    />
  );
}

export default function LevelUpCelebration({ newLevel, title, onDismiss }) {
  const [visible, setVisible] = useState(true);
  const color = TITLE_COLORS[title] || "#459492";

  // Auto-dismiss after 5s
  useEffect(() => {
    const timer = setTimeout(() => {
      setVisible(false);
      setTimeout(onDismiss, 300);
    }, 5000);
    return () => clearTimeout(timer);
  }, [onDismiss]);

  const handleDismiss = () => {
    setVisible(false);
    setTimeout(onDismiss, 300);
  };

  if (!visible && !newLevel) return null;

  return (
    <div
      className={`fixed inset-0 z-[100] flex items-center justify-center transition-opacity duration-300 ${
        visible ? "opacity-100" : "opacity-0"
      }`}
      onClick={handleDismiss}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

      {/* Confetti */}
      <Confetti />

      {/* Content */}
      <div className="relative z-10 text-center px-6" style={{ animation: "scaleIn 0.5s cubic-bezier(0.34, 1.56, 0.64, 1)" }}>
        {/* Level badge — large, glowing */}
        <div
          className="w-28 h-28 rounded-full flex items-center justify-center mx-auto mb-6 shadow-2xl"
          style={{
            background: `linear-gradient(135deg, ${color}, ${color}cc)`,
            boxShadow: `0 0 60px ${color}60, 0 0 120px ${color}30`,
          }}
        >
          <div className="text-center">
            <Star className="w-6 h-6 text-white/80 mx-auto mb-0.5" fill="white" />
            <span className="text-4xl font-bold text-white">{newLevel}</span>
          </div>
        </div>

        <h2 className="text-3xl font-bold text-white mb-2">
          Niveau supérieur !
        </h2>

        <p className="text-lg text-white/80 mb-1">
          Tu es maintenant
        </p>

        <p
          className="text-2xl font-bold mb-6"
          style={{ color }}
        >
          {title}
        </p>

        <div className="flex items-center gap-3">
          <Button
            onClick={async (e) => {
              e.stopPropagation();
              const text = `Niveau ${newLevel} atteint sur InFinea ! Je suis maintenant "${title}"`;
              const url = window.location.origin;
              if (navigator.share) {
                try { await navigator.share({ title: "InFinea", text, url }); } catch {}
              } else {
                try {
                  await navigator.clipboard.writeText(`${text} — ${url}`);
                } catch {}
              }
            }}
            className="rounded-xl px-5 h-12 text-base font-semibold shadow-lg border-2 border-white/20 bg-white/10 hover:bg-white/20 text-white backdrop-blur-sm"
          >
            <Share2 className="w-4 h-4 mr-2" />
            Partager
          </Button>
          <Button
            onClick={handleDismiss}
            className="rounded-xl px-8 h-12 text-base font-semibold shadow-lg"
            style={{
              background: `linear-gradient(135deg, ${color}, ${color}cc)`,
              color: "white",
            }}
          >
            Continuer
          </Button>
        </div>
      </div>

      {/* Keyframe for scale animation */}
      <style>{`
        @keyframes scaleIn {
          from { transform: scale(0.5); opacity: 0; }
          to { transform: scale(1); opacity: 1; }
        }
      `}</style>
    </div>
  );
}
