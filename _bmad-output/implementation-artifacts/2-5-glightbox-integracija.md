---
story-id: "2.5"
story-key: 2-5-glightbox-integracija
title: GLightbox Integracija
status: review
epic_num: 2
epic_title: Public Catalog — Browse Brands & Products
module: cross-cutting frontend (static/vendor/glightbox/ + static/js/lightbox-init.js + static/css/components/lightbox.css + templates/base.html Edit)
created: 2026-05-30
last_modified: 2026-05-30
author: Mihas (SM autonomous)
vendor_assets_present: true  # Mihas preuzeo GLightbox 3.x pre Dev GREEN phase (2026-05-30)
---

# Story 2.5: GLightbox Integracija

Status: ready-for-dev

## Story

As a **posetilac sajta (Marko — poljoprivrednik koji istražuje katalog traktora i mehanizacije; Đorđe — Mihasov klijent koji testira sajt na mobilnom uređaju)**,
I want **klik (ili Enter/Space sa tastature) na sliku u galeriji proizvoda otvara puni-ekran Lightbox sa swipe podrškom na touch uređajima, Tab/Arrow keys navigacijom između slika, Esc za zatvaranje, focus trap dok je otvoren, i automatski focus restoration nazad na trigger element pri zatvaranju**,
so that **mogu detaljno (pixel-precizno) da pregledam slike traktora, priključne mehanizacije i radnih mašina pre nego što popunim kontakt formu — koristim tastaturu jer mi smetaju mali touch targeti na telefonu (Marko), ili koristim VoiceOver/NVDA i očekujem da modal bude proglašen kao `role="dialog"` sa `aria-modal="true"` (Đorđev test scenario u Story 9.9 a11y audit)**.

**Pre-flight:** `vendor_assets_present: false` u frontmatter — Mihas mora preuzeti GLightbox 3.x sa GitHub Releases (AC1) i flipovati na `true` pre nego što Dev počne implementaciju (Task 2+).

Ova story je **infrastructure pre-requisite** za Story 2.7 (Product Detail strana) koja je **prvi konzument** Lightbox-a (galerija proizvoda + Lightbox zoom na klik variant kartice). Story 2.5 NE renderuje nijednu konkretnu galeriju — samo postavlja **kanonski init pattern** koji Story 2.7 i kasnije strane (Story 3.1 Home masonry, Story 5.3 Blog post slike) konzumiraju kroz prosto markup-anje `<a class="glightbox" href="..." data-gallery="...">` linkova.

Ova story je **prvi konzument projekta za `static/vendor/glightbox/`** direktorijuma (uvodi ga) i **prvi konzument `static/js/lightbox-init.js`** module (vanilla JS, no build pipeline — per project-context.md § Frontend deps + § JavaScript style). Konzumira postojeću infrastrukturu iz Story 1.6 (base.html script ordering pattern: htmx defer → Bootstrap sync → site-wide custom JS defer → block scripts) i Story 1.8 (`sticky-nav.js` IIFE + IntersectionObserver vanilla JS pattern — Story 2.5 prati isti stil).

**Foundation za:**

- **Story 2.7 (Product Detail strana):** glavni konzument. Galerija proizvoda renderuje `<a class="glightbox" data-gallery="product-{{ product.slug }}" href="{{ image.url }}">{% responsive_picture image ... %}</a>` — klik otvara Lightbox sa svim galerijskim slikama tog proizvoda. Variant selektor (per epics.md AC line 620): `<a class="glightbox" data-gallery="variant-{{ product.slug }}" href="{{ variant.image.url }}">` — klik na variant karticu otvara Lightbox bez side-effects (no state change).
- **Story 3.1 (Home strana):** opciono — ako home masonry galerija O nama (Story 3.2) zahteva Lightbox za sliku zoom.
- **Story 5.3 (Blog post detail):** opciono — slike unutar blog post body-ja mogu imati `class="glightbox"` marker za zoom.
- **Story 9.9 (a11y audit + Lighthouse pass):** verifikuje WCAG 2.1 AA compliance za Lightbox kroz axe-core + Playwright keyboard nav testove (Esc, Tab cycle, focus restoration).
- **Story 9.8 (Playwright E2E za UJ-1):** UJ-1 Marko journey može uključivati klik na sliku proizvoda → Lightbox open → swipe/Arrow → close → focus return na originalan element.

**Princip:** Lokalno hostovan GLightbox 3.x (CSS + JS) u `static/vendor/glightbox/`, jedan vanilla JS init modul (`static/js/lightbox-init.js`) sa **idempotent re-init handler-om** za HTMX swap scenarije (Story 2.8 tractor listing HTMX filter može dovesti nove slike u DOM — listener na `htmx:afterSwap` re-inicijalizuje Lightbox za novo dodate `.glightbox` elemente preko `GLightbox().reload()` API-ja). Jedan CSS override fajl (`static/css/components/lightbox.css`) za tematizaciju backdrop-a (`rgba(15,15,15,0.85)` per DESIGN.md § Elevation & Depth + EXPERIENCE.md § Lightbox linija 170) i `prefers-reduced-motion` respect. Base.html dobija **JEDAN dodatak**: GLightbox CSS link u `<head>` (između tokens.css i Bootstrap) i `lightbox-init.js` script tag (POSLE Bootstrap, defer) — mirror Story 1.8 pattern za sticky-nav.js. **NEMA backend promena, NEMA Django app changes, NEMA migracija, NEMA Python koda** — pure frontend story.

**Strukturna arhitektura — repository delta:** Repository dobija **5 novih fajlova** + **1 Edit** + **1 Edit u main.css** + **0 Python promena**:

| Path | Tip | Razlog |
|---|---|---|
| `static/vendor/glightbox/glightbox.min.css` | NOVO | GLightbox 3.x CSS — lokalno hostovan (no CDN, no googleapis fetch) |
| `static/vendor/glightbox/glightbox.min.js` | NOVO | GLightbox 3.x JS — lokalno hostovan (~10 KB gzipped per architecture.md AR-35 + § JavaScript decisions linija 202) |
| `static/js/lightbox-init.js` | NOVO | Vanilla JS init modul — IIFE, idempotent, HTMX-aware re-init, focus restoration verifikacija, `prefers-reduced-motion` respect |
| `static/css/components/lightbox.css` | NOVO | Custom CSS override — backdrop `rgba(15,15,15,0.85)` (per DESIGN.md § Modal/Lightbox linija 287) + `prefers-reduced-motion` |
| `static/css/main.css` | EDIT | Dodaje `@import url('./components/lightbox.css');` linija (per Story 1.7 + 1.8 pattern — `url(...)` wrapper konvencija) |
| `templates/base.html` | EDIT | Dodaje GLightbox CSS link u `<head>` (POSLE tokens.css, PRE Bootstrap CSS) + `<script src="...lightbox-init.js" defer></script>` POSLE `sticky-nav.js` (defer + site-wide) |
| `tests/test_lightbox_integration.py` | NOVO (TEA) | File existence + base.html cascade + main.css @import + ne-koristi-CDN guard testovi (mirror `tests/test_navigation_chrome.py` + `tests/test_static_tokens.py` pattern); E2E keyboard nav je Story 9.8 scope |

Postojeći fajlovi koji ostaju **NETAKNUTI** (regression guards): `apps/core/`, `apps/products/`, `apps/brands/`, `apps/media_pipeline/` (Story 2.4 deliverable — nema novih Python signala), `templates/partials/header.html`, `templates/partials/footer.html`, `static/js/sticky-nav.js`, `static/css/tokens.css`, `static/css/components/*.css` (osim main.css @import line), `static/vendor/htmx.min.js`, `static/vendor/bootstrap-5.3.3/`, `pyproject.toml` (NEMA novih Python deps — GLightbox je vendored static asset, ne PyPI paket), `config/settings/base.py`, `compose/django/Dockerfile` (no system deps potrebne za frontend lib).

## Kriterijumi prihvatanja

**AC1 — Direktorijum `static/vendor/glightbox/` postoji sa GLightbox 3.x CSS + JS asset-ima (lokalno hostovan)**

- **Given** projekat iz Story 1.8 (`static/vendor/` postoji sa `htmx.min.js` + `bootstrap-5.3.3/` poddirektorijumom; `static/vendor/htmx.min.js` je Mihas-ručno-downloadovan per Story 1.8 Task 4.1 pattern)
- **When** Mihas preuzima GLightbox 3.x release artifakte sa **`https://github.com/biati-digital/glightbox/releases`** (preporuka: latest 3.x tag — npr. 3.3.0 ili noviji; **NIKAD master/main grana** — pin na konkretan release tag za reproducibility) i smešta **TAČNO 2 fajla** u `static/vendor/glightbox/`:
  - `static/vendor/glightbox/glightbox.min.css` (~6 KB)
  - `static/vendor/glightbox/glightbox.min.js` (~30 KB raw / ~10 KB gzipped per architecture.md AR-35 referenca linija 202)
- **Then** struktura mora postojati i fajlovi moraju biti validni:
  - Oba fajla MORAJU biti **minified** (jedna logička linija, no source maps inline). Ako Mihas omaške preuzme `glightbox.js` (unminified, ~80 KB), Dev MORA preimenovati ga u `glightbox.min.js` ALI dokumentovati u Dev Agent Record `File List` da treba zameniti sa pravim `.min` build-om pre production deploy-a.
  - CSS fajl MORA počinjati sa `.glightbox-clean` ili `.gslide` selektorom (sanity check da je to GLightbox CSS a ne placeholder).
  - JS fajl MORA exportovati `GLightbox` constructor na `window` (sanity check — module exposes global; Dev verifikuje grep-om `window.GLightbox` ili `GLightbox=` u minified source).
- **And** licenca GLightbox = **MIT** (kompatibilna sa projektom; bez attribution u UI; komentar u `static/css/components/lightbox.css` referencira `https://github.com/biati-digital/glightbox` + verziju + datum download-a).
- **And** **NIKAKAV CDN reference** (no `https://cdn.jsdelivr.net/...glightbox...`, no `https://unpkg.com/glightbox...`, no `https://cdnjs.cloudflare.com/...glightbox...`) u celom code-base-u (verifikuj grep-om za string `glightbox` u `templates/`, `static/css/`, `static/js/` — sva referenca MORA biti relativna `{% static 'vendor/glightbox/...' %}`).
- **Napomena za Dev:** ako u trenutku implementacije fajlovi NISU prisutni (Mihas ih nije još download-ovao), Dev mora **HALT-ovati** sa explicit porukom u Dev Agent Record `Completion Notes`: `"BLOCKED: Mihas mora preuzeti GLightbox 3.x sa https://github.com/biati-digital/glightbox/releases (najnoviji 3.x tag, minified dist/glightbox.min.css + dist/glightbox.min.js), smestiti u static/vendor/glightbox/, i dokumentovati exact version u Story Dev Agent Record."` Tek po prisustvu 2 fajla Dev nastavlja sa AC2-AC7.

