import React, { useState, useEffect, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Trophy,
  Target,
  Clock,
  Loader2,
  Users,
  Flame,
  Zap,
  Heart,
  BookOpen,
  Sparkles,
  Plus,
  ChevronRight,
  ArrowLeft,
  Crown,
  CheckCircle2,
  Play,
  UserPlus,
  LogOut as LeaveIcon,
} from "lucide-react";
import { toast } from "sonner";
import { API, useAuth, authFetch } from "@/App";
import Sidebar from "@/components/Sidebar";
import InviteChallengeDialog from "@/components/InviteChallengeDialog";

// ── Icon mapping ──
const ICON_MAP = {
  users: Users, target: Target, flame: Flame, clock: Clock,
  zap: Zap, heart: Heart, "book-open": BookOpen, trophy: Trophy,
  sparkles: Sparkles,
};

const CATEGORY_LABELS = {
  mixed: "Mixte", learning: "Apprentissage",
  productivity: "Productivité", well_being: "Bien-être",
};

const GOAL_LABELS = {
  sessions: "sessions", time: "minutes", streak: "jours de streak",
};

const TYPE_LABELS = {
  duo: "Duo", group: "Groupe", community: "Communauté",
};

const DIFFICULTY_COLORS = {
  easy: "bg-[#5DB786]/15 text-[#5DB786]",
  medium: "bg-[#459492]/15 text-[#459492]",
  hard: "bg-[#E48C75]/15 text-[#E48C75]",
  community: "bg-purple-100 text-purple-600",
};

function getInitials(name) {
  if (!name) return "U";
  return name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2);
}

function timeLeft(endDate) {
  if (!endDate) return null;
  const diff = new Date(endDate) - Date.now();
  if (diff <= 0) return "Terminé";
  const d = Math.floor(diff / 86400000);
  if (d > 0) return `${d}j restant${d > 1 ? "s" : ""}`;
  const h = Math.floor(diff / 3600000);
  return `${h}h restante${h > 1 ? "s" : ""}`;
}

