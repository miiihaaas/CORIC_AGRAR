---
story-id: "2.13"
story-key: 2-13-global-search-sa-postgresql-fts
artifact: interface-contract
created: 2026-05-31
author: SM / Mihas (autonomous)
purpose: Canonical contract for Global Search sa PostgreSQL FTS — NOVI apps/search/ app,
         search_vector SearchVectorField + GIN indeks na products.Product, 2 extension+schema
         migracije, SearchView/search_dropdown FBV, FTS query helper, header wiring,
         3 templates + search.css + search-expand.js, locale .po edits. Dev MORA satisfy
         svaku klauzulu u GREEN phase. ZAVRŠAVA Epic 2; reuse Story 2.8 HTMX pattern;
         wire-uje Story 1.8 deferred search-toggle button.
---

# Interface Contract — Story 2.13 Global Search sa PostgreSQL FTS

Story 2.13 kreira NOVI `apps/search/` app (SM-D1), dodaje `search_vector` SearchVectorField +
GIN indeks na `products.Product` (SM-D8) kroz 2 migracije (0004a extension + 0004 schema, SM-D7),
implementira `search_dropdown` FBV + FTS query helper (locale-aware, unaccent diacritic-insensitive,
SearchRank), wire-uje header search-toggle button (Story 1.8 deferred IMP-3), i renderuje dropdown
grupisan po tipu (Proizvodi / Objave — `objave` PRAZAN forward-compat skelet, SM-D3) sa OOB aria-live,
empty-state, Esc-to-close + focus return.

Ovaj ugovor enumerise file-system delta + Python surface + migration surface + template +
DOM/data-testid surface + CSS klase + JS module surface + locale .po koje TEA RED-phase testovi
verifikuju. Dev GREEN-phase realizuje sve klauzule; bilo koje odstupanje vraća story u `paused`.

---

## 1. File-system delta

### Fajlovi koji MORAJU postojati posle GREEN phase (10 NOVO + 2 migracije + 8 EDIT, 0 DELETE)

| Path | Status | Vlasništvo |
|---|---|---|
| `apps/search/__init__.py` | NOVO (Dev) | Prazan package marker |
| `apps/search/apps.py` | NOVO (Dev) | `SearchConfig(AppConfig)` name="apps.search" |
| `apps/search/views.py` | NOVO (Dev) | `search_dropdown` FBV + `search_results`/`SearchResultsView` + grouped dict |
| `apps/search/urls.py` | NOVO (Dev) | app_name="search"; `dropdown` (htmx) + `results` (full) paths |
| `apps/search/search.py` | NOVO (Dev) | `build_product_search_qs(query, language_code)` FTS helper |
| `templates/search/partials/_search_dropdown.html` | NOVO (Dev) | listbox grupisani rezultati + „Vidi sve" + OOB aria-live |
| `templates/search/partials/_search_empty.html` | NOVO (Dev) | empty-state + < 2 znaka + CTA blok |
| `templates/search/search_results.html` | NOVO (Dev) | „Vidi sve" full strana (extends base.html) |
| `static/css/components/search.css` | NOVO (Dev) | coric-search-* BEM, slide-in, dropdown, empty |
| `static/js/search-expand.js` | NOVO (Dev) | IIFE — expand toggle, Esc, focus return, listbox nav |
| `apps/products/migrations/0004a_enable_search_extensions.py` | NOVO migracija (Dev) | CREATE EXTENSION unaccent + pg_trgm (reverse DROP) |
| `apps/products/migrations/0004_product_search_vector.py` | NOVO migracija (Dev) | AddField search_vector + AddIndex GIN; deps na 0004a |
| `apps/products/models.py` | EDIT (Dev) | ADD search_vector SearchVectorField + GinIndex u Meta |
| `templates/partials/header.html` | EDIT (Dev) | search button aria-expanded/aria-controls/data-search-toggle + panel mount |
| `config/settings/base.py` | EDIT (Dev) | ADD "django.contrib.postgres" + "apps.search" u INSTALLED_APPS |
| `config/urls.py` | EDIT (Dev) | ADD include("apps.search.urls") |
| `static/css/main.css` | EDIT (Dev) | +1 @import search.css |
| `locale/sr/LC_MESSAGES/django.po` | EDIT (Dev) | sr msgstr + 3 plural slot-a |
| `locale/hu/LC_MESSAGES/django.po` | EDIT (Dev) | hu prevodi (nplurals=2) |
| `locale/en/LC_MESSAGES/django.po` | EDIT (Dev) | en prevodi (nplurals=2) |
| `apps/search/tests/__init__.py` | NOVO (TEA) | tests package |
| `apps/search/tests/factories.py` | NOVO (TEA) | Product factory sa translated name/description |
| `apps/search/tests/test_app_config.py` | NOVO (TEA) | AC1 |
| `apps/search/tests/test_migrations.py` | NOVO (TEA) | AC2 field+GIN+ordering |
| `apps/search/tests/test_search_query.py` | NOVO (TEA) | AC3/AC4/AC8 FTS (`requires_postgres` marker — Task 8.0/IMP-2) |
| `apps/search/tests/test_views.py` | NOVO (TEA) | AC3/AC5/AC6/AC7 |
| `apps/search/tests/test_templates.py` | NOVO (TEA) | AC6/AC7 |
| `apps/search/tests/test_header_wiring.py` | NOVO (TEA) | AC5 |