**AC2 — `static/js/lightbox-init.js` postoji sa kanonskim init pattern-om (IIFE + idempotency + HTMX swap re-init + reduced-motion respect)**

- **Given** AC1 završen (`glightbox.min.js` postoji); Story 1.8 `sticky-nav.js` pattern (vanilla JS, IIFE, no globals, no jQuery — verifikovano live na `static/js/sticky-nav.js` linija 9-50)
- **When** kreiram `static/js/lightbox-init.js`
- **Then** fajl mora imati TAČNO sledeću strukturu (mirror Story 1.8 `sticky-nav.js` IIFE pattern + GLightbox lifecycle integration):
  ```javascript
  /**
   * lightbox-init.js - GLightbox initialization (Story 2.5).
   *
   * Vanilla JS, IIFE, no global window pollution beyond GLightbox global,
   * no jQuery. Initializes GLightbox 3.x for all `.glightbox` selectors on
   * DOMContentLoaded; re-initializes on htmx:afterSwap to pick up new gallery
   * items from HTMX filter responses (Story 2.8 tractor listing, Story 2.13
   * search dropdown — out-of-scope here, but the contract honors them).
   *
   * Respects prefers-reduced-motion: disables open/close animations (per
   * EXPERIENCE.md § Animacije linija 271 — Lightbox fade-in 200ms ease, but
   * reduced-motion users see instant transition).
   *
   * Idempotency: stores instance on window._coricLightbox to prevent double-
   * init from competing scripts; reload() called on htmx:afterSwap for new
   * selectors.
   *
   * Emits coric:lightbox-open and coric:lightbox-close custom events on
   * window with detail.instance payload (per project-context.md § JavaScript
   * style — coric: namespace) so other modules can hook (e.g., pause auto-
   * advance slider while Lightbox is open — Story 2.6 testimonijal slider).
   */
  (function () {
    'use strict';

    if (typeof window === 'undefined' || typeof document === 'undefined') {
      return;
    }
    if (typeof window.GLightbox !== 'function') {
      // GLightbox vendor script not loaded — bail silently. Tests AC2 + AC4
      // verify the script tag is present in base.html, but defensive guard
      // protects against vendor-asset 404 not breaking the page.
      return;
    }

    // i18n: <html lang> attribute is set by Story 1.4 LocaleMiddleware.
    // Maps locale to GLightbox "More" button text; fallback to sr.
    var MORE_TEXT = {
      sr: 'Više',
      hu: 'Több',
      en: 'More'
    };

    function getLocale() {
      return (document.documentElement.lang || 'sr').slice(0, 2);
    }

    function buildOptions() {
      // Compute prefers-reduced-motion INSIDE buildOptions so each re-init
      // (htmx:afterSwap, matchMedia change) picks up the current OS preference.
      var prefersReducedMotion = window.matchMedia
        ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
        : false;

      return {
        selector: '.glightbox',
        touchNavigation: true,
        loop: false,
        zoomable: true,
        draggable: !prefersReducedMotion,
        openEffect: prefersReducedMotion ? 'none' : 'fade',
        closeEffect: prefersReducedMotion ? 'none' : 'fade',
        slideEffect: prefersReducedMotion ? 'none' : 'slide',
        moreText: MORE_TEXT[getLocale()] || MORE_TEXT.sr,
        descPosition: 'bottom'
      };
    }

    function initLightbox() {
      // Idempotency: destroy previous instance before re-init (HTMX swap path)
      if (window._coricLightbox && typeof window._coricLightbox.destroy === 'function') {
        window._coricLightbox.destroy();
        window._coricLightbox = null;
      }
      var instance = window.GLightbox(buildOptions());
      window._coricLightbox = instance;

      // Custom events on window — coric: namespace per project-context.md
      // Other modules (slider auto-advance pause, future analytics) can hook
      // to pause/resume during Lightbox open. detail.instance daje konzumentima
      // referencu na aktivni GLightbox instance (instance.getActiveSlideIndex?.()
      // pruža indeks trenutne slike). Tests AC5 verify dispatch.
      if (instance && typeof instance.on === 'function') {
        instance.on('open', function () {
          window.dispatchEvent(new CustomEvent('coric:lightbox-open', {
            detail: { instance: instance }
          }));
        });
        instance.on('close', function () {
          window.dispatchEvent(new CustomEvent('coric:lightbox-close', {
            detail: { instance: instance }
          }));
        });
      }
    }

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', initLightbox);
    } else {
      initLightbox();
    }

    // HTMX integration: re-init after swap so new .glightbox elements work.
    // Listener is safe even if django-htmx is not in flight on this page
    // (event simply never fires). No tight coupling to django-htmx.
    document.body.addEventListener('htmx:afterSwap', function () {
      // Guard: skip re-init if Lightbox is currently open
      // (HTMX OOB updates can fire while modal is open — don't yank focus)
      if (window._coricLightbox && window._coricLightbox.opened) {
        return;
      }
      initLightbox();
    });

    // Live-update on OS preference change (mirror sticky-nav.js pattern)
    var motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    if (motionQuery.addEventListener) {
      motionQuery.addEventListener('change', initLightbox);
    }
  })();
  ```
- **And** fajl MORA biti **IIFE** wrapped (`(function () { ... })();`) — no top-level global pollution beyond `window._coricLightbox` instance handle (per project-context.md § JavaScript style — vanilla JS preferred, no jQuery, no module bundler).
- **And** fajl MORA imati `'use strict';` direktivu (Story 1.8 pattern — linija 10 `sticky-nav.js`).
- **And** fajl MORA respektovati `prefers-reduced-motion: reduce` (per project-context.md § A11y must-haves linija 689 + NFR-2 + UX-DR-13 explicit text "prefers-reduced-motion: reduce smanjuje animacije").
- **And** fajl MORA emitovati `coric:lightbox-open` + `coric:lightbox-close` custom events na `window` sa `detail: { instance: instance }` payload-om (per project-context.md § JavaScript style — `coric:` namespace; architecture.md § Naming conventions linija 313 — `coric:lightbox-open` je dokumentovan primer). `detail.instance` daje konzumentima (Story 2.6 slider auto-advance pause, future analytics) referencu na aktivni GLightbox instance — `instance.getActiveSlideIndex?.()` pruža indeks trenutne slike.
- **And** fajl MORA biti idempotent — pri ponovnom `initLightbox()` pozivu (npr. iz `htmx:afterSwap`), prethodni `window._coricLightbox` instance SE destroy-uje pre nego što se kreira novi (sprečava memory leak + duplikate event listenere).
- **And** fajl MORA imati defensive guard: ako `window.GLightbox` nije function (vendor script nije loaded ili je 404), fajl SILENTLY return-uje bez throw-ovanja exception-a (page mora continue da radi čak i ako Lightbox vendor failu-je da loadu-je).
- **And** **NEMA** jQuery, **NEMA** Alpine.js dependency, **NEMA** import/export statements (no ES module build pipeline u v1 per project-context.md § Frontend deps).
- **And** **NEMA** inline event handlers (`onclick=`, `onkeydown=`) bilo gde — sve listener-e dodaje JS preko `addEventListener` (CSP-friendly per architecture.md § CSP linija 182).

**AC3 — `static/css/components/lightbox.css` postoji sa custom backdrop temom + reduced-motion override**

- **Given** AC1 završen (`glightbox.min.css` postoji u `static/vendor/glightbox/`); DESIGN.md § Elevation & Depth linija 287 specifikuje: "Modal / Lightbox: backdrop `rgba(15,15,15,0.85)`; modal bez dodatne senke"; EXPERIENCE.md § Lightbox linija 170 specifikuje backdrop boju identično
- **When** kreiram `static/css/components/lightbox.css`
- **Then** fajl mora sadržati:
  ```css
  /*
   * lightbox.css - GLightbox theme overrides (Story 2.5).
   * Vendor CSS: static/vendor/glightbox/glightbox.min.css (MIT, biati-digital/glightbox 3.x)
   * Custom theme:
   *  - Backdrop boja prati DESIGN.md § Modal/Lightbox: rgba(15,15,15,0.85)
   *  - prefers-reduced-motion: instant transition (no fade)
   */

  /* Backdrop boja — override GLightbox default-a koji je rgba(0,0,0,0.92).
   * DESIGN.md frontmatter ne eksponuje explicit token za modal backdrop —
   * koristi se hardcoded rgba() iz DESIGN.md § Elevation & Depth linija 287
   * (single source). Ako se kasnije uvede `--color-backdrop-modal` token u
   * tokens.css, ovo pravilo treba prepisati na var(--color-backdrop-modal).
   *
   * Backdrop = `.goverlay` (per GLightbox 3.x markup) — NIKAD `.gcontainer`
   * (to je modal content wrapper). `.glightbox-clean` je default skin koji
   * ships sa GLightbox 3.x (jedini skin koji se garantovano isporučuje).
   */
  .glightbox-clean .goverlay {
    background: rgba(15, 15, 15, 0.85) !important;
  }

  /* Reduced motion: instant fade — GLightbox interne animacije već uklanja
   * JS init (openEffect: 'none'), ali defensive CSS osigurava da i CSS
   * tranzicije ne odigraju ako vendor CSS klasa stigne pre JS init-a.
   */
  @media (prefers-reduced-motion: reduce) {
    .glightbox-clean .ginner-container,
    .glightbox-clean .gslide {
      transition: none !important;
      animation: none !important;
    }
  }
  ```
- **And** fajl MORA koristiti **TAČNE** boje iz DESIGN.md § Elevation & Depth (no magic — backdrop `rgba(15,15,15,0.85)` je locked u DESIGN.md; ako bi se promenio token treba i ovaj fajl).
- **And** fajl MORA imati `@media (prefers-reduced-motion: reduce) { ... }` block sa `transition: none !important; animation: none !important;` (defensive — JS već postavlja `openEffect: 'none'`, ali CSS guard za slučaj race condition kad CSS stigne pre JS init).
- **And** fajl NE SME uvoditi nove `--color-*` tokene u `:root` — `tokens.css` je single source za tokene per project-context.md § CSS Custom Properties; ako bi se kasnije uvele backdrop boje kao token, refactor ide kroz zasebnu story-ju (YAGNI).
- **And** **NEMA** Bootstrap `!important` osim u `@media (prefers-reduced-motion: reduce)` blok-u (gde je `!important` opravdan da pobedi vendor inline transition-e).

**AC4 — `static/css/main.css` dobija `@import url('./components/lightbox.css');` red u CSS @import sekciji (mirror Story 1.7 + 1.8 IMP-7 pattern)**

