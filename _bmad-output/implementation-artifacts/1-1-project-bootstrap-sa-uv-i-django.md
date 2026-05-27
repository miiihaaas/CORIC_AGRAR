---
story-id: "1.1"
story-key: 1-1-project-bootstrap-sa-uv-i-django
title: Project Bootstrap sa uv i Django
status: ready-for-dev
epic_num: 1
epic_title: Project Foundation & Visual Identity
created: 2026-05-27
author: Mihas (SM autonomous)
---

# Story 1.1: Project Bootstrap sa uv i Django

Status: ready-for-dev

<!-- Validacija je opcionalna. Pre dev-story koraka možeš pokrenuti validate-create-story za quality check. -->

## Story

As a **dev (Mihas)**,
I want **inicijalan Python/Django projekat sa pravom strukturom direktorijuma, uv paket menadžerom i osnovnim task runner setup-om**,
so that **mogu da krenem sa razvojem ostalih story-ja na čvrstoj osnovi koja prati arhitektonske odluke iz Architecture dokumenta**.

## Acceptance Criteria

**AC1 — Bootstrap uv projekta**

- **Given** već postojeći git repo direktorijum `C:\Programming\dev-bmad\CORIC_AGRAR\` (sa `.git/`, `.gitignore`, `_bmad-output/`, `_bmad/`, `docs/`, `.claude/`)
- **When** izvršim `uv init --python 3.13 --no-readme` u već postojećem repo direktorijumu (`C:\Programming\dev-bmad\CORIC_AGRAR\`)
- **Then** kreirani su `pyproject.toml`, `.python-version` (pinovan na `3.13`) i `uv.lock` (posle prvog `uv add`)
- **And** `uv --version` i `python --version` (preko `uv run python`) odgovaraju 3.13.x
- **And** `uv --version` reportuje verziju ≥ 0.5 (PEP 735 `[dependency-groups]` zahteva uv 0.5+)

**AC2 — Instalacija core dependency-ja**

- **Given** projekat inicijalizovan kroz AC1
- **When** dodam core deps komandom:
  `uv add "django>=5.2" "psycopg[binary]" django-modeltranslation django-htmx django-template-partials django-bootstrap5 django-environ django-anymail django-ratelimit django-axes django-csp sorl-thumbnail pdf2image python-magic`
- **Then** `pyproject.toml` ima `dependencies = [...]` listu pod `[project]` tabelom (PEP 621 / PEP 735 standard format) i ona sadrži sve gore navedene pakete sa zadovoljenim version constraint-ovima
- **And** `uv.lock` je ažuriran (commitable artefakt)
- **And** `uv pip list` prikazuje Django ≥ 5.2 i sve ostale pakete

**AC3 — Django project skeleton**

- **Given** core deps instalirane kroz AC2
- **When** izvršim `uv run django-admin startproject config .` (NAPOMENA: završni `.` je obavezan — kreira `config/` u root-u, ne u sub-folder-u)
- **Then** struktura sadrži: `manage.py` u root-u i `config/` direktorijum sa `__init__.py`, `settings.py`, `urls.py`, `wsgi.py`, `asgi.py`
- **And** `uv run python manage.py check` izvršava se bez grešaka (exit code 0, output: `System check identified no issues (0 silenced).`)
- **And** `uv run python manage.py --version` štampa Django ≥ 5.2.x

**AC4 — Dev dependency grupa**

- **Given** projekat iz AC3
- **When** dodam dev deps komandom:
  `uv add --dev pytest pytest-django ruff djade pre-commit playwright django-debug-toolbar`
- **Then** `pyproject.toml` ima `[dependency-groups]` tabelu (PEP 735 standard — pošto je `uv ≥ 0.5` zahtev, ovo je deterministički očekivani format; NE `[tool.uv.dev-dependencies]` legacy) sa `dev = [...]` koji sadrži svih 7 paketa
- **And** `uv run pytest --version` i `uv run ruff --version` izvršavaju se bez grešaka
- **And** glavna `dependencies` lista NE sadrži dev pakete (čisto razdvojeni)

**AC5 — justfile sa task runner receptima**

- **Given** projekat iz AC4
- **When** kreiram `justfile` u root-u projekta
- **Then** `justfile` sadrži najmanje sledeće recepte (vidi Dev Notes za sample sadržaj):
  - `dev` — pokreće lokalni development server (placeholder za sada: `uv run python manage.py runserver` ili docker compose komanda koja će biti kompletirana u Story 1.3)
  - `test` — pokreće test suite: `uv run pytest`
  - `lint` — pokreće linter i template formatter: `uv run ruff check . && uv run djade --check templates/`
  - `migrate` — applies DB migrations: `uv run python manage.py migrate`
  - `messages` — i18n message handling: `uv run python manage.py makemessages -a && uv run python manage.py compilemessages`
- **And** `just --list` (ako je `just` instaliran lokalno) prikazuje sve recepte; ALTERNATIVNO `cat justfile` mora prikazati sve recepte čitljivo
- **And** justfile koristi `set shell := ["bash", "-c"]` (ili Windows-compatible alternativu — vidi Dev Notes) tako da recepti rade konzistentno

**AC6 — Repo hygiene fajlovi**

- **Given** sva prethodna AC su pokrivena
- **When** komitujem prvu verziju projekta
- **Then** postoje sledeći fajlovi sa razumnim default sadržajem:
  - `.gitignore` (uključujući `__pycache__/`, `*.pyc`, `.env`, `.venv/`, `db.sqlite3`, `staticfiles/`, `media/`, `.pytest_cache/`, `.ruff_cache/`, `.playwright/`)
  - `.python-version` čiji sadržaj **počinje sa `3.13`** (može biti `3.13`, `3.13.0`, `3.13.1`, itd. — tačan format zavisi od `uv` verzije; bitno je da major.minor odgovaraju)
  - `README.md` (minimalni — naziv projekta + jedan paragraf opisa + odeljak Quickstart sa komandama `uv sync` i `uv run python manage.py runserver`)
- **And** `.env` fajl (ako postoji) NIJE komitovan (samo `.env.example` smatra se OK ali nije obavezan u ovoj story-ji — pokriva ga Story 1.2)
- **And** `.gitignore` i dalje sadrži BMad carve-out pravila (`_bmad/bmm/`, `.claude/skills/`, `docs/Dizajn/`, `bmad-orchestrators-bundle/`) nakon `uv init`-a (vidi Task 0)

## Tasks / Subtasks

- [ ] **Task 0: Preservation of existing .gitignore** (AC: 6 — preservation bullet)
  - [ ] 0.1 Project root `C:\Programming\dev-bmad\CORIC_AGRAR\` već ima working `.gitignore` (committed u initial commit) sa BMad installer carve-out pravilima i `docs/Dizajn/` exclude (1.3 GB design assets zavise od ovog pravila). Pre bilo kakvog `uv init` koraka, backup-uj: `cp .gitignore .gitignore.bmad-baseline`
  - [ ] 0.2 Zapamti / proveri baseline pravila (BMad installer carve-outs, `_bmad/bmm/`, `.claude/skills/`, `bmad-orchestrators-bundle/`, `docs/Dizajn/`, design assets exclude)
  - [ ] 0.3 NAPOMENA: `uv init` može da kreira novi `.gitignore` ili da ga overwrite-uje. Posle `uv init` koraka (Task 1.3), MORAŠ verifikovati da BMad pravila i dalje postoje (vidi Task 6.1 — verifikacija nakon `uv init`)
  - [ ] 0.4 Ako `uv init` overwrite-uje `.gitignore`, opcije za recovery: (a) `git checkout .gitignore` da vratiš committed baseline, ili (b) merge BMad pravila iz `.gitignore.bmad-baseline` nazad u novi `.gitignore`

- [ ] **Task 1: Pripremi radni direktorijum i pokreni uv init** (AC: 1)
  - [ ] 1.1 Verifikuj da je `uv` instaliran lokalno i da je verzija **≥ 0.5** (`uv --version` mora reportovati ≥ 0.5, jer od te verzije postoji deterministička podrška za `[dependency-groups]` per PEP 735). Ako nije instaliran ili je starija verzija, instaliraj/upgrade-uj. Windows instalacione opcije: `winget install --id=astral-sh.uv -e` (Windows package manager) ili PowerShell jednolinijaš: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`. Za ostale platforme: vidi https://docs.astral.sh/uv/getting-started/installation/
  - [ ] 1.2 Verifikuj da je Python 3.13 dostupan (ili dozvoli `uv` da ga preuzme automatski preko `uv python install 3.13`)
  - [ ] 1.3 Radimo u već-postojećem repo-u: `C:\Programming\dev-bmad\CORIC_AGRAR\` (sa već postojećim `.git/`, `.gitignore`, `_bmad-output/`, `_bmad/`, `docs/`, `.claude/`). U trenutnom cwd-u (root repo-a) pokreni KANONIČNU komandu: `uv init --python 3.13 --no-readme`. Ako naletiš na grešku zbog ne-praznog dir-a, vidi Gotcha #13 za `--bare` fallback. NE koristi varijantu `uv init coric-agrar ...` — ona kreira novi sub-folder i razbija naš već postojeći repo layout. Out-of-scope varijanta (za referencu, NE primenjivati u ovom projektu): `uv init coric-agrar --python 3.13 && cd coric-agrar` — koristi se samo ako se startuje od potpuno praznog parent dir-a.
  - [ ] 1.4 Verifikuj kreirane fajlove: `pyproject.toml`, `.python-version`
  - [ ] 1.5 Obriši automatski generisane placeholder fajlove koje `uv init` kreira (ako postoje) — Django dobija sopstvenu strukturu. Tipični artefakti po verzijama `uv`-a:
    - `main.py` (uv ≥ 0.5 default za application template) — OBRIŠI
    - `hello.py` (older uv default) — OBRIŠI
    - `src/` (samo ako je `--lib` flag korišćen — kod nas NIJE) — ne pojavljuje se
    - `README.md` (uv može da kreira stub) — OK je da ga overwrite-ujemo svojim Task 6.3 sadržajem (overwrite je INTENCIONALAN, ne briši pre 6.3)
    NAPOMENA: Ako koristiš `--no-readme` flag kao u Task 1.3, stub README se ne kreira — onda ga samo Task 6.3 kreira from-scratch.

- [ ] **Task 2: Dodaj core production dependencies** (AC: 2)
  - [ ] 2.1 Izvrši sledeću `uv add` komandu. **Shell quoting napomena:** u PowerShell-u koristi **jednostruke navodnike** oko paketa sa uglastim zagradama (`'psycopg[binary]'`) jer dvostruki navodnici trigeruju expansion. U bash/zsh-u i jedni i drugi navodnici rade.

    **Windows PowerShell (one-liner, preporučeno za naš stack):**
    ```powershell
    uv add 'django>=5.2' 'psycopg[binary]' django-modeltranslation django-htmx django-template-partials django-bootstrap5 django-environ django-anymail django-ratelimit django-axes django-csp sorl-thumbnail pdf2image python-magic
    ```

    **Bash/zsh (Linux/macOS) — backslash continuations OK:**
    ```bash
    uv add "django>=5.2" "psycopg[binary]" django-modeltranslation django-htmx \
           django-template-partials django-bootstrap5 django-environ \
           django-anymail django-ratelimit django-axes django-csp \
           sorl-thumbnail pdf2image python-magic
    ```

    NAPOMENA: bash-style `\` line-continuation NE radi u PowerShell-u — koristi one-liner gore ili backtick (` ` `) continuation ako ti baš treba multi-line u PS.
  - [ ] 2.2 Verifikuj `pyproject.toml` — pod `[project]` tabelom postoji `dependencies = [...]` lista (PEP 621 / PEP 735 standard format) i ona sadrži svih 14 paketa
  - [ ] 2.3 Verifikuj `uv.lock` — fajl postoji, sadrži resolved verzije svih deps
  - [ ] 2.4 Pokreni `uv pip list | grep -i django` (ili `findstr` na Windows) — Django mora biti ≥ 5.2

