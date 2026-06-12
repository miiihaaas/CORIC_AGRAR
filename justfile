# CORIC_AGRAR — justfile (task runner)
# Pokrenuti `just --list` za listu svih recepata.

# Windows: koristi PowerShell umesto default-a `sh` (koji nije prisutan na Windows-u).
# Direktiva važi samo na Windows-u; Linux/Mac koriste default sh.
set windows-shell := ["powershell.exe", "-c"]

# Default recept — prikazuje listu kad se pokrene `just` bez argumenata
default:
    @just --list

# Pokrece dev stack (Django + PostgreSQL) kroz Docker Compose
dev:
    docker compose -f compose/local.yml up

# Builduje Django image (potrebno samo kad se Dockerfile menja ili posle prvog clone-a)
dev-build:
    docker compose -f compose/local.yml build

# Stop dev stack (ČUVA postgres_data volume; koristi `down -v` ručno ako baš želiš da brišeš data)
dev-down:
    docker compose -f compose/local.yml down

# Tail logs (follow mode; Ctrl+C izlazi)
dev-logs:
    docker compose -f compose/local.yml logs -f

# Otvori bash shell u django kontejneru (za debug, manage.py shell, itd.)
# dev-shell zavisi od bash u runtime image-u (python:3.13-slim ima bash); ako future story prebaci na alpine, koristi sh.
dev-shell:
    docker compose -f compose/local.yml exec django /bin/bash

# Wrapper za manage.py komande u kontejneru
# Primer: just dev-manage createsuperuser
dev-manage *ARGS:
    docker compose -f compose/local.yml exec django python manage.py {{ARGS}}

# Pokrece test suite (kroz Docker — libmagic + poppler-utils system deps NISU dostupni na Windows host-u)
# Per Story 2.3 Decision MP-D6: konzistentan dev UX, izbegava libmagic SEGFAULT na Windows.
# Primer sa argumentima: just test apps/media_pipeline/tests/
test *ARGS:
    docker compose -f compose/local.yml run --rm django uv run pytest {{ARGS}}

# Pokrece ISKLJUCIVO Playwright E2E suite (Story 9.8) headless protiv pokrenute, seed-ovane app.
# `just test` (sa `-m 'not e2e'` u pyproject addopts) NE povlaci E2E — dve suite su razdvojene.
#
# Prereqs (pre `just e2e`):
#   1. `just dev` — Django + Postgres up (compose/local.yml).
#   2. `just dev-manage seed_e2e_data --force` — 9-7 seed + AC12 listing-visibility + galerija + UJ-3 cleanup.
#   3. `playwright install --with-deps chromium` — browser binarije (unutar django kontejnera prvi put).
#   4. DJANGO_SUPERUSER_PASSWORD u env-u (NIKAD hardkodovan — AC11); E2E_BASE_URL default http://localhost:8000.
#
# Headed lokalni debug: prefiksuj PWDEBUG=1 (npr. `PWDEBUG=1 just e2e`) za Playwright inspector.
# Primer sa argumentima: just e2e -k marko
e2e *ARGS:
    docker compose -f compose/local.yml run --rm django uv run pytest -m e2e tests/e2e/ {{ARGS}}

# Pokrece ISKLJUCIVO axe a11y audit suite (Story 9.9) protiv pokrenute, seed-ovane app.
# `just test` (-m 'not e2e and not a11y') NE povlaci a11y; tri suite razdvojene (SM-D8).
#
# Prereqs isti kao `just e2e` (dev up + seed_e2e_data --force + playwright chromium +
# DJANGO_SUPERUSER_PASSWORD u env-u) + axe runner dep (axe-playwright-python).
# Primer sa argumentima: just a11y --collect-only
a11y *ARGS:
    docker compose -f compose/local.yml run --rm django uv run pytest -m a11y tests/e2e/ {{ARGS}}

# Lint (read-only check, ne menja kod)
lint:
    uv run ruff check .
    uv run djade --check templates/ || echo "djade: templates/ folder ne postoji jos (OK za Story 1.1)"

# Apply DB migrations
migrate:
    uv run python manage.py migrate

# i18n message handling
messages:
    uv run python manage.py makemessages -a
    uv run python manage.py compilemessages

# Setup pre-commit hooks (Story 1.9 — jednokratno posle klon-a)
precommit-install:
    uv run pre-commit install

# ── Production stack (Story 9.1) ─────────────────────────────────────────────
# Validira production.yml schema (NE diže kontejnere)
prod-config:
    docker compose -f compose/production.yml config

# Builduje prod image-ove (django --no-dev target + nginx)
prod-build:
    docker compose -f compose/production.yml build

# Diže prod stack (postgres + django/Gunicorn + nginx) — detached
prod-up:
    docker compose -f compose/production.yml up -d

# Stop prod stack (ČUVA volume-e; koristi `down -v` ručno za brisanje data)
prod-down:
    docker compose -f compose/production.yml down
