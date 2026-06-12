---
story-id: 9-2-hetzner-deployment-script-ssl
title: Hetzner Deployment Script + SSL
status: review
epic: 9
epic-title: Go-Live Readiness (Production + Quality)
risk_tier: HIGH
needs_e2e: false
test_approach: INFRA-VERIFY (pure-Python file parsing — pathlib + yaml + regex; bez Django/libmagic importa)
depends_on:
  - 9-1-production-docker-compose-nginx-config
  - 1-9-github-actions-ci-pipeline
forward:
  - 9-3-glitchtip-6-self-host-setup
  - 9-5-pg-dump-restic-hetzner-storage-box-backup
  - 9-8-playwright-e2e-testovi-za-3-uj-a
created_by: SM (autonomous)
created_date: 2026-06-12
---

# Story 9.2 — Hetzner Deployment Script + SSL

## Opis

Kao **dev**, želim **skriptovan, reproducibilan deploy proces na Hetzner VPS sa Let's Encrypt SSL-om**, da bi **deploy bio idempotentan, siguran i automatski pokrenut iz CI/CD-a po push-u na deploy branch**.

Ova story je naslednik Story 9.1 (production Docker stack). 9.1 je isporučio `compose/production.yml`, `compose/nginx/nginx.conf` (HTTP/80 FUNKCIONALAN, HTTPS/443 PLACEHOLDER zakomentarisan), `compose/django/start.sh` (Gunicorn, NE migrira). 9.2 isporučuje **operativni sloj iznad toga**:

1. `ops/deploy/deploy.sh` — deploy orkestracija na Hetzner box-u (git pull → docker compose pull → uv sync --frozen → collectstatic → migrate --plan → migrate → compilemessages → up -d django (re-create) → up -d nginx/reload → healthcheck), idempotentna, sa eksplicitnim ORDERING-om (pull PRE migrate-a, migrate PRE re-create-a Gunicorn-a).
2. `ops/deploy/rollback.sh` — checkout prethodnog tag-a/commit-a + redeploy (NIKAD force push; `git revert` filozofija).
3. `ops/nginx/nginx-init.sh` — certbot provisioning (Let's Encrypt webroot challenge) + auto-renewal (cron ~1x mesečno).
4. `compose/nginx/nginx.conf` 443/HTTPS extension — odkomentariši i parametrizuj placeholder blok + dodaj HTTP→HTTPS redirect (osim ACME challenge-a) + ACME challenge location.
5. `.github/workflows/deploy.yml` — NOVI workflow, trigger na deploy branch-eve, SSH na Hetzner box kroz GitHub Actions secrets, poziva `ops/deploy/deploy.sh`; ujedno dodaje DEFERRED GHCR login+push iz 9.1 build job-a.
6. `.env.example` deploy placeholder-i (domen, ACME email, deploy host/user) + `ops/secrets/README.md` (lista zahtevanih GH secrets).
7. `justfile` deploy recepti (opciono, ako prirodno).

**Test pristup: INFRA-VERIFY (`needs_e2e=false`).** NE Playwright. Sledi USTALJEN pattern projekta (`tests/test_production_stack.py`, `tests/test_ci_workflow_config.py`): pytest parsira shell/YAML/conf fajlove i tvrdi kontrakt kroz grep-lock-ove + strukturne provere. Novi 9.2 testovi MORAJU biti import-light (samo `pathlib` + `yaml` + `re`) — bez Django app importa i bez libmagic — da se izvršavaju i na Windows host-u i u Docker/CI. **shellcheck/bats NISU instalirani na host-u → testovi su čisto Python file-inspekcija, NE subprocess shellcheck.**

## Acceptance Criteria

> Mapiranje na epics.md Story 9.2 "When/And/Then". Svaki AC je konkretan i testabilan kroz INFRA-VERIFY (file-parse) testove.

**AC1 — `ops/deploy/deploy.sh` postoji i ima deploy korake (epics: "git pull, docker compose pull, down+up, migrate, collectstatic").**
**Given** production compose iz 9.1
**When** Dev kreira `ops/deploy/deploy.sh`
**Then** skripta sadrži, redom: `git pull`, `docker compose -f compose/production.yml pull` (povlači NOVI GHCR image PRE migrate/collectstatic — AC9 push; epics:1204 lista `docker compose pull`; SM-D5), `uv sync --frozen`, `python manage.py collectstatic --noinput`, `python manage.py migrate --plan` (assertion/pre-check korak), `python manage.py migrate`, `python manage.py compilemessages`, re-create Django servisa sa novim image-om (`docker compose -f compose/production.yml up -d django`; goli `restart` ne menja image — SM-D5), pa re-create/reload nginx-a (`docker compose -f compose/production.yml up -d nginx` ILI `exec nginx nginx -s reload` da pokupi novi bind-mount-ovan nginx.conf — SM-D9).
**And** `docker compose pull` je STRIKTNO PRE `migrate`/`collectstatic` (koji se izvršavaju kroz novi image) i PRE `up -d django` re-create-a (ordering lock — vidi AC2).
**And** skripta počinje sa `set -euo pipefail` i ima LF line-endings (G-1: bash u Linux kontejneru/boxu ne tolerira CRLF).

**AC2 — ORDERING LOCK: migrate IZVRŠAVA PRE restart-a Gunicorn-a (deploy.sh korak 5 pre koraka 7).**
**Given** deploy korake iz project-context:447-454
**When** test parsira `ops/deploy/deploy.sh`
**Then** pozicija `manage.py migrate` (apply, ne `--plan`) je STRIKTNO PRE pozicije `up -d django`/`restart django`/gunicorn re-create-a u fajlu.
**And** `migrate --plan` (pre-check) je PRE `migrate` (apply).
**And** `collectstatic` je prisutan PRE re-create-a (static volume mora biti svež kad Nginx počne da servira).
**And** `docker compose pull` (povlačenje novog GHCR image-a) je STRIKTNO PRE `migrate`/`collectstatic`/`up -d` (inače migrate/collectstatic teku kroz STARI image i re-create povlači stari kod — SM-D5; epics:1204).
**Razlog:** šema baze mora biti migrirana pre nego novi Gunicorn worker-i počnu da služe (inače novi kod udara u staru šemu). Ovaj redosled je INHERENTNI deploy ugovor (forward-dep iz 9.1) i MORA biti zaključan testom.

**AC3 — IDEMPOTENCY: ponovno pokretanje istog deploy-a NE menja stanje / ne pada (project-context:477).**
**Given** deploy.sh
**When** test parsira skriptu
**Then** koraci su idempotentni: `collectstatic --noinput` (ne interaktivan), `migrate` (Django migrate je već idempotentan), `uv sync --frozen` (deterministički iz lock-a), `compilemessages` (overwrite .mo). NEMA `--no-input`-manjkavih interaktivnih komandi.
**And** skripta dokumentuje idempotency invariantu komentarom (marker za grep-lock).

**AC4 — NO FORCE-PUSH: ni deploy.sh ni rollback.sh ne smeju `push --force` / `--force` / `reset --hard origin` na deljeni branch (project-context:456 "NIKAD force push").**
**Given** deploy + rollback skripte
**When** test grep-uje obe skripte
**Then** NEMA `git push --force`, `git push -f`, `--force-with-lease` na remote deploy branch. Rollback koristi `git checkout <tag>` / `git revert`, NE force-rewrite istorije.

**AC5 — SECRET INJECTION: POSTGRES_PASSWORD i ostali secret-i se injektuju kroz env/.env na Hetzner box-u, NIKAD komitovani u repo (forward-dep iz 9.1).**
**Given** 9.1 prazan `POSTGRES_PASSWORD:-` default (prod MORA injektovati)
**When** Dev wire-uje secret handling
**Then** `deploy.sh` se oslanja na `.env` na box-u (van Git-a) ILI shell/Hetzner env — NE generiše/embed-uje secret u repo fajl.
**And** `.env.example` dobija deploy placeholder-e (prazne vrednosti / komentar), ali NIKAD realan secret.
**And** `ops/secrets/README.md` dokumentuje koje secret-e box mora imati i odakle (Hetzner secrets panel).
**And** NEGATIVE test: ni jedan novi fajl (deploy.sh, rollback.sh, nginx-init.sh, deploy.yml, .env.example, README) NE sadrži plaintext password/private key (grep na sumnjive patterne: `BEGIN PRIVATE KEY`, hardkodovan `POSTGRES_PASSWORD=<nešto-ne-prazno-ne-${...}>`).

**AC6 — CERT PROVISIONING + AUTO-RENEWAL: `ops/nginx/nginx-init.sh` izdaje Let's Encrypt cert pri prvom deploy-u i obnavlja ga ~1x mesečno (epics: "HTTPS certifikat se izdaje pri prvom deploy-u i obnavlja se 1x mesečno").**
**Given** nginx 443 placeholder iz 9.1
**When** Dev kreira `ops/nginx/nginx-init.sh`
**Then** skripta poziva `certbot certonly --webroot -w /var/www/certbot` (webroot LOCKED — Nginx već sluša :80 sa ACME location-om; webroot path je KONKRETAN `/var/www/certbot`, usklađen sa nginx ACME alias-om i production.yml bind-mount-om — AC13/SM-D4) za izdavanje cert-a za domen (parametrizovan env-om, default `coricagrar.rs` + `www.`).
**And** skripta SPROVODI first-deploy BOOTSTRAP sekvencu (AC15/SM-D10): nginx HTTP-only (bootstrap conf bez 443) → certbot izda cert → swap na pun conf (443 aktivan) → reload. Idempotentno: preskače izdavanje ako cert već postoji.
**And** skripta registruje auto-renewal (cron `certbot renew` ILI systemd timer) sa `--deploy-hook` koji reload-uje Nginx (`docker compose exec nginx nginx -s reload`).
**And** ACME email i domen su parametrizovani (env var / argument), ne hardkodovani gde je razumno.
**And** webroot metod + webroot path `/var/www/certbot` su dokumentovani komentarom u skripti (path-contract marker).

**AC7 — NGINX 443/HTTPS EXTENSION: nginx.conf 443 blok je AKTIVAN (ne zakomentarisan) sa ssl_certificate putanjama, HTTP→HTTPS redirect-om i ACME challenge location-om.**
**Given** 9.1 zakomentarisan 443 placeholder (linije ~87-136)
**When** Dev odkomentariše/parametrizuje 443 blok
**Then** nginx.conf ima `listen 443 ssl;` aktivan blok sa `ssl_certificate` + `ssl_certificate_key` (putanje `/etc/letsencrypt/live/<domen>/fullchain.pem` + `privkey.pem`).
**And** HTTP/80 blok dodaje `location /.well-known/acme-challenge/` sa `root /var/www/certbot;` (KONKRETAN webroot path — usklađen sa certbot `-w` i production.yml bind-mount-om, AC13/SM-D4) koji vraća sadržaj (NE redirect-uje se na HTTPS; ostaje 200/404 sa webroot-a).
**And** HTTP/80 blok redirect-uje SAV ostali saobraćaj na HTTPS (`return 301 https://$host$request_uri;`) OSIM ACME challenge location-a (redirect je BEZUSLOVAN/prod-realan, NE env-uslovljen — SM-D6).
**And** 443 blok re-emituje sva 3 security headera (`X-Frame-Options DENY`, `X-Content-Type-Options nosniff`, `Referrer-Policy same-origin` — svaki sa `always`), `location /static/` + `/media/` direktan serving, `proxy_set_header X-Forwarded-Proto $scheme` (G-3: bez ovoga 301 loop), `ssl_protocols TLSv1.2 TLSv1.3`.
**And** REGRESSION (test-ownership LOCKED, SM-D6): 9.1 HTTP/80 `location /static/`, `/media/`, security headeri, `proxy_pass django` ostaju netaknuti na :80 (struktura). Pošto :80 sada radi `return 301 https://` za `/sr/`, 9.1 smoke test **`test_ac8_container_smoke_http_200_and_security_headers`** (u `tests/test_production_stack.py`, `@pytest.mark.docker`) PRELAZI u vlasništvo ove story (9.2) i SVESNO se ažurira da: (a) prati redirect (`allow_redirects=True` / `curl -IL`) i tvrdi sletanje na 200 sa HTTPS, ILI (b) tvrdi `:80 /sr/` → 301 sa `Location` koji počinje `https://`; PLUS novi assert da `GET http://.../.well-known/acme-challenge/<probe>` NE redirect-uje (200/404, NIKAD 301). Ova izmena je IMENOVANA u AC12 kao jedina dozvoljena izmena 9.1 testova.

**AC8 — DEPLOY.YML SSH: `.github/workflows/deploy.yml` postoji, trigger-uje na deploy branch, SSH na Hetzner kroz GitHub Actions secrets, poziva `ops/deploy/deploy.sh`.**
**Given** postojeći `.github/workflows/ci.yml` (trigger master)
**When** Dev kreira NOVI `deploy.yml`
**Then** workflow trigger-uje na push na deploy branch-eve (SM-D1: `staging` + `main` per project-context go-live naming; OQ-1 master→main reconciliation).
**And** koristi SSH key + host + user kroz `${{ secrets.* }}` (npr. `appleboy/ssh-action@v1` ILI raw `ssh` sa `webfactory/ssh-agent`), NIKAD hardkodovan privatni ključ/host/lozinku.
**And** remote komanda poziva `ops/deploy/deploy.sh <env>` (env iz branch-a: staging branch → staging, main → production).
**And** least-privilege `permissions:` (contents: read na workflow nivou).
**And** NEGATIVE: NEMA plaintext secret-a u YAML-u (grep: nema `BEGIN ... PRIVATE KEY`, nema inline IP/host literal-a gde secret očekivan).

**AC9 — GHCR LOGIN + PUSH (deferred iz 9.1 build job-a).**
**Given** `ci.yml` build job sa komentarom "placeholder za Story 9.2 GHCR push" / "NEMA docker/login-action ... DEFERRED do Story 9.2"
**When** Dev aktivira deferred push
**Then** image se log:in-uje na GHCR (`docker/login-action@v3` sa `${{ secrets.GITHUB_TOKEN }}` / registry `ghcr.io`) i push-uje (`push: true`) **u `ci.yml` build job-u (KANONSKA lokacija — LOCKED, SM-D7)**, sa `packages: write` job-level permission (već postoji u ci.yml build job-u). `deploy.yml` SAMO SSH-uje i pokreće `deploy.sh`; NE gradi/push-uje image (izbegava dupli build + dvosmislen test-kontrakt).
**And** image tag je deterministički (`ghcr.io/<repo-lowercase>:<sha>` i/ili `:latest` na deploy branch).
**And** KONZUMACIJA: image push-ovan ovde MORA biti povučen na box-u kroz `docker compose pull` korak u deploy.sh (AC1/AC2) PRE re-create-a — inače box pokreće STARI image i posle GHCR push-a. production.yml django servis `image:` tag mora referencirati GHCR putanju koju ovaj job push-uje (ILI deploy.sh `pull` cilja taj image) da bi `pull` povukao sveže izgrađen image.
**And** REGRESSION: `ci.yml` lint+test+build redosled (`needs: [lint, test]`) i lowercase image-name pattern netaknuti.

**AC10 — HEALTHCHECK posle restart-a (forward-dep iz 9.1).**
**Given** deploy.sh restart Django-a
**When** Dev dodaje post-restart verifikaciju
**Then** deploy.sh, posle re-create-a (`up -d django`/`up -d nginx`), izvršava healthcheck (npr. `curl -fsS https://<domen>/sr/ -o /dev/null` ILI `docker compose exec django python manage.py check --deploy` ILI retry-loop na lokalni `:8000`/`https`) i fail-uje deploy (non-zero exit) ako app ne odgovori.
**And** healthcheck poziciono dolazi POSLE re-create-a (parse-ordering lock).

**AC11 — ROLLBACK: `ops/deploy/rollback.sh` revertuje na prethodni tag/commit + redeploy (epics: "rollback može da revertuje na prethodni commit + migrate down").**
**Given** deploy.sh
**When** Dev kreira `ops/deploy/rollback.sh`
**Then** skripta `git checkout <prethodni-tag-ili-commit>` (argument / detektovan prethodni tag), pa re-pokreće deploy (poziva deploy.sh ILI inline collectstatic+restart).
**And** skripta tretira migrate-down SVESNO: ILI `migrate <app> <prethodna_migracija>` (samo ako je dato/sigurno) ILI eksplicitan komentar/upozorenje da migrate-down nije automatski (data-loss rizik) sa uputstvom za ručni rollback (SM-D3: migrate-down je opasna operacija — vidi OQ).
**And** `set -euo pipefail` + LF + NEMA force-push (deljeno sa AC4).

**AC12 — 0 NOVIH MIGRACIJA / 0 NOVIH RUNTIME DEP / regresija postojećih testova.**
**Given** 9.2 je INFRA/ops-only (shell + YAML + nginx conf)
**When** Dev završi
**Then** `makemigrations --check` = No changes (9.2 NE dira Django modele).
**And** NEMA novih Python runtime dep-ova (certbot/ssh su sistem/CI alati, ne Python paketi).
**And** 9.1 `tests/test_production_stack.py` non-docker testovi ostaju zeleni. JEDINA dozvoljena izmena 9.1 testova (test-ownership prelazi na 9.2, SM-D6): **`test_ac8_container_smoke_http_200_and_security_headers`** se SVESNO ažurira da prati 80→443 redirect (vidi AC7) — IMENOVAN ovde kao owned/updated test. NIJEDAN drugi 9.1 test se ne menja. Bind-mount nginx.conf-a (SM-D9) NE menja sadržaj conf-a koji 9.1 non-docker testovi parsiraju → struktura tih testova ostaje zelena.

**AC13 — CERT-PATH CONTRACT: certbot webroot `-w` path == nginx ACME `location` alias path == production.yml nginx webroot bind-mount; `/etc/letsencrypt` deljen u nginx (SM-D4).**
**Given** certbot izdaje cert (AC6), nginx servira ACME challenge i čita cert (AC7)
**When** Dev wire-uje certbot↔nginx deljenje filesystem-a
**Then** webroot path je KONKRETNO `/var/www/certbot` na SVA tri mesta: (1) `nginx-init.sh` certbot `--webroot -w /var/www/certbot`, (2) `nginx.conf` ACME `location /.well-known/acme-challenge/ { root /var/www/certbot; }`, (3) `production.yml` nginx servis bind-mount `- /var/www/certbot:/var/www/certbot:ro`.
**And** `/etc/letsencrypt` (gde certbot piše izdat cert na host-u) deljen u nginx kontejner READ-ONLY: `production.yml` nginx servis bind-mount `- /etc/letsencrypt:/etc/letsencrypt:ro` → `ssl_certificate /etc/letsencrypt/live/<domen>/fullchain.pem` resolve-uje u kontejneru.
**And** certbot trči na HOST-u (system paket + cron, NE certbot kontejner — AR-13), `--webroot` deli `/var/www/certbot` sa nginx kontejnerom kroz host bind-mount; ovo je DOKUMENTOVANO u Dev Notes "Certbot↔nginx path contract".
**And** PATH-CONSISTENCY LOCK (test): test parsira `nginx-init.sh` `-w` putanju i `nginx.conf` ACME `root`/`alias` putanju i tvrdi da su IDENTIČNE (`/var/www/certbot`); test tvrdi production.yml nginx ima oba bind-mount-a (`/etc/letsencrypt:ro` + `/var/www/certbot:ro`).

**AC14 — NGINX.CONF REACHABILITY: nginx.conf je BIND-MOUNT u production.yml (NE samo baked u image) + deploy.sh reload-uje/re-create-uje nginx (SM-D9).**
**Given** `compose/nginx/Dockerfile` BAKE-uje nginx.conf u image (`COPY ... default.conf`) → goli `restart django` NIKAD ne dostiže izmenu 443 conf-a
**When** Dev rešava baked-conf nedostižnost
**Then** `production.yml` nginx servis dobija bind-mount `- ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro` (relativno na `compose/`) tako da `git pull` + reload aplicira novi conf BEZ image rebuild-a.
**And** `deploy.sh` posle `git pull` izvršava `docker compose -f compose/production.yml up -d nginx` (re-create) ILI `docker compose -f compose/production.yml exec nginx nginx -s reload` da nginx pokupi novi bind-mount-ovan conf (NE samo `restart django`).
**And** Dockerfile `COPY` OSTAJE netaknut (image-baked conf kao fallback; bind-mount ga override-uje u runtime-u).
**And** MEHANIZAM LOCK (test): test tvrdi production.yml nginx servis ima bind-mount `nginx.conf` → `default.conf`; test tvrdi deploy.sh sadrži nginx re-create/reload korak (NE samo `restart django`).

**AC15 — FIRST-DEPLOY BOOTSTRAP: HTTP-only bootstrap → certbot → aktiviraj 443 (rešava chicken-and-egg; SM-D10).**
**Given** na svežem box-u nginx sa aktivnim `listen 443 ssl` koji referencira nepostojeći cert FAIL-uje da starta, a certbot `--webroot` zahteva nginx koji već sluša :80
**When** Dev sprovodi prvi deploy
**Then** postoji `compose/nginx/nginx.bootstrap.conf` (HTTP-only: :80 sa ACME location-om + static/media/proxy, BEZ ijednog `listen 443 ssl` bloka) za bootstrap fazu.
**And** `nginx-init.sh` sprovodi sekvencu: (1) digni nginx sa bootstrap conf-om (HTTP-only) → :80 servira ACME, (2) `certbot certonly --webroot -w /var/www/certbot ...` izda inicijalni cert, (3) swap na pun `nginx.conf` (443 aktivan), (4) `up -d nginx`/`exec nginx -s reload` → 443 starta jer cert sada postoji.
**And** sekvenca je idempotentna: ako cert već postoji (`/etc/letsencrypt/live/<domen>/fullchain.pem`), preskače bootstrap+izdavanje i ide direktno na pun conf.
**And** BOOTSTRAP LOCK (test): `nginx.bootstrap.conf` postoji i NEMA `listen 443 ssl`; `nginx-init.sh` referencira bootstrap conf PRE certbot poziva i swap-uje na pun conf POSLE certbot poziva (positional ordering parse).

## Tasks / Subtasks

### Task 1 — Web Intel (PRE koda; OBAVEZNO)
- [ ] 1.1 Verifikuj aktuelnu `certbot` webroot vs standalone praksu za Nginx-u-Docker-u (Nginx već sluša :80 → webroot challenge kroz deljeni volume je standard; standalone zahteva da Nginx stane). Potvrdi `--deploy-hook` reload sintaksu.
- [ ] 1.2 Verifikuj aktuelnu verziju `appleboy/ssh-action` (ILI `webfactory/ssh-agent` + raw ssh) i `docker/login-action` (v3 stable). Potvrdi `secrets.GITHUB_TOKEN` GHCR login pattern + `packages: write`.
- [ ] 1.3 Potvrdi da `certbot renew` cron/systemd-timer sa deploy-hook reload-uje Nginx bez downtime-a. Dokumentuj webroot path konvenciju (`/var/www/certbot` ILI deljeni volume).

### Task 2 — `ops/deploy/deploy.sh` (NOVI; primarni deliverable)
- [x] 2.1 Kreiraj `ops/` direktorijum (NE postoji još — arhitektura ga definiše: `ops/deploy/`, `ops/nginx/`, `ops/secrets/`).
- [x] 2.2 Napiši `ops/deploy/deploy.sh` sa `#!/usr/bin/env bash` + `set -euo pipefail`, LF line-endings. **`.gitattributes` `*.sh text eol=lf` VEĆ POSTOJI (`.gitattributes:8`) — VERIFIKUJ da je pravilo prisutno, NE re-kreiraj fajl (izbegni redundantan duplikat/churn).**
- [x] 2.3 Argument `$1` = environment (`staging`|`production`); biraj `compose -f compose/production.yml` + odgovarajući `.env`/host. Default-uj graceful ako arg nedostaje (fail-loud sa usage porukom).
- [x] 2.4 Implementiraj korake REDOM (AC1/AC2/SM-D5): `git pull` → `docker compose -f compose/production.yml pull` (OBAVEZNO — povuci novi GHCR image PRE migrate/collectstatic; epics:1204) → `uv sync --frozen` → `collectstatic --noinput` → `migrate --plan` (echo/assertion pre-check) → `migrate` → `compilemessages` → `docker compose -f compose/production.yml up -d django` (re-create sa novim image-om; NE goli `restart` koji zadržava stari image) → `docker compose -f compose/production.yml up -d nginx` ILI `exec nginx nginx -s reload` (pokupi novi bind-mount-ovan nginx.conf — AC14/SM-D9).
- [x] 2.4a DIRTY-TREE GUARD (IMPROVEMENT): na POČETKU deploy.sh (PRE `git pull`), proveri `git status --porcelain` (ILI `git diff --quiet && git diff --cached --quiet`) i FAIL-LOUD (exit non-zero + poruka) ako je tree prljav — NE `git stash`-uj-pa-nastavi. Sprečava tihi polu-deploy na boxu sa nekomitovanim izmenama. Testabilno (Task 9.1).
- [x] 2.4b CONCURRENCY LOCK (IMPROVEMENT): on-box `flock`/lockfile guard na startu deploy.sh (npr. `exec 200>/var/lock/coric-deploy.lock; flock -n 200 || { echo "deploy već u toku"; exit 1; }`) tako da CI + ručni deploy ne mogu da se ispreplet u (`git pull`/`migrate`/`restart`). GH Actions `concurrency` (6.1) štiti SAMO CI-side; ovo dodaje box-side zaštitu. Testabilno (Task 9.1).
- [x] 2.5 Dodaj post-restart healthcheck (AC10): retry-loop `curl -fsS` na app endpoint, fail deploy ako ne 2xx. POSLE re-create-a django+nginx.
- [x] 2.6 Komentar-marker za idempotency invariantu (AC3) + komentar zašto migrate PRE re-create-a (AC2) + komentar zašto `pull` PRE migrate-a (AC1/AC9 — inače stari image).
- [x] 2.7 Komande kroz `compose ... run --rm django python manage.py ...` (start.sh wait-for-db passthrough — 9.1 start.sh prosleđuje argumente) ILI `compose exec` — SM-D5 bira pattern (ali migrate/collectstatic MORAJU teći kroz NOVI pull-ovan image).

### Task 3 — `ops/deploy/rollback.sh` (NOVI)
- [x] 3.1 `#!/usr/bin/env bash` + `set -euo pipefail` + LF.
- [x] 3.2 Argument: ciljni tag/commit (ILI auto-detektuj prethodni `git describe --tags --abbrev=0 HEAD^`).
- [x] 3.3 `git checkout <tag>` → re-deploy (pozovi `deploy.sh` ILI inline collectstatic+restart). NEMA force-push (AC4).
- [x] 3.4 Migrate-down: SVESTAN tretman (AC11/SM-D3) — komentar-upozorenje + opcioni `migrate <app> <target>` SAMO ako eksplicitno dat. Default: NE auto-migrate-down (data-loss), uputstvo za ručni rollback.
- [x] 3.4a IRREVERSIBLE-MIGRATION WARNING (IMPROVEMENT): rollback.sh štampa GLASNO upozorenje na stderr PRE redeploy-a da, ako je tekući deploy uveo NEREVERZIBILNU šemu-migraciju (drop/rename kolone, destruktivan data-transform), ručna DBA intervencija je OBAVEZNA PRE rollback-a — inače checkout starog koda ka novoj šemi = broken state. Fail-loud/warn, NIKAD tiho ostavi pokvaren sistem (template u Dev Notes "Operativni safety guard-ovi"). NE pokušava auto-detekciju ireverzibilnosti (out-of-scope).

### Task 4 — `ops/nginx/nginx-init.sh` (NOVI; certbot + first-deploy bootstrap)
- [x] 4.1 `#!/usr/bin/env bash` + `set -euo pipefail` + LF.
- [x] 4.2 Parametrizuj `DOMAIN` (default `coricagrar.rs`), `ACME_EMAIL` kroz env/arg (AC6).
- [x] 4.3 FIRST-DEPLOY BOOTSTRAP (AC15/SM-D10): (1) digni nginx sa `compose/nginx/nginx.bootstrap.conf` (HTTP-only, BEZ 443) → :80 servira ACME; (2) certbot izda cert; (3) swap na pun `nginx.conf`; (4) `up -d nginx`/`exec nginx -s reload`. Guard idempotentno: ako `/etc/letsencrypt/live/$DOMAIN/fullchain.pem` postoji, preskoči bootstrap+izdavanje.
- [x] 4.4 `certbot certonly --webroot -w /var/www/certbot -d $DOMAIN -d www.$DOMAIN --email $ACME_EMAIL --agree-tos --non-interactive`. **Webroot path je KONKRETNO `/var/www/certbot` — MORA biti identičan ACME `root` u nginx.conf i bind-mount-u u production.yml (AC13/SM-D4 path-contract).**
- [x] 4.5 Registruj auto-renewal: cron entry (`0 3 1 * *` ILI `certbot renew` 2x dnevno per LE preporuci) ILI systemd timer, sa `--deploy-hook "docker compose -f compose/production.yml exec nginx nginx -s reload"`.
- [x] 4.5a RENEWAL FAILURE VISIBILITY: cron/timer `certbot renew` MORA učiniti neuspeh VIDLJIVIM (inače istekao cert obori sajt ~60-90 dana kasnije, tiho). Minimalno: `--deploy-hook` reload-uje nginx SAMO na uspeh (već 4.5), a neuspeh se loguje u cron/journal — npr. cron komanda umotana u `certbot renew ... || echo "CERT RENEWAL FAILED $(date)" >&2` (stderr → cron mail/journal) ILI systemd `OnFailure=` jedinica. Komentar u skripti objasni da je ovo BASELINE vidljivost; richer alerting (UptimeRobot/GlitchTip) je defer-ovan (OQ-6). NE implementiraj monitoring stack ovde (scope-disciplina — to je 9.3/9.4).
- [x] 4.6 Dokumentuj webroot path-contract (`/var/www/certbot`) + da je idempotentno (certbot ne re-izdaje ako cert još važi) + da certbot trči na HOST-u (NE certbot kontejner — AR-13).

### Task 5 — `compose/nginx/nginx.conf` 443 extension + production.yml EXTEND (UPDATE; EXTEND 9.1)
- [x] 5.1 Dodaj `location /.well-known/acme-challenge/ { root /var/www/certbot; }` u HTTP/80 blok (KONKRETAN webroot path usklađen sa certbot `-w` i bind-mount-om — AC13; NE redirect-uje, ostaje 200/404) (AC7).
- [x] 5.2 Dodaj BEZUSLOVAN HTTP→HTTPS redirect (`return 301 https://$host$request_uri;`) za sav ostali :80 saobraćaj OSIM ACME location-a (AC7/SM-D6). NE env-uslovljen. 9.1 smoke test `test_ac8_container_smoke_http_200_and_security_headers` se SVESNO ažurira (test-ownership, vidi Task 9.7 + AC12).
- [x] 5.3 Odkomentariši + parametrizuj 443 blok (linije ~87-136): `listen 443 ssl;`, `http2 on;`, `ssl_certificate`/`ssl_certificate_key` (`/etc/letsencrypt/live/<domen>/...`), `ssl_protocols TLSv1.2 TLSv1.3`, sva 3 security headera (`always`), `location /static/` + `/media/`, `proxy_pass django` + `X-Forwarded-Proto $scheme` (G-3), `client_max_body_size 11m`.
- [x] 5.4 Kreiraj `compose/nginx/nginx.bootstrap.conf` (HTTP-only: :80 blok sa ACME location `root /var/www/certbot;` + static/media/proxy, BEZ ijednog `listen 443 ssl` bloka) za first-deploy bootstrap (AC15/SM-D10).
- [x] 5.5 EXTEND `compose/production.yml` nginx servis volumes (SM-D4/SM-D9 — DODAJ stavke, NE re-write servis): `- ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro` (bind-mount conf da deploy reload aplicira izmenu — AC14), `- /etc/letsencrypt:/etc/letsencrypt:ro` (cert read-only — AC13), `- /var/www/certbot:/var/www/certbot:ro` (ACME webroot read-only — AC13). NE diraj postgres/django servise. Dockerfile `COPY` OSTAJE (fallback).
- [x] 5.5a KOMENTAR-USKLAĐIVANJE u `compose/production.yml`: postojeći header komentar (`compose/production.yml:8`) glasi `NEMA bind-mount source (image je SOT)`. Posle dodavanja nginx bind-mount-ova (5.5) taj komentar postaje DELIMIČNO netačan za nginx servis. Kvalifikuj ga (ne briši) tako da glasi tačno — npr.: `django/postgres: image je SOT (NEMA source bind-mount); nginx: config/cert/ACME bind-mount-ovi (conf reload bez rebuild-a + host-pisan cert) — Story 9.2 SM-D4/D9`. Cilj: dev koji čita header ne dobija pogrešan utisak da nijedan servis nema bind-mount.
- [x] 5.6 REGRESSION: 9.1 HTTP/80 static/media/proxy/headeri ostaju strukturno funkcionalni (AC7/AC12); bind-mount NE menja sadržaj conf-a koji 9.1 non-docker testovi parsiraju.

### Task 6 — `.github/workflows/deploy.yml` (NOVI) + GHCR push (UPDATE ci.yml)
- [x] 6.1 Kreiraj `deploy.yml`: `on: push: branches: [staging, main]` (SM-D1/OQ-1), `permissions: contents: read`, `concurrency` group po ref-u.
- [x] 6.2 Deploy job: checkout → SSH na Hetzner (`appleboy/ssh-action@v1` ILI raw) sa `${{ secrets.DEPLOY_SSH_KEY }}`, `${{ secrets.DEPLOY_HOST }}`, `${{ secrets.DEPLOY_USER }}` → remote `cd <app_dir> && ./ops/deploy/deploy.sh <env>` (env iz branch-a) (AC8).
- [x] 6.3 GHCR login+push (AC9): `docker/login-action@v3` (registry ghcr.io, `secrets.GITHUB_TOKEN`) + `docker/build-push-action@v7` `push: true`. Aktiviraj u `ci.yml` build job-u (`push: false`→`true` + dodaj login step) — KANONSKA lokacija LOCKED (SM-D7); NE u deploy.yml. Re-use postojeći lowercase image-name pattern + deterministički `:<sha>` tag koji deploy.sh `pull` referencira (AC9).
- [x] 6.4 REGRESSION: `ci.yml` lint/test/build redosled + lowercase pattern netaknut (AC9/AC12).

### Task 7 — `.env.example` + `ops/secrets/README.md`
- [x] 7.1 Dodaj deploy placeholder-e u `.env.example` (sekcija "Story 9.2 deploy"): `DEPLOY_DOMAIN=`, `ACME_EMAIL=`, komentar za `DEPLOY_HOST`/`DEPLOY_USER`/`DEPLOY_SSH_KEY` (idu kroz GH secrets, NE .env) (AC5).
- [x] 7.2 Kreiraj `ops/secrets/README.md`: lista zahtevanih GitHub Actions secrets (`DEPLOY_SSH_KEY`, `DEPLOY_HOST`, `DEPLOY_USER`; box `.env` mora imati `POSTGRES_PASSWORD`, `DJANGO_SECRET_KEY`, `DATABASE_URL`, `DJANGO_CSRF_TRUSTED_ORIGINS`...) + odakle (Hetzner secrets panel). NIKAD realne vrednosti (AC5).
- [x] 7.2a SSH LEAST-PRIVILEGE GUIDANCE (IMPROVEMENT — dokumentacija, NE implementacija): u `ops/secrets/README.md` dodaj sekciju "Deploy-key blast-radius" — box-side `~/.ssh/authorized_keys` treba da restriktuje deploy ključ (`command="..."` forced-command na deploy.sh, `no-pty`, `no-port-forwarding`, `no-agent-forwarding`) i deploy user NE sme biti `root` (namenski `deploy` user, sudo SAMO za potrebne docker/compose komande). Cilj: kompromitovan CI ključ ≠ pun root na boxu. Ovo je GUIDANCE/checklist — NE over-engineer-uj.

### Task 8 — justfile recepti (opciono)
- [ ] 8.1 Dodaj `deploy env`, `rollback` recepte u `justfile` AKO prirodno (mirror postojećih `prod-*` recepata). Opciono — NE obavezno za AC.

### Task 9 — Tests (TEA piše RED; ovde dokumentuj kontrakt)
- [ ] 9.1 `tests/test_deploy_scripts.py` — INFRA-VERIFY za deploy.sh/rollback.sh (AC1-AC5, AC10, AC11): postojanje, `set -euo pipefail`, LF, korak-ORDERING (`docker compose pull` index < migrate index < `up -d`/re-create index; --plan < migrate; collectstatic < re-create), idempotency markeri, NEMA `--force`/`push -f`, healthcheck posle re-create-a, rollback checkout+no-force.
- [ ] 9.1a DOCKER-PULL-ORDERING LOCK (AC1/AC2/AC9): test tvrdi deploy.sh sadrži `docker compose ... pull` i da je njegova pozicija STRIKTNO PRE `migrate`/`collectstatic`/`up -d` re-create-a (inače box pokreće stari image posle GHCR push-a).
- [ ] 9.1b NGINX-RELOAD LOCK (AC14/SM-D9): test tvrdi deploy.sh sadrži nginx re-create/reload korak (`up -d nginx` ILI `exec nginx ... -s reload`), NE samo `restart django`.
- [ ] 9.1c DIRTY-TREE + CONCURRENCY GUARD (IMPROVEMENT — Task 2.4a/2.4b): test tvrdi deploy.sh sadrži dirty-tree guard (`git status --porcelain` ILI `git diff --quiet`) i `flock`/lockfile pattern. (Best-effort asert — ako Dev guard ugradi, test ga zaključava.)
- [ ] 9.2 `tests/test_nginx_ssl_config.py` — nginx.conf 443 lint (AC7): `listen 443 ssl`, ssl_certificate/_key, BEZUSLOVAN HTTP→HTTPS redirect, ACME challenge location sa `root /var/www/certbot`, 3 security headera na 443, X-Forwarded-Proto; + 9.1 HTTP/80 regresija (static/media/proxy ostaju).
- [ ] 9.2a NGINX.CONF BIND-MOUNT LOCK (AC14/SM-D9): test tvrdi `compose/production.yml` nginx servis ima bind-mount `nginx.conf` → `/etc/nginx/conf.d/default.conf` (mehanizam da reload dostiže conf).
- [ ] 9.2b BOOTSTRAP CONF LOCK (AC15/SM-D10): `compose/nginx/nginx.bootstrap.conf` postoji, ima :80 ACME location, NEMA ijedan `listen 443 ssl`.
- [ ] 9.3 `tests/test_certbot_init.py` — `ops/nginx/nginx-init.sh` (AC6): `certbot` poziv, webroot `-w /var/www/certbot`, auto-renewal cron/timer, deploy-hook reload, domen/email parametrizovan; FIRST-DEPLOY ordering (AC15): bootstrap conf referenciran PRE certbot poziva, swap na pun conf POSLE; cert-existence idempotency guard.
- [ ] 9.3a CERT-PATH-CONTRACT LOCK (AC13/SM-D4): test parsira `nginx-init.sh` `-w` putanju i `nginx.conf` ACME `root`/`alias` putanju → tvrdi IDENTIČNE (`/var/www/certbot`); test tvrdi `compose/production.yml` nginx ima oba bind-mount-a `/etc/letsencrypt:ro` + `/var/www/certbot:ro`.
- [ ] 9.4 `tests/test_deploy_workflow_config.py` — `deploy.yml` YAML struktura (AC8): trigger branches, SSH kroz `secrets.*` (NE hardkodovan), poziva `ops/deploy/deploy.sh`, least-privilege permissions, NEMA plaintext secret-a. **GHCR login/push asert ide na `ci.yml` build job (KANONSKA lokacija — SM-D7), NE na deploy.yml**: test parsira `ci.yml` build job i tvrdi `docker/login-action` + `push: true` + lowercase image-name + deterministički `:<sha>` tag (deploy.yml NE gradi/push-uje — može imati zaseban grep-asert da deploy.yml NEMA `build-push-action`).
- [ ] 9.5 SECURITY negative grep (AC5): ni jedan novi fajl ne sadrži `BEGIN PRIVATE KEY` / hardkodovan ne-prazan password.
- [ ] 9.6 Sve 9.2 testove drži IMPORT-LIGHT (`pathlib` + `yaml` + `re` SAMO; bez Django app importa, bez libmagic) — moraju trčati na Windows host-u I u CI.
- [ ] 9.7 9.1 SMOKE TEST-OWNERSHIP (AC7/AC12/SM-D6): SVESNO ažuriraj `test_ac8_container_smoke_http_200_and_security_headers` u `tests/test_production_stack.py` da prati 80→443 redirect (`allow_redirects=True`/`curl -IL` → sletanje na 200 sa HTTPS, ILI 301 sa `Location` `https://`) + novi assert da `GET /.well-known/acme-challenge/<probe>` NE redirect-uje (200/404, NIKAD 301). JEDINA dozvoljena izmena 9.1 testova.

## Dev Notes

### Architecture reference
- **AR-13** (architecture.md): Hetzner VPS — CX22 (staging) / CX32 (production), Nginx + Gunicorn + Let's Encrypt SSL auto-renewal. SSL red u stack tabeli: `certbot + Nginx auto-renewal cron` (architecture:218).
- **AR-22** (backup): defer-uje na Story 9.5 — 9.2 NE implementira backup.
- **Direktorijum** (architecture:693-703): `ops/deploy/{deploy.sh,rollback.sh}`, `ops/nginx/` (nginx-init.sh — arhitektura ga implicira certbot init-om), `ops/secrets/README.md`. `ops/` NE POSTOJI još — 9.2 ga kreira.
- **Deploy workflow** (architecture:856-857, project-context:444-457): staging push → deploy.yml → SSH staging Hetzner → `ops/deploy/deploy.sh staging`; main (po PR review) → production. `.github/workflows/deploy.yml` (architecture:547) "deploy to Hetzner na main branch push".

### Deploy koraci (project-context:447-454 — SOT za ORDERING)
```
1. git pull
2. docker compose -f compose/production.yml pull   # OBAVEZNO — novi GHCR image PRE migrate-a (AC1/AC9; epics:1204)
   # 3. uv sync --frozen  -> UKLONJEN sa host-a (M3): frozen deps su BAKED u GHCR image
   #    (prod-builder stage radi `uv sync --frozen --no-dev` u build vremenu). Bare host
   #    uv sync bi fail-ovao/bio besmislen za Docker-image-SOT deploy.
4. python manage.py collectstatic --noinput        # KROZ novi image (docker compose run --rm django)
5. python manage.py migrate --plan                 # assertion/pre-check
6. python manage.py migrate                        # apply (PRE re-create-a — AC2)
7. python manage.py compilemessages
   # pre 8: cp compose/nginx/nginx.conf compose/nginx/.active-default.conf  (M1 steady-state swap)
8. docker compose -f compose/production.yml up -d django   # re-create sa novim image-om (NE goli restart — SM-D5)
9. docker compose -f compose/production.yml up -d nginx     # ILI: exec nginx nginx -s reload (pokupi bind-mount conf — AC14/SM-D9)
10. healthcheck (AC10/M4): docker compose exec -T django curl -fsS http://127.0.0.1:8000/sr/
    # UNUTAR kontejnera — :8000 NIJE izlozen na host (bare host curl = connection refused).
```
> **Fix-iter (M1-M8) reconciliation:** Code-review HIGH panel je flag-ovao 8 Mandatory issue-a. Razresene su (vidi sekciju "Fix Iteration 1" dole): M1 swappable `.active-default.conf` bind-mount (bootstrap swap vise nije inertan), M2 GHCR-pathed django `image:` (+ stable per-branch tag u ci.yml), M3 uv-sync image-baked (uklonjen sa host-a), M4 healthcheck unutar kontejnera, M5 DEPLOY_APP_DIR dokumentovan+guard, M6 CWD guard-ovi (SCRIPT_DIR/REPO_ROOT + apsolutna cron compose putanja), M7 9.1 smoke test 80→301 ownership, M8 SSH host-key fingerprint + ssh-action SHA-pin.
> **Napomena o ordering-u:** project-context:454 lista samo `docker compose restart django`, ali epics:1204 eksplicitno lista i `docker compose pull` + `down + up`. 9.2 LOCK-uje pull-prvo-pa-re-create (SM-D5) jer deploy konzumira novi GHCR image (AC9); goli `restart` bi zadržao stari image. nginx re-create/reload je dodat jer je nginx.conf sada bind-mount (SM-D9) — `restart django` ne dostiže conf izmenu.
- **"NIKAD force push na main/staging — koristi revert"** (project-context:456) → AC4.
- **"Migrations su deploy-time, ne app-startup"** (project-context:478) → 9.1 start.sh NAMERNO ne migrira; 9.2 deploy.sh JE mesto gde migrate živi. NE diraj start.sh.
- **"Deploy je idempotentan"** (project-context:477) → AC3.

### 9.1 forward-deps koje OVA story konzumira/honoriše
1. **nginx HTTPS/443 PLACEHOLDER** (`compose/nginx/nginx.conf:87-136`, zakomentarisan) — 9.2 certbot wire-uje: cert provisioning (AC6), 443 aktivacija (AC7), HTTP→HTTPS redirect + ACME location.
2. **`POSTGRES_PASSWORD:-` prazan default** (`compose/production.yml:24`) — prod MORA injektovati. 9.2 secret injection kroz box `.env` (AC5). 9.1 ga je flagovao kao open item → ovde se rešava.
3. **start.sh ne migrira** (`compose/django/start.sh:24`) — migrate je deploy-step → deploy.sh (AC1/AC2). NE diraj start.sh (regresija `test_ac5_start_sh_does_not_migrate`).
4. **ci.yml build job DEFERRED push** (`ci.yml:120-130`, `push: false` + "DEFERRED do Story 9.2") — 9.2 aktivira GHCR login+push (AC9). `packages: write` job-level permission VEĆ postoji.
5. **production.yml nginx 443 port VEĆ mapiran** (`80:80` + `443:443`, production.yml:88-89) — port je tu; 9.2 dodaje cert/webroot/conf bind-mount-ove (Task 5.5, SM-D4/SM-D9).

### Certbot↔nginx path contract (KRITIČNO — AC13/SM-D4)
Certbot izdaje cert i piše ACME challenge fajlove; nginx servira challenge i čita cert. Ako se putanje ne poklapaju, ACME validacija FAIL-uje (challenge nedostupan) ILI nginx ne starta (cert nedostupan). Zato je path-ugovor KONKRETAN i LOCKED na 3 mesta:

| Šta | Putanja | Gde |
|-----|---------|-----|
| ACME webroot (certbot `-w`) | `/var/www/certbot` | `nginx-init.sh` certbot poziv |
| ACME `location` root/alias | `/var/www/certbot` | `nginx.conf` :80 `location /.well-known/acme-challenge/` |
| webroot bind-mount (nginx čita) | `/var/www/certbot:/var/www/certbot:ro` | `production.yml` nginx servis |
| cert dir (certbot piše) | `/etc/letsencrypt` (host) | host filesystem |
| cert bind-mount (nginx čita) | `/etc/letsencrypt:/etc/letsencrypt:ro` | `production.yml` nginx servis |
| `ssl_certificate` | `/etc/letsencrypt/live/<domen>/fullchain.pem` | `nginx.conf` 443 blok |

- **Certbot trči na HOST-u** (system paket + auto-renewal cron — AR-13 `certbot + Nginx auto-renewal cron`), NE kao certbot kontejner. Zato su `/etc/letsencrypt` i `/var/www/certbot` **host bind-mount-ovi** (NE named volume-i) — host-pisan sadržaj mora biti vidljiv nginx kontejneru.
- nginx mount-ovi su `:ro` (nginx samo čita; certbot na host-u piše).
- Path-consistency LOCK test (AC13/Task 9.3a) parsira `-w` putanju iz `nginx-init.sh` i `root`/`alias` iz `nginx.conf` i tvrdi da su identične.

### Baked-conf resolution (KRITIČNO — AC14/SM-D9)
`compose/nginx/Dockerfile` radi `COPY compose/nginx/nginx.conf /etc/nginx/conf.d/default.conf` → conf je BAKED u image u BUILD vremenu. Ako deploy.sh samo `git pull` + `restart django`, **izmena 443 nginx.conf-a NIKAD ne stigne do running nginx-a** (image se ne rebuild-uje, a bind-mount-a nema). Razrešenje (opcija A — najmanji correctness rizik):
- production.yml nginx servis dobija bind-mount `- ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro` (putanja relativna na `compose/` direktorijum gde production.yml živi → `compose/nginx/nginx.conf`). Bind-mount override-uje baked conf u runtime-u.
- Posle `git pull` (ažurira conf na disku) deploy.sh radi `up -d nginx` (re-create) ILI `exec nginx nginx -s reload` → novi conf aktivan BEZ image rebuild-a.
- Dockerfile `COPY` OSTAJE netaknut (fallback za standalone run bez compose-a).
- Ovo EXTEND-uje 9.1 production.yml (dozvoljeno — story scope pokriva 443 wiring); HTTP/80 ponašanje netaknuto (isti conf fajl).

### First-deploy bootstrap (KRITIČNO — AC15/SM-D10)
Chicken-and-egg: nginx sa aktivnim `listen 443 ssl` koji referencira NEPOSTOJEĆI cert FAIL-uje da starta, ali certbot `--webroot` zahteva nginx koji VEĆ sluša :80. Razrešenje — HTTP-only bootstrap conf, pa swap:
1. `nginx-init.sh` digne nginx sa `compose/nginx/nginx.bootstrap.conf` (HTTP-only, BEZ 443) → :80 servira ACME challenge.
2. `certbot certonly --webroot -w /var/www/certbot ...` izda inicijalni cert.
3. swap bind-mount/conf na pun `compose/nginx/nginx.conf` (443 aktivan).
4. `up -d nginx`/`exec nginx -s reload` → 443 starta jer cert sada postoji.
- Idempotentno: ako `/etc/letsencrypt/live/<domen>/fullchain.pem` postoji, preskoči bootstrap+izdavanje, idi direktno na pun conf.
- Steady-state (svi naredni deploy-evi): `nginx.conf` je SOT sa aktivnim 443; bootstrap conf se koristi SAMO pri prvom izdavanju.
- Alternativa (dokumentovana, NE default): seed self-signed dummy cert pa swap pravim — odbačeno jer ostavlja dummy artefakt.

### Fix Iteration 1 (code-review HIGH panel — 8 Mandatory M1-M8 RESOLVED)

5-reviewer HIGH-tier panel (Dev-A/Dev-B/Architect/Security/TEA) konvergirao na 8 Mandatory issue-a. Sve razresene; ugovor-menjajuce ispravke sinhronizovane sa testovima (`tests/test_deployment_ssl.py` + `tests/test_production_stack.py`) i interface contract-om.

- **M1 (BUG CRITICAL) — first-deploy bootstrap swap je bio INERTAN.** production.yml je mount-ovao `nginx.conf` direktno, a nginx-init.sh je kopirao bootstrap u `.active-default.conf` koji nista ne mount-uje → na svezem boxu nginx starta sa 443 + nepostojeci cert → fail → ACME se ne servira → prvi cert se nikad ne izda. **Fix:** production.yml bind-mount cilja `./nginx/.active-default.conf` (swappable); nginx-init.sh `cp bootstrap → .active-default.conf` (PRE certbot), `cp nginx.conf → .active-default.conf` (POSLE certbot); deploy.sh kopira nginx.conf→.active-default.conf pre nginx re-create-a (steady-state). `.active-default.conf` u `.gitignore`. Testovi: AC14 bind-mount asert + AC15 swap-after asert azurirani.
- **M2 (BUG CRITICAL) — GHCR image se nikad ne pull-uje.** production.yml django `image: coric_agrar_django_production` je lokalno ime → `docker compose pull` ne resolve-uje GHCR. **Fix:** `image: ghcr.io/${GHCR_IMAGE:-miiihaaas/coric_agrar}:${IMAGE_TAG:-latest}` (build: ostaje lokalni fallback); ci.yml push-uje stabilan per-branch tag (master→latest) pored `:ci-<sha>`; GHCR_IMAGE/IMAGE_TAG u .env.example. Testovi: django-image-ghcr asert + stable-tag asert dodati.
- **M3 (BUG) — `uv sync --frozen` na host-u.** Uklonjen iz deploy.sh — deps su image-baked (prod-builder stage). Komentar-marker `BAKED u GHCR image` (reconciliation sa project-context). Test azuriran: bare-host uv-sync negative lock + image-baked marker asert.
- **M4 (BUG) — healthcheck na neizlozen :8000.** Promenjeno na `docker compose exec -T django curl -fsS http://127.0.0.1:8000/sr/` (interni Gunicorn, zaobilazi nginx 301/cert). Novi test: healthcheck-inside-container.
- **M5 (BUG) — DEPLOY_APP_DIR nedokumentovan.** Dodat u ops/secrets/README.md (OBAVEZAN); deploy.yml fail-loud guard (`[ -z "$APP_DIR" ] && exit 1`). Testovi dodati.
- **M6 (BUG) — nema CWD guard-ova / relativne putanje.** Sve 3 skripte: `SCRIPT_DIR/REPO_ROOT` + `cd "${REPO_ROOT}"`. rollback.sh `exec "${SCRIPT_DIR}/deploy.sh"`. nginx-init.sh cron koristi APSOLUTNU `${REPO_ROOT}/compose/production.yml` (cron CWD != repo root). `mkdir -p /var/lock` pre flock-a.
- **M7 (BUG) — 9.1 docker smoke nije azuriran.** `test_ac8_container_smoke_http_200_and_security_headers` (test_production_stack.py) preuzet (AC12/SM-D6): :80 /sr/ → 301 `Location: https://` + 3 headera na 301 + ACME probe NE 301. Seed-uje `.active-default.conf` pre `up`. TEST_MODIFICATION logovan.
- **M8 (SECURITY MEDIUM) — SSH host-key + action SHA pinning.** deploy.yml: `fingerprint: ${{ secrets.DEPLOY_HOST_FINGERPRINT }}` + `appleboy/ssh-action@2ead5e36573f08b82fbfce1504f1a4b05a647c6f` (v1.2.2 SHA-pin, jer rukuje SSH kljucem). DEPLOY_HOST_FINGERPRINT dokumentovan; SHA-pinning ostalih akcija = OQ best-effort.

### Fix Iteration 2 (code-review NON-Mandatory polish — best-effort, low-risk)

Drugi prolaz pokriva NON-Mandatory (ARCHITECTURE/TEST_GAP/PERFORMANCE/STYLE) nalaze. M1-M8 NETAKNUTI. Sve `tests/test_deployment_ssl.py` prolaze (75 passed).

- **[ARCHITECTURE] deploy.yml — uklonjen `actions/checkout@v6`.** Sav stvaran rad ide preko SSH na Hetzner boxu (deploy.sh radi sopstveni `git pull`), pa je runner-side checkout bio mrtav teret (~30s + supply-chain povrsina). Job sada ima samo `Resolve environment` + `Deploy via SSH`. deploy.yml ostaje validan YAML; svi deploy.yml testovi prolaze.
- **[PERFORMANCE] deploy.sh healthcheck retry budzet 60s→120s.** Django+Postgres cold start na CX22 moze potrajati 90-120s; 12×5s=60s je rizikovao false-negative. Parametrizovano: `HEALTHCHECK_RETRIES="${HEALTHCHECK_RETRIES:-24}"` (default 24×5s=120s), `seq 1 "${HEALTHCHECK_RETRIES}"`. I dalje BOUNDED (nikad hang). Healthcheck ostaje POSLE re-create-a (AC10 ordering netaknut).
- **[TEST_GAP] AC7 `ssl_protocols` lock dodat.** Novi `test_ac7_nginx_conf_443_ssl_protocols_hardened`: scope-ovan na AKTIVAN 443 blok (`_extract_443_server_block`), tvrdi TLSv1.2 + TLSv1.3 prisutni i legacy (TLSv1.0/1.1/SSLv2/3) ODSUTNI. nginx.conf vec ima `ssl_protocols TLSv1.2 TLSv1.3;` (9.1/M-fix) — sad je test-locked.
- **[TEST_GAP] AC10 healthcheck-existence vec radi na `_strip_comments`** (komentar ne moze lazno da zadovolji) — verifikovano, bez izmene.
- **[TEST_GAP] AC7 ACME-not-redirected scope-ovan na aktivne linije.** Ekstrakcija tela ACME location-a sada ide kroz `_active_lines(...)` pa DOTALL — zakomentarisan `return 301` ne moze lazno da fail-uje, niti se 443-block location pokupi.
- **[TEST_GAP] AC13 webroot `-w` ekstrakcija robusnija.** Sada na `_strip_comments` + usidreno uz `--webroot`/`certbot` (`--webroot -w (\S+)` → `certbot ... -w (\S+)` → `(?<!\S)-w (\S+)` fallback) — ne pokupi komentar/continuation backslash. String-equality contract sa nginx ACME root zadrzan.
- **[TEST_GAP] AC6 renewal-failure-visibility pooStren.** Sada vezuje vidljivost za `certbot renew` (`certbot renew ...||... >&2`) ILI systemd `OnFailure=` — labavi `FAIL`/golo `>&2` bilo gde vise ne prolazi. Match-uje realnu implementaciju (cron `CRON_LINE` `|| echo "CERT RENEWAL FAILED ..." >&2`).
- **[STYLE] Test konsolidacija.** Tasks su naveli 4 logicka test fajla (`test_deploy_scripts.py`, `test_nginx_ssl_config.py`, `test_certbot_init.py`, `test_deploy_workflow_config.py`); isporucen je 1 kohezivan `tests/test_deployment_ssl.py` koji pokriva sve 4 grupe (deploy/nginx-ssl/certbot/workflow). Konsolidacija je namerna (deljeni helperi `_read_file`/`_active_lines`/`_extract_443_server_block` zive na jednom mestu) — funkcionalno ekvivalentno planu.
- **[ARCHITECTURE/STYLE] nginx-init.sh cron `--deploy-hook` quoting — PREGLEDANO, OSTAVLJENO.** `RENEW_HOOK` se dodeljuje bash varijabli, ekspanduje u `CRON_LINE`, pa pipe-uje u `crontab -` (NIJE `eval`-ovan). Nested `\"${RENEW_HOOK}\"` daje literalne duple navodnike oko deploy-hook vrednosti u crontab unosu (ispravno), a `\$(date)` je escape-ovan da se evaluira u cron-run vremenu (ne pri registraciji). Runtime-korektno — TEA/Dev-B flag je adresiran ostavljanjem (izmena bi rizikovala radnu cron liniju). Scoped verifier presuda potvrdjena.

### Operativni safety guard-ovi (IMPROVEMENT — best-effort, low-risk)
Ove napomene OJAČAVAJU operativnu sigurnost bez proširenja scope-a (nema monitoring stack-a, nema novih runtime dep-ova). Dev ih sprovodi kroz već-postojeće Task-ove (4.5a, 2.4/2.5, 3.4) — NE dodaju nove deliverable fajlove.

- **Cert-renewal FAILURE vidljivost (Task 4.5a):** tihi neuspeh auto-renewal-a = istekao cert = sajt nedostupan 60-90 dana kasnije. BASELINE razrešenje: `--deploy-hook` reload na uspeh + neuspeh surface-ovan u cron/journal (`|| echo "CERT RENEWAL FAILED" >&2` ILI systemd `OnFailure=`). Bogatiji alerting (email/UptimeRobot ping/GlitchTip event) je DEFER-ovan — vidi OQ-6. Ovde NE uvodimo monitoring (9.3 GlitchTip / 9.4 UptimeRobot to pokrivaju).

- **Rollback kad je migracija IREVERZIBILNA (Task 3.4 / AC11 / SM-D3):** SM-D3 default je no-auto-migrate-down (dobro). ALI ako je deploy uveo migraciju koja je šema-nekompatibilna i NEMA reverzibilnu operaciju (npr. `DROP COLUMN` / `RENAME` bez reverse migracije, ili destruktivan data-transform), gola `git checkout <prev>` + redeploy STAROG koda udara u NOVU šemu → broken state. `rollback.sh` MORA fail-loud / štampati GLASNO upozorenje umesto da tiho ostavi pokvaren sistem. Template upozorenja za ugraditi u `rollback.sh` (echo na stderr pre redeploy-a):
  ```
  echo "[ROLLBACK WARNING] Ako je tekući deploy uveo NEREVERZIBILNU migraciju (drop/rename kolone, destruktivan data-transform)," >&2
  echo "  ručna DBA intervencija je OBAVEZNA PRE rollback-a — checkout starog koda ka novoj šemi = broken state." >&2
  echo "  Auto migrate-down je ISKLJUČEN (data-loss rizik, SM-D3). Potvrdi šema-kompatibilnost ili migriraj ručno." >&2
  ```
  rollback.sh NE pokušava auto-detekciju ireverzibilnosti (out-of-scope, nepouzdano) — samo GLASNO upozorava i prepušta operatoru svesnu odluku.

- **Deploy na DIRTY git tree (Task 2.4):** ako Hetzner box ima nekomitovane lokalne izmene, `git pull` može fail-ovati/konfliktovati i ostaviti polu-deploy. `deploy.sh` MORA proveriti `git status --porcelain` (ILI `git diff --quiet && git diff --cached --quiet`) NA POČETKU i FAIL-LOUD (exit non-zero sa porukom) ako je tree prljav — NE `git stash`-uj-pa-nastavi (rizično: stash može tiho odbaciti izmene / konfliktovati pri pop-u). Dirty-tree guard je TESTABILAN (test tvrdi deploy.sh sadrži `git status --porcelain` ILI `git diff --quiet` guard koji exit-uje pre `git pull`).

- **Concurrency: on-box deploy LOCK (Task 2.4):** GH Actions `concurrency` grupa (Task 6.1) serijalizuje CI-side deploy-eve, ALI NE štiti od čoveka koji ručno pokrene `deploy.sh` na boxu istovremeno (CI + manual interleave → ispreplitan `git pull`/`migrate`/`restart` = korupcija). `deploy.sh` koristi on-box `flock`/lockfile guard (npr. `exec 200>/var/lock/coric-deploy.lock; flock -n 200 || { echo "deploy već u toku"; exit 1; }`) tako da se preklapajući deploy-evi ne mogu isprepleteti. Testabilno (test tvrdi deploy.sh sadrži `flock` ILI lockfile pattern).

- **SSH-key blast-radius / least-privilege (Task 7.2 — `ops/secrets/README.md`):** `DEPLOY_SSH_KEY` u GH secrets je dobro, ali kompromitovan CI ključ NE sme značiti pun root na boxu. `ops/secrets/README.md` dokumentuje GUIDANCE (ne implementira ovde): (1) box-side `~/.ssh/authorized_keys` restrikcija deploy ključa kroz `command="..."` (forced-command na deploy.sh), `no-pty`, `no-port-forwarding`, `no-agent-forwarding`; (2) deploy user NIJE `root` — namenski `deploy` user sa sudo SAMO za potrebne docker/compose komande. Ovo je dokumentacija/guidance — NE over-engineer-uj (nema custom PAM/seccomp).

### Planning-artefakt diskrepancija (STYLE — orientation napomena)
- **epics.md 9.2 (`epics.md:1204`) vs project-context (`project-context:447-454`) — deploy korak SHAPE se razlikuje:** epics.md lista korake drugačijim redom/oblikom (`docker compose down + up` umesto `up -d` re-create; collectstatic uz migrate; certbot inline u istom "When"). **SOT za ORDERING je `project-context:447-454`** (collectstatic kao korak 3, migrate posle, restart/re-create na kraju) — story SLEDI project-context, a 9.2 LOCK-uje `pull`-prvo + `up -d` re-create umesto golog `restart`/`down+up` (SM-D5). Dev koji unakrsno čita epics.md NE treba da se zbuni: epics.md je high-level "When/And/Then", project-context je konkretan ordered SOT. Nema kontradikcije u nameri — samo razlika u granularnosti/obliku.

### Postojeći INFRA-VERIFY test pattern (REUSE stil)
- `tests/test_production_stack.py` (9.1) — `_read_file`/`_has_lf_only`/`_parse_yaml`/grep-lock helperi, `pytest.fail` kad fajl ne postoji (RED signal). KOPIRAJ ovaj stil.
- `tests/test_ci_workflow_config.py` (1.9) — `yaml.safe_load` na workflow + `module`-scoped fixture, raw-text fixture za grep. KOPIRAJ za `deploy.yml`.
- **PyYAML quirk:** `on:` se parsira kao Python `True` ključ (YAML 1.1) — koristi `workflow[True]` za pristup trigger bloku (vidi test_ci_workflow_config.py docstring).

### Host test caveat (KRITIČNO — stavi u test docstring)
- **Native Windows host pytest NE može da collect-uje pun suite** (libmagic nedostaje — `python-magic` u `apps/media_pipeline`; DOKUMENTOVAN pre-existing baseline, NIJE regresija). Vidi memory: "17 pre-existing foundational test grešaka = NIJE regresija".
- **ALI novi 9.2 INFRA-VERIFY testovi su čist file-parsing** (`pathlib` + `yaml` + `re`) — NE importuju Django settings ni libmagic → MOGU i TREBA da trče na host-u I u Docker/CI. TEA: drži 9.2 testove import-light (Task 9.6).
- **shellcheck/bats NISU instalirani na host-u** → testovi su čisto Python file-inspekcija, NE `subprocess.run(["shellcheck", ...])`. Parsiraj sadržaj skripte sami (grep `set -euo pipefail`, pozicija `re.search` indeksa za ORDERING).
- Pokretanje: `uv run pytest tests/test_deploy_scripts.py tests/test_nginx_ssl_config.py tests/test_certbot_init.py tests/test_deploy_workflow_config.py -v` (radi i na host-u jer su import-light).

### Files (apsolutne putanje)
- NOVI: `ops/deploy/deploy.sh`, `ops/deploy/rollback.sh`, `ops/nginx/nginx-init.sh`, `ops/secrets/README.md`, `.github/workflows/deploy.yml`, `compose/nginx/nginx.bootstrap.conf` (HTTP-only first-deploy bootstrap — AC15)
- UPDATE: `compose/nginx/nginx.conf` (443 extension + ACME `root /var/www/certbot` + bezuslovan redirect), `.env.example` (deploy placeholder-i), `.github/workflows/ci.yml` (GHCR push — KANONSKA lokacija, LOCKED SM-D7; NE deploy.yml), `compose/production.yml` (nginx cert/webroot/conf bind-mount-ovi — Task 5.5, SM-D4/SM-D9), `tests/test_production_stack.py` (SAMO `test_ac8_container_smoke_http_200_and_security_headers` — test-ownership, AC7/AC12/SM-D6), `justfile` (opciono recepti), `.gitattributes` (`*.sh text eol=lf` VEĆ prisutan na `.gitattributes:8` — verify-not-create)
- TESTS (TEA): `tests/test_deploy_scripts.py`, `tests/test_nginx_ssl_config.py`, `tests/test_certbot_init.py`, `tests/test_deploy_workflow_config.py`

### Naming / konvencije
- Srpska latinica + engleski identifikatori; **BEZ ćirilice** (project-context Critical Don't-Miss Rule).
- LF line-endings za sve `.sh` (G-1 — 9.1 start.sh presedan; bash u Linux crash-uje na CRLF).
- `set -euo pipefail` na svim bash skriptama (fail-fast).

## SM Decisions

**SM-D1 — Deploy branch naming: `staging` + `main` (trigger deploy.yml), uz logovan OQ za master→main.**
project-context (456, 856-857) i architecture (547) eksplicitno govore `staging` + `main`. Repo realnost: default branch je `master`, CI (`ci.yml`) trigger-uje na `master`. Biram **`on: push: branches: [staging, main]`** za `deploy.yml` jer je `main`/`staging` GO-LIVE ciljano naming iz planning artefakata, a deploy je nova površina (ne nasleđuje `master` iz CI-ja). Master→main reconciliation je realna nedoslednost koju Mihas mora razrešiti PRE prvog deploy-a (OQ-1) — ne pogađam tiho. Ako Mihas zadrži `master` kao default, `branches` lista se trivijalno menja; test asertuje da deploy branch nije prazno/hardkodovan na pogrešno, fleksibilno na `{staging, main}` ILI `{master}`.

**SM-D2 — Domen parametrizovan env-om (default `coricagrar.rs`).**
9.1 placeholder koristi `coricagrar.rs`. Parametrizujem `DOMAIN`/`DEPLOY_DOMAIN` kroz env u `nginx-init.sh`/`deploy.sh` umesto hardkodovanja gde je razumno. nginx.conf `server_name` sme ostati `coricagrar.rs www.coricagrar.rs` (conf nije lako env-templejtovan bez envsubst — SM-D8), ali cert putanje `/etc/letsencrypt/live/<domen>/` i certbot poziv koriste env var. OQ-2: realan produkcioni domen (`coricagrar.rs` vs `.example` placeholder iz drugih artefakata) = Mihas potvrda.

**SM-D3 — Rollback migrate-down je SVESTAN, NE auto.**
epics:1208 traži "revert na prethodni commit + migrate down". ALI auto `migrate <app> <prev>` na produkciji je data-loss rizik (drop kolone briše podatke). `rollback.sh` PODRAZUMEVANO NE radi auto-migrate-down — checkout-uje kod + redeploy + eksplicitan komentar/upozorenje sa uputstvom za ručni migrate-down ako je potreban. Opcioni argument dozvoljava ciljani `migrate app target`. AC11 ovo zaključava. OQ-3 eskalacija: da li produkcija ikad sme auto-migrate-down (preporuka: NE).

**SM-D4 — nginx cert volume + ACME webroot = EXTEND production.yml nginx servisa, NE re-write. KONKRETAN path ugovor.**
443 blok referencira `/etc/letsencrypt/live/...` — taj path MORA biti mount-ovan u nginx kontejner. ACME challenge MORA da deli istu putanju na koju certbot piše `-w <PATH>`. Zaključavam KONKRETAN ugovor (LOCKED, NE "dev bira"):
- **Webroot path (host i kontejner istovetno):** `/var/www/certbot`. Certbot na **host-u** piše challenge u `/var/www/certbot`; nginx ga čita iz iste host putanje preko bind-mount-a.
- **Cert path:** `/etc/letsencrypt` na host-u (gde certbot piše izdat cert), deljen u nginx kontejner **read-only**.
- **production.yml nginx servis dobija 2 NOVA host bind-mount volume-a** (mirror 9.1 EXTEND-not-overwrite disciplina; named volume NIJE pogodan jer certbot trči na host-u, ne u nginx kontejneru):
  - `- /etc/letsencrypt:/etc/letsencrypt:ro`  (cert read-only za nginx — `ssl_certificate` putanje resolve-uju)
  - `- /var/www/certbot:/var/www/certbot:ro`  (ACME webroot read-only za nginx — challenge fajlovi vidljivi)
- **Certbot trči na HOST-u** (system paket, NE certbot kontejner) preko `--webroot -w /var/www/certbot`. Time je `-w` putanja IDENTIČNA nginx ACME `location` alias-u → challenge se servira i validira. Host-instalirani certbot + auto-renewal cron je AR-13 stack izbor (`certbot + Nginx auto-renewal cron`).
- NE diram postgres/django servise. Path-consistency LOCK testom (AC13/Task 9.3a — path-contract; AC15/Task 9.3 je first-deploy bootstrap, NE meša): `nginx-init.sh` certbot `-w` putanja == nginx.conf ACME `location` alias putanja == production.yml nginx webroot bind-mount.

**SM-D5 — Restart pattern + OBAVEZAN `docker compose pull` + nginx re-create. LOCKED ordering.**
project-context:454 kaže `docker compose restart django`, ALI deploy konzumira NOVI GHCR image (AC9 push) → goli `restart` zadržava STARI image i deploy ne bi povukao novi kod. Zato LOCK-ujem (NE "dev bira"):
- **`docker compose -f compose/production.yml pull` je OBAVEZAN ordered korak** — povlači novi GHCR image PRE migrate/collectstatic (koji se izvršavaju KROZ taj novi image) i PRE re-create servisa. epics:1204 eksplicitno lista `docker compose pull`.
- **Re-create umesto golog restart:** `docker compose -f compose/production.yml up -d django` (re-create kontejnera sa novim pull-ovanim image-om). Goli `restart` NE menja image → ne sme biti jedini mehanizam.
- **nginx re-load posle git pull-a:** pošto je nginx.conf sada BIND-MOUNT (SM-D9), deploy.sh radi `docker compose -f compose/production.yml up -d nginx` (re-create da pokupi novi conf) ILI `docker compose -f compose/production.yml exec nginx nginx -s reload`. Goli `restart django` NE dostiže nginx.conf izmenu (vidi SM-D9).
- Redosled je LOCKED: `git pull` → `pull` (image) → migrate-stack (collectstatic/migrate/compilemessages KROZ novi image) → `up -d django` (re-create) → `up -d nginx`/`exec nginx -s reload` → healthcheck. Test asertuje `pull` PRE re-create-a i PRE migrate-a (AC2 ordering).

**SM-D6 — HTTP→HTTPS redirect: LOCKED opcija (a) — 9.1 smoke test SVESNO ažuriran da prati redirect; ACME passthrough ostaje 200.**
9.1 `test_ac8_container_smoke_http_200_and_security_headers` (`@pytest.mark.docker`) očekuje `GET http://localhost/sr/` → **200**. Sa novim :80 blokom koji bezuslovno radi `return 301 https://` za sve OSIM ACME location-a, taj smoke dobija 301. **Razrešenje je KONKRETNO i LOCKED (NE "dev bira"): opcija (a).**
- **:80 blok zadržava `location /.well-known/acme-challenge/` koji vraća sadržaj (NE redirect, ostaje 200)** — to je smoke-friendly putanja koja dokazuje da nginx sluša :80.
- **9.1 smoke test se SVESNO ažurira (test-ownership prelazi na 9.2):** `test_ac8_container_smoke_http_200_and_security_headers` u `tests/test_production_stack.py` menja se da PRATI redirect (`requests.get(..., allow_redirects=True)` ILI `curl -IL`) i tvrdi DA SE SLEĆE na 200, **ILI** tvrdi da je `:80 /sr/` → 301 sa `Location` koji počinje `https://` (redirect korektnost), PLUS NOVI assert: `GET http://localhost/.well-known/acme-challenge/<probe>` NE redirect-uje (200/404 sa webroot-a, NIKAD 301).
- **Test-ownership je DOKUMENTOVAN:** AC12 + AC7 IMENUJU `test_ac8_container_smoke_http_200_and_security_headers` kao 9.1 test koji 9.2 PREUZIMA i ažurira; ova izmena je JEDINA dozvoljena izmena 9.1 testova (AC12). Redirect je BEZUSLOVAN (prod-realan), NE env-uslovljen — jednostavnije i deterministički.

**SM-D9 — nginx.conf je BIND-MOUNT u production.yml (NE samo baked u image). Rešava baked-conf nedostižnost.**
KRITIČNO: `compose/nginx/Dockerfile` radi `COPY compose/nginx/nginx.conf /etc/nginx/conf.d/default.conf` → conf je BAKED u image u BUILD vremenu. Ako deploy.sh samo `git pull` + `restart django`, izmena 443 nginx.conf-a NIKAD ne stigne do running nginx-a (image se ne rebuild-uje). **Razrešenje LOCKED: opcija A (najmanji correctness rizik) — nginx.conf postaje BIND-MOUNT.**
- production.yml nginx servis dobija NOVI bind-mount: `- ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro` (putanja relativna na `compose/` direktorijum gde production.yml živi → `compose/nginx/nginx.conf`).
- Posle `git pull` (koji ažurira `compose/nginx/nginx.conf` na disku), `docker compose up -d nginx` ILI `exec nginx nginx -s reload` aplicira novi conf BEZ image rebuild-a.
- Dockerfile `COPY` OSTAJE (image i dalje ima default conf kao fallback / za standalone run bez compose-a) — bind-mount ga override-uje u runtime-u. NE diram Dockerfile.
- Ovo EXTEND-uje 9.1 production.yml (dozvoljeno — story scope pokriva 443 wiring); 9.1 HTTP/80 ponašanje OSTAJE netaknuto (isti conf fajl, samo sada bind-mount-ovan umesto isključivo baked).
- Test asertuje da production.yml nginx servis ima bind-mount `nginx.conf:...default.conf` (mehanizam LOCK).

**SM-D7 — GHCR push lokacija: `ci.yml` build job (KANONSKI — LOCKED, NE "dev bira").**
ci.yml build job VEĆ ima `packages: write` + lowercase pattern + `push: false` placeholder. Aktiviram TAČNO tamo (`push: false`→`true` + `docker/login-action@v3`). **Zaključavam ci.yml jer:** (1) najmanja izmena (placeholder već postoji), (2) box `docker compose pull`-uje taj image u deploy.sh (AC1) — jedan izvor istine za image; (3) jednoznačan test-kontrakt (`test_deploy_workflow_config.py` cilja deploy.yml SSH/struktura; GHCR push-asert ide na ci.yml — vidi Task 9.4 napomenu). `deploy.yml` NE gradi/push-uje (izbegava dupli build i dvosmislen "OR" kontrakt iz ranije iteracije). Trade-off prihvaćen: push se dešava na svaki build branch (uklj. `master`), ne samo deploy branch — image tag je `:<sha>` (deterministički) pa nema kolizije; box povlači tačan tag koji deploy.sh referencira. NE sme razbiti ci.yml lint/test/build redosled (AC9 regresija).

**SM-D8 — nginx.conf ostaje statički conf (NE envsubst template) za v1.**
Parametrizacija domena kroz `envsubst`/template render-bi uvela kompleksnost (entrypoint koji renderuje conf). Za v1 `server_name`/cert-path ostaju literal `coricagrar.rs` u conf-u (mirror 9.1 placeholder), env-parametrizacija je u `nginx-init.sh` certbot pozivu. Ako Mihas potvrdi finalni domen (OQ-2), literal se update-uje jednokratno. Ovo je YAGNI-disciplina (mirror 9.1 SM stila).

**SM-D10 — First-deploy chicken-and-egg: BOOTSTRAP sekvenca (HTTP-only → certbot → aktiviraj 443).**
Na svežem box-u nginx sa AKTIVNIM `listen 443 ssl` blokom koji referencira NEPOSTOJEĆI cert FAIL-uje da starta (nginx odbija da učita ssl_certificate koji ne postoji). ALI certbot `--webroot` zahteva da nginx VEĆ sluša :80 da bi servirao ACME challenge. To je circular dependency koji se mora razrešiti redosledom. **LOCKED rešenje: HTTP-only bootstrap conf, pa swap na pun conf.**
- `compose/nginx/nginx.conf` se commit-uje sa AKTIVNIM 443 blokom (steady-state SOT za sve naredne deploy-eve).
- Za PRVI deploy, `nginx-init.sh` koristi ZASEBAN bootstrap conf `compose/nginx/nginx.bootstrap.conf` (HTTP-only: :80 blok sa ACME location-om + static/media/proxy, BEZ 443 bloka) tako da nginx starta bez cert-a i servira :80 ACME challenge.
- Sekvenca (nginx-init.sh, idempotentna — preskače ako cert već postoji): (1) `up -d nginx` sa bootstrap conf-om (bind-mount pokazuje na `nginx.bootstrap.conf` ILI se bootstrap conf privremeno kopira preko default.conf), (2) `certbot certonly --webroot -w /var/www/certbot ...` izda cert, (3) prebaci bind-mount/conf na pun `nginx.conf` (sa 443 blokom), (4) `up -d nginx` / `exec nginx -s reload` → 443 sada starta jer cert postoji.
- Alternativa (dokumentovana, NE default): seed self-signed dummy cert na cert-path pre prvog nginx start-a, pa swap pravim. Biram bootstrap-conf pristup jer ne ostavlja dummy cert artefakt.
- Test asertuje: `nginx.bootstrap.conf` postoji i NEMA `listen 443 ssl`; `nginx-init.sh` referencira bootstrap conf PRE certbot poziva i swap-uje na pun conf POSLE; AC6 "cert izdat pri prvom deploy-u" je sada konkretno dostižan.

## Open Questions

**OQ-1 (TVRD — go-live gate PRE prvog deploy-a): Deploy branch naming `master` → `main`/`staging`?**
Repo default je `master`, CI trigger-uje na `master`, ali planning artefakti (project-context, architecture) govore `main` + `staging`. Pre nego deploy.yml ide u funkciju, Mihas mora odlučiti: (a) preimenovati `master`→`main` + kreirati `staging` branch (usklađivanje sa planom), ILI (b) zadržati `master` i deploy-ovati sa njega (promeni `branches:` listu). SM-D1 default-uje na `[staging, main]`; trivijalno se menja. **Bez ove odluke deploy.yml se ne aktivira (push na nepostojeći branch = no-op).**

**OQ-2: Finalni produkcioni domen — `coricagrar.rs` (9.1 placeholder) vs `.example`/drugi?**
Različiti artefakti koriste `coricagrar.rs`, `coricagrar.example`, `coricagrar.rs`. certbot cert se izdaje za KONKRETAN domen sa važećim DNS A-record-om ka Hetzner IP-u. Mihas potvrđuje finalni domen + da DNS pokazuje na box PRE prvog certbot run-a (inače ACME challenge fail).

**OQ-3: Da li produkcija ikad sme auto-migrate-down u rollback-u?**
SM-D3 default: NE (data-loss). Preporuka ostaje manualan migrate-down uz svestan pregled. Mihas/produkt potvrđuje politiku rollback-a (verovatno: kod-rollback DA auto, šema-rollback NE auto).

**OQ-4: Staging box — postoji li zaseban CX22 staging VPS, ili se staging i prod dele?**
architecture:216 govori CX22 staging + CX32 production (zasebni). deploy.sh `staging`/`production` arg pretpostavlja 2 boxa (2 SSH host-a → 2 seta GH secrets ILI host iz branch-a). Mihas potvrđuje da li staging box postoji / IP / SSH pristup. Ako v1 ima samo prod box, staging grana se defer-uje.

**OQ-5: Required GitHub Actions secrets — ko ih postavlja i kada?**
`DEPLOY_SSH_KEY` (privatni ključ čiji javni deo je u `~/.ssh/authorized_keys` na box-u), `DEPLOY_HOST`, `DEPLOY_USER`. Mihas postavlja u repo Settings → Secrets PRE prvog deploy run-a. `ops/secrets/README.md` (Task 7.2) dokumentuje listu; vrednosti su van repo-a.

**OQ-6 (DEFER na 9.3/9.4 — NE blokira 9.2): Richer cert-renewal failure alerting.**
9.2 isporučuje BASELINE vidljivost neuspeha auto-renewal-a (cron/journal stderr — Task 4.5a). Bogatiji alerting (email notifikacija, UptimeRobot ping na cert-expiry, GlitchTip event na renewal fail) je SVESNO defer-ovan: **Story 9.4 (UptimeRobot)** pokriva uptime/expiry monitoring, **Story 9.3 (GlitchTip)** pokriva error eventove. 9.2 NE uvodi monitoring stack (scope-disciplina). Mihas/produkt potvrđuje da je baseline cron-vidljivost dovoljna do 9.3/9.4.

---

**Status: ready-for-dev** — Ultimate context engine analiza završena: 9.1 deliverable-i pročitani (production.yml, nginx.conf placeholder, start.sh, ci.yml, justfile), INFRA-VERIFY test pattern (test_production_stack.py / test_ci_workflow_config.py) internalizovan, project-context deploy ORDERING + architecture AR-13/AR-22 mapirani na AC-eve. Dev NE piše testove (TEA RED faza). **SM Fix iteracija 1: razrešeno 5 CRITICAL (C1 redirect/smoke test-ownership LOCKED, C2 `docker compose pull` ordered korak, C3 baked-conf → nginx.conf bind-mount, C4 certbot↔nginx path-contract `/var/www/certbot` + `/etc/letsencrypt`, C5 first-deploy bootstrap HTTP-only→certbot→443).** **SM Fix iteracija 2 (IMPROVEMENT/STYLE, best-effort): SM-D4 cross-ref typo→AC13/Task 9.3a; GHCR push lokacija LOCKED na ci.yml (SM-D7, ukloni "OR deploy.yml" dvosmislenost AC9/Task 9.4); production.yml header-komentar usklađivanje (Task 5.5a); cert-renewal failure vidljivost (Task 4.5a + OQ-6 defer 9.3/9.4); rollback irreversible-migration warning (Task 3.4a); dirty-tree guard (Task 2.4a/9.1c); on-box flock concurrency lock (Task 2.4b/9.1c); SSH least-privilege guidance (Task 7.2a); epics.md vs project-context ordering orientation napomena; `.gitattributes` verify-not-create (Task 2.2).** 15 AC (NIJEDAN obrisan) / 9 Task (sa novim sub-point-ima) / 10 SM-D / 6 OQ.
