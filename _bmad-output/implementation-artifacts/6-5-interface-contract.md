# Story 6.5 — Interface Contract (TEA RED)

**Story:** 6.5 — i18n Fallback Marker (ⓘ Tooltip)
**Module:** `apps/core`
**Phase:** RED (failing tests written; Dev implements to GREEN)
**Author:** Test Architect (TEA)
**Date:** 2026-06-06

> This contract is **authoritative** for the Dev. Tests in
> `apps/core/tests/test_i18n_fallback.py` (+ 2 integration files) lock it. Dev MUST
> implement to satisfy these tests **without modifying them**. 0 migrations, 0 model
> changes, 0 new dependencies, 0 vendored assets.

---

## 1. Tag signature

```python
# apps/core/templatetags/i18n_fallback.py  (NEW — second tag module in apps.core
# alongside htmx_aria.py; templatetags is already a package with __init__.py)

from django import template
from django.utils.translation import get_language, gettext
from django.utils.html import format_html
from django.utils.safestring import mark_safe
import itertools

register = template.Library()

@register.simple_tag(takes_context=True)
def translated_field(context, obj, field):
    """Returns SafeString: plain escaped field value (no fallback) OR a
    coric-fallback-marker span (fallback detected)."""
```

- `simple_tag(takes_context=True)` — needs `get_language()` (runtime, LocaleMiddleware-set)
  and `context["request"]` for the per-request id counter.
- Returns either plain escaped resolved value, or the marker span — both via `format_html`.

Usage:
```django
{% load i18n_fallback %}
{% translated_field post 'title' %}
{% translated_field product 'name' %}
```

---

## 2. Detection algorithm (CRUX — SM-D1, G1)

```
if obj is None:                          → return ""                       (graceful)
lang = (get_language() or "sr").split("-")[0]     # BCP-47 normalize (G9): en-us→en, sr-latn→sr
if lang == "sr":                         → return format_html("{}", str(getattr(obj, field, "") or ""))
                                            (sr is source — NEVER mark)
current = getattr(obj, f"{field}_{lang}", _UNSET)
if current is _UNSET:                    → return plain  (non-translated field / wrong name; graceful, NOT 500)
if current and str(current).strip():     → return format_html("{}", str(current))   (locale filled — no fallback)
else:  # empty/blank current = FALLBACK
    sr_val = getattr(obj, f"{field}_sr", None)
    if not (sr_val and str(sr_val).strip()): → return plain  (nothing to mark)
    else:                                → return _render_marker(context, sr_val)   (MARKER)
```

- **NEVER read `obj.field` for detection** — `MODELTRANSLATION_FALLBACK_LANGUAGES=("sr",)`
  makes `obj.name` already silently fallback-resolve to sr; comparing `obj.name == name_sr`
  is a FALSE test (G1). The ONLY reliable signal is "is the raw `field_<lang>` column empty".
- whitespace-only (`str(x).strip()` empty) is treated as empty (G7).
- `_UNSET = object()` sentinel distinguishes "no accessor" from "accessor returns None/empty".

---

## 3. Marker markup structure (AC2 — tooltip is a CHILD of the marker, NOT a sibling)

```html
<span class="coric-fallback-marker" tabindex="0" aria-describedby="fallback-tooltip-N" lang="sr">{sr_text} <svg class="coric-fallback-marker__icon" aria-hidden="true" focusable="false" ...>…</svg><span class="coric-fallback-marker__tooltip" id="fallback-tooltip-N" role="tooltip">{localized tooltip}</span></span>
```

- `{sr_text}` and `{localized tooltip}` are `{}` placeholders in `format_html` → **AUTOESCAPED** (AC7).
- `_INFO_ICON_SVG` MUST be `mark_safe`'d (static markup) so `format_html`/`conditional_escape`
  passes it through as a `SafeString` (else it becomes literal `&lt;svg&gt;`; G3b).
