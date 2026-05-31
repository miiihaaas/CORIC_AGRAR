---
story_id: "2.12"
story-key: 2-12-hzm-radne-masine-tulip-mix-prikolice-strane
title: Interface Contract — HZM Radne Mašine + Tulip MIX Prikolice Strane
phase: RED (TEA — testovi PRE implementacije)
author: TEA (Test Architect)
date: 2026-05-31
status: contract-locked
---

# Story 2.12 — Interface Contract (RED phase)

Ovaj dokument je **UGOVOR** koji Dev (GREEN phase) mora zadovoljiti. TEA piše
testove protiv ovog kontrakta PRE implementacije; svi novi testovi MORAJU pasti
dok Dev ne isporuči views/templates/URLs/migraciju/CSS.

Kontrakt mirror-uje Story 2-10 (Jeegee) + 2-11 (Subcategory) precedent 1:1 gde god
je primenljivo. Sve user-facing strings su srpski latinica pune dijakritike; slugovi
ASCII.

---

## 1. URL pattern-i (`apps/brands/urls.py` — ADD 2 path POSLE postojećih)

| Name | Path (bez locale) | reverse (sr) | View |
|---|---|---|---|
| `brands:hzm_radne_masine` | `mehanizacija/radne-masine/` | `/sr/mehanizacija/radne-masine/` | `HzmRadneMasineView` |
| `brands:tulip_mix_prikolice` | `mehanizacija/mix-prikolice/` | `/sr/mehanizacija/mix-prikolice/` | `TulipMixPrikoliceView` |

```python
path("mehanizacija/radne-masine/", HzmRadneMasineView.as_view(), name="hzm_radne_masine"),
path("mehanizacija/mix-prikolice/", TulipMixPrikoliceView.as_view(), name="tulip_mix_prikolice"),
```

**Deconfliction (SM-D5):** oba su statički dvoslojni path-ovi bez slug konvertera;
`radne-masine`/`mix-prikolice` ≠ `prikljucna` ≠ `polovna`. NEMA kolizije sa Story
2-9/2-10/2-11. URL import lista u `urls.py` dobija `HzmRadneMasineView`,
`TulipMixPrikoliceView`.

**Regression guard:** `brands:jeegee_prikljucna` → `/sr/mehanizacija/prikljucna/`,
`brands:subcategory_listing_category` → `/sr/mehanizacija/prikljucna/<cat>/`,
`products:used_machinery_list` → `/sr/mehanizacija/polovna/`,
`products:tractor_list` → `/sr/traktori/`, `products:detail` → `/sr/proizvod/<slug>/`
ostaju NETAKNUTI.

---

## 2. View klase (`apps/brands/views.py` — ADD 2 klase + 3 konstante; UŽA izmena SubcategoryListView)

Module-level konstante (POSLE `_PRIKLJUCNA_CATEGORY_SLUGS`):
```python
_HZM_BRAND_SLUG = "hzm"
_HZM_CATEGORY_SLUG = "radne-masine"
_TULIP_BRAND_SLUG = "tulip"
```

### 2.1 `HzmRadneMasineView(DetailView)`
- `model = Brand`, `context_object_name = "brand"`.
- `get_object()` → `Brand.objects.get(slug="hzm")`; `Brand.DoesNotExist` → `Http404("HZM brand nije konfigurisan u sistemu.")`.
- `get_template_names()` → `["brands/brand_coming_soon.html"]` ako `is_coming_soon`, inače `["brands/hzm_radne_masine.html"]`.
- `get_context_data()` → ako `is_coming_soon` early-return (NE fetch subcategories).
  Inače fetch HZM `radne-masine` Category (is_for=MEHANIZACIJA); ako Category nema →
  `subcategories = []`; inače `subcategories = list(category.subcategories.filter(parent=None).order_by("display_order", "name"))`.
