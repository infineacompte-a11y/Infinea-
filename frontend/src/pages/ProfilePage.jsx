import React, { useState, useEffect, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Switch } from "@/components/ui/switch";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import Sidebar from "@/components/Sidebar";
import ActivityHeatmap from "@/components/ActivityHeatmap";
import {
  Activity,
  BarChart3,
  LogOut,
  Crown,
  Mail,
  ChevronRight,
  Settings,
  CreditCard,
  Users,
  AtSign,
  User,
  Flame,
  Clock,
  Eye,
  EyeOff,
  Copy,
  Check,
  Pencil,
  Loader2,
  Shield,
  Ban,
  Trash2,
  AlertTriangle,
  Camera,
} from "lucide-react";
import { toast } from "sonner";
import { API, useAuth, authFetch } from "@/App";

export default function ProfilePage() {
  const { user, setUser, logout } = useAuth();
  const navigate = useNavigate();
  const [socialStats, setSocialStats] = useState(null);
  const [privacySettings, setPrivacySettings] = useState(null);
  const [copiedUsername, setCopiedUsername] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [editForm, setEditForm] = useState({ display_name: "", username: "", bio: "" });
  const [editSaving, setEditSaving] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState("");
  const [deleting, setDeleting] = useState(false);
  const [avatarUploading, setAvatarUploading] = useState(false);
  const avatarInputRef = React.useRef(null);

  // Fetch social stats (followers/following counts)
  const fetchSocialStats = useCallback(async () => {
    if (!user?.user_id) return;
    try {
      const res = await authFetch(`${API}/users/${user.user_id}/profile`);
      if (res.ok) {
        const data = await res.json();
        setSocialStats({
          followers_count: data.followers_count || 0,
          following_count: data.following_count || 0,
        });
      }
    } catch { /* silent */ }
  }, [user?.user_id]);

  // Fetch privacy settings
  const fetchPrivacy = useCallback(async () => {
    try {
      const res = await authFetch(`${API}/profile/privacy`);
      if (res.ok) {
        const data = await res.json();
        setPrivacySettings(data);
      }
    } catch { /* silent */ }
  }, []);

  useEffect(() => {
    fetchSocialStats();
    fetchPrivacy();
  }, [fetchSocialStats, fetchPrivacy]);

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  const handlePrivacyToggle = async (field, value) => {
    const prev = { ...privacySettings };
    setPrivacySettings((s) => ({ ...s, [field]: value }));
    try {
      const res = await authFetch(`${API}/profile/privacy`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...privacySettings, [field]: value }),
      });
      if (!res.ok) {
        setPrivacySettings(prev);
        toast.error("Erreur lors de la mise à jour");
      }
    } catch {
      setPrivacySettings(prev);
      toast.error("Erreur de connexion");
    }
  };

  const copyUsername = () => {
    if (user?.username) {
      navigator.clipboard.writeText(`@${user.username}`);
      setCopiedUsername(true);
      setTimeout(() => setCopiedUsername(false), 2000);
    }
  };

  const openEditDialog = async () => {
    try {
      const res = await authFetch(`${API}/profile/me`);
      if (res.ok) {
        const data = await res.json();
        setEditForm({
          display_name: data.display_name || "",
          username: data.username || "",
          bio: data.bio || "",
        });
      }
    } catch { /* use current user fallback */ }
    setEditOpen(true);
  };

  const handleEditSave = async () => {
    setEditSaving(true);
    try {
      const res = await authFetch(`${API}/profile/me`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(editForm),
      });
      if (res.ok) {
        const data = await res.json();
        setUser((prev) => ({
          ...prev,
          display_name: data.display_name,
          username: data.username,
          bio: data.bio,
          name: data.display_name || prev.name,
        }));
        setEditOpen(false);
        toast.success("Profil mis à jour");
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || "Erreur lors de la mise à jour");
      }
    } catch {
      toast.error("Erreur de connexion");
    } finally {
      setEditSaving(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (deleteConfirm !== "SUPPRIMER") return;
    setDeleting(true);
    try {
      const res = await authFetch(`${API}/account`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ confirm: "DELETE_MY_ACCOUNT" }),
      });
      if (res.ok) {
        toast.success("Compte supprimé. Au revoir.");
        await logout();
        navigate("/");
      } else {
        const data = await res.json().catch(() => ({}));
        toast.error(data.detail || "Erreur lors de la suppression");
      }
    } catch {
      toast.error("Erreur de connexion");
    } finally {
      setDeleting(false);
    }
  };

  const handleAvatarUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Client-side validation
    const allowedTypes = ["image/jpeg", "image/png", "image/webp"];
    if (!allowedTypes.includes(file.type)) {
      toast.error("Format non supporté. Utilisez JPEG, PNG ou WebP.");
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      toast.error("L'image ne doit pas dépasser 5 Mo");
      return;
    }

    setAvatarUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await authFetch(`${API}/profile/avatar`, {
        method: "POST",
        body: formData,
      });

      if (res.ok) {
        const data = await res.json();
        setUser((prev) => ({ ...prev, picture: data.avatar_url, avatar_url: data.avatar_url }));
        toast.success("Photo de profil mise à jour");
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || "Erreur lors de l'upload");
      }
    } catch {
      toast.error("Erreur de connexion");
    } finally {
      setAvatarUploading(false);
      // Reset input so same file can be re-selected
      if (avatarInputRef.current) avatarInputRef.current.value = "";
    }
  };

  const getInitials = (name) => {
    if (!name) return "U";
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <div className="min-h-screen app-bg-mesh">
      <Sidebar />
      <main className="lg:ml-64 pt-14 lg:pt-0 pb-8">
        {/* Dark Header */}
        <div className="section-dark-header px-4 lg:px-8 pt-8 lg:pt-10 pb-8">
          <div className="max-w-3xl mx-auto">
            <div className="flex items-center gap-5">
              <div className="avatar-gradient-ring relative flex items-center justify-center opacity-0 animate-fade-in">
                <button
                  onClick={() => avatarInputRef.current?.click()}
                  className="relative group cursor-pointer"
                  disabled={avatarUploading}
                  title="Changer la photo de profil"
                >
                  <Avatar className="w-20 h-20 lg:w-24 lg:h-24 ring-offset-2 ring-offset-[#275255]">
                    <AvatarImage src={user?.avatar_url || user?.picture} alt={user?.display_name || user?.name} />
                    <AvatarFallback className="bg-white/10 text-white text-2xl">
                      {getInitials(user?.display_name || user?.name)}
                    </AvatarFallback>
                  </Avatar>
                  {/* Camera overlay */}
                  <div className="absolute inset-0 flex items-center justify-center rounded-full bg-black/0 group-hover:bg-black/40 transition-colors">
                    {avatarUploading ? (
                      <Loader2 className="w-6 h-6 text-white animate-spin" />
                    ) : (
                      <Camera className="w-5 h-5 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
                    )}
                  </div>
                </button>
                <input
                  ref={avatarInputRef}
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  onChange={handleAvatarUpload}
                  className="hidden"
                />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-3 mb-1 opacity-0 animate-fade-in" style={{ animationDelay: "50ms" }}>
                  <h1 className="text-display text-2xl lg:text-3xl font-semibold text-white truncate">
                    {user?.display_name || user?.name || "Utilisateur"}
                  </h1>
                  {user?.subscription_tier === "premium" && (
                    <Badge className="bg-gradient-to-r from-[#E48C75] to-[#459492] text-white border-0 shrink-0">
                      <Crown className="w-3 h-3 mr-1" />
                      Premium
                    </Badge>
                  )}
                </div>
                {user?.username && (
                  <button
                    onClick={copyUsername}
                    className="flex items-center gap-1.5 text-white/50 hover:text-white/80 transition-colors opacity-0 animate-fade-in"
                    style={{ animationDelay: "75ms" }}
                    title="Copier l'identifiant"
                  >
                    <AtSign className="w-3.5 h-3.5" />
                    <span className="text-sm">{user.username}</span>
                    {copiedUsername ? (
                      <Check className="w-3 h-3 text-[#5DB786]" />
                    ) : (
                      <Copy className="w-3 h-3 opacity-50" />
                    )}
                  </button>
                )}
                <div className="flex items-center gap-3 mt-1.5 opacity-0 animate-fade-in" style={{ animationDelay: "100ms" }}>
                  <p className="text-white/40 text-xs flex items-center gap-1">
                    <Mail className="w-3 h-3" />
                    {user?.email}
                  </p>
                  <button
                    onClick={openEditDialog}
                    className="flex items-center gap-1 text-white/40 hover:text-white/70 transition-colors text-xs"
                  >
                    <Pencil className="w-3 h-3" />
                    <span>Modifier</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="px-4 lg:px-8">
          <div className="max-w-3xl mx-auto">
            {/* Social stats — prominent */}
            <Card className="mb-6 opacity-0 animate-fade-in" style={{ animationDelay: "150ms", animationFillMode: "forwards" }}>
              <CardContent className="p-5">
                <div className="flex items-center justify-between">
                  <div className="flex gap-8">
                    <Link
                      to={`/users/${user?.user_id}`}
                      className="text-center hover:opacity-70 transition-opacity"
                    >
                      <p className="text-2xl font-semibold tabular-nums text-foreground">
                        {socialStats?.followers_count ?? "—"}
                      </p>
                      <p className="text-xs text-muted-foreground mt-0.5">Abonnés</p>
                    </Link>
                    <Link
                      to={`/users/${user?.user_id}`}
                      className="text-center hover:opacity-70 transition-opacity"
                    >
                      <p className="text-2xl font-semibold tabular-nums text-foreground">
                        {socialStats?.following_count ?? "—"}
                      </p>
                      <p className="text-xs text-muted-foreground mt-0.5">Abonnements</p>
                    </Link>
                  </div>
                  <Link to={`/users/${user?.user_id}`}>
                    <Button variant="outline" className="rounded-xl gap-2">
                      <Eye className="w-4 h-4" />
                      Voir mon profil public
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>

            {/* Stats Summary */}
            <Card className="mb-6 opacity-0 animate-fade-in" style={{ animationDelay: "200ms", animationFillMode: "forwards" }}>
              <CardContent className="p-5">
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 rounded-xl bg-gradient-to-br from-[#459492]/20 to-transparent border border-border/50">
                    <div className="flex items-center gap-2 mb-1">
                      <Clock className="w-4 h-4 text-[#459492]" />
                      <span className="text-xs text-muted-foreground">Temps investi</span>
                    </div>
                    <p className="text-2xl font-semibold text-primary tabular-nums">
                      {user?.total_time_invested || 0}
                      <span className="text-sm font-normal ml-1">min</span>
                    </p>
                  </div>
                  <div className="p-3 rounded-xl bg-gradient-to-br from-[#E48C75]/20 to-transparent border border-border/50">
                    <div className="flex items-center gap-2 mb-1">
                      <Flame className="w-4 h-4 text-[#E48C75]" />
                      <span className="text-xs text-muted-foreground">Streak</span>
                    </div>
                    <p className="text-2xl font-semibold text-[#E48C75] tabular-nums">
                      {user?.streak_days || 0}
                      <span className="text-sm font-normal ml-1">jours</span>
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Activity Heatmap (GitHub contributions pattern) */}
            {user?.user_id && (
              <Card className="mb-6 opacity-0 animate-fade-in" style={{ animationDelay: "240ms", animationFillMode: "forwards" }}>
                <CardHeader className="pb-2">
                  <CardTitle className="font-sans font-semibold tracking-tight text-lg flex items-center gap-2">
                    <Activity className="w-5 h-5 text-[#459492]" />
                    Mon activité
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ActivityHeatmap userId={user.user_id} />
                </CardContent>
              </Card>
            )}

            {/* Privacy settings */}
            {privacySettings && (
              <Card className="mb-6 opacity-0 animate-fade-in" style={{ animationDelay: "250ms", animationFillMode: "forwards" }}>
                <CardHeader>
                  <CardTitle className="font-sans font-semibold tracking-tight text-lg flex items-center gap-2">
                    {privacySettings.profile_visible ? (
                      <Eye className="w-5 h-5 text-[#459492]" />
                    ) : (
                      <EyeOff className="w-5 h-5 text-muted-foreground" />
                    )}
                    Visibilité du compte
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium">Compte public</p>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {privacySettings.profile_visible
                          ? "Tout le monde peut voir votre profil"
                          : "Seuls vos abonnés peuvent voir votre profil"}
                      </p>
                    </div>
                    <Switch
                      checked={privacySettings.profile_visible}
                      onCheckedChange={(v) => handlePrivacyToggle("profile_visible", v)}
                    />
                  </div>
                  <div className="h-px bg-border/50" />
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium">Afficher les statistiques</p>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        Streak et temps investi visibles sur votre profil public
                      </p>
                    </div>
                    <Switch
                      checked={privacySettings.show_stats}
                      onCheckedChange={(v) => handlePrivacyToggle("show_stats", v)}
                    />
                  </div>
                  <div className="h-px bg-border/50" />
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium">Afficher les badges</p>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        Vos badges sont visibles sur votre profil public
                      </p>
                    </div>
                    <Switch
                      checked={privacySettings.show_badges}
                      onCheckedChange={(v) => handlePrivacyToggle("show_badges", v)}
                    />
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Subscription Card */}
            <Card className="mb-6 opacity-0 animate-fade-in" style={{ animationDelay: "300ms", animationFillMode: "forwards" }}>
              <CardHeader>
                <CardTitle className="font-sans font-semibold tracking-tight text-lg flex items-center gap-2">
                  <CreditCard className="w-5 h-5" />
                  Abonnement
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between p-4 rounded-xl bg-gradient-to-br from-[#459492]/20 to-transparent border border-border/50 mb-4">
                  <div>
                    <p className="font-medium mb-1">
                      {user?.subscription_tier === "premium" ? "Plan Premium" : "Plan Gratuit"}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {user?.subscription_tier === "premium"
                        ? "Accès illimité à toutes les fonctionnalités"
                        : "Fonctionnalités de base"}
                    </p>
                  </div>
                  <Badge
                    variant={user?.subscription_tier === "premium" ? "default" : "secondary"}
                    className={user?.subscription_tier === "premium" ? "bg-[#5DB786]/40 text-[#5DB786] border-0" : ""}
                  >
                    {user?.subscription_tier === "premium" ? "Actif" : "Gratuit"}
                  </Badge>
                </div>

                {user?.subscription_tier === "premium" ? (
                  <Button
                    variant="outline"
                    className="w-full rounded-xl shadow-md"
                    onClick={async () => {
                      try {
                        const res = await authFetch(`${API}/premium/portal`, { method: "POST" });
                        if (res.ok) {
                          const data = await res.json();
                          window.open(data.url, "_blank");
                        } else {
                          toast.error("Erreur lors de l'ouverture du portail");
                        }
                      } catch {
                        toast.error("Erreur de connexion");
                      }
                    }}
                  >
                    <Settings className="w-5 h-5 mr-2" />
                    Gérer mon abonnement
                  </Button>
                ) : (
                  <Link to="/pricing">
                    <Button className="btn-premium-shimmer w-full rounded-xl shadow-md hover:shadow-lg transition-shadow" data-testid="upgrade-btn">
                      <Crown className="w-5 h-5 mr-2" />
                      Passer à Premium
                      <ChevronRight className="w-5 h-5 ml-2" />
                    </Button>
                  </Link>
                )}
              </CardContent>
            </Card>

            {/* Actions */}
            <Card className="mb-6 opacity-0 animate-fade-in" style={{ animationDelay: "350ms", animationFillMode: "forwards" }}>
              <CardContent className="p-4 space-y-1">
                <Link to="/progress">
                  <Button
                    variant="ghost"
                    className="group w-full justify-start gap-3 h-12 rounded-xl"
                  >
                    <BarChart3 className="w-5 h-5 text-muted-foreground" />
                    <span className="flex-1 text-left">Voir mes statistiques</span>
                    <ChevronRight className="w-5 h-5 text-muted-foreground group-hover:translate-x-1 transition-transform" />
                  </Button>
                </Link>
                <Button
                  variant="ghost"
                  onClick={handleLogout}
                  className="group w-full justify-start gap-3 h-12 rounded-xl text-destructive hover:bg-destructive/10"
                  data-testid="profile-logout-btn"
                >
                  <LogOut className="w-5 h-5" />
                  <span className="flex-1 text-left">Se déconnecter</span>
                  <ChevronRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </Button>
              </CardContent>
            </Card>

            {/* Security & Account */}
            <Card className="opacity-0 animate-fade-in" style={{ animationDelay: "400ms", animationFillMode: "forwards" }}>
              <CardHeader>
                <CardTitle className="font-sans font-semibold tracking-tight text-lg flex items-center gap-2">
                  <Shield className="w-5 h-5 text-muted-foreground" />
                  Sécurité du compte
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-1">
                <Link to="/blocked-users">
                  <Button
                    variant="ghost"
                    className="group w-full justify-start gap-3 h-12 rounded-xl"
                  >
                    <Ban className="w-5 h-5 text-muted-foreground" />
                    <span className="flex-1 text-left">Utilisateurs bloqués</span>
                    <ChevronRight className="w-5 h-5 text-muted-foreground group-hover:translate-x-1 transition-transform" />
                  </Button>
                </Link>
                <Button
                  variant="ghost"
                  onClick={() => setDeleteOpen(true)}
                  className="group w-full justify-start gap-3 h-12 rounded-xl text-destructive hover:bg-destructive/10"
                >
                  <Trash2 className="w-5 h-5" />
                  <span className="flex-1 text-left">Supprimer mon compte</span>
                  <ChevronRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>

      {/* Delete Account Dialog */}
      <Dialog open={deleteOpen} onOpenChange={(open) => { setDeleteOpen(open); if (!open) setDeleteConfirm(""); }}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="font-sans font-semibold tracking-tight flex items-center gap-2 text-destructive">
              <AlertTriangle className="w-5 h-5" />
              Supprimer mon compte
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 pt-2">
            <div className="p-3 rounded-xl bg-destructive/10 border border-destructive/20">
              <p className="text-sm text-destructive font-medium mb-1">
                Cette action est irréversible.
              </p>
              <p className="text-xs text-destructive/80">
                Toutes vos données seront définitivement supprimées : profil, sessions,
                objectifs, routines, badges, commentaires, groupes, et abonnements.
              </p>
            </div>
            <div className="space-y-2">
              <Label>Tapez <span className="font-mono font-bold">SUPPRIMER</span> pour confirmer</Label>
              <Input
                value={deleteConfirm}
                onChange={(e) => setDeleteConfirm(e.target.value)}
                placeholder="SUPPRIMER"
                className="font-mono"
              />
            </div>
            <div className="flex gap-3">
              <Button
                variant="outline"
                className="flex-1 rounded-xl"
                onClick={() => setDeleteOpen(false)}
              >
                Annuler
              </Button>
              <Button
                variant="destructive"
                className="flex-1 rounded-xl"
                onClick={handleDeleteAccount}
                disabled={deleting || deleteConfirm !== "SUPPRIMER"}
              >
                {deleting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                Supprimer définitivement
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Edit Profile Dialog */}
      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="font-sans font-semibold tracking-tight">
              Modifier mon profil
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 pt-2">
            <div className="space-y-2">
              <Label htmlFor="edit-display-name">Nom affiché</Label>
              <Input
                id="edit-display-name"
                value={editForm.display_name}
                onChange={(e) => setEditForm((f) => ({ ...f, display_name: e.target.value }))}
                placeholder="Votre nom public"
                maxLength={50}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-username">Identifiant</Label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground text-sm">@</span>
                <Input
                  id="edit-username"
                  value={editForm.username}
                  onChange={(e) => setEditForm((f) => ({ ...f, username: e.target.value.toLowerCase().replace(/[^a-z0-9._]/g, "") }))}
                  placeholder="identifiant"
                  maxLength={30}
                  className="pl-7"
                />
              </div>
              <p className="text-[11px] text-muted-foreground">
                Lettres minuscules, chiffres, points et underscores (3-30 car.)
              </p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-bio">Bio</Label>
              <Textarea
                id="edit-bio"
                value={editForm.bio}
                onChange={(e) => setEditForm((f) => ({ ...f, bio: e.target.value }))}
                placeholder="Décrivez-vous en quelques mots..."
                maxLength={200}
                rows={3}
                className="resize-none"
              />
              <p className="text-[11px] text-muted-foreground text-right">
                {editForm.bio.length}/200
              </p>
            </div>
            <div className="flex gap-3 pt-2">
              <Button
                variant="outline"
                className="flex-1 rounded-xl"
                onClick={() => setEditOpen(false)}
              >
                Annuler
              </Button>
              <Button
                className="flex-1 rounded-xl"
                onClick={handleEditSave}
                disabled={editSaving || !editForm.display_name.trim()}
              >
                {editSaving ? (
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                ) : null}
                Enregistrer
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
