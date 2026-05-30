---
story-id: "2.9"
story-key: 2-9-used-machinery-listing-sa-filterima
artifact: interface-contract
created: 2026-05-30
author: TEA / Murat (RED phase)
purpose: Canonical contract for Used Machinery Listing strana sa HTMX filterima — URL pattern,
         UsedMachineryListView CBV, 1 main template + 3 partials, REUSE noUiSlider + tractor-filters.js
         + range-slider.css iz Story 2.8 (NEMA novi JS modul, NEMA novi vendor), 1 nova CSS komponenta,
         locale .po edits, data-testid surface. Dev MORA satisfy svaku klauzulu u GREEN phase.
         DRUGA HTMX story u Epic 2 — proširuje Story 2.8 kanonski pattern sa multi-dropdown +
         sort + pagination kombinatorikom; uvodi sort whitelist SECURITY pattern + Paginator.get_page()
         overflow safety.
---

# Interface Contract — Story 2.9 Used Machinery Listing sa HTMX Filterima

Story 2.9 dodaje NOVI URL `/sr/mehanizacija/polovna/` (prvi „mehanizacija" scope URL u
repository-ju; ne shadow-uje Story 2.6 `/sr/traktori/<brand-slug>/` ni Story 2.8
`/sr/traktori/` ni Story 2.7 `/sr/proizvod/<slug>/`), NOVI `UsedMachineryListView` CBV
(ListView sa `@vary_on_headers("HX-Request")` dekoratorom + `Paginator.get_page()` override),
1 glavni template + 3 partials, NOVA `used-machinery-listing.css` komponenta, locale .po edits
(REUSE pluralized count msgid iz Story 2.8 .po + dodaje ~25 NOVIH msgid-a za Story 2.9).

**REUSE iz Story 2.8 1:1 (NEMA edit, NEMA copy):**
- `static/vendor/nouislider/` (LICENSE.md + VERSION.txt + nouislider.min.js + nouislider.min.css)
- `static/js/tractor-filters.js` (generic IIFE — radi na BILO KOM `[data-range-slider]` container-u)
- `static/css/components/range-slider.css` (site-wide BEM `coric-range-slider`)
- `static/css/components/brand-listing.css` (site-wide BEM `coric-product-card`)
- `apps/products/views.py` module-level `_parse_int` + `_parse_decimal` helperi
- `apps/products/views.py` module-level `_PRODUCTS_PER_PAGE` konstanta (NEMA reuse — Story 2.9
  koristi 12, novu konstantu `_USED_MACHINERY_PER_PAGE = 12` per SM-D8)

Ovaj ugovor enumerise file-system delta + Python surface + template + DOM/data-testid
surface + CSS klase + locale .po keys koje TEA RED-phase testovi verifikuju. Dev
GREEN-phase realizuje sve klauzule; bilo koje odstupanje vraća story u `paused`.

---

## 1. File-system delta

### Fajlovi koji MORAJU postojati posle GREEN phase (5 NEW + 6 EDIT, 0 DELETE)

| Path | Status | Vlasništvo |
|---|---|---|
| `apps/products/views.py` | EDIT (ADD class + imports + 2 konstante) | `UsedMachineryListView` CBV — postojeći `ProductDetailView` + `TractorListView` NETAKNUTI |
| `apps/products/urls.py` | EDIT (ADD path) | `path("mehanizacija/polovna/", views.UsedMachineryListView.as_view(), name="used_machinery_list")` posle postojećeg `traktori/` |
| `templates/products/used_machinery_listing.html` | NOVO (Dev) | Glavni template — extends base.html |
| `templates/products/partials/_used_filter_form.html` | NOVO (Dev) | Filter form (2 dropdown + 1 hidden input + 2 range slidera + 1 sort dropdown + RESETUJ FILTERE CTA + loading) |
| `templates/products/partials/_used_results_grid.html` | NOVO (Dev) | Results grid + pagination + OOB aria-live (HTMX target id="used-results") |
| `templates/products/partials/_used_empty_state.html` | NOVO (Dev) | Empty state markup sa „POGLEDAJ NOVE TRAKTORE" CTA (FR-13 verbatim) |
| `static/css/components/used-machinery-listing.css` | NOVO (Dev) | Layout (page header, filter form grid, results grid, pagination, empty state) |
| `static/css/main.css` | EDIT | +1 `@import url('./components/used-machinery-listing.css');` linija |
| `locale/sr/LC_MESSAGES/django.po` | EDIT | Popuni msgstr za ~25 novih msgid-a (REUSE pluralized count msgid iz Story 2.8) |
| `locale/hu/LC_MESSAGES/django.po` | EDIT | Popuni hu prevode (nplurals=2) |
| `locale/en/LC_MESSAGES/django.po` | EDIT | Popuni en prevode (nplurals=2) |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | EDIT (Dev/Orchestrator) | Story 2-9 status: `ready-for-dev` → `in-progress` (Dev start) → `review` (Dev end) |
| `apps/products/tests/test_used_machinery_view.py` | NOVO (TEA) | AC1+AC2 view-layer (URL resolve, queryset, sort whitelist, pagination overflow, context, Vary header) |
| `apps/products/tests/test_used_machinery_filters.py` | NOVO (TEA) | AC2 defensive parsing + invalid kategorija slug normalization + sort fallback |
| `apps/products/tests/test_used_machinery_htmx.py` | NOVO (TEA) | AC2+AC5 HTMX branching + OOB aria-live + pluralized count + hx-push-url + pagination preserva filter+sort |
| `apps/products/tests/test_used_machinery_templates.py` | NOVO (TEA) | AC3+AC4+AC5+AC6+AC7 template structure + 2 dropdown + 2 slider + 1 sort + stanje hidden + empty state copy verbatim + vendor refs |
| `apps/products/tests/test_used_machinery_i18n.py` | NOVO (TEA) | AC8 i18n: sr/hu/en URL resolve + sr nplurals=3 plural completion za count |
| `apps/products/tests/test_used_machinery_security.py` | NOVO (TEA) | AC2 security: SQL/ORDER BY injection u sort, stanje=new defensive guard (no scope expand), no auth required (public page) |
| `apps/products/tests/factories.py` | EDIT (TEA) | EXTEND sa `UsedProductFactory` (kreira `Product(condition="used", subcategory__category__is_for="mehanizacija")`) |

