---
story-id: "2.1"
story-key: 2-1-brand-series-category-subcategory-modeli
title: Interface Contract — Brand/Series/Category/Subcategory Modeli + apps/core foundation
status: contract
created: 2026-05-29
last_modified: 2026-05-29
author: TEA (RED phase)
---

# Story 2.1 — Interface Contract

Ovaj dokument je kanonski specifikacija ugovora za sve artifakte Story 2.1. TEA RED-phase
test-suite (`apps/brands/tests/*`, `apps/core/tests/test_utils.py`, `apps/core/tests/test_models.py`)
direktno enkodira asercije definisane ovde. Dev MUST satisfy ovaj ugovor da bi Story 2.1
prešla u GREEN.

Story 2.1 uvodi **prvi domain Django app u Epic 2** (`apps/brands/`) i **prvu Django ORM
test infrastructure** u projektu (postojeći Epic 1 testovi NE koriste `@pytest.mark.django_db`).

---

## 1. Artifact inventory

### 1.1 Novi fajlovi (production code)

| Path | Purpose |
|---|---|
| `apps/brands/__init__.py` | Prazan paket marker. |
| `apps/brands/apps.py` | `BrandsConfig(AppConfig)` sa `name = "apps.brands"`, `verbose_name = _("Brendovi")`. |
| `apps/brands/models.py` | 4 modela (Brand, Series, Category, Subcategory) — vidi § 3. |
| `apps/brands/admin.py` | Stub registracije za sva 4 modela (bez custom ModelAdmin). |
| `apps/brands/translation.py` | `TranslationOptions` za sva 4 modela — vidi § 4. |
| `apps/brands/migrations/__init__.py` | Prazan paket marker. |
| `apps/brands/migrations/0001_initial.py` | Generisana migracija; MANUAL REVIEWED. |
| `apps/core/models.py` | `TimestampedModel` + `SluggedModel` (abstract). Vidi § 2. |
| `apps/core/utils.py` | `slugify_ascii(text)` — ASCII transliteration helper. Vidi § 5. |

### 1.2 Novi fajlovi (test code — TEA RED phase)

| Path | Purpose |
|---|---|
| `apps/brands/tests/__init__.py` | Prazan paket marker. |
| `apps/brands/tests/test_models.py` | Model-level testovi (`__str__`, FK on_delete, save() auto-slug, validation). |
| `apps/brands/tests/test_translation.py` | modeltranslation registration testovi. |
| `apps/core/tests/test_utils.py` | `slugify_ascii` unit testovi (no DB). |
| `apps/core/tests/test_models.py` | `TimestampedModel`/`SluggedModel` abstract base introspection testovi. |

### 1.3 Modifikovani fajlovi

| Path | Modifications |
|---|---|
| `config/settings/base.py` | `INSTALLED_APPS` dodaje `"modeltranslation"` (PRE `apps.brands`) i `"apps.brands"` (POSLE `apps.core`). |

### 1.4 NIJE kreirano u Story 2.1
- NEMA `apps/brands/views.py` content (startapp default — prazan)
- NEMA `apps/brands/urls.py` content
- NEMA `apps/brands/forms.py`, `managers.py`, `signals.py`
- NEMA custom `ModelAdmin` klasa (samo `admin.site.register()`)
- NEMA template-a u Story 2.1
- NEMA CSS / JS promene

---

## 2. `apps/core/models.py` — abstract base klase (AC9)

### 2.1 `TimestampedModel`

```python
class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
```

### 2.2 `SluggedModel`

```python
class SluggedModel(models.Model):
    slug = models.SlugField(max_length=140, unique=True, db_index=True)

    class Meta:
        abstract = True
```

### 2.3 Honest YAGNI acknowledgment (Decision D3)

Brand/Series/Category/Subcategory **NE nasleđuju** ove mixine u Story 2.1 — definišu polja
eksplicitno (per AC2-AC5). Razlog: Series i Subcategory imaju per-scope unique slug
(UniqueConstraint), što je nekompatibilno sa `SluggedModel.slug.unique=True`.

