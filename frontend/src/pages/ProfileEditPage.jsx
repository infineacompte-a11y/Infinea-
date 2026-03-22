import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  User,
  Shield,
  Save,
  Loader2,
  ArrowLeft,
  Eye,
  BarChart3,
  Award,
  BookOpen,
  Users,
} from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api";
import { useAuth } from "@/App";
import AppLayout from "@/components/AppLayout";

function getInitials(name) {
  if (!name) return "U";
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

export default function ProfileEditPage() {
  const { user, setUser } = useAuth();
  const navigate = useNavigate();

  // Profile fields
  const [displayName, setDisplayName] = useState("");
  const [bio, setBio] = useState("");
  const [avatarUrl, setAvatarUrl] = useState("");
  const [profileLoading, setProfileLoading] = useState(false);

  // Privacy settings
  const [privacy, setPrivacy] = useState({
    profile_visible: true,
    show_stats: true,
    show_badges: true,
    show_reflections: false,
    activity_default_visibility: "followers",
  });
  const [privacyLoading, setPrivacyLoading] = useState(false);

  const [initialLoading, setInitialLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [profile, privacyData] = await Promise.all([
        api.getMyProfile(),
        api.getPrivacy(),
      ]);
      setDisplayName(profile.display_name || profile.name || "");
      setBio(profile.bio || "");
      setAvatarUrl(profile.avatar_url || profile.picture || "");
      setPrivacy(privacyData);
    } catch (err) {
      toast.error("Impossible de charger le profil");
    } finally {
      setInitialLoading(false);
    }
  };

  const handleSaveProfile = async () => {
    setProfileLoading(true);
    try {
      const update = {};
      if (displayName.trim()) update.display_name = displayName.trim();
      if (bio !== undefined) update.bio = bio.trim();
      if (avatarUrl.trim()) update.avatar_url = avatarUrl.trim();

      await api.updateProfile(update);
      // Update local auth context
      setUser((prev) => ({ ...prev, ...update }));
      toast.success("Profil mis à jour");
    } catch (err) {
      toast.error(err.message);
    } finally {
      setProfileLoading(false);
    }
  };

  const handleSavePrivacy = async () => {
    setPrivacyLoading(true);
    try {
      await api.updatePrivacy(privacy);
      toast.success("Paramètres de confidentialité mis à jour");
    } catch (err) {
      toast.error(err.message);
    } finally {
      setPrivacyLoading(false);
    }
  };

  if (initialLoading) {
    return (
      <AppLayout>
        <div className="flex items-center justify-center py-32">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      {/* Header */}
      <div className="flex items-center gap-4 mb-8">
        <Button variant="ghost" size="icon" onClick={() => navigate("/profile")}>
          <ArrowLeft className="w-5 h-5" />
        </Button>
        <div>
          <h1 className="font-heading text-3xl font-semibold">Modifier mon profil</h1>
          <p className="text-muted-foreground">Personnalisez votre présence sur InFinea</p>
        </div>
      </div>

      {/* Profile Edit */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="font-heading text-lg flex items-center gap-2">
            <User className="w-5 h-5" />
            Informations publiques
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Avatar preview */}
          <div className="flex items-center gap-6">
            <Avatar className="w-20 h-20">
              <AvatarImage src={avatarUrl} alt={displayName} />
              <AvatarFallback className="bg-primary/10 text-primary text-2xl">
                {getInitials(displayName)}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1">
              <Label htmlFor="avatar_url">URL de l'avatar</Label>
              <Input
                id="avatar_url"
                value={avatarUrl}
                onChange={(e) => setAvatarUrl(e.target.value)}
                placeholder="https://..."
                className="mt-1"
              />
            </div>
          </div>

          {/* Display name */}
          <div>
            <Label htmlFor="display_name">Nom d'affichage</Label>
            <Input
              id="display_name"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="Votre nom public"
              className="mt-1"
              maxLength={50}
            />
          </div>

          {/* Bio */}
          <div>
            <Label htmlFor="bio">Bio</Label>
            <Textarea
              id="bio"
              value={bio}
              onChange={(e) => setBio(e.target.value)}
              placeholder="Parlez de vous en quelques mots..."
              className="mt-1 resize-none"
              rows={3}
              maxLength={280}
            />
            <p className="text-xs text-muted-foreground mt-1">{bio.length}/280</p>
          </div>

          <Button
            onClick={handleSaveProfile}
            disabled={profileLoading}
            className="rounded-xl"
          >
            {profileLoading ? (
              <Loader2 className="w-4 h-4 animate-spin mr-2" />
            ) : (
              <Save className="w-4 h-4 mr-2" />
            )}
            Enregistrer le profil
          </Button>
        </CardContent>
      </Card>

      {/* Privacy Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="font-heading text-lg flex items-center gap-2">
            <Shield className="w-5 h-5" />
            Confidentialité
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Eye className="w-5 h-5 text-muted-foreground" />
              <div>
                <p className="font-medium">Profil visible</p>
                <p className="text-sm text-muted-foreground">
                  Les autres peuvent voir votre profil
                </p>
              </div>
            </div>
            <Switch
              checked={privacy.profile_visible}
              onCheckedChange={(v) => setPrivacy((p) => ({ ...p, profile_visible: v }))}
            />
          </div>

          <Separator />

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <BarChart3 className="w-5 h-5 text-muted-foreground" />
              <div>
                <p className="font-medium">Afficher les stats</p>
                <p className="text-sm text-muted-foreground">
                  Temps investi et streak visibles
                </p>
              </div>
            </div>
            <Switch
              checked={privacy.show_stats}
              onCheckedChange={(v) => setPrivacy((p) => ({ ...p, show_stats: v }))}
            />
          </div>

          <Separator />

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Award className="w-5 h-5 text-muted-foreground" />
              <div>
                <p className="font-medium">Afficher les badges</p>
                <p className="text-sm text-muted-foreground">
                  Vos badges sont visibles sur votre profil
                </p>
              </div>
            </div>
            <Switch
              checked={privacy.show_badges}
              onCheckedChange={(v) => setPrivacy((p) => ({ ...p, show_badges: v }))}
            />
          </div>

          <Separator />

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <BookOpen className="w-5 h-5 text-muted-foreground" />
              <div>
                <p className="font-medium">Afficher les réflexions</p>
                <p className="text-sm text-muted-foreground">
                  Vos réflexions de journal sont visibles
                </p>
              </div>
            </div>
            <Switch
              checked={privacy.show_reflections}
              onCheckedChange={(v) => setPrivacy((p) => ({ ...p, show_reflections: v }))}
            />
          </div>

          <Separator />

          <div>
            <div className="flex items-center gap-3 mb-3">
              <Users className="w-5 h-5 text-muted-foreground" />
              <div>
                <p className="font-medium">Visibilité de l'activité</p>
                <p className="text-sm text-muted-foreground">
                  Qui peut voir vos sessions dans le feed
                </p>
              </div>
            </div>
            <div className="flex gap-2">
              {[
                { value: "public", label: "Tout le monde" },
                { value: "followers", label: "Mes followers" },
                { value: "private", label: "Personne" },
              ].map((opt) => (
                <Button
                  key={opt.value}
                  variant={
                    privacy.activity_default_visibility === opt.value
                      ? "default"
                      : "outline"
                  }
                  size="sm"
                  className="rounded-full"
                  onClick={() =>
                    setPrivacy((p) => ({
                      ...p,
                      activity_default_visibility: opt.value,
                    }))
                  }
                >
                  {opt.label}
                </Button>
              ))}
            </div>
          </div>

          <Button
            onClick={handleSavePrivacy}
            disabled={privacyLoading}
            className="rounded-xl"
          >
            {privacyLoading ? (
              <Loader2 className="w-4 h-4 animate-spin mr-2" />
            ) : (
              <Save className="w-4 h-4 mr-2" />
            )}
            Enregistrer la confidentialité
          </Button>
        </CardContent>
      </Card>
    </AppLayout>
  );
}
