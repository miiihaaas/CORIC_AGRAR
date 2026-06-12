---
story-id: 9-6-django-logging-konfiguracija
artifact: interface-contract
authored_by: TEA (Test Architect, RED faza)
created: 2026-06-12
language: Srpski (latinica)
status: RED (tests written, all FAILING — Dev mora da implementira)
module: config/settings/{base,development,production}.py (pure Django settings; 0 migracija, 0 dep)
test_file: tests/test_logging_config.py
---

# Interface Contract — Story 9.6 Django Logging Konfiguracija

Ovo je **SPECIFIKACIJA** (ugovor) koju Dev mora da zadovolji. Testovi u
`tests/test_logging_config.py` su izvršna verzija ovog ugovora. Ovaj dokument
pin-uje TAČAN oblik `LOGGING` dict-a tako da Dev zna precizno šta da napiše.

> TEA ne piše implementaciju. Niže su PRIMERI oblika (reference shape), ne
> kopiraj-nalepi obavezni izvor. Obavezno je samo ono što testovi asertuju.

---

## 1. `config/settings/base.py` — `LOGGING` dict (SOT — Single Source of Truth)

`base.py` definiše KOMPLETAN `LOGGING` dict. Per-env moduli ga SAMO podešavaju
(level override), NE re-definišu od nule (SM-D6 / AC8).

### 1.1. Env-gated nivo (PRE `LOGGING` dict-a)

```python
# Operativna fleksibilnost bez redeploy-a (SM-D9). Production-safe default.
# NE DEBUG default (DEBUG bi mogao log-ovati osetljive detalje + noise; G-8/G-13).
DJANGO_LOG_LEVEL = env("DJANGO_LOG_LEVEL", default="INFO")
```

- `DJANGO_LOG_LEVEL` postoji kao env var u `base.py` (SM-D9). Default `"INFO"`.
- **NIJE** obavezan za AC5 (per-env konkretni nivoi su dovoljni), ali MORA postojati
  kao dodatni operativni mehanizam (SM-D9). Test asertuje da `base.py` source
  sadrži `DJANGO_LOG_LEVEL` + `env("DJANGO_LOG_LEVEL"`.

### 1.2. Oblik `LOGGING` dict-a (reference shape)

```python
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,          # OBAVEZNO False (G-1 / AC4)
    "formatters": {
        "verbose": {
            # Zero-dep Django-native (SM-D2). NEMA PII/secret token-a (AC6).
            # SAMO logging metapodaci: level/timestamp/logger/module/process/thread/message.
            "format": "{levelname} {asctime} {name} {module} {process:d} {thread:d} {message}",
            "style": "{",                       # {} placeholderi → style "{" (G-10)
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",       # STDOUT, NE stderr (G-2 / AC2)
            "formatter": "verbose",
            "level": "DEBUG",                   # handler propušta sve; loggeri/root filtriraju nivoom
        },
        # NEMA file handler-a (SM-D1). NEMA mail_admins/AdminEmailHandler (AC6/SM-D5).
        # NEMA sentry/glitchtip handler-a (AC7/SM-D3).
    },
    "root": {
        "handlers": ["console"],                # console SAMO na root (kanonski obrazac SM-D8)
        "level": DJANGO_LOG_LEVEL,              # ≤ INFO (G-13 — Sentry breadcrumb-ovi)
    },
    "loggers": {
        # Kanonski obrazac SM-D8/G-12: žičani loggeri NEMAJU sopstveni handler;
        # propagate True → record stiže do root console handler-a I do sentry-sdk
        # root-attached capture handler-a. Per-logger tiše = preko `level`, NIKAD
        # preko propagate=False + sopstveni handler (gladuje Sentry — G-12).
        "django": {"level": "INFO", "propagate": True},
        "django.request": {"level": "ERROR", "propagate": True},
        "django.security": {"level": "ERROR", "propagate": True},
        "apps": {"level": "INFO", "propagate": True},   # project logger (SM-D8) — hvata sve apps.*
        # ZABRANJENO žičati: django.db.backends (SQL noise/PII — G-8),
        # django.server (request-line leak — AC6).
    },
}
```

**Napomene (base nivoi su default — per-env tighten):**
- U `base.py` `django` može biti `INFO` (default). Production ga spušta na `WARNING`.
- `django.request`/`django.security` na `ERROR` već u base-u je prihvatljivo (prod ih drži).
- `apps` na `INFO` u base-u; development ga diže na `DEBUG`.

