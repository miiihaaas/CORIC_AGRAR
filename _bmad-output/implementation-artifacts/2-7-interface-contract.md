---
story-id: "2.7"
story-key: 2-7-product-detail-strana
artifact: interface-contract
created: 2026-05-30
author: TEA / Murat (RED phase)
purpose: Canonical contract for Product Detail page — URL patterns, view, templates,
         partials, factory expectations, data-testid surface, CSS components.
         REPLACES Story 2.6 placeholder_view stub at the same URL. Dev MUST satisfy
         every clause in GREEN phase.
---

# Interface Contract — Story 2.7 Product Detail Strana

Story 2.7 ZAMENJUJE Story 2.6 placeholder stub (`placeholder_view` FBV + `_placeholder.html`
template) sa pravim `ProductDetailView` CBV + 1 main template + 7 partials. URL pattern
`/<lang>/proizvod/<slug>/` (registrovan u Story 2.6) OSTAJE NETAKNUT — menja se SAMO views
referenca. Dodatno: Story 2.6 testimonials slider partial se PREMEŠTA u shared lokaciju
sa parametrizovanim `slider_id` kwarg-om (per SM-D23 + SM-D27 backwards compat).

Ovaj ugovor enumerise fajl-sistem deltu + Python surface + template + DOM/data-testid
surface + CSS klase koje TEA RED-phase testovi verifikuju. Dev GREEN-phase realizuje sve
klauzule; bilo koje odstupanje vraća story u `paused`.

---

## 1. File-system delta

### Fajlovi koji MORAJU postojati posle GREEN phase (12-13 NOVO + 5-7 EDIT + 3 DELETE)

| Path | Status | Vlasništvo |
|---|---|---|
| `apps/products/views.py` | EDIT (REPLACE) | `placeholder_view` FBV BRIŠE; `ProductDetailView` CBV NOVO |
| `apps/products/urls.py` | EDIT (1-line) | `views.placeholder_view` → `views.ProductDetailView.as_view()` |
| `templates/products/_placeholder.html` | DELETE | Placeholder template iz Story 2.6 C8 fix |
| `templates/products/product_detail.html` | NOVO (Dev) | Glavni template — extends base.html |
| `templates/products/partials/_hero_section.html` | NOVO (Dev) | Hero wrapper — delegated u `hero_overlay_card.html` |
| `templates/products/partials/_description.html` | NOVO (Dev) | Opis sekcija sa `linebreaks` filter |
| `templates/products/partials/_gallery_carousel.html` | NOVO (Dev) | Galerija carousel sa GLightbox auto-pickup |
| `templates/products/partials/_specs_accordion.html` | NOVO (Dev) | `<details>/<summary>` akordion sa regroup |
| `templates/products/partials/_brochure_card.html` | NOVO (Dev) | Brošure card sa cover_thumbnail + size + PDF download |
| `templates/products/partials/_similar_products.html` | NOVO (Dev) | Slični modeli sekcija — reuse `coric-product-card` BEM |
| `templates/products/partials/_variants_selector.html` | NOVO (Dev) | Variants kartice sa GLightbox zoom (no state change) |
| `templates/partials/_testimonials_slider.html` | MOVE (NOVO destination) | Shared partial sa `slider_id` kwarg (per SM-D23+D27) |
| `templates/brands/partials/_testimonials_slider.html` | DELETE (MOVE source) | Premešten u shared `templates/partials/` |
| `templates/brands/brand_detail.html` | EDIT (1-line) | Line 22: novi include path + `slider_id="brand-testimonials-title"` kwarg per SM-D27 |
| `static/css/components/product-detail.css` | NOVO (Dev) | Layout sekcija, accordion summary/details, brochure card, similar grid; MIGRATE placeholder klase iz `brand-listing.css` |
| `static/css/components/product-gallery.css` | NOVO (Dev) | Gallery carousel (CSS Grid desktop / scroll-snap mobile) |
| `static/css/components/product-variants.css` | NOVO (Dev) | Variant kartice grid, hover, focus-visible outline |
| `static/css/main.css` | EDIT | +3 `@import url('./components/...')` linije |
| `static/css/components/brand-listing.css` | EDIT (CLEANUP) | UKLONI 3 `coric-product-placeholder*` selektora per SM-D21 |
| `_bmad-output/implementation-artifacts/2-6-interface-contract.md` | EDIT (Dev, Subtask 9.0e) | L207 — include path + slider_id kwarg note; historical footnote |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | EDIT (Dev, Subtask 9.0d) | `last_updated` napomena za cross-story cascade tracking |
| `apps/products/tests/test_placeholder.py` | DELETE | 4 testova orfani posle FBV+template DELETE (per SM-D16, C2) |
| `apps/products/tests/test_views_product_detail.py` | NOVO (TEA) | AC1+AC2 view + queries + context |
| `apps/products/tests/test_templates_product_detail.py` | NOVO (TEA) | AC3-AC8 + AC5 hu locale |
| `apps/products/tests/test_url_routing.py` | NOVO (TEA) | AC1 URL routing 5 tests |
| `apps/products/tests/test_placeholder_deleted.py` | NOVO (TEA) | Subtask 12.5 regression guard za DELETE-ove |
| `apps/products/tests/test_static_assets.py` | NOVO (TEA) | Subtask 12.6 cross-cutting CSS + i18n + a11y audit |
| `apps/products/tests/test_lighthouse_manual.py` | NOVO (TEA) | AC9 placeholder xfail (manual smoke) |
| `apps/products/tests/factories.py` | EDIT (EXTEND) | +ProductImageFactory, +ProductBrochureFactory, +ProductVariantFactory, +ProductSimilarFactory |