Mixine se uvode SADA kao FOUNDATION za Story 2.2+ (Product, gde je slug globalno unique).

---

## 3. `apps/brands/models.py` — 4 modela

### 3.1 Imports (module header)

```python
import re

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.core.utils import slugify_ascii
```

### 3.2 `Brand` model (AC2)

| Polje | Tip | Constraint | Translatable |
|---|---|---|---|
| `name` | `CharField(max_length=120)` | required | **YES** (_sr/_hu/_en) |
| `slug` | `SlugField(max_length=140, unique=True, db_index=True)` | globally unique, ASCII | no |
| `logo` | `ImageField(upload_to="brands/logos/", max_length=255, blank=True, null=True)` | optional | no |
| `hero_image` | `ImageField(upload_to="brands/heroes/", max_length=255, blank=True, null=True)` | optional | no |
| `description` | `TextField(blank=True)` | optional | **YES** |
| `slogan` | `CharField(max_length=200, blank=True)` | optional | **YES** |
| `statistics` | `JSONField(default=list, blank=True)` | list of dict, max 4 entries | no |
| `catalog_pdf` | `FileField(upload_to="brands/catalogs/", max_length=255, blank=True, null=True)` | optional | no |
| `brand_color` | `CharField(max_length=7, blank=True)` | hex `#RRGGBB` if present | no |
| `is_coming_soon` | `BooleanField(default=False)` | NO `db_index=True` (IMP-3) | no |
| `created_at` | `DateTimeField(auto_now_add=True)` | — | no |
| `updated_at` | `DateTimeField(auto_now=True)` | — | no |

**Meta:**
```python
class Meta:
    ordering = ["name"]
    verbose_name = _("Brend")
    verbose_name_plural = _("Brendovi")
    indexes = [
        models.Index(fields=["is_coming_soon", "name"], name="brands_brand_coming_name_idx"),
    ]
```

**`__str__`** → `self.name`

**`get_absolute_url()`** → `reverse("brands:detail", kwargs={"slug": self.slug})` (raise NoReverseMatch u 2.1 — test koristi `@pytest.mark.skip`).

**`clean()`:**
- `brand_color`: ako non-empty, mora match-ovati `^#[0-9A-Fa-f]{6}$` (empty passes — CRIT-3)
- `statistics`: mora biti `list`; svaka stavka mora biti `dict`; `len() <= 4`

**`save()` override (CRIT-2 pattern):**
```python
def save(self, *args, **kwargs):
    if not self.slug and self.name:
        self.slug = slugify_ascii(self.name)
    self.full_clean()
    super().save(*args, **kwargs)
```

### 3.3 `Series` model (AC3)

| Polje | Tip | Constraint | Translatable |
|---|---|---|---|
| `brand` | `ForeignKey("brands.Brand", on_delete=models.PROTECT, related_name="series")` | required | no |
| `name` | `CharField(max_length=120)` | required | **YES** |
| `slug` | `SlugField(max_length=140, db_index=True)` | per-brand unique (UniqueConstraint), NE globalno | no |
| `description` | `TextField(blank=True)` | optional | **YES** |
| `layout_mode` | `CharField(max_length=10, choices=LayoutMode.choices, default=LayoutMode.GRID)` | TextChoices | no |
| `display_order` | `PositiveSmallIntegerField(default=0, db_index=True)` | — | no |
| `created_at` / `updated_at` | timestamps | — | no |

**TextChoices:**
```python
class LayoutMode(models.TextChoices):
    GRID = "grid", _("Grid")
    EXTENDED = "extended", _("Extended")
```

**Meta:**
```python
class Meta:
    ordering = ["display_order", "name"]  # IMP-5: NO brand__name JOIN
    verbose_name = _("Serija")
    verbose_name_plural = _("Serije")
    constraints = [
        models.UniqueConstraint(fields=["brand", "slug"], name="brands_series_brand_slug_unique"),
    ]
    indexes = [
        models.Index(fields=["brand", "display_order"], name="brands_series_brand_order_idx"),
    ]
```