- Tooltip `<span role="tooltip">` is the **last child INSIDE** `.coric-fallback-marker`
  (after text + icon), NOT an adjacent sibling — so the CSS descendant reveal selector
  `.coric-fallback-marker:hover .coric-fallback-marker__tooltip` matches (G4). A sibling
  would never reveal.
- `aria-describedby` value MUST exactly equal the tooltip `id` (pair; AC3). The id-reference
  works regardless of DOM nesting.
- `lang="sr"` on the marker element wrapping the sr fallback text (WCAG 3.1.2; AC2).
- Icon: inline `<svg aria-hidden="true" focusable="false">` (Bootstrap Icons NOT vendored →
  NOT `class="bi-info-circle"`; SM-D5/G3). Use the exact Bootstrap Icons `info-circle` path
  data from Story Task 1.4 (two `<path>`s).

`format_html` template (from Task 3.2):
```python
format_html(
    '<span class="coric-fallback-marker" tabindex="0" aria-describedby="{}" lang="sr">'
    '{} {}'
    '<span class="coric-fallback-marker__tooltip" id="{}" role="tooltip">{}</span></span>',
    tooltip_id, sr_text, _INFO_ICON_SVG, tooltip_id, tooltip_text,
)
```

---

## 4. Unique id scheme (AC3 — SM-D3, G5)

```python
_FALLBACK_ID_FALLBACK_COUNTER = itertools.count(1)   # module-level, request=None fallback

def _next_tooltip_id(context):
    request = context.get("request")
    if request is not None:                          # PRIMARY — per-request, resets each request
        n = getattr(request, "_coric_fallback_counter", 0) + 1
        setattr(request, "_coric_fallback_counter", n)
        return f"fallback-tooltip-{n}"
    return f"fallback-tooltip-{next(_FALLBACK_ID_FALLBACK_COUNTER)}"   # request=None: monotonic
```

- Primary path: per-request `request._coric_fallback_counter` → deterministic `-1/-2/...`
  per request.
- `request is None` (shell/management/isolated render): module-level `itertools.count(1)` →
  IDs stay UNIQUE within a render (cross-request non-determinism accepted).
- **FORBIDDEN:** a static string constant (`"fallback-tooltip-x"`) → would give all markers
  the same id, breaking `aria-describedby` uniqueness. NEVER 500.
- Tests assert **uniqueness + `fallback-tooltip-\d+` pattern + aria-describedby↔id pair**,
  NOT a hardcoded `-1`/`-2` value (module-level path makes the exact value brittle).

---

## 5. Tooltip text (AC4 — SM-D4, G2)

- `tooltip_text = gettext("Sadržaj na srpskom — još nije preveden")` called **at runtime
  INSIDE the tag function** (per-request locale) — NOT a module-level `gettext(...)` constant
  (would cache to import-time locale; G2). Full diacritics in the msgid (project-context).
- Mark-for-translation (`makemessages` picks up the in-function `gettext(...)`).
- **REQUIRED hu/en .po translations (Task 6.2, required-for-done):**
  - hu: `A tartalom szerb nyelven — még nincs lefordítva`
  - en: `Content in Serbian — not yet translated`
  - `compilemessages` to regenerate `.mo`.
- RED-state tolerance: tests accept the sr msgid as fallback until the .po is compiled,
  but lock that the text is present + that markers render under both hu and en.

---

## 6. CSS class names + file (AC5 — SM-D6)

- NEW `static/css/components/i18n-fallback-marker.css`; `@import` it in `static/css/main.css`
  (per-component @import pattern).
- BEM classes:
  - `.coric-fallback-marker` — wrapper (`position: relative; cursor: help`;
    `color: var(--color-semantic-text-muted)`).
  - `.coric-fallback-marker__icon` — inline SVG (`1em` square, `currentColor`).
  - `.coric-fallback-marker__tooltip` — DEFAULT visually-hidden clip pattern
    (`position:absolute; width:1px; height:1px; clip-path:inset(50%); overflow:hidden;
    white-space:nowrap;` — NOT `display:none`/`visibility:hidden`/bare `opacity:0`).