### Fajlovi koji MORAJU OSTATI NETAKNUTI (regression guard)

- `apps/products/models.py`, `apps/products/admin.py`, `apps/products/translation.py`,
  `apps/products/migrations/`, `apps/products/apps.py`
- `apps/brands/views.py`, `apps/brands/urls.py`, `apps/brands/models.py`,
  `apps/brands/admin.py`, `apps/brands/translation.py`, `apps/brands/migrations/`
- `apps/brands/tests/test_templates_brand_listing.py` (per SM-D27 backwards compat — brand
  prosleđuje explicit `slider_id="brand-testimonials-title"` kwarg, assertion ostaje validna)
- `apps/core/`, `apps/media_pipeline/`
- `config/urls.py` (pattern + namespace + URL name `detail` registrovani u Story 2.6)
- `_bmad-output/project-context.md` (NEMA cross-boundary izuzetka u 2.7 — products → brands je natural direction)
- `static/vendor/`, `static/css/tokens.css`
- `static/css/components/{header,footer,sticky-nav,lightbox,hero-overlay-card,
  repeating-element,pill-button,section-eyebrow,wave-divider,statistic-medallion,
  testimonials-slider}.css`
- `templates/partials/{header,footer,hero_overlay_card,repeating_element,pill_button,
  section_eyebrow,wave_divider,language_switcher,language_switcher_nav}.html`
- `templates/brands/brand_coming_soon.html`, `templates/brands/partials/*` (ostali, except
  `_testimonials_slider.html` koji je MOVED)
- `pyproject.toml`, `config/settings/`

---

## 2. URL patterns

### `apps/products/urls.py`

```python
from django.urls import path

from apps.products import views

app_name = "products"

urlpatterns = [
    path("proizvod/<slug:slug>/", views.ProductDetailView.as_view(), name="detail"),
]
```

**Invarijante:**
- `app_name = "products"` (namespace, NETAKNUT od Story 2.6).
- URL name `detail` (matchuje `Product.get_absolute_url()` iz Story 2.2 — `reverse("products:detail", kwargs={"slug": self.slug})` linija 270).
- Kwarg ime `slug` (matchuje default `DetailView.slug_url_kwarg`).
- URL path string `proizvod/<slug:slug>/` (NETAKNUT od Story 2.6; multi-locale slug-ovi su Story 6.6 scope).
- DIFF od Story 2.6: `views.placeholder_view` → `views.ProductDetailView.as_view()` (1-line edit).

### Root URLconf `config/urls.py` wiring

NETAKNUT od Story 2.6:

```python
urlpatterns += i18n_patterns(
    path("admin/", admin.site.urls),
    path("", include("apps.brands.urls")),
    path("", include("apps.products.urls")),
    path("", include("apps.core.urls")),
    prefix_default_language=True,
)
```

Resulting URL-ovi (sr/hu/en locale prefiks):

- `/sr/proizvod/<slug>/` → `products:detail` (ProductDetailView u Story 2.7; ranije placeholder)
- `/hu/proizvod/<slug>/` → `products:detail`
- `/en/proizvod/<slug>/` → `products:detail`

---

## 3. Views

### `apps/products/views.py` — `ProductDetailView`

**Klasa:** `ProductDetailView(DetailView)`

**Atributi:**
- `model = Product`
- `context_object_name = "product"`
- `template_name = "products/product_detail.html"`
- `slug_url_kwarg = "slug"` (Django default — može biti izostavljeno)
- `slug_field = "slug"` (Django default — može biti izostavljeno)

**Override `get_queryset(self)`:**
- Vraća `Product.objects.filter(is_published=True).select_related("brand", "series", "subcategory").prefetch_related(...)`
- Prefetch chain (5 prefetches):
  - `Prefetch("images", queryset=ProductImage.objects.order_by("order", "id"))`
  - `Prefetch("variants", queryset=ProductVariant.objects.order_by("order", "id"))`
  - `Prefetch("specifications", queryset=specs_qs)` gde `specs_qs` = `ProductSpecification.objects.annotate(section_rank=section_order, section_label=section_label).order_by("section_rank", "order", "id")`
  - `Prefetch("brochures", queryset=ProductBrochure.objects.order_by("id"))` (NAPOMENA: Story spec naznačuje `[:5]` slice ali Django Prefetch NE PODRŽAVA slice queryset; cap se primenjuje u `get_context_data` `brochures_list` pre-computation per SM-D24)
  - `Prefetch("testimonials", queryset=ProductTestimonial.objects.order_by("order", "-created_at"))`
