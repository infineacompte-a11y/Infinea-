"""
InFinea — Alert Service.

Sends structured alerts to Slack via Incoming Webhooks.
Designed for ops monitoring — not user-facing notifications.

Alert types:
- LLM circuit breaker opened
- LLM error rate spike (> 10% in 5 min)
- Feature computation failure
- Slow API response (> 10s)
- High memory extraction failure rate
- Background job stale (missed scheduled run)

Config: SLACK_ALERTS_WEBHOOK_URL env var.
Free: Slack Incoming Webhooks are free for any workspace.

Benchmark: PagerDuty (severity levels), Stripe (structured alerts),
Netflix (circuit breaker alerts with context).
"""

import os
import logging
from datetime import datetime, timezone
from enum import Enum

import httpx

logger = logging.getLogger("infinea")

SLACK_WEBHOOK_URL = os.environ.get("SLACK_ALERTS_WEBHOOK_URL", "")

# Dedup: don't send same alert more than once per cooldown period
_alert_cooldowns: dict[str, float] = {}
COOLDOWN_SECONDS = 300  # 5 min between identical alerts


class AlertSeverity(str, Enum):
    INFO = "info"          # FYI, no action needed
    WARNING = "warning"    # Attention needed, not urgent
    CRITICAL = "critical"  # Immediate action required


# Severity → Slack color
_SEVERITY_COLORS = {
    AlertSeverity.INFO: "#36a64f",      # Green
    AlertSeverity.WARNING: "#ff9900",   # Orange
    AlertSeverity.CRITICAL: "#ff0000",  # Red
}

_SEVERITY_EMOJI = {
    AlertSeverity.INFO: "ℹ️",
    AlertSeverity.WARNING: "⚠️",
    AlertSeverity.CRITICAL: "🚨",
}


async def send_alert(
    title: str,
    message: str,
    severity: AlertSeverity = AlertSeverity.WARNING,
    context: dict = None,
    alert_key: str = None,
) -> bool:
    """Send an alert to Slack. Returns True if sent, False if suppressed or failed.

    Args:
        title: Short alert title (e.g., "Circuit Breaker Opened")
        message: Detailed message
        severity: INFO / WARNING / CRITICAL
        context: Optional dict of key-value pairs for context
        alert_key: Dedup key — if same key sent within COOLDOWN_SECONDS, suppressed
    """
    if not SLACK_WEBHOOK_URL:
        logger.debug(f"Alert suppressed (no webhook): {title}")
        return False

    # Dedup check
    import time
    if alert_key:
        now = time.monotonic()
        last_sent = _alert_cooldowns.get(alert_key, 0)
        if now - last_sent < COOLDOWN_SECONDS:
            return False
        _alert_cooldowns[alert_key] = now

    # Build Slack payload (Block Kit format)
    color = _SEVERITY_COLORS.get(severity, "#cccccc")
    emoji = _SEVERITY_EMOJI.get(severity, "")
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    fields = []
    if context:
        for k, v in context.items():
            fields.append({"title": k, "value": str(v), "short": True})

    payload = {
        "attachments": [{
            "color": color,
            "blocks": [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": f"{emoji} {title}"}
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": message}
                },
            ],
            "fields": fields,
            "footer": f"InFinea Alerts • {timestamp}",
        }]
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(SLACK_WEBHOOK_URL, json=payload)
            if resp.status_code == 200:
                return True
            logger.warning(f"Slack alert failed ({resp.status_code}): {resp.text[:100]}")
    except Exception as e:
        logger.debug(f"Slack alert error: {e}")

    return False


# ═══════════════════════════════════════════════════════════════════════════
# PRE-BUILT ALERT FUNCTIONS (called from other services)
# ═══════════════════════════════════════════════════════════════════════════

async def alert_circuit_breaker_opened(provider: str, failures: int):
    """Alert when circuit breaker trips to OPEN state."""
    await send_alert(
        title=f"Circuit Breaker OPEN — {provider}",
        message=(
            f"Le circuit breaker pour *{provider}* est passé en état OPEN "
            f"après {failures} échecs consécutifs.\n"
            f"Les appels LLM vers {provider} sont *bloqués* pendant 30s."
        ),
        severity=AlertSeverity.CRITICAL,
        context={"Provider": provider, "Failures": failures},
        alert_key=f"cb_open_{provider}",
    )


async def alert_circuit_breaker_recovered(provider: str):
    """Alert when circuit breaker recovers to CLOSED state."""
    await send_alert(
        title=f"Circuit Breaker RECOVERED — {provider}",
        message=f"Le circuit breaker pour *{provider}* est revenu à l'état CLOSED. Les appels LLM reprennent normalement.",
        severity=AlertSeverity.INFO,
        context={"Provider": provider},
        alert_key=f"cb_recovered_{provider}",
    )


async def alert_slow_request(method: str, path: str, duration_ms: float, request_id: str = ""):
    """Alert on very slow API response (> 10s)."""
    await send_alert(
        title="Slow API Request",
        message=f"`{method} {path}` a pris *{duration_ms:.0f}ms*.",
        severity=AlertSeverity.WARNING,
        context={"Method": method, "Path": path, "Duration": f"{duration_ms:.0f}ms", "Request ID": request_id},
        alert_key=f"slow_{path}",
    )


async def alert_background_job_failed(job_name: str, error: str):
    """Alert when a background job fails."""
    await send_alert(
        title=f"Background Job Failed — {job_name}",
        message=f"Le job *{job_name}* a échoué.\nErreur: `{error[:200]}`",
        severity=AlertSeverity.CRITICAL,
        context={"Job": job_name},
        alert_key=f"job_failed_{job_name}",
    )


async def alert_high_error_rate(endpoint: str, error_rate: float, window_minutes: int = 5):
    """Alert when an endpoint's error rate exceeds threshold."""
    await send_alert(
        title=f"High Error Rate — {endpoint}",
        message=(
            f"Le taux d'erreur pour *{endpoint}* est de *{error_rate:.0%}* "
            f"sur les {window_minutes} dernières minutes."
        ),
        severity=AlertSeverity.WARNING if error_rate < 0.3 else AlertSeverity.CRITICAL,
        context={"Endpoint": endpoint, "Error Rate": f"{error_rate:.0%}", "Window": f"{window_minutes}min"},
        alert_key=f"error_rate_{endpoint}",
    )
