---
story-id: "2.6"
story-key: 2-6-brand-listing-strana-sa-grid-extended-layout-om
artifact: interface-contract
created: 2026-05-30
author: TEA / Murat (RED phase)
purpose: Canonical contract for Brand Listing page — URL patterns, views, templates,
         partials, JS modules, CSS components, data-testid surface, factory expectations.
         Dev MUST satisfy every clause in GREEN phase.
---

# Interface Contract — Story 2.6 Brand Listing Strana

Story 2.6 uvodi **prvi views/urls/templates layer** u `apps/brands/` Django app + minimalan
placeholder stub u `apps/products/`. Modeli (Brand, Series, Product, ProductSpecification,
ProductTestimonial) postoje od Story 2.1/2.2 i NE menjaju se ovde. Ovaj ugovor enumerise
**fajl-sistem delta + Python surface + template + DOM/data-testid surface + CSS klase**
koje TEA RED-phase testovi verifikuju. Dev GREEN phase realizuje sve klauzule; bilo koje
odstupanje vraća story u `paused`.

---

## 1. File-system delta

### Fajlovi koji MORAJU postojati posle GREEN phase (19 NOVO + 4 EDIT)

| Path | Status | Vlasništvo |
|---|---|---|
| `apps/brands/views.py` | NOVO (Dev) | BrandDetailView CBV |
| `apps/brands/urls.py` | NOVO (Dev) | namespace `brands`, pattern `traktori/<slug:slug>/` |
| `apps/products/views.py` | NOVO (Dev) | `placeholder_view` FBV |
| `apps/products/urls.py` | NOVO (Dev) | namespace `products`, pattern `proizvod/<slug:slug>/` |
| `templates/products/_placeholder.html` | NOVO (Dev) | placeholder + noindex |
| `templates/brands/brand_detail.html` | NOVO (Dev) | glavni template |
| `templates/brands/brand_coming_soon.html` | NOVO (Dev) | minimal coming-soon |
| `templates/brands/partials/_hero_section.html` | NOVO (Dev) | hero overlay wrapper |
| `templates/brands/partials/_statistics_medallions.html` | NOVO (Dev) | 4-medallion grid |
| `templates/brands/partials/_testimonials_slider.html` | NOVO (Dev) | slider markup |
| `templates/brands/partials/_series_section.html` | NOVO (Dev) | iterator + branching |
| `templates/brands/partials/_series_grid.html` | NOVO (Dev) | 2-col grid kartice |
| `templates/brands/partials/_series_extended.html` | NOVO (Dev) | row + akordion |
| `templates/brands/partials/_catalog_cta.html` | NOVO (Dev) | CTA banner |
| `static/js/statistic-counter.js` | NOVO (Dev) | IIFE count-up + IO + prefers-reduced-motion |
| `static/js/testimonials-slider.js` | NOVO (Dev) | IIFE auto-advance + pause/play + keyboard + lightbox event |
| `static/css/components/brand-listing.css` | NOVO (Dev) | layout + coming-soon + placeholder selektori |
| `static/css/components/statistic-medallion.css` | NOVO (Dev) | medallion circle stilovi |
| `static/css/components/testimonials-slider.css` | NOVO (Dev) | slider stilovi |
| `config/urls.py` | EDIT (Dev) | include brands + products u i18n_patterns |
| `static/css/main.css` | EDIT (Dev) | +3 `@import url('./components/...');` linije |
| `templates/base.html` | EDIT (Dev) | +2 `<script defer>` tag-a posle lightbox-init.js |
| `_bmad-output/project-context.md` | VERIFY-ONLY (Dev) | Cross-boundary Exception bullet već prisutan |
| `apps/brands/tests/test_views_brand_detail.py` | NOVO (TEA) | AC1 + AC2 |
| `apps/brands/tests/test_templates_brand_listing.py` | NOVO (TEA) | AC3, AC4, AC5, AC6, AC7, AC8 |
| `apps/brands/tests/test_brand_coming_soon.py` | NOVO (TEA) | AC2.5 |
| `apps/products/tests/test_placeholder.py` | NOVO (TEA) | AC2.6 |
| `apps/brands/tests/factories.py` | NOVO (TEA) | BrandFactory, SeriesFactory |
| `apps/products/tests/factories.py` | NOVO (TEA) | ProductFactory, ProductSpecificationFactory, ProductTestimonialFactory |