Vendor files (NETAKNUTI — REUSE iz Story 2.8):
- `static/vendor/nouislider/nouislider.min.js`
- `static/vendor/nouislider/nouislider.min.css`
- `static/vendor/nouislider/LICENSE.md`
- `static/vendor/nouislider/VERSION.txt`

Static assets (NETAKNUTI — REUSE iz Story 2.8 + 2.6):
- `static/js/tractor-filters.js`
- `static/css/components/range-slider.css`
- `static/css/components/brand-listing.css` (coric-product-card BEM owner)

---

## 2. Python surface

### `apps/products/views.py` (EDIT)

#### Module-level imports — Dev MORA verifikovati i dodati ŠTA NEDOSTAJE (SM-D22 import discipline)

Postojeće (NE re-import):
- `from django.utils.decorators import method_decorator` (postoji linija 16)
- `from django.utils.translation import gettext_lazy as _` (postoji linija 17)
- `from django.views.decorators.vary import vary_on_headers` (postoji linija 18)
- `from django.views.generic import DetailView, ListView` (postoji linija 19)

EDIT postojeće linije:
- Linija 21: `from apps.brands.models import Brand` → **`from apps.brands.models import Brand, Category`**

DODAJ novi import (Django utility group, grupisan sa `from django.*`):
- **`from django.utils import timezone`**

KRITIČNO (SM-D22): NIKAD `from … import …` UNUTAR `get_queryset()` ili `get_context_data()`
metoda — ruff E402/F811 lint failure ili NameError ako Dev kopira AC2 source skeleton verbatim.

#### Module-level constants (POSLE postojeće `_PRODUCTS_PER_PAGE = 24`)

```python
_USED_MACHINERY_PER_PAGE = 12  # Per epics.md FR-13 (SM-D8)

# Sort whitelist (SECURITY — prevent ORDER BY injection per SM-D7 + AC2 SECURITY).
# Whitelist 4 keys; queryset.order_by() prima SAMO whitelisted DB column references.
_USED_SORT_OPTIONS = {
    "default": "-created_at",   # Najnovije prvo
    "cena_asc": "price_eur",    # Cena rastuće
    "cena_desc": "-price_eur",  # Cena opadajuće
    "godina_desc": "-year",     # Godina opadajuće
}
```

#### `UsedMachineryListView` (POSLE postojeće `TractorListView`)

