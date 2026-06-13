# Secrets — Story 9.2 Deploy + SSL

Ovaj dokument lista **gde** secret-i zive (nikad u repo-u) i **koje** secret-e
deploy pipeline zahteva. NIKAD ne komituj realne vrednosti — sve ide kroz GitHub
Actions secrets ILI box `.env` (van Git-a).

Naming convention: srpska latinica + engleski identifikatori; bez cirilice.

## 1. GitHub Actions secrets (Settings -> Secrets and variables -> Actions)

Postavlja ih Mihas PRE prvog deploy run-a (OQ-5). Koristi ih `.github/workflows/deploy.yml`.

| Secret | Opis |
|--------|------|
| `DEPLOY_SSH_KEY` | Privatni SSH kljuc (PEM) ciji je javni deo u `~/.ssh/authorized_keys` na boxu. |
| `DEPLOY_HOST` | IP ili hostname Hetzner box-a (staging i/ili production). |
| `DEPLOY_USER` | Non-root deploy user na boxu (npr. `deploy`). |
| `DEPLOY_APP_DIR` | Apsolutna putanja do repo checkout-a na boxu (npr. `/srv/coric_agrar`). OBAVEZAN — deploy.yml fail-uje ako je prazan (M5). |
| `DEPLOY_HOST_FINGERPRINT` | SSH host-key fingerprint box-a (host-key pinning protiv MITM-a — M8). Dobij sa `ssh-keyscan -t ed25519 <host>` ili `ssh-keygen -lf <known_hosts_entry>`. |

`GITHUB_TOKEN` (GHCR login+push u `ci.yml` build job-u) je auto-injektovan od GitHub-a —
NE postavlja se rucno.

### Akcija SHA-pinning (M8 — supply-chain hardening)

`deploy.yml` SSH korak koristi `appleboy/ssh-action` PIN-ovan na commit SHA (v1.2.2), NE
mutable major tag, jer ta akcija rukuje `DEPLOY_SSH_KEY` (kompromitovan upstream tag =
exfiltracija privatnog kljuca). Ostale akcije (`actions/checkout`, `docker/*` u ci.yml)
koriste major-version tagove po projektnoj konvenciji (1.9 CI); SHA-pinning SVIH akcija je
preporucen dalji hardening (OQ — best-effort batch), ali SECURITY-sensitive SSH akcija je
pinovana SADA jer je najveci blast-radius.

## 2. Box `.env` (van Git-a, na Hetzner box-u; izvor: Hetzner secrets panel)

`compose/production.yml` cita ove kroz `${...}` env interpolaciju (G-5). NIKAD u repo.

| Var | Opis |
|-----|------|
| `POSTGRES_PASSWORD` | DB password (prazan default u production.yml — prod MORA injektovati). |
| `DJANGO_SECRET_KEY` | Django secret key (generisi `secrets.token_urlsafe(50)`). |
| `DATABASE_URL` | Pun postgres URL sa password-om. |
| `DJANGO_ALLOWED_HOSTS` | Produkcioni hostovi (domen). |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://<domen>,https://www.<domen>` (G-9). |
| `DEPLOY_DOMAIN` / `ACME_EMAIL` | Domen + email za certbot (nginx-init.sh). |

### Backup (Story 9.5) — restic + Hetzner Storage Box

`ops/backup/{pg_backup.sh,media_backup.sh,restore.sh}` čitaju ove kroz `${...}` env
(box `.env`), NIKAD u repo. restic trči u pinovanom `restic/restic` Docker image-u
(SM-D12), creds se prosleđuju kroz `docker run -e ...` / `-v ...:ro` mount.

