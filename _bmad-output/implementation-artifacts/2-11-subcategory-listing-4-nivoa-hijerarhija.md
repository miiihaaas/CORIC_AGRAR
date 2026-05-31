---
story_id: "2.11"
story-key: 2-11-subcategory-listing-4-nivoa-hijerarhija
title: Subcategory Listing (4-nivoa hijerarhija)
status: ready-for-dev
epic: 2
epic_num: 2
epic_title: Public Catalog — Browse Brands & Products
module: brands
created: 2026-05-31
last_modified: 2026-05-31
complexity: M-L
author: Mihas (SM autonomous; HIJERARHIJSKI drill-down story — varijabilan URL depth /mehanizacija/prikljucna/<category>/[<subcat>/[<subsubcat>/]]; mapira na Category root + Subcategory self-FK chain MAX 3 nivoa duboko = 4 nivoa stabla; intermediate nivoi renderuju coric-category-card REUSE iz Story 2-10, leaf nivo renderuje coric-product-card model-kartice; breadcrumb na vrhu; ovo je FIRST story koja implementira Subcategory.get_absolute_url() + ZAVRŠAVA dug 2-10 href→{% url %} refactor; cross-boundary brands→products READ-ONLY per SM-D16 — view query-uje Product.objects.filter(subcategory=...) za leaf level)
depends_on:
  - 2-1-brand-series-category-subcategory-modeli  # Category (is_for="mehanizacija") + Subcategory self-FK chain + get_ancestors_chain()/get_depth() helpers + MAX 3 nivoa depth validation
  - 2-2-product-i-related-modeli                   # Product.subcategory FK (nullable PROTECT) + Product.is_published; leaf model-card render
  - 2-3-image-pipeline-sa-sorl-thumbnail-responsive-srcset  # {% responsive_picture %} za product.main_image u model-karticama
  - 2-7-product-detail-strana                       # coric-product-card target — product.get_absolute_url() vodi na products:detail
  - 2-8-tractor-listing-strana-sa-htmx-filterima    # coric-product-card BEM + _results_grid.html model-card markup precedent (REUSE pattern, NE HTMX)
  - 2-10-jeegee-prikljucna-mehanizacija-strana      # coric-category-card BEM + category-showcase.css (1:1 REUSE za intermediate nivoe); 0003 seed migracija (Jeegee Brand + 3 Category); CTA href placeholder koji OVA story konvertuje u {% url %}
---

# Story 2.11: Subcategory Listing (4-nivoa hijerarhija)

Status: ready-for-dev

## Opis

As a **posetilac (poljoprivrednik koji je sa Jeegee landing strane `/sr/mehanizacija/prikljucna/` kliknuo na kategoriju npr. „Osnovna obrada zemljišta" i sada drill-uje kroz hijerarhiju potkategorija da nađe konkretan tip mašine; Đorđe — Mihasov klijent koji testira tastaturom + NVDA i očekuje breadcrumb orijentir „gde sam u stablu")**,