// ── Challenge Card (shared) ──
function ChallengeCard({ challenge, onClick, showParticipants = false }) {
  const Icon = ICON_MAP[challenge.icon] || Target;
  const isCompleted = challenge.status === "completed";
  const goal = challenge.goal_value || 1;
  const progress = challenge.total_progress || 0;
  const pct = Math.min(100, Math.round((progress / goal) * 100));
  const participantCount = challenge.participant_count || challenge.participants?.length || 0;
  const remaining = timeLeft(challenge.end_date);

  return (
    <Card
      className={`cursor-pointer hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 ${
        isCompleted ? "border-[#5DB786]/30 bg-[#5DB786]/3" : ""
      }`}
      onClick={onClick}
    >
      <CardContent className="p-4">
        <div className="flex items-start gap-3 mb-3">
          <div className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 ${
            isCompleted ? "bg-[#5DB786]/20" : "bg-primary/10"
          }`}>
            <Icon className={`w-5 h-5 ${isCompleted ? "text-[#5DB786]" : "text-primary"}`} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="font-semibold text-sm truncate">{challenge.title}</h3>
              {isCompleted && (
                <Badge variant="outline" className="text-[9px] bg-[#5DB786]/15 text-[#5DB786] border-[#5DB786]/20">
                  <CheckCircle2 className="w-2.5 h-2.5 mr-0.5" />
                  Réussi
                </Badge>
              )}
              {challenge.status === "pending" && (
                <Badge variant="outline" className="text-[9px]">En attente</Badge>
              )}
            </div>
            {challenge.description && (
              <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">{challenge.description}</p>
            )}
          </div>
          <ChevronRight className="w-4 h-4 text-muted-foreground shrink-0 mt-1" />
        </div>

        {/* Progress */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground tabular-nums">
              {progress}/{goal} {GOAL_LABELS[challenge.goal_type] || ""}
            </span>
            <span className="font-medium text-primary tabular-nums">{pct}%</span>
          </div>
          <Progress value={pct} className="h-2 rounded-full [&>div]:rounded-full [&>div]:transition-all" />
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between mt-3 pt-2 border-t border-border/30">
          <div className="flex items-center gap-3 text-[11px] text-muted-foreground">
            <span className="flex items-center gap-1">
              <Users className="w-3 h-3" />
              <span className="tabular-nums">{participantCount}</span>
            </span>
            <span>{TYPE_LABELS[challenge.challenge_type] || ""}</span>
            {remaining && <span>{remaining}</span>}
          </div>
          <span className="text-[10px] text-muted-foreground">
            {CATEGORY_LABELS[challenge.category] || ""}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}

// ── Challenge Detail View ──
function ChallengeDetail({ challengeId, onBack, currentUserId }) {
  const [challenge, setChallenge] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [inviteOpen, setInviteOpen] = useState(false);

  const fetchDetail = useCallback(async () => {
    try {
      const res = await authFetch(`${API}/challenges/${challengeId}`);
      if (res.ok) setChallenge(await res.json());
      else toast.error("Impossible de charger le défi");
    } catch {
      toast.error("Erreur de connexion");
    } finally {
      setLoading(false);
    }
  }, [challengeId]);

  useEffect(() => { fetchDetail(); }, [fetchDetail]);

  const handleJoin = async () => {
    setActionLoading(true);
    try {
      const res = await authFetch(`${API}/challenges/${challengeId}/join`, { method: "POST" });
      if (res.ok) {
        toast.success("Vous avez rejoint le défi !");
        fetchDetail();
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || "Impossible de rejoindre");
      }
    } catch { toast.error("Erreur"); }
    finally { setActionLoading(false); }
  };

  const handleLeave = async () => {
    setActionLoading(true);
    try {
      const res = await authFetch(`${API}/challenges/${challengeId}/leave`, { method: "POST" });
      if (res.ok) {
        toast.success("Vous avez quitté le défi");
        fetchDetail();
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || "Impossible de quitter");
      }
    } catch { toast.error("Erreur"); }
    finally { setActionLoading(false); }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="w-6 h-6 text-primary animate-spin" />
      </div>
    );
  }

  if (!challenge) return null;

  const Icon = ICON_MAP[challenge.icon] || Target;
  const isCompleted = challenge.status === "completed";
  const goal = challenge.goal_value || 1;
  const pct = challenge.progress_percent || 0;
  const leaderboard = challenge.leaderboard || [];

  return (
    <div className="space-y-4 opacity-0 animate-fade-in" style={{ animationFillMode: "forwards" }}>
      {/* Back button */}
      <button
        onClick={onBack}
        className="flex items-center gap-1.5 text-muted-foreground hover:text-foreground text-sm transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Retour
      </button>

      {/* Header card */}
      <Card>
        <CardContent className="p-5">
          <div className="flex items-start gap-4 mb-4">
            <div className={`w-14 h-14 rounded-xl flex items-center justify-center shrink-0 ${
              isCompleted ? "bg-[#5DB786]/20" : "bg-primary/10"
            }`}>
              <Icon className={`w-7 h-7 ${isCompleted ? "text-[#5DB786]" : "text-primary"}`} />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap mb-1">
                <h2 className="text-lg font-semibold">{challenge.title}</h2>
                {isCompleted && (
                  <Badge className="bg-[#5DB786]/15 text-[#5DB786] border-0 text-xs">
                    <CheckCircle2 className="w-3 h-3 mr-1" />
                    Réussi
                  </Badge>
                )}
              </div>
              {challenge.description && (
                <p className="text-sm text-muted-foreground">{challenge.description}</p>
              )}
              <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                <span>{TYPE_LABELS[challenge.challenge_type]}</span>
                <span>{CATEGORY_LABELS[challenge.category]}</span>
                <span>{challenge.duration_days}j</span>
                {timeLeft(challenge.end_date) && (
                  <span className="text-primary font-medium">{timeLeft(challenge.end_date)}</span>
                )}
              </div>
            </div>
          </div>

          {/* Global progress */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">
                Progression collective
              </span>
              <span className="font-semibold text-primary tabular-nums">{pct}%</span>
            </div>
            <Progress value={pct} className="h-3 rounded-full [&>div]:rounded-full [&>div]:transition-all" />
            <p className="text-xs text-muted-foreground tabular-nums text-right">
              {challenge.total_progress || 0} / {goal} {GOAL_LABELS[challenge.goal_type] || ""}
            </p>
          </div>

          {/* Action buttons */}
          {!challenge.is_participant && challenge.status !== "completed" && (
            <Button
              onClick={handleJoin}
              disabled={actionLoading}
              className="w-full mt-4 rounded-xl gap-2"
            >
              {actionLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <UserPlus className="w-4 h-4" />}
              Rejoindre le défi
            </Button>
          )}
          {challenge.is_participant && challenge.status !== "completed" && (
            <div className="flex gap-2 mt-4">
              <Button
                onClick={() => setInviteOpen(true)}
                className="flex-1 rounded-xl gap-2"
              >
                <UserPlus className="w-4 h-4" />
                Inviter
              </Button>
              {challenge.created_by !== currentUserId && (
                <Button
                  variant="outline"
                  onClick={handleLeave}
                  disabled={actionLoading}
                  className="rounded-xl gap-2 text-muted-foreground"
                >
                  {actionLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <LeaveIcon className="w-4 h-4" />}
                  Quitter
                </Button>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Leaderboard */}
      {leaderboard.length > 0 && (
        <Card>
          <CardContent className="p-5">
            <h3 className="font-semibold text-sm mb-3 flex items-center gap-2">
              <Crown className="w-4 h-4 text-[#E48C75]" />
              Classement
            </h3>
            <div className="space-y-2.5">
              {leaderboard.map((p) => {
                const myPct = goal > 0 ? Math.min(100, Math.round((p.progress || 0) / goal * 100)) : 0;
                const isMe = p.user_id === currentUserId;
                return (
                  <div
                    key={p.user_id}
                    className={`flex items-center gap-3 p-2.5 rounded-lg ${
                      isMe ? "bg-primary/5 ring-1 ring-primary/15" : ""
                    }`}
                  >
                    <span className={`w-6 text-center font-bold text-sm tabular-nums ${
                      p.rank === 1 ? "text-[#E48C75]" : p.rank === 2 ? "text-[#459492]" : "text-muted-foreground"
                    }`}>
                      {p.rank}
                    </span>
                    <Link to={`/users/${p.user_id}`}>
                      <Avatar className="w-8 h-8">
                        <AvatarImage src={p.avatar_url} />
                        <AvatarFallback className="text-[10px] bg-primary/10">
                          {getInitials(p.display_name)}
                        </AvatarFallback>
                      </Avatar>
                    </Link>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5">
                        <Link
                          to={`/users/${p.user_id}`}
                          className="text-xs font-medium truncate hover:underline"
                        >
                          {p.display_name}
                        </Link>
                        {isMe && (
                          <span className="text-[9px] text-primary font-medium">(vous)</span>
                        )}
                      </div>
                      <Progress value={myPct} className="h-1.5 mt-1 rounded-full [&>div]:rounded-full" />
                    </div>
                    <span className="text-xs text-muted-foreground tabular-nums shrink-0">
                      {p.progress || 0}
                    </span>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Invite dialog */}
      {challenge && (
        <InviteChallengeDialog
          open={inviteOpen}
          onOpenChange={setInviteOpen}
          challengeId={challengeId}
          challengeTitle={challenge.title}
          existingParticipantIds={(challenge.participants || []).map((p) => p.user_id)}
          onInvited={fetchDetail}
        />
      )}
    </div>
  );
}

// ── Template picker dialog ──
function TemplateDialog({ open, onOpenChange, onLaunch }) {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [launching, setLaunching] = useState(null);

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    authFetch(`${API}/challenges/templates`)
      .then(async (res) => {
        if (res.ok) {
          const data = await res.json();
          setTemplates(data.templates || []);
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [open]);

  const handleLaunch = async (templateId) => {
    setLaunching(templateId);
    try {
      const res = await authFetch(`${API}/challenges/from-template`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ template_id: templateId }),
      });
      if (res.ok) {
        const challenge = await res.json();
        toast.success(`Défi "${challenge.title}" créé !`);
        onOpenChange(false);
        onLaunch(challenge);
      } else {
        toast.error("Erreur de création");
      }
    } catch {
      toast.error("Erreur de connexion");
    } finally {
      setLaunching(null);
    }
  };

  const grouped = {
    duo: templates.filter((t) => t.challenge_type === "duo"),
    group: templates.filter((t) => t.challenge_type === "group"),
    community: templates.filter((t) => t.challenge_type === "community"),
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="font-sans font-semibold tracking-tight">
            Lancer un défi
          </DialogTitle>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-5 h-5 animate-spin text-primary" />
          </div>
        ) : (
          <div className="space-y-5 pt-2">
            {[
              { key: "duo", label: "Duo", desc: "À deux, haute responsabilité" },
              { key: "group", label: "Groupe", desc: "3-10 personnes, dynamique d'équipe" },
              { key: "community", label: "Communauté", desc: "Ouvert à tous, objectif collectif" },
            ].map((section) => (
              <div key={section.key}>
                <div className="mb-2">
                  <h4 className="text-sm font-semibold">{section.label}</h4>
                  <p className="text-[11px] text-muted-foreground">{section.desc}</p>
                </div>
                <div className="space-y-2">
                  {(grouped[section.key] || []).map((t) => {
                    const Icon = ICON_MAP[t.icon] || Target;
                    return (
                      <div
                        key={t.template_id}
                        className="flex items-center gap-3 p-3 rounded-xl border border-border/50 hover:border-primary/20 hover:bg-primary/[0.02] transition-all"
                      >
                        <div className="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                          <Icon className="w-4 h-4 text-primary" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium">{t.title}</p>
                          <p className="text-[11px] text-muted-foreground mt-0.5">
                            {t.goal_value} {GOAL_LABELS[t.goal_type]} · {t.duration_days}j
                          </p>
                        </div>
                        {t.difficulty && (
                          <Badge variant="outline" className={`text-[9px] shrink-0 ${DIFFICULTY_COLORS[t.difficulty] || ""}`}>
                            {t.difficulty === "easy" ? "Facile" : t.difficulty === "medium" ? "Moyen" : t.difficulty === "hard" ? "Difficile" : "Collectif"}
                          </Badge>
                        )}
                        <Button
                          size="sm"
                          variant="outline"
                          className="shrink-0 rounded-lg h-8 text-xs gap-1"
                          disabled={launching === t.template_id}
                          onClick={() => handleLaunch(t.template_id)}
                        >
                          {launching === t.template_id ? (
                            <Loader2 className="w-3 h-3 animate-spin" />
                          ) : (
                            <Play className="w-3 h-3" />
                          )}
                          Lancer
                        </Button>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

// ── Main Page ──
export default function ChallengesPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState("mine");
  const [myChallenges, setMyChallenges] = useState([]);
  const [discoverChallenges, setDiscoverChallenges] = useState([]);
  const [invites, setInvites] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedChallenge, setSelectedChallenge] = useState(null);
  const [templateOpen, setTemplateOpen] = useState(false);
  const [categoryFilter, setCategoryFilter] = useState("all");

  const fetchMine = useCallback(async () => {
    try {
      const res = await authFetch(`${API}/challenges`);
      if (res.ok) {
        const data = await res.json();
        setMyChallenges(data.challenges || []);
      }
    } catch { /* silent */ }
  }, []);

  const fetchDiscover = useCallback(async () => {
    try {
      const params = new URLSearchParams({ limit: "20" });
      if (categoryFilter && categoryFilter !== "all") params.set("category", categoryFilter);
      const res = await authFetch(`${API}/challenges/discover?${params}`);
      if (res.ok) {
        const data = await res.json();
        setDiscoverChallenges(data.challenges || []);
      }
    } catch { /* silent */ }
  }, [categoryFilter]);

  const fetchInvites = useCallback(async () => {
    try {
      const res = await authFetch(`${API}/challenges/invites`);
      if (res.ok) {
        const data = await res.json();
        setInvites(data.invites || []);
      }
    } catch { /* silent */ }
  }, []);

  useEffect(() => {
    Promise.all([fetchMine(), fetchDiscover(), fetchInvites()]).finally(() =>
      setIsLoading(false)
    );
  }, [fetchMine, fetchDiscover, fetchInvites]);

  const handleAcceptInvite = async (inviteId) => {
    try {
      const res = await authFetch(`${API}/challenges/invites/${inviteId}/accept`, { method: "POST" });
      if (res.ok) {
        toast.success("Invitation acceptée !");
        fetchInvites();
        fetchMine();
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || "Erreur");
      }
    } catch { toast.error("Erreur"); }
  };

  const handleDeclineInvite = async (inviteId) => {
    try {
      await authFetch(`${API}/challenges/invites/${inviteId}/decline`, { method: "POST" });
      fetchInvites();
    } catch { /* silent */ }
  };

  const handleTemplateLaunch = (challenge) => {
    fetchMine();
    // Open detail view immediately so user can invite friends
    if (challenge?.challenge_id) {
      setSelectedChallenge(challenge.challenge_id);
    } else {
      setActiveTab("mine");
    }
  };

  // Detail view
  if (selectedChallenge) {
    return (
      <div className="min-h-screen app-bg-mesh">
        <Sidebar />
        <main className="lg:ml-64 pt-14 lg:pt-0 pb-8">
          <div className="section-dark-header px-4 lg:px-8 pt-8 lg:pt-10 pb-8">
            <div className="max-w-3xl mx-auto">
              <h1 className="text-display text-3xl font-semibold text-white opacity-0 animate-fade-in">
                Détail du défi
              </h1>
            </div>
          </div>
          <div className="px-4 lg:px-8">
            <div className="max-w-3xl mx-auto">
              <ChallengeDetail
                challengeId={selectedChallenge}
                onBack={() => { setSelectedChallenge(null); fetchMine(); fetchDiscover(); }}
                currentUserId={user?.user_id}
              />
            </div>
          </div>
        </main>
      </div>
    );
  }

  const tabs = [
    { key: "mine", label: "Mes défis", count: myChallenges.length },
    { key: "discover", label: "Découvrir", count: discoverChallenges.length },
  ];

  const activeMine = myChallenges.filter((c) => c.status === "active" || c.status === "pending");
  const completedMine = myChallenges.filter((c) => c.status === "completed");

  return (
    <div className="min-h-screen app-bg-mesh">
      <Sidebar />
      <main className="lg:ml-64 pt-14 lg:pt-0 pb-8">
        {/* Dark Header */}
        <div className="section-dark-header px-4 lg:px-8 pt-8 lg:pt-10 pb-8">
          <div className="max-w-3xl mx-auto">
            <div className="flex items-center justify-between opacity-0 animate-fade-in" style={{ animationFillMode: "forwards" }}>
              <div>
                <h1 className="text-display text-3xl lg:text-4xl font-semibold text-white">
                  Défis
                </h1>
                <p className="text-white/60 text-sm mt-1">
                  Relevez des défis et progressez ensemble
                </p>
              </div>
              <Button
                onClick={() => setTemplateOpen(true)}
                className="rounded-xl gap-2 bg-white/10 hover:bg-white/20 text-white border-0"
              >
                <Plus className="w-4 h-4" />
                <span className="hidden sm:inline">Nouveau défi</span>
              </Button>
            </div>
          </div>
        </div>

        <div className="px-4 lg:px-8">
          <div className="max-w-3xl mx-auto">
            {/* Invites banner */}
            {invites.length > 0 && (
              <Card className="mb-4 border-[#E48C75]/20 bg-[#E48C75]/5 opacity-0 animate-fade-in" style={{ animationFillMode: "forwards" }}>
                <CardContent className="p-4">
                  <h4 className="text-sm font-semibold mb-2 flex items-center gap-2">
                    <UserPlus className="w-4 h-4 text-[#E48C75]" />
                    Invitations ({invites.length})
                  </h4>
                  <div className="space-y-2">
                    {invites.map((inv) => (
                      <div key={inv.invite_id} className="flex items-center gap-3 p-2 rounded-lg bg-background/60">
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">
                            {inv.challenge?.title || "Défi"}
                          </p>
                          <p className="text-[11px] text-muted-foreground">
                            {inv.challenge?.challenge_type && TYPE_LABELS[inv.challenge.challenge_type]} · {inv.challenge?.duration_days}j
                          </p>
                        </div>
                        <Button
                          size="sm"
                          className="h-7 text-xs rounded-lg"
                          onClick={() => handleAcceptInvite(inv.invite_id)}
                        >
                          Accepter
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-7 text-xs rounded-lg text-muted-foreground"
                          onClick={() => handleDeclineInvite(inv.invite_id)}
                        >
                          Décliner
                        </Button>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Tab switcher */}
            <div className="flex gap-1 p-1 mb-5 bg-muted/30 rounded-xl opacity-0 animate-fade-in" style={{ animationDelay: "100ms", animationFillMode: "forwards" }}>
              {tabs.map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 px-3 rounded-lg text-sm font-medium transition-all duration-200 ${
                    activeTab === tab.key
                      ? "bg-background shadow-sm text-foreground"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {tab.label}
                  {tab.count > 0 && (
                    <span className="text-[10px] tabular-nums bg-primary/10 text-primary px-1.5 py-0.5 rounded-md">
                      {tab.count}
                    </span>
                  )}
                </button>
              ))}
            </div>

            {isLoading && (
              <div className="flex items-center justify-center py-16">
                <Loader2 className="w-6 h-6 text-primary animate-spin" />
              </div>
            )}

            {/* ── My Challenges Tab ── */}
            {!isLoading && activeTab === "mine" && (
              <div className="opacity-0 animate-fade-in" style={{ animationDelay: "200ms", animationFillMode: "forwards" }}>
                {myChallenges.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-12 text-center">
                    <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center mb-4 ring-1 ring-primary/10">
                      <Trophy className="w-7 h-7 text-primary" />
                    </div>
                    <h2 className="text-base font-semibold mb-1">Aucun défi en cours</h2>
                    <p className="text-sm text-muted-foreground max-w-xs mb-4">
                      Lancez un défi depuis un template ou rejoignez un défi communautaire.
                    </p>
                    <Button onClick={() => setTemplateOpen(true)} className="rounded-xl gap-2">
                      <Plus className="w-4 h-4" />
                      Lancer un défi
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-6">
                    {activeMine.length > 0 && (
                      <div>
                        <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                          En cours ({activeMine.length})
                        </h3>
                        <div className="space-y-2.5">
                          {activeMine.map((ch, i) => (
                            <div key={ch.challenge_id} className="opacity-0 animate-fade-in" style={{ animationDelay: `${i * 50}ms`, animationFillMode: "forwards" }}>
                              <ChallengeCard
                                challenge={ch}
                                onClick={() => setSelectedChallenge(ch.challenge_id)}
                              />
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    {completedMine.length > 0 && (
                      <div>
                        <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                          Terminés ({completedMine.length})
                        </h3>
                        <div className="space-y-2.5">
                          {completedMine.map((ch, i) => (
                            <div key={ch.challenge_id} className="opacity-0 animate-fade-in" style={{ animationDelay: `${i * 50}ms`, animationFillMode: "forwards" }}>
                              <ChallengeCard
                                challenge={ch}
                                onClick={() => setSelectedChallenge(ch.challenge_id)}
                              />
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* ── Discover Tab ── */}
            {!isLoading && activeTab === "discover" && (
              <div className="opacity-0 animate-fade-in" style={{ animationDelay: "200ms", animationFillMode: "forwards" }}>
                {/* Category filter pills */}
                <div className="flex gap-1.5 mb-4 overflow-x-auto pb-1 scrollbar-hide">
                  {[{ key: "all", label: "Tous" }, ...Object.entries(CATEGORY_LABELS).map(([k, v]) => ({ key: k, label: v }))].map((cat) => (
                    <button
                      key={cat.key}
                      onClick={() => setCategoryFilter(cat.key)}
                      className={`shrink-0 px-3.5 py-1.5 rounded-full text-xs font-medium transition-all duration-200 ${
                        categoryFilter === cat.key
                          ? "bg-primary text-white shadow-sm"
                          : "bg-muted/40 text-muted-foreground hover:bg-muted/70 hover:text-foreground"
                      }`}
                    >
                      {cat.label}
                    </button>
                  ))}
                </div>

                {discoverChallenges.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-12 text-center">
                    <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center mb-4 ring-1 ring-primary/10">
                      <Sparkles className="w-7 h-7 text-primary" />
                    </div>
                    <h2 className="text-base font-semibold mb-1">Aucun défi à découvrir</h2>
                    <p className="text-sm text-muted-foreground max-w-xs mb-4">
                      Soyez le premier à lancer un défi communautaire !
                    </p>
                    <Button onClick={() => setTemplateOpen(true)} className="rounded-xl gap-2">
                      <Plus className="w-4 h-4" />
                      Créer un défi
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-2.5">
                    {discoverChallenges.map((ch, i) => (
                      <div key={ch.challenge_id} className="opacity-0 animate-fade-in" style={{ animationDelay: `${i * 50}ms`, animationFillMode: "forwards" }}>
                        <ChallengeCard
                          challenge={ch}
                          onClick={() => setSelectedChallenge(ch.challenge_id)}
                        />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Template picker dialog */}
      <TemplateDialog
        open={templateOpen}
        onOpenChange={setTemplateOpen}
        onLaunch={handleTemplateLaunch}
      />
    </div>
  );
}
