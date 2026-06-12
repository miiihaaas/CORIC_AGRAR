# AUDIT REPORT — A11y + Performance (Story 9.9)

**Status: BASELINE / harness postavljen.** Autoritativno merenje je **staging/CI** (OQ-1..OQ-4),
NE Windows dev host. Brojevi koji nisu izmereni stoje kao **„TBD — staging run"**.
**Fabrikovani brojevi su ZABRANJENI** (iskrenost iznad zelene — AC8).

| Datum sastavljanja | 2026-06-12 |
| ------------------ | ---------- |
| Branch             | `story-9-9-a11y-audit-performance-load-test` |
| Host caveat        | Win host: pytest collect pada na `libmagic` baseline (dokumentovan kroz Epik 9); Playwright/Lighthouse/k6 NE izvršavaju na ovom hostu. Merenje = CI (`.github/workflows/lighthouse.yml`) + deploy-ovani staging (9-2). |

---

## (a) Scope — strane / alati / budgeti

### Strane pod auditom
| Strana | axe (WCAG 2.1 AA) | Lighthouse perf budget |
| ------ | :---------------: | :--------------------: |
| `/` (home) | ✅ | ✅ |
| `/sr/traktori/` (listing) | ✅ | ✅ |
| `/sr/proizvod/agri-tracking-tb804/` (product detail + galerija) | ✅ | ✅ |
| `/sr/kontakt/` (kontakt forma) | ✅ | ✅ |
| `/sr/blog/pet-saveta-za-prolecnu-setvu/` (blog post) | ✅ | ✅ |
| `/sr/kontakt/` POSLE HTMX swap-a (AC2b) | ✅ | — |
| `/admin-coric/` (login-gated) | ✅ (form labels) | ❌ izuzet (SM-D3 — login-gated, tuđi static markup, nije javni LCP target) |

### Alati
- **axe-core** kroz Playwright (`axe-playwright-python>=0.1.7`) — `tests/e2e/test_a11y_audit.py`, marker `a11y`.
- **Lighthouse CI** (`@lhci/cli`) — `lighthouserc.json`, `numberOfRuns: 3` (median, SM-D10).
- **k6** — `ops/perf/load_test.js` (manual go-live, OQ-2).
- **Manuelni checklist + NVDA** — `ops/quality/a11y-manual-checklist.md` (OQ-3).

### Budgeti (Lighthouse — `lighthouserc.json`)
| Metrika | Budget |
| ------- | ------ |
| `categories:accessibility` | ≥ **0.95** |
| `largest-contentful-paint` | < **2500 ms** |
| `server-response-time` (TTFB) | < **600 ms** |
| `total-byte-weight` | < **1572864 B** (1.5 MB) |

### Gate (axe)
- **Fail (gate):** `impact ∈ {critical, serious}` (po strani).
- **Log, NE fail:** `moderate` / `minor` (SM-D2 baseline pragmatizam → remediation Issue).

---

## (b) Baseline nalazi

### axe (WCAG 2.1 AA)
| Strana | critical | serious | moderate | minor |
| ------ | :------: | :-----: | :------: | :---: |
| `/` | TBD — CI axe run | TBD | TBD | TBD |
| `/sr/traktori/` | TBD | TBD | TBD | TBD |
| `/sr/proizvod/agri-tracking-tb804/` | TBD | TBD | TBD | TBD |
| `/sr/kontakt/` | TBD | TBD | TBD | TBD |
| `/sr/blog/pet-saveta-za-prolecnu-setvu/` | TBD | TBD | TBD | TBD |
| `/sr/kontakt/` (post-HTMX-swap) | TBD | TBD | TBD | TBD |
| `/admin-coric/` | TBD | TBD | TBD | TBD |

