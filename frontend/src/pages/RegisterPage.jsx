import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Mail, Lock, User, ArrowRight, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { API, useAuth } from "@/App";
import InFineaLogo from "@/components/InFineaLogo";

export default function RegisterPage() {
  const navigate = useNavigate();
  const { setUser } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  });

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (formData.password !== formData.confirmPassword) {
      toast.error("Les mots de passe ne correspondent pas");
      return;
    }

    if (formData.password.length < 6) {
      toast.error("Le mot de passe doit contenir au moins 6 caractères");
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch(`${API}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          name: formData.name,
          email: formData.email,
          password: formData.password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Erreur lors de l'inscription");
      }

      // Store tokens in localStorage
      if (data.token) {
        localStorage.setItem("infinea_token", data.token);
      }
      if (data.refresh_token) {
        localStorage.setItem("infinea_refresh_token", data.refresh_token);
      }

      setUser(data);
      toast.success("Compte créé avec succès !");
      navigate("/onboarding", { state: { user: data } });
    } catch (error) {
      toast.error(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleSignup = async () => {
    try {
      const response = await fetch(`${API}/auth/google`);
      const data = await response.json();
      window.location.href = data.auth_url;
    } catch (error) {
      toast.error("Erreur lors de l'inscription avec Google");
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#F8FAFB] via-white to-[#F0F7F7] flex items-center justify-center p-4">
      {/* Subtle decorative elements */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-[#459492]/5 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-[#55B3AE]/5 rounded-full blur-3xl" />
      </div>

      <div className="w-full max-w-md relative">
        {/* Logo */}
        <Link to="/" className="flex items-center justify-center mb-8 opacity-0 animate-fade-in">
          <InFineaLogo size={40} withText animate />
        </Link>
        <div className="h-px w-32 mx-auto bg-gradient-to-r from-transparent via-[#459492]/30 to-transparent mb-6" />

        <Card className="bg-white shadow-xl rounded-2xl border border-[#E2E6EA]/50 opacity-0 animate-fade-in" style={{ animationDelay: "100ms", animationFillMode: "forwards" }}>
          <CardHeader className="text-center pb-2">
            <CardTitle className="font-sans font-semibold tracking-tight text-2xl text-[#141E24]">Créez votre compte</CardTitle>
            <p className="text-[#667085] mt-2">
              Commencez à investir vos instants perdus
            </p>
          </CardHeader>
          <CardContent className="space-y-6 pt-4">
            {/* Google Signup */}
            <div className="opacity-0 animate-fade-in" style={{ animationDelay: "200ms", animationFillMode: "forwards" }}>
              <Button
                variant="outline"
                className="w-full h-12 rounded-xl bg-white border-[#E2E6EA] text-[#141E24] hover:bg-[#F8FAFB] shadow-sm hover:shadow-md transition-all duration-200 btn-press"
                onClick={handleGoogleSignup}
                data-testid="google-signup-btn"
              >
                <svg className="w-5 h-5 mr-3" viewBox="0 0 24 24">
                  <path
                    fill="#4285F4"
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  />
                  <path
                    fill="#34A853"
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  />
                  <path
                    fill="#FBBC05"
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                  />
                  <path
                    fill="#EA4335"
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                  />
                </svg>
                S'inscrire avec Google
              </Button>
            </div>

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-[#E2E6EA]" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-white px-3 text-[#667085]">ou</span>
              </div>
            </div>

            {/* Email Registration Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2 opacity-0 animate-fade-in" style={{ animationDelay: "300ms", animationFillMode: "forwards" }}>
                <Label htmlFor="name" className="text-[#141E24] font-medium">Nom complet</Label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#667085]" />
                  <Input
                    id="name"
                    name="name"
                    type="text"
                    placeholder="Jean Dupont"
                    className="pl-10 h-12 rounded-xl bg-[#F8FAFB] border-[#E2E6EA] text-[#141E24] placeholder:text-[#667085]/50 focus:ring-2 focus:ring-[#459492]/20 focus:border-[#459492] transition-all"
                    value={formData.name}
                    onChange={handleChange}
                    required
                    data-testid="register-name-input"
                  />
                </div>
              </div>

              <div className="space-y-2 opacity-0 animate-fade-in" style={{ animationDelay: "400ms", animationFillMode: "forwards" }}>
                <Label htmlFor="email" className="text-[#141E24] font-medium">Email</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#667085]" />
                  <Input
                    id="email"
                    name="email"
                    type="email"
                    placeholder="vous@exemple.com"
                    className="pl-10 h-12 rounded-xl bg-[#F8FAFB] border-[#E2E6EA] text-[#141E24] placeholder:text-[#667085]/50 focus:ring-2 focus:ring-[#459492]/20 focus:border-[#459492] transition-all"
                    value={formData.email}
                    onChange={handleChange}
                    required
                    data-testid="register-email-input"
                  />
                </div>
              </div>

              <div className="space-y-2 opacity-0 animate-fade-in" style={{ animationDelay: "500ms", animationFillMode: "forwards" }}>
                <Label htmlFor="password" className="text-[#141E24] font-medium">Mot de passe</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#667085]" />
                  <Input
                    id="password"
                    name="password"
                    type="password"
                    placeholder="••••••••"
                    className="pl-10 h-12 rounded-xl bg-[#F8FAFB] border-[#E2E6EA] text-[#141E24] placeholder:text-[#667085]/50 focus:ring-2 focus:ring-[#459492]/20 focus:border-[#459492] transition-all"
                    value={formData.password}
                    onChange={handleChange}
                    required
                    data-testid="register-password-input"
                  />
                </div>
              </div>

              <div className="space-y-2 opacity-0 animate-fade-in" style={{ animationDelay: "600ms", animationFillMode: "forwards" }}>
                <Label htmlFor="confirmPassword" className="text-[#141E24] font-medium">Confirmer le mot de passe</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#667085]" />
                  <Input
                    id="confirmPassword"
                    name="confirmPassword"
                    type="password"
                    placeholder="••••••••"
                    className="pl-10 h-12 rounded-xl bg-[#F8FAFB] border-[#E2E6EA] text-[#141E24] placeholder:text-[#667085]/50 focus:ring-2 focus:ring-[#459492]/20 focus:border-[#459492] transition-all"
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    required
                    data-testid="register-confirm-password-input"
                  />
                </div>
              </div>

              <div className="opacity-0 animate-fade-in" style={{ animationDelay: "700ms", animationFillMode: "forwards" }}>
                <Button
                  type="submit"
                  className="w-full h-12 text-base font-semibold rounded-xl shadow-md bg-gradient-to-r from-[#459492] to-[#55B3AE] text-white hover:shadow-lg hover:brightness-105 transition-all duration-200 btn-press"
                  disabled={isLoading}
                  data-testid="register-submit-btn"
                >
                  {isLoading ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <>
                      Créer mon compte
                      <ArrowRight className="w-5 h-5 ml-2" />
                    </>
                  )}
                </Button>
              </div>
            </form>

            <p className="text-center text-sm text-[#667085]">
              Déjà un compte ?{" "}
              <Link to="/login" className="text-[#459492] hover:text-[#275255] font-medium hover:underline transition-colors" data-testid="login-link">
                Se connecter
              </Link>
            </p>

            <p className="text-center text-xs text-[#667085]/80">
              En créant un compte, vous acceptez nos{" "}
              <a href="#" className="text-[#459492] hover:text-[#275255] underline transition-colors">conditions d'utilisation</a> et notre{" "}
              <a href="#" className="text-[#459492] hover:text-[#275255] underline transition-colors">politique de confidentialité</a>.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
