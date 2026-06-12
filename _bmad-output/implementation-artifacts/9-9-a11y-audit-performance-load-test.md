---
story-id: 9-9-a11y-audit-performance-load-test
title: A11y Audit + Performance Load Test (audit harness + budgeti + baseline nalazi)
epic: 9
module: ops/quality + CI tooling (NIJE Django app)
status: ready-for-dev
risk-tier: MEDIUM
base-branch: epic-9
depends_on: [9-7, 9-8, 9-2]
forward-dep: [9-10]
needs_e2e: false
e2e_count: 0
---

# Story 9.9: A11y Audit + Performance Load Test

Status: ready-for-dev

## Opis (Description)

As a **dev**,
I want **audit accessibility-a (WCAG 2.1 AA) i performance budget + load test harness pre launch-a**,
so that **WCAG 2.1 AA i performance budget targeti budu verifikovani na staging-u/CI pre go-live, a fail-ovane stavke završe kao GitHub Issue za remediation**.

**SPECIJALNA STORY — deliverable je AUDIT/QUALITY TOOLING, ne nova feature i NE novi user-journey.**
Ova story postavlja **harness + budgete + baseline nalaze**, NE garantuje zelene brojeve na ovom
hostu. Sastoji se od:

1. **A11y audit spec** — `axe-playwright` (axe-core) integrisan u POSTOJEĆI Story 9-8 `tests/e2e/`
   Playwright harness (reuse `conftest.py` fixtures + page objects + `seed_e2e_data`), kao **zaseban
   a11y spec** (`tests/e2e/test_a11y_audit.py`) markiran posebnim `a11y` markerom — **NE duplira 3 UJ
   journey-ja** (axe je audit-gate, ne user-flow). Skenira ključne strane: `/`, `/sr/traktori/`,
   `/sr/proizvod/agri-tracking-tb804/`, formu (`/sr/kontakt/` ili model-inquiry forma), blog post,
   `/admin-coric/` (login-gated).
2. **Lighthouse CI budget config** — `lighthouserc` (lighthouse-ci) sa **budget thresholdovima**
   (a11y ≥ 95, LCP < 2.5s, TTFB < 600ms, total page weight < 1.5MB) + GitHub Actions workflow koji
   ih izvršava (mirror 9-8 `e2e.yml` self-contained job pattern).
3. **Load test** — `k6` skripta (`ops/perf/load_test.js`) + runbook (`ops/perf/README.md`) sa
   dokumentovanim thresholdovima. epics.md NE imenuje load tool → SM-D5 bira k6 (vidi SM odluke).
4. **MANUAL audit checklist** — `ops/quality/a11y-manual-checklist.md` (keyboard Tab/Esc, focus
   management, `prefers-reduced-motion`, kontrast 4.5:1, NVDA screen-reader 1-UJ).