```python
@method_decorator(vary_on_headers("HX-Request"), name="dispatch")
class UsedMachineryListView(ListView):
    """Polovna mehanizacija listing strana sa HTMX filterima — Story 2.9.

    DRUGA HTMX story u Epic 2 — proširuje Story 2.8 single-view request.htmx branching
    pattern (SM-D3) sa multi-dropdown + sort + pagination kombinatorikom. Sort whitelist
    SECURITY (SM-D7) + Paginator.get_page() overflow safety (SM-D25) su Story 2.9
    novi patterni; svi ostali HTMX/CSS/JS patterni su REUSE iz Story 2.8.

    SM-D21 (cache poisoning defense): @vary_on_headers("HX-Request") REUSE iz Story 2.8
    SM-D24 — sprečava CDN/browser cache da serve-uje full-page response na HTMX request
    (broken UX) ili obrnuto.
    """

    model = Product
    context_object_name = "products"
    paginate_by = _USED_MACHINERY_PER_PAGE

    def get_template_names(self):
        if getattr(self.request, "htmx", False):
            return ["products/partials/_used_results_grid.html"]
        return ["products/used_machinery_listing.html"]

    def get_queryset(self):
        # SM-D2 used scope: condition='used' hardcoded; stanje filter NIJE permitted to
        # expand scope (security: javni URL ne sme biti repurposed).
        qs = (
            Product.objects.filter(
                is_published=True,
                condition="used",
            )
            .select_related("brand", "subcategory", "subcategory__category")
        )

        # SM-D11 defensive parsing (REUSE _parse_int/_parse_decimal iz Story 2.8 module-level).

        kategorija_slug = self.request.GET.get("kategorija", "").strip()
        if kategorija_slug:
            qs = qs.filter(
                subcategory__category__slug=kategorija_slug,
                subcategory__category__is_for="mehanizacija",
            )

        brend_slug = self.request.GET.get("brend", "").strip()
        if brend_slug:
            qs = qs.filter(brand__slug=brend_slug)

        cena_min = _parse_decimal(self.request.GET.get("cena_min"))
        cena_max = _parse_decimal(self.request.GET.get("cena_max"))
        if cena_min is not None:
            qs = qs.filter(price_eur__gte=cena_min)
        if cena_max is not None:
            qs = qs.filter(price_eur__lte=cena_max)

        godina_min = _parse_int(self.request.GET.get("godina_min"), min_value=1900, max_value=2100)
        godina_max = _parse_int(self.request.GET.get("godina_max"), min_value=1900, max_value=2100)
        if godina_min is not None:
            qs = qs.filter(year__gte=godina_min)
        if godina_max is not None:
            qs = qs.filter(year__lte=godina_max)

        # Stanje filter no-op u v1 (condition='used' hardcoded above per SM-D2).
        # Defensive guard: ?stanje=new se ignoriše — NE sme expand scope na NEW.

        # Sort whitelist SECURITY (SM-D7): prevent ORDER BY injection.
        sort_key = self.request.GET.get("sort", "default").strip()
        if sort_key not in _USED_SORT_OPTIONS:
            sort_key = "default"
        qs = qs.order_by(_USED_SORT_OPTIONS[sort_key])

        return qs

    def paginate_queryset(self, queryset, page_size):
        # SM-D25 pagination overflow safety — Paginator.get_page() clamps invalid/
        # out-of-range page numbers na last available page (NIJE 404 EmptyPage).
        paginator = self.get_paginator(
            queryset,
            page_size,
            orphans=self.get_paginate_orphans(),
            allow_empty_first_page=self.get_allow_empty(),
        )
        page_kwarg = self.page_kwarg
        page = self.kwargs.get(page_kwarg) or self.request.GET.get(page_kwarg) or 1
        page_obj = paginator.get_page(page)
        return (paginator, page_obj, page_obj.object_list, page_obj.has_other_pages())

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        ctx["categories_for_dropdown"] = Category.objects.filter(
            is_for="mehanizacija"
        ).order_by("display_order", "name")

        ctx["brands_for_dropdown"] = Brand.objects.filter(
            is_coming_soon=False
        ).order_by("name")

        active_filters = {
            "kategorija": self.request.GET.get("kategorija", ""),
            "brend": self.request.GET.get("brend", ""),
            "cena_min": self.request.GET.get("cena_min", ""),
            "cena_max": self.request.GET.get("cena_max", ""),
            "godina_min": self.request.GET.get("godina_min", ""),
            "godina_max": self.request.GET.get("godina_max", ""),
            "stanje": self.request.GET.get("stanje", "used"),
        }

        # IMP-3 normalization: invalid kategorija slug → reset na "" za form-restore
        # koherenciju sa dropdown setom (queryset još uvek vraća 0 results — empty state handluje).
        valid_kategorija_slugs = {c.slug for c in ctx["categories_for_dropdown"]}
        if active_filters["kategorija"] and active_filters["kategorija"] not in valid_kategorija_slugs:
            active_filters["kategorija"] = ""

        ctx["active_filters"] = active_filters

        sort_key = self.request.GET.get("sort", "default").strip()
        if sort_key not in _USED_SORT_OPTIONS:
            sort_key = "default"
        ctx["selected_sort"] = sort_key

        ctx["sort_options"] = [
            ("default", _("Najnovije prvo (datum dodavanja)")),
            ("cena_asc", _("Cena: rastuće")),
            ("cena_desc", _("Cena: opadajuće")),
            ("godina_desc", _("Godina: opadajuće")),
        ]

        ctx["count"] = ctx["paginator"].count

        # SM-D6 static year range — UI slider scope 1990 to current year.
        # Parser bounds (1900-2100) are intentionally wider per defensive parsing pattern.
        ctx["year_min_range"] = 1990
        ctx["year_max_range"] = timezone.now().year

        return ctx
```

