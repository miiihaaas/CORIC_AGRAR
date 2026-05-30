---
story-id: "2.6"
story-key: 2-6-brand-listing-strana-sa-grid-extended-layout-om
title: Brand Listing Strana sa Grid/Extended Layout-om
status: review
epic_num: 2
epic_title: Public Catalog — Browse Brands & Products
module: apps/brands/ (PRVI add views/urls/templates; modeli postoje od Story 2.1)
created: 2026-05-30
last_modified: 2026-05-30
author: Mihas (SM autonomous; SM Fix iter 2/5 — 8 IMPROVEMENT issues resolved [I-iter2-1 through I-iter2-8]; cumulative since iter 1: 9 CRITICAL + 11 IMPROVEMENT [iter 1] + 8 IMPROVEMENT [iter 2])
depends_on:
  - 2-1-brand-series-category-subcategory-modeli  # Brand, Series, Category, Subcategory modeli + layout_mode TextChoices
  - 2-2-product-i-related-modeli                  # Product (FK brand, series), ProductSpecification (section TextChoices)
  - 2-3-image-pipeline-sa-sorl-thumbnail-responsive-srcset  # {% responsive_picture %} + sorl-thumbnail
  - 2-4-pdf-cover-thumbnail-generator             # Brand.catalog_pdf cover + "Preuzmi katalog" CTA
  - 2-5-glightbox-integracija                     # base.html lightbox-init.js wiring (listing strana NE renderuje galleries direktno, ali base sloj prisutan)
---

# Story 2.6: Brand Listing Strana sa Grid/Extended Layout-om

Status: review

## Story

As a **Marko (poljoprivrednik koji istražuje katalog traktora online; Đorđe — Mihasov klijent koji testira sajt na mobilnom i sa tastature)**,
I want **da otvorim brand listing stranu (npr. `/sr/traktori/agri-tracking/`) i vidim cijeli pregled brenda: hero overlay karticu sa logom, sloganom i Repeating Element vodenim žigom; 4 statistika-medaljona sa count-up animacijom koja respektuje `prefers-reduced-motion`; citat-banner (testimonijal slider sa pause/play kontrolom, keyboard-accessible); sve modele brenda grupisane po seriji, gde Grid serije renderuju 2-kolone kartice (slika + naziv + CTA "OPŠIRNIJE") a Extended serije renderuju jedan-red-po-modelu (krupna slika levo + akordion specifikacija desno); i CTA banner "Preuzmi katalog" sa wave divider top koji vodi na `brand.catalog_pdf`**,
so that **mogu efikasno da poredim modele brenda u jednom screen-u (Marko brzo skenira KS i godinu kroz Grid kartice; Đorđe Tab-uje kroz medaljone i akordion bez miša i NVDA mu pravilno najavi otvaranje sekcija); strana zadovoljava Lighthouse a11y skor ≥ 95 (UX-DR-13 + NFR-2 + Story 9.9 a11y audit predikat) i postavlja kanonski listing pattern koji Story 2.8 (Tractor Listing sa HTMX filterima), Story 2.9 (Used Listing), Story 2.10/2.11 (Jeegee + Subcategory listing) reuse-uju**.

Ova story je **prva implementacija views/urls/templates layer-a u `apps/brands/` Django app-u** (modeli + admin stub iz Story 2.1 su jedino što app trenutno ima — vidi snapshot `apps/brands/` strukture u Dev Notes). Story 2.6 uvodi `apps/brands/views.py`, `apps/brands/urls.py`, `templates/brands/` direktorijum (`brand_detail.html` + 5 partials), 2 nova static JS modula (`statistic-counter.js`, `testimonials-slider.js`), 2 nova static CSS komponentna fajla (`brand-listing.css`, `statistic-medallion.css`, `testimonials-slider.css` — Decision SM-D7), i wiring kroz `config/urls.py` (`apps.brands.urls` include) + `static/css/main.css` (@import 3 nove komponente).

Server-side rendering only (NO HTMX swap u 2.6 — Decision SM-D1; interaktivni filteri su Story 2.8 scope). Strana je **prvi konzument** sledećih artefakata iz prethodnih story-ja:
- **`Series.LayoutMode` TextChoices** (Story 2.1 AC3) — template branching `{% if series.layout_mode == "grid" %}` → grid partial, else extended partial
- **`{% responsive_picture %}` template tag** (Story 2.3) — za sve below-fold slike (brand logo u hero, model thumbnails u Grid kartice, krupne slike u Extended layout-u) sa `loading="lazy"` atributom
- **`Brand.catalog_pdf`** (Story 2.1 AC2) — `{% if brand.catalog_pdf %}` guard pre nego što renderuje "Preuzmi katalog" CTA banner
- **`Brand.statistics` JSONField** (Story 2.1 AC2) — lista do 4 dict-a `[{"icon": "tractor", "value": 5000, "label": "..."}]` → renderuje 4-medallion grid sa IntersectionObserver-triggered count-up
- **Repeating Element partial** (Story 1.7) — vodeni žig unutar Hero Overlay Card-a (Decision SM-D2: koristi `templates/partials/hero_overlay_card.html` koji je već wired za `repeating_element.html`)
- **Wave Divider partial** (Story 1.7) — iznad "Preuzmi katalog" CTA banner-a (`position="top"`)
- **Pill Button partial** (Story 1.7) — sve CTA dugmad ("OPŠIRNIJE", "PREUZMI KATALOG")
- **Section Eyebrow partial** (Story 1.7) — UPPERCASE eyebrow caption iznad serija ("MODELI BRENDA", "STATISTIKE", "ŠTA KAŽU NAŠI KORISNICI")

**Foundation za:**

- **Story 2.7 (Product Detail strana):** Grid kartica `CTA "OPŠIRNIJE"` link vodi na `{% url 'products:detail' slug=product.slug %}` (URL će raise-ovati `NoReverseMatch` dok 2.7 ne uvede `apps.products.urls`; vidi Decision SM-D8 za handling — Story 2.6 koristi `product.get_absolute_url()` koji već postoji u 2.2 modelu uz `@pytest.mark.skip(reason='Story 2.7')` pattern u testovima koji to verifikuju runtime).
- **Story 2.8 (Tractor Listing sa HTMX filterima):** reuse-uje `coric-product-card` BEM komponentu iz `static/css/components/brand-listing.css` koja je uvedena ovde; HTMX `partials/product_grid.html` (Story 2.8) renderuje istu karticu unutar HTMX swap-a.
- **Story 2.9 (Used Listing):** isti card pattern (FR-13 polovna lista).
- **Story 2.10/2.11 (Jeegee Priključna + Subcategory listing):** reuse-uju Hero Overlay Card sa **plavom varijantom** Repeating Element-a (Brand.brand_color "#00A4E9" je već dostupan na Brand modelu iz 2.1 AC2; template logika koja mapira `brand.brand_color` na `repeating_element.html variant` parametar uvodi se u 2.6 i reuse-uje u 2.10).
- **Story 2.12 (HZM Radne Mašine + Tulip MIX):** isti hero card + subcategory grid pattern.
- **Story 3.1 (Home strana):** sekcija "Traktori" koristi reuse-ovanu `_brand_logo_card.html` mini-partial kada lista sve brand-ove (Decision SM-D9 — partial je dovoljno general-purpose da i Home strana može include-ovati uz `is_coming_soon` pill-badge).
- **Story 9.8 (Playwright E2E za UJ-1):** UJ-1 Marko journey **prvi screen je brand listing strana** — Playwright testovi verifikuju hero kartica vidljiva, 4 medaljona prebroj animaciju, CTA "OPŠIRNIJE" klik vodi na product detail. `data-testid` atributi na ključnim elementima moraju biti prisutni (per UX-DR-13 + Story 9.8 spec).
- **Story 9.9 (a11y audit + Lighthouse pass):** verifikuje WCAG 2.1 AA kroz axe-core + Playwright keyboard nav; Story 2.6 mora dostići Lighthouse a11y ≥ 95 u Dev smoke test (manuelni AC8).

**Princip:** Server-side rendering, **NO HTMX swap** (Decision SM-D1 — interaktivni filteri su 2.8 scope; 2.6 je čista listing strana). Vanilla JS modules (IIFE + `'use strict';` + `prefers-reduced-motion` respect + Story 1.8 + 2.5 stilski mirror), no Alpine.js, no jQuery, no build pipeline. CSS BEM sa `coric-` prefiksom + isključivo `var(--token)` reference iz `static/css/tokens.css` (Story 1.5 deliverable). Sve user-facing string-ove kroz `{% translate %}` / `gettext_lazy as _`. URL pattern `/<lang>/traktori/<brand-slug>/` registrovan kroz `i18n_patterns` (Story 1.4). **NEMA backend forme**, **NEMA HTMX endpoint-a**, **NEMA admin promena**, **NEMA migracija** — pure view + template + static asset story.

**Strukturna arhitektura — repository delta:** Repository dobija **19 novih fajlova** + **4 Edit operacije** (1 od kojih je verify-only — `_bmad-output/project-context.md` već primenjen u SM Fix iter 1) + **0 model/migration promena**:

| Path | Tip | Razlog |
|---|---|---|
| `apps/brands/views.py` | NOVO | `BrandDetailView(DetailView)` — query Brand + select_related/prefetch_related za Series → Product chain (Decision SM-D3 za query strategy) |
| `apps/brands/urls.py` | NOVO | Namespace `brands`; pattern `traktori/<slug:slug>/` mapira na `BrandDetailView` (URL name `detail`) — matches `Brand.get_absolute_url()` iz Story 2.1 |
| `apps/products/urls.py` | NOVO | Namespace `products`; placeholder pattern `proizvod/<slug:slug>/` mapira na `product_detail_placeholder` view (URL name `detail`); puna implementacija u Story 2.7 — vidi Decision SM-D8 |
| `apps/products/views.py` | NOVO | `product_detail_placeholder(request, slug)` FBV koji renderuje minimalan "uskoro" template (HTTP 200 sa placeholder porukom); puna `ProductDetailView` dolazi u Story 2.7 |
| `templates/products/_placeholder.html` | NOVO | Minimalan placeholder template "Stranica još nije dostupna — uskoro" za product detail; spečuje `NoReverseMatch` runtime kada Story 2.6 grid kartica linkuje ka `{% url 'products:detail' slug=product.slug %}` |
| `config/urls.py` | EDIT | Dodaje `path("", include("apps.brands.urls"))` + `path("", include("apps.products.urls"))` u `i18n_patterns` blok (postavlja pre `apps.core.urls` jer brands/products imaju specifičnije pattern-e) |
| `templates/brands/brand_detail.html` | NOVO | Glavni template koji `{% extends "base.html" %}`; sekcije: hero card, statistike-medaljoni, testimonijali, serije (grid/extended branching), "Preuzmi katalog" CTA |
| `templates/brands/brand_coming_soon.html` | NOVO | Minimal coming-soon template (logo + naziv + "Uskoro" pill-badge + nazad-na-Home CTA); render-uje se kad `brand.is_coming_soon == True` per Decision SM-D4 |
| `templates/brands/partials/_hero_section.html` | NOVO | Hero overlay sa brand logo + slogan + Repeating Element watermark (wrapper oko `partials/hero_overlay_card.html`) |
| `templates/brands/partials/_statistics_medallions.html` | NOVO | Render 4-medallion grid; data-attribute `data-count-target="X"` za JS count-up |
| `templates/brands/partials/_testimonials_slider.html` | NOVO | Slider sa pause/play button, prev/next, role="region" + aria-label, `data-testimonials-slider` markup |
| `templates/brands/partials/_series_section.html` | NOVO | Iterira `brand.series.all()`; za svaku seriju render `{% if series.layout_mode == "grid" %} include grid partial {% else %} include extended partial {% endif %}` |
| `templates/brands/partials/_series_grid.html` | NOVO | 2-col card grid (slika + naziv + CTA OPŠIRNIJE) za Series.LayoutMode.GRID |
| `templates/brands/partials/_series_extended.html` | NOVO | 1-row-per-model layout: krupna slika levo + akordion specifikacija desno za Series.LayoutMode.EXTENDED |
| `templates/brands/partials/_catalog_cta.html` | NOVO | "Preuzmi katalog" CTA banner sa Wave Divider iznad (samo render-uje se ako `brand.catalog_pdf` postoji) |
| `static/js/statistic-counter.js` | NOVO | Vanilla IIFE; IntersectionObserver pri scroll-into-view triggers count-up animaciju; respektuje `prefers-reduced-motion: reduce` (instant set) |
| `static/js/testimonials-slider.js` | NOVO | Vanilla IIFE; prev/next + auto-advance sa pause/play; keyboard nav (Arrow Left/Right); auto-advance pauzira na fokus i na `coric:lightbox-open` event (Story 2.5 kontrakt); slider pauzira ako `prefers-reduced-motion` |
| `static/css/components/brand-listing.css` | NOVO | Layout sekcija (hero, sections wrappers, grid layouts, extended layout, akordion stilovi) |
| `static/css/components/statistic-medallion.css` | NOVO | 4-medallion circle styles + count-up tipografija |
| `static/css/components/testimonials-slider.css` | NOVO | Slider container, navigation buttons, pause/play, focus-visible outline |
| `static/css/main.css` | EDIT | Dodaje 3 nove `@import url('./components/...');` linije (brand-listing, statistic-medallion, testimonials-slider) — TAČNO mirror Story 1.7+1.8+2.5 pattern |
| `templates/base.html` | EDIT | Dodaje 2 nova `<script>` tag-a sa `defer` POSLE `lightbox-init.js` (linija ~39): `statistic-counter.js` + `testimonials-slider.js`. **Site-wide JS jer su komponente koje se koriste i na Home (Story 3.1), Product Detail (2.7), itd.** Defensive guard u JS bail-uje ako selektori ne postoje na strani. |
| `_bmad-output/project-context.md` | EDIT (already applied during validation; verify only — Subtask 1.7) | Dokumentuje view-layer izuzetak na pravilu "brands ne sme importovati products" (BrandDetailView aggregates products under their brand — read-only query layer, no cyclic model dependency) — vidi C2 fix i Decision SM-D16. **FACT:** Edit JE primenjen u SM Fix iter 1; verifikovano linije 619-632. |

**Brojanje:** 19 NOVO fajlova (4 .py: `apps/brands/views.py`, `apps/brands/urls.py`, `apps/products/views.py`, `apps/products/urls.py`; 1 products template: `templates/products/_placeholder.html`; 2 brands main templates: `brand_detail.html` + `brand_coming_soon.html`; 7 brands partials: `_hero_section`, `_statistics_medallions`, `_testimonials_slider`, `_series_section`, `_series_grid`, `_series_extended`, `_catalog_cta`; 2 JS: `statistic-counter.js` + `testimonials-slider.js`; 3 CSS: `brand-listing.css` + `statistic-medallion.css` + `testimonials-slider.css`) + 4 EDIT (`config/urls.py`, `static/css/main.css`, `templates/base.html`, `_bmad-output/project-context.md` — poslednji je verify-only per Subtask 1.7 jer je već primenjen u SM Fix iter 1). **Računica:** 4 + 1 + 2 + 7 + 2 + 3 = 19 NOVO; 3 active EDIT + 1 verify-only EDIT = 4 EDIT total.

Postojeći fajlovi koji ostaju **NETAKNUTI** (regression guards): `apps/brands/models.py`, `apps/brands/admin.py`, `apps/brands/translation.py`, `apps/brands/migrations/`, `apps/products/models.py`, `apps/products/admin.py`, `apps/products/translation.py`, `apps/products/migrations/`, `apps/core/`, `apps/media_pipeline/`, `static/vendor/`, `static/css/tokens.css`, `static/css/components/{header,footer,sticky-nav,lightbox,hero-overlay-card,repeating-element,pill-button,section-eyebrow,wave-divider}.css`, `templates/partials/*`, `pyproject.toml`, `config/settings/`, `compose/django/Dockerfile`.

## Kriterijumi prihvatanja

**AC1 — URL pattern `/<lang>/traktori/<brand-slug>/` rezolvuje `BrandDetailView`; rezolucija prolazi i daje HTTP 200 za `is_coming_soon=False` brendove, HTTP 404 za nepostojeće slug-ove**

- **Given** Brand modeli iz Story 2.1; `apps.brands` registrovan u `INSTALLED_APPS`; `i18n_patterns()` aktivan iz Story 1.4; `APPEND_SLASH = True` (Django default; `django.middleware.common.CommonMiddleware` aktivan u `MIDDLEWARE` per `config/settings/base.py`)
- **When** kreiram `apps/brands/urls.py` sa namespace-om `brands` i pattern-om `traktori/<slug:slug>/` mapiranim na `BrandDetailView.as_view()` sa URL name `detail`, i registrujem `path("", include("apps.brands.urls"))` u `config/urls.py` UNUTAR `i18n_patterns(...)` blok-a **PRE** `path("", include("apps.core.urls"))` (per Django URL resolution — više specifični pattern-i moraju biti pre catch-all home)
- **Then**:
  - `reverse("brands:detail", kwargs={"slug": "agri-tracking"})` vraća `/sr/traktori/agri-tracking/` kad je aktivan locale `sr` (i analogno `/hu/traktori/agri-tracking/`, `/en/traktori/agri-tracking/` za druge lokale)
  - GET `/sr/traktori/agri-tracking/` vraća HTTP 200 ako Brand sa `slug="agri-tracking"` postoji u DB
  - GET `/sr/traktori/nepostojeci-brand/` vraća HTTP 404 (DetailView `get_object_or_404` ili `DoesNotExist` → 404 handler)
  - GET `/sr/traktori/agri-tracking` (bez trailing slash) → Django `APPEND_SLASH` redirektuje na sa-slash varijantu (301/302 zavisno od request method-a); funkcionalno i dalje važi
- **And** URL name `detail` matches `Brand.get_absolute_url()` iz Story 2.1 (koji vraća `reverse("brands:detail", kwargs={"slug": self.slug})` — live verifikovano `apps/brands/models.py:158`). **NIKAKAV edit na `apps/brands/models.py` nije potreban** — URL pattern koristi default `DetailView` `slug_url_kwarg = "slug"` i `slug_field = "slug"` (Django defaults; explicit override nije nužno). Vidi Decision SM-D5.
- **And** za brand-ove sa `is_coming_soon=True`, view vraća HTTP 200 ali template renderuje **placeholder "Uskoro" stanje** (vidi AC2 + AC2.5) umesto pune listing strane. URL je accessible (vraća 200), ali sadržaj jasno komunicira da brand nije pun aktivan. Decision SM-D4: dovoljno je vidno različito od pune strane, ne raise-ujemo 404 jer Marko kroz Home stranu može doći link-om i očekuje neki kontekst, ne hard error.
- **And** smoke verifikacija: `uv run python manage.py check` exit code 0. Za enumeraciju URL-ova bez dodatnih dev-deps (mirror I8 fix — `django-extensions` se NE dodaje u v1), koristiti stock Django introspection u shell-u:
  ```bash
  uv run python manage.py shell -c "from django.urls import get_resolver; \
    patterns = get_resolver().reverse_dict; \
    print('brands:detail' in [n for n in patterns.keys() if isinstance(n, str)])"
  ```
  Očekivan output: `True` (URL name `brands:detail` registrovan). Alternativno, eksplicitan reverse check:
  ```bash
  uv run python manage.py shell -c "from django.urls import reverse; \
    from django.utils.translation import activate; activate('sr'); \
    print(reverse('brands:detail', kwargs={'slug': 'agri-tracking'}))"
  ```
  Očekivan output: `/sr/traktori/agri-tracking/`.

