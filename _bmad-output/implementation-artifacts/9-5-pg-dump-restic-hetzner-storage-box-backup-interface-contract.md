---
story-id: 9-5-pg-dump-restic-hetzner-storage-box-backup
artifact: interface-contract
module: ops/backup (shell skripte + cron + restore runbook; NIJE Django app)
created_by: TEA (RED phase)
created: 2026-06-12
test_file: tests/test_backup_restic.py
---

# Interface Contract — Story 9.5 (pg_dump + restic + Hetzner Storage Box Backup)

Ovaj ugovor definiše **TAČNE** fajlove i ključni sadržaj koji Dev mora isporučiti,
tako da TEA RED testovi (`tests/test_backup_restic.py`) i Dev implementacija dele
isti contract. Svaki red mapira na AC + SM-D odluku iz story-ja. Testovi su
INFRA-VERIFY (import-light: pathlib + re + opcioni `bash -n`); NE importuju Django,
NE pokreću stvarni restic/pg_dump.

## Fajlovi koje Dev MORA isporučiti

| # | Fajl | Tip | Ključni sadržaj (grep-locked) |
|---|------|-----|-------------------------------|
| 1 | `ops/backup/pg_backup.sh` | NEW | `#!/usr/bin/env bash` + `set -euo pipefail`; SCRIPT_DIR/REPO_ROOT; RESTIC env pre-flight guard; `docker compose -f compose/production.yml exec -T postgres pg_dump -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" --no-owner --no-privileges` (plain, NE `-Fc`) → temp fajl; `gzip`; NON-EMPTY guard (`test -s` + size-floor i/ili `grep '-- PostgreSQL database dump'`) PRE restic push-a; restic init idempotency guard (`snapshots ... || ... init`); restic push kroz `docker run --rm ... "${RESTIC_IMAGE}" backup`; `restic forget --keep-daily 7 --keep-weekly 4 --keep-monthly 3 --prune` GATED posle push-a; `trap 'notify_failure' ERR` + `notify_failure()` thin curl na env GlitchTip DSN/URL; svi creds env (`${...}`), 0 literala; LF line-endings. |
| 2 | `ops/backup/media_backup.sh` | NEW | `set -euo pipefail`; RESTIC env pre-flight guard; restic init idempotency guard; `docker run --rm -v coric_agrar_production_media:/data:ro -e RESTIC_REPOSITORY -e RESTIC_PASSWORD_FILE ... "${RESTIC_IMAGE}" backup /data --tag media`; isti retention 7/4/3 --prune; `trap ... ERR` notify; LF; env creds. |
| 3 | `ops/backup/restore.sh` | NEW | `set -euo pipefail`; fail-loud usage (`exit` non-zero) ako `$1`/`snapshotID` nedostaje; RESTIC env pre-flight guard; restic restore kroz `"${RESTIC_IMAGE}" restore "${SNAPSHOT_ID}" --target`; load kroz `gunzip` + `psql` (NIKAD `pg_restore` — plain par SM-D13); čita `RESTORE_TARGET_DB`/`RESTORE_DB_URL`, default TEST, NIKAD prod `DATABASE_URL` fallback (SM-D14); LF. |
| 4 | `ops/backup/_restic_common.sh` | NEW (opciono, G-14) | Deljeni helper: `docker run --rm "${RESTIC_IMAGE}"` wrapper + pre-flight guard + retention. Ako postoji, retention/guard grep-ovi ga uključuju (scope: SVE `ops/backup/*.sh`). |
| 5 | `ops/backup/crontab` | NEW | `TZ=UTC`; `0 3 * * *` → APSOLUTNA putanja `pg_backup.sh` (daily 03:00 UTC); `0 4 * * 0` (ILI weekly) → `media_backup.sh`; komentovan `restic check` + mesečni restore-test scaffold. |
| 6 | `ops/backup/RESTORE.md` | NEW | Restore runbook: kako pokrenuti `restore.sh <snapshotID>`; MESEČNI manual restore-test; `restic unlock` stale-lock napomena; `restic check` integritet napomena; restic-password offline-backup upozorenje; retention 7/4/3 objašnjenje; pokazuje na `ops/secrets/README.md` za creds. |
| 7 | `ops/secrets/README.md` | UPDATE | Novi backup var-ovi: `RESTIC_PASSWORD`/`RESTIC_PASSWORD_FILE`, `RESTIC_REPOSITORY`, `RESTIC_IMAGE` (pinovan tag, NE `:latest`), Storage Box host/user (`STORAGE_BOX_HOST`/`STORAGE_BOX_USER`) + rclone config, GlitchTip notify DSN/URL, `RESTORE_TARGET_DB`/`RESTORE_DB_URL`. |

