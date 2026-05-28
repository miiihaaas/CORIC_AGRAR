---
story-id: "1.8"
story-key: 1-8-sticky-nav-top-header-footer-language-switcher-partial
title: Sticky Nav + Top Header + Footer + Language Switcher Partial
status: review
epic_num: 1
epic_title: Project Foundation & Visual Identity
module: cross-cutting (templates/partials/ + static/js/ + static/css/components/)
created: 2026-05-28
last_modified: 2026-05-28
author: Mihas (SM autonomous)
---

# Story 1.8: Sticky Nav + Top Header + Footer + Language Switcher Partial

Status: review

## Story

As a **posetilac sajta (Marko, Stojan, Marijana, Đorđe)**,
I want **konzistentan top header sa kontakt informacijama + sticky glavni nav sa shrink-on-scroll ponašanjem + solid green footer sa 4 kolone i social linkovima + integrisan language switcher dostupan sa svake strane**,
so that **navigacija i kontakt podaci (telefon servisa za Stojana sa terena, social za Marijanu) su uvek dostupni, sa pristupačnošću tastatura/čitača ekrana i mobilnim hamburger menijem za polje (<768px) i bez zaglušujuće animacije kod korisnika koji su zatražili `prefers-reduced-motion: reduce`**.

Ova story je **prvi konzument iz Story 1.7 reusable library** — direktno reuse **Section Eyebrow** (UPPERCASE heading-ovi 3 footer kolona — PROIZVODI, NAJNOVIJE VESTI, KONTAKT — sa zlatnim linijama; variant `on-dark`) i **opciono Pill Button** (sekundarna varijanta za CTA u nav-u/footer-u — vidi Decision D15, default je "not used"). Ostale tri komponente iz Story 1.7 (Repeating Element, Wave Divider, Hero Overlay Card) NIJE konzumiraju u Story 1.8 — one su za Epic 2-7 katalogske strane. Ne dodaje nove tokene; konzumira postojeće iz `tokens.css` (Story 1.5).

Ova story je takođe **prvi konzument projekta za `static/js/`** — uvodi `sticky-nav.js` kao vanilla JS modul (no build pipeline — `static/js/` se servira direktno preko Whitenoise per project-context.md § Frontend), učitan preko `defer` atributa u `templates/base.html`.

**Foundation za:**
- **Story 1.9 (CI Pipeline):** lint pravila moraju validirati novi JS fajl (`ruff` za Python ne čita JS — Dev Notes dokumentuje kako se JS validira u v1: manual + pytest na file existence).
- **Story 2.6+ (Brand listing, Product detail):** sve katalogske strane nasleđuju `base.html` koji već sadrži `{% include "partials/header.html" %}` i `{% include "partials/footer.html" %}`.
- **Story 3.1 (Home strana):** koristi celi `base.html` chrome.
- **Story 5.4 (Footer dynamic Najnovije vesti):** zameniće Lorem Ipsum placeholder dinamičkim BlogPost queryset-om.
- **Story 9.8 (Playwright E2E):** verifikuje stvarno scroll ponašanje + mobile hamburger toggle + language switcher state.

**Princip:** Tri nova partial-a (`header.html`, `footer.html`, `language_switcher_nav.html`) + jedan JS modul (`sticky-nav.js`) + parni CSS fajlovi (`header.css`, `footer.css`, `sticky-nav.css`). Bootstrap 5 dropdown + collapse za "Mehanizacija" dropdown i hamburger toggle (no custom JS for those — sve standardno preko `data-bs-toggle` atributa). Custom JS samo za sticky shrink-on-scroll (`IntersectionObserver` pattern). **Postojeći `language_switcher.html` (Story 1.4) ostaje netaknut kao regression guard**, ali Story 1.8 kreira NOVI partial `language_switcher_nav.html` (Decision D3) sa 3 link/form-button po locale (jedan POST `<form>` per locale → no inline `onchange=` handler → CSP-friendly + `aria-current="page"` na trenutnom locale-u — vidi CRITICAL-1 fix u changelog-u + AC4).

**Strukturna arhitektura (post-fix CRITICAL-5/6/7):** base.html ne uvija top-header + nav u zajednički `<header>` wrapper. Umesto toga:
- Sentinel je **direct child `<body>`** PRE include header.html (ne unutar header partial-a — sprečava da sentinel bude sakriven sopstvenim efektom kad top-header dobije `height: 0`).
- `<body>` ima `position: relative` (set u sticky-nav.css) da bi sentinel `position: absolute; top: 100px` imao stable containing block.
- Top-header (`<div class="coric-top-header">`) i Nav (`<nav class="coric-nav">`) renderuju se kao DVA SIBLINGS na body level (NE jedan `<header>` wrapper iznad njih), tako da `position: sticky` na `.coric-nav` ima `<body>` kao containing block i sticky bug "scroll-away-with-wrapper" se eliminiše.
- CLS u shrunk stanju: top-header se NE krije sa `display: none` (CLS regression u D16); umesto toga koristi `height: 0; overflow: hidden;` transition (smooth collapse) — vidi CRITICAL-11 fix + Decision D16.

## Acceptance Criteria

**AC1 — Direktorijumi i nove fajl-strukture postoje sa očekivanom strukturom**

- **Given** projekat iz Story 1.7 (`templates/partials/{pill_button,section_eyebrow,language_switcher}.html` + `static/css/components/{pill-button,section-eyebrow}.css` + `static/css/main.css` sa @import direktivama postoje)
- **When** kreiram nove fajlove
- **Then** sledeća struktura mora postojati:
  - `templates/partials/header.html` (NOVO)
  - `templates/partials/footer.html` (NOVO)
  - `templates/partials/language_switcher_nav.html` (NOVO — Decision D3 RESOLUTION: nav-specifični language switcher sa 3 `<form>` po locale + `<button type="submit">` + `aria-current="page"` na trenutnom locale-u; NO inline `onchange=` → CSP-friendly; jedan partial per locale link → satisfijes AC4)
  - `static/css/components/header.css` (NOVO — CSS za top-bar, navbar, sticky states, mobile collapse)
  - `static/css/components/footer.css` (NOVO — CSS za green-800 bg, 4 kolone, copyright separator)
  - `static/css/components/sticky-nav.css` (NOVO — sticky shrunk-state animation tokens, transitions, motion-guards, `body { position: relative }` za sentinel positioning)
  - `static/js/` (NOVO direktorijum — prvi put se kreira u projektu)
  - `static/js/sticky-nav.js` (NOVO — vanilla JS modul, IIFE pattern, IntersectionObserver, `matchMedia` resize listener)
  - `static/img/` (NOVO direktorijum — prvi put se kreira u projektu; vidi Task 1.9 + 1.10)
  - `static/img/coric-agrar-logo-transp-200.png` (NOVO — kopirano iz `docs/Dizajn/_HTML/img/`)
  - `static/img/coric-agrar-logo-transp-light-200.png` (NOVO — kopirano iz `docs/Dizajn/_HTML/img/`)
- **And** `templates/partials/{language_switcher,pill_button,section_eyebrow,repeating_element,wave_divider,hero_overlay_card}.html` ostaju **netaknuti** (regression guard za Story 1.4 + 1.7). KRITIČNO: `language_switcher.html` (Story 1.4) ostaje sa svojim postojećim inline `onchange="this.form.submit()"` — to je known CSP debt deferred to Story 1.9/8.x; Story 1.8 NE uključuje `language_switcher.html` u nov header.html (jer ima inline handler), umesto toga koristi novi `language_switcher_nav.html`.
- **And** `static/css/tokens.css` ostaje **netaknut** (regression guard za Story 1.5).
- **And** `static/css/main.css` se proširuje sa 3 nova `@import` linije za `header.css`, `footer.css`, `sticky-nav.css` (relative-with-dot `./components/...` sintaksa — IMP-7 iz Story 1.7).
- **And** `templates/base.html` se **modifikuje** sa sledećim KANONSKIM redosledom (CRITICAL-4 + CRITICAL-5 + CRITICAL-7 fix — flatten Option A):
  1. `<body>` otvara
  2. Skip link (`<a class="visually-hidden-focusable">...`) ostaje prvi (regression sa Story 1.6)
  3. `<div class="coric-sticky-sentinel" aria-hidden="true"></div>` — **NOVO, direct child `<body>`**, pre header include (CRITICAL-5: sentinel mora biti VAN top-header da observer ne izgubi signal kad top-header dobije `height: 0`). **IMP-CASCADE-12 iter 2:** `tabindex="-1"` UKLONJEN — `<div>` je po default-u NE-focusable (samo elementi sa `tabindex`, links, buttons, inputs, contenteditable su focusable). `tabindex="-1"` na `<div>` je suvišan + signal za code reader-e da je element nekada bio focusable. `aria-hidden="true"` je dovoljan da signaliziramo AT-ovima da preskoče element.
  4. `{% include "partials/header.html" %}` — sadrži `.coric-top-header` + `<nav class="coric-nav">` kao dva siblings (NE wrapped u `<header class="coric-site-header">` — CRITICAL-7 flatten Option A)
  5. `<main id="main-content" tabindex="-1">...</main>` (regression sa Story 1.6)
  6. `{% include "partials/footer.html" %}` — POSLE `</main>` i PRE `{% aria_live %}` (CRITICAL-4 kanonski redosled)
  7. `{% aria_live %}` (regression sa Story 1.6)
  8. `<noscript>...</noscript>` (regression sa Story 1.6)
  9. Scripts: `htmx defer` → `{% bootstrap_javascript %}` (sync) → `<script src="{% static 'js/sticky-nav.js' %}" defer></script>` (NOVO) → `{% block scripts %}`
- **And** postojeći `<header>{% include "partials/language_switcher.html" %}</header>` blok se UKLANJA iz base.html (language switcher se sada renderuje INTERNO unutar header.html preko `{% include "partials/language_switcher_nav.html" %}`).

**AC2 — Top header (desktop & tablet ≥768px) renderuje adresu + telefon prodaje + telefon servisa + social linkove sa pravim ARIA atributima i kontaktnim semantičkim elementima**

- **Given** `templates/partials/header.html` kreiran i uključen u `base.html`
- **When** GET na bilo koju stranu (npr. `/sr/`) sa viewport ≥768px
- **Then** rendered HTML sadrži `<div class="coric-top-header" role="banner" aria-label="{% translate "Kontakt informacije" %}">` — KRITIČNO: ovaj `<div>` je **direct child header.html template root** (standalone sibling sa `<nav>`, NE wrapped u `<header class="coric-site-header">` — CRITICAL-7 flatten Option A). **CRITICAL-CASCADE-1 (iter 2):** `role="banner"` (NE `role="region"`) — top-header nosi ARIA `banner` landmark koji je iter 1 izgubio kad je flatten uklonio `<header class="coric-site-header">` wrapper. `.coric-top-header` je prvi chrome region na template root i logički je banner landmark; `<nav>` ostaje sa `role="navigation"`. Per WAI-ARIA Authoring Practices: jedan `role="banner"` po stranici je dozvoljen (uz `<main>` + `<contentinfo>` u footer-u). Renderuje:
  - Adresu kao `<p class="coric-top-header__address">Vojvođanska 1, Bašaid, Srbija</p>` (IMP-2: HTML5 `<address>` element je rezervisan za "contact information for the nearest `<article>` or `<body>` element ancestor" — kontaktna info kompanije u top headeru NIJE semantički `<address>`; koristimo `<p>` sa BEM klasom; lokalizovano kroz `{% translate %}`)
  - Telefon prodaje kao `<a href="tel:+381230468168" class="coric-top-header__phone">+381 230 468 168</a>` sa `aria-label="{% translate "Telefon prodaje" %}"`
  - Telefon servisa kao `<a href="tel:+381XXXXXXXXX" class="coric-top-header__phone--service">{% translate "Servis" %}: +381 XXX XXX XXX</a>` sa `aria-label="{% translate "Telefon servisa" %}"` — **IMP-4 RESOLUTION:** broj servisa je **hardkoderan placeholder string** u v1 (npr. `+381 XXX XXX XXX`) jer SiteSettings model NE postoji u Epic 1. Dev Notes TODO: Story 8.x SiteSettings model uvodi `service_phone` field; tada zameniti hardkoderani placeholder sa `{{ site_settings.service_phone }}` template var.
  - Social ikone kao `<a href="#" aria-label="Facebook" class="coric-top-header__social"><svg aria-hidden="true">...</svg></a>` minimum za Facebook + Instagram (placeholder href-ovi `#` u v1 — dinamičke vrednosti dolaze u Epic 8 SiteSettings).
- **And** klasa `.coric-top-header` ima:
  - `background-color: var(--color-brand-green-900)` (najtamniji ton — DESIGN.md `colors.brand.green-900`)
  - `color: var(--color-semantic-text-on-dark)` (white)
  - `padding: var(--spacing-scale-2) var(--spacing-container-gutter-desktop)` (8px 24px)
  - `font-size: var(--typography-scale-caption)` (0.875rem / 14px)
  - Visina: `height: 40px` (full state, hardcoded — IMP-9 konstanta `TOP_HEADER_HEIGHT` formalno dokumentovana; **CRITICAL-CASCADE-4 (iter 2):** mora biti eksplicitna numerička vrednost umesto `height: auto` jer CSS NE može animirati iz `auto` u `0` — bez eksplicitne pune vrednosti `height: 0` tranzicija neće smooth-animirati). Mobile override: `@media (max-width: 767px) { .coric-top-header { height: auto; } }` (mobile expand-on-toggle ima varijabilnu visinu collapse sadržaja; sticky shrink se ne primenjuje na mobile per D4).
  - `overflow: hidden` (KRITIČNO — za smooth `height: 0` collapse u shrunk state; CRITICAL-11 + Decision D16 fix)
  - `visibility: visible` (full state — **CRITICAL-CASCADE-3 (iter 2):** parna sa `visibility: hidden` u shrunk state; transitiona sa `transition-delay` 0s u full state da odmah postane visible, i sa 200ms delay u shrunk state da flips POSLE height tranzicije; uklanja descendants iz tab order + screen reader announcement u shrunk state per WCAG 2.4.7 / 2.4.11)
  - `transition: height 200ms ease, padding 200ms ease, visibility 0s linear 0s` (smooth collapse umesto `display: none` koji bi izazvao CLS; visibility transition-delay pattern dokumentovan u sticky-nav.css; vidi Dev Notes "CSS Transition Shorthand Reference" za parsing detalje full vs shrunk state).
- **And** linkovi u top header-u imaju `min-height: 44px` (touch target WCAG 2.5.5/2.5.8) na mobilnim breakpointima — videti AC6.

**AC3 — Glavni nav (sticky position) renderuje logo + 6 stavki menija + dropdown za "Mehanizacija" + search ikonu + language switcher; nav je sticky preko cele strane**

- **Given** `header.html` uključen u `base.html`
- **When** GET na bilo koju stranu sa viewport ≥768px
- **Then** rendered HTML sadrži `<nav class="coric-nav navbar navbar-expand-md" role="navigation" aria-label="{% translate "Glavna navigacija" %}">` — KRITIČNO: `<nav>` je **direct child header.html template root** (standalone sibling sa `.coric-top-header`, NE wrapped u `<header class="coric-site-header">` — CRITICAL-7 flatten Option A — eliminiše "sticky scrolls away with wrapper" bug; nav-ov containing block za `position: sticky` postaje `<body>`). Renderuje:
  - Logo kao `<a class="navbar-brand coric-nav__logo" href="{% url 'core:home' %}"><img src="{% static 'img/coric-agrar-logo-transp-200.png' %}" alt="Ćorić Agrar"></a>` (CRITICAL-9: `apps/core/urls.py` ima `app_name = 'core'` + `path('', home, name='home')`; URL name je **`core:home`** — fully qualified namespace; URL UVEK postoji post-Story 1.4 pa nema "fallback" wording-a).
  - 6 stavki menija (per EXPERIENCE.md § Information Architecture linije 43-63):
    - Početna (`{% url 'core:home' %}`)
    - Traktori (`#` placeholder — Epic 2 zamenjuje stvarnim URL-om; dropdown sa 3 brenda planiranih za Epic 2 — u Story 1.8 staticki placeholderi: Wuzheng / Agri Tracking / Saillong by Maki)
    - **Mehanizacija** — Bootstrap 5 dropdown (`data-bs-toggle="dropdown"`, `aria-haspopup="true"`, `aria-expanded="false"`) sa stavkama: Priključna mehanizacija (Jeegee), Radne mašine (HZM), MIX prikolice (Tulip), Polovna mehanizacija. Sve stavke su placeholderi href="#" u Story 1.8 — pravi URL-ovi dolaze u Epic 2.
    - Servis (sa dropdown: Servisna podrška, Rezervni delovi — placeholderi; non-binding stylistic note: dropdown markup-a za Servis NE renderuje u Story 1.8 — samo Mehanizacija ima dropdown; Servis je single link u v1)
    - Priče sa polja (placeholder href)
    - O nama (placeholder)
    - Kontakt (placeholder)
  - Search ikonu kao `<button type="button" class="coric-nav__search-toggle" aria-label="{% translate "Otvori pretragu" %}" data-coric-search-toggle><svg aria-hidden="true">...</svg></button>` — IMP-3 FIX: `aria-expanded` atribut UKLONJEN (button trenutno NE controlsuje expanded state; Bootstrap toggle wiring stiže u Story 2.13. `aria-expanded` bez funkcionalnog toggle-a je a11y misinformation — bolje ga ne renderovati uopšte dok ne postoji). Klik = no-op u Story 1.8; full implementacija u Story 2.13.
  - Language switcher kao `{% include "partials/language_switcher_nav.html" %}` (CRITICAL-1 fix: koristi NOVI partial — vidi AC4 za strukturu).
- **And** klasa `.coric-nav` ima:
  - `position: sticky; top: 0; z-index: 1020;` (CRITICAL-12 fix: Bootstrap `.dropdown-menu` default z-index je 1000 + popover 1010; nav mora biti iznad obojih. 1020 je ispod modal default 1055 — pravilan layering. Decision D11 ažuriran.)
  - `background-color: var(--color-brand-green-800)` (DESIGN.md `colors.brand.green-800` — nav bg)
  - `color: var(--color-semantic-text-on-dark)` (white)
  - `height: 80px` (full state — Dev Notes Decision D1; matches DESIGN.md container conventions)
  - `transition: height 200ms ease, box-shadow 200ms ease` (200ms per EXPERIENCE.md § Sticky nav linija 216)
- **And** Mehanizacija dropdown koristi **Bootstrap 5 dropdown API** (no custom JS — Decision D2): `data-bs-toggle="dropdown"`, `aria-expanded`, `aria-haspopup="true"`, `aria-labelledby`. Bootstrap već uključen kroz `{% bootstrap_javascript %}` u `base.html` (Story 1.6).
- **And** stavke menija imaju klasu `nav-link coric-nav__link`, `text-transform: uppercase`, `letter-spacing: var(--typography-tracking-wide)`, `font-weight: var(--typography-weight-bold)`, `min-height: 44px` (touch target), i `:focus-visible` outline koristi `var(--color-semantic-focus-ring)`.

**AC4 — Language switcher prikazuje 3 jezika (SR/HU/EN) sa `aria-current="page"` za trenutni i lokalizovanim `aria-label`**