### `apps/products/urls.py` (EDIT — ADD path)

```python
urlpatterns = [
    path("proizvod/<slug:slug>/", views.ProductDetailView.as_view(), name="detail"),
    path("traktori/", views.TractorListView.as_view(), name="tractor_list"),
    # Story 2.9 — SM-D1: `mehanizacija/polovna/` statički dvoslojni path bez slug-a;
    # ne shadow-uje nijedan postojeći pattern.
    path(
        "mehanizacija/polovna/",
        views.UsedMachineryListView.as_view(),
        name="used_machinery_list",
    ),
]
```

URL deconfliction (SM-D1): `mehanizacija/polovna/` je statički — ne overlap-uje sa
`traktori/<slug:slug>/` (brands:detail) ni `traktori/` (tractor_list) ni `proizvod/<slug:slug>/`
(detail). Resolver-u redosled je irelevantan jer pattern ne match-uje nijedan postojeći.

### Context surface (svaki request — full page i HTMX)

| Key | Tip | Opis |
|---|---|---|
| `products` | QuerySet[Product] | Current page slice (paginate_by=12) |
| `categories_for_dropdown` | QuerySet[Category] | `is_for="mehanizacija"` ordered by display_order, name |
| `brands_for_dropdown` | QuerySet[Brand] | `is_coming_soon=False` ordered by name |
| `active_filters` | dict[str, str] | 7 string vrednosti (kategorija, brend, cena_min/max, godina_min/max, stanje); stanje default "used" |
| `selected_sort` | str | Jedan od ključeva u `_USED_SORT_OPTIONS`; default "default" |
| `sort_options` | list[tuple[str, lazy_str]] | 4 tuple-a sa translated labelama |
| `count` | int | Total broj filtriranih rezultata across all pages (paginator.count) |
| `paginator`, `page_obj`, `is_paginated` | Django ListView defaults | Present (paginate_by=12 set) |
| `year_min_range` | int | 1990 (SM-D6 static) |
| `year_max_range` | int | `timezone.now().year` (SM-D6 current year) |

### HTMX branching

- `request.htmx == True` → `get_template_names()` returns `["products/partials/_used_results_grid.html"]`
- `request.htmx == False` → returns `["products/used_machinery_listing.html"]`

OOB aria-live `<div hx-swap-oob="innerHTML:#aria-live">` MORA biti wrapped u
`{% if request.htmx %}` guard u `_used_results_grid.html` (SM-D23 OOB fix — sprečava
plain-text render u inicijalnom server-side full-page render-u).

### Vary header (SM-D21 cache poisoning defense)

`@method_decorator(vary_on_headers("HX-Request"), name="dispatch")` na klasu MORA emit
`Vary: HX-Request` header u response (verifikuj: `response.headers.get("Vary", "")`
mora sadržati substring `"HX-Request"`).

### Pagination overflow safety (SM-D25)

`paginate_queryset` override koristi `Paginator.get_page(page)` umesto default
`Paginator.page(page)`. `get_page()` clamps invalid `?page=999` na last page (NIJE 404).

---

## 3. Template surface

### `templates/products/used_machinery_listing.html` (main, NOVO)

- `{% extends "base.html" %}` + `{% load i18n static media_tags htmx_aria %}`
- `{% block title %}{% translate "Polovna mehanizacija" %} | Ćorić Agrar{% endblock %}`
- `{% block meta_description %}{% blocktranslate %}Polovna poljoprivredna mehanizacija — filtrirajte po kategoriji, brendu, ceni i godini proizvodnje.{% endblocktranslate %}{% endblock %}`
- `{% block content %}` sadrži outer `<section class="coric-used-machinery-listing" data-testid="used-machinery-listing-page" aria-labelledby="used-machinery-listing-title">` wrapper (NIJE drugi `<main>`)
- **3 sekcije TAČNIM redosledom** (NEMA brand header sekcije — różnica vs Story 2.8):
  1. Page heading (`<header>` + JEDINI `<h1 id="used-machinery-listing-title">Polovna mehanizacija</h1>` + lead `<p>`)
  2. `<section id="used-filters" aria-labelledby="used-filters-title">` koji `{% include "products/partials/_used_filter_form.html" %}`
  3. `<section id="used-results-wrap" aria-labelledby="used-results-title">` sa visually-hidden `<h2>` + `{% include "products/partials/_used_results_grid.html" %}`