**Kanonsko brojanje (AUTORITATIVNO — ovaj dokument je izvor istine, IMP-7):** 10 NOVO (5 app: `__init__`, apps, views, urls, search.py + 3 template + 2 static) + 2 migracije (0004a + 0004) + 8 EDIT (`apps/products/models.py`, `templates/partials/header.html`, `config/settings/base.py`, `config/urls.py`, `static/css/main.css` = 5, + 3 .po = 8) + 0 DELETE. **Kanonsko: 10 NOVO + 2 migracije + 8 EDIT (uklj. 3 .po + main.css).** (`_bmad-output/.../sprint-status.yaml` je rutinski tracking update — NE računa se u code delta. TEA test fajlovi su zasebni red ispod — nisu deo NOVO/EDIT code-delta brojanja.)

**NETAKNUTI (regression guards):** `apps/products/views.py`, `apps/products/urls.py`, `apps/products/translation.py`, `apps/products/admin.py`, `apps/brands/*`, `apps/core/*`, `apps/media_pipeline/*`, `templates/base.html`, `templates/products/*`, `templates/brands/*`, `static/css/tokens.css`, postojeći `static/css/components/*` (osim NOVE search.css), `static/vendor/*`.

---

## 2. Python surface

### `apps/search/apps.py` (NOVO)

```python
from django.apps import AppConfig


class SearchConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.search"
```

### `apps/products/models.py` (EDIT — ADD field + indeks)

```python
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField

# u class Product:
search_vector = SearchVectorField(_("Search vektor"), null=True, editable=False)

# u Product.Meta.indexes (dodatak postojećim _ProductIndex):
GinIndex(fields=["search_vector"], name="products_search_gin")
```

- **Autoritativno ime indeksa: `products_search_gin` (19 char)** — ≤ Django `Index.max_name_length = 30`. NE `products_product_search_gin` (34 char → models.E033 name-too-long pri `makemigrations`/`check`). NE koristi se `_ProductIndex` subclass (on je `models.Index`, ne `GinIndex`) — `GinIndex` se koristi direktno sa kratkim imenom (Django konvencija). Vidi story SM-D20 C1.
- `null=True` (SM-D8 — nematerijalizovan u v1, annotation-at-query-time), `editable=False` (ne u admin formi)
- **search_vector kolona ostaje UVEK NULL u v1** (nema trigger/signal/save populacije); GIN indeks na njoj je no-op (forward-compat). Runtime upit filtrira ISKLJUČIVO po annotation aliasu — NE po `search_vector` koloni (vidi § 3 search.py + SM-D8)
- search_vector NIJE u `translation.py` (SM-D9)

### `apps/search/search.py` (NOVO)

**Import (C2 — KOREKCIJA tokom GREEN protiv Django 5.2.14: `Unaccent` živi u `django.contrib.postgres.lookups`, NE u `...search` — `from ...search import Unaccent` baca ImportError; `SearchVector`/`SearchQuery`/`SearchRank` ostaju u `...search`; `Value` iz `django.db.models` obmotava literal string argument — IMP-8):**
```python
from django.contrib.postgres.lookups import Unaccent
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.db.models import Value
```

```python
def build_product_search_qs(query: str, language_code: str) -> "QuerySet[Product]":
    """FTS upit nad Product — locale-aware kolone, unaccent diacritic-insensitive, ranked.

    - kolone: name_<language_code> (weight A) + description_<language_code> (weight B)
    - region-suffix normalizacija (IMP-3): "sr-latn"/"sr-Latn" -> split("-")[0].lower() -> "sr" PRE biranja kolone
    - language_code van LANGUAGES (posle normalizacije) → fallback "sr" (MODELTRANSLATION_FALLBACK_LANGUAGES)
    - diacritic-insensitive kroz Unaccent obmotavanje ili unaccent text search config
    - vektor se gradi kao ANNOTATION ALIAS i filtrira se po aliasu — NE po search_vector koloni (C3/SM-D8)
    - .filter(is_published=True)
    - .annotate(search=...).annotate(rank=SearchRank("search", q)).filter(search=q).order_by("-rank", "-created_at")  # SM-D10
    """
```