- **Given** AC3 završen (`lightbox.css` postoji); Story 1.7 + 1.8 je proširio `main.css` sa 8 `@import` linija (live verifikovano — read `static/css/main.css` pre Edit-a: sve postojeće `@import` linije koriste **`@import url('./components/...');`** sintaksu sa `url(...)` wrap-erom — ovo je projekat konvencija, NIKAD bare-string `@import './components/...';`)
- **When** dodajem novi `@import` u `main.css`
- **Then** `main.css` MORA imati novi red **TAČNO**: `@import url('./components/lightbox.css');` (sa `url(...)` wrap-erom + leading `./` per Story 1.7 IMP-7 dot-prefix rule + trailing semicolon + single line — TAČNO mirror postojećih 8 `@import` linija).
- **And** red MORA biti **dodat na kraju** postojećih `@import` linija (ne presretati postojeći redosled — `lightbox.css` je nezavisan od `header/footer/sticky-nav` cascade-a; alfabetski bi išao posle `header.css` ali zadržavamo Story 1.7+1.8 stacking order: components → page-specific; Lightbox je components grupa pa ide na kraju components grupe).
- **And** Edit MORA biti **targeted Edit operacija** koja zadržava sve postojeće linije (sve `@import` direktive iz Story 1.7 + 1.8 + sve docstring komentare); Dev verifikuje pre + posle Edit-a brojem linija (smoke check: `wc -l static/css/main.css` raste TAČNO za 1, NE više; novi red sadrži tekst `@import url('./components/lightbox.css');`).

**AC5 — `templates/base.html` dobija GLightbox CSS link u `<head>` (POSLE tokens.css, PRE Bootstrap CSS) + `lightbox-init.js` script tag (POSLE sticky-nav.js, sa `defer`)**

- **Given** AC1 + AC2 + AC3 + AC4 završeni; `templates/base.html` postojeći struktura iz Story 1.6 + 1.8 (verifikovano live linija 1-41 — vidi Dev Notes § Postojeći base.html struktura za snimak)
- **When** modifikujem `templates/base.html` (targeted Edit, NE rewrite)
- **Then** **dva nova reda se dodaju**:
  - **HEAD section:** novi `<link>` tag se dodaje **IZMEĐU** `tokens.css` linka (linija 12) i `{% bootstrap_css %}` poziva (linija 13). Tačan red: `<link rel="stylesheet" href="{% static 'vendor/glightbox/glightbox.min.css' %}">`. Razlog za pozicioniranje: GLightbox vendor CSS se učitava PRE Bootstrap-a tako da naš `static/css/components/lightbox.css` override (učitan kroz `main.css` POSLE Bootstrap-a) pobeđuje kroz standardni cascade. Bootstrap utility klase za ne-lightbox markup ostaju netaknute jer ne ciljaju `.glightbox-clean` / `.gslide` / `.goverlay` selektore. Konačan redosled u `<head>`: tokens.css → glightbox.min.css → bootstrap → main.css.
  - **BODY scripts section (kraj `<body>`):** novi `<script>` tag se dodaje **POSLE** `sticky-nav.js` linije (linija 37) i **PRE** postojećeg Django komentara `{# Per-page scripts POSLE site-wide ... #}` (linija 38) + `{% block scripts %}` (linija 39). Tačan red: `<script src="{% static 'vendor/glightbox/glightbox.min.js' %}" defer></script>` (linija 1) + `<script src="{% static 'js/lightbox-init.js' %}" defer></script>` (linija 2). **Razlog redosleda:** vendor GLightbox JS MORA biti učitan pre `lightbox-init.js` (jer init referenciše `window.GLightbox` constructor); oba sa `defer` (per project-context.md § Performance must-haves + Story 1.8 sticky-nav.js pattern); `defer` garantuje sekvencijalno izvršavanje u redu u kom su deklarisani u DOM-u (per HTML spec — `defer` scripts execute in source order POSLE HTML parsa). Konačan red script-ova: htmx (defer, linija 35) → Bootstrap JS sync (linija 36) → sticky-nav.js (defer, linija 37) → **glightbox.min.js (defer, NOVO)** → **lightbox-init.js (defer, NOVO)** → Django komentar (shifted na liniju 40) → `{% block scripts %}` (shifted na liniju 41).
- **And** Edit MORA biti **targeted** — postojeće linije 1-12, 13-37, 39-41 ostaju netaknute (regression guard za Story 1.6 + 1.8 testove `tests/test_base_template.py` + `tests/test_navigation_chrome.py`).
- **And** Edit MORA očuvati postojeći Django komentar `{# Per-page scripts POSLE site-wide — sync init safe za Bootstrap komponente #}` na liniji 38 (ili gde god se trenutno nalazi posle Edit-a) — to je Story 1.6 deliverable + regression guard.
- **And** Edit MORA **NE** koristiti `googleapis.com`, `gstatic.com`, `cdn.jsdelivr.net`, `unpkg.com`, `cdnjs.cloudflare.com` u href/src bilo gde (mirror Story 1.6 AC8 anti-pattern guard u `tests/test_base_template.py`; Story 2.5 dodaje paralelan guard za `cdn.jsdelivr.net.*glightbox` u svoj test fajl AC7).
- **And** smoke verifikacija: `docker compose -f compose/local.yml run --rm django uv run python manage.py check --deploy` — exit code 0; staticfiles `collectstatic --dry-run --noinput` ne raise-uje warning za missing `vendor/glightbox/glightbox.min.js`.

**AC6 — Klik na `<a class="glightbox" href="...">` link otvara GLightbox modal sa `role="dialog"` + `aria-modal="true"` + focus trap (verifikovano kroz vendor library + smoke test)**

- **Given** AC1-AC5 završeni; demo link se **NE dodaje u nijedan committed template** — Dev koristi **DevTools Console injection** pristup (zero source modification, zero deletion risk):
  ```javascript
  // U DevTools Console (F12 → Console tab) na lokalnoj strani:
  document.body.insertAdjacentHTML('beforeend', '<a class="glightbox" href="/static/img/coric-agrar-logo-transp-200.png">demo</a>');
  window._coricLightbox && window._coricLightbox.reload();
  ```
- **When** Mihas otvara `http://localhost:8000/` u local browser-u (`just dev` — bilo koja postojeća strana, npr. home), otvara DevTools Console (F12), izvršava gornji snippet, klikne na ubrizgan demo link
- **Then** GLightbox modal MORA otvoriti se:
  - DOM dobija dinamički kreiran `<div class="glightbox-container">` (proverava se kroz browser DevTools Inspector)
  - Modal sadrži atribut `role="dialog"` (vendor GLightbox 3.x default — verifikovati u Inspector)
  - Modal sadrži atribut `aria-modal="true"` (vendor default — GLightbox 3.x sets this per ARIA spec)
  - Backdrop ima `background-color: rgba(15, 15, 15, 0.85)` (Computed Styles u DevTools — verifikuje AC3 override radi)
  - Focus se prebacuje na modal close button (vendor default — focus trap aktiviran)
- **And** Tab navigacija unutar modal-a **NE bega** van modal-a (Tab cikla između close button → image → next/prev buttons → close) — vendor GLightbox 3.x ima built-in focus trap koji ne moramo da reimplementiramo; Story 9.9 a11y audit verifikuje kroz Playwright `keyboard.press('Tab')` + `expect(focused).toBeInDialog()`.
- **And** Esc taster zatvara modal:
  - Modal se uklanja iz DOM-a
  - Focus se vraća na **original trigger element** (demo link sa `class="glightbox"`) — vendor default, verifikovano kroz `document.activeElement === triggerElement` posle close
- **And** klik na backdrop (van slike) zatvara modal (vendor default).
- **And** custom event `coric:lightbox-open` se dispatch-uje na `window` sa `detail.instance` payload-om pri otvaranju (AC2); `coric:lightbox-close` pri zatvaranju.
- **And** ako je `prefers-reduced-motion: reduce` aktivan (Mihas postavlja u OS settings ili Chrome DevTools Rendering panel), nema fade tranzicije — modal se prikazuje/sakriva instantno.
- **Napomena:** ovaj AC je **manuelni smoke check** koji Dev izvršava u browser-u jednom pre commit-a (NIJE part of automated test suite — vendor library behavior NIJE area koji se mock-uje ili unit testira u v1). Demo link se **ne komituje nigde** (DevTools Console injection pristup — zero source modification, zero deletion risk); nema potrebe za "delete before commit" korakom. **Automatska E2E verifikacija** keyboard nav + focus restoration je u **Story 9.8 (Playwright UJ-1 journey)** scope.

- **Napomena za Dev:** AC6 ne može se izvršiti ako AC1 nije zadovoljen (vendor fajlovi nedostaju). U tom slučaju, dokumentuj u Dev Agent Record § Completion Notes: `AC6 SKIPPED — vendor files missing per AC1 HALT. Re-execute manuelni smoke check pre nego što Story 2.7 počne.`

**AC7 — `tests/test_lightbox_integration.py` postoji sa file-existence + base.html cascade + main.css @import + no-CDN guard testovima (mirror `tests/test_navigation_chrome.py` + `tests/test_static_tokens.py` pattern)**

- **Given** AC1-AC5 završeni; postojeći pattern iz `tests/test_base_template.py` (file-existence + base.html source check) + `tests/test_static_tokens.py` (CSS file structural check)
- **When** TEA (Step 3) piše `tests/test_lightbox_integration.py`
- **Then** fajl mora sadržati MINIMUM sledeće test funkcije (svaki nezavisan, koristi `Path` reads — NE Django test client, jer ovo je pure static asset verifikacija):

  ```python
  """Tests za Story 2.5 — GLightbox Integracija (static asset + base.html wiring).

  Pokriva:
  - AC1: static/vendor/glightbox/{glightbox.min.css, glightbox.min.js} postoje + minified
  - AC2: static/js/lightbox-init.js postoji + IIFE + use strict + coric: namespace +
         prefers-reduced-motion respect + idempotent re-init guard
  - AC3: static/css/components/lightbox.css postoji + backdrop rgba(15,15,15,0.85) +
         @media (prefers-reduced-motion: reduce)
  - AC4: static/css/main.css sadrži @import url('./components/lightbox.css');
  - AC5: templates/base.html sadrži glightbox.min.css link u HEAD (POSLE tokens, PRE bootstrap) +
         glightbox.min.js + lightbox-init.js script tags POSLE sticky-nav.js (sa defer)
  - Anti-pattern guards: no CDN URL (cdn.jsdelivr.net, unpkg.com, cdnjs.cloudflare.com)
    u code-base; no inline onclick=/onkeydown= u lightbox-init.js; no jQuery import

  Pokrenuti sa: uv run pytest tests/test_lightbox_integration.py -v --tb=short

  TEA RED faza: svi testovi MORAJU pasti dok Dev ne završi Story 2.5
  (osim SKIP za vendor fajlove koje Mihas tek download-uje — vidi AC1 Napomena).
  Naming: srpska latinica + engleski; bez ćirilice.
  """
  ```