| Var | Tip | Opis |
|-----|-----|------|
| `RESTIC_PASSWORD` | secret | restic client-side encrypt password. Gubitak = nepovratan backup → backup-uj ODVOJENO/offline (NE samo na boxu, SM-D4/G-6). |
| `RESTIC_PASSWORD_FILE` | secret (alt) | Putanja do fajla sa restic password-om (alternativa `RESTIC_PASSWORD`; mount-uj `:ro` u restic kontejner). Postavi BAR JEDAN od ova dva. |
| `RESTIC_REPOSITORY` | config | restic repo backend. **rclone** (primarni, epics): `rclone:storagebox:coric-backup`. **sftp** (alternativa): `sftp:u123456@u123456.your-storagebox.de:/backup`. |
| `RESTIC_IMAGE` | config (NE secret) | Pinovan restic image tag (default `restic/restic:0.17.3`). NIKAD `:latest` (SM-D12/G-15). |
| `STORAGE_BOX_HOST` | config | Hetzner Storage Box host (npr. `u123456.your-storagebox.de`). Za **rclone backend** ide u `rclone.conf` remote, NE direktno u shell skripte; za **sftp backend** u `RESTIC_REPOSITORY` + SSH key. |
| `STORAGE_BOX_USER` | config | Storage Box user/subuser (npr. `u123456`). Isti rclone-vs-sftp razlaz kao host (SM-D5/G-12). |
| `RCLONE_CONFIG` / `RCLONE_CONFIG_DIR` | secret (rclone backend) | Putanja do `rclone.conf` (sadrži Storage Box SSH/SFTP creds). Mount-uje se `:ro` u restic kontejner (`-v "${RCLONE_CONFIG_DIR}:/root/.config/rclone:ro"`). |
| `GLITCHTIP_BACKUP_NOTIFY_DSN` | secret | GlitchTip ingest/store URL za thin fail-notify (`trap ERR → curl`, SM-D8). Zaseban od Django app DSN-a (9.3). NIKAD literal. |
| `RESTORE_TARGET_DB` | config | Restore-cilj psql URL — **default TEST DB, NIKAD prod** (SM-D14/G-22). `restore.sh` fail-loud ako nije postavljen. |
| `RESTORE_DB_URL` | config (alt) | Alternativni naziv za restore-cilj (fallback na `RESTORE_TARGET_DB`). Nikad ne pada nazad na prod `DATABASE_URL`. |

> **rclone vs sftp (SM-D5/G-12):** za **rclone backend** Storage Box host/user/creds idu u
> `rclone.conf` (`RCLONE_CONFIG`), NE u shell skripte; za **sftp backend** idu u
> `RESTIC_REPOSITORY` + SSH key path. `RESTIC_REPOSITORY` je env-driven → bezbolan switch (OQ-4).
>
> **restic password offline (SM-D4/G-6):** `RESTIC_PASSWORD`/`RESTIC_PASSWORD_FILE` se backup-uje
> ODVOJENO/offline — gubitak = kriptografski nepovratan backup. Vidi `ops/backup/RESTORE.md`.

## 3. Deploy-key blast-radius / SSH least-privilege (Task 7.2a — GUIDANCE)

Kompromitovan CI kljuc NE sme znaciti pun root na boxu. Restriktuj deploy kljuc
**box-side** u `~/.ssh/authorized_keys`:

```
command="/srv/coric_agrar/ops/deploy/deploy.sh production",no-pty,no-port-forwarding,no-agent-forwarding,no-X11-forwarding ssh-ed25519 AAAA... deploy@ci
```

- **`command="..."`** — forced-command: kljuc moze pokrenuti SAMO deploy.sh, nista drugo.
- **`no-pty`** — nema interaktivnog shell-a.
- **`no-port-forwarding` / `no-agent-forwarding`** — nema tunela / agent hijack-a.
- **Non-root deploy user** — namenski `deploy` user (NE `root`), sa `sudo` SAMO za
  potrebne docker/compose komande (least-privilege).

Cilj: kompromitovan CI kljuc != pun root na boxu (minimiziran blast-radius).
Ovo je guidance/checklist — NE over-engineer-uj (nema custom PAM/seccomp).