**AC2 — `BrandDetailView` (CBV `DetailView`) query-uje Brand sa optimizovanim `select_related` + `prefetch_related` chain za Series → Product (i Product.specifications za extended layout), bez N+1; context sadrži `brand` + `testimonials`; coming_soon stanje renderuje minimalan template**

- **Given** Brand modeli + Product modeli + `Series.layout_mode` TextChoices iz 2.1/2.2; live verifikovano: `Brand.get_absolute_url()` u `apps/brands/models.py:158` koristi `reverse("brands:detail", kwargs={"slug": self.slug})`; live verifikovano: `ProductSpecification.Meta.ordering = ["product", "order", "id"]` (Story 2.2 NOTE I3 namerno NE uključuje `section` jer alphabetical sort `hidraulika→motor→ostalo→transmisija` je SUPROTAN od traženog display order-a Motor→Transmisija→Hidraulika→Ostalo)
- **And — Cross-boundary import izuzetak (KRITIČNO za review):** Pravilo iz `_bmad-output/project-context.md` (linija 622) zabranjuje `brands → products` import (jednosmerna `products → brands`). Story 2.6 `BrandDetailView` MORA importovati `Product`, `ProductSpecification`, `ProductTestimonial` jer view fundamentalno agregira "produkte grupisane po brendu" — coupling na Product je intrinzičan domain semantici brand-listing strane. **Ovo je dokumentovani izuzetak**: read-only query layer (no model dependency, no save/create na Product iz brands view-a, no FK iz brand → product). Vidi Decision SM-D16 + EDIT operaciju na `_bmad-output/project-context.md` u file delta tabeli (sekcija § Cross-boundary import dobija "Exception" note). Refactor "premestiti view u apps/products" je odbačen — view semantički pripada `brands` (URL je `/traktori/<brand-slug>/`, ne `/proizvod/<brand-slug>/`).
- **When** definišem `apps/brands/views.py`:
  ```python
  """Brand listing strana — Story 2.6 (Epic 2 Public Catalog).

  Server-side rendering only; HTMX filteri su Story 2.8 scope.
  Query optimizacija: prefetch_related za serije + per-series prefetch za
  products + per-product prefetch za specifications. ProductSpecification
  queryset koristi Case/When annotation za section_rank (display order
  Motor→Transmisija→Hidraulika→Ostalo) i section_label (translated label
  za {% regroup %} grouper) — Story 2.2 NOTE I3. Case/When SE INSTANCIRA
  unutar get_queryset() per-request (SM-D20) jer Value(gettext_lazy(...))
  freeze-uje aktivni jezik pri instanciji ako se postavi na module-level.

  Cross-boundary import izuzetak (vidi Decision SM-D16 + project-context.md
  § Cross-boundary import "Exception" note): BrandDetailView agregira products
  grupisane po brendu. View-layer-only coupling, no model dependency.
  """

  from __future__ import annotations

  from django.db.models import Case, CharField, IntegerField, Prefetch, Value, When
  from django.utils.translation import gettext_lazy as _
  from django.views.generic import DetailView

  from apps.brands.models import Brand, Series
  from apps.products.models import Product, ProductSpecification, ProductTestimonial


  class BrandDetailView(DetailView):
      model = Brand
      context_object_name = "brand"
      # NAPOMENA: Brand model NEMA `is_published` flag u Story 2.1 (samo
      # is_coming_soon BooleanField). Sve brand entry-je su accessible kroz
      # URL; coming_soon flag samo menja koji template se render-uje
      # (vidi get_template_names() override). slug_url_kwarg i slug_field
      # koriste Django default ("slug") da matchuje pattern
      # `traktori/<slug:slug>/` — C1 fix; matches Brand.get_absolute_url()
      # iz Story 2.1 koji koristi reverse("brands:detail", kwargs={"slug": ...}).

      def get_queryset(self):
          # Optimizacija: prefetch serija + per-serija prefetch products + per-product
          # prefetch specifications (za extended layout akordion).
          #
          # KRITIČNO (SM-D20): Case/When sa Value(_("...")) MORA biti definisan
          # UNUTAR get_queryset() (ili helper method-a koji se zove per-request),
          # NE na module level. Razlog: gettext_lazy proxy unutar Value() ne
          # eager-evaluuje pri import-u, ali Case/When OBJEKAT je instanciran
          # tačno jednom pri Python load-u modula; ako se Case definiše na
          # module-level, prvi request "zamrzne" jezik za sve buduće requeste
          # (Value sa istim proxy-em SQL-bind-uje translation rezolvanu pri
          # PRVOM korišćenju). LocaleMiddleware (Story 1.4) postavlja
          # `translation.activate(lang)` per-request; konstruisanje Case/When
          # u svakom request-u garantuje da grouper labels (Motor/Transmisija/
          # Hidraulika/Ostalo) renderuju u trenutno aktivnoj lokali.
          # Section display order — Motor → Transmisija → Hidraulika → Ostalo
          # (Story 2.2 NOTE I3: alphabetical sort daje WRONG order; view-layer
          # Case/When annotation je kanonski fix.)
          section_order = Case(
              When(section="motor", then=Value(1)),
              When(section="transmisija", then=Value(2)),
              When(section="hidraulika", then=Value(3)),
              When(section="ostalo", then=Value(4)),
              default=Value(99),
              output_field=IntegerField(),
          )
          # Section label — translated; koristi se kao {% regroup %} grouper da
          # template renderuje translated label umesto raw TextChoices value
          # (C9 fix).
          section_label = Case(
              When(section="motor", then=Value(_("Motor"))),
              When(section="transmisija", then=Value(_("Transmisija"))),
              When(section="hidraulika", then=Value(_("Hidraulika"))),
              When(section="ostalo", then=Value(_("Ostalo"))),
              default=Value(_("Ostalo")),
              output_field=CharField(),
          )
          specs_qs = ProductSpecification.objects.annotate(
              section_rank=section_order,
              section_label=section_label,
          ).order_by("section_rank", "order", "id")

          published_products = Product.objects.filter(is_published=True).prefetch_related(
              Prefetch("specifications", queryset=specs_qs)
          )
          series_qs = (
              Series.objects.order_by("display_order", "name")
              .prefetch_related(
                  Prefetch("products", queryset=published_products)
              )
          )
          return Brand.objects.prefetch_related(
              Prefetch("series", queryset=series_qs)
          )

      def get_template_names(self):
          # Coming-soon brand → minimal template; ostali → puna listing strana.
          # self.object MORA biti set pre poziva (vidi get() override).
          if getattr(self, "object", None) is not None and self.object.is_coming_soon:
              return ["brands/brand_coming_soon.html"]
          return ["brands/brand_detail.html"]

      def get(self, request, *args, **kwargs):
          # Set self.object PRE get_template_names() poziva (DetailView default
          # get() calls get_template_names u render_to_response AFTER context).
          # Ovaj pattern je CBV-idiomatic (preserve-uje get_context_data hook
          # za buduće mixin-e) — vidi I11 + Decision SM-D19.
          self.object = self.get_object()
          context = self.get_context_data(object=self.object)
          return self.render_to_response(context)

      def get_context_data(self, **kwargs):
          ctx = super().get_context_data(**kwargs)
          if self.object.is_coming_soon:
              # Minimal context za coming-soon — bez testimonijala i bez agregata.
              return ctx
          # Testimonijali: svi published proizvodi za ovaj brand → testimonijali
          # (FR-19 — "Iz prve ruke" slider; ako brand nema testimonijala, sekcija
          # se SKRIVA u template-u kroz {% if testimonials %} guard).
          # order_by("order", "-created_at"): poštuje ProductTestimonial.Meta
          # konvenciju (Story 2.2) + recency tie-breaker. C4 fix.
          ctx["testimonials"] = (
              ProductTestimonial.objects.filter(
                  product__brand=self.object,
                  product__is_published=True,
              )
              .select_related("product")
              .order_by("order", "-created_at")[:10]
          )
          return ctx
  ```
- **Then**:
  - Query plan (Django Debug Toolbar smoke): **TAČNO 5 SQL upita** za render strane (I1 fix):
    1. Brand (DetailView get_object — `SELECT * FROM brands_brand WHERE slug = ...`)
    2. Series prefetch (`SELECT * FROM brands_series WHERE brand_id IN (...) ORDER BY display_order, name`)
    3. Product prefetch (`SELECT * FROM products_product WHERE series_id IN (...) AND is_published = TRUE`)
    4. ProductSpecification prefetch (`SELECT *, Case/When section_rank, Case/When section_label FROM products_productspecification WHERE product_id IN (...) ORDER BY section_rank, order, id`)
    5. ProductTestimonial filter + select_related("product") (`SELECT testimonial.*, product.* FROM products_producttestimonial JOIN products_product ... WHERE brand_id = ... AND is_published = TRUE ORDER BY order, -created_at LIMIT 10`)
  - **NEMA N+1** — iteriranje `{% for series in brand.series.all %}{% for product in series.products.all %}{% for spec in product.specifications.all %}` u template-u NE pravi dodatne query-je (sve cached kroz Prefetch).
  - Context sadrži ključeve `brand` (Brand instance, sa prefetched `series` relation) + `testimonials` (QuerySet ProductTestimonial). **I2 fix:** NE postoji odvojen `series_list` ključ; template pristupa direktno kroz `brand.series.all` (prefetched manager). Sve ostale data ide kroz brand instance accessor-e (`brand.statistics`, `brand.catalog_pdf`, `brand.slogan`, itd.).
- **And** ako `brand.is_coming_soon == True`, `get_template_names()` vraća `["brands/brand_coming_soon.html"]` i view renderuje minimal template sa MINIMAL context-om (samo `brand` key); `testimonials` se NE fetch-uje. Vidi AC2.5 za detaljan markup spec.
- **And** view koristi default Django `DetailView` `slug_url_kwarg = "slug"` i `slug_field = "slug"` (NIJE override-ovano) da matchuje URL pattern `traktori/<slug:slug>/`. **C1 fix** — eliminiše prethodni mismatch sa `Brand.get_absolute_url()` u Story 2.1.
- **And** view NE oslobađa eksplicitno `request` user (anonimni view, javni katalog) — `LoginRequiredMixin` se NE koristi.
- **And** ako brand nema nijednu seriju (`brand.series.all().count() == 0`), template prikazuje empty state poruku `{% translate "Modeli ovog brenda su u pripremi." %}` umesto prazne sekcije (Decision SM-D6 — explicit empty state, ne tihi skok).
- **And — PR-D2 napomena (I4 fix):** Story 2.6 ograničena na brendove gde svi published proizvodi imaju `series` (Coric trakto brendovi — Agri-Tracking, John Deere ekvivalenti). Brendovi sa nullable `Product.series` (Jeegee, HZM, Tulip — per PR-D2) imaju zasebni listing pattern (flat product grid bez series grupisanja) koji se uvodi u Story 2.10/2.11/2.12. Vidi Decision SM-D17. Story 2.6 view ne fetch-uje `series__isnull=True` produkte — to je out-of-scope.

**AC2.5 — `brand_coming_soon.html` minimal template renderuje "Uskoro" stanje (logo + naziv + pill-badge + nazad-na-Home CTA) bez statistike/serija/testimonijala (C6 fix)**

- **Given** AC2 završen; `brand.is_coming_soon == True` triggers ovaj template kroz `get_template_names()` override
- **When** kreiram `templates/brands/brand_coming_soon.html`
- **Then** template MORA imati minimalnu strukturu:
  ```django
  {% extends "base.html" %}
  {% load i18n static media_tags %}

  {% block title %}{{ brand.name }} — {% translate "Uskoro" %} | {% translate "Ćorić Agrar" %}{% endblock %}
  {% block meta_description %}{% blocktranslate with brand=brand.name %}Brend {{ brand }} će uskoro biti dostupan u našem katalogu.{% endblocktranslate %}{% endblock %}

  {% block content %}
  <main role="main" class="coric-brand-coming-soon container py-5">
    <section aria-labelledby="brand-coming-soon-title" class="text-center">
      {% if brand.logo %}
        <div class="coric-brand-coming-soon__logo mb-4">
          {% responsive_picture brand.logo alt=brand.name sizes="(max-width: 768px) 80vw, 320px" loading="eager" format='PNG' %}
        </div>
      {% endif %}
      <h1 id="brand-coming-soon-title" class="coric-brand-coming-soon__title">{{ brand.name }}</h1>
      <span class="coric-pill-badge coric-pill-badge--coming-soon mt-3" role="status">
        {% translate "Uskoro" %}
      </span>
      <p class="coric-brand-coming-soon__message mt-4">
        {% blocktranslate with brand=brand.name %}Brend {{ brand }} će uskoro biti dostupan u našem katalogu.{% endblocktranslate %}
      </p>
      <a href="{% url 'core:home' %}" class="coric-button coric-button--primary mt-4">
        {% translate "Nazad na Home" %}
      </a>
    </section>
  </main>
  {% endblock %}
  ```
- **And** template MORA:
  - Imati semantic `<main role="main">` wrapper (a11y landmark)
  - Sadržati JEDNU `<h1>` sa brand.name
  - Renderovati `brand.logo` SAMO ako postoji (`{% if brand.logo %}` guard); ako nema logo, sekcija renderuje samo naziv + pill-badge + CTA
  - Pill-badge MORA imati `role="status"` (live region announcement za screen reader-e) i klasu `coric-pill-badge--coming-soon`. **Klasa je definitivno assigned u Story 2.6 spec-u** — vidi AC8 § `static/css/components/brand-listing.css` enumeraciju (`coric-pill-badge` base + `coric-pill-badge--coming-soon` variant). Visual treatment će se reuse-ovati u Story 3.1 (Home strana FR-7 brand listing sa pill-badge "Uskoro" overlayer) i Story 2.10/2.11 (subcategory listing coming-soon badge).
  - **NEMA statistike, NEMA serija, NEMA testimonijala** — svi sub-sektori brand_detail.html su izostavljeni
  - Sve user-facing string-ove kroz `{% translate %}` ili `{% blocktranslate %}`
  - CTA "Nazad na Home" linkuje na `{% url 'core:home' %}` (per Story 1.4 home URL name — verifikovati pre commit-a; ako nema namespace, koristiti `{% url 'home' %}` ili odgovarajuće)

**AC2.6 — `templates/products/_placeholder.html` minimal template renderuje "Stranica još nije dostupna — uskoro" za product detail placeholder (C8 fix dependency), sa SEO `noindex` guard-om (I-iter2-4 fix)**

- **Given** Subtask 1.4 dodaje `apps/products/urls.py` sa `path("proizvod/<slug:slug>/", views.product_detail_placeholder, name="detail")`; Subtask 1.3 dodaje `product_detail_placeholder` FBV koja renderuje ovaj template; korisnik koji klikne grid karticu OPŠIRNIJE pre Story 2.7 (`ProductDetailView` puna implementacija) sleti na ovaj placeholder
- **When** kreiram `templates/products/_placeholder.html`
- **Then** template MORA imati TAČAN markup:
  ```django
  {% extends "base.html" %}
  {% load i18n %}

  {% block title %}{% translate "Stranica još nije dostupna" %} | {% translate "Ćorić Agrar" %}{% endblock %}

  {% block extra_head %}
    <meta name="robots" content="noindex, nofollow">
  {% endblock %}

  {% block content %}
  <main role="main" class="coric-product-placeholder">
    <h1 class="coric-product-placeholder__title">{% translate "Stranica još nije dostupna" %}</h1>
    <p class="coric-product-placeholder__message">{% translate "Detalji ovog modela uskoro će biti dostupni. Hvala na strpljenju." %}</p>
    <a href="{% url 'core:home' %}" class="coric-button coric-button--primary">
      {% translate "Nazad na Home" %}
    </a>
  </main>
  {% endblock %}
  ```
- **And** template MORA:
  - Imati `<meta name="robots" content="noindex, nofollow">` u `{% block extra_head %}` — KRITIČNO za SEO: placeholder strana ne sme biti indexed dok Story 2.7 ne uvede pravu Product detail; bez `noindex` Googlebot bi indexirao "Stranica još nije dostupna" za ~stotine product slug-ova što je SEO katastrofa
  - Imati semantic `<main role="main">` wrapper (a11y landmark)
  - Sadržati TAČNO JEDNU `<h1>` sa porukom "Stranica još nije dostupna"
  - Sadržati paragraf sa apology/uskoro porukom
  - CTA "Nazad na Home" koji linkuje na `{% url 'core:home' %}` (per Story 1.4 home URL name; verifikovati pre commit-a — ako nema `core` namespace, koristiti `{% url 'home' %}` ili odgovarajuće)
  - Sve user-facing string-ove kroz `{% translate %}`
- **And** template provider-uje `base.html` extends — koristi site-wide header/footer/navigation (Story 1.4 deliverable); placeholder NIJE blank strana, ima full layout context
- **And — Pretpostavka:** `base.html` (Story 2.5 deliverable) podržava `{% block extra_head %}` ili equivalent ekstension point za per-page `<head>` content. Ako block ne postoji, **Subtask 1.5 mora prvo dodati `{% block extra_head %}{% endblock %}` u `templates/base.html` <head> sekciju** (između `<title>` i closing `</head>`); ovaj edit je trivijalan i ne menja postojeću semantiku. Verifikovati live pre implementacije.
- **And** placeholder klase (`coric-product-placeholder`, `coric-product-placeholder__title`, `coric-product-placeholder__message`) se definišu u `static/css/components/brand-listing.css` per SM-D21 (scope decision — minimalan tech debt, drop u Story 2.7)

**AC3 — `templates/brands/brand_detail.html` renderuje sekcije TAČNIM redosledom: hero overlay → statistike-medaljoni (ako `brand.statistics` ima items) → testimonijali (ako `testimonials` queryset nije prazan) → serije sekcija (sa grid/extended branching) → "Preuzmi katalog" CTA (ako `brand.catalog_pdf` postoji); sve sekcije semantičke (`<section>` sa `aria-labelledby`)**

