---
story-id: "1.7"
artifact: interface-contract
author: TEA
created: 2026-05-28
status: red-phase
---

# Story 1.7 — Interface Contract (TEA RED phase)

Ovaj dokument definiše **interfejs kontrakt** (filesystem + Django template API + CSS API)
za Story 1.7. Sve tačke su **testabilne** — TEA-ovi RED testovi (`tests/test_visual_components.py`)
direktno verifikuju ovaj kontrakt. Dev MORA implementirati tačno ovo da bi testovi prošli GREEN.

Kontrakt je izveden iz Story 1.7 AC1-AC9 + Dev Notes templates + Decisions D1-D4 + IMP-1 do IMP-17.

---

## 1. Filesystem kontrakt (Dev kreira)

| Path | Stanje pre 1.7 | Akcija | Sadržaj |
|---|---|---|---|
| `static/css/components/` | does NOT exist | CREATE (directory) | — |
| `static/css/components/repeating-element.css` | does NOT exist | CREATE | Repeating Element CSS (BEM `.coric-repeating-element*`) |
| `static/css/components/pill-button.css` | does NOT exist | CREATE | Pill Button CSS (BEM `.coric-button*` + 3 varijante + a11y media queries) |
| `static/css/components/wave-divider.css` | does NOT exist | CREATE | Wave Divider CSS (BEM `.coric-wave-divider*`) |
| `static/css/components/section-eyebrow.css` | does NOT exist | CREATE | Section Eyebrow CSS (BEM `.coric-section-eyebrow*`) |
| `static/css/components/hero-overlay-card.css` | does NOT exist | CREATE | Hero Overlay Card CSS (BEM `.coric-hero-overlay-card*`) |
| `templates/partials/repeating_element.html` | does NOT exist | CREATE | Django partial — dekorativan grafem |
| `templates/partials/pill_button.html` | does NOT exist | CREATE | Django partial — CTA dugme (3 varijante, `as` + `type`) |
| `templates/partials/wave_divider.html` | does NOT exist | CREATE | Django partial — inline SVG wave |
| `templates/partials/section_eyebrow.html` | does NOT exist | CREATE | Django partial — UPPERCASE caption sa zlatnim linijama |
| `templates/partials/hero_overlay_card.html` | does NOT exist | CREATE | Django partial — green-800 kartica sa h1 + bullets + watermark |
| `static/css/main.css` | exists (Story 1.6 placeholder ~120 bytes) | UPDATE (Strategy A) | Dodaj 5 `@import url('./components/...')` direktiva — relative-with-dot syntax |
| `templates/partials/language_switcher.html` | exists (Story 1.4) | **DO NOT MODIFY** | regression guard |
| `static/css/tokens.css` | exists (Story 1.5) | **DO NOT MODIFY** | regression guard |
| `templates/base.html` | exists (Story 1.6, 40 linija) | **DO NOT MODIFY** (Strategy A) | regression guard; load-order `tokens.css < bootstrap_css < main.css` ostaje |

---

## 2. Django template partial kontrakti

### 2.1 `templates/partials/repeating_element.html`

**Include sintaksa:**
```django
{% include "partials/repeating_element.html" with variant="green" %}
{% include "partials/repeating_element.html" with variant="jeegee" %}
{% include "partials/repeating_element.html" %}  {# default variant=green #}
```

**Parametri:**
| Parametar | Tip | Default | Validne vrednosti |
|---|---|---|---|
| `variant` | string | `"green"` | `"green"`, `"jeegee"` |

**Render output (must contain):**
- Korenski element: `<div class="coric-repeating-element coric-repeating-element--{variant}" aria-hidden="true">`
- Unutar njega: inline `<svg class="coric-repeating-element__corner" aria-hidden="true">` sa 3-4 `<path>` arc elementima, `stroke="white"`, `opacity="0.5"`, `stroke-width="1"`
- SVG ima `viewBox="0 0 60 40"` i `preserveAspectRatio="xMaxYMin meet"`

### 2.2 `templates/partials/pill_button.html`

