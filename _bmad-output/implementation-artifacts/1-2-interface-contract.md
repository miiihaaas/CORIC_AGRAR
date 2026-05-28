---
story-id: "1.2"
story-key: 1-2-multi-environment-settings-split-sa-django-environ
artifact: interface-contract
phase: RED (TDD)
author: TEA (autonomous)
created: 2026-05-28
---

# Interface Contract — Story 1.2 (Multi-environment Settings Split sa django-environ)

Ovaj dokument definiše **machine-verifiable** post-implementation stanje. Dev (implementator) **NE** smije menjati `tests/test_settings_split.py` — mora menjati filesystem/source code tako da svi testovi pređu sa RED na GREEN.

Testovi su organizovani po AC: `tests/test_settings_split.py`. Pokretanje:
```
uv run pytest tests/test_settings_split.py -v
```
(iz `C:\Programming\dev-bmad\CORIC_AGRAR`)

---

## 1. Filesystem state — settings package layout

### 1.1 Fajlovi koji MORAJU postojati nakon implementacije

| Path | Opis | Izvor (AC) |
|---|---|---|
| `config/__init__.py` | Postojeći config package marker (NE diraj) | AC1 |
| `config/settings/__init__.py` | NOVO — prazan ili docstring-only; NE re-export iz base | AC1 |
| `config/settings/base.py` | NOVO — zajednički settings + django-environ init | AC1, AC2 |
| `config/settings/development.py` | NOVO — `from .base import *`, dev overrides (DEBUG=True) | AC1, AC3 |
| `config/settings/staging.py` | NOVO — production-like, bez HSTS pin-a | AC1, AC3 |
| `config/settings/production.py` | NOVO — full security hardening + HSTS | AC1, AC3 |
| `.env.example` | NOVO — committable template (root) | AC4 |
| `manage.py` | MODIFIED — default `DJANGO_SETTINGS_MODULE` = `config.settings.development` | AC5 |
| `config/wsgi.py` | MODIFIED — isto kao manage.py | AC5 |
| `config/asgi.py` | MODIFIED — isto kao manage.py | AC5 |

### 1.2 Fajlovi koji MORAJU biti obrisani

| Path | Razlog | Test |
|---|---|---|
| `config/settings.py` | Replaced by `config/settings/` package — koegzistencija razbija Python module resolution | `test_ac1_old_single_settings_py_removed` |

### 1.3 Fajlovi koji ostaju nepromenjeni iz Story 1.1

| Path | Razlog |
|---|---|
| `pyproject.toml` | `django-environ` već postoji u deps; ne dodaje se nista novo |
| `.gitignore` | `.env`, `.env.*`, `!.env.example` već postoje |
| `config/urls.py` | URL conf nepromenjen |
| `uv.lock` | Bez deps promena |

---

## 2. `config/settings/base.py` — module attribute contract

`base.py` MORA eksponovati sledeće attribute (svi proverljivi `importlib.import_module("config.settings.base")` posle setovanja `DJANGO_SECRET_KEY` env vara):

| Attribute | Tip / Pattern | Source pattern (regex provera) |
|---|---|---|
| `BASE_DIR` | `pathlib.Path` — repo root (3 parenta od ovog fajla) | `Path(__file__).resolve().parent.parent.parent` |
| `SECRET_KEY` | `str`, non-empty | `env("DJANGO_SECRET_KEY")` — NEMA default |
| `DEBUG` | `bool` — default `False` ako env var nije set | `env.bool("DJANGO_DEBUG", default=False)` |
| `ALLOWED_HOSTS` | `list[str]` | `env.list("DJANGO_ALLOWED_HOSTS", default=[])` |
| `INSTALLED_APPS` | `list[str]` — 6 Django default app-ova (kao u Story 1.1) | hardcoded list |
| `MIDDLEWARE` | `list[str]` — 7 default Django middleware-a | hardcoded list |
| `ROOT_URLCONF` | `"config.urls"` | hardcoded |
| `TEMPLATES` | `list[dict]` | hardcoded |
| `WSGI_APPLICATION` | `"config.wsgi.application"` | hardcoded |
| `DATABASES` | `dict` — konstruisan via `env.db(...)` | source contains `env.db(` |
| `AUTH_PASSWORD_VALIDATORS` | `list[dict]` — 4 validatora | hardcoded |
| `LANGUAGE_CODE` | `"en-us"` (Story 1.4 menja na `sr-latn`) | hardcoded |
| `TIME_ZONE` | `"UTC"` | hardcoded |
| `USE_I18N`, `USE_TZ` | `True` | hardcoded |
| `STATIC_URL` | `"static/"` | hardcoded |
| `DEFAULT_AUTO_FIELD` | `"django.db.models.BigAutoField"` | hardcoded |