**`__str__`** → `f"{self.brand.name} — {self.name}"` (em-dash)

**`get_absolute_url()`** → `reverse("brands:series_detail", kwargs={"brand_slug": self.brand.slug, "series_slug": self.slug})`

**`save()`** — isti CRIT-2 pattern kao Brand.

### 3.4 `Category` model (AC4)

| Polje | Tip | Constraint | Translatable |
|---|---|---|---|
| `name` | `CharField(max_length=120)` | required | **YES** |
| `slug` | `SlugField(max_length=140, unique=True, db_index=True)` | globally unique | no |
| `description` | `TextField(blank=True)` | optional | **YES** |
| `is_for` | `CharField(max_length=20, choices=CategoryScope.choices, db_index=True)` | NO default (admin mora birati) | no |
| `display_order` | `PositiveSmallIntegerField(default=0, db_index=True)` | — | no |
| `icon` | `CharField(max_length=64, blank=True)` | Bootstrap Icons class | no |
| `created_at` / `updated_at` | timestamps | — | no |

**TextChoices:**
```python
class CategoryScope(models.TextChoices):
    TRAKTORI = "traktori", _("Traktori")
    MEHANIZACIJA = "mehanizacija", _("Mehanizacija")
```

**Meta:**
```python
class Meta:
    ordering = ["is_for", "display_order", "name"]
    verbose_name = _("Kategorija")
    verbose_name_plural = _("Kategorije")
    indexes = [
        models.Index(fields=["is_for", "display_order"], name="brands_category_scope_order_idx"),
    ]
```

**`__str__`** → `f"{self.get_is_for_display()} — {self.name}"`

**`get_absolute_url()`** → routes po `is_for` ka `brands:category_traktori` ili `brands:category_mehanizacija` URL pattern-u.

**`save()`** — isti CRIT-2 pattern.

### 3.5 `Subcategory` model (AC5, AC11)

| Polje | Tip | Constraint | Translatable |
|---|---|---|---|
| `category` | `ForeignKey("brands.Category", on_delete=models.CASCADE, related_name="subcategories")` | required | no |
| `parent` | `ForeignKey("self", on_delete=models.CASCADE, related_name="children", blank=True, null=True)` | optional (top-level) | no |
| `name` | `CharField(max_length=120)` | required | **YES** |
| `slug` | `SlugField(max_length=140, db_index=True)` | per (category, parent) unique | no |
| `description` | `TextField(blank=True)` | optional | **YES** |
| `icon` | `CharField(max_length=64, blank=True)` | Bootstrap Icons class | no |
| `display_order` | `PositiveSmallIntegerField(default=0, db_index=True)` | — | no |
| `created_at` / `updated_at` | timestamps | — | no |

**Meta:**
```python
class Meta:
    ordering = ["category", "parent_id", "display_order", "name"]
    verbose_name = _("Potkategorija")
    verbose_name_plural = _("Potkategorije")
    constraints = [
        models.UniqueConstraint(
            fields=["category", "parent", "slug"],
            name="brands_subcategory_cat_parent_slug_unique",
        ),
    ]
    indexes = [
        models.Index(
            fields=["category", "parent", "display_order"],
            name="brands_subcat_cat_parent_order_idx",
        ),
    ]
```

**`__str__`** → `self.name`

**`get_absolute_url()`** → raise `NotImplementedError("Subcategory URL pattern defined in Story 2.11")` (BR-12).

**`clean()`** — Subcategory chain depth validation:
- self counts as level 1
- traverse `self.parent` chain
- `visited_ids` set guard za circular reference
- raise `ValidationError` ako depth > 3 ili ako se detect-uje cycle

**`save()`:**
```python
def save(self, *args, **kwargs):
    if not self.slug and self.name:
        self.slug = slugify_ascii(self.name)
    self.full_clean()  # enforces depth + slug + other constraints
    super().save(*args, **kwargs)
```