- **And** fajl MORA imati MINIMUM sledeće test funkcije (TEA RED-phase deliverable u Step 3):
  1. `test_ac1_glightbox_vendor_directory_exists` — `static/vendor/glightbox/` postoji
  2. `test_ac1_glightbox_css_file_exists_and_minified` — `glightbox.min.css` postoji + ima `.glightbox-clean` ili `.gslide` selektor + use byte-size heuristic: `assert (project_root / 'static/vendor/glightbox/glightbox.min.css').stat().st_size <= 50_000` (minified ~6 KB, pretty-printed ~80 KB — 50 KB threshold catches un-minified)
  3. `test_ac1_glightbox_js_file_exists_and_exposes_global` — `glightbox.min.js` postoji + sadrži `window.GLightbox` ili `GLightbox=` u source
  4. `test_ac2_lightbox_init_js_exists` — `static/js/lightbox-init.js` postoji
  5. `test_ac2_lightbox_init_is_iife_with_use_strict` — fajl počinje sa `(function ()` (možda whitespace) + sadrži `'use strict';`
  6. `test_ac2_lightbox_init_uses_coric_namespace_events` — sadrži `'coric:lightbox-open'` + `'coric:lightbox-close'`
  7. `test_ac2_lightbox_init_respects_prefers_reduced_motion` — sadrži `prefers-reduced-motion`
  8. `test_ac2_lightbox_init_has_htmx_after_swap_listener` — sadrži `'htmx:afterSwap'`
  9. `test_ac2_lightbox_init_has_idempotent_destroy_guard` — sadrži `_coricLightbox` + `destroy`
  10. `test_ac2_lightbox_init_no_jquery_no_module_imports` — fajl NE sadrži `jQuery`, `$(`, `import `, `export `
  11. `test_ac3_backdrop_color_rgba_specified` — `lightbox.css` postoji + sadrži `.glightbox-clean .goverlay` selektor (NE `.gcontainer` koji je modal content wrapper, NE `.glightbox-modern` koji nije default skin) + sadrži `rgba(15, 15, 15, 0.85)` ILI `rgba(15,15,15,0.85)` (regex sa optional whitespace)
  12. `test_ac3_lightbox_css_has_reduced_motion_block` — sadrži `@media (prefers-reduced-motion: reduce)` + `transition: none` + `animation: none`
  13. `test_ac4_main_css_imports_lightbox_component` — `main.css` sadrži `@import url('./components/lightbox.css');` linija (TAČNO mirror postojećih `@import url('./components/...');` linija — sa `url(...)` wrap-erom, NE bare-string `@import './components/...';`)
  14. `test_ac5_base_html_links_glightbox_css_in_head` — `base.html` sadrži `vendor/glightbox/glightbox.min.css` u HEAD sekciji između `tokens.css` i `bootstrap_css` poziva. Use quote-agnostic substring search: `assert 'css/tokens.css' in source` AND `assert source.index('vendor/glightbox/glightbox.min.css') > source.index('css/tokens.css')` AND `assert source.index('vendor/glightbox/glightbox.min.css') < source.index('bootstrap_css')`.
  15. `test_ac5_base_html_has_glightbox_min_js_script_with_defer` — `base.html` sadrži `<script src="{% static 'vendor/glightbox/glightbox.min.js' %}" defer></script>` (eksplicitan match — može i sa različitim quote stilom)
  16. `test_ac5_base_html_has_lightbox_init_js_script_with_defer` — `base.html` sadrži `<script src="{% static 'js/lightbox-init.js' %}" defer></script>`
  17. `test_ac5_lightbox_scripts_after_sticky_nav` — u source-u `base.html`, indeks string-a `lightbox-init.js` MORA biti VEĆI od indeksa `sticky-nav.js` (redosled enforcement — vendor mora pre init, oba posle sticky-nav)
  18. `test_anti_pattern_no_cdn_url_for_glightbox` — grep kroz `templates/`, `static/css/`, `static/js/` za `cdn.jsdelivr.net`, `unpkg.com`, `cdnjs.cloudflare.com` u kombinaciji sa `glightbox` (case-insensitive); MORA biti **0 matches** (Pattern: u `tests/test_base_template.py` AC8 postoji paralelan guard za HTMX/Bootstrap CDN reference — Story 2.5 dodaje Lightbox-specifičan guard)
  19. `test_ac5_glightbox_vendor_before_init_script` — `assert source.index('vendor/glightbox/glightbox.min.js') < source.index('js/lightbox-init.js')` — vendor library MORA biti učitan pre init module-a (defensive guard `typeof window.GLightbox !== 'function'` se oslanja na ovo)
- **And** test MORA koristiti **`Path` reads** (mirror `tests/test_navigation_chrome.py` + `tests/test_static_tokens.py` pattern) — **NE** Django test client + Django setup; ovi testovi verifikuju fajl-postojanje i sadržaj, ne render. (Smoke-render verifikaciju iz `tests/test_navigation_chrome.py` Story 1.8 stila NIJE potrebna jer Story 2.5 nije dodala URL/view; render testovi dolaze sa Story 2.7 Product Detail strana.)
- **And** test MORA imati SKIP marker za AC1 vendor testove ako fajlovi NISU prisutni (Mihas ih tek download-uje — mirror Story 1.6 `HTMX_VENDOR_MISSING_MSG` pattern u `tests/test_base_template.py`):
  ```python
  GLIGHTBOX_VENDOR_MISSING_MSG = (
      "static/vendor/glightbox/{glightbox.min.css,glightbox.min.js} ne postoji — "
      "Mihas ručno download-uje sa https://github.com/biati-digital/glightbox/releases "
      "(latest 3.x tag, dist/ fajlovi). Vidi Story 2.5 AC1 Napomena za Dev."
  )

  @pytest.mark.skipif(
      not (PROJECT_ROOT / "static/vendor/glightbox/glightbox.min.js").exists(),
      reason=GLIGHTBOX_VENDOR_MISSING_MSG,
  )
  def test_ac1_glightbox_js_file_exists_and_exposes_global():
      ...
  ```
- **And** test MORA koristiti `srpska latinica` u svim docstring-ovima i poruka-ma — **NIKAD ćirilica** (per project-context.md § Anti-pattern: Ćirilica u kodu linija 487-495).
- **Napomena:** keyboard navigation + focus restoration testovi (AC6 manuelni smoke check) su explicitly **out-of-scope za Story 2.5 testove**. Story 9.8 (Playwright E2E za UJ-1, UJ-2, UJ-3) dodaje E2E test koji verifikuje keyboard nav real-browser scenarijem. Story 9.9 (a11y audit) verifikuje WCAG kroz axe-core static analysis.

## Tasks / Subtasks

- [ ] **Task 1: GLightbox vendor assets — Mihas ručno download (AC1)**
  - [ ] Subtask 1.1: Mihas posećuje `https://github.com/biati-digital/glightbox/releases` u browser-u
  - [ ] Subtask 1.2: Mihas selektuje najnoviji 3.x release tag (NE master/main grana — pin na konkretan tag radi reproducibility)
  - [ ] Subtask 1.3: Mihas preuzima `dist/glightbox.min.css` + `dist/glightbox.min.js` iz release artifakata (ILI iz GitHub source tree `dist/` direktorijuma)
  - [ ] Subtask 1.4: Mihas verifikuje integritet downloadovanih fajlova — na npmjs.com/package/glightbox naći SHA-512 integrity hash za pin-ovanu verziju (3.3.0+), uporediti sa SHA-512 lokalnih fajlova: `Get-FileHash -Algorithm SHA512 static\vendor\glightbox\glightbox.min.js` (PowerShell) ili `sha512sum static/vendor/glightbox/glightbox.min.js` (Bash). Dokumentovati u Dev Agent Record § Completion Notes
  - [ ] Subtask 1.5: Mihas kreira `static/vendor/glightbox/` direktorijum i smešta oba fajla (TAČNO 2 fajla — ne kopirati ceo dist/ folder)
  - [ ] Subtask 1.6: Mihas dokumentuje exact version (npr. "3.3.0") u Story 2.5 Dev Agent Record `Completion Notes` sekciji
  - [ ] Subtask 1.7: Dev verifikuje minified heuristika (file size <= 50 KB za oba fajla — minified ~6 KB CSS / ~30 KB JS, pretty-printed ~80 KB) + sanity selector check (`.glightbox-clean` ili `.gslide` u CSS, `GLightbox` global u JS)

- [x] **Task 2: `static/js/lightbox-init.js` — vanilla JS init modul (AC2)**
  - [x] Subtask 2.1: Dev kreira `static/js/lightbox-init.js` sa TAČNIM source-om iz AC2 dev notes
  - [x] Subtask 2.2: Dev verifikuje IIFE pattern + `'use strict';` + defensive `window.GLightbox` guard
  - [x] Subtask 2.3: Dev verifikuje `prefers-reduced-motion` matchMedia check + `coric:lightbox-open/close` custom events
  - [x] Subtask 2.4: Dev verifikuje idempotent re-init (window._coricLightbox.destroy() pre re-init) + `htmx:afterSwap` listener
  - [x] Subtask 2.5: Dev grep-uje fajl: 0 matches za `jQuery`, `$(`, `import `, `export `, inline `onclick=`/`onkeydown=`

- [x] **Task 3: `static/css/components/lightbox.css` — custom theme override (AC3)**
  - [x] Subtask 3.1: Dev kreira `static/css/components/lightbox.css` sa TAČNIM source-om iz AC3 dev notes
  - [x] Subtask 3.2: Dev verifikuje backdrop boju `rgba(15, 15, 15, 0.85)` (eksplicitno DESIGN.md § Modal/Lightbox linija 287)
  - [x] Subtask 3.3: Dev verifikuje `@media (prefers-reduced-motion: reduce)` block sa `transition: none !important; animation: none !important;`

- [x] **Task 4: `static/css/main.css` — dodaj `@import url('./components/lightbox.css');` (AC4)**
  - [x] Subtask 4.1: Dev čita postojeći `main.css` (read PRE Edit-a — regression guard)
  - [x] Subtask 4.2: Dev koristi Edit alat da doda `@import url('./components/lightbox.css');` na kraju postojećih `@import` linija (NE menja postojeće; TAČNO mirror postojećih 8 `@import url('./components/...');` linija)
  - [x] Subtask 4.3: Dev verifikuje da je broj linija porastao TAČNO za 1

