---
story-id: "1.8"
story-key: 1-8-sticky-nav-top-header-footer-language-switcher-partial
title: Interface Contract — Sticky Nav + Top Header + Footer + Language Switcher Partial
status: contract
created: 2026-05-28
last_modified: 2026-05-28
author: TEA (RED phase)
---

# Story 1.8 — Interface Contract

This contract is the canonical specification for Story 1.8 artifacts. The TEA RED-phase test
suite `tests/test_navigation_chrome.py` directly encodes the assertions defined here. Dev
MUST satisfy this contract to ship Story 1.8 GREEN.

## 1. Artifact inventory

### 1.1 New template partials (3)
| Path | Purpose |
|---|---|
| `templates/partials/header.html` | Top header (`.coric-top-header`) + main nav (`<nav class="coric-nav">`) as TWO SIBLINGS on template root (CRITICAL-7 flatten Option A; no `<header class="coric-site-header">` wrapper). |
| `templates/partials/footer.html` | Footer (`<footer role="contentinfo">`) with 4 columns + section eyebrow headings + copyright separator. |
| `templates/partials/language_switcher_nav.html` | Nav-specific language switcher with `<form>`-per-locale + `<button type="submit">` + `aria-current="page"` on current locale (CSP-friendly; CRITICAL-1 fix). |

### 1.2 New JavaScript files (1)
| Path | Purpose |
|---|---|
| `static/js/sticky-nav.js` | Vanilla JS IIFE module — IntersectionObserver-based sticky shrink-on-scroll. Toggles `.coric-nav--shrunk` on `.coric-nav` and `coric-nav-shrunk` on `<body>`. No global pollution, defensive guards, matchMedia mobile bail + change listener. |

### 1.3 New CSS files (3)
| Path | Purpose |
|---|---|
| `static/css/components/header.css` | Top header + nav styling (green-900/800 bg, sticky position, focus rings, Safari 14 fallback, forced-colors override). |
| `static/css/components/footer.css` | Footer styling (green-800 bg, 4 columns, separator, copyright, address inline reset). |
| `static/css/components/sticky-nav.css` | `body { position: relative }` + sentinel positioning + shrunk-state rules + reduced-motion + mobile bail. |

### 1.4 New logo assets (2)
| Path | Source |
|---|---|
| `static/img/coric-agrar-logo-transp-200.png` | `docs/Dizajn/_HTML/img/coric-agrar-logo-transp-200.png` (provisioned by Task 1.10). |
| `static/img/coric-agrar-logo-transp-light-200.png` | `docs/Dizajn/_HTML/img/coric-agrar-logo-transp-light-200.png` (provisioned by Task 1.10). |

### 1.5 Modified files (2)
| Path | Modifications |
|---|---|
| `templates/base.html` | (a) Remove `<header>{% include "partials/language_switcher.html" %}</header>` block. (b) Insert sentinel `<div class="coric-sticky-sentinel" aria-hidden="true"></div>` as direct child `<body>` BEFORE `{% include "partials/header.html" %}`. (c) Insert `{% include "partials/header.html" %}` after sentinel, BEFORE `<main>`. (d) Insert `{% include "partials/footer.html" %}` AFTER `</main>` and BEFORE `{% aria_live %}`. (e) Insert `<script src="{% static 'js/sticky-nav.js' %}" defer></script>` AFTER `{% bootstrap_javascript %}`. |
| `static/css/main.css` | Append 3 new `@import url('./components/...')` lines for `header.css`, `footer.css`, `sticky-nav.css`. |
| `tests/test_base_template.py` | Task 10a — migrate `test_ac2_skip_link_first_child_of_body` from literal `src.find("<header>")` to `re.search(r'\{%\s*include\s*[\'"]partials/header\.html[\'"]\s*%\}', src)` (POLISH-7 iter 3 regex pattern). |

## 2. Template parameter contracts

### 2.1 `partials/header.html`
- **No parameters** — header reads no context-level vars. All content is `{% translate %}`-localized literals + Bootstrap default classes.
- **Required template tags loaded:** `{% load i18n %}`, `{% load static %}`.
- **Includes:** `{% include "partials/language_switcher_nav.html" %}` (1×, inside nav `<li>`).
- **URL references:** `{% url 'core:home' %}` (logo + Početna link); rest are `href="#"` placeholders.
- **Required context (provided by Django globally):** `request` (for downstream language_switcher_nav), `LANGUAGE_CODE` (i18n context processor).

