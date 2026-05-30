---
story-id: "2.8"
story-key: 2-8-tractor-listing-strana-sa-htmx-filterima
artifact: interface-contract
created: 2026-05-30
author: TEA / Murat (RED phase)
purpose: Canonical contract for Tractor Listing page sa HTMX filterima — URL pattern,
         TractorListView CBV, 1 main template + 4 partials, JS + CSS, vendor noUiSlider,
         locale .po edits, data-testid surface. Dev MORA satisfy svaku klauzulu u GREEN
         phase. PRVA HTMX story u Epic 2 — uspostavlja kanonski request.htmx branching +
         OOB aria-live + hx-push-url pattern za buduće 2.9/2.11/2.13.
---

# Interface Contract — Story 2.8 Tractor Listing sa HTMX Filterima

Story 2.8 dodaje NOVI URL `/sr/traktori/` (root listing, NE shadow-uje Story 2.6
`/sr/traktori/<brand-slug>/` brand detail per SM-D1 URL deconfliction), NOVI
`TractorListView` CBV, 1 glavni template + 4 partials, range slider widget kroz vendored
noUiSlider (SM-D4 + SM-D22), HTMX filter pattern (debounce + hx-push-url + OOB aria-live),
i locale .po edits (sr nplurals=3 plural completion).

Ovaj ugovor enumerise file-system delta + Python surface + template + DOM/data-testid
surface + CSS klase + JS module surface koje TEA RED-phase testovi verifikuju. Dev
GREEN-phase realizuje sve klauzule; bilo koje odstupanje vraća story u `paused`.

---

## 1. File-system delta

### Fajlovi koji MORAJU postojati posle GREEN phase (10 NOVO + 6 EDIT, 0 DELETE)

| Path | Status | Vlasništvo |
|---|---|---|
| `apps/products/views.py` | EDIT (ADD class) | `TractorListView` CBV — postojeća `ProductDetailView` netaknuta |
| `apps/products/urls.py` | EDIT (ADD path) | `path("traktori/", views.TractorListView.as_view(), name="tractor_list")` posle postojećeg `proizvod/<slug>/` |
| `templates/products/tractor_listing.html` | NOVO (Dev) | Glavni template — extends base.html |
| `templates/products/partials/_brand_header.html` | NOVO (Dev) | Brand logo header (filter is_coming_soon=False) |
| `templates/products/partials/_filter_form.html` | NOVO (Dev) | Filter form (2 range slidera + RESETUJ FILTERE CTA + HTMX atributi) |
| `templates/products/partials/_results_grid.html` | NOVO (Dev) | Results grid + OOB aria-live (HTMX target shared sa initial render) |
| `templates/products/partials/_empty_state.html` | NOVO (Dev) | Empty state markup sa RESETUJ FILTERE CTA |
| `static/css/components/tractor-listing.css` | NOVO (Dev) | Layout (brand header, filter form, results grid, empty state) |
| `static/css/components/range-slider.css` | NOVO (Dev) | Range slider widget styling (noUiSlider override) |
| `static/js/tractor-filters.js` | NOVO (Dev) | Vanilla IIFE — slider init + URL sync + historyRestore |
| `static/vendor/nouislider/nouislider.min.js` | NOVO (Dev) | Vendor JS (~10 KB gzipped) — pin 15.7.1 |
| `static/vendor/nouislider/nouislider.min.css` | NOVO (Dev) | Vendor CSS (~5 KB) |
| `static/css/main.css` | EDIT | +2 `@import url('./components/...');` linije (tractor-listing, range-slider) |
| `locale/sr/LC_MESSAGES/django.po` | EDIT | Popuni msgstr za sve nove msgid + 3 plural slot-a (SM-D15) |
| `locale/hu/LC_MESSAGES/django.po` | EDIT | Popuni hu prevode (nplurals=2) |
| `locale/en/LC_MESSAGES/django.po` | EDIT | Popuni en prevode (nplurals=2) |
| `apps/products/tests/test_views_tractor_list.py` | NOVO (TEA) | AC1+AC2 view + queryset + context + HTMX branching |
| `apps/products/tests/test_templates_tractor_listing.py` | NOVO (TEA) | AC3-AC8 template structure + partials |
| `apps/products/tests/test_htmx_tractor_filter.py` | NOVO (TEA) | AC6 HTMX request handling + OOB div + hx-push-url |
| `apps/products/tests/test_url_routing_tractor.py` | NOVO (TEA) | AC1 URL routing 5 tests + deconfliction |
| `apps/products/tests/test_filter_restore.py` | NOVO (TEA) | AC9/SR3 parametrized 4 restore scenarija |
| `apps/products/tests/test_lighthouse_manual_tractor.py` | NOVO (TEA) | AC9 placeholder xfail (manual smoke) |
| `apps/products/tests/factories.py` | EDIT (TEA) | EXTEND sa `TractorProductFactory` (Category+Subcategory chain) |

