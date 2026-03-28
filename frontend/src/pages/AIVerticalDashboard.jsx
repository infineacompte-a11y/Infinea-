import React, { useState, useEffect, useCallback } from "react";
import { authFetch } from "@/App";
import {
  Brain, Activity, MessageCircle, DollarSign, Users, TrendingUp,
  AlertTriangle, Zap, BarChart3, PieChart, Target, Clock, Shield,
  RefreshCw, ChevronDown, ChevronUp, Sparkles, Heart, Eye,
  ArrowUpRight, ArrowDownRight, Minus, Loader2
} from "lucide-react";

const API = process.env.REACT_APP_API_URL || "";

// ── KPI Card ──
function KPICard({ label, value, icon: Icon, trend, trendLabel, color = "teal", subtitle }) {
  const colors = {
    teal: "from-teal-500/20 to-teal-600/10 border-teal-500/30",
    orange: "from-orange-500/20 to-orange-600/10 border-orange-500/30",
    blue: "from-blue-500/20 to-blue-600/10 border-blue-500/30",
    green: "from-green-500/20 to-green-600/10 border-green-500/30",
    red: "from-red-500/20 to-red-600/10 border-red-500/30",
    purple: "from-purple-500/20 to-purple-600/10 border-purple-500/30",
  };
  const TrendIcon = trend > 0 ? ArrowUpRight : trend < 0 ? ArrowDownRight : Minus;
  const trendColor = trend > 0 ? "text-green-400" : trend < 0 ? "text-red-400" : "text-gray-400";

  return (
    <div className={`rounded-2xl border bg-gradient-to-br ${colors[color]} p-5 transition-all hover:scale-[1.02]`}>
      <div className="flex items-start justify-between mb-3">
        <div className="p-2 rounded-xl bg-white/10">
          <Icon size={20} className="text-white/80" />
        </div>
        {trend !== undefined && (
          <div className={`flex items-center gap-1 text-xs ${trendColor}`}>
            <TrendIcon size={14} />
            <span>{trendLabel || `${Math.abs(trend)}%`}</span>
          </div>
        )}
      </div>
      <div className="text-2xl font-bold text-white">{value}</div>
      <div className="text-sm text-white/60 mt-1">{label}</div>
      {subtitle && <div className="text-xs text-white/40 mt-1">{subtitle}</div>}
    </div>
  );
}

// ── Section Header ──
function SectionHeader({ icon: Icon, title, subtitle, action }) {
  return (
    <div className="flex items-center justify-between mb-4">
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-xl bg-teal-500/20">
          <Icon size={20} className="text-teal-400" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-white">{title}</h2>
          {subtitle && <p className="text-xs text-white/50">{subtitle}</p>}
        </div>
      </div>
      {action}
    </div>
  );
}