## Ključne asercije (test ↔ Dev contract)

- **AC1/SM-D2** — `pg_backup.sh` postoji; sadrži `pg_dump`, `--no-owner`, cilja `postgres` servis kroz `docker compose -f compose/production.yml exec -T postgres`; 0 password literala (creds kroz `${...}`).
- **AC2/SM-D1 (RETENTION LOCK)** — preko SVIH `ops/backup/*.sh`: TAČNO `--keep-daily 7`, `--keep-weekly 4`, `--keep-monthly 3`, `--prune`; ODSUTNO `--keep-daily 30`.
- **AC3/SM-D12** — `media_backup.sh` koristi `docker run --rm` sa `coric_agrar_production_media` mount-ovan `:ro` + pinovan `${RESTIC_IMAGE}`; NEMA host bind-path / restic-na-hostu za media.
- **SM-D12 image pin** — `RESTIC_IMAGE` referenciran; NEMA `restic/restic:latest`.
- **AC4 encryption** — restic password env (`RESTIC_PASSWORD` ILI `RESTIC_PASSWORD_FILE`); NEMA plaintext repo/password.
- **AC5 cron** — `crontab` ima `TZ=UTC` + `0 3 * * *` (daily 03:00 UTC) + weekly media linija; apsolutne putanje.
- **AC6/SM-D13/D14 restore** — `restore.sh` postoji; fail-loud na missing snapshotID; `gunzip`+`psql`, NIKAD `pg_restore`; čita `RESTORE_TARGET_DB`/`RESTORE_DB_URL`; NE default-uje na prod `DATABASE_URL`.
- **AC7** — `RESTORE.md` postoji; mesečni restore-test, `restic unlock`, `restic check`, restic-password offline upozorenje.
- **AC8/SM-D7 fail-loud** — svaka `ops/backup/*.sh` ima `set -euo pipefail`; NEMA `|| true` maskiranja backup koraka; NON-EMPTY dump guard (`test -s` ili marker grep) u `pg_backup.sh`.
- **SM (prune gate)** — `restic forget`/`--prune` strukturno POSLE non-empty guard-a/push-a.
- **AC9/SM-D9 idempotency** — restic init guard (`snapshots ... || ... init`).
- **SM-D15 env pre-flight** — fail-loud guard ako `RESTIC_REPOSITORY`/`RESTIC_PASSWORD(_FILE)` prazan (`[ -n "${VAR:-}" ]` ili `${VAR:?}`).
- **AC10/SM-D8 notify** — `pg_backup.sh` ima `trap ... ERR` + notify funkcija koja curl-uje env GlitchTip DSN/URL (NE literal); NEMA `LOGGING = {` (9.6 deferred) u `ops/backup`.
- **AC11/SM-D10 secrets** — `ops/secrets/README.md` ažuriran sa backup var-ovima; NEMA literal secret-a u `ops/backup` (no `BEGIN PRIVATE KEY`, no hardkodovan password literal).
- **bash -n** — opciono/skip-guarded: ako `bash` na hostu → `bash -n` exit 0; inače `pytest.skip`.
