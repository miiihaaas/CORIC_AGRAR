---
story-id: 9-3-glitchtip-6-self-host-setup
story_key: 9-3-glitchtip-6-self-host-setup
story_id_dotted: 9.3
epic: 9
module: ops/monitoring + config/settings/production.py (+ staging.py) + pyproject.toml (sentry-sdk[django]) + compose/production.yml + .env.example
title: "GlitchTip 6 Self-host Setup"
status: ready-for-dev
risk_tier: MEDIUM
language: Srpski (latinica)
created: 2026-06-12
created_by: SM (autonomous, YOLO)
needs_e2e: false
migrations: 0
new_dependencies: 1   # sentry-sdk[django] (NIJE u pyproject.toml/uv.lock — Story 9.3 dodaje u [project].dependencies)
depends_on:
  - 9-1    # compose/production.yml (django/Gunicorn+postgres+nginx) + zakomentarisan glitchtip PLACEHOLDER (linije ~121-131) — 9.3 AKTIVIRA
  - 9-2    # deploy.sh/SSL/secret-injection pattern + nginx 443 — GlitchTip subdomena/port ide kroz isti reverse-proxy/cert flow (OQ)
  - 1-2    # Settings split (config/settings/{base,development,staging,production}.py) — production.py:70 ima hook komentar za sentry_sdk.init
forward_dep:
  - 9-4    # UptimeRobot monitoring (uključuje GlitchTip URL kao monitor target)
  - 9-5    # backup skripte loguju backup FAIL u GlitchTip (sentry_sdk.capture u pg_backup.sh wrapper-u)
  - 9-6    # Django LOGGING dict — full structured logging (JSON/file/logrotate); 9.3 samo wire-uje sentry-sdk default LoggingIntegration
---

# Story 9.3: GlitchTip 6 Self-host Setup

Status: ready-for-dev

## Story

As a **dev**,
I want **GlitchTip 6 self-host stack (web + worker + sopstveni postgres + sopstveni redis) aktiviran u `compose/production.yml`, plus DSN-guarded `sentry-sdk[django]` init u Django production/staging settings-ima**,
so that **vidim sve uncaught exceptions iz produkcije sa stack trace-om, environment tag-om i alert email-ovima — bez plaćanja Sentry SaaS-a i bez PII curenja (GDPR)**.

## Opis

**TREĆA Epic 9 (Go-Live Readiness) story** — uvodi error tracking. Ovo je **INFRASTRUKTURNA/OPS story**, NE Django app feature: deliverable-i su (1) **aktivacija glitchtip servisa** u `compose/production.yml` (web+worker+sopstveni postgres+sopstveni redis — GlitchTip 6 zahteva sva četiri), (2) **mali production/staging settings blok** koji guarded-uje `sentry_sdk.init`, (3) **jedna nova runtime dep** (`sentry-sdk[django]`), (4) **proširenje `.env.example`** GlitchTip-servisnim env varijablama (sve kao PRAZNI placeholderi). NEMA migracija, NEMA Django modela, NEMA novog app-a.

Testovi su **INFRA-VERIFY** (`needs_e2e=false`): `docker compose config` lint sa aktiviranim glitchtip servisom + settings-import sanity (Django mora da se digne i kad je `GLITCHTIP_DSN` prazan — sentry no-op) + DSN-from-env wiring + `.env.example` placeholder provera + `pyproject.toml` dep provera. **NEMA browser/Playwright E2E.**