### 2.1 Source-level requirements za `base.py`

- MORA imati `import environ` na vrhu
- MORA imati `env = environ.Env()` poziv
- MORA imati `environ.Env.read_env(...)` poziv (učitava `.env` ako postoji)
- `SECRET_KEY` poziv NE sme imati `default=` argument (fail-fast)
- `DEBUG` poziv MORA imati `default=False`
- NE SME sadržati hardkodovan `django-insecure-...` string

---

## 3. `config/settings/development.py` — module attribute contract

| Attribute | Vrednost |
|---|---|
| `DEBUG` | `True` (override iz base) |
| `ALLOWED_HOSTS` | `["localhost", "127.0.0.1", "[::1]"]` |
| `INTERNAL_IPS` | `["127.0.0.1"]` |
| `EMAIL_BACKEND` | `"django.core.mail.backends.console.EmailBackend"` |

Source requirement: prvi non-import statement MORA biti `from .base import *` (sa ili bez `# noqa`).

---

## 4. `config/settings/staging.py` — module attribute contract

| Attribute | Vrednost |
|---|---|
| `DEBUG` | `False` |
| `SECURE_SSL_REDIRECT` | `True` |
| `SESSION_COOKIE_SECURE` | `True` |
| `CSRF_COOKIE_SECURE` | `True` |

**Note:** `SECURE_HSTS_SECONDS` se NAMERNO ne postavlja na staging-u (vidi story AC3). Pun HSTS set je samo u production.py.

Source requirement: `from .base import *` mora biti prisutan.

---

## 5. `config/settings/production.py` — module attribute contract

| Attribute | Vrednost |
|---|---|
| `DEBUG` | `False` |
| `SECURE_SSL_REDIRECT` | `True` |
| `SECURE_HSTS_SECONDS` | `int >= 31536000` (1 godina default) |
| `SECURE_HSTS_INCLUDE_SUBDOMAINS` | `True` |
| `SECURE_HSTS_PRELOAD` | `True` |
| `SESSION_COOKIE_SECURE` | `True` |
| `CSRF_COOKIE_SECURE` | `True` |
| `SECURE_PROXY_SSL_HEADER` | `("HTTP_X_FORWARDED_PROTO", "https")` |
| `SECURE_REFERRER_POLICY` | `"same-origin"` |
| `X_FRAME_OPTIONS` | `"DENY"` |

Source requirement: `from .base import *` mora biti prisutan.

---

## 6. CLI contracts (`manage.py check`)

| Komanda | Expected exit code | Required env vars |
|---|---|---|
| `uv run python manage.py check --settings=config.settings.development` | 0 | `DJANGO_SECRET_KEY` (može `test-secret-key-for-tea`) |
| `uv run python manage.py check --settings=config.settings.staging` | 0 | `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS=example.com` |
| `uv run python manage.py check --settings=config.settings.production --deploy` | 0 (uz potencijalne `security.W...` warnings za kratak SECRET_KEY) | `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS=example.com` |

NAPOMENA: TEA testovi se fokusiraju na development check (najmanje env zavisnosti). Staging/production check je u smoke test sekciji story-ja (Task 8) — Dev će ručno verifikovati.

---

## 7. `.env.example` filesystem contract

Lokacija: `C:/Programming/dev-bmad/CORIC_AGRAR/.env.example` (root).

### 7.1 MORA sadržati sledeće ključeve (prefiks-match, vrednost može biti prazna ili placeholder):

- `DJANGO_SECRET_KEY=` (linija počinje sa ovim)
- `DJANGO_DEBUG=`
- `DJANGO_ALLOWED_HOSTS=`
- `DATABASE_URL=`
- `EMAIL_URL=`
- `DJANGO_SECURE_HSTS_SECONDS=`

