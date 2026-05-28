#!/usr/bin/env bash
# CORIC_AGRAR — Django container entrypoint
# Wait for db -> migrate -> exec CMD (runserver)

set -euo pipefail

# -- Wait for PostgreSQL --------------------------------------
# Env vars POSTGRES_* su informational; defaults match compose/local.yml `db` servis
DB_HOST="${POSTGRES_HOST:-db}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_USER="${POSTGRES_USER:-coric}"

echo "[entrypoint] Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT} (user=${DB_USER})..."
until pg_isready -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -q; do
    echo "[entrypoint] db not ready, retrying in 1s..."
    sleep 1
done
echo "[entrypoint] PostgreSQL is ready."

# -- Apply migrations -----------------------------------------
echo "[entrypoint] Running Django migrations..."
python manage.py migrate --noinput

# -- Hand off to CMD (runserver default; gunicorn u prod-u kroz Story 9.1 override) --
echo "[entrypoint] Starting Django: $*"
exec "$@"