### 2.2 `partials/footer.html`
- **No parameters** — footer reads no context-level vars in v1.
- **Required template tags loaded:** `{% load i18n %}`, `{% load static %}`.
- **Includes:** `{% include "partials/section_eyebrow.html" with text="..." tag="h2" variant="on-dark" %}` (3× — PROIZVODI, NAJNOVIJE VESTI, KONTAKT).
- **URL references:** `{% url 'core:home' %}` (footer logo link, BONUS-2 iter 3).
- **Lorem Ipsum placeholder:** 3 hardcoded `<li><a href="#">Lorem ipsum dolor sit amet (vest N)</a></li>` items wrapped in TODO comment for Story 5.4.
- **Copyright:** hardcoded "© 2026 Ćorić Agrar" (Decision D8 — `{% now "Y" %}` deferred to Epic 8 SiteSettings).

### 2.3 `partials/language_switcher_nav.html`
- **No call-site parameters** — uses i18n template tags.
- **Required template tags loaded:** `{% load i18n %}`.
- **Required context variables (from Django context processors, Story 1.4):**
  - `request` — for `{{ request.path }}` in hidden `next` input.
  - `LANGUAGE_CODE` — for `aria-current="page"` detection on current locale.
- **Required URL pattern:** `set_language` (provided by `path('i18n/', include('django.conf.urls.i18n'))`, Story 1.4).
- **Markup pattern:** `<ul class="coric-nav__language-switcher" role="list">` with `{% for lang_code, lang_name in available_languages %}` loop emitting one `<li><form action="{% url 'set_language' %}" method="post">...<button type="submit">{{ lang_code|upper }}</button></form></li>` per locale.
- **`aria-current="page"`** rendered only on current locale's button.
- **`aria-label="Prebaci na {{ language }}"`** localized via `{% blocktranslate %}` on each button.
- **CSRF tokens:** 3× `{% csrf_token %}` per page render (one per form) — accepted ~450 bytes/page DOM cost (Decision D3 + POLISH-9 iter 3).

## 3. CSS class contract (BEM)

### 3.1 `.coric-top-header` (header.css)
- `role="banner"` ARIA landmark (CRITICAL-CASCADE-1 iter 2).
- `background-color: var(--color-brand-green-900)`, `color: var(--color-semantic-text-on-dark)`.
- **`height: 40px`** explicit (CRITICAL-CASCADE-4 iter 2 — enables `height: 0` shrunk transition).
- `overflow: hidden`, `visibility: visible`.
- `transition: height 200ms ease, padding 200ms ease, visibility 0s linear 0s`.
- Children: `.coric-top-header__address` (`<p>` not `<address>` per IMP-2), `.coric-top-header__phone`, `.coric-top-header__phone--service`, `.coric-top-header__social`, `.coric-top-header__mobile-toggle`, `.coric-top-header__content`.

### 3.2 `.coric-nav` (header.css)
- `role="navigation"` (set via element + explicit attr).
- `position: sticky; top: 0; z-index: 1020;` (CRITICAL-12).
- `background-color: var(--color-brand-green-800)`, `color: var(--color-semantic-text-on-dark)`.
- `height: 80px` (full state, Decision D1).
- `transition: height 200ms ease, box-shadow 200ms ease`.
- Bootstrap utility classes: `navbar navbar-expand-md` (CRITICAL-3 — NOT `lg`).
- Children: `.coric-nav__logo`, `.coric-nav__logo-img`, `.coric-nav__link`, `.coric-nav__hamburger`, `.coric-nav__search-toggle`, `.coric-nav__dropdown`, `.coric-nav__language-switcher`, `.coric-nav__list`.

### 3.3 `.coric-language-switcher__btn` / `.coric-language-switcher__form` (header.css)
- `background: transparent; color: inherit; border: 0; min-height: 44px; font-weight: bold; text-transform: uppercase;`
- Modifier `.coric-language-switcher__btn--current` — visual indicator (underline/bold) on active locale.

### 3.4 `.coric-footer` (footer.css)
- `role="contentinfo"` (HTML5 default + explicit for older AT).
- `background-color: var(--color-brand-green-800)`, `color: var(--color-semantic-text-on-dark)`.
- `padding: var(--spacing-scale-10) 0 var(--spacing-scale-5) 0`.
- Children: `.coric-footer__top`, `.coric-footer__col`, `.coric-footer__logo-link`, `.coric-footer__logo`, `.coric-footer__slogan`, `.coric-footer__menu`, `.coric-footer__news`, `.coric-footer__contact`, `.coric-footer__social`, `.coric-footer__separator`, `.coric-footer__copyright`, `.coric-footer__bottom`.
- **FINAL-3 reset:** `.coric-footer__contact address { display: inline; margin: 0; font-style: normal; }` (BONUS-3 iter 3).

