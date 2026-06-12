---
story-id: 9-5-pg-dump-restic-hetzner-storage-box-backup
story_key: 9-5-pg-dump-restic-hetzner-storage-box-backup
story_id_dotted: 9.5
title: "pg_dump + restic + Hetzner Storage Box Backup"
status: review
epic: 9
epic-title: Go-Live Readiness (Production + Quality)
module: ops/backup (shell skripte + cron + restore runbook; NIJE Django app)
risk_tier: HIGH
language: Srpski (latinica)
created: 2026-06-12
created_by: SM (autonomous, YOLO)
needs_e2e: false
migrations: 0
new_dependencies: 0   # restic/rclone/pg_dump su SISTEM/box alati (NE Python paketi); 0 Django dep
test_approach: INFRA-VERIFY (import-light: bash -n parse + grep/file-inspekcija; bez Django/libmagic; stvarni restic/pg_dump run u Docker/CI/box)
depends_on:
  - 9-1    # compose/production.yml: `postgres` servis (postgres:16-alpine, DB/USER/PASSWORD env, interni DNS postgres:5432, BEZ host port) + `media` named volume coric_agrar_production_media
  - 9-2    # ops/ direktorijum + box `.env` secret pattern (ops/secrets/README.md) + deploy.sh bash konvencije (set -euo pipefail, SCRIPT_DIR/REPO_ROOT, fail-loud, srpska-latinica)
  - 9-3    # GlitchTip self-host (compose/production.yml glitchtip servisi) — fail-notify cilj (thin hook, NE 9.6 logging)
forward_dep:
  - 9-6    # Django LOGGING dict — nepovezano (deferred, NE diraj logging konfiguraciju)
---

# Story 9.5 — pg_dump + restic + Hetzner Storage Box Backup

Status: review

## Story / Opis

Kao **dev**, želim **automatski dnevni encrypted backup baze i media na off-site Hetzner Storage Box**, da bih **mogao da restore-ujem u slučaju katastrofe** (disk fail, ransomware, ljudska greška, box-loss).

**PETA Epic 9 (Go-Live Readiness) story** — uvodi off-site disaster-recovery backup. Ovo je **ops/infra story** (shell skripte + cron + restore runbook) — **NIJE Django app**: 0 modela, 0 migracija, 0 Django dep-ova, 0 app koda. Naslednik je 9.2 (deploy + production stack) i konzumira 9.1 forward-dep-ove (`postgres` servis + `media` named volume) + 9.2 secret pattern (box `.env`, van Git-a) + 9.3 GlitchTip (fail-notify cilj).

### Šta 9.5 STVARNO isporučuje

| # | Artefakt | Tip | Napomena |
|---|---|---|---|
| 1 | `ops/backup/pg_backup.sh` | NEW | `pg_dump` (iz `postgres` servisa, `--no-owner`) → gzip → temp fajl → restic encrypt push kroz pinovan `restic/restic` Docker image (`docker run --rm`, SM-D12) → Storage Box. Daily 03:00 UTC. `set -euo pipefail`. |
| 2 | `ops/backup/media_backup.sh` | NEW | restic snapshot `media` named volume-a (encrypted, dedup) kroz `restic/restic` image koji mount-uje volume read-only (SM-D12). WEEKLY (nedeljno). `set -euo pipefail`. |
| 3 | `ops/backup/restore.sh` | NEW | restic restore `<snapshotID>` na lokal + `gunzip → psql` load (NE pg_restore — plain-format par zaključan, SM-D13) u `RESTORE_TARGET_DB` (default TEST DB, NIKAD prod — SM-D14) — za mesečni restore-test. `set -euo pipefail`. |
| 4 | `ops/backup/crontab` (ILI `ops/backup/cron.d` dokumentovane linije) | NEW | Daily DB 03:00 UTC + weekly media (npr. ned 04:00 UTC). Apsolutne putanje (M6-stil). |
| 5 | `ops/backup/RESTORE.md` | NEW | Restore runbook + **mesečni manual restore-test** procedura (project-context:468) + retention/encrypt objašnjenje. |
| 6 | `ops/secrets/README.md` | UPDATE | Dodaj backup secret-e (RESTIC_PASSWORD/RESTIC_PASSWORD_FILE, RESTIC_REPOSITORY, Storage Box host/user/key, GlitchTip notify DSN/URL) u tabelu. |
| 7 | `.env.example` (opciono) | UPDATE (opciono) | Backup placeholder-i (prazni, NIKAD realan secret). |
| 8 | `compose` backup sidecar | OPCIONO | NIJE zahtevan — cron radi na HOST-u (mirror certbot HOST-pattern AR-13). Vidi SM-D6. |
| 9 | `tests/test_backup_scripts.py` | NEW (TEA) | INFRA-VERIFY import-light: bash -n parse + grep retention-flagovi / cron 03:00 + TZ=UTC / pg_dump correctness + non-empty-assert / restic env pre-flight guard / restore gunzip-psql + restore-target-not-prod / no-literal-secrets / restic-init-idempotency / prune-gated / restore runbook present. |

### Postojeće stanje (READ pre izmene — obavezno)

| Fajl | Linija | Sadržaj / zašto je relevantno |
|---|---|---|
| `compose/production.yml` | 19-37 | **`postgres` servis** — `image: postgres:16-alpine`, `POSTGRES_DB: ${POSTGRES_DB:-coric_agrar}`, `POSTGRES_USER: ${POSTGRES_USER:-coric}`, `POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-}` (prazan default — prod injektuje), **BEZ host port expose** (interni Docker DNS `postgres:5432`). → `pg_dump` MORA teći IZ/PROTIV tog servisa (`docker compose -f compose/production.yml exec -T postgres pg_dump ...`). |
| `compose/production.yml` | 203-209 | **`media` named volume** `coric_agrar_production_media` (mount `/app/media` u django/nginx). → media restic snapshot cilja taj volume kroz pinovan `restic/restic` image koji ga mount-uje read-only DIREKTNO u restic kontejner (`docker run --rm -v coric_agrar_production_media:/data:ro ... "${RESTIC_IMAGE}" backup /data` — SM-D12/G-9). NE host bind-path (named volume root-only na hostu). |
| `ops/deploy/deploy.sh` | 1-59 | **Bash konvencije** koje 9.5 nasleđuje: `#!/usr/bin/env bash`, `set -euo pipefail` (linija 25), `SCRIPT_DIR`/`REPO_ROOT` resolve + `cd "${REPO_ROOT}"` (M6 CWD guard, linije 34-36), fail-loud usage + exit codes, srpska latinica + engleski identifikatori, BEZ ćirilice, LF line-endings (`.gitattributes:8` `*.sh text eol=lf`). |
| `ops/secrets/README.md` | 33-44 | **Box `.env` secret pattern (9.2)** — secret-i žive na boxu (van Git-a), čitaju se kroz `${...}` env interpolaciju, NIKAD u repo. 9.5 PROŠIRUJE ovu tabelu backup var-ovima. |
| `compose/production.yml` | 127-158 | **GlitchTip servisi (9.3)** — self-host error tracking. Fail-notify hook iz pg_backup.sh/media_backup.sh cilja GlitchTip ingest (thin curl, NE 9.6 logging stack). |
| `_bmad-output/planning-artifacts/epics.md` | 1235-1246 | **Story 9.5 ACs — AUTORITATIVNI SCOPE.** pg_backup.sh + media_backup.sh + cron 3am daily UTC + restore.sh + retention 7/4/3 + restic encrypt + GlitchTip fail-log. |
| `_bmad-output/project-context.md` | 465-469 | Backup & restore: cron dnevni pg_dump 3:00 UTC, encrypt+upload Storage Box, **„30 dana retencija"** (RECONCILE sa epics 7/4/3 — vidi SM-D1), restore test mesečno (manual), media sedmični rsync (RECONCILE → restic snapshot weekly — vidi SM-D3). |
| `.gitattributes` | 8 | `*.sh text eol=lf` VEĆ POSTOJI — VERIFIKUJ, NE re-kreiraj (izbegni churn; mirror 9.2 Task 2.2). |

---

## SM Decisions (autoritativno nad ilustrativnom formulacijom; reconciliacije epics.md ↔ project-context.md)

**SM-D1 — RETENTION RECONCILIATION: epics.md 7/4/3 POBEĐUJE flat „30 dana".** ⚠️ VEROVATNA REVIEW ZAMKA.
project-context.md:467 kaže flat **„30 dana retencija"** a brief implicira `--keep-daily 30`. ALI epics.md:1244 (AUTORITATIVNI SCOPE SOT) eksplicitno kaže: **„Restic policy retain-uje 7 dnevnih + 4 nedeljnih + 3 mesečnih (do 30 dana effective coverage)".** **ODLUKA: prati epics.md.** Koristi TAČNO:
```
restic forget --keep-daily 7 --keep-weekly 4 --keep-monthly 3 --prune
```
Ovo zadovoljava „30-day effective coverage" (7 dnevnih pokriva poslednju nedelju dan-po-dan; weekly+monthly produžavaju recovery horizont) i DR-robustnije je od flat keep-daily 30 (manje snapshot-a, duži horizont, bolji prune). AC2 asertuje TAČAN flag-set. (Flat keep-daily 30 NIJE pogrešno samo po sebi, ali epics je SOT — NE improvizuj flat 30.)

