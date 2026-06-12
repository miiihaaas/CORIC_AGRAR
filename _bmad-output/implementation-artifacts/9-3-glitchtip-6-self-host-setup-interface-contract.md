---
story-id: 9-3-glitchtip-6-self-host-setup
artifact: interface-contract
authored_by: TEA (Test Architect, RED phase)
created: 2026-06-12
source_of_truth_files:
  - compose/production.yml
  - config/settings/production.py
  - config/settings/staging.py
  - config/settings/base.py
  - config/settings/development.py
  - .env.example
  - pyproject.toml
test_file: tests/test_glitchtip_monitoring.py
---

# Interface Contract — Story 9.3 GlitchTip 6 Self-host Setup

This is the **machine-verifiable specification** the Dev MUST satisfy. It is derived
directly from the story ACs (AC1–AC9 incl. AC9 a–f), SM-Decisions (SM-D1..D11) and
Gotchas (G-1..G-17). The TEA test suite (`tests/test_glitchtip_monitoring.py`) asserts
every clause below. **All tests are RED until implementation lands.**

INFRA-VERIFY story (`needs_e2e=false`). NOT a Django app — no `apps/{module}/`. Deliverables
are config files. Tests are import-light (file-parse + `docker compose config` subprocess +
SUBPROCESS settings-import) so they run on the native Windows host despite the documented
libmagic baseline (python-magic missing → full-suite collection failure; NOT a regression).

---

## 1. compose/production.yml — activate GlitchTip stack (AC1, AC7, SM-D1/D2/D11)

Replace the commented placeholder block (current lines ~121–131) with **four real services**.

### Services (all four MUST appear in `docker compose config` rendered output)

| service | image | role |
|---|---|---|
| `glitchtip` | `glitchtip/glitchtip:<PINNED v6 tag>` (NOT `:latest`, SM-D11) | web/UI |
| `glitchtip-worker` | same pinned image | celery worker/beat (event ingest + cleanup), distinct `command:` |
| `glitchtip-postgres` | `postgres:16-alpine` | GlitchTip's own DB |
| `glitchtip-redis` | `redis:7-alpine` | GlitchTip's own queue/cache |

### `glitchtip` (web) service contract
- `image:` MUST be pinned, MUST NOT end with `:latest` (SM-D11).
- `environment:` (inline, interpolated `${...}` — NEVER inline literal secrets, G-5):
  - `SECRET_KEY: ${GLITCHTIP_SECRET_KEY:-}` (distinct from Django `DJANGO_SECRET_KEY`, G-6)
  - `DATABASE_URL: ${GLITCHTIP_DATABASE_URL:-}`
  - `REDIS_URL: ${GLITCHTIP_REDIS_URL:-}`
  - `GLITCHTIP_DOMAIN: ${GLITCHTIP_DOMAIN:-}`
  - `GLITCHTIP_MAX_EVENT_LIFE_DAYS: ${GLITCHTIP_MAX_EVENT_LIFE_DAYS:-30}` (retention 30d, AC7)
  - `EMAIL_URL: ${GLITCHTIP_EMAIL_URL:-}` (GlitchTip internal `EMAIL_URL` mapped from distinct key, SM-D6/G-16)
- `depends_on:` MUST be EXACTLY `glitchtip-postgres` + `glitchtip-redis`. MUST NOT include the app `postgres` service (G-15/SM-D2).
- MUST NOT have `env_file: ../.env` (G-14 — would leak Django secrets into GlitchTip container). Same for `glitchtip-worker`.
- `restart: unless-stopped`.
- **Machine-verifiable memory limit (AC7/AC9(f)):** MUST declare EITHER
  `deploy.resources.limits.memory: 512m` OR legacy `mem_limit: 512m` on the `glitchtip` web
  service, parsing to ~512 MiB (accepted range 400m–600m, i.e. ~419430400–629145600 bytes).
  A bare `# ~512MB` comment FAILS this — it does not survive `docker compose config` render.

### `glitchtip-worker`
- Same pinned image, same env block, `depends_on` glitchtip-postgres + glitchtip-redis,
  NO `env_file: ../.env` (G-14), distinct `command:` (celery worker/beat).

### `glitchtip-postgres`
- `postgres:16-alpine`, dedicated named volume `glitchtip_postgres_data`
  (NOT shared with `postgres_data` / `coric_agrar_production_postgres_data`, G-7).

### Top-level `volumes:`
- Add `glitchtip_postgres_data` (e.g. `name: coric_agrar_production_glitchtip_postgres_data`).
  Existing `postgres_data` / `staticfiles` / `media` untouched (regression).

### Lint
- `docker compose -f compose/production.yml config --quiet` exit 0 with all four glitchtip
  services parsable; existing `postgres`/`django`/`nginx` untouched.

---

## 2. config/settings/production.py — DSN-guarded init (AC3, AC4, SM-D3/D4)

Replace the hook comment (current line 70) with:

```python
import sentry_sdk

GLITCHTIP_DSN = env("GLITCHTIP_DSN", default="")
if GLITCHTIP_DSN:
    sentry_sdk.init(
        dsn=GLITCHTIP_DSN,
        traces_sample_rate=env.float("SENTRY_TRACES_SAMPLE_RATE", default=0.0),
        send_default_pii=False,        # GDPR (G — Epic 7 sensitive)
        environment="production",
        # release=... optional only if IMAGE_TAG non-empty (SM-D7); NO git subprocess
    )
```

