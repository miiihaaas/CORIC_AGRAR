# Interface Contract — Story 9.2 Hetzner Deployment Script + SSL

> **Tip:** INFRA-VERIFY (`needs_e2e=false`). Deliverable-i su shell/YAML/nginx-conf fajlovi.
> Testovi (`tests/test_deployment_ssl.py`) su pure-Python file-parse (pathlib + re + yaml).
> Ovaj dokument enumeriše EGZAKTNE fajl-artefakte koje Dev mora kreirati/ažurirati i
> njihove ključne sadržaje, izvedene iz 15 AC i 9 Task-ova story-ja.
>
> Naming: srpska latinica + engleski identifikatori; **bez ćirilice**. LF za sve `.sh`.

---

## 0. Globalni invarijanti (svi `.sh` artefakti)

| Invariant | Vrednost | AC |
|-----------|----------|----|
| Shebang | `#!/usr/bin/env bash` | Task 2.2/3.1/4.1 |
| Fail-fast | `set -euo pipefail` | AC1/AC11 |
| Line endings | LF only (`.gitattributes:8` `*.sh text eol=lf` VEĆ postoji) | G-1 |
| Force-push | ZABRANJEN (`push --force`, `push -f`, `--force-with-lease`, `reset --hard origin`) | AC4 |
| Plaintext secret | ZABRANJEN (`BEGIN PRIVATE KEY`, hardkodovan ne-prazan `POSTGRES_PASSWORD=`) | AC5 |
| Ćirilica | ZABRANJENA u svim artefaktima | project-context |

---

## 1. `ops/deploy/deploy.sh` (NOVI — primarni deliverable)

Ordered deploy orkestracija. Koraci REDOM (SOT: project-context:447-454 + SM-D5):

1. **Dirty-tree guard** (Task 2.4a): `git status --porcelain` (ILI `git diff --quiet && git diff --cached --quiet`) → fail-loud exit non-zero ako je tree prljav. PRE `git pull`.
2. **Concurrency lock** (Task 2.4b): `flock`/lockfile (npr. `exec 200>/var/lock/coric-deploy.lock; flock -n 200 || exit 1`).
3. `git pull`
4. `docker compose -f compose/production.yml pull` — **STRIKTNO PRE** migrate/collectstatic/up (AC1/AC2/AC9; novi GHCR image).
5. ~~`uv sync --frozen`~~ — **UKLONJEN sa host-a (M3).** Frozen deps su BAKED u GHCR image (prod-builder stage radi `uv sync --frozen --no-dev` u build vremenu); bare host `uv sync` bi fail-ovao (uv mozda nije na boxu) ILI bio besmislen. Komentar-marker `BAKED u GHCR image` dokumentuje reconciliation sa project-context.
6. `python manage.py collectstatic --noinput` — PRE re-create-a.
7. `python manage.py migrate --plan` — pre-check, PRE `migrate` apply.
8. `python manage.py migrate` — **STRIKTNO PRE** `up -d django`/restart (AC2 ORDERING LOCK).
9. `python manage.py compilemessages`
10. `docker compose -f compose/production.yml up -d django` (re-create; NE goli `restart` — SM-D5).
11. `docker compose -f compose/production.yml up -d nginx` ILI `exec nginx nginx -s reload` (pokupi bind-mount conf — AC14/SM-D9).
12. **Healthcheck** (AC10/M4): `docker compose exec -T django python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/sr/', timeout=5)"` retry-loop POSLE re-create-a → fail deploy ako ne 2xx (urlopen raise HTTPError). **UNUTAR django kontejnera** (M4) — production.yml NE izlaze :8000 na host (bare host curl = connection refused). Python urllib (NE curl) jer prod image nema curl.

Markeri: idempotency invariant komentar (AC3), `migrate` PRE re-create komentar (AC2), `pull` PRE migrate komentar (AC1/AC9).
Argument `$1` = environment (`staging`|`production`); fail-loud usage ako nedostaje.

