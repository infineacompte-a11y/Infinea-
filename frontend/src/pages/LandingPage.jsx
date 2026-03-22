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
  Timer,
  TrendingUp,
} from "lucide-react";

export default function LandingPage() {
  const features = [
    {
      icon: Clock,
      title: "2-15 minutes",
      description: "Micro-actions conçues pour vos temps morts quotidiens",
    },
    {
      icon: Zap,
      title: "IA contextuelle",
      description: "Suggestions adaptées à votre temps et niveau d'énergie",
    },
    {
      icon: TrendingUp,
      title: "Capital-Temps",
      description: "Transformez chaque minute en progrès mesurable",
    },
  ];

  const categories = [
    {
      icon: BookOpen,
      name: "Apprentissage",
      color: "text-blue-500",
      bg: "category-card-learning",
      examples: ["Vocabulaire", "Lecture", "Concepts"],
    },
    {
      icon: Target,
      name: "Productivité",
      color: "text-amber-500",
      bg: "category-card-productivity",
      examples: ["Planning", "Emails", "Brainstorm"],
    },
    {
      icon: Heart,
      name: "Bien-être",
      color: "text-emerald-500",
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
        "Toutes les micro-actions",
        "Suggestions IA illimitées",
        "Statistiques avancées",
        "Actions personnalisées",
        "Support prioritaire",
      ],
      cta: "Essayer Premium",
      popular: true,
    },
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 glass">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
                <Timer className="w-5 h-5 text-primary-foreground" />
              </div>
              <span className="font-heading text-xl font-semibold">InFinea</span>
            </div>
            <div className="hidden md:flex items-center gap-6">
              <a href="#features" className="text-muted-foreground hover:text-foreground transition-colors">
                Fonctionnalités
              </a>
              <a href="#pricing" className="text-muted-foreground hover:text-foreground transition-colors">
                Tarifs
              </a>
              <Link to="/login">
                <Button variant="ghost" data-testid="nav-login-btn">Connexion</Button>
              </Link>
              <Link to="/register">
                <Button data-testid="nav-register-btn" className="rounded-full">
                  Commencer gratuitement
                </Button>
              </Link>
            </div>
            <div className="md:hidden">
              <Link to="/login">
                <Button size="sm" data-testid="mobile-login-btn">Connexion</Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 px-4 overflow-hidden">
        <div className="hero-glow absolute inset-0" />
        <div className="max-w-7xl mx-auto relative">
          <div className="text-center max-w-4xl mx-auto">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 mb-8 animate-fade-in">
              <Sparkles className="w-4 h-4 text-primary" />
              <span className="text-sm text-primary">Nouveau : Suggestions IA personnalisées</span>
            </div>
            
            <h1 className="font-heading text-5xl md:text-7xl font-bold tracking-tight mb-6 animate-fade-in stagger-1">
              Investissez vos
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500"> instants perdus</span>
            </h1>
            
            <p className="text-lg md:text-xl text-muted-foreground mb-10 max-w-2xl mx-auto animate-fade-in stagger-2">
              Transformez vos temps morts en micro-victoires. 2 à 15 minutes suffisent pour apprendre, 
              avancer sur vos projets, ou prendre soin de vous.
            </p>
            
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-fade-in stagger-3">
              <Link to="/register">
                <Button size="lg" className="rounded-full px-8 h-12 text-base btn-lift" data-testid="hero-cta-btn">
                  Commencer gratuitement
                  <ArrowRight className="ml-2 w-5 h-5" />
                </Button>
              </Link>
              <a href="#features">
                <Button variant="outline" size="lg" className="rounded-full px-8 h-12 text-base" data-testid="hero-learn-more-btn">
                  En savoir plus
                </Button>
              </a>
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-4 md:gap-8 mt-20 max-w-3xl mx-auto animate-fade-in stagger-4">
            <div className="text-center">
              <div className="text-3xl md:text-4xl font-heading font-bold text-foreground">2-15</div>
              <div className="text-sm text-muted-foreground mt-1">minutes/session</div>
            </div>
            <div className="text-center">
              <div className="text-3xl md:text-4xl font-heading font-bold text-foreground">+15%</div>
              <div className="text-sm text-muted-foreground mt-1">productivité/an</div>
            </div>
            <div className="text-center">
              <div className="text-3xl md:text-4xl font-heading font-bold text-foreground">100%</div>
              <div className="text-sm text-muted-foreground mt-1">RGPD conforme</div>
            </div>
          </div>
        </div>
      </section>

      {/* Problem Section */}
      <section className="py-20 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="font-heading text-3xl md:text-4xl font-semibold mb-6">
                Le temps, votre ressource la plus précieuse
              </h2>
              <p className="text-muted-foreground text-lg mb-8">
                Chaque jour, nous perdons des dizaines de minutes en "temps morts" : transports, 
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
                    <span className="text-muted-foreground">{item}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="relative">
              <div className="aspect-video rounded-2xl overflow-hidden">
                <img
                  src="https://images.unsplash.com/photo-1579689314629-4e0bdad946e3?crop=entropy&cs=srgb&fm=jpg&q=85&w=800"
                  alt="Commuter looking out train window"
                  className="w-full h-full object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-background to-transparent" />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="font-heading text-3xl md:text-4xl font-semibold mb-4">
              La solution InFinea
            </h2>
            <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
              Une application qui répond à une question simple : "Que puis-je faire maintenant ?"
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6 mb-16">
            {features.map((feature, i) => (
              <Card key={i} className="bg-card border-border hover:border-primary/30 transition-colors">
                <CardContent className="p-6">
                  <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center mb-4">
                    <feature.icon className="w-6 h-6 text-primary" />
                  </div>
                  <h3 className="font-heading text-xl font-medium mb-2">{feature.title}</h3>
                  <p className="text-muted-foreground">{feature.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Categories */}
          <div className="grid md:grid-cols-3 gap-6">
            {categories.map((cat, i) => (
              <Card key={i} className={`${cat.bg} border-border hover:border-opacity-50 transition-all`}>
                <CardContent className="p-6">
                  <cat.icon className={`w-8 h-8 ${cat.color} mb-4`} />
                  <h3 className="font-heading text-xl font-medium mb-3">{cat.name}</h3>
                  <div className="flex flex-wrap gap-2">
                    {cat.examples.map((ex, j) => (
                      <span key={j} className="px-3 py-1 rounded-full bg-white/5 text-sm text-muted-foreground">
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

      {/* How it works */}
      <section className="py-20 px-4 bg-card/50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="font-heading text-3xl md:text-4xl font-semibold mb-4">
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
              <div key={i} className="relative">
                <div className="text-5xl font-heading font-bold text-primary/20 mb-4">{item.step}</div>
                <h3 className="font-heading text-lg font-medium mb-2">{item.title}</h3>
                <p className="text-muted-foreground text-sm">{item.desc}</p>
                {i < 3 && (
                  <ChevronRight className="hidden md:block absolute top-10 -right-4 w-8 h-8 text-primary/30" />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-20 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="font-heading text-3xl md:text-4xl font-semibold mb-4">
              Tarifs simples et transparents
            </h2>
            <p className="text-muted-foreground text-lg">
              Commencez gratuitement, passez en Premium quand vous êtes prêt
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            {pricingPlans.map((plan, i) => (
              <Card
                key={i}
                className={`relative ${plan.popular ? "pricing-card-premium" : "bg-card"} border-border`}
              >
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <span className="px-4 py-1 rounded-full bg-primary text-primary-foreground text-sm font-medium">
                      Populaire
                    </span>
                  </div>
                )}
                <CardContent className="p-8">
                  <h3 className="font-heading text-2xl font-semibold mb-2">{plan.name}</h3>
                  <div className="flex items-baseline gap-1 mb-6">
                    <span className="text-4xl font-heading font-bold">{plan.price}</span>
                    <span className="text-muted-foreground">{plan.period}</span>
                  </div>
                  <ul className="space-y-3 mb-8">
                    {plan.features.map((feature, j) => (
                      <li key={j} className="flex items-center gap-3">
                        <Check className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                        <span className="text-muted-foreground">{feature}</span>
                      </li>
                    ))}
                  </ul>
                  <Link to="/register">
                    <Button
                      className={`w-full rounded-full ${plan.popular ? "" : "bg-secondary text-secondary-foreground hover:bg-secondary/80"}`}
                      data-testid={`pricing-${plan.name.toLowerCase()}-btn`}
                    >
                      {plan.cta}
                    </Button>
                  </Link>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <div className="p-12 rounded-3xl bg-gradient-to-br from-primary/10 via-purple-500/10 to-pink-500/10 border border-primary/20">
            <Brain className="w-16 h-16 text-primary mx-auto mb-6" />
            <h2 className="font-heading text-3xl md:text-4xl font-semibold mb-4">
              Prêt à investir vos instants perdus ?
            </h2>
            <p className="text-muted-foreground text-lg mb-8 max-w-xl mx-auto">
              Rejoignez des milliers d'utilisateurs qui transforment leur temps en Capital-Temps.
            </p>
            <Link to="/register">
              <Button size="lg" className="rounded-full px-8 h-12 text-base btn-lift animate-pulse-glow" data-testid="final-cta-btn">
                Commencer maintenant
                <ArrowRight className="ml-2 w-5 h-5" />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-4 border-t border-border">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
                <Timer className="w-5 h-5 text-primary-foreground" />
              </div>
              <span className="font-heading text-xl font-semibold">InFinea</span>
            </div>
            <div className="flex items-center gap-6 text-sm text-muted-foreground">
              <span>© 2024 InFinea</span>
              <a href="#" className="hover:text-foreground transition-colors">Confidentialité</a>
              <a href="#" className="hover:text-foreground transition-colors">CGU</a>
              <a href="mailto:Infinea.compte@gmail.com" className="hover:text-foreground transition-colors">Contact</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
