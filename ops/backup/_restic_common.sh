# shellcheck shell=bash
# CORIC_AGRAR — Deljeni restic helper za backup skripte (Story 9.5, G-14).
#
# Ovo NIJE samostalna skripta — source-uje se iz pg_backup.sh / media_backup.sh /
# restore.sh (`source "${SCRIPT_DIR}/_restic_common.sh"`). Enkapsulira:
#   - RESTIC env pre-flight guard (SM-D15/G-21 — fail-loud na prazan repo/password),
#   - pinovan restic/restic image wrapper kroz `docker run --rm` (SM-D12/G-15),
#   - restic init idempotency guard (SM-D9/G-4 — init SAMO ako repo nedostaje),
#   - retention forget (SM-D1 — 7/4/3 --prune),
#   - thin GlitchTip fail-notify (SM-D8 — curl na env DSN, NE 9.6 LOGGING dict).
#
# Naming convention: srpska latinica + engleski identifikatori; bez cirilice.
# Svi creds dolaze kroz env (box `.env`/`${...}`) — 0 literala (SM-D10).

# ── RESTIC_IMAGE pin (SM-D12/G-15) — NIKAD :latest ────────────────────────────
# Pinovan zvanicni restic/restic image; restic se NE instalira na host. Tacan tag
# potvrdjen kroz Task 1.2 (mirror glitchtip:v6.0 pin-disciplina iz 9.3).
RESTIC_IMAGE="${RESTIC_IMAGE:-restic/restic:0.17.3}"

# ── RESTIC env pre-flight guard (SM-D15/G-21 — ORPHANED-REPO ZAMKA) ───────────
# `set -u` hvata UNSET ali NE postavljen-ali-prazan → eksplicitan ne-prazan check.
# Prazan repo/password rusi `restic snapshots` iz credential razloga → init-guard
# bi pogresno `init`-ovao ORPHANED repo. Zato fail-loud PRE init-guard-a.
restic_preflight() {
    : "${RESTIC_REPOSITORY:?[BACKUP ERROR] RESTIC_REPOSITORY je prazan — odbijam restic operaciju (orphaned-repo zamka, SM-D15).}"
    # Prihvati BILO KOJI od dva password izvora; fail-loud ako su OBA prazna.
    # Ako RESTIC_PASSWORD_FILE nije postavljen, RESTIC_PASSWORD MORA biti ne-prazan (`:?`).
    if [ -z "${RESTIC_PASSWORD_FILE:-}" ]; then
        : "${RESTIC_PASSWORD:?[BACKUP ERROR] I RESTIC_PASSWORD i RESTIC_PASSWORD_FILE su prazni — restic encrypt password je obavezan (SM-D4/SM-D15).}"
    fi
}

# ── restic wrapper kroz pinovan image (SM-D12/G-15) ──────────────────────────
# Sve restic komande (snapshots/init/backup/forget/restore/unlock/check) idu kroz
# `docker run --rm "${RESTIC_IMAGE}"` — restic NIKAD na hostu. Repo/password se
# prosledjuju kroz `-e` env-passthrough.
#
# Backend creds mount (rclone.conf ILI SSH key) ide kroz RESTIC_BACKEND_MOUNTS koji
# wrapper UVEK prepend-uje — tako da SVAKA restic invokacija (snapshots/init/backup/
# forget/restore/unlock/check) vidi backend (inace `forget --prune` i `ensure_repo`
# bi padali jer rclone:/sftp: backend nije dostupan bez creds mount-a). Per-call data
# mount-ovi (temp dump dir, media volume) se DODAJU kroz RESTIC_EXTRA_MOUNTS.
restic_run() {
    # shellcheck disable=SC2086
    docker run --rm \
        -e RESTIC_REPOSITORY \
        -e RESTIC_PASSWORD \
        -e RESTIC_PASSWORD_FILE \
        ${RESTIC_BACKEND_MOUNTS:-} \
        ${RESTIC_EXTRA_MOUNTS:-} \
        "${RESTIC_IMAGE}" "$@"
}

# ── restic init idempotency guard (SM-D9/G-4) ────────────────────────────────
# init SAMO ako repo nedostaje — re-run kad repo postoji NE pada
# („repository master key already exists"). MORA biti pozvan POSLE restic_preflight.
restic_ensure_repo() {
    restic_run snapshots >/dev/null 2>&1 || restic_run init
}

# Retention (SM-D1/G-17 — 7/4/3 --prune) se INLINE-uje u svakoj backup skripti
# (pg_backup.sh / media_backup.sh) odmah posle uspesnog push-a (`set -e` GATE) —
# NE u ovom helperu — da prune-gate ordering ostane vidljiv u samoj skripti.

# ── GlitchTip thin fail-notify (SM-D8/G-11) — NE 9.6 Django LOGGING dict ──────
# trap ERR → notify_failure → curl na env-driven GlitchTip ingest endpoint. THIN.
# DSN/URL kroz env (box `.env`), NIKAD literal. Ako DSN nije postavljen, tiho
# preskaci notify (ne maskira originalni fail — exit kod ostaje non-zero).
notify_failure() {
    local exit_code=$?
    local script_name="${BACKUP_SCRIPT_NAME:-backup}"
    if [ -n "${GLITCHTIP_BACKUP_NOTIFY_DSN:-}" ]; then
        curl -fsS -m 10 -X POST \
            -H "Content-Type: application/json" \
            -d "{\"message\":\"[CORIC backup FAIL] ${script_name} exit ${exit_code}\",\"level\":\"error\"}" \
            "${GLITCHTIP_BACKUP_NOTIFY_DSN}" >/dev/null 2>&1 || true
    fi
    echo "[BACKUP ERROR] ${script_name} nije uspeo (exit ${exit_code})." >&2
    exit "${exit_code}"
}