**Include sintaksa:**
```django
{% include "partials/pill_button.html" with variant="primary" label="Saznaj više" href="/proizvodi/" %}
{% include "partials/pill_button.html" with variant="secondary" label="Kontakt" href="/kontakt/" %}
{% include "partials/pill_button.html" with variant="cta-light" label="Preuzmi katalog" href="/katalog.pdf" %}
{% include "partials/pill_button.html" with as="button" type="submit" variant="primary" label="Pošalji" %}
{% include "partials/pill_button.html" with as="button" type="reset" variant="secondary" label="Obriši" %}
```

**Parametri:**
| Parametar | Tip | Default | Validne vrednosti |
|---|---|---|---|
| `variant` | string | `"primary"` | `"primary"`, `"secondary"`, `"cta-light"` |
| `label` | string | (required) | bilo koji string (mixed-case kanon — D2/IMP-D4) |
| `href` | string | `"#"` | URL (samo kad `as="link"`) |
| `as` | string | `"link"` | `"link"` (renders `<a>`) ili `"button"` (renders `<button>`) |
| `type` | string | `"button"` | `"button"`, `"submit"`, `"reset"` (samo kad `as="button"`) |
| `extra_classes` | string | (none) | dodatne Bootstrap utility klase (npr. `"mt-4"`) |
| `aria_label` | string | (none) | aria-label override (opciono) |

**Render output (must contain):**
- Default `as="link"` → `<a class="coric-button coric-button--{variant}" href="{href}">{label}</a>`
- `as="button"` → `<button type="{type}" class="coric-button coric-button--{variant}">{label}</button>`
- Label se rendera **mixed-case u source-u**; CSS `text-transform: uppercase` vizuelno transformiše (D2)

### 2.3 `templates/partials/wave_divider.html`

**Include sintaksa:**
```django
{% include "partials/wave_divider.html" %}
{% include "partials/wave_divider.html" with position="bottom" %}
```

**Parametri:**
| Parametar | Tip | Default | Validne vrednosti |
|---|---|---|---|
| `position` | string | `"top"` | `"top"`, `"bottom"` |

**Render output (must contain):**
- Inline `<svg>` (NE `<img src=...>`) sa:
  - `aria-hidden="true"` + `role="presentation"`
  - `xmlns="http://www.w3.org/2000/svg"`
  - `viewBox="0 0 1200 80"`
  - `preserveAspectRatio="none"`
  - `width="100%"`, `height="80"`
  - `class="coric-wave-divider"` (i `coric-wave-divider--bottom` kad `position="bottom"`)
- Unutar SVG: 1 `<path>` sa `fill="var(--color-brand-green-800)"` (IMP-17 FOUC fallback — eksplicitan token-based fill, NE `currentColor`, NE hardcoded hex)

### 2.4 `templates/partials/section_eyebrow.html`

**Include sintaksa:**
```django
{% include "partials/section_eyebrow.html" with text="PROIZVODI" %}
{% include "partials/section_eyebrow.html" with text="O nama" tag="p" %}
{% include "partials/section_eyebrow.html" with text="Naša priča" variant="on-dark" %}
```

**Parametri:**
| Parametar | Tip | Default | Validne vrednosti |
|---|---|---|---|
| `text` | string | (required) | bilo koji string |
| `tag` | string | `"div"` | `"div"`, `"p"`, `"span"`, `"h6"` |
| `variant` | string | (none) | `"on-dark"` (jedina varijanta) |

**Render output (must contain):**
- Korenski element: `<{tag} class="coric-section-eyebrow">` (ili `coric-section-eyebrow coric-section-eyebrow--on-dark` ako variant)
- 3 child elementa redom:
  1. `<span class="coric-section-eyebrow__line" aria-hidden="true"></span>`
  2. `<span class="coric-section-eyebrow__text">{text}</span>`
  3. `<span class="coric-section-eyebrow__line" aria-hidden="true"></span>`

### 2.5 `templates/partials/hero_overlay_card.html`

**Include sintaksa:**
```django
{% include "partials/hero_overlay_card.html" with title="Hero" bullets=bullets_list %}
{% include "partials/hero_overlay_card.html" with title="Jeegee" brand_logo="img/jeegee.png" brand_logo_alt="Jeegee logo" bullets=bullets variant="jeegee" %}
```

