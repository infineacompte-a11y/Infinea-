import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
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
  learning: "#3b82f6",
  productivity: "#f59e0b",
  well_being: "#10b981",
};

const categoryIcons = {
  learning: BookOpen,
  productivity: Target,
  well_being: Heart,
};

export default function B2BDashboard() {
  const { t, i18n } = useTranslation();
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
      toast.success(t("b2b.toasts.companyCreated"));
      setShowCreateCompany(false);
      fetchData();
    } catch (error) {
      toast.error(t("b2b.toasts.companyCreateError"));
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

      toast.success(t("b2b.toasts.inviteSent"));
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
        name: t(`categories.${key}`),
        value: value.sessions,
        time: value.time,
        color: categoryColors[key] || "#6366f1",
        categoryKey: key,
      }))
    : [];

  // Sort employees by total time for leaderboard
  const sortedEmployees = [...employees].sort((a, b) => b.total_time - a.total_time);

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
            <CardTitle className="font-heading text-2xl">{t("b2b.createCompany.title")}</CardTitle>
            <CardDescription>
              {t("b2b.createCompany.description")}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreateCompany} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">{t("b2b.createCompany.nameLabel")}</Label>
                <Input
                  id="name"
                  placeholder={t("b2b.createCompany.namePlaceholder")}
                  value={companyForm.name}
                  onChange={(e) => setCompanyForm({ ...companyForm, name: e.target.value })}
                  required
                  data-testid="company-name-input"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="domain">{t("b2b.createCompany.domainLabel")}</Label>
                <Input
                  id="domain"
                  placeholder={t("b2b.createCompany.domainPlaceholder")}
                  value={companyForm.domain}
                  onChange={(e) => setCompanyForm({ ...companyForm, domain: e.target.value })}
                  required
                  data-testid="company-domain-input"
                />
                <p className="text-xs text-muted-foreground">
                  {t("b2b.createCompany.domainHint", { domain: companyForm.domain || "domaine.com" })}
                </p>
              </div>
              <Button type="submit" className="w-full" data-testid="create-company-btn">
                <Building2 className="w-4 h-4 mr-2" />
                {t("b2b.createCompany.submit")}
              </Button>
              <Button
                type="button"
                variant="ghost"
                className="w-full"
                onClick={() => navigate("/dashboard")}
              >
                {t("common.cancel")}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />

      {/* Main Content */}
      <main className="lg:ml-64 pt-20 lg:pt-8 px-4 lg:px-8 pb-8">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
            <div>
              <div className="flex items-center gap-3 mb-2 flex-wrap">
                <h1 className="font-heading text-2xl sm:text-3xl font-semibold" data-testid="b2b-title">
                  {company?.name || t("b2b.header.defaultTitle")}
                </h1>
                <Badge className="bg-primary/20 text-primary border-primary/30">{t("b2b.header.managerBadge")}</Badge>
              </div>
              <p className="text-muted-foreground">
                {t("b2b.header.subtitle")}
              </p>
            </div>
            <div className="flex gap-2 sm:gap-3 shrink-0">
              <Button variant="outline" onClick={() => toast.info(t("b2b.toasts.exportSoon"))}>
                <Download className="w-4 h-4 mr-2" />
                {t("b2b.header.export")}
              </Button>
              <Dialog open={showInvite} onOpenChange={setShowInvite}>
                <DialogTrigger asChild>
                  <Button data-testid="invite-btn">
                    <UserPlus className="w-4 h-4 mr-2" />
                    {t("b2b.header.invite")}
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>{t("b2b.invite.title")}</DialogTitle>
                    <DialogDescription>
                      {t("b2b.invite.description", { domain: company?.domain })}
                    </DialogDescription>
                  </DialogHeader>
                  <form onSubmit={handleInvite} className="space-y-4 mt-4">
                    <Input
                      type="email"
                      placeholder={t("b2b.invite.placeholder", { domain: company?.domain })}
                      value={inviteEmail}
                      onChange={(e) => setInviteEmail(e.target.value)}
                      required
                      data-testid="invite-email-input"
                    />
                    <Button type="submit" className="w-full" data-testid="send-invite-btn">
                      <Send className="w-4 h-4 mr-2" />
                      {t("b2b.invite.submit")}
                    </Button>
                  </form>
                </DialogContent>
              </Dialog>
            </div>
          </div>

          {/* Overview KPIs */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
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
                    <p className="text-xs text-muted-foreground">{t("b2b.kpis.activeEmployees")}</p>
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
                    <p className="text-xs text-muted-foreground">{t("b2b.kpis.engagementRate")}</p>
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
                    <p className="text-xs text-muted-foreground">{t("b2b.kpis.totalTimeInvested")}</p>
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
                    <p className="text-xs text-muted-foreground">{t("b2b.kpis.qvtScore")}</p>
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
                  <CardTitle className="font-heading text-lg">{t("b2b.roi.title")}</CardTitle>
                  <CardDescription>{t("b2b.roi.subtitle")}</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-3 gap-6">
                <div className="text-center p-4 rounded-xl bg-white/5">
                  <Heart className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
                  <p className="text-3xl font-heading font-bold text-emerald-500">{roi.wellbeingHours}h</p>
                  <p className="text-sm text-muted-foreground">{t("b2b.roi.wellbeingThisMonth")}</p>
                </div>
                <div className="text-center p-4 rounded-xl bg-white/5">
                  <TrendingUp className="w-8 h-8 text-blue-500 mx-auto mb-2" />
                  <p className="text-3xl font-heading font-bold text-blue-500">+{roi.estimatedProductivityGain}%</p>
                  <p className="text-sm text-muted-foreground">{t("b2b.roi.estimatedProductivity")}</p>
                </div>
                <div className="text-center p-4 rounded-xl bg-white/5">
                  <Trophy className="w-8 h-8 text-amber-500 mx-auto mb-2" />
                  <p className="text-3xl font-heading font-bold text-amber-500">{dashboard?.total_sessions || 0}</p>
                  <p className="text-sm text-muted-foreground">{t("b2b.roi.completedSessions")}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Tabs */}
          <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="overview">{t("b2b.tabs.overview")}</TabsTrigger>
              <TabsTrigger value="team">{t("b2b.tabs.team")}</TabsTrigger>
              <TabsTrigger value="categories">{t("b2b.tabs.categories")}</TabsTrigger>
            </TabsList>

            {/* Overview Tab */}
            <TabsContent value="overview" className="space-y-6">
              {/* Activity Chart */}
              <Card>
                <CardHeader>
                  <CardTitle className="font-heading text-lg">{t("b2b.overview.activityTitle")}</CardTitle>
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
                      <p>{t("b2b.overview.noActivityData")}</p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Category Distribution */}
              <Card>
                <CardHeader>
                  <CardTitle className="font-heading text-lg">{t("b2b.overview.categoryDistribution")}</CardTitle>
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
                          const Icon = categoryIcons[entry.categoryKey] || Target;
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
                              <Badge variant="secondary">{t("b2b.overview.sessionsCount", { count: entry.value })}</Badge>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  ) : (
                    <div className="h-[200px] flex items-center justify-center text-muted-foreground">
                      <p>{t("b2b.overview.noData")}</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* Team Tab */}
            <TabsContent value="team" className="space-y-6">
              {/* Leaderboard Toggle */}
              <div className="flex items-center justify-between">
                <h2 className="font-heading text-lg font-semibold">{t("b2b.team.leaderboardTitle")}</h2>
                <div className="flex items-center gap-2">
                  <Label htmlFor="leaderboard-toggle" className="text-sm text-muted-foreground">
                    {t("b2b.team.gamifiedLeaderboard")}
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
                    const medals = ["\u{1F947}", "\u{1F948}", "\u{1F949}"];

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
                                    {t("b2b.team.sessionsCount", { count: emp.total_sessions })}
                                  </span>
                                </div>
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="flex items-center gap-1 text-amber-500">
                                <Flame className="w-4 h-4" />
                                <span className="font-bold">{emp.streak_days}</span>
                              </div>
                              <p className="text-xs text-muted-foreground">{t("b2b.team.streakDays")}</p>
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
                                {t("b2b.team.employeeSummary", { sessions: emp.total_sessions, time: emp.total_time })}
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
                    <p className="text-muted-foreground mb-4">{t("b2b.team.noEmployees")}</p>
                    <Button onClick={() => setShowInvite(true)}>
                      <UserPlus className="w-4 h-4 mr-2" />
                      {t("b2b.team.inviteEmployees")}
                    </Button>
                  </div>
                </Card>
              )}
            </TabsContent>

            {/* Categories Tab */}
            <TabsContent value="categories" className="space-y-6">
              <div className="grid md:grid-cols-3 gap-4">
                {Object.keys(categoryIcons).map((key) => {
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
                          <h3 className="font-heading text-lg font-semibold">{t(`categories.${key}`)}</h3>
                        </div>
                        <div className="space-y-3">
                          <div className="flex justify-between">
                            <span className="text-sm text-muted-foreground">{t("b2b.categories.sessions")}</span>
                            <span className="font-bold">{data.sessions}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm text-muted-foreground">{t("b2b.categories.timeInvested")}</span>
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