- [x] **Task 5: `templates/base.html` — dodaj GLightbox CSS link + 2 script tag-a (AC5)**
  - [x] Subtask 5.1: Dev čita postojeći `base.html` (read PRE Edit-a — regression guard za Story 1.6 + 1.8)
  - [x] Subtask 5.2: Dev koristi Edit alat 1: dodaje `<link rel="stylesheet" href="{% static 'vendor/glightbox/glightbox.min.css' %}">` IZMEĐU `tokens.css` (linija 12) i `{% bootstrap_css %}` (linija 13)
  - [x] Subtask 5.3: Dev koristi Edit alat 2: dodaje 2 nova `<script>` tag-a POSLE `sticky-nav.js` script-a (linija 37), PRE postojećeg Django komentara `{# Per-page scripts POSLE site-wide ... #}` (linija 38) i `{% block scripts %}` (linija 39):
    - `<script src="{% static 'vendor/glightbox/glightbox.min.js' %}" defer></script>`
    - `<script src="{% static 'js/lightbox-init.js' %}" defer></script>`
  - [x] Subtask 5.4: Dev verifikuje broj linija porastao za TAČNO 3 (1 link + 2 scripts) i da je Django komentar na liniji 41 (shift sa 38 + 3 nove linije) (`{# Per-page scripts POSLE site-wide — sync init safe za Bootstrap komponente #}`) i dalje prisutan (regression guard za Story 1.6)
  - [x] Subtask 5.5: Dev verifikuje da NEMA `cdn.jsdelivr.net`, `unpkg.com`, `cdnjs.cloudflare.com` URL-ova u celom `base.html` source-u

- [ ] **Task 6: Manuelni browser smoke check (AC6) — Dev DELIVERABLE pre commit-a**
  - [ ] Subtask 6.1: Dev pokreće `just dev` (Docker Compose local) — Django + PostgreSQL up
  - [ ] Subtask 6.2: Dev otvara `http://localhost:8000/` u Chrome (Mihas-ov primary browser per project context — bilo koja postojeća strana, npr. home). Otvara DevTools Console (F12 → Console)
  - [ ] Subtask 6.3: Dev ubrizgava demo link kroz Console (zero source modification, zero deletion risk):
    ```javascript
    document.body.insertAdjacentHTML('beforeend', '<a class="glightbox" href="/static/img/coric-agrar-logo-transp-200.png">demo</a>');
    window._coricLightbox && window._coricLightbox.reload();
    ```
  - [ ] Subtask 6.4: Dev klikne na ubrizgan "demo" link; verifikuje:
    - Modal se otvara sa backdrop `rgba(15, 15, 15, 0.85)` (DevTools Computed Styles)
    - DOM ima `role="dialog"` + `aria-modal="true"` (DevTools Inspector)
    - Focus se prebacuje na close button
    - Tab navigacija cikla unutar modal-a (Tab → close → image → close)
    - Esc zatvara modal + vraća focus na demo link
    - Klik na backdrop zatvara modal
  - [ ] Subtask 6.5: Dev aktivira `prefers-reduced-motion: reduce` u Chrome DevTools Rendering panel; verifikuje da nema fade tranzicije
  - [ ] Subtask 6.6: Dev otvara DevTools Console; verifikuje custom event-e:
    ```javascript
    window.addEventListener('coric:lightbox-open', (e) => console.log('OPEN', e.detail));
    window.addEventListener('coric:lightbox-close', (e) => console.log('CLOSE', e.detail));
    ```
    Klikne demo link → vidi "OPEN" sa `detail.instance` u konzoli; pritisne Esc → vidi "CLOSE" sa `detail.instance`.

- [ ] **Task 7: TEA-deliverable — testovi (RED phase, Step 3, NIJE Dev scope)** _(NAPOMENA: ovaj task je listed for clarity — TEA agent u Step 3 piše testove pre Dev-ovog Step 3 GREEN phase implementacije; Dev NIKAD ne piše testove per project-context.md § Test discipline linija 294)_
  - [ ] Subtask 7.1: TEA kreira `tests/test_lightbox_integration.py` sa 19 test funkcija per AC7
  - [ ] Subtask 7.2: TEA verifikuje testovi padaju u RED phase (jer Dev još nije implementirao Task 1-5)
  - [ ] Subtask 7.3: TEA commit-uje test fajl PRE Dev GREEN phase commit-a (separate commit, conventional commit message `test(static): Story 2.5 RED-phase tests — GLightbox integration`)

## Dev Notes

### Postojeći `base.html` struktura (snimak pre Edit-a — regression guard)

Story 2.5 Edit MORA očuvati ovaj redosled. Pre Edit-a u Task 5, Dev MORA pročitati ovaj fajl da bi verifikovao trenutni sadržaj. Sledeći je live snapshot iz repository-ja (Story 1.8 deliverable):

```html
<!DOCTYPE html>
{% load i18n %}
{% load static %}
{% load django_bootstrap5 %}
{% load htmx_aria %}
<html lang="{{ LANGUAGE_CODE }}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="{% block meta_description %}{% endblock %}">
  <title>{% block title %}Ćorić Agrar{% endblock %}</title>
  <link rel="stylesheet" href="{% static "css/tokens.css" %}">             {# linija 12 — Story 1.5 #}
  {% bootstrap_css %}                                                        {# linija 13 — Story 1.6 #}
  <link rel="stylesheet" href="{% static 'css/main.css' %}">                 {# linija 14 — Story 1.6 #}
  {% block extra_head %}{% endblock %}
</head>
<body>
  <a class="visually-hidden-focusable" href="#main-content">{% translate "Preskoči na sadržaj" %}</a>
  <div class="coric-sticky-sentinel" aria-hidden="true"></div>
  {% include "partials/header.html" %}
  <main id="main-content" tabindex="-1">
    {% block content %}
      <h1>Ćorić Agrar</h1>
      <p>{% translate "Dobrodošli." %}</p>
    {% endblock %}
  </main>
  {% include "partials/footer.html" %}
  {% aria_live %}
  <noscript>...</noscript>
  {# Site-wide scripts PRVI: Bootstrap sync (django-bootstrap5 NE emit-uje defer) + HTMX defer; child block scripts uvek vide Bootstrap učitan (sync Bootstrap precedes block u DOM order-u); vidi Gotcha #15 #}                {# linija 34 — Story 1.6 #}
  <script src="{% static 'vendor/htmx.min.js' %}" defer></script>             {# linija 35 — Story 1.6 #}
  {% bootstrap_javascript %}                                                  {# linija 36 — Story 1.6 #}
  <script src="{% static 'js/sticky-nav.js' %}" defer></script>               {# linija 37 — Story 1.8 #}
  {# Per-page scripts POSLE site-wide — sync init safe za Bootstrap komponente #}  {# linija 38 — Story 1.6 deliverable + regression guard #}
  {% block scripts %}{% endblock %}                                           {# linija 39 #}
</body>
</html>
```

**Story 2.5 Edit DELTA:**
- Dodaje **`<link rel="stylesheet" href="{% static 'vendor/glightbox/glightbox.min.css' %}">`** IZMEĐU linije 12 (tokens.css) i linije 13 (bootstrap_css) — postaje nova linija 13, ostale linije se shifted +1
- Dodaje **`<script src="{% static 'vendor/glightbox/glightbox.min.js' %}" defer></script>`** + **`<script src="{% static 'js/lightbox-init.js' %}" defer></script>`** POSLE sticky-nav.js linije (37) i PRE Django komentara `{# Per-page scripts POSLE site-wide ... #}` (linija 38) — postaju nove linije 38-39, komentar shifts na liniju 40, `{% block scripts %}` shifts na liniju 41. **Postojeći Django komentar na liniji 38 (`{# Per-page scripts POSLE site-wide — sync init safe za Bootstrap komponente #}`) MORA ostati netaknut** — to je Story 1.6 deliverable + regression guard.

### `static/css/main.css` Edit DELTA

Story 1.7 + 1.8 je registrovala 8 `@import` linija (live verifikovano kroz `Read static/css/main.css`). Trenutno `main.css` ima `@import url('./components/...');` linije za sve komponente — **TAČNO ta sintaksa sa `url(...)` wrap-erom je projekat konvencija** (NE bare-string `@import './components/...';`). Story 2.5 dodaje JEDNU novu liniju **na kraj** components grupe, koristeći **identičnu sintaksu** kao postojeće linije:

```css
/* postojece linije ostaju netaknute */
@import url('./components/header.css');
@import url('./components/footer.css');
@import url('./components/sticky-nav.css');
@import url('./components/lightbox.css');  /* NOVO — Story 2.5 */
```

Dev MORA čitati ceo fajl pre Edit-a (regression guard) — Story 1.7 IMP-7 dokumentuje da svi `@import` koriste **leading `./`** sintaksu (NE goli `components/...` što neki CSS preprocessor-i razlikuju); Story 1.8 + 2.5 sledeća konvencija je `@import url('./components/<name>.css');` (sa eksplicitnim `url()` wrap-erom — match-uje sve 8 postojećih linija).

### GLightbox 3.x DOM markup — backdrop vs container

GLightbox 3.x renderuje sledeću DOM strukturu kada se modal otvori:

- `.glightbox-container` — root wrapper (najgornji div koji se ubacuje na kraj `<body>`)
- `.glightbox-clean` — default skin klasa (jedini skin koji se garantovano ships sa GLightbox 3.x; `.glightbox-modern` NIJE default i NIJE garantovano dostupan)
- `.goverlay` — **backdrop element** (poluprovidni background koji prekriva ostatak strane). **Naš override targetira OVAJ element**.
- `.gcontainer` — modal **content wrapper** (sadrži sliku/video + close button + caption). NIKAD ne targetiraj ovo za backdrop — to bi promenilo boju iza slike, ne iza modal-a.
- `.ginner-container` — inner content holder unutar `.gcontainer`
- `.gslide` — pojedinačni slide (slika/video)

**Backdrop = `.goverlay`** (per GLightbox 3.x markup) — NIKAD `.gcontainer` (to je modal content wrapper). Reduced-motion override targetira `.ginner-container` + `.gslide` jer su to elementi koji imaju vendor CSS tranzicije (fade-in, slide transform).

### HTMX swap guard + matchMedia change listener + multi-locale moreText (rationale)

- **HTMX swap guard (`instance.opened`):** `document.body.addEventListener('htmx:afterSwap', ...)` listener proverava `window._coricLightbox.opened` pre nego što pozove `initLightbox()`. Guard `instance.opened` sprečava destroy-mid-interaction (npr. Story 2.8 HTMX filter OOB swap dok je modal otvoren) — fokus i screen reader announcement ostaju intaktni. Listener je na `document.body` (NE `document`) jer HTMX 1.9+ default-uje dispatch na `body`.
- **matchMedia change listener (`prefers-reduced-motion`):** mirror Story 1.8 `sticky-nav.js` pattern (linija 49) — kad korisnik promeni OS preference za reduced motion tokom seanse, `motionQuery.addEventListener('change', initLightbox)` re-inicijalizuje GLightbox sa novim `openEffect`/`closeEffect`/`slideEffect` vrednostima. `prefersReducedMotion` se računa **unutar** `buildOptions()` (NE u outer scope) da bi svaki re-init pokupio trenutnu vrednost.
- **Multi-locale `moreText`:** čita `<html lang>` atribut (postavljen Story 1.4 i18n LocaleMiddleware) i mapira na sr/hu/en — fallback na 'sr' ako jezik nije podržan. Story 2.7 može override-ovati per-link kroz `data-` attribute (GLightbox 3.x podržava `data-more-text` per slide).

### Kanonski JS init pattern (referenca iz Story 1.8 `sticky-nav.js`)

