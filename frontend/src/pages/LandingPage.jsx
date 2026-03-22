import React from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Clock,
  Zap,
  Heart,
  BookOpen,
  Target,
  Brain,
  ChevronRight,
  Check,
  ArrowRight,
  Sparkles,
  TrendingUp,
} from "lucide-react";
import InFineaLogo from "@/components/InFineaLogo";

export default function LandingPage() {
  const features = [
    {
      icon: Clock,
      title: "2-15 minutes",
      description: "Des micro-actions pour chaque instant libre, puisées dans une bibliothèque en perpétuelle évolution",
    },
    {
      icon: Zap,
      title: "IA qui vous connait",
      description: "Des suggestions personnalisées selon vos habitudes, votre énergie et le moment de la journée",
    },
    {
      icon: TrendingUp,
      title: "Capital-Temps",
      description: "Chaque session enrichit votre profil. Plus vous agissez, plus l'IA devient pertinente",
    },
  ];

  const categories = [
    {
      icon: BookOpen,
      name: "Apprentissage",
      color: "text-[#459492]",
      bg: "category-card-learning",
      examples: ["Vocabulaire", "Lecture", "Concepts"],
    },
    {
      icon: Target,
      name: "Productivité",
      color: "text-[#E48C75]",
      bg: "category-card-productivity",
      examples: ["Planning", "Emails", "Brainstorm"],
    },
    {
      icon: Heart,
      name: "Bien-être",
      color: "text-[#5DB786]",
      bg: "category-card-well-being",
      examples: ["Respiration", "Méditation", "Étirements"],
    },
  ];

  const pricingPlans = [
    {
      name: "Gratuit",
      price: "0€",
      period: "",
      features: [
        "Accès aux micro-actions de base",
        "Suggestions IA limitées",
        "Suivi de progression",
        "3 catégories d'actions",
      ],
      cta: "Commencer",
      popular: false,
    },
    {
      name: "Premium",
      price: "6,99€",
      period: "/mois",
      features: [
        "700+ actions (11 catégories)",
        "IA avancée avec suggestions personnalisées",
        "Suggestion proactive au bon moment",
        "Bouclier de Streak (1x/semaine)",
        "Analytics avancées & insights",
        "20 badges Premium",
      ],
      cta: "Découvrir Premium",
      popular: true,
      link: "/pricing",
    },
  ];

  return (
    <div className="min-h-screen app-bg-mesh">
      {/* Navigation — frosted glass, Revolut-style */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-[#275255]/80 backdrop-blur-2xl border-b border-white/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <InFineaLogo size={32} withText animate variant="light" />
            <div className="hidden md:flex items-center gap-6">
              <a href="#features" className="text-white/70 hover:text-white transition-colors text-sm">
                Fonctionnalités
              </a>
              <Link to="/pricing" className="text-white/70 hover:text-white transition-colors text-sm">
                Tarifs
              </Link>
              <Link to="/login">
                <Button variant="ghost" data-testid="nav-login-btn" className="text-white/80 hover:text-white hover:bg-white/10">Connexion</Button>
              </Link>
              <Link to="/register">
                <Button data-testid="nav-register-btn" className="rounded-full bg-white text-[#275255] hover:bg-white/90 font-medium">
                  Commencer gratuitement
                </Button>
              </Link>
            </div>
            <div className="md:hidden">
              <Link to="/login">
                <Button size="sm" data-testid="mobile-login-btn" className="rounded-full bg-white text-[#275255] hover:bg-white/90">Connexion</Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section — Immersive dark teal, Revolut-level impact */}
      <section className="relative pt-32 pb-28 px-4 overflow-hidden bg-gradient-to-b from-[#1F3F42] via-[#275255] to-[#2F6669]">
        {/* Rich decorative gradients */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_60%_at_20%_80%,rgba(85,179,174,0.20),transparent_60%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_60%_50%_at_80%_20%,rgba(93,183,134,0.12),transparent_60%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_40%_40%_at_50%_10%,rgba(69,148,146,0.15),transparent_50%)]" />
        <div className="max-w-7xl mx-auto relative">
          <div className="text-center max-w-4xl mx-auto">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/8 border border-white/15 mb-8 animate-fade-in">
              <Sparkles className="w-4 h-4 text-[#7DD3D0]" />
              <span className="text-sm text-white/80">Une IA qui apprend de vous, une bibliothèque qui grandit sans cesse</span>
            </div>

            <h1 className="text-display text-5xl sm:text-6xl md:text-8xl font-bold mb-6 text-white animate-fade-in stagger-1">
              Investissez vos
              <br />
              <span className="text-gradient-light">instants perdus</span>
            </h1>

            <p className="text-lg md:text-xl text-white/60 mb-12 max-w-2xl mx-auto animate-fade-in stagger-2 leading-relaxed">
              Transformez votre temps disponible en micro-victoires. Une bibliothèque de micro-actions en perpétuelle évolution,
              portée par une IA qui s'adapte à vos habitudes, votre énergie et votre rythme.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-fade-in stagger-3">
              <Link to="/register">
                <button className="btn-pill-white h-12 px-8 text-base font-semibold shadow-lg hover:shadow-xl" data-testid="hero-cta-btn">
                  Commencer gratuitement
                  <ArrowRight className="w-5 h-5" />
                </button>
              </Link>
              <a href="#features">
                <button className="inline-flex items-center gap-2 h-12 px-8 rounded-full border border-white/25 text-white/90 text-base font-medium hover:bg-white/10 hover:border-white/35 transition-all" data-testid="hero-learn-more-btn">
                  En savoir plus
                </button>
              </a>
            </div>
          </div>

          {/* Stats — glass cards on hero */}
          <div className="grid grid-cols-3 gap-2 sm:gap-4 md:gap-6 mt-16 sm:mt-20 max-w-3xl mx-auto animate-fade-in stagger-4">
            <div className="card-on-dark text-center rounded-xl sm:rounded-2xl py-3 px-1.5 sm:py-5 sm:px-4">
              <div className="text-2xl sm:text-3xl md:text-4xl font-sans font-semibold tracking-tight font-bold text-white">2-15</div>
              <div className="text-[9px] sm:text-xs text-white/50 mt-1 sm:mt-1.5 uppercase tracking-normal sm:tracking-wider leading-tight">minutes</div>
            </div>
            <div className="card-on-dark text-center rounded-xl sm:rounded-2xl py-3 px-1.5 sm:py-5 sm:px-4">
              <div className="text-2xl sm:text-3xl md:text-4xl font-sans font-semibold tracking-tight font-bold text-white">700+</div>
              <div className="text-[9px] sm:text-xs text-white/50 mt-1 sm:mt-1.5 uppercase tracking-normal sm:tracking-wider leading-tight">actions</div>
            </div>
            <div className="card-on-dark text-center rounded-xl sm:rounded-2xl py-3 px-1.5 sm:py-5 sm:px-4">
              <div className="text-2xl sm:text-3xl md:text-4xl font-sans font-semibold tracking-tight font-bold text-white">100%</div>
              <div className="text-[9px] sm:text-xs text-white/50 mt-1 sm:mt-1.5 uppercase tracking-normal sm:tracking-wider leading-tight">RGPD</div>
            </div>
          </div>
        </div>
      </section>

      {/* Problem Section — white background */}
      <section className="py-24 px-4 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-display text-3xl md:text-5xl font-semibold mb-6 text-[#141E24]">
                Le temps, votre ressource la plus précieuse
              </h2>
              <p className="text-[#667085] text-lg mb-8">
                Chaque jour, des dizaines de minutes de temps disponible s'envolent : transports,
                files d'attente, pauses entre réunions. Ces moments fragmentés semblent trop courts
                pour être utiles.
              </p>
              <div className="space-y-4">
                {[
                  "2 à 15 minutes perdues, plusieurs fois par jour",
                  "Trop court pour être productif, trop long pour ne rien faire",
                  "Surcharge cognitive face aux nombreuses apps",
                ].map((item, i) => (
                  <div key={i} className="flex items-start gap-3">
                    <div className="w-5 h-5 rounded-full bg-destructive/20 flex items-center justify-center mt-0.5">
                      <div className="w-2 h-2 rounded-full bg-destructive" />
                    </div>
                    <span className="text-[#667085]">{item}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="relative">
              <div className="aspect-video rounded-2xl overflow-hidden shadow-lg">
                <img
                  src="https://images.unsplash.com/photo-1579689314629-4e0bdad946e3?crop=entropy&cs=srgb&fm=jpg&q=85&w=800"
                  alt="Commuter looking out train window"
                  className="w-full h-full object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent" />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section — light teal surface */}
      <section id="features" className="py-24 px-4 bg-[#F0F7F7] section-edge-top">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-display text-3xl md:text-5xl font-semibold mb-4 text-[#141E24]">
              La solution InFinea
            </h2>
            <p className="text-[#667085] text-lg max-w-2xl mx-auto">
              Une bibliothèque infinie de micro-actions, une IA qui apprend de vous. Que faire maintenant ? InFinea sait.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6 mb-16">
            {features.map((feature, i) => (
              <Card key={i} className="group bg-white shadow-md hover:shadow-xl rounded-2xl border border-[#E2E6EA]/50 hover:border-[#459492]/20 hover:-translate-y-1 transition-all duration-300">
                <CardContent className="p-6">
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#459492]/10 to-[#55B3AE]/5 flex items-center justify-center mb-4 group-hover:scale-110 group-hover:shadow-[0_0_20px_rgba(69,148,146,0.15)] transition-all duration-300">
                    <feature.icon className="w-6 h-6 text-[#459492]" />
                  </div>
                  <h3 className="font-sans font-semibold tracking-tight text-xl font-semibold mb-2 text-[#141E24]">{feature.title}</h3>
                  <p className="text-[#667085] leading-relaxed">{feature.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Categories */}
          <div className="grid md:grid-cols-3 gap-6">
            {categories.map((cat, i) => (
              <Card key={i} className="group bg-white shadow-md hover:shadow-lg rounded-2xl border border-[#E2E6EA]/50 hover:-translate-y-1 transition-all duration-300">
                <CardContent className="p-6">
                  <cat.icon className={`w-8 h-8 ${cat.color} mb-4 group-hover:scale-110 transition-transform duration-300`} />
                  <h3 className="font-sans font-semibold tracking-tight text-xl font-medium mb-3 text-[#141E24]">{cat.name}</h3>
                  <div className="flex flex-wrap gap-2">
                    {cat.examples.map((ex, j) => (
                      <span key={j} className="px-3 py-1 rounded-full bg-[#F8FAFB] border border-[#E2E6EA] text-sm text-[#667085]">
                        {ex}
                      </span>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* How it works — dark teal block for visual rhythm */}
      <section className="py-24 px-4 bg-gradient-to-b from-[#1F3F42] to-[#275255]">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-display text-3xl md:text-5xl font-semibold mb-4 text-white">
              Comment ça marche
            </h2>
          </div>

          <div className="grid md:grid-cols-4 gap-8">
            {[
              { step: "01", title: "Ouvrez l'app", desc: "En moins de 60 secondes" },
              { step: "02", title: "Indiquez votre temps", desc: "De 2 à 15 minutes" },
              { step: "03", title: "Choisissez l'énergie", desc: "Basse, moyenne ou haute" },
              { step: "04", title: "Agissez !", desc: "L'IA vous guide" },
            ].map((item, i) => (
              <div key={i} className="relative group hover:-translate-y-1 transition-all duration-300">
                <div className="w-14 h-14 rounded-2xl bg-white/10 border border-white/10 flex items-center justify-center mb-4 group-hover:bg-white/15 group-hover:border-white/20 group-hover:shadow-[0_0_20px_rgba(125,211,208,0.15)] transition-all duration-300">
                  <span className="text-xl font-sans font-semibold tracking-tight font-bold text-[#7DD3D0]">{item.step}</span>
                </div>
                <h3 className="font-sans font-semibold tracking-tight text-lg font-semibold mb-2 text-white">{item.title}</h3>
                <p className="text-white/60 text-sm leading-relaxed">{item.desc}</p>
                {i < 3 && (
                  <ChevronRight className="hidden md:block absolute top-6 -right-4 w-6 h-6 text-white/20" />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section — dark background, white cards (Revolut-style) */}
      <section id="pricing" className="py-24 px-4 bg-gradient-to-b from-[#275255] to-[#1F3F42]">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-display text-3xl md:text-5xl font-semibold mb-4 text-white">
              Tarifs simples et transparents
            </h2>
            <p className="text-white/60 text-lg">
              Commencez gratuitement, passez Premium pour une IA qui s'adapte à vous
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            {pricingPlans.map((plan, i) => (
              <Card
                key={i}
                className={`relative bg-white hover:shadow-2xl rounded-2xl transition-all duration-300 hover:-translate-y-1 ${plan.popular ? "border-2 border-[#459492] shadow-xl ring-1 ring-[#459492]/20" : "border border-[#E2E6EA] shadow-lg"}`}
              >
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <span className="premium-badge px-4 py-1 rounded-full text-white text-sm font-medium shadow-lg">
                      Populaire
                    </span>
                  </div>
                )}
                <CardContent className="p-8">
                  <h3 className="font-sans font-semibold tracking-tight text-2xl font-semibold mb-2 text-[#141E24]">{plan.name}</h3>
                  <div className="flex items-baseline gap-1 mb-6">
                    <span className="text-4xl font-sans font-semibold tracking-tight font-bold text-[#141E24]">{plan.price}</span>
                    <span className="text-[#667085]">{plan.period}</span>
                  </div>
                  <ul className="space-y-3 mb-8">
                    {plan.features.map((feature, j) => (
                      <li key={j} className="flex items-center gap-3">
                        <Check className="w-5 h-5 text-[#5DB786] flex-shrink-0" />
                        <span className="text-[#667085]">{feature}</span>
                      </li>
                    ))}
                  </ul>
                  <Link to={plan.link || "/register"}>
                    <button
                      className={`w-full h-11 rounded-full font-medium transition-all btn-press ${plan.popular ? "btn-pill-primary" : "bg-[#F0F7F7] text-[#275255] hover:bg-[#E2E6EA] rounded-full"}`}
                      data-testid={`pricing-${plan.name.toLowerCase()}-btn`}
                    >
                      {plan.cta}
                    </button>
                  </Link>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section — immersive dark with glow */}
      <section className="py-28 px-4 bg-gradient-to-b from-[#1F3F42] to-[#163233] relative overflow-hidden">
        {/* Ambient glow */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_60%_60%_at_50%_50%,rgba(85,179,174,0.18),transparent_70%)]" />
        <div className="max-w-4xl mx-auto text-center relative">
          <div className="w-16 h-16 rounded-2xl bg-white/10 border border-white/15 flex items-center justify-center mx-auto mb-8">
            <Brain className="w-8 h-8 text-[#7DD3D0]" />
          </div>
          <h2 className="text-display text-3xl md:text-5xl font-semibold mb-5 text-white">
            Prêt à investir vos instants perdus ?
          </h2>
          <p className="text-white/55 text-lg mb-10 max-w-xl mx-auto leading-relaxed">
            Commencez dès maintenant à transformer votre temps en Capital-Temps.
          </p>
          <Link to="/register">
            <button className="btn-pill-white h-13 px-10 text-base font-semibold shadow-lg hover:shadow-2xl" data-testid="final-cta-btn">
              Commencer maintenant
              <ArrowRight className="w-5 h-5" />
            </button>
          </Link>
        </div>
      </section>

      {/* Footer — dark primary background for contrast */}
      <footer className="py-12 px-4 bg-[#275255]">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <InFineaLogo size={32} withText variant="light" />
            <div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-sm text-white/70">
              <span>&copy; 2025 InFinea</span>
              <Link to="/privacy" className="hover:text-white transition-colors">Confidentialité</Link>
              <Link to="/cgu" className="hover:text-white transition-colors">CGU</Link>
              <a href="mailto:Infinea.compte@gmail.com" className="hover:text-white transition-colors">Contact</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
