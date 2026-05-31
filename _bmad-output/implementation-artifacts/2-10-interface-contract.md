---
story-id: "2.10"
story-key: 2-10-jeegee-prikljucna-mehanizacija-strana
artifact: interface-contract
created: 2026-05-30
author: TEA / Murat (RED phase)
purpose: Canonical contract for Jeegee Priključna Mehanizacija landing strana — statička
         landing strana sa hero overlay + 3-card category showcase. NEMA HTMX, NEMA JS,
         NEMA filtera, NEMA paginacije. URL pattern, view CBV, 2 partials, 1 nova CSS
         komponenta, data migracija (seed Jeegee Brand + 3 Category), locale .po edits,
         data-testid surface. Dev MORA satisfy svaku klauzulu u GREEN phase.
         PRVA non-tractor brand listing strana u Epic 2 — uvodi kanonski `coric-category-card`
         BEM koji Story 2-11 + 2-12 REUSE-uju 1:1.
---

# Interface Contract — Story 2.10 Jeegee Priključna Mehanizacija Strana

Story 2.10 dodaje NOVI URL `/sr/mehanizacija/prikljucna/` (statički dvoslojni path bez
slug-a; ne shadow-uje Story 2-6 `/sr/traktori/<brand-slug>/`, Story 2-8 `/sr/traktori/`,
Story 2-9 `/sr/mehanizacija/polovna/`, Story 2-7 `/sr/proizvod/<slug>/`), NOVI
`JeegeePrikljucnaView` CBV (DetailView sa hardcoded Jeegee brand lookup), 1 glavni
template + 2 partials, NOVA `category-showcase.css` komponenta, locale .po edits za
~12 novih msgid-a, i 1 data migracija (`0003`) koja seed-uje Jeegee Brand + 3
mehanizacija Category instance.

**REUSE iz Story 1-7 + 2-6 (NEMA edit, NEMA copy):**
- `templates/partials/hero_overlay_card.html` (Story 1-7) — pozvan kroz `_jeegee_hero.html` sa `variant="jeegee"`
- `templates/partials/repeating_element.html` (Story 1-7) — indirektno kroz hero_overlay_card
- `templates/partials/section_eyebrow.html` (Story 1-7) — UPPERCASE eyebrow iznad category showcase grid-a
- `templates/partials/wave_divider.html` (Story 1-7) — iznad catalog CTA banner-a
- `templates/brands/brand_coming_soon.html` (Story 2-6) — REUSE 1:1 kad `jeegee_brand.is_coming_soon=True`
- `static/css/components/repeating-element.css` (Story 1-7) — `--jeegee` variant već postoji (linija 14)
- `static/css/components/pill-button.css` (Story 1-7) — `coric-button--primary` BEM klasa REUSE
- `static/css/tokens.css` (Story 1-5) — sve tokene koje koristi nova CSS komponenta već postoje
- `apps/brands/views.py` `BrandDetailView` (Story 2-6) — NETAKNUT; nova klasa dodata POSLE
- `apps/brands/urls.py` (Story 2-6) — postojeći `traktori/<slug:slug>/` pattern NETAKNUT

---

## 1. File-system delta

### Fajlovi koji MORAJU postojati posle GREEN phase (4 NEW + 6 EDIT + 1 data migracija)

