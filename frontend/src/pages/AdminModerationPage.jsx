import React, { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Textarea } from "@/components/ui/textarea";
import {
  Shield,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  MessageCircle,
  UserX,
  Trash2,
  Eye,
  ChevronLeft,
  RefreshCw,
  Filter,
  Loader2,
} from "lucide-react";
import { toast } from "sonner";
import { API, useAuth, authFetch } from "@/App";
import Sidebar from "@/components/Sidebar";

const REASON_LABELS = {
  harassment: "Harcèlement",
  spam: "Spam",
  hate_speech: "Discours haineux",
  inappropriate_content: "Contenu inapproprié",
  impersonation: "Usurpation d'identité",
  self_harm: "Automutilation",
  other: "Autre",
};

const REASON_COLORS = {
  harassment: "bg-red-500/15 text-red-500 border-red-500/20",
  spam: "bg-yellow-500/15 text-yellow-500 border-yellow-500/20",
  hate_speech: "bg-red-600/15 text-red-600 border-red-600/20",
  inappropriate_content: "bg-orange-500/15 text-orange-500 border-orange-500/20",
  impersonation: "bg-purple-500/15 text-purple-500 border-purple-500/20",
  self_harm: "bg-red-700/15 text-red-700 border-red-700/20",
  other: "bg-muted text-muted-foreground border-border",
};

const TYPE_LABELS = { user: "Utilisateur", comment: "Commentaire", activity: "Activité", group: "Groupe" };

const STATUS_TABS = [
  { key: "pending", label: "En attente" },
  { key: "resolved", label: "Résolus" },
  { key: "dismissed", label: "Rejetés" },
];

