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
  ExternalLink,
} from "lucide-react";

const statusConfig = {
  connected: {
    label: "Connecte",
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
    label: "Non connecte",
    color: "bg-zinc-500",
    badgeClass: "bg-zinc-500/20 text-zinc-400 border-zinc-500/30",
    Icon: WifiOff,
  },
  syncing: {
    label: "Sync...",
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
      className={`transition-all ${isConnected ? colors.border + " border" : "hover:border-primary/50 cursor-pointer"}`}
      data-testid={`integration-card-${service}`}
      onClick={!isConnected && !isLimitReached ? () => onConnect?.(service) : undefined}
    >
      <CardContent className="p-4">
        {/* Top row: icon + name + status */}
        <div className="flex items-center gap-3 mb-2">
          <div className={`w-10 h-10 sm:w-12 sm:h-12 rounded-xl ${colors.bg} flex items-center justify-center shrink-0 relative`}>
            <Icon className={`w-5 h-5 sm:w-6 sm:h-6 ${colors.text}`} />
            <div className={`absolute -top-1 -right-1 w-3 h-3 rounded-full ${statusInfo.color} border-2 border-background`} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="font-heading font-semibold text-sm sm:text-base">{name}</h3>
              <Badge className={`text-[10px] sm:text-xs ${statusInfo.badgeClass}`}>
                <StatusIcon className={`w-3 h-3 mr-1 ${currentStatus === "syncing" ? "animate-spin" : ""}`} />
                {statusInfo.label}
              </Badge>
            </div>
          </div>
          {/* Connect button (disconnected — also triggered by card click) */}
          {!isConnected && !isLimitReached && (
            <Button
              size="sm"
              onClick={(e) => { e.stopPropagation(); onConnect?.(service); }}
              className="shrink-0 rounded-xl gap-1"
              data-testid={`connect-${service}-btn`}
            >
              <span className="hidden sm:inline">Connecter</span>
              <ChevronRight className="w-4 h-4" />
            </Button>
          )}
          {!isConnected && isLimitReached && (
            <Button size="sm" variant="outline" className="text-amber-500 border-amber-500/30 shrink-0" disabled>
              <Lock className="w-4 h-4 sm:mr-1" />
              <span className="hidden sm:inline">Premium</span>
            </Button>
          )}
        </div>

        {/* Content area */}
        {isConnected ? (
          <div className="ml-[52px] sm:ml-[60px] space-y-2">
            <div className="space-y-0.5">
              {accountName && (
                <p className="text-sm text-muted-foreground truncate">{accountName}</p>
              )}
              <p className="text-xs text-muted-foreground">
                Connecte le {connectedAt ? new Date(connectedAt).toLocaleDateString("fr-FR") : "\u2014"}
                {lastSync && (
                  <> &middot; Sync : {new Date(lastSync).toLocaleString("fr-FR", { hour: "2-digit", minute: "2-digit", day: "numeric", month: "short" })}</>
                )}
              </p>
              {lastError && (
                <p className="text-xs text-red-400 flex items-center gap-1">
                  <AlertCircle className="w-3 h-3 shrink-0" />
                  <span className="truncate">{lastError}</span>
                </p>
              )}
            </div>
            {/* Action buttons */}
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => onSync?.(service)}
                disabled={isSyncing}
                className="h-8 gap-1.5 text-xs"
                data-testid={`sync-${service}-btn`}
              >
                {isSyncing ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <RefreshCw className="w-3.5 h-3.5" />
                )}
                <span className="hidden sm:inline">Sync</span>
              </Button>
              {onTest && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onTest?.(service)}
                  className="h-8 gap-1.5 text-xs"
                  data-testid={`test-${service}-btn`}
                >
                  <Wifi className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">Tester</span>
                </Button>
              )}
              <Button
                variant="outline"
                size="sm"
                onClick={() => onSettings?.(service)}
                className="h-8 gap-1.5 text-xs"
              >
                <Settings className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Param.</span>
              </Button>
            </div>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground ml-[52px] sm:ml-[60px]">{description}</p>
        )}
      </CardContent>
    </Card>
  );
}