| Path | Status | Vlasništvo |
|---|---|---|
| `apps/brands/views.py` | EDIT (ADD class + imports + 2 konstante) | `JeegeePrikljucnaView` CBV — postojeća `BrandDetailView` NETAKNUTA |
| `apps/brands/urls.py` | EDIT (ADD path + import) | `path("mehanizacija/prikljucna/", JeegeePrikljucnaView.as_view(), name="jeegee_prikljucna")` posle postojećeg `traktori/<slug>/` |
| `apps/brands/migrations/0003_seed_jeegee_and_prikljucna_categories.py` | NOVO (Dev) | RunPython data migracija (idempotent get_or_create + reverse_code) |
| `templates/brands/jeegee_prikljucna.html` | NOVO (Dev) | Glavni template — extends base.html |
| `templates/brands/partials/_jeegee_hero.html` | NOVO (Dev) | Hero wrapper sa fiksnim `variant="jeegee"` |
| `templates/brands/partials/_category_showcase.html` | NOVO (Dev) | 3-card grid sa Section Eyebrow + h2 + per-category kartica |
| `static/css/components/category-showcase.css` | NOVO (Dev) | Layout (grid wrapper + card + per-element modifier) |
| `static/css/main.css` | EDIT | +1 `@import url('./components/category-showcase.css');` linija |
| `locale/sr/LC_MESSAGES/django.po` | EDIT | Popuni msgstr za ~12 novih msgid-a |
| `locale/hu/LC_MESSAGES/django.po` | EDIT | Popuni hu prevode |
| `locale/en/LC_MESSAGES/django.po` | EDIT | Popuni en prevode |
| `apps/brands/tests/test_jeegee_prikljucna_urls.py` | NOVO (TEA) | AC1 URL routing |
| `apps/brands/tests/test_jeegee_prikljucna_view.py` | NOVO (TEA) | AC2 + AC2.5 view + Http404 + coming-soon |
| `apps/brands/tests/test_jeegee_prikljucna_templates.py` | NOVO (TEA) | AC3 + AC4 + AC5 + AC8 template + partial-degradation + aria-label regression |
| `apps/brands/tests/test_seed_migration_0003.py` | NOVO (TEA) | AC7 data migracija + idempotency + reverse |
| `apps/brands/tests/test_jeegee_prikljucna_static_assets.py` | NOVO (TEA) | AC6 CSS tokens + main.css import + repeating-element--jeegee selektor |

### Fajlovi koji MORAJU OSTATI NETAKNUTI (regression guard)

- `apps/brands/models.py` — NEMA model promene (Story 2-1 modeli ostaju)
- `apps/brands/admin.py`, `apps/brands/translation.py`
- `apps/brands/migrations/0001_initial.py`, `apps/brands/migrations/0002_alter_brand_created_at.py`
- `apps/brands/views.py` `BrandDetailView` klasa (Story 2-6 deliverable — ostaje netaknuta)
- `templates/brands/brand_detail.html` + svi `templates/brands/partials/_*` Story 2-6 partials
- `templates/brands/brand_coming_soon.html` (REUSE 1:1 — NE editovati)
- `templates/partials/*` (sve Story 1-7 partials — REUSE 1:1)
- `apps/products/` (kompletno — Story 2-10 NE query-uje Product modele; SM-D12)
- `static/vendor/*` (NEMA novih vendor asset-a)
- `static/js/*` (NEMA novih JS modula)
- `static/css/tokens.css` (svi tokeni već postoje — verifikovano live)
- `static/css/components/{header,footer,sticky-nav,lightbox,hero-overlay-card,
  repeating-element,pill-button,section-eyebrow,wave-divider,statistic-medallion,
  testimonials-slider,brand-listing,product-detail,product-gallery,product-variants,
  tractor-listing,used-machinery-listing,range-slider}.css`
- `templates/base.html` — NEMA novih `<script>` tag-ova (Story 2-10 NEMA JS)
- `config/urls.py` — i18n_patterns red NETAKNUT (apps.brands.urls već uključeno)
- `pyproject.toml`, `config/settings/`

---

## 2. URL patterns

### `apps/brands/urls.py` (EDIT)

```python
"""URL routing za apps.brands — Story 2.6 + Story 2.10."""

from django.urls import path

from apps.brands.views import BrandDetailView, JeegeePrikljucnaView

app_name = "brands"

urlpatterns = [
    path("traktori/<slug:slug>/", BrandDetailView.as_view(), name="detail"),
    path(
        "mehanizacija/prikljucna/",
        JeegeePrikljucnaView.as_view(),
        name="jeegee_prikljucna",
    ),
]
```

**Invarijante:**
- `app_name = "brands"` (postojeći namespace).
- URL name `jeegee_prikljucna` (NOVO — Story 2-10 specifičan, NE generic).
- Pattern je **statički dvoslojni path bez slug converter-a**.
- URL deconfliction (SM-D3): `mehanizacija/prikljucna/` NE overlap-uje sa
  `traktori/<slug:slug>/` (brands:detail), `traktori/` (products:tractor_list),
  `proizvod/<slug:slug>/` (products:detail), `mehanizacija/polovna/`
  (products:used_machinery_list). Resolver redosled je irelevantan.

### Root URLconf `config/urls.py` — NEMA EDIT

