---
story-id: 9-10-webp-avif-final-lighthouse-pass
title: WebP/AVIF + Final Lighthouse Pass
status: review
epic: 9 — Go-Live Readiness (Production + Quality)
risk_tier: MEDIUM
needs_e2e: false
e2e_count: 0
depends_on:
  - 9-9-a11y-audit-performance-load-test
  - 2-3-media-pipeline-responsive-picture
forward_dep: []   # POSLEDNJA story Epic-a 9 — zatvara epic
---

# Story 9.10 — WebP/AVIF + Final Lighthouse Pass

## Story / Opis

**As a** posetilac sa modernim browser-om,
**I want** slike (pre svega LCP hero) u WebP/AVIF formatu kad ih browser podržava,
**so that** se strana učitava brže (manji `total-byte-weight`, brži LCP), uz JPG fallback za starije browsere.

Ovo je **POSLEDNJA story Epic-a 9 (Go-Live Readiness)** — ona **ZATVARA epic**. Posle nje
ostaje samo `epic-9-retrospective` (optional). Scope je striktno: (1) optimizacija LCP hero
slike kroz `<picture>` AVIF/WebP/JPG, (2) **promocija Lighthouse budget gate-a iz report-only u
ENFORCED**, (3) finalni audit sign-off. **NIKAKAV novi scope van ovoga.**

---

## Acceptance Criteria

