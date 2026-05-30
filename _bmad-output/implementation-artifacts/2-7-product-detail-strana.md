---
story-id: "2.7"
story-key: 2-7-product-detail-strana
title: Product Detail Strana
status: draft
epic_num: 2
epic_title: Public Catalog — Browse Brands & Products
module: apps/products/ (REPLACE placeholder_view sa pravim ProductDetailView; templates/products/ dobija product_detail.html + 8 partials)
created: 2026-05-30
last_modified: 2026-05-30
author: Mihas (SM autonomous; Story 2.6 SM-D1..D22 patterns reused: get_template_names, locale-aware Case/When per-request, direct anchor CTA, hidden empty sections; SM Fix iter 1/5 — 6 CRITICAL + 10 IMPROVEMENT issues resolved [C1-C6 + I1-I10] adding SM-D19..D26; SM Fix iter 2/5 — 7 IMPROVEMENT issues resolved [I-iter2-1..I-iter2-7] adding SM-D27..D28 and I-iter2-8 logged STYLE to Open Questions #7)
depends_on:
  - 2-1-brand-series-category-subcategory-modeli   # Brand (logo, slogan, brand_color), Series (layout_mode), Subcategory
  - 2-2-product-i-related-modeli                   # Product + ProductImage + ProductVariant + ProductSpecification + ProductBrochure + ProductTestimonial + ProductSimilar (sve potvrđeno postoji live)
  - 2-3-image-pipeline-sa-sorl-thumbnail-responsive-srcset  # {% responsive_picture %} template tag + MP-D5 format='PNG' za transparency
  - 2-4-pdf-cover-thumbnail-generator              # ProductBrochure.cover_thumbnail_image (auto-gen kroz post_save signal); responsive_picture render brošure cover-a
  - 2-5-glightbox-integracija                      # base.html lightbox-init.js + `.glightbox` selektor + coric:lightbox-open/close event kontrakt
  - 2-6-brand-listing-strana-sa-grid-extended-layout-om  # statistic-counter/testimonials-slider JS site-wide; coric-button BEM klase; brand-listing.css coming-soon/placeholder klase (deferred cleanup u Subtask 8.9); Case/When section_rank+section_label pattern (SM-D14/D20) extract candidate
---

# Story 2.7: Product Detail Strana

Status: draft

## Opis

As a **Marko (poljoprivrednik koji istražuje konkretan model traktora online — npr. Agri-Tracking TB-804 — i poredi specifikacije pre nego što pošalje upit; Đorđe — Mihasov klijent koji testira responsive ponašanje na 375px ekranu, tabuje kroz akordion specifikacija sa tastature, otvara galeriju kroz Lightbox bez miša)**,
I want **kompletnu stranicu modela na `/sr/proizvod/<brand-series-model-slug>/` koja prikazuje: hero overlay karticu sa brand logo + nazivom modela + do 3 bullet ključnih karakteristika (`Product.key_features`) preko Repeating Element vodenog žiga; sekciju „Opis proizvoda" sa formatiranim `Product.description`; karusel galerije slika (`ProductImage` u redosledu) gde svaka slika ima `<picture>` sa srcset 400w/800w/1600w i klik otvara GLightbox modal; akordion specifikacije (4 sekcije — Motor → Transmisija → Hidraulika → Ostalo) gde je Motor `<details open>` po default-u sa `+/-` toggle ikonom a ostale zatvorene, prazne sekcije se skrivaju; Brošura card sa `{% responsive_picture brochure.cover_thumbnail_image %}` cover-thumbnailom + naslovom + size labelom („X.X MB, PDF") + direktnim PDF download CTA (`target="_blank" rel="noopener noreferrer" download`); sekciju „Slični modeli" sa FR-20 hibrid logikom (manual `ProductSimilar` ako postoji, inače auto fallback po istom brendu+seriji); slider testimonijala „Iz prve ruke" (reuse `_testimonials_slider.html` partial iz Story 2.6); Variant selektor sekciju koja renderuje SAMO ako Product ima ≥1 `ProductVariant`, sa karticama (slika + naziv + opcioni kod + opcioni opis) gde klik otvara GLightbox zoom slike — bez state change, bez URL change, bez form submita**,
so that **mogu informisano da uporedim model sa konkurentima i pošaljem upit pre kupovine (Marko vidi sve specifikacije + brošuru + sličnu opciju u jednom screen-u; Đorđe tabuje kroz akordion bez miša, NVDA mu najavi sekciju, GLightbox poštuje `prefers-reduced-motion`, slider auto-advance pauzira kad se Lightbox otvori per Story 2.5 kontrakt); strana zadovoljava Lighthouse a11y skor ≥ 95 (UX-DR-13 + NFR-2 + Story 9.9 a11y audit gate), poštuje single-h1 pravilo (B1 fix iz Story 2.6 — `<h1>` se renderuje TAČNO jednom preko `hero_overlay_card.html` partial-a), i postavlja kanonski detail pattern koji Story 2.10/2.11/2.12 (priključna mehanizacija detail strane) reuse-uju**.

Ova story **ZAMENJUJE** placeholder stub uveden u Story 2.6 (C8 fix). Specifično:

- `apps/products/urls.py` — pattern `path("proizvod/<slug:slug>/", ..., name="detail")` i `app_name = "products"` OSTAJU NETAKNUTI; menja se SAMO `views` referenca (FBV `placeholder_view` → CBV `ProductDetailView.as_view()`).
- `apps/products/views.py` — `placeholder_view(request, slug)` FBV se BRIŠE; zamena je `ProductDetailView(DetailView)` CBV sa `get_queryset()`, `get_context_data()`, i (opciono) `get_template_names()` override (`get_template_names` nije nužan jer products nema coming-soon ekvivalent — vidi SM-D2).
- `templates/products/_placeholder.html` se **BRIŠE** (kraći lifespan od 1 story-je per SM-D21 iz Story 2.6); novi entry-template je `templates/products/product_detail.html` plus 8 partials u `templates/products/partials/`.

Server-side rendering only (NO HTMX u 2.7 — Decision SM-D1; svi HTMX entry-points za product page su out-of-scope: Story 2.8 HTMX filteri su listing scope; Story 4.3 model inquiry forma uvodi HTMX submit). Strana je **prvi konzument** sledećih artefakata iz Story 2.2-2.6:

- **`ProductImage`, `ProductVariant`, `ProductSpecification`, `ProductBrochure`, `ProductTestimonial`, `ProductSimilar` modeli** (Story 2.2) — sve verifikovano live `apps/products/models.py` (vidi Dev Notes § Model discovery).
- **`{% responsive_picture %}` template tag** (Story 2.3) — za hero brand logo (sa `format='PNG'` per MP-D5), galeriju slika, brošure cover-thumbnail, testimonijal photo, variant kartice, slične-model kartice.
- **`ProductBrochure.cover_thumbnail_image`** (Story 2.4 deliverable — auto-gen post_save signal); brošure card renderuje `cover_thumbnail_image` kroz `responsive_picture`.
- **GLightbox vendor + `coric:lightbox-open/close` event kontrakt** (Story 2.5) — galerija slika i variant selektor koriste `class="glightbox"` data-attribute pattern; testimonials slider auto-advance pauzira na `coric:lightbox-open`.
- **`_testimonials_slider.html` partial markup struktura** (Story 2.6) — Story 2.7 REUSE-uje pattern kroz **shared partial move + slider_id kwarg** (vidi SM-D4 revidirano + SM-D23 + SM-D27): MOVE iz `templates/brands/partials/_testimonials_slider.html` u `templates/partials/_testimonials_slider.html` (shared) sa opcionim `slider_id` kwarg-om (default `"testimonials-title"`); konzumira se kroz `{% include "partials/_testimonials_slider.html" with testimonials=product.testimonials.all slider_id="product-testimonials-title" %}` u product_detail.html. NE kreira se mirror copy `templates/products/partials/_testimonials.html`.
- **`coric-button`, `coric-button--primary`, `coric-pill-badge`, `coric-product-card` BEM klase** (Story 1.7 + Story 2.6) — site-wide loaded kroz `main.css`; Story 2.7 SAMO koristi, NE re-definiše.
- **Section Eyebrow + Wave Divider + Repeating Element partials** (Story 1.7) — koriste se u sekcijama (eyebrow za sekcijske naslove, wave divider iznad slični-modeli sekcije, repeating element u hero kartici per `_hero_section.html` mapping).
- **`statistic-counter.js` + `testimonials-slider.js`** (Story 2.6) — site-wide u `base.html`; product detail strana ne renderuje statistike (`brand.statistics` je brand-only feature, ne product), ali testimonials slider reuse-uje JS.

**Foundation za:**

- **Story 2.10/2.11/2.12 (Jeegee + Subcategory + HZM/Tulip detail strane):** isti detail layout pattern (hero + opis + galerija + akordion + brošura + slični + testimonijali + variants); ako se pokaže da je markup zaista isti, refaktor iz `templates/products/product_detail.html` u shared `_product_detail_layout.html` partial je trivijalan (Story 2.10 SM može refaktor u svom create-story koraku).
- **Story 4.3 (Model Inquiry Form):** forma će biti rendered ispod hero kartice ili pored opisa proizvoda na product detail strani — Story 4.3 dodaje `{% block product_detail_inquiry %}{% endblock %}` extension tačku u `product_detail.html` (Story 2.7 NE renderuje formu — placeholder block je dovoljan; Story 4.3 implementuje formu i HTMX submit logiku).
- **Story 2.8 (Tractor Listing sa HTMX filterima):** Grid kartica „OPŠIRNIJE" CTA linkuje na `{% url 'products:detail' slug=product.slug %}` — Story 2.7 ZAMENJUJE placeholder; svi prethodni linkovi automatski počinju da rade.
- **Story 6.1 (SEOMeta model):** product detail `<title>` + `meta description` + Open Graph + Twitter Card će postati admin-editable kroz `apps/seo` (Story 6.1 dodaje `SEOMeta` model sa generic FK ka Product); Story 2.7 koristi default `{{ product.name }} | {{ product.brand.name }} | Ćorić Agrar` title i `{{ product.description|truncatewords:25 }}` meta description (placeholder dok 6.1 ne uvede admin override).
- **Story 9.8 (Playwright E2E za UJ-1):** Marko journey screen 2 je product detail (klik na karticu sa Story 2.6 → product detail; click „Otvori galeriju" → Lightbox; click „Pošalji upit" CTA → Story 4.3 forma; sve interaktivnosti testirane kroz `data-testid` atribute koje Story 2.7 obezbeđuje).
- **Story 9.9 (a11y audit + Lighthouse pass):** verifikuje WCAG 2.1 AA + Lighthouse a11y ≥ 95; Story 2.7 mora dostići isti gate kao 2.6 (manuelni AC8).

**Princip:** Server-side rendering, **NO HTMX swap u 2.7** (Decision SM-D1; HTMX form submit dolazi u Story 4.3). Vanilla JS modules (IIFE + `'use strict';` + `prefers-reduced-motion` respect + Story 2.5 + 2.6 stilski mirror) ako budu potrebne (npr. gallery carousel — vidi SM-D6 za carousel-vs-CSS-only decision). CSS BEM sa `coric-` prefiksom + isključivo `var(--token)` reference iz `static/css/tokens.css`. Sve user-facing string-ove kroz `{% translate %}` / `gettext_lazy as _`. URL pattern `/<lang>/proizvod/<slug>/` već registrovan kroz Story 2.6 placeholder; Story 2.7 NE EDITUJE `config/urls.py` (pattern + namespace ostaju identični). **NEMA backend forme**, **NEMA HTMX endpoint-a**, **NEMA admin promena**, **NEMA migracija** — pure view + template + static asset story.

**Strukturna arhitektura — repository delta:** Repository dobija **12-13 novih fajlova** + **7-8 EDIT operacija** + **3 DELETE operacije** + **1 MOVE operacija (DELETE + ADD net 0 brojano kao MOVE)** + **0 model/migration promena**. (SM Fix iter 1 update: -1 NOVO `_testimonials.html` partial koji se NE kreira per SM-D22/D23; +1 MOVE `_testimonials_slider.html` iz brands/partials/ u partials/ shared; +1 DELETE `apps/products/tests/test_placeholder.py` per C2; +1 EDIT `templates/brands/brand_detail.html` line 21 `aria-labelledby` reference update per SM-D23. **SM Fix iter 2 update**: brand_detail.html linija 21 EDIT je SKINUT (per SM-D27 backwards compat — `aria-labelledby="brand-testimonials-title"` ostaje, samo line 22 include path + slider_id kwarg se EDITUJE); +1 EDIT `_bmad-output/implementation-artifacts/2-6-interface-contract.md` linija 207 per I-iter2-1 cascade sync; +1 EDIT `_bmad-output/implementation-artifacts/sprint-status.yaml` `last_updated` polje per I-iter2-1 cross-story cascade tracking; brand tests file je SKINUT iz EDIT liste per SM-D27 backwards compat — assertion ostaje unchanged.):

| Path | Tip | Razlog |
|---|---|---|
| `apps/products/views.py` | EDIT (REPLACE) | `placeholder_view` FBV se BRIŠE; dodaje se `ProductDetailView(DetailView)` CBV sa get_queryset() (Case/When section_rank + section_label + prefetch_related chain za images/variants/specifications/brochures/testimonials), get_context_data() (similar_products manual-or-auto FR-20 logika) |
| `apps/products/urls.py` | NETAKNUT | Pattern `path("proizvod/<slug:slug>/", ..., name="detail")` ostaje; SAMO se views import promeni iz `views.placeholder_view` → `views.ProductDetailView.as_view()` — JE deo Story 2.7 EDIT-a (1-line change) |
| `templates/products/_placeholder.html` | DELETE | Placeholder template iz Story 2.6 C8 fix se uklanja; Story 2.7 product_detail.html je naslednik |
| `templates/products/product_detail.html` | NOVO | Glavni template; `{% extends "base.html" %}`; renderuje sekcije TAČNIM redosledom (hero → opis → galerija → akordion specs → brošura → slični → testimonijali → variants) |
| `templates/products/partials/_hero_section.html` | NOVO | Hero overlay sa brand logo + naziv proizvoda + do 3 bullets iz `product.key_features` (wrapper oko `partials/hero_overlay_card.html` iz Story 1.7) |
| `templates/products/partials/_description.html` | NOVO | „Opis proizvoda" sekcija — `{{ product.description|linebreaks }}` (Django built-in filter za paragraph wrapping); empty state ako `description` je prazan |
| `templates/products/partials/_gallery_carousel.html` | NOVO | Karusel galerije slika (`ProductImage.objects.filter(product=product).order_by('order', 'id')`); svaka slika je `<a class="glightbox" data-gallery="product-{{ product.slug }}" href="{{ image.image.url }}"><picture>...</picture></a>` — GLightbox auto-pickup po `.glightbox` selektoru per Story 2.5 |
| `templates/products/partials/_specs_accordion.html` | NOVO | Akordion specifikacija sa `{% regroup product.specifications.all by section_label as spec_sections %}` + `<details open>` na prvoj (Motor) sekciji; `<table>` per-section sa key/value rows |
| `templates/products/partials/_brochure_card.html` | NOVO | Brošura card sa `responsive_picture` cover thumbnail + naslov + size label + direktan `<a>` PDF download (target=_blank, rel=noopener, download); render-uje SAMO ako `product.brochures.exists()` |
| `templates/products/partials/_similar_products.html` | NOVO | Slični modeli sekcija sa Wave Divider iznad + 2-4 kartice (FR-20 hibrid logika resolvana u view layer); reuse-uje `coric-product-card` BEM iz Story 2.6 |
| ~~`templates/products/partials/_testimonials.html`~~ | ~~NOVO~~ | **DEPRECATED** (SM Fix iter 1, C6/SM-D23) — mirror copy NIJE potreban; vidi MOVE row ispod za shared partial pristup. |
| `templates/partials/_testimonials_slider.html` | MOVE (NOVO + DELETE) | **Shared partial** (single source-of-truth za brand listing 2.6, product detail 2.7, future home 3.1). MOVE source: `templates/brands/partials/_testimonials_slider.html` (Story 2.6 deliverable) → MOVE destination: `templates/partials/_testimonials_slider.html` (Story 2.7 shared dir). Promene tokom move-a (SM Fix iter 2, SM-D27): UVODI se opcioni `slider_id` kwarg sa default `"testimonials-title"`; `<h2 id="...">` koristi `{{ slider_id }}` interpolaciju umesto hardcoded ID. Brand konzument prosleđuje `slider_id="brand-testimonials-title"` (backwards compat), product konzument prosleđuje `slider_id="product-testimonials-title"` (story-specific future-collision guard). Vidi SM-D22/D23/D27. |
| `templates/brands/brand_detail.html` | EDIT (1-line) | **SM Fix iter 1+2, SM-D23+D27 update:** Linija 21 `<section ... aria-labelledby="brand-testimonials-title">` OSTAJE NETAKNUTA (backwards compat per SM-D27 — brand prosleđuje story-specific kwarg za isti ID koji testovi već asertuju). Linija 22 `{% include "brands/partials/_testimonials_slider.html" %}` se EDITUJE u `{% include "partials/_testimonials_slider.html" with testimonials=testimonials slider_id="brand-testimonials-title" %}` (eksplicitan binding + slider_id kwarg — Story 2.6 view već postavlja `testimonials` u kontekst, ali eksplicitni `with` kontrakt je vidljiv u oba konzumenta; `slider_id` osigurava da renderovani `<h2 id="brand-testimonials-title">` matchuje postojeću `aria-labelledby` reference). |
| `apps/products/tests/test_placeholder.py` | DELETE | **SM Fix iter 1, C2:** 4 tests iz Story 2.6 koji asertuju placeholder_view + _placeholder.html renderovanje regress-uju nakon Subtask 1.3 DELETE template-a + Subtask 1.1 DELETE FBV-a. Brisanje testova zajedno sa source-om (zero-orphan policy). Replacement: novi test_placeholder_deleted.py (Subtask 12.5) + test_urls_detail.py/test_views_detail.py (Subtask 12.1-12.2) covers ista URL ruta sad serve-uje ProductDetailView. Vidi SM-D16 (proširen). |
| `templates/products/partials/_variants_selector.html` | NOVO | Variant selektor sekcija; render-uje SAMO ako `product.variants.exists()`; kartice sa GLightbox link na variant.image |
| `static/css/components/product-detail.css` | NOVO | Layout sekcija (hero, gallery wrapper, accordion details/summary stilovi, brochure card, similar grid, variants grid); migracija `coric-product-placeholder*` BEM klasa iz `brand-listing.css` (SM-D21 cleanup); coric-button hover/focus states ostaju u Story 1.7 pill-button.css |
| `static/css/components/product-gallery.css` | NOVO | Galerija carousel container, slide thumbnail grid (desktop) / scroll-snap horizontal scroll (mobile), nav prev/next (ako se koristi vanilla JS carousel — SM-D6 alternativa) |
| `static/css/components/product-variants.css` | NOVO | Variant kartice grid (1-4 per row responzivno), hover state, focus-visible outline; reuse coric-button BEM iz Story 1.7 |
| `static/css/main.css` | EDIT | Dodaje 3 nove `@import url('./components/...');` linije (product-detail, product-gallery, product-variants) — TAČAN mirror Story 1.7+1.8+2.5+2.6 sintaksu |
| `static/css/components/brand-listing.css` | EDIT (CLEANUP) | UKLANJA `.coric-product-placeholder*` 3 selektora (per Story 2.6 SM-D21 cleanup plan — placeholder template je obrisan); ostatak fajla netaknut |
| `static/js/product-gallery.js` | NOVO (opciono — vidi SM-D6) | Vanilla IIFE za gallery carousel navigacija; AKO bira se vanilla carousel (NE pure CSS scroll-snap), implementira prev/next + keyboard nav + thumbnail klik; respektuje prefers-reduced-motion |
| `templates/base.html` | EDIT | Dodaje 1 novi `<script>` tag sa `defer` POSLE `testimonials-slider.js` (linija 42): `product-gallery.js` (uslovno, samo ako SM-D6 odluka je vanilla JS carousel) |

**Brojanje (SM Fix iter 1, I4 — recount):** **12-13 NOVO fajlova** (1 main template: `product_detail.html`; 7 partials u products/: `_hero_section`, `_description`, `_gallery_carousel`, `_specs_accordion`, `_brochure_card`, `_similar_products`, `_variants_selector` — **NEMA** `_testimonials.html` jer se koristi shared kroz MOVE; 3 CSS: `product-detail.css`, `product-gallery.css`, `product-variants.css`; 1 JS opciono: `product-gallery.js`; ako SM-D6 izabere pure CSS scroll-snap, JS se NE kreira pa je broj 11 NOVO + EDIT na base.html otpada) + **6 EDIT** (`apps/products/views.py` REPLACE, `apps/products/urls.py` 1-line, `static/css/main.css` +3 @import, `static/css/components/brand-listing.css` -3 selektora cleanup, `templates/brands/brand_detail.html` 1-line aria-labelledby + include path update per SM-D23, `templates/base.html` +1 script tag — uslovno; OBAVEZNO 5 EDIT ako bez JS) + **2 DELETE** (`templates/products/_placeholder.html` + `apps/products/tests/test_placeholder.py`) + **1 MOVE** (`_testimonials_slider.html` brands/partials/ → partials/; net 0 file count change ali računa se kao kompozitan MOVE = 1 DELETE source + 1 NEW destination operacija). **Računica:** 1 main + 7 partials + 3 CSS + (0 ili 1 JS) = 11-12 NOVO unique; +1 NEW iz MOVE destination = 12-13 NOVO total; 5-6 EDIT; 2 DELETE + 1 DELETE iz MOVE source = 3 DELETE total (alternativno: ako MOVE računamo atomarno kao single operacija net 0, onda 2 DELETE + 11-12 NOVO).

Postojeći fajlovi koji ostaju **NETAKNUTI** (regression guards): `apps/products/models.py`, `apps/products/admin.py`, `apps/products/translation.py`, `apps/products/migrations/`, `apps/brands/views.py`, `apps/brands/urls.py`, `apps/brands/models.py`, `apps/brands/templates/`, `apps/core/`, `apps/media_pipeline/`, `config/urls.py` (pattern netaknut), `static/vendor/`, `static/css/tokens.css`, `static/css/components/{header,footer,sticky-nav,lightbox,hero-overlay-card,repeating-element,pill-button,section-eyebrow,wave-divider,statistic-medallion,testimonials-slider}.css`, `templates/partials/*`, `templates/brands/*`, `pyproject.toml`, `config/settings/`, `compose/django/Dockerfile`.

## Kriterijumi prihvatanja

**AC1 — URL pattern `/<lang>/proizvod/<slug>/` rezolvuje `ProductDetailView`; rezolucija prolazi i daje HTTP 200 za `is_published=True` proizvode (status TextChoices vrednost je IRRELEVANTNA — `is_published` je SOLE public-visibility gate per SM-D20), HTTP 404 za nepostojeće ili `is_published=False` proizvode (regardless of status); query plan je optimizovan na TAČNO 7 SQL upita per request (enumerisanih u AC2 docstring + view-layer komentaru); `assertNumQueries(7)` exact-match per SM-D21**

