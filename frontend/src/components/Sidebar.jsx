import React, { useState, useEffect, useCallback } from "react";
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
  Trophy,
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
  ChevronRight,
} from "lucide-react";
import InFineaLogo from "@/components/InFineaLogo";
import { API, authFetch, useAuth } from "@/App";

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

// ─── Grouped navigation structure ───
const navGroups = [
  {
    label: null, // Main — no header
    items: [
      { to: "/dashboard", label: "Dashboard", icon: LayoutGrid },
      { to: "/my-day", label: "Ma Journée", icon: Zap },
    ],
  },
  {
    label: "Actions",
    items: [
      { to: "/micro-instants", label: "Micro-Instants", icon: Timer },
      { to: "/actions", label: "Bibliothèque", icon: Sparkles },
      { to: "/objectives", label: "Objectifs", icon: Target },
      { to: "/routines", label: "Habitudes", icon: CalendarClock },
    ],
  },
  {
    label: "Suivi",
    items: [
      { to: "/progress", label: "Progression", icon: BarChart3 },
      { to: "/badges", label: "Badges", icon: Award },
      { to: "/challenges", label: "Défis", icon: Trophy },
      { to: "/journal", label: "Journal", icon: Brain },
      { to: "/notes", label: "Notes", icon: FileText },
    ],
  },
  {
    label: "Réseau",
    items: [
      { to: "/groups", label: "Groupes", icon: Users },
      { to: "/integrations", label: "Intégrations", icon: Calendar },
      { to: "/b2b", label: "Entreprise", icon: Building2 },
    ],
  },
];

// Bottom nav items (always visible, outside groups)
const bottomItems = [
  { to: "/notifications", label: "Notifications", icon: Bell },
  { to: "/profile", label: "Profil", icon: User },
];

function NavItem({ to, label, icon: Icon, isActive, isNotif, unreadCount, mobile, onNavigate, animDelay }) {
  return (
    <Link
      key={to}
      to={to}
      className={`nav-item group flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 focus-visible:ring-2 focus-visible:ring-[#459492]/50 focus-visible:outline-none active:scale-[0.98] active:transition-[transform] active:duration-75 ${
        isActive
          ? "bg-gradient-to-r from-[#459492]/15 to-[#55B3AE]/8 text-[#275255] font-semibold shadow-sm shadow-[0_1px_3px_rgba(39,82,85,0.06)] border border-[#459492]/20 border-l-[3px] border-l-[#459492]"
          : "text-[#667085] hover:text-[#275255] hover:bg-[#459492]/[0.06] border border-transparent"
      }`}
      style={animDelay != null ? { animationDelay: `${animDelay}ms`, animationFillMode: "forwards" } : undefined}
      onClick={() => mobile && onNavigate?.()}
    >
      <div className={`relative flex items-center justify-center w-8 h-8 rounded-lg transition-colors ${
        isActive ? "bg-[#459492]/15" : "group-hover:bg-[#459492]/8"
      }`}>
        <Icon className={`w-[18px] h-[18px] ${isActive ? "text-[#459492]" : ""}`} />
        {isNotif && unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 min-w-[16px] h-4 px-1 flex items-center justify-center rounded-full bg-[#E48C75] text-white text-[9px] font-bold leading-none shadow-sm">
            {unreadCount > 99 ? "99+" : unreadCount}
          </span>
        )}
      </div>
      <span className="text-[13px] tracking-wide">{label}</span>
      {isActive && (
        <ChevronRight className="w-3.5 h-3.5 ml-auto text-[#459492]/50" />
      )}
    </Link>
  );
}