`apps.brands.urls` već uključeno u `i18n_patterns(...)` blok-u (Story 2-6 wiring; live
verifikovano `config/urls.py:27`). Story 2-10 dodaje pattern UNUTAR postojećeg include-a.

Resulting URL-ovi (sr/hu/en locale prefiks):

- `/sr/mehanizacija/prikljucna/` → `brands:jeegee_prikljucna`
- `/hu/mehanizacija/prikljucna/` → `brands:jeegee_prikljucna`
- `/en/mehanizacija/prikljucna/` → `brands:jeegee_prikljucna`

---

## 3. Views

### `apps/brands/views.py` — `JeegeePrikljucnaView` (NOVO)

#### Module-level imports — Dev MORA verifikovati i dodati ŠTA NEDOSTAJE

Postojeće (NE re-import — verifikovano live `apps/brands/views.py`):
- `from __future__ import annotations` (linija 12)
- `from django.db.models import Case, CharField, IntegerField, Prefetch, Value, When` (linija 14)
- `from django.utils.translation import gettext_lazy as _` (linija 15)
- `from django.views.generic import DetailView` (linija 16)
- `from apps.brands.models import Brand, Series` (linija 18) — **EDIT**: dodaj `Category`
- `from apps.products.models import Product, ProductSpecification, ProductTestimonial` (linija 19) — NETAKNUT

DODAJ novi import:
- **`from django.http import Http404`** (gore u grupi `from django.*`)

EDIT postojeće linije:
- Linija 18: `from apps.brands.models import Brand, Series` →
  **`from apps.brands.models import Brand, Category, Series`**

#### Module-level constants (POSLE imports, PRE `BrandDetailView` klase)

```python
# Story 2.10 — Jeegee priključna mehanizacija landing strana
_JEEGEE_BRAND_SLUG = "jeegee"
_PRIKLJUCNA_CATEGORY_SLUGS = (
    "osnovna-obrada-zemljista",
    "priprema-zemljista",
    "masine-za-setvu",
)
```

#### `JeegeePrikljucnaView` (POSLE postojeće `BrandDetailView` klase)

**Klasa:** `JeegeePrikljucnaView(DetailView)`

**Atributi:**
- `model = Brand`
- `context_object_name = "brand"`
- **NEMA** `slug_field` ni `slug_url_kwarg` — URL je statički bez slug kwarg-a;
  `get_object()` override hardcoduje `slug="jeegee"` lookup.

**Override `get_object(self, queryset=None)`:**
- Queryset = `self.get_queryset()` ako None
- Try: `return queryset.get(slug=_JEEGEE_BRAND_SLUG)`
- Except `Brand.DoesNotExist`: raise `Http404(_("Jeegee brand nije konfigurisan u sistemu."))`
- **SM-D7**: explicit raise sa `from django.http import Http404` (NE `get_object_or_404` shortcut)

**Override `get_template_names(self)`:**
- Ako `getattr(self, "object", None) is not None` AND `self.object.is_coming_soon` →
  vraća `["brands/brand_coming_soon.html"]`
- Inače → vraća `["brands/jeegee_prikljucna.html"]`
- (Default `DetailView.get()` flow setuje `self.object` PRE poziva `get_template_names()`;
  NEMA potreba za custom `get()` override — IMP-7 fix)

**Override `get_context_data(self, **kwargs)`:**
- `ctx = super().get_context_data(**kwargs)`
- Ako `self.object.is_coming_soon` → early return `ctx` (NEMA categories)
- Inače: `ctx["categories"] = list(Category.objects.filter(is_for=Category.CategoryScope.MEHANIZACIJA, slug__in=_PRIKLJUCNA_CATEGORY_SLUGS).order_by("display_order", "name"))`
- `list(...)` materializacija — template iteracija ne re-evaluuje queryset

**Context contract (renderuje template):**
- `brand` (Brand instance — Jeegee)
- `categories` (list[Category] — 3 mehanizacija kategorije; SAMO ako NOT is_coming_soon)

**Query budget contract:** **TAČNO 2 SQL upita** za pun render (SM-D27 placeholder; Dev
empirijski locks posle GREEN iter 1):
1. Brand fetch (`SELECT * FROM brands_brand WHERE slug = 'jeegee' LIMIT 1`)
2. Categories list (`SELECT * FROM brands_category WHERE is_for = 'mehanizacija' AND slug IN (...) ORDER BY display_order, name`)

