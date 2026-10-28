# ── Stage 1: Builder ──────────────────────────────────────────────────────────
# Install dependencies in an isolated layer so they can be cached
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --target=/app/deps -r requirements.txt


# ── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# Runtime system deps (libpq for psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /app/deps /usr/local/lib/python3.12/site-packages

# Copy application code
COPY . .

# Non-root user for security
RUN addgroup --system agen && adduser --system --ingroup agen agen
RUN mkdir -p /app/.tts_cache
RUN chown -R agen:agen /app
USER agen

# Expose port
EXPOSE 8000

# Startup: run migrations then start server
# (start.sh is the entrypoint — see scripts/start.sh)
CMD ["sh", "scripts/start.sh"]
