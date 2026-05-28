---
story-id: "1.2"
story-key: 1-2-multi-environment-settings-split-sa-django-environ
title: Multi-environment Settings Split sa django-environ
status: done
epic_num: 1
epic_title: Project Foundation & Visual Identity
created: 2026-05-27
completed: 2026-05-28
author: Mihas (SM autonomous)
---

# Story 1.2: Multi-environment Settings Split sa django-environ

Status: done

<!-- Validacija je opcionalna. Pre dev-story koraka možeš pokrenuti validate-create-story za quality check. -->

## Story

As a **dev (Mihas)**,
I want **odvojene Django settings module-e po environment-u (local / staging / production) sa `django-environ` integracijom za sve secret-e i env-driven konfiguraciju**,
so that **mogu sigurno da menjam parametre između lokal/staging/prod bez code change-a, da nikad ne komitujem secret u repo, i da svaki environment ima eksplicitne security guardrail-e (DEBUG, SECURE_*, HSTS) bez šanse za confused-deployment greške**.

## Acceptance Criteria

**AC1 — `config/settings/` package structure**

- **Given** Django projekat iz Story 1.1 sa single-file `config/settings.py` u root-u
- **When** kreiram Python paket `config/settings/` sa sledećim modulima:
  - `config/settings/__init__.py` (prazan ili sa docstring-om — NE re-export-uje sve iz `base`; svaki environment module je import target)
  - `config/settings/base.py` — sve zajedničke settings (INSTALLED_APPS, MIDDLEWARE, TEMPLATES, AUTH_PASSWORD_VALIDATORS, STATIC_URL, BASE_DIR, env init, secret reading, DB config)
  - `config/settings/development.py` — `from .base import *`, dev overrides
  - `config/settings/staging.py` — `from .base import *`, staging overrides
  - `config/settings/production.py` — `from .base import *`, production hardening
- **Then** stari `config/settings.py` (single file) je **OBRISAN** (NE ostaje pored package-a — Python bi mogao da rezolvuje na pogrešan target)
- **And** `config/__init__.py` i dalje postoji (settings paket NIJE `config/__init__.py` — to su dva različita paketa)
- **And** `uv run python manage.py check --settings=config.settings.development` izvršava se sa exit code 0
- **And** `uv run python manage.py check --settings=config.settings.staging` izvršava se sa exit code 0 (sa staging env vars u procesu — vidi AC4)
- **And** `uv run python manage.py check --settings=config.settings.production --deploy` izvršava se uspešno (sa prod env vars; `--deploy` flag aktivira deployment checks)

**AC2 — `base.py` content i `django-environ` integracija**

- **Given** package struktura iz AC1
- **When** popunim `base.py` sa migracijom svih relevantnih settings iz starog `config/settings.py` PLUS `django-environ` setup
- **Then** `base.py` sadrži:
  - `import environ; env = environ.Env()` inicijalizaciju na vrhu
  - `environ.Env.read_env(BASE_DIR / '.env')` poziv koji učitava `.env` ako postoji (no-op ako ne postoji — `.env` se ne komituje)
  - `SECRET_KEY = env('DJANGO_SECRET_KEY')` (NEMA default — fail-fast ako env var ne postoji)
  - `DEBUG = env.bool('DJANGO_DEBUG', default=False)` (default `False` — sigurno default-uje na production-safe)
  - `ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=[])`
  - `DATABASES = {'default': env.db('DATABASE_URL', default='sqlite:///' + str(BASE_DIR / 'db.sqlite3'))}` — `env.db()` parsira DATABASE_URL i vraća Django-ready dict
  - `INSTALLED_APPS`, `MIDDLEWARE`, `TEMPLATES`, `AUTH_PASSWORD_VALIDATORS`, `WSGI_APPLICATION`, `ROOT_URLCONF`, `STATIC_URL`, `LANGUAGE_CODE`, `TIME_ZONE`, `USE_I18N`, `USE_TZ` — preuzeti iz starog `settings.py` 1:1 (Story 1.4 menja LANGUAGE_CODE/LANGUAGES; ne diraj sada)
  - `EMAIL_*` settings čitani kroz `env.email_url('EMAIL_URL', default='consolemail://')` (django-environ helper)
  - `BASE_DIR = Path(__file__).resolve().parent.parent.parent` (TRI parent-a — fajl je u `config/settings/base.py`, root je 3 nivoa gore; STARI BASE_DIR sa 2 parent-a je za single-file `config/settings.py`)
- **And** `base.py` NE postavlja `DEBUG = True` nigde (development.py ga override-uje)
- **And** `base.py` NE sadrži hardkodovan `SECRET_KEY` (development fallback je u `.env`, NE u kodu)

**AC3 — Per-environment override moduli**

- **Given** `base.py` iz AC2
- **When** popunim development/staging/production module sa env-specific override-ima
- **Then** `development.py` sadrži:
  - `from .base import *`
  - `DEBUG = True` (dev convenience override — overrides `False` iz base)
  - `ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]']` (dev hosts)
  - `INTERNAL_IPS = ['127.0.0.1']` (django-debug-toolbar requirement)
  - `EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'` (dev — print to console, no SMTP)
- **And** `staging.py` sadrži:
  - `from .base import *`
  - `DEBUG = False`
  - `ALLOWED_HOSTS` čita iz env (već u base; staging može dodati staging-specific host kao `env.list('DJANGO_ALLOWED_HOSTS', default=['staging.example.com'])` ili samo nasleđuje base behavior)
  - Staging.py MORA sadržati sledeće SECURE_* konfiguracije (lagana varijanta production hardening-a — bez HSTS na staging-u):
    - `SECURE_SSL_REDIRECT = True`
    - `SESSION_COOKIE_SECURE = True`
    - `CSRF_COOKIE_SECURE = True`
  - **Napomena (opciono):** `SECURE_HSTS_SECONDS` se na staging-u NAMERNO ne postavlja — HSTS na ne-production domeni može da pin-uje host na HTTPS sa preload listom i da napravi trajnu nedostupnost kad se staging premesti/ugasi. Pun HSTS set (`SECURE_HSTS_SECONDS`, `SECURE_HSTS_INCLUDE_SUBDOMAINS`, `SECURE_HSTS_PRELOAD`) je samo u `production.py`. Ako baš želiš kratak HSTS na staging-u (rizik prihvataš), postavi npr. `SECURE_HSTS_SECONDS = 60` lokalno — to NIJE u Dev Notes Template-u za jednostavnost.
  - Staging mora biti production-like za realan test (TLS, secure cookies), ali bez HSTS pin-a
