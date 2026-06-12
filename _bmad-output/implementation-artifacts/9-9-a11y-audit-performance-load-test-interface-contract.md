---
story-id: 9-9-a11y-audit-performance-load-test
artifact: interface-contract (RED-faza AUDIT-GATE kontrakt)
epic: 9
module: ops/quality + CI tooling (NIJE Django app)
risk-tier: MEDIUM
needs_e2e: false
e2e_count: 0
authored-by: TEA (Test Architect, RED phase)
date: 2026-06-12
---

# Story 9.9 — Interface Contract (RED → GREEN)

SPECIJALNA story: deliverable je **AUDIT/QUALITY TOOLING**, NE Django app/feature, NE
novi user-journey. NEMA modela/view-ova/migracija. „Failing test" = **audit harness
čija struktura JESTE kontrakt** koji Dev mora ispuniti. Autoritativno a11y/perf merenje
je staging/CI (OQ-1..OQ-4) — NE ovaj Windows host. Iskrenost iznad zelene lampice (AC8).

Ovaj dokument definiše TAČNO šta Dev isporučuje da harness pređe iz RED (collection /
import fail na host-u) u GREEN (collect-able + izvršen bar jednom u CI; AC11).

---

## 0. RED signal (host) — VEĆ POTVRĐEN od strane TEA

`tests/e2e/test_a11y_audit.py` je napisan kao realan RED spec (contract-as-code). Na
native Windows host-u:

- `python -m py_compile tests/e2e/test_a11y_audit.py` → **OK** (spec sintaksno validan).
- `python -m pytest tests/e2e/test_a11y_audit.py --collect-only` → **ImportError:
  failed to find libmagic** pri `django.setup()` (admin autodiscover → `apps.brands.admin`
  → `apps.media_pipeline.pdf_utils` → `import magic`). Dokumentovani Epik-9 host baseline;
  pytest NE stigne ni do collect-a spec-a.
- Sekundarni (i nezavisni) RED uzrok: `import axe_playwright_python` →
  **ModuleNotFoundError** (axe runner dep NIJE instaliran još).

Oba uzroka su OČEKIVANA i by-design. GREEN je CI/staging posao (AC11), NE Win host.

---

## 1. Fajlovi koje Dev MORA da kreira / izmeni

### 1.1 `tests/e2e/test_a11y_audit.py` — VEĆ NAPISAN (TEA, RED)
Dev **NE prepisuje** ovaj spec — samo ga GREEN-uje instalacijom dep-a + CI ožičenjem.
Spec sadrži (sve obavezno po AC1/AC2/AC2b):
- `pytestmark = pytest.mark.a11y` (ZASEBAN marker, NE `e2e`).
- REUSE 9-8 conftest fixtures: `base_url`, `e2e_data` (seed_e2e_data), `dev_superuser`.
- REUSE page objects: `AdminProductPage.login()`, `TraktoriListingPage` (dokumentovana
  AC2b alternativa).
- WCAG 2.1 AA tagovi: `["wcag2a","wcag2aa","wcag21a","wcag21aa"]`.
- Gate: `impact in {critical, serious}` fail; `moderate`/`minor` se logују u assert
  poruci, NE fail-uju (SM-D2).
- **Parametrize javne strane (AC2 a–e)** — tačni URL-ovi (potvrđeni iz urls.py):
  - `/` (home)
  - `/sr/traktori/` (listing)
  - `/sr/proizvod/agri-tracking-tb804/` (product detail + galerija)
  - `/sr/kontakt/` (kontakt forma)
  - `/sr/blog/pet-saveta-za-prolecnu-setvu/` (blog post — **TAČAN deterministički seed
    slug**; 404 = false-pass, zato fiksan)
- **Admin (AC2 f)** — zaseban test `test_a11y_admin_login_gated`: `dev_superuser` fixture
  + `AdminProductPage.login()` (LOGIN_PATH `/admin-coric/login/`) → axe na admin index.
