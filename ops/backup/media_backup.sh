#!/usr/bin/env bash
# CORIC_AGRAR — Weekly media backup (Story 9.5, AC3/AC4/AC8/AC9/AC10).
#
# restic SNAPSHOT named media volume-a `coric_agrar_production_media` kroz pinovan
# restic/restic image koji mount-uje volume READ-ONLY DIREKTNO u restic kontejner
# (SM-D12/G-9 — named volume NIJE citljiv preko host bind-path-a bez root-a).
# Encrypted, dedup, isti Storage Box backend kao DB backup. WEEKLY (cron, vidi
# ops/backup/crontab). Reconcile project-context „sedmicni rsync" → restic snapshot (SM-D3).
#
# Naming convention: srpska latinica + engleski identifikatori; bez cirilice.
# Svi creds dolaze kroz env (box `.env`/`${...}`) — 0 literala (SM-D10).

set -euo pipefail

# ── CWD guard (M6, mirror deploy.sh:34-36) ───────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

# BACKUP_SCRIPT_NAME se cita u deljenom notify_failure (mora biti set PRE source-a).
BACKUP_SCRIPT_NAME="media_backup.sh"

# Named media volume iz 9.1 (compose/production.yml:203-209).
MEDIA_VOLUME="coric_agrar_production_media"

# ── Deljeni restic helper (G-14): pre-flight guard + restic_run + init guard ──
# shellcheck source=ops/backup/_restic_common.sh
source "${SCRIPT_DIR}/_restic_common.sh"

# ── GlitchTip thin fail-notify (AC10/SM-D8/G-11) — NE 9.6 Django LOGGING dict ─
# Kanonski `notify_failure` zivi u _restic_common.sh (DRY — REFACTOR de-dup); cita
# `${BACKUP_SCRIPT_NAME}` (set iznad PRE source-a). trap ERR okida notify na non-zero exit.
trap 'notify_failure' ERR

# ── RESTIC env pre-flight guard (SM-D15/G-21) — PRE init-guard-a ──────────────
restic_preflight

# ── restic init idempotency guard (AC9/SM-D9/G-4) ────────────────────────────
restic_ensure_repo

# ── restic snapshot media volume-a (AC3/SM-D12/G-9) ──────────────────────────
# `docker run --rm` mount-uje named volume READ-ONLY (`:ro`) DIREKTNO u restic
# kontejner — NE host bind-path (`/var/lib/docker/volumes/...` root-only). Backend
# creds (rclone.conf ILI SSH key) kroz RESTIC_BACKEND_MOUNTS. `:ro` jer backup NE pise u media.
echo "[BACKUP] restic snapshot media volume '${MEDIA_VOLUME}' (read-only)"
# shellcheck disable=SC2086
docker run --rm \
    -v coric_agrar_production_media:/data:ro \
    -e RESTIC_REPOSITORY \
    -e RESTIC_PASSWORD \
    -e RESTIC_PASSWORD_FILE \
    ${RESTIC_BACKEND_MOUNTS:-} \
    "${RESTIC_IMAGE}" backup /data --tag media

# ── Retention (AC2/SM-D1/G-17) — GATE-ovan na uspeh snapshot-a (set -e iznad) ─
# TACAN flag-set 7/4/3 --prune; NIKAD flat keep-daily=30 (epics 7/4/3 je SOT, G-5).
echo "[BACKUP] restic forget retention (7 daily / 4 weekly / 3 monthly) + prune"
restic_run forget --keep-daily 7 --keep-weekly 4 --keep-monthly 3 --prune

echo "[BACKUP] media_backup.sh uspesno zavrsen ($(date -u +%Y-%m-%dT%H:%M:%SZ))."