- `{% block scripts %}` na bottom REUSE iz Story 2.8 (IDENTIČNI 3 line-a):
  ```django
  <link rel="stylesheet" href="{% static 'vendor/nouislider/nouislider.min.css' %}">
  <script src="{% static 'vendor/nouislider/nouislider.min.js' %}" defer></script>
  <script src="{% static 'js/tractor-filters.js' %}" defer></script>
  ```

### `templates/products/partials/_used_filter_form.html` (NOVO)

- `{% load i18n %}`
- Section Eyebrow `{% include "partials/section_eyebrow.html" with text=_("FILTERI") tag="div" %}`
- Skriveni `<h2 id="used-filters-title" class="visually-hidden">{% translate "Filteri pretrage polovne mehanizacije" %}</h2>`
- `<form id="used-filter-form" method="get" action="{% url 'products:used_machinery_list' %}" hx-get="{% url 'products:used_machinery_list' %}" hx-trigger="input changed delay:300ms, change delay:300ms" hx-target="#used-results" hx-swap="innerHTML" hx-push-url="true" hx-indicator="#used-filter-loading" class="coric-used-machinery-filters__form" data-testid="used-filter-form">`
- **2 dropdown filtera** (Kategorija, Brend) sa `<label for="filter-...">` + `<select name="kategorija/brend">` + iteracija opcija iz `categories_for_dropdown` / `brands_for_dropdown` queryset-a; svaki dropdown ima default `<option value="">` („Sve kategorije" / „Svi brendovi") + `{% if active_filters.X == option.slug %}selected{% endif %}` restore
- **2 range slidera** (Cena 0-200000 step=500, Godina year_min_range-year_max_range step=1) sa `<div class="coric-range-slider" data-range-slider data-min data-max data-step data-name-min data-name-max data-value-min data-value-max data-aria-label-min data-aria-label-max>` + 2 `<input type="hidden">` sa `value="{{ active_filters.* }}"` form restore
- **1 sort dropdown** sa `<label for="filter-sort">` + `<select name="sort">` + iteracija kroz `sort_options` sa `{% if selected_sort == sort_key %}selected{% endif %}`
- **1 stanje hidden input** (SM-D26 IMP-6): `<input type="hidden" name="stanje" value="used" data-testid="filter-stanje">`
- **RESETUJ FILTERE CTA**: `<a href="{% url 'products:used_machinery_list' %}" class="coric-button coric-button--secondary" data-testid="reset-filters-button">{% translate "RESETUJ FILTERE" %}</a>` (SM-D6 full reload, NIJE HTMX)
- **Loading indicator**: `<div id="used-filter-loading" class="coric-used-machinery-filters__loading htmx-indicator" aria-hidden="true">` sa Bootstrap `spinner-border-sm` + visually-hidden „Učitavanje rezultata…"
- NEMA `{% csrf_token %}` (GET form)

### `templates/products/partials/_used_results_grid.html` (NOVO)

- `{% load i18n media_tags %}`
- Outer `<div id="used-results" class="coric-used-machinery-results__inner" role="region" aria-labelledby="used-results-title" data-testid="used-results-grid">` (INVARIJANTAN ID — HTMX target)
- `{% if products %}` → grid iteracija kroz `coric-product-card` linkable kartice (REUSE Story 2.6 BEM):
  - Per card: `<a class="coric-product-card" href="{{ product.get_absolute_url }}" aria-label="{% blocktranslate %}{{ name }} — pregled polovnog modela{% endblocktranslate %}" data-testid="used-card-{{ product.slug }}">` sa image + `<h3>` title + **`product.year` display** (NOVI element vs Story 2.8 grid) + EUR + CTA `<span aria-hidden="true">{% translate "OPŠIRNIJE" %}</span>`
  - Year display sa `visually-hidden` „Godina proizvodnje:" prefix (SM-D12 WCAG SC 1.3.1):
    ```django
    {% if product.year %}
      <p class="coric-product-card__spec coric-product-card__year">
        <span class="visually-hidden">{% translate "Godina proizvodnje:" %}</span>
        {{ product.year }}
      </p>
    {% endif %}
    ```