NEMA Vary header — Story 2-10 je statička bez HTMX branching; `@vary_on_headers("HX-Request")`
NIJE primenjeno (razlika vs Story 2-9).

---

## 4. Templates

### `templates/brands/jeegee_prikljucna.html` (glavni, NOVO)

- `{% extends "base.html" %}`
- `{% load i18n static media_tags %}` (media_tags je safe-loaded za potencijalni future use; v1 ne koristi `{% responsive_picture %}`)
- `{% block title %}{{ brand.name }} {% translate "Priključna mehanizacija" %} | {% translate "Ćorić Agrar" %}{% endblock %}`
- `{% block meta_description %}{% blocktranslate with brand=brand.name %}Pregled priključne mehanizacije {{ brand }} po kategorijama — osnovna obrada zemljišta, priprema zemljišta, mašine za setvu.{% endblocktranslate %}{% endblock %}`
- `{% block content %}` outer wrapper: `<section class="coric-brand-detail coric-jeegee-prikljucna" data-testid="jeegee-prikljucna-page" aria-label="{% blocktranslate with brand=brand.name %}{{ brand }} priključna mehanizacija{% endblocktranslate %}">`

**CRITICAL-1 lock (SM-D8):** Outer wrapper koristi `aria-label`, **NE** `aria-labelledby`,
jer `<h1>` u Story 1-7 `hero_overlay_card.html` partial-u NEMA `id` atribut (linija 8:
`<h1 class="coric-hero-overlay-card__title">{{ title }}</h1>`). Modifikacija partial-a je
out-of-scope (breaking change za 4 postojeća konzumenta).

**3 sekcije TAČNIM redosledom:**

1. **Hero sekcija** — `<section id="jeegee-prikljucna-hero" aria-label="{% blocktranslate with brand=brand.name %}{{ brand }} hero{% endblocktranslate %}" class="coric-jeegee-prikljucna__hero-section">` koja `{% include "brands/partials/_jeegee_hero.html" %}`
2. **Categories sekcija** — `<section id="jeegee-prikljucna-categories" aria-labelledby="jeegee-prikljucna-categories-title" class="coric-jeegee-prikljucna__categories-section">` koja `{% include "brands/partials/_category_showcase.html" %}`
3. **Catalog CTA banner** (CONDITIONAL `{% if brand.catalog_pdf %}`) — `<section id="jeegee-prikljucna-catalog-cta" aria-labelledby="jeegee-prikljucna-catalog-cta-title" class="coric-jeegee-prikljucna__catalog-cta-section">` sadrži:
   - `{% include "partials/wave_divider.html" with position="top" %}`
   - `<div class="coric-catalog-cta-banner">` sa `<h2 id="jeegee-prikljucna-catalog-cta-title">` + `<p>` description + direct `<a href="{{ brand.catalog_pdf.url }}" target="_blank" rel="noopener noreferrer" download class="coric-button coric-button--primary" data-testid="jeegee-catalog-download">{% translate "Preuzmi katalog" %}</a>`

**Invarijante:**
- TAČNO 1 `<h1>` na strani (dolazi iz hero_overlay_card partial-a — `{{ brand.name }}`)
- Single `<main>` element (samo iz base.html) — outer wrapper je `<section>`, NIJE drugi `<main>`
- NEMA inline `style="..."`
- Svi user-facing string-ovi kroz `{% translate %}` ili `{% blocktranslate %}`
- NEMA ćirilice
- NEMA šišane latinice (sve č/ć/ž/š/đ pune dijakritike)

### `templates/brands/partials/_jeegee_hero.html` (NOVO)

```django
{% load i18n %}
<div class="coric-brand-hero" data-testid="jeegee-hero">
  {% if brand.logo %}
    {% include "partials/hero_overlay_card.html" with title=brand.name brand_logo=brand.logo.url brand_logo_alt=brand.name variant="jeegee" bullets="" %}
  {% else %}
    {% include "partials/hero_overlay_card.html" with title=brand.name brand_logo="" brand_logo_alt=brand.name variant="jeegee" bullets="" %}
  {% endif %}
</div>
```