- [ ] **Task 3: Inicijalizuj Django project skeleton** (AC: 3)
  - [ ] 3.1 Izvrši: `uv run django-admin startproject config .` (završna tačka KRITIČNA — startproject kreira `config/` u trenutnom dir-u umesto u `./config/config/`)
  - [ ] 3.2 Verifikuj strukturu:
    ```
    ./manage.py
    ./config/__init__.py
    ./config/settings.py
    ./config/urls.py
    ./config/wsgi.py
    ./config/asgi.py
    ```
  - [ ] 3.3 Pokreni `uv run python manage.py check` — mora vratiti `System check identified no issues (0 silenced).`
  - [ ] 3.4 Pokreni `uv run python manage.py --version` — output mora biti Django ≥ 5.2.x

- [ ] **Task 4: Dodaj dev dependency grupu** (AC: 4)
  - [ ] 4.1 Izvrši:
    ```bash
    uv add --dev pytest pytest-django ruff djade pre-commit playwright django-debug-toolbar
    ```
    **Napomena:** Eksplicitno dodajemo `pytest` u dev grupu pored `pytest-django` (iako je `pytest` transitive dep `pytest-django`-ja). Razlog: čini nameru jasnom i fiksira `pytest` verziju u `uv.lock` direktno (kao direct dep, ne samo kao zavisnost zavisnosti). Tako se izbegava implicitni downgrade ako `pytest-django` u budućnosti relaks-uje pytest constraint.
  - [ ] 4.2 Verifikuj `pyproject.toml` — `[dependency-groups]` sekcija (PEP 735) sadrži `dev = [...]` sa svih 7 paketa (uz `uv ≥ 0.5` ovo je očekivani format)
  - [ ] 4.3 Verifikuj separaciju: glavna `dependencies` ne sme imati `pytest`, `ruff`, `djade` itd.
  - [ ] 4.4 Pokreni `uv run pytest --version` i `uv run ruff --version` — oba bez grešaka

