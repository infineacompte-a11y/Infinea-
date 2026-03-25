import React, { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Target,
  Loader2,
  Users,
  Heart,
  BookOpen,
  Sparkles,
  Plus,
  Globe,
  Lock,
  Timer,
  Repeat,
  BarChart3,
} from "lucide-react";
import { toast } from "sonner";
import { API, authFetch } from "@/App";

/**
 * CreateChallengeDialog — Full custom challenge creation form.
 * Pattern: Strava challenge creation (single-page, sectioned, smart defaults).
 *
 * Props:
 *   open — boolean
 *   onOpenChange — function
 *   onCreated — (challenge) => void (callback after challenge created)
 */

const CATEGORIES = [
  { key: "learning", label: "Apprentissage", icon: BookOpen },
  { key: "productivity", label: "Productivit\u00e9", icon: Target },
  { key: "well_being", label: "Bien-\u00eatre", icon: Heart },
  { key: "mixed", label: "Mixte", icon: Sparkles },
];

const CATEGORY_COLORS = {
  learning: "bg-[#459492]/10 text-[#459492] border-[#459492]/30",
  productivity: "bg-[#55B3AE]/10 text-[#55B3AE] border-[#55B3AE]/30",
  well_being: "bg-[#E48C75]/10 text-[#E48C75] border-[#E48C75]/30",
  mixed: "bg-purple-500/10 text-purple-500 border-purple-500/30",
};

const TYPES = [
  { key: "duo", label: "Duo", desc: "\u00c0 deux", icon: Users },
  { key: "group", label: "Groupe", desc: "3\u201310 pers.", icon: Users },
  { key: "community", label: "Communaut\u00e9", desc: "Ouvert", icon: Globe },
];

const GOALS = [
  { key: "sessions", label: "Sessions", icon: BarChart3, unit: "sessions", defaultVal: 10 },
  { key: "time", label: "Temps", icon: Timer, unit: "minutes", defaultVal: 60 },
  { key: "streak", label: "Streak", icon: Repeat, unit: "jours", defaultVal: 7 },
];

const DURATION_PRESETS = [3, 5, 7, 14, 21, 30];