**SM-D2 — pg_dump TEČE PROTIV `postgres` servisa kroz `docker compose exec -T` (NE bare host psql).**
`postgres` servis (compose/production.yml:19-37) NE izlaže host port — interni Docker DNS `postgres:5432` je jedini pristup. **ODLUKA:** `docker compose -f compose/production.yml exec -T postgres pg_dump -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" --no-owner ...` (ILI `run --rm` one-off). `-T` (no TTY) je OBAVEZAN za cron/non-interactive. `--no-owner` (i razmotri `--no-privileges`) jer restore ide u svež DB sa drugim role-ovima. Credentials (`POSTGRES_USER`/`POSTGRES_DB`/`POSTGRES_PASSWORD`) iz env-a (box `.env`/`${...}`), NIKAD literali. `PGPASSWORD` (ili `~/.pgpass`) kroz env, ne argument.

**SM-D3 — MEDIA: restic SNAPSHOT (weekly) reconcile-uje project-context „sedmični rsync".**
project-context.md:469 kaže „media bekap: sedmični rsync ka Storage Box-u"; epics.md:1242 kaže `media_backup.sh` radi restic SNAPSHOT media volume-a. **ODLUKA: primarni put = restic snapshot media volume-a (encrypted, dedup, isti repo/backend kao DB), NA WEEKLY (sedmičnoj) kadenci** — reconcile dva izvora: restic supersede-uje goli rsync (encrypted + dedup + isti retention/restore tooling), kadenca ostaje sedmična (project-context). NE pravi zaseban rsync put (jedan backup tool = jedan restore runbook). Media snapshot može biti zaseban restic repo ILI zaseban path/tag u istom repo-u (Dev bira; runbook dokumentuje).

**SM-D4 — ENCRYPTION: restic native client-side encryption (encrypted-at-rest na Storage Box-u).**
restic šifruje SVE pre push-a — Storage Box nikad ne vidi plaintext. restic password kroz `RESTIC_PASSWORD` ILI `RESTIC_PASSWORD_FILE` env, **NIKAD u repo** (box `.env`). Gubitak restic password-a = nepovratan backup (runbook MORA upozoriti: password se backup-uje ODVOJENO/offline — npr. password manager, NE na istom boxu). AC za encrypt-at-rest (epics:1243 „encrypted, restic native").

**SM-D5 — BACKEND: restic rclone backend (RESTIC_REPOSITORY=rclone:<remote>:<path>) per epics.md; sftp dokumentovana alternativa.**
epics.md:1242 kaže „push na Hetzner Storage Box **via rclone**". restic podržava i `rclone:` i `sftp:` backend za Storage Box. **ODLUKA: primarni = rclone backend** (`RESTIC_REPOSITORY=rclone:storagebox:coric-backup`), sa **sftp kao prihvatljivom dokumentovanom alternativom** (`RESTIC_REPOSITORY=sftp:u123456@u123456.your-storagebox.de:/backup`). Svi creds (Storage Box user/host/SSH key, rclone remote config, restic password) kroz box `.env`/env, NIKAD komitovani. (rclone vs sftp final izbor = OQ-4 go-live.)

**SM-D6 — CRON NA HOSTU (NE compose sidecar) — sidecar OPCIONO.**
Mirror certbot HOST-pattern (9.2 AR-13: certbot trči na hostu, ne kontejner). **ODLUKA: backup cron živi na boxu (`ops/backup/crontab` ILI `/etc/cron.d/coric-backup` linije), pozива skripte koje `docker compose exec`-uju u postgres servis.** Compose backup sidecar (PERZISTENTAN servis sa restic/cron unutar compose-a) je OPCIONO — NE zahtevan, NE preporučen za v1 (jednostavnost; host cron ima pristup `docker compose` + box `.env`). **NAPOMENA (SM-D12):** prolazni `restic/restic` `docker run --rm` koji skripte pokreću NIJE sidecar (nije perzistentan servis) — to je kratkotrajan one-off kontejner; restic binarka živi u image-u, NE na hostu. Host cron + one-off restic kontejner = v1 (sidecar ostaje OPCIONO). Cron linije koriste APSOLUTNE putanje (npr. `/srv/coric_agrar/ops/backup/pg_backup.sh`) — relativne fail-uju iz cron CWD-a (M6 lekcija iz 9.2). (Host vs sidecar = OQ-5.)

**SM-D7 — FAIL-LOUD je #1 prioritet: TIHI backup fail je NAJGORI ishod. NON-EMPTY DUMP ASSERT je OBAVEZAN (NE alternativa).**
„Misliš da imaš backup, a nemaš." **ODLUKA:** sve skripte `set -euo pipefail`; `pg_dump | gzip` pipe MORA imati `pipefail` AKTIVAN (NE samo `set -e`). ALI `pipefail` SAM NIJE DOVOLJAN: pg_dump može exit-ovati 0 a proizvesti PRAZAN/skoro-prazan dump (pogrešna/prazna baza, schema-only race, prekinut konekcija koja vrati 0). **OBAVEZNI STRUKTURNI PUT (PREFERRED, ne opcija):** dump u temp fajl → **assert non-trivial** (`test -s "${TMPFILE}"` AND size-floor check, npr. min bajtova, AND/ILI grep za očekivani marker `-- PostgreSQL database dump` u dekompresovanom/sirovom dump-u) → TEK ONDA restic push. Ako assert padne → `exit` non-zero + fail-notify (SM-D8) PRE bilo kakvog restic push-a. Goli `pipefail`-bez-temp-fajla je SLABIJI fallback (hvata pg_dump≠0 ali NE hvata exit-0-prazan-dump) — NE koristi ga kao primarni put. `trap ERR`/`trap EXIT` → fail-notify hook (SM-D8). NIKAD `|| true` na backup koraku. (Ovo eskalira raniju „ILI ... idealno" formulaciju u TVRD zahtev — AC8.)

**SM-D8 — GlitchTip fail-notify je THIN HOOK (9.6 logging OSTAJE deferred).**
epics.md:1246: „Backup status (sukces/fail) loguje u GlitchTip pri fail-u". GlitchTip self-host postoji od 9.3. **ODLUKA: tanak fail-notify hook** — `trap ERR` → `notify_failure()` funkcija koja radi `curl` na GlitchTip ingest endpoint (DSN/store URL iz env-a) ILI minimalno jasno-označen hook sa env var-om. **NE gradi 9.6 Django LOGGING dict ovde** (scope-disciplina — 9.6 ostaje backlog NETAKNUT). Notify-on-FAILURE je u scope-u; success-logging je opciono/best-effort (epics kaže „pri fail-u"). GlitchTip notify DSN/URL kroz env (box `.env`), NIKAD literal.

