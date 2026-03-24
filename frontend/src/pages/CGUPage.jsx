import React from "react";
import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import InFineaLogo from "@/components/InFineaLogo";

export default function CGUPage() {
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
          <h1 className="font-sans font-semibold tracking-tight text-3xl font-bold mb-2 text-[#141E24]">Conditions Générales d'Utilisation</h1>
          <p className="text-[#667085] mb-8">Dernière mise à jour : 7 mars 2026</p>

          <section className="mb-8">
            <h2 className="font-sans font-semibold tracking-tight text-xl font-semibold mb-3 text-[#141E24]">1. Objet</h2>
            <p className="text-[#667085] leading-relaxed">
              Les présentes Conditions Générales d'Utilisation (ci-après « CGU ») régissent l'accès et l'utilisation de la plateforme InFinea, accessible à l'adresse{" "}
              <a href="https://infinea.app" className="text-[#459492] hover:text-[#55B3AE] hover:underline transition-colors">infinea.app</a>.
              InFinea est un service de productivité personnelle qui aide ses utilisateurs à transformer leur temps disponible en micro-actions productives, grâce à des suggestions personnalisées par intelligence artificielle.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-sans font-semibold tracking-tight text-xl font-semibold mb-3 text-[#141E24]">2. Acceptation des CGU</h2>
            <p className="text-[#667085] leading-relaxed">
              L'inscription et l'utilisation du service impliquent l'acceptation pleine et entière des présentes CGU. Si vous n'acceptez pas ces conditions, vous ne devez pas utiliser le service. InFinea se réserve le droit de modifier les présentes CGU à tout moment. Les utilisateurs seront informés de toute modification substantielle par email ou notification dans l'application.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-sans font-semibold tracking-tight text-xl font-semibold mb-3 text-[#141E24]">3. Accès au service</h2>
            <p className="text-[#667085] leading-relaxed mb-3">
              L'accès au service nécessite la création d'un compte utilisateur. Pour créer un compte, vous devez :
            </p>
            <ul className="text-[#667085] space-y-2 list-disc list-inside">
              <li>Être âgé d'au moins 16 ans</li>
              <li>Fournir une adresse email valide</li>
              <li>Créer un mot de passe sécurisé ou vous authentifier via Google</li>
              <li>Ne créer qu'un seul compte par personne</li>
            </ul>
            <p className="text-[#667085] leading-relaxed mt-3">
              Vous êtes responsable de la confidentialité de vos identifiants de connexion et de toute activité effectuée depuis votre compte.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-sans font-semibold tracking-tight text-xl font-semibold mb-3 text-[#141E24]">4. Description du service</h2>
            <p className="text-[#667085] leading-relaxed mb-3">InFinea propose les fonctionnalités suivantes :</p>
            <ul className="text-[#667085] space-y-2 list-disc list-inside">
              <li><strong className="text-[#141E24]">Micro-actions :</strong> catalogue de plus de 300 actions courtes (2-15 minutes) dans les domaines de l'apprentissage, de la productivité et du bien-être</li>
              <li><strong className="text-[#141E24]">Suggestions IA :</strong> recommandations personnalisées basées sur votre profil, votre niveau d'énergie et le temps disponible</li>
              <li><strong className="text-[#141E24]">Suivi de progression :</strong> tableau de bord, Capital-Temps, séries quotidiennes</li>
              <li><strong className="text-[#141E24]">Intégrations :</strong> connexion à des services tiers (Google Calendar, Notion, Todoist, Slack, iCal) pour une expérience enrichie</li>
              <li><strong className="text-[#141E24]">Journal :</strong> historique de vos sessions et débriefs</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="font-sans font-semibold tracking-tight text-xl font-semibold mb-3 text-[#141E24]">5. Offres et tarifs</h2>
            <p className="text-[#667085] leading-relaxed mb-3">InFinea propose deux niveaux de service :</p>
            <ul className="text-[#667085] space-y-2 list-disc list-inside">
              <li><strong className="text-[#141E24]">Offre Gratuite :</strong> accès aux micro-actions de base, suggestions IA limitées, suivi de progression</li>
              <li><strong className="text-[#141E24]">Offre Premium (6,99 €/mois) :</strong> suggestions IA illimitées, accès à toutes les micro-actions, intégrations complètes, statistiques détaillées</li>
            </ul>
            <p className="text-[#667085] leading-relaxed mt-3">
              Les paiements sont gérés par Stripe. L'abonnement Premium est renouvelé automatiquement chaque mois. Vous pouvez annuler à tout moment depuis votre profil ; l'accès Premium reste actif jusqu'à la fin de la période payée.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-sans font-semibold tracking-tight text-xl font-semibold mb-3 text-[#141E24]">6. Obligations de l'utilisateur</h2>
            <p className="text-[#667085] leading-relaxed mb-3">En utilisant InFinea, vous vous engagez à :</p>
            <ul className="text-[#667085] space-y-2 list-disc list-inside">
              <li>Fournir des informations exactes lors de l'inscription</li>
              <li>Ne pas utiliser le service à des fins illicites ou contraires aux présentes CGU</li>
              <li>Ne pas tenter d'accéder de manière non autorisée aux systèmes d'InFinea</li>
              <li>Ne pas perturber le fonctionnement du service</li>
              <li>Respecter les droits de propriété intellectuelle d'InFinea et des tiers</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="font-sans font-semibold tracking-tight text-xl font-semibold mb-3 text-[#141E24]">7. Propriété intellectuelle</h2>
            <p className="text-[#667085] leading-relaxed">
              L'ensemble des éléments constituant le service InFinea (textes, graphismes, logiciels, images, marques, logos) sont protégés par le droit de la propriété intellectuelle. Toute reproduction, représentation ou exploitation non autorisée est interdite.
              Les contenus générés par l'IA à destination de l'utilisateur restent à l'usage personnel de celui-ci.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-sans font-semibold tracking-tight text-xl font-semibold mb-3 text-[#141E24]">8. Responsabilité</h2>
            <p className="text-[#667085] leading-relaxed mb-3">
              InFinea s'efforce d'assurer la disponibilité et le bon fonctionnement du service. Toutefois :
            </p>
            <ul className="text-[#667085] space-y-2 list-disc list-inside">
              <li>Le service est fourni « en l'état », sans garantie d'absence d'interruption ou d'erreur</li>
              <li>Les suggestions IA sont indicatives et ne constituent pas des conseils professionnels (médicaux, financiers ou autres)</li>
              <li>InFinea ne saurait être tenu responsable des dommages indirects résultant de l'utilisation du service</li>
              <li>Les intégrations tierces sont soumises aux conditions de leurs fournisseurs respectifs</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="font-sans font-semibold tracking-tight text-xl font-semibold mb-3 text-[#141E24]">9. Données personnelles</h2>
            <p className="text-[#667085] leading-relaxed">
              Le traitement de vos données personnelles est détaillé dans notre{" "}
              <Link to="/privacy" className="text-[#459492] hover:text-[#55B3AE] hover:underline transition-colors">Politique de Confidentialité</Link>.
              En utilisant InFinea, vous acceptez ce traitement conformément au Règlement Général sur la Protection des Données (RGPD).
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-sans font-semibold tracking-tight text-xl font-semibold mb-3 text-[#141E24]">10. Résiliation</h2>
            <p className="text-[#667085] leading-relaxed">
              Vous pouvez supprimer votre compte à tout moment depuis les paramètres de votre profil. InFinea se réserve le droit de suspendre ou supprimer un compte en cas de violation des présentes CGU, après notification préalable sauf cas d'urgence.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-sans font-semibold tracking-tight text-xl font-semibold mb-3 text-[#141E24]">11. Modification des CGU</h2>
            <p className="text-[#667085] leading-relaxed">
              InFinea se réserve le droit de modifier les présentes CGU à tout moment. Les modifications prennent effet dès leur publication. L'utilisation continue du service après modification vaut acceptation des nouvelles CGU. En cas de modification substantielle, les utilisateurs seront informés par email au moins 30 jours avant l'entrée en vigueur.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-sans font-semibold tracking-tight text-xl font-semibold mb-3 text-[#141E24]">12. Droit applicable</h2>
            <p className="text-[#667085] leading-relaxed">
              Les présentes CGU sont régies par le droit français. En cas de litige, les parties s'engagent à rechercher une solution amiable. À défaut, les tribunaux français seront seuls compétents.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-sans font-semibold tracking-tight text-xl font-semibold mb-3 text-[#141E24]">13. Contact</h2>
            <p className="text-[#667085] leading-relaxed">
              Pour toute question relative aux présentes CGU, contactez-nous à{" "}
              <a href="mailto:infinea.compte@gmail.com" className="text-[#459492] hover:text-[#55B3AE] hover:underline transition-colors">infinea.compte@gmail.com</a>.
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
            <Link to="/privacy" className="hover:text-[#141E24] transition-colors">Confidentialité</Link>
            <span className="text-[#459492]">CGU</span>
            <a href="mailto:infinea.compte@gmail.com" className="hover:text-[#141E24] transition-colors">Contact</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
