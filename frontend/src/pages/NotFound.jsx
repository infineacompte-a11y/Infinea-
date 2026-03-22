import React from "react";
import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import InFineaLogo from "@/components/InFineaLogo";

export default function NotFound() {
  return (
    <div className="min-h-screen app-bg-mesh flex flex-col items-center justify-center px-4 animate-fade-in">
      {/* Animated brand logo */}
      <div className="mb-8">
        <InFineaLogo size={64} animate />
      </div>

      {/* 404 number with brand teal accent */}
      <h1 className="font-sans font-semibold tracking-tight text-8xl sm:text-9xl font-bold tracking-tighter mb-2">
        <span className="text-[#459492]">4</span>
        <span className="text-[#141E24]/20">0</span>
        <span className="text-[#459492]">4</span>
      </h1>

      {/* Message */}
      <p className="font-sans font-semibold tracking-tight text-xl text-[#141E24] mb-2">
        Page introuvable
      </p>
      <p className="text-[#667085] text-sm mb-10 text-center max-w-sm leading-relaxed">
        Cette page n'existe pas ou a été déplacée.
        Pas de temps perdu, retourne transformer tes instants.
      </p>

      {/* CTA */}
      <Link to="/">
        <Button
          size="lg"
          className="gap-2 rounded-xl h-12 px-8 transition-all hover:shadow-lg hover:shadow-[#459492]/10"
        >
          <ArrowLeft className="w-4 h-4" />
          Retour à l'accueil
        </Button>
      </Link>

      {/* Subtle brand footer */}
      <p className="text-[#667085]/40 text-xs mt-16">
        InFinea — Chaque instant compte
      </p>
    </div>
  );
}