I want **da navigiram kroz varijabilno-duboku URL hijerarhiju priključne mehanizacije:**
- `/sr/mehanizacija/prikljucna/<category-slug>/` → prikazuje top-level potkategorije te Category-je kao kartice (npr. „Osnovna obrada zemljišta" → Plugovi, Podrivači, Gruberi);
- `/sr/mehanizacija/prikljucna/<category-slug>/<subcat-slug>/` → prikazuje child potkategorije te potkategorije kao kartice (npr. „Plugovi" → Plugovi ravnjaci, Plugovi obrtači);
- `/sr/mehanizacija/prikljucna/<category-slug>/<subcat-slug>/<subsubcat-slug>/` → LEAF nivo: prikazuje konkretne MODELE (Product instance vezane za tu potkategoriju) kao model-kartice sa slikom + nazivom + ključnim specifikacijama + „OPŠIRNIJE" CTA koji vodi na product detail stranu;

**i da na svakom nivou vidim breadcrumb navigaciju na vrhu (Početna › Priključna mehanizacija › Osnovna obrada zemljišta › Plugovi › …) koja mi omogućava da skočim nazad na bilo koji predačni nivo**,

so that **brzo dolazim do tačnog tipa mašine koji me zanima bez gubljenja orijentacije u dubokom stablu, i mogu jednim klikom da odem na detalj konkretnog modela**.

**KLJUČNA arhitektonska postavka (SM-D2):** „4-nivoa hijerarhija" iz epics.md mapira na **Category root (nivo 1) + Subcategory self-FK chain MAX 3 nivoa duboko (nivoi 2–4)**. Story 2-1 Subcategory model dozvoljava chain dubinu od MAX 3 (`_SUBCATEGORY_MAX_DEPTH = 3`, validovano u `clean()`), što kombinovano sa Category root-om daje TAČNO 4 nivoa stabla. URL path segmenti POSLE `<category-slug>/` su Subcategory slug-ovi (1 do 3 segmenta). Helper metode `Subcategory.get_ancestors_chain()` i `get_depth()` (Story 2-1 AC11) već postoje i koriste se za breadcrumb + depth resoluciju.

**KLJUČNA navigaciona logika (SM-D3):** Da li je nivo „intermediate" (renderuj subcategory kartice) ili „leaf" (renderuj model-kartice) NIJE fiksno vezano za depth — odlučuje se **dinamički iz strukture podataka**: ako trenutna potkategorija (ili Category, na nivou 1) IMA decu-potkategorije → renderuj subcategory kartice (intermediate); ako NEMA dece → renderuj Product model-kartice vezane za tu potkategoriju (leaf). Ovo dozvoljava da različite grane stabla imaju različitu dubinu (jedna kategorija može biti leaf na nivou 2, druga ide do nivoa 4). Epics.md primer „plugovi-obrtaci → grupisani po debljini grede (90×90 … 160×160)" je leaf nivo gde se model-kartice opciono grupišu po atributu (vidi SM-D7 za grouping strategiju).

**Strana NEMA HTMX, NEMA JavaScript interakciju, NEMA forme, NEMA paginaciju, NEMA range slider, NEMA sort dropdown — pure server-side rendered drill-down navigacija.** Ovo je svesno DIFERENTNO od Story 2-8/2-9 (HTMX filteri); ova story je čista hijerarhijska navigacija (mirror Story 2-10 statički pattern, ali sa varijabilnim URL depth-om umesto fiksnog). Svaki nivo je jedan full-page server render.

**REUSE fokus (0 novih JS modula; 1 nova CSS komponenta — breadcrumb):**

- **`Category` model** (Story 2-1): root resolucija prvog URL segmenta — `Category.objects.get(slug=<category-slug>, is_for=Category.CategoryScope.MEHANIZACIJA)`. Polja: `category.slug`, `category.name`, `category.description`.
- **`Subcategory` model** (Story 2-1): chain resolucija ostalih segmenata kroz `category` FK + `parent` self-FK. Polja: `subcategory.slug`, `subcategory.name`, `subcategory.description`, `subcategory.icon`, `subcategory.children` (related_name), `subcategory.products` (related_name iz Product.subcategory). Helper-i: `get_ancestors_chain()`, `get_depth()`.
- **`Product` model** (Story 2-2, READ-ONLY cross-boundary per SM-D16): leaf nivo — `Product.objects.filter(subcategory=<leaf-subcat>, is_published=True)`. Polja korišćena u model-kartici: `product.slug`, `product.name`, `product.main_image`, `product.horse_power`, `product.price_eur`, `product.get_absolute_url`, `product.key_features` (opciono za ključne specifikacije). **NE WRITE na Product iz brands view-a.**
- **`coric-category-card` BEM + `static/css/components/category-showcase.css`** (Story 2-10) — REUSE 1:1 za intermediate (subcategory) nivoe. Subcategory kartice mapiraju isto kao Category kartice (ikona + naziv + opis + CTA), pa se isti `_category_showcase.html` markup pattern REUSE-uje sa subcategory queryset-om (vidi SM-D5 za partial reuse vs new).
- **`coric-product-card` BEM + model-card markup** (Story 2-8 `templates/products/partials/_results_grid.html`) — REUSE markup PATTERN za leaf nivo model-kartice (slika + naziv + horse_power/price + „OPŠIRNIJE" CTA → `product.get_absolute_url`). Story 2-11 NE REUSE-uje `_results_grid.html` direktno (sadrži HTMX paginaciju + OOB aria-live koji su out-of-scope ovde); umesto toga kreira svoj `_model_grid.html` partial koji REUSE-uje istu `coric-product-card` BEM klasu (CSS već postoji — NEMA nove CSS za model-karticu).
- **`{% responsive_picture %}` template tag** (Story 2-3) — za `product.main_image` render u model-karticama.
- **`templates/partials/section_eyebrow.html`** (Story 1-7) — UPPERCASE eyebrow iznad grid-a.
- **`brands` URL namespace + apps/brands/urls.py + apps/brands/views.py modul** (Story 2-6 + 2-10) — Story 2-11 dodaje URL pattern-e + CBV unutar postojećih fajlova.
- **CSS tokens** (`static/css/tokens.css`, Story 1-5) — breadcrumb komponenta koristi `var(--token)` reference (boje, spacing, typography); NEMA novih tokena.

**Foundation za buduće Story-je:**

- **Story 2-12 (HZM Radne Mašine + Tulip MIX):** HZM strana ima 4 potkategorije sa drill-down u model listing — REUSE-uje istu `SubcategoryListView` + breadcrumb pattern ako se URL prostor proširi na `/mehanizacija/radne-masine/<subcat>/`. (TBD u Story 2-12 SM — možda dedicated view; ali breadcrumb komponenta + model-grid partial su reusable.)
- **Story 2-13 (Global Search):** search rezultati linkuju na leaf subcategory / product detail strane registrovane ovde.

**Princip:** Pure server-side rendering, **NEMA HTMX**, **NEMA JavaScript**, **NEMA forma**, **NEMA admin promena**, **NEMA migracije šeme** (Story 2-1 + 2-2 modeli su nepromenjeni). Opciono: jedna OPCIONA seed migracija `0004` koja dodaje Subcategory + sample Product instance za smoke-test demonstraciju hijerarhije (vidi SM-D14 — Dev MAY skip ako test factory pokriva sve; NIJE blokirajuće). Vanilla Django CBV (`TemplateView` ili custom `View` — vidi SM-D4). CSS BEM sa `coric-` prefiksom + isključivo `var(--token)`. Sve user-facing string-ove kroz `{% translate %}` / `gettext_lazy as _`. URL slug ASCII (`osnovna-obrada-zemljista`, `plugovi`, `plugovi-obrtaci` — NE dijakritike u slug-u; ali č/ć/ž/š/đ PUNE u `name` poljima koja se renderuju).

**Strukturna arhitektura — repository delta:** **5 NEW + 5 EDIT + 0 DELETE + 0 obavezne migracije (1 opciona)** (kanonsko brojanje — prebrojivo iz tabele ispod):

| Path | Tip | Razlog |
|---|---|---|
| `apps/brands/views.py` | EDIT (ADD class + import) | Dodaje `SubcategoryListView` CBV (postojeće `BrandDetailView` + `JeegeePrikljucnaView` iz Story 2-6/2-10 ostaju NETAKNUTE). View resoluje varijabilan URL path → Category root + Subcategory chain; odlučuje intermediate vs leaf; gradi breadcrumb + children/products context. EDIT import: dodaj `from apps.brands.models import Subcategory` u postojeću `from apps.brands.models import Brand, Category, Series` liniju. Reuse postojeći `from apps.products.models import Product` (SM-D16 read-only). Dodaj `from django.http import Http404` (već importovan iz Story 2-10). |
| `apps/brands/urls.py` | EDIT (ADD 1–3 path) | Dodaje URL pattern(e) za 3 nivoa drill-down POSLE postojećeg `mehanizacija/prikljucna/`. Vidi SM-D6 za pattern strategiju (3 eksplicitna path-a vs 1 catch-all `<path:subpath>`). Imena: `subcategory_listing` (ili po nivou). **KRITIČNO (SM-D6):** novi path-ovi MORAJU biti registrovani POSLE statičkog `mehanizacija/prikljucna/` (bez segmenta) da ne shadow-uju `JeegeePrikljucnaView`; i NE smeju kolidirati sa `traktori/<slug>/` (brands), `proizvod/<slug>/` / `traktori/` / `mehanizacija/polovna/` (products). |
| `apps/brands/models.py` | EDIT (1 metoda) | Implementira `Subcategory.get_absolute_url()` koji trenutno `raise NotImplementedError("Subcategory URL pattern defined in Story 2.11")` (live `apps/brands/models.py:411-414`). Nova implementacija gradi `/<lang>/mehanizacija/prikljucna/<category-slug>/<...subcat-slugs.../>` kroz `reverse()` ili manuelnu konstrukciju iz `get_ancestors_chain()`. **JEDINA model promena — NEMA šeme promene, NEMA migracije** (metoda nije DB polje). Vidi SM-D8. |
| `templates/brands/subcategory_listing.html` | NOVO | Glavni template — `{% extends "base.html" %}`; outer `<section class="coric-subcategory-listing" data-testid="subcategory-listing-page" aria-labelledby="subcategory-listing-title">`; renderuje breadcrumb partial → `<h1 id="subcategory-listing-title">` (naziv trenutnog nivoa) → CONDITIONAL: intermediate → `_subcategory_showcase.html`, leaf → `_model_grid.html`. **JEDAN `<h1>`** (naziv trenutne kategorije/potkategorije — ovo je listing strana BEZ hero card-a, za razliku od 2-10; h1 je legitiman ovde). **single `<main>`** (iz base.html). |
| `templates/brands/partials/_breadcrumb.html` | NOVO | Breadcrumb nav partial — `<nav aria-label="...">` sa `<ol>` listom: Početna › Priključna mehanizacija › <Category.name> › <ancestor subcat names...> › <trenutni nivo (NIJE link — aria-current="page")>. Prima `breadcrumb_items` context (lista dict-ova `{label, url, is_current}`). Vidi SM-D9. |
| `templates/brands/partials/_subcategory_showcase.html` | NOVO | Intermediate-nivo grid — Section Eyebrow + grid wrapper koji iterira `children` queryset (Subcategory instance) i renderuje per-subcategory `coric-category-card` (REUSE 2-10 BEM 1:1: ikona + naziv + opis + CTA → `subcategory.get_absolute_url`). `{% empty %}` clause za prazno stablo. Vidi SM-D5. |
| `templates/brands/partials/_model_grid.html` | NOVO | Leaf-nivo grid — Section Eyebrow + grid koji iterira `products` (ili `grouped_products` ako grouping aktivan — SM-D7) i renderuje per-product `coric-product-card` (REUSE 2-8 BEM 1:1: `responsive_picture(main_image)` + naziv + horse_power/price + „OPŠIRNIJE" CTA → `product.get_absolute_url`). `{% empty %}` clause „Nema dostupnih modela u ovoj kategoriji.". Vidi SM-D7. |
| `static/css/components/breadcrumb.css` | NOVO | Layout za `coric-breadcrumb` (flex/inline `<ol>` sa separatorom `›`, link styling, current-page styling, responsive wrap, focus-visible state). Sve vrednosti kroz `var(--token)`. **JEDINA nova CSS komponenta** (subcategory grid REUSE-uje category-showcase.css; model grid REUSE-uje product-card iz tractor-listing.css). |
| `static/css/main.css` | EDIT | Dodaje TAČNO 1 nova `@import url('./components/breadcrumb.css');` linija POSLE postojeće `@import url('./components/category-showcase.css');` (Story 2-10 zadnja). |
| `locale/sr/LC_MESSAGES/django.po`, `locale/hu/LC_MESSAGES/django.po`, `locale/en/LC_MESSAGES/django.po` | EDIT (×3) | Popuni msgstr za nove msgid (breadcrumb „Početna" / „Priključna mehanizacija", eyebrow tekstovi, empty-state poruke, aria-labeli, Http404 poruke). Subcategory.name polja se ne prevode ovde (SM-D16 — modeltranslation hu/en deferred to Story 8-5). |

**Brojanje (KANONSKO — single source of truth):** **5 NEW + 5 EDIT + 0 DELETE + 0 obavezne migracije.**
- **5 NEW:** `subcategory_listing.html` + `_breadcrumb.html` + `_subcategory_showcase.html` + `_model_grid.html` + `breadcrumb.css`.
- **5 EDIT:** `apps/brands/views.py` (ADD class) + `apps/brands/urls.py` (ADD path-ovi) + `apps/brands/models.py` (implement get_absolute_url) + `static/css/main.css` (+1 @import) + 3 .po fajla (broji se kao 1 logički EDIT „locale" ali fizički 3 fajla — kanonsko brojanje računa locale kao 1; ukupno fizičkih EDIT fajlova = 7). Sprint-status.yaml update je SM handoff tracking, NIJE deliverable edit.
- **1 OPCIONA migracija** (SM-D14): `apps/brands/migrations/0004_seed_subcategory_hierarchy.py` — Dev MAY dodati za smoke-test demo podatke; NIJE blokirajuće za AC.

**KRITIČNA 2-10 href→{% url %} REFACTOR OBAVEZA (SM-D10):** Story 2-10 je svesno postavio placeholder direct-string href u `templates/brands/partials/_category_showcase.html` (linija 283): `href="/{{ LANGUAGE_CODE }}/mehanizacija/prikljucna/{{ category.slug }}/"` jer named URL pattern nije postojao. Story 2-11 REGISTRUJE taj named pattern (`brands:subcategory_listing` ili ekvivalent). **Story 2-11 MORA refaktorisati 2-10 placeholder href u proper `{% url %}` tag** čim pattern postoji — npr. `href="{% url 'brands:subcategory_listing' category_slug=category.slug %}"`. Ovo je EDIT na postojeći `_category_showcase.html` partial (vidi SM-D10 za tačan tag oblik i fallback). **DODAJ `templates/brands/partials/_category_showcase.html` kao 6. fizički EDIT fajl** ako Dev konvertuje href (preporučeno; vidi Open Question OQ-3 za semantiku ako se pattern signature razlikuje).

Postojeći fajlovi koji ostaju **NETAKNUTI** (regression guards): `apps/brands/views.py` `BrandDetailView` + `JeegeePrikljucnaView` klase (samo se DODAJE nova klasa), `apps/brands/admin.py`, `apps/brands/translation.py`, `apps/brands/migrations/0001-0003`, `apps/products/` (kompletno — READ-ONLY query, NEMA edit), `apps/core/`, `apps/media_pipeline/`, `config/urls.py` (include red ne menja se — `apps.brands.urls` već uključeno), `templates/base.html`, `templates/partials/*` (Story 1-7), `templates/brands/jeegee_prikljucna.html` + `_jeegee_hero.html` (Story 2-10 — NETAKNUTI), `templates/products/partials/_results_grid.html` (Story 2-8 — REUSE pattern, NE edit), `static/vendor/*`, `static/js/*` (NEMA JS), `static/css/tokens.css`, `static/css/components/category-showcase.css` (Story 2-10 — REUSE 1:1, NE edit), `static/css/components/tractor-listing.css` (sadrži coric-product-card — REUSE, NE edit), `pyproject.toml`, `config/settings/`.

## Kriterijumi prihvatanja

**AC1 — URL routing: varijabilan-depth path rezolvuje `SubcategoryListView` za 3 nivoa drill-down; sva 3 locale; NEMA kolizije sa postojećim pattern-ima**

**Given** Category (is_for="mehanizacija") + Subcategory chain iz Story 2-1
**When** posetim:
- `/sr/mehanizacija/prikljucna/<category-slug>/` (nivo 1 drill — Category top-level subcategories)
- `/sr/mehanizacija/prikljucna/<category-slug>/<subcat-slug>/` (nivo 2)
- `/sr/mehanizacija/prikljucna/<category-slug>/<subcat-slug>/<subsubcat-slug>/` (nivo 3 = leaf u 3-deep grani)
**Then** svaki URL rezolvuje `SubcategoryListView` i daje HTTP 200 kad podaci postoje
**And** rezolucija radi za `/sr/`, `/hu/`, `/en/` prefix
**And** statički `/sr/mehanizacija/prikljucna/` (BEZ segmenta) i dalje rezolvuje `JeegeePrikljucnaView` (Story 2-10 — NIJE shadow-ovan)
**And** novi pattern NE kolidira sa `traktori/<slug>/`, `proizvod/<slug>/`, `traktori/`, `mehanizacija/polovna/`.

**AC2 — Category root resolucija (nivo 1): nepostojeći/pogrešan-scope category-slug → Http404; postojeći → renderuje top-level potkategorije**

**Given** Category „Osnovna obrada zemljišta" (slug osnovna-obrada-zemljista) sa decom-potkategorijama Plugovi / Podrivači / Gruberi
**When** posetim `/sr/mehanizacija/prikljucna/osnovna-obrada-zemljista/`
**Then** view fetch-uje Category po slug-u + `is_for=MEHANIZACIJA` filter; ako ne postoji ili je `is_for=TRAKTORI` → raise `Http404`
**And** strana renderuje 3 top-level potkategorije (Subcategory sa `category=ova` + `parent=None`) kao `coric-category-card` kartice ordered by `display_order, name`.

**AC3 — Subcategory chain resolucija (nivo 2–3): svaki path segment posle category MORA biti validan child prethodnog; nevalidan chain → Http404**

**Given** chain Plugovi (parent=None) → Plugovi obrtači (parent=Plugovi)
**When** posetim `/sr/mehanizacija/prikljucna/osnovna-obrada-zemljista/plugovi/plugovi-obrtaci/`
**Then** view resoluje: segment `plugovi` = Subcategory(category=osnovna-obrada-zemljista, parent=None, slug=plugovi); segment `plugovi-obrtaci` = Subcategory(parent=plugovi, slug=plugovi-obrtaci)
**And** ako bilo koji segment ne postoji kao child prethodnog (ili category za prvi) → raise `Http404` (NE renderuj parcijalno)
**And** ako se URL depth ne poklapa sa stvarnim chain-om (npr. slug postoji ali pod drugim parent-om) → `Http404`
**And** URL-level depth enforcement: putanja sa više segmenata nego što lanac može da resolvuje — uključujući >3 subcategory segmenta posle `<category-slug>` (preko `_SUBCATEGORY_MAX_DEPTH = 3`) — MORA vratiti Http404 jer chain resolution otkaže na prvom neresolvabilnom segmentu (ne postoji takvo dete); važi strategijski-nezavisno (drži i kad SM-D6 bira 3 eksplicitne putanje — 4. nivo nema URL pattern — i kad bi se koristio catch-all). Vidi AC13 + test `test_url_depth_exceeds_max_returns_404`.

**AC4 — Intermediate vs leaf odluka iz strukture podataka (NE iz fiksnog depth-a)**

**Given** trenutni nivo resoluje na Category ili Subcategory X
**When** view gradi context
**Then** ako X IMA decu-potkategorije (`children.exists()` za Subcategory, ili `subcategories.filter(parent=None).exists()` za Category root) → INTERMEDIATE: context sadrži `children` (lista Subcategory) i `is_leaf=False`
**And** ako X NEMA dece → LEAF: context sadrži `products` (`Product.objects.filter(subcategory=X, is_published=True)`) i `is_leaf=True`
**And** precedence (mešovit čvor): ako čvor ima ISTOVREMENO decu-subkategorije I direktno vezane Product zapise → deca POBEĐUJU → renderuje se INTERMEDIATE (subcategory cards); sopstveni Product zapisi tog čvora se IGNORIŠU na tom nivou (children win). Vidi AC14 + test `test_mixed_node_children_win_intermediate`.
**And** Category root je UVEK intermediate: `Product.subcategory` je FK ka Subcategory (nikada ka Category), pa Category root ne može biti leaf. Category bez ijedne potkategorije renderuje empty-intermediate stanje „Nema dostupnih potkategorija." per SM-D11.

**AC5 — Intermediate nivo renderuje subcategory kartice (REUSE coric-category-card 1:1)**

**Given** intermediate nivo sa `children` listom
**When** strana se renderuje
**Then** renderuje grid `coric-category-card` kartica (REUSE Story 2-10 BEM + category-showcase.css), po jedna per child Subcategory: ikona (CONDITIONAL `{% if subcategory.icon %}` — v1 prazan, Story 9-10 wire) + naziv (`subcategory.name`, pune dijakritike) + opis (`subcategory.description|truncatewords`) + „POGLEDAJ" CTA → `subcategory.get_absolute_url`
**And** prazna `children` lista → `{% empty %}` „Nema dostupnih potkategorija."
**And** svaka kartica ima `data-testid="subcategory-card-{slug}"` + CTA `data-testid="subcategory-card-cta-{slug}"`.

**AC6 — Leaf nivo renderuje MODEL kartice sa slikom + nazivom + ključnim specifikacijama + CTA**

**Given** leaf nivo sa `products` listom (publikovani Product vezani za leaf Subcategory)
**When** strana se renderuje
**Then** renderuje grid `coric-product-card` kartica (REUSE Story 2-8 BEM iz tractor-listing.css), po jedna per Product: `responsive_picture(product.main_image)` (renderuje se ako main_image postoji) + naziv (`product.name`) + deterministički spec fields + „OPŠIRNIJE" CTA
**And** spec fields pravilo (deterministički): renderuj `horse_power` (sa sufiksom „ KS") AKO nije null; renderuj `price_eur` (formatiran sa € per project-context) AKO nije null; ako su OBA null → ne renderuje se nijedan spec field, a kartica ostaje validna (slika + ime + CTA)
**And** cela kartica je `<a href="{{ product.get_absolute_url }}">` koji vodi na products:detail (Story 2-7)
**And** prazna `products` lista → `{% empty %}` „Nema dostupnih modela u ovoj kategoriji."
**And** empty-state (samo-unpublished): leaf čiji su SVI Product zapisi `is_published=False` daje prazan grid → prikazuje empty-state „Nema dostupnih modela u ovoj kategoriji." (isto stanje kao leaf bez ijednog proizvoda); pokriveno testom `test_leaf_all_unpublished_shows_empty_state`
**And** svaka kartica ima `data-testid="model-card-{slug}"`
**And** view query-uje Product READ-ONLY (SM-D16) sa `select_related`/prefetch da izbegne N+1 (vidi AC10).

**AC7 — Breadcrumb navigacija na vrhu svakog nivoa**

**Given** bilo koji nivo (1–3)
**When** strana se renderuje
**Then** na vrhu (pre h1) renderuje se `<nav aria-label="...">` breadcrumb sa `<ol>`:
- „Početna" (link → konkretan home URL pattern `core:home`, live u `apps/core/urls.py` — `{% url 'core:home' %}`)
- „Priključna mehanizacija" (link → `brands:jeegee_prikljucna`)
- `<Category.name>` (link → category root listing preko `brands:subcategory_listing_l1` sa `category_slug`) — UVEK prisutan od nivoa 1
- za svaki ancestor Subcategory u chain-u (`get_ancestors_chain()`): `<name>` (link → njegov listing URL preko `subcategory_listing_l1` / `_l2` / `_l3` po dubini ancestora — vidi `get_absolute_url()` u AC8 + binding SM-D6)
- trenutni nivo: `<name>` NIJE link, ima `aria-current="page"`
**And** breadcrumb redosled je root-first (Početna prvo, trenutni nivo zadnji)
**And** breadcrumb partial ima `data-testid="breadcrumb-nav"`; trenutni item `data-testid="breadcrumb-current"`.

**AC8 — Subcategory.get_absolute_url() implementiran (model promena bez šeme/migracije)**

**Given** `Subcategory.get_absolute_url()` koji trenutno raise `NotImplementedError`
**When** Dev implementira metodu
**Then** vraća validan path `/mehanizacija/prikljucna/<category-slug>/<...ancestor-subcat-slugs.../><self-slug>/` koristeći `reverse()` + `get_ancestors_chain()` za chain konstrukciju; metoda bira pattern ime po `get_depth()` (binding SM-D6): depth 1 → `reverse('subcategory_listing_l1', kwargs={category_slug, l1_slug})`; depth 2 → `reverse('subcategory_listing_l2', kwargs={category_slug, l1_slug, l2_slug})`; depth 3 → `reverse('subcategory_listing_l3', kwargs={category_slug, l1_slug, l2_slug, l3_slug})`
**And** EKSPLICITNO mapiranje `get_depth()` → ime pattern-a → kwargs (NEMA off-by-one): Subcategory sa `get_depth() == N` mapira se na pattern `subcategory_listing_lN`, a taj pattern prima `category_slug` (iz `self.category.slug`) PLUS TAČNO N subcategory slug-ova. Tih N slug-ova su N-1 slug-ova predaka (iz `get_ancestors_chain()` u root-first redosledu) PRAĆENI sa `self.slug`. Konkretno: top-level Subcategory (`parent=None`) ima `get_depth() == 1` → `subcategory_listing_l1` → `category_slug` + 1 subcat slug (`self.slug`); `get_depth() == 2` → `subcategory_listing_l2` → `category_slug` + 2 subcat slug-a (1 ancestor + `self.slug`); `get_depth() == 3` → `subcategory_listing_l3` → `category_slug` + 3 subcat slug-a (2 ancestora + `self.slug`). Relacija je jednoznačna: dubina N ⇒ pattern `lN` ⇒ `category_slug` + N subcat slug-ova; broj subcategory slug kwargs UVEK = `get_depth()` (NIKAD off-by-one između dubine lanca i broja URL slug kwargs)
**And** round-trip zahtev: za SVAKI nivo (depth 1, 2 I 3) `resolve(get_absolute_url())` MORA da vrati nazad isti čvor (URL → view → kwargs → isti Subcategory); round-trip assertion je obavezna na sva tri nivoa, ne samo na jednom (test `test_get_absolute_url_roundtrip_depth_1_2_3`)
**And** NEMA nove migracije (metoda nije DB polje); postojeći `NotImplementedError` raise se uklanja (SM-D8).

**AC9 — 2-10 placeholder href → {% url %} refactor (DUG iz Story 2-10 SM-D5)**

**Given** Story 2-10 `templates/brands/partials/_category_showcase.html` placeholder href (live na liniji 25) `/{{ LANGUAGE_CODE }}/mehanizacija/prikljucna/{{ category.slug }}/`
**When** Story 2-11 registruje named URL pattern za nivo-1 drill
**Then** Dev refaktoriše placeholder u `{% url %}` tag sa konkretnim pattern imenom per binding SM-D6: `{% url 'brands:subcategory_listing_l1' category_slug=category.slug %}`
**And** Jeegee landing CTA i dalje vodi na isti rezultujući path (`/sr/mehanizacija/prikljucna/<slug>/`) ALI sada kroz reverse resolution (NoReverseMatch ako pattern signature pogrešan — fail-fast)
**And** postojeći Story 2-10 testovi za `_category_showcase.html` (`apps/brands/tests/test_jeegee_prikljucna_templates.py`) i dalje PASS (href produkuje isti path; regression guard).

**AC10 — Query budget + N+1 zaštita (cross-boundary Product read SM-D16)**

**Given** view koji resoluje chain + gradi context
**When** stranica se renderuje
**Then** chain resolucija MORA biti optimizovana: ne sme generisati 1 SQL po path segmentu nekontrolisano (vidi SM-D12 — `select_related('parent', 'parent__parent', 'category')` ili batch fetch chain)
**And** breadcrumb gradnja koristi `get_ancestors_chain()` koje NE sme N+1-ovati (Dev prefetch-uje chain ili koristi već-resolved instance)
**And** leaf model-card render NE sme N+1-ovati na `product.main_image` / `product.brand` — Dev koristi `select_related('brand')` + sorl thumbnail pattern iz Story 2-8
**And** RED faza testira UPPER BOUND preko `assertNumQueries`: intermediate `assertNumQueries(<= 4)` i leaf `assertNumQueries(<= 4)` kao RED ceilings (AC10 je time testabilan već u RED-u sa konkretnim brojem)
**And** posle GREEN iteracije 1 Dev ZAKLJUČAVA TAČAN broj upita i pooštrava assertion na egzaktnu vrednost (align sa SM-D12).

**AC11 — i18n + a11y: pune dijakritike, gettext na svemu, aria-current, single-h1, semantic nav**

**Given** render-ovana strana na bilo kojem nivou
**When** se audit-uje
**Then** svi user-facing string-ovi (eyebrow, empty-states, breadcrumb labeli „Početna"/„Priključna mehanizacija", CTA tekstovi, aria-labeli) kroz `{% translate %}` / `{% blocktranslate %}` / `gettext_lazy`
**And** Subcategory.name + Category.name + Product.name renderuju se sa PUNIM dijakriticima (č/ć/ž/š/đ); NEMA ćirilice; NEMA šišane latinice
**And** breadcrumb je `<nav aria-label="...">` sa `<ol>`; trenutni item ima `aria-current="page"`
**And** TAČNO 1 `<h1>` na strani (naziv trenutnog nivoa); single `<main>` (iz base.html)
**And** model-card CTA + subcategory-card CTA imaju aria-label sa interpolovanim imenom (WCAG 2.1 SC 2.4.4 — link purpose in context).

**AC12 — Manual smoke + Lighthouse (Dev gate, NIJE automated)**

**Given** GREEN faza završena
**When** Dev ručno smoke-test-uje drill-down kroz 3 nivoa + breadcrumb back-navigaciju + keyboard tab order
**Then** Lighthouse a11y ≥ 95 (NFR-2 + UX-DR-13); keyboard navigacija prolazi kroz breadcrumb → kartice u prirodnom redu; NVDA najavljuje breadcrumb + trenutni nivo
**And** Dev čuva Lighthouse JSON artifact (mirror Story 2-10 AC9 pattern). (Real-browser keyboard + axe-core su Story 9-8/9-9 scope.)

**AC13 — URL-Level Depth Enforcement (>3 subcategory segmenata → Http404)**

**Given** URL putanju sa više segmenata nego što resolvabilni lanac dozvoljava (uključujući 4+ subcategory segmenta posle `<category-slug>`, preko `_SUBCATEGORY_MAX_DEPTH = 3`)
**When** korisnik pristupi takvoj putanji
**Then** vraća se Http404
**And** enforcement je na URL nivou, nezavisno od model `clean()` validacije pri kreiranju
**And** strategijski-nezavisno: drži i sa 3 eksplicitne putanje (per SM-D6 — 4. nivo nema URL pattern) i sa hipotetičkim catch-all (chain resolution otkaže na prvom neresolvabilnom segmentu — ne postoji takvo dete)
**And** pokriveno testom `test_url_depth_exceeds_max_returns_404` (vidi Test specification guidance).

**AC14 — Mixed Node Precedence (Children Win)**

**Given** čvor koji ima ISTOVREMENO child subcategories I direktno vezane Product zapise
**When** se određuje tip prikaza
**Then** deca pobeđuju → renderuje se kao intermediate (subcategory cards), a sopstveni Product zapisi tog čvora se ignorišu na tom nivou
**And** konzistentno je sa AC4 precedence pravilom
**And** pokriveno testom `test_mixed_node_children_win_intermediate` (vidi Test specification guidance).

## Tasks / Subtasks

### T1 — URL routing (AC1, AC3) — `apps/brands/urls.py`
- [x] Odluči pattern strategiju per SM-D6 (3 eksplicitna path-a sa fiksnim brojem `<slug:...>` kwargs, ILI 1 catch-all `<path:subpath>` — preporuka: 3 eksplicitna za type-safe reverse)
- [x] Dodaj path-ove POSLE `mehanizacija/prikljucna/` (statički — Story 2-10) tako da NE shadow-uje `JeegeePrikljucnaView`
- [x] Imenuj pattern(e): `subcategory_listing_l1/l2/l3` (eksplicitni, per SM-D6 (resolved) — uticaj na `get_absolute_url` reverse)
- [x] Verifikuj 0 kolizije sa `traktori/<slug>/` (brands), `proizvod/<slug>/` + `traktori/` + `mehanizacija/polovna/` (products)
- [x] Import `SubcategoryListView`

### T2 — View (AC2, AC3, AC4, AC10) — `apps/brands/views.py`
- [x] Dodaj `SubcategoryListView` (`TemplateView` ili `View` — SM-D4) POSLE `JeegeePrikljucnaView` (NE diraj postojeće klase)
- [x] Import `Subcategory` (EDIT postojeću `from apps.brands.models import ...` liniju); reuse `Product` import (SM-D16 read-only)
- [x] Resolve nivo 1: `Category.objects.get(slug=category_slug, is_for=MEHANIZACIJA)` → `Http404` ako miss/wrong-scope (AC2)
- [x] Resolve subcat chain: iteriraj URL segmente, svaki MORA biti child prethodnog (`category=...` za prvi, `parent=...` za ostale) → `Http404` na bilo kakav mismatch (AC3); optimizuj sa `select_related('parent')` (AC10, SM-D12)
- [x] Odluči intermediate vs leaf iz `children`/`subcategories` postojanja (AC4, SM-D11)
- [x] Intermediate: context `children` (ordered display_order, name) + `is_leaf=False`
- [x] Leaf: context `products` = `Product.objects.filter(subcategory=X, is_published=True).select_related('brand')` (+ thumbnail prefetch pattern iz 2-8) + `is_leaf=True` (AC6, AC10)
- [ ] Opciono leaf grouping po atributu (SM-D7 — vidi OQ-1; v1 verovatno NEMA grouping)
- [x] Build `breadcrumb_items` context (AC7) iz Category + `get_ancestors_chain()` + current
- [x] Empirijski lock query budget (`assertNumQueries`, SM-D12)

### T3 — Subcategory.get_absolute_url() (AC8) — `apps/brands/models.py`
- [x] Zameni `raise NotImplementedError` (linija ~411-414) implementacijom koja gradi path iz `category.slug` + `get_ancestors_chain()` slug-ovi + `self.slug` kroz `reverse()` (SM-D8)
- [x] Verifikuj round-trip: `resolve(subcat.get_absolute_url())` → `SubcategoryListView` + ispravni kwargs
- [x] Potvrdi NEMA nove migracije (metoda nije polje)

### T4 — Templates (AC5, AC6, AC7, AC11)
- [x] `templates/brands/subcategory_listing.html` (NOVO): extends base; breadcrumb include → h1 (trenutni nivo) → CONDITIONAL `{% if is_leaf %}_model_grid{% else %}_subcategory_showcase{% endif %}`; single-h1, single-main, NEMA inline style
- [x] `templates/brands/partials/_breadcrumb.html` (NOVO): `<nav aria-label>` + `<ol>`; iteriraj `breadcrumb_items`; current = `aria-current="page"` ne-link; data-testid (AC7)
- [x] `templates/brands/partials/_subcategory_showcase.html` (NOVO): Section Eyebrow + grid `coric-category-card` per child; CTA → `subcategory.get_absolute_url`; `{% empty %}`; data-testid (AC5, REUSE 2-10 BEM)
- [x] `templates/brands/partials/_model_grid.html` (NOVO): Section Eyebrow + grid `coric-product-card` per product; `responsive_picture(main_image)` + naziv + horse_power/price + CTA → `product.get_absolute_url`; `{% empty %}`; data-testid (AC6, REUSE 2-8 BEM)
- [x] Svi user-facing string-ovi kroz `{% translate %}`/`{% blocktranslate %}`; pune dijakritike; CTA aria-labeli (AC11)

### T5 — 2-10 href→{% url %} refactor (AC9) — `templates/brands/partials/_category_showcase.html`
- [x] Zameni placeholder `href="/{{ LANGUAGE_CODE }}/mehanizacija/prikljucna/{{ category.slug }}/"` sa `{% url %}` tag (tačan oblik per registrovan pattern + SM-D10 + per SM-D6 (resolved))
- [x] Verifikuj rezultujući path identičan (regression: Story 2-10 `test_jeegee_prikljucna_templates.py` i dalje PASS)

### T6 — CSS (AC7, AC11) — breadcrumb
- [x] `static/css/components/breadcrumb.css` (NOVO): `coric-breadcrumb` `<ol>` flex/inline + separator `›` (CSS `::before` content ili span) + link/current styling + responsive wrap + `:focus-visible`; sve `var(--token)`; NEMA inline style
- [x] `static/css/main.css` (EDIT): +1 `@import url('./components/breadcrumb.css');` POSLE category-showcase import
- [x] Verifikuj NE diraš category-showcase.css ni tractor-listing.css (REUSE 1:1)

### T7 — Locale (AC11) — 3 .po fajla
- [x] Dodaj + popuni msgstr za nove msgid u sr/hu/en (breadcrumb labeli, eyebrow, empty-states, aria-labeli, Http404 poruke)
- [x] `makemessages` → popuni → `compilemessages`

### T8 — Opciona seed migracija (SM-D14)
- [ ] (OPCIONO) `0004_seed_subcategory_hierarchy.py`: RunPython koji seed-uje sample Subcategory chain + Product za smoke demo; idempotent get_or_create + reverse_code; depends_on 0003
- [ ] Ako Dev skip-uje: dokumentuj u Dev Notes da AC pokriva test factory

### T9 — Manual smoke + Lighthouse (AC12)
- [ ] Drill-down 3 nivoa + breadcrumb back-nav + keyboard tab order
- [ ] Lighthouse a11y ≥ 95; sačuvaj JSON artifact

## Dev Notes

Jedinstvena ulazna tačka za implementaciju (pokazuje, ne duplira):

- Repository-delta tabela (sekcija "Repository Delta" niže): 5 NEW + 5 EDIT fajlova — to je kompletna lista artefakata.
- Binding OQ rezolucije:
  - OQ-1 (product grouping na leaf): v1 NEMA grouping → flat lista modela.
  - OQ-2 (subcategory image fallback): potvrđeno → placeholder slika ako je `subcategory.image` NULL.
  - OQ-3 (URL pattern signature): RESOLVED → 3 eksplicitne putanje per binding SM-D6 (`subcategory_listing_l1/l2/l3`).
- 3 load-bearing live-code sidra:
  - `apps/brands/models.py` — `Subcategory.get_absolute_url()` trenutno baca `NotImplementedError` (linije 411-414); ovaj story je implementira (AC8).
  - `apps/brands/models.py` — postojeći helperi `get_ancestors_chain()` (linija 413, za breadcrumb/AC7) i `get_depth()` (linija 420, za izbor pattern imena/AC8); REUSE, ne reimplementirati.
  - `templates/brands/partials/_category_showcase.html` — placeholder href `#` na liniji 25; refaktor na `reverse('subcategory_listing_l1', ...)` (AC9 / T5).
- Seed podaci dolaze iz `apps/brands/migrations/0003_seed_jeegee_and_prikljucna_categories.py` (read-only zavisnost; ne menja se).
## SM Decisions

**SM-D1 — Scope: hijerarhijski drill-down, NEMA HTMX.** Story 2-11 je pure server-side rendered drill-down (mirror 2-10 statički princip), svesno BEZ HTMX/JS/forma/paginacije/sort/filter. Razlika vs 2-8/2-9 je namerna — navigacija kroz stablo, ne filtriranje. Svaki nivo = jedan full-page render.

**SM-D2 — „4 nivoa" = Category root (1) + Subcategory chain MAX 3 (nivoi 2–4).** Reconciliacija sa Story 2-1: `Subcategory._SUBCATEGORY_MAX_DEPTH = 3` (validovano u `clean()`), kombinovano sa Category root daje 4 nivoa stabla. URL path segmenti posle `<category-slug>/` su Subcategory slug-ovi (1–3). Helper-i `get_ancestors_chain()` + `get_depth()` (Story 2-1 AC11) već postoje — REUSE za breadcrumb + depth.

**SM-D3 — Intermediate vs leaf je DATA-DRIVEN, ne depth-driven.** Nivo renderuje subcategory kartice ako trenutni čvor IMA decu; renderuje model-kartice ako NEMA dece. Ovo dozvoljava neravnomerno stablo (jedna grana leaf na nivou 2, druga na nivou 4). Epics.md primer „plugovi-obrtaci → grupisano po debljini grede" je leaf nivo (Plugovi obrtači nema dece-potkategorije; ima Product instance).

**SM-D4 — View bazna klasa: `TemplateView` (preporuka) ili custom `View`.** `DetailView` ne odgovara (varijabilan kwargs + nije single-object lookup po pk/slug na fiksnom modelu — trenutni „objekat" je ili Category ili Subcategory zavisno od depth-a). `TemplateView` sa `get_context_data()` koji resoluje chain je najčistije; `get_template_names()` može ostati fiksan (jedan template sa `{% if is_leaf %}` granom) — preferirano nad dva template-a (manje fajlova, jedan breadcrumb). Dev bira; preporuka `TemplateView`.

**SM-D5 — Subcategory showcase REUSE `coric-category-card` 1:1 (NOVI partial, ISTA BEM/CSS).** Subcategory kartica je vizuelno identična Category kartici (ikona+naziv+opis+CTA). REUSE `category-showcase.css` (Story 2-10 — NE edit). Kreira se NOVI partial `_subcategory_showcase.html` (a NE reuse 2-10 `_category_showcase.html`) jer: (a) 2-10 partial iterira `categories` context var + ima Jeegee-specific eyebrow tekst; (b) izbegava coupling 2-10 landing partial-a sa 2-11 drill view-om. Markup je near-identičan ali context var je `children` (Subcategory) + generički eyebrow. CSS klase identične → 0 nove CSS.

**SM-D6 — URL pattern signature (BINDING).** BINDING odluka: 3 eksplicitne URL putanje sa konkretnim pattern imenima:
- `subcategory_listing_l1` — kwargs: `category_slug` + `l1_slug`.
- `subcategory_listing_l2` — kwargs: `category_slug` + `l1_slug` + `l2_slug`.
- `subcategory_listing_l3` — kwargs: `category_slug` + `l1_slug` + `l2_slug` + `l3_slug`.

REJECTED alternativa: catch-all `<path:subpath>` (jedan pattern koji hvata proizvoljnu dubinu). Odbijeno jer otežava `reverse()` po nivou, briše URL-level depth ograničenje (pomera depth enforcement u view) i komplikuje breadcrumb/`get_absolute_url`. Eksplicitne putanje automatski daju URL-level depth cap na 3 (per AC3/AC13). **KRITIČNO:** svi path-ovi POSLE statičkog `mehanizacija/prikljucna/` (2-10) da ne shadow-uju Jeegee landing. Ova odluka je obavezujuća i napaja AC7 (breadcrumb reverse), AC8 (`get_absolute_url` po `get_depth()`) i AC9 (2-10 href refaktor koristi `subcategory_listing_l1`). Vidi OQ-3 (RESOLVED).

**SM-D7 — Leaf grouping po atributu (epics.md „90×90 … 160×160"): v1 NEMA dedicated model field — derived ILI deferred.** Product model (Story 2-2) NEMA „beam_thickness" polje. Opcije: (a) derive iz `ProductSpecification` (key=„Debljina grede") grupisanjem u view-u; (b) derive iz `Product.name` substring; (c) DEFER grouping na buduću story i v1 prikazuje flat model grid (preporuka za v1). Preporuka: **v1 leaf = flat model grid bez grouping-a** (epics.md grouping je nice-to-have; flat grid zadovoljava „prikazuje modele kao kartice"). Vidi OQ-1 — ako Mihas hoće grouping u v1, treba odlučiti izvor atributa. Markup `_model_grid.html` strukturiraj tako da grouping može biti dodat kasnije (opcioni `grouped_products` context).

**SM-D8 — `Subcategory.get_absolute_url()` implementacija: NEMA migracije.** Metoda (ne DB polje) — implementacija menja samo Python, NEMA `makemigrations` output. Gradi path iz `self.category.slug` + `get_ancestors_chain()` slug-ovi + `self.slug` kroz `reverse(name, kwargs=...)`. Uklanja postojeći `raise NotImplementedError`. Verifikuj round-trip resolve. **Eksplicitna dubina→ime→kwargs usklađenost (vidi AC8, NEMA off-by-one):** za `get_depth() == N` metoda bira pattern `subcategory_listing_lN` i prosleđuje `category_slug` (iz `self.category.slug`) PLUS TAČNO N subcategory slug-ova = N-1 slug-ova predaka iz `get_ancestors_chain()` (root-first) + `self.slug`. Broj subcategory slug kwargs UVEK = `get_depth()` (1→1, 2→2, 3→3); top-level (`parent=None`) je depth 1 → `l1`. Time je depth→name→kwargs relacija jednoznačna i Dev je ne može pogrešno poravnati.

**SM-D9 — Breadcrumb: server-rendered `<nav><ol>` partial, context-driven.** View gradi `breadcrumb_items` listu dict-ova (`label`, `url`, `is_current`); partial iterira. Root-first redosled. „Početna" → home `/`; „Priključna mehanizacija" → `brands:jeegee_prikljucna`; Category → category root listing; svaki ancestor → njegov listing; current = ne-link `aria-current="page"`. Nova `breadcrumb.css` komponenta (jedina nova CSS).

**SM-D10 — 2-10 href→{% url %} refactor je OBAVEZAN deo ove story (AC9).** Story 2-10 SM-D5 eksplicitno je ostavio placeholder direct-string href jer named pattern nije postojao; 2-10 § Out-of-scope navodi „Story 2-10 CTA href je placeholder ... 404 dok 2-11 ne dođe". Ova story registruje pattern → MORA konvertovati `_category_showcase.html` href u `{% url %}`. Tačan oblik (binding SM-D6): zameniti placeholder `#`/direct-string href (live na liniji 25 u `templates/brands/partials/_category_showcase.html`) sa `{% url 'brands:subcategory_listing_l1' category_slug=category.slug %}`. Regression: 2-10 template testovi MORAJU ostati zeleni (path output identičan). Ovo dodaje `_category_showcase.html` kao EDIT fajl.

**SM-D11 — Category bez potkategorija = prazan intermediate state (NE leaf).** Product.subcategory je FK na Subcategory (NE Category), pa Category sama NE drži Product-e direktno. Category root je UVEK intermediate; ako nema potkategorija → prikaže `{% empty %}` „Nema dostupnih potkategorija." (ne pokušava da fetch-uje Product po Category). Leaf je uvek Subcategory bez dece. Vidi OQ-2.

**SM-D12 — Query/N+1 strategija.** Chain resolucija: per-segment `.get()` je prihvatljiv za MAX 3 segmenta (3 upita ograničena), ALI Dev MOŽE optimizovati sa `select_related('parent', 'category')` na zadnjem segmentu + reverse-walk. Breadcrumb: `get_ancestors_chain()` već-resolved instance (NE re-query). Leaf products: `select_related('brand')` + sorl thumbnail prefetch (Story 2-8 pattern) — NE N+1 na main_image/brand. `children`: jedan `.filter().order_by('display_order', 'name')` materijalizovan u `list()`. Query budget je testabilan u RED-u preko `assertNumQueries` GORNJE granice: intermediate `<= 4` i leaf `<= 4` kao RED ceiling. Dev zaključava TAČAN broj posle GREEN iteracije 1 i pooštrava assertion na egzaktnu vrednost (align sa AC10).

**SM-D13 — Cross-boundary brands→products READ-ONLY (SM-D16 precedent).** `SubcategoryListView` (brands modul) query-uje `apps.products.models.Product` SAMO za read (leaf model grid). NEMA write na Product, NEMA brand→product FK. Ovo je isti view-layer-only coupling kao Story 2-6 `BrandDetailView` (dokumentovano u project-context.md § Cross-boundary „Exception" + Story 2-6 SM-D16). Import `from apps.products.models import Product` već postoji u `apps/brands/views.py:20`.

**SM-D14 — Seed migracija 0004 OPCIONA (ne blokira AC).** AC se mogu zadovoljiti kroz test factory (CategoryFactory iz Story 2-10 + nova SubcategoryFactory + ProductFactory). Sample hijerarhija u DB je korisna za manual smoke (AC12) ali Dev MAY skip ako test pokriva sve i smoke koristi shell-kreirane podatke. Ako se dodaje: idempotent get_or_create + reverse_code, depends_on 0003.

**SM-D15 — Slug reconciliacija epics-vs-0003: AUTHORITATIVE su 0003/2-10 dugi slug-ovi.** Epics.md koristi skraćene primere (`osnovna-obrada`, `plugovi-obrtaci`), ali Story 2-10 seed migracija 0003 (live `apps/brands/migrations/0003...py` + 2-10 contract) seed-uje **dugi authoritative Category slug set**: `osnovna-obrada-zemljista`, `priprema-zemljista`, `masine-za-setvu`. Story 2-11 MORA koristiti TE slug-ove za Category root resoluciju (AC2). Subcategory slug-ovi (plugovi, plugovi-obrtaci, podrivaci, gruberi, …) NISU još seed-ovani u 0003 — definišu se kroz admin (Story 8-5) ili opcionu 0004 (SM-D14) ili test factory; ASCII konvencija: `plugovi-ravnjaci`, `plugovi-obrtaci` (NE dijakritike). Epics.md skraćeni primeri su ILUSTRATIVNI — NE menjati 0003.

**SM-D16 — Pune dijakritike u name poljima, ASCII u slug-ovima.** `Category.name`/`Subcategory.name`/`Product.name` renderuju se sa č/ć/ž/š/đ (npr. „Podrivači", „Mašine za setvu"). URL slug-ovi su ASCII (`podrivaci`, `masine-za-setvu`) kroz `slugify_ascii` (Story 2-1). NEMA ćirilice, NEMA šišane latinice u user-facing tekstu.

## Open Questions

**OQ-1 (leaf grouping po atributu — potreban human/PO input):** Epics.md spominje „grupisani po debljini grede (90×90, 100×100, 120×120, 140×140, 160×160)" na leaf nivou (Plugovi obrtači). Product model (2-2) NEMA strukturisano polje za debljinu grede. **SM preporuka za v1: flat model grid bez grouping-a** (SM-D7 opcija c). Ako PO/Mihas zahteva grouping u v1, treba odlučiti IZVOR: (a) novo Product polje + migracija (van trenutnog „NEMA šeme promene" scope-a → eskalira na novu story ili scope expansion), (b) derive iz `ProductSpecification` key=„Debljina grede" (zahteva seed/admin konvenciju), (c) derive iz name. NE izmišljam kontrakt — Dev gradi flat grid dok PO ne potvrdi grouping.

**OQ-2 (Category-direct products — potvrda):** Potvrđeno iz modela: `Product.subcategory` je FK na Subcategory (nullable), NE na Category. Category sama NE drži Product-e. SM-D11 tretira Category root kao UVEK intermediate. Pitanje za arhitektu: postoji li use-case gde Category bez potkategorija treba da prikaže Product-e direktno (Product.subcategory=None ali brand=Jeegee)? Trenutno NE — top-level Jeegee landing (2-10) i ovaj drill ne fetch-uju Product bez subcategory. Ako se pojavi (Jeegee proizvod bez subcategory drill-a), treba odluka. SM pretpostavka: NE u Epic 2 scope-u.

**OQ-3 (URL pattern signature — RESOLVED, SM-D6 binding):** RESOLVED — 3 eksplicitne putanje `subcategory_listing_l1/l2/l3` (catch-all `<path:subpath>` odbijen). Vidi SM-D6 za binding signature. `Subcategory.get_absolute_url()` (AC8) bira ime po `get_depth()`; 2-10 href (AC9) koristi `subcategory_listing_l1`. Istorijski zapis (prethodno otvoreno pitanje 3 eksplicitna path-a vs 1 catch-all) zadržan radi sledljivosti; TEA može hardkodovati finalna imena `subcategory_listing_l1/l2/l3` u RED testovima.

## Test specification guidance (TEA RED phase)

AC→test mapping + rough count (mirror Story 2-10 § 11 stil; finalni naziv URL pattern-a parametrizovati po OQ-3):

| AC | Test fajl | Rough count |
|---|---|---|
| AC1 URL routing (3 nivoa × resolve + 200 + locale + no-shadow + no-collision) | `apps/brands/tests/test_subcategory_listing_urls.py` | 6 |
| AC2 Category root resolucija + Http404 (miss + wrong scope) | `apps/brands/tests/test_subcategory_listing_view.py` | 3 |
| AC3 chain resolucija + Http404 (invalid segment, wrong parent, depth mismatch) | `apps/brands/tests/test_subcategory_listing_view.py` | 4 |
| AC3/AC13 URL-level depth >MAX → 404 (`test_url_depth_exceeds_max_returns_404`) | `apps/brands/tests/test_subcategory_listing_urls.py` | 1 |
| AC4 intermediate vs leaf data-driven odluka | `apps/brands/tests/test_subcategory_listing_view.py` | 3 |
| AC4/AC14 mixed node (deca + products) → children win intermediate (`test_mixed_node_children_win_intermediate`) | `apps/brands/tests/test_subcategory_listing_view.py` | 1 |
| AC5 intermediate subcategory cards (REUSE coric-category-card) + empty | `apps/brands/tests/test_subcategory_listing_templates.py` | 4 |
| AC2/AC5 deterministički redosled dece: `display_order` pa `name` tiebreak kad je `display_order` isti (`test_children_order_display_order_then_name_tiebreak`) | `apps/brands/tests/test_subcategory_listing_view.py` | 1 |
| AC6 leaf model cards + CTA→product detail + empty | `apps/brands/tests/test_subcategory_listing_templates.py` | 4 |
| AC6 leaf gde su SVI Product `is_published=False` → empty-state „Nema dostupnih modela u ovoj kategoriji." (`test_leaf_all_unpublished_shows_empty_state`) | `apps/brands/tests/test_subcategory_listing_templates.py` | 1 |
| AC7 breadcrumb (struktura, root-first, aria-current, links) | `apps/brands/tests/test_subcategory_listing_templates.py` | 4 |
| AC8 Subcategory.get_absolute_url() + obavezan round-trip `resolve()` na depth 1, 2 I 3 + no NotImplementedError (`test_get_absolute_url_roundtrip_depth_1_2_3`) | `apps/brands/tests/test_subcategory_get_absolute_url.py` | 5 |
| AC9 2-10 href→{% url %} refactor (path identičan + 2-10 testovi PASS regression) | `apps/brands/tests/test_subcategory_listing_templates.py` (+ existing 2-10 suite green) | 2 |
| AC10 query budget / N+1 (assertNumQueries intermediate + leaf) | `apps/brands/tests/test_subcategory_listing_view.py` | 2 |
| AC11 i18n + a11y (gettext audit, dijakritike, aria-current, single-h1, CTA aria-label) | `apps/brands/tests/test_subcategory_listing_templates.py` | 4 |
| AC12 manual smoke + Lighthouse | (MANUAL — Dev gate, NIJE automated) | — |
| AC7/static-assets (REQUIRED RED deliverable) breadcrumb.css BEM + main.css @import + NO-EDIT guard (category-showcase.css, tractor-listing.css) | `apps/brands/tests/test_subcategory_listing_static_assets.py` | 4 |

**Required total: 44 testova** (URL + view + templates + get_absolute_url + static-asset suite). `test_subcategory_listing_static_assets.py` je OBAVEZAN RED deliverable (NIJE više opciona preporuka): verifikuje breadcrumb.css BEM selektore + main.css `@import` prisutnost + NO-EDIT guard za `category-showcase.css` i `tractor-listing.css`. Dodatni RED redovi gore (depth-404, mixed-node, order-tiebreak, all-unpublished empty-state, round-trip depth 1/2/3) uračunati su u 44.

**Test factory:** REUSE `CategoryFactory` (Story 2-10 `apps/brands/tests/factories.py`); TEA dodaje `SubcategoryFactory` (sa `category` + opcioni `parent` kwarg za chain) i koristi postojeći ProductFactory (apps/products) za leaf. Chain depth ≤ 3 (model `clean()` enforce-uje).

**Što TEA/Dev MORA znati:** (1) finalni URL pattern naziv NIJE lock-ovan dok Dev ne reši OQ-3 — parametrizuj testove na resolved name; (2) leaf grouping (OQ-1) je v1-flat dok PO ne potvrdi — NE piši testove za beam-thickness grouping u RED; (3) AC9 regression — postojeća Story 2-10 `test_jeegee_prikljucna_templates.py` MORA ostati zelena posle href refactora.