- `{% else %}` → `{% include "products/partials/_used_empty_state.html" %}`
- Pagination markup `{% if is_paginated %}` sa dual `hx-get` + `href` (HTMX path + fallback) + `{% querystring %}` Django 5.2 tag preserving filter+sort params (SM-D9):
  ```django
  <nav class="coric-used-machinery-results__pagination" aria-label="{% translate 'Paginacija' %}">
    {% if page_obj.has_previous %}
      <a hx-get="?{% querystring page=page_obj.previous_page_number %}"
         hx-target="#used-results"
         hx-swap="innerHTML"
         hx-push-url="true"
         href="?{% querystring page=page_obj.previous_page_number %}"
         class="coric-button coric-button--secondary"
         data-testid="pagination-prev">{% translate "Prethodna" %}</a>
    {% endif %}
    <span class="coric-used-machinery-results__page-info">
      {% blocktranslate with current=page_obj.number total=paginator.num_pages %}Strana {{ current }} od {{ total }}{% endblocktranslate %}
    </span>
    {% if page_obj.has_next %}
      <a hx-get="?{% querystring page=page_obj.next_page_number %}"
         hx-target="#used-results"
         hx-swap="innerHTML"
         hx-push-url="true"
         href="?{% querystring page=page_obj.next_page_number %}"
         class="coric-button coric-button--secondary"
         data-testid="pagination-next">{% translate "Sledeća" %}</a>
    {% endif %}
  </nav>
  ```
- OOB div WRAPPED u `{% if request.htmx %}` guard (SM-D23 OOB fix) sa pluralized count REUSE-ujući IDENTIČAN msgid iz Story 2.8:
  ```django
  {% if request.htmx %}
    <div hx-swap-oob="innerHTML:#aria-live">
      {% blocktranslate count counter=count %}Pronađen {{ counter }} model.{% plural %}Pronađeno {{ counter }} modela.{% endblocktranslate %}
    </div>
  {% endif %}
  ```

### `templates/products/partials/_used_empty_state.html` (NOVO)

- `{% load i18n %}`
- `<div class="coric-used-machinery-empty" data-testid="used-empty-state">`
- `<h3 class="coric-used-machinery-empty__title">{% translate "Trenutno nemamo polovne mehanizacije u ponudi" %}</h3>` (**EKSPLICITNO iz epics.md FR-13 — Dev NE SME parafrazirati**)
- `<p class="coric-used-machinery-empty__lead">{% translate "Pogledajte našu ponudu novih traktora ili promenite kriterijume pretrage." %}</p>`
- `<a href="{% url 'products:tractor_list' %}" class="coric-button coric-button--primary" data-testid="empty-view-new-tractors-button">{% translate "POGLEDAJ NOVE TRAKTORE" %}</a>` (**EKSPLICITNO iz epics.md FR-13 — Dev NE SME parafrazirati**; CTA vodi na Story 2.8 tractor_list URL — full reload)

---

## 4. JavaScript surface — NEMA NOVI JS MODUL

Story 2.9 REUSE-uje `static/js/tractor-filters.js` (Story 2.8 deliverable) 1:1. Verifikovano
da je modul generic IIFE — radi na BILO KOM `[data-range-slider]` container-u; nema „tractor"-
specific selektor coupling.

Story 2.9 dropdown filteri (Kategorija, Brend) + sort dropdown rade BEZ JS-a — native
`<select>` element + HTMX `change delay:300ms` form-level trigger handluje all `<select>`
change events automatski.

Story 2.9 stanje filter je `<input type="hidden">` — NE renderuje UI control (per SM-D26
IMP-6 — jednoopcioni dropdown je UX noise).

---

## 5. CSS surface (`static/css/components/used-machinery-listing.css` — NOVO)

BEM `coric-` prefix; var(--token) reference (NE hex/px); `@media (prefers-reduced-motion: reduce)` blok.

Selektori:
- `.coric-used-machinery-listing` + `__header`, `__title`, `__lead`
- `.coric-used-machinery-filters` + `__form`, `__group`, `__label`, `__legend`, `__select`, `__actions`, `__loading`
- `.coric-used-machinery-results` + `__inner`, `__grid`, `__pagination`, `__page-info`
- `.coric-used-machinery-empty` + `__title`, `__lead`
- (opciono) `.coric-product-card__year` modifier — ako `brand-listing.css` Story 2.6 grid card BEM ne pokriva year display styling
- NE re-definisati `coric-range-slider` (Story 2.8 owner — `range-slider.css`)
- NE re-definisati `coric-product-card` (Story 2.6 owner — `brand-listing.css`)

`static/css/main.css` EDIT: dodaje TAČNO 1 nova `@import url('./components/used-machinery-listing.css');` linija.

---

## 6. data-testid contract

Testovi assert na ovim selektorima — Dev NE SME ih menjati:

| testid | Element | Lokacija |
|---|---|---|
| `used-machinery-listing-page` | `<section>` outer wrapper | `used_machinery_listing.html` |
| `used-filter-form` | `<form>` element | `_used_filter_form.html` |
| `filter-kategorija` | `<select name="kategorija">` | `_used_filter_form.html` |
| `filter-brend` | `<select name="brend">` | `_used_filter_form.html` |
| `filter-sort` | `<select name="sort">` | `_used_filter_form.html` |
| `filter-stanje` | `<input type="hidden" name="stanje">` (SM-D26) | `_used_filter_form.html` |
| `reset-filters-button` | `<a>` RESETUJ FILTERE | `_used_filter_form.html` |
| `used-results-grid` | `<div id="used-results">` HTMX target | `_used_results_grid.html` |
| `used-card-{slug}` | `<a>` per product card | `_used_results_grid.html` |
| `pagination-prev` / `pagination-next` | `<a>` per pagination link | `_used_results_grid.html` (uslovno na `is_paginated`) |
| `used-empty-state` | `<div>` empty wrapper | `_used_empty_state.html` |
| `empty-view-new-tractors-button` | `<a>` POGLEDAJ NOVE TRAKTORE CTA | `_used_empty_state.html` |

---

## 7. Locale .po edits (sr/hu/en)

### REUSE iz Story 2.8 (NE pravi novi prevod):

```po
msgid "Pronađen %(counter)s model."
msgid_plural "Pronađeno %(counter)s modela."
msgstr[0] "Pronađen %(counter)s model."
msgstr[1] "Pronađena %(counter)s modela."
msgstr[2] "Pronađeno %(counter)s modela."
```
(sr nplurals=3; hu/en nplurals=2 — popunjeno u Story 2.8)

Plus REUSE: `RESETUJ FILTERE`, `Učitavanje rezultata…`, `OPŠIRNIJE`, `Cena (EUR)`, `EUR`,
`Prethodna`, `Sledeća`, `Paginacija`, `Strana %(current)s od %(total)s`.

### NOVI msgid za Story 2.9 (~25 keys — popuni za sva 3 locale-a):

```
Polovna mehanizacija
Polovna poljoprivredna mehanizacija — filtrirajte po kategoriji, brendu, ceni i godini proizvodnje.
Pregled polovnih mašina iz naše ponude — filtrirajte po kategoriji, brendu, ceni i godini proizvodnje.
Filteri pretrage polovne mehanizacije
Rezultati pretrage polovne mehanizacije
Kategorija
Sve kategorije
Brend
Svi brendovi
Godina proizvodnje
Godina minimum
Godina maksimum
Godina proizvodnje:                            (visually-hidden card prefix — WCAG SC 1.3.1)
Sortiraj po
Najnovije prvo (datum dodavanja)
Cena: rastuće
Cena: opadajuće
Godina: opadajuće
Trenutno nemamo polovne mehanizacije u ponudi  (EKSPLICITNO iz epics.md FR-13)
Pogledajte našu ponudu novih traktora ili promenite kriterijume pretrage.
POGLEDAJ NOVE TRAKTORE                          (EKSPLICITNO iz epics.md FR-13)
%(name)s — pregled polovnog modela              (blocktranslate aria-label per card)
Cena minimum (EUR)                              (slider data-aria-label-min — REUSE iz 2.8 ako postoji)
Cena maksimum (EUR)                             (slider data-aria-label-max)
```

`just compilemessages` MORA emit 0 warninga.

---

## 8. Factory extensions (`apps/products/tests/factories.py`)

### `UsedProductFactory` (NOVO classmethod helper)

```python
class UsedProductFactory:
    """Helper koji kreira Product u USED + mehanizacija scope-u za Story 2.9 testove.

    Story 2.9 UsedMachineryListView filter:
        Product.objects.filter(
            is_published=True,
            condition='used',
        )

    Kategorija filter (opcionalno) primenjuje subcategory__category__is_for='mehanizacija'.

    Kreira shared Category(is_for='mehanizacija') + Subcategory + delegira na
    ProductFactory.create() sa condition='used' i subcategory= override.
    NE menja postojeći TractorProductFactory (Story 2.8 owner — koristi 'traktori' scope).
    """

    _SHARED_CATEGORY_SLUG = "tea-mehanizacija-default"
    _SHARED_SUBCATEGORY_SLUG = "tea-mech-default-subcat"

    @classmethod
    def _get_or_create_subcategory(cls):
        from apps.brands.models import Category, Subcategory
        category, _ = Category.objects.get_or_create(
            slug=cls._SHARED_CATEGORY_SLUG,
            defaults={"name": "TEA Mehanizacija Default", "is_for": "mehanizacija"},
        )
        subcategory, _ = Subcategory.objects.get_or_create(
            category=category,
            slug=cls._SHARED_SUBCATEGORY_SLUG,
            parent=None,
            defaults={"name": "TEA Mehanizacija Default Subcat"},
        )
        return subcategory

    @classmethod
    def create(cls, brand=None, year=None, price_eur=None, **overrides):
        subcategory = cls._get_or_create_subcategory()
        overrides.setdefault("subcategory", subcategory)
        overrides.setdefault("condition", "used")
        if year is not None:
            overrides["year"] = year
        if price_eur is not None:
            overrides["price_eur"] = price_eur
        return ProductFactory.create(brand=brand, **overrides)

    @classmethod
    def create_unpublished(cls, **overrides):
        overrides["is_published"] = False
        return cls.create(**overrides)
```