### Fajlovi koji MORAJU OSTATI NETAKNUTI (regression guard)

- `apps/brands/models.py`, `apps/brands/admin.py`, `apps/brands/translation.py`,
  `apps/brands/migrations/`, `apps/brands/apps.py`
- `apps/products/models.py`, `apps/products/admin.py`, `apps/products/translation.py`,
  `apps/products/migrations/`
- `apps/core/`, `apps/media_pipeline/`
- `static/vendor/`, `static/css/tokens.css`
- `static/css/components/{header,footer,sticky-nav,lightbox,hero-overlay-card,
  repeating-element,pill-button,section-eyebrow,wave-divider}.css`
- `templates/partials/{header,footer,hero_overlay_card,repeating_element,pill_button,
  section_eyebrow,wave_divider,language_switcher,language_switcher_nav}.html`
- `pyproject.toml`, `config/settings/`

---

## 2. URL patterns

### `apps/brands/urls.py`

```python
from django.urls import path
from apps.brands.views import BrandDetailView

app_name = "brands"

urlpatterns = [
    path("traktori/<slug:slug>/", BrandDetailView.as_view(), name="detail"),
]
```

**Invarijante:**
- `app_name = "brands"` (namespace).
- URL name `detail` (matchuje `Brand.get_absolute_url()` iz Story 2.1).
- Kwarg ime `slug` (matchuje default `DetailView.slug_url_kwarg`).
- URL slug-segment `traktori` (hardcoded sr; multi-locale slug-ovi su Story 6.6 scope).

### `apps/products/urls.py`

```python
from django.urls import path
from apps.products import views

app_name = "products"

urlpatterns = [
    path("proizvod/<slug:slug>/", views.placeholder_view, name="detail"),
]
```

**Invarijante:**
- `app_name = "products"`.
- URL name `detail` (matchuje `Product.get_absolute_url()` iz Story 2.2).
- FBV ime: **`placeholder_view`** (Dev MOŽE koristiti drugu funkciju, ali test
  uvozi `from apps.products import urls` i reverse-uje URL name — ime view-a
  je interno; potpis je `(request, slug)`).

### Root URLconf `config/urls.py` wiring

Brands + products include MORAJU biti **unutar `i18n_patterns(...)` blok-a** i
**PRE** `apps.core.urls` (catch-all home):

```python
urlpatterns += i18n_patterns(
    path("admin/", admin.site.urls),
    path("", include("apps.brands.urls")),    # NOVO Story 2.6
    path("", include("apps.products.urls")),  # NOVO Story 2.6
    path("", include("apps.core.urls")),
    prefix_default_language=True,
)
```

Resulting URL-ovi (sr/hu/en locale prefiks):

- `/sr/traktori/<slug>/` → `brands:detail`
- `/hu/traktori/<slug>/` → `brands:detail`
- `/en/traktori/<slug>/` → `brands:detail`
- `/sr/proizvod/<slug>/` → `products:detail` (placeholder)
- `/hu/proizvod/<slug>/` → `products:detail`
- `/en/proizvod/<slug>/` → `products:detail`

---

## 3. Views

### `apps/brands/views.py` — `BrandDetailView`

**Klasa:** `BrandDetailView(DetailView)`

**Atributi:**
- `model = Brand`
- `context_object_name = "brand"`
- `slug_url_kwarg = "slug"` (Django default — može biti izostavljeno)
- `slug_field = "slug"` (Django default — može biti izostavljeno)