> **Win host NE izvršava axe** (libmagic + browser baseline). Realan axe result objekat
> (`{violations, passes, incomplete, inapplicable}`) dolazi iz CI a11y job-a
> (`lighthouse.yml` → „A11y axe spec — run-at-least-once", AC11). Posle prvog CI run-a upiši
> per-page count-ove ovde.

### Lighthouse
| Strana | a11y score | LCP | TTFB | total-byte-weight |
| ------ | :--------: | :-: | :--: | :---------------: |
| sve (gornje, admin izuzet) | TBD — staging Lighthouse run | TBD | TBD | TBD |

> **CAVEAT (AC4 / OQ-1):** CI v1 koristi `runserver --insecure` (static NIJE prod
> nginx/Whitenoise/Gunicorn) → TTFB / total-byte-weight / LCP su **INDIKATIVNI**, ne
> prod-reprezentativni. **Autoritativni brojevi = staging-targeted mod** (`STAGING_BASE_URL` +
> secrets, OQ-4). Upiši realne staging brojeve pred go-live (OQ-1).

### k6 load test
| Metrika | Rezultat |
| ------- | -------- |
| `http_req_duration` p(95) | TBD — staging k6 run (OQ-2) |
| `http_req_failed` rate | TBD |
| VU profil dostignut | TBD |

> Pokretanje: vidi [`ops/perf/README.md`](../perf/README.md). Manual go-live korak (OQ-2),
> NIKAD prod bez dogovora.

### Manuelni / NVDA
| Sekcija checklist-a | Rezultat |
| ------------------- | -------- |
| (a) Tastatura Tab/Esc | TBD — manuelni prolaz (OQ-3) |
| (b) Focus posle HTMX swap-a | TBD |
| (c) prefers-reduced-motion | TBD |
| (d) Kontrast 4.5:1 | TBD |
| (e) NVDA 1-UJ | TBD |

> Izvor: [`a11y-manual-checklist.md`](./a11y-manual-checklist.md). Tester potpisuje OQ-3 pred go-live.

---

## (c) Jeftine popravke primenjene u 9.9

Statička inspekcija ključnih template-a (base / header / nav / hero / traktori listing /
product detail / kontakt forma / footer) je pokazala da je projekat **već a11y-zreo**: svaki
`<img>` ima `alt` (provereno — 0 `<img>` bez `alt`), ikon-only dugmad/linkovi imaju `aria-label`,
ikone su `aria-hidden`, `<html lang>` je vezan na lokal, `font-display: swap` je na svim 7
`@font-face` blokova, `loading="lazy"` se koristi na below-the-fold slikama (`responsive_picture`
default), `width`/`height` su renderovani (CLS guard), a `prefers-reduced-motion` blok postoji u
19 komponentnih CSS fajlova. **Površina za jeftine popravke je zato mala** — primenjeno samo
trivijalno-sigurno (additivno, markup-lock-safe, Epic 5/6/7 lock netaknut):

| Fajl | Šta | Zašto |
| ---- | --- | ----- |
| `templates/partials/header.html` | Logo `alt="Coric Agrar"` → **`alt="Ćorić Agrar"`** (oba logo `<img>`) | Pune dijakritike u user-facing `alt` (project-context anti-pattern č/ć/ž/š/đ); screen-reader izgovara tačno brend ime. Additivno; ne dira `hero_overlay_card` partial koji testovi lock-uju. |
| `templates/partials/footer.html` | Footer logo `alt="Coric Agrar"` → **`alt="Ćorić Agrar"`** | Isto kao iznad. |

> **Lock-safety provera:** `tests/test_visual_components.py` asertuje `alt="Coric Agrar"` ali na
> **`hero_overlay_card`** partial-u (prosleđuje `brand_logo_alt` kao test param) — NE na
> header/footer logo-u. Header/footer izmene ga ne dotiču → 0 lock regresija.

> **NEMA host-merenja** za dalje popravke: Win host ne izvršava axe/Lighthouse, pa stvarni nalazi
> (kontrast brojevi, dinamičke violacije) dolaze TEK iz CI/staging run-a (OQ-1..OQ-3). Dodatne
> jeftine popravke koje CI axe otkrije unose se ovde u sledećoj iteraciji. (DoD disambiguacija
> Task 5.2: prazan/mali fix-set NIJE failure jer je obrazložen kao „nema host-merenja"; fabrikovane
> popravke bez nalaza su ZABRANJENE.)

---

## (d) „Fail item → GitHub Issue" putanja (OQ-5)

Svaki **non-trivijalni** axe/Lighthouse/manuelni fail koji se NE popravlja u 9.9 dobija GitHub
Issue. Predloženi labels: `a11y`, `perf`, `remediation`. Vlasnik/blocker-status: OQ-5 (Mihas/Dana).

### Ready-to-paste Issue template

```markdown
**Naslov:** [a11y/perf] <strana> — <kratak opis prekršaja>

**Strana / URL:** /sr/...
**Alat:** axe-core | Lighthouse | NVDA | manuelni checklist
**WCAG kriterijum:** npr. 1.4.3 Contrast (Minimum) — AA
**Impact:** critical | serious | moderate | minor
**Nalaz:** <šta je axe/Lighthouse/tester prijavio; rule id ako axe>
**Predlog fix-a:** <konkretan, markup-lock-safe predlog>
**Blocker za go-live?** da / ne (OQ-5 odluka)
**Labels:** a11y, remediation
```

### Backlog fail-ova (popunjava se posle CI/staging run-a)
- _(prazno — čeka prvi CI axe + staging Lighthouse run; TBD)_

---

## (e) NOTE za 9.10 (scope-defer — NE konvertuj ovde)

Story 9.10 (WebP/AVIF konverzija + finalni Lighthouse pass) ostaje **DEFERRED**. Image-weight /
format nalazi se OVDE **beleže, NE rešavaju** (SM-D4 / AC10):

- **Hero foto-pozadina** (`static/img/home/home-hero-1.jpg`, eager/LCP element): JPG, potencijalni
  `total-byte-weight` / LCP doprinos. **NOTE za 9.10:** kandidat za WebP/AVIF + `responsive_picture`
  + dimenzionisanje. NE konvertovati u 9.9. **✅ DONE u 9.10** — hero konvertovan u AVIF+WebP `<picture>`
  (JPG fallback zadržan); vidi sekciju **„(g) Final Lighthouse pass / sign-off (9.10)"** za KB brojeve.
- **Bilo koji `total-byte-weight > 1.5MB` Lighthouse miss** posle staging run-a verovatno potiče od
  ne-optimizovanih rasterskih slika → **NOTE za 9.10**, ne hard-fix u 9.9 (SM-D7: lhci assert je
  `continue-on-error` u v1 upravo zbog ovoga).
- Konkretni image-weight brojevi: **TBD — staging Lighthouse run** (OQ-1).

---

## (f) Disclaimer — axe-green ≠ dokazan WCAG 2.1 AA (AC7f)

> **„0 critical axe violation" je NUŽAN, ali NE DOVOLJAN uslov za WCAG 2.1 AA.**
>
> Automatizovani axe-core pokriva samo **~30–40%** WCAG kriterijuma. **NE dokazuju se axe-om:**
> - **kontrast** (1.4.3) — spot-check manuelno (checklist d),
> - **keyboard-only navigacija** i **focus-order / focus management** (2.1.1, 2.1.2, 2.4.3) — manuelno (checklist a, b),
> - **`prefers-reduced-motion`** (2.3.3) — manuelno (checklist c),
> - **screen-reader razumevanje** (1.3.1, 4.1.2, 4.1.3) — NVDA (checklist e).
>
> WCAG 2.1 AA tvrdnja zahteva **i** axe-green (CI) **i** prolaz manuelnog checklist-a (AC6) **i**
> NVDA pass (OQ-3). Ovaj izveštaj NE tvrdi AA dok sve tri komponente nisu zelene na staging-u.

---

## (g) Final Lighthouse pass / sign-off (9.10)

Story 9.10 zatvara Epic 9. Ova sekcija je finalni **sign-off** image-weight optimizacije +
promocije Lighthouse budget gate-a u **ENFORCED**.

**Image-weight optimizovan (hero LCP)**

`static/img/home/home-hero-1.{jpg → avif/webp}` — generisano reproducibilnim Django mgmt
command-om `convert_static_images` (Pillow native AVIF+WebP; idempotentno = skip-if-exists,
`--force` regen). Sve varijante **komitovane u repo** kao binarni asset-i. JPG zadržan kao
legacy fallback. `<picture>` redosled: AVIF → WebP → JPG.

| Varijanta | Veličina | vs JPG | Format (PIL) |
| --------- | -------: | -----: | ------------ |
| `home-hero-1.jpg` (source) | **413348 B** (≈ 403.7 KB) | — | JPEG |
| `home-hero-1.avif` | **167704 B** (≈ 163.8 KB) | **−59.4 %** | AVIF (q=60) |
| `home-hero-1.webp` | **244132 B** (≈ 238.4 KB) | **−40.9 %** | WEBP (q=80) |

Obe varijante su **STRIKTNO manje** od source JPG-a (AC1 size-guard zadovoljen; command
fail-loud-uje na `>=` osim sa `--allow-larger`). Format/MIME potvrđen `PIL.Image.open(...).format`
== `AVIF`/`WEBP` (hvata bytes-na-pogrešnoj-ekstenziji mismatch). Hero `<img>` zadržava
`alt=""` + `aria-hidden="true"` + `loading="eager"` + `class="coric-home-hero__bg"` egzaktno,
+ dodato `fetchpriority="high"` (LCP boost).

**Lighthouse budget gate — ENFORCED**

`continue-on-error: true` je **UKLONJEN** sa koraka „Lighthouse CI autorun" u
`.github/workflows/lighthouse.yml` → budget miss **OBARA job**. Gate je sada **ENFORCED**
(promovisan iz report-only / SM-D7 baseline). Axe `run-at-least-once` korak ZADRŽAVA
`continue-on-error` (a11y je već pokriven `categories:accessibility` Lighthouse assertom —
ne dupliramo enforce).

Enforced asserti (`lighthouserc.json`):

| Assert | Budget | Pouzdan na v1 `runserver --insecure`? |
| ------ | ------ | ------------------------------------- |
| `categories:accessibility` | ≥ 0.95 | ✅ DA — content-kontrolisan |
| `categories:best-practices` | ≥ 0.90 | ✅ DA — content-kontrolisan |
| `categories:seo` | ≥ 0.95 | ✅ DA — content-kontrolisan |
| `total-byte-weight` | < 1572864 B (1.5 MB) | ✅ razumno (posle AVIF/WebP) — content-kontrolisan |
| `server-response-time` (TTFB) | < 600 ms | ⚠️ **STAGING-only autoritativan** — najosetljiviji na non-prod stack |
| `largest-contentful-paint` (LCP) | < 2500 ms | ⚠️ **STAGING-only autoritativan** (apsolutni LCP) |

**HONESTY caveat (SM-D7):** v1 CI vozi protiv `runserver --insecure` (NE prod
nginx/Whitenoise/Gunicorn) → TTFB i apsolutni LCP su **INDIKATIVNI**, ne prod-reprezentativni.
**Autoritativni go-live brojevi dolaze iz staging-targeted moda** (`STAGING_BASE_URL` + secrets,
OQ-1/OQ-4). **Staging-push RED na TTFB/LCP MOŽE biti non-prod artefakt — prihvatljiv/očekivan
pre staging tuning-a, NE nužno regresija u kodu.** Gate se okida samo na push:[staging] +
workflow_dispatch → enforcing NE može oboriti master merge PR. **Fabrikovani Lighthouse score
brojevi su ZABRANJENI** — gore su SAMO realno izmerene KB veličine + gate mehanizam; realni
Lighthouse score-ovi = staging/CI gate.

**Task 3 ishod — `responsive_picture` WebP `<source>` za uploaded media: DEFERRED**

Proširenje `responsive_picture` tag-a da emituje dodatni `<source type="image/webp">` za
**uploaded** media (sorl `get_thumbnail(..., format="WEBP")`) je **DEFERRED** (post-go-live
optimizacija). Razlog: 6+ caller-a kroz Epic 2/3/5 (brand logo, product main/galerija, blog
cover, home carousel) → izmena nosi regresioni rizik na Epic-zatvarajućoj story-ji. Primarni
obavezni deliverable (static LCP hero `<picture>`) je isporučen; uploaded-media WebP je opcioni
(SM-D8 / OQ-4). `responsive_picture` default `loading="lazy"` ostaje **NETAKNUT** (below-the-fold
lazy regresija-guard). Uvođenje uz pun re-run `media_pipeline` test suite-a = post-go-live.

---

## Go-live gates (OQ rezime)

| OQ | Opis | Status |
| -- | ---- | ------ |
| OQ-1 | Lighthouse hard-gate vs report-only + **staging** Lighthouse run (realni brojevi) — **mehanizam ENFORCED u CI (9.10)**; preostaje autoritativni **staging Lighthouse run** za realne TTFB/LCP brojeve | otvoren (Mihas) |
| OQ-2 | k6 load test izvršenje protiv staging-a + upis rezultata | otvoren |
| OQ-3 | NVDA manuelni pass + keyboard/focus/reduced-motion checklist potpis | otvoren |
| OQ-4 | CI secret/URL za staging-targeted mod (`STAGING_BASE_URL` + `DJANGO_SUPERUSER_PASSWORD` + LHCI token) | otvoren |
| OQ-5 | fail → GitHub Issue vlasnik / labela / blocker-status | otvoren |
