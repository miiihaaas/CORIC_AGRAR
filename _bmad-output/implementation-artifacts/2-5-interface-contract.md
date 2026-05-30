---
story-id: "2.5"
story-key: 2-5-glightbox-integracija
artifact: interface-contract
created: 2026-05-30
author: TEA (RED phase)
purpose: Frontend integration contract for GLightbox 3.x — file paths, base.html cascade,
         JS module surface (window globals + custom events), CSS override targets.
---

# Interface Contract — Story 2.5 GLightbox Integracija

Story 2.5 je **frontend-only** integracija — nema Django modela, URL-ova, view-ova, migracija.
Ovaj ugovor definiše **fajl-sistem strukturu** + **DOM/window surface** + **HTML template kaskadu**
koju Dev mora isporučiti u GREEN phase. TEA-ovi testovi u `tests/test_lightbox_integration.py`
verifikuju svaki red ove specifikacije.

---

## 1. File-system delta

### Fajlovi koji MORAJU postojati posle GREEN phase (5 novih + 2 edita)

| Path | Status | Velicina (kontrola) |
|---|---|---|
| `static/vendor/glightbox/glightbox.min.css` | NOVO (Mihas pre-download) | <= 50 KB (minified heuristika) |
| `static/vendor/glightbox/glightbox.min.js` | NOVO (Mihas pre-download) | mora sadrzati `GLightbox` token |
| `static/js/lightbox-init.js` | NOVO (Dev) | IIFE + use strict + idempotent |
| `static/css/components/lightbox.css` | NOVO (Dev) | backdrop override + reduced-motion |
| `static/css/main.css` | EDIT (Dev) | +1 linija `@import url('./components/lightbox.css');` |
| `templates/base.html` | EDIT (Dev) | +3 linije (1 link + 2 script) |
| `tests/test_lightbox_integration.py` | NOVO (TEA) | 22 testova (21 originalna + 1 dodat u fix iter 1 — `test_ac7_plyr_cdn_dormant_via_buildoptions_disable`) |

### Fajlovi koji MORAJU OSTATI NETAKNUTI (regression guard)

- `apps/core/`, `apps/products/`, `apps/brands/`, `apps/media_pipeline/` (no Python promene)
- `templates/partials/header.html`, `templates/partials/footer.html`
- `static/js/sticky-nav.js` (Story 1.8 deliverable)
- `static/css/tokens.css` (Story 1.5 deliverable)
- `static/css/components/{header,footer,sticky-nav,*}.css` osim sto se main.css @import lista produzava
- `pyproject.toml` (no nove Python deps)
- `config/settings/base.py`

---

## 2. `static/css/main.css` ugovor (EDIT)

### Ulaz (postojece stanje pre Edit-a)
8 `@import` linija u dva komentarisana bloka (Story 1.7 + 1.8). Sve linije koriste
**`url(...)` wrap-er sintaksu** sa **leading `./`** (IMP-7 invariant).

### Izlaz (posle Edit-a)
Postojecih 8 linija ostaju netaknute; **dodaje se TACNO 1 nova linija na kraj**:

```css
@import url('./components/lightbox.css');
```

Quote-agnostic substring guarantija: rezultat mora sadrzati `@import` + `components/lightbox.css`
u istom redu. Test #15 (`test_ac4_main_css_imports_lightbox_component`) verifikuje.

---

## 3. `templates/base.html` kaskada (EDIT)

### HEAD section — CSS redosled (TACAN cascade)

```
1. {% load static %}  (Story 1.5 deliverable)
2. <link rel="stylesheet" href="{% static 'css/tokens.css' %}">       (linija 12 — Story 1.5)
3. <link rel="stylesheet" href="{% static 'vendor/glightbox/glightbox.min.css' %}">   (NOVO — Story 2.5)
4. {% bootstrap_css %}                                                 (linija 13 — Story 1.6)
5. <link rel="stylesheet" href="{% static 'css/main.css' %}">          (linija 14 — Story 1.6)
6. {% block extra_head %}{% endblock %}
```

**Pozicija invariant:** `tokens.css` indeks < `vendor/glightbox/glightbox.min.css` indeks < `bootstrap_css` indeks.
Razlog: nas override (`static/css/components/lightbox.css` ucitan kroz `main.css` posle Bootstrap-a)
mora pobediti u cascade — vendor CSS u HEAD se ucitava PRE Bootstrap-a tako da nema clash-a.

Test #16 verifikuje quote-agnosticky redosled.

### BODY scripts section — JS redosled (TACAN cascade)