- [ ] **Task 5: Kreiraj justfile sa task runner receptima** (AC: 5)
  - [ ] 5.1 Kreiraj fajl `justfile` u root-u sa sadržajem iz Dev Notes § justfile Template
  - [ ] 5.2 Verifikuj da su definisani recepti: `dev`, `test`, `lint`, `migrate`, `messages` (+ opciono `default`, `lint-fix`, `shell`)
  - [ ] 5.3 Ako je `just` instaliran lokalno, pokreni `just --list` — mora prikazati sve recepte; ako nije instaliran, pregled `cat justfile` mora čitljivo pokazati recepte
  - [ ] 5.4 NAPOMENA: `dev` recept će biti rewired na `docker compose` u Story 1.3 — za sada pokreće `uv run python manage.py runserver`. To je očekivano i prihvatljivo

- [ ] **Task 6: Repo hygiene fajlovi** (AC: 6)
  - [ ] 6.1 `.gitignore` — VERIFIKACIJA NAKON `uv init`-a: `.gitignore` već postoji (committed BMad baseline). Posle Task 1.3 (`uv init`), proveri da li BMad pravila i dalje postoje: grep za `_bmad/bmm/`, `docs/Dizajn/`, `.claude/skills/`, `bmad-orchestrators-bundle/`. Ako su preživela — OK, samo dodaj nedostajuće Python/Django/uv/IDE pattern-e iz Dev Notes § .gitignore Template (Python `__pycache__/`, `.venv/`, `db.sqlite3`, `media/`, `staticfiles/`, `.pytest_cache/`, `.ruff_cache/`, `.playwright/`, itd.). Ako su nestala (uv ih je overwrite-ovao), vrati ih iz `.gitignore.bmad-baseline` ili `git checkout .gitignore` pa zatim merge-uj Python/Django/uv pravila iznad.
  - [ ] 6.2 Verifikuj postojanje `.python-version` (auto-kreiran kroz `uv init`); sadržaj **počinje sa `3.13`** (može biti `3.13`, `3.13.0`, `3.13.1`, itd. — zavisi od `uv` verzije, sve su prihvatljive)
  - [ ] 6.3 Kreiraj minimalan `README.md` sa: naslov, opis projekta (jedan paragraf — preuzmi iz PRD overview), Quickstart sekcija sa komandama:
    ```
    uv sync
    uv run python manage.py migrate
    uv run python manage.py runserver
    ```
  - [ ] 6.4 Ne kreiraj `.env` — to dolazi u Story 1.2 (django-environ setup). `.env.example` takođe pripada Story 1.2