- **Given** AC1 + AC2 završeni
- **When** kreiram `templates/brands/brand_detail.html`
- **Then** template MORA:
  - `{% extends "base.html" %}` + `{% load i18n static media_tags %}` (media_tags za `{% responsive_picture %}`)
  - `{% block title %}{{ brand.name }} | {% translate "Ćorić Agrar" %}{% endblock %}`
  - `{% block meta_description %}{{ brand.slogan|default:brand.description|truncatewords:25 }}{% endblock %}`
  - `{% block content %}` sadrži sekcije TAČNIM redosledom (po epics.md Story 2.6 spec):
    1. **Hero overlay sekcija** (`<section id="brand-hero" aria-labelledby="brand-hero-title">`) — include `templates/brands/partials/_hero_section.html` koja prosleđuje brand kontekst u `partials/hero_overlay_card.html` (Story 1.7 partial). Hero card prima:
       - `title` = `brand.name`
       - `bullets` = lista do 3 ključne karakteristike brenda (Decision SM-D10: koristi `brand.slogan` kao jedini bullet ako `brand.statistics` već zauzima drugi sekcija — za sada **prosleđujemo praznu listu** i hero card sadrži samo title + watermark)
       - `brand_logo` = `brand.logo.url` (ako postoji); `brand_logo_alt` = `brand.name`
       - `variant` = mapiranje `brand.brand_color` na `repeating_element.html` variant: `"blue"` ako `brand_color == "#00A4E9"` (Jeegee), inače `"green"` (default). **Decision SM-D11 — explicit mapping helper umesto generic CSS-var injection** (yagni za sada; ako brendova bude > 2, refaktor je trivijalan).
    2. **Statistike medaljoni sekcija** (`<section id="brand-statistics" aria-labelledby="brand-statistics-title" class="coric-brand-statistics">`) — render SAMO ako `brand.statistics` lista nije prazna:
       ```django
       {% if brand.statistics %}
         {% include "brands/partials/_statistics_medallions.html" %}
       {% endif %}
       ```
       Partial iterira `brand.statistics` (max 4 items per 2.1 validation) i renderuje 4 medaljona sa `data-count-target="{{ stat.value }}"` data atributom.
    3. **Testimonijali slider sekcija** (`<section id="brand-testimonials" aria-labelledby="brand-testimonials-title" class="coric-testimonials">`) — render SAMO ako `testimonials` queryset nije prazan:
       ```django
       {% if testimonials %}
         {% include "brands/partials/_testimonials_slider.html" %}
       {% endif %}
       ```
    4. **Serije sekcija** (`<section id="brand-series" aria-labelledby="brand-series-title" class="coric-brand-series">`) — uvek render (čak i ako prazno, sa empty state porukom):
       ```django
       {% include "brands/partials/_series_section.html" %}
       ```
       _series_section.html iterira `brand.series.all()` i per-series radi branching:
       ```django
       {% for series in brand.series.all %}
         <article class="coric-series-block" aria-labelledby="series-{{ series.id }}-title">
           <h2 id="series-{{ series.id }}-title">{{ series.name }}</h2>
           {% if series.description %}<p>{{ series.description }}</p>{% endif %}
           {% if series.layout_mode == "grid" %}
             {% include "brands/partials/_series_grid.html" %}
           {% else %}
             {% include "brands/partials/_series_extended.html" %}
           {% endif %}
         </article>
       {% empty %}
         <p class="coric-empty-state">{% translate "Modeli ovog brenda su u pripremi." %}</p>
       {% endfor %}
       ```
    5. **"Preuzmi katalog" CTA banner** (`<section id="brand-catalog-cta" aria-labelledby="brand-catalog-cta-title" class="coric-catalog-cta-banner">`) — render SAMO ako `brand.catalog_pdf` postoji:
       ```django
       {% if brand.catalog_pdf %}
         {% include "brands/partials/_catalog_cta.html" %}
       {% endif %}
       ```
       Partial include-uje `partials/wave_divider.html with position="top"` (Story 1.7 partial) na vrhu, zatim heading "PREUZMI KATALOG", kratak description, i **direktan `<a>` tag (NE `pill_button.html` partial — vidi SM-D22 + I-iter2-6 fix)** sa target=_blank/rel=noopener/download atributima:
       ```django
       <a href="{{ brand.catalog_pdf.url }}"
          target="_blank"
          rel="noopener noreferrer"
          download
          class="coric-button coric-button--primary"
          data-testid="brand-catalog-download">
         {% translate "Preuzmi katalog" %}
       </a>
       ```
       **Razlog NE-pill_button:** `templates/partials/pill_button.html` (Story 1.7) renderuje `<a class="coric-button coric-button--{{ variant }}" href="{{ href }}">{{ label }}</a>` plus opcioni `aria_label` i `extra_classes` — partial NEMA prosleđivanje za `target`, `rel`, ni `download` atribute. Modifikacija Story 1.7 partial-a je out-of-scope za Story 2.6 (potencijalno breaking change za sve postojeće konzumente). Vizuelni parity se postiže reuse-om iste `coric-button coric-button--primary` BEM klase iz `static/css/components/pill-button.css` (Story 1.7 deliverable, site-wide loaded). Vidi SM-D22.
- **And** sve sekcije moraju imati semantic HTML5 (`<section>`) sa `aria-labelledby` koji referencira heading id unutar te sekcije (a11y must-have). Decoratorne SVG elemente koji su unutar Repeating Element-a već imaju `aria-hidden="true"` (Story 1.7 deliverable).
- **And** **NEMA inline `style="..."` attribute-a** bilo gde u template-u — sve stilizovanje ide kroz `coric-*` BEM klase iz novih CSS komponentnih fajlova (AC6).
- **And** **NEMA hardcoded srpski string** — sve labels prolaze kroz `{% translate "..." %}` ili `{% blocktranslate %}`.

**AC4 — Grid layout partial (`_series_grid.html`) renderuje 2-col responzivni grid kartica modela (slika + naziv + CTA "OPŠIRNIJE"); kartica je linkabilna; slike koriste `{% responsive_picture %}` sa `loading="lazy"`**

- **Given** AC3 završen; Story 2.3 `{% responsive_picture %}` template tag iz `media_pipeline.templatetags.media_tags`
- **When** kreiram `templates/brands/partials/_series_grid.html`
- **Then** partial MORA:
  - Iterirati `series.products.all` (već prefetched u view; `is_published=True` filter primenjen u prefetch query)
  - Renderovati 2-col grid (Bootstrap 5 `row` + `col-md-6` ili custom CSS Grid u `brand-listing.css` — Decision SM-D12: koristi **custom CSS Grid** sa `grid-template-columns: repeat(2, 1fr)` za desktop, `1fr` za mobile, da ne stvori Bootstrap class-clash u brand-listing.css i da sve grid spacing-e kontroliše `var(--spacing-scale-*)` tokeni)
  - Svaka kartica je **linkabilan `<a>` element** koji obavija celu karticu (linkable card pattern); `<a>` ima `aria-label="{{ product.name }}"` (I6 fix — screen reader najavi cilj link-a kao "Naziv proizvoda, link"; bez aria-label najava bi bila konkatenacija svog vidljivog teksta uključujući "OPŠIRNIJE" što je redundantno). Vidljivi "OPŠIRNIJE" span ima `aria-hidden="true"` jer je dekorativan u kontekstu linkable card-a:
    ```django
    <a class="coric-product-card"
       href="{{ product.get_absolute_url }}"
       aria-label="{{ product.name }}"
       data-testid="product-card-{{ product.slug }}">
      <div class="coric-product-card__image">
        {% responsive_picture product.main_image alt=product.name sizes="(max-width: 768px) 100vw, 50vw" loading="lazy" css_class="coric-product-card__img" %}
      </div>
      <div class="coric-product-card__body">
        <h3 class="coric-product-card__title">{{ product.name }}</h3>
        {% if product.horse_power %}
          <p class="coric-product-card__spec">{{ product.horse_power }} {% translate "KS" %}</p>
        {% endif %}
        <span class="coric-button coric-button--primary coric-product-card__cta" aria-hidden="true">{% translate "OPŠIRNIJE" %}</span>
      </div>
    </a>
    ```
  - **NAPOMENA — linkable card pattern + nested interactive guard:** `<a>` obavija karticu pa CTA "OPŠIRNIJE" je `<span>` (NE `<a>` ili `<button>`) da ne kreira nested interactive elements (a11y violation per WCAG 2.1 SC 4.1.2 + HTML5 § "Interactive content cannot be nested"). Vizuelno reuse-uje `coric-button` BEM klasu iz Story 1.7 (Pill Button styling) ali NE include-uje `partials/pill_button.html` jer Pill Button partial render-uje `<a>` element koji bi se nested unutar wrapping `<a>` — vidi I3 napomenu u Dev Notes. Hover/focus styling na celoj kartici (per AC8).
  - **Empty state:** ako `series.products.all` je prazno (svi proizvodi `is_published=False`), partial renderuje `<p class="coric-empty-state">{% translate "Modeli ove serije su u pripremi." %}</p>`.
  - **`loading="lazy"` atribut** ide na sve slike OSIM prve kartice u prvoj seriji koja je iznad fold-a (Decision SM-D13: u v1 sve kartice koriste `loading="lazy"` jer ispod hero sekcije + statistike sekcije + testimonijala — fold je dovoljno duboko da nijedna grid kartica nije above-the-fold. `{% responsive_picture %}` već propušta `loading` parametar).
  - `data-testid` atributi: `product-card-{slug}` na svakom kartici (za Playwright Story 9.8).

**AC5 — Extended layout partial (`_series_extended.html`) renderuje 1-row-per-model: krupna slika levo (60% width desktop) + akordion specifikacija desno (40%); akordion koristi native HTML `<details>/<summary>` sa Bootstrap-uglađenim stilom; specifikacije grupisane po `ProductSpecification.section` TextChoices (Motor → Transmisija → Hidraulika → Ostalo); prazna sekcija se SKRIVA**

- **Given** AC4 završen; Story 2.2 `ProductSpecification.section` TextChoices (`motor`, `transmisija`, `hidraulika`, `ostalo`)
- **When** kreiram `templates/brands/partials/_series_extended.html`
- **Then** partial MORA:
  - Iterirati `series.products.all` (prefetched sa `specifications` per AC2 query)
  - Per-product renderovati article wrapper sa flex/grid layout:
    ```django
    <article class="coric-product-row" data-testid="product-row-{{ product.slug }}">
      <div class="coric-product-row__image">
        {% responsive_picture product.main_image alt=product.name sizes="(max-width: 768px) 100vw, 60vw" loading="lazy" %}
      </div>
      <div class="coric-product-row__specs">
        <h3 class="coric-product-row__title">{{ product.name }}</h3>
        {% if product.description %}<p class="coric-product-row__desc">{{ product.description|truncatewords:25 }}</p>{% endif %}
        {% regroup product.specifications.all by section_label as spec_sections %}
        {% for section_group in spec_sections %}
          <details class="coric-product-row__accordion" {% if forloop.first %}open{% endif %}>
            <summary>
              {{ section_group.grouper }}
              <span class="coric-product-row__accordion-icon" aria-hidden="true">+</span>
            </summary>
            <table class="coric-product-row__specs-table">
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
        <a class="coric-button coric-button--primary" href="{{ product.get_absolute_url }}">{% translate "OPŠIRNIJE" %}</a>
      </div>
    </article>
    ```
  - **`{% regroup ... by section_label as spec_sections %}`** grupiše specifications po `section_label` annotation iz view-a (vidi AC2 `section_label` Case/When — instanciran per-request unutar `get_queryset()` per SM-D20). Queryset je već sortiran po `section_rank` (Motor=1, Transmisija=2, Hidraulika=3, Ostalo=4), pa `regroup` daje sekcije u tom redosledu. **`{{ section_group.grouper }}` direktno renderuje translated label** (npr. "Motor", "Transmisija" za sr locale; "Motor", "Hajtómű" za hu locale per LocaleMiddleware aktivni jezik) — NEMA potrebe za `|capfirst` filter-om ili manualnim translation chain-om u template-u (C9 fix).
  - **Display order rationale (C3 fix + Story 2.2 NOTE I3):** `ProductSpecification.Meta.ordering = ["product", "order", "id"]` SVESNO NE uključuje `section` jer alphabetical sort daje `hidraulika→motor→ostalo→transmisija` što je SUPROTNO od traženog Motor→Transmisija→Hidraulika→Ostalo display order-a. View-layer Case/When annotation (uvedena u AC2 za Story 2.6) je kanonski Django pattern za ovaj use-case (per Story 2.2 plan: "Display order će biti primenjen u Story 2.7 view-layer kroz Case/When annotation" — Story 2.6 implementira ovaj pattern jedna story ranije jer je akordion deo brand listing strane).
  - **Prazna sekcija se ne renderuje** — `regroup` automatski skroz preskače sections bez items.
  - **Prva accordion sekcija (Motor — section_rank=1) je `open` po default-u** (per epics.md Story 2.7 spec: "Motor default-open sa `+/-` toggle"); ostale su zatvorene. `<details open>` native HTML attribute. Pošto queryset je sorted po `section_rank`, `{% if forloop.first %}open{% endif %}` pouzdano otvara Motor sekciju (ne random prva po alphabetical).
  - **`+/-` toggle ikona** se animira kroz CSS (rotacija ili swap content) zasnovan na `details[open] summary::after` pseudo-element pattern-u.
  - Empty state isto kao Grid: ako `series.products.all` prazan → empty state poruka.
  - `data-testid="product-row-{slug}"` na svakom row-u.
- **And** akordion mora biti **keyboard-accessible** (native `<details>/<summary>` to garantuje besplatno — Enter/Space na `<summary>` toggle-uje sekciju).
- **And** akordion mora respektovati `prefers-reduced-motion: reduce` — CSS animacija toggle-a se onemogućava (instant open/close).

**AC6 — Statistic medaljon partial (`_statistics_medallions.html`) renderuje 4-circle grid (value + label only, BEZ ikona); `static/js/statistic-counter.js` (vanilla IIFE) implementira count-up animaciju triggered IntersectionObserver-om pri scroll-into-view; respektuje `prefers-reduced-motion: reduce` (instant set vrednost bez animacije)**

- **Given** AC3 završen; `brand.statistics` JSONField iz Story 2.1 sadrži listu do 4 dict-a sa ključevima `value` + `label` (npr. `[{"value": 5000, "label": "Prodatih traktora"}]`); **`icon` ključ je deferred to Story 9-10** (C7 fix — vidi Decision SM-D18)
- **When** kreiram `templates/brands/partials/_statistics_medallions.html`
- **Then** partial MORA:
  - Wrapper sekcija sa Section Eyebrow (`partials/section_eyebrow.html with text=_("STATISTIKE")`)
  - 4-medallion grid koji iterira `brand.statistics` — render-uje SAMO `value` + `label`, BEZ ikona:
    ```django
    <div class="coric-statistic-medallions" data-statistic-counters>
      {% for stat in brand.statistics|slice:":4" %}
        <div class="coric-statistic-medallion">
          <span class="coric-statistic-medallion__value" data-count-target="{{ stat.value }}" data-count-duration="1500">0</span>
          <span class="coric-statistic-medallion__label">{{ stat.label }}</span>
        </div>
      {% endfor %}
    </div>
    ```
  - `|slice:":4"` defensive guard ako admin omaške upiše > 4 entry-ja (Story 2.1 Brand.clean() već limitira na 4, ali defensive UI sloj).
  - `data-count-target` numerička vrednost koju JS animira ka.
  - `data-count-duration` u milisekundama (default 1500ms; CSS easing u JS).
- **And — Ikone deferred to Story 9-10 (C7 fix):** Bootstrap Icons font NIJE učitan u base.html niti u `static/vendor/` (live verifikovano 2026-05-30: `static/vendor/` sadrži samo `bootstrap-5.3.3`, `glightbox`, `htmx.min.js`). Render-ovanje `<i class="bi bi-...">` bi proizvelo prazne placeholder kvadratiće. Tri opcije (vendor font ~230KB, inline SVG mapping, ili defer) su razmotrene; Story 2.6 bira **defer** opciju (Decision SM-D18) — medaljoni u v1 renderuju minimalist "value + label" treatment. Wiring Bootstrap Icons font (`static/vendor/bootstrap-icons/`) + admin field za icon mapping je Story 9-10 Polish scope. **Posledica za admin (Story 8.4 brand admin):** `Brand.statistics` JSONField forma može i dalje da prima `icon` ključ u v1 (model sloj nema schema check za icon — Story 2.1 § soft validation potvrđuje "deep schema je Story 2.6 view-layer concern"), ali template ga ignoriše. Story 9-10 PR će dodati conditional render `{% if stat.icon %}...{% endif %}`.
- **When** kreiram `static/js/statistic-counter.js` (NOVO file)
- **Then** fajl MORA imati strukturu (vanilla IIFE, mirror Story 1.8 sticky-nav.js + 2.5 lightbox-init.js pattern):
  ```javascript
  /**
   * statistic-counter.js — count-up animacija za 4-medallion grid (Story 2.6).
   *
   * Vanilla JS, IIFE, no global pollution, no jQuery. Pri scroll-into-view
   * (IntersectionObserver), animira tekst svakog `[data-count-target]` elementa
   * od 0 do target vrednosti kroz `data-count-duration` ms (default 1500ms,
   * ease-out kubic).
   *
   * Respektuje `prefers-reduced-motion: reduce`: u tom slučaju instantno
   * postavlja target vrednost bez animacije (per project-context.md
   * § A11y must-haves linija 689 + UX-DR-13).
   *
   * Defensive: ako selektor `[data-statistic-counters]` nije na strani,
   * fajl silently exit-uje (omogućava global script tag u base.html).
   */
  (function () {
    'use strict';

    if (typeof window === 'undefined' || typeof document === 'undefined') {
      return;
    }

    var counterRoots = document.querySelectorAll('[data-statistic-counters]');
    if (counterRoots.length === 0) {
      return;  // strana nema medaljone — silently exit
    }

    var prefersReducedMotion = window.matchMedia
      ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
      : false;

    function animateCounter(el) {
      var target = parseInt(el.getAttribute('data-count-target'), 10);
      var duration = parseInt(el.getAttribute('data-count-duration') || '1500', 10);
      if (isNaN(target)) return;

      if (prefersReducedMotion) {
        el.textContent = target.toString();
        return;
      }

      var startTime = null;
      function step(timestamp) {
        if (!startTime) startTime = timestamp;
        var progress = Math.min((timestamp - startTime) / duration, 1);
        // Ease-out cubic
        var eased = 1 - Math.pow(1 - progress, 3);
        var current = Math.round(target * eased);
        el.textContent = current.toString();
        if (progress < 1) {
          window.requestAnimationFrame(step);
        }
      }
      window.requestAnimationFrame(step);
    }

    if (!('IntersectionObserver' in window)) {
      // Fallback: trigger odmah (no observer)
      counterRoots.forEach(function (root) {
        root.querySelectorAll('[data-count-target]').forEach(animateCounter);
      });
      return;
    }

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.querySelectorAll('[data-count-target]').forEach(animateCounter);
          observer.unobserve(entry.target);  // animiramo samo jednom
        }
      });
    }, { threshold: 0.3 });

    counterRoots.forEach(function (root) {
      observer.observe(root);
    });
  })();
  ```
- **And** fajl MORA biti IIFE wrapped sa `'use strict';`.
- **And** fajl MORA respektovati `prefers-reduced-motion: reduce`.
- **And** fajl MORA biti defensive — bail-uje silently ako nema `[data-statistic-counters]` na strani (site-wide script tag u base.html).
- **And** **NEMA jQuery, NEMA build pipeline, NEMA `import`/`export`**.
- **And** broj se prikazuje sa minimalnim format-om u v1 (raw integer); ako kasnije zatreba thousand separator (npr. 5.000), refaktor je trivijalan (`Intl.NumberFormat` poziv).

**AC7 — Testimonijali slider partial (`_testimonials_slider.html`) renderuje 1-na-vreme kartice sa prev/next + pause/play kontrolama; `static/js/testimonials-slider.js` (vanilla IIFE) implementira auto-advance, keyboard nav, focus pause, lightbox-open pause (Story 2.5 kontrakt), `prefers-reduced-motion` respect (no auto-advance)**

