#!/usr/bin/env bash
# CORIC_AGRAR — Daily DB backup (Story 9.5, AC1/AC2/AC4/AC8/AC9/AC10).
#
# Tok: pg_dump (plain SQL, PROTIV `postgres` servisa kroz `docker compose exec -T`)
#   -> temp fajl -> gzip -> NON-EMPTY ASSERT (SM-D7/HIGH-1) -> restic encrypt push
#   kroz pinovan restic/restic image (SM-D12) -> retention forget 7/4/3 --prune
#   (GATE-ovan na uspeh push-a, SM-D1/G-17) -> cleanup temp fajla.
#
# Daily 03:00 UTC (cron, vidi ops/backup/crontab). Tihi backup-fail je NAJGORI
# ishod (SM-D7) → fail-loud svuda; trap ERR → GlitchTip thin notify (SM-D8).
#
# Naming convention: srpska latinica + engleski identifikatori; bez cirilice.
# Svi creds dolaze kroz env (box `.env`/`${...}`) — 0 literala (SM-D10).

set -euo pipefail

# ── CWD guard (M6, mirror deploy.sh:34-36) ───────────────────────────────────
# Resolvuj repo root iz lokacije skripte (ops/backup/pg_backup.sh -> ../.. = repo root)
# i cd-uj tamo da relativne compose/ops putanje resolve-uju iz cron CWD-a (G-7).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

COMPOSE_FILE="compose/production.yml"
# BACKUP_SCRIPT_NAME se cita u deljenom notify_failure (mora biti set PRE source-a).
BACKUP_SCRIPT_NAME="pg_backup.sh"

# DB credentials iz env-a (compose/production.yml defaults) — NIKAD literali (SM-D2/D10).
POSTGRES_USER="${POSTGRES_USER:-coric}"
POSTGRES_DB="${POSTGRES_DB:-coric_agrar}"
# PGPASSWORD se injektuje u KONTEJNER env (NE host argv) kroz `exec -e` (vidi nize).
# Prod postgres:16-alpine je scram-sha-256 — bez PGPASSWORD-a pg_dump baca auth error
# (POSTGRES_PASSWORD u kontejneru NIJE automatski PGPASSWORD za pg_dump). Prazna default
# vrednost dozvoljava lokalni trust-auth smoke; prod injektuje pravu vrednost iz box `.env`.
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-}"

# ── Deljeni restic helper (G-14): pre-flight guard + restic_run + init guard ──
# shellcheck source=ops/backup/_restic_common.sh
source "${SCRIPT_DIR}/_restic_common.sh"

# ── GlitchTip thin fail-notify (AC10/SM-D8/G-11) — NE 9.6 Django LOGGING dict ─
# Kanonski `notify_failure` zivi u _restic_common.sh (DRY — REFACTOR de-dup); cita
# `${BACKUP_SCRIPT_NAME}` (set iznad PRE source-a). trap ERR okida notify na non-zero
# exit; DSN/URL kroz env (box `.env`), NIKAD literal. THIN curl (9.6 LOGGING deferred).
trap 'notify_failure' ERR

# ── RESTIC env pre-flight guard (SM-D15/G-21) — PRE init-guard-a ──────────────
restic_preflight

# ── Temp dump fajl (deljen host put) + cleanup trap ──────────────────────────
TMPDIR_BACKUP="$(mktemp -d "${TMPDIR:-/tmp}/coric-pgbackup.XXXXXX")"
DUMP_BASENAME="coric_agrar-$(date -u +%Y%m%dT%H%M%SZ).sql"
TMPFILE="${TMPDIR_BACKUP}/${DUMP_BASENAME}"
cleanup() { rm -rf "${TMPDIR_BACKUP}"; }
trap 'cleanup' EXIT

# ── restic init idempotency guard (AC9/SM-D9/G-4) ────────────────────────────
restic_ensure_repo

# ── pg_dump (plain SQL, NE -Fc — SM-D13) PROTIV postgres servisa (SM-D2/G-2) ──
# `exec -T` (no TTY) je OBAVEZAN za cron; postgres servis NEMA host port.
# `--no-owner --no-privileges` (G-16) za cist restore u svez DB sa drugim role-ovima.
# Dump u temp fajl (NE pipe direktno u restic) → drzi fail-check PRE push-a (SM-D7).
# PGPASSWORD ide kroz `exec -e` u KONTEJNER env (NE na host command line — ne curi u host `ps`).
echo "[BACKUP] pg_dump (plain SQL, --no-owner --no-privileges) -> ${TMPFILE}"
docker compose -f "${COMPOSE_FILE}" exec -T -e PGPASSWORD="${POSTGRES_PASSWORD:-}" postgres \
    pg_dump -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" --no-owner --no-privileges \
    > "${TMPFILE}"

# ── NON-EMPTY DUMP ASSERT (AC8/SM-D7/HIGH-1) — OBAVEZNO PRE restic push-a ─────
# Goli `pipefail` hvata pg_dump≠0 ali NE exit-0-prazan-dump (prazna baza, schema-only
# race). Zato: (1) non-prazan fajl (`test -s`), (2) marker grep da je STVARNI dump.
if ! test -s "${TMPFILE}"; then
    echo "[BACKUP ERROR] pg_dump je proizveo PRAZAN dump (${TMPFILE}) — prekidam PRE restic push-a." >&2
    exit 1
fi
if ! grep -q -- "-- PostgreSQL database dump" "${TMPFILE}"; then
    echo "[BACKUP ERROR] dump ne sadrzi ocekivani marker '-- PostgreSQL database dump' — sumnjiv/skoro-prazan dump; prekidam PRE restic push-a." >&2
    exit 1
fi

# ── gzip temp dump-a (TEK posle asserta) ─────────────────────────────────────
echo "[BACKUP] gzip ${TMPFILE}"
gzip "${TMPFILE}"
GZ_FILE="${TMPFILE}.gz"

# ── restic encrypt push (AC1/AC4/SM-D12) — kroz pinovan restic/restic image ──
# Mount temp dir read-only u restic kontejner; repo/password kroz `-e` env-passthrough
# (helper restic_run). Backend creds (rclone.conf ILI SSH key) UVEK ide kroz
# RESTIC_BACKEND_MOUNTS koji restic_run prepend-uje na SVAKU invokaciju (i forget/init).
echo "[BACKUP] restic backup (encrypted push) ${GZ_FILE}"
RESTIC_EXTRA_MOUNTS="-v ${TMPDIR_BACKUP}:/backup:ro" \
    restic_run backup "/backup/${DUMP_BASENAME}.gz" --tag db

# ── Retention (AC2/SM-D1/G-17) — GATE-ovan na uspeh push-a (set -e iznad) ─────
# TACAN flag-set 7/4/3 --prune; NIKAD flat keep-daily=30 (epics 7/4/3 je SOT, G-5). Dolazi STRUKTURNO
# POSLE non-empty asserta i push-a — niz losih run-ova NE prune-uje poslednji DOBAR snapshot.
echo "[BACKUP] restic forget retention (7 daily / 4 weekly / 3 monthly) + prune"
restic_run forget --keep-daily 7 --keep-weekly 4 --keep-monthly 3 --prune

echo "[BACKUP] pg_backup.sh uspesno zavrsen ($(date -u +%Y-%m-%dT%H:%M:%SZ))."