**Invarijante:**
- TAČNO `variant="jeegee"` (NE "blue", NE "jeegee-blue") — **SM-D9 lock** (CSS klasa `.coric-repeating-element--jeegee` JE definisana u `static/css/components/repeating-element.css:14`)
- Defensive `{% if brand.logo %}` guard — `brand.logo.url` raise ValueError ako logo polje empty
- `data-testid="jeegee-hero"` na outer `<div class="coric-brand-hero">`

### `templates/brands/partials/_category_showcase.html` (NOVO)

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

**Invarijante:**
- Section Eyebrow tekst „KATEGORIJE PRIKLJUČNE MEHANIZACIJE" (UPPERCASE — Story 1-7 konvencija)
- `<h2 id="jeegee-prikljucna-categories-title">` (referenca iz outer section `aria-labelledby`)
- 3 `<article class="coric-category-card">` u v1 (po 1 per seeded Category)
- Per-category `<h3>` sa `id="cat-card-{slug}-title"` + `aria-labelledby` na `<article>`
- Per-category CTA href = **direct string interpolation** `/{{ LANGUAGE_CODE }}/mehanizacija/prikljucna/{{ category.slug }}/` (SM-D5)
- Per-category CTA `aria-label` = blocktranslate sa category.name interpolation (WCAG 2.1 SC 2.4.4)
- `{% empty %}` clause sa „Kategorije priključne mehanizacije su u pripremi." (defensive empty state)
- `data-testid` atributi: `category-showcase-grid`, `category-card-{slug}`, `category-card-cta-{slug}`
- IMP-5 fix (bare `{{ LANGUAGE_CODE }}` — NE `{{ request.LANGUAGE_CODE }}` — codebase konvencija)

### `templates/brands/brand_coming_soon.html` (Story 2-6 deliverable — REUSE 1:1, NE EDIT)

Story 2-10 NE kreira novi coming-soon template. `JeegeePrikljucnaView.get_template_names()`
vraća `["brands/brand_coming_soon.html"]` kad `is_coming_soon=True`. Postojeći template
renderuje brand (Jeegee) sa logom + nazivom + „Uskoro" badge + nazad-na-Home CTA bez izmena.

---

## 5. CSS

### `static/css/components/category-showcase.css` (NOVO)

Mora sadržati BEM klase (sve sa `coric-` prefiks-om, sve vrednosti kroz `var(--token)`):

- `.coric-category-showcase` — grid wrapper sa `display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));`
- `.coric-category-showcase__title` — h2 naslov iznad grid-a
- `.coric-category-card` — kartica root (flex column layout sa transition)
- `.coric-category-card:hover, .coric-category-card:focus-within` — hover/focus state (translateY + box-shadow)
- `.coric-category-card__icon` — ikona container (v1 prazan jer Bootstrap Icons font deferred)
- `.coric-category-card__title` — h3 naziv kategorije
- `.coric-category-card__description` — paragraf opisa
- `.coric-category-card__cta` — CTA dugme pozicioniranje (base style iz `.coric-button--primary` Story 1-7)
- `.coric-empty-state` — empty state paragraph (IMP-2 fix — `{% empty %}` clause CSS)
- `@media (prefers-reduced-motion: reduce)` block koji uklanja transition + transform

**Token verifikacija (live verifikovano 2026-05-30):**
- `--color-jeegee-blue: #00a4e9;` (`static/css/tokens.css:94`)
- `--color-neutral-gray-700: #4a4a4a;` (`static/css/tokens.css:102`)
- `--spacing-scale-5: 24px;` (`static/css/tokens.css:161`)
- `--color-brand-green-800`, `--color-neutral-white`, `--rounded-md`, `--typography-scale-{h2,h3,body}` — VEĆ postoje (Story 1-5)

### `static/css/main.css` (EDIT — +1 linija)

Dodaje TAČNO 1 nova `@import` linija na kraj postojećih @import linija (mirror Story 2-9
sintaksa — `url(...)` wrap + leading `./` + trailing semicolon):

```css
@import url('./components/category-showcase.css');
```

Pozicionira POSLE postojeće `@import url('./components/used-machinery-listing.css');` (Story 2-9, line 32).

---

## 6. Data migracija

### `apps/brands/migrations/0003_seed_jeegee_and_prikljucna_categories.py` (NOVO)