- **AC2b (edge case)** — `test_a11y_after_htmx_swap`: `/sr/kontakt/` → submit kontakt
  forme (hx-post → `#contact-form-section`, hx-swap=outerHTML) → čekaj HTMX-settled
  (success `.coric-contact-form__success` `role="status"` vidljiv, auto-wait, NEMA sleep)
  → `axe.run()` na POST-SWAP DOM-u (OOB aria-live + success fragment; project-context #1/#3).

### 1.2 `lighthouserc.json` (repo root ili `ops/quality/`) — AC3, SM-D10
LHCI config:
```jsonc
{
  "ci": {
    "collect": {
      "numberOfRuns": 3,                 // median, smanji flake (SM-D10)
      "url": [                           // ADMIN IZUZET (SM-D3: login-gated, nije LCP target)
        "http://localhost:8000/",
        "http://localhost:8000/sr/traktori/",
        "http://localhost:8000/sr/proizvod/agri-tracking-tb804/",
        "http://localhost:8000/sr/kontakt/",
        "http://localhost:8000/sr/blog/pet-saveta-za-prolecnu-setvu/"
      ]
    },
    "assert": {
      "assertions": {
        "categories:accessibility": ["error", { "minScore": 0.95 }],
        "largest-contentful-paint": ["error", { "maxNumericValue": 2500 }],
        "server-response-time":     ["error", { "maxNumericValue": 600 }],
        "total-byte-weight":        ["error", { "maxNumericValue": 1572864 }]
      }
    },
    "upload": { "target": "filesystem", "outputDir": "./lighthouse-report" }
  }
}
```
v1 napomena (SM-D7): `assert` fail je **continue-on-error** u workflow-u (baseline-collect),
hard-gate = OQ-1 (Mihas). Brojevi su INDIKATIVNI na runserver-u; autoritativni na staging-u.

### 1.3 `.github/workflows/lighthouse.yml` — AC4, mirror `e2e.yml`
**Self-contained**, mirror strukture `.github/workflows/e2e.yml`:
- `on: push: branches: [staging]` + `workflow_dispatch` (NE master/PR — SM mirror 9-8 AC7).
- Postgres 16 service (localhost:5432, isti env kao e2e.yml).
- Koraci: checkout → setup-uv → `apt install libmagic1 poppler-utils` → `uv sync --frozen
  --group dev` → `migrate` → `seed_e2e_data --force --reset-axes` → `collectstatic` →
  `runserver 0.0.0.0:8000 --noreload --insecure &` → wait-for-app loop (`curl /sr/`) →
  `actions/setup-node` → `npm i -g @lhci/cli` (ili `npx`) → `lhci autorun`.
- `lhci assert` korak: **`continue-on-error: true`** (SM-D7 v1 baseline-collect) +
  komentar da hard-gate = OQ-1.
- `actions/upload-artifact` za `./lighthouse-report`.
- **AC11 a11y job (ista ili paralelna lane):** isti self-contained setup pokreće
  `uv run pytest -m a11y tests/e2e/ -v` (sa `E2E_SKIP_DATA_SETUP: "1"` jer je seed
  zaseban step) tako da axe injektuje axe.min.js i `axe.run()` vrati realan result
  objekat bar jednom (NE fabrikovano). `--collect-only` pre toga mora biti clean.
  - Caveat: ako a11y CI job još nije ožičen → eksplicitan TODO + OQ (NE tiho preskočen).
- Komentar-caveat u YAML: brojevi autoritativni TEK na staging-u (OQ-1/OQ-4), NE Win host.

### 1.4 `ops/perf/load_test.js` — AC5, SM-D5/SM-D6
k6 skripta:
```js
import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = __ENV.BASE_URL;            // fail-loud; NIKAD hardkodovan prod
if (!BASE_URL) { throw new Error('BASE_URL env nije postavljen — NIKAD prod bez dogovora (OQ-2).'); }

export const options = {
  stages: [
    { duration: '30s', target: 20 },        // ramp 0→20
    { duration: '60s', target: 50 },        // ramp/hold 20→50
    { duration: '30s', target: 0 },         // ramp-down 50→0
  ],
  thresholds: {
    http_req_duration: ['p(95)<600'],       // TTFB-ekvivalent p95 < 600ms
    http_req_failed: ['rate<0.01'],         // < 1% fail
  },
};

const ROUTES = [                            // read-heavy JAVNE rute (GET)
  '/sr/', '/sr/traktori/',
  '/sr/proizvod/agri-tracking-tb804/',
  '/sr/blog/',
];

export default function () {
  for (const path of ROUTES) {
    const res = http.get(`${BASE_URL}${path}`);
    check(res, { 'status 200': (r) => r.status === 200 });
  }
  sleep(1);
}
```
**NE pokreće se u CI v1** (SM-D6 — manual go-live korak, OQ-2).

### 1.5 `ops/perf/README.md` — AC5
k6 runbook (srpska latinica, pune dijakritike): instalacija (`choco install k6` /
`brew install k6` / static binary), pokretanje (`BASE_URL=https://staging... k6 run
ops/perf/load_test.js`), čitanje izlaza (p95/req_failed/VU), pragovi i šta znače,
**UPOZORENJE: NIKAD protiv prod-a bez dogovora**; load test = manual go-live korak (OQ-2),
NE CI v1; potvrdi staging kapacitet (CX22) pre gađanja shared staging-a.

### 1.6 `ops/quality/a11y-manual-checklist.md` — AC6
Manual go-live gate (OQ-3), svaka stavka = checkbox + očekivani rezultat + WCAG referenca:
- (a) **keyboard-only** Tab kroz 3 UJ-a (sve interaktivno dostupno); **Esc** zatvara
  modale/Lightbox/mobile-nav (WCAG 2.1.1, 2.1.2).
- (b) **focus management posle HTMX swap-a** (fokus se vraća na trigger/target;
  project-context #3) (WCAG 2.4.3).
- (c) **`prefers-reduced-motion`** respect (slider/animacije se gase) (WCAG 2.3.3).
- (d) **kontrast 4.5:1** spot-check ključnih parova (DESIGN.md tokeni) (WCAG 1.4.3).
- (e) **NVDA (Windows) screen-reader** prolaz bar 1 UJ (form labels, aria-live announcement,
  heading struktura) (WCAG 1.3.1, 4.1.2, 4.1.3).

### 1.7 `ops/quality/AUDIT-REPORT.md` — AC7, AC8, AC10
- (a) **scope** (strane/alati/budgeti).
- (b) **baseline nalazi** (axe violations po strani po impact-u; Lighthouse „TBD — staging
  Lighthouse run" ako ne-mereno — **fabrikovani brojevi ZABRANJENI**).
- (c) **jeftine popravke primenjene u 9.9** (alt/aria-label/lang/focus-visible/kontrast
  token; male template delte, markup-lock-safe) — ILI eksplicitno `n/a — audit nije
  pokrenut na host-u` (DoD disambiguacija Task 5.2: prazan fix-set NIJE failure ako je
  obrazložen kao „nema host-merenja").
- (d) **„fail item → GitHub Issue" putanja** (template: strana + alat + WCAG kriterijum +
  impact + predlog fix-a) (OQ-5).
- (e) **„NOTE za 9.10" sekcija** za svaki image-weight/format nalaz (NE konvertuj — scope-defer).
- (f) **EKSPLICITAN disclaimer (AC7f): axe-green ≠ dokazan WCAG 2.1 AA.** Automatizovani
  axe pokriva ~30–40% kriterijuma; kontrast/keyboard/focus-order/reduced-motion/SR razumevanje
  se NE dokazuju axe-om → zavise od manual checklist-a (AC6) + NVDA (OQ-3). „0 critical axe"
  je NUŽAN ali NE DOVOLJAN uslov za AA.

---

## 2. `pyproject.toml` delta (Dev — Task 1.1/1.2)

1. **Registruj `a11y` marker** u `[tool.pytest.ini_options].markers`:
   ```toml
   "a11y: axe-core WCAG 2.1 AA audit suite (Story 9.9); audit-gate NE user-journey; trazi pokrenutu seed-ovanu app + browser + axe; deselect sa -m 'not a11y'",
   ```
2. **Promeni `addopts`** sa `-m 'not e2e'` na:
   ```toml
   addopts = "--import-mode=importlib -m 'not e2e and not a11y'"
   ```
   (čuva fast unit loop: `just test` NE povlači a11y audit — SM-D8.)
3. **Dodaj axe dev dep** u `[dependency-groups].dev`:
   ```
   "axe-playwright-python>=0.1.7",
   ```
   (preko `uv add --dev axe-playwright-python` + `uv lock --native-tls` per Epic-9 TLS
   baseline). **VERZIJA (TEA-verifikovano na PyPI 2026-06-12):** poslednji objavljeni
   release je **0.1.7** — NE postoji 1.x. Pin MORA biti `>=0.1.7` (ranije `>=1.1` je bilo
   NEZADOVOLJIVO → `uv add` bi pao na „no matching distribution"). API (0.1.7,
   `axe_playwright_python/sync_playwright.py`): `Axe().run(page, context=None,
   options=...)` → vraća `AxeResults` sa `.response` (`{violations, passes, incomplete,
   inapplicable}`) i `.violations_count`. Spec prosleđuje `options={"runOnly": {"type":
   "tag", "values": [...]}}` što OVERRIDE-uje built-in `DEFAULT_OPTIONS={"resultTypes":
   ["violations"]}` → axe-core onda vraća PUN result objekat (sve 4 sekcije) — tačno ono
   što AC11(b) traži. **Fallback** (Dev Notes): `npm i -D axe-core` → vendor
   `node_modules/axe-core/axe.min.js` u `tests/e2e/assets/` + `Axe.from_file(path)` ILI
   `page.add_script_tag(path=...)` (tada spec import-uje vendored runner umesto
   `axe_playwright_python`). 0 prod dep (axe je DEV/CI-only).

---

## 3. `justfile` delta (Dev — Task 6.1) — AC9

Dodaj `a11y` recept (mirror `e2e`):
```just
# Pokrece ISKLJUCIVO axe a11y audit suite (Story 9.9) protiv pokrenute, seed-ovane app.
# `just test` (-m 'not e2e and not a11y') NE povlaci a11y; tri suite razdvojene (SM-D8).
# Prereqs isti kao `just e2e` (dev up + seed_e2e_data --force + playwright chromium +
# DJANGO_SUPERUSER_PASSWORD u env-u) + axe runner dep.
a11y *ARGS:
    docker compose -f compose/local.yml run --rm django uv run pytest -m a11y tests/e2e/ {{ARGS}}
```

---

## 4. CI workflow rezime

- Novi fajl: `.github/workflows/lighthouse.yml` (self-contained, mirror `e2e.yml`):
  Postgres service + migrate + `seed_e2e_data --force --reset-axes` + collectstatic +
  `runserver --insecure` bg + wait-for-app + (setup-node + `lhci autorun`) + (`pytest -m
  a11y` izvršen bar jednom — AC11) + upload-artifact. Trigger `push:[staging]` +
  `workflow_dispatch`. `lhci assert` `continue-on-error: true` (v1, SM-D7).
- **v1 self-contained CI runserver mod** (radi danas, indikativni brojevi) vs
  **staging-targeted mod** (real prod nginx/Whitenoise; traži `STAGING_BASE_URL` +
  `DJANGO_SUPERUSER_PASSWORD` + LHCI token secrets) — EKSPLICITNO razdvojeni (AC4/OQ-4).
  Autoritativni go-live brojevi dolaze IZ staging moda, NE iz v1.

---

## 5. Scope-guard (AC10) — šta Dev NE sme

- 0 image-format konverzije (WebP/AVIF = 9.10); image-weight nalaz → „NOTE za 9.10".
- 0 izmena `sorl-thumbnail` config-a; 0 migracija/auth/forme/upload/novih network ruta.
- Jeftine popravke su MALE additivne template delte (alt/aria/lang/focus/kontrast),
  markup-lock-safe (Epic 5/6/7 head-count / lock testovi NETAKNUTI; mirror 9-8 disciplina).
- Pune dijakritike (č/ć/ž/š/đ) u svim user-facing `alt`/`aria-label`/checklist/report stringovima.

---

## 6. GREEN definicija (AC11 — „harness proven running")

1. `pytest -m a11y tests/e2e/ --collect-only` u CI → 0 collection error (import/marker/fixture);
   svi parametrize case-ovi (AC2 a–e + admin f + AC2b) sakupljeni.
2. a11y CI job pokreće spec bar jednom protiv self-contained runserver-a tako da
   `axe.run()` VRATI realan result objekat (`{violations, passes, incomplete, inapplicable}`)
   za bar jednu stranu. Fabrikovan green ZABRANJEN.
3. Caveat OČUVAN: CI-job zahtev, NE Win host. `continue-on-error` na assert/budget ostaje
   (SM-D7). Ako a11y CI job još nije ožičen → eksplicitan TODO + OQ.