### AC1 — LCP hero konvertovan u AVIF + WebP, JPG zadržan, varijante komitovane
**Given** statička hero slika `static/img/home/home-hero-1.jpg` (eager/LCP element flagovan u 9.9 „NOTE-za-9.10")
**When** pokrenem reproducibilan konverzioni alat (Task 1)
**Then** u `static/img/home/` postoje `home-hero-1.avif` + `home-hero-1.webp` + zadržan `home-hero-1.jpg`
**And** generisane `.avif`/`.webp` varijante su **komitovane u repo** (binarni asset-i)
**And** svaka generisana varijanta je **STRIKTNO MANJA** od originalnog JPG-a (`home-hero-1.jpg` ≈ 413 KB) — realan očekivani rezultat za fotografski hero: AVIF i WebP su znatno manji. **NEMA escape hatch-a:** varijanta koja je `>=` od source-a **NE SME biti tiho komitovana** — konverzioni alat (Task 1.1) MORA fail-loud (warn + non-zero exit, ILI eksplicitni `--allow-larger` override flag) ako je generisana varijanta `>=` source JPG. Ovo se slaže sa Task 7.2 koji hard-asertuje `.avif`/`.webp` < `.jpg`. **Quality-tuning vodič:** ako je prvi encode veći od source-a, spusti `quality=` i re-enkoduj dok varijanta ne postane striktno manja.

### AC2 — Hero template koristi `<picture>` sa ispravnim redosledom source-ova
**Given** `templates/pages/partials/_home_hero.html` (trenutno plain `<img>`)
**When** zamenim plain `<img>` `<picture>` elementom
**Then** `<picture>` sadrži po redu: `<source type="image/avif" srcset="...avif">` **PRVI**, zatim `<source type="image/webp" srcset="...webp">`, zatim `<img src="...jpg">` kao **poslednji** (JPG fallback)
**And** browser bira prvi podržan format (AVIF → WebP → JPG)
**And** sva tri `srcset`/`src` koriste `{% static %}` (statički asset, NE media URL).

### AC3 — `alt` i `aria-hidden` očuvani EGZAKTNO (dekorativni hero)
**Given** trenutni `<img alt="" aria-hidden="true" ...>` (dekorativan, namerno prazan alt)
**When** prepravim u `<picture>`
**Then** `<img>` unutar `<picture>` zadržava **`alt=""`** + **`aria-hidden="true"`** EGZAKTNO — **NE izmišljaj alt tekst** (slika je dekorativna, semantiku nosi `<h1>` overlay)
**And** ako se bilo gde dodaje `alt` tekst na drugim slikama, koristi **pune dijakritike** (č/ć/ž/š/đ) — nikad šišana latinica (project-context anti-pattern).

### AC4 — LCP hero ostaje eager; below-the-fold slike ostaju lazy
**Given** hero je above-the-fold LCP element
**When** renderujem `<picture>`
**Then** `<img>` unutar `<picture>` zadržava **`loading="eager"`** (NE `lazy` — lazy na LCP element usporava LCP)
**And** opciono dodato `fetchpriority="high"` na hero `<img>` (LCP boost; additivno)
**And** below-the-fold slike (kroz `responsive_picture` default `loading="lazy"`) ostaju **netaknute** — nema regresije na lazy ponašanje.

### AC5 — Reproducibilan konverzioni alat postoji i dokumentovan je
**Given** host ima Pillow 12.2.0 sa native AVIF + WebP podrškom (verifikovano: `PIL.features.check('avif')==True`, `check('webp')==True`)
**When** kreiram konverzioni alat (Django management command `convert_static_images` — vidi Dev Notes za izbor)
**Then** alat čita izvorni JPG i emituje `.avif` + `.webp` varijante **idempotentno** — gde „idempotentno" znači **SKIP-IF-EXISTS** (ponovno pokretanje NE menja već-komitovani output osim ako se prosledi `--force`), a **NE** bit-identičan re-encode. (Pillow AVIF/WebP enkoderi NISU garantovano byte-reproducibilni preko verzija/run-ova — NE juri bit-reproducibilnost.)
**And** alat je dokumentovan (docstring + pominjanje u AUDIT-REPORT sign-off sekciji) tako da je asset-korak **reproducibilan** (ne ručno-jednokratan)
**And** generisane varijante su komitovane (AC1).

### AC6 — `lighthouserc.json` asserti prošireni
**Given** postojeći `lighthouserc.json` (9.9): `categories:accessibility>=0.95`, `largest-contentful-paint<2500`, `server-response-time<600`, `total-byte-weight<1572864`
**When** dodam finalne asserte iz epics.md 9.10
**Then** dodato `categories:best-practices` → `["error", { "minScore": 0.90 }]`
**And** dodato `categories:seo` → `["error", { "minScore": 0.95 }]`
**And** **postojeća 4 asserta ostaju netaknuta** (a11y/LCP/TTFB/total-byte).

### AC7 — `lighthouse.yml` Lighthouse autorun korak ENFORCED (gate promovisan)
**Given** `.github/workflows/lighthouse.yml` korak „Lighthouse CI autorun (collect + assert budgeti)" trenutno ima `continue-on-error: true` (report-only, SM-D7 baseline iz 9.9)
**When** promovišem budget gate u enforced
**Then** sa tog koraka je **uklonjen `continue-on-error: true`** → miss budžeta (a11y/LCP/TTFB/total-byte/best-practices/seo) **OBARA job**
**And** dokumentovano (u komentaru workflow-a i/ili AUDIT-REPORT) da su **v1 brojevi INDIKATIVNI** (`runserver --insecure` static NIJE prod nginx/Whitenoise) — **autoritativni go-live brojevi dolaze iz staging-targeted moda** (OQ).
**And** (odluka za Dev — vidi Dev Notes) axe `run-at-least-once` korak ostaje `continue-on-error` (a11y gate je već u `categories:accessibility` Lighthouse assertu; ne dupliraj enforce-ovanje — promovi SAMO Lighthouse autorun korak per AC formulaciji).
**And** **NON-ISSUE — gate NE može da obori Epic-9 merge u master:** `lighthouse.yml` se okida ISKLJUČIVO na `push: branches:[staging]` + `workflow_dispatch` (VERIFIKOVANO: linije 28-31 fajla), **NE na PR-ovima ni na master push-u**. Zato uklanjanje `continue-on-error` **NE MOŽE da „crveni" PR koji merge-uje 9.10 u master** — enforced gate puca tek na staging-push / ručni dispatch. Prvi realni RED se po dizajnu pojavljuje na staging push-u (očekivano i prihvatljivo — vidi AC10 honesty caveat za TTFB/LCP non-prod artefakte).

### AC8 — Nema slomljenih referenci na slike
**Given** `<picture>` source-ovi pokazuju na `.avif`/`.webp`/`.jpg`
**When** proverim postojanje fajlova
**Then** SVAKI `srcset`/`src` u hero `<picture>` pokazuje na fajl koji **fizički postoji** u `static/img/home/`
**And** nema 404 reference (test asertuje postojanje fajla za svaki path naveden u markup-u).
**And** **format/MIME ispravnost (vidi Task 7.2):** test MORA asertovati `PIL.Image.open(path).format == "AVIF"` za `.avif` path i `== "WEBP"` za `.webp` path — ovo hvata format/ekstenzija mismatch (npr. WebP byte-stream sačuvan na `.avif` path-u, što bi nateralo `<source type="image/avif">` da servira ne-AVIF fajl). Pillow je već prisutan (NEMA novog prod-dep-a).

### AC9 — Legacy-browser JPG fallback radi bez grešaka
**Given** browser koji ne podržava AVIF ni WebP (ili `<picture>` uopšte)
**When** renderuje hero
**Then** `<img src="...jpg">` unutar `<picture>` se prikazuje (legacy-safe — `<picture>` graceful degradacija na `<img>`)
**And** `<img>` ima validan `src` (NE samo `srcset` na source-ovima) tako da i browseri bez `<picture>` podrške vide sliku.

### AC10 — AUDIT-REPORT.md ažuriran finalnim sign-off-om
**Given** `ops/quality/AUDIT-REPORT.md` (9.9) ima sekciju „(e) NOTE za 9.10" o hero JPG-u
**When** zatvaram 9.10
**Then** AUDIT-REPORT.md je ažuriran novom **„Final Lighthouse pass / sign-off"** sekcijom koja dokumentuje: (a) image-weight optimizovan (hero AVIF/WebP + JPG fallback, KB pre/posle), (b) Lighthouse budget gate **ENFORCED** (koji asserti), (c) šta je mereno lokalno vs. šta je staging/CI-deferred (iskreno: v1 brojevi indikativni)
**And** sign-off **MORA EKSPLICITNO navesti KOJI asserti su pouzdani na v1 `runserver --insecure` vs. koji su staging-only** (iskrenost iznad zelene): `categories:accessibility` / `categories:best-practices` / `categories:seo` / `total-byte-weight` (posle AVIF/WebP) su **razumno smisleni i na v1** (content-kontrolisani), dok su `server-response-time` (TTFB) i apsolutni `largest-contentful-paint` (LCP) **najosetljiviji na non-prod `runserver --insecure` stack i AUTORITATIVNI SAMO na staging-u**. Sign-off MORA jasno reći da **staging-push RED na TTFB/LCP može biti non-prod artefakt — prihvatljiv/očekivan pre staging tuning-a**, NE nužno regresija u kodu.
**And** sign-off **MORA EKSPLICITNO zabeležiti ishod Task 3** (`responsive_picture` WebP `<source>` extension: **IMPLEMENTIRAN** ili **DEFERRED**) — bez ovog zapisa dev NE SME tiho preskočiti Task 3 (named-condition: Task 3 ishod je obavezan unos u sign-off).
**And** „NOTE za 9.10" iz sekcije (e) je razrešen (markiran kao DONE / referenca na sign-off sekciju).

---

## Tasks / Zadaci

### Task 1 — Konverzioni alat + generiši & komituj hero varijante (AC1, AC5)
- [x] 1.1 Kreiraj reproducibilan konverzioni alat: **Django management command** `apps/media_pipeline/management/commands/convert_static_images.py` (vidi Dev Notes za rationale — management command > stand-alone `scripts/` jer projekat nema `scripts/` dir, a `just` + `manage.py` su SOT). Command:
  - čita izvorne statičke JPG-ove (minimalno `static/img/home/home-hero-1.jpg`; opciono uzima listu/glob),
  - za svaki: `Image.open(src)` → `.save(dst.avif, format="AVIF", quality=…)` i `.save(dst.webp, format="WEBP", quality=…)`,
  - idempotentno = **SKIP-IF-EXISTS** (ponovno pokretanje NE menja committed output osim `--force`; NE juri bit-identičan re-encode — vidi AC5),
  - koristi `PIL.features.check('avif')` / `check('webp')` guard sa jasnom porukom ako format nedostaje (fail-loud, NE tiho preskoči),
  - **size-guard (AC1, NE tiho komituj veću varijantu):** posle svakog encode-a uporedi `dst` veličinu sa `src` JPG-om; ako je `dst >= src`, **fail-loud** (warn + non-zero exit) ILI zahtevaj eksplicitni `--allow-larger` override flag. Bez override-a, varijanta `>=` source-a se NE sme komitovati. Vodič: ako je prvi encode veći, spusti `quality=` i re-enkoduj.
- [x] 1.2 Kreiraj `apps/media_pipeline/management/__init__.py` i `.../management/commands/__init__.py` ako ne postoje (paket init-ovi).
- [x] 1.3 Pokreni alat → generiši `static/img/home/home-hero-1.avif` + `home-hero-1.webp`.
- [x] 1.4 Verifikuj veličine: `.avif` i `.webp` < `home-hero-1.jpg` (≈413 KB). Zabeleži KB vrednosti (idu u AUDIT-REPORT Task 6).
- [x] 1.5 **Komituj** generisane `.avif` + `.webp` binarne varijante zajedno sa command-om (atomic commit).

### Task 2 — Hero `<picture>` markup (AC2, AC3, AC4, AC9)
- [x] 2.1 U `templates/pages/partials/_home_hero.html` zameni plain `<img ... class="coric-home-hero__bg">` `<picture>` elementom:
  - `<source type="image/avif" srcset="{% static 'img/home/home-hero-1.avif' %}">` PRVI,
  - `<source type="image/webp" srcset="{% static 'img/home/home-hero-1.webp' %}">` drugi,
  - `<img src="{% static 'img/home/home-hero-1.jpg' %}" alt="" aria-hidden="true" loading="eager" class="coric-home-hero__bg">` poslednji.
  - **Opciono (additivno, full-bleed hero):** dodaj `sizes="100vw"` na `<source>`/`<img>` zbog korektnosti (hero je full-bleed); ne lomi ništa, čisto signal browseru.
- [x] 2.2 Očuvaj EGZAKTNO `alt=""`, `aria-hidden="true"`, `class="coric-home-hero__bg"`, `loading="eager"` (AC3/AC4). NE menjaj CSS klasu (CSS cilja `.coric-home-hero__bg` na `<img>`, ne na `<picture>`).
- [x] 2.3 **Preporučeno (SHOULD)** dodaj `fetchpriority="high"` na hero `<img>` (LCP boost; additivno, ne lomi ništa). Napomena: browseri primenjuju `fetchpriority` na `<img>`, **NE** pouzdano na `<source>` — drži ga na `<img>`.
- [x] 2.4 Single-line Django komentari (multi-line nije podržan — postojeći `{# ... #}` su single-line; zadrži taj stil).
- [x] 2.5 Provera: `djade templates/` clean nakon izmene.

### Task 3 — `responsive_picture` WebP source extension ILI dokumentovani defer (AC: scope honesty)
- [x] 3.1 Proceni da li je čisto izvodljivo proširiti `apps/media_pipeline/templatetags/media_tags.py` `responsive_picture` da emituje **dodatni `<source type="image/webp">`** za UPLOADED media (sorl `get_thumbnail(..., format="WEBP")` za isti 400/800/1600w set), uz `<img>` JPG fallback u `responsive_picture.html`.
- [x] 3.2 **AKO čisto izvodljivo** (≤ minimalna izmena tag-a + template-a, bez lomljenja postojećih caller-a): implementiraj WebP source set za uploaded media. **NE dodaj izmišljen `THUMBNAIL_FORMAT_FALLBACK` setting** (vidi Dev Notes — ne postoji u sorl-thumbnail-u).
- [x] 3.3 **AKO NIJE čisto izvodljivo** u scope-u (rizik regresije na 6+ caller-a iz Epic 2/3/5): **dokumentuj kao DEFERRED** u AUDIT-REPORT sign-off + Open Questions (uploaded-media WebP = post-go-live optimizacija). LCP hero (static, Task 2) je primarni i obavezan deliverable; uploaded-media WebP je opcioni.
- [x] 3.4 Šta god se izabere (3.2 ili 3.3) — **mora biti eksplicitno zabeleženo** (honesty over silent skip).

### Task 4 — `lighthouserc.json` proširi asserte (AC6)
- [x] 4.1 Dodaj u `assert.assertions`:
  - `"categories:best-practices": ["error", { "minScore": 0.90 }]`
  - `"categories:seo": ["error", { "minScore": 0.95 }]`
- [x] 4.2 NE diraj postojeća 4 asserta (a11y/LCP/TTFB/total-byte) ni `collect.url` listu.
- [x] 4.3 Validacija: JSON parse-able (`python -m json.tool lighthouserc.json`).

### Task 5 — `lighthouse.yml` enforce gate (AC7)
- [x] 5.1 U koraku **„Lighthouse CI autorun (collect + assert budgeti)"** ukloni liniju `continue-on-error: true` (linija ~180 u trenutnom fajlu, direktno iznad `run: npx @lhci/cli@0.14.x autorun`).
- [x] 5.2 Ažuriraj prateći komentar (SM-D7 baseline → sada ENFORCED): kratko objašnjenje da budget miss SADA obara job, uz caveat da su v1 (`runserver --insecure`) brojevi INDIKATIVNI; autoritativni = staging-targeted mod (OQ).
- [x] 5.3 **NE** uklanjaj `continue-on-error` sa drugih koraka (axe `run-at-least-once`, axe `collect-only`) — promovi SAMO Lighthouse autorun korak (a11y je već pokriven Lighthouse `categories:accessibility` assertom).
- [x] 5.4 Validacija: YAML valid (`python -c "import yaml; yaml.safe_load(open('.github/workflows/lighthouse.yml'))"`).

### Task 6 — AUDIT-REPORT.md finalni sign-off (AC10)
- [x] 6.1 Dodaj novu sekciju (npr. „(g) Final Lighthouse pass / sign-off (9.10)"):
  - image-weight: hero `home-hero-1.{jpg→avif/webp}` KB pre/posle (iz Task 1.4),
  - Lighthouse gate: ENFORCED — lista assert-a (a11y≥0.95, LCP<2500, TTFB<600, total-byte<1.5MB, best-practices≥0.90, seo≥0.95),
  - mereno lokalno vs. CI/staging-deferred: iskreno navedi da su v1 brojevi indikativni i da autoritativni dolaze iz staging-a (OQ),
  - status `responsive_picture` WebP extension (Task 3 ishod: implementiran ILI deferred).
- [x] 6.2 Razreši „(e) NOTE za 9.10" — markiraj hero stavku kao DONE sa referencom na novu sign-off sekciju.
- [x] 6.3 Ažuriraj „Go-live gates (OQ rezime)" tabelu: OQ-1 (Lighthouse hard-gate) — mehanizam ENFORCED u CI; preostaje **staging Lighthouse run** za realne brojeve.

### Task 7 — Testovi (markup-level / import-light) (svi AC)
- [x] 7.1 `apps/pages/tests/` ili `apps/media_pipeline/tests/` — markup test renderovanog hero partial-a (ili parse `_home_hero.html` izvora):
  - `<picture>` prisutan,
  - `<source type="image/avif">` se pojavljuje PRE `<source type="image/webp">` (redosled bitan — AC2),
  - `<img>` JPG fallback prisutan kao poslednji child,
  - `alt=""` + `aria-hidden="true"` očuvani (AC3),
  - `loading="eager"` na hero `<img>` (NE `lazy`) (AC4),
  - **`fetchpriority="high"` prisutnost na hero `<img>`** — assert/log koji čini odsustvo VIDLJIVIM (čak i ako je opciono): ako fali, test loguje warning/skip-marker (NE tihi prolaz), tako da omisija nije nevidljiva (AC4 SHOULD).
- [x] 7.2 Test postojanja + format-ispravnosti varijanti: za svaki path naveden u hero markup-u (`.avif`/`.webp`/`.jpg`) fajl **fizički postoji** u `static/img/home/` (AC8) **I** `.avif`/`.webp` su **striktno manji** od `.jpg` (AC1) **I** `PIL.Image.open(path).format` je `"AVIF"` za `.avif` path odn. `"WEBP"` za `.webp` path (AC8/AC9 format/MIME guard — hvata WebP-bytes-na-.avif-path mismatch; Pillow već prisutan, bez novog dep-a).
- [x] 7.3 Test `lighthouserc.json`: `best-practices` (≥0.90) i `seo` (≥0.95) asserti prisutni; postojeća 4 asserta i dalje prisutna (AC6). (Parse JSON, NE Lighthouse run.)
- [x] 7.4 Test `lighthouse.yml`: Lighthouse autorun korak **NEMA** `continue-on-error: true` (AC7). (Parse YAML, locate step `name` sadrži „Lighthouse CI autorun", assert key odsutan/false.)
- [x] 7.5 Test below-the-fold lazy očuvan: `responsive_picture` tag default `loading="lazy"` netaknut (AC4 regresija-guard — može biti tag unit test ili source assert).
- [ ] 7.6 (Ako Task 3.2 implementiran) test da `responsive_picture` emituje `<source type="image/webp">` za uploaded media; (ako 3.3 deferred) preskoči — bez fabrikovanog testa.

> **Host caveat (mirror Epic 9):** native-Win `pytest` collect pada na `libmagic` baseline (dokumentovani Epic-9 baseline — NIJE regresija). Testovi MORAJU biti import-light / markup-parse / file-stat (NE Playwright, NE Lighthouse run na hostu). Gde markup test zahteva Django template render, koristi izolaciju koju prethodne Epic-9 stories koriste (subprocess / `-p no:django` / RequestFactory) ili čist `pathlib`+`re` parse izvornog template fajla. **Stvarni Lighthouse brojevi = CI/staging gate, NE host-fabrikovani.**

---

## Dev Notes

### KRITIČNE rekoncilijacije (orchestrator pre-verifikovao — NE re-litigiraj)

**1. STATIC vs UPLOADED media split (centralna dizajn-odluka):**
- **STATIC slike** (`static/img/...`) NEMAJU build pipeline i NISU `ImageField` → sorl-thumbnail ih **NE procesira**. Zato dobijaju **ručno-pisani `<picture>`** sa **PRE-GENERISANIM** `.avif` + `.webp` + `.jpg` varijantama **komitovanim u repo**. Ovo je hero (LCP) put — primarni deliverable.
- **UPLOADED media** (`ImageField`) već teče kroz `apps/media_pipeline/templatetags/media_tags.py::responsive_picture` (sorl-thumbnail, srcset 400/800/1600w, `loading="lazy"` default, eager za above-fold). Renderuje `templates/media_pipeline/responsive_picture.html`. WebP source za uploaded media je **opciono proširenje** (Task 3) — implementiraj ako čisto, inače dokumentuj defer.

**2. NEMA izmišljenog sorl setting-a (epics.md AC reconcile):**
- epics.md 9.10 doslovno traži `THUMBNAIL_FORMAT_FALLBACK = ['avif', 'webp', 'jpg']`. **Taj setting key NE POSTOJI** u sorl-thumbnail-u. sorl podržava `THUMBNAIL_FORMAT` (jedan format) i per-call `format=`. Nema native multi-source AVIF/WebP fallback-a out-of-the-box.
- **NE cargo-cult-uj nepostojeći setting.** Realan scope v1: (a) LCP hero (static) dobija pravi `<picture>` AVIF/WebP/JPG; (b) opciono proširi `responsive_picture` da emituje WebP `<source>` za uploaded media AKO čisto izvodljivo, inače dokumentuj defer. **Iskrenost iznad lažnog setting-a.**

**3. TOOLING (host-verifikovano):**
- Pillow **12.2.0** na ovom hostu IMA native AVIF (`PIL.features.check('avif')==True`) **I** WebP (`check('webp')==True`). Binarne `.avif`/`.webp` varijante MOGU se generisati na hostu reproducibilnim Pillow alatom i komitovati.
- `cwebp`/`avifenc`/`pillow_avif` NISU instalirani — **native Pillow pokriva oba**, ne dodaji te dep-ove (YAGNI).
- **Izbor alata:** Django **management command** `convert_static_images` (u `apps/media_pipeline/management/commands/`) je preferiran nad stand-alone `scripts/convert_images.py` jer: projekat nema `scripts/` dir, `manage.py`/`just` su SOT za komande, i `media_pipeline` je prirodni dom za image-konverziju. (Ako Dev jako preferira stand-alone skriptu — prihvatljivo, ali mora biti reproducibilna i dokumentovana; AC5 ne mandira tačnu lokaciju, samo reproducibilnost.)

**4. LIGHTHOUSE HARD-GATE promocija (tačne ciljne linije):**
- 9.9 isporučio `lighthouserc.json` (asserts: `categories:accessibility>=0.95`, `largest-contentful-paint<2500`, `server-response-time<600`, `total-byte-weight<1572864`) + `.github/workflows/lighthouse.yml`.
- U `lighthouse.yml`, korak **„Lighthouse CI autorun (collect + assert budgeti)"** (oko linije 179-181) ima `continue-on-error: true` (linija ~180) direktno iznad `run: npx @lhci/cli@0.14.x autorun`. **9.10 UKLANJA tu liniju** → budget miss obara job.
- Takođe axe `run-at-least-once` korak (linija ~144) ima `continue-on-error: true` — **NE diraj ga** (a11y je već pokriven Lighthouse `categories:accessibility` assertom; ne dupliraj).
- epics.md 9.10 dodaje `best-practices≥0.90` i `seo≥0.95` finalnom passu → dodaj te asserte u `lighthouserc.json` (Task 4).
- **GATE-TRIGGER NON-ISSUE (VERIFIKOVANO):** `lighthouse.yml` se okida ISKLJUČIVO na `push: branches:[staging]` + `workflow_dispatch` (linije 28-31 fajla) — **NE na PR-ovima ni master push-u.** Posledica: uklanjanje `continue-on-error` **NE MOŽE da obori PR koji merge-uje 9.10 u master**; enforced budget gate fire-uje tek na staging-push / ručni dispatch. Prvi realni RED se po dizajnu pojavljuje na staging push-u. Time je strah „da li enforced gate blokira Epic-9 merge?" → dokumentovan NON-ISSUE.

**5. HOST-HONESTY o brojevima:**
- v1 `lighthouse.yml` vozi protiv `runserver --insecure` (NE prod nginx/Whitenoise/Gunicorn) → TTFB / total-byte-weight / LCP su **INDIKATIVNI**, ne prod-reprezentativni. **Autoritativni go-live brojevi dolaze iz staging-targeted moda** (OQ — `STAGING_BASE_URL` + secrets).
- Story MORA biti iskrena: realni Lighthouse brojevi su staging/CI gate, NE host-fabrikovan broj. AUDIT-REPORT sign-off (Task 6) eksplicitno razdvaja mereno-lokalno vs. staging-deferred.
- **KOJI asserti su pouzdani gde (sign-off MORA ovo navesti, AC10):** `categories:accessibility` / `categories:best-practices` / `categories:seo` / `total-byte-weight` (posle AVIF/WebP) su **content-kontrolisani → razumno smisleni i na v1 `runserver --insecure`**. Nasuprot tome, `server-response-time` (TTFB) i apsolutni `largest-contentful-paint` (LCP) su **najosetljiviji na non-prod stack i AUTORITATIVNI SAMO na staging-u**. **Staging-push RED na TTFB/LCP može biti non-prod artefakt (prihvatljiv/očekivan pre staging tuning-a) — NE nužno regresija u kodu.** Iskrenost iznad zelene.

### Postojeće stanje fajlova koji se menjaju (UPDATE — pročitano)

| Fajl | Trenutno stanje | Šta 9.10 menja | Šta očuvati |
| ---- | --------------- | -------------- | ----------- |
| `templates/pages/partials/_home_hero.html` | plain `<img src="{% static 'img/home/home-hero-1.jpg' %}" alt="" aria-hidden="true" loading="eager" class="coric-home-hero__bg">` unutar `<section class="coric-home-hero">`; ispod njega `__overlay` sa `<h1>`/lead/CTA | `<img>` → `<picture>` (AVIF/WebP/JPG) | `alt=""`+`aria-hidden="true"`+`loading="eager"`+`class="coric-home-hero__bg"` na `<img>`; overlay, `<h1>` `{% blocktranslate %}`, CTA NETAKNUTI; single-line `{# #}` komentar stil |
| `apps/media_pipeline/templatetags/media_tags.py` | `responsive_picture(image, alt, sizes, loading="lazy", css_class, crop, format="JPEG")` → srcset 400/800/1600w, `loading="lazy"` default, FIX-8 real width/height | (Task 3 opciono) dodaj WebP `<source>` set | NE lomi 6+ caller-a (Epic 2/3/5); `loading="lazy"` default; FIX-8 width/height logika |
| `templates/media_pipeline/responsive_picture.html` | `<picture>` sa samo `<img srcset>` (jedan format) | (Task 3 opciono) dodaj `<source type="image/webp">` | postojeći `<img>` fallback + `{% if image %}` guard |
| `lighthouserc.json` | 4 asserta + 5 URL-ova + numberOfRuns:3 | +2 asserta (best-practices, seo) | 4 postojeća asserta + collect.url + upload |
| `.github/workflows/lighthouse.yml` | Lighthouse autorun korak `continue-on-error: true` (SM-D7 baseline) | ukloni `continue-on-error` SAMO sa Lighthouse autorun koraka | axe koraci `continue-on-error` netaknuti; self-contained runserver setup netaknut |
| `ops/quality/AUDIT-REPORT.md` | sekcije (a)-(f) + „(e) NOTE za 9.10" (hero JPG) + OQ rezime | + finalni sign-off sekcija; razreši „(e)" NOTE | postojeće sekcije; „TBD — staging" honesty pattern |

### Ground-truth činjenice
- `static/img/home/home-hero-1.jpg` ≈ **413 KB** (verifikovano: 413348 B, mtime Jun 11). Drugi static hero: `static/img/home/hero-traktor.jpg` ≈ 33 KB (NIJE u scope-u v1 — opciono, vidi OQ).
- `apps/media_pipeline/` NEMA `management/` dir još — Task 1.2 ga kreira.
- Hero CSS (`.coric-home-hero__bg`) cilja `<img>` element; zato klasa ostaje na `<img>`, NE na `<picture>` (inače background-pozicioniranje puca).
- **CSS no-shift napomena (pre-empt buduće regresije):** `<picture>` je `display:inline` i nestilizovan; apsolutno-pozicioniran `.coric-home-hero__bg` `<img>` se pozicionira u odnosu na `.coric-home-hero` sekciju (najbliži pozicionirani predak), NE u odnosu na `<picture>` wrapper. Zato umotavanje `<img>` u `<picture>` **NE pomera layout**. Klasa ostaje na `<img>` (već mandirano).
- `<img alt="">` + `aria-hidden="true"` je **namerno** dekorativno (semantiku nosi `<h1>` u overlay-u) — project-context A11y must-have „alt="" za dekoraciju". **NE izmišljaj alt.**

### Project-context pravila relevantna ovde
- Pune dijakritike (č/ć/ž/š/đ) u SVAKOM user-facing tekstu (ako se igde dodaje alt/title) — ASCII samo u slug/URL/file-name.
- Performance must-haves: `loading="lazy"` ispod fold-a (očuvaj), `font-display: swap` (netaknuto), Whitenoise compressed manifest (static su Whitenoise-served u prod — generisane `.avif`/`.webp` će biti collectstatic-ovane i hash-busted automatski). **MIME-caveat (OQ-6):** Whitenoise mapira ekstenzija→mimetype; `.avif` je u Python `mimetypes` registru od **Python 3.13** (CI python), na starijim runtime-ovima može pasti na `application/octet-stream` — verifikuj served `Content-Type` na staging-u (`<picture>` selekcija je browser-side po `type=` i nije pogođena, ali byte-fetch može imati pogrešan mime). Non-blocking.
- A11y: `alt=""` za dekoraciju (hero), deskriptivan inače.
- Komentari samo za WHY (postojeći hero komentar objašnjava „dekorativna, eager LCP" — zadrži/proširi minimalno).

### Git intelligence (skorašnji Epic 9 obrazac)
Prethodne Epic-9 stories (9-6..9-9) su sve **non-app, infra/quality** deliverabli sa **import-light testovima** (file-parse / subprocess / `-p no:django` zbog libmagic baseline). 9.10 prati isti obrazac: markup-parse + file-stat testovi, 0 migracija, 0 novih prod-dep. Pillow je VEĆ prod-dep (sorl-thumbnail ga povlači) — konverzioni command ne dodaje dep.

---

## Testing

**Strategija:** import-light / markup-level / file-stat. **NE** Playwright, **NE** Lighthouse run na hostu (oba = CI/staging gate). Razlog: native-Win `pytest` collect pada na `libmagic` (dokumentovani Epic-9 baseline, NIJE regresija).

**Pokrivanje po AC:**
- AC1/AC8 → file-stat test: svaki path u hero markup-u postoji + `.avif`/`.webp` < `.jpg` (`pathlib.Path.stat().st_size`).
- AC2/AC3/AC4/AC9 → markup test renderovanog/parsiranog `_home_hero.html`: `<picture>` prisutan, AVIF-source PRE WebP-source, `<img>` JPG fallback poslednji sa validnim `src`, `alt=""`+`aria-hidden`+`loading="eager"` očuvani.
- AC6 → JSON parse `lighthouserc.json`: best-practices/seo asserti prisutni + 4 postojeća.
- AC7 → YAML parse `lighthouse.yml`: Lighthouse autorun korak nema `continue-on-error` (a axe korak ga zadržava — pozitiv+negativ).
- AC4 (regresija) → `responsive_picture` default `loading="lazy"` netaknut.
- Task 7.6 (uploaded WebP source) → samo ako Task 3.2 implementiran; ako 3.3 deferred, BEZ fabrikovanog testa.

**Lokacija testova:** `apps/pages/tests/test_home_hero_picture.py` (markup) + `apps/media_pipeline/tests/test_convert_static_images.py` ili `tests/` za config-fajl asserte (`lighthouserc.json` / `lighthouse.yml`) — Dev bira konzistentno sa postojećim Epic-9 testovima.

**Render-izolacija:** ako template render zahteva Django app-registry (libmagic crash), parsiraj izvor `_home_hero.html` kroz `pathlib`+`re` (statički markup, `{% static %}` predvidljiv) ILI render kroz subprocess/`-p no:django` izolaciju kao 9-6/9-9.

**Fabrikovani brojevi ZABRANJENI:** nijedan test ne sme tvrditi konkretan Lighthouse/LCP/TTFB broj sa hosta. Realni brojevi = CI/staging.

---

## Open Questions (go-live gates)

| OQ | Opis | Vlasnik / status |
| -- | ---- | ---------------- |
| OQ-1 | **Autoritativni staging Lighthouse run** = REALAN go-live gate. CI v1 enforce-uje budget na `runserver --insecure` (INDIKATIVNI brojevi); staging-targeted mod (`STAGING_BASE_URL` + secrets, 9.9 OQ-4) daje prod-reprezentativne brojeve. Pred go-live: pokreni staging Lighthouse i potvrdi a11y≥0.95 / LCP<2.5s / TTFB<600ms / total-byte<1.5MB / best-practices≥0.90 / seo≥0.95 na REALNOM stack-u. | Mihas / otvoren |
| OQ-2 | **Ostale statičke slike za `<picture>`?** v1 konvertuje SAMO LCP hero (`home-hero-1.jpg`). `static/img/home/hero-traktor.jpg` (≈33 KB) + ostali static asset-i = kandidati za naknadnu konverziju (post-go-live, ako Lighthouse total-byte miss to traži). Deferred. | Mihas / otvoren |
| OQ-3 | **AVIF browser-support prihvatanje.** AVIF nije podržan u veoma starim browserima → graceful fallback je WebP pa JPG (`<picture>` semantika to garantuje). Potvrdi da je biznis OK sa AVIF-first redosledom (best-effort + siguran fallback). | Mihas / otvoren |
| OQ-4 | **`responsive_picture` WebP za uploaded media (Task 3 ishod).** Ako Dev oceni da NIJE čisto izvodljivo bez regresije na 6+ caller-a → uploaded-media WebP optimizacija je DEFERRED post-go-live. Hero (static) je obavezan; uploaded-media WebP je opcioni. | Dev/Mihas / otvoren |
| OQ-5 | **Epic 9 close + retrospektiva.** 9.10 zatvara Epic 9. Posle merge-a: `epic-9` YAML flag → done preko Epic Orchestratora + `epic-9-retrospective` (optional). Nasleđeni 9.9 OQ-i (k6 staging run OQ-2, NVDA/keyboard potpis OQ-3, CI secrets OQ-4) ostaju ZASEBNI go-live gate-ovi van koda. | Mihas / otvoren |
| OQ-6 | **Whitenoise `.avif` MIME-type na staging-u (NON-BLOCKING).** Whitenoise servira static po ekstenzija→mimetype mapi. `.webp` je u Python `mimetypes` registru; `.avif` je registrovan u **Python 3.13** (CI python), ali na starijim Python runtime-ovima može biti serviran kao `application/octet-stream`. `<picture>` source SELEKCIJA je browser-side preko `type=` atributa i NIJE pogođena — ali byte-fetch može da vrati 200-sa-pogrešnim-mime na starijim runtime-ovima. **Akcija:** verifikuj served `Content-Type` za `.avif` na staging-u; ako treba, eksplicitno registruj mimetype (`mimetypes.add_type('image/avif', '.avif')` ili Whitenoise config). Non-blocking; dokumentovano. | Dev/Mihas / otvoren |

---

## SM Decisions (rezime)
- **SM-D1:** STATIC hero dobija ručni `<picture>` sa komitovanim AVIF/WebP/JPG; sorl NE procesira static (split static-vs-uploaded je centralna odluka).
- **SM-D2:** NEMA izmišljenog `THUMBNAIL_FORMAT_FALLBACK` setting-a (ne postoji u sorl) — iskrenost iznad cargo-cult-a.
- **SM-D3:** Konverzioni alat = Django management command `convert_static_images` (reproducibilan, idempotentan, Pillow native AVIF+WebP), generisane varijante KOMITOVANE.
- **SM-D4:** `alt=""`+`aria-hidden="true"` na hero `<img>` OČUVANI EGZAKTNO — dekorativan, NE izmišljaj alt.
- **SM-D5:** `loading="eager"` na LCP hero OČUVAN (NE lazy); opciono `fetchpriority="high"`; below-fold lazy netaknut.
- **SM-D6:** Lighthouse gate promocija = ukloni `continue-on-error` SAMO sa „Lighthouse CI autorun" koraka; axe korak netaknut; +best-practices/seo asserti.
- **SM-D7:** v1 CI brojevi INDIKATIVNI (`runserver --insecure`); autoritativni = staging (OQ-1). FABRIKOVANI brojevi zabranjeni.
- **SM-D8:** `responsive_picture` WebP za uploaded media = opciono (Task 3); implementiraj ako čisto, inače dokumentuj defer eksplicitno.
- **SM-D9:** Import-light/markup/file-stat testovi (mirror Epic-9 libmagic-baseline obrazac); 0 migracija, 0 novih prod-dep (Pillow već tu).
- **SM-D10:** Ova story ZATVARA Epic 9 — NIKAKAV scope van image-opt + Lighthouse enforce + audit sign-off.

---

_Story status: **ready-for-dev**. Ultimate context engine analiza završena — sveobuhvatan developer vodič kreiran (static-vs-uploaded split, no-fake-setting honesty, Pillow native AVIF+WebP tooling, tačne continue-on-error ciljne linije, host-honesty staging, file-path mapa)._
