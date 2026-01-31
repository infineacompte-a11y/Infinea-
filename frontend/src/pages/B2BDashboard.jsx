import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Timer,
  Sparkles,
  LayoutGrid,
  BarChart3,
  User,
  LogOut,
  Menu,
  Building2,
  Users,
  TrendingUp,
  Clock,
  Activity,
  Plus,
  Send,
  Heart,
  BookOpen,
  Target,
  Loader2,
} from "lucide-react";
import { toast } from "sonner";
import { API, useAuth } from "@/App";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
} from "recharts";

const categoryColors = {
  learning: "#3b82f6",
  productivity: "#f59e0b",
  well_being: "#10b981",
};

const categoryLabels = {
  learning: "Apprentissage",
  productivity: "Productivité",
  well_being: "Bien-être",
};

export default function B2BDashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [company, setCompany] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [employees, setEmployees] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [showCreateCompany, setShowCreateCompany] = useState(false);
  const [showInvite, setShowInvite] = useState(false);
  const [companyForm, setCompanyForm] = useState({ name: "", domain: "" });
  const [inviteEmail, setInviteEmail] = useState("");

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      // Check if user has a company
      const companyRes = await fetch(`${API}/b2b/company`, { credentials: "include" });
      
      if (companyRes.ok) {
        const companyData = await companyRes.json();
        setCompany(companyData);

        // Fetch dashboard and employees
        const [dashRes, empRes] = await Promise.all([
          fetch(`${API}/b2b/dashboard`, { credentials: "include" }),
          fetch(`${API}/b2b/employees`, { credentials: "include" }),
        ]);

        if (dashRes.ok) setDashboard(await dashRes.json());
        if (empRes.ok) {
          const empData = await empRes.json();
          setEmployees(empData.employees || []);
        }
      } else {
        setShowCreateCompany(true);
      }
    } catch (error) {
      console.error("Error fetching data:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateCompany = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API}/b2b/company`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(companyForm),
      });

      if (!res.ok) throw new Error("Erreur");

      const data = await res.json();
      toast.success("Entreprise créée avec succès!");
      setShowCreateCompany(false);
      fetchData();
    } catch (error) {
      toast.error("Erreur lors de la création");
    }
  };

  const handleInvite = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API}/b2b/invite`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email: inviteEmail }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Erreur");
      }

      toast.success("Invitation envoyée!");
      setInviteEmail("");
      setShowInvite(false);
    } catch (error) {
      toast.error(error.message);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  const pieData = dashboard
    ? Object.entries(dashboard.category_distribution || {}).map(([key, value]) => ({
        name: categoryLabels[key] || key,
        value: value.sessions,
        color: categoryColors[key] || "#6366f1",
      }))
    : [];

  const NavLinks = ({ mobile = false }) => (
    <>
      <Link
        to="/dashboard"
        className="nav-item flex items-center gap-3 px-4 py-3 rounded-xl text-muted-foreground hover:text-foreground"
        onClick={() => mobile && setMobileMenuOpen(false)}
      >
        <LayoutGrid className="w-5 h-5" />
        <span>Dashboard</span>
      </Link>
      <Link
        to="/b2b"
        className="nav-item active flex items-center gap-3 px-4 py-3 rounded-xl"
        onClick={() => mobile && setMobileMenuOpen(false)}
      >
        <Building2 className="w-5 h-5" />
        <span>Entreprise</span>
      </Link>
      <Link
        to="/progress"
        className="nav-item flex items-center gap-3 px-4 py-3 rounded-xl text-muted-foreground hover:text-foreground"
        onClick={() => mobile && setMobileMenuOpen(false)}
      >
        <BarChart3 className="w-5 h-5" />
        <span>Progression</span>
      </Link>
      <Link
        to="/profile"
        className="nav-item flex items-center gap-3 px-4 py-3 rounded-xl text-muted-foreground hover:text-foreground"
        onClick={() => mobile && setMobileMenuOpen(false)}
      >
        <User className="w-5 h-5" />
        <span>Profil</span>
      </Link>
    </>
  );

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  if (showCreateCompany && !company) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <Card className="max-w-md w-full">
          <CardHeader>
            <CardTitle className="font-heading text-2xl flex items-center gap-2">
              <Building2 className="w-6 h-6 text-primary" />
              Créer votre entreprise
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreateCompany} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">Nom de l'entreprise</Label>
                <Input
                  id="name"
                  placeholder="Ma Super Entreprise"
                  value={companyForm.name}
                  onChange={(e) => setCompanyForm({ ...companyForm, name: e.target.value })}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="domain">Domaine email</Label>
                <Input
                  id="domain"
                  placeholder="entreprise.com"
                  value={companyForm.domain}
                  onChange={(e) => setCompanyForm({ ...companyForm, domain: e.target.value })}
                  required
                />
                <p className="text-xs text-muted-foreground">
                  Les collaborateurs devront avoir un email @{companyForm.domain || "domaine.com"}
                </p>
              </div>
              <Button type="submit" className="w-full">
                Créer l'entreprise
              </Button>
              <Button
                type="button"
                variant="ghost"
                className="w-full"
                onClick={() => navigate("/dashboard")}
              >
                Annuler
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
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
            </SheetContent>
          </Sheet>
        </div>
      </header>

      {/* Main Content */}
      <main className="lg:ml-64 pt-20 lg:pt-8 px-4 lg:px-8 pb-8">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="font-heading text-3xl font-semibold mb-2" data-testid="b2b-title">
                {company?.name || "Dashboard Entreprise"}
              </h1>
              <p className="text-muted-foreground">
                Tableau de bord QVT anonymisé
              </p>
            </div>
            <Dialog open={showInvite} onOpenChange={setShowInvite}>
              <DialogTrigger asChild>
                <Button data-testid="invite-btn">
                  <Plus className="w-4 h-4 mr-2" />
                  Inviter
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Inviter un collaborateur</DialogTitle>
                  <DialogDescription>
                    L'email doit être @{company?.domain}
                  </DialogDescription>
                </DialogHeader>
                <form onSubmit={handleInvite} className="space-y-4 mt-4">
                  <Input
                    type="email"
                    placeholder={`collaborateur@${company?.domain}`}
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    required
                  />
                  <Button type="submit" className="w-full">
                    <Send className="w-4 h-4 mr-2" />
                    Envoyer l'invitation
                  </Button>
                </form>
              </DialogContent>
            </Dialog>
          </div>

          {/* KPIs */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <Card className="stat-card">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
                    <Users className="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <p className="text-2xl font-heading font-bold">
                      {dashboard?.employee_count || 0}
                    </p>
                    <p className="text-xs text-muted-foreground">collaborateurs</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="stat-card">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-xl bg-emerald-500/10 flex items-center justify-center">
                    <Activity className="w-6 h-6 text-emerald-500" />
                  </div>
                  <div>
                    <p className="text-2xl font-heading font-bold">
                      {dashboard?.engagement_rate || 0}%
                    </p>
                    <p className="text-xs text-muted-foreground">engagement</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="stat-card">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-xl bg-amber-500/10 flex items-center justify-center">
                    <Clock className="w-6 h-6 text-amber-500" />
                  </div>
                  <div>
                    <p className="text-2xl font-heading font-bold">
                      {Math.round((dashboard?.total_time_minutes || 0) / 60)}h
                    </p>
                    <p className="text-xs text-muted-foreground">total investies</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="stat-card bg-gradient-to-br from-primary/10 to-purple-500/10 border-primary/30">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-xl bg-primary/20 flex items-center justify-center">
                    <TrendingUp className="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <p className="text-2xl font-heading font-bold">
                      {dashboard?.qvt_score || 0}
                    </p>
                    <p className="text-xs text-muted-foreground">score QVT</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Charts */}
          <div className="grid lg:grid-cols-2 gap-6 mb-8">
            {/* Activity Over Time */}
            <Card>
              <CardHeader>
                <CardTitle className="font-heading text-lg">Activité (28 derniers jours)</CardTitle>
              </CardHeader>
              <CardContent>
                {dashboard?.daily_activity?.length > 0 ? (
                  <ResponsiveContainer width="100%" height={250}>
                    <LineChart data={dashboard.daily_activity}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                      <XAxis
                        dataKey="_id"
                        tick={{ fill: "#a1a1aa", fontSize: 10 }}
                        tickFormatter={(v) => v.slice(5)}
                      />
                      <YAxis tick={{ fill: "#a1a1aa", fontSize: 12 }} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "#121212",
                          border: "1px solid #27272a",
                          borderRadius: "8px",
                        }}
                      />
                      <Line
                        type="monotone"
                        dataKey="sessions"
                        stroke="#6366f1"
                        strokeWidth={2}
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-[250px] flex items-center justify-center text-muted-foreground">
                    <p>Pas encore de données</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Category Distribution */}
            <Card>
              <CardHeader>
                <CardTitle className="font-heading text-lg">Répartition par catégorie</CardTitle>
              </CardHeader>
              <CardContent>
                {pieData.length > 0 ? (
                  <>
                    <ResponsiveContainer width="100%" height={200}>
                      <PieChart>
                        <Pie
                          data={pieData}
                          cx="50%"
                          cy="50%"
                          innerRadius={50}
                          outerRadius={80}
                          paddingAngle={5}
                          dataKey="value"
                        >
                          {pieData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip
                          contentStyle={{
                            backgroundColor: "#121212",
                            border: "1px solid #27272a",
                            borderRadius: "8px",
                          }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                    <div className="flex justify-center gap-4 mt-4">
                      {pieData.map((entry, i) => (
                        <div key={i} className="flex items-center gap-2">
                          <div
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: entry.color }}
                          />
                          <span className="text-sm text-muted-foreground">{entry.name}</span>
                        </div>
                      ))}
                    </div>
                  </>
                ) : (
                  <div className="h-[250px] flex items-center justify-center text-muted-foreground">
                    <p>Pas encore de données</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Employees List */}
          <Card>
            <CardHeader>
              <CardTitle className="font-heading text-lg">Collaborateurs</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {employees.map((emp, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between p-4 rounded-xl bg-white/5"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                        <span className="text-sm font-medium">{emp.employee_number}</span>
                      </div>
                      <div>
                        <p className="font-medium">
                          {emp.name}
                          {emp.is_admin && (
                            <Badge variant="secondary" className="ml-2 text-xs">
                              Admin
                            </Badge>
                          )}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {emp.total_sessions} sessions • {emp.total_time} min
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-amber-500">
                        {emp.streak_days} jours
                      </p>
                      <p className="text-xs text-muted-foreground">streak</p>
                    </div>
                  </div>
                ))}
                {employees.length === 0 && (
                  <div className="text-center py-8 text-muted-foreground">
                    <Users className="w-10 h-10 mx-auto mb-2 opacity-50" />
                    <p>Aucun collaborateur</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
