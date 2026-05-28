# syntax=docker/dockerfile:1.7

# ============================================================
# Stage 1 — builder: install Python deps to .venv kroz uv
# ============================================================
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

# uv tuning — bytecode compile za brzi import, link mode copy za stabilnost
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Cache-friendly: COPY samo lockfiles, instaliraj deps, tek onda copy source u runtime stage
# Ako se promeni samo source code, ovaj layer je vec cached
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# ============================================================
# Stage 2 — runtime: slim image sa system deps + .venv iz builder-a
# ============================================================
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

# System deps:
#   libmagic1       — python-magic MIME validacija (Story 4.x file uploads)
#   poppler-utils   — pdf2image PDF cover-thumbnail (Story 2.4)
#   postgresql-client — pg_isready za entrypoint wait-for-db
#   gettext         — django compilemessages (Story 1.4+)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        libmagic1 \
        poppler-utils \
        postgresql-client \
        gettext \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Preuzmi venv iz builder stage-a (bez uv binary, bez build artifacts)
COPY --from=builder /app/.venv /app/.venv

# Entrypoint script (LF line endings — vidi Gotcha #5)
COPY compose/django/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Application source — u dev-u ce biti override-ovan kroz bind mount,
# ali u standalone image-u (CI, staging, prod) ovaj COPY je SOT.
COPY . /app

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
