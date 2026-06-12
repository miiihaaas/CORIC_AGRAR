#!/usr/bin/env bash
# CORIC_AGRAR — Rollback na prethodni tag/commit + redeploy (Story 9.2).
#
# Filozofija: git checkout <tag/commit> (NIKAD force-rewrite istorije — AC4),
# pa re-deploy. Migrate-down je SVESTAN/opcioni, NE auto (SM-D3 — data-loss rizik).
#
# Naming convention: srpska latinica + engleski identifikatori; bez cirilice.

set -euo pipefail

# ── CWD guard (M6) ─────────────────────────────────────────────────────────────
# Resolvuj repo root iz lokacije skripte da relativne compose/ops putanje resolve-uju
# bez obzira odakle se skripta poziva. exec deploy.sh ide kroz ${SCRIPT_DIR} (apsolutno).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

COMPOSE_FILE="compose/production.yml"

# Argument $1 = ciljni tag/commit. Ako nije dat, auto-detektuj prethodni tag.
TARGET="${1:-}"
ENVIRONMENT="${2:-production}"

if [[ -z "${TARGET}" ]]; then
    # git describe --tags --abbrev=0 HEAD^ = prethodni anotirani tag pre HEAD-a.
    TARGET="$(git describe --tags --abbrev=0 HEAD^ 2>/dev/null || true)"
fi
if [[ -z "${TARGET}" ]]; then
    echo "Usage: ops/deploy/rollback.sh <tag-ili-commit> [environment]" >&2
    echo "  (auto-detekcija prethodnog tag-a nije uspela — eksplicitno navedi cilj)." >&2
    exit 2
fi

# ── IRREVERSIBLE-MIGRATION WARNING (Task 3.4a/AC11/SM-D3) — GLASNO na stderr ─────
# Auto migrate-down je ISKLJUCEN (data-loss). Ako je tekuci deploy uveo nereverzibilnu
# semu-migraciju, checkout starog koda ka novoj semi = broken state — rucna DBA intervencija.
echo "[ROLLBACK WARNING] Ako je tekuci deploy uveo NEREVERZIBILNU migraciju (drop/rename kolone, destruktivan data-transform)," >&2
echo "  rucna DBA intervencija je OBAVEZNA PRE rollback-a — checkout starog koda ka novoj semi = broken state." >&2
echo "  Auto migrate-down je ISKLJUCEN (data-loss rizik, SM-D3). Potvrdi sema-kompatibilnost ili migriraj rucno." >&2

echo "[ROLLBACK] git checkout ${TARGET}"
git checkout "${TARGET}"

# ── Opcioni/SVESTAN migrate-down (SM-D3) ───────────────────────────────────────
# NAMERNO ZAKOMENTARISANO: NEMA bezuslovnog auto migrate-down (data-loss). Operater
# MORA svesno otkomentarisati + navesti tacne app/target migracije ako je sema-rollback
# stvarno potreban i bezbedan. Default rollback = SAMO kod (git checkout) + redeploy.
#   docker compose -f "${COMPOSE_FILE}" run --rm django python manage.py migrate <app> <prev_migracija>

# ── Re-deploy starog koda (NEMA force-push — AC4) ──────────────────────────────
# Apsolutna putanja kroz ${SCRIPT_DIR} (M6) — radi i kad checkout promeni CWD/dir-strukturu.
echo "[ROLLBACK] re-deploy environment=${ENVIRONMENT}"
exec "${SCRIPT_DIR}/deploy.sh" "${ENVIRONMENT}"
