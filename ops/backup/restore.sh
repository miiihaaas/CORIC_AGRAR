#!/usr/bin/env bash
# CORIC_AGRAR — Restore snapshot na LOKAL/TEST (Story 9.5, AC6/AC8).
#
# Restore-uje konkretan restic `<snapshotID>` na lokal + ucitava plain dump kroz
# `gunzip | psql` (NE pg_restore — plain-format par je zakljucan, SM-D13/G-20) u
# RESTORE_TARGET_DB. Za MESECNI restore-test (vidi ops/backup/RESTORE.md).
#
# DATA-LOSS GUARD (SM-D14/G-22): restore-cilj je EKSPLICITAN env var; NIKAD fallback
# na prod `DATABASE_URL` — restore-test ne sme tiho prepisati zivu prod bazu.
#
# Naming convention: srpska latinica + engleski identifikatori; bez cirilice.
# Svi creds dolaze kroz env (box `.env`/`${...}`) — 0 literala (SM-D10).

set -euo pipefail

# ── CWD guard (M6, mirror deploy.sh:34-36) ───────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

# BACKUP_SCRIPT_NAME se cita u deljenom notify_failure (mora biti set PRE source-a).
BACKUP_SCRIPT_NAME="restore.sh"

# ── Argument $1 = <snapshotID>; fail-loud usage ako nedostaje (mirror deploy.sh:42-49) ─
if [ "$#" -lt 1 ] || [ -z "${1:-}" ]; then
    echo "Usage: ops/backup/restore.sh <snapshotID> [restoreDir]" >&2
    exit 2
fi
# RESTORE_TARGET_DB (ILI RESTORE_DB_URL) MORA biti TEST baza (NIKAD prod) — vidi guard nize.
SNAPSHOT_ID="$1"
RESTORE_DIR="${2:-${REPO_ROOT}/ops/backup/.restore}"

# ── RESTORE-TARGET DB guard (AC6/SM-D14/G-22 — DATA-LOSS GUARD) ──────────────
# Eksplicitan restore-cilj iz env-a; NIKAD fallback na prod DATABASE_URL/POSTGRES_*.
# Ako cilj nije bezbedno postavljen → fail-loud (NE pretpostavljaj prod).
: "${RESTORE_TARGET_DB:?[RESTORE ERROR] RESTORE_TARGET_DB nije postavljen — odbijam restore u nepoznatu (moguce prod) bazu (SM-D14). Postavi eksplicitan TEST-DB URL.}"
RESTORE_DB_URL="${RESTORE_DB_URL:-${RESTORE_TARGET_DB}}"

# ── Deljeni restic helper (G-14): pre-flight guard + restic_run + notify_failure ─
# shellcheck source=ops/backup/_restic_common.sh
source "${SCRIPT_DIR}/_restic_common.sh"

# ── GlitchTip thin fail-notify (AC10/SM-D8) — deljeni notify_failure iz helper-a ─
# trap ERR okida notify na non-zero exit (npr. restic restore fail / psql load fail).
trap 'notify_failure' ERR

# ── RESTIC env pre-flight guard (SM-D15/G-21) ────────────────────────────────
restic_preflight

mkdir -p "${RESTORE_DIR}"

# ── restic restore (SM-D12) — kroz pinovan restic/restic image ───────────────
echo "[RESTORE] restic restore snapshot '${SNAPSHOT_ID}' -> ${RESTORE_DIR}"
RESTIC_EXTRA_MOUNTS="-v ${RESTORE_DIR}:/restore" \
    restic_run restore "${SNAPSHOT_ID}" --target /restore

# ── Load plain dump kroz gunzip | psql (SM-D13/G-20 — NIKAD pg_restore) ──────
# Plain `pg_dump | gzip` se restore-uje ISKLJUCIVO kroz `gunzip | psql`. pg_restore
# radi samo sa custom -Fc formatom koji 9.5 NE koristi. Cilj = RESTORE_TARGET_DB (TEST).
# `-print -quit` izlazi cisto posle PRVOG matcha (NEMA pipe → nema SIGPIPE/exit-141
# pod `set -o pipefail` kao kod `find ... | head -n 1`).
DUMP_GZ="$(find "${RESTORE_DIR}" -name '*.sql.gz' -type f -print -quit)"
if [ -z "${DUMP_GZ}" ]; then
    echo "[RESTORE ERROR] Nije nadjen *.sql.gz dump u ${RESTORE_DIR} posle restic restore-a." >&2
    exit 1
fi
echo "[RESTORE] gunzip | psql load '${DUMP_GZ}' -> RESTORE_TARGET_DB (TEST)"
gunzip -c "${DUMP_GZ}" | psql "${RESTORE_DB_URL}"

echo "[RESTORE] restore.sh uspesno zavrsen (snapshot ${SNAPSHOT_ID} -> TEST DB)."
