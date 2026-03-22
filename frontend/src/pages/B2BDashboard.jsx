import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Building2,
  Users,
  User,
  TrendingUp,
  Clock,
  Activity,
  Send,
  Heart,
  BookOpen,
  Target,
  Loader2,
  Trophy,
  Download,
  UserPlus,
  Flame,
  Zap,
} from "lucide-react";
import { toast } from "sonner";
import { API, useAuth, authFetch } from "@/App";
import Sidebar from "@/components/Sidebar";
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
  learning: "#459492",
  productivity: "#E48C75",
  well_being: "#5DB786",
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
  const { user } = useAuth();
  const navigate = useNavigate();
  const [company, setCompany] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [employees, setEmployees] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
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
      // Check if user has a company
      const companyRes = await authFetch(`${API}/b2b/company`);

      if (companyRes.ok) {
        const companyData = await companyRes.json();
        setCompany(companyData);

        // Fetch dashboard and employees
        const [dashRes, empRes] = await Promise.all([
          authFetch(`${API}/b2b/dashboard`),
          authFetch(`${API}/b2b/employees`),
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
      const res = await authFetch(`${API}/b2b/company`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
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
      const res = await authFetch(`${API}/b2b/invite`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
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
        color: categoryColors[key] || "#459492",
      }))
    : [];

  // Sort employees by total time for leaderboard
  const sortedEmployees = [...employees].sort((a, b) => b.total_time - a.total_time);

  if (isLoading) {
    return (
      <div className="min-h-screen app-bg-mesh">
        <Sidebar />
        <main className="lg:ml-64 pt-14 lg:pt-0 pb-8">
          <div className="section-dark-header px-4 lg:px-8 pt-8 lg:pt-10 pb-8">
            <div className="max-w-6xl mx-auto">
              <h1 className="text-display text-3xl lg:text-4xl font-semibold text-white opacity-0 animate-fade-in">
                {company?.name || "Dashboard Entreprise"}
              </h1>
              <p className="text-white/60 text-sm mt-1 opacity-0 animate-fade-in" style={{ animationDelay: "50ms" }}>
                Tableau de bord entreprise
              </p>
            </div>
          </div>
          <div className="px-4 lg:px-8">
            <div className="max-w-6xl mx-auto space-y-8">
              {/* KPI skeletons */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {[...Array(4)].map((_, i) => (
                  <div key={i} className="rounded-xl border border-border bg-card p-4 animate-pulse">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 rounded-xl bg-muted" />
                      <div className="space-y-2">
                        <div className="h-6 w-12 rounded bg-muted" />
                        <div className="h-3 w-24 rounded bg-muted" />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              {/* Chart skeleton */}
              <div className="rounded-xl border border-border bg-card p-6 animate-pulse">
                <div className="h-5 w-48 rounded bg-muted mb-4" />
                <div className="h-[200px] rounded bg-muted" />
              </div>
            </div>
          </div>
        </main>
      </div>
    );
  }

  if (showCreateCompany && !company) {
    return (
      <div className="min-h-screen app-bg-mesh flex items-center justify-center p-4">
        <Card className="max-w-md w-full rounded-xl opacity-0 animate-fade-in" style={{ animationDelay: "100ms", animationFillMode: "forwards" }}>
          <CardHeader className="text-center">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center mx-auto mb-4">
              <Building2 className="w-8 h-8 text-primary" />
            </div>
            <CardTitle className="font-sans font-semibold tracking-tight text-2xl">Créer votre espace entreprise</CardTitle>
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
              <Button type="submit" className="w-full rounded-xl shadow-md hover:shadow-lg transition-all duration-200 btn-press" data-testid="create-company-btn">
                <Building2 className="w-4 h-4 mr-2" />
                Créer l'espace entreprise
              </Button>
              <Button
                type="button"
                variant="ghost"
                className="w-full rounded-xl transition-all duration-200"
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
    <div className="min-h-screen app-bg-mesh">
      <Sidebar />
      <main className="lg:ml-64 pt-14 lg:pt-0 pb-8">
        {/* Dark teal header */}
        <div className="section-dark-header px-4 lg:px-8 pt-8 lg:pt-10 pb-8">
          <div className="max-w-6xl mx-auto flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-display text-3xl lg:text-4xl font-semibold text-white opacity-0 animate-fade-in" data-testid="b2b-title">
                {company?.name || "Dashboard Entreprise"}
              </h1>
              <Badge className="bg-white/10 text-white border-white/20 opacity-0 animate-fade-in" style={{ animationDelay: "50ms" }}>Manager</Badge>
            </div>
            <p className="text-white/60 text-sm mt-1 opacity-0 animate-fade-in" style={{ animationDelay: "50ms" }}>
              Tableau de bord entreprise
            </p>
          </div>
          <div className="flex gap-2 sm:gap-3 shrink-0 opacity-0 animate-fade-in" style={{ animationDelay: "100ms" }}>
            <Button variant="outline" onClick={() => toast.info("Export PDF bientôt disponible")} className="rounded-xl transition-all duration-200 btn-press bg-white/10 hover:bg-white/20 text-white border-white/20">
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
            <Dialog open={showInvite} onOpenChange={setShowInvite}>
              <DialogTrigger asChild>
                <Button data-testid="invite-btn" className="rounded-xl shadow-md hover:shadow-lg transition-all duration-200 btn-press bg-white/10 hover:bg-white/20 text-white border-white/20">
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
                  <Button type="submit" className="w-full rounded-xl shadow-md hover:shadow-lg transition-all duration-200 btn-press" data-testid="send-invite-btn">
                    <Send className="w-4 h-4 mr-2" />
                    Envoyer l'invitation
                  </Button>
                </form>
              </DialogContent>
            </Dialog>
          </div>
        </div>
      </div>

        <div className="px-4 lg:px-8">
          <div className="max-w-6xl mx-auto">

          {/* Overview KPIs */}
          <div className="opacity-0 animate-fade-in grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8" style={{ animationDelay: "200ms", animationFillMode: "forwards" }}>
            <Card className="group bg-gradient-to-br from-primary/10 to-transparent border-border hover:shadow-md hover:border-primary/30 transition-all duration-300 rounded-xl">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-xl bg-primary/15 flex items-center justify-center">
                    <Users className="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <p className="text-2xl font-sans font-semibold tracking-tight font-bold tabular-nums">
                      {dashboard?.employee_count || 0}
                    </p>
                    <p className="text-xs text-muted-foreground">collaborateurs actifs</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="group bg-gradient-to-br from-[#5DB786]/10 to-transparent border-border hover:shadow-md hover:border-[#5DB786]/30 transition-all duration-300 rounded-xl">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-xl bg-[#5DB786]/15 flex items-center justify-center">
                    <Activity className="w-6 h-6 text-[#5DB786]" />
                  </div>
                  <div>
                    <p className="text-2xl font-sans font-semibold tracking-tight font-bold tabular-nums">
                      {dashboard?.engagement_rate || 0}%
                    </p>
                    <p className="text-xs text-muted-foreground">taux d'engagement</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="group bg-gradient-to-br from-[#E48C75]/10 to-transparent border-border hover:shadow-md hover:border-[#E48C75]/30 transition-all duration-300 rounded-xl">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-xl bg-[#E48C75]/15 flex items-center justify-center">
                    <Clock className="w-6 h-6 text-[#E48C75]" />
                  </div>
                  <div>
                    <p className="text-2xl font-sans font-semibold tracking-tight font-bold tabular-nums">
                      {Math.round((dashboard?.total_time_minutes || 0) / 60)}h
                    </p>
                    <p className="text-xs text-muted-foreground">temps total investi</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="group bg-gradient-to-br from-[#459492]/10 to-transparent border-[#459492]/30 hover:shadow-md hover:border-[#459492]/40 transition-all duration-300 rounded-xl">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-xl bg-[#459492]/15 flex items-center justify-center">
                    <TrendingUp className="w-6 h-6 text-[#459492]" />
                  </div>
                  <div>
                    <p className="text-2xl font-sans font-semibold tracking-tight font-bold tabular-nums">
                      {dashboard?.qvt_score || 0}
                    </p>
                    <p className="text-xs text-muted-foreground">score QVT</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* ROI Card */}
          <div className="opacity-0 animate-fade-in mb-8" style={{ animationDelay: "300ms", animationFillMode: "forwards" }}>
            <Card className="bg-gradient-to-br from-[#5DB786]/5 to-[#459492]/5 border-[#5DB786]/20 rounded-xl hover:shadow-md transition-all duration-300">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-[#5DB786]/15 flex items-center justify-center">
                    <Zap className="w-5 h-5 text-[#5DB786]" />
                  </div>
                  <div>
                    <CardTitle className="font-sans font-semibold tracking-tight text-lg">ROI Bien-être</CardTitle>
                    <CardDescription>Impact mesurable sur la productivité</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-3 gap-6">
                  <div className="text-center p-4 rounded-xl bg-[#F8FAFB] border border-[#E2E6EA] hover:shadow-sm transition-all duration-200">
                    <Heart className="w-8 h-8 text-[#5DB786] mx-auto mb-2" />
                    <p className="text-3xl font-sans font-semibold tracking-tight font-bold text-[#5DB786] tabular-nums">{roi.wellbeingHours}h</p>
                    <p className="text-sm text-muted-foreground">en bien-être ce mois</p>
                  </div>
                  <div className="text-center p-4 rounded-xl bg-[#F8FAFB] border border-[#E2E6EA] hover:shadow-sm transition-all duration-200">
                    <TrendingUp className="w-8 h-8 text-[#459492] mx-auto mb-2" />
                    <p className="text-3xl font-sans font-semibold tracking-tight font-bold text-[#459492] tabular-nums">+{roi.estimatedProductivityGain}%</p>
                    <p className="text-sm text-muted-foreground">productivité estimée</p>
                  </div>
                  <div className="text-center p-4 rounded-xl bg-[#F8FAFB] border border-[#E2E6EA] hover:shadow-sm transition-all duration-200">
                    <Trophy className="w-8 h-8 text-[#E48C75] mx-auto mb-2" />
                    <p className="text-3xl font-sans font-semibold tracking-tight font-bold text-[#E48C75] tabular-nums">{dashboard?.total_sessions || 0}</p>
                    <p className="text-sm text-muted-foreground">sessions complétées</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Tabs */}
          <div className="opacity-0 animate-fade-in" style={{ animationDelay: "400ms", animationFillMode: "forwards" }}>
            <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="overview">Vue d'ensemble</TabsTrigger>
                <TabsTrigger value="team">Équipe</TabsTrigger>
                <TabsTrigger value="categories">Catégories</TabsTrigger>
              </TabsList>

              {/* Overview Tab */}
              <TabsContent value="overview" className="space-y-6">
                {/* Activity Chart */}
                <Card className="rounded-xl hover:shadow-md transition-all duration-300">
                  <CardHeader>
                    <CardTitle className="font-sans font-semibold tracking-tight text-lg">Activité (28 derniers jours)</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {dashboard?.daily_activity?.length > 0 ? (
                      <ResponsiveContainer width="100%" height={250}>
                        <AreaChart data={dashboard.daily_activity}>
                          <defs>
                            <linearGradient id="colorSessions" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#459492" stopOpacity={0.3}/>
                              <stop offset="95%" stopColor="#459492" stopOpacity={0}/>
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" stroke="#E2E6EA" />
                          <XAxis
                            dataKey="_id"
                            tick={{ fill: "#9A9A9A", fontSize: 10 }}
                            tickFormatter={(v) => v.slice(5)}
                          />
                          <YAxis tick={{ fill: "#9A9A9A", fontSize: 12 }} />
                          <Tooltip
                            contentStyle={{
                              backgroundColor: "#FFFFFF",
                              border: "1px solid #E2E6EA",
                              borderRadius: "12px",
                              boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
                            }}
                          />
                          <Area
                            type="monotone"
                            dataKey="sessions"
                            stroke="#459492"
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
                <Card className="rounded-xl hover:shadow-md transition-all duration-300">
                  <CardHeader>
                    <CardTitle className="font-sans font-semibold tracking-tight text-lg">Répartition par catégorie</CardTitle>
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
                                backgroundColor: "#FFFFFF",
                                border: "1px solid #E2E6EA",
                                borderRadius: "12px",
                                boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
                              }}
                            />
                          </PieChart>
                        </ResponsiveContainer>
                        <div className="space-y-4">
                          {pieData.map((entry, i) => {
                            const Icon = categoryIcons[Object.keys(categoryLabels).find(k => categoryLabels[k] === entry.name)] || Target;
                            return (
                              <div key={i} className="flex items-center justify-between p-3 rounded-xl bg-[#F8FAFB] border border-[#E2E6EA]/50 hover:bg-muted/30 transition-all duration-200">
                                <div className="flex items-center gap-3">
                                  <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${entry.color}20` }}>
                                    <Icon className="w-5 h-5" style={{ color: entry.color }} />
                                  </div>
                                  <div>
                                    <p className="font-medium">{entry.name}</p>
                                    <p className="text-xs text-muted-foreground tabular-nums">{entry.time} min</p>
                                  </div>
                                </div>
                                <Badge variant="secondary" className="tabular-nums">{entry.value} sessions</Badge>
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
                  <h2 className="font-sans font-semibold tracking-tight text-lg font-semibold text-foreground">Classement de l'équipe</h2>
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
                          className={`opacity-0 animate-fade-in group hover:shadow-lg hover:-translate-y-0.5 active:translate-y-px transition-all duration-200 rounded-xl ${isTop3 ? "border-[#E48C75]/30 bg-[#E48C75]/5" : "hover:border-[#459492]/30"}`}
                          style={{ animationDelay: `${i * 30}ms`, animationFillMode: "forwards" }}
                          data-testid={`employee-card-${i}`}
                        >
                          <CardContent className="p-4">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-4">
                                <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                                  isTop3
                                    ? "bg-[#E48C75]/40 text-2xl"
                                    : "bg-primary/10"
                                }`}>
                                  {isTop3 ? medals[i] : <span className="font-medium text-muted-foreground tabular-nums">#{i + 1}</span>}
                                </div>
                                <div>
                                  <div className="flex items-center gap-2">
                                    <p className="font-medium">{emp.name}</p>
                                    {emp.is_admin && (
                                      <Badge variant="secondary" className="text-xs">Admin</Badge>
                                    )}
                                  </div>
                                  <div className="flex items-center gap-3 text-xs text-muted-foreground">
                                    <span className="flex items-center gap-1 tabular-nums">
                                      <Clock className="w-3 h-3" />
                                      {emp.total_time} min
                                    </span>
                                    <span className="flex items-center gap-1 tabular-nums">
                                      <Target className="w-3 h-3" />
                                      {emp.total_sessions} sessions
                                    </span>
                                  </div>
                                </div>
                              </div>
                              <div className="text-right">
                                <div className="flex items-center gap-1 text-[#E48C75]">
                                  <Flame className="w-4 h-4" />
                                  <span className="font-bold tabular-nums">{emp.streak_days}</span>
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
                  <Card className="rounded-xl">
                    <CardContent className="p-0">
                      <div className="divide-y divide-border">
                        {employees.map((emp, i) => (
                          <div key={i} className="flex items-center justify-between p-4 hover:bg-muted/30 transition-all duration-200">
                            <div className="flex items-center gap-3">
                              <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                                <User className="w-5 h-5 text-primary" />
                              </div>
                              <div>
                                <p className="font-medium">{emp.name}</p>
                                <p className="text-xs text-muted-foreground tabular-nums">
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
                  <Card className="py-12 rounded-xl">
                    <div className="text-center">
                      <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-muted/40 to-transparent flex items-center justify-center mx-auto mb-4">
                        <Users className="w-8 h-8 text-muted-foreground/50" />
                      </div>
                      <p className="text-muted-foreground mb-4">Aucun collaborateur pour le moment</p>
                      <Button onClick={() => setShowInvite(true)} className="rounded-xl shadow-md hover:shadow-lg transition-all duration-200 btn-press">
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
                  {Object.entries(categoryLabels).map(([key, label], idx) => {
                    const Icon = categoryIcons[key];
                    const data = dashboard?.category_distribution?.[key] || { sessions: 0, time: 0 };
                    const color = categoryColors[key];

                    return (
                      <Card
                        key={key}
                        className="opacity-0 animate-fade-in overflow-hidden group hover:shadow-lg hover:-translate-y-0.5 transition-all duration-200 rounded-xl"
                        style={{ animationDelay: `${idx * 100}ms`, animationFillMode: "forwards" }}
                      >
                        <div className="h-1" style={{ backgroundColor: color }} />
                        <CardContent className="p-6">
                          <div className="flex items-center gap-3 mb-4">
                            <div
                              className="w-12 h-12 rounded-xl flex items-center justify-center"
                              style={{ backgroundColor: `${color}20` }}
                            >
                              <Icon className="w-6 h-6" style={{ color }} />
                            </div>
                            <h3 className="font-sans font-semibold tracking-tight text-lg font-semibold">{label}</h3>
                          </div>
                          <div className="space-y-3">
                            <div className="flex justify-between">
                              <span className="text-sm text-muted-foreground">Sessions</span>
                              <span className="font-bold tabular-nums">{data.sessions}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-sm text-muted-foreground">Temps investi</span>
                              <span className="font-bold tabular-nums">{data.time} min</span>
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
          </div>
        </div>
      </main>
    </div>
  );
}