- **Given** AC2 završen (context ima `testimonials` queryset); Story 2.5 dispatch-uje `coric:lightbox-open` + `coric:lightbox-close` custom events na `window`
- **When** kreiram `templates/brands/partials/_testimonials_slider.html`
- **Then** partial MORA:
  - Wrapper sekcija sa Section Eyebrow (`partials/section_eyebrow.html with text=_("IZ PRVE RUKE")` per FR-19)
  - Slider markup:
    ```django
    <div class="coric-testimonials-slider"
         data-testimonials-slider
         data-autoadvance-ms="6000"
         role="region"
         aria-roledescription="{% translate 'karusel' %}"
         aria-label="{% translate 'Testimonijali korisnika' %}">
      <div class="coric-testimonials-slider__viewport">
        {% for t in testimonials %}
          <article class="coric-testimonials-slider__slide{% if forloop.first %} is-active{% endif %}"
                   role="group"
                   aria-roledescription="{% translate 'slajd' %}"
                   aria-label="{% blocktranslate with counter=forloop.counter total=testimonials|length %}{{ counter }} od {{ total }}{% endblocktranslate %}"
                   aria-hidden="{% if not forloop.first %}true{% endif %}">
            <blockquote class="coric-testimonials-slider__quote">{{ t.quote }}</blockquote>
            <p class="coric-testimonials-slider__attribution">
              {% if t.photo %}
                <span class="coric-testimonials-slider__photo">
                  {% responsive_picture t.photo alt=t.author_name sizes="80px" loading="lazy" %}
                </span>
              {% endif %}
              — {{ t.author_name }}{% if t.location %}, {{ t.location }}{% endif %}
            </p>
            {% if t.product %}
              <a class="coric-testimonials-slider__product-link" href="{{ t.product.get_absolute_url }}">{{ t.product.name }}</a>
            {% endif %}
          </article>
        {% endfor %}
      </div>
      <div class="coric-testimonials-slider__controls">
        <button type="button" class="coric-testimonials-slider__nav coric-testimonials-slider__nav--prev"
                data-slider-prev aria-label="{% translate 'Prethodni testimonijal' %}">‹</button>
        <button type="button" class="coric-testimonials-slider__pause"
                data-slider-pause aria-label="{% translate 'Pauziraj autoadvance' %}" aria-pressed="false">⏸</button>
        <button type="button" class="coric-testimonials-slider__nav coric-testimonials-slider__nav--next"
                data-slider-next aria-label="{% translate 'Sledeći testimonijal' %}">›</button>
      </div>
      <span class="visually-hidden" aria-live="polite" data-slider-live></span>
    </div>
    ```
  - **`ProductTestimonial` polja (C4 fix — live verifikovano `apps/products/models.py:464-499`):** Model ima polja `product` (FK), `photo` (ImageField optional), `quote` (TextField required), `author_name` (CharField required), `location` (CharField optional), `order` (PositiveSmallIntegerField), `created_at` (inherited iz TimestampedModel). **NEMA `author_role` polja.** Template renderuje `t.quote`, `t.author_name`, `t.location` (kao opcioni suffix uz `{% if t.location %}` guard), i conditionally `t.photo` kroz `{% if t.photo %}{% responsive_picture t.photo ... %}{% endif %}`. Open Question #1 iz prethodne verzije Dev Notes (TBD-PRE-DEV: verifikovati polja) — **resolved here**, uklonjen iz Dev Notes liste.
  - **`testimonials|length` u `blocktranslate` (C5 fix):** Prethodna verzija je koristila `{% blocktranslate count counter=forloop.counter %}...{{ total }}...{% endblocktranslate %}` što je BROKEN — `count`/`counter` su za pluralization (singular vs plural form), NE za format-string variable. Pravilna sintaksa za "X od Y" string je `{% blocktranslate with counter=forloop.counter total=testimonials|length %}{{ counter }} od {{ total }}{% endblocktranslate %}`. `testimonials|length` je QuerySet length (Django evaluuje queryset; pošto context queryset ima `[:10]` slice, len je ≤10).
- **When** kreiram `static/js/testimonials-slider.js` (NOVO file)
- **Then** fajl MORA implementirati (vanilla IIFE):
  ```javascript
  /**
   * testimonials-slider.js — slider sa pause/play + keyboard nav (Story 2.6).
   *
   * Vanilla JS, IIFE. Auto-advance svakih [data-autoadvance-ms] ms (default 6000).
   * Pauzira na: focus unutar slider-a, hover, klik na pause button, ili kad se
   * dispatch-uje `coric:lightbox-open` event na window (Story 2.5 kontrakt —
   * dok je Lightbox modal otvoren, slider ne sme da napreduje da ne yanka focus).
   * Resume na: `coric:lightbox-close` event ako pre toga nije bio manualno pauziran.
   *
   * Respektuje `prefers-reduced-motion: reduce`: NEMA auto-advance (samo manual prev/next).
   *
   * Keyboard: Arrow Left → prev, Arrow Right → next (samo kad fokus unutar slider-a).
   * `aria-live="polite"` najavi "Slajd X od Y" pri promeni.
   */
  (function () {
    'use strict';

    if (typeof window === 'undefined' || typeof document === 'undefined') return;

    var sliders = document.querySelectorAll('[data-testimonials-slider]');
    if (sliders.length === 0) return;  // strana nema slider — silently exit

    var prefersReducedMotion = window.matchMedia
      ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
      : false;

    sliders.forEach(function (slider) {
      var slides = slider.querySelectorAll('.coric-testimonials-slider__slide');
      if (slides.length < 2) {
        // Single-slide ili prazno — sakrij nav controls
        var controls = slider.querySelector('.coric-testimonials-slider__controls');
        if (controls) controls.style.display = 'none';
        return;
      }

      var current = 0;
      var manuallyPaused = false;
      var autoTimer = null;
      var autoMs = parseInt(slider.getAttribute('data-autoadvance-ms') || '6000', 10);
      var live = slider.querySelector('[data-slider-live]');
      var pauseBtn = slider.querySelector('[data-slider-pause]');

      function showSlide(idx) {
        slides.forEach(function (s, i) {
          var active = i === idx;
          s.classList.toggle('is-active', active);
          s.setAttribute('aria-hidden', active ? 'false' : 'true');
        });
        current = idx;
        if (live) {
          live.textContent = (idx + 1) + ' / ' + slides.length;
        }
      }

      function next() { showSlide((current + 1) % slides.length); }
      function prev() { showSlide((current - 1 + slides.length) % slides.length); }

      function startAuto() {
        if (prefersReducedMotion || manuallyPaused) return;
        stopAuto();
        autoTimer = window.setInterval(next, autoMs);
      }
      function stopAuto() {
        if (autoTimer) { window.clearInterval(autoTimer); autoTimer = null; }
      }

      // Manual prev/next — I5 fix: ne auto-restart-uje. Korisnik je eksplicitno
      // signalizirao kontrolu nad slider-om; auto-advance se vraća tek na
      // focusout (resumeIfAllowed) ili klik na pause/play da otključa.
      var prevBtn = slider.querySelector('[data-slider-prev]');
      var nextBtn = slider.querySelector('[data-slider-next]');
      if (prevBtn) prevBtn.addEventListener('click', function () { stopAuto(); prev(); });
      if (nextBtn) nextBtn.addEventListener('click', function () { stopAuto(); next(); });

      // Pause/play toggle — eksplicitni togle uvek smetala manualPaused flag.
      // Klik na ▶ (play) je JEDINI način da se auto-advance ponovo pokrene
      // nakon manual interakcije (per I5 fix).
      if (pauseBtn) {
        pauseBtn.addEventListener('click', function () {
          manuallyPaused = !manuallyPaused;
          pauseBtn.setAttribute('aria-pressed', manuallyPaused ? 'true' : 'false');
          pauseBtn.textContent = manuallyPaused ? '▶' : '⏸';
          if (manuallyPaused) { stopAuto(); } else { startAuto(); }
        });
      }

      // Keyboard nav (only when focus is inside slider) — I5 fix: NE auto-restart.
      slider.addEventListener('keydown', function (e) {
        if (e.key === 'ArrowLeft') { e.preventDefault(); stopAuto(); prev(); }
        if (e.key === 'ArrowRight') { e.preventDefault(); stopAuto(); next(); }
      });

      // Focus pause (a11y must-have per project-context.md § A11y must-haves) —
      // I5 fix: auto-advance se NASTAVLJA samo kad fokus napušta slider
      // (focusout) i kursor napušta hover (mouseleave). Manual interakcija
      // (prev/next/keyboard) NE trigger-uje auto-restart — vraćanje se dešava
      // tek na blur/focus-leave.
      slider.addEventListener('focusin', stopAuto);
      slider.addEventListener('focusout', startAuto);
      slider.addEventListener('mouseenter', stopAuto);
      slider.addEventListener('mouseleave', startAuto);

      // Lightbox integration (Story 2.5 kontrakt)
      window.addEventListener('coric:lightbox-open', stopAuto);
      window.addEventListener('coric:lightbox-close', startAuto);

      // Init: show first slide + start auto (if not reduced-motion)
      showSlide(0);
      startAuto();
    });
  })();
  ```
- **And — I5 napomena (a11y rationale):** Auto-advance se ne restart-uje nakon manual prev/next/keyboard interakcije jer korisnik sa motor/cognitive disability-jem koji manualno navigira ne želi da slider iznenada "skoči" nakon 6s. Auto-advance resume-uje tek na focus-leave (signal "korisnik je prešao na drugi element") ili explicit play button click. Hover/focus pause/resume su NEPROMENJENI (pasivna interakcija).
- **And** fajl MORA biti IIFE, `'use strict';`, defensive bail.
- **And** Pause button MORA biti keyboard-accessible (`<button>` element + `aria-pressed` toggle); fokus indicator MORA biti vidljiv (CSS `:focus-visible` outline iz tokens.css `--color-accent-gold-500`).
- **And** **NEMA jQuery, NEMA Bootstrap Carousel** (custom da imamo kontrolu nad lightbox integration + reduced-motion semantics; Bootstrap Carousel ne nudi clean way da pauzira na custom event).

**AC8 — CSS komponente (`brand-listing.css`, `statistic-medallion.css`, `testimonials-slider.css`) postoje u `static/css/components/`; `main.css` ima 3 nove `@import url('./components/...');` linije TAČNO mirror Story 1.7+1.8+2.5 pattern; svi stilovi koriste isključivo `var(--token)` reference iz `tokens.css`; svi BEM klase imaju `coric-` prefix**

- **Given** AC4-AC7 završeni; Story 1.5 `tokens.css` definiše sve potrebne tokene; Story 1.7 + 1.8 + 2.5 main.css pattern (`@import url('./components/...');` sa `url(...)` wrap-erom i leading `./`)
- **When** kreiram 3 nova CSS fajla i editujem main.css
- **Then**:
  - `static/css/components/brand-listing.css` MORA sadržati:
    - `.coric-brand-detail` — root wrapper sa max-width: var(--layout-container-max) (ili Bootstrap container reuse — Decision SM-D15)
    - `.coric-brand-series` sekcija stilovi
    - `.coric-series-block` per-series article wrapper sa `margin-bottom: var(--spacing-scale-6)` itd.
    - `.coric-product-card` Grid kartica: linkable, hover/focus state (transform + shadow), Bootstrap card-style sa nashim tokenima
    - `.coric-product-card__image`, `.coric-product-card__body`, `.coric-product-card__title`, `.coric-product-card__cta`
    - `.coric-product-row` Extended layout flex/grid (slika levo 60% / specs desno 40%, mobile stack vertikalno)
    - `.coric-product-row__image`, `.coric-product-row__specs`, `.coric-product-row__accordion` (`<details>` styling)
    - `.coric-empty-state` minimal text styling za empty cases
    - `.coric-catalog-cta-banner` banner stil sa background gradient ili solid token color
    - **Coming-soon brand template selektori (AC2.5 markup — I-iter2-2 fix):**
      - `.coric-brand-coming-soon` — centered wrapper: `padding: var(--spacing-scale-6) var(--spacing-scale-4); max-width: 600px; margin: 0 auto; text-align: center;`
      - `.coric-brand-coming-soon__logo` — logo container: `max-width: 240px; margin: 0 auto var(--spacing-scale-4); display: block;`
      - `.coric-brand-coming-soon__title` — naslov: `font-size: var(--typography-scale-h1); color: var(--color-brand-green-800); margin-bottom: var(--spacing-scale-3);`
      - `.coric-brand-coming-soon__message` — message text: `font-size: var(--typography-scale-body); color: var(--color-neutral-gray-700); margin-bottom: var(--spacing-scale-4);`
      - `.coric-pill-badge` — base pill (reuse-able): `display: inline-block; padding: var(--spacing-scale-1) var(--spacing-scale-3); border-radius: var(--rounded-pill); font-size: var(--typography-scale-small); font-weight: var(--typography-weight-bold); letter-spacing: var(--typography-tracking-wide); text-transform: uppercase;`
      - `.coric-pill-badge--coming-soon` — variant: `background: var(--color-accent-gold-500); color: var(--color-brand-green-800);`
    - **Product placeholder selektori (Subtask 1.5 / AC2.6 markup — I-iter2-4 fix, scope per SM-D21):**
      - `.coric-product-placeholder` — centered wrapper: `padding: var(--spacing-scale-8) var(--spacing-scale-4); max-width: 600px; margin: 0 auto; text-align: center;`
      - `.coric-product-placeholder__title` — naslov: `font-size: var(--typography-scale-h2); color: var(--color-brand-green-800); margin-bottom: var(--spacing-scale-4);`
      - `.coric-product-placeholder__message` — message: `font-size: var(--typography-scale-body); color: var(--color-neutral-gray-700); margin-bottom: var(--spacing-scale-5);`
    - **NAPOMENA:** `.coric-button` i `.coric-button--primary` su base klase iz Story 1.7 `static/css/components/pill-button.css` (već site-wide loaded kroz `main.css`) — `brand-listing.css` ih SAMO KORISTI u markup-u (coming-soon CTA, catalog CTA, placeholder CTA), NE re-definiše. Ako Dev primeti da `pill-button.css` ne definiše ove klase (regression check), ESCALATE kroz Step-04 review — Story 2.6 ne sme dodavati `coric-button` base styles (out-of-scope, krši Story 1.7 boundary).
    - `@media (prefers-reduced-motion: reduce)` blok koji uklanja transform/transition na `.coric-product-card`
  - `static/css/components/statistic-medallion.css` MORA sadržati:
    - `.coric-statistic-medallions` grid wrapper (4-col desktop, 2-col tablet, 1-col mobile kroz CSS Grid)
    - `.coric-statistic-medallion` circular medallion (border-radius: 50%, background gradient ili solid token color)
    - `.coric-statistic-medallion__icon` Bootstrap Icon styling (size, color)
    - `.coric-statistic-medallion__value` velika cifra (`var(--typography-scale-display-1)` ili sličan token)
    - `.coric-statistic-medallion__label` mali tekst
    - `@media (prefers-reduced-motion: reduce)` opcioni (CSS nema animacija; JS već handle-uje reduce — defensive blok ipak prisutan)
  - `static/css/components/testimonials-slider.css` MORA sadržati:
    - `.coric-testimonials-slider` root container
    - `.coric-testimonials-slider__viewport` sa overflow-hidden, relative pozicioniranjem
    - `.coric-testimonials-slider__slide` apsolutno pozicionirano, `opacity: 0` default, `.is-active` → `opacity: 1` + `z-index: 1`
    - `.coric-testimonials-slider__quote` blockquote stiling (italic, larger font, leading-quote ornament opciono)
    - `.coric-testimonials-slider__controls` flex layout
    - `.coric-testimonials-slider__nav`, `.coric-testimonials-slider__pause` button styling (transparent bg, hover effect, focus-visible outline)
    - `@media (prefers-reduced-motion: reduce)` — transition: none na slide opacity (instant swap)
- **And** SVI CSS pravila MORAJU koristiti `var(--token)` za boje, spacing, typography (sve postoje u tokens.css iz Story 1.5; ako se naleti na manjak token-a, **NE uvoditi nove tokene u tokens.css u ovoj story** — koristiti najbliži postojeći token + dokumentovati u Dev Notes Completion Notes kao tech debt za Story 2.x design-tokens refresh).
- **And** SVI BEM klase MORAJU imati `coric-` prefix (per project-context.md § CSS naming linija 315).
- **And** `static/css/main.css` MORA dobiti 3 nove `@import` linije TAČNO mirror Story 1.7+1.8+2.5 sintaksu (sa `url(...)` wrap-erom + leading `./` + trailing semicolon):
  ```css
  @import url('./components/brand-listing.css');
  @import url('./components/statistic-medallion.css');
  @import url('./components/testimonials-slider.css');
  ```
- **And** Edit `main.css` MORA biti **targeted Edit** koji ZADRŽAVA sve postojeće linije; nove linije idu na kraj postojećih `@import` linija (NE presretati postojeći stacking order — Story 1.7+1.8+2.5 ostaju netaknute).
- **And** `templates/base.html` MORA dobiti 2 nova `<script>` tag-a sa `defer` POSLE `lightbox-init.js`:
  ```html
  <script src="{% static 'js/statistic-counter.js' %}" defer></script>
  <script src="{% static 'js/testimonials-slider.js' %}" defer></script>
  ```
  Edit je **targeted** (postojeće linije netaknute; nove idu PRE postojećeg Django komentara `{# Per-page scripts POSLE site-wide ... #}`).
- **And** **NEMA `cdn.jsdelivr.net`, `unpkg.com`, `cdnjs.cloudflare.com`** reference u bilo kojem novom fajlu (anti-CDN guard, mirror Story 1.6 + 2.5 pattern).

**AC9 — Manuelni Dev smoke check + Lighthouse a11y skor ≥ 95 na lokalnoj instanci**