---

## 9. Query budget (SM-D27 + AC1)

Inicijalni page render bez filtera, sa paginate_by=12:

1. Categories dropdown (`WHERE is_for='mehanizacija' ORDER BY display_order, name`)
2. Brands dropdown (`WHERE is_coming_soon=FALSE ORDER BY name`)
3. Product COUNT(*) (Paginator total — `condition='used' AND is_published=TRUE`)
4. Product page slice sa select_related (`brand`, `subcategory`, `subcategory__category`)
5. (Opciono) middleware overhead (LocaleMiddleware, session)

**TEA test placeholder:** `assertNumQueries(5)` SOFT starting point. **Dev MORA empirijski
lock-ovati posle GREEN iter 1** per Story 2.8 SM-D14 + Story 2.9 SM-D27 discipline; tail-up
za middleware queries (locale, session, auth) je očekivano i NEMA krivnja.

---

## 10. Sprint-status workflow

| Phase | Status |
|---|---|
| SM hand-off (Step 1 complete) | `ready-for-dev` |
| Dev start (Step 3) | `in-progress` |
| Dev end (Step 3 complete, tests pass) | `review` |
| Code review pass (Step 4) | `done` |

---

## 11. Out-of-scope (NE TEA, NE Dev)

- Range slider thumb drag E2E (Playwright Story 9.8)
- NVDA screen reader voice transcript verification (manual AC8)
- Lighthouse CLI a11y ≥ 95 (manual AC8 + Story 9.9 audit gate)
- `prefers-reduced-motion` runtime DevTools toggle (manual AC8)
- HX-Trigger response header `coric:filter-applied` analytics (NICE-TO-HAVE)
- Infinite scroll (out-of-scope; SM-D8 paginate_by=12 chosen)
- Cascading dropdown (Brend filter dynamic na osnovu Kategorija) — SM-D5 explicit decline u v1

---

## 12. Adversarial fixes (mirror story SM-D fixes)

| Fix ID | SM-D | Tema | Test coverage |
|---|---|---|---|
| URL-DECONFLICT | SM-D1 | `mehanizacija/polovna/` ne shadow-uje postojeće pattern | `test_used_machinery_view.py::test_used_url_does_not_shadow_*` (4 testa) |
| HARDLOCK | SM-D2 | `condition='used'` hardcoded; `?stanje=new` ignored | `test_used_machinery_security.py::test_stanje_new_does_not_expand_scope` |
| SORT-WHITELIST | SM-D7 | ORDER BY injection defense | `test_used_machinery_security.py::test_sort_sql_injection_falls_back_to_default` |
| PAG-OVERFLOW | SM-D25 | `Paginator.get_page()` clamps overflow | `test_used_machinery_view.py::test_pagination_out_of_range_page_clamps_to_last_page` |
| OOB-GUARD | SM-D23 | OOB div wrapped u `{% if request.htmx %}` | `test_used_machinery_htmx.py::test_oob_div_*` (2 testa) |
| BT | SM-D15 | `%(counter)s` placeholder + sr nplurals=3 | `test_used_machinery_i18n.py::test_pluralized_count_*` (3 testa) |
| KAT-NORM | SM-D11 IMP-3 | Invalid kategorija slug → active_filters reset to "" | `test_used_machinery_filters.py::test_invalid_kategorija_slug_resets_active_filter` |
| YEAR-RANGE | SM-D6 | `year_min_range=1990, year_max_range=current_year` | `test_used_machinery_view.py::test_get_context_data_year_range_constants` |
| VARY | SM-D21 | `Vary: HX-Request` header presence | `test_used_machinery_view.py::test_vary_hx_request_header_present_on_dispatch` |
| STANJE-HIDDEN | SM-D26 IMP-6 | `<input type="hidden" name="stanje" value="used">` | `test_used_machinery_templates.py::test_filter_form_has_2_dropdowns_2_sliders_1_sort_and_stanje_hidden_input` |
| EMPTY-VERBATIM | SM-D? | „Trenutno nemamo polovne mehanizacije u ponudi" + „POGLEDAJ NOVE TRAKTORE" verbatim | `test_used_machinery_templates.py::test_empty_state_*` (3 testa) |
