import React, { useState, useEffect } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { trackSubscriptionStarted } from "@/lib/analytics";
import {
  Check,
  X,
  ArrowRight,
  Loader2,
  Crown,
  Sparkles,
  Zap,
  Shield,
  Brain,
  Palette,
  Dumbbell,
  Leaf,
  Trophy,
  Settings,
  Gift,
  ChevronDown,
} from "lucide-react";
import { toast } from "sonner";
import { API, useAuth, authFetch } from "@/App";
import InFineaLogo from "@/components/InFineaLogo";

export default function PricingPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [isLoading, setIsLoading] = useState(false);
  const [portalLoading, setPortalLoading] = useState(false);
  const [paymentStatus, setPaymentStatus] = useState(null);
  const [promoCode, setPromoCode] = useState("");
  const [promoLoading, setPromoLoading] = useState(false);
  const [promoOpen, setPromoOpen] = useState(false);

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
      // Temporary: activate premium directly (replace with Stripe checkout later)
      const response = await authFetch(`${API}/premium/activate-free`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });

      if (!response.ok) throw new Error("Erreur d'activation");

      trackSubscriptionStarted("premium");
      toast.success("Premium activé ! Bienvenue dans Premium !");
      window.location.href = "/dashboard";
      return;
    } catch (error) {
      toast.error("Impossible d'activer Premium");
    } finally {
      setIsLoading(false);
    }
  };

  const handleManageSubscription = async () => {
    setPortalLoading(true);
    try {
      const response = await authFetch(`${API}/premium/portal`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ origin_url: window.location.origin }),
      });

      if (!response.ok) throw new Error("Erreur");

      const data = await response.json();
      window.location.href = data.url;
    } catch (error) {
      toast.error("Impossible d'accéder à la gestion de l'abonnement");
    } finally {
      setPortalLoading(false);
    }
  };

  const handlePromoRedeem = async () => {
    if (!promoCode.trim()) return;
    setPromoLoading(true);
    try {
      const response = await authFetch(`${API}/promo/redeem`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code: promoCode.trim() }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Erreur");
      trackSubscriptionStarted("premium_promo");
      toast.success("Premium activé ! Bienvenue dans Premium !");
      window.location.href = "/dashboard";
    } catch (error) {
      toast.error(error.message || "Code promo invalide");
    } finally {
      setPromoLoading(false);
    }
  };

  const isPremium = user?.subscription_tier === "premium";

  const plans = [
    {
      name: "Gratuit",
      price: "0€",
      period: "",
      description: "Pour découvrir InFinea",
      features: [
        "300+ micro-actions (3 catégories)",
        "Coach IA personnalisé",
        "Suivi de progression & streaks",
        "12 badges à débloquer",
        "Journal de réflexion",
      ],
      cta: user ? "Plan actuel" : "Commencer",
      action: () => navigate("/register"),
      popular: false,
      disabled: !!user,
    },
    {
      name: "Premium",
      price: "6,99€",
      period: "/mois",
      description: "L'expérience complète",
      features: [
        "Tout le plan Gratuit +",
        "8 catégories exclusives (400+ actions)",
        "IA avancée avec suggestions personnalisées",
        "Suggestion proactive au bon moment",
        "Bouclier de Streak (1x/semaine)",
        "Défis mensuels & récompenses",
        "Analytics avancées & insights",
        "20 badges Premium",
      ],
      cta: isPremium ? "Déjà Premium" : "Passer à Premium",
      action: handleUpgrade,
      popular: true,
      disabled: isPremium,
    },
  ];

  const comparisonFeatures = [
    { name: "Micro-actions", free: "300+ (3 catégories)", premium: "700+ (11 catégories)" },
    { name: "Catégories", free: "Learning, Productivité, Bien-être", premium: "+ Créativité, Fitness, Mindfulness, Leadership, Finance, Relations, Santé mentale, Entrepreneuriat" },
    { name: "Coach IA", free: "Claude Haiku", premium: "Claude Sonnet (avancé)" },
    { name: "Suggestions IA", free: true, premium: true },
    { name: "Suggestions personnalisées", free: "Basiques", premium: "IA comportementale avancée" },
    { name: "Suggestion proactive", free: false, premium: "Au bon moment, sans rien demander" },
    { name: "Débrief post-session", free: true, premium: true },
    { name: "Analyse hebdomadaire", free: true, premium: true },
    { name: "Création d'actions custom", free: true, premium: true },
    { name: "Badges", free: "12 badges", premium: "20 badges (dont 8 exclusifs)" },
    { name: "Bouclier de Streak", free: false, premium: true },
    { name: "Défis mensuels", free: false, premium: true },
    { name: "Analytics avancées", free: false, premium: true },
    { name: "Intégrations", free: "1 (Google Calendar)", premium: "Toutes (Calendar, Notion, Todoist, Slack)" },
  ];

  if (paymentStatus === "pending") {
    return (
      <div className="min-h-screen app-bg-mesh flex items-center justify-center p-4">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-primary mx-auto mb-4" />
          <h2 className="font-sans font-semibold tracking-tight text-2xl mb-2">Vérification du paiement...</h2>
          <p className="text-muted-foreground">Merci de patienter quelques instants</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen app-bg-mesh">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 glass">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link to="/" className="flex items-center gap-2">
              <InFineaLogo size={32} withText />
            </Link>
            <div className="flex items-center gap-4">
              {user ? (
                <Link to="/dashboard">
                  <Button variant="ghost" className="rounded-xl transition-all duration-200">Dashboard</Button>
                </Link>
              ) : (
                <>
                  <Link to="/login">
                    <Button variant="ghost" className="rounded-xl transition-all duration-200">Connexion</Button>
                  </Link>
                  <Link to="/register">
                    <Button className="rounded-xl shadow-md hover:shadow-lg transition-all duration-200 btn-press">Commencer</Button>
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="pt-24 sm:pt-32 pb-16 sm:pb-20 px-4">
        <div className="max-w-5xl mx-auto">
          {/* Header */}
          <div className="opacity-0 animate-fade-in" style={{ animationDelay: "100ms", animationFillMode: "forwards" }}>
            <div className="text-center mb-10 sm:mb-16">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 sm:px-4 sm:py-2 rounded-full bg-[#E48C75]/40 border border-[#E48C75]/20 mb-5 sm:mb-6">
                <Crown className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-[#E48C75]" />
                <span className="text-xs sm:text-sm text-[#E48C75]">Investissez dans votre temps</span>
              </div>
              <h1 className="font-sans font-semibold tracking-tight text-3xl sm:text-4xl md:text-5xl font-bold mb-3 sm:mb-4" data-testid="pricing-title">
                Choisissez votre plan
              </h1>
              <p className="text-base sm:text-lg text-muted-foreground max-w-2xl mx-auto">
                Commencez gratuitement et passez à Premium pour une IA qui apprend de vous et une bibliothèque de micro-actions en perpétuelle évolution.
              </p>
            </div>
          </div>

          {/* Pricing Cards */}
          <div className="opacity-0 animate-fade-in" style={{ animationDelay: "200ms", animationFillMode: "forwards" }}>
            <div className="grid md:grid-cols-2 gap-6 sm:gap-8 max-w-4xl mx-auto mb-10 sm:mb-16">
              {plans.map((plan, i) => (
                <div
                  key={i}
                  className="opacity-0 animate-fade-in"
                  style={{ animationDelay: `${300 + i * 100}ms`, animationFillMode: "forwards" }}
                >
                  <Card
                    className={`relative transition-all duration-300 hover:shadow-xl hover:-translate-y-1 ${
                      plan.popular
                        ? "pricing-card-premium border-primary/30 ring-2 ring-[#459492] shadow-xl shadow-[#459492]/10 scale-[1.02] md:scale-105"
                        : "bg-white shadow-sm border border-[#E2E6EA] hover:border-[#459492]/30"
                    }`}
                  >
                    {plan.popular && (
                      <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                        <span className="px-4 py-1 rounded-full bg-gradient-to-r from-[#459492] to-[#55B3AE] text-white text-sm font-medium shadow-lg">
                          Populaire
                        </span>
                      </div>
                    )}
                    <CardContent className="p-5 sm:p-8">
                      <h3 className="font-sans font-semibold tracking-tight text-xl sm:text-2xl font-semibold mb-1.5 sm:mb-2">{plan.name}</h3>
                      <p className="text-sm sm:text-base text-muted-foreground mb-3 sm:mb-4">{plan.description}</p>
                      <div className="flex items-baseline gap-1 mb-4 sm:mb-6">
                        <span className="text-4xl sm:text-5xl font-sans font-semibold tracking-tight font-bold tabular-nums">{plan.price}</span>
                        <span className="text-muted-foreground">{plan.period}</span>
                      </div>
                      <ul className="space-y-2.5 sm:space-y-3 mb-6 sm:mb-8">
                        {plan.features.map((feature, j) => (
                          <li key={j} className="flex items-start gap-2.5 sm:gap-3">
                            <Check className="w-4 h-4 sm:w-5 sm:h-5 text-[#5DB786] flex-shrink-0 mt-0.5" />
                            <span className="text-sm sm:text-base text-muted-foreground">{feature}</span>
                          </li>
                        ))}
                      </ul>
                      <Button
                        onClick={plan.action}
                        disabled={plan.disabled || isLoading}
                        className={`w-full h-12 transition-all duration-200 btn-press ${
                          plan.popular
                            ? "rounded-xl shadow-md hover:shadow-lg bg-gradient-to-r from-[#459492] to-[#55B3AE] hover:from-[#275255] hover:to-[#459492] text-white border-0"
                            : "rounded-xl bg-secondary text-secondary-foreground hover:bg-secondary/80"
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
                      {isPremium && plan.popular && (
                        <Button
                          variant="ghost"
                          onClick={handleManageSubscription}
                          disabled={portalLoading}
                          className="w-full mt-3 text-muted-foreground rounded-xl transition-all duration-200"
                        >
                          {portalLoading ? (
                            <Loader2 className="w-4 h-4 animate-spin mr-2" />
                          ) : (
                            <Settings className="w-4 h-4 mr-2" />
                          )}
                          Gérer mon abonnement
                        </Button>
                      )}
                    </CardContent>
                  </Card>
                </div>
              ))}
            </div>
          </div>

          {/* Promo Code Section */}
          {user && !isPremium && (
            <div className="opacity-0 animate-fade-in" style={{ animationDelay: "500ms", animationFillMode: "forwards" }}>
              <div className="max-w-4xl mx-auto mb-8">
                <button
                  onClick={() => setPromoOpen(!promoOpen)}
                  className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors mx-auto"
                >
                  <Gift className="w-4 h-4" />
                  Vous avez un code promo ?
                  <ChevronDown className={`w-4 h-4 transition-transform duration-200 ${promoOpen ? "rotate-180" : ""}`} />
                </button>
                {promoOpen && (
                  <div className="mt-4 flex gap-3 max-w-md mx-auto animate-in fade-in slide-in-from-top-2 duration-300">
                    <Input
                      type="text"
                      placeholder="Entrez votre code"
                      value={promoCode}
                      onChange={(e) => setPromoCode(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && handlePromoRedeem()}
                      className="flex-1 rounded-xl"
                      disabled={promoLoading}
                    />
                    <Button
                      onClick={handlePromoRedeem}
                      disabled={promoLoading || !promoCode.trim()}
                      className="rounded-xl shadow-md hover:shadow-lg transition-all duration-200 btn-press"
                    >
                      {promoLoading ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        "Activer"
                      )}
                    </Button>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Premium Categories Showcase */}
          <div className="opacity-0 animate-fade-in" style={{ animationDelay: "600ms", animationFillMode: "forwards" }}>
            <div className="max-w-4xl mx-auto mb-10 sm:mb-16">
              <h2 className="font-sans font-semibold tracking-tight text-xl sm:text-2xl font-semibold text-center mb-6 sm:mb-8">
                8 catégories exclusives Premium
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
                {[
                  { icon: Palette, name: "Créativité", color: "text-[#55B3AE]", bg: "bg-[#55B3AE]/40" },
                  { icon: Dumbbell, name: "Fitness", color: "text-[#E48C75]", bg: "bg-[#E48C75]/40" },
                  { icon: Leaf, name: "Mindfulness", color: "text-[#459492]", bg: "bg-[#459492]/40" },
                  { icon: Crown, name: "Leadership", color: "text-[#7B8FA1]", bg: "bg-[#7B8FA1]/10" },
                  { icon: Zap, name: "Finance", color: "text-[#2E9B6A]", bg: "bg-[#2E9B6A]/10" },
                  { icon: Sparkles, name: "Relations", color: "text-[#C4806E]", bg: "bg-[#C4806E]/10" },
                  { icon: Brain, name: "Santé mentale", color: "text-[#6EAAA8]", bg: "bg-[#6EAAA8]/10" },
                  { icon: Trophy, name: "Entrepreneuriat", color: "text-[#E48C75]", bg: "bg-[#E48C75]/40" },
                ].map(({ icon: Icon, name, color, bg }, idx) => (
                  <div
                    key={name}
                    className="opacity-0 animate-fade-in"
                    style={{ animationDelay: `${700 + idx * 60}ms`, animationFillMode: "forwards" }}
                  >
                    <Card className="bg-white shadow-sm border border-[#E2E6EA] border-dashed hover:border-[#459492]/20 hover:shadow-lg hover:-translate-y-1 transition-all duration-300 group">
                      <CardContent className="p-4 text-center">
                        <div className={`w-10 h-10 rounded-lg ${bg} flex items-center justify-center mx-auto mb-2 group-hover:scale-110 transition-transform duration-200`}>
                          <Icon className={`w-5 h-5 ${color}`} />
                        </div>
                        <p className="text-sm font-medium">{name}</p>
                        <p className="text-xs text-muted-foreground tabular-nums">50 actions</p>
                      </CardContent>
                    </Card>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Features Comparison */}
          <div className="opacity-0 animate-fade-in" style={{ animationDelay: "800ms", animationFillMode: "forwards" }}>
            <div className="max-w-4xl mx-auto mb-10 sm:mb-16">
              <h2 className="font-sans font-semibold tracking-tight text-xl sm:text-2xl font-semibold text-center mb-6 sm:mb-8">
                Pourquoi passer à Premium ?
              </h2>
              <div className="grid md:grid-cols-3 gap-4 sm:gap-6 mb-8 sm:mb-12">
                {[
                  {
                    icon: Sparkles,
                    iconColor: "text-primary",
                    iconBg: "bg-primary/10",
                    title: "IA qui vous connait",
                    desc: "Suggestions personnalisées selon vos habitudes, votre énergie et le moment de la journée",
                  },
                  {
                    icon: Zap,
                    iconColor: "text-[#E48C75]",
                    iconBg: "bg-[#E48C75]/40",
                    title: "Bibliothèque infinie",
                    desc: "700+ micro-actions dans 11 catégories, enrichie en continu pour ne jamais manquer d'inspiration",
                  },
                  {
                    icon: Shield,
                    iconColor: "text-[#5DB786]",
                    iconBg: "bg-[#5DB786]/40",
                    title: "Bouclier de Streak",
                    desc: "Protégez votre streak une fois par semaine si vous manquez un jour",
                  },
                ].map((item, idx) => {
                  const FeatureIcon = item.icon;
                  return (
                    <div
                      key={item.title}
                      className="opacity-0 animate-fade-in"
                      style={{ animationDelay: `${900 + idx * 100}ms`, animationFillMode: "forwards" }}
                    >
                      <Card className="bg-white shadow-sm border border-[#E2E6EA] hover:border-[#459492]/20 hover:shadow-lg hover:-translate-y-1 transition-all duration-300 group">
                        <CardContent className="p-6 text-center">
                          <div className={`w-12 h-12 rounded-xl ${item.iconBg} flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform duration-200`}>
                            <FeatureIcon className={`w-6 h-6 ${item.iconColor}`} />
                          </div>
                          <h3 className="font-sans font-semibold tracking-tight text-lg font-medium mb-2">{item.title}</h3>
                          <p className="text-sm text-muted-foreground">{item.desc}</p>
                        </CardContent>
                      </Card>
                    </div>
                  );
                })}
              </div>

              {/* Detailed comparison table */}
              <div className="relative">
                <div className="rounded-xl border border-[#E2E6EA] bg-white shadow-sm">
                  <table className="w-full table-fixed">
                    <thead>
                      <tr className="border-b bg-[#F8FAFB]">
                        <th className="text-left p-2.5 sm:p-4 text-xs sm:text-sm font-semibold w-[38%]">Fonctionnalité</th>
                        <th className="text-center p-2.5 sm:p-4 text-xs sm:text-sm font-semibold w-[28%]">Gratuit</th>
                        <th className="text-center p-2.5 sm:p-4 text-xs sm:text-sm font-semibold text-[#E48C75] w-[34%]">
                          <div className="flex items-center justify-center gap-1">
                            <Crown className="w-3.5 h-3.5 text-[#E48C75]" /> Premium
                          </div>
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {comparisonFeatures.map((feature, i) => (
                        <tr key={i} className={`transition-colors hover:bg-muted/30 ${i < comparisonFeatures.length - 1 ? "border-b border-border/50" : ""}`}>
                          <td className="p-2.5 sm:p-4 text-[11px] sm:text-sm font-medium">{feature.name}</td>
                          <td className="p-2.5 sm:p-4 text-center text-[11px] sm:text-sm">
                            {typeof feature.free === "boolean" ? (
                              feature.free ? (
                                <Check className="w-4 h-4 sm:w-5 sm:h-5 text-[#5DB786] mx-auto" />
                              ) : (
                                <X className="w-4 h-4 sm:w-5 sm:h-5 text-muted-foreground/40 mx-auto" />
                              )
                            ) : (
                              <span className="text-muted-foreground">{feature.free}</span>
                            )}
                          </td>
                          <td className="p-2.5 sm:p-4 text-center text-[11px] sm:text-sm">
                            {typeof feature.premium === "boolean" ? (
                              feature.premium ? (
                                <Check className="w-4 h-4 sm:w-5 sm:h-5 text-primary mx-auto" />
                              ) : (
                                <X className="w-4 h-4 sm:w-5 sm:h-5 text-muted-foreground/40 mx-auto" />
                              )
                            ) : (
                              <span className="text-primary font-medium">{feature.premium}</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>

          {/* FAQ or Trust signals */}
          <div className="opacity-0 animate-fade-in" style={{ animationDelay: "1000ms", animationFillMode: "forwards" }}>
            <div className="mt-10 sm:mt-16 text-center">
              <p className="text-sm text-muted-foreground mb-4">
                Paiement sécurisé par Stripe • Annulez à tout moment • Sans engagement
              </p>
              <p className="text-xs text-muted-foreground">
                Des questions ? Contactez-nous à{" "}
                <a href="mailto:Infinea.compte@gmail.com" className="text-primary hover:underline">
                  Infinea.compte@gmail.com
                </a>
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