Vendor LICENSE / VERSION metadata (tracking-only, NE broji u 10 NOVO count):

- `static/vendor/nouislider/LICENSE.md` (MIT license tekst) — pratite Story 2.5 GLightbox precedent
- `static/vendor/nouislider/VERSION.txt` (`15.7.1`)

---

## 2. Python surface

### `apps/products/views.py` (EDIT — ADD `TractorListView`)

```python
from decimal import Decimal, InvalidOperation
from django.views.generic import ListView
from apps.brands.models import Brand
from apps.products.models import Product

_PRODUCTS_PER_PAGE = 24  # SM-D8


def _parse_int(raw, *, min_value=0, max_value=10_000):
    if raw is None:
        return None
    try:
        value = int(raw)
    except (ValueError, TypeError):
        return None
    if value < min_value or value > max_value:
        return None
    return value


def _parse_decimal(raw, *, min_value=Decimal("0"), max_value=Decimal("10000000")):
    if raw is None:
        return None
    try:
        value = Decimal(raw)
    except (InvalidOperation, ValueError, TypeError):
        return None
    if value < min_value or value > max_value:
        return None
    return value


class TractorListView(ListView):
    model = Product
    context_object_name = "products"
    paginate_by = _PRODUCTS_PER_PAGE

    def get_template_names(self):
        if self.request.htmx:
            return ["products/partials/_results_grid.html"]
        return ["products/tractor_listing.html"]

    def get_queryset(self):
        qs = (
            Product.objects.filter(
                is_published=True,
                subcategory__category__is_for="traktori",
            )
            .select_related("brand", "series", "subcategory")
            .order_by("-created_at")
        )
        snaga_min = _parse_int(self.request.GET.get("snaga_min"))
        snaga_max = _parse_int(self.request.GET.get("snaga_max"))
        cena_min = _parse_decimal(self.request.GET.get("cena_min"))
        cena_max = _parse_decimal(self.request.GET.get("cena_max"))
        if snaga_min is not None:
            qs = qs.filter(horse_power__gte=snaga_min)
        if snaga_max is not None:
            qs = qs.filter(horse_power__lte=snaga_max)
        if cena_min is not None:
            qs = qs.filter(price_eur__gte=cena_min)
        if cena_max is not None:
            qs = qs.filter(price_eur__lte=cena_max)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["brands_for_header"] = Brand.objects.filter(
            is_coming_soon=False
        ).order_by("name")
        ctx["active_filters"] = {
            "snaga_min": self.request.GET.get("snaga_min", ""),
            "snaga_max": self.request.GET.get("snaga_max", ""),
            "cena_min": self.request.GET.get("cena_min", ""),
            "cena_max": self.request.GET.get("cena_max", ""),
        }
        paginator = ctx.get("paginator")
        if paginator is not None:
            ctx["count"] = paginator.count
        else:
            ctx["count"] = self.get_queryset().count()
        return ctx
```

### `apps/products/urls.py` (EDIT — ADD path)

```python
urlpatterns = [
    path("proizvod/<slug:slug>/", views.ProductDetailView.as_view(), name="detail"),
    path("traktori/", views.TractorListView.as_view(), name="tractor_list"),
]
```

URL deconfliction (SM-D1): `apps.brands.urls` (`traktori/<slug:slug>/`) je include-ovan
PRE `apps.products.urls` u `config/urls.py:27-28`. Resolver iterira u redu — `traktori/`
(bez slug-a) ne matchuje `traktori/<slug:slug>/` (slug zahteva content) → pada na
`apps.products.urls` `traktori/` → `TractorListView`.

### Context surface (svaki request — full page i HTMX)