**Override `get_queryset(self)`:**
- Vraća Brand queryset sa `prefetch_related("series", queryset=series_qs)` chain-om
- `series_qs` = `Series.objects.order_by("display_order", "name").prefetch_related(Prefetch("products", queryset=published_products))`
- `published_products` = `Product.objects.filter(is_published=True).prefetch_related(Prefetch("specifications", queryset=specs_qs))`
- `specs_qs` = `ProductSpecification.objects.annotate(section_rank=section_order, section_label=section_label).order_by("section_rank", "order", "id")`
- **KRITIČNO (SM-D20):** `section_order` i `section_label` Case/When ekspresije MORAJU biti definisane UNUTAR `get_queryset()` per-request (lokalne varijable), NE na module-level. `gettext_lazy` proxy unutar `Value()` mora re-evaluati po request-u — module-level konstanta freeze-uje locale za prvi request.
- `section_order` mapping: motor=1, transmisija=2, hidraulika=3, ostalo=4, default=99 (`IntegerField`)
- `section_label` mapping: motor→_("Motor"), transmisija→_("Transmisija"), hidraulika→_("Hidraulika"), ostalo→_("Ostalo"), default→_("Ostalo") (`CharField`)

**Override `get_template_names(self)`:**
- Ako `self.object is not None` AND `self.object.is_coming_soon` → vraća `["brands/brand_coming_soon.html"]`
- Inače → vraća `["brands/brand_detail.html"]`
- (Implementacija MORA pozvati `getattr(self, "object", None)` defensive; vidi I11/SM-D19)

**Override `get(self, request, *args, **kwargs)` (per SM-D19):**
- Postavlja `self.object = self.get_object()`
- Poziva `context = self.get_context_data(object=self.object)`
- Vraća `self.render_to_response(context)`

**Override `get_context_data(self, **kwargs)`:**
- Ako `self.object.is_coming_soon` → early return super().get_context_data() bez testimonials-a
- Inače dodaje `ctx["testimonials"] = ProductTestimonial.objects.filter(product__brand=self.object, product__is_published=True).select_related("product").order_by("order", "-created_at")[:10]`

**Context contract (renderuje template):**
- `brand` (Brand instance, sa prefetched `series.all`)
- `testimonials` (QuerySet ProductTestimonial; max 10; **SAMO ako NOT is_coming_soon**)
- **NEMA** ključeva `series_list`, `products`, `specifications` (template pristupa kroz `brand.series.all`).

**Query count contract:** **TAČNO 5 SQL upita** za pun render strane (NOT-coming-soon brand sa series + products + specs + testimonials).

### `apps/products/views.py` — `placeholder_view`

**Potpis:** `def placeholder_view(request, slug) -> HttpResponse`

**Ponašanje:**
- HTTP 200
- Renderuje `templates/products/_placeholder.html`
- **NEMA DB query za `Product` lookup** — slug se prima kao argument samo da URL pattern resolvuje; template ne pristupa nikom Product instance-u
- (Dev opciono može proslediti `slug` kroz context za debug; nije testirano)

---

## 4. Templates

### `templates/brands/brand_detail.html` (glavni)

- `{% extends "base.html" %}`
- `{% load i18n static media_tags %}`
- `{% block title %}{{ brand.name }} | {% translate "Ćorić Agrar" %}{% endblock %}`
- `{% block meta_description %}{{ brand.slogan|default:brand.description|truncatewords:25 }}{% endblock %}`
- `{% block content %}` sadrži sekcije u TAČNOM redosledu (verifikuje test AC3):
  1. Hero `<section id="brand-hero" aria-labelledby="brand-hero-title">` → include `brands/partials/_hero_section.html`
  2. Statistike `<section id="brand-statistics" aria-labelledby="brand-statistics-title" class="coric-brand-statistics">` — render SAMO kada `brand.statistics` nije prazno; include `brands/partials/_statistics_medallions.html`
  3. Testimonijali `<section id="brand-testimonials" aria-labelledby="brand-testimonials-title" class="coric-testimonials">` — render SAMO kada `testimonials` nije prazno; include `partials/_testimonials_slider.html` with `testimonials=testimonials slider_id="brand-testimonials-title"` kwargs. **Historical note:** Refactored in Story 2.7 SM-D23/D27 — shared partial moved to `templates/partials/`, parametrized with optional `slider_id` kwarg (default `"testimonials-title"`); brand_detail.html passes explicit kwarg za backwards-compat aria-labelledby reference.
  4. Serije `<section id="brand-series" aria-labelledby="brand-series-title" class="coric-brand-series">` — uvek render; include `brands/partials/_series_section.html`
  5. Catalog CTA `<section id="brand-catalog-cta" aria-labelledby="brand-catalog-cta-title" class="coric-catalog-cta-banner">` — render SAMO kada `brand.catalog_pdf` postoji; include `brands/partials/_catalog_cta.html`
