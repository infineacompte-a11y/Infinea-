"""
InFinea — Prometheus Metrics Service.

Exposes application metrics at /metrics for Prometheus scraping.
Designed for Grafana Cloud free tier (10k series, 14d retention).

Metrics exported:
- HTTP request latency (histogram, by endpoint + method + status)
- HTTP request count (counter, by endpoint + method + status)
- LLM call latency (histogram, by model + caller)
- LLM call count (counter, by model + caller + success)
- LLM token usage (counter, by model + type)
- LLM cost (counter, by model)
- Circuit breaker state (gauge, by provider)
- Active users (gauge, daily/weekly)
- Feature computation duration (histogram)
- Memory extraction count (counter)
- Background job status (gauge)

Benchmark: Stripe (p99 per endpoint), Netflix (circuit breaker),
Spotify (business metrics alongside infra metrics).
"""

import time
import logging
from prometheus_client import (
    Counter, Histogram, Gauge, Info,
    generate_latest, CONTENT_TYPE_LATEST,
    CollectorRegistry, REGISTRY,
)

logger = logging.getLogger("infinea")


# ═══════════════════════════════════════════════════════════════════════════
# HTTP METRICS
# ═══════════════════════════════════════════════════════════════════════════

HTTP_REQUEST_DURATION = Histogram(
    "infinea_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint", "status_code"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
)

HTTP_REQUEST_COUNT = Counter(
    "infinea_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)


# ═══════════════════════════════════════════════════════════════════════════
# LLM METRICS
# ═══════════════════════════════════════════════════════════════════════════

LLM_CALL_DURATION = Histogram(
    "infinea_llm_call_duration_seconds",
    "LLM API call latency in seconds",
    ["model", "caller"],
    buckets=[0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 15.0, 30.0],
)

LLM_CALL_COUNT = Counter(
    "infinea_llm_calls_total",
    "Total LLM API calls",
    ["model", "caller", "success"],
)

LLM_TOKENS = Counter(
    "infinea_llm_tokens_total",
    "Total LLM tokens consumed",
    ["model", "token_type"],  # token_type: input, output, cache_read, cache_write
)

LLM_COST_USD = Counter(
    "infinea_llm_cost_usd_total",
    "Total estimated LLM cost in USD",
    ["model"],
)

LLM_RETRIES = Counter(
    "infinea_llm_retries_total",
    "Total LLM call retries",
    ["model", "caller"],
)


# ═══════════════════════════════════════════════════════════════════════════
# CIRCUIT BREAKER METRICS
# ═══════════════════════════════════════════════════════════════════════════

CIRCUIT_BREAKER_STATE = Gauge(
    "infinea_circuit_breaker_state",
    "Circuit breaker state (0=closed, 1=open, 2=half_open)",
    ["provider"],
)

CIRCUIT_BREAKER_FAILURES = Counter(
    "infinea_circuit_breaker_failures_total",
    "Total circuit breaker recorded failures",
    ["provider"],
)


# ═══════════════════════════════════════════════════════════════════════════
# BUSINESS METRICS
# ═══════════════════════════════════════════════════════════════════════════

ACTIVE_USERS_DAILY = Gauge(
    "infinea_active_users_daily",
    "Number of daily active users (updated periodically)",
)

ACTIVE_USERS_WEEKLY = Gauge(
    "infinea_active_users_weekly",
    "Number of weekly active users (updated periodically)",
)

MEMORY_EXTRACTIONS = Counter(
    "infinea_memory_extractions_total",
    "Total AI memory extractions",
    ["category"],  # preference, goal, constraint, insight, struggle
)

COACHING_SESSIONS = Counter(
    "infinea_coaching_sessions_total",
    "Total coaching interactions",
    ["endpoint"],  # coach_dashboard, coach_chat, debrief
)


# ═══════════════════════════════════════════════════════════════════════════
# BACKGROUND JOB METRICS
# ═══════════════════════════════════════════════════════════════════════════

FEATURE_COMPUTATION_DURATION = Histogram(
    "infinea_feature_computation_duration_seconds",
    "Feature computation batch duration",
    buckets=[1, 5, 10, 30, 60, 120, 300, 600],
)

FEATURE_COMPUTATION_USERS = Gauge(
    "infinea_feature_computation_users_processed",
    "Number of users processed in last feature computation",
)

BACKGROUND_JOB_STATUS = Gauge(
    "infinea_background_job_last_success_timestamp",
    "Timestamp of last successful background job run",
    ["job_name"],  # feature_computation, memory_cleanup, collective_patterns
)


# ═══════════════════════════════════════════════════════════════════════════
# APP INFO
# ═══════════════════════════════════════════════════════════════════════════

APP_INFO = Info(
    "infinea_app",
    "Application metadata",
)
APP_INFO.info({
    "name": "infinea",
    "component": "backend",
    "framework": "fastapi",
})


# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS (called from other services)
# ═══════════════════════════════════════════════════════════════════════════

def record_http_request(method: str, endpoint: str, status_code: int, duration: float):
    """Record an HTTP request metric. Called from middleware."""
    # Normalize endpoint to reduce cardinality (strip IDs)
    normalized = _normalize_endpoint(endpoint)
    HTTP_REQUEST_DURATION.labels(method=method, endpoint=normalized, status_code=str(status_code)).observe(duration)
    HTTP_REQUEST_COUNT.labels(method=method, endpoint=normalized, status_code=str(status_code)).inc()


def record_llm_call(model: str, caller: str, success: bool, duration: float,
                     input_tokens: int = 0, output_tokens: int = 0,
                     cache_read: int = 0, cache_write: int = 0,
                     cost_usd: float = 0, retries: int = 0):
    """Record an LLM call metric. Called from llm_provider."""
    LLM_CALL_DURATION.labels(model=model, caller=caller).observe(duration)
    LLM_CALL_COUNT.labels(model=model, caller=caller, success=str(success)).inc()

    if input_tokens:
        LLM_TOKENS.labels(model=model, token_type="input").inc(input_tokens)
    if output_tokens:
        LLM_TOKENS.labels(model=model, token_type="output").inc(output_tokens)
    if cache_read:
        LLM_TOKENS.labels(model=model, token_type="cache_read").inc(cache_read)
    if cache_write:
        LLM_TOKENS.labels(model=model, token_type="cache_write").inc(cache_write)
    if cost_usd:
        LLM_COST_USD.labels(model=model).inc(cost_usd)
    if retries:
        LLM_RETRIES.labels(model=model, caller=caller).inc(retries)


def record_circuit_breaker_state(provider: str, state: str, failures: int = 0):
    """Update circuit breaker gauge. Called from llm_provider."""
    state_map = {"closed": 0, "open": 1, "half_open": 2}
    CIRCUIT_BREAKER_STATE.labels(provider=provider).set(state_map.get(state, 0))


def get_metrics_response():
    """Generate Prometheus metrics text for /metrics endpoint."""
    return generate_latest(REGISTRY), CONTENT_TYPE_LATEST


def _normalize_endpoint(path: str) -> str:
    """Normalize endpoint paths to reduce label cardinality.
    /api/objectives/obj_abc123/skills → /api/objectives/{id}/skills
    """
    parts = path.strip("/").split("/")
    normalized = []
    for part in parts:
        # Replace UUIDs, ObjectIDs, and custom IDs with {id}
        if (len(part) >= 10 and any(c.isdigit() for c in part)) or part.startswith(("obj_", "action_", "user_", "sess_", "notif_", "custom_")):
            normalized.append("{id}")
        else:
            normalized.append(part)
    return "/" + "/".join(normalized)