- **KRITIČNO (SM-D14/D20 reuse iz Story 2.6):** `section_order` i `section_label` Case/When ekspresije MORAJU biti definisane UNUTAR `get_queryset()` per-request (lokalne varijable), NE na module-level. `gettext_lazy` proxy unutar `Value()` mora re-evaluati po request-u — module-level konstanta freeze-uje locale za prvi request. Koristi `Value(str(_("Motor")))` (eager coerce gettext_lazy → string AT REQUEST TIME) — `psycopg.ProgrammingError: cannot adapt type '__proxy__'` ako se izostavi `str(...)`.
- `section_order` mapping: motor=1, transmisija=2, hidraulika=3, ostalo=4, default=99 (`IntegerField`)
- `section_label` mapping: motor→str(_("Motor")), transmisija→str(_("Transmisija")), hidraulika→str(_("Hidraulika")), ostalo→str(_("Ostalo")), default→str(_("Ostalo")) (`CharField`)

**NEMA override:**
- `get_template_names()` — Story 2.7 NE koristi (products nema coming-soon ekvivalent; `is_published=False` vodi 404 per SM-D2).
- `get()` — Story 2.7 NE koristi (DetailView default je dovoljan; nema branching kao u Brand coming-soon).

**Override `get_context_data(self, **kwargs)`:**

Konstanta:
```python
_SIMILAR_PRODUCTS_LIMIT = 4
```

Dodaje 3 ključa u context:
1. **`similar_products`** (lista do 4 Product instance-a) — FR-20 hybrid:
   - **Manual override path:** `ProductSimilar.objects.filter(product=self.object, related_product__is_published=True).select_related("related_product__brand").order_by("order", "id")[:_SIMILAR_PRODUCTS_LIMIT]` — SQL-level `is_published=True` filter per SM-D19 (NE Python post-filter).
   - **Auto fallback path:** ako manual_list je prazna, `Product.objects.filter(brand=self.object.brand, is_published=True).exclude(pk=self.object.pk).select_related("brand").order_by("-created_at")[:_SIMILAR_PRODUCTS_LIMIT]`. (NAPOMENA: Story SM-D3 i AC2 source spominju i `.filter(series=...)` za uže matchovanje ako `series_id` postoji; oba pattern-a su acceptable — test ne forsira specifičan filter beyond `brand` match + exclude self + is_published.)
   - **Empty state:** ako ni manual ni auto ne daju rezultate, `similar_products = []`; template `{% if similar_products %}` skipuje sekciju.
2. **`similar_source`** (string: `"manual"` / `"auto"` / `"none"`) — debug/analytics flag, nije u UI.
3. **`brochures_list`** (lista do 5 dict entries `{"brochure": ProductBrochure, "size_bytes": int}`) — view-pre-computed defensive size handling per SM-D26:
   - Loop kroz `self.object.brochures.all()[:5]` (cap 5 per SM-D24).
   - Per-entry try/except oko `b.pdf_file.size` koji catches `(FileNotFoundError, OSError, ValueError, SuspiciousFileOperation)` per SM-D26/I8+I-iter2-4 broadened scope; fallback `size_bytes = 0` → renderuje "0 bytes".
   - Template renderuje brošure SAMO kroz `brochures_list` (NE `product.brochures.all`).

**Context contract (renderuje template):**
- `product` (Product instance, sa prefetched `images`, `variants`, `specifications`, `brochures`, `testimonials`)
- `similar_products` (lista, max 4; može biti prazna)
- `similar_source` (string `"manual"` / `"auto"` / `"none"`)
- `brochures_list` (lista dict entries, max 5)
- **NEMA** odvojenih ključeva `gallery_images`, `variants`, `specifications`, `testimonials` (template pristupa kroz `product.<relation>.all` koje su cached kroz Prefetch).

**Query count contract (SM-D21/D28 — empirical pre-verify u Subtask 1.5(d)):**

**EMPIRIJSKI VERIFIKOVANO (2026-05-30, TEA RED-phase Subtask 1.5(d) probe):**
- **7 SQL upita** za pun render strane kada **manual ProductSimilar entry postoji** (manual path — FR-20 admin override case)
- **8 SQL upita** kada manual je prazan i auto fallback fire-uje (oba se exec-uju)

Story enumeracija u AC1 dokumentuje "TAČNO 7" pretpostavljajući manual path; u praksi obe putanje se exec-uju kad manual returns empty (manual SELECT vraća 0 rows, ali query se ipak izvršio = +1 query). Stoga:

- **Test `test_assert_num_queries_exactly_7` MORA biti construct-ovan sa `ProductSimilar` fixture entry-jem da hit-uje manual path** — to je AC1 explicit canonical case.
- **NIJEDAN auto-fallback test ne sme koristiti `assertNumQueries(7)`** — auto path je 8 queries.

Enumeracija (manual path, 7 queries):
1. Product DetailView get_object (sa select_related `brand`+`series`+`subcategory`) — 1 JOIN-ed SELECT
2. Prefetch ProductImage (ordered)
3. Prefetch ProductVariant (ordered)
4. Prefetch ProductSpecification (annotated sa Case/When + ordered)
5. Prefetch ProductBrochure (ordered)
6. Prefetch ProductTestimonial (ordered)
7. ProductSimilar manual override (sa SQL `is_published=True` filter na `related_product`)