- **Given** `apps.products` registrovan u `INSTALLED_APPS`; `i18n_patterns()` aktivan iz Story 1.4; Story 2.6 je registrovala `apps/products/urls.py` sa `app_name="products"` + pattern `proizvod/<slug:slug>/` (live verifikovano `apps/products/urls.py:7,10`); placeholder view se zamenjuje (vidi Repository delta tabelu)
- **When** menjam `apps/products/views.py` da uvozi `ProductDetailView` CBV (DetailView naslednik) i `apps/products/urls.py` menja `views.placeholder_view` → `views.ProductDetailView.as_view()` (1-line EDIT, pattern + namespace + URL name `detail` se NE menjaju)
- **Then**:
  - `reverse("products:detail", kwargs={"slug": "agri-tracking-tb804"})` vraća `/sr/proizvod/agri-tracking-tb804/` kad je aktivan locale `sr` (i analogno `/hu/proizvod/...`, `/en/proizvod/...`)
  - GET `/sr/proizvod/agri-tracking-tb804/` vraća HTTP 200 ako Product sa `slug="agri-tracking-tb804"` postoji u DB i `is_published=True`
  - GET `/sr/proizvod/agri-tracking-tb804/` vraća HTTP 404 ako Product postoji ali `is_published=False` (per Decision SM-D3 — `get_queryset()` filtruje `is_published=True` da neobjavljeni proizvodi nisu javno dostupni)
  - GET `/sr/proizvod/nepostojeci/` vraća HTTP 404
  - GET `/sr/proizvod/agri-tracking-tb804` (bez trailing slash) → Django `APPEND_SLASH` redirektuje na sa-slash varijantu
- **And** URL name `detail` matches `Product.get_absolute_url()` iz Story 2.2 (koji vraća `reverse("products:detail", kwargs={"slug": self.slug})` — live verifikovano `apps/products/models.py:269-270`). **NIKAKAV edit na `apps/products/models.py` nije potreban** — URL pattern koristi default `DetailView` `slug_url_kwarg = "slug"` i `slug_field = "slug"` (Django defaults). Vidi SM-D2.
- **And** smoke verifikacija: `uv run python manage.py check` exit code 0. URL reverse provera kroz stock Django shell:
  ```bash
  uv run python manage.py shell -c "from django.urls import reverse; \
    from django.utils.translation import activate; activate('sr'); \
    print(reverse('products:detail', kwargs={'slug': 'agri-tracking-tb804'}))"
  ```
  Očekivan output: `/sr/proizvod/agri-tracking-tb804/`
- **And** Query plan (Django Debug Toolbar smoke + `django_assert_num_queries(7)` exact-match test per SM-D21): **TAČNO 7 SQL upita** za pun render strane (kompletno popunjen proizvod sa svim podsekcijama). Verifikovano empirijski u Subtask 1.5(d) PRE TEA RED-phase per SM-D21+D28 — empirical literal je locked u AC1+AC2+test signature PRE pisanja testa (eliminisan "moving-target" test contract). Ako empirijska verifikacija u Subtask 1.5 pokaže drugačiji broj (6 ili 8 zbog Django ORM nuanse), spec mutation se izvršava u Subtask 1.5 phase (PRE TEA RED-phase), NE u Subtask 12 ili kasnije. Exact-match je strožiji guard od upper-bound (sakriva N+1 regresije). Enumeracija:
  1. Product (DetailView get_object — `SELECT * FROM products_product WHERE slug = ... AND is_published = TRUE` sa `select_related("brand", "series", "subcategory")`)
  2. ProductImage prefetch (`SELECT * FROM products_productimage WHERE product_id = ... ORDER BY order, id`)
  3. ProductVariant prefetch (`SELECT * FROM products_productvariant WHERE product_id = ... ORDER BY order, id`)
  4. ProductSpecification prefetch (`SELECT *, Case/When section_rank, section_label FROM products_productspecification WHERE product_id = ... ORDER BY section_rank, order, id`)
  5. ProductBrochure prefetch (`SELECT * FROM products_productbrochure WHERE product_id = ... ORDER BY id`)
  6. ProductTestimonial prefetch (`SELECT * FROM products_producttestimonial WHERE product_id = ... ORDER BY order, -created_at`)
  7. ProductSimilar resolution (`SELECT * FROM products_productsimilar JOIN products_product ... WHERE product_id = ... ORDER BY order, id LIMIT 4` — manual override path) ILI auto fallback (`SELECT * FROM products_product WHERE brand_id = ... AND series_id = ... AND is_published = TRUE AND id != ... ORDER BY -created_at LIMIT 4` — vidi AC6)
  - **NEMA N+1** — iteriranje partials u template-u NE pravi dodatne query-je (sve cached kroz select_related/prefetch_related).

**AC2 — `ProductDetailView` (CBV `DetailView`) sa locale-aware Case/When section_rank + section_label per-request (SM-D14/D20 reuse pattern; locale-aware Case/When MORA biti per-request); context sadrži ključeve `product` (sa prefetched relations), `similar_products` (FR-20 resolved manual ili auto), `similar_source` (debug/analytics flag), `brochures_list` (view-pre-computed entries sa defensive size_bytes — vidi SM-D26 + I8); NEMA odvojenih ključeva `gallery_images`/`variants`/`specifications`/`testimonials` — accessuju se kroz `product.<relation>.all`. View koristi SAMO `is_published=True` kao public-visibility gate (per SM-D20 — `status` TextChoices je admin-only metadata, NE javni gate).**

- **Given** AC1; Product modeli iz Story 2.2 (sa svim related-name relacijama: `images`, `variants`, `specifications`, `brochures`, `testimonials`, `outgoing_similars`); Story 2.6 BrandDetailView SM-D14/D20 pattern za locale-aware Case/When (REUSE bez extract — vidi SM-D5 za REFACTOR-candidate note)
- **When** definišem `apps/products/views.py`:
  ```python
  """Product detail strana — Story 2.7 (Epic 2 Public Catalog).

  Zamenjuje Story 2.6 placeholder_view sa ProductDetailView CBV-om.
  Server-side rendering; HTMX form submit (Story 4.3 model inquiry)
  je out-of-scope. Query optimizacija: select_related za brand/series/
  subcategory; prefetch_related za images, variants, specifications,
  brochures, testimonials. ProductSpecification queryset koristi
  Case/When annotation za section_rank (display order Motor → Transmisija →
  Hidraulika → Ostalo) i section_label (translated label za {% regroup %}
  grouper) — REUSE Story 2.6 BrandDetailView pattern (per-request
  konstruisano, SM-D14/D20 lokal-aware).

  Similar products (FR-20 hibrid): manual `product.outgoing_similars.all()`
  ako nije prazan; inače auto fallback po istom brendu + seriji
  (deterministic -created_at order za cache stability — SM-D3).
  """

  from __future__ import annotations

  from django.core.exceptions import SuspiciousFileOperation
  from django.db.models import Case, CharField, IntegerField, Prefetch, Value, When
  from django.utils.translation import gettext_lazy as _
  from django.views.generic import DetailView

  from apps.products.models import (
      Product,
      ProductImage,
      ProductSpecification,
      ProductVariant,
      ProductBrochure,
      ProductTestimonial,
      ProductSimilar,
  )

  _SIMILAR_PRODUCTS_LIMIT = 4


  class ProductDetailView(DetailView):
      model = Product
      context_object_name = "product"
      template_name = "products/product_detail.html"
      # slug_url_kwarg = "slug" + slug_field = "slug" su Django defaults

      def get_queryset(self):
          # KRITIČNO (SM-D14/D20 reuse): Case/When sa Value(str(_("..."))) MORA biti
          # definisan UNUTAR get_queryset() (per-request), NE na module-level.
          # str(_(...)) eager-coerce gettext_lazy proxy u koncretan string AT REQUEST TIME
          # (LocaleMiddleware je aktivirao current lang pre poziva), izbegavajući
          # `psycopg.ProgrammingError: cannot adapt type '__proxy__'` (Story 2.6
          # Completion Notes § Implementation choices worth noting).
          # Display order: Motor → Transmisija → Hidraulika → Ostalo (Story 2.2 NOTE I3).
          section_order = Case(
              When(section="motor", then=Value(1)),
              When(section="transmisija", then=Value(2)),
              When(section="hidraulika", then=Value(3)),
              When(section="ostalo", then=Value(4)),
              default=Value(99),
              output_field=IntegerField(),
          )
          section_label = Case(
              When(section="motor", then=Value(str(_("Motor")))),
              When(section="transmisija", then=Value(str(_("Transmisija")))),
              When(section="hidraulika", then=Value(str(_("Hidraulika")))),
              When(section="ostalo", then=Value(str(_("Ostalo")))),
              default=Value(str(_("Ostalo"))),
              output_field=CharField(),
          )
          specs_qs = ProductSpecification.objects.annotate(
              section_rank=section_order,
              section_label=section_label,
          ).order_by("section_rank", "order", "id")

          images_qs = ProductImage.objects.order_by("order", "id")
          variants_qs = ProductVariant.objects.order_by("order", "id")
          brochures_qs = ProductBrochure.objects.order_by("id")
          testimonials_qs = ProductTestimonial.objects.order_by("order", "-created_at")

          return (
              Product.objects.filter(is_published=True)
              .select_related("brand", "series", "subcategory")
              .prefetch_related(
                  Prefetch("images", queryset=images_qs),
                  Prefetch("variants", queryset=variants_qs),
                  Prefetch("specifications", queryset=specs_qs),
                  Prefetch("brochures", queryset=brochures_qs),
                  Prefetch("testimonials", queryset=testimonials_qs),
              )
          )

      def get_context_data(self, **kwargs):
          ctx = super().get_context_data(**kwargs)
          product = self.object
          # FR-20 hibrid: manual ProductSimilar override > auto same-brand+series fallback.
          # SM-D19: is_published=True filter MORA biti SQL-level WHERE clause na queryset-u,
          # NE Python post-filter na sliced rezultatu. Python filter posle slice-a daje
          # invalid count (npr. admin uneo 4 manual similars od kojih 2 unpublished →
          # rezultanta lista ima 2 entries (truthy) → auto fallback ne fire-uje → korisnik
          # vidi 2 kartice umesto očekivanih 4). SQL filter respektuje FR-20 admin-override
          # semantiku ("admin override u celini zamenjuje automatske predloge" → ako admin
          # nije obezbedio dovoljno PUBLISHED similars za slice, rezultat je manji od 4
          # ali još uvek "manual" path; auto fallback fire-uje SAMO ako manual_list je
          # potpuno prazan — što je ispravan signal "no admin override intent").
          manual_similars = (
              ProductSimilar.objects.filter(
                  product=product,
                  related_product__is_published=True,  # SQL filter, ne Python post-filter
              )
              .select_related("related_product__brand")
              .order_by("order", "id")[:_SIMILAR_PRODUCTS_LIMIT]
          )
          manual_list = [s.related_product for s in manual_similars]
          if manual_list:
              ctx["similar_products"] = manual_list
              ctx["similar_source"] = "manual"
          else:
              # Auto fallback: isti brand + ista serija (ako postoji), exclude trenutni,
              # deterministic order -created_at (cache stability + sortable; random
              # order bi pravio cache-bust po request-u — SM-D3).
              auto_qs = Product.objects.filter(
                  brand=product.brand,
                  is_published=True,
              ).exclude(pk=product.pk)
              if product.series_id:
                  auto_qs = auto_qs.filter(series=product.series)
              ctx["similar_products"] = list(
                  auto_qs.select_related("brand").order_by("-created_at")[:_SIMILAR_PRODUCTS_LIMIT]
              )
              ctx["similar_source"] = "auto" if ctx["similar_products"] else "none"

          # SM-D26 + I8 + SM Fix iter 2 I-iter2-4: Pre-compute brochure size labels view-side;
          # pdf_file.size triggeruje filesystem stat call per render i može da raise-uje 4
          # documented exception paths (+ future storage-backend-specific exceptions u Story 9.x):
          #   - FileNotFoundError: fajl nedostaje na disk-u (race condition: DB record postoji,
          #     file storage je inconsistent)
          #   - OSError: permission denied, disk corruption, file system error
          #   - ValueError: FieldFile.name je None ili unsaved instance (defensive — admin shell
          #     create() bez file upload-a)
          #   - SuspiciousFileOperation: Django storage path traversal guard (npr. fajl path
          #     pokušava ići van MEDIA_ROOT-a — security)
          # Template renderuje kroz ctx["brochures_list"] umesto product.brochures.all direktno
          # za AC7 sekciju. SM-D24/I1 cap: max 5 brochures per render (admin oversight guard).
          brochures_list = []
          for b in product.brochures.all()[:5]:
              try:
                  size_bytes = b.pdf_file.size
              except (FileNotFoundError, OSError, ValueError, SuspiciousFileOperation):
                  size_bytes = 0
                  # Opcioni soft logging za observability (Story 9-6 Django logging):
                  # logger.warning("brochure pdf_file inaccessible: pk=%s", b.pk)
              brochures_list.append({"brochure": b, "size_bytes": size_bytes})
          ctx["brochures_list"] = brochures_list

          return ctx

      # SM-D21: TAČNO 7 SQL upita per request — enumerisanih ispod (mirror AC1 enumeration).
      # NAPOMENA: query #7 broji se kao 1 čak iako manual ILI auto fallback path putanje
      # alternative su (samo jedan se exec-uje per request).
      #
      # 7 SQL upita:
      #   1) Product DetailView get_object (sa select_related brand+series+subcategory) — 1 JOIN-ed SELECT
      #   2) Prefetch ProductImage (ordered)
      #   3) Prefetch ProductVariant (ordered)
      #   4) Prefetch ProductSpecification (annotated sa Case/When + ordered)
      #   5) Prefetch ProductBrochure (ordered)
      #   6) Prefetch ProductTestimonial (ordered)
      #   7) ProductSimilar resolution (manual sa SQL is_published filter) ILI auto fallback
      #      (Product.objects.filter(...) — alternative, samo 1 putanja se exec-uje per request)
  ```
- **Then**:
  - Context sadrži ključeve:
    - `product` (Product instance sa prefetched `images`, `variants`, `specifications`, `brochures`, `testimonials`)
    - `similar_products` (lista do 4 Product instance-a; može biti prazna lista ako ni manual ni auto ne daju rezultate)
    - `similar_source` (string: `"manual"` / `"auto"` / `"none"` — za debug log + opciono za template eyebrow text variant)
    - `brochures_list` (lista do 5 dict entries `{"brochure": ProductBrochure, "size_bytes": int}`; defensive size pre-compute sa try/except guard per SM-D26 + I8; cap 5 per SM-D24/I1)
  - Template pristupa: galerija/specs/testimonijali/variants kroz `product.images.all` / `product.specifications.all` / `product.testimonials.all` / `product.variants.all` (sve cached kroz Prefetch); **brošure pristupaju se kroz `brochures_list` (ne `product.brochures.all`)** jer view-layer je pre-computed size_bytes; testimonials slider partial dobija `testimonials=product.testimonials.all` kroz eksplicitni `{% include ... with %}` per SM-D22.
  - **NEMA** odvojenih ključeva `gallery_images`, `variants`, `specifications`, `testimonials` u context-u (mirror Story 2.6 SM-D — sve podliste se accessuju kroz `product.<relation>.all` da minimizuje context surface; **brochures_list je izuzetak** jer view-layer pre-computation je potrebna za defensive size handling).
- **And** view koristi default Django `DetailView` `slug_url_kwarg = "slug"` i `slug_field = "slug"` (NIJE override-ovano) da matchuje URL pattern `proizvod/<slug:slug>/`.
- **And** view NE oslobađa eksplicitno `request.user` (anonimni view, javni katalog) — `LoginRequiredMixin` se NE koristi.
- **And** ako proizvod nema slika (`product.images.exists() == False`), galerija sekcija SE NE renderuje (vidi AC3 § hidden empty sections). Ako nema specifications, akordion SE NE renderuje. Ako nema brochures, brošure card SE NE renderuje. Ako nema variants, variant selektor SE NE renderuje. Ako nema testimonijala, slider SE NE renderuje. Ako nema similar_products, sekcija SE NE renderuje. Sve empty-state hide-ovi su template-side `{% if ... %}` guard-ovi.

**AC3 — `templates/products/product_detail.html` renderuje sekcije TAČNIM redosledom: hero overlay → opis → galerija → akordion specs → brošura card → slični modeli (sa Wave Divider iznad) → testimonijali → variants (ako postoje); sve sekcije semantičke HTML5 (`<article>` outer wrapper, `<section aria-labelledby>` per sub-section, `<aside>` za brošure card); JEDAN `<h1>` na strani (delegated kroz `hero_overlay_card.html` partial — B1 fix iz Story 2.6)**

- **Given** AC1 + AC2 završeni; Story 1.7 partials (`hero_overlay_card.html`, `repeating_element.html`, `wave_divider.html`, `section_eyebrow.html`) site-wide dostupni; Story 2.5 GLightbox vendor + init JS site-wide
- **When** kreiram `templates/products/product_detail.html`
- **Then** template MORA:
  - `{% extends "base.html" %}` + `{% load i18n static media_tags %}`
  - `{% block title %}{{ product.name }} | {{ product.brand.name }} | {% translate "Ćorić Agrar" %}{% endblock %}`
  - `{% block meta_description %}{{ product.description|truncatewords:25 }}{% endblock %}`
  - `{% block content %}` sadrži **outer `<article class="coric-product-detail" data-testid="product-detail-page">`** wrapper (NE drugi `<main>` — base.html već renderuje `<main id="main-content">` per Story 2.6 nested-main guard B1 fix). **Eksplicitna verifikacija (I7 regression guard):** `<article>` MORA sedeti UNUTAR `{% block content %}` koji se renderuje INSIDE `<main id="main-content">` u base.html — NE replace-uje `<main>`. Test za EXACTLY 1 `<main>` element na rendered output (mirror Story 2.6 B1 fix) — vidi Subtask 12.3 AC3 test `test_product_detail_has_single_main_element`. Unutar `<article>` sekcije idu TAČNIM redosledom:
    1. **Hero overlay sekcija** (`<section id="product-hero" aria-labelledby="product-hero-title">`) — include `templates/products/partials/_hero_section.html`. Hero card prima:
       - `title` = `product.name` (renderuje se kao `<h1>` unutar `hero_overlay_card.html` per Story 1.7 — **JEDINI `<h1>` na strani**, B1 fix reuse iz Story 2.6 iter 1)
       - `bullets` = `product.key_features|slice:":3"` (lista do 3 stringa; render-uje se kao `<ul>` ako nije prazno; ako je prazno, `hero_overlay_card.html` skroz preskače `<ul>` — verify per Story 1.7 partial source)
       - `brand_logo` = `product.brand.logo.url` ako postoji; `brand_logo_alt` = `product.brand.name`
       - `variant` = mapiranje `product.brand.brand_color` na repeating_element variant (REUSE iz Story 2.6 SM-D11 — `"blue"` ako brand_color je `"#00a4e9"` (Jeegee, case-insensitive); else `"green"` default)
    2. **Opis proizvoda sekcija** (`<section id="product-description" aria-labelledby="product-description-title" class="coric-product-description">`) — render SAMO ako `product.description` nije prazan; include `_description.html`:
       ```django
       {% if product.description %}
         {% include "products/partials/_description.html" %}
       {% endif %}
       ```
    3. **Galerija karusel sekcija** (`<section id="product-gallery" aria-labelledby="product-gallery-title" class="coric-product-gallery">`) — render SAMO ako `product.images.all` nije prazno:
       ```django
       {% if product.images.all %}
         {% include "products/partials/_gallery_carousel.html" %}
       {% endif %}
       ```
    4. **Akordion specifikacija sekcija** (`<section id="product-specs" aria-labelledby="product-specs-title" class="coric-product-specs">`) — render SAMO ako `product.specifications.all` nije prazno:
       ```django
       {% if product.specifications.all %}
         {% include "products/partials/_specs_accordion.html" %}
       {% endif %}
       ```
    5. **Brošura sekcija** — wrapped u `<aside class="coric-product-brochure-wrap" aria-labelledby="product-brochure-title">` (semantic `<aside>` jer brošura je periferna ali povezana sadržajem) — render SAMO ako `brochures_list` nije prazna lista (view-level pre-computed iz `product.brochures.all()[:5]` per SM-D24 + SM-D26):
       ```django
       {% if brochures_list %}
         <aside class="coric-product-brochure-wrap" aria-labelledby="product-brochure-title">
           {% include "products/partials/_brochure_card.html" %}
         </aside>
       {% endif %}
       ```
    6. **Slični modeli sekcija** (`<section id="product-similar" aria-labelledby="product-similar-title" class="coric-product-similar">`) — render SAMO ako `similar_products` lista nije prazna; uključuje Wave Divider iznad:
       ```django
       {% if similar_products %}
         {% include "products/partials/_similar_products.html" %}
       {% endif %}
       ```
    7. **Testimonijali slider sekcija** (`<section id="product-testimonials" aria-labelledby="product-testimonials-title" class="coric-testimonials">`) — render SAMO ako `product.testimonials.all` nije prazno. **SM Fix iter 1 + iter 2 update (C1+C6+I-iter2-2, SM-D22+D23+D27):** koristi SHARED partial iz `templates/partials/_testimonials_slider.html` (NIJE `products/partials/_testimonials.html`!) sa eksplicitnim `{% include ... with testimonials=... slider_id=... %}` context binding-om. `aria-labelledby` referencira story-specific `id="product-testimonials-title"` (NE generic `testimonials-title` ni `brand-testimonials-title`) jer shared partial prima `slider_id` kwarg per SM-D27 future-collision guard:
       ```django
       {% if product.testimonials.all %}
         {% include "partials/_testimonials_slider.html" with testimonials=product.testimonials.all slider_id="product-testimonials-title" %}
       {% endif %}
       ```
    8. **Variants selektor sekcija** (`<section id="product-variants" aria-labelledby="product-variants-title" class="coric-product-variants">`) — render SAMO ako `product.variants.all` nije prazno:
       ```django
       {% if product.variants.all %}
         {% include "products/partials/_variants_selector.html" %}
       {% endif %}
       ```
    9. **Story 4.3 extension tačka** (placeholder za buduću model inquiry formu):
       ```django
       {% block product_detail_inquiry %}{% endblock %}
       ```
       Story 4.3 implementira ovaj block u svom create-story koraku; Story 2.7 ostavlja prazan.
  - `<article>` MORA imati `data-testid="product-detail-page"` (Playwright Story 9.8 hook)
  - **NEMA inline `style="..."`** atributa bilo gde u template-u — sve stilizovanje kroz `coric-*` BEM klase
  - **NEMA hardcoded srpski string** — sve labels prolaze kroz `{% translate %}` ili `{% blocktranslate %}`
  - **TAČNO JEDAN `<h1>`** na strani — proverava se sa BeautifulSoup parse u testu (Subtask 10.6 — mirror Story 2.6 T1 test pattern)

**AC4 — Galerija karusel partial (`_gallery_carousel.html`) renderuje slike kroz `{% responsive_picture %}` (srcset 400w/800w/1600w sa `loading="lazy"`); svaka slika je `<a class="glightbox" data-gallery="product-{{ product.slug }}">` koja triggeruje GLightbox modal (Story 2.5 integration); markup poštuje `<picture>` semantiku za responsive images**

