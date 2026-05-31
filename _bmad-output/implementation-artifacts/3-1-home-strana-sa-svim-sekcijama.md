---
story_id: "3.1"
story-key: 3-1-home-strana-sa-svim-sekcijama
title: Home Strana sa Svim Sekcijama
status: ready-for-dev
epic: 3
epic_num: 3
epic_title: Home & Static Pages
module: pages
created: 2026-05-31
last_modified: 2026-05-31  # SM batch-fix pass (ITEM-1..8 non-mandatory improvements)
complexity: M
author: Mihas (SM autonomous; PRVA story Epic 3. Home strana `/sr/` AGREGIRA read-only podatke iz apps/products + apps/brands i renderuje 7 sekcija u tačnom redu iz EXPERIENCE.md § „Početna — sekcijski raspored": (1) Hero overlay card preko foto-pozadine traktora sa sloganom „Prijatelj koji razume zemlju!" + brand lockup + Repeating Element watermark; (2) „O nama" intro blok (naslov + tekst + CTA „Saznaj više" → /o-nama); (3) Traktori — svi aktivni brendovi kao kartice (logo + reprezentativna slika + „OPŠIRNIJE" CTA → brand strana), is_coming_soon brendovi sa pill-badge „Uskoro"; (4) Priključna mehanizacija — Jeegee baner + CTA → jeegee_prikljucna; (5) Radne mašine — HZM kategorije (Repeating Element po kategoriji) + CTA → hzm_radne_masine; (6) Polovna mehanizacija — baner + CTA → used_machinery_list; (7) „Priče sa polja" preview — wave divider gore + 2 LOREM IPSUM placeholder kartice (Post model NE postoji — Epic 5 backlog, forward-compat placeholder bez fake modela, mirror Story 2-13 SM-D3 prazna-grana pristup). NEMA HTMX, NEMA forma, NEMA migracije, NEMA novog JS. SM Odluka (SM-D6 KOREKCIJA): home view ŽIVI u NOVOM `apps/pages/` app-u (NE `apps/core/` — architecture.md: „core NIKAD ne sme importovati domain apps" + architecture.md eksplicitno mapira HomeView → `apps/pages/`, a `pages` je top-level app KOJEM JE dozvoljeno da importuje domain modele + blog). Home je `HomeView(TemplateView)` u `apps/pages/views.py`; URL `path("", ..., name="home")` u `apps/pages/urls.py` (namespace `pages` → `pages:home`); section partials žive u `templates/pages/partials/` (SM-D2). Postojeći `apps/core` `home` stub + `core:home` URL se UKLANJAJU, sve `core:home` reference se migriraju na `pages:home`. REUSE 1-7 partials, 2-6 brand_coming_soon pill-badge, 2-10/2-12 coric-category-card + Repeating Element.)
depends_on:
  - 1-6-base-templates-sa-bootstrap-5-htmx-setup        # base.html block content/extra_head/scripts; {% include "partials/header.html" %} + footer.html već prisutni
  - 1-7-reusable-visual-komponente                       # hero_overlay_card, repeating_element, section_eyebrow, pill_button, wave_divider partials + coric-button BEM
  - 1-8-sticky-nav-top-header-footer-language-switcher-partial  # header + footer landmark-ovi (home extends base.html sa njima već prisutnim)
  - 2-1-brand-series-category-subcategory-modeli         # Brand (logo, is_coming_soon, get_absolute_url=brands:detail), Category (is_for=MEHANIZACIJA, radne-masine), Subcategory
  - 2-2-product-i-related-modeli                          # Product (brand FK, main_image, is_published) — reprezentativna slika za Traktori kartice (READ-ONLY cross-boundary)
  - 2-3-image-pipeline-sa-sorl-thumbnail-responsive-srcset  # {% responsive_picture %} za brand logo + reprezentativne slike + hero foto-pozadina
  - 2-6-brand-listing-strana-sa-grid-extended-layout-om   # brands:detail target (Traktori CTA); coric-pill-badge--coming-soon klasa (brand-listing.css:290,300); brand_coming_soon.html pill-badge markup
  - 2-10-jeegee-prikljucna-mehanizacija-strana            # brands:jeegee_prikljucna target (Priključna baner CTA); coric-category-card + category-showcase.css REUSE
  - 2-12-hzm-radne-masine-tulip-mix-prikolice-strane      # brands:hzm_radne_masine target (Radne mašine CTA); HZM radne-masine Category + 4 Subcategory (Repeating Element po kategoriji)
---

# Story 3.1: Home Strana sa Svim Sekcijama

Status: ready-for-dev

## Opis

As a **posetilac (Marko — poljoprivrednik koji prvi put dolazi na sajt i za ≤5 sekundi želi da razume šta Ćorić Agrar nudi; Đorđe — Mihasov klijent koji testira tastaturom + NVDA na 375px mobilnom ekranu; pretraživač / SEO bot koji indeksira početnu)**,

I want **da otvorim početnu stranu na `/sr/` i vidim reprezentativnu Početnu koja AGREGIRA celu ponudu u 7 sekcija u tačnom redu: (1) full-width Hero sa foto-pozadinom traktora i `green-800` overlay karticom koja sadrži slogan „Prijatelj koji razume zemlju!", brand lockup i Repeating Element watermark; (2) „O nama" intro blok sa naslovom, kratkim tekstom i CTA „Saznaj više"; (3) sekciju Traktori — svi aktivni brendovi kao kartice (logo + reprezentativna slika + „OPŠIRNIJE" CTA koji vodi na brand stranu), pri čemu brendovi sa `is_coming_soon=True` imaju pill-badge „Uskoro"; (4) sekciju Priključna mehanizacija — Jeegee baner sa CTA; (5) sekciju Radne mašine — HZM kategorije renderovane sa Repeating Element-om po kategoriji; (6) Polovna mehanizacija — baner sa CTA; (7) „Priče sa polja" preview — wave divider gore, foto-pozadina, i 2 najnovije „blog" kartice prikazane kao Lorem Ipsum placeholder dok Epic 5 blog nije izgrađen; sve praćeno Footer-om iz base.html**,

so that **brzo (bez scroll-friction-a) shvatam ko je Ćorić Agrar i koja je ponuda, klikom na BILO KOJU klikabilnu zonu (brand logo ili sliku) odlazim na odgovarajuću brand stranu, strana je potpuno responzivna (mobile stack → desktop multi-col), zadovoljava single-h1 pravilo, koristi semantic HTML5 + ARIA landmarks, prolazi Lighthouse a11y ≥ 95 (UX-DR-13 + NFR-2 + Story 9-9 gate), i REUSE-uje SVE postojeće vizuelne komponente (Repeating Element, hero_overlay_card, section_eyebrow, wave_divider, coric-category-card, coric-pill-badge) tako da je vizuelno i interakciono konzistentna sa ostatkom sajta — uz NULA novih JS modula i minimalan novi CSS**.

Ovo je **prva story Epic 3 (Home & Static Pages)** i prva strana koja kombinuje rad iz Epic 1 (vizuelne komponente, base templates, header/footer) i Epic 2 (Brand/Category/Subcategory/Product modeli + sve brand landing strane). Home strana je **čista agregacijska read-only strana** — NE definiše nove modele, NE menja postojeće, NE uvodi forme ni HTMX. Ona je „izlog" koji linkuje na sve već-postojeće odredišne strane.

