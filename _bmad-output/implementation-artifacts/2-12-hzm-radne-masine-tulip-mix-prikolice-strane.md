---
story_id: "2.12"
story-key: 2-12-hzm-radne-masine-tulip-mix-prikolice-strane
title: HZM Radne Mašine + Tulip MIX Prikolice Strane
status: ready-for-dev
epic: 2
epic_num: 2
epic_title: Public Catalog — Browse Brands & Products
module: brands
created: 2026-05-31
last_modified: 2026-05-31
complexity: M
author: Mihas (SM autonomous; DVE statičke brand landing strane u jednoj story — (A) HZM Radne Mašine `/mehanizacija/radne-masine/` REUSE 1:1 Story 2-10 JeegeePrikljucnaView + coric-category-card pattern ali sa 4 potkategorije umesto 3 Category-je (Mini utovarivači / Utovarivači bez teleskopa / Teleskopski utovarivači / Telehendleri — modelirano kao Subcategory dece HZM radne-masine Category-je) → CTA vodi na Story 2-11 SubcategoryListView; (B) Tulip MIX Prikolice `/mehanizacija/mix-prikolice/` model-showcase strana sa 2 Product modela (6 m³ + 8 m³) + uporedna dimenziona tabela (DESIGN.md ključ-vrednost tabela token layout, side-by-side iz ProductSpecification) + „Zadovoljni kupci" testimonials slider (REUSE Story 2-7 _testimonials_slider.html shared partial) + „Preuzmi katalog" CTA. NEMA HTMX, NEMA range slidera, NEMA paginacije, NEMA forma. REUSE: BrandDetailView/JeegeePrikljucnaView CBV pattern (2-6/2-10), hero_overlay_card/section_eyebrow/pill_button/wave_divider partials (1-7), brand_coming_soon.html (2-6), coric-category-card + category-showcase.css (2-10), _testimonials_slider.html (2-7), responsive_picture (2-3). Cross-boundary brands→products READ-ONLY za Tulip Product query (SM-D16 Exception, mirror Story 2-11).)
depends_on:
  - 2-1-brand-series-category-subcategory-modeli  # Brand, Category (is_for="mehanizacija"), Subcategory self-FK chain + get_absolute_url(); CategoryScope.MEHANIZACIJA
  - 2-2-product-i-related-modeli                   # Product (subcategory FK), ProductSpecification (key/value dimenzije), ProductTestimonial (Zadovoljni kupci)
  - 2-3-image-pipeline-sa-sorl-thumbnail-responsive-srcset  # {% responsive_picture %} za HZM/Tulip brand logo + Tulip model slike
  - 2-6-brand-listing-strana-sa-grid-extended-layout-om     # BrandDetailView CBV pattern, get_template_names() coming-soon branching, brand_coming_soon.html 1:1, _catalog_cta.html catalog CTA pattern, cross-boundary brands→products (SM-D16)
  - 2-7-product-detail-strana                       # templates/partials/_testimonials_slider.html shared partial (slider_id kwarg) za Tulip „Zadovoljni kupci"; ProductSpecification akordion → ovde uporedna tabela
  - 2-10-jeegee-prikljucna-mehanizacija-strana      # JeegeePrikljucnaView pattern (1 brand → N showcase kartice) + coric-category-card BEM + category-showcase.css 1:1 REUSE; 0003 seed migracija precedent; _category_showcase.html markup
  - 2-11-subcategory-listing-4-nivoa-hijerarhija    # SubcategoryListView (HZM CTA vodi na njega kroz Subcategory.get_absolute_url()); Subcategory.get_absolute_url() već implementiran; subcategory_listing_l* URL pattern-i
---

# Story 2.12: HZM Radne Mašine + Tulip MIX Prikolice Strane

Status: ready-for-dev

## Opis

As a **posetilac (poljoprivrednik / vozni-park menadžer koji pregleda preostali deo Ćorić Agrar portfolija — HZM utovarivače i Tulip MIX prikolice — kroz Home „Radne mašine" / „Mehanizacija" sekciju ili direct deep-link; Đorđe — Mihasov klijent koji testira tastaturom + NVDA na 375px mobilnom ekranu)**,

I want **(A) da otvorim HZM Radne Mašine landing stranu na `/sr/mehanizacija/radne-masine/` i vidim: HZM hero overlay karticu (logo + slogan + Repeating Element watermark) + 4-card showcase grid sa 4 potkategorije radnih mašina — „Mini utovarivači", „Utovarivači bez teleskopa", „Teleskopski utovarivači", „Telehendleri" — svaka kartica sa nazivom + opisom + „POGLEDAJ KATEGORIJU" CTA koji vodi na listing modela u toj potkategoriji (Story 2-11 `SubcategoryListView`); i (B) da otvorim Tulip MIX Prikolice landing stranu na `/sr/mehanizacija/mix-prikolice/` i vidim: Tulip hero overlay karticu + 2 modela prikolica (MIX 6 m³ i MIX 8 m³) kao model-kartice sa slikom + nazivom + ključnim karakteristikama + „OPŠIRNIJE" CTA → product detail; uporednu dimenzionu tabelu (ključ-vrednost layout iz DESIGN.md, dva modela side-by-side: zapremina, dužina, širina, nosivost, …); sekciju „Zadovoljni kupci" (testimonials slider) ako Tulip Product-i imaju testimonijale; i „Preuzmi Tulip katalog" CTA banner (Wave Divider iznad) ako `tulip.catalog_pdf` postoji**,