**Parametri:**
| Parametar | Tip | Default | Validne vrednosti |
|---|---|---|---|
| `title` | string | (required) | bilo koji string |
| `brand_logo` | string | (none) | URL slike (opciono) |
| `brand_logo_alt` | string | `""` | alt tekst (caller MORA postaviti kad logo je informacioni) |
| `bullets` | list | (none) | lista stringova; template kapira na maks 3 (`\|slice:":3"`) |
| `variant` | string | `"green"` | `"green"`, `"jeegee"` (prosleđuje se watermark Repeating Element-u) |

**Render output (must contain):**
- Korenski element: `<div class="coric-hero-overlay-card">`
- Opciono: `<div class="coric-hero-overlay-card__brand-lockup"><img src="{brand_logo}" alt="{brand_logo_alt}"></div>`
- `<h1 class="coric-hero-overlay-card__title">{title}</h1>`
- Opciono: `<ul class="coric-hero-overlay-card__bullets">{% for bullet in bullets|slice:":3" %}<li>{bullet}</li>{% endfor %}</ul>`
- `<div class="coric-hero-overlay-card__watermark">{% include "partials/repeating_element.html" with variant=variant|default:"green" %}</div>`

---

## 3. CSS klasni kontrakt (BEM nomenclatura)

### 3.1 Repeating Element (`static/css/components/repeating-element.css`)

| Klasa | Tip | Ključna pravila |
|---|---|---|
| `.coric-repeating-element` | Block | `position: relative`, `aspect-ratio: 3 / 2`, `border-radius: var(--rounded-md)`, `overflow: hidden` |
| `.coric-repeating-element--green` | Modifier | `background-color: var(--color-brand-green-800)` |
| `.coric-repeating-element--jeegee` | Modifier | `background-color: var(--color-jeegee-blue)` |
| `.coric-repeating-element__corner` | Element | `position: absolute`, `top: 0`, `right: 0`, `width: 50%`, `height: auto`, `aspect-ratio: 3 / 2`, `pointer-events: none` |

### 3.2 Pill Button (`static/css/components/pill-button.css`)

| Klasa | Tip | Ključna pravila |
|---|---|---|
| `.coric-button` | Block | `border-radius: var(--rounded-pill)`, `padding: var(--spacing-scale-3) var(--spacing-scale-6)`, `font-weight: var(--typography-weight-bold)`, `letter-spacing: var(--typography-tracking-wide)`, `font-size: var(--typography-scale-small)`, `text-decoration: none`, `display: inline-block`, `text-transform: uppercase`, `min-height: 44px`, `transition: background-color 200ms ease, color 200ms ease` |
| `.coric-button--primary` | Modifier | `background-color: var(--color-brand-green-800)`, `color: var(--color-semantic-text-on-dark)`, `border: 2px solid transparent`; hover → lime-500 bg + green-900 text |
| `.coric-button--secondary` | Modifier | `background-color: transparent`, `color: var(--color-brand-green-800)`, `border: 2px solid var(--color-brand-green-800)`; hover → green-800 bg + white text |
| `.coric-button--cta-light` | Modifier | `background-color: var(--color-accent-gold-500)`, `color: var(--color-brand-green-900)`, `border: 2px solid transparent`; hover → lime-500 bg + green-900 text |
| `.coric-button:focus` | Pseudo | `outline: 2px solid var(--color-semantic-focus-ring); outline-offset: 2px;` |

**Media queries (KRITIČNO):**
```css
@media (prefers-reduced-motion: reduce) {
  .coric-button { transition: none; }
}
@media (forced-colors: active) {
  .coric-button { border-color: ButtonText; }
}
```

### 3.3 Wave Divider (`static/css/components/wave-divider.css`)

| Klasa | Tip | Ključna pravila |
|---|---|---|
| `.coric-wave-divider` | Block | `display: block`, `width: 100%`, `color: var(--color-brand-green-800)` (defensive future-use per IMP-D3), `height: 80px` |
| `.coric-wave-divider--bottom` | Modifier | `transform: scaleY(-1)` |

**Media query:**
```css
@media (max-width: 767px) {
  .coric-wave-divider { height: 48px; }
}
```

### 3.4 Section Eyebrow (`static/css/components/section-eyebrow.css`)