Auto fallback (kada manual returns 0 rows): query #7 (manual SELECT vraća empty) + query #8 (auto fallback Product SELECT) = 8 queries.

**Test settings (regression guard):** `config/settings/test.py` (ili `development.py` koji pytest uses) NE SME uključivati `django-debug-toolbar` middleware koji bi dodao session/toolbar query-je i pokvario count.

---

## 4. Templates

### `templates/products/product_detail.html` (glavni)

- `{% extends "base.html" %}`
- `{% load i18n static media_tags %}`
- `{% block title %}{{ product.name }} | {{ product.brand.name }} | {% translate "Ćorić Agrar" %}{% endblock %}`
- `{% block meta_description %}{{ product.description|truncatewords:25 }}{% endblock %}`
- `{% block content %}` sadrži **outer `<article class="coric-product-detail" data-testid="product-detail-page">`** wrapper unutar `<main id="main-content">` koji base.html provider već renderuje.
- **KRITIČNO (SM-D9 + I7 regression guard):** `<article>` MORA sedeti INSIDE `{% block content %}` koji renderuje INSIDE `<main id="main-content">` — NE replace-uje `<main>`, NE wraps u sopstveni `<main>`. EXACTLY 1 `<main>` element na rendered output (mirror Story 2.6 B1 fix).
- Sekcije unutar `<article>` u TAČNOM redosledu (verifikuje test AC3):
  1. **Hero** `<section id="product-hero" aria-labelledby="product-hero-title">` → include `_hero_section.html` (delegated u `hero_overlay_card.html` koji renderuje JEDINI `<h1>` na strani — `product.name`)
  2. **Opis** `{% if product.description %}<section id="product-description" aria-labelledby="product-description-title" class="coric-product-description">{% include "products/partials/_description.html" %}</section>{% endif %}`
  3. **Galerija** `{% if product.images.all %}<section id="product-gallery" aria-labelledby="product-gallery-title" class="coric-product-gallery">{% include "products/partials/_gallery_carousel.html" %}</section>{% endif %}`
  4. **Specs akordion** `{% if product.specifications.all %}<section id="product-specs" aria-labelledby="product-specs-title" class="coric-product-specs">{% include "products/partials/_specs_accordion.html" %}</section>{% endif %}`
  5. **Brošure** `{% if brochures_list %}<aside class="coric-product-brochure-wrap" aria-labelledby="product-brochure-title">{% include "products/partials/_brochure_card.html" %}</aside>{% endif %}` (`<aside>` jer brošure su peripheral content per SM-D9)
  6. **Slični modeli** `{% if similar_products %}<section id="product-similar" aria-labelledby="product-similar-title" class="coric-product-similar">{% include "products/partials/_similar_products.html" %}</section>{% endif %}` (uključuje Wave Divider top iz partial-a)
  7. **Testimonijali (SHARED PARTIL)** `{% if product.testimonials.all %}<section id="product-testimonials" aria-labelledby="product-testimonials-title" class="coric-testimonials">{% include "partials/_testimonials_slider.html" with testimonials=product.testimonials.all slider_id="product-testimonials-title" %}</section>{% endif %}` (SM-D22+D27: explicit include with binding + story-specific `slider_id` da preserve aria-labelledby reference)
  8. **Variants** `{% if product.variants.all %}<section id="product-variants" aria-labelledby="product-variants-title" class="coric-product-variants">{% include "products/partials/_variants_selector.html" %}</section>{% endif %}`
  9. **Story 4.3 extension tačka:** `{% block product_detail_inquiry %}{% endblock %}` (Story 2.7 ostavlja prazan)
- Outer `<article>` MORA imati `data-testid="product-detail-page"` (Playwright Story 9.8 hook)
- NEMA inline `style="..."` atributa bilo gde
- NEMA hardcoded srpski string-ova (sve kroz `{% translate %}` / `{% blocktranslate %}`)
- **TAČNO JEDAN `<h1>`** na strani — proveren BeautifulSoup parse (mirror Story 2.6 T1 test pattern)

### `templates/partials/_testimonials_slider.html` (SHARED — MOVE destination per SM-D23+D27)

Premešten iz `templates/brands/partials/_testimonials_slider.html` (Story 2.6 deliverable). Uvodi se opcioni `slider_id` kwarg sa default vrednošću `"testimonials-title"`. Markup top-of-file:

```django
{% load i18n media_tags %}
{% with slider_id=slider_id|default:"testimonials-title" %}
<h2 id="{{ slider_id }}" class="visually-hidden">{% translate "Iz prve ruke" %}</h2>
{% include "partials/section_eyebrow.html" with text=_("IZ PRVE RUKE") tag="div" %}
<div class="coric-testimonials-slider" data-testimonials-slider ...>
  ... (postojeći markup iz Story 2.6 NETAKNUT) ...
</div>
{% endwith %}
```

