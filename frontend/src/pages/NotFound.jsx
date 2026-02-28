import React from "react";
import { Link } from "react-router-dom";
import { Timer, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center px-4">
      <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mb-6">
        <Timer className="w-8 h-8 text-primary" />
      </div>
      <h1 className="font-heading text-6xl font-bold text-foreground mb-2">404</h1>
      <p className="text-lg text-muted-foreground mb-8">
        Cette page n'existe pas ou a été déplacée.
      </p>
      <Link to="/">
        <Button>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Retour à l'accueil
        </Button>
      </Link>
    </div>
  );
}
