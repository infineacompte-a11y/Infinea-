import React from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
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
import LanguageSelector from "@/components/LanguageSelector";

const FEATURE_ICONS = [
  { icon: Clock, key: "time" },
  { icon: Zap, key: "ai" },
  { icon: TrendingUp, key: "capital" },
];

const CATEGORY_META = [
  { icon: BookOpen, color: "text-blue-500", bg: "category-card-learning", key: "learning" },
  { icon: Target, color: "text-amber-500", bg: "category-card-productivity", key: "productivity" },
  { icon: Heart, color: "text-emerald-500", bg: "category-card-well-being", key: "wellBeing" },
];

const STEPS = ["step1", "step2", "step3", "step4"];

export default function LandingPage() {
  const { t } = useTranslation();

  const pricingPlans = [
    {
      key: "free",
      popular: false,
      link: "/register",
      featureKeys: ["feature1", "feature2", "feature3", "feature4"],
    },
    {
      key: "premium",
      popular: true,
      link: "/pricing",
      featureKeys: ["feature1", "feature2", "feature3", "feature4", "feature5", "feature6"],
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
                {t("landing.nav.features")}
              </a>
              <Link to="/pricing" className="text-muted-foreground hover:text-foreground transition-colors">
                {t("landing.nav.pricing")}
              </Link>
              <Link to="/login">
                <Button variant="ghost" data-testid="nav-login-btn">{t("landing.nav.login")}</Button>
              </Link>
              <Link to="/register">
                <Button data-testid="nav-register-btn" className="rounded-full">
                  {t("landing.nav.getStarted")}
                </Button>
              </Link>
            </div>
            <div className="md:hidden">
              <Link to="/login">
                <Button size="sm" data-testid="mobile-login-btn">{t("landing.nav.login")}</Button>
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
              <span className="text-sm text-primary">{t("landing.hero.badge")}</span>
            </div>

            <h1 className="font-heading text-4xl sm:text-5xl md:text-7xl font-bold tracking-tight mb-6 animate-fade-in stagger-1">
              {t("landing.hero.titleStart")}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500">{t("landing.hero.titleHighlight")}</span>
            </h1>

            <p className="text-lg md:text-xl text-muted-foreground mb-10 max-w-2xl mx-auto animate-fade-in stagger-2">
              {t("landing.hero.subtitle")}
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-fade-in stagger-3">
              <Link to="/register">
                <Button size="lg" className="rounded-full px-8 h-12 text-base btn-lift" data-testid="hero-cta-btn">
                  {t("landing.hero.cta")}
                  <ArrowRight className="ml-2 w-5 h-5" />
                </Button>
              </Link>
              <a href="#features">
                <Button variant="outline" size="lg" className="rounded-full px-8 h-12 text-base" data-testid="hero-learn-more-btn">
                  {t("landing.hero.learnMore")}
                </Button>
              </a>
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-4 md:gap-8 mt-20 max-w-3xl mx-auto animate-fade-in stagger-4">
            <div className="text-center">
              <div className="text-3xl md:text-4xl font-heading font-bold text-foreground">{t("landing.stats.timeValue")}</div>
              <div className="text-sm text-muted-foreground mt-1">{t("landing.stats.timeLabel")}</div>
            </div>
            <div className="text-center">
              <div className="text-3xl md:text-4xl font-heading font-bold text-foreground">{t("landing.stats.actionsValue")}</div>
              <div className="text-sm text-muted-foreground mt-1">{t("landing.stats.actionsLabel")}</div>
            </div>
            <div className="text-center">
              <div className="text-3xl md:text-4xl font-heading font-bold text-foreground">{t("landing.stats.gdprValue")}</div>
              <div className="text-sm text-muted-foreground mt-1">{t("landing.stats.gdprLabel")}</div>
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
                {t("landing.problem.title")}
              </h2>
              <p className="text-muted-foreground text-lg mb-8">
                {t("landing.problem.description")}
              </p>
              <div className="space-y-4">
                {["point1", "point2", "point3"].map((key) => (
                  <div key={key} className="flex items-start gap-3">
                    <div className="w-5 h-5 rounded-full bg-destructive/20 flex items-center justify-center mt-0.5">
                      <div className="w-2 h-2 rounded-full bg-destructive" />
                    </div>
                    <span className="text-muted-foreground">{t(`landing.problem.${key}`)}</span>
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
              {t("landing.features.title")}
            </h2>
            <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
              {t("landing.features.subtitle")}
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6 mb-16">
            {FEATURE_ICONS.map((feature, i) => (
              <Card key={i} className="bg-card border-border hover:border-primary/30 transition-colors">
                <CardContent className="p-6">
                  <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center mb-4">
                    <feature.icon className="w-6 h-6 text-primary" />
                  </div>
                  <h3 className="font-heading text-xl font-medium mb-2">{t(`landing.features.${feature.key}.title`)}</h3>
                  <p className="text-muted-foreground">{t(`landing.features.${feature.key}.description`)}</p>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Categories */}
          <div className="grid md:grid-cols-3 gap-6">
            {CATEGORY_META.map((cat, i) => (
              <Card key={i} className={`${cat.bg} border-border hover:border-opacity-50 transition-all`}>
                <CardContent className="p-6">
                  <cat.icon className={`w-8 h-8 ${cat.color} mb-4`} />
                  <h3 className="font-heading text-xl font-medium mb-3">{t(`landing.categories.${cat.key}.name`)}</h3>
                  <div className="flex flex-wrap gap-2">
                    {["ex1", "ex2", "ex3"].map((ex) => (
                      <span key={ex} className="px-3 py-1 rounded-full bg-white/5 text-sm text-muted-foreground">
                        {t(`landing.categories.${cat.key}.${ex}`)}
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
              {t("landing.howItWorks.title")}
            </h2>
          </div>

          <div className="grid md:grid-cols-4 gap-8">
            {STEPS.map((stepKey, i) => (
              <div key={stepKey} className="relative">
                <div className="text-5xl font-heading font-bold text-primary/20 mb-4">{t(`landing.howItWorks.${stepKey}.num`)}</div>
                <h3 className="font-heading text-lg font-medium mb-2">{t(`landing.howItWorks.${stepKey}.title`)}</h3>
                <p className="text-muted-foreground text-sm">{t(`landing.howItWorks.${stepKey}.desc`)}</p>
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
              {t("landing.pricing.title")}
            </h2>
            <p className="text-muted-foreground text-lg">
              {t("landing.pricing.subtitle")}
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            {pricingPlans.map((plan) => (
              <Card
                key={plan.key}
                className={`relative ${plan.popular ? "pricing-card-premium" : "bg-card"} border-border`}
              >
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <span className="px-4 py-1 rounded-full bg-primary text-primary-foreground text-sm font-medium">
                      {t("landing.pricing.popular")}
                    </span>
                  </div>
                )}
                <CardContent className="p-8">
                  <h3 className="font-heading text-2xl font-semibold mb-2">{t(`landing.pricing.${plan.key}.name`)}</h3>
                  <div className="flex items-baseline gap-1 mb-6">
                    <span className="text-4xl font-heading font-bold">{t(`landing.pricing.${plan.key}.price`)}</span>
                    <span className="text-muted-foreground">{t(`landing.pricing.${plan.key}.period`)}</span>
                  </div>
                  <ul className="space-y-3 mb-8">
                    {plan.featureKeys.map((fk) => (
                      <li key={fk} className="flex items-center gap-3">
                        <Check className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                        <span className="text-muted-foreground">{t(`landing.pricing.${plan.key}.${fk}`)}</span>
                      </li>
                    ))}
                  </ul>
                  <Link to={plan.link || "/register"}>
                    <Button
                      className={`w-full rounded-full ${plan.popular ? "" : "bg-secondary text-secondary-foreground hover:bg-secondary/80"}`}
                      data-testid={`pricing-${plan.key}-btn`}
                    >
                      {t(`landing.pricing.${plan.key}.cta`)}
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
              {t("landing.cta.title")}
            </h2>
            <p className="text-muted-foreground text-lg mb-8 max-w-xl mx-auto">
              {t("landing.cta.subtitle")}
            </p>
            <Link to="/register">
              <Button size="lg" className="rounded-full px-8 h-12 text-base btn-lift animate-pulse-glow" data-testid="final-cta-btn">
                {t("landing.cta.button")}
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
              <LanguageSelector />
              <span>{t("landing.footer.copyright")}</span>
              <Link to="/privacy" className="hover:text-foreground transition-colors">{t("landing.footer.privacy")}</Link>
              <Link to="/cgu" className="hover:text-foreground transition-colors">{t("landing.footer.terms")}</Link>
              <a href="mailto:Infinea.compte@gmail.com" className="hover:text-foreground transition-colors">{t("landing.footer.contact")}</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
