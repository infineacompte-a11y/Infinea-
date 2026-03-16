import React from "react";
import { Link } from "react-router-dom";
import { Timer, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTranslation } from "react-i18next";

export default function PrivacyPage() {
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
          <h1 className="font-heading text-3xl font-bold mb-2">{t("privacy.title")}</h1>
          <p className="text-muted-foreground mb-8">{t("privacy.lastUpdated")}</p>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">{t("privacy.dataController.heading")}</h2>
            <p className="text-muted-foreground leading-relaxed">
              {t("privacy.dataController.text")}<br />
              <strong className="text-foreground">InFinea</strong><br />
              {t("privacy.dataController.email")} <a href="mailto:infinea.compte@gmail.com" className="text-primary hover:underline">infinea.compte@gmail.com</a>
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">{t("privacy.dataCollected.heading")}</h2>
            <p className="text-muted-foreground leading-relaxed mb-3">
              {t("privacy.dataCollected.intro")}
            </p>
            <ul className="text-muted-foreground space-y-2 list-disc list-inside">
              <li><strong className="text-foreground">{t("privacy.dataCollected.registrationLabel")}</strong> {t("privacy.dataCollected.registrationText")}</li>
              <li><strong className="text-foreground">{t("privacy.dataCollected.profileLabel")}</strong> {t("privacy.dataCollected.profileText")}</li>
              <li><strong className="text-foreground">{t("privacy.dataCollected.usageLabel")}</strong> {t("privacy.dataCollected.usageText")}</li>
              <li><strong className="text-foreground">{t("privacy.dataCollected.connectionLabel")}</strong> {t("privacy.dataCollected.connectionText")}</li>
              <li><strong className="text-foreground">{t("privacy.dataCollected.integrationLabel")}</strong> {t("privacy.dataCollected.integrationText")}</li>
              <li><strong className="text-foreground">{t("privacy.dataCollected.googleCalendarLabel")}</strong> {t("privacy.dataCollected.googleCalendarText")}</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">{t("privacy.googleData.heading")}</h2>
            <p className="text-muted-foreground leading-relaxed mb-3">
              {t("privacy.googleData.intro")} <code className="text-xs bg-muted px-1.5 py-0.5 rounded">calendar.readonly</code>{t("privacy.googleData.introSuffix")}
            </p>
            <ul className="text-muted-foreground space-y-2 list-disc list-inside">
              <li><strong className="text-foreground">{t("privacy.googleData.freeSlotLabel")}</strong> {t("privacy.googleData.freeSlotText")}</li>
              <li><strong className="text-foreground">{t("privacy.googleData.contextualLabel")}</strong> {t("privacy.googleData.contextualText")}</li>
            </ul>
            <p className="text-muted-foreground leading-relaxed mt-3">
              <strong className="text-foreground">{t("privacy.googleData.notDoTitle")}</strong>
            </p>
            <ul className="text-muted-foreground space-y-2 list-disc list-inside">
              <li>{t("privacy.googleData.notDo1")}</li>
              <li>{t("privacy.googleData.notDo2")}</li>
              <li>{t("privacy.googleData.notDo3")}</li>
              <li>{t("privacy.googleData.notDo4")}</li>
              <li>{t("privacy.googleData.notDo5")}</li>
            </ul>
            <p className="text-muted-foreground leading-relaxed mt-3">
              {t("privacy.googleData.complianceText")}{" "}
              <a href="https://developers.google.com/terms/api-services-user-data-policy" className="text-primary hover:underline" target="_blank" rel="noopener noreferrer">
                {t("privacy.googleData.complianceLink")}
              </a>{t("privacy.googleData.complianceSuffix")}
            </p>
            <p className="text-muted-foreground leading-relaxed mt-3">
              {t("privacy.googleData.revokeText")}{" "}
              <a href="https://myaccount.google.com/permissions" className="text-primary hover:underline" target="_blank" rel="noopener noreferrer">
                {t("privacy.googleData.revokeLink")}
              </a>{" "}
              {t("privacy.googleData.revokeSuffix")}
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">{t("privacy.purposes.heading")}</h2>
            <ul className="text-muted-foreground space-y-2 list-disc list-inside">
              <li>{t("privacy.purposes.item1")}</li>
              <li>{t("privacy.purposes.item2")}</li>
              <li>{t("privacy.purposes.item3")}</li>
              <li>{t("privacy.purposes.item4")}</li>
              <li>{t("privacy.purposes.item5")}</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">{t("privacy.legalBasis.heading")}</h2>
            <ul className="text-muted-foreground space-y-2 list-disc list-inside">
              <li><strong className="text-foreground">{t("privacy.legalBasis.contractLabel")}</strong> {t("privacy.legalBasis.contractText")}</li>
              <li><strong className="text-foreground">{t("privacy.legalBasis.consentLabel")}</strong> {t("privacy.legalBasis.consentText")}</li>
              <li><strong className="text-foreground">{t("privacy.legalBasis.legitimateLabel")}</strong> {t("privacy.legalBasis.legitimateText")}</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">{t("privacy.retention.heading")}</h2>
            <p className="text-muted-foreground leading-relaxed">
              {t("privacy.retention.text")}
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">{t("privacy.rights.heading")}</h2>
            <p className="text-muted-foreground leading-relaxed mb-3">
              {t("privacy.rights.intro")}
            </p>
            <ul className="text-muted-foreground space-y-2 list-disc list-inside">
              <li><strong className="text-foreground">{t("privacy.rights.accessLabel")}</strong> {t("privacy.rights.accessText")}</li>
              <li><strong className="text-foreground">{t("privacy.rights.rectificationLabel")}</strong> {t("privacy.rights.rectificationText")}</li>
              <li><strong className="text-foreground">{t("privacy.rights.erasureLabel")}</strong> {t("privacy.rights.erasureText")}</li>
              <li><strong className="text-foreground">{t("privacy.rights.portabilityLabel")}</strong> {t("privacy.rights.portabilityText")}</li>
              <li><strong className="text-foreground">{t("privacy.rights.objectionLabel")}</strong> {t("privacy.rights.objectionText")}</li>
              <li><strong className="text-foreground">{t("privacy.rights.restrictionLabel")}</strong> {t("privacy.rights.restrictionText")}</li>
            </ul>
            <p className="text-muted-foreground leading-relaxed mt-3">
              {t("privacy.rights.contact")}{" "}
              <a href="mailto:infinea.compte@gmail.com" className="text-primary hover:underline">infinea.compte@gmail.com</a>.
              {" "}{t("privacy.rights.responseTime")}
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">{t("privacy.deletion.heading")}</h2>
            <p className="text-muted-foreground leading-relaxed mb-3">
              {t("privacy.deletion.intro")}
            </p>
            <ul className="text-muted-foreground space-y-2 list-disc list-inside">
              <li><strong className="text-foreground">{t("privacy.deletion.accountLabel")}</strong> {t("privacy.deletion.accountText")}</li>
              <li><strong className="text-foreground">{t("privacy.deletion.googleLabel")}</strong> {t("privacy.deletion.googleText")}{" "}
                <a href="https://myaccount.google.com/permissions" className="text-primary hover:underline" target="_blank" rel="noopener noreferrer">{t("privacy.deletion.googleLink")}</a>{t("privacy.deletion.googleSuffix")}</li>
              <li><strong className="text-foreground">{t("privacy.deletion.emailLabel")}</strong> {t("privacy.deletion.emailText")}{" "}
                <a href="mailto:infinea.compte@gmail.com" className="text-primary hover:underline">infinea.compte@gmail.com</a> {t("privacy.deletion.emailSuffix")}</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">{t("privacy.hosting.heading")}</h2>
            <p className="text-muted-foreground leading-relaxed mb-3">{t("privacy.hosting.intro")}</p>
            <ul className="text-muted-foreground space-y-2 list-disc list-inside">
              <li><strong className="text-foreground">MongoDB Atlas</strong> {t("privacy.hosting.mongodb")}</li>
              <li><strong className="text-foreground">Render</strong> {t("privacy.hosting.render")}</li>
              <li><strong className="text-foreground">Vercel</strong> {t("privacy.hosting.vercel")}</li>
              <li><strong className="text-foreground">Stripe</strong> {t("privacy.hosting.stripe")}</li>
            </ul>
            <p className="text-muted-foreground leading-relaxed mt-3">
              {t("privacy.hosting.encryption")}
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">{t("privacy.cookies.heading")}</h2>
            <p className="text-muted-foreground leading-relaxed mb-3">{t("privacy.cookies.intro")}</p>
            <ul className="text-muted-foreground space-y-2 list-disc list-inside">
              <li><strong className="text-foreground">{t("privacy.cookies.essentialLabel")}</strong> {t("privacy.cookies.essentialText")}</li>
              <li><strong className="text-foreground">{t("privacy.cookies.analyticsLabel")}</strong> {t("privacy.cookies.analyticsText")}</li>
            </ul>
            <p className="text-muted-foreground leading-relaxed mt-3">
              {t("privacy.cookies.disable")}
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">{t("privacy.transfers.heading")}</h2>
            <p className="text-muted-foreground leading-relaxed">
              {t("privacy.transfers.text")}
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">{t("privacy.contactSection.heading")}</h2>
            <p className="text-muted-foreground leading-relaxed">
              {t("privacy.contactSection.text")}{" "}
              <a href="mailto:infinea.compte@gmail.com" className="text-primary hover:underline">infinea.compte@gmail.com</a>.
            </p>
            <p className="text-muted-foreground leading-relaxed mt-3">
              {t("privacy.contactSection.cnilText")}{" "}
              <strong className="text-foreground">{t("privacy.contactSection.cnilName")}</strong> :{" "}
              <a href="https://www.cnil.fr" className="text-primary hover:underline" target="_blank" rel="noopener noreferrer">www.cnil.fr</a>.
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
            <span className="text-primary">{t("common.privacy")}</span>
            <Link to="/cgu" className="hover:text-foreground transition-colors">{t("common.terms")}</Link>
            <a href="mailto:infinea.compte@gmail.com" className="hover:text-foreground transition-colors">{t("common.contact")}</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