function GroupedNav({ mobile = false, onNavigate, unreadCount = 0 }) {
  const location = useLocation();
  let globalIndex = 0;

  return (
    <div className="flex flex-col gap-1">
      {navGroups.map((group, gi) => (
        <div key={gi} className={gi > 0 ? "mt-3" : ""}>
          {group.label && (
            <div className="px-3 mb-1.5">
              <span className="text-[10px] font-semibold uppercase tracking-[0.08em] text-[#459492]/60">
                {group.label}
              </span>
            </div>
          )}
          <div className="flex flex-col gap-0.5">
            {group.items.map((item) => {
              const idx = globalIndex++;
              const isActive = location.pathname === item.to ||
                (item.to === "/dashboard" && location.pathname === "/");
              return (
                <NavItem
                  key={item.to}
                  {...item}
                  isActive={isActive}
                  isNotif={false}
                  unreadCount={0}
                  mobile={mobile}
                  onNavigate={onNavigate}
                  animDelay={mobile ? null : idx * 25}
                />
              );
            })}
          </div>
        </div>
      ))}

      {/* Separator */}
      <div className="my-2 mx-3 h-px bg-gradient-to-r from-transparent via-[#E2E6EA] to-transparent" />

      {/* Bottom items */}
      <div className="flex flex-col gap-0.5">
        {bottomItems.map((item) => {
          const idx = globalIndex++;
          const isActive = location.pathname === item.to;
          const isNotif = item.to === "/notifications";
          return (
            <NavItem
              key={item.to}
              {...item}
              isActive={isActive}
              isNotif={isNotif}
              unreadCount={unreadCount}
              mobile={mobile}
              onNavigate={onNavigate}
              animDelay={mobile ? null : idx * 25}
            />
          );
        })}
      </div>
    </div>
  );
}

export default function Sidebar() {
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
      <aside className="hidden lg:flex fixed left-0 top-0 bottom-0 w-64 z-40 flex-col sidebar-premium border-r border-[#E2E6EA]/60 shadow-[0_0_40px_rgba(39,82,85,0.06)]">
        {/* Logo */}
        <div className="px-6 pt-6 pb-4">
          <InFineaLogo size={34} withText />
          <div className="h-px mt-5 bg-gradient-to-r from-[#459492]/20 via-[#459492]/10 to-transparent" />
        </div>

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto px-3 py-1 scrollbar-thin">
          <GroupedNav unreadCount={unreadCount} />
        </nav>

        {/* Logout */}
        <div className="px-3 pb-4 pt-2">
          <div className="h-px mb-3 bg-gradient-to-r from-transparent via-[#E2E6EA] to-transparent" />
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-[#667085] hover:text-[#E48C75] hover:bg-[#E48C75]/5 transition-all duration-200 focus-visible:ring-2 focus-visible:ring-[#459492]/50 focus-visible:outline-none btn-press"
            data-testid="logout-btn"
          >
            <div className="flex items-center justify-center w-8 h-8 rounded-lg">
              <LogOut className="w-[18px] h-[18px]" />
            </div>
            <span className="text-[13px] tracking-wide">Déconnexion</span>
          </button>
        </div>
      </aside>

      {/* Mobile Header */}
      <header className="lg:hidden fixed top-0 left-0 right-0 z-50 bg-[#E8F4F3]/80 backdrop-blur-2xl backdrop-saturate-[2.0] border-b border-[#459492]/10 shadow-[0_1px_24px_rgba(39,82,85,0.10)]">
        <div className="flex items-center justify-between px-4 h-14">
          <InFineaLogo size={26} withText />

          <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" data-testid="mobile-menu-btn" className="relative text-[#667085] hover:text-[#275255] hover:bg-[#F0F7F7] h-9 w-9">
                <Menu className="w-5 h-5" />
                {unreadCount > 0 && (
                  <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-[#E48C75] ring-2 ring-white" />
                )}
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-72 bg-white/95 backdrop-blur-xl border-l border-[#E2E6EA]/80 shadow-2xl p-0 flex flex-col">
              {/* Mobile menu header */}
              <div className="px-5 pt-5 pb-3">
                <InFineaLogo size={28} withText />
                <div className="h-px mt-4 bg-gradient-to-r from-[#459492]/20 via-[#459492]/10 to-transparent" />
              </div>

              {/* Scrollable nav */}
              <nav className="flex-1 overflow-y-auto px-3 pb-2">
                <GroupedNav mobile onNavigate={() => setMobileMenuOpen(false)} unreadCount={unreadCount} />
              </nav>

              {/* Logout — properly positioned, not absolute */}
              <div className="px-3 pb-5 pt-2 border-t border-[#E2E6EA]/60">
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-[#667085] hover:text-[#E48C75] hover:bg-[#E48C75]/5 transition-all duration-200 btn-press"
                >
                  <div className="flex items-center justify-center w-8 h-8 rounded-lg">
                    <LogOut className="w-[18px] h-[18px]" />
                  </div>
                  <span className="text-[13px] tracking-wide">Déconnexion</span>
                </button>
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </header>
    </>
  );
}