**Konzumenti i njihovi kwargs:**
- **Story 2.6 brand_detail.html (line 22):** `{% include "partials/_testimonials_slider.html" with testimonials=testimonials slider_id="brand-testimonials-title" %}` — backwards compat (Story 2.6 testovi na `aria-labelledby="brand-testimonials-title"` ostaju validni, no mutation).
- **Story 2.7 product_detail.html (sekcija 7):** `{% include "partials/_testimonials_slider.html" with testimonials=product.testimonials.all slider_id="product-testimonials-title" %}` — story-specific ID za future-collision guard (Story 3.1 Home može hostovati oba konzumenta na istoj strani).

### `templates/products/partials/_hero_section.html`

Wrapper koji prosleđuje product kontekst u `partials/hero_overlay_card.html` (Story 1.7 partial). Mapping:
- `title` = `product.name` (renderuje se kao `<h1>` unutar `hero_overlay_card.html` — JEDINI `<h1>` na strani per SM-D8/B1)
- `bullets` = `product.key_features|slice:":3"` (lista do 3 stringa)
- `brand_logo` = `product.brand.logo.url` ako postoji, inače `""`
- `brand_logo_alt` = `product.brand.name`
- `variant` = mapiranje `product.brand.brand_color` na repeating_element variant (REUSE Story 2.6 SM-D11 pattern: case-insensitive hex compare `|lower == "#00a4e9"` → `"blue"`, else `"green"`)

### `templates/products/partials/_description.html`

```django
{% load i18n %}
{% include "partials/section_eyebrow.html" with text=_("OPIS PROIZVODA") tag="div" %}
<h2 id="product-description-title" class="visually-hidden">{% translate "Opis proizvoda" %}</h2>
<div class="coric-product-description__body">
  {{ product.description|linebreaks }}
</div>
```

### `templates/products/partials/_gallery_carousel.html`

```django
{% load i18n media_tags %}
{% include "partials/section_eyebrow.html" with text=_("GALERIJA") tag="div" %}
<h2 id="product-gallery-title" class="visually-hidden">{% translate "Galerija slika" %}</h2>
<div class="coric-product-gallery__grid" data-testid="product-gallery-grid">
  {% for image in product.images.all %}
    <a class="glightbox coric-product-gallery__item"
       data-gallery="product-{{ product.slug }}"
       href="{{ image.image.url }}"
       data-glightbox="title: {{ image.alt_text|default:product.name }};"
       data-testid="gallery-item-{{ forloop.counter }}">
      {% responsive_picture image.image alt=image.alt_text|default:product.name sizes="(max-width: 768px) 100vw, 33vw" loading="lazy" css_class="coric-product-gallery__img" %}
    </a>
  {% endfor %}
</div>
```

- `class="glightbox"` + `data-gallery="product-{{ product.slug }}"` su Story 2.5 contract (slug-scoped per Story 2-5 interface contract + SM-D15)
- Sve slike sa `loading="lazy"` (galerija je ispod hero+opis fold-a per SM-D13)
- NEMA `format='PNG'` (product gallery slike su JPEG fotografije — SM brand logo PNG policy AC4)

### `templates/products/partials/_specs_accordion.html`

```django
{% load i18n %}
{% include "partials/section_eyebrow.html" with text=_("SPECIFIKACIJE") tag="div" %}
<h2 id="product-specs-title" class="visually-hidden">{% translate "Tehničke specifikacije" %}</h2>
{% regroup product.specifications.all by section_label as spec_sections %}
{% for section_group in spec_sections %}
  <details class="coric-product-specs__accordion"
           {% if forloop.first %}open{% endif %}
           data-testid="spec-section-{{ section_group.grouper|slugify }}">
    <summary class="coric-product-specs__summary">
      <span class="coric-product-specs__section-label">{{ section_group.grouper }}</span>
      <span class="coric-product-specs__accordion-icon" aria-hidden="true">+</span>
    </summary>
    <table class="coric-product-specs__table">
      <tbody>
        {% for spec in section_group.list %}
          <tr><th scope="row">{{ spec.key }}</th><td>{{ spec.value }}</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </details>
{% endfor %}
```

- `{% if forloop.first %}open{% endif %}` na prvoj sekciji — pošto je queryset sorted po `section_rank` (Motor=1), Motor je uvek prva (SM-D14)
- Prazne sekcije se preskaču kroz `{% regroup %}` (ne renderuje group ako nema items)
- `data-testid="spec-section-{slugified-label}"` per details

### `templates/products/partials/_brochure_card.html`

```django
{% load i18n media_tags %}
{% include "partials/section_eyebrow.html" with text=_("BROŠURE") tag="div" %}
<h2 id="product-brochure-title" class="coric-product-brochure__title">
  {% blocktranslate count counter=brochures_list|length %}Preuzmite brošuru{% plural %}Preuzmite brošure{% endblocktranslate %}
</h2>
<div class="coric-product-brochure__list">
  {% for entry in brochures_list %}
    <div class="coric-product-brochure__card" data-testid="brochure-card-{{ entry.brochure.id }}">
      {% if entry.brochure.cover_thumbnail_image and entry.brochure.cover_thumbnail_image.name %}
        <div class="coric-product-brochure__cover">
          {% responsive_picture entry.brochure.cover_thumbnail_image alt=entry.brochure.title|default:product.name sizes="(max-width: 768px) 100vw, 240px" loading="lazy" css_class="coric-product-brochure__cover-img" %}
        </div>
      {% endif %}
      <div class="coric-product-brochure__meta">
        <h3 class="coric-product-brochure__name">{{ entry.brochure.title|default:product.name }}</h3>
        <p class="coric-product-brochure__size">{{ entry.size_bytes|filesizeformat }}, {% translate "PDF" %}</p>
        <a href="{{ entry.brochure.pdf_file.url }}"
           target="_blank"
           rel="noopener noreferrer"
           download
           class="coric-button coric-button--primary"
           data-testid="brochure-download-{{ entry.brochure.id }}">
          {% translate "PREUZMI" %}
        </a>
      </div>
    </div>
  {% endfor %}
</div>
```