**Ključni kontrakti (test-locked):**
- `set -euo pipefail` prisutan.
- ORDERING: `index(docker compose pull)` < `index(migrate apply)` < `index(up -d django)`.
- ORDERING: `index(migrate --plan)` < `index(migrate apply)`.
- ORDERING: `index(collectstatic)` < `index(up -d django re-create)`.
- nginx reload/re-create korak prisutan (NE samo restart django).
- **Healthcheck (AC10) prisutan** (`curl -fsS`/`check --deploy`) **i POZICIONO POSLE** `up -d django`/`up -d nginx` re-create-a (ordering lock — healthcheck verifikuje NOVE kontejnere).
- **Dirty-tree guard** (`git status --porcelain` ILI `git diff --quiet`) + **concurrency lock** (`flock`/lockfile) prisutni (Task 2.4a/2.4b — best-effort lock).
- NEMA `--force`/`push -f`.

## 2. `ops/deploy/rollback.sh` (NOVI)

- `#!/usr/bin/env bash` + `set -euo pipefail` + LF.
- `git checkout <tag/commit>` (argument ILI `git describe --tags --abbrev=0 HEAD^`) → re-deploy.
- **Irreversible-migration WARNING** (Task 3.4a/AC11): GLASNO upozorenje na stderr PRE redeploy-a (drop/rename kolone, destruktivan data-transform → ručna DBA intervencija).
- **NO auto-migrate-down** default (SM-D3, data-loss); opcioni `migrate <app> <target>` SAMO ako eksplicitno dat.
- NEMA force-push (AC4).

## 3. `ops/nginx/nginx-init.sh` (NOVI — certbot + bootstrap)

- `#!/usr/bin/env bash` + `set -euo pipefail` + LF.
- `DOMAIN` (default `coricagrar.rs`) + `ACME_EMAIL` parametrizovani (env/arg) — AC6/SM-D2.
- **BOOTSTRAP sekvenca** (AC15/SM-D10): (1) nginx sa `nginx.bootstrap.conf` (HTTP-only) → :80 ACME, (2) `certbot certonly --webroot -w /var/www/certbot ...` izda cert, (3) swap na pun `nginx.conf`, (4) `up -d nginx`/`exec nginx -s reload`.
  - Positional: bootstrap conf reference PRE certbot poziva; pun nginx.conf swap POSLE.
- **Idempotency guard**: ako `/etc/letsencrypt/live/$DOMAIN/fullchain.pem` postoji → preskoči.
- **Auto-renewal** (AC6/Task 4.5): cron (`certbot renew`) ILI systemd timer + `--deploy-hook` koji reload-uje nginx (`docker compose ... exec nginx nginx -s reload`).
- **Renewal-failure visibility** (Task 4.5a): `|| echo "CERT RENEWAL FAILED ..." >&2` ILI systemd `OnFailure=`.
- Webroot path `/var/www/certbot` dokumentovan komentarom (path-contract marker).

## 4. `compose/nginx/nginx.bootstrap.conf` (NOVI — HTTP-only bootstrap)

- `:80` blok sa `location /.well-known/acme-challenge/ { root /var/www/certbot; }` + static/media/proxy.
- **NEMA nijedan `listen 443 ssl`** (AC15/Task 9.2b).

## 5. `compose/nginx/nginx.conf` (UPDATE — aktiviraj 443)