- **And** `production.py` sadrži:
  - `from .base import *`
  - `DEBUG = False` (eksplicitno, kao defense-in-depth iako base već default-uje na False)
  - `SECURE_SSL_REDIRECT = True`
  - `SESSION_COOKIE_SECURE = True`
  - `CSRF_COOKIE_SECURE = True`
  - `SECURE_HSTS_SECONDS = env.int('DJANGO_SECURE_HSTS_SECONDS', default=31536000)` (1 godina)
  - `SECURE_HSTS_INCLUDE_SUBDOMAINS = True`
  - `SECURE_HSTS_PRELOAD = True`
  - `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')` (Django sluša Nginx X-Forwarded-Proto)
  - `SECURE_REFERRER_POLICY = 'same-origin'`
  - `X_FRAME_OPTIONS = 'DENY'`
- **And** `production.py` NE override-uje `EMAIL_BACKEND` — koristi `EMAIL_URL` iz `base.py` koji parsira env var (Resend/Brevo SMTP URL će biti postavljen u prod env, Epic 4)

**AC4 — `.env.example` template**

- **Given** package struktura iz AC1-AC3
- **When** kreiram `.env.example` u root-u projekta (`C:/Programming/dev-bmad/CORIC_AGRAR/.env.example`)
- **Then** fajl sadrži SVE env varijable koje base/dev/staging/production module čitaju, sa **prazn-im ili placeholder vrednostima** (NIKADA realni secret), grouped i comment-ovane sekcijama:
  - **Core Django:** `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS` (NAPOMENA: `DJANGO_SETTINGS_MODULE` je NAMERNO izostavljen — settings module se određuje PRE čitanja `.env` fajla; vidi Gotcha #16. Promena se vrši preko shell env vara ili default-a u `manage.py`/`wsgi.py`/`asgi.py`.)
  - **Database:** `DATABASE_URL`
  - **Email:** `EMAIL_URL` (format: `smtp://user:pass@host:port` ili `consolemail://`)
  - **Security (production):** `DJANGO_SECURE_HSTS_SECONDS`
  - **Error tracking (Epic 9, Story 9.3):** `GLITCHTIP_DSN` (alt naziv `SENTRY_DSN` — isti SDK protokol; vidi Dev Notes; PLACEHOLDER za sada, ne čita se u base/dev/staging/prod iz Story 1.2)
  - **Email destinations (Epic 4):** `CONTACT_EMAIL_TO`, `SERVICE_EMAIL_TO`, `PARTS_EMAIL_TO` (PLACEHOLDER — ne čitaju se u Story 1.2)
- **And** svaki ključ je dokumentovan inline komentarima (jedan-linijski iznad — opis + primer)
- **And** fajl je **commit-able** i biće commitovan u repo (`!.env.example` već postoji u `.gitignore` carve-out-u)
- **And** `.env` fajl (real one) NIJE kreiran u ovoj story — local dev kopira `.env.example` → `.env` i popunjava lokalno (instrukcija u Quickstart README-a)

**AC5 — `.gitignore` verifikacija + `manage.py` / `wsgi.py` / `asgi.py` updates**

- **Given** `.env.example` iz AC4
- **When** proverim `.gitignore` (iz Story 1.1) i update-ujem entry-point fajlove
- **Then** `.gitignore` sadrži:
  - `.env` (već postoji iz Story 1.1, linija 40)
  - `.env.*` (već postoji iz Story 1.1, linija 41)
  - `!.env.example` (carve-out, već postoji iz Story 1.1, linija 42)
  - `!.env.sample` (alt, već postoji iz Story 1.1, linija 43) — opciono, ne treba menjati
- **And** `manage.py` ima izmenjenu liniju:
  - **Pre:** `os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')`
  - **Posle:** `os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')`
- **And** `config/wsgi.py` ima identičnu izmenu (default na `config.settings.development` — production overrides preko env var)
- **And** `config/asgi.py` ima identičnu izmenu
- **And** `uv run python manage.py check` (bez `--settings` flag) izvršava se uspešno sa default-om `config.settings.development`
- **And** `uv run python manage.py check --settings=config.settings.production --deploy` izvršava se uspešno **uz** valid prod env vars u procesu

## Tasks / Subtasks

- [x] **Task 1: Pre-flight i backup** (AC: 1, 5)
  - [x] 1.1 Verifikuj da je Story 1.1 done (sprint-status.yaml entry `1-1-...` == `done`)
  - [x] 1.2 Backup postojeći `config/settings.py` u memoriji — preuzmi sve relevantne settings (SECRET_KEY default value se NEĆE rekopirati u kod; SECRET_KEY ide u `.env`)
  - [x] 1.3 Verifikuj postojanje fajlova: `manage.py`, `config/__init__.py`, `config/settings.py`, `config/wsgi.py`, `config/asgi.py`, `config/urls.py`, `pyproject.toml`, `.gitignore`
  - [x] 1.4 Verifikuj da `django-environ` već postoji u `pyproject.toml` (Story 1.1 ga je dodao — vidi `[project].dependencies`). Komanda: `grep -i "django-environ" pyproject.toml` mora vratiti match.

- [x] **Task 2: Kreiraj `config/settings/` package** (AC: 1)
  - [x] 2.1 Kreiraj direktorijum: `config/settings/`
  - [x] 2.2 Kreiraj `config/settings/__init__.py` (PRAZAN fajl — NE re-export iz base; svaki env module je import target). Opcionalno: dodaj kratak docstring sa explanation.
  - [x] 2.3 **NEĆEMO još uvek obrisati** `config/settings.py` (single file) — to radimo u Task 5 nakon što novi moduli rade. Privremena koegzistencija je rizična zbog Python module resolution-a (vidi Gotcha #1), ali u koraku 5 brišemo single file.

- [x] **Task 3: Popuni `base.py`** (AC: 2)
  - [x] 3.1 Kreiraj `config/settings/base.py` sa sadržajem iz Dev Notes § `base.py` Template
  - [x] 3.2 KRITIČNO: `BASE_DIR = Path(__file__).resolve().parent.parent.parent` (3 parent-a; fajl je `config/settings/base.py` → root je 3 nivoa gore)
  - [x] 3.3 Migriraj iz starog `settings.py`: `INSTALLED_APPS`, `MIDDLEWARE`, `TEMPLATES`, `AUTH_PASSWORD_VALIDATORS`, `WSGI_APPLICATION`, `ROOT_URLCONF`, `STATIC_URL`, `LANGUAGE_CODE`, `TIME_ZONE`, `USE_I18N`, `USE_TZ`, `DEFAULT_AUTO_FIELD`
  - [x] 3.4 Dodaj `import environ; env = environ.Env()` na vrhu (posle Path import-a)
  - [x] 3.5 Dodaj `environ.Env.read_env(BASE_DIR / '.env')` posle env inicijalizacije
  - [x] 3.6 Zameni hardkodovan `SECRET_KEY` sa `SECRET_KEY = env('DJANGO_SECRET_KEY')` (NEMA default)
  - [x] 3.7 Zameni `DEBUG = True` sa `DEBUG = env.bool('DJANGO_DEBUG', default=False)`
  - [x] 3.8 Zameni `ALLOWED_HOSTS = []` sa `ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=[])`
  - [x] 3.9 Zameni SQLite DATABASES dict sa `DATABASES = {'default': env.db('DATABASE_URL', default=f'sqlite:///{BASE_DIR / "db.sqlite3"}')}`
  - [x] 3.10 Dodaj `EMAIL_CONFIG = env.email_url('EMAIL_URL', default='consolemail://')` zatim `vars().update(EMAIL_CONFIG)` (django-environ-canonical pattern — ekspanduje `EMAIL_BACKEND`, `EMAIL_HOST`, itd.)
  - [x] 3.11 NE dodaj LANGUAGES list, LOCALE_PATHS, niti modeltranslation settings — to dolazi u Story 1.4
  - [x] 3.12 NE dodaj `apps/` INSTALLED_APPS entries — Story 1.4+ dodaju kako kreiraju apps

- [x] **Task 4: Popuni development.py / staging.py / production.py** (AC: 3)
  - [x] 4.1 Kreiraj `config/settings/development.py` sa sadržajem iz Dev Notes § `development.py` Template
  - [x] 4.2 Kreiraj `config/settings/staging.py` sa sadržajem iz Dev Notes § `staging.py` Template
  - [x] 4.3 Kreiraj `config/settings/production.py` sa sadržajem iz Dev Notes § `production.py` Template
  - [x] 4.4 Verifikuj: `from .base import *` postoji kao prvi statement (posle imports) u svakom env module-u
  - [x] 4.5 Verifikuj: `production.py` NE re-definiše `EMAIL_BACKEND` — nasleđuje iz `base.py` (čije se `EMAIL_URL` env var resolve-uje u prod)

- [x] **Task 5: Obriši stari `config/settings.py`** (AC: 1)
  - [x] 5.1 Verifikuj da je `config/settings/__init__.py` kreiran (Task 2.2) i `config/settings/base.py` postoji (Task 3.1)
  - [x] 5.2 Obriši `config/settings.py` (single file). KRITIČNO: ako oba postoje (`config/settings.py` AND `config/settings/`), Python module resolution može favorizovati single file — to bi tiho srušilo sve sledeće test/check komande
  - [x] 5.3 Verifikuj: `ls config/` ne sme prikazati `settings.py` u root config dir-u; samo `settings/` direktorijum + ostali fajlovi (`__init__.py`, `urls.py`, `wsgi.py`, `asgi.py`)

- [x] **Task 6: Update `manage.py`, `wsgi.py`, `asgi.py`** (AC: 5)
  - [x] 6.1 Update `manage.py` linija 9: `os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')`
  - [x] 6.2 Update `config/wsgi.py` linija 14: identično — `'config.settings.development'`
  - [x] 6.3 Update `config/asgi.py` linija 14: identično — `'config.settings.development'`

- [x] **Task 7: Kreiraj `.env.example`** (AC: 4)
  - [x] 7.1 Kreiraj `.env.example` u root-u sa sadržajem iz Dev Notes § `.env.example` Template
  - [x] 7.2 Verifikuj: `.env.example` je commit-able (`.gitignore` ima `!.env.example` carve-out)
  - [x] 7.3 NEMOJ kreirati real `.env` fajl. Local dev će kopirati template lokalno.
  - [x] 7.4 Generiši fresh `SECRET_KEY` za local dev: pokreni `uv run python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` — ručno upiši output u lokalni `.env` posle implementacije (NE u `.env.example`, NE komituj). Dokumentuj u Completion Notes ako je urađeno.

- [x] **Task 8: Smoke validacija** (AC: 1, 5)
  - [x] 8.1 Kreiraj lokalni `.env` u root-u (za smoke test). Sadržaj minimalno:
    ```
    DJANGO_SECRET_KEY=<output iz Task 7.4 ili bilo koja non-empty string za smoke>
    DJANGO_DEBUG=True
    DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
    ```
  - [x] 8.2 Pokreni: `uv run python manage.py check` — exit code 0, output: `System check identified no issues (0 silenced).`
  - [x] 8.3 Pokreni: `uv run python manage.py check --settings=config.settings.development` — exit 0
  - [x] 8.4 Pokreni: `uv run python manage.py check --settings=config.settings.staging` — exit 0 (možeš dodatno env vars privremeno postaviti; AC1 explicit)
  - [x] 8.5 Pokreni: `DJANGO_SECRET_KEY=test DJANGO_ALLOWED_HOSTS=example.com uv run python manage.py check --settings=config.settings.production --deploy` — proveri da prolazi sa env vars; Linux/macOS syntax (PowerShell varijanta u Gotcha #6)
    - **Pass-criteria (KRITIČNO):** Očekivani output: **exit code 0**, sa eventualnim **warnings** poput `security.W009: SECRET_KEY... less than 50 chars` (to je OK za smoke — pravi production SECRET_KEY je 50+ chars random). **NE očekuj errors** (`security.E...`). Ako vidiš `security.E` ili exit code != 0 → fix configuration. Django docs: errors blokiraju exit code, warnings ne (vidi Gotcha #17).
    - **Alternative za clean output:** Za realan smoke bez warning-a možeš generisati 50+ char SECRET_KEY: `openssl rand -base64 60` (Linux/macOS) ili `python -c "import secrets; print(secrets.token_urlsafe(60))"` (cross-platform). Onda u komandi koristi taj generisan key umesto literal `test`.
  - [x] 8.6 Pokreni: `uv run python -c "from config.settings.development import DEBUG; print(DEBUG)"` — output mora biti `True`
  - [x] 8.7 Pokreni: `uv run python -c "from config.settings.production import DEBUG; print(DEBUG)"` — output mora biti `False`
  - [x] 8.8 Pokreni: `uv run python -c "from config.settings.base import SECRET_KEY; print(len(SECRET_KEY) > 0)"` — output mora biti `True`

- [x] **Task 9: Final review i sanity check** (AC: sve)
  - [x] 9.1 Verifikuj package strukturu: `tree config/` ili `ls config/settings/` — mora prikazati `__init__.py`, `base.py`, `development.py`, `staging.py`, `production.py`
  - [x] 9.2 Verifikuj da `config/settings.py` (single file) NE postoji više
  - [x] 9.3 Popuni "File List" i "Completion Notes List" u "Dev Agent Record" sekciji ovog story fajla
  - [x] 9.4 NEMOJ commitovati `.env` (real one) — proveri `git status` da `.env` nije u staged changes

## Dev Notes

### Kontekst story-ja

Ovo je **infrastructure refactor** story — bez funkcionalnih promena, ali sa **kritičnim impact-om na svaki sledeći story u svim epikima**. Settings split će biti foundation za:

- Story 1.3 (Docker Compose) — koristi `config.settings.development` u local compose, `production` u prod compose
- Story 1.4 (i18n) — proširi `base.py` sa LANGUAGES, LOCALE_PATHS, LocaleMiddleware
- Story 1.9 (CI) — koristi `config.settings.development` za pytest, proverava da prod settings rade kroz `--deploy` check
- Epic 4 (Forms) — `EMAIL_URL` env-driven SMTP
- Epic 9 (Go-live) — `GLITCHTIP_DSN` činijenje (Story 9.3) doda se u prod settings

**Princip:** ako nešto pripada budućoj story-ji (LANGUAGES, modeltranslation, GlitchTip, INSTALLED_APPS dodavanje), NE radi u ovoj. Drži scope čistim.

**Out-of-scope** za Story 1.2:
- PostgreSQL Docker container (Story 1.3 — DATABASE_URL za sada može biti SQLite default)
- LANGUAGES, LOCALE_PATHS, LocaleMiddleware (Story 1.4)
- INSTALLED_APPS dodaci za 3rd-party (django-htmx, django-bootstrap5, etc. — Story 1.6+)
- `apps/` direktorijum i Django app-ovi (Epic 2+)
- GLITCHTIP_DSN aktivacija u prod settings (Story 9.3)
- `EMAIL_URL` realne SMTP credentials (Epic 4)

### Tech stack — verzije i razlozi

| Paket | Verzija | Razlog |
|---|---|---|
| `django-environ` | `>=0.13.0` | Već u `pyproject.toml` iz Story 1.1; standard za `.env` parsing u Django ekosistemu [Source: project-context.md § Django ekosistem]. **NE** `python-dotenv` (project-context.md eksplicitno zabranjuje). |
| `django` | `>=5.2,<6.0` | LTS, već instalirano iz Story 1.1 |

`django-environ` 0.13.0+ podržava sve helper-e koje koristimo (`env.bool`, `env.list`, `env.db`, `env.email_url`, `env.int`).

**Dokumentacija:** https://django-environ.readthedocs.io/en/latest/

### `base.py` Template

[Source: architecture.md § Complete Project Tree, lines 630-635; architecture.md § Infrastructure & Deployment, line 225-226 (django-environ); project-context.md § Environment management]

```python
"""Common settings (base). Inherited by development.py, staging.py, production.py."""

from pathlib import Path

import environ

# ── Env init ─────────────────────────────────────────────────────────────────
# BASE_DIR je 3 nivoa gore: config/settings/base.py → config/settings/ → config/ → <repo root>
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
# Učitava .env iz repo root-a ako postoji (no-op u prod-u gde se env vars set-uju kroz Docker/Hetzner)
environ.Env.read_env(BASE_DIR / ".env")

# ── Core ─────────────────────────────────────────────────────────────────────
# SECRET_KEY: NEMA default — fail-fast ako env var nije set
SECRET_KEY = env("DJANGO_SECRET_KEY")

# DEBUG: default False — sigurnosno default-uje na production-safe
DEBUG = env.bool("DJANGO_DEBUG", default=False)

# ALLOWED_HOSTS: csv-list iz env
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=[])

# ── Applications ────────────────────────────────────────────────────────────
# NAPOMENA: Story 1.2 zadržava default Django INSTALLED_APPS. 3rd-party app-ovi
# (django-htmx, django-bootstrap5, modeltranslation) dodaju se u kasnijim story-jama.
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ── Database ─────────────────────────────────────────────────────────────────
# env.db() parsira DATABASE_URL u Django-ready dict.
# Default je SQLite u repo root-u za Story 1.2 smoke-test; Story 1.3 dodaje PostgreSQL.
DATABASES = {
    "default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
}

# ── Email ────────────────────────────────────────────────────────────────────
# env.email_url() ekspanduje u EMAIL_BACKEND, EMAIL_HOST, EMAIL_PORT, ...
# Default 'consolemail://' (print u konzolu — dev-friendly). Story 4.x postavlja Resend/Brevo URL.
EMAIL_CONFIG = env.email_url("EMAIL_URL", default="consolemail://")
vars().update(EMAIL_CONFIG)

# ── Auth ─────────────────────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ── i18n / l10n ──────────────────────────────────────────────────────────────
# Story 1.4 menja LANGUAGE_CODE na 'sr-latn' i dodaje LANGUAGES/LOCALE_PATHS.
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ── Static ───────────────────────────────────────────────────────────────────
STATIC_URL = "static/"
# STATIC_ROOT, STATICFILES_DIRS, MEDIA_ROOT — dolaze u Story 1.5/1.6 kad static asset folder bude kreiran

# ── Default ─────────────────────────────────────────────────────────────────
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
```

### `development.py` Template

```python
"""Development settings — used locally via `manage.py runserver` and `just dev`."""

from .base import *  # noqa: F401, F403

# Dev convenience override (overrides base default of False)
DEBUG = True

# Dev hosts only
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]

# django-debug-toolbar requires this in dev
INTERNAL_IPS = ["127.0.0.1"]

# Email goes to console in dev (no SMTP needed)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
```

### `staging.py` Template

```python
"""Staging settings — production-like, deployed to staging.coricagrar.example (Hetzner CX22)."""

from .base import *  # noqa: F401, F403

DEBUG = False

# ALLOWED_HOSTS inherited from base (env-driven). Override only ako treba dodatne hosts.

# Security — staging mora biti production-like za realan test
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Bez HSTS na staging-u (HSTS pin-uje host na HTTPS — ne želiš to na staging domenu)
```

### `production.py` Template

```python
"""Production settings — deployed to coricagrar.example (Hetzner CX32)."""

from .base import *  # noqa: F401, F403

# Eksplicitno False (defense-in-depth — base već default-uje na False)
DEBUG = False

# ALLOWED_HOSTS inherited from base (env-driven, MORA biti set u prod env)

# ── HTTPS hardening ──────────────────────────────────────────────────────────
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# HSTS (1 year default; override-able preko env)
SECURE_HSTS_SECONDS = env.int("DJANGO_SECURE_HSTS_SECONDS", default=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Additional headers
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

# Story 9.3 doda: import sentry_sdk; sentry_sdk.init(dsn=env("GLITCHTIP_DSN"), ...)
```

### `.env.example` Template

```env
# ============================================================
# Ćorić Agrar — Environment variables template
# Kopiraj ovaj fajl u `.env` (`cp .env.example .env`) i popuni vrednosti.
# `.env` se NE komituje u repo (vidi .gitignore).
# ============================================================

# ── Core Django ──────────────────────────────────────────────
# NAPOMENA: DJANGO_SETTINGS_MODULE NIJE listan ovde — `.env` se čita TEK NAKON
# što je DJANGO_SETTINGS_MODULE već postavljen kroz manage.py/wsgi.py/asgi.py
# default-e ili shell env var. Postavljanje u `.env` ne bi imalo efekta.
# Za switch između environment-a koristi:
#   - shell env var: `$env:DJANGO_SETTINGS_MODULE = "config.settings.production"` (PS) ili
#     `export DJANGO_SETTINGS_MODULE=config.settings.production` (bash)
#   - ili promeni default u manage.py/wsgi.py/asgi.py
# Default u manage.py / wsgi.py / asgi.py je `config.settings.development`.

# SECRET_KEY: generiši lokalno sa:
#   uv run python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
DJANGO_SECRET_KEY=

# Debug mode (True u local dev, False u staging/prod)
DJANGO_DEBUG=True

# Komma-separated list hostova koji smeju da serve-uju Django
# Local: localhost,127.0.0.1
# Staging: staging.example.com
# Prod: coricagrar.example,www.coricagrar.example
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# ── Database ─────────────────────────────────────────────────
# Format: postgres://user:pass@host:port/dbname
# Local (Story 1.3 PostgreSQL u Docker): postgres://coric:coric@localhost:5432/coric_agrar
# Story 1.2 default je SQLite (sqlite:///db.sqlite3) ako ostavi prazno
DATABASE_URL=

# ── Email ────────────────────────────────────────────────────
# Format: smtp+tls://user:pass@host:port  ili  consolemail://  (dev)
# Local dev default je consolemail (Email se printuje u terminalu).
# Production (Epic 4): smtp+tls://api:KEY@smtp.resend.com:465
EMAIL_URL=consolemail://

# ── Security (production only) ───────────────────────────────
# HSTS max-age u sekundama. Default 31536000 (1 godina). Postavi 0 da disable-uješ HSTS.
DJANGO_SECURE_HSTS_SECONDS=31536000

# ── Error tracking (Epic 9, Story 9.3) ───────────────────────
# GlitchTip 6 self-host DSN. Kompatibilan sa Sentry SDK protokolom.
# Format: https://<public_key>@glitchtip.example/<project_id>
# PLACEHOLDER za sada — NIJE čitan u Story 1.2 settings; aktivira se u Story 9.3.
GLITCHTIP_DSN=

# ── Email destinations (Epic 4) ──────────────────────────────
# Lead-gen forme šalju ovde. PLACEHOLDER — NIJE čitan u Story 1.2.
CONTACT_EMAIL_TO=
SERVICE_EMAIL_TO=
PARTS_EMAIL_TO=
```

### Project struktura posle ove story-je

```
coric-agrar/                                # root projekta (postojeći)
├── .env.example                            # NEW (Story 1.2)
├── .env                                    # NEW lokalno (NE komituje se; dev kreira ručno)
├── manage.py                               # MODIFIED — default settings = config.settings.development
├── config/
│   ├── __init__.py                         # EXISTING (Story 1.1)
│   ├── settings/                           # NEW package (Story 1.2)
│   │   ├── __init__.py                     # NEW (prazan)
│   │   ├── base.py                         # NEW
│   │   ├── development.py                  # NEW
│   │   ├── staging.py                      # NEW
│   │   └── production.py                   # NEW
│   ├── settings.py                         # DELETED (Story 1.2)
│   ├── urls.py                             # EXISTING
│   ├── wsgi.py                             # MODIFIED — default settings = config.settings.development
│   └── asgi.py                             # MODIFIED — default settings = config.settings.development
└── (ostali fajlovi nepromenjeni)
```

### Gotchas / Anti-patterns

1. **NIKAD ne ostavi `config/settings.py` (single file) pored `config/settings/` paketa** — Python module resolution može preferentno pokupiti single file, što tiho razbija sve subsequent test/check komande. Task 5 je MUST do; ne preskoči ga.

2. **`BASE_DIR` ima 3 parent-a, ne 2** — u single-file `config/settings.py` BASE_DIR je `Path(__file__).resolve().parent.parent` (2 parent-a). U `config/settings/base.py` MORA biti `parent.parent.parent` (3 parent-a). Ako uneseš 2 parent-a, BASE_DIR će biti `config/` umesto root-a — što razbija DATABASE_URL default path, MEDIA_ROOT (Story 1.3+), LOCALE_PATHS (Story 1.4), itd.

3. **`SECRET_KEY` NEMA default** — fail-fast je intencionalan. Ako env var nije set, `env("DJANGO_SECRET_KEY")` raise-uje `ImproperlyConfigured` što sprečava deploy sa unknown secret. Ako ti je potreban dev fallback, postavi u `.env` lokalno.

4. **`DEBUG` default mora biti `False`** — security best practice. Ako negde u kodu vidiš `env.bool("DJANGO_DEBUG", default=True)`, to je BUG (production-incentive misconfiguration). `development.py` override-uje na `True` lokalno.

5. **NIKAD ne komituj `.env`** — `.gitignore` ima `*.env` i `!.env.example` carve-out iz Story 1.1. Proveri `git status` posle implementacije; `.env` ne sme biti u staged. Ako jeste — `git rm --cached .env` pre commit-a.

6. **PowerShell vs Bash env var syntax za Task 8.5:** Linux/macOS: `DJANGO_SECRET_KEY=test uv run ...`. PowerShell: `$env:DJANGO_SECRET_KEY="test"; uv run ...` (set, then run). Kratak ad-hoc syntax kao u bash-u NE postoji u PowerShell-u.

7. **`vars().update(EMAIL_CONFIG)` pattern u `base.py`** — `env.email_url()` vraća dict sa ključevima `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`. `vars().update()` ih pojedinačno postavlja kao top-level settings (Django ih očekuje kao module attributes, ne dict). Alternative: ručno `EMAIL_BACKEND = EMAIL_CONFIG['EMAIL_BACKEND']` itd. — verbose ali eksplicitno. Koristi `vars().update()` (canonical pattern).

8. **`from .base import *` NIJE anti-pattern u settings module-ima** — to je canonical Django pattern. `# noqa: F401, F403` komentar sprečava ruff da prijavi unused-import / star-import warning-e za settings fajlove. NE pokušavaj da listaš sve symbol-e eksplicitno.

9. **`config/__init__.py` ostaje** — to je `config/` package marker (zaprava Django startproject ga je kreirao). `config/settings/__init__.py` je ZASEBAN package marker. Ne brkati dva.

10. **`production.py` NE setuje `DATABASES`** — DATABASE_URL u prod env override-uje base default. Ako primetiš tendenciju da hardkoduješ `DATABASES = {...}` u `production.py`, to je anti-pattern — koristi env var.

11. **`STATIC_ROOT` se NE definiše u Story 1.2** — `STATIC_ROOT` (path gde `collectstatic` pakuje fajlove) dolazi u Story 1.5 (kad imamo static asset folder) ili Story 1.6. Story 1.2 ostavlja samo `STATIC_URL` da Django check ne padne.

12. **Nemoj još dodavati `django-csp`, `django-axes`, `django-htmx` settings** — paketi su instalirani (Story 1.1) ali se aktivira kroz INSTALLED_APPS + MIDDLEWARE tek u kasnijim story-jama (1.6 za htmx middleware, 8.1 za axes, 9.x za csp). Story 1.2 zadržava default Django INSTALLED_APPS + MIDDLEWARE.

13. **Linter (`ruff`) warnings na star imports** — `from .base import *` će dati `F401` ili `F403` warning u `ruff`. Reši kroz `# noqa: F401, F403` inline komentar (vidi templates iznad). Globalna `ruff.toml` konfiguracija dolazi u Story 1.9 (može tamo dodati `per-file-ignores` za `config/settings/*.py`).

14. **`pyproject.toml [tool.pytest.ini_options]` config** — Story 1.2 NE dodaje pytest config (`DJANGO_SETTINGS_MODULE = "config.settings.development"`). To je out-of-scope (testovi nisu u ovoj story; project-context.md spominje ovo kao standard ali pytest config se kreira kad prvi test bude potreban — Story 1.9 ili Epic 2). Ako u smoke test-u `uv run pytest --collect-only` padne zbog missing DJANGO_SETTINGS_MODULE, log-uj u Completion Notes (NIJE blocker, Story 1.9 fix-uje).

15. **Database backend NIJE menjan u Story 1.2** — i dalje koristi `db.sqlite3` lokalno (default fallback u base.py). PostgreSQL container i `DATABASE_URL=postgres://...` ulaze u Story 1.3 (Docker compose). Smoke test 8.2-8.5 prolazi sa SQLite — DA, to je očekivano.

16. **`DJANGO_SETTINGS_MODULE` se NE čita iz `.env`** — load order je: `manage.py`/`wsgi.py`/`asgi.py` postavi default `DJANGO_SETTINGS_MODULE` (preko `os.environ.setdefault`) → Python import-uje settings module → unutar settings module-a (`base.py`) `environ.Env.read_env()` pročita `.env` u `os.environ`. To znači da je settings module odluka već donesena PRE nego što se `.env` pročita. Postavljanje `DJANGO_SETTINGS_MODULE=...` u `.env` NEMA efekta. Ako želiš override, koristi shell env var (`$env:DJANGO_SETTINGS_MODULE` PS, `export DJANGO_SETTINGS_MODULE` bash) ili promeni default u entry-point fajlovima. Iz tog razloga `DJANGO_SETTINGS_MODULE` NIJE u `.env.example` template-u (AC4).

17. **`--deploy` check: warnings vs errors** — Django `manage.py check --deploy` razlikuje:
    - `security.W...` (warnings) — exit code OSTAJE 0; check „prolazi" iako emit-uje upozorenja
    - `security.E...` (errors) — exit code != 0; check FAIL-uje
    Posledica: smoke test sa `DJANGO_SECRET_KEY=test` (< 50 chars) emit-uje `security.W009` warning ali exit code je 0. Pass-criteria za Task 8.5: očekuj exit 0; warnings su OK; errors NIJE OK. [Django docs: System check framework, message levels]

### Previous Story Intelligence (Story 1.1)

[Source: _bmad-output/implementation-artifacts/1-1-project-bootstrap-sa-uv-i-django.md]

**Patterns established u Story 1.1:**
- `pyproject.toml` koristi PEP 621 (`[project].dependencies`) + PEP 735 (`[dependency-groups].dev`) — Story 1.2 ne dira ove
- `uv.lock` je commit-ovan — Story 1.2 ne menja deps, lock fajl ostaje isti
- `.gitignore` ima BMad baseline + Python/Django/uv pattern-e (linije 40-43 cover-uju `.env`/`.env.example`/`.env.sample`) — Story 1.2 SAMO verifikuje, ne menja
- `manage.py`, `config/__init__.py`, `config/settings.py`, `config/urls.py`, `config/wsgi.py`, `config/asgi.py` postoje od `django-admin startproject config .`
- `SECRET_KEY` u `config/settings.py` je `django-insecure-d2^...` (default Django auto-generated) — Story 1.2 ga zamenjuje env-var pristupom; dev će generisati novi za lokalni `.env`

**Learnings to carry forward:**
- Postojeći `.gitignore` ima carve-out pravila (`.env.example`, `.env.sample`) — NE menjati
- Story 1.1 nije kreirao `apps/`, `templates/`, `static/`, `locale/`, `media/`, `compose/` — Story 1.2 ih takođe NE kreira
- Story 1.1 ima fresh-from-startproject `INSTALLED_APPS` i `MIDDLEWARE` — Story 1.2 ih kopira 1:1 u `base.py` bez dodavanja 3rd-party-ja

**Story 1.1 interface contract patterns (informacionalno):**
- TEA agent koristi `tests/test_<feature>.py` lokaciju za interface contract testove. Story 1.2 NEMA interface contract jer nije code-feature story (refactor + env config; vidi Testing section); ako TEA odluči da generiše testove, oni će biti `tests/test_settings.py` smoke tests (vidi Testing).

### Architecture & PRD reference

- **Settings split layout:** [Source: architecture.md § Complete Project Tree, lines 630-635] — definiše `config/settings/{base,development,staging,production}.py`
- **django-environ izbor:** [Source: architecture.md § Infrastructure & Deployment, line 225] — `django-environ` za `.env` per env
- **Environment management pravila:** [Source: project-context.md § Environment management, lines 458-464] — 3 env-a, settings split, `.env` per env, secrets u Hetzner Cloud panel za prod
- **PRD § 8 Operational Requirements:** [Source: prd.md, lines 748-753] — 3 okruženja Docker, monitoring, error tracking placeholder za Story 9.3
- **PRD § 5.3 Sigurnost:** [Source: prd.md, lines 661-666] — HTTPS, CSRF (Django default), rate-limiting — relevant settings (SECURE_*) ulaze u production.py u ovoj story
- **Story 1.1 references:** `_bmad-output/implementation-artifacts/1-1-project-bootstrap-sa-uv-i-django.md` § File List, § Tech stack
- **AR-15 (Architecture Reqs):** "Settings split sa `django-environ`" — ova story implementira AR-15
- **AR-38:** "HSTS + `SECURE_*` settings u production" — implementacija u `production.py` (Task 4.3)

### Testing Strategy

Refactor story bez funkcionalnih promena. Validacija je infrastructure smoke test + Django self-check.

1. **Smoke testovi (mandatorni — Task 8):**
   - `uv run python manage.py check` (default dev settings) → 0 issues
   - `uv run python manage.py check --settings=config.settings.development` → 0 issues
   - `uv run python manage.py check --settings=config.settings.staging` → 0 issues
   - `uv run python manage.py check --settings=config.settings.production --deploy` (sa env vars) → 0 issues
   - Module import validacija (Task 8.6-8.8): direct import-i moraju da rade i da return-uju očekivane vrednosti (DEBUG False u prod, True u dev, SECRET_KEY non-empty)

2. **Production `--deploy` check** je posebno KRITIČAN: Django dodaje extra security checks (HSTS, SECURE_SSL_REDIRECT, etc.) kada se runi sa `--deploy` flag-om. Ako `production.py` ne setuje neki potreban setting, `--deploy` check će failovati sa specifičnom porukom (npr. "(security.W004) You have not set a value for SECURE_HSTS_SECONDS").

3. **Automated testovi:** Story 1.2 NEMA dedikovane pytest testove (refactor story; nema test fajl). TEA agent može odlučiti da generiše `tests/test_settings.py` smoke testove koji import-uju svaki settings modul i verifikuju assertion-e iz AC1-AC3-AC5 (DEBUG vrednosti, SECRET_KEY env-driven, .env.example contains expected keys). Ako TEA generiše testove, Dev mora da ih pass-uje bez menjanja test fajla (per BMad TDD ciklus). Vidi `project-context.md § Test discipline`.

4. **Lint:** `uv run ruff check config/` može da prijavi `F401`/`F403` na star imports — rešen kroz `# noqa: F401, F403` u svakom env module-u (vidi templates).

5. **Coverage target:** N/A (no functional code).

### Project Structure Notes

Story 1.2 striktno prati Architecture § Complete Project Tree (lines 630-635) za `config/settings/` package layout. Naziv fajlova (`base.py`, `development.py`, `staging.py`, `production.py`) je 1:1 sa Architecture-om.

**Konflikti sa unified strukturom:** Nema. Architecture eksplicitno propisuje ovaj layout.

**Stvari koje OSTAJU placeholder-i posle Story 1.2 (i to je OK):**
- `STATIC_ROOT`, `STATICFILES_DIRS`, `MEDIA_ROOT` — Story 1.5/1.6
- `LANGUAGES`, `LOCALE_PATHS`, `LocaleMiddleware` — Story 1.4
- `LANGUAGE_CODE = 'sr-latn'` (Story 1.2 ostavlja default `en-us`) — Story 1.4
- `INSTALLED_APPS` proširenja za `django.contrib.humanize`, `django_htmx`, `bootstrap5`, `modeltranslation`, `template_partials`, `sorl.thumbnail` — Story 1.4-1.6
- `INSTALLED_APPS` proširenje za `apps.core`, `apps.brands`, itd. — Epic 2+
- `DEBUG_TOOLBAR` middleware aktivacija u dev — Story 1.3 ili 1.6
- `EMAIL_BACKEND` Resend SMTP URL — Epic 4
- `CSP_*` settings (django-csp) — Story 9.x ili kad bude needed
- `AXES_*` settings (django-axes) — Story 8.1 (custom admin login)
- `MODELTRANSLATION_*` settings — Story 1.4
- `SENTRY_DSN` / `GLITCHTIP_DSN` aktivacija u prod settings sa `sentry_sdk.init(...)` — Story 9.3

### References

- [Source: _bmad-output/planning-artifacts/epics.md § Story 1.2: Multi-environment Settings Split sa django-environ, lines 414-425]
- [Source: _bmad-output/planning-artifacts/architecture.md § Infrastructure & Deployment, lines 225-226 (django-environ choice)]
- [Source: _bmad-output/planning-artifacts/architecture.md § Complete Project Tree, lines 630-638]
- [Source: _bmad-output/planning-artifacts/architecture.md § Implementation Sequence, line 233 (Story 1.2 placement)]
- [Source: _bmad-output/planning-artifacts/architecture.md § External integration boundaries, line 787 (GlitchTip env-var placeholder)]
- [Source: _bmad-output/planning-artifacts/prds/prd-CORIC_AGRAR-2026-05-27/prd.md § 5.3 Sigurnost, lines 659-666]
- [Source: _bmad-output/planning-artifacts/prds/prd-CORIC_AGRAR-2026-05-27/prd.md § 8 Operational Requirements, lines 748-753]
- [Source: _bmad-output/project-context.md § Environment management, lines 458-464]
- [Source: _bmad-output/project-context.md § Django ekosistem, line 35 (django-environ pin)]
- [Source: _bmad-output/project-context.md § Anti-pattern: Direct User import (general Django settings discipline)]
- [Source: _bmad-output/implementation-artifacts/1-1-project-bootstrap-sa-uv-i-django.md § File List (current state references)]
- [Source: django-environ documentation, https://django-environ.readthedocs.io/en/latest/]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.7 (1M context) — Dev agent (autonomous GREEN phase)

### Debug Log References

- Baseline test run pre implementacije: 24 failed + 2 passed (regression-guards `test_ac1_config_package_init_preserved` i `test_ac4_env_in_gitignore_with_carveout`)
- Smoke checks (Task 8.2-8.5) svi prošli exit 0 sa PowerShell `$env:DJANGO_SECRET_KEY` set-om

### Completion Notes List

- Implementacija sledila Dev Notes templates 1:1 za sve 4 settings module (base/dev/staging/prod) i `.env.example`
- `vars().update(EMAIL_CONFIG)` pattern (Gotcha #7) korišćen u base.py — Ruff `# noqa: F401, F403` na star imports u env modulima
- Smoke validacija u PowerShell-u: postavljen `$env:DJANGO_SECRET_KEY` privremeno; sve 3 komande (`--settings=...development/staging/production --deploy`) vratile exit 0 sa "System check identified no issues (0 silenced)."
- `.env` (lokalni) NIJE kreiran u repo-u tokom Story 1.2 — Mihas treba da kopira `.env.example` → `.env` i ručno popuni `DJANGO_SECRET_KEY` (predlog: `uv run python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
- **TEST_MODIFICATIONS u `tests/test_bootstrap.py`** (4 testa, sve legitimne refactor side-effects iz Story 1.2):
  1. `test_ac3_django_skeleton_files_exist`: prihvata `config/settings.py` ILI `config/settings/` (Story 1.2 zamenjuje single-file sa paketom)
  2. `test_ac3_manage_py_check_passes`: setuje `DJANGO_SECRET_KEY` env var za poziv (Story 1.2 uvodi fail-fast guardrail, Gotcha #3)
  3. `test_ac3_installed_apps_is_default_django`: importuje `config.settings.base` umesto `config.settings`, postavlja DJANGO_SETTINGS_MODULE na `config.settings.development` (Story 1.2 paket umesto modula)
  4. `test_no_out_of_scope_artifacts_yet`: ukloni `.env.example` i `config/settings/` iz forbidden liste (Story 1.2 ih NAMERNO uvodi po AC1 i AC4)

### File List

**NEW:**
- `config/settings/__init__.py` (prazan docstring-only)
- `config/settings/base.py` (svi shared settings + django-environ init)
- `config/settings/development.py` (DEBUG=True, console email)
- `config/settings/staging.py` (DEBUG=False, SECURE_SSL/COOKIE_SECURE, bez HSTS)
- `config/settings/production.py` (full HTTPS hardening + HSTS + headers)
- `.env.example` (commit-able template sa svim env varijablama)

**MODIFIED:**
- `manage.py` (DJANGO_SETTINGS_MODULE default → `config.settings.development`)
- `config/wsgi.py` (DJANGO_SETTINGS_MODULE default → `config.settings.development`)
- `config/asgi.py` (DJANGO_SETTINGS_MODULE default → `config.settings.development`)
- `tests/test_bootstrap.py` (4 regression-guard testovi update-ovani — vidi Completion Notes)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (status: ready-for-dev → in-progress → review)

**DELETED:**
- `config/settings.py` (replaced by paket; Gotcha #1)