```python
"""Story 2.10 data migracija — seed Jeegee Brand + 3 mehanizacija kategorije.

Idempotentna kroz get_or_create. Reverse delete-uje tačno te 4 instance po slug-u.
NEMA modeltranslation hu/en prevode za Category.name u v1 (per SM-D14 — Story 8-5
admin populacija planirana kasnije).
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
        "icon": "",
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

**Invarijante:**
- `dependencies` pokazuje na `("brands", "0002_alter_brand_created_at")` (verifikovano live 2026-05-30 najnovija)
- Koristi `apps.get_model()` (NE direct model import — historical models snapshot)
- `get_or_create()` za idempotentnost
- `reverse_code=reverse_seed` za reversibility (`migrate brands 0002` rollback OK)
- Jeegee Brand: `brand_color="#00A4E9"` (uppercase per Story 2-1 hex regex; live `apps/brands/models.py:47` regex `^#[0-9A-Fa-f]{6}$` accept-uje uppercase)
- 3 Category instance sa `is_for="mehanizacija"` + display_order 10/20/30
- `icon=""` za sve 3 (Bootstrap Icons font deferred per SM-D18)

---

## 7. Anti-CDN guard

Sva nova fajlovi (CSS + templates) MORAJU biti audited za odsustvo eksternih CDN URL-ova:
- `cdn.jsdelivr.net` — 0 matches
- `unpkg.com` — 0 matches
- `cdnjs.cloudflare.com` — 0 matches

Story 2-10 NEMA JS module-a; NEMA novih vendor asset-a; sva referenca na Story 1-7 partials
ide kroz `{% include %}` (no CDN ovde).

---

## 8. HTML data-testid surface

| data-testid | Lokacija | Test koji ga koristi |
|---|---|---|
| `jeegee-prikljucna-page` | `templates/brands/jeegee_prikljucna.html` outer `<section>` | test_templates (AC3) |
| `jeegee-hero` | `templates/brands/partials/_jeegee_hero.html` outer `<div>` | test_templates (AC4) |
| `category-showcase-grid` | `templates/brands/partials/_category_showcase.html` grid wrapper | test_templates (AC5) |
| `category-card-{slug}` | per-category `<article>` (slug = osnovna-obrada-zemljista, priprema-zemljista, masine-za-setvu) | test_templates (AC5) |
| `category-card-cta-{slug}` | per-category CTA `<a>` | test_templates (AC5) |
| `jeegee-catalog-download` | catalog CTA banner `<a>` (CONDITIONAL) | test_templates (AC3) |
| `brand-coming-soon-page` | `templates/brands/brand_coming_soon.html` wrapper (REUSE Story 2-6) | test_view (AC2.5) |

---

## 9. Test factory expectations

### `apps/brands/tests/factories.py` (POSTOJI — REUSE, NE EDIT)

Story 2-10 testovi REUSE postojeći `BrandFactory` (Story 2-6 deliverable):
- `BrandFactory.create(name="Jeegee", slug="jeegee", brand_color="#00A4E9")` — kreira Jeegee Brand inline (test-time alternativa primeni 0003 migracije)
- `BrandFactory.create_coming_soon(slug="jeegee")` — coming-soon Jeegee

### `apps/brands/tests/factories.py` ADD `CategoryFactory` (NOVO klasa, dodata POSLE SeriesFactory)

Postojeći `factories.py` NEMA `CategoryFactory`. TEA dodaje minimalnu klasu sa
classmethod pattern (mirror BrandFactory/SeriesFactory stil — NEMA factory_boy
dependency u pyproject.toml):

```python
class CategoryFactory:
    """Helper factory za apps.brands.models.Category.

    Default-i: name='Test Category', is_for=Category.CategoryScope.MEHANIZACIJA,
    display_order=0, description='', icon=''.
    Slug se auto-generiše iz name kroz Category.save() (CRIT-2 pattern).
    """

    _counter = 0

    @classmethod
    def _next_name(cls) -> str:
        cls._counter += 1
        return f"Test Category {cls._counter}"

    @classmethod
    def create(cls, **overrides: Any):
        from apps.brands.models import Category

        defaults = {
            "name": cls._next_name(),
            "is_for": Category.CategoryScope.MEHANIZACIJA,
            "display_order": 0,
            "description": "",
            "icon": "",
        }
        defaults.update(overrides)
        return Category.objects.create(**defaults)

    @classmethod
    def create_mehanizacija(cls, **overrides: Any):
        from apps.brands.models import Category

        overrides.setdefault("is_for", Category.CategoryScope.MEHANIZACIJA)
        return cls.create(**overrides)

    @classmethod
    def create_traktori(cls, **overrides: Any):
        from apps.brands.models import Category

        overrides.setdefault("is_for", Category.CategoryScope.TRAKTORI)
        return cls.create(**overrides)
```