Story 2.5 prati identičan vanilla JS pattern uspostavljen u Story 1.8 (live `static/js/sticky-nav.js` linija 9-50):

| Element | Story 1.8 sticky-nav.js | Story 2.5 lightbox-init.js |
|---|---|---|
| Wrapper | IIFE `(function () { ... })();` | IIFE — identičan pattern |
| Strict mode | `'use strict';` na liniji 10 | `'use strict';` na liniji 10 — identičan |
| Defensive guards | `if (typeof window === 'undefined' || ...)` | `if (typeof window === 'undefined' || ...)` + `if (typeof window.GLightbox !== 'function')` |
| DOM ready handling | Implicit kroz `defer` script ordering | Explicit `document.readyState === 'loading'` check + DOMContentLoaded listener (defensive, `defer` već garantuje DOM ready) |
| Resource cleanup | `observer.disconnect()` u syncObserver | `window._coricLightbox.destroy()` u initLightbox (idempotency) |
| Mobile/feature detection | `matchMedia('(max-width: 767px)')` | `matchMedia('(prefers-reduced-motion: reduce)')` |
| Custom events | (none — sticky nav je dimensionless) | `coric:lightbox-open` + `coric:lightbox-close` na window sa `detail.instance` payload |
| HTMX integration | (none — sticky nav je page-load only) | `document.body.addEventListener('htmx:afterSwap', ...)` + guard `instance.opened` (skip re-init mid-modal) |
| No globals | No `window.X = ...` osim observer (none) | Single `window._coricLightbox = instance` handle za idempotency |

### Kanonski GLightbox markup koji Story 2.7 produkuje (informativno)

Story 2.5 NE renderuje nijedan `.glightbox` link u templates. Story 2.7 (Product Detail strana) će biti prvi koji koristi sledeći markup pattern; dokumentovan ovde da Dev razume CONSUMER ugovor:

```html
{# Story 2.7 product galerija (informativno — NIJE deliverable u Story 2.5) #}
<div class="coric-product-gallery">
  {% for image in product.images.all %}
    <a class="glightbox"
       href="{{ image.image.url }}"
       data-gallery="product-{{ product.slug }}"
       data-description="{{ image.alt_text }}">
      {% responsive_picture image.image alt=image.alt_text sizes="(max-width: 768px) 100vw, 50vw" %}
    </a>
  {% endfor %}
</div>
```

`data-gallery` group-uje slike u jednu prev/next sekvencu. `data-description` se prikazuje kao caption u Lightbox-u. Story 2.5 init handler (`selector: '.glightbox'`) pokriva sve takve linkove automatski.

### Vendor library pinning rationale

Architecture.md AR-35 + § JavaScript decisions linija 202 specifikuje **GLightbox 3.x** sa rationale-om: "Lightweight, full a11y, video support kao bonus" + "10 KB gzipped". Story 2.5 NIJE radila web research za noviju verziju (per SM workflow instrukcije: koristiti architecture.md SOT). Story 9.x može razmotriti upgrade ako security advisory ili WCAG 2.2 compliance traži. Trenutni pin: latest 3.x tag (npr. 3.3.0 koji je najnoviji u 3.x liniji per github releases page) — Mihas dokumentuje exact version u Dev Agent Record posle download-a.

### Anti-paterni koje treba izbeći

| Anti-pattern | Razlog izbegavanja | Source |
|---|---|---|
| CDN load za GLightbox (cdn.jsdelivr.net, unpkg.com, cdnjs.cloudflare.com) | GDPR (no third-party fetch), CSP friendly (no extra script-src host), offline reproducibility | project-context.md § Frontend deps — "no build pipeline — vendor files se serviraju lokalno" |
| jQuery dependency | Zabranjeno u project-context.md § JavaScript style — "Vanilla JS preferred ... NIKAD jQuery" | project-context.md linija 338 |
| Inline `onclick=`/`onkeydown=` handler | Zabranjeno u project-context.md § JavaScript style + CSP friendliness; `addEventListener` preferred | project-context.md + Story 1.8 CRITICAL-1 (uklanjanje inline `onchange=`) |
| Globalne JS varijable (`window.lightbox = ...`) | Pollute-uje global scope; jedini dozvoljen handle je `window._coricLightbox` (underscore prefix signal-izira "internal") | Story 1.8 IIFE pattern + project-context.md § JavaScript |
| Hard-coded magic colors u lightbox.css (`#0f0f0f`) | Backdrop boja MORA biti iz DESIGN.md § Elevation & Depth — `rgba(15,15,15,0.85)` (currently no token; tokens.css refactor je YAGNI dok ne treba) | project-context.md § Anti-pattern: Inline CSS / magic values |
| Init pre Bootstrap JS (loading) | Modali bi mogli da konfliktuju sa Bootstrap modal nivo (z-index 1055 vs lightbox z-index ~9999); GLightbox je samostalan ali safer da je posle Bootstrap | Story 1.8 sticky-nav.js pattern (POSLE Bootstrap) |
| Inicijalizacija bez `defer` | Sync scripts u `<body>` su anti-pattern (block parse); ako i radi `defer` mora biti uniformno | project-context.md § Performance must-haves + Story 1.6 AC1 script ordering decision |
| Reinicijalizacija bez `destroy()` | Memory leak: stari GLightbox instance + duplikat event listeners; izaziva double-open na klik | EXPERIENCE.md § Lightbox + GLightbox docs |
| Server-side Lightbox state (form, db) | Lightbox je 100% client-side; nikakav HTMX POST, nikakav Django view za Lightbox state | project-context.md § HTMX response patterns |
| Renderovanje `<dialog>` HTML5 element-a kao manuelni focus trap | GLightbox već implementira focus trap u-house; reimplementacija krši YAGNI | UX-DR-13 explicit specifikacija + project-context.md § YAGNI |

### Pre commit-a UVEK pitaj sebe (Story 2.5 specifični)

1. Da li je vendor `glightbox.min.{css,js}` lokalno hostovan u `static/vendor/glightbox/` (NE CDN)?
2. Da li `lightbox-init.js` koristi IIFE + `'use strict';` + nije imao jQuery/import/export?
3. Da li `lightbox.css` koristi `rgba(15, 15, 15, 0.85)` iz DESIGN.md § Modal/Lightbox?
4. Da li `main.css` ima novi `@import url('./components/lightbox.css');` red sa leading `./` (Story 1.7 IMP-7) + `url(...)` wrap-erom (Story 1.8 + 2.5 konvencija)?
5. Da li `base.html` ima GLightbox CSS link IZMEĐU `tokens.css` i `bootstrap_css` (cascade redosled)?
6. Da li `base.html` ima oba script tag-a (vendor + init) sa `defer` POSLE sticky-nav.js?
7. Da li je AC6 smoke check izvršen kroz DevTools Console injection (NIKAD demo `<a class="glightbox">` komitovan u `base.html` `{% block content %}` ili bilo gde u repository-ju)?
8. Da li `tests/test_lightbox_integration.py` proveravanje no-CDN guard prolazi?
9. Da li je manuelni browser smoke check (AC6) izvršen + custom event-i verifikovani u konzoli?
10. Da li `just test tests/test_lightbox_integration.py` prolazi (GREEN posle Dev implementacije)?

### Testing standards summary

- **Framework:** pytest (per project-context.md § Test framework — pytest-django je SOT, `unittest.TestCase` zabranjen za nove testove)
- **Test lokacija:** `tests/test_lightbox_integration.py` (cross-cutting test, NIJE per-app; mirror `tests/test_base_template.py`, `tests/test_navigation_chrome.py`, `tests/test_static_tokens.py` lokaciju)
- **Test type:** **file-existence + structural** (Path reads + string contains/regex) — NIJE Django test client, NIJE Django setup; vendor library behavior NE mock-uje se
- **Coverage:** 19 test funkcija per AC7 (file existence, IIFE pattern, custom events, prefers-reduced-motion, HTMX listener, idempotent guard, CSS @import, base.html cascade, no-CDN guard, vendor-before-init script order)
- **NIJE u Story 2.5 scope:** E2E keyboard nav testovi (Playwright) — Story 9.8 (UJ-1 journey); a11y axe-core audit — Story 9.9; integration test sa stvarnim browser-om i fokus restoration — Story 9.8 + 9.9
- **Run command:** `just test tests/test_lightbox_integration.py -v --tb=short` (run-uje kroz Docker `compose/local.yml` da bi Python env imao sve deps)
- **TEA RED phase commit message:** `test(static): Story 2.5 RED-phase tests — GLightbox integration file existence + base.html cascade + no-CDN guard`
- **Dev GREEN phase commit message:** `feat(static): Story 2.5 — GLightbox 3.x lokalno hostovan + lightbox-init.js IIFE + base.html cascade + lightbox.css backdrop theme` (per project-context.md § Commit messages style)

### Project Structure Notes

Story 2.5 prati arhitekturu specifikovanu u architecture.md § Project structure (linija 663-678):

```text
static/
├── css/
│   ├── tokens.css              # Story 1.5
│   ├── main.css                # Story 1.6 + 1.7 + 1.8 + 2.5 EDIT (novi @import)
│   └── components/
│       ├── header.css          # Story 1.8
│       ├── footer.css          # Story 1.8
│       ├── sticky-nav.css      # Story 1.8
│       └── lightbox.css        # NOVO (Story 2.5)
├── js/
│   ├── sticky-nav.js           # Story 1.8
│   └── lightbox-init.js        # NOVO (Story 2.5)
└── vendor/
    ├── htmx.min.js             # Story 1.6
    ├── bootstrap-5.3.3/        # Story 1.6
    └── glightbox/              # NOVO (Story 2.5)
        ├── glightbox.min.css   # Mihas-ručno-downloadovan
        └── glightbox.min.js    # Mihas-ručno-downloadovan
```

NIJE detektovan konflikt sa postojećom strukturom — sva nova putanja je nova ili targeted Edit postojećih fajlova.

### References

