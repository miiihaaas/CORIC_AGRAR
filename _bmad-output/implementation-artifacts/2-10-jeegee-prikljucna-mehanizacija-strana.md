---
story_id: "2.10"
story-key: 2-10-jeegee-prikljucna-mehanizacija-strana
title: Jeegee Priključna Mehanizacija Strana
status: ready-for-dev
epic: 2
epic_num: 2
epic_title: Public Catalog — Browse Brands & Products
module: brands
created: 2026-05-30
last_modified: 2026-05-30
complexity: S-M
author: Mihas (SM autonomous; STATIC content story — NEMA HTMX filtera, NEMA paginacije, NEMA sort dropdown-a; REUSE Story 2-6 BrandDetailView pattern + Story 1-7 Repeating Element jeegee variant + Story 1-7 hero_overlay_card partial + Story 1-7 section_eyebrow partial + Story 1-7 pill_button partial; PRVA story u Epic 2 koja koristi NE-tractor brand listing pattern — brendovi sa nullable Product.series gde subcategory-based grouping zamenjuje series-based grouping per Story 2-6 SM-D17; uvodi `coric-category-card` BEM kao kanonski 3-card / 4-card category showcase pattern koji Story 2-12 HZM + 2-11 Subcategory listing REUSE-uju)
depends_on:
  - 2-1-brand-series-category-subcategory-modeli  # Brand, Category (is_for="mehanizacija"), Subcategory; CategoryScope.MEHANIZACIJA TextChoices
  - 2-3-image-pipeline-sa-sorl-thumbnail-responsive-srcset  # {% responsive_picture %} za brand logo render
  - 2-6-brand-listing-strana-sa-grid-extended-layout-om     # BrandDetailView CBV pattern, hero_overlay_card include, _hero_section.html partial pattern, Repeating Element variant mapping, coming_soon template branching, get_template_names() override, cross-boundary brands → products import precedent (SM-D16 Exception), is_coming_soon → brand_coming_soon.html re-use 1:1
  - 2-7-product-detail-strana                                # _testimonials_slider.html shared lokacija (templates/partials/) iz Story 2-7 SM-D23/D27 cascade refaktoring — N/A za Story 2-10 (NEMA testimonijala u v1)
---

# Story 2.10: Jeegee Priključna Mehanizacija Strana

Status: ready-for-dev

## Opis

