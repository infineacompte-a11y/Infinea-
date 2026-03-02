import React, { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import {
  Timer,
  LayoutGrid,
  Sparkles,
  Trophy,
  Brain,
  Award,
  BarChart3,
  Calendar,
  Bell,
  Building2,
  User,
  LogOut,
  Menu,
} from "lucide-react";

const NAV_ITEMS = [
  { key: "dashboard", label: "Dashboard", to: "/dashboard", icon: LayoutGrid },
  { key: "actions", label: "Bibliothèque", to: "/actions", icon: Sparkles },
  { key: "challenges", label: "Défis", to: "/challenges", icon: Trophy },
  { key: "journal", label: "Journal", to: "/journal", icon: Brain },
  { key: "badges", label: "Badges", to: "/badges", icon: Award },
  { key: "progress", label: "Progression", to: "/progress", icon: BarChart3 },
  { key: "integrations", label: "Intégrations", to: "/integrations", icon: Calendar },
  { key: "notifications", label: "Notifications", to: "/notifications", icon: Bell },
  { key: "b2b", label: "Entreprise", to: "/b2b", icon: Building2 },
  { key: "profile", label: "Profil", to: "/profile", icon: User },
];

export default function AppSidebar({ activePage, onLogout, notificationCount }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const NavLinks = ({ mobile = false }) => (
    <>
      {NAV_ITEMS.map((item) => {
        const Icon = item.icon;
        const isActive = item.key === activePage;
        return (
          <Link
            key={item.key}
            to={item.to}
            className={
              isActive
                ? "nav-item active flex items-center gap-3 px-4 py-3 rounded-xl"
                : "nav-item flex items-center gap-3 px-4 py-3 rounded-xl text-muted-foreground hover:text-foreground"
            }
            onClick={() => mobile && setMobileMenuOpen(false)}
          >
            <Icon className="w-5 h-5" />
            <span>{item.label}</span>
            {item.key === "notifications" && notificationCount > 0 && (
              <Badge variant="destructive" className="ml-auto">
                {notificationCount}
              </Badge>
            )}
          </Link>
        );
      })}
    </>
  );

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
            onClick={onLogout}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-muted-foreground hover:text-foreground hover:bg-white/5 transition-colors"
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
              <Button variant="ghost" size="icon">
                <Menu className="w-6 h-6" />
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-72 bg-card p-6">
              <nav className="flex flex-col gap-1 mt-8">
                <NavLinks mobile />
              </nav>
              <div className="mt-auto pt-4 border-t border-border absolute bottom-6 left-6 right-6">
                <button
                  onClick={onLogout}
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