so that **brzo (≤3 klika sa Home strane) vidim ostatak ponude i navigiram do detalja: za HZM — klik na potkategoriju vodi me na model listing (Marko traži teleskopski utovarivač → klikne „Teleskopski utovarivači"); za Tulip — odmah uporedim 6 m³ vs 8 m³ prikolicu kroz dimenzionu tabelu i pročitam iskustva drugih kupaca; strana zadovoljava Lighthouse a11y ≥ 95 (UX-DR-13 + NFR-2 + Story 9-9 audit gate), poštuje single-h1 pravilo (h1 je brand naziv iz hero card-a), koristi semantic HTML5, i REUSE-uje SVE postojeće patterne (NEMA novih JS modula, minimalan novi CSS) tako da je vizuelno i interakciono konzistentna sa Jeegee stranom iz Story 2-10**.

Ova story završava **brand-landing trijadu mehanizacije** (Jeegee 2-10 → HZM + Tulip 2-12). Dve strane dele isti REUSE temelj ali imaju **dve različite varijante**:

- **HZM = category-showcase varijanta** (identičan pattern kao Story 2-10 Jeegee): 1 brand → N showcase kartice koje vode dalje u drill-down. Jedina razlika od Jeegee je: (1) HZM ima **4 kartice** (Jeegee 3) — `category-showcase.css` već koristi responzivni `repeat(auto-fit, minmax(280px, 1fr))` grid koji automatski handluje 4 kartice (foundation eksplicitno postavljena u Story 2-10 SM-D); (2) HZM kartice su **Subcategory** instance (dece HZM `radne-masine` Category-je), NE root Category instance kao kod Jeegee — pa CTA href vodi na Story 2-11 `SubcategoryListView` kroz `subcategory.get_absolute_url()` (već implementiran u Story 2-11), umesto na `subcategory_listing_category`. Vidi SM-D2 + SM-D4.
- **Tulip = model-showcase varijanta** (NOVI mini-pattern u ovoj story, ali sastavljen iz postojećih komponenti): 1 brand → 2 konkretna Product modela + uporedna dimenziona tabela + testimonials. Ovo je jedina **nova kompozicija** u Epic 2 brand-landing prostoru; renderuje Product model-kartice (NE Subcategory kartice) i side-by-side spec tabelu.

**Strane NEMAJU HTMX, NEMAJU JavaScript interakciju (izuzev REUSE testimonials slider-a iz Story 2-7 koji ima sopstveni vendor-free JS modul `testimonials-slider.js` — NE dodaje se novi JS), NEMAJU forme, NEMAJU paginaciju, NEMAJU sort, NEMAJU filtere — pure server-side rendered static content.** Razlika u odnosu na Story 2-8/2-9 (HTMX filteri) je kritična i namerna.

**REUSE fokus (0 novih JS modula; 1 nova CSS komponenta — uporedna dimenziona tabela):**

- **`Brand` model** (Story 2-1): `Brand.objects.get(slug="hzm")` i `Brand.objects.get(slug="tulip")` (seed kroz data migraciju 0004 — SM-D3). Polja: `brand.slug`, `brand.name`, `brand.logo`, `brand.slogan`, `brand.brand_color`, `brand.catalog_pdf`, `brand.is_coming_soon`.
- **`Category` model** (Story 2-1): HZM strana fetch-uje HZM `radne-masine` Category (slug="radne-masine", is_for="mehanizacija") kao root, a 4 kartice su njena **Subcategory** dece (`category.subcategories.filter(parent=None)`).
- **`Subcategory` model** (Story 2-1 + 2-11): 4 HZM potkategorije (Mini utovarivači / Utovarivači bez teleskopa / Teleskopski utovarivači / Telehendleri); polja `subcategory.slug`, `subcategory.name`, `subcategory.description`, `subcategory.icon`, `subcategory.get_absolute_url()` (Story 2-11 — vodi na `subcategory_listing_l1`).
- **`Product` model** (Story 2-2, READ-ONLY cross-boundary per SM-D16): Tulip strana — `Product.objects.filter(brand=tulip, is_published=True)`. Polja: `product.slug`, `product.name`, `product.main_image`, `product.key_features`, `product.get_absolute_url`, `product.specifications` (ProductSpecification prefetch za dimenzionu tabelu). **NE WRITE na Product iz brands view-a.**
- **`ProductSpecification` model** (Story 2-2): Tulip uporedna dimenziona tabela — key/value specifikacije dva modela renderovane side-by-side (zapremina, dužina, širina, nosivost, …).
- **`ProductTestimonial` model** (Story 2-2): Tulip „Zadovoljni kupci" slider — `ProductTestimonial.objects.filter(product__brand=tulip, product__is_published=True)`.
- **`templates/partials/hero_overlay_card.html`** (Story 1-7) — REUSE 1:1 za HZM i Tulip hero; prima `title=brand.name`, `brand_logo`, `brand_logo_alt`, `variant`, `bullets=""`.
- **`templates/partials/repeating_element.html`** (Story 1-7) — INDIREKTNO kroz hero_overlay_card; `variant` se rezolvira na CSS klasu. **KRITIČNO (SM-D9):** CSS ima SAMO `coric-repeating-element--green` (linija 11) i `coric-repeating-element--jeegee` (linija 14). HZM i Tulip NEMAJU dedicated variant CSS klasu → koriste `variant="green"` (default brand-green watermark) DOK Story 9-10 polish ne doda brand-specifične variant-e. Vidi SM-D9 — NE izmišljati `variant="hzm"` ili `variant="tulip"` (rezultiralo bi unstyled watermark-om, mirror Story 2-6 `variant="blue"` dormant bug).
- **`templates/partials/section_eyebrow.html`** (Story 1-7) — UPPERCASE eyebrow iznad svake sekcije.
- **`templates/partials/pill_button.html`** (Story 1-7) — opciono za CTA dugmad (HZM/Tulip koriste direct `coric-button` markup, mirror Story 2-10 SM-D6).
- **`templates/partials/wave_divider.html`** (Story 1-7) — iznad „Preuzmi katalog" CTA banner-a (Tulip; HZM opciono ako catalog_pdf postoji).
- **`templates/partials/_testimonials_slider.html`** (Story 2-7 shared partial sa `slider_id` kwarg-om) — REUSE 1:1 za Tulip „Zadovoljni kupci"; prima `testimonials` context + opciono `slider_id`.
- **`templates/brands/brand_coming_soon.html`** (Story 2-6) — REUSE 1:1 za HZM ili Tulip ako `is_coming_soon=True` (get_template_names() branching mirror Story 2-10).
- **`templates/brands/partials/_category_showcase.html`** (Story 2-10/2-11) — REFERENCE markup pattern; HZM koristi vlastiti `_hzm_subcategory_showcase.html` jer kartice su Subcategory (CTA href je `subcategory.get_absolute_url()`), ali REUSE 1:1 `coric-category-card` BEM iz `category-showcase.css`. Vidi SM-D4.
- **`static/css/components/category-showcase.css`** (Story 2-10) — REUSE 1:1 za HZM 4-card grid (`coric-category-showcase` + `coric-category-card`). NE edit-uje se.
- **`{% responsive_picture %}`** (Story 2-3) — za Tulip model-kartice (`product.main_image`) i opciono brand logo.
- **CSS tokens** (`static/css/tokens.css`, Story 1-5): `--color-brand-green-800`, `--color-neutral-white`, `--color-neutral-cream`, `--color-neutral-gray-700`, `--spacing-scale-*`, `--rounded-md`, `--typography-scale-h2/h3/body/caption`.
- **`coric-button` + `coric-button--primary`** BEM (Story 1-7 `pill-button.css`) — REUSE za sve CTA.
- **`coric-product-card` BEM** (definisano u `static/css/components/brand-listing.css:72` — verifikovano live; `tractor-listing.css` ga SAMO referencira u komentaru, NE definiše) — REUSE za Tulip model-kartice (slika + naziv + ključne karakteristike + „OPŠIRNIJE" CTA). NE re-definiše se. Oba CSS fajla su import-ovana u `main.css` pa se renderuje, ali izvorni fajl je `brand-listing.css`.

**Jedina NOVA CSS komponenta:** `static/css/components/comparison-table.css` — Tulip uporedna dimenziona tabela (`coric-comparison-table` BEM: responsive ključ-vrednost grid sa header redom dva modela, zebra redovi, horizontal scroll na mobile-u). Sve vrednosti kroz `var(--token)`.

**Foundation za buduće Story-je:**

- **Story 3-1 (Home strana):** sekcija „Radne mašine" prikazuje HZM kategorije (Repeating Element po kategoriji per epics.md 3.1); može reuse-ovati `coric-category-card`. Sekcija „Mehanizacija" linkuje na sve 3 brand landing strane (Jeegee/HZM/Tulip).
- **Story 2-13 (Global Search):** rezultati linkuju na Tulip Product detail strane + HZM SubcategoryListView strane registrovane lancem.

**Princip:** Pure server-side rendering, **NEMA HTMX**, **NEMA novog JavaScript-a** (Tulip testimonials REUSE postojeći `testimonials-slider.js` iz Story 2-7), **NEMA forma**, **NEMA admin promena**, **NEMA migracije šeme** (Story 2-1 + 2-2 modeli nepromenjeni) — ALI **JEDNA data migracija 0004** koja seed-uje HZM Brand + HZM `radne-masine` Category + 4 Subcategory dece + Tulip Brand + 2 Tulip Product-a (+ specifikacije za dimenzionu tabelu). Vanilla Django CBV (`DetailView` mirror Story 2-10 `JeegeePrikljucnaView` — 2 nove view klase). CSS BEM sa `coric-` prefiksom + isključivo `var(--token)`. Sve user-facing string-ove kroz `{% translate %}` / `gettext_lazy as _`. URL slug ASCII (`radne-masine`, `mix-prikolice`, `mini-utovarivaci`, `teleskopski-utovarivaci` — NE dijakritike u slug-u; ali č/ć/ž/š/đ PUNE u `name` poljima koja se renderuju korisniku).

**Strukturna arhitektura — repository delta:** **8 NEW fizičkih fajlova (6 logičkih grupa) + 6 EDIT + 0 DELETE + 1 data migracija** (kanonsko brojanje — prebrojivo iz tabele ispod; IMP-1 lock: Dev stvara svih 8 fizičkih NEW fajlova):

| Path | Tip | Razlog |
|---|---|---|
| `apps/brands/views.py` | EDIT (ADD 2 klase + konstante + parametrizuj `SubcategoryListView._build_breadcrumb` root label — SM-D13) | Dodaje `HzmRadneMasineView(DetailView)` + `TulipMixPrikoliceView(DetailView)` (postojeće `BrandDetailView` + `JeegeePrikljucnaView` ostaju NETAKNUTE). **`SubcategoryListView` dobija UŽU izmenu (SM-D13 / OQ-1a — iter 2):** `_build_breadcrumb` root stavka se parametrizuje preko `_breadcrumb_root_for(category)` (mapa `_CATEGORY_LANDING_BREADCRUMB_ROOT` sadrži SAMO `radne-masine`→„Radne mašine"/`hzm_radne_masine`; DEFAULT = postojeći generički „Priključna mehanizacija"/`jeegee_prikljucna` prefiks za sve Jeegee kategorije) DA HZM drill-down NE renderuje pogrešan VIDLJIV label „Priključna mehanizacija", I intermediate/leaf grana RECONCILE-uje duplikat: kada je `is_category_landing=True` (radne-masine), `category.name` stavka se PRESKAČE da HZM ne renderuje susedni duplikat „Radne mašine → Radne mašine". Kanonski HZM L1 trag = `["Početna", "Radne mašine"(link), "<sub>"(non-link)]` (3 stavke, duplikat-free). Regression guard: Jeegee `prikljucna` breadcrumb i dalje pokazuje „Priključna mehanizacija" + zadržava `category.name` link stavku (root-label ≠ category.name pa NEMA kolapsa). Obe view klase imaju `get_object()` override sa hardcoded brand slug lookup (`hzm` / `tulip`) + Http404 guard (REUSE Story 2-10 SM-D7 idiom); `get_template_names()` coming-soon branching (REUSE Story 2-6 SM-D19 + brand_coming_soon.html 1:1); `get_context_data()`: HZM dodaje `subcategories` (4 dece HZM Category-je), Tulip dodaje `products` (2 Tulip Product-a + prefetch specifications) + `testimonials` + `spec_rows` (transponovan dimenzioni tabela kontekst — SM-D7). Module-level konstante `_HZM_BRAND_SLUG`, `_HZM_CATEGORY_SLUG`, `_TULIP_BRAND_SLUG`. Cross-boundary `from apps.products.models import Product, ProductSpecification, ProductTestimonial` VEĆ importovan (linija 21) — REUSE. `Http404` već importovan (linija 15). EDIT NIJE potreban za import (Category/Subcategory/Brand već importovani linija 20). |
| `apps/brands/urls.py` | EDIT (ADD 2 path) | Dodaje TAČNO 2 nova statička URL pattern-a POSLE postojećih: `path("mehanizacija/radne-masine/", HzmRadneMasineView.as_view(), name="hzm_radne_masine")` + `path("mehanizacija/mix-prikolice/", TulipMixPrikoliceView.as_view(), name="tulip_mix_prikolice")`. **KRITIČNO (SM-D5):** oba su statički dvoslojni path-ovi bez slug-a → NEMA kolizije sa `mehanizacija/prikljucna/<slug:category_slug>/` (Story 2-11) jer `radne-masine`/`mix-prikolice` NISU `prikljucna`; NEMA kolizije sa `mehanizacija/polovna/` (Story 2-9 products); NEMA kolizije sa `traktori/<slug>/`. EDIT import: dodaj `HzmRadneMasineView, TulipMixPrikoliceView` u postojeću `from apps.brands.views import (...)` listu. |
| `templates/brands/hzm_radne_masine.html` | NOVO | HZM glavni template — `{% extends "base.html" %}`; outer `<section class="coric-brand-detail coric-hzm-radne-masine" data-testid="hzm-radne-masine-page" aria-label="...">`; hero sekcija (include `_hzm_hero.html`) → 4-card subcategory showcase (include `_hzm_subcategory_showcase.html`) → opciono catalog CTA banner. **JEDAN `<h1>`** (kroz hero_overlay_card partial). **single `<main>`** (iz base.html). Mirror Story 2-10 `jeegee_prikljucna.html` strukturu 1:1. |
| `templates/brands/partials/_hzm_hero.html` | NOVO | HZM hero wrapper — `<div class="coric-brand-hero">` + include `partials/hero_overlay_card.html` sa `title=brand.name`, `brand_logo`, `variant="green"` (SM-D9 — NEMA hzm variant CSS), `bullets=""`. Defensive `{% if brand.logo %}` guard (mirror Story 2-10 `_jeegee_hero.html`). |
| `templates/brands/partials/_hzm_subcategory_showcase.html` | NOVO | HZM 4-card grid — Section Eyebrow („KATEGORIJE RADNIH MAŠINA") + h2 + `coric-category-showcase` grid koji iterira `subcategories` context list i renderuje per-subcategory `coric-category-card` (REUSE 2-10 BEM 1:1). RAZLIKA od 2-10 `_category_showcase.html`: CTA href je `{% url 'brands:subcategory_listing_category' category_slug='radne-masine' %}` NIJE primenjivo — kartice su Subcategory pa href = `subcategory.get_absolute_url()` (Story 2-11 — vodi na `subcategory_listing_l1`). `{% empty %}` clause. Vidi SM-D4. |
| `templates/brands/tulip_mix_prikolice.html` | NOVO | Tulip glavni template — `{% extends "base.html" %}`; outer `<section class="coric-brand-detail coric-tulip-mix" ...>`; hero (include `_tulip_hero.html`) → 2-model showcase grid (include `_tulip_model_showcase.html`) → uporedna dimenziona tabela (include `_tulip_comparison_table.html`, samo ako oba modela imaju specifikacije) → „Zadovoljni kupci" testimonials (include `partials/_testimonials_slider.html` sa `slider_id="tulip-testimonials-title"`, samo ako `testimonials` nije prazno) → opciono „Preuzmi Tulip katalog" CTA. **JEDAN `<h1>`** + **single `<main>`**. |
| `templates/brands/partials/_tulip_hero.html` | NOVO | Tulip hero wrapper — mirror `_hzm_hero.html` sa `variant="green"` (SM-D9). |
| `templates/brands/partials/_tulip_model_showcase.html` | NOVO | Tulip 2-model grid — Section Eyebrow + `coric-category-showcase` grid (REUSE grid wrapper) koji iterira `products` i renderuje per-product `coric-product-card` (REUSE Story 2-8 BEM: `responsive_picture(main_image)` + naziv + `key_features` lista + „OPŠIRNIJE" CTA → `product.get_absolute_url`). `{% empty %}` clause „Modeli prikolica su u pripremi.". |
| `templates/brands/partials/_tulip_comparison_table.html` | NOVO | Tulip uporedna dimenziona tabela — `<table class="coric-comparison-table">` sa header redom (2 model naziva) + redovi ključ-vrednost (transponovan iz `spec_rows` context-a — SM-D7); DESIGN.md ključ-vrednost token layout. `<caption class="visually-hidden">` za a11y. Renderuje samo ako `spec_rows` nije prazno. |
| `static/css/components/comparison-table.css` | NOVO | `coric-comparison-table` BEM (header red, ključ ćelija, vrednost ćelije, zebra redovi, responsive horizontal scroll na <768px). Sve vrednosti kroz `var(--token)`. JEDINA nova CSS komponenta. |
| `static/css/main.css` | EDIT | Dodaje TAČNO 1 nova `@import url('./components/comparison-table.css');` linija POSLE postojeće `@import url('./components/breadcrumb.css');` (Story 2-11 zadnja). HZM grid REUSE-uje category-showcase.css (NEMA novog import-a); Tulip model-kartice REUSE-uju `brand-listing.css` (gde je `.coric-product-card` DEFINISAN — linija 72; NE tractor-listing.css koji ga samo komentariše). |
| `apps/brands/migrations/0004_seed_hzm_tulip_brands.py` | NOVO (data migracija) | RunPython idempotentna (`get_or_create`) data migracija: HZM Brand (slug="hzm", name="HZM", is_coming_soon=False) + HZM Category (slug="radne-masine", name="Radne mašine", is_for="mehanizacija", display_order=40) + 4 Subcategory dece (mini-utovarivaci/10, utovarivaci-bez-teleskopa/20, teleskopski-utovarivaci/30, telehendleri/40 — sve `category=radne-masine`, `parent=None`) + Tulip Brand (slug="tulip", name="Tulip") + 2 Tulip Product (slug="tulip-mix-6m3" + "tulip-mix-8m3", brand=tulip, is_published=True) + ProductSpecification redovi za dimenzionu tabelu (zapremina/dužina/širina/nosivost za oba modela). `reverse_code` DELETE-uje TAČNO te instance po slug-u. Vidi SM-D3 + SM-D8 za depends_on. |
| `locale/sr/LC_MESSAGES/django.po`, `locale/hu/LC_MESSAGES/django.po`, `locale/en/LC_MESSAGES/django.po` | EDIT (×3) | Popuni msgstr za nove msgid (page title-ovi, meta description-i, eyebrow tekstovi „KATEGORIJE RADNIH MAŠINA" / „MODELI PRIKOLICA", „POGLEDAJ KATEGORIJU" / „OPŠIRNIJE" / „Preuzmi katalog" / „Uporedne dimenzije" / „Zadovoljni kupci" CTA/heading, empty-state poruke, aria-labeli, Http404 poruke). Subcategory/Product/Category `name` polja se NE prevode ovde (modeltranslation hu/en deferred to Story 8-5; v1 prikazuje sr na svim locale-ima — mirror Story 2-10 SM-D). |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | EDIT | Postavi `2-12-hzm-radne-masine-tulip-mix-prikolice-strane` status na `ready-for-dev` (SM handoff). NIJE deliverable file edit (SM tracking). |

**Brojanje (KANONSKO — single source of truth):** **8 NEW fizičkih fajlova (6 logičkih grupa) + 6 EDIT + 0 DELETE + 1 data migracija.**

Razlaganje (prebrojiti iz tabele iznad — TAČNO 8 fizičkih NEW fajlova):
- **8 NEW fizičkih fajlova:** `hzm_radne_masine.html` + `_hzm_hero.html` + `_hzm_subcategory_showcase.html` + `tulip_mix_prikolice.html` + `_tulip_hero.html` + `_tulip_model_showcase.html` + `_tulip_comparison_table.html` + `comparison-table.css` (= 8 fajlova). **Logičko grupisanje (6 grupa, samo orijentir — NIJE broj fajlova za kreiranje):** 2 main template-a + 1 CSS = 3; 5 partials grupisani u 3 logičke jedinice (HZM partials, Tulip partials, comparison partial) = 3; ukupno 6 logičkih grupa. **IMP-1 lock — Dev: KANONSKI broj fajlova za kreiranje je 8 fizičkih NEW; „6 logičkih grupa" je samo organizaciona napomena. Stvaraj svih 8 fajlova.**
- **6 EDIT:** `apps/brands/views.py` (ADD 2 klase) + `apps/brands/urls.py` (ADD 2 path) + `static/css/main.css` (+1 @import) + 3 .po fajla (locale = 1 logički EDIT, 3 fizička). Sprint-status.yaml je SM handoff tracking (counted separately).
- **1 data migracija:** `apps/brands/migrations/0004_seed_hzm_tulip_brands.py` — pure RunPython, NEMA šeme promene.

Postojeći fajlovi koji ostaju **NETAKNUTI** (regression guards): `apps/brands/models.py` (NEMA model promena — samo data; `Subcategory.get_absolute_url()` već implementiran u Story 2-11), `apps/brands/admin.py`, `apps/brands/translation.py`, `apps/brands/migrations/0001-0003`, `apps/brands/views.py` postojeće klase (`BrandDetailView`, `JeegeePrikljucnaView` — NETAKNUTE; `SubcategoryListView` — DODAJU se 2 nove klase + UŽA izmena `_build_breadcrumb` root-parametrizacije + duplikat-reconciliacije po SM-D13 / OQ-1a (iter 2), ostatak `SubcategoryListView` logike NETAKNUT), `apps/products/` (kompletno — READ-ONLY query, NEMA edit), `apps/core/`, `apps/media_pipeline/`, `config/urls.py` (URL include red ne menja se), `templates/base.html`, `templates/partials/*` (Story 1-7 + Story 2-7 `_testimonials_slider.html` — REUSE 1:1 bez izmena), `templates/brands/jeegee_prikljucna.html` + `_jeegee_hero.html` + `_category_showcase.html` (Story 2-10/2-11 — NETAKNUTI), `templates/brands/subcategory_listing.html` + `_breadcrumb.html` + `_subcategory_showcase.html` + `_model_grid.html` (Story 2-11 — NETAKNUTI), `templates/products/partials/_results_grid.html` (Story 2-8 — REUSE pattern, NE edit), `static/vendor/*` (NEMA novih vendor asset-a), `static/js/*` (NEMA novih JS modula — testimonials-slider.js iz Story 2-7 REUSE), `static/css/tokens.css`, `static/css/components/category-showcase.css` (Story 2-10 — REUSE 1:1, NE edit), `static/css/components/brand-listing.css` (`.coric-product-card` DEFINISAN linija 72 — REUSE, NE edit), `static/css/components/tractor-listing.css` (NE edit; samo komentar-referenca na coric-product-card), `static/css/components/{repeating-element,hero-overlay-card,pill-button,section-eyebrow,wave-divider,testimonials-slider,breadcrumb}.css` (REUSE), `pyproject.toml`, `config/settings/`.

## Kriterijumi prihvatanja

**AC1 — URL pattern-i: `/<lang>/mehanizacija/radne-masine/` rezolvuje `HzmRadneMasineView`; `/<lang>/mehanizacija/mix-prikolice/` rezolvuje `TulipMixPrikoliceView`; oba HTTP 200 za sva 3 locale; NEMA kolizije sa Story 2-9/2-10/2-11 pattern-ima**

- **Given** `apps.brands` registrovan; `i18n_patterns()` aktivan (Story 1-4); postojeći pattern-i u `apps/brands/urls.py`: `traktori/<slug:slug>/`, `mehanizacija/prikljucna/` (Story 2-10), `mehanizacija/prikljucna/<slug:category_slug>/...` (Story 2-11 — 4 pattern-a); u `apps/products/urls.py`: `proizvod/<slug>/`, `traktori/`, `mehanizacija/polovna/`; `config/urls.py` učitava `apps.brands.urls` PRE `apps.products.urls`; HZM + Tulip Brand instance postoje u DB (seed 0004 — SM-D3)
- **When** dodajem 2 nove view klase u `apps/brands/views.py` i 2 nova pattern-a u `apps/brands/urls.py`:
  ```python
  path("mehanizacija/radne-masine/", HzmRadneMasineView.as_view(), name="hzm_radne_masine"),
  path("mehanizacija/mix-prikolice/", TulipMixPrikoliceView.as_view(), name="tulip_mix_prikolice"),
  ```
- **Then**:
  - `reverse("brands:hzm_radne_masine")` → `/sr/mehanizacija/radne-masine/` (analogno hu/en)
  - `reverse("brands:tulip_mix_prikolice")` → `/sr/mehanizacija/mix-prikolice/`
  - GET `/sr/mehanizacija/radne-masine/` → HTTP 200; GET `/sr/mehanizacija/mix-prikolice/` → HTTP 200
  - GET `/sr/mehanizacija/prikljucna/` i dalje → HTTP 200 (JeegeePrikljucnaView Story 2-10) — NIJE shadow-ovano
  - GET `/sr/mehanizacija/prikljucna/osnovna-obrada-zemljista/` i dalje → rezolvuje SubcategoryListView (Story 2-11) — NIJE shadow-ovano
  - GET `/sr/mehanizacija/polovna/` i dalje → HTTP 200 (UsedMachineryListView Story 2-9) — NIJE shadow-ovano
  - GET `/sr/mehanizacija/radne-masine` (bez trailing slash) → `APPEND_SLASH` redirekt na `/sr/mehanizacija/radne-masine/`
- **And** URL deconfliction (SM-D5): `radne-masine` i `mix-prikolice` su statički segmenti POSLE `mehanizacija/`; NE poklapaju se sa `prikljucna` ni `polovna`; NEMA slug converter overlap-a
- **And** `uv run python manage.py check` exit code 0; routing test asertuje svi pattern-i koegzistiraju
- **And** smoke verifikacija:
  ```bash
  uv run python manage.py shell -c "from django.urls import reverse; \
    from django.utils.translation import activate; activate('sr'); \
    print(reverse('brands:hzm_radne_masine')); \
    print(reverse('brands:tulip_mix_prikolice')); \
    print(reverse('brands:jeegee_prikljucna')); \
    print(reverse('products:used_machinery_list'))"
  ```
  Očekivan output:
  ```
  /sr/mehanizacija/radne-masine/
  /sr/mehanizacija/mix-prikolice/
  /sr/mehanizacija/prikljucna/
  /sr/mehanizacija/polovna/
  ```

**AC2 — `HzmRadneMasineView` (CBV `DetailView`): hardcoded HZM brand lookup (slug="hzm") + Http404 guard; `get_template_names()` coming-soon branching (REUSE brand_coming_soon.html 1:1); `get_context_data()` dodaje `subcategories` (4 dece HZM `radne-masine` Category-je, parent=None, ordered by display_order)**

- **Given** AC1; Brand + Category + Subcategory modeli (Story 2-1); HZM Brand + HZM Category + 4 Subcategory seed-ovani (0004 — SM-D3); CategoryScope.MEHANIZACIJA TextChoices
- **When** dodajem `HzmRadneMasineView` u `apps/brands/views.py` POSLE `SubcategoryListView`. Module-level konstante (POSLE postojećih `_JEEGEE_*`):
  ```python
  # Story 2.12 — HZM Radne Mašine + Tulip MIX Prikolice landing strane
  _HZM_BRAND_SLUG = "hzm"
  _HZM_CATEGORY_SLUG = "radne-masine"
  _TULIP_BRAND_SLUG = "tulip"
  ```
  Source skeleton (Dev MORA implementirati — mirror Story 2-10 `JeegeePrikljucnaView` 1:1):
  ```python
  class HzmRadneMasineView(DetailView):
      """HZM Radne Mašine landing strana — Story 2.12.

      Statička 4-card subcategory showcase (REUSE Story 2-10 Jeegee pattern).
      Kartice su Subcategory dece HZM 'radne-masine' Category-je; CTA href je
      subcategory.get_absolute_url() (Story 2-11 SubcategoryListView). View NE
      query-uje Product — samo Brand + Subcategory.
      """

      model = Brand
      context_object_name = "brand"

      def get_object(self, queryset=None):
          if queryset is None:
              queryset = self.get_queryset()
          try:
              return queryset.get(slug=_HZM_BRAND_SLUG)
          except Brand.DoesNotExist as exc:
              raise Http404(_("HZM brand nije konfigurisan u sistemu.")) from exc

      def get_template_names(self):
          if getattr(self, "object", None) is not None and self.object.is_coming_soon:
              return ["brands/brand_coming_soon.html"]
          return ["brands/hzm_radne_masine.html"]

      def get_context_data(self, **kwargs):
          ctx = super().get_context_data(**kwargs)
          if self.object.is_coming_soon:
              return ctx
          try:
              category = Category.objects.get(
                  slug=_HZM_CATEGORY_SLUG,
                  is_for=Category.CategoryScope.MEHANIZACIJA,
              )
          except Category.DoesNotExist:
              ctx["subcategories"] = []
              return ctx
          subcategories = list(
              category.subcategories.filter(parent=None).order_by(
                  "display_order", "name"
              )
          )
          # get_absolute_url() na Subcategory zahteva da category/parent budu
          # postavljeni (već jesu iz query-ja); set za sigurnost u get_ancestors_chain.
          for sub in subcategories:
              sub.category = category
          ctx["subcategories"] = subcategories
          return ctx
  ```
  **NAPOMENA — related_name (SM-D6 — Dev MORA verifikovati):** `category.subcategories` je pretpostavljeni `related_name` na `Subcategory.category` FK. Story 2-11 view koristi `category.subcategories.filter(parent=None)` (live `apps/brands/views.py:168-170`) — pa je related_name potvrđeno `subcategories`. Dev koristi isti pristup (NE re-verifikovati u models.py — Story 2-11 ga već koristi u produkciji).
- **Then**:
  - Query budget: **2 SQL upita** (Brand fetch + Subcategory list — HZM NE query-uje Product/prefetch pa nema N+1 rizik); lock-uje se posle `assertNumQueries` GREEN runa (mirror Story 2-10 SM-D empirical-lock)
  - Context: `brand` (HZM Brand instance) + `subcategories` (list[Subcategory] — 4 dece, ordered display_order)
  - Ako `brand.is_coming_soon == True` → `get_template_names()` vraća `brand_coming_soon.html`; `subcategories` NIJE fetch-ovan
  - Ako HZM brand ne postoji u DB → `get_object()` raise Http404 „HZM brand nije konfigurisan u sistemu."
  - Ako HZM `radne-masine` Category ne postoji → `subcategories = []` (empty state render umesto crash — defensive guard, mirror Story 2-10 empty handling)
- **And** view koristi cross-boundary `from apps.products.models import ...` SAMO ako treba (HZM NE query-uje Product — pa NEMA Product upita u HZM view-u; import već postoji u modulu iz Story 2-6, ali HZM view ga ne koristi)

**AC3 — `TulipMixPrikoliceView` (CBV `DetailView`): hardcoded Tulip brand lookup (slug="tulip") + Http404 guard; coming-soon branching; `get_context_data()` dodaje `products` (Tulip Product-i + prefetch specifications), `testimonials` (Tulip ProductTestimonial), `spec_rows` (transponovani dimenzioni tabela context — SM-D7)**

- **Given** AC1; Brand + Product + ProductSpecification + ProductTestimonial modeli; Tulip Brand + 2 Tulip Product (+ specifikacije) seed-ovani (0004); cross-boundary brands→products READ-ONLY per SM-D16 (Exception, mirror Story 2-11 SubcategoryListView)
- **When** dodajem `TulipMixPrikoliceView` u `apps/brands/views.py` POSLE `HzmRadneMasineView`. Source skeleton:
  ```python
  class TulipMixPrikoliceView(DetailView):
      """Tulip MIX Prikolice landing strana — Story 2.12.

      Statička model-showcase strana: 2 Product modela (6 m³ + 8 m³) + uporedna
      dimenziona tabela + 'Zadovoljni kupci' testimonials slider + katalog CTA.
      Cross-boundary brands→products READ-ONLY (SM-D16, mirror Story 2-11). View
      NE WRITE-uje na Product.
      """

      model = Brand
      context_object_name = "brand"

      def get_object(self, queryset=None):
          if queryset is None:
              queryset = self.get_queryset()
          try:
              return queryset.get(slug=_TULIP_BRAND_SLUG)
          except Brand.DoesNotExist as exc:
              raise Http404(_("Tulip brand nije konfigurisan u sistemu.")) from exc

      def get_template_names(self):
          if getattr(self, "object", None) is not None and self.object.is_coming_soon:
              return ["brands/brand_coming_soon.html"]
          return ["brands/tulip_mix_prikolice.html"]

      def get_context_data(self, **kwargs):
          ctx = super().get_context_data(**kwargs)
          if self.object.is_coming_soon:
              return ctx
          products = list(
              Product.objects.filter(
                  brand=self.object,
                  is_published=True,
              )
              .prefetch_related(
                  # KRITIČNO (prefetch defeat fix iter 1): plain
                  # prefetch_related("specifications") bi bio POBIJEN per-product
                  # .order_by() u _build_spec_rows (Django re-issue query po
                  # proizvodu → N+1). Prefetch sa ORDERED queryset-om koji
                  # MATCHUJE sort u _build_spec_rows znači da je per-product
                  # .all() poslužen iz prefetch cache-a (NE novi upit). Vidi SM-D14.
                  Prefetch(
                      "specifications",
                      queryset=ProductSpecification.objects.order_by("order", "id"),
                  )
              )
              .order_by("price_eur", "name")
          )
          ctx["products"] = products
          ctx["spec_rows"] = self._build_spec_rows(products)
          ctx["testimonials"] = list(
              ProductTestimonial.objects.filter(
                  product__brand=self.object,
                  product__is_published=True,
              )
              .select_related("product")
              .order_by("order", "-created_at")[:10]
          )
          return ctx

      @staticmethod
      def _build_spec_rows(products):
          # SM-D7: transponuj per-product specifications u uporedne redove.
          # Svaki red: {"key": <spec key>, "values": [v_model1, v_model2, ...]}.
          # Zadržava redosled prvog pojavljivanja key-a (order, id sort iz modela).
          # Ako model nema vrednost za key → prazna ćelija ("—" u template-u).
          if not products:
              return []
          key_order = []
          per_product = []
          for product in products:
              spec_map = {}
              # KRITIČNO (SM-D14): koristi .all() BEZ .order_by() — redosled je
              # već primenjen kroz Prefetch(queryset=...order_by("order","id"))
              # u get_context_data, pa .all() vraća prefetch cache (NE novi upit).
              # Dodavanje .order_by() ovde bi POBILO prefetch i vratilo N+1.
              for spec in product.specifications.all():
                  if spec.key not in spec_map:
                      spec_map[spec.key] = spec.value
                  if spec.key not in key_order:
                      key_order.append(spec.key)
              per_product.append(spec_map)
          rows = []
          for key in key_order:
              rows.append(
                  {"key": key, "values": [pp.get(key) for pp in per_product]}
              )
          return rows
  ```
- **Then**:
  - Context: `brand` (Tulip) + `products` (2 Product, ordered price_eur) + `spec_rows` (list dict-ova za uporednu tabelu) + `testimonials` (list ProductTestimonial, max 10)
  - `spec_rows` MORA biti transponovan: svaki red = jedna specifikacija (key) sa listom vrednosti po modelu (mirror DESIGN.md ključ-vrednost tabela — SM-D7)
  - Query budget: **lock-uje se TEK POSLE verifikacije da prefetch NIJE pobijen** (Brand + Product + prefetch specifications kroz `Prefetch(queryset=...order_by)` + ProductTestimonial select_related ≈ 4 upita; broj MORA biti KONSTANTAN bez obzira na broj proizvoda/specifikacija). **OBAVEZNO:** verifikuj kroz `assertNumQueries` test (Subtask 8.3) — ako broj upita raste sa brojem proizvoda → prefetch je pobijen (per-product `.order_by()` greška, SM-D14) i budget se NE sme zaključati dok se ne popravi. Brojevi su orijentir DOK assertNumQueries empirijski ne potvrdi konstantnost
  - Coming-soon i Http404 ponašanje mirror AC2 (sa „Tulip" porukom)
  - Empty stanja poštovana: 0 products → `_tulip_model_showcase.html` empty state; <2 products ili 0 spec_rows → dimenziona tabela SE NE renderuje (`{% if spec_rows %}` guard); 0 testimonials → „Zadovoljni kupci" sekcija SE NE renderuje (`{% if testimonials %}` guard)
- **And** view NE WRITE-uje na Product / ProductSpecification / ProductTestimonial (READ-ONLY cross-boundary — project-context.md § Cross-boundary import Exception, SM-D16, mirror Story 2-11)

**AC4 — `HzmRadneMasineView` template + partials: hero (variant="green") → 4-card subcategory showcase (REUSE coric-category-card; CTA href = subcategory.get_absolute_url()) → opciono catalog CTA; JEDAN h1; single main; semantic HTML5; mirror Story 2-10 Jeegee strukturu**

- **Given** AC2; Story 1-7 partials (hero_overlay_card, section_eyebrow, wave_divider); Story 2-10 `category-showcase.css` (coric-category-card REUSE); Story 2-11 `Subcategory.get_absolute_url()` (live `apps/brands/models.py:411-417` — vodi na `subcategory_listing_l{depth}`)
- **When** kreiram `templates/brands/hzm_radne_masine.html` + `_hzm_hero.html` + `_hzm_subcategory_showcase.html`
- **Then** `hzm_radne_masine.html` MORA imati strukturu (mirror `jeegee_prikljucna.html`):
  ```django
  {% extends "base.html" %}
  {% load i18n static media_tags %}

  {% block title %}{{ brand.name }} {% translate "Radne mašine" %} | {% translate "Ćorić Agrar" %}{% endblock %}

  {% block meta_description %}{% blocktranslate with brand=brand.name %}Pregled HZM radnih mašina po kategorijama — mini utovarivači, utovarivači bez teleskopa, teleskopski utovarivači, telehendleri.{% endblocktranslate %}{% endblock %}

  {% block content %}
  <section class="coric-brand-detail coric-hzm-radne-masine"
           data-testid="hzm-radne-masine-page"
           aria-label="{% blocktranslate with brand=brand.name %}{{ brand }} radne mašine{% endblocktranslate %}">

    <section id="hzm-hero"
             aria-label="{% blocktranslate with brand=brand.name %}{{ brand }} hero{% endblocktranslate %}"
             class="coric-hzm-radne-masine__hero-section">
      {% include "brands/partials/_hzm_hero.html" %}
    </section>

    <section id="hzm-subcategories"
             aria-labelledby="hzm-subcategories-title"
             class="coric-hzm-radne-masine__subcategories-section">
      {% include "brands/partials/_hzm_subcategory_showcase.html" %}
    </section>

    {% if brand.catalog_pdf %}
      <section id="hzm-catalog-cta"
               aria-labelledby="hzm-catalog-cta-title"
               class="coric-hzm-radne-masine__catalog-cta-section">
        {% include "partials/wave_divider.html" with position="top" %}
        <div class="coric-catalog-cta-banner">
          <h2 id="hzm-catalog-cta-title" class="coric-catalog-cta-banner__title">
            {% blocktranslate with brand=brand.name %}Preuzmi {{ brand }} katalog{% endblocktranslate %}
          </h2>
          <a href="{{ brand.catalog_pdf.url }}" target="_blank" rel="noopener noreferrer" download
             class="coric-button coric-button--primary" data-testid="hzm-catalog-download">
            {% translate "Preuzmi katalog" %}
          </a>
        </div>
      </section>
    {% endif %}

  </section>
  {% endblock %}
  ```
- **And** `_hzm_subcategory_showcase.html` MORA (REUSE 2-10 markup, RAZLIKA = Subcategory href):
  ```django
  {% load i18n %}

  {% include "partials/section_eyebrow.html" with text=_("KATEGORIJE RADNIH MAŠINA") tag="div" %}

  <h2 id="hzm-subcategories-title" class="coric-category-showcase__title">
    {% translate "Pregled po kategorijama" %}
  </h2>

  <div class="coric-category-showcase" data-testid="hzm-subcategory-showcase-grid">
    {% for sub in subcategories %}
      <article class="coric-category-card"
               aria-labelledby="sub-card-{{ sub.slug }}-title"
               data-testid="hzm-subcategory-card-{{ sub.slug }}">
        {% if sub.icon %}
          <div class="coric-category-card__icon" aria-hidden="true"><i class="{{ sub.icon }}"></i></div>
        {% endif %}
        <h3 id="sub-card-{{ sub.slug }}-title" class="coric-category-card__title">{{ sub.name }}</h3>
        {% if sub.description %}
          <p class="coric-category-card__description">{{ sub.description|truncatewords:25 }}</p>
        {% endif %}
        <a href="{{ sub.get_absolute_url }}"
           class="coric-button coric-button--primary coric-category-card__cta"
           aria-label="{% blocktranslate with category=sub.name %}Pogledaj kategoriju: {{ category }}{% endblocktranslate %}"
           data-testid="hzm-subcategory-cta-{{ sub.slug }}">
          {% translate "POGLEDAJ KATEGORIJU" %}
        </a>
      </article>
    {% empty %}
      <p class="coric-empty-state">{% translate "Kategorije radnih mašina su u pripremi." %}</p>
    {% endfor %}
  </div>
  ```
  - **KRITIČNO (SM-D4):** CTA href koristi `{{ sub.get_absolute_url }}` (Subcategory metoda — Story 2-11 implementirana) NE `{% url 'brands:subcategory_listing_category' %}`. Subcategory na nivou 1 (parent=None, depth=1) → `get_absolute_url()` vraća `/<lang>/mehanizacija/prikljucna/<category-slug>/<sub-slug>/`... **ČEKAJ — vidi SM-D4 + OQ-1:** HZM Subcategory pripada `radne-masine` Category-ji, ali Story 2-11 URL prostor je `mehanizacija/prikljucna/<category>/...`. `Subcategory.get_absolute_url()` (live linija 411-417) gradi URL kroz `reverse("brands:subcategory_listing_l{depth}", ...)` koji je HARDCODED na `prikljucna` prefix. **OQ-1 (Open Question — Dev/SM mora rešiti pre GREEN):** da li HZM `radne-masine` deca ispravno rezolvuju kroz `subcategory_listing_l1` (`/mehanizacija/prikljucna/radne-masine/<sub-slug>/`)? Story 2-11 `SubcategoryListView` fetch-uje Category po `category_slug` sa `is_for=MEHANIZACIJA` filter-om — `radne-masine` JE MEHANIZACIJA scope, pa rezolucija RADI bez izmene (URL kaže „prikljucna" ali view ne hardcoduje category="prikljucna" — `prikljucna` je samo statički path segment, a `<category_slug>` hvata `radne-masine`). **Lock (SM-D4):** HZM kartice koriste `sub.get_absolute_url()` koje vodi na `/sr/mehanizacija/prikljucna/radne-masine/<sub-slug>/` i Story 2-11 view ga ispravno renderuje (Category `radne-masine` + Subcategory chain). Semantički URL je „prikljucna" generički prefiks za sav mehanizacija drill-down (NIJE samo Jeegee). Ako je ovo neprihvatljivo SEO-wise, alternativa je dedicated `radne-masine/<sub>/` URL prostor — ODBAČENO za v1 (dupliranje Story 2-11 view-a + URL pattern-a; net negative). **URL putanja (`prikljucna` prefiks) je odvojeno pitanje od VIDLJIVOG breadcrumb labela — vidi SM-D13 + OQ-1 ispod za breadcrumb defekt koji se MORA popraviti u ovoj story.** SEO rasprava o URL putanji ostaje deferred to Story 6-6.
- **And** `_hzm_hero.html` MORA (mirror `_jeegee_hero.html`, RAZLIKA = variant="green"):
  ```django
  {% load i18n %}
  <div class="coric-brand-hero" data-testid="hzm-hero">
    {% if brand.logo %}
      {% include "partials/hero_overlay_card.html" with title=brand.name brand_logo=brand.logo.url brand_logo_alt=brand.name variant="green" bullets="" %}
    {% else %}
      {% include "partials/hero_overlay_card.html" with title=brand.name brand_logo="" brand_logo_alt=brand.name variant="green" bullets="" %}
    {% endif %}
  </div>
  ```
  - **KRITIČNO (SM-D9):** `variant="green"` jer CSS NEMA `coric-repeating-element--hzm` klasu (live `repeating-element.css` ima samo `--green` + `--jeegee`). NE koristiti `variant="hzm"` (unstyled watermark). Brand-specifične variant-e su Story 9-10 polish scope.
- **And** template MORA: `{% extends "base.html" %}`; `{% block title %}` + `{% block meta_description %}`; TAČNO 1 `<h1>` (iz hero_overlay_card); single `<main>` (iz base.html — outer je `<section>`); outer `<section>` koristi `aria-label` (NE `aria-labelledby` — h1 u hero_overlay_card nema id, mirror Story 2-10 SM-D8); NEMA inline `style`; NEMA hardcoded srpski string; NEMA ćirilice; heading hijerarhija h1 → h2 → h3

**AC5 — `TulipMixPrikoliceView` template + partials: hero → 2-model showcase (coric-product-card REUSE) → uporedna dimenziona tabela (DESIGN.md ključ-vrednost layout) → „Zadovoljni kupci" testimonials (REUSE _testimonials_slider.html) → opciono catalog CTA; empty stanja poštovana; JEDAN h1; single main**

- **Given** AC3; Story 2-8 `coric-product-card` BEM (tractor-listing.css REUSE); Story 2-7 `templates/partials/_testimonials_slider.html` (live — prima `testimonials` + `slider_id` kwarg, linija 2); Story 2-3 `{% responsive_picture %}`; DESIGN.md § Components „tabela ključ-vrednost" (linija 324) + „Card Base" (linija 311)
- **When** kreiram `tulip_mix_prikolice.html` + `_tulip_hero.html` + `_tulip_model_showcase.html` + `_tulip_comparison_table.html`
- **Then** `tulip_mix_prikolice.html` MORA imati sekcije TAČNIM redosledom:
  ```django
  {% extends "base.html" %}
  {% load i18n static media_tags %}

  {% block title %}{{ brand.name }} {% translate "MIX prikolice" %} | {% translate "Ćorić Agrar" %}{% endblock %}
  {% block meta_description %}{% blocktranslate with brand=brand.name %}Tulip MIX prikolice — pregled modela sa uporednim dimenzijama i iskustvima korisnika.{% endblocktranslate %}{% endblock %}

  {% block content %}
  <section class="coric-brand-detail coric-tulip-mix"
           data-testid="tulip-mix-page"
           aria-label="{% blocktranslate with brand=brand.name %}{{ brand }} MIX prikolice{% endblocktranslate %}">

    <section id="tulip-hero" aria-label="..." class="coric-tulip-mix__hero-section">
      {% include "brands/partials/_tulip_hero.html" %}
    </section>

    <section id="tulip-models" aria-labelledby="tulip-models-title" class="coric-tulip-mix__models-section">
      {% include "brands/partials/_tulip_model_showcase.html" %}
    </section>

    {% if spec_rows %}
      <section id="tulip-comparison" aria-labelledby="tulip-comparison-title" class="coric-tulip-mix__comparison-section">
        {% include "brands/partials/_tulip_comparison_table.html" %}
      </section>
    {% endif %}

    {% if testimonials %}
      <section id="tulip-testimonials" aria-labelledby="tulip-testimonials-title" class="coric-tulip-mix__testimonials-section">
        {% include "partials/_testimonials_slider.html" with slider_id="tulip-testimonials-title" %}
      </section>
    {% endif %}

    {% if brand.catalog_pdf %}
      <section id="tulip-catalog-cta" aria-labelledby="tulip-catalog-cta-title" class="coric-tulip-mix__catalog-cta-section">
        {% include "partials/wave_divider.html" with position="top" %}
        <div class="coric-catalog-cta-banner">
          <h2 id="tulip-catalog-cta-title" class="coric-catalog-cta-banner__title">
            {% blocktranslate with brand=brand.name %}Preuzmi {{ brand }} katalog{% endblocktranslate %}
          </h2>
          <a href="{{ brand.catalog_pdf.url }}" target="_blank" rel="noopener noreferrer" download
             class="coric-button coric-button--primary" data-testid="tulip-catalog-download">
            {% translate "Preuzmi katalog" %}
          </a>
        </div>
      </section>
    {% endif %}

  </section>
  {% endblock %}
  ```
- **And** `_tulip_model_showcase.html` MORA renderovati per-product `coric-product-card` (REUSE Story 2-8 BEM):
  - `{% include "partials/section_eyebrow.html" with text=_("MODELI PRIKOLICA") tag="div" %}`
  - `<h2 id="tulip-models-title">` (referenciran `aria-labelledby`)
  - `<div class="coric-category-showcase">` grid wrapper (REUSE grid layout) iterira `products`
  - Per-product `<article class="coric-product-card" data-testid="tulip-model-card-{{ product.slug }}">`: `{% responsive_picture product.main_image alt=product.name sizes="(max-width: 768px) 100vw, 50vw" loading="lazy" %}` (guard `{% if product.main_image %}`) + `<h3>{{ product.name }}</h3>` + `key_features` lista (`{% for f in product.key_features %}`) + `<a href="{{ product.get_absolute_url }}" class="coric-button coric-button--primary">{% translate "OPŠIRNIJE" %}</a>` sa deskriptivnim `aria-label`
  - `{% empty %}` clause „Modeli prikolica su u pripremi."
- **And** `_tulip_comparison_table.html` MORA (DESIGN.md ključ-vrednost token layout, side-by-side):
  ```django
  {% load i18n %}

  {% include "partials/section_eyebrow.html" with text=_("UPOREDNE DIMENZIJE") tag="div" %}

  <h2 id="tulip-comparison-title" class="coric-comparison-table__heading">
    {% translate "Uporedne dimenzije" %}
  </h2>

  <div class="coric-comparison-table__scroll">
    <table class="coric-comparison-table" data-testid="tulip-comparison-table">
      <caption class="visually-hidden">{% translate "Uporedne dimenzije Tulip MIX prikolica" %}</caption>
      <thead>
        <tr>
          <th scope="col" class="coric-comparison-table__corner">{% translate "Specifikacija" %}</th>
          {% for product in products %}
            <th scope="col" class="coric-comparison-table__model">{{ product.name }}</th>
          {% endfor %}
        </tr>
      </thead>
      <tbody>
        {% for row in spec_rows %}
          <tr class="coric-comparison-table__row">
            <th scope="row" class="coric-comparison-table__key">{{ row.key }}</th>
            {% for value in row.values %}
              <td class="coric-comparison-table__value">{{ value|default:"—" }}</td>
            {% endfor %}
          </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
  ```
  - Tabela koristi `<th scope="col">` za model header + `<th scope="row">` za ključ ćeliju (a11y — WCAG 1.3.1 table header association)
  - `<caption class="visually-hidden">` za screen reader kontekst
  - Prazna vrednost → `—` (em-dash) kroz `|default`
- **And** `_tulip_hero.html` mirror `_hzm_hero.html` sa `variant="green"` (SM-D9), `data-testid="tulip-hero"`
- **And** template MORA: TAČNO 1 `<h1>` (iz hero_overlay_card); single `<main>`; outer `<section>` `aria-label`; testimonials sekcija renderuje SAMO ako `testimonials` nije prazno; comparison tabela SAMO ako `spec_rows` nije prazno (≥2 modela sa specifikacijama); NEMA inline style; NEMA hardcoded srpski; NEMA ćirilice
- **And** REUSE `_testimonials_slider.html` prima `slider_id="tulip-testimonials-title"` kwarg (live partial linija 2 — `{% with slider_id=slider_id|default:"testimonials-title" %}`); h2 id="tulip-testimonials-title" je generisan UNUTAR partial-a (linija 3: `<h2 id="{{ slider_id }}" class="visually-hidden">`), pa `aria-labelledby="tulip-testimonials-title"` na outer section ispravno referencira (SM-D10 — verifikovati da slider_id matchuje aria-labelledby)

**AC6 — `comparison-table.css` definiše `coric-comparison-table` BEM (header red, ključ ćelija, vrednost ćelija, zebra redovi, responsive horizontal scroll); sve vrednosti kroz `var(--token)`; `main.css` +1 @import; HZM grid REUSE category-showcase.css (NEMA novog import-a); Tulip model-kartice REUSE `brand-listing.css` coric-product-card (DEFINISAN linija 72; NE tractor-listing.css)**

- **Given** AC5; Story 1-5 tokens.css (`--color-brand-green-800`, `--color-neutral-white`, `--color-neutral-cream`, `--color-neutral-gray-700`, `--spacing-scale-*`, `--rounded-md`, `--typography-scale-*`); Story 2-10 `category-showcase.css` (REUSE); `brand-listing.css` (`.coric-product-card` DEFINISAN linija 72 — REUSE; NE tractor-listing.css koji ga samo referencira u komentaru)
- **When** kreiram `static/css/components/comparison-table.css`
- **Then** CSS MORA sadržati selektore (svi `coric-` prefix; sve vrednosti `var(--token)`):
  - `.coric-comparison-table__heading` — h2 (centriran, green-800, h2 size, margin-bottom scale-5)
  - `.coric-comparison-table__scroll` — wrapper sa `overflow-x: auto` (horizontal scroll na mobile-u) + `-webkit-overflow-scrolling: touch`
  - `.coric-comparison-table` — `width: 100%; border-collapse: collapse;`
  - `.coric-comparison-table__corner` + `.coric-comparison-table__model` — `<th>` header ćelije (green-800 bg, white text, padding scale-3, text-align)
  - `.coric-comparison-table__key` — `<th scope="row">` ključ (bold, green-800 text, left-align, padding)
  - `.coric-comparison-table__value` — `<td>` vrednost (gray-700 text, padding, center-align)
  - `.coric-comparison-table__row:nth-child(even)` — zebra background (`var(--color-neutral-cream)` ili gray-50)
  - **NAPOMENA — token verifikacija:** Dev MORA verifikovati svaki `var(--token)` postoji u `static/css/tokens.css` PRE commit-a (mirror Story 2-10 IMP-6 token verifikacija); ako neki token nedostaje (npr. `--spacing-section`), koristi postojeći ekvivalent ili dokumentuj u Completion Notes (NE dodavati nove tokene u ovoj story — tokens.css je Story 1-5 deliverable)
- **And** `static/css/main.css` MORA dobiti TAČNO 1 nova linija (mirror Story 2-9/2-10/2-11 sintaksu — `url(...)` wrap + `./` + `;`):
  ```css
  @import url('./components/comparison-table.css');
  ```
  POSLE postojeće `@import url('./components/breadcrumb.css');` (Story 2-11 zadnja)
- **And** Edit `main.css` MORA biti **targeted Edit** koji ZADRŽAVA sve postojeće linije
- **And** HZM 4-card grid NE dobija novi CSS — REUSE `category-showcase.css` (`coric-category-showcase` + `coric-category-card`); responzivni `repeat(auto-fit, minmax(280px, 1fr))` automatski renderuje 4 kartice
- **And** Tulip model-kartice NE dobijaju novi CSS — REUSE `coric-product-card` BEM koji je DEFINISAN u `static/css/components/brand-listing.css:72` (verifikovano live; NE u `tractor-listing.css` koji ga samo referencira u komentaru linija 6). Dev MORA verifikovati klasa postoji live u `brand-listing.css` (mirror Story 2-11 SM-D koja REUSE-uje coric-product-card)
- **And** SVI BEM klasi imaju `coric-` prefix; nijedan magic hex/px/em (sve tokeni); **NEMA CDN referenci**

**AC7 — Data migracija `0004_seed_hzm_tulip_brands.py` seed-uje HZM Brand + HZM `radne-masine` Category + 4 Subcategory dece + Tulip Brand + 2 Tulip Product + ProductSpecification redovi (idempotentna `get_or_create`); reverse callable DELETE-uje TAČNO te instance po slug-u; depends_on poslednja brands migracija**

- **Given** AC1-AC5 (svi koriste seed podatke); Story 2-1 (Brand, Category, Subcategory) + Story 2-2 (Product, ProductSpecification) modeli; live poslednja brands migracija je `0003_seed_jeegee_and_prikljucna_categories` (verifikovano); cross-app Product seed kroz `apps.get_model("products", "Product")` (NE direct import)
- **When** kreiram `apps/brands/migrations/0004_seed_hzm_tulip_brands.py`
- **Then** migracija MORA:
  - `dependencies = [("brands", "0003_seed_jeegee_and_prikljucna_categories"), ("products", "<poslednja products migracija>")]` — **KRITIČNO (SM-D8):** Product seed zahteva `products` app migracija dependency (cross-app data migracija MORA depend-ovati na obe app migracije da historical modeli postoje). Dev MORA verifikovati poslednju `products` migraciju (`uv run python manage.py showmigrations products` ili `apps/products/migrations/` listing) i lock-ovati u dependencies
  - Seed HZM Brand (`get_or_create(slug="hzm", defaults={name="HZM", is_coming_soon=False, brand_color="", description="", slogan="", statistics=[]})`)
  - Seed HZM Category (`get_or_create(slug="radne-masine", defaults={name="Radne mašine", is_for="mehanizacija", display_order=40, description="Utovarivači i telehendleri za sve poljoprivredne i industrijske potrebe.", icon=""})`)
  - Seed 4 Subcategory dece (svi `category=radne-masine` Category, `parent=None`):
    - `mini-utovarivaci` / „Mini utovarivači" / display_order=10
    - `utovarivaci-bez-teleskopa` / „Utovarivači bez teleskopa" / display_order=20
    - `teleskopski-utovarivaci` / „Teleskopski utovarivači" / display_order=30
    - `telehendleri` / „Telehendleri" / display_order=40
  - Seed Tulip Brand (`get_or_create(slug="tulip", defaults={name="Tulip", ...})`)
  - Seed 2 Tulip Product (`get_or_create(slug="tulip-mix-6m3", defaults={brand=tulip, name="Tulip MIX 6 m³", is_published=True, status="published", price_eur=Decimal("6500.00"), description="...", key_features=["Zapremina 6 m³", "Robusna konstrukcija", "Pocinkovano kućište"]})` — TAČNO 3 stavke (cap ≤ 3, vidi napomenu ispod) + analogno `tulip-mix-8m3` / „Tulip MIX 8 m³" / 8 m³ / `price_eur=Decimal("8200.00")` / `key_features=["Zapremina 8 m³", "Robusna konstrukcija", "Pocinkovano kućište"]`)
    - **KRITIČNO (price ordering — fix iter 1):** `TulipMixPrikoliceView` sortira `order_by("price_eur", "name")` (AC3). `price_eur` je NULLABLE (live `apps/products/models.py:141-147`). Seed MORA postaviti EKSPLICITNU `price_eur` za oba modela sa **6 m³ < 8 m³** (npr. 6500.00 < 8200.00) tako da je PRIMARNI sort ključ deterministički PO NAMERI — NE oslanjati se na string fallback `"Tulip MIX 6 m³" < "Tulip MIX 8 m³"`. Vrednosti su DEMO/placeholder (vidi AC7 napomenu o demo podacima ispod), ali relativni redosled (6m³ jeftiniji od 8m³) je namerni invariant koji test `test_tulip_products_ordered_by_price` zaključava. Koristi `from decimal import Decimal` u migraciji.
  - Seed ProductSpecification redovi za uporednu tabelu (za oba modela, isti `key` set da side-by-side ima poravnate redove):
    - „Zapremina" → „6 m³" / „8 m³"
    - „Dužina" → DEMO „4035 mm" / „4500 mm"
    - „Širina" → DEMO „2100 mm" / „2300 mm"
    - „Nosivost" → DEMO „6000 kg" / „8000 kg"
    - (svi `section="ostalo"`, `order` redom 0,1,2,3 da tabela ima konzistentan redosled)
    - **⚠️ DEMO/PLACEHOLDER PODACI (fabricated dims fix iter 1 — OQ-4):** vrednosti Dužina/Širina/Nosivost (i `price_eur`) su **DEMO placeholder-i za smoke-test prikaz**, NISU verifikovane realne tehničke specifikacije Tulip MIX prikolica. Renderuju se u PUBLIC uporednoj tabeli pa izgledaju kao realni podaci. **Dev MORA:** (1) dodati komentar u migraciji `# DEMO/PLACEHOLDER — realne dimenzije čekaju biznis potvrdu (Mihas), vidi OQ-4` iznad spec seed bloka; (2) zabeležiti u `Completion Notes` da su dimenzije demo i da PRE produkcije zahtevaju potvrdu od Mihas-a/biznisa. „Zapremina" (6/8 m³) je jedina pouzdana vrednost (iz naziva modela). NE shipovati fabrikovane tehničke podatke tiho u produkciju — vidi OQ-4.
  - Koristi `apps.get_model()` (NE direct import) — historical models snapshot
  - **KRITIČNO (key_features cap fix iter 1):** `Product.key_features` je CAP-ovan na **MAKSIMALNO 3 stavke** (live `apps/products/models.py:238-240`, `_PRODUCT_KEY_FEATURES_MAX=3` → `ValidationError("Najviše 3 ključne karakteristike.")`). Seed `key_features` za oba Tulip modela MORA imati **≤ 3 stringa** — inače `full_clean()` (poziva se kroz `Product.save()`/`get_or_create` path) raise-uje ValidationError i migracija pada. Primer validnog seed-a: `key_features=["Zapremina 6 m³", "Robusna konstrukcija", "Pocinkovano kućište"]` (TAČNO 3). NE prelaziti 3.
  - `get_or_create()` za idempotentnost (re-run NE baca IntegrityError)
  - `reverse_code=reverse_seed` koji DELETE-uje: Tulip ProductSpecification (kroz product__slug), 2 Tulip Product, Tulip Brand, 4 HZM Subcategory, HZM Category, HZM Brand (redosled poštuje FK constraint — specs pre products, subcategories pre category, products/categories pre brands)
- **And** **NAPOMENA (SM-D8 — FK order u reverse; rationale ispravljen iter 1):** Tačni `on_delete` (verifikovano live): `Subcategory.category` = **CASCADE** (`apps/brands/models.py:321`), `Subcategory.parent` = CASCADE; `Product.brand` = **PROTECT** (`apps/products/models.py:100`); `ProductSpecification.product` (verifikovati live — tipično CASCADE). Reverse redosled je FK-safe bez obzira na CASCADE/PROTECT, ali se zadržava EKSPLICITAN dependent-pre-parent redosled radi determinizma (kod PROTECT FK-a kao `Product.brand` to je OBAVEZNO — brisanje Brand-a pre Product-a bi raise IntegrityError; kod CASCADE FK-a kao `Subcategory.category` nije strogo nužno, ali eksplicitno brisanje je čistije i ne oslanja se na cascade side-effect). Ispravan reverse redosled (NEPROMENJEN): ProductSpecification → Product → (Tulip Brand) → Subcategory → Category → (HZM Brand)
- **And** **NEMA modeltranslation hu/en** prevoda za name polja (v1 sr fallback — Story 8-5 admin populacija; mirror Story 2-10 SM-D)
- **And** smoke verifikacija:
  ```bash
  uv run python manage.py migrate brands
  uv run python manage.py shell -c "from apps.brands.models import Brand, Category, Subcategory; \
    from apps.products.models import Product, ProductSpecification; \
    print(Brand.objects.filter(slug__in=['hzm','tulip']).count()); \
    print(Subcategory.objects.filter(category__slug='radne-masine').count()); \
    print(Product.objects.filter(brand__slug='tulip').count()); \
    print(ProductSpecification.objects.filter(product__brand__slug='tulip').count())"
  ```
  Očekivan output: `2`, `4`, `2`, `8` (4 spec × 2 modela)
- **And** reverse smoke (manuelna): `migrate brands 0003` → verifikuje sve obrisano; re-apply `migrate brands`

**AC8 — i18n + a11y + WCAG 2.1 AA: sve user-facing string kroz `{% translate %}`/`gettext_lazy`; .po fajlovi (sr/hu/en) popunjeni; single h1; single main na obe strane; ARIA landmarks; tabela header association (scope); color contrast ≥ 4.5:1; `<html lang>` automatski**

- **Given** AC4 + AC5 + AC6 završeni; Story 1-4 i18n; Story 1-5 tokens (contrast validated); project-context.md § A11y must-haves + § Critical Don't-Miss Rules
- **When** Dev kompletira template-e i CSS; pokreće `just messages`
- **Then**:
  - SVI user-facing string kroz `{% translate %}` / `{% blocktranslate %}` (NIJEDAN hardcoded srpski)
  - `locale/sr/LC_MESSAGES/django.po` MORA imati popunjene msgstr za nove msgid (među ostalim): „Radne mašine", „MIX prikolice", „KATEGORIJE RADNIH MAŠINA", „MODELI PRIKOLICA", „UPOREDNE DIMENZIJE", „Pregled po kategorijama", „Uporedne dimenzije", „Uporedne dimenzije Tulip MIX prikolica" (caption), „Specifikacija", „POGLEDAJ KATEGORIJU", „OPŠIRNIJE", „Preuzmi katalog", „Preuzmi {{ brand }} katalog" (blocktranslate), „Pogledaj kategoriju: {{ category }}" (blocktranslate aria), „Kategorije radnih mašina su u pripremi.", „Modeli prikolica su u pripremi.", „{{ brand }} radne mašine"/„{{ brand }} MIX prikolice"/„{{ brand }} hero" (aria-labeli), meta description-i, Http404 poruke („HZM brand nije konfigurisan u sistemu.", „Tulip brand nije konfigurisan u sistemu.")
  - `locale/hu/` + `locale/en/` popunjeni (Dev DeepL/manual; prazan msgstr → msgid fallback, flagged za Story 6-5)
  - `just messages` pokrenut (regeneriše .po); `just compilemessages` rebuild .mo
  - **NEMA ćirilice** (anti-pattern); **NEMA šišane latinice** (pune č/ć/ž/š/đ)
  - **IMP-2 — fallback marker OUT-OF-SCOPE:** v1 prikazuje sr `name` polja (Category/Subcategory/Product) na /hu/ /en/ BEZ UX-DR-22 marker-a (deferred Story 6-5); admin populacija prevoda Story 8-5
- **And** semantic HTML5 (obe strane):
  - TAČNO 1 `<h1>` po strani (kroz hero_overlay_card partial)
  - HZM h2: „Pregled po kategorijama" (+ opciono catalog CTA h2); h3: 4× subcategory naziv
  - Tulip h2: „Pregled po kategorijama"/„MODELI PRIKOLICA" wrapper, „Uporedne dimenzije", „Iz prve ruke" (testimonials partial — visually-hidden h2 sa slider_id), opciono catalog CTA h2; h3: 2× model naziv
  - Heading hijerarhija h1 → h2 → h3 (NEMA skok-ova)
  - **Single `<main>`** po strani (iz base.html — outer wrapper je `<section>`)
  - `<section>` sa `aria-label`/`aria-labelledby` na svakoj outer sekciji
  - `<article>` za svaku karticu (subcategory/model)
  - `<table>` sa `<caption>` + `scope="col"`/`scope="row"` (WCAG 1.3.1 — table header association za uporednu tabelu)
- **And** ARIA landmarks: outer `<section>` `aria-label` (NE `aria-labelledby` — h1 u hero_overlay_card nema id, SM-D8 lock mirror 2-10); inner sekcije `aria-labelledby` referenciraju lokalne h2 id-jeve; hero koristi `aria-label`
- **And** fokus indikator vidljiv (CTA dugmad `:focus-visible` iz pill-button.css; kartice `:focus-within`); testimonials slider keyboard kontrole (REUSE Story 2-7)
- **And** color contrast ≥ 4.5:1 (Story 1-5 tokens): green-800 na white 11.5:1; gray-700 na white 7.2:1; tabela header green-800 bg + white text 11.5:1 — sve pass
- **And** smoke verifikacija (Dev):
  ```bash
  uv run python manage.py makemessages -l sr -l hu -l en
  uv run python manage.py compilemessages -l sr -l hu -l en
  ```
  ```powershell
  Select-String -Pattern 'msgstr ""' -Path locale/sr/LC_MESSAGES/django.po | Select-Object -First 20
  ```

**AC9 — Manuelni Dev smoke check + Lighthouse a11y ≥ 95 na obe strane (mirror Story 2-10 AC9)**

- **Given** AC1-AC8 završeni; 0004 migracija primenjena; HZM/Tulip seed podaci u DB
- **When** Dev pokreće `just dev` i otvara obe strane u Chrome
- **Then** Dev verifikuje (HZM `/sr/mehanizacija/radne-masine/`):
  - Hero renderuje: HZM logo (stub kroz admin/shell ako treba) + naziv (h1) + Repeating Element watermark `coric-repeating-element--green` (DevTools: green-800 background, NE unstyled)
  - 4-card grid: desktop ≥768px → 3-4 kartice u redu (auto-fit), tablet → 2 kolone, mobile → 1 stack
  - Per-kartica: naziv potkategorije („Mini utovarivači" itd.) + opis + „POGLEDAJ KATEGORIJU" CTA
  - Klik na CTA → navigira na `/sr/mehanizacija/prikljucna/radne-masine/<sub-slug>/` koji **rezolvuje Story 2-11 SubcategoryListView** (NIJE 404 — OQ-1b lock; verifikovati da SubcategoryListView renderuje HZM subcategory chain ispravno). Ako 404 → OQ-1b nije rešen, vidi SM-D4 fallback
  - **Breadcrumb PUN TRAG — duplikat-free (SM-D13 / OQ-1a — MORA biti tačan; AŽURIRANO iter 2):** na HZM L1 drill-down strani (`/sr/mehanizacija/prikljucna/radne-masine/<sub-slug>/`) renderovani breadcrumb MORA da bude TAČNO **3 stavke u redosledu**: (1) „Početna" (link → `core:home`); (2) „Radne mašine" (link → `reverse("brands:hzm_radne_masine")`); (3) „<naziv subcategory-je>" (NON-link, aria-current/current). **NE SME postojati DRUGA „Radne mašine" stavka** (susedni duplikat koji self-linkuje na trenutnu stranu) — ako je trag „Početna → Radne mašine → Radne mašine → <sub>" (length 4), reconciliacija nije primenjena (defekt, blokira). Ako breadcrumb pokazuje „Priključna mehanizacija" iznad radnih mašina → root-parametrizacija nije primenjena (defekt, blokira). Tail (trenutna subcategory) MORA biti NON-link. **Regression:** Jeegee drill-down (`/sr/mehanizacija/prikljucna/<cat>/…`) i dalje pokazuje pun trag „Početna → Priključna mehanizacija → <category.name> → … → <leaf>" — root „Priključna mehanizacija" zadržan I `category.name` link stavka zadržana (Jeegee NEMA kolaps jer root-label ≠ category.name)
  - Hover na kartice: translateY(-4px) + shadow (REUSE category-showcase.css)
- **And** Dev verifikuje (Tulip `/sr/mehanizacija/mix-prikolice/`):
  - Hero renderuje: Tulip logo + naziv (h1) + green Repeating Element
  - 2-model showcase: 2 `coric-product-card` (slika + naziv + key_features + „OPŠIRNIJE" CTA → product detail)
  - Klik „OPŠIRNIJE" → navigira na `/sr/proizvod/tulip-mix-6m3/` (Story 2-7 ProductDetailView — verifikovati 200)
  - Uporedna dimenziona tabela: 2 model kolone + redovi (Zapremina/Dužina/Širina/Nosivost) sa vrednostima side-by-side; mobile <768px → horizontal scroll (NE overflow lom layout-a)
  - „Zadovoljni kupci" sekcija: renderuje SAMO ako Tulip Product-i imaju testimonijale (stub kroz shell za test); slider pause/play kontrole rade (REUSE Story 2-7)
  - Catalog CTA: renderuje SAMO ako `tulip.catalog_pdf` postoji (stub kroz admin)
- **And** empty/coming-soon/404 testovi (oba brenda, kroz shell — mirror Story 2-10 AC9):
  - HZM/Tulip `is_coming_soon=True` → `brand_coming_soon.html` render; reset
  - HZM/Tulip brand DELETE → Http404 sa kustomizovanom porukom; restore migracijom
  - Tulip 0 products → model-showcase empty state; comparison + testimonials sekcije SE NE renderuju
  - Tulip 1 product (ili 0 spec_rows) → comparison tabela SE NE renderuje (`{% if spec_rows %}` guard)
- **And** `prefers-reduced-motion: reduce` test (Chrome DevTools Rendering): hover na kartice ne triggeruje transform (category-showcase.css `@media` block); testimonials slider respektuje reduced-motion (REUSE Story 2-7 ponašanje)
- **And** Dev pokreće Lighthouse audit (CLI mode, OBE strane — mirror Story 2-10 § Lighthouse JSON artifact preservation):
  ```bash
  lighthouse http://localhost:8000/sr/mehanizacija/radne-masine/ --output=json \
    --output-path=_bmad-output/implementation-artifacts/2-12-hzm-lighthouse-YYYYMMDD.json \
    --only-categories=accessibility,performance,seo --form-factor=mobile --chrome-flags="--headless"
  lighthouse http://localhost:8000/sr/mehanizacija/mix-prikolice/ --output=json \
    --output-path=_bmad-output/implementation-artifacts/2-12-tulip-lighthouse-YYYYMMDD.json \
    --only-categories=accessibility,performance,seo --form-factor=mobile --chrome-flags="--headless"
  ```
  (`YYYYMMDD` literal placeholder — zameni datumom npr. `20260531`; PowerShell ne expand-uje `$(date)`)
  - **Accessibility ≥ 95** (obe strane; UX-DR-13 + NFR-2; Story 9-9 gate)
  - **Performance ≥ 80** (NEMA HTMX/range slider; Tulip ima testimonials JS ali lagano)
  - Dev MORA citirati skor-ove (obe strane) u `Dev Agent Record § Completion Notes` PRE Step-04 Code Review
- **Napomena:** AC je manuelni smoke check (Dev pre commit-a); automated E2E je Story 9-8; axe-core je Story 9-9

## Tasks / Subtasks

- [x] **Task 1: Data migracija 0004 — seed HZM + Tulip brendove, kategorije, modele, specifikacije (AC7)**
  - [x] Subtask 1.1: Verifikovati poslednju `brands` migraciju (live: `0003_seed_jeegee_and_prikljucna_categories`) + poslednju `products` migraciju (`uv run python manage.py showmigrations products`) za cross-app `dependencies` lock (SM-D8)
  - [x] Subtask 1.2: Kreirati `apps/brands/migrations/0004_seed_hzm_tulip_brands.py` per AC7: RunPython `get_or_create` (HZM Brand + Category + 4 Subcategory + Tulip Brand + 2 Product + 8 ProductSpecification); `reverse_code` sa FK-safe delete redosledom (specs → products → subcategories → category → brands)
  - [x] Subtask 1.3: Koristi `apps.get_model()` za sve modele (historical snapshot); cross-app `apps.get_model("products", "Product")` + `("products", "ProductSpecification")`
  - [x] Subtask 1.4: Smoke verifikacija — `migrate brands`; shell verifikuje counts (2 brenda, 4 subcat, 2 product, 8 spec)
  - [x] Subtask 1.5: Reverse smoke — `migrate brands 0003` rollback; verifikuje sve obrisano; re-apply

- [x] **Task 2: `apps/brands/views.py` ADD 2 view klase + `apps/brands/urls.py` ADD 2 path (AC1, AC2, AC3)**
  - [x] Subtask 2.1: ADD module-level konstante POSLE `_PRIKLJUCNA_CATEGORY_SLUGS`: `_HZM_BRAND_SLUG`, `_HZM_CATEGORY_SLUG`, `_TULIP_BRAND_SLUG`
  - [x] Subtask 2.2: ADD `HzmRadneMasineView(DetailView)` POSLE `SubcategoryListView` per AC2 skeleton (get_object Http404 guard, get_template_names coming-soon, get_context_data subcategories). Verifikovati `category.subcategories` related_name (Story 2-11 ga već koristi — SM-D6)
  - [x] Subtask 2.3: ADD `TulipMixPrikoliceView(DetailView)` POSLE `HzmRadneMasineView` per AC3 skeleton (get_object Http404, get_context_data products + spec_rows + testimonials, `_build_spec_rows` static metoda). Cross-boundary `Product`/`ProductSpecification`/`ProductTestimonial` već importovani (linija 21 — REUSE, NE re-import). **KRITIČNO (SM-D14): koristi `Prefetch("specifications", queryset=ProductSpecification.objects.order_by("order","id"))`** u get_context_data + `product.specifications.all()` BEZ `.order_by()` u `_build_spec_rows` (NE pobiti prefetch → N+1). `Prefetch` već importovan (`apps/brands/views.py:14` — REUSE)
  - [x] Subtask 2.4: `apps/brands/urls.py` ADD 2 path POSLE postojećih (`hzm_radne_masine`, `tulip_mix_prikolice`); EDIT view import liste
  - [x] Subtask 2.5: Smoke — `manage.py check` exit 0; reverse 4 URL-a (AC1 smoke)
  - [x] Subtask 2.6: **Parametrizuj `SubcategoryListView._build_breadcrumb` root + RECONCILE duplikat (SM-D13 / OQ-1a — user-facing breadcrumb fix, AC9; AŽURIRANO iter 2):** (a) zameni hardcode-ovanu drugu breadcrumb stavku (`_("Priključna mehanizacija")` + `reverse("brands:jeegee_prikljucna")`, live `apps/brands/views.py:244-248`) parametrizacijom kroz `_breadcrumb_root_for(category)` → `(item, is_category_landing)`; mapa `_CATEGORY_LANDING_BREADCRUMB_ROOT` sadrži SAMO kategorije sa sopstvenom landing stranom (`radne-masine`→„Radne mašine"/`hzm_radne_masine`); **DEFAULT (ne-mapirano, uklj. SVE Jeegee kategorije `osnovna-obrada-zemljista`/`priprema-zemljista`/`masine-za-setvu`) = postojeći generički „Priključna mehanizacija"/`jeegee_prikljucna` prefiks — NEPROMENJENO ponašanje** (NE `category.name` — verifikovano live: nijedna Jeegee kategorija nema slug „prikljucna"); (b) **u intermediate/leaf grani (live `apps/brands/views.py:258-264`) PRESKOČI dodavanje `category.name` stavke kada je root mapiran (`root_is_landing=True`)** — inače HZM dobija susedni duplikat „Radne mašine → Radne mašine" (drugi self-linkuje na trenutnu landing stranu). Label kroz `gettext` (dodaj „Radne mašine" msgid). NE menjaj reverse redosled preostalih stavki. **KANONSKI HZM L1 trag: TAČNO `["Početna", "Radne mašine"(link→hzm_radne_masine), "<sub naziv>"(non-link)]` — length 3, NEMA ponovljene „Radne mašine".** Regression: Jeegee `prikljucna` drill-down i dalje pokazuje root „Priključna mehanizacija" + zadržava `category.name` link stavku (reconciliacija NE kolabira Jeegee jer root-label ≠ category.name); postojeći Story 2-11 testovi MORAJU i dalje proći

- [x] **Task 3: HZM template-i (AC4)**
  - [x] Subtask 3.1: Kreirati `templates/brands/hzm_radne_masine.html` per AC4 skeleton (mirror jeegee_prikljucna.html: outer section + hero + showcase + opciono catalog CTA)
  - [x] Subtask 3.2: Kreirati `templates/brands/partials/_hzm_hero.html` (mirror _jeegee_hero.html, `variant="green"` SM-D9, defensive logo guard)
  - [x] Subtask 3.3: Kreirati `templates/brands/partials/_hzm_subcategory_showcase.html` per AC4 (REUSE coric-category-card; CTA href = `{{ sub.get_absolute_url }}` SM-D4; empty state)
  - [x] Subtask 3.4: Verifikovati TAČNO 1 h1 + single main + aria-label outer + NEMA hardcoded srpski + NEMA ćirilice
  - [x] Subtask 3.5: **OQ-1 verifikacija** — manuelno reload-uj HZM CTA target URL i potvrdi Story 2-11 SubcategoryListView renderuje (NIJE 404); ako 404, eskaliraj SM-D4 fallback

- [x] **Task 4: Tulip template-i (AC5)**
  - [x] Subtask 4.1: Kreirati `templates/brands/tulip_mix_prikolice.html` per AC5 skeleton (hero → models → conditional comparison → conditional testimonials → conditional catalog CTA)
  - [x] Subtask 4.2: Kreirati `templates/brands/partials/_tulip_hero.html` (`variant="green"`)
  - [x] Subtask 4.3: Kreirati `templates/brands/partials/_tulip_model_showcase.html` (REUSE coric-product-card + responsive_picture + key_features + „OPŠIRNIJE" → product.get_absolute_url; empty state)
  - [x] Subtask 4.4: Kreirati `templates/brands/partials/_tulip_comparison_table.html` per AC5 (`<table coric-comparison-table>` + caption visually-hidden + scope col/row + spec_rows iteracija + `|default:"—"`)
  - [x] Subtask 4.5: Include `partials/_testimonials_slider.html` sa `slider_id="tulip-testimonials-title"` (SM-D10 — verifikovati aria-labelledby matchuje)
  - [x] Subtask 4.6: Verifikovati single h1 + single main + empty stanja (testimonials/comparison/catalog conditional render)

- [x] **Task 5: `comparison-table.css` + `main.css` Edit (AC6)**
  - [x] Subtask 5.1: Kreirati `static/css/components/comparison-table.css` per AC6 (svi `coric-` prefix + svi `var(--token)`; horizontal scroll wrapper; zebra redovi; header bg green-800)
  - [x] Subtask 5.2: Token verifikacija — svaki `var(--token)` postoji u tokens.css (IMP-6 mirror); ako nedostaje, koristi postojeći ekvivalent + dokumentuj
  - [x] Subtask 5.3: EDIT `static/css/main.css` +1 `@import url('./components/comparison-table.css');` POSLE breadcrumb.css
  - [x] Subtask 5.4: Verifikovati NEMA CDN referenci; svi BEM `coric-` prefix; HZM REUSE category-showcase.css (NEMA novog import-a); Tulip REUSE `coric-product-card` DEFINISAN u `brand-listing.css:72` (NE tractor-listing.css — verifikovati klasa postoji live u brand-listing.css)

- [x] **Task 6: i18n .po fajlovi update (AC8)**
  - [x] Subtask 6.1: `uv run python manage.py makemessages -l sr -l hu -l en` (Docker container)
  - [x] Subtask 6.2: `locale/sr/LC_MESSAGES/django.po` — popuniti msgstr za sve nove msgid (AC8 listing)
  - [x] Subtask 6.3: `locale/hu/` + `locale/en/` — popuniti prevode (DeepL/manual review)
  - [x] Subtask 6.4: `uv run python manage.py compilemessages -l sr -l hu -l en`
  - [x] Subtask 6.5: Smoke — verifikuj 0 empty msgstr za nove msgid (sr)

- [ ] **Task 7: Manuelni Dev smoke check + Lighthouse a11y audit obe strane (AC9)**
  - [ ] Subtask 7.1: `just dev`; verifikuj 0004 migracija primenjena
  - [ ] Subtask 7.2: HZM smoke — `/sr/mehanizacija/radne-masine/`: hero + 4 kartice + CTA → SubcategoryListView (OQ-1 verifikacija) + responsive grid + hover
  - [ ] Subtask 7.3: Tulip smoke — `/sr/mehanizacija/mix-prikolice/`: hero + 2 model-kartice + „OPŠIRNIJE" → product detail + comparison tabela (mobile scroll) + testimonials (stub) + catalog CTA (stub)
  - [ ] Subtask 7.4: Empty/coming-soon/404 testovi oba brenda (shell mirror Story 2-10 AC9)
  - [ ] Subtask 7.5: `prefers-reduced-motion` test (kartice + testimonials)
  - [ ] Subtask 7.6: Lighthouse CLI obe strane (`2-12-hzm-lighthouse-*.json` + `2-12-tulip-lighthouse-*.json`); A11y ≥ 95 + Performance ≥ 80; citiraj skor-ove u Completion Notes PRE Step-04
  - [ ] Subtask 7.7: Keyboard nav obe strane (Tab kroz CTA/slider; fokus outline vidljiv)

- [ ] **Task 8: TEA-deliverable — testovi (RED phase, Step 3, NIJE Dev scope)** _(TEA agent u Step 3 piše testove PRE Dev GREEN; Dev NIKAD ne piše testove — project-context.md § Test discipline)_
  - **Minimum test count (~47 testova):**
  - [ ] Subtask 8.1: `apps/brands/tests/test_urls_hzm_tulip.py` — **AC1: 5 tests**
    - `test_hzm_url_resolves_sr/hu/en` (3 lokala HTTP 200)
    - `test_tulip_url_resolves_sr` (HTTP 200)
    - `test_hzm_tulip_no_collision_with_jeegee_subcategory_used_machinery` — `/sr/mehanizacija/prikljucna/`, `/sr/mehanizacija/prikljucna/osnovna-obrada-zemljista/`, `/sr/mehanizacija/polovna/` i dalje rezolvuju svoje view-ove
  - [ ] Subtask 8.2: `apps/brands/tests/test_views_hzm.py` — **AC2: 5 tests**
    - `test_hzm_context_contains_brand_and_4_subcategories`
    - `test_hzm_subcategories_ordered_by_display_order` (10/20/30/40)
    - `test_hzm_coming_soon_renders_brand_coming_soon_template` (subcategories NIJE u kontekstu)
    - `test_hzm_404_when_brand_does_not_exist` („HZM brand nije konfigurisan u sistemu.")
    - `test_hzm_empty_subcategories_when_category_missing` (radne-masine Category DELETE → subcategories=[] empty state, NE crash)
  - [ ] Subtask 8.3: `apps/brands/tests/test_views_tulip.py` — **AC3: 9 tests**
    - `test_tulip_context_contains_brand_products_spec_rows_testimonials`
    - `test_tulip_products_ordered_by_price` (6m³ pre 8m³ — seed price_eur 6500 < 8200; PRIMARNI sort ključ price_eur deterministički, NE string fallback)
    - `test_spec_rows_transposed_correctly` — verifikuje `spec_rows[0] == {"key": "Zapremina", "values": ["6 m³", "8 m³"]}` (SM-D7)
    - `test_spec_rows_missing_value_yields_none` — model bez nekog key-a → None u values (template → „—")
    - `test_tulip_coming_soon_renders_brand_coming_soon`
    - `test_tulip_404_when_brand_does_not_exist`
    - `test_tulip_no_testimonials_yields_empty_list` (0 testimonijala → testimonials=[])
    - `test_tulip_view_query_count_constant_with_assertNumQueries` (SM-D14 — N+1 guard) — sa `django.test.utils.CaptureQueriesContext`/`assertNumQueries`: broj upita MORA biti KONSTANTAN za 2 proizvoda i za N proizvoda (npr. seed-uj 4. proizvod sa 5 specifikacija → broj upita NE raste). Dokazuje da `Prefetch(queryset=...order_by)` NIJE pobijen per-product `.order_by()`-jem. **Ovaj test ZAKLJUČAVA query budget (AC3); ako padne → prefetch pobijen, NE lock-uj budget**
    - `test_spec_rows_uses_prefetched_specifications_no_extra_query` — unutar `assertNumQueries` bloka pozovi view i potvrdi da iteracija `_build_spec_rows` NE generiše dodatne upite (čita iz prefetch cache-a)
  - [ ] Subtask 8.4: `apps/brands/tests/test_templates_hzm.py` — **AC4 + AC8: ~7 tests**
    - `test_hzm_renders_exactly_one_h1` (BeautifulSoup)
    - `test_hzm_renders_exactly_one_main`
    - `test_hzm_renders_4_subcategory_cards`
    - `test_hzm_card_cta_href_uses_subcategory_get_absolute_url` — verifikuje CTA href je `/sr/mehanizacija/prikljucna/radne-masine/<sub-slug>/` (SM-D4)
    - `test_hzm_hero_renders_green_variant_repeating_element` — `coric-repeating-element--green` (NE --hzm; SM-D9)
    - `test_hzm_outer_section_has_aria_label_not_aria_labelledby` (SM-D8 mirror 2-10)
    - `test_hzm_no_cirillic_in_rendered_html`
  - [ ] Subtask 8.4b: `apps/brands/tests/test_breadcrumb_root_parametrization.py` — **SM-D13 / OQ-1a (AC9 breadcrumb fix — PUN TRAG, duplikat-free; AŽURIRANO iter 2): 5 tests**
    - `test_hzm_subcategory_breadcrumb_full_trail_no_duplicate` — **KANONSKI FULL-TRAIL ASSERTION:** GET `/sr/mehanizacija/prikljucna/radne-masine/<sub-slug>/` → ekstrahuj breadcrumb stavke kao ordered listu `{label, is_link/url}` (iz konteksta `breadcrumb` ili parsiraj DOM); assert **length == 3** i tačan item-by-item redosled: `[{"label": "Početna", url == reverse("core:home")}, {"label": "Radne mašine", url == reverse("brands:hzm_radne_masine")}, {"label": "<sub naziv>", is_link == False}]`. **Eksplicitno assert da NEMA ponovljene „Radne mašine" stavke** (npr. `[i.label for i in trail].count("Radne mašine") == 1`) i da je poslednja stavka NON-link (tail). Ovo dokazuje da je susedni duplikat „Radne mašine → Radne mašine" kolapsiran (SM-D13 reconciliacija)
    - `test_hzm_subcategory_drilldown_breadcrumb_root_is_radne_masine` — root (druga) stavka label == „Radne mašine" + url == `reverse("brands:hzm_radne_masine")` (NE „Priključna mehanizacija")
    - `test_jeegee_subcategory_breadcrumb_full_trail_unchanged` — **REGRESSION (full trail):** postojeći Jeegee `prikljucna` drill-down breadcrumb i dalje sadrži root „Priključna mehanizacija" (url `jeegee_prikljucna`) PA `category.name` link stavku PA ancestor lanac PA leaf non-link tail; assert da `category.name` link stavka NIJE kolapsirana (Jeegee distinct-label trag NETAKNUT — root-label ≠ category.name)
    - `test_jeegee_subcategory_drilldown_breadcrumb_root_unchanged` — Jeegee root i dalje == „Priključna mehanizacija" + `jeegee_prikljucna` url
    - `test_breadcrumb_root_fallback_for_unknown_category` — Category van mapiranja → root label = `category.name`, url=None, intermediate `category.name` stavka zadržana po staroj logici (no crash, no collapse)
  - [ ] Subtask 8.5: `apps/brands/tests/test_templates_tulip.py` — **AC5 + AC8: ~10 tests**
    - `test_tulip_renders_exactly_one_h1` + `test_tulip_renders_exactly_one_main`
    - `test_tulip_renders_2_model_cards` (coric-product-card)
    - `test_tulip_model_card_cta_links_to_product_detail` (href = product.get_absolute_url)
    - `test_tulip_comparison_table_renders_with_scope_attributes` — `<th scope="col">` model headers + `<th scope="row">` keys + `<caption>` (WCAG)
    - `test_tulip_comparison_table_missing_value_shows_emdash` („—")
    - `test_tulip_comparison_table_divergent_spec_keys_fills_emdash` — **OQ-2 lock (divergent-key fix iter 1):** seed model A sa key „Težina" koji model B NEMA → `spec_rows` ima red „Težina" sa `values=["<A vrednost>", None]`; renderovan red prikazuje „—" u koloni modela B. Verifikuje da neporavnati spec key-evi NE lome tabelu (NIJE samo aligned-seed happy path; pokriva i obrnuto — B ima key koji A nema)
    - `test_tulip_comparison_table_hidden_when_no_spec_rows` (0 spec → tabela NIJE u DOM-u)
    - `test_tulip_testimonials_section_hidden_when_empty` (0 testimonijala → sekcija NIJE u DOM-u)
    - `test_tulip_testimonials_slider_id_matches_aria_labelledby` (SM-D10)
  - [ ] Subtask 8.6: `apps/brands/tests/test_migration_0004_seed_hzm_tulip.py` — **AC7: 6 tests**
    - `test_migration_creates_hzm_brand_category_4_subcategories`
    - `test_migration_creates_tulip_brand_2_products_with_specs`
    - `test_migration_is_idempotent` (re-run → no duplicates)
    - `test_migration_reverse_deletes_all_seeded_data` (FK-safe order)
    - `test_subcategory_parents_are_none_and_category_is_radne_masine`
    - `test_tulip_products_key_features_within_cap_and_price_set` — verifikuje oba Tulip Product-a imaju `len(key_features) <= 3` (cap, `apps/products/models.py:238`) i `price_eur` postavljen (6m³ < 8m³); dokazuje da seed prolazi `full_clean()` bez ValidationError
  - [ ] Subtask 8.7: `tests/test_comparison_table_css.py` — **AC6: 3 tests**
    - `test_comparison_table_css_imported_in_main_css`
    - `test_comparison_table_css_uses_only_var_tokens` (0 magic hex; allow white/transparent/none keywords)
    - `test_comparison_table_css_has_coric_prefix_on_all_classes`
  - [ ] Subtask 8.8: TEA verifikuje RED phase (testovi padaju pre Dev GREEN); commit test fajlove PRE Dev (`test(brands): Story 2.12 RED-phase tests — HZM + Tulip landing views + templates + comparison table + data migracija`)

## Dev Notes

### Postojeća `apps/brands/` struktura (snimak pre Edit-a — regression guard)

Live verifikovano 2026-05-31:
```
apps/brands/
├── views.py            (BrandDetailView, JeegeePrikljucnaView, SubcategoryListView — Story 2.6/2.10/2.11; DODAJ HzmRadneMasineView + TulipMixPrikoliceView)
├── urls.py             (6 pattern-a — traktori/<slug>, mehanizacija/prikljucna/ + 4 subcategory_listing_l*; DODAJ 2 statička)
├── models.py           (Brand, Series, Category, Subcategory — NETAKNUTO; Subcategory.get_absolute_url() VEĆ implementiran Story 2.11)
├── migrations/         (0001_initial, 0002_alter_brand_created_at, 0003_seed_jeegee_and_prikljucna_categories — DODAJ 0004)
├── admin.py, translation.py, apps.py  (NETAKNUTO)
└── tests/
```

### Kritični REUSE pointeri (live verifikovani)

- `apps/brands/views.py:97-135` — `JeegeePrikljucnaView` (mirror za HZM/Tulip get_object/get_template_names/get_context_data idiom 1:1)
- `apps/brands/views.py:15` — `Http404` import VEĆ postoji
- `apps/brands/views.py:20-21` — `Brand, Category, Series, Subcategory` + `Product, ProductSpecification, ProductTestimonial` VEĆ importovani (REUSE; NEMA novog import-a)
- `apps/brands/views.py:168-170` — `category.subcategories.filter(parent=None).order_by("display_order", "name")` (potvrđuje related_name = `subcategories`; SM-D6)
- `apps/brands/models.py:411-417` — `Subcategory.get_absolute_url()` (REUSE za HZM CTA href; SM-D4)
- `templates/brands/partials/_category_showcase.html` — markup REFERENCE za `_hzm_subcategory_showcase.html` (RAZLIKA: href = sub.get_absolute_url, NE {% url subcategory_listing_category %})
- `templates/brands/partials/_jeegee_hero.html` (Story 2.10) — mirror za `_hzm_hero.html` + `_tulip_hero.html` (RAZLIKA: variant="green")
- `templates/partials/_testimonials_slider.html:2-3` — `slider_id` kwarg (Tulip prosleđuje "tulip-testimonials-title"; SM-D10)
- `static/css/components/category-showcase.css` (Story 2.10) — REUSE coric-category-card za HZM grid (NEMA edit)
- `static/css/components/brand-listing.css:72` — `.coric-product-card` DEFINISAN ovde (verifikovano live) — REUSE za Tulip model-kartice (Dev verifikuj klasa postoji live u brand-listing.css). **NAPOMENA:** `tractor-listing.css:6` ga SAMO referencira u komentaru, NE definiše — NE pokazivati na tractor-listing.css kao izvor.
- `static/css/components/repeating-element.css:11,14` — SAMO `--green` + `--jeegee` variant-e (SM-D9)

### SM Decisions log

- **SM-D1** — Jedna story za DVE strane (HZM + Tulip): epics.md Story 2.12 spec eksplicitno grupiše obe; dele REUSE temelj; razdvajanje bi dupliralo seed migraciju + view modul boilerplate. Net: 1 story, 2 view klase, 2 main template-a.
- **SM-D2** — HZM kao Subcategory dece (NE root Category instance kao Jeegee): epics.md kaže „4 potkategorije"; modelirano kao Subcategory dece HZM `radne-masine` Category-je da CTA vodi na Story 2-11 SubcategoryListView model listing (epics.md „Klik na potkategoriju vodi na listing modela u toj potkategoriji"). Jeegee 2-10 kartice su root Category jer vode na Subcategory listing nivo dublje; HZM kartice su Subcategory jer vode direktno na model listing.
- **SM-D3** — Data migracija 0004 seed (mirror Story 2-10 0003): seed-uje HZM/Tulip brendove + hijerarhiju + Tulip modele za smoke-test demonstraciju. Idempotentna get_or_create + FK-safe reverse.
- **SM-D4** — HZM CTA href = `subcategory.get_absolute_url()` (Story 2-11): vodi na `/mehanizacija/prikljucna/radne-masine/<sub-slug>/`. „prikljucna" je generički mehanizacija drill-down prefiks (NIJE Jeegee-specifičan) — Story 2-11 SubcategoryListView fetch-uje Category po `<category_slug>` sa `is_for=MEHANIZACIJA`, pa `radne-masine` rezolvuje bez izmene. Vidi OQ-1 za SEO. Fallback ako neprihvatljivo: dedicated `radne-masine/<sub>/` URL prostor (ODBAČENO za v1).
- **SM-D5** — URL deconfliction: `radne-masine` + `mix-prikolice` statički segmenti, NEMA kolizije.
- **SM-D6** — `category.subcategories` related_name potvrđen iz Story 2-11 live usage (NE re-verifikovati models.py).
- **SM-D7** — `spec_rows` transponovan kontekst za uporednu tabelu: `_build_spec_rows()` u view-u gradi listu `{key, values[]}` redova iz per-product ProductSpecification (key-order = first-appearance; missing → None → template „—"). DESIGN.md ključ-vrednost tabela layout (linija 324).
- **SM-D8** — 0004 cross-app dependency: Product/ProductSpecification seed zahteva `("products", "<last>")` u migration dependencies. Reverse FK-safe order: specs → products → subcategories → category → brands. **Rationale ispravljen (iter 1):** tačni `on_delete` su `Subcategory.category` = **CASCADE** (`models.py:321`, NE PROTECT) i `Product.brand` = **PROTECT** (`apps/products/models.py:100`). Reverse redosled je FK-safe u oba slučaja; eksplicitan dependent-pre-parent redosled je OBAVEZAN samo za PROTECT FK (`Product` pre `Brand`), a za CASCADE FK (`Subcategory` pre `Category`) je čistija praksa (ne oslanja se na cascade side-effect). Redosled stavki NEPROMENJEN.
- **SM-D9** — `variant="green"` za HZM + Tulip hero (NE `variant="hzm"`/`"tulip"` — CSS nema te klase; mirror Story 2-6 `variant="blue"` dormant bug). Brand-specifične variant-e = Story 9-10 polish.
- **SM-D10** — Tulip testimonials REUSE `_testimonials_slider.html` sa `slider_id="tulip-testimonials-title"`; partial generiše `<h2 id="{{ slider_id }}">` (linija 3), pa outer section `aria-labelledby="tulip-testimonials-title"` ispravno referencira.
- **SM-D11** — Cross-boundary brands→products READ-ONLY (Tulip Product/Spec/Testimonial query): project-context.md § Cross-boundary import Exception (SM-D16 precedent iz Story 2-6/2-11). View-layer-only, no .save()/.create().
- **SM-D12** — Sprint-status.yaml update je SM handoff tracking (NIJE deliverable file edit).
- **SM-D14** — **Prefetch ne sme biti pobijen per-product `.order_by()` (N+1 guard):** Original skeleton je imao `prefetch_related("specifications")` + per-product `product.specifications.all().order_by("order","id")` u `_build_spec_rows`. Django prefetch cache se gradi BEZ ordering-a, pa svaki `.order_by()` na prefetch-ovanom related manageru re-issue-uje NOVI upit PO PROIZVODU → N+1 (prefetch POBIJEN). **Lock: koristi `Prefetch("specifications", queryset=ProductSpecification.objects.order_by("order","id"))`** u `get_context_data` (ordered prefetch), a u `_build_spec_rows` koristi `product.specifications.all()` BEZ `.order_by()` (čita iz cache-a). `Prefetch` je VEĆ importovan u `apps/brands/views.py:14` (`from django.db.models import ... Prefetch ...` — REUSE, NEMA novog import-a). Query budget se zaključava TEK posle `assertNumQueries` testa koji dokazuje konstantan broj upita nezavisno od broja proizvoda/specifikacija (Subtask 8.3).
- **SM-D13** — **Breadcrumb root parametrizacija + reconciliacija duplikata (user-facing fix, NIJE SEO — OQ-1a; AŽURIRANO iter 2):** `SubcategoryListView._build_breadcrumb` (live `apps/brands/views.py:227-274`) ima DVE grane koje doprinose root delu traga: (1) drugu fiksnu stavku (`_("Priključna mehanizacija")` + `reverse("brands:jeegee_prikljucna")`, live `:244-248`) i (2) intermediate/leaf granu (live `:258-264`) koja ODMAH POSLE fiksne stavke dodaje JOŠ JEDNU stavku sa `category.name` + `_category_breadcrumb_url(...)`. **Iter-1 fix je parametrizovao SAMO granu (1)** — ali za HZM, gde parametrizovani root label („Radne mašine") == `category.name` HZM kategorije („Radne mašine"), grana (2) dodaje IDENTIČNU susednu stavku → renderovani breadcrumb postaje DUPLIKAT „Početna → Radne mašine → Radne mašine → <sub>" (drugi „Radne mašine" self-linkuje na trenutnu landing stranu). Za Jeegee duplikat se NE dešava jer root „Priključna mehanizacija" ≠ Jeegee `category.name` (npr. „Osnovna obrada zemljišta").

  **KRITIČNA KOREKCIJA DISKRIMINATORA (iter 2 — verifikovano live):** mapiranje se NE sme keyovati na pretpostavku da Jeegee kategorija ima slug „prikljucna". Live seed (`0003`) dokazuje da su Jeegee kategorije `osnovna-obrada-zemljista` / `priprema-zemljista` / `masine-za-setvu` — **NIJEDNA NIJE „prikljucna"**. „prikljucna" je SAMO statički URL path segment, NIKAD `category.slug`. Zato je **DEFAULT (ne-mapirano) ponašanje = postojeći generički „Priključna mehanizacija" prefiks** (link na `jeegee_prikljucna`) + zadržavanje `category.name` link stavke (Jeegee trag NETAKNUT). SAMO eksplicitno mapirane category-landing kategorije (`radne-masine` → HZM) ZAMENJUJU taj prefiks svojim landing root-om I KOLABIRAJU duplikat (preskaču `category.name` stavku jer ROOT JESTE ta kategorija). Mapiranje je keyovano na `category.slug` SAMO za kategorije koje IMAJU sopstvenu landing stranu izvan generičkog `prikljucna` prostora.

  **Lock (iter 2): parametrizuj root + RECONCILE duplikat, sa DEFAULT-om = generički Jeegee prefiks.** Dev MORA izmeniti `_build_breadcrumb` da: (a) izvuče root iz `_breadcrumb_root_for(category)` koje vraća `(item, is_category_landing)`; default (ne-mapirano) → `("Priključna mehanizacija", jeegee_prikljucna)` + `is_category_landing=False`; mapirano (`radne-masine`) → `("Radne mašine", hzm_radne_masine)` + `is_category_landing=True`; (b) u intermediate/leaf grani PRESKOČI `category.name` stavku KADA `is_category_landing=True` (root JE ta kategorija → druga „category.name" stavka bi bila susedni duplikat). Kada `is_category_landing=False` (Jeegee i sve generičke prikljucna kategorije), zadržava se postojeći `category.name` link stavka po staroj logici → Jeegee pun trag NETAKNUT.

  ```python
  # Mapiranje category.slug → DEDICATED landing root (kategorije sa sopstvenom
  # brand-landing stranom izvan generičkog `prikljucna` prostora). Default (ne u
  # mapi) = generički „Priključna mehanizacija" prefiks (postojeće ponašanje).
  # Drži se uz module-level konstante; proširivo za buduće brand landing-e.
  _CATEGORY_LANDING_BREADCRUMB_ROOT = {
      "radne-masine": ("Radne mašine", "brands:hzm_radne_masine"),
  }

  def _breadcrumb_root_for(self, category):
      # Vraća (item, is_category_landing). is_category_landing=True znači da root
      # JESTE landing čvor ove kategorije → intermediate grana NE sme ponovo da
      # doda category.name stavku (reconciliacija duplikata). False = generički
      # „Priključna mehanizacija" prefiks (Jeegee + sve ostale prikljucna kat.).
      mapped = _CATEGORY_LANDING_BREADCRUMB_ROOT.get(category.slug)
      if mapped is not None:
          label, url_name = mapped
          item = {"label": _(label), "url": reverse(url_name), "is_current": False}
          return item, True
      # Default: postojeći generički prikljucna prefiks (NEPROMENJENO ponašanje).
      item = {
          "label": _("Priključna mehanizacija"),
          "url": reverse("brands:jeegee_prikljucna"),
          "is_current": False,
      }
      return item, False
  ```

  i u `_build_breadcrumb` (prva fiksna stavka „Početna" ostaje; zameni hardcode-ovanu drugu stavku + intermediate granu):
  ```python
  # items započinje sa [{"label": _("Početna"), "url": reverse("core:home"), ...}]
  root_item, is_category_landing = self._breadcrumb_root_for(category)

  if current is None:
      # Category-root strana (.../prikljucna/<cat>/ bez subcat).
      if is_category_landing:
          # HZM radne-masine landing: root JE current (non-link) tail —
          # NE dupliraj category.name (root već predstavlja kategoriju).
          items.append({**root_item, "is_current": True, "url": None})
      else:
          # Generička prikljucna kategorija: prefiks link + category.name tail.
          items.append(root_item)
          items.append({"label": category.name, "url": None, "is_current": True})
      return items

  # Intermediate/leaf:
  items.append(root_item)
  if not is_category_landing:
      # Generička prikljucna: Category kao link, pa lanac ancestor-a, pa tail.
      items.append({
          "label": category.name,
          "url": self._category_breadcrumb_url(category, current),
          "is_current": False,
      })
  # Ako is_category_landing → preskoči category.name stavku (root JE ta
  # kategorija; izbegava se duplikat „Radne mašine → Radne mašine").
  for ancestor in current.get_ancestors_chain():
      items.append({
          "label": ancestor.name,
          "url": ancestor.get_absolute_url(),
          "is_current": False,
      })
  items.append({"label": current.name, "url": None, "is_current": True})
  return items
  ```

  **KANONSKI HZM L1 trag (duplikat-free, eksplicitno definisan):** za HZM `radne-masine` L1 subcategory drill-down (parent=None, depth=1, `get_ancestors_chain()==[]`) renderovani breadcrumb MORA biti TAČNO 3 stavke:
  ```
  ["Početna" (link → core:home),
   "Radne mašine" (link → brands:hzm_radne_masine),
   "<naziv subcategory-je>" (NON-link, is_current)]
  ```
  — NEMA druge „Radne mašine" stavke. Za Jeegee `prikljucna` drill-down (root label ≠ category.name) trag ostaje NEPROMENJEN: „Početna → Priključna mehanizacija → <category.name> → … → <leaf>" (Jeegee `category.name` JESTE realan naziv kategorije, NE duplikat root-a — reconciliacija NE kolabira ništa kod Jeegee jer je root-label-vs-category-name uvek različit).

  **VAŽNO:** svi label string-ovi kroz `gettext`/`{% translate %}` (dodati „Radne mašine" msgid u .po). Reconciliacija je GENERIČKA — radi za BILO koju kategoriju upisanu u `_CATEGORY_LANDING_BREADCRUMB_ROOT` (kategorija sa sopstvenom landing stranom čiji root label JESTE njena landing tačka), i NE regresira Jeegee (Jeegee kategorije nisu u mapi → default „Priključna mehanizacija" prefiks + zadržan `category.name` link → trag NETAKNUT). Ovo je MALA, ciljanja izmena postojeće metode — NE menja redosled preostalih stavki. **Ovo je JEDINI dozvoljen EDIT na Story 2-11 `SubcategoryListView` u ovoj story** (uži scope: samo `_build_breadcrumb` root-parametrizacija + duplikat-reconciliacija; ostatak view-a NETAKNUT — regression guard: Jeegee `prikljucna` breadcrumb i dalje pokazuje „Priključna mehanizacija" kao root i NE gubi `category.name` stavku).

### Open Questions

- **OQ-1 (DVA odvojena pitanja — VIDLJIVI breadcrumb label MORA se popraviti u ovoj story; SEO URL putanja deferred Story 6-6):**
  - **(1a) VIDLJIVI breadcrumb label + DUPLIKAT defekt — NIJE SEO, MORA fix u ovoj story (vidi SM-D13 + AC9 + Subtask 2.6; AŽURIRANO iter 2):** HZM „Radne mašine" drill-down vodi na Story 2-11 `SubcategoryListView`, ali `SubcategoryListView._build_breadcrumb` ima DVA defekta za HZM: (i) hardcode-ovan root label „Priključna mehanizacija" (live `:244-248`); i (ii) — OTKRIVENO POSLE iter-1 fix-a — intermediate/leaf grana (live `:258-264`) dodaje JOŠ JEDNU stavku `category.name`, koja za HZM == parametrizovani root („Radne mašine"), pa nastaje SUSEDNI DUPLIKAT „Početna → Radne mašine → Radne mašine → <sub>" (drugi „Radne mašine" self-linkuje na trenutnu landing stranu). **Lock (SM-D13 iter 2): popraviti parametrizacijom root-a (preko `_breadcrumb_root_for`) + RECONCILE-ovanjem duplikata** — kada je `is_category_landing=True` (kategorija upisana u `_CATEGORY_LANDING_BREADCRUMB_ROOT`, npr. `radne-masine`), root JE ta kategorija pa intermediate grana PRESKAČE `category.name` stavku. **KANONSKI HZM L1 trag (duplikat-free): TAČNO `["Početna", "Radne mašine"(link→hzm_radne_masine), "<sub naziv>"(non-link)]` — length 3.** Reconciliacija je GENERIČKA (radi za bilo koju kategoriju registrovanu u landing mapi) i NE regresira Jeegee: Jeegee kategorije (`osnovna-obrada-zemljista` itd.) NISU u mapi → DEFAULT generički „Priključna mehanizacija" prefiks + zadržan `category.name` link → trag NETAKNUT (NEMA kolapsa). Vidi SM-D13 za skeleton i AC9 + Subtask 8.4b za full-trail assertion.
  - **(1b) SEO — URL putanja `prikljucna` prefiks (deferred Story 6-6):** HZM subcategory URL-ovi koriste `prikljucna` prefiks (`/mehanizacija/prikljucna/radne-masine/<sub>/`) iako je HZM „radne mašine" semantički, ne „priključna". Funkcionalno radi (Story 2-11 view category-agnostic), ali URL putanja (segment u browser bar-u) je generička. SEO odluka (dedicated `radne-masine/<sub>/` URL prostor vs zadržati `prikljucna` generički prefiks + canonical tag) deferred to Story 6-6 (hreflang + locale-aware slug-ovi). v1 lock: `prikljucna` generički u PUTANJI. **Napomena:** breadcrumb LABEL (1a) je nezavisno od URL PUTANJE (1b) — label se popravlja sada, putanja ostaje za 6-6.
- **OQ-2 (Tulip comparison tabela source) — RESOLVED + test-locked (iter 1):** spec_rows iz ProductSpecification (per SM-D7). Alternativa bi bila dedicated dimension model — ODBAČENO (ProductSpecification je već key/value, REUSE). Ako Tulip modeli imaju neporavnate (divergent) spec key-eve (npr. model A ima „Težina", model B nema — ili obrnuto), tabela prikazuje „—" za prazno — acceptable v1. **Ovo ponašanje je sada ZAKLJUČANO TEA RED testom** `test_tulip_comparison_table_divergent_spec_keys_fills_emdash` (Subtask 8.5) + `test_spec_rows_missing_value_yields_none` (Subtask 8.3) — pokriva i model-A-ima-B-nema i obrnuto, NE samo aligned-seed happy path. AC7 seed koristi poravnate key-eve (isti set za oba modela) za primarni prikaz, ali divergent slučaj je eksplicitno testiran da se zaključa „—" fill ponašanje.
- **OQ-4 (Tulip demo dimenzije — biznis sign-off PRE produkcije):** AC7 seed-uje Tulip MIX dimenzije (Dužina/Širina/Nosivost) + `price_eur` kao DEMO/PLACEHOLDER vrednosti za smoke-test prikaz. One se renderuju u PUBLIC uporednoj tabeli kao da su realne specifikacije. **Akcija pre produkcije:** Mihas/biznis MORA potvrditi realne tehničke vrednosti (ili ih dopuniti kroz admin) PRE nego što Tulip strana ide live. „Zapremina" (6/8 m³) je pouzdana (iz naziva modela); ostalo je placeholder. Dev beleži u Completion Notes da su demo. Status: OTVORENO — čeka biznis potvrdu (NIJE blocking za Dev GREEN/smoke, ALI blocking za production publish Tulip strane).
- **OQ-3 (HZM catalog CTA):** epics.md ne pominje HZM catalog CTA (samo Tulip „Preuzmi katalog"). Story dodaje opcioni HZM catalog CTA (`{% if brand.catalog_pdf %}` guard) za konzistentnost sa Jeegee/Tulip — render-uje samo ako admin doda PDF. Ako neželjeno, Dev MAY izostaviti HZM catalog sekciju (NIJE blocking AC).

### Project Context Reference

Sva pravila iz `_bmad-output/project-context.md` se primenjuju. Posebno kritično za ovu story:
- Srpski latinica pune dijakritike (č/ć/ž/š/đ) u svemu renderovanom; ASCII u slugovima (`radne-masine`, `mix-prikolice`, `teleskopski-utovarivaci`)
- Sve UI string kroz `{% translate %}` / `gettext_lazy as _`
- CSS `var(--token)` (NEMA magic hex/px); `coric-` BEM prefix
- Cross-boundary brands→products READ-ONLY (Exception note linija 658-664)
- Migracija manual review pre commit (RunPython sa reverse_code)
- A11y must-haves: single h1, single main, aria landmarks, table scope, focus-visible, contrast ≥ 4.5:1, prefers-reduced-motion
- Performance: select_related/prefetch_related (Tulip **`Prefetch("specifications", queryset=...order_by("order","id"))`** — ORDERED prefetch da per-product iteracija ne pobije cache, SM-D14; + select_related testimonials product), responsive_picture srcset, loading="lazy". Query budget zaključan `assertNumQueries` testom (Subtask 8.3) koji dokazuje konstantan broj upita

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.12 (linije 678-689)]
- [Source: _bmad-output/implementation-artifacts/2-10-jeegee-prikljucna-mehanizacija-strana.md — JeegeePrikljucnaView pattern + coric-category-card + _jeegee_hero.html + 0003 seed precedent]
- [Source: _bmad-output/implementation-artifacts/2-11-subcategory-listing-4-nivoa-hijerarhija.md — SubcategoryListView + Subcategory.get_absolute_url + breadcrumb + cross-boundary READ-ONLY]
- [Source: apps/brands/views.py:97-135 — JeegeePrikljucnaView; :168-170 related_name; :15,20-21 imports]
- [Source: apps/brands/models.py:241-303 Category; :311-417 Subcategory + get_absolute_url]
- [Source: apps/products/models.py:78-196 Product; :366-417 ProductSpecification; :464-499 ProductTestimonial]
- [Source: templates/partials/_testimonials_slider.html:2-3 — slider_id kwarg]
- [Source: templates/brands/partials/_category_showcase.html — markup reference]
- [Source: _bmad-output/planning-artifacts/ux-designs/ux-CORIC_AGRAR-2026-05-27/DESIGN.md:311 Card Base; :324 tabela ključ-vrednost; :305-308 Button]
- [Source: _bmad-output/project-context.md — sva pravila]

## Dev Agent Record

### Agent Model Used

_(popunjava Dev agent)_

### Debug Log References

### Completion Notes List

### File List
