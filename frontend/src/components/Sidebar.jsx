import React, { useState, useEffect, useCallback, useRef, useLayoutEffect } from "react";
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
  Activity,
  Search,
  MessageCircle,
  Medal,
  Shield,
  PlusCircle,
} from "lucide-react";
import InFineaLogo from "@/components/InFineaLogo";
import { API, authFetch, useAuth } from "@/App";

// ─── Lightweight poll for unread message count ───
function useUnreadMessages(intervalMs = 30000) {
  const [count, setCount] = useState(0);
  const location = useLocation();

  const fetch_ = useCallback(async () => {
    try {
      const res = await authFetch(`${API}/messages/unread-count`);
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
    if (location.pathname.startsWith("/messages")) {
      const t = setTimeout(() => fetch_(), 2000);
      return () => clearTimeout(t);
    }
  }, [location.pathname, fetch_]);

  return count;
}

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
      { to: "/journal", label: "Journal", icon: Brain },
      { to: "/notes", label: "Notes", icon: FileText },
    ],
  },
  {
    label: "Communauté",
    items: [
      { to: "/community", label: "Communauté", icon: Activity },
      { to: "/messages", label: "Messages", icon: MessageCircle },
      { to: "/search", label: "Rechercher", icon: Search },
      { to: "/groups", label: "Groupes", icon: Users },
      { to: "/challenges", label: "Défis", icon: Trophy },
      { to: "/leaderboard", label: "Classement", icon: Medal },
    ],
  },
  {
    label: "Réglages",
    items: [
      { to: "/integrations", label: "Intégrations", icon: Calendar },
      { to: "/b2b", label: "Entreprise", icon: Building2 },
    ],
  },
];

