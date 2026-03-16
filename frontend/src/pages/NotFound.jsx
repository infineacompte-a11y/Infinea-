import React from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Timer, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  const { t } = useTranslation();

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center px-4">
      <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mb-6">
        <Timer className="w-8 h-8 text-primary" />
      </div>
      <h1 className="font-heading text-6xl font-bold text-foreground mb-2">404</h1>
      <p className="text-lg text-muted-foreground mb-8">
        {t("notFound.message")}
      </p>
      <Link to="/">
        <Button>
          <ArrowLeft className="w-4 h-4 mr-2" />
          {t("notFound.backHome")}
        </Button>
      </Link>
    </div>
  );
}