// ── Progress Bar ──
function ProgressBar({ value, max, label, color = "teal" }) {
  const pct = Math.min(100, Math.round((value / Math.max(max, 1)) * 100));
  const colors = { teal: "bg-teal-500", orange: "bg-orange-500", blue: "bg-blue-500", green: "bg-green-500", red: "bg-red-500" };
  return (
    <div className="mb-3">
      <div className="flex justify-between text-xs text-white/60 mb-1">
        <span>{label}</span>
        <span>{pct}%</span>
      </div>
      <div className="h-2 bg-white/10 rounded-full overflow-hidden">
        <div className={`h-full ${colors[color]} rounded-full transition-all duration-500`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

// ── Stat Row ──
function StatRow({ label, value, icon: Icon }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
      <div className="flex items-center gap-2">
        {Icon && <Icon size={14} className="text-white/40" />}
        <span className="text-sm text-white/70">{label}</span>
      </div>
      <span className="text-sm font-medium text-white">{value}</span>
    </div>
  );
}

// ── Mini Bar Chart ──
function MiniBarChart({ data, labelKey, valueKey, maxBars = 7 }) {
  if (!data || !data.length) return <div className="text-xs text-white/40 py-4 text-center">Pas encore de donnees</div>;
  const items = data.slice(-maxBars);
  const max = Math.max(...items.map(d => d[valueKey] || 0), 1);
  return (
    <div className="flex items-end gap-1 h-24 mt-2">
      {items.map((d, i) => (
        <div key={i} className="flex-1 flex flex-col items-center gap-1">
          <div
            className="w-full bg-teal-500/60 rounded-t hover:bg-teal-400/80 transition-colors"
            style={{ height: `${Math.max(4, ((d[valueKey] || 0) / max) * 100)}%` }}
            title={`${d[labelKey]}: ${d[valueKey]}`}
          />
          <span className="text-[10px] text-white/40 truncate w-full text-center">
            {String(d[labelKey] || "").slice(-5)}
          </span>
        </div>
      ))}
    </div>
  );
}

// ── Main Dashboard ──
export default function AIVerticalDashboard() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");
  const [data, setData] = useState({});
  const [lastRefresh, setLastRefresh] = useState(null);

  const tabs = [
    { id: "overview", label: "Vue d'ensemble", icon: BarChart3 },
    { id: "coaching", label: "Coaching Kira", icon: Brain },
    { id: "memory", label: "Memoire IA", icon: Sparkles },
    { id: "costs", label: "Couts", icon: DollarSign },
    { id: "collective", label: "Intelligence", icon: Users },
    { id: "drift", label: "Drift & Alertes", icon: AlertTriangle },
    { id: "trends", label: "Tendances", icon: TrendingUp },
  ];

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const endpoints = ["overview", "coaching", "memory", "costs", "collective", "drift", "feature-trends"];
      const results = await Promise.allSettled(
        endpoints.map(e => authFetch(`${API}/api/admin/ai/${e}`).then(r => r.ok ? r.json() : null))
      );
      const newData = {};
      endpoints.forEach((e, i) => {
        const key = e.replace("-", "_");
        newData[key] = results[i].status === "fulfilled" ? results[i].value : null;
      });
      setData(newData);
      setLastRefresh(new Date());
    } catch (err) {
      setError("Erreur de chargement. Verifiez vos droits admin.");
    }
    setLoading(false);
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Shield size={48} className="text-red-400 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-white mb-2">Acces restreint</h2>
          <p className="text-white/60">{error}</p>
        </div>
      </div>
    );
  }

  const overview = data.overview || {};
  const coaching = data.coaching || {};
  const memory = data.memory || {};
  const costs = data.costs || {};
  const collective = data.collective || {};
  const drift = data.drift || {};
  const trends = data.feature_trends || {};

  return (
    <div className="min-h-screen pb-20">
      {/* Header */}
      <div className="px-6 pt-6 pb-4">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-white flex items-center gap-3">
              <Brain className="text-teal-400" size={28} />
              IA Verticale — Cockpit
            </h1>
            <p className="text-sm text-white/50 mt-1">
              Pilotage en temps reel de Kira et de l'intelligence InFinea
            </p>
          </div>
          <button
            onClick={fetchAll}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-teal-500/20 border border-teal-500/30 text-teal-400 hover:bg-teal-500/30 transition-all text-sm"
          >
            <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
            {loading ? "Chargement..." : "Actualiser"}
          </button>
        </div>

        {lastRefresh && (
          <p className="text-xs text-white/30 mb-4">
            Derniere mise a jour : {lastRefresh.toLocaleTimeString("fr-FR")}
          </p>
        )}

        {/* Tabs */}
        <div className="flex gap-1 overflow-x-auto pb-2 scrollbar-hide">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm whitespace-nowrap transition-all ${
                activeTab === tab.id
                  ? "bg-teal-500/30 text-teal-300 border border-teal-500/40"
                  : "text-white/50 hover:text-white/80 hover:bg-white/5"
              }`}
            >
              <tab.icon size={16} />
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 size={32} className="text-teal-400 animate-spin" />
        </div>
      ) : (
        <div className="px-6">
          {/* ═══ OVERVIEW ═══ */}
          {activeTab === "overview" && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <KPICard label="Utilisateurs actifs (7j)" value={overview.active_users_7d || 0} icon={Users} color="teal" />
                <KPICard label="Appels IA aujourd'hui" value={overview.ai_calls_today || 0} icon={Zap} color="blue" />
                <KPICard label="Cout IA aujourd'hui" value={`$${overview.ai_cost_today_usd || 0}`} icon={DollarSign} color="orange" />
                <KPICard label="Memoires IA actives" value={overview.total_ai_memories || 0} icon={Brain} color="purple" />
              </div>

              <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
                <SectionHeader icon={Activity} title="Sante du systeme" subtitle="Derniere computation de features" />
                <StatRow label="Derniere computation" value={overview.last_feature_computation ? new Date(overview.last_feature_computation).toLocaleString("fr-FR") : "N/A"} icon={Clock} />
                <StatRow label="Utilisateurs traites" value={overview.last_feature_users_processed || 0} icon={Users} />
              </div>
            </div>
          )}

          {/* ═══ COACHING ═══ */}
          {activeTab === "coaching" && (
            <div className="space-y-6">
              <SectionHeader icon={Brain} title="Coaching Kira — Distribution Prochaska" subtitle="Repartition des utilisateurs par stade de changement comportemental" />

              <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                {["precontemplation", "contemplation", "preparation", "action", "maintenance"].map((stage, i) => {
                  const labels = { precontemplation: "Decouverte", contemplation: "Exploration", preparation: "Construction", action: "Action", maintenance: "Maitrise" };
                  const colors = ["orange", "blue", "teal", "green", "purple"];
                  const count = (coaching.stage_distribution || {})[stage] || 0;
                  return (
                    <KPICard key={stage} label={labels[stage]} value={count} icon={Target} color={colors[i]} subtitle={`Stade ${i + 1}/5`} />
                  );
                })}
              </div>

              <div className="grid md:grid-cols-2 gap-4">
                <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
                  <SectionHeader icon={Heart} title="Qualite des reponses" subtitle="Feedback par endpoint" />
                  {Object.entries(coaching.feedback_by_endpoint || {}).map(([ep, stats]) => (
                    <StatRow key={ep} label={ep} value={`${stats.avg_rating}/5 (${stats.total} avis)`} icon={MessageCircle} />
                  ))}
                  {!Object.keys(coaching.feedback_by_endpoint || {}).length && (
                    <p className="text-xs text-white/40 py-4 text-center">Pas encore de feedback</p>
                  )}
                </div>

                <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
                  <SectionHeader icon={Target} title="Suivi des suggestions" subtitle="Est-ce que les users suivent Kira ?" />
                  <div className="text-center py-4">
                    <div className="text-4xl font-bold text-teal-400">
                      {Math.round((coaching.suggestion_follow_rate || 0) * 100)}%
                    </div>
                    <div className="text-sm text-white/50 mt-2">Taux de suivi des suggestions</div>
                    <div className="text-xs text-white/30 mt-1">
                      {coaching.suggestions_followed_7d || 0} suivies / {coaching.coach_served_7d || 0} servies (7j)
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ═══ MEMORY ═══ */}
          {activeTab === "memory" && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <KPICard label="Memoires actives" value={memory.total_active_memories || 0} icon={Brain} color="purple" />
                <KPICard label="Utilisateurs avec memoire" value={memory.users_with_memories || 0} icon={Users} color="teal" />
                <KPICard label="Moyenne par user" value={memory.avg_memories_per_user || 0} icon={BarChart3} color="blue" />
                <KPICard label="Extraites (7j)" value={memory.memories_extracted_7d || 0} icon={Sparkles} color="orange" />
              </div>

              <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
                <SectionHeader icon={PieChart} title="Distribution par categorie" subtitle="Types de faits retenus par Kira" />
                {Object.entries(memory.category_distribution || {}).map(([cat, count]) => {
                  const labels = { goal: "Objectifs", preference: "Preferences", struggle: "Difficultes", insight: "Ce qui marche", constraint: "Contraintes" };
                  const colors = { goal: "teal", preference: "blue", struggle: "red", insight: "green", constraint: "orange" };
                  const total = memory.total_active_memories || 1;
                  return <ProgressBar key={cat} label={labels[cat] || cat} value={count} max={total} color={colors[cat] || "teal"} />;
                })}
                {!Object.keys(memory.category_distribution || {}).length && (
                  <p className="text-xs text-white/40 py-4 text-center">Pas encore de memoires</p>
                )}
              </div>
            </div>
          )}

          {/* ═══ COSTS ═══ */}
          {activeTab === "costs" && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <KPICard
                  label="Cache hit rate"
                  value={`${Math.round((costs.cache_hit_rate || 0) * 100)}%`}
                  icon={Zap}
                  color="green"
                  subtitle="Economies sur les prompts"
                />
                <KPICard
                  label="Tokens cache lus (7j)"
                  value={(costs.cache_read_tokens_7d || 0).toLocaleString()}
                  icon={Eye}
                  color="blue"
                />
                <KPICard
                  label="Cout total (7j)"
                  value={`$${(costs.cost_by_endpoint_7d || []).reduce((s, e) => s + e.cost_usd, 0).toFixed(2)}`}
                  icon={DollarSign}
                  color="orange"
                />
              </div>

              <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
                <SectionHeader icon={BarChart3} title="Cout par endpoint (7j)" subtitle="Repartition des depenses IA" />
                {(costs.cost_by_endpoint_7d || []).map(ep => (
                  <div key={ep.endpoint} className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
                    <div>
                      <span className="text-sm text-white/70">{ep.endpoint}</span>
                      <span className="text-xs text-white/30 ml-2">({ep.calls} appels)</span>
                    </div>
                    <div className="text-right">
                      <span className="text-sm font-medium text-white">${ep.cost_usd.toFixed(4)}</span>
                      <span className="text-xs text-white/30 ml-2">{ep.avg_input_tokens} tok moy.</span>
                    </div>
                  </div>
                ))}
              </div>

              <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
                <SectionHeader icon={PieChart} title="Cout par modele (7j)" />
                {(costs.cost_by_model_7d || []).map(m => (
                  <StatRow key={m.model} label={m.model} value={`$${m.cost_usd.toFixed(4)} (${m.calls} appels)`} icon={Brain} />
                ))}
              </div>
            </div>
          )}

          {/* ═══ COLLECTIVE ═══ */}
          {activeTab === "collective" && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <KPICard label="Patterns actifs" value={collective.active_patterns || 0} icon={Users} color="teal" />
                <KPICard label="Versions historiques" value={collective.history_versions || 0} icon={Clock} color="blue" />
              </div>

              <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
                <SectionHeader icon={Brain} title="Patterns detectes" subtitle="Intelligence collective issue des donnees agregees" />
                {(collective.patterns || []).map((p, i) => (
                  <div key={i} className="py-3 border-b border-white/5 last:border-0">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-teal-400">{p.pattern_type}</span>
                      <span className="text-xs text-white/40">
                        {p.sample_size} users | conf. {Math.round((p.confidence || 0) * 100)}%
                      </span>
                    </div>
                    <div className="text-xs text-white/50">Segment: {p.segment}</div>
                    {p.data && (
                      <pre className="text-xs text-white/30 mt-1 overflow-x-auto">
                        {JSON.stringify(p.data, null, 2).slice(0, 200)}
                      </pre>
                    )}
                  </div>
                ))}
                {!(collective.patterns || []).length && (
                  <p className="text-xs text-white/40 py-4 text-center">
                    Les patterns se calculent chaque semaine (min 50 utilisateurs)
                  </p>
                )}
              </div>
            </div>
          )}

          {/* ═══ DRIFT ═══ */}
          {activeTab === "drift" && (
            <div className="space-y-6">
              <div className="grid grid-cols-3 gap-4">
                <KPICard
                  label="Utilisateurs en drift"
                  value={drift.users_drifting || 0}
                  icon={AlertTriangle}
                  color={drift.users_drifting > 0 ? "red" : "green"}
                  subtitle="engagement_trend < -0.3"
                />
                <KPICard
                  label="Abandon eleve"
                  value={drift.users_high_abandonment || 0}
                  icon={TrendingUp}
                  color={drift.users_high_abandonment > 0 ? "orange" : "green"}
                  subtitle="abandonment_rate > 40%"
                />
                <KPICard
                  label="Fatigue categorie"
                  value={drift.users_category_fatigued || 0}
                  icon={Activity}
                  color={drift.users_category_fatigued > 0 ? "orange" : "green"}
                  subtitle="hausse abandon par categorie"
                />
              </div>

              <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
                <SectionHeader icon={Shield} title="Interpretation" subtitle="Signaux de risque detectes par le systeme" />
                {(drift.users_drifting || 0) === 0 && (drift.users_high_abandonment || 0) === 0 ? (
                  <div className="text-center py-6">
                    <div className="text-3xl mb-2">&#9989;</div>
                    <div className="text-sm text-green-400">Aucun signal de risque detecte</div>
                    <div className="text-xs text-white/40 mt-1">Tous les utilisateurs sont dans une trajectoire positive</div>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {drift.users_drifting > 0 && (
                      <div className="flex items-center gap-3 p-3 rounded-xl bg-red-500/10 border border-red-500/20">
                        <AlertTriangle size={18} className="text-red-400" />
                        <span className="text-sm text-white/80">{drift.users_drifting} utilisateur(s) avec engagement en forte baisse</span>
                      </div>
                    )}
                    {drift.users_high_abandonment > 0 && (
                      <div className="flex items-center gap-3 p-3 rounded-xl bg-orange-500/10 border border-orange-500/20">
                        <Activity size={18} className="text-orange-400" />
                        <span className="text-sm text-white/80">{drift.users_high_abandonment} utilisateur(s) avec taux d'abandon eleve</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ═══ TRENDS ═══ */}
          {activeTab === "trends" && (
            <div className="space-y-6">
              <SectionHeader icon={TrendingUp} title="Evolution des features (30j)" subtitle="Tendances globales de la base utilisateurs" />

              <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
                <h3 className="text-sm font-medium text-white/70 mb-2">Taux de completion moyen</h3>
                <MiniBarChart
                  data={(trends.daily_trends || []).map(d => ({
                    date: d.date,
                    value: Math.round((d.avg_completion_rate || 0) * 100),
                  }))}
                  labelKey="date"
                  valueKey="value"
                  maxBars={14}
                />
              </div>

              <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
                <h3 className="text-sm font-medium text-white/70 mb-2">Regularite moyenne</h3>
                <MiniBarChart
                  data={(trends.daily_trends || []).map(d => ({
                    date: d.date,
                    value: Math.round((d.avg_consistency || 0) * 100),
                  }))}
                  labelKey="date"
                  valueKey="value"
                  maxBars={14}
                />
              </div>

              <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
                <h3 className="text-sm font-medium text-white/70 mb-2">Utilisateurs traites par jour</h3>
                <MiniBarChart
                  data={(trends.daily_trends || []).map(d => ({
                    date: d.date,
                    value: d.users_computed || 0,
                  }))}
                  labelKey="date"
                  valueKey="value"
                  maxBars={14}
                />
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