- Loop kroz `brochures_list` (NE `product.brochures.all`) per SM-D26/I8 view pre-computation
- Plural heading per SM-D24/I1 (`{% blocktranslate count %}{% plural %}{% endblocktranslate %}`)
- `entry.size_bytes|filesizeformat` Django built-in filter
- Direktan `<a>` markup (NE `pill_button.html` partial — SM-D22 mirror Story 2.6 jer pill_button ne podržava `target/rel/download` atribute)
- `{% translate "PDF" %}` per SM-D25/I3 policy compliance
- `{% if entry.brochure.cover_thumbnail_image and entry.brochure.cover_thumbnail_image.name %}` double guard per SM-D26/I9 (partial-state ImageField defense)

### `templates/products/partials/_similar_products.html`

```django
{% load i18n media_tags %}
{% include "partials/wave_divider.html" with position="top" %}
{% include "partials/section_eyebrow.html" with text=_("SLIČNI MODELI") tag="div" %}
<h2 id="product-similar-title" class="coric-product-similar__title">{% translate "Možda će vas zanimati i" %}</h2>
<div class="coric-product-similar__grid" data-testid="product-similar-grid">
  {% for sim in similar_products %}
    <a class="coric-product-card"
       href="{{ sim.get_absolute_url }}"
       aria-label="{{ sim.name }}"
       data-testid="similar-product-card-{{ sim.slug }}">
      <div class="coric-product-card__image">
        {% responsive_picture sim.main_image alt=sim.name sizes="(max-width: 768px) 100vw, 25vw" loading="lazy" css_class="coric-product-card__img" %}
      </div>
      <div class="coric-product-card__body">
        <h3 class="coric-product-card__title">{{ sim.name }}</h3>
        {% if sim.horse_power %}
          <p class="coric-product-card__spec">{{ sim.horse_power }} {% translate "KS" %}</p>
        {% endif %}
        <span class="coric-button coric-button--primary coric-product-card__cta" aria-hidden="true">{% translate "OPŠIRNIJE" %}</span>
      </div>
    </a>
  {% endfor %}
</div>
```

- Wave Divider iznad sekcije (`with position="top"`)
- Visible heading "Možda će vas zanimati i" per SM-D13 (NE skriveni)
- Linkable card sa nested-interactive guard: `<a>` wrapper + `aria-label` + CTA `<span aria-hidden="true">` (NE `<a>` ni `<button>`)
- `data-testid="similar-product-card-{slug}"` per card
- View limituje na 4 entries; template ne treba dodatni cap

### `templates/products/partials/_variants_selector.html`

```django
{% load i18n media_tags %}
{% include "partials/section_eyebrow.html" with text=_("VARIJANTE") tag="div" %}
<h2 id="product-variants-title" class="coric-product-variants__title">{% translate "Varijante proizvoda" %}</h2>
<p class="coric-product-variants__intro">{% translate "Kliknite na varijantu za uvećani prikaz slike." %}</p>
<div class="coric-product-variants__grid" data-testid="product-variants-grid">
  {% for variant in product.variants.all %}
    {% if variant.image %}
      <a class="glightbox coric-product-variants__card"
         data-gallery="product-{{ product.slug }}-variants"
         href="{{ variant.image.url }}"
         data-glightbox="title: {{ variant.name }};{% if variant.code %} description: {% translate 'Kod' %}: {{ variant.code }};{% endif %}"
         data-testid="variant-card-{{ variant.id }}"
         aria-label="{% blocktranslate with name=variant.name %}Otvori uvećani prikaz: {{ name }}{% endblocktranslate %}">
        ... (image + body) ...
      </a>
    {% else %}
      <div class="coric-product-variants__card coric-product-variants__card--no-image"
           data-testid="variant-card-{{ variant.id }}">
        ... (body only) ...
      </div>
    {% endif %}
  {% endfor %}
</div>
```

- `class="glightbox"` + `data-gallery="product-{{ product.slug }}-variants"` (RAZLIČIT od main galery `product-{{ product.slug }}` per SM-D10/D15 — sprečava prev/next preklapanje između main + variants)
- NEMA `<form>` element, NEMA `data-variant-id`, NEMA URL fragment, NEMA state change (per PRD FR-48 + SM-D10)
- Variant bez slike: render plain `<div>` (no GLightbox link) — defensive
- `aria-label` na `<a>` koji najavi cilj klika