| Key | Tip | Opis |
|---|---|---|
| `products` | QuerySet[Product] | Current page slice (paginate_by=24 default) ili full queryset |
| `brands_for_header` | QuerySet[Brand] | `is_coming_soon=False` ordered by name |
| `active_filters` | dict[str, str] | 4 string vrednosti (snaga_min/max, cena_min/max) iz request.GET |
| `count` | int | Total broj filtriranih rezultata across all pages (za pluralized OOB count) |
| `paginator`, `page_obj`, `is_paginated` | Django ListView defaults | Present samo ako paginate_by set |

### HTMX branching

- `request.htmx == True` → `get_template_names()` vraća `["products/partials/_results_grid.html"]`
- `request.htmx == False` → vraća `["products/tractor_listing.html"]`

OOB aria-live `<div hx-swap-oob="innerHTML:#aria-live">` se renderuje SAMO u `_results_grid.html`
template wrapped u `{% if request.htmx %}` guard (SM-D23 OOB fix — sprečava plain-text
render OOB div-a u inicijalnom server-side full-page render-u).

---

## 3. Template surface

### `templates/products/tractor_listing.html` (main, NOVO)

- `{% extends "base.html" %}` + `{% load i18n static media_tags htmx_aria %}`
- `{% block title %}{% translate "Traktori" %} | Ćorić Agrar{% endblock %}`
- `{% block meta_description %}{% blocktranslate %}Filtrirajte traktore po snazi i ceni — kompletna ponuda svih brendova Ćorić Agrar-a.{% endblocktranslate %}{% endblock %}`
- `{% block content %}` sadrži outer `<section class="coric-tractor-listing" data-testid="tractor-listing-page" aria-labelledby="tractor-listing-title">` wrapper (NIJE drugi `<main>`)
- 4 sekcije TAČNIM redosledom:
  1. Page heading (`<header>` + JEDINI `<h1 id="tractor-listing-title">Traktori</h1>` + lead `<p>`)
  2. `<section id="brand-header" aria-labelledby="brand-header-title">` koji `{% include "products/partials/_brand_header.html" %}`
  3. `<section id="tractor-filters" aria-labelledby="tractor-filters-title">` koji `{% include "products/partials/_filter_form.html" %}`
  4. `<section id="tractor-results-wrap" aria-labelledby="tractor-results-title">` sa `<h2 class="visually-hidden">` + `{% include "products/partials/_results_grid.html" %}`
- `{% block scripts %}` na bottom sa noUiSlider vendor CSS+JS i `tractor-filters.js`

### `templates/products/partials/_brand_header.html` (NOVO)

- `{% load i18n media_tags %}`
- Section Eyebrow (`{% include "partials/section_eyebrow.html" with text=_("BRENDOVI") tag="div" %}`)
- `<h2 id="brand-header-title" class="visually-hidden">{% translate "Brendovi traktora" %}</h2>`
- Grid `<div class="coric-brand-header__grid" data-testid="brand-header-grid">` iteracija kroz `brands_for_header`
- Per brand: `<a class="coric-brand-header__item" href="{% url 'brands:detail' slug=brand.slug %}" aria-label="..." data-testid="brand-header-link-{{ brand.slug }}">` wraps `{% responsive_picture brand.logo format='PNG' ... %}` (MP-D5 PNG policy)
- Brand bez logo-a → `<span class="coric-brand-header__name-fallback">{{ brand.name }}</span>` fallback
- Empty state `<p class="coric-brand-header__empty">{% translate "Nema brendova trenutno." %}</p>` ako 0 brendova

### `templates/products/partials/_filter_form.html` (NOVO)