- `listen 443 ssl;` AKTIVAN (ne zakomentarisan) blok.
- `ssl_certificate /etc/letsencrypt/live/<domen>/fullchain.pem;` + `ssl_certificate_key .../privkey.pem;`.
- `ssl_protocols TLSv1.2 TLSv1.3;`.
- `:80` blok: `location /.well-known/acme-challenge/ { root /var/www/certbot; }` — **NE redirect-uje** (ostaje 200/404).
- `:80` blok: `return 301 https://$host$request_uri;` za sav OSTALI saobraćaj (BEZUSLOVAN, SM-D6).
- 443 blok re-emituje sva 3 security headera (`X-Frame-Options DENY`, `X-Content-Type-Options nosniff`, `Referrer-Policy same-origin`, svaki `always`).
- 443 blok: `proxy_set_header X-Forwarded-Proto $scheme` (G-3), `location /static/` + `/media/`.
- gzip ostaje.

## 6. `compose/production.yml` (UPDATE — nginx bind-mounts)

nginx servis `volumes:` DODAJ (EXTEND, ne re-write — SM-D4/SM-D9/M1):
- `- ./nginx/.active-default.conf:/etc/nginx/conf.d/default.conf:ro` (**M1 swappable conf** — bind-mount cilja `.active-default.conf` koji nginx-init.sh popunjava bootstrap conf-om PRE certbot-a i punim nginx.conf-om POSLE; deploy.sh kopira nginx.conf→.active-default.conf pre svakog nginx re-create-a. Mount-ovanje direktno nginx.conf-a bi ucinilo bootstrap swap INERTNIM → prvi cert se nikad ne izda).
- `- /etc/letsencrypt:/etc/letsencrypt:ro` (cert read-only — AC13).
- `- /var/www/certbot:/var/www/certbot:ro` (ACME webroot read-only — AC13).
- **django `image:` je GHCR-pathed (M2):** `ghcr.io/${GHCR_IMAGE:-miiihaaas/coric_agrar}:${IMAGE_TAG:-latest}` da `docker compose pull` na boxu resolve-uje CI-build (lokalno ime se ne moze pull-ovati). `build:` blok ostaje (lokalni fallback).
- postgres servis NETAKNUT; mora ostati validan YAML.
- `.active-default.conf` je u `.gitignore` (generisan/runtime fajl — M1).

## 7. `.github/workflows/deploy.yml` (NOVI)

- Validan YAML.
- `on: push: branches: [staging, main]` (SM-D1/OQ-1 — test asertuje OVU vrednost, sa fallback tolerancijom za `[master]` ako Mihas zadrži default).
- `permissions: contents: read` (least-privilege).
- SSH na Hetzner kroz `${{ secrets.* }}` (`DEPLOY_SSH_KEY`/`DEPLOY_HOST`/`DEPLOY_USER`/`DEPLOY_APP_DIR`/`DEPLOY_HOST_FINGERPRINT`) — NIKAD hardkodovan ključ/host.
- **M5:** `DEPLOY_APP_DIR` guard — fail-loud (`[ -z "$APP_DIR" ] && exit 1`) pre `cd` (prazan `cd ""` = pogresan CWD).
- **M8 (SECURITY):** `fingerprint: ${{ secrets.DEPLOY_HOST_FINGERPRINT }}` (host-key pinning protiv MITM-a); `appleboy/ssh-action` SHA-pinovan (`@2ead5e36...` = v1.2.2) jer rukuje SSH kljucem.
- Remote poziva `ops/deploy/deploy.sh <env>`.
- NEMA plaintext secret-a; NEMA `build-push-action` (deploy.yml NE gradi — SM-D7).

## 8. `.github/workflows/ci.yml` (UPDATE — GHCR push aktiviran)

build job (KANONSKA GHCR lokacija — AC9/SM-D7):
- `docker/login-action@v3` (registry `ghcr.io`, `${{ secrets.GITHUB_TOKEN }}`).
- `docker/build-push-action` `push: true` (bilo `false` u 9.1).
- lowercase image-name pattern + `:ci-<sha>` tag NETAKNUTI (regresija).
- **M2: dodatni STABILAN per-branch tag** (`:${STABLE_TAG}` — master→latest, staging→staging, main→production) pored `:ci-<sha>` da deploy.sh `docker compose pull` (production.yml default `:latest`) resolve-uje stabilan tag, ne sha.
- `needs: [lint, test]` redosled NETAKNUT.

