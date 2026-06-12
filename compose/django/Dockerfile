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
# Story 2.3 Decision MP-D6: local dev image uključuje dev dependencies (pytest, ruff, djade)
# kako bi `just test` (Docker-backed) imao pytest dostupan u kontejneru.
# Production override (compose/production.yml) treba ponovo dodati --no-dev kad se uvede.
RUN uv sync --frozen --no-install-project

# ============================================================
# Stage 1b — prod-builder: install SAMO runtime deps (--no-dev) za prod image
# ============================================================
# Story 9.1 (G-4): ZASEBAN prod build put. NE dira dev `builder` stage (linija iznad)
# koji zadržava pytest/ruff/playwright za `just test`. Prod venv je manji (bez dev grupe).
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS prod-builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml uv.lock ./
# --no-dev: izostavlja [dependency-groups].dev (pytest/ruff/playwright/djade).
# gunicorn je u [project].dependencies (runtime) → ulazi u prod venv.
RUN uv sync --frozen --no-install-project --no-dev

# ============================================================
# Stage 2 — runtime: slim image sa system deps + .venv iz builder-a (DEV default)
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

# Story 2.3 Decision MP-D6: kopiramo uv binary u runtime image radi `just test` kompatibilnosti
# (Docker-backed pytest run). Production deploy može preskočiti ovaj korak ako image size matters.
COPY --from=builder /usr/local/bin/uv /usr/local/bin/uv

# Entrypoint script (LF line endings — vidi Gotcha #5)
COPY compose/django/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Prod start skripta (Story 9.1 — wait-for-db + gunicorn, BEZ migrate; LF G-1).
# Kopira se i u dev runtime (bezopasno — koristi se tek u prod kroz entrypoint override).
COPY compose/django/start.sh /start.sh
RUN chmod +x /start.sh

# Application source — u dev-u ce biti override-ovan kroz bind mount,
# ali u standalone image-u (CI, staging, prod) ovaj COPY je SOT.
COPY . /app

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# ============================================================
# Stage 3 — prod: runtime image sa --no-dev venv (Story 9.1)
# ============================================================
# production.yml builduje sa `target: prod`. Identičan runtime-u ALI .venv dolazi
# iz prod-builder stage-a (bez dev grupe). Dev `runtime` target NETAKNUT (G-4).
FROM python:3.13-slim AS prod

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        libmagic1 \
        poppler-utils \
        postgresql-client \
        gettext \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Prod venv (--no-dev) iz prod-builder stage-a.
COPY --from=prod-builder /app/.venv /app/.venv

# Entrypoint + prod start skripta (LF — G-1).
COPY compose/django/entrypoint.sh /entrypoint.sh
COPY compose/django/start.sh /start.sh
RUN chmod +x /entrypoint.sh /start.sh

COPY . /app

EXPOSE 8000

# Prod ENTRYPOINT je `/start.sh` (wait-for-db + gunicorn, BEZ migrate — G-6/G-10).
# production.yml ponavlja `entrypoint: ["/start.sh"]` eksplicitno (defense-in-depth /
# čitljivost) — to NIJE override drugačijeg default-a; ova vrednost se već poklapa.
ENTRYPOINT ["/start.sh"]
