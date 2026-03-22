import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
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
  Trophy,
  Medal,
  Award,
  Download,
  UserPlus,
  CheckCircle,
  XCircle,
  ChevronRight,
  Brain,
  Flame,
  Zap,
  Calendar,
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
  DialogFooter,
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
  AreaChart,
  Area,
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

const categoryIcons = {
  learning: BookOpen,
  productivity: Target,
  well_being: Heart,
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
  const [showLeaderboard, setShowLeaderboard] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem("infinea_token");
      const headers = { Authorization: `Bearer ${token}` };

      // Check if user has a company
      const companyRes = await fetch(`${API}/b2b/company`, { 
        credentials: "include",
        headers 
      });
      
      if (companyRes.ok) {
        const companyData = await companyRes.json();
        setCompany(companyData);

        // Fetch dashboard and employees
        const [dashRes, empRes] = await Promise.all([
          fetch(`${API}/b2b/dashboard`, { credentials: "include", headers }),
          fetch(`${API}/b2b/employees`, { credentials: "include", headers }),
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
      const token = localStorage.getItem("infinea_token");
      const res = await fetch(`${API}/b2b/company`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}` 
        },
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
      const token = localStorage.getItem("infinea_token");
      const res = await fetch(`${API}/b2b/invite`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}` 
        },
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

  // Calculate ROI metrics
  const calculateROI = () => {
    if (!dashboard) return { wellbeingHours: 0, estimatedProductivityGain: 0 };
    
    const wellbeingTime = dashboard.category_distribution?.well_being?.time || 0;
    const wellbeingHours = Math.round(wellbeingTime / 60 * 10) / 10;
    // Estimated 15% productivity boost per hour of well-being activity
    const estimatedProductivityGain = Math.round(wellbeingHours * 15);
    
    return { wellbeingHours, estimatedProductivityGain };
  };

  const roi = calculateROI();

  const pieData = dashboard
    ? Object.entries(dashboard.category_distribution || {}).map(([key, value]) => ({
        name: categoryLabels[key] || key,
        value: value.sessions,
        time: value.time,
        color: categoryColors[key] || "#6366f1",
      }))
    : [];

  // Sort employees by total time for leaderboard
  const sortedEmployees = [...employees].sort((a, b) => b.total_time - a.total_time);

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
        to="/journal"
        className="nav-item flex items-center gap-3 px-4 py-3 rounded-xl text-muted-foreground hover:text-foreground"
        onClick={() => mobile && setMobileMenuOpen(false)}
      >
        <Brain className="w-5 h-5" />
        <span>Journal</span>
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
          <CardHeader className="text-center">
            <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-4">
              <Building2 className="w-8 h-8 text-primary" />
            </div>
            <CardTitle className="font-heading text-2xl">Créer votre espace entreprise</CardTitle>
            <CardDescription>
              Suivez la progression de votre équipe et mesurez l'impact QVT
            </CardDescription>
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
                  data-testid="company-name-input"
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
                  data-testid="company-domain-input"
                />
                <p className="text-xs text-muted-foreground">
                  Les collaborateurs devront avoir un email @{companyForm.domain || "domaine.com"}
                </p>
              </div>
              <Button type="submit" className="w-full" data-testid="create-company-btn">
                <Building2 className="w-4 h-4 mr-2" />
                Créer l'espace entreprise
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
              <div className="flex items-center gap-3 mb-2">
                <h1 className="font-heading text-3xl font-semibold" data-testid="b2b-title">
                  {company?.name || "Dashboard Entreprise"}
                </h1>
                <Badge className="bg-primary/20 text-primary border-primary/30">Manager</Badge>
              </div>
              <p className="text-muted-foreground">
                Analytics d'équipe & ROI bien-être
              </p>
            </div>
            <div className="flex gap-3">
              <Button variant="outline" onClick={() => toast.info("Export PDF bientôt disponible")}>
                <Download className="w-4 h-4 mr-2" />
                Export
              </Button>
              <Dialog open={showInvite} onOpenChange={setShowInvite}>
                <DialogTrigger asChild>
                  <Button data-testid="invite-btn">
                    <UserPlus className="w-4 h-4 mr-2" />
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
                      data-testid="invite-email-input"
                    />
                    <Button type="submit" className="w-full" data-testid="send-invite-btn">
                      <Send className="w-4 h-4 mr-2" />
                      Envoyer l'invitation
                    </Button>
                  </form>
                </DialogContent>
              </Dialog>
            </div>
          </div>

          {/* Overview KPIs */}
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
                    <p className="text-xs text-muted-foreground">collaborateurs actifs</p>
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
                    <p className="text-xs text-muted-foreground">taux d'engagement</p>
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
                    <p className="text-xs text-muted-foreground">temps total investi</p>
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

          {/* ROI Card */}
          <Card className="mb-8 bg-gradient-to-br from-emerald-500/5 to-blue-500/5 border-emerald-500/20">
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center">
                  <Zap className="w-5 h-5 text-emerald-500" />
                </div>
                <div>
                  <CardTitle className="font-heading text-lg">ROI Bien-être</CardTitle>
                  <CardDescription>Impact mesurable sur la productivité</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-3 gap-6">
                <div className="text-center p-4 rounded-xl bg-white/5">
                  <Heart className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
                  <p className="text-3xl font-heading font-bold text-emerald-500">{roi.wellbeingHours}h</p>
                  <p className="text-sm text-muted-foreground">en bien-être ce mois</p>
                </div>
                <div className="text-center p-4 rounded-xl bg-white/5">
                  <TrendingUp className="w-8 h-8 text-blue-500 mx-auto mb-2" />
                  <p className="text-3xl font-heading font-bold text-blue-500">+{roi.estimatedProductivityGain}%</p>
                  <p className="text-sm text-muted-foreground">productivité estimée</p>
                </div>
                <div className="text-center p-4 rounded-xl bg-white/5">
                  <Trophy className="w-8 h-8 text-amber-500 mx-auto mb-2" />
                  <p className="text-3xl font-heading font-bold text-amber-500">{dashboard?.total_sessions || 0}</p>
                  <p className="text-sm text-muted-foreground">sessions complétées</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Tabs */}
          <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="overview">Vue d'ensemble</TabsTrigger>
              <TabsTrigger value="team">Équipe</TabsTrigger>
              <TabsTrigger value="categories">Catégories</TabsTrigger>
            </TabsList>

            {/* Overview Tab */}
            <TabsContent value="overview" className="space-y-6">
              {/* Activity Chart */}
              <Card>
                <CardHeader>
                  <CardTitle className="font-heading text-lg">Activité (28 derniers jours)</CardTitle>
                </CardHeader>
                <CardContent>
                  {dashboard?.daily_activity?.length > 0 ? (
                    <ResponsiveContainer width="100%" height={250}>
                      <AreaChart data={dashboard.daily_activity}>
                        <defs>
                          <linearGradient id="colorSessions" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3}/>
                            <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                          </linearGradient>
                        </defs>
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
                        <Area
                          type="monotone"
                          dataKey="sessions"
                          stroke="#6366f1"
                          strokeWidth={2}
                          fill="url(#colorSessions)"
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-[250px] flex items-center justify-center text-muted-foreground">
                      <p>Pas encore de données d'activité</p>
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
                    <div className="grid md:grid-cols-2 gap-8 items-center">
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
                      <div className="space-y-4">
                        {pieData.map((entry, i) => {
                          const Icon = categoryIcons[Object.keys(categoryLabels).find(k => categoryLabels[k] === entry.name)] || Target;
                          return (
                            <div key={i} className="flex items-center justify-between p-3 rounded-xl bg-white/5">
                              <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${entry.color}20` }}>
                                  <Icon className="w-5 h-5" style={{ color: entry.color }} />
                                </div>
                                <div>
                                  <p className="font-medium">{entry.name}</p>
                                  <p className="text-xs text-muted-foreground">{entry.time} min</p>
                                </div>
                              </div>
                              <Badge variant="secondary">{entry.value} sessions</Badge>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  ) : (
                    <div className="h-[200px] flex items-center justify-center text-muted-foreground">
                      <p>Pas encore de données</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* Team Tab */}
            <TabsContent value="team" className="space-y-6">
              {/* Leaderboard Toggle */}
              <div className="flex items-center justify-between">
                <h2 className="font-heading text-lg font-semibold">Classement de l'équipe</h2>
                <div className="flex items-center gap-2">
                  <Label htmlFor="leaderboard-toggle" className="text-sm text-muted-foreground">
                    Classement gamifié
                  </Label>
                  <Switch
                    id="leaderboard-toggle"
                    checked={showLeaderboard}
                    onCheckedChange={setShowLeaderboard}
                  />
                </div>
              </div>

              {showLeaderboard ? (
                /* Gamified Leaderboard */
                <div className="space-y-3">
                  {sortedEmployees.map((emp, i) => {
                    const isTop3 = i < 3;
                    const medals = ["🥇", "🥈", "🥉"];
                    
                    return (
                      <Card 
                        key={i} 
                        className={`transition-all ${isTop3 ? "border-amber-500/30 bg-amber-500/5" : ""}`}
                        data-testid={`employee-card-${i}`}
                      >
                        <CardContent className="p-4">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-4">
                              <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                                isTop3 
                                  ? "bg-amber-500/20 text-2xl" 
                                  : "bg-primary/10"
                              }`}>
                                {isTop3 ? medals[i] : <span className="font-medium text-muted-foreground">#{i + 1}</span>}
                              </div>
                              <div>
                                <div className="flex items-center gap-2">
                                  <p className="font-medium">{emp.name}</p>
                                  {emp.is_admin && (
                                    <Badge variant="secondary" className="text-xs">Admin</Badge>
                                  )}
                                </div>
                                <div className="flex items-center gap-3 text-xs text-muted-foreground">
                                  <span className="flex items-center gap-1">
                                    <Clock className="w-3 h-3" />
                                    {emp.total_time} min
                                  </span>
                                  <span className="flex items-center gap-1">
                                    <Target className="w-3 h-3" />
                                    {emp.total_sessions} sessions
                                  </span>
                                </div>
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="flex items-center gap-1 text-amber-500">
                                <Flame className="w-4 h-4" />
                                <span className="font-bold">{emp.streak_days}</span>
                              </div>
                              <p className="text-xs text-muted-foreground">jours streak</p>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              ) : (
                /* Simple Employee List */
                <Card>
                  <CardContent className="p-0">
                    <div className="divide-y divide-border">
                      {employees.map((emp, i) => (
                        <div key={i} className="flex items-center justify-between p-4">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                              <User className="w-5 h-5 text-primary" />
                            </div>
                            <div>
                              <p className="font-medium">{emp.name}</p>
                              <p className="text-xs text-muted-foreground">
                                {emp.total_sessions} sessions • {emp.total_time} min
                              </p>
                            </div>
                          </div>
                          {emp.is_admin && <Badge variant="secondary">Admin</Badge>}
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {employees.length === 0 && (
                <Card className="py-12">
                  <div className="text-center">
                    <Users className="w-12 h-12 mx-auto mb-4 text-muted-foreground opacity-50" />
                    <p className="text-muted-foreground mb-4">Aucun collaborateur pour le moment</p>
                    <Button onClick={() => setShowInvite(true)}>
                      <UserPlus className="w-4 h-4 mr-2" />
                      Inviter des collaborateurs
                    </Button>
                  </div>
                </Card>
              )}
            </TabsContent>

            {/* Categories Tab */}
            <TabsContent value="categories" className="space-y-6">
              <div className="grid md:grid-cols-3 gap-4">
                {Object.entries(categoryLabels).map(([key, label]) => {
                  const Icon = categoryIcons[key];
                  const data = dashboard?.category_distribution?.[key] || { sessions: 0, time: 0 };
                  const color = categoryColors[key];
                  
                  return (
                    <Card key={key} className="overflow-hidden">
                      <div className="h-1" style={{ backgroundColor: color }} />
                      <CardContent className="p-6">
                        <div className="flex items-center gap-3 mb-4">
                          <div 
                            className="w-12 h-12 rounded-xl flex items-center justify-center"
                            style={{ backgroundColor: `${color}20` }}
                          >
                            <Icon className="w-6 h-6" style={{ color }} />
                          </div>
                          <h3 className="font-heading text-lg font-semibold">{label}</h3>
                        </div>
                        <div className="space-y-3">
                          <div className="flex justify-between">
                            <span className="text-sm text-muted-foreground">Sessions</span>
                            <span className="font-bold">{data.sessions}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm text-muted-foreground">Temps investi</span>
                            <span className="font-bold">{data.time} min</span>
                          </div>
                          <Progress 
                            value={Math.min(100, (data.sessions / Math.max(1, dashboard?.total_sessions || 1)) * 100)} 
                            className="h-2"
                            style={{ "--progress-color": color }}
                          />
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </main>
    </div>
  );
}