- `{% load i18n %}`
- Section Eyebrow `{% include "partials/section_eyebrow.html" with text=_("FILTERI") tag="div" %}`
- Skriveni `<h2 id="tractor-filters-title" class="visually-hidden">{% translate "Filteri pretrage" %}</h2>`
- `<form id="tractor-filter-form" method="get" action="{% url 'products:tractor_list' %}" hx-get="{% url 'products:tractor_list' %}" hx-trigger="input changed delay:300ms, change delay:300ms" hx-target="#tractor-results" hx-swap="innerHTML" hx-push-url="true" hx-indicator="#filter-loading" class="coric-tractor-filters__form" data-testid="tractor-filter-form">`
- 2 `<fieldset>` (Snaga 0-500 KS step=10, Cena 0-200000 EUR step=500) sa `<legend>` + slider container + 2 hidden inputs (`snaga_min`/`snaga_max` ili `cena_min`/`cena_max`) sa `value="{{ active_filters.* }}"` form restore
- Slider container `<div class="coric-range-slider" data-range-slider data-min data-max data-step data-name-min data-name-max data-value-min data-value-max data-aria-label-min data-aria-label-max>` (SM-D20 A11Y-S — translated aria-label-min/max attributes)
- `<a href="{% url 'products:tractor_list' %}" class="coric-button coric-button--secondary" data-testid="reset-filters-button">{% translate "RESETUJ FILTERE" %}</a>` (SM-D6 full reload, NIJE HTMX)
- `<div id="filter-loading" class="coric-tractor-filters__loading htmx-indicator" aria-hidden="true">` sa Bootstrap `spinner-border-sm` + visually-hidden „Učitavanje rezultata…"
- NEMA `{% csrf_token %}` (GET form)

### `templates/products/partials/_results_grid.html` (NOVO)

- `{% load i18n media_tags %}`
- Outer `<div id="tractor-results" class="coric-tractor-results__inner" role="region" aria-labelledby="tractor-results-title" data-testid="tractor-results-grid">` (INVARIJANTAN ID — HTMX target)
- `{% if products %}` → grid iteracija kroz coric-product-card (linkable card + nested-interactive guard pattern Story 2.6 reuse)
- Per card: `<a class="coric-product-card" href="{{ product.get_absolute_url }}" aria-label="..." data-testid="tractor-card-{{ product.slug }}">` sa image + title `<h3>` + KS + EUR + CTA `<span aria-hidden="true">{% translate "OPŠIRNIJE" %}</span>`
- `{% else %}` → `{% include "products/partials/_empty_state.html" %}`
- Opciono pagination (SM-D8) sa `{% querystring page=N %}` (Django 5.2+) + HTMX `hx-get` + `hx-target="#tractor-results"` + `hx-push-url="true"` + dual `href` fallback (SM-D18 PAG fix)
- OOB div WRAPPED u `{% if request.htmx %}` guard (SM-D23 OOB fix):
  ```django
  {% if request.htmx %}
    <div hx-swap-oob="innerHTML:#aria-live">
      {% blocktranslate count counter=count %}Pronađen {{ counter }} model.{% plural %}Pronađeno {{ counter }} modela.{% endblocktranslate %}
    </div>
  {% endif %}
  ```

### `templates/products/partials/_empty_state.html` (NOVO)

- `{% load i18n %}`
- `<div class="coric-tractor-empty" data-testid="tractor-empty-state">`
- `<h3 class="coric-tractor-empty__title">{% translate "Nema modela koji odgovaraju vašim kriterijumima" %}</h3>`
- `<p class="coric-tractor-empty__lead">{% translate "Probajte da proširite opseg filtera ili poništite filtere i pregledajte celokupnu ponudu." %}</p>`
- `<a href="{% url 'products:tractor_list' %}" class="coric-button coric-button--primary" data-testid="empty-reset-button">{% translate "RESETUJ FILTERE" %}</a>`

---

## 4. JavaScript surface (`static/js/tractor-filters.js`)

IIFE + `'use strict';` (mirror Story 2.6 `statistic-counter.js`).

Public DOM contract:
- `[data-range-slider]` — slider container; module pozove `noUiSlider.create()` na svakom
- `[data-range-min-input]`, `[data-range-max-input]` — hidden inputs (HTMX form serialization target)
- `[data-range-value-min]`, `[data-range-value-max]` — visible value display spans
- `data-min`, `data-max`, `data-step`, `data-value-min`, `data-value-max`, `data-aria-label-min`, `data-aria-label-max`, `data-name-min`, `data-name-max` — attribute config

Required behaviors:
- noUiSlider init sa `handleAttributes: [{aria-label: dataset.ariaLabelMin}, {aria-label: dataset.ariaLabelMax}]` (SM-D20 A11Y-S)
- `animate: !window.matchMedia('(prefers-reduced-motion: reduce)').matches` (RED fix)
- `on('update', ...)` callback: sync hidden input values + visible display + `toggleDisabledForDefaults()` (SM-D19 URL fix — disable hidden inputs koji su na default extreme)
- `on('change', ...)` callback: dispatch `new Event('input', {bubbles: true})` na hidden input → HTMX `hx-trigger="input changed delay:300ms"` picks up
- `htmx:historyRestore` event listener: refresh `widget.noUiSlider.set([newMin, newMax])` iz hidden inputs (SM-D21 HIST fix)