**RED phase NOTE:** Testovi mogu birati između (a) primena 0003 migracije kroz
pytest-django default fresh DB + django_db decorator (preferirana strategija — testira
GREEN-phase migration end-to-end), ili (b) inline kreiranje Brand + 3 Category instance
kroz factory-je. **Story 2-10 testovi koriste opciju (a) — pytest-django automatski
primenjuje sve migracije uključujući 0003 u --create-db fazi**; testovi ne treba
da inline kreiraju Jeegee Brand za happy path. Za negative testove (Http404, partial-
degradation) testovi koriste explicit DELETE/CREATE da menjaju state.

---

## 10. Locale + i18n contract

- Aktivni `LANGUAGE_CODE` per request prolazi kroz `i18n_patterns(...)` segment iz URL-a (`/sr/`, `/hu/`, `/en/`).
- Svi user-facing string-ovi u template-ima MORAJU biti kroz `{% translate %}` ili `{% blocktranslate %}`; testovi za AC8 audit-uju odsustvo hardcoded srpskih reči u render-ovanim sekcijama.
- Category.name polja seed-uju se u 0003 migraciji sa srpskim vrednostima; modeltranslation `name_hu` i `name_en` ostaju empty u v1 (SM-D14 + SM-D16). Pragmatic per Story 2-6 § Multi-locale URL slug-ovi open question; deferred to Story 8-5 + Story 6-5.

**Novi msgid-ovi (popunjeni za sva 3 locale-a):**
- `"Priključna mehanizacija"` (page title fragment)
- `"Pregled priključne mehanizacije {{ brand }} po kategorijama — osnovna obrada zemljišta, priprema zemljišta, mašine za setvu."` (meta description blocktranslate)
- `"KATEGORIJE PRIKLJUČNE MEHANIZACIJE"` (Section Eyebrow UPPERCASE)
- `"Pregled po kategorijama"` (categories h2)
- `"POGLEDAJ KATEGORIJU"` (CTA dugme tekst)
- `"Pogledaj kategoriju: {{ category }}"` (CTA aria-label blocktranslate)
- `"Kategorije priključne mehanizacije su u pripremi."` (empty state)
- `"Preuzmi {{ brand }} katalog"` (catalog CTA h2 blocktranslate)
- `"PDF dokument sa kompletnom ponudom priključne mehanizacije."` (catalog CTA description)
- `"Preuzmi katalog"` (catalog CTA dugme tekst)
- `"{{ brand }} hero"` (hero aria-label blocktranslate)
- `"{{ brand }} priključna mehanizacija"` (outer section aria-label blocktranslate)
- `"Jeegee brand nije konfigurisan u sistemu."` (Http404 message, gettext_lazy iz view-a)
- `"Ćorić Agrar"` (REUSE Story 2-6)

---

## 11. AC pokrivenost — test mapping

| AC | Test fajl | Test count |
|---|---|---|
| AC1 URL routing | `apps/brands/tests/test_jeegee_prikljucna_urls.py` | 4 |
| AC2 view + query budget | `apps/brands/tests/test_jeegee_prikljucna_view.py` | 5 |
| AC2.5 coming-soon | (pokriveno u test_jeegee_prikljucna_view.py) | — |
| AC3 page structure | `apps/brands/tests/test_jeegee_prikljucna_templates.py` | 5 |
| AC4 hero | `apps/brands/tests/test_jeegee_prikljucna_templates.py` | 2 |
| AC5 category showcase | `apps/brands/tests/test_jeegee_prikljucna_templates.py` | 5 |
| AC6 CSS + main.css import | `apps/brands/tests/test_jeegee_prikljucna_static_assets.py` | 4 |
| AC7 data migracija | `apps/brands/tests/test_seed_migration_0003.py` | 4 |
| AC8 i18n + a11y | `apps/brands/tests/test_jeegee_prikljucna_templates.py` | 3 |
| AC9 manual smoke + Lighthouse | (MANUAL — Dev gate, NIJE automated) | — |

