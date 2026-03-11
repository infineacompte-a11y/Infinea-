import React, { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import {
  Timer,
  LayoutGrid,
  Sparkles,
  Calendar,
  Brain,
  FileText,
  Award,
  BarChart3,
  Bell,
  Building2,
  User,
  LogOut,
  Menu,
  Target,
  CalendarClock,
  Zap,
} from "lucide-react";
import { useAuth } from "@/App";

const navItems = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutGrid },
  { to: "/my-day", label: "Ma Journée", icon: Zap },
  { to: "/objectives", label: "Mes Objectifs", icon: Target },
  { to: "/routines", label: "Mes Routines", icon: CalendarClock },
  { to: "/actions", label: "Bibliothèque", icon: Sparkles },
  { to: "/integrations", label: "Intégrations", icon: Calendar },
  { to: "/journal", label: "Journal", icon: Brain },
  { to: "/notes", label: "Mes Notes", icon: FileText },
  { to: "/badges", label: "Badges", icon: Award },
  { to: "/progress", label: "Progression", icon: BarChart3 },
  { to: "/notifications", label: "Notifications", icon: Bell },
  { to: "/b2b", label: "Entreprise", icon: Building2 },
  { to: "/profile", label: "Profil", icon: User },
];

function NavLinks({ mobile = false, onNavigate }) {
  const location = useLocation();

  return (
    <>
      {navItems.map(({ to, label, icon: Icon }) => {
        const isActive = location.pathname === to ||
          (to === "/dashboard" && location.pathname === "/");

        return (
          <Link
            key={to}
            to={to}
            className={`nav-item flex items-center gap-3 px-4 py-3 rounded-xl ${
              isActive
                ? "active"
                : "text-muted-foreground hover:text-foreground"
            }`}
            onClick={() => mobile && onNavigate?.()}
          >
            <Icon className="w-5 h-5" />
            <span>{label}</span>
          </Link>
        );
      })}
    </>
  );
}

export default function Sidebar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <>
      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex fixed left-0 top-0 bottom-0 w-64 flex-col p-6 border-r border-border bg-card/50">
        <div className="flex items-center gap-2 mb-8">
          <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center">
            <Timer className="w-6 h-6 text-primary-foreground" />
          </div>
          <span className="font-heading text-xl font-semibold">InFinea</span>
        </div>

        <nav className="flex flex-col gap-1 flex-1">
          <NavLinks />
        </nav>

        <div className="pt-4 border-t border-border">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-muted-foreground hover:text-foreground hover:bg-white/5 transition-colors"
            data-testid="logout-btn"
          >
            <LogOut className="w-5 h-5" />
            <span>Déconnexion</span>
          </button>
        </div>
      </aside>

      {/* Mobile Header */}
      <header className="lg:hidden fixed top-0 left-0 right-0 z-50 glass">
        <div className="flex items-center justify-between px-4 h-16">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
              <Timer className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="font-heading text-lg font-semibold">InFinea</span>
          </div>

          <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" data-testid="mobile-menu-btn">
                <Menu className="w-6 h-6" />
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-72 bg-card p-6">
              <nav className="flex flex-col gap-1 mt-8">
                <NavLinks mobile onNavigate={() => setMobileMenuOpen(false)} />
              </nav>
              <div className="mt-auto pt-4 border-t border-border absolute bottom-6 left-6 right-6">
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-muted-foreground hover:text-foreground"
                >
                  <LogOut className="w-5 h-5" />
                  <span>Déconnexion</span>
                </button>
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </header>
    </>
  );
}