- **Given** AC1-AC8 završeni; sample seed podaci postoje u DB za bar 1 Brand sa: logo, slogan, brand_color, statistics (4 entry-ja), catalog_pdf, 2 serije (1 Grid + 1 Extended) sa po 3 published Product-a (sa main_image i specifications); 3 ProductTestimonial entry-ja
- **When** Dev pokreće `just dev` (Docker Compose local) i otvara `http://localhost:8000/sr/traktori/<seed-brand-slug>/` u Chrome
- **Then** Dev verifikuje (manuelni checklist):
  - Hero overlay sekcija renderuje: brand logo + Repeating Element watermark (varijanta odgovara brand_color mapping-u); responzivan na mobile (375px width)
  - 4 statistike-medaljona renderuju sa correct icon+value+label; count-up animacija se okida pri scroll-into-view (DevTools Performance Recording verifikuje requestAnimationFrame poziva)
  - Testimonijali slider radi: pause/play button toggle-uje auto-advance (verifikuj `aria-pressed` change i text content change `⏸ ↔ ▶`); prev/next dugmad rade; Arrow Left/Right na fokusiranom slider-u promene slajd; fokus unutar slider-a pauzira auto-advance (focusin)
  - Serije sekcija renderuje 2 serije; Grid serija prikazuje 2-col kartice (desktop) / 1-col (mobile); Extended serija prikazuje 1-row layout sa akordion-ima; akordion Motor sekcija je open by default, druge zatvorene; klik na summary toggle-uje sekciju
  - "Preuzmi katalog" CTA banner renderuje sa Wave Divider iznad; klik na "PREUZMI" otvara PDF u novom tabu (`brand.catalog_pdf.url`)
  - **Empty states verifikuju:**
    - Testiraj brand bez statistics — sekcija medaljona SE NE renderuje (no empty container)
    - Testiraj brand bez testimonijala — slider SE NE renderuje
    - Testiraj brand bez catalog_pdf — CTA banner SE NE renderuje
    - Testiraj seriju bez published Product-a — empty state poruka "Modeli ove serije su u pripremi."
  - **`prefers-reduced-motion` test:** uključi `prefers-reduced-motion: reduce` u Chrome DevTools Rendering panel; reload strane; verifikuj:
    - Statistike: vrednost se postavi instantno (no count-up animation)
    - Slider: nema auto-advance (samo manual prev/next radi)
    - Akordion: instant open/close (no CSS transition)
  - **`is_coming_soon` test:** posetiti URL brenda sa `is_coming_soon=True` — render minimal coming-soon template (no statistike, no serije, no testimonijali)
- **And** Dev pokreće Lighthouse audit (Chrome DevTools Lighthouse tab → Generate report → Mobile + Accessibility category):
  - **Accessibility score ≥ 95** (UX-DR-13 + NFR-2 traget; Story 9.9 audit gate)
  - Common Lighthouse a11y fail points to prevent:
    - Insufficient color contrast — kontrast `var(--color-brand-green-800)` text na white background mora biti ≥ 4.5:1 (Story 1.5 tokens su validated)
    - Missing alt text on images — sve `<img>` kroz `{% responsive_picture %}` MORAJU imati `alt` parametar prosleđen iz kontekst-a (product.name ili brand.name)
    - Buttons without accessible name — pause/prev/next buttons MORAJU imati `aria-label`
    - `<html>` lang attribute — već postavljen kroz `{{ LANGUAGE_CODE }}` u base.html iz Story 1.4
    - Focus order linear — keyboard Tab traverza: skip link → header → hero CTA → medaljoni (ako linkabilni; v1 nisu) → testimonijal slider prev → pause → next → serije karticе → catalog CTA → footer
  - **Performance score ≥ 75** (lighter target — slike su lazy-loaded ali nismo optimizovali WebP/AVIF u 2.6; Story 9.10 polish)
- **And — Lighthouse JSON artifact preservation (I-iter2-8 fix, audit-gate alignment sa Story 9.9):** Dev MORA pokrenuti Lighthouse u CLI mode-u (NE samo Chrome DevTools manual run) i sačuvati JSON output kao artifact:
  ```bash
  # Iz Story 2.6 Dev workstation; pretpostavlja se da je `lighthouse` CLI instaliran globalno (npm i -g lighthouse)
  lighthouse http://localhost:8000/sr/traktori/agri-tracking/ \
    --output=json \
    --output-path=_bmad-output/implementation-artifacts/2-6-lighthouse-$(date +%Y%m%d).json \
    --only-categories=accessibility,performance,seo \
    --form-factor=mobile \
    --chrome-flags="--headless"
  ```
  - **Dev MORA citirati skor-ove u `Dev Agent Record § Completion Notes` sekciji story fajla PRE Step-04 Code Review:** "Lighthouse skor (mobile): a11y={N}, performance={M}, seo={K}; JSON artifact: `_bmad-output/implementation-artifacts/2-6-lighthouse-YYYYMMDD.json`."
  - **Razlog:** Story 9.9 (a11y audit + Lighthouse pass) audit-gate zahteva da svaki listing/detail story ima preserved Lighthouse JSON za baseline-trend-tracking (regresion detection); manual DevTools run bez JSON artifact-a nije reproducible. Story 9.9 će rerun Lighthouse i compare protiv Story 2.6 baseline-a — bez baseline-a, regression detection je nemoguć.
  - Ako CLI lighthouse nije instaliran u dev environment-u (npr. headless server, no npm), alternativa je Chrome DevTools Lighthouse run → Save report (JSON) → manuelno kopirati u `_bmad-output/implementation-artifacts/2-6-lighthouse-YYYYMMDD.json`. CLI je preferred (reproducible flags), ali manual save je acceptable fallback.
- **Napomena:** Ovaj AC je **manuelni smoke check** koji Dev izvršava pre commit-a; automated E2E je Story 9.8 (Playwright UJ-1) scope, automated a11y axe-core je Story 9.9 scope. Dev dokumentuje rezultate u `Dev Agent Record § Completion Notes`.

## Tasks / Subtasks

- [x] **Task 1: `apps/brands/views.py` + `apps/brands/urls.py` + `apps/products/{views,urls}.py` placeholder + `config/urls.py` wiring (AC1, AC2, C8 fix)**
  - [x] Subtask 1.1: Kreirati `apps/brands/views.py` sa `BrandDetailView(DetailView)` per AC2 source code (Case/When section_rank + section_label annotation, get_template_names override, order_by("order", "-created_at") za testimonijale)
  - [x] Subtask 1.2: Kreirati `apps/brands/urls.py` sa `app_name = "brands"` + `path("traktori/<slug:slug>/", BrandDetailView.as_view(), name="detail")` — TAČAN URL kwarg `slug` matches `Brand.get_absolute_url()` iz Story 2.1 (C1 fix)
  - [x] Subtask 1.3: Kreirati `apps/products/views.py` sa `placeholder_view(request, slug)` FBV koji renderuje `templates/products/_placeholder.html` (HTTP 200; minimalan "Stranica još nije dostupna — uskoro" template). Spečuje `NoReverseMatch` runtime kada brand listing kartica linkuje na `{% url 'products:detail' slug=... %}` pre Story 2.7 (C8 fix)
  - [x] Subtask 1.4: Kreirati `apps/products/urls.py` sa `app_name = "products"` + `path("proizvod/<slug:slug>/", views.placeholder_view, name="detail")` (matches `Product.get_absolute_url()` iz Story 2.2)
  - [x] Subtask 1.5: Kreirati `templates/products/_placeholder.html` per AC2.6 TAČAN markup spec (`{% extends "base.html" %}` + `{% load i18n %}` + `{% block extra_head %}<meta name="robots" content="noindex, nofollow">{% endblock %}` + `<main role="main" class="coric-product-placeholder">` wrapper + `<h1 class="coric-product-placeholder__title">` + `<p class="coric-product-placeholder__message">` + `<a class="coric-button coric-button--primary">` nazad-na-Home CTA; sve string-ove kroz `{% translate %}`). **PREREQ:** Verifikovati da `templates/base.html` ima `{% block extra_head %}{% endblock %}` u `<head>` sekciji (ako nema, dodati pre Subtask 1.5 — vidi AC2.6 § Pretpostavka). I-iter2-4 fix obezbeđuje noindex za SEO.
  - [x] Subtask 1.6: Editovati `config/urls.py` da doda `path("", include("apps.brands.urls"))` + `path("", include("apps.products.urls"))` UNUTAR `i18n_patterns(...)` blok-a PRE `path("", include("apps.core.urls"))`
  - [x] Subtask 1.7: **VERIFY-ONLY** — Otvoriti `_bmad-output/project-context.md` i verifikovati da § Cross-boundary import sekcija (linije ~619-632) sadrži exception note za `apps/brands/views.py` → `apps.products.models` import izuzetak. **FACT (verifikovano 2026-05-30 pre SM Fix iter 2):** Note JE već primenjen u sklopu Story 2.6 validacionog fix iter 1 — Dev SAMO čita i verifikuje prisustvo bullet-a koji počinje sa "**Exception** (Story 2.6+): `apps/brands/views.py` SME importovati `Product`, `ProductSpecification`, `ProductTestimonial`...". **NIJE potrebno editovati fajl.** Ako (regression) bullet nedostaje, dodati per tekst iz Dev Notes § "Cross-boundary import izuzetak (C2 fix — load-bearing project-context.md EDIT)" sekcije. Ova subtask je no-op u srećnom slučaju.
  - [x] Subtask 1.8: Smoke verifikacija — `uv run python manage.py check` exit code 0; URL reverse check kroz stock Django shell (I8 fix — NE koristiti `manage.py show_urls` koji zahteva `django-extensions`):
    ```bash
    uv run python manage.py shell -c "from django.urls import reverse; \
      from django.utils.translation import activate; activate('sr'); \
      print(reverse('brands:detail', kwargs={'slug': 'agri-tracking'})); \
      print(reverse('products:detail', kwargs={'slug': 'test-slug'}))"
    ```
    Očekivan output: `/sr/traktori/agri-tracking/` + `/sr/proizvod/test-slug/`

- [x] **Task 2: `templates/brands/brand_detail.html` + `brand_coming_soon.html` glavni templates (AC3, AC2 coming-soon path, AC2.5 minimal markup spec)**
  - [x] Subtask 2.1: Kreirati `templates/brands/brand_detail.html` sa `{% extends "base.html" %}` strukturom per AC3 spec
  - [x] Subtask 2.2: Kreirati `templates/brands/brand_coming_soon.html` minimal coming-soon template per AC2.5 source code — wrapper `<div class="coric-brand-coming-soon">` (NE drugi `<main>` per interface contract § 4, nested-main HTML5 violation guard)
  - [x] Subtask 2.3: Verifikovati da svi user-facing string-ovi koriste `{% translate %}` / `{% blocktranslate %}`; NEMA hardcoded srpski string-ova; NEMA ćirilice

- [x] **Task 3: `_hero_section.html` partial (AC3, AC3 § hero overlay)**
  - [x] Subtask 3.1: Kreirati `templates/brands/partials/_hero_section.html` wrapper koji prosleđuje brand kontekst u `partials/hero_overlay_card.html` (Story 1.7 partial)
  - [x] Subtask 3.2: Implementirati `brand.brand_color → variant` mapping helper (template `{% if %}` per SM-D11)
  - [x] Subtask 3.3: Hero card prima: title=brand.name, brand_logo=brand.logo.url (defensively guarded via `{% if brand.logo %}`), brand_logo_alt=brand.name, variant=mapped, bullets="" (empty u v1)

- [x] **Task 4: `_statistics_medallions.html` partial + `static/js/statistic-counter.js` (AC6, C7 fix)**
  - [x] Subtask 4.1: Kreirati `templates/brands/partials/_statistics_medallions.html` sa Section Eyebrow + 4-medallion grid markup. **NEMA `<i class="bi bi-...">` elementa** (C7 fix)
  - [x] Subtask 4.2: Defensive `|slice:":4"` filter
  - [x] Subtask 4.3: Kreirati `static/js/statistic-counter.js` sa IIFE + IntersectionObserver + prefers-reduced-motion respect per AC6 source code
  - [x] Subtask 4.4: Verifikovati nema jQuery, nema `import`/`export`, nema inline event handlers; `'use strict';` prisutan

- [x] **Task 5: `_testimonials_slider.html` partial + `static/js/testimonials-slider.js` (AC7)**
  - [x] Subtask 5.1: Kreirati `templates/brands/partials/_testimonials_slider.html` koji renderuje TAČNA polja `ProductTestimonial` modela
  - [x] Subtask 5.2: Implementirati slider markup sa role=region + aria-label + aria-roledescription + pause/play + prev/next per AC7 source
  - [x] Subtask 5.3: Kreirati `static/js/testimonials-slider.js` sa IIFE + auto-advance + keyboard nav + focus pause + lightbox event integration + prefers-reduced-motion respect per AC7 source code
  - [x] Subtask 5.4: Verifikovati keyboard handlers prisutni (run-time test verifikuje data-testid; manual smoke je AC9)

- [x] **Task 6: `_series_section.html` + `_series_grid.html` + `_series_extended.html` partials (AC3, AC4, AC5)**
  - [x] Subtask 6.1: Kreirati `templates/brands/partials/_series_section.html` iterator wrapper koji branch-uje na `series.layout_mode`
  - [x] Subtask 6.2: Kreirati `templates/brands/partials/_series_grid.html` linkable card pattern per AC4 source
  - [x] Subtask 6.3: Kreirati `templates/brands/partials/_series_extended.html` flex layout sa `{% regroup ... by section_label %}` akordion pattern per AC5
  - [x] Subtask 6.4: Verifikovati empty states (per-series no products → empty state poruka; per-brand no series → empty state)
  - [x] Subtask 6.5: Verifikovati `data-testid` atributi prisutni (product-card-{slug}, product-row-{slug})

- [x] **Task 7: `_catalog_cta.html` partial (AC3 § CTA banner)**
  - [x] Subtask 7.1: Kreirati `templates/brands/partials/_catalog_cta.html` koji include-uje `partials/wave_divider.html with position="top"` + Section Eyebrow + heading + description + **direktan `<a>` markup (NE `partials/pill_button.html` partial — vidi SM-D22 + I-iter2-6 fix)** sa atributima `href="{{ brand.catalog_pdf.url }}" target="_blank" rel="noopener noreferrer" download class="coric-button coric-button--primary" data-testid="brand-catalog-download"`. Razlog: Story 1.7 pill_button partial ne podržava `target`/`rel`/`download` kwarg-e; modifying partial je out-of-scope (breaking change risk za sve postojeće konzumente). Vizuelni parity kroz reuse `coric-button coric-button--primary` BEM klase iz Story 1.7 pill-button.css (site-wide loaded).

- [x] **Task 8: 3 nova CSS komponentna fajla + `main.css` Edit + `base.html` Edit (AC8)**
  - [x] Subtask 8.1: Kreirati `static/css/components/brand-listing.css` sa svim selektorima iz AC8 listing-a, isključivo `var(--token)` reference
  - [x] Subtask 8.2: Kreirati `static/css/components/statistic-medallion.css`
  - [x] Subtask 8.3: Kreirati `static/css/components/testimonials-slider.css`
  - [x] Subtask 8.4: Editovati `static/css/main.css` — dodati 3 nove `@import url('./components/...');` linije
  - [x] Subtask 8.5: Editovati `templates/base.html` — dodati 2 nova `<script>` tag-a sa `defer` POSLE `lightbox-init.js`
  - [x] Subtask 8.6: Verifikovati nema CDN referenci u novim fajlovima
  - [x] Subtask 8.7: Verifikovati svi BEM klasi imaju `coric-` prefix; svi CSS koriste `var(--token)` reference

- [ ] **Task 9: Manuelni Dev smoke check + Lighthouse a11y audit (AC9)**
  - [ ] Subtask 9.1: Dev pokrene `just dev` (Docker Compose local)
  - [ ] Subtask 9.2: Dev seed-uje sample podatke (Django shell ili admin GUI) za bar 1 Brand sa svim potrebnim poljima (statistics, catalog_pdf, 2 serije sa Grid + Extended layouts, published Products sa specifications, ProductTestimonials)
  - [ ] Subtask 9.3: Dev poseti `http://localhost:8000/sr/traktori/<seed-brand-slug>/` u Chrome; verifikuje sve sekcije rade per AC9 checklist
  - [ ] Subtask 9.4: Dev aktivira `prefers-reduced-motion: reduce` u DevTools Rendering panel; reload; verifikuje statistike instant, slider no auto-advance, akordion no transition
  - [ ] Subtask 9.5: Dev testira coming-soon stanje (privremeno setuje `brand.is_coming_soon=True` u shell-u, reload, verifikuje minimal template)
  - [ ] Subtask 9.6: Dev pokrene Lighthouse audit u CLI mode-u (per AC9 § Lighthouse JSON artifact preservation, I-iter2-8 fix): `lighthouse http://localhost:8000/sr/traktori/agri-tracking/ --output=json --output-path=_bmad-output/implementation-artifacts/2-6-lighthouse-$(date +%Y%m%d).json --only-categories=accessibility,performance,seo --form-factor=mobile --chrome-flags="--headless"`. Verifikuje Accessibility ≥ 95 + Performance ≥ 75; dokumentuje sve 3 skor-ove (a11y/performance/seo) u Dev Agent Record § Completion Notes sekciji story fajla PRE Step-04 commit (audit-gate alignment sa Story 9.9). Ako CLI nije dostupan, fallback je manual Chrome DevTools save-as-JSON u istu putanju.
  - [ ] Subtask 9.7: Dev verifikuje keyboard nav: skip link → Tab kroz sve interaktivne elemente; fokus indicator vidljiv (`:focus-visible` outline iz tokens)

