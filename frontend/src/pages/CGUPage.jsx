import React from "react";
import { Link } from "react-router-dom";
import { Timer, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTranslation } from "react-i18next";

export default function CGUPage() {
  const { t, i18n } = useTranslation();

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <nav className="fixed top-0 w-full z-50 glass">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
              <Timer className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="font-heading text-xl font-semibold">InFinea</span>
          </Link>
          <Link to="/">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="w-4 h-4 mr-2" />
              {t("common.back")}
            </Button>
          </Link>
        </div>
      </nav>

      {/* Content */}
      <main className="pt-24 pb-16 px-4">
        <div className="max-w-3xl mx-auto prose prose-invert prose-sm">
          <h1 className="font-heading text-3xl font-bold mb-2">{t("cgu.title")}</h1>
          <p className="text-muted-foreground mb-8">{t("cgu.lastUpdated")}</p>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">{t("cgu.purpose.heading")}</h2>
            <p className="text-muted-foreground leading-relaxed">
              {t("cgu.purpose.text1")}{" "}
              <a href="https://infinea.vercel.app" className="text-primary hover:underline">infinea.vercel.app</a>.
              {" "}{t("cgu.purpose.text2")}
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">{t("cgu.acceptance.heading")}</h2>
            <p className="text-muted-foreground leading-relaxed">
              {t("cgu.acceptance.text")}
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">{t("cgu.access.heading")}</h2>
            <p className="text-muted-foreground leading-relaxed mb-3">
              {t("cgu.access.intro")}
            </p>
            <ul className="text-muted-foreground space-y-2 list-disc list-inside">
              <li>{t("cgu.access.item1")}</li>
              <li>{t("cgu.access.item2")}</li>
              <li>{t("cgu.access.item3")}</li>
              <li>{t("cgu.access.item4")}</li>
            </ul>
            <p className="text-muted-foreground leading-relaxed mt-3">
              {t("cgu.access.responsibility")}
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">{t("cgu.serviceDescription.heading")}</h2>
            <p className="text-muted-foreground leading-relaxed mb-3">{t("cgu.serviceDescription.intro")}</p>
            <ul className="text-muted-foreground space-y-2 list-disc list-inside">
              <li><strong className="text-foreground">{t("cgu.serviceDescription.microActionsLabel")}</strong> {t("cgu.serviceDescription.microActionsText")}</li>
              <li><strong className="text-foreground">{t("cgu.serviceDescription.aiSuggestionsLabel")}</strong> {t("cgu.serviceDescription.aiSuggestionsText")}</li>
              <li><strong className="text-foreground">{t("cgu.serviceDescription.progressLabel")}</strong> {t("cgu.serviceDescription.progressText")}</li>
              <li><strong className="text-foreground">{t("cgu.serviceDescription.integrationsLabel")}</strong> {t("cgu.serviceDescription.integrationsText")}</li>
              <li><strong className="text-foreground">{t("cgu.serviceDescription.journalLabel")}</strong> {t("cgu.serviceDescription.journalText")}</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">{t("cgu.pricing.heading")}</h2>
            <p className="text-muted-foreground leading-relaxed mb-3">{t("cgu.pricing.intro")}</p>
            <ul className="text-muted-foreground space-y-2 list-disc list-inside">
              <li><strong className="text-foreground">{t("cgu.pricing.freeLabel")}</strong> {t("cgu.pricing.freeText")}</li>
              <li><strong className="text-foreground">{t("cgu.pricing.premiumLabel")}</strong> {t("cgu.pricing.premiumText")}</li>
            </ul>
            <p className="text-muted-foreground leading-relaxed mt-3">
              {t("cgu.pricing.paymentInfo")}
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">{t("cgu.userObligations.heading")}</h2>
            <p className="text-muted-foreground leading-relaxed mb-3">{t("cgu.userObligations.intro")}</p>
            <ul className="text-muted-foreground space-y-2 list-disc list-inside">
              <li>{t("cgu.userObligations.item1")}</li>
              <li>{t("cgu.userObligations.item2")}</li>
              <li>{t("cgu.userObligations.item3")}</li>
              <li>{t("cgu.userObligations.item4")}</li>
              <li>{t("cgu.userObligations.item5")}</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">{t("cgu.intellectualProperty.heading")}</h2>
            <p className="text-muted-foreground leading-relaxed">
              {t("cgu.intellectualProperty.text")}
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">{t("cgu.liability.heading")}</h2>
            <p className="text-muted-foreground leading-relaxed mb-3">
              {t("cgu.liability.intro")}
            </p>
            <ul className="text-muted-foreground space-y-2 list-disc list-inside">
              <li>{t("cgu.liability.item1")}</li>
              <li>{t("cgu.liability.item2")}</li>
              <li>{t("cgu.liability.item3")}</li>
              <li>{t("cgu.liability.item4")}</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">{t("cgu.personalData.heading")}</h2>
            <p className="text-muted-foreground leading-relaxed">
              {t("cgu.personalData.text1")}{" "}
              <Link to="/privacy" className="text-primary hover:underline">{t("cgu.personalData.privacyLink")}</Link>.
              {" "}{t("cgu.personalData.text2")}
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">{t("cgu.termination.heading")}</h2>
            <p className="text-muted-foreground leading-relaxed">
              {t("cgu.termination.text")}
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">{t("cgu.modifications.heading")}</h2>
            <p className="text-muted-foreground leading-relaxed">
              {t("cgu.modifications.text")}
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">{t("cgu.applicableLaw.heading")}</h2>
            <p className="text-muted-foreground leading-relaxed">
              {t("cgu.applicableLaw.text")}
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">{t("cgu.contactSection.heading")}</h2>
            <p className="text-muted-foreground leading-relaxed">
              {t("cgu.contactSection.text")}{" "}
              <a href="mailto:infinea.compte@gmail.com" className="text-primary hover:underline">infinea.compte@gmail.com</a>.
            </p>
          </section>
        </div>
      </main>

      {/* Footer */}
      <footer className="py-8 px-4 border-t border-border">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
              <Timer className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="font-heading text-xl font-semibold">InFinea</span>
          </div>
          <div className="flex items-center gap-6 text-sm text-muted-foreground">
            <span>© 2025-2026 InFinea</span>
            <Link to="/privacy" className="hover:text-foreground transition-colors">{t("common.privacy")}</Link>
            <span className="text-primary">{t("common.terms")}</span>
            <a href="mailto:infinea.compte@gmail.com" className="hover:text-foreground transition-colors">{t("common.contact")}</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
