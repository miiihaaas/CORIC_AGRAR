---
story-id: 9-6-django-logging-konfiguracija
story_key: 9-6-django-logging-konfiguracija
story_id_dotted: 9.6
epic: 9
module: config/settings/{base,production,development}.py (LOGGING dict — pure Django settings; NEMA app feature, NEMA migracije) + (opciono) .env.example log-level placeholder + ops/ journald nota
title: "Django Logging Konfiguracija"
status: ready-for-dev
risk_tier: MEDIUM
language: Srpski (latinica)
created: 2026-06-12
created_by: SM (autonomous, YOLO)
needs_e2e: false
migrations: 0
new_dependencies: 0   # ODLUKA SM-D2: zero-dep Django-native verbose formatter (python-json-logger NIJE usvojen u v1 — vidi SM-D2/OQ-2). Ako se kasnije usvoji JSON → +1 dep + pyproject.
depends_on:
  - 1-2    # Settings split (config/settings/{base,development,staging,production}.py) — LOGGING ide u base + per-env tightening
  - 9-1    # compose/production.yml (django/Gunicorn + log capture preko docker/journald stdout-a) — 12-factor stdout je deployment realnost
  - 9-3    # sentry-sdk[django] default LoggingIntegration — LOGGING dict MORA koegzistirati bez double-report-a
consumes:
  - 9-3    # sentry-sdk LoggingIntegration (ERROR+ → GlitchTip event, INFO+ → breadcrumb) već radi; LOGGING ga NE sme gušiti ni duplirati
---

# Story 9.6: Django Logging Konfiguracija

Status: ready-for-dev

## Story

As a **dev**,
I want **strukturisan, dosledan Django `LOGGING` dict koji loguje na stdout (Docker/journald capture-uje), sa dev-verbose vs prod-tiši nivoima, i koji koegzistira sa GlitchTip sentry-sdk integracijom**,
so that **mogu da debug-ujem post-mortem kroz `docker logs`/`journalctl` bez disk-fill-up-a i bez duplog reportovanja grešaka u GlitchTip**.

## Opis

**ŠESTA Epic 9 (Go-Live Readiness) story** — uvodi eksplicitnu logging konfiguraciju. Ovo je **PURE DJANGO SETTINGS story**, NE app feature: deliverable je (1) **`LOGGING` dict u `config/settings/base.py`** (console handler → stdout, `disable_existing_loggers=False`, razuman default nivo, žičani `django`/`django.request`/`django.security` + jedan project-level logger), (2) **per-env tightening** (`development.py` verbose/DEBUG, `production.py` tiši WARNING/INFO), (3) **ops/journald nota** (logrotate/retention kao host-level concern, NE Django), (4) opciono **`.env.example` log-level placeholder**. **NEMA migracija, NEMA Django modela, NEMA novog app-a, NEMA (u v1) nove dependency-je.**

Testovi su **import-light settings testovi** (`needs_e2e=false`), modelovani po `tests/test_settings_split.py` kanonskom obrascu (`_read_settings_source` regex source-check + `_load_settings_module` module-load): `LOGGING` je validan dict koji `logging.config.dictConfig` prihvata; očekivani logger-i/handler-i/formatter-i prisutni; console handler streamuje na `stdout`; `disable_existing_loggers=False`; prod nivo ≠ dev nivo; format string ne sadrži PII/secret token; NEMA zaseban Sentry/GlitchTip handler u `LOGGING` (sentry-sdk integracija jaše sama). **NEMA browser/Playwright E2E.**

### Reconciliacija: epics.md file-handler/logrotate vs Docker/journald stdout realnost (SRŽ STORY-JA)

epics.md 9.6 doslovno traži: `LOGGING` dict **u production.py**, **JSON formatter** (`python-json-logger`), **FILE handler na `/var/log/django/app.log`**, INFO za app / ERROR za django, **+ logrotate** (dnevno, 14d retencija, compress).

ALI stvarni deployment (Stories 9-1..9-5) je **Docker + Gunicorn + journald/`docker logs` capture** (12-factor: proces loguje na stdout, platforma persistuje). 9-4 `/healthz/` i 9-3 GlitchTip već pretpostavljaju container-stdout capture. File handler na `/var/log/django/app.log` UNUTAR kontejnera je anti-pattern (bez mount-ovanog volume-a se gubi pri restart-u; konkuriše journald/Docker capture-u; logrotate ne vidi container-interni fajl). Ovo je **RECONCILIACIJA ODLUKA** — vidi SM-D1/SM-D2/SM-D7. Ukratko: epics intent (strukturisano, post-mortem-debuggable, bez disk-fill-up-a) se ispunjava **strukturisanim logom na stdout** (journald/Docker rotacija persistuje+rotira), BEZ in-container file handler-a kao default-a. logrotate postaje host/journald ops nota (DEFER, NE Django concern — mirror 9-5 host-level cron pristup).

### Šta 9.6 STVARNO isporučuje

1. `config/settings/base.py` — **`LOGGING` dict**: `version: 1`, `disable_existing_loggers: False` (OBAVEZNO), `formatters` (verbose Django-native, zero-dep), `handlers` (`console` → `logging.StreamHandler`, `stream: ext://sys.stdout`), `loggers` (`django` WARNING/INFO, `django.request` ERROR propagate-aware, `django.security` ERROR, project logger npr. `apps`/`coric_agrar` INFO), `root` console handler na razuman nivo. Env-gated nivo preko `DJANGO_LOG_LEVEL` env (default-uje razumno).
2. `config/settings/development.py` — **per-env tightening (loosen)**: project/django nivo na DEBUG ili INFO (verbose dev convenience). Console ostaje stdout.
3. `config/settings/production.py` — **per-env tightening**: project nivo INFO, `django` WARNING (tiši — manje noise, GlitchTip hvata ERROR+). NE dodaje Sentry handler (SM-D3). NE dodaje file handler kao default (SM-D1).
4. ops/journald nota — kratak komentar (u settings-u i/ili `ops/` README) da je log retencija/rotacija HOST-level (journald `SystemMaxUse`/Docker `--log-opt max-size/max-file`), NE Django — mirror 9-5 host-cron pristup. logrotate config se NE piše kao Django deliverable.
5. (opciono) `.env.example` — `DJANGO_LOG_LEVEL=` placeholder ako se uvede env-gated nivo (prazan/komentar default).