- Korenski wrapper element MORA imati `data-testid="brand-detail-page"`
- NEMA inline `style="..."`
- Svi string-ovi kroz `{% translate %}` / `{% blocktranslate %}`

### `templates/brands/brand_coming_soon.html` (AC2.5)

- `{% extends "base.html" %}` + `{% load i18n static media_tags %}`
- Wrapper: `<div class="coric-brand-coming-soon container py-5" data-testid="brand-coming-soon-page">` — **NE drugi `<main>` element** (HTML5 zabranjuje nested `<main>`; base.html već renderuje `<main id="main-content">` i `{% block content %}` živi unutar njega). Reuse postojećeg `<main>` landmark-a; wrapper je `<div>` (ili `<section aria-labelledby="brand-coming-soon-title">` ako se semantička sekcija preferira).
- Sadrži:
  - `{% if brand.logo %}{% responsive_picture brand.logo alt=brand.name sizes="(max-width: 768px) 80vw, 320px" loading="eager" format='PNG' %}{% endif %}` — **KRITIČNO `format='PNG'` (I-iter2-7 + Story 2.3 MP-D5)**
  - JEDNU `<h1 id="brand-coming-soon-title">{{ brand.name }}</h1>`
  - `<span class="coric-pill-badge coric-pill-badge--coming-soon" role="status">{% translate "Uskoro" %}</span>`
  - `<a href="{% url 'core:home' %}" class="coric-button coric-button--primary">{% translate "Nazad na Home" %}</a>`
- NEMA statistike, NEMA serija, NEMA testimonijala
- Svi string-ovi kroz `{% translate %}` / `{% blocktranslate %}`

### `templates/products/_placeholder.html` (AC2.6)

- `{% extends "base.html" %}` + `{% load i18n %}`
- `{% block title %}{% translate "Stranica još nije dostupna" %} | {% translate "Ćorić Agrar" %}{% endblock %}`
- `{% block extra_head %}<meta name="robots" content="noindex, nofollow">{% endblock %}` — **KRITIČNO SEO guard pre Story 2.7**
- `{% block content %}` wrapper: `<div class="coric-product-placeholder" data-testid="product-placeholder-page">` — **NE drugi `<main>` element** (HTML5 zabranjuje nested `<main>`; base.html već renderuje `<main id="main-content">` wrapper i `{% block content %}` živi unutar njega). Reuse postojećeg `<main>` landmark-a iz base.html — placeholder wrapper je `<div>`.
- Sadrži:
  - TAČNO 1 `<h1 class="coric-product-placeholder__title">{% translate "Stranica još nije dostupna" %}</h1>`
  - `<p class="coric-product-placeholder__message">{% translate "..." %}</p>`
  - `<a href="{% url 'core:home' %}" class="coric-button coric-button--primary">{% translate "Nazad na Home" %}</a>`

### Partials u `templates/brands/partials/`

Svi partials uvode markup spec-ove iz story AC3-AC7. Ključne data-testid + a11y invarijante:

- `_hero_section.html` — wrapper sa `data-testid="brand-hero"`, include-uje `templates/partials/hero_overlay_card.html` sa brand.name + brand.logo + variant mapping
- `_statistics_medallions.html` — `<div class="coric-statistic-medallions" data-statistic-counters>` sa `{% for stat in brand.statistics|slice:":4" %}`; svaki medallion `data-testid="statistic-medallion-{{ forloop.counter }}"`; **NEMA `<i class="bi ...">`** elemenata (SM-D18 C7 fix); svaka vrednost `<span class="coric-statistic-medallion__value" data-count-target="{{ stat.value }}" data-count-duration="1500">0</span>` + label `<span class="coric-statistic-medallion__label">{{ stat.label }}</span>`
- `_testimonials_slider.html` — `<div class="coric-testimonials-slider" data-testimonials-slider data-autoadvance-ms="6000" role="region" aria-roledescription="..." aria-label="..." data-testid="testimonials-slider">`; svaki slide `<article class="coric-testimonials-slider__slide" role="group" data-testid="testimonial-{{ forloop.counter }}">`; kontrole: prev (`data-slider-prev` + `data-testid="prev-testimonial"`), pause (`data-slider-pause` + `aria-pressed="false"` + `data-testid="pause-testimonial"`), next (`data-slider-next` + `data-testid="next-testimonial"`); live region `<span class="visually-hidden" aria-live="polite" data-slider-live></span>`
- `_series_section.html` — iterira `brand.series.all`; per-series `<article class="coric-series-block" aria-labelledby="series-{{ series.slug }}-title" data-testid="series-section-{{ series.slug }}">`; branching `{% if series.layout_mode == "grid" %}` → grid partial, else extended partial; empty state poruka `{% translate "Modeli ovog brenda su u pripremi." %}`
- `_series_grid.html` — 2-col grid; svaka kartica `<a class="coric-product-card" href="{{ product.get_absolute_url }}" aria-label="{{ product.name }}" data-testid="product-card-{{ product.slug }}">`; vidljivi "OPŠIRNIJE" je `<span class="coric-button coric-button--primary coric-product-card__cta" aria-hidden="true">{% translate "OPŠIRNIJE" %}</span>` (NE `<a>`/`<button>`); slika kroz `{% responsive_picture product.main_image alt=product.name sizes="..." loading="lazy" %}`; empty state ako `series.products.all` prazan
- `_series_extended.html` — per-product `<article class="coric-product-row" data-testid="product-row-{{ product.slug }}">`; `{% regroup product.specifications.all by section_label as spec_sections %}`; per-section `<details class="coric-product-row__accordion" {% if forloop.first %}open{% endif %} data-testid="spec-section-{{ section_group.grouper|slugify }}">`; `<summary>` sadrži `{{ section_group.grouper }}`; `<table>` sa `<th scope="row">{{ spec.key }}</th><td>{{ spec.value }}</td>`; standalone `<a class="coric-button coric-button--primary">` ka product.get_absolute_url
- `_catalog_cta.html` — include `partials/wave_divider.html with position="top"`; sadrži Section Eyebrow + heading + description + **direktan `<a>`** (NE pill_button.html) sa atributima: `href="{{ brand.catalog_pdf.url }}" target="_blank" rel="noopener noreferrer" download class="coric-button coric-button--primary" data-testid="brand-catalog-download"`; tekst `{% translate "Preuzmi katalog" %}`

---

## 5. JS modules

### `static/js/statistic-counter.js`

- IIFE wrap: `(function () { 'use strict'; ... })()`
- Selector entry: `document.querySelectorAll('[data-statistic-counters]')`
- Defensive bail ako nema elemenata
- Iterira children `[data-count-target]`, čita `data-count-target` i `data-count-duration`
- IntersectionObserver triggering pri scroll-into-view (threshold 0.3); fallback ako `IntersectionObserver` ne postoji → trigger odmah
- Animira preko `requestAnimationFrame` (ease-out cubic), `Math.round(target * eased)`
- **`prefers-reduced-motion: reduce`** check kroz `window.matchMedia` → instant set `el.textContent = target.toString()`
- NEMA `import`/`export`, NEMA jQuery

### `static/js/testimonials-slider.js`