- [ ] **Task 10: TEA-deliverable — testovi (RED phase, Step 3, NIJE Dev scope)** _(NAPOMENA: ovaj task je listed for clarity — TEA agent u Step 3 piše testove pre Dev-ovog GREEN phase implementacije; Dev NIKAD ne piše testove per project-context.md § Test discipline linija 294)_
  - **Minimum test count per AC (I7 fix — mirror Stories 2-3 i 2-5 konvencija):** ~30 tests total
  - [ ] Subtask 10.1: TEA kreira `apps/brands/tests/test_urls.py` — **AC1: 5 tests**
    - test_brand_detail_url_resolves_sr_locale (200 za postojeći brand sa `slug="agri-tracking"` na /sr/)
    - test_brand_detail_url_resolves_hu_locale (200 na /hu/)
    - test_brand_detail_url_resolves_en_locale (200 na /en/)
    - test_brand_detail_404_for_nonexistent_slug (404 za /sr/traktori/nepostojeci/)
    - test_append_slash_redirect_for_missing_trailing_slash (301/302 za /sr/traktori/agri-tracking)
  - [ ] Subtask 10.2: TEA kreira `apps/brands/tests/test_views.py` — **AC2: 4 tests**
    - test_context_contains_brand_and_testimonials_only (no `series_list` key — I2 fix)
    - test_assert_num_queries_equals_5 (with assertNumQueries(5) — I1 fix; brand + series prefetch + product prefetch + spec prefetch + testimonial filter)
    - test_coming_soon_brand_renders_brand_coming_soon_template (uses Client + assertTemplateUsed; testimonials NIJE u kontekstu)
    - test_404_when_brand_does_not_exist
  - [ ] Subtask 10.3: TEA kreira `apps/brands/tests/test_templates.py` — sve preostale AC-ove:
    - **AC3: 2 tests** — test_sections_render_in_correct_order (hero → statistike → testimonijali → serije → catalog_cta); test_aria_landmarks_present (`<main>`, `<section aria-labelledby>` na svim sekcijama)
    - **AC4 grid: 3 tests** — test_product_card_markup_structure (a + img + h3 + cta span); test_data_testid_present (`data-testid="product-card-{slug}"`); test_a11y_attributes (aria-label na `<a>`, aria-hidden=true na CTA span — I6 fix)
    - **AC5 extended: 4 tests** — test_regroup_orders_sections_motor_first (rank-based ordering — C3); test_motor_section_open_by_default (`<details open>` na prvoj); test_empty_section_skipped (products bez specs ne renderuju akordion); test_accordion_uses_native_details_summary
    - **AC6 medallions: 3 tests** — test_medallion_renders_value_and_label_without_icon (C7 fix — no `<i class="bi">` element); test_intersection_observer_mock_triggers_count_up (JS unit-style ili integration kroz Playwright); test_prefers_reduced_motion_instant_set
    - **AC7 testimonials: 4 tests** — test_slider_markup_renders_with_aria_roles; test_pause_play_button_toggle_aria_pressed; test_keyboard_arrow_navigation_works; test_single_testimonial_hides_controls (kad `testimonials|length == 1`)
  - [ ] Subtask 10.4: TEA kreira `apps/brands/tests/test_coming_soon.py` — AC2.5 (C6 fix): tests da minimal template renderuje h1 sa brand.name + pill-badge "Uskoro" sa role=status + nazad-na-Home CTA; tests da statistike/serije/testimonijali sekcije NISU prisutne u DOM-u. **Dodatni test (I-iter2-1 fix — locale-aware Case/When verifikacija):** `test_extended_layout_section_labels_hu` — render `brand_detail.html` pod `LANGUAGE_CODE='hu'` (kroz `override_settings` ili `translation.override('hu')` decorator) sa seed brand-om koji ima Extended seriju + product sa specifications iz svih 4 sekcija (motor/transmisija/hidraulika/ostalo); parsovati render-ovan HTML i asertovati da `<details><summary>` elementi sadrže hu-locale prevode (npr. ako `locale/hu/LC_MESSAGES/django.po` mapira "Transmisija" → "Hajtómű", test asertuje "Hajtómű" prisutnost). **Cilj testa:** verifikovati da `section_label` Case/When per-request konstrukcija (SM-D20) zaista re-evaluuje translation u svakom request-u — ako se test izvrši prvo sa sr lokalom pa onda sa hu lokalom (ili obrnuto), oba moraju vratiti svoje native prevode (no "frozen language" bug). Suite mora kontaminirati Django translation cache između testova (`translation.deactivate()` u tearDown ili koristiti pytest fixture). Ako hu prevodi `locale/hu/LC_MESSAGES/django.po` ne postoje za "Motor"/"Transmisija"/"Hidraulika"/"Ostalo" entry-je, dodati ih (out-of-scope za 2.6 ali blokira ovaj test ako fale — Dev verifikuje u predusvarbi i raise-uje TEA blocker ako nedostaju).
  - [ ] Subtask 10.5: TEA kreira `apps/products/tests/test_placeholder.py` (C8 + AC2.6 + I-iter2-4 fix): **4 tests**
    - `test_placeholder_returns_http_200_with_template` — `GET /sr/proizvod/test-slug/` vraća HTTP 200 + `assertTemplateUsed(response, 'products/_placeholder.html')`; spečuje regression NoReverseMatch ako brand listing kartica linkuje
    - `test_placeholder_has_noindex_meta_tag` — response.content sadrži `<meta name="robots" content="noindex, nofollow">` (parser kroz `BeautifulSoup` ili regex assertion); KRITIČAN SEO guard pre Story 2.7
    - `test_placeholder_has_single_h1` — response.content sadrži TAČNO 1 `<h1>` element sa tekstom "Stranica još nije dostupna" (i18n marker prisutan)
    - `test_placeholder_uses_semantic_main_landmark` — response.content sadrži `<main role="main">` wrapper (a11y landmark assertion)
  - [ ] Subtask 10.6: TEA kreira `tests/test_brand_listing_static_assets.py` (mirror Story 2.5 file-existence pattern) — **AC8: 4 tests** — test_all_strings_translatable_no_hardcoded_serbian; test_no_aria_live_oob_for_static_page (AC8 spec — N/A za listing strana); test_bootstrap_icons_not_loaded_in_base_html (C7 fix verification — grep base.html za "bootstrap-icons" ili "bi bi-" → NE postoji); test_semantic_html5_structure_main_section_landmarks
  - [ ] Subtask 10.7: TEA dokumentuje **AC9 manuelni smoke check** kao SINGLE manual checklist item u retrospective (NE automated test): "Dev manualno verifikuje Lighthouse a11y ≥ 95 + `prefers-reduced-motion` Chrome DevTools test"
  - [ ] Subtask 10.8: TEA verifikuje testovi padaju u RED phase (`uv run pytest apps/brands/tests/ apps/products/tests/` ima fail-ove zbog missing views/templates)
  - [ ] Subtask 10.9: TEA commit-uje test fajlove PRE Dev GREEN phase (`test(brands): Story 2.6 RED-phase tests — brand listing views + templates + static assets + products placeholder`)

## Dev Notes

### Postojeća `apps/brands/` struktura (snimak pre Edit-a — regression guard)

Pre Story 2.6, `apps/brands/` direktorijum sadrži (live verifikovano 2026-05-30):

```
apps/brands/
├── __init__.py          (prazan)
├── admin.py              (stub register-i za Brand/Series/Category/Subcategory — Story 2.1)
├── apps.py               (BrandsConfig — Story 2.1)
├── migrations/
│   ├── __init__.py
│   └── 0001_initial.py   (Story 2.1)
├── models.py             (Brand, Series, Category, Subcategory — Story 2.1; 17 KB)
├── tests/
│   └── (test fajlovi iz Story 2.1)
└── translation.py        (TranslationOptions za 4 modela — Story 2.1)
```

**Story 2.6 dodaje (DELTA — `apps/brands/`):**
- `apps/brands/views.py` (NOVO — `BrandDetailView` sa Case/When section_rank + section_label annotacijama i get_template_names override za coming-soon)
- `apps/brands/urls.py` (NOVO — namespace `brands`, pattern `traktori/<slug:slug>/`, URL name `detail`)

**Story 2.6 dodaje (DELTA — `apps/products/`, C8 fix):**
- `apps/products/views.py` (NOVO — `product_detail_placeholder(request, slug)` FBV; renderuje HTTP 200 sa minimal "uskoro" template-om; Story 2.7 zameni sa pravim `ProductDetailView`)
- `apps/products/urls.py` (NOVO — namespace `products`, pattern `proizvod/<slug:slug>/`, URL name `detail`; matches `Product.get_absolute_url()`)
- `templates/products/_placeholder.html` (NOVO — minimal placeholder template)

Razlog C8 stub: `Product.get_absolute_url()` u Story 2.2 koristi `reverse("products:detail", ...)` koji raise-uje `NoReverseMatch` ako URL pattern ne postoji. Story 2.6 grid kartica i extended row linkuju ka product detail; bez placeholder URL-a, render strane bi crashovao. Stub je minimal (1 view + 1 URL + 1 template); refaktor Story 2.7 je trivijalan (replace view + drop placeholder template).

**Story 2.6 NE menja:**
- `apps/brands/models.py` (regression guard za Story 2.1 testove)
- `apps/brands/admin.py` (Story 8.4 scope)
- `apps/brands/translation.py`
- `apps/brands/migrations/` (NEMA novih migracija u 2.6)
- `apps/brands/apps.py`
- `apps/products/models.py` (regression guard za Story 2.2 testove)
- `apps/products/admin.py`, `apps/products/translation.py`, `apps/products/migrations/`

### `config/urls.py` Edit DELTA

Postojeći `config/urls.py` (live snapshot 2026-05-30):

```python
urlpatterns = [
    path("i18n/setlang/", set_language, name="set_language"),
]

urlpatterns += i18n_patterns(
    path("admin/", admin.site.urls),
    path("", include("apps.core.urls")),
    prefix_default_language=True,
)
```

**Story 2.6 dodaje DVE linije u `i18n_patterns(...)` blok PRE `apps.core.urls` include-a (C8 fix — products URLs su uključene jer Story 2.6 uvodi placeholder views za `products:detail` URL name):**

```python
urlpatterns += i18n_patterns(
    path("admin/", admin.site.urls),
    path("", include("apps.brands.urls")),    # NOVO Story 2.6 — /sr/traktori/<slug>/
    path("", include("apps.products.urls")),  # NOVO Story 2.6 — /sr/proizvod/<slug>/ (placeholder; Story 2.7 zameni)
    path("", include("apps.core.urls")),
    prefix_default_language=True,
)
```

**Razlog pozicioniranja PRE `apps.core.urls`:** Django URL resolver matchuje top-to-bottom; ako `apps.core.urls` ima catch-all root pattern (npr. `path("", home_view, name="home")`), placiranje brands i products prvo osigurava da `/traktori/...` i `/proizvod/...` matchuju brand/product view, ne home. Trenutno `apps.core.urls` ima samo home root path (Story 1.4 deliverable), pa nema risk-a; ali konvencija je: specifičniji prvi.

### `static/css/main.css` Edit DELTA

Story 1.7 + 1.8 + 2.5 je registrovalo niz `@import url('./components/...');` linija. Sintaksa je STROGO `url(...)` wrapper sa leading `./` (NE bare-string `@import './components/...';`).

Story 2.6 dodaje 3 nove linije na kraj postojećih @import linija (mirror 2.5 pattern):

```css
/* postojece linije ostaju netaknute */
@import url('./components/lightbox.css');         /* Story 2.5 */
@import url('./components/brand-listing.css');    /* NOVO Story 2.6 */
@import url('./components/statistic-medallion.css'); /* NOVO Story 2.6 */
@import url('./components/testimonials-slider.css'); /* NOVO Story 2.6 */
```

### `templates/base.html` Edit DELTA

Trenutni base.html (Story 2.5 deliverable; live snapshot 2026-05-30) ima script tagove ovog redosleda:

```html
<script src="{% static 'vendor/htmx.min.js' %}" defer></script>
{% bootstrap_javascript %}
<script src="{% static 'js/sticky-nav.js' %}" defer></script>
<script src="{% static 'vendor/glightbox/glightbox.min.js' %}" defer></script>
<script src="{% static 'js/lightbox-init.js' %}" defer></script>
{# Per-page scripts POSLE site-wide — sync init safe za Bootstrap komponente #}
{% block scripts %}{% endblock %}
```

**Story 2.6 dodaje 2 nova script tag-a POSLE `lightbox-init.js` i PRE Django komentara:**

```html
<script src="{% static 'js/lightbox-init.js' %}" defer></script>
<script src="{% static 'js/statistic-counter.js' %}" defer></script>      <!-- NOVO Story 2.6 -->
<script src="{% static 'js/testimonials-slider.js' %}" defer></script>    <!-- NOVO Story 2.6 -->
{# Per-page scripts POSLE site-wide — sync init safe za Bootstrap komponente #}
```

**Razlog za site-wide tag-ovi (NE per-page block scripts):**
- Statistic counter će biti reuse-ovan na Home strani (Story 3.1) i potencijalno O nama strani (3.2); dosadno bi bilo per-page include
- Testimonials slider će biti reuse-ovan na Home strani (Story 3.1), Product Detail strani (Story 2.7 — "Iz prve ruke" slider), Tractor Listing (2.8), itd.
- Defensive guard u JS module-ima bail-uje silently ako selektori ne postoje na strani → no performance overhead

### Relevantni Modeli (iz Story 2.1, 2.2)