**TAČAN pattern (C3 — copy-paste; kolone/weight/config per SM-D9/SM-D10):**
```python
# IMP-1: Unaccent se primenjuje na OBE strane — i SearchVector kolone (name/description)
#        i SearchQuery argument — inače diacritic-insensitive radi samo u jednom smeru.
# IMP-8: literal query string se obmotava u Value(...) (Django idiom za literal argument).
# IMP-10: search_type="plain" tretira user input kao plain tekst — NE raw to_tsquery —
#         pa tsquery meta-znaci (& | ! : *) NE bacaju SyntaxError.
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
**⛔ NE `.filter(search_vector=search_query)` — `search_vector` kolona je UVEK NULL u v1; GIN indeks na njoj je no-op (forward-compat). Filtrira se ISKLJUČIVO po annotation aliasu `search`** (`name_sr`/`description_sr` ilustrativni — stvarne kolone su `name_<language_code>`/`description_<language_code>` per SM-D9).

Implementacijske napomene:
- config baseline `'simple'` + Unaccent (sr/hu nemaju PG stemmer config; en `'english'` opciono) — SM-D9 / OQ-5
- **Unaccent MORA obmotati i kolone i query argument (IMP-1)** — `Unaccent("name_sr")` u SearchVector-u + `Unaccent(Value(query))` u SearchQuery-ju. Jednosmerno (npr. samo na koloni) ostavlja jedan smer diacritic-sensitive.
- **`search_type="plain"` je OBAVEZAN (IMP-10)** — sprečava `SyntaxError` na tsquery meta-znacima (`& | ! : *`); whitespace-only query je već uhvaćen `.strip()` + min-2-char guard-om (SM-D13) pre nego što dospe ovde.
- **`'simple'` config NEMA stemmer (IMP-1 / OQ-5)** — morfološki upiti („berbu" → „berba", „traktori" → „traktor") NEĆE matchovati u v1. Ovo je svestan v1 trade-off (exact token + unaccent dovoljan za ~100 proizvoda). Prefix matching (`search_type="websearch"` ili `:*` u upitu) je moguće v1.1 poboljšanje — NE mandatorno u v1.
- vraća annotated QuerySet (NE slice — view radi slice + count, SM-D11)

### `apps/search/views.py` (NOVO)

```python
from django.utils.translation import get_language

_MIN_QUERY_LEN = 2          # SM-D13
_MAX_QUERY_LEN = 100        # SM-D17
_PER_GROUP = 5              # SM-D11


def search_dropdown(request):
    """HTMX dropdown endpoint — grouped FTS rezultati + OOB aria-live.

    - q = request.GET.get("q", "").strip()[:_MAX_QUERY_LEN]   # SM-D17 cap
    - if len(q) < _MIN_QUERY_LEN: render _search_empty.html ("Unesi makar 2 znaka")  # SM-D13
    - qs = build_product_search_qs(q, get_language())
    - suggestion_count = qs.count()                            # PRE slice — SM-D11
    - grouped = {"proizvodi": list(qs[:_PER_GROUP]), "objave": []}  # SM-D3 forward-compat
    - if suggestion_count == 0: render _search_empty.html (sa CTA blok — SM-D18)
    - else: render _search_dropdown.html
    """
```

- `objave` ključ UVEK prisutan, UVEK `[]` u v1 (SM-D3); view NE query-uje Post (model ne postoji)
- `request.htmx` branching: dropdown/empty partial (htmx) vs full strana (non-htmx /pretraga/)
- empty-state CTA context (SM-D18): `popular_categories` (Category by display_order), `header_brands` (Brand is_coming_soon=False)

### `apps/search/urls.py` (NOVO)

```python
app_name = "search"
urlpatterns = [
    path("htmx/pretraga/", views.search_dropdown, name="dropdown"),
    path("pretraga/", views.search_results, name="results"),  # ili SearchResultsView.as_view()
]
```

URL deconfliction (SM-D2): `htmx/pretraga/` + `pretraga/` su statički bez slug-a — ne kolidiraju sa postojećim products/brands pattern-ima. Include POSLE products u config/urls.py.

### `config/settings/base.py` (EDIT)

```python
INSTALLED_APPS = [
    # ... django.contrib.* ...
    "django.contrib.postgres",   # NOVO Story 2.13 — SearchVectorField + GinIndex (SM-D6)
    # ...
    "apps.products",
    "apps.search",               # NOVO Story 2.13 — POSLE products (SM-D2)
    "apps.media_pipeline",
]
```

### Context surface (search_dropdown)

| Key | Tip | Opis |
|---|---|---|
| `query` | str | sanitized q (stripped, capped 100) |
| `grouped` | dict | `{"proizvodi": list[Product], "objave": []}` (SM-D3) |
| `suggestion_count` | int | total PRE slice (aria-live count — SM-D11) |
| `too_short` | bool | True ako < 2 znaka (SM-D13 — empty template render-uje „Unesi makar 2 znaka") |
| `popular_categories` | QuerySet[Category] | empty-state CTA (SM-D18) — samo kad 0 rezultata |
| `header_brands` | QuerySet[Brand] | empty-state CTA is_coming_soon=False (SM-D18) |

---

## 3. Migration surface (SM-D7)

### `0004a_enable_search_extensions.py` (NOVO — extension)

```python
from django.contrib.postgres.operations import TrigramExtension, UnaccentExtension
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("products", "0003_alter_productvariant_description_and_more")]
    operations = [UnaccentExtension(), TrigramExtension()]