- [ ] **Task 7: Final validation pre marking-a story-ja kao done** (AC: sve)
  - [ ] 7.1 `uv sync` — mora se izvršiti bez grešaka, kreira `.venv/` i instalira sve deps
  - [ ] 7.2 `uv run python manage.py check` — 0 issues
  - [ ] 7.3 `uv run python manage.py runserver` — Django welcome screen na `http://127.0.0.1:8000/` (manual smoke test; nije zahtev za AC ali korisno za sanity check)
  - [ ] 7.4 `uv run pytest --collect-only` — exit 0 (no tests collected jeste OK; znači pytest-django plugin radi)
  - [ ] 7.5 `uv run ruff check .` — može imati findings (`.gitignore` i sample fajlovi), ali nema crash-a
  - [ ] 7.6 Popuni "File List" i "Completion Notes List" u "Dev Agent Record" sekciji ovog story fajla

## Dev Notes

### Kontekst story-ja

Ovo je **prva implementaciona story u celom projektu**. Cilj je SAMO bootstrap — instalacija paketa i kreiranje skeletona. **NE** rešavamo:

- Multi-environment settings split (`config/settings/base.py` itd.) → Story 1.2
- Docker compose + PostgreSQL kontejneri → Story 1.3
- i18n routing + `LANGUAGES` setting → Story 1.4
- CSS tokens, Roboto fontovi → Story 1.5
- `apps/` direktorijum i Django app-ovi → Epic 2+ (nijedan app se ne kreira u ovoj story)
- `pre-commit` config (`.pre-commit-config.yaml`) → Story 1.9 (CI pipeline)
- GitHub Actions workflows → Story 1.9
- `Dockerfile`, `compose/` → Story 1.3

**Princip:** ako nešto pripada budućoj story-ji, NE radi u ovoj. Drži skopove čistim.

### Tech stack — pinovane verzije i razlozi

Sve odluke su iz [Source: _bmad-output/planning-artifacts/architecture.md § Starter Template Evaluation, lines 80-150]:

| Paket | Min. verzija | Razlog |
|---|---|---|
| Python | 3.13 | Django 5.2 LTS podržava 3.13; type-hint improvements |
| Django | ≥ 5.2 (LTS) | Long-term support do 2028; sveže async views, GeneratedField |
| psycopg | binary extra | Production driver za PostgreSQL (psycopg3, ne psycopg2) |
| django-modeltranslation | latest | i18n model fields sa `_sr`/`_hu`/`_en` suffix-ima |
| django-htmx | latest | HTMX middleware + `request.htmx` introspection |
| django-template-partials | latest | Reusable HTML fragmenti — kritično za HTMX response pattern |
| django-bootstrap5 | latest | Bootstrap 5 template tags za formu rendering |
| django-environ | latest | `.env` parsing (koristi se u Story 1.2) |
| django-anymail | latest | SMTP abstraction (Resend/Brevo) — koristi se u Epic 4 |
| django-ratelimit | latest | Form throttling za NFR-3 (10/15min IP) |
| django-axes | latest | Admin login bruteforce protection (5/15min) |
| django-csp | latest | Content-Security-Policy header |
| sorl-thumbnail | ≥ 12.10 | Image processing + srcset helper (Epic 2 story 2.3) |
| pdf2image | latest | PDF cover-thumbnail render (Epic 2 story 2.4); ZAVISI od poppler sistemskog paketa — instalacija poppler-a pripada Story 1.3 (Dockerfile) i Story 2.4 (eksplicitno) |
| python-magic | latest | MIME type validacija upload-a; na Windows-u zahteva `python-magic-bin` (vidi Gotchas) |

**Dev grupa:**

| Paket | Razlog |
|---|---|
| pytest | Test framework |
| pytest-django | Django integration plugin za pytest |
| ruff | Linter + formatter (zamenjuje black + flake8 + isort) |
| djade | Django template formatter |
| pre-commit | Git hooks runner (konfiguracija u Story 1.9) |
| playwright | E2E testovi (instalacija browsera u Story 9.8) |
| django-debug-toolbar | Dev-only profiling middleware |

### Tačan sled komandi (canonical)

[Source: _bmad-output/planning-artifacts/architecture.md § Implementation Handoff, lines 1024-1046]

```bash
# 1. Init (u trenutnom cwd-u — već postojeći git repo C:\Programming\dev-bmad\CORIC_AGRAR\)
uv init --python 3.13 --no-readme

# 2. Core deps
uv add "django>=5.2" "psycopg[binary]" django-modeltranslation django-htmx \
       django-template-partials django-bootstrap5 django-environ \
       django-anymail django-ratelimit django-axes django-csp \
       sorl-thumbnail pdf2image python-magic

# 3. Django skeleton (završna tačka je obavezna!)
uv run django-admin startproject config .

# 4. Dev deps
uv add --dev pytest pytest-django ruff djade pre-commit playwright \
              django-debug-toolbar

# 5. Smoke test
uv run python manage.py check
```

**Out-of-scope za Story 1.1:** `uv tool install falco-cli` (Architecture step 5 — opcioni global dev helper, Falcon DSL generator) — pomeren u Story 1.9 ili kasnije ako se ikad koristi. Story 1.1 ga preskače. Takođe `playwright install` (browser binaries) — Story 9.8.

### justfile Template

Sledeći sadržaj možeš direktno koristiti kao osnovu. Komande su pisane tako da rade kroz `uv run` (PEP 723 / uv-managed env), bez zavisnosti od ručno aktiviranog `.venv`. Windows korisnici treba da imaju `just` binary u PATH-u (instaliraj kroz `cargo install just` ili `winget install Casey.Just`).

```just
# Default recept — prikazuje listu kad se pokrene `just` bez argumenata
default:
    @just --list

# Pokreće dev server (zameniti docker compose komandom u Story 1.3)
dev:
    uv run python manage.py runserver

# Pokreće test suite
test:
    uv run pytest

# Lint (read-only check, ne menja kod)
lint:
    uv run ruff check .
    uv run djade --check templates/ || echo "djade: templates/ folder ne postoji još (OK za Story 1.1)"

# Apply DB migrations
migrate:
    uv run python manage.py migrate

# i18n message handling
messages:
    uv run python manage.py makemessages -a
    uv run python manage.py compilemessages
```

**Napomena za Windows:** `just` koristi `sh.exe` (Git Bash) ili `cmd.exe` kao default shell na Windows-u. Ako naletiš na probleme sa pipe-ovima (`|`) ili escape sekvencama, dodaj na vrh `justfile`-a:

```just
set windows-shell := ["cmd.exe", "/c"]
```

Ali za ovaj jednostavni set komandi default je sasvim OK.