Ovo NIJE prvi dodir GlitchTip-a u kodu — 9-1 i 9-2 su namerno staged hook-ove koje 9.3 popunjava (vidi „Postojeće stanje" niže). 9.3 EXTENDS/AKTIVIRA; NE re-implementira.

### Šta 9.3 STVARNO isporučuje

1. `compose/production.yml` — **aktiviran** `glitchtip` (web) + `glitchtip-worker` + `glitchtip-postgres` + `glitchtip-redis` servisi (zamenjuje zakomentarisan placeholder na linijama ~121-131), sa **MAŠINSKI-VERIFIKABILNIM ~512MB memory limit-om** (`deploy.resources.limits.memory: 512m` ILI `mem_limit` na `glitchtip` web servisu — AC7, NE samo komentar) i retention=30d env-om. `docker compose -f compose/production.yml config` i dalje lint-uje čisto.
2. `pyproject.toml` — `sentry-sdk[django]` dodat u `[project].dependencies`; `uv.lock` regenerisan (`uv add 'sentry-sdk[django]'`).
3. `config/settings/production.py` — **DSN-guarded** `sentry_sdk.init` (popunjava hook komentar na liniji 70): prazan/odsutan `GLITCHTIP_DSN` → no-op, Django se DIŽE bez crash-a. Sa setovanim DSN-om → init pozvan sa `send_default_pii=False`, `traces_sample_rate`, `environment` tag.
4. `config/settings/staging.py` — isti guarded init (staging je production-like; `environment="staging"`). `base.py`/`development.py` **NIKAD** ne init-uju (nema error egress u dev-u).
5. `.env.example` — proširena „Error tracking" sekcija (linije ~90-94) GlitchTip-servisnim env-om (GlitchTip `SECRET_KEY`, njegov `DATABASE_URL`/postgres creds, redis url, SMTP/email za alerting preko Resend, `GLITCHTIP_MAX_EVENT_LIFE_DAYS=30`, `GLITCHTIP_DOMAIN`/port). Svi secret-i ostaju PRAZNI placeholderi.

### Postojeće stanje (READ pre izmene — obavezno)

| Fajl | Linija | Sadržaj koji 9.3 popunjava |
|---|---|---|
| `compose/production.yml` | ~121-131 | Zakomentarisan `# glitchtip:` placeholder blok („PLACEHOLDER — NE wiring u Story 9.1 (SM-D4). Story 9.3 dodaje realan servis…"). 9.3 ga AKTIVIRA. |
| `config/settings/production.py` | 70 | `# Story 9.3 doda: import sentry_sdk; sentry_sdk.init(dsn=env("GLITCHTIP_DSN"), ...)` — hook KOMENTAR. 9.3 ga zamenjuje realnim guarded init-om. |
| `config/settings/staging.py` | kraj fajla | Production-like (DEBUG=False, SSL, anymail Resend). 9.3 dodaje isti guarded init (`environment="staging"`). |
| `config/settings/base.py` | 12 | `env = environ.Env()` — helper. Pattern: `env("VAR", default="")`. NEMA sentry init u base/development. |
| `.env.example` | ~90-94 | `# ── Error tracking (Epic 9, Story 9.3) ──` sekcija sa `GLITCHTIP_DSN=` placeholder-om. 9.3 proširuje. |
| `pyproject.toml` | 6-25 | `[project].dependencies` — **NEMA `sentry-sdk`**. 9.3 dodaje `sentry-sdk[django]`. |

> **REAL-CODE-WINS reconciliacija:** hook na `production.py:70` koristi ime **`GLITCHTIP_DSN`** (NE `SENTRY_DSN` kako epics:1217 ilustrativno piše). `.env.example` već ima `GLITCHTIP_DSN=`. **Koristi `GLITCHTIP_DSN`** — to je živo, autoritativno ime. (Interno se prosledi kao `dsn=` Sentry SDK-u; ime env varijable je naše.)

---

## SM Decisions (reconciliacija — autoritativno nad epics.md ilustrativnom formulacijom)

**SM-D1 — Compose lokacija: AKTIVIRAJ u `compose/production.yml` (NE zaseban `ops/monitoring/glitchtip-compose.yml`).**
epics:1217 ilustrativno traži `ops/monitoring/glitchtip-compose.yml`, ALI 9-1 je NAMERNO staged zakomentarisan placeholder UNUTAR `compose/production.yml` (linije ~121-131, sa eksplicitnim „Story 9.3 dodaje realan servis") i `compose/production.yml` je **jedini SOT prod stack** koji se diže kroz `just prod-up` (single-stack workflow). Trade-off: zaseban fajl bi izolovao GlitchTip resource/lifecycle, ali bi zahtevao drugi `-f` flag + zaseban network bridge za reverse-proxy i razbio bi `just prod-up` single-command UX. **ODLUKA: aktiviraj blok in-place u `compose/production.yml`.** GlitchTip dobija sopstveni postgres+redis (NE deli app DB/redis — vidi SM-D2). Dev NE kreira `ops/monitoring/glitchtip-compose.yml`. (Ako ikad zatreba izolacija: budući split je trivijalan jer servisi imaju distinktna imena.)

**SM-D2 — GlitchTip 6 zahteva SVOJ postgres + SVOJ redis + worker (4 servisa, NE deli app infra).**
GlitchTip 6 je Django+Celery aplikacija sa sopstvenom šemom i event queue-om. NE sme deliti `coric_agrar` app bazu (mešanje šema, migration konflikt, blast-radius na app DB) niti app redis (app nema redis u v1 — project-context.md:84 „Bez Celery / Redis u v1"). **ODLUKA: 4 nova servisa** — `glitchtip` (web/UI), `glitchtip-worker` (Celery beat+worker za event ingest/cleanup), `glitchtip-postgres` (sopstveni named volume `glitchtip_postgres_data`), `glitchtip-redis`. Web i worker dele isti `SECRET_KEY`/`DATABASE_URL`/`REDIS_URL` env. `depends_on` postgres+redis (healthcheck gde je moguće, mirror 9-1 postgres healthcheck pattern).

**SM-D3 — DSN-guarded init: prazan/odsutan `GLITCHTIP_DSN` → sentry no-op, Django MORA da se digne (NIKAD crash pri import-u).**
Ovo je **#1 testabilni behavior**. `sentry_sdk.init(dsn="")` (ili dsn=None) je validan no-op u Sentry SDK-u — ne baca, ne šalje. ALI guard MORA biti eksplicitan da je čitljivo i da `traces_sample_rate`/`environment`/integracije ne troše ciklus kad nema DSN-a. Pattern (production.py i staging.py):
```python
import sentry_sdk

GLITCHTIP_DSN = env("GLITCHTIP_DSN", default="")
if GLITCHTIP_DSN:
    sentry_sdk.init(
        dsn=GLITCHTIP_DSN,
        traces_sample_rate=env.float("SENTRY_TRACES_SAMPLE_RATE", default=0.0),
        send_default_pii=False,   # GDPR — NE šalji PII (Epic 7 projekt je GDPR-osetljiv)
        environment="production",  # "staging" u staging.py
        # release tag opciono (vidi SM-D6)
    )
```
`import sentry_sdk` na vrhu modula je bezbedan (pure-python, nema side-effect na import). Settings-import NIKAD ne sme da padne ako je dep prisutan i DSN prazan.

**SM-D4 — `send_default_pii=False` + nizak default `traces_sample_rate` + `environment` tag (GDPR + resource).**
- `send_default_pii=False` — OBAVEZNO. Sajt je GDPR-osetljiv (Epic 7 ceo). Ne šalji IP/user/cookie/headere u GlitchTip event. (Ovo je Sentry SDK default ali se eksplicitno postavlja kao GDPR-dokaz.)
- `traces_sample_rate` default `0.0` (error tracking, NE performance APM u v1 — ~512MB box ne podnosi trace volume; env-override-abilan ako zatreba). Error capture NE zavisi od trace rate-a — unhandled exceptions se i dalje hvataju.
- **Env var ime `SENTRY_TRACES_SAMPLE_RATE` ZADRŽAVA `SENTRY_` prefiks (NIJE typo).** To je env varijabla koju **Sentry SDK** čita za `traces_sample_rate` (čitamo je u settings-u kroz `env.float("SENTRY_TRACES_SAMPLE_RATE", ...)`); to je SDK-vezana varijabla, ne GlitchTip-SERVIS varijabla. Sve env varijable koje konfigurišu GlitchTip KONTEJNER/SERVIS nose `GLITCHTIP_` prefiks (`GLITCHTIP_DSN`, `GLITCHTIP_SECRET_KEY`, `GLITCHTIP_EMAIL_URL`…); SDK-konfiguracione zadržavaju `SENTRY_`. (Dokumentovano da Dev ne pomisli da je nedoslednost/typo.)
- `environment` tag: `"production"` u production.py, `"staging"` u staging.py (razdvaja prod/staging event-e u GlitchTip UI). Mirror DJANGO env semantike.

**SM-D5 — Init SAMO u production/staging; base.py i development.py NIKAD ne init-uju.**
Dev/local NE sme slati error-e u GlitchTip (nema error egress u dev-u, nema double-report). `base.py` nema sentry init. `development.py` nema sentry init. Guard je per-settings-modul (production.py + staging.py imaju identičan blok), NE u base.py. Time je development potpuno čist (čak i da neko slučajno setuje `GLITCHTIP_DSN` u dev `.env`, development.py ga ne čita za init).

**SM-D6 — Email alerting = GlitchTip-servisni SMTP env (NE Django anymail).**
epics:1220 „Email alerting konfigurisan za critical errors — Resend SMTP iz Epic 4". GlitchTip šalje SOPSTVENE alert email-ove preko svog `EMAIL_URL`/SMTP env-a (GlitchTip-service config, NE Django `EMAIL_BACKEND`). **ODLUKA: GlitchTip SMTP pokazuje na Resend** (reuse Epic 4 Resend creds kroz env placeholder). **U `.env.example` ključ je STANDARDIZOVAN na `GLITCHTIP_EMAIL_URL=` (NE goli `EMAIL_URL`)** — Django app već koristi `EMAIL_URL=consolemail://` u `.env.example`, a GlitchTip 6 (Django app) interno takođe čita `EMAIL_URL`; dva `EMAIL_URL` ključa u istom `.env.example` = operator konfuzija. Compose `environment:` blok glitchtip servisa mapira `EMAIL_URL: ${GLITCHTIP_EMAIL_URL:-}` (operator vidi distinktan `GLITCHTIP_EMAIL_URL`, GlitchTip kontejner dobija svoj interni `EMAIL_URL`). Ne kolidiraju u runtime-u (zasebni compose env blokovi) ali distinktan KLJUČ uklanja `.env.example` dvosmislenost. Ostaje PRAZAN placeholder u `.env.example`. Konkretna konfiguracija alert pravila (koji error → email kome) je GlitchTip UI podešavanje POSLE deploy-a (OQ). 9.3 SAMO obezbeđuje SMTP env kanal.

**SM-D7 — Release tag opciono (cheaply-derivable ili izostavi).**
Ako je `release` jeftino izvodljiv (npr. `env("IMAGE_TAG", default="")` koji već postoji u .env.example, ili git sha kroz env) — dodaj `release=...`. Ako nije trivijalno bez subprocess/git poziva u settings-u (anti-pattern — settings ne sme spawn-ovati proces) — **IZOSTAVI**. NE uvodi git subprocess u settings import. Default: izostavi osim ako `IMAGE_TAG` env nije prazan.

**SM-D8 — SCOPE GUARD — šta JESTE i šta NIJE 9.3:**
- **U SCOPE-u:** glitchtip 4-servisni stack aktivacija u production.yml; `sentry-sdk[django]` dep + uv.lock; guarded init u production.py+staging.py; `.env.example` GlitchTip env proširenje; retention 30d env; ~512MB resource nota; INFRA-VERIFY testovi.
- **VAN SCOPE-a (DEFER):**
  - **9.4** UptimeRobot monitoring (uključujući monitor GlitchTip URL-a samog) — NE konfiguriši UptimeRobot ovde.
  - **9.5** backup skripte koje loguju FAIL u GlitchTip — to je 9.5 concern (`capture` poziv u backup wrapper-u). NE piši backup hook ovde.
  - **9.6** Django `LOGGING` dict (JSON formatter, file handler, logrotate). 9.3 SAMO oslanja na sentry-sdk **default `LoggingIntegration`** (auto breadcrumb-uje `logging` ERROR+ kao event). Puna strukturisana logging konfiguracija je 9.6. **NE implementiraj `LOGGING` dict ovde.** (Vidi SM-D9 za granicu.)
  - Test view koji namerno baca 500 (epics:1219 „simulirano kroz test view") — ovo je RUNTIME smoke koji se radi POSLE deploy-a na živom GlitchTip-u; NIJE INFRA-VERIFY test koji se može odraditi u CI-ju bez live stack-a. Dokumentovan kao manual go-live verifikacija (OQ), NE kao Dev deliverable view (NE dodaj `raise Exception` view u app — to bi bio dead/risk kod). Ako TEA želi marker, neka bude pytest koji asertuje DA init wiring postoji, NE da error stvarno stigne u GlitchTip.

**SM-D9 — Logging↔Sentry granica (jedna nota, NE implementacija).**
sentry-sdk `[django]` extra automatski instalira `DjangoIntegration` + default `LoggingIntegration` (hvata `logging.ERROR`+ kao GlitchTip event, `logging.INFO`+ kao breadcrumb). 9.3 NE konfiguriše ovo eksplicitno — koristi SDK default-e. Puni `LOGGING` dict (JSON-to-file + logrotate) je **9.6**. Granica: 9.3 = „SDK default integracije rade"; 9.6 = „strukturisani app log-ovi na disku". NE preklapaj.

**SM-D10 — Secret pattern (mirror 9-1 G-5 + 9-2 secret-injection).**
Svi GlitchTip secret-i (`GLITCHTIP_SECRET_KEY`, postgres password, DSN, SMTP creds) ostaju PRAZNI placeholderi u `.env.example`. U `compose/production.yml` se čitaju kroz `${...}` env interpolaciju (NIKAD inline literal). GlitchTip `SECRET_KEY` MORA biti DISTINKTAN od Django `DJANGO_SECRET_KEY` (zaseban env var — deljenje bi spojilo crypto domene dve aplikacije). NIKAD realan secret u repo (CI test `test_no_inline_secrets` mirror 9-1).

**SM-D11 — GlitchTip image MORA biti pin-ovan na konkretan GlitchTip 6 tag, NE `:latest` (resolves OQ-5 :latest deo).**
`glitchtip/glitchtip:latest` je nedeterministički — postojeći stack pin-uje sve (`postgres:16-alpine`, `redis:7-alpine`). **ODLUKA: pin-uj `glitchtip` (i `glitchtip-worker`, isti image) na konkretan GlitchTip 6 major/version tag** za reproducibilan deploy. Dev u Task 1.1 verifikuje TAČAN aktuelni upstream GlitchTip 6 tag + env-var imena za tu verziju (npr. `GLITCHTIP_MAX_EVENT_LIFE_DAYS` — env imena su se menjala kroz verzije, G-11) PRE merge-a. `:latest` je odlučeno = NE koristi se. (Rezidualni OQ-5 ostaje SAMO „koji tačan patch tag" ako precizan upstream tag mora da potvrdi Mihas/Dev na go-live — ali :latest decision je rešena: PIN.)

---

## Acceptance Criteria

**AC1 — GlitchTip servisi aktivirani + compose config lint-uje čisto**
**Given** zakomentarisan glitchtip placeholder u `compose/production.yml` (linije ~121-131)
**When** Dev aktivira `glitchtip` (web) + `glitchtip-worker` + `glitchtip-postgres` + `glitchtip-redis` servise sa sopstvenim named volume-om za GlitchTip postgres
**Then** `docker compose -f compose/production.yml config --quiet` vraća exit code 0 (YAML/schema/reference lint čist) sa sva 4 nova servisa parsabilna
**And** postojeći `django`/`postgres`/`nginx` servisi ostaju netaknuti (regression guard)
**And** GlitchTip postgres koristi ZASEBAN named volume (`glitchtip_postgres_data`), NE deli `coric_agrar_production_postgres_data`

**AC2 — `sentry-sdk[django]` dodat u dependencies**
**Given** `pyproject.toml` `[project].dependencies` bez sentry-sdk
**When** Dev pokrene `uv add 'sentry-sdk[django]'`
**Then** `pyproject.toml` `[project].dependencies` sadrži `sentry-sdk[django]` (sa `[django]` extra)
**And** `uv.lock` je regenerisan i sadrži `sentry-sdk` (+ tranzitivne deps)

**AC3 — DSN-guarded init: prazan DSN = no-op, NEMA crash (KRITIČNO)**
**Given** `config.settings.production` (i `config.settings.staging`) sa praznim `GLITCHTIP_DSN`
**When** se settings modul importuje (`python -c "import config.settings.production"` sa minimalno potrebnim env-om, GLITCHTIP_DSN nepostavljen/prazan)
**Then** import USPEVA bez izuzetka (sentry_sdk.init NIJE pozvan — guarded `if GLITCHTIP_DSN:` grana je False)
**And** Django se diže normalno (settings validan)

**AC4 — DSN-from-env wiring: setovan DSN → init pozvan sa korektnim kwargs**
**Given** `GLITCHTIP_DSN` setovan na ne-prazan string
**When** se `config.settings.production` importuje
**Then** `sentry_sdk.init` je pozvan sa `dsn=<GLITCHTIP_DSN vrednost>`
**And** poziv uključuje `send_default_pii=False` i `environment="production"` i `traces_sample_rate` (env-override-abilan, default 0.0)
**And** ime env varijable je `GLITCHTIP_DSN` (NE `SENTRY_DSN` — usaglašeno sa živim hook-om production.py:70)

**AC5 — Init SAMO u production/staging; dev/base čisti**
**Given** `config.settings.development` (i `config.settings.base`)
**When** se modul importuje sa BILO KOJOM vrednošću `GLITCHTIP_DSN` (čak i ne-prazna)
**Then** `sentry_sdk.init` NIJE pozvan (development/base nemaju init blok — nema error egress u dev-u)
**And** staging.py wiring parity: sa setovanim `GLITCHTIP_DSN`, `config.settings.staging` import poziva `sentry_sdk.init` sa IDENTIČNIM kwargs-ima kao production (AC4) ALI `environment="staging"` (NE "production") — pozitivna, testabilna asercija (mirror AC4 wiring test, staging varijanta)
**And** `staging.py` ima eksplicitan `from .base import env` (mirror production.py — sprečava ruff F405 na `just lint`)

**AC6 — `.env.example` GlitchTip placeholderi prisutni (svi prazni)**
**Given** „Error tracking (Epic 9, Story 9.3)" sekcija u `.env.example`
**When** Dev proširi sekciju GlitchTip-servisnim env-om
**Then** `.env.example` sadrži (kao PRAZNE placeholdere/komentare): `GLITCHTIP_DSN=`, GlitchTip `SECRET_KEY` (npr. `GLITCHTIP_SECRET_KEY=`), GlitchTip postgres creds/DATABASE_URL, redis url, SMTP/email za alerting (Resend), retention (`GLITCHTIP_MAX_EVENT_LIFE_DAYS=30`), `GLITCHTIP_DOMAIN`/port
**And** NIJEDAN secret nema realnu vrednost (sve prazno posle `=` ili zakomentarisano)
**And** `SENTRY_TRACES_SAMPLE_RATE` placeholder/komentar prisutan (opciono override)

**AC7 — Retention 30 dana + MAŠINSKI-VERIFIKABILAN ~512MB memory limit (AR-19)**
**Given** GlitchTip env u compose + `.env.example`
**When** Dev konfiguriše retention i resource constraint
**Then** GlitchTip servisi imaju `GLITCHTIP_MAX_EVENT_LIFE_DAYS=30` (ili ekvivalentnu retention env var) — event-i stariji od 30 dana se brišu (disk guard)
**And** `glitchtip` (web) servis MORA deklarisati MAŠINSKI-VERIFIKABILAN memory limit kroz Compose construct — ILI `deploy.resources.limits.memory` (Compose spec; Compose v2 ga honor-uje za `docker compose`, ne samo Swarm) ILI legacy `mem_limit` — postavljen na ~`512m` (AR-19 ~512MB budžet — autoritativna cita epics.md:162 + architecture.md:221; project-context.md:76 je konceptualni izvor bez 512MB broja). **Slobodan komentar `# ~512MB` SAM NIJE dovoljan** — limit MORA biti deklarativni compose ključ koji `docker compose config` renderuje i koji je asertabilan (vidi AC9(f)).
**And** alokacija ~512MB budžeta: **web servis je kapiran** (npr. `deploy.resources.limits.memory: 512m`); `glitchtip-worker`/`glitchtip-postgres`/`glitchtip-redis` su best-effort (opcioni dodatni limiti, NE blokiraju AC7). Mašinski-verifikabilna asercija je MINIMUM jedan — memory limit na `glitchtip` web servisu. (Ako Dev split-uje budžet eksplicitno preko više servisa, mora ostati barem jedan asertabilan limit na `glitchtip` web.)
**And** `docker compose -f compose/production.yml config` renderovani YAML izlaže deklarisan limit na `services.glitchtip.deploy.resources.limits.memory` (ili `services.glitchtip.mem_limit`) — to je vrednost koju AC9(f) test asertuje.

**AC8 — Email alerting kanal (GlitchTip SMTP → Resend) kao env placeholder**
**Given** GlitchTip servis
**When** Dev konfiguriše GlitchTip email env
**Then** GlitchTip servis ima SMTP/EMAIL env var koji pokazuje na Resend (reuse Epic 4 Resend creds kroz env placeholder); `.env.example` ključ je `GLITCHTIP_EMAIL_URL=` (distinktan od Django `EMAIL_URL`), a compose mapira `EMAIL_URL: ${GLITCHTIP_EMAIL_URL:-}` u GlitchTip interni `EMAIL_URL` (vidi SM-D6, G-16)
**And** vrednost ostaje PRAZAN placeholder u `.env.example` (NIKAD realan SMTP secret)
**And** komentar dokumentuje da je konkretno alert pravilo (koji error → kome) GlitchTip UI podešavanje POSLE deploy-a (OQ)

**AC9 — INFRA-VERIFY testovi (NE Playwright)**
**Given** sve gore
**When** TEA piše testove
**Then** testovi pokrivaju: (a) `docker compose config` lint sa glitchtip servisima (skip ako docker nije na PATH-u — mirror 9-1 pattern); (b) settings-import sanity za production+staging sa praznim DSN-om (subprocess `python -c` ili import-light, da izbegne admin autodiscover / libmagic baseline); (c) DSN-set → init wiring (monkeypatch `sentry_sdk.init`, asertuj kwargs); (d) `.env.example` GlitchTip placeholderi; (e) `pyproject.toml` sadrži `sentry-sdk[django]`; **(f) AC7 memory-limit asercija — parse-uj RENDEROVANI `docker compose -f compose/production.yml config` izlaz (YAML iz stdout, NE `--quiet`) i asertuj da `glitchtip` web servis deklariše memory limit: `services.glitchtip.deploy.resources.limits.memory` JE postavljen (ILI `services.glitchtip.mem_limit`), vrednost ~`512m` (npr. parse-uj na bajtove i proveri da je u opsegu, npr. `400m`–`600m`, ili egzaktno `512m`/`536870912`). Mirror `_run_docker_compose_config` helper (ali bez `--quiet` da bi se uhvatio rendered YAML na stdout); skip ako docker nije na PATH-u. Test FAIL-uje ako limit nije deklarisan kao compose ključ — slobodan `# ~512MB` komentar ne prolazi.**
**And** NIJEDAN test ne zahteva browser/Playwright (`needs_e2e=false`)
**And** testovi NE zahtevaju živ GlitchTip stack (no network egress u test-u)

---

## Tasks / Zadaci

**Task 1 — Aktiviraj GlitchTip servise u `compose/production.yml` (AC1, AC7, SM-D1, SM-D2)**
1.1. Zameni zakomentarisan placeholder blok (linije ~121-131) realnim servisima: `glitchtip` (web/UI, **pin-uj image na konkretan GlitchTip 6 tag — NE `:latest`** — mirror `postgres:16-alpine` determinizam, SM-D11; **verifikuj tačan upstream tag + env-var imena (npr. `GLITCHTIP_MAX_EVENT_LIFE_DAYS`) za tu verziju pre merge-a**), `glitchtip-worker` (isti pin-ovan image, `command:` za celery worker/beat), `glitchtip-postgres` (`postgres:16-alpine`, sopstveni named volume), `glitchtip-redis` (`redis:7-alpine`).
1.2. Web+worker env (inline `environment:`, NE `env_file`): `SECRET_KEY: ${GLITCHTIP_SECRET_KEY:-}`, `DATABASE_URL: ${GLITCHTIP_DATABASE_URL:-}`, `REDIS_URL: ${GLITCHTIP_REDIS_URL:-}`, `GLITCHTIP_DOMAIN: ${GLITCHTIP_DOMAIN:-}`, `GLITCHTIP_MAX_EVENT_LIFE_DAYS: ${GLITCHTIP_MAX_EVENT_LIFE_DAYS:-30}`, `EMAIL_URL: ${GLITCHTIP_EMAIL_URL:-}` (GlitchTip interni `EMAIL_URL` mapiran iz distinktnog `GLITCHTIP_EMAIL_URL` ključa — SM-D6, G-16). Sve kroz `${...}` interpolaciju (G-5).
1.3. `depends_on` glitchtip-postgres + glitchtip-redis (healthcheck na postgres mirror 9-1 pattern). `restart: unless-stopped`. **NE prenosi `depends_on: - postgres` (app DB servis) iz zakomentarisanog placeholder-a — GlitchTip MORA `depends_on` ISKLJUČIVO `glitchtip-postgres` + `glitchtip-redis` (sopstveni servisi); kopling na app `postgres` krši separate-DB mandat (SM-D2, vidi G-15).** Takođe: `glitchtip` i `glitchtip-worker` koriste SAMO svoj inline `environment:` blok — **NIKAD `env_file: ../.env`** (samo `django` servis ima `env_file`; kopiranje bi procurilo Django secret-e — `DJANGO_SECRET_KEY`/`ANYMAIL_RESEND_API_KEY` itd. — u GlitchTip kontejner; vidi G-14).
1.4. Dodaj `glitchtip_postgres_data` (i po potrebi `glitchtip_redis_data`) u top-level `volumes:` sa `name: coric_agrar_production_glitchtip_*`.
1.5. ~512MB memory limit (AC7, AR-19 — cita epics.md:162 + architecture.md:221) — **OBAVEZNO MAŠINSKI-VERIFIKABILNO**: `glitchtip` web servis MORA deklarisati `deploy.resources.limits.memory: 512m` (Compose spec — v2 honor-uje za `docker compose`) ILI legacy `mem_limit: 512m`. **Slobodan komentar `# ~512MB` SAM NIJE dovoljan — AC9(f) test parse-uje renderovani `docker compose config` i FAIL-uje ako compose ključ nedostaje.** `glitchtip-worker`/`-postgres`/`-redis` su best-effort (opcioni dodatni limiti). NE prejaki limit koji bi OOM-ovao web na boot-u (GlitchTip 6 web ~512m je realan minimum; ako je tesno, kapiraj web na 512m i pusti worker bez limita).
1.6. Verifikuj: `docker compose -f compose/production.yml config --quiet` exit 0.

**Task 2 — Dodaj `sentry-sdk[django]` dep (AC2)**
2.1. `uv add 'sentry-sdk[django]'` (dodaje u `[project].dependencies` + regeneriše `uv.lock`). NE u dev grupu — runtime dep, mora u prod `--no-dev` venv.
2.2. Manual review `pyproject.toml` diff (jedna linija) + `uv.lock` (sentry-sdk + tranzitivne). NE commituj bez review-a.

**Task 3 — Guarded `sentry_sdk.init` u `production.py` (AC3, AC4, SM-D3, SM-D4, SM-D7)**
3.1. Zameni hook komentar (production.py:70) realnim blokom: `import sentry_sdk` (na vrhu modula uz ostale import-e ILI lokalno pre init-a), `GLITCHTIP_DSN = env("GLITCHTIP_DSN", default="")`, `if GLITCHTIP_DSN: sentry_sdk.init(dsn=..., traces_sample_rate=env.float("SENTRY_TRACES_SAMPLE_RATE", default=0.0), send_default_pii=False, environment="production")`.
3.2. Release tag (SM-D7): SAMO ako trivijalno (`IMAGE_TAG` env ne-prazan) → `release=env("IMAGE_TAG", default="") or None`. Inače izostavi. NE uvodi git subprocess.

**Task 4 — Isti guarded init u `staging.py` (AC5, SM-D5)**
4.1. Dodaj identičan blok u `config/settings/staging.py` sa `environment="staging"` (init kwargs identični production.py, RAZLIKA samo `environment`).
4.2. **Dodaj eksplicitan `from .base import env` u `staging.py`** uz init blok (mirror production.py L4-6 koji ima `from .base import (env,)`). `staging.py` trenutno ima SAMO `from .base import *`; pošto novi init blok koristi `env(...)`/`env.float(...)`, eksplicitan import sprečava ruff F405 ("`env` may be undefined from star import") na `just lint` DoD gate-u. (Production.py već ima ovaj eksplicitan import jer koristi `env.int()`.)
4.3. Verifikuj da `base.py` i `development.py` NEMAJU sentry init (regression — ostaju čisti).

**Task 5 — Proširi `.env.example` GlitchTip sekciju (AC6, AC7, AC8, SM-D6, SM-D10)**
5.1. Pod „── Error tracking (Epic 9, Story 9.3) ──" (linije ~90-94) dodaj GlitchTip-servisne placeholdere: `GLITCHTIP_SECRET_KEY=` (DISTINKTAN od DJANGO_SECRET_KEY — komentar), `GLITCHTIP_DATABASE_URL=`, `GLITCHTIP_REDIS_URL=`, `GLITCHTIP_DOMAIN=`, `GLITCHTIP_MAX_EVENT_LIFE_DAYS=30`, `GLITCHTIP_EMAIL_URL=` (GlitchTip SMTP/email → Resend; komentar: compose mapira ovo u GlitchTip interni `EMAIL_URL`, KLJUČ je distinktan od Django `EMAIL_URL` da bi se izbegao duplikat ključa — SM-D6, G-16), `# SENTRY_TRACES_SAMPLE_RATE=0.0` (opciono override).
5.2. Komentari: DSN format, „aktivira se u Story 9.3" → ažuriraj na „aktivan", $ interpolacija upozorenje za GlitchTip SECRET_KEY (G-22 mirror), Resend reuse iz Epic 4.

**Task 6 — INFRA-VERIFY testovi (AC9) — TEA RED faza**
6.1. `tests/test_glitchtip_setup.py` (ili proširi `tests/test_docker_compose.py`): `docker compose -f compose/production.yml config` lint sa glitchtip servisima; skip ako docker nije na PATH-u (mirror postojeći `_run_docker_compose_config`).
6.2. Settings-import sanity: subprocess `python -c "import config.settings.production"` sa minimalnim env-om + praznim GLITCHTIP_DSN → exit 0 (production + staging). Subprocess izolacija izbegava admin autodiscover / libmagic baseline (NETESTABILNO na native Windows host — pre-existing baseline, vidi „Host caveat").
6.3. DSN-set wiring: asertuj da `sentry_sdk.init` bude pozvan sa `send_default_pii=False` + `environment="production"` + `dsn` match (+ staging varijanta `environment="staging"` za AC5 wiring parity). **Implementacioni hint (izbegni settings-singleton footgun — pytest-django pre-import-uje settings):** mock `sentry_sdk.init` PRE import-a; u izolovanoj test funkciji `monkeypatch.setenv("GLITCHTIP_DSN", "https://k@example.test/1")`, zatim `sys.modules.pop("config.settings.production", None)` i `importlib.reload`/import-uj modul pod `mock.patch("sentry_sdk.init")`, pa asertuj `init.assert_called_once()` + `call_args.kwargs`. **ALI:** pošto je `config.settings.production` već učitan kroz pytest-django conftest (singleton), pop+reload je krhko — **PREFERIRANA, robusnija varijanta = subprocess** (mirror AC3 empty-DSN subprocess test): pokreni `python -c` child sa `GLITCHTIP_DSN` setovanim u env-u koji monkeypatch-uje `sentry_sdk.init` da ispiše/zapiše svoje kwargs (npr. preko sitecustomize/`-c` skripte koja postavlja `sentry_sdk.init = lambda **kw: print(json.dumps(...))`), pa asertuj iz stdout-a da je init pozvan sa očekivanim kwargs-ima. Subprocess varijanta daje čistu izolaciju (svež interpreter, NEMA pre-import-ovanog settings singleton-a) i radi na host-u uprkos libmagic baseline-u.
6.4. `.env.example` GlitchTip placeholderi prisutni + svi secret-prazni.
6.5. `pyproject.toml` sadrži `sentry-sdk[django]`.
6.6. `test_no_inline_secrets` na glitchtip blok u production.yml (mirror 9-1).
6.7. **AC7 memory-limit test (AC9(f)) — OBAVEZNO**: parse-uj RENDEROVANI `docker compose -f compose/production.yml config` stdout (mirror `_run_docker_compose_config`, ali BEZ `--quiet` da uhvatiš YAML; skip ako docker nije na PATH-u). Asertuj da `glitchtip` web servis deklariše memory limit: `services.glitchtip.deploy.resources.limits.memory` postavljen (ILI `services.glitchtip.mem_limit`), vrednost ~`512m` (parse na bajtove, proveri opseg ~`400m`–`600m` ili egzaktno `512m`). Test MORA FAIL-ovati ako je limit izražen samo kao slobodan komentar (jer komentar ne preživi `docker compose config` render). Bez živog stack-a, no network egress.

**Task 7 — Manual review + reconciliacija dokumentacija**
7.1. Verifikuj SM-D1 (in-production.yml, NE ops/monitoring) + SM-D3 (empty-DSN-no-crash) lokalno ako docker dostupan.
7.2. NE implementiraj: UptimeRobot (9.4), backup-to-GlitchTip (9.5), LOGGING dict (9.6), test-500-view (manual go-live OQ).

---

## Gotchas

- **G-1 — GlitchTip 6 zahteva 4 servisa (web+worker+postgres+redis).** Nije „samo jedan kontejner". Web bez worker-a ne procesira event ingest/cleanup; bez sopstvenog redis-a worker queue ne radi; bez sopstvenog postgres-a meša šemu sa app DB. Sva četiri ili ništa.
- **G-2 — empty-DSN-no-crash je #1 test.** `if GLITCHTIP_DSN:` guard MORA biti prisutan. `sentry_sdk.init(dsn="")` je tehnički no-op ali eksplicitan guard je čitljiviji i sprečava da `environment`/`traces` rade kad nema egress-a. Settings import NIKAD ne sme da padne ako je dep prisutan i DSN prazan.
- **G-3 — `import sentry_sdk` mora postojati ali NE sme imati side-effect na import.** sentry-sdk je pure-python; `import` je bezbedan. `init()` je taj koji ima efekat — i on je guarded. Ako dep NIJE instaliran (npr. neko testira pre `uv sync`), `import sentry_sdk` baca ImportError — zato je dep dodavanje (Task 2) prerequisite za settings init (Task 3); testови koji import-uju settings očekuju da je `uv sync` odrađen.
- **G-4 — staging vs production environment tag.** Lako je copy-paste-ovati production blok u staging.py i zaboraviti `environment="staging"`. Razdvajanje prod/staging event-a u GlitchTip UI zavisi od ovog tag-a.
- **G-5 — Compose `$` interpolacija u secret-ima (mirror 9-1 G-22).** GlitchTip `SECRET_KEY` generisan sa `secrets.token_urlsafe(50)` (NE `get_random_secret_key()` koji uključuje `$` koji Compose interpolira → broken secret). Dokumentuj u `.env.example` komentaru.
- **G-6 — GlitchTip `SECRET_KEY` ≠ Django `DJANGO_SECRET_KEY`.** Distinktan env var. Deljenje bi spojilo crypto domene dve aplikacije (session/CSRF crossover rizik). Zaseban `GLITCHTIP_SECRET_KEY`.
- **G-7 — GlitchTip postgres ZASEBAN volume.** NE deli `coric_agrar_production_postgres_data` (mešanje šema, migration konflikt, app DB blast-radius). `glitchtip_postgres_data` distinktan named volume.
- **G-8 — dev NE init-uje (no double-report).** development.py i base.py BEZ sentry init. Čak i ako neko setuje DSN u dev `.env`, development.py ga ne čita za init. Sprečava da lokalni dev error-i zatrpaju prod GlitchTip.
- **G-9 — Whitenoise/manifest NETAKNUT.** sentry-sdk init NE dira `STORAGES`/static pipeline. DjangoIntegration je WSGI-level middleware injekcija (automatska), ne menja collectstatic/whitenoise. Regression: postojeći STORAGES blok u production.py ostaje.
- **G-10 — email alerting = GlitchTip SMTP, NE Django anymail.** Django `EMAIL_BACKEND=anymail.resend` šalje LEAD email-ove (Epic 4). GlitchTip alert email-ovi idu kroz GlitchTip-ov SOPSTVENI SMTP env. Dva nezavisna email kanala (oba mogu ka Resend-u). NE konfiguriši GlitchTip alerting kroz Django settings.
- **G-11 — retention env ime.** GlitchTip 6 koristi `GLITCHTIP_MAX_EVENT_LIFE_DAYS` (verifikuj tačno ime za pin-ovanu image verziju — env imena su se menjala kroz GlitchTip verzije). 30 dana = disk guard na ~512MB box-u.
- **G-12 — `sentry-sdk[django]` extra, NE bare `sentry-sdk`.** `[django]` extra obezbeđuje `DjangoIntegration` auto-discovery. Bez extra-e moraš ručno registrovati integraciju.
- **G-13 — settings-import test na native Windows host.** Pytest collect na host-u pada (libmagic missing — pre-existing baseline, NIJE regresija). Settings-import test MORA biti subprocess (`python -c`) ili import-light koji izbegava admin autodiscover, da bi se izvršio na host/CI. Vidi „Host caveat".
- **G-14 — `glitchtip`/`glitchtip-worker` NIKAD `env_file: ../.env`.** Samo `django` servis ima `env_file: ../.env`. Ako Dev kopira django servis kao template i ponese `env_file`, Django secret-i (`DJANGO_SECRET_KEY`, `ANYMAIL_RESEND_API_KEY`, DB creds…) procure u GlitchTip kontejner. GlitchTip web i worker koriste SAMO svoj inline `environment:` blok (Fix 2 / SM-D10).
- **G-15 — `depends_on` ISKLJUČIVO sopstveni servisi.** Zakomentarisan placeholder (~L130) ima `depends_on: - postgres` koji pokazuje na APP postgres. Pri aktivaciji NE prenosi to — GlitchTip MORA `depends_on` samo `glitchtip-postgres` + `glitchtip-redis`. Kopling na app `postgres` krši separate-DB mandat (SM-D2) i pravi lažnu lifecycle zavisnost na app DB.
- **G-16 — GlitchTip `EMAIL_URL` kolizija ključa u `.env.example`.** GlitchTip 6 (Django app) interno čita `EMAIL_URL`, a Django app već ima `EMAIL_URL=consolemail://` u `.env.example`. Dva ista ključa = operator konfuzija (NE runtime konflikt — zasebni compose env blokovi). Zato `.env.example` ključ je distinktan `GLITCHTIP_EMAIL_URL=`, a compose mapira `EMAIL_URL: ${GLITCHTIP_EMAIL_URL:-}` na glitchtip servisu (SM-D6).
- **G-17 — malformed (ne-prazan ali nevalidan) `GLITCHTIP_DSN` = NAMERNO fail-fast.** `if GLITCHTIP_DSN:` prolazi za ne-prazan nevalidan DSN, pa `sentry_sdk.init` baca `BadDsn` pri import-u → settings crash pri deploy-u. **Ovo je ŽELJENO ponašanje:** loše konfigurisan DSN TREBA da padne glasno pri deploy-u (fail-fast), NE tiho da proguta error egress u produkciji. NE wrap-uj u širok try/except koji bi sakrio misconfig. (Prazan DSN = legitiman no-op kroz `if` guard; nevalidan ne-prazan DSN = operatorska greška koja se vidi odmah. AC3 testira SAMO prazan-DSN-no-crash put, NE nevalidan-DSN — nevalidan je deploy-time fail-fast, ne CI invariant.)

---

## Open Questions

- **OQ-1 (go-live gate) — finalni GlitchTip URL: subdomena `errors.<domena>` vs port.** epics:1218 „https://errors.example.com (subdomena ili port)". Subdomena zahteva DNS A-record + nginx reverse-proxy blok + zaseban cert (9.2 certbot flow) → 9.4 monitor target. Port-only je jednostavniji ali manje čist. **Mihas odluka pre go-live** (vezano za OQ-2 domena iz 9.2). 9.3 ostavlja `GLITCHTIP_DOMAIN` env placeholder.
- **OQ-2 — GlitchTip na ISTOM boxu vs zaseban (512MB constraint).** CX32 prod box + ~512MB GlitchTip stack (4 servisa) deli RAM sa app stack-om. Da li GlitchTip ide na prod box ili zaseban mali box (CX22)? Trade-off: isti box = jednostavnije/jeftinije ali deljeni resource; zaseban = izolacija ali +trošak. **Mihas/infra odluka.** 9.3 honor-uje ~512MB notom ali ne forsira deployment topologiju.
- **OQ-3 — Resend SMTP creds za GlitchTip alerting.** GlitchTip email kanal pokazuje na Resend (Epic 4 creds). Da li koristi ISTI Resend API key/SMTP kao Django lead email-ovi, ili zaseban? **Mihas potvrda pre go-live.** Placeholder ostaje prazan.
- **OQ-4 — test-500-view za live smoke (epics:1219).** „Trigger 500 → pojavi se u dashboard-u" je RUNTIME verifikacija POSLE deploy-a na živom GlitchTip-u, NE CI INFRA-VERIFY. Da li dodati privremen `/__sentry-debug__/` view iza superadmin/DEBUG-guard-a za jednokratni smoke, pa ga ukloniti? Ili manual `sentry_sdk.capture_message` iz django shell-a? **Preporuka: manual shell capture** (NE dead view u app-u). Mihas/Dev odluka na go-live.
- **OQ-5 (REŠENO → SM-D11; rezidual: koji TAČAN patch tag) — GlitchTip image pin.** `:latest` deo je ODLUČEN: **pin-uj na konkretan GlitchTip 6 tag, NE `:latest`** (SM-D11, mirror `postgres:16-alpine` determinizam). Rezidualno otvoreno SAMO: koji TAČAN upstream GlitchTip 6 patch tag (npr. `v6.x.y`) + verifikacija env-var imena za tu verziju (G-11) — Dev/Mihas potvrda pri implementaciji/go-live. Nije više otvoreno PITANJE „pin ili latest".

---

## Host caveat (za Dev/TEA)

Native Windows `pytest` **ne može da collect-uje** (libmagic missing — `python-magic` zahteva system `libmagic`; dokumentovan **pre-existing baseline**, NIJE regresija ove story). INFRA-VERIFY testovi su dizajnirani da to zaobiđu:
- `docker compose config` lint = `subprocess` poziv `docker` CLI-ja (ne zahteva pytest app import).
- Settings-import sanity = `subprocess` `python -c "import config.settings.production"` (izolovan proces, NE app autodiscover kroz pytest-django conftest koji bi triggerovao libmagic).
- DSN wiring = import-light monkeypatch (ako pytest collect radi na CI Linux-u sa libmagic; na host-u ide kroz subprocess varijantu).

Svi testovi se mogu izvršiti na host/CI bez živog GlitchTip stack-a (no network egress).

## Definition of Done

- [x] AC1-AC9 zadovoljeni
- [x] `docker compose -f compose/production.yml config --quiet` exit 0 sa glitchtip servisima
- [x] `glitchtip` web servis ima MAŠINSKI-VERIFIKABILAN memory limit (`deploy.resources.limits.memory`/`mem_limit` ~512m) — AC9(f) test prolazi (NE samo komentar)
- [x] `python -c "import config.settings.production"` (i staging) ne crash-uje sa praznim GLITCHTIP_DSN
- [x] `sentry-sdk[django]` u pyproject.toml + uv.lock regenerisan (manual review)
- [x] `.env.example` GlitchTip placeholderi (svi secret-prazni)
- [x] development.py/base.py BEZ sentry init (regression)
- [x] `just lint` clean (ruff)
- [x] TEA INFRA-VERIFY testovi prolaze (31/31; docker-zavisni stvarno izvrseni — NE skip)
- [x] 0 migracija (verifikovano)
- [x] NIJEDAN realan secret u repo