- IIFE wrap: `(function () { 'use strict'; ... })()`
- Selector entry: `document.querySelectorAll('[data-testimonials-slider]')`
- Defensive bail ako nema elemenata; **per-slider** ako manje od 2 slide-a → sakrij `.coric-testimonials-slider__controls` (`display:none`)
- Auto-advance kroz `setInterval` (parsed `data-autoadvance-ms`, default 6000ms)
- **Manual interakcija (prev/next/keyboard) ZAUSTAVLJA auto-advance i NE re-startuje** — auto se vraća tek na `focusout` / `mouseleave` (I5 fix)
- Pause/play button toggle: `manuallyPaused = !manuallyPaused`; `aria-pressed` toggle; tekst toggle `⏸ ↔ ▶`
- Keyboard nav: ArrowLeft → prev, ArrowRight → next (samo kad focus unutar slider-a)
- Focus pause: `focusin` → stopAuto; `focusout` → startAuto
- Hover pause: `mouseenter` → stopAuto; `mouseleave` → startAuto
- Lightbox integracija: `window.addEventListener('coric:lightbox-open', stopAuto)` + `window.addEventListener('coric:lightbox-close', startAuto)` (Story 2.5 kontrakt)
- **`prefers-reduced-motion: reduce`** → NEMA auto-advance (samo manual)
- aria-live live region update: `(idx + 1) + ' / ' + slides.length` u `[data-slider-live]` na svaku promenu
- NEMA `import`/`export`, NEMA jQuery, NEMA Bootstrap Carousel

---

## 6. CSS

### `static/css/components/brand-listing.css`

Mora sadržati BEM klase (sve sa `coric-` prefix-om, sve vrednosti kroz `var(--token)`):

- `.coric-brand-detail` (root wrapper)
- `.coric-brand-series`, `.coric-series-block`
- `.coric-product-card`, `.coric-product-card__image`, `.coric-product-card__body`, `.coric-product-card__title`, `.coric-product-card__cta`, `.coric-product-card__spec`
- `.coric-product-row`, `.coric-product-row__image`, `.coric-product-row__specs`, `.coric-product-row__title`, `.coric-product-row__desc`, `.coric-product-row__accordion`, `.coric-product-row__accordion-icon`, `.coric-product-row__specs-table`
- `.coric-empty-state`
- `.coric-catalog-cta-banner`
- **Coming-soon (AC2.5):** `.coric-brand-coming-soon`, `.coric-brand-coming-soon__logo`, `.coric-brand-coming-soon__title`, `.coric-brand-coming-soon__message`
- **Pill badge:** `.coric-pill-badge`, `.coric-pill-badge--coming-soon`
- **Product placeholder (SM-D21):** `.coric-product-placeholder`, `.coric-product-placeholder__title`, `.coric-product-placeholder__message`
- `@media (prefers-reduced-motion: reduce)` blok koji uklanja transform/transition

### `static/css/components/statistic-medallion.css`

- `.coric-statistic-medallions` (4-col desktop CSS Grid)
- `.coric-statistic-medallion`
- `.coric-statistic-medallion__value`
- `.coric-statistic-medallion__label`
- `@media (prefers-reduced-motion: reduce)` defensive blok

### `static/css/components/testimonials-slider.css`

- `.coric-testimonials-slider`
- `.coric-testimonials-slider__viewport`
- `.coric-testimonials-slider__slide` (default `opacity:0`; `.is-active` → `opacity:1`)
- `.coric-testimonials-slider__quote`
- `.coric-testimonials-slider__attribution`
- `.coric-testimonials-slider__controls`
- `.coric-testimonials-slider__nav`, `.coric-testimonials-slider__nav--prev`, `.coric-testimonials-slider__nav--next`
- `.coric-testimonials-slider__pause`
- `@media (prefers-reduced-motion: reduce)` → transition: none

### `static/css/main.css` (EDIT)

Dodaje TAČNO 3 nove linije na kraj postojećih `@import` linija (mirror Story 1.7+1.8+2.5 sintaksu — `url(...)` wrap + leading `./`):

```css
@import url('./components/brand-listing.css');
@import url('./components/statistic-medallion.css');
@import url('./components/testimonials-slider.css');
```

### `templates/base.html` (EDIT)

Dodaje TAČNO 2 nova `<script defer>` tag-a posle `lightbox-init.js` i pre Django komentara `{# Per-page scripts POSLE site-wide ... #}`:

```html
<script src="{% static 'js/statistic-counter.js' %}" defer></script>
<script src="{% static 'js/testimonials-slider.js' %}" defer></script>
```

---

## 7. Anti-CDN guard

Sva nova fajlovi (CSS + JS + templates) MORAJU biti audited za odsustvo eksternih CDN URL-ova:
- `cdn.jsdelivr.net` — 0 matches
- `unpkg.com` — 0 matches
- `cdnjs.cloudflare.com` — 0 matches

