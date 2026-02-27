import React, { useEffect, useRef, useState } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";

// Pages
import LandingPage from "@/pages/LandingPage";
import LoginPage from "@/pages/LoginPage";
import RegisterPage from "@/pages/RegisterPage";
import Dashboard from "@/pages/Dashboard";
import ActionsLibrary from "@/pages/ActionsLibrary";
import ActiveSession from "@/pages/ActiveSession";
import ProgressStats from "@/pages/ProgressStats";
import PricingPage from "@/pages/PricingPage";
import ProfilePage from "@/pages/ProfilePage";
import BadgesPage from "@/pages/BadgesPage";
import NotificationsPage from "@/pages/NotificationsPage";
import B2BDashboard from "@/pages/B2BDashboard";
import IntegrationsPage from "@/pages/IntegrationsPage";
import JournalPage from "@/pages/JournalPage";
import OnboardingPage from "@/pages/OnboardingPage";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "http://localhost:8000";
export const API = `${BACKEND_URL}/api`;

// Helper fetch that always includes auth token from localStorage
export const authFetch = (url, options = {}) => {
  const token = localStorage.getItem("infinea_token");
  const headers = {
    ...options.headers,
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return fetch(url, {
    ...options,
    credentials: "include",
    headers,
  });
};

// Register Service Worker for PWA
const registerServiceWorker = async () => {
  if ("serviceWorker" in navigator) {
    try {
      const registration = await navigator.serviceWorker.register("/sw.js");
      console.log("Service Worker registered:", registration.scope);
    } catch (error) {
      console.error("Service Worker registration failed:", error);
    }
  }
};

// Auth Context
export const AuthContext = React.createContext(null);

export const useAuth = () => {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
};

// Auth Callback Component - Handles Google OAuth redirect
const AuthCallback = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const hasProcessed = useRef(false);
  const { setUser } = useAuth();

  useEffect(() => {
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const processAuth = async () => {
      const hash = location.hash;
      const sessionId = new URLSearchParams(hash.substring(1)).get("session_id");

      if (!sessionId) {
        navigate("/login");
        return;
      }

      try {
        const response = await fetch(`${API}/auth/session`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ session_id: sessionId }),
        });

        if (!response.ok) {
          throw new Error("Auth failed");
        }

        const userData = await response.json();

        // Store token in localStorage
        if (userData.token) {
          localStorage.setItem("infinea_token", userData.token);
        }

        setUser(userData);
        navigate("/dashboard", { state: { user: userData } });
      } catch (error) {
        console.error("OAuth error:", error);
        navigate("/login");
      }
    };

    processAuth();
  }, [location, navigate, setUser]);

  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="text-center">
        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <p className="text-muted-foreground">Connexion en cours...</p>
      </div>
    </div>
  );
};

// Protected Route — robust version handling React 19 StrictMode double-mount
const ProtectedRoute = ({ children }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, setUser } = useAuth();
  const [authState, setAuthState] = useState("checking"); // "checking" | "authenticated" | "unauthenticated"

  useEffect(() => {
    let cancelled = false;

    // 1. User already in context (set by LoginPage/RegisterPage before navigate)
    if (user) {
      setAuthState("authenticated");
      return;
    }

    // 2. User data passed via navigation state (from login/register navigate)
    if (location.state?.user) {
      setUser(location.state.user);
      setAuthState("authenticated");
      return;
    }

    // 3. Check localStorage token → verify with backend
    const token = localStorage.getItem("infinea_token");
    if (!token) {
      if (!cancelled) {
        setAuthState("unauthenticated");
        navigate("/login", { replace: true });
      }
      return;
    }

    // Token exists, verify it with backend
    const verifyToken = async () => {
      try {
        const response = await fetch(`${API}/auth/me`, {
          credentials: "include",
          headers: { "Authorization": `Bearer ${token}` },
        });

        if (!response.ok) throw new Error("Token invalid");

        const userData = await response.json();
        if (!cancelled) {
          setUser(userData);
          setAuthState("authenticated");
        }
      } catch (error) {
        console.error("Auth verification failed:", error);
        localStorage.removeItem("infinea_token");
        if (!cancelled) {
          setAuthState("unauthenticated");
          navigate("/login", { replace: true });
        }
      }
    };

    verifyToken();

    return () => { cancelled = true; };
  }, [user, location.state, navigate, setUser]);

  if (authState === "checking") {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (authState === "unauthenticated") {
    return null;
  }

  return children;
};

// App Router
function AppRouter() {
  const location = useLocation();

  // Check for session_id in URL hash (Google OAuth callback)
  if (location.hash?.includes("session_id=")) {
    return <AuthCallback />;
  }

  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/pricing" element={<PricingPage />} />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/actions"
        element={
          <ProtectedRoute>
            <ActionsLibrary />
          </ProtectedRoute>
        }
      />
      <Route
        path="/session/:sessionId"
        element={
          <ProtectedRoute>
            <ActiveSession />
          </ProtectedRoute>
        }
      />
      <Route
        path="/progress"
        element={
          <ProtectedRoute>
            <ProgressStats />
          </ProtectedRoute>
        }
      />
      <Route
        path="/profile"
        element={
          <ProtectedRoute>
            <ProfilePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/badges"
        element={
          <ProtectedRoute>
            <BadgesPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/notifications"
        element={
          <ProtectedRoute>
            <NotificationsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/b2b"
        element={
          <ProtectedRoute>
            <B2BDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/integrations"
        element={
          <ProtectedRoute>
            <IntegrationsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/journal"
        element={
          <ProtectedRoute>
            <JournalPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/onboarding"
        element={
          <ProtectedRoute>
            <OnboardingPage />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

// Auth Provider
const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);

  const logout = async () => {
    try {
      const token = localStorage.getItem("infinea_token");
      await fetch(`${API}/auth/logout`, {
        method: "POST",
        credentials: "include",
        headers: token ? { "Authorization": `Bearer ${token}` } : {},
      });
    } catch (e) {
      console.error("Logout error:", e);
    }
    localStorage.removeItem("infinea_token");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, setUser, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

function App() {
  useEffect(() => {
    registerServiceWorker();
  }, []);

  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRouter />
        <Toaster position="top-right" richColors />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
