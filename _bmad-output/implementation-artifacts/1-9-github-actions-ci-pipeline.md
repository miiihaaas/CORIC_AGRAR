---
story-id: "1.9"
story-key: 1-9-github-actions-ci-pipeline
title: GitHub Actions CI Pipeline
status: review
epic_num: 1
epic_title: Project Foundation & Visual Identity
module: cross-cutting (.github/workflows/ + .pre-commit-config.yaml + repository root — no Django app)
created: 2026-05-29
last_modified: 2026-05-29
author: Mihas (SM autonomous)
---

# Story 1.9: GitHub Actions CI Pipeline

Status: review

## Story

As a **solo dev (Mihas) koji svakog dana radi na Epic 1-9 sprint planu**,
I want **automatski CI build koji proverava `ruff` lint, `djade` template format i `pytest` test suite na svaki push / PR ka `master` (i kasnije ka `staging`/`main`) plus identičan pre-commit hook lokalno**,
so that **regression-i (sintaksa, format, template, test fail) NE dolaze u `master` branch, GHCR vendor cache je spreman za buduću `deploy.yml` story (Epic 9 9.1/9.2), i moj lokalni commit workflow je isti `ruff/djade/pytest` standard kao CI — bez "rush" `--no-verify` bypassa**.

Ova story je **prvi konzument `.github/workflows/`** u projektu — uvodi `ci.yml` kao authoritative CI gate (`ruff check`, `djade --check`, `pytest`) i postavlja temelj za `deploy.yml` koji stiže u Epic 9 (Story 9.2: "Hetzner deployment skript + SSL"). Ovo je takođe **prvi konzument `.pre-commit-config.yaml`** — uvodi lokalne pre-commit hooks za **lint paritet** sa CI lint job-om: `ruff` i `djade` su 1:1 sinhronizovani izmedju pre-commit i CI (ista verzija, isti flags), tako da fail lokalno = fail u CI. **`pytest` se NAMERNO ne pokreće u pre-commit-u** (Decision D11) jer pytest traje ~30-60s a pre-commit budget je <5s da ne ometa git commit UX; pytest gate je CI-only. Time je narrative consistent: pre-commit i CI imaju 1:1 LINT sync (ne 1:1 ceo CI flow sync).

**Foundation za:**
- **Story 9.1 (Production Docker compose + Nginx config):** CI workflow pattern reuse — `deploy.yml` će koristiti isti `actions/checkout@v4` + `uv` setup pattern.
- **Story 9.2 (Hetzner deployment script + SSL):** GHCR login pattern iz `ci.yml` direktno se preliva u `deploy.yml` (push image-a u `ghcr.io/<owner>/coric-agrar:<sha>` posle CI green).
- **Story 9.6 (Django logging konfiguracija):** CI mora moći da pokrene `pytest` bez log-noise-a.
- **Sve buduće stories (Epic 2-9):** svaki push aktivira gate; svaka story-ja koja dodaje novi Django app, model, view, template, ili JS modul mora prolaziti CI bez regression-a.

**Princip:** Jedan `ci.yml` workflow sa **TRI sekvencijalna job-a** (`lint`, `test`, `build`) — lint i test job-ovi NE zavise jedan od drugog (paraleli za brzinu), build job zavisi od oba (ne builduje image ako lint ili test pada). `pytest` se pokreće u **`uv` venv na runner-u** (NE u Docker container-u — Decision D1) jer je brže (cached `uv.lock` deps) i jer Story 1.9 ne ima production parity zahtev (production parity stiže u Epic 9 9.1). PR-ovi ka `master` (i `staging`/`main` u budućnosti) **MORAJU** imati green CI da bi se mergovali — branch protection rules pripreme su deo Definition of Done (manual GitHub UI step, dokumentovan u Dev Notes). GHCR je pripreman sa Docker buildx login step (`docker/login-action@v3`) ali **push image-a je DEFERRED do Story 9.2** — Story 1.9 samo verifikuje da `docker build` prolazi bez push-a (smoke test za buduću `deploy.yml`).

**Strukturna arhitektura:** Repository root level dobija dva nova fajla (`.pre-commit-config.yaml`, `.github/workflows/ci.yml`) plus jedan novi direktorijum (`.github/workflows/`). NEMA Django app promene. NEMA template / CSS / JS promene. NEMA pyproject.toml dep promene (sve potrebne dev deps su već u `dependency-groups.dev` per Story 1.1). justfile **MOŽE** dobiti opcioni `just precommit-install` recept kao convenience (vidi Task 4 — opcioni gold-plate, ne blocker).

## Acceptance Criteria

**AC1 — `.github/workflows/ci.yml` postoji i definiše tri job-a (`lint`, `test`, `build`) koji se pokreću na `push` ka `master` i `pull_request` ka `master`**

- **Given** projekat iz Story 1.1-1.8 (pyproject.toml ima `[dependency-groups.dev]` sa `ruff>=0.15.14`, `djade>=1.9.0`, `pytest>=9.0.3`, `pytest-django>=4.12.0`; `uv.lock` postoji; `templates/` direktorijum sadrži `base.html` + partials/; `tests/` direktorijum sadrži svih postojecih test fajlova — trenutno 8: `test_base_template`, `test_bootstrap`, `test_docker_compose`, `test_i18n_setup`, `test_navigation_chrome`, `test_settings_split`, `test_static_tokens`, `test_visual_components` — IMP-10)
- **When** kreiram `.github/workflows/ci.yml`
- **Then** sledeća struktura mora postojati:
  - Fajl `.github/workflows/ci.yml` u repository root-u.
  - YAML `name: CI` na vrhu.
  - `on:` trigger sekcija:
    - `push: branches: [master]` (current default branch per `git status` opener)
    - `pull_request: branches: [master]` (PR gate)
    - `workflow_dispatch:` (IMP-IT2-4 — omogućava manual run iz GitHub Actions UI; koristi se za pre-merge dry-run na throwaway feature branch i debugging). Vidi Decision D13.
    - Dev Notes dokumentuje da kad se `staging`/`main` branch-ovi pojave (Epic 9), oni se dodaju u trigger listu — Story 1.9 ne uvodi `staging`/`main` jer ti branch-ovi NE postoje u Epic 1.
  - `permissions:` block sa **workflow-level least-privilege** (IMP-1):
    - `contents: read` (za checkout — workflow-level, dovoljno za sva tri job-a)
    - **NEMA workflow-level `packages: write`** — to je preširoko (lint i test job-ovi ne diraju GHCR).
  - Tri job-a:
    - `lint` (runs-on: `ubuntu-latest`, `timeout-minutes: 10`)
    - `test` (runs-on: `ubuntu-latest`, `timeout-minutes: 10`)
    - `build` (runs-on: `ubuntu-latest`, `needs: [lint, test]`, `timeout-minutes: 15`)
      - **Job-level `permissions: packages: write`** — SAMO build job dobija GHCR write scope (deferred do Story 9.2 za push; Story 1.9 build job ne push-uje, ali permission je placeholder za Story 9.2). Ovo je least-privilege per IMP-1.
  - `timeout-minutes:` na svaki job (IMP-4): `lint: 10`, `test: 10`, `build: 15` — sprečava infinite hang scenarije (npr. Docker Hub rate limit retry, GHA cache fetch hang).
  - **`concurrency:` block na workflow-level** (IMP-3) — sprečava dva paralelna CI run-a za isti branch:
    ```yaml
    concurrency:
      group: ci-${{ github.ref }}
      cancel-in-progress: true
    ```
    Bez ovoga, dva push-a brzo za redom triggeruju dva paralelna CI run-a i troše GHA free minute.
  - **NAPOMENA (IMP-IT2-3 — concurrency race sa branch protection):** Edge case — ako Mihas push-uje hotfix dok prvi post-merge CI run traje, `cancel-in-progress: true` otkazuje prethodni run. Status "canceled" NIJE "success" za branch protection (per Task 5.6) — sledeci PR check moze pasti dok novi run ne završi. Acceptable trade-off: kratak prozor neusagasenosti vs duplikat CI minute. **Mitigation:** ne push-uj hotfix neposredno nakon Story 1.9 merge-a; sačekaj prvi CI run da prođe (~3 min). Vidi Gotcha CI-8.
- **And** `lint` i `test` job-ovi su nezavisni (paraleli su po default-u jer ne dele `needs:`).
- **And** ako bilo koji job pada, GitHub PR check status je `failed` — branch protection rules (manual setup dokumentovan u DoD) blokira merge.

**AC2 — `lint` job pokreće `ruff check .` i `djade --check templates/partials/*.html` kroz `uv run` sa cached `uv.lock` deps**

**Napomena (iter-1 + iter-2 audit):** base.html je privremeno izvan djade scope-a zbog konflikt Story 1.5/1.6/1.7 literal substring testova vs. djade 1.9.0 `{% load %}` consolidation. Vidi Decision D14 i Acceptable scope deviations § 'djade scope evolution path'. Konkretna komanda u `ci.yml` je `uv run djade --check templates/partials/*.html` (flat glob, Epic 1 scope).

- **Given** `ci.yml` `lint` job
- **When** GitHub Actions worker runner kreće `lint` job
- **Then** job mora imati sledeće step-ove:
  - **Step 1:** `actions/checkout@v4` (default depth — ne treba `fetch-depth: 0` jer lint ne čita git history).
  - **Step 2:** `astral-sh/setup-uv@v3` (official uv setup action; verzija pinned na v3 minor — Decision D2) sa:
    - `python-version: '3.13'` (eksplicitno; matchuje `pyproject.toml` `requires-python = ">=3.13"` — IMP-9)
    - `enable-cache: true` (cached `uv.lock` deps preko GitHub Actions cache — Decision D3)
    - `cache-dependency-glob: "uv.lock"` (cache invalidates kad se `uv.lock` promeni)
  - **Step 3:** `uv sync --frozen --group dev` (instalira sve dev deps; `--frozen` osigurava da `uv.lock` nije menjan u toku CI-ja; `--group dev` ekplicitno aktivira `[dependency-groups.dev]` — Decision D4 ražuje zašto ne `--all-groups`).
  - **Step 4:** `uv run ruff check .` (lint provera celog repo-a — exit code 0 = pass, non-zero = fail). **Polish-B:** `ruff check` koristi `pyproject.toml [tool.ruff]` konfiguraciju, uključujući `line-length=100` per project-context.md — CI ne overajduje config, samo izvršava.
  - **Step 5:** `uv run djade --check templates/partials/*.html` (template format check; `--check` mode = ne menja fajlove, samo prijavi diff — exit code 0 = pass, non-zero = fail). **Napomena (iter-2):** djade 1.9.0 NE prihvata directory arg (testirao Dev iter-1) — koristi se glob po fajlovima. `base.html` izuzet iz scope-a zbog konflikt sa Story 1.5/1.6/1.7 literal substring testovima (vidi Decision D14). Story 2.1+ proširuje scope per IMP-12 (`git ls-files '*.html' | xargs -r uv run djade --check`).
- **And** Step 3 (uv sync) koristi GitHub Actions cache key zasnovan na `uv.lock` hash-u (preko `cache-dependency-glob`) — ako se `uv.lock` ne menja između push-ova, deps se restauriraju iz cache-a (~5-10s umesto ~60-90s clean install).
- **And** lint job NE pokreće Python kod — samo statičku analizu. Bez Django ili PostgreSQL setup-a (lint ne treba DB).
- **And** **`lint` job MORA imati `env:` blok** sa `DJANGO_SECRET_KEY: ci-test-secret-key-not-for-prod-50chars-padding` (dummy vrednost — NE stvarni secret). Iako `djade>=1.9.0` standalone template parser NE poziva Django settings, postavljanje `DJANGO_SECRET_KEY` u lint job je 0-cost insurance — ako buduća verzija `djade` ili nov lint hook (npr. `django-template-validator`) ucita Django settings, izostanak ovog env-a bi uzrokovao `ImproperlyConfigured` exception pre nego lint moze da pokrene. Vidi Gotcha CI-1.
- **And** ako `ruff check` ili `djade --check` pada, job exit code je non-zero i CI status postaje `failed` (blokira merge u AC1).

**AC3 — `test` job pokreće `uv run pytest` u `uv` venv na runner-u (NE u Docker container-u), sa cached `uv.lock` deps, BEZ PostgreSQL servisa (v1 scope)**

- **Given** `ci.yml` `test` job
- **When** GitHub Actions worker runner kreće `test` job
- **Then** job mora imati sledeće step-ove:
  - **Step 1:** `actions/checkout@v4`
  - **Step 2:** `astral-sh/setup-uv@v3` sa istim cache config-om kao u AC2 (`python-version: '3.13'`, `enable-cache: true`, `cache-dependency-glob: "uv.lock"`).
  - **Step 3:** `uv sync --frozen --group dev` (isti pattern kao AC2; deduplicirano logički, ne fizički — GitHub Actions ne podržava "shared steps" preko reusable workflow-a u Story 1.9 v1 scope, vidi Decision D5).
  - **Step 4:** `uv run pytest` (pokreće test suite — `pyproject.toml` ima `[tool.pytest.ini_options]` sa `DJANGO_SETTINGS_MODULE = "config.settings.development"`, `testpaths = ["tests", "apps"]`).