```

Alternativa (ako PG operations zahtevaju superuser grant problem): `migrations.RunSQL("CREATE EXTENSION IF NOT EXISTS unaccent;", reverse_sql="DROP EXTENSION IF EXISTS unaccent;")` + isto za pg_trgm.

**⚠️ Privilegija assumption (IMP-9):** `CREATE EXTENSION` / `UnaccentExtension` / `TrigramExtension` zahtevaju da migration DB rola sme da kreira extension. Lokal + standardni Docker `postgres:16-alpine` (`postgres` superuser) → radi. Managed/restricted PG → app rola možda nema privilegiju; tada DBA ručno `CREATE EXTENSION` pre-grant PRE migrate-a, a `IF NOT EXISTS` guard čini migraciju no-op (ne greška). Dokumentovano da prod deploy ne pukne tiho.

### `0004_product_search_vector.py` (NOVO — schema)

```python
class Migration(migrations.Migration):
    dependencies = [("products", "0004a_enable_search_extensions")]
    operations = [
        migrations.AddField(model_name="product", name="search_vector",
                            field=SearchVectorField(null=True, editable=False, verbose_name="Search vektor")),
        migrations.AddIndex(model_name="product",
                            index=GinIndex(fields=["search_vector"], name="products_search_gin")),
    ]