- **Given** AC3 završen; Story 2.3 `{% responsive_picture %}` template tag; Story 2.5 GLightbox auto-pickup po `.glightbox` selektoru + `coric:lightbox-open/close` event kontrakt
- **When** kreiram `templates/products/partials/_gallery_carousel.html`
- **Then** partial MORA:
  - `{% load i18n media_tags %}` u header-u
  - Section Eyebrow header: `{% include "partials/section_eyebrow.html" with text=_("GALERIJA") tag="div" %}`
  - Skriveni heading (a11y landmark name): `<h2 id="product-gallery-title" class="visually-hidden">{% translate "Galerija slika" %}</h2>`
  - Galerija container sa CSS Grid (desktop) ili horizontal scroll-snap (mobile) — vidi SM-D6 za carousel-vs-CSS-only decision. Pretpostavlja CSS-only scroll-snap u v1 (decision SM-D6 favoring pure CSS):
    ```django
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
  - **GLightbox integration:** `class="glightbox"` + `data-gallery="product-{{ product.slug }}"` su Story 2.5 kontrakt — GLightbox auto-pickup po `.glightbox` selektoru (Story 2.5 `lightbox-init.js` AC2 source), `data-gallery` grupiše slike u jedan modal sa prev/next navigacijom unutar Lightbox-a; `data-glightbox="title: ..."` postavlja caption u Lightbox toolbar-u.
  - **Slike SVE imaju `loading="lazy"`** — galerija je ispod hero + opisa sekcije, nijedna slika nije above-the-fold (mirror Story 2.6 SM-D13).
  - `data-testid` atributi: `product-gallery-grid` na wrapper-u, `gallery-item-{N}` na svakoj slici (za Playwright).
- **And** `responsive_picture` MORA proslediti `alt` parametar (image.alt_text ili fallback product.name) — a11y must-have iz project-context.md § A11y must-haves linija 727.
- **And** **NEMA `format='PNG'`** na product gallery slikama (per Story 2.6 § Brand logo PNG policy — galerija product slika su JPEG fotografije bez transparency-ja; `format='PNG'` se primenjuje SAMO na brand.logo render).

**AC5 — Akordion specifikacija partial (`_specs_accordion.html`) renderuje specs grupisane po `section_label` annotation (Motor → Transmisija → Hidraulika → Ostalo per AC2 Case/When); prva sekcija (Motor) je `<details open>`, ostale zatvorene; prazne sekcije se automatski skroz preskaču kroz `regroup`; `+/-` toggle ikona; akordion native HTML `<details>/<summary>` (keyboard-accessible besplatno); poštuje `prefers-reduced-motion: reduce`**

- **Given** AC2 završen (view-layer Case/When section_rank + section_label annotation); AC3 § sekcija 4 (akordion sekcija) registrovan; Story 2.6 `_series_extended.html` (live verifikovano) je kanonski pattern za isti markup u brand listing strani
- **When** kreiram `templates/products/partials/_specs_accordion.html`
- **Then** partial MORA:
  - `{% load i18n %}` u header-u
  - Section Eyebrow: `{% include "partials/section_eyebrow.html" with text=_("SPECIFIKACIJE") tag="div" %}`
  - Skriveni heading: `<h2 id="product-specs-title" class="visually-hidden">{% translate "Tehničke specifikacije" %}</h2>`
  - `{% regroup product.specifications.all by section_label as spec_sections %}` (NAPOMENA: `section_label` je view-layer annotation iz AC2 Case/When — translated label tačno odgovara aktivnoj lokali; `{% regroup %}` koristi `section_label` kao grouper, NE raw `section` TextChoices value)
  - Per-section render:
    ```django
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
              <tr>
                <th scope="row">{{ spec.key }}</th>
                <td>{{ spec.value }}</td>
              </tr>
            {% endfor %}
          </tbody>
        </table>
      </details>
    {% endfor %}
    ```
  - **`<details open>` na PRVOJ sekciji** kroz `{% if forloop.first %}open{% endif %}` — pošto je queryset sorted po `section_rank` (Motor=1, Transmisija=2, Hidraulika=3, Ostalo=4), Motor sekcija je uvek prva, pouzdano dobija `open` atribut.
  - **`+/-` toggle ikona** kroz CSS `details[open] > summary > .coric-product-specs__accordion-icon::after { content: "−"; }` ili sličan pseudo-element pattern (`+` default state; `−` (en-dash) open state). Implementacija u `product-detail.css`.
  - **Prazne sekcije se automatski skip-uju** — `{% regroup %}` ne renderuje group ako nema items; ako Product ima specs samo u sekciji „motor" i „ostalo", samo 2 `<details>` se renderuju (transmisija + hidraulika su skipped jer su prazne na DB nivou — vidi AC2 query SQL).
  - `data-testid="spec-section-{slugified-label}"` na svakom `<details>` — Story 2.6 pattern.
- **And** akordion mora biti **keyboard-accessible** (native `<details>/<summary>` to garantuje besplatno — Enter/Space na `<summary>` toggle-uje sekciju per HTML5 spec).
- **And** akordion mora respektovati `prefers-reduced-motion: reduce` — CSS animacija toggle-a (open/close transition na content area) se onemogućava (`@media (prefers-reduced-motion: reduce) { .coric-product-specs__accordion[open] { transition: none !important; } }`) u `product-detail.css`.
- **And — locale verifikacija:** mirror Story 2.6 hu-locale test (Subtask 10.4 SM-D20 plan); render `product_detail.html` pod `LANGUAGE_CODE='hu'` sa fixture proizvodom koji ima specs iz svih 4 sekcija; asertovati da `<summary>` elementi sadrže hu-locale prevode (npr. "Hajtómű" za "Transmisija" prema `locale/hu/LC_MESSAGES/django.po`). Test je `xfail` ako hu prevodi za 4 sekcijska label-a još uvek nisu populated u .po fajlu (live status verify pre Subtask 10.7 — mirror Story 2.6 xfail handling).

**AC6 — Slični modeli sekcija (`_similar_products.html`) renderuje 2-4 kartice (FR-20 hibrid: manual `ProductSimilar` ako postoji, inače auto fallback po istom brendu+seriji deterministic `-created_at` order); kartice reuse-uju `coric-product-card` BEM komponentu iz Story 2.6; Wave Divider iznad sekcije**

- **Given** AC2 završen (`similar_products` resolved u context-u sa FR-20 hibrid logikom); AC3 § sekcija 6 (slični modeli sa Wave Divider top); `coric-product-card` BEM iz `static/css/components/brand-listing.css` (Story 2.6 deliverable, site-wide loaded); PRD § 4.4 FR-20 spec: „Podrazumevani izvor: automatski izbor 2-4 modela iz iste serije ili istog brenda; Admin može u proizvodu ručno da označi listu sličnih modela; admin override u celini zamenjuje automatske predloge"
- **When** kreiram `templates/products/partials/_similar_products.html`
- **Then** partial MORA:
  - `{% load i18n media_tags %}`
  - Wave Divider iznad sekcije: `{% include "partials/wave_divider.html" with position="top" %}`
  - Section Eyebrow: `{% include "partials/section_eyebrow.html" with text=_("SLIČNI MODELI") tag="div" %}`
  - Visible heading: `<h2 id="product-similar-title" class="coric-product-similar__title">{% translate "Možda će vas zanimati i" %}</h2>` (NE skriveni — heading je vidljiv za UX clarity; razlika od Galerije gde je heading skriveni jer Section Eyebrow već signalizuje)
  - Kartice grid (max 4 entries — view limituje na 4):
    ```django
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
  - **Linkable card pattern** sa nested-interactive guard (mirror Story 2.6 AC4): `<a>` obavija celu karticu, `aria-label="{{ sim.name }}"`, CTA je `<span aria-hidden="true">` (NE `<a>` ili `<button>` — nested interactive violation per WCAG 2.1 SC 4.1.2).
  - `data-testid="similar-product-card-{slug}"` per kartica.
- **And** view-layer FR-20 logika (vidi AC2 `get_context_data` source):
  - **Manual override path:** ako `ProductSimilar.objects.filter(product=current_product, related_product__is_published=True)...[:4]` (SQL-level published filter per SM Fix iter 1 C3/SM-D19) ima ≥1 entry, koristi te (do 4).
  - **Auto fallback path:** ako manual je prazan, query `Product.objects.filter(brand=self.object.brand, is_published=True).exclude(pk=self.object.pk)`; ako `self.object.series_id` postoji, dodaj `.filter(series=self.object.series)` da uže filtruje; order `-created_at` (deterministic — SM-D3 cache stability rationale: random order bi pravio cache-bust po request-u); limit 4.
  - **Empty state:** ako ni manual ni auto ne daju rezultate, sekcija SE NE renderuje (`{% if similar_products %}` u product_detail.html).
- **And** `similar_source` context flag (`"manual"` / `"auto"` / `"none"`) je dostupan za buduće analytics ili debug logging — Story 2.7 NE renderuje u UI (Story 9.x analytics može hook-ovati).