**SM-D9 — restic init IDEMPOTENTAN: re-run kad repo postoji NE sme fail-ovati.**
Prvi backup mora `restic init` repo; svaki naredni NE sme pokušati re-init (fail „repo already exists"). **ODLUKA:** guard — `restic snapshots >/dev/null 2>&1 || restic init` (ILI eksplicitan check da li repo postoji → init SAMO ako nedostaje). Mirror 9.2 certbot cert-existence idempotency guard. AC za ovo.

**SM-D10 — SECRETS DISCIPLINE: 0 literala. SVE kroz env/box `.env` (reuse 9.2 pattern).**
restic password, Storage Box user/host/SSH key path, rclone remote config, DB creds, GlitchTip notify DSN — SVE kroz env (box `.env`, van Git-a). **ODLUKA:** ni jedan script NE sadrži plaintext secret. UPDATE `ops/secrets/README.md` tabelu sa novim backup var-ovima. `.env.example` dobija prazne placeholder-e (opciono). NEGATIVE AC: grep na sumnjive patterne (`BEGIN ... PRIVATE KEY`, hardkodovan ne-prazan `RESTIC_PASSWORD=<nešto>`/`POSTGRES_PASSWORD=<nešto>`).

**SM-D12 — restic TRČI KAO PINOVAN `restic/restic` DOCKER IMAGE (one-off `docker run --rm`), NE restic-na-hostu, NE long-running sidecar.** ⚠️ KRITIČNA DISAMBIGUACIJA (host-vs-container tenzija).
`new_dependencies=0` znači **0 host-deps i 0 Python paketa** — restic se NE instalira na host. Pošto ni `django` ni `postgres` image NE isporučuju restic, a named Docker volume (`coric_agrar_production_media`) NIJE vidljiv na host bind-path-u bez root-a (Linux default `/var/lib/docker/volumes/.../_data`, root-only), **ODLUKA: restic se SVUDA poziva kroz pinovan zvanični `restic/restic` image kao prolazni `docker run --rm` kontejner** — NE binarka na hostu, NE perzistentan compose servis.
- **Pinovani tag (mirror image-pin discipline `glitchtip:v6.0` iz 9.3):** definiši `RESTIC_IMAGE` env (default npr. `restic/restic:0.17.3` — Dev potvrđuje tačan tag kroz Task 1.2 Web Intel), NIKAD `:latest`.
- **MEDIA backup (AC3/Task 3.2/G-9):** named volume se mount-uje DIREKTNO u restic kontejner (Docker ga čini vidljivim unutar kontejnera — rešava root-only host-path problem):
  ```
  docker run --rm \
    -v coric_agrar_production_media:/data:ro \
    -e RESTIC_REPOSITORY -e RESTIC_PASSWORD_FILE \
    -v "${RCLONE_CONFIG_DIR}:/root/.config/rclone:ro" \   # ILI SSH key za sftp backend
    "${RESTIC_IMAGE}" backup /data --tag media
  ```
  `:ro` na volume-u (backup NE piše u media). Repo creds (`RESTIC_REPOSITORY`/`RESTIC_PASSWORD_FILE`) kroz `-e` env-passthrough; rclone.conf (ILI SSH key za sftp) kroz dodatni `-v` mount. **UKLANJA „ILI box bind-path" hand-waving** — named volume se NE čita preko host bind-path-a.
- **DB backup (AC1/Task 2):** `pg_dump` teče kroz `docker compose exec -T postgres pg_dump` (SM-D2, NEPROMENJENO) → dump u temp fajl na **deljenom host putanji** (npr. `${REPO_ROOT}/ops/backup/.tmp/` ili `/tmp`) → restic push tog temp fajla kroz ISTI `restic/restic docker run --rm` (mount temp dir + repo creds), zatim cleanup temp fajla. pg_dump izlaz ide u temp fajl (NE pipe-uje se direktno u restic kontejner) — ovo zadržava FAIL-LOUD error-check PRE restic koraka (SM-D7/AC8) i drži restic-invokaciju jednoobraznom (uvek restic image).
- **restic init / forget / restore takođe kroz `restic/restic` image** (ista invokaciona forma) — idempotency guard (SM-D9), retention (SM-D1) i restore (AC6) su `docker run --rm "${RESTIC_IMAGE}" snapshots|init|forget|restore ...`.
- Ovo pomiruje „sidecar OPCIONO" (SM-D6): prolazni `docker run --rm` restic kontejner NIJE perzistentan servis (NIJE sidecar) — host cron poziva skripte, skripte pokreću kratkotrajan restic kontejner i izlaze. Cron i dalje na HOSTU (SM-D6 NEPROMENJEN); SAMO restic binarka živi u svom image-u.
- `RESTIC_IMAGE` ide u `ops/secrets/README.md` env tabelu (AC11/Task 7) i `.env.example` (kao NE-secret config var sa default pin-om).

**SM-D13 — DUMP-FORMAT ↔ RESTORE-COMMAND PAIRING: zaključaj JEDAN par. plain `pg_dump | gzip` ⇒ restore `gunzip | psql` (NE pg_restore).** ⚠️ MISMATCH FAIL-UJE TEK PRI RESTORE-u.
AC1 koristi plain-text `pg_dump` (NE custom `-Fc`) → gzip. Plain-SQL dump se restore-uje SAMO kroz `gunzip | psql` — `pg_restore` radi ISKLJUČIVO sa custom (`-Fc`) ILI directory/tar formatom, NE sa plain SQL. Ako restore.sh nudi `pg_restore` na plain dump → fail tek u DR trenutku („input file appears to be a text format dump. Please use psql."). **ODLUKA: zaključaj par plain `pg_dump | gzip` ⇒ restore `gunzip | psql`.** restore.sh koristi ISKLJUČIVO `gunzip → psql` put. `pg_restore` se UKLANJA iz restore.sh (ILI se jasno označi kao „SAMO ako se DB backup pređe na custom `-Fc` format" — što 9.5 NE radi). AC1↔AC6 MORAJU biti konzistentni (oba plain/psql). (Ako bi se ikad prešlo na `-Fc`: restore = `pg_restore`, BEZ gzip — ali to NIJE 9.5 izbor.)

**SM-D14 — RESTORE-TARGET DB je EKSPLICITAN env var; default = TEST DB; NIKAD fallback na prod `DATABASE_URL`.** ⚠️ DATA-LOSS GUARD.
restore.sh restore-uje za restore-TEST (AC6/SM-D11) — NE sme tiho prepisati živu prod bazu. **ODLUKA:** restore.sh čita eksplicitan restore-cilj iz `RESTORE_TARGET_DB` (ILI `RESTORE_DB_URL`) env var-a koji **default-uje na TEST DB**, i **NE sme pasti nazad na prod `DATABASE_URL`/`POSTGRES_*` prod-creds** ako restore-cilj nije postavljen. Ako restore-cilj nije eksplicitno setovan i nema bezbedan test-default → fail-loud (ne pretpostavljaj prod). `RESTORE_TARGET_DB` ide u AC11 secrets tabelu + `ops/secrets/README.md` (kao config var, NE secret-per-se). Test asertuje da restore.sh NE koristi prod `DATABASE_URL` kao default psql cilj.

**SM-D15 — RESTIC ENV PRE-FLIGHT GUARD: fail-loud na prazan `RESTIC_REPOSITORY`/`RESTIC_PASSWORD(_FILE)` PRE snapshots-or-init guard-a.** ⚠️ ORPHANED-REPO ZAMKA.
Idempotency guard `restic snapshots || restic init` (SM-D9) ima opasnu interakciju: ako su creds prazni/pogrešni, `restic snapshots` padne iz CREDENTIAL razloga, što guard pogrešno čita kao „repo ne postoji" → `restic init` kreira ORPHANED repo na pogrešnom mestu (ili pokušava, maskirajući pravi uzrok). **ODLUKA:** svaka skripta MORA fail-loud (exit non-zero + jasna poruka) ako je `RESTIC_REPOSITORY` prazan ILI ako su i `RESTIC_PASSWORD` i `RESTIC_PASSWORD_FILE` prazni — **PRE** snapshots-or-init guard-a. `set -u` hvata UNSET var, ali NE hvata postavljen-ali-prazan → eksplicitan `[ -n "${RESTIC_REPOSITORY:-}" ] || { echo ...; exit 1; }` check (i ekvivalent za password). Helper `_restic_common.sh` je prirodno mesto (G-14). Test asertuje prisustvo pre-flight guard-a.

**SM-D11 — SCOPE GUARD — šta JESTE i šta NIJE 9.5:**
- **U SCOPE-u:** `ops/backup/{pg_backup.sh,media_backup.sh,restore.sh}`, cron fajl/linije, `ops/backup/RESTORE.md` runbook, `ops/secrets/README.md` EDIT (+ opciono `.env.example`), opcioni compose sidecar, INFRA-VERIFY testovi.
- **VAN SCOPE-a (DEFER, NE DIRAJ):**
  - **9.6** (Django LOGGING dict) — ostaje `backlog`. NE diraj logging konfiguraciju. Fail-notify je THIN curl hook, NE 9.6.
  - Re-implementacija `ops/deploy/deploy.sh` — NE diraj deploy/rollback skripte.
  - Stvarno Storage Box provisioning + creds + GlitchTip notify endpoint — EKSTERNO, manual go-live gate (OQ).
  - Auto-restore u produkciju — restore.sh restore-uje na LOKAL za TEST (NE prepisuje živu prod bazu bez svesne ručne intervencije — data-loss guard, mirror 9.2 rollback migrate-down svesnost).
  - Django migracija — NEMA (nema modela).

---

## Acceptance Criteria

> Mapiranje na epics.md Story 9.5 „When/And/Then". Svaki AC konkretan i testabilan kroz INFRA-VERIFY (bash -n parse + grep/file-inspekcija).

**AC1 — `ops/backup/pg_backup.sh` postoji i radi pg_dump → gzip → restic encrypt → Storage Box push** (epics:1242-1243)
**Given** `postgres` servis iz 9.1 (postgres:16-alpine, interni DNS, BEZ host port)
**When** Dev kreira `ops/backup/pg_backup.sh`
**Then** skripta: (1) izvršava **plain-text** `pg_dump` (NE custom `-Fc`) PROTIV `postgres` servisa kroz `docker compose -f compose/production.yml exec -T postgres pg_dump` (ILI `run --rm`) sa `--no-owner` (i `--no-privileges` — SM-D2/G-16), dump u temp fajl na deljenom host putanji; (2) komprimuje (`gzip`); (3) **assert-uje da je dump non-trivial (`test -s` + size-floor/marker grep) PRE push-a** (AC8/SM-D7 — OBAVEZNO); (4) push-uje temp dump kroz restic (encrypted) na Storage Box backend, gde se restic poziva kroz pinovan `restic/restic` Docker image (`docker run --rm -e RESTIC_REPOSITORY -e RESTIC_PASSWORD_FILE -v <temp-dir> -v <rclone/ssh creds> "${RESTIC_IMAGE}" backup ...` — SM-D12, NE restic-na-hostu, NE sidecar) (SM-D4/D5); (5) `restic forget` retention takođe kroz `restic/restic` image, GATE-ovan na uspeh push-a (AC2); (6) cleanup temp fajla.
**And** format-par je ZAKLJUČAN: plain `pg_dump | gzip` ⇒ restore je `gunzip | psql` (NE `pg_restore` — SM-D13); AC1↔AC6 konzistentni.
**And** DB/USER/PASSWORD dolaze iz env-a (`${POSTGRES_USER}`/`${POSTGRES_DB}`/`PGPASSWORD` ili `.pgpass`), NIKAD literali (AC8/SM-D10).
**And** skripta počinje sa `#!/usr/bin/env bash` + `set -euo pipefail`, LF line-endings (G-1), SCRIPT_DIR/REPO_ROOT resolve (M6 mirror deploy.sh).

**AC2 — RETENTION POLICY: TAČAN flag-set `--keep-daily 7 --keep-weekly 4 --keep-monthly 3 --prune`** (epics:1244, SM-D1)
**Given** restic repo sa snapshot-ima
**When** test parsira `ops/backup/pg_backup.sh` (i/ili media skriptu / zajednički helper)
**Then** skripta sadrži TAČNO `restic forget --keep-daily 7 --keep-weekly 4 --keep-monthly 3 --prune` (7 dnevnih + 4 nedeljnih + 3 mesečnih → 30-day effective coverage).
**And** NE sadrži `--keep-daily 30` flat (reconciliacija — epics 7/4/3 SOT nad project-context flat-30; SM-D1). Test asertuje TAČNE brojeve (7/4/3) i `--prune`.
**And** `restic forget --prune` se izvršava SAMO POSLE uspešnog dump+push koraka (koji je prošao non-empty assert AC8/SM-D7) — NIKAD pre/nezavisno: niz loših run-ova NE sme prune-ovati poslednji DOBAR snapshot. Strukturno: forget je posle push-a u istom skript-toku, iza fail-loud guard-a (`set -e` prekida pre forget-a ako push padne). (SM-D7/G-17)

**AC3 — `ops/backup/media_backup.sh` radi restic snapshot media volume-a (WEEKLY)** (epics:1242, SM-D3)
**Given** `media` named volume `coric_agrar_production_media` (9.1)
**When** Dev kreira `ops/backup/media_backup.sh`
**Then** skripta radi `restic backup` (snapshot) media volume-a kroz pinovan `restic/restic` Docker image koji mount-uje named volume read-only DIREKTNO u restic kontejner: `docker run --rm -v coric_agrar_production_media:/data:ro -e RESTIC_REPOSITORY -e RESTIC_PASSWORD_FILE -v <rclone.conf ILI SSH key>:ro "${RESTIC_IMAGE}" backup /data --tag media` (SM-D12). Encrypted, na isti Storage Box backend. **NE restic-na-hostu i NE host bind-path** — named volume NIJE čitljiv preko host putanje bez root-a; Docker ga čini vidljivim UNUTAR restic kontejnera (SM-D12/G-9).
**And** kadenca je WEEKLY (cron — AC5), reconcile-ujući project-context „sedmični rsync" → restic snapshot (SM-D3).
**And** restic se NE instalira na host (consistent sa `new_dependencies=0`) — živi u pinovanom `restic/restic:<tag>` image-u (NE `:latest`), `RESTIC_IMAGE` env-driven (SM-D12).
**And** `set -euo pipefail` + LF + env-driven secrets + restic-init idempotency (AC9).

**AC4 — ENCRYPTION AT REST: restic native client-side encryption** (epics:1243, SM-D4)
**Given** backup arhive na Storage Box-u
**When** restic push-uje
**Then** repo je restic-encrypted (`restic init` kreira encrypted repo); password kroz `RESTIC_PASSWORD`/`RESTIC_PASSWORD_FILE` env (NIKAD u repo/skripti — SM-D4/D10). Pošto restic trči u `restic/restic` kontejneru (SM-D12), creds se prosleđuju kroz `docker run -e RESTIC_REPOSITORY -e RESTIC_PASSWORD_FILE` (env-passthrough) + `-v` mount za `RESTIC_PASSWORD_FILE`/rclone.conf/SSH key — NIKAD literal u `docker run` argumentima.
**And** test asertuje da skripte referenciraju `RESTIC_PASSWORD`/`RESTIC_PASSWORD_FILE` (NE inline password) i da je `RESTIC_REPOSITORY` env-driven (prosleđen kroz `-e` u restic kontejner).
**And** runbook upozorava da se restic password backup-uje ODVOJENO/offline (gubitak = nepovratan backup).

**AC5 — CRON: daily DB 03:00 UTC + weekly media** (epics:1242, project-context:466, SM-D6)
**Given** backup skripte
**When** Dev kreira `ops/backup/crontab` (ILI dokumentovane `/etc/cron.d` linije)
**Then** postoji cron entry koji pokreće `pg_backup.sh` **daily u 03:00 UTC** (`0 3 * * *`) i `media_backup.sh` **weekly** (npr. nedeljom 04:00 UTC `0 4 * * 0`).
**And** cron linije koriste APSOLUTNE putanje do skripti (relativne fail-uju iz cron CWD — M6; SM-D6).
**And** test grep-uje cron za `0 3 * * *` (ILI ekvivalent 03:00) + pg_backup poziv, i weekly media poziv.

**AC6 — `ops/backup/restore.sh` restore-uje konkretan snapshot na lokal** (epics:1245)
**Given** restic repo sa snapshot-ima
**When** Dev kreira `ops/backup/restore.sh`
**Then** skripta prima `<snapshotID>` argument, radi `restic restore <snapshotID> --target <lokal>` + učitava dump u DB ISKLJUČIVO kroz `gunzip → psql` (NE `pg_restore` — plain-format par je zaključan, SM-D13; pg_restore radi samo sa custom `-Fc` formatom koji 9.5 NE koristi) za restore-TEST.
**And** restore-cilj je EKSPLICITAN env var `RESTORE_TARGET_DB` (ILI `RESTORE_DB_URL`) koji **default-uje na TEST DB** i **NE sme pasti nazad na prod `DATABASE_URL`/prod creds** (SM-D14 data-loss guard). Ako restore-cilj nije bezbedno postavljen → fail-loud, NE pretpostavljaj prod.
**And** skripta restore-uje na LOKAL/TEST cilj (NE prepisuje živu prod bazu bez svesne ručne intervencije — data-loss guard SM-D11/SM-D14).
**And** fail-loud usage ako `snapshotID` nedostaje (`exit` non-zero + poruka, mirror deploy.sh:42-49).
**And** test asertuje: restore.sh koristi `gunzip`+`psql` (NE `pg_restore`); čita `RESTORE_TARGET_DB`/`RESTORE_DB_URL`; NE koristi prod `DATABASE_URL` kao default psql cilj.

**AC7 — RESTORE RUNBOOK + mesečni manual restore-test dokumentovan** (project-context:468)
**Given** restore procedura
**When** Dev napiše `ops/backup/RESTORE.md`
**Then** runbook postoji i dokumentuje: (1) kako pokrenuti `restore.sh <snapshotID>`; (2) **MESEČNI manual restore-test** procedura (verify backup nije corrupted — project-context:468); (3) gde su restic password / Storage Box creds (pokazuje na ops/secrets/README.md, NE literali); (4) retention objašnjenje (7/4/3); (5) restic-password offline-backup upozorenje (SM-D4); (6) checklist forma (kockice) za mesečni restore-test.

**AC8 — FAIL-LOUD: `set -euo pipefail` + OBAVEZAN non-empty dump assert PRE restic push-a** (project-context:477 idempotency duh + DR safety, SM-D7)
**Given** `pg_dump | gzip` → temp fajl → restic pipeline
**When** test parsira skripte
**Then** sve skripte sadrže `set -euo pipefail` (eksplicitno `pipefail` — NE samo `set -e`).
**And** DB backup MORA (OBAVEZNO, ne opciono): dump-u-temp-fajl → **assert non-trivial** (`test -s "${TMPFILE}"` AND size-floor check, npr. min-bajtova prag, AND/ILI grep za očekivani marker `-- PostgreSQL database dump`) → push restic TEK kad assert prođe (SM-D7). Ako dump padne assert (prazan/skoro-prazan — pogrešna/prazna baza, schema-only race, prekinuta konekcija sa exit-0) → `exit` non-zero + fail-notify PRE restic push-a. Goli `pipefail`-bez-temp-asserta je SLABIJI fallback (hvata pg_dump≠0 ali NE exit-0-prazan-dump) — NE prihvatljiv kao primarni put za DB backup.
**And** NIKAD `|| true` na backup koraku.
**And** test asertuje: `set -euo pipefail` prisutno; NEMA `|| true` na pg_dump/restic koraku; **I prisutan size/content non-empty check** (`test -s` ILI `[ -s` ILI size-floor ILI marker-grep `-- PostgreSQL database dump`) PRE restic push-a u pg_backup.sh.

**AC9 — restic init IDEMPOTENT: re-run kad repo postoji NE pada** (SM-D9, project-context:477)
**Given** restic repo koji možda već postoji
**When** backup skripta startuje
**Then** skripta init-uje repo SAMO ako ne postoji — guard kroz `restic/restic` image (SM-D12): `docker run --rm <creds> "${RESTIC_IMAGE}" snapshots >/dev/null 2>&1 || docker run --rm <creds> "${RESTIC_IMAGE}" init` (ILI ekvivalent guard) — re-run kad repo postoji NE fail-uje (graceful).
**And** RESTIC ENV PRE-FLIGHT GUARD (SM-D15): PRE snapshots-or-init guard-a, skripta MORA fail-loud (exit non-zero + jasna poruka) ako je `RESTIC_REPOSITORY` prazan ILI ako su i `RESTIC_PASSWORD` i `RESTIC_PASSWORD_FILE` prazni — inače credential-fail bude pogrešno pročitan kao „repo ne postoji" i `restic init` kreira ORPHANED repo. (`set -u` hvata UNSET ali NE postavljen-ali-prazan → eksplicitan `[ -n "${VAR:-}" ]` check.)
**And** test grep-uje: idempotency guard pattern (init-only-if-missing) U skripti; I pre-flight guard koji proverava `RESTIC_REPOSITORY`/`RESTIC_PASSWORD`(`_FILE`) ne-prazan PRE init guard-a.

**AC10 — GlitchTip FAIL NOTIFICATION (thin hook)** (epics:1246, SM-D8)
**Given** GlitchTip self-host (9.3)
**When** backup fail-uje (`trap ERR`/non-zero exit)
**Then** skripta poziva tanak fail-notify hook (`notify_failure()` → `curl` na GlitchTip ingest/store endpoint, DSN/URL iz env-a) ILI minimalno jasno-označen hook funkciju sa env var-om.
**And** hook je THIN — NE gradi 9.6 Django LOGGING dict (SM-D8/D11 scope-disciplina). GlitchTip notify DSN/URL iz env (box `.env`), NIKAD literal.
**And** test asertuje prisustvo `trap ERR`/fail-notify funkcije + env-driven GlitchTip URL/DSN (NE literal).

**AC11 — SECRETS: 0 literala; sve kroz env/box `.env`; `ops/secrets/README.md` ažuriran** (project-context:461-462, SM-D10)
**Given** restic password, Storage Box creds, DB creds, GlitchTip DSN
**When** test grep-uje SVE nove fajlove
**Then** ni jedan script NE sadrži plaintext secret (NEGATIVE grep: `BEGIN ... PRIVATE KEY`, hardkodovan ne-prazan `RESTIC_PASSWORD=`/`POSTGRES_PASSWORD=` sa literalom, ne-`${...}` vrednost).
**And** `ops/secrets/README.md` tabela dobija backup var-ove: `RESTIC_PASSWORD`/`RESTIC_PASSWORD_FILE`, `RESTIC_REPOSITORY`, Storage Box host/user/SSH key path, GlitchTip notify DSN/URL, `RESTIC_IMAGE` (pinovan tag config var — NE secret, npr. `restic/restic:0.17.3`; SM-D12), `RESTORE_TARGET_DB`/`RESTORE_DB_URL` (restore-cilj config — default TEST DB, NIKAD prod; SM-D14), i (za rclone backend) `RCLONE_CONFIG`/`RCLONE_CONFIG_PATH` ako rclone.conf nije na default putanji.
**And** tabela jasno navodi da za **rclone backend** Storage Box host/user idu u rclone remote config (`rclone.conf` / `RCLONE_CONFIG`), NE direktno u shell skripte; za **sftp backend** host/user idu u `RESTIC_REPOSITORY` + SSH key path (SM-D5/G-12).
**And** `.env.example` (ako se dira) dobija PRAZNE placeholder-e, NIKAD realan secret.

**AC12 — 0 NOVIH MIGRACIJA / 0 NOVIH PYTHON DEP / regresija postojećih testova** (scope-disciplina)
**Given** 9.5 je ops-only (shell + cron + runbook)
**When** Dev završi
**Then** `makemigrations --check` = No changes (9.5 NE dira Django modele).
**And** NEMA novih Python runtime dep-ova NITI novih HOST binarki: restic NE ide na host — trči u pinovanom `restic/restic` Docker image-u (SM-D12); pg_dump kroz `postgres` servis (SM-D2); rclone config je creds-fajl (NE host-instalacija — rclone backend resolve-uje restic image ILI rclone binarka u image-u). `new_dependencies=0` = 0 host/Python deps (image-pull NIJE host dep).
**And** 9.2 deploy/secrets fajlovi + 9.3/9.4 NETAKNUTI; 9.6 ostaje backlog NETAKNUT.

---

## Tasks / Zadaci

### Task 1 — Web Intel (PRE koda; OBAVEZNO)
- [x] 1.1 Verifikuj aktuelan restic rclone-vs-sftp backend za Hetzner Storage Box (RESTIC_REPOSITORY format `rclone:<remote>:<path>` vs `sftp:user@host:/path`); potvrdi rclone remote config za Storage Box (`rclone config` SFTP tip).
- [x] 1.2 Potvrdi `restic forget --keep-daily 7 --keep-weekly 4 --keep-monthly 3 --prune` semantiku (snapshot grouping/policy) i `restic snapshots`-existence idempotency guard pattern. **Potvrdi i TAČAN pinovan `restic/restic:<tag>` image tag** (npr. `restic/restic:0.17.3`) za `RESTIC_IMAGE` (NIKAD `:latest` — SM-D12); upiši tačan tag u default.
- [x] 1.3 Potvrdi `pg_dump` kroz `docker compose exec -T postgres` (TTY-less za cron) + `--no-owner` + `--no-privileges` (preporučeno — čistiji restore u svež DB sa drugim role-ovima, G-16) flagove + `PGPASSWORD`/`.pgpass` env injection. Potvrdi i `gunzip | psql` restore put za plain dump (NE pg_restore — SM-D13).
- [x] 1.4 Potvrdi GlitchTip ingest/store URL format za thin curl notify (DSN → store endpoint).

### Task 2 — `ops/backup/pg_backup.sh` (NOVI; primarni deliverable) (AC1, AC2, AC4, AC8, AC9, AC10, AC11)
- [x] 2.1 Kreiraj `ops/backup/` direktorijum (NE postoji — `ops/` ima `deploy/`, `nginx/`, `secrets/`; ovo je NOV poddir). `mkdir`/`New-Item -ItemType Directory`.
- [x] 2.2 `#!/usr/bin/env bash` + `set -euo pipefail`, SCRIPT_DIR/REPO_ROOT resolve + `cd "${REPO_ROOT}"` (M6 mirror deploy.sh:34-36), LF (`.gitattributes:8` VERIFIKUJ, NE re-kreiraj).
- [x] 2.2a Definiši `RESTIC_IMAGE` env (pinovan tag, NE `:latest` — npr. `restic/restic:0.17.3`, potvrdi tačan tag kroz Task 1.2) + helper za restic invokaciju kroz `docker run --rm` (SM-D12). restic se NE instalira na host.
- [x] 2.2b RESTIC ENV PRE-FLIGHT GUARD (AC9/SM-D15): PRE init guard-a fail-loud ako je `RESTIC_REPOSITORY` prazan ILI su i `RESTIC_PASSWORD` i `RESTIC_PASSWORD_FILE` prazni — `[ -n "${RESTIC_REPOSITORY:-}" ] || { echo "RESTIC_REPOSITORY prazan"; exit 1; }` (i ekvivalent za password). Sprečava orphaned-repo (credential-fail pogrešno čitan kao „repo missing"). Prirodno u `_restic_common.sh` (G-14).
- [x] 2.3 restic-init idempotency guard (AC9/SM-D9) kroz `restic/restic` image — POSLE pre-flight guard-a (2.2b): `docker run --rm <creds> "${RESTIC_IMAGE}" snapshots >/dev/null 2>&1 || docker run --rm <creds> "${RESTIC_IMAGE}" init`.
- [x] 2.4 **plain-text** pg_dump PROTIV postgres servisa (AC1/SM-D2/SM-D13): `docker compose -f compose/production.yml exec -T postgres pg_dump -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" --no-owner --no-privileges` (NE custom `-Fc` — plain par zaključan; razmotri `--clean`) → **dump u temp fajl na deljenom host putanji** (npr. `${REPO_ROOT}/ops/backup/.tmp/` ili `/tmp` — gitignore temp dir). Credentials iz env (`${...}`/`PGPASSWORD`), NIKAD literali.
- [x] 2.5 gzip temp dump-a + OBAVEZAN NON-EMPTY ASSERT PRE restic koraka (AC8/SM-D7): `pipefail` aktivan; dump-u-temp → `test -s "${TMPFILE}"` AND size-floor/marker check (`-- PostgreSQL database dump`) → ako prazan/skoro-prazan: `exit` non-zero + notify_failure PRE restic-a. NIKAD `|| true`. (Goli pipefail-bez-asserta NIJE dovoljan — hvata pg_dump≠0 ali NE exit-0-prazan-dump.)
- [x] 2.6 restic push temp dump-a na Storage Box backend kroz `restic/restic` image (AC4/SM-D5/D12) — TEK kad assert (2.5) prođe: `docker run --rm -v <temp-dir>:/data -e RESTIC_REPOSITORY -e RESTIC_PASSWORD_FILE -v <rclone.conf ILI SSH key>:ro "${RESTIC_IMAGE}" backup /data/<dump> --tag db`. `RESTIC_REPOSITORY` (rclone primarni) + `RESTIC_PASSWORD`/`RESTIC_PASSWORD_FILE` kroz `-e` env-passthrough. Cleanup temp fajla posle push-a.
- [x] 2.7 Retention (AC2/SM-D1) kroz `restic/restic` image — GATE-ovan na uspeh push-a (2.6) (NIKAD pre/nezavisno; `set -e` prekida pre forget-a ako push padne — G-17): `docker run --rm <creds> "${RESTIC_IMAGE}" forget --keep-daily 7 --keep-weekly 4 --keep-monthly 3 --prune` — TAČAN flag-set, NE flat keep-daily 30.
- [x] 2.8 Fail-notify hook (AC10/SM-D8): `trap 'notify_failure' ERR` → `notify_failure()` `curl` GlitchTip ingest (DSN/URL iz env). THIN — NE 9.6 LOGGING. NIKAD literal DSN.

### Task 3 — `ops/backup/media_backup.sh` (NOVI; weekly restic snapshot) (AC3, AC4, AC8, AC9, AC10, AC11)
- [x] 3.1 `#!/usr/bin/env bash` + `set -euo pipefail` + SCRIPT_DIR/REPO_ROOT + LF.
- [x] 3.2 RESTIC ENV PRE-FLIGHT GUARD (AC9/SM-D15, deli `_restic_common.sh` sa 2.2b) + restic-init idempotency guard (AC9) + restic snapshot media volume (AC3/SM-D3/SM-D12) kroz pinovan `restic/restic` image koji mount-uje named volume DIREKTNO read-only u restic kontejner: `docker run --rm -v coric_agrar_production_media:/data:ro -e RESTIC_REPOSITORY -e RESTIC_PASSWORD_FILE -v <rclone.conf ILI SSH key>:ro "${RESTIC_IMAGE}" backup /data --tag media`. **NE `docker compose run` django/postgres image-a (ne isporučuju restic), NE host bind-path** (named volume root-only na hostu — Docker ga čini vidljivim UNUTAR restic kontejnera). `:ro` na volume-u.
- [x] 3.3 Isti Storage Box backend + encrypt (AC4) + isti `restic/restic` image (`RESTIC_IMAGE` deljen sa pg_backup.sh) + retention (zajednički helper ILI duplikat 7/4/3 — Rule of Three: ako se logika ponovi 3×, extract; za 2 skripte prihvatljiv sourced helper `ops/backup/_restic_common.sh` koji enkapsulira `docker run --rm "${RESTIC_IMAGE}" ...` wrapper + creds mount).
- [x] 3.4 Fail-loud pipe (AC8) + GlitchTip fail-notify hook (AC10). WEEKLY kadenca kroz cron (Task 5).

### Task 4 — `ops/backup/restore.sh` (NOVI; restore na lokal za test) (AC6, AC8, AC11)
- [x] 4.1 `#!/usr/bin/env bash` + `set -euo pipefail` + SCRIPT_DIR/REPO_ROOT + LF.
- [x] 4.2 Argument `$1` = `<snapshotID>`; fail-loud usage ako nedostaje (mirror deploy.sh:42-49 — `exit 2` + Usage poruka).
- [x] 4.2a RESTIC ENV PRE-FLIGHT GUARD (SM-D15, deli `_restic_common.sh`) PRE restic restore-a.
- [x] 4.2b RESTORE-TARGET DB guard (AC6/SM-D14 data-loss): čitaj `RESTORE_TARGET_DB` (ILI `RESTORE_DB_URL`) iz env, default = TEST DB; ako restore-cilj nije bezbedno postavljen → fail-loud. NIKAD fallback na prod `DATABASE_URL`/prod creds.
- [x] 4.3 restic restore kroz `restic/restic` image (SM-D12): `docker run --rm -v <restore-target>:/restore -e RESTIC_REPOSITORY -e RESTIC_PASSWORD_FILE -v <creds>:ro "${RESTIC_IMAGE}" restore "${SNAPSHOT_ID}" --target /restore` (lokal/test cilj) → `gunzip` → `psql` load u `RESTORE_TARGET_DB` (AC6/SM-D13/D14 — ISKLJUČIVO `gunzip | psql`, NE `pg_restore` jer je dump plain-SQL; NE prepisuj živu prod bazu; data-loss guard komentar).
- [x] 4.4 restic password/repo iz env (AC11), NIKAD literal.

### Task 5 — `ops/backup/crontab` (NOVI; daily 03:00 UTC + weekly media) (AC5, SM-D6)
- [x] 5.1 Kreiraj `ops/backup/crontab` (ILI dokumentovane `/etc/cron.d/coric-backup` linije): `0 3 * * *` → APSOLUTNA putanja `pg_backup.sh` (daily 03:00 UTC); `0 4 * * 0` → `media_backup.sh` (weekly, nedeljom 04:00 UTC). **Postavi `TZ=UTC` na vrhu crontab-a** (eksplicitno, ne oslanjaj se na box-TZ — G-8).
- [x] 5.1a (MEDIUM-6) Periodičan `restic check` integritet repo-a: komentovana cron linija (npr. weekly `restic check` ILI monthly `restic check --read-data-subset=...`) kroz `restic/restic` image — detektuje korupciju repo-a pre nego što zatreba restore. Dokumentuj u RESTORE.md.
- [x] 5.1b (MEDIUM-8) MESEČNI restore-test scaffold kao KOD artefakt (NE samo proza): komentovana crontab linija / kalendar-reminder stub u `ops/backup/` (npr. zakomentarisana `# 0 6 1 * * <owner> pokreni restore-test po RESTORE.md`) — schedule postoji u kodu; ljudski owner ostaje deferred (OQ-3).
- [x] 5.2 APSOLUTNE putanje (M6 — relativne fail-uju iz cron CWD, SM-D6). Cron radi na HOSTU (NE compose sidecar — SM-D6); sidecar OPCIONO, NE v1.
- [x] 5.3 Komentar: instalacija (`crontab ops/backup/crontab` ILI `cp` u `/etc/cron.d/`) + UTC napomena (cron `TZ=UTC` ili box-TZ je UTC).

### Task 6 — `ops/backup/RESTORE.md` runbook + mesečni restore-test (AC7, project-context:468)
- [x] 6.1 Kreiraj `ops/backup/RESTORE.md`: kako pokrenuti `restore.sh <snapshotID>`, `restic snapshots` listing, izbor snapshot-a.
- [x] 6.2 MESEČNI manual restore-test procedura (verify backup nije corrupted) + checklist (kockice): [ ] `restic snapshots` listano, [ ] restore-test izvršen, [ ] dump load u test DB bez grešaka, [ ] row-count/integrity sanity, [ ] datum + ko-je-radio.
- [x] 6.3 Retention (7/4/3) objašnjenje + restic-password offline-backup upozorenje (SM-D4) + pokaži na `ops/secrets/README.md` za creds (NE literali).
- [x] 6.4 (MEDIUM-7) `restic unlock` stale-lock napomena: ako je prekinut run (kill/OOM) ostavio stale repo lock, naredni cron tiho fail-uje zauvek („repository is already locked"). Dokumentuj kako ručno `docker run --rm <creds> "${RESTIC_IMAGE}" unlock` reši; opciono bounded stale-lock handling napomena u skriptama.
- [x] 6.5 (MEDIUM-6) Periodičan `restic check` integritet-check napomena (weekly/monthly) — kako pokrenuti + šta znači fail (repo korupcija).
- [x] 6.6 (SM-D14) Restore-cilj napomena: `RESTORE_TARGET_DB`/`RESTORE_DB_URL` default = TEST DB; restore.sh NIKAD ne prepisuje prod tiho; eksplicitno postaviti cilj pre restore-test-a.

### Task 7 — `ops/secrets/README.md` EDIT (+ opciono `.env.example`) (AC11, SM-D10)
- [x] 7.1 Dodaj sekciju/redove u `ops/secrets/README.md` box `.env` tabelu: `RESTIC_PASSWORD`/`RESTIC_PASSWORD_FILE`, `RESTIC_REPOSITORY` (rclone/sftp), Storage Box `STORAGE_BOX_HOST`/`STORAGE_BOX_USER`/SSH key path, `GLITCHTIP_BACKUP_NOTIFY_DSN`/URL, `RESTIC_IMAGE` (pinovan tag config — NE secret, default `restic/restic:<tag>`; SM-D12), `RESTORE_TARGET_DB`/`RESTORE_DB_URL` (restore-cilj config — default TEST DB, NIKAD prod; SM-D14), i (rclone backend) `RCLONE_CONFIG`/`RCLONE_CONFIG_PATH` ako rclone.conf nije na default putanji.
- [x] 7.1a Napomena u tabeli: za **rclone backend** Storage Box host/user idu u rclone remote config (`rclone.conf`/`RCLONE_CONFIG`), NE direktno u shell skripte; za **sftp backend** u `RESTIC_REPOSITORY` + SSH key path (SM-D5/G-12).
- [x] 7.2 (Opciono) `.env.example` backup placeholder-i (PRAZNI, NIKAD realan secret).
- [x] 7.3 Napomena: restic password se backup-uje ODVOJENO/offline (gubitak = nepovratan backup — SM-D4).

### Task 8 — (OPCIONO) compose backup sidecar (SM-D6) — DEFAULT: PRESKOČENO
- [ ] 8.1 OPCIONO — cron na HOSTU je default (SM-D6). Sidecar NE zahtevan; ako Dev odluči, dokumentuj u RESTORE.md zašto host-cron (jednostavnost + `docker compose` pristup + box `.env`). NE blokira nijedan AC.

### Task 9 — Tests (TEA piše RED; INFRA-VERIFY import-light) (AC1-AC12)
- [x] 9.1 `tests/test_backup_scripts.py` — import-light (`pathlib` + `re` SAMO; bez Django/libmagic): postojanje 3 skripte + cron + runbook.
- [x] 9.1a `bash -n` parse SVAKE skripte (sintaksa) — `subprocess` na `bash -n` AKO `bash` dostupan na hostu (Windows: Git-bash); inače grep-only fallback. (shellcheck/bats NISU instalirani — mirror 9.2 Task 9.6.)
- [x] 9.1b RETENTION LOCK (AC2/SM-D1): grep `ops/backup/*.sh` (sve skripte + opcioni `_restic_common.sh` — izbegni false-negative ako se logika extract-uje, MEDIUM-10) za TAČAN `--keep-daily 7`, `--keep-weekly 4`, `--keep-monthly 3`, `--prune`; asert NEMA `--keep-daily 30` flat.
- [x] 9.1c PG_DUMP CORRECTNESS (AC1/SM-D2/SM-D13): grep `exec -T postgres pg_dump` (ILI `run --rm`), `--no-owner`, `--no-privileges`, plain format (NE `-Fc`), `${POSTGRES_USER}`/`${POSTGRES_DB}` (env, NE literal), `compose/production.yml`.
- [x] 9.1d CRON LINT (AC5): grep `0 3 * * *` (03:00 UTC daily) + pg_backup poziv; weekly media poziv; APSOLUTNE putanje; **asert crontab sadrži `TZ=UTC`** (ILI dokumentuje UTC-host pretpostavku) — MEDIUM-9.
- [x] 9.1e FAIL-LOUD + NON-EMPTY ASSERT (AC8/SM-D7): grep `set -euo pipefail` u SVE 3 skripte; asert NEMA `|| true` na pg_dump/restic koraku; **asert prisutan non-empty dump check** (`test -s`/`[ -s`/size-floor/marker-grep `-- PostgreSQL database dump`) PRE restic push-a u pg_backup.sh (HIGH-1).
- [x] 9.1f RESTIC-INIT IDEMPOTENCY + PRE-FLIGHT GUARD (AC9/SM-D9/SM-D15): grep `ops/backup/*.sh` za init-only-if-missing guard pattern; **asert pre-flight guard** koji proverava `RESTIC_REPOSITORY`/`RESTIC_PASSWORD`(`_FILE`) ne-prazan PRE init guard-a (HIGH-4).
- [x] 9.1g ENCRYPT/ENV-SECRETS (AC4/AC11/SM-D10): grep `RESTIC_PASSWORD`/`RESTIC_PASSWORD_FILE` + `RESTIC_REPOSITORY` env-driven; NEGATIVE grep — NEMA `BEGIN PRIVATE KEY` / hardkodovan ne-prazan password literal.
- [x] 9.1j RESTIC-IMAGE DISCIPLINE (SM-D12/G-15): grep da restic ide kroz `docker run` + `restic/restic`/`${RESTIC_IMAGE}` (NE bare `restic ` host-poziv u backup koraku); asert `RESTIC_IMAGE` env-driven sa PINOVANIM tagom (NE `:latest`); media skripta grep `-v coric_agrar_production_media:` mount (NE host bind-path).
- [x] 9.1h GLITCHTIP FAIL-NOTIFY (AC10/SM-D8): grep `trap ... ERR`/`notify_failure` + env-driven GlitchTip DSN/URL (NE literal).
- [x] 9.1i RESTORE RUNBOOK (AC7): asert `ops/backup/RESTORE.md` postoji + sadrži „mesečno"/restore-test sekciju + restore.sh referencu + `restic unlock` stale-lock napomenu (MEDIUM-7) + `restic check` integritet napomenu (MEDIUM-6).
- [x] 9.1k RESTORE DATA-LOSS GUARD (AC6/SM-D14): grep restore.sh — asert čita `RESTORE_TARGET_DB`/`RESTORE_DB_URL`; **asert NE koristi prod `DATABASE_URL` kao default psql cilj**; asert restore load kroz `gunzip`+`psql` (NE `pg_restore` — SM-D13) (HIGH-2/HIGH-3).
- [x] 9.1l PRUNE-GATED (AC2/SM-D7): asert `restic forget --prune` dolazi POSLE push/non-empty-assert koraka u skript-toku (NE pre/nezavisno) (MEDIUM-5).
- [x] 9.2 Sve testove drži IMPORT-LIGHT (bez Django app importa, bez libmagic) — moraju trčati na Windows host-u I u CI. Stvarni restic/pg_dump/restore run = Docker/CI/box (NE host pytest).

### Task 10 — Manual review + scope guard (AC12)
- [x] 10.1 `makemigrations --check` = No changes (0 migracija). 0 novih Python dep-ova (verifikuj pyproject NETAKNUT).
- [x] 10.2 NE diraj: 9.2 deploy/rollback/secrets-9.2-redovi, 9.3 GlitchTip, 9.4 healthz, **9.6 LOGGING (backlog)**. NE pravi 9.6 Django LOGGING dict (fail-notify je THIN curl, SM-D8/D11).
- [ ] 10.3 (Ako box dostupan) smoke: `pg_backup.sh` STVARNO push-uje na Storage Box, `restore.sh <snap>` STVARNO restore-uje — kroz Docker/box (NE host).

---

## Gotchas

- **G-1 — LF line-endings OBAVEZNI.** Bash u Linux box-u/kontejneru NE tolerira CRLF (`\r` → `command not found`). `.gitattributes:8` `*.sh text eol=lf` VEĆ POSTOJI — VERIFIKUJ da pravilo važi za `ops/backup/*.sh`, NE re-kreiraj fajl (churn).
- **G-2 — pg_dump kroz `exec -T` (NO TTY) je OBAVEZAN za cron.** Bez `-T`, `docker compose exec` traži TTY → cron/non-interactive FAIL („the input device is not a TTY"). `postgres` servis NEMA host port → bare host `pg_dump -h localhost` = connection refused; MORA kroz `docker compose exec -T postgres` (SM-D2).
- **G-3 — `pipefail` MORA biti aktivan, inače pg_dump fail je TIHO maskiran.** `pg_dump | gzip` — bez `set -o pipefail`, exit-status je status POSLEDNJE komande, pa pg_dump fail (npr. DB down) → gzip uspešno-prazno → restic bi snapshot-ovao PRAZAN/korumpiran dump → exit 0 → „backup uspeo" laž. **REŠENJE (SM-D12/SM-D7):** `pg_dump` → gzip → **temp fajl** sa eksplicitnim size/exit-check PRE restic koraka; restic (`docker run --rm "${RESTIC_IMAGE}" backup`) se zove TEK kad je temp dump verifikovan ne-prazan/uspešan. `set -euo pipefail` aktivan. NAJGORI ishod = tihi fail. (NE pipe-uj pg_dump direktno u restic kontejner — dump-u-temp + check + push drži fail-check pre push-a i restic-invokaciju jednoobraznom.)
- **G-4 — restic init NIJE idempotentan po defaultu.** Drugi `restic init` na postojeći repo → fail „repository master key already exists". Guard (kroz `restic/restic` image — SM-D12): `docker run --rm <creds> "${RESTIC_IMAGE}" snapshots >/dev/null 2>&1 || docker run --rm <creds> "${RESTIC_IMAGE}" init` (init SAMO ako repo nedostaje — SM-D9/AC9). Mirror 9.2 certbot cert-existence guard.
- **G-5 — RETENTION: epics 7/4/3 NE flat-30 (REVIEW ZAMKA).** project-context:467 kaže „30 dana" → lako pogrešno `--keep-daily 30`. epics:1244 (SOT) = `--keep-daily 7 --keep-weekly 4 --keep-monthly 3 --prune`. SM-D1 reconcile: epics SOT. Test asertuje TAČNE brojeve (AC2).
- **G-6 — restic password gubitak = NEPOVRATAN backup.** restic encrypt je client-side; bez password-a repo je kriptografski nedostupan. Password MORA biti backup-ovan ODVOJENO/offline (NE samo na istom boxu koji backup-uješ — ako box izgori, izgubiš i password i pristup backup-u). Runbook upozorava (SM-D4/AC4/AC7).
- **G-7 — cron CWD nije repo root.** cron pokreće sa `$HOME` ili `/` CWD-om → relativne `compose/...`/`ops/...` putanje FAIL. Cron linije = APSOLUTNE putanje do skripti; skripte same rade SCRIPT_DIR/REPO_ROOT + `cd` (M6 mirror deploy.sh). (SM-D6/AC5)
- **G-8 — cron TZ = UTC.** epics/project-context traže 03:00 **UTC**. Box-TZ može biti lokalni → `0 3 * * *` bi bio lokalnih 3 ujutru, ne UTC. Postavi `TZ=UTC` u crontab-u (ILI box je UTC + dokumentuj). (AC5)
- **G-9 — media named volume se mount-uje DIREKTNO u pinovan `restic/restic` kontejner (read-only) — NE host bind-path, NE restic-na-hostu.** `coric_agrar_production_media` je named Docker volume; NIJE vidljiv na host bind-path-u bez root-a (Linux default `/var/lib/docker/volumes/coric_agrar_production_media/_data`, root-only) — zato „restic na hostu + bind-path" NE radi čisto. Ni `django` ni `postgres` image NE isporučuju restic. **REŠENJE (SM-D12):** pokreni zvanični pinovan `restic/restic` image kao prolazni `docker run --rm` i mount-uj named volume read-only DIREKTNO u njega — Docker ga čini vidljivim UNUTAR kontejnera (zaobilazi root-only host-path): `docker run --rm -v coric_agrar_production_media:/data:ro -e RESTIC_REPOSITORY -e RESTIC_PASSWORD_FILE -v <rclone.conf/SSH key>:ro "${RESTIC_IMAGE}" backup /data --tag media`. `:ro` (read-only) — backup NE sme pisati u media. Repo creds kroz `-e` env-passthrough + `-v` mount config-a/key-a. Ovo drži restic VAN hosta (`new_dependencies=0` konzistentno) i NIJE perzistentan sidecar (prolazni one-off run pomiruje SM-D6 „sidecar OPCIONO"). (AC3/SM-D3/SM-D12)
- **G-10 — restore.sh NE sme prepisati živu prod bazu tiho.** `restore.sh` je za restore-TEST na LOKAL/TEST cilj. Auto-restore u prod = data-loss rizik (mirror 9.2 rollback migrate-down svesnost). Eksplicitan komentar/guard + restore-target argument koji default-uje na test, NE prod (SM-D11/AC6).
- **G-11 — GlitchTip fail-notify je THIN, NE 9.6 logging.** `trap ERR` → `curl` GlitchTip ingest. NE gradi Django LOGGING dict / python-json-logger / logrotate (sve to je 9.6 backlog NETAKNUT). Prekoračenje = scope creep (SM-D8/D11).
- **G-12 — 0 literala — reuse 9.2 secret pattern.** restic password / Storage Box SSH key / rclone config / DB password / GlitchTip DSN — SVE box `.env`/`${...}`. NEGATIVE grep test (AC11). Mirror ops/secrets/README.md 9.2 disciplina.
- **G-13 — `rclone` vs `sftp` backend — oba validna, rclone primarni (epics).** epics kaže „via rclone" → `RESTIC_REPOSITORY=rclone:storagebox:path`. sftp je dokumentovana alternativa (`sftp:u123@u123.your-storagebox.de:/backup`). Ne hardkoduj — `RESTIC_REPOSITORY` env-driven (SM-D5/OQ-4).
- **G-14 — Rule of Three za zajednički restic helper.** pg_backup + media dele restic init-guard + retention + repo/password env + fail-notify + `docker run --rm "${RESTIC_IMAGE}"` wrapper. 2 skripte = prihvatljiv sourced helper `ops/backup/_restic_common.sh` (DRY bez over-abstract). NE 3 kopije; NE preuranjena framework apstrakcija.
- **G-16 — `--no-privileges` uz `--no-owner` za čistiji restore u svež DB.** Plain restore (`gunzip | psql`) u SVEŽ DB sa drugačijim role-ovima može fail-ovati na `GRANT ... TO <role-koji-ne-postoji>` / owner-stmt. `--no-owner` rešava owner; `--no-privileges` (ILI `-x`) rešava GRANT/REVOKE. **Preporučeno: oba** (`--no-owner --no-privileges`). Bezbedno je izostaviti `--no-privileges` SAMO ako restore-cilj ima identične role-ove kao izvor (retko za DR u svež box). (SM-D2/AC1)
- **G-17 — `restic forget --prune` MORA biti GATE-ovan na uspeh backup-a.** Ako prune/forget trči nezavisno od (ili pre) dump+push-a, niz LOŠIH run-ova (npr. DB down → prazan dump uhvaćen assert-om, ali forget ipak izvršen) može prune-ovati poslednji DOBAR snapshot → gubitak svih validnih backup-a. **REŠENJE:** forget je POSLE push-a u istom skript-toku, iza fail-loud guard-a (`set -e` + non-empty assert prekidaju PRE forget-a ako bilo šta padne). Nikad zaseban forget-cron koji ne zna za backup-status. (SM-D7/AC2)
- **G-18 — stale repo lock → tihi-fail-zauvek; `restic unlock` u runbook.** Prekinut restic run (kill/OOM/network drop) ostavi lock u repo-u; naredni run fail-uje „repository is already locked exclusively". Bez monitoringa, svaki naredni cron tiho fail-uje (do GlitchTip notify — AC10). Runbook dokumentuje ručno `docker run --rm <creds> "${RESTIC_IMAGE}" unlock`; opciono bounded auto-unlock u skriptama (pažljivo — unlock briše SVE lock-ove, ne pokreći ako drugi backup STVARNO trči). (MEDIUM-7)
- **G-19 — `restic check` integritet — repo korupcija je tiha do restore-a.** restic ne verifikuje repo-integritet pri svakom backup-u. Bit-rot/parcijalan upload/backend-bug može korumpirati repo, a otkriješ tek kad restore padne (najgori trenutak). **REŠENJE:** periodičan `restic check` (weekly) ILI `restic check --read-data-subset=<n%>` (monthly, čita stvarne podatke). Komentovana cron linija + runbook napomena. (MEDIUM-6)
- **G-20 — DUMP-FORMAT ↔ RESTORE mismatch fail-uje TEK pri restore-u (DR trenutak).** plain `pg_dump | gzip` se restore-uje SAMO kroz `gunzip | psql`; `pg_restore` traži custom (`-Fc`)/dir/tar format i odbija plain SQL („input file appears to be a text format dump. Please use psql."). Mešanje (plain dump + pg_restore restore) prolazi sve dok ne zatreba restore. **ZAKLJUČANO (SM-D13):** plain `pg_dump | gzip` ⇒ restore `gunzip | psql`; pg_restore NIJE u restore.sh. (AC1↔AC6)
- **G-21 — RESTIC ENV PRE-FLIGHT pre init-guard-a (orphaned-repo zamka).** `restic snapshots || restic init` (SM-D9) pretpostavlja da snapshots-fail znači repo-ne-postoji. ALI prazan/pogrešan `RESTIC_REPOSITORY`/`RESTIC_PASSWORD` takođe ruši `snapshots` → guard pogrešno kreira `init` ORPHANED repo (pogrešno mesto/prazne creds). `set -u` hvata UNSET ali NE postavljen-ali-prazan. **REŠENJE (SM-D15):** eksplicitan `[ -n "${RESTIC_REPOSITORY:-}" ]` + password check fail-loud PRE init-guard-a. (AC9)
- **G-22 — restore.sh restore-cilj NIKAD prod default (data-loss).** Ako restore.sh padne nazad na prod `DATABASE_URL`/`POSTGRES_*` kad `RESTORE_TARGET_DB` nije set, restore-test može PREPISATI živu prod bazu. **REŠENJE (SM-D14):** eksplicitan `RESTORE_TARGET_DB`/`RESTORE_DB_URL`, default TEST DB, NIKAD fallback na prod; fail-loud ako cilj nije bezbedno postavljen. Test asertuje. (AC6/G-10)
- **G-15 — restic se NIKAD ne instalira na host; SVE restic komande kroz pinovan `restic/restic` image (SM-D12).** `new_dependencies=0` = 0 host/Python deps; restic živi u svom image-u, NE kao host binarka. Razlozi: (1) ni django ni postgres image ne isporučuju restic; (2) named media volume root-only na hostu → mount u restic kontejner je jedini čist pristup. Zato `init`/`backup`/`forget`/`restore`/`snapshots` SVI idu kroz `docker run --rm -e RESTIC_REPOSITORY -e RESTIC_PASSWORD_FILE -v <data> -v <rclone.conf/SSH key>:ro "${RESTIC_IMAGE}" <subcommand>`. **PIN tag** (`RESTIC_IMAGE=restic/restic:<verzija>`, NIKAD `:latest` — mirror `glitchtip:v6.0` pin-disciplina iz 9.3). Prolazni `docker run --rm` NIJE perzistentan sidecar → pomiruje SM-D6 „sidecar OPCIONO" + host cron (cron i dalje na hostu, SAMO restic u image-u). NE pretvaraj ovo u long-running compose servis (to bi bio sidecar = OPCIONO, NE v1).

---

## Host caveat (za Dev/TEA)

Native Windows `pytest` **ne može da collect-uje pun suite** (libmagic missing — `python-magic` zahteva system `libmagic`; **pre-existing baseline, NIJE regresija ove story**). 9.5 testovi su dizajnirani da to zaobiđu:
- INFRA-VERIFY import-light (`pathlib` + `re` SAMO; bez Django app importa, bez libmagic) — file-parse + grep asercije trče na Windows host-u I u CI.
- `bash -n` parse kroz Git-bash AKO dostupan; inače grep-only fallback (shellcheck/bats NISU instalirani — mirror 9.2 Task 9.6).
- Stvarni `restic`/`pg_dump`/`restore` run = Docker/CI Linux ILI na boxu (sa restic/rclone instaliranim + Storage Box creds). NE host pytest. `needs_e2e=false`.

## Definition of Done

- [x] AC1-AC12 zadovoljeni
- [x] `ops/backup/pg_backup.sh` — pg_dump (exec -T postgres, --no-owner) → gzip → temp → restic encrypt push kroz pinovan `restic/restic` image (`docker run --rm`) → Storage Box, retention 7/4/3 --prune
- [x] `ops/backup/media_backup.sh` — restic snapshot media named volume kroz `restic/restic` image (volume mount :ro, NE host bind-path), weekly, encrypted
- [x] restic NIJE na hostu — SVE restic komande kroz pinovan `restic/restic:<tag>` image (`RESTIC_IMAGE` env, NE `:latest`); `new_dependencies=0` konzistentno (SM-D12)
- [x] `ops/backup/restore.sh` — restore `<snapshotID>` na lokal/test kroz `gunzip → psql` (NE pg_restore — SM-D13), `RESTORE_TARGET_DB` default TEST (NIKAD prod — SM-D14), fail-loud usage
- [x] `ops/backup/crontab` — daily 03:00 UTC (DB) + weekly (media), apsolutne putanje, `TZ=UTC`, komentovani `restic check` + mesečni restore-test scaffold
- [x] `ops/backup/RESTORE.md` — restore runbook + mesečni restore-test checklist + password-offline upozorenje + `restic unlock` stale-lock + `restic check` integritet napomene
- [x] Sve skripte `set -euo pipefail` + LF + SCRIPT_DIR/REPO_ROOT (M6); DB backup OBAVEZAN non-empty dump assert (`test -s`+size/marker) PRE restic push-a; `restic forget --prune` GATE-ovan na uspeh
- [x] restic-init idempotentan (init-only-if-missing) + RESTIC env pre-flight guard (ne-prazan REPOSITORY/PASSWORD PRE init-guard-a, SM-D15)
- [x] GlitchTip thin fail-notify hook (trap ERR → curl, env DSN); 9.6 LOGGING NETAKNUT
- [x] 0 literal secret-a; `ops/secrets/README.md` ažuriran sa backup var-ovima
- [x] `just lint` clean (ako primenljivo na shell — ruff Python-only; shell = bash -n)
- [x] TEA INFRA-VERIFY testovi prolaze (import-light; bash -n + grep)
- [x] 0 migracija (verifikovano) / 0 novih Python dep-ova (verifikovano)
- [x] 9.6 backlog NETAKNUT; 9.2/9.3/9.4 fajlovi NETAKNUTI

---

## Open Questions (go-live gates)

- **OQ-1 (go-live gate, manual) — Storage Box provisioning + creds.** Ko provisionira Hetzner Storage Box (account/subuser), koji `STORAGE_BOX_HOST`/`STORAGE_BOX_USER`, SSH key setup? **Mihas pre go-live.** restic repo path + rclone remote config. Box `.env` MORA imati creds pre prvog backup run-a.
- **OQ-2 (go-live gate) — GlitchTip backup-notify endpoint/DSN potvrda.** Tačan GlitchTip ingest/store URL + projekat/DSN za backup-fail notify (zaseban od Django app DSN-a 9.3?). **Mihas/infra.** Runbook placeholder `GLITCHTIP_BACKUP_NOTIFY_DSN`.
- **OQ-3 (go-live gate) — mesečni restore-test owner + kalendar.** Ko izvršava mesečni restore-test (project-context:468) i kada (kalendar/podsetnik)? **Mihas/operator.** Schedule je sada kod-artefakt (komentovan crontab/reminder stub u `ops/backup/`, Task 5.1b) + RESTORE.md checklist; SAMO ljudski owner ostaje deferred.
- **OQ-4 — rclone vs sftp backend finalni izbor.** epics primarni = rclone; sftp dokumentovana alternativa (SM-D5). Finalni izbor zavisi od Storage Box setup-a (OQ-1). **Mihas/infra na go-live.** `RESTIC_REPOSITORY` env-driven → bezbolan switch.
- **OQ-5 — cron na hostu vs compose sidecar.** v1 = host cron (SM-D6). Da li ikad treba compose backup sidecar (npr. ako box cron nije pouzdan / multi-box)? **DEFER — host cron je svesna v1 odluka; sidecar opciono.**