- **Given** Story 1.8 kreira NOVI partial `templates/partials/language_switcher_nav.html` (CRITICAL-1 fix: Story 1.4 `language_switcher.html` ima inline `onchange="this.form.submit()"` što krši Anti-pattern #2 / AC9; rewrite kroz novi partial je explicit path izabran preko Decision D3 update).
- **When** uključen u `header.html` (AC3) na bilo kojoj strani
- **Then** `language_switcher_nav.html` renderuje 3 inline `<form>` elementa (po jedan per locale) sa `<button type="submit">` — `<form>` semantika čuva POST behavior za /i18n/setlang/ endpoint BEZ ikakvog JS-a (NO inline `onchange=` handler):
  ```django
  {% load i18n %}
  <ul class="coric-nav__language-switcher" role="list">
    {% get_available_languages as available_languages %}
    {% for lang_code, lang_name in available_languages %}
      <li>
        <form action="{% url 'set_language' %}" method="post" class="coric-language-switcher__form">
          {% csrf_token %}
          <input name="next" type="hidden" value="{{ request.path }}">
          <input name="language" type="hidden" value="{{ lang_code }}">
          <button type="submit"
                  class="coric-language-switcher__btn{% if LANGUAGE_CODE == lang_code %} coric-language-switcher__btn--current{% endif %}"
                  {% if LANGUAGE_CODE == lang_code %}aria-current="page"{% endif %}
                  aria-label="{% blocktranslate with language=lang_name %}Prebaci na {{ language }}{% endblocktranslate %}">
            {{ lang_code|upper }}
          </button>
        </form>
      </li>
    {% endfor %}
  </ul>
  ```
- **And** trenutni locale ima:
  - `aria-current="page"` (CRITICAL-2 RESOLVED: satisfijes AC4 jer novi partial podržava per-link atribut). **IMP-CASCADE-2 iter 2 rationale:** `aria-current="page"` (umesto `aria-current="true"`) je deliberate izbor po GOV.UK design system precedent-u — NVDA + JAWS screen reader-i najavljuju identično za oba ("current page"); `page` je semantic-richer i bolji za multi-page sajtove sa state-ful trenutnim URL-om.
  - CSS modifier klasu `.coric-language-switcher__btn--current` za vizuelni indikator (underline ili bold)
- **And** svaki button ima `aria-label="{% blocktranslate %}Prebaci na {{ language }}{% endblocktranslate %}"` (lokalizovan, ne hardkoderan engleski).
- **And** Story 1.4 `language_switcher.html` ostaje **netaknut** (regression guard sa Story 1.4 testovima) — taj partial je known CSP debt deferred to Story 1.9 (CI CSP hardening) ili Story 8.x (admin CSP rollout); Story 1.8 ga NE konzumira u svom novom header-u.
- **And** klasa `.coric-nav__language-switcher` ima `display: flex; gap: var(--spacing-scale-3); align-items: center; list-style: none; padding: 0; margin: 0;` u nav layout-u.
- **And** **Known minor cost (IMP-CASCADE-3 iter 2 + POLISH-9 iter 3):** 3 inline `<form>` × `{% csrf_token %}` znači 3 CSRF token render-a po stranici. Cost: ~450 bytes per page DOM (3× hidden input fields rendering same session-cookie-backed token; cookie sync is per-request not per-form, Django reuses token within RequestContext — `{% csrf_token %}` tag retrieves cached token sa context-a, NE generiše novi po formi). Dakle pravi payload trošak je DOM-only (~3 × 150 bytes hidden input markup) bez CSRF cookie size multiplication. Tradeoff prihvaćen — alternativa (1 deljeni form sa JS button selection) bi prebacila kompleksnost u JS i krši CSP-safe princip per Decision D3. Simplicity vs payload tradeoff favored simplicity.

**AC5 — Sticky nav shrink-on-scroll: `IntersectionObserver` pattern u `static/js/sticky-nav.js`, vanilla ES2020+, IIFE, no global window pollution, sa motion-reduce guard**

- **Given** `static/js/sticky-nav.js` kreiran i učitan kroz `<script defer>` u `base.html`
- **When** korisnik skroluje stranu nadole >100px (sentinel breakpoint — EXPERIENCE.md § Sticky nav linija 214) na desktop/tablet
- **Then** `.coric-nav` dobija klasu `.coric-nav--shrunk` i (preko `body.coric-nav-shrunk` klase — Decision D13):
  - `height: 60px` (per epic spec linija 505)
  - `box-shadow: var(--shadow-nav-shrunk)` (iz tokens.css — `0 2px 4px rgba(0, 0, 0, 0.1)`)
  - Logo CSS scaler smanjuje sliku na ~70% (npr. `max-height: 40px` u shrunk state; full state `max-height: 56px`)
  - Top header (`.coric-top-header`) collapsing kroz `height: 0; padding: 0; visibility: hidden;` (CRITICAL-11 fix + Decision D16 ažuriran: NE `display: none` koje izaziva CLS u Core Web Vitals; umesto toga `overflow: hidden` na .coric-top-header + transition na height + padding daju smooth collapse animation; element ostaje u flow-u ali zauzima 0px). **CRITICAL-CASCADE-3 (iter 2):** dodato `visibility: hidden` sa `transition-delay: 200ms` (flips POSLE height tranzicije) — uklanja `tel:` linkove + social linkove iz tab order + screen reader announcement u shrunk state (WCAG 2.4.7 Focus Visible + 2.4.11 Focus Not Obscured); `height: 0 + overflow: hidden` SAM ne uklanja descendants iz tab order (browseri to ne rade). `visibility: hidden` je CSS-only rešenje (alternativa Option B sa `inert` atributom kroz JS odbačena zbog dodatne JS kompleksnosti).
  - Tranzicija 200ms ease (per epic spec linija 506) + `visibility: hidden` flips u 0s sa `transition-delay: 200ms` u shrunk state-u (visibility ne treba da bude animirana; samo se prebacuje POSLE što se height završi)
- **And** kada korisnik skroluje nagore preko sentinel breakpoint-a, klasa `body.coric-nav-shrunk` se uklanja i nav + top header se vraćaju u full state sa istom 200ms ease tranzicijom.
- **And** **Sentinel placement (CRITICAL-5 + CRITICAL-6 fix):**
  - Sentinel MORA biti **direct child `<body>`** PRE include header.html — NIKAD unutar header.html ili unutar `.coric-top-header` (jer bi se sakrio sopstvenim efektom kad top-header collapses na `height: 0`).
  - Sentinel je `position: absolute; top: 100px;` — ovo zahteva da `<body>` ima `position: relative` (CRITICAL-6 fix); inače sentinel anchora na initial containing block (viewport) što daje neočekivano ponašanje sa scroll-om.
  - `static/css/components/sticky-nav.css` MORA dodati `body { position: relative; }` (mali globalni dodatak — dokumentovan u Dev Notes inline komentaru).
- **And** **`@media (prefers-reduced-motion: reduce)` override** (KRITIČNO — Story 1.8 ŠALJE motion u produkciju, dakle MORA da je guard-uje per Story 1.7 CRITICAL-3 lekcija):
  ```css
  @media (prefers-reduced-motion: reduce) {
    .coric-nav,
    .coric-nav__logo-img,
    .coric-top-header {
      transition: none;
    }
  }
  ```
- **And** JS pattern (predlog — vidi Dev Notes za pun primer):
  - **IIFE wrapper** (`(function () { ... })();`) — NE pollute `window` (NIKAD `window.stickyNav = ...`)
  - **`IntersectionObserver`** pattern: observer prati sentinel; kad sentinel izađe iz viewport-a, body dobija klasu.
  - **Defensive guards:** `if (!('IntersectionObserver' in window)) return;` (graceful degradation — bez observer-a nav ostaje u full state-u, sajt i dalje radi).
  - **`prefers-reduced-motion` check u JS-u takođe** (defense-in-depth):
    ```js
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    // observer i dalje prebacuje klasu (semantika), ali CSS `transition: none` brine o animaciji
    ```
  - **IMP-1 — Mobile resize/orientation listener:** mora postojati `mobileQuery.addEventListener('change', handler)` koji re-initializuje (`observer.observe`) ili teardown-uje (`observer.disconnect`) observer kad korisnik prelazi 768px breakpoint (npr. rotacija orientacije tablet-a). Bez ovog, korisnik koji startuje portrait <768px (no observer) → rotira u landscape ≥768px (treba observer) ostaje bez sticky behavior-a do refresh-a.
- **And** Mobile (<768px): sentinel pattern se NE primenjuje (Decision D4); na mobile-u nav ostaje uvek na vrhu sa hamburger toggle-om — vidi AC6.

**AC6 — Mobile (<768px) renderuje hamburger meni + kondenzovan top header (samo telefon ikona, klik proširi)**

- **Given** Bootstrap 5 navbar-expand-lg pattern (collapses ispod `lg` breakpoint = <992px po default-u; ali EXPERIENCE.md kaže <768px = mobile — Decision D5 dokumentuje overriding na `navbar-expand-md` da matchuje EXPERIENCE.md mobile breakpoint)
- **When** viewport <768px
- **Then** `.coric-nav` prikazuje:
  - Logo levo (centriran po EXPERIENCE.md linija 456: "Hamburger meni (top-left), logo je centriran, ikona pretrage top-right" — ovo zahteva CSS reorder, ne markup; Decision D6 dokumentuje)
  - Hamburger ikona (`<button class="navbar-toggler coric-nav__hamburger" type="button" data-bs-toggle="collapse" data-bs-target="#coricMainNav" aria-controls="coricMainNav" aria-expanded="false" aria-label="{% translate "Otvori meni" %}"><span class="navbar-toggler-icon" aria-hidden="true"></span></button>`)
  - Search ikona (kao na desktop-u, top-right)
  - Stavke menija u `<div class="collapse navbar-collapse" id="coricMainNav">` (Bootstrap collapse handlovan automatski)
  - Language switcher unutar collapse-a (ne u top bar-u na mobile)
- **And** `.coric-top-header` na mobile-u prikazuje SAMO ikonu telefona (servisa) kao kompresovan toggle:
  - `<button type="button" class="coric-top-header__mobile-toggle" aria-expanded="false" aria-controls="coricTopHeaderExpanded" aria-label="{% translate "Pokaži kontakt informacije" %}"><svg aria-hidden="true">...</svg></button>`
  - Klik proširi ostalu sadržinu (`<div id="coricTopHeaderExpanded" class="collapse">` ili custom CSS-only toggle koristeći `:has(input:checked)` — Decision D7 (preferiramo Bootstrap collapse zbog konzistentnosti sa hamburger toggle-om)).
- **And** hamburger toggle, mobile top-header toggle, search button SVI imaju `min-width: 44px; min-height: 44px;` (WCAG 2.5.5).
- **And** focus se vraća na trigger button kada se collapse zatvori (Bootstrap default ponašanje — ne treba custom JS).
- **And** klasa `.coric-nav__hamburger` koristi `var(--color-semantic-text-on-dark)` za boju ikone i `var(--color-semantic-focus-ring)` za focus outline.

**AC7 — Footer renderuje 4 kolone (Logo+slogan / Proizvodi / Najnovije vesti placeholder / Kontakt+Social) sa green-800 solid bg, copyright separator, Section Eyebrow heading-ovi**

- **Given** `templates/partials/footer.html` kreiran i uključen u `base.html`
- **When** GET na bilo koju stranu, viewport ≥768px
- **Then** rendered HTML sadrži `<footer class="coric-footer" role="contentinfo">` koji ima:
  - `background-color: var(--color-brand-green-800)` (per epic spec linija 504 "green-800 solid bg"; DESIGN.md konflikt resolved at linija 369 — JPG mockup ima prednost)
  - `color: var(--color-semantic-text-on-dark)` (white)
  - `padding: var(--spacing-scale-10) 0 var(--spacing-scale-5) 0` (64px gore, 24px dole)
- **And** footer ima dve sekcije:
  - **Footer-top** sa Bootstrap row + 4 col-md-3 kolone:
    - **Kolona 1 (Logo + slogan):** `<img>` sa light verzijom logo-a + `<p>` sa sloganom "Prijatelj koji razume zemlju!" (lokalizovano).
    - **Kolona 2 (Proizvodi):** Section Eyebrow heading "PROIZVODI" + `<ul class="coric-footer__menu">` sa 4-5 stavki: Traktori, Mehanizacija, Polovna mehanizacija, Rezervni delovi (placeholderi `href="#"` u Story 1.8 — Epic 2 zamenjuje pravim URL-ovima).
    - **Kolona 3 (Najnovije vesti placeholder):** Section Eyebrow heading "NAJNOVIJE VESTI" + `<ul class="coric-footer__news">` sa 3 hardkoderana Lorem Ipsum naslova obavijenih u `<!-- TODO: Story 5.4 zamenjuje dinamičkim {% for post in latest_posts %} loop-om -->` HTML komentar.
    - **Kolona 4 (Kontakt + Social):** Section Eyebrow heading "KONTAKT" + `<ul>` sa: telefon (kao `<a href="tel:...">`), email (`<a href="mailto:...">`), adresa, social linkovi (FB + IG ikone sa `aria-label`-ovima).
  - **Footer-bottom** (copyright separator):
    - `<hr class="coric-footer__separator">` sa CSS `border-top: 1px solid rgba(255, 255, 255, 0.2); margin: var(--spacing-scale-5) 0;` (tanka bela linija per EXPERIENCE.md linija 76)
    - `<p class="coric-footer__copyright text-center">© 2026 Ćorić Agrar. {% translate "Sva prava zadržana." %}</p>` — godina je hardkoderana 2026 u v1 (Decision D8 — alternativa je `{% now "Y" %}` za auto-update, ali EXPERIENCE.md i mockup specifikuju 2026; ostavljamo hardkoderano dok ne stigne Epic 8 SiteSettings).
- **And** **Section Eyebrow konzumira se** za svaki header kolone (KRITIČNO — to je Story 1.7 reuse pattern):
  ```django
  {% include "partials/section_eyebrow.html" with text="PROIZVODI" tag="h2" variant="on-dark" %}
  ```
  Variant `"on-dark"` (Story 1.7 kontrakt 2.4) osigurava da tekst koristi `var(--color-semantic-text-on-dark)` (belu) jer footer ima taman bg.
- **And** **Pill Button konzumira se** ako footer Kolona 4 ima CTA "POŠALJI UPIT" — opcionalno (vidi predlog u Dev Notes). Default: jednostavni linkovi bez Pill Button-a u footer-u.

**AC8 — Sve interaktivne komponente Story 1.8 zadovoljavaju WCAG 2.1 AA: keyboard navigation, focus management, ARIA atributi, kontrasti**

- **Given** sve komponente Story 1.8 implementirane (header, footer, sticky-nav.js)
- **When** korisnik koristi samo tastaturu (no mouse), screen reader, ili Windows High Contrast Mode
- **Then** sledeće moraju biti zadovoljeno:
  - Skip link iz Story 1.6 (`<a class="visually-hidden-focusable" href="#main-content">`) i dalje radi (regression — Story 1.8 ne menja taj element).
  - **Tab order:** logo → top header linkovi → nav stavke → Mehanizacija dropdown trigger → ... → search button → language switcher → footer linkovi (logičan flow).
  - **Focus indikatori:** svi linkovi i button-i imaju `:focus-visible` outline `2px solid var(--color-semantic-focus-ring)` sa `outline-offset: 2px` (per State Patterns u EXPERIENCE.md linija 234).
  - **ARIA atributi pravilno postavljeni:**
    - `<div class="coric-top-header" role="banner" aria-label="Kontakt informacije">` (CRITICAL-CASCADE-1 iter 2: top-header nosi `banner` landmark jer flatten Option A uklanja `<header>` wrapper koji bi po default-u bio banner; jedan `banner` landmark po stranici je preporučen po WAI-ARIA APG)
    - `<nav role="navigation" aria-label="Glavna navigacija">` na nav-u
    - `<nav role="navigation" aria-label="Footer navigacija">` na footer nav-u
    - `<footer role="contentinfo">` (HTML5 default ali eksplicitno za starije AT-ove)
    - Dropdown trigger: `aria-haspopup="true"`, `aria-expanded="false"`, `aria-controls="..."`
    - Hamburger trigger: `aria-expanded` koje Bootstrap update-uje automatski
    - Search trigger: `aria-label="{% translate "Otvori pretragu" %}"` + `aria-expanded` (ako otvara expand pattern)
    - Sentinel za sticky observer: `<div class="coric-sticky-sentinel" aria-hidden="true">` (dekorativan, screen reader ga preskače)
    - SVG ikone (telefon, FB, IG, hamburger lines, search): `aria-hidden="true"` na `<svg>` (ikona je dekorativna; meta je button/link sa svojim `aria-label`-om)
  - **Kontrasti:** white tekst na green-900 (top header) = ~12.6:1 ✓ AAA; white na green-800 (nav, footer) = ~11.1:1 ✓ AAA (per EXPERIENCE.md linija 290-292).
  - **Forced colors (WHCM)** override za nav linkove i button-e:
    ```css
    @media (forced-colors: active) {
      .coric-nav__link:focus-visible,
      .coric-nav__hamburger:focus-visible,
      .coric-nav__search-toggle:focus-visible,
      .coric-footer a:focus-visible {
        outline: 2px solid CanvasText;
      }
    }
    ```
  - **Reduced motion** override per AC5.
  - **`role="banner"` + `aria-label`** na top header bloku (CRITICAL-CASCADE-1 iter 2 update — promovirano iz `role="region"` u `role="banner"` da restaurira landmark koji je iter 1 flatten Option A izgubio):
    `<div class="coric-top-header" role="banner" aria-label="{% translate "Kontakt informacije" %}">`
- **And** Lighthouse a11y skor (kad se može pokrenuti — Epic 9 9.9) treba da bude ≥ 95 na bilo kojoj strani sa nav-om i footer-om.

**AC9 — Token discipline: NIJEDAN hardcoded hex/px (osim whitelist) u novim CSS fajlovima; sve preko `var(--...)` tokena**

- **Given** 3 nova CSS fajla (`header.css`, `footer.css`, `sticky-nav.css`)
- **When** grep ili AST-skenirana sva 3 fajla
- **Then** sledeće mora biti zadovoljeno:
  - **Zabranjeno:** hardcoded `#XXXXXX`, `#XXX`, `rgb()`, `hsl()` u CSS-u — sve preko `var(--color-*)`. Izuzeci: `transparent`, `inherit`, `currentColor`, `white` (CSS named keyword — dozvoljen ako se koristi za `border-color: white` u retkim slučajevima, npr. `border-top: 1px solid rgba(255, 255, 255, 0.2)` separator; Decision D9 dozvoljava `rgba(255, 255, 255, ...)` u footer separator-u SAMO ako opacity-based, jer tokens.css nema semi-transparent white token; alternativa je novi token `--color-overlay-white-20` koji NE uvodimo u Story 1.8 da bismo izbegli token sprawl).
  - **Whitelist hardcoded px (with-unit `\d+px`):**
    - `1px` (border/stroke)
    - `2px` (border/outline)
    - `44px` (WCAG touch target)
    - `60px` (sticky shrunk nav height — per epic spec linija 505)
    - `80px` (full nav height — Decision D1)
    - `40px`, `56px` (logo dimensions — Decision D10)
    - `100px` (scroll sentinel offset — per EXPERIENCE.md linija 214)
    - `120px` (combined initial chrome reservation: 80px nav + 40px top-header — IMP-9 documented constant)
  - **Whitelist hardcoded unitless magic numbers (CRITICAL-12 split):**
    - `1020` (z-index `.coric-nav` — Decision D11 ažuriran; iznad Bootstrap `.dropdown-menu` 1000 i `.popover` 1010, ispod `.modal` 1055; alternativa novi token `--z-index-nav` NE uvodimo da očuvamo Story 1.5 sealed token set)
  - Sve ostale spacing/font-size/border-radius vrednosti MORAJU biti `var(--spacing-*)`, `var(--typography-*)`, `var(--rounded-*)`, `var(--shadow-*)`.
  - **Cyrillic forbidden** — sve latinica (project-context.md § Critical Don't-Miss).
- **And** **NIJEDAN inline `style="..."`** u **3 NOVA HTML/Django partial-a** (`header.html`, `footer.html`, `language_switcher_nav.html`) — IMP-CASCADE-1 iter 2: file count eksplicitno 3 NOVA fajla. regression guard. KRITIČNO: grep scope je strogo na NOVE fajlove kreirane u Story 1.8; postojeći `language_switcher.html` (Story 1.4) je known CSP debt sa inline `onchange=` — to NE blokira Story 1.8 jer Story 1.8 ne konzumira taj partial.
- **And** **NIJEDAN inline `<script>` ili `onclick=...`, `onchange=...`, `onsubmit=...` atribut** u NOVIM fajlovima `header.html`, `footer.html`, `language_switcher_nav.html` (CSP-friendly — project-context.md § 6). Story 1.4 `language_switcher.html` postojeći `onchange=` je dokumentovan kao deferred debt (Story 1.9 CI CSP hardening ili Story 8.x admin CSP rollout).

**AC10 — Mobile hamburger toggle pokazuje correct focus management i collapse animation poštuje reduced-motion; Story 1.6 regression test invariant je migriran u skladu sa Decision D17 flatten**

- **CRITICAL-CASCADE-2 (iter 2) regression scope item:** Story 1.8 deliverable uključuje UPDATE Story 1.6 regression testa `tests/test_base_template.py::test_ac2_skip_link_first_child_of_body` jer postojeći test hard-asserts da `<header>` postoji u base.html — POSLE Task 5.1 (uklanja `<header>{% include "partials/language_switcher.html" %}</header>` blok) i pošto CRITICAL-CASCADE-1 flatten Option A NE re-uvija top-header u `<header>` wrapper, taj assert FAIL-uje. Story 1.8 mora explicitly update-ovati taj test (vidi Task 10a). Story 1.6 contract "skip link je prvi child body-ja" je očuvan — samo se invariant pattern menja iz "PRE `<header>` tag" u "PRE prvi chrome include (`{% include "partials/header.html" %}`)".



- **Given** mobile viewport (<768px) i hamburger button vidljiv
- **When** korisnik klikne hamburger button (touch ili keyboard Enter/Space)
- **Then** Bootstrap 5 collapse otvara `<div id="coricMainNav" class="collapse navbar-collapse">` sa svojim default animation timing-om (~350ms ease)
- **And** `aria-expanded` na hamburger button-u se updates iz `"false"` u `"true"` (Bootstrap automatski)
- **And** focus ostaje na hamburger button-u (default Bootstrap ponašanje — NE pokušavati custom focus trap u Story 1.8; Bootstrap collapse nije modal pa ne treba focus trap).
- **And** Esc tipka NE zatvara collapse (Bootstrap collapse nije modal — to je očekivano; alternativa bi bila custom JS kojeg NE uvodimo).
- **And** **`@media (prefers-reduced-motion: reduce)`** override poštuje Bootstrap collapse animation:
  ```css
  @media (prefers-reduced-motion: reduce) {
    .navbar-collapse.collapsing { transition: none; }
  }
  ```

## Tasks / Subtasks

### Task 1 — Setup direktorijuma i fajl-strukture (AC1)

- [x] 1.1: Kreirati `templates/partials/header.html` (prazan placeholder + komentar header).
- [x] 1.2: Kreirati `templates/partials/footer.html` (prazan placeholder + komentar header).
- [x] 1.3: Kreirati `static/css/components/header.css` (prazan + komentar header).
- [x] 1.4: Kreirati `static/css/components/footer.css` (prazan + komentar header).
- [x] 1.5: Kreirati `static/css/components/sticky-nav.css` (prazan + komentar header).
- [x] 1.6: Kreirati `static/js/` direktorijum (prvi put u projektu).
- [x] 1.7: Kreirati `static/js/sticky-nav.js` (prazan IIFE skelet + komentar header sa licencom).
- [x] 1.8: Dodati 3 `@import` linije u `static/css/main.css` (relative-with-dot sintaksa): `header.css`, `footer.css`, `sticky-nav.css` — postavljene **posle** Story 1.7 komponentnih import-ova (load order: tokens → bootstrap → main.css {1.7 imports → 1.8 imports}).
- [x] 1.9: Kreirati `static/img/` direktorijum (prvi put u projektu) — `mkdir -p static/img` (PowerShell: `New-Item -ItemType Directory -Force static/img`).
- [x] 1.10: Kopirati logo PNG-ove iz `docs/Dizajn/_HTML/img/` u `static/img/` (CRITICAL-8 fix):
  - `cp docs/Dizajn/_HTML/img/coric-agrar-logo-transp-200.png static/img/coric-agrar-logo-transp-200.png`
  - `cp docs/Dizajn/_HTML/img/coric-agrar-logo-transp-light-200.png static/img/coric-agrar-logo-transp-light-200.png`
  - PowerShell ekvivalent: `Copy-Item docs/Dizajn/_HTML/img/coric-agrar-logo-transp-200.png static/img/`
- [x] 1.11: Kreirati `templates/partials/language_switcher_nav.html` (CRITICAL-1 fix — nav-specifični language switcher; vidi AC4 za structure; postavlja se kao novi partial pored postojećeg Story 1.4 `language_switcher.html` koji ostaje netaknut).

### Task 2 — Header partial (top header + nav, AC2 + AC3 + AC4)

- [x] 2.1: U `header.html`, NE definisati outer `<header class="coric-site-header">` wrapper (CRITICAL-7 flatten Option A — `.coric-top-header` + `<nav class="coric-nav">` se renderuju kao DVA SIBLINGS na template root level). Template direktno počinje sa `{% load i18n %}{% load static %}` pa sledi `.coric-top-header` div, pa `<nav>`.
- [x] 2.2: Implementirati `<div class="coric-top-header" role="banner" aria-label="{% translate "Kontakt informacije" %}">` (CRITICAL-CASCADE-1 iter 2 — `role="banner"` restauriše ARIA landmark koji je iter 1 flatten izgubio kad je `<header class="coric-site-header">` wrapper uklonjen) sa:
  - Adresa kao `<p class="coric-top-header__address">` element (IMP-2: NE `<address>` — HTML5 `<address>` je za contact info nearest `<article>`/`<body>` ancestor, ne za company contact u top headeru)
  - Telefon prodaje sa `tel:` href i `aria-label`
  - Telefon servisa sa `tel:` href i `aria-label` — HARDKODERAN placeholder string `+381 XXX XXX XXX` u v1 (IMP-4 — Story 8.x SiteSettings model zameniti `{{ site_settings.service_phone }}`)
  - Social linkovi (FB + IG SVG ikone sa `aria-hidden="true"`, parent `<a>` sa `aria-label`)
- [x] 2.3: Implementirati `<nav class="coric-nav navbar navbar-expand-md" role="navigation" aria-label="{% translate "Glavna navigacija" %}">` sa Bootstrap 5 layout (CRITICAL-3: `navbar-expand-md` NE `navbar-expand-lg` — EXPERIENCE.md mandira <768px hamburger):
  - `<a class="navbar-brand coric-nav__logo" href="{% url 'core:home' %}">` sa logo `<img src="{% static 'img/coric-agrar-logo-transp-200.png' %}" alt="Ćorić Agrar">` (CRITICAL-9: `core:home` namespace; CRITICAL-8: logo asset provisionovan u Task 1.10)
  - Hamburger button `.navbar-toggler` sa Bootstrap collapse atributima (vidi AC6, AC10)
  - `<div class="collapse navbar-collapse" id="coricMainNav">` sa 6 `<li class="nav-item">` stavki, dropdown za Mehanizaciju sa `dropdown-menu`, search ikona, language switcher
- [x] 2.4: Implementirati Mehanizacija dropdown sa Bootstrap 5 markup pattern:
  ```html
  <li class="nav-item dropdown">
    <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown"
       aria-expanded="false" aria-haspopup="true" id="navbarDropdownMehanizacija">
      {% translate "Mehanizacija" %}
    </a>
    <ul class="dropdown-menu coric-nav__dropdown" aria-labelledby="navbarDropdownMehanizacija">
      <li><a class="dropdown-item" href="#">{% translate "Priključna mehanizacija (Jeegee)" %}</a></li>
      <!-- ... -->
    </ul>
  </li>
  ```
- [x] 2.5: Implementirati search ikonu kao `<button type="button" class="coric-nav__search-toggle" aria-label="{% translate "Otvori pretragu" %}">` — IMP-3 fix: BEZ `aria-expanded` atributa (button trenutno ne controlsuje expanded state; dodavanje je a11y misinformation; wiring stiže u Story 2.13). Bez funkcionalnosti, samo render.
- [x] 2.6: Uključiti language switcher kroz `{% include "partials/language_switcher_nav.html" %}` unutar `<li class="nav-item">` direktno (NOVI partial sa CRITICAL-1 fix — koristi `<form>` per locale, NE Story 1.4 `language_switcher.html`). `<ul class="coric-nav__language-switcher">` je već u nov partial-u.
- [x] 2.7: U `header.css`, stilovati `.coric-top-header` (bg green-900, padding, font-size, flex layout, `height: 40px` (CRITICAL-CASCADE-4 — eksplicitna numerička vrednost da `height: 0` tranzicija u shrunk state može da animira; CSS NE animira iz `auto` u length-vrednost), `overflow: hidden`, `visibility: visible` (CRITICAL-CASCADE-3 — parno sa `visibility: hidden` u shrunk state-u), `transition: height 200ms ease, padding 200ms ease, visibility 0s linear 0s`).
- [x] 2.8: U `header.css`, stilovati `.coric-nav` (bg green-800, height 80px, `position: sticky; top: 0; z-index: 1020;` (CRITICAL-12), transition).
- [x] 2.9: U `header.css`, stilovati `.coric-nav__link` (uppercase, tracking, min-height 44px, focus-visible outline).
- [x] 2.10: U `header.css`, stilovati `.coric-nav__dropdown` (background green-700 ili green-800, item hover state).
- [x] 2.11: U `header.css`, dodati `@media (forced-colors: active)` override za focus-visible (per AC8).
- [x] 2.12: U `header.css`, dodati Safari 14 baseline gap fix (IMP-5): `:focus, :focus-visible` dual selector sa `:focus { outline: none }` reset unutar `@supports (selector(:focus-visible))` block — pravi fallback za Safari <15.4 koji nema `:focus-visible` podršku:
  ```css
  /* Safari 14 fallback — keyboard focus dobija outline na :focus */
  .coric-nav__link:focus,
  .coric-nav__search-toggle:focus,
  .coric-nav__hamburger:focus {
    outline: 2px solid var(--color-semantic-focus-ring);
    outline-offset: 2px;
  }
  /* Modern: prefer :focus-visible (no outline on mouse click) */
  @supports selector(:focus-visible) {
    .coric-nav__link:focus,
    .coric-nav__search-toggle:focus,
    .coric-nav__hamburger:focus { outline: none; }
    .coric-nav__link:focus-visible,
    .coric-nav__search-toggle:focus-visible,
    .coric-nav__hamburger:focus-visible {
      outline: 2px solid var(--color-semantic-focus-ring);
      outline-offset: 2px;
    }
  }
  ```
  - **Napomena:** project minimum bumped to Safari 14.1+ per POLISH-1 (iter 3); ovaj fallback i dalje važi za 14.1, 14.2, 15.0-15.3 koji nemaju :focus-visible until 15.4.

### Task 3 — Sticky nav JS modul (AC5)

- [x] 3.1: U `static/js/sticky-nav.js`, postaviti IIFE wrapper (`(function () { 'use strict'; ... })();`).
- [x] 3.2: Defensive guards: `if (!('IntersectionObserver' in window)) return;` na vrhu.
- [x] 3.3: Selektovati `document.querySelector('.coric-nav')` i `document.querySelector('.coric-sticky-sentinel')`. Ako bilo koji ne postoji, `return;`.
- [x] 3.4: Kreirati `IntersectionObserver` koji prati sentinel i prebacuje klasu na `<body>` (Decision D13):
  ```js
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      const isShrunk = !entry.isIntersecting;
      nav.classList.toggle('coric-nav--shrunk', isShrunk);
      document.body.classList.toggle('coric-nav-shrunk', isShrunk);
    });
  }, { rootMargin: '0px', threshold: 0 });
  observer.observe(sentinel);
  ```
- [x] 3.5: Sentinel postavljen u **`base.html`** (NE u header.html — CRITICAL-5 fix) kao direct child `<body>` PRE `{% include "partials/header.html" %}`: `<div class="coric-sticky-sentinel" aria-hidden="true"></div>` — NO inline style (Decision D12 — CSS klasa). **IMP-CASCADE-12 iter 2:** `tabindex="-1"` UKLONJEN — `<div>` je po default-u NE-focusable; `tabindex="-1"` je suvišan + cleaner aligned sa Anti-pattern #12 (bez stale focus-management hint-a). `aria-hidden="true"` je dovoljan signal za AT-ove. Sentinel MORA biti VAN top-header-a inače observer izgubi signal kad top-header dobije `height: 0` u shrunk state.
- [x] 3.6: U `sticky-nav.css`, definisati:
  - `body { position: relative; }` (CRITICAL-6 fix — sentinel je `position: absolute; top: 100px;` i mora imati `<body>` kao positioned containing block, inače anchora na initial containing block / viewport sa neočekivanim ponašanjem; KRITIČNO: ovaj `body { position: relative }` je mali globalni dodatak — dokumentovan u inline komentaru: "Story 1.8 sticky-nav: enables IntersectionObserver sentinel positioning")
  - `.coric-sticky-sentinel { position: absolute; top: 100px; height: 1px; width: 1px; pointer-events: none; }` (per EXPERIENCE.md linija 214 "scroll >100px")
  - `.coric-nav--shrunk { height: 60px; box-shadow: var(--shadow-nav-shrunk); }`
  - `.coric-nav--shrunk .coric-nav__logo-img { max-height: 40px; }` (shrunk logo)
  - `.coric-nav__logo-img { max-height: 56px; transition: max-height 200ms ease; }` (full state logo)
  - `body.coric-nav-shrunk .coric-top-header { height: 0; padding-top: 0; padding-bottom: 0; visibility: hidden; transition: height 200ms ease, padding 200ms ease, visibility 0s linear 200ms; }` (CRITICAL-11 + Decision D16 fix: NE `display: none` koje izaziva CLS; koristi `height: 0; padding: 0` na top-header koji ima `overflow: hidden` set u header.css; transition na height + padding daje smooth collapse animation. **CRITICAL-CASCADE-3 (iter 2):** `visibility: hidden` sa `transition-delay: 200ms` flips visibility POSLE height transition completes — uklanja `tel:` linkove + social linkove iz tab order + screen reader announcement u shrunk state (WCAG 2.4.7 + 2.4.11)).
- [x] 3.7: U `sticky-nav.css`, dodati `@media (prefers-reduced-motion: reduce)` override (per AC5).
- [x] 3.8: Anti-pattern provera (KRITIČNO): nema `window.<anything> = ...`, nema `console.log`, nema `addEventListener` bez cleanup-a (IntersectionObserver + matchMedia listener žive za ceo lifecycle strane — to je OK), nema jQuery.
- [x] 3.9: IMP-1 — Dodati mobile/orientation resize listener u sticky-nav.js (re-init/teardown observer kad korisnik prelazi 768px breakpoint):
  ```js
  const mobileQuery = window.matchMedia('(max-width: 767px)');
  function syncObserver() {
    if (mobileQuery.matches) {
      observer.disconnect();
      nav.classList.remove('coric-nav--shrunk');
      document.body.classList.remove('coric-nav-shrunk');
    } else {
      observer.observe(sentinel);
    }
  }
  syncObserver(); // initial state
  mobileQuery.addEventListener('change', syncObserver);
  ```

### Task 3a — Language switcher nav partial (CRITICAL-1 fix, AC4)

- [x] 3a.1: U `templates/partials/language_switcher_nav.html`, implementirati strukturu sa 3 `<form>` per locale (vidi AC4 za pun template):
  - `{% get_available_languages as available_languages %}` (i18n template tag — emituje listu `(code, name)` parova)
  - `{% for lang_code, lang_name in available_languages %}` loop renderuje `<form action="{% url 'set_language' %}" method="post">` sa hidden `next` + hidden `language` input + `<button type="submit">`.
  - `aria-current="page"` SAMO na buttonu trenutnog locale-a (`{% if LANGUAGE_CODE == lang_code %}`).
  - `aria-label="{% blocktranslate with language=lang_name %}Prebaci na {{ language }}{% endblocktranslate %}"` (lokalizovan).
  - CSS modifier klasa `coric-language-switcher__btn--current` na trenutnom locale-u za vizuelni indikator.
- [x] 3a.2: U `header.css`, stilovati `.coric-nav__language-switcher` (display: flex, gap, align-items, list-style: none, padding: 0, margin: 0).
- [x] 3a.3: U `header.css`, stilovati `.coric-language-switcher__btn` (background transparent, color inherit, border 0, padding token, min-height 44px, font-weight bold, text-transform uppercase) + `.coric-language-switcher__btn--current` (underline ili font-weight diferencijacija — vizuelno označava trenutni locale).
- [x] 3a.4: Anti-pattern provera: nema inline `onchange=`, `onclick=`, `onsubmit=`, `style=` u `language_switcher_nav.html` (regression sa AC9 scope na NEW files).

### Task 4 — Footer partial (AC7)

- [x] 4.1: U `footer.html`, definisati `<footer class="coric-footer" role="contentinfo">`.
- [x] 4.2: Dodati footer-top sekciju sa Bootstrap row + 4 col-md-3 kolone.
- [x] 4.3: **Kolona 1 (Logo+slogan):** `<a href="{% url 'core:home' %}" class="coric-footer__logo-link">` wrap oko `<img>` (BONUS-2 iter 3 — parity sa header logo-om koji je već wrapped u home link; konzistentnost UX expectation-a), `<p>` sa sloganom kroz `{% translate "Prijatelj koji razume zemlju!" %}`. Logo link ima `aria-label="{% translate "Početna" %}"` da screen reader ne najavi samo "Ćorić Agrar" (img alt) bez context-a da je link.
- [x] 4.4: **Kolona 2 (Proizvodi):** Section Eyebrow heading kroz `{% include "partials/section_eyebrow.html" with text="PROIZVODI" tag="h2" variant="on-dark" %}` + `<ul class="coric-footer__menu">` sa 4-5 stavki.
- [x] 4.5: **Kolona 3 (Najnovije vesti):** Section Eyebrow "NAJNOVIJE VESTI" + `<ul class="coric-footer__news">` sa 3 hardkoderana Lorem Ipsum naslova OBAVIJENA u HTML komentar:
  ```django
  {# TODO: Story 5.4 zameniće dinamičkim {% for post in latest_posts|slice:":3" %} ... {% endfor %} #}
  <ul class="coric-footer__news">
    <li><a href="#">Lorem ipsum dolor sit amet 1</a></li>
    <li><a href="#">Lorem ipsum dolor sit amet 2</a></li>
    <li><a href="#">Lorem ipsum dolor sit amet 3</a></li>
  </ul>
  ```
- [x] 4.6: **Kolona 4 (Kontakt+Social):** Section Eyebrow "KONTAKT" + `<ul>` sa: `<a href="tel:...">`, `<a href="mailto:...">`, adresa kao `<address>`, social linkovi (FB + IG SVG ikone sa `aria-label`). **BONUS-3 iter 3 — CSS reset za `<address>` unutar `<li>`:** Browser default `<address>` ima `display: block; font-style: italic; margin: 0 0 1em 0;` što razbija inline footer list layout (address bi prešao u novi red sa italic font-om i extra margin-om). Dodati u `footer.css` reset: `.coric-footer__contact address { display: inline; margin: 0; font-style: normal; }` da address renderuje inline u `<li>` flow-u sa drugim kontakt linkovima.
- [x] 4.7: Dodati footer-bottom sekciju sa `<hr class="coric-footer__separator">` + `<p class="coric-footer__copyright text-center">© 2026 Ćorić Agrar. {% translate "Sva prava zadržana." %}</p>`.
- [x] 4.8: U `footer.css`, stilovati `.coric-footer` (bg green-800, color white, padding).
- [x] 4.9: U `footer.css`, stilovati `.coric-footer__menu` i `.coric-footer__news` (`list-style: none`, padding 0, link colors, hover states).
- [x] 4.10: U `footer.css`, stilovati `.coric-footer__separator` (1px solid rgba(255,255,255,0.2)) i `.coric-footer__copyright` (font-size caption, opacity).
- [x] 4.11: U `footer.css`, dodati `@media (max-width: 767px)` override za stacked layout (single column) — Bootstrap col-md-3 već radi ovo automatski; CSS samo override-uje spacing.

### Task 5 — Base template wiring (AC1)

- [x] 5.1: U `templates/base.html`, UKLONITI postojeći `<header>{% include "partials/language_switcher.html" %}</header>` blok (language switcher se sada renderuje INTERNO u header.html kroz `language_switcher_nav.html` include).
- [x] 5.2: DODATI sentinel u **`base.html`** kao **direct child `<body>`** PRE `{% include "partials/header.html" %}` (CRITICAL-5 fix — sentinel MORA biti VAN top-header-a inače observer izgubi signal kad top-header collapses na `height: 0`):
  ```django
  <body>
    <a class="visually-hidden-focusable" href="#main-content">{% translate "Preskoči na sadržaj" %}</a>
    <div class="coric-sticky-sentinel" aria-hidden="true"></div>
    {% include "partials/header.html" %}
    <main id="main-content" tabindex="-1">...</main>
    ...
  </body>
  ```
- [x] 5.3: DODATI `{% include "partials/footer.html" %}` u `base.html` POSLE `</main>` i PRE `{% aria_live %}` (CRITICAL-4 kanonski redosled: `</main>` → `<footer>` → `{% aria_live %}` → `<noscript>` → scripts).
- [x] 5.4: DODATI `<script src="{% static 'js/sticky-nav.js' %}" defer></script>` u site-wide scripts blok POSLE `{% bootstrap_javascript %}` (CRITICAL-10 fix — empirijska napomena: `{% bootstrap_javascript %}` je SYNC u base.html line 34 komentaru jasno piše "django-bootstrap5 NE emit-uje defer"; bootstrap.sync execute-uje TOKOM parse-a; DCL fires; htmx + sticky-nav defer execute-uju POSLE DCL. Order: bootstrap.sync executes during parse → DCL fires → htmx + sticky-nav defer execute. Ovo je acceptable jer sticky-nav.js zahteva DOM elemente koji postoje by DCL).
- [x] 5.5: Regression check: skip link, aria_live, noscript blok, htmx defer, bootstrap_css/javascript redosled svi ostaju netaknuti.

### Task 6 — Mobile responzivnost (AC6, AC10)

- [x] 6.1: U `header.css`, dodati `@media (max-width: 767px)` blok sa:
  - `.coric-top-header__mobile-toggle { display: block; min-width: 44px; min-height: 44px; }`
  - `.coric-top-header__expanded { /* Bootstrap collapse zatvoreno default */ }`
  - **POLISH-2 iter 3 napomena:** `.coric-top-header { height: auto }` mobile override JE U `sticky-nav.css` (single-sourced canonical lokacija — sticky-nav.css owns shrunk-state behavior + mobile bypass per D4). NE duplicirati ovde u `header.css`. Inline komentar dodati: `/* Mobile override managed by sticky-nav.css */`.
- [x] 6.2: U `header.html`, dodati mobile-only toggle button i collapse div za top header:
  ```html
  <button type="button" class="coric-top-header__mobile-toggle d-md-none" data-bs-toggle="collapse"
          data-bs-target="#coricTopHeaderExpanded" aria-expanded="false" aria-controls="coricTopHeaderExpanded"
          aria-label="{% translate "Pokaži kontakt informacije" %}">
    <svg aria-hidden="true">...</svg>
  </button>
  <div id="coricTopHeaderExpanded" class="collapse d-md-block">
    <!-- adresa, telefoni, social -->
  </div>
  ```
- [x] 6.3: U `header.css`, dodati `@media (prefers-reduced-motion: reduce) { .navbar-collapse.collapsing, .coric-top-header__expanded.collapsing { transition: none; } }`.
- [x] 6.4: Verifikovati da hamburger button ima `min-width: 44px; min-height: 44px;` (Bootstrap default je oko 30px — Story 1.8 mora override-ovati).
- [x] 6.5: Mobile logo: po EXPERIENCE.md linija 456 "logo je centriran" — CSS reorder kroz `flexbox order` ili `margin: 0 auto` na navbar-brand u mobile breakpoint-u.

### Task 7 — A11y polish (AC8)

- [x] 7.1: Verifikovati sve interaktivne elemente imaju `:focus-visible` outline `2px solid var(--color-semantic-focus-ring)` sa `outline-offset: 2px` u `header.css` i `footer.css`.
- [x] 7.2: Dodati `@media (forced-colors: active)` override za focus-visible u `header.css`, `footer.css`, `sticky-nav.css`.
- [x] 7.3: Verifikovati svi SVG dekorativni elementi imaju `aria-hidden="true"`.
- [x] 7.4: Verifikovati svi `aria-label`-ovi su lokalizovani kroz `{% translate %}` ili `{% blocktranslate %}`.
- [x] 7.5: Verifikovati Tab order pasuje EXPERIENCE.md linija 295-298 (manual test sa keyboard-only navigation).

### Task 8 — Anti-pattern provera (AC9)

- [x] 8.1: Grep skenirati 3 nova CSS fajla na hardcoded `#XXXXXX`, `#XXX`, `rgb(...)` van whitelist-a; sve se mora menjati u `var(--...)`.
- [x] 8.2: Grep skenirati 3 nova CSS fajla na hardcoded px van whitelist-a `[1, 2, 44, 60, 80, 40, 56, 100, 120]`; sve ostale → `var(--spacing-*)`. IMP-CASCADE-7 iter 2: uklonjeno `1000` iz px enumeration-a — `1000` je bila stara z-index vrednost, sada je `1020` (Decision D11 ažuriran u CRITICAL-12); `1020` je unitless magic number (NE px) u AC9 split whitelist-u.
- [x] 8.3: Grep skenirati 3 nova HTML/Django partial-a (header.html, footer.html, language_switcher_nav.html) na `style="..."` (forbidden) i `onclick="..."`/`on*=`/`<script>` (forbidden) — IMP-CASCADE-1 iter 2: file count ispravljen sa 2 na 3 (uključuje language_switcher_nav.html koji je sam NOV partial Story 1.8).
- [x] 8.4: Grep skenirati `sticky-nav.js` na `window.<x> = ` (forbidden — global pollution), `$.` (forbidden — jQuery), `console.log` (forbidden u production).
- [x] 8.5: Grep skenirati sve nove fajlove na cyrillic karaktere (forbidden — `[Ѐ-ӿ]`).

### Task 9 — Pytest skelet (testabilno u Story 1.8)

- [x] 9.1: Kreirati `tests/test_header_footer.py` ili dodati u postojeći `tests/test_visual_components.py` (Decision D14 — preferiramo novi fajl `tests/test_navigation_chrome.py` zbog koheznosti scope-a).
- [x] 9.2: Test: `test_header_partial_renders_top_header_with_address_and_phone` (HTML rendering test).
- [x] 9.3: Test: `test_header_partial_includes_language_switcher` (verifikuje `{% include %}` reuse).
- [x] 9.4: Test: `test_header_partial_conditional_pill_button_opt_in` (IMP-6 fix: original test je bio self-contradictory jer D15 default je "not used"; ovo je opt-in fixture sa `@pytest.mark.skipif(not USE_PILL_BUTTON_IN_NAV, reason="D15 default: pill button not used in nav")` skip marker — Dev koji izabere D15 alternativu uključuje fixture; default je skipped i ne fails CI).
- [x] 9.4a: Test: `test_sticky_nav_js_toggles_body_class` (IMP-10: verifikuje Decision D13 wiring — grep `sticky-nav.js` za `document.body.classList.toggle('coric-nav-shrunk'` substring).
- [x] 9.4b: Test: `test_logo_assets_present` (CRITICAL-8: verifikuje da `static/img/coric-agrar-logo-transp-200.png` i `static/img/coric-agrar-logo-transp-light-200.png` postoje na disku posle Task 1.10 provisioning-a).
- [x] 9.4c: Test: `test_language_switcher_nav_partial_renders_aria_current` (CRITICAL-1/2: verifikuje da rendered HTML iz `language_switcher_nav.html` ima `aria-current="page"` na trenutnom locale-u i NEMA inline `onchange=`).
- [x] 9.4d: Test: `test_base_html_url_uses_core_home_namespace` (CRITICAL-9: grep za `{% url 'core:home' %}` u header.html; grep negative za `{% url 'home' %}` bez namespace-a).
- [x] 9.4e: Test: `test_nav_z_index_is_1020` (CRITICAL-12: grep `header.css` za `z-index: 1020`; grep negative za `z-index: 1000` na `.coric-nav`).
- [x] 9.4f: Test: `test_sticky_nav_css_has_body_position_relative` (CRITICAL-6: grep za `body { position: relative;` ili equivalent u sticky-nav.css).
- [x] 9.4g: Test: `test_sticky_nav_js_has_matchmedia_change_listener` (IMP-1: grep za `mobileQuery.addEventListener('change'` u sticky-nav.js).
- [x] 9.4h: Test: `test_top_header_uses_p_not_address` (IMP-2: grep `header.html` za `coric-top-header__address` klase + `<p` tag; grep negative za `<address class="coric-top-header__address">`).
- [x] 9.5: Test: `test_footer_partial_renders_4_columns_with_section_eyebrow` (verifikuje Story 1.7 reuse u footer-u + 4 col-md-3).
- [x] 9.6: Test: `test_footer_partial_renders_lorem_ipsum_placeholder_for_news` (verifikuje 3 hardkoderan placeholder + komentar TODO).
- [x] 9.7: Test: `test_footer_partial_renders_copyright_2026` (verifikuje hardkoderan 2026 string).
- [x] 9.8: Test: `test_sticky_nav_js_file_exists_and_uses_intersection_observer` (file existence + grep za `IntersectionObserver` substring).
- [x] 9.9: Test: `test_sticky_nav_js_uses_iife_pattern` (grep za `(function ()` ili `(() =>`).
- [x] 9.10: Test: `test_sticky_nav_js_no_window_pollution` (grep negative za `window.\w+ = `).
- [x] 9.11: Test: `test_sticky_nav_css_has_prefers_reduced_motion_override` (grep za `@media (prefers-reduced-motion: reduce)`).
- [x] 9.11a: Test: `test_sticky_nav_css_reduced_motion_disables_visibility_transition` (POLISH-3 iter 3): grep `sticky-nav.css` za `body.coric-nav-shrunk .coric-top-header { transition: none }` (ili equivalent contained rule) UNUTAR `@media (prefers-reduced-motion: reduce)` blok-a. Razlog: u reduced-motion mode-u, visibility takođe mora instant-flip bez 200ms delay-a (jer nema height transition da se sačeka); bez ovog WCAG-safe tab order pravilo postaje WCAG-non-compliant u reduced-motion kontekstu. Verifikacija prati CRITICAL-CASCADE-3 sticky-nav.css skeleton koji već sadrži ovaj rule unutar reduced-motion override block-a.
- [x] 9.12: Test: `test_header_css_no_hardcoded_hex` (grep negative za `#[0-9a-fA-F]{3,6}` van whitelist-a).
- [x] 9.13: Test: `test_footer_css_no_hardcoded_hex` (isto).
- [x] 9.14: Test: `test_base_html_includes_header_and_footer_and_sticky_nav_script` (regression test).
- [x] 9.15: Test: `test_no_cyrillic_in_new_files` (regression — vidi Story 1.7 testovi za pattern).
- [x] 9.16: Test: `test_main_css_imports_3_new_components` (regression — verifikuje 3 nova @import).

### Task 10 — Manual verification & sign-off

- [x] 10.1: `uv run pytest tests/test_navigation_chrome.py -v --tb=short` mora proći (svi novi testovi GREEN).
- [x] 10.2: `uv run pytest tests/` (svi prethodni testovi — Story 1.4-1.7 — moraju proći jer ima regression risk u base.html modifikaciji).
- [x] 10.3: `uv run python manage.py runserver` + browser smoke test:
  - Desktop (≥768px): top header pokazuje adresu/telefon/social; nav je sticky; scroll >100px kondenzuje nav; scroll <100px vraća full.
  - Mobile (<768px): hamburger toggle radi; top header pokazuje samo telefon toggle; klik proširi.
  - Tastatura-only: Tab kroz sve interaktivne elemente; focus-visible outline svuda; Enter na hamburger otvara; Esc NE zatvara (Bootstrap collapse limit).
  - Language switcher: klik na opciju → preusmerenje na isti path u novom locale-u.
  - **POLISH-4 iter 3 — AT landmark smoke test:** NVDA D-key (D / Shift+D) ili JAWS `;` / `R` shortcut za landmark navigation — verifikovati da rendered strana sadrži TAČNO: 1× banner + 1× navigation + 1× main + 1× contentinfo landmark; NEMA duplikat landmarka (npr. nema dva `banner`-a). Banner landmark **disappears** iz landmark liste kad korisnik scroll-uje preko 100px sentinel-a (top-header dobija `visibility: hidden`, što je dokumentovani CRITICAL-CASCADE-3 tradeoff — landmark menu re-includes banner pri scroll-up preko sentinel-a). Dokumentovati u Manual Sign-Off Log da je banner-disappear-during-shrunk acceptable per Decision D17 + CRITICAL-CASCADE-3 fix.
- [x] 10.4: `prefers-reduced-motion: reduce` u OS settings → sticky nav transition postaje trenutan; hamburger collapse postaje trenutan (no fade).
- [x] 10.5: Update sprint-status.yaml: `1-8-sticky-nav-top-header-footer-language-switcher-partial` postavlja se na `review` (u Dev Notes — Dev će ovo uraditi po završetku).

### Task 10a — Story 1.6 regression test update (CRITICAL-CASCADE-2 iter 2)

**Scope rationale:** Story 1.6 regression test `tests/test_base_template.py::test_ac2_skip_link_first_child_of_body` (linije 373-388) trenutno HARD-asserts da `<header>` postoji u base.html kroz `src.find("<header>") != -1` (linija 378, 383). Story 1.8 Task 5.1 uklanja postojeći `<header>{% include "partials/language_switcher.html" %}</header>` blok iz base.html, A CRITICAL-CASCADE-1 iter 2 odlučno NE re-uvija novi top-header u `<header>` wrapper (umesto toga koristi `role="banner"` na `.coric-top-header` div-u per Decision D17 + flatten Option A). To znači da postojeći test FALI POSLE Story 1.8 implementation-a → moramo ga UPDATE-ovati kao deo Story 1.8 scope-a.

**Odluka:** Story 1.8 deliberately removes the bare `<header>` wrapper in favor of `role="banner"` on `.coric-top-header` (Decision D17 + Story 1.8 CRITICAL-CASCADE-1). Story 1.6 regression test is updated within Story 1.8 scope.

- [x] 10a.1: Update `tests/test_base_template.py::test_ac2_skip_link_first_child_of_body` (oko linije 373-388):
  - **Stari (failing) assert pattern (linije 378, 383, 384):**
    ```python
    header_idx = src.find("<header>")
    assert header_idx != -1, "base.html ne sadrži <header> tag (regression)."
    assert body_open_idx < skip_link_idx < header_idx, ...
    ```
  - **Novi (Story 1.8 align) assert pattern (POLISH-7 iter 3 — regex umesto literal `.find()`):**
    ```python
    import re
    # Story 1.8: <header> wrapper uklonjen u korist role="banner" na .coric-top-header div-u
    # (per Story 1.8 CRITICAL-CASCADE-1 + Decision D17 flatten Option A).
    # Canonical landmark region u base.html je sada `.coric-top-header` include preko header.html partial-a.
    #
    # POLISH-7 iter 3: regex umesto literal `src.find('{% include "partials/header.html" %}')` — resilient
    # na whitespace varijacije ({% include%}, {%  include  %}, jednostruki vs dvostruki navodnici,
    # eventualni linije-breaks unutar tag-a). Brittleness eliminisana — test ne fail-uje na sitne
    # template formatting promene koje su semantički ekvivalentne.
    header_include_match = re.search(
        r'\{%\s*include\s*[\'"]partials/header\.html[\'"]\s*%\}',
        src
    )
    assert header_include_match is not None, (
        "base.html ne uključuje header partial (regression — Story 1.8 zahteva da je "
        "`{% include \"partials/header.html\" %}` u base.html; regex prihvata whitespace + jednostruke/dvostruke navodnike)."
    )
    coric_top_header_include_idx = header_include_match.start()
    assert body_open_idx < skip_link_idx < coric_top_header_include_idx, (
        f"Skip link nije prvi element body-ja. "
        f"body_open={body_open_idx}, skip_link={skip_link_idx}, header_include={coric_top_header_include_idx}. "
        f"AC2 (Story 1.6 regression updated u Story 1.8 scope): skip link mora biti TAČNO PRVI fokusabilan element (PRE chrome includes)."
    )
    ```
- [x] 10a.2: Dodati docstring komentar u updated test koji referencira Story 1.8 CRITICAL-CASCADE-2 + Decision D17 + canonical landmark approach (banner landmark migriran iz `<header>` wrapper-a na `.coric-top-header` div).
- [x] 10a.3: Verify update kroz `uv run pytest tests/test_base_template.py::test_ac2_skip_link_first_child_of_body -v` posle base.html modifikacije u Task 5.1.
- [x] 10a.4: Story 1.6 regression test update je DELIVERABLE Story 1.8 (deo AC10/Testing scope — ne čeka se Story 1.6 revisit; Story 1.6 contract o "skip link prvi element body-ja" je očuvan, samo se invariant pattern menja iz "PRE `<header>` tag" u "PRE prvi chrome include").

## Dev Notes

### Kontekst story-ja

Story 1.8 je **kapital chrome komponenta projekta** — svaka strana koja nasleđuje `base.html` (a to su SVE javne strane od Epic 2 do Epic 7 + sve admin strane od Epic 8) konzumira `header.html` i `footer.html`. Drugim rečima: bug u Story 1.8 = bug na 100% strana projekta.

Story 1.8 je takođe **prvi konzument `static/js/`** u projektu. Project-context.md § 333-339 propisuje:
- Vanilla JS preferred — Alpine.js opciono, NIKAD jQuery
- No build pipeline — JS se servira direktno iz `static/js/`
- Module naming: `kebab-case.js` → `sticky-nav.js`, `lightbox-init.js`, `statistic-counter.js`

Ovo postavlja precedente za sve buduće JS module (npr. `count-up.js` u Epic 3, `lightbox-init.js` u Epic 2, `htmx-form-handlers.js` u Epic 4). Story 1.8 mora postaviti idiomatske pattern-e (IIFE, defensive guards, no global pollution, motion-reduce respect) koje budući autori kopiraju.

### Tech stack — Template + CSS + JS specifics

- **Django 5.2 LTS template language** sa `{% load i18n %}`, `{% load static %}`, `{% load django_bootstrap5 %}` (već uključeni u base.html).
- **Bootstrap 5.3** — dropdown + collapse + navbar koriste se preko `data-bs-*` atributa (NE custom JS).
- **HTMX 1.9+** — NIJE potreban u Story 1.8 (search funkcionalnost je deferred do Story 2.13; collapse je Bootstrap-handled).
- **Vanilla JS ES2020+** — `IntersectionObserver`, `MutationObserver`, `matchMedia`, `URLSearchParams` su svi globalno dostupni u modernim browser-ima (project minimum: Chrome 90+, Firefox 88+, **Safari 14.1+** per project-context.md — POLISH-1 iter 3: bumped sa Safari 14+ na **Safari 14.1+** jer Safari 14.0 ima poznat WebKit bug sa `visibility` tranzicijom sa nenultim `transition-delay` koji blokira CRITICAL-CASCADE-3 pattern; bug fixed u WebKit 14.1 release. Empirijski signal: Story 1.8 oslanja se na `transition: visibility 0s linear 200ms` pattern u shrunk state-u; Safari 14.0 ignores delay i flips visibility u 0s što razbija WCAG 2.4.7/2.4.11 tab order kontrakt. Browser support matrix Story 1.8 sad eksplicitno isključuje Safari 14.0 — fallback je gracious-degrade: korisnici na Safari 14.0 vide instant visibility flip bez animation polish, ali tab order ostaje korektan).
- **No build pipeline:** JS se servira preko Whitenoise iz `static/js/` direktno. Bez minifikacije u dev; production whitenoise compress preko `CompressedManifestStaticFilesStorage` (Story 1.6).

### Decisions log (Dev će ažurirati po izboru)

| # | Pitanje | Default izbor | Alternativa | Rationale |
|---|---|---|---|---|
| D1 | Nav full-state height | 80px | 72px | 80px = okrugla vrednost, ostavlja prostor za logo (56px max-height) + 12px vertical padding × 2 |
| D2 | Mehanizacija dropdown implementacija | Bootstrap 5 dropdown (`data-bs-toggle`) | Custom JS | Bootstrap ima full a11y handling već; custom JS bi duplikovao posao |
| D3 | Language switcher rewrite za nav | DA — kreiraj NOVI `language_switcher_nav.html` sa `<form>`-per-locale + `aria-current="page"` (CRITICAL-1 fix Option A) | NE — reuse Story 1.4 partial netaknut | Story 1.4 partial ima inline `onchange="this.form.submit()"` koji krši AC9 / Anti-pattern #2 (no inline handler in NEW files Story 1.8 konzumira). Novi partial koristi `<form>` per locale + `<button type="submit">` — no JS, CSP-friendly, satisfijes AC4 `aria-current="page"`. Story 1.4 partial ostaje netaknut kao known CSP debt deferred to Story 1.9/8.x |
| D4 | Mobile sticky shrink-on-scroll | NE — sticky se ne primenjuje <768px | DA — sentinel pattern radi i na mobile-u | EXPERIENCE.md ne specifikuje mobile sticky; mobile nav je već kompaktan (hamburger samo); sentinel = unnecessary complexity |
| D5 | Mobile breakpoint za hamburger | 768px (Bootstrap `md`) | 992px (Bootstrap `lg` default) | EXPERIENCE.md linija 26 specifikuje <768px = mobile; mora se override-ovati `navbar-expand-md` umesto default `navbar-expand-lg` |
| D6 | Mobile logo pozicija | Levo (sa hamburger desno) | Centriran (kako EXPERIENCE.md linija 456 kaže) | EXPERIENCE.md kaže centriran — implementiraj kroz CSS `flexbox order` ili `position: absolute; left: 50%; transform: translateX(-50%);` |
| D7 | Mobile top-header expand pattern | Bootstrap collapse | Custom CSS `:has(input:checked)` toggle | Bootstrap collapse je konzistentan sa hamburger pattern-om + ima a11y built-in |
| D8 | Copyright godina | Hardkoderano "2026" | `{% now "Y" %}` (auto-update) | Story spec + mockup specifikuju 2026; auto-update čeka Epic 8 SiteSettings |
| D9 | rgba(255,255,255,0.2) za footer separator | Dozvoljeno (whitelist) | Novi token `--color-overlay-white-20` | Token sprawl — semi-transparent white je 1-time-use slučaj u footer separator-u; ne opravdava token |
| D10 | Logo dimensions hardkoderano (40px, 56px) | Whitelist (hardkoderani px) | Tokeni `--logo-height-full`, `--logo-height-shrunk` | 1-time-use, ne opravdava token; alternative `var(--spacing-scale-...) * factor` ne radi u plain CSS-u |
| D11 | z-index hardkoderan na .coric-nav | **1020 (unitless whitelist)** — iznad Bootstrap dropdown (1000) + popover (1010), ispod modal (1055) | Novi token `--z-index-nav` | CRITICAL-12 fix: original z-index 1000 kolidirao sa Bootstrap `.dropdown-menu` default 1000 (race condition pri stacking-u). 1020 daje deterministic layer order. z-index token sistem se može uvesti kad bude više sticky layer-a (modal, lightbox); za Story 1.8 jedan layer = preuranjeno (Story 1.5 sealed) |
| D12 | Sticky sentinel inline style vs CSS klasa | CSS klasa (preferred) | Inline style="height:1px" | Anti-pattern policy zabranjuje inline style; klasa je `.coric-sticky-sentinel` u sticky-nav.css |
| D13 | Sentinel → nav klasa: kako se top-header sakriva | JS dodaje `body.coric-nav-shrunk` klasu | CSS sibling selector iz `.coric-nav--shrunk` | Sibling selector ne radi unazad (top header je pre nav-a); body klasa je jednostavna i CSS-friendly |
| D14 | Test fajl ime | `tests/test_navigation_chrome.py` (novi) | Dodaj u `tests/test_visual_components.py` (postojeći) | Kohezija — Story 1.8 testovi su o navigation/chrome, ne o vizuelnim komponentama; lakše za održavanje |
| D15 | Pill Button konzumacija u nav-u | NE u Story 1.8 (default) | DA — npr. KONTAKT dugme u nav-u kao `secondary` variant | Epic spec ne traži eksplicitno; opcioni reuse — Dev može dodati ako želi pokazati Pill Button u nav layout-u, ali nije AC requirement. Test scenario je opt-in fixture (IMP-6 fix). |
| D16 | Top-header collapse u shrunk state | **`height: 0; padding: 0; overflow: hidden; visibility: hidden` SA transition (smooth collapse + WCAG-safe tab order)** — promoted in-scope (CRITICAL-11 + CRITICAL-CASCADE-3 fix) | `display: none` (sharp removal, izaziva CLS) | Original D16 deferred; promoted jer `display: none` izaziva CLS regression na svakom scroll past 100px (Lighthouse perf gate u Story 1.9). `height: 0` + overflow hidden + height transition daje smooth collapse, element ostaje u flow-u ali zauzima 0px. **Iter 2 dodato:** `visibility: hidden` (sa `transition-delay: 200ms`) za uklanjanje descendants iz tab order (CRITICAL-CASCADE-3). **CLS impact (iter 2 ažuriran wording — bivši aspirational zero-CLS claim povučen):** CLS impact minimized via smooth transition + scroll input grace window (browser CWV CLS metric typically excludes 40px reflow within 500ms grace window posle korisničkog scroll input-a); pending Story 1.9 Lighthouse verification — ne tvrdimo apsolutni zero-CLS jer scroll-induced height transition tehnički može biti detected u edge browser implementations (vidi Dev Notes "Acceptable Layout Behavior — Scroll-Threshold Reflow" za pun tradeoff analysis). |
| D17 | Header.html wrapping pattern | **Standalone siblings: `.coric-top-header` + `<nav class="coric-nav">` kao dva direct children template root-a (NO `<header class="coric-site-header">` wrapper); `.coric-top-header` nosi `role="banner"` ARIA landmark (iter 2 CRITICAL-CASCADE-1 dodato)** — CRITICAL-7 flatten Option A + iter 2 landmark restoration | `<header class="coric-site-header">` sa `position: sticky` na samom header-u | Flatten eliminiše "sticky scrolls away with wrapper" bug — kad je `.coric-nav` unutar `<header>` wrapper-a, `position: sticky` je constrained na wrapper containing block; nav scrollovao AWAY sa wrapper-om umesto da ostane sticky preko cele strane. Flatten daje `<body>` kao stable containing block za nav-ovu stickiness. **Iter 2 cascade fix:** flatten je inicijalno izgubio ARIA `banner` landmark (jer `<header>` direct child `<body>` je default banner); fix je dodavanje eksplicitnog `role="banner"` atributa na `.coric-top-header` div (čuva landmark + flatten benefits). Story 1.6 regression test invariant je migriran u Task 10a sa "PRE `<header>` tag" u "PRE prvi chrome include". |
| D18 | Language switcher form factor change od Story 1.4 baseline-a | **Promenjeno iz `<select>` (Story 1.4) u horizontal `<button>` list per locale (CSP-safe + WCAG `aria-current` support)** — IMP-CASCADE-6 iter 2 | Zadržati Story 1.4 `<select>` pattern netaknut | Driven by: (1) CSP-safe requirement — Story 1.4 koristi inline `onchange="this.form.submit()"` što krši CSP `script-src 'self'`; (2) WCAG `aria-current="page"` zahteva per-link atribut (`<option>` element NE podržava `aria-current` semantiku); (3) horizontalni button layout aligned sa mockup-om nav pattern-a per DESIGN.md. **UX implication:** vizuelni delta od Story 1.4 baseline-a — Dev će primetiti razliku između `language_switcher.html` (Story 1.4, select dropdown) i `language_switcher_nav.html` (Story 1.8, horizontal buttons). To je deliberate split: Story 1.4 partial je known CSP debt deferred to Story 1.9/8.x, dok Story 1.8 nov partial postavlja CSP-safe + WCAG-compliant pattern za sve buduće javne strane. Mockup horizontal nav pattern (DESIGN.md) potvrđuje Layout izbor. **POLISH-8 iter 3 — Story 1.4 partial orphan status (eksplicitno):** `templates/partials/language_switcher.html` (Story 1.4) je **on-disk regression guard only** — Story 1.4 testovi i dalje prolaze (partial postoji + grep za `<select>` element i dalje pasuje), ALI partial NIJE rendered u v1 published surface-u jer Story 1.8 AC1/Task 5.1 eksplicitno UKLANJA `<header>{% include "partials/language_switcher.html" %}</header>` blok iz base.html. Drugim rečima: na Story 1.8 deploy-u, posetilac sajta nikad NE VIDI rendered output Story 1.4 partial-a (njegov sav HTML output je SAMO `language_switcher_nav.html`). Story 1.4 partial postaje **orphan template** koji čeka odluku u Future Story 8.x (admin surface, gde `<select>` može da bude prikladniji) ili Story 9.x (CSP rollout, koji bi konvertovao postojeći `onchange=` u CSP-nonce-d inline JS ili event delegation pattern). U Story 1.8 scope-u Story 1.4 partial nije ni "removed" ni "consumed" — naprosto orphan. |

### Arhitekturni dijagram (CRITICAL-5/6/7 fix — flatten + sentinel u body)

```
base.html
├── <body>                          ← position: relative (sticky-nav.css)
│   ├── <a class="visually-hidden-focusable">…</a>      (skip link, Story 1.6)
│   ├── <div class="coric-sticky-sentinel">             (CRITICAL-5: direct child <body>, NE u header.html)
│   │      • position: absolute; top: 100px;            ← needs body{position:relative} (CRITICAL-6)
│   ├── {% include "partials/header.html" %}
│   │   ├── <div class="coric-top-header">              ← sibling (NO <header> wrapper — CRITICAL-7)
│   │   │      • height transition 200ms (CRITICAL-11 — no display:none; CLS impact minimized via CWV grace window per CRITICAL-CASCADE-5)
│   │   │      • height: 40px (CRITICAL-CASCADE-4 — explicit value enables shrunk-state animation)
│   │   │      • visibility transition w/ delay (CRITICAL-CASCADE-3 — WCAG 2.4.7 tab-order safe)
│   │   │      • role="banner" (CRITICAL-CASCADE-1 — ARIA landmark restored after flatten)
│   │   │      • overflow: hidden
│   │   └── <nav class="coric-nav navbar-expand-md">    ← sibling
│   │          • position: sticky; top: 0; z-index: 1020 (CRITICAL-12 — above Bootstrap dropdown 1000)
│   │          • {% include "partials/language_switcher_nav.html" %}  ← <form>×3 per locale (CRITICAL-1)
│   ├── <main id="main-content" tabindex="-1">…</main>
│   ├── {% include "partials/footer.html" %}            ← CRITICAL-4: posle </main>, pre {% aria_live %}
│   ├── {% aria_live %}
│   ├── <noscript>…</noscript>
│   └── scripts: htmx.defer → bootstrap.sync → sticky-nav.defer  ← CRITICAL-10 rationale
```

Sticky behavior: kad scroll prelazi sentinel (100px from top), sentinel izlazi iz viewport-a; observer ga detektuje i `body.coric-nav-shrunk` klasa se prebacuje. CSS pravila pod `body.coric-nav-shrunk` collapse-uju top-header i shrinking-uju nav.

### Konkretni dimenzioni iz DESIGN.md + EXPERIENCE.md (Dev MORA mapirati 1:1)

| Element | Token / dimension | Source |
|---|---|---|
| Top header bg | `var(--color-brand-green-900)` (#1f3f2f) | DESIGN.md `colors.brand.green-900` |
| Nav bg | `var(--color-brand-green-800)` (#25402f) | DESIGN.md `colors.brand.green-800` |
| Nav text | `var(--color-semantic-text-on-dark)` (white) | DESIGN.md `colors.semantic.text-on-dark` |
| Nav full-state height | `80px` (hardcoded; Decision D1) | empirijski + DESIGN.md container conventions |
| Nav shrunk-state height | `60px` (hardcoded) | Epic spec linija 505 |
| Nav shrunk-state shadow | `var(--shadow-nav-shrunk)` | tokens.css linija 153 (`0 2px 4px rgba(0,0,0,0.1)`) |
| Nav transition | `200ms ease` | Epic spec linija 506 + EXPERIENCE.md linija 216 |
| Nav link uppercase | `text-transform: uppercase; letter-spacing: var(--typography-tracking-wide);` | DESIGN.md + EXPERIENCE.md mikrokopija |
| Nav link min-height | `44px` | WCAG 2.5.5/2.5.8 + EXPERIENCE.md linija 38 |
| Top header padding | `var(--spacing-scale-2) var(--spacing-container-gutter-desktop)` (8px 24px) | spacing tokens + DESIGN.md container |
| Footer bg | `var(--color-brand-green-800)` (NE green-900) | Epic spec linija 504 + DESIGN.md konflikt resolved linija 369 |
| Footer text | `var(--color-semantic-text-on-dark)` | DESIGN.md |
| Footer padding | `var(--spacing-scale-10) 0 var(--spacing-scale-5) 0` (64px / 24px) | spacing tokens |
| Footer separator | `border-top: 1px solid rgba(255, 255, 255, 0.2)` | Decision D9 |
| Copyright font-size | `var(--typography-scale-caption)` (0.875rem) | typography tokens |
| Mobile breakpoint | `@media (max-width: 767px)` | EXPERIENCE.md linija 26 + Bootstrap md |
| Sentinel scroll threshold | `100px` | EXPERIENCE.md linija 214 |
| Logo full-state max-height | `56px` (hardcoded; Decision D10) | empirijski iz mockup-a |
| Logo shrunk-state max-height | `40px` (hardcoded; Decision D10) | empirijski iz mockup-a |
| z-index nav | `1020` (hardcoded; Decision D11 ažuriran u CRITICAL-12 fix) | Iznad Bootstrap dropdown 1000 + popover 1010, ispod modal 1055 |

### Story 1.8 hardkoderani konstanti — rationale (IMP-9 formalna dokumentacija)

Story 1.8 koristi sledeće hardkoderane konstante (unutar AC9 whitelist-a) sa formalnim imenima:

| Naziv (formal) | Vrednost | Lokacija | Rationale (zašto NIJE token) |
|---|---|---|---|
| `NAV_HEIGHT_FULL` | 80px | `.coric-nav { height: 80px }` u header.css | 1-time use; Story 1.5 sealed; ne opravdava token |
| `NAV_HEIGHT_SHRUNK` | 60px | `.coric-nav--shrunk { height: 60px }` u sticky-nav.css | per Epic spec linija 505 |
| `TOP_HEADER_HEIGHT` | 40px | `.coric-top-header { height: 40px }` (full state) u header.css | empirijski iz mockup-a |
| `LOGO_HEIGHT_FULL` | 56px | `.coric-nav__logo-img { max-height: 56px }` | Decision D10 |
| `LOGO_HEIGHT_SHRUNK` | 40px | `.coric-nav--shrunk .coric-nav__logo-img { max-height: 40px }` | Decision D10 |
| `STICKY_SENTINEL_OFFSET` | 100px | `.coric-sticky-sentinel { top: 100px }` u sticky-nav.css | EXPERIENCE.md linija 214 |
| `CHROME_INITIAL_RESERVE` | 120px | (rezervisano: 80 nav + 40 top-header — NIJE potreban explicit `body { padding-top }` jer `position: sticky` ne uklanja element iz flow-a) | informaciono samo |
| `NAV_Z_INDEX` | 1020 (unitless) | `.coric-nav { z-index: 1020 }` u header.css | Decision D11 ažuriran (CRITICAL-12) |
| `WCAG_TOUCH_TARGET` | 44px | `min-height: 44px` na interaktivnim elementima | WCAG 2.5.5/2.5.8 |

Sve gore navedene vrednosti su u AC9 whitelist-u; CSS lint test (Task 9.4d + 9.4e) ih dopušta a sve ostale `\d+px` ili unitless magic numbers blokira.

### sticky-nav.js — pun predlog (Dev može da kopira i adaptira)

```js
/**
 * sticky-nav.js — Sticky Navigation Shrink-on-Scroll
 *
 * Vanilla JS, IIFE, no global window pollution, no jQuery.
 * Uses IntersectionObserver to detect when scroll passes sentinel (~100px from top).
 * Toggles `.coric-nav--shrunk` on .coric-nav and `.coric-nav-shrunk` on body.
 *
 * CSS handles motion (transitions + @media prefers-reduced-motion).
 * JS only toggles class — graceful degradation if IntersectionObserver missing.
 *
 * Story 1.8 — Epic 1: Project Foundation & Visual Identity
 */
(function () {
  'use strict';

  // Defensive: bail if API missing (older browsers — Story 1.8 minimum: Chrome 90+, FF 88+, Safari 14.1+ per POLISH-1 visibility-delay WebKit bug fix)
  if (typeof window === 'undefined' || !('IntersectionObserver' in window)) {
    return;
  }

  // Defensive: bail if required DOM nodes missing
  const nav = document.querySelector('.coric-nav');
  const sentinel = document.querySelector('.coric-sticky-sentinel');
  if (!nav || !sentinel) {
    return;
  }

  // Mobile detection — Decision D4: sticky shrink ne primenjuje se <768px
  // (EXPERIENCE.md: mobile nav je već kompaktan hamburger only; sticky shrink nepotreban)
  const mobileQuery = window.matchMedia('(max-width: 767px)');

  // Toggle klase kad sentinel izlazi iz viewport-a (scroll past 100px from top)
  const observer = new IntersectionObserver(
    function (entries) {
      entries.forEach(function (entry) {
        const isShrunk = !entry.isIntersecting;
        nav.classList.toggle('coric-nav--shrunk', isShrunk);
        document.body.classList.toggle('coric-nav-shrunk', isShrunk);
      });
    },
    { rootMargin: '0px', threshold: 0 }
  );

  // IMP-1 — Sync observer state sa mobile breakpoint-om.
  // Pokrivanje: portrait <768 → landscape ≥768 (rotacija tableta) i resize između breakpoint-ova.
  function syncObserver() {
    if (mobileQuery.matches) {
      observer.disconnect();
      nav.classList.remove('coric-nav--shrunk');
      document.body.classList.remove('coric-nav-shrunk');
    } else {
      observer.observe(sentinel);
    }
  }

  syncObserver(); // initial state
  mobileQuery.addEventListener('change', syncObserver);

  // No cleanup needed — observer + matchMedia listener žive za ceo lifecycle strane.
  // No event listeners on window scroll (memory-leak-safe; IntersectionObserver replaces scroll listener).
})();
```

### header.html — pun skelet predlog (Dev adaptira)

```django
{% load i18n %}
{% load static %}

{# CRITICAL-7 flatten Option A: NEMA <header class="coric-site-header"> wrapper. #}
{# .coric-top-header i <nav class="coric-nav"> su DVA SIBLINGS na template root level. #}
{# Sentinel je u base.html (direct child <body>), NIJE ovde — CRITICAL-5 fix. #}

{# Top header — kontakt informacije (desktop & tablet; mobile collapsed) #}
{# CRITICAL-CASCADE-1 (iter 2): role="banner" — top-header carries ARIA banner landmark since flatten removed <header> wrapper. #}
{# Nav below stays role="navigation"; footer has role="contentinfo". One banner per page per WAI-ARIA APG. #}
<div class="coric-top-header" role="banner" aria-label="{% translate "Kontakt informacije" %}">
  <button type="button"
          class="coric-top-header__mobile-toggle d-md-none"
          data-bs-toggle="collapse"
          data-bs-target="#coricTopHeaderExpanded"
          aria-expanded="false"
          aria-controls="coricTopHeaderExpanded"
          aria-label="{% translate "Pokaži kontakt informacije" %}">
    {# Telefon SVG ikona — inline SVG za no-dep stack #}
    <svg aria-hidden="true" viewBox="0 0 16 16" width="20" height="20">
      <!-- phone path -->
    </svg>
  </button>
  <div id="coricTopHeaderExpanded" class="collapse d-md-block coric-top-header__content">
    {# IMP-2 fix: NE <address> — HTML5 <address> je za contact info nearest <article>/<body>; #}
    {# company contact u top header je obična kontakt informacija → koristimo <p> sa BEM klasom. #}
    <p class="coric-top-header__address">
      {% translate "Vojvođanska 1, Bašaid, Srbija" %}
    </p>
    <a href="tel:+381230468168" class="coric-top-header__phone"
       aria-label="{% translate "Telefon prodaje" %}">
      +381 230 468 168
    </a>
    {# IMP-4 fix: service_phone HARDKODERAN placeholder; TODO Story 8.x SiteSettings #}
    {# zameniti sa {{ site_settings.service_phone }} kad postoji SiteSettings model. #}
    <a href="tel:+381000000000" class="coric-top-header__phone--service"
       aria-label="{% translate "Telefon servisa" %}">
      {% translate "Servis" %}: +381 XXX XXX XXX
    </a>
    <div class="coric-top-header__social">
      <a href="#" aria-label="Facebook">
        <svg aria-hidden="true" viewBox="0 0 24 24" width="20" height="20">
          <!-- FB icon path -->
        </svg>
      </a>
      <a href="#" aria-label="Instagram">
        <svg aria-hidden="true" viewBox="0 0 24 24" width="20" height="20">
          <!-- IG icon path -->
        </svg>
      </a>
    </div>
  </div>
</div>

{# Glavni nav — sticky shrink-on-scroll #}
{# CRITICAL-7: <nav> je sibling sa .coric-top-header (NE inside <header> wrapper). #}
{# position: sticky containing block postaje <body>, nav ostaje sticky preko cele strane. #}
<nav class="coric-nav navbar navbar-expand-md"
     role="navigation"
     aria-label="{% translate "Glavna navigacija" %}">
  <div class="container">
    {# CRITICAL-9: URL namespace je 'core:home' (apps/core/urls.py: app_name = 'core'). #}
    {# CRITICAL-8: logo asset provisionovan u static/img/ kroz Task 1.10. #}
    <a class="navbar-brand coric-nav__logo" href="{% url 'core:home' %}">
      <img src="{% static 'img/coric-agrar-logo-transp-200.png' %}"
           alt="Ćorić Agrar"
           class="coric-nav__logo-img">
    </a>

    <button class="navbar-toggler coric-nav__hamburger"
            type="button"
            data-bs-toggle="collapse"
            data-bs-target="#coricMainNav"
            aria-controls="coricMainNav"
            aria-expanded="false"
            aria-label="{% translate "Otvori meni" %}">
      <span class="navbar-toggler-icon" aria-hidden="true"></span>
    </button>

    <div class="collapse navbar-collapse" id="coricMainNav">
      <ul class="navbar-nav ms-auto coric-nav__list">
        <li class="nav-item">
          <a class="nav-link coric-nav__link" href="{% url 'core:home' %}">{% translate "Početna" %}</a>
        </li>
        <li class="nav-item">
          <a class="nav-link coric-nav__link" href="#">{% translate "Traktori" %}</a>
        </li>
        <li class="nav-item dropdown">
          <a class="nav-link coric-nav__link dropdown-toggle"
             href="#"
             role="button"
             data-bs-toggle="dropdown"
             aria-expanded="false"
             aria-haspopup="true"
             id="navbarDropdownMehanizacija">
            {% translate "Mehanizacija" %}
          </a>
          <ul class="dropdown-menu coric-nav__dropdown" aria-labelledby="navbarDropdownMehanizacija">
            <li><a class="dropdown-item" href="#">{% translate "Priključna mehanizacija (Jeegee)" %}</a></li>
            <li><a class="dropdown-item" href="#">{% translate "Radne mašine (HZM)" %}</a></li>
            <li><a class="dropdown-item" href="#">{% translate "MIX prikolice (Tulip)" %}</a></li>
            <li><a class="dropdown-item" href="#">{% translate "Polovna mehanizacija" %}</a></li>
          </ul>
        </li>
        <li class="nav-item"><a class="nav-link coric-nav__link" href="#">{% translate "Servis" %}</a></li>
        <li class="nav-item"><a class="nav-link coric-nav__link" href="#">{% translate "Priče sa polja" %}</a></li>
        <li class="nav-item"><a class="nav-link coric-nav__link" href="#">{% translate "O nama" %}</a></li>
        <li class="nav-item"><a class="nav-link coric-nav__link" href="#">{% translate "Kontakt" %}</a></li>
        <li class="nav-item">
          {# IMP-3 fix: NEMA aria-expanded jer button još nije wired za toggle (Story 2.13 wiring). #}
          {# aria-expanded bez funkcionalnog toggle = a11y misinformation; ne renderuje se dok ne postoji. #}
          <button type="button"
                  class="coric-nav__search-toggle"
                  aria-label="{% translate "Otvori pretragu" %}">
            <svg aria-hidden="true" viewBox="0 0 24 24" width="20" height="20">
              <!-- search icon path -->
            </svg>
          </button>
        </li>
        <li class="nav-item">
          {# CRITICAL-1 fix: koristi NOVI partial language_switcher_nav.html (form-per-locale, no inline JS). #}
          {# Story 1.4 language_switcher.html ostaje netaknut kao regression guard. #}
          {% include "partials/language_switcher_nav.html" %}
        </li>
      </ul>
    </div>
  </div>
</nav>
```

### footer.html — pun skelet predlog (Dev adaptira)

```django
{% load i18n %}
{% load static %}

<footer class="coric-footer" role="contentinfo">
  <div class="container">
    <div class="coric-footer__top">
      <div class="row">
        {# Kolona 1 — Logo + slogan #}
        {# BONUS-2 iter 3: Footer logo wrapped u <a href="{% url 'core:home' %}"> za parity sa header logo-om. #}
        {# Konzistentnost: oba logoa (top header + footer) navigiraju na home; očekivano UX. #}
        <div class="col-md-3 coric-footer__col">
          <a href="{% url 'core:home' %}" class="coric-footer__logo-link" aria-label="{% translate "Početna" %}">
            <img src="{% static 'img/coric-agrar-logo-transp-light-200.png' %}"
                 alt="Ćorić Agrar"
                 class="coric-footer__logo">
          </a>
          <p class="coric-footer__slogan">
            {% translate "Prijatelj koji razume zemlju!" %}
          </p>
        </div>

        {# Kolona 2 — Proizvodi #}
        <div class="col-md-3 coric-footer__col">
          {% include "partials/section_eyebrow.html" with text="PROIZVODI" tag="h2" variant="on-dark" %}
          <ul class="coric-footer__menu">
            <li><a href="#">{% translate "Traktori" %}</a></li>
            <li><a href="#">{% translate "Mehanizacija" %}</a></li>
            <li><a href="#">{% translate "Polovna mehanizacija" %}</a></li>
            <li><a href="#">{% translate "Rezervni delovi" %}</a></li>
          </ul>
        </div>

        {# Kolona 3 — Najnovije vesti (Lorem Ipsum placeholder; Story 5.4 zamenjuje dinamičkim) #}
        <div class="col-md-3 coric-footer__col">
          {% include "partials/section_eyebrow.html" with text="NAJNOVIJE VESTI" tag="h2" variant="on-dark" %}
          {# TODO: Story 5.4 (Epic 5) zameniće ovo sa {% for post in latest_posts|slice:":3" %}...{% endfor %} #}
          <ul class="coric-footer__news">
            <li><a href="#">{% translate "Lorem ipsum dolor sit amet (vest 1)" %}</a></li>
            <li><a href="#">{% translate "Lorem ipsum dolor sit amet (vest 2)" %}</a></li>
            <li><a href="#">{% translate "Lorem ipsum dolor sit amet (vest 3)" %}</a></li>
          </ul>
        </div>

        {# Kolona 4 — Kontakt + Social #}
        <div class="col-md-3 coric-footer__col">
          {% include "partials/section_eyebrow.html" with text="KONTAKT" tag="h2" variant="on-dark" %}
          <ul class="coric-footer__contact">
            <li><a href="tel:+381230468168">+381 230 468 168</a></li>
            <li><a href="mailto:prodaja@coricagrar.rs">prodaja@coricagrar.rs</a></li>
            <li>
              <address>{% translate "Vojvođanska 1, Bašaid, Srbija" %}</address>
            </li>
          </ul>
          <div class="coric-footer__social">
            <a href="#" aria-label="Facebook">
              <svg aria-hidden="true" viewBox="0 0 24 24" width="24" height="24">
                <!-- FB icon path -->
              </svg>
            </a>
            <a href="#" aria-label="Instagram">
              <svg aria-hidden="true" viewBox="0 0 24 24" width="24" height="24">
                <!-- IG icon path -->
              </svg>
            </a>
          </div>
        </div>
      </div>
    </div>

    <hr class="coric-footer__separator">

    <div class="coric-footer__bottom">
      <p class="coric-footer__copyright text-center">
        © 2026 Ćorić Agrar. {% translate "Sva prava zadržana." %}
      </p>
    </div>
  </div>
</footer>
```

### header.css — predlog ključnih pravila za `.coric-top-header` full-state (iter 2 CRITICAL-CASCADE-3/4)

```css
/* CRITICAL-CASCADE-4 (iter 2): eksplicitna height: 40px u full state — bez nje height: 0 transition u shrunk state NE ANIMIRA */
/* (CSS ne može animirati iz auto u length; mora biti eksplicitna numerička vrednost u full state). */
/* CRITICAL-CASCADE-3 (iter 2): visibility: visible u full state je par sa visibility: hidden u shrunk state — */
/* uklanja tel: linkove + social iz tab order kad je shrunk (WCAG 2.4.7 + 2.4.11). */
.coric-top-header {
  background-color: var(--color-brand-green-900);
  color: var(--color-semantic-text-on-dark);
  padding: var(--spacing-scale-2) var(--spacing-container-gutter-desktop);
  font-size: var(--typography-scale-caption);
  height: 40px;                /* CRITICAL-CASCADE-4 — full state explicit height (IMP-9 TOP_HEADER_HEIGHT konstanta) */
  overflow: hidden;            /* za smooth height: 0 collapse (D16) */
  visibility: visible;         /* CRITICAL-CASCADE-3 — par sa shrunk visibility: hidden */
  transition: height 200ms ease, padding 200ms ease, visibility 0s linear 0s;
}

/* Mobile height: auto override in sticky-nav.css (single-source). */
```

### sticky-nav.css — predlog ključnih pravila

```css
/* CRITICAL-6 fix: body{position:relative} daje stable containing block za sentinel{position:absolute}. */
/* Story 1.8 sticky-nav: enables IntersectionObserver sentinel positioning. */
/* Mali globalni dodatak — dokumentovano namerno. */
body {
  position: relative;
}

/* Sentinel — invisible, positioned for IntersectionObserver */
/* CRITICAL-5 fix: sentinel je direct child <body> (placed u base.html PRE include header.html), */
/* NIJE inside header partial — sprečava da sentinel bude sakriven sopstvenim efektom kad top-header dobije height:0. */
.coric-sticky-sentinel {
  position: absolute;
  top: 100px; /* per EXPERIENCE.md linija 214 */
  left: 0;
  width: 1px;
  height: 1px;
  pointer-events: none;
}

/* Sticky nav transitions */
.coric-nav {
  transition: height 200ms ease, box-shadow 200ms ease;
}

.coric-nav__logo-img {
  max-height: 56px; /* Decision D10 */
  transition: max-height 200ms ease;
}

/* Shrunk state */
.coric-nav--shrunk {
  height: 60px; /* per epic spec */
  box-shadow: var(--shadow-nav-shrunk);
}

.coric-nav--shrunk .coric-nav__logo-img {
  max-height: 40px; /* Decision D10 */
}

/* CRITICAL-11 + Decision D16 fix: NE display:none (izaziva CLS na svakom scroll past 100px). */
/* Koristimo height:0 + padding:0 + visibility:hidden SA transition (overflow:hidden je u header.css na .coric-top-header). */
/* Top-header collapses smoothly i ostaje u flow-u (zauzima 0px); CLS impact minimized via smooth transition + scroll input grace window (pending Story 1.9 Lighthouse verification). */
/* CRITICAL-CASCADE-3 (iter 2): visibility: hidden sa transition-delay: 200ms uklanja tel: linkove + social iz tab order + screen reader announcement u shrunk state. */
/* visibility flips POSLE height transition completes (200ms delay) → smooth collapse animacija nije prekinuta + WCAG 2.4.7/2.4.11 zadovoljeno. */
body.coric-nav-shrunk .coric-top-header {
  height: 0;
  padding-top: 0;
  padding-bottom: 0;
  visibility: hidden;
  transition: height 200ms ease, padding 200ms ease, visibility 0s linear 200ms;
}

/* Reduced motion respect — KRITIČNO (per Story 1.7 CRITICAL-3 lekcija) */
@media (prefers-reduced-motion: reduce) {
  .coric-nav,
  .coric-nav__logo-img,
  .coric-top-header {
    transition: none;
  }
  /* CRITICAL-CASCADE-3: u reduced-motion mode-u visibility takođe instantly switches — bez delay-a (jer nema height transition da se sačeka) */
  body.coric-nav-shrunk .coric-top-header {
    transition: none;
  }
}

/* Mobile — sticky shrink se ne primenjuje (Decision D4) */
@media (max-width: 767px) {
  .coric-sticky-sentinel { display: none; }
  /* CRITICAL-CASCADE-4 iter 2: mobile top-header ima variable height (collapse content) — height auto override */
  .coric-top-header { height: auto; }
}
```

**Edge case — scroll-restoration mid-scroll:** Ako korisnik refresh-uje stranu sa scroll pozicijom past sentinel, browser-ov default scroll restoration ide na sačuvanu poziciju → IntersectionObserver inicijalno detektuje sentinel kao non-intersecting → body dobija `coric-nav-shrunk` klasu bez animation flash (jer transition kreće iz krajnjeg state-a). Acceptable ponašanje — dokumentovano.

### Known visual edge cases (IMP-CASCADE-11 iter 2 dokumentovano + POLISH-5 iter 3)

- **Mid-scroll dropdown expand race:** Ako korisnik otvori Mehanizacija dropdown dok je nav u shrunk state-u (height: 60px), pa zatim scroll-uje gore preko sentinel-a (100px) — nav se proširava nazad u full state (80px), što takođe trigeruje dropdown menu position recalculation (Bootstrap Popper.js). Korisnik vidi mid-transition jump (~150-200ms) gde dropdown menu se "skoči" 20px naniže da prati ekspandirajući nav. **Acceptable behavior** — dropdown re-pozicioniranje je intentional (Bootstrap Popper inherent ponašanje), i samo se događa u edge case-u koincidencije timing-a (korisnik mora otvoriti dropdown, pa scroll-ovati gore unutar ~200ms). Playwright snapshot test za ovaj edge case **deferred to Story 9.8** (E2E flight) jer pytest cannot simulate scroll-induced animation timing.
- **Initial paint flash u skip-scroll scenariju:** Ako korisnik klikne anchor link `#footer` ili sličan, browser instant-jumps na anchor poziciju (no scroll animation). IntersectionObserver fires immediately u sledećem frame-u, body dobija `coric-nav-shrunk` klasu, top-header collapses smooth 200ms transition. Korisnik vidi initial 1-frame full-state, pa 200ms collapse. **Acceptable** — alternativa (matching `instant-jump → instant-shrunk`) bi zahtevala JS scroll-position check on DCL što usporava prvi paint.
- **Touch-device momentum scroll above-sentinel:** Na touch device-ima, momentum scrolling iznad sentinel-a može oscillating-toggle `coric-nav-shrunk` klasu (in/out/in/out u par frame-ova). CSS transition pattern `height 200ms ease` je nedovoljno za prevent jitter — browser native CSS handling se ovde oslanja na IntersectionObserver throttling. Vidno samo u edge case-u sa low-end mobile (Android <Chrome 90 era), pa **out-of-scope za Story 1.8** mobile minimum.
- **Tab-during-collapse 200ms race (POLISH-5 iter 3):** Korisnik pritiska Tab tokom 200ms height transition-a top-header-a → focus može da sleti na `tel:` link koji je VIZUELNO compressed (visibility flips na `hidden` POSLE 200ms delay-a, NE u 0ms). Ovo je transient WCAG 2.4.11 (Focus Not Obscured) edge case koji traje tačno 200ms po scroll past sentinel-a. **Mitigation alternative razmatrane + odbačene:** (a) **JS `inert` attribute apply at 0ms** — dodaje JS kompleksnost per arhitektonska rationala D16 (CSS-only solution preferred za chrome partial); (b) **Instant `visibility: hidden` at 0ms** umesto delay-a — uzrokuje sadržaj da nestane PRE nego što se height collapse završi, što je vizuelno jarring i razbija smooth transition UX. **Accept as transient 200ms edge case** — verifikacija u Story 9.8 Playwright Tab-during-transition test (deferred jer pytest cannot simulate timing).

**Copyright Unicode safety (L-1 style note):** `©` karakter renderuje se u UTF-8; svi novi HTML/CSS/JS fajlovi treba da budu UTF-8 (default u Django + Whitenoise stack-u). Za maksimalnu portabilnost može se koristiti `&copy;` HTML entity u footer.html — non-binding stylistic preference.

### Acceptable A11y Behavior — Banner Landmark Lifecycle (POLISH-6 iter 3)

Story 1.8 namerno usvaja sledeći netipičan ali dokumentovan a11y tradeoff vezan za `role="banner"` landmark na `.coric-top-header` div-u:

- **Banner landmark intentionally removed from accessibility tree during shrunk state:** kad korisnik scroll-uje preko 100px sentinel-a, body dobija `coric-nav-shrunk` klasu → `.coric-top-header` dobija `visibility: hidden` (sa 200ms transition-delay per CRITICAL-CASCADE-3). Po W3C CSSOM spec-u, `visibility: hidden` element je uklonjen iz a11y tree-a, što znači da je i njegov `role="banner"` landmark uklonjen iz screen reader landmark menu-a (NVDA D-key, JAWS `;` / `R`).
- **Screen reader landmark menu u shrunk state-u prikazuje:** `navigation` (`.coric-nav`) + `main` (`<main id="main-content">`) + `contentinfo` (`<footer>`). Banner se vraća u landmark menu kad korisnik scroll-uje gore preko sentinel-a (top-header dobija `visibility: visible`).
- **Unconventional but documented tradeoff:** standardna preporuka WAI-ARIA APG je da landmarks ostanu uvek dostupni za sve content faze. Story 1.8 deliberately odstupa jer je banner content vizuelno hidden u shrunk state-u — održavanje landmark menu unosa bez vidljivog content-a bi confuses screen reader korisnike koji landmark-navigate na nešto što nije perceivable.
- **Lepši nego alternatives razmatrane + odbačene:**
  - **(a) Držanje content focusable u shrunk state-u** (skidanje `visibility: hidden` declaracije): re-uvodi CRITICAL-CASCADE-3 fail — `tel:` linkovi + social linkovi ostaju u tab order kad su vizuelno collapsed → WCAG 2.4.7 Focus Visible + 2.4.11 Focus Not Obscured non-compliance.
  - **(b) Re-introduction `<header class="coric-site-header">` wrapper-a sa `role="banner"`** (umesto inline `role="banner"` na `.coric-top-header`): re-uvodi CRITICAL-7 sticky-scrolls-away bug — `position: sticky` na `.coric-nav` ima wrapper kao containing block, sticky scrolls away umesto da ostane preko cele strane.
- **Manual sign-off:** Manual checklist u Task 10.3 (POLISH-4 iter 3 ažuriran) eksplicitno verifikuje da banner disappears iz landmark menu-a kad je strana scroll-ovana past 100px i reappears na scroll-up — to je očekivano ponašanje, NE bug.

### Token usage manifest (Story 1.8 komponente konzumiraju iz tokens.css)

| Token | Konzumira |
|---|---|
| `--color-brand-green-900` | header.css (top-header bg) |
| `--color-brand-green-800` | header.css (nav bg), footer.css (footer bg) |
| `--color-semantic-text-on-dark` | header.css (top header + nav text), footer.css (footer text) |
| `--color-semantic-focus-ring` | header.css (focus outlines), footer.css (focus outlines), sticky-nav.css (n/a — uses inherited) |
| `--shadow-nav-shrunk` | sticky-nav.css (shrunk state box-shadow) |
| `--spacing-scale-2` | header.css (top header padding) |
| `--spacing-scale-3` | header.css (language switcher gap) |
| `--spacing-scale-4` | header.css (nav link padding) |
| `--spacing-scale-5` | footer.css (footer-bottom padding, separator margin) |
| `--spacing-scale-10` | footer.css (footer-top padding) |
| `--spacing-container-gutter-desktop` | header.css (top header horizontal padding) |
| `--spacing-container-gutter-mobile` | header.css (mobile horizontal padding) |
| `--spacing-container-max-width` | (inherited from Bootstrap container) |
| `--typography-family-primary` | header.css, footer.css |
| `--typography-weight-bold` | header.css (nav links uppercase) |
| `--typography-weight-light` | footer.css (slogan, copyright) |
| `--typography-scale-caption` | header.css (top header text), footer.css (copyright) |
| `--typography-scale-small` | header.css (nav links), footer.css (footer links) |
| `--typography-tracking-wide` | header.css (nav links uppercase tracking) |
| `--rounded-sm` | (n/a — Story 1.8 nema rounded elements direktno; nav i footer su pravougaoni) |

Ukupno: **~17 različitih tokena** konzumirano kroz 3 nova CSS fajla. Story 1.8 NE uvodi nove tokene.

### Reuse pattern — Story 1.7 komponente koje Story 1.8 konzumira

**Section Eyebrow** (footer headings — 3x):
```django
{% include "partials/section_eyebrow.html" with text="PROIZVODI" tag="h2" variant="on-dark" %}
{% include "partials/section_eyebrow.html" with text="NAJNOVIJE VESTI" tag="h2" variant="on-dark" %}
{% include "partials/section_eyebrow.html" with text="KONTAKT" tag="h2" variant="on-dark" %}
```

`tag="h2"` umesto default `"div"` — semantička heading hijerarhija u footer-u (footer-content ima h1 na main strani, h2 na footer kolonama).
`variant="on-dark"` — KRITIČNO jer footer ima green-800 bg; bez ovog `coric-section-eyebrow__text` bi koristio default `--color-brand-green-800` boju (nevidljivu na zelenom).

**Pill Button** (potencijalna konzumacija — opciono per Decision D15):
- Nav CTA "KONTAKT" kao `secondary` variant — Dev odlučuje.
- Footer CTA "POŠALJI UPIT" — opciono u Kolona 4.

Ako Dev koristi:
```django
{% include "partials/pill_button.html" with variant="secondary" label="Kontakt" href="#" extra_classes="ms-2" %}
```

**Language Switcher (Story 1.4 — NETAKNUT, ne konzumira se direktno u Story 1.8):**
Story 1.4 `language_switcher.html` ima inline `onchange="this.form.submit()"` što krši AC9 Anti-pattern #2. Story 1.8 ga ne konzumira u svom novom header-u — umesto toga kreira novi partial:

**Language Switcher Nav (NOVI partial — Story 1.8):**
```django
{% include "partials/language_switcher_nav.html" %}
```

Novi partial koristi `<form>` per locale + `<button type="submit">` — no JS, CSP-friendly, podržava `aria-current="page"` per AC4 (CRITICAL-1 fix). CSS wrapper `.coric-nav__language-switcher` u header.css daje vizuelne stilove specifične za nav layout.

### Mehanizacija dropdown — `<a>` vs `<button>` keyboard semantic (IMP-CASCADE-8 iter 2)

Skeleton koristi `<a role="button" href="#" data-bs-toggle="dropdown">` za dropdown toggle, što je Bootstrap 5 konvencija. Komentar za buduće code review:

- **Bootstrap 5 pattern dozvoljava `<a role='button' href='#'>` za dropdown toggle:** Bootstrap JS kalkuliše `event.preventDefault()` da spreči navigation na `#`; `role="button"` daje screen reader-ima signal "dugme, ne link". Funkcionalno radi.
- **Za bolju keyboard semantiku razmotriti `<button class='nav-link dropdown-toggle'>`:** Browser native `<button>` ima default Space + Enter handling + nema "phantom href" problem (`href="#"` je suvišan signal); Bootstrap JS prihvata oba.
- **Current izbor:** `<a>` je accepted za konzistentnost sa Bootstrap konvencijom (manji code surface, lakše za održavanje); `<button>` je preporučen za buduće dropdown stories ako se ikada uradi rewrite. Nije blocker u Story 1.8.

### CSS Transition Shorthand Reference — visibility full vs shrunk parsing (BONUS-1 iter 3 — moved from AC2 in iter 4)

CSS shorthand `transition: visibility 0s linear 0s` parsuje se po standardnom transition-property/duration/timing-function/delay redosledu:
- `transition-property: visibility`
- `transition-duration: 0s`
- `transition-timing-function: linear`
- `transition-delay: 0s`

Drugim rečima, **duration 0s + delay 0s** znači "visibility property se prebacuje instant kad bilo koja promena state-a stigne, bez animacije i bez čekanja". Ovo je **full-state pair vrednost** za visibility property na `.coric-top-header`.

U **shrunk state-u** (vidi `body.coric-nav-shrunk .coric-top-header` u sticky-nav.css) prelazi se na `visibility 0s linear 200ms` (duration 0s + delay 200ms) — visibility flip-uje instant, ali POSLE 200ms čekanja da se height transition završi. Ovo daje smooth height collapse animation pa onda hard visibility flip POSLE — tab order i screen reader announcement se uklanjaju tek kad je element vizuelno collapsed (WCAG 2.4.7 + 2.4.11 compliant, vidi CRITICAL-CASCADE-3).

Praktičan side-by-side:

| State | Vrednost | Effective behavior |
|---|---|---|
| Full (`.coric-top-header`) | `visibility 0s linear 0s` | Instant flip prilikom state-entry, bez animacije |
| Shrunk (`body.coric-nav-shrunk .coric-top-header`) | `visibility 0s linear 200ms` | Instant flip POSLE 200ms (waits height collapse) |
| Reduced-motion (oba state-a) | `transition: none` | Instant flip bez delay-a (jer nema height transition da se sačeka) |

### `<address>` semantic split — top-header vs footer (IMP-CASCADE-4 iter 2)

Story 1.8 koristi `<p>` u top-header-u i `<address>` u footer-u za istu kontakt adresu — to je deliberate. Rationale:

- **Footer `<address>` je CANONICAL** per HTML5 spec: "When the `<address>` element is contained within a `<body>`, it represents contact information for that body." Footer je nearest section ancestor svojom semantikom site-wide owner-a, pa `<address>` u footer-u predstavlja canonical site contact info.
- **Top-header `<p class="coric-top-header__address">` je REDUNDANT NAV CHROME**, NE canonical site contact. Top-header je marketing chrome (prikazuje contact za quick reference + telefon-tap funkcionalnost), NIJE site identification block. Korišćenje `<address>` na top-header-u bi bilo nesemantsko duplikat (dva `<address>` elementa na istoj strani sa identičnom informacijom — confuses Reader Mode + zbunjuje screen reader-e koji izlistavaju landmark-e).
- **Rezultat:** Top-header koristi BEM klasu sa `<p>` (vidi IMP-2); footer koristi `<address>` element. Stylistic difference je deliberate, NIJE bug.

### Anti-patterns za Story 1.8 (project-context.md § Critical Don't-Miss + Story 1.7 lessons)

1. **NEMA inline `style="..."`** u NOVIM fajlovima (header.html, footer.html, language_switcher_nav.html). Sentinel se stilizuje preko `.coric-sticky-sentinel` CSS klase (Decision D12). KRITIČNO: grep scope je STROGO na NOVE fajlove kreirane u Story 1.8 — Story 1.4 `language_switcher.html` (postojeći) ima inline `onchange="this.form.submit()"` što je known CSP debt deferred to Story 1.9 (CI CSP hardening) / Story 8.x; Story 1.8 NE blokira jer Story 1.8 ne konzumira taj partial.
2. **NEMA inline `<script>`** ili `onclick=...`/`onsubmit=...`/`onchange=...` u NOVIM HTML fajlovima Story 1.8 (CSP-friendly).
3. **NEMA hardcoded hex** u CSS-u van whitelist-a (per AC9).
4. **NEMA hardcoded px** u CSS-u van whitelist-a (`1px, 2px, 44px, 60px, 80px, 40px, 56px, 100px, 120px`) — sve ostale → `var(--spacing-*)`.
5. **NEMA hardcoded unitless magic numbers** osim `1020` (z-index `.coric-nav`) — sve ostale unitless takođe nedozvoljene (AC9 split whitelist — CRITICAL-12).
6. **NEMA `window.<x> = ...`** u sticky-nav.js (global pollution forbidden — koristiti IIFE).
7. **NEMA `console.log`** u sticky-nav.js u produkciji (debugging samo).
8. **NEMA `addEventListener('scroll', ...)`** za sticky pattern (anti-pattern — koristi IntersectionObserver per epic spec).
9. **NEMA jQuery** ili Alpine.js u Story 1.8 (vanilla JS only).
10. **NEMA cyrillic** karaktera bilo gde (sve latinica).
11. **NEMA `display: none` na top-header u shrunk state-u** (CRITICAL-11 + Decision D16) — koristi se `height: 0 + padding: 0 + visibility: hidden` SA transition (`overflow: hidden` na elementu); visibility ima `transition-delay: 200ms` da flips POSLE height tranzicije završi (CRITICAL-CASCADE-3 iter 2 — WCAG-safe tab order). Razlog: `display: none` izaziva CLS regression u Lighthouse Core Web Vitals (gate u Story 1.9). Iter 2 ažurirano: CLS impact minimized via smooth transition + CWV grace window (pending Story 1.9 verification — vidi CRITICAL-CASCADE-5 Dev Notes subsekciju "Acceptable Layout Behavior — Scroll-Threshold Reflow").
12. **CRITICAL-CASCADE-3 iter 2 — ISPRAVKA prethodne iter 1 tvrdnje:** prethodna verzija (iter 1) je tvrdila da `height: 0; overflow: hidden` automatski uklanja descendants iz tab order — **TO JE NETAČNO**. Browseri NE uklanjaju `<a href="tel:...">` linkove iz tab order kad je parent `height: 0` + `overflow: hidden` (linkovi ostaju keyboard-focusable). Korišćen `visibility: hidden` (sa `transition-delay: 200ms` da flips POSLE height tranzicije) za uklanjanje shrunk descendants iz tab order + AT announcement — WCAG 2.4.7 (Focus Visible) + 2.4.11 (Focus Not Obscured) compliant. Bez ovog fixa screen reader bi i dalje najavio "+381 230 468 168, link, telefon prodaje" iako je element vizuelno collapsed.
13. **NEMA `defer`** na sticky-nav.js BEZ verifikacije da DOM postoji u trenutku izvršavanja — `defer` čeka DOM parse complete, pa je sigurno koristiti `document.querySelector(...)` direktno (NE treba `DOMContentLoaded` listener).

### Performance & a11y must-haves

- **Sticky-nav.js veličina:** treba biti <2KB unminified (vanilla, no deps).
- **Render path:** header.html + footer.html render ne sme blokirati first paint — server-side rendering Django + CSS u head-u (Story 1.6 pattern).
- **CSS bundle size:** 3 nova CSS fajla ukupno treba biti <8KB.
- **CLS (Cumulative Layout Shift):** CRITICAL-11 + Decision D16 promovirano in-scope — top-header collapses smooth `height: 0` transition umesto `display: none`. `position: sticky` ne uklanja element iz flow-a; bez explicit `body { padding-top }`. **CRITICAL-CASCADE-5 iter 2 ažurirano:** CLS impact minimized via smooth transition + scroll input grace window (browser CWV CLS metric typically excludes layout shifts ≤500ms posle korisničkog scroll input-a); pending Story 1.9 Lighthouse verification — ne tvrdimo apsolutni zero-CLS jer scroll-induced reflow tehnički može biti detected. Vidi "Acceptable Layout Behavior — Scroll-Threshold Reflow" subsekcija ispod za pun tradeoff analysis.

### Acceptable Layout Behavior — Scroll-Threshold Reflow (CRITICAL-CASCADE-5 iter 2)

**Tradeoff documentation:** Top-header collapse (`height: 40px → 0`) menja document height za 40px na svakom scroll past 100px sentinel breakpoint-a. Ovo je deliberate accept-with-tradeoffs decision:

- **Observed behavior:** Glavni content (main + footer) shifta gore 40px kad korisnik scroll-uje preko 100px (jer top-header ide na 0 visine), pa shifta dole 40px kad korisnik scroll-uje natrag iznad 100px. Iako je `transition: height 200ms ease` smooth, ovo TEHNIČKI ulazi u kategoriju layout shift-a.
- **CWV CLS metric mitigation:** Chrome (i većina browser-a) ima 500ms "user input grace window" — layout shifts koje se dese unutar 500ms posle scroll/click/keypress input-a se NE računaju u CLS score. Sticky shrink reflow se događa direktno tokom scroll događaja → ulazi u grace window → CLS impact je u praksi 0 ili vrlo mali.
- **Alternativna rešenja razmatrana ali odbačena:**
  - (a) **Body `padding-top: 40px` reservation:** Dodaje 40px dead space iznad above-the-fold na home strani; estetski neprijatno za UX (Marko prvi posetilac vidi "prazno" iznad hero-a).
  - (b) **`position: absolute` na top-header:** Komplikuje sticky nav top anchor (nav-u treba `top: 0` ili `top: 40px` depending na top-header state — dvostruki transition trigger; loš code-smell).
  - (c) **Revert flatten / vraćanje `<header>` wrapper-a:** Re-uvodi originalni "sticky scrolls away with wrapper" bug koji je iter 1 CRITICAL-7 fix originally rešio; netačan izbor.
- **Current choice rationale:** Accept smooth-transition reflow unutar CWV grace window-a — best balance simplicity vs visual quality vs metric impact. Verify u Story 1.9 Lighthouse run sa pravim CLS metric-om; ako Lighthouse pokaže CLS regression > 0.1, razmotriti option (a) sa accept-the-dead-space tradeoff.
- **Empirijski signal za Story 1.9:** Story 1.9 CI Lighthouse gate treba da meri CLS na home strani sa scroll simulation (`lighthouse --view --emulated-form-factor=desktop`). Ako CLS > 0.1, treba escalirati u option (a) ili (b).
- **Pattern: deferred verification consistent with Story 1.7 AC9.10 (FINAL-5 iter 4 precedent citation):** collectstatic hashed-import verification deferred to Story 1.6 vendor cleanup OR Story 1.9 CI prep with `@pytest.mark.skip` scaffold. Story 1.8 follows same pattern: in-scope verification (file presence, render contracts, CSS grep, ARIA roles, base.html structure) covers Story 1.8 deliverable surface; CLS / Lighthouse perf empirical verification is downstream (Story 1.9) and not solvable in Story 1.8 scope alone. Architectural reflow is accepted-tradeoff dokumentovan kroz CRITICAL-CASCADE-5 sa Story 1.9 Lighthouse verification gate, aligned sa project precedent-om deferred verification pattern-a.

### Project structure alignment (architecture.md)

`static/js/` + `static/img/` se uvode prvi put — tree posle Story 1.8:
```
static/
  css/
    tokens.css                 (Story 1.5)
    main.css                   (Story 1.6 + Story 1.7 imports + Story 1.8 imports)
    components/
      repeating-element.css    (Story 1.7)
      pill-button.css          (Story 1.7)
      wave-divider.css         (Story 1.7)
      section-eyebrow.css      (Story 1.7)
      hero-overlay-card.css    (Story 1.7)
      header.css               (Story 1.8 NEW)
      footer.css               (Story 1.8 NEW)
      sticky-nav.css           (Story 1.8 NEW)
  fonts/roboto/                (Story 1.5)
  img/                         (Story 1.8 NEW direktorijum — prvi put)
    coric-agrar-logo-transp-200.png         (Story 1.8 NEW — kopirano iz docs/Dizajn/_HTML/img/)
    coric-agrar-logo-transp-light-200.png   (Story 1.8 NEW — kopirano iz docs/Dizajn/_HTML/img/)
  js/                          (Story 1.8 NEW direktorijum — prvi put)
    sticky-nav.js              (Story 1.8 NEW)
  vendor/                      (Story 1.6 — htmx, bootstrap)
templates/
  base.html                    (Story 1.6 — modifikovan u Story 1.8: sentinel + header.html include + footer.html include + sticky-nav.js script)
  partials/
    language_switcher.html     (Story 1.4 — netaknut, NE konzumira se u Story 1.8 header-u)
    repeating_element.html     (Story 1.7)
    pill_button.html           (Story 1.7)
    wave_divider.html          (Story 1.7)
    section_eyebrow.html       (Story 1.7)
    hero_overlay_card.html     (Story 1.7)
    header.html                (Story 1.8 NEW — standalone siblings, no <header> wrapper)
    footer.html                (Story 1.8 NEW)
    language_switcher_nav.html (Story 1.8 NEW — form-per-locale, aria-current="page", CSP-friendly)
```

### Interface contract (IMP-7)

Story 1.8 SHOULD imati prateći interface contract dokument `1-8-interface-contract.md` modelovan po Story 1.7 contract-u (`1-7-interface-contract.md`). Mandatory components:
1. **5 novih artifacts:** header.html, footer.html, language_switcher_nav.html, sticky-nav.js, header.css + footer.css + sticky-nav.css (CSS triple).
2. **Parameter tables** za svaki konzumirani partial (Section Eyebrow `text/tag/variant`).
3. **CSS classes** — kompletna BEM lista (.coric-top-header, .coric-nav, .coric-footer, .coric-language-switcher__btn, etc.).
4. **Tokens** — manifest 17 tokena (vidi gore).
5. **Strategy A imports** — main.css `@import './components/header.css'` itd. relative-with-dot sintaksa.

Action: Dev kreira `_bmad-output/implementation-artifacts/1-8-interface-contract.md` paralelno sa story implementation-om (NIJE strictly blocking AC, ali strongly recommended za downstream Epic 2-7 consumers — Story 1.7 precedent već postavlja kontrakt patterns kao expected artefact).

### Interface contract — language_switcher_nav.html context (IMP-CASCADE-5 iter 2)

Partial `templates/partials/language_switcher_nav.html` zahteva sledeći Django template context (provided by middleware + context processors konfigurisani u Story 1.4):

- **Required context variables:**
  - `request` (Django HttpRequest object) — koristi se za `{{ request.path }}` u hidden `next` input (POST se vraća na isti path nakon switch-a).
  - `LANGUAGE_CODE` (str, npr. `"sr"`, `"hu"`, `"en"`) — koristi se za `aria-current="page"` detection na trenutnom locale-u i za CSS modifier klasu `coric-language-switcher__btn--current`.
- **Provided by:** Django context processors konfigurisani u `settings.TEMPLATES[0]['OPTIONS']['context_processors']`:
  - `django.template.context_processors.request` — provides `request` global
  - `django.template.context_processors.i18n` — provides `LANGUAGE_CODE` global
  - Oba su standardno konfigurisana u Story 1.4 i NEMA dodatne config zahteve od Story 1.8.
- **Required template tags loaded inside partial:**
  - `{% load i18n %}` na prvoj liniji — provides `{% get_available_languages %}`, `{% blocktranslate %}`.
- **Required URL pattern:** `set_language` URL name — provided by `path('i18n/', include('django.conf.urls.i18n'))` u root urls.py (Story 1.4).
- **Anti-contract (NE zavisi od):** NE koristi `language_switcher.html` (Story 1.4 partial); NE koristi inline `onchange=`; NE pollute window namespace; NE zahteva custom JS modul.

### Project-wide invariants — sticky-nav.css globalni efekti (IMP-CASCADE-9 iter 2)

Story 1.8 sticky-nav.css uvodi sledeći project-wide invariant koji future stories MORAJU poštovati:

- **`body { position: relative }`** — set u sticky-nav.css za stable containing block sentinel-a (CRITICAL-6 fix). **Future stories koje dodaju `position: absolute` element direktno na `<body>` nivou treba da preprovere ovaj invariant:** ako element treba viewport anchor (NE body anchor), koristi `position: fixed` umesto `position: absolute`; ako element treba body anchor (npr. modal overlay), `position: absolute` će raditi sa body kao positioned containing block. Najčešći use case-ovi gde se ovo javlja:
  - Story 2.13 Search popup overlay — preporuka: `position: fixed` (viewport anchor) ili `position: absolute` (body anchor — radi sa Story 1.8 invariant-om).
  - Future modal/lightbox stories — uvek `position: fixed` za viewport anchor (Bootstrap modal već koristi `position: fixed`).
- Dokumentovano u `sticky-nav.css` inline komentaru: `/* Story 1.8 sticky-nav: enables IntersectionObserver sentinel positioning */`.

## Testing

### Test framework

- `pytest` + `pytest-django` (već konfigurisan u Story 1.6)
- `tests/conftest.py` već definiše `client` fixture (Story 1.6)
- Pretpostavlja se da postoji bar jedan URL pattern u `urls.py` koji renderuje `base.html` (Story 1.6 testovi rely on `/sr/` GET)

### Test fajl (Dev kreira u Task 9)

`tests/test_navigation_chrome.py` (Decision D14 — novi fajl za kohezivnost; alternativa: dodati u `tests/test_visual_components.py`).

### Test scenariji (predlog za Dev/TEA)

**POLISH-10 iter 3 — Test scenario count asymmetry resolution (MUST vs SHOULD):** Task 9 lista (~24 explicit subtasks 9.1-9.16 + extensions 9.4a-h) i Testing scenarios sekcija (~55 sub-scenarios) NE matchuju 1:1 brojanjem — to je deliberate intent. Konvencija:
- **[MUST]** — Task 9.x eksplicitan subtask. Dev MORA implementirati tokom Story 1.8 (blocking gate u Task 10.1). Pokriva svaki AC i CRITICAL/CASCADE fix verifikaciju.
- **[SHOULD]** — Dodatne thoroughness scenarios koji su recommended za detailed coverage ali se mogu odložiti do Story 9.8 Playwright E2E ili manual smoke u Task 10.3. NE blokira Story 1.8 sign-off ako se izostavi, pod uslovom da MUST-set prolazi.

Dev biraće optimalno: za prvi prolazak, focus na [MUST]; za production hardening, dodati [SHOULD] scenarios. Annotation prati svaki scenario inline.

**Filesystem & struktura (AC1):**
- `[MUST] test_header_partial_file_exists` — `templates/partials/header.html` postoji.
- `[MUST] test_footer_partial_file_exists` — `templates/partials/footer.html` postoji.
- `[MUST] test_header_css_file_exists` — `static/css/components/header.css` postoji.
- `[MUST] test_footer_css_file_exists` — `static/css/components/footer.css` postoji.
- `[MUST] test_sticky_nav_css_file_exists` — `static/css/components/sticky-nav.css` postoji.
- `[MUST] test_sticky_nav_js_file_exists` — `static/js/sticky-nav.js` postoji.
- `[MUST] test_main_css_imports_header_footer_sticky` — `main.css` ima 3 nova @import za Story 1.8 komponente.

**Header rendering (AC2, AC3, AC4):**
- `[MUST] test_header_renders_top_header_with_p_address` — GET `/sr/` → HTML sadrži `<p class="coric-top-header__address">` u `.coric-top-header` (IMP-2: NE `<address>` element).
- `[MUST] test_header_renders_top_header_with_tel_links` — HTML sadrži `<a href="tel:+...">` × 2 (prodaja + servis).
- `[MUST] test_header_renders_top_header_with_aria_label` — HTML sadrži `role="banner" aria-label="...kontakt..."` (CRITICAL-CASCADE-1 iter 2: `role="region"` → `role="banner"`).
- `[MUST] test_header_renders_main_nav_with_role_navigation` — HTML sadrži `<nav role="navigation" aria-label="...">`.
- `[MUST] test_header_nav_uses_navbar_expand_md` — HTML sadrži `navbar-expand-md` klasu na `<nav class="coric-nav">` (CRITICAL-3: NE `navbar-expand-lg`).
- `[MUST] test_header_renders_mehanizacija_dropdown_with_bootstrap_attrs` — HTML sadrži `data-bs-toggle="dropdown"` + `aria-haspopup="true"`.
- `[MUST] test_header_renders_search_toggle_button_no_aria_expanded` — HTML sadrži `<button class="...search-toggle..." aria-label="...">` ALI NEMA `aria-expanded` atribut (IMP-3).
- `[MUST] test_header_includes_language_switcher_nav_partial` — HTML sadrži novi `language_switcher_nav.html` rendered output (CRITICAL-1 — `<form action="{% url 'set_language' %}">` × 3 sa `<button type="submit">`).
- `[MUST] test_language_switcher_nav_has_aria_current_on_current_locale` — Rendered HTML ima `aria-current="page"` na buttonu za trenutni `LANGUAGE_CODE` i NEMA na ostalima (CRITICAL-2).
- `[MUST] test_language_switcher_nav_no_inline_onchange` — `language_switcher_nav.html` source nema `onchange=`, `onclick=`, `onsubmit=` atribute (CRITICAL-1).
- `[MUST] test_header_renders_logo_with_alt_text` — `<img alt="Ćorić Agrar">` postoji.
- `[SHOULD] test_header_logo_uses_core_home_url` — Rendered HTML sadrži `href="/sr/"` ili equivalent rezultat `{% url 'core:home' %}` (CRITICAL-9; SHOULD jer Django routing var je locale-dependent — full validation u Story 9.8 multi-locale routing).
- `[MUST] test_header_html_grep_url_core_home` — `header.html` source grep za `{% url 'core:home' %}`; grep negative za `{% url 'home' %}` bez namespace-a.
- `[MUST] test_no_url_home_without_namespace_in_all_chrome_files` — IMP-CASCADE-10 iter 2 broadened scope: grep `header.html` + `footer.html` + `base.html` (NE samo header.html) negative za `{% url 'home' %}` bez namespace-a; positive grep za `{% url 'core:home' %}` (gde god se home pominje). Razlog: home URL link može biti i u footer-u (logo footer kolone) i u base.html (skip link target nije home, ali aria_live/footer/header includes mogu sadržati home reference); broaden scope eliminiše blind spot.
- `[SHOULD] test_header_navlinks_have_uppercase_class_or_inline_css` — verifikacija kroz CSS file content, ne render (CSS chain).
- `[MUST] test_header_html_no_coric_site_header_wrapper` — `header.html` source NEMA `<header class="coric-site-header">` wrapper (CRITICAL-7 flatten Option A — top-header i nav su siblings na template root).
- `[MUST] test_logo_assets_present` — `static/img/coric-agrar-logo-transp-200.png` i `static/img/coric-agrar-logo-transp-light-200.png` postoje na disku (CRITICAL-8).

**Footer rendering (AC7):**
- `[MUST] test_footer_renders_4_columns` — HTML sadrži 4 `<div class="col-md-3">` u `.coric-footer__top`.
- `[MUST] test_footer_renders_logo_in_column_1` — Kolona 1 ima `<img>`.
- `[MUST] test_footer_renders_slogan` — HTML sadrži "Prijatelj koji razume zemlju!".
- `[MUST] test_footer_includes_section_eyebrow_proizvodi` — Kolona 2 sadrži section_eyebrow output sa text="PROIZVODI".
- `[MUST] test_footer_includes_section_eyebrow_najnovije_vesti` — Kolona 3 sadrži section_eyebrow output sa text="NAJNOVIJE VESTI".
- `[MUST] test_footer_includes_section_eyebrow_kontakt` — Kolona 4 sadrži section_eyebrow output sa text="KONTAKT".
- `[MUST] test_footer_section_eyebrow_uses_on_dark_variant` — sve 3 section_eyebrow konzumacije imaju `variant="on-dark"`.
- `[MUST] test_footer_renders_lorem_ipsum_news_placeholder` — Kolona 3 sadrži "Lorem ipsum" × 3.
- `[MUST] test_footer_renders_todo_comment_for_blog_replacement` — `footer.html` source sadrži `TODO: Story 5.4` HTML komentar.
- `[MUST] test_footer_renders_copyright_2026` — HTML sadrži "© 2026 Ćorić Agrar".
- `[MUST] test_footer_renders_separator_hr` — HTML sadrži `<hr class="coric-footer__separator">`.
- `[MUST] test_footer_has_role_contentinfo` — `<footer role="contentinfo">`.
- `[SHOULD] test_footer_renders_social_links_with_aria_label` — `<a aria-label="Facebook">` + `<a aria-label="Instagram">`.
- `[SHOULD] test_footer_address_has_display_inline_reset` — grep `footer.css` za `.coric-footer__contact address { display: inline` rule presence (BONUS-3 iter 3 — verifikuje da browser default `<address>` block + italic + 1em margin override-uje resetom da address renderuje inline u `<li>` flow-u sa drugim kontakt linkovima).

**Sticky nav JS (AC5):**
- `[MUST] test_sticky_nav_js_uses_intersection_observer` — fajl sadrži substring `IntersectionObserver`.
- `[MUST] test_sticky_nav_js_uses_iife_pattern` — fajl počinje sa `(function ()` ili `(() =>`.
- `[MUST] test_sticky_nav_js_has_defensive_guard_for_intersection_observer` — fajl sadrži `'IntersectionObserver' in window` ili equivalent.
- `[MUST] test_sticky_nav_js_no_window_pollution` — grep negative za `window\.\w+\s*=` (regex, izbegavajući `window.matchMedia` callove).
- `[MUST] test_sticky_nav_js_no_jquery` — grep negative za `\$(`.
- `[MUST] test_sticky_nav_js_no_console_log` — grep negative za `console\.log`.
- `[MUST] test_sticky_nav_js_uses_matchmedia_for_mobile_bail` — grep za `matchMedia.*max-width.*767`.
- `[MUST] test_sticky_nav_js_has_matchmedia_change_listener` — grep za `mobileQuery.addEventListener('change'` (IMP-1).
- `[MUST] test_sticky_nav_js_toggles_body_class` — grep za `document.body.classList.toggle('coric-nav-shrunk'` (IMP-10 — verifikuje Decision D13 wiring).

**Sticky nav CSS (AC5):**
- `[MUST] test_sticky_nav_css_has_prefers_reduced_motion_override` — grep za `@media (prefers-reduced-motion: reduce)`.
- `[MUST] test_sticky_nav_css_reduced_motion_disables_visibility_transition` — POLISH-3 iter 3: grep `sticky-nav.css` za `body.coric-nav-shrunk .coric-top-header { transition: none }` UNUTAR `@media (prefers-reduced-motion: reduce)` blok-a. Verifikuje da u reduced-motion mode-u visibility takođe instant-flips bez 200ms delay-a (kombinacija WCAG 2.4.7 tab order + reduced-motion respect).
- `[MUST] test_sticky_nav_css_defines_shrunk_state` — grep za `.coric-nav--shrunk { ... height: 60px`.
- `[MUST] test_sticky_nav_css_uses_shadow_nav_shrunk_token` — grep za `var(--shadow-nav-shrunk)`.
- `[MUST] test_sticky_nav_css_collapses_top_header_via_height_zero` — grep za `body.coric-nav-shrunk .coric-top-header { height: 0` (CRITICAL-11 + D16: NO `display: none`; height-0 transition).
- `[MUST] test_sticky_nav_css_has_body_position_relative` — grep za `body { position: relative` ili equivalent (CRITICAL-6).
- `[MUST] test_sticky_nav_css_disables_sentinel_on_mobile` — grep za `@media (max-width: 767px) { .coric-sticky-sentinel { display: none`.
- `[MUST] test_header_css_nav_z_index_is_1020` — grep `header.css` za `z-index: 1020` na `.coric-nav` (CRITICAL-12); grep negative za `z-index: 1000`.
- `[SHOULD] test_header_css_has_safari_focus_visible_fallback` — grep za `@supports selector(:focus-visible)` blok u header.css (IMP-5).

**A11y (AC8):**
- `[MUST] test_header_focus_outlines_use_focus_ring_token` — grep `header.css` za `var(--color-semantic-focus-ring)` + `:focus-visible`.
- `[MUST] test_footer_focus_outlines_use_focus_ring_token` — isto za `footer.css`.
- `[MUST] test_header_css_has_forced_colors_override` — grep za `@media (forced-colors: active)`.
- `[SHOULD] test_footer_css_has_forced_colors_override` — isto.
- `[MUST] test_navbar_links_have_min_height_44px` — grep `header.css` za `min-height: 44px` ili `min-height: 44`.

**Token discipline (AC9):**
- `[MUST] test_header_css_no_hardcoded_hex` — grep negative za `#[0-9a-fA-F]{3,6}` van whitelist-a (CSS keywords).
- `[MUST] test_footer_css_no_hardcoded_hex` — isto.
- `[MUST] test_sticky_nav_css_no_hardcoded_hex` — isto.
- `[MUST] test_header_css_no_hardcoded_px_outside_whitelist` — regex za `\d+px` filterujući whitelist `[1, 2, 44, 60, 80, 40, 56, 100, 120]`.
- `[MUST] test_footer_css_no_hardcoded_px_outside_whitelist` — isto.
- `[MUST] test_sticky_nav_css_no_hardcoded_px_outside_whitelist` — isto.
- `[MUST] test_css_no_unitless_magic_numbers_outside_whitelist` — grep negative za unitless `\d{3,4}\s*[;}]` u CSS-u; whitelist je `[1020]` (z-index). CRITICAL-12 split.
- `[MUST] test_no_inline_style_attribute_in_NEW_partials` — grep negative `style="` u SVIM NOVIM fajlovima: `header.html`, `footer.html`, `language_switcher_nav.html` (scope STROGO na NEW; Story 1.4 `language_switcher.html` known CSP debt).
- `[MUST] test_no_inline_handler_in_NEW_partials` — grep negative za `onclick=`, `onchange=`, `onsubmit=`, `onload=` u SVIM NOVIM fajlovima Story 1.8.
- `[MUST] test_no_inline_script_in_NEW_partials` — grep negative `<script` u `header.html`, `footer.html`, `language_switcher_nav.html`.
- `[MUST] test_no_cyrillic_in_new_files` — grep regex `[Ѐ-ӿ]` na svim novim fajlovima.

**Base template integration (AC1, AC10):**
- `[MUST] test_base_html_includes_header_partial` — `base.html` source sadrži `{% include "partials/header.html" %}`.
- `[MUST] test_base_html_includes_footer_partial` — `base.html` source sadrži `{% include "partials/footer.html" %}`.
- `[MUST] test_base_html_loads_sticky_nav_script` — `base.html` source sadrži `<script src="{% static 'js/sticky-nav.js' %}" defer>`.
- `[MUST] test_base_html_does_not_have_orphan_language_switcher_include` — `base.html` više nema direct `{% include "partials/language_switcher.html" %}` na top-level header bloku (regression — language switcher je sada interno u header.html kroz `language_switcher_nav.html`).
- `[MUST] test_base_html_sentinel_is_direct_body_child` — `base.html` source sadrži `<div class="coric-sticky-sentinel"` PRE `{% include "partials/header.html" %}` (CRITICAL-5).
- `[MUST] test_base_html_footer_between_main_and_aria_live` — `base.html` source order: `</main>` → `{% include "partials/footer.html" %}` → `{% aria_live %}` (CRITICAL-4).
- `[MUST] test_base_html_skip_link_still_present` — regression sa Story 1.6 — skip link `<a class="visually-hidden-focusable" href="#main-content">` i dalje postoji.
- `[MUST] test_top_header_has_role_banner` — render `header.html` partial → parse HTML → find element sa `role="banner"` (CRITICAL-CASCADE-1 iter 2; assertion: `<div class="coric-top-header" role="banner" ...>` postoji u rendered output-u).
- `[MUST] test_top_header_visibility_hidden_in_shrunk_state` — grep `sticky-nav.css` za `body.coric-nav-shrunk .coric-top-header` blok i validiraj da sadrži `visibility: hidden` deklaraciju (CRITICAL-CASCADE-3 iter 2).
- `[MUST] test_top_header_descendants_not_focusable_when_shrunk` — CSS rule grep test: grep `sticky-nav.css` za `body.coric-nav-shrunk .coric-top-header { ... visibility: hidden` substring; potvrđuje CSS contract koji uklanja `tel:` linkove iz tab order (WCAG 2.4.7).
- `[MUST] test_top_header_has_explicit_height_in_full_state` — grep `header.css` za `.coric-top-header` blok i validiraj da sadrži `height: 40px` deklaraciju (CRITICAL-CASCADE-4 iter 2; bez ove `height: 0` transition u shrunk state NE ANIMIRA).
- `[MUST] test_top_header_mobile_height_auto_override` — grep `sticky-nav.css` za `@media (max-width: 767px)` blok koji sadrži `.coric-top-header { height: auto }` deklaraciju (POLISH-2 iter 3: scope reduced na sticky-nav.css single source; header.css ima samo komentar bez duplikata).
- `[MUST] test_story_1_6_regression_test_updated_for_flatten` — meta test: import `tests.test_base_template`; verifikuj da `test_ac2_skip_link_first_child_of_body` source NE sadrži `src.find("<header>")` više (regression — Story 1.8 CRITICAL-CASCADE-2: Story 1.6 invariant migriran iz "PRE `<header>` tag" u "PRE prvi chrome include"). POLISH-7 iter 3: test takođe verifikuje da se koristi `re.search` umesto literal `.find()`.

**Story 1.7 reuse regression:**
- `[MUST] test_section_eyebrow_partial_still_works_after_story_18` — regression: include sa text="TEST" tag="h2" variant="on-dark" i dalje renderuje očekivani HTML iz Story 1.7 kontrakta 2.4.
- `[SHOULD] test_pill_button_partial_still_works_after_story_18` — regression: include sa variant="secondary" label="Test" href="/test" i dalje renderuje očekivani HTML iz Story 1.7 kontrakta 2.2.

### Coverage cilj

Story 1.8 testovi treba da imaju **≥ 80%** branch coverage za novi kod (verifikuje se na CI u Story 1.9). U praksi: ~50 pytest scenarija na 3 CSS fajla + 2 HTML partial-a + 1 JS fajla treba dati dovoljnu pokrivenost.

### Out-of-scope za testiranje u Story 1.8 (deferred do Story 9.8 Playwright E2E)

- Stvarno scroll ponašanje (`window.scrollTo` + assert klasa promenjena) — Playwright zna ovo, pytest ne.
- Hamburger collapse animation timing (mid-flight CSS transition state) — Playwright pattern.
- Language switcher POST → redirect na novi locale → page state — može i Django test client, ali zahteva Django URLs koje ne postoje u Story 1.8 scope-u.
- Search popup overlay otvaranje (search funkcionalnost deferred do Story 2.13).
- Visual regression (screenshot diff) — Story 9.8.
- Lighthouse a11y skor — Story 1.9 / Story 9.9.
- Cross-browser test (Chrome / Firefox / Safari) — Story 9.8.

## References

- [Epic 1 spec (Story 1.8)](../planning-artifacts/epics.md) — linije 497-509 (verbatim spec)
- [Epic 1 spec (Story 1.7)](../planning-artifacts/epics.md) — linije 483-495 (kontekst reuse komponenata)
- [DESIGN.md](../planning-artifacts/ux-designs/ux-CORIC_AGRAR-2026-05-27/DESIGN.md) — frontmatter (tokens), § Brand & Style, § Colors, § Layout & Spacing, § Elevation, § Conflicts resolved (linije 369-371 footer bg + nav search)
- [EXPERIENCE.md](../planning-artifacts/ux-designs/ux-CORIC_AGRAR-2026-05-27/EXPERIENCE.md) — § Information Architecture (linije 43-77 nav + top header + footer struktura), § Sticky nav (linije 212-217), § Search (linije 219-224), § Lokalizacija switcher (linije 278-282), § Mobile (linije 455-466), § A11y (linije 285-316)
- [PRD](../planning-artifacts/prds/prd-CORIC_AGRAR-2026-05-27/prd.md) — FR-1 (search), FR-30 (footer)
- [project-context.md](../project-context.md) — § Frontend (linije 66-71, no build pipeline), § JavaScript style (linije 333-339), § CSP (linija 675), § Critical Don't-Miss
- [Story 1.4 implementation](./1-4-i18n-setup-sa-locale-url-routing-i-switcher.md) — postojeći language_switcher.html (regression guard)
- [Story 1.6 implementation](./1-6-base-templates-sa-bootstrap-5-htmx-setup.md) — base.html struktura, Bootstrap 5 + HTMX vendor setup
- [Story 1.7 implementation](./1-7-reusable-visual-komponente.md) — Pill Button (§ AC3) + Section Eyebrow (§ AC5) kontrakti
- [Story 1.7 interface contract](./1-7-interface-contract.md) — § 2.2 Pill Button include sintaksa, § 2.4 Section Eyebrow include sintaksa (`variant="on-dark"`)
- [Mockup HTML](../../docs/Dizajn/_HTML/index.html) — referenca za nav, top-bar, footer struktura (NE kopirati 1:1 — vidi sticky implementaciju na bazi `window.scrollY` u customs.js linija 1-14 — to je anti-pattern; mi koristimo IntersectionObserver)
- [Mockup style.css](../../docs/Dizajn/_HTML/css/style.css) — referenca za `.site-header.sticky` ponašanje (linije 6-18)

---

## Changelog

- **2026-05-28: Iter 1 fix — 12 CRITICAL + 10 IMPROVEMENT addressed:**
  - **CRITICAL-1:** `language_switcher_nav.html` mandated (resolves CSP + AC4) — novi partial sa `<form>` per locale + `<button type="submit">` + `aria-current="page"`; Story 1.4 `language_switcher.html` ostaje netaknut kao known CSP debt.
  - **CRITICAL-2:** Resolved by CRITICAL-1 Option A (novi partial podržava per-link `aria-current="page"`).
  - **CRITICAL-3:** `navbar-expand-lg` → `navbar-expand-md` (AC3 line consistent sa D5/skeleton/Task; EXPERIENCE.md mandira <768px hamburger).
  - **CRITICAL-4:** Footer placement kanonski — `</main>` → `<footer>` → `{% aria_live %}` → `<noscript>` → scripts (AC1 + Task 5.3 align).
  - **CRITICAL-5:** Sentinel premestena u base.html kao direct child `<body>` PRE include header.html (NIJE u header.html); sprečava observer signal loss kad top-header collapses.
  - **CRITICAL-6:** `body { position: relative; }` dodato u sticky-nav.css; daje sentinel positioned containing block.
  - **CRITICAL-7:** Struktura flattened — `<header class="coric-site-header">` wrapper eliminisan; `.coric-top-header` i `<nav class="coric-nav">` su sada DVA SIBLINGS na template root; nav sticky containing block postaje `<body>`.
  - **CRITICAL-8:** Logo provisioning task dodat — `mkdir static/img/` + kopirati `coric-agrar-logo-transp-200.png` i `coric-agrar-logo-transp-light-200.png` iz `docs/Dizajn/_HTML/img/`.
  - **CRITICAL-9:** URL namespace ispravljeno na `{% url 'core:home' %}` (verified `apps/core/urls.py` ima `app_name = 'core'`); fallback wording uklonjen.
  - **CRITICAL-10:** Bootstrap defer rationale ispravljen — bootstrap_javascript je SYNC (verified base.html line 34 komentar); korektan ordering: bootstrap.sync executes during parse → DCL fires → htmx + sticky-nav defer execute after DCL.
  - **CRITICAL-11:** D16 promoted in-scope — CLS regression preventovana sa `height: 0; padding: 0; overflow: hidden` transition umesto `display: none`.
  - **CRITICAL-12:** Z-index moved to 1020 (above Bootstrap dropdown 1000 + popover 1010, below modal 1055); AC9 whitelist split into px vs unitless magic numbers.
  - **IMP-1:** `mobileQuery.addEventListener('change', syncObserver)` dodat u sticky-nav.js za resize/orientation handling.
  - **IMP-2:** `<address>` → `<p class="coric-top-header__address">` (HTML5 semantic correctness; `<address>` rezervisan za nearest `<article>`/`<body>` contact info).
  - **IMP-3:** `aria-expanded` uklonjen sa search button-a (no functional toggle yet — wiring stiže u Story 2.13).
  - **IMP-4:** `service_phone` undefined var fiksiran — hardkoderan placeholder `+381 XXX XXX XXX` u v1 sa TODO Story 8.x SiteSettings replacement.
  - **IMP-5:** Safari 14 `:focus, :focus-visible` dual-selector dodat sa `@supports selector(:focus-visible)` block; reset za modern + fallback za Safari <15.4.
  - **IMP-6:** Task 9.4 pill button test refaktorisan u opt-in fixture sa `@pytest.mark.skipif(not USE_PILL_BUTTON_IN_NAV)` (D15 default je not used).
  - **IMP-7:** Interface contract `1-8-interface-contract.md` mandated (strongly recommended) — Strategy A imports, parameter tables, BEM classes, token manifest.
  - **IMP-8:** Reuse claim tightened — opening paragraph clarifies Story 1.7 reuse is **Section Eyebrow primary + Pill Button optional**, ne svih 5 komponenata.
  - **IMP-9:** Hardcoded constants formally named (NAV_HEIGHT_FULL, LOGO_HEIGHT_SHRUNK, STICKY_SENTINEL_OFFSET, NAV_Z_INDEX, itd.) u Dev Notes subsekciji.
  - **IMP-10:** `test_sticky_nav_js_toggles_body_class` test scenario dodat za Decision D13 wiring verification.
  - **Style notes (logged):** Mehanizacija dropdown only-dropdown note, sentinel `tabindex="-1"` defensive, `©` Unicode safety, scroll-restoration mid-scroll edge case documented.

- **2026-05-28: Iter 2 fix — 5 CASCADE CRITICAL + 12 IMPROVEMENT-CASCADE addressed (cascade rezultat iter 1 flatten + height-0 strategy):**
  - **CRITICAL-CASCADE-1:** ARIA `banner` landmark restoration — iter 1 flatten Option A je uklonio `<header class="coric-site-header">` wrapper koji je default banner; iter 2 dodaje eksplicitan `role="banner"` na `.coric-top-header` div (uz `aria-label="Kontakt informacije"`). Propagated u AC2, AC8, Task 2.2, header.html skeleton, Decision D17, test scenarios (`test_top_header_has_role_banner`), Anti-pattern korigovan.
  - **CRITICAL-CASCADE-2:** Story 1.6 regression test invariant migration — `tests/test_base_template.py::test_ac2_skip_link_first_child_of_body` hard-asserts `<header>` u base.html (linija 378, 383); posle Task 5.1 remove + flatten Option A ovaj assert FAIL-uje. Story 1.8 deliverable sada uključuje NOV Task 10a koji UPDATE-uje regression test (assert pattern menja se sa `src.find("<header>")` na `src.find('{% include "partials/header.html" %}')`); empirijski potvrđeno čitanjem testa pre apliciranja fixa. Propagated u AC10 + Task 10a + Testing scenarios.
  - **CRITICAL-CASCADE-3:** Shrunk-state focusable descendants fix — `height: 0; overflow: hidden` NE uklanja `<a href="tel:...">` linkove iz tab order (WCAG 2.4.7 + 2.4.11 failure). Solution Option A (CSS-only): dodato `visibility: hidden` u shrunk state SA `transition-delay: 200ms` da flips POSLE height tranzicije; pair sa `visibility: visible` u full state. Anti-pattern #12 ispravljen (bivša false claim o `overflow:hidden` tab order pattern-u). Propagated u AC2, AC5, Task 2.7, Task 3.6, sticky-nav.css skeleton, header.css skeleton, test scenarios (`test_top_header_visibility_hidden_in_shrunk_state`, `test_top_header_descendants_not_focusable_when_shrunk`).
  - **CRITICAL-CASCADE-4:** Explicit `.coric-top-header { height: 40px }` u full state — iter 1 je tvrdio CSS animation iz `auto` u `0` što ne radi (CSS limitation). Iter 2 dodaje eksplicitnu `height: 40px` u full state (IMP-9 hardcoded constant) + mobile override `@media (max-width: 767px) { .coric-top-header { height: auto } }`. Propagated u AC2, Task 2.7, Task 6.1, sticky-nav.css skeleton mobile media query, test scenarios (`test_top_header_has_explicit_height_in_full_state`, `test_top_header_mobile_height_auto_override`).
  - **CRITICAL-CASCADE-5:** Accept-with-tradeoffs CLS dokumentacija — aspirational zero-CLS claim je tehnički netačan jer top-header collapse menja document height za 40px na svakom scroll past 100px. Iter 2 dodaje NOVU Dev Notes subsekciju "Acceptable Layout Behavior — Scroll-Threshold Reflow" sa: observed behavior + CWV grace window mitigation + 3 alternative rejected (body padding-top, position absolute, revert flatten) + verify-in-Story-1.9 plan. Wording zero-CLS zamenjen sa "CLS impact minimized via smooth transition + scroll input grace window; pending Story 1.9 verification" na svim mestima. Propagated u Decision D16, AC5/AC2 text, Anti-pattern #11, Performance & a11y must-haves subsekciji.
  - **IMP-CASCADE-1:** Task 8.3 file count fix — "2 nova HTML fajla" → "3 nova HTML/Django partial-a (header.html, footer.html, language_switcher_nav.html)"; propagated u AC9.
  - **IMP-CASCADE-2:** `aria-current="page"` semantic — GOV.UK precedent rationale dodat u AC4 (NVDA/JAWS najavljuju identično za `page` i `true`; `page` je semantic-richer za multi-page).
  - **IMP-CASCADE-3:** 3× CSRF tokens cost dokumentovan — Dev Notes "Known minor cost" dodat u AC4 sa ~450 bytes/page payload bloat + simplicity-vs-complexity tradeoff per D3.
  - **IMP-CASCADE-4:** `<address>` semantic split documentation — Dev Notes section "`<address>` semantic split — top-header vs footer" dodata; footer `<address>` canonical per HTML5, top-header `<p>` redundant nav chrome.
  - **IMP-CASCADE-5:** language_switcher_nav.html context contract — Dev Notes "Interface contract — language_switcher_nav.html context" subsekcija dodata sa Required context (request, LANGUAGE_CODE) + Provided by (context processors).
  - **IMP-CASCADE-6:** Decision D18 dodato — language switcher form factor change od `<select>` (Story 1.4) u horizontal `<button>` list per locale; UX implication dokumentovano (vizuelni delta od Story 1.4 baseline).
  - **IMP-CASCADE-7:** AC9 whitelist `1000` stale uklonjen — Task 8.2 enumeration ažurirana sa `[1, 2, 44, 60, 80, 40, 56, 100, 120]`; `1000` (stara z-index vrednost) uklonjen jer je sada `1020` u unitless whitelist-u.
  - **IMP-CASCADE-8:** Mehanizacija dropdown `<a>` vs `<button>` Dev Notes — Bootstrap 5 konvencija accepted u v1; preporuka `<button>` za buduće dropdown stories.
  - **IMP-CASCADE-9:** `body { position: relative }` documentation — dodato u Dev Notes "Project-wide invariants" subsekciju + interface contract; future stories upozorenje za `position: absolute` na body level.
  - **IMP-CASCADE-10:** Test grep scope broaden — `test_no_url_home_without_namespace_in_all_chrome_files` dodat; grep scope proširen na header.html + footer.html + base.html (NE samo header.html).
  - **IMP-CASCADE-11:** Mid-scroll dropdown race + 2 dodatna edge case-a — Dev Notes "Known visual edge cases" subsekcija dodata; Playwright snapshot deferred to Story 9.8.
  - **IMP-CASCADE-12:** `tabindex="-1"` na sentinel UKLONJEN — `<div>` je po default-u NE-focusable; `tabindex="-1"` je suvišan; cleaner aligned sa Anti-pattern #12; propagated na 3 mesta (AC1 line 67, Task 3.5, Task 5.2 skeleton).
  - **Architectural decision log iter 2:** Iter 2 strategy je RESTORE-WHERE-POSSIBLE bez re-uvođenja originalno-rešenih bug-ova. Specifično: (a) ARIA banner landmark restored via eksplicitan `role="banner"` atribut umesto re-introduction `<header>` wrapper-a koji bi vratio sticky-scroll-away bug; (b) shrunk state tab order fix via `visibility: hidden` umesto `display: none` (koji bi izazvao CLS) ili `inert` attribute (dodatna JS kompleksnost); (c) explicit `height: 40px` umesto `height: auto` da animation radi, bez gubljenja mobile variable-height fleksibilnosti (mobile override `@media (max-width: 767px) { height: auto }`); (d) Story 1.6 regression test sada EXPLICIT scope item Story 1.8 deliverable-a umesto čekanja Story 1.6 revisit; (e) CLS accept-with-tradeoffs dokumentacija zamenjuje aspirational zero-CLS claim sa realistic CWV grace-window-mitigation strategy + Lighthouse verification plan u Story 1.9. **Princip:** taktičke pravke + ARHITEKTURALNI INVARIANT RESTORATION (a11y + regression + WCAG + animation) bez retreat-a od iter 1 flatten benefits (sticky containing block fix).

- **2026-05-28: Iter 3 fix — 10 POLISH IMPROVEMENT + 3 BONUS polish convergence (NO cascade fixes; NO architectural changes):**
  - **Strategy:** TARGETED POLISH — iter 3 fokus na izlaganje već-rešenih nuansi + browser compat fix + missing test scenarios. NO architectural changes; iter 1 + iter 2 su strukturalno rešili sve velike probleme. Iter 3 dovodi PASS od svih 3 reviewer-a tako da loop legitimno exit-uje.
  - **POLISH-1:** Browser minimum bumped sa "Safari 14+" na "Safari 14.1+" (Safari 14.0 ima WebKit bug sa `visibility` tranzicijom + `transition-delay` koji blokira CRITICAL-CASCADE-3 pattern; fixed u 14.1 release). Propagated u Dev Notes Tech stack baseline + sticky-nav.js IIFE komentar.
  - **POLISH-2:** Duplicate mobile `.coric-top-header { height: auto }` override uklonjen iz header.css skeleton-a; sticky-nav.css je canonical owner shrunk-state behavior + mobile bypass per D4. Header.css ima samo inline komentar; sticky-nav.css media query block ostaje single source. Task 6.1 ažurirana sa cross-reference napomenom.
  - **POLISH-3:** Test scenario `test_sticky_nav_css_reduced_motion_disables_visibility_transition` dodat — verifikuje da u `@media (prefers-reduced-motion: reduce)` mode-u visibility takođe instant-flips bez 200ms delay-a (kombinacija WCAG 2.4.7 + reduced-motion respect). Dodat u Task 9.11a + Testing section.
  - **POLISH-4:** Task 10.3 manual sign-off checklist proširen sa AT landmark smoke test bullet point-om (NVDA D-key / JAWS `;` / `R` shortcut) — verifikuje 1 banner + 1 navigation + 1 main + 1 contentinfo landmark u landmark menu; banner disappears u shrunk state (acceptable per CRITICAL-CASCADE-3 + POLISH-6 dokumentacija).
  - **POLISH-5:** "Tab-during-collapse 200ms race" edge case dodat u Known visual edge cases sekciju — fokus tokom 200ms height transition može sleteti na compressed `tel:` link; transient WCAG 2.4.11 (Focus Not Obscured) edge case sa rejected JS `inert` + instant `visibility:hidden` alternative-ima.
  - **POLISH-6:** NOVA "Acceptable A11y Behavior — Banner Landmark Lifecycle" Dev Notes subsekcija — dokumentuje da `role="banner"` landmark namerno disappear-uje iz a11y tree-a u shrunk state-u (jer `visibility: hidden` uklanja element); banner re-appears na scroll-up. Unconventional ali better-than-alternatives (keeping content focusable failed CRITICAL-CASCADE-3; re-introducing `<header>` wrapper-a re-uvodi CRITICAL-7).
  - **POLISH-7:** Task 10a.1 (Story 1.6 regression test update) pattern menjao iz literal `src.find('{% include "partials/header.html" %}')` u regex `re.search(r'\{%\s*include\s*[\'"]partials/header\.html[\'"]\s*%\}', src)` za resilience na whitespace + jednostruke/dvostruke navodnike + linije-breaks unutar tag-a.
  - **POLISH-8:** Decision D18 proširen — Story 1.4 `language_switcher.html` orphan status eksplicitan: "on-disk regression guard only" (Story 1.4 testovi i dalje pasuju) ali NIJE rendered u v1 published surface-u (Story 1.8 uklanja `<header>` include iz base.html). Future Story 8.x admin ili 9.x CSP rollout može revisit partial.
  - **POLISH-9:** AC4 CSRF cookie cost wording tightened — "~450 bytes/page" sad eksplicitno objašnjeno kao "3× hidden input fields rendering same session-cookie-backed token; cookie sync je per-request not per-form, Django reuses token within RequestContext" (uklanja implicit cookie sync misimplikaciju).
  - **POLISH-10:** Testing section header-u dodat "MUST vs SHOULD" konvencijski note + svi inline scenarios annotirani sa `[MUST]` ili `[SHOULD]` tag-om za jasno razlikovanje Task 9.x explicit subtasks od recommended-coverage scenarios. Annotation rezultat: jasno blocking-vs-non-blocking signal Dev-u + TEA-u za prioritizaciju implementacije.
  - **BONUS-1:** AC2 line wording polish — CSS transition shorthand `visibility 0s linear 0s` parsing inline objašnjeno (duration 0s + delay 0s = "instant flip" pair vrednost full state-a; shrunk state ima delay 200ms — visibility flip POSLE height transition).
  - **BONUS-2:** Footer logo wrapped u `<a href="{% url 'core:home' %}" class="coric-footer__logo-link" aria-label="Početna">` za parity sa header logo-om (konzistentna UX expectation da klik na logo navigira na home). Task 4.3 + footer.html skeleton ažurirani.
  - **BONUS-3:** Task 4.6 proširen sa CSS reset rule-om za `<address>` element unutar `.coric-footer__contact` `<li>` — `display: inline; margin: 0; font-style: normal;` (browser default je block + italic + 1em margin koji bi razbio inline footer list layout).
  - **Architectural decision log iter 3:** Iter 3 strategy je POLISH-ONLY, NO architectural changes. Sva 3 re-validatora iter 3 vraćaju PROCEED (Iter 1 12 CRITICAL + 10 IMPROVEMENT i Iter 2 5 CRITICAL-CASCADE + 12 IMPROVEMENT-CASCADE su strukturalno rešili sve velike probleme); finalna CONCERNS odluka je bila zbog ~10 IMPROVEMENT polish items koje iter 3 sada eksplicitno adresira. Iter 3 NE menja AC count, NE menja Task count beyond polish subtask 9.11a + dodavanje [MUST]/[SHOULD] tagova. **Princip:** legitiman PASS od svih 3 re-validatora kroz dokumentaciju + browser compat fix + missing test scenarios, bez novih structural rizika.

- **2026-05-28: Iter 4 fix — 5 FINAL POLISH items (surgical Validator B convergence target; NO architectural changes):**
  - **Strategy:** SURGICAL — iter 3 dobio PASS od Validator A + Adversarial, ali Validator B drži CONCERNS na 5 LOW items + accepted-tradeoff NEW-2 reflow. Iter 4 cilja samo specifične 5 LOW items koje je Validator B identifikovao da konvergira na PASS od svih 3. NO CRITICAL ili HIGH ostalo posle iter 3. NO architectural restructure ili cascade fix. NEW-2 (40px main reflow on scroll) je accepted-tradeoff dokumentovan u iter 2 CRITICAL-CASCADE-5 sa Story 1.9 Lighthouse verification gate — NE menja se arhitektura.
  - **FINAL-1 (POLISH-2 verbose comment reduction):** header.css skeleton 3-line cross-reference comment block reduced to ONE-LINE inline comment `/* Mobile height: auto override in sticky-nav.css (single-source). */` per project-context.md § Comments policy "Default: nema komentara; samo za WHY koji nije očigledan".
  - **FINAL-2 (Task 2.12 Safari 14 fallback cross-reference):** Task 2.12 dobija 1-line napomenu na kraju: "project minimum bumped to Safari 14.1+ per POLISH-1 (iter 3); ovaj fallback i dalje važi za 14.1, 14.2, 15.0-15.3 koji nemaju :focus-visible until 15.4" — explicit veza između IMP-5 fallback-a i POLISH-1 browser minimum bump-a.
  - **FINAL-3 (BONUS-3 footer address CSS reset test):** test scenario `[SHOULD] test_footer_address_has_display_inline_reset` dodat u Testing section Footer rendering — grep `footer.css` za `.coric-footer__contact address { display: inline` rule presence; corresponding test za BONUS-3 CSS reset koji je iter 3 dodao bez testa.
  - **FINAL-4 (BONUS-1 inline CSS-parsing explanation organization):** CSS shorthand `visibility 0s linear 0s` parsing inline objašnjenje uklonjeno iz AC2 line 93 inline narrative (AC2 sada terser sa canonical CSS rule + cross-reference) i preseljen u NOVU Dev Notes "CSS Transition Shorthand Reference" subsection sa side-by-side full vs shrunk vs reduced-motion table — bolja organizacija dev-notes-level detalja van AC narrative-a.
  - **FINAL-5 (NEW-2 architectural reflow explicit Story 1.7 precedent citation):** CRITICAL-CASCADE-5 "Acceptable Layout Behavior — Scroll-Threshold Reflow" dobija eksplicitan Story 1.7 AC9.10 precedent citation bullet: "Pattern: deferred verification consistent with Story 1.7 AC9.10 (collectstatic hashed-import verification deferred to Story 1.6 vendor cleanup OR Story 1.9 CI prep with @pytest.mark.skip scaffold). Story 1.8 follows same pattern: in-scope verification covers Story 1.8 deliverable surface; CLS / Lighthouse perf empirical verification is downstream (Story 1.9) and not solvable in Story 1.8 scope alone" — makes deferral pattern explicit i aligned sa project precedent-om za Validator B context.
  - **Architectural decision log iter 4:** Iter 4 strategy je SURGICAL FINAL POLISH — ZERO architectural changes, ZERO cascade fixes, ZERO new AC additions, ZERO new Tasks. Samo 5 surgical fixes (1 comment reduction + 1 cross-reference + 1 test scenario + 1 reorganization + 1 precedent citation). **Validator B convergence target:** accepted-tradeoff NEW-2 (architectural main reflow) je sada explicitly contextualized sa Story 1.7 AC9.10 deferral precedent + all 5 LOW items resolved. **Princip:** finalna surgical convergencija ka PASS od svih 3 reviewer-a u iter 5 re-val bez ikakvog novog structural rizika ili gold-plating-a.

---

**End of Story 1.8 — Sticky Nav + Top Header + Footer + Language Switcher Partial**
