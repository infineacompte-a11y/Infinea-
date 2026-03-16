import React, { useState, useEffect, useCallback } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
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
  Users,
  LogOut,
  Menu,
  Target,
  CalendarClock,
  Zap,
} from "lucide-react";
import { API, authFetch, useAuth } from "@/App";
import LanguageSelector from "@/components/LanguageSelector";

// ─── Lightweight poll for unread notification count ───
function useUnreadCount(intervalMs = 60000) {
  const [count, setCount] = useState(0);
  const location = useLocation();

  const fetch_ = useCallback(async () => {
    try {
      const res = await authFetch(`${API}/notifications/unread-count`);
      if (res.ok) {
        const data = await res.json();
        setCount(data.unread_count || 0);
      }
    } catch { /* silent */ }
  }, []);

  useEffect(() => {
    fetch_();
    const id = setInterval(fetch_, intervalMs);
    return () => clearInterval(id);
  }, [fetch_, intervalMs]);

  useEffect(() => {
    if (location.pathname === "/notifications") {
      const t = setTimeout(() => fetch_(), 2000);
      return () => clearTimeout(t);
    }
  }, [location.pathname, fetch_]);

  return count;
}

const NAV_ITEMS = [
  { to: "/dashboard", key: "dashboard", icon: LayoutGrid },
  { to: "/my-day", key: "myDay", icon: Zap },
  { to: "/micro-instants", key: "microInstants", icon: Timer },
  { to: "/objectives", key: "objectives", icon: Target },
  { to: "/routines", key: "routines", icon: CalendarClock },
  { to: "/actions", key: "library", icon: Sparkles },
  { to: "/integrations", key: "integrations", icon: Calendar },
  { to: "/journal", key: "journal", icon: Brain },
  { to: "/notes", key: "notes", icon: FileText },
  { to: "/groups", key: "groups", icon: Users },
  { to: "/badges", key: "badges", icon: Award },
  { to: "/progress", key: "progress", icon: BarChart3 },
  { to: "/notifications", key: "notifications", icon: Bell },
  { to: "/b2b", key: "business", icon: Building2 },
  { to: "/profile", key: "profile", icon: User },
];

function NavLinks({ mobile = false, onNavigate, unreadCount = 0 }) {
  const { t } = useTranslation();
  const location = useLocation();

  return (
    <>
      {NAV_ITEMS.map(({ to, key, icon: Icon }) => {
        const isActive = location.pathname === to ||
          (to === "/dashboard" && location.pathname === "/");
        const isNotif = to === "/notifications";

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
            <div className="relative">
              <Icon className="w-5 h-5" />
              {isNotif && unreadCount > 0 && (
                <span className="absolute -top-1.5 -right-1.5 min-w-[16px] h-4 px-1 flex items-center justify-center rounded-full bg-red-500 text-white text-[9px] font-bold leading-none">
                  {unreadCount > 99 ? "99+" : unreadCount}
                </span>
              )}
            </div>
            <span>{t(`sidebar.${key}`)}</span>
          </Link>
        );
      })}
    </>
  );
}

export default function Sidebar() {
  const { t } = useTranslation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { logout } = useAuth();
  const navigate = useNavigate();
  const unreadCount = useUnreadCount();

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
          <NavLinks unreadCount={unreadCount} />
        </nav>

        <div className="pt-4 border-t border-border space-y-2">
          <LanguageSelector className="px-4 py-2" />
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-muted-foreground hover:text-foreground hover:bg-white/5 transition-colors"
            data-testid="logout-btn"
          >
            <LogOut className="w-5 h-5" />
            <span>{t("sidebar.logout")}</span>
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
              <Button variant="ghost" size="icon" data-testid="mobile-menu-btn" className="relative">
                <Menu className="w-6 h-6" />
                {unreadCount > 0 && (
                  <span className="absolute top-1 right-1 w-2.5 h-2.5 rounded-full bg-red-500 ring-2 ring-background" />
                )}
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-72 bg-card p-6">
              <nav className="flex flex-col gap-1 mt-8">
                <NavLinks mobile onNavigate={() => setMobileMenuOpen(false)} unreadCount={unreadCount} />
              </nav>
              <div className="mt-auto pt-4 border-t border-border absolute bottom-6 left-6 right-6 space-y-2">
                <LanguageSelector className="px-4 py-2" />
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-muted-foreground hover:text-foreground"
                >
                  <LogOut className="w-5 h-5" />
                  <span>{t("sidebar.logout")}</span>
                </button>
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </header>
    </>
  );
}
