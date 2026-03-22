# ============================================================
# InFinea Backend — Production Dockerfile
# Multi-stage build, non-root, health-checked, signal-safe
# ============================================================

# ---------- Stage 1: Builder ----------
FROM python:3.12-slim AS builder

WORKDIR /build

# System deps for compiled packages (bcrypt, cryptography, motor)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libffi-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---------- Stage 2: Production ----------
FROM python:3.12-slim AS production

# Security: non-root user
RUN groupadd -r infinea && useradd -r -g infinea -d /app -s /sbin/nologin infinea

WORKDIR /app

# Copy only compiled dependencies from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Remove dev/test files that slipped past .dockerignore
RUN rm -rf tests/ __pycache__/ .pytest_cache/ .mypy_cache/

# Ownership
RUN chown -R infinea:infinea /app

USER infinea

# Expose port
EXPOSE 8001

# Health check — lightweight, no external deps
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/api/health')" || exit 1

# Uvicorn with proper signal handling for graceful shutdown
# --workers scaled via docker-compose or orchestrator, not hardcoded
CMD ["python", "-m", "uvicorn", "server:app", \
     "--host", "0.0.0.0", \
     "--port", "8001", \
     "--workers", "1", \
     "--log-level", "info", \
     "--proxy-headers", \
     "--forwarded-allow-ips", "*"]