export default function AdminModerationPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [reports, setReports] = useState([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("pending");
  const [selectedReport, setSelectedReport] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [adminNote, setAdminNote] = useState("");

  const fetchStats = useCallback(async () => {
    try {
      const res = await authFetch(`${API}/admin/reports/stats`);
      if (res.ok) setStats(await res.json());
    } catch { /* silently fail */ }
  }, []);

  const fetchReports = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await authFetch(`${API}/admin/reports?status=${statusFilter}&limit=50`);
      if (res.ok) {
        const data = await res.json();
        setReports(data.reports || []);
        setTotal(data.total || 0);
      } else if (res.status === 403) {
        toast.error("Accès réservé aux administrateurs");
      }
    } catch {
      toast.error("Erreur de chargement");
    } finally {
      setIsLoading(false);
    }
  }, [statusFilter]);

  const fetchDetail = async (reportId) => {
    setDetailLoading(true);
    setAdminNote("");
    try {
      const res = await authFetch(`${API}/admin/reports/${reportId}`);
      if (res.ok) setSelectedReport(await res.json());
    } catch {
      toast.error("Erreur de chargement du détail");
    } finally {
      setDetailLoading(false);
    }
  };

  const handleAction = async (action) => {
    if (!selectedReport) return;
    setActionLoading(true);
    try {
      const res = await authFetch(`${API}/admin/reports/${selectedReport.report_id}/action`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, note: adminNote }),
      });
      if (res.ok) {
        const data = await res.json();
        toast.success(`Action "${action}" effectuée`);
        setSelectedReport(null);
        fetchReports();
        fetchStats();
      }
    } catch {
      toast.error("Erreur lors de l'action");
    } finally {
      setActionLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    fetchReports();
  }, [fetchStats, fetchReports]);

  const initials = (name) => (name || "?").slice(0, 2).toUpperCase();

  return (
    <div className="min-h-screen app-bg-mesh">
      <Sidebar />
      <main className="lg:ml-64 pt-14 lg:pt-0 pb-8">
        {/* Dark Header */}
        <div className="section-dark-header px-4 lg:px-8 pt-8 lg:pt-10 pb-8">
          <div className="max-w-5xl mx-auto">
            <div className="flex items-center gap-3">
              <Shield className="w-7 h-7 text-white/80" />
              <div>
                <h1 className="text-display text-3xl lg:text-4xl font-semibold text-white opacity-0 animate-fade-in">
                  Modération
                </h1>
                <p className="text-white/60 text-sm mt-1 opacity-0 animate-fade-in" style={{ animationDelay: "50ms" }}>
                  Queue de signalements — administration
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="px-4 lg:px-8">
          <div className="max-w-5xl mx-auto">
            {/* ── Stats cards ── */}
            {stats && (
              <div
                className="opacity-0 animate-fade-in grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5"
                style={{ animationDelay: "150ms", animationFillMode: "forwards" }}
              >
                <Card className="p-4 rounded-xl">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-[#E48C75]" />
                    <span className="text-sm text-muted-foreground">En attente</span>
                  </div>
                  <p className="text-2xl font-bold mt-1 tabular-nums">{stats.pending}</p>
                </Card>
                <Card className="p-4 rounded-xl">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-[#5DB786]" />
                    <span className="text-sm text-muted-foreground">Résolus</span>
                  </div>
                  <p className="text-2xl font-bold mt-1 tabular-nums">{stats.resolved}</p>
                </Card>
                {Object.entries(stats.by_reason || {}).slice(0, 2).map(([reason, count]) => (
                  <Card key={reason} className="p-4 rounded-xl">
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-muted-foreground">{REASON_LABELS[reason] || reason}</span>
                    </div>
                    <p className="text-2xl font-bold mt-1 tabular-nums">{count}</p>
                  </Card>
                ))}
              </div>
            )}

            {/* ── Two-column layout: list + detail ── */}
            <div className="flex gap-4 flex-col lg:flex-row">
              {/* Left: report list */}
              <div className="flex-1 min-w-0">
                {/* Status tabs */}
                <div
                  className="opacity-0 animate-fade-in flex gap-1 p-1 mb-4 bg-muted/30 rounded-xl"
                  style={{ animationDelay: "200ms", animationFillMode: "forwards" }}
                >
                  {STATUS_TABS.map((tab) => (
                    <button
                      key={tab.key}
                      onClick={() => { setStatusFilter(tab.key); setSelectedReport(null); }}
                      className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-all duration-200 ${
                        statusFilter === tab.key
                          ? "bg-background shadow-sm text-foreground"
                          : "text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      {tab.label}
                      {tab.key === "pending" && stats?.pending > 0 && (
                        <Badge className="ml-1.5 h-4 px-1.5 text-[9px] bg-[#E48C75]/20 text-[#E48C75] border-[#E48C75]/20">
                          {stats.pending}
                        </Badge>
                      )}
                    </button>
                  ))}
                </div>

                {/* Report list */}
                {isLoading ? (
                  <div className="space-y-2">
                    {[...Array(4)].map((_, i) => (
                      <div key={i} className="rounded-xl border border-border bg-card p-4 animate-pulse">
                        <div className="flex items-start gap-3">
                          <div className="w-8 h-8 rounded-full bg-muted" />
                          <div className="flex-1 space-y-2">
                            <div className="h-3 w-2/5 rounded bg-muted" />
                            <div className="h-2 w-3/5 rounded bg-muted" />
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : reports.length === 0 ? (
                  <Card className="p-8 text-center rounded-xl">
                    <CheckCircle2 className="w-10 h-10 text-[#5DB786]/40 mx-auto mb-2" />
                    <h3 className="font-semibold mb-1">Queue vide</h3>
                    <p className="text-sm text-muted-foreground">
                      Aucun signalement {statusFilter === "pending" ? "en attente" : statusFilter === "resolved" ? "résolu" : "rejeté"}
                    </p>
                  </Card>
                ) : (
                  <div className="space-y-1.5">
                    {reports.map((report, idx) => {
                      const isSelected = selectedReport?.report_id === report.report_id;
                      const reasonColor = REASON_COLORS[report.reason] || REASON_COLORS.other;
                      return (
                        <div
                          key={report.report_id}
                          onClick={() => fetchDetail(report.report_id)}
                          className={`opacity-0 animate-fade-in group p-3 rounded-xl border cursor-pointer transition-all duration-200 hover:shadow-sm ${
                            isSelected
                              ? "border-[#459492]/40 bg-[#459492]/8 ring-1 ring-[#459492]/20"
                              : "border-border bg-card hover:bg-muted/20"
                          }`}
                          style={{ animationDelay: `${250 + idx * 25}ms`, animationFillMode: "forwards" }}
                        >
                          <div className="flex items-start gap-3">
                            <Avatar className="w-8 h-8">
                              <AvatarImage src={report.reporter_avatar} />
                              <AvatarFallback className="text-[10px]">{initials(report.reporter_name)}</AvatarFallback>
                            </Avatar>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-1.5 flex-wrap">
                                <span className="text-sm font-medium truncate">{report.reporter_name}</span>
                                <Badge className={`text-[9px] px-1.5 py-0 ${reasonColor}`}>
                                  {REASON_LABELS[report.reason] || report.reason}
                                </Badge>
                                <Badge variant="outline" className="text-[9px] px-1.5 py-0">
                                  {TYPE_LABELS[report.target_type] || report.target_type}
                                </Badge>
                              </div>
                              {report.details && (
                                <p className="text-xs text-muted-foreground mt-0.5 line-clamp-1">{report.details}</p>
                              )}
                              <p className="text-[10px] text-muted-foreground/60 mt-0.5 tabular-nums">
                                {new Date(report.created_at).toLocaleString("fr-FR")}
                              </p>
                            </div>
                            {report.action_taken && (
                              <Badge variant="secondary" className="text-[9px] shrink-0">
                                {report.action_taken}
                              </Badge>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Right: detail panel */}
              <div className="lg:w-[380px] shrink-0">
                {detailLoading ? (
                  <Card className="p-8 rounded-xl text-center">
                    <Loader2 className="w-6 h-6 animate-spin mx-auto text-muted-foreground" />
                  </Card>
                ) : selectedReport ? (
                  <Card className="rounded-xl sticky top-4">
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-base">Détail du signalement</CardTitle>
                        <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={() => setSelectedReport(null)}>
                          <XCircle className="w-4 h-4" />
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {/* Reporter */}
                      <div>
                        <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1">Signalé par</p>
                        <div className="flex items-center gap-2">
                          <Avatar className="w-6 h-6">
                            <AvatarImage src={selectedReport.reporter?.avatar_url} />
                            <AvatarFallback className="text-[8px]">
                              {initials(selectedReport.reporter?.display_name)}
                            </AvatarFallback>
                          </Avatar>
                          <span className="text-sm">{selectedReport.reporter?.display_name || "Inconnu"}</span>
                        </div>
                      </div>

                      {/* Reason + details */}
                      <div>
                        <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1">Raison</p>
                        <Badge className={REASON_COLORS[selectedReport.reason] || REASON_COLORS.other}>
                          {REASON_LABELS[selectedReport.reason] || selectedReport.reason}
                        </Badge>
                        {selectedReport.details && (
                          <p className="text-sm mt-2 p-2 rounded-lg bg-muted/30 border border-border">
                            {selectedReport.details}
                          </p>
                        )}
                      </div>

                      {/* Target content */}
                      <div>
                        <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1">
                          Contenu signalé ({TYPE_LABELS[selectedReport.target_type]})
                        </p>
                        {selectedReport.target ? (
                          <div className="p-2 rounded-lg bg-muted/30 border border-border text-sm">
                            {selectedReport.target_type === "comment" && (
                              <p>{selectedReport.target.text || selectedReport.target.content || "—"}</p>
                            )}
                            {selectedReport.target_type === "activity" && (
                              <p>{selectedReport.target.text || selectedReport.target.content || selectedReport.target.activity_type || "—"}</p>
                            )}
                            {selectedReport.target_type === "user" && (
                              <div className="flex items-center gap-2">
                                <Avatar className="w-8 h-8">
                                  <AvatarImage src={selectedReport.target.avatar_url} />
                                  <AvatarFallback>{initials(selectedReport.target.display_name)}</AvatarFallback>
                                </Avatar>
                                <div>
                                  <p className="font-medium">{selectedReport.target.display_name}</p>
                                  <p className="text-xs text-muted-foreground">@{selectedReport.target.username}</p>
                                </div>
                              </div>
                            )}
                            {selectedReport.target_type === "group" && (
                              <p>{selectedReport.target.name || "Groupe"}</p>
                            )}
                          </div>
                        ) : (
                          <p className="text-sm text-muted-foreground italic">Contenu supprimé ou introuvable</p>
                        )}
                      </div>

                      {/* Previous reports */}
                      {selectedReport.previous_reports_count > 0 && (
                        <div className="flex items-center gap-2 p-2 rounded-lg bg-[#E48C75]/10 border border-[#E48C75]/20">
                          <AlertTriangle className="w-4 h-4 text-[#E48C75]" />
                          <span className="text-xs text-[#E48C75]">
                            {selectedReport.previous_reports_count} signalement{selectedReport.previous_reports_count > 1 ? "s" : ""} précédent{selectedReport.previous_reports_count > 1 ? "s" : ""}
                          </span>
                        </div>
                      )}

                      {/* Admin note */}
                      {selectedReport.status === "pending" && (
                        <div>
                          <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1">Note admin</p>
                          <Textarea
                            value={adminNote}
                            onChange={(e) => setAdminNote(e.target.value)}
                            placeholder="Note interne (optionnel)"
                            rows={2}
                            className="text-sm rounded-lg"
                            maxLength={500}
                          />
                        </div>
                      )}

                      {/* Actions */}
                      {selectedReport.status === "pending" && (
                        <div className="space-y-1.5 pt-2 border-t border-border">
                          <Button
                            variant="outline"
                            size="sm"
                            className="w-full justify-start gap-2 text-xs rounded-lg"
                            onClick={() => handleAction("dismiss")}
                            disabled={actionLoading}
                          >
                            <XCircle className="w-3.5 h-3.5 text-muted-foreground" />
                            Rejeter (faux signalement)
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            className="w-full justify-start gap-2 text-xs rounded-lg"
                            onClick={() => handleAction("warn")}
                            disabled={actionLoading}
                          >
                            <MessageCircle className="w-3.5 h-3.5 text-[#F5A623]" />
                            Avertir l'utilisateur
                          </Button>
                          {(selectedReport.target_type === "comment" || selectedReport.target_type === "activity") && (
                            <Button
                              variant="outline"
                              size="sm"
                              className="w-full justify-start gap-2 text-xs rounded-lg text-[#E48C75] hover:text-[#E48C75] hover:border-[#E48C75]/30"
                              onClick={() => handleAction("remove_content")}
                              disabled={actionLoading}
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                              Supprimer le contenu
                            </Button>
                          )}
                          <Button
                            variant="outline"
                            size="sm"
                            className="w-full justify-start gap-2 text-xs rounded-lg text-red-500 hover:text-red-500 hover:border-red-500/30"
                            onClick={() => handleAction("suspend_user")}
                            disabled={actionLoading}
                          >
                            <UserX className="w-3.5 h-3.5" />
                            Suspendre l'utilisateur
                          </Button>
                        </div>
                      )}

                      {/* Already resolved */}
                      {selectedReport.status !== "pending" && selectedReport.action_taken && (
                        <div className="p-3 rounded-lg bg-muted/30 border border-border">
                          <p className="text-xs text-muted-foreground">
                            Action : <strong>{selectedReport.action_taken}</strong>
                          </p>
                          {selectedReport.admin_note && (
                            <p className="text-xs mt-1">{selectedReport.admin_note}</p>
                          )}
                          <p className="text-[10px] text-muted-foreground/60 mt-1 tabular-nums">
                            {new Date(selectedReport.resolved_at).toLocaleString("fr-FR")}
                          </p>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ) : (
                  <Card className="p-8 text-center rounded-xl">
                    <Eye className="w-8 h-8 text-muted-foreground/30 mx-auto mb-2" />
                    <p className="text-sm text-muted-foreground">
                      Sélectionne un signalement pour voir les détails
                    </p>
                  </Card>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