---

## 5. JavaScript modules

### `static/js/product-gallery.js` (OPCIONO — SM-D6 default je NE)

**Default odluka (SM-D6):** pure CSS scroll-snap (mobile) + CSS Grid (desktop) za gallery carousel. NEMA novi JS modul. `templates/base.html` ne dobija novi `<script>` tag.

Razlog: GLightbox već handluje prev/next + keyboard nav unutar Lightbox-a (Story 2.5 deliverable); outer-carousel prev/next bi dupliralo funkcionalnost.

### `static/js/testimonials-slider.js` (Story 2.6 deliverable — REUSE)

Site-wide loaded u `base.html` (Story 2.6). Selektor `[data-testimonials-slider]` ostaje identičan; shared partial NE menja markup beyond `slider_id` interpolation u `<h2 id>`. JS defensive auto-detect — ako selektor nije na strani, bail-uje silently.

---

## 6. CSS components

### `static/css/components/product-detail.css` (NOVO)

- `.coric-product-detail` root klasa
- `.coric-product-description`, `.coric-product-description__body`
- `.coric-product-brochure-wrap` (aside), `.coric-product-brochure__list`, `.coric-product-brochure__card`, `.coric-product-brochure__cover`, `.coric-product-brochure__cover-img`, `.coric-product-brochure__meta`, `.coric-product-brochure__name`, `.coric-product-brochure__size`, `.coric-product-brochure__title`
- `.coric-product-similar`, `.coric-product-similar__grid`, `.coric-product-similar__title`
- `.coric-product-specs`, `.coric-product-specs__accordion`, `.coric-product-specs__summary`, `.coric-product-specs__section-label`, `.coric-product-specs__accordion-icon`, `.coric-product-specs__table`
- `+/-` toggle pseudo-element CSS:
  ```css
  details.coric-product-specs__accordion[open] > summary > .coric-product-specs__accordion-icon::after { content: "−"; }
  ```
- `prefers-reduced-motion` blok:
  ```css
  @media (prefers-reduced-motion: reduce) {
    .coric-product-specs__accordion { transition: none !important; }
  }
  ```
- **MIGRATE (SM-D21):** `.coric-product-placeholder`, `.coric-product-placeholder__title`, `.coric-product-placeholder__message` iz `brand-listing.css` (defunkcionalne sad — placeholder template je obrisan; opciono DELETE umesto migracije)
- Sve vrednosti kroz `var(--token-name)` (NIKAD magic hex/px)
- `coric-` prefix na svim klasama

### `static/css/components/product-gallery.css` (NOVO)

- `.coric-product-gallery`, `.coric-product-gallery__grid`, `.coric-product-gallery__item`, `.coric-product-gallery__img`
- CSS Grid (desktop) ili scroll-snap (mobile) per SM-D6

### `static/css/components/product-variants.css` (NOVO)

- `.coric-product-variants`, `.coric-product-variants__grid`, `.coric-product-variants__card`, `.coric-product-variants__card--no-image`, `.coric-product-variants__image`, `.coric-product-variants__img`, `.coric-product-variants__body`, `.coric-product-variants__name`, `.coric-product-variants__code`, `.coric-product-variants__desc`, `.coric-product-variants__title`, `.coric-product-variants__intro`
- 1-4 per row responsive grid
- hover state + `:focus-visible` outline iz tokens

### `static/css/main.css` (EDIT)

Dodaje 3 nove `@import url('./components/...');` linije (mirror Story 1.7+1.8+2.5+2.6 sintaksu):

```css
@import url('./components/product-detail.css');
@import url('./components/product-gallery.css');
@import url('./components/product-variants.css');
```

### `static/css/components/brand-listing.css` (EDIT — CLEANUP)

UKLONI 3 selektora per SM-D21 cleanup plan:
- `.coric-product-placeholder`
- `.coric-product-placeholder__title`
- `.coric-product-placeholder__message`

Ostatak fajla netaknut (regression guard za Story 2.6 testove).

---

## 7. Factory expectations (TEA — `apps/products/tests/factories.py` EXTEND)

Story 2.6 je uveo `ProductFactory`, `ProductSpecificationFactory`, `ProductTestimonialFactory`. Story 2.7 EXTEND-uje istom plain-Python classmethod pattern (factory_boy NIJE u pyproject.toml):

### `ProductImageFactory` (NOVO)

```python
@classmethod
def create(cls, product=None, order=0, alt_text="Test slika", image=None, **overrides):
    # image=None → use SimpleUploadedFile sa minimal PNG bytes
    ...
```

### `ProductBrochureFactory` (NOVO)

```python
@classmethod
def create(cls, product=None, title="Test Brošura", pdf_file=None, cover_thumbnail_image=None, **overrides):
    # pdf_file=None → ContentFile sa minimal %PDF-1.4 stub
    # cover_thumbnail_image=None → opciono PNG stub
    ...
```

### `ProductVariantFactory` (NOVO)

```python
@classmethod
def create(cls, product=None, name="Test Varijanta", code="", image=None, description="", order=0, **overrides):
    ...
```

### `ProductSimilarFactory` (NOVO)