```

- `migrate --plan` MORA prikazati 0004a PRE 0004
- oba reverzibilna; manual review obavezan

---

## 4. Template surface

### `templates/partials/header.html` (EDIT)

Postojeći button (Story 1.8) — DODAJ atribute (NE ukloni `aria-label`/SVG):
```django
<button type="button"
        class="coric-nav__search-toggle"
        data-search-toggle
        aria-expanded="false"
        aria-controls="coric-search-panel"
        aria-label="{% translate "Otvori pretragu" %}">
  {# postojeći SVG netaknut #}
</button>
```
DODAJ panel mount (uz button, unutar nav-a — SM-D12):
```django
<div id="coric-search-panel" class="coric-search-panel" hidden>
  <form role="search"
        hx-get="{% url 'search:dropdown' %}"
        hx-trigger="keyup changed delay:300ms"
        hx-target="#coric-search-results"
        hx-swap="innerHTML"
        hx-indicator="#coric-search-loading"
        class="coric-search-panel__form">
    <input type="search" name="q" minlength="2" autocomplete="off"
           class="coric-search-panel__input"
           aria-label="{% translate "Pretraga" %}"
           placeholder="{% translate "Pretraži proizvode…" %}"
           data-search-input>
    <div id="coric-search-loading" class="coric-search-panel__loading htmx-indicator" aria-hidden="true">
      <span class="spinner-border spinner-border-sm" role="status">
        <span class="visually-hidden">{% translate "Pretraga u toku…" %}</span>
      </span>
    </div>
    <div id="coric-search-results" class="coric-search-panel__results" data-testid="search-results-container"></div>
  </form>
</div>
```
NEMA `{% csrf_token %}` (GET — SM-D17). `search-expand.js` include `defer` (header.html bottom ili base.html scripts blok — posle HTMX vendor).

### `templates/search/partials/_search_dropdown.html` (NOVO)

- `{% load i18n media_tags %}`
- `<div id="coric-search-results">` je HTMX target (INVARIJANTAN — header `hx-target`); ovaj partial renderuje SADRŽAJ unutar njega
- `<ul class="coric-search-dropdown__list" role="listbox" aria-label="{% translate 'Predlozi pretrage' %}" data-testid="search-dropdown-list">`
- iteracija grupe (`proizvodi`, `objave`) — render grupu SAMO ako ima rezultata (`{% if grouped.proizvodi %}` … Objave grupa `{% if grouped.objave %}` → nevidljiva u v1, SM-D3)
- per grupa: `<li role="presentation" class="coric-search-dropdown__group-heading">{% translate "Proizvodi" %}</li>` + max 5 `<li role="option" class="coric-search-dropdown__option" id="search-opt-{{ product.slug }}" data-testid="search-option-{{ product.slug }}">` koji wrap `<a href="{{ product.get_absolute_url }}">` (opciono `{% responsive_picture product.main_image %}` thumbnail — SM-D11) + naziv + brand
- „Vidi sve" link po grupi: `<a href="{% url 'search:results' %}?q={{ query|urlencode }}" class="coric-search-dropdown__see-all" data-testid="search-see-all-{{ group_key }}">{% translate "Vidi sve" %}</a>` (SM-D16) — **testid je per-grupa (IMP-6/SM-D3 forward-compat):** `group_key` je iteracijski ključ (`proizvodi`, kasnije `objave`) pa Epic 5 dodaje Objave grupu BEZ refaktora ovog test-lock-a („zero refactor"). U v1 renderuje se samo `search-see-all-proizvodi`; `search-see-all-objave` je forward-compat (nevidljiv dok blog ne postoji)
- OOB aria-live (guarded SM-D14):
  ```django
  {% if request.htmx %}
    <div hx-swap-oob="innerHTML:#aria-live">
      {% blocktranslate count counter=suggestion_count %}{{ counter }} predlog.{% plural %}{{ counter }} predloga.{% endblocktranslate %}
    </div>
  {% endif %}
  ```
- NEMA inline style; NEMA ćirilice; NEMA šišane latinice

### `templates/search/partials/_search_empty.html` (NOVO)

- `{% load i18n %}`
- `<div class="coric-search-empty" data-testid="search-empty-state">`
- `{% if too_short %}` → `<p class="coric-search-empty__hint">{% translate "Unesi makar 2 znaka." %}</p>` (BEZ CTA — EXPERIENCE.md linija 248)
- `{% else %}` → `<p class="coric-search-empty__message">{% blocktranslate %}Nema rezultata za „{{ query }}".{% endblocktranslate %}</p>` + CTA blok (SM-D18):
  - `<div class="coric-search-empty__cta">` sa `popular_categories` (linkovi `category.get_absolute_url`) + `header_brands` (linkovi `brands:detail`)
- OOB aria-live guarded (SM-D14) — DVE RAZLIČITE poruke (IMP-4):
  - `{% if too_short %}` → NON-plural string `{% translate "Unesi makar 2 znaka." %}` (NIJE count/plural — to je fiksna instrukcija, NE „{n} predloga")
  - `{% else %}` (0 rezultata, ≥2 znaka) → plural `{% blocktranslate count counter=suggestion_count %}{{ counter }} predlog.{% plural %}{{ counter }} predloga.{% endblocktranslate %}` (counter=0 → „0 predloga.")
  - dakle too_short koristi zaseban non-plural msgid; rezultat slučaj koristi isti plural msgid kao `_search_dropdown.html`
- `{{ query }}` auto-escaped (Django default — XSS guard, AC7)

### `templates/search/search_results.html` (NOVO — „Vidi sve" full strana, SM-D16)

- `{% extends "base.html" %}` + `{% load i18n media_tags %}`
- `{% block title %}{% blocktranslate %}Rezultati pretrage za „{{ query }}"{% endblocktranslate %} | Ćorić Agrar{% endblock %}`
- `{% block content %}` outer `<section data-testid="search-results-page">` (NIJE drugi `<main>`)
- JEDINI `<h1>` „Rezultati pretrage za „{{ query }}"" (single-h1 + single-main regression guard mirror Story 2.8 AC3)
- reuse grouped rendering (bez 5-cap — full lista); empty-state ako 0
- NEMA OOB aria-live (non-HTMX full render — guarded `{% if request.htmx %}` u partial-u to već handluje)
- **Reflected XSS guard (IMP-5):** full strana echo-uje `{{ query }}` na više mesta — `{% block title %}`, `<h1>`, i eventualni „Vidi sve"/refine href (`?q={{ query|urlencode }}`). PRAVILO: u title i h1 koristi golo `{{ query }}` (Django auto-escape ON — `<script>` → `&lt;script&gt;`); u svakom HREF/URL kontekstu koristi `{{ query|urlencode }}` (NE golo). NIKAD `|safe` na query. Reflected-XSS test (IMP-5) MORA pokriti FULL stranu (`search_results.html`), ne samo partiale: `GET /sr/pretraga/?q=<script>alert(1)</script>` → response NE sme sadržati neeskejpovan `<script>` (asert `&lt;script&gt;` u title+h1, i `%3Cscript%3E` u href).

---

## 5. JavaScript surface (`static/js/search-expand.js`)

IIFE + `'use strict';` (mirror Story 2.6/2.8 module konvencija).

Public DOM contract:
- `[data-search-toggle]` — header button (toggle trigger)
- `#coric-search-panel` — expand panel (`hidden` attribute toggle)
- `[data-search-input]` — search input (focus target on open)
- `#coric-search-results` — dropdown results (listbox parent za keyboard nav)

Required behaviors (AC5 + AC9):
- klik na `[data-search-toggle]` → toggle `panel.hidden` + sync `aria-expanded` + on-open fokus na `[data-search-input]`; slide-in 200ms (CSS transform; `prefers-reduced-motion: reduce` → instant)
- **Esc** (keydown) kad panel otvoren → close + fokus return na `[data-search-toggle]`
- **klik van** (document click, target van panela i toggle-a) → close
- **ArrowDown/ArrowUp** kad dropdown ima `role="option"` → roving `aria-selected`; **Enter** → navigira na selektovan option href
- `aria-expanded` UVEK sinhronizovan sa panel visibility
- respektuje `window.matchMedia('(prefers-reduced-motion: reduce)')` — no transform transition

NAPOMENA: JS-runtime ponašanje (Esc, focus, listbox nav, slide-in) je manual smoke / Playwright Story 9.8 — NE pytest (vidi § 9 Out-of-scope).

---

## 6. CSS surface (`static/css/components/search.css`)

BEM `coric-search-*` prefiks; `var(--token)` (NE hex/px); `@media (prefers-reduced-motion: reduce)` blok.

Selektori:
- `.coric-search-panel` + `__form`, `__input`, `__loading`, `__results` (slide-in transform 200ms; `[hidden]` → display none)
- `.coric-search-dropdown__list`, `__group-heading`, `__option`, `__option--selected` (aria-selected styling), `__see-all`
- `.coric-search-empty` + `__hint`, `__message`, `__cta`
- `.htmx-indicator` (opacity 0 default; `.htmx-request .htmx-indicator { opacity:1 }` + transition 200ms — SM-D15 min loading)
- NE re-definisati `coric-nav__search-toggle` (Story 1.8 owner — header.css)

`static/css/main.css` EDIT: +1 `@import url('./components/search.css');`.

---

## 7. data-testid contract

Testovi assert na ovim selektorima — Dev NE SME ih menjati:

| testid | Element | Lokacija |
|---|---|---|
| `search-results-container` | `<div id="coric-search-results">` HTMX target | `header.html` |
| `search-dropdown-list` | `<ul role="listbox">` | `_search_dropdown.html` |
| `search-option-{slug}` | `<li role="option">` per product | `_search_dropdown.html` |
| `search-see-all-{group}` | „Vidi sve" link po grupi (v1: `search-see-all-proizvodi`; Epic 5: `search-see-all-objave` bez refaktora — IMP-6/SM-D3) | `_search_dropdown.html` |
| `search-empty-state` | `<div>` empty wrapper | `_search_empty.html` |
| `search-results-page` | `<section>` full strana | `search_results.html` |

Header button selektor: `[data-search-toggle]` (NE testid — atribut je JS hook + test hook).

---

## 8. Locale .po edits (sr/hu/en)

Novi msgid (svi pokriveni `{% translate %}`/`{% blocktranslate %}`):

```
Otvori pretragu                         (već postoji iz Story 1.8 — NE dupliraj)
Pretraga
Pretraži proizvode…
Pretraga u toku…
Predlozi pretrage
Proizvodi
Objave
Vidi sve
Unesi makar 2 znaka.
Nema rezultata za „%(query)s".          (blocktranslate)
Rezultati pretrage za „%(query)s"       (blocktranslate — results strana h1 + title)
Popularne kategorije                    (empty CTA heading — opciono)
Popularni brendovi                      (empty CTA heading — opciono)
```

sr nplurals=3 plural (SM-D19 — placeholder `%(counter)s`):

```po
msgid "%(counter)s predlog."
msgid_plural "%(counter)s predloga."
msgstr[0] "%(counter)s predlog."
msgstr[1] "%(counter)s predloga."
msgstr[2] "%(counter)s predloga."
```

hu/en nplurals=2: `msgstr[0]` + `msgstr[1]`. `just compilemessages` MORA emit 0 warninga.

**NAPOMENA (IMP-4 — too_short je NON-plural, zaseban od plural „X predloga"):** `Unesi makar 2 znaka.` je obična `msgid` (NEMA `msgid_plural`) — to je fiksna instrukcija za aria-live too_short slučaj, NE count string. Plural blok (`%(counter)s predlog./predloga.`) pokriva SAMO rezultat/0-rezultata slučaj. Dva odvojena msgid-a: (1) non-plural `Unesi makar 2 znaka.` (jedan `msgstr`), (2) plural `%(counter)s predlog.` sa `msgstr[0..n]`. NE spajati ih u jedan plural — too_short nema brojač.

---

## 9. Out-of-scope (NE TEA, NE Dev u ovoj story)

- Objave (blog) search rezultati — Epic 5 Story 5.x popunjava `objave` granu (SM-D3 forward-compat)
- JS-runtime ponašanje (Esc, focus return, listbox keyboard nav, slide-in animacija) — manual smoke + Playwright Story 9.8
- NVDA screen-reader voice transcript — manual AC9 + Story 9.9
- SearchRank weight tuning — OQ-2 (default weights u v1)
- Materijalizovani search_vector (trigger) — OQ-3 (v1.1)
- Custom sr/hu PG stemmer config — OQ-5 (`'simple'` + unaccent u v1)
- Ratelimit na search endpoint — OQ-4 (baseline bez)
- `/pretraga/` strana SEO meta (noindex/canonical) — Epic 6
- Lighthouse a11y skor — manual AC9 + Story 9.9 audit gate

---

## 10. Adversarial / risk fixes (mirror story SM decisions)

| Fix ID | SM-D | Tema | Test coverage |
|---|---|---|---|
| MIG-ORDER | SM-D7 | Extension migracija PRE AddField/AddIndex | `test_migrations.py` (dependency assert + migrate --plan order) |
| OOB-GUARD | SM-D14 | OOB div guarded `{% if request.htmx %}` | `test_templates.py::test_oob_only_on_htmx` |
| MIN-CHAR | SM-D13 | Server-side 2-char guard (NE samo HTML5) | `test_views.py::test_short_query_no_sql` |
| LEN-CAP | SM-D17 | Query trunkovan 100 (DoS guard) | `test_views.py::test_long_query_truncated` |
| LOCALE-ISO | SM-D9 | Locale isolation (hu term ne nalazi na sr) | `test_search_query.py::test_locale_isolation` (parametrized sr/hu/en) |
| LOCALE-SUFFIX | SM-D9/IMP-3 | `"sr-latn"` region-suffix normalizuje na `_sr` kolone (NE slepi fallback) | `test_search_query.py::test_locale_region_suffix_fallback` (param `"sr-latn"` → `_sr`) |
| DIACRITIC | SM-D4/D9 | „berba" nalazi „Bérba" (unaccent) | `test_search_query.py::test_diacritic_insensitive` |
| RANK | SM-D10 | name(A) > description(B); tie-break -created_at | `test_search_query.py::test_rank_and_tiebreak` |
| FWD-OBJAVE | SM-D3 | grouped dict UVEK ima `objave: []` | `test_views.py::test_grouped_has_empty_objave` |
| ANNOT-NOT-COL | SM-D8/C3 | Runtime filtrira po annotation aliasu `search`, NE po NULL `search_vector` koloni → upit vraća rezultate (NE 0) | `test_search_query.py::test_diacritic_insensitive` + `test_rank_and_tiebreak` (vraćaju >0 redova dokazuje da kolona nije query path) |
| GIN-NAME | SM-D20/C1 | GIN ime `products_search_gin` ≤30 char (NE `products_product_search_gin`) | `test_migrations.py` (index name assert + `manage.py check` exit 0) |
| PG-DB | OQ-1 → Task 8.0 (IMP-2) | FTS testovi zahtevaju PostgreSQL (ne SQLite) | `requires_postgres` marker + conftest hard assert `connection.vendor == "postgresql"` koji FAILA (NE skipif) ako backend nije psycopg |
| XSS-REFLECT | IMP-5 | Reflected query auto-escaped na FULL results strani (title/h1 golo `{{ query }}`, href `|urlencode`) | `test_templates.py` (`?q=<script>` → `&lt;script&gt;` u title/h1 + `%3Cscript%3E` u href) |
| TSQUERY-SAFE | IMP-10 | `search_type="plain"` — meta-znaci (& \| ! : *) ne bacaju SyntaxError; whitespace-only uhvaćen min-2 guard | `test_search_query.py` (query sa meta-znacima vraća 0 redova, NE 500) |
| HDR-WIRE | SM-D12 | header button aria-expanded/aria-controls + NE ukloni aria-label | `test_header_wiring.py` |

---

## TEA Addendum (RED phase)

> Dodato od strane TEA (RED phase) — NE menja nijednu SM sekciju/odluku iznad. Beleži
> RED-phase test inventory + nekoliko clarifikacija koje su otkrivene tokom pisanja
> failing testova. Sve ostaje konzistentno sa SM ugovorom; ovo su test-arbitraž napomene
> za Dev (GREEN phase).

### A. Test inventory (8 fajlova; ~69 test instanci sa parametrizacijom)

| Fajl | AC pokrivenost | # test inst. | Marker |
|---|---|---|---|
| `apps/search/tests/conftest.py` | — (infra) | `requires_postgres` hard-fail fixture | autouse |
| `apps/search/tests/factories.py` | — (helper) | `SearchProductFactory` (per-locale name/description) | — |
| `test_app_config.py` | AC1 | 9 | — |
| `test_migrations.py` | AC2 | 9 (uklj. param unaccent/pg_trgm) | `requires_postgres` |
| `test_search_query.py` | AC3/AC4/AC8 | 19 (parametrized locale + meta-char) | `django_db` + `requires_postgres` |
| `test_views.py` | AC3/AC5/AC6/AC7 | 12 | `django_db` + `requires_postgres` |
| `test_templates.py` | AC6/AC7/AC9(static) | 12 | `django_db` + `requires_postgres` |
| `test_header_wiring.py` | AC5/AC9(static) | 11 | `django_db` |

RED potvrda: 69 failed / 0 passed (collection uspeva jer `apps/search/tests/` paket
postoji; svaki test pada na nedostajući `apps.search.apps`/`search.py`/view/template/URL
ili `Database access not allowed` jer `apps.search` NIJE u INSTALLED_APPS). Ovo je očekivani
RED state — Dev GREEN phase realizuje sve klauzule.

### B. Clarifikacije koje testovi zaključavaju (arbitraž za Dev)

1. **`too_short` context ključ (potvrda § 2 Context surface):** `test_views.py` asertuje
   `response.context["too_short"] is True` za `< 2` znaka i `in (False, None)` za `≥ 2` znaka.
   Dev MORA postaviti `too_short` u context (već u § 2 tabeli) — testovi ga čitaju direktno.
2. **`suggestion_count == 0` u too_short slučaju:** too_short NE izvršava SQL (SM-D13) → view
   MORA postaviti `suggestion_count = 0` (NE izostaviti ključ). `test_short_query_no_sql_executed`
   čita `context.get("suggestion_count", 0) == 0`.
3. **GET-only → 405 očekivanje (SM-D17):** `test_dropdown_endpoint_is_get_only` očekuje da POST
   na `search:dropdown` vrati **405** (ili 400). Implikacija: FBV treba da bude ograničen na GET
   (npr. `@require_GET` dekorator) — inače POST prolazi kroz isti kod i vraća 200, što test obara.
   Ovo je test-arbitraž preciziranje SM-D17 „GET-only" (SM nije eksplicirao HTTP status za POST).
4. **`Unaccent`/`Value` import (potvrda § 2 C2/IMP-8):** `test_search_query.py` ne importuje ove
   direktno (testira ponašanje, ne import path), ali diacritic + meta-char testovi pucaju ako Dev
   NE koristi `Unaccent(Value(query))` na obe strane + `search_type="plain"`. Import ostaje per § 2.
5. **`search_results.html` single-`<h1>`:** `test_results_page_single_h1` zaključava TAČNO jedan
   `<h1>` na full strani (mirror Story 2.8 AC3 regression guard) — nije eksplicitno u § 4 ali je
   implicirano („JEDINI `<h1>`"). Sada je test-locked.
6. **`SearchProductFactory` postavlja `status=PUBLISHED` + `is_published=True`:** postojeći
   `ProductFactory` default-uje `status="draft"`; search factory ga override-uje na published za
   pozitivne FTS testove. Dev ne mora ništa — samo napomena da factory popunjava sva 3 locale
   `name_<lang>` polja kad caller ne prosledi eksplicitno (za locale-isolation testove caller
   prosleđuje `name_sr`/`name_hu`/`name_en` zasebno).

### C. Out-of-scope potvrda (mirror § 9)

JS-runtime ponašanje (Esc-to-close, focus return, click-outside, listbox keyboard nav ArrowUp/Down/Enter,
slide-in animacija, `prefers-reduced-motion`) NIJE pytest-pokriveno — `test_header_wiring.py` +
`test_templates.py` asertuju SAMO statički ARIA markup (`role="listbox"/"option"`, `aria-expanded`,
`aria-controls`, OOB `#aria-live` region). Runtime ponašanje je MANUAL smoke + Playwright Story 9.8/9.9
(AC9 manual gate). Ovo je eksplicitno označeno komentarima u test fajlovima.
