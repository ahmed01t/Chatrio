# ==============================================================================
# Chatrio Backend — Production Dockerfile
# ==============================================================================
# Multi-stage Docker build utilizing Astral `uv` for blazingly fast dependency
# installation, minimal image size, and non-root security.
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build Dependencies (Builder)
# ------------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS builder

# 1. Install Astral uv package manager binary directly from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 2. Set environment variables to optimize Python & uv in container builds
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 3. Copy project definition and lockfile first (optimizes Docker layer caching)
COPY pyproject.toml uv.lock ./

# 4. Install production dependencies into a virtual environment at /app/.venv
RUN uv sync --frozen --no-dev --no-install-project


# ------------------------------------------------------------------------------
# Stage 2: Lean Production Runtime (Final)
# ------------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS runtime

WORKDIR /app

# 1. Environment configuration:
#    - Add the virtual environment binaries (uvicorn, etc.) to system PATH
#    - Set Python unbuffered mode to emit real-time logs directly to Docker
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 2. Create a secure, unprivileged system user (do not run as root)
RUN groupadd -r chatrio && useradd -r -g chatrio -m chatrio

# 3. Copy installed virtual environment from builder stage
COPY --from=builder --chown=chatrio:chatrio /app/.venv /app/.venv

# 4. Copy backend source code & alembic migration files
COPY --chown=chatrio:chatrio app ./app
COPY --chown=chatrio:chatrio alembic.ini ./alembic.ini
COPY --chown=chatrio:chatrio migrations ./migrations

# 5. Switch to unprivileged user
USER chatrio

# 6. Expose FastAPI internal application port
EXPOSE 8000

# 7. Health check: Docker periodically polls /health to confirm backend readiness
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# 8. Start the FastAPI application with Uvicorn ASGI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

