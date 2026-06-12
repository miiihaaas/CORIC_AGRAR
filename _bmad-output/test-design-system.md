# Test Design — System / Epic Strategy — CORIC_AGRAR

**Projekat:** CORIC_AGRAR (Ćorić Agrar — public sajt + admin CMS)
**Autor:** TEA (Master Test Architect)
**Datum:** 2026-06-12
**Tip:** Konsolidovana test-strategija; E2E Strategy Map za Epic Orchestrator runtime-konzumaciju.

## Svrha i opseg

Ovaj fajl je **glue contract** koji Epic Orchestrator čita u `step-00-init.md §0.4` da izgradi `test_strategy_map` i u `step-01a-tea-atdd.md` da generiše RED-fazne Playwright E2E po story-ju.

**SCOPE NOTE:** Epici 1–8 su **DONE** (implementirani, review-ovani, merge-ovani). Ova mapa se **live-konzumira samo za Epic 9** (Go-Live Readiness). Sekcije za Epic 9 su jedine koje runtime parser čita; sve ostalo je human-readable kontekst.

### Done epics (1–8) — nije runtime-konzumirano

Informativno (parser ovo NE čita): Epici 1–8 su završeni i imaju sopstvenu pytest/integration coverage. E2E backbone (3 user journeys) namerno je rezervisan za Epic 9 (story 9-8), jer zahteva ceo stack 1–8 + seed data (9-7) pre nego što ima smisla voziti ga end-to-end. Zato ova mapa ne sadrži E2E unose za stories 1-x..8-x — oni nisu u live epicu.

---

## Testing konvencije (iz project-context.md — obavezujuće za 9-8/9-9)

- **E2E framework:** Playwright (`playwright >= 1.60.0`); fajlovi u `tests/e2e/test_<journey>.py`.
- **Per-locale variants:** svaki journey za **sr (primarni) + 1 sample za hu/en** (po fixture-u).
- **Selectors:** preferirati `data-testid` atribut pre CSS klase.
- **Wait strategy:** `await expect(locator).toBeVisible()` — NIKAD `sleep`.
- **CI:** headless u CI; headed lokalno (`PWDEBUG=1`). E2E se vozi na **staging push**, ne na main (presporo).
- **Page object pattern:** `tests/e2e/page_objects/` (ili `apps/<app>/page_object.py`).
- **Critical paths MORAJU imati testove:** auth, lead form submit, admin product save, locale routing.

---

## Epic 9 — Production, Deployment & Hardening (Go-Live Readiness)

Epic 9 je infrastruktura + kvalitet pred launch. Većina stories je ops/infra/asset (bez browser-E2E koristi); E2E težina je koncentrisana u **9-8** (3 user journeys), sa **9-7** kao seed-data prerekvizitom i **9-9** kao audit-gate-om (a11y/perf alat, ne novi user-journey E2E).

### E2E Strategy Map (machine-parseable — Epic Orchestrator čita ovaj blok)

```
9-1-production-docker-compose-nginx-config: { needs_e2e: false, e2e_count: 0 }
9-2-hetzner-deployment-script-ssl: { needs_e2e: false, e2e_count: 0 }
9-3-glitchtip-6-self-host-setup: { needs_e2e: false, e2e_count: 0 }
9-4-uptimerobot-konfiguracija: { needs_e2e: false, e2e_count: 0 }
9-5-pg-dump-restic-hetzner-storage-box-backup: { needs_e2e: false, e2e_count: 0 }
9-6-django-logging-konfiguracija: { needs_e2e: false, e2e_count: 0 }
9-7-sample-seed-data-fixtures: { needs_e2e: false, e2e_count: 0 }
9-8-playwright-e2e-testovi-za-3-uj-a: { needs_e2e: true, e2e_count: 3 }
9-9-a11y-audit-performance-load-test: { needs_e2e: false, e2e_count: 0 }
9-10-webp-avif-final-lighthouse-pass: { needs_e2e: false, e2e_count: 0 }
```

**Ukupno očekivanih E2E specs za Epic 9: 3** (sva tri u story 9-8; svaki spec parametrizovan za sr + 1 sample hu/en).

---

### Per-story risk + testability beleške

#### 9-1-production-docker-compose-nginx-config — `needs_e2e: false`
- **Scope:** `compose/production.yml` (postgres, django/Gunicorn, nginx, glitchtip) + `nginx.conf` (HTTPS termination, gzip, static fallback, security headers).
- **Risk:** Srednji — misconfig security headera ili static routing-a. **Testability:** infra-verify, ne browser-E2E. Validira se preko `docker compose up` smoke + curl asercija na header-e (`X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`) i static serve путању. Nema user-journey vrednosti — **false**.

#### 9-2-hetzner-deployment-script-ssl — `needs_e2e: false`
- **Scope:** `ops/deploy/deploy.sh` (SSH, git pull, compose up, migrate, collectstatic) + certbot Let's Encrypt + GitHub Actions deploy.yml + `rollback.sh`.
- **Risk:** Visok (deploy/rollback put), ali **testability** je CI/shell-script + manuelni staging deploy verify, ne Playwright. SSL handshake se proverava `openssl s_client`/curl-om. Rollback je shell test. **false** — ops put, ne browser.

