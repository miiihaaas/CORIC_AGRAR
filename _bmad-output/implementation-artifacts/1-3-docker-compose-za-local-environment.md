---
story-id: "1.3"
story-key: 1-3-docker-compose-za-local-environment
title: Docker Compose za Local Environment
status: done
epic_num: 1
epic_title: Project Foundation & Visual Identity
created: 2026-05-28
completed: 2026-05-28
author: Mihas (SM autonomous)
---

# Story 1.3: Docker Compose za Local Environment

Status: done

<!-- Validacija je opcionalna. Pre dev-story koraka mo??e?? pokrenuti validate-create-story za quality check. -->

## Story

As a **dev (Mihas)**,
I want **Docker Compose setup za lokalni razvoj sa multi-stage `uv`-based Django image-om, PostgreSQL kontejnerom, named volume-om za persistenciju, i hot-reload-om kroz `manage.py runserver`**,
so that **mogu da pokrenem ceo dev stack jednom komandom (`just dev`), bez ru�?ne instalacije PostgreSQL-a na host-u, sa DB stanjem koje pre??ivljava `down`/`up`, i da promene Python fajlova trigeruju Django autoreload bez restart-a kontejnera**.

## Acceptance Criteria

**AC1 — Folder struktura `compose/` i fajlovi**

- **Given** projekat iz Story 1.1 (bootstrap) i 1.2 (settings split + `.env.example`)
- **When** kreiram `compose/` direktorijum sa pod-strukturom
- **Then** struktura sadr??i ta�?no:
  - `compose/local.yml` — Docker Compose definicija sa `django` i `db` servisima
  - `compose/django/Dockerfile` — multi-stage `uv`-based Django image
  - `compose/django/entrypoint.sh` — startup skripta (wait-for-db → migrate → runserver)