## 9. `.env.example` (UPDATE — deploy placeholders)

- `DEPLOY_DOMAIN=` / `ACME_EMAIL=` (prazni placeholderi).
- Komentar za `DEPLOY_HOST`/`DEPLOY_USER`/`DEPLOY_SSH_KEY` (idu kroz GH secrets, NE .env).
- NIKAD realne vrednosti (AC5).

## 10. `ops/secrets/README.md` (NOVI)

- Lista zahtevanih GitHub Actions secrets (`DEPLOY_SSH_KEY`, `DEPLOY_HOST`, `DEPLOY_USER`).
- Box `.env` lista (`POSTGRES_PASSWORD`, `DJANGO_SECRET_KEY`, ...).
- **SSH least-privilege guidance** (Task 7.2a): `command="..."` forced-command, `no-pty`, non-root deploy user.
- NIKAD realne vrednosti.

---

## Key cross-cutting contracts (LOCKED)

1. **Cert-path `/var/www/certbot`** identičan na 3 mesta: `nginx-init.sh` certbot `-w`, `nginx.conf` ACME `root`, `production.yml` bind-mount (AC13/SM-D4).
2. **migrate-before-restart** ordering (AC2): `migrate` apply STRIKTNO PRE `up -d django`.
3. **docker-pull-before-migrate** (AC1/AC9): `docker compose pull` PRE migrate/collectstatic/up.
4. **bootstrap-no-443** (AC15): `nginx.bootstrap.conf` NEMA `listen 443 ssl`.
5. **GHCR-in-ci.yml** (AC9/SM-D7): GHCR login+push u `ci.yml` build job, NE u deploy.yml.

---

## AC → artefakt → test pokrivenost (sažeto)

| AC | Artefakt | Ključni assert |
|----|----------|----------------|
| AC1 | deploy.sh | set -euo pipefail, git pull, docker compose pull, uv sync --frozen, collectstatic, migrate, compilemessages, up -d |
| AC2 | deploy.sh | ORDERING: pull < migrate < up -d; --plan < migrate; collectstatic < up -d |
| AC3 | deploy.sh | idempotency marker, --noinput |
| AC4 | deploy.sh, rollback.sh | NEMA --force/push -f |
| AC5 | svi novi fajlovi, .env.example, README | NEMA BEGIN PRIVATE KEY / hardkodovan pw |
| AC6 | nginx-init.sh | certbot certonly --webroot, auto-renewal, renewal-failure visibility, idempotency |
| AC7 | nginx.conf | listen 443 ssl, ssl_certificate(_key), ACME location root /var/www/certbot (no redirect), 301 redirect, **3 headera + X-Forwarded-Proto UNUTAR 443 server bloka** (test scope-ovan na 443 blok — 9.1 :80 headeri NE zadovoljavaju 9.2 kontrakt) |
| AC8 | deploy.yml | trigger branches, SSH via secrets, poziva deploy.sh, no plaintext |
| AC9 | ci.yml | docker/login-action, push: true |
| AC10 | deploy.sh | healthcheck korak prisutan (`curl -fsS`/`check --deploy`) + POSITIONAL: healthcheck POSLE `up -d django`/`up -d nginx` re-create-a (ordering lock) |
| AC11 | rollback.sh | checkout, irreversible-migration warning, no force-push |
| AC12 | (0 migracija — out-of-band; ne file-parse) | n/a |
| AC13 | nginx-init.sh, nginx.conf, production.yml | -w path == ACME root == /var/www/certbot; bind-mounts |
| AC14 | production.yml, deploy.sh | nginx.conf bind-mount; nginx reload korak |
| AC15 | nginx.bootstrap.conf, nginx-init.sh | bootstrap exists, no 443, bootstrap-before-certbot ordering |