- **And** **`test` job MORA imati `env:` blok** sa SAMO sledecom env varijablom:
  - `DJANGO_SECRET_KEY: ci-test-secret-key-not-for-prod-50chars-padding` (dummy vrednost, NE stvarni secret)
  - **NAPOMENA (IMP-IT2-1):** `manage.py check --deploy` step je UKLONJEN iz Story 1.9 v1 CI — vidi Decision D13 za rationale (settings.development namerno ima DEBUG=True; `continue-on-error: true` bi učinio step placebo; pravo mesto za `check --deploy` je Story 9.6 nakon prelaska na settings.production).
  - **NAPOMENA (CRIT-IT2-1):** `DATABASE_URL` env NIJE postavljen u test job-u — `config/settings/base.py:78` već default-uje DATABASES na `sqlite:///db.sqlite3` (vidi Gotcha CI-7). Postavljanje `DATABASE_URL=sqlite:///test.db` bi bilo redundantno i kreiralo NEW DB na non-default putanji što može maskirati pravo ponašanje. SQLite default iz `base.py` je dovoljan za v1 (Epic 1-8); PostgreSQL service container stiže u Epic 9 9.1.
  - **KRITICNO:** Bez `DJANGO_SECRET_KEY` env-a, `config/settings/base.py` zove `env("DJANGO_SECRET_KEY")` BEZ default-a; `pytest-django` ucitava settings PRE testova → `ImproperlyConfigured` exception → test job pada 100% na prvom run-u pre nego pytest moze i da collect-uje testove. Odsustvo ovog env-a je guaranteed failure. Vidi Gotcha CI-1.
- **And** **Decision D1 RESOLUTION — pytest se pokreće u `uv` venv na runner-u, NE u Docker container-u**. Rationale (vidi Dev Notes D1 sekciju za pun tradeoff analysis):
  - `uv` venv na runner-u je brže (~30-60s test run vs ~3-5min Docker build + run u istoj akciji).
  - Story 1.9 testovi su pure-Python + Django ORM (SQLite in-memory ili kroz Django test DB) — NIJE postoji PostgreSQL integration test u Story 1.1-1.8.
  - Production parity stiže u Epic 9 9.1 (Production Docker Compose + Nginx config), tada `deploy.yml` može opciono dodati Docker-based integration test job.
  - Story 1.9 NE uvodi PostgreSQL `services:` block (Docker compose servis u runner-u) jer postojeći Story 1.1-1.8 testovi NE zahtevaju live DB connection (vidi `tests/conftest.py` — ne koristi `@pytest.mark.django_db`).
- **And** ako neki test pada (`pytest` exit code != 0), job exit code je non-zero i CI status postaje `failed`.
- **And** test job runs paraleli sa lint job-om (oba zavise samo od checkout + uv setup + uv sync; nemaju `needs:` jedan od drugog).

**AC4 — `build` job uspeva da builduje Docker image kroz `docker/build-push-action@v6` BEZ push-a i BEZ GHCR login-a (smoke test); GHCR login + push su DEFERRED do Story 9.2**

- **Given** `ci.yml` `build` job sa `needs: [lint, test]` (pokreće se TEK pošto lint + test prođu green)
- **When** GitHub Actions worker runner kreće `build` job
- **Then** job mora imati sledeće step-ove (IMP-6 — GHCR login je deferred do Story 9.2):
  - **Step 1:** `actions/checkout@v4`
  - **Step 2:** `docker/setup-buildx-action@v3` (postavlja Docker Buildx za multi-stage build — kompatibilno sa `compose/django/Dockerfile` koji koristi `# syntax=docker/dockerfile:1.7` i dva stage-a `builder` + `runtime`).
  - **Step 3 (IMP-2):** `Set lowercase image name` — bash run step koji transformise `${{ github.repository }}` (moze biti mixed case, npr. `Miiihaaas/CORIC_AGRAR`) u lowercase (GHCR zahteva lowercase namespace):
    ```yaml
    - name: Set lowercase image name
      run: echo "IMAGE_NAME=$(echo '${{ github.repository }}' | tr '[:upper:]' '[:lower:]')" >> $GITHUB_ENV
    ```
  - **Step 4:** `docker/build-push-action@v6` sa:
    - `context: .`
    - `file: ./compose/django/Dockerfile`
    - `push: false` (KRITIČNO za v1 — Story 1.9 NE push-uje image; samo verifikuje da `docker build` prolazi; push stiže u Story 9.2 `deploy.yml`)
    - `tags: ghcr.io/${{ env.IMAGE_NAME }}:ci-${{ github.sha }}` (tag template spreman za Story 9.2 reuse; koristi lowercase `IMAGE_NAME` iz Step 3; tag se kreira lokalno na runner-u i baca posle job-a — bez push-a)
    - `cache-from: type=gha` (GitHub Actions buildx layer cache — sledeći build koristi cached layer-e ako se Dockerfile ili `uv.lock` ne menjaju)
    - `cache-to: type=gha,mode=max` (sve layer-e cache-uje)
- **And** **GHCR login step JE UKLONJEN iz Story 1.9 (IMP-6)** — Story 1.9 build job verifikuje SAMO da Dockerfile builduje bez sintaksne greske; NEMA `docker/login-action@v3`, NEMA push step. Razlog: login je premature kad nema push-a (login + immediately throwaway = wasted CI minute + skupost potencijalnih GHCR auth side-effect-a). Story 9.2 dobija task da doda GHCR login + push step kao deo `deploy.yml` ili produzene `ci.yml` build job-a.
- **And** ako Docker build pada (npr. `uv sync --frozen --no-install-project --no-dev` u stage 1 pada, ili `apt-get install` u stage 2 pada), job exit code je non-zero i CI status postaje `failed`.
- **And** `build` job služi kao **smoke test** za Story 9.2 `deploy.yml` — ako `compose/django/Dockerfile` builduje u CI, builduje i lokalno + u staging deploy-u; ako pada — early signal pre Story 9.2 work-a.

**AC5 — GHCR namespace + secrets management su dokumentovani u Dev Notes; LOGIN + PUSH su DEFERRED do Story 9.2 (Story 1.9 build job ne pravi auth handshake sa GHCR)**

- **Given** AC4 build job BEZ GHCR login step-a (IMP-6 — login deferred do Story 9.2)
- **When** workflow startuje
- **Then** sledeće mora biti tačno:
  - Story 1.9 build job ne pravi network call ka `ghcr.io` (NEMA `docker/login-action@v3`); tag se kreira lokalno u Docker daemon-u i baca posle job-a.
  - Job-level `permissions: packages: write` na build job-u (per AC1 IMP-1) je placeholder za Story 9.2 — kad Story 9.2 doda `docker/login-action@v3` + `push: true`, permission je vec spreman bez novog AC.
  - Dev Notes dokumentuje da kad Story 9.2 doda GHCR login, koristice `secrets.GITHUB_TOKEN` (default GHA token, NE custom PAT — Decision D6); pattern je isti kao većina production GHA workflow-a.
- **And** **Dev Notes sekcija "GHCR + Secrets Management" eksplicitno dokumentuje:**
  - GHCR koristi `ghcr.io/<github_owner>/<github_repo>:<tag>` namespace; **owner+repo MORAJU biti lowercase** (Gotcha CI-2 + IMP-2) — koristi se shell transformacija `tr '[:upper:]' '[:lower:]'` u build job Step 3 (per AC4).
  - Primer posle lowercase transformacije (Polish-C konzistentnost): `ghcr.io/<github_owner>/<github_repo>:ci-abc1234` (sve lowercase; konkretne vrednosti se runtime-resolve-uju kroz `${{ github.repository }}` GHA context; `abc1234` je git sha skraćen).
  - `secrets.GITHUB_TOKEN` se automatski generiše po job-u — ne treba manualnu konfiguraciju u GitHub UI. Token istekne na kraju job-a (sigurnije od long-lived PAT).
  - Branch protection rules za `master` (Task 5.6 DoD blocker per IMP-7) su dokumentovane kao DoD condition — Story 1.9 NIJE done bez branch protection setup-a.
- **And** GHCR setup je verifikovan ISKLJUCIVO kroz dokumentacioni handoff ka Story 9.2 — NEMA live login step u Story 1.9 (login + push handshake stiže u Story 9.2 sa pravim production scenarijem).

**AC6 — `.pre-commit-config.yaml` postoji u repository root-u i konfiguriše standardne pre-commit-hooks + `ruff` (lint + format) + `djade` (template format) hooks; `ruff` i `djade` su 1:1 sinhronizovani sa CI lint job-om (LINT-only sync, NE pytest sync)**

- **Given** projekat sa `pyproject.toml` `[dependency-groups.dev]` koji ima `ruff>=0.15.14`, `djade>=1.9.0`, `pre-commit>=4.6.0`
- **When** kreiram `.pre-commit-config.yaml`
- **Then** fajl mora postojati u repository root-u sa sledećom strukturom (Decision D7 — `repos` sa pre-commit hooks; IMP-5 dodaje standardne pre-commit-hooks na vrh liste):
  ```yaml
  # .pre-commit-config.yaml
  # Pokrece se lokalno na svaki commit (posle `pre-commit install` setup-a)
  # CI lint job (.github/workflows/ci.yml) pokrece iste lint komande — fail lokalno = fail u CI
  # NAPOMENA: pytest se NAMERNO ne pokreće u pre-commit-u (Decision D11) — pytest je CI-only gate

  repos:
    - repo: https://github.com/pre-commit/pre-commit-hooks
      rev: v4.6.0  # CRIT-4 (prosiren IMP-IT2-2): verify https://github.com/pre-commit/pre-commit-hooks/releases pre commit-a — koristi latest stable major ako je viši
      hooks:
        - id: trailing-whitespace
        - id: end-of-file-fixer
        - id: check-yaml
        - id: check-merge-conflict

    - repo: https://github.com/astral-sh/ruff-pre-commit
      rev: v0.15.14  # CRIT-4 (prosiren IMP-IT2-2): verify https://github.com/astral-sh/ruff-pre-commit/releases pre commit-a — koristi latest stable major ako je viši
      hooks:
        - id: ruff-check
          args: [--fix]
        - id: ruff-format

    - repo: https://github.com/adamchainz/djade-pre-commit
      rev: 1.9.0  # CRIT-4 (prosiren IMP-IT2-2): verify https://github.com/adamchainz/djade-pre-commit/releases pre commit-a — koristi latest stable major ako je viši
      hooks:
        - id: djade
          args: [--target-version, "5.2"]
  ```
- **And** **standardni pre-commit-hooks (IMP-5):** `trailing-whitespace`, `end-of-file-fixer`, `check-yaml`, `check-merge-conflict` su minimum baseline higijenski hooks za svaki repo — hvataju trivial issues (whitespace, missing newline EOF, invalid YAML, leftover merge markers `<<<<<<<`) pre nego se commit-uju.
- **And** **LINT-only sync semantika (KRITICNO — Decision D11):** "1:1 sinhronizacija" između pre-commit i CI odnosi se ISKLJUCIVO na lint hookove (`ruff`, `djade`) — NE na pytest. Razlog: pre-commit budget je <5s da ne ometa git commit UX; pytest run je 30-60s. CI test job je pravo mesto za pytest gate. Lokalno Mihas i dalje pokreće `uv run pytest` manualno pre push-a (preporučeno), ali pytest NIJE pre-commit hook.
- **And** **verzija pinning STRATEGIJA (KRITIČNO — Decision D8):** `ruff` verzija u `.pre-commit-config.yaml` (`v0.15.14`) i `djade` verzija (`1.9.0`) MORAJU matchovati MINIMUM verzije iz `pyproject.toml` `[dependency-groups.dev]`. Ako Mihas u budućnosti `uv add --dev ruff==0.16.0` u `pyproject.toml`, `.pre-commit-config.yaml` MORA biti ažuriran ručno (preko `pre-commit autoupdate` ili manual edit). Dev Notes dokumentuje ovaj sync-disciplinski problem + alternative ($-pinning vs floating).
- **And** **`djade` `--target-version` flag** koristi `"5.2"` (matchuje `pyproject.toml` `django>=5.2,<6.0` constraint).
- **And** **`ruff-check` hook ima `args: [--fix]`** — pre-commit hook automatski popravlja fixable issue-e (npr. import sortiranje, trailing whitespace); CI lint job ne koristi `--fix` (samo `--check`) jer CI ne sme da menja fajlove.
- **And** **`ruff-format` hook je separatan od `ruff-check`** — `ruff-format` je ekvivalent black-u; oba hooks moraju biti present jer `ruff check` ne format-uje sam po sebi.
- **And** **anti-pattern:** NEMA `--no-verify` instrukcija u Dev Notes ili bilo gde u Story 1.9. Mihas se obavezuje da NIKAD ne bypassuje pre-commit hook (per project-context.md § "🚫 Anti-pattern: Skipping pre-commit hooks").

**AC7 — Dev workflow dokumentacija: pre-commit hook install + CI debugging steps u Dev Notes**

- **Given** `.pre-commit-config.yaml` kreiran (AC6) i `pre-commit>=4.6.0` već u `pyproject.toml` (Story 1.1)
- **When** Dev (ili novi onboarding kolaborator) klonira repo
- **Then** Dev Notes sekcija "Lokalni pre-commit install workflow" mora dokumentovati sledeće korake:
  1. `uv sync --group dev` (instalira `pre-commit` u venv)
  2. `uv run pre-commit install` (postavlja `.git/hooks/pre-commit` hook script)
  3. (Opciono) `uv run pre-commit run --all-files` (jednokratan run preko svih fajlova da verifikuje setup; očekuje green)
  4. Posle ovoga, svaki `git commit` automatski pokreće `ruff-check --fix`, `ruff-format`, `djade --target-version 5.2` na staged fajlovima
- **And** Dev Notes sekcija "CI debugging steps" mora dokumentovati:
  - Ako CI lint pada lokalno reprodukciju: `uv run ruff check .` + `uv run djade --check templates/partials/*.html` (iter-2: scope match-uje stvarnu ci.yml komandu, ne ceo `templates/` dir)
  - Ako CI test pada lokalno reprodukciju: `uv run pytest -v --tb=short`
  - Ako CI build pada lokalno reprodukciju: `docker build -f compose/django/Dockerfile .`
