#!/usr/bin/env bash
# CORIC_AGRAR — Production Django start skripta (Gunicorn).
# Story 9.1 / SM-D2: prod NE migrira na startup (project-context:478 — migracije su
# deploy-time, Story 9.2 deploy.sh). Ova skripta SAMO: wait-for-db -> exec gunicorn.
# Lokalni dev koristi entrypoint.sh (koji migrira) — ovaj fajl ga NE menja.
#
# G-1: LF line endings OBAVEZNO (bash u Linux kontejneru ne tolerira CRLF).

set -euo pipefail

# -- Wait for PostgreSQL ----------------------------------------------
# Env vars POSTGRES_* su informational za pg_isready (Docker DNS host "postgres").
DB_HOST="${POSTGRES_HOST:-postgres}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_USER="${POSTGRES_USER:-coric}"

echo "[start] Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT} (user=${DB_USER})..."
until pg_isready -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -q; do
    echo "[start] db not ready, retrying in 1s..."
    sleep 1
done
echo "[start] PostgreSQL is ready."

# -- NE migrate (project-context:478) — migracije su deploy-step (Story 9.2 deploy.sh).

# -- Ako su prosleđeni argumenti (npr. `docker compose run django python manage.py
#    collectstatic`), izvrši njih umesto gunicorn-a. Ovo omogućava deploy/seed
#    komande kroz isti entrypoint (wait-for-db i dalje važi). Bez argumenata →
#    default gunicorn (normalan prod servis).
if [ "$#" -gt 0 ]; then
    echo "[start] Izvršavam prosleđenu komandu: $*"
    exec "$@"
fi

# -- Gunicorn -------------------------------------------------------------------
# Workers formula (Gunicorn zvanična preporuka "How Many Workers?"):
#   workers = 2 * CPU + 1   ->   za 2vCPU = 2*2+1 = 5 workera (epics:1194 "2vCPU VPS").
# Env-parametrizovano kroz WEB_CONCURRENCY (default 5); realan Hetzner CX32 (4vCPU)
# može override-ovati na 9 (OQ-2). Timeout 60s razuman za sync view-ove + upload.
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${WEB_CONCURRENCY:-5}" \
    --timeout "${GUNICORN_TIMEOUT:-60}" \
    --access-logfile - \
    --error-logfile -
