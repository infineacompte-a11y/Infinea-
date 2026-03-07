import React from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Loader2,
  Settings,
  ChevronRight,
  Lock,
  Wifi,
  WifiOff,
} from "lucide-react";

const statusConfig = {
  connected: {
    label: "Connecté",
    color: "bg-emerald-500",
    badgeClass: "bg-emerald-500/20 text-emerald-500 border-emerald-500/30",
    Icon: CheckCircle2,
  },
  error: {
    label: "Erreur",
    color: "bg-red-500",
    badgeClass: "bg-red-500/20 text-red-500 border-red-500/30",
    Icon: AlertCircle,
  },
  disconnected: {
    label: "Non connecté",
    color: "bg-zinc-500",
    badgeClass: "bg-zinc-500/20 text-zinc-400 border-zinc-500/30",
    Icon: WifiOff,
  },
  syncing: {
    label: "Synchronisation...",
    color: "bg-blue-500",
    badgeClass: "bg-blue-500/20 text-blue-500 border-blue-500/30",
    Icon: Loader2,
  },
};

const colorClasses = {
  blue: { bg: "bg-blue-500/10", text: "text-blue-500", border: "border-blue-500/30" },
  gray: { bg: "bg-zinc-500/10", text: "text-zinc-400", border: "border-zinc-500/30" },
  red: { bg: "bg-red-500/10", text: "text-red-500", border: "border-red-500/30" },
  purple: { bg: "bg-purple-500/10", text: "text-purple-500", border: "border-purple-500/30" },
  orange: { bg: "bg-orange-500/10", text: "text-orange-500", border: "border-orange-500/30" },
};

export default function IntegrationCard({
  service,
  name,
  description,
  icon: Icon,
  color = "blue",
  status = "disconnected",
  accountName,
  connectedAt,
  lastSync,
  lastError,
  isSyncing = false,
  isLimitReached = false,
  onConnect,
  onDisconnect,
  onSync,
  onSettings,
  onTest,
}) {
  const colors = colorClasses[color] || colorClasses.blue;
  const currentStatus = isSyncing ? "syncing" : status;
  const statusInfo = statusConfig[currentStatus] || statusConfig.disconnected;
  const StatusIcon = statusInfo.Icon;
  const isConnected = status === "connected" || status === "error";

  return (
    <Card
      className={`transition-all ${isConnected ? colors.border + " border" : "hover:border-primary/50"}`}
      data-testid={`integration-card-${service}`}
    >
      <CardContent className="p-4">
        <div className="flex items-start gap-4">
          {/* Icon */}
          <div className={`w-12 h-12 rounded-xl ${colors.bg} flex items-center justify-center shrink-0 relative`}>
            <Icon className={`w-6 h-6 ${colors.text}`} />
            {/* Status dot */}
            <div className={`absolute -top-1 -right-1 w-3.5 h-3.5 rounded-full ${statusInfo.color} border-2 border-background`} />
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="font-heading font-semibold">{name}</h3>
              <Badge className={`text-xs ${statusInfo.badgeClass}`}>
                <StatusIcon className={`w-3 h-3 mr-1 ${currentStatus === "syncing" ? "animate-spin" : ""}`} />
                {statusInfo.label}
              </Badge>
            </div>

            {isConnected ? (
              <div className="space-y-1">
                {accountName && (
                  <p className="text-sm text-muted-foreground">{accountName}</p>
                )}
                <p className="text-xs text-muted-foreground">
                  Connecté le {connectedAt ? new Date(connectedAt).toLocaleDateString("fr-FR") : "—"}
                  {lastSync && (
                    <> · Dernière sync : {new Date(lastSync).toLocaleString("fr-FR", { hour: "2-digit", minute: "2-digit", day: "numeric", month: "short" })}</>
                  )}
                </p>
                {lastError && (
                  <p className="text-xs text-red-400 flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" />
                    {lastError}
                  </p>
                )}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground mb-3">{description}</p>
            )}
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2 shrink-0">
            {isConnected ? (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onSync?.(service)}
                  disabled={isSyncing}
                  data-testid={`sync-${service}-btn`}
                >
                  {isSyncing ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <RefreshCw className="w-4 h-4" />
                  )}
                </Button>
                {onTest && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onTest?.(service)}
                    data-testid={`test-${service}-btn`}
                  >
                    <Wifi className="w-4 h-4" />
                  </Button>
                )}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onSettings?.(service)}
                >
                  <Settings className="w-4 h-4" />
                </Button>
              </>
            ) : isLimitReached ? (
              <Button size="sm" variant="outline" className="text-amber-500 border-amber-500/30" disabled>
                <Lock className="w-4 h-4 mr-2" />
                Premium
              </Button>
            ) : (
              <Button
                size="sm"
                onClick={() => onConnect?.(service)}
                data-testid={`connect-${service}-btn`}
              >
                Connecter
                <ChevronRight className="w-4 h-4 ml-1" />
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