### .gitignore Template

Minimalna verzija za bootstrap (proširi po potrebi u kasnijim story-jama):

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so

# Virtual environments
.venv/
venv/
env/

# uv
# uv.lock se KOMITUJE — to nije ignore
.uv/

# Django
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal
media/
staticfiles/

# Environment
.env
.env.local
.env.*.local

# IDE
.idea/
.vscode/
*.swp
*.swo
.DS_Store

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/
.playwright/

# Linting
.ruff_cache/
.mypy_cache/

# Build
build/
dist/
*.egg-info/
```

### README.md Template

```markdown
# Ćorić Agrar — Korporativni Sajt

Trojezičan (sr/hu/en) Django sajt za poljoprivredni biznis Ćorić Agrar — katalog brendova/proizvoda, blog "Priče sa polja", lead-gen forme i SEO-spreman public-facing site.

## Tech Stack

- Python 3.13 + Django 5.2 LTS
- PostgreSQL + django-modeltranslation
- HTMX + Bootstrap 5 + django-template-partials
- uv (paket menadžer) + just (task runner)

## Quickstart

\`\`\`bash
# Instaliraj sve dep-ove
uv sync

# Migracije (kad PostgreSQL bude konfigurisan — Story 1.2/1.3)
uv run python manage.py migrate

# Dev server
uv run python manage.py runserver
# ili: just dev
\`\`\`

## Više

Dokumentacija u `_bmad-output/planning-artifacts/`.
```

### Project struktura posle ove story-je

[Source: _bmad-output/planning-artifacts/architecture.md § Complete Project Tree, lines 530-714]

```
coric-agrar/                       # root projekta
├── pyproject.toml                 # NEW — uv-managed
├── uv.lock                        # NEW — auto-generated
├── .python-version                # NEW — počinje sa "3.13" (može biti 3.13, 3.13.0, 3.13.1, ...)
├── .gitignore                     # EXISTING (preserved) — proširen Python/Django/uv pravilima
├── README.md                      # NEW
├── justfile                       # NEW
├── manage.py                      # NEW — Django entry point
└── config/                        # NEW — Django settings root
    ├── __init__.py
    ├── settings.py                # Single-file za sada; biće split u Story 1.2
    ├── urls.py
    ├── wsgi.py
    └── asgi.py
```

**Stvari koje NEĆE postojati posle Story 1.1 (i to je OK):**

- `apps/` folder (kreira se u Epic 2, story 2.1)
- `templates/`, `static/`, `locale/`, `media/`, `compose/` (kasnije story-je)
- `.env`, `.env.example`, `config/settings/` folder (Story 1.2)
- `.pre-commit-config.yaml`, `.github/` (Story 1.9)
- `Dockerfile` (Story 1.3)

### Gotchas / Anti-patterns