### 3.5 `.coric-sticky-sentinel` (sticky-nav.css)
- `position: absolute; top: 100px; left: 0; width: 1px; height: 1px; pointer-events: none;`
- HTML attrs: `aria-hidden="true"` (no `tabindex` — IMP-CASCADE-12 iter 2: `<div>` is non-focusable by default).
- Mobile bypass: `@media (max-width: 767px) { .coric-sticky-sentinel { display: none } }` (Decision D4).

### 3.6 Shrunk-state rules (sticky-nav.css)
- `.coric-nav--shrunk { height: 60px; box-shadow: var(--shadow-nav-shrunk); }`
- `.coric-nav--shrunk .coric-nav__logo-img { max-height: 40px; }`
- `.coric-nav__logo-img { max-height: 56px; transition: max-height 200ms ease; }`
- `body.coric-nav-shrunk .coric-top-header { height: 0; padding-top: 0; padding-bottom: 0; visibility: hidden; transition: height 200ms ease, padding 200ms ease, visibility 0s linear 200ms; }` (CRITICAL-11 + CRITICAL-CASCADE-3).

### 3.7 Reduced-motion override (sticky-nav.css)
```css
@media (prefers-reduced-motion: reduce) {
  .coric-nav,
  .coric-nav__logo-img,
  .coric-top-header { transition: none; }
  body.coric-nav-shrunk .coric-top-header { transition: none; } /* POLISH-3 iter 3 */
}
```

### 3.8 Mobile bypass (sticky-nav.css — single source per POLISH-2)
```css
@media (max-width: 767px) {
  .coric-sticky-sentinel { display: none; }
  .coric-top-header { height: auto; }
}
```

## 4. `sticky-nav.js` contract