- **And** **OPCIONI gold-plate (NIJE blocker — Task 4):** `justfile` MOŽE dobiti `precommit-install` recept:
  ```just
  # Setup pre-commit hooks (jednokratno posle klon-a)
  precommit-install:
      uv run pre-commit install
  ```

**AC8 — Prvi CI run je POST-MERGE push trigger; svaki naredni PR koristi `pull_request` trigger**

- **Given** `.github/workflows/ci.yml` postoji u Story 1.9 PR branch-u
- **When** Mihas otvori Story 1.9 PR ka `master`
- **Then** **GitHub Actions NE pokreće CI workflow na taj PR** (circular dependency: `pull_request` trigger zahteva workflow fajl u DEFAULT branch-u pre nego što radi; `ci.yml` jos uvek nije u master-u). Ovo je expected GitHub Actions ponasanje — vidi Gotcha CI-4 i Decision D12.
- **And** posle merge-a Story 1.9 PR-a u master, **prvi CI run se odvija na `push` triggeru** (jer push na master triggeruje `on.push.branches: [master]` part workflow-a):
  - `lint` job: `ruff check .` + `djade --check templates/partials/*.html` — green (svi Story 1.1-1.8 fajlovi su ranije prošli ruff/djade lokalno; base.html izuzet per Decision D14).
  - `test` job: `uv run pytest` — green (svi `tests/test_*.py` testovi prolaze; ovo je smoke verifikacija da Story 1.7 + 1.8 testovi nisu regrediram). **NEMA `manage.py check --deploy` step-a (IMP-IT2-1 — vidi Decision D13).**
  - `build` job: `docker build` kroz buildx — green (`compose/django/Dockerfile` builduje bez greške).
- **And** verifikacija: posle merge-a Story 1.9, push na master triggeruje sva tri job-a (`lint`, `test`, `build`) i sva tri prikazuju green status u GitHub Actions UI-ju (Tab → Actions → najnoviji run).
- **And** **Pre-merge dry-run opcija (IMP-IT2-4 — silent fail mitigation):** Mihas može gurati Story 1.9 commits na throwaway feature branch (npr. `tmp/ci-dry-run`), otvoriti tu branch u GitHub UI, kliknuti Actions tab → CI workflow → "Run workflow" dugme (workflow_dispatch trigger iz AC1) da verifikuje workflow validnost PRE merge-a u master. Ovaj korak je **preporučen ali ne mandator** (Mihas može ići pravo na merge ako ima visok confidence u skeletu — silent fail rizik je ograničen na 1 minut do prvog post-merge run-a). Vidi Decision D13.
- **And** **svaki naredni PR ka master-u (počevši od Story 2.1 PR-a) triggeruje CI kroz `pull_request` trigger** — sada radi jer `ci.yml` je u default branch-u:
  - PR otvoren → GitHub Actions startuje sva tri job-a.
  - Ako CI je green, PR check status je "All checks have passed" — branch protection (Task 5.6 — DoD blocker, IMP-7) omogucava "Merge pull request" dugme.
  - Ako CI je crveno (npr. ruff prijavi nov lint error u Story 2.1 kodu), PR check status je "Some checks were not successful" — branch protection BLOKIRA merge; Mihas mora fix-ovati lokalno PRE re-push-a.
- **And** **Manual sign-off (Task 5.5):** Mihas mora ručno verifikovati prvi post-merge push CI run — green status na sva tri job-a je condition za "Story 1.9 done" status u sprint-status.yaml.
- **And** **Napomena (iter-2 AC8 framing):** "First CI run green" condition applies to NEW gates that Story 1.9 introduces (`ruff check .`, `djade --check templates/partials/*.html`, `docker build`). 2 pre-existing test failures u `tests/test_base_template.py` (`test_ac7_htmx_min_js_version_1_9_x` + `test_ac8_main_css_exists_placeholder`) reflektuju Story 1.7/1.8 vendor i main.css drift (verifikovano kroz `git stash` da NIJE Story 1.9 regression). Mihas MORA pre branch protection enable-ovanja: ili **(a)** regenerisati `htmx.min.js` sa očuvanim verzionim komentarom i recompile-ovati `main.css` placeholder, ili **(b)** prilagoditi assertion-e u `test_base_template.py` (smaller scope). Bez ovog manual koraka, branch protection ne sme biti aktiviran jer bi blokirao buduće PR-ove. Ovo je dokumentovan known issue, NE Story 1.9 regression.

**AC9 — Token / file discipline za novi `.github/workflows/ci.yml`: koristi pinned major-version actions (verifikovane na current latest stable), NEMA hardcoded secrets, sve action-i su iz oficijelnih sources-a**

- **Given** `ci.yml` postoji
- **When** grep / manual review fajla
- **Then** sledeće mora biti zadovoljeno:
  - **Pinned major versions (MINIMUM acceptable — verifikovano na datum 2026-05-29):**
    - `actions/checkout@v4` (verified 2026-05-29)
    - `astral-sh/setup-uv@v3` (verified 2026-05-29)
    - `docker/setup-buildx-action@v3` (verified 2026-05-29)
    - `docker/build-push-action@v6` (verified 2026-05-29)
    - `pre-commit/pre-commit-hooks` rev `v4.6.0` u `.pre-commit-config.yaml` (verified 2026-05-29)
    - **NAPOMENA (CRIT-4):** Pre commit-a, Dev MORA verifikovati current latest stable major na `https://github.com/<owner>/<action>/releases` (npr. `astral-sh/setup-uv`, `docker/build-push-action`, `docker/login-action`, `actions/checkout`). Ako je major verzija viša u trenutku implementacije, koristiti najnoviji stable major (npr. ako `astral-sh/setup-uv@v5` postoji 2026-05-29 ili kasnije, pin na `@v5`).
    - **Pin format:** `@v<MAJOR>` (npr. `@v5`) — NE `@latest` (anti-pattern AC9), NE `@main` (anti-pattern AC9). Za supply-chain security opciono: pin na SHA (`actions/checkout@<40-char-sha>`).
  - **NEMA hardcoded secrets:** sve secret reference idu kroz `${{ secrets.NAME }}` ili `${{ github.token }}` / `${{ secrets.GITHUB_TOKEN }}`. NEMA `password: my-actual-password`.
  - **Sve action-i su iz oficijelnih sources-a:** `actions/*` (GitHub official), `astral-sh/*` (uv official), `docker/*` (Docker official), `pre-commit/*` (pre-commit official). NEMA fork-ovi ili nepoznati third-party action-i.
  - **Eksplicitni `working-directory: .` gde je relevantno** — opciono, default je repo root pa nije strict required.
  - **NEMA `continue-on-error: true`** za bilo koji step u Story 1.9 (IMP-IT2-1 — `manage.py check --deploy` step koji je ranije imao `continue-on-error: true` je UKLONJEN; vidi Decision D13).
- **And** YAML sintaksa je validna (lint kroz GitHub Actions parser pri prvom push-u; ako YAML nije valid, GitHub UI prijavi "workflow file invalid" odmah).
- **And** sve indentation je 2-space (YAML standard, matches `compose/local.yml` projektni stil).

## Tasks / Subtasks

### Task 1 — Kreiranje `.github/workflows/ci.yml` (AC1, AC2, AC3, AC4, AC9)

- [x] 1.1: Kreirati direktorijum `.github/workflows/` u repository root-u (prvi put se kreira u projektu). PowerShell: `New-Item -ItemType Directory -Force .github/workflows/`.
- [x] 1.2: Kreirati `.github/workflows/ci.yml` sa YAML skeleton-om (vidi pun skelet u "ci.yml — pun skelet predlog" sekciji):
  ```yaml
  name: CI

  on:
    push:
      branches: [master]
    pull_request:
      branches: [master]
    workflow_dispatch:  # IMP-IT2-4: Manual run iz Actions UI — pre-merge dry-run i debugging

  permissions:
    contents: read  # workflow-level least-privilege (IMP-1)

  concurrency:
    group: ci-${{ github.ref }}
    cancel-in-progress: true

  jobs:
    lint:
      runs-on: ubuntu-latest
      timeout-minutes: 10
      env:
        DJANGO_SECRET_KEY: ci-test-secret-key-not-for-prod-50chars-padding
      steps:
        # Step 1: Checkout
        # Step 2: Setup uv (python-version 3.13)
        # Step 3: uv sync --frozen --group dev
        # Step 4: uv run ruff check .
        # Step 5: uv run djade --check templates/partials/*.html  (iter-2 sync; base.html izuzet per D14)

    test:
      runs-on: ubuntu-latest
      timeout-minutes: 10
      env:
        DJANGO_SECRET_KEY: ci-test-secret-key-not-for-prod-50chars-padding
        # DATABASE_URL not set — base.py default sqlite:///db.sqlite3 (see Gotcha CI-7)
      steps:
        # Step 1: Checkout
        # Step 2: Setup uv (python-version 3.13)
        # Step 3: uv sync --frozen --group dev
        # Step 4: uv run pytest
        # NOTE (IMP-IT2-1): manage.py check --deploy step UKLONJEN — vidi Decision D13

    build:
      runs-on: ubuntu-latest
      timeout-minutes: 15
      needs: [lint, test]
      permissions:
        packages: write  # job-level (IMP-1); placeholder za Story 9.2 push
      steps:
        # Step 1: Checkout
        # Step 2: Setup buildx
        # Step 3: Set lowercase image name (IMP-2)
        # Step 4: docker/build-push-action (push: false, BEZ GHCR login — IMP-6)
  ```
- [x] 1.3: Implementirati `lint` job-ove step-ove (vidi AC2 za pun listing):
  - `env: DJANGO_SECRET_KEY` postavljen (CRIT-2 + Gotcha CI-1).
  - `actions/checkout@v4` (nema parametara — default checkout).
  - `astral-sh/setup-uv@v3` sa `python-version: '3.13'` (IMP-9), `enable-cache: true`, `cache-dependency-glob: "uv.lock"`.
  - `uv sync --frozen --group dev` (run command).
  - `uv run ruff check .` (run command).
  - `uv run djade --check templates/partials/*.html` (run command — iter-2 narrative sync; flat glob, base.html izuzet per Decision D14).
- [x] 1.4: Implementirati `test` job-ove step-ove (vidi AC3 za pun listing):
  - `env: DJANGO_SECRET_KEY` postavljen (CRIT-1 + Gotcha CI-1). **NEMA `DATABASE_URL` env-a (CRIT-IT2-1)** — `base.py:78` default-uje na `sqlite:///db.sqlite3`; vidi Gotcha CI-7.
  - isti checkout + setup-uv (sa `python-version: '3.13'`) + `uv sync --frozen --group dev`.
  - `uv run pytest` (run command). **NEMA `manage.py check --deploy` step-a (IMP-IT2-1)** — vidi Decision D13.
- [x] 1.5: Implementirati `build` job-ove step-ove (vidi AC4 za pun listing; IMP-6 — GHCR login deferred):
  - Job-level `permissions: packages: write` (IMP-1).
  - `actions/checkout@v4`.
  - `docker/setup-buildx-action@v3`.
  - **Set lowercase image name** (IMP-2): `run: echo "IMAGE_NAME=$(echo '${{ github.repository }}' | tr '[:upper:]' '[:lower:]')" >> $GITHUB_ENV`.
  - `docker/build-push-action@v6` sa `context: .`, `file: ./compose/django/Dockerfile`, `push: false`, `tags: ghcr.io/${{ env.IMAGE_NAME }}:ci-${{ github.sha }}`, `cache-from: type=gha`, `cache-to: type=gha,mode=max`.
  - **NEMA `docker/login-action@v3`** — deferred do Story 9.2 (IMP-6).
- [x] 1.6: Verifikovati YAML validnost lokalno — `Get-Content .github/workflows/ci.yml | Select-String "^\s*-"` (basic indent check) ILI online YAML validator. **Decision D9:** Story 1.9 NE uvodi `yamllint` u dev deps jer scope eksplicitno isključuje novi tooling osim za CI artifacts; YAML validacija se desi pri prvom push-u (GitHub Actions parser).
- [x] 1.7: Anti-pattern provera (AC9):
  - Grep `\@latest|\@main` u `ci.yml` (forbidden — sve action-i pinned na `@vN`).
  - Grep `password: [^$]` van `${{ secrets.* }}` patterns (forbidden — NEMA hardcoded password).
  - Grep `continue-on-error: true` u `ci.yml` (forbidden u Story 1.9 — IMP-IT2-1 uklonio jedini step koji je to imao).

### Task 2 — Kreiranje `.pre-commit-config.yaml` (AC6, AC7)

- [x] 2.1: Kreirati `.pre-commit-config.yaml` u repository root-u sa YAML strukturom iz AC6:
  - `repos:` section sa tri `repo:` block-a (`pre-commit-hooks` + `ruff-pre-commit` + `djade-pre-commit`).
  - **(IMP-5) `pre-commit/pre-commit-hooks` rev: `v4.6.0`** sa hooks: `trailing-whitespace`, `end-of-file-fixer`, `check-yaml`, `check-merge-conflict`.
  - `ruff-pre-commit` rev: `v0.15.14` (matches `pyproject.toml` `ruff>=0.15.14`).
  - `ruff-pre-commit` hooks: `ruff-check` sa `args: [--fix]` i `ruff-format` (oba hooks).
  - `djade-pre-commit` rev: `1.9.0` (matches `pyproject.toml` `djade>=1.9.0`).
  - `djade-pre-commit` hooks: `djade` sa `args: [--target-version, "5.2"]`.