As a **posetilac (poljoprivrednik koji traži priključnu mehanizaciju i u browser-u otvara Jeegee landing stranu kroz Home strane „Mehanizacija" sekciju ili direct deep-link `/sr/mehanizacija/prikljucna/`; Đorđe — Mihasov klijent koji testira sa tastature i NVDA na mobilnom 375px ekranu)**,

I want **da otvorim Jeegee priključnu mehanizaciju landing stranu na URL `/sr/mehanizacija/prikljucna/` i vidim: (1) Jeegee hero overlay karticu sa Jeegee logom + sloganom (opciono `brand.slogan` ako postoji) + PLAVOM (JEEGEE) varijantom Repeating Element watermark-a (REUSE Story 1-7 `repeating_element.html` `variant="jeegee"` koji rezolvira na `coric-repeating-element--jeegee` BEM klasu koja maps na `--color-jeegee-blue` token #00a4e9 iz Story 1-5 tokens.css); (2) 3-card category showcase ispod hero-a sa karticama za 3 mehanizacija kategorije: „Osnovna obrada zemljišta", „Priprema zemljišta", „Mašine za setvu" — svaka kartica sadrži ikonu (Story 9-10 deferred — placeholder ili Bootstrap Icon class iz `Category.icon` polja koje JE renderuje samo ako vendor font postoji; v1 fallback je samo naziv + opis) + naziv kategorije + kratak opis (`Category.description` polje) + „POGLEDAJ KATEGORIJU" CTA dugme koje linkuje na placeholder URL `/sr/mehanizacija/prikljucna/<category-slug>/` (URL pattern dolazi u Story 2-11 Subcategory Listing; v1 link je placeholder anchor href koji raise NoReverseMatch tokom render-a IZUZEV ako Story 2-11 dođe pre 2-10, što neće — vidi SM-D5 za handling); (3) opciono „Preuzmi Jeegee katalog" CTA banner na dnu ako `jeegee_brand.catalog_pdf` postoji (mirror Story 2-6 AC3 § Preuzmi katalog CTA, koristi Wave Divider iznad — REUSE Story 1-7 partial)**,

so that **brzo (3 klika max sa Home strane: Home → „Mehanizacija" → „Priključna" → kategorija) navigiram do željene priključne kategorije u svojoj radnoj nameni (Marko klikne „Osnovna obrada zemljišta" jer mu treba plug; Đorđe NVDA mu najavi „Jeegee priključna mehanizacija, region; Osnovna obrada zemljišta, link" — keyboard tab vodi kroz hero → 3 kategorije → katalog CTA u prirodnom redu); strana zadovoljava Lighthouse a11y skor ≥ 95 (UX-DR-13 + NFR-2 + Story 9-9 a11y audit gate), poštuje single-h1 pravilo (`<h1>` je „Jeegee" iz hero card-a), koristi `<section>` semantic HTML5 za sve sekcije, i postavlja kanonski **3-card / 4-card category showcase pattern** koji Story 2-12 (HZM Radne Mašine sa 4 potkategorije) i Story 2-11 (Subcategory listing na nižim nivoima hijerarhije) REUSE-uju 1:1 (`coric-category-card` BEM komponenta uvodi se ovde kao site-wide reusable kartica za bilo koji „category showcase grid" use-case)**.

Ova story je **PRVA non-tractor brand listing strana u Epic 2** — Story 2-6 (BrandDetailView za tractor brendove) je uveo series-based grupisanje koje pretpostavlja `Product.series` FK postavljen (per Story 2-6 SM-D17: tractor brendovi imaju series; mehanizacija brendovi NEMAJU); Jeegee brand ima Product proizvode sa `Product.series = NULL` + `Product.subcategory` postavljenom (PR-D2 iz Story 2-2). Story 2-10 je **DIFERENTNI pattern** od Story 2-6 — NE renderuje series sekcije, NE renderuje statistike-medaljone, NE renderuje testimonijale, NE renderuje grid/extended layout branching; umesto toga renderuje **statički 3-card category showcase** koji direktno linkuje na sledeći nivo URL hijerarhije.

**Strana NEMA HTMX, NEMA JavaScript interakciju, NEMA forme, NEMA paginaciju, NEMA sort, NEMA filtere — pure server-side rendered static content layout.** Razlika u odnosu na Story 2-8/2-9 (HTMX filteri sa range slidera) je kritična: Story 2-10 je čista landing strana koja samo navigira korisnika nadalje; sav „filtering" se dešava kroz kategorija dropdown u Story 2-9 (used machinery) ili kroz Subcategory listing u Story 2-11 (na nivou ispod). Ovo simplifikuje arhitekturu — view je trivijalan (1-2 SQL upita: Brand fetch + Category list); template je čist (hero + 3 kartice + opciono catalog CTA); CSS uvodi 1 novu komponentu (`coric-category-card`) site-wide reusable.

**Strana KORISTI sledeće artefakte iz prethodnih Story-ja (REUSE focus — 0 novih JS modula, 1 nova CSS komponenta):**

- **`Brand` model** (Story 2-1): `Brand.objects.get(slug="jeegee")` (vidi SM-D2 za seed/migracija strategiju — story uvodi Jeegee brand kao data migration). Polja korišćena: `brand.slug`, `brand.name`, `brand.logo`, `brand.slogan`, `brand.description`, `brand.brand_color`, `brand.catalog_pdf`, `brand.is_coming_soon`.
- **`Category` model** (Story 2-1): `Category.objects.filter(is_for=Category.CategoryScope.MEHANIZACIJA, slug__in=["osnovna-obrada-zemljista", "priprema-zemljista", "masine-za-setvu"]).order_by("display_order", "name")` — 3 fiksne kategorije za Jeegee landing. Polja korišćena: `category.slug`, `category.name`, `category.description`, `category.icon` (Bootstrap Icons class — v1 NIJE renderovan jer vendor font nije wired per Story 2-6 SM-D18; conditional render kroz `{% if category.icon %}` koji forever evaluuje na False u v1 — ali markup je postavljen za Story 9-10 polish koji wire-uje Bootstrap Icons font; klase ne smetaju ako se render-uju kao prazni `<i>` placeholder, pa će v1 prikazati samo naziv + opis bez ikone).
- **`CategoryScope.MEHANIZACIJA = "mehanizacija"` TextChoices** (Story 2-1, live `apps/brands/models.py:249`) — koristi se u view-u za scope filter.
- **`{% responsive_picture %}` template tag** (Story 2-3) — za brand.logo render (u hero_overlay_card.html partial — delegated render po Story 2-6 hero pattern; Story 2-10 ne renderuje direktno responsive_picture za brand logo).
- **`templates/partials/hero_overlay_card.html`** (Story 1-7) — REUSE 1:1; prima `title=brand.name`, `brand_logo=brand.logo.url|default:""`, `brand_logo_alt=brand.name`, `variant="jeegee"`, `bullets=""` (per Story 2-6 SM-D10 — hero bullets empty u v1).
- **`templates/partials/repeating_element.html`** (Story 1-7) — INDIREKTNO koristi kroz hero_overlay_card include sa `variant="jeegee"` kwarg-om; rezultuje u `coric-repeating-element--jeegee` BEM klasi (live verifikovano `static/css/components/repeating-element.css:14`).
- **`templates/partials/section_eyebrow.html`** (Story 1-7) — za UPPERCASE eyebrow naslov iznad category showcase grid-a („KATEGORIJE PRIKLJUČNE MEHANIZACIJE").
- **`templates/partials/pill_button.html`** (Story 1-7) — REUSE 1:1 za „POGLEDAJ KATEGORIJU" CTA dugmad u kategorija karticama (vidi SM-D6 — koristimo pill_button partial direktno jer nema target/rel/download requirements; razlika od Story 2-6 catalog CTA koji nije mogao koristiti pill_button jer treba target/rel atribute).
- **`templates/partials/wave_divider.html`** (Story 1-7) — za Wave Divider iznad „Preuzmi katalog" CTA banner-a (samo ako jeegee_brand.catalog_pdf postoji; mirror Story 2-6 _catalog_cta.html pattern).
- **`templates/brands/brand_coming_soon.html`** (Story 2-6) — REUSE 1:1 ako `jeegee_brand.is_coming_soon=True` (admin može privremeno setovati Jeegee brand kao coming-soon — npr. ako pripreme content nisu spremne; defensive guard u view-u kroz `get_template_names()` override mirror Story 2-6).
- **`brands` URL namespace + apps/brands/urls.py + apps/brands/views.py modul layout** (Story 2-6) — Story 2-10 dodaje 1 novi URL pattern i 1 novu CBV klasu unutar postojećih fajlova (NIJE novi modul).
- **CSS tokens** (`static/css/tokens.css`, Story 1-5): `--color-jeegee-blue` (#00a4e9, live verifikovano linija 94), `--color-brand-green-800`, `--color-neutral-cream`, `--color-neutral-white`, `--spacing-scale-*`, `--rounded-md`, `--typography-scale-h1/h2/h3/body`.
- **`coric-button` + `coric-button--primary` + `coric-button--secondary` BEM** (Story 1-7 `static/css/components/pill-button.css`) — REUSE za sve CTA dugmad.

**Foundation za buduće Story-je:**

- **Story 2-11 (Subcategory Listing 4-nivoa hijerarhija):** REUSE-uje `coric-category-card` BEM uvedeno ovde + ovaj URL pattern `/mehanizacija/prikljucna/<category-slug>/` rezolvuje SubcategoryListView; 3-card showcase pattern se reuse-uje za sub-podkategorije (npr. „Osnovna obrada" → 3 sub-kategorije: Plugovi, Podrivači, Gruberi — istih 3-card grid layout).
- **Story 2-12 (HZM Radne Mašine + Tulip MIX):** REUSE-uje `coric-category-card` BEM uvedeno ovde + `JeegeePrikljucnaView` pattern (1 brand → N kategorija showcase grid); HZM strana ima 4 potkategorije umesto 3 (Mini utovarivači, Utovarivači bez teleskopa, Teleskopski, Telehendleri); `coric-category-card` BEM je responsive (CSS Grid sa `auto-fit, minmax`) pa 3 vs 4 kartice automatski radi.
- **Story 3-1 (Home strana):** sekcija „Mehanizacija" Home strane prikazuje 3 brenda mehanizacije (Jeegee, HZM, Tulip) kao karticе — moguće reuse `coric-category-card` BEM ako se brand-level kartica vizuelno podudara (TBD u Story 3-1 SM).

**Princip:** Pure server-side rendering, **NEMA HTMX**, **NEMA JavaScript**, **NEMA forma**, **NEMA admin promena**, **NEMA migracije šeme** (ALI **JEDNA data migracija** koja seed-uje Jeegee Brand + 3 mehanizacija Category instance — vidi SM-D2). Vanilla Django CBV (DetailView slično Story 2-6 BrandDetailView, ali specijalizovan za Jeegee + 3-card showcase). CSS BEM sa `coric-` prefiksom + isključivo `var(--token)` reference iz `static/css/tokens.css`. Sve user-facing string-ove kroz `{% translate %}` / `gettext_lazy as _`. URL slug ASCII (`prikljucna` ne `priključna`; `osnovna-obrada-zemljista` ne `osnovna-obrada-zemljišta`).

**Strukturna arhitektura — repository delta:** Repo delta: **4 NEW + 6 EDIT + 0 DELETE + 1 data migracija** (kanonsko brojanje — prebrojivo iz tabele ispod):

| Path | Tip | Razlog |
|---|---|---|
| `apps/brands/views.py` | EDIT (ADD class) | Dodaje `JeegeePrikljucnaView(DetailView)` CBV (postojeća `BrandDetailView` iz Story 2-6 ostaje netaknuta); CBV implementira `get_object()` override koji vraća `Brand.objects.get(slug="jeegee")` (NEMA URL kwarg slug jer URL je statički `/mehanizacija/prikljucna/` — vidi SM-D3); `get_template_names()` override za coming-soon branching (REUSE pattern iz Story 2-6 SM-D19 — koristi se `brand_coming_soon.html` 1:1); `get_context_data()` dodaje `categories` queryset (3 fiksne mehanizacija kategorije ordered by display_order). Module-level Jeegee slug konstanta `_JEEGEE_BRAND_SLUG = "jeegee"`. Reuse postojeće `from apps.brands.models import Brand, Category` import-e (Brand već importovan, Category dodati). |
| `apps/brands/urls.py` | EDIT (ADD path) | Dodaje TAČNO 1 novi URL pattern POSLE postojećeg `traktori/<slug:slug>/`: `path("mehanizacija/prikljucna/", JeegeePrikljucnaView.as_view(), name="jeegee_prikljucna")`. **KRITIČNO (SM-D3):** URL `mehanizacija/prikljucna/` je dvoslojni statički path bez slug-a; NEMA URL kolizije sa nijednim postojećim pattern-om (apps/brands/urls.py:10 `traktori/<slug:slug>/`, apps/products/urls.py `proizvod/<slug>/`, `traktori/`, `mehanizacija/polovna/`). `mehanizacija/` prefix je slobodno dostupan u brands namespace-u (Story 2-9 `mehanizacija/polovna/` je registrovan u products namespace, ne brands — vidi config/urls.py:27-29 redoslijed include-ova). |
| `templates/brands/jeegee_prikljucna.html` | NOVO | Glavni template — `{% extends "base.html" %}`; outer `<section class="coric-brand-detail coric-jeegee-prikljucna" data-testid="jeegee-prikljucna-page" aria-label="{{ brand.name }} priključna mehanizacija">` (vidi SM-D8 — `aria-label` umesto `aria-labelledby` jer h1 unutar hero_overlay_card partial-a nema id); renderuje hero sekciju (REUSE `_hero_section.html` pattern iz Story 2-6 — vidi SM-D4 za REUSE vs new partial decision) → 3-card category showcase → opciono Wave Divider + „Preuzmi Jeegee katalog" CTA banner. **JEDAN `<h1>`** na strani (kroz `hero_overlay_card.html` partial — partial render-uje `<h1>` iz `title=brand.name` per Story 2-6 B1 fix); **single `<main>`** element (samo iz base.html — outer wrapper je `<section>` per Story 2-6 + 2-7 + 2-8 + 2-9 single-main konvencija). |
| `templates/brands/partials/_jeegee_hero.html` | NOVO | Hero wrapper partial — **NIJE REUSE postojećeg `_hero_section.html`** (vidi SM-D4 — Story 2-6 `_hero_section.html` ima conditional brand_color → variant branching koji je tractor-brand-generic; Jeegee uvek koristi `variant="jeegee"` hardcoded pa je čistije imati dedicated thin partial koji ne nosi conditional logiku). Wrapping `<div class="coric-brand-hero" data-testid="jeegee-hero">`; include-uje `partials/hero_overlay_card.html` sa fiksnim `variant="jeegee"`, `title=brand.name`, `brand_logo=brand.logo.url|default:""`, `brand_logo_alt=brand.name`, `bullets=""`. **TOTAL: 1 include statement.** |
| `templates/brands/partials/_category_showcase.html` | NOVO | 3-card grid wrapper sa Section Eyebrow + heading + grid wrapper koji iterira `categories` context queryset i renderuje per-category karticu. Markup per AC3 spec (vidi ispod) — koristi `coric-category-card` BEM (nova komponenta uvedena u ovoj story). |
| `static/css/components/category-showcase.css` | NOVO | Layout sekcija za `coric-category-showcase` wrapper grid + `coric-category-card` karticu (image/icon top + naziv + opis + CTA bottom); responzivni CSS Grid `repeat(auto-fit, minmax(280px, 1fr))` koji automatski handluje 3 vs 4 kartice (foundation za Story 2-12); hover/focus states + `@media (prefers-reduced-motion: reduce)` block koji uklanja transform animaciju. Sve vrednosti kroz `var(--token)`. |
| `static/css/main.css` | EDIT | Dodaje TAČNO 1 nova `@import url('./components/category-showcase.css');` linija (mirror Story 2-9 + 2-8 + 2-7 sintaksu — `url(...)` wrapper sa leading `./` + trailing semicolon). Pozicionira POSLE postojeće `@import url('./components/used-machinery-listing.css');` (Story 2-9 zadnja). |
| `apps/brands/migrations/0003_seed_jeegee_and_prikljucna_categories.py` | NOVO (data migracija) | RunPython data migracija koja kreira Jeegee Brand (slug="jeegee", name="Jeegee", brand_color="#00A4E9", is_coming_soon=False) + 3 mehanizacija kategorije (slug="osnovna-obrada-zemljista", name="Osnovna obrada zemljišta", is_for="mehanizacija", display_order=10; slug="priprema-zemljista", name="Priprema zemljišta", is_for="mehanizacija", display_order=20; slug="masine-za-setvu", name="Mašine za setvu", is_for="mehanizacija", display_order=30). Reverse callable (`reverse_code`) defined da delete-uje samo te 4 instance (slug-based lookup). Vidi SM-D2 za rationale. |
| `locale/sr/LC_MESSAGES/django.po` | EDIT | Popuni msgstr za sve nove msgid (page title, meta description, „KATEGORIJE PRIKLJUČNE MEHANIZACIJE" eyebrow, „Pregled priključne mehanizacije Jeegee...", „POGLEDAJ KATEGORIJU" CTA label, „Preuzmi Jeegee katalog" CTA label). Mehanizacija kategorija naming-i („Osnovna obrada zemljišta", „Priprema zemljišta", „Mašine za setvu") su Category.name polja koja se seed-uju u data migraciji — modeltranslation auto-translacija za hu/en je out-of-scope za ovu story (Story 2-1 D2 — auto-discovery registracija postoji; ali hu/en prevodi `name_hu`/`name_en` se popunjavaju u Story 8-5 Category admin ili manual u sledecim story-jama). v1 prikazuje srpski naziv na svim locale-ima — pragmatic per Story 2-6 § Multi-locale URL slug-ovi open question. |
| `locale/hu/LC_MESSAGES/django.po` | EDIT | Popuni hu prevode za nove msgid (template stringovi, NE Category.name polja). |
| `locale/en/LC_MESSAGES/django.po` | EDIT | Popuni en prevode za nove msgid. |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | EDIT | Postavi `2-10-jeegee-prikljucna-mehanizacija-strana` status na `ready-for-dev` (SM completion handoff). Counted separately u SM-D11 — NIJE deliverable file edit. |

**Brojanje (KANONSKO — single source of truth):** **4 NEW + 6 EDIT + 0 DELETE + 1 data migracija** (IMP-9 fix: ovo je SINGLE canonical brojanje; raniji iteracija spec-a je imao 5 EDIT → korekciju → korigovano brojanje u istom paragraphu — kompaktovano u 1 statement).

Razlaganje (prebrojiti iz tabele iznad):
- **4 NEW:** 1 main template (`jeegee_prikljucna.html`) + 2 partials (`_jeegee_hero.html`, `_category_showcase.html`) + 1 CSS komponenta (`category-showcase.css`).
- **6 EDIT:** `apps/brands/views.py` (ADD class) + `apps/brands/urls.py` (ADD path) + `static/css/main.css` (+1 `@import`) + 3 .po fajla (`locale/sr/LC_MESSAGES/django.po`, `locale/hu/LC_MESSAGES/django.po`, `locale/en/LC_MESSAGES/django.po`). Sprint-status.yaml update je rutinski SM handoff tracking, NIJE deliverable file edit (counted separately u SM-D11).
- **1 data migracija:** `apps/brands/migrations/0003_seed_jeegee_and_prikljucna_categories.py` — pure RunPython data migracija, NEMA model šeme promene (Story 2-1 modeli su nepromenjeni).

Postojeći fajlovi koji ostaju **NETAKNUTI** (regression guards): `apps/brands/models.py` (NEMA model promena — samo data; admin/translation/migrations 0001-0002 ostaju), `apps/brands/admin.py`, `apps/brands/translation.py`, `apps/brands/templates/brand_detail.html` + `brand_coming_soon.html` + `partials/_hero_section.html` + `partials/_statistics_medallions.html` + `partials/_testimonials_slider.html` (Story 2-7 cascade) + `partials/_series_section.html` + `partials/_series_grid.html` + `partials/_series_extended.html` + `partials/_catalog_cta.html` (Story 2-6 deliverables — Story 2-10 ne deli partials; ima vlastite `_jeegee_hero.html` i `_category_showcase.html`), `apps/products/` (kompletno netaknuto), `apps/core/`, `apps/media_pipeline/`, `config/urls.py` (URL include red ne menja se), `templates/base.html`, `templates/partials/*` (sve Story 1-7 partials — koriste se REUSE 1:1 bez izmena), `static/vendor/*` (NEMA novih vendor asset-a — NEMA noUiSlider potrebe jer NEMA range slidera), `static/js/*` (NEMA novih JS modula), `static/css/tokens.css`, `static/css/components/{header,footer,sticky-nav,lightbox,hero-overlay-card,repeating-element,pill-button,section-eyebrow,wave-divider,statistic-medallion,testimonials-slider,brand-listing,product-detail,product-gallery,product-variants,tractor-listing,used-machinery-listing,range-slider}.css`, `pyproject.toml`, `config/settings/`, `compose/django/Dockerfile`.

## Kriterijumi prihvatanja

**AC1 — URL pattern `/<lang>/mehanizacija/prikljucna/` rezolvuje `JeegeePrikljucnaView`; rezolucija prolazi i daje HTTP 200 za sva 3 locale; NEMA URL kolizije sa Story 2-6/2-8/2-9 pattern-ima**

- **Given** `apps.brands` registrovan u `INSTALLED_APPS`; `i18n_patterns()` aktivan iz Story 1-4; Story 2-6 je registrovala `apps/brands/urls.py` sa app_name="brands" + pattern `traktori/<slug:slug>/` (live verifikovano `apps/brands/urls.py:10`); Story 2-9 je registrovala `apps/products/urls.py` sa pattern `mehanizacija/polovna/` (live verifikovano `apps/products/urls.py:18-21`); `config/urls.py:27-29` učitava `apps.brands.urls` PRE `apps.products.urls` PRE `apps.core.urls`; Jeegee Brand instance postoji u DB (seed migracija per SM-D2)
- **When** dodajem `JeegeePrikljucnaView(DetailView)` u `apps/brands/views.py` (postojeća BrandDetailView ostaje netaknuta) i u `apps/brands/urls.py` dodajem novi pattern POSLE postojećeg `traktori/<slug:slug>/`:
  ```python
  path("mehanizacija/prikljucna/", JeegeePrikljucnaView.as_view(), name="jeegee_prikljucna"),
  ```
- **Then**:
  - `reverse("brands:jeegee_prikljucna")` vraća `/sr/mehanizacija/prikljucna/` kad je aktivan locale `sr` (analogno `/hu/mehanizacija/prikljucna/`, `/en/mehanizacija/prikljucna/`)
  - GET `/sr/mehanizacija/prikljucna/` vraća HTTP 200 (JeegeePrikljucnaView)
  - GET `/sr/traktori/<bilo-koji-slug>/` i dalje vraća HTTP 200 (BrandDetailView Story 2-6) — NIJE shadow-ovano
  - GET `/sr/mehanizacija/polovna/` i dalje vraća HTTP 200 (UsedMachineryListView Story 2-9) — NIJE shadow-ovano
  - GET `/sr/proizvod/<bilo-koji-slug>/` i dalje rezolvuje na ProductDetailView (Story 2-7) — NIJE shadow-ovano
  - GET `/sr/mehanizacija/prikljucna` (bez trailing slash) → Django `APPEND_SLASH` redirektuje na `/sr/mehanizacija/prikljucna/`
- **And** URL deconfliction provera (SM-D3): `mehanizacija/prikljucna/` je statički path bez slug converter-a; NEMA potencijalnog overlap-a sa postojećim pattern-ima. `mehanizacija/` prefix može i dalje biti reuse-ovan u Story 2-11 (`mehanizacija/prikljucna/<category-slug>/`) i Story 2-12 (`mehanizacija/radne-masine/`, `mehanizacija/mix-prikolice/`) bez koliziranja jer su sve statičke path komponente
- **And** `uv run python manage.py check` exit code 0; URL routing test asertuje SVA 4 pattern-a koegzistiraju
- **And** smoke verifikacija (mirror Story 2-9 AC1):
  ```bash
  uv run python manage.py shell -c "from django.urls import reverse; \
    from django.utils.translation import activate; activate('sr'); \
    print(reverse('brands:jeegee_prikljucna')); \
    print(reverse('brands:detail', kwargs={'slug': 'agri-tracking'})); \
    print(reverse('products:used_machinery_list'))"
  ```
  Očekivan output:
  ```
  /sr/mehanizacija/prikljucna/
  /sr/traktori/agri-tracking/
  /sr/mehanizacija/polovna/
  ```

**AC2 — `JeegeePrikljucnaView` (CBV `DetailView`) sa hardcoded Jeegee brand lookup (slug="jeegee"); `get_template_names()` branching za coming-soon (REUSE Story 2-6 SM-D19 pattern + brand_coming_soon.html template 1:1); `get_context_data()` dodaje `categories` queryset (3 fiksne mehanizacija kategorije ordered by display_order)**

- **Given** AC1; Brand i Category modeli iz Story 2-1; Jeegee Brand instance postoji u DB (seed migracija per SM-D2); Brand.is_coming_soon polje BooleanField (default False); CategoryScope.MEHANIZACIJA = "mehanizacija" TextChoices
- **When** dodajem `JeegeePrikljucnaView` u `apps/brands/views.py` POSLE postojeće `BrandDetailView` klase. Source skeleton (Dev MORA implementirati):

  **Module-level imports (PRE klase) — Dev MORA verifikovati šta postoji u `apps/brands/views.py:14-19` i ŠTA TREBA DODATI:**
  - `from django.db.models import Case, CharField, IntegerField, Prefetch, Value, When` — VEĆ POSTOJI (linija 14) — NE re-import; **N/A za Story 2-10** (NEMA Case/When potrebe — NEMA ProductSpecification akordion-a)
  - `from django.utils.translation import gettext_lazy as _` — VEĆ POSTOJI (linija 15)
  - `from django.views.generic import DetailView` — VEĆ POSTOJI (linija 16)
  - `from apps.brands.models import Brand, Series` — VEĆ POSTOJI (linija 18); **EDIT da postane `from apps.brands.models import Brand, Category, Series` (dodaj Category)** — Series ostaje za BrandDetailView, Category nova za JeegeePrikljucnaView
  - `from apps.products.models import Product, ProductSpecification, ProductTestimonial` — VEĆ POSTOJI (linija 19); **NE menja se** (BrandDetailView i dalje koristi te modele)
  - `from django.http import Http404` — **NE POSTOJI još** — **DODAJ** (canonical, MORA biti dodato; source skeleton ispod koristi `Http404` + explicit raise). **IMP-1 fix (lock):** koristi `from django.http import Http404` + explicit raise per source skeleton; **NE** `get_object_or_404`. Razlog: treba nam (a) custom porukа za 404 („Jeegee brand nije konfigurisan u sistemu.") koja se surface-uje u DEBUG=True dev mode + logs/Sentry; (b) explicit control flow u `get_object()` override-u (queryset građenje + try/except idiom). `get_object_or_404` shortcut bi sakrio control flow + ne podržava custom message string elegantno.

  **Module-level konstante (PRE klase, POSLE postojećih import-a):**
  ```python
  _JEEGEE_BRAND_SLUG = "jeegee"
  _PRIKLJUCNA_CATEGORY_SLUGS = (
      "osnovna-obrada-zemljista",
      "priprema-zemljista",
      "masine-za-setvu",
  )
  ```

  ```python
  class JeegeePrikljucnaView(DetailView):
      """Jeegee priključna mehanizacija landing strana — Story 2.10.

      Statička landing strana sa 3-card category showcase grid. NEMA HTMX,
      NEMA filtera, NEMA paginacije. Cross-boundary brands → products import
      NIJE potreban (view NE query-uje Product-e — samo Brand + Category).

      get_object() override vraća Jeegee Brand (slug='jeegee') jer URL je
      statički bez slug kwarg-a (SM-D3). get_template_names() koristi
      brand_coming_soon.html ako is_coming_soon=True (REUSE Story 2-6
      SM-D19 pattern + brand_coming_soon.html template 1:1).
      """

      model = Brand
      context_object_name = "brand"

      def get_object(self, queryset=None):
          # SM-D3: URL je statički /mehanizacija/prikljucna/ bez slug kwarg-a;
          # view hardcoduje Jeegee brand lookup. Ako Jeegee brand nije seed-ovan
          # (data migracija 0003 nije primenjena), raise 404 — defensive (SM-D7).
          if queryset is None:
              queryset = self.get_queryset()
          try:
              return queryset.get(slug=_JEEGEE_BRAND_SLUG)
          except Brand.DoesNotExist as exc:
              raise Http404(
                  _("Jeegee brand nije konfigurisan u sistemu.")
              ) from exc

      def get_template_names(self):
          # REUSE Story 2-6 SM-D19 pattern. Default DetailView.get() flow je:
          # get_object() -> self.object = ... -> get_context_data() -> render_to_response()
          # (koji onda interno poziva get_template_names()). Dakle self.object JE set
          # pre get_template_names() poziva — NEMA potrebe za custom get() override-om
          # (IMP-7 fix: prethodna iteracija je imala redundant get() override).
          if getattr(self, "object", None) is not None and self.object.is_coming_soon:
              return ["brands/brand_coming_soon.html"]
          return ["brands/jeegee_prikljucna.html"]

      def get_context_data(self, **kwargs):
          ctx = super().get_context_data(**kwargs)
          if self.object.is_coming_soon:
              # Minimal context za coming-soon — NEMA categories.
              return ctx
          # 3 fiksne mehanizacija kategorije (per epics.md Story 2.10 spec);
          # filter po is_for + slug whitelist garantuje precise set.
          ctx["categories"] = list(
              Category.objects.filter(
                  is_for=Category.CategoryScope.MEHANIZACIJA,
                  slug__in=_PRIKLJUCNA_CATEGORY_SLUGS,
              ).order_by("display_order", "name")
          )
          return ctx
  ```
- **Then**:
  - Query budget: **2 SQL upita** za render strane (lock-uje se u GREEN fix iter posle prvog `just test` runa — mirror Story 2-9 SM-D27 empirical-lock discipline):
    1. Brand fetch (`SELECT * FROM brands_brand WHERE slug = 'jeegee' LIMIT 1`)
    2. Categories list (`SELECT * FROM brands_category WHERE is_for = 'mehanizacija' AND slug IN (...) ORDER BY display_order, name`)
  - Context sadrži ključeve:
    - `brand` (Brand instance — Jeegee)
    - `categories` (list[Category] — 3 mehanizacija kategorije; lista je materijalizovana sa `list(...)` da template iteracija ne re-evaluuje queryset)
  - Ako `brand.is_coming_soon == True`, `get_template_names()` vraća `["brands/brand_coming_soon.html"]` (REUSE Story 2-6 template 1:1) i view renderuje minimal coming-soon template sa MINIMAL context-om (samo `brand` key); `categories` se NE fetch-uje
  - Ako Jeegee brand nije seed-ovan u DB (data migracija nije primenjena ili je manually obrisan), `get_object()` raise Http404 sa user-friendly porukom „Jeegee brand nije konfigurisan u sistemu." (defensive guard per SM-D7); test mora verifikovati ovo eksplicitno
- **And** view NE oslobađa eksplicitno `request.user` — anonimni view, javni katalog; `LoginRequiredMixin` se NE koristi
- **And** view NEMA cross-boundary import-e ka `apps.products.models` — Story 2-10 NE query-uje Product (NEMA series-based grupisanje, NEMA testimonijala iz Product-a, NEMA flat product grid); samim tim Story 2-6 SM-D16 cross-boundary exception NIJE primenjiv ovde (compliance sa project-context.md § Cross-boundary import bez exception-a)

**AC2.5 — `brand_coming_soon.html` REUSE za coming-soon stanje (Story 2-6 deliverable, 1:1 reuse — NEMA template kopiranja ili duplikacije)**

- **Given** AC2 završen; Story 2-6 deliverable `templates/brands/brand_coming_soon.html` postoji i renderuje minimalan markup (logo + naziv + „Uskoro" pill-badge + nazad-na-Home CTA — per Story 2-6 AC2.5 spec; live verifikovano `templates/brands/brand_coming_soon.html`)
- **When** Jeegee brand ima `is_coming_soon=True` (npr. admin privremeno setuje pre nego što content bude spreman)
- **Then** view `get_template_names()` vraća `["brands/brand_coming_soon.html"]`; postojeći template renderuje brand (Jeegee) sa logom + nazivom + „Uskoro" badge + „Nazad na Home" CTA bez izmena
- **And** Story 2-10 NE kreira novi coming-soon template; NE modifikuje Story 2-6 template; sva test/regression discipline iz Story 2-6 (AC2.5: single h1, role=status pill-badge, semantic main wrapper, S1 fix noindex meta tag, T4 responsive_picture render-ovanje za logo) ostaje validna
- **And** smoke verifikacija (manual): privremeno setovati `jeegee_brand.is_coming_soon = True` u Django shell-u, reload `/sr/mehanizacija/prikljucna/`, verifikovati render coming-soon template-a; reset na False

**AC3 — `templates/brands/jeegee_prikljucna.html` renderuje sekcije TAČNIM redosledom: hero overlay (sa „jeegee" PLAVOM varijantom Repeating Element-a) → 3-card category showcase grid → opciono „Preuzmi Jeegee katalog" CTA banner (sa Wave Divider iznad, samo ako brand.catalog_pdf postoji); JEDAN `<h1>` na strani (kroz hero_overlay_card partial); semantic HTML5 sa `<section aria-labelledby ili aria-label>` na svim sekcijama (outer wrapper + hero koriste `aria-label`; inner sections koriste `aria-labelledby` na lokalnim h2 sa id-em — vidi SM-D8 za detaljnu odluku); single `<main>` element (samo iz base.html)**

- **Given** AC1 + AC2 završeni; Story 1-6 base.html provider; Story 1-7 partials site-wide (hero_overlay_card, repeating_element, section_eyebrow, pill_button, wave_divider); Story 2-6 _hero_section.html partial pattern REFERENCE (Story 2-10 ne reuse-uje već koristi sopstveni `_jeegee_hero.html` — vidi SM-D4)
- **When** kreiram `templates/brands/jeegee_prikljucna.html`
- **Then** template MORA imati strukturu:
  ```django
  {% extends "base.html" %}
  {% load i18n static media_tags %}

  {% block title %}{{ brand.name }} {% translate "Priključna mehanizacija" %} | {% translate "Ćorić Agrar" %}{% endblock %}

  {% block meta_description %}{% blocktranslate with brand=brand.name %}Pregled priključne mehanizacije {{ brand }} po kategorijama — osnovna obrada zemljišta, priprema zemljišta, mašine za setvu.{% endblocktranslate %}{% endblock %}

  {% block content %}
  <section class="coric-brand-detail coric-jeegee-prikljucna"
           data-testid="jeegee-prikljucna-page"
           aria-label="{% blocktranslate with brand=brand.name %}{{ brand }} priključna mehanizacija{% endblocktranslate %}">

    {# 1. Hero overlay sekcija (h1 dolazi iz hero_overlay_card partial-a) #}
    <section id="jeegee-prikljucna-hero"
             aria-label="{% blocktranslate with brand=brand.name %}{{ brand }} hero{% endblocktranslate %}"
             class="coric-jeegee-prikljucna__hero-section">
      {% include "brands/partials/_jeegee_hero.html" %}
    </section>

    {# 2. 3-card category showcase #}
    <section id="jeegee-prikljucna-categories"
             aria-labelledby="jeegee-prikljucna-categories-title"
             class="coric-jeegee-prikljucna__categories-section">
      {% include "brands/partials/_category_showcase.html" %}
    </section>

    {# 3. Opciono catalog CTA banner (samo ako brand.catalog_pdf postoji) #}
    {% if brand.catalog_pdf %}
      <section id="jeegee-prikljucna-catalog-cta"
               aria-labelledby="jeegee-prikljucna-catalog-cta-title"
               class="coric-jeegee-prikljucna__catalog-cta-section">
        {% include "partials/wave_divider.html" with position="top" %}
        <div class="coric-catalog-cta-banner">
          <h2 id="jeegee-prikljucna-catalog-cta-title"
              class="coric-catalog-cta-banner__title">
            {% blocktranslate with brand=brand.name %}Preuzmi {{ brand }} katalog{% endblocktranslate %}
          </h2>
          <p class="coric-catalog-cta-banner__description">
            {% translate "PDF dokument sa kompletnom ponudom priključne mehanizacije." %}
          </p>
          <a href="{{ brand.catalog_pdf.url }}"
             target="_blank"
             rel="noopener noreferrer"
             download
             class="coric-button coric-button--primary"
             data-testid="jeegee-catalog-download">
            {% translate "Preuzmi katalog" %}
          </a>
        </div>
      </section>
    {% endif %}

  </section>
  {% endblock %}
  ```
- **And** template MORA:
  - `{% extends "base.html" %}` + `{% load i18n static media_tags %}` (media_tags je za bilo koji `{% responsive_picture %}` koji bi mogao biti potreban; v1 nije strogo potreban jer hero koristi `brand.logo.url` direktno kroz hero_overlay_card partial — ali safer da je loaded ako Story 9-10 polish doda responsive_picture za logo)
  - `{% block title %}` + `{% block meta_description %}` definisani
  - Outer `<section class="coric-brand-detail coric-jeegee-prikljucna">` wrapper sa `data-testid="jeegee-prikljucna-page"` + `aria-label="{{ brand.name }} priključna mehanizacija"` (blocktranslate-wrapped za i18n). **KRITIČNO (CRITICAL-1 fix, vidi SM-D8 lock):** Outer wrapper koristi `aria-label`, NE `aria-labelledby`, jer `<h1>` unutar Story 1-7 `hero_overlay_card.html` partial-a NEMA id atribut (linija 8: `<h1 class="coric-hero-overlay-card__title">{{ title }}</h1>`); modifikacija partial-a je out-of-scope (breaking change za 4 postojeća konzumenta). `aria-label` na outer landmark daje screen reader-u semantičko ime „<brand> priključna mehanizacija" bez dangling aria reference.
  - 3 unutrašnje `<section>` element (hero, categories, opcioni catalog CTA) — svaka sa `aria-labelledby` ili `aria-label` (jer hero_overlay_card partial render-uje h1 bez id; categories section MOŽE imati h2 sa id; catalog CTA section MOŽE imati h2 sa id)
  - **NEMA inline `style="..."`** atributa
  - **NEMA hardcoded srpski string** — sve labels prolaze kroz `{% translate %}` ili `{% blocktranslate %}`
  - **NEMA ćirilice** (project-context.md striktno)
  - **TAČNO JEDAN `<h1>`** na strani (BeautifulSoup parse test) — h1 dolazi iz `partials/hero_overlay_card.html` koji renderuje `<h1 class="coric-hero-overlay-card__title">{{ title }}</h1>` (live verifikovano `templates/partials/hero_overlay_card.html:8`)
  - **Single `<main>`** element check — BeautifulSoup parse za 1 `<main>` (mirror Story 2-6/2-7/2-8/2-9 regression guard); outer wrapper je `<section>` jer base.html već imao `<main>`
  - `aria-labelledby` referencira h2 id-jeve gde su prisutni (categories-title, catalog-cta-title); hero section koristi `aria-label` umesto `aria-labelledby` jer h1 unutar hero_overlay_card partial-a NEMA id (vidi SM-D8 — Story 2-10 NE modifikuje Story 1-7 hero_overlay_card partial dodavanjem id atributa jer to bi bio breaking change za sve postojeće konzumente Story 2-6 + 2-7 + 2-8 + 2-9)

**AC4 — `_jeegee_hero.html` partial wrappuje `partials/hero_overlay_card.html` (Story 1-7) sa fiksnim Jeegee parametrima: `variant="jeegee"` (rezolvira na `coric-repeating-element--jeegee` BEM klasu koja maps na `--color-jeegee-blue` token), `title=brand.name`, `brand_logo=brand.logo.url|default:""`, `brand_logo_alt=brand.name`, `bullets=""` (per Story 2-6 SM-D10 — hero bullets empty u v1)**

- **Given** AC3 § 1. Hero overlay sekcija; Story 1-7 `partials/hero_overlay_card.html` live (linije 1-19 — prima title, brand_logo, brand_logo_alt, bullets, variant; renderuje h1 + opcioni img + opcioni bullets ul + watermark koji include-uje repeating_element.html sa variant kwarg-om); Story 1-7 `partials/repeating_element.html` live (linije 1-21 — prima variant kwarg, renderuje `coric-repeating-element--{{ variant|default:'green' }}` BEM klasu); `static/css/components/repeating-element.css` ima samo dve variant klase: `--green` (line 11) i `--jeegee` (line 14)
- **When** kreiram `templates/brands/partials/_jeegee_hero.html`
- **Then** partial MORA imati TAČAN markup:
  ```django
  {% load i18n %}
  {# Jeegee hero — fiksna PLAVA varijanta Repeating Element-a. #}
  {# NIJE REUSE Story 2-6 _hero_section.html (per SM-D4) — Jeegee variant je hardcoded, #}
  {# NEMA conditional brand_color → variant branching iz Story 2-6. #}
  <div class="coric-brand-hero" data-testid="jeegee-hero">
    {% if brand.logo %}
      {% include "partials/hero_overlay_card.html" with title=brand.name brand_logo=brand.logo.url brand_logo_alt=brand.name variant="jeegee" bullets="" %}
    {% else %}
      {% include "partials/hero_overlay_card.html" with title=brand.name brand_logo="" brand_logo_alt=brand.name variant="jeegee" bullets="" %}
    {% endif %}
  </div>
  ```
- **And** partial MORA:
  - Imati **JEDINI** `{% load %}` directive na vrhu (i18n; static + media_tags nisu potrebni jer logo render-uje hero_overlay_card kroz direct `<img src="{{ brand_logo }}">`)
  - Defensive `{% if brand.logo %}` guard pre prosleđivanja `brand.logo.url` (mirror Story 2-6 _hero_section.html B1 fix iter 1 — `brand.logo.url` raise ValueError ako logo polje je prazno; partial bezbedno predaje `""` empty string ako logo ne postoji, što hero_overlay_card lakše handluje kroz `{% if brand_logo %}` guard u liniji 3)
  - Renderovati TAČNO `variant="jeegee"` (NE "blue", NE "blue-jeegee", NE bilo šta drugo) — **KRITIČNO** jer `coric-repeating-element--jeegee` JE definisan u CSS-u (live verifikovano `static/css/components/repeating-element.css:14`) dok `coric-repeating-element--blue` NIJE definisan i izbacio bi unstyled watermark
  - Renderovati `<h1 class="coric-hero-overlay-card__title">Jeegee</h1>` kroz hero_overlay_card partial koji prima `title=brand.name` (brand.name == "Jeegee" iz seed migracije per SM-D2)
- **And — Repeating Element variant naming clarification (SM-D9 — IMPORTANT):** Epics.md govori o „plavoj varijanti Repeating Element-a"; UX dokument referencira „Jeegee plava boja"; Story 2-6 `_hero_section.html` koristi `variant="blue"` (live verifikovano linije 4-10) **što JE BUG iz Story 2-6** (renderuje `coric-repeating-element--blue` BEM klasu koja **NE postoji u CSS-u** — fallback CSS rule ne primenjuje boju, watermark renderuje bez background-color-a). Story 2-10 koristi `variant="jeegee"` (TAČNA CSS klasa) — ovo je **kanonski naming**. Story 2-6 hero `_hero_section.html` SE NE MODIFIKUJE u Story 2-10 scope-u (drift fix je out-of-scope za 2-10; ako se Story 2-6 hero ne render-uje za bilo koji postojeći tractor brand sa `brand_color="#00A4E9"`, fix može doći u Story 9-10 polish iteraciji ili kao zaseban tehnički dug). **Dev MUST verifikovati pre commit-a:** `_jeegee_hero.html` koristi TAČNO `variant="jeegee"` (lowercase, jednina, bez prefiksa) — TEA test verifikuje rendered HTML sadrži klasu `coric-repeating-element--jeegee` (NE `--blue` ili `--jeegee-blue`)

**AC5 — `_category_showcase.html` partial renderuje 3-card grid sa Section Eyebrow + h2 + grid wrapper koji iterira `categories` context list i renderuje per-category karticu sa: kategorija ikona (conditional render kroz `{% if category.icon %}`) + naziv (`category.name`) + kratak opis (`category.description|truncatewords:25`) + „POGLEDAJ KATEGORIJU" CTA dugme; CTA linkuje na placeholder URL `/sr/mehanizacija/prikljucna/<category-slug>/` (URL pattern dolazi u Story 2-11; v1 koristi `<a href>` direct string interpolation, NE `{% url %}` template tag — vidi SM-D5)**

- **Given** AC3 § 2. Categories section; AC2 view dodaje `categories` context list (3 Category instance-i); Story 1-7 `partials/section_eyebrow.html` partial (prima `text` + opciono `tag`/`variant`); Story 1-7 `partials/pill_button.html` partial (prima `label`, `href`, `variant`, opciono `aria_label`, `extra_classes`, `as`, `type`)
- **When** kreiram `templates/brands/partials/_category_showcase.html`
- **Then** partial MORA imati strukturu:
  ```django
  {% load i18n %}

  {% include "partials/section_eyebrow.html" with text=_("KATEGORIJE PRIKLJUČNE MEHANIZACIJE") tag="div" %}

  <h2 id="jeegee-prikljucna-categories-title"
      class="coric-category-showcase__title">
    {% translate "Pregled po kategorijama" %}
  </h2>

  <div class="coric-category-showcase" data-testid="category-showcase-grid">
    {% for category in categories %}
      <article class="coric-category-card"
               aria-labelledby="cat-card-{{ category.slug }}-title"
               data-testid="category-card-{{ category.slug }}">
        {% if category.icon %}
          <div class="coric-category-card__icon" aria-hidden="true">
            <i class="{{ category.icon }}"></i>
          </div>
        {% endif %}
        <h3 id="cat-card-{{ category.slug }}-title"
            class="coric-category-card__title">{{ category.name }}</h3>
        {% if category.description %}
          <p class="coric-category-card__description">{{ category.description|truncatewords:25 }}</p>
        {% endif %}
        <a href="/{{ LANGUAGE_CODE }}/mehanizacija/prikljucna/{{ category.slug }}/"
           class="coric-button coric-button--primary coric-category-card__cta"
           aria-label="{% blocktranslate with category=category.name %}Pogledaj kategoriju: {{ category }}{% endblocktranslate %}"
           data-testid="category-card-cta-{{ category.slug }}">
          {% translate "POGLEDAJ KATEGORIJU" %}
        </a>
      </article>
    {% empty %}
      <p class="coric-empty-state">
        {% translate "Kategorije priključne mehanizacije su u pripremi." %}
      </p>
    {% endfor %}
  </div>
  ```
- **And** partial MORA:
  - Imati `{% load i18n %}` na vrhu (NE static, NE media_tags — kartica koristi `category.icon` direct string interpolation i obični `<a>` linkove; nema slike u v1 kartici)
  - Renderovati Section Eyebrow sa tekstom „KATEGORIJE PRIKLJUČNE MEHANIZACIJE" (UPPERCASE per Story 1-7 eyebrow konvencija)
  - Renderovati `<h2 id="jeegee-prikljucna-categories-title">` (referencira `aria-labelledby` iz outer section u jeegee_prikljucna.html)
  - Renderovati grid wrapper `<div class="coric-category-showcase">` koji iterira `categories` context list
  - Per-category renderovati `<article class="coric-category-card">` sa:
    - Konditionalna ikona (`{% if category.icon %}`) — v1 svi seed-ovani Category-ji imaju `icon=""` (per SM-D2 seed migration); ako admin kasnije popuni `category.icon` polje sa Bootstrap Icons klasom (npr. "bi bi-tractor"), ikona se rendеra; v1 strana neće prikazivati ikone (Bootstrap Icons font deferred per Story 2-6 SM-D18)
    - `<h3 id="cat-card-{{ category.slug }}-title">` sa nazivom kategorije
    - Konditionalan opis (`{% if category.description %}`) sa `|truncatewords:25` filter-om
    - „POGLEDAJ KATEGORIJU" CTA dugme — **direct `<a>` markup** (NE `{% include "partials/pill_button.html" %}` — vidi SM-D6) sa `href="/{{ LANGUAGE_CODE }}/mehanizacija/prikljucna/{{ category.slug }}/"` (placeholder URL koji rezolvuje 404 do Story 2-11 koje implementira `SubcategoryListView`); `class="coric-button coric-button--primary coric-category-card__cta"`; `aria-label` koji DESKRIPTIVNO opisuje destinaciju (per WCAG 2.1 SC 2.4.4 — link purpose in context); `data-testid` za Playwright Story 9-8
  - `{% empty %}` clause za empty state (defensive — ako seed migracija nije primenjena ili je admin manualno obrisao kategorije, prikazuje user-friendly poruku umesto prazne sekcije)
  - **NEMA `<a>` wrapping cele kartice** — kartica je `<article>` semantic wrapper, ne linkable card pattern (mirror Story 2-9 SM-D razlikuje od Story 2-6 linkable card-a); CTA dugme JE jedini linkabilan element u kartici (single-action pattern — jednoznačnost target-a)
- **And — CTA URL render strategy (SM-D5 — IMPORTANT):** Story 2-10 koristi **direct string interpolation** za CTA href (`/{{ LANGUAGE_CODE }}/mehanizacija/prikljucna/{{ category.slug }}/`) umesto `{% url %}` template tag-a jer URL pattern `subcategory_list` (ili kako god se imenuje) NE postoji do Story 2-11. Ako Story 2-10 dođe pre Story 2-11 (što je očekivano per sprint-status.yaml redoslijed 2-10 → 2-11), `{% url 'brands:subcategory_list' ... %}` bi raise `NoReverseMatch` tokom template render-a — strana bi crashovala. Direct string interpolation je defensive: render uvek prolazi; klik na CTA produkuje 404 koji je Django-ov default „Page not found" (acceptable jer Story 2-11 immediately uvodi pattern). Story 2-11 SM MORA u svom create-story koraku refaktorisati direct interpolation u `{% url %}` tag — to je load-bearing TODO za Story 2-11 (vidi „Foundation za buduće Story-je" sekciju iznad). Alternativna strategija „uvesti placeholder URL pattern u Story 2-10 sliko Story 2-6 C8 fix za products" je odbačena jer placeholder dodaje 2 file-a (urls.py path + view + template) koji se odmah brišu u Story 2-11 — net negative (više work-a, više code churn-a). Direct interpolation je 1 line trade-off
- **And — A11y must-have:** `aria-label` na CTA dugmetu MORA imati BLOCKTRANSLATE wrap sa category.name interpolacijom za screen reader announcement „Pogledaj kategoriju: Osnovna obrada zemljišta, link" (per WCAG 2.1 SC 2.4.4); bez aria-label, screen reader najavi samo „POGLEDAJ KATEGORIJU, link" 3 puta uzastopno (ambiguous link purpose)

**AC6 — CSS komponenta `category-showcase.css` definiše `coric-category-showcase` wrapper grid + `coric-category-card` karticu + per-element modifier-e; responzivni CSS Grid `repeat(auto-fit, minmax(280px, 1fr))` automatski handluje 3 vs 4 vs N kartica (foundation za Story 2-12); hover/focus states; `@media (prefers-reduced-motion: reduce)` block koji uklanja transform animaciju; sve vrednosti kroz `var(--token)`; `static/css/main.css` dobija +1 `@import` linija**

- **Given** AC5 završen; Story 1-5 tokens.css ima sve potrebne tokene (`--color-brand-green-800`, `--color-neutral-cream`, `--color-neutral-white`, `--spacing-scale-*`, `--rounded-md`, `--typography-scale-h2/h3/body`); Story 1-7 `static/css/components/pill-button.css` definiše `.coric-button` i `.coric-button--primary` (REUSE — Story 2-10 NE re-definiše te klase)
- **When** kreiram `static/css/components/category-showcase.css`
- **Then** CSS fajl MORA sadržati selektore:
  - `.coric-category-showcase` — root grid wrapper:
    ```css
    .coric-category-showcase {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: var(--spacing-scale-5);
      margin-top: var(--spacing-scale-5);
      margin-bottom: var(--spacing-section);
    }
    ```
  - `.coric-category-showcase__title` — h2 naslov iznad grid-a:
    ```css
    .coric-category-showcase__title {
      font-size: var(--typography-scale-h2);
      color: var(--color-brand-green-800);
      text-align: center;
      margin-bottom: var(--spacing-scale-5);
    }
    ```
  - `.coric-category-card` — kartica root (flex/grid column layout sa icon top + naziv + opis + CTA bottom):
    ```css
    .coric-category-card {
      display: flex;
      flex-direction: column;
      gap: var(--spacing-scale-3);
      padding: var(--spacing-scale-5);
      background-color: var(--color-neutral-white);
      border-radius: var(--rounded-md);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
      transition: transform 200ms ease, box-shadow 200ms ease;
    }

    .coric-category-card:hover,
    .coric-category-card:focus-within {
      transform: translateY(-4px);
      box-shadow: 0 6px 16px rgba(0, 0, 0, 0.10);
    }
    ```
  - `.coric-category-card__icon` — ikona container (v1 nedostaje Bootstrap Icons font pa će biti prazan; CSS rule postavlja size + boja za buduće Story 9-10 ikona render):
    ```css
    .coric-category-card__icon {
      font-size: var(--typography-scale-h2);
      color: var(--color-jeegee-blue);
      text-align: center;
    }
    ```
  - `.coric-category-card__title` — h3 naziv kategorije:
    ```css
    .coric-category-card__title {
      font-size: var(--typography-scale-h3);
      color: var(--color-brand-green-800);
      margin: 0;
    }
    ```
  - `.coric-category-card__description` — paragraf opisa:
    ```css
    .coric-category-card__description {
      font-size: var(--typography-scale-body);
      color: var(--color-neutral-gray-700);
      flex-grow: 1;  /* push CTA na dno kad description je kraći */
    }
    ```
  - `.coric-category-card__cta` — pozicioniranje CTA dugmeta unutar kartice (sve typography/color base styles dolaze iz `.coric-button--primary` BEM klase iz Story 1-7 pill-button.css — Story 2-10 NE re-definiše):
    ```css
    .coric-category-card__cta {
      align-self: flex-start;  /* leva strana kartice */
      margin-top: var(--spacing-scale-3);
    }
    ```
  - `.coric-empty-state` — empty state paragraph za `{% empty %}` clause kada `categories` je prazan (IMP-2 fix — AC5 markup koristi `<p class="coric-empty-state">` ali ranija iteracija spec-a nije imala CSS rule):
    ```css
    .coric-empty-state {
      text-align: center;
      padding: var(--spacing-scale-5);
      color: var(--color-neutral-gray-700);
      font-style: italic;
    }
    ```
    **Token verifikacija (IMP-6 — REJECTED false positive):** `--color-neutral-gray-700` JE verifikovan live u `static/css/tokens.css:102` = `#4a4a4a`; `--spacing-scale-5` JE verifikovan live u tokens.css. Nema potrebe za dodavanjem tokena — postojeci.
  - `@media (prefers-reduced-motion: reduce)` block koji onemogućava transform animaciju:
    ```css
    @media (prefers-reduced-motion: reduce) {
      .coric-category-card {
        transition: none;
      }
      .coric-category-card:hover,
      .coric-category-card:focus-within {
        transform: none;
      }
    }
    ```
- **And** SVI BEM klasi MORAJU imati `coric-` prefix (per project-context.md § CSS naming linija 315)
- **And** SVI CSS pravila MORAJU koristiti `var(--token)` za boje, spacing, typography (nijedan magic hex/px/em u komponentnom CSS-u — sve tokeni iz Story 1-5 tokens.css)
- **And** `static/css/main.css` MORA dobiti TAČNO 1 nova `@import` linija TAČNO mirror Story 2-9 + 2-8 + 2-7 sintaksu (sa `url(...)` wrap-erom + leading `./` + trailing semicolon):
  ```css
  @import url('./components/category-showcase.css');
  ```
- **And** Edit `main.css` MORA biti **targeted Edit** koji ZADRŽAVA sve postojeće linije; nova linija ide na kraj postojećih `@import` linija (NE presretati postojeći stacking order — Story 2-9 ostaje poslednja pre nove)
- **And** **NEMA `cdn.jsdelivr.net`, `unpkg.com`, `cdnjs.cloudflare.com`** reference (anti-CDN guard, mirror Story 2-6 + 2-7 + 2-8 + 2-9)

**AC7 — Data migracija `apps/brands/migrations/0003_seed_jeegee_and_prikljucna_categories.py` seed-uje Jeegee Brand instance + 3 mehanizacija Category instance (idempotentna kroz `get_or_create`); reverse callable defined koji DELETE-uje TAČNO te 4 instance po slug-u**

- **Given** AC1 + AC2 + AC5 (svi koriste Jeegee Brand i 3 Category instance iz DB); Story 2-1 modeli (Brand, Category sa CategoryScope.MEHANIZACIJA TextChoices); Django migration framework `RunPython` + `migrations.RunPython.noop` patterns
- **When** kreiram `apps/brands/migrations/0003_seed_jeegee_and_prikljucna_categories.py`
- **Then** migracija MORA imati strukturu:
  ```python
  """Story 2.10 data migracija — seed Jeegee Brand + 3 mehanizacija kategorije.

  Idempotentna kroz get_or_create. Reverse delete-uje tačno te 4 instance po slug-u.
  NEMA modeltranslation hu/en prevode za Category.name u v1 (per Story 2.10 SM-D
  fall-back na sr name; Story 8.5 Category admin omogućava admin-u da popuni
  prevode kasnije).
  """

  from django.db import migrations


  _JEEGEE_BRAND_DATA = {
      "slug": "jeegee",
      "name": "Jeegee",
      "brand_color": "#00A4E9",
      "is_coming_soon": False,
      "description": "",
      "slogan": "",
      "statistics": [],
  }

  _PRIKLJUCNA_CATEGORIES = [
      {
          "slug": "osnovna-obrada-zemljista",
          "name": "Osnovna obrada zemljišta",
          "is_for": "mehanizacija",
          "display_order": 10,
          "description": "Plugovi, podrivači, gruberi za primarnu obradu zemljišta.",
          "icon": "",  # Bootstrap Icons font NIJE wired u v1 (Story 2.6 SM-D18 defer).
      },
      {
          "slug": "priprema-zemljista",
          "name": "Priprema zemljišta",
          "is_for": "mehanizacija",
          "display_order": 20,
          "description": "Tanjirače, drljače, valjci za sekundarnu pripremu zemljišta.",
          "icon": "",
      },
      {
          "slug": "masine-za-setvu",
          "name": "Mašine za setvu",
          "is_for": "mehanizacija",
          "display_order": 30,
          "description": "Sejalice i mašine za setvu strnih žita i okopavinskih kultura.",
          "icon": "",
      },
  ]


  def seed_jeegee_and_categories(apps, schema_editor):
      Brand = apps.get_model("brands", "Brand")
      Category = apps.get_model("brands", "Category")

      Brand.objects.get_or_create(
          slug=_JEEGEE_BRAND_DATA["slug"],
          defaults=_JEEGEE_BRAND_DATA,
      )

      for cat_data in _PRIKLJUCNA_CATEGORIES:
          Category.objects.get_or_create(
              slug=cat_data["slug"],
              defaults=cat_data,
          )


  def reverse_seed(apps, schema_editor):
      Brand = apps.get_model("brands", "Brand")
      Category = apps.get_model("brands", "Category")

      Brand.objects.filter(slug=_JEEGEE_BRAND_DATA["slug"]).delete()
      Category.objects.filter(
          slug__in=[c["slug"] for c in _PRIKLJUCNA_CATEGORIES]
      ).delete()


  class Migration(migrations.Migration):

      dependencies = [
          ("brands", "0002_alter_brand_created_at"),
      ]

      operations = [
          migrations.RunPython(seed_jeegee_and_categories, reverse_code=reverse_seed),
      ]
  ```
- **And** migracija MORA:
  - Imati `dependencies` pokazivati na poslednju brands migraciju (`0002_alter_brand_created_at` per live `apps/brands/migrations/` listing) — Dev MORA verifikovati pre commit-a (ako su druge migracije dodate u međuvremenu, dependency MORA pokazivati na poslednju)
  - Koristi `apps.get_model()` (NE direct import iz `apps.brands.models`) — Django migration best practice (historical models snapshot)
  - Koristi `get_or_create()` za **idempotentnost** — re-pokretanje migracije ne baca IntegrityError ako instance već postoji (npr. migracija je primenjena pa rollback-ovana pa primenjena ponovo)
  - Reverse callable (`reverse_code=reverse_seed`) defined da migracija može biti **reversible** (`manage.py migrate brands 0002` rollback-uje ka stanju pre Story 2-10)
  - **NEMA modeltranslation hu/en prevod-a** za Category.name u migraciji (svi instance-i kreirani sa srpskim nazivom; modeltranslation auto-discovery iz Story 2-1 D2 znači da će `name_sr` polje biti popunjeno kroz fallback ali `name_hu` i `name_en` ostaju None/empty; v1 prikazuje srpski naziv na svim locale-ima — pragmatic per Story 2-6 § Multi-locale URL slug-ovi open question; Story 8-5 Category admin omogućava admin-u da popuni `name_hu` i `name_en` polja kasnije)
  - `category.icon` polje je prazan string `""` za sve 3 instance (Bootstrap Icons font deferred per Story 2-6 SM-D18; conditional render u `_category_showcase.html` partial `{% if category.icon %}` će uvek evaluuirati False u v1)
- **And** smoke verifikacija (mirror Story 2-9 AC pattern):
  ```bash
  uv run python manage.py migrate brands  # primenuje 0003 migraciju
  uv run python manage.py shell -c "from apps.brands.models import Brand, Category; \
    print(Brand.objects.filter(slug='jeegee').exists()); \
    print(Category.objects.filter(is_for='mehanizacija', slug__in=['osnovna-obrada-zemljista', 'priprema-zemljista', 'masine-za-setvu']).count())"
  ```
  Očekivan output:
  ```
  True
  3
  ```
- **And** reverse smoke verifikacija (manuelna):
  ```bash
  uv run python manage.py migrate brands 0002  # rollback do pre 2-10
  uv run python manage.py shell -c "from apps.brands.models import Brand, Category; \
    print(Brand.objects.filter(slug='jeegee').exists()); \
    print(Category.objects.filter(slug__in=['osnovna-obrada-zemljista', 'priprema-zemljista', 'masine-za-setvu']).count())"
  ```
  Očekivan output:
  ```
  False
  0
  ```
  (Posle rollback-a, Dev mora ponovo primeniti `migrate brands` da vrati 0003.)

**AC8 — i18n + a11y + WCAG 2.1 AA compliance: sve user-facing string-ove kroz `{% translate %}` ili `gettext_lazy as _`; locale .po fajlovi (sr/hu/en) popunjeni; `<html lang="{{ LANGUAGE_CODE }}">` automatski iz base.html; semantic HTML5 (`<section>`, `<article>`, `<h1>/<h2>/<h3>` hijerarhija) — single h1 pravilo; ARIA landmarks (`<section aria-labelledby>` ili `aria-label`); fokus indikator vidljiv (`:focus-visible` outline iz Story 1-5 tokena); color contrast ≥ 4.5:1 na svim text-background kombinacijama**

- **Given** AC3 + AC5 + AC6 završeni; Story 1-4 i18n setup (LANGUAGE_CODE, LANGUAGES, LocaleMiddleware); Story 1-5 tokens.css (color contrast validated); Story 1-7 partials (semantic HTML5 base već u partials); project-context.md § A11y must-haves linija 723-732 + § Critical Don't-Miss Rules linije 497-528
- **When** Dev kompletira AC3 + AC5 + AC6 templates i CSS; pokreće `just messages` da regeneriše .po fajlove
- **Then**:
  - SVI user-facing string-ovi u templates prolaze kroz `{% translate "..." %}` ili `{% blocktranslate %}` (NIJEDAN hardcoded srpski string)
  - `locale/sr/LC_MESSAGES/django.po` MORA imati popunjene `msgstr` za sve nove msgid:
    - „Priključna mehanizacija" → „Priključna mehanizacija"
    - „Pregled priključne mehanizacije {{ brand }} po kategorijama — osnovna obrada zemljišta, priprema zemljišta, mašine za setvu." → identičan sr (blocktranslate with brand)
    - „Pregled po kategorijama" → „Pregled po kategorijama"
    - „KATEGORIJE PRIKLJUČNE MEHANIZACIJE" → identičan (Section Eyebrow UPPERCASE)
    - „POGLEDAJ KATEGORIJU" → „POGLEDAJ KATEGORIJU"
    - „Pogledaj kategoriju: {{ category }}" → identičan sr (blocktranslate with category — aria-label)
    - „Kategorije priključne mehanizacije su u pripremi." → identičan sr (empty state)
    - „Preuzmi {{ brand }} katalog" → identičan sr (blocktranslate with brand — catalog CTA heading)
    - „PDF dokument sa kompletnom ponudom priključne mehanizacije." → identičan sr (catalog CTA description)
    - „Preuzmi katalog" → „Preuzmi katalog"
    - „{{ brand }} hero" → identičan sr (blocktranslate with brand — hero aria-label)
    - „{{ brand }} priključna mehanizacija" → identičan sr (blocktranslate with brand — outer section aria-label, CRITICAL-1 fix)
  - `locale/hu/LC_MESSAGES/django.po` MORA imati popunjene hu prevode (Dev koristi DeepL/Google Translate + manual review za precision; ako neke msgid nemaju hu prevod, `msgstr ""` blank fallback automatski koristi `msgid` source string — pragmatic but flagged za Story 6-5 i18n fallback marker)
  - `locale/en/LC_MESSAGES/django.po` MORA imati popunjene en prevode (mirror hu)
  - `just messages` MORA biti pokrenut (regeneriše .po fajlove sa novim msgid-ovima); `just compilemessages` na CI rebuild-uje .mo fajlove
  - **NEMA ćirilice** u nijednom string-u (project-context.md anti-pattern linija 486-495)
  - **NEMA šišane latinice** (sve č/ć/ž/š/đ pune dijakritike — project-context.md anti-pattern linija 497-528)
  - **IMP-4 fix — UX-DR-22 fallback marker explicit OUT-OF-SCOPE:** v1 prikazuje sr `Category.name` (npr. „Osnovna obrada zemljišta", „Priprema zemljišta", „Mašine za setvu") na /hu/ /en/ stranama BEZ fallback marker-a — UX-DR-22 marker („ⓘ tooltip 'Sadržaj na srpskom — još nije preveden'") je **explicit out-of-scope za Story 2-10** i deferred to **Story 6-5 (i18n fallback marker tooltip)**; lokali su tehnički podržani (LocaleMiddleware aktivan iz Story 1-4), ali HU/EN `msgstr` za `Category.name` polja su prazni (admin populacija planirana u Story 8-5 Category CRUD). Pragmatic UX trade-off za v1. Vlasnik marker UI komponente je Story 6-5; vlasnik popunjavanja prevod-a je Story 8-5 admin.
- **And** semantic HTML5:
  - **TAČNO 1 `<h1>`** na strani (kroz hero_overlay_card partial `<h1 class="coric-hero-overlay-card__title">{{ brand.name }}</h1>`)
  - `<h2>` za 2 sekcije: „Pregled po kategorijama" (categories section) + „Preuzmi {{ brand }} katalog" (catalog CTA section ako se renderuje)
  - `<h3>` za per-category title u svakoj kartici (3x na strani)
  - Heading hijerarhija: h1 → h2 → h3 (NEMA skok-ova; svaki nivo prisutan logički)
  - **Single `<main>`** element (samo iz base.html — outer wrapper u jeegee_prikljucna.html je `<section>`, NE drugi `<main>`)
  - `<section>` sa `aria-labelledby` ili `aria-label` na svakoj outer sekciji (hero, categories, opcioni catalog CTA)
  - `<article>` za svaku kategorija karticu (semantic standalone content)
- **And** ARIA landmarks:
  - Outer `<section>` na strani koristi `aria-label="{{ brand.name }} priključna mehanizacija"` (blocktranslate-wrapped) — **NE `aria-labelledby`** (CRITICAL-1 fix; SM-D8 lock-uje ovu odluku jer `<h1>` u hero_overlay_card partial-u nema id, modifikacija partial-a je breaking change za 4 postojeća konzumenta)
  - Categories section ima `aria-labelledby="jeegee-prikljucna-categories-title"` koji referencira `<h2 id="jeegee-prikljucna-categories-title">`
  - Catalog CTA section (ako se renderuje) ima `aria-labelledby="jeegee-prikljucna-catalog-cta-title"` koji referencira `<h2 id="jeegee-prikljucna-catalog-cta-title">`
  - Hero section koristi `aria-label="{{ brand }} hero"` (jer h1 unutar hero_overlay_card nema id per SM-D8)
- **And** fokus indikator:
  - Sve CTA dugmad (POGLEDAJ KATEGORIJU + Preuzmi katalog) imaju vidljiv fokus outline (`:focus-visible` styled iz Story 1-7 pill-button.css)
  - Kartice (`.coric-category-card:focus-within`) imaju hover/focus state (transform translateY + shadow) — keyboard tab kroz CTA dugme triggeruje `:focus-within` na parent kartici
- **And** color contrast:
  - Sve text-background kombinacije ≥ 4.5:1 (Story 1-5 tokens validated): `--color-brand-green-800` text na `--color-neutral-white` background → 11.5:1 (pass); `--color-neutral-gray-700` text na `--color-neutral-white` → 7.2:1 (pass); CTA `--color-brand-green-800` background sa white text → 11.5:1 (pass); Jeegee blue (#00a4e9) ima 2.8:1 na white što JE BELOW WCAG 2.1 AA — ali se koristi SAMO za dekorativnu ikonu (aria-hidden) i Repeating Element watermark (aria-hidden), NE za interaktivni text — ne primenjuje se kontrast pravilo per WCAG SC 1.4.3 koji eksplicitno isključuje „decorative" content i UI components koji nisu interaktivni
- **And — Smoke verifikacija (Dev pre commit-a):**
  ```bash
  uv run python manage.py makemessages -l sr -l hu -l en  # regeneriše .po fajlove
  uv run python manage.py compilemessages -l sr -l hu -l en  # rebuild .mo
  # Verifikuj 0 fuzzy translation-a (manual review .po fajlova)
  grep -r "msgstr \"\"" locale/sr/LC_MESSAGES/django.po | head -20  # 0 empty msgstr za nove msgid
  ```

  ```powershell
  # PowerShell equivalent (run if on Windows host — grep + head nisu native u PowerShell-u):
  Select-String -Pattern 'msgstr ""' -Path locale/sr/LC_MESSAGES/django.po | Select-Object -First 20
  ```

**AC9 — Manuelni Dev smoke check + Lighthouse a11y skor ≥ 95 na lokalnoj instanci (mirror Story 2-6 AC9 + Story 2-9 manual gate)**

- **Given** AC1-AC8 završeni; data migracija primenjena; Jeegee Brand i 3 Category instance u DB
- **When** Dev pokreće `just dev` (Docker Compose local) i otvara `http://localhost:8000/sr/mehanizacija/prikljucna/` u Chrome
- **Then** Dev verifikuje (manuelni checklist):
  - Hero overlay sekcija renderuje: Jeegee logo (ako postoji upload — možeš stub-ovati kroz Django admin ili kroz shell-om za testing) + Jeegee naziv (h1) + PLAVA varijanta Repeating Element-a u gornjem desnom uglu hero kartice (DevTools Elements panel: verifikuj `<div class="coric-repeating-element coric-repeating-element--jeegee">` postoji; background-color computed style je `#00a4e9` koji je `--color-jeegee-blue` token)
  - 3-card category showcase renderuje 3 kartice u responzivnom grid-u:
    - Desktop (≥768px): 3 kartice u redu (3 column)
    - Tablet (480-768px): 2 kartice u redu, 1 u drugom (2 column)
    - Mobile (<480px): 1 kartica po redu (1 column stack)
  - Per-kartica sadrži: (v1 BEZ ikone — Bootstrap Icons font nije wired) naziv kategorije („Osnovna obrada zemljišta", „Priprema zemljišta", „Mašine za setvu") + kratak opis + „POGLEDAJ KATEGORIJU" CTA dugme
  - Klik na „POGLEDAJ KATEGORIJU" CTA navigira na `/sr/mehanizacija/prikljucna/osnovna-obrada-zemljista/` (ili odgovarajući slug) — vraća Django 404 strana („Page not found") jer Story 2-11 URL pattern još ne postoji; **ovo je EXPECTED ponašanje u v1** (Dev verifikuje da CTA URL kompozicija je tačna — slug se interpolira korektno)
  - Hover na kartice: kartica translate-up sa 4px i box-shadow se proširi (smooth 200ms transition)
  - Keyboard tab kroz CTA dugmad: fokus outline vidljiv; Enter klik aktivira navigation
  - Ako `brand.catalog_pdf` postoji (može se attach-ovati kroz admin za testing): „Preuzmi Jeegee katalog" CTA banner se renderuje na dnu sa Wave Divider iznad; klik otvara PDF u novom tabu (`target="_blank"` + `download` atributi)
  - Ako `brand.catalog_pdf` NE postoji (default state posle seed migracije): CTA banner SE NE RENDERUJE (conditional `{% if brand.catalog_pdf %}` guard)
  - **Empty state test:** kroz Django shell, privremeno DELETE-uj 3 Category instance (`Category.objects.filter(slug__in=['osnovna-obrada-zemljista', 'priprema-zemljista', 'masine-za-setvu']).delete()`); reload strane; verifikuj prikazuje se „Kategorije priključne mehanizacije su u pripremi." poruka umesto prazne sekcije; restore kategorije (re-run migracije: `uv run python manage.py migrate brands zero --fake; uv run python manage.py migrate brands` — ili manual recreate u shell-u)
  - **Coming-soon test:** kroz Django shell, set `Brand.objects.filter(slug='jeegee').update(is_coming_soon=True)`; reload strane; verifikuj prikazuje se `brand_coming_soon.html` template (logo + naziv + „Uskoro" pill-badge + nazad-na-Home CTA); reset `is_coming_soon=False`
  - **Coming-soon brand → 404 test:** kroz Django shell, DELETE Jeegee Brand (`Brand.objects.filter(slug='jeegee').delete()`); reload strane; verifikuj prikazuje se Django 404 strana sa porukom „Jeegee brand nije konfigurisan u sistemu." (kustomizovana Http404 message iz `get_object()`); restore Jeegee brand kroz re-run migracije
  - **`prefers-reduced-motion` test:** uključi `prefers-reduced-motion: reduce` u Chrome DevTools Rendering panel; reload strane; verifikuj:
    - Hover na kartice ne triggeruje transform animaciju (CSS `@media (prefers-reduced-motion: reduce)` block primenjuje `transition: none` i `transform: none`)
    - Strana renderuje statički sve sekcije bez ikakvih JS-driven animacija (Story 2-10 NEMA JavaScript pa nema reduced-motion JS hook-a)
- **And** Dev pokreće Lighthouse audit (Chrome DevTools Lighthouse tab → Generate report → Mobile + Accessibility category):
  - **Accessibility score ≥ 95** (UX-DR-13 + NFR-2 target; Story 9-9 audit gate)
  - **Performance score ≥ 80** (target je viši nego Story 2-6 jer NEMA JavaScript-a, NEMA range slidera, NEMA HTMX; Story 9-10 polish dovešće na ≥ 90)
  - **IMP-10 clarification:** Performance ≥ 80 + A11y ≥ 95 su MEASURABLE gates — Dev MORA citirati skor-ove u Completion Notes; ako Chrome/lighthouse-cli nije dostupan, fallback je Chrome DevTools Lighthouse panel (manual JSON save je acceptable). Ako su OBE alati nedostupni, gate je DEFERRED uz `unfixable_issue` log entry sa rationale-om.
- **And — Lighthouse JSON artifact preservation (mirror Story 2-6 I-iter2-8 fix + Story 2-9 alignment, audit-gate alignment sa Story 9-9):** Dev MORA pokrenuti Lighthouse u CLI mode-u (NE samo Chrome DevTools manual run) i sačuvati JSON output kao artifact:
  ```bash
  lighthouse http://localhost:8000/sr/mehanizacija/prikljucna/ \
    --output=json \
    --output-path=_bmad-output/implementation-artifacts/2-10-lighthouse-YYYYMMDD.json \
    --only-categories=accessibility,performance,seo \
    --form-factor=mobile \
    --chrome-flags="--headless"
  ```
  **IMP-8 fix:** `YYYYMMDD` je literal placeholder — Dev MORA manualno zameniti sa datumom (npr. `20260530`). PowerShell host NE expand-uje `$(date +%Y%m%d)` Bash syntax (parser error u PowerShell 5.1); literal placeholder garantuje konzistentno ponašanje cross-platform. Alternativa: pokrenuti `lighthouse` iz Docker container-a (gde Bash radi) — tada `$(date +%Y%m%d)` može da se koristi.
  - **Dev MORA citirati skor-ove u `Dev Agent Record § Completion Notes` sekciji story fajla PRE Step-04 Code Review:** „Lighthouse skor (mobile): a11y={N}, performance={M}, seo={K}; JSON artifact: `_bmad-output/implementation-artifacts/2-10-lighthouse-YYYYMMDD.json`."
  - **Razlog:** mirror Story 2-6 reasoning — Story 9-9 audit-gate zahteva preserved Lighthouse JSON baseline za trend tracking
  - Fallback (ako CLI lighthouse nije dostupan): Chrome DevTools Lighthouse run → Save report (JSON) → manuelno kopirati u `_bmad-output/implementation-artifacts/2-10-lighthouse-YYYYMMDD.json`
- **Napomena:** Ovaj AC je **manuelni smoke check** koji Dev izvršava pre commit-a; automated E2E je Story 9-8 (Playwright UJ-1) scope; automated a11y axe-core je Story 9-9 scope. Dev dokumentuje rezultate u `Dev Agent Record § Completion Notes`

## Tasks / Subtasks

- [x] **Task 1: Data migracija — seed Jeegee Brand + 3 mehanizacija Category (AC7)**
  - [x] Subtask 1.1: Verifikovati `apps/brands/migrations/` zadnju migraciju (live: `0002_alter_brand_created_at.py`); ako su nove dodate u međuvremenu, lock dependency na najnoviju
  - [x] Subtask 1.2: Kreirati `apps/brands/migrations/0003_seed_jeegee_and_prikljucna_categories.py` per AC7 source skeleton (RunPython sa idempotent `get_or_create` + reverse callable koji DELETE-uje po slug-u)
  - [x] Subtask 1.3: Smoke verifikacija — `uv run python manage.py migrate brands` exit code 0; shell verifikuje 1 Brand + 3 Category postoje u DB
  - [x] Subtask 1.4: Reverse smoke verifikacija — `uv run python manage.py migrate brands 0002` rollback; verifikuje 4 instance OBRISANE; re-apply `migrate brands` da vrati state

- [x] **Task 2: `apps/brands/views.py` ADD `JeegeePrikljucnaView` + `apps/brands/urls.py` ADD path (AC1, AC2, AC2.5)**
  - [x] Subtask 2.1: Otvoriti `apps/brands/views.py`; EDIT module-level import `from apps.brands.models import Brand, Series` → `from apps.brands.models import Brand, Category, Series` (dodaj Category; Series ostaje za postojeću BrandDetailView)
  - [x] Subtask 2.2: ADD module-level konstante POSLE postojećih import-a:
    ```python
    _JEEGEE_BRAND_SLUG = "jeegee"
    _PRIKLJUCNA_CATEGORY_SLUGS = (
        "osnovna-obrada-zemljista",
        "priprema-zemljista",
        "masine-za-setvu",
    )
    ```
  - [x] Subtask 2.3: ADD `from django.http import Http404` import (defensive raise u get_object — SM-D7)
  - [x] Subtask 2.4: ADD `JeegeePrikljucnaView(DetailView)` klasu POSLE postojeće `BrandDetailView` klase per AC2 source skeleton (`get_object` sa Http404 guard, `get_template_names` sa coming-soon branching, `get_context_data` sa categories queryset). **IMP-7 fix:** NEMA `get()` override — default `DetailView.get()` flow je: `get_object()` → `self.object = ...` → `get_context_data()` → `render_to_response()` (interno poziva `get_template_names()`); `self.object` JE set pre `get_template_names()` poziva pa custom override nije potreban (raniji iteracija spec-a je imao redundant `get()` override).
  - [x] Subtask 2.5: Otvoriti `apps/brands/urls.py`; ADD novi URL pattern POSLE postojećeg `traktori/<slug:slug>/`:
    ```python
    path("mehanizacija/prikljucna/", JeegeePrikljucnaView.as_view(), name="jeegee_prikljucna"),
    ```
    EDIT import na vrhu: `from apps.brands.views import BrandDetailView` → `from apps.brands.views import BrandDetailView, JeegeePrikljucnaView`
  - [x] Subtask 2.6: Smoke verifikacija — `uv run python manage.py check` exit code 0; URL reverse check:
    ```bash
    uv run python manage.py shell -c "from django.urls import reverse; \
      from django.utils.translation import activate; activate('sr'); \
      print(reverse('brands:jeegee_prikljucna'))"
    ```
    Očekivan output: `/sr/mehanizacija/prikljucna/`

- [x] **Task 3: `templates/brands/jeegee_prikljucna.html` glavni template (AC3)**
  - [x] Subtask 3.1: Kreirati `templates/brands/jeegee_prikljucna.html` per AC3 source skeleton ({% extends "base.html" %} + outer `<section class="coric-brand-detail coric-jeegee-prikljucna">` wrapper sa 3 unutrašnje `<section>`)
  - [x] Subtask 3.2: Include `brands/partials/_jeegee_hero.html` u hero section
  - [x] Subtask 3.3: Include `brands/partials/_category_showcase.html` u categories section
  - [x] Subtask 3.4: Conditional render catalog CTA banner sa Wave Divider iznad (samo ako `brand.catalog_pdf` postoji); direct `<a>` markup sa target/rel/download (mirror Story 2-6 SM-D22)
  - [x] Subtask 3.5: Verifikovati sve user-facing string-ovi koriste `{% translate %}` / `{% blocktranslate %}`; NEMA hardcoded srpski string-ova; NEMA ćirilice
  - [x] Subtask 3.6: Verifikovati TAČNO 1 `<h1>` (kroz hero_overlay_card partial) + single `<main>` (samo iz base.html) + heading hijerarhija h1 → h2 → h3

- [x] **Task 4: `templates/brands/partials/_jeegee_hero.html` (AC4)**
  - [x] Subtask 4.1: Kreirati `templates/brands/partials/_jeegee_hero.html` per AC4 source skeleton (defensive `{% if brand.logo %}` guard + include hero_overlay_card partial sa fiksnim `variant="jeegee"` + bullets="")
  - [x] Subtask 4.2: Verifikovati TAČNO `variant="jeegee"` (NIJE "blue") — KRITIČNO za CSS klase mapping (vidi SM-D9)

- [x] **Task 5: `templates/brands/partials/_category_showcase.html` (AC5)**
  - [x] Subtask 5.1: Kreirati `templates/brands/partials/_category_showcase.html` per AC5 source skeleton (Section Eyebrow + h2 + grid wrapper iterirajući `categories` context list)
  - [x] Subtask 5.2: Per-kategorija renderovati `<article class="coric-category-card">` sa conditional icon (`{% if category.icon %}`) + h3 + conditional description + CTA `<a>` direct markup
  - [x] Subtask 5.3: CTA href koristi **direct string interpolation** `/{{ LANGUAGE_CODE }}/mehanizacija/prikljucna/{{ category.slug }}/` (NE `{% url %}` template tag — per SM-D5)
  - [x] Subtask 5.4: CTA aria-label koristi `{% blocktranslate with category=category.name %}Pogledaj kategoriju: {{ category }}{% endblocktranslate %}` (a11y must-have)
  - [x] Subtask 5.5: `{% empty %}` clause sa empty state porukom „Kategorije priključne mehanizacije su u pripremi."
  - [x] Subtask 5.6: data-testid atributi prisutni: `category-showcase-grid`, `category-card-{slug}`, `category-card-cta-{slug}` (za Playwright Story 9-8)

- [x] **Task 6: `static/css/components/category-showcase.css` + `main.css` Edit (AC6)**
  - [x] Subtask 6.1: Kreirati `static/css/components/category-showcase.css` sa svim selektorima iz AC6 source — sve vrednosti kroz `var(--token)` reference iz Story 1-5 tokens.css; svi BEM klasi imaju `coric-` prefix; `@media (prefers-reduced-motion: reduce)` block za onemogućavanje transform animacije
  - [x] Subtask 6.2: Editovati `static/css/main.css` — dodati TAČNO 1 nova `@import url('./components/category-showcase.css');` linija POSLE postojeće `@import url('./components/used-machinery-listing.css');` (Story 2-9)
  - [x] Subtask 6.3: Verifikovati nema CDN referenci u novom CSS-u
  - [x] Subtask 6.4: Verifikovati svi BEM klasi imaju `coric-` prefix

- [x] **Task 7: i18n .po fajlovi update (AC8)**
  - [x] Subtask 7.1: Pokrenuti `uv run python manage.py makemessages -l sr -l hu -l en` u Docker container-u — regeneriše .po fajlove sa novim msgid-ovima iz Task 3-5 templates
  - [x] Subtask 7.2: Otvoriti `locale/sr/LC_MESSAGES/django.po`; popuniti `msgstr` za sve nove msgid (mirror AC8 listing)
  - [x] Subtask 7.3: Otvoriti `locale/hu/LC_MESSAGES/django.po`; popuniti hu prevode (Dev koristi DeepL/manual review)
  - [x] Subtask 7.4: Otvoriti `locale/en/LC_MESSAGES/django.po`; popuniti en prevode
  - [x] Subtask 7.5: Pokrenuti `uv run python manage.py compilemessages -l sr -l hu -l en` u Docker container-u — rebuild .mo fajlove
  - [x] Subtask 7.6: Smoke verifikacija — `grep -c "msgstr \"\"" locale/sr/LC_MESSAGES/django.po` brojanje empty msgstr (0 očekivano za nove msgid-ove)

- [ ] **Task 8: Manuelni Dev smoke check + Lighthouse a11y audit (AC9)**
  - [ ] Subtask 8.1: Dev pokrene `just dev` (Docker Compose local)
  - [ ] Subtask 8.2: Dev verifikuje data migracija primenjena (`migrate brands`); shell verifikuje Jeegee + 3 Category postoje u DB
  - [ ] Subtask 8.3: Dev poseti `http://localhost:8000/sr/mehanizacija/prikljucna/` u Chrome; verifikuje sve sekcije rade per AC9 checklist (hero + 3 kategorije + opciono catalog CTA)
  - [ ] Subtask 8.4: Dev aktivira `prefers-reduced-motion: reduce` u DevTools Rendering panel; reload; verifikuje hover na kartice ne triggeruje transform
  - [ ] Subtask 8.5: Dev testira empty state (privremeno DELETE 3 Category u shell-u, reload, verifikuje empty state poruku, restore)
  - [ ] Subtask 8.6: Dev testira coming-soon stanje (privremeno set `jeegee.is_coming_soon=True` u shell-u, reload, verifikuje brand_coming_soon.html render, reset)
  - [ ] Subtask 8.7: Dev testira Http404 stanje (privremeno DELETE Jeegee brand u shell-u, reload, verifikuje 404 sa kustomizovanom porukom, restore migracijom)
  - [ ] Subtask 8.8: Dev pokrene Lighthouse audit u CLI mode-u (per AC9 § Lighthouse JSON artifact preservation): `lighthouse http://localhost:8000/sr/mehanizacija/prikljucna/ --output=json --output-path=_bmad-output/implementation-artifacts/2-10-lighthouse-YYYYMMDD.json --only-categories=accessibility,performance,seo --form-factor=mobile --chrome-flags="--headless"` (IMP-8 fix: zameni `YYYYMMDD` sa stvarnim datumom npr. `20260530`; PowerShell ne expand-uje `$(date +%Y%m%d)`). Verifikuje Accessibility ≥ 95 + Performance ≥ 80; dokumentuje sve 3 skor-ove u Dev Agent Record § Completion Notes sekciji PRE Step-04 commit
  - [ ] Subtask 8.9: Dev verifikuje keyboard nav: skip link → Tab kroz hero (brand_logo img je ne-fokusabilan jer nije `<a>`) → 3 kategorija CTA dugmad → opciono catalog CTA → footer; fokus indicator vidljiv (`:focus-visible` outline iz tokens)

- [x] **Task 9: TEA-deliverable — testovi (RED phase, Step 3, NIJE Dev scope)** _(NAPOMENA: ovaj task je listed for clarity — TEA agent u Step 3 piše testove pre Dev-ovog GREEN phase implementacije; Dev NIKAD ne piše testove per project-context.md § Test discipline linija 294)_
  - **Minimum test count per AC (~32 tests total — +2 dodato u iter 1/5 validation fix: AC3 aria-label regression guard + AC5 partial-degradation whitelist test):**
  - [x] Subtask 9.1: TEA kreira `apps/brands/tests/test_urls_jeegee.py` — **AC1: 4 tests**
    - `test_jeegee_prikljucna_url_resolves_sr_locale` — GET `/sr/mehanizacija/prikljucna/` → HTTP 200
    - `test_jeegee_prikljucna_url_resolves_hu_locale` — GET `/hu/mehanizacija/prikljucna/` → HTTP 200
    - `test_jeegee_prikljucna_url_resolves_en_locale` — GET `/en/mehanizacija/prikljucna/` → HTTP 200
    - `test_jeegee_prikljucna_url_no_collision_with_brand_detail` — verifikuje da `/sr/traktori/agri-tracking/` i dalje rezolvuje BrandDetailView (NIJE shadow-ovano novim pattern-om); paralelno `/sr/mehanizacija/polovna/` rezolvuje UsedMachineryListView
  - [x] Subtask 9.2: TEA kreira `apps/brands/tests/test_views_jeegee.py` — **AC2 + AC2.5: 5 tests**
    - `test_context_contains_brand_and_categories` — verifikuje `ctx["brand"].slug == "jeegee"` i `len(ctx["categories"]) == 3`
    - `test_categories_ordered_by_display_order` — verifikuje redoslijed: osnovna-obrada (10), priprema (20), masine-za-setvu (30)
    - `test_assert_num_queries_equals_2_lock_empirical` — `assertNumQueries(2)` placeholder; Dev lock-uje stvarni broj posle GREEN iter (mirror Story 2-9 SM-D27)
    - `test_coming_soon_jeegee_renders_brand_coming_soon_template` — postavi `is_coming_soon=True`, verifikuje `assertTemplateUsed(response, 'brands/brand_coming_soon.html')`; categories NIJE u kontekstu
    - `test_404_when_jeegee_brand_does_not_exist` — DELETE Jeegee, GET URL → HTTP 404 sa porukom „Jeegee brand nije konfigurisan u sistemu."
  - [x] Subtask 9.3: TEA kreira `apps/brands/tests/test_templates_jeegee.py` — **AC3 + AC4 + AC5 + AC8: ~14 tests** (+2 u iter 1/5 fix: AC3 aria-label regression + AC5 partial-degradation whitelist)
    - **AC3 page structure (4 tests):**
      - `test_jeegee_prikljucna_renders_exactly_one_h1` — BeautifulSoup parse → 1 `<h1>` (brand.name iz hero)
      - `test_jeegee_prikljucna_renders_exactly_one_main` — BeautifulSoup parse → 1 `<main>` (single-main regression guard, mirror Story 2-6/2-7/2-8/2-9)
      - `test_jeegee_prikljucna_sections_render_in_correct_order` — hero → categories → opciono catalog_cta
      - `test_outer_section_has_aria_label_not_aria_labelledby` — BeautifulSoup parse outer `<section class="coric-brand-detail coric-jeegee-prikljucna">`; verifikuje `aria-label` atribut postoji i sadrži „priključna mehanizacija" string; verifikuje da NEMA `aria-labelledby` atribut (CRITICAL-1 regression guard, SM-D8 lock)
    - **AC4 hero (2 tests):**
      - `test_jeegee_hero_renders_jeegee_variant_repeating_element` — rendered HTML sadrži `coric-repeating-element--jeegee` klasu (NE --blue, NE --jeegee-blue); SM-D9 verifikacija
      - `test_jeegee_hero_brand_logo_guard_works_when_logo_missing` — brand bez logo polja → hero section renderuje ali bez `<img>` tag-a
    - **AC5 category showcase (5 tests):**
      - `test_category_showcase_renders_3_cards` — BeautifulSoup parse `.coric-category-card` → 3 instances
      - `test_category_card_cta_href_uses_locale_prefixed_url` — verifikuje CTA href je `/sr/mehanizacija/prikljucna/osnovna-obrada-zemljista/` (string interpolation per SM-D5)
      - `test_category_card_cta_aria_label_includes_category_name` — aria-label sadrži „Pogledaj kategoriju: Osnovna obrada zemljišta"
      - `test_category_showcase_empty_state_renders_when_no_categories` — DELETE 3 Category, render → empty state poruka „Kategorije priključne mehanizacije su u pripremi."
      - `test_only_seeded_mehanizacija_categories_with_whitelist_slugs_appear` — IMP-3 partial-degradation guard: kreira 4. MEHANIZACIJA Category sa non-whitelisted slug-om (npr. `random-slug`, name=„Random Kategorija"); verifikuje da renderovana strana ima TAČNO 3 kartice (samo whitelist slug-ovi: osnovna-obrada-zemljista, priprema-zemljista, masine-za-setvu) i da non-whitelisted category NIJE u DOM-u
    - **AC8 i18n + a11y (3 tests):**
      - `test_html_lang_attribute_set_correctly` — `<html lang="sr">` na /sr/, `<html lang="hu">` na /hu/
      - `test_no_hardcoded_serbian_strings` — render HTML, verifikuje sve user-facing string-ovi prolaze kroz translation (greppable patterns za poznate string-ove); akt-pe testing kroz `override_settings(LANGUAGE_CODE='en')` i verifikacija da bar deo string-ova menja vrednosti
      - `test_no_cirillic_characters_in_rendered_html` — render HTML, regex assertion da nema `[А-Яа-яЁё]` karaktera
  - [x] Subtask 9.4: TEA kreira `apps/brands/tests/test_migration_0003_seed_jeegee.py` — **AC7: 4 tests**
    - `test_migration_creates_jeegee_brand_with_correct_fields` — apply 0003, verifikuje Brand sa slug="jeegee", name="Jeegee", brand_color="#00A4E9", is_coming_soon=False
    - `test_migration_creates_3_mehanizacija_categories_with_correct_slugs` — verifikuje 3 Category sa is_for="mehanizacija" i odgovarajućim slug-ovima + display_order vrednostima (10, 20, 30)
    - `test_migration_is_idempotent` — apply 0003 dva puta, verifikuje samo 1 Brand + 3 Category u DB (no duplicates kroz `get_or_create`)
    - `test_migration_reverse_deletes_seeded_data` — apply 0003 pa reverse 0002, verifikuje Jeegee Brand + 3 Category obrisane
  - [x] Subtask 9.5: TEA kreira `tests/test_jeegee_static_assets.py` — **AC6: 3 tests**
    - `test_category_showcase_css_imported_in_main_css` — grep `static/css/main.css` za `@import url('./components/category-showcase.css');`
    - `test_category_showcase_css_uses_only_var_tokens` — grep `category-showcase.css` za magic hex (`#[0-9a-fA-F]{3,6}` regex; allow named CSS keywords like `white`/`transparent`/`none`); verifikuje 0 magic colors
    - `test_category_showcase_css_has_coric_prefix_on_all_classes` — grep CSS selektore, verifikuje svi class-ovi imaju `coric-` prefix
  - [x] Subtask 9.6: TEA dokumentuje **AC9 manuelni smoke check** kao SINGLE manual checklist item u retrospective (NE automated test): „Dev manualno verifikuje Lighthouse a11y ≥ 95 + `prefers-reduced-motion` Chrome DevTools test"
  - [x] Subtask 9.7: TEA verifikuje testovi padaju u RED phase (`uv run pytest apps/brands/tests/test_urls_jeegee.py apps/brands/tests/test_views_jeegee.py apps/brands/tests/test_templates_jeegee.py apps/brands/tests/test_migration_0003_seed_jeegee.py` ima fail-ove zbog missing view/urls/templates/migracije)
  - [x] Subtask 9.8: TEA commit-uje test fajlove PRE Dev GREEN phase (`test(brands): Story 2.10 RED-phase tests — Jeegee priključna landing view + templates + data migracija + static assets`)

## Dev Notes

### Postojeća `apps/brands/` struktura (snimak pre Edit-a — regression guard)

Pre Story 2.10, `apps/brands/` direktorijum sadrži (live verifikovano 2026-05-30):

```
apps/brands/
├── __init__.py
├── admin.py             (Story 2.1)
├── apps.py
├── migrations/
│   ├── __init__.py
│   ├── 0001_initial.py  (Story 2.1)
│   └── 0002_alter_brand_created_at.py
├── models.py            (Story 2.1 — Brand, Series, Category, Subcategory)
├── tests/               (Story 2.1 + 2.6 testovi)
├── translation.py       (Story 2.1)
├── urls.py              (Story 2.6 — namespace "brands", pattern traktori/<slug:slug>/)
└── views.py             (Story 2.6 — BrandDetailView)
```

**Story 2.10 dodaje (DELTA — `apps/brands/`):**
- `apps/brands/views.py` EDIT — ADD `JeegeePrikljucnaView(DetailView)` POSLE postojeće `BrandDetailView`; ADD module-level konstante `_JEEGEE_BRAND_SLUG`, `_PRIKLJUCNA_CATEGORY_SLUGS`; EDIT import za Category; ADD `Http404` import
- `apps/brands/urls.py` EDIT — ADD path `mehanizacija/prikljucna/`; EDIT import za `JeegeePrikljucnaView`
- `apps/brands/migrations/0003_seed_jeegee_and_prikljucna_categories.py` NOVO — data migracija sa RunPython

**Story 2.10 NE menja:**
- `apps/brands/models.py` (regression guard za Story 2.1 + 2.6 testove)
- `apps/brands/admin.py`, `apps/brands/translation.py`, `apps/brands/migrations/0001` i `0002`, `apps/brands/apps.py`
- `apps/products/` (kompletno netaknuto — Story 2.10 NE query-uje Product modele)
- `apps/brands/views.py` `BrandDetailView` klasa (Story 2.6 deliverable — ostaje netaknuta)
- `templates/brands/brand_detail.html`, `templates/brands/brand_coming_soon.html`, `templates/brands/partials/*` (Story 2.6 deliverables; Story 2.10 REUSE-uje brand_coming_soon.html bez izmena)

### Multi-locale URL slug-ovi i Category.name prevod-i (open question — pragmatic v1 fallback)

Story 2.10 URL koristi srpski slug `prikljucna` (ASCII transliteracija); multi-locale URL aliasing (npr. `/hu/mellekkellek/...`) je Story 6-6 scope (apps.seo locale-aware slug-ovi). V1 funkcionalno radi na svim locale-ima ali svi koriste sr URL prefix.

Category.name polja (Story 2.1 modeltranslation D2 — auto-discovery): seed migracija (`0003`) postavlja `name` u srpsku vrednost. `django-modeltranslation` auto-popunjava `name_sr` polje istim string-om kroz fallback logic (Story 2.1 NOTE — modeltranslation patch_indexes registracija na startup-u). Polja `name_hu` i `name_en` ostaju NULL/empty u v1. Template `{{ category.name }}` koristi aktivni locale resolver koji vraća `name_<lang>` ili fallback na `name_sr` ako nema prevod. Posledica: posetilac /hu/ ili /en/ strane vidi srpski naziv kategorije („Osnovna obrada zemljišta") — pragmatic UX trade-off za v1.

**Story 8-5 (Category CRUD sa hierarchy admin):** admin omogućava admin-u da popuni `name_hu` i `name_en` polja kroz django-modeltranslation tabovi u Django admin GUI; bez admin-a UI-ja, Dev može popuniti polja kroz Django shell (npr. `Category.objects.filter(slug='osnovna-obrada-zemljista').update(name_hu='...', name_en='...')`) ili kroz dodatnu data migraciju.

**Story 6-5 (i18n fallback marker tooltip):** dodaje UI marker (tooltip) na nepreveden tekst za signaliziranje editor-ima da treba popuniti prevod — ne menja Story 2-10 fall-back ponašanje.

### Repeating Element variant naming (SM-D9 — KRITIČNO za Dev)

**Story 2-6 `_hero_section.html` koristi `variant="blue"` (linije 4-10 — live verifikovano)** koji rezolvira na `coric-repeating-element--blue` BEM klasu — ali ta klasa **NE postoji u CSS-u**. `static/css/components/repeating-element.css` definiše SAMO dve variant klase: `--green` (linija 11) i `--jeegee` (linija 14). Story 2-6 hero render je BUG (Repeating Element watermark NEMA background-color za brendove sa brand_color="#00A4E9" — ali Story 2-6 nije renderovao Jeegee jer Jeegee brand nije postojao u DB; bug je dormant).

**Story 2-10 koristi TAČAN naming `variant="jeegee"`** (kanonski naming koji matchuje CSS klasu). Dev MORA verifikovati pre commit-a:
- `_jeegee_hero.html` linija sa include-om sadrži `variant="jeegee"` (tačno tako; lowercase; bez prefiksa)
- Rendered HTML sadrži `class="coric-repeating-element coric-repeating-element--jeegee"`
- Background-color computed style je `#00a4e9` (kroz `var(--color-jeegee-blue)` token resolution)

**Out-of-scope za Story 2-10:** Fix Story 2-6 `_hero_section.html` variant="blue" → "jeegee" za tractor brendove sa brand_color="#00A4E9". Razlog: Story 2-6 trenutno nema tractor brend sa Jeegee blue color (Agri-Tracking ima zelenu, ostali takođe); bug je dormant. Story 9-10 (final polish) ili zaseban tech-debt commit može fix-ovati.

### CTA URL strategy (SM-D5 — load-bearing decision)

Story 2-10 koristi **direct string interpolation** za CTA href umesto `{% url %}` template tag-a. Razlog je da URL pattern `subcategory_list` (Story 2-11) NE postoji do Story 2-11 GREEN phase-a. Ako Story 2-10 dođe pre Story 2-11 (očekivano redoslijed per sprint-status.yaml), `{% url 'brands:subcategory_list' kwargs={...} %}` bi raise `NoReverseMatch` tokom template render-a.

**Implementacija:** `<a href="/{{ LANGUAGE_CODE }}/mehanizacija/prikljucna/{{ category.slug }}/">` (direct interpolation).

**Trade-off:**
- ✅ Render uvek prolazi (no NoReverseMatch crash)
- ✅ Slug-ovi su ASCII (osnovna-obrada-zemljista, priprema-zemljista, masine-za-setvu) — URL kompozicija je čista
- ✅ 1-line implementacija; nema potrebe za placeholder URL pattern + view + template (mirror Story 2-6 C8 fix za products je odbačen jer Story 2-11 immediately uvodi pattern — net negative)
- ❌ Klik na CTA u v1 produkuje 404 (acceptable — Story 2-11 immediately rešava)
- ❌ Refaktor obavezan u Story 2-11 (direct interpolation → `{% url %}` tag) — load-bearing TODO za Story 2-11 SM

**Story 2-11 SM MORA u svom create-story koraku eksplicitno enumerisati ovaj refaktor u svojoj Tasks/Subtasks sekciji** (npr. „Subtask X.Y: Editovati `templates/brands/partials/_category_showcase.html` linije Z — direct interpolation `/{{ LANGUAGE_CODE }}/mehanizacija/prikljucna/{{ category.slug }}/` zamenuti sa `{% url 'brands:subcategory_list' kwargs={'category_slug': category.slug} %}` ili kako god se imenuje pattern").

### CTA reuse — Pill Button partial DA-koriščen u kategorija karticama, NE-koriščen u catalog CTA banner-u

**`_category_showcase.html` (AC5):** Direct `<a class="coric-button coric-button--primary">` markup (NIJE `{% include "partials/pill_button.html" %}` partial). Razlog: aria-label MORA biti dinamički prosleđen sa `{% blocktranslate %}` interpolation (per a11y must-have za WCAG SC 2.4.4 link purpose) — Story 1-7 pill_button.html partial podržava `aria_label` parametar (live verifikovano linija 3 partial-a) ali NE podržava blocktranslate as variable — partial bi primio resolved string. Direct markup je čistiji i omogućava inline blocktranslate.

**Alternativa:** Story 2-10 mogla je koristiti pill_button.html partial sa pre-rezolvanim aria-label vrednostima kroz view kontekst (npr. `category.cta_aria_label = blocktranslate(...)` u view). Odbačeno — view bi trebalo da reflectsl-uje UI strings, što je layering anti-pattern (view treba da fokusira na data, template na presentation). Direct markup u template-u je clean separation.

**`_catalog_cta.html` (AC3 § catalog CTA banner — opciono):** Direct `<a href="..." target="_blank" rel="noopener noreferrer" download class="coric-button coric-button--primary">` markup (NIJE pill_button.html partial). Razlog: ISTI razlog kao Story 2-6 SM-D22 — Story 1-7 pill_button.html partial NE podržava `target`, `rel`, `download` kwarg-e. Modifikacija partial-a je out-of-scope (potencijalno breaking change za sve postojeće konzumente). Vizuelna konzistentnost kroz reuse `coric-button coric-button--primary` BEM klase.

**Konvencija za Story 2-10 i naredne:** Pill Button partial se reuse-uje SAMO za **standard CTA** bez specijalnih HTML atributa (target, rel, download, dynamic aria-label). Za CTA-ove sa specijalnim HTML atributima, koristi se direct markup sa `coric-button coric-button--primary` BEM reuse. Story 2-6 SM-D22 (catalog CTA) i Story 2-10 SM-D6 (category showcase CTA + catalog CTA) su precedent.

### `static/css/main.css` Edit DELTA

Story 1-7 + 1-8 + 2-5 + 2-6 + 2-7 + 2-8 + 2-9 je registrovala niz `@import url('./components/...');` linija. Sintaksa je STROGO `url(...)` wrapper sa leading `./` (NE bare-string `@import './components/...';`).

Story 2-10 dodaje 1 nova linija na kraj postojećih @import linija (mirror Story 2-9 pattern):

```css
/* postojece linije ostaju netaknute */
@import url('./components/used-machinery-listing.css');  /* Story 2-9 */
@import url('./components/category-showcase.css');       /* NOVO Story 2-10 */
```

### `apps/brands/views.py` EDIT DELTA

Trenutni `apps/brands/views.py` (Story 2-6 deliverable; live snapshot 2026-05-30; vidi `apps/brands/views.py` linije 1-85):

```python
"""Brand listing strana — Story 2.6 (Epic 2 Public Catalog).
...
"""

from __future__ import annotations

from django.db.models import Case, CharField, IntegerField, Prefetch, Value, When
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView

from apps.brands.models import Brand, Series
from apps.products.models import Product, ProductSpecification, ProductTestimonial


class BrandDetailView(DetailView):
    ...
```

**Story 2-10 EDIT-ovi (3 specifična placement-a):**

1. **Module docstring** — POSLE postojećeg docstring-a (linije 1-10), dodati napomenu:
   ```python
   """Brand listing strana — Story 2.6 + Jeegee Priključna Mehanizacija — Story 2.10 (Epic 2 Public Catalog).
   ...
   """
   ```
   (Opciono — Dev odlučuje; pragmatic je samo dodati nov inline comment iznad JeegeePrikljucnaView klase.)

2. **Imports** — EDIT linije 18 i ADD `Http404`:
   ```python
   from django.http import Http404  # NOVO Story 2.10
   from apps.brands.models import Brand, Category, Series  # EDIT Story 2.10 (dodat Category)
   from apps.products.models import Product, ProductSpecification, ProductTestimonial  # NETAKNUT
   ```

3. **Konstante** — POSLE imports, PRE `BrandDetailView` klase:
   ```python
   # Story 2.10 — Jeegee priključna mehanizacija landing strana
   _JEEGEE_BRAND_SLUG = "jeegee"
   _PRIKLJUCNA_CATEGORY_SLUGS = (
       "osnovna-obrada-zemljista",
       "priprema-zemljista",
       "masine-za-setvu",
   )
   ```

4. **Nova klasa** — POSLE postojeće `BrandDetailView` klase (linija 85):
   ```python
   class JeegeePrikljucnaView(DetailView):
       """Jeegee priključna mehanizacija landing strana — Story 2.10."""
       ...  # Per AC2 source skeleton
   ```

### `apps/brands/urls.py` EDIT DELTA

Trenutni `apps/brands/urls.py` (Story 2-6 deliverable; live snapshot 2026-05-30):

```python
"""URL routing za apps.brands — Story 2.6."""

from django.urls import path

from apps.brands.views import BrandDetailView

app_name = "brands"

urlpatterns = [
    path("traktori/<slug:slug>/", BrandDetailView.as_view(), name="detail"),
]
```

**Story 2-10 EDIT-ovi:**

1. **Module docstring** — EDIT linija 1:
   ```python
   """URL routing za apps.brands — Story 2.6 + Story 2.10."""
   ```

2. **Imports** — EDIT linija 5:
   ```python
   from apps.brands.views import BrandDetailView, JeegeePrikljucnaView
   ```

3. **urlpatterns** — ADD novi path POSLE postojećeg:
   ```python
   urlpatterns = [
       path("traktori/<slug:slug>/", BrandDetailView.as_view(), name="detail"),
       path("mehanizacija/prikljucna/", JeegeePrikljucnaView.as_view(), name="jeegee_prikljucna"),  # NOVO Story 2.10
   ]
   ```

### Relevantni Modeli (iz Story 2-1)

**Brand** (apps/brands/models.py, Story 2-1) — Story 2-10 koristi sledeća polja:
- `slug` (SlugField, unique, max_length=140) — koristi se za hardcoded `slug="jeegee"` lookup u view-u
- `name` (CharField, translatable) — koristi se za h1 u hero (kroz brand.name)
- `logo` (ImageField, optional) — koristi se conditionally u _jeegee_hero.html
- `description` (TextField, translatable) — može se koristiti u meta description ali Story 2-10 koristi blocktranslate template string umesto
- `slogan` (CharField, translatable) — opciono renderuje se kroz hero_overlay_card partial (ali u Story 2-10 hero, bullets je empty per SM-D10)
- `brand_color` (CharField hex #RRGGBB, optional) — NIJE koriščen u Story 2-10 templates (Jeegee variant je hardcoded „jeegee" u _jeegee_hero.html; brand.brand_color je informativan field za admin)
- `catalog_pdf` (FileField, optional) — koristi se conditionally u catalog CTA banner sekciji
- `is_coming_soon` (BooleanField, default False) — koristi se za template branching u `get_template_names()`
- `get_absolute_url()` → `reverse("brands:detail", kwargs={"slug": self.slug})` — N/A za Story 2-10 (Jeegee URL nije generic brand_detail URL; Jeegee koristi specijalni `brands:jeegee_prikljucna` URL name bez slug kwarg-a)

**Category** (apps/brands/models.py, Story 2-1) — Story 2-10 koristi sledeća polja:
- `slug` (SlugField, globally unique) — koristi se za CTA href interpolation
- `name` (CharField, translatable) — koristi se za h3 u kartici
- `description` (TextField, translatable) — koristi se za p u kartici (truncatewords:25)
- `is_for` (CharField, choices=CategoryScope) — koristi se za queryset filter (`is_for="mehanizacija"`)
- `display_order` (PositiveSmallIntegerField, default 0) — koristi se za ordering queryset-a
- `icon` (CharField, Bootstrap Icons class) — v1 svi seed-ovani su empty string; conditional render `{% if category.icon %}` će uvek evaluuirati False u v1
- `get_absolute_url()` → `reverse("brands:category_traktori"/"brands:category_mehanizacija", kwargs={"slug": ...})` — NIJE koriščen u Story 2-10 (CTA href je direct interpolation za URL koji ne postoji do Story 2-11)

### URL pattern (i18n_patterns)

`config/urls.py` koristi `i18n_patterns(...)` (Story 1-4); Story 2-10 URL će biti:
- `sr` locale: `/sr/mehanizacija/prikljucna/`
- `hu` locale: `/hu/mehanizacija/prikljucna/`
- `en` locale: `/en/mehanizacija/prikljucna/`

**NAPOMENA:** „mehanizacija" + „prikljucna" su hardcoded srpski URL segment-i. Multi-locale URL aliasing je Story 6-6 scope.

### Slika lazy loading strategy

Story 2-10 strana je vrlo light na slike:
- Brand logo (hero) — opciono; renderovan kroz hero_overlay_card partial sa direct `<img src="{{ brand_logo }}">` (NE `{% responsive_picture %}` — partial je Story 1-7 deliverable koji ne koristi responsive_picture); `loading="eager"` (above-the-fold)
- Category kartica ikone — v1 NEMA renderovanih ikona (Bootstrap Icons font deferred per Story 2-6 SM-D18)
- Catalog CTA banner — NEMA slika (samo Wave Divider SVG + tekst + CTA)

Lazy loading nije relevantan u v1; Story 9-10 polish može optimizovati brand logo kroz responsive_picture sa `loading="lazy"` ako se ispostavi LCP problem.

### Brand logo `format='PNG'` policy (Story 2-3 MP-D5 contract — NIJE primenjivo u Story 2-10)

Story 2-3 MP-D5 nalaže: sve slike koje koriste `{% responsive_picture %}` i imaju transparency MORAJU prosediti `format='PNG'` kwarg. **Story 2-10 NE koristi `{% responsive_picture %}` u nijednom novom template-u** — brand logo se renderuje kroz Story 1-7 `hero_overlay_card.html` partial koji koristi direct `<img>` tag (linija 5 — `<img src="{{ brand_logo }}" alt="{{ brand_logo_alt|default:'' }}">`). Transparency preservation je delegated u Story 1-7 partial scope.

Ako Story 9-10 polish odluči da migrira brand logo render iz direct `<img>` u `{% responsive_picture %}`, MP-D5 contract će tada postati primenjiv i `format='PNG'` mora biti dodato.

### Dev pre-commit checklist (i18n + a11y)

Pre `git commit` Dev MORA proveriti:

- [ ] Did I add `lang="sr"` wrapper na Category.name u template-u? **Odgovor:** NE — explicit defer Story 6-5 (UX-DR-22 fallback marker tooltip); v1 prikazuje sr name na svim locale-ima bez markera (vidi SM-D16 + AC8 IMP-4 fix). Bez akcije u Story 2-10.
- [ ] Did I verify outer `<section>` koristi `aria-label` (NE `aria-labelledby`)? CRITICAL-1 regression guard — vidi SM-D8 lock.
- [ ] Did I run `just messages` + `just compilemessages`? AC8 verification.
- [ ] Did I run `manage.py check` (exit 0) + `migrate brands` (data migracija primenjena)?
- [ ] Did I add `.coric-empty-state` CSS rule u `category-showcase.css`? IMP-2 fix.

### `prefers-reduced-motion` respect (UX-DR-13 + NFR-2 + a11y must-have)

**1 mesto gde prefers-reduced-motion mora biti respektovan u Story 2-10:**

1. **CSS hover transform animacija na kategorija karticama** (`category-showcase.css`): `@media (prefers-reduced-motion: reduce) { .coric-category-card { transition: none; } .coric-category-card:hover, .coric-category-card:focus-within { transform: none; } }`

Story 2-10 NEMA JavaScript-a pa NEMA JS-driven animacija koje bi trebalo respektovati reduced-motion preference.

**Test plan:** Dev manuelni smoke (AC9 § prefers-reduced-motion test); automated test bi koristio Playwright `page.emulateMedia({reducedMotion: 'reduce'})` (Story 9-8 scope).

### Decision Log (SM-D*)

- **SM-D1:** Story 2-10 je STATIČKA listing strana — NEMA HTMX, NEMA JS, NEMA filtera, NEMA paginacije, NEMA sort dropdown-a. Razlika od Story 2-8 (tractor listing sa HTMX filterima) i Story 2-9 (used listing sa HTMX multi-dropdown filterima) je fundamentalna: Story 2-10 je *landing strana* koja samo navigira korisnika nadalje (do Subcategory Listing iz Story 2-11), NIJE *catalog browse* strana. Rationale: epics.md spec za Story 2-10 ne pominje filtere ili paginaciju; strana ima 3 fiksne kategorije koje su brže prikazane staticki nego sa HTMX overhead-om.

- **SM-D2:** Jeegee Brand + 3 mehanizacija Category instance se seed-uju kroz **data migraciju** (`apps/brands/migrations/0003_seed_jeegee_and_prikljucna_categories.py`). Alternative razmotrene:
  - **(a) Django admin manual create** — odbačeno: nije reproducible, Dev mora ručno setovati instance na svakom env-u (local, staging, prod); test fixtures bi trebalo da dupliciraju entries.
  - **(b) Fixture file (`.json` ili `.yaml`)** — odbačeno: fixture-i nisu deo standardnog deploy flow-a (per project-context.md `ops/deploy/deploy.sh` koji koristi `migrate` ali ne `loaddata`); admin bi morao manually loaddata posle migracije.
  - **(c) Data migracija sa get_or_create + reverse callable** — IZABRANO: idempotentna, reproducible across env-ova, deploy-time primenjena kroz standardan migrate flow (per ops/deploy/deploy.sh), reverse-able za rollback. **Story 2-10 kanonski pattern za seeding initial brand + category data koje view direktno query-uje.**

- **SM-D3:** URL je **statički** `/mehanizacija/prikljucna/` bez slug kwarg-a (NIJE `/<brand-slug>/prikljucna/`). Razlog: Story 2-10 je dedicated Jeegee landing strana — Jeegee je jedini priključni brand u portfolio-u (per project arch domain), pa generic brand_slug parameter je premature abstraction. Story 2-12 (HZM Radne Mašine + Tulip MIX) takođe koristi dedicated statičke URL-ove (`/mehanizacija/radne-masine/`, `/mehanizacija/mix-prikolice/`) jer su to drugi dedicated brand-listing strane. Generic URL pattern `/<brand-slug>/<category-scope>/` bi bio yagni u v1 — ako budu potrebne dodatne brand listing strane, refaktor je trivijalan.

- **SM-D4:** Story 2-10 koristi **dedicated `_jeegee_hero.html` partial** umesto reuse Story 2-6 `_hero_section.html`. Razlog: Story 2-6 hero partial ima conditional `brand_color → variant` mapping koji je tractor-brand-generic (`{% if brand.brand_color|lower == "#00a4e9" %}variant="blue"{% else %}variant="green"{% endif %}` — live `templates/brands/partials/_hero_section.html:3-10`). Jeegee uvek koristi hardcoded `variant="jeegee"` pa je čistije imati thin dedicated partial bez conditional logike. Trade-off:
  - ✅ Čista implementacija (~10 linija); nema conditional grananja u template-u za jednu konkretnu brand stranu
  - ✅ Story 2-6 `_hero_section.html` ostaje netaknut (nemoram pravim breaking change za sve postojeće tractor brendove)
  - ❌ Minimalna code duplikacija (3 linije markup-a — div wrapper + 2 include statement-a u if/else); acceptable
  - **Refaktor put:** Ako budu potrebne >= 2 dedicated landing strane (HZM, Tulip), kreira se generic `_static_brand_hero.html` partial koji prima `variant` kao explicit kwarg

- **SM-D5:** CTA URL u `_category_showcase.html` koristi **direct string interpolation** (`/{{ LANGUAGE_CODE }}/mehanizacija/prikljucna/{{ category.slug }}/`) umesto `{% url %}` template tag-a jer URL pattern za Subcategory Listing nije registrovan do Story 2-11. Vidi „CTA URL strategy" sekcija iznad za detaljno rationale + refaktor plan za Story 2-11. **IMP-5 fix:** koristi bare `{{ LANGUAGE_CODE }}` (NE `{{ request.LANGUAGE_CODE }}`) — codebase konvencija (base.html + language_switcher_*.html sve koriste bare `{{ LANGUAGE_CODE }}`); obe forme funkcionalno rade jer su i18n + request context processor-i enabled u `config/settings/base.py:73-74`, ali bare forma je codebase precedent.

- **SM-D6:** `_category_showcase.html` koristi **direct `<a>` markup** za CTA dugme (NIJE `{% include "partials/pill_button.html" %}`). Razlog: aria-label MORA biti `{% blocktranslate with category=category.name %}Pogledaj kategoriju: {{ category }}{% endblocktranslate %}` (a11y must-have); pill_button.html partial prima `aria_label` kao string-resolved parametar — ne podržava blocktranslate as kwarg vrednost. Vidi „CTA reuse" sekcija iznad za detaljno rationale + konvencija za kasnije Story-je.

- **SM-D7:** `JeegeePrikljucnaView.get_object()` raise **Http404** sa kustomizovanom porukom „Jeegee brand nije konfigurisan u sistemu." ako Jeegee Brand instance ne postoji u DB (umesto raise `Brand.DoesNotExist` koji bi proizveo Django default 500). Razlog: defensive guard za scenario gde admin manualno DELETE Jeegee Brand kroz admin GUI ili gde data migracija nije primenjena na fresh env. Http404 je user-friendly (Django default 404 strana je razumljiva), ne crash. Alternativa „render empty page sa placeholder porukom" je odbačena (404 je semantički tačno — strana ne postoji jer brand ne postoji). **IMP-1 fix napomena:** custom Http404 message surface-uje se SAMO u `DEBUG=True` dev mode-u + log fajlovima/Sentry capture-u; production 404 strana koristi Django default template (generic „Page not found" copy) — korisnik ne vidi srpsku porukу u prod-u. Acceptable za v1; za user-visible custom 404 page (sa srpskom porukom i nazad-na-Home CTA), buduća tech-debt story treba da uvede custom `templates/404.html` template. Alternativa `from django.shortcuts import get_object_or_404` je IMP-1 odbijena (vidi AC2 imports rationale).

- **SM-D8 (LOCKED — CRITICAL-1 iter 1/5 fix):** I outer `<section class="coric-brand-detail coric-jeegee-prikljucna">` wrapper i unutrašnja hero `<section>` koriste `aria-label` umesto `aria-labelledby` jer `<h1>` unutar Story 1-7 `hero_overlay_card.html` partial-a NEMA id atribut (verifikovano linija 8: `<h1 class="coric-hero-overlay-card__title">{{ title }}</h1>`). Iteracija 0 spec-a je sadržala `aria-labelledby="jeegee-prikljucna-title"` na outer wrapper-u koji je referencirao ID koji NIJEDAN element ne nosi (dangling aria reference — screen reader fallback na bezimeni landmark); validator je detektovao internal contradiction sa SM-D8 koji explicit odbija modifikaciju Story 1-7 partial-a. **Fix:** outer wrapper koristi `aria-label="{{ brand.name }} priključna mehanizacija"` (blocktranslate-wrapped za i18n). Razlog: modifikacija Story 1-7 partial-a da prima `title_id` kwarg je out-of-scope (potencijalno breaking change za sve postojeće konzumente — Story 2-6 brand_detail.html, Story 2-7 product_detail.html, Story 2-8 tractor_listing.html, Story 2-9 used_machinery_listing.html — koji bi morali biti updated). `aria-label` na outer landmark je acceptable alternativa (WCAG 2.1 SC 4.1.2 omogućava i `aria-label` i `aria-labelledby` za section accessible name). **Lock decision:** sve buduće landing strane sa Story 1-7 hero_overlay_card include-om koriste `aria-label` na outer wrapper-u dok partial ne dobije `title_id` kwarg podršku (potencijalno Story 9-10 polish). Trade-off:
  - ✅ Story 1-7 partial ostaje netaknut (regression guard za 4 postojeće konzumente)
  - ✅ A11y compliance preserved bez dangling aria reference
  - ✅ Outer landmark dobija semantičko ime „<brand> priključna mehanizacija" (kontekst za screen reader-e)
  - ❌ Minor inconsistency — sve OSTALE unutrašnje sekcije u jeegee_prikljucna.html koriste `aria-labelledby` (jer h2 id-jeve dodajemo u svojim partial-ima); outer wrapper i hero sekcija koriste `aria-label`
  - **Iter 2/5 note (dual aria-label verbosity ACK):** outer `aria-label="Jeegee priključna mehanizacija"` + hero `aria-label="Jeegee hero"` su INTENTIONAL — hero aria-label dodaje semantičku kvalifikaciju „hero" koja razdvaja brand-level landmark od specific-section landmark-a u screen reader navigaciji. Tri „Jeegee" pojave (outer landmark + hero landmark + h1) NISU WCAG SC 4.1.2 violacija (različiti elementi/role); verbose ali pristupačno. Future polishing (Story 9-10): rejavaditi treba li hero section uopšte ima own landmark name ili neka oslanjati na implicit h1 fallback.

- **SM-D9:** Repeating Element variant naming — Story 2-10 koristi TAČNO `variant="jeegee"` (NE „blue", NE „jeegee-blue") jer CSS klasa `.coric-repeating-element--jeegee` JE definisana u `static/css/components/repeating-element.css:14`. Vidi „Repeating Element variant naming" sekcija iznad za detaljno rationale + Story 2-6 hero bug napomena (out-of-scope za Story 2-10).

- **SM-D10:** Hero bullets su empty u v1 (mirror Story 2-6 SM-D10). Original UX spec za Story 2-10 hero nema bullets — hero card sadrži samo title + watermark.

- **SM-D11:** sprint-status.yaml update je counted SEPARATELY od deliverable file edit-ova (mirror Story 2-9 SM-D19 + Story 2-6 konvencija). Brojanje 4 NEW + 6 EDIT + 0 DELETE + 1 data migracija NE uračunava sprint-status.yaml jer je to rutinski SM completion handoff tracking fajl, NIJE deliverable.

- **SM-D12:** Story 2-10 NEMA cross-boundary brands → products import (mirror Story 2-6 SM-D16 exception NIJE primenjiv ovde). Razlog: view query-uje SAMO Brand + Category modele (oba u `apps.brands.models`); NEMA Product, ProductSpecification, ProductTestimonial query-ja. project-context.md § Cross-boundary import (linije 619-625 + Exception bullet) je compliance OK bez izuzetka u Story 2-10.

- **SM-D13:** `coric-category-card` BEM komponenta je **site-wide reusable** — Story 2-12 (HZM Radne Mašine + Tulip MIX) i Story 2-11 (Subcategory Listing) REUSE-uju 1:1. Responzivni CSS Grid `repeat(auto-fit, minmax(280px, 1fr))` automatski handluje 3 vs 4 vs N kartica bez izmena CSS-a (HZM ima 4 potkategorije; Story 2-11 može imati 2-5 sub-podkategorija na različitim nivoima hijerarhije). Lokovan je u dedicated `static/css/components/category-showcase.css` fajlu (NIJE u brand-listing.css ili negde drugde) jer je general-purpose pattern.

- **SM-D14:** Category seed migracija NE popunjava `name_hu` / `name_en` polja (modeltranslation auto-popunjava `name_sr` kroz fallback iz `name`). v1 prikazuje srpski naziv na svim locale-ima. Story 8-5 (Category CRUD admin) ili manual data migracija u kasnijim Story-jama može popuniti prevode. Razlog: prevodi naziva kategorija su sadržajna decision-a (treba ih admin/editor reviews); inicijalna data migracija ne treba da hardcoduje hu/en prevode bez review-a.

- **SM-D15 (IMP-3 ACK):** Silent partial degradation u slučaju da admin mis-edituje seeded mehanizacija kategorije (postavi `is_for ≠ 'mehanizacija'` ILI rename slug-a izvan whitelist `_PRIKLJUCNA_CATEGORY_SLUGS`) je **ACCEPTED v1 behavior**. Posledica: strana renderuje < 3 kartice (npr. 2 ili 1) bez error-a; ako su sve 3 mis-edited, strana renderuje `{% empty %}` poruku „Kategorije priključne mehanizacije su u pripremi.". Vlasnik guard-a je **Story 8-5 (Category CRUD admin)** koji treba da implementira admin-level validation (npr. `clean()` method na CategoryForm koji upozorava admin-a ako menja `is_for` polja seeded kategorija). Story 2-10 view tests pokrivaju (a) happy path sa 3 kartice, (b) full empty `{% empty %}` state, (c) partial-degradation guard (Subtask 9.3 AC5 5. test — verifikuje samo whitelisted slug-ovi renderuju). Partial-degradation gracefully renderuje fewer cards bez crash-a.

- **SM-D16 (IMP-4 ACK):** Story 2-10 NE implementira UX-DR-22 fallback marker („ⓘ tooltip 'Sadržaj na srpskom — još nije preveden'") na nepreveden Category.name na /hu/ /en/ stranama. Razlog: marker je site-wide UI/UX feature koji vlasništvo ima **Story 6-5 (i18n fallback marker tooltip)**. Story 2-10 v1 prikazuje sr Category.name na svim locale-ima bez markera; lokali su tehnički podržani (LocaleMiddleware aktivan iz Story 1-4), ali HU/EN msgstr za Category.name su prazni (admin populacija planirana u Story 8-5). Vidi AC8 i18n § fallback marker bullet za explicit out-of-scope statement.

### Dependencies note (KRITIČNO za Dev)

Story 2-10 STROGO zavisi od ovih prethodnih story-ja (sve `done` per sprint-status.yaml):
- **Story 2-1:** Brand, Category modeli + CategoryScope.MEHANIZACIJA TextChoices — Story 2-10 query-uje `Brand.objects.get(slug='jeegee')` i `Category.objects.filter(is_for='mehanizacija', slug__in=[...])`
- **Story 2-3:** {% responsive_picture %} template tag — N/A za Story 2-10 (hero koristi direct img kroz hero_overlay_card partial), ali safe load-uje `media_tags` u template za Story 9-10 future use
- **Story 2-6:** BrandDetailView CBV pattern (REUSE get_template_names + get_object + get_context_data idiomatic pattern); brand_coming_soon.html template (REUSE 1:1); cross-boundary brands → products import precedent — Story 2-10 NE koristi izuzetak

Sve prethodne story-je su `done` u sprint-status.yaml (verifikovano 2026-05-30); Story 2-10 je spremna za RED phase (TEA) → GREEN phase (Dev).

### Open questions / warnings za Validation (Step 2)

1. **Lighthouse Performance score target ≥ 80** (viši nego Story 2-6 ≥ 75) — Story 2-10 nema HTMX, nema JS, nema range slidera, nema slika osim brand logo-a; strana je vrlo light pa Performance score treba biti viši. Ako Dev manualni smoke pokaže < 80, Story 9-10 polish je escalation path (WebP/AVIF za brand logo).
2. **Bootstrap Icons wiring deferred** — Category icon polje je seed-ovano kao empty string (per SM-D2); conditional render u _category_showcase.html `{% if category.icon %}` će uvek evaluuirati False u v1. Story 9-10 polish wire-uje Bootstrap Icons font i admin može popuniti `category.icon` polje.
3. **CTA URL placeholder** — Klik na „POGLEDAJ KATEGORIJU" CTA produkuje 404 u v1 (Story 2-11 immediately rešava). Manuelni smoke check (AC9) eksplicitno potvrdi da to je expected behavior; korisnik bez Story 2-11 deployed-a videće 404. Story 2-11 SM ima load-bearing TODO za refaktor direct interpolation → `{% url %}` tag.
4. **Multi-locale Category.name** — v1 prikazuje srpski naziv kategorija na hu/en stranama. Pragmatic per Story 2-6 open question; Story 8-5 + Story 6-5 rešavaju.
5. **Story 2-6 hero `variant="blue"` dormant bug** — Story 2-6 _hero_section.html koristi `variant="blue"` koji ne postoji u CSS-u; bug je dormant jer nijedan tractor brend nema brand_color="#00A4E9" u DB. Story 2-10 koristi tačan `variant="jeegee"`. Fix Story 2-6 je out-of-scope za 2-10; Story 9-10 polish ili zaseban tech-debt commit.

## Completion Notes

_(Dev fills this section after GREEN phase implementation.)_

## SM Decisions Log

**Final summary:**
- **16 SM decisions** documented (SM-D1 through SM-D16; +SM-D15 + SM-D16 dodate u iter 1/5 validation fix)
- **Key architectural choices:**
  - SM-D1: NO HTMX (static landing strana)
  - SM-D2: Data migracija za seed Jeegee + 3 Category (idempotent get_or_create + reverse callable)
  - SM-D3: Statički URL `/mehanizacija/prikljucna/` (no brand_slug kwarg)
  - SM-D4: Dedicated `_jeegee_hero.html` partial (NE reuse Story 2-6 `_hero_section.html` — clean separation, hardcoded variant)
  - SM-D5: Direct string interpolation za CTA href (NE `{% url %}` — Story 2-11 dependency placeholder); bare `{{ LANGUAGE_CODE }}` (NE `{{ request.LANGUAGE_CODE }}` — codebase konvencija, IMP-5 fix)
  - SM-D6: Direct `<a>` markup za category CTA (NIJE pill_button partial — aria-label blocktranslate requirement)
  - SM-D7: Http404 sa kustomizovanom porukom u get_object() (defensive guard; IMP-1 lock — explicit raise sa `from django.http import Http404`, NE `get_object_or_404` shortcut)
  - SM-D8: `aria-label` na BOTH outer wrapper-u I hero section (umesto `aria-labelledby` — Story 1-7 partial preserve; CRITICAL-1 fix lock — outer wrapper NEMA dangling aria reference)
  - SM-D9: TAČNO `variant="jeegee"` (NE "blue" — Story 2-6 dormant bug napomena)
  - SM-D10: Hero bullets empty u v1
  - SM-D11: sprint-status.yaml NE counted u deliverable EDIT count
  - SM-D12: NEMA cross-boundary brands → products import (Story 2-6 SM-D16 exception N/A)
  - SM-D13: `coric-category-card` BEM site-wide reusable (foundation za Story 2-12 + 2-11)
  - SM-D14: Category seed migracija NE popunjava hu/en prevode (Story 8-5 + Story 6-5 follow-up)
  - SM-D15 (IMP-3 ACK): Silent partial degradation prihvaćeno v1 — Story 8-5 owns admin guard; Story 2-10 view tests pokrivaju happy path + empty + partial-degradation
  - SM-D16 (IMP-4 ACK): UX-DR-22 fallback marker explicit out-of-scope za Story 2-10 — deferred to Story 6-5; sr Category.name prikazuje se na svim locale-ima u v1