### Postojeće stanje (READ pre izmene — obavezno)

| Fajl | Stanje | Šta 9.6 radi |
|---|---|---|
| `config/settings/base.py` | **NEMA `LOGGING` dict** (Django koristi default config). `env = environ.Env()` pattern dostupan (L12). | DODAJE `LOGGING` dict (console→stdout, disable_existing_loggers=False, žičani loggeri). |
| `config/settings/production.py` | L75 komentar „NE konfiguriše LOGGING dict (9.6) — koristi sentry-sdk default LoggingIntegration". sentry_sdk.init blok L76-87. | DODAJE per-env tightening (NE dira sentry_sdk.init blok — SM-D3). |
| `config/settings/staging.py` | sentry_sdk.init `environment="staging"` (L42-48). | NE menja per-env LOGGING (nasleđuje base; production-like je dovoljno). sentry_sdk.init blok NETAKNUT (regression guard paralelan production.py — AC7). |
| `config/settings/development.py` | `DEBUG=True`, dev STORAGES. | DODAJE per-env loosen (verbose). |
| `tests/test_settings_split.py` | Kanonski settings test obrazac (`_read_settings_source`, `_load_settings_module`). | TEA mirror-uje obrazac za LOGGING testove (zaseban fajl ili proširenje). |

> **REAL-CODE-WINS reconciliacija:** production.py:75 živi komentar eksplicitno kaže „NE konfiguriše LOGGING dict (9.6) — koristi sentry-sdk default LoggingIntegration". To je SOT: 9.3 namerno NIJE pisao LOGGING; 9.6 ga sada piše, ALI tako da sentry-sdk LoggingIntegration nastavi da radi netaknut (SM-D3).

---

## SM Decisions (reconciliacija — autoritativno nad epics.md ilustrativnom formulacijom)