**Helper metode (AC11):**
- `get_ancestors_chain() -> list["Subcategory"]` — vraća root-to-direct-parent (bez self), sa circular guard.
- `get_depth() -> int` — `len(get_ancestors_chain()) + 1`.

---

## 4. `apps/brands/translation.py` (AC6)

**modeltranslation auto-discovery** zahteva `INSTALLED_APPS` order: `"modeltranslation"` MORA biti PRE `"apps.brands"`.

```python
from modeltranslation.translator import TranslationOptions, register

from apps.brands.models import Brand, Category, Series, Subcategory


@register(Brand)
class BrandTranslationOptions(TranslationOptions):
    fields = ("name", "description", "slogan")


@register(Series)
class SeriesTranslationOptions(TranslationOptions):
    fields = ("name", "description")


@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ("name", "description")


@register(Subcategory)
class SubcategoryTranslationOptions(TranslationOptions):
    fields = ("name", "description")
```

**LANGUAGES iz Story 1.4** = `[("sr", "Srpski"), ("hu", "Magyar"), ("en", "English")]` →
modeltranslation auto-generiše `_sr`, `_hu`, `_en` suffix kolone u migraciji.

---

## 5. `apps/core/utils.py` — `slugify_ascii()` helper

### 5.1 Signature

```python
def slugify_ascii(text: str) -> str
```

### 5.2 Implementacija (two-stage replacement — BR-14)

```python
"""Shared utility helpers for app-level cross-cutting concerns."""
from django.utils.text import slugify

# Srpska latinica digrafovi — MORAJU se zameniti PRE str.maketrans()
# jer str.maketrans(dict) zahteva single-character ključeve.
SR_DIGRAPHS = {
    "Dž": "Dz", "dž": "dz",
    "Lj": "Lj", "lj": "lj",
    "Nj": "Nj", "nj": "nj",
}

# Single-character dijakritici — preko str.maketrans
SR_DIAKRITICI = str.maketrans({
    "Ć": "C", "ć": "c", "Č": "C", "č": "c",
    "Š": "S", "š": "s", "Ž": "Z", "ž": "z",
    "Đ": "D", "đ": "d",
})


def slugify_ascii(text: str) -> str:
    """ASCII-only slug per project-context.md § Slugovi.

    Two-stage replacement:
    1. Multi-character digrafovi (Dž/Lj/Nj) preko str.replace()
    2. Single-character dijakritici (Ć/Č/Š/Ž/Đ) preko str.translate()
    Zatim Django default slugify sa allow_unicode=False.
    """
    if not text:
        return ""
    for src, dst in SR_DIGRAPHS.items():
        text = text.replace(src, dst)
    text = text.translate(SR_DIAKRITICI)
    return slugify(text, allow_unicode=False)
```

### 5.3 Behavior contract (matches TEA tests)

| Input | Output | Test |
|---|---|---|
| `""` | `""` | `test_slugify_ascii_empty_string_returns_empty` |
| `"Čorić"` | `"coric"` | `test_slugify_ascii_handles_diakritici` |
| `"Šargarepa"` | `"sargarepa"` | `test_slugify_ascii_handles_diakritici` |
| `"Žutilo"` | `"zutilo"` | `test_slugify_ascii_handles_diakritici` |
| `"Đak"` | `"dak"` | `test_slugify_ascii_handles_diakritici` |
| `"Džon"` | `"dzon"` | `test_slugify_ascii_handles_digraphs` |
| `"Ljubo"` | `"ljubo"` | `test_slugify_ascii_handles_digraphs` |
| `"Njuska"` | `"njuska"` | `test_slugify_ascii_handles_digraphs` |
| `"Đorđe Šarac"` | `"dorde-sarac"` | `test_slugify_ascii_handles_mixed` |
| `"ČORIĆ"` | `"coric"` | `test_slugify_ascii_handles_uppercase_mixed_diakritici` |

**KRITIČAN regression guard (BR-14):** Module mora učitati bez `ValueError: string keys in
translate table must be of length 1`. Test `test_slugify_ascii_module_imports_without_error`
proverava ovaj invariant.