0. **Postojeći `.gitignore` (KRITIČNO)** — `uv init` može da kreira ili overwrite-uje `.gitignore` fajl u radnom direktorijumu. Pošto je BMad `.gitignore` već postavljen sa kritičnim pravilima (BMad installer carve-outs `_bmad/bmm/`, `.claude/skills/`, `bmad-orchestrators-bundle/` + `docs/Dizajn/` 1.3 GB design assets exclude), backup-uj ga PRE `uv init`-a (`cp .gitignore .gitignore.bmad-baseline`) i merge-uj BMad pravila nazad ako je `uv init` promenio fajl. Vidi Task 0 za precizne korake. Ako se ova pravila izgube, design assets folder (1.3 GB) može da uđe u git index i razbije repo veličinu.
1. **Završna tačka u `startproject config .`** — bez tačke Django kreira `config/config/settings.py` (nested), što kvari sve buduće settings paths.
2. **`python-magic` na Windows-u** — pure-Python paket zahteva native `libmagic` DLL. Ako razvijaš na Windows i naiđeš na `ImportError: failed to find libmagic` (tipično pri pokretanju `manage.py check` ili kasnijih komandi nakon `uv sync`), dodaj `python-magic-bin` u dev grupu **samo na Windows-u** preko optional dep grupe: `uv add --dev python-magic-bin --optional windows` (ili kao opcioni dep marker). NE menjaj produkcijsku dependency listu (production radi u Linux Docker container-u gde `libmagic` postoji preko `apt-get`). NAPOMENA za Story 1.1: validacija MIME se NE koristi u bootstrap-u (nema file upload-a), pa ovo NIJE blocker za AC; workaround se primenjuje samo ako se desi pri `uv sync` na drugoj mašini. Dokumentuj u Completion Notes ako naletiš.
3. **`pdf2image` poppler dependency** — pdf2image je Python wrapper za `poppler-utils` sistemski paket. NE moraš instalirati poppler za ovu story-ju (sve dok ne pokrećeš `from pdf2image import convert_from_path`); samo `uv add pdf2image` mora proći. Poppler će biti dodat u `compose/django/Dockerfile` u Story 2.4.
4. **`uv.lock` komituj** — `uv.lock` JE deo komita (kao `package-lock.json` u npm svetu). Reproducible builds zavise od njega.
5. **`startproject` ne diraj posle prvog run-a** — u kasnijim story-jama ima šanse da želiš "regenerisati" config; ne radi to. Ručno menjaj `config/settings.py` (i kasnije split).
6. **Ćirilica u kodu zabranjena** — sav kod, naming, komentari moraju biti srpski latinica ili engleski [Source: architecture.md § Implementation Patterns, line 517-518]. README može sadržati latinicu naslov bez problema.
7. **Linter na praznom projektu** — `ruff check .` može da prijavi findings u auto-generated Django fajlovima (`settings.py` ima `SECRET_KEY`, itd.). Za Story 1.1 OK je da `ruff check` ima findings — finalna ruff konfiguracija (line-length 100, naming) dolazi u Story 1.9.
8. **Ne dodaj `apps/` u `INSTALLED_APPS` još uvek** — Story 1.1 zadržava `INSTALLED_APPS` na default Django sadržaju (admin, auth, contenttypes, sessions, messages, staticfiles). Brendovi i ostali app-ovi se dodaju kako se budu kreirali u kasnijim story-jama.
9. **`config/settings.py` NIJE deo dependency-ja modifikacije u Story 1.1** — startproject ga generiše sa defaultima; NE menjaj ga (osim ako test `check` baca grešku — onda potreban je manji tweak; logguj u Completion Notes). Settings reorganizacija je Story 1.2.
10. **Playwright browser binaries NISU u scope-u Story 1.1** — Story 1.1 dodaje `playwright` Python paket u dev grupu, ALI ne pokreće `playwright install` (browser binaries). Browser instalacija je Story 9.8 (E2E setup). Ako `uv run pytest --collect-only` u Task 7.4 padne zbog playwright fixture-a, ignoriši — Story 1.1 nema testova i `--collect-only` exit > 0 zbog playwright-a je acceptable noise (ne blocker).
11. **`falco-cli` je out-of-scope za Story 1.1** — Architecture step 5 spominje `uv tool install falco-cli` (opcioni global dev helper, Falcon DSL generator). Ovo se NE radi u Story 1.1 — pomeren je u Story 1.9 ili kasnije ako se ikad koristi. Story 1.1 ga preskače.
12. **AC2 dep resolution conflict fallback** — Ako `uv add` jedinstvenu komandu padne na dep resolution conflict (npr. između najnovijeg `django-anymail` i `django-csp` zbog Django version constraints), fallback strategija: pinuj Django na konkretnu verziju iz Architecture-a (`uv add 'django==5.2.0' ...`) i ponovi komandu. Logguj konflikt u Completion Notes — možda treba eksplicitan pin u kasnijem PR-u. Ne forsiraj resolver kroz `--resolution lowest-direct` ili slično u Story 1.1.
13. **`uv init` u već postojećem ne-praznom direktorijumu** — Ako `uv init --python 3.13 --no-readme` u našem postojećem repo-u (sa `.git/`, `.gitignore`, `_bmad-output/`, `_bmad/`, `docs/`, `.claude/`) odbije execution sa porukom o non-empty dir-u ili sličnom, koristi `--bare` flag: `uv init --python 3.13 --no-readme --bare`. Ako i to padne, fallback: `uv venv --python 3.13` + ručno kreiraj minimalan `pyproject.toml` (videti šablon u Dev Notes § canonical command sequence) i nastavi sa `uv add` komandama. `--bare` u uv 0.5+ generiše SAMO `pyproject.toml` (bez `main.py`/`hello.py`/`README.md`/`.gitignore`), što je idealno za naš slučaj — razmotri ovo kao primarnu komandu ako tvoja uv verzija to podržava.

### Architecture & PRD reference