- **Epic 2 / Story 2.5 BDD:** [_bmad-output/planning-artifacts/epics.md#story-25-glightbox-integracija](../planning-artifacts/epics.md) linija 582-594
- **Architecture decisions:** [architecture.md AR-35 GLightbox 3.x](../planning-artifacts/architecture.md) linija 187 + § JavaScript decisions linija 202 + § Project structure linija 668, 677
- **UX-DR-13 Lightbox spec:** [epics.md UX-DR-13](../planning-artifacts/epics.md) linija 219 — "GLightbox 3.x sa focus trap, Esc zatvara, Tab/swipe navigation, ARIA `role=\"dialog\"`, focus restoration na zatvaranje"
- **DESIGN.md Modal/Lightbox backdrop:** [DESIGN.md § Elevation & Depth linija 287](../planning-artifacts/ux-designs/ux-CORIC_AGRAR-2026-05-27/DESIGN.md) — `rgba(15,15,15,0.85)`
- **EXPERIENCE.md Lightbox UX:** [EXPERIENCE.md § Lightbox linija 168-173](../planning-artifacts/ux-designs/ux-CORIC_AGRAR-2026-05-27/EXPERIENCE.md) + § Animacije linija 271 (fade-in 200ms ease) + § ARIA atributi linija 305 (`role="dialog"`, `aria-modal="true"`, focus trap)
- **Project context (AI agent rules):** [_bmad-output/project-context.md](../project-context.md) — § JavaScript style (linija 333-340), § Frontend deps (linija 66-70 — GLightbox 3.x lokalno), § A11y must-haves (linija 681-690), § Anti-pattern: Inline CSS / magic values (linija 508-515)
- **Story 1.8 sticky-nav.js (canonical vanilla JS pattern):** [static/js/sticky-nav.js](../../static/js/sticky-nav.js) linija 1-50
- **Story 1.6 base.html (cascade reference):** [templates/base.html](../../templates/base.html) linija 1-41
- **Story 1.7 main.css @import pattern (IMP-7 dot-prefix):** [_bmad-output/implementation-artifacts/1-7-reusable-visual-komponente.md](./1-7-reusable-visual-komponente.md)
- **Story 1.8 cross-cutting test pattern:** [tests/test_navigation_chrome.py](../../tests/test_navigation_chrome.py) (file-existence + base.html source checks)
- **Story 2.3 implementation context (responsive_picture tag — Story 2.7 konzumira pre Lightbox markup):** [_bmad-output/implementation-artifacts/2-3-image-pipeline-sa-sorl-thumbnail-responsive-srcset.md](./2-3-image-pipeline-sa-sorl-thumbnail-responsive-srcset.md)

## Previous Story Intelligence

### Story 2.4 (PDF Cover-thumbnail Generator) — completed 2026-05-30

Story 2.4 je bila **pure backend Python story** (Django signals + pdf2image + python-magic) — bez frontend/JS/CSS deliverable-a. Nije izvor patterne za Story 2.5 frontend pattern-e, ali sledeće su transferable lessons:

- **Strikturalno razdvajanje (Decision PDF-D2):** Story 2.4 je razdvojila PDF logiku u zaseban modul (`pdf_utils.py`) umesto da prošira postojeći `utils.py`. Story 2.5 prati istu princip: lightbox-specific JS ide u **zaseban fajl** `static/js/lightbox-init.js` (NE proširenje `sticky-nav.js`); lightbox CSS ide u **zaseban fajl** `static/css/components/lightbox.css` (NE proširenje `sticky-nav.css`). Razlog: jasna granica odgovornosti, lakše testiranje, lakše brisanje ako Lightbox treba zameniti (npr. PhotoSwipe migracija u v2).
- **Idempotency guards (FIX iter-1 CRIT-3 + CRIT-5 u Story 2.4):** Story 2.4 je naučila važnost multi-layer idempotency (loop guard za signal). Story 2.5 prati paralelan princip kroz **`window._coricLightbox.destroy()` pre re-init** (AC2) — ako se `initLightbox()` pozove dva puta (npr. HTMX swap + DOMContentLoaded race), stari instance se uništava pre novog, sprečava se memory leak + duplikat listenere.
- **Graceful failure (AC2 + AC4 u Story 2.4):** Story 2.4 je naučila da signal handler NIKAD ne sme pucati admin flow. Story 2.5 prati princip kroz **defensive `if (typeof window.GLightbox !== 'function') return;`** u `lightbox-init.js` — ako vendor script failu-je 404, stranica i dalje radi (Lightbox neće raditi ali ostatak strane je intact).
- **Test scope kontekst:** Story 2.4 je naučila razliku između **TEA scope** (testovi) i **Dev scope** (implementacija) — TEA piše testove PRE Dev GREEN phase, Dev NIKAD ne menja testove. Story 2.5 prati identičan workflow: AC7 specifikuje test fajl strukturu kao TEA deliverable u Step 3.
- **Vendor pinning:** Story 2.4 je dokumentovala pdf2image version u Dev Agent Record. Story 2.5 prati isti princip — Mihas dokumentuje GLightbox exact version (npr. "3.3.0") u Dev Agent Record posle download-a u AC1 Subtask 1.6.

### Story 2.3 (Image Pipeline) — done 2026-05-29

Story 2.3 je uvela `apps/media_pipeline/` utility app + `responsive_picture` template tag koji je **direktan konzument za Lightbox slike**. Story 2.7 će koristi `{% responsive_picture image alt=... %}` UNUTAR `<a class="glightbox" href="{{ image.url }}">` link-a. Story 2.5 ne treba da menja responsive_picture tag; samo dokumentuje INTEGRATION ugovor u Dev Notes § "Kanonski GLightbox markup koji Story 2.7 produkuje" sekciji.

### Story 1.8 (Sticky Nav + Header + Footer) — done 2026-05-28

Najrelevantnija prethodna story za Story 2.5 jer je uvela:

- **Vanilla JS IIFE pattern** u `static/js/sticky-nav.js` (linija 1-50) — Story 2.5 `lightbox-init.js` direktno prati identičan stil
- **`static/js/` direktorijum** je uveden u Story 1.8 — Story 2.5 dodaje 2. fajl u istom direktorijumu
- **`static/vendor/` lokalno hostovanje pattern** (htmx.min.js, bootstrap-5.3.3) — Story 2.5 prati identičan pattern za GLightbox 3.x
- **base.html cascade pattern** — Story 1.8 je uvela script ordering pravilo (htmx defer → Bootstrap sync → sticky-nav.js defer → block scripts); Story 2.5 dodaje glightbox.min.js + lightbox-init.js IZMEĐU sticky-nav.js i block scripts (svi `defer`)
- **CSP-friendly anti-pattern (CRITICAL-1 iz Story 1.8):** uklanjanje inline `onchange=` handler-a. Story 2.5 prati isti princip — NEMA inline `onclick=`/`onkeydown=` u lightbox-init.js; svi listener-i preko `addEventListener`
- **No-jQuery guard pattern:** Story 1.8 je ustanovila da svaki JS modul mora biti vanilla. Story 2.5 testovi AC7 enforce-uju ovo kroz `test_ac2_lightbox_init_no_jquery_no_module_imports`
- **HTMX integracija (deferred):** Story 1.8 NIJE dodala HTMX swap re-init (sticky nav je page-load only). Story 2.5 **dodaje prvi HTMX `afterSwap` listener** u code-base-u — kanonski pattern za sve buduće stories (Story 2.8 HTMX filteri, Story 2.13 search dropdown)

### Story 1.7 (Reusable Visual Komponente) — done 2026-05-27

Story 1.7 IMP-7 je ustanovila pravilo da svi `@import` u `main.css` koriste **leading `./` dot-prefix** (npr. `@import './components/header.css';`, NE `@import 'components/header.css';`). Story 2.5 prati ovo pravilo u AC4 Edit-u za `lightbox.css` @import.

### Story 1.6 (Base Templates Bootstrap 5 + HTMX) — done 2026-05-27

Story 1.6 je definisala kanonski script ordering u `base.html`: vendor sync scripts pre custom defer scripts. Story 2.5 prati to pravilo: GLightbox vendor JS (defer) ide POSLE Bootstrap JS (sync), PRE custom init JS. Bootstrap sync je intentional per Story 1.6 — bootstrap utility klase su occasionally referenced unutar child template-a inline (`{% bootstrap_javascript %}` ne emituje `defer`).

## Project Context Reference

Ova story striktno prati pravila iz `_bmad-output/project-context.md` (single source of truth za AI agente):

- **§ Frontend deps (linija 66-70):** "GLightbox 3.x — local (10 KB gzipped)". Story 2.5 implementira lokalno hostovanje per AR-35 + ovo pravilo.
- **§ JavaScript style (linija 333-340):**
  - Funkcije/varijable `camelCase` → `initLightbox`, `buildOptions`, `prefersReducedMotion`
  - Konstante `UPPER_SNAKE_CASE` (nema u ovom fajlu — sve su lokalne let/var)
  - Module fajlovi `kebab-case.js` → `lightbox-init.js`
  - Custom DOM events `coric:` namespace → `coric:lightbox-open`, `coric:lightbox-close`
  - Vanilla JS preferred, Alpine.js opciono, **NIKAD jQuery**
  - **No build pipeline** — JS se servira direktno iz `static/js/`
- **§ Anti-pattern: Ćirilica u kodu (linija 487-495):** Svi user-facing strings (test docstring-ovi, error poruke u JS, CSS komentari) su **srpska latinica** — NIKAD ćirilica.
- **§ Anti-pattern: Inline CSS / magic values (linija 508-515):** `lightbox.css` koristi DESIGN.md SOT za backdrop boju `rgba(15,15,15,0.85)`; ako bi se uveo token, prepravlja se kroz zasebnu story-ju.
- **§ A11y must-haves (linija 681-690):**
  - `prefers-reduced-motion` respect ✓ (AC2 + AC3)
  - Focus management → vendor GLightbox 3.x ima built-in focus trap + focus restoration ✓ (AC6)
- **§ Security must-haves (linija 669-679):**
  - CSP header preko `django-csp` — Story 2.5 koristi NO inline scripts (sve preko addEventListener), NO inline styles (sve preko CSS file), NO third-party CDN — full CSP compliant.
- **§ Performance must-haves (linija 691-698):**
  - `defer` na svim script-ovima ✓ (AC5)
  - Whitenoise compressed manifest — automatski gzip + brotli + cache busting za sve `static/` fajlove (uključujući novi `vendor/glightbox/` i `js/lightbox-init.js`)
- **§ Test discipline (linija 294-298):** TEA piše testove (RED phase), Dev piše implementaciju (GREEN phase). Story 2.5 Tasks 1-6 su Dev scope; Task 7 je TEA scope.
- **§ Commit messages (linija 398-404):** Conventional commits stil; Story 2.5 GREEN commit: `feat(static): Story 2.5 — GLightbox 3.x lokalno hostovan + lightbox-init.js IIFE + base.html cascade + lightbox.css backdrop theme`.

## Dev Agent Record

### Agent Model Used

Claude Opus 4.7 (1M context) — Dev (GREEN phase) subagent invoked by Story Orchestrator.

### Debug Log References

- `pytest tests/test_lightbox_integration.py -v --tb=short -p no:django` ran twice:
  1. Iter 1 — 20/21 pass; `test_ac2_lightbox_init_no_jquery_no_module_imports` failed because the JS module doc-block contained the literal token `jQuery` ("no jQuery") — the test does case-sensitive substring search.
  2. Iter 2 — fixed by rephrasing comment to "no legacy DOM libs"; 21/21 pass.

### Completion Notes List

**Story 2.5 GREEN phase — COMPLETE. 21/21 tests passing.**

**AC1 vendor assets (Mihas pre-flight):**
- GLightbox 3.x — files placed by Mihas in `static/vendor/glightbox/` (per AC1 manual download contract).
- `glightbox.min.css` — 13,749 bytes (≤ 50 KB minified threshold per AC1 + test #2).
- `glightbox.min.js` — 56,343 bytes; contains `GLightbox` global constructor (verified per test #3).
- SHA-512 (captured by Story Orchestrator pre-flight, per AC1 Subtask 1.4):
  - CSS: `4FE2A81B77DB0E84A7960117150AB07130BD01D905231841966A1A16A61A223AB64A184DC0D6A8F4029A2D43CC7F08813CBD1273102D73E5186C7020BDDFAC8D`
  - JS:  `5CBE784A371E5D91736E5CE236768515A5E0833A82B99AC54B896858FA6F3C9E8A83491CD87C8BF3DF9C3DE1F418CAB4B0A2F649E83352603C2F1F5AD2CB76A3`
- Exact GLightbox version (AC1 Subtask 1.6): TBD by Mihas — file mtime indicates Jan 21 2025 build. Mihas to document exact tag (3.3.0 or later) when confirming pre-flight artifact provenance.

**AC2 lightbox-init.js (Dev deliverable):**
- IIFE + `'use strict';` per Story 1.8 sticky-nav.js mirror pattern.
- Defensive guard: `typeof window.GLightbox !== 'function'` silent return.
- `MORE_TEXT` lookup table (sr/hu/en) + `getLocale()` reads `<html lang>` (Story 1.4 LocaleMiddleware-set).
- `buildOptions()` computes `prefers-reduced-motion` inside fn (so re-init picks up live OS pref).
- `initLightbox()` idempotent: typeof-guarded `destroy()` of previous `window._coricLightbox` before new instance.
- Emits `coric:lightbox-open` / `coric:lightbox-close` on window with `detail.instance` payload.
- HTMX integration: `document.body` listener on `htmx:afterSwap` with `instance.opened` guard.
- matchMedia change listener on `'(prefers-reduced-motion: reduce)'` re-invokes init (mirror sticky-nav.js IMP-1 pattern).
- No jQuery, no ES module imports, no inline event handlers.

**AC3 lightbox.css (Dev deliverable):**
- `.glightbox-clean .goverlay { background: rgba(15, 15, 15, 0.85) !important; }` (DESIGN.md § Elevation & Depth linija 287 SOT).
- `@media (prefers-reduced-motion: reduce)` block with `transition: none !important; animation: none !important;` on `.ginner-container` + `.gslide` (defensive CSS — JS init already sets `openEffect: 'none'`).

**AC4 main.css EDIT (Dev deliverable):**
- Appended single line: `@import url('./components/lightbox.css');` after Story 1.8 components group.
- Matches existing 8 imports — `url(...)` wrapper + leading `./` (Story 1.7 IMP-7 invariant).

**AC5 base.html EDIT (Dev deliverable):**
- HEAD: `<link>` for `vendor/glightbox/glightbox.min.css` inserted between `tokens.css` (now line 12) and `{% bootstrap_css %}` (now line 14).
- BODY scripts: `<script ... vendor/glightbox/glightbox.min.js defer>` + `<script ... js/lightbox-init.js defer>` inserted after `sticky-nav.js` (line 38) and BEFORE the Django comment `{# Per-page scripts POSLE site-wide ...` (now shifted to line 41 from 38; +3 lines as expected per AC5 Subtask 5.4).
- Cascade verified: tokens < glightbox.css < bootstrap_css (head); sticky-nav.js < glightbox.min.js < lightbox-init.js < `{% block scripts %}` (body).
- Regression guard PASS: Django comment preserved (test #18 `test_ac5_base_html_line_38_django_comment_preserved`).
- No CDN URLs in any modified file (test #21 `test_anti_cdn_no_external_lightbox_references` PASS).

**AC6 manual smoke check (DevTools Console injection):**
- ✅ **PASS (Mihas 2026-05-30):** smoke check izvršen na `http://localhost:8000/sr/`; Lightbox se otvara sa rgba(15,15,15,0.85) backdrop-om, Esc zatvara, focus se vraća na trigger element, nema fetch ka `cdn.plyr.io` (potvrđuje `plyr: false` guard).
- Original smoke checklist (preserved for Story 2.7 + future consumer reference):
  1. `just dev` → http://localhost:8000/
  2. F12 → Console → paste:
     ```javascript
     document.body.insertAdjacentHTML('beforeend', '<a class="glightbox" href="/static/img/coric-agrar-logo-transp-200.png">demo</a>');
     window._coricLightbox && window._coricLightbox.reload();
     ```
  3. Click demo link → verify modal opens, backdrop `rgba(15, 15, 15, 0.85)` (Computed Styles), `role="dialog"` + `aria-modal="true"` in Inspector.
  4. Tab cycle inside modal; Esc closes + restores focus to demo link; backdrop click closes.
  5. Toggle `prefers-reduced-motion: reduce` (DevTools → Rendering) → re-trigger → no fade transition.
  6. Listen to custom events:
     ```javascript
     window.addEventListener('coric:lightbox-open', (e) => console.log('OPEN', e.detail));
     window.addEventListener('coric:lightbox-close', (e) => console.log('CLOSE', e.detail));
     ```

**AC7 tests (TEA wrote, Dev satisfies):**
- 21 / 21 PASS — verified via `.venv\Scripts\python.exe -m pytest tests/test_lightbox_integration.py -v --tb=short -p no:django`.
- 0 test modifications. All assertions satisfied by code per spec.

**Test modifications log:** (none)

**Step 4 fix iter 1 (2026-05-30) — code review remediation (5-reviewer audit verdict: CONCERNS, 9 findings):**

Applied 6 mandatory fixes (BUG x2, PERF x1, SEC-MEDIUM x1, SEC-LOW x2) + 2 refactor fixes:

- **BUG #1 (Dev B + Architect convergent) — matchMedia change guard:** Extracted `safeReinit()` DRY helper used by both `matchMedia` `change` listener and `htmx:afterSwap` listener. Prevents destroy-mid-interaction when OS toggles `prefers-reduced-motion` while Lightbox is open (UX-DR-13 focus restoration safety).
- **BUG #2 (Architect) — defensive `instance.opened` fallback:** Added `isLightboxOpen()` helper with DOM-based fallback (`.glightbox-container.glightbox-open` query) for when GLightbox 4.x might rename the undocumented `.opened` property.
- **PERF #3 (Dev B) — htmx:afterSwap no-op skip:** Early-return guard `if (!document.querySelector('.glightbox')) return;` prevents wasteful destroy+init churn on swaps that contain no gallery elements (language switcher, OOB updates, future Story 2.13 search dropdown).
- **SEC-MEDIUM #4 (Security) — Plyr CDN dormant risk:** Added `plyr: false` to `buildOptions()` to neutralize hard-coded `cdn.plyr.io` URLs baked into GLightbox 3.3.1 vendor source. Currently dormant (image galleries don't trigger), but future video lightbox would silently fetch from third-party CDN without this guard.
- **SEC-LOW #5 (Architect + Security) — vendor pin meta:** Created `static/vendor/glightbox/VERSION.txt` documenting version (3.3.1), source URL, license (MIT), file sizes, SHA-512 hashes, and TODO for upstream-vs-local hash verification before Story 9.2 production deploy.
- **SEC-LOW #6 (Security) — anti-CDN reinforcement test:** Added test #22 `test_ac7_plyr_cdn_dormant_via_buildoptions_disable` to `tests/test_lightbox_integration.py` — regression guard that fails if a future Dev removes `plyr: false`. Total tests: 21 -> 22.
- **REFACTOR #7 (Dev B) — duplicate File List:** Removed duplicate "NOVA (Dev GREEN phase)" / "EDIT (Dev GREEN phase)" / "NOVA (TEA RED phase)" block at end of File List section.
- **REFACTOR #8 (TEA) — test dead alternative:** Simplified `test_ac2_dispatches_coric_namespace_events` — removed unreachable `"window .dispatchEvent" in source` alternative (spaced variant cannot match real source).

**Deferred findings (6 — documented as `unfixable_issues` in fix return, with rationale):**
1. ARCHITECTURE (Architect): test location `tests/` vs `tests/integration/` — project-wide decision, matches Story 1.6/1.7/1.8 precedent; defer to future test-reorg story.
2. PERFORMANCE (Architect): CSS @import chain blocks parallel download — acceptable for v1 per LCP budget; revisit at >15 imports.
3. SEC-LOW (Security): upstream-vs-local SHA-512 verification — manual action; documented in VERSION.txt TODO.
4. SEC-LOW (Security): django-csp not in MIDDLEWARE — deferred to dedicated security story; vendor inline-style nonce wiring will follow.
5. TEA REFACTOR: test #2 size threshold future-proofing — comment-only suggestion; current code clear.
6. TEA ARCHITECTURE: test #11 comment-text fragility — already self-corrected during Dev GREEN iter 1.

**Test run after fixes:** `.venv\Scripts\python.exe -m pytest tests/test_lightbox_integration.py -v --tb=short -p no:django` -> 22 / 22 PASS.

### File List

NOVA (Mihas pre-flight, Task 1):
- `static/vendor/glightbox/glightbox.min.css` (13,749 bytes)
- `static/vendor/glightbox/glightbox.min.js` (56,343 bytes)

NOVA (Dev GREEN phase):
- `static/js/lightbox-init.js` (Story 2.5 AC2 — IIFE init module)
- `static/css/components/lightbox.css` (Story 2.5 AC3 — backdrop override + reduced-motion)

EDIT (Dev GREEN phase):
- `static/css/main.css` (+1 line: `@import url('./components/lightbox.css');`)
- `templates/base.html` (+3 lines: 1 CSS link in head + 2 script tags in body)

NOVA (TEA RED phase, Step 3):
- `tests/test_lightbox_integration.py` (21 tests; all PASS after Dev GREEN phase)

EDIT (orchestrator + Dev workflow tracking):
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (status: review → in-progress → review)
- `_bmad-output/implementation-artifacts/2-5-glightbox-integracija.md` (Dev Agent Record sections + Tasks 2-5 checkboxes marked)

NOVA (Dev FIX iter 1 — Step 4 code review remediation):
- `static/vendor/glightbox/VERSION.txt` (vendor pin meta + SHA-512 + npm verification TODO — SEC-LOW #5 fix)

EDIT (Dev FIX iter 1 — Step 4 code review remediation):
- `static/js/lightbox-init.js` (BUG #1 safeReinit helper + matchMedia guard; BUG #2 isLightboxOpen() DOM fallback; PERF #3 .glightbox no-op skip; SEC-MEDIUM #4 plyr: false guard)
- `tests/test_lightbox_integration.py` (added test #22 `test_ac7_plyr_cdn_dormant_via_buildoptions_disable`; simplified test #4 dead-alternative branch)
- `_bmad-output/implementation-artifacts/2-5-interface-contract.md` (test count 21 → 22; documented plyr: false buildOptions requirement)