#### 9-3-glitchtip-6-self-host-setup — `needs_e2e: false`
- **Scope:** `ops/monitoring/glitchtip-compose.yml` + `SENTRY_DSN` u production.py + sentry-sdk[django] + email alerting.
- **Risk:** Srednji. **Testability:** trigger 500 kroz test view → verifikacija da se greška pojavi u GlitchTip dashboard-u (manuelni/integration smoke), ne user journey. **false**.

#### 9-4-uptimerobot-konfiguracija — `needs_e2e: false`
- **Scope:** Eksterni SaaS monitori (staging/prod/glitchtip URL, 5min interval, email alert).
- **Risk:** Nizak. **Testability:** konfiguracija u eksternom alatu; verifikacija ručna (monitor zelen). Nema kod-a za E2E. **false**.

#### 9-5-pg-dump-restic-hetzner-storage-box-backup — `needs_e2e: false`
- **Scope:** `pg_backup.sh` + `media_backup.sh` (restic encrypt, rclone push), cron 3am, retention policy, `restore.sh`.
- **Risk:** Visok (disaster recovery), ali **testability** je shell/integration: izvrši backup → verifikuj encrypted arhivu na Storage Box-u → restore na lokal i diff. **false** — nije browser put.

#### 9-6-django-logging-konfiguracija — `needs_e2e: false`
- **Scope:** `LOGGING` dict (JSON formatter, file handler, log-level), logrotate config.
- **Risk:** Nizak. **Testability:** unit/integration — emituj log, assert JSON struktura u fajlu; logrotate dry-run. **false**.

#### 9-7-sample-seed-data-fixtures — `needs_e2e: false` (ali E2E PREREKVIZIT)
- **Scope:** `tests/fixtures/sample_data.json` (3 brenda, 3 serije, 10–15 proizvoda, 5 polovnih, 3–5 blog, SiteSettings, 1 superadmin).
- **Risk:** Srednji — ako `loaddata` pukne ili sadržaj nedostaje, **9-8 E2E ne može da se vozi**. **Testability:** `loaddata` smoke + render-asercija (sve sekcije imaju realan content, ne Lorem). Sam po sebi nema browser-journey, ali je **HARD DEPENDENCY za 9-8** — seed mora postojati pre nego što ATDD za 9-8 ima determinističke podatke (Agri Tracking TB804, HZM 812T, slug-ovi). **false**, uz napomenu: orchestrator treba da osigura redosled 9-7 → 9-8.

#### 9-8-playwright-e2e-testovi-za-3-uj-a — `needs_e2e: true, e2e_count: 3`
- **Scope:** THE E2E story. `tests/e2e/conftest.py` (Playwright fixture) + 3 test fajla, page object pattern, `just e2e` protiv staging URL-a.
- **Risk:** Visok — pokriva critical revenue/lead paths. **Prerekvizit:** Epici 1–8 DONE + seed data 9-7.
- **e2e_count = 3** → **tri spec fajla, jedan po journey-u**. Po project-context-u svaki journey ima **sr (primarni, pun journey) + 1 sample hu/en** varijantu; locale varijante se **parametrizuju unutar istog spec fajla** (pytest `parametrize` / Playwright fixture), NE kao zasebni fajlovi — zato je count 3 specs, ne 9. ATDD (step-01a) treba da generiše 3 RED specs sa locale-parametrizacijom.

  **Spec breakdown (kontekst za step-01a ATDD generaciju):**

  - **`test_marko_buys_traktor.py` (UJ-1 — anon, desktop):**
    `/` → klik *Traktori* → `/sr/traktori` listing → HTMX live-filter (range slider snaga > 60 KS, cena ≤ 25.000 €) → klik kartica *Agri Tracking TB804* (cela kartica klikabilna) → `/sr/proizvod/agri-tracking-tb804` → galerija/Lightbox, Specifikacije akordion (Motor default-open) → skrol do *„Imate pitanja?"* forme (polje *Model* auto-popunjeno) → popuni 5 polja (Ime, Email, Telefon, Model, Poruka) → submit → **assert** success kartica *„Hvala! Vaš upit je primljen."*.
    Locale sample: ponovi core flow na `/hu/` ili `/en/` ekvivalentnom slug-u (locale-aware slug, `<html lang>` ažuriran).
    Selektori: `data-testid` na filter slider-ima, product kartici, form poljima, success kartici. Wait: `expect(success).toBeVisible()`.

  - **`test_stojan_service_request.py` (UJ-2 — anon, MOBILE viewport):**
    Mobile viewport (<768px, hamburger) → `/sr/servis` → popuni servisnu formu (Ime, Telefon, Email opciono, Vrsta mehanizacije dropdown, Brend/model slobodan unos, Opis kvara) → *Dodaj sliku* (file upload, thumbnail preview, X za uklanjanje) → submit → **assert** success *„Vaš servisni zahtev je primljen…"*.
    Edge: foto > 5MB → greška PRE upload-a (opciono u istom spec-u).
    Locale sample: 1 hu/en varijanta servis forme.
    Selektori: `data-testid` na mobile nav toggle, form polja, file input, preview thumbnail, success.

  - **`test_marijana_adds_product.py` (UJ-3 — ADMIN, auth):**
    `/admin-coric/` login (email+lozinka) → dashboard → *DODAJ PROIZVOD* → forma: Osnovno (Naziv, opis, kategorija, brend, serija, 3 ključne karakteristike) + Specifikacije akordion + Galerija multi-upload + (po potrebi brošura) → unos na **SR**, HU/EN prazno → status **Skica** → Sačuvaj → re-open → status **Objavljeno** → **publish-gate validacija** (SR Naziv + ≥1 slika galerije + ≥1 sekcija specifikacija) → **assert** success toast *„Proizvod 'HZM 812T' je objavljen."*.
    Edge: pokušaj objave bez SR sadržaja → blokirano sa linkom na nedostajuća polja.
    Locale sample: admin UI je primarno sr; sample varijanta pokriva locale-switch taba u formi (SR→HU prazno) umesto pun preprod.
    Selektori: `data-testid` na login formi, dashboard *DODAJ PROIZVOD*, form taba, upload widget, status toggle, publish toast. NAPOMENA: admin je na `/admin-coric/` (Epic 8 hardening, van i18n prefiksa).