- **Source za sve odluke:** `_bmad-output/planning-artifacts/architecture.md` § Starter Template Evaluation (lines 80-150) i § Implementation Handoff (lines 1014-1046).
- **PRD relevantne sekcije:** `_bmad-output/planning-artifacts/prds/prd-CORIC_AGRAR-2026-05-27/prd.md` § 4 (FR ne diraju Story 1.1 direktno — to je bootstrap), § 5 NFR-3 (security pivot na `django-ratelimit`/`django-axes`/`django-csp` pakete koje sad instaliramo).
- **Architecture § Code Quality Stack (lines 462-469):** ruff (linter, line-length 100), djade (Django templates), pre-commit, GitHub Actions CI. Konfiguracija ovih alata dolazi u kasnijim story-jama; instalacija paketa je u Story 1.1.
- **Architecture § Dependency Stack:** Sve verzije i razlozi paketa — već extracted u tabeli iznad.
- **Architecture § Project Structure (lines 526-714):** Pun project tree — Story 1.1 popunjava root-level fajlove i `config/` direktorijum.
- **UX dokumenti (DESIGN.md, EXPERIENCE.md):** Nemaju direktan uticaj na Story 1.1 (UX se primenjuje od Story 1.5 nadalje). Skip.

### Testing Strategy

Bootstrap story nema funkcionalnih testova. Validacija je "infrastructure smoke test":

1. **Manual smoke test (mandatorni):**
   - `uv run python manage.py check` → 0 issues
   - `uv run python manage.py runserver` → Django welcome page na `http://127.0.0.1:8000/`
   - `uv run pytest --collect-only` → exit 0 (potvrđuje da pytest-django plugin radi i nema collection error-a)
   - `uv run python -c "import django; print(django.VERSION)"` → tuple sa prvim brojem `5`

2. **Automated testovi:** Nema. Prvi test fajl se kreira tek u Epic 2 story 2.1 (kada budu postojali modeli za test).

3. **Lint:**
   - `uv run ruff check .` može da bude noisy na auto-generated fajlovima — to je očekivano. Nije blocker.
   - `djade --check templates/` će failovati jer `templates/` ne postoji — `justfile`-ov `lint` recept ima `|| echo ...` fallback.

4. **CI:** Nema u Story 1.1 (Story 1.9 sets up GitHub Actions).

5. **Coverage target:** N/A (nema test fajlova).

### Project Structure Notes

Ova story striktno prati Architecture § Project Structure samo za root-level fajlove i `config/` direktorijum. Sve ostale stavke (`apps/`, `templates/`, `static/`, `locale/`, `media/`, `compose/`, `ops/`, `docs/`, `.github/`) su odgovornost kasnijih story-ja i ne kreiraju se ovde — drži scope čistim. Ako naiđeš na artefakt koji `uv init` generiše a koji se ne uklapa u Architecture target structure (npr. `src/` folder, `main.py`, `hello.py`), obriši ga.

**Konflikti sa unified strukturom:** Nema. Architecture eksplicitno propisuje ovaj početni layout i Story 1.1 je "the first implementation story" [Source: architecture.md § Implementation Handoff, line 1024].

### References

- [Source: _bmad-output/planning-artifacts/epics.md § Story 1.1: Project Bootstrap sa uv i Django, lines 401-412]
- [Source: _bmad-output/planning-artifacts/architecture.md § Starter Template Evaluation, lines 80-150]
- [Source: _bmad-output/planning-artifacts/architecture.md § Implementation Handoff — First Implementation Priority, lines 1014-1046]
- [Source: _bmad-output/planning-artifacts/architecture.md § Complete Project Tree, lines 530-714]
- [Source: _bmad-output/planning-artifacts/architecture.md § Code Quality Pattern enforcement automatika, lines 462-469]
- [Source: _bmad-output/planning-artifacts/architecture.md § Development Workflow Integration, lines 849-857]
- [Source: _bmad-output/planning-artifacts/architecture.md § Additional Requirements AR-1..AR-15, AR-32..AR-38, koje pripadaju Epic 1]
- [Source: _bmad-output/planning-artifacts/prds/prd-CORIC_AGRAR-2026-05-27/prd.md § 5 NFR-3 Sigurnost — pivot na rate limiting / axes / CSP pakete]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

_Popuni tokom implementacije._

### Completion Notes List

_Popuni posle implementacije. Tipično ovde dokumentuješ: poppler instalacijske odluke, Windows-specific gotcha-e, ruff finding-e koje ostavljaš za Story 1.9, bilo koju devijaciju od kanonskog command sled-a._

### File List

_Popuni posle implementacije — lista NEW fajlova koje si kreirao/izmenio. Očekivano za Story 1.1:_

- `pyproject.toml` (NEW)
- `uv.lock` (NEW)
- `.python-version` (NEW — auto-generated by `uv init`)
- `.gitignore` (MODIFIED — preserved BMad baseline + added Python/Django/uv pravila; backup u `.gitignore.bmad-baseline`)
- `README.md` (NEW)
- `justfile` (NEW)
- `manage.py` (NEW — auto-generated by `django-admin startproject`)
- `config/__init__.py` (NEW)
- `config/settings.py` (NEW)
- `config/urls.py` (NEW)
- `config/wsgi.py` (NEW)
- `config/asgi.py` (NEW)