**AC7 — Brošura card partial (`_brochure_card.html`) renderuje `responsive_picture entry.brochure.cover_thumbnail_image` (Story 2.4 auto-gen, sa defensive `.name` guard per SM-D26/I9) + naslov + file-size labela („X.X MB, PDF") sa view-pre-computed `entry.size_bytes` (SM-D26/I8 defensive size handling) + direktan `<a>` PDF download CTA (`target="_blank" rel="noopener noreferrer" download`); render-uje SAMO ako `brochures_list` nije prazna; pluralizovan heading per SM-D24/I1 (`{% blocktranslate count %}` "Preuzmite brošuru"/"Preuzmite brošure"); cap MAX 5 brochures per SM-D24/I1 (view-layer slice); "PDF" acronym kroz `{% translate %}` per SM-D25/I3 policy compliance**

- **Given** AC3 § sekcija 5 (`<aside>` wrapper); Story 2.4 deliverable `ProductBrochure.cover_thumbnail_image` (auto-gen post_save signal iz `pdf_utils.generate_brochure_cover_thumbnail`); Story 1.7 `pill_button.html` partial **NE PODRŽAVA** `target`/`rel`/`download` kwarg-e (per Story 2.6 SM-D22 — direct anchor pattern je obavezan za PDF download CTA-jeve); Python `os.path.getsize` ili Django FileField `size` attribute za file-size izračunavanje
- **When** kreiram `templates/products/partials/_brochure_card.html`
- **Then** partial MORA:
  - `{% load i18n media_tags %}`
  - Section Eyebrow: `{% include "partials/section_eyebrow.html" with text=_("BROŠURE") tag="div" %}`
  - Pluralized heading (SM-D24/I1 — singular "brošuru" je gramatički netačan za N>1):
    ```django
    <h2 id="product-brochure-title" class="coric-product-brochure__title">
      {% blocktranslate count counter=brochures_list|length %}Preuzmite brošuru{% plural %}Preuzmite brošure{% endblocktranslate %}
    </h2>
    ```
  - Loop kroz `brochures_list` (view-pre-computed, capped @ 5 per SM-D24; per-entry render):
    ```django
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
            <p class="coric-product-brochure__size">
              {{ entry.size_bytes|filesizeformat }}, {% translate "PDF" %}
            </p>
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
  - **`{{ entry.size_bytes|filesizeformat }}`** Django built-in `filesizeformat` filter primenjuje se na view-layer pre-computed `size_bytes` int (per SM-D26/I8 — sirovi `pdf_file.size` triggeruje filesystem stat call koji raise-uje FileNotFoundError ako fajl nedostaje); vraća human-readable string ("2.4 MB", "850 KB") sa lokalizovanim decimal separator-om (sr koristi tačku kao decimal separator u v1 — verifikuj lokalizaciju u testu; ako ne odgovara, override sa custom filter u Story 9-10 polish). Ako `size_bytes=0` (file missing edge case), prikazuje "0 bytes" — graceful degradation.
  - **Direktan `<a>` markup (NE `pill_button.html` partial)** sa atributima `target="_blank"`, `rel="noopener noreferrer"`, `download`, `class="coric-button coric-button--primary"` — TAČAN mirror Story 2.6 SM-D22 + AC3 § Preuzmi katalog CTA pattern (Story 1.7 pill_button NE PODRŽAVA ove atribute; modifikacija partial-a je out-of-scope).
  - `data-testid="brochure-card-{id}"` per card + `data-testid="brochure-download-{id}"` per CTA — Playwright hook.
- **And** cover thumbnail render-uje SAMO ako `entry.brochure.cover_thumbnail_image and entry.brochure.cover_thumbnail_image.name` (SM-D26/I9 defensive — ImageField sa praznim `.name=""` može biti truthy u edge case partial-state record-a; double guard sprečava broken `<img>` render).
- **And** ako proizvod NEMA brošure (`brochures_list` je prazna lista jer `product.brochures.all()[:5]` daje 0 entries), CELA `<aside>` sekcija u product_detail.html SE NE renderuje (per AC3 § sekcija 5 `{% if brochures_list %}` guard).
- **And — `responsive_picture` ZA brošure cover NE koristi `format='PNG'`** (per Story 2.6 § Brand logo PNG policy — cover thumbnail je JPEG fotografija renderovan iz PDF cover-a, no transparency).

**AC8 — Variant selektor partial (`_variants_selector.html`) renderuje SAMO ako `product.variants.exists()`; kartice su `<a class="glightbox" data-gallery="product-{{ product.slug }}-variants" href="{{ variant.image.url }}">`; klik otvara GLightbox zoom slike — **bez state change, bez URL change, bez form submita** (per PRD FR-48 spec); poštuje `coric:lightbox-open` event (testimonijal slider auto-advance se pauzira). `data-gallery` slug-scoped per Story 2-5 interface contract (forward-compat sa Story 3.1 Home koji bi mogao renderovati više proizvoda sa varijantama).**

- **Given** AC3 § sekcija 8 (variants); PRD § 4.5 FR-48 spec: „Klik na karticu varijante otvara Lightbox sa zoom slikom (čista vizuelna inspekcija, bez sporednih efekata — ne menja stanje stranice i ne pokreće formu)"; `ProductVariant` model iz Story 2.2 (verifikovano live `apps/products/models.py:315-358`) ima polja: `product`, `name`, `code` (opciono), `image` (opciono), `description` (opciono), `order`; Story 2.5 GLightbox grupisanje kroz `data-gallery` atribut
- **When** kreiram `templates/products/partials/_variants_selector.html`
- **Then** partial MORA:
  - `{% load i18n media_tags %}`
  - Section Eyebrow: `{% include "partials/section_eyebrow.html" with text=_("VARIJANTE") tag="div" %}`
  - Heading: `<h2 id="product-variants-title" class="coric-product-variants__title">{% translate "Varijante proizvoda" %}</h2>`
  - Description: `<p class="coric-product-variants__intro">{% translate "Kliknite na varijantu za uvećani prikaz slike." %}</p>` (UX hint za korisnika — varijante su informativne, klik zoom-uje sliku, ne menja state)
  - Kartice grid (1-4 per row responzivno):
    ```django
    <div class="coric-product-variants__grid" data-testid="product-variants-grid">
      {% for variant in product.variants.all %}
        {% if variant.image %}
          <a class="glightbox coric-product-variants__card"
             data-gallery="product-{{ product.slug }}-variants"
             href="{{ variant.image.url }}"
             data-glightbox="title: {{ variant.name }};{% if variant.code %} description: {% translate 'Kod' %}: {{ variant.code }};{% endif %}"
             data-testid="variant-card-{{ variant.id }}"
             aria-label="{% blocktranslate with name=variant.name %}Otvori uvećani prikaz: {{ name }}{% endblocktranslate %}">
            <div class="coric-product-variants__image">
              {% responsive_picture variant.image alt=variant.name sizes="(max-width: 768px) 100vw, 25vw" loading="lazy" css_class="coric-product-variants__img" %}
            </div>
            <div class="coric-product-variants__body">
              <h3 class="coric-product-variants__name">{{ variant.name }}</h3>
              {% if variant.code %}
                <p class="coric-product-variants__code">{% translate "Kod" %}: {{ variant.code }}</p>
              {% endif %}
              {% if variant.description %}
                <p class="coric-product-variants__desc">{{ variant.description|truncatewords:20 }}</p>
              {% endif %}
            </div>
          </a>
        {% else %}
          {# Varijanta bez slike — render bez GLightbox link-a (anti-pattern bi bilo
             linkovati ka praznom URL-u); samo info card bez interakcije. #}
          <div class="coric-product-variants__card coric-product-variants__card--no-image"
               data-testid="variant-card-{{ variant.id }}">
            <div class="coric-product-variants__body">
              <h3 class="coric-product-variants__name">{{ variant.name }}</h3>
              {% if variant.code %}
                <p class="coric-product-variants__code">{% translate "Kod" %}: {{ variant.code }}</p>
              {% endif %}
              {% if variant.description %}
                <p class="coric-product-variants__desc">{{ variant.description }}</p>
              {% endif %}
            </div>
          </div>
        {% endif %}
      {% endfor %}
    </div>
    ```
  - **GLightbox integration:** `class="glightbox"` + `data-gallery="product-{{ product.slug }}-variants"` (RAZLIČIT `data-gallery` ID od `product-{{ product.slug }}` u AC4 main galeriji — sprečava clash gde bi prev/next u Lightbox-u prelazio između main galerije i variant kartica; slug-scope per Story 2-5 contract); `data-glightbox` postavlja caption sa naziv + kod.
  - **NO STATE CHANGE — pure visual zoom** (FR-48): NEMA `data-variant-id` JS hook-a, NEMA forme/select-a, NEMA URL fragment-a (`#variant-1` itd.). Klik = otvara Lightbox = zatvara se = strana ostaje identična. Verifikuje se u testu (Subtask 10.8).
  - **`aria-label`** na `<a>` jasno najavi cilj klika („Otvori uvećani prikaz: {variant.name}") — bez toga screen reader bi rekao samo konkatenaciju vidljivog teksta, što je manje informativno.
  - `data-testid="variant-card-{id}"` per card.
- **And** ako variant nema sliku (`variant.image` je null), kartica render-uje plain info bez GLightbox link-a (defensive — varijanta sa samo nazivom + kodom + opisom, no zoom interaction). Editor admin može dodati sliku kasnije (Story 8.6 ProductVariant admin scope).
- **And** Story 2.5 `lightbox-init.js` dispatch-uje `coric:lightbox-open` na window kad se modal otvori; `testimonials-slider.js` (Story 2.6, site-wide) sluša ovaj event i pauzira auto-advance — verifikuje se kao part of AC9 manual smoke test (Lightbox otvori sa product variants → testimonials slider auto-advance se zaustavlja → Lightbox zatvori → auto-advance resume-uje).

**AC9 — Manuelni Dev smoke check + Lighthouse a11y skor ≥ 95 na lokalnoj instanci; manuelna verifikacija `prefers-reduced-motion`; Lighthouse JSON artifact preservation za Story 9.9 audit-gate alignment**

- **Given** AC1-AC8 završeni; sample seed podaci postoje u DB za bar 1 published Product sa svim opcijama: main_image, key_features (3 entries), description, 4+ ProductImage entries, 2+ ProductVariant entries (sa images), specifications iz svih 4 sekcija (motor/transmisija/hidraulika/ostalo), 1+ ProductBrochure sa generated cover_thumbnail_image, 3+ ProductTestimonial entries, opciono 1+ ProductSimilar entry za manual override path (a takođe drugi Product u istom brendu+seriji da auto fallback test radi); manuelni AC9 mirror Story 2.6 § 9.1-9.7 pattern
- **When** Dev pokreće `just dev` (Docker Compose local) i otvara `http://localhost:8000/sr/proizvod/<seed-product-slug>/` u Chrome
- **Then** Dev verifikuje (manuelni checklist):
  - **Hero sekcija renderuje:** brand logo + naziv proizvoda kao `<h1>` (PROVERI TAČNO 1 `<h1>` kroz DevTools `$$('h1').length === 1`) + 3 bullet ključne karakteristike + Repeating Element watermark (varijanta odgovara brand_color mapping-u); responzivan na mobile (375px width)
  - **Opis sekcija renderuje** sa `linebreaks` filter aplicirano (paragrafima razdvojen tekst); empty state poštovan ako description je prazan
  - **Galerija karusel renderuje:** SVE ProductImage entries kroz `<picture>` sa srcset; klik na bilo koju sliku otvara GLightbox modal sa caption; prev/next u Lightbox-u radi (data-gallery="product-{{ product.slug }}" grupiše); Esc/click-outside zatvara modal; respektuje prefers-reduced-motion (instant open/close)
  - **Akordion specifikacija renderuje 4 sekcije** (ako sve 4 imaju specs): Motor je `<details open>` po default-u, ostale zatvorene; klik na summary toggle-uje sekciju; `+/-` ikona se menja (CSS pseudo-element); prazna sekcija ne renderuje (test: setuj product sa specs samo u 2 sekcije, reload, verifikuj 2 `<details>` ne 4)
  - **Brošure card renderuje:** cover_thumbnail_image (ako je generated kroz Story 2.4 signal) + title + size labela („X.X MB, PDF") + CTA „PREUZMI"; klik otvara PDF u novom tabu (target=_blank); test brand-ovi sa 2+ brošure → 2+ cards renderovane
  - **Slični modeli sekcija renderuje:**
    - Test manual override path: kreiraj `ProductSimilar` entry; reload; verifikuj da je *baš* taj related_product renderovan (NE auto fallback)
    - Test auto fallback path: obriši ProductSimilar; reload; verifikuj 2-4 kartice iz istog brenda + serije (deterministic `-created_at` order); klik na karticu vodi na taj product detail
    - Test empty state: izolovan proizvod (jedinstven brand+series, nema manual override) → sekcija SE NE renderuje
  - **Testimonijali slider renderuje:** mirror Story 2.6 AC9 verifikacija (pause/play, prev/next, keyboard nav, focus pause, lightbox-open pause); test scenario: klikni sliku galerije → Lightbox se otvori → slider auto-advance se pauzira (NVDA/JAWS najavi prestanak); zatvori Lightbox → auto-advance se vraća
  - **Variant selektor renderuje SAMO ako `product.variants.exists()`:**
    - Test sa variants: kartice renderuju image + name + code + description; klik na karticu otvara GLightbox zoom (data-gallery="product-variants"); state strane se NE menja (URL ostaje isti, fokus se vraća na karticu nakon zatvaranja Lightbox-a per Story 2.5 contract)
    - Test bez variants: sekcija SE NE renderuje
  - **`prefers-reduced-motion` test:** uključi `prefers-reduced-motion: reduce` u Chrome DevTools Rendering panel; reload strane; verifikuj:
    - Galerija slika: GLightbox modal je instant (no transition)
    - Akordion: instant open/close (no CSS transition)
    - Testimonials slider: nema auto-advance (samo manual prev/next radi)
    - Variant selektor: klik je instant zoom (GLightbox respect)
  - **Single h1 verifikacija:** `document.querySelectorAll('h1').length === 1` u DevTools Console — TAČNO 1 (product name, delegated kroz hero_overlay_card)
  - **Semantic HTML5 verifikacija:** `<article data-testid="product-detail-page">` outer wrapper postoji; `<section aria-labelledby="...">` per podsekcija; `<aside aria-labelledby="product-brochure-title">` za brošure
- **And** Dev pokreće Lighthouse audit u CLI mode-u (PER Story 2.6 § Lighthouse JSON artifact preservation, I-iter2-8 fix — audit-gate alignment sa Story 9.9):
  ```bash
  lighthouse http://localhost:8000/sr/proizvod/<seed-product-slug>/ \
    --output=json \
    --output-path=_bmad-output/implementation-artifacts/2-7-lighthouse-$(date +%Y%m%d).json \
    --only-categories=accessibility,performance,seo \
    --form-factor=mobile \
    --chrome-flags="--headless"
  ```
  - **Accessibility score ≥ 95** (mirror Story 2.6 AC9 — UX-DR-13 + NFR-2 + Story 9.9 audit gate)
  - **Performance score ≥ 75** (lighter target — slike su lazy-loaded ali WebP/AVIF je Story 9.10 polish; product detail strana ima više slika nego brand listing pa može biti malo niži)
  - **SEO score ≥ 90** (no broken links, sve slike imaju alt, single h1, meta description prisutan)
  - **Dev MORA citirati skor-ove u `Dev Agent Record § Completion Notes` sekciji story fajla PRE Step-04 Code Review:** "Lighthouse skor (mobile): a11y={N}, performance={M}, seo={K}; JSON artifact: `_bmad-output/implementation-artifacts/2-7-lighthouse-YYYYMMDD.json`."
  - Ako CLI lighthouse nije instaliran u dev environment-u, alternativa je Chrome DevTools Lighthouse run → Save report (JSON) → manuelno kopirati u `_bmad-output/implementation-artifacts/2-7-lighthouse-YYYYMMDD.json`.
- **Napomena:** Ovaj AC je **manuelni smoke check** koji Dev izvršava pre commit-a (mirror Story 2.6 AC9); automated E2E je Story 9.8 scope, automated a11y axe-core je Story 9.9 scope. Dev dokumentuje rezultate u `Dev Agent Record § Completion Notes`.

## Tasks / Subtasks

- [ ] **Task 1: `apps/products/views.py` REPLACE + `apps/products/urls.py` 1-line EDIT + DELETE `templates/products/_placeholder.html` (AC1, AC2)**
  - [ ] Subtask 1.1: Otvori `apps/products/views.py`; OBRIŠI `placeholder_view` FBV; dodaj `ProductDetailView(DetailView)` CBV per AC2 source code (sve Prefetch chain-ove, Case/When section_rank + section_label per-request, get_context_data sa FR-20 hibrid logikom). Verifikuj sve imports (Product, ProductImage, ProductSpecification, ProductVariant, ProductBrochure, ProductTestimonial, ProductSimilar).
  - [ ] Subtask 1.2: Otvori `apps/products/urls.py`; promeni `path("proizvod/<slug:slug>/", views.placeholder_view, name="detail"),` u `path("proizvod/<slug:slug>/", views.ProductDetailView.as_view(), name="detail"),`. `app_name = "products"` i path string ostaju identični (1-line EDIT).
  - [ ] Subtask 1.3: OBRIŠI `templates/products/_placeholder.html` (placeholder template iz Story 2.6 C8 fix — više nije potreban jer ProductDetailView render-uje stvarne template-ove).
  - [ ] Subtask 1.4 (NOVA, SM Fix iter 1 C2): OBRIŠI `apps/products/tests/test_placeholder.py` (4 testova iz Story 2.6 koji asertuju placeholder rendering — `test_placeholder_returns_http_200_with_template`, `test_placeholder_has_noindex_meta_tag`, `test_placeholder_has_single_h1`, `test_placeholder_uses_semantic_main_landmark`). **Razlog:** posle Subtask 1.1 (DELETE `placeholder_view` FBV) + Subtask 1.3 (DELETE `_placeholder.html` template), tih 4 tests će regress-ovati svi (FBV i template više ne postoje). Backup nije potreban — testovi neće više biti relevantni; replacement coverage kroz Subtask 12.1+12.2 (URL pattern sad serve-uje ProductDetailView) + Subtask 12.5 (eksplicitan deletion regression guard). TEA test count baseline: -4 placeholder + ~32 novih = net +28 tests.
  - [ ] Subtask 1.5 (PROŠIRENA, SM Fix iter 2 I-iter2-5 — empirical query count pre-verify PRE TEA RED-phase): Smoke verifikacija + empirijska query count provera MORA biti completed + literal locked u AC1/AC2 PRE Subtask 12 (TEA RED-phase).
    - (a) `uv run python manage.py check` exit code 0
    - (b) URL reverse provera:
      ```bash
      uv run python manage.py shell -c "from django.urls import reverse; \
        from django.utils.translation import activate; activate('sr'); \
        print(reverse('products:detail', kwargs={'slug': 'agri-tracking-tb804'}))"
      ```
      Očekivan output: `/sr/proizvod/agri-tracking-tb804/`
    - (c) Smoke check: GET `/sr/proizvod/test-tk-500/` vraća 200 (verifikuje URL routing posle ProductDetailView replacement); GET `/sr/proizvod/nepostojeci/` vraća 404.
    - (d) **Empirical query count probe (PRE TEA RED-phase — eliminate moving-target test contract per I-iter2-5 + SM-D28; uses `CaptureQueriesContext` per SM-D28 rationale extension — `settings.DEBUG=True` mutation in shell is UNRELIABLE because Django's `BaseDatabaseWrapper.force_debug_cursor` is set at `.connect()` time, NOT per-query):**
      ```bash
      docker compose -f compose/local.yml exec django uv run python manage.py shell -c "
      from django.db import connection
      from django.test import Client
      from django.test.utils import CaptureQueriesContext

      with CaptureQueriesContext(connection) as ctx:
          Client(HTTP_HOST='localhost').get('/sr/proizvod/test-tk-500/')
      print(f'Empirical query count: {len(ctx.captured_queries)}')
      for i, q in enumerate(ctx.captured_queries, 1):
          print(f'  {i}. {q[\"sql\"][:120]}')
      "
      ```
      **Expected: 7 queries** (per AC1 + AC2 enumeracije).
      - Ako empirijski daje 6 ili 8 (Django ORM nuanse — npr. session middleware, locale-aware Case/When adapt count), Dev MORA update-ovati literal u AC1 prose + AC2 docstring + Subtask 12.2 test signature **PRE Subtask 12 RED-phase**. Spec mutation PRE TEA pisanja je acceptable; mutation POSLE TEA pisanja je strogo zabranjena (test bi morao biti red i ostati red dok GREEN phase ne ispravi).
    - (e) **Subtask 1.5 MORA completed + literal locked PRE Subtask 12 (TEA RED-phase).** Validation gate: SM Fix iter 2 / SM-D28 — Subtask 12.2 ne sme započeti pre nego što je empirical literal verifikovan u Subtask 1.5(d).
  - [ ] Subtask 1.6: Verifikuj cross-boundary import status — `apps/products/views.py` SME importovati `apps.products.models` (same app, no boundary issue); takođe sme importovati `apps.brands.models` jer products → brands je natural direction per project-context.md § Cross-boundary import (linija 626 — „jednosmerna — `products → brands`"). NIKAKAV edit na project-context.md nije potreban za Story 2.7 (RAZLIČITO od Story 2.6 koja je dodala explicit izuzetak za brands → products view-layer coupling).

- [ ] **Task 2: `templates/products/product_detail.html` glavni template (AC3, AC4-AC8 wiring kroz includes)**
  - [ ] Subtask 2.1: Kreirati `templates/products/product_detail.html` sa `{% extends "base.html" %}` strukturom per AC3 spec
  - [ ] Subtask 2.2: Implementirati outer `<article class="coric-product-detail" data-testid="product-detail-page">` wrapper. **Verifikovati (I7, SM Fix iter 1):** `<article>` MORA sedeti UNUTAR `{% block content %}` koji je inside `<main id="main-content">` u base.html (Story 1.6 base.html provider — Story 2.6 B1 fix mirror). NE replace-uje `<main>`, NE wraps u sopstveni `<main>`. Smoke verifikacija: render i count `<main>` elemenata u output-u — TAČNO 1.
  - [ ] Subtask 2.3: Implementirati svih 8 `<section>`/`<aside>` sekcija TAČNIM redosledom (hero → opis → galerija → specs → brošura → slični → testimonijali → variants) sa `{% if ... %}` guard-ima za empty states. **Testimonials sekcija (sekcija 7, SM Fix iter 1+2, C1+C6+I-iter2-2/SM-D22+D23+D27):** koristi shared partial putanju `{% include "partials/_testimonials_slider.html" with testimonials=product.testimonials.all slider_id="product-testimonials-title" %}` (NIJE `products/partials/_testimonials.html`!) i `aria-labelledby="product-testimonials-title"` (story-specific ID, NE generic `testimonials-title` ni `brand-testimonials-title` — per SM-D27 future-collision guard za Story 3.1 Home). **Brošure sekcija (sekcija 5):** koristi `brochures_list` context kao guard i loop subject (NIJE `product.brochures.all`) per SM-D26/I8 view-pre-computation.
  - [ ] Subtask 2.4: Dodati `{% block product_detail_inquiry %}{% endblock %}` extension tačku za Story 4.3
  - [ ] Subtask 2.5: Verifikovati da svi user-facing string-ovi koriste `{% translate %}` / `{% blocktranslate %}`; NEMA hardcoded srpski string-ova; NEMA ćirilice
  - [ ] Subtask 2.6: Verifikovati single `<h1>` rule — proverava se da `product_detail.html` ne render-uje sopstveni `<h1>` (delegated kroz hero_overlay_card.html partial); ako se naleti na duplikat, B1 fix iz Story 2.6 mora biti aplicirano

- [ ] **Task 3: `_hero_section.html` partial (AC3 § hero overlay)**
  - [ ] Subtask 3.1: Kreirati `templates/products/partials/_hero_section.html` wrapper koji prosleđuje product kontekst u `partials/hero_overlay_card.html` (Story 1.7 partial)
  - [ ] Subtask 3.2: Implementirati `product.brand.brand_color → variant` mapping (REUSE Story 2.6 SM-D11 pattern: case-insensitive hex compare `|lower == "#00a4e9"` → `"blue"`, else `"green"`)
  - [ ] Subtask 3.3: Hero card prima: `title=product.name`, `bullets=product.key_features|slice:":3"`, `brand_logo=product.brand.logo.url` (defensively guarded via `{% if product.brand.logo %}`), `brand_logo_alt=product.brand.name`, `variant=mapped`. Ako `product.brand.logo` ne postoji, prosledi `brand_logo=""` (Story 2.6 Completion Notes Implementation choice).

- [ ] **Task 4: `_description.html` partial (AC3 § opis sekcija)**
  - [ ] Subtask 4.1: Kreirati `templates/products/partials/_description.html`:
    ```django
    {% load i18n %}
    {% include "partials/section_eyebrow.html" with text=_("OPIS PROIZVODA") tag="div" %}
    <h2 id="product-description-title" class="visually-hidden">{% translate "Opis proizvoda" %}</h2>
    <div class="coric-product-description__body">
      {{ product.description|linebreaks }}
    </div>
    ```
  - [ ] Subtask 4.2: Verifikuj `linebreaks` filter ponašanje (Django built-in: konvertuje `\n\n` u `<p>` paragraphs, single `\n` u `<br>`)

- [ ] **Task 5: `_gallery_carousel.html` partial (AC4)**
  - [ ] Subtask 5.1: Kreirati `templates/products/partials/_gallery_carousel.html` sa GLightbox auto-pickup pattern (`class="glightbox" data-gallery="product-{{ product.slug }}"`)
  - [ ] Subtask 5.2: Sve slike kroz `{% responsive_picture %}` sa `loading="lazy"` i `sizes="(max-width: 768px) 100vw, 33vw"`
  - [ ] Subtask 5.3: `data-glightbox="title: ..."` postavlja caption u Lightbox toolbar-u; alt text fallback iz `image.alt_text|default:product.name`
  - [ ] Subtask 5.4: `data-testid="gallery-item-{N}"` per slika (Playwright hook)

- [ ] **Task 6: `_specs_accordion.html` partial (AC5)**
  - [ ] Subtask 6.1: Kreirati `templates/products/partials/_specs_accordion.html` koji koristi `{% regroup product.specifications.all by section_label as spec_sections %}`
  - [ ] Subtask 6.2: Per-section `<details {% if forloop.first %}open{% endif %}>` sa `<summary>` (label + +/- ikona) + `<table>` (key/value rows)
  - [ ] Subtask 6.3: `data-testid="spec-section-{slugified-label}"` per details
  - [ ] Subtask 6.4: CSS za `+/-` toggle (pseudo-element `::after` content swap) u `product-detail.css`
  - [ ] Subtask 6.5: `@media (prefers-reduced-motion: reduce)` blok u `product-detail.css` za accordion

- [ ] **Task 7: `_brochure_card.html` partial (AC7)**
  - [ ] Subtask 7.1: Kreirati `templates/products/partials/_brochure_card.html` sa loop kroz `brochures_list` (view-pre-computed entries per SM-D26/I8 + cap 5 per SM-D24/I1). Pluralized heading per SM-D24/I1 (`{% blocktranslate count counter=brochures_list|length %}Preuzmite brošuru{% plural %}Preuzmite brošure{% endblocktranslate %}`).
  - [ ] Subtask 7.2: Per-entry render:
    ```django
    {% if entry.brochure.cover_thumbnail_image and entry.brochure.cover_thumbnail_image.name %}
      {% responsive_picture entry.brochure.cover_thumbnail_image ... %}
    {% endif %}
    <h3>{{ entry.brochure.title|default:product.name }}</h3>
    <p>{{ entry.size_bytes|filesizeformat }}, {% translate "PDF" %}</p>
    <a href="{{ entry.brochure.pdf_file.url }}" target="_blank" rel="noopener noreferrer" download class="coric-button coric-button--primary">{% translate "PREUZMI" %}</a>
    ```
    Defensive guards (SM Fix iter 1+2): (a) `.name` proširen guard za partial-state ImageField record per SM-D26/I9; (b) `entry.size_bytes` (NE `brochure.pdf_file.size` direktno) jer view-layer pre-computes sa try/except za `(FileNotFoundError, OSError, ValueError, SuspiciousFileOperation)` per SM-D26/I8 + I-iter2-4 broadened scope; (c) "PDF" wrapped kroz `{% translate %}` per SM-D25/I3 policy compliance. **Direktan `<a>` markup** (NE pill_button partial — SM-D22 mirror Story 2.6 — pill_button NE PODRŽAVA target/rel/download).
  - [ ] Subtask 7.3: `data-testid="brochure-card-{{ entry.brochure.id }}"` + `data-testid="brochure-download-{{ entry.brochure.id }}"` per card
  - [ ] Subtask 7.4 (NOVA, SM Fix iter 2 I-iter2-3 / SM-D24 plural completion): Posle Dev pokretanja `just makemessages` (regenerate .po fajlova za sr/hu/en za sve nove plural-tagged string-ove iz Story 2.7, uključujući brochure heading), Dev MORA editovati `locale/sr/LC_MESSAGES/django.po` i popuniti SVA 3 msgstr slot-a za sr plural key-ove. Konkretno za brochure heading:
    ```po
    #: templates/products/partials/_brochure_card.html
    msgid "Preuzmite brošuru"
    msgid_plural "Preuzmite brošure"
    msgstr[0] "Preuzmite brošuru"
    msgstr[1] "Preuzmite brošure"
    msgstr[2] "Preuzmite brošura"
    ```
    Razlog: `locale/sr/LC_MESSAGES/django.po` linija 19 deklariše `nplurals=3` za srpsku lokalu; ako se msgstr[2] ostavi prazan, Django runtime fall-back daje "Preuzmite brošure" za N=5+ (gramatički netačno — treba genitiv plural "brošura"). Za en/hu lokale, msgstr count je 2 (nplurals=2) — Dev popuni msgstr[0]="Download brochure", msgstr[1]="Download brochures" (en); msgstr[0]="Töltsd le a brosúrát", msgstr[1]="Töltsd le a brosúrákat" (hu — verify sa native review). Verifikovati `just compilemessages` (ili `django-admin compilemessages`) ne emituje warning ("incomplete translation" ili "wrong number of plural forms").

- [ ] **Task 8: `_similar_products.html` partial (AC6)**
  - [ ] Subtask 8.1: Kreirati `templates/products/partials/_similar_products.html` sa Wave Divider iznad (`{% include "partials/wave_divider.html" with position="top" %}`)
  - [ ] Subtask 8.2: Section Eyebrow + visible heading `<h2 id="product-similar-title">{% translate "Možda će vas zanimati i" %}</h2>`
  - [ ] Subtask 8.3: Loop kroz `similar_products` lista (resolved u view get_context_data); linkable card pattern (reuse `coric-product-card` BEM iz Story 2.6) sa `aria-label` + nested-interactive guard (CTA je `<span aria-hidden="true">`)
  - [ ] Subtask 8.4: `data-testid="similar-product-card-{slug}"` per card

- [ ] **Task 9: Testimonials partial SHARED MOVE (AC3 § sekcija 7) + `_variants_selector.html` partial (AC8)**
  - [ ] Subtask 9.0 (NOVA, SM Fix iter 1 C6/SM-D23 + SM Fix iter 2 I-iter2-1/I-iter2-2/SM-D27 — ZNAČAJNA REFAKTORIZACIJA + Story 2.6 EDIT obavezna + interface contract cascade): Premestiti `_testimonials_slider.html` iz `templates/brands/partials/` u `templates/partials/` (shared lokacija — single source-of-truth za brand 2.6 + product 2.7 + future home 3.1). U istom potezu:
    - (a) EDIT-ovati `templates/brands/brand_detail.html` linija 21 da `aria-labelledby` referencira eksplicitan ID iz `slider_id` kwarg-a (`aria-labelledby="brand-testimonials-title"` — vrednost ostaje ista zbog SM-D27 backwards compat) i linija 22 include path da bude `{% include "partials/_testimonials_slider.html" with testimonials=testimonials slider_id="brand-testimonials-title" %}` (umesto `brands/partials/_testimonials_slider.html` bez kwarg-a). NAPOMENA SM-D27 (I-iter2-2): Story 2.6 ID `brand-testimonials-title` se EKSPLICITNO prosleđuje da bi se sprečio future ID collision u Story 3.1 Home (gde bi se i featured-brand snippet i page-level testimonials sekcija mogle pojaviti na istoj strani sa istim partial-om); shared partial ima `default:"testimonials-title"` ali svaki konzument PREPORUČENO koristi story-specific ID.
    - (b) U premeštenom `templates/partials/_testimonials_slider.html` UVODI se opcioni `slider_id` kwarg sa default vrednošću `"testimonials-title"`. Markup top-of-file:
      ```django
      {% load i18n media_tags %}
      {% with slider_id=slider_id|default:"testimonials-title" %}
      <h2 id="{{ slider_id }}" class="visually-hidden">{% translate "Iz prve ruke" %}</h2>
      {% include "partials/section_eyebrow.html" with text=_("IZ PRVE RUKE") tag="div" %}
      <div class="coric-testimonials-slider"
           data-testimonials-slider
           ...>
        ... (postojeći markup netaknut) ...
      </div>
      {% endwith %}
      ```
      (1-line edit `<h2 id="brand-testimonials-title">` → `<h2 id="{{ slider_id }}">` + wrap u `{% with slider_id=slider_id|default:"testimonials-title" %}...{% endwith %}` za safe default).
    - (c) ALSO UPDATE: `apps/brands/tests/test_templates_brand_listing.py` — `aria-labelledby="brand-testimonials-title"` assertion (live verifikovano u 2 mesta: linija 129-130) **OSTAJE NETAKNUTA** jer Story 2.6 brand_detail.html eksplicitno prosleđuje `slider_id="brand-testimonials-title"` kwarg per SM-D27 backwards compat (vidi 9.0a). Test assertion verifikuje da renderovani HTML i dalje sadrži taj string — što je tačno per SM-D27. NEMA Story 2.6 test mutacije.
    - (d) Add sprint-status.yaml + Story 2.6 file napomenu: editovati `_bmad-output/implementation-artifacts/sprint-status.yaml` `last_updated` polje da uključi: "Story 2.7 SM Fix iter 2: refaktoriše shared testimonials partial iz `templates/brands/partials/_testimonials_slider.html` u `templates/partials/_testimonials_slider.html` (+1 MOVE) i uvodi `slider_id` kwarg (SM-D27); cross-story cascade scope: +/-3 lines across 2 source files (brand_detail.html + _testimonials_slider.html) + 1 interface contract doc edit (2-6-interface-contract.md L207); tested by Subtask 9.0c (no-op — brand-testimonials-title assertion ostaje validna)." Story 2.6 file (Completion Notes append) dobija notu: "Story 2.7 je refaktorisao testimonials partial location: `templates/brands/partials/_testimonials_slider.html` → `templates/partials/_testimonials_slider.html` (shared sa `slider_id` kwarg, default `testimonials-title`). `brand_detail.html` linija 22 sad prosleđuje `slider_id=\"brand-testimonials-title\"` da preserve postojeću ID konvenciju (backwards compat — SM-D27)."
    - (e) NOVA (SM Fix iter 2, I-iter2-1): EDIT-ovati `_bmad-output/implementation-artifacts/2-6-interface-contract.md` linija 207 (sekcija "## 4. Templates → `templates/brands/brand_detail.html`"): zameniti tekst `include `brands/partials/_testimonials_slider.html`` sa `include `partials/_testimonials_slider.html` with `slider_id="brand-testimonials-title"` kwarg (SM-D27)`. ID `brand-testimonials-title` u `aria-labelledby` OSTAJE u contract-u (jer brand_detail.html eksplicitno prosleđuje kwarg). Dodati inline historical napomenu (inline ili pod tekstom): "Refaktorisano u Story 2.7 (SM-D23/SM-D27) — shared partial premešten u `templates/partials/`, uveden `slider_id` kwarg sa default `testimonials-title`; brand_detail eksplicitno prosleđuje `brand-testimonials-title` za backwards compat." TAKOĐE update interface contract sekciju 3 "Templates" table (linija ~38) red `templates/brands/partials/_testimonials_slider.html` → `templates/partials/_testimonials_slider.html` (shared) ako tabela postoji (verify live u Step 3 GREEN; bez kreiranja novog reda).
    - (f) NOVA (SM Fix iter 2, I-iter2-1): Verifikovati nema OTHER assertion u `apps/brands/tests/test_templates_brand_listing.py` koji referencira `brand-testimonials-title` ID beyond lines 129-130 (sve enumerisane u live grep-u): `git grep brand-testimonials-title apps/brands/tests/` ili equivalent Grep tool. Ako orphan reference postoji (beyond linija 129-130), update/uskladiti pre commit-a. Live grep verifikovan tokom SM Fix iter 2: SAMO 2 hits (linije 129 i 130) — no orphans.
  - [ ] Subtask 9.1 (REVIDIRANA SM Fix iter 1, C1/SM-D22 + SM Fix iter 2 I-iter2-2/SM-D27): **NEMA mirror copy** — Story 2.7 koristi shared partial premešten u Subtask 9.0. U `product_detail.html` sekcija 7, include sa eksplicitnim context binding-om I story-specific `slider_id`: `{% include "partials/_testimonials_slider.html" with testimonials=product.testimonials.all slider_id="product-testimonials-title" %}`. Pattern dokumentovan u SM-D22 (include-with-context) + SM-D27 (slider_id kwarg per-konzument). NEMA novog fajla `templates/products/partials/_testimonials.html` (originalna Subtask 9.1 DEPRECATED — vidi SM-D4 revidirano).
  - [ ] Subtask 9.2: NEMA novog JS modula — `static/js/testimonials-slider.js` (Story 2.6 deliverable, site-wide loaded u base.html) je reuse-ovan; defensive bail-uje silently ako selektor nije na strani (vidi Story 2.6 AC7 JS source). JS selektor `[data-testimonials-slider]` ostaje identičan jer markup nije se promenio (samo lokacija + ID rename).
  - [ ] Subtask 9.3: Kreirati `templates/products/partials/_variants_selector.html` per AC8 spec
  - [ ] Subtask 9.4: Conditional render: ako `variant.image` postoji → GLightbox `<a class="glightbox" data-gallery="product-{{ product.slug }}-variants">` (slug-scoped per Story 2-5 contract / I2); ako ne, plain `<div>` (no link)
  - [ ] Subtask 9.5: `data-testid="variant-card-{id}"` per card; `aria-label` na `<a>` jasno najavi otvaranje zoom-a

- [ ] **Task 10: 3 nova CSS komponentna fajla + `main.css` Edit + `brand-listing.css` cleanup (AC3-AC8 styling, SM-D21 cleanup, SM-D6 carousel decision)**
  - [ ] Subtask 10.1: Kreirati `static/css/components/product-detail.css` sa root klasa (`.coric-product-detail`) + svim sub-klasama (description, brochure card, brochure-wrap aside, similar grid, accordion summary/details + `+/-` toggle pseudo-elementi); MIGRACIJA `coric-product-placeholder*` BEM klasa iz `brand-listing.css` u ovaj fajl per Story 2.6 SM-D21 cleanup plan (klase: `.coric-product-placeholder`, `.coric-product-placeholder__title`, `.coric-product-placeholder__message` — defunkcionalne sad jer placeholder template je obrisan; cleanup je tehnički nepotreban ali sledi SM-D21 najavu)
  - [ ] Subtask 10.2: Kreirati `static/css/components/product-gallery.css` sa gallery grid (CSS Grid desktop / scroll-snap mobile per SM-D6); slide thumbnail stilovi (`coric-product-gallery__grid`, `coric-product-gallery__item`, `coric-product-gallery__img`)
  - [ ] Subtask 10.3: Kreirati `static/css/components/product-variants.css` sa variant kartice grid (responsive 1-4 per row), hover state, focus-visible outline; `coric-product-variants__card`, `__card--no-image`, `__image`, `__body`, `__name`, `__code`, `__desc`
  - [ ] Subtask 10.4: Editovati `static/css/main.css` — dodaj 3 nove `@import url('./components/...');` linije TAČAN mirror Story 1.7+1.8+2.5+2.6 sintaksu:
    ```css
    @import url('./components/product-detail.css');
    @import url('./components/product-gallery.css');
    @import url('./components/product-variants.css');
    ```
  - [ ] Subtask 10.5: Editovati `static/css/components/brand-listing.css` — UKLONI 3 selektora (`.coric-product-placeholder`, `.coric-product-placeholder__title`, `.coric-product-placeholder__message`) per SM-D21 cleanup plan. Ostatak fajla netaknut (regression guard za Story 2.6 testove).
  - [ ] Subtask 10.6: Verifikovati nema CDN referenci u novim fajlovima (`cdn.jsdelivr.net`, `unpkg.com`, `cdnjs.cloudflare.com`) — mirror Story 2.6 AC8 anti-CDN guard
  - [ ] Subtask 10.7: Verifikovati svi BEM klasi imaju `coric-` prefix; svi CSS koriste `var(--token)` reference (NIKADA magic hex/px); ako se naleti na manjak token-a, NE uvoditi nove tokene u 2.7 — koristiti najbliži postojeći token + dokumentovati u Completion Notes (mirror Story 2.6 AC8)
  - [ ] Subtask 10.8 (uslovno, SAMO ako SM-D6 odluka je vanilla JS carousel): Kreirati `static/js/product-gallery.js` (vanilla IIFE; prev/next + keyboard nav + thumbnail klik); editovati `templates/base.html` da doda `<script src="{% static 'js/product-gallery.js' %}" defer></script>` POSLE `testimonials-slider.js`. **DEFAULT odluka (SM-D6): pure CSS scroll-snap u v1; JS module se NE kreira; base.html EDIT se preskaže.** Ako se v1 UX testing pokaže da scroll-snap nije dovoljan (npr. fokusiranje izgubi kontekst trenutne slike), refaktor je trivijalan u Story 9-10 polish.

- [ ] **Task 11: Manuelni Dev smoke check + Lighthouse a11y audit (AC9)**
  - [ ] Subtask 11.1: Dev pokrene `just dev` (Docker Compose local)
  - [ ] Subtask 11.2: Dev seed-uje sample podatke (Django shell ili admin GUI) za bar 1 published Product sa: main_image, key_features (3), description, 4+ ProductImage, 2+ ProductVariant (sa images), specifications iz 4 sekcija, 1+ ProductBrochure sa cover_thumbnail (Story 2.4 signal generates), 3+ ProductTestimonial; opciono 1 ProductSimilar (manual override path); takođe drugi Product u istom brendu + seriji (auto fallback path test)
  - [ ] Subtask 11.3: Dev poseti `http://localhost:8000/sr/proizvod/<seed-product-slug>/` u Chrome; verifikuje sve sekcije rade per AC9 checklist (hero, opis, galerija, akordion, brošure, slični, testimonijali, variants)
  - [ ] Subtask 11.4: Dev verifikuje single `<h1>` rule (`document.querySelectorAll('h1').length === 1` u DevTools Console)
  - [ ] Subtask 11.5: Dev aktivira `prefers-reduced-motion: reduce` u DevTools Rendering panel; reload; verifikuje Lightbox instant, akordion instant, slider no auto-advance
  - [ ] Subtask 11.6: Dev testira FR-20 hibrid: setuje ProductSimilar; verifikuje manual override; obriše; verifikuje auto fallback; izolovan proizvod (no brand+series match) → sekcija sakrivena
  - [ ] Subtask 11.7: Dev testira variant selektor: klik na variant karticu otvara GLightbox zoom; verifikuj `coric:lightbox-open` pauzira testimonials slider auto-advance (DevTools Network/Console + manual time check)
  - [ ] Subtask 11.8: Dev pokrene Lighthouse audit u CLI mode-u (per AC9 § Lighthouse JSON artifact preservation, mirror Story 2.6 I-iter2-8). **SM Fix iter 1 (I6) — Windows host PowerShell vs POSIX:**
    - **Opcija A (preferirana — Docker container POSIX shell):** `docker compose -f compose/local.yml exec django sh -c 'lighthouse http://localhost:8000/sr/proizvod/<seed-product-slug>/ --output=json --output-path=/app/_bmad-output/implementation-artifacts/2-7-lighthouse-$(date +%Y%m%d).json --only-categories=accessibility,performance,seo --form-factor=mobile --chrome-flags="--headless"'`
    - **Opcija B (Windows host PowerShell, ako lighthouse instaliran na host-u):** `lighthouse http://localhost:8000/sr/proizvod/<seed-product-slug>/ --output=json --output-path=_bmad-output/implementation-artifacts/2-7-lighthouse-$(Get-Date -Format yyyyMMdd).json --only-categories=accessibility,performance,seo --form-factor=mobile --chrome-flags="--headless"`. NAPOMENA: `$(date +%Y%m%d)` (POSIX) ne radi u PowerShell-u; koristi `$(Get-Date -Format yyyyMMdd)`.
    - **Opcija C (fallback):** Chrome DevTools Lighthouse run → Save report (JSON) → manuelno kopirati u `_bmad-output/implementation-artifacts/2-7-lighthouse-YYYYMMDD.json`.
    - Verifikuje Accessibility ≥ 95 + Performance ≥ 75 + SEO ≥ 90; dokumentuje sve 3 skor-ove u Dev Agent Record § Completion Notes sekciji story fajla PRE Step-04 commit.
  - [ ] Subtask 11.9: Dev verifikuje keyboard nav: skip link → Tab kroz hero CTA → galerija slike → akordion summary → brošura PDF download → slični kartice → testimonijal prev/pause/next → variant kartice; fokus indicator vidljiv (`:focus-visible` outline iz tokens)

- [ ] **Task 12: TEA-deliverable — testovi (RED phase, Step 3, NIJE Dev scope)** _(NAPOMENA: ovaj task je listed for clarity — TEA agent u Step 3 piše testove pre Dev-ovog GREEN phase implementacije; Dev NIKAD ne piše testove per project-context.md § Test discipline linija 294)_
  - **Minimum test count per AC (mirror Story 2.6 ~30+ tests konvencija):** **~55 tests total** (recount per SM Fix iter 2 I-iter2-7): Subtask 12.1 = 5 tests (AC1 URL routing); Subtask 12.2 = 13 tests (AC2 view/queries/context — 5 originalna + 8 SM Fix iter 1: C3/C4/SM-D24/SM-D26; +0 method-count u iter 2, ali test_brochures_list je sada parametrized preko 4 exception path-ova per I-iter2-4); Subtask 12.3 = 27 tests (AC3 5 = 3 originalna + 1 iter1 I7 + 1 iter2 I-iter2-2 testimonials aria id; AC4 3; AC5 4; AC6 4; AC7 7 = 4 originalna + 3 iter1 SM-D24/D25/D26; AC8 4); Subtask 12.4 = 1 test (AC5 hu locale specs xfail); Subtask 12.5 = 4 tests (placeholder deletion regression); Subtask 12.6 = 4 tests (cross-cutting static assets). **Total: 5 + 13 + 27 + 1 + 4 + 4 = 54-55 tests** (cap depending on AC3 testimonials test methodology — 1 method = 54; if SM-D27 verification split u 2 method (postive `product-testimonials-title` + negative `not brand-testimonials-title`) = 55). **Test count baseline delta:** -4 (deleted `test_placeholder.py` per Subtask 1.4 / C2) + ~55 novih = **net +51 tests** vs pre-Story 2.7 baseline.
  - [ ] Subtask 12.1: TEA kreira/proširuje `apps/products/tests/test_urls_detail.py` — **AC1 URL routing: 5 tests** (NAPOMENA: dodatne parametrizovane status tests su u Subtask 12.2 per SM Fix iter 1 C4/SM-D20 — `test_unpublished_product_returns_404_regardless_of_status` + `test_published_product_renders_regardless_of_status`):
    - test_product_detail_url_resolves_sr_locale (200 za published Product sa `slug="agri-tracking-tb804"` na /sr/)
    - test_product_detail_url_resolves_hu_locale (200 na /hu/)
    - test_product_detail_url_resolves_en_locale (200 na /en/)
    - test_product_detail_404_for_nonexistent_slug (404)
    - test_product_detail_404_for_unpublished_product (404 za `is_published=False` — SM-D3 + SM-D20: `is_published` je SOLE public-visibility gate, status TextChoices je admin-only metadata)
  - [ ] Subtask 12.2: TEA kreira `apps/products/tests/test_views_detail.py` — **AC2 view + queries + context: ~13 tests (5 originalna + 8 dodato SM Fix iter 1; iter 2 expansion: test_brochures_list_pre_computed_with_size_bytes parametrized preko 4 exception path-ova per I-iter2-4 — still 1 test method, 4 invocations)**
    - test_context_contains_product_and_similar_products (no `gallery_images` etc. odvojeni ključevi — sve kroz product.<relation>.all; brochures_list je izuzetak per SM-D26/I8)
    - test_assert_num_queries_exactly_7 (assertNumQueries EXACT-match per SM-D21/C5; ako empirijski drugačiji, Dev update-uje literal — vidi AC2 docstring enumeraciju)
    - test_similar_products_manual_override_path (kreira ProductSimilar sa published related_product, verifikuje manual list, similar_source=="manual")
    - test_similar_products_auto_fallback_path (no ProductSimilar; kreira drugi published Product u istom brendu+seriji; verifikuje auto list, similar_source=="auto")
    - test_similar_products_empty_state (no manual, no auto matches; similar_source=="none", similar_products=[])
    - **(SM Fix iter 1, C3 + SM-D19)** test_manual_similars_with_unpublished_filtered_at_sql_level — admin postavi 4 ProductSimilar entries gde su 2 published + 2 unpublished; verifikuj da rezultantna lista ima 2 entries (NE 4, NE auto fallback firing); `similar_source=="manual"` jer manual_list nije prazan; verifikuj `assertNumQueries(7)` unchanged (added WHERE clause je još 1 query).
    - **(SM Fix iter 1, C4 + SM-D20)** test_unpublished_product_returns_404_regardless_of_status — parametrizovan preko 3 kombinacije: (is_published=False, status="published"), (is_published=False, status="draft"), (is_published=False, status="archived"); sve daju HTTP 404 (is_published je SOLE gate).
    - **(SM Fix iter 1, C4 + SM-D20)** test_published_product_renders_regardless_of_status — parametrizovan preko 3 kombinacije: (is_published=True, status="draft"), (is_published=True, status="published"), (is_published=True, status="archived"); sve daju HTTP 200 (is_published je SOLE gate; status je admin-only metadata).
    - **(SM Fix iter 1+2, SM-D26/I8 + I-iter2-4 broadened scope)** test_brochures_list_pre_computed_with_size_bytes — verifikuj `ctx["brochures_list"]` je list dict-ova `{"brochure": ..., "size_bytes": int}`; cap 5 entries; **parametrized over 4 exception types**: file missing (mock raise FileNotFoundError) → size_bytes=0; OS error (mock raise OSError("permission denied")) → size_bytes=0; unsaved FieldFile (mock raise ValueError) → size_bytes=0; suspicious path (mock raise SuspiciousFileOperation) → size_bytes=0. Sve 4 putanje → graceful degradation, no 500 error.
    - **(SM Fix iter 1, SM-D24/I1)** test_brochures_list_capped_at_5 — admin kreira 7 ProductBrochure entries; verifikuj `ctx["brochures_list"]` ima 5 entries (slice cap).
  - [ ] Subtask 12.3: TEA kreira/proširuje `apps/products/tests/test_templates_detail.py` — sve preostale AC-ove:
    - **AC3: 5 tests (3 originalna + 1 dodato SM Fix iter 1 I7 + 1 dodato SM Fix iter 2 I-iter2-2)** — test_sections_render_in_correct_order (hero → opis → galerija → specs → brošura → slični → testimonijali → variants); test_article_outer_wrapper_with_testid (`<article data-testid="product-detail-page">` outer wrapper); test_exactly_one_h1_on_page (BeautifulSoup parse + assertEqual 1 — mirror Story 2.6 T1); **(SM Fix iter 1, I7)** test_product_detail_has_single_main_element (BeautifulSoup parse + assertEqual `len(soup.find_all("main"))` == 1 — mirror Story 2.6 B1 nested-main guard; `<article>` MORA sedeti INSIDE `<main id="main-content">` koji base.html provider već renderuje); **(SM Fix iter 2, I-iter2-2/SM-D27)** test_testimonials_section_uses_product_specific_aria_id (verify renderovani HTML sadrži `aria-labelledby="product-testimonials-title"` na sekciji 7 `<section id="product-testimonials">` AND verify shared partial output `<h2 id="product-testimonials-title">` postoji — story-specific ID per SM-D27 future-collision guard; verify NEMA generic `id="testimonials-title"` ni `brand-testimonials-title` na renderovanoj product detail strani).
    - **AC4 galerija: 3 tests** — test_gallery_renders_all_images (sve ProductImage entries); test_glightbox_data_attributes (`class="glightbox"` + `data-gallery="product-{{ product.slug }}"` per slika); test_responsive_picture_alt_text (alt fallback iz alt_text ili product.name)
    - **AC5 akordion: 4 tests** — test_specs_grouped_by_section_label (regroup output); test_motor_section_open_by_default (`<details open>` na prvoj); test_empty_section_skipped (kreiraj product sa specs samo u "motor" + "ostalo", verifikuj 2 details ne 4); test_accordion_uses_native_details_summary
    - **AC6 slični: 4 tests (+ 1 cross-listed u Subtask 12.2 — `test_manual_similars_with_unpublished_filtered_at_sql_level` per C3/SM-D19)** — test_similar_cards_render_with_aria_label (linkable card pattern + aria-label); test_similar_cta_is_span_not_link (nested-interactive guard); test_max_4_similar_products (LIMIT 4 enforced); test_wave_divider_rendered_above_section
    - **AC7 brošure: 7 tests (4 originalna + 3 dodato SM Fix iter 1)** — test_brochure_renders_with_cover_thumbnail (responsive_picture); test_brochure_size_label_uses_filesizeformat (e.g. "2.4 MB"); test_brochure_download_anchor_has_target_blank_rel_noopener_download (direct anchor pattern, NO pill_button); test_multiple_brochures_render_all (loop iteration kroz `brochures_list`); **(SM-D24/I1)** test_brochure_heading_pluralized_singular_vs_plural (verifikuj `{% blocktranslate count %}{% plural %}` — N=1 daje "Preuzmite brošuru", N≥2 daje "Preuzmite brošure"); **(SM-D25/I3)** test_brochure_pdf_acronym_is_translatable (grep `_brochure_card.html` za `{% translate "PDF" %}` ili `{% trans "PDF" %}`); **(SM-D26/I9)** test_brochure_cover_thumbnail_guard_handles_empty_name (mock brochure sa cover_thumbnail_image=ImageFieldFile sa praznim `.name` → `<img>` se NE renderuje)
    - **AC8 variants: 4 tests** — test_variant_card_with_image_renders_glightbox_anchor (`class="glightbox" data-gallery="product-variants"`); test_variant_card_no_image_renders_plain_div (defensive); test_variant_no_state_change_no_form (markup audit — no `<form>` u variants partial, no `data-variant-id` JS hook); test_data_gallery_distinct_from_main_gallery (variant_card data-gallery != gallery-item data-gallery)
  - [ ] Subtask 12.4: TEA kreira `apps/products/tests/test_locale_specs.py` — **AC5 locale-aware Case/When verifikacija (mirror Story 2.6 SM-D20 test):**
    - test_extended_layout_section_labels_hu — render `product_detail.html` pod `LANGUAGE_CODE='hu'`; asertovati hu-locale prevode `<summary>` elemenata (npr. "Hajtómű" za "Transmisija"); `xfail` ako hu prevodi nedostaju u `locale/hu/LC_MESSAGES/django.po` (verify live pre Subtask)
  - [ ] Subtask 12.5: TEA kreira `apps/products/tests/test_placeholder_deleted.py` — **Regression guard za Subtask 1.3 + Subtask 1.4 (SM Fix iter 1, C2 replacement coverage):**
    - test_placeholder_template_file_does_not_exist (`assert not (BASE_DIR / "templates/products/_placeholder.html").exists()`)
    - test_placeholder_view_no_longer_in_views_module (`from apps.products import views; assert not hasattr(views, "placeholder_view")`)
    - test_placeholder_test_file_does_not_exist (`assert not (BASE_DIR / "apps/products/tests/test_placeholder.py").exists()` — SM Fix iter 1 C2 regression guard za Subtask 1.4 DELETE)
    - test_product_detail_url_now_serves_product_detail_view (sanity check: ista URL ruta `/sr/proizvod/<slug>/` koja je Story 2.6 servirala placeholder sada serve-uje ProductDetailView — verifikuje response.resolver_match.func.view_class je ProductDetailView; ovo je REPLACEMENT za 4 obrisana placeholder tests koji asertuju isti URL serve-uje 200)
  - [ ] Subtask 12.6: TEA kreira `tests/test_product_detail_static_assets.py` — **AC3 § cross-cutting static asset audit + i18n/no-inline-styles requirements (mirror Story 2.6 AC8 + Story 2.5 file-existence pattern; SM Fix iter 1, I5 — renumerisano iz "AC10" jer Story 2.7 ima samo AC1-AC9): 4 tests**
    - test_all_strings_translatable_no_hardcoded_serbian (grep partials za hardcoded srpski osim u {% translate %})
    - test_no_inline_styles_in_product_templates (grep `style="` u svim products templates → 0)
    - test_product_detail_css_imports_in_main_css (verify 3 new `@import` linije)
    - test_brand_listing_css_no_longer_has_placeholder_selectors (SM-D21 cleanup verification)
  - [ ] Subtask 12.7: TEA dokumentuje **AC9 manuelni smoke check** kao SINGLE manual checklist item u retrospective (NE automated test): "Dev manualno verifikuje Lighthouse a11y ≥ 95 + `prefers-reduced-motion` Chrome DevTools test + FR-20 manual override / auto fallback paths + variant zoom no-state-change"
  - [ ] Subtask 12.8: TEA verifikuje testovi padaju u RED phase (`uv run pytest apps/products/tests/test_views_detail.py apps/products/tests/test_templates_detail.py apps/products/tests/test_locale_specs.py apps/products/tests/test_placeholder_deleted.py tests/test_product_detail_static_assets.py` ima fail-ove zbog missing ProductDetailView + templates)
  - [ ] Subtask 12.9: TEA commit-uje test fajlove PRE Dev GREEN phase (`test(products): Story 2.7 RED-phase tests — product detail view + templates + locale + static assets + placeholder deletion regression`)

## Dev Notes

### Postojeća `apps/products/` struktura (snimak pre Edit-a — regression guard)

Pre Story 2.7, `apps/products/` direktorijum sadrži (live verifikovano 2026-05-30):

```
apps/products/
├── __init__.py             (prazan)
├── admin.py                 (stub register-i za Product/related — Story 2.2; Story 8.6 puni)
├── apps.py                  (ProductsConfig — Story 2.2)
├── migrations/
│   ├── __init__.py
│   └── 0001_initial.py      (Story 2.2 — Product + 6 related models)
├── models.py                (Product, ProductImage, ProductVariant, ProductSpecification, ProductBrochure, ProductTestimonial, ProductSimilar — Story 2.2; 21 KB)
├── tests/
│   └── (test fajlovi iz Story 2.2 i 2.6 placeholder)
├── translation.py           (TranslationOptions za 6 modela — Story 2.2)
├── views.py                 (placeholder_view FBV — Story 2.6 C8 fix)
└── urls.py                  (placeholder URL pattern — Story 2.6 C8 fix)
```

**Story 2.7 menja (DELTA — `apps/products/`):**
- `apps/products/views.py` (REPLACE — placeholder_view FBV → ProductDetailView CBV)
- `apps/products/urls.py` (EDIT 1-line — views.placeholder_view → views.ProductDetailView.as_view())
- `templates/products/_placeholder.html` (DELETE — placeholder template iz Story 2.6 C8 fix)
- `templates/products/product_detail.html` (NOVO — entry template)
- `templates/products/partials/` (NOVO direktorijum sa 8 partials)

**Story 2.7 NE menja:**
- `apps/products/models.py` (regression guard za Story 2.2 testove — sva 7 modela ostaju identični)
- `apps/products/admin.py` (Story 8.6 scope)
- `apps/products/translation.py`
- `apps/products/migrations/` (NEMA novih migracija u 2.7)
- `apps/products/apps.py`
- `apps/brands/views.py`, `apps/brands/urls.py`, `apps/brands/models.py` (Story 2.6 deliverable; regression guard)
- `config/urls.py` (pattern + namespace + URL name `detail` registrovani u Story 2.6, ostaju identični)
- `_bmad-output/project-context.md` (NEMA cross-boundary izuzetka u 2.7 — products → brands je natural direction)

### Model discovery — **SVE PRETPOSTAVKE POTVRĐENE LIVE (2026-05-30)**

Live verifikovano `apps/products/models.py`:

| Model | Postoji | Polja relevantna za Story 2.7 |
|---|---|---|
| `Product` (linija 78) | ✓ | brand FK, series FK nullable, subcategory FK nullable, name, slug, description, key_features (JSONField list), main_image, horse_power, is_published, condition, status |
| `ProductImage` (linija 278) | ✓ | product FK, image, order, alt_text — related_name="images" |
| `ProductVariant` (linija 315) | ✓ | product FK, name, code, image, description, order — related_name="variants" |
| `ProductSpecification` (linija 366) | ✓ | product FK, section (TextChoices: motor/transmisija/hidraulika/ostalo), key, value, order — related_name="specifications" |
| `ProductBrochure` (linija 416) | ✓ | product FK, pdf_file (FileField), cover_thumbnail_image (ImageField — auto-gen iz Story 2.4 signal), title — related_name="brochures" |
| `ProductTestimonial` (linija 464) | ✓ | product FK, photo, quote, author_name, location, order — related_name="testimonials" |
| `ProductSimilar` (linija 507) | ✓ | product FK (related_name="outgoing_similars"), related_product FK (related_name="incoming_similars"), order — directional per PR-D5 |

**Sve 4 uncertainties iz orchestrator KEY UNCERTAINTIES liste su RESOLVED:**

1. ✓ `ProductVariant` model **POSTOJI** (Story 2.2 deliverable) — Story 2.7 može renderovati variants sekcija per AC8
2. ✓ `ProductSimilar` M2M-like model **POSTOJI** (Story 2.2 deliverable, directional via 2 FK-a) — Story 2.7 može renderovati FR-20 hibrid sa manual override
3. ✓ `Product.brochures` (FK reverse iz ProductBrochure) **POSTOJI** (Story 2.2) — brošure sekcija je in-scope; `cover_thumbnail_image` polje (Story 2.4 auto-gen) podržava `responsive_picture` render
4. ✓ `Product.images` (FK reverse iz ProductImage) **POSTOJI** (Story 2.2) — galerija sekcija je in-scope (NE samo single `main_image`)

**NIJEDNA AC nije conditional ni deferred** — sve sekcije strane (hero, opis, galerija, specs, brošura, slični, testimonijali, variants) su scope-in.

### Relevantni Modeli (iz Story 2.1, 2.2 — live verifikovano)

**Product** (apps/products/models.py linija 78, Story 2.2):
- `slug` (SlugField, globally unique, kroz SluggedModel mixin)
- `brand` (FK Brand, PROTECT, related_name="products")
- `series` (FK Series, PROTECT nullable, related_name="products")
- `subcategory` (FK Subcategory, PROTECT nullable, related_name="products")
- `name` (CharField, translatable, max_length=200)
- `description` (TextField, translatable, MaxLengthValidator(50000))
- `key_features` (JSONField list, max 3 entries, translatable, validated u clean())
- `main_image` (ImageField, optional)
- `year` (PositiveSmallIntegerField, optional)
- `price_eur` (DecimalField, optional, max_digits=10, decimal_places=2)
- `horse_power` (PositiveSmallIntegerField, optional)
- `condition` (TextChoices: NEW/USED)
- `status` (TextChoices: DRAFT/PUBLISHED/ARCHIVED, db_index=True)
- `is_published` (BooleanField, default=False)
- `get_absolute_url()` → `reverse("products:detail", kwargs={"slug": self.slug})` (verifikovano linija 269-270)

**ProductImage** (linija 278):
- `product` (FK Product, CASCADE, related_name="images")
- `image` (ImageField, upload_to="products/gallery/")
- `order` (PositiveSmallIntegerField, default 0, db_index=True)
- `alt_text` (CharField, max_length=200, translatable)
- Meta.ordering = ["order", "id"]

**ProductVariant** (linija 315):
- `product` (FK Product, CASCADE, related_name="variants")
- `name` (CharField, max_length=200, translatable)
- `code` (CharField, max_length=50, blank)
- `image` (ImageField, optional, upload_to="products/variants/")
- `description` (TextField, translatable, MaxLengthValidator(50000))
- `order` (PositiveSmallIntegerField, default 0, db_index=True)
- Meta.ordering = ["order", "id"]

**ProductSpecification** (linija 366):
- `product` (FK Product, CASCADE, related_name="specifications")
- `section` (TextChoices SpecSection.MOTOR / TRANSMISIJA / HIDRAULIKA / OSTALO, default OSTALO, db_index=True)
- `key` (CharField, max_length=200, translatable)
- `value` (CharField, max_length=200, translatable)
- `order` (PositiveSmallIntegerField, default 0, db_index=True)
- Meta.ordering = ["product", "order", "id"] (NOTE I3 — section NIJE u ordering jer alphabetical sort daje pogrešan red; Case/When section_rank u view layer je kanonski fix per Story 2.6 SM-D14)

**ProductBrochure** (linija 416):
- `product` (FK Product, CASCADE, related_name="brochures")
- `pdf_file` (FileField, upload_to="products/brochures/")
- `cover_thumbnail_image` (ImageField, optional, upload_to="products/brochure_covers/" — auto-gen Story 2.4 post_save signal)
- `title` (CharField, max_length=200, blank)
- Meta.ordering = ["product", "id"]

**ProductTestimonial** (linija 464):
- Identično kao Story 2.6 § Relevantni Modeli (mirror) — product FK, photo, quote, author_name, location, order
- Meta.ordering = ["order", "id"]
- Story 2.7 fetch-uje sa `.order_by("order", "-created_at")` (mirror Story 2.6 § AC2)

**ProductSimilar** (linija 507):
- `product` (FK Product, CASCADE, related_name="outgoing_similars")
- `related_product` (FK Product, CASCADE, related_name="incoming_similars")
- `order` (PositiveSmallIntegerField, default 0, db_index=True)
- Directional per PR-D5 — Product A → B ne znači B → A
- Meta.ordering = ["product", "order", "id"]
- UniqueConstraint pair (product, related_product) — sprečava duplikat
- CheckConstraint product != related_product — sprečava self-reference

### URL pattern (i18n_patterns)

`config/urls.py` koristi `i18n_patterns(...)`; product detail URL je:
- `sr` locale: `/sr/proizvod/agri-tracking-tb804/`
- `hu` locale: `/hu/proizvod/agri-tracking-tb804/`
- `en` locale: `/en/proizvod/agri-tracking-tb804/`

**NAPOMENA:** "proizvod" kao URL segment je trenutno **hardcoded srpski**. Multi-locale URL slug variant (`/hu/termek/...`, `/en/product/...`) je Story 6.6 scope; v1 koristi srpski URL slug-ove na svim locale-ima — funkcionalno radi, SEO refinement kasnije.

### Section ordering pattern — REUSE iz Story 2.6 BrandDetailView (SM-D14/D20)

Story 2.7 ProductDetailView **DIREKTNO REUSE-uje** Case/When section_rank + section_label pattern uveden u Story 2.6 BrandDetailView (vidi Story 2.6 AC2 source code + SM-D14/D20 Decision Log). Razlog za reuse (NE extract u helper sad):

- **Code duplication: 1 mesto za sada (BrandDetailView)**. Story 2.7 dodaje 2. mesto (ProductDetailView). YAGNI per project-context.md § "Three similar lines are not reason for abstraction" (linija 357). Sa 2 konzumenta to nije "premature abstraction" ali ni urgentno za refaktor.
- **REFACTOR-candidate flag:** Ako Story 2.8 (Tractor Listing sa HTMX filterima — ListView) takođe treba isti Case/When pattern za grupisanje specs, 3 mesta = jasan triplikat → extract u `apps/products/services.py:get_specs_queryset_with_section_annotation()` ili `apps/core/utils.py:case_when_section_annotation()`. Trenutno (Story 2.7) ne extraktujem — copy je pragmatičan.
- **Single source of truth:** Ako se ikad menja redosled sekcija (npr. Hidraulika postaje 2. umesto 3.), MORAJU se editovati TAČNO 2 mesta (Story 2.6 + Story 2.7); ovo je dokumentovano u SM-D7 da Code Review može pratiti (mirror invariant flag).
- **str(_(...)) coerce:** Story 2.7 koristi `Value(str(_("Motor")))` (eager coerce gettext_lazy → string AT REQUEST TIME) per Story 2.6 Completion Notes § Implementation choices worth noting — `Value(_(...))` direktno raise-uje `psycopg.ProgrammingError: cannot adapt type '__proxy__'` (psycopg ne zna kako da serijalizuje lazy proxy). Per-request konstrukcija unutar `get_queryset()` garantuje da LocaleMiddleware-aktiviran jezik bude resolvan u trenutku coerce-a.

### FR-20 hibrid logika (similar products) — view-layer resolution

Per PRD § 4.4 FR-20 spec:
- **Podrazumevani izvor:** automatski izbor 2-4 modela iz iste serije ili istog brenda
- **Admin override:** ako admin ručno označi listu sličnih modela, **admin override u celini zamenjuje automatske predloge**

Story 2.7 implementacija (vidi AC2 `get_context_data` source):

1. **Manual override path** (PRVI): query `ProductSimilar.objects.filter(product=current_product, related_product__is_published=True).select_related("related_product__brand").order_by("order", "id")[:4]` — **SM Fix iter 1 (C3/SM-D19):** `is_published=True` filter je SQL-level (WHERE clause na queryset-u), NE Python post-filter, da spreči edge case gde admin postavi 4 manual entries od kojih su 2 unpublished (slice-pa-filter daje 2 entries koji su truthy, ali auto fallback ne fire-uje pa korisnik vidi samo 2 kartice umesto očekivanih 4). SQL filter respektuje FR-20 admin-override semantiku — admin može uneti < 4 published similars (rezultat je manji od 4 ali još "manual" path); auto fallback fire-uje SAMO ako manual_list je potpuno prazan.
2. **Auto fallback path** (DRUGI, samo ako manual_list je prazan): `Product.objects.filter(brand=current.brand, is_published=True).exclude(pk=current.pk)`; ako `current.series_id` postoji, dodaj `.filter(series=current.series)` da uže matchuje istu seriju (ne samo isti brand); order `-created_at`; limit 4.
3. **Empty state path** (TREĆI, samo ako i auto je prazan — npr. izolovan proizvod u jedinstvenom brendu+seriji): `similar_products = []`; template `{% if similar_products %}` guard skip-uje celu sekciju.

**Deterministic ordering rationale (SM-D3):** auto fallback koristi `-created_at` (deterministic) umesto `?` (random) jer:
- **Cache stability:** ako Story 6.x dodaje page-level cache za product detail, random order bi pravio cache-bust po request-u (svaki request bi prikazao drugačiji set 4 sličnih)
- **Predictable UX:** korisnik koji refresh-uje stranu vidi iste predloge — manje konfuzno
- **Sortable:** najnovije dodati proizvodi imaju veći recency signal ("Možda i ovaj noviji model")
- Trade-off: less diverse rotation — moguć Story 9-10 polish za rotating sample (npr. weekly bucket seed sa cache key invalidation)

**Dokumentacija u Dev Notes:** SM-D3 (similar query strategy) — formal decision log entry.

### Brošura card — Story 2.4 dependency

Brošure card render-uje `responsive_picture brochure.cover_thumbnail_image` (NE direktan render kroz `sorl-thumbnail` ili druge transformacije). Story 2.4 deliverable je:

- `apps/media_pipeline/pdf_utils.py:generate_brochure_cover_thumbnail(pdf_field) -> ContentFile` — generiše JPEG thumbnail (240×320 portrait) iz prve strane PDF-a kroz `pdf2image.convert_from_bytes`
- `apps/media_pipeline/signals.py:handle_brochure_post_save` — post_save signal handler koji invoke-uje generator pri save-u ProductBrochure instance-a i upisuje rezultat u `ProductBrochure.cover_thumbnail_image` field

**Race condition consideration:** Story 2.4 signal je sync (no Celery — per project-context.md § Async/Sync linija 128); thumbnail je generisan PRE nego što `ProductBrochure.save()` vrati. Stoga `brochure.cover_thumbnail_image` MORA postojati po normalnom flow-u. Defensive `{% if brochure.cover_thumbnail_image %}` guard u template-u handluje edge cases (signal handler raise-ovao, ručno setovan brochure bez save-a koji bi triggerovao signal, itd.).

**File size labela** (`"X.X MB, PDF"`) — koristi Django built-in `{{ brochure.pdf_file.size|filesizeformat }}` filter koji vraća lokalizovan string. Sr lokalizacija u v1 koristi "MB"/"KB"/"B" abbreviation sa tačkom kao decimal separator (verify kroz live test); ako lokalizacija ne odgovara (npr. hu koristi drugo abbreviation), Story 9-10 polish može uvesti custom filter.

### Variant selektor — "no state change" UX (PRD FR-48)

PRD § 4.5 FR-48 spec eksplicitno: „Klik na karticu varijante otvara Lightbox sa zoom slikom (čista vizuelna inspekcija, **bez sporednih efekata** — ne menja stanje stranice i ne pokreće formu)."

**Implementacija (Story 2.7):**
- Klik na variant kartu = klik na `<a class="glightbox" href="{{ variant.image.url }}">` = GLightbox auto-pickup otvara modal sa zoom-om
- NEMA `data-variant-id` JS hook-a, NEMA URL fragment-a (`#variant-1`), NEMA hidden form submit-a, NEMA event listener-a koji menja React/Alpine state
- `data-gallery="product-variants"` (RAZLIČIT ID od `product-gallery` u AC4 main galeriji) — Lightbox prev/next se kreće SAMO unutar varijanti (ne meša se sa main galerijom)
- Story 2.5 `lightbox-init.js` dispatch-uje `coric:lightbox-open` na window kad se modal otvori; `testimonials-slider.js` (Story 2.6) sluša ovaj event i pauzira auto-advance dok je modal otvoren

**Test verifikacija (Subtask 12.3 AC8 test_variant_no_state_change_no_form):** markup audit:
- `<form>` element NE postoji u `_variants_selector.html`
- `data-variant-id` ili sličan state hook NE postoji
- URL ostaje identičan pre i posle klika (manual DevTools verify u Subtask 11.7)

### Reuse iz Story 2.6 (REUSE patterns + delta)

| Story 2.6 element | Story 2.7 reuse status | Razlog |
|---|---|---|
| `coric-product-card` BEM (`_series_grid.html`) | REUSE (similar products kartice + brand listing kartice — Story 2.6 svesni reuse plan SM-D9) | Identican linkable card pattern; `static/css/components/brand-listing.css` ostaje site-wide loaded |
| `coric-button`, `coric-button--primary` BEM | REUSE (brošure CTA, similar OPŠIRNIJE CTA) | Story 1.7 pill-button.css site-wide |
| `coric-pill-badge` BEM | NE REUSE (Story 2.7 nema "coming soon" stanje za pojedinačni proizvod — Story 8.6 admin može označiti `status="draft"` koji već vodi 404; ne treba pill-badge) | Out of scope |
| `_testimonials_slider.html` markup (brands/partials) | **MOVE u shared `templates/partials/_testimonials_slider.html`** + **opcioni `slider_id` kwarg** (SM Fix iter 1, C6/SM-D23 + SM Fix iter 2, I-iter2-2/SM-D27 — revidira originalni SM-D4 mirror-copy pristup) | 3-konzument scope (brand 2.6 + product 2.7 + home 3.1) + ARIA id collision + dual-maintenance burden opravdavaju refaktor sada; konzumira se kroz `{% include "partials/_testimonials_slider.html" with testimonials=... slider_id="..." %}` (SM-D22+D27) sa story-specific `slider_id` per call site |
| `statistic-counter.js` site-wide | NE KORISTI (product detail nema statistike — brand-level feature) | Defensive bail-uje silently |
| `testimonials-slider.js` site-wide | REUSE (defensive auto-detect `[data-testimonials-slider]` selektor; product detail page ga koristi) | Story 2.6 deliverable |
| Case/When section_rank + section_label per-request (SM-D14/D20) | REUSE u ProductDetailView | Vidi § "Section ordering pattern — REUSE" |
| `get_template_names()` override (SM-D19) | NE KORISTI u Story 2.7 (products nema coming-soon ekvivalent; `is_published=False` proizvodi vode 404 per SM-D3) | Out of scope |
| Hero card `partials/hero_overlay_card.html` (Story 1.7) | REUSE (mirror Story 2.6 SM-D2) | Generic partial, brand/product agnostic; prima title + bullets + brand_logo + variant |
| Wave Divider partial (Story 1.7) | REUSE (iznad slični-modeli sekcije, mirror Story 2.6 `_catalog_cta.html`) | Generic partial |
| Section Eyebrow partial (Story 1.7) | REUSE (svake sekcije eyebrow header) | Generic partial |
| direct anchor PDF download (SM-D22) | REUSE u brošure card (NE pill_button partial) | Story 1.7 pill_button ne podržava target/rel/download — mirror Story 2.6 SM-D22 rationale |

### Single h1 rule (B1 fix iz Story 2.6)

Story 2.6 Code Review iter 1 B1 fix uveo regression guard: `_hero_section.html` NE sme renderovati sopstveni `<h1>` jer `hero_overlay_card.html` partial već renderuje `<h1 class="coric-hero-overlay-card__title">{{ title }}</h1>` (linija 8 live source). Duplikat `<h1>` na strani krši WCAG 2.1 single-h1 best practice (akronim: WCAG 2.1 dozvoljava multiple h1 ako su sectioning-content scoped, ALI najbolja praksa je single-h1).

**Story 2.7 implementacija:**
- `_hero_section.html` (product version) **NE renderuje `<h1>`** — delegated kroz `hero_overlay_card.html` include
- `product_detail.html` **NE renderuje sopstveni `<h1>`** — outer wrapper je `<article>` ne semantic title element
- Sve podsekcije koriste `<h2>` (visible ili visually-hidden — npr. galerija ima skriveni `<h2 class="visually-hidden">Galerija slika</h2>` jer Section Eyebrow vec dovodi vizuelni naslov)
- Sekcije sa visible heading (Slični modeli "Možda će vas zanimati i", Brošure "Preuzmite brošuru", Variants "Varijante proizvoda") koriste `<h2>` (NE `<h1>`)
- Per-card titles (similar product name, variant name, brochure name) koriste `<h3>` (mirror Story 2.6 A1 fix heading hierarchy h2 → h3)

**Test verifikacija (Subtask 12.3 AC3 test_exactly_one_h1_on_page):** BeautifulSoup parse render-ovan HTML; `assertEqual(len(soup.find_all('h1')), 1)`; verifikuj da je TAJ `<h1>` baš product.name (text content match).

### Lightbox event integration (Story 2.5 contract)

Story 2.5 `static/js/lightbox-init.js` dispatch-uje 2 custom events na `window`:
- `coric:lightbox-open` — kad GLightbox modal `open` event okida (detail.instance payload)
- `coric:lightbox-close` — kad GLightbox modal `close` event okida (detail.instance payload)

Story 2.6 `static/js/testimonials-slider.js` (site-wide loaded) sluša oba event-a:
- `window.addEventListener('coric:lightbox-open', stopAuto)` — pauzira auto-advance dok je modal otvoren
- `window.addEventListener('coric:lightbox-close', startAuto)` — resume-uje auto-advance ako pre toga nije bio manualno pauziran

**Story 2.7 verifikacija (manuelni AC9 Subtask 11.7):**
1. Klik na galerija slike (`class="glightbox" data-gallery="product-{{ product.slug }}"`) → modal se otvori → `coric:lightbox-open` dispatch-uje → testimonials slider auto-advance se pauzira (verifikuj `setInterval` clear u DevTools Performance ili manualno time-watch da slider ne menja slajdove dok je modal otvoren)
2. Esc/klik-outside zatvara modal → `coric:lightbox-close` dispatch-uje → auto-advance resume-uje (verifikuj sledeći slajd posle ~6s)
3. Klik na variant karticu (`class="glightbox" data-gallery="product-variants"`) → ISTO ponašanje (data-gallery atribut samo grupiše Lightbox modal cycle, NE menja event semantiku — `coric:lightbox-open` se okida za bilo koji GLightbox modal otvori)

### `static/css/main.css` Edit DELTA

Story 1.7 + 1.8 + 2.5 + 2.6 je registrovalo niz `@import url('./components/...');` linija. Sintaksa je STROGO `url(...)` wrapper sa leading `./` (NE bare-string `@import './components/...';`).

Story 2.7 dodaje 3 nove linije na kraj postojećih @import linija (mirror Story 2.6 pattern):

```css
/* postojece linije ostaju netaknute */
@import url('./components/testimonials-slider.css'); /* Story 2.6 */
@import url('./components/product-detail.css');      /* NOVO Story 2.7 */
@import url('./components/product-gallery.css');     /* NOVO Story 2.7 */
@import url('./components/product-variants.css');    /* NOVO Story 2.7 */
```

### `static/css/components/brand-listing.css` Edit DELTA (SM-D21 cleanup)

Story 2.6 SM-D21 najavila: kad Story 2.7 uvede pravu ProductDetailView, 3 placeholder klase (`.coric-product-placeholder`, `.coric-product-placeholder__title`, `.coric-product-placeholder__message`) se sele iz `brand-listing.css` (privremeni dom u 2.6) u `product-detail.css` ili se brišu ako više nisu potrebne.

Story 2.7 Subtask 1.3 BRIŠE `_placeholder.html` template; sledom toga 3 BEM klase postaju dead code u `brand-listing.css`. **Subtask 10.5 UKLANJA tih 3 selektora iz `brand-listing.css`** (regression-safe — nema drugih konzumenata pošto je template obrisan). Ako Dev preferira da MIGRIRA klase u `product-detail.css` (umesto brisanja), to je acceptable ali u Story 2.7 nema render-ovog konzumenta, pa brisanje je čisto.

**Test verifikacija (Subtask 12.6 test_brand_listing_css_no_longer_has_placeholder_selectors):** grep `brand-listing.css` za `coric-product-placeholder` → 0 matches.

### `templates/base.html` Edit DELTA (uslovno — SM-D6)

**SM-D6 default:** pure CSS scroll-snap za galleryproduct carousel u v1 → NEMA novi JS modul → NEMA edit na `base.html`.

**SM-D6 alternative:** ako se odluči vanilla JS carousel (npr. prev/next + thumbnail klik), Story 2.7 kreira `static/js/product-gallery.js` i editujet `base.html`:

```html
<script src="{% static 'js/testimonials-slider.js' %}" defer></script>
<script src="{% static 'js/product-gallery.js' %}" defer></script>    <!-- NOVO Story 2.7 -->
{# Per-page scripts POSLE site-wide — sync init safe za Bootstrap komponente #}
```

**Default odluka (Story 2.7 SM): pure CSS scroll-snap.** Razlog: GLightbox već handluje prev/next + keyboard nav unutar Lightbox-a (Story 2.5 deliverable); na product detail strani galerija je SAMO "preview surface" — korisnik vidi 4-6 thumbnails u grid-u i klikne na bilo koju da otvori Lightbox carousel. Pure CSS scroll-snap dovoljan za mobile horizontal scroll (4 prsta swipe), CSS Grid za desktop. Vanilla JS carousel bi dupliralo Lightbox funkcionalnost (prev/next van Lightbox-a) — redundantno UX. Ako budući UX test pokaže da je dodatni carousel potreban, refaktor u Story 9-10 polish (paralel testimonials-slider.js pattern).

### Slika lazy loading strategy

Sve slike unutar product detail strane:
- Hero brand logo: defensively rendered kroz Story 1.7 hero_overlay_card partial (delegated; vidi Story 2.6 § Brand logo `format='PNG'` policy)
- Galerija slike: `{% responsive_picture image.image alt=... loading="lazy" sizes="..." %}` — sve lazy (galerija je ispod hero+opis fold-a)
- Brošure cover thumbnail: `{% responsive_picture brochure.cover_thumbnail_image ... loading="lazy" %}`
- Slični modeli kartice: `{% responsive_picture sim.main_image ... loading="lazy" %}`
- Testimonijal photos: `{% responsive_picture t.photo ... loading="lazy" %}`
- Variant images: `{% responsive_picture variant.image ... loading="lazy" %}`

Hero brand logo NIJE lazy (above-the-fold; eager load za LCP) — to je responsibility Story 1.7 hero_overlay_card partial-a.

### Brand logo `format='PNG'` policy reminder

Per Story 2.6 § Brand logo `format='PNG'` policy (Story 2.3 MP-D5 contract):
- **brand.logo** kroz `{% responsive_picture %}` MORA imati `format='PNG'` da preserve transparency (PNG default vs JPEG flatten-on-white)
- **product.main_image, ProductImage.image, ProductTestimonial.photo, ProductBrochure.cover_thumbnail_image, ProductVariant.image** — JPEG default je correct (fotografije bez transparency)

**Story 2.7 mesta gde se brand.logo renderuje:** SAMO unutar `_hero_section.html` (kroz delegation u hero_overlay_card.html partial). Hero_overlay_card.html (Story 1.7 partial) koristi direktno `<img src="{{ brand_logo }}">` (ne kroz responsive_picture) — vidi linija 5 live source. Stoga **Story 2.7 NE prosleđuje brand.logo kroz responsive_picture; delegated u Story 1.7 partial; `format='PNG'` ne primenjuje se** (kao Story 2.6 napomena za hero — delegated u 1.7).

### `prefers-reduced-motion` respect (mirror Story 2.6 § A11y)

**3 mesta gde prefers-reduced-motion mora biti respektovan u Story 2.7:**

1. **GLightbox modal animation** — već handled u Story 2.5 `static/css/components/lightbox.css` (`@media (prefers-reduced-motion: reduce)` blok); Story 2.7 ne dodaje custom — auto inherit
2. **`<details>/<summary>` accordion transitions** (`product-detail.css`): `@media (prefers-reduced-motion: reduce) { .coric-product-specs__accordion { transition: none !important; } }`
3. **Testimonials slider auto-advance** — već handled u `testimonials-slider.js` (Story 2.6); Story 2.7 ne dodaje custom — auto inherit

**Test plan:** Dev manuelni smoke (AC9 § prefers-reduced-motion test); automated test bi koristio Playwright `page.emulateMedia({reducedMotion: 'reduce'})` (Story 9.8 scope).

### Decision Log (SM-D*)

- **SM-D1:** No HTMX u 2.7. Story 4.3 (Model Inquiry Form) uvodi HTMX form submit na product detail; Story 2.7 ostavlja `{% block product_detail_inquiry %}{% endblock %}` extension tačku ali ne implementira formu. Rationale: izolovati 2.7 cilj (kanonski detail layout) od forme complexity-ja (validation + email send + rate limit).
- **SM-D2:** ProductDetailView NE koristi `get_template_names()` override (vs Story 2.6 SM-D19 koji koristi za coming-soon). Razlog: products nema "coming-soon" ekvivalent (Brand.is_coming_soon je brand-level flag; Product.is_published=False vodi 404 per SM-D3 — admin može pristupiti kroz admin preview u Story 8.6, ali public katalog je čist 404). Stoga je view jednostavniji od BrandDetailView (jedan template_name = "products/product_detail.html").
- **SM-D3:** `get_queryset()` filtruje `is_published=True` (sprečava javno renderovanje neobjavljenih proizvoda); auto fallback similar query takođe filtruje `is_published=True`; deterministic ordering `-created_at` u auto fallback (NE random) za cache stability i predictable UX. Alternativa (random sample): odbačena jer Story 6.x cache layer + UX consistency precepti su jači signal.
- **SM-D4:** ~~`_testimonials_slider.html` markup je KOPIJA iz Story 2.6~~ **REVIDIRANO u SM Fix iter 1 (C6 + C1 cluster) + SM Fix iter 2 (I-iter2-2/SM-D27).** Mirror-copy pristup ima 2 problema: (a) ARIA id collision (`brand-testimonials-title` bi se "leak-ovao" u product page kao stale grupisani identifikator); (b) silent zero-slides bug — Story 2.6 partial loopuje `{% for t in testimonials %}` (top-level kontekst), ali Story 2.7 view NEMA `testimonials` ključ u context-u (per AC2: sve podliste accessuju se kroz `product.<relation>.all`). Mirror copy bi tiho renderovao 0 slajdova na prvom run-u. **Nova odluka (vidi SM-D23 + SM-D24 + SM-D27):** Story 2.7 koristi (1) **shared partial move** u `templates/partials/_testimonials_slider.html` (single source-of-truth za sva 3 buduća konzumenta — brand 2.6, product 2.7, home 3.1) sa **opcionim `slider_id` kwarg-om** (default `"testimonials-title"`); i (2) **`{% include ... with testimonials=... slider_id=... %}` pattern** na include site-u (explicit context binding + story-specific ID). Brand prosleđuje `slider_id="brand-testimonials-title"` (backwards compat), product prosleđuje `slider_id="product-testimonials-title"` (story-specific future-collision guard). NEMA fajla `templates/products/partials/_testimonials.html` (mirror copy se NE kreira).
- **SM-D5:** Case/When section_rank + section_label pattern (Story 2.6 SM-D14/D20) REUSE bez extract. Razlog: 2 konzumenta (BrandDetailView + ProductDetailView) je još uvek "YAGNI threshold" per project-context.md; REFACTOR-candidate ako se naleti na 3. konzument (Story 2.8 Tractor Listing — verovatno NE jer to je listing flat + HTMX filter, ne render-uje akordion specs per-product). REFACTOR put: `apps/products/services.py:get_specs_queryset_with_section_annotation()` ili `apps/core/utils.py:case_when_section_annotation()`.
- **SM-D6:** Gallery carousel = **pure CSS scroll-snap (mobile) + CSS Grid (desktop)** u v1; NE vanilla JS carousel. Razlog: GLightbox već handluje prev/next + keyboard nav unutar modal-a; outer-carousel prev/next bi dupliralo funkcionalnost. Pure CSS je lighter (no JS payload, no event handlers, no defensive bail logic) i a11y-friendly (native scroll-snap je predictable). Trade-off: korisnici sa malim mobile ekranom moraju swipe-ovati horizontalno do svake thumbnail-e umesto klik prev/next; ako budući UX test pokaže problem, refaktor u Story 9-10 polish.
- **SM-D7:** Reuse Story 2.6 SM-D14/D20 patterns DUPLICATED u 2.7 (Case/When in 2 places: BrandDetailView.get_queryset i ProductDetailView.get_queryset). Mirror invariant flag dokumentovan ovde za Code Review tracking — ako se Motor/Transmisija/Hidraulika/Ostalo display order ikad menja, oba mesta moraju biti editovana.
- **SM-D8:** Single h1 rule (B1 fix iz Story 2.6) reuse-ovan u 2.7 — `_hero_section.html` NE renderuje sopstveni `<h1>` (delegated kroz hero_overlay_card.html partial koji već renderuje); test_exactly_one_h1_on_page (Subtask 12.3) je guard.
- **SM-D9:** Outer wrapper element u product_detail.html je `<article>` (NE `<div>` ni drugi `<main>`). Razlog: semantic HTML5 — proizvod je samostalan content piece koji ima smisao van konteksta strane (može biti syndicirano, share-ovano, RSS-ovano u budućnosti). `<article>` je idiomatski element za "self-contained composition" per HTML5 spec. Sub-sekcije su `<section>` (gallery, specs, similar, testimonijali, variants) ili `<aside>` (brochure, jer je peripheral ali povezan). `<main>` NIJE u 2.7 (base.html već renderuje `<main id="main-content">`; nested `<main>` je HTML5 violation per Story 2.6 nested-main guard).
- **SM-D10:** Variant selektor implementuje "no state change" UX (PRD FR-48): klik je TAČNO Lightbox zoom, ničega više. NEMA `data-variant-id` JS hook-a, NEMA URL fragment-a, NEMA forme. `data-gallery="product-{{ product.slug }}-variants"` (SM Fix iter 1 update — slug-scoped per Story 2-5 contract/I2; RAZLIČIT ID od main `product-{{ product.slug }}`) sprečava prev/next preklapanje. Test verifikuje markup audit (no `<form>` u partial, no `data-variant-id` hook).
- **SM-D11:** Brošure card koristi `{% if brochure.cover_thumbnail_image %}` defensive guard. Razlog: Story 2.4 post_save signal je sync (no Celery), pa thumbnail je generated PRE save() vraća — normalan flow garantuje `cover_thumbnail_image` postoji. Edge cases (signal raise-ovao, manual `Brochure.objects.create()` koji bi ipak triggerovao signal ali ne save, race condition u Storage backend-u) sve resolved kroz defensive guard; ako thumbnail nedostaje, card renderuje title + size + CTA bez slike (degradacija je acceptable; primary funkcionalnost je PDF download koji uvek radi).
- **SM-D12:** Brošure card uses `filesizeformat` Django built-in filter za file size labela ("X.X MB, PDF"). Razlog: lokalizovan na nivou Django (sr lokalizacija u v1 koristi "MB"/"KB" abbreviation sa tačkom kao decimal separator); custom filter bi bio premature abstraction. Story 9-10 polish može uvesti custom filter ako multi-locale formatting nije čisto kroz Django default (npr. hu može koristiti drugo abbreviation).
- **SM-D13:** Slični modeli sekcija ima visible heading "Možda će vas zanimati i" (NE skriveni). Razlog: UX clarity — korisnik treba da razume zašto se ova sekcija pojavljuje; "Slični modeli" Section Eyebrow nije dovoljno objašnjenje (može pomisliti "isti modeli" ili "konkurenti"). Visible h2 sa lepom porukom je friendly + clear (kao Amazon "Customers who bought this also bought").
- **SM-D14:** Akordion `<details open>` na PRVOJ sekciji (Motor) kroz `{% if forloop.first %}open{% endif %}` (NE per-section conditional `{% if section == "motor" %}`). Razlog: queryset je sorted po `section_rank` (Motor=1) — `forloop.first` pouzdano daje Motor sekciju. Per-section conditional bi bio fragile ako se ikad redosled promeni.
- **SM-D15:** Gallery i Variants koriste RAZLIČITE `data-gallery` ID-jeve (`product-{{ product.slug }}` vs `product-{{ product.slug }}-variants` — slug-scoped per Story 2-5 interface contract / I2 SM Fix iter 1; revidira originalni `product-gallery`/`product-variants` static names) da Lightbox prev/next ne preklapa između main galerije i variant kartica. GLightbox grupiše prev/next unutar istog `data-gallery` value-ja per Story 2.5 vendor defaults. Slug-scoping je forward-compat sa Story 3.1 Home koji bi mogao renderovati više proizvoda sa galerijama/varijantama na istoj strani (svaki dobija jedinstven scope).
- **SM-D16:** `_placeholder.html` template + `placeholder_view` FBV se BRIŠE (NE samo deprecate komentar). Razlog: dead code je tehnički debt; placeholder je bio C8 fix u Story 2.6 sa eksplicitnim "Story 2.7 zameni" napomenom (vidi Story 2.6 SM-D8). Brisanje je čisto. **Posledica (SM Fix iter 1, C2):** `apps/products/tests/test_placeholder.py` (4 tests iz Story 2.6 koji asertuju HTTP 200 + assertTemplateUsed('products/_placeholder.html') + noindex meta + single h1 'Stranica još nije dostupna') se ZAJEDNO BRIŠE — bez placeholder view+template ti testovi će regress-ovati svi. Backup nije potreban — testovi neće više biti relevantni posle DELETE-a. Replacement coverage: novi `apps/products/tests/test_placeholder_deleted.py` (Subtask 12.5) verifikuje da template fajl i `placeholder_view` symbol više ne postoje, i implicitno test_views_detail.py + test_urls_detail.py (Subtask 12.1+12.2) verifikuju da ista `/sr/proizvod/<slug>/` ruta sada serve-uje ProductDetailView (HTTP 200 za published, 404 za unpublished). TEA test count baseline: -4 (Story 2.6 placeholder tests) + ~32 novih = net +28 tests.
- **SM-D17:** Story 4.3 (Model Inquiry Form) integration tačka kroz `{% block product_detail_inquiry %}{% endblock %}` — placeholder block u product_detail.html koji Story 4.3 implementuje. Razlog: extension tačka je low-cost (1 linija template-a) i jasno signalizuje gde Story 4.3 može hook-ovati formu bez ponovnog editovanja Story 2.7 template-a; Story 4.3 SM može override-ovati block sa formu markup-om u svom create-story koraku.
- **SM-D18:** AC9 manual smoke check defer-uje se Mihasu (mirror Story 2.6 AC9 § final note). Automated tests (Subtask 12) pokriju programmatic requirements; manual Lighthouse + prefers-reduced-motion + FR-20 manual override/auto fallback paths + variant zoom no-state-change su out-of-scope za TEA/Dev automation (Story 9.8 Playwright UJ-1 + Story 9.9 a11y audit-gate scope).
- **SM-D19 (SM Fix iter 1, C3):** ProductSimilar manual override koristi **SQL-level `is_published=True` filter** umesto Python post-filter na sliced queryset. Razlog: edge case gde admin postavi 4 manual similars od kojih su 2 unpublished — slice-pa-filter daje 2 entries (truthy) i `if manual_list:` guard ne fall-back-uje na auto, pa korisnik vidi samo 2 kartice umesto očekivanih 4. SQL-level filter respektuje FR-20 "admin override u celini zamenjuje automatske predloge" — admin namera je 4 published similars (unpublished su filtrirani PRE slice-a, ne SAMO published su uzeti u obzir za slice, pa može isporučiti < 4 ako admin nije obezbedio dovoljno published kandidata; auto fallback i dalje firingu-je SAMO ako rezultantna lista je prazna — što je ispravno: admin override je "non-empty" intent signal). Query count unchanged (1 SQL upit sa dodatnim WHERE clause-om).
- **SM-D20 (SM Fix iter 1, C4):** `is_published` (boolean) je **SOLE PUBLIC-VISIBILITY GATE** za product detail strana. `Product.status` (TextChoices: draft/published/archived) je admin-only workflow metadata (NE javni gate). Razlog: `is_published=True + status='draft'` je obviously valid intermediate state u publishing pipeline (admin pripremi sadržaj kao draft → preview kroz `is_published=True` → finalizuje status kao published nakon QA-a); `is_published=True + status='archived'` je admin oversight (treba UI guard u future Story 8.6 ProductAdmin: disable `is_published` toggle kad `status='archived'`) — ali NE javni 404 trigger (regression risk za već-objavljene proizvode koje admin samo archive-uje za internal tracking). View koristi `Product.objects.filter(is_published=True)` u get_queryset(); NIJE dodato `status=Product.StatusChoice.PUBLISHED` filter. **Verify live:** `Product.StatusChoice` enum je u `apps/products/models.py:93-96` sa string values "draft"/"published"/"archived". **Future Story 8.6 napomena:** ProductAdmin UI mora dodati JS guard "disable is_published toggle when status='archived'" da prevenuje admin oversight. Test verifikacija u Subtask 12.2: 6 parametrizovanih kombinacija (is_published=True/False × status=draft/published/archived) sa očekivanim 200/404 izlazima koji potvrđuju `is_published` je sole gate.
- **SM-D21 (SM Fix iter 1, C5 + SM Fix iter 2, I-iter2-5 empirical pre-verify cross-ref):** `assertNumQueries` koristi **EXACT count (7)**, NE upper-bound (`<= 7`). Razlog: Django `assertNumQueries(N)` API je exact-match (raise-uje na bilo koji != N); upper-bound bi zahtevao `assert len(connection.queries) <= 7` što sakriva regresije ka više query-ja (npr. ako neko refaktoruje view i case-no-no dodaje N+1, test bi i dalje prošao sa npr. 12 ≤ 13). Exact count je strožiji guard. Trade-off: u environment-u sa django-debug-toolbar middleware aktivnim u test settings, test može pasti — ali test settings (`config/settings/test.py`) NE uključuje toolbar middleware (verify pre Subtask 12.2 RED phase). **Empirical pre-verify pattern (SM-D28):** literal je locked u Subtask 1.5(d) PRE TEA RED-phase — eliminisan "moving-target" test contract (Dev više ne sme mutirati literal POSLE pisanja testa).
- **SM-D27 (SM Fix iter 2, I-iter2-2 — slider_id kwarg future-collision guard):** Shared `templates/partials/_testimonials_slider.html` prima opcioni `slider_id` kwarg sa default vrednošću `"testimonials-title"`. Markup koristi `<h2 id="{{ slider_id }}">` umesto hardcoded ID. Svaki konzument MORA proslediti story-specific `slider_id` da preserve postojeću `aria-labelledby` reference i izbegne future ID collision:
  - **Story 2.6 brand_detail.html (line 22):** `{% include "partials/_testimonials_slider.html" with testimonials=testimonials slider_id="brand-testimonials-title" %}` — backwards compat (Story 2.6 testovi na `aria-labelledby="brand-testimonials-title"` ostaju validni, no mutation).
  - **Story 2.7 product_detail.html (sekcija 7):** `{% include "partials/_testimonials_slider.html" with testimonials=product.testimonials.all slider_id="product-testimonials-title" %}` — story-specific ID za izolaciju.
  - **Story 3.1 Home (future):** ako Home renderuje BOTH featured-brand snippet (koji nest-uje testimonials partial) AND page-level testimonials sekciju, oba moraju imati distinkt `slider_id` (npr. `slider_id="home-featured-brand-testimonials-title"` + `slider_id="home-page-testimonials-title"`) — `default:"testimonials-title"` samo fallback za standalone usage ili test render bez kwarg-a. Razlog: bez kwarg-a, dva include-a na istoj strani bi generisala duplikat ID-jeve (krši WCAG SC 4.1.1) i `aria-labelledby` selektor bi nedeterministički pokazivao na prvi match.
- **SM-D28 (SM Fix iter 2, I-iter2-5 — empirical query count pre-verify; SM Fix iter 3 IMPROVEMENT-NEW1 — probe pattern correctness rationale):** Query count literal (trenutno 7 per AC1 enumeracija) MORA biti empirically verifikovan u Subtask 1.5(d) **PRE** Subtask 12 (TEA RED-phase). Razlog: SM-D21 originalno dozvoljava "Dev update-uje literal ako empirijski daje 6 ili 8" — ali ta licenca u AC1 prose-u (line 110 originalno: "Ako empirijski count u Subtask 1.4 smoke check pokaže drugačiji broj... Dev update-uje literal") kreira moving-target test contract: TEA piše `assertNumQueries(7)` u RED phase → Dev otkriva empirijski 8 u GREEN phase → Dev menja AC2 + test u GREEN phase = "test was modified after RED to make GREEN pass" anti-pattern. Rešenje: literal je locked u Subtask 1.5(d) PRE TEA pisanja testa; ako se empirically pokaže 6 ili 8, spec mutacija (AC1 prose + AC2 docstring + Subtask 12.2 test number) izvršava se u Subtask 1.5 phase (RED-phase još nije počeo). Validation gate: Subtask 12.2 ne sme započeti pre Subtask 1.5 completion. Dev orchestrator (Step 3) MORA enforcovati redosled.
  - **Probe pattern correctness (SM Fix iter 3, IMPROVEMENT-NEW1 — why `CaptureQueriesContext` umesto `settings.DEBUG=True` mutacije):** Subtask 1.5(d) shell snippet KORISTI `django.test.utils.CaptureQueriesContext(connection)` context manager — NE runtime `settings.DEBUG = True` + `reset_queries()` pattern. Razlozi:
    - **Django `BaseDatabaseWrapper.force_debug_cursor` je postavljen u trenutku `.connect()` poziva** na osnovu `settings.DEBUG` vrednosti AT CONNECT TIME, NE per-query. Mid-process mutacija `settings.DEBUG = True` u `manage.py shell` NE flip-uje retroaktivno taj flag na već-otvorenoj konekciji — `connection.queries` lista može tiho ostati prazna iako su request-i izvršeni. Probe bi vratio `len(connection.queries) == 0` (false negative) i SM-D28 hard gate (literal locked PRE TEA RED-phase) bi bio podriven.
    - **`CaptureQueriesContext` eksplicitno postavlja `connection.force_debug_cursor = True` na entry-ju** (snima prethodnu vrednost), izvršava captured block, i restore-uje originalnu vrednost na exit-u (čak i pri exception-u kroz `__exit__`). Ovo je Django-native preporučeni pattern iza scene za `TransactionTestCase.assertNumQueries` — robustan, idempotent, safe za shell-based one-off probe.
    - **Bonus benefit:** radi nezavisno od `settings.DEBUG` vrednosti — production-mode probe (DEBUG=False) takođe radi, što omogućava staging/CI environment query count verifikaciju bez DEBUG side-effect-ova (template debug pages, security warnings, etc.).
    - **Inner-content scope:** SAMO inner Python content (između `python manage.py shell -c "` i closing `"`) je promenjen; outer docker exec wrapper (`docker compose -f compose/local.yml exec django uv run python manage.py shell -c "..."`) ostaje identičan — `CaptureQueriesContext` import je dostupan u standardnoj Django test utils biblioteci (no extra dep).
- **SM-D22 (SM Fix iter 1, C1):** Testimonials partial integration koristi **`{% include ... with testimonials=product.testimonials.all %}` pattern** (explicit context binding na include site-u). Razlog: shared partial (per SM-D23) referencira `{% for t in testimonials %}` na top-level kontekst varijabli `testimonials` (Story 2.6 brand view već postavlja `testimonials = brand.testimonials.all()` u get_context_data); product view NEMA ovaj ključ (per AC2 "context surface minimization"), pa direct include bi tiho renderovao 0 slajdova. `{% include ... with x=y %}` Django sintaksa preimenuje context varijablu lokalno za include scope (per Django docs), bez nepotrebnog duplikata context surface-a u view layer-u. Explicit binding na call site čini ugovor između include-a i partial-a vidljivim u template-u (lakše za code review).
- **SM-D23 (SM Fix iter 1, C6 + SM Fix iter 2, I-iter2-2 superseded by SM-D27 kwarg pattern):** `_testimonials_slider.html` partial se **PREMEŠTA** iz `templates/brands/partials/_testimonials_slider.html` u **shared `templates/partials/_testimonials_slider.html`** (single source-of-truth). Razlog: 3 očekivana konzumenta (Story 2.6 brand listing, Story 2.7 product detail, Story 3.1 home — open question #4 prelazi u "in-flight refactor" odluku). Po SM-D4 originalu mirror copy je bio acceptable u v1 sa YAGNI rationale ("3 lines nije reason za abstraction"); međutim ARIA id collision (`brand-testimonials-title` selektor koji bi se "leak-ovao" na product page) + dual maintenance burden + očekivana 3-konzumenta scope nakratko opravdavaju refaktor SADA. **SM Fix iter 1 originalan plan** (rename `id="brand-testimonials-title"` u generičan `id="testimonials-title"` + Story 2.6 test file EDIT za novi ID) je **REVIDIRAN u SM Fix iter 2 (I-iter2-2 / SM-D27):** umesto rename-a, partial prima opcioni `slider_id` kwarg sa default `"testimonials-title"`. Svaki konzument prosleđuje story-specific ID: brand_detail.html prosleđuje `slider_id="brand-testimonials-title"` (backwards compat → Story 2.6 testovi ostaju validni, no mutation), product_detail.html prosleđuje `slider_id="product-testimonials-title"` (story-specific). Subtask 9.0 (nova) izvršava potez; Subtask 9.1 (originalna "mirror copy") se SKIDA i zamenjuje subtask-om koji wired-uje shared partial kroz `{% include ... with testimonials=... slider_id=... %}` (per SM-D22+D27). Story 2.6 brand_detail.html linija 21 `aria-labelledby="brand-testimonials-title"` OSTAJE NETAKNUTA (only linija 22 include path + slider_id kwarg se EDITUJE); test file `apps/brands/tests/test_templates_brand_listing.py` OSTAJE NETAKNUT. Story 2.6 file (ili sprint-status log entry) i `_bmad-output/implementation-artifacts/2-6-interface-contract.md` dobijaju deferred-with-docs nadogradnju "Story 2.7 je refaktorisao testimonials partial location" — partial physical move se odigrava u Step 3 GREEN phase (Dev, ne SM).
- **SM-D24 (SM Fix iter 1, I1 + SM Fix iter 2, I-iter2-3):** Brošure card heading koristi **`{% blocktranslate count counter=... %}{% plural %}{% endblocktranslate %}`** za pluralizaciju ("Preuzmite brošuru" / "Preuzmite brošure" u zavisnosti od broja brochures); brochures queryset slice-uje na **MAX 5** entries (`product.brochures.all()[:5]`) da prevenuje admin oversight (renderovanje 20+ cards je UX katastrofa i ruši Lighthouse Performance). Razlog: singular "brošuru" (akuzativ) je gramatički netačno za N>1 ("brošure" je akuzativ plural u srpskom); slice je defensive guard koji ne ograničava admin slobodu da uvodi više brošura (može biti više u DB ali se renderuju top 5 — pristup ka stratezijama za 6+ entries je out-of-scope Story 8.6/9.10). View-layer pre-computation brochure_size_label (per I8) takođe slice-uje na 5. **NAPOMENA SM-D24 / I-iter2-3 — Serbian nplurals=3 translator authoring:** `locale/sr/LC_MESSAGES/django.po` (live verifikovano linija 19) deklariše `Plural-Forms: nplurals=3; plural=(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);` — Django `{% blocktranslate count %}{% plural %}{% endblocktranslate %}` template syntax obezbeđuje samo 2 source string-a (singular + plural), ALI `msgmerge` emituje 3 `msgstr[0/1/2]` slot-a za sr lokalu koje translator MORA popuniti nezavisno. Posle `just makemessages`, Dev MORA popuniti SVA 3 msgstr-a za brochure heading key (i ostale plural key-ove dodate u Story 2.7):
  - **msgstr[0]** = `"Preuzmite brošuru"` (singular form, n%10==1 && n%100!=11 — npr. 1, 21, 31, 101)
  - **msgstr[1]** = `"Preuzmite brošure"` (paucal/few form, n%10∈[2,4] && n%100∉[10,20] — npr. 2, 3, 4, 22, 23, 24)
  - **msgstr[2]** = `"Preuzmite brošura"` (plural genitive form, ostalo — npr. 0, 5, 6, 7, 8, 9, 10, 11-20, 25-30)
  Ako Dev OSTAVI msgstr[2] prazan, Django fall-back ponašanje za prazne msgstr-ove u sr lokali rezultuje sa pogrešnim plural form za N=5+ (gramatički netačno: "Preuzmite brošure" za N=5 → treba genitiv "Preuzmite brošura"). Subtask 7.3 (NOVA, ispod) obezbeđuje verifikaciju.
- **SM-D25 (SM Fix iter 1, I3):** "PDF" acronym u brošure size label se **WRAP-uje kroz `{% translate "PDF" %}`** iako je acronym identičan u sve 3 lokale (sr/hu/en). Razlog: project-context.md § A11y must-haves zahteva sve user-facing strings kroz gettext. Wrap je no-op runtime cost, ali maintains policy compliance + buduća sloboda za locale-specific format ("PDF dokument" u en proširenom prevodu, npr.). Alternativa (acronym exception) bi otvorila precedent za "skip translation kad acronym je univerzalan" što erodira policy.
- **SM-D26 (SM Fix iter 1, I8 + I9 + SM Fix iter 2, I-iter2-4 broadened scope):** Brošure card defensive guards za file system error i partial-state record: (a) `pdf_file.size` triggeruje filesystem stat call per render i može raise-ovati **4 documented exception paths**: `FileNotFoundError` (fajl nedostaje na disk-u, race condition), `OSError` (permission denied, disk corruption, FS error), `ValueError` (FieldFile.name je None ili unsaved instance — admin shell create() bez file upload-a), `SuspiciousFileOperation` (Django storage path traversal guard — Storage backend security check za file path-ove van MEDIA_ROOT-a). View-layer pre-compute `brochures_list` sa try/except oko `b.pdf_file.size` koji catches sva 4 exception type-a (fallback 0 → renderuje "0 bytes"); (b) `cover_thumbnail_image` ImageField sa pristupom kroz `{% if brochure.cover_thumbnail_image %}` može biti truthy čak i kad fajl ne postoji (partial-state record sa `.name=""` u edge case-u); guard se proširuje na `{% if brochure.cover_thumbnail_image and brochure.cover_thumbnail_image.name %}`. Razlog: graceful degradation > render exception (a 500 error stranica je mnogo lošija UX nego "0 bytes" labela ili missing slike). **Rationale za broadened exception scope (I-iter2-4):** Django `FieldFile.size` Python source level kombinuje stat() call (može raise FileNotFoundError/OSError) sa Storage backend abstraction (svaki backend može raise različite exception type-ove — npr. `default_storage` može raise SuspiciousFileOperation ako path traverse-uje, a buduća S3 migracija u Story 9-x deployment scope dodaje `boto3.exceptions.ClientError`). Broad catch je opravdan jer alternativa je 500 error iz view layer-a; defensive fallback (size_bytes=0) renderuje gracefully sa "0 bytes" labelom — UX trade-off prihvatljiv. NAPOMENA: ValueError handling pokriva i `FieldFile.name is None` slučaj koji se javlja kad admin kreira `ProductBrochure(product=p)` instance bez `.pdf_file = ...` set-a (shell context); production admin form workflow ovo neće triggerovati jer `pdf_file` je required field. Future Story 9-x (S3/cloud storage) — ako boto3 ClientError dodatak postane potreban, exception tuple se proširuje u tom commit-u; trenutno cap na 4 stdlib + Django path-ova.

### Dependencies note (KRITIČNO za Dev)

Story 2.7 STROGO zavisi od ovih prethodnih story-ja (sve `done` per sprint-status.yaml 2026-05-30):
- **Story 2-1:** Brand, Series, Category, Subcategory modeli — Story 2-7 koristi `product.brand.logo`, `product.brand.name`, `product.brand.brand_color`, `product.series` (FK relation, opciono)
- **Story 2-2:** Product i 6 related modela (ProductImage, ProductVariant, ProductSpecification, ProductBrochure, ProductTestimonial, ProductSimilar) — sve verifikovano live (vidi § Model discovery)
- **Story 2-3:** `{% responsive_picture %}` template tag iz `media_pipeline.templatetags.media_tags` — Story 2-7 koristi za sve slike sa `loading="lazy"`
- **Story 2-4:** `ProductBrochure.cover_thumbnail_image` auto-gen kroz post_save signal — Story 2-7 brošure card render-uje cover thumbnail kroz `responsive_picture`
- **Story 2-5:** GLightbox vendor + `lightbox-init.js` + `coric:lightbox-open/close` event kontrakt — Story 2-7 koristi `class="glightbox"` selektor pattern za gallery + variants; testimonials slider auto-advance pauzira na event (kroz site-wide JS iz Story 2.6)
- **Story 2-6:** `coric-product-card` BEM (similar products kartice reuse); `testimonials-slider.js` site-wide (testimonials partial reuse); Case/When section_rank pattern (REUSE u ProductDetailView SM-D5/D7); `coric-button` direct anchor pattern za PDF download (SM-D22 reuse u brošure card)

Sve prethodne story-je su `done` u sprint-status.yaml (verifikovano 2026-05-30); Story 2-7 je spremna za RED phase (TEA) → GREEN phase (Dev).

### Cross-boundary import — NEMA novog izuzetka

Story 2.7 `apps/products/views.py` importuje SAMO iz `apps.products.models` (same-app, no boundary issue) + potencijalno `apps.brands.models` (kroz `Product.brand` FK queries — natural `products → brands` direction per project-context.md § Cross-boundary import linija 626).

**NIKAKAV edit na `_bmad-output/project-context.md` nije potreban** (RAZLIČITO od Story 2.6 koja je dodala explicit izuzetak za brands → products view-layer coupling). Story 2.7 sledi prirodnu zavisnost.

Subtask 1.6 verifikuje ovaj status (no-op u srećnom slučaju). (Subtask 1.5 ranije, renumerisan u SM Fix iter 1 — C2 dodao novu 1.4 za test DELETE pa su 1.4→1.5 i 1.5→1.6.)

### Open questions / warnings za Validation (Step 2)

1. **hu translation gap (PREREQ za AC5 hu test):** mirror Story 2.6 § Open Question — `locale/hu/LC_MESSAGES/django.po` trenutno može sadržati `msgstr ""` za "Motor", "Transmisija", "Hidraulika", "Ostalo"; ako da, TEA test koji asertuje hu prevode je `xfail` dok Dev ne popuni .po fajl. Verify live pre Subtask 12.4. Ako prevodi su already populated (možda Story 2.6 Dev ih je dodao u sklopu fix-a), test je solid pass.
2. **Lighthouse Performance score lower target (≥ 75 vs ideal ≥ 90)** — mirror Story 2.6 § Open Question — image pipeline u 2.3 koristi JPEG (no WebP/AVIF), Story 2.7 ima više slika nego brand listing (galerija + variants + brošura) pa Performance može biti niži. Story 9.10 Polish pass dovešće na ≥ 90.
3. **Multi-locale URL slug-ovi** — URL segment "proizvod" je hardcoded srpski; Story 6.6 scope (mirror Story 2.6 § Open Question #2).
4. ~~**`_testimonials.html` mirror copy iz Story 2.6 — refaktor candidate**~~ **RESOLVED u SM Fix iter 1 (C6/SM-D23):** umesto mirror copy, Story 2.7 izvršava shared partial MOVE — `templates/brands/partials/_testimonials_slider.html` → `templates/partials/_testimonials_slider.html` (shared), uz generičan rename `id="brand-testimonials-title"` → `id="testimonials-title"`. Story 2.6 brand_detail.html dobija 1-line EDIT (Subtask 9.0c) za novu putanju + ID; Story 2.6 test `apps/brands/tests/test_templates_brand_listing.py:129-130` dobija 1-line EDIT za rename verify-uje. Story 3.1 (Home) je sada 3. konzument bez dodatnog refaktora.
5. **SM-D6 carousel decision (pure CSS vs vanilla JS)** — default je pure CSS scroll-snap; ako UX testing (Story 9.x) pokaže da je vanilla JS carousel potreban, dodaje se Story 9-10 polish.
6. **`filesizeformat` lokalizacija** — Django built-in koristi tačku kao decimal separator u sr ("2.4 MB"); ako lokalizacija ne odgovara per locale, Story 9-10 polish može uvesti custom filter.
7. **(SM Fix iter 2, I-iter2-8 STYLE — log only, NO FIX)** 4-of-4 unpublished similars edge case: admin može uneti EXACTLY 4 manual `ProductSimilar` entries gde su SVI 4 unpublished. Trenutna SM-D19 SQL-filter logika u `get_context_data()` daje `manual_list = []` (sva 4 filtered out) → fallback na auto path firingu-je → korisnik vidi auto fallback similar models umesto admin-namernog "no similars" intent-a (ako je admin namera bila "stage 4 similars all unpublished za buduće QA review"). Trade-off: SM-D19 prioritizuje "user-visible non-empty similars" preko "admin intent fidelity" — što je ispravan default jer empty similars sekcija + auto fallback su graceful degradation, a 4-of-4 unpublished je obviously partial-state oversight koji admin treba ispraviti (publish similars ili obrisati ProductSimilar entries). **Razlog za log-only (no fix u Story 2.7):** ne dodaje se Subtask 12.2 test za ovaj edge case jer (a) reproduces već-postojeću SM-D19 design intent (defer fix do Story 8-6 admin UI guard "warn admin: all 4 manual similars are unpublished; please publish at least 1 or remove"); (b) automated test bi zaključao trenutno ponašanje kao "spec" što ograničava Story 8-6 da redefiniše semantiku; (c) Code Review može flagovati ako Dev empirijski naleti na slučaj. **Action:** defer fix do Story 8-6 ProductSimilar admin UI guard (form-level validation ili admin save_model hook koji prikazuje warning ali ne blokira save).

## Completion Notes

_(Ova sekcija se popunjava od strane Dev agenta u Step 3 GREEN phase — Story 2.7 status promenjen draft → review nakon Dev implementacije.)_

_Template (mirror Story 2.6 Completion Notes format):_

**Status:** GREEN phase završen; status promenjen draft → review; sprint-status.yaml ažuriran ready-for-dev → review.

### Test results
- **Total Story 2.7 tests: ~55** (X PASSED + Y XFAILED — expected hu-locale xfail per Subtask 12.4 / SM-D5; SM Fix iter 2 baseline: -4 deleted placeholder tests + ~55 novih = net +51; recount per I-iter2-7: 5 (Subtask 12.1) + 13 (Subtask 12.2) + 27 (Subtask 12.3) + 1 (Subtask 12.4) + 4 (Subtask 12.5) + 4 (Subtask 12.6) = 54 method count; +1 if testimonials aria id test je split u positive/negative methods → 55)
- Run pod `docker compose -f compose/local.yml exec django uv run pytest apps/products/tests/test_views_detail.py apps/products/tests/test_templates_detail.py apps/products/tests/test_locale_specs.py apps/products/tests/test_placeholder_deleted.py tests/test_product_detail_static_assets.py` → exit 0
- Full module regression: `apps/products/tests/` = X passed, Y skipped (no regressions vs Story 2.2/2.6 baseline)

### Files created (~12-13 NOVO; SM Fix iter 1 update)
- `templates/products/product_detail.html`
- `templates/products/partials/_hero_section.html`
- `templates/products/partials/_description.html`
- `templates/products/partials/_gallery_carousel.html`
- `templates/products/partials/_specs_accordion.html`
- `templates/products/partials/_brochure_card.html`
- `templates/products/partials/_similar_products.html`
- ~~`templates/products/partials/_testimonials.html`~~ — **NIJE kreiran (SM-D23 shared MOVE umesto mirror copy)**
- `templates/products/partials/_variants_selector.html`
- `templates/partials/_testimonials_slider.html` (MOVE destination — fizički NEW iz brands/partials/ premeštanja per SM-D23)
- `static/css/components/product-detail.css`
- `static/css/components/product-gallery.css`
- `static/css/components/product-variants.css`
- (opciono) `static/js/product-gallery.js` (samo ako SM-D6 odluka revidirana ka vanilla JS carousel)

### Files modified (7-8 EDIT; SM Fix iter 1+2 update)
- `apps/products/views.py` (REPLACE placeholder_view → ProductDetailView)
- `apps/products/urls.py` (1-line: placeholder_view → ProductDetailView.as_view())
- `static/css/main.css` (+3 `@import url('./components/...')` linije)
- `static/css/components/brand-listing.css` (-3 placeholder selektora — SM-D21 cleanup)
- `templates/brands/brand_detail.html` (1-line edit linija 22 include path + `slider_id="brand-testimonials-title"` kwarg — SM-D23+D27 shared partial move sa backwards compat; linija 21 `aria-labelledby="brand-testimonials-title"` OSTAJE NETAKNUTA per SM-D27)
- `_bmad-output/implementation-artifacts/2-6-interface-contract.md` (linija 207 — include path + slider_id kwarg note + historical refactor footnote per I-iter2-1 cascade sync; SM-D23/D27)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (last_updated polje — cross-story cascade tracking napomena per I-iter2-1)
- (opciono) `templates/base.html` (+1 script tag samo ako SM-D6 revidirano)
- ~~`apps/brands/tests/test_templates_brand_listing.py`~~ — **SKINUT iz EDIT liste** (SM Fix iter 2, SM-D27 backwards compat — assertion ostaje validna jer brand_detail.html eksplicitno prosleđuje `slider_id="brand-testimonials-title"` kwarg).

### Files deleted (3 DELETE; SM Fix iter 1 update — includes MOVE source + test_placeholder.py)
- `templates/products/_placeholder.html`
- `templates/brands/partials/_testimonials_slider.html` (MOVE source — fizički DELETE iz brands/partials/ posle premeštanja u shared partials/ per SM-D23)
- `apps/products/tests/test_placeholder.py` (4 tests koji asertuju placeholder rendering — orphaned posle Subtask 1.1+1.3 source DELETE per C2/SM-D16)

### Implementation choices worth noting
- **Brochure size label — filesizeformat (reverted iz Python pre-compute):** Originalna Dev rationale o ćirilici pod sr locale-om bila je delimično tačna (`filesizeformat` vraća "бајтова" za < 1KB, ali Latinica "X,X KB" / "X,X MB" za >= 1KB). U code-review iter 1 odluka revidirana: vratiti se na Django built-in `{{ entry.size_bytes|filesizeformat }}` jer (1) realističke brošure su uvek >= 1KB → Latinica garantovana; (2) bypass-uje Django i18n nepotrebno; (3) hardcoded `.1f` ignoriše sr/hu comma decimal konvenciju. Test factory `_MINIMAL_PDF_BYTES` padded sa PDF comment-om do >= 1024 bytes da reflect realistic brochure size.
- **Wave divider position za `_similar_products.html`:** premešten iz partial-a (gde je bio render-ovan UNUTAR `<section id="product-similar">`) u `product_detail.html` PRE `<section>` opener-a, da zadovolji test `test_wave_divider_rendered_above_similar_section` koji asertuje wave divider markup pozicija < `id="product-similar"` pozicija. (Vidi SM-D30 ispod.)
- **Cross-story cascade (Subtask 9.0 a-f) primenjen u celosti:** testimonials_slider.html MOVED iz `brands/partials/` u `templates/partials/` + parametrized sa `slider_id` kwarg; brand_detail.html line 22 include EDIT prosleđuje `slider_id="brand-testimonials-title"` (backwards compat — Story 2.6 tests pass without modification); product_detail.html include prosleđuje `slider_id="product-testimonials-title"`; 2-6-interface-contract.md L207 i sprint-status.yaml `last_updated` EDITs primenjeni.

### Code Review Iteration 1 (2026-05-30) — 7 fixes applied
- **S1 (SECURITY MEDIUM) — Stored XSS via GLightbox innerHTML sink:** Dodato `|striptags` na sve admin-controlled field interpolacije unutar `data-glightbox="..."` atributa (gallery_carousel.html line 9, variants_selector.html line 11). GLightbox parsira `data-glightbox` microformat i assignuje `title`/`description` vrednosti u `element.innerHTML` (sink); `|striptags` defense-in-depth uklanja HTML tagove iz alt_text/variant.name/variant.code pre interpolacije.
- **B1 (BUG HIGH) — Brochure size_label deviation reverted:** Uklonjen view-side `size_label` pre-compute iz `apps/products/views.py` lines 117-133; restored `{{ entry.size_bytes|filesizeformat }}` u `_brochure_card.html` line 16. Test factory `_MINIMAL_PDF_BYTES` padded >= 1024 bytes (komentar prefix `%` + 600 `x` bytes) da garantuje Latinica KB output. Defensive try/except guard za pdf_file.size ostaje (SM-D26).
- **B2 (BUG LOW) — Variants visible "Kod:" prefix:** `_variants_selector.html` linije 19+28 sada renderuju `{% translate "Kod" %}: {{ variant.code }}` (umesto bare `{{ variant.code }}`); aligned sa AC8 spec za sighted user clarity (aria-label i data-glightbox već imaju "Kod:" prefix).
- **P1 (PROCESS BLOCKING) — i18n .po extraction:** Pokrenut `makemessages -l sr -l hu -l en`; svi novi Story 2.7 strings (Preuzmite brošuru, OPŠIRNIJE, Kod, PDF, Galerija slika, itd.) extrahovani u `locale/{sr,hu,en}/LC_MESSAGES/django.po`. Popunjeni svi 3 nplurals=3 msgstr slot-a za "Preuzmite brošuru" plural u sr locale-u (msgstr[0]="brošuru", msgstr[1]="brošure", msgstr[2]="brošura"). hu/en msgstrs ostaju prazni — per project locale fallback policy (project-context.md line 208) padaju na sr. `compilemessages` clean (no warnings).
- **A1 (ARCHITECTURE MEDIUM) — _hero_section.html duplication collapsed:** Predcomputed `hero_variant` (blue/green based on brand_color) i `hero_brand_logo_url` u `get_context_data()`; `_hero_section.html` redukovan sa 4 grane (brand_color × has_logo) na single `{% include "partials/hero_overlay_card.html" with ... %}`. Aligned sa project-context.md §347 "NIKAD logic u template-u koji može biti u view-u".
- **A2 (ARCHITECTURE LOW) — Magic px tokens introduced:** Dodato 3 nova tokena u `static/css/tokens.css`: `--card-min-width-sm: 220px` (variants), `--card-min-width-md: 240px` (similar), `--card-min-width-lg: 280px` (brochures). Sve 3 `minmax(Xpx, 1fr)` deklaracije u product-detail.css i product-variants.css zamenjene `var(--card-min-width-*)`.
- **R1 (REFACTOR LOW) — Wave divider position:** Decision recorded as SM-D30 (vidi novu sekciju ispod). Wave divider ostaje u `product_detail.html` PRE `<section id="product-similar">` da zadovolji test position assertion.

### New Decisions (SM Fix iter / Code-Review iter 1)
- **SM-D29 (Security defense-in-depth):** Sve admin-controlled field interpolacije unutar `data-glightbox="..."` atributa MORAJU koristiti `|striptags` filter. Django attribute escape encoduje entities u atribut, ali browser decoduje pre nego što GLightbox čita `element.dataset.glightbox` i prosleđuje string u `element.innerHTML` sink → script execution risk bez striptags. Applies to: title, description, bilo koji microformat value koji potiče iz user/admin input-a.
- **SM-D30 (Wave divider placement):** Wave divider include premešten iz `_similar_products.html` partial-a u `product_detail.html` parent template PRE `<section id="product-similar">` opener-a (umesto unutar partial-a). Rationale: test `test_wave_divider_rendered_above_similar_section` asertuje da wave divider markup pozicija < `id="product-similar"` pozicija; držanjem inside partial-a uz `<section>` wrapper komplikuje partial signaturu. Partial više nije fully self-contained ali ostaje atomic u svom rendering scope-u. Buduće story consumers `_similar_products.html` partial-a MORAJU wrap sa svojim wave divider-om ako visual continuity je potrebna.

### Test modifications
- (GREEN phase) Nijedna. Sve TEA RED-phase testove su zadovoljene fixovima u production code-u.
- (Code-Review iter 1) `apps/products/tests/factories.py` `_MINIMAL_PDF_BYTES`: padded sa `b"%" + b"x" * 600 + b"\n"` (PDF comment) da total veličina pređe 1024 bytes. Razlog: Django `filesizeformat` pod sr locale vraća Cyrillic "бајтова" za < 1KB; padding garantuje Latinica "X,X KB" output (matchuje regex `\d+(?:[.,]\d+)?\s*(bytes|byte|KB|MB|GB)` u `test_brochure_size_label_uses_filesizeformat`). Realistic brochures su uvek >= 1KB pa je test više reprezentativan production-a.

### Unfixable issues
- Nijedna.

### AC status
- AC1 URL routing + 404 + APPEND_SLASH: **implemented** (5 tests pass)
- AC2 view + queries + context: **implemented** (10 methods / ~17 invocations pass; assertNumQueries(7) manual path lock per SM-D28)
- AC3 page structure + landmarks: **implemented** (5 tests pass — single h1, single main, product-specific aria id)
- AC4 gallery + GLightbox: **implemented** (3 tests pass — slug-scoped data-gallery)
- AC5 specs accordion: **implemented** (4 tests pass + 1 xfail hu locale per SM-D20)
- AC6 similar products (FR-20 hybrid): **implemented** (4 tests pass — manual SQL filter per SM-D19, auto fallback)
- AC7 brochure card: **implemented** (7 tests pass — multi-brochure, plural blocktranslate, PDF translate, defensive size + cover guards)
- AC8 variants selector: **implemented** (4 tests pass — distinct data-gallery, no state change)
- AC9 manual Lighthouse smoke: **pending Mihas** (xfail placeholder)

### Lint status
- `ruff check apps/products/ apps/brands/`: 6 auto-fixed; **3 F841 remaining** u TEA test fajlovima (`apps/products/tests/test_templates_product_detail.py` linija 638-640 `anchor_pattern` + 2x `product` unused vars); deferred to TEA Step 4 review (test scope, out of Dev edit boundary per workflow).
- `djade --check` direktorijum-mode neuspeo (CLI očekuje fajl-target); per-file run može Step 4 pokrenuti ako format issues iskoče.

### Test results
- **Total: 236 collected** (231 passed + 2 skipped + 3 xfail + 0 failed + 0 errors).
- Story 2-6 regression: ZERO (brand listing tests stay 100% passing — backwards compat per SM-D27 verified).
- 3 xfail: AC9 Lighthouse placeholder (manual), AC5 hu locale (translations TBD), 1 brands legacy.