5. **AUDIT REPORT artefakt** — `ops/quality/AUDIT-REPORT.md` (nalazi + jeftine popravke primenjene
   ovde + „fail item → GitHub Issue" putanja za remediation).

**Host/CI realnost (KRITIČNO — vidi Dev Notes):** native Windows host pytest collection pada na
`libmagic` (dokumentovan baseline kroz Epik 9), a Playwright browseri + Lighthouse (Chrome headless)
+ k6 binarni **verovatno NE mogu da se izvrše na ovom Windows hostu**. **Autoritativno a11y/perf
merenje je staging/CI.** Story zahteva korektnu konfiguraciju harness-a + budgete + RED/baseline
potvrdu — **NE zahteva fabrikovane brojeve.** Stvarni Lighthouse skor, axe-green, load-test brojevi i
NVDA pass su **staging/CI go-live gate** (OQ-1..OQ-4). Iskrenost iznad zelene lampice.

**SCOPE-DEFER (TVRD):** Story **9.10 (WebP/AVIF konverzija + FINALNI Lighthouse pass) ostaje
DEFERRED.** 9.9 postavlja audit harness + baseline nalaze. **NE radi image-format konverziju ovde.**
Ako audit otkrije image-weight problem (LCP/page-weight), story to **zabeleži kao „NOTE za 9.10"** u
AUDIT-REPORT.md — NE konvertuje.

**Konzumira 9-7 seed** (deterministički audit ciljevi) i **9-8 Playwright harness** (reuse
`conftest.py` + page objects + `seed_e2e_data`). Audit cilja iste determinističke slug-ove:
`agri-tracking-tb804`, traktori listing, model-inquiry/kontakt forma, blog post, admin.

## Acceptance Criteria

- [ ] **AC1 — A11y audit spec (axe-core) integrisan u 9-8 Playwright harness, ZASEBAN od 3 UJ-a.**
  `tests/e2e/test_a11y_audit.py` postoji, markiran `pytestmark = pytest.mark.a11y` (NOVI marker,
  registrovan u `pyproject.toml [tool.pytest.ini_options].markers`, **različit od `e2e`** da
  `just e2e` i `just a11y` budu razdvojeni). Spec **reuse-uje** 9-8 `conftest.py` fixtures
  (`base_url`, `e2e_data`/`seed_e2e_data`, `dev_superuser` za admin stranu) i page objects — **NE
  duplira UJ-1/2/3 journey-je** (axe je audit-gate, ne user-flow; `needs_e2e=false`, `e2e_count=0`).
  Koristi `axe-playwright-python` (ili ekvivalentni `Axe` runner koji injektuje `axe.min.js` i poziva
  `axe.run()`) — vidi SM-D1.

- [ ] **AC2 — Axe skenira ključne strane pokrivajući WCAG 2.1 AA, 0 critical issue-a kao gate.**
  Spec skenira (svaka strana = zaseban test/parametrize case): (a) `/` (home), (b) `/sr/traktori/`
  (listing), (c) `/sr/proizvod/agri-tracking-tb804/` (product detail + galerija), (d) forma —
  `/sr/kontakt/` ILI model-inquiry forma na product detail strani, (e) blog post detail —
  **TAČNA URL: `/sr/blog/pet-saveta-za-prolecnu-setvu/`** (deterministički seedovan slug, isti
  ugovorni status kao `agri-tracking-tb804`; potvrđeno `seed_sample_data.py` `_BLOG_POSTS[0].slug`
  + `apps/blog/urls.py` `blog:detail` ruta `blog/<slug:slug>/` uključena na i18n root → sa `/sr/`
  prefiksom). Parametrize MORA gађati **ovaj tačan URL** — 404 (pogrešan slug) bi dao false-pass
  (axe ne nađe violation jer nema sadržaja). (f) `/admin-coric/` (login-gated — koristi
  `dev_superuser` fixture). Axe se konfiguriše na **WCAG 2.1 AA tagove** (`wcag2a`, `wcag2aa`,
  `wcag21a`, `wcag21aa`). **Gate: 0 `critical` (i `serious`) impact violation** po strani (assert na
  `results["violations"]` filtriran po impact-u). Manje ozbiljni nalazi (`moderate`/`minor`) se
  **logују u AUDIT-REPORT, NE fail-uju build** (SM-D2 — baseline pragmatizam).

- [ ] **AC2b — Axe sken POSLE HTMX swap-a (dinamički DOM, ne samo initial load).**
  Pored static `page.goto → axe.run` skenova (AC2 a–f), spec MORA imati **bar jedan parametrize/test
  case koji pokreće HTMX interakciju, a zatim skenira RE-renderovani DOM**: npr. submit traktori
  filtera na `/sr/traktori/` (HTMX `hx-get`/`hx-post` koji zameni listing fragment) ILI submit
  kontakt/model-inquiry forme — pa `axe.run()` POSLE swap-a (čekaj na HTMX-settled stanje, npr.
  `page.wait_for_selector` na swap-ovani target / `hx-on::after-settle` ili Playwright
  `expect(...).to_be_visible()` na novi fragment). **Razlog (project-context #1 aria-live OOB + #3
  focus management posle HTMX swap-a = NAJVEĆI a11y rizik projekta):** static-load axe ne vidi
  dinamički ubačen markup, pa OOB aria-live regioni i post-swap fokus ostaju nepokriveni ako se
  skenira samo initial load. Gate je isti (0 `critical`/`serious`); ovaj case obezbeđuje da axe vidi
  i swap-ovani DOM, ne samo prvu boju. (Keyboard/fokus-traversal posle swap-a ostaje manual — AC6(b)
  „focus management posle HTMX swap" — ali bar STATIČKE post-swap WCAG violacije se sada automatski
  hvataju.)

- [ ] **AC3 — Lighthouse CI budget config sa thresholdovima.**
  `lighthouserc.json` (ili `.lighthouserc.cjs`) postoji u repo root-u (ili `ops/quality/`) sa
  `ci.assert` budget asercijama: **a11y kategorija ≥ 0.95**, **LCP < 2500ms**, **TTFB
  (`server-response-time`) < 600ms**, **total byte weight (`total-byte-weight`) < 1.5MB (1572864 B)**.
  `ci.collect.url` lista cilja iste ključne strane (`/`, `/sr/traktori/`,
  `/sr/proizvod/agri-tracking-tb804/`, forma, blog post). `numberOfRuns ≥ 3` (median, smanji flake).
  **Admin strana je IZUZETA** iz Lighthouse perf budgeta (login-gated, nije javni LCP target) — vidi
  SM-D3.

- [ ] **AC4 — Lighthouse CI GitHub Actions workflow (self-contained, mirror 9-8 e2e.yml).**
  `.github/workflows/lighthouse.yml` postoji, **self-contained** (ephemeral Postgres service +
  Django runserver u pozadini + `seed_e2e_data --force` + Chrome headless + `@lhci/cli autorun`),
  cilja `E2E_BASE_URL=http://localhost:8000` (mirror 9-8 `e2e.yml` job strukture). Vozi se na
  **`staging` push** (NE `master`/PR — suviše sporo, mirror 9-8 AC7) + `workflow_dispatch`. Budget
  fail = **`continue-on-error: true` na `lhci assert` koraku u v1** (baseline-collect mod) ILI hard
  fail — vidi SM-D7 + OQ-1 (Mihas odlučuje hard-gate vs report-only za go-live).
  **Dva moda EKSPLICITNO razdvojena:**
  - **v1 default = self-contained CI runserver** (Postgres service + `runserver --insecure` +
    `E2E_BASE_URL=http://localhost:8000`). **Radi DANAS, bez ikakvih secret-a/live boxa**; brojevi su
    **INDIKATIVNI** (runserver static ≠ prod nginx/Whitenoise/Gunicorn → TTFB/page-weight nisu
    prod-reprezentativni). Ovo je ono što ova story isporučuje i može da se izvrši end-to-end u CI.
  - **staging-targeted mod = OQ-4 follow-up go-live gate.** Lighthouse/k6 protiv DEPLOY-ovanog
    staging-a (9-2) za **realne prod nginx/Whitenoise brojeve**; traži `STAGING_BASE_URL` +
    `DJANGO_SUPERUSER_PASSWORD` (+ eventualni LHCI token) GH secrets i live box. **NIJE deo v1** —
    konfiguriše se kad su secrets/staging spremni (OQ-1/OQ-4). Autoritativni brojevi za go-live
    dolaze IZ OVOG moda, ne iz v1 self-contained.

- [ ] **AC5 — k6 load test skripta + runbook + thresholdovi.**
  `ops/perf/load_test.js` (k6) postoji: ramp-up VU profil (npr. `stages` 0→20→50 VU preko ~2min),
  cilja read-heavy javne rute (`/sr/`, `/sr/traktori/`, `/sr/proizvod/agri-tracking-tb804/`, blog
  index) protiv env-driven `BASE_URL` (NIKAD hardkodovan prod URL). Dokumentovani `thresholds`:
  `http_req_duration: ['p(95)<600']` (TTFB-ekvivalent server response p95 < 600ms), `http_req_failed:
  ['rate<0.01']`. `ops/perf/README.md` runbook: kako pokrenuti (`k6 run`), protiv kog env-a (staging,
  NIKAD prod bez dogovora), kako čitati izlaz, koji su pragovi i šta znače. **NE pokreće se u CI v1**
  (load test protiv staging-a = manual go-live korak, OQ-2) — SM-D6.

- [ ] **AC6 — MANUAL audit checklist (keyboard / focus / reduced-motion / kontrast / NVDA).**
  `ops/quality/a11y-manual-checklist.md` postoji sa proverljivim stavkama mapiranim na
  project-context A11y must-haves: (a) **keyboard-only** Tab navigacija kroz 3 UJ-a (sve interaktivno
  dostupno), **Esc** zatvara modale/Lightbox/mobile-nav; (b) **focus management** posle HTMX swap
  (focus se vraća na trigger/target — vidi project-context #3); (c) **`prefers-reduced-motion`**
  respect (slider/animacije se gase); (d) **kontrast 4.5:1** (DESIGN.md tokeni — spot-check ključnih
  parova); (e) **NVDA (Windows) screen-reader** prolaz **bar 1 UJ** sa razumevanjem (form labels,
  aria-live announcement, heading struktura). Checklist je **manual go-live gate** (OQ-3) — NIJE
  automatizovan u v1.

- [ ] **AC7 — AUDIT REPORT artefakt sa nalazima + jeftine popravke + „fail → GitHub Issue" putanja.**
  `ops/quality/AUDIT-REPORT.md` postoji i dokumentuje: (a) **scope** (koje strane/alati/budgeti),
  (b) **baseline nalazi** (axe violations po strani po impact-u; Lighthouse skorovi PLACEHOLDER/„TBD
  na staging-u" ako nisu mereni na hostu — vidi AC8); (c) **jeftine popravke primenjene U OVOJ
  STORY-ji** (npr. nedostajući `alt`, `aria-label`, `lang`, focus-visible, kontrast token swap — male
  template delte; vidi SM-D4); (d) **„fail item → GitHub Issue" remediation putanja** (template/format
  issue-a: strana + alat + WCAG kriterijum + impact + predlog fix-a; svaki non-trivijalni fail koji se
  NE popravlja u 9.9 dobija Issue stub/lista za kreiranje); (e) **„NOTE za 9.10"** sekcija za svaki
  image-weight/format nalaz (NE konvertuj ovde — scope-defer); (f) **EKSPLICITAN disclaimer:
  axe-green ≠ dokazan WCAG 2.1 AA.** AUDIT-REPORT scope MORA jasno reći da automatizovani axe
  pokriva samo **~30–40% WCAG kriterijuma**; **kontrast, keyboard-only navigacija, focus-order/focus
  management, `prefers-reduced-motion` i screen-reader razumevanje** se NE dokazuju axe-om i zavise od
  **manual checklist-a (AC6) + NVDA pass-a (OQ-3)**. „0 critical axe violation" je NUŽAN ali NE
  DOVOLJAN uslov za AA — izbegava lažni utisak da je AA automatski dokazan.

- [ ] **AC8 — HOST/CI caveat eksplicitno enkodiran: merenje je staging/CI, NE host.**
  Story artefakti (AUDIT-REPORT.md + workflow komentari + Dev Notes) eksplicitno beleže: **stvarni
  axe-green, Lighthouse brojevi, k6 rezultati i NVDA pass su staging/CI go-live gate (OQ-1..OQ-4), NE
  ovaj Windows host.** Lighthouse skorovi u AUDIT-REPORT v1 su **„TBD — staging Lighthouse run"** ako
  nisu izmereni — **fabrikovani brojevi su ZABRANJENI** (iskrenost iznad zelene). Harness MORA biti
  korektno konfigurisan (budgeti, tagovi, URL-ovi) i RED/baseline-potvrđen (struktura validna), čak i
  ako merenje čeka CI/staging.

- [ ] **AC9 — `just a11y` recept + harness razdvojen od `just test`/`just e2e`.**
  `justfile` dobija `just a11y` recept koji pokreće axe spec (`pytest -m a11y tests/e2e/` u Docker,
  protiv pokrenute seed-ovane app — mirror `just e2e` prereqs). `pyproject.toml` `addopts` već
  `-m 'not e2e'`; proširiti na `-m 'not e2e and not a11y'` da `just test` (unit) **NE** povlači a11y
  audit. Lighthouse/k6 se NE pokreću kroz `just test` (zaseban workflow/runbook).

- [ ] **AC10 — SCOPE-DEFER 9.10 + 0 image-konverzije + 0 novih migracija/auth/upload surface.**
  Story **NE** radi WebP/AVIF konverziju (9.10), **NE** menja `sorl-thumbnail` config, **NE** dodaje
  migracije/auth/forme/upload/nove network rute. Dozvoljene su **male a11y/perf template delte** (alt,
  aria-label, lang, focus-visible, kontrast token, `loading="lazy"`, `font-display` provera) kao
  „jeftine popravke" (AC7c) — additivno, markup-lock-safe (Epic 5/6/7 lock poštovan, mirror 9-8
  data-testid delta disciplina). Svaki veći nalaz → GitHub Issue (AC7d) ili NOTE za 9.10 (AC7e).

- [ ] **AC11 — Harness „proven running": axe spec DEMONSTRABILNO collect-able I izvršen bar JEDNOM u CI.**
  Pošto `continue-on-error` (SM-D7) + „TBD staging brojevi" (AC8) zajedno dozvoljavaju da SVE ostale AC
  „prođu" bez da je harness ikad izvršen end-to-end, ova AC traži **realan signal da harness STVARNO radi**,
  ne samo da je sintaksno validan:
  - **(a) Collect-able:** `pytest -m a11y tests/e2e/ --collect-only` u CI a11y/Lighthouse job-u uspešno
    sakuplja sve parametrize case-ove (AC2 a–f + AC2b HTMX case) — 0 collection error-a (import/marker/fixture).
  - **(b) Izvršen bar jednom protiv self-contained CI runserver-a:** a11y job (mirror 9-8 `e2e.yml`
    self-contained: Postgres + `runserver --insecure` + seed) pokreće axe spec **bar jednom** tako da
    **axe injektuje `axe.min.js` i `axe.run()` vrati REALAN result objekat** (`{ violations, passes,
    incomplete, inapplicable }`) za bar jednu stranu. Ovo je „harness proven running" signal: hvata
    syntactically-valid-ali-nikad-pokrenut harness koji bi pukao na prvom realnom post-merge run-u.
    Fabrikovan green je ZABRANJEN — traži se da axe VRATI result, ne da neko upiše „prošlo".
  - **Caveat OČUVAN:** ovo je **CI-job zahtev, NE Windows-host zahtev.** Win host (libmagic + browser)
    i dalje NE pokreće — `continue-on-error` na `assert`/budget koraku ostaje (SM-D7); ali axe spec MORA
    biti dokazano collect-able + izvršen bar jednom u CI (NE fabrikovano zeleno). Ako CI runner trenutno
    nije konfigurisan da izvrši a11y job, to je zabeleženo kao eksplicitan TODO + OQ (NE tiho preskočeno).

## Tasks / Subtasks

- [x] **Task 1 — A11y audit spec (axe-core) u 9-8 harness-u** (AC1, AC2, AC2b, AC8, AC11)
  - [x] 1.1 Dodati dev dep za axe runner: `axe-playwright-python` (ili `playwright-axe`) preko
    `uv add --dev` + `uv.lock` regen (`uv lock --native-tls` per Epic 9 sandbox TLS baseline).
  - [x] 1.2 Registrovati `a11y` marker u `pyproject.toml [tool.pytest.ini_options].markers`
    (različit od `e2e`); proširiti `addopts` na `-m 'not e2e and not a11y'`.
  - [x] 1.3 `tests/e2e/test_a11y_audit.py`: `pytestmark = pytest.mark.a11y`; reuse `base_url`,
    `e2e_data`/`seed_e2e_data`, `dev_superuser` (admin), page objects iz `tests/e2e/page_objects/`. (TEA-spec, NETAKNUT)
  - [x] 1.4 Parametrize po stranama (AC2 a–f); za svaku: `page.goto(url)` → injektuj axe → `axe.run()`
    sa WCAG 2.1 AA tagovima → assert 0 `critical`/`serious` violation (filter po `impact`); upiši
    `moderate`/`minor` u izlaz (NE fail). **Blog post case = TAČAN URL
    `/sr/blog/pet-saveta-za-prolecnu-setvu/`** (deterministički seed; 404 = false-pass, NE „npr."). (TEA-spec)
  - [x] 1.4b **HTMX post-swap sken (AC2b):** bar jedan case koji pokrene HTMX interakciju (traktori
    filter submit na `/sr/traktori/` ILI kontakt/model-inquiry forma) → čekaj HTMX-settled
    (`wait_for_selector`/`expect(...).to_be_visible()` na swap-ovani fragment) → `axe.run()` POSLE
    swap-a (skenira dinamički DOM: OOB aria-live + post-swap markup, project-context #1/#3 rizik). (TEA-spec)
  - [x] 1.5 Admin strana (`/admin-coric/`): autentikovan kontekst se obezbeđuje preko **`dev_superuser`
    fixture-a iz `tests/e2e/conftest.py`** (env-driven `createsuperuser --noinput` + MANDATORY
    `axes_reset` flush — 9-8 AC1c/AC1d), NE preko izmišljenog helpera. Za samu navigaciju/login formu
    reuse-uj **postojeći `AdminProductPage.login(username, password)`** (realna metoda u
    `tests/e2e/page_objects/admin_product_page.py:54`, `LOGIN_PATH="/admin-coric/login/"`) pre skena.
    Credencijali dolaze iz istog env-a koji `dev_superuser` koristi (NIKAD hardkodovan password). (TEA-spec)
  - [x] 1.6 Caveat header u docstring-u: stvarni green = CI/staging; host (Win libmagic + browser) NE
    pokreće. RED-potvrda strukture, NE fabrikuj green. (TEA-spec)

- [x] **Task 2 — Lighthouse CI budget config + workflow** (AC3, AC4, AC8)
  - [x] 2.1 `lighthouserc.json` (root ili `ops/quality/`): `ci.collect.url` (ključne javne strane,
    admin IZUZET), `numberOfRuns: 3`, `ci.assert` budgeti (a11y ≥ 0.95, LCP < 2500, server-response
    < 600, total-byte-weight < 1572864).
  - [x] 2.2 `.github/workflows/lighthouse.yml`: self-contained (mirror `e2e.yml` — Postgres service +
    migrate + `seed_e2e_data --force` + collectstatic + runserver bg + wait-for-app) + `@lhci/cli
    autorun` (Node setup-node step). Trigger: `push: [staging]` + `workflow_dispatch`.
  - [x] 2.3 SM-D7 odluka: `lhci assert` korak `continue-on-error: true` (baseline-collect v1) sa
    komentarom da hard-gate = OQ-1 (Mihas). Upload Lighthouse report kao artifact (`actions/upload-artifact`).
  - [x] 2.4 Komentar-caveat: brojevi su autoritativni TEK na staging-u/CI (ne na Win hostu).

- [x] **Task 3 — k6 load test + runbook** (AC5, AC8)
  - [x] 3.1 `ops/perf/load_test.js`: k6 `options.stages` ramp profil — **konkretno:**
    `[{ duration: '30s', target: 20 }, { duration: '60s', target: 50 }, { duration: '30s', target: 0 }]`
    (ramp 0→20, hold/ramp 20→50, ramp-down 50→0) + `thresholds`
    (`http_req_duration: ['p(95)<600']`, `http_req_failed: ['rate<0.01']`); čita `__ENV.BASE_URL`
    (fail-loud ako nije set; NIKAD hardkodovan prod). GET read-heavy rute (home/traktori/product/blog).
  - [x] 3.2 `ops/perf/README.md`: kako instalirati k6, `BASE_URL=https://staging... k6 run
    ops/perf/load_test.js`, čitanje izlaza, pragovi, **UPOZORENJE: NE protiv prod-a bez dogovora**;
    load test = manual go-live korak (OQ-2), NE CI v1.

- [x] **Task 4 — Manual a11y checklist** (AC6)
  - [x] 4.1 `ops/quality/a11y-manual-checklist.md`: keyboard Tab/Esc (3 UJ), focus management posle
    HTMX swap, `prefers-reduced-motion`, kontrast 4.5:1 spot-check, NVDA 1-UJ. Svaka stavka = checkbox
    + očekivani rezultat + WCAG referenca. Označiti kao manual go-live gate (OQ-3).

- [x] **Task 5 — AUDIT REPORT + jeftine popravke + GitHub Issue putanja** (AC7, AC8, AC10)
  - [x] 5.1 `ops/quality/AUDIT-REPORT.md`: scope, baseline nalazi (axe per-page; Lighthouse „TBD
    staging" ako ne-mereno), Issue-template (strana+alat+WCAG+impact+fix), „NOTE za 9.10" sekcija.
  - [x] 5.2 Jeftine popravke: primenjene 2 trivijalno-sigurne (header.html + footer.html logo alt
    „Coric Agrar"→„Ćorić Agrar", pune dijakritike). Statička inspekcija: projekat već a11y-zreo
    (0 `<img>` bez alt, aria-label na ikon-dugmadima, font-display:swap, prefers-reduced-motion u 19
    CSS, lazy loading default). Dalji nalazi = TEK iz CI/staging axe run-a (OQ-1..OQ-3). 0 image-konverzija (9.10).
  - [x] 5.3 Lista non-trivijalnih fail-ova za GitHub Issue kreiranje (remediation backlog — template + prazan, čeka CI run).

- [x] **Task 6 — justfile recept + lint/format gate + harness-proven-running** (AC9, AC10, AC11)
  - [x] 6.1 `just a11y` recept (Docker, `pytest -m a11y tests/e2e/`, isti prereqs kao `just e2e`).
  - [x] 6.2 `ruff check .` clean (Python axe spec); `lighthouserc.json`/workflow YAML/JSON valid;
    k6 JS sintaksno valid (node --check). 0 migracija, 0 schema promene.
  - [x] 6.3 **AC11 harness-proven-running:** `pytest -m a11y tests/e2e/ --collect-only` DOKAZANO clean
    u Docker-u (7/17 collected, 0 collection error — import/marker/fixture resolve). a11y CI job
    (`lighthouse.yml`) ožičen da axe spec izvrši **bar jednom** protiv self-contained runserver-a
    (`axe.run()` realan result). Caveat: CI-job zahtev, NE Win host (`continue-on-error` na assert ostaje).

## SM Decisions (SM-D)

- **SM-D1 — axe-playwright (axe-core) PREKO Pa11y.** epics.md kaže „axe-core ili Pa11y + Lighthouse
  CI". Biram **axe-core kroz Playwright** (`axe-playwright-python`/inject `axe.min.js`) jer 9-8 VEĆ
  isporučuje Playwright harness (conftest + page objects + seed) — reuse > novi Node Pa11y stack.
  Pa11y bi tražio zaseban Node toolchain i duplirao navigaciju koju Playwright već radi. axe-core
  pokriva WCAG 2.1 AA tagove. Lighthouse a11y kategorija (zasnovan na axe interno) ostaje kao DRUGI,
  nezavisni signal (AC3) — defense-in-depth, ne duplikat.
- **SM-D2 — Gate samo na `critical`+`serious` axe impact; `moderate`/`minor` loguje se, ne fail-uje.**
  epics AC „0 critical a11y issue-a". Baseline pragmatizam: blokirati build na minor (npr. landmark
  preporuke) bi učinio audit krhkim na first-pass. Critical/serious = gate; ostalo u AUDIT-REPORT za
  remediation Issue. (Mihas može pooštriti na go-live — OQ-1.)
- **SM-D3 — Admin (`/admin-coric/`) u axe sken ALI VAN Lighthouse perf budgeta.** Admin je
  login-gated, nije javni LCP/page-weight target (Django admin static je tuđi markup). A11y axe sken
  admin-a ima vrednost (form labels), ali perf budget na njemu je besmislen → Lighthouse `collect.url`
  izuzima admin.
- **SM-D4 — Jeftine popravke su MALE template delte, markup-lock-safe.** Dozvoljeno: `alt`,
  `aria-label`, `lang`, `focus-visible` CSS, kontrast token swap, `loading="lazy"`, `font-display`
  provera. ZABRANJENO: image-format konverzija (9.10), strukturni markup rewrite koji lomi Epic 5/6/7
  lock testove. Mirror 9-8 data-testid additivne-delte discipline. Sve dokumentovano u AUDIT-REPORT.
- **SM-D5 — k6 PREKO locust kao load tool.** epics.md NE imenuje load tool. Biram **k6** (lakši:
  single static binary, JS skripta, thresholds first-class, 0 Python runtime zavisnost — ne sudara se
  sa libmagic host baseline-om; locust bi tražio Python proces + web UI + Flask-style overhead). k6 se
  pokreće protiv staging URL-a (env-driven), runbook-dokumentovan.
- **SM-D6 — Load test = MANUAL go-live korak, NE CI v1.** Load protiv staging-a troši resurse i nije
  per-push potreban; vozi se ručno pred go-live (OQ-2). k6 skripta + runbook su deliverable; izvršenje
  je gate, ne automatski build korak. (Sprečava i flake/cost na svaki staging push.)
- **SM-D7 — Lighthouse `lhci assert` v1 `continue-on-error` (baseline-collect), hard-gate = OQ-1.**
  Prvi pass na realnom staging content-u verovatno NEĆE odmah pogoditi sve budgete (npr. page-weight
  pre 9.10 WebP/AVIF). v1 prikuplja baseline + upload report; hard-fail-na-budget je go-live odluka
  (Mihas, OQ-1) kad je 9.10 gotov. Iskrenost: ne maskiramo realan miss zelenom lampom.
- **SM-D8 — `a11y` marker razdvojen od `e2e`.** Axe audit NIJE user-journey (`needs_e2e=false`,
  `e2e_count=0`). Zaseban marker → `just test` (unit) i `just e2e` (3 UJ) i `just a11y` (audit) su tri
  nezavisne suite. `addopts -m 'not e2e and not a11y'` čuva fast unit loop.
- **SM-D9 — Reuse 9-8 `seed_e2e_data` (NE novi seed).** Audit cilja iste determinističke slug-ove
  (`agri-tracking-tb804`, traktori listing, blog post). `seed_e2e_data --force` (9-8) je SOT; story NE
  pravi novi seed command (DRY, idempotentnost već dokazana u 9-8).
- **SM-D10 — Lighthouse `numberOfRuns ≥ 3` median.** Single-run LCP/TTFB su šumoviti; median od 3
  smanjuje flake u budget asercijama (LHCI best practice).

## Open Questions / Go-Live Gates (OQ)

- **OQ-1 (TVRD go-live gate) — Lighthouse hard-gate vs report-only + staging Lighthouse run.**
  Mihas/Dana odlučuju da li `lhci assert` postaje hard-fail (block staging) ILI ostaje report-only do
  9.10. **Stvarni Lighthouse brojevi se mere na deploy-ovanom staging-u (9-2)** — to je autoritativni
  izvor (NE Win host, NE CI runserver nužno reprezentativan za prod nginx/Whitenoise/Gunicorn). Pre
  go-live: pokreni Lighthouse protiv staging URL-a, upiši realne brojeve u AUDIT-REPORT.
- **OQ-2 (TVRD go-live gate) — k6 load test izvršenje protiv staging-a.** Skripta + runbook su
  spremni; izvršenje (`BASE_URL=staging k6 run`) + upis rezultata u AUDIT-REPORT je manual pre-launch
  korak. Potvrditi staging kapacitet (CX22) i da li load test sme da gađa shared staging.
- **OQ-3 (TVRD go-live gate) — NVDA manual screen-reader pass + keyboard checklist.** NVDA (Windows)
  prolaz bar 1 UJ + keyboard/focus/reduced-motion checklist su **manual** — Mihas (ili imenovani
  tester) izvršava `a11y-manual-checklist.md` pre go-live i potpisuje rezultat u AUDIT-REPORT.
- **OQ-4 — CI secret/URL za Lighthouse/staging.** Ako Lighthouse cilja deploy-ovani staging (ne
  self-contained job), treba `STAGING_BASE_URL` secret + `DJANGO_SUPERUSER_PASSWORD` (admin a11y sken)
  + eventualni LHCI server token. Potvrditi GH secrets postavku (mirror 9-2 OQ-5 / 9-8 OQ-3).
- **OQ-5 — Fail item → GitHub Issue kreiranje (vlasnik/labela).** AUDIT-REPORT lista non-trivijalne
  fail-ove; ko kreira Issue-e i pod kojom labelom (`a11y`/`perf`/`remediation`) + da li je to blocker
  za go-live ili post-launch backlog. (epics AC „evidentno u GitHub Issue".)

## Dev Notes

- **Host/CI baseline (PONOVITI):** native Windows host pytest collection pada na `libmagic`
  (dokumentovan kroz Epik 9 — 9-3..9-8). Playwright browseri, Lighthouse (headless Chrome) i k6 binar
  **se NE očekuje da rade na ovom Win hostu.** Autoritativni runner = GitHub Actions CI (Ubuntu, mirror
  9-8 `e2e.yml` system deps: `libmagic1 poppler-utils`) + deploy-ovani staging (9-2) za realne brojeve.
  Story je „GREEN-na-Win NIJE gate by design" — RED/struktura-potvrda + CI/staging merenje.
- **Reuse 9-8 harness:** `tests/e2e/conftest.py` (`base_url`, `e2e_data` koji zove `seed_e2e_data
  --force`, `dev_superuser` env-driven + axes-flush, `sample_image_path`, `mobile_*`), page objects
  (`traktori_listing_page`, `product_detail_page`, `service_page`, `admin_product_page`). A11y spec
  **reuse**-uje ove — NE reimplementira navigaciju/login.
  - `E2E_SKIP_DATA_SETUP=1` env (9-8) preskače subprocess seed kad CI radi setup kao zaseban step —
    isto važi za a11y/Lighthouse workflow.
- **Axe runner:** `axe-playwright-python` izlaže `Axe().run(page)`; alternativa: ručno
  `page.add_script_tag(path=axe.min.js)` + `page.evaluate("axe.run(...)")`. Konfiguriši
  `runOnly: { type: 'tag', values: ['wcag2a','wcag2aa','wcag21a','wcag21aa'] }`. Filter
  `violations` po `impact in {critical, serious}` za gate.
  - **`axe.min.js` fallback izvor (ako se ne koristi `axe-playwright-python` koji ga već bundle-uje):**
    `npm install axe-core` (ili `npm i -D axe-core`) pa **vendor-uj `node_modules/axe-core/axe.min.js`
    u `tests/e2e/assets/`** i referenci ga preko `page.add_script_tag(path=...)`. NIJE „nađi neki
    axe.min.js" — tačan izvor je `axe-core` npm paket. Preferirano: `axe-playwright-python` (bundluje
    axe, 0 ručnog vendor-a) — vidi SM-D1.
- **Lighthouse self-contained CI:** mirror `e2e.yml` — Postgres service + migrate + `seed_e2e_data
  --force --reset-axes` + collectstatic + `runserver 0.0.0.0:8000 --noreload --insecure &` +
  wait-for-app loop + `setup-node` + `@lhci/cli autorun`. CAVEAT: `runserver --insecure` static NIJE
  isto što i prod nginx/Whitenoise → page-weight/TTFB brojevi su INDIKATIVNI; autoritativni su na
  staging-u (OQ-1).
  - **Axes-flush naming (NE zbuni Dev-a — dva imena, ista svrha):** `axes_reset` je **built-in
    django-axes** management command (ono što `dev_superuser` fixture interno zove —
    `conftest.py:162`). `seed_e2e_data --reset-axes` je **flag istog projekt-seed komandanta** (vidi
    `apps/core/management/commands/seed_e2e_data.py:80`) koji **interno radi isti axes-flush**. U
    a11y pytest putanji axes-flush dolazi BESPLATNO preko `dev_superuser` fixture-a (NE moraš ručno);
    u Lighthouse workflow-u (gde nema pytest fixture-a) koristi `seed_e2e_data --force --reset-axes`
    kao jedan korak. Oba su validna — biraj prema kontekstu, ne mešaj.
- **k6:** static binary; CI ga NE pokreće v1 (SM-D6). Runbook pokriva install (`brew`/`choco`/binary)
  + `BASE_URL` env. Thresholds: `http_req_duration p(95)<600` (mapира TTFB-budget), `http_req_failed
  rate<0.01`.
- **SCOPE-DEFER 9.10:** NE diraj `sorl-thumbnail` config, NE `<picture>`/AVIF/WebP. Image-weight
  nalazi → „NOTE za 9.10" u AUDIT-REPORT.
- **Markup-lock:** jeftine popravke (alt/aria/lang/focus/kontrast) su additivne, NE smeju lomiti Epic
  5/6/7 head-count / lock testove (mirror 9-8 data-testid disciplina). Pune dijakritike (č/ć/ž/š/đ) u
  svim user-facing `alt`/`aria-label` stringovima (project-context anti-pattern).
- **Determinstički ciljevi (9-7 manifest):** product `agri-tracking-tb804` (€28.500/80KS), traktori
  listing (3 traktora vidljiva posle `seed_e2e_data` subcategory-assign), blog post
  `pet-saveta-za-prolecnu-setvu`, model-inquiry/kontakt forma, `/admin-coric/`.
- **0 migracija, 0 dep za prod** (axe runner + lhci su DEV/CI-only; k6 je sistem binar van Python-a).
  `just lint` (ruff) clean za Python; YAML/JSON/JS sintaksno valid.

## Definition of Done

- [ ] `tests/e2e/test_a11y_audit.py` (a11y marker) skenira 6 ključnih strana, gate na 0 critical/serious.
- [ ] Bar 1 axe case POSLE HTMX swap-a (dinamički DOM, ne samo initial load) — AC2b (traktori filter/forma).
- [ ] Blog post case gađa TAČAN URL `/sr/blog/pet-saveta-za-prolecnu-setvu/` (deterministički seed, NE 404).
- [ ] Harness „proven running": `pytest -m a11y --collect-only` clean + axe izvršen bar jednom u CI
      (axe.run vraća realan result objekat), NE fabrikovano — AC11. (CI-job zahtev, NE Win host.)
- [ ] `lighthouserc.json` budgeti (a11y≥95, LCP<2.5s, TTFB<600ms, weight<1.5MB) + `lighthouse.yml` workflow.
- [ ] `ops/perf/load_test.js` (k6) + `ops/perf/README.md` runbook sa thresholdovima.
- [ ] `ops/quality/a11y-manual-checklist.md` (keyboard/focus/reduced-motion/kontrast/NVDA).
- [ ] `ops/quality/AUDIT-REPORT.md` (nalazi + jeftine popravke + Issue putanja + NOTE-za-9.10 +
      disclaimer „axe-green ≠ dokazan WCAG 2.1 AA" — AC7f).
- [ ] v1 self-contained CI runserver mod (radi danas, indikativni brojevi) vs staging-targeted mod
      (real prod nginx/Whitenoise, traži STAGING_BASE_URL + secrets) EKSPLICITNO razdvojeni — AC4/OQ-4.
- [ ] `just a11y` recept + `addopts -m 'not e2e and not a11y'`.
- [ ] HOST/CI caveat enkodiran; Lighthouse/k6/NVDA brojevi „TBD staging" gde ne-mereno (NE fabrikovano).
- [ ] 9.10 image-konverzija NE dirana; 0 migracija/auth/upload surface; ruff clean.
- [ ] OQ-1..OQ-5 zabeleženi kao go-live gates.