**Brand** (apps/brands/models.py, Story 2.1):
- `slug` (SlugField, unique, max_length=140)
- `name` (CharField, translatable)
- `logo` (ImageField, optional)
- `hero_image` (ImageField, optional)
- `description` (TextField, translatable)
- `slogan` (CharField max 200, translatable)
- `statistics` (JSONField, lista do 4 dict-a `[{"icon": ..., "value": ..., "label": ...}]`)
- `catalog_pdf` (FileField, optional)
- `brand_color` (CharField, hex #RRGGBB, optional)
- `is_coming_soon` (BooleanField, default False)
- `get_absolute_url()` → `reverse("brands:detail", kwargs={"slug": self.slug})`
- related_name `products` (Product.brand FK), `series` (Series.brand FK)

**Series** (apps/brands/models.py, Story 2.1):
- `slug` (SlugField, per-brand unique)
- `name` (CharField, translatable)
- `description` (TextField, translatable)
- `layout_mode` (TextChoices: `LayoutMode.GRID = "grid"` | `LayoutMode.EXTENDED = "extended"`, default GRID)
- `display_order` (PositiveSmallIntegerField, default 0)
- `brand` (FK Brand, PROTECT, related_name="series")
- related_name `products` (Product.series FK)

**Product** (apps/products/models.py, Story 2.2):
- `slug` (SlugField, globally unique, kroz SluggedModel mixin)
- `name` (CharField, translatable)
- `description` (TextField, translatable)
- `main_image` (ImageField, optional)
- `horse_power` (PositiveSmallIntegerField, optional)
- `is_published` (BooleanField, default False)
- `brand` (FK Brand, PROTECT, related_name="products")
- `series` (FK Series, PROTECT nullable, related_name="products")
- `subcategory` (FK Subcategory, PROTECT nullable, related_name="products")
- related_name `specifications` (ProductSpecification.product FK)
- related_name `testimonials` (ProductTestimonial.product FK)
- `get_absolute_url()` → `reverse("products:detail", kwargs={"slug": self.slug})` (URL ne postoji do Story 2.7)

**ProductSpecification** (apps/products/models.py, Story 2.2):
- `section` (TextChoices: `SpecSection.MOTOR = "motor"` | `TRANSMISIJA = "transmisija"` | `HIDRAULIKA = "hidraulika"` | `OSTALO = "ostalo"`)
- `key` (CharField, translatable)
- `value` (CharField, translatable)
- `order` (PositiveSmallIntegerField, default 0)
- `product` (FK Product, CASCADE, related_name="specifications")

**ProductTestimonial** (apps/products/models.py, Story 2.2; **C4 fix — live verifikovano `apps/products/models.py:464-499`**):
- `product` (FK Product, CASCADE, related_name="testimonials")
- `photo` (ImageField, opciono, upload_to="products/testimonials/")
- `quote` (TextField, required, max 50000 char hard cap)
- `author_name` (CharField, max_length=120, required)
- `location` (CharField, max_length=120, opciono — **NEMA `author_role` polja**)
- `order` (PositiveSmallIntegerField, default 0, db_index=True)
- `created_at` (inherited iz TimestampedModel)
- Meta.ordering = ["order", "id"] (Story 2.2 konvencija)
- Story 2.6 BrandDetailView fetch-uje testimonijale sa `.order_by("order", "-created_at")[:10]` — honoring `order` polje sa recency tie-breaker; limit 10 latest.

### URL pattern (i18n_patterns)

`config/urls.py` koristi `i18n_patterns(...)` (Story 1.4); brand listing URL će biti:
- `sr` locale: `/sr/traktori/agri-tracking/`
- `hu` locale: `/hu/traktori/agri-tracking/`
- `en` locale: `/en/traktori/agri-tracking/`

**NAPOMENA:** "traktori" kao URL segment je trenutno **hardcoded srpski**. Multi-locale URL slug variant (npr. `/hu/traktorok/agri-tracking/`) je Story 6.6 scope (`apps.seo` locale-aware slug-ovi); v1 koristi srpski URL slug-ove na svim locale-ima — funkcionalno radi, SEO refinement kasnije.

### Slika lazy loading strategy

Sve slike unutar listing strane (grid kartice, extended row image, testimonijal photos) koriste:
- `{% responsive_picture image alt="..." loading="lazy" sizes="..." %}` (Story 2.3 deliverable)
- `loading="lazy"` atribut je native browser hint; modern browseri (Chrome, Firefox, Safari) podržavaju
- Hero brand logo NIJE lazy (above-the-fold; eager load za LCP)
- Statistike sekcija nema slike (samo value + label u v1; SM-D18 defer Bootstrap Icons) — no lazy concerns

### Brand logo `format='PNG'` policy (Story 2.3 MP-D5 contract — I-iter2-7 fix)

Story 2.3 Decision MP-D5 nalaže: **sve slike koje koriste `{% responsive_picture %}` i imaju transparency MORAJU prosediti `format='PNG'` kwarg** (default JPEG flattens transparency na bele pozadine, što je vizuelni regression za brand logo koji se renderuje na šarenoj pozadini hero kartice).

**Story 2.6 mesta gde se brand.logo / brand icons renderuju kroz `{% responsive_picture %}`:**

1. **`brand_coming_soon.html` (AC2.5, linija 270 u story specu):** ✅ FIXED — `format='PNG'` dodato.
2. **`_hero_section.html` (AC3 § Hero overlay, Subtask 3.3):** Hero card include-uje Story 1.7 `partials/hero_overlay_card.html` koji prima `brand_logo=brand.logo.url` (raw URL, NE `{% responsive_picture %}` poziv). Story 1.7 partial je responsibility-no za render-ovanje — Story 2.6 NE renderuje brand.logo kroz responsive_picture u hero. **NIJE potreban `format='PNG'` u Story 2.6 hero markup-u** (delegated u Story 1.7 partial; ako je Story 1.7 partial responsible za transparency preservation, to je 1.7 scope — Dev verifikuje da hero overlay card čuva transparency. Ako ne, escalate kroz Step-04 review.)
3. **`_statistics_medallions.html` (AC6):** Medaljoni renderuju samo `value` + `label`, **BEZ brand.logo i bez ikona** (per SM-D18 defer C7 fix). Nije primenjivo.
4. **`_series_grid.html` (AC4):** Renderuje `product.main_image` (NE `brand.logo`) — `{% responsive_picture product.main_image alt=product.name sizes="..." loading="lazy" %}`. Product slike su tipično JPEG fotografije bez transparency; `format='PNG'` se NE primenjuje. Ako Editor upload-uje product slike sa transparency-em i to mora biti preserved, Story 9-10 polish može override-ovati per product (out-of-scope za 2.6).
5. **`_series_extended.html` (AC5):** Renderuje `product.main_image` slično kao Grid. Isto pravilo — JPEG default, no `format='PNG'`.
6. **`_testimonials_slider.html` (AC7):** Renderuje `t.photo` (ProductTestimonial.photo) — fotografije korisnika, JPEG default, no `format='PNG'`.

**Pravilo za Story 2.6 Dev:** Ako pišeš `{% responsive_picture brand.logo ... %}` u bilo kom Story 2.6 template-u, MORA imati `format='PNG'`. Ako pišeš `{% responsive_picture product.main_image ... %}` ili `{% responsive_picture t.photo ... %}`, NE dodavaj `format='PNG'` (JPEG default). Story 2.3 MP-D5 je load-bearing decision; commit će biti reject-ovan u Step-04 ako brand.logo render nema `format='PNG'`.

### `prefers-reduced-motion` respect (UX-DR-13 + NFR-2 + a11y must-have)

**3 mesta gde prefers-reduced-motion mora biti respektovan u Story 2.6:**

1. **Statistic counter** (`static/js/statistic-counter.js`): ako `prefersReducedMotion === true`, instant set `el.textContent = target.toString()` bez requestAnimationFrame loop-a
2. **Testimonials slider** (`static/js/testimonials-slider.js`): ako `prefersReducedMotion === true`, **NEMA** auto-advance (samo manual prev/next radi)
3. **CSS akordion `<details>` transitions** (`brand-listing.css`): `@media (prefers-reduced-motion: reduce) { .coric-product-row__accordion { transition: none !important; } }`

**Test plan:** Dev manuelni smoke (AC9 § prefers-reduced-motion test); automated test bi koristio Playwright `page.emulateMedia({reducedMotion: 'reduce'})` (Story 9.8 scope).

### Decision Log (SM-D*)

- **SM-D1:** No HTMX swap u 2.6. Interaktivni filteri (range slider snage, range slider cene) su Story 2.8 scope. Story 2.6 je čista listing strana sa server-side rendering. Rationale: izolovati 2.6 cilj (kanonska brand listing layout) od HTMX filter complexity-ja koji ima sopstvene a11y i URL state management challenge-e (Story 2.8 aria-live OOB + query param sync).
- **SM-D2:** Reuse `templates/partials/hero_overlay_card.html` (Story 1.7 deliverable) umesto pisanja novog hero markup-a. Wrapper partial `_hero_section.html` prosleđuje brand-specifične vrednosti u generic hero card.
- **SM-D3:** Query strategy = `Prefetch(series, queryset=...) + Prefetch(products, queryset=published_with_specs) + select_related per Brand`. Daje 3-4 SQL upita za render strane. Alternativa (raw SQL ili Django's `prefetch_related` bez Prefetch objekta) ne pozvoljava filter `is_published=True` na nested products — Prefetch objekat sa custom queryset-om je kanonsko Django rešenje.
- **SM-D4:** Coming-soon brand renderuje minimal template (NE 404). Rationale: link sa Home strane sa pill-badge "Uskoro" mora otići negde sa contextom; 404 bi bio loš UX. Minimal template ima brand logo + naziv + "Uskoro" badge + nazad CTA.
- **SM-D5:** URL name = `"detail"` + URL kwarg = `"slug"` (Django `DetailView` default `slug_url_kwarg = "slug"` + `slug_field = "slug"`). Matches `Brand.get_absolute_url()` iz Story 2.1 koji koristi `reverse("brands:detail", kwargs={"slug": self.slug})` (live verifikovano `apps/brands/models.py:158`). Bolje da urls.py prilagodi naming-u modela nego obrnuto (model je single source of truth za get_absolute_url + sitemap + share linkovi). **NIKAKAV edit na `apps/brands/models.py` nije potreban** — C1 fix eliminiše ranije confusing prose o "brand_slug" kwarg alternativi koje je proizvodilo NoReverseMatch.
- **SM-D6:** Explicit empty state za brand bez serija (`Modeli ovog brenda su u pripremi.`) umesto sakrivene sekcije. UX je bolji — Marko zna da nije baga u UI, sadržaj je u pripremi.
- **SM-D7:** 3 odvojena CSS komponentna fajla (`brand-listing.css`, `statistic-medallion.css`, `testimonials-slider.css`) umesto jednog monolithic `brand-detail.css`. Rationale: statistic-medallion i testimonials-slider će biti reuse-ovani na drugim stranama (Home, Product Detail); razdvajanje komponenata sad olakšava reuse kasnije bez side-effect-a.
- **SM-D8:** Product `get_absolute_url()` u Grid kartici linkovima radi runtime kroz **placeholder products view + URL pattern dodat u Story 2.6** (C8 fix). Kreira se `apps/products/urls.py` sa `app_name = "products"` + `path("proizvod/<slug:slug>/", views.product_detail_placeholder, name="detail")`, plus minimalan `apps/products/views.py` FBV koji vraća HTTP 200 sa `templates/products/_placeholder.html` ("Stranica još nije dostupna — uskoro"). Story 2.7 zatim zameni `product_detail_placeholder` sa pravim `ProductDetailView` (CBV). Prethodna varijanta (samo `@pytest.mark.skip` pattern u testovima) je odbačena jer template render na runtime krši **page MUST NOT 500** principijel — koristnik koji klikne karticu mora dobiti nešto, ne NoReverseMatch traceback. Placeholder stub je minimalan (1 view + 1 URL + 1 template), refaktor Story 2.7 je trivijalan (replace view + drop placeholder template).
- **SM-D9:** Grid kartica nije reuse-ovana iz dedicated partial-a (npr. `_product_card.html`) — markup je inline u `_series_grid.html`. Story 3.1 (Home) i Story 2.8/2.9 (Tractor/Used Listing) će ekstrahovati `_product_card.html` kao zasebnu partial kada bude jasno da su isti card pattern. Sad je premature abstraction (YAGNI per project-context.md).
- **SM-D10:** Hero card prima EMPTY `bullets=[]` u v1. Original UX spec sa epics.md ne specificira bullets za brand listing hero (bullets su za product detail hero). Brand hero ima samo title + watermark.
- **SM-D11:** `brand.brand_color → repeating_element variant` mapping je explicit `{% if %}` u `_hero_section.html`: ako `brand.brand_color == "#00A4E9"` → `"blue"`, else `"green"`. Yagni za custom Django template filter dok brendova bude > 2.
- **SM-D12:** CSS Grid (`grid-template-columns: repeat(2, 1fr)`) u `brand-listing.css` umesto Bootstrap `.row` + `.col-md-6` za Grid layout. Rationale: zadržava sve grid spacing tokene unutar naših CSS Custom Properties; Bootstrap grid bi unosao Bootstrap-specifične token-e (margin negative, gutter etc.) koji ne matchuju DESIGN.md.
- **SM-D13:** SVE grid kartice imaju `loading="lazy"` (čak prva kartica prve serije). Rationale: brand listing strana ima hero + statistike + testimonijali iznad serija sekcije; nijedna kartica nije above-the-fold. Ako kasnije UX testing pokaže LCP problem, prva kartica može dobiti `loading="eager"` (refaktor je trivijalan).
- **SM-D14 (REVIDIRANO — C3 + C9 fix):** ProductSpecification ordering u extended layout akordion-u koristi **view-layer Case/When annotation** za `section_rank` (Motor=1 → Transmisija=2 → Hidraulika=3 → Ostalo=4) plus `section_label` annotation sa `gettext_lazy` za translated grouper labels (vidi AC2 `get_queryset()` `section_order` i `section_label` lokalne definicije; per-request instanciranje uvedeno u SM-D20). Prethodna verzija ove decision (oslanjanje na `Meta.ordering` + admin convention) BIO NEISPRAVAN — Story 2.2 NOTE I3 svesno NE uključuje `section` u Meta.ordering jer bi alphabetical sort dao `hidraulika→motor→ostalo→transmisija` što je SUPROTNO od traženog display order-a. Case/When annotation je kanonski Django pattern; ovaj pristup je bio plan za Story 2.7 (per Story 2.2 NOTE I3) ali se implementira jedna story ranije jer je akordion deo brand listing strane.
- **SM-D15:** Brand detail wrapper koristi Bootstrap `.container` class (no custom max-width token). Reuse-uje Bootstrap container responsive breakpoints; ne stvara novi token.
- **SM-D16 (NOVO — C2 fix):** Cross-boundary import izuzetak: `apps/brands/views.py` može importovati `Product`, `ProductSpecification`, `ProductTestimonial` iz `apps/products/models` jer BrandDetailView fundamentalno agregira "produkte grupisane po brendu" — coupling je intrinzičan domain semantici brand-listing strane (URL je `/traktori/<brand-slug>/`, ne `/proizvod/<brand-slug>/`). Ovaj izuzetak je **view-layer-only** (read-only query layer, no model dependency, no FK iz brand → product, no .save()/.create() na Product iz brands view-a) i NE krši arhitektonsku invariantu jednosmerne zavisnosti `products → brands`. Rationale za odbacivanje alternative "premestiti view u apps/products": URL semantika i namespace pripadaju brands (`/traktori/<brand-slug>/`); refactor bi promenio URL strukturu i create churn u sitemap-u i SEO. Story 2-6 dodaje EDIT operaciju na `_bmad-output/project-context.md` § Cross-boundary import sekciju koja eksplicitno dokumentuje ovaj izuzetak za buduće reviewer-e.
- **SM-D17 (NOVO — I4 fix):** Story 2.6 explicitno handluje SAMO brendove gde svi published proizvodi imaju `series` FK postavljen (Coric tractor brendovi — Agri-Tracking, John Deere, etc.). Brendovi sa nullable `Product.series` (Jeegee priključke, HZM radne mašine, Tulip MIX — per PR-D2 iz Story 2.2) imaju **zasebni listing pattern** (flat product grid bez series grupisanja) koji se uvodi u Story 2.10/2.11/2.12. Razlog: series-bazirani layout (Grid 2-col vs Extended 1-row sa akordion-om) je tractor-specific spec; mehanizacija brendovi imaju subcategory-based grouping (different UX pattern). Story 2.6 view ne fetch-uje `series__isnull=True` produkte — sav `BrandDetailView.queryset` logic pretpostavlja series-bound products. Ako Coric admin slučajno doda Jeegee/HZM/Tulip brand i poseti URL `/traktori/<jeegee-slug>/`, sekcija serija će biti prazna i empty state poruka "Modeli ovog brenda su u pripremi." će se prikazati — defensive, ne crash. Pravilan listing pattern za te brendove je Story 2.10/2.11/2.12 deliverable.
- **SM-D18 (NOVO — C7 fix):** Bootstrap Icons font NIJE wired u v1 base.html (live verifikovano 2026-05-30: `static/vendor/` sadrži `bootstrap-5.3.3`, `glightbox`, `htmx.min.js` — NEMA `bootstrap-icons` direktorijuma; `base.html` ne učitava bootstrap-icons CSS). Tri opcije razmotrene za statistic medallion ikone: (a) vendor Bootstrap Icons CSS + font files (~230KB total), (b) inline SVG mapping sa Brand admin field za SVG slug, (c) defer ikona to Story 9-10 (Polish). **Bira se opcija (c)** — Story 2.6 medaljoni renderuju samo `value` + `label` (minimalist, accessible — value sam po sebi prenosi statistiku; label clarify-uje kontekst). Bootstrap Icons wiring + `Brand.statistics.icon` field render-ing je Story 9-10 polish scope. Rationale: scope tightness — Story 2.6 deliverable focus je listing layout (Grid/Extended branching + akordion + slider), ne icon font integracija; defer ne blokira FR-37 osnovnu funkcionalnost; admin v1 može i dalje upisivati `icon` ključ u JSON (Story 2.1 soft validation dopušta arbitrary dict keys), tek render se uključuje u 9-10.
- **SM-D19 (NOVO — I11 fix):** `BrandDetailView` koristi **`get_template_names()` override** umesto monolithic `get()` override za coming-soon branching. Prethodna varijanta (`get()` override koji ručno renderuje `brands/brand_coming_soon.html` kroz `render(request, ...)` poziv) BIO JE non-CBV-idiomatic — bypass-ovao je `self.get_context_data()` hook i čino mixin composition (npr. budući `LoginRequiredMixin`, `AccessLogMixin`) nemoguć bez code duplicate-a. Novi pattern: `get()` postavi `self.object` i pozove `get_context_data` + `render_to_response`; `get_template_names()` se konsultuje unutar `render_to_response` i vraća `["brands/brand_coming_soon.html"]` ako `self.object.is_coming_soon`, else `["brands/brand_detail.html"]`. `get_context_data` skipuje `testimonials` fetch kad je coming-soon (early return). Pattern je composable, preserve-uje DetailView semantike, i čista je single-responsibility distribucija.
- **SM-D20 (NOVO — I-iter2-1 fix; locale-aware Case/When pattern):** `section_order` i `section_label` Case/When ekspresije SE INSTANCIRAJU UNUTAR `BrandDetailView.get_queryset()` (lokalne varijable u method body-ju), NE na module-level. Razlog: `Value(gettext_lazy(...))` evaluacioni model — `gettext_lazy` proxy preserve-uje lazy evaluation, ali `Value()` wrap-er + `Case()`/`When()` objekti su konstruisani EAGER pri Python ekspresijskoj evaluaciji. Ako se ekspresije postave na module-level, one se construct-uju TAČNO JEDNOM pri import-u modula; iako `gettext_lazy` proxy unutar `Value` "treba" da re-evaluuje, Django ORM-ov compile path za `Case/When` može cache-ovati internal SQL representation pri prvom `.annotate()` pozivu i SQL bind-ovati vrednost u tom prvom request-ovom kontekstu. Bezbedan pattern: konstruisati Case/When per-request unutar `get_queryset()` jer `LocaleMiddleware` (Story 1.4) postavlja `translation.activate(request.LANGUAGE_CODE)` PRE `get()` poziva. **Verifikacija u testovima (vidi Subtask 10.4):** `test_extended_layout_section_labels_hu` renderuje `brand_detail.html` pod `LANGUAGE_CODE='hu'` i asertuje da `<details><summary>` elementi sadrže hu-locale prevode (npr. "Hajtómű" za "Transmisija" prema `locale/hu/LC_MESSAGES/django.po`). Test garantuje da prvi request u sr lokali ne "zamrzne" labels za buduće hu request-e. **Posledica za buduće CBV-ove sa `gettext_lazy` u Case/When:** UVEK definisati ovakve ekspresije unutar instance method-a (get_queryset/get_context_data) ili u helper method-u koji se zove per-request, NIKAD kao module-level konstante.
- **SM-D21 (NOVO — I-iter2-4 fix; placeholder template CSS scope):** `templates/products/_placeholder.html` BEM klasi (`coric-product-placeholder`, `coric-product-placeholder__title`, `coric-product-placeholder__message`) se dodaju u **`static/css/components/brand-listing.css`** umesto u zasebni `static/css/components/product-placeholder.css`. Razlog: placeholder template je minimalan (h1 + p + CTA) i koristi se SAMO dok Story 2.7 ne uvede pravu `ProductDetailView` (placeholder template se drop-uje); zasebni CSS fajl bi bio scope-creep za 3 klase koje će živeti < 2 stories. Trade-off: `brand-listing.css` više nije strogo "brand-listing only", ali je pragmatičan choice — alternativa (zaseban CSS fajl + main.css @import + 2-3 stories kasnije cleanup) je veći overhead. Cleanup u Story 2.7: kad se uvede prava `ProductDetailView`, ove 3 klase se sele u `static/css/components/product-detail.css` (Story 2.7 deliverable) i brišu iz brand-listing.css.
- **SM-D22 (NOVO — I-iter2-6 fix; catalog CTA renderuje direct anchor):** `templates/brands/partials/_catalog_cta.html` NE koristi `{% include "partials/pill_button.html" %}` partial — umesto toga renderuje direktan `<a>` tag sa `target="_blank"`, `rel="noopener noreferrer"`, `download`, i `class="coric-button coric-button--primary"` atributima. Razlog: Story 1.7 Pill Button partial signature (`templates/partials/pill_button.html`, verifikovano live) ne podržava prosleđivanje `target`, `rel`, ili `download` kwarg-a — partial renderuje `<a class="coric-button coric-button--{{ variant }}" href="{{ href }}">{{ label }}</a>` (plus `aria_label` i `extra_classes`), bez extension-tačaka za HTML atribute. Modifikacija Story 1.7 partial-a da prima dodatne kwarg-e je out-of-scope za Story 2.6 (potencijalno breaking change za sve postojeće konzumente partial-a — header CTA, footer link, hero CTA u Story 1.7+1.8). Direct anchor pattern je standardan Django/HTML approach za PDF download CTA-jeve sa target=_blank; vizuelni parity sa Pill Button-om se postiže reuse-om iste BEM klase (`coric-button coric-button--primary`) koja je definisana u `static/css/components/pill-button.css` (Story 1.7 deliverable; site-wide loaded kroz main.css). Trade-off: minimalna code duplication (2 atributa: class string), ali jasan separation od partial-ovog scope-a. Refaktor put: ako budu potrebne >= 2 CTA-ja sa target/download (npr. Story 5.x blog PDF attach), kreira se novi `templates/partials/download_button.html` partial sa eksplicitnim download semantics i sa `target` kwarg-om.

### Dependencies note (KRITIČNO za Dev)

Story 2-6 STROGO zavisi od ovih prethodnih story-ja (sve `done` per sprint-status.yaml):
- **Story 2-1:** Brand, Series, Category, Subcategory modeli sa `layout_mode` TextChoices na Series — Story 2-6 koristi `series.layout_mode == "grid"` branching
- **Story 2-2:** Product i related modeli — Story 2-6 query-uje `Product.objects.filter(is_published=True)` + `ProductSpecification.section` TextChoices za extended akordion grouping
- **Story 2-3:** Image pipeline (`{% responsive_picture %}` template tag iz `media_pipeline.templatetags.media_tags`) — Story 2-6 koristi ovaj tag za sve slike sa `loading="lazy"`
- **Story 2-4:** PDF cover thumbnail generator — Story 2-6 "Preuzmi katalog" CTA banner koristi `brand.catalog_pdf.url` direct download; cover-thumbnail je Story 2-7 scope (Product brochure card), NE 2-6 (brand level CTA je direct download bez preview)
- **Story 2-5:** GLightbox base.html wiring — Story 2-6 NE renderuje galleries direktno (galleries dolaze u Story 2-7 Product Detail), ali base.html ima lightbox-init.js učitan globalno; testimonials slider RESPECTS `coric:lightbox-open` event (pause auto-advance dok je modal otvoren) per Story 2-5 kontrakt

Sve prethodne story-je su `done` u sprint-status.yaml (verifikovano 2026-05-30); Story 2-6 je spremna za RED phase (TEA) → GREEN phase (Dev).

### Cross-boundary import izuzetak (C2 fix — load-bearing project-context.md EDIT)

Story 2.6 uvodi **explicit, dokumentovan izuzetak** od pravila "brands ne sme importovati products" iz `_bmad-output/project-context.md` linija 622. `BrandDetailView` mora importovati `Product`, `ProductSpecification`, `ProductTestimonial` jer view fundamentalno agregira "products grouped by brand" — coupling na Product je intrinzičan domain semantici. Story 2.6 EDIT operacija na `_bmad-output/project-context.md` § "🚫 Anti-pattern: Cross-boundary import" sekciju (linije 619-625) dodaje sledeću napomenu odmah nakon `brands ne sme importovati products` bullet-a:

```markdown
### 🚫 Anti-pattern: Cross-boundary import
App dependency rules (iz architecture.md):
- ❌ `core` ne sme importovati domain apps (products, brands, ...)
- ❌ `brands` ne sme importovati `products` (jednosmerna — `products → brands`)
  - **Exception** (Story 2.6+): `apps/brands/views.py` SME importovati `Product`,
    `ProductSpecification`, `ProductTestimonial` iz `apps.products.models`
    zato što `BrandDetailView` agregira products grupisane po brendu (read-only
    query layer, no model dependency, no FK iz brand → product, no .save()).
    Coupling je view-layer-only i ne krši arhitektonsku invariantu jednosmerne
    zavisnosti. Vidi Story 2.6 Decision SM-D16 za rationale.
- ❌ `forms` ne sme importovati `catalog` / `blog` direktno
- ❌ Domain apps ne smeju importovati iz `admin_ext`
```

Task 1.7 (vidi Tasks/Subtasks sekciju) eksplicitno enumerise ovaj EDIT.

### CTA reuse — Pill Button partial nije koriščen ni u `_series_grid.html` ni u `_catalog_cta.html` (I3 + I-iter2-6 razjašnjenje)

Story 1.7 deliverable `templates/partials/pill_button.html` render-uje `<a>` (default) ili `<button>` (as="button") element sa `coric-button` BEM klasama; partial signature prima `label`, `variant`, `href`, `as`, `type`, `aria_label`, `extra_classes` — **NEMA `target`, `rel`, `download` parametre**.

**Story 2.6 NIJEDAN site nije konzument Pill Button partial-a, sva 3 CTA mesta renderuju direct markup:**

1. **`_series_grid.html` (AC4 — OPŠIRNIJE CTA u grid kartici):** Inline `<span class="coric-button coric-button--primary coric-product-card__cta" aria-hidden="true">{% translate "OPŠIRNIJE" %}</span>`. Razlog: cela kartica je već wrapping `<a>` (linkable card pattern); Pill Button render-uje `<a>` što bi proizvelo **nested interactive elements** (a11y violation per HTML5 spec § "Interactive content cannot be nested"; WCAG 2.1 SC 4.1.2). Vizuelna konzistentnost kroz reuse `coric-button` BEM klase, element je `<span>` umesto `<a>`.

2. **`_series_extended.html` (AC5 — OPŠIRNIJE CTA u extended row-u):** Standalone `<a class="coric-button coric-button--primary" href="{{ product.get_absolute_url }}">{% translate "OPŠIRNIJE" %}</a>`. Razlog: akordion red NIJE wrapping link (specifikacije se otvaraju/zatvaraju in-place), pa standalone `<a>` je čist; ali template autor ne koristi pill_button partial zbog konzistentnosti sa ostalih 2 CTA mesta (svi 3 direct markup, lakše za grep/refactor).

3. **`_catalog_cta.html` (AC3 § PREUZMI katalog CTA banner — I-iter2-6 fix + SM-D22):** Direct `<a href="{{ brand.catalog_pdf.url }}" target="_blank" rel="noopener noreferrer" download class="coric-button coric-button--primary" data-testid="brand-catalog-download">{% translate "Preuzmi katalog" %}</a>`. **Razlog NE-pill_button:** PDF download CTA mora otvoriti u novom tabu (UX-DR i AC9 smoke check: "klik na 'PREUZMI' otvara PDF u novom tabu") + `rel="noopener noreferrer"` (security best practice za target=_blank) + `download` HTML5 attribute (sugeriše browser-u da download umesto inline render — quality of life za korisnike sa PDF viewer extensions). Story 1.7 partial NEMA prosleđivanje za nijedan od ova 3 atributa; modifikacija partial-a je out-of-scope za Story 2.6 (potencijalno breaking change za sve postojeće konzumente — header CTA, footer link, hero CTA u Story 1.7/1.8/2.5).

**Refaktor put:** Ako budu potrebne >= 2 CTA-ja sa target/download (npr. Story 5.x blog PDF attach, Story 4.x service download brochures), kreira se novi `templates/partials/download_button.html` partial sa eksplicitnim download semantics, target i rel kwargs. Story 2.6 ne uvodi taj partial — yagni za 1 use-case.

### Open questions / warnings za Validation (Step 2)

1. **Lighthouse Performance score lower target (≥ 75 vs ideal ≥ 90)** — image pipeline u 2.3 koristi JPEG (no WebP/AVIF) i 2.6 nije optimizovala dalje. Story 9.10 Polish pass dovešće Performance score na ≥ 90.
2. **Multi-locale URL slug-ovi** — URL segment "traktori" je hardcoded srpski; multi-locale URL aliasing (npr. `/hu/traktorok/...`) je Story 6.6 scope. V1 funkcionalno radi sa svim locale-ima ali SEO refinement kasnije.
3. **`coric-product-card` reuse u Story 2-8/2-9** — Story 2-6 uvodi karticu inline u `_series_grid.html`. Story 2-8 (HTMX filter swap) će potencijalno trebati ekstrahovati u dedicated `_product_card.html` partial za HTMX `{% include %}` reuse. Trenutno yagni; Story 2-8 SM može refaktor u svom create-story koraku.
4. **Bootstrap Icons wiring deferred** — Statistic medallion ikone su deferred to Story 9-10 polish (vidi Decision SM-D18 + C7 fix). Admin v1 može upisivati `icon` ključ u `Brand.statistics` JSON ali template ga ignoriše; Story 9-10 PR će dodati conditional render.

**Resolved during SM Fix iteration 1/5 (vidi commit log za detalje):**
- ~~TBD-PRE-DEV: ProductTestimonial polja~~ → C4 fix: polja verifikovana live `apps/products/models.py:464-499`; `t.author_role` zamenjen sa `t.location` u AC7 template snippet.
- ~~ProductSpecification.section display order~~ → C3 fix: view-layer Case/When `section_rank` annotation uvedena u AC2 (umesto admin convention).
- ~~`is_coming_soon` minimal template spec~~ → C6 fix: AC2.5 dodat sa kompletnim markup spec-om.

**Resolved during SM Fix iteration 2/5 (vidi commit log za detalje):**
- ~~I-iter2-1 (Adversarial high): module-level `_SECTION_LABEL` može freeze-ovati locale~~ → SM-D20 fix: Case/When ekspresije premestene unutar `get_queryset()` per-request; dodat `test_extended_layout_section_labels_hu` u Subtask 10.4.
- ~~I-iter2-2 (B+Adversarial): coming-soon CSS klase ne nabrojane u AC8~~ → AC8 brand-listing.css spec proširen 7 selektora (`.coric-brand-coming-soon`, `__logo`, `__title`, `__message`, `.coric-pill-badge`, `--coming-soon`, base note); hedging prose o "TBD u Dev Notes" uklonjen iz AC2.5.
- ~~I-iter2-3 (B+Adversarial): Subtask 1.7 instrukcija zastarjela~~ → Subtask 1.7 prepisana kao VERIFY-ONLY; file delta table EDIT row za project-context.md anotiran sa "already applied during validation; verify only".
- ~~I-iter2-4 (Adversarial): `_placeholder.html` nema markup spec ni SEO noindex~~ → AC2.6 dodat sa kompletnim markup spec-om (uključujući `<meta name="robots" content="noindex, nofollow">`); Subtask 1.5 prepisana; Subtask 10.5 proširen sa 4 tests (status 200 + noindex + h1 + main landmark); SM-D21 dokumentuje CSS scope decision.
- ~~I-iter2-5 (B): File delta count math inconsistency (17 vs 19)~~ → intro line 55 i Brojanje sentence (linija 83) ažurirane na "19 NOVO + 4 EDIT" sa eksplicitnom računicom (4 .py + 1 products template + 2 brands main + 7 brands partials + 2 JS + 3 CSS = 19; 3 active + 1 verify-only = 4 EDIT).
- ~~I-iter2-6 (B): `pill_button.html` ne podržava `target`~~ → SM-D22 fix: `_catalog_cta.html` renderuje direct `<a>` markup (NE pill_button partial) sa `target="_blank"`, `rel="noopener noreferrer"`, `download`; AC3 § "Preuzmi katalog" CTA spec i Subtask 7.1 ažurirani; Dev Notes § "CTA reuse" sekcija prepisana da pokriva sva 3 mesta gde pill_button NIJE koriščen.
- ~~I-iter2-7 (B): `format='PNG'` fali na brand.logo u brand_coming_soon.html~~ → AC2.5 markup snippet (linija 270) dobio `format='PNG'` kwarg per Story 2.3 MP-D5; nova Dev Notes sekcija "Brand logo `format='PNG'` policy" enumeriše svih 6 potencijalnih render mesta sa per-site verifikacijom; hero (Subtask 3.3) koristi `brand.logo.url` (NE responsive_picture; delegated u Story 1.7 partial).
- ~~I-iter2-8 (A): AC9 Lighthouse nema artifact preservation~~ → AC9 § Lighthouse JSON artifact spec dodat sa CLI poziv-om (`lighthouse --output=json --output-path=_bmad-output/implementation-artifacts/2-6-lighthouse-YYYYMMDD.json`); Subtask 9.6 ažuriran; Dev mora citirati a11y/performance/seo skor-ove u Completion Notes PRE Step-04.

## Completion Notes (Dev — GREEN phase 2026-05-30)

**Status:** GREEN phase završen; status promenjen draft → review; sprint-status.yaml ažuriran in-progress → review.

### Test results
- **Total Story 2.6 tests: 38** (37 PASSED + 1 XFAILED — expected hu-locale xfail per Subtask 10.4 / SM-D20)
- Run pod `docker compose -f compose/local.yml exec django uv run pytest apps/brands/tests/test_views_brand_detail.py apps/brands/tests/test_templates_brand_listing.py apps/brands/tests/test_brand_coming_soon.py apps/products/tests/test_placeholder.py` → exit 0
- Full module regression: `apps/brands/tests/ + apps/products/tests/` = **173 passed, 2 skipped, 1 xfailed** (no regressions vs Story 2.1/2.2 baseline)

### Files created (19 NOVO)
- `apps/brands/views.py` — `BrandDetailView(DetailView)` sa Case/When section_rank + section_label (per-request konstruisano, SM-D20), get_template_names override za coming-soon (SM-D19)
- `apps/brands/urls.py` — app_name="brands", `traktori/<slug:slug>/`
- `apps/products/views.py` — `placeholder_view(request, slug)` FBV
- `apps/products/urls.py` — app_name="products", `proizvod/<slug:slug>/`
- `templates/products/_placeholder.html` — noindex + h1 + CTA
- `templates/brands/brand_detail.html` — root sa data-testid="brand-detail-page"
- `templates/brands/brand_coming_soon.html` — wrapper `<div>` (NE nested `<main>` per interface contract § 4)
- `templates/brands/partials/_hero_section.html`
- `templates/brands/partials/_statistics_medallions.html`
- `templates/brands/partials/_testimonials_slider.html`
- `templates/brands/partials/_series_section.html`
- `templates/brands/partials/_series_grid.html`
- `templates/brands/partials/_series_extended.html`
- `templates/brands/partials/_catalog_cta.html`
- `static/js/statistic-counter.js`
- `static/js/testimonials-slider.js`
- `static/css/components/brand-listing.css`
- `static/css/components/statistic-medallion.css`
- `static/css/components/testimonials-slider.css`

### Files modified (3 EDIT)
- `config/urls.py` — dodate brands.urls + products.urls u i18n_patterns PRE core.urls
- `static/css/main.css` — +3 `@import url('./components/...')` linije
- `templates/base.html` — +2 `<script defer>` tag-a posle lightbox-init.js

### Implementation choices worth noting
- **`str(_("Motor"))` u `Value()`:** Initial implementation sa `Value(_("Motor"))` raise-uje `psycopg.ProgrammingError: cannot adapt type '__proxy__'` jer psycopg ne zna kako da serijalizuje lazy gettext proxy. Workaround je `Value(str(_("Motor")))` koji forsira eager evaluation AT REQUEST TIME (per-request `get_queryset()` poziv garantuje da LocaleMiddleware-aktiviran jezik bude resolvan u trenutku Case/When konstrukcije). Per-request pattern (SM-D20) i dalje važi — samo eksplicitno koerciram lazy → str.
- **Hero section logo guard:** `brand.logo.url` raise-uje ValueError ako logo polje je prazno (ImageField bez fajla). Template koristi `{% if brand.logo %}...{% endif %}` da bezbedno predaje `brand.logo.url` u hero_overlay_card partial; ako logo nedostaje, prosleđujemo prazan string (`brand_logo=""`) i partial ne renderuje img tag (kroz `{% if brand_logo %}` guard u hero_overlay_card.html iz Story 1.7).
- **No new dependencies:** Sve testirano sa postojećim stack-om (Django 5.2, sorl-thumbnail, django-modeltranslation); NEMA factory_boy / NEMA Bootstrap Icons / NEMA novih vendor asset-a.
- **Migracije:** `manage.py makemigrations --dry-run` → "No changes detected" (potvrda da Story 2.6 NE menja modele).

### Test modifications
**Nijedna.** Sve TEA testove iz RED phase su zadovoljeni bez izmena.

### Unfixable issues
**Nijedna.**

### AC status
- **AC1** (URL routing): implemented — 5 testova prolaze (sr/hu/en locale + 404 + APPEND_SLASH)
- **AC2** (view + queries + context + coming-soon branching): implemented — 4 testova prolaze (context keys + assertNumQueries(5) + coming-soon path + 404)
- **AC2.5** (coming-soon template): implemented — 5 testova prolaze (template_used + single h1 + pill-badge + nazad-na-Home CTA + no nested main)
- **AC2.6** (placeholder template): implemented — 4 testova prolaze (200 + noindex meta + single h1 + semantic main)
- **AC3** (page structure): implemented — 2 testova prolaze (section order + ARIA landmarks)
- **AC4** (grid layout): implemented — 3 testova prolaze (markup + data-testid + aria-label)
- **AC5** (extended layout): implemented — 4 testova (3 PASSED + 1 XFAILED hu-locale per Subtask 10.4 SM-D20 plan; xfail očekivan dok hu prevodi ne budu populated u locale/hu/LC_MESSAGES/django.po)
- **AC6** (medallions): implemented — 3 testova prolaze (value+label no icon + slice cap 4 + section hidden when empty)
- **AC7** (testimonials slider): implemented — 4 testova prolaze (aria roles + pause aria-pressed + data-testid + hidden when empty)
- **AC8** (i18n + a11y): implemented — 4 testova prolaze (html lang + no bi icons + key translations present + semantic section landmarks)
- **AC9** (manual smoke + Lighthouse): **pending manual verification by Mihas** — automated tests cover all programmatic requirements; manual `prefers-reduced-motion` Chrome DevTools test, Lighthouse CLI run, and JSON artifact save (`_bmad-output/implementation-artifacts/2-6-lighthouse-YYYYMMDD.json`) remain. Lighthouse skorovi: TBD (manual run pending).

### Lint status
- `ruff check` na `apps/brands/views.py apps/brands/urls.py apps/products/views.py apps/products/urls.py` — **All checks passed** (postojeći ruff errors u test fajlovima su TEA scope)
- `ruff format` na fajlovima koje sam kreirao — clean (auto-formatted views.py kroz `ruff format`)
- `djade` na novim templates — clean (auto-formatted 3 fajla kroz djade)

### Story 2.7 cascade footnote (2026-05-30)
- Story 2.7 GREEN-phase refaktorisala `templates/brands/partials/_testimonials_slider.html` → `templates/partials/_testimonials_slider.html` (shared lokacija); partial dobio opcioni `slider_id` kwarg sa default `"testimonials-title"`. `brand_detail.html` linija 22 ažuriran da prosledi `slider_id="brand-testimonials-title"` kwarg, preserving postojeću `aria-labelledby` referencu (Story 2.6 testovi netaknuti). Per SM-D23/D27 — vidi `2-7-interface-contract.md § 4 templates/partials/_testimonials_slider.html`.

---

## Code Review Iteration 1 — Fixes (2026-05-30)

**Iteration:** 1/3 (Dev Fix Agent)
**Test results posle fix-eva:** 177 passed, 2 skipped, 1 xfailed (4 nova testa: T1/T2/T3/T4). Bez regresija.

### Issues fixed (12/12)

**SECURITY (1):**
- **S1** — `templates/brands/brand_coming_soon.html`: dodat `{% block extra_head %}<meta name="robots" content="noindex, nofollow">{% endblock %}` (parallel sa `_placeholder.html` AC2.6 fix; štiti pre-launch brend stranice od search-result pollution-a).

**BUG (3):**
- **B1** — `templates/brands/partials/_hero_section.html`: uklonjen duplikat `<h1 id="brand-hero-title">{{ brand.name }}</h1>` (hero_overlay_card.html partial već renderuje svoj `<h1>`); `brand_detail.html` ažuriran sa `aria-label` umesto `aria-labelledby="brand-hero-title"` da section landmark ima accessible name. Test `test_aria_landmarks_present` ažuriran sa regex match-em na `<section id="brand-hero" ... aria-label="...">`.
- **B2** — `_hero_section.html`: hex comparison `brand.brand_color == "#00A4E9"` zamenjen sa case-insensitive `brand.brand_color|lower == "#00a4e9"` (sklađen sa `tokens.css` lowercase `--color-jeegee-blue`).
- **B3** — `_series_grid.html` + `_series_extended.html`: uklonjen redundantni `{% if product.is_published %}` guard — Prefetch queryset već filtruje `is_published=True` (anti-pattern "No defensive validation on internal code").

**ARCHITECTURE (1):**
- **A1** — `_series_section.html`: per-series naslov promenjen iz `<h2>` u `<h3>` (parent section `brand_detail.html` ima `<h2 id="brand-series-title">` — heading hierarchy h2 → h3 sada ispravno).

**TEST_GAP (4):**
- **T1** — `test_brand_detail_renders_exactly_one_h1` u `test_templates_brand_listing.py`: asertuje TAČNO 1 `<h1>` u brand_detail render-u (paralelno coming-soon parnjaku).
- **T2** — `test_unpublished_products_excluded_from_brand_listing`: kreira published + unpublished produkt, verifikuje da unpublished ne dolazi u render kroz Prefetch filter.
- **T3** — `test_empty_series_shows_empty_state_message`: serija bez published produkata pokazuje `{% empty %}` poruku "Modeli ove serije su u pripremi.".
- **T4** — `test_coming_soon_renders_responsive_picture_when_brand_has_logo` u `test_brand_coming_soon.py`: brand sa logo upload-om renderuje `<picture>` element kroz responsive_picture template tag.

**REFACTOR (3):**
- **R1** — `_hero_section.html`: 4 nearly-identical `{% include %}` blokova collapse-ovani u 2 `{% with variant=... %}` blocka sa po 2 conditional `{% if brand.logo %}` include-a (4 → 2 include calls, jasniji intent).
- **R2** — `_catalog_cta.html`: uklonjen unstyled `<div class="coric-wave-divider-wrap coric-wave-divider-wrap--top">` wrapper — klasa nije imala CSS pravilo, dead markup. `{% include "partials/wave_divider.html" %}` ostaje bez wrapper-a.
- **R3** — pokriveno B2 (case-insensitive hex compare); nema zasebne akcije.

### Files modified (8)
- `templates/brands/brand_coming_soon.html` (S1)
- `templates/brands/brand_detail.html` (B1)
- `templates/brands/partials/_hero_section.html` (B1, B2, R1, R3)
- `templates/brands/partials/_series_grid.html` (B3)
- `templates/brands/partials/_series_extended.html` (B3)
- `templates/brands/partials/_series_section.html` (A1)
- `templates/brands/partials/_catalog_cta.html` (R2)
- `apps/brands/tests/test_templates_brand_listing.py` (B1 test update + T1 + T2 + T3)
- `apps/brands/tests/test_brand_coming_soon.py` (T4)

### Test modifications
- `apps/brands/tests/test_templates_brand_listing.py:119-124` — `test_aria_landmarks_present`: assertion `'aria-labelledby="brand-hero-title"' in html` → regex `<section[^>]*id="brand-hero"[^>]*aria-label="` jer je B1 fix uklonio `aria-labelledby` (više nema h1 sa tim id-jem).

### Unfixable issues
**Nijedna.** Svih 12 issue-a iz code review iter-1 uspešno rešeno.

### Lint status (iter-1 fixes)
- `ruff check` na `apps/brands/tests/test_templates_brand_listing.py` + `apps/brands/tests/test_brand_coming_soon.py` — postojeće 3 greške su TEA scope (F401/F841 u testovima iz RED phase-a) i ne potiču od fix-eva ove iteracije.
- `djade --check` na svim `templates/brands/*.html` + `templates/products/*.html` (10 fajlova) — **All formatted clean.**