**Total: 32 testova** (4 URL + 5 view + 15 templates + 4 migracija + 4 static assets).

**TEA RED-phase review addendum (2026-05-31):** dodato 2 testa pokrivanjem ranije gap-ova:
- AC3: `test_catalog_cta_banner_renders_when_catalog_pdf_present` — PRESENT path opcionog
  catalog CTA banner-a (raniji testovi pokrivali su SAMO ABSENT path); verifikuje
  `jeegee-catalog-download` data-testid + wave_divider include (contract § 8 surface).
- AC6: `test_category_showcase_css_defines_required_bem_selectors` — sadržaj nove
  `category-showcase.css` (BEM selektori + auto-fit grid + `prefers-reduced-motion` block);
  raniji test je proveravao SAMO @import liniju + file existence (prošao bi i sa praznim fajlom).

AC9 (manuelni Lighthouse + smoke check) NIJE automatizovan — Dev izvršava ručno u GREEN phase per AC9 § Lighthouse JSON artifact preservation.

---

## 12. Dev pre-flight checklist (GREEN phase)

Pre nego što Dev počne implementaciju:

1. Verifikovati `apps/brands/migrations/` najnovija je `0002_alter_brand_created_at.py` — verifikovano live 2026-05-30. Ako su nove migracije dodate u međuvremenu, dependency u 0003 MORA pokazivati na poslednju.
2. Verifikovati `apps/brands/views.py` postojeća `BrandDetailView` klasa ima Story 2-6 markup; nova `JeegeePrikljucnaView` ide POSLE.
3. Verifikovati `static/css/tokens.css` definiše: `--color-jeegee-blue` (linija 94), `--color-neutral-gray-700` (linija 102), `--spacing-scale-5` (linija 161), `--color-brand-green-800`, `--color-neutral-white`, `--rounded-md`, `--typography-scale-{h2,h3,body}` — VEĆ verifikovano.
4. Verifikovati `static/css/components/repeating-element.css:14` definiše `.coric-repeating-element--jeegee` — VEĆ verifikovano.
5. Verifikovati `templates/partials/hero_overlay_card.html` prima `variant` kwarg (linija 17 — `with variant=variant|default:"green"`) — VEĆ verifikovano.
6. Verifikovati `templates/base.html:6` koristi bare `{{ LANGUAGE_CODE }}` konvenciju (NE `request.LANGUAGE_CODE`) — VEĆ verifikovano (IMP-5 reference).
7. Verifikovati `templates/brands/brand_coming_soon.html` postoji i renderuje pill-badge + nazad-na-Home CTA (Story 2-6 deliverable) — VEĆ verifikovano.

---

## 13. Out-of-scope (eksplicitno)

- Real-browser keyboard + `prefers-reduced-motion` test (Playwright `page.emulateMedia(reducedMotion)`) — **Story 9.8 scope**
- WCAG axe-core static analysis — **Story 9.9 scope**
- Multi-locale URL slug-ovi (`/hu/mellekkellek/...`) — **Story 6.6 scope**
- Bootstrap Icons font wiring + category icon render — **Story 9-10 scope** (SM-D18)
- UX-DR-22 i18n fallback marker tooltip (kontekst „sadržaj na srpskom") — **Story 6-5 scope** (SM-D16)
- Category.name hu/en prevodi — **Story 8-5 (admin) + Story 6-5 (marker)**
- `coric-category-card` BEM REUSE u Story 2-11 + 2-12 — **future** (foundation lock-ovan ovde)
- Subcategory listing URL pattern `/mehanizacija/prikljucna/<category-slug>/` — **Story 2-11 scope** (Story 2-10 CTA href je placeholder direct interpolation, 404 produkuje 404 dok 2-11 ne dođe)
- Story 2-6 `_hero_section.html` `variant="blue"` dormant bug fix — **Story 9-10 polish** (out-of-scope za Story 2-10; SM-D9)
- Lighthouse Performance ≥ 80 (WebP/AVIF za brand logo) — **Story 9.10 scope**
- Custom 404 template sa srpskom porukom „Jeegee brand nije konfigurisan u sistemu." — **buduća tech-debt story** (v1 koristi Django default 404; custom message vidljiva samo u DEBUG=True + logs)