#### 9-9-a11y-audit-performance-load-test — `needs_e2e: false`
- **Scope:** axe-core/Pa11y na ključne strane (`/`, `/traktori`, `/proizvod/<slug>`, `/kontakt`, `/admin-coric/`) + Lighthouse CI + manuelni keyboard-only test 3 UJ + NVDA screen-reader test 1 UJ + GitHub Issue za remediaciju.
- **Risk:** Visok (WCAG 2.1 AA + perf budget = go-live gate: 0 critical a11y, Lighthouse a11y ≥95, LCP <2.5s, TTFB <600ms, page weight <1.5MB).
- **Testability / E2E odluka:** **false** — uz svesno scope-ovanje. axe/Lighthouse jesu browser-driven, ALI to su **audit-gate alati** (Pa11y/Lighthouse CI kao zaseban CI step), **ne novi Playwright user-journey E2E specs** pod ovim harness-om koji orchestrator brojač (`e2e_count`) cilja. Manuelni keyboard + NVDA su po definiciji ručni (ne automatizovani specs). Ako se tim kasnije odluči da poveže `axe-playwright` skenove u postojeća 3 UJ spec-a iz 9-8, to su **asercije unutar 9-8 specova**, ne dodatni `e2e_count` za 9-9. Zato 9-9 ne traži RED-fazni Playwright scaffold od step-01a. **Assumption (logovan):** epics.md ne navodi load-test alat (locust/k6) eksplicitno — „load test" se tretira kao perf-budget verifikacija preko Lighthouse + ad-hoc load alata posle staging deploy-a (architecture.md §951 traži load test post-staging). Ako produkt zahteva dedicated load-test automatizaciju kao gate, to je NFR-audit task, i dalje van Playwright E2E count-a.

#### 9-10-webp-avif-final-lighthouse-pass — `needs_e2e: false`
- **Scope:** sorl-thumbnail `THUMBNAIL_FORMAT_FALLBACK = ['avif','webp','jpg']` + `<picture>` template-i (avif/webp/jpg fallback) + final Lighthouse pass (a11y ≥95, LCP <2.5s, best practices ≥90, SEO ≥95).
- **Risk:** Srednji (perf/asset optimizacija; risk od pokvarenog fallback-a za legacy browser). **Testability:** template/asset verify + Lighthouse CI gate (isti audit-alat kao 9-9). Provera formata kroz Network tab / `<source type>` asercija je content-test, ne user journey. Final Lighthouse je audit-gate, ne Playwright spec. **false**.

---

## Sažetak za orchestrator

| Story | needs_e2e | e2e_count |
|---|---|---|
| 9-1-production-docker-compose-nginx-config | false | 0 |
| 9-2-hetzner-deployment-script-ssl | false | 0 |
| 9-3-glitchtip-6-self-host-setup | false | 0 |
| 9-4-uptimerobot-konfiguracija | false | 0 |
| 9-5-pg-dump-restic-hetzner-storage-box-backup | false | 0 |
| 9-6-django-logging-konfiguracija | false | 0 |
| 9-7-sample-seed-data-fixtures | false | 0 (E2E prereq za 9-8) |
| 9-8-playwright-e2e-testovi-za-3-uj-a | **true** | **3** |
| 9-9-a11y-audit-performance-load-test | false | 0 (audit-gate, ne Playwright journey) |
| 9-10-webp-avif-final-lighthouse-pass | false | 0 |

**Total Epic 9 E2E specs: 3** (UJ-1 Marko, UJ-2 Stojan, UJ-3 Marijana — svaki sr + 1 sample hu/en parametrizovan).

**Redosled-zavisnost:** 9-7 (seed) MORA pre 9-8 (E2E) — bez fixture-a 9-8 nema determinističke podatke.
