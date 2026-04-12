# =============================================================================
# Stage 1 — Builder
# Install dependencies and compile native extensions (asyncpg, Pillow)
# =============================================================================
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build tools needed to compile C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install production dependencies only
COPY requirements-prod.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements-prod.txt


# =============================================================================
# Stage 2 — Runtime
# Clean slim image — only compiled packages and app code
# =============================================================================
FROM python:3.12-slim AS runtime

WORKDIR /app

# Install runtime OS libraries only (no build tools)
# libmagic1  — required by python-magic at runtime
# libpq5     — required by asyncpg/psycopg2 at runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy compiled site-packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY app/ ./app/
COPY migrations/ ./migrations/
COPY alembic.ini .
COPY entrypoint.sh .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Non-root user for security
RUN useradd --no-create-home --shell /bin/false appuser \
    && chown -R appuser:appuser /app
USER appuser

# Cloud Run default port
EXPOSE 8080

# Cloud SQL Unix socket path (for reference):
# /cloudsql/your-gcp-project:us-central1:YOUR_INSTANCE_NAME
# Set DATABASE_URL in Cloud Run env:
# postgresql+asyncpg://USER:PASSWORD@/DATABASE?host=/cloudsql/your-gcp-project:us-central1:YOUR_INSTANCE_NAME

ENTRYPOINT ["./entrypoint.sh"]
