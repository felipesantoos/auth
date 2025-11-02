# Multi-stage build for Auth System API

# ============================================
# Builder stage - Install dependencies
# ============================================
FROM python:3.12-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# ============================================
# Base stage - Common configuration
# ============================================
FROM python:3.12-slim AS base

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user (SECURITY: Don't run as root)
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app && \
    chown -R appuser:appuser /app

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code with correct ownership
COPY --chown=appuser:appuser . .

# Copy and make entrypoint executable
COPY --chown=appuser:appuser scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose port
EXPOSE 8080

# Use entrypoint for migrations
ENTRYPOINT ["/entrypoint.sh"]


# ============================================
# Development stage
# ============================================
FROM base AS development

ENV PYTHONUNBUFFERED=1
ENV DEBUG=true
ENV LOG_LEVEL=debug

# Switch to non-root user (SECURITY)
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run with hot reload
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]


# ============================================
# Production stage
# ============================================
FROM base AS production

ENV PYTHONUNBUFFERED=1
ENV DEBUG=false
ENV LOG_LEVEL=warning

# Switch to non-root user (SECURITY: inherited from base stage)
USER appuser

# Health check (using curl for reliability)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Use multiple workers for production
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "4"]