| Klasa | Tip | Ključna pravila |
|---|---|---|
| `.coric-section-eyebrow` | Block | `display: flex`, `align-items: center`, `justify-content: center`, `gap: var(--spacing-scale-3)`, `margin-bottom: var(--spacing-scale-4)` |
| `.coric-section-eyebrow__line` | Element | `flex: 0 0 var(--spacing-scale-10)` (KRITIČNO — IMP-5: NE hardcoded 64px), `height: 1px`, `background-color: var(--color-accent-gold-500)` |
| `.coric-section-eyebrow__text` | Element | `font-family: var(--typography-family-primary)`, `font-weight: var(--typography-weight-light)`, `font-size: var(--typography-scale-caption)`, `letter-spacing: var(--typography-tracking-wide)`, `text-transform: uppercase`, `color: var(--color-brand-green-800)` |
| `.coric-section-eyebrow--on-dark .coric-section-eyebrow__text` | Modifier | `color: var(--color-semantic-text-on-dark)` |

### 3.5 Hero Overlay Card (`static/css/components/hero-overlay-card.css`)

| Klasa | Tip | Ključna pravila |
|---|---|---|
| `.coric-hero-overlay-card` | Block | `background-color: var(--color-brand-green-800)`, `color: var(--color-semantic-text-on-dark)`, `border-radius: var(--rounded-md)`, `padding: var(--spacing-scale-6)`, `box-shadow: var(--shadow-none)`, `position: relative`, `max-width: 480px` |
| `.coric-hero-overlay-card__title` | Element | `font-family: var(--typography-family-primary)`, `font-weight: var(--typography-weight-light)`, `font-size: var(--typography-scale-h1)`, `line-height: var(--typography-line-height-tight)`, `margin: 0 0 var(--spacing-scale-5) 0` |
| `.coric-hero-overlay-card__bullets` | Element | `list-style: none`, `padding: 0`, `margin: 0`, `font-size: var(--typography-scale-body)`, `line-height: var(--typography-line-height-base)` |
| `.coric-hero-overlay-card__watermark` | Element | `position: absolute`, `bottom: var(--spacing-scale-4)`, `right: var(--spacing-scale-4)`, `width: 80px`, `opacity: 0.3`, `pointer-events: none` |
| `.coric-hero-overlay-card__brand-lockup` | Element | (optional grouping for brand logo `img` — no strict CSS rules required) |

---

## 4. CSS load strategy (AC8)

**Strategy A (preferirana — D1 default):** `static/css/main.css` dobija 5 `@import` direktiva — **MANDATORY relative-with-dot syntax `./components/...`** (IMP-7):

```css
@import url('./components/repeating-element.css');
@import url('./components/pill-button.css');
@import url('./components/wave-divider.css');
@import url('./components/section-eyebrow.css');
@import url('./components/hero-overlay-card.css');
```

Strategy B (alternativa): 5 `<link>` tagova u `templates/base.html` posle `main.css` link-a. TEA testovi pretpostavljaju Strategy A.

**Regression guard (IMP-D2):** `tokens.css` linija < `bootstrap_css` linija < `main.css` linija u `templates/base.html`.

---

## 5. Token usage manifest (komponente konzumiraju iz `tokens.css`)