Sva referenca na vendor stack-ove mora ići kroz `{% static 'vendor/...' %}` (Story 1.6 pattern).

---

## 8. HTML data-testid surface

| data-testid | Lokacija | Test koji ga koristi |
|---|---|---|
| `brand-detail-page` | `templates/brands/brand_detail.html` root wrapper | test_views, test_templates |
| `brand-coming-soon-page` | `templates/brands/brand_coming_soon.html` `<main>` | test_brand_coming_soon |
| `product-placeholder-page` | `templates/products/_placeholder.html` `<main>` | test_placeholder |
| `brand-hero` | `_hero_section.html` wrapper | test_templates AC3 |
| `statistic-medallion-{N}` (1..4) | `_statistics_medallions.html` per item | test_templates AC6 |
| `testimonials-slider` | `_testimonials_slider.html` root | test_templates AC7 |
| `testimonial-{N}` (1..) | `_testimonials_slider.html` per slide | test_templates AC7 |
| `prev-testimonial`, `pause-testimonial`, `next-testimonial` | `_testimonials_slider.html` controls | test_templates AC7 |
| `series-section-{slug}` | `_series_section.html` per series | test_templates AC4/AC5 |
| `product-card-{slug}` | `_series_grid.html` per card | test_templates AC4 |
| `product-row-{slug}` | `_series_extended.html` per row | test_templates AC5 |
| `spec-section-{slugified-label}` | `_series_extended.html` per `<details>` | test_templates AC5 |
| `brand-catalog-download` | `_catalog_cta.html` `<a>` | test_templates AC3 |

---

## 9. Test factory expectations

### `apps/brands/tests/factories.py` (NEW)

Zavisno od projektne konvencije (no `factory_boy` dependency u `pyproject.toml`),
factories su **plain Python helper klase** sa `create(**overrides)` classmethod-om
(mirror Factory Boy public surface bez vendor lock-a). Dev koji menja modele MORA
održavati ove factory-je u sync sa modelima.

- `BrandFactory.create(**overrides) -> Brand` — defaults: name="Test Brand", brand_color="", statistics=[], is_coming_soon=False
- `BrandFactory.create_coming_soon(**overrides) -> Brand` — convenience za `is_coming_soon=True`
- `BrandFactory.create_with_statistics(stats=None, **overrides) -> Brand` — sample 4-medallion statistics list
- `SeriesFactory.create(brand=None, **overrides) -> Series` — defaults: name="Test Series", layout_mode="grid", display_order=0
- `SeriesFactory.create_grid(brand=None, **overrides) -> Series`
- `SeriesFactory.create_extended(brand=None, **overrides) -> Series`

### `apps/products/tests/factories.py` (NEW)

- `ProductFactory.create(brand=None, series=None, **overrides) -> Product` — defaults: name="Test Product", is_published=True, condition="new", status="draft"
- `ProductFactory.create_published(...)`, `ProductFactory.create_unpublished(...)`
- `ProductSpecificationFactory.create(product=None, section="motor", **overrides) -> ProductSpecification` — defaults: key="Snaga", value="100 KS", order=0
- `ProductTestimonialFactory.create(product=None, **overrides) -> ProductTestimonial` — defaults: quote="Odlični traktor.", author_name="Marko Petrović", location="Novi Sad", order=0

---

## 10. Locale + i18n contract

- Aktivni `LANGUAGE_CODE` per request prolazi kroz `i18n_patterns(...)` segment iz URL-a (`/sr/`, `/hu/`, `/en/`).
- `BrandDetailView.get_queryset()` MORA per-request konstruisati `section_label` Case/When (SM-D20).
- Svi user-facing string-ovi u template-ima MORAJU biti kroz `{% translate %}` ili `{% blocktranslate %}`; testovi za AC8 audit-uju odsustvo hardcoded srpskih reči u render-ovanim sekcijama.
- **hu translation gap (PREREQ za AC5 hu test):** `locale/hu/LC_MESSAGES/django.po` trenutno (live verifikovano 2026-05-30) sadrži `msgstr ""` za "Motor", "Transmisija", "Hidraulika", "Ostalo" — TEA test koji asertuje hu prevode je **`xfail` sa razlogom dok Dev ne popuni prevode**. Bez prevoda, Django fallback vraća msgid string sam (sr varijantu); Case/When pattern je verifikovan kroz sr render (default locale).