### 7.2 NE SME sadržati `DJANGO_SETTINGS_MODULE=` kao aktivnu liniju

`DJANGO_SETTINGS_MODULE` je intencionalno izostavljen iz `.env.example` jer se settings modul odlučuje PRE čitanja `.env` (Gotcha #16). Test allow-uje comment linije koje pominju ime (jer Dev Notes template ima opis), ali NE SME postojati aktivan key=value pattern `DJANGO_SETTINGS_MODULE=...`.

### 7.3 `.gitignore` carve-out

`.gitignore` MORA i dalje sadržati:
- linija `.env`
- linija `!.env.example` (carve-out — bez ovoga template fajl bi bio gitignored)

Ne menjamo `.gitignore` u ovoj story (preserved iz Story 1.1).

---

## 8. Entry-point default `DJANGO_SETTINGS_MODULE` contract

| File | Posle Story 1.1 (stanje) | Posle Story 1.2 (zahtev) |
|---|---|---|
| `manage.py` | `'config.settings'` | `'config.settings.development'` |
| `config/wsgi.py` | `'config.settings'` | `'config.settings.development'` |
| `config/asgi.py` | `'config.settings'` | `'config.settings.development'` |

Source-level check: svaki od tri fajla MORA sadržati literal string `'config.settings.development'` ili `"config.settings.development"`.

---

## 9. Security guardrails (fail-fast behavior)

### 9.1 Missing `DJANGO_SECRET_KEY` → import raises

Importovanje `config.settings.base` BEZ setovanog `DJANGO_SECRET_KEY` u `os.environ` (i bez `.env` fajla sa tom vrednošću) MORA raise-ovati `ImproperlyConfigured` ili `django.core.exceptions.ImproperlyConfigured` ili `environ.exceptions.ImproperlyConfigured`. Testira se kao subprocess.

### 9.2 No hardcoded SECRET_KEY

`base.py` source NE SME sadržati substring `django-insecure-` (Django startproject default leak).

---

## 10. Test fajl organizacija (`tests/test_settings_split.py`)

Sekcije po AC:
- AC1 — Package Structure (6 testova)
- AC2 — base.py content + django-environ (6 testova)
- AC3 — Per-env modules (6 testova; ukljucuje `test_ac3_production_has_additional_security_headers`)
- AC4 — .env.example (3 testa)
- AC5 — Entry points (3 testa)
- Edge cases / negative / security (2 testa)

**Test count target:** 26 testova ukupno (24 trebaju da padnu pre Dev-a, 2 regression guard testa prolaze i danas — `test_ac1_config_package_init_preserved`, `test_ac4_env_in_gitignore_with_carveout`).

Helper funkcije (lokalno u test fajlu):
- `_read_settings_source(name: str) -> str` — čita `config/settings/<name>.py` source
- `_load_settings_module(name: str)` — importuje modul kroz `importlib`, posle setdefault na DJANGO_SECRET_KEY
- `_run(cmd: list[str]) -> CompletedProcess` — subprocess wrapper (kopiran iz test_bootstrap.py)

---

## 11. Dependencies / pre-conditions

- Story 1.1 je done — Django skeleton postoji.
- `django-environ>=0.13.0` je u `pyproject.toml` (verifikovano).
- `uv` binary u PATH-u.
- Python 3.13.

---

## 12. Out-of-scope za Story 1.2 (informacionalno)

Sledeće NE testiramo (jer nisu u AC):
- `LANGUAGES`, `LOCALE_PATHS`, `LocaleMiddleware` (Story 1.4)
- `STATIC_ROOT`, `STATICFILES_DIRS`, `MEDIA_ROOT` (Story 1.5/1.6)
- PostgreSQL `DATABASE_URL` integration (Story 1.3)
- pytest `[tool.pytest.ini_options]` configuration (Story 1.9)
- 3rd-party `INSTALLED_APPS` (`django_htmx`, `bootstrap5`, ...) — kasnije story-je
- `EMAIL_URL` Resend/Brevo SMTP — Epic 4

Dev MORA proći sve testove SAMO za in-scope AC. Out-of-scope artefakti se ne dodaju u Story 1.2.