### 4.1 Structural requirements
- **IIFE wrapper:** `(function () { 'use strict'; ... })();` (NOT named function, NOT module export).
- **No global window pollution:** zero matches for regex `window\.\w+\s*=` (excluding `window.matchMedia(...)` callsite where `matchMedia` is a read-only API access, not assignment).
- **No jQuery:** zero matches for `\$\(` or `jQuery`.
- **No production console:** zero matches for `console.log` (debugging strip per Anti-pattern #7).

### 4.2 Defensive guards
- `if (typeof window === 'undefined' || !('IntersectionObserver' in window)) { return; }` — bail on missing API.
- `if (!nav || !sentinel) { return; }` — bail if DOM nodes missing.

### 4.3 IntersectionObserver wiring
- Observer target: `document.querySelector('.coric-sticky-sentinel')`.
- Observer callback: toggles `.coric-nav--shrunk` on nav element AND `coric-nav-shrunk` on `document.body` (Decision D13).
- Options: `{ rootMargin: '0px', threshold: 0 }`.
- Callback substring: `document.body.classList.toggle('coric-nav-shrunk'` (IMP-10).

### 4.4 Mobile matchMedia bail + change listener (IMP-1)
- `const mobileQuery = window.matchMedia('(max-width: 767px)');`
- `syncObserver()` function:
  - If mobile → `observer.disconnect()` + remove `coric-nav--shrunk` + remove `coric-nav-shrunk` body class.
  - If desktop → `observer.observe(sentinel)`.
- `mobileQuery.addEventListener('change', syncObserver);` — re-init/teardown on orientation change.
- Initial call: `syncObserver();` before listener registration.

## 5. `base.html` structural modifications

### 5.1 Canonical body structure (post-modification)
```
<body>
  <a class="visually-hidden-focusable" href="#main-content">...</a>     ← Story 1.6 skip link
  <div class="coric-sticky-sentinel" aria-hidden="true"></div>          ← NEW (Story 1.8 sentinel)
  {% include "partials/header.html" %}                                  ← NEW (Story 1.8 chrome)
  <main id="main-content" tabindex="-1">...</main>                      ← Story 1.6
  {% include "partials/footer.html" %}                                  ← NEW (Story 1.8 footer)
  {% aria_live %}                                                       ← Story 1.6
  <noscript>...</noscript>                                              ← Story 1.6
  <script src="{% static 'vendor/htmx.min.js' %}" defer></script>       ← Story 1.6
  {% bootstrap_javascript %}                                            ← Story 1.6 (SYNC)
  <script src="{% static 'js/sticky-nav.js' %}" defer></script>         ← NEW (Story 1.8)
  {% block scripts %}{% endblock %}                                     ← Story 1.6
</body>
```

### 5.2 Removed elements
- `<header>{% include "partials/language_switcher.html" %}</header>` — REMOVED (language switcher now rendered inside `header.html` via `language_switcher_nav.html`).

## 6. Story 1.6 regression test update (Task 10a)

`tests/test_base_template.py::test_ac2_skip_link_first_child_of_body` must be migrated from
literal `src.find("<header>")` to regex pattern `re.search(r'\{%\s*include\s*[\'"]partials/header\.html[\'"]\s*%\}', src)`
(POLISH-7 iter 3). Updated assertion order: `body_open_idx < skip_link_idx < header_include_idx`.
This is **deliverable in Story 1.8 scope** (CRITICAL-CASCADE-2 iter 2).

The test:
- Must use `re.search` (not `.find()` literal).
- Must search for `{% include "partials/header.html" %}` pattern (whitespace-tolerant, quote-tolerant).
- Must assert `body_open < skip_link < coric_top_header_include_idx`.
- Must NOT assert `<header>` tag presence (Story 1.8 flatten removes wrapper).

## 7. Cross-component invariants

1. **No inline `style="..."`** in the 3 new partials (`header.html`, `footer.html`, `language_switcher_nav.html`). Story 1.4 `language_switcher.html` is out-of-scope (known CSP debt deferred to Story 1.9/8.x).
2. **No inline event handlers** (`onclick=`, `onchange=`, `onsubmit=`, `onload=`) in the 3 new partials.
3. **No inline `<script>` tags** in the 3 new partials.
4. **No hardcoded hex** (`#XXX`, `#XXXXXX`) in the 3 new CSS files. Exception whitelist: `transparent`, `inherit`, `currentColor`, named CSS keyword `white` (rare use only in `rgba(255, 255, 255, ...)` for footer separator per Decision D9).
5. **No hardcoded `rgb(...)`/`hsl(...)`** with numeric literals in 3 new CSS files. Exception: `rgba(255, 255, 255, 0.2)` for `.coric-footer__separator` (Decision D9).
6. **No hardcoded `\d+px` outside whitelist** `[1, 2, 44, 60, 80, 40, 56, 100, 120]` in 3 new CSS files.
7. **No hardcoded unitless magic numbers outside whitelist** `[1020]` (`.coric-nav` z-index).
8. **No Cyrillic characters** (regex `[Ѐ-ӿ]`) in any new file.
9. **`body { position: relative }`** must be set in `sticky-nav.css` (CRITICAL-6 — required for sentinel positioning).
10. **`role="banner"`** on `.coric-top-header` div (CRITICAL-CASCADE-1 iter 2 — ARIA landmark after flatten).
11. **`role="navigation"`** on `<nav class="coric-nav">`.
12. **`role="contentinfo"`** on `<footer class="coric-footer">`.
13. **Only 1× `role="banner"` per page** (WAI-ARIA APG compliance).

## 8. Key decisions reference

- **D3** — Create NEW `language_switcher_nav.html` (CSP-safe); Story 1.4 `language_switcher.html` remains as orphan (POLISH-8).
- **D13** — JS toggles `body.coric-nav-shrunk` class (not sibling selector) to enable top-header collapse.
- **D14** — Test file: `tests/test_navigation_chrome.py` (new, cohesive scope).
- **D16** — Top-header shrunk-state collapse via `height: 0 + padding: 0 + visibility: hidden` with transition (not `display: none`; CLS-friendly).
- **D17** — Flatten Option A: no `<header class="coric-site-header">` wrapper; standalone siblings.
- **D18** — Language switcher form factor: horizontal `<button>` list per locale (CSP-safe + WCAG `aria-current` support).

## 9. Token usage manifest

Story 1.8 consumes ~17 tokens from `tokens.css` (Story 1.5). No new tokens introduced.

Key tokens:
- `--color-brand-green-900` (top-header bg)
- `--color-brand-green-800` (nav + footer bg)
- `--color-semantic-text-on-dark` (white text)
- `--color-semantic-focus-ring` (focus outlines)
- `--shadow-nav-shrunk` (shrunk-state box-shadow)
- `--spacing-scale-2`, `--spacing-scale-3`, `--spacing-scale-5`, `--spacing-scale-10` (paddings/gaps)
- `--spacing-container-gutter-desktop`
- `--typography-scale-caption`, `--typography-scale-small`
- `--typography-weight-bold`, `--typography-weight-light`
- `--typography-tracking-wide`

## 10. Test contract summary

Test file: `tests/test_navigation_chrome.py` (Decision D14).
- ~35-40 tests covering AC1-AC10 [MUST] scenarios primarily.
- File-system testable scenarios only (browser-dependent scenarios deferred to Story 9.8 Playwright).
- All tests must FAIL clean in RED phase (FileNotFoundError, TemplateDoesNotExist, AssertionError). Some may be SKIPPED if marked deferred.
- 1 test (Story 1.6 regression invariant `test_story_1_6_regression_test_updated_for_flatten`) may pass pre-impl if test file is already updated; tests the migration is complete.

---

**End of Story 1.8 Interface Contract**