---

## 11. AC pokrivenost — test mapping

| AC | Test fajl | Test count |
|---|---|---|
| AC1 URL routing | `apps/brands/tests/test_views_brand_detail.py` | 5 |
| AC2 view + queries | `apps/brands/tests/test_views_brand_detail.py` | 4 |
| AC2.5 coming-soon | `apps/brands/tests/test_brand_coming_soon.py` | 5 (1 nested-main guard dodat u iter 2) |
| AC2.6 placeholder | `apps/products/tests/test_placeholder.py` | 4 |
| AC3 page structure | `apps/brands/tests/test_templates_brand_listing.py` | 2 |
| AC4 grid | `apps/brands/tests/test_templates_brand_listing.py` | 3 |
| AC5 extended | `apps/brands/tests/test_templates_brand_listing.py` | 4 (1 xfail-hu) |
| AC6 medallions | `apps/brands/tests/test_templates_brand_listing.py` | 3 |
| AC7 testimonials | `apps/brands/tests/test_templates_brand_listing.py` | 4 |
| AC8 i18n + a11y | `apps/brands/tests/test_templates_brand_listing.py` | 4 |

**Total: 38 testova** (1 markiran kao `xfail` za hu prevode dok Dev/Mihas ne popuni `locale/hu/LC_MESSAGES/django.po`). Iter 2 dodaje paralelan nested-main guard za coming-soon template (test_coming_soon_no_nested_main_element) — mirror placeholder testa, prevenira regression gde Dev iz inertia po story prose-u doda dodatni `<main role="main">` wrapper umesto `<div>` per contract § 4.

AC9 (manuelni Lighthouse + smoke check) NIJE automatizovan — Dev izvršava ručno u GREEN phase per AC9 § Lighthouse JSON artifact preservation.

---

## 12. Dev pre-flight checklist (GREEN phase)

Pre nego što Dev počne implementaciju:

1. Verifikovati `templates/base.html` već sadrži `{% block extra_head %}{% endblock %}` između `<title>` i `</head>` — ✅ verifikovano live 2026-05-30 (linija 16). Ako se regression desi, dodati ga PRE Subtask 1.5.
2. Verifikovati `_bmad-output/project-context.md` § Cross-boundary import sadrži "Exception (Story 2.6+)" bullet — Subtask 1.7 (VERIFY-ONLY).
3. Verifikovati `apps/core/urls.py` koristi `app_name = "core"` + URL name `home` → `{% url 'core:home' %}` rezolvuje (live verifikovano 2026-05-30).
4. Verifikovati `static/css/tokens.css` definiše tokene: `--color-brand-green-800`, `--color-neutral-gray-700`, `--color-accent-gold-500`, `--spacing-scale-{1..8}`, `--typography-scale-{h1,h2,body,small,display-1}`, `--typography-weight-bold`, `--typography-tracking-wide`, `--rounded-pill`. Ako fali, dokumentovati u Completion Notes (ne uvoditi nove tokene u 2.6).

---

## 13. Out-of-scope (eksplicitno)

- Real-browser keyboard + IntersectionObserver tests (Playwright `page.emulateMedia(reducedMotion)`) — **Story 9.8 scope**
- WCAG axe-core static analysis — **Story 9.9 scope**
- Multi-locale URL slug-ovi (`/hu/traktorok/...`) — **Story 6.6 scope**
- Bootstrap Icons font wiring + statistic icon render — **Story 9-10 scope** (SM-D18)
- Pravi `ProductDetailView` — **Story 2.7 scope** (placeholder je C8 fix u 2.6)
- Brand admin layout polish + statistics editor — **Story 8.4 scope**
- HTMX filtering + URL state sync — **Story 2.8 scope** (SM-D1)
- Lighthouse Performance ≥ 90 (WebP/AVIF pipeline) — **Story 9.10 scope**