// Bottom nav items (always visible, outside groups)
const bottomItems = [
  { to: "/profile", label: "Profil", icon: User },
  { to: "/notifications", label: "Notifications", icon: Bell },
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

function GroupedNav({ mobile = false, onNavigate, unreadCount = 0, unreadMessages = 0, isAdmin = false }) {
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
              const isMsg = item.to === "/messages";
              return (
                <NavItem
                  key={item.to}
                  {...item}
                  isActive={isActive}
                  isNotif={isMsg}
                  unreadCount={isMsg ? unreadMessages : 0}
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

      {/* Admin — visible only for admins */}
      {isAdmin && (
        <>
          <div className="my-2 mx-3 h-px bg-gradient-to-r from-transparent via-[#E48C75]/30 to-transparent" />
          <div className="px-3 mb-1.5">
            <span className="text-[10px] font-semibold uppercase tracking-[0.08em] text-[#E48C75]/60">
              Admin
            </span>
          </div>
          <NavItem
            to="/admin/moderation"
            label="Modération"
            icon={Shield}
            isActive={location.pathname === "/admin/moderation"}
            mobile={mobile}
            onNavigate={onNavigate}
            animDelay={mobile ? null : (globalIndex++) * 25}
          />
          <NavItem
            to="/admin/ai"
            label="IA Verticale"
            icon={Brain}
            isActive={location.pathname === "/admin/ai"}
            mobile={mobile}
            onNavigate={onNavigate}
            animDelay={mobile ? null : (globalIndex++) * 25}
          />
        </>
      )}
    </div>
  );
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// MOBILE BOTTOM NAVIGATION — Instagram/TikTok/Strava/Duolingo pattern
// 5 tabs: Home, Feed, Create, Messages, Profile
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

const BOTTOM_TABS = [
  { to: "/my-day", label: "Accueil", icon: Zap },
  { to: "/community", label: "Feed", icon: Activity },
  { to: "/__create__", label: "Créer", icon: PlusCircle, isCreate: true },
  { to: "/messages", label: "Messages", icon: MessageCircle },
  { to: "/profile", label: "Profil", icon: User },
];

function MobileBottomNav({ unreadMessages = 0 }) {
  const location = useLocation();
  const navigate = useNavigate();

  // Hide on specific pages where bottom nav would interfere
  const hideOn = ["/login", "/register", "/onboarding", "/landing", "/session/"];
  const shouldHide = hideOn.some((p) => location.pathname.startsWith(p));
  if (shouldHide) return null;

  return (
    <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-50 bg-white/90 backdrop-blur-2xl backdrop-saturate-[1.8] border-t border-[#E2E6EA]/60 shadow-[0_-1px_20px_rgba(39,82,85,0.06)]">
      {/* Safe area padding for iPhones with home indicator */}
      <div className="flex items-center justify-around h-16 px-2 pb-[env(safe-area-inset-bottom)]">
        {BOTTOM_TABS.map((tab) => {
          const isActive =
            location.pathname === tab.to ||
            (tab.to === "/my-day" && location.pathname === "/dashboard") ||
            (tab.to === "/community" && location.pathname.startsWith("/activity/")) ||
            (tab.to === "/messages" && location.pathname.startsWith("/messages/")) ||
            (tab.to === "/profile" && location.pathname.startsWith("/users/"));
          const Icon = tab.icon;
          const isMsg = tab.to === "/messages";

          if (tab.isCreate) {
            return (
              <button
                key="create"
                onClick={() => navigate("/community", { state: { focusCreate: true } })}
                className="flex flex-col items-center justify-center gap-0.5 -mt-3"
              >
                <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-[#459492] to-[#55B3AE] flex items-center justify-center shadow-lg shadow-[#459492]/25 active:scale-95 transition-transform">
                  <PlusCircle className="w-5 h-5 text-white" />
                </div>
              </button>
            );
          }

          return (
            <Link
              key={tab.to}
              to={tab.to}
              className={`relative flex flex-col items-center justify-center gap-0.5 min-w-[56px] py-1.5 rounded-xl transition-colors active:scale-95 active:transition-[transform] active:duration-75 ${
                isActive ? "text-[#459492]" : "text-[#98A2B3]"
              }`}
            >
              <div className="relative">
                <Icon className={`w-[22px] h-[22px] ${isActive ? "stroke-[2.5]" : "stroke-[1.8]"}`} />
                {isMsg && unreadMessages > 0 && (
                  <span className="absolute -top-1.5 -right-2.5 min-w-[16px] h-4 px-1 flex items-center justify-center rounded-full bg-[#E48C75] text-white text-[9px] font-bold leading-none shadow-sm">
                    {unreadMessages > 99 ? "99+" : unreadMessages}
                  </span>
                )}
              </div>
              <span className={`text-[10px] leading-tight ${isActive ? "font-semibold" : "font-medium"}`}>
                {tab.label}
              </span>
              {isActive && (
                <div className="absolute -bottom-1.5 w-5 h-0.5 rounded-full bg-[#459492]" />
              )}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}

// Persist sidebar scroll position across remounts (each page renders its own Sidebar)
let _sidebarScrollY = 0;

export default function Sidebar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { logout, user } = useAuth();
  const isAdmin = !!user?.is_admin;
  const navigate = useNavigate();
  const unreadCount = useUnreadCount(30000);
  const unreadMessages = useUnreadMessages();
  const navRef = useRef(null);

  // Restore scroll position on mount (useLayoutEffect to avoid flash)
  useLayoutEffect(() => {
    if (navRef.current) {
      navRef.current.scrollTop = _sidebarScrollY;
    }
  }, []);

  // Save scroll position on scroll
  const handleNavScroll = useCallback((e) => {
    _sidebarScrollY = e.target.scrollTop;
  }, []);

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
        <nav ref={navRef} onScroll={handleNavScroll} className="flex-1 overflow-y-auto px-3 py-1 scrollbar-thin">
          <GroupedNav unreadCount={unreadCount} unreadMessages={unreadMessages} isAdmin={isAdmin} />
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

          <div className="flex items-center gap-1">
            {/* Notification bell in header */}
            <Link
              to="/notifications"
              className="relative flex items-center justify-center w-9 h-9 rounded-lg text-[#667085] hover:text-[#275255] hover:bg-[#F0F7F7] transition-colors"
            >
              <Bell className="w-5 h-5" />
              {unreadCount > 0 && (
                <span className="absolute top-1 right-1 min-w-[16px] h-4 px-1 flex items-center justify-center rounded-full bg-[#E48C75] text-white text-[9px] font-bold leading-none shadow-sm">
                  {unreadCount > 99 ? "99+" : unreadCount}
                </span>
              )}
            </Link>
            <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
              <SheetTrigger asChild>
                <Button variant="ghost" size="icon" data-testid="mobile-menu-btn" className="relative text-[#667085] hover:text-[#275255] hover:bg-[#F0F7F7] h-9 w-9">
                  <Menu className="w-5 h-5" />
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
                  <GroupedNav mobile onNavigate={() => setMobileMenuOpen(false)} unreadCount={unreadCount} unreadMessages={unreadMessages} isAdmin={isAdmin} />
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
        </div>
      </header>

      {/* ━━━ Mobile Bottom Navigation ━━━
          Instagram/TikTok pattern — 5 tabs for instant access to core sections.
          Benchmarked: Instagram (5 tabs), TikTok (5 tabs), Strava (5 tabs), Duolingo (5 tabs).
          All major social/learning apps converge on this pattern for mobile engagement. */}
      <MobileBottomNav unreadMessages={unreadMessages} />
    </>
  );
}