```python
@classmethod
def create(cls, product=None, related_product=None, order=0, **overrides):
    # related_product=None → kreira drugi Product
    ...
```

Svi factory-ji slede Story 2.6 pattern: `_counter` class var za unique names, `**overrides` propagiraju u `Model.objects.create()`, **kwargs override defaults.

---

## 8. HTML `data-testid` surface contract (Playwright Story 9.8 hooks)

- `product-detail-page` (outer `<article>`)
- `product-gallery-grid` (gallery wrapper)
- `gallery-item-{N}` (per gallery image, 1-indexed forloop.counter)
- `spec-section-{slugified-label}` (per `<details>`)
- `brochure-card-{id}` (per brochure card)
- `brochure-download-{id}` (per brochure PDF download CTA)
- `product-similar-grid` (similar products wrapper)
- `similar-product-card-{slug}` (per similar card)
- `testimonials-slider` (preserved iz shared partial; per SM-D27 slider_id MENJA `<h2 id>` ali NE `data-testid`)
- `testimonial-{N}` (per testimonial slide)
- `prev-testimonial`, `pause-testimonial`, `next-testimonial` (slider controls)
- `product-variants-grid` (variants wrapper)
- `variant-card-{id}` (per variant card)

---

## 9. AC9 Lighthouse manual smoke (out-of-test-scope)

Manuelni Dev smoke check + Lighthouse audit (a11y ≥ 95, performance ≥ 75, SEO ≥ 90). JSON artifact preservation u `_bmad-output/implementation-artifacts/2-7-lighthouse-YYYYMMDD.json` per Story 2.6 § Lighthouse JSON pattern.

Test placeholder: `apps/products/tests/test_lighthouse_manual.py` — 1 `xfail` test sa `reason="manual smoke per AC9"`.

---

## 10. Prereq warnings (Dev MUST satisfy or document)

1. **HU translation gap (PREREQ za AC5 hu test):** `locale/hu/LC_MESSAGES/django.po` linije 309-323 imaju `msgstr ""` (PRAZNE) za "Motor", "Transmisija", "Hidraulika", "Ostalo" (verifikovano live 2026-05-30). TEA test `test_specs_section_labels_hu_locale` (Subtask 12.4) je markiran `xfail`. Kad Dev/Mihas popuni hu prevode, decorator se uklanja.
2. **Empirical query count locked at 7 (manual path) per SM-D28 (verifikovano 2026-05-30):** Manual ProductSimilar path = 7 queries; auto fallback path = 8 queries (manual SELECT returns empty + auto SELECT executes). Test `test_assert_num_queries_exactly_7` MORA construct fixture sa `ProductSimilar` entry da hit-uje manual path. Story's AC1 enumeracija ("samo jedan se exec-uje per request") je tehnički netačno za auto fallback path, ali "exactly 7 on manual path" je validno.
3. **Plural Serbian (sr nplurals=3) — Subtask 7.4 SM-D24/I-iter2-3:** posle `just makemessages`, Dev MORA popuniti SVA 3 msgstr-a za "Preuzmite brošuru" plural key:
   - msgstr[0] = "Preuzmite brošuru" (n%10==1 && n%100!=11)
   - msgstr[1] = "Preuzmite brošure" (n%10∈[2,4] && n%100∉[10,20])
   - msgstr[2] = "Preuzmite brošura" (ostalo — genitive plural)
4. **SM-D6 carousel decision (pure CSS vs vanilla JS):** Default = pure CSS scroll-snap. Ako Dev revidira ka vanilla JS, kreira `static/js/product-gallery.js` + edituje `templates/base.html` (+1 `<script>` tag).

---

## 11. Test discipline note

Per project-context.md § Test discipline (linija 294): TEA piše testove (RED phase), Dev piše kod (GREEN phase). Story 2.7 RED-phase test fajlovi:

- `apps/products/tests/test_views_product_detail.py` — AC1+AC2 view + queries + context (~13 method, ~15 parametrized invocations)
- `apps/products/tests/test_templates_product_detail.py` — AC3-AC8 + AC5 hu locale (~27 tests; 1 xfail hu)
- `apps/products/tests/test_url_routing.py` — AC1 URL routing (5 tests)
- `apps/products/tests/test_placeholder_deleted.py` — Subtask 12.5 regression guard (4 tests)
- `apps/products/tests/test_static_assets.py` — Subtask 12.6 cross-cutting (4 tests)
- `apps/products/tests/test_lighthouse_manual.py` — AC9 xfail placeholder (1 test)
- `apps/products/tests/factories.py` — EXTEND sa 4 nova factory classes

**Total: ~55 tests** (54-55 method count depending on AC3 testimonials split).

Run komanda:
```bash
docker compose -f compose/local.yml exec django uv run pytest apps/products/tests/ -v
```

Expected RED-phase result:
- ~50 FAILED (ProductDetailView ne postoji, templates ne postoje)
- 4 PASSED (existing `test_placeholder.py` testovi — Dev briše u GREEN Subtask 1.4)
- 1 XFAILED (AC9 Lighthouse manual placeholder)
- 1 XFAILED (AC5 hu locale ako prevodi prazni)

---

END OF CONTRACT