---

## 2. `config/settings/production.py` — per-env tightening (level override)

NE re-definiše ceo dict. Podešava SAMO nivoe (SM-D6). KONKRETNI prod nivoi (AC3):

| Logger | Production level | Numerički |
|---|---|---|
| `django` | `WARNING` | 30 |
| `django.request` | `ERROR` | 40 |
| `django.security` | `ERROR` (ili `WARNING`) | 40 (ili 30) |
| `apps` | `INFO` | 20 |
| `root` / `console` handler | ≤ `INFO` | ≤ 20 (G-13 — breadcrumb) |

Reference shape (safe mutation — G-7):

```python
import copy
LOGGING = copy.deepcopy(LOGGING)                # NE deli nested referencu sa base (G-7)
LOGGING["loggers"]["django"]["level"] = "WARNING"
LOGGING["loggers"]["django.request"]["level"] = "ERROR"
LOGGING["loggers"]["django.security"]["level"] = "ERROR"
LOGGING["loggers"]["apps"]["level"] = "INFO"
# NE menjaj propagate na False (G-12). NE spuštaj root/console ispod INFO (G-13).
```

- `sentry_sdk.init` blok (L76-87) ostaje NETAKNUT (AC7 regression).
- Stale komentar L75 se ažurira (G-11) — edit NE sme pomeriti init blok.

---

## 3. `config/settings/development.py` — per-env loosen (verbose)

```python
import copy
LOGGING = copy.deepcopy(LOGGING)                # G-7
LOGGING["loggers"]["apps"]["level"] = "DEBUG"   # verbose dev
LOGGING["loggers"]["django"]["level"] = "INFO"  # niži (verbose-niji) od prod WARNING
# console ostaje stdout. propagate ostaje True (G-12).
```

- Dev je **verbose-niji** od prod-a — bar na jednom žičanom logger-u numerički
  niži nivo: `apps` DEBUG(10) < INFO(20), ILI `django` INFO(20) < WARNING(30) (AC5).

---

## 4. `config/settings/staging.py` — NE menja LOGGING

Nasleđuje base (production-like je dovoljno). `sentry_sdk.init` blok (`environment="staging"`,
L42-48) ostaje NETAKNUT (AC7 regression guard paralelan production.py).

---

## 5. `.env.example` (opciono, SM-D9)

`DJANGO_LOG_LEVEL=` placeholder (prazan ili `# DJANGO_LOG_LEVEL=INFO`). Production-safe default.
(NIJE testirano hard u ovom RED setu — opcioni deliverable.)

---

## 6. Šta JE i ŠTA NIJE deo ugovora

| JE deo ugovora (testirano) | NIJE deo (NE implementiraj) |
|---|---|
| `LOGGING` u base.py, valid `dictConfig` | JSON formatter / python-json-logger (OQ-2) |
| console → `ext://sys.stdout` | in-container file handler (SM-D1) |
| `disable_existing_loggers: False` | logrotate config (SM-D7 — host nota) |
| konkretni prod nivoi (AC3) | per-app logger eksplozija (OQ-3) |
| prod≠dev numerički (AC5) | sentry/glitchtip handler u LOGGING (AC7) |
| 0 PII/secret token u format string-u | mail_admins/AdminEmailHandler (AC6) |
| propagate True svuda (no Sentry starvation) | `django.db.backends` / `django.server` wiring |
| sentry init netaknut (prod + staging) | `LOGGING_CONFIG = None` (G-3) |

---

## 7. Sažetak za return payload

- **logging_keys**: `version`, `disable_existing_loggers`, `formatters`, `handlers`, `root`, `loggers`
- **loggers**: `django`, `django.request`, `django.security`, `apps` (svi propagate=True, bez sopstvenog handler-a)
- **per_env_levels**:
  - base: django=INFO, django.request=ERROR, django.security=ERROR, apps=INFO, root=DJANGO_LOG_LEVEL(INFO)
  - production: django=WARNING, django.request=ERROR, django.security=ERROR(ili WARNING), apps=INFO
  - development: apps=DEBUG (i/ili django=INFO) — numerički niži od prod-a
  - staging: nasleđuje base (NE menja)
- **sentry_coexistence**: NIJEDAN sentry/glitchtip handler u LOGGING; propagate=True svuda
  (no starvation, no double-report); production.py + staging.py `sentry_sdk.init` NETAKNUT;
  base/development bez sentry init; root/console level ≤ INFO (breadcrumb-ovi rade).