```
1. <script src="{% static 'vendor/htmx.min.js' %}" defer></script>          (linija 35 — Story 1.6)
2. {% bootstrap_javascript %}                                                (linija 36 — Story 1.6)
3. <script src="{% static 'js/sticky-nav.js' %}" defer></script>            (linija 37 — Story 1.8)
4. <script src="{% static 'vendor/glightbox/glightbox.min.js' %}" defer></script>  (NOVO — Story 2.5)
5. <script src="{% static 'js/lightbox-init.js' %}" defer></script>          (NOVO — Story 2.5)
6. {# Per-page scripts POSLE site-wide — sync init safe za Bootstrap komponente #}  (preserved Story 1.6 comment)
7. {% block scripts %}{% endblock %}
```

**Redosled invariants:**
- `sticky-nav.js` indeks < `vendor/glightbox/glightbox.min.js` indeks (test #19 lightbox-scripts-after-sticky-nav AC5)
- `vendor/glightbox/glightbox.min.js` indeks < `js/lightbox-init.js` indeks (test #21 vendor-before-init)
- `vendor/glightbox/glightbox.min.js` indeks < `{% block scripts %}` indeks (test #17)
- `js/lightbox-init.js` indeks < `{% block scripts %}` indeks (test #17)

### Regression guard — Django komentar
Linija 38 (pre Edit-a) sadrzi `{# Per-page scripts POSLE site-wide ...`. Posle Edit-a,
komentar je shift-ovan na liniju 41 (zbog +3 nove linije). Test #18 verifikuje da je
substring `{# Per-page scripts POSLE site-wide` jos uvek u source-u.

---

## 4. `static/js/lightbox-init.js` modul ugovor

### Struktura
- IIFE wrap: source mora sadrzati `(function ()` + `'use strict';`
- Defensive guard: ako `window.GLightbox !== 'function'`, silently return
- No jQuery, no `import`/`export`, no inline event handlers

### Window globals (citanje i pisanje)
- **Pise:** `window._coricLightbox` — drzi referencu na GLightbox instance
- **Cita:** `window.GLightbox` (vendor constructor), `window.matchMedia`,
  `document.documentElement.lang`

### GLightbox options (buildOptions return)
Mora sadrzati TACNE kljuceve (po imenu) — per Story AC2 Dev Notes sample (linija 131-142):
- `selector` ('.glightbox')
- `touchNavigation`
- `loop`
- `openEffect`, `closeEffect`, `slideEffect`
- `moreText` (lokal-aware — `MORE_TEXT[getLocale()] || MORE_TEXT.sr`)
- `plyr: false` (Anti-CDN guard — Security review iter 1 SEC-MEDIUM; neutralise
  hard-coded `cdn.plyr.io` URL-ove u GLightbox 3.3.1 vendor source-u. Re-enable
  tek kad Plyr bude lokalno hostovan u future story. Test #22 enforce-uje.)

NAPOMENA: `keyboardNavigation` NIJE u Story sample-u i NIJE u AC7 enumeration-u — vendor
GLightbox 3.x ima keyboard navigation enabled by default, ne treba eksplicitan opt-in u
buildOptions. Test #6 (`test_ac2_buildoptions_includes_required_keys`) ne proverava ovaj
kljuc.

### Custom events
- **`coric:lightbox-open`** — dispatch-uje se na `window` sa `detail.instance` payload-om kad
  GLightbox `open` event okine
- **`coric:lightbox-close`** — dispatch-uje se na `window` sa `detail.instance` payload-om kad
  GLightbox `close` event okine

Konzumenti (Story 2.6 slider auto-advance pause, future analytics) mogu hook-ovati ove eventove
preko `window.addEventListener('coric:lightbox-open', handler)`.

### Lokal lookup
```javascript
var MORE_TEXT = { sr: 'Vise', hu: 'Tobb', en: 'More' };
function getLocale() {
  return (document.documentElement.lang || 'sr').slice(0, 2);
}
```

### Idempotency (re-init guard)
Pre nego sto se kreira nov `GLightbox()` instance:
1. Provera `typeof window._coricLightbox` defensive guard
2. Ako prethodni instance postoji i ima `destroy` metod, pozvati `destroy()`
3. Tek onda kreirati novi instance

### HTMX integration
Listener na `document.body` za `htmx:afterSwap` event:
- PERF guard (fix iter 1): preskoci re-init ako swap ne sadrzi nijedan
  `.glightbox` element (sprecava destroy+init churn na language switcher /
  OOB updates / Story 2.13 search dropdown swap-ovima)
- Open-modal guard: ako je modal otvoren (preko `isLightboxOpen()` helper-a sa
  DOM fallback-om) → skip re-init (ne yank-uj fokus)
- Inace → `initLightbox()` kroz `safeReinit()` helper (re-bind selektore za nove
  `.glightbox` elemente)

### matchMedia re-init (prefers-reduced-motion)
Listener na `window.matchMedia('(prefers-reduced-motion: reduce)')` `change` event
poziva `safeReinit()` (BUG #1 fix iter 1) da pokupi novu OS preferenciju.
**Mora** koristiti isti open-modal guard kao htmx:afterSwap — toggle OS pref dok
je modal otvoren NE sme destroy-ovati modal mid-interaction (UX-DR-13 focus
restoration contract).

---

## 5. `static/css/components/lightbox.css` ugovor

### Backdrop override
```css
.glightbox-clean .goverlay {
  background: rgba(15, 15, 15, 0.85) !important;
}
```

Selektor `.glightbox-clean .goverlay` je TACAN — `.glightbox-clean` je default skin
GLightbox 3.x, `.goverlay` je backdrop wrapper. `!important` je dozvoljen jer pobedjuje
vendor inline style.

### Reduced motion guard
```css
@media (prefers-reduced-motion: reduce) {
  .glightbox-clean .ginner-container,
  .glightbox-clean .gslide {
    transition: none !important;
    animation: none !important;
  }
}
```

---

## 6. Anti-CDN guard (kritican!)

### Zabranjene URL reference (u `templates/base.html`, `static/css/main.css`,
### `static/js/lightbox-init.js`, `static/css/components/lightbox.css`)

- `cdnjs.cloudflare.com` (bilo gde u source-u sa rec "glightbox" u istom fajlu)
- `unpkg.com` (bilo gde)
- `jsdelivr.net` / `cdn.jsdelivr.net` (bilo gde)

Sva referenca na GLightbox vendor mora biti relativna `{% static 'vendor/glightbox/...' %}`.

Test #20 (`test_anti_cdn_no_external_lightbox_references`) verifikuje 0 matches.

---

## 7. AC pokrivenost — test mapping

| AC | Sta verifikuje | Testovi |
|---|---|---|
| AC1 | Vendor files (CSS + JS) postoje + size + global | #1, #2, #3 |
| AC2 | lightbox-init.js IIFE + options + events + lokal + idempotency + htmx + prefers-reduced-motion + no-jquery | #4, #5, #6, #7, #8, #9, #10, #11, #12 |
| AC3 | lightbox.css backdrop + reduced-motion | #13, #14 |
| AC4 | main.css @import row | #15 |
| AC5 | base.html cascade (CSS link + scripts + redosled + comment) | #16, #17, #18, #19, #21 |
| AC6 | Manuelni browser smoke (DevTools Console injection) | MANUAL (not automated) |
| AC7 | Anti-CDN guard (CDN URL ban + Plyr dormant disable) | #20, #22 |

Ukupno: **22 automatizovan testa** (21 originalna RED-phase + 1 dodat u fix iter 1 — `test_ac7_plyr_cdn_dormant_via_buildoptions_disable`), **1 manuelni smoke** (AC6).

Test count je 21 (a ne 19 originalno enumerirano u Story AC7) jer su dva valuable testa
dodata povrh AC7 minimum-a:
- Test #7 `test_ac2_uses_locale_lookup_for_moretext` — verifikuje MORE_TEXT mapu (sr/hu/en)
  + getLocale funkciju (interface contract surface)
- Test #6 `test_ac2_buildoptions_includes_required_keys` — verifikuje sve TACNE kljuc-imena
  GLightbox opcija iz Story AC2 sample-a

AC7 explicitno koristi termin "MORA imati MINIMUM sledece test funkcije" (linija 327) —
21 > 19 minimum je u skladu sa specifikacijom.

---

## 8. Dev pre-flight check

Pre nego sto Dev pokrene GREEN phase, mora verifikovati:

1. `static/vendor/glightbox/glightbox.min.css` postoji (Mihas pre-download)
2. `static/vendor/glightbox/glightbox.min.js` postoji (Mihas pre-download)

Ako nedostaju, Dev HALT-uje sa porukom u Completion Notes:
"BLOCKED: Mihas mora preuzeti GLightbox 3.x sa https://github.com/biati-digital/glightbox/releases"

Tek po prisustvu oba fajla Dev nastavlja sa AC2-AC7.

---

## 9. Out-of-scope (eksplicitno)

- Real-browser keyboard navigation testovi (Tab/Esc/Arrow) — **Story 9.8 Playwright scope**
- WCAG axe-core static analysis — **Story 9.9 a11y audit scope**
- Konkretna galerija proizvoda (Product Detail strana) — **Story 2.7**
- Variant selector Lightbox markup — **Story 2.7**
- Home masonry Lightbox — **Story 3.1 / 3.2 (opciono)**
- Blog post slike Lightbox — **Story 5.3 (opciono)**
