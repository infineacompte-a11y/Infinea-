import React, { useState, useEffect } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Timer,
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

export default function PricingPage() {
  const { t } = useTranslation();
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
        toast.success(t("pricing.toasts.paymentSuccess"));
        window.location.href = "/dashboard";
      } else if (data.status === "expired") {
        setPaymentStatus("expired");
        toast.error(t("pricing.toasts.sessionExpired"));
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

      toast.success(t("pricing.toasts.premiumActivated"));
      window.location.href = "/dashboard";
      return;
    } catch (error) {
      toast.error(t("pricing.toasts.activationError"));
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
      toast.error(t("pricing.toasts.portalError"));
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
      toast.success(t("pricing.toasts.premiumActivated"));
      window.location.href = "/dashboard";
    } catch (error) {
      toast.error(error.message || t("pricing.toasts.invalidPromo"));
    } finally {
      setPromoLoading(false);
    }
  };

  const isPremium = user?.subscription_tier === "premium";

  const plans = [
    {
      name: t("pricing.plans.free.name"),
      price: t("pricing.plans.free.price"),
      period: "",
      description: t("pricing.plans.free.description"),
      features: [
        t("pricing.plans.free.feature1"),
        t("pricing.plans.free.feature2"),
        t("pricing.plans.free.feature3"),
        t("pricing.plans.free.feature4"),
        t("pricing.plans.free.feature5"),
      ],
      cta: user ? t("pricing.plans.free.ctaCurrent") : t("pricing.plans.free.ctaStart"),
      action: () => navigate("/register"),
      popular: false,
      disabled: !!user,
    },
    {
      name: t("pricing.plans.premium.name"),
      price: t("pricing.plans.premium.price"),
      period: t("pricing.plans.premium.period"),
      description: t("pricing.plans.premium.description"),
      features: [
        t("pricing.plans.premium.feature1"),
        t("pricing.plans.premium.feature2"),
        t("pricing.plans.premium.feature3"),
        t("pricing.plans.premium.feature4"),
        t("pricing.plans.premium.feature5"),
        t("pricing.plans.premium.feature6"),
        t("pricing.plans.premium.feature7"),
        t("pricing.plans.premium.feature8"),
      ],
      cta: isPremium ? t("pricing.plans.premium.ctaAlready") : t("pricing.plans.premium.ctaUpgrade"),
      action: handleUpgrade,
      popular: true,
      disabled: isPremium,
    },
  ];

  const comparisonFeatures = [
    { name: t("pricing.comparison.microActions.name"), free: t("pricing.comparison.microActions.free"), premium: t("pricing.comparison.microActions.premium") },
    { name: t("pricing.comparison.categories.name"), free: t("pricing.comparison.categories.free"), premium: t("pricing.comparison.categories.premium") },
    { name: t("pricing.comparison.aiCoach.name"), free: t("pricing.comparison.aiCoach.free"), premium: t("pricing.comparison.aiCoach.premium") },
    { name: t("pricing.comparison.aiSuggestions.name"), free: true, premium: true },
    { name: t("pricing.comparison.personalizedSuggestions.name"), free: t("pricing.comparison.personalizedSuggestions.free"), premium: t("pricing.comparison.personalizedSuggestions.premium") },
    { name: t("pricing.comparison.proactiveSuggestion.name"), free: false, premium: t("pricing.comparison.proactiveSuggestion.premium") },
    { name: t("pricing.comparison.postSessionDebrief.name"), free: true, premium: true },
    { name: t("pricing.comparison.weeklyAnalysis.name"), free: true, premium: true },
    { name: t("pricing.comparison.customActions.name"), free: true, premium: true },
    { name: t("pricing.comparison.badges.name"), free: t("pricing.comparison.badges.free"), premium: t("pricing.comparison.badges.premium") },
    { name: t("pricing.comparison.streakShield.name"), free: false, premium: true },
    { name: t("pricing.comparison.monthlyChallenges.name"), free: false, premium: true },
    { name: t("pricing.comparison.advancedAnalytics.name"), free: false, premium: true },
    { name: t("pricing.comparison.integrations.name"), free: t("pricing.comparison.integrations.free"), premium: t("pricing.comparison.integrations.premium") },
  ];

  if (paymentStatus === "pending") {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-primary mx-auto mb-4" />
          <h2 className="font-heading text-2xl mb-2">{t("pricing.payment.verifying")}</h2>
          <p className="text-muted-foreground">{t("pricing.payment.pleaseWait")}</p>
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
                    <Button variant="ghost">{t("pricing.nav.login")}</Button>
                  </Link>
                  <Link to="/register">
                    <Button className="rounded-full">{t("pricing.nav.getStarted")}</Button>
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
              <span className="text-sm text-primary">{t("pricing.header.badge")}</span>
            </div>
            <h1 className="font-heading text-4xl md:text-5xl font-bold mb-4" data-testid="pricing-title">
              {t("pricing.header.title")}
            </h1>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              {t("pricing.header.subtitle")}
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
                      {t("pricing.popular")}
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
                  {isPremium && plan.popular && (
                    <Button
                      variant="ghost"
                      onClick={handleManageSubscription}
                      disabled={portalLoading}
                      className="w-full mt-3 text-muted-foreground"
                    >
                      {portalLoading ? (
                        <Loader2 className="w-4 h-4 animate-spin mr-2" />
                      ) : (
                        <Settings className="w-4 h-4 mr-2" />
                      )}
                      {t("pricing.manageSubscription")}
                    </Button>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Promo Code Section */}
          {user && !isPremium && (
            <div className="max-w-4xl mx-auto mb-8">
              <button
                onClick={() => setPromoOpen(!promoOpen)}
                className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors mx-auto"
              >
                <Gift className="w-4 h-4" />
                {t("pricing.promo.haveCode")}
                <ChevronDown className={`w-4 h-4 transition-transform ${promoOpen ? "rotate-180" : ""}`} />
              </button>
              {promoOpen && (
                <div className="mt-4 flex gap-3 max-w-md mx-auto">
                  <Input
                    type="text"
                    placeholder={t("pricing.promo.placeholder")}
                    value={promoCode}
                    onChange={(e) => setPromoCode(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handlePromoRedeem()}
                    className="flex-1"
                    disabled={promoLoading}
                  />
                  <Button
                    onClick={handlePromoRedeem}
                    disabled={promoLoading || !promoCode.trim()}
                    className="rounded-full"
                  >
                    {promoLoading ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      t("pricing.promo.activate")
                    )}
                  </Button>
                </div>
              )}
            </div>
          )}

          {/* Premium Categories Showcase */}
          <div className="max-w-4xl mx-auto mb-16">
            <h2 className="font-heading text-2xl font-semibold text-center mb-8">
              {t("pricing.premiumCategories.title")}
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { icon: Palette, nameKey: "creativity", color: "text-pink-500", bg: "bg-pink-500/10" },
                { icon: Dumbbell, nameKey: "fitness", color: "text-orange-500", bg: "bg-orange-500/10" },
                { icon: Leaf, nameKey: "mindfulness", color: "text-green-500", bg: "bg-green-500/10" },
                { icon: Crown, nameKey: "leadership", color: "text-amber-500", bg: "bg-amber-500/10" },
                { icon: Zap, nameKey: "finance", color: "text-emerald-500", bg: "bg-emerald-500/10" },
                { icon: Sparkles, nameKey: "relations", color: "text-blue-500", bg: "bg-blue-500/10" },
                { icon: Brain, nameKey: "mental_health", color: "text-purple-500", bg: "bg-purple-500/10" },
                { icon: Trophy, nameKey: "entrepreneurship", color: "text-red-500", bg: "bg-red-500/10" },
              ].map(({ icon: Icon, nameKey, color, bg }) => (
                <Card key={nameKey} className="bg-card/50 border-dashed">
                  <CardContent className="p-4 text-center">
                    <div className={`w-10 h-10 rounded-lg ${bg} flex items-center justify-center mx-auto mb-2`}>
                      <Icon className={`w-5 h-5 ${color}`} />
                    </div>
                    <p className="text-sm font-medium">{t(`categories.${nameKey}`)}</p>
                    <p className="text-xs text-muted-foreground">{t("pricing.premiumCategories.actionsCount")}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          {/* Features Comparison */}
          <div className="max-w-4xl mx-auto mb-16">
            <h2 className="font-heading text-2xl font-semibold text-center mb-8">
              {t("pricing.whyPremium.title")}
            </h2>
            <div className="grid md:grid-cols-3 gap-6 mb-12">
              <Card className="bg-card/50">
                <CardContent className="p-6 text-center">
                  <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center mx-auto mb-4">
                    <Sparkles className="w-6 h-6 text-primary" />
                  </div>
                  <h3 className="font-heading text-lg font-medium mb-2">{t("pricing.whyPremium.aiTitle")}</h3>
                  <p className="text-sm text-muted-foreground">
                    {t("pricing.whyPremium.aiDescription")}
                  </p>
                </CardContent>
              </Card>
              <Card className="bg-card/50">
                <CardContent className="p-6 text-center">
                  <div className="w-12 h-12 rounded-xl bg-amber-500/10 flex items-center justify-center mx-auto mb-4">
                    <Zap className="w-6 h-6 text-amber-500" />
                  </div>
                  <h3 className="font-heading text-lg font-medium mb-2">{t("pricing.whyPremium.libraryTitle")}</h3>
                  <p className="text-sm text-muted-foreground">
                    {t("pricing.whyPremium.libraryDescription")}
                  </p>
                </CardContent>
              </Card>
              <Card className="bg-card/50">
                <CardContent className="p-6 text-center">
                  <div className="w-12 h-12 rounded-xl bg-emerald-500/10 flex items-center justify-center mx-auto mb-4">
                    <Shield className="w-6 h-6 text-emerald-500" />
                  </div>
                  <h3 className="font-heading text-lg font-medium mb-2">{t("pricing.whyPremium.shieldTitle")}</h3>
                  <p className="text-sm text-muted-foreground">
                    {t("pricing.whyPremium.shieldDescription")}
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Detailed comparison table */}
            <Card className="bg-card/50">
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-4 font-heading font-semibold">{t("pricing.comparisonTable.feature")}</th>
                        <th className="text-center p-4 font-heading font-semibold">{t("pricing.comparisonTable.free")}</th>
                        <th className="text-center p-4 font-heading font-semibold text-primary">
                          <div className="flex items-center justify-center gap-1">
                            <Crown className="w-4 h-4" /> {t("pricing.comparisonTable.premium")}
                          </div>
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {comparisonFeatures.map((feature, i) => (
                        <tr key={i} className={i < comparisonFeatures.length - 1 ? "border-b border-border/50" : ""}>
                          <td className="p-4 text-sm font-medium">{feature.name}</td>
                          <td className="p-4 text-center text-sm">
                            {typeof feature.free === "boolean" ? (
                              feature.free ? (
                                <Check className="w-5 h-5 text-emerald-500 mx-auto" />
                              ) : (
                                <X className="w-5 h-5 text-muted-foreground/40 mx-auto" />
                              )
                            ) : (
                              <span className="text-muted-foreground">{feature.free}</span>
                            )}
                          </td>
                          <td className="p-4 text-center text-sm">
                            {typeof feature.premium === "boolean" ? (
                              feature.premium ? (
                                <Check className="w-5 h-5 text-primary mx-auto" />
                              ) : (
                                <X className="w-5 h-5 text-muted-foreground/40 mx-auto" />
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
              </CardContent>
            </Card>
          </div>

          {/* FAQ or Trust signals */}
          <div className="mt-16 text-center">
            <p className="text-sm text-muted-foreground mb-4">
              {t("pricing.footer.trustSignals")}
            </p>
            <p className="text-xs text-muted-foreground">
              {t("pricing.footer.contactPrefix")}{" "}
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
