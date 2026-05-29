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

# Stop dev stack (CHUVA postgres_data volume; koristi `down -v` rucno ako bas zelis da brises data)
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

# Pokrece test suite
test:
    uv run pytest

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