---

## 6. `config/settings/base.py` — INSTALLED_APPS izmena

```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "modeltranslation",            # NOVO Story 2.1 — MORA PRE apps.brands
    "django_htmx",
    "django_bootstrap5",
    "apps.core",
    "apps.brands",                  # NOVO Story 2.1
]
```

---

## 7. Migracija `apps/brands/migrations/0001_initial.py`

**Backend-agnostic asercija (CRIT-4):** strukturalna, NE column-type literal.

**Expected operacije:**
- 4 × `CreateModel` (Brand, Series, Category, Subcategory)
- Translation field-ovi: `_sr`, `_hu`, `_en` suffix-i na translatable poljima
  - Brand: `name`, `description`, `slogan` × 3 langs = 9 dodatnih kolona
  - Series, Category, Subcategory: `name`, `description` × 3 langs = 6 dodatnih kolona po modelu
- `AddIndex` za sva 4 modela (Meta.indexes)
- `AddConstraint` za UniqueConstraint na Series i Subcategory
- FK `on_delete`:
  - `PROTECT` na `Series.brand`
  - `CASCADE` na `Subcategory.category` i `Subcategory.parent`

---

## 8. Test infrastructure (RED phase — pytest-django patterns)

### 8.1 First Django ORM test infrastructure u projektu

Postojeći Epic 1 testovi (`tests/test_docker_compose.py`, etc.) su **konfiguraciono-orijentisani**
(filesystem + YAML + JSON checks) — ne koriste `@pytest.mark.django_db`. Story 2.1 testovi su
**prvi koji aktivno koriste DB** preko pytest-django.

### 8.2 Pattern za DB testove

```python
import pytest
from django.core.exceptions import ValidationError
from django.db.models import ProtectedError

pytestmark = pytest.mark.django_db  # SVI testovi u modulu


def test_brand_save_auto_generates_slug_from_name():
    from apps.brands.models import Brand
    brand = Brand(name="John Deere", brand_color="#25402F", statistics=[])
    brand.save()
    assert brand.slug == "john-deere"
```

### 8.3 Pattern za pure unit testove (no DB)

`slugify_ascii` testovi NE trebaju DB — bez `@pytest.mark.django_db` dekoratora.

### 8.4 Pattern za URL testove (Gotcha BR-4 / BR-12)

```python
@pytest.mark.skip(reason="URLs come in Story 2.6")
def test_brand_get_absolute_url_returns_path(): ...
```

---

## 9. Test summary mapping AC → test files

| AC | Test file | Tests |
|---|---|---|
| AC1 (app skeleton) | `apps/brands/tests/test_apps.py` | OUT OF SCOPE — Story 2.1 ne traži test_apps.py; AC1 verifikuje se kroz `manage.py check` |
| AC2 (Brand) | `apps/brands/tests/test_models.py` | `test_brand_*` |
| AC3 (Series) | `apps/brands/tests/test_models.py` | `test_series_*` |
| AC4 (Category) | `apps/brands/tests/test_models.py` | `test_category_*` |
| AC5 (Subcategory) | `apps/brands/tests/test_models.py` | `test_subcategory_*` |
| AC6 (translation) | `apps/brands/tests/test_translation.py` | `test_*_has_translation_fields*` |
| AC7 (migration) | Manual review (Task 5.2 grep checklist) | — |
| AC8 (admin) | OUT OF SCOPE | — |
| AC9 (core base classes) | `apps/core/tests/test_models.py` | `test_timestamped_*`, `test_sluggedmodel_*` |
| AC10 (gettext_lazy) | Lint + manual review | — |
| AC11 (helper methods) | `apps/brands/tests/test_models.py` | `test_subcategory_get_depth*`, `test_subcategory_get_ancestors_chain*` (cover via 3-level chain test) |
| AC12 (test coverage) | All files above | — |
| Utils (BR-14) | `apps/core/tests/test_utils.py` | `test_slugify_ascii_*` |

---

**End of Interface Contract 2.1**