Invariants:
- Empty/absent `GLITCHTIP_DSN` → `if` is False → init NOT called → import succeeds (AC3, #1 behavior).
- Set `GLITCHTIP_DSN` → init called once with `dsn=<value>`, `environment="production"`,
  `send_default_pii=False`, a numeric `traces_sample_rate` (AC4).
- Env var name is `GLITCHTIP_DSN` (NOT `SENTRY_DSN`). The SDK-tuning var keeps `SENTRY_` prefix:
  `SENTRY_TRACES_SAMPLE_RATE` (SM-D4 — deliberate, not a typo).
- `import sentry_sdk` is safe (pure-python, no import side-effect, G-3).
- Existing HTTPS hardening / Whitenoise STORAGES untouched (G-9, EXTEND not overwrite).

## 3. config/settings/staging.py — same init, environment="staging" (AC5, SM-D5)

- Identical block, `environment="staging"` (G-4 — the only diff vs production).
- MUST add explicit `from .base import env` (staging.py currently only has `from .base import *`;
  the new `env(...)`/`env.float(...)` usage needs it to avoid ruff F405 on `just lint`).

## 4. config/settings/base.py + development.py — NO init (AC5, SM-D5/G-8)

- Neither file calls `sentry_sdk.init` (no error egress in dev, no double-report) — even if
  `GLITCHTIP_DSN` is set. Regression guard.

---

## 5. .env.example — GlitchTip placeholders (AC6, AC7, AC8, SM-D6/D10)

Under the existing `# ── Error tracking (Epic 9, Story 9.3) ──` section, all EMPTY placeholders
(secrets blank after `=`):

| key | value | note |
|---|---|---|
| `GLITCHTIP_DSN=` | empty | already present; comment updated "aktivan" |
| `GLITCHTIP_SECRET_KEY=` | empty | distinct from `DJANGO_SECRET_KEY` (G-6); `secrets.token_urlsafe(50)` note (G-5) |
| `GLITCHTIP_DATABASE_URL=` | empty | GlitchTip own postgres |
| `GLITCHTIP_REDIS_URL=` | empty | GlitchTip own redis |
| `GLITCHTIP_DOMAIN=` | empty | subdomain/port (OQ-1) |
| `GLITCHTIP_MAX_EVENT_LIFE_DAYS=30` | `30` | retention (AC7) — non-secret default OK |
| `GLITCHTIP_EMAIL_URL=` | empty | distinct from Django `EMAIL_URL` (G-16); compose maps to internal `EMAIL_URL` |
| `# SENTRY_TRACES_SAMPLE_RATE=0.0` | commented | optional override (SDK-tuning var) |

- NO second bare `EMAIL_URL` key for GlitchTip (must be `GLITCHTIP_EMAIL_URL`, G-16).
- No real DSN/secret committed.

---

## 6. pyproject.toml — sentry-sdk[django] (AC2, G-12)

- Add `sentry-sdk[django]` (the `[django]` extra specifically, NOT bare `sentry-sdk`) to
  `[project].dependencies` (runtime, NOT `[dependency-groups].dev`).
- `uv.lock` regenerated (`uv add 'sentry-sdk[django]'`) containing `name = "sentry-sdk"`.

---

## Out of scope (DEFER — do NOT implement here)
- UptimeRobot (9.4), backup-to-GlitchTip capture (9.5), Django `LOGGING` dict (9.6 — SDK default
  integrations only), test-500 view (manual go-live OQ-4). SM-D8.

---

## Test → contract mapping (tests/test_glitchtip_monitoring.py)

| test (`# AC-N`) | clause |
|---|---|
| AC1 services present + config lint | §1 four services, lint exit 0 |
| AC2 sentry-sdk[django] in deps | §6 |
| AC3 empty-DSN import (prod+staging) subprocess | §2/§3 empty-DSN no-crash |
| AC4 set-DSN init kwargs (prod) subprocess | §2 init kwargs |
| AC5 dev/base no init + staging positive + `from .base import env` | §3/§4 |
| AC6 .env.example keys present + empty | §5 |
| AC7(f) memory limit ~512m on glitchtip web | §1 mem limit |
| AC7 retention 30d (.env.example) | §5 GLITCHTIP_MAX_EVENT_LIFE_DAYS=30 |
| AC7 retention env on glitchtip service (web+worker) | §1 `GLITCHTIP_MAX_EVENT_LIFE_DAYS: ${...:-30}` |
| AC8 glitchtip maps `EMAIL_URL: ${GLITCHTIP_EMAIL_URL:-}` | §1 distinct-key email mapping (SM-D6/G-16) |
| depends_on hygiene (G-15) | §1 depends_on excludes app postgres |
| env_file hygiene (G-14) | §1 no env_file on glitchtip/worker |
| image pin (SM-D11) | §1 NOT :latest |
| secrets hygiene (G-5/G-6) | §1 ${...} interpolation, distinct SECRET_KEY |