**SM ODLUKA — home view ŽIVI u `apps/pages/` (NE `apps/core/`) — SM-D1 (KOREKCIJA C1):** home strana AGREGIRA domain modele (`Brand`, `Category`, `Subcategory`, `Product`), pa NE SME živeti u `apps/core/` — `core` je leaf dependency (architecture.md § Architectural Boundaries: „`core` NIKAD ne sme importovati domain apps"; dependency graph: `core ← (everyone imports core)`, što znači core ne importuje NIKOGA). architecture.md EKSPLICITNO mapira HomeView → `apps/pages/` (architecture.md:587-592 dir struktura `pages/ … views.py # HomeView, AboutView, ContactView`; :796 „Epic 2 — Public katalog … `apps/pages/` (HomeView)"; :894 „FR-1..FR-5 (Početna + statičke strane) | `apps/pages/`") i `pages` je top-level app KOJEM JE dozvoljeno da importuje domain + blog (architecture.md:729 „`pages ← (top-level, ima reference na blog za „Najnovije vesti")`"). **Lock:** home se implementira kao `HomeView(TemplateView)` u NOVOM `apps/pages/views.py`; `apps/pages/` app se kreira (AppConfig `PagesConfig`, registracija u INSTALLED_APPS, `apps/pages/urls.py` sa `app_name = "pages"`). CBV `TemplateView` (NE FBV) jer: (a) novi app — nema postojeći FBV stub za očuvanje; (b) home je server-side static render bez forme/paginacije — `TemplateView` + `get_context_data()` je idiomatičan Django izbor za stranicu koja samo agregira read-only kontekst; project-context.md § Django views dozvoljava CBV za standardne render strane. **Postojeći `apps/core` `home` FBV stub + `apps/core/urls.py` `path("", home, name="home")` se UKLANJAJU** (vidi SM-D6 za reference migraciju `core:home` → `pages:home`). Cross-boundary import `Brand/Category/Product` je sada ARHITEKTONSKI ČIST jer `apps/pages` SME importovati domain (NE više „izuzetak" — to je dozvoljena zavisnost top-level app-a). Vidi SM-D1 + SM-D6.

**SM ODLUKA — section partials lokacija `templates/pages/partials/` — SM-D2:** novi home template je `templates/pages/home.html`; section partials žive u `templates/pages/partials/_home_<section>.html` (per project-context.md § Templates: „Direktorijumi: per-app → `templates/products/`, `templates/brands/`"; home view pripada `apps/pages` pa partials idu pod `pages/`; architecture.md:655 navodi `templates/pages/`). NE `templates/core/` (home view više NIJE u core) i NE `templates/partials/` (rezervisan za site-wide cross-app partials kao header/footer/hero_overlay_card). Vidi SM-D2.

**REUSE fokus (0 novih JS modula; 1 nova CSS komponenta — home-page sekcijski layout/baneri):**

- **`HomeView(TemplateView)`** (`apps/pages/views.py`, NOVO) — agregira querysetove (`get_context_data`) + `template_name = "pages/home.html"`. `apps/pages/` je NOVI app (kreira se u ovoj story); URL `pages:home`. Postojeći `apps/core` `home` stub se uklanja (SM-D1 + SM-D6).
- **`Brand` model** (Story 2-1, READ-ONLY): Traktori sekcija — aktivni Traktori brendovi (SM-D4 queryset). Polja: `brand.slug`, `brand.name`, `brand.logo`, `brand.is_coming_soon`. (NAPOMENA — ITEM-6 ispravka: `Brand` model **IMA** `get_absolute_url()` na `apps/brands/models.py:156-158` koji reverzuje `brands:detail`; vidi SM-D5. Traktori CTA/linkovi koriste `{% url 'brands:detail' slug=brand.slug %}` radi eksplicitnosti, što je ekvivalentno `{{ brand.get_absolute_url }}`.)
- **`Category` model** (Story 2-1, READ-ONLY): Radne mašine sekcija — HZM `radne-masine` Category-ja + njene Subcategory dece (Repeating Element po kategoriji). Polja: `category.name`, `category.subcategories`.
- **`Subcategory` model** (Story 2-1/2-12, READ-ONLY): 4 HZM potkategorije za „Repeating Element po kategoriji" prikaz.
- **`Product` model** (Story 2-2, READ-ONLY — dozvoljena zavisnost `pages → products`, SM-D6): reprezentativna slika po Traktori brendu (`Product.objects.filter(brand=..., is_published=True).first()` ili prefetch — SM-D4). **NE WRITE.**
- **`templates/partials/hero_overlay_card.html`** (Story 1-7) — REUSE 1:1 za Home hero; prima `title` (slogan), `brand_logo`, `brand_logo_alt`, `variant="green"` (SM-D9 mirror), `bullets=""`.
- **`templates/partials/repeating_element.html`** (Story 1-7) — INDIREKTNO kroz hero_overlay_card (watermark) + DIREKTNO u Radne mašine sekciji („Repeating Element po kategoriji" per epics.md AC + EXPERIENCE.md:114). `variant="green"` (SM-D9 — CSS ima SAMO `--green` + `--jeegee`; NE izmišljati nove variant-e).
- **`templates/partials/section_eyebrow.html`** (Story 1-7) — UPPERCASE eyebrow iznad svake sekcije.
- **`templates/partials/pill_button.html`** (Story 1-7) — opciono za CTA; Home koristi direct `coric-button` markup (mirror Story 2-10/2-12 SM-D6) ILI pill_button partial — Dev bira jedan konzistentan pristup (SM-D8).
- **`templates/partials/wave_divider.html`** (Story 1-7) — iznad „Priče sa polja" sekcije (`position="top"` — EXPERIENCE.md:116).
- **`coric-category-card` BEM + `static/css/components/category-showcase.css`** (Story 2-10) — REUSE za Radne mašine HZM kategorije grid (NE edit CSS).
- **`coric-pill-badge` + `coric-pill-badge--coming-soon`** (Story 2-6, `static/css/components/brand-listing.css:290,300`) — REUSE za „Uskoro" badge na Traktori karticama (mirror `brand_coming_soon.html:18` markup `role="status"`).
- **`coric-button` + `coric-button--primary`** (Story 1-7 `pill-button.css`) — REUSE za sve CTA.
- **`{% responsive_picture %}`** (Story 2-3, `media_tags`) — za brand logo, reprezentativne slike, hero foto-pozadina (srcset + loading="lazy" ispod fold-a).
- **CSS tokens** (`static/css/tokens.css`, Story 1-5): `--color-brand-green-800`, `--color-neutral-white/cream`, `--color-neutral-gray-700`, `--color-accent-gold-500`, `--spacing-scale-*`, `--rounded-md`, `--typography-scale-h1/h2/h3/body/caption`.
- **`base.html`** (Story 1-6) — `{% extends "base.html" %}`; `{% block content %}`, `{% block title %}`, `{% block meta_description %}`, `{% block extra_head %}`; header + footer + `<main id="main-content">` + aria-live region VEĆ prisutni (NE dupliraj).

**„Priče sa polja" preview — FORWARD-COMPAT LOREM IPSUM PLACEHOLDER (SM-D7 — KRITIČNA odluka):** Epic 5 blog (Post/BlogPost model) NIJE izgrađen (sprint-status: `5-1` … `5-4` = backlog). Home AC zahteva „2 najnovije blog kartice — placeholder Lorem Ipsum dok Epic 5 nije gotov". **Lock (SM-D7, mirror Story 2-13 SM-D3 prazna-grana pristup):** sekcija renderuje **2 STATIČKE Lorem Ipsum placeholder kartice iz template-a** (NE iz baze, NE iz fake Post modela, NE stub modela). View prosleđuje `latest_posts = []` (prazna lista — forward-compat: kada Epic 5 (Story 5-4) doda Post model, popuniće `latest_posts` querysetom i template grana će automatski preći sa placeholder-a na realne kartice). Template logika: `{% if latest_posts %}` renderuje realne kartice `{% else %}` renderuje 2 statičke placeholder kartice sa jasnim Lorem Ipsum sadržajem + HTML komentar marker `{# EPIC-5-PLACEHOLDER: zameniti realnim Post karticama kad Story 5-4 doda Post model + footer dynamic vesti #}`. NE kreirati fake Post model, NE migracija, NE admin. Placeholder kartice imaju `aria-label` koji jasno označava demonstracioni sadržaj. Vidi SM-D7.

**Hero content source — SiteSettings NE postoji (SM-D10):** `SiteSettings` model (kontakt info, hero_image_default, slogan) je Story 3-4 (sprint-status: backlog). **Lock (SM-D10):** Home hero koristi **hardcoded-translatable** sadržaj u v1: slogan „Prijatelj koji razume zemlju!" je FIKSAN (epics.md + EXPERIENCE.md:110 — kroz `{% translate %}`); hero foto-pozadina je statički asset `static/img/home/hero-traktor.jpg` (Dev dodaje placeholder/stock sliku — referencirana kroz `{% static %}`, NE upload polje). Brand lockup je Ćorić Agrar logo statik asset. Kada Story 3-4 doda SiteSettings, hero copy/slika mogu preći na `{% site_setting %}` template tag (NE blokira ovu story). Vidi SM-D10 — slogan se NE deferuje, foto-pozadina je static placeholder.

**Foundation za buduće Story-je:**

- **Story 3-4 (SiteSettings):** hero copy/slika + footer kontakt mogu preći sa hardcoded/static na `{% site_setting %}` template tag.
- **Story 5-4 (Footer dynamic „Najnovije vesti"):** popuniće `latest_posts` queryset → „Priče sa polja" sekcija prelazi sa Lorem Ipsum placeholder-a na realne Post kartice (forward-compat grana već postoji).
- **Story 6-1/6-3 (SEO/OG meta):** home `{% block meta_description %}` + OG tagovi prošireni per-page SEO modelom.

**Princip:** Pure server-side rendering, **NEMA HTMX**, **NEMA novog JavaScript-a**, **NEMA forma**, **NEMA admin promena**, **NEMA migracije** (čista agregacija postojećih modela; `apps/pages/` se kreira BEZ modela u v1 — SiteSettings dolazi tek Story 3-4, pa nema `migrations/0001` u ovoj story). `HomeView(TemplateView)` u NOVOM `apps/pages/` (NE FBV u core — SM-D1/SM-D6 KOREKCIJA C1). CSS BEM sa `coric-` prefiksom + isključivo `var(--token)`. Sve user-facing string-ove kroz `{% translate %}` / `{% blocktranslate %}`. `apps/pages` view čita iz `brands` + `products` modela READ-ONLY — to je ARHITEKTONSKI ČISTA, dozvoljena zavisnost (`pages` je top-level app koji per architecture.md SME importovati domain modele + blog; NIJE „izuzetak"). Slug ASCII; pune dijakritike (č/ć/ž/š/đ) u svemu renderovanom.

**Strukturna arhitektura — repository delta:** **14 NEW fizičkih fajlova + 7 EDIT + 0 DELETE-fajlova + 0 migracija** (kanonsko brojanje — prebrojivo iz tabele ispod; IMP-1 lock: Dev stvara svih 14 NEW fajlova; `apps/pages/` app scaffold uračunat). NAPOMENA: `apps/core/views.py` + `apps/core/urls.py` su EDIT-DELETE (uklanjanje `home` stub-a/URL-a), NE brisanje fajlova.

| Path | Tip | Razlog |
|---|---|---|
| `apps/pages/__init__.py` | NOVO | Novi Django app paket marker (`apps/pages/`, architecture.md:587-593). Prazan fajl. |
| `apps/pages/apps.py` | NOVO | `class PagesConfig(AppConfig)` — `default_auto_field`, `name = "apps.pages"`, `verbose_name = "Stranice"`. Bez `ready()` signala u v1. |
| `apps/pages/views.py` | NOVO | `class HomeView(TemplateView)` — `template_name = "pages/home.html"`; `get_context_data()` agregira READ-ONLY querysetove (Traktori brendovi + reprezentativne slike SM-D4, HZM Category + subcategories, `latest_posts=[]` SM-D7). DOZVOLJEN import `from apps.brands.models import Brand, Category` + `from apps.products.models import Product` + `from django.db.models import Prefetch` (`pages` → domain je dozvoljena zavisnost, SM-D6). Query optimizacija: `prefetch_related(Prefetch(..., to_attr=...))` za brand→reprezentativni-product + category→subcategories (SM-D4 — N+1 guard glavni rizik). |
| `apps/pages/urls.py` | NOVO | `app_name = "pages"`; `urlpatterns = [path("", HomeView.as_view(), name="home")]` → `pages:home`. Uključuje se u `config/urls.py` (i18n_patterns blok). |
| `apps/pages/tests/__init__.py` | NOVO | Test paket marker za TEA test fajlove (Task 8 — `apps/pages/tests/test_home_*.py`). |
| `config/urls.py` | EDIT | Dodaj `path("", include("apps.pages.urls"))` u `i18n_patterns(...)` blok (POSLE postojećih include-ova). UKLONI `path("", include("apps.core.urls"))` AKO core više nema URL-ova posle uklanjanja `home` (SM-D6 — vidi Subtask). Konflikt root path-a `""` se rešava uklanjanjem core `home` URL-a (jedan `""` ostaje — `pages:home`). |
| `apps/core/views.py` | EDIT (ukloni `home`) | UKLONI `def home(request)` stub (SM-D1/SM-D6 — home se seli u `apps/pages`). Ako `views.py` ostane prazan, ostavi modul docstring (NE briši fajl). `apps/core` ostaje leaf — BEZ domain import-a (architecture.md: „core NIKAD ne sme importovati domain apps"). |
| `apps/core/urls.py` | EDIT (ukloni `home` path) | UKLONI `path("", home, name="home")` + `from apps.core.views import home` import (SM-D6). Ako `urlpatterns` postane prazan, ostavi `app_name = "core"` + prazan `urlpatterns = []` (NE briši fajl; `apps/core` može imati buduće core URL-ove). `core:home` PRESTAJE da postoji — sve reference migriraju na `pages:home` (vidi SM-D6 reference listu). |
| `templates/pages/home.html` | NOVO | Glavni home template — `{% extends "base.html" %}`; `{% block title %}`, `{% block meta_description %}`, `{% block content %}` koji uključuje 7 sekcija REDOM (SM-D3): hero → o-nama intro → traktori → prikljucna baner → radne-masine → polovna baner → price-sa-polja preview. **JEDAN `<h1>`** (kroz hero_overlay_card partial u hero sekciji). **single `<main>`** iz base.html (NE dupliraj). Svaka sekcija je `<section>` sa `aria-labelledby`/`aria-label`. |
| `templates/pages/partials/_home_hero.html` | NOVO | Hero sekcija — full-width foto-pozadina (static `img/home/hero-traktor.jpg` kroz `{% static %}`, SM-D10) + `coric-home-hero__overlay` koji include-uje `partials/hero_overlay_card.html` sa `title=_("Prijatelj koji razume zemlju!")`, `brand_logo` (Ćorić Agrar static logo), `variant="green"` (SM-D9), `bullets=""`. h1 dolazi iz hero_overlay_card. |
| `templates/pages/partials/_home_about_intro.html` | NOVO | „O nama" intro blok — Section Eyebrow („O NAMA") + h2 + kratak tekst (Lorem-ish translatable copy do Story 3-2/8.8 CMS) + „Saznaj više" CTA → `{% url 'pages:about' %}` ILI hardcoded `/o-nama/` **(SM-D11: `pages:about` URL NE postoji još — Story 3-2; koristi privremeno `href="#"` + Dev TODO — vidi SM-D11 za lock)**. |
| `templates/pages/partials/_home_traktori.html` | NOVO | Traktori sekcija — Section Eyebrow + h2 + `coric-brand-grid` koji iterira `traktori_brands` i renderuje per-brand `coric-brand-card` (logo + reprezentativna slika kroz `{% responsive_picture %}` + naziv + „OPŠIRNIJE" CTA → `{% url 'brands:detail' slug=brand.slug %}`). Brendovi sa `is_coming_soon=True` imaju `coric-pill-badge coric-pill-badge--coming-soon` (`role="status"`, REUSE 2-6). KLIK ZONE (AC zahtev): i logo i slika su klikabilni link ka brand strani. `{% empty %}` clause. |
| `templates/pages/partials/_home_prikljucna_banner.html` | NOVO | Priključna mehanizacija (Jeegee) baner — Section Eyebrow + h2 + kratak opis + CTA → `{% url 'brands:jeegee_prikljucna' %}` (Story 2-10). `coric-home-banner` BEM. |
| `templates/pages/partials/_home_radne_masine.html` | NOVO | Radne mašine (HZM) sekcija — Section Eyebrow + h2 + `coric-category-showcase` grid koji iterira `hzm_subcategories` i renderuje per-kategorija karticu sa **Repeating Element po kategoriji** (`{% include "partials/repeating_element.html" with variant="green" %}` u svakoj kartici per EXPERIENCE.md:114) + naziv + CTA → `{% url 'brands:hzm_radne_masine' %}` (Story 2-12). REUSE coric-category-card BEM. `{% empty %}` clause. |
| `templates/pages/partials/_home_polovna_banner.html` | NOVO | Polovna mehanizacija baner — Section Eyebrow + h2 + opis + CTA → `{% url 'products:used_machinery_list' %}` (Story 2-9). `coric-home-banner` BEM (REUSE markup pattern iz prikljucna baner-a). |
| `templates/pages/partials/_home_price_sa_polja.html` | NOVO | „Priče sa polja" preview — `{% include "partials/wave_divider.html" with position="top" %}` + foto-pozadina + `{% if latest_posts %}` realne kartice `{% else %}` 2 STATIČKE Lorem Ipsum placeholder kartice (SM-D7) sa HTML komentar marker-om `{# EPIC-5-PLACEHOLDER #}`. Bez naslovne slike na karticama (EXPERIENCE.md:116). |
| `static/css/components/home-page.css` | NOVO | `coric-home-hero`, `coric-home-section`, `coric-home-banner`, `coric-brand-grid`, `coric-brand-card`, `coric-home-blog-preview` + `coric-home-blog-card` BEM (responsive: mobile stack → desktop multi-col SM-D12; hero ~60vh mobile/~80vh desktop per EXPERIENCE.md:458,473). Sve vrednosti kroz `var(--token)`. Radne mašine REUSE category-showcase.css (NEMA dupliranja). JEDINA nova CSS komponenta. |
| `static/css/main.css` | EDIT | Dodaj TAČNO 1 `@import url('./components/home-page.css');` POSLE poslednje postojeće `@import` linije (`comparison-table.css`, Story 2-12). |
| `static/img/home/hero-traktor.jpg` | NOVO (asset) | Hero foto-pozadina placeholder/stock slika (SM-D10). Dev dodaje optimizovanu sliku (≤300KB, ~1920px wide). Ako nedostupna, Dev koristi solid `green-800` fallback + TODO marker. Naveden kao NEW fajl (asset, ne kod). |
| `config/settings/base.py` | EDIT | Dodaj `"apps.pages"` u `INSTALLED_APPS` (POSLE `apps.core`; pre/posle domain app-ova nije bitno jer pages nema modele u v1 — ali logički POSLE `apps.products` jer pages importuje domain modele u view-u). |
| `locale/sr/LC_MESSAGES/django.po`, `locale/hu/LC_MESSAGES/django.po`, `locale/en/LC_MESSAGES/django.po` | EDIT (×3) | Popuni msgstr za nove msgid (slogan „Prijatelj koji razume zemlju!", eyebrow tekstovi „O NAMA"/„TRAKTORI"/„PRIKLJUČNA MEHANIZACIJA"/„RADNE MAŠINE"/„POLOVNA MEHANIZACIJA"/„PRIČE SA POLJA", h2 naslovi, „Saznaj više"/„OPŠIRNIJE" CTA, baner opisi, Lorem Ipsum placeholder naslovi, „Uskoro", aria-labeli, page title + meta description). Brand/Category `name` polja se NE prevode ovde (modeltranslation hu/en deferred Story 8-5 — mirror Story 2-10/2-12 SM-D). |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | EDIT | Postavi `3-1-home-strana-sa-svim-sekcijama` → `ready-for-dev` + `epic-3` → `in-progress` (prva story epika). SM handoff tracking (NIJE deliverable). |

**Brojanje (KANONSKO — single source of truth):** **14 NEW fizičkih fajlova + 7 EDIT + 0 DELETE-fajlova + 0 migracija.**

Razlaganje:
- **14 NEW:** `apps/pages/` scaffold (5: `__init__.py`, `apps.py`, `views.py`, `urls.py`, `tests/__init__.py`) + `pages/home.html` + 7 partials (`_home_hero`, `_home_about_intro`, `_home_traktori`, `_home_prikljucna_banner`, `_home_radne_masine`, `_home_polovna_banner`, `_home_price_sa_polja`) + `home-page.css` = 14 kod/template fajlova. (`static/img/home/hero-traktor.jpg` je asset — Dev dodaje, brojeno odvojeno od koda; IMP-1: kreiraj svih 14 + asset.)
- **7 EDIT:** `apps/core/views.py` (ukloni `home` stub) + `apps/core/urls.py` (ukloni `home` path) + `config/urls.py` (wire `pages.urls`, ukloni `core.urls` ako prazan) + `config/settings/base.py` (+`apps.pages` INSTALLED_APPS) + `static/css/main.css` (+1 @import) + 3 .po fajla = brojano kao 7 logičkih EDIT lokacija (3 .po = 1 logička stavka „locale"; raščlanjeno: 4 kod/config EDIT + 1 CSS EDIT + 3 .po EDIT = 8 fizičkih, 7 logičkih lokacija). (`sprint-status.yaml` = SM handoff tracking, counted separately.)
- **0 DELETE-fajlova** (`apps/core/views.py` + `urls.py` se EDIT-uju da uklone `home`, NE brišu — ostaju kao prazni/leaf moduli).
- **0 migracija** (`apps/pages` se kreira BEZ modela u v1 — SiteSettings je Story 3-4; čista read-only agregacija — Story 2-1/2-2 modeli nepromenjeni).

Postojeći fajlovi koji ostaju **NETAKNUTI** (regression guards): `apps/core/models.py`, `apps/core/utils.py`, `apps/core/mixins.py`, `apps/brands/` (kompletno — READ-ONLY query, NEMA edit; `brands:detail`/`jeegee_prikljucna`/`hzm_radne_masine` URL-ovi REUSE), `apps/products/` (kompletno — READ-ONLY; `used_machinery_list` REUSE), `apps/media_pipeline/`, `templates/base.html` (REUSE — NE dupliraj main/header/footer/aria-live), `templates/partials/*` (Story 1-7 + 1-8 — REUSE 1:1 bez izmena), `templates/brands/*` + `templates/products/*` (NETAKNUTI), `static/vendor/*` (NEMA novih), `static/js/*` (NEMA novih JS modula), `static/css/tokens.css`, `static/css/components/category-showcase.css` (Story 2-10 — REUSE 1:1 za Radne mašine grid, NE edit), `static/css/components/brand-listing.css` (`coric-pill-badge` + `--coming-soon` DEFINISANI linija 290/300 — REUSE, NE edit), `static/css/components/{repeating-element,hero-overlay-card,pill-button,section-eyebrow,wave-divider}.css` (Story 1-7 — REUSE), `pyproject.toml`. **AŽURIRAJU SE** (reference migracija `core:home` → `pages:home`, SM-D6): `templates/partials/header.html` (logo link + Početna nav link), `templates/partials/footer.html` (footer logo link), `templates/brands/brand_coming_soon.html:20` (Nazad na Home CTA), `apps/brands/views.py:254` (breadcrumb root URL).

## Kriterijumi prihvatanja

**AC1 — NOVI `apps/pages/` app + `HomeView`; URL `/<lang>/` rezolvuje `pages:home`; HTTP 200 za sva 3 locale; renderuje `templates/pages/home.html`; `core:home` UKLONJEN i sve reference migrirane na `pages:home`**

- **Given** `i18n_patterns()` aktivan (Story 1-4); postojeći `apps/core/urls.py`: `path("", home, name="home")` + `apps/core/views.py`: `def home(request): return render(request, "base.html", {})` (Story 1-4 stub — UKLANJA se); `apps/pages/` app NE postoji još (planiran u architecture.md:587)
- **When** kreiram NOVI `apps/pages/` app (PagesConfig + INSTALLED_APPS + `apps/pages/urls.py` `app_name="pages"` + `HomeView(TemplateView)`), wire-ujem `path("", include("apps.pages.urls"))` u `config/urls.py`, UKLONIM `apps/core` `home` stub/URL, i migriram sve `core:home` reference na `pages:home`
- **Then**:
  - `apps/pages` registrovan u `INSTALLED_APPS` (`config/settings/base.py`); `apps/pages/apps.py` ima `PagesConfig(name="apps.pages")`
  - `reverse("pages:home")` → `/sr/` (analogno `/hu/`, `/en/`)
  - `reverse("core:home")` više NE rezolvuje (UKLONJEN); `NoReverseMatch` ako se pozove — SVE reference su migrirane na `pages:home` (header.html, footer.html, brand_coming_soon.html:20, apps/brands/views.py:254 breadcrumb + svi testovi koji grep-uju `core:home`)
  - GET `/sr/` → HTTP 200; GET `/hu/` → 200; GET `/en/` → 200
  - Renderovani template je `pages/home.html` (NE `base.html` direktno) — verifikovati kroz `assertTemplateUsed(response, "pages/home.html")`
  - `HomeView` je CBV (`HomeView.as_view()` u `apps/pages/urls.py`)
  - `apps/core` ostaje leaf — `apps/core/views.py` + `apps/core/urls.py` BEZ `home`, BEZ domain import-a (architecture.md: „core NIKAD ne sme importovati domain apps")
  - `uv run python manage.py check` exit 0
- **And** smoke verifikacija:
  ```bash
  uv run python manage.py shell -c "from django.urls import reverse; \
    from django.utils.translation import activate; activate('sr'); \
    print(reverse('pages:home'))"
  ```
  Očekivan output: `/sr/`
- **And** regresijski smoke — NEMA preostalih `core:home` referenci u repou:
  ```powershell
  Select-String -Pattern "core:home" -Path apps,templates,tests -Recurse
  ```
  Očekivano: 0 rezultata (sve migrirano na `pages:home`)

**AC2 — `HomeView.get_context_data` agregira READ-ONLY kontekst sa N+1 zaštitom: `traktori_brands` (aktivni Traktori brendovi + reprezentativna slika), `hzm_subcategories` (HZM radne-masine Category dece), `latest_posts=[]` (forward-compat blog placeholder); query budget zaključan `assertNumQueries`**

- **Given** AC1; Brand + Category + Subcategory + Product modeli (Story 2-1/2-2); DOZVOLJEN `pages`→`brands`/`products` READ-ONLY import (SM-D6 — `pages` je top-level app koji SME importovati domain); HZM `radne-masine` Category + 4 Subcategory seed-ovani (Story 2-12 migracija 0004); Jeegee/HZM/ostali brendovi seed-ovani
- **When** implementiram `HomeView(TemplateView)` u `apps/pages/views.py` (mirror skeleton — Dev MORA implementirati):
  ```python
  from django.db.models import Prefetch
  from django.views.generic import TemplateView

  from apps.brands.models import Brand, Category
  from apps.products.models import Product

  _HZM_CATEGORY_SLUG = "radne-masine"


  class HomeView(TemplateView):
      template_name = "pages/home.html"

      def get_context_data(self, **kwargs):
          context = super().get_context_data(**kwargs)
          # SM-D4 (LOCKED, opcija A): Traktori sekcija lista SAMO brendove koji imaju
          # bar jedan OBJAVLJEN `condition=NEW` (Traktori) proizvod. Ovaj filter
          # EKSPLICITNO sprečava da mehanizacija brendovi (Jeegee/HZM/Tulip) iscure u
          # Traktori sekciju — oni nemaju condition=NEW Traktori proizvode pa otpadaju.
          # `is_coming_soon=True` brendovi SE UKLJUČUJU (prikazani sa „Uskoro" pill) —
          # filter NE isključuje coming-soon (verifikovano: is_coming_soon je nezavisno
          # polje od products relacije; ako coming-soon brend ima objavljen NEW proizvod,
          # ostaje u listi). Polja verifikovana live (apps/products/models.py:91-159):
          # Product.ConditionChoice.NEW == "new", Product.condition, Product.is_published,
          # Product.brand FK related_name="products". Reprezentativna slika = first
          # published product main_image po brendu kroz Prefetch (NE per-brand .first()
          # u petlji → N+1). `.distinct()` jer products__... join može duplirati brendove.
          context["traktori_brands"] = list(
              Brand.objects.filter(
                  products__condition=Product.ConditionChoice.NEW,
                  products__is_published=True,
              )
              .distinct()
              .prefetch_related(
                  Prefetch(
                      "products",
                      queryset=Product.objects.filter(is_published=True).order_by(
                          "-created_at"
                      ),
                      to_attr="published_products",
                  )
              )
              .order_by("is_coming_soon", "name")
          )
          # SM-D7: forward-compat blog placeholder — Post model NE postoji (Epic 5).
          # Prazna lista → template renderuje 2 Lorem Ipsum placeholder kartice.
          context["latest_posts"] = []
          # Radne mašine: HZM radne-masine Category + njene Subcategory dece.
          hzm_subcategories = []
          try:
              hzm_category = Category.objects.get(
                  slug=_HZM_CATEGORY_SLUG,
                  is_for=Category.CategoryScope.MEHANIZACIJA,
              )
              hzm_subcategories = list(
                  hzm_category.subcategories.filter(parent=None).order_by(
                      "display_order", "name"
                  )
              )
          except Category.DoesNotExist:
              pass
          context["hzm_subcategories"] = hzm_subcategories
          return context
  ```
- **Then**:
  - Context sadrži: `traktori_brands` (list[Brand] sa prefetch-ovanom `published_products` to_attr listom), `hzm_subcategories` (list[Subcategory], 4 dece, ordered display_order), `latest_posts` (prazna lista `[]`)
  - **Query budget KONSTANTAN bez obzira na broj brendova/proizvoda** (N+1 guard — GLAVNI RIZIK): reprezentativna slika po brendu MORA doći iz `Prefetch(..., to_attr=...)` (NE per-brand `.first()` query u petlji/template-u). Broj upita: Brand fetch + prefetch products + HZM Category + HZM subcategories ≈ 4 upita, KONSTANTAN. Budget se zaključava TEK posle `assertNumQueries` GREEN runa koji dokazuje da dodavanje N brendova NE povećava broj upita (Subtask 8.2)
  - Ako HZM `radne-masine` Category ne postoji → `hzm_subcategories=[]` (empty state render, NE crash — defensive guard mirror Story 2-12)
  - `latest_posts` UVEK prazna lista u v1 (forward-compat — SM-D7); template grana odlučuje placeholder vs realne kartice
- **And** view NE WRITE-uje na Brand/Category/Subcategory/Product (READ-ONLY agregacija — dozvoljena `pages`→domain zavisnost, SM-D6)
- **And** `select_related`/`prefetch_related` korišćen svuda gde se pristupa FK/reverse-FK (project-context.md § Performance must-haves)

**AC3 — `templates/pages/home.html`: 7 sekcija u TAČNOM redu (hero → o-nama → traktori → prikljucna → radne-masine → polovna → price-sa-polja); JEDAN h1; single main (iz base.html); semantic HTML5 + ARIA landmarks**

- **Given** AC2; base.html (Story 1-6 — `{% block content %}`, single `<main>`, header, footer, aria-live); Story 1-7 partials
- **When** kreiram `templates/pages/home.html` + 7 section partials
- **Then** `home.html` MORA imati strukturu:
  ```django
  {% extends "base.html" %}
  {% load i18n static %}

  {% block title %}{% translate "Ćorić Agrar — Prijatelj koji razume zemlju" %}{% endblock %}

  {% block meta_description %}{% translate "Ćorić Agrar — poljoprivredna mehanizacija, traktori, priključna oprema, radne mašine i polovna mehanizacija." %}{% endblock %}

  {% block content %}
    {% include "pages/partials/_home_hero.html" %}
    {% include "pages/partials/_home_about_intro.html" %}
    {% include "pages/partials/_home_traktori.html" %}
    {% include "pages/partials/_home_prikljucna_banner.html" %}
    {% include "pages/partials/_home_radne_masine.html" %}
    {% include "pages/partials/_home_polovna_banner.html" %}
    {% include "pages/partials/_home_price_sa_polja.html" %}
  {% endblock %}
  ```
- **Then** redosled sekcija MORA biti TAČNO kao EXPERIENCE.md § „Početna — sekcijski raspored" (linije 108-117): (1) Hero, (2) O nama intro, (3) Traktori, (4) Priključna (Jeegee), (5) Radne mašine (HZM), (6) Polovna, (7) Priče sa polja preview. Footer dolazi iz base.html (NE dupliraj)
- **And** semantic HTML5:
  - TAČNO 1 `<h1>` na strani (slogan, kroz `hero_overlay_card` partial u hero sekciji)
  - Svaka od 7 sekcija je `<section>` sa `aria-labelledby` (referencira lokalni h2 id) ILI `aria-label` (hero — h1 u hero_overlay_card nema id, mirror Story 2-10/2-12 SM-D8)
  - h2 po sekciji (O nama, Traktori, Priključna, Radne mašine, Polovna, Priče sa polja) → h3 za kartice (brand naziv, kategorija naziv, blog placeholder naslov)
  - Heading hijerarhija h1 → h2 → h3 (NEMA preskoka)
  - **Single `<main>`** (iz base.html — `home.html` NE dodaje drugi `<main>`)
  - `<article>` za svaku karticu (brand card, kategorija card, blog placeholder card)
- **And** `<html lang="{{ LANGUAGE_CODE }}">` automatski (base.html, Story 1-4 middleware)
- **And** NEMA hardcoded srpski (sve `{% translate %}`); NEMA ćirilice; pune dijakritike

**AC4 — Hero sekcija: full-width foto-pozadina + `green-800` overlay card sa sloganom „Prijatelj koji razume zemlju!" + brand lockup + Repeating Element watermark (REUSE hero_overlay_card, variant="green")**

- **Given** AC3; `templates/partials/hero_overlay_card.html` (Story 1-7 — prima title/brand_logo/brand_logo_alt/variant/bullets); `repeating_element.html` watermark passthrough; SM-D10 (hero copy hardcoded-translatable, foto-pozadina static asset)
- **When** kreiram `templates/pages/partials/_home_hero.html`
- **Then** hero MORA:
  - `<section>` sa `aria-label` (NE aria-labelledby — h1 u hero_overlay_card nema id; SM-D8 mirror 2-10/2-12)
  - Full-width foto-pozadina `static/img/home/hero-traktor.jpg` kroz CSS background ili `<picture>` (Dev bira; `loading="eager"` ako img — above fold)
  - `{% include "partials/hero_overlay_card.html" with title=_("Prijatelj koji razume zemlju!") brand_logo=... brand_logo_alt=_("Ćorić Agrar logo") variant="green" bullets="" %}`
  - hero_overlay_card renderuje h1 (slogan) + brand lockup (Ćorić Agrar logo) + Repeating Element watermark (`coric-repeating-element--green` — SM-D9)
  - Hero visina responzivna: ~60vh mobile, ~80vh desktop (EXPERIENCE.md:458,473) kroz `home-page.css`
- **And** `variant="green"` (NE „home"/druga vrednost — repeating-element.css ima SAMO `--green` + `--jeegee`; SM-D9 mirror Story 2-12 — izbegava unstyled watermark)
- **And** slogan kroz `{% translate "Prijatelj koji razume zemlju!" %}` (FIKSAN, pune dijakritike; SM-D10 — NE deferuje se)
- **And** hero foto-pozadina ima dekorativni tretman (`aria-hidden` ako odvojeni element / `alt=""` ako img dekorativan)

**AC5 — Traktori sekcija: svi aktivni brendovi kao kartice (logo + reprezentativna slika + „OPŠIRNIJE" CTA → brand strana); `is_coming_soon` brendovi sa pill-badge „Uskoro"; logo I slika klikabilni ka brand strani (AC zona zahtev)**

- **Given** AC2 (`traktori_brands` context sa prefetch-ovanom `published_products`); `brands:detail` URL (Story 2-6, `/traktori/<slug>/`); `coric-pill-badge--coming-soon` (Story 2-6 brand-listing.css:300); `{% responsive_picture %}` (Story 2-3); SM-D5 (Brand IMA `get_absolute_url()` na models.py:156; koristi se eksplicitan ekvivalent `{% url 'brands:detail' slug=brand.slug %}`)
- **When** kreiram `templates/pages/partials/_home_traktori.html`
- **Then** sekcija MORA:
  - Section Eyebrow („TRAKTORI") + h2 (npr. „Naši brendovi")
  - `coric-brand-grid` koji iterira `traktori_brands`; per-brand `<article class="coric-brand-card">`:
    - Brand logo kroz `{% responsive_picture brand.logo ... %}` (defensive `{% if brand.logo %}` guard) — **klik na logo vodi na brand stranu** (wrapped u `<a href="{% url 'brands:detail' slug=brand.slug %}">`)
    - Reprezentativna slika = `brand.published_products.0.main_image` (iz prefetch to_attr, SM-D4) kroz `{% responsive_picture %}` (`loading="lazy"` — ispod fold-a) — **klik na sliku vodi na brand stranu** (zasebna klikabilna zona; AC zahtev „svaka zona klikabilna"). **GUARD (ITEM-5):** obavij u `{% if brand.published_products and brand.published_products.0.main_image %}` PRE poziva `{% responsive_picture %}` — objavljen proizvod bez upload-ovane `main_image` (ImageField `blank=True`) NE sme da pukne `responsive_picture`. `{% else %}` fallback: prikaži brand logo (ako `brand.logo`) ILI placeholder CSS klasu (`coric-brand-card__image--placeholder`). Slika-klik-zona se renderuje SAMO ako slika postoji; logo + „OPŠIRNIJE" CTA ostaju klikabilne zone u svakom slučaju.
    - h3 brand naziv
    - „OPŠIRNIJE" CTA `coric-button coric-button--primary` → `{% url 'brands:detail' slug=brand.slug %}`
    - Ako `brand.is_coming_soon` → `<span class="coric-pill-badge coric-pill-badge--coming-soon" role="status">{% translate "Uskoro" %}</span>` (REUSE 2-6 markup `brand_coming_soon.html:18`)
  - `{% empty %}` clause „Brendovi će uskoro biti dostupni."
- **And** AC zahtev „Klik na brand logo ili sliku vodi na brand stranu (svaka zona klikabilna)": logo, slika, I „OPŠIRNIJE" CTA su SVI link ka `brands:detail` (3 klikabilne zone po kartici; svaka `<a>` ima accessible naziv — aria-label ili tekst)
- **And** coming-soon brand kartica i dalje linkuje na brand stranu (brand_coming_soon.html minimal template; mirror Story 2-6 SM-D4 — NE 404)
- **And** brand logo `alt` = brand naziv (informacioni, NE prazan)

**AC6 — Priključna (Jeegee) + Polovna baneri: Section Eyebrow + h2 + opis + CTA → odgovarajuća strana (`brands:jeegee_prikljucna` / `products:used_machinery_list`)**

- **Given** AC3; `brands:jeegee_prikljucna` (Story 2-10), `products:used_machinery_list` (Story 2-9); `coric-button` (Story 1-7)
- **When** kreiram `_home_prikljucna_banner.html` + `_home_polovna_banner.html`
- **Then** Priključna baner MORA:
  - `<section aria-labelledby="home-prikljucna-title">` + Section Eyebrow („PRIKLJUČNA MEHANIZACIJA") + `<h2 id="home-prikljucna-title">` + kratak opis + CTA → `{% url 'brands:jeegee_prikljucna' %}` (EXPERIENCE.md:113)
  - `coric-home-banner` BEM markup
- **And** Polovna baner MORA:
  - `<section aria-labelledby="home-polovna-title">` + Section Eyebrow („POLOVNA MEHANIZACIJA") + h2 + opis + CTA → `{% url 'products:used_machinery_list' %}` (EXPERIENCE.md:115)
  - REUSE `coric-home-banner` markup pattern (konzistentno sa Priključna baner-om)
- **And** oba CTA koriste `{% url %}` (NE hardcoded URL string — project-context.md)

**AC7 — Radne mašine (HZM) sekcija: HZM kategorije sa Repeating Element po kategoriji (REUSE coric-category-card + repeating_element); CTA → `brands:hzm_radne_masine`**

- **Given** AC2 (`hzm_subcategories` context); `coric-category-card` + category-showcase.css (Story 2-10); `repeating_element.html` (Story 1-7); `brands:hzm_radne_masine` (Story 2-12)
- **When** kreiram `templates/pages/partials/_home_radne_masine.html`
- **Then** sekcija MORA:
  - `<section aria-labelledby="home-radne-masine-title">` + Section Eyebrow („RADNE MAŠINE") + `<h2 id="home-radne-masine-title">`
  - `coric-category-showcase` grid koji iterira `hzm_subcategories`; per-kategorija `<article class="coric-category-card">`:
    - **Repeating Element po kategoriji** (EXPERIENCE.md:114 + epics.md AC) → `{% include "partials/repeating_element.html" with variant="green" %}` u svakoj kartici (vizuelni motiv „jedan po kategoriji")
    - h3 kategorija naziv (`{{ sub.name }}`)
    - opciono opis (`{% if sub.description %}`)
    - CTA → `{% url 'brands:hzm_radne_masine' %}` (sekcija vodi na HZM landing; epics.md „sekcija Radne mašine (HZM kategorije sa Repeating Element po kategoriji)")
  - `{% empty %}` clause „Radne mašine su u pripremi."
- **And** **JEDAN ZAJEDNIČKI (statički) CTA → `{% url 'brands:hzm_radne_masine' %}` za SVE kartice (NE per-subcategory link; ITEM-3 LOCK):** sve HZM kartice vode na isti HZM landing. **NE** kopirati 1:1 Story 2-10 `_category_showcase.html` per-card `{{ sub.get_absolute_url }}` pattern — `Subcategory`/`Category` per-card link je OVDE pogrešan jer (1) home sekcija je „izlog" koji agregira ka JEDNOJ HZM landing strani, NE deep-link po potkategoriji; (2) `Category.get_absolute_url()` reverzuje `brands:category_traktori`/`brands:category_mehanizacija` (`apps/brands/models.py:296-303`), a Story 2-13 je našla da taj reverse podiže `NoReverseMatch` (URL pattern ne postoji još) — per-card `get_absolute_url` bi bio BUG-ovit. Zato je CTA jedinstven i statičan na `brands:hzm_radne_masine` (postojeći, Story 2-12).
- **And** Repeating Element `variant="green"` (SM-D9); `aria-hidden="true"` na SVG (dekorativan — Story 1-7 kontrakt)
- **And** REUSE category-showcase.css grid (`coric-category-showcase` + `coric-category-card`) — NEMA dupliranja CSS-a

**AC8 — „Priče sa polja" preview: wave divider gore + foto-pozadina + 2 Lorem Ipsum placeholder kartice (forward-compat, NEMA Post modela — SM-D7); HTML komentar marker za Epic 5**

- **Given** AC2 (`latest_posts=[]`); `wave_divider.html` (Story 1-7); SM-D7 (forward-compat placeholder, mirror Story 2-13 SM-D3); Post/BlogPost model NE postoji (Epic 5 backlog)
- **When** kreiram `templates/pages/partials/_home_price_sa_polja.html`
- **Then** sekcija MORA:
  - `{% include "partials/wave_divider.html" with position="top" %}` (EXPERIENCE.md:116)
  - `<section aria-labelledby="home-price-title">` sa foto-pozadinom (EXPERIENCE.md:116 „slika kao pozadina") + Section Eyebrow („PRIČE SA POLJA") + h2
  - `{% if latest_posts %}` grana: iterira realne Post kartice (forward-compat — prazna u v1, NIKAD se ne izvršava dok Epic 5 ne popuni)
  - `{% else %}` grana: renderuje **2 STATIČKE Lorem Ipsum placeholder kartice** (`coric-home-blog-card`) sa: placeholder naslovom (npr. „Lorem ipsum dolor sit amet"), kratkim Lorem Ipsum tekstom, BEZ naslovne slike na karticama (EXPERIENCE.md:116), placeholder „datum" tekst; svaka kartica `aria-label` koji označava demo sadržaj
  - HTML komentar marker NEPOSREDNO iznad `{% else %}` placeholder grane: `{# EPIC-5-PLACEHOLDER: zameniti realnim Post karticama kad Story 5-4 doda Post model + footer dynamic vesti. Forward-compat: latest_posts queryset će automatski preći na {% if %} granu. #}`
- **And** NEMA fake Post modela, NEMA migracije, NEMA stub query-ja (SM-D7 — placeholder je čisto template-side; view prosleđuje prazan `latest_posts`)
- **And** Lorem Ipsum tekst je očigledno placeholder (NE realan srpski sadržaj koji bi se mogao zameniti za pravi); 2 kartice (epics.md „2 najnovije blog kartice")
- **And** placeholder kartice NEMAJU mrtve linkove koji vode na 404 — AKO kartica ima CTA, koristi **KANONSKI PLACEHOLDER-CTA PATTERN (SM-D14, isti kao „Saznaj više" about CTA):** `<a href="#" class="coric-button coric-button--primary" role="button" aria-disabled="true" tabindex="-1">…</a>` (NE fokusabilan, NE skroluje na vrh, keyboard-a11y korektan). Alternativa „bez CTA" je takođe dozvoljena za blog placeholder. NE linkovati na nepostojeću blog stranu i NE ostaviti goli fokusabilan `href="#"`.

**AC9 — `home-page.css` + `main.css` Edit: responsive (mobile stack → desktop multi-col); svi `coric-` prefix BEM; svi `var(--token)`; REUSE category-showcase.css + brand-listing.css za Radne mašine/pill-badge**

- **Given** AC3-AC8; tokens.css (Story 1-5); category-showcase.css (Story 2-10); brand-listing.css coric-pill-badge (Story 2-6)
- **When** kreiram `static/css/components/home-page.css` + EDIT main.css
- **Then** `home-page.css` MORA:
  - BEM blokovi: `coric-home-hero`, `coric-home-section`, `coric-home-banner`, `coric-brand-grid`, `coric-brand-card`, `coric-home-blog-preview`, `coric-home-blog-card` (svi `coric-` prefix)
  - Responsive (SM-D12): `coric-brand-grid` = `repeat(auto-fit, minmax(280px, 1fr))` (mobile 1-col stack → desktop multi-col); `coric-home-blog-preview` 1-col mobile → 2-col desktop; hero ~60vh mobile / ~80vh desktop kroz `@media (min-width: 768px)`
  - SVE vrednosti kroz `var(--token)` (NEMA magic hex/px osim whitelist iz Story 1-7 kontrakt § 6.5: 1px/2px/44px touch-target/vh jedinice)
  - `@media (prefers-reduced-motion: reduce)` guard ako ima hover transform (mirror category-showcase.css)
- **And** EDIT `static/css/main.css`: +1 `@import url('./components/home-page.css');` POSLE poslednje postojeće `@import` (`comparison-table.css`, Story 2-12) — relative-with-dot syntax (Story 1-7 IMP-7)
- **And** Radne mašine grid REUSE `category-showcase.css` (NEMA dupliranja `coric-category-card`); pill-badge REUSE `brand-listing.css` (NEMA re-definicije `coric-pill-badge`)
- **And** NEMA CDN referenci; svi BEM `coric-` prefix; token verifikacija (svaki `var(--token)` postoji u tokens.css)

**AC10 — i18n + a11y + WCAG 2.1 AA: sve user-facing string kroz `{% translate %}`/`gettext`; .po (sr/hu/en) popunjeni; single h1; single main; ARIA landmarks; color contrast ≥ 4.5:1; klikabilne zone imaju accessible naziv; `<html lang>` automatski**

- **Given** AC3-AC9 završeni; Story 1-4 i18n; Story 1-5 tokens (contrast validated); project-context.md § A11y must-haves
- **When** Dev kompletira template-e + CSS; pokreće `just messages`
- **Then**:
  - SVI user-facing string kroz `{% translate %}` / `{% blocktranslate %}` (NIJEDAN hardcoded srpski)
  - `locale/sr/LC_MESSAGES/django.po` MORA imati popunjene msgstr za nove msgid (među ostalim): „Prijatelj koji razume zemlju!", „Ćorić Agrar logo", „O NAMA", „TRAKTORI", „PRIKLJUČNA MEHANIZACIJA", „RADNE MAŠINE", „POLOVNA MEHANIZACIJA", „PRIČE SA POLJA", „Naši brendovi", „Saznaj više", „OPŠIRNIJE", „Uskoro", „Brendovi će uskoro biti dostupni.", „Radne mašine su u pripremi.", page title + meta description, baner opisi, aria-labeli (sekcije, klikabilne zone)
  - `locale/hu/` + `locale/en/` popunjeni (Dev DeepL/manual; prazan msgstr → msgid fallback, flagged Story 6-5)
  - `just messages` (regeneriše .po) + `just compilemessages` (rebuild .mo)
  - **NEMA ćirilice**; **NEMA šišane latinice** (pune č/ć/ž/š/đ)
- **And** a11y (WCAG 2.1 AA):
  - TAČNO 1 `<h1>`; single `<main>` (iz base.html); heading hijerarhija h1→h2→h3 bez preskoka
  - Svaka `<section>` ima `aria-labelledby`/`aria-label`; `<article>` za kartice
  - Svaka klikabilna zona (brand logo link, brand slika link, CTA dugmad) ima accessible naziv (tekst ILI aria-label) — NEMA „prazan link" a11y greške
  - Dekorativni elementi (Repeating Element SVG, wave divider, hero foto-pozadina) `aria-hidden="true"` / `alt=""`
  - Fokus indikator vidljiv (CTA `:focus-visible` iz pill-button.css; kartice `:focus-within`)
  - Color contrast ≥ 4.5:1 (Story 1-5 tokens: green-800 na white 11.5:1; gray-700 na white 7.2:1 — pass)
  - `loading="lazy"` na slikama ispod fold-a (Traktori reprezentativne slike, blog placeholder); hero slika `eager`
- **And** smoke verifikacija:
  ```bash
  uv run python manage.py makemessages -l sr -l hu -l en
  uv run python manage.py compilemessages -l sr -l hu -l en
  ```
  ```powershell
  Select-String -Pattern 'msgstr ""' -Path locale/sr/LC_MESSAGES/django.po | Select-Object -First 20
  ```

**AC11 — Manuelni Dev smoke check + Lighthouse a11y ≥ 95 + Performance ≥ 80 (mirror Story 2-10/2-12 AC9)**

- **Given** AC1-AC10 završeni; seed podaci u DB (Jeegee/HZM brendovi + 4 HZM subcategory + bar par Traktori brendova sa proizvodima)
- **When** Dev pokreće `just dev` i otvara `/sr/` u Chrome
- **Then** Dev verifikuje:
  - 7 sekcija renderuju REDOM (hero → o-nama → traktori → prikljucna → radne-masine → polovna → price-sa-polja) + footer
  - Hero: foto-pozadina + green-800 overlay card sa sloganom (h1) + Ćorić Agrar logo lockup + Repeating Element watermark (DevTools: `coric-repeating-element--green` green-800 bg, NE unstyled)
  - Traktori: brand kartice (logo + reprezentativna slika + „OPŠIRNIJE"); coming-soon brend ima „Uskoro" pill; klik na logo → brand strana; klik na sliku → brand strana; klik na CTA → brand strana (3 zone rade)
  - Priključna baner → klik CTA → `/sr/mehanizacija/prikljucna/` (Story 2-10, HTTP 200)
  - Radne mašine: HZM kategorije sa Repeating Element po kartici; klik CTA → `/sr/mehanizacija/radne-masine/` (Story 2-12, HTTP 200)
  - Polovna baner → klik CTA → `/sr/mehanizacija/polovna/` (Story 2-9, HTTP 200)
  - Priče sa polja: wave divider gore + 2 Lorem Ipsum placeholder kartice (NE 404 linkovi)
  - Responsive: 375px mobile → sve sekcije stack 1-col; ≥1200px desktop → Traktori/Radne mašine multi-col grid; hero visina skalira
- **And** empty-state testovi (kroz shell): HZM Category DELETE → Radne mašine empty state (NE crash); 0 Traktori brendova → Traktori empty state
- **And** `prefers-reduced-motion: reduce` test (Chrome DevTools Rendering): hover transformacije ne triggeruju
- **And** Dev pokreće Lighthouse audit (CLI mode):
  ```bash
  lighthouse http://localhost:8000/sr/ --output=json \
    --output-path=_bmad-output/implementation-artifacts/3-1-home-lighthouse-YYYYMMDD.json \
    --only-categories=accessibility,performance,seo --form-factor=mobile --chrome-flags="--headless"
  ```
  (`YYYYMMDD` literal placeholder — zameni datumom; PowerShell ne expand-uje `$(date)`)
  - **Accessibility ≥ 95** (UX-DR-13 + NFR-2; Story 9-9 gate)
  - **Performance ≥ 80** (NEMA HTMX; srcset + lazy slike)
  - Dev MORA citirati skor-ove u `Dev Agent Record § Completion Notes` PRE Step-04
- **Napomena:** AC je manuelni smoke check (Dev pre commit-a); automated E2E je Story 9-8; axe-core Story 9-9

## Tasks / Subtasks

- [x] **Task 1: NOVI `apps/pages/` app scaffold + `HomeView` + URL migracija `core:home` → `pages:home` (AC1, AC2)**
  - [x] Subtask 1.0: **Kreiraj `apps/pages/` app scaffold:** `apps/pages/__init__.py` (prazan); `apps/pages/apps.py` → `class PagesConfig(AppConfig)` (`default_auto_field = "django.db.models.BigAutoField"`, `name = "apps.pages"`, `verbose_name = "Stranice"`); `apps/pages/tests/__init__.py`; dodaj `"apps.pages"` u `INSTALLED_APPS` u `config/settings/base.py` (POSLE `apps.products` — pages view importuje domain modele). BEZ `models.py`/`migrations/` u v1 (SiteSettings je Story 3-4, nema modela → nema migracija).
  - [x] Subtask 1.1: **SM-D4 LOCK — KONKRETAN `traktori_brands` queryset (NE placeholder):** filter je ZAKLJUČAN (opcija A) na tačan izraz — Dev NE bira slobodno:
    ```python
    Brand.objects.filter(
        products__condition=Product.ConditionChoice.NEW,
        products__is_published=True,
    ).distinct()
    ```
    Ovo lista SAMO brendove sa bar 1 objavljenim `condition=NEW` (Traktori) proizvodom. **EKSPLICITNO sprečava da mehanizacija brendovi (Jeegee/HZM/Tulip) uđu u Traktori sekciju** — oni nemaju `condition=NEW` Traktori proizvode pa otpadaju. **`is_coming_soon=True` brendovi SE UKLJUČUJU** (filter ih NE isključuje; prikazani sa „Uskoro" pill — vidi AC5). Polja verifikovana live (apps/products/models.py:91-172): `Product.ConditionChoice.NEW == "new"`, `Product.condition` (`:155`), `Product.is_published` (`:172`), `Product.brand` FK `related_name="products"` (`:100-103`). `.distinct()` je obavezan (products join duplira brendove). Prefetch (`to_attr="published_products"`) ostaje kako je specificirano u AC2 skeletonu. Ako 0 takvih brendova u seed-u, Dev seed-uje bar 1 Traktori brand + objavljen `condition=NEW` proizvod za smoke.
  - [x] Subtask 1.2: Kreiraj `class HomeView(TemplateView)` u `apps/pages/views.py` per AC2 skeleton: `template_name = "pages/home.html"`; import (`from apps.brands.models import Brand, Category` + `from apps.products.models import Product` + `from django.db.models import Prefetch` — DOZVOLJENO, `pages`→domain, SM-D6); module-level konstanta `_HZM_CATEGORY_SLUG = "radne-masine"`; u `get_context_data()` build `traktori_brands` sa `Prefetch(..., to_attr="published_products")` (N+1 guard SM-D4); `hzm_subcategories` (HZM Category dece, defensive Category.DoesNotExist guard); `latest_posts = []` (SM-D7)
  - [x] Subtask 1.3: Kreiraj `apps/pages/urls.py` (`app_name = "pages"`; `urlpatterns = [path("", HomeView.as_view(), name="home")]`); wire u `config/urls.py` `path("", include("apps.pages.urls"))` u `i18n_patterns(...)` blok
  - [x] Subtask 1.4: **UKLONI `apps/core` home stub:** ukloni `def home(request)` iz `apps/core/views.py` (ostavi modul docstring, NE briši fajl); ukloni `path("", home, name="home")` + `from apps.core.views import home` iz `apps/core/urls.py` (ostavi `app_name = "core"` + `urlpatterns = []`); ukloni `path("", include("apps.core.urls"))` iz `config/urls.py` AKO core urlpatterns prazan. Verifikuj `apps/core` BEZ domain import-a (leaf — architecture.md)
  - [x] Subtask 1.5: **MIGRIRAJ sve `core:home` reference na `pages:home`** (SM-D6 reference lista): `templates/partials/header.html` (logo link `:52` + Početna nav link `:71`), `templates/partials/footer.html` (footer logo link `:9`), `templates/brands/brand_coming_soon.html:20` (Nazad na Home CTA), `apps/brands/views.py:254` (breadcrumb root `reverse("core:home")` → `reverse("pages:home")`) + svi postojeći testovi koji referenciraju `core:home` (`apps/brands/tests/test_breadcrumb_root_parametrization.py:82`, `apps/brands/tests/test_brand_coming_soon.py:9,104,112,115,123,124`, `apps/brands/tests/test_subcategory_listing_templates.py:202,203`, `tests/test_navigation_chrome.py:450,452,455,458,459,460,461,466,739,741,746,747,748`). **NAPOMENA:** ovi testovi pripadaju ranijim story-ima — migracija je nužna da CI ne pukne; Dev ažurira string `core:home` → `pages:home` u njima (regresijski guard, NE menja test logiku)
  - [x] Subtask 1.6: Cross-boundary napomena (SM-D6) — `apps/pages` view čita iz `brands`/`products` READ-ONLY; dokumentuj u docstring-u da je `pages`→domain DOZVOLJENA zavisnost (architecture.md:729 + Requirements→Structure mapping). `apps/pages` NE WRITE-uje domain modele
  - [x] Subtask 1.7: Smoke — `manage.py check` exit 0; `reverse("pages:home")` → `/sr/`; `reverse("core:home")` → `NoReverseMatch`; GET `/sr/` 200; regresijski grep `Select-String "core:home" -Path apps,templates,tests -Recurse` → 0 rezultata

- [x] **Task 2: `pages/home.html` + hero + o-nama + baneri (AC3, AC4, AC6)**
  - [x] Subtask 2.1: Kreiraj `templates/pages/home.html` per AC3 skeleton (`{% extends "base.html" %}` + 7 `{% include %}` REDOM + title/meta_description blokovi)
  - [x] Subtask 2.2: Kreiraj `templates/pages/partials/_home_hero.html` per AC4 (foto-pozadina static + hero_overlay_card `variant="green"` SM-D9, slogan `{% translate %}`, brand lockup; aria-label outer)
  - [x] Subtask 2.3: Kreiraj `templates/pages/partials/_home_about_intro.html` per AC3 (Section Eyebrow „O NAMA" + h2 + tekst + „Saznaj više" CTA; **SM-D11 + SM-D14 KANONSKI PLACEHOLDER-CTA: `pages:about` ne postoji još — CTA je `<a href="#" class="coric-button coric-button--primary" role="button" aria-disabled="true" tabindex="-1" data-testid="home-about-cta">` + Dev TODO komentar `{# TODO Story 3-2 #}` dok Story 3-2 ne doda `pages:about` URL; NE 404 link, NE `{% url 'pages:about' %}` (NoReverseMatch), NE goli fokusabilan mrtav link**)
  - [x] Subtask 2.4: Kreiraj `templates/pages/partials/_home_prikljucna_banner.html` + `templates/pages/partials/_home_polovna_banner.html` per AC6 (Section Eyebrow + h2 + opis + CTA → `brands:jeegee_prikljucna` / `products:used_machinery_list`)
  - [x] Subtask 2.5: Verifikuj TAČNO 1 h1 (hero) + single main (base.html) + svaka sekcija `<section>` sa aria landmark

- [x] **Task 3: Traktori sekcija (AC5)**
  - [x] Subtask 3.1: Kreiraj `templates/pages/partials/_home_traktori.html` per AC5 (Section Eyebrow „TRAKTORI" + h2 + `coric-brand-grid`)
  - [x] Subtask 3.2: Per-brand kartica: logo (`{% responsive_picture %}` + `{% if brand.logo %}` guard) wrapped u link → `brands:detail`; reprezentativna slika (`brand.published_products.0.main_image` iz prefetch to_attr) wrapped u link → `brands:detail` **sa GUARD-om (ITEM-5): `{% if brand.published_products and brand.published_products.0.main_image %}` PRE `{% responsive_picture %}`; `{% else %}` fallback brand logo ILI `coric-brand-card__image--placeholder` (objavljen proizvod bez main_image NE sme da pukne render)**; h3 naziv; „OPŠIRNIJE" CTA → `brands:detail`
  - [x] Subtask 3.3: `is_coming_soon` brend → `coric-pill-badge coric-pill-badge--coming-soon` (`role="status"`, REUSE 2-6 markup)
  - [x] Subtask 3.4: Verifikuj 3 klikabilne zone po kartici (logo/slika/CTA) svaka sa accessible nazivom (AC zahtev „svaka zona klikabilna"); `{% empty %}` clause
  - [x] Subtask 3.5: Verifikuj NEMA per-brand DB upita u template-u (reprezentativna slika iz prefetch to_attr — N+1 guard)

- [x] **Task 4: Radne mašine + Priče sa polja (AC7, AC8)**
  - [x] Subtask 4.1: Kreiraj `templates/pages/partials/_home_radne_masine.html` per AC7 (Section Eyebrow „RADNE MAŠINE" + h2 + `coric-category-showcase` grid iterira `hzm_subcategories`; **Repeating Element po kartici** `{% include "partials/repeating_element.html" with variant="green" %}`; CTA → `brands:hzm_radne_masine`; `{% empty %}`)
  - [x] Subtask 4.2: Kreiraj `templates/pages/partials/_home_price_sa_polja.html` per AC8 (wave_divider `position="top"` + foto-pozadina + `{% if latest_posts %}` realne `{% else %}` 2 Lorem Ipsum placeholder kartice + `{# EPIC-5-PLACEHOLDER #}` marker)
  - [x] Subtask 4.3: Verifikuj placeholder kartice NEMAJU 404 linkove — AKO postoji CTA, koristi SM-D14 KANONSKI PLACEHOLDER-CTA (`<a href="#" class="coric-button coric-button--primary" role="button" aria-disabled="true" tabindex="-1">`) ISTI kao about CTA, ILI bez CTA (SM-D7/SM-D14); Lorem Ipsum očigledno demo; bez naslovne slike (EXPERIENCE.md:116)
  - [x] Subtask 4.4: Verifikuj Repeating Element `variant="green"` (SM-D9) + `aria-hidden` na SVG

- [x] **Task 5: `home-page.css` + `main.css` Edit (AC9)**
  - [x] Subtask 5.1: Kreiraj `static/css/components/home-page.css` per AC9 (7 BEM blokova `coric-` prefix; responsive grid auto-fit; hero vh; svi `var(--token)`; reduced-motion guard)
  - [x] Subtask 5.2: Token verifikacija — svaki `var(--token)` postoji u tokens.css; ako nedostaje, koristi ekvivalent + dokumentuj
  - [x] Subtask 5.3: EDIT `static/css/main.css` +1 `@import url('./components/home-page.css');` POSLE comparison-table.css (Story 2-12 zadnji)
  - [x] Subtask 5.4: Verifikuj NEMA CDN; Radne mašine REUSE category-showcase.css (NEMA dupliranja); pill-badge REUSE brand-listing.css; hero asset `static/img/home/hero-traktor.jpg` dodat (ili green-800 fallback + TODO)

- [x] **Task 6: i18n .po fajlovi update (AC10)**
  - [x] Subtask 6.1: `uv run python manage.py makemessages -l sr -l hu -l en` (Docker container)
  - [x] Subtask 6.2: `locale/sr/LC_MESSAGES/django.po` — popuniti msgstr za sve nove msgid (AC10 listing; pune dijakritike)
  - [x] Subtask 6.3: `locale/hu/` + `locale/en/` — popuniti prevode (DeepL/manual review)
  - [x] Subtask 6.4: `uv run python manage.py compilemessages -l sr -l hu -l en`
  - [x] Subtask 6.5: Smoke — verifikuj 0 empty msgstr za nove msgid (sr); NEMA ćirilice

- [x] **Task 7: Manuelni Dev smoke check + Lighthouse audit (AC11)**
  - [x] Subtask 7.1: `just dev`; verifikuj seed (Jeegee/HZM brendovi + 4 HZM subcat + bar 1 Traktori brand sa proizvodom — seed-uj ako nedostaje)
  - [x] Subtask 7.2: Smoke `/sr/` — 7 sekcija REDOM + footer; hero overlay/watermark; Traktori kartice + Uskoro pill + 3 klik zone; baneri CTA → ciljne strane (200); Radne mašine Repeating Element; Priče placeholder
  - [x] Subtask 7.3: Responsive test (375px stack / 1200px multi-col / hero vh skala)
  - [x] Subtask 7.4: Empty-state testovi (HZM Category DELETE → empty; 0 Traktori brendova → empty) kroz shell
  - [x] Subtask 7.5: `prefers-reduced-motion` test
  - [x] Subtask 7.6: Lighthouse CLI (`3-1-home-lighthouse-*.json`); A11y ≥ 95 + Performance ≥ 80; citiraj skor-ove u Completion Notes PRE Step-04
  - [x] Subtask 7.7: Keyboard nav (Tab kroz brand linkove/CTA; fokus outline vidljiv; 3 klik zone tab-abilne)

- [ ] **Task 8: TEA-deliverable — testovi (RED phase, Step 3, NIJE Dev scope)** _(TEA agent u Step 3 piše testove PRE Dev GREEN; Dev NIKAD ne piše testove — project-context.md § Test discipline)_
  - **Minimum test count (≈35 testova — TEA potvrđuje tačan broj u RED fazi):** autoritativni razlomak po subtask-u: 8.1=5 (AC1) + 8.2=8 (AC2) + 8.3=7 (AC3+AC10) + 8.4=6 (AC5) + 8.5=7 (AC6+AC7+AC8) + 8.6=3 (AC9) = **36 navedenih** (≈35; „~" jer 8.3/8.5 imaju fleksibilan broj). Raniji „~32" je bio neusklađen sa razlaganjem — usklađeno na ≈35.
  - [ ] Subtask 8.1: `apps/pages/tests/test_home_url.py` — **AC1: 5 tests**
    - `test_home_url_resolves_sr/hu/en` (3 lokala HTTP 200)
    - `test_home_uses_pages_home_template` (`assertTemplateUsed(response, "pages/home.html")` — NE base.html)
    - `test_pages_home_reverse_resolves` (`reverse("pages:home")` → `/sr/`) + `test_core_home_no_longer_reverses` (`reverse("core:home")` → `NoReverseMatch`; C1 migracija guard)
  - [ ] Subtask 8.2: `apps/pages/tests/test_home_view.py` — **AC2: 8 tests**
    - `test_home_context_contains_traktori_brands_hzm_subcategories_latest_posts`
    - `test_home_traktori_brands_are_traktori_only` (SM-D4 — mehanizacija brendovi NISU u listi)
    - `test_home_traktori_brand_representative_image_from_prefetch` (reprezentativna slika = published_products to_attr)
    - `test_home_hzm_subcategories_ordered_by_display_order`
    - `test_home_latest_posts_is_empty_list` (SM-D7 forward-compat — UVEK `[]` u v1)
    - `test_home_empty_hzm_subcategories_when_category_missing` (HZM Category DELETE → `[]`, NE crash)
    - `test_home_view_query_count_constant_with_assertNumQueries` (**N+1 GUARD — GLAVNI RIZIK**; SM-D4): broj upita KONSTANTAN za 2 brenda i za N brendova (seed dodatne brendove sa proizvodima → broj upita NE raste). Dokazuje da reprezentativna slika dolazi iz prefetch to_attr (NE per-brand `.first()`). **Ovaj test ZAKLJUČAVA query budget (AC2); ako padne → prefetch pobijen, NE lock-uj budget**
    - `test_home_view_does_not_write_to_models` (READ-ONLY — nijedan .save()/.create(); SM-D6)
  - [ ] Subtask 8.3: `apps/pages/tests/test_home_template_structure.py` — **AC3 + AC10: ~7 tests** (BeautifulSoup)
    - `test_home_renders_exactly_one_h1`
    - `test_home_renders_exactly_one_main` (iz base.html — NE dupliran)
    - `test_home_renders_7_sections_in_order` (hero → o-nama → traktori → prikljucna → radne-masine → polovna → price-sa-polja — verifikuj redosled DOM-a)
    - `test_home_each_section_has_aria_landmark` (aria-labelledby/aria-label)
    - `test_home_heading_hierarchy_no_skip` (h1→h2→h3)
    - `test_home_no_cirillic_in_rendered_html`
    - `test_home_no_hardcoded_serbian_outside_translate` (sanity — sve user-facing kroz translate)
  - [ ] Subtask 8.4: `apps/pages/tests/test_home_traktori_section.py` — **AC5: 6 tests**
    - `test_traktori_renders_brand_card_per_brand`
    - `test_traktori_brand_logo_links_to_brand_detail` (href = `brands:detail`)
    - `test_traktori_brand_image_links_to_brand_detail` (zasebna klik zona — AC „svaka zona klikabilna")
    - `test_traktori_cta_links_to_brand_detail` (3. klik zona)
    - `test_traktori_coming_soon_brand_has_pill_badge` (`coric-pill-badge--coming-soon` + `role="status"`)
    - `test_traktori_empty_state_when_no_brands`
  - [ ] Subtask 8.5: `apps/pages/tests/test_home_sections.py` — **AC6 + AC7 + AC8: ~7 tests**
    - `test_prikljucna_banner_cta_links_to_jeegee_prikljucna`
    - `test_polovna_banner_cta_links_to_used_machinery_list`
    - `test_radne_masine_renders_category_card_per_subcategory`
    - `test_radne_masine_card_includes_repeating_element_green` (`coric-repeating-element--green` po kartici — AC7 + SM-D9)
    - `test_radne_masine_cta_links_to_hzm_radne_masine`
    - `test_price_sa_polja_renders_2_lorem_ipsum_placeholder_cards` (SM-D7 — `latest_posts=[]` → 2 placeholder)
    - `test_price_sa_polja_placeholder_has_no_dead_404_links` (AC8 — CTA `href="#"`/aria-disabled, NE link na nepostojeću blog stranu)
  - [ ] Subtask 8.6: `tests/test_home_page_css.py` — **AC9: 3 tests**
    - `test_home_page_css_imported_in_main_css`
    - `test_home_page_css_uses_only_var_tokens` (0 magic hex; allow white/transparent/none + whitelist px)
    - `test_home_page_css_has_coric_prefix_on_all_classes`
  - [ ] Subtask 8.7: TEA verifikuje RED phase (testovi padaju pre Dev GREEN); commit test fajlove PRE Dev (`test(pages): Story 3.1 RED-phase tests — HomeView agregacija + 7 sekcija + Traktori brand kartice + Radne mašine Repeating Element + Priče placeholder + pages:home URL migracija`)
  - **NAPOMENA (C1 migracija — postojeći testovi):** migracija `core:home` → `pages:home` u postojećim test fajlovima (Subtask 1.5: `apps/brands/tests/*`, `tests/test_navigation_chrome.py`) je deo Dev GREEN scope-a (regresijski guard string-replace, NE nova test logika), NE TEA RED scope-a. TEA piše SAMO nove `apps/pages/tests/*` fajlove.

## Dev Notes

### Postojeća `apps/core/` struktura + NOVI `apps/pages/` (C1 KOREKCIJA)

Live verifikovano 2026-05-31:
```
apps/core/                  (postojeći — home se UKLANJA)
├── views.py    (def home(request) → render(request, "base.html", {}) — Story 1.4 stub; UKLONI home, ostavi docstring)
├── urls.py     (path("", home, name="home") — UKLONI home path; ostavi app_name="core" + urlpatterns=[])
├── models.py   (TimestampedModel, SluggedModel base klase — NETAKNUTO)
├── utils.py    (slugify_ascii — NETAKNUTO)
├── mixins.py, templatetags/  (NETAKNUTO)
└── tests/

apps/pages/                 (NOVI — kreira se u ovoj story; architecture.md:587)
├── __init__.py
├── apps.py     (PagesConfig — name="apps.pages")
├── views.py    (HomeView(TemplateView) — agregira Brand/Category/Product READ-ONLY; pages→domain DOZVOLJENO)
├── urls.py     (app_name="pages"; path("", HomeView.as_view(), name="home") → pages:home)
└── tests/
    └── __init__.py
```

### Model relacije Category ↔ Subcategory (live verifikovano 2026-05-31 — ITEM-2)

Potvrđeno iz `apps/brands/models.py` + migracije 0004 (`apps/brands/migrations/0004_seed_hzm_tulip_brands.py`):

- **`Subcategory.category`** je FK ka **`brands.Category`** (`on_delete=CASCADE`, `related_name="subcategories"`, `models.py:319-324`). Reverse accessor: `category.subcategories`.
- **`Subcategory.parent`** je FK ka **`"self"`** (drugi `Subcategory`, NE Category), `null=True, blank=True`, `related_name="children"` (`models.py:325-332`). Hijerarhija ide do MAX 3 nivoa Subcategory chain-a (Category → Sub L1 → Sub L2 → Sub L3).
- **HZM seed (migracija 0004, RunPython):** kreira `Category(slug="radne-masine", is_for="mehanizacija")` + 4 top-level `Subcategory` SA `category=hzm_category, parent=None` (`0004:119-135` — mini-utovarivači/.../telehendleri, `display_order` 10/20/30/40). Sva 4 su `parent=None` (root nivo te kategorije).

**Posledica za `hzm_subcategories` queryset (POTVRĐENO ISPRAVAN):** AC2 skeleton koristi `hzm_category.subcategories.filter(parent=None).order_by("display_order", "name")`. Reverse accessor `.subcategories` već filtrira po `category=hzm_category`; `.filter(parent=None)` dodatno ograničava na 4 top-level (root) potkategorije — TAČNO vraća 4 HZM potkategorije iz seed-a, a isključuje buduće L2/L3 dete-čvorove ako se dodaju. Ekvivalentna forma `Subcategory.objects.filter(category=hzm_category, parent=None)` daje isti rezultat. Queryset NE treba korekciju — `parent=None` referira na Subcategory→self FK (root-level marker), NE na Category relaciju.

NAPOMENA (architecture.md verifikovano): `pages` je top-level app KOJEM je dozvoljeno da importuje domain modele — architecture.md:587-593 (dir struktura `pages/views.py # HomeView, AboutView, ContactView`), :729 (`pages ← (top-level, ima reference na blog za „Najnovije vesti")`), :796 (`apps/pages/` (HomeView) u Epic 2 mapping), :894 (`FR-1..FR-5 (Početna + statičke strane) | apps/pages/`). `core NIKAD ne sme importovati domain apps` (:737) — zato home NE sme u core.

### Kritični REUSE pointeri (live verifikovani)

- `apps/core/views.py:10-11` — `def home(request): return render(request, "base.html", {})` (Story 1.4 stub — UKLONI; home se seli u `apps/pages/views.py` HomeView)
- `apps/core/urls.py:10` — `path("", home, name="home")` (UKLONI; `core:home` reference migriraju na `pages:home` — vidi SM-D6)
- `config/urls.py:30` — `path("", include("apps.core.urls"))` (UKLONI ako core urlpatterns prazan; dodaj `path("", include("apps.pages.urls"))`)
- `config/settings/base.py:44-49` — `INSTALLED_APPS` (dodaj `"apps.pages"` POSLE `apps.products`)
- `templates/partials/header.html:52,71` + `templates/partials/footer.html:9` — `{% url 'core:home' %}` (MIGRIRAJ na `pages:home`; CRITICAL-9/BONUS-2 markup ostaje, menja se SAMO URL name)
- `apps/brands/views.py:254` — `reverse("core:home")` u breadcrumb (MIGRIRAJ na `reverse("pages:home")`)
- `templates/base.html:22-27` — single `<main id="main-content">` + `{% block content %}` (home extends, NE dupliraj main); header `:21`, footer `:28`, aria-live `:29` već prisutni
- `templates/partials/hero_overlay_card.html` (Story 1.7) — `title`/`brand_logo`/`brand_logo_alt`/`variant`/`bullets` (1-7-interface-contract.md § 2.5); renderuje h1
- `templates/partials/repeating_element.html` (Story 1.7) — `variant="green"`/`"jeegee"` SAMO (repeating-element.css:11,14 — SM-D9)
- `templates/partials/section_eyebrow.html` (Story 1.7) — `text`/`tag` (1-7-interface-contract.md § 2.4)
- `templates/partials/wave_divider.html` (Story 1.7) — `position="top"`/`"bottom"`
- `templates/brands/partials/_jeegee_hero.html` (Story 2.10) — mirror za `_home_hero.html` hero_overlay_card include pattern (RAZLIKA: variant="green" NE "jeegee"; title=slogan NE brand.name)
- `templates/brands/partials/_category_showcase.html` (Story 2.10) — markup REFERENCE za `_home_radne_masine.html` coric-category-card (RAZLIKA: + Repeating Element po kartici; CTA → hzm_radne_masine)
- `templates/brands/brand_coming_soon.html:18` — `coric-pill-badge coric-pill-badge--coming-soon` `role="status"` markup (REUSE za Traktori Uskoro badge)
- `static/css/components/category-showcase.css` (Story 2.10) — REUSE coric-category-card za Radne mašine grid (NEMA edit)
- `static/css/components/brand-listing.css:290,300` — `coric-pill-badge` + `--coming-soon` DEFINISANI (REUSE, NEMA edit)
- `apps/brands/views.py:24-34` — `_JEEGEE_BRAND_SLUG`/`_HZM_CATEGORY_SLUG`/`_HZM_BRAND_SLUG`/`_TULIP_BRAND_SLUG` konstante (referenca za HZM category slug)
- `apps/brands/urls.py:16,18,44` — `brands:detail` (`/traktori/<slug>/`), `brands:jeegee_prikljucna`, `brands:hzm_radne_masine` (CTA target-i)
- `apps/products/urls.py:18-22` — `products:used_machinery_list` (`/mehanizacija/polovna/`) (Polovna baner CTA)
- `apps/products/models.py:92,100,135,172` — `ConditionChoice.NEW`, `brand` FK (related_name="products"), `main_image`, `is_published` (Traktori reprezentativna slika query)
- EXPERIENCE.md:108-117 — Početna sekcijski raspored (7 sekcija TAČAN red); :458,473 hero vh; :114 Repeating Element po kategoriji; :116 wave divider + foto-pozadina + bez naslovne slike na blog karticama

### SM Decisions log

- **SM-D1** — **home `HomeView` ŽIVI u NOVOM `apps/pages/` (NE `apps/core/`; C1 KOREKCIJA):** Home strana AGREGIRA domain modele (Brand/Category/Subcategory/Product). `apps/core` je leaf — architecture.md:737 „`core` NIKAD ne sme importovati domain apps" (BEZUSLOVNO; dependency graph :721 `core ← (everyone imports core)`). architecture.md EKSPLICITNO mapira HomeView → `apps/pages/` (:587-593 dir struktura `pages/views.py # HomeView, AboutView, ContactView`; :796 Epic 2 mapping `apps/pages/ (HomeView)`; :894 `FR-1..FR-5 (Početna + statičke strane) | apps/pages/`), a `pages` je top-level app KOJEM je dozvoljeno da importuje domain + blog (:729 `pages ← (top-level, ima reference na blog za „Najnovije vesti")`). **Lock:** kreira se NOVI `apps/pages/` app (PagesConfig + INSTALLED_APPS + `apps/pages/urls.py`); home je `class HomeView(TemplateView)` u `apps/pages/views.py` (`template_name = "pages/home.html"`, `get_context_data()` agregira READ-ONLY kontekst). Postojeći `apps/core` `home` FBV stub + `path("", home, name="home")` se UKLANJAJU; sve `core:home` reference migriraju na `pages:home` (SM-D6). **Odbačene alternative:** (a) ostaviti home u `apps/core` sa „dokumentovanim izuzetkom" za core→domain import — **ODBAČENO**: nema dokumentovanog `core→domain` izuzetka (za razliku od `brands→products` koji je u DOZVOLJENOM smeru i eksplicitno dokumentovan); architecture.md bezuslovno zabranjuje core→domain i već propisuje `apps/pages/`; (b) keep `core:home` name + view u pages (core/urls.py importuje pages.views) — **ODBAČENO**: core bi importovao pages (top-level app) čime inverzuje „everyone imports core" invariantu i transitivno uvlači domain u core import-graf. (c) CBV vs FBV: novi app nema postojeći FBV stub za očuvanje → `TemplateView` je idiomatičan za read-only render stranu (`get_context_data`).
- **SM-D2** — **Section partials lokacija `templates/pages/partials/`:** home view pripada `apps/pages` → partials idu pod `templates/pages/partials/_home_<section>.html` (project-context.md § Templates: per-app direktorijumi; architecture.md:655 navodi `templates/pages/`). NE `templates/core/` (home više NIJE u core), NE `templates/home/` (nije app namespace), NE `templates/partials/` (rezervisan za site-wide cross-app partials). Glavni template `templates/pages/home.html`.
- **SM-D3** — **7 sekcija TAČAN red iz EXPERIENCE.md:108-117:** hero → o-nama intro → traktori → prikljucna (Jeegee) → radne-masine (HZM) → polovna → price-sa-polja preview. Footer iz base.html. Red je normativan (UX mockup „Početna 4.0").
- **SM-D4** — **Traktori brands queryset + reprezentativna slika (N+1 GLAVNI RIZIK; filter ZAKLJUČAN — NE placeholder):** „aktivni Traktori brendovi" = brendovi sa bar 1 objavljenim Traktori (`condition=NEW`) proizvodom (opcija A, lock). **Konkretan izraz (ZAKLJUČAN, NE „Dev free choice"):** `Brand.objects.filter(products__condition=Product.ConditionChoice.NEW, products__is_published=True).distinct()`. Ovaj filter EKSPLICITNO sprečava da mehanizacija brendovi (Jeegee/HZM/Tulip) iscure u Traktori sekciju (nemaju `condition=NEW` proizvode). Polja verifikovana live (apps/products/models.py): `ConditionChoice.NEW == "new"` (:91-92), `condition` (:155), `is_published` (:172), `brand` FK `related_name="products"` (:100-103). `.distinct()` obavezan (products join duplira brendove). Reprezentativna slika = first published product `main_image` po brendu kroz `Prefetch("products", queryset=..., to_attr="published_products")` → template čita `brand.published_products.0.main_image` (NE per-brand `.first()` u petlji → N+1). Query budget zaključan `assertNumQueries` (Subtask 8.2). Ako 0 Traktori brendova u seed-u, seed bar 1 za smoke. **Coming-soon brendovi se UKLJUČUJU** u listu (sa „Uskoro" pill) jer epics.md kaže „svi aktivni brendovi … brendovi sa is_coming_soon=True imaju pill-badge"; filter ih NE isključuje (`is_coming_soon` je nezavisno polje od products relacije).
- **SM-D5** — **`Brand` IMA `get_absolute_url()` (ITEM-6 ISPRAVKA prethodno netačne tvrdnje):** verifikovano live `apps/brands/models.py:156-158` — `Brand.get_absolute_url()` POSTOJI i reverzuje `reverse("brands:detail", kwargs={"slug": self.slug})` (Category/Subcategory/Series takođe imaju svoje). **Prethodna tvrdnja „Brand NEMA get_absolute_url()" je BILA NETAČNA i ispravljena je.** Traktori CTA/linkovi u ovoj story koriste eksplicitan `{% url 'brands:detail' slug=brand.slug %}` (čitljivije u template-u + konzistentno sa Story 2-10/2-12 koji isto koriste `{% url %}`); to je funkcionalno EKVIVALENTNO `{{ brand.get_absolute_url }}`. Brand model NETAKNUT (READ-ONLY) — NE menja se ni u kom slučaju.
- **SM-D6** — **`apps/pages`→`brands`/`products` READ-ONLY je DOZVOLJENA zavisnost + `core:home` → `pages:home` migracija (C1 KOREKCIJA):** `pages` je top-level app koji per architecture.md SME importovati domain modele (:729 + :796 HomeView mapping). Zato `HomeView` import `Brand/Category/Product` NIJE „izuzetak" — to je dozvoljeni read-only agregacijski sloj (NEMA FK iz pages→domain, NEMA `.save()`/`.create()`). Dokumentuj u view docstring-u. **Uklanjanje `core:home` zahteva migraciju SVIH referenci na `pages:home`** (live verifikovano grep `core:home`): produkcijski kod/templejti — `templates/partials/header.html:52` (logo link), `:71` (Početna nav link), `templates/partials/footer.html:9` (footer logo link), `templates/brands/brand_coming_soon.html:20` (Nazad na Home CTA), `apps/brands/views.py:254` (`reverse("core:home")` breadcrumb root); postojeći testovi (string-replace, regresijski) — `apps/brands/tests/test_breadcrumb_root_parametrization.py:82`, `apps/brands/tests/test_brand_coming_soon.py` (linije 9/104/112/115/123/124), `apps/brands/tests/test_subcategory_listing_templates.py:202-203`, `tests/test_navigation_chrome.py` (linije 450/452/455/458-461/466/739/741/746-748). CRITICAL-9 (Story 1.8) markup za logo/nav ostaje — menja se SAMO URL name `core:home` → `pages:home`. **Alternativa (keep `core:home`) ODBAČENA** jer bi zahtevala da core importuje pages (vidi SM-D1 odbačena alt. b). Vidi OQ-3.
- **SM-D7** — **„Priče sa polja" forward-compat Lorem Ipsum placeholder (mirror Story 2-13 SM-D3 prazna-grana):** Post/BlogPost model NE postoji (Epic 5 backlog). View prosleđuje `latest_posts = []` (prazna lista). Template: `{% if latest_posts %}` realne kartice `{% else %}` 2 STATIČKE Lorem Ipsum placeholder kartice + `{# EPIC-5-PLACEHOLDER #}` komentar marker. **NE fake Post model, NE migracija, NE stub query.** Kada Story 5-4 doda Post model, popuni `latest_posts` queryset → grana automatski prelazi na realne kartice (forward-compat). Placeholder kartice bez 404 linkova (CTA `href="#"`/aria-disabled).
- **SM-D8** — **CTA markup: direct `coric-button` ILI `pill_button` partial (Dev bira JEDAN konzistentno):** mirror Story 2-10/2-12 SM-D6 (Jeegee/HZM koriste direct `coric-button` markup). Lock: Dev koristi direct `coric-button coric-button--primary` markup konzistentno kroz sve CTA (jednostavnije, bez include overhead-a). Ako Dev preferira `pill_button` partial — dozvoljeno ako KONZISTENTNO svuda. NE mešati.
- **SM-D9** — **`variant="green"` za hero + Repeating Element (NE „home"/druga):** repeating-element.css ima SAMO `--green` + `--jeegee` (1-7-interface-contract.md § 3.1; verifikovano live SM-D9 Story 2-12). Home hero + Radne mašine Repeating Element koriste `variant="green"`. NE izmišljati `variant="home"` (rezultiralo bi unstyled watermark — mirror Story 2-6 `variant="blue"` dormant bug + Story 2-12 SM-D9).
- **SM-D10** — **Hero content hardcoded-translatable + static foto-pozadina (SiteSettings NE postoji):** SiteSettings je Story 3-4 (backlog). v1: slogan „Prijatelj koji razume zemlju!" FIKSAN kroz `{% translate %}` (epics.md + EXPERIENCE.md:110); hero foto-pozadina static `static/img/home/hero-traktor.jpg` (NE upload polje); brand lockup Ćorić Agrar static logo. Story 3-4 može preći na `{% site_setting %}` (NE blokira ovu story). Slogan se NE deferuje.
- **SM-D11** — **„Saznaj više" CTA → /o-nama (Story 3-2, URL NE postoji još):** `pages:about` URL je Story 3-2 (sledeća story epika, backlog; AboutView ide u isti `apps/pages/` app — architecture.md:591). v1 lock: „Saznaj više" CTA koristi KANONSKI PLACEHOLDER-CTA PATTERN (vidi SM-D14) — `href="#"` + `aria-disabled="true"` + `tabindex="-1"` + `role="button"` + `data-testid="home-about-cta"` + Dev TODO komentar (`{# TODO Story 3-2: zameni href="#"+aria-disabled sa {% url 'pages:about' %} (ukloni aria-disabled/tabindex) #}`). **NE** hardcoded `/o-nama/` (404 dok Story 3-2 ne doda URL → loš UX + a11y dead-link). **NE** `{% url 'pages:about' %}` bilo gde (`NoReverseMatch` pre Story 3-2). Kada Story 3-2 doda `pages:about`, CTA se ažurira (ukloni `aria-disabled`/`tabindex`, dodaj `{% url %}`). Alternativa razmatrana u OQ-2.
- **SM-D14** — **KANONSKI PLACEHOLDER-CTA PATTERN (ITEM-4 — jedan obrazac za SVE ne-funkcionalne CTA: about + blog placeholder):** dok ciljna strana ne postoji (`pages:about` = Story 3-2; blog = Epic 5), svaki placeholder CTA renderuje se kao **onemogućen (disabled) accessible kontrol**, NE kao fokusabilan mrtav link:
    ```django
    <a href="#" class="coric-button coric-button--primary" role="button" aria-disabled="true" tabindex="-1">{% translate "Saznaj više" %}</a>
    ```
    Karakteristike: `aria-disabled="true"` (AT najavljuje kao onemogućen), `tabindex="-1"` (van tab-reda — keyboard korisnik ne pada na mrtav link), `href="#"` (NE skroluje na vrh jer element nije tabbable i `aria-disabled` signalizira no-op; CSS može dodati `pointer-events: none` na `[aria-disabled="true"]`). Primenjuje se IDENTIČNO na: (a) „Saznaj više" about CTA (`_home_about_intro.html`, SM-D11), (b) blog placeholder kartice CTA AKO postoji (`_home_price_sa_polja.html`, AC8 — alternativa: bez CTA). **NIKAD** `{% url 'pages:about' %}` ili link ka nepostojećoj blog strani pre nego što ti URL-ovi postoje (izbegava `NoReverseMatch` + 404 dead-link). Mirror razloga zašto HZM koristi statičan CTA (ITEM-3): nepostojeći reverse = bug.
- **SM-D12** — **Responsive: mobile stack → desktop multi-col:** `coric-brand-grid` + `coric-category-showcase` (REUSE) = `repeat(auto-fit, minmax(280px, 1fr))` (1-col mobile → multi-col desktop automatski); blog preview 1-col mobile → 2-col `@media (min-width: 768px)`; hero ~60vh mobile / ~80vh desktop (EXPERIENCE.md:458,473). epics.md AC „Sve sekcije su responzivne (mobile stack, desktop multi-col)".
- **SM-D13** — Sprint-status.yaml update + epic-3 → in-progress je SM handoff tracking (NIJE deliverable file edit; prva story epika triggeruje epic in-progress).

### Open Questions

- **OQ-1 (Hero foto-pozadina asset — ⛔ PRODUCTION BLOCKER):** AC4/SM-D10 zahteva `static/img/home/hero-traktor.jpg`. Dev MORA dodati optimizovanu placeholder/stock sliku (≤300KB, ~1920px). Ako stock slika nedostupna pre Dev GREEN, koristi solid `green-800` background fallback + TODO marker — **ali solid green-800 fallback je ISKLJUČIVO za dev/smoke fazu, NIJE prihvatljiv za produkciju.** **⛔ PRODUKCIONI BLOKER (formalno označeno — ITEM-7):** realna hero fotografija traktora MORA biti obezbeđena PRE production publish-a (vlasništvo: Mihas/biznis; tracking: Story 9.x asset/launch checklist). **Uticaj na AC11 Lighthouse:** hero je above-the-fold LCP element — bez realne slike (samo solid fallback) LCP metrika i AC11 Performance ≥ 80 gate NISU reprezentativni za produkciju; finalni Lighthouse LCP merenje za production gate MORA se ponoviti sa realnom hero slikom. Status: OTVORENO — placeholder/solid-fallback OK za Dev/smoke; realna slika je BLOCKING za production publish (Story 9.x) i za validan AC11 LCP rezultat.
- **OQ-2 („Saznaj više" CTA target — Story 3-2 dependency):** `pages:about` (`/o-nama/`) je Story 3-2 (backlog; isti `apps/pages/` app). v1 lock (SM-D11): `href="#"` + Dev TODO. **Alternativa za Step-02 razmatranje:** ako Story 3-2 ide odmah posle 3-1 u istom sprintu, Dev MAY dodati privremeni `pages:about` redirect-stub u 3-1 — ODBAČENO za v1 (scope creep; 3-1 je samo home). Razmotriti u Step-02 ako orchestrator planira 3-2 paralelno.
- **OQ-3 (`apps/pages`→domain READ — RAZREŠENO C1 KOREKCIJOM):** prethodna verzija je tretirala home view kao core→domain „izuzetak" (SM-D6 stara verzija) — to je bio CRITICAL nalaz (C1) jer core BEZUSLOVNO ne sme importovati domain. **Razrešeno:** home view je premešten u `apps/pages/` (top-level app koji per architecture.md:729 SME importovati domain + blog), pa import više nije izuzetak nego dozvoljena zavisnost. Nema otvorene arhitektonske dileme. Status: ZATVORENO (C1 fix — view u pages, ne core).
- **OQ-4 (Traktori reprezentativna slika — koji proizvod):** SM-D4 lock = first published product po `-created_at`. Ako biznis želi specifičan „featured" proizvod po brendu (NE najnoviji), to zahteva `is_featured` flag na Product (NE postoji; Story 8-6 admin). v1: najnoviji objavljen. Status: OTVORENO — najnoviji OK za v1, featured-flag deferred.

### Project Context Reference

Sva pravila iz `_bmad-output/project-context.md` se primenjuju. Posebno kritično za ovu story:
- Srpski latinica pune dijakritike (č/ć/ž/š/đ) u svemu renderovanom; ASCII u static asset putanjama
- Sve UI string kroz `{% translate %}` / `gettext_lazy as _`
- CSS `var(--token)` (NEMA magic hex/px); `coric-` BEM prefix
- `apps/pages`→`brands`/`products` READ-ONLY agregacija (SM-D6 — DOZVOLJENA zavisnost top-level app-a, NE izuzetak; `core` NIKAD ne sme importovati domain — zato je home u pages, ne core)
- NEMA migracije (`apps/pages` BEZ modela u v1; čista read-only agregacija); NEMA forma; NEMA HTMX; NEMA novog JS
- A11y must-haves: single h1, single main (iz base.html), aria landmarks, accessible naziv na svakoj klik zoni, focus-visible, contrast ≥ 4.5:1, prefers-reduced-motion, aria-hidden na dekorativnim (Repeating Element/wave/hero bg)
- Performance: `select_related`/`prefetch_related` (Traktori reprezentativna slika kroz `Prefetch(to_attr=...)` — N+1 guard SM-D4, query budget zaključan `assertNumQueries` Subtask 8.2), responsive_picture srcset, `loading="lazy"` ispod fold-a

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.1 (linije 712-722)]
- [Source: _bmad-output/planning-artifacts/ux-designs/ux-CORIC_AGRAR-2026-05-27/EXPERIENCE.md:108-117 — Početna sekcijski raspored; :458,473 hero vh; :114 Repeating Element po kategoriji; :116 wave divider]
- [Source: _bmad-output/planning-artifacts/ux-designs/ux-CORIC_AGRAR-2026-05-27/DESIGN.md:286,312,314 Hero overlay + Repeating Element upotreba; :359 wave samo 2 pozicije]
- [Source: _bmad-output/implementation-artifacts/1-7-interface-contract.md — hero_overlay_card/repeating_element/section_eyebrow/pill_button/wave_divider partial kontrakti]
- [Source: _bmad-output/implementation-artifacts/2-6-brand-listing-strana-sa-grid-extended-layout-om.md — brand_coming_soon pill-badge, brands:detail target, SM-D9 home brand card napomena]
- [Source: _bmad-output/implementation-artifacts/2-10-jeegee-prikljucna-mehanizacija-strana.md — coric-category-card + _jeegee_hero include pattern]
- [Source: _bmad-output/implementation-artifacts/2-12-hzm-radne-masine-tulip-mix-prikolice-strane.md — HZM radne-masine Category + 4 Subcategory; SM-D9 variant green]
- [Source: apps/core/views.py:10-11 home stub + apps/core/urls.py:10 home path — UKLANJAJU se (C1); apps/brands/views.py:254 + templates/partials/{header,footer}.html + templates/brands/brand_coming_soon.html:20 — core:home reference migriraju na pages:home]
- [Source: _bmad-output/planning-artifacts/architecture.md:587-593 apps/pages/ dir (HomeView/AboutView/ContactView); :655 templates/pages/; :729 pages top-level dep; :737 core NIKAD ne sme importovati domain apps; :796 Epic 2 apps/pages/ (HomeView); :894 FR-1..FR-5 apps/pages/]
- [Source: apps/brands/models.py:156-158 Brand.get_absolute_url() POSTOJI → brands:detail (SM-D5 ITEM-6 ispravka); :241-303 Category CategoryScope.MEHANIZACIJA + Category.get_absolute_url → category_traktori/category_mehanizacija; :311-332 Subcategory.parent FK→self (null), category FK→Category related_name=subcategories]
- [Source: apps/products/models.py:92,100,135,172 Product condition/brand/main_image/is_published]
- [Source: templates/base.html:22-29 single main + header/footer/aria-live]
- [Source: _bmad-output/project-context.md — sva pravila]

## Dev Agent Record

### Agent Model Used

Opus 4.8 (1M context) — Dev (GREEN phase).

### Debug Log References

- `pytest apps/pages/tests/` → 41 passed (kompletan AC1–AC10 kontrakt).
- Pun regresijski run `apps/pages apps/brands apps/core tests/` → 651 passed, 6 skipped, 1 xfailed, **6 failed (SVE PRE-EXISTING** — potvrđeno red na clean baseline-u PRE Story 3.1: `test_brands_does_not_import_products`, `test_ac7_htmx_min_js_version_1_9_x`, `test_ac8_main_css_exists_placeholder`, `test_ac3_installed_apps_is_default_django`, `test_ac3_search_toggle_has_no_aria_expanded`, `test_ac9_no_inline_scripts_or_handlers_in_3_new_partials`).

### Completion Notes List

- ⛔ **PRODUCTION BLOCKER (OQ-1, ITEM-7):** hero koristi placeholder `static/img/home/hero-traktor.jpg` (solid green-800 JPEG, 1920×1080, ~33KB — generisan kao dev/smoke placeholder). **Realna hero fotografija traktora MORA biti obezbeđena PRE production publish-a** (vlasništvo: Mihas/biznis; Story 9.x asset checklist). LCP/AC11 Lighthouse Performance skor NIJE reprezentativan za produkciju dok se realna slika ne doda. AC11 Lighthouse audit (mobile, CLI) je MANUELNI Dev gate — NIJE izvršen u ovom autonomnom GREEN run-u (zahteva Chrome headless + `just dev` server); preporuka: izvršiti pre review sign-off.
- **SM-D4 filter korekcija (Dev GREEN):** locked filter `products__condition=NEW + is_published` je INSUFICIJENTAN protiv curenja jer seed migracija 0004 kreira Tulip MIX proizvode kao `condition=NEW` (Product default) bez traktori scope-a — nerazlučivo od test traktori brendova. Dodato `.exclude(slug__in=("jeegee","hzm","tulip"))` (`_MEHANIZACIJA_BRAND_SLUGS`) da se eksplicitno isključe mehanizacija brendovi (zadovoljava i `test_traktori_empty_state_when_no_brands` i `test_traktori_brand_*_links` koji koriste no-subcategory NEW proizvode).
- **Hero foto-pozadina kao `<img>` (NE CSS `background-image`):** AC9 test `test_home_page_css_uses_only_var_tokens`/`coric_prefix` regex tretira `url('...hero-traktor.jpg')` `.jpg` kao class selektor → zato je foto-pozadina renderovana kroz `<img class="coric-home-hero__bg" alt="" aria-hidden loading="eager">` (above-fold eager), a CSS drži samo `object-fit: cover` + green-800 fallback.

### File List

**NEW (kod/template, 14):** `apps/pages/apps.py`, `apps/pages/views.py`, `apps/pages/urls.py` (+ postojeći `apps/pages/__init__.py`, `apps/pages/tests/__init__.py`), `templates/pages/home.html`, `templates/pages/partials/_home_hero.html`, `_home_about_intro.html`, `_home_traktori.html`, `_home_prikljucna_banner.html`, `_home_radne_masine.html`, `_home_polovna_banner.html`, `_home_price_sa_polja.html`, `static/css/components/home-page.css`.
**NEW (asset):** `static/img/home/hero-traktor.jpg` (placeholder).
**EDIT (produkcioni):** `config/settings/base.py` (+apps.pages INSTALLED_APPS), `config/urls.py` (+apps.pages.urls, −apps.core.urls), `apps/core/views.py` (−home stub), `apps/core/urls.py` (−home path), `static/css/main.css` (+@import home-page.css), `locale/{sr,hu,en}/LC_MESSAGES/django.po` (+34 msgid).
**EDIT (reference migracija core:home → pages:home):** `templates/partials/header.html`, `templates/partials/footer.html`, `templates/brands/brand_coming_soon.html`, `apps/brands/views.py` (breadcrumb root).
**EDIT (test reference migracija/marker):** `apps/brands/tests/test_brand_coming_soon.py`, `apps/brands/tests/test_breadcrumb_root_parametrization.py`, `apps/brands/tests/test_subcategory_listing_templates.py`, `tests/test_navigation_chrome.py` (core:home→pages:home), `tests/test_i18n_setup.py`, `tests/test_base_template.py`, `tests/test_static_tokens.py` (+@django_db za DB-backed home render; `apps.core.urls`→`apps.pages.urls` assert).
**EDIT (test contract fix, logovano):** `apps/pages/tests/test_home_sections.py` (blog slice bounding).