| Token | Vrednost | Konzumira |
|---|---|---|
| `--color-brand-green-800` | `#25402f` | repeating-element (green bg), pill-button (primary bg + secondary border/text), wave-divider (color setter + SVG fill), section-eyebrow (text), hero-overlay-card (bg) |
| `--color-brand-green-900` | `#1f3f2f` | pill-button (cta-light text, hover text) |
| `--color-jeegee-blue` | `#00a4e9` | repeating-element (jeegee bg) |
| `--color-accent-gold-500` | `#e7af12` | pill-button (cta-light bg), section-eyebrow (lines) |
| `--color-accent-lime-500` | `#c8d32c` | pill-button (primary/cta-light hover bg) |
| `--color-semantic-text-on-dark` | `#ffffff` | pill-button (primary text), hero-overlay-card (text), section-eyebrow (on-dark variant) |
| `--color-semantic-focus-ring` | `#5a8a6e` | pill-button (focus outline) |
| `--rounded-md` | `8px` | repeating-element, hero-overlay-card |
| `--rounded-pill` | `999px` | pill-button |
| `--spacing-scale-3` | `12px` | pill-button padding-y, section-eyebrow gap |
| `--spacing-scale-4` | `16px` | hero-overlay-card watermark offset, section-eyebrow margin-bottom |
| `--spacing-scale-5` | `24px` | hero-overlay-card title margin-bottom |
| `--spacing-scale-6` | `32px` | pill-button padding-x, hero-overlay-card padding |
| `--spacing-scale-10` | `64px` | section-eyebrow line width (IMP-5) |
| `--shadow-none` | `none` | hero-overlay-card |
| `--typography-family-primary` | `'Roboto', system-ui, sans-serif` | section-eyebrow, hero-overlay-card |
| `--typography-weight-light` | `300` | hero-overlay-card title, section-eyebrow |
| `--typography-weight-bold` | `700` | pill-button |
| `--typography-scale-h1` | `3.5rem` | hero-overlay-card title |
| `--typography-scale-body` | `1.25rem` | hero-overlay-card bullets |
| `--typography-scale-small` | `1rem` | pill-button |
| `--typography-scale-caption` | `0.875rem` | section-eyebrow text |
| `--typography-line-height-tight` | `1.2` | hero-overlay-card title |
| `--typography-line-height-base` | `1.5` | hero-overlay-card bullets |
| `--typography-tracking-wide` | `0.05em` | pill-button, section-eyebrow |

Ukupno: **25 različitih tokena konzumirano kroz 5 komponenata.** Story 1.7 NE uvodi nove tokene.

---

## 6. Cross-component invariants (AC7 — token discipline)