---

## 5. CSS surface (`static/css/components/tractor-listing.css` + `range-slider.css`)

BEM `coric-` prefix; var(--token) reference (NE hex/px); `@media (prefers-reduced-motion: reduce)` blok.

Selektori:
- `.coric-tractor-listing` + `__header`, `__title`, `__lead`
- `.coric-brand-header__grid`, `__item`, `__logo`, `__name-fallback`, `__empty`
- `.coric-tractor-filters` + `__form`, `__group`, `__legend`, `__actions`, `__loading`
- `.coric-tractor-results` + `__inner`, `__grid`, `__pagination`, `__page-info`
- `.coric-tractor-empty` + `__title`, `__lead`
- `.coric-range-slider` + `__track`, `__values`, `__value-min`, `__value-max`, `__separator`, `__unit`
- `.htmx-indicator` (default opacity:0; `.htmx-request .htmx-indicator { opacity:1 }` + transition 200ms — SM-D13 min loading time)
- NE re-definisati `coric-product-card` (Story 2.6 owner)

`static/css/main.css` EDIT: dodaje 2 `@import` linije.

---

## 6. data-testid contract

Testovi assert na ovim selektorima — Dev NE SME ih menjati:

| testid | Element | Lokacija |
|---|---|---|
| `tractor-listing-page` | `<section>` outer wrapper | `tractor_listing.html` |
| `brand-header-grid` | `<div>` brand grid | `_brand_header.html` |
| `brand-header-link-{slug}` | `<a>` per brand | `_brand_header.html` |
| `tractor-filter-form` | `<form>` element | `_filter_form.html` |
| `reset-filters-button` | `<a>` RESETUJ FILTERE | `_filter_form.html` |
| `tractor-results-grid` | `<div id="tractor-results">` HTMX target | `_results_grid.html` |
| `tractor-card-{slug}` | `<a>` per product card | `_results_grid.html` |
| `pagination-prev` / `pagination-next` | `<a>` per pagination link | `_results_grid.html` (uslovno) |
| `tractor-empty-state` | `<div>` empty wrapper | `_empty_state.html` |
| `empty-reset-button` | `<a>` empty RESETUJ FILTERE | `_empty_state.html` |

---

## 7. Locale .po edits (sr/hu/en)

### Novi msgid (svi pokriveni `{% translate %}` ili `{% blocktranslate %}`):

```
Traktori
Filtrirajte traktore po snazi i ceni — kompletna ponuda svih brendova Ćorić Agrar-a.
Pronađite traktor koji odgovara vašoj farmi i budžetu.
BRENDOVI
Brendovi traktora
%(name)s — pregled brenda           (blocktranslate aria-label brand link)
Nema brendova trenutno.
FILTERI
Filteri pretrage
Snaga (KS)
Snaga minimum (konjske snage)
Snaga maksimum (konjske snage)
KS
Cena (EUR)
Cena minimum (EUR)
Cena maksimum (EUR)
EUR
RESETUJ FILTERE
Učitavanje rezultata…
Rezultati pretrage
OPŠIRNIJE
%(name)s — pregled modela           (blocktranslate aria-label product card)
Pronađen %(counter)s model.         (blocktranslate count=counter — sr 3 msgstr; en/hu 2)
Strana %(current)s od %(total)s     (blocktranslate pagination)
Prethodna
Sledeća
Paginacija
Nema modela koji odgovaraju vašim kriterijumima
Probajte da proširite opseg filtera ili poništite filtere i pregledajte celokupnu ponudu.
```

### sr nplurals=3 plural completion (SM-D15 — placeholder je `%(counter)s` per BT fix):

```po
msgid "Pronađen %(counter)s model."
msgid_plural "Pronađeno %(counter)s modela."
msgstr[0] "Pronađen %(counter)s model."
msgstr[1] "Pronađena %(counter)s modela."
msgstr[2] "Pronađeno %(counter)s modela."
```

### hu / en nplurals=2: popuni `msgstr[0]` + `msgstr[1]` sa odgovarajućim prevodima.