export default function CreateChallengeDialog({ open, onOpenChange, onCreated }) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("mixed");
  const [challengeType, setChallengeType] = useState("group");
  const [goalType, setGoalType] = useState("sessions");
  const [goalValue, setGoalValue] = useState(10);
  const [durationDays, setDurationDays] = useState(7);
  const [privacy, setPrivacy] = useState("invite_only");
  const [creating, setCreating] = useState(false);

  const resetForm = () => {
    setTitle("");
    setDescription("");
    setCategory("mixed");
    setChallengeType("group");
    setGoalType("sessions");
    setGoalValue(10);
    setDurationDays(7);
    setPrivacy("invite_only");
  };

  const handleClose = (isOpen) => {
    onOpenChange(isOpen);
    if (!isOpen) resetForm();
  };

  const handleCreate = async () => {
    const trimmed = title.trim();
    if (!trimmed) {
      toast.error("Le titre est obligatoire");
      return;
    }
    if (trimmed.length < 3) {
      toast.error("Le titre doit faire au moins 3 caract\u00e8res");
      return;
    }
    setCreating(true);
    try {
      const res = await authFetch(`${API}/challenges`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: trimmed,
          description: description.trim(),
          challenge_type: challengeType,
          category,
          goal_type: goalType,
          goal_value: goalValue,
          duration_days: durationDays,
          privacy,
        }),
      });
      if (res.ok) {
        const challenge = await res.json();
        toast.success(`D\u00e9fi \u00ab ${challenge.title} \u00bb cr\u00e9\u00e9 !`);
        handleClose(false);
        onCreated?.(challenge);
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || "Erreur lors de la cr\u00e9ation");
      }
    } catch {
      toast.error("Erreur de connexion");
    } finally {
      setCreating(false);
    }
  };

  const currentGoal = GOALS.find((g) => g.key === goalType);

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-lg max-h-[85vh] overflow-y-auto bg-card border-border">
        <DialogHeader>
          <DialogTitle className="font-sans font-semibold tracking-tight flex items-center gap-2">
            <Plus className="w-5 h-5 text-primary" />
            Cr\u00e9er un d\u00e9fi personnalis\u00e9
          </DialogTitle>
          <p className="text-xs text-muted-foreground mt-0.5">
            D\u00e9finissez votre propre challenge et invitez vos amis
          </p>
        </DialogHeader>

        <div className="space-y-5 pt-1">
          {/* ── Title ── */}
          <div>
            <SectionLabel>Titre du d\u00e9fi *</SectionLabel>
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value.slice(0, 100))}
              placeholder="Ex : Sprint productivit\u00e9 7 jours"
              className="h-10"
              autoFocus
            />
            <div className="flex justify-between mt-1">
              <p className="text-[10px] text-muted-foreground">
                Choisissez un titre motivant et clair
              </p>
              <p className="text-[10px] text-muted-foreground tabular-nums">
                {title.length}/100
              </p>
            </div>
          </div>

          {/* ── Description ── */}
          <div>
            <SectionLabel>Description</SectionLabel>
            <Textarea
              value={description}
              onChange={(e) => setDescription(e.target.value.slice(0, 500))}
              placeholder="D\u00e9crivez l\u2019objectif et les r\u00e8gles du d\u00e9fi..."
              rows={2}
              className="resize-none text-sm"
            />
            <p className="text-[10px] text-muted-foreground mt-1 text-right tabular-nums">
              {description.length}/500
            </p>
          </div>

          {/* ── Category ── */}
          <div>
            <SectionLabel>Cat\u00e9gorie</SectionLabel>
            <div className="grid grid-cols-2 gap-2">
              {CATEGORIES.map((cat) => {
                const Icon = cat.icon;
                const isActive = category === cat.key;
                return (
                  <button
                    key={cat.key}
                    type="button"
                    onClick={() => setCategory(cat.key)}
                    className={`flex items-center gap-2 p-2.5 rounded-xl border transition-all duration-200 text-left ${
                      isActive
                        ? CATEGORY_COLORS[cat.key]
                        : "border-border/50 text-muted-foreground hover:border-border hover:text-foreground"
                    }`}
                  >
                    <Icon className="w-4 h-4 shrink-0" />
                    <span className="font-medium text-xs">{cat.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* ── Challenge Type ── */}
          <div>
            <SectionLabel>Type de d\u00e9fi</SectionLabel>
            <div className="grid grid-cols-3 gap-2">
              {TYPES.map((type) => {
                const Icon = type.icon;
                const isActive = challengeType === type.key;
                return (
                  <button
                    key={type.key}
                    type="button"
                    onClick={() => {
                      setChallengeType(type.key);
                      if (type.key === "community") setPrivacy("public");
                      else setPrivacy("invite_only");
                    }}
                    className={`flex flex-col items-center gap-1 p-3 rounded-xl border transition-all duration-200 ${
                      isActive
                        ? "bg-primary/8 border-primary/30 text-foreground ring-1 ring-primary/20"
                        : "border-border/50 text-muted-foreground hover:border-border hover:text-foreground"
                    }`}
                  >
                    <Icon className={`w-5 h-5 ${isActive ? "text-primary" : ""}`} />
                    <span className="font-medium text-xs">{type.label}</span>
                    <span className="text-[10px] text-muted-foreground leading-tight">
                      {type.desc}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* ── Goal ── */}
          <div>
            <SectionLabel>Objectif</SectionLabel>
            <div className="flex gap-1.5 mb-3">
              {GOALS.map((goal) => {
                const Icon = goal.icon;
                return (
                  <button
                    key={goal.key}
                    type="button"
                    onClick={() => {
                      setGoalType(goal.key);
                      setGoalValue(goal.defaultVal);
                    }}
                    className={`flex-1 flex items-center justify-center gap-1.5 py-2 px-2 rounded-lg text-xs font-medium transition-all duration-200 ${
                      goalType === goal.key
                        ? "bg-primary text-white shadow-sm"
                        : "bg-muted/40 text-muted-foreground hover:bg-muted/70 hover:text-foreground"
                    }`}
                  >
                    <Icon className="w-3.5 h-3.5" />
                    {goal.label}
                  </button>
                );
              })}
            </div>
            <div className="flex items-center gap-3">
              <Input
                type="number"
                min={1}
                max={10000}
                value={goalValue}
                onChange={(e) => {
                  const v = parseInt(e.target.value, 10);
                  if (!isNaN(v)) setGoalValue(Math.max(1, Math.min(10000, v)));
                }}
                className="w-24 h-10 text-center font-semibold tabular-nums"
              />
              <span className="text-sm text-muted-foreground">
                {currentGoal?.unit || ""}
              </span>
              <p className="text-[10px] text-muted-foreground ml-auto">
                {goalType === "sessions" && "Sessions compl\u00e9t\u00e9es par tous"}
                {goalType === "time" && "Minutes cumul\u00e9es par tous"}
                {goalType === "streak" && "Jours cons\u00e9cutifs d\u2019activit\u00e9"}
              </p>
            </div>
          </div>

          {/* ── Duration ── */}
          <div>
            <SectionLabel>Dur\u00e9e</SectionLabel>
            <div className="flex flex-wrap gap-1.5">
              {DURATION_PRESETS.map((d) => (
                <button
                  key={d}
                  type="button"
                  onClick={() => setDurationDays(d)}
                  className={`px-3.5 py-1.5 rounded-full text-xs font-medium transition-all duration-200 ${
                    durationDays === d
                      ? "bg-primary text-white shadow-sm"
                      : "bg-muted/40 text-muted-foreground hover:bg-muted/70 hover:text-foreground"
                  }`}
                >
                  {d} jour{d > 1 ? "s" : ""}
                </button>
              ))}
            </div>
          </div>

          {/* ── Privacy (group/community only) ── */}
          {challengeType !== "duo" && (
            <div>
              <SectionLabel>Visibilit\u00e9</SectionLabel>
              <div className="flex gap-2">
                {[
                  { key: "invite_only", label: "Sur invitation", icon: Lock },
                  { key: "public", label: "Public", icon: Globe },
                ].map((opt) => {
                  const Icon = opt.icon;
                  const isActive = privacy === opt.key;
                  return (
                    <button
                      key={opt.key}
                      type="button"
                      onClick={() => setPrivacy(opt.key)}
                      className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl border transition-all duration-200 ${
                        isActive
                          ? "bg-primary/8 border-primary/30 text-foreground ring-1 ring-primary/20"
                          : "border-border/50 text-muted-foreground hover:border-border"
                      }`}
                    >
                      <Icon className="w-3.5 h-3.5" />
                      <span className="font-medium text-xs">{opt.label}</span>
                    </button>
                  );
                })}
              </div>
              <p className="text-[10px] text-muted-foreground mt-1.5">
                {privacy === "public"
                  ? "Visible dans l\u2019onglet D\u00e9couvrir \u2014 tout le monde peut rejoindre"
                  : "Seules les personnes invit\u00e9es peuvent rejoindre"}
              </p>
            </div>
          )}

          {/* ── Preview summary ── */}
          {title.trim() && (
            <div className="rounded-xl bg-muted/30 border border-border/50 p-3 space-y-1.5">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                R\u00e9sum\u00e9
              </p>
              <p className="text-sm font-semibold">{title.trim()}</p>
              <div className="flex flex-wrap gap-x-3 gap-y-1 text-[11px] text-muted-foreground">
                <span>
                  {CATEGORIES.find((c) => c.key === category)?.label}
                </span>
                <span>\u00b7</span>
                <span>
                  {TYPES.find((t) => t.key === challengeType)?.label}
                </span>
                <span>\u00b7</span>
                <span>
                  {goalValue} {currentGoal?.unit}
                </span>
                <span>\u00b7</span>
                <span>
                  {durationDays} jour{durationDays > 1 ? "s" : ""}
                </span>
                <span>\u00b7</span>
                <span>
                  {privacy === "public" ? "Public" : "Priv\u00e9"}
                </span>
              </div>
            </div>
          )}
        </div>

        <DialogFooter className="pt-3">
          <Button
            type="button"
            variant="outline"
            onClick={() => handleClose(false)}
            disabled={creating}
          >
            Annuler
          </Button>
          <Button
            onClick={handleCreate}
            disabled={creating || !title.trim() || title.trim().length < 3}
            className="gap-2"
          >
            {creating ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Plus className="w-4 h-4" />
            )}
            Cr\u00e9er le d\u00e9fi
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

/** Reusable section label */
function SectionLabel({ children }) {
  return (
    <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-1.5">
      {children}
    </p>
  );
}