1. **NIJEDAN hardcoded hex (`#XXXXXX`, `#XXX`)** u `static/css/components/*.css` — sve preko `var(--color-*)`. EXCEPTION: named CSS keywords (`white`, `transparent`, `inherit`, `currentColor`) dozvoljeni.
2. **NIJEDAN hardcoded hex u** `templates/partials/{repeating_element,pill_button,wave_divider,section_eyebrow,hero_overlay_card}.html`.
3. **NIJEDAN inline `style="..."`** u nijednom novom partial-u (AC9.4).
4. **NIJEDAN hardcoded 64px** u CSS-u (IMP-5 — mora `var(--spacing-scale-10)`).
5. **Whitelist hardcoded px:** `1px` (stroke/border), `2px` (border/outline), `44px` (WCAG touch target), `48px` (wave mobile), `80px` (wave desktop, watermark), `480px` (hero card max-width). Sve ostale px MORAJU biti `var(--spacing-*)`, `var(--typography-*)`, ili `var(--rounded-*)`.
6. **Cyrillic forbidden** — sve latinica (project-context.md § Critical Don't-Miss).
7. **SVG path `fill`/`stroke`:** dozvoljen `currentColor`, `var(--...)`, named CSS keyword (`white`, `transparent`, `inherit`), ili izostavljen. NE hardcoded hex.
8. **`aria-hidden="true"`** uvek prisutan na Repeating Element root, Wave Divider SVG, i Section Eyebrow `__line` span-ima (dekorativni elementi).
9. **CSS klase MORAJU koristiti `coric-` prefix** + BEM nomenclaturu (block`__`element`--`modifier).
10. **`@media (prefers-reduced-motion: reduce)`** override prisutan u `pill-button.css` (CRITICAL-3 — Story 1.7 ship-uje motion, dakle ona ship-uje i guard).
11. **`@media (forced-colors: active)`** override prisutan u `pill-button.css` (IMP-13 — WHCM border visibility).

---

## 7. Test → kontrakt traceability

| AC | TEA test (`tests/test_visual_components.py`) | Contract item |
|---|---|---|
| AC1 | `test_ac1_components_directory_exists` | Section 1 (directory) |
| AC1 | `test_ac1_all_5_partials_present` | Section 1 (partials) |
| AC1 | `test_ac1_all_5_css_files_present` | Section 1 (CSS files) |
| AC2 | `test_ac2_repeating_element_renders_green_variant` | Section 2.1, 3.1 |
| AC2 | `test_ac2_repeating_element_renders_jeegee_variant` | Section 2.1, 3.1 |
| AC2 | `test_ac2_repeating_element_has_corner_positioning_css` | Section 3.1 (`__corner`) |
| AC2 | `test_ac2_repeating_element_has_white_arcs_with_opacity` | Section 2.1 (SVG corner stroke/opacity) |
| AC3 | `test_ac3_pill_button_renders_primary_variant` | Section 2.2, 3.2 |
| AC3 | `test_ac3_pill_button_renders_secondary_and_cta_light_variants` | Section 2.2, 3.2 |
| AC3 | `test_ac3_pill_button_renders_as_anchor_and_button` | Section 2.2 (as/type) |
| AC3 | `test_ac3_pill_button_supports_as_button_with_type_submit` | Section 2.2 (IMP-11) |
| AC4 | `test_ac4_wave_divider_renders_with_aria_hidden_and_token_fill` | Section 2.3 |
| AC4 | `test_ac4_wave_divider_supports_top_and_bottom_position` | Section 2.3, 3.3 |
| AC5 | `test_ac5_section_eyebrow_renders_uppercase_text_with_gold_lines` | Section 2.4, 3.4 |
| AC5 | `test_ac5_section_eyebrow_on_dark_variant_adds_modifier_class` | Section 2.4 (variant) |
| AC5 | `test_ac5_section_eyebrow_custom_tag_renders_as_p` | Section 2.4 (tag) |
| AC6 | `test_ac6_hero_overlay_card_renders_with_brand_logo_alt` | Section 2.5 |
| AC6 | `test_ac6_hero_overlay_card_caps_bullets_at_3` | Section 2.5 (IMP-15) |
| AC6 | `test_ac6_hero_overlay_card_brand_logo_alt_default_empty` | Section 2.5 (IMP-14) |
| AC6 | `test_ac6_hero_overlay_card_brand_logo_alt_explicit` | Section 2.5 (IMP-14) |
| AC6 | `test_ac6_hero_overlay_card_includes_watermark_repeating_element` | Section 2.5 (watermark include) |
| AC6 | `test_ac6_hero_overlay_card_passes_variant_to_watermark` | Section 2.5 (variant passthrough) |
| AC7 | `test_ac7_no_hardcoded_hex_in_component_css` | Section 6.1 |
| AC7 | `test_ac7_no_hardcoded_rgb_hsl_in_component_css` | Section 6.1 |
| AC7 | `test_ac7_no_hardcoded_64px_in_component_css` | Section 6.4 (IMP-5) |
| AC7 | `test_ac7_components_use_var_tokens` | Section 5 |
| AC9.3 | `test_ac9_components_meet_token_usage_thresholds` | Section 5 (AC9.3 thresholds) |
| (a11y) | `test_pill_button_has_prefers_reduced_motion_override` | Section 6.10 |
| (a11y) | `test_pill_button_has_forced_colors_override` | Section 6.11 |
| (a11y) | `test_pill_button_has_min_touch_target` | Section 3.2 (`min-height: 44px`) |
| AC4 | `test_wave_divider_path_uses_token_fill` | Section 2.3 (IMP-17) |
| AC8 | `test_base_html_css_load_order` | Section 4 (IMP-D2) |
| AC8 | `test_main_css_imports_all_5_components` | Section 4 (Strategy A) |
| AC7 | `test_no_inline_style_attribute_in_partials` | Section 6.3 |
| AC9.10 | `test_collectstatic_rewrites_import_paths_to_hashed` | DEFERRED (`@pytest.mark.skip`) |

---

## 8. Out-of-scope za 1.7 testove

- Playwright visual regression (Story 1.8 / 9.8)
- Lighthouse a11y audit (Story 1.9 / 9.9)
- Production collectstatic hash verification (DEFERRED — AC9.10 dokumentuje strukturni vendor blocker)
- Browser visual smoke (manual; izveden van pytest-a)

---

## 9. Strategy decision (TEA prijem)

TEA testovi pretpostavljaju **Strategy A** (D1 default) — `@import` u `main.css`. Ako Dev izabere Strategy B (5 `<link>` tagova u `base.html`), tada test `test_main_css_imports_all_5_components` mora biti adaptiran ili skipovan, a test `test_base_html_css_load_order` se proširuje da verifikuje 5 dodatnih `<link>` tagova posle main.css. Default očekivanje: Strategy A.

---

**End of Interface Contract for Story 1.7**