- [ ] 2.2: Verifikovati lokalno: `uv run pre-commit install` (postavi hook), pa `uv run pre-commit run --all-files` (sve fajlove provera; očekuje green ili fixable issues koje `--fix` rešava). _(Manual verification step — Mihas pokrece lokalno post-merge.)_
- [ ] 2.3: Ako `pre-commit run --all-files` prijavi issue-e koji nisu auto-fixovani (npr. djade template format koji `--check` ne menja u manual run-u), Dev koristi `uv run djade templates/partials/*.html` (iter-2 sync) da format-uje pa onda commit. base.html izuzet per Decision D14.
- [x] 2.4: Verifikovati da `.pre-commit-config.yaml` `rev:` field-ovi sync-uju sa `pyproject.toml` `[dependency-groups.dev]` versions (Decision D8 sync-disciplinski problem). _Verified: ruff v0.15.15 >= pyproject ruff>=0.15.14; djade 1.9.0 == pyproject djade>=1.9.0._

### Task 3 — Dev Notes dokumentacija (AC5, AC7)

- [x] 3.1: Dodati sekciju "Lokalni pre-commit install workflow" u Dev Notes (AC7 koraci 1-4). _(Sekcija postoji u ovom story fajlu — "Lokalni pre-commit install workflow (AC7)".)_
- [x] 3.2: Dodati sekciju "CI debugging steps" u Dev Notes (lokalna reprodukcija lint/test/build failure-a). _(Sekcija postoji u ovom story fajlu — "CI debugging steps (AC7)".)_
- [x] 3.3: Dodati sekciju "GHCR + Secrets Management" u Dev Notes (AC5 detalji: `GITHUB_TOKEN` default, namespace `ghcr.io/<owner>/<repo>` lowercase per IMP-2, branch protection rules manual setup; login + push deferred do Story 9.2 per IMP-6). _(Sekcija postoji — "GHCR + Secrets Management (AC5)".)_
- [x] 3.4: Dodati sekciju "Decisions log" u Dev Notes sa D1-D13 tabelom (D11 = pre-commit ne pokrece pytest, D12 = prvi CI run je post-merge push + DB strategija per CRIT-IT2-1, D13 = `manage.py check --deploy` izostavljen + `workflow_dispatch` dodat per IMP-IT2-1/IMP-IT2-4 — vidi Dev Notes sekciju). _(Sekcija postoji — "Decisions log".)_
- [x] 3.5: Dodati sekciju "Gotchas" u Dev Notes sa minimum 7 CI-specifičnih gotchas (CI-1 do CI-8 — CI-7 i CI-8 dodati u Iter 2 za CRIT-IT2-1 + IMP-IT2-3). _(Sekcija postoji — "Gotchas".)_
- [x] 3.6: Dodati sekciju "Branch protection rules — manual setup" u Dev Notes sa step-by-step uputstvom za GitHub UI (Settings → Branches → Add rule → "Require status checks to pass before merging" → "Require branches to be up to date" → select `lint`, `test`, `build` jobs). _(Sekcija postoji u "GHCR + Secrets Management" → "Branch protection rules — manual setup".)_

### Task 4 — Opcioni `justfile` recept za pre-commit install (AC7 OPCIONAL — gold-plate)

- [x] 4.1: Dodati novi recept u `justfile` (POSLE `messages` recept-a):
  ```just
  # Setup pre-commit hooks (jednokratno posle klon-a)
  precommit-install:
      uv run pre-commit install
  ```
- [ ] 4.2: Test lokalno: `just precommit-install` mora installirati pre-commit hook (verifikuje da `.git/hooks/pre-commit` postoji posle). _(Manual verification — Mihas pokrece.)_
- [x] 4.3: **NAPOMENA:** Ovaj task je OPCIONALAN gold-plate. Ako Dev odluči da ga ne implementira (npr. zato što justfile expansionet nije critical), Story 1.9 i dalje prolazi sve ostale AC-ove. Acceptable scope deviation. _Dev je dodao recept._

### Task 5 — Manual verification & sign-off (AC8)

- [ ] 5.1: Push lokalnu Story 1.9 branch (npr. `feature/epic1-story-1.9-ci-pipeline`) ka GitHub.
- [ ] 5.2: GitHub UI: otvoriti PR ka `master` branch-u. **NAPOMENA (Decision D12 + Gotcha CI-4):** Ovaj PR NE pokrece CI jer `ci.yml` jos uvek nije u default branch-u. Expected ponasanje — verifikacija dolazi u 5.3 POSLE merge-a.
- [ ] 5.3: **POSLE merge-a Story 1.9** (Decision D12), GitHub Actions: verifikovati da `ci.yml` pokreće tri job-a (`lint`, `test`, `build`) na `push` triggeru:
  - `lint` job zelena (svi Story 1.1-1.8 fajlovi su prošli ruff/djade ranije, regression test).
  - `test` job zelena (svi `tests/test_*.py` — trenutno 8 fajlova per IMP-10 — prolaze). NEMA `manage.py check --deploy` step (IMP-IT2-1).
  - `build` job zelena (`docker build` prolazi sa cached GHA layer-ima; NEMA GHCR login per IMP-6 — verifikacija samo da Dockerfile builduje bez sintaksne greske).
- [ ] 5.4: ~~Verifikovati GHCR login step~~ DEFERRED do Story 9.2 (IMP-6). Zamenjeno: **verifikovati IMAGE_NAME lowercase transformation** — `build` job "Set lowercase image name" step logs prikazuju lowercase `IMAGE_NAME` env (placeholder `<github_owner>/<github_repo>` se runtime-resolve-uje u konkretnu lowercase vrednost) per IMP-2 + Gotcha CI-2.
- [ ] 5.5: Manual smoke test lokalno:
  - `uv run pre-commit run --all-files` (sve fajlove kroz pre-commit hooks — očekuje green).
  - `uv run ruff check .` (lokalno mora prolaziti — isti standard kao CI).
  - `uv run djade --check templates/partials/*.html` (isto — green lokalno = green CI; iter-2: scope match-uje ci.yml).
  - `uv run pytest` (isto — green lokalno = green CI).
- [ ] 5.6: **Branch protection rules manual setup — DoD BLOCKER (IMP-7):** Story 1.9 NE moze biti `done` bez ovog setup-a, jer bez branch protection nista ne zaustavlja merge crvene PR-eve → defeats the entire purpose of CI gate.
  - [ ] **PRE-STEP (iter-2 AC8 framing):** Rešiti 2 pre-existing test failure-a u `tests/test_base_template.py` (`test_ac7_htmx_min_js_version_1_9_x` + `test_ac8_main_css_exists_placeholder`) koji reflektuju Story 1.7/1.8 vendor i main.css drift (NIJE Story 1.9 regression — verifikovano `git stash`-om). Bez ovog koraka branch protection bi blokirao SVE buduće PR-ove jer `test` job ostaje crveno. Opcija (a) regenerisati `htmx.min.js` + recompile `main.css`; opcija (b) prilagoditi assertion-e u `test_base_template.py` (smaller scope).
  - GitHub UI → Settings → Branches → Add rule
  - Branch name pattern: `master`
  - Require status checks to pass before merging: ON
  - Require branches to be up to date before merging: ON
  - Status checks: `lint`, `test`, `build` (sve tri)
  - Include administrators: ON (samo-disciplinujem; Mihas ne moze bypass-ovati CI ni kao admin)
  - **Verifikacija obavezna:** posle setup-a, izvrsiti `gh api repos/<owner>/<repo>/branches/master/protection` (ili GitHub UI screenshot) — output mora pokazati `required_status_checks.contexts: [lint, test, build]`. Bez ove verifikacije, Task 5.6 NIJE done.
- [x] 5.7: Update sprint-status.yaml: `1-9-github-actions-ci-pipeline: review` (posle Dev implementacije; Dev će ovo uraditi po završetku).

## Dev Notes

### Kontekst story-ja

Story 1.9 je **poslednja story u Epic 1** i zatvara temelj projekta. Posle nje, Epic 2 (Public Catalog) može da startuje sa sigurnošću da svaki push aktivira `ruff/djade/pytest` gate. Ova story je **infra-only** — NEMA Django app promene, NEMA template / CSS / JS promene, NEMA pyproject.toml dep promene. Sve dev deps su već u Story 1.1 (`ruff>=0.15.14`, `djade>=1.9.0`, `pytest>=9.0.3`, `pytest-django>=4.12.0`, `pre-commit>=4.6.0`).

Story 1.9 je takođe **prvi konzument `.github/workflows/`** i postavlja precedent za sve buduće GitHub Actions workflow-ove:
- `deploy.yml` (Story 9.2 — staging + production deploy ka Hetzner)
- Eventualni `release.yml` (semantic-release ili manual tagging) — out-of-scope za v1
- Eventualni `scheduled-deps-audit.yml` (npr. weekly `uv pip audit`) — out-of-scope za v1

### Tech stack — CI/CD specifics

