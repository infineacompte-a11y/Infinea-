import React from "react";
import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import InFineaLogo from "@/components/InFineaLogo";

export default function PrivacyPage() {
  return (
    <div className="min-h-screen app-bg-mesh text-[#141E24]">
      {/* Header */}
      <nav className="fixed top-0 w-full z-50 bg-white/80 backdrop-blur-md border-b border-[#E2E6EA]">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <InFineaLogo size={32} withText />
          </Link>
          <Link to="/">
            <Button variant="ghost" size="sm" className="transition-all">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Retour
            </Button>
          </Link>
        </div>
      </nav>

      {/* Content */}
      <main className="pt-24 pb-16 px-4 animate-fade-in">
        <div className="max-w-3xl mx-auto prose prose-sm">
          <h1 className="font-sans font-semibold tracking-tight text-3xl font-bold mb-2 text-[#141E24]">Politique de Confidentialité</h1>
          <p className="text-[#667085] mb-8">Dernière mise à jour : 7 mars 2026</p>

          <section className="mb-8">
            <h2 className="font-sans font-semibold tracking-tight text-xl font-semibold mb-3 text-[#141E24]">1. Responsable du traitement</h2>
            <p className="text-[#667085] leading-relaxed">
              Le responsable du traitement des données collectées sur InFinea est :<br />
              <strong className="text-[#141E24]">InFinea</strong><br />
              Email : <a href="mailto:infinea.compte@gmail.com" className="text-[#459492] hover:text-[#55B3AE] hover:underline transition-colors">infinea.compte@gmail.com</a>
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-sans font-semibold tracking-tight text-xl font-semibold mb-3 text-[#141E24]">2. Données collectées</h2>
            <p className="text-[#667085] leading-relaxed mb-3">
              Dans le cadre de l'utilisation du service, nous collectons les données suivantes :
            </p>
            <ul className="text-[#667085] space-y-2 list-disc list-inside">
              <li><strong className="text-[#141E24]">Données d'inscription :</strong> nom, adresse email, mot de passe (hashé)</li>
              <li><strong className="text-[#141E24]">Données de profil :</strong> objectifs, centres d'intérêt, préférences d'énergie</li>
              <li><strong className="text-[#141E24]">Données d'utilisation :</strong> sessions réalisées, temps investi, progression</li>
              <li><strong className="text-[#141E24]">Données de connexion :</strong> adresse IP, type de navigateur (via cookies analytiques)</li>
              <li><strong className="text-[#141E24]">Données d'intégration :</strong> tokens d'accès aux services tiers (chiffrés AES-256)</li>
              <li><strong className="text-[#141E24]">Données Google Calendar :</strong> informations d'agenda (titre, horaires, durée des événements) — accès en lecture seule</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="font-sans font-semibold tracking-tight text-xl font-semibold mb-3 text-[#141E24]">3. Utilisation des données Google</h2>
            <p className="text-[#667085] leading-relaxed mb-3">
              InFinea utilise l'API Google Calendar avec un accès <strong className="text-[#141E24]">en lecture seule</strong> (scope <code className="text-xs bg-[#F0F7F7] px-1.5 py-0.5 rounded text-[#275255]">calendar.readonly</code>). Cet accès est strictement limité aux finalités suivantes :
            </p>
            <ul className="text-[#667085] space-y-2 list-disc list-inside">
              <li><strong className="text-[#141E24]">Détection de créneaux libres :</strong> lecture de vos événements pour identifier les plages de temps disponibles et vous suggérer des micro-actions adaptées</li>
              <li><strong className="text-[#141E24]">Suggestions contextuelles :</strong> adaptation des recommandations en fonction de la durée de vos créneaux libres</li>
            </ul>
            <p className="text-[#667085] leading-relaxed mt-3">
              <strong className="text-[#141E24]">Ce que nous ne faisons PAS avec vos données Google :</strong>
            </p>
            <ul className="text-[#667085] space-y-2 list-disc list-inside">
              <li>Nous ne modifions, ne créons et ne supprimons aucun événement de votre calendrier</li>
              <li>Nous ne partageons pas vos données Google Calendar avec des tiers</li>
              <li>Nous ne stockons pas le contenu de vos événements de manière permanente — seuls les créneaux horaires sont analysés en temps réel</li>
              <li>Nous n'utilisons pas vos données Google à des fins publicitaires</li>
              <li>Nous ne transférons pas vos données Google à des outils d'intelligence artificielle ou de machine learning non liés au service</li>
            </ul>
            <p className="text-[#667085] leading-relaxed mt-3">
              L'utilisation des données reçues des API Google respecte la{" "}
              <a href="https://developers.google.com/terms/api-services-user-data-policy" className="text-[#459492] hover:text-[#55B3AE] hover:underline transition-colors" target="_blank" rel="noopener noreferrer">
                Politique relative aux données utilisateur des services API Google
              </a>, y compris les exigences d'utilisation limitée (Limited Use requirements).
            </p>
            <p className="text-[#667085] leading-relaxed mt-3">
              Vous pouvez révoquer l'accès d'InFinea à votre Google Calendar à tout moment depuis la page{" "}
              <a href="https://myaccount.google.com/permissions" className="text-[#459492] hover:text-[#55B3AE] hover:underline transition-colors" target="_blank" rel="noopener noreferrer">
                Autorisations de votre compte Google
              </a>{" "}
              ou depuis la page Intégrations de votre compte InFinea.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-sans font-semibold tracking-tight text-xl font-semibold mb-3 text-[#141E24]">4. Finalités du traitement</h2>
            <ul className="text-[#667085] space-y-2 list-disc list-inside">
              <li>Fourniture et personnalisation du service (suggestions IA, micro-actions)</li>
              <li>Gestion de votre compte utilisateur</li>
              <li>Amélioration continue du service et de l'expérience utilisateur</li>
              <li>Communication relative au service (notifications, mises à jour)</li>
              <li>Gestion des paiements et abonnements via Stripe</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="font-sans font-semibold tracking-tight text-xl font-semibold mb-3 text-[#141E24]">5. Base légale du traitement</h2>
            <ul className="text-[#667085] space-y-2 list-disc list-inside">
              <li><strong className="text-[#141E24]">Exécution du contrat :</strong> traitement nécessaire à la fourniture du service (article 6.1.b du RGPD)</li>
              <li><strong className="text-[#141E24]">Consentement :</strong> pour les cookies analytiques et les communications optionnelles (article 6.1.a)</li>
              <li><strong className="text-[#141E24]">Intérêt légitime :</strong> pour l'amélioration du service et la sécurité (article 6.1.f)</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="font-sans font-semibold tracking-tight text-xl font-semibold mb-3 text-[#141E24]">6. Durée de conservation</h2>
            <p className="text-[#667085] leading-relaxed">
              Vos données sont conservées pendant la durée de votre utilisation du service. En cas de suppression de votre compte, vos données personnelles sont supprimées dans un délai de 30 jours, à l'exception des données nécessaires au respect de nos obligations légales (données de facturation : 10 ans).
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-sans font-semibold tracking-tight text-xl font-semibold mb-3 text-[#141E24]">7. Vos droits</h2>
            <p className="text-[#667085] leading-relaxed mb-3">
              Conformément au Règlement Général sur la Protection des Données (RGPD), vous disposez des droits suivants :
            </p>
            <ul className="text-[#667085] space-y-2 list-disc list-inside">
              <li><strong className="text-[#141E24]">Droit d'accès</strong> (article 15) : obtenir une copie de vos données personnelles</li>
              <li><strong className="text-[#141E24]">Droit de rectification</strong> (article 16) : corriger vos données inexactes</li>
              <li><strong className="text-[#141E24]">Droit à l'effacement</strong> (article 17) : demander la suppression de vos données</li>
              <li><strong className="text-[#141E24]">Droit à la portabilité</strong> (article 20) : recevoir vos données dans un format structuré</li>
              <li><strong className="text-[#141E24]">Droit d'opposition</strong> (article 21) : vous opposer au traitement de vos données</li>
              <li><strong className="text-[#141E24]">Droit à la limitation</strong> (article 18) : limiter le traitement dans certaines circonstances</li>
            </ul>
            <p className="text-[#667085] leading-relaxed mt-3">
              Pour exercer ces droits, contactez-nous à{" "}
              <a href="mailto:infinea.compte@gmail.com" className="text-[#459492] hover:text-[#55B3AE] hover:underline transition-colors">infinea.compte@gmail.com</a>.
              Nous répondrons dans un délai de 30 jours.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-sans font-semibold tracking-tight text-xl font-semibold mb-3 text-[#141E24]">8. Suppression de vos données</h2>
            <p className="text-[#667085] leading-relaxed mb-3">
              Vous pouvez demander la suppression de vos données de plusieurs manières :
            </p>
            <ul className="text-[#667085] space-y-2 list-disc list-inside">
              <li><strong className="text-[#141E24]">Suppression du compte :</strong> depuis la page Profil de l'application, vous pouvez supprimer votre compte. Toutes vos données personnelles, y compris vos tokens d'intégration et votre historique de sessions, seront supprimées sous 30 jours</li>
              <li><strong className="text-[#141E24]">Révocation Google Calendar :</strong> vous pouvez déconnecter Google Calendar depuis la page Intégrations ou depuis les{" "}
                <a href="https://myaccount.google.com/permissions" className="text-[#459492] hover:text-[#55B3AE] hover:underline transition-colors" target="_blank" rel="noopener noreferrer">paramètres de votre compte Google</a>. Vos tokens d'accès Google seront immédiatement supprimés de nos serveurs</li>
              <li><strong className="text-[#141E24]">Demande par email :</strong> envoyez un email à{" "}
                <a href="mailto:infinea.compte@gmail.com" className="text-[#459492] hover:text-[#55B3AE] hover:underline transition-colors">infinea.compte@gmail.com</a> pour toute demande de suppression. Nous traiterons votre demande sous 30 jours</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="font-sans font-semibold tracking-tight text-xl font-semibold mb-3 text-[#141E24]">9. Hébergement et sécurité</h2>
            <p className="text-[#667085] leading-relaxed mb-3">Vos données sont hébergées chez les prestataires suivants :</p>
            <ul className="text-[#667085] space-y-2 list-disc list-inside">
              <li><strong className="text-[#141E24]">MongoDB Atlas</strong> (base de données) — hébergement AWS, région EU</li>
              <li><strong className="text-[#141E24]">Render</strong> (serveur API) — hébergement aux États-Unis</li>
              <li><strong className="text-[#141E24]">Vercel</strong> (application web) — CDN mondial avec points de présence en Europe</li>
              <li><strong className="text-[#141E24]">Stripe</strong> (paiements) — certifié PCI DSS niveau 1</li>
            </ul>
            <p className="text-[#667085] leading-relaxed mt-3">
              Les tokens d'intégration sont chiffrés avec l'algorithme AES-256 (Fernet) avant stockage en base de données. Les mots de passe sont hashés avec bcrypt.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-sans font-semibold tracking-tight text-xl font-semibold mb-3 text-[#141E24]">10. Cookies et traceurs</h2>
            <p className="text-[#667085] leading-relaxed mb-3">InFinea utilise les cookies suivants :</p>
            <ul className="text-[#667085] space-y-2 list-disc list-inside">
              <li><strong className="text-[#141E24]">Cookies essentiels :</strong> authentification (JWT), préférences de session</li>
              <li><strong className="text-[#141E24]">Cookies analytiques :</strong> PostHog (analyse d'usage anonymisée) — soumis à votre consentement</li>
            </ul>
            <p className="text-[#667085] leading-relaxed mt-3">
              Vous pouvez à tout moment désactiver les cookies analytiques via les paramètres de votre navigateur.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-sans font-semibold tracking-tight text-xl font-semibold mb-3 text-[#141E24]">11. Transferts de données</h2>
            <p className="text-[#667085] leading-relaxed">
              Certaines données peuvent être transférées vers les États-Unis (Render, Vercel). Ces transferts sont encadrés par les clauses contractuelles types de la Commission européenne et/ou le Data Privacy Framework EU-US.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-sans font-semibold tracking-tight text-xl font-semibold mb-3 text-[#141E24]">12. Contact et réclamation</h2>
            <p className="text-[#667085] leading-relaxed">
              Pour toute question relative à la protection de vos données, contactez-nous à{" "}
              <a href="mailto:infinea.compte@gmail.com" className="text-[#459492] hover:text-[#55B3AE] hover:underline transition-colors">infinea.compte@gmail.com</a>.
            </p>
            <p className="text-[#667085] leading-relaxed mt-3">
              Si vous estimez que le traitement de vos données constitue une violation du RGPD, vous pouvez introduire une réclamation auprès de la{" "}
              <strong className="text-[#141E24]">CNIL</strong> (Commission Nationale de l'Informatique et des Libertés) :{" "}
              <a href="https://www.cnil.fr" className="text-[#459492] hover:text-[#55B3AE] hover:underline transition-colors" target="_blank" rel="noopener noreferrer">www.cnil.fr</a>.
            </p>
          </section>
        </div>
      </main>

      {/* Footer */}
      <footer className="py-8 px-4 border-t border-[#E2E6EA]">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <InFineaLogo size={28} withText />
          <div className="flex items-center gap-6 text-sm text-[#667085]">
            <span>© 2025-2026 InFinea</span>
            <span className="text-[#459492]">Confidentialité</span>
            <Link to="/cgu" className="hover:text-[#141E24] transition-colors">CGU</Link>
            <a href="mailto:infinea.compte@gmail.com" className="hover:text-[#141E24] transition-colors">Contact</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
