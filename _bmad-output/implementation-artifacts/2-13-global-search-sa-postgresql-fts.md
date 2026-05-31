---
story-id: "2.13"
story-key: 2-13-global-search-sa-postgresql-fts
title: Global Search sa PostgreSQL FTS
status: ready-for-dev
epic_num: 2
epic_title: Public Catalog — Browse Brands & Products
module: NOVI apps/search/ (dedikovan site-wide search app — SearchView FBV + 2 HTMX endpoint-a; search_vector SearchVectorField DODAT na products.Product kroz products migraciju 0004; unaccent + pg_trgm CREATE EXTENSION kroz zasebnu products migraciju 0004a koja PRETHODI AddField-u; header search-toggle wiring (Story 1.8 deferred); 3 partiala + search.css + search-expand.js; locale .po edits)
created: 2026-05-31
last_modified: 2026-05-31
author: Mihas (SM autonomous; ZAVRŠAVA Epic 2 — POSLEDNJA story epica. Reuse-uje kanonski HTMX pattern iz Story 2-8 (request.htmx branching, OOB aria-live, debounce 300ms, min loading 200ms, empty-state) + wire-uje header search-toggle button koji je Story 1-8 IMP-3 NAMERNO ostavio bez funkcionalnosti („wiring stiže u Story 2.13"). PRVA story koja uvodi `django.contrib.postgres` u INSTALLED_APPS + PostgreSQL extension migracije (unaccent, pg_trgm) + SearchVectorField na Product + GIN indeks. PRVA story koja kreira NOVI app posle Story 2.2 — vidi SM-D1 module ownership rationale.)
depends_on:
  - 2-2-product-i-related-modeli                   # Product (name_sr/_hu/_en, description_sr/_hu/_en modeltranslation polja; is_published; get_absolute_url; main_image) — search_vector se DODAJE ovde
  - 2-8-tractor-listing-strana-sa-htmx-filterima   # KANONSKI HTMX pattern: request.htmx branching, OOB aria-live `<div hx-swap-oob="innerHTML:#aria-live">`, debounce delay:300ms, htmx-indicator min loading 200ms, empty-state partial, hx-push-url; coric-button BEM za empty-state CTA
  - 1-8-sticky-nav-top-header-footer-language-switcher-partial  # header.html `<button class="coric-nav__search-toggle" aria-label="Otvori pretragu">` (IMP-3: NEMA aria-expanded, NEMA wiring — Story 2.13 owner). Story 2.13 EDIT-uje header.html da doda hx-* + aria-expanded + aria-controls + dropdown mount point
  - 1-6-base-templates-sa-bootstrap-5-htmx-setup   # base.html `{% aria_live %}` singleton (apps/core/templatetags/htmx_aria.py) + HTMX vendor učitan + HtmxMiddleware (config/settings/base.py:60 → request.htmx)
  - 2-3-image-pipeline-sa-sorl-thumbnail-responsive-srcset  # {% responsive_picture %} za product thumbnail u dropdown rezultatu (opciono — vidi SM-D11)
---

# Story 2.13: Global Search sa PostgreSQL FTS

Status: ready-for-dev

## Opis

As a **posetilac (Marko — poljoprivrednik koji zna naziv modela ili brenda i želi da brzo skoči na njega bez navigacije kroz meni; Đorđe — Mihasov klijent koji testira na 375px ekranu, koristi tastaturu (Tab/Esc) i NVDA koji najavljuje broj predloga kroz aria-live region)**,

I want **da kliknem na search ikonu u header-u (postojeći `<button class="coric-nav__search-toggle">` iz Story 1.8) koja se proširi u inline tekstualno polje (slide-in s desna, 200ms), ukucam ključnu reč (min 2 znaka), i da dobijem dropdown sa rezultatima grupisanim po tipu (Proizvodi / Objave), rangiranim po relevantnosti, diacritic-insensitive (npr. „berba" pronalazi „Berba" i „bérba") i case-insensitive, sa max 5 rezultata po grupi i „Vidi sve" linkom; rezultati su locale-aware (samo trenutni jezik); empty-state „Nema rezultata za '{query}'" sa CTA blokom popularnih kategorija + brendova; Esc zatvara search i vraća fokus na ikonu**,

so that **brzo dolazim do željenog proizvoda ili objave bez ponavljanog page-reload-a (Marko ukuca „TB804", vidi predlog odmah, klikne i stigne na detalj stranu; Đorđe tabuje do search ikone, otvori je Enter-om, ukuca upit, NVDA mu najavi „5 predloga", strelicama prolazi kroz listbox opcije, Esc zatvara i fokus se vraća na ikonu); strana zadovoljava WCAG 2.1 AA (aria-live najava, `role="listbox"`/`role="option"` semantika, focus management, Esc-to-close) i ZAVRŠAVA Epic 2 javni katalog**.

Ova story je **POSLEDNJA story Epic 2** i **ZATVARA dug iz Story 1.8** (IMP-3: header search button je NAMERNO ostavljen bez wiring-a — „wiring stiže u Story 2.13"). Uvodi tri nova arhitektonska elementa:

- **`django.contrib.postgres` u INSTALLED_APPS** (PRVI put u projektu) — potreban za `SearchVector`, `SearchQuery`, `SearchRank`, `SearchVectorField`, `GinIndex`. Vidi **SM-D6**.
- **PostgreSQL extension migracije (`unaccent` + `pg_trgm`)** kroz zasebnu products migraciju **0004a** koja PRETHODI AddField migraciji 0004 (extension MORA postojati pre nego što GIN indeks ili `unaccent()` funkcija budu referencirani). Vidi **SM-D7** (migration ordering) + project-context.md § Migrations discipline (RunPython sa reverse_code).
- **`search_vector` SearchVectorField na products.Product** + **GIN indeks** + populacija kroz **SearchVector annotation pri query-time** (NE trigger, NE signal, NE save() override — vidi SM-D8 i „no Celery u v1" constraint).

**Module odluka (SM-D1):** Search živi u **NOVOM `apps/search/` app-u**. Architecture.md AR-26 + § struktura (linije 581-586) predviđa hipotetički `catalog/` app koji bi sadržao listing + filter + search, ALI stvarna implementacija je odstupila — listing view-ovi (`TractorListView` 2.8, `UsedMachineryListView` 2.9) žive u `apps/products/`. Global search je **site-wide cross-domain** feature (pretražuje Product danas, Post sutra u Epic 5) — NE pripada nijednom domenskom app-u. Stavljanje u `products/` bi vezalo cross-domain search za jedan domen i prekršilo forward-compat za Objave grupu. Stavljanje u `core/` bi prekršilo pravilo „core ne sme importovati domain apps" (project-context.md § Cross-boundary import — `apps/search/views.py` MORA importovati `Product`). Dedikovan `apps/search/` app je čista granica: zavisi OD products (jednosmerno), spreman da doda blog dep u Epic 5. Vidi **SM-D1** za pun rationale + **SM-D2** za INSTALLED_APPS poziciju (POSLE products).

**Objave (blog) odluka (SM-D3) — KRITIČNA:** Epic 5 (Blog) je `backlog` — `apps/blog/` + `Post` model NE postoje. Story 2.13 gradi **forward-compatible grouping skelet** koji renderuje SAMO Proizvodi grupu danas, ALI sa strukturom (grouped dict `{"proizvodi": [...], "objave": [...]}`) gde je `objave` lista UVEK prisutna ali PRAZNA u v1. Dropdown template iterira kroz grupe i renderuje grupu SAMO ako ima rezultata (`{% if group.results %}`) — pa Objave grupa je nevidljiva dok blog ne postoji, ali kod NE traži refaktor kad Epic 5 doda Post search. **NE stub-uje se** fake Post model (YAGNI — project-context.md). **NE defer-uje se** cela story. Epic 5 Story 5.x će dodati `search_vector` na Post + popuniti `objave` granu u `SearchView`. Vidi **SM-D3** za pun rationale + forward-compat ugovor.

**Strana KORISTI sledeće artefakte iz prethodnih Story-ja:**

- **`Product` model** (Story 2.2) — translated `name_sr/_hu/_en` + `description_sr/_hu/_en` (modeltranslation, verifikovano `apps/products/translation.py`); `is_published` BooleanField (search vraća samo published); `get_absolute_url()` (link u rezultatu); `main_image` (opciona thumbnail u dropdown-u per SM-D11); `created_at` (tie-break za proizvode per SM-D10).
- **Header `<button class="coric-nav__search-toggle">`** (Story 1.8, verifikovano `templates/partials/header.html:99-106`) — Story 2.13 EDIT-uje ovaj button: dodaje `aria-expanded="false"`, `aria-controls="coric-search-panel"`, i wiring kroz `search-expand.js`. Mount point za expand panel + dropdown se DODAJE u header.html (vidi SM-D12).
- **`{% aria_live %}` singleton** (Story 1.6, `apps/core/templatetags/htmx_aria.py` → `<div id="aria-live" aria-live="polite" aria-atomic="true">` u base.html) — search dropdown OOB swap najavi „X predloga" u njega.
- **Kanonski HTMX pattern** (Story 2.8) — `request.htmx` branching (vraća partial), OOB `<div hx-swap-oob="innerHTML:#aria-live">` wrapped u `{% if request.htmx %}` guard (SM-D14 mirror SM-D23 iz 2.8), `hx-trigger="keyup changed delay:300ms"` debounce, `htmx-indicator` Bootstrap spinner sa min loading 200ms (SM-D15).
- **`coric-button`, `coric-button--primary/--secondary` BEM** (Story 1.7/2.6) — empty-state CTA dugmad.
- **`{% responsive_picture %}` template tag** (Story 2.3) — opciona product thumbnail u dropdown rezultatu (SM-D11).
- **`HtmxMiddleware`** (Story 1.6, `config/settings/base.py:60`) — `request.htmx` boolean.

**Foundation za:**

- **Epic 5 Story 5.x (Blog Search):** dodaje `search_vector` na `Post` model + popunjava `objave` granu u `SearchView.get_grouped_results()` (forward-compat ugovor SM-D3). NEMA refaktora `apps/search/` strukture.
- **Story 6.x (SEO):** dedikovana `/pretraga/?q=...` strana (SM-D16 — „Vidi sve" link) može dobiti meta noindex + canonical u Epic 6.

**Princip:** Hybrid server-side + HTMX. Vanilla JS modul (`search-expand.js`, IIFE + `'use strict';`) za expand/collapse panel + Esc-to-close + focus return + keyboard listbox navigaciju + `prefers-reduced-motion` respect; HTMX za debounced query → dropdown swap + OOB aria-live. PostgreSQL FTS query kroz `SearchVector` annotation (locale-aware kolone per SM-D9) + `unaccent` (diacritic-insensitive) + `SearchRank` (name weight A > description weight B). CSS BEM `coric-` prefiks + isključivo `var(--token)`. Sve user-facing string kroz `{% translate %}` / `{% blocktranslate %}` (sr nplurals=3 plural za „X predloga"). **GET-only** (search forma je `hx-get`, NEMA POST, NEMA CSRF, NEMA ratelimit per SM-D17 — read-only public query, ALI vidi SM-D17 za query-length DoS guard).

**Strukturna arhitektura — repository delta:** Repository dobija **10 NOVO + 8 EDIT + 0 DELETE** + **2 migracije na products** (0004a extension + 0004 AddField/AddIndex). Autoritativna lista (uključujući tačan broj) je u **interface-contract § 1** — ovaj dokument i interface-contract MORAJU se slagati (IMP-7).

| Path | Tip | Razlog |
|---|---|---|
| `apps/search/__init__.py` | NOVO | Novi app package |
| `apps/search/apps.py` | NOVO | `SearchConfig(AppConfig)` — `name = "apps.search"` |
| `apps/search/views.py` | NOVO | `SearchView` (FBV — vidi SM-D5 FBV vs CBV) + `search_query()` helper; `request.htmx` branching (dropdown partial vs full „Vidi sve" strana); grouped results dict `{"proizvodi": [...], "objave": []}` (SM-D3 forward-compat); locale-aware SearchVector (SM-D9); min-2-char guard (SM-D13); query-length cap (SM-D17) |
| `apps/search/urls.py` | NOVO | `app_name="search"`; `path("htmx/pretraga/", views.search_dropdown, name="dropdown")` (HTMX endpoint) + `path("pretraga/", views.SearchResultsView..., name="results")` („Vidi sve" full strana — SM-D16) |
| `apps/search/search.py` | NOVO | PostgreSQL FTS query helper-i (per architecture.md linija 585 `search.py` konvencija) — `build_product_search_qs(query, language_code)` vraća annotated+ranked QuerySet[Product] |
| `templates/search/partials/_search_dropdown.html` | NOVO | Dropdown rezultati grupisani po tipu (`role="listbox"`); per-grupa heading + max 5 `role="option"`; „Vidi sve" link; UKLJUČUJE OOB aria-live (guarded `{% if request.htmx %}`) |
| `templates/search/partials/_search_empty.html` | NOVO | Empty-state „Nema rezultata za '{query}'" + CTA blok popularnih kategorija + brendova (SM-D18) |
| `templates/search/search_results.html` | NOVO | „Vidi sve" full strana (`{% extends "base.html" %}`) — SM-D16 |
| `static/css/components/search.css` | NOVO | Search expand panel (slide-in 200ms), dropdown, listbox option, empty-state; `coric-search-*` BEM; `@media (prefers-reduced-motion: reduce)` (no slide animacija) |
| `static/js/search-expand.js` | NOVO | Vanilla IIFE — toggle expand panel + slide-in, Esc-to-close + focus return na search-toggle, click-outside close, keyboard listbox nav (ArrowUp/Down/Enter), aria-expanded sync; respektuje prefers-reduced-motion |
| `templates/partials/header.html` | EDIT | Search button dobija `aria-expanded="false"` + `aria-controls="coric-search-panel"` + `data-search-toggle`; DODAJE search expand panel mount point (`<div id="coric-search-panel" class="coric-search-panel" hidden>` sa `<form hx-get>` + dropdown target) — vidi SM-D12 |
| `apps/products/models.py` | EDIT (ADD field) | DODAJE `search_vector = SearchVectorField(null=True, editable=False)` na Product + `GinIndex(fields=["search_vector"], name="products_search_gin")` u Meta.indexes (SM-D8; ime ≤30 char — vidi SM-D20 C1) |
| `apps/products/migrations/0004a_enable_search_extensions.py` | NOVO (migracija) | `RunPython` ili `migrations.RunSQL` koji `CREATE EXTENSION IF NOT EXISTS unaccent;` + `CREATE EXTENSION IF NOT EXISTS pg_trgm;` (reverse: DROP EXTENSION) — PRETHODI 0004 (SM-D7). Alternativno `django.contrib.postgres.operations.UnaccentExtension` + `TrigramExtension` |
| `apps/products/migrations/0004_product_search_vector.py` | NOVO (migracija) | `AddField` search_vector + `AddIndex` GIN; `dependencies` na 0004a (SM-D7) |
| `config/settings/base.py` | EDIT | DODAJE `"django.contrib.postgres"` u INSTALLED_APPS (SM-D6) |
| `config/urls.py` | EDIT | DODAJE `path("", include("apps.search.urls"))` (vidi SM-D2 include order) |
| `static/css/main.css` | EDIT | DODAJE `@import url('./components/search.css');` (mirror Story 2.8 import pattern — Task 6.5) |
| `locale/sr/LC_MESSAGES/django.po` | EDIT | sr msgstr za nove msgid + 3 plural slot-a (SM-D19) |
| `locale/hu/LC_MESSAGES/django.po` | EDIT | hu prevodi (nplurals=2) |
| `locale/en/LC_MESSAGES/django.po` | EDIT | en prevodi (nplurals=2) |

**Brojanje (AUTORITATIVNO — usklađeno sa interface-contract § 1, IMP-7):** **10 NOVO** (apps/search: `__init__`, apps, views, urls, search.py = 5; templates: _search_dropdown, _search_empty, search_results = 3; static: search.css, search-expand.js = 2 → 5+3+2 = 10) + **2 migracije** (0004a + 0004) + **8 EDIT** (header.html, products/models.py, settings/base.py, config/urls.py, **static/css/main.css**, + 3 .po = 5 + 3 = 8) + **0 DELETE** (+ sprint-status.yaml rutinski, NE računa se u code delta). **Kanonsko brojanje: 10 NOVO + 2 migracije + 8 EDIT (uklj. 3 .po + main.css).** Interface-contract § 1 sadrži punu listu sa vlasništvom.

Postojeći fajlovi koji ostaju **NETAKNUTI** (regression guards): `apps/products/views.py` (TractorListView/UsedMachineryListView/ProductDetailView netaknuti — search NE živi ovde), `apps/products/urls.py`, `apps/products/translation.py` (search_vector NIJE translated polje — vidi SM-D9 zašto), `apps/products/admin.py`, `apps/brands/`, `apps/core/`, `apps/media_pipeline/`, `templates/base.html` (aria-live tag + HTMX vendor već prisutni — header.html include se ne menja na nivou base.html), `static/css/tokens.css`, `static/vendor/`, postojeći `static/css/components/*.css` (osim NOVE search.css), `templates/products/*`, `templates/brands/*`.

## Kriterijumi prihvatanja

**AC1 — `apps/search/` app kreiran i registrovan; `django.contrib.postgres` u INSTALLED_APPS; `apps.search` POSLE `apps.products` u INSTALLED_APPS (jednosmerna zavisnost search → products); `config/urls.py` uključuje `apps.search.urls`; `python manage.py check` exit 0**

- **Given** postojeći INSTALLED_APPS (verifikovano `config/settings/base.py:43-47` — core, brands, products, media_pipeline) BEZ `django.contrib.postgres`; postojeći `config/urls.py` i18n_patterns include order (brands → products → core)
- **When** kreiram `apps/search/` (sa `__init__.py`, `apps.py` `SearchConfig(name="apps.search")`), dodajem `"django.contrib.postgres"` + `"apps.search"` u INSTALLED_APPS, i `path("", include("apps.search.urls"))` u config/urls.py
- **Then**:
  - `"apps.search"` je registrovan POSLE `"apps.products"` u INSTALLED_APPS (SM-D2 — search importuje Product, jednosmerna dep mirror PR-D1)
  - `"django.contrib.postgres"` je u INSTALLED_APPS (SM-D6 — potreban za SearchVectorField + GinIndex Meta validacije)
  - `apps.search.urls` ima `app_name = "search"`
  - `config/urls.py` include `apps.search.urls` — pozicija u i18n_patterns NE shadow-uje postojeće pattern-e (vidi SM-D2 deconfliction: `pretraga/` i `htmx/pretraga/` su statički bez slug-a)
  - `uv run python manage.py check` exit code 0
  - `reverse("search:dropdown")` → `/sr/htmx/pretraga/`; `reverse("search:results")` → `/sr/pretraga/` (locale-aware)

**AC2 — `search_vector` SearchVectorField DODAT na products.Product + GIN indeks; migracija 0004 (AddField + AddIndex) zavisi od 0004a (CREATE EXTENSION unaccent + pg_trgm); migracija manually reviewed; `migrate --plan` čist; reverzibilna**

- **Given** Product model (Story 2.2, verifikovano `apps/products/models.py`); `_ProductIndex` postojeći subclass; `django.contrib.postgres` registrovan (AC1)
- **When** dodajem na Product: `from django.contrib.postgres.search import SearchVectorField` + `from django.contrib.postgres.indexes import GinIndex`; field `search_vector = SearchVectorField(_("Search vektor"), null=True, editable=False)`; u `Meta.indexes` dodajem `GinIndex(fields=["search_vector"], name="products_search_gin")` (ime je 19 char — ≤ Django `Index.max_name_length = 30`; NE koristi se `_ProductIndex` subclass jer je on `models.Index`, ne `GinIndex` — vidi SM-D20 C1); kreiram migracije 0004a + 0004
- **Then**:
  - **VERIFIKACIJA JE STRUKTURNA (schema introspection), NE runtime:** AC2 dokazuje SAMO da `search_vector` kolona + `products_search_gin` GIN indeks POSTOJE u schema-i (`makemigrations --check` clean, `migrate --plan` order, introspekcija `Product._meta.indexes`). AC2 NE dokazuje da runtime upit koristi tu kolonu — kolona je UVEK NULL u v1 (nema trigger/signal/save koji je popunjava), a runtime filtriranje ide ISKLJUČIVO kroz annotation alias (vidi AC3/AC4 + SM-D8). GIN indeks na NULL koloni je no-op (forward-compat skelet ka v1.1 materijalizovanom pristupu).
  - GIN indeks ima ime **`products_search_gin`** (19 char — ≤ Django `Index.max_name_length = 30`; vidi SM-D20 C1 za zašto NE `products_product_search_gin` i zašto NE `_ProductIndex` subclass)
  - `search_vector` je `null=True` (SM-D8 — annotation-at-query-time strategija NE materijalizuje vector u kolonu u v1; field + GIN indeks postoje za forward-compat ako se pređe na materijalizovani trigger pristup u v1.1; vidi SM-D8 puni rationale) + `editable=False` (ne prikazuje se u admin formi)
  - migracija **0004a** (`0004a_enable_search_extensions.py` ili sufiks po Dev izboru — vidi SM-D7) sadrži `CREATE EXTENSION IF NOT EXISTS unaccent;` + `CREATE EXTENSION IF NOT EXISTS pg_trgm;` kroz `migrations.RunSQL` (reverse `DROP EXTENSION IF EXISTS ...`) ILI `django.contrib.postgres.operations.UnaccentExtension()` + `TrigramExtension()`; `dependencies = [("products", "0003_...")]`
  - migracija **0004** (`AddField` search_vector + `AddIndex` GIN) ima `dependencies = [("products", "0004a_...")]` — extension PRETHODI indeksu (SM-D7)
  - `uv run python manage.py makemigrations products --check` ne prijavljuje missing migrations posle implementacije
  - `uv run python manage.py migrate --plan` prikazuje 0004a PRE 0004
  - migracije su manually reviewed (project-context.md § Migrations discipline; `RunSQL`/operation ima reverse)
  - search_vector NIJE u `apps/products/translation.py` (SM-D9 — locale handling je u SearchVector annotation, NE u modeltranslation virtuelnim poljima)

**AC3 — `SearchView` / `search_dropdown` FBV izvršava PostgreSQL FTS upit: `SearchVector` na locale-aware name + description kolonama, `unaccent` diacritic-insensitive, case-insensitive; vraća grouped dict `{"proizvodi": [...], "objave": []}`; samo `is_published=True`; min-2-char guard; query-length cap**

- **Given** AC1 + AC2; Product translated kolone `name_<lang>` + `description_<lang>`; trenutni aktivni locale kroz `django.utils.translation.get_language()`
- **When** GET `/sr/htmx/pretraga/?q=berba` sa `HX-Request: true`; view poziva `build_product_search_qs("berba", "sr")` iz `apps/search/search.py`
- **Then**:
  - upit koristi `SearchVector("name_sr", weight="A", config=...) + SearchVector("description_sr", weight="B", config=...)` (SM-D9 — locale-aware kolone bira-ju se po `get_language()`; fallback na `_sr` kolone ako locale nepoznat per MODELTRANSLATION_FALLBACK_LANGUAGES=("sr",))
  - **diacritic-insensitive (OBA smera — IMP-1)**: ostvareno kroz `unaccent` obmotan na OBE strane (kolone u `SearchVector` + query u `SearchQuery`) — ILI `config` postavljen na custom unaccent-aware text search config. **Tačan import (KOREKCIJA tokom GREEN protiv Django 5.2.14): `from django.contrib.postgres.lookups import Unaccent`** (`Unaccent` živi u `django.contrib.postgres.lookups`, NE u `...search` — `from ...search import Unaccent` baca ImportError; `SearchVector`/`SearchQuery`/`SearchRank` ostaju u `...search`) — Dev bira (SM-D9 implementacijska napomena). Test asertuje OBA smera: query „berba" pronalazi proizvod čiji name sadrži „Bérba"/„BERBA" **I** query „Bérba" pronalazi proizvod čiji name sadrži „berba" (jednosmerni unaccent — npr. samo na koloni — ne zadovoljava AC3)
  - **NAPOMENA (stemmer, IMP-1 / OQ-5):** `'simple'` config nema stemmer — morfološke varijante („berbu" → „berba") NE matchuju u v1; prihvaćen trade-off (vidi SM-D9 stemmer napomena + OQ-5)
  - **case-insensitive**: PostgreSQL FTS to-tsvector je inherentno case-folding (lowercases tokens) — test asertuje „TB804" i „tb804" daju iste rezultate
  - rezultat je `dict` sa **UVEK prisutnim ključevima** `"proizvodi"` (lista ranked Product) i `"objave"` (UVEK prazna `[]` u v1 — SM-D3 forward-compat); view NE pokušava da query-uje Post (model ne postoji)
  - QuerySet filtriran `is_published=True` (search NE vraća draft/archived proizvode)
  - **min-2-char guard** (SM-D13): ako `len(q.strip()) < 2` → view vraća partial sa „Unesi makar 2 znaka." porukom (EXPERIENCE.md linija 248), NE izvršava SQL upit, OOB aria-live najavi 0 predloga ili „Unesi makar 2 znaka"
  - **query-length cap** (SM-D17): query duži od 100 znakova se trunkuje na 100 (DoS guard — sprečava pathološki dugačke tsquery upite); NEMA 400 error, samo truncate
  - `request.htmx == True` → render `_search_dropdown.html` ili `_search_empty.html`; `request.htmx == False` na `/pretraga/` → render `search_results.html` full strana (SM-D16)

**AC4 — Rangiranje po relevantnosti: match u name (weight A) iznad match u description (weight B); tie-break za proizvode po `-created_at` (najnoviji prvi); rezultati su `SearchRank`-ordered**

- **Given** AC3; ≥3 Product sa varirajućim match pozicijama (jedan match samo u name, jedan samo u description, dva sa match u name ali različitim created_at)
- **When** izvršavam search upit koji matchuje sve tri
- **Then**:
  - QuerySet je `.annotate(rank=SearchRank(vector, query)).order_by("-rank", "-created_at")` (SM-D10)
  - Product sa match u `name` rangira IZNAD Product sa match samo u `description` (weight A > B; `SearchRank` weights `{"A": 1.0, "B": 0.4, ...}` default ili eksplicitni — Dev koristi default Django weights osim ako Mihas zatraži tuning per OQ-2)
  - tie-break: dva Product-a sa istim rank-om → `-created_at` (najnoviji prvi) per epics.md AC („po datumu dodavanja za proizvode") + SM-D10
  - **NAPOMENA forward-compat (SM-D3):** epics.md kaže „najnoviji prvi za blog" — blog tie-break (`-published_at`) se implementira u Epic 5 kad Post dobije search; v1 implementira SAMO proizvodi tie-break (`-created_at`)

**AC5 — Header search-toggle button (Story 1.8) WIRED: klik proširi inline polje (slide-in s desna 200ms); `aria-expanded` toggle; min 2 znaka pokreće HTMX request sa debounce 300ms; loading indikator min 200ms**

- **Given** header.html `<button class="coric-nav__search-toggle">` (Story 1.8, BEZ aria-expanded — IMP-3); `search-expand.js`; `search.css`
- **When** EDIT-ujem header.html + kreiram JS/CSS
- **Then**:
  - search button dobija `aria-expanded="false"` (initial) + `aria-controls="coric-search-panel"` + `data-search-toggle` atribut
  - DODAJE se mount point `<div id="coric-search-panel" class="coric-search-panel" hidden>` (SM-D12) koji sadrži `<form hx-get="{% url 'search:dropdown' %}" hx-trigger="keyup changed delay:300ms" hx-target="#coric-search-results" hx-swap="innerHTML" hx-indicator="#coric-search-loading" role="search">` sa `<input type="search" name="q" minlength="2" autocomplete="off" aria-label="...">` + `<div id="coric-search-results">` dropdown target + `<div id="coric-search-loading" class="htmx-indicator">` spinner
  - klik na button → `search-expand.js` toggle-uje `hidden` na panelu + `aria-expanded` na button-u + fokus prelazi na `<input>`; slide-in animacija 200ms (CSS transform; `@media prefers-reduced-motion: reduce` → instant, no transform transition)
  - kucanje min 2 znaka (`minlength="2"` HTML5 + server-side guard SM-D13) → HTMX `keyup changed delay:300ms` (debounce 300ms) → request; ispod 2 znaka HTMX se ipak okida ali server vraća „Unesi makar 2 znaka" partial (SM-D13)
  - loading: `htmx-indicator` Bootstrap spinner sa `aria-busy` (HTMX auto) + min 200ms (CSS transition mirror Story 2.8 SM-D13/SM-D15)

**AC6 — Dropdown prikazuje rezultate grupisane po tipu (Proizvodi / Objave); max 5 po grupi; `role="listbox"` + `role="option"` ARIA; „Vidi sve" link po grupi; aria-live OOB najavi „X predloga"**

- **Given** AC3-AC5; `_search_dropdown.html` partial; grouped results dict
- **When** view vraća dropdown sa N proizvoda
- **Then** `_search_dropdown.html` MORA:
  - `{% load i18n media_tags %}`
  - Outer `<div id="coric-search-results">` HTMX target (INVARIJANTAN — header.html `hx-target`)
  - `<ul class="coric-search-dropdown__list" role="listbox" aria-label="{% translate 'Predlozi pretrage' %}">`
  - iteracija kroz grupe (`proizvodi`, `objave`); **grupa se renderuje SAMO ako ima rezultata** (`{% if ... %}`) → Objave grupa nevidljiva u v1 (SM-D3); per grupa: group heading `<li role="presentation" class="coric-search-dropdown__group-heading">{% translate "Proizvodi" %}</li>` + max 5 `<li role="option" id="..." class="coric-search-dropdown__option">` (SM-D11 — opciono thumbnail + naziv + brand)
  - svaki `role="option"` je linkable (klik vodi na `product.get_absolute_url`); keyboard-navigable kroz `search-expand.js` (ArrowUp/Down menja `aria-selected`, Enter aktivira)
  - „Vidi sve" link po grupi ka `{% url 'search:results' %}?q={{ query|urlencode }}` (SM-D16) ako ima ≥1 rezultat
  - max 5 po grupi (slice u view-u ili template `|slice:":5"` — SM-D11; view radi slice da total count za aria-live bude tačan PRE slice-a per SM-D11)
  - OOB aria-live (guarded SM-D14):
    ```django
    {% if request.htmx %}
      <div hx-swap-oob="innerHTML:#aria-live">
        {% blocktranslate count counter=suggestion_count %}{{ counter }} predlog{% plural %}{{ counter }} predloga{% endblocktranslate %}
      </div>
    {% endif %}
    ```
  - NEMA inline `style`; NEMA ćirilice; NEMA šišane latinice; sve string kroz `{% translate %}`/`{% blocktranslate %}`

**AC7 — Empty-state: „Nema rezultata za '{query}'" + CTA blok popularnih kategorija + brendova; min-2-char poruka „Unesi makar 2 znaka."**

- **Given** AC3 (view); `_search_empty.html` partial; EXPERIENCE.md linije 247-248 empty-state spec
- **When** search vrati 0 rezultata ZA validan query (≥2 znaka) ILI query < 2 znaka
- **Then**:
  - 0 rezultata (≥2 znaka): `_search_empty.html` renderuje `<p>{% blocktranslate %}Nema rezultata za „{{ query }}".{% endblocktranslate %}</p>` + CTA blok (SM-D18): lista popularnih kategorija (`Category.objects` top N po display_order — vidi SM-D18 query) + brendova (`Brand.objects.filter(is_coming_soon=False)`) kao linkovi ka `category.get_absolute_url` / `brands:detail`
  - < 2 znaka: poruka `{% translate "Unesi makar 2 znaka." %}` BEZ CTA bloka (EXPERIENCE.md linija 248)
  - empty-state ima OOB aria-live najavu (guarded `{% if request.htmx %}`) — DVE RAZLIČITE poruke (IMP-4): too_short slučaj emituje NON-plural string „Unesi makar 2 znaka." (fiksna instrukcija, NEMA brojač), dok 0-rezultata slučaj (≥2 znaka) emituje plural „{n} predloga." (`blocktranslate count`, counter=0). Dva odvojena msgid-a — too_short NIJE plural string (vidi interface-contract § 8)
  - `{{ query }}` u poruci je auto-escaped (Django default — XSS guard; query je user input renderovan nazad)
  - **reflected XSS — FULL strana (IMP-5):** `search_results.html` echo-uje `{{ query }}` u `{% block title %}` + `<h1>` (auto-escaped golo `{{ query }}`) i u „Vidi sve"/refine href (`?q={{ query|urlencode }}`). Test MORA pokriti FULL stranu, ne samo partiale: `GET /sr/pretraga/?q=<script>alert(1)</script>` → odgovor sadrži `&lt;script&gt;` (escaped, NE izvršen) u title/h1 i `%3Cscript%3E` u href; NIKAD `|safe` na query

**AC8 — Search je locale-aware: vraća rezultate SAMO na trenutnom jeziku (sr/hu/en); kolone vektora biraju se po aktivnom locale-u**

- **Given** AC3-AC4; Product sa `name_sr="Berač"`, `name_hu="Szedő"`, `name_en="Harvester"`; aktivni locale menja se kroz URL prefiks (`/sr/`, `/hu/`, `/en/`)
- **When** isti query izvršen na `/hu/htmx/pretraga/?q=szedo` vs `/sr/htmx/pretraga/?q=berac`
- **Then**:
  - `build_product_search_qs(query, language_code)` koristi kolone za `language_code` (npr. `name_hu`/`description_hu` za hu) — `language_code` dolazi iz `get_language()` (SM-D9)
  - upit na `/hu/` sa hu terminom vraća proizvod; isti hu term na `/sr/` (gde se pretražuju `_sr` kolone) NE vraća (locale isolation per epics.md AC „vraća rezultate samo na trenutnom jeziku")
  - **fallback (SM-D9):** ako `get_language()` vrati locale van LANGUAGES (edge: bot sa neispravnim Accept-Language), view fallback-uje na `_sr` kolone (MODELTRANSLATION_FALLBACK_LANGUAGES=("sr",))
  - **region-suffix edge (IMP-3):** ako `get_language()` vrati `"sr-latn"`/`"sr-Latn"` (LocaleMiddleware može dodati script/region suffiks koji NIJE modeltranslation ključ), normalizuj strip-ovanjem suffiksa (`split("-")[0].lower()`) PRE biranja kolone → mapira na `"_sr"` kolone (NE slepi fallback). Vidi SM-D9 region-suffix napomena
  - test parametrizovan po `LANGUAGE_CODE` sr/hu/en **+ edge case `"sr-latn"` → očekivane `_sr` kolone** (IMP-3) (project-context.md § Testing — i18n parametrizacija)

**AC9 — Esc zatvara search, fokus se vraća na search ikonu; klik van panela zatvara; keyboard listbox navigacija (Arrow/Enter); WCAG 2.1 AA**

- **Given** AC5-AC6; `search-expand.js`
- **When** panel je otvoren i korisnik pritisne Esc / klikne van / koristi strelice
- **Then** `search-expand.js` MORA:
  - **Esc** → zatvara panel (`hidden=true`, `aria-expanded="false"`) + vraća fokus na `[data-search-toggle]` button (EXPERIENCE.md linija 224)
  - **klik van** panela (`document` click listener, target nije unutar panela ni toggle-a) → zatvara panel (EXPERIENCE.md linija 223)
  - **ArrowDown/ArrowUp** kad je dropdown otvoren → pomera `aria-selected` kroz `role="option"` elemente (roving); **Enter** na selektovanoj opciji → navigira na njen href
  - fokus management: otvaranje → fokus na `<input>`; zatvaranje → fokus na toggle button
  - `aria-expanded` na toggle uvek sinhronizovan sa panel visibility
  - `prefers-reduced-motion: reduce` → no slide-in transform transicija (instant show/hide)
  - **NAPOMENA:** keyboard listbox + screen-reader voice transcript (NVDA) su manual smoke (AC9 manual gate + Story 9.8/9.9 E2E); JS-runtime ponašanje se NE pokriva pytest-om (vidi interface-contract § Out-of-scope)

## Tasks / Subtasks

### Task 1 — Kreiraj `apps/search/` app + registruj (AC1)
- [x] 1.1: Kreiraj `apps/search/__init__.py` (prazan)
- [x] 1.2: Kreiraj `apps/search/apps.py` sa `class SearchConfig(AppConfig): name = "apps.search"; default_auto_field = "django.db.models.BigAutoField"`
- [x] 1.3: EDIT `config/settings/base.py` — dodaj `"django.contrib.postgres"` (uz ostale django.contrib, vidi SM-D6 pozicija) + `"apps.search"` POSLE `"apps.products"` (SM-D2)
- [x] 1.4: Kreiraj `apps/search/urls.py` sa `app_name="search"` + 2 path-a (dropdown HTMX + results full)
- [x] 1.5: EDIT `config/urls.py` — dodaj `path("", include("apps.search.urls"))` u i18n_patterns (vidi SM-D2 za poziciju + deconfliction)
- [x] 1.6: Verify `uv run python manage.py check` exit 0 + `reverse("search:dropdown")`/`reverse("search:results")` rade

### Task 2 — `search_vector` field + GIN indeks + extension migracije (AC2)
- [x] 2.1: EDIT `apps/products/models.py` — import `SearchVectorField` + `GinIndex`; dodaj `search_vector = SearchVectorField(_("Search vektor"), null=True, editable=False)` na Product; dodaj `GinIndex(fields=["search_vector"], name="products_search_gin")` u `Meta.indexes` (ime ≤30 char; NE `_ProductIndex` jer je on `models.Index` ne `GinIndex` — vidi SM-D20 C1)
- [x] 2.2: Kreiraj extension migraciju (0004a po SM-D7) — `CREATE EXTENSION IF NOT EXISTS unaccent;` + `pg_trgm;` (RunSQL sa reverse, ILI postgres operations Unaccent/Trigram Extension); `dependencies = [("products", "0003_...")]`
- [x] 2.3: `uv run python manage.py makemigrations products` → generiše AddField+AddIndex (0004); MANUAL EDIT da `dependencies` uključi 0004a (extension PRE indeksa — SM-D7)
- [x] 2.4: MANUAL REVIEW oba migration fajla (project-context.md § Migrations discipline) — checklist (IMP-11a):
  - [x] `IF NOT EXISTS` u extension ops (UnaccentExtension/TrigramExtension interno CREATE EXTENSION IF NOT EXISTS — idempotentno, IMP-9)
  - [x] `reverse_sql`/`reverse_code` (reverzibilna operacija) prisutna u OBE migracije (`migrate products 0003 --plan` unapply potvrđen)
  - [x] dependency lanac: 0003 → 0004a → 0004 (extension PRE AddField/AddIndex)
  - [x] GIN index ime `products_search_gin` (19 char) ≤30 (Django max_name_length, SM-D20)
  - [x] `migrate --plan` prikazuje 0004a PRE 0004
- [x] 2.5: `uv run python manage.py migrate --plan` → potvrdi 0004a PRE 0004; `uv run python manage.py migrate` na lokalnoj test DB

### Task 3 — FTS query helper `apps/search/search.py` (AC3, AC4, AC8)
- [x] 3.1: Implementiraj `build_product_search_qs(query: str, language_code: str) -> QuerySet[Product]` — `SearchVector` na `name_<lang>` (weight A) + `description_<lang>` (weight B) sa unaccent config (SM-D9). Import (KOREKCIJA tokom GREEN protiv Django 5.2.14): `from django.contrib.postgres.lookups import Unaccent` + `from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank` (`Unaccent` JESTE u `lookups`, NE u `...search` — `from ...search import Unaccent` baca ImportError, vidi C2)
- [x] 3.2: Build vektor kao annotation alias, filtriraj po aliasu (NE po `search_vector` koloni — vidi SM-D8 C3): `.annotate(search=<SearchVector(...A...) + SearchVector(...B...)>)` + `.annotate(rank=SearchRank("search", search_query))` + `.filter(is_published=True)` + `.filter(search=search_query)` + `.order_by("-rank", "-created_at")` (SM-D10). ⛔ NE `.filter(search_vector=search_query)` — kolona je UVEK NULL u v1 → 0 rezultata u runtime-u (vidi SM-D8 copy-paste primer)
- [x] 3.3: locale fallback (SM-D9) — (a) normalizuj region/script suffiks PRE biranja kolone (`language_code.split("-")[0].lower()` → `"sr-latn"`/`"sr-Latn"` → `"sr"`, IMP-3); (b) ako normalizovani `language_code` i dalje van LANGUAGES → koristi `"sr"` kolone
- [x] 3.4: diacritic-insensitive verifikacija (IMP-1) — Unaccent obmotan na OBE strane (kolone `Unaccent("name_<lang>")`/`Unaccent("description_<lang>")` + query `Unaccent(Value(query))`) ILI unaccent text search config; `SearchQuery(..., search_type="plain")` (IMP-10) da meta-znaci ne bacaju SyntaxError (SM-D9 implementacijska napomena)

### Task 4 — `SearchView` / `search_dropdown` view (AC3, AC5, AC6, AC7, AC8)
- [x] 4.1: Implementiraj `search_dropdown(request)` FBV (SM-D5) — čita `q` iz `request.GET`, strip + query-length cap 100 (SM-D17)
- [x] 4.2: min-2-char guard (SM-D13) — ako `< 2` → render `_search_empty.html` sa „Unesi makar 2 znaka." (NE izvršava SQL)
- [x] 4.3: poziva `build_product_search_qs(q, get_language())`; gradi grouped dict `{"proizvodi": qs[:5], "objave": []}` (SM-D3); `suggestion_count` = total PRE slice (SM-D11)
- [x] 4.4: `request.htmx` branching — render `_search_dropdown.html` (ima rezultata) ili `_search_empty.html` (0)
- [x] 4.5: Implementiraj `SearchResultsView` / `search_results(request)` za `/pretraga/` full strana (SM-D16) — `request.htmx=False` path; renderuje `search_results.html`
- [x] 4.6: empty-state CTA data — popularne kategorije + brendovi u context (SM-D18)

### Task 5 — Dropdown + empty + results templates (AC6, AC7)
- [x] 5.1: Kreiraj `templates/search/partials/_search_dropdown.html` — `role="listbox"`, grupe (renderuj samo ako ima rezultata — SM-D3), max 5 `role="option"`, „Vidi sve" link, OOB aria-live guarded (SM-D14)
- [x] 5.2: Kreiraj `templates/search/partials/_search_empty.html` — empty poruka + CTA blok (SM-D18) + < 2 znaka varijanta + OOB aria-live
- [x] 5.3: Kreiraj `templates/search/search_results.html` — `{% extends "base.html" %}`, JEDINI `<h1>` „Rezultati pretrage za '{query}'", reuse grouped rendering, single `<main>` (base.html), `data-testid="search-results-page"`; reflected-XSS guard (IMP-5): title+h1 koriste auto-escaped golo `{{ query }}`, href koristi `{{ query|urlencode }}`, NIKAD `|safe`

### Task 6 — Header wiring (EDIT header.html) + JS + CSS (AC5, AC9)
- [x] 6.1: EDIT `templates/partials/header.html` — search button dobija `aria-expanded="false"` + `aria-controls="coric-search-panel"` + `data-search-toggle` (vidi SM-D12 — NE ukloni postojeći `aria-label`/SVG)
- [x] 6.2: DODAJ `<div id="coric-search-panel" class="coric-search-panel" hidden>` mount point sa `<form role="search" hx-get hx-trigger="keyup changed delay:300ms" hx-target="#coric-search-results" hx-indicator>` + `<input type="search" name="q" minlength="2" autocomplete="off">` + dropdown target + loading spinner (SM-D12)
- [x] 6.3: Kreiraj `static/js/search-expand.js` (IIFE) — toggle expand + slide-in, Esc-to-close + focus return, click-outside, keyboard listbox nav, aria-expanded sync, prefers-reduced-motion (AC5+AC9)
- [x] 6.4: Kreiraj `static/css/components/search.css` — `coric-search-*` BEM, slide-in 200ms transform, dropdown/listbox/option/empty stilizovanje, `var(--token)`, `@media prefers-reduced-motion: reduce`
- [x] 6.5: EDIT `static/css/main.css` — dodaj `@import url('./components/search.css');` (mirror Story 2.8 import pattern)
- [x] 6.6: Uključi `<script src="{% static 'js/search-expand.js' %}" defer>` (vidi SM-D12 — u header.html partial ili base.html scripts blok; Dev bira mesto koje garantuje load posle HTMX vendor-a)

### Task 7 — Locale .po edits (sr/hu/en) (AC6, AC7)
- [x] 7.1: `uv run python manage.py makemessages -l sr -l hu -l en` (preko `just messages`)
- [x] 7.2: Popuni sr msgstr za sve nove msgid + 3 plural slot-a za „X predloga" (SM-D19 nplurals=3)
- [x] 7.3: Popuni hu/en msgstr (nplurals=2)
- [x] 7.4: `uv run python manage.py compilemessages` → 0 warninga

### Task 8 — Tests (TEA RED phase piše; Dev NE piše testove)
- [ ] 8.0 (IMP-2, BLOKER — NIJE skipif): TEA dodaje `requires_postgres` pytest marker koji **FAILA (NE skip-uje)** kad PostgreSQL/psycopg nije test DB backend — inače 4 od 8 test fajlova (test_migrations, test_search_query, plus FTS delovi test_views/test_templates) tiho prolaze na SQLite → false green. U `conftest.py` (ili `apps/search/tests/conftest.py`) dodaj fixture sa **tvrdim assertom na DB vendor**: `assert connection.vendor == "postgresql", "FTS testovi zahtevaju PostgreSQL test DB (NE SQLite) — vidi OQ-1/IMP-2"`. Markiraj sve FTS-zavisne testove `@pytest.mark.requires_postgres`. ⛔ NE koristi `@pytest.mark.skipif` (skip = tihi false green). Potvrda: projektna test DB JESTE PostgreSQL per project-context.md (`DJANGO_SETTINGS_MODULE=config.settings.development` → Docker PostgreSQL), pa marker treba da prođe lokalno i u CI; ako ne prođe, to je infra bug koji MORA da pukne glasno.
- [ ] 8.1: `apps/search/tests/test_app_config.py` — AC1 app registracija + postgres u INSTALLED_APPS + URL reverse
- [ ] 8.2: `apps/search/tests/test_migrations.py` — AC2 search_vector field + GIN indeks postoji + 0004a PRE 0004 (`migrate --plan` introspection ili migration dependency assert)
- [ ] 8.3: `apps/search/tests/test_search_query.py` — AC3/AC4/AC8 FTS: diacritic-insensitive OBA smera (IMP-1: „berba"→„Bérba" I „Bérba"→„berba"), case-insensitive, rank name>description, tie-break -created_at, is_published filter, locale isolation (parametrizovano sr/hu/en), region-suffix fallback („sr-latn"→`_sr`, IMP-3), tsquery meta-char safety (IMP-10: query `& | ! : *` vraća 0 redova NE 500), `@pytest.mark.django_db` + `@pytest.mark.requires_postgres` (real PostgreSQL — NE SQLite; Task 8.0/IMP-2)
- [ ] 8.4: `apps/search/tests/test_views.py` — AC3/AC5/AC6/AC7 view: min-2-char guard, query-length cap, grouped dict ima `objave: []`, htmx branching, empty-state, suggestion_count
- [ ] 8.5: `apps/search/tests/test_templates.py` — AC6/AC7 partials: role=listbox/option, max 5 slice, OOB guarded, „Vidi sve" link, empty CTA blok, single h1 na results strani; **reflected XSS na FULL results strani (IMP-5)** — `GET /sr/pretraga/?q=<script>...` → `&lt;script&gt;` u title/h1 + `%3Cscript%3E` u href (NE samo partiale)
- [ ] 8.6: `apps/search/tests/test_header_wiring.py` — AC5 header.html search button ima aria-expanded + aria-controls + data-search-toggle (regression: NE ukloni postojeći aria-label)
- [ ] 8.7: `apps/search/tests/factories.py` — Product factory helper sa translated name/description za search testove

### Task 9 — Sprint status update
- [x] 9.1: Update `_bmad-output/implementation-artifacts/sprint-status.yaml` — `2-13-global-search-sa-postgresql-fts: ready-for-dev`

## SM Decisions

### SM-D1 — Module: NOVI `apps/search/` app (NE products, NE core, NE hipotetički catalog)
**Opcije:** (A) `apps/products/views.py` SearchView; (B) `apps/core/` SearchView; (C) NOVI `apps/search/`; (D) hipotetički `apps/catalog/` iz architecture.md.
**Izbor: (C) NOVI `apps/search/`.**
**Rationale:** Global search je site-wide cross-domain feature — pretražuje `Product` danas i `Post` (Epic 5) sutra. (A) products bi vezao cross-domain search za jedan domen i prekršio forward-compat za Objave. (B) core je ZABRANJENO — `apps/search/views.py` MORA importovati `Product`, a project-context.md § Cross-boundary import eksplicitno zabranjuje „core importuje domain apps". (D) catalog app nikad nije kreiran — stvarna implementacija stavlja listing u products (2.8/2.9), pa catalog je mrtav arhitektonski artefakt. (C) dedikovan search app je čista jednosmerna granica: `search → products` (i `search → brands` za empty-state CTA), spreman da doda `search → blog` u Epic 5. Mirror AR-26 namere (FTS sloj) bez nasleđivanja mrtve catalog strukture.
**arch.md drift napomena (IMP-11b):** Ova story NAMERNO kreira `apps/search/` umesto hipotetičkog `apps/catalog/` iz architecture.md (§ struktura, linije 581-586). `apps/catalog/` NIKADA nije kreiran — listing view-ovi žive u `apps/products/` (Story 2.8/2.9). Budući dev NE treba da traži nepostojeći `catalog` app: search backend je u `apps/search/`, listing u `apps/products/`. (Rationale gore.)

### SM-D2 — `apps.search` POSLE `apps.products` u INSTALLED_APPS; URL include posle products
**Izbor:** `apps.search` registrovan POSLE `apps.products` (i `apps.brands`); `config/urls.py` `include("apps.search.urls")` dodato POSLE products include.
**Rationale:** Jednosmerna zavisnost search → products (mirror PR-D1 brands→products red). URL deconfliction: `pretraga/` + `htmx/pretraga/` su statički path-ovi bez slug-a — ne kolidiraju sa `proizvod/<slug>/`, `traktori/<slug>/`, `traktori/`, `mehanizacija/polovna/`. Pozicija include-a nije kritična (nema prefix overlap), ali konvencija je posle products.

### SM-D3 — Objave (blog) grupa: forward-compatible PRAZAN skelet (NE stub, NE defer)
**Opcije:** (A) stub fake Post model; (B) defer cela story do Epic 5; (C) build sa grouped strukturom gde je `objave` UVEK prisutna ali prazna lista u v1.
**Izbor: (C) forward-compatible prazan skelet.**
**Rationale:** Epic 5 je `backlog` — `apps/blog/`/`Post` ne postoje. (A) krši YAGNI (project-context.md — „nemoj graditi za hipotetičke buduće potrebe"). (B) blokira završetak Epic 2 zbog Epic 5. (C) je sredina: `SearchView` vraća `{"proizvodi": [...], "objave": []}` — `objave` ključ UVEK postoji (forward-compat ugovor), template iterira grupe i renderuje grupu SAMO ako ima rezultata (`{% if group.results %}`) → Objave nevidljiva u v1, ali nula refaktora kad Epic 5 doda Post search (samo popuni `objave` granu u view-u + doda `search_vector` na Post). epics.md AC eksplicitno traži grupisanje „Proizvodi / Objave" — (C) poštuje contract bez fiktivnog modela.
**Forward-compat ugovor za Epic 5:** Epic 5 Story 5.x dodaje (1) `search_vector` na Post (mirror AC2 migracija pattern), (2) `build_post_search_qs()` u `apps/search/search.py`, (3) popunjava `grouped["objave"]` u view-u, (4) dodaje `search → blog` dep u INSTALLED_APPS red. NEMA promene u dropdown template strukturi.

### SM-D4 — Diacritic-insensitive kroz `unaccent` extension (NE app-level normalizacija)
**Izbor:** PostgreSQL `unaccent` extension (CREATE EXTENSION) + Unaccent funkcija/config u upitu.
**Rationale:** epics.md AC eksplicitno traži „diacritic-insensitive (`unaccent` extension)". DB-level unaccent je tačniji i brži od Python-side normalizacije (radi u tsvector/tsquery sloju, ne posle fetch-a). pg_trgm dodatno omogućava similarity/typo-tolerant u v1.1 (nije v1 zahtev, ali extension se kreira sad da migracija ne mora ponovo).

### SM-D5 — FBV za HTMX dropdown endpoint (CBV opciono za results strana)
**Izbor:** `search_dropdown` FBV za HTMX endpoint; `/pretraga/` full strana FBV ili `TemplateView`-style — Dev bira.
**Rationale:** project-context.md § Views — „FBV za jednostavne ili HTMX-specific endpoints". Search dropdown je jednostavan read-only HTMX endpoint sa custom query logikom (min-char guard, length cap, grouped dict) — FBV je čišći od CBV mixin gymnastike. Mirror project-context.md FBV preporuke za HTMX.

### SM-D6 — `django.contrib.postgres` u INSTALLED_APPS
**Izbor:** Dodati `"django.contrib.postgres"` u INSTALLED_APPS.
**Rationale:** `SearchVectorField` + `GinIndex` zahtevaju app registraciju za system check validacije (`postgres.E...` checks). `SearchVector`/`SearchQuery`/`SearchRank` funkcije rade i bez app-a, ali field + indeks NE. Stack je PostgreSQL-only (project-context.md) pa nema cross-db rizika. PRVI put se uvodi — dokumentovano kao Epic 2 closing infra promena.

### SM-D7 — Migration ordering: extension (0004a) PRE AddField/AddIndex (0004)
**Izbor:** Zasebna migracija 0004a (`CREATE EXTENSION unaccent + pg_trgm`) sa `dependencies` na 0003; migracija 0004 (AddField search_vector + AddIndex GIN) ima `dependencies` na 0004a.
**Rationale:** GIN indeks na SearchVectorField i `unaccent()` u upitima zahtevaju da extension VEĆ postoji. Django ne garantuje red osim kroz eksplicitne `dependencies`. Razdvajanje u 2 migracije čini extension idempotentnim (`IF NOT EXISTS`) i reverzibilnim nezavisno od schema promene. project-context.md § Migrations discipline: RunSQL/RunPython sa reverse. Alternativa `django.contrib.postgres.operations.UnaccentExtension()` + `TrigramExtension()` je čistija (Django-native, ima reverse) — Dev preferira to ako radi na lokalnom PG superuser-u; RunSQL fallback ako extension zahteva ručni grant.
**⚠️ Privilegija assumption (IMP-9):** `CREATE EXTENSION` (i `UnaccentExtension`/`TrigramExtension`, koje interno izvršavaju isti SQL) zahtevaju da migration DB rola ima privilegiju za kreiranje extension-a. Na lokalu i standardnom Docker `postgres:16-alpine` default `postgres` rola JESTE superuser → radi out-of-the-box. ALI na managed/restricted PostgreSQL (npr. neki cloud provideri) app rola možda NEMA tu privilegiju → migracija pukne na deploy-u. Pretpostavka: deploy DB rola sme `CREATE EXTENSION`; ako ne — DBA mora ručno `CREATE EXTENSION unaccent; CREATE EXTENSION pg_trgm;` (pre-grant) PRE migrate-a, a `IF NOT EXISTS` guard (već prisutan u RunSQL varijanti) tada čini migraciju no-op umesto greške. Eksplicitno dokumentovano da prod deploy ne pukne tiho.

### SM-D8 — search_vector populacija: SearchVector annotation pri query-time (NE trigger/signal/save)
**Opcije:** (A) DB trigger materializuje tsvector u kolonu; (B) post_save signal; (C) save() override; (D) SearchVector annotation u query-time (vector se NE persistira).
**Izbor: (D) annotation pri query-time; field + GIN indeks postoje ali ostaju `null=True` (nematerijalizovani) u v1.**
**Rationale:** Kolekcija je ~100 proizvoda (architecture.md linija 166) — annotation-at-query-time je trivijalno brz na toj skali, izbegava trigger/signal kompleksnost i „no Celery u v1" duh (sve sync, minimalna infra). (A) trigger je najbrži za velike kolekcije ali overkill + dodaje raw SQL trigger održavanje. (B/C) signal/save populacija dodaje write-path coupling. **Zašto onda field + GIN uopšte?** Forward-compat: ako v1.1 skala traži materijalizovani vector (trigger pristup), field + indeks već postoje — prelazak je samo data migracija koja popuni kolonu + zameni annotation `F("search_vector")`. GIN indeks na nematerijalizovanoj koloni je no-op danas (kolona null) ali nula-košta i sprema teren. **NAPOMENA za TEA/Dev:** annotation gradi SearchVector iz `name_<lang>`/`description_<lang>` u svakom upitu — GIN indeks se NE koristi za to (indeks pokriva kolonu, ne expression). Ovo je svesni v1 trade-off (jednostavnost > mikrooptimizacija na 100 redova). Vidi OQ-3.

**⚠️ KRITIČNI runtime pattern (C3 — „pass-the-AC-build-the-wrong-thing" zamka):** Pošto `search_vector` kolona ostaje **UVEK NULL u v1** (nijedan trigger/signal/save je ne popunjava), upit se MORA graditi kao annotation alias i filtrirati po TOM aliasu — NIKAD po stored `search_vector` koloni. Filtriranje po koloni („izgleda tačno" prema AC2 „field + GIN postoje") prolazi sintaksno ALI vraća **0 rezultata u runtime-u** jer je kolona NULL, a GIN indeks na njoj je no-op (samo forward-compat skelet ka budućem materijalizovanom/trigger pristupu — zato prisustvo field-a NIJE aktivan code path).

**TAČAN pattern (copy-paste; prilagodi tačnim kolonama/weight/config iz SM-D9/SM-D10):**
```python
# KOREKCIJA tokom GREEN protiv Django 5.2.14: Unaccent je u `...lookups`, NE u `...search`
# (`from ...search import Unaccent` baca ImportError).
from django.contrib.postgres.lookups import Unaccent
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.db.models import Value

# Unaccent na OBE strane (IMP-1); Value() obmotava literal query (IMP-8);
# search_type="plain" sprečava tsquery meta-char SyntaxError (IMP-10).
search_query = SearchQuery(Unaccent(Value(query)), config="simple", search_type="plain")
qs = (
    Product.objects.filter(is_published=True)
    .annotate(
        search=SearchVector(Unaccent("name_sr"), weight="A", config="simple")
             + SearchVector(Unaccent("description_sr"), weight="B", config="simple")
    )
    .annotate(rank=SearchRank("search", search_query))
    .filter(search=search_query)
    .order_by("-rank", "-created_at")
)
```
**⛔ NE `Product.objects.filter(search_vector=search_query)` — kolona je UVEK NULL u v1; GIN indeks na njoj je no-op (forward-compat). Filtrira se ISKLJUČIVO po annotation aliasu `search`.** (`name_sr`/`description_sr` su ilustrativni — stvarne kolone su `name_<language_code>`/`description_<language_code>` per SM-D9 locale logika.)

### SM-D9 — Locale-awareness: SearchVector na per-locale kolonama (`name_<lang>`/`description_<lang>`); NE u modeltranslation
**Izbor:** `build_product_search_qs(query, language_code)` bira kolone `name_<language_code>` + `description_<language_code>`; search_vector field NIJE registrovan u translation.py.
**Rationale:** Product već ima materijalizovane translated kolone (`name_sr/_hu/_en`, `description_sr/_hu/_en` — verifikovano translation.py). Locale isolation (epics.md AC „samo trenutni jezik") se postiže biranjem kolona za aktivni `get_language()`. search_vector NIJE translated polje — to bi stvorilo `search_vector_sr/_hu/_en` virtuelne kolone bez svrhe (vector se gradi iz već-translated izvornih kolona). Config (`'serbian'`/`'hungarian'`/`'english'` text search config ILI `'simple'` + unaccent) bira se po locale-u — Dev koristi `'simple'` config + Unaccent kao baseline (sr/hu nemaju ugrađene PG stemmer config-e; `'simple'` + unaccent je bezbedan default). Fallback: locale van LANGUAGES → `_sr` kolone (MODELTRANSLATION_FALLBACK_LANGUAGES=("sr",)).
**Region-suffix normalizacija (IMP-3):** `get_language()` (LocaleMiddleware) može vratiti `"sr-latn"`/`"sr-Latn"` (sa region/script suffiksom), što NIJE modeltranslation ključ (`"sr"`). Pre biranja kolone Dev MORA normalizovati: strip-uj region/script suffiks (npr. `language_code.split("-")[0].lower()`) → `"sr-latn"`/`"sr-Latn"` → `"sr"`. Tek POSLE normalizacije proveri da li je u LANGUAGES; ako i dalje nije → `_sr` fallback. Bez ovog koraka `"sr-latn"` bi promašio i pao na fallback slučajno-tačno za sr, ali bi pao pogrešno za hipotetički `"hu-..."` — eksplicitna normalizacija je SOT.
**Implementacijska napomena (diacritic — IMP-1):** `'simple'` PG config ne radi unaccent sam — Dev MORA obmotati Unaccent na OBE strane upita: `SearchVector(Unaccent("name_sr"), ...)` + `SearchVector(Unaccent("description_sr"), ...)` (kolone) **I** `SearchQuery(Unaccent(Value(query)), config="simple", search_type="plain")` (query argument). Obmotavanje samo jedne strane ostavlja jedan smer diacritic-sensitive (npr. unaccent samo na koloni → „bérba" upit ne nalazi „berba"). Alternativa je `unaccent`-aware custom text search config. **Import (KOREKCIJA tokom GREEN protiv Django 5.2.14): `from django.contrib.postgres.lookups import Unaccent` + `from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank` + `from django.db.models import Value`** (`Unaccent` JESTE u `lookups`, NE u `...search` — `from ...search import Unaccent` baca ImportError; `Value` obmotava literal string — IMP-8). Test (AC3) je arbitar — diacritic-insensitive MORA raditi u OBA smera: „berba" nalazi „Bérba" **I** „Bérba" nalazi „berba".

**Napomena (stemmer — IMP-1 / OQ-5):** `'simple'` config NEMA stemmer. Morfološki upiti („berbu" → „berba", „traktori" → „traktor") NEĆE matchovati u v1 — exact token (case-folded + unaccent) je jedini match path. Ovo je prihvaćen v1 trade-off (dovoljno za ~100 proizvoda). Opciono v1.1 poboljšanje: prefix matching kroz `search_type="websearch"` ili `:*` sufiks u tsquery-ju — **NE mandatorno u v1.**

### SM-D10 — Rangiranje: SearchRank weight A(name)>B(description); tie-break -created_at
**Izbor:** `.annotate(rank=SearchRank(vector, query)).order_by("-rank", "-created_at")`; weight A za name, B za description.
**Rationale:** epics.md AC: „match u name > match u description; tie-break po datumu (po datumu dodavanja za proizvode)". Django SearchVector `weight="A"`/`"B"` + SearchRank default weights `{A:1.0, B:0.4, C:0.2, D:0.1}` daju traženo rangiranje. `-created_at` tie-break = „najnoviji prvi". Blog tie-break (`-published_at`) je Epic 5 (SM-D3 — v1 implementira samo proizvodi).

### SM-D11 — Max 5 po grupi: slice u VIEW-u; suggestion_count PRE slice; thumbnail opciono
**Izbor:** View slice-uje `qs[:5]` ALI računa `suggestion_count = qs.count()` (ili len) PRE slice za tačnu aria-live najavu; product thumbnail u dropdown-u kroz `{% responsive_picture product.main_image %}` (opciono — graceful ako main_image null).
**Rationale:** epics.md AC „max 5 po grupi" + „aria-live najavi 'X predloga'". Ako se slice radi u template-u (`|slice:":5"`), count bi bio max 5 (netačno za „8 predloga, prikazano 5"). View slice + odvojen count daje tačnu najavu. Thumbnail je UX nice-to-have (EXPERIENCE.md ne zahteva eksplicitno) — Dev uključuje ako main_image postoji, fallback bez slike.

### SM-D12 — Header expand panel mount: u header.html partial (NE poseban overlay app)
**Izbor:** Expand panel `<div id="coric-search-panel" hidden>` + `<form hx-get>` + dropdown target živi UNUTAR `templates/partials/header.html` (uz postojeći search-toggle button); `search-expand.js` include u header.html ili base.html scripts blok.
**Rationale:** Story 1.8 IMP-3 ostavio button u header.html bez wiring-a; panel logički pripada uz toggle (aria-controls referencira ga). 1-8 interface-contract linija 1315 preporučuje „Search popup overlay: position: fixed (viewport anchor) ili position: absolute (body anchor)". Story 2.13 koristi `position: absolute`/`fixed` panel anchored uz header — CSS odluka, ne novi template wrapper. Skripta `defer` posle HTMX vendor-a (base.html već učitava HTMX pre `{% block scripts %}`).

### SM-D13 — Min-2-char guard: server-side (NE samo HTML5 minlength)
**Izbor:** `<input minlength="2">` (UX) + server-side guard u view-u (`if len(q.strip()) < 2: return empty-partial sa "Unesi makar 2 znaka."`); HTMX se ipak okida ispod 2 znaka ali server ne izvršava SQL.
**Rationale:** epics.md AC „min 2 znaka pre HTMX request-a". HTML5 `minlength` ne blokira HTMX keyup trigger (validira tek na submit). Server-side guard je SOT (project-context.md § Forms — „Server-side validation kao SOT"). < 2 znaka → „Unesi makar 2 znaka." poruka (EXPERIENCE.md linija 248) bez SQL hita (perf + DoS guard).

### SM-D14 — OOB aria-live guarded `{% if request.htmx %}` (mirror Story 2.8 SM-D23)
**Izbor:** OOB `<div hx-swap-oob="innerHTML:#aria-live">` u `_search_dropdown.html`/`_search_empty.html` WRAPPED u `{% if request.htmx %}`.
**Rationale:** Mirror Story 2.8 SM-D23 — sprečava render OOB div-a kao plain plutajući tekst pri non-HTMX render-u (`/pretraga/` full strana koja include-uje iste partiale). project-context.md § A11y must-haves — sve HTMX swaps announce u `#aria-live` singleton.

### SM-D15 — Debounce 300ms (keyup changed) + min loading 200ms
**Izbor:** `hx-trigger="keyup changed delay:300ms"`; htmx-indicator sa CSS transition min 200ms (mirror Story 2.8 SM-D13).
**Rationale:** epics.md AC + EXPERIENCE.md linija 221 „debounce 300ms". `keyup changed` (NE `input` — search input; `changed` modifier sprečava request ako vrednost nepromenjena, npr. arrow keys). Min loading 200ms sprečava flicker (project-context.md linija 193).

### SM-D16 — „Vidi sve" link ka dedikovanoj `/pretraga/?q=...` full strani
**Izbor:** Dropdown ima „Vidi sve" link po grupi ka `{% url 'search:results' %}?q=...`; `search_results.html` full strana renderuje sve rezultate (bez 5-cap).
**Rationale:** EXPERIENCE.md linija 222 „'Vidi sve' link ka dedikovanoj strani sa rezultatima pretrage". `search:results` je `request.htmx=False` path istog view-a (ili zaseban view) — renderuje full `base.html` stranu. Epic 6 može dodati noindex meta (OQ van scope-a).
**Testid forward-compat (IMP-6 / SM-D3):** „Vidi sve" testid je PER-GRUPA — `data-testid="search-see-all-{{ group_key }}"` (NE hardcoded `search-see-all-proizvodi`). U v1 renderuje se samo `search-see-all-proizvodi`; Epic 5 Objave grupa dobija `search-see-all-objave` bez refaktora test-lock-a („zero refactor" — mirror SM-D3 forward-compat ugovor).

### SM-D17 — GET-only, NEMA CSRF/ratelimit; query-length cap 100 kao DoS guard
**Izbor:** Search forma je `hx-get` (GET); NEMA `{% csrf_token %}`, NEMA `@ratelimit`; query trunkovan na 100 znakova u view-u.
**Rationale:** project-context.md § Forms zahteva CSRF+ratelimit za forme koje PRIMAJU user input koji menja stanje (POST). Search je read-only GET query — CSRF/ratelimit ne primenjuju (GET je idempotentan, nema state mutacije). ALI: pathološki dug query → skup tsquery parse → length cap 100 je lagani DoS guard (truncate, ne 400). Ako Mihas u Step-02 zatraži ratelimit na search (scraper guard), dodaje se `@ratelimit(key='ip', rate='30/m', block=False)` — vidi OQ-4.
**tsquery meta-char / whitespace guard (IMP-10):** Query sa tsquery meta-znacima (`& | ! : *`) ili samo-whitespace može da baci `SyntaxError` sa sirovim `to_tsquery`. Zato `SearchQuery(..., search_type="plain")` (ili `"websearch"`) MORA da se koristi — NE sirov `to_tsquery` — pa se user input tretira kao plain tekst (meta-znaci se tretiraju doslovno, ne kao operatori). Whitespace-only query je već uhvaćen postojećim `.strip()` + min-2-char guard-om (SM-D13) PRE nego što ikad stigne do `build_product_search_qs`.

### SM-D18 — Empty-state CTA: popularne kategorije (Category by display_order) + brendovi (is_coming_soon=False)
**Izbor:** Empty-state CTA blok = top N `Category.objects.order_by("is_for", "display_order")` (linkovi ka `category.get_absolute_url`) + `Brand.objects.filter(is_coming_soon=False).order_by("name")` (linkovi ka `brands:detail`).
**Rationale:** EXPERIENCE.md linija 247 „Lista popularnih kategorija i brendova". Category nema „popularity" metriku u v1 — `display_order` je admin-curated proxy za „popularno". Brendovi filtrirani is_coming_soon=False (mirror Story 2.8 SM-D5 — coming-soon nemaju vidljiv sadržaj). „Popularno" tačno rangiranje (po view count) je Epic 7/analytics scope — v1 koristi display_order.

### SM-D20 — GIN indeks ime: `products_search_gin` (≤30 char direktni GinIndex, NE `_ProductIndex` subclass) [Adversarial fix C1]
**Opcije:** (A) skrati ime na ≤30 char i koristi `GinIndex` direktno; (B) napravi `GinIndex` subclass sa proširenim `max_name_length` (mirror postojećeg `_ProductIndex`).
**Izbor: (A) `products_search_gin` (19 char) preko `GinIndex` direktno.**
**Rationale:** Django `Index.max_name_length = 30` (cross-db Oracle compat). Prethodno predloženo ime `products_product_search_gin` ima **34 char** → prelazi limit → `makemigrations`/`manage.py check` baca `models.E033` (name-too-long). Postojeći `_ProductIndex` (apps/products/models.py:54) JESTE subclass koji proširuje `max_name_length=64` — ALI on nasleđuje `models.Index`, a GIN indeksu treba `django.contrib.postgres.indexes.GinIndex`. Reuse `_ProductIndex` za GIN bi tražio multiple-inheritance gymnastiku (`class _ProductGinIndex(GinIndex): max_name_length=64`) bez stvarne koristi — kratko ime je čistije i prati Django konvenciju za nove indekse. Opcija (B) bi bila opravdana samo da je traženo semantičko ime > 30 char neophodno; `products_search_gin` je dovoljno opisno na 19 char. **Autoritativno ime svuda (AC2, Task 2.1, interface-contract §2/§3): `products_search_gin`.** `_ProductIndex` ostaje load-bearing za 6 postojećih `<table>_<columns>_idx` indeksa (NE diramo ga).

## Open Questions

- **OQ-1 — Test DB engine za FTS testove [REŠENO → Task 8.0, IMP-2]:** PostgreSQL FTS (`SearchVector`/`unaccent`/GIN) NE radi na SQLite. project-context.md § Database tests kaže „NIKAD mock Django ORM ili PostgreSQL — koristi real test DB" + `just test` koristi `DJANGO_SETTINGS_MODULE=config.settings.development` (PostgreSQL preko Docker compose) — **dakle projektna test DB JESTE PostgreSQL** (potvrđeno). Ovo VIŠE NIJE open question: promovisano u hard Task 8.0 — TEA dodaje `requires_postgres` marker sa tvrdim DB-vendor assertom u conftest koji **FAILA (NE skip-uje)** ako backend nije psycopg/PostgreSQL. ⛔ `@pytest.mark.skipif` se NE koristi (skip = tihi false green za 4 od 8 test fajlova). Marker treba da prođe na svakom okruženju koje prati project-context.md; glasan fail = infra drift signal.
- **OQ-2 — SearchRank weight tuning:** architecture.md linija 952-953 eksplicitno: „konkretni weight-evi (title vs body, recency tie-break) treba tune-ovati posle sample podataka". v1 koristi Django default weights (A:1.0, B:0.4). Da li Mihas želi custom weights (npr. A:1.0, B:0.2 da name dominira jače)? Defer do Story 9.7 sample seed data + manual relevance smoke. **Defer — default weights u v1.**
- **OQ-3 — Materijalizovani search_vector u v1.1:** SM-D8 bira annotation-at-query-time (field nematerijalizovan). Ako post-launch analytics pokaže da je 100 → 500+ proizvoda, prelazak na trigger-populated vector je v1.1 tech debt. **Defer — nematerijalizovan u v1; field+GIN spremni za upgrade.**
- **OQ-4 — Ratelimit na search:** SM-D17 ne dodaje ratelimit (GET read-only). Scraper koji hammeruje `/htmx/pretraga/` mogao bi opteretiti DB. Da li dodati `@ratelimit(rate='30/m', block=False)` (soft, non-blocking)? **Defer do Step-02 / Mihas odluka — baseline bez ratelimit.**
- **OQ-5 — PG text search config za sr/hu:** SM-D9 bira `'simple'` config + Unaccent (sr/hu nemaju ugrađene PostgreSQL stemmer config-e; en ima `'english'`). Stemming (npr. „traktori" → „traktor") NE radi sa `'simple'`. Da li je za sr potreban custom stemmer config (npr. snowball serbian)? v1 prihvata no-stemming (exact token + unaccent + prefix match je dovoljno za ~100 proizvoda). **Defer — `'simple'` + unaccent u v1; custom stemmer je v1.1 ako relevance pati.**

## Reference

- [epics.md](../planning-artifacts/epics.md) — Story 2.13 (linije 691-706), FR-27 (linija 76), AR-26 (linija 172), UX-DR-15 (linija 221), UX-DR-26 (linija 235), UX-DR-30 (linija 242)
- [architecture.md](../planning-artifacts/architecture.md) — § Search backend (linija 166 PostgreSQL FTS), § struktura catalog/search.py (linije 581-586), § Data boundaries (linija 744 raw SQL samo u FTS), § Open questions (linije 952-953 weight tuning)
- [EXPERIENCE.md](../planning-artifacts/ux-designs/ux-CORIC_AGRAR-2026-05-27/EXPERIENCE.md) — § Search (linije 219-224), § HTMX/aria-live (linije 186-195), § Empty states (linije 242-250 — search 0 rezultata + < 2 znaka)
- [project-context.md](../project-context.md) — § HTMX response patterns, § Migrations discipline, § Cross-boundary import (core ne sme importovati domain apps), § A11y must-haves, § Testing (real PostgreSQL, i18n parametrizacija)
- [2-2-product-i-related-modeli.md](2-2-product-i-related-modeli.md) — Product model (search_vector deferral note linija 21), _ProductIndex subclass
- [2-8-tractor-listing-strana-sa-htmx-filterima.md](2-8-tractor-listing-strana-sa-htmx-filterima.md) — kanonski HTMX pattern (request.htmx branching, OOB aria-live SM-D23, debounce, empty-state)
- [1-8-sticky-nav-top-header-footer-language-switcher-partial.md](1-8-sticky-nav-top-header-footer-language-switcher-partial.md) — header search-toggle button (IMP-3 deferral; linija 1315 popup overlay preporuka)