- **GitHub Actions** je SOT za CI (per architecture.md linija 214: "GitHub Actions (free tier 2000 min/mo) — Standard; free za solo dev").
- **ubuntu-latest** runner (24.04 LTS u 2026) za sva tri job-a — standardni izbor, dobro testiran sa `uv` + Docker Buildx.
- **`astral-sh/setup-uv@v3`** je oficijelan uv setup action (https://github.com/astral-sh/setup-uv) — zamenjuje stari `actions/setup-python@v5` + manual `pip install uv` pattern (Decision D2).
- **`docker/build-push-action@v6`** je oficijelan Docker action (https://github.com/docker/build-push-action) — podržava GHA layer cache preko `cache-from: type=gha` + `cache-to: type=gha,mode=max` (Decision D10).
- **GHCR (GitHub Container Registry)** je free tier registry vezan za GitHub repo — `secrets.GITHUB_TOKEN` ima default `packages: write` scope kad je `permissions:` workflow-level deklaracija (per architecture.md linija 215).

### Decisions log

| # | Pitanje | Default izbor | Alternativa | Rationale |
|---|---|---|---|---|
| D1 | Pytest runtime: `uv` venv na runner-u vs Docker container | **`uv` venv na runner-u** | Pokrenuti `pytest` u Docker container-u (kroz `docker compose run`) | Brže (~30-60s vs ~3-5min); Story 1.1-1.8 testovi NE zahtevaju live DB (vidi `tests/conftest.py` — bez `@pytest.mark.django_db` koji bi triggerovao Django test DB setup); production parity stiže u Epic 9 9.1; Docker integration test job se može dodati u `deploy.yml` (Story 9.2) ili kao zaseban `ci-docker.yml` u budućnosti |
| D2 | uv setup u CI + action version verification ritual + **pre-commit hook repos verifikacija (IMP-IT2-2)** | **`astral-sh/setup-uv@v3` (oficijelan action) + verifikuj latest stable major na GitHub Releases pre commit-a za SVE GHA actions I SVE pre-commit hook repos** | `actions/setup-python@v5` pa `pip install uv` u manual step-u | Oficijelan action je zvanično podržan od `astral-sh` (uv autor); integrirani GitHub Actions cache; jedan step umesto dva. **PROSIRENJE (IMP-IT2-2):** version verification ritual sada uključuje pre-commit hook repos: `pre-commit/pre-commit-hooks`, `astral-sh/ruff-pre-commit`, `adamchainz/djade-pre-commit`. Dev MORA verifikovati current stable major na GitHub Releases (`https://github.com/<owner>/<repo>/releases`) pre commit-a — ako je viši major (npr. `pre-commit-hooks v5.x` u 2026), koristi njega. Hardkoderani pin u Story 1.9 (`v4.6.0`) je 2024 verzija, MINIMUM acceptable; verifikacija obavezna jer 18+ meseci je dovoljno da se major podigne. |
| D3 | uv deps cache strategija u CI | **`enable-cache: true` + `cache-dependency-glob: "uv.lock"`** | Manual `actions/cache@v4` sa custom key | Oficijelan setup-uv@v3 integriše cache automatski; `cache-dependency-glob` invalidira cache TAČNO kad `uv.lock` se menja — manual `actions/cache@v4` je više code za isti rezultat |
| D4 | `uv sync` flags u CI: `--group dev` vs `--all-groups` vs `--no-dev` | **`uv sync --frozen --group dev`** | `uv sync --frozen --all-groups` ILI `uv sync --frozen` (default = all groups) | Eksplicitno `--group dev` matchuje `pyproject.toml` `[dependency-groups.dev]`; jasno čitljivo; `--frozen` osigurava da CI ne menja `uv.lock` |
| D5 | Deduplikacija lint + test `uv sync` step-a | **NE — separate `uv sync` u svakom job-u** | Reusable workflow (composite action) ili matrix strategy | Story 1.9 v1 scope ne uvodi reusable workflows; cache hit u job-2 brzo (~5-10s) jer cache se deli kroz workflow run; YAML jednostavnost iznad DRY |
| D6 | GHCR autentifikacija: `secrets.GITHUB_TOKEN` vs custom PAT | **`secrets.GITHUB_TOKEN` (default GHA token)** | Custom Personal Access Token kao `secrets.GHCR_PAT` | Default token + workflow-level `permissions: packages: write` je dovoljno za GHCR push i pull; manual PAT setup nije potreban; manje secret-a za održavanje |
| D7 | Pre-commit config: `repos:` sa hooks vs `repository_local: true` (local-only hooks) | **`repos:` sa external pre-commit hooks (ruff-pre-commit + djade-pre-commit)** | Local hooks koji direktno pozivaju `uv run ruff check` | External hooks su standardni pre-commit pattern; auto-update preko `pre-commit autoupdate`; isti standard kao većina Django open-source projekata |
| D8 | Verzija pinning sync između `pyproject.toml` i `.pre-commit-config.yaml` | **Manual sync (pin u oba)** | `pre-commit autoupdate` automation u CI | Story 1.9 v1 scope ne uvodi automation za `autoupdate`; Mihas obavezno proverava sync kad menja ruff/djade verziju u pyproject.toml; alternative scope-ovan u Epic 9 polish |
| D9 | YAML lint tooling u Story 1.9 (`yamllint` u dev deps) | **NE — GitHub Actions parser je dovoljan** | `uv add --dev yamllint` + dodati u `lint` job | Story 1.9 scope eksplicitno isključuje nove dev deps; YAML validnost se verifikuje pri prvom push-u (GitHub UI prijavi loš YAML); over-engineering za v1 |
| D10 | Docker buildx layer cache: GHA (type=gha) vs registry (type=registry) | **`type=gha,mode=max`** | `type=registry,ref=ghcr.io/<repo>:cache` | GHA cache je free i bez quota issue-a za solo dev (10GB per repo); registry cache zahteva push u GHCR koji je deferred do Story 9.2; per-job cache hit ratio dovoljan |
| D11 | Pre-commit pokrece samo brze lint hookove (ruff + djade + std hooks), NE pytest | **Pre-commit: ruff + djade + std hooks; pytest = CI-only** | Dodati `pytest` kao pre-commit hook (npr. preko `local` repo sa `entry: uv run pytest`) | Pytest traje ~30-60s na Story 1.9 codebase-u; pre-commit budget je <5s da ne ometa git commit UX (svaki amend, rebase, cherry-pick re-trigeruje pre-commit). CI je pravo mesto za pytest gate jer GHA runner ima dedicated CPU budget i job timeout. Time je narrative consistent: pre-commit i CI imaju 1:1 LINT sync (ruff + djade verzije match), ne 1:1 ceo CI flow sync. Adresira CRIT-3. |
| D12 | Prvi CI run je post-merge push, ne PR check + **DB strategija** (CRIT-IT2-1) | **Post-merge push trigger** + **SQLite default iz `base.py:78` — bez `DATABASE_URL` env override-a u CI** | Manually trigger workflow_dispatch na PR branch-u pre merge-a | GitHub Actions ima fundamental constraint: `pull_request` trigger ne radi za workflow fajl koji nije u default branch-u u trenutku PR-a (circular dependency). Posledica: Story 1.9 PR ka master NE pokreće CI (workflow jos uvek nije u master-u). Posle merge-a Story 1.9 PR-a, push na master triggeruje `on.push.branches: [master]` part workflow-a — to je prvi CI run. Svaki naredni PR (počevši od Story 2.1) koristi `pull_request` trigger jer `ci.yml` je sada u default branch-u. **DB strategija (CRIT-IT2-1):** test job NE postavlja `DATABASE_URL` env — `config/settings/base.py:78` već default-uje DATABASES na `sqlite:///db.sqlite3`. Postavljanje `DATABASE_URL=sqlite:///test.db` bilo bi redundantno i kreiralo DB na non-default putanji (maskira pravo ponašanje). Adresira CRIT-5 + CRIT-IT2-1. |
| D13 | `manage.py check --deploy` step izostavljen iz Story 1.9 CI + `workflow_dispatch` trigger za pre-merge dry-run | **(a) `manage.py check --deploy` step UKLONJEN iz Story 1.9 v1; (b) `workflow_dispatch:` trigger DODAT u `on:` listu** | (a) Zadržati step sa `continue-on-error: true`; (b) ne dodavati `workflow_dispatch` (čekati Story 9.2) | **(a) Step izostavljen jer:** (1) `config.settings.development` namerno ima `DEBUG=True` i bez prod-flagova (`SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS`, itd.); (2) `--fail-level WARNING` + `continue-on-error: true` čine step placebo — uvek prijavi warnings koje step ignoriše, ne dodaje vrednost u CI gate-u; (3) pravo mesto za `check --deploy` je Story 9.6 (Django logging) nakon prelaska na `settings.production` SA `continue-on-error: false` (strict). Adresira IMP-IT2-1. **(b) `workflow_dispatch` trigger dodat jer:** (1) silent fail mitigation — Mihas može pre-merge dry-run na throwaway branch (`tmp/ci-dry-run`) kroz Actions UI "Run workflow" dugme; (2) debugging pomoć kad CI ima flake bez code change; (3) one-time over-engineering kost je minimalan (jedna linija). Adresira IMP-IT2-4. |
| **D14** | **base.html temporary djade exclusion (iter-1 compromise)** | **djade scope sužen na `templates/partials/*.html` (base.html izuzet)** | Uključiti base.html u djade scope odmah u Story 1.9 (= razbiti 5+ postojećih testova) | Story 1.5/1.6/1.7 testovi imaju literal substring asercije za pojedinačne `{% load %}` direktive u base.html. djade 1.9.0 konsoliduje 4 `{% load %}` direktive u jednu `{% load i18n static django_bootstrap5 htmx_aria %}` — što bi razbio 5+ postojećih testova u `tests/test_base_template.py` (substring assercije tipa `assert "{% load i18n %}" in content`). Iter-1 compromise: ci.yml djade scope sužen na `templates/partials/*.html` (base.html izuzet). **Cleanup contract:** Story 2.1 (ili dedicated tech-debt story pre toga) MORA ili **(a)** restruktuirati `templates/base.html` da ima 1 konsolidovan `{% load %}` line (format koji djade generiše), ili **(b)** update Story 1.5/1.6/1.7 testove da prihvate djade consolidated format. Opcija (a) je preporučena. Vidi IMP-12 (updated iter-2) za concrete migration pattern (`git ls-files '*.html' \| xargs -r uv run djade --check`). Adresira iter-2 TEST_GAP #6 (audit trail za base.html exclusion). |

### Gotchas

CI-specifične gotchas koje Dev MORA znati pre implementacije (IMP-13):

- **Gotcha CI-1 — `DJANGO_SECRET_KEY` MORA biti u CI env-u (test + lint job):**
  - `config/settings/base.py` linija 17: `SECRET_KEY = env("DJANGO_SECRET_KEY")` — NEMA default.
  - `pytest-django` ucitava `DJANGO_SETTINGS_MODULE` PRE collect-a testova → poziva `base.py` → `env("DJANGO_SECRET_KEY")` → ako env var nije set, `django-environ` baca `ImproperlyConfigured: DJANGO_SECRET_KEY not found`.
  - Posledica: bez ovog env-a, test job pada 100% na prvom run-u sa cryptic error message-om (NE pytest fail, vec settings load fail pre pytest-a).
  - **Fix:** `env: DJANGO_SECRET_KEY: ci-test-secret-key-not-for-prod-50chars-padding` na test job. Lint job dobija isti env defensively (`djade>=1.9.0` standalone parser NE poziva settings, ALI buduca verzija moze promeniti ponasanje, ili nov lint hook moze uvesti settings load — 0-cost insurance).
  - Adresirano u CRIT-1/CRIT-2 fix-u (AC2 + AC3).

- **Gotcha CI-2 — GHCR namespace mora biti lowercase:**
  - GitHub Container Registry (`ghcr.io`) zahteva lowercase namespace (`ghcr.io/<github_owner>/<github_repo>`).
  - `${{ github.repository }}` GHA context expression vraca raw repo path — moze biti mixed case (placeholder primer: `<Github_Owner>/<Github_Repo>`).
  - Posledica: ako se mixed-case namespace prosledi `docker/build-push-action@v6` `tags:` field-u, build pada sa: `ERROR: failed to solve: failed to push ghcr.io/<Github_Owner>/<Github_Repo>:ci-abc1234: invalid reference format: repository name must be lowercase`.
  - **Fix:** Shell transformacija u build job-u (IMP-2): `echo "IMAGE_NAME=$(echo '${{ github.repository }}' | tr '[:upper:]' '[:lower:]')" >> $GITHUB_ENV`, zatim koristiti `${{ env.IMAGE_NAME }}` u tag template-u. Polish-C: konzistentni placeholder syntax `<github_owner>/<github_repo>` koristi se kroz ceo dokument (Dev Notes + Gotcha).
  - Adresirano u AC4 Step 3.

- **Gotcha CI-3 — `setup-uv@vN` cache-dependency-glob mora tačno matchovati `uv.lock` putanju:**
  - `astral-sh/setup-uv@v3` koristi `cache-dependency-glob:` field za cache key (default je nesto kao `**/uv.lock`).
  - Ako repo ima više lock fajlova (npr. monorepo sa `subproject/uv.lock`), glob moze matchovati pogresan fajl → cache miss je TIH (action ne prijavi warning, samo se cache ne hit-uje).
  - Posledica: clean install svaki run (~60-90s umesto cached ~5-10s) → spori CI run-ovi bez visible signala.
  - **Fix:** Eksplicitno `cache-dependency-glob: "uv.lock"` (exact path, ne glob) za single-repo single-lockfile setup. Ako kasnije postanemo monorepo, ažurirati glob.
  - Postavljeno u AC2 i AC3 Step 2.

- **Gotcha CI-4 — `pull_request` trigger NE RADI dok workflow fajl nije u default branch-u:**
  - GitHub Actions fundamental constraint: `on.pull_request.*` trigger evaluira workflow definiciju iz default branch-a (NE iz PR branch-a) za sigurnost (sprečava da PR ubaci malicious workflow).
  - Posledica: prvi PR koji uvodi `ci.yml` (Story 1.9 PR) NE pokreće CI. GitHub UI prikazuje 0 checks na PR-u.
  - **Fix:** Story 1.9 prvi CI run je `push` trigger nakon merge-a (Decision D12). Adresirano u CRIT-5 + AC8 + Decision D12.

- **Gotcha CI-5 — Docker Hub anonymous pull rate limit za base image:**
  - `compose/django/Dockerfile` koristi `python:3.13-slim` base image (Docker Hub).
  - Docker Hub anonymous rate limit: 100 pulls / 6h po IP (shared GHA runner IP pool).
  - Posledica: u peak hours (US business day), pull moze hang-ovati ili pasti sa `toomanyrequests: You have reached your pull rate limit`. Retry scenariji mogu hang-ovati build job bez ikakvog progress signala.
  - **Fix:** `timeout-minutes: 15` na build job (IMP-4) sprečava infinite hang. Ako problem postane chronic, Story 9.x moze uvesti Docker Hub authenticated pull (5000 pulls / 6h za free account) ili switch na mirror (npr. `mcr.microsoft.com/devcontainers/python:3.13`).

- **Gotcha CI-6 — Verzija drift između `pyproject.toml` i `.pre-commit-config.yaml`:**
  - `pyproject.toml` `[dependency-groups.dev]` ima MINIMUM constraints (`ruff>=0.15.14`, `djade>=1.9.0`).
  - `.pre-commit-config.yaml` `rev:` polja su EXACT version pins (`v0.15.14`, `1.9.0`).
  - Posledica: ako `uv add --dev ruff==0.16.5` u budućnosti update-uje `pyproject.toml`, `.pre-commit-config.yaml` OSTAJE na `v0.15.14` dok Mihas manualno ne update-uje. Rezultat: pre-commit lokalno koristi stari ruff (0.15.14) dok CI lint job koristi noviji ruff (0.16.5) iz `uv sync` — fail u CI koji ne reprodukuje lokalno.
  - **Fix:** Manual sync discipline (Decision D8) ili `pre-commit autoupdate` u dev workflow-u. Story 1.9 dokumentuje ali ne automatizuje.

- **Gotcha CI-7 — pytest-django + SQLite + lazy session creation (postojeci testovi ne koriste @pytest.mark.django_db):**
  - Postojeci tests/ fajlovi (test_base_template, test_i18n_setup, test_static_tokens) zovu `client.get("/sr/")` bez `@pytest.mark.django_db` dekoratora. Lokalno rade jer Django SessionMiddleware kreira session lazily — ne pise u DB za anonimni GET bez session mutacija (npr. `request.session["key"] = value`).
  - U CI:
    - `config/settings/base.py:78` default-uje DATABASES na `sqlite:///db.sqlite3` (SQLite je dovoljan za v1).
    - pytest-django bez `@pytest.mark.django_db` blokira DB access — ALI lazy session ne diralja DB pa testovi prolaze.
    - Ako buduca story (Epic 2+) doda test koji mutira session (npr. login flow), MORA dodati `@pytest.mark.django_db` ili pre dodavanja PostgreSQL u Epic 9 9.1 pretpostaviti service container u test job-u.
  - **Sto NE raditi:** ne dodavati `DATABASE_URL` env u test job (redundantno — `base.py:78` default-uje na SQLite); ne dodavati `migrate` step (pytest-django automatski radi `migrate` na test DB ako je `@pytest.mark.django_db` detektovan); ne menjati postojece testove samo da bi imali dekorator — to je YAGNI.
  - Adresira CRIT-IT2-1.

- **Gotcha CI-8 — `concurrency: cancel-in-progress: true` race sa branch protection:**
  - `concurrency.cancel-in-progress: true` (per AC1 IMP-3) otkazuje predhodni CI run kada novi push dolazi za isti branch.
  - Edge case: ako Mihas push-uje hotfix dok prvi post-merge CI run traje, prethodni run dobija status "canceled" — što NIJE "success" za branch protection (per Task 5.6). Sledeci PR check moze pasti dok novi run ne završi.
  - Acceptable trade-off: kratak prozor neusagasenosti vs duplikat CI minute potrošnja.
  - **Mitigation:** Ne push-uj hotfix neposredno nakon Story 1.9 merge-a; sačekaj prvi CI run da prođe (~3 min) pre sledećeg push-a. Adresira IMP-IT2-3.

### Lokalni pre-commit install workflow (AC7)

Posle Story 1.9 merge-a, novi onboarding (ili posle reset venv-a) workflow je:

1. **Instalirati dev deps:**
   ```powershell
   uv sync --group dev
   ```
   Ovo instalira `pre-commit>=4.6.0` zajedno sa `ruff`, `djade`, `pytest` itd.

2. **Setup pre-commit git hook:**
   ```powershell
   uv run pre-commit install
   ```
   Ovo postavlja `.git/hooks/pre-commit` shell script koji pokreće hooks iz `.pre-commit-config.yaml` na svaki `git commit`.

3. **(Opciono) Jednokratan run preko svih fajlova:**
   ```powershell
   uv run pre-commit run --all-files
   ```
   Verifikuje setup; očekuje green ili fixable issue-e koje `--fix` automatski rešava.

4. **Standardni dev loop posle setup-a:**
   - `git add <files>` (staging)
   - `git commit -m "..."` — pre-commit hook se pokreće automatski:
     - `ruff-check --fix` (auto-fix import sort + trailing whitespace + slično)
     - `ruff-format` (auto-format Python kod, ekvivalent black)
     - `djade --target-version 5.2` (Django template format)
   - Ako hook prijavi non-fixable issue, commit pada — Dev mora ručno fix-ovati i re-stage-ovati pa ponoviti `git commit`.
   - **NIKAD** `git commit --no-verify` (per project-context.md Anti-pattern § "Skipping pre-commit hooks").

5. **Update workflow (kad `ruff` ili `djade` dobiju novu verziju u `pyproject.toml`):**
   ```powershell
   uv run pre-commit autoupdate
   ```
   Ovo update-uje `rev:` polja u `.pre-commit-config.yaml` na latest verzije. Posle ovoga, **manual verifikacija** da nova `rev:` matchuje minimum version constraint u `pyproject.toml` (Decision D8 sync disciplina).

### CI debugging steps (AC7)

Ako CI workflow pada, Dev reprodukuje issue lokalno:

**`lint` job pada:**
```powershell
uv run ruff check .                                       # ista komanda kao CI Step 4
uv run djade --check templates/partials/*.html            # ista komanda kao CI Step 5 (iter-2 sync)
```
- Fix issue lokalno (`uv run ruff check . --fix` + `uv run djade templates/partials/*.html` za auto-fix), commit i push.
- **Napomena (iter-2):** ako menjate `base.html`, NE pokrećite djade na njega dok Decision D14 cleanup contract nije izvršen — djade 1.9.0 konsolidacija `{% load %}` direktiva razbija Story 1.5/1.6/1.7 testove. Lokalno `pre-commit` će automatski preskakati `base.html` ako sub-partials patern matchuje samo `templates/partials/*.html`.

**`test` job pada:**
```powershell
uv run pytest -v --tb=short                   # verbose + short traceback za debug
```
- Identifikuj failed test, fix kod, ponovi `pytest`.

**`build` job pada:**
```powershell
docker build -f compose/django/Dockerfile . --no-cache
```
- `--no-cache` flag isključuje lokalni Docker layer cache da reprodukuje CI-style clean build.
- Najčešći uzroci: `uv sync --frozen --no-install-project --no-dev` pada (stale `uv.lock`), `apt-get install` pada (network ili package not found).

**Cache miss debug:**
- GitHub Actions UI → workflow run → job → expand step "Set up uv" — pokaži "Cache hit" ili "Cache miss" status.
- Ako cache miss → `uv.lock` se promenio (očekivano) ILI cache key (`cache-dependency-glob`) je drugačiji od prethodnog run-a.

### GHCR + Secrets Management (AC5)

GitHub Container Registry (GHCR) je free container registry vezan za GitHub organizaciju ili user-a. Story 1.9 koristi GHCR za **buduće** image push-ove u Story 9.2 (deploy workflow). Story 1.9 samo verifikuje da login uspeva, NE push-uje image.

**Namespace konvencija:**
- `ghcr.io/<github_owner>/<github_repo>:<tag>` (placeholder; lowercase transformation kroz `tr` step iz IMP-2 generiše konkretne vrednosti za ovaj projekat).
- Primer posle lowercase transformacije: `ghcr.io/<github_owner>/<github_repo>:ci-abc1234` (kde je `abc1234` git sha skraćen). Polish-C: koristi se placeholder syntax za konzistentnost sa Gotcha CI-2 — konkretne owner+repo vrednosti se runtime-resolve-uju kroz `${{ github.repository }}` + `tr '[:upper:]' '[:lower:]'` transformaciju (AC4 Step 3).
- Story 9.2 će koristiti tag pattern `:latest` (production) + `:staging` (staging) + `:<sha>` (immutable per-commit).

**Autentifikacija:**
- `secrets.GITHUB_TOKEN` je default token koji GitHub Actions automatski generiše po job-u.
- Da bi imao `packages: write` scope (potreban za GHCR push), workflow MORA imati top-level `permissions:` block sa `packages: write` (per AC1).
- **NIJE potreban** manual PAT (Personal Access Token) setup u GitHub UI Settings → Developer Settings → Tokens.
- Token istekne na kraju job-a — sigurnije od long-lived PAT-a.

**Branch protection rules — manual setup (post Story 1.9 merge):**

Posle Story 1.9 merge-a u `master`, Mihas mora ručno konfigurisati branch protection rules (NIJE moguće preko `ci.yml` — GitHub Actions ne može da menja branch rules; mora preko GitHub UI ili `gh` CLI).

Step-by-step GitHub UI:
1. Open repo na GitHub-u → `Settings` tab → `Branches` (left sidebar).
2. Click `Add rule` (ili `Add branch protection rule`).
3. **Branch name pattern:** `master`.
4. Check `Require status checks to pass before merging`:
   - Sub-check `Require branches to be up to date before merging` (osigurava da PR ima latest `master`).
   - Status checks to require (search u checkbox listi):
     - `lint` (iz `ci.yml`)
     - `test` (iz `ci.yml`)
     - `build` (iz `ci.yml`)
5. (Opciono) Check `Include administrators` — samo-disciplinujem (Mihas ne može da bypass-uje CI ni kao admin).
6. (Opciono) Check `Require a pull request before merging` — već je default best practice ali ne strict za solo dev.
7. Click `Create` (ili `Save changes`).

**Alternativa kroz `gh` CLI** (off-script, ne deo Story 1.9 AC):
```bash
gh api -X PUT repos/{owner}/{repo}/branches/master/protection \
  -f required_status_checks[strict]=true \
  -f required_status_checks[contexts][]=lint \
  -f required_status_checks[contexts][]=test \
  -f required_status_checks[contexts][]=build
```

**Future Hetzner SSH secrets (NE u Story 1.9):**
- `secrets.HETZNER_SSH_KEY` (private SSH key za deploy na VPS) — dodaje se u Story 9.2.
- `secrets.HETZNER_STAGING_HOST` + `secrets.HETZNER_PROD_HOST` — IP / hostname-ovi VPS-eva, dodaju se u Story 9.2.
- Story 1.9 NE uvodi ove secret-e jer ne postoji `deploy.yml` u Story 1.9 scope-u.

### Project structure alignment (architecture.md linija 540-547)

`.github/workflows/` se uvodi prvi put — tree posle Story 1.9:
```
CORIC_AGRAR/
├── .github/                              (Story 1.9 NEW direktorijum — prvi put)
│   └── workflows/                        (Story 1.9 NEW direktorijum)
│       └── ci.yml                        (Story 1.9 NEW — lint + test + build na svaki push/PR)
├── .pre-commit-config.yaml               (Story 1.9 NEW — ruff + djade hooks za lokalni dev)
├── compose/
│   └── django/Dockerfile                 (Story 1.3 — koristi se u build job)
├── pyproject.toml                        (Story 1.1 — dev deps su SOT za verzije)
├── uv.lock                               (Story 1.1 — cache key za GHA cache)
├── justfile                              (Story 1.1 — opciono dobija precommit-install recept; Task 4 OPCIONALNO)
├── tests/                                (Story 1.1-1.8 — 8 test fajlova per IMP-10; CI pokreće sve)
└── ...
```

`deploy.yml` se NE uvodi u Story 1.9 — to je Story 9.2 (Hetzner deployment skript + SSL).

### Anti-patterns za Story 1.9 (project-context.md § Critical Don't-Miss + CI best practices)

1. **NEMA hardcoded secrets** u `ci.yml` — sve secret reference idu kroz `${{ secrets.NAME }}` ili `${{ github.token }}`.
2. **NEMA `@latest` ili `@main`** u action references — uvek `@vN` major pinning (security: `@latest` može dobiti rogue update).
3. **NEMA `continue-on-error: true`** u Story 1.9 (IMP-IT2-1 — `manage.py check --deploy` step koji je ranije imao `continue-on-error: true` je UKLONJEN). Fail mora fail-ovati glasno. `check --deploy` step se vraca u Story 9.6 SA `continue-on-error: false` nakon prelaska na settings.production.
4. **NEMA `--no-verify`** pre-commit bypass — ovo nije forbidden u Story 1.9 fajlovima per se, ali project-context.md § Anti-pattern eksplicitno zabranjuje (Mihas se obavezuje).
5. **NEMA `pip install`** u CI — sve preko `uv` (matches project standard).
6. **NEMA Docker container test runtime** u Story 1.9 — `uv` venv na runner-u (Decision D1).
7. **NEMA push image-a u GHCR** u Story 1.9 — push je deferred do Story 9.2 (Decision: out-of-scope).
8. **NEMA `staging` ili `main` branch triggers** u `ci.yml` u Story 1.9 — ti branch-evi NE postoje u Epic 1; dodavaju se u Story 9.2.
9. **NEMA verzija drift** između `pyproject.toml` i `.pre-commit-config.yaml` `rev:` polja — Mihas manualno proverava sync (Decision D8).
10. **NEMA cyrillic karaktera** bilo gde u novim CI/config fajlovima (sve latinica, per project-context.md).

### Performance & sigurnost must-haves

- **CI workflow run time target:** <3 min za clean cache, <90s za cached uv deps. Ako prelazi 3 min, optimizovati cache strategy.
- **Free tier budget:** GitHub Actions free tier je 2000 min/mo. Sa ~3 push-ova dnevno × ~90s avg = ~135s × 30 = ~67.5 min/mo. Velika margina (~30× ispod limit-a).
- **Token scope minimalizam:** `permissions: contents: read, packages: write` (NE `write-all` koji bi dao excess scope).
- **Action source verification:** sve action-i iz `actions/`, `astral-sh/`, `docker/` namespace-a (oficijelni); NEMA fork-ova.
- **Cache poisoning mitigation:** `cache-dependency-glob: "uv.lock"` osigurava da cache se invalidira kad `uv.lock` se menja — sprečava stale cache attack vector.

### Acceptable scope deviations

- **Task 4 (justfile precommit-install recept):** OPCIONALAN gold-plate. Acceptable za Dev da preskoči ako preferira da Mihas direktno pokreće `uv run pre-commit install`.
- **~~Branch protection rules manual setup (Task 5.6):~~ JESTE DoD BLOCKER (IMP-7).** Story 1.9 NIJE done bez branch protection setup-a — bez njega nista ne zaustavlja merge crvene PR-eve, što obesmišljava ceo CI gate. Story 9.2 može refine to dalje (npr. dodati require PR reviews, signed commits), ali Story 1.9 minimum (require status checks: lint, test, build) je strict requirement.
- **Reusable workflow / composite action za `uv sync` dedup:** OUT-OF-SCOPE (Decision D5). Možda u budućnosti kad CI ima 5+ workflow fajlova sa istim uv sync pattern-om.
- **IMP-12 (UPDATED iter-2) — djade scope expansion za Epic 2+ (djade scope evolution path):**
  - **Current Story 1.9 v1:** ci.yml koristi `uv run djade --check templates/partials/*.html` (flat glob; NE hvata nested `templates/partials/*/` sub-direktorijume, NE hvata `templates/base.html`, NE hvata `apps/*/templates/`).
  - **Story 2.1+ MORA preci na file-listing pattern:** `git ls-files '*.html' | xargs -r uv run djade --check` (Unix shell, `ubuntu-latest` GHA runner) — hvata sve `.html` fajlove u repo-u, uključujući `apps/*/templates/` i nested sub-partials. Ovaj pattern je portabilan na sve buduće template lokacije bez dodatnih izmena u `ci.yml`.
  - **base.html cleanup (Decision D14) — REQUIRED pre Story 2.1:** Pre prelaska na `git ls-files` pattern (koji hvata base.html), Mihas mora izabrati: (a) **PREPORUČENO** — restruktuirati `templates/base.html` da ima 1 konsolidovan `{% load %}` line (format koji djade 1.9.0 generiše), ili (b) update Story 1.5/1.6/1.7 test asercije u `tests/test_base_template.py` da prihvate djade consolidated format. Opcija (a) je preporučena jer test izmena bi učinila testove labavije; restruktuiranje base.html-a je 1-time fix.
  - **Alternative Windows-friendly pattern (ako buduca story koristi Windows runner):** Python helper script `tools/lint_templates.py` koji koristi `glob.glob('**/*.html', recursive=True)` i prosleđuje listu fajlova djade-u. Story 1.9 ne uvodi ovaj pattern jer GHA runner je `ubuntu-latest` (Unix shell dovoljan).
  - **Story 1.9 NE adresira ovo direktno** jer `apps/*/templates/` direktorijumi NE postoje u Epic 1 (proverava `tree apps/` koji vraca samo `apps/core/` bez `templates/` subdir-a). Cleanup contract je preliven na Story 2.1 ili na dedicated tech-debt story pre Story 2.1.
- **YAML linting:** OUT-OF-SCOPE (Decision D9). GitHub Actions parser je dovoljan za v1.
- **Multi-Python matrix testing:** OUT-OF-SCOPE. Projekat pin-uje Python 3.13 (pyproject.toml `requires-python = ">=3.13"`); nije relevantno testirati 3.10/3.11/3.12 jer dep matrix ne podržava.
- **Story 9.2 evolution path (ARCH #6 iter-1):** Story 9.2 (Hetzner deployment + SSL) kreira SEPARATAN `.github/workflows/deploy.yml` per `architecture.md` linija 547; NEĆE modifikovati `ci.yml` build job (cache scope per-workflow je acceptable trade-off za jasnu separaciju lifecycle-a). `ci.yml` build job ostaje smoke-test-only (`push: false`) zauvek; push + GHCR login pripadaju `deploy.yml` workflow-u.

### Iter 1 + Iter 2 Code Review Fix Log

**Iter 1 (Step-04 fix iter 1) — fixes:**
- BUG-1/4: ruff F541 cleanup (`uv run ruff check --fix .` + `ruff format .`) — 28 fixable + 1 F405 (`config/settings/production.py` got explicit `from .base import env`). Side effect: ~20 source files reformatted by ruff format (mechanical: line wrapping, quote style). Semantic test changes: `tests/test_bootstrap.py` and `tests/test_static_tokens.py` `forbidden` lists emptied with NAPOMENA — same pattern as prior Story 1.2/1.3/1.4/1.5 amendments.
- BUG-2: djade scope changed from `templates/` to `templates/partials/*.html` (djade 1.9.0 does NOT accept directory arg — verified).
- BUG-3: `templates/partials/header.html` reverted to master, then djade auto-formatted (legitimate Story 1.9 cleanup).
- BUG-4: `templates/partials/footer.html` djade auto-formatted.
- ARCH-5: Added version pin audit trail block with 2026-05-29 verification dates.
- ARCH-6: Added Story 9.2 evolution path bullet (deploy.yml separate from ci.yml).
- REFACTOR-8/11: pre-commit-config got `default_language_version: python3.13`, `default_stages: [pre-commit]`, exclude regex.
- REFACTOR-9: IMAGE_NAME shell refactored to env mapping + `${REPO,,}` (defense-in-depth per Security MEDIUM finding).
- REFACTOR-10: All `name: Checkout` → `name: Checkout repo` for consistency.
- Side effect unresolved: base.html djade exclusion (see Decision D14 + IMP-12).
- Side effect unresolved: 2 pre-existing test failures in `tests/test_base_template.py` (Story 1.7/1.8 vendor + main.css drift) — confirmed NOT Story 1.9 regression via git stash verification.

**Iter 2 (Step-04 fix iter 2) — fixes:**
- BUG-1: pre-commit exclude regex corrected from `^(static/vendor/|locale/.*\.mo)$` to `^(static/vendor/.*|locale/.*\.mo)$` (was not matching files INSIDE vendor dir; empirically confirmed by Dev Reviewer B).
- ARCH-1: IMP-12 hand-off updated with concrete `git ls-files '*.html' | xargs -r uv run djade --check` pattern for Epic 2+ (replaced stale "directory args" assumption).
- REFACTOR-1: AC2 narrative synced with actual ci.yml impl (`templates/partials/*.html` not `templates/`) + clarification re: base.html exclusion. All 9 occurrences of `djade --check templates/` u Dev Notes/Tasks/DoD/Meta-test sync-ovani.
- REFACTOR-2: Skeleton predlog action versions updated to match actual implementation (`actions/checkout@v6`, `astral-sh/setup-uv@v8`, `docker/setup-buildx-action@v4`, `docker/build-push-action@v7`) sa "Verified 2026-05-29" comment-om. `.pre-commit-config.yaml` skeleton dobio defaults block + exclude regex sync.
- REFACTOR-3: Hardkoderani konstanti tabela updated — `PRE_COMMIT_HOOKS_REV = v6.0.0`, `RUFF_PRE_COMMIT_REV = v0.15.15`, `DJADE_PRE_COMMIT_REV = 1.9.0`, `ACTIONS_CHECKOUT_PIN = @v6`, `SETUP_UV_PIN = @v8`, `SETUP_BUILDX_PIN = @v4`, `BUILD_PUSH_ACTION_PIN = @v7`.
- TEST_GAP-1: Decision D14 added (base.html exclusion contract — audit trail).
- TEST_GAP-2: This Iter 1 + Iter 2 fix log section added (audit completeness).
- TEST_GAP-3: AC8 framing — explicit pre-existing failures acknowledgment + Task 5.6 pre-step za rešavanje `tests/test_base_template.py` failures-a pre branch protection enable-ovanja.
- **Optional REFACTOR (deferred):** `justfile` line 45 (`uv run djade --check templates/`) + `architecture.md` line 853 reference. Decision: leave as-is jer (1) `justfile` je local developer convenience i njegov `|| echo` fallback je benigan; (2) `architecture.md` je planning artifact, ne CI source of truth. Mihas mora pre branch protection enable-ovanja ili (a) sync-ovati justfile na `templates/partials/*.html`, ili (b) prihvatiti da lokalni `just lint` može hvatati base.html problem koji CI ne hvata (defense-in-depth). Trenutni `just lint` recept koristi `|| echo` fallback što znači da NE pada — Mihas može run-ovati pre commit-a bez problema.



Story 1.9 koristi sledeće hardkoderane vrednosti u CI workflow-u koje treba znati:

| Naziv | Vrednost | Lokacija | Rationale | Verified on date (CRIT-4) |
|---|---|---|---|---|
| `RUNNER_OS` | `ubuntu-latest` | `ci.yml` sva tri job-a | Standardni izbor za GHA; 24.04 LTS u 2026 | 2026-05-29 |
| `PYTHON_VERSION` | `3.13` | `ci.yml` setup-uv `python-version` (IMP-9) | Matches `pyproject.toml` `requires-python = ">=3.13"` | 2026-05-29 |
| `RUFF_PRE_COMMIT_REV` | `v0.15.15` | `.pre-commit-config.yaml` `rev:` (ruff-pre-commit) | Mora matchovati `pyproject.toml` `ruff>=0.15.14` (Decision D8); iter-2: tabela sync sa stvarnom impl | 2026-05-29 |
| `DJADE_PRE_COMMIT_REV` | `1.9.0` | `.pre-commit-config.yaml` `rev:` (djade-pre-commit) | Mora matchovati `pyproject.toml` `djade>=1.9.0` (Decision D8) | 2026-05-29 |
| `PRE_COMMIT_HOOKS_REV` | `v6.0.0` | `.pre-commit-config.yaml` `rev:` (pre-commit-hooks repo, IMP-5) | Iter-1 Dev verified latest stable major na GitHub Releases (bilo v4.6.0 MINIMUM u spec-u) | 2026-05-29 |
| `DJADE_TARGET_VERSION` | `5.2` | `.pre-commit-config.yaml` `djade` hook args | Matches `pyproject.toml` `django>=5.2,<6.0` | 2026-05-29 |
| `GHCR_REGISTRY` | `ghcr.io` | `ci.yml` build job tag template | Oficijelan GitHub Container Registry namespace (Story 9.2 push) | 2026-05-29 |
| `ACTIONS_CHECKOUT_PIN` | `@v6` | `ci.yml` sva tri job-a | Iter-1 Dev verified latest stable major (bilo @v4 MINIMUM u spec-u) | 2026-05-29 |
| `SETUP_UV_PIN` | `@v8` | `ci.yml` lint + test job-ovi | Iter-1 Dev verified latest stable major (bilo @v3 MINIMUM u spec-u) | 2026-05-29 |
| `SETUP_BUILDX_PIN` | `@v4` | `ci.yml` build job | Iter-1 Dev verified latest stable major (bilo @v3 MINIMUM u spec-u) | 2026-05-29 |
| `BUILD_PUSH_ACTION_PIN` | `@v7` | `ci.yml` build job | Iter-1 Dev verified latest stable major (bilo @v6 MINIMUM u spec-u; v7 podržava GHA cache) | 2026-05-29 |

**NAPOMENA (CRIT-4):** Verzije ispod su MINIMUM acceptable na datum 2026-05-29. Pre commit-a, Dev MORA verifikovati current latest stable major na `https://github.com/<owner>/<action>/releases` za svaku action (npr. `astral-sh/setup-uv`, `docker/build-push-action`, `actions/checkout`). Ako je major verzija viša u trenutku implementacije, koristiti najnoviji stable major. Pin format: `@v<MAJOR>` (NE `@latest`, NE `@main`). `LOGIN_ACTION_VERSION` UKLONJEN iz tabele jer GHCR login je deferred do Story 9.2 (IMP-6).

**Audit trail (2026-05-29 Dev verification — ARCH #5 iter-1):**
- `actions/checkout@v6` — current stable major per https://github.com/actions/checkout/releases (bilo @v4 minimum u spec-u)
- `astral-sh/setup-uv@v8` — current stable major per https://github.com/astral-sh/setup-uv/releases (bilo @v3 minimum u spec-u)
- `docker/setup-buildx-action@v4` — current stable major per https://github.com/docker/setup-buildx-action/releases (bilo @v3 minimum u spec-u)
- `docker/build-push-action@v7` — current stable major per https://github.com/docker/build-push-action/releases (bilo @v6 minimum u spec-u)
- `pre-commit/pre-commit-hooks v6.0.0` — current stable per releases (bilo v4.6.0 minimum u spec-u)
- `astral-sh/ruff-pre-commit v0.15.15` — matches `pyproject.toml ruff>=0.15.14`
- `adamchainz/djade-pre-commit 1.9.0` — matches `pyproject.toml djade>=1.9.0`

### `ci.yml` — pun skelet predlog (Dev može da kopira i adaptira)

NAPOMENA: action verzije ispod su MINIMUM acceptable per AC9 + CRIT-4; pre commit-a Dev MORA verifikovati current latest stable major na GitHub Releases page-u (https://github.com/<owner>/<action>/releases) i koristiti najnoviji stable major ako postoji.

```yaml
name: CI

on:
  push:
    branches: [master]
  pull_request:
    branches: [master]
  workflow_dispatch:  # IMP-IT2-4: Manual run iz Actions UI — pre-merge dry-run i debugging

# Workflow-level: contents: read (svi job-ovi rade checkout); packages: write je JOB-LEVEL na build only (IMP-1)
permissions:
  contents: read

# Sprecava paralelne CI run-ove za isti branch (IMP-3)
concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

jobs:
  lint:
    runs-on: ubuntu-latest
    timeout-minutes: 10  # IMP-4
    env:
      # CRIT-2 + Gotcha CI-1: defensive insurance (djade je standalone parser ali buduce promene
      # mogu uvesti Django settings load; 0-cost da postoji).
      DJANGO_SECRET_KEY: ci-test-secret-key-not-for-prod-50chars-padding
    steps:
      - name: Checkout
        uses: actions/checkout@v6  # Verified 2026-05-29 — latest stable major per Decision D2

      - name: Setup uv
        uses: astral-sh/setup-uv@v8  # Verified 2026-05-29 — latest stable major per Decision D2
        with:
          python-version: '3.13'  # IMP-9
          enable-cache: true
          cache-dependency-glob: "uv.lock"

      - name: Install dev deps
        run: uv sync --frozen --group dev

      - name: Ruff check
        run: uv run ruff check .

      - name: Djade check
        run: uv run djade --check templates/partials/*.html  # iter-2 sync; base.html izuzet per D14

  test:
    runs-on: ubuntu-latest
    timeout-minutes: 10  # IMP-4
    env:
      # CRIT-1 + Gotcha CI-1: bez DJANGO_SECRET_KEY env, pytest-django ucitava settings
      # → ImproperlyConfigured exception pre nego pytest collect-uje testove.
      DJANGO_SECRET_KEY: ci-test-secret-key-not-for-prod-50chars-padding
      # DATABASE_URL not set — base.py default sqlite:///db.sqlite3 (see Gotcha CI-7)
      # CRIT-IT2-1: namerno NEMA DATABASE_URL; base.py:78 default-uje na SQLite.
    steps:
      - name: Checkout
        uses: actions/checkout@v6  # Verified 2026-05-29 — latest stable major per Decision D2

      - name: Setup uv
        uses: astral-sh/setup-uv@v8  # Verified 2026-05-29 — latest stable major per Decision D2
        with:
          python-version: '3.13'
          enable-cache: true
          cache-dependency-glob: "uv.lock"

      - name: Install dev deps
        run: uv sync --frozen --group dev

      # IMP-IT2-1: "Django deploy checks" step UKLONJEN — settings.development namerno ima
      # DEBUG=True; continue-on-error: true bi učinio step placebo. Vidi Decision D13.
      # Story 9.6 dodaje check --deploy nakon prelaska na settings.production.

      - name: Pytest
        run: uv run pytest

  build:
    runs-on: ubuntu-latest
    timeout-minutes: 15  # IMP-4
    needs: [lint, test]
    permissions:
      packages: write  # IMP-1: job-level; placeholder za Story 9.2 GHCR push
    steps:
      - name: Checkout
        uses: actions/checkout@v6  # Verified 2026-05-29 — latest stable major per Decision D2

      - name: Setup Docker Buildx
        uses: docker/setup-buildx-action@v4  # Verified 2026-05-29 — latest stable major per Decision D2

      - name: Set lowercase image name
        # IMP-2 + Gotcha CI-2: GHCR zahteva lowercase namespace; ${{ github.repository }} moze biti mixed case
        # REFACTOR #9 (iter-1): env mapping + ${REPO,,} bash 4+ param expansion (defense-in-depth
        # vs shell-injection surface kod direktnog ${{ ... }} expansion-a).
        env:
          REPO: ${{ github.repository }}
        run: echo "IMAGE_NAME=${REPO,,}" >> $GITHUB_ENV

      # IMP-6: NEMA docker/login-action — login deferred do Story 9.2.
      # Story 1.9 build job samo verifikuje da Dockerfile builduje bez sintaksne greske.

      - name: Docker build (no push — Story 1.9 smoke test)
        uses: docker/build-push-action@v7  # Verified 2026-05-29 — latest stable major per Decision D2
        with:
          context: .
          file: ./compose/django/Dockerfile
          push: false
          tags: ghcr.io/${{ env.IMAGE_NAME }}:ci-${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

### `.pre-commit-config.yaml` — pun skelet predlog

```yaml
# .pre-commit-config.yaml
# Pokrece se lokalno na svaki commit (posle `pre-commit install` setup-a)
# CI lint job (.github/workflows/ci.yml) pokrece iste lint komande — fail lokalno = fail u CI
# NAPOMENA (Decision D11): pytest se NAMERNO ne pokreće u pre-commit-u — pytest je CI-only gate.
# Verzija sync sa pyproject.toml [dependency-groups.dev] — Decision D8

# REFACTOR #8 (iter-1): defaults eksplicitno — python3.13 matchuje pyproject requires-python;
# default_stages [pre-commit] osigurava da se hooks ne pokrecu na push/merge stage-ima slucajno.
default_language_version:
  python: python3.13

default_stages: [pre-commit]

repos:
  # IMP-5: standardni pre-commit-hooks (baseline higijenski hooks)
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v6.0.0  # Verified 2026-05-29 — latest stable major per Decision D2
    hooks:
      # REFACTOR #11 (iter-1) + BUG-1 (iter-2): exclude vendor JS i compiled .mo binare;
      # `static/vendor/.*` (sa `.*`) — `static/vendor/` bez `.*` match-uje samo dir, ne fajlove.
      - id: trailing-whitespace
        exclude: '^(static/vendor/.*|locale/.*\.mo)$'
      - id: end-of-file-fixer
        exclude: '^(static/vendor/.*|locale/.*\.mo)$'
      - id: check-yaml
      - id: check-merge-conflict

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.15  # Verified 2026-05-29 — matches pyproject.toml ruff>=0.15.14
    hooks:
      - id: ruff-check
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/adamchainz/djade-pre-commit
    rev: 1.9.0  # Verified 2026-05-29 — matches pyproject.toml djade>=1.9.0
    hooks:
      - id: djade
        args: [--target-version, "5.2"]
```

### Acceptable Behavior — CI flakiness (very low risk u Story 1.9)

Story 1.9 CI workflow je deterministički — bez network calls van GHA cache + Docker base images + pre-commit hook repos. Flakiness risk je minimalan, ali sledeće edge cases-ove može Dev encounter:

- **GHA cache miss u prvih nekoliko run-ova:** Očekivano dok cache nije primarno populated. Posle ~3-5 push-ova, cache hit ratio dostiže ~95%.
- **Docker Hub rate limit za base image pull:** `python:3.13-slim` i `ghcr.io/astral-sh/uv:python3.13-bookworm-slim` se pull-uju kroz Docker Buildx. GitHub Actions runner-i imaju anonymous rate limit od ~100 pulls/6h (kroz shared IP), retko hit-uje za solo dev workflow.
- **pre-commit hook repo cache miss:** Prvi run `pre-commit run` posle `install` clone-uje hook repos (`ruff-pre-commit`, `djade-pre-commit`) — ~5-10s overhead. Subsequent run-ovi su instant.

Bez retry logic-e u Story 1.9 v1 — flakiness se rešava re-run-om job-a kroz GitHub UI manually.

## Definition of Done

- [ ] `.github/workflows/ci.yml` postoji i prolazi YAML sintaksu (GitHub UI ne prijavi "workflow file invalid").
- [ ] `.pre-commit-config.yaml` postoji i prolazi `uv run pre-commit run --all-files` lokalno (green ili samo fixable issues).
- [ ] Sva tri CI job-a (`lint`, `test`, `build`) prikazuju green status na sample PR-u (Task 5.3 verifikacija):
  - `lint`: `uv run ruff check .` + `uv run djade --check templates/partials/*.html` prolazi (iter-2 sync; base.html izuzet per D14).
  - `test`: `uv run pytest` prolazi (svi Story 1.1-1.8 testovi — trenutno 8 fajlova per IMP-10 — su regression-safe).
  - `build`: `docker build` kroz buildx prolazi (NEMA GHCR login per IMP-6 — login + push deferred do Story 9.2).
- [ ] Sample PR ka `master` blokira merge kad CI je crveno (verifikacija manual: pošalji namerno broken commit, CI postaje crveno, "Merge pull request" dugme je disabled — POSLE branch protection setup-a u Task 5.6). **Polish-D napomena:** Ova verifikacija počinje od Story 2.1 PR-a, NE Story 1.9 PR-a, per Decision D12 — D12 dokumentuje da je Story 1.9 PR vlastiti prvi post-merge push (`pull_request` trigger ne radi za workflow fajl koji nije u default branch-u), ne pull_request CI.
- [ ] **Branch protection rules postavljene za `master`** (IMP-7 — DoD BLOCKER): Require status checks: `lint`, `test`, `build` — verifikovano kroz `gh api repos/<owner>/<repo>/branches/master/protection` (output mora pokazati `required_status_checks.contexts: [lint, test, build]`) ILI GitHub UI screenshot. Bez ovog DoD checklist stavka NIJE done.
- [ ] Verzija pinning sync između `pyproject.toml` `[dependency-groups.dev]` i `.pre-commit-config.yaml` `rev:` polja je verifikovan (Decision D8).
- [ ] Dev Notes sekcije "Lokalni pre-commit install workflow", "CI debugging steps", "GHCR + Secrets Management" su kompletne u ovoj story-ji.
- [ ] Story 1.9 lokalno: `uv run ruff check .` (green), `uv run djade --check templates/partials/*.html` (green; iter-2 sync), `uv run pytest` (green) — isti standard koji CI proverava.
- [ ] (Opcionalno) `just precommit-install` recept u `justfile` (Task 4 — gold-plate, ne blocker).
- [ ] sprint-status.yaml: `1-9-github-actions-ci-pipeline` postavlja se na `done` posle merge-a Story 1.9 + green CI run + branch protection setup (manual u GitHub UI).
- [ ] Epic 1 retrospective: optional → može da se pokrene (epic-1-retrospective u sprint-status.yaml).
- [ ] **NEMA cyrillic karaktera** u novim CI / config fajlovima (regression — vidi Story 1.7 + 1.8 testovi za pattern).
- [ ] **NEMA hardcoded secrets** u `ci.yml` — sve preko `${{ secrets.* }}` ili `${{ github.token }}`.

## Testing

### Test framework

Story 1.9 je **infra-only** — NEMA novi Python kod, NEMA novi Django app, NEMA novi template ili CSS. Tradicionalni `pytest` test fajl NIJE potreban (CI workflow se testira **kroz svoj sopstveni run** — meta-test).

Postojeći test framework (`pytest` + `pytest-django`, već konfigurisan u Story 1.1) MORA prolaziti CI test job — to je verifikacija da Story 1.9 nije regrediram Story 1.1-1.8.

### Meta-test scenariji (kako se Story 1.9 verifikuje)

1. **YAML sintaksa `ci.yml` je valid:** GitHub UI pri prvom push-u prijavi "workflow file invalid" ako YAML nije ispravan. Test = "workflow se appears u Actions tab-u".
2. **Sva tri job-a se pokreću na post-merge push** (Decision D12): Task 5.3 manual verifikacija — GitHub Actions UI pokazuje 3 paralelna job-a (lint, test) + sequential build job posle.
3. **Lint job zelena:** `uv run ruff check .` + `uv run djade --check templates/partials/*.html` prolaze (iter-2 sync; base.html izuzet per D14). Verifikuje da Story 1.1-1.8 fajlovi su clean. `env: DJANGO_SECRET_KEY` postavljen per CRIT-2.
4. **Test job zelena:** `uv run pytest` prolazi. Verifikuje da Story 1.1-1.8 testovi (trenutno 8 fajlova per IMP-10) nisu regrediram. `env: DJANGO_SECRET_KEY` postavljen per CRIT-1; `DATABASE_URL` NIJE postavljen (CRIT-IT2-1 — `base.py:78` default-uje na SQLite). `manage.py check --deploy` step UKLONJEN (IMP-IT2-1 — vidi D13).
5. **Build job zelena:** `docker build` kroz buildx prolazi. Verifikuje da `compose/django/Dockerfile` je build-able u clean GHA runner environment-u. NEMA GHCR login (deferred do Story 9.2 per IMP-6).
6. **IMAGE_NAME lowercase transformation:** `build` job "Set lowercase image name" step prikazuje lowercase `IMAGE_NAME` env (per IMP-2 + Gotcha CI-2). Verifikuje AC4 Step 3.
7. **Pre-commit hooks pokreću se lokalno:** `uv run pre-commit run --all-files` prolazi (ili samo `--fix`-uje fixable issues). Verifikuje AC6 (sa std hooks + ruff + djade per IMP-5).
8. **Pre-commit hook se attachuje na `.git/hooks/pre-commit`:** Posle `uv run pre-commit install`, fajl `.git/hooks/pre-commit` postoji i ima shebang `#!/usr/bin/env bash` + pre-commit-run pattern. Verifikuje AC7.
9. **Branch protection setup verifikovan (IMP-7 DoD blocker):** `gh api repos/<owner>/<repo>/branches/master/protection` output mora pokazati `required_status_checks.contexts: [lint, test, build]`. Verifikuje DoD blocker iz Task 5.6.

### Regression scenariji

Story 1.9 NE menja postojeće Python kod, template, CSS, JS — pa NEMA tradicionalnih regression risk-a u Story 1.1-1.8 fajlovima. **Jedina regression mogućnost je da `pre-commit run` lokalno prijavi greške u postojećim fajlovima** (npr. ako Story 1.7 ili 1.8 CSS fajlovi imaju format issue koji `ruff` ili `djade` prijavi posle update-a).

Mitigation: pre Story 1.9 merge-a, pokrenuti `uv run pre-commit run --all-files` lokalno (Task 2.2) i fix-ovati sve issue-e (ako ih ima) kao deo Story 1.9 commit-a.

### Meta-anti-pattern provera (anti-pattern grep scope na NOVE fajlove)

- Grep `\.github/workflows/ci\.yml` na `@latest|@main` — forbidden (Decision: pinned major versions per AC9).
- Grep `\.github/workflows/ci\.yml` na hardcoded `password:` van `${{ secrets.* }}` — forbidden (Decision: sve secrets kroz GHA secret store).
- Grep `\.github/workflows/ci\.yml` na `continue-on-error: true` — forbidden u Story 1.9 (IMP-IT2-1 — jedini step koji je ovo imao, `manage.py check --deploy`, je UKLONJEN; vidi Decision D13).
- Grep `\.pre-commit-config\.yaml` na cyrillic karaktere `[Ѐ-ӿ]` — forbidden (per project-context.md).

### Test scenariji u tradicionalnom smislu (NEMA u Story 1.9)

Story 1.9 NEMA nove `tests/test_*.py` fajlove. Ako Mihas ili Dana odluče da ipak žele "smoke test" da `ci.yml` postoji + `.pre-commit-config.yaml` postoji, Story 1.9 acceptable scope deviation dozvoljava dodavanje optional `tests/test_ci_workflow_config.py`:

```python
# OPCIONI smoke test — NIJE u AC, ali Dev može da doda za extra confidence
from pathlib import Path


def test_ci_workflow_yaml_exists():
    """AC1 regression — .github/workflows/ci.yml mora postojati."""
    assert Path(".github/workflows/ci.yml").exists()


def test_pre_commit_config_exists():
    """AC6 regression — .pre-commit-config.yaml mora postojati u repo root-u."""
    assert Path(".pre-commit-config.yaml").exists()


def test_ci_yml_defines_three_jobs():
    """AC1 regression — ci.yml mora imati lint, test, build job-ove."""
    content = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "jobs:" in content
    assert "lint:" in content
    assert "test:" in content
    assert "build:" in content


def test_pre_commit_config_pins_ruff_and_djade():
    """AC6 regression — .pre-commit-config.yaml mora imati ruff i djade hooks."""
    content = Path(".pre-commit-config.yaml").read_text(encoding="utf-8")
    assert "ruff-pre-commit" in content
    assert "djade-pre-commit" in content
```

Ovaj test je OPCIONALAN — Story 1.9 prolazi DoD bez njega (CI workflow je glavni "test"). Acceptable scope deviation za Dev da doda ako želi extra defensiveness.

---

**SM (Scrum Master) sign-off:**
Story 1.9 je infra-only cross-cutting story koji zatvara Epic 1 i postavlja CI gate za sve buduće epics. Pripremljena je sa eksplicitnim decisions log-om (D1-D13; D11 = pre-commit ne pokrece pytest, D12 = prvi CI run je post-merge push + SQLite default iz base.py:78 per CRIT-IT2-1, D13 = `manage.py check --deploy` izostavljen iz v1 CI + `workflow_dispatch` trigger dodat per IMP-IT2-1/IMP-IT2-4), Gotchas sekcijom (CI-1 do CI-8 — CI-7 i CI-8 dodati u Iter 2 za pytest-django + SQLite lazy session i concurrency race), AC pokrivenošću za sva 5 epic spec AC + 4 dodatne AC (testabilnost, dokumentacija, anti-patterns, sample PR verifikacija), i fokus na minimum scope (NO push image-a, NO GHCR login u Story 1.9, NO staging/main branch-evi, NO matrix Python testing — sve to je deferred do Epic 9). Dev može direktno krenuti sa implementacijom — sva CI tooling odluke (uv venv vs Docker, GHCR token strategija, cache strategija, env vars za DJANGO_SECRET_KEY samo, lowercase IMAGE_NAME, concurrency, timeout-minutes, branch protection DoD blocker, workflow_dispatch dry-run opcija) su rešene u Dev Notes Decisions log-u + Gotchas sekciji.