**SM-D1 — stdout console handler (NE in-container file handler) kao default. epics file-handler/logrotate = INTENT ispunjen kroz journald/Docker stdout capture.**
epics:1255 ilustrativno traži FILE handler na `/var/log/django/app.log`. ALI stvarni stack (9-1..9-5) je Docker+Gunicorn → log capture preko `docker logs`/journald (12-factor stdout; epics:1258 SAM kaže „`journalctl -u django` ili Docker `logs` prikazuje structured log-ove"). File handler unutar kontejnera bez mount-ovanog volume-a je anti-pattern (gubi se pri restart-u, konkuriše journald capture-u, logrotate ne vidi container-interni put). **ODLUKA: primarni/jedini handler = `console` (`logging.StreamHandler`, `stream: ext://sys.stdout`).** Epics intent (strukturisano + post-mortem + bez disk-fill-up-a) se ispunjava: strukturisan format na stdout, journald/Docker rotacija persistuje+rotira+ograničava disk (host-level). Ako se ikad poželi in-container file handler, mora biti env-gated i OFF by default (NE u v1). Trade-off: file handler bi dao app-lokalan fajl, ali bi tražio volume mount + logrotate sidecar + dupliranje sa journald — neto komplikacija bez dobitka u Docker svetu.

**SM-D2 — Zero-dep Django-native verbose formatter u v1 (NE `python-json-logger`).**
epics:1255 traži `python-json-logger` JSON formatter. To je realan, mali dep, ALI dodaje runtime dependency + uv.lock regen za marginalnu korist u v1 (single-box, `docker logs` čitljiv ljudski; GlitchTip već daje strukturisane error event-e). **ODLUKA: dosledan Django-native `verbose` formatter** (npr. `"{levelname} {asctime} {name} {module} {process:d} {thread:d} {message}"`, `style="{"`) — zero-dep, čitljiv u `docker logs`, dovoljno strukturisan za grep/post-mortem. **python-json-logger se NE usvaja u v1** (vidi OQ-2 go-live gate). Ako biznis/ops kasnije traže mašinski-parsabilan JSON za log aggregator → usvojiti tada (+1 dep u pyproject + `pythonjsonlogger.jsonlogger.JsonFormatter` formatter). Pravilo: ne uvodi dep dok ne postoji konzument JSON-a (YAGNI).

**SM-D3 — Sentry/GlitchTip koegzistencija: NIKAD Sentry handler u `LOGGING`. sentry-sdk LoggingIntegration jaše sama — i MORA dobiti propagaciju do root-a.**
9-3 sentry-sdk `[django]` default `LoggingIntegration` već hvata `logging.ERROR`+ kao GlitchTip event i `logging.INFO`+ kao breadcrumb — AUTOMATSKI, preko SDK init-a, NE preko `LOGGING` handler-a. SDK instalira svoj capture handler na **ROOT logger** i oslanja se da record-i PROPAGIRAJU naviše do root-a. Ako bismo dodali eksplicitan Sentry/GlitchTip handler u `LOGGING.handlers`, dobili bismo **dupli report** (jednom kroz integraciju, jednom kroz handler). **ODLUKA: `LOGGING` ima SAMO console handler; NIJEDAN handler ne cilja sentry/glitchtip.** `disable_existing_loggers=False` (SM-D4) garantuje da SDK-ove integracije i Django interni loggeri ostaju živi. **KRITIČNO za koegzistenciju: žičani loggeri MORAJU propagirati do root-a — vidi kanonski obrazac u SM-D8 i G-12** (propagate=True svuda, console handler SAMO na root). 9.6 NE dira 9-3 `sentry_sdk.init` blok (production.py L76-87 / staging.py) — koegzistencija zahteva tačno NIŠTA osim „ne bori se sa njom" + da NE preseče propagaciju. `send_default_pii=False` je već u 9-3 (PII guard na SDK strani).

**SM-D4 — `disable_existing_loggers=False` je OBAVEZAN (NE ubij Django loggere).**
dictConfig default je `disable_existing_loggers=True` što bi UGASILO sve već-konfigurisane loggere (Django interne, sentry-sdk, third-party) koji nisu eksplicitno re-deklarisani u našem dict-u. To bi tiho slomilo `django.request`/`django.security`/SDK breadcrumb-ove. **ODLUKA: eksplicitno `"disable_existing_loggers": False`.** Ovo je #1 logging footgun i ima dedikovan test (AC4).

**SM-D5 — Bez-PII / bez-secret format string (security, MEDIUM risk).**
Format string MORA biti bezbedan: NE log-uj POST body-je, password-e, header-e, cookie. Django default `django.request` logger NE loguje request body — držimo to (NE dodajemo custom filter koji bi ga ubacio). Format string sadrži SAMO logging metapodatke (`levelname`/`asctime`/`name`/`module`/`process`/`thread`/`message`) — NIKAD `%(request)s` sa punim request-om niti secret env. **ODLUKA: format string bez PII/secret token-a; nema `mail_admins` handler-a koji bi slao traceback sa lokalnim varijablama; GlitchTip (`send_default_pii=False`) ostaje kanal za error-e.** Test (AC6) asertuje da format string ne sadrži zabranjene token-e (npr. `request`, `password`, `secret`, `cookie`, `authorization`).

**SM-D6 — base-vs-per-env split: base.py drži CEO `LOGGING` dict; per-env moduli SAMO tighten/loosen nivoe.**
`LOGGING` ide u `base.py` (jedan kanonski dict, console→stdout, svi handler-i/formatter-i/loggeri definisani, razuman default nivo env-gated). `development.py` i `production.py` ga ne re-definišu od nule — **podešavaju nivoe** (npr. `LOGGING["loggers"]["django"]["level"] = "WARNING"` u prod, `"DEBUG"`/`"INFO"` u dev) ILI postavljaju `DJANGO_LOG_LEVEL` semantiku. Trade-off: pun re-define po env-u bi bio eksplicitniji ali bi duplikovao 95% dict-a i razilazio bi se (drift). **ODLUKA: base = SOT dict; per-env = surgical level override.** (Ako per-env override mutira nasleđeni dict in-place, koristi `copy.deepcopy` ILI re-assignuj nested key bez deljenja reference — vidi G-7.)

**SM-D7 — logrotate/retencija = HOST/journald ops nota, DEFER (NE Django deliverable). Mirror 9-5 host-cron.**
epics:1256 traži logrotate (dnevno, 14d, compress). U Docker/journald svetu retencija je: journald `SystemMaxUse=`/`MaxRetentionSec=` ILI Docker `--log-opt max-size=10m --log-opt max-file=5` (compose `logging:` driver opcije). **ODLUKA: 9.6 NE piše `/etc/logrotate.d/django` config** (nema in-container fajla za rotirati). Umesto toga: kratka **ops nota** (komentar u settings-u + opciono `ops/` red) da je retencija host-level — mirror kako je 9-5 cron na HOSTU (SM-D6 te story-je), NE Django concern. Opciono: 9.6 MOŽE dodati `logging:` driver blok (`json-file` sa `max-size`/`max-file`) na `django` servis u `compose/production.yml` kao mašinski-realnu zamenu za logrotate — ALI to je host/compose, NE Django LOGGING dict. (Ako Dev doda compose `logging:` blok, drži ga konzervativnim i dokumentuj kao journald/Docker-rotation ekvivalent epics 14d retencije; 14d→Docker `max-file` aproksimacija je OQ-1.)

**SM-D8 — Žičani loggeri: `django`, `django.request`, `django.security`, + jedan project logger. KANONSKI OBRAZAC: console handler SAMO na `root`, žičani loggeri `propagate: True` (bez sopstvenog handler-a).**
**Obavezan obrazac (gasi I dupli red G-6 I čuva Sentry propagaciju SM-D3/G-12):** `console` handler se kači SAMO na `root` (`root: {"handlers": ["console"], "level": ...}`). Žičani loggeri NEMAJU sopstveni `handlers` (ili imaju prazan) i imaju `"propagate": True` (ili izostavljen — default je True). Tako svaki record propagira do root-a → jednom se ispiše kroz root console handler → I stigne do sentry-sdk root-attached capture handler-a.
- `django` — root Django logger; prod **WARNING** (tiši), dev INFO/DEBUG. Level-only override, BEZ sopstvenog handler-a.
- `django.request` — 5xx/4xx server error-i; prod **ERROR**; level-only, propagate True.
- `django.security` — `SuspiciousOperation` itd.; prod **ERROR** (ili WARNING); bitan za prod (DisallowedHost, CSRF anomalije); level-only, propagate True.
- project logger — JEDAN imenovan logger za app kod (npr. `"apps"` ili `"coric_agrar"`); prod **INFO**. apps već koriste `logging.getLogger("apps.media_pipeline.pdf_utils")` (vidi 2-4) — biraj root prefiks koji ih sve hvata (`"apps"`). **ODLUKA: project logger = `"apps"`** (hvata sve `apps.*` getLogger pozive jednim wiring-om; NE izmišljaj po-app logger-e — YAGNI, vidi OQ-3). NE žičaj `django.db.backends` (SQL query log = noise/PII-rizik u prod-u; ostavi default OFF).
- **ZABRANJENO: `propagate: False` na žičanom loggeru koji UZ TO ima sopstveni `console` handler.** Taj obrazac gladuje sentry-sdk LoggingIntegration (root-attached) — record nikad ne stigne do root-a → GlitchTip ne dobija ništa (kontradikcija AC7/SM-D3). Ako ops želi per-logger tiše ponašanje, to se radi PREKO `level` (npr. `django` na WARNING), NIKAD preko `propagate: False` + sopstveni handler. (Jedini bezbedan izuzetak: `propagate: False` UZ koji logger NEMA sopstveni handler — ali kanonski obrazac je propagate True svuda, pa ga koristi.)

**SM-D9 — Env-gated nivo: `DJANGO_LOG_LEVEL` env (default razuman po env-u).**
Operativna fleksibilnost bez redeploy-a code-a: `DJANGO_LOG_LEVEL = env("DJANGO_LOG_LEVEL", default="INFO")` (ili default izveden po env-u). Project/root logger nivo čita ovu env. **ODLUKA: jedan env var `DJANGO_LOG_LEVEL`** (NE po-logger env eksplozija). `.env.example` dobija `DJANGO_LOG_LEVEL=` placeholder/komentar. Default mora biti production-safe (INFO ili WARNING, NE DEBUG — DEBUG bi mogao log-ovati osetljive detalje + noise). Mirror `DJANGO_DEBUG` env pattern iz base.py.

---

## Acceptance Criteria

**AC1 — `LOGGING` dict postoji u base.py i validan je za `logging.config.dictConfig`**
**Given** `config/settings/base.py` bez `LOGGING` dict-a
**When** Dev doda `LOGGING` dict
**Then** `config.settings.base` (i `development`/`production`) eksponuje `LOGGING` kao `dict` sa `LOGGING["version"] == 1`
**And** `logging.config.dictConfig(settings.LOGGING)` se izvršava BEZ izuzetka (dict je strukturno validan — svi handler-i referenciraju postojeće formatter-e, svi loggeri postojeće handler-e)

**AC2 — Console handler streamuje na stdout (Docker/journald capture)**
**Given** `LOGGING["handlers"]`
**When** se dict pregleda
**Then** postoji `console` handler sa `"class": "logging.StreamHandler"`
**And** handler eksplicitno cilja **stdout** (`"stream": "ext://sys.stdout"`) — NE stderr default (vidi G-2)
**And** NEMA file handler-a na `/var/log/django/*` kao default (SM-D1); ako postoji ikakav file handler, env-gated je i OFF by default

**AC3 — Žičani loggeri: django / django.request / django.security / project (`apps`) sa konkretnim prod nivoima**
**Given** `LOGGING["loggers"]`
**When** se dict pregleda
**Then** prisutni su loggeri: `django`, `django.request`, `django.security`, i project logger (`apps`)
**And** svaki dolazi do `console` handler-a kroz `root`/propagaciju (kanonski obrazac SM-D8: handler na root, žičani loggeri propagate=True)
**And** u **production** modulu efektivni nivoi su KONKRETNI i falsifikabilni testom (uskladi sa SM-D8/Task 2.2): `django` == `WARNING`, `django.request` == `ERROR`, `django.security` == `ERROR` (ili `WARNING`), `apps` == `INFO`. Test asertuje konkretne nivoe, NE samo prisutnost logger-a.
**And** NIJEDAN žičani logger nema `propagate: False` UZ koji ima sopstveni `console` handler (Sentry-starvation guard — G-12/SM-D3); test FAIL-uje na takvu kombinaciju.
**And** `django.db.backends` NIJE žičan (NE log-uj SQL u prod — noise/PII; SM-D8)

**AC4 — `disable_existing_loggers=False` (KRITIČNO — ne ubij Django loggere)**
**Given** `LOGGING` dict
**When** se pregleda
**Then** `LOGGING["disable_existing_loggers"] is False` (eksplicitno)
**And** test FAIL-uje ako je True ili odsutno (dictConfig default je True — footgun, vidi G-1)

**AC5 — Prod nivo ≠ dev nivo (per-env tightening)**
**Given** `config.settings.development` i `config.settings.production`
**When** se oba modula učitaju i uporedi efektivni nivo project/django logger-a (ili root)
**Then** development je verbose-niji (DEBUG ili INFO) a production tiši (INFO ili WARNING) — nivoi se RAZLIKUJU bar na jednom žičanom logger-u (npr. `django` WARNING u prod vs INFO/DEBUG u dev)
**And** test koristi **numeričko poređenje** logging nivoa (`logging.getLevelName(name)` → int; `logging.DEBUG`==10 < `INFO`==20 < `WARNING`==30 < `ERROR`==40), NE string-poređenje — da „DEBUG ili INFO za dev" vs „INFO ili WARNING za prod" radi korektno (dev_level < prod_level na žičanom logger-u koji se razlikuje)
**And** oba i dalje koriste console→stdout handler (base `LOGGING` nasleđen, NE re-definisan od nule — SM-D6)
**And** AC5 testira prod≠dev kroz KONKRETNE nivoe (AC3/SM-D8). `DJANGO_LOG_LEVEL` env-gating (SM-D9) je DODATNI operativni mehanizam, **NIJE obavezan za AC5** — AC5 prolazi i bez env-gatinga ako su per-env konkretni nivoi različiti. (Env-gating ostaje deo SM-D9 deliverable-a, ali AC5 ga ne zahteva.)

**AC6 — Format string bez PII/secret token-a (security, MEDIUM)**
**Given** `LOGGING["formatters"]` format string(ovi)
**When** se format string-ovi pregledaju
**Then** test ITERIRA preko SVIH `LOGGING["formatters"][*]["format"]` (ne samo jednog) i svaki NE sadrži zabranjene token-e koji bi log-ovali osetljiv sadržaj: `request` (pun request objekat), `password`, `secret`, `cookie`, `authorization`, `token`, `body`
**And** svaki format string sadrži SAMO logging metapodatke (`levelname`/`asctime`/`name`/`module`/`message` i sl.)
**And** NEMA `mail_admins` handler-a (eksplicitno: nijedan handler u `LOGGING["handlers"]` nema `class` koji sadrži `AdminEmailHandler`, niti ključ `mail_admins`) niti handler-a koji emit-uje traceback sa lokalnim varijablama van GlitchTip-a (SM-D5)
**And** NIJE žičan `django.server` logger niti bilo koji request-body/header logging koji bi leak-ovao PII (test asertuje `django.server` odsutan iz `LOGGING["loggers"]`)

**AC7 — Sentry koegzistencija: NIJEDAN Sentry/GlitchTip handler u LOGGING + propagacija očuvana (no double-report, no starvation)**
**Given** `LOGGING` dict + 9-3 sentry-sdk LoggingIntegration (root-attached capture handler)
**When** se `LOGGING["handlers"]` i `LOGGING["loggers"]` pregledaju
**Then** NIJEDAN handler nema `class` koji sadrži `sentry`/`glitchtip` (npr. NE `sentry_sdk.integrations.logging.EventHandler` / NE custom GlitchTip handler) — SDK integracija jaše sama (SM-D3)
**And** NIJEDAN žičani logger (`django`/`django.request`/`django.security`/`apps`) nema `propagate: False` UZ koji ima sopstveni handler (Sentry-starvation: record bi se zaustavio pre root-a → SDK ne bi dobio event/breadcrumb). Kanonski obrazac: svi žičani loggeri `propagate` True (ili izostavljen). Test FAIL-uje ako bilo koji žičani logger ima `propagate == False` I neprazan sopstveni `handlers` (G-12/SM-D3).
**And** `config/settings/production.py` sentry_sdk.init blok (L76-87) ostaje NETAKNUT (regression guard — 9.6 ga NE menja; edit stale komentara L75 NE sme pomeriti init blok)
**And** `config/settings/staging.py` sentry_sdk.init blok (L42-48, `environment="staging"`) ostaje NETAKNUT (regression guard paralelan production.py)
**And** `base.py`/`development.py` i dalje nemaju sentry init (9-3 invariant očuvan)

**AC8 — base-vs-per-env split korektan (base = SOT dict, per-env = level override)**
**Given** `base.py` `LOGGING` + per-env moduli
**When** se moduli učitaju
**Then** `base.LOGGING` je kompletan dict (handlers/formatters/loggers definisani); `development.py` i `production.py` NE re-definišu ceo dict od nule već podešavaju nivoe (ili `DJANGO_LOG_LEVEL`)
**And** per-env override NE deli mutabilnu nested referencu sa base na način koji bi cross-kontaminirao (deepcopy ILI re-assign nested key — G-7); učitavanje `development` pa `production` daje različite prod/dev nivoe (NE poslednji-pobeđuje bug)

**AC9 — Import-light settings testovi (NE Playwright)**
**Given** sve gore
**When** TEA piše testove (mirror `tests/test_settings_split.py`: `_read_settings_source` regex + `_load_settings_module` module-load)
**Then** testovi pokrivaju: (a) `LOGGING` postoji + `dictConfig` ga prihvata; (b) console handler `ext://sys.stdout`; (c) žičani loggeri prisutni + KONKRETNI prod nivoi (numeričko poređenje); (d) `disable_existing_loggers is False`; (e) prod nivo ≠ dev nivo (numeričko poređenje); (f) SVI format string-ovi bez PII/secret token-a + nema `mail_admins`/`django.server`; (g) nema sentry/glitchtip handler-a u LOGGING + nijedan žičani logger nema `propagate==False` sa sopstvenim handler-om (Sentry-starvation guard) + production.py I staging.py sentry init netaknut; (h) base-vs-per-env split (base SOT, per-env level override); (i) NEGATIVAN: `base.py` source NE sadrži `LOGGING_CONFIG = None` (G-3 guard)
**And** NIJEDAN test ne zahteva browser/Playwright (`needs_e2e=false`)
**And** testovi su robusni na native-Windows libmagic baseline (subprocess `python -c` ILI import-light koji izbegava admin autodiscover — vidi Host caveat)

---

## Tasks / Zadaci

**Task 1 — `LOGGING` dict u `config/settings/base.py` (AC1, AC2, AC3, AC4, AC6, AC7, SM-D1..D8)**
1.1. Dodaj `import sys` (za `ext://sys.stdout` referencu nije nužan import u dict-u — string-form je dovoljan; ali ako koristiš programatski `sys.stdout`, importuj). Preferiraj string-form `"stream": "ext://sys.stdout"` (dictConfig razrešava ext:// referencu — NE zahteva `import sys` u settings-u).
1.2. Definiši `LOGGING = { "version": 1, "disable_existing_loggers": False, "formatters": {...}, "handlers": {...}, "loggers": {...}, "root": {...} }`.
   - `formatters`: `verbose` Django-native (`"format": "{levelname} {asctime} {name} {module} {process:d} {thread:d} {message}"`, `"style": "{"`) — zero-dep (SM-D2). NE `python-json-logger`.
   - `handlers`: `console` → `{"class": "logging.StreamHandler", "stream": "ext://sys.stdout", "formatter": "verbose", "level": "DEBUG"}` (handler propušta sve; loggeri/root filtriraju nivoom). NEMA file handler-a (SM-D1).
   - `loggers`: `django` (WARNING default), `django.request` (ERROR), `django.security` (ERROR), `apps` (INFO project logger, SM-D8). **KANONSKI OBRAZAC (SM-D8/G-12): svaki žičani logger je `{"level": <...>, "propagate": True}` BEZ sopstvenog `handlers` ključa** (ili praznog) — console handler je SAMO na `root`. Ovo istovremeno gasi dupli red (G-6) I čuva sentry-sdk propagaciju (SM-D3). **NE koristi `propagate: False` + sopstveni `console` handler** (gladuje Sentry — G-12). Per-logger tiše = preko `level`, NE preko propagacije. NE žičaj `django.db.backends`.
   - `root`: `{"handlers": ["console"], "level": env("DJANGO_LOG_LEVEL", default="INFO")}` (env-gated, SM-D9). **root i console handler `level` MORAJU ostati ≤ INFO** da sentry-sdk INFO+→breadcrumb radi (G-13).
1.3. Env-gated nivo: `DJANGO_LOG_LEVEL = env("DJANGO_LOG_LEVEL", default="INFO")` PRE `LOGGING` dict-a; koristi u root/project logger nivou. Production-safe default (INFO/WARNING, NE DEBUG).
1.4. NE diraj `disable_existing_loggers` na True; NE dodaj `mail_admins`/sentry/glitchtip handler (SM-D3/D5).

**Task 2 — Per-env tightening (AC5, AC8, SM-D6)**
2.1. `development.py`: loosen — npr. `LOGGING["loggers"]["django"]["level"] = "INFO"` + `LOGGING["loggers"]["apps"]["level"] = "DEBUG"` (verbose dev). ILI postavi `DJANGO_LOG_LEVEL` semantiku tako da dev default-uje verbose. Console ostaje stdout. NE diraj `propagate` (ostaje True — SM-D8/G-12).
2.2. `production.py`: tighten — KONKRETNI nivoi (AC3): `django` == WARNING (tiši; GlitchTip hvata ERROR+), `django.request` == ERROR, `django.security` == ERROR (ili WARNING), `apps` == INFO. NE re-definiši ceo dict; podesi SAMO `level` (SM-D6) — NE menjaj `propagate` na False (gladuje Sentry — G-12). NE spuštaj root/console handler `level` ispod INFO (breadcrumb-ovi — G-13). NE diraj sentry_sdk.init blok (AC7 regression).
2.3. Ako mutiraš nasleđeni `LOGGING` in-place u per-env modulu, koristi `copy.deepcopy(LOGGING)` ILI re-assignuj samo nested level key (NE deli mutabilnu referencu — G-7). Verifikuj da učitavanje dev pa prod daje RAZLIČITE nivoe.
2.4. `staging.py`: NE menja per-env LOGGING — nasleđuje base (production-like je dovoljno). sentry_sdk.init blok (`environment="staging"`, L42-48) ostaje NETAKNUT (AC7 regression guard paralelan production.py). NE dodavati staging-specifičan LOGGING tightening osim ako se eksplicitno zatraži.

**Task 3 — ops/journald retencija nota (SM-D7) — DEFER logrotate**
3.1. Dodaj kratak komentar u `base.py`/`production.py` (uz `LOGGING`) da je log retencija/rotacija HOST-level (journald `SystemMaxUse`/Docker `--log-opt max-size/max-file`), NE Django — mirror 9-5 host-cron. NE piši `/etc/logrotate.d/django`.
3.2. (OPCIONO, mašinski-realna zamena za logrotate) Dodaj `logging:` driver blok na `django` servis u `compose/production.yml`: `driver: "json-file"`, `options: { max-size: "10m", max-file: "5" }` — Docker-native rotacija (epics 14d aproksimacija → OQ-1). Ako dodaš, dokumentuj kao journald/Docker ekvivalent, NE Django LOGGING concern.

**Task 4 — `.env.example` log-level placeholder (AC opciono, SM-D9)**
4.1. Dodaj `DJANGO_LOG_LEVEL=` placeholder (prazan ili `# DJANGO_LOG_LEVEL=INFO` komentar) u relevantnu sekciju `.env.example`. Default je production-safe (INFO).

**Task 5 — Import-light testovi (AC9) — TEA RED faza**
5.1. `tests/test_logging_config.py` (ili proširi `tests/test_settings_split.py`): mirror `_read_settings_source` + `_load_settings_module`.
5.2. `dictConfig` validnost: `logging.config.dictConfig(base.LOGGING)` ne baca (u izolaciji — pazi da ne pregaziš pytest caplog/global logging state; po potrebi save/restore preko `logging.config` ili subprocess).
5.3. AC2 stdout: asertuj `LOGGING["handlers"]["console"]["stream"] == "ext://sys.stdout"` + class `logging.StreamHandler`.
5.4. AC3 loggeri prisutni + KONKRETNI prod nivoi (numeričko poređenje `logging.getLevelName` → int: `django`=WARNING/30, `django.request`=ERROR/40, `django.security`=ERROR/40 ili WARNING/30, `apps`=INFO/20); AC4 `disable_existing_loggers is False`; AC5 prod≠dev nivo (učitaj oba modula, **numeričko** poređenje nivoa NE string); AC6 ITERIRAJ preko SVIH `LOGGING["formatters"][*]["format"]` token-scan (regex za zabranjene token-e) + asertuj nema `mail_admins`/`AdminEmailHandler` + `django.server` odsutan iz loggers; AC7 nema sentry/glitchtip handler class + **nijedan žičani logger nema `propagate==False` sa nepraznim sopstvenim handlers (Sentry-starvation guard)** + production.py I staging.py sentry init netaknut (source grep); AC8 base-vs-per-env.
5.5. NEGATIVAN source test (AC9/SM-D6 guard): `_read_settings_source("base")` NE sme da matchuje regex `LOGGING_CONFIG\s*=\s*None` — sprečava da neko tiho onemogući primenu LOGGING dict-a (G-3). Test FAIL-uje ako je `LOGGING_CONFIG = None` prisutan u base.py source-u.
5.6. Host caveat: subprocess `python -c` ILI import-light koji izbegava libmagic admin autodiscover (mirror 9-3/9-4/9-5 host caveat).

**Task 6 — Manual review + scope guard**
6.1. Verifikuj `disable_existing_loggers=False` + nema sentry handler + prod≠dev nivo + 0 nove dep (SM-D2 zero-dep).
6.2. NE implementiraj: JSON formatter/python-json-logger (OQ-2), in-container file handler (SM-D1), logrotate config (SM-D7), per-app logger eksplozija (SM-D8/OQ-3). 0 migracija.

---

## Dev Notes

**Trenutna settings struktura.** `config/settings/` paket: `base.py` (SOT, `from .base import *` u per-env), `development.py` (DEBUG=True), `staging.py` (production-like + sentry `environment="staging"`), `production.py` (DEBUG=False, HSTS, sentry `environment="production"`). `env = environ.Env()` instanca u base.py:12 — pattern `env("VAR", default=...)` / `env.bool(...)` / `env.int(...)`. `LOGGING` dict trenutno NE postoji nigde — Django koristi svoj default logging config (koji `disable_existing_loggers` semantiku ostavlja Django-internoj `DEFAULT_LOGGING`).

**Kanonski test obrazac (`tests/test_settings_split.py`).** Import-light: `_read_settings_source(module_name)` čita `.py` source za regex/substring proveru BEZ import-a (bezbedno za pattern check). `_load_settings_module(module_name)` setuje test `DJANGO_SECRET_KEY`, briše `config.settings.*` iz `sys.modules`, pa `importlib.import_module` (svež import, pokupi env promene). Za AC5 (prod≠dev) učitaj oba modula kroz `_load_settings_module` i uporedi `LOGGING` nivoe. Za `dictConfig` validnost — pazi: `dictConfig` mutira globalni `logging` state; izoluj (subprocess ILI save/restore handler-a) da ne zagadiš pytest log capture.

**Reconciliacija framing (vidi SM-D1/D2/D7).** epics.md 9.6 opisuje file-handler+logrotate svet; stvarni deployment je Docker+journald stdout svet. 9.6 ispunjava epics INTENT (strukturisano + post-mortem + bez disk-fill-up-a) kroz **console→stdout** + host-level journald/Docker rotaciju. file handler/logrotate su NAMERNO izostavljeni iz Django sloja (anti-pattern u kontejneru bez volume-a). Ovo NIJE skraćivanje scope-a — to je tačan modern ekvivalent (mirror 9-5 host-cron, 9-4 stdout-capture pretpostavka).

**sentry-sdk koegzistencija (9-3).** sentry-sdk `[django]` default `LoggingIntegration`: `logging.ERROR`+ → GlitchTip event, `logging.INFO`+ → breadcrumb. SDK capture handler sedi na ROOT loggeru i hvata record-e kad PROPAGIRAJU do root-a. Radi AUTOMATSKI kroz `sentry_sdk.init` (production.py L79-87 / staging.py L42-48), NEZAVISNO od `LOGGING` dict-a. 9.6 `LOGGING` MORA: (1) NE dodavati Sentry handler (dupli report — SM-D3); (2) NE gušiti ono što SDK treba (`disable_existing_loggers=False` čuva SDK + django loggere — SM-D4); (3) NE dirati init blok (AC7 regression); (4) **NE preseći propagaciju** — žičani loggeri `propagate: True`, handler SAMO na root (G-12); (5) **root/handler level ≤ INFO** da INFO+→breadcrumb radi (G-13).

**Postojeći app getLogger pozivi.** Bar jedan app već koristi `logging.getLogger("apps.media_pipeline.pdf_utils")` (Story 2-4). Project logger `"apps"` (SM-D8) hvata sve `apps.*` jednim wiring-om kroz logger hierarhiju (Python logging propagation `apps.media_pipeline.pdf_utils` → `apps.media_pipeline` → `apps` → root).

## Gotchas

- **G-1 — `dictConfig` `disable_existing_loggers` default je `True` (footgun).** Ako izostaviš, dictConfig GASI sve loggere koji nisu eksplicitno u tvom dict-u (Django interni, sentry-sdk, third-party). `django.request`/`django.security`/SDK breadcrumb-ovi tiho prestaju. MORA `"disable_existing_loggers": False` eksplicitno (AC4/SM-D4).
- **G-2 — `StreamHandler` default stream je `sys.stderr`, NE stdout.** Za Docker/journald capture želiš stdout (12-factor). Eksplicitno `"stream": "ext://sys.stdout"`. Bez toga app log-ovi idu na stderr i mešaju se sa Gunicorn error stream-om (zbunjuje `docker logs` parsing).
- **G-3 — `LOGGING_CONFIG = None` vs default.** Django po default-u poziva `logging.config.dictConfig(DEFAULT_LOGGING)` pa MERGE-uje tvoj `LOGGING` (preko `LOGGING_CONFIG` callable). NE postavljaj `LOGGING_CONFIG = None` (to bi reklo Django-u da NE konfiguriše logging uopšte — tvoj dict se ne bi primenio osim ako sam ne pozoveš dictConfig). Drži default `LOGGING_CONFIG` (NE diraj ga) i samo definiši `LOGGING` dict.
- **G-4 — pytest hvata log-ove (`caplog`) + dictConfig globalni state.** `logging.config.dictConfig` mutira globalni logging registry. Test koji ga pozove može zagaditi pytest log capture za ostale testove. Izoluj: subprocess `python -c`, ILI u testu save/restore `logging` handler-e, ILI samo asertuj dict STRUKTURU (NE pozivaj dictConfig na živom interpreteru osim u izolaciji).
- **G-5 — `ext://sys.stdout` string-form NE zahteva `import sys` u settings-u.** dictConfig razrešava `ext://` referencu interno. Ako umesto toga upišeš programatski `"stream": sys.stdout`, MORAŠ `import sys` u base.py. Preferiraj string-form (manje import noise).
- **G-6 — dupli red u konzoli zbog propagate + handler na više loggera.** Ako `django` ima `console` handler I `propagate: True`, a `root` takođe ima `console` handler — log se ispiše DVAPUT. Pravilo: ili handler na konkretnom loggeru sa `propagate: False`, ili handler SAMO na root + loggeri bez handler-a (propagate ka root). NE oboje. Test render može uhvatiti dupli red.
- **G-7 — per-env in-place mutacija deljene `LOGGING` reference.** `from .base import *` donosi REFERENCU na isti dict. Ako `development.py` radi `LOGGING["loggers"]["django"]["level"] = "DEBUG"` a `production.py` `= "WARNING"` — pošto test učitava oba modula u istom procesu (`_load_settings_module` reload-uje ali deli `base` import semantiku), mutacija MOŽE cross-kontaminirati ako se deli ista nested reference. Koristi `copy.deepcopy(LOGGING)` u per-env modulu PRE mutacije, ILI re-assignuj kompletan nested dict. AC8 testira da prod≠dev opstaje.
- **G-8 — `django.db.backends` SQL log = noise + PII rizik.** NE žičaj ga (ostaje default OFF). Na DEBUG nivou loguje SVAKI SQL query (uključujući parametre — potencijalno PII/lozinke u WHERE). Eksplicitno NE u `loggers` (SM-D8).
- **G-9 — Host-Windows pytest libmagic baseline.** Native Windows `pytest` collect pada (libmagic missing — pre-existing baseline kroz ceo Epic 9, NIJE regresija). LOGGING testovi: subprocess `python -c` ILI import-light koji izbegava admin autodiscover (mirror 9-3/9-4/9-5). `_read_settings_source` (regex source-check) ne triggeruje import → bezbedan na host-u.
- **G-10 — `style="{"` mora pratiti `{}` format placeholdere.** Django-native formatter sa `"{levelname} ..."` zahteva `"style": "{"`. Ako koristiš `%(levelname)s` stil, `style` je `"%"` (default). Ne mešaj — `{}` placeholderi sa `%` style-om → KeyError pri prvom log emit-u (ne pri dictConfig — latentno).
- **G-11 — production.py:75 komentar postaje stale.** L75 kaže „NE konfiguriše LOGGING dict (9.6)". Pošto 9.6 SADA konfiguriše (u base.py), ažuriraj/ukloni taj zastareli komentar da ne zbunjuje (npr. „LOGGING dict u base.py — 9.6; ovde samo per-env tightening"). PAŽNJA: edit komentara NE sme pomeriti/oštetiti sentry_sdk.init blok odmah ispod (L76-87) — AC7 regression guard (live regression-surface; potvrđeno u DoD).
- **G-12 — `propagate: False` + per-logger handler GLADUJE sentry-sdk LoggingIntegration (#1 koegzistencijski footgun).** sentry-sdk instalira capture handler na ROOT logger i hvata record-e kad PROPAGIRAJU naviše do root-a. Ako žičani logger (`django`/`django.request`/`django.security`/`apps`) ima `propagate: False` UZ sopstveni `console` handler, record se zaustavi na tom loggeru → NIKAD ne stigne do root-a → GlitchTip NE dobija ni ERROR event ni INFO breadcrumb (tiha kontradikcija AC7/SM-D3). **Kanonski obrazac: console handler SAMO na `root`; žičani loggeri `propagate: True` (ili izostavljen) BEZ sopstvenog handler-a.** Ovo istovremeno gasi dupli red (G-6). Per-logger tiše = preko `level`, NIKAD preko `propagate: False` + handler. Test (AC7) FAIL-uje na `propagate==False` + neprazan sopstveni `handlers`.
- **G-13 — root/console-handler `level` mora ostati ≤ INFO za Sentry breadcrumb-ove.** sentry-sdk LoggingIntegration default-uje `breadcrumb_level=INFO` — INFO+ record-i postaju breadcrumb-ovi, ali samo ako stignu kroz logging pipeline (root level ≤ INFO ih propušta). Ako se root ILI console handler `level` digne na WARNING (npr. `DJANGO_LOG_LEVEL=WARNING` na root-u), INFO record-i se filtriraju PRE nego što SDK breadcrumb handler vidi → degradirani breadcrumb-ovi (manje konteksta uz GlitchTip event). **Pravilo: root i console handler ostaju ≤ INFO. Ako ops želi tiše logove, tighten PER-LOGGER preko `level` (npr. `django` na WARNING), NE root/handler level.** `DJANGO_LOG_LEVEL=WARNING` na root-u svesno degradira Sentry breadcrumb-ove — dokumentovano ops-u.

## Open Questions

- **OQ-1 (TVRD go-live gate) — finalna log retencija na host/journald nivou (AR-21/epics 14d ops zahtev).** epics 14d/compress logrotate → u Docker svetu: journald `SystemMaxUse=`/`MaxRetentionSec=14day` ILI Docker `--log-opt max-size/max-file` na `django` servisu. Koja TAČNA host konfiguracija (journald globalno vs per-container Docker logging driver) + da li 14d retencija mapira na journald MaxRetentionSec ili Docker max-file count. **TVRD go-live gate (istom formulacijom kao OQ-ovi u 9-2/9-5): realan AR-21/epics ops zahtev koji BEZ host konfiguracije NIJE ispunjen** — 9.6 Django sloj isporučuje strukturisan stdout (SM-D7) ali host retencija/rotacija mora biti postavljena na serveru pre go-live. **Mihas/ops odluka + host config pre go-live.** 9.6 dokumentuje (SM-D7) ali ne forsira host journald config iz Django koda.
- **OQ-2 (go-live gate) — da li je `python-json-logger` JSON format poželjan u prod-u.** SM-D2 odlučio zero-dep verbose u v1. Ako biznis/ops uvedu log aggregator (Loki/ELK/Datadog) koji traži mašinski-parsabilan JSON → usvojiti `python-json-logger` (+1 dep + `JsonFormatter`). **Mihas/ops odluka** — trigger je postojanje JSON konzumenta (YAGNI do tada).
- **OQ-3 — da li su potrebni per-app logger-i van jednog `apps` project logger-a.** SM-D8 wire-uje jedan `apps` root project logger (hvata sve `apps.*`). Ako neki app treba zaseban nivo (npr. `apps.forms` verbose za debug lead-send-a a ostalo tiho) → dodati ciljani logger tada. **Defer dok ne postoji konkretna potreba** (YAGNI).

---

## Host caveat (za Dev/TEA)

Native Windows `pytest` **ne može da collect-uje** (libmagic missing — `python-magic` zahteva system `libmagic`; **pre-existing baseline** kroz ceo Epic 9, NIJE regresija ove story). LOGGING testovi su dizajnirani da to zaobiđu:
- `_read_settings_source` (regex/substring source-check) NE import-uje modul → bezbedan na host-u.
- `dictConfig` validnost + module-load (`_load_settings_module`) = subprocess `python -c "import config.settings.base; logging.config.dictConfig(...)"` ILI import-light koji izbegava admin autodiscover kroz pytest-django conftest (koji bi triggerovao libmagic).
- Svi testovi se izvršavaju na host/CI bez živog stack-a (no network, no Docker za core LOGGING testove; opcioni compose `logging:` driver test skip-uje ako docker nije na PATH-u — mirror 9-1).

## Definition of Done

- [x] AC1-AC9 zadovoljeni
- [x] `LOGGING` dict u `config/settings/base.py` (console→stdout, `disable_existing_loggers=False`)
- [x] `logging.config.dictConfig(LOGGING)` validan (ne baca)
- [x] console handler `ext://sys.stdout` (NE stderr); NEMA in-container file handler default-a
- [x] žičani `django`/`django.request`/`django.security`/`apps`; `django.db.backends` NIJE žičan; `django.server` NIJE žičan
- [x] kanonski obrazac: console handler na `root`, žičani loggeri `propagate: True` BEZ sopstvenog handler-a (NE `propagate: False` + handler — G-12 Sentry-starvation guard)
- [x] root i console handler `level` ≤ INFO (Sentry breadcrumb-ovi — G-13); ops tightening ide PER-LOGGER preko `level`
- [x] prod nivo ≠ dev nivo (per-env tightening; base = SOT dict); KONKRETNI prod nivoi (django=WARNING, django.request=ERROR, django.security=ERROR/WARNING, apps=INFO)
- [x] format string (SVI formatteri) bez PII/secret token-a; nema `mail_admins`/`AdminEmailHandler`/sentry handler u LOGGING
- [x] `base.py` NE sadrži `LOGGING_CONFIG = None` (G-3 negativni source test)
- [x] production.py I staging.py sentry_sdk.init blok NETAKNUT (AC7 regression); base/development bez sentry init
- [x] production.py:75 stale komentar ažuriran (G-11) — edit NE pomera sentry init blok L76-87
- [x] 0 nove dependency (SM-D2 zero-dep verbose; python-json-logger NE u v1)
- [x] logrotate config NE napisan (SM-D7 host/journald nota umesto)
- [x] `just lint` clean (ruff)
- [x] TEA import-light testovi prolaze (host caveat zaobiđen subprocess/import-light)
- [x] 0 migracija (verifikovano)
