import React from "react";
import { Link } from "react-router-dom";
import { Timer, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function PrivacyPage() {
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
              Retour
            </Button>
          </Link>
        </div>
      </nav>

      {/* Content */}
      <main className="pt-24 pb-16 px-4">
        <div className="max-w-3xl mx-auto prose prose-invert prose-sm">
          <h1 className="font-heading text-3xl font-bold mb-2">Politique de Confidentialité</h1>
          <p className="text-muted-foreground mb-8">Dernière mise à jour : 28 février 2025</p>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">1. Responsable du traitement</h2>
            <p className="text-muted-foreground leading-relaxed">
              Le responsable du traitement des données collectées sur InFinea est :<br />
              <strong className="text-foreground">InFinea</strong><br />
              Email : <a href="mailto:infinea.compte@gmail.com" className="text-primary hover:underline">infinea.compte@gmail.com</a>
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">2. Données collectées</h2>
            <p className="text-muted-foreground leading-relaxed mb-3">
              Dans le cadre de l'utilisation du service, nous collectons les données suivantes :
            </p>
            <ul className="text-muted-foreground space-y-2 list-disc list-inside">
              <li><strong className="text-foreground">Données d'inscription :</strong> nom, adresse email, mot de passe (hashé)</li>
              <li><strong className="text-foreground">Données de profil :</strong> objectifs, centres d'intérêt, préférences d'énergie</li>
              <li><strong className="text-foreground">Données d'utilisation :</strong> sessions réalisées, temps investi, progression</li>
              <li><strong className="text-foreground">Données de connexion :</strong> adresse IP, type de navigateur (via cookies analytiques)</li>
              <li><strong className="text-foreground">Données d'intégration :</strong> tokens d'accès aux services tiers (chiffrés AES-256)</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">3. Finalités du traitement</h2>
            <ul className="text-muted-foreground space-y-2 list-disc list-inside">
              <li>Fourniture et personnalisation du service (suggestions IA, micro-actions)</li>
              <li>Gestion de votre compte utilisateur</li>
              <li>Amélioration continue du service et de l'expérience utilisateur</li>
              <li>Communication relative au service (notifications, mises à jour)</li>
              <li>Gestion des paiements et abonnements via Stripe</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">4. Base légale du traitement</h2>
            <ul className="text-muted-foreground space-y-2 list-disc list-inside">
              <li><strong className="text-foreground">Exécution du contrat :</strong> traitement nécessaire à la fourniture du service (article 6.1.b du RGPD)</li>
              <li><strong className="text-foreground">Consentement :</strong> pour les cookies analytiques et les communications optionnelles (article 6.1.a)</li>
              <li><strong className="text-foreground">Intérêt légitime :</strong> pour l'amélioration du service et la sécurité (article 6.1.f)</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">5. Durée de conservation</h2>
            <p className="text-muted-foreground leading-relaxed">
              Vos données sont conservées pendant la durée de votre utilisation du service. En cas de suppression de votre compte, vos données personnelles sont supprimées dans un délai de 30 jours, à l'exception des données nécessaires au respect de nos obligations légales (données de facturation : 10 ans).
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">6. Vos droits</h2>
            <p className="text-muted-foreground leading-relaxed mb-3">
              Conformément au Règlement Général sur la Protection des Données (RGPD), vous disposez des droits suivants :
            </p>
            <ul className="text-muted-foreground space-y-2 list-disc list-inside">
              <li><strong className="text-foreground">Droit d'accès</strong> (article 15) : obtenir une copie de vos données personnelles</li>
              <li><strong className="text-foreground">Droit de rectification</strong> (article 16) : corriger vos données inexactes</li>
              <li><strong className="text-foreground">Droit à l'effacement</strong> (article 17) : demander la suppression de vos données</li>
              <li><strong className="text-foreground">Droit à la portabilité</strong> (article 20) : recevoir vos données dans un format structuré</li>
              <li><strong className="text-foreground">Droit d'opposition</strong> (article 21) : vous opposer au traitement de vos données</li>
              <li><strong className="text-foreground">Droit à la limitation</strong> (article 18) : limiter le traitement dans certaines circonstances</li>
            </ul>
            <p className="text-muted-foreground leading-relaxed mt-3">
              Pour exercer ces droits, contactez-nous à{" "}
              <a href="mailto:infinea.compte@gmail.com" className="text-primary hover:underline">infinea.compte@gmail.com</a>.
              Nous répondrons dans un délai de 30 jours.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">7. Hébergement et sécurité</h2>
            <p className="text-muted-foreground leading-relaxed mb-3">Vos données sont hébergées chez les prestataires suivants :</p>
            <ul className="text-muted-foreground space-y-2 list-disc list-inside">
              <li><strong className="text-foreground">MongoDB Atlas</strong> (base de données) — hébergement AWS, région EU</li>
              <li><strong className="text-foreground">Render</strong> (serveur API) — hébergement aux États-Unis</li>
              <li><strong className="text-foreground">Vercel</strong> (application web) — CDN mondial avec points de présence en Europe</li>
              <li><strong className="text-foreground">Stripe</strong> (paiements) — certifié PCI DSS niveau 1</li>
            </ul>
            <p className="text-muted-foreground leading-relaxed mt-3">
              Les tokens d'intégration sont chiffrés avec l'algorithme AES-256 (Fernet) avant stockage en base de données. Les mots de passe sont hashés avec bcrypt.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">8. Cookies et traceurs</h2>
            <p className="text-muted-foreground leading-relaxed mb-3">InFinea utilise les cookies suivants :</p>
            <ul className="text-muted-foreground space-y-2 list-disc list-inside">
              <li><strong className="text-foreground">Cookies essentiels :</strong> authentification (JWT), préférences de session</li>
              <li><strong className="text-foreground">Cookies analytiques :</strong> PostHog (analyse d'usage anonymisée) — soumis à votre consentement</li>
            </ul>
            <p className="text-muted-foreground leading-relaxed mt-3">
              Vous pouvez à tout moment désactiver les cookies analytiques via les paramètres de votre navigateur.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">9. Transferts de données</h2>
            <p className="text-muted-foreground leading-relaxed">
              Certaines données peuvent être transférées vers les États-Unis (Render, Vercel). Ces transferts sont encadrés par les clauses contractuelles types de la Commission européenne et/ou le Data Privacy Framework EU-US.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">10. Contact et réclamation</h2>
            <p className="text-muted-foreground leading-relaxed">
              Pour toute question relative à la protection de vos données, contactez-nous à{" "}
              <a href="mailto:infinea.compte@gmail.com" className="text-primary hover:underline">infinea.compte@gmail.com</a>.
            </p>
            <p className="text-muted-foreground leading-relaxed mt-3">
              Si vous estimez que le traitement de vos données constitue une violation du RGPD, vous pouvez introduire une réclamation auprès de la{" "}
              <strong className="text-foreground">CNIL</strong> (Commission Nationale de l'Informatique et des Libertés) :{" "}
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
            <span>© 2025 InFinea</span>
            <span className="text-primary">Confidentialité</span>
            <Link to="/cgu" className="hover:text-foreground transition-colors">CGU</Link>
            <a href="mailto:infinea.compte@gmail.com" className="hover:text-foreground transition-colors">Contact</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