- Reveal: descendant selector `.coric-fallback-marker:hover .coric-fallback-marker__tooltip`
  and `:focus`/`:focus-within` → visible state. Tooltip background PINNED
  `var(--color-brand-green-800)` + `color: var(--color-semantic-text-on-dark)` (~11.5:1).
- `:focus-visible` outline `var(--color-semantic-focus-ring)`; `@media (prefers-reduced-motion)`;
  contrast ≥ 4.5:1; ONLY `var(--...)` tokens (clip primitives `1px`/`inset(50%)` exempt).
- (CSS is not directly unit-testable — tests lock the markup/class structure that the CSS
  selectors depend on.)

---

## 7. Hero adoption param contract (AC6 — SM-D7 option A, opt-in backward-compatible)

- `templates/partials/hero_overlay_card.html`:
  ```django
  {% load i18n_fallback %}
  <h1 class="coric-hero-overlay-card__title">{% if fallback_obj %}{% translated_field fallback_obj fallback_field %}{% else %}{{ title }}{% endif %}</h1>
  ```
  `fallback_obj` / `fallback_field` are **OPTIONAL** include params.
- `templates/products/partials/_hero_section.html`: add `fallback_obj=product fallback_field='name'`
  to the existing include (keeps `title=product.name`).
- `templates/brands/partials/_hero_section.html`: add `fallback_obj=brand fallback_field='name'`
  to all 4 includes.
- `templates/blog/post_detail.html`: `{% load i18n_fallback %}` + H1 →
  `{% translated_field post 'title' %}`.
- **Zero blast-radius:** existing callers without `fallback_obj` (home/listing/about/
  brand-specific hero) fall to `{{ title }}` → render identically (test #14c).

---

## 8. Files the Dev will CREATE / EDIT

| Path | Type | Purpose |
|---|---|---|
| `apps/core/templatetags/i18n_fallback.py` | **NEW** | The `{% translated_field %}` tag (§1–§5). |
| `static/css/components/i18n-fallback-marker.css` | **NEW** | Marker/tooltip BEM CSS (§6). |
| `static/css/main.css` | EDIT | `@import url('./components/i18n-fallback-marker.css');` |
| `templates/blog/post_detail.html` | EDIT | `{% load i18n_fallback %}` + H1 → `{% translated_field post 'title' %}` |
| `templates/partials/hero_overlay_card.html` | EDIT | opt-in `{% if fallback_obj %}...{% else %}{{ title }}{% endif %}` (§7) |
| `templates/products/partials/_hero_section.html` | EDIT | pass `fallback_obj=product fallback_field='name'` |
| `templates/brands/partials/_hero_section.html` | EDIT | pass `fallback_obj=brand fallback_field='name'` (×4) |
| `locale/hu/LC_MESSAGES/django.po` + `.mo` | EDIT | hu tooltip translation + compile |
| `locale/en/LC_MESSAGES/django.po` + `.mo` | EDIT | en tooltip translation + compile |

**Do NOT touch:** any model/migration (`makemigrations --check` must stay clean),
`config/settings/base.py`, `apps/core/templatetags/htmx_aria.py`,
`apps/seo/templatetags/seo_meta.py`, `static/css/tokens.css`, `pyproject.toml`,
existing CSS components, `templates/base.html`, and the TEA test files.

---

## 9. Test files (locked contract)

| File | Scope |
|---|---|
| `apps/core/tests/test_i18n_fallback.py` | Tag unit tests (detection, CRUX, BCP-47, XSS, edge, a11y markup, unique ids, tooltip text) + makemigrations regression guard. |
| `apps/products/tests/test_hero_fallback_marker.py` | Integration #14b/#14c — `/hu/proizvod/<slug>/` hero H1 marker + en locale + zero-regression. |
| `apps/blog/tests/test_post_detail_fallback_marker.py` | Integration #14 — `/hu/blog/<slug>/` H1 marker (empty/populated/sr). |
