import React from "react";
import { Link } from "react-router-dom";
import { Timer, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function CGUPage() {
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
          <h1 className="font-heading text-3xl font-bold mb-2">Conditions Générales d'Utilisation</h1>
          <p className="text-muted-foreground mb-8">Dernière mise à jour : 28 février 2025</p>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">1. Objet</h2>
            <p className="text-muted-foreground leading-relaxed">
              Les présentes Conditions Générales d'Utilisation (ci-après « CGU ») régissent l'accès et l'utilisation de la plateforme InFinea, accessible à l'adresse{" "}
              <a href="https://infinea.vercel.app" className="text-primary hover:underline">infinea.vercel.app</a>.
              InFinea est un service de productivité personnelle qui aide ses utilisateurs à transformer leurs temps morts en micro-actions productives, grâce à des suggestions personnalisées par intelligence artificielle.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">2. Acceptation des CGU</h2>
            <p className="text-muted-foreground leading-relaxed">
              L'inscription et l'utilisation du service impliquent l'acceptation pleine et entière des présentes CGU. Si vous n'acceptez pas ces conditions, vous ne devez pas utiliser le service. InFinea se réserve le droit de modifier les présentes CGU à tout moment. Les utilisateurs seront informés de toute modification substantielle par email ou notification dans l'application.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">3. Accès au service</h2>
            <p className="text-muted-foreground leading-relaxed mb-3">
              L'accès au service nécessite la création d'un compte utilisateur. Pour créer un compte, vous devez :
            </p>
            <ul className="text-muted-foreground space-y-2 list-disc list-inside">
              <li>Être âgé d'au moins 16 ans</li>
              <li>Fournir une adresse email valide</li>
              <li>Créer un mot de passe sécurisé ou vous authentifier via Google</li>
              <li>Ne créer qu'un seul compte par personne</li>
            </ul>
            <p className="text-muted-foreground leading-relaxed mt-3">
              Vous êtes responsable de la confidentialité de vos identifiants de connexion et de toute activité effectuée depuis votre compte.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">4. Description du service</h2>
            <p className="text-muted-foreground leading-relaxed mb-3">InFinea propose les fonctionnalités suivantes :</p>
            <ul className="text-muted-foreground space-y-2 list-disc list-inside">
              <li><strong className="text-foreground">Micro-actions :</strong> catalogue de plus de 300 actions courtes (2-15 minutes) dans les domaines de l'apprentissage, de la productivité et du bien-être</li>
              <li><strong className="text-foreground">Suggestions IA :</strong> recommandations personnalisées basées sur votre profil, votre niveau d'énergie et le temps disponible</li>
              <li><strong className="text-foreground">Suivi de progression :</strong> tableau de bord, Capital-Temps, séries quotidiennes</li>
              <li><strong className="text-foreground">Intégrations :</strong> connexion à des services tiers (Google Calendar, Notion, Todoist, Slack, iCal) pour une expérience enrichie</li>
              <li><strong className="text-foreground">Journal :</strong> historique de vos sessions et débriefs</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">5. Offres et tarifs</h2>
            <p className="text-muted-foreground leading-relaxed mb-3">InFinea propose deux niveaux de service :</p>
            <ul className="text-muted-foreground space-y-2 list-disc list-inside">
              <li><strong className="text-foreground">Offre Gratuite :</strong> accès aux micro-actions de base, suggestions IA limitées, suivi de progression</li>
              <li><strong className="text-foreground">Offre Premium (6,99 €/mois) :</strong> suggestions IA illimitées, accès à toutes les micro-actions, intégrations complètes, statistiques détaillées</li>
            </ul>
            <p className="text-muted-foreground leading-relaxed mt-3">
              Les paiements sont gérés par Stripe. L'abonnement Premium est renouvelé automatiquement chaque mois. Vous pouvez annuler à tout moment depuis votre profil ; l'accès Premium reste actif jusqu'à la fin de la période payée.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">6. Obligations de l'utilisateur</h2>
            <p className="text-muted-foreground leading-relaxed mb-3">En utilisant InFinea, vous vous engagez à :</p>
            <ul className="text-muted-foreground space-y-2 list-disc list-inside">
              <li>Fournir des informations exactes lors de l'inscription</li>
              <li>Ne pas utiliser le service à des fins illicites ou contraires aux présentes CGU</li>
              <li>Ne pas tenter d'accéder de manière non autorisée aux systèmes d'InFinea</li>
              <li>Ne pas perturber le fonctionnement du service</li>
              <li>Respecter les droits de propriété intellectuelle d'InFinea et des tiers</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">7. Propriété intellectuelle</h2>
            <p className="text-muted-foreground leading-relaxed">
              L'ensemble des éléments constituant le service InFinea (textes, graphismes, logiciels, images, marques, logos) sont protégés par le droit de la propriété intellectuelle. Toute reproduction, représentation ou exploitation non autorisée est interdite.
              Les contenus générés par l'IA à destination de l'utilisateur restent à l'usage personnel de celui-ci.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">8. Responsabilité</h2>
            <p className="text-muted-foreground leading-relaxed mb-3">
              InFinea s'efforce d'assurer la disponibilité et le bon fonctionnement du service. Toutefois :
            </p>
            <ul className="text-muted-foreground space-y-2 list-disc list-inside">
              <li>Le service est fourni « en l'état », sans garantie d'absence d'interruption ou d'erreur</li>
              <li>Les suggestions IA sont indicatives et ne constituent pas des conseils professionnels (médicaux, financiers ou autres)</li>
              <li>InFinea ne saurait être tenu responsable des dommages indirects résultant de l'utilisation du service</li>
              <li>Les intégrations tierces sont soumises aux conditions de leurs fournisseurs respectifs</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">9. Données personnelles</h2>
            <p className="text-muted-foreground leading-relaxed">
              Le traitement de vos données personnelles est détaillé dans notre{" "}
              <Link to="/privacy" className="text-primary hover:underline">Politique de Confidentialité</Link>.
              En utilisant InFinea, vous acceptez ce traitement conformément au Règlement Général sur la Protection des Données (RGPD).
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">10. Résiliation</h2>
            <p className="text-muted-foreground leading-relaxed">
              Vous pouvez supprimer votre compte à tout moment depuis les paramètres de votre profil. InFinea se réserve le droit de suspendre ou supprimer un compte en cas de violation des présentes CGU, après notification préalable sauf cas d'urgence.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">11. Modification des CGU</h2>
            <p className="text-muted-foreground leading-relaxed">
              InFinea se réserve le droit de modifier les présentes CGU à tout moment. Les modifications prennent effet dès leur publication. L'utilisation continue du service après modification vaut acceptation des nouvelles CGU. En cas de modification substantielle, les utilisateurs seront informés par email au moins 30 jours avant l'entrée en vigueur.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">12. Droit applicable</h2>
            <p className="text-muted-foreground leading-relaxed">
              Les présentes CGU sont régies par le droit français. En cas de litige, les parties s'engagent à rechercher une solution amiable. À défaut, les tribunaux français seront seuls compétents.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="font-heading text-xl font-semibold mb-3">13. Contact</h2>
            <p className="text-muted-foreground leading-relaxed">
              Pour toute question relative aux présentes CGU, contactez-nous à{" "}
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
            <span>© 2025 InFinea</span>
            <Link to="/privacy" className="hover:text-foreground transition-colors">Confidentialité</Link>
            <span className="text-primary">CGU</span>
            <a href="mailto:infinea.compte@gmail.com" className="hover:text-foreground transition-colors">Contact</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