`just compilemessages` MORA emit 0 warninga.

---

## 8. Factory extensions (`apps/products/tests/factories.py`)

`TractorProductFactory` (NOVO classmethod helper):

```python
class TractorProductFactory:
    """Helper koji kreira Product u traktori scope-u.

    Kreira Category(is_for='traktori') + Subcategory + Product sa subcategory=...
    Pošto se ProductFactory koristi i u test_views_product_detail.py (NE smije
    biti tractor-scoped by default — to bi pokvarilo Story 2.7 tests), Story 2.8
    EXTEND je SAMO novi helper, NE menja ProductFactory default-e.
    """

    @classmethod
    def create(cls, brand=None, horse_power=None, price_eur=None, **overrides):
        from apps.brands.models import Category, Subcategory
        from apps.products.tests.factories import ProductFactory  # ili reuse local
        # Get or create traktori Category + Subcategory (shared across tests)
        category, _ = Category.objects.get_or_create(
            slug="traktori-default",
            defaults={"name": "Traktori Default", "is_for": "traktori"},
        )
        subcategory, _ = Subcategory.objects.get_or_create(
            category=category,
            slug="default-subcat",
            defaults={"name": "Default Subcat"},
        )
        overrides.setdefault("subcategory", subcategory)
        if horse_power is not None:
            overrides["horse_power"] = horse_power
        if price_eur is not None:
            overrides["price_eur"] = price_eur
        return ProductFactory.create(brand=brand, **overrides)
```

---

## 9. Query budget (SM-D14 + AC1)

Inicijalni page render bez filtera, sa paginate_by=24:

1. Brand list (`is_coming_soon=False ORDER BY name`)
2. Product COUNT(*) (Paginator total)
3. Product page slice sa select_related (`brand`, `series`, `subcategory`)
4. (Opciono) Image/main_image — direktan field na Product, NEMA dodatni query

**TEA test placeholder:** `assertNumQueries(5)` (Brand + Product count + Product slice +
sessions/middleware overhead). **Lock-uje se empirijski u GREEN fix iter 1** — view ne
postoji, ne može probe-ovati. Speculation: 3-5 SQL upita.

---

## 10. Out-of-scope (NE TEA, NE Dev)

- Range slider thumb drag E2E (Playwright Story 9.8)
- NVDA screen reader voice transcript (manual AC9)
- Lighthouse CLI a11y skor ≥ 95 (manual AC9 + Story 9.9 audit gate)
- HX-Trigger response header `coric:filter-applied` analytics (N5 NICE-TO-HAVE)
- Sort dropdown (open question — Story 9-x scope ako Mihas zatraži)
- `prefers-reduced-motion` runtime DevTools toggle (manual AC9)
- Infinite scroll (out-of-scope; SM-D8 paginate_by=24 chosen)

---

## 11. Adversarial fixes (mirror story SM-D18 … SM-D23)

| Fix ID | SM-D | Tema | Test coverage |
|---|---|---|---|
| SR3 | SM-D? | Filter restore na 4 nezavisna scenarija | `test_filter_restore.py` (parametrized 4) |
| PAG | SM-D18 | Pagination + HTMX integration | `test_htmx_tractor_filter.py::test_pagination_link_preserves_filter_params_and_uses_htmx` |
| OOB | SM-D23 | OOB div guarded `{% if request.htmx %}` | `test_htmx_tractor_filter.py::test_oob_div_*` (2 testa) |
| A11Y-S | SM-D20 | noUiSlider thumb aria-label | `test_templates_tractor_listing.py::test_slider_thumbs_have_aria_labels` |
| URL | SM-D19 | Disable empty inputs JS — manual smoke | N/A (JS-runtime; manual AC9) |
| HIST | SM-D21 | historyRestore re-init — manual smoke | N/A (browser-runtime; manual AC9) |
| VEN | SM-D22 | noUiSlider vendor pin LICENSE | `test_templates_tractor_listing.py::test_vendor_nouislider_files_exist` |
| BT | SM-D15 | blocktranslate `%(counter)s` placeholder | `test_htmx_tractor_filter.py::test_oob_count_message_is_pluralized` |
| RED | (SM-D4 + Subtask 7.12) | `animate: false` ako reduce-motion — manual smoke | N/A (browser-runtime) |