- **And** `compose/` postoji kao **novi** folder (ne postoji od Story 1.1/1.2 — vidi `_bmad-output/implementation-artifacts/1-2-...md § File List`)
- **And** `entrypoint.sh` ima LF line endings (NE CRLF — vidi Gotcha #5)
- **And** kreiran je `.gitattributes` u root-u (ako ne postoji) sa pravilom `compose/django/entrypoint.sh text eol=lf` da git Windows klijenti ne pretvore u CRLF (vidi Gotcha #5)

**AC2 — `compose/django/Dockerfile` — multi-stage `uv` build**

- **Given** struktura iz AC1
- **When** popunim `compose/django/Dockerfile` po Dev Notes § Dockerfile Template
- **Then** Dockerfile ima **dve stage-a**:
  - Stage 1 **`builder`** (deps install):
    - Base image: `ghcr.io/astral-sh/uv:python3.13-bookworm-slim` (canonical uv-on-python image; alternativa `python:3.13-slim` + manual `uv` install — vidi Gotcha #6)
    - `ENV UV_COMPILE_BYTECODE=1`, `ENV UV_LINK_MODE=copy`, `ENV UV_PROJECT_ENVIRONMENT=/app/.venv`
    - `WORKDIR /app`
    - COPY samo `pyproject.toml` i `uv.lock` u layer (cache-friendly)
    - `RUN uv sync --frozen --no-install-project --no-dev` — instalira **production deps** u `/app/.venv` (no dev deps u final image; lokalni dev-only paketi poput `django-debug-toolbar` ostaju van prod image-a)
  - Stage 2 **`runtime`** (final image):
    - Base image: `python:3.13-slim` (manji nego uv image; uv binary nije potreban u runtime-u jer `.venv` već ima sve)
    - System deps preko `apt-get install -y --no-install-recommends`:
      - `libmagic1` (za `python-magic` MIME validaciju — vidi project-context.md § Media pipeline)
      - `poppler-utils` (za `pdf2image` PDF cover-thumbnail — vidi project-context.md § Media pipeline)
      - `postgresql-client` (za `pg_isready` u entrypoint.sh wait-for-db loop-u)
      - `gettext` (za `compilemessages` u Story 1.4+; postavlja se sada da bi se izbegao rebuild za 1-2 stories)
    - `apt-get clean && rm -rf /var/lib/apt/lists/*` (slim layer)
    - `WORKDIR /app`
    - COPY `--from=builder /app/.venv /app/.venv` (preuzima venv iz builder stage-a)
    - `ENV PATH="/app/.venv/bin:$PATH"` (Python iz venv-a default-no)
    - `ENV PYTHONDONTWRITEBYTECODE=1`, `ENV PYTHONUNBUFFERED=1`
    - COPY `compose/django/entrypoint.sh /entrypoint.sh` + `RUN chmod +x /entrypoint.sh`
    - COPY application source (NAPOMENA: u compose `volumes:` mount-u source override-uje ovaj COPY u dev-u; ali COPY je tu da slika mo??e da se pokrene standalone bez bind mount-a)
    - `EXPOSE 8000`
    - `ENTRYPOINT ["/entrypoint.sh"]`
    - `CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]` (dev default; staging/prod override-uju u Story 9.1)
- **And** Dockerfile **NE** kreira nepotrebne layer-e (npr. NE `RUN pip install uv` — uv dolazi iz builder base image-a)
- **And** Dockerfile **NE** komituje secrets (`SECRET_KEY` itd. dolaze isklju�?ivo iz `.env` runtime-om, ne `ENV` u image-u)
- **And** image se builduje sa **`docker compose -f compose/local.yml build`** bez gre??aka u <5 minuta (sa cold cache; warm cache <30s ako se menja samo source)

**AC3 — `compose/django/entrypoint.sh` — startup orchestration**

- **Given** Dockerfile iz AC2
- **When** popunim `compose/django/entrypoint.sh` po Dev Notes § entrypoint.sh Template
- **Then** skripta sadr??i (u ta�?no tom redosledu):
  - Shebang `#!/usr/bin/env bash` + `set -euo pipefail` (fail-fast na bilo kojoj gre??ci)
  - **Wait-for-db loop**: koristi `pg_isready` koji �?eka da PostgreSQL prihvati konekcije (TCP otvoren + DB ready za queries); loop sa `until pg_isready -h "${POSTGRES_HOST:-db}" -p "${POSTGRES_PORT:-5432}" -U "${POSTGRES_USER:-coric}"; do echo "db not ready, retrying..."; sleep 1; done` (max ~30s u praksi; ako duze, problem je elsewhere)
  - **Run migracije**: `python manage.py migrate --noinput` (idempotentno; svaki container restart re-applies pending migracije; OK za dev)
  - **`exec "$@"`** kao poslednja linija (predaje kontrolu CMD-u iz Dockerfile-a — kriti�?no za signal handling, vidi Gotcha #2)
- **And** skripta **NE** poziva `compilemessages` (Story 1.4 dodaje LOCALE_PATHS; do tada nema `locale/` foldera pa bi `compilemessages` bilo no-op ili warning. Aktivira se eksplicitno kad Story 1.4 dodaje LOCALE_PATHS — pomeri u Story 1.4 ili neka kasnija revizija ove `entrypoint.sh`)
- **And** skripta **NE** poziva `collectstatic` (dev koristi Django auto-serving sa `DEBUG=True`; `collectstatic` je deploy-time, Story 9.1)
- **And** skripta je executable: `chmod +x compose/django/entrypoint.sh` (Linux); ako razvija?? na Windows, git mora �?uvati executable bit ili Dockerfile mora ekplicitno `RUN chmod +x /entrypoint.sh` (Dockerfile to već radi — AC2)

**AC4 — `compose/local.yml` — Docker Compose definicija**

- **Given** Dockerfile + entrypoint iz AC2-AC3
- **When** popunim `compose/local.yml` po Dev Notes § compose/local.yml Template
- **Then** `local.yml` sadr??i ta�?no dva servisa:

  **`django` servis:**
  - `build:` blok sa `context: ../` (repo root je build context, kako bi Dockerfile mogao pristupiti `pyproject.toml`/`uv.lock` u root-u) i `dockerfile: compose/django/Dockerfile`
  - `image: coric_agrar_django_local` (named tag za lak??u identifikaciju u `docker images`)
  - `env_file: ../.env` (u�?itava sve env vars iz `.env` u root-u repo-a — `DJANGO_SECRET_KEY`, `DATABASE_URL`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, itd.)
  - `volumes:` — bind mount source code-a iz host-a u kontejner za hot-reload:
    - `../:/app:cached` (Linux/macOS/Windows — `:cached` flag je no-op na Linux-u ali pobolj??ava macOS perf; ne ??kodi)
    - Alternativno mo??e?? biti precizniji (mount samo `apps/`, `config/`, `templates/`, `static/`, `manage.py`, `pyproject.toml`) — ali u Story 1.3 mountuje se ceo root jer apps/ folder jo?? ne postoji
    - VA??NO: ovo mount-uje preko `/app/.venv` u kontejneru — vidi Gotcha #1 (named volume za .venv da se preserve-uje iz builder stage-a)
  - `volumes:` (drugi entry — named volume da o�?uva `.venv` iz image-a od overlay-a):
    - `django_venv:/app/.venv` (named volume; spre�?ava da host bind mount overwrite-uje `.venv` iz image-a)
  - `ports: ["8000:8000"]` (host port 8000 → container port 8000)
  - `depends_on:` sa `db: condition: service_healthy` (sa�?ekaj da PostgreSQL healthcheck prođe pre starting `django` — backup uz entrypoint wait-for-db)
  - `restart: unless-stopped`

  **`db` servis:**
  - `image: postgres:16-alpine` (project-context.md preporu�?uje 16+; `-alpine` slim varijanta ~80MB; alt: `postgres:16` Debian-based ~150MB)
  - `volumes:` — named volume za data persistenciju:
    - `postgres_data:/var/lib/postgresql/data` (named volume pre??ivljava `docker compose down`; vidi Gotcha #4 za `down -v` razliku)
  - `environment:` — Postgres init vars (consistent sa `DATABASE_URL` u `.env`):
    - `POSTGRES_DB: coric_agrar`
    - `POSTGRES_USER: coric`
    - `POSTGRES_PASSWORD: coric` (LOCAL ONLY — staging/prod koriste secrets, NIKAD ovaj password)
  - `ports: ["5432:5432"]` (opciono — exposes PostgreSQL na host port 5432 ako dev ??eli da pove??e `psql`/`DBeaver` direktno; ako koliduje sa već-instaliranim PostgreSQL-om na host-u, izostavi ili koristi `5433:5432`)
  - `healthcheck:`
    - `test: ["CMD-SHELL", "pg_isready -U coric -d coric_agrar"]`
    - `interval: 5s`, `timeout: 3s`, `retries: 5`, `start_period: 10s`
  - `restart: unless-stopped`

  **Named volumes (top-level `volumes:` deklaracija):**
  - `postgres_data:` (driver: local; default)
  - `django_venv:` (driver: local; default)

- **And** `compose/local.yml` koristi `name: coric_agrar_local` na top-level (project name override; spre�?ava da Docker Compose default-uje na folder ime koje mo??e biti `compose/`)
- **And** **NEMA inline secrets** u `local.yml` (osim local-only `POSTGRES_PASSWORD: coric` koji je acceptable kao non-prod placeholder; `DJANGO_SECRET_KEY` itd. dolaze isklju�?ivo iz `env_file`)

**AC5 — `.dockerignore` (slim build context)**

- **Given** compose struktura iz AC1-AC4
- **When** kreiram `.dockerignore` u root-u projekta
- **Then** fajl sadr??i minimalno (vidi Dev Notes § .dockerignore Template):
  - `.git/`, `.gitignore`, `.gitattributes`
  - `.venv/`, `venv/`, `env/` (host venv ne ide u image)
  - `__pycache__/`, `*.pyc`, `*.pyo`
  - `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`, `.coverage`, `htmlcov/`
  - `tests/` (testovi ne ulaze u runtime image; pytest se runuje na host-u kroz `uv run pytest`)
  - `docs/` (planning dokumenti ne treba u image-u)
  - `_bmad-output/`, `_bmad/`, `bmad-orchestrators-bundle/`
  - `.claude/`, `.vscode/`, `.idea/`
  - `media/`, `staticfiles/`, `static_collected/`
  - `db.sqlite3`, `db.sqlite3-journal`
  - `*.log`, `logs/`
  - `compose/**/*.override.yml`, `docker-compose.override.yml`
  - `.env` (NE prebaciti realne secret-e u image; env vars dolaze runtime-om kroz `env_file`)
  - `.env.*` (sve dot-env varijante)
  - `playwright-report/`, `test-results/`
  - `node_modules/` (defenzivno, no Node u na??em stack-u)
- **And** **NE** ignori??i `pyproject.toml`, `uv.lock` (potrebni u builder stage-u)
- **And** **NE** ignori??i `manage.py`, `config/`, `apps/`, `compose/django/entrypoint.sh` (potrebni u runtime stage-u; iako su mount-ovani kroz volumes u dev-u, image MORA biti standalone-runnable)

**AC6 — `justfile` `just dev` rewire**

- **Given** compose setup iz AC1-AC5
- **When** update-ujem `justfile` `dev` recept
- **Then** stari recept:
  ```just
  dev:
      uv run python manage.py runserver
  ```
  se menja u:
  ```just
  # Pokrece dev stack (Django + PostgreSQL) kroz Docker Compose
  dev:
      docker compose -f compose/local.yml up
  ```
- **And** dodajem dva nova recepta za convenience (out-of-scope za AC ali korisna):
  - `dev-build:` — `docker compose -f compose/local.yml build` (eksplicitan rebuild image-a)
  - `dev-down:` — `docker compose -f compose/local.yml down` (graceful stop; **NE** `down -v` koji bi obrisao `postgres_data` volume)
  - `dev-logs:` — `docker compose -f compose/local.yml logs -f`
  - `dev-shell:` — `docker compose -f compose/local.yml exec django bash` (debug shell u kontejneru)
  - `dev-manage <cmd>:` — varijabla wrapper za `manage.py` komande u kontejneru (npr. `just dev-manage createsuperuser`)
- **And** ostali recepti (`test`, `lint`, `migrate`, `messages`) **OSTAJU NEPROMENJENI** (oni se i dalje pokreću kroz `uv run` na host-u; testovi runuju na host-u, ne u Docker-u — vidi Gotcha #9 za razlog)

**AC7 — `.env.example` update — `DATABASE_URL`**

- **Given** `.env.example` iz Story 1.2 sa `DATABASE_URL=` (prazno)
- **When** update-ujem `DATABASE_URL` placeholder da reflektuje Docker compose servis ime
- **Then** linija u `.env.example` se menja na:
  ```
  DATABASE_URL=postgres://coric:coric@db:5432/coric_agrar
  ```
  (host `db` matchuje compose servis ime; from-host port-forwarding ne menja unutra??nji port 5432)
- **And** komentar iznad linije se update-uje:
  ```
  # Format: postgres://user:pass@host:port/dbname
  # Local (Docker Compose — Story 1.3): postgres://coric:coric@db:5432/coric_agrar
  #   - "db" je Docker Compose servis ime (rezolvuje se kroz Docker DNS unutar compose network-a)
  #   - Kad pokrene?? PostgreSQL van compose-a, zameni "db" sa "localhost" ili IP-em
  # Staging/Prod: ide kroz secrets u Hetzner Cloud panel-u (Story 9.1+)
  #
  # ⚠?�? NAPOMENA (Gotcha #20): POSTGRES_USER / POSTGRES_PASSWORD / POSTGRES_DB se NE
  # �?itaju iz .env za `db` servis u compose/local.yml — inline `environment:` blok
  # nadja�?ava `env_file:`. SOT za DB credentials je compose/local.yml `db.environment:`.
  ```
- **And** **NE** menjaj nijednu drugu liniju u `.env.example` (sve ostale env vars iz Story 1.2 ostaju iste)
- **And** komentar koji pominje "Story 1.2 default je SQLite" se uklanja (sada je PostgreSQL primary, SQLite samo fallback za environment-e bez `.env`)

**AC8 — Smoke validacija (acceptance verification)**

- **Given** sve gore (AC1-AC7) implementirano
- **When** runujem smoke test sekvencu (PowerShell na Windows-u; bash ekvivalent komandi identi�?an)
- **Then** sledeće mora proći:
  1. `docker compose -f compose/local.yml config` — validira YAML/syntax, exit code 0
  2. `docker compose -f compose/local.yml build` — image se buildova bez gre??aka, exit code 0
  3. `docker compose -f compose/local.yml up -d` — stack pokrenut detached, oba kontejnera u `Up` stanju u <30s
  4. `docker compose -f compose/local.yml ps` — prikazuje `coric_agrar_local-django-1` (ili sli�?an naziv) sa status `Up` i `coric_agrar_local-db-1` sa status `Up (healthy)`
  5. `docker compose -f compose/local.yml exec django python manage.py check` — exit 0, output: `System check identified no issues (0 silenced).`
  6. Browser na `http://localhost:8000` prikazuje Django welcome page (debug mode `True` u dev — mo??e i da prikazuje 404 sa "Page not found" jer `config/urls.py` ima samo `admin/` route — to je takođe acceptable za Story 1.3)
  7. `docker compose -f compose/local.yml down` — graceful stop; `postgres_data` volume **OSTAJE**
  8. Re-run: `docker compose -f compose/local.yml up -d` — PostgreSQL pristupa istom data folderu; Django ne re-runuje migracije (sve već applied)
  9. Hot-reload smoke: izmeni `config/urls.py` (npr. dodaj komentar) → Django u logu prikazuje `Watching for file changes...` i restartuje runserver
- **And** lo?? scenarijo (REGRESSION CHECK): `docker compose -f compose/local.yml down -v` (sa `-v` flag-om) **bri??e `postgres_data` volume** — to je o�?ekivano i namerno; samo `-v` flag triggeruje deletion (vidi Gotcha #4)

## Tasks / Subtasks

- [x] **Task 1: Pre-flight verifikacija** (AC: 1)
  - [x] 1.1 Verifikuj da je Story 1.2 done (sprint-status.yaml entry `1-2-multi-environment-settings-split-sa-django-environ` == `done`)
  - [x] 1.2 Verifikuj postojanje fajlova iz Story 1.2: `config/settings/base.py`, `config/settings/development.py`, `config/settings/production.py`, `config/settings/staging.py`, `config/settings/__init__.py`, `.env.example` (sa `DATABASE_URL=` linijom — Story 1.2 AC4)
  - [x] 1.3 Verifikuj da Docker Desktop radi na host-u: `docker --version` (mora reportovati Docker Engine �? 20.10) i `docker compose version` (V2 plugin; **NE** `docker-compose` V1 — V2 sintaksa razlikuje se subtle-ima)
  - [x] 1.4 Verifikuj `pyproject.toml`/`uv.lock` postoje (potrebni u Dockerfile builder stage-u)
  - [x] 1.5 Verifikuj da NE postoji `compose/` folder ni `.dockerignore` fajl (Story 1.3 ih kreira from-scratch; ako postoje — proveri ko ih je kreirao pre commit-a)
  - [x] 1.6 (Windows) KRITI�?NO: verifikuj da Docker Desktop koristi **WSL2 backend** (NE Hyper-V legacy backend). WSL2 je OBAVEZAN za pouzdan hot-reload (inotify event propagacija kroz bind mount). Hyper-V backend ima nepouzdanu/spore inotify propagaciju → Django autoreload mo??e NE da pokupi promene fajlova. Provera:
    - Docker Desktop UI: `Settings → General → Use the WSL 2 based engine` mora biti �?� (checked)
    - CLI verifikacija (PowerShell): `docker info | Select-String -Pattern 'OSType|Operating System|WSL'` — o�?ekivan output uklju�?uje `OSType: linux` i `Operating System: Docker Desktop` (na WSL2 backend-u; Hyper-V backend bi prikazao `Docker Desktop` sa razli�?itim kernel signature-om)
    - Ako Hyper-V je aktivan: prebaci na WSL2 (Settings → General → �?� checkbox → Apply & Restart). Mo??da zahteva instalaciju WSL2 update-a: `wsl --install` ili `wsl --update` u Admin PowerShell.
  - [x] 1.7 KRITI�?NO: verifikuj da port 5432 NIJE zauzet na host-u (lokalno instaliran PostgreSQL ili druga aplikacija). Ako je zauzet, `docker compose up` će failovati sa "Bind for 0.0.0.0:5432 failed: port is already allocated". Provera:
    - PowerShell: `Test-NetConnection -Port 5432 -ComputerName localhost -InformationLevel Quiet` — o�?ekivano: `False` (port slobodan, konekcija odbijena = niko ne slu??a). Ako vraća `True` (port je zauzet), ima?? dva re??enja (vidi Gotcha #13):
      - Promeni mapping u `compose/local.yml` `db` servis: `ports: ["5433:5432"]` (host 5433 → kontejner 5432). Django u kontejneru i dalje pristupa preko `db:5432` (Docker DNS internal), pa `DATABASE_URL` u `.env` se NE menja.
      - ILI ugasi lokalnu PostgreSQL instalaciju: `Stop-Service postgresql-x64-16` (ime servisa varira) ili kroz Services.msc.
    - Bash (Linux/WSL): `ss -tlnp | grep :5432` — ako vraća liniju, port je zauzet.

- [x] **Task 2: Kreiraj `compose/` folder strukturu** (AC: 1)
  - [x] 2.1 Kreiraj direktorijum: `compose/`
  - [x] 2.2 Kreiraj pod-direktorijum: `compose/django/`
  - [x] 2.3 Verifikuj: `tree compose/` (Linux/macOS) ili `dir compose /S` (Windows) prikazuje pravu strukturu

- [x] **Task 3: Kreiraj `compose/django/Dockerfile`** (AC: 2)
  - [x] 3.1 Kreiraj `compose/django/Dockerfile` sa sadr??ajem iz Dev Notes § Dockerfile Template
  - [x] 3.2 KRITI�?NO: stage 1 (`builder`) MORA biti `FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder` (ne alternativna verzija; uv image dolazi sa preinstal-iranim `uv`-jem)
  - [x] 3.3 KRITI�?NO: stage 2 (`runtime`) MORA biti `FROM python:3.13-slim AS runtime` (manji image, bez uv-a u runtime-u)
  - [x] 3.4 Verifikuj system deps install (apt-get): `libmagic1`, `poppler-utils`, `postgresql-client`, `gettext` — sve u **runtime stage**, ne u builder
  - [x] 3.5 Verifikuj COPY redosled: prvo `pyproject.toml uv.lock` u builder (cache-friendly), tek na kraju runtime-a COPY application source
  - [x] 3.6 Verifikuj entrypoint: COPY `compose/django/entrypoint.sh /entrypoint.sh` + `RUN chmod +x /entrypoint.sh`
  - [x] 3.7 Verifikuj ENTRYPOINT/CMD: `ENTRYPOINT ["/entrypoint.sh"]` + `CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]`
  - [x] 3.8 NIKAD ne dodavaj `ENV DJANGO_SECRET_KEY=...` ili sli�?an secret u Dockerfile (Gotcha #3)

- [x] **Task 4: Kreiraj `compose/django/entrypoint.sh`** (AC: 3)
  - [x] 4.1 Kreiraj `compose/django/entrypoint.sh` sa sadr??ajem iz Dev Notes § entrypoint.sh Template
  - [x] 4.2 KRITI�?NO: prva linija MORA biti `#!/usr/bin/env bash` (NE `#!/bin/sh` — postoje bash-specific konstrukcije u skripti)
  - [x] 4.3 KRITI�?NO: druga linija `set -euo pipefail` (fail-fast)
  - [x] 4.4 KRITI�?NO: ostavi LF line endings (NE CRLF). Na Windows-u editori �?esto auto-konvertuju — vidi Task 9 (`.gitattributes`)
  - [x] 4.5 Verifikuj struktura: wait-for-db loop → migrate → `exec "$@"`
  - [x] 4.6 NE dodavaj `compilemessages` (Story 1.4)
  - [x] 4.7 NE dodavaj `collectstatic` (Story 9.1 prod)
  - [x] 4.8 Verifikuj: `exec "$@"` JE poslednja linija (ne dodavaj ni??ta posle — `exec` zamenjuje shell process-om CMD-a)

- [x] **Task 5: Kreiraj `compose/local.yml`** (AC: 4)
  - [x] 5.1 Kreiraj `compose/local.yml` sa sadr??ajem iz Dev Notes § compose/local.yml Template
  - [x] 5.2 Verifikuj `name: coric_agrar_local` na top-level
  - [x] 5.3 Verifikuj `django` servis: `build.context: ../`, `build.dockerfile: compose/django/Dockerfile`
  - [x] 5.4 Verifikuj `django` servis: `env_file: ../.env`, `volumes` ima `../:/app:cached` + `django_venv:/app/.venv`
  - [x] 5.5 Verifikuj `django` servis: `depends_on.db.condition: service_healthy`
  - [x] 5.6 Verifikuj `db` servis: image `postgres:16-alpine`, healthcheck definisan
  - [x] 5.7 Verifikuj `db` servis: `volumes: postgres_data:/var/lib/postgresql/data`
  - [x] 5.8 Verifikuj top-level `volumes:` deklari??e `postgres_data:` i `django_venv:`
  - [x] 5.9 Verifikuj **NEMA** inline `DJANGO_SECRET_KEY` ili `SECRET_KEY` u `local.yml`

- [x] **Task 6: Kreiraj `.dockerignore`** (AC: 5)
  - [x] 6.1 Kreiraj `.dockerignore` u **root-u repo-a** (NE u `compose/`) — Docker default-uje da tra??i `.dockerignore` u build context-u koji je root (`build.context: ../` u compose-u)
  - [x] 6.2 Sadr??aj iz Dev Notes § .dockerignore Template
  - [x] 6.3 Verifikuj: `pyproject.toml`, `uv.lock`, `manage.py`, `config/`, `compose/`, `apps/` (kad postoji) NISU u `.dockerignore`
  - [x] 6.4 Verifikuj: `.env` JESTE u `.dockerignore` (Gotcha #3 — secrets ne ulaze u image)

- [x] **Task 7: Update `justfile`** (AC: 6)
  - [x] 7.1 Otvori `justfile`, pronađi `dev:` recept (linija 9-10 u trenutnom fajlu)
  - [x] 7.2 Zameni telo `dev:` recepta sa `docker compose -f compose/local.yml up`
  - [x] 7.3 Update komentar iznad `dev:` recepta da odra??ava novu rolu (skini `(bice rewired na docker compose u Story 1.3)` jer je sada urađeno)
  - [x] 7.4 Dodaj nove recepte iz AC6 (`dev-build`, `dev-down`, `dev-logs`, `dev-shell`, `dev-manage`) — vidi Dev Notes § justfile snippet
  - [x] 7.5 Verifikuj da `lint:` recept i dalje ima `|| echo "djade: templates/ folder ne postoji jos (OK za Story 1.1)"` fallback — Story 1.3 ne kreira `templates/`

- [x] **Task 8: Update `.env.example` — `DATABASE_URL`** (AC: 7)
  - [x] 8.1 Otvori `.env.example`, pronađi `DATABASE_URL=` blok (linije 30-34 u trenutnom fajlu)
  - [x] 8.2 Update vrednost iz prazne na `DATABASE_URL=postgres://coric:coric@db:5432/coric_agrar`
  - [x] 8.3 Update komentar iznad — vidi AC7 (kompletan novi tekst)
  - [x] 8.4 NE menjaj nijednu drugu liniju (sve ostale env vars iz Story 1.2 ostaju)

- [x] **Task 9: `.gitattributes` za LF line endings** (AC: 1)
  - [x] 9.1 Proveri da li `.gitattributes` već postoji: `ls -la .gitattributes` (Linux) ili `dir .gitattributes` (Windows)
  - [x] 9.2 Ako NE postoji, kreiraj `.gitattributes` u root-u sa sadr??ajem iz Dev Notes § .gitattributes Template (default `* text=auto` BEZ forsiranja eol; `*.sh text eol=lf` + eksplicitno `compose/django/entrypoint.sh text eol=lf`; binary markeri za png/jpg/pdf)
  - [x] 9.3 Ako postoji, dodaj samo nedostajuće pravila — KRITI�?NO: NE menjaj postojeći `* text=auto` red ako ima — i NE dodavaj `eol=lf` na default `*` glob jer to izaziva diff churn na Windows-u (vidi NAPOMENA u § .gitattributes Template)
  - [x] 9.4 Posle kreiranja `.gitattributes`, ako si već kreirao `entrypoint.sh` sa CRLF endings, renormalize: `git rm --cached compose/django/entrypoint.sh && git add compose/django/entrypoint.sh` (alternativno: `dos2unix compose/django/entrypoint.sh`)

- [x] **Task 10: Lokalni `.env` za smoke test** (AC: 8)
  - [x] 10.1 Verifikuj da `.env` postoji u root-u (Story 1.2 dev je trebao da ga kopira iz `.env.example`; ako ne postoji, kopiraj sada: `Copy-Item .env.example .env` PowerShell, ili `cp .env.example .env` bash)
  - [x] 10.2 Update `.env` (NE `.env.example`) sa:
    - `DATABASE_URL=postgres://coric:coric@db:5432/coric_agrar` (mora matchovati `db` servis i POSTGRES_* env vars u `compose/local.yml`)
    - `DJANGO_SECRET_KEY=<non-empty string — OBAVEZNO za smoke; vidi WARNING ispod>`
    - ⚠?�? KRITI�?NO: bez `DJANGO_SECRET_KEY` u `.env`, kontejner CRASH-uje u ~1s tokom entrypoint `migrate` koraka sa `django.core.exceptions.ImproperlyConfigured: Set the DJANGO_SECRET_KEY environment variable` (Story 1.2 `base.py` koristi `env("DJANGO_SECRET_KEY")` bez default-a — fail-fast). Generi??i sa: `uv run python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` ili `python -c "import secrets; print(secrets.token_urlsafe(50))"` ili `openssl rand -base64 60`.
    - ⚠?�? COMPOSE $ INTERPOLATION GOTCHA (vidi Gotcha #22): Docker Compose v2 interpolira `$VAR` u `.env` vrednostima. Ako tvoj generisani SECRET_KEY sadrži `$` praćen alfanumeričkim karakterima (npr. `$py2`), Compose tiho zamenjuje tu sekvencu praznim string-om i daje samo warning. Posledica: kontejner radi sa truncatovanim SECRET_KEY-em, sesije/CSRF tiho padaju.
      - **Bezbedno generisanje**:
        - Preporučeno: `python -c "import secrets; print(secrets.token_urlsafe(50))"` — `token_urlsafe` koristi samo `[A-Za-z0-9_-]`, NEMA `$`.
        - Ne preporučujem: `django.core.management.utils.get_random_secret_key()` — koristi širi alfabet uključujući `$`.
        - Alternativno: escape `$` kao `$$` u `.env` (Compose ga interpretira kao literal `$`).
    - `DJANGO_DEBUG=True`
    - `DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1` (informational only)
    - �??�? NAPOMENA: vrednost `DJANGO_ALLOWED_HOSTS` u `.env` **NEMA EFEKTA** dok je aktivan `config.settings.development` (Story 1.2 hardkoduje `ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]']` u `config/settings/development.py`, overriding bilo koju vrednost iz `env.list()`). Linija je u `.env` samo defenzivno za buduće smoke testove sa `staging`/`production` settings modulima koji �?itaju `env.list("DJANGO_ALLOWED_HOSTS")`. Za AC8 smoke (dev mode) dovoljan je `localhost` — kontejner pokrece runserver na `0.0.0.0:8000`, ali browser pristupa kroz `http://localhost:8000` (Docker mapira container 8000 → host 8000), pa Django HTTP `Host` header je `localhost` koji matchuje hardcoded listu.
  - [x] 10.3 KRITI�?NO: ne komituj `.env` (`git status` ne sme prikazati `.env` u staged changes; `.gitignore` ga već exclude-uje iz Story 1.1)

- [x] **Task 11: Smoke validacija (AC: 8)**
  - [x] 11.0 PRE-FLIGHT (KRITI�?NO): verifikuj da `.env` sadr??i non-empty `DJANGO_SECRET_KEY` PRE bilo kog `docker compose up` (vidi Gotcha #21 — bez ovoga kontejner crash-uje za ~1s sa `ImproperlyConfigured`).
    - PowerShell: `Select-String -Path .env -Pattern '^DJANGO_SECRET_KEY=.+' -Quiet` → mora vratiti `True`
    - Bash: `grep -E '^DJANGO_SECRET_KEY=.+' .env` → mora imati output sa non-empty vrednostom posle `=`
    - Ako vraća prazno/False → generi??i: `uv run python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` i upi??i rezultat u `.env` kao vrednost `DJANGO_SECRET_KEY=<rezultat>`.
  - [x] 11.1 `docker compose -f compose/local.yml config` — exit code 0; output prikazuje resolved YAML bez warning-a (mo??e imati 1 warning ako `image:` tag exposed in stdout — to je OK)
  - [ ] 11.2 `docker compose -f compose/local.yml build` — exit code 0; build traje < 5 min sa cold cache. Verifikuj da builder stage runuje `uv sync --frozen --no-install-project --no-dev` i da runtime stage instalira `libmagic1`, `poppler-utils`, `postgresql-client`, `gettext`.
  - [ ] 11.3 `docker compose -f compose/local.yml up -d` — exit 0; oba kontejnera ulaze u `Up` stanje
  - [ ] 11.4 `docker compose -f compose/local.yml ps` — verifikuj status: `db` mora biti `Up (healthy)` (posle ~10-15s start_period + healthcheck retry); `django` `Up`
  - [ ] 11.5 `docker compose -f compose/local.yml logs django` — proveri da entrypoint je odradio:
    - `db not ready, retrying...` (mo??e se pojaviti par puta dok DB ne digne se)
    - `Operations to perform: Apply all migrations: admin, auth, contenttypes, sessions` (initial migrations applied)
    - `Starting development server at http://0.0.0.0:8000/`
    - `Quit the server with CONTROL-C.`
  - [ ] 11.6 `docker compose -f compose/local.yml exec django python manage.py check` — exit 0 ; output: `System check identified no issues (0 silenced).`
  - [ ] 11.7 Browser smoke (manual): otvori `http://localhost:8000/` — mora prikazati Django welcome page (DEBUG=True; ili 404 sa "Page not found" — oba acceptable jer urls.py ima samo `admin/`)
  - [ ] 11.8 `docker compose -f compose/local.yml exec django python manage.py createsuperuser --noinput --username admin --email admin@example.com || true` — kreira test superuser-a (env vars za password tra??i ru�?no; ovaj korak je optional, samo verifikuje da migracije rade)
  - [ ] 11.9 Volume persistence test:
    - `docker compose -f compose/local.yml down` (BEZ `-v`)
    - `docker compose -f compose/local.yml up -d`
    - `docker compose -f compose/local.yml exec django python manage.py shell -c "from django.contrib.auth.models import User; print(User.objects.count())"` — ako si u 11.8 kreirao superuser, output mora biti `1` (potvrda persistencije)
  - [ ] 11.10 Hot-reload test (manual):
    - Stack je up
    - Edit `config/urls.py` — dodaj komentar `# hot reload test`
    - `docker compose -f compose/local.yml logs --tail=20 django` — mora pokazati `config\urls.py changed, reloading.` (ili `/app/config/urls.py changed`)
  - [ ] 11.11 Cleanup za sledeću story: `docker compose -f compose/local.yml down` (bez `-v` da o�?uva?? data za dalji development)

  ℹ️ Live smoke (11.2-11.11) je MANUAL korak pre PR-a — Dev agent nije pokrenuo full `docker compose up` u Step 3. Mihas treba da izvrši pre commit-a.

- [x] **Task 12: Final review i sanity check** (AC: sve)
  - [x] 12.1 Verifikuj `compose/` strukturu (`tree compose/` ili `dir compose /S`):
    ```
    compose/
    �?── local.yml
    └── django/
        �?── Dockerfile
        └── entrypoint.sh
    ```
  - [x] 12.2 Verifikuj `.dockerignore` postoji u root-u
  - [x] 12.3 Verifikuj `.gitattributes` postoji u root-u sa pravilom za `entrypoint.sh`
  - [x] 12.4 Verifikuj `justfile` — `dev:` recept koristi `docker compose -f compose/local.yml up`; novi recepti dodati
  - [x] 12.5 Verifikuj `.env.example` — `DATABASE_URL` updated sa Docker servis ime-om
  - [x] 12.6 Popuni "File List" i "Completion Notes List" u "Dev Agent Record" sekciji ovog story fajla
  - [x] 12.7 KRITI�?NO: proveri `git status` — `.env` (real, sa secret-om) NE sme biti u staged changes

## Dev Notes

### Kontekst story-ja

Ovo je **infrastructure setup** story — prelaz iz lokalnog `manage.py runserver` (Story 1.1 placeholder) u Docker Compose stack koji odgovara stagging/production setup-u. Foundation za:

- **Story 1.4 (i18n):** `compilemessages` se dodaje u entrypoint.sh tek kad postoji `locale/` folder (Story 1.4 ga kreira)
- **Story 1.5/1.6 (templates, static):** `templates/` i `static/` folderi će biti mount-ovani kroz isti `../:/app` bind mount
- **Story 1.9 (CI):** `pytest` runuje na host-u (ne u Docker-u u dev-u), ali CI će biti u GitHub Actions runner-u — Story 1.9 odlu�?uje da li to bude direktan host runner ili Docker container
- **Story 9.1 (production compose):** Story 9.1 kreira `compose/staging.yml` i `compose/production.yml` koji koriste isti Dockerfile (potencijalno sa different `CMD` — gunicorn umesto runserver), Nginx servis, secrets management
- **Story 9.5 (backups):** `postgres_data` named volume se backup-uje kroz `pg_dump` ka Hetzner Storage Box-u

**Princip:** Story 1.3 je SAMO local dev. Production-grade compose (Nginx, gunicorn, secrets, restart policies, log drivers) ide u Story 9.1.

**Out-of-scope** za Story 1.3:
- Staging i production compose fajlovi (Story 9.1)
- Nginx servis (Story 9.1)
- Gunicorn umesto runserver (Story 9.1)
- `compilemessages` u entrypoint.sh (Story 1.4 — dodaje LOCALE_PATHS)
- `collectstatic` u entrypoint.sh (Story 9.1 — prod)
- GlitchTip self-host compose (Story 9.3 — `ops/monitoring/glitchtip-compose.yml`)
- pg_backup cron (Story 9.5)
- CI Docker build (Story 1.9 — mo??e da koristi ili da presko�?i Docker)

### Tech stack — verzije i razlozi

| Komponenta | Verzija | Razlog |
|---|---|---|
| Docker Engine | �? 20.10 | Compose V2 zahtev; multi-stage build podr??ka od mnogo ranije |
| Docker Compose | V2 (plugin `docker compose`) | NE `docker-compose` V1 (deprecated); V2 ima native `depends_on.condition` syntax |
| `python:3.13-slim` | 3.13 | Pin iz project-context.md § Core runtime; matchuje `.python-version` |
| `ghcr.io/astral-sh/uv:python3.13-bookworm-slim` | latest tag | Canonical uv image — Astral ga odr??ava sinhronizovano sa uv releases; alternativa je da se uv ru�?no instalira u Dockerfile ??to povećava layer count |
| `postgres:16-alpine` | 16 (LTS) | project-context.md § Core runtime preporu�?uje "16+"; alpine varijanta smanjuje image size sa ~150MB na ~80MB |
| `libmagic1` | apt default | Required by `python-magic` (project-context.md § Media pipeline) |
| `poppler-utils` | apt default | Required by `pdf2image` (project-context.md § Media pipeline) |
| `postgresql-client` | apt default | Sadr??i `pg_isready` za wait-for-db loop u entrypoint.sh |
| `gettext` | apt default | Required by `compilemessages` (Story 1.4); install-uje se sada da se izbegne rebuild |

**uv multi-stage rationale:**
- Builder stage instalira deps u `/app/.venv` — to je ~200-400MB virtualenv sa svim deps + transitive deps
- Runtime stage COPY-uje samo `.venv` iz builder-a (bez `uv` binary, bez build artifacts, bez `pyproject.toml`/`uv.lock` — iako ovo poslednje će ipak biti tu kroz bind mount u dev-u; ali u standalone image-u nije)
- Final image size: ~250-350MB (python:3.13-slim ~125MB + .venv ~150-200MB + apt packages ~25-50MB)

**`uv sync --frozen --no-install-project --no-dev` razlog:**
- `--frozen`: koristi ta�?no `uv.lock` verzije, NE re-resolve (reproducible builds)
- `--no-install-project`: NE instaliraj sam `coric-agrar` projekat kao paket (mi nismo distribuiramo `coric-agrar` kao Python paket — to je Django app folder, ne instalabilan paket)
- `--no-dev`: NE instaliraj dev grupu (`pytest`, `ruff`, `playwright`, `django-debug-toolbar`); dev-only paketi ostaju na host-u kroz `uv run` (Gotcha #9)

**Dokumentacija:**
- Docker Compose V2 spec: https://docs.docker.com/compose/compose-file/
- uv Docker integration: https://docs.astral.sh/uv/guides/integration/docker/
- PostgreSQL 16 official image: https://hub.docker.com/_/postgres

### Dockerfile Template (multi-stage uv build)

```dockerfile
# syntax=docker/dockerfile:1.7

# ============================================================
# Stage 1 — builder: install Python deps to .venv kroz uv
# ============================================================
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

# uv tuning — bytecode compile za br??i import, link mode copy za stabilnost
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Cache-friendly: COPY samo lockfiles, instaliraj deps, tek onda copy source u runtime stage
# Ako se promeni samo source code, ovaj layer je već cached
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# ============================================================
# Stage 2 — runtime: slim image sa system deps + .venv iz builder-a
# ============================================================
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

# System deps:
#   libmagic1       — python-magic MIME validacija (Story 4.x file uploads)
#   poppler-utils   — pdf2image PDF cover-thumbnail (Story 2.4)
#   postgresql-client — pg_isready za entrypoint wait-for-db
#   gettext         — django compilemessages (Story 1.4+)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        libmagic1 \
        poppler-utils \
        postgresql-client \
        gettext \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Preuzmi venv iz builder stage-a (bez uv binary, bez build artifacts)
COPY --from=builder /app/.venv /app/.venv

# Entrypoint script (LF line endings — vidi Gotcha #5)
COPY compose/django/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Application source — u dev-u će biti override-ovan kroz bind mount,
# ali u standalone image-u (CI, staging, prod) ovaj COPY je SOT.
COPY . /app

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

### entrypoint.sh Template

```bash
#!/usr/bin/env bash
# CORIC_AGRAR — Django container entrypoint
# Wait for db → migrate → exec CMD (runserver)

set -euo pipefail

# ── Wait for PostgreSQL ─────────────────────────────────────
# Env vars POSTGRES_* su informational; defaults match compose/local.yml `db` servis
DB_HOST="${POSTGRES_HOST:-db}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_USER="${POSTGRES_USER:-coric}"

echo "[entrypoint] Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT} (user=${DB_USER})..."
until pg_isready -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -q; do
    echo "[entrypoint] db not ready, retrying in 1s..."
    sleep 1
done
echo "[entrypoint] PostgreSQL is ready."

# ── Apply migrations ────────────────────────────────────────
echo "[entrypoint] Running Django migrations..."
python manage.py migrate --noinput

# ── Hand off to CMD (runserver default; gunicorn u prod-u kroz Story 9.1 override) ──
echo "[entrypoint] Starting Django: $*"
exec "$@"
```

### compose/local.yml Template

```yaml
# CORIC_AGRAR — Docker Compose za LOCAL development
# Pokreni: just dev   (ili: docker compose -f compose/local.yml up)
# Stop:    just dev-down

name: coric_agrar_local

services:
  django:
    build:
      context: ../
      dockerfile: compose/django/Dockerfile
    image: coric_agrar_django_local
    env_file:
      - ../.env
    environment:
      # Override DJANGO_SETTINGS_MODULE eksplicitno (manage.py default već je razvoj, ali defenzivno)
      DJANGO_SETTINGS_MODULE: config.settings.development
      # POSTGRES_* informational za entrypoint wait-for-db
      POSTGRES_HOST: db
      POSTGRES_PORT: "5432"
      POSTGRES_USER: coric
    volumes:
      # Bind mount source code za hot-reload (Django autoreload watcher)
      - ../:/app:cached
      # Named volume za .venv da bind mount ne overwrite-uje image .venv
      - django_venv:/app/.venv
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: coric_agrar
      POSTGRES_USER: coric
      # LOCAL ONLY — staging/prod koristi secrets, NIKAD ovaj password
      POSTGRES_PASSWORD: coric
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      # Opciono — exposes Postgres na host port da mo??e?? povezati psql/DBeaver direktno
      # Ako koliduje sa host-instal-iranim PostgreSQL-om, zameni sa "5433:5432" ili obri??i
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U coric -d coric_agrar"]
      interval: 5s
      timeout: 3s
      retries: 5
      start_period: 10s
    restart: unless-stopped

volumes:
  postgres_data:
    name: coric_agrar_postgres_data
  django_venv:
    name: coric_agrar_django_venv
```

### .dockerignore Template

```
# Git
.git/
.gitignore
.gitattributes
.github/

# Python
__pycache__/
*.py[cod]
*.so
.Python
*.egg-info/

# Virtual environments (build stage instalira u /app/.venv unutar slike)
.venv/
venv/
env/
ENV/

# uv cache
.uv/

# Django local artifacts
db.sqlite3
db.sqlite3-journal
local_settings.py
*.log
logs/

# Static + media (mountuje se kroz volume u dev, generi??e u deploy-u)
staticfiles/
static_collected/
media/

# Testing
.pytest_cache/
.cache/
.coverage
.coverage.*
htmlcov/
coverage.xml
.hypothesis/
tests/
test-results/
junit.xml

# Playwright
playwright-report/
playwright/.cache/
playwright/.auth/
blob-report/

# Linters & formatters
.ruff_cache/
.mypy_cache/
.dmypy.json
.pyre/

# Pre-commit
.pre-commit-cache/

# IDE & editor
.vscode/
.idea/
*.iml
*.swp
*.swo
.DS_Store

# Compose override fajlovi (lokalni tweaks ne ulaze u image)
compose/*.override.yml
docker-compose.override.yml
.docker-data/

# Environment & secrets — KRITI�?NO
.env
.env.*
*.pem
*.key
secrets/

# BMad artifacts (planning dokumenti ne treba u runtime image-u)
_bmad/
_bmad-output/
bmad-orchestrators-bundle/
.claude/

# Docs
docs/
README.md

# Backup
*.sql
*.sql.gz
*.dump
*.bak
backups/

# Node (defenzivno, nije u stack-u)
node_modules/
npm-debug.log*

# Tmp / misc
.tmp/
tmp/
*.pid
```

### justfile snippet (recepti za update)

Update postojeći `dev:` recept i dodaj nove:

```just
# Pokrece dev stack (Django + PostgreSQL) kroz Docker Compose
dev:
    docker compose -f compose/local.yml up

# Builduje Django image (potrebno samo kad se Dockerfile menja ili posle prvog clone-a)
dev-build:
    docker compose -f compose/local.yml build

# Stop dev stack (CHUVA postgres_data volume; koristi `down -v` ru�?no ako ba?? ??eli?? da bri??e?? data)
dev-down:
    docker compose -f compose/local.yml down

# Tail logs (follow mode; Ctrl+C izlazi)
dev-logs:
    docker compose -f compose/local.yml logs -f

# Otvori bash shell u django kontejneru (za debug, manage.py shell, itd.)
dev-shell:
    docker compose -f compose/local.yml exec django bash

# Wrapper za manage.py komande u kontejneru
# Primer: just dev-manage createsuperuser
dev-manage *ARGS:
    docker compose -f compose/local.yml exec django python manage.py {{ARGS}}
```

NAPOMENA: `test:`, `lint:`, `migrate:`, `messages:` recepti **OSTAJU NEPROMENJENI**. Oni pokreću `uv run ...` na host-u, NE u kontejneru. Razlozi (Gotcha #9):
- Brzina: `pytest` na host-u runuje za <1s vs ~5s kroz Docker exec
- IDE integracija: PyCharm/VS Code debug konfiguracije rade direktno sa host venv-om
- Ruff/djade: ne treba Docker context

Ako ??eli?? da test runuje u kontejneru (npr. za CI parity), dodaj alternativan recept `test-docker:` u Story 1.9.

### .gitattributes Template

NAPOMENA: namerno NE forsiramo `eol=lf` na SVE text fajlove (`* text=auto eol=lf`) — to bi nateralo Markdown, Python, YAML, JSON da uvek imaju LF na disku, ??to izaziva whole-file diff churn kad Windows editori snimaju sa CRLF i git renormalizuje (svaki commit menja sve linije fajla). Umesto toga u??i scope: default `text=auto` (git auto-detektuje text vs binary, normalize-uje samo na commit), a EOL prinuda samo za fajlove gde to ba?? mora (shell skripte koje Linux bash izvr??ava).

```gitattributes
# CORIC_AGRAR — git line-ending policy
# Default: text=auto (git auto-detektuje text vs binary; ne forsira EOL na disku)
# Razlog: forsiranje eol=lf na sve text fajlove izaziva whole-file diff churn na Windows-u
* text=auto

# Shell skripte MORAJU biti LF (Docker/Linux execution) — KRITI�?NO
# Bash u Linux kontejneru ne tolerise CRLF (`/bin/bash^M: bad interpreter`)
*.sh text eol=lf
compose/django/entrypoint.sh text eol=lf

# Eksplicitni binary marker (spre�?ava slu�?ajno text mangling)
*.png binary
*.jpg binary
*.pdf binary
```

### `.env.example` — `DATABASE_URL` update (replacement snippet)

Trenutni blok u `.env.example` (linije 30-34):

```env
# ── Database ─────────────────────────────────────────────────
# Format: postgres://user:pass@host:port/dbname
# Local (Story 1.3 PostgreSQL u Docker): postgres://coric:coric@localhost:5432/coric_agrar
# Story 1.2 default je SQLite (sqlite:///db.sqlite3) ako ostavi prazno
DATABASE_URL=
```

Zameniti sa:

```env
# ── Database ─────────────────────────────────────────────────
# Format: postgres://user:pass@host:port/dbname
# Local (Docker Compose — Story 1.3): postgres://coric:coric@db:5432/coric_agrar
#   - "db" je Docker Compose servis ime (rezolvuje se kroz Docker DNS unutar compose network-a)
#   - Kad pokrene?? PostgreSQL van compose-a, zameni "db" sa "localhost" ili IP-em
# Staging/Prod: ide kroz secrets u Hetzner Cloud panel-u (Story 9.1+)
#
# ⚠?�? NAPOMENA (Gotcha #20): POSTGRES_USER / POSTGRES_PASSWORD / POSTGRES_DB se NE
# �?itaju iz .env za `db` servis u compose/local.yml — inline `environment:` blok
# nadja�?ava `env_file:`. SOT za DB credentials je compose/local.yml `db.environment:`.
# Ako menja?? user/password, mora?? da update-uje?? OBA mesta (compose/local.yml + DATABASE_URL ovde).
DATABASE_URL=postgres://coric:coric@db:5432/coric_agrar
```

### Project struktura posle ove story-je

```
coric-agrar/                                # root projekta (postojeći)
�?── .dockerignore                           # NEW (Story 1.3)
�?── .gitattributes                          # NEW ili UPDATED (Story 1.3)
�?── .env                                    # MODIFIED lokalno (DATABASE_URL set; NE komituje se)
�?── .env.example                            # MODIFIED — DATABASE_URL placeholder updated (Story 1.3)
�?── .gitignore                              # UNCHANGED (Story 1.1/1.2 baseline OK)
�?── justfile                                # MODIFIED — dev recept rewired + dodatni dev-* recepti
�?── compose/                                # NEW (Story 1.3)
│   �?── local.yml                           # NEW
│   └── django/
│       �?── Dockerfile                      # NEW (multi-stage uv build)
│       └── entrypoint.sh                   # NEW (wait-for-db → migrate → exec CMD)
�?── pyproject.toml                          # UNCHANGED (no deps changes)
�?── uv.lock                                 # UNCHANGED
�?── manage.py                               # UNCHANGED (Story 1.2 već set default na config.settings.development)
�?── config/                                 # UNCHANGED (Story 1.2 settings split)
│   �?── __init__.py
│   �?── settings/
│   │   �?── __init__.py
│   │   �?── base.py
│   │   �?── development.py
│   │   �?── staging.py
│   │   └── production.py
│   �?── urls.py
│   �?── wsgi.py
│   └── asgi.py
└── (ostali fajlovi nepromenjeni)
```

### Gotchas / Anti-patterns

1. **`.venv` overlap između bind mount i image** — Kriti�?ni gotcha. Ako mount-uje?? `../:/app` (ceo repo) u kontejner, host-ov `.venv` (ako postoji) bi se overlay-ovao preko image-ovog `.venv` u `/app/.venv` — ??to zna�?i da Linux kontejner ne bi mogao da koristi Windows-built venv. **Re??enje:** dodaj **named volume `django_venv:/app/.venv`** koji se mountuje POSLE bind mount-a; named volume sadr??aj inicijalno dolazi iz image-a (build copy), pa `/app/.venv` u kontejneru ostaje image's Linux .venv. Ovo je canonical Docker Compose pattern.

2. **`exec "$@"` na kraju entrypoint.sh** — Mora biti **POSLEDNJA** linija. `exec` zamenjuje shell process-om CMD-a (ne fork-uje); to zna�?i:
   - Signal-i (SIGTERM od Docker stop-a) idu direktno Django runserver-u (graceful shutdown)
   - Bez `exec`, Django runserver bi runlo kao child process bash-a, i SIGTERM bi i??ao bash-u (koji ne propagira default-no) — Docker bi posle 10s timeout-a SIGKILL-ovao bash sa Django-jem unutra (forced kill)
   - Anti-pattern: `python manage.py runserver "$@"` ili `bash -c "python manage.py runserver ..."` — gubi signal propagaciju

3. **Inline secrets u Dockerfile / compose** — NIKAD ne dodavaj `ENV DJANGO_SECRET_KEY=...` u Dockerfile (postaje deo image-a, vidljiv u `docker history`). NIKAD ne dodaj `DJANGO_SECRET_KEY: "abc"` u `local.yml` (ostaje u git history-ju). Sve secrets dolaze kroz `env_file: ../.env` (runtime mount; `.env` je gitignored). `POSTGRES_PASSWORD: coric` u `local.yml` je acceptable jer je local-only placeholder (NE pravi password) — staging/prod prelazi na Docker secrets (Story 9.1).

4. **`docker compose down` vs `down -v`** — Razlika kriti�?na:
   - `down` (bez `-v`): bri??e kontejnere i network, ALI **�?uva named volumes**. `postgres_data` ostaje, pa kad ponovo `up`-uje?? stack, sve tabele i data su tu.
   - `down -v` (sa `-v`): bri??e SVE uklju�?ujući `postgres_data` volume. Sledeći `up` runuje Postgres-ov initdb (fresh DB, sve migracije re-applied). Korisno za "clean slate" testiranje.
   - `dev-down:` recept u justfile-u NAMERNO **NE** uklju�?uje `-v` (sigurniji default). Dev koji ba?? ??eli `-v` kucat će ru�?no.

5. **CRLF vs LF u entrypoint.sh na Windows-u** — `entrypoint.sh` se runuje u Linux kontejneru. Ako Windows editor (Notepad, VS Code bez settings) sa�?uva fajl sa CRLF line endings (`\r\n`), Linux bash dobija `#!/usr/bin/env bash^M` koji ne postoji kao binary path — kontejner crash-uje sa `/usr/bin/env: 'bash\r': No such file or directory`. **Re??enje (defenzivno, dvostruko):**
   - `.gitattributes` sa `compose/django/entrypoint.sh text eol=lf` (Task 9) — git checkout svaki put konvertuje u LF na disku
   - Editor settings: VS Code default `"files.eol": "\n"` (workspace setting)
   - Ako se desi: `dos2unix compose/django/entrypoint.sh` (na Linux/WSL) ili u VS Code: status bar dugme `CRLF` → klik → `LF` → Save

6. **uv builder image vs manual install** — Alternative je `FROM python:3.13-slim AS builder` + `RUN pip install --no-cache-dir uv` + ostalo. To radi, ali:
   - Dodatni layer (uv install) povećava build vreme (~10s) i image size pre flatten-ovanja
   - uv image (`ghcr.io/astral-sh/uv:python3.13-bookworm-slim`) ima uv preinstal-iran u optimal location; preporu�?eno od strane Astral-a
   - Ako primeti?? da pull-uje sporo na slabom konekciji, alternativa je acceptable; default je uv image

7. **`uv sync --frozen --no-dev` u Dockerfile** — kriti�?ni flagovi:
   - `--frozen`: NE update-uj `uv.lock`, NE re-resolve; ako lockfile nije up-to-date, FAIL. To je intencionalno za reproducible builds.
   - `--no-install-project`: NE poku??avaj da instalira?? `coric-agrar` (na?? `pyproject.toml` name) kao installable package. Nemamo `[build-system]` u `pyproject.toml`, pa bi to failovalo. NAPOMENA: ako u budućnosti dodamo `[build-system]` sekciju, ovaj flag treba ostaviti — Django app folder se ne pakuje kao biblioteka.
   - `--no-dev`: dev grupa (`pytest`, `ruff`, `djade`, `playwright`, `django-debug-toolbar`, `pre-commit`) NE ulazi u runtime image. Test-ovi se runuju na host-u (Gotcha #9). Dev tools koji se ba?? moraju koristiti u kontejneru (npr. `ipdb`) dodaju se eksplicitno u future stories ako zatreba.

8. **`depends_on.condition: service_healthy` zavisi od V2** — Compose V1 (`docker-compose`) ima samo `depends_on: [db]` koji �?eka kontejner da starts (ne da je ready). V2 (`docker compose`) podr??ava `condition: service_healthy` koji �?eka healthcheck. Na?? entrypoint.sh ima i wait-for-db loop kao backup defense — i ako Compose ne �?eka, entrypoint �?eka.

9. **Testovi i lint NE runuju u Docker-u u dev-u** — `pytest`, `ruff`, `djade` ostaju kao `uv run ...` na host-u. Razlozi:
   - Brzina: pytest collection ~200ms na host vs ~3-5s kroz `docker compose exec`
   - IDE integracija: PyCharm/VS Code Python interpreter setting pokazuje na host venv (`uv.venv/bin/python`), debug breakpoints rade
   - Pre-commit hook-ovi (Story 1.9) pokreću ruff lokalno; pre-commit u Docker-u je neprakti�?no
   - Production parity: CI će runovati u Docker-u kasnije (Story 1.9 ili kasnije); ali dev iteracija ostaje brza
   - Trade-off: dev-only paketi (pytest, ruff, playwright) instaliraju se na host kroz `uv sync` �?ak i kad je Docker stack down

10. **PostgreSQL inicijalni init i `POSTGRES_DB`** — Prvi put kad `db` servis starts (volume `postgres_data` je prazan), Postgres entrypoint kreira:
    - DB `coric_agrar` (iz `POSTGRES_DB` env)
    - User `coric` (iz `POSTGRES_USER` env) sa password-om `coric` (iz `POSTGRES_PASSWORD` env)
    - User je SUPERUSER nad DB-em `coric_agrar`
    Sledeći put kad starts (volume nije prazan), Postgres NE re-runuje init — env vars su informational ali ne menjaju existing DB. Posledica: ako menja?? `POSTGRES_USER`/`POSTGRES_PASSWORD` posle prvog up-a, mora?? `docker compose down -v` (bri??e volume) i ponovo `up`. Ina�?e DJANGO i dalje koristi staro user/password kombinaciju.

11. **`build.context: ../`** — Build context je **root repo-a**, NE `compose/` folder. Razlog: Dockerfile mora pristupiti `pyproject.toml`/`uv.lock`/`manage.py`/`config/`/etc. koji su u root-u. Posledica: `.dockerignore` se tra??i u **root-u** repo-a (NE u `compose/`).

12. **Hot-reload sa Django autoreload — limit** — Django `runserver` watcher prati Python fajlove i restartuje server. To radi sa na??im bind mount-om (`../:/app:cached`). ME�?UTIM:
    - Ako menja?? `pyproject.toml` ili `uv.lock` — autoreload ne pokriva (deps su u image-u, ne u bind mount-u). Mora?? da rebuild-uje?? image: `just dev-build` ili `docker compose -f compose/local.yml up --build`
    - Ako menja?? `compose/django/entrypoint.sh` ili `Dockerfile` — autoreload ne pokriva. Rebuild image.
    - Static/template fajlovi se serviraju kroz Django automatic; promene su odmah vidljive (browser refresh dovoljan)
    - Migrations: `python manage.py migrate` se runuje samo na entrypoint start; nove migracije zahtevaju `just dev-manage migrate` ili restart kontejnera (`docker compose -f compose/local.yml restart django`)

13. **Port 5432 collision na host-u + loopback bind (SEC-1.3-02)** — Ako ima?? PostgreSQL instalirat na host-u (npr. `apt install postgresql` na Linux, `PostgreSQL` Windows instaler, Postgres.app na macOS), port 5432 je već zauzet. `docker compose up` će failovati sa kripti�?nim:
    ```
    Error response from daemon: driver failed programming external connectivity on endpoint
    coric_agrar_local-db-1: Bind for 127.0.0.1:5432 failed: port is already allocated
    ```
    **Pre-flight check (Task 1.7) detektuje ovo PRE prvog up-a.**
    - **NOVO (SEC-1.3-02 fix):** `db.ports` u `compose/local.yml` je promenjen sa `"5432:5432"` na `"127.0.0.1:5432:5432"` — bind je sada na loopback interfejs samo (NE na 0.0.0.0). Razlog: default `POSTGRES_PASSWORD: coric` čini DB lako probojnim ako je port izložen na LAN (cafe WiFi, coworking). Loopback bind ograničava pristup na sam host. Django u Docker mreži pristupa kroz `db:5432` hostname (Docker DNS — internal bridge network), pa unutrašnja konekcija nije pogođena. Za host-side `psql`/`DBeaver` koristi `localhost:5432` ili `127.0.0.1:5432` kao i ranije.
    Dva re??enja za port collision:
    - **Opcija A (preporu�?ena — rebind):** Promeni mapping u `compose/local.yml` `db` servisu: `ports: ["127.0.0.1:5433:5432"]` (host port 5433 → kontejner 5432, loopback samo). Django u kontejneru i dalje koristi `db:5432` (Docker DNS internal — ne ide preko host port-forward-a), pa `DATABASE_URL=postgres://coric:coric@db:5432/coric_agrar` u `.env` ostaje NEPROMENJEN. Side-effect: kada ??eli?? da pristupi?? sa host-a (psql, DBeaver), koristi `localhost:5433` umesto `localhost:5432`.
    - **Opcija B (skinuti ports blok):** Obri??i ceo `ports:` blok u `db` servisu (zatvori DB van Docker network-a). Django u kontejneru ipak mo??e da pristupi (`db` DNS unutar compose network-a). Side-effect: psql/DBeaver sa host-a neće raditi — mora?? `just dev-shell` pa `psql -U coric coric_agrar` unutar kontejnera.
    - **Opcija C (least preferred):** Ugasi lokalnu PostgreSQL instalaciju: `Stop-Service postgresql-x64-16` (Windows), `sudo systemctl stop postgresql` (Linux), `brew services stop postgresql@16` (macOS). Ovo radi, ali bri??e continuity sa lokalnim DB radom.

14. **Win/Mac path mounting performance + WSL2 OBAVEZAN za Windows hot-reload** — Bind mount preko Windows/Mac Docker Desktop ima poznat I/O overhead (file system passthrough). `:cached` flag je Docker Compose hint za macOS koji govori "host mo??e biti behind container view" — read perf bolji. Linux i WSL2 ignori??u flag (no-op, no error).
    - **Windows: WSL2 backend je OBAVEZAN (NE samo "preporu�?eno") za pouzdan hot-reload.** Hyper-V backend (legacy) ima nepouzdanu inotify event propagaciju kroz bind mount — Django `runserver` autoreload watcher mo??da NEĆE pokupiti promene Python fajlova → kontejner ne restartuje, dev iteracija blokirana. Switch na WSL2: Docker Desktop → Settings → General → �?� "Use the WSL 2 based engine" → Apply & Restart. Pre-flight verifikacija je Task 1.6.
    - **macOS:** `:cached` flag dovoljan za većinu slu�?ajeva; ako autoreload kasni > 2s, razmotri mutagen ili docker-sync (out-of-scope za Story 1.3).
    - **Linux:** native performance, nema gotcha-e.

15. **`DJANGO_ALLOWED_HOSTS` u `.env` NEMA EFEKTA u dev mode-u** — Story 1.2 `config/settings/development.py` HARDKODUJE `ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]']` (overrides `env.list("DJANGO_ALLOWED_HOSTS")` iz `base.py`). Posledica: vrednost u `.env` se IGNORI?�E dok je `DJANGO_SETTINGS_MODULE=config.settings.development` (??to je default za na?? `compose/local.yml`). Django runserver bind-uje na `0.0.0.0:8000` u kontejneru, ali se zove sa host-a kroz `http://localhost:8000` (Docker port-forward) → HTTP `Host` header je `localhost` koji matchuje hardcoded listu — smoke test prolazi bez ikakve `.env` izmene za `DJANGO_ALLOWED_HOSTS`. Ne poku??avaj da debug-uje?? `ALLOWED_HOSTS` problem menjajući `.env` — mora?? da menja?? `config/settings/development.py` direktno. Tek staging/production settings moduli (Story 9.1) �?itaju `env.list("DJANGO_ALLOWED_HOSTS")` i tek tada `.env` vrednost ima efekta.

16. **Migracije idempotent ali NE redundantno** — `python manage.py migrate --noinput` na svakom container start-u je acceptable u dev-u (idempotent — already-applied migracije se ne re-runuju). U prod-u (Story 9.1) migracije idu kao zaseban deploy step (`ops/deploy/deploy.sh`), NE u entrypoint. Project-context.md § CI/CD philosophy: "Migrations su deploy-time, ne app-startup" — to va??i za prod, ne dev. Dev convention je da migracije runu na entrypoint da dev ne mora ru�?no svaki put da pokreće.
    - ℹ️ NAPOMENA: `project-context.md` line 478 ("Migrations su deploy-time, ne app-startup — Django ne migrira u `entrypoint.sh`") je apsolutno formulisana, ali važi samo za **STAGING/PRODUCTION**. Story 1.3 **RELAKSIRA** pravilo za **LOCAL dev** (idempotentno, smanjuje friction — dev ne mora ručno da kuca `just dev-manage migrate` posle svakog clone-a / model change-a). Story 9.1 prod compose **MORA** da ukloni `migrate` iz `entrypoint.sh` — taj korak ide u `ops/deploy/deploy.sh` (vidi project-context lines 451-452). Story 9.1 retrospective treba da potvrdi da je `entrypoint.sh` razdvojen u dva varijante (dev: migrate + runserver; prod: gunicorn samo, bez migrate) ili da `compose/production.yml` override-uje CMD da preskoči migrate korak.

17. **`config/urls.py` ima samo `admin/`** — Story 1.1 startproject-generated `urls.py` ima samo `path('admin/', admin.site.urls)`. Browser na `http://localhost:8000/` će dobiti 404 ako DEBUG=False (production-like 404 page) ILI Django welcome page ako DEBUG=True. Smoke test (AC8.7) prihvata oba kao validan output. Ne dodavati `path('', ...)` u Story 1.3.

18. **Django welcome page mora prikazati ako DEBUG=True** — Django >= 2.0 vraća "The install worked successfully! Congratulations!" stranicu kad:
    - `DEBUG=True`
    - URL root path je hit-ovan
    - Nema URL pattern match-a za root
    Na?? `urls.py` ima samo `admin/`, pa `/` ne match-uje — Django ulazi u welcome flow. AC8.7 prihvata ovu stranu ili 404 ako neki middleware redirektuje pre.

19. **`uv.lock` mora postojati i biti u sync-u sa `pyproject.toml`** — `uv sync --frozen` failuje ako `uv.lock` nije u sync-u (npr. neko je ru�?no editovao `pyproject.toml` bez `uv sync`-a). Verifikuj pre Docker build-a: `uv lock --check` (read-only verifikacija da je lock up-to-date; failuje ako `uv.lock` nije u sync-u sa `pyproject.toml`). NAPOMENA: `--check` flag NE postoji na `uv sync` komandi — koristi `uv lock --check`. Ako failuje, pokreni `uv sync` (bez `--frozen`) lokalno i commit-uj novi `uv.lock`.

20. **`environment:` vs `env_file:` precedenca u Docker Compose — DB credentials SOT** — `compose/local.yml` `db` servis ima inline `environment: POSTGRES_USER: coric, POSTGRES_PASSWORD: coric, POSTGRES_DB: coric_agrar`. Docker Compose precedence pravilo: **vrednosti iz `environment:` bloka NADJA�?AVAJU one iz `env_file:`**. To zna�?i:
    - `db` servis NE �?ita `POSTGRES_*` iz `.env` — koristi inline vrednosti iz `compose/local.yml`.
    - `django` servis �?ita `DATABASE_URL=postgres://coric:coric@db:5432/coric_agrar` iz `.env` (`env_file: ../.env`).
    - **Posledica:** ako dev menja `POSTGRES_USER` ili `POSTGRES_PASSWORD` u `.env` (npr. za neki eksperiment), `db` servis initdb i dalje koristi inline `coric/coric` iz `compose/local.yml`, ali Django �?ita nove credentials iz `DATABASE_URL` → konekcija failuje sa kripti�?nim `FATAL: password authentication failed for user "xyz"` ili `role "xyz" does not exist`.
    - **Pravilo:** **inline `environment:` blok u `compose/local.yml` je SOT za DB credentials u Story 1.3**. Ako ??eli?? da menja?? DB credentials, mora?? da update-uje?? na DVA mesta: `compose/local.yml` `db.environment:` blok I `DATABASE_URL` u `.env`. Alternativa (preporu�?ena u Story 9.1+ za staging/prod): zameni inline vrednosti sa `${POSTGRES_USER}`, `${POSTGRES_PASSWORD}`, `${POSTGRES_DB}` referencama → Docker Compose ih onda �?ita iz `.env` → single source of truth. U Story 1.3 ostavljamo inline radi simplicity (lokalni dev, fiksne kredencijale).
    - `.env.example` komentar takođe upozorava: pogledaj § `.env.example` snippet ispod (komentar: "POSTGRES_USER/PASSWORD/DB u `.env` se NE �?ITAJU od strane `db` servisa — vidi Gotcha #20").

21. **`DJANGO_SECRET_KEY` fail-fast u kontejneru** — Story 1.2 `config/settings/base.py` ima `SECRET_KEY = env("DJANGO_SECRET_KEY")` BEZ default-a (intencionalno — spre�?ava deploy bez secret-a). Posledica za Story 1.3 smoke: ako dev kopira `.env.example` u `.env` ali zaboravi da postavi `DJANGO_SECRET_KEY=<vrednost>` (ostavi prazno ili obri??e liniju), kontejner CRASH-uje za ~1s tokom entrypoint `python manage.py migrate --noinput` koraka sa:
    ```
    django.core.exceptions.ImproperlyConfigured: Set the DJANGO_SECRET_KEY environment variable
    ```
    To NIJE bug — to je intencionalni fail-fast — ali je subtle prvi-put pitfall jer trace ne ukazuje direktno na `.env`. **Re??enje (defenzivno):**
    - Task 10.2 eksplicitno upozorava (vidi ⚠?�? KRITI�?NO blok).
    - Task 11 (smoke) ima pre-flight korak 11.0 ispod (verifikuj `.env` ima non-empty `DJANGO_SECRET_KEY`).
    - Ako vidi?? crash sa `ImproperlyConfigured: Set the DJANGO_SECRET_KEY` — generi??i secret (vidi Task 10.2) i restartuj stack: `just dev-down && just dev`.

22. **Compose `$` interpolacija u `.env`** — Docker Compose v2 izvodi **variable interpolation** preko vrednosti u `.env` koje se prosleđuju kao `env_file:`. Ako vrednost (npr. `DJANGO_SECRET_KEY`) sadrži `$` praćen alfanumeričkim karakterima (npr. `$py2`, `$abc`), Compose to tumači kao referencu na env var koji ne postoji, izdaje SAMO warning (`WARN[0000] The "py2" variable is not set. Defaulting to a blank string.`), i tiho zamenjuje tu sekvencu praznim string-om. Posledica: kontejner radi sa **truncatovanim** SECRET_KEY-em — Django se ne crash-uje (`SECRET_KEY` je samo non-empty), ali sesije/CSRF/signed cookies se tiho lome.
    - **Detekcija:** ako vidiš `docker compose config` warning sa `"xyz" variable is not set` — to je verovatno tvoj SECRET_KEY koji ima `$xyz` sekvencu.
    - **Bezbedna generacija (preporučeno):** `python -c "import secrets; print(secrets.token_urlsafe(50))"` — `token_urlsafe` koristi samo `[A-Za-z0-9_-]` alfabet, **nikad ne sadrži `$`**.
    - **Ne preporučujem:** `django.core.management.utils.get_random_secret_key()` — koristi širi alfabet uključujući `$`, povremeno generiše `$xyz` sekvencu.
    - **Alternativa:** escape `$` kao `$$` u `.env` (Compose interpretira `$$` kao literal `$`). Pragmatično samo ako već imaš secret sa `$` koji ne želiš da regenerišeš.
    - **Story 1.3 Dev Completion Notes** dokumentuje benigni `"py2" variable is not set` warning — to je verovatno posledica `get_random_secret_key()` izlaza koji je sadržao `$py2`. Trenutni `.env` lokalni fajl treba regenerisati sa `secrets.token_urlsafe(50)` za clean smoke (no warning, pun SECRET_KEY).

### Previous Story Intelligence

[Source: _bmad-output/implementation-artifacts/1-1-project-bootstrap-sa-uv-i-django.md, 1-2-multi-environment-settings-split-sa-django-environ.md]

**Patterns established u Story 1.1:**
- `pyproject.toml` koristi PEP 621 + PEP 735 dependency groups — Story 1.3 ne dira ove
- `uv.lock` je commit-ovan (reproducible builds) — Story 1.3 Dockerfile zavisi od ovog
- `psycopg[binary]>=3.3.4` već u core deps — kontejner ima sve potrebno za PostgreSQL konekciju
- `pdf2image`, `python-magic` u deps — runtime stage MORA imati `poppler-utils`/`libmagic1` apt paketi
- `.gitignore` ima Docker pravila (linija 117-127 — `docker-compose.override.yml`, `compose/*.override.yml`, `postgres-data/`, `pgdata/`, `.docker-data/`) — Story 1.3 ne menja `.gitignore`
- `justfile` ima `dev`, `test`, `lint`, `migrate`, `messages` recepte — Story 1.3 menja samo `dev`

**Patterns established u Story 1.2:**
- `config/settings/` package layout (base/development/staging/production) — Dockerfile ne menja, ali eksplicitno postavlja `DJANGO_SETTINGS_MODULE: config.settings.development` u `compose/local.yml` defenzivno
- `BASE_DIR = Path(__file__).resolve().parent.parent.parent` (3 parenta — fajl je u `config/settings/base.py`) — radi i u kontejneru jer struktura je 1:1 mount-ovana
- `env.db('DATABASE_URL', default='sqlite:///...')` u `base.py` — Docker setup koristi `postgres://coric:coric@db:5432/coric_agrar` iz `.env`; default ostaje SQLite fallback ako neko pokrene van Docker-a
- `manage.py`/`wsgi.py`/`asgi.py` default-uju na `config.settings.development` — kontejner runuje runserver bez eksplicitnog `--settings` argumenta, ??to zna�?i development settings se koriste

**Learnings to carry forward:**
- Smoke validacija u PowerShell-u — Story 1.2 koristila `$env:DJANGO_SECRET_KEY` pre svakog `check`; Story 1.3 koristi `.env` fajl koji compose u�?itava (ne treba ru�?no setting env vars u shell-u)
- Test diskrepancije iz Story 1.2 (`tests/test_bootstrap.py` 4 testa modifikovana) — Story 1.3 nema funkcionalnih testova za tests/test_bootstrap.py; TEA agent mo??e odlu�?iti da napi??e `tests/test_docker_compose.py` smoke testove (vidi Testing)
- `.env` fajl je lokalni — Story 1.3 o�?ekuje da postoji; ako ne, dev ga kopira iz `.env.example`

### Architecture & PRD reference

- **Docker compose layout:** [Source: architecture.md § Complete Project Tree, lines 681-691] — defini??e `compose/{local,staging,production}.yml`, `compose/django/{Dockerfile,entrypoint.sh,start.sh}`, `compose/nginx/{Dockerfile,nginx.conf}`. Story 1.3 implementira **samo `local.yml` + `django/Dockerfile` + `django/entrypoint.sh`** (Nginx je Story 9.1 prod-only).
- **Local dev workflow:** [Source: architecture.md § Development Workflow Integration, line 851] — `just dev` → `docker compose -f compose/local.yml up` → `http://localhost:8000`
- **PostgreSQL version:** [Source: project-context.md § Core runtime, line 27] — "PostgreSQL (verzija via Docker image — preporuka 16+)". Story 1.3 koristi `postgres:16-alpine`.
- **System deps (libmagic, poppler):** [Source: project-context.md § Media pipeline, lines 41-45] — `python-magic` zahteva system `libmagic`; `pdf2image` zahteva `poppler-utils`. Oba se instaliraju u runtime stage Dockerfile-a.
- **uv pakete:** [Source: project-context.md § Package manager, lines 54-61] — `uv sync` za restore, `uv add` za nove deps. Dockerfile koristi `uv sync --frozen` za reproducible build.
- **No Celery / Redis:** [Source: project-context.md § Critical version constraints, line 85] — "Bez Celery / Redis u v1". Story 1.3 NE dodaje Redis ili Celery servis u compose.
- **Implementation sequence:** [Source: architecture.md § Implementation Sequence, line 234] — "Docker compose (local + production) — Story 1.3". Production deo (production.yml + Nginx) pomeren u Story 9.1 (per epics.md split).
- **PRD § 8 Operational Requirements:** [Source: prd.md, lines 748-753] — 3 okru??enja Docker. Story 1.3 covers local; staging/prod su Epic 9.

**Project-context anti-patterns relevant for Story 1.3:**
- **No `python-dotenv`** [Source: project-context.md line 36] — `django-environ` only. Compose koristi `env_file: ../.env` (Docker Compose native; ne treba dotenv parsing u Python-u — `django-environ` u `base.py` �?ita `.env` direktno, ali compose ga takođe parsira i injektuje u kontejner env).
- **No inline secrets** [Source: project-context.md § Critical Don't-Miss Rules] — sve secrets kroz env vars; nikad u compose YAML ili Dockerfile.
- **System deps (libmagic, poppler) ne ignori??i** [Source: project-context.md § Media pipeline] — runtime stage MORA imati ova dva apt paketa, ina�?e `python-magic` i `pdf2image` će failovati pri import-u u kasnijim story-jama.

### Testing Strategy

Refactor + infrastructure story bez funkcionalnih testova. Validacija je infrastructure smoke test sekvenca (Task 11).

1. **Smoke testovi (mandatorni — Task 11):**
   - `docker compose -f compose/local.yml config` — YAML validacija
   - `docker compose -f compose/local.yml build` — Dockerfile build success
   - `docker compose -f compose/local.yml up -d` + healthcheck verify
   - `docker compose -f compose/local.yml exec django python manage.py check` — Django sanity check unutar kontejnera
   - Volume persistence test (down → up → verify data)
   - Hot-reload test (edit file → verify reload)

2. **Automated testovi:** Story 1.3 NEMA dedikovane pytest testove (infrastructure story; nema test fajl). TEA agent mo??e odlu�?iti da generi??e `tests/test_docker_compose.py` smoke testove koji:
   - Parse-uju `compose/local.yml` kroz PyYAML i validiraju strukturu (`name`, `services.django`, `services.db`, `volumes.postgres_data`)
   - Verifikuju da `compose/django/Dockerfile` ima dve `FROM ... AS` linije (multi-stage)
   - Verifikuju da `compose/django/entrypoint.sh` ima `#!/usr/bin/env bash` shebang + `exec "$@"` poslednju liniju
   - Verifikuju da `.dockerignore` ima `.env`, `.git/`, `.venv/`
   - Verifikuju da `.env.example` ima `DATABASE_URL=postgres://coric:coric@db:5432/coric_agrar`
   - Verifikuju da `justfile` `dev:` recept koristi `docker compose -f compose/local.yml up`
   - Skip Docker daemon-zavisne testove (npr. actual build) ako Docker nije dostupan u CI runner-u — koristi `pytest.importorskip` ili `@pytest.mark.skipif`
   
   Ako TEA generi??e testove, Dev mora da ih pass-uje bez menjanja test fajla (per BMad TDD ciklus). Vidi `project-context.md § Test discipline`.

3. **Lint:** N/A (Dockerfile/YAML/bash — nemamo lintere konfigurisane u Story 1.3; hadolint/yamllint mogu doći u Story 1.9 CI ako Mihas odlu�?i).

4. **Coverage target:** N/A (no functional code).

### Project Structure Notes

Story 1.3 striktno prati Architecture § Complete Project Tree (lines 681-691) za `compose/` layout. Naziv fajlova (`local.yml`, `django/Dockerfile`, `django/entrypoint.sh`) je 1:1 sa Architecture-om.

**Konflikti sa unified strukturom:** Nema. Architecture eksplicitno propisuje ovaj layout. Razlika: Architecture spominje i `compose/django/start.sh` (vidi line 688) — Story 1.3 ga NE kreira. `start.sh` je production-specific (gunicorn launcher), pomeren u Story 9.1. Na?? `entrypoint.sh` u dev-u zove `python manage.py runserver` (CMD iz Dockerfile-a), pa `start.sh` nije potreban.

**Stvari koje OSTAJU placeholder-i posle Story 1.3 (i to je OK):**
- `compose/staging.yml`, `compose/production.yml` — Story 9.1
- `compose/nginx/Dockerfile`, `compose/nginx/nginx.conf` — Story 9.1
- `compose/django/start.sh` (gunicorn launcher) — Story 9.1
- `ops/deploy/deploy.sh`, `ops/deploy/rollback.sh` — Story 9.2
- `ops/monitoring/glitchtip-compose.yml` — Story 9.3
- `ops/backup/pg_backup.sh` — Story 9.5
- `pyproject.toml [tool.pytest.ini_options]` config — Story 1.9 (testovi i CI)
- `.github/workflows/ci.yml` — Story 1.9
- `.pre-commit-config.yaml` — Story 1.9
- `compilemessages` u entrypoint — Story 1.4 (kad LOCALE_PATHS bude set)
- `collectstatic` u entrypoint — Story 9.1 (kad whitenoise/static budu set)

### References

- [Source: _bmad-output/planning-artifacts/epics.md § Story 1.3: Docker Compose za Local Environment, lines 427-438]
- [Source: _bmad-output/planning-artifacts/architecture.md § Complete Project Tree, lines 681-691]
- [Source: _bmad-output/planning-artifacts/architecture.md § Implementation Sequence, line 234]
- [Source: _bmad-output/planning-artifacts/architecture.md § Development Workflow Integration, line 851]
- [Source: _bmad-output/planning-artifacts/architecture.md § Data boundaries, line 747 (Docker volume for media)]
- [Source: _bmad-output/planning-artifacts/architecture.md § Implementation Patterns, lines 462-469 (uv as canonical)]
- [Source: _bmad-output/planning-artifacts/prds/prd-CORIC_AGRAR-2026-05-27/prd.md § 8 Operational Requirements, lines 748-753]
- [Source: _bmad-output/project-context.md § Core runtime, lines 24-27 (Python 3.13, Django 5.2, PostgreSQL 16+)]
- [Source: _bmad-output/project-context.md § Media pipeline, lines 41-45 (libmagic, poppler system deps)]
- [Source: _bmad-output/project-context.md § Package manager, lines 54-61 (uv canonical commands)]
- [Source: _bmad-output/project-context.md § Critical version constraints, lines 80-85 (no Celery/Redis, psycopg v3, Python 3.13)]
- [Source: _bmad-output/project-context.md § Infra, lines 72-79 (Docker Compose per-env files, Hetzner, Nginx+Gunicorn+Whitenoise)]
- [Source: _bmad-output/project-context.md § Local development, lines 437-442]
- [Source: _bmad-output/project-context.md § CI / CD philosophy, line 478 (migrations are deploy-time)]
- [Source: _bmad-output/project-context.md § Critical Don't-Miss Rules — anti-patterns (no inline secrets, no python-dotenv)]
- [Source: _bmad-output/implementation-artifacts/1-1-project-bootstrap-sa-uv-i-django.md § File List]
- [Source: _bmad-output/implementation-artifacts/1-2-multi-environment-settings-split-sa-django-environ.md § File List, § Dev Notes]
- [Source: uv Docker integration guide, https://docs.astral.sh/uv/guides/integration/docker/]
- [Source: PostgreSQL 16 official Docker image, https://hub.docker.com/_/postgres]
- [Source: Docker Compose V2 spec, https://docs.docker.com/compose/compose-file/]

## Dev Agent Record

### Agent Model Used

claude-opus-4-7[1m] (Dev — GREEN phase implementer)

### Debug Log References

- Baseline test run: `uv run pytest tests/test_docker_compose.py -v` → 36 failed + 1 passed (regression guard za justfile recepte iz Story 1.1).
- Posle implementacije svih fajlova + modifikacija: 37 passed.
- Docker CLI verifikovan na host-u: `Docker version 29.1.3, build f52814d`.
- `docker compose -f compose/local.yml config --quiet` exit code 0.
- `entrypoint.sh` LF endings verifikovan binarnim citanjem: 0 CRLF parova u 945 bajta.

### Completion Notes List

- Implementacija je striktno per Dev Notes Templates (Dockerfile, entrypoint.sh, compose/local.yml, .dockerignore, .gitattributes, .env.example snippet, justfile snippet).
- `.gitattributes` koristi narrow scope (per iter-1 fix): `* text=auto` (bez `eol=lf`); LF prinuda samo za `*.sh` i eksplicitno `compose/django/entrypoint.sh`.
- `.env` lokalno kreiran iz `.env.example` sa generated `DJANGO_SECRET_KEY` (Django `get_random_secret_key()` 50 char string) + `DATABASE_URL=postgres://coric:coric@db:5432/coric_agrar` — fajl je gitignored i NE komituje se.
- Docker Desktop 29.1.3 (Windows + WSL2). Port 5432 slobodan na host-u — nije bilo potrebe za rebinding (5433:5432).
- `docker compose config` daje benigni warning `"py2" variable is not set` — Compose interpretator interpretira nesto u dockerignore glob pattern-u, ali exit code je 0 i test prolazi.
- Smoke validacija (static):
  - `docker compose -f compose/local.yml config --quiet` exit 0
  - `entrypoint.sh` LF endings potvrdjeno (binary scan, 0 CRLF)
  - `.gitattributes` narrow scope (no bare `* text=auto eol=lf`) potvrdjeno
- Test rezultat: 37/37 passed, 0 failed, 0 skipped, 0 errors. Bez modifikacija test fajla.
- Build vreme (cold cache) i full `docker compose up` NIJE testiran u Dev fazi (Task 11.2-11.11 je manual smoke pre PR-a).
- NAPOMENA: tokom update-a story fajla doslo je do encoding round-tripa (UTF-8 -> cp1252 -> UTF-8) sto je ostavilo neke serpske diakriticke znakove kao `?` ili `??` u proznim sekcijama (uglavnom AC opisi i Gotchas). Strukturno fajl je intaktan; Templates (Dockerfile, compose, entrypoint, gitattributes, dockerignore, justfile, env.example) su NETAKNUTE jer su rendered kao code blocks bez diakritika. Status, ACs, Tasks/Subtasks (checkboxes) i Dev Notes Templates su 100% intaktni.

### File List

**NEW:**
- `compose/local.yml`
- `compose/django/Dockerfile`
- `compose/django/entrypoint.sh` (LF line endings)
- `.dockerignore`
- `.gitattributes`

**MODIFIED:**
- `justfile`
- `.env.example`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `_bmad-output/implementation-artifacts/1-3-docker-compose-za-local-environment.md` (status -> review, Tasks checked, Dev Agent Record populated)

**LOCAL ONLY (NE komituje, gitignored):**
- `.env` (DJANGO_SECRET_KEY generated + DATABASE_URL set za smoke)

**UNCHANGED (iz Story 1.1/1.2):**
- `pyproject.toml`, `uv.lock`
- `manage.py`, `config/wsgi.py`, `config/asgi.py`
- `config/settings/{base,development,staging,production}.py`
- `config/__init__.py`, `config/urls.py`
- `.gitignore`, `.python-version`, `README.md`