- **Query budget: 3 SQL upita** (Brand get_object + Category lookup + Subcategory list). HZM NE query-uje Product → NEMA N+1. Skeleton radi zaseban `Category.objects.get(...)` upit PA `category.subcategories.filter(...)`; test `test_hzm_query_budget_two_queries` lock-uje `django_assert_num_queries(3)`. (Ranija „2" formulacija je spajala Category+Subcategory u jedan; tačan broj iz skeleton-a je 3.)

### 2.2 `TulipMixPrikoliceView(DetailView)`
- `model = Brand`, `context_object_name = "brand"`.
- `get_object()` → `Brand.objects.get(slug="tulip")`; `Brand.DoesNotExist` → `Http404("Tulip brand nije konfigurisan u sistemu.")`.
- `get_template_names()` → coming-soon branching mirror 2.1 (`brands/tulip_mix_prikolice.html`).
- `get_context_data()` → ako `is_coming_soon` early-return. Inače:
  - `products` = `Product.objects.filter(brand=self.object, is_published=True).prefetch_related(Prefetch("specifications", queryset=ProductSpecification.objects.order_by("order", "id"))).order_by("price_eur", "name")` → list.
  - `spec_rows` = `_build_spec_rows(products)` — transponovan: `[{"key": <spec key>, "values": [v_model1, v_model2, ...]}]`; missing value → `None` (template → "—").
  - `testimonials` = `ProductTestimonial.objects.filter(product__brand=self.object, product__is_published=True).select_related("product").order_by("order", "-created_at")[:10]` → list.
- **Query budget (SM-D14):** KONSTANTAN bez obzira na broj proizvoda/specifikacija
  (Brand + Product + prefetch specifications + ProductTestimonial). `_build_spec_rows`
  koristi `product.specifications.all()` BEZ `.order_by()` → čita prefetch cache (NE N+1).
- **READ-ONLY cross-boundary** (SM-D16): NE WRITE na Product/Spec/Testimonial.

### 2.3 `SubcategoryListView` — UŽA izmena (SM-D13 / OQ-1a)
- ADD module-level mapa:
  ```python
  _CATEGORY_LANDING_BREADCRUMB_ROOT = {
      "radne-masine": {"label": _("Radne mašine"), "url_name": "brands:hzm_radne_masine"},
  }
  ```
- ADD `_breadcrumb_root_for(category)` → vraća `(item_dict, is_category_landing: bool)`.
  - Ako `category.slug` u mapi → `item = {"label": <mapped label>, "url": reverse(<mapped url_name>), "is_current": False}`, `is_category_landing = True`.
  - DEFAULT (sve Jeegee + nemapirano) → `item = {"label": _("Priključna mehanizacija"), "url": reverse("brands:jeegee_prikljucna"), "is_current": False}`, `is_category_landing = False`. **NEPROMENJENO ponašanje za Jeegee.**
- `_build_breadcrumb(category, current)`:
  - druga stavka (root) sada dolazi iz `_breadcrumb_root_for(category)`.
  - U intermediate/leaf grani: ako `is_category_landing == True` → **PRESKAČI** `category.name` link stavku (reconciliacija duplikata — HZM NE renderuje „Radne mašine → Radne mašine"). Ako `False` → zadrži `category.name` link stavku (Jeegee NEPROMENJENO).
- **Kanonski HZM L1 trag:** `["Početna"(link), "Radne mašine"(link→hzm_radne_masine), "<sub naziv>"(non-link)]` — length 3, duplikat-free.
- **Jeegee regression:** `["Početna"(link), "Priključna mehanizacija"(link→jeegee_prikljucna), "<category.name>"(link), <ancestors...>, "<leaf>"(non-link)]` — NEPROMENJENO.
- Breadcrumb context key: `breadcrumb_items` (list[dict] sa `label`/`url`/`is_current`), renderovan kroz `templates/brands/partials/_breadcrumb.html` (NETAKNUT).

---

## 3. Template-i (8 NEW fizičkih fajlova: 2 main + 5 partials + 1 CSS)

| Path | Tip | Sadržaj |
|---|---|---|
| `templates/brands/hzm_radne_masine.html` | NEW | `{% extends "base.html" %}`; outer `<section class="coric-brand-detail coric-hzm-radne-masine" data-testid="hzm-radne-masine-page" aria-label="…">`; `<section id="hzm-hero">` → `<section id="hzm-subcategories">` → opciono `<section id="hzm-catalog-cta">` (`{% if brand.catalog_pdf %}`). JEDAN h1 (hero); single main (base). |
| `templates/brands/partials/_hzm_hero.html` | NEW | `<div class="coric-brand-hero" data-testid="hzm-hero">` + include `hero_overlay_card.html` sa `variant="green"` (SM-D9), `{% if brand.logo %}` guard. |
| `templates/brands/partials/_hzm_subcategory_showcase.html` | NEW | Section eyebrow „KATEGORIJE RADNIH MAŠINA" + `<h2 id="hzm-subcategories-title">` + `.coric-category-showcase` grid; per-`subcategories` `<article class="coric-category-card" data-testid="hzm-subcategory-card-{{ sub.slug }}">`; CTA href = `{{ sub.get_absolute_url }}` (SM-D4) data-testid `hzm-subcategory-cta-{{ sub.slug }}`; `{% empty %}` „Kategorije radnih mašina su u pripremi." (`.coric-empty-state`). |
| `templates/brands/tulip_mix_prikolice.html` | NEW | outer `<section class="coric-brand-detail coric-tulip-mix" data-testid="tulip-mix-page" aria-label="…">`; `<section id="tulip-hero">` → `<section id="tulip-models">` → `{% if spec_rows %}<section id="tulip-comparison">` → `{% if testimonials %}<section id="tulip-testimonials">` → `{% if brand.catalog_pdf %}<section id="tulip-catalog-cta">`. JEDAN h1; single main. |
| `templates/brands/partials/_tulip_hero.html` | NEW | mirror `_hzm_hero.html`, `variant="green"`, `data-testid="tulip-hero"`. |
| `templates/brands/partials/_tulip_model_showcase.html` | NEW | Section eyebrow „MODELI PRIKOLICA" + `<h2 id="tulip-models-title">` + `.coric-category-showcase` grid; per-`products` `<article class="coric-product-card" data-testid="tulip-model-card-{{ product.slug }}">`; `responsive_picture(product.main_image)` (guard) + `<h3>` naziv + `key_features` lista + CTA „OPŠIRNIJE" href = `{{ product.get_absolute_url }}`; `{% empty %}` „Modeli prikolica su u pripremi.". |
| `templates/brands/partials/_tulip_comparison_table.html` | NEW | Section eyebrow „UPOREDNE DIMENZIJE" + `<h2 id="tulip-comparison-title">` + `<table class="coric-comparison-table" data-testid="tulip-comparison-table">` sa `<caption class="visually-hidden">` + `<thead>` `<th scope="col">` (Specifikacija + per-product naziv) + `<tbody>` `<th scope="row">{{ row.key }}` + `<td>{{ value|default:"—" }}`. |

Reuse partials (NETAKNUTI): `partials/hero_overlay_card.html`, `partials/section_eyebrow.html`,
`partials/wave_divider.html`, `partials/_testimonials_slider.html` (sa `slider_id="tulip-testimonials-title"`),
`brands/brand_coming_soon.html`.

---

## 4. CSS (`static/css/components/comparison-table.css` NEW + `main.css` EDIT)

`comparison-table.css` — `coric-comparison-table` BEM, sve vrednosti `var(--token)`:
- `.coric-comparison-table__heading`, `.coric-comparison-table__scroll` (`overflow-x: auto`),
  `.coric-comparison-table`, `.coric-comparison-table__corner`, `.coric-comparison-table__model`,
  `.coric-comparison-table__key`, `.coric-comparison-table__value`,
  `.coric-comparison-table__row:nth-child(even)` (zebra).
- 0 magic hex/px (allow `white`/`transparent`/`none`/`0`/`100%` keywords); svi BEM `coric-` prefiks.

`main.css` EDIT — ADD TAČNO 1 linija POSLE breadcrumb.css:
```css
@import url('./components/comparison-table.css');
```

REUSE bez novog import-a: `category-showcase.css` (HZM grid + coric-category-card),
`brand-listing.css` (coric-product-card DEFINISAN linija 72).

---

## 5. Data migracija (`apps/brands/migrations/0004_seed_hzm_tulip_brands.py` NEW)

`dependencies = [("brands", "0003_seed_jeegee_and_prikljucna_categories"),
("products", "0003_alter_productvariant_description_and_more")]` (SM-D8 cross-app lock).

RunPython idempotentna (`get_or_create`), seed callable + `reverse_code`.

**Callable nazivi (test-locked — `test_migration_0004_seed_hzm_tulip.py` import-uje po imenu):**
forward seed funkcija MORA biti nazvana `seed_hzm_and_tulip` (alt prihvaćen: `seed_hzm_tulip`);
reverse funkcija MORA biti nazvana `reverse_seed` (mirror 0003 precedent; alt prihvaćen: `reverse_hzm_tulip`).
`migrations.RunPython(seed_hzm_and_tulip, reverse_code=reverse_seed)`.

| Entitet | Ključ | Polja |
|---|---|---|
| HZM Brand | `slug="hzm"` | `name="HZM"`, `name_sr="HZM"`, `is_coming_soon=False` |
| HZM Category | `slug="radne-masine"` | `name="Radne mašine"`, `is_for="mehanizacija"`, `display_order=40` |
| Subcategory ×4 | `category=radne-masine`, `parent=None` | `mini-utovarivaci`/„Mini utovarivači"/10, `utovarivaci-bez-teleskopa`/„Utovarivači bez teleskopa"/20, `teleskopski-utovarivaci`/„Teleskopski utovarivači"/30, `telehendleri`/„Telehendleri"/40 |
| Tulip Brand | `slug="tulip"` | `name="Tulip"`, `name_sr="Tulip"` |
| Tulip Product ×2 | `brand=tulip`, `is_published=True` | `tulip-mix-6m3`/„Tulip MIX 6 m³"/`price_eur=Decimal("6500.00")`, `tulip-mix-8m3`/„Tulip MIX 8 m³"/`price_eur=Decimal("8200.00")`; `key_features` ≤ 3 stavke |
| ProductSpecification ×8 | po `product__slug` | „Zapremina" (6 m³/8 m³), „Dužina", „Širina", „Nosivost" — DEMO/placeholder; `section="ostalo"`, `order` 0..3 |

**Lock-ovi:**
- `price_eur` EKSPLICITNO 6500 < 8200 (deterministički primarni sort ključ).
- `key_features` MAX 3 stavke (`_PRODUCT_KEY_FEATURES_MAX=3` → `full_clean()` ValidationError ako više).
- Koristi `apps.get_model()` (historical snapshot) + `apps.get_model("products", "Product")`/`("products", "ProductSpecification")`.
- `reverse_code` FK-safe redosled: ProductSpecification → Product → Tulip Brand → Subcategory → Category → HZM Brand.
- Smoke očekivani count: Brand hzm/tulip = 2, Subcategory radne-masine = 4, Tulip Product = 2, Tulip ProductSpecification = 8.

---

## 6. i18n / a11y (AC8)

Novi msgid (sr msgstr popunjen; hu/en fallback): „Radne mašine", „MIX prikolice",
„KATEGORIJE RADNIH MAŠINA", „MODELI PRIKOLICA", „UPOREDNE DIMENZIJE", „Pregled po
kategorijama", „Uporedne dimenzije", „Uporedne dimenzije Tulip MIX prikolica",
„Specifikacija", „POGLEDAJ KATEGORIJU", „OPŠIRNIJE", „Preuzmi katalog",
„Preuzmi {{ brand }} katalog", „Pogledaj kategoriju: {{ category }}", empty-state
poruke, aria-labeli, Http404 poruke.

A11y: TAČNO 1 `<h1>` (hero) + single `<main>` (base) po strani; outer `<section>`
`aria-label` (NE `aria-labelledby` — SM-D8); inner sekcije `aria-labelledby`; tabela
`<caption>` + `scope="col"`/`scope="row"` (WCAG 1.3.1); NEMA ćirilice; pune dijakritike.

---

## 7. data-testid površina

`hzm-radne-masine-page`, `hzm-hero`, `hzm-subcategory-showcase-grid`,
`hzm-subcategory-card-<slug>`, `hzm-subcategory-cta-<slug>`, `hzm-catalog-download`,
`tulip-mix-page`, `tulip-hero`, `tulip-model-card-<slug>`, `tulip-comparison-table`,
`tulip-catalog-download`, (testimonials slider reuse: `testimonials-slider`).
