import React, { useState, useEffect } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Timer,
  Check,
  ArrowRight,
  Loader2,
  Crown,
  Sparkles,
  Zap,
  Shield,
} from "lucide-react";
import { toast } from "sonner";
import { API, useAuth, authFetch } from "@/App";

export default function PricingPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [isLoading, setIsLoading] = useState(false);
  const [paymentStatus, setPaymentStatus] = useState(null);

  // Check for payment return
  useEffect(() => {
    const sessionId = searchParams.get("session_id");
    if (sessionId) {
      pollPaymentStatus(sessionId);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  const pollPaymentStatus = async (sessionId, attempts = 0) => {
    if (attempts >= 5) {
      setPaymentStatus("timeout");
      return;
    }

    try {
      const response = await authFetch(`${API}/payments/status/${sessionId}`);

      if (!response.ok) throw new Error("Error");

      const data = await response.json();

      if (data.payment_status === "paid") {
        setPaymentStatus("success");
        toast.success("Paiement réussi ! Bienvenue dans Premium !");
        // Refresh user data
        window.location.href = "/dashboard";
      } else if (data.status === "expired") {
        setPaymentStatus("expired");
        toast.error("Session expirée. Veuillez réessayer.");
      } else {
        setPaymentStatus("pending");
        setTimeout(() => pollPaymentStatus(sessionId, attempts + 1), 2000);
      }
    } catch (error) {
      console.error("Payment status error:", error);
      setPaymentStatus("error");
    }
  };

  const handleUpgrade = async () => {
    if (!user) {
      navigate("/login");
      return;
    }

    setIsLoading(true);
    try {
      const response = await authFetch(`${API}/payments/checkout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          origin_url: window.location.origin,
        }),
      });

      if (!response.ok) throw new Error("Erreur de paiement");

      const data = await response.json();
      window.location.href = data.url;
    } catch (error) {
      toast.error("Impossible de créer la session de paiement");
    } finally {
      setIsLoading(false);
    }
  };

  const plans = [
    {
      name: "Gratuit",
      price: "0€",
      period: "",
      description: "Pour découvrir InFinea",
      features: [
        "Accès aux micro-actions de base",
        "5 suggestions IA par jour",
        "Suivi de progression basique",
        "3 catégories d'actions",
      ],
      cta: user ? "Plan actuel" : "Commencer",
      action: () => navigate("/register"),
      popular: false,
      disabled: user?.subscription_tier === "free",
    },
    {
      name: "Premium",
      price: "6,99€",
      period: "/mois",
      description: "Pour maximiser votre temps",
      features: [
        "Toutes les micro-actions débloquées",
        "Suggestions IA illimitées",
        "Statistiques avancées",
        "Actions personnalisées",
        "Support prioritaire",
        "Nouvelles fonctionnalités en avant-première",
      ],
      cta: user?.subscription_tier === "premium" ? "Déjà Premium" : "Passer à Premium",
      action: handleUpgrade,
      popular: true,
      disabled: user?.subscription_tier === "premium",
    },
  ];

  if (paymentStatus === "pending") {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-primary mx-auto mb-4" />
          <h2 className="font-heading text-2xl mb-2">Vérification du paiement...</h2>
          <p className="text-muted-foreground">Merci de patienter quelques instants</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 glass">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link to="/" className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
                <Timer className="w-5 h-5 text-primary-foreground" />
              </div>
              <span className="font-heading text-xl font-semibold">InFinea</span>
            </Link>
            <div className="flex items-center gap-4">
              {user ? (
                <Link to="/dashboard">
                  <Button variant="ghost">Dashboard</Button>
                </Link>
              ) : (
                <>
                  <Link to="/login">
                    <Button variant="ghost">Connexion</Button>
                  </Link>
                  <Link to="/register">
                    <Button className="rounded-full">Commencer</Button>
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="pt-32 pb-20 px-4">
        <div className="max-w-5xl mx-auto">
          {/* Header */}
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 mb-6">
              <Crown className="w-4 h-4 text-primary" />
              <span className="text-sm text-primary">Investissez dans votre temps</span>
            </div>
            <h1 className="font-heading text-4xl md:text-5xl font-bold mb-4" data-testid="pricing-title">
              Choisissez votre plan
            </h1>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Commencez gratuitement et passez à Premium quand vous êtes prêt à maximiser chaque instant.
            </p>
          </div>

          {/* Pricing Cards */}
          <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto mb-16">
            {plans.map((plan, i) => (
              <Card
                key={i}
                className={`relative ${
                  plan.popular
                    ? "pricing-card-premium border-primary/30"
                    : "bg-card"
                }`}
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
                  <p className="text-muted-foreground mb-4">{plan.description}</p>
                  <div className="flex items-baseline gap-1 mb-6">
                    <span className="text-5xl font-heading font-bold">{plan.price}</span>
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
                  <Button
                    onClick={plan.action}
                    disabled={plan.disabled || isLoading}
                    className={`w-full rounded-full h-12 ${
                      plan.popular
                        ? ""
                        : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
                    }`}
                    data-testid={`pricing-${plan.name.toLowerCase()}-btn`}
                  >
                    {isLoading && plan.popular ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      <>
                        {plan.cta}
                        {!plan.disabled && <ArrowRight className="w-5 h-5 ml-2" />}
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Features Comparison */}
          <div className="max-w-4xl mx-auto">
            <h2 className="font-heading text-2xl font-semibold text-center mb-8">
              Pourquoi passer à Premium ?
            </h2>
            <div className="grid md:grid-cols-3 gap-6">
              <Card className="bg-card/50">
                <CardContent className="p-6 text-center">
                  <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center mx-auto mb-4">
                    <Sparkles className="w-6 h-6 text-primary" />
                  </div>
                  <h3 className="font-heading text-lg font-medium mb-2">IA Illimitée</h3>
                  <p className="text-sm text-muted-foreground">
                    Suggestions personnalisées sans limite pour optimiser chaque instant
                  </p>
                </CardContent>
              </Card>
              <Card className="bg-card/50">
                <CardContent className="p-6 text-center">
                  <div className="w-12 h-12 rounded-xl bg-amber-500/10 flex items-center justify-center mx-auto mb-4">
                    <Zap className="w-6 h-6 text-amber-500" />
                  </div>
                  <h3 className="font-heading text-lg font-medium mb-2">Actions Exclusives</h3>
                  <p className="text-sm text-muted-foreground">
                    Accès à toutes les micro-actions, y compris les plus avancées
                  </p>
                </CardContent>
              </Card>
              <Card className="bg-card/50">
                <CardContent className="p-6 text-center">
                  <div className="w-12 h-12 rounded-xl bg-emerald-500/10 flex items-center justify-center mx-auto mb-4">
                    <Shield className="w-6 h-6 text-emerald-500" />
                  </div>
                  <h3 className="font-heading text-lg font-medium mb-2">Support Prioritaire</h3>
                  <p className="text-sm text-muted-foreground">
                    Une équipe dédiée pour vous accompagner dans votre progression
                  </p>
                </CardContent>
              </Card>
            </div>
          </div>

          {/* FAQ or Trust signals */}
          <div className="mt-16 text-center">
            <p className="text-sm text-muted-foreground mb-4">
              Paiement sécurisé par Stripe • Annulez à tout moment
            </p>
            <p className="text-xs text-muted-foreground">
              Des questions ? Contactez-nous à{" "}
              <a href="mailto:Infinea.compte@gmail.com" className="text-primary hover:underline">
                Infinea.compte@gmail.com
              </a>
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
