---
story-id: "2.2"
story-key: 2-2-product-i-related-modeli
title: Interface Contract — Product i Related Modeli (7 entiteta) + translation + config delta
status: contract
created: 2026-05-29
last_modified: 2026-05-29
author: TEA (RED phase)
---

# Story 2.2 — Interface Contract

Ovaj dokument je kanonski specifikacija ugovora za sve artifakte Story 2.2. TEA RED-phase
test-suite (`apps/products/tests/test_models.py`, `tests/integration/test_app_boundaries.py`)
direktno enkodira asercije definisane ovde. Dev MUST satisfy ovaj ugovor da bi Story 2.2
prešla u GREEN.

Story 2.2 uvodi **drugi domain Django app u Epic 2** (`apps/products/`) — prvi konzument
`apps.core.models` mixina (`TimestampedModel`, `SluggedModel`) uvedenih u Story 2.1 kao
FOUNDATION (Decision D3 u 2-1 honest YAGNI acknowledgment).

---

## 1. Artifact inventory

### 1.1 Novi fajlovi (production code — Dev deliverable u GREEN phase)

| Path | Purpose |
|---|---|
| `apps/products/__init__.py` | Prazan paket marker (startapp generiše). |
| `apps/products/apps.py` | `ProductsConfig(AppConfig)` sa `name = "apps.products"`, `verbose_name = _("Proizvodi")`. |
| `apps/products/models.py` | 7 modela (Product, ProductImage, ProductVariant, ProductSpecification, ProductBrochure, ProductTestimonial, ProductSimilar) — vidi § 3. |
| `apps/products/admin.py` | Stub registracije za svih 7 modela (bare `admin.site.register()`, NE `TranslationAdmin`). |
| `apps/products/translation.py` | `TranslationOptions` za 6 od 7 modela — vidi § 4. ProductSimilar IZUZET (no translatable fields). |
| `apps/products/migrations/__init__.py` | Prazan paket marker (startapp generiše). |
| `apps/products/migrations/0001_initial.py` | Generisana migracija; MANUAL REVIEWED. |

### 1.2 Novi fajlovi (test code — TEA RED phase deliverable)

| Path | Purpose |
|---|---|
| `apps/products/tests/__init__.py` | Prazan paket marker (Dev kreira u Task 1.2). |
| `apps/products/tests/test_models.py` | Model-level testovi (`__str__`, FK on_delete, save() auto-slug, validation, ProductSimilar constraints, translation introspection). |
| `apps/products/tests/test_apps.py` | `ProductsConfig.name` smoke (Gotcha PR-1 regression guard). |
| `tests/integration/__init__.py` | Paket marker za cross-app integration testove. |
| `tests/integration/test_app_boundaries.py` | AST-based regression: `apps.brands` NE importuje `apps.products`; `apps.products` NE importuje `apps.catalog`. |

### 1.3 Modifikovani fajlovi (Dev u GREEN)

| Path | Modifications |
|---|---|
| `config/settings/base.py` | `INSTALLED_APPS` APENDUJ `"apps.products",` POSLE `"apps.brands",`. Dodaj `MODELTRANSLATION_FALLBACK_LANGUAGES = ("sr",)` POSLE `LANGUAGES = [...]`. |

### 1.4 NIJE kreirano u Story 2.2

- NEMA `apps/products/views.py` (Task 1.2b briše startapp default; views su 2.7/2.8 scope)
- NEMA `apps/products/urls.py` (startapp NE generiše; Story 2.7 prvi put kreira sa `app_name = "products"`)
- NEMA `apps/products/forms.py` (Story 2.7/8.6)
- NEMA `apps/products/managers.py` (Story 2.6 — `PublishedProductManager`)
- NEMA `apps/products/signals.py` (Story 2.4 — `post_save` za ProductBrochure cover thumbnail)
- NEMA custom `ModelAdmin` klasa (samo bare `admin.site.register()`)
- NEMA `search_vector` polja (Story 2.13 zasebna migracija)
- NEMA MIME validacije za file/image polja (Story 2.3/2.4)
- NEMA `TranslationAdmin` base klase (Story 8.6)

---

## 2. `apps/products/apps.py` — AppConfig

```python
"""AppConfig za apps.products — Product i related modeli content layer."""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ProductsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.products"                     # KRITIČNO — sa apps. prefiksom (Gotcha PR-1)
    verbose_name = _("Proizvodi")
```

---

## 3. `apps/products/models.py` — 7 modela

### 3.1 Imports (module header)

```python
from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.core.models import SluggedModel, TimestampedModel
from apps.core.utils import slugify_ascii

_PRODUCT_KEY_FEATURES_MAX = 3
```

### 3.2 `Product` model (AC2)

**Inheritance:** `class Product(SluggedModel, TimestampedModel):` — KRITIČAN redosled (SluggedModel pre TimestampedModel; oba `abstract = True`). **Prvi konzument 2.1 D3 foundation.**

**Nested TextChoices:**

```python
class ConditionChoice(models.TextChoices):
    NEW = "new", _("Novo")
    USED = "used", _("Polovno")


class StatusChoice(models.TextChoices):
    DRAFT = "draft", _("Nacrt")
    PUBLISHED = "published", _("Objavljen")
    ARCHIVED = "archived", _("Arhiviran")
```

**Polja:**

| Polje | Tip | Constraint | Translatable |
|---|---|---|---|
| `brand` | `ForeignKey("brands.Brand", on_delete=PROTECT, related_name="products", verbose_name=_("Brend"))` | required | no |
| `series` | `ForeignKey("brands.Series", on_delete=PROTECT, related_name="products", null=True, blank=True, verbose_name=_("Serija"))` | optional (PR-D2) | no |
| `subcategory` | `ForeignKey("brands.Subcategory", on_delete=PROTECT, related_name="products", null=True, blank=True, verbose_name=_("Potkategorija"))` | optional (PR-D3) | no |
| `name` | `CharField(_("Naziv"), max_length=200)` | required | **YES** (_sr/_hu/_en) |
| `description` | `TextField(_("Opis"), blank=True, validators=[MaxLengthValidator(50000)])` | optional, hard cap 50000 chars (SECURITY M2 iter-1) | **YES** |
| `key_features` | `JSONField(_("Ključne karakteristike"), default=list, blank=True)` | list of str, MAX 3 | **YES** |
| `main_image` | `ImageField(_("Glavna slika"), upload_to="products/main/", max_length=255, blank=True, null=True)` | optional | no |
| `year` | `PositiveSmallIntegerField(_("Godina"), blank=True, null=True)` | optional | no |
| `price_eur` | `DecimalField(_("Cena (EUR)"), max_digits=10, decimal_places=2, blank=True, null=True)` | optional | no |
| `horse_power` | `PositiveSmallIntegerField(_("Konjska snaga"), blank=True, null=True)` | optional | no |
| `condition` | `CharField(_("Stanje"), max_length=10, choices=ConditionChoice.choices, default=NEW)` | **NEMA `db_index=True`** (composite index pokriva) | no |
| `status` | `CharField(_("Status"), max_length=12, choices=StatusChoice.choices, default=DRAFT, db_index=True)` | required | no |
| `is_published` | `BooleanField(_("Objavljen"), default=False)` | **NEMA `db_index=True`** (composite index leftmost) | no |
| `slug` | inherited iz `SluggedModel` (`max_length=140, unique=True, db_index=True`) | globally unique, ASCII | no |
| `created_at`/`updated_at` | inherited iz `TimestampedModel` | — | no |

**Meta:**

```python
class Meta:
    ordering = ["-created_at"]
    verbose_name = _("Proizvod")
    verbose_name_plural = _("Proizvodi")
    indexes = [
        models.Index(fields=["is_published", "-created_at"],
                     name="products_product_pub_created_idx"),
        models.Index(fields=["brand", "status"],
                     name="products_product_brand_status_idx"),
        models.Index(fields=["condition", "is_published"],
                     name="products_product_condition_pub_idx"),
    ]
```

**`__str__`** → `f"{self.brand.name} — {self.name}"` (em-dash)

**`get_absolute_url()`** → `reverse("products:detail", kwargs={"slug": self.slug})` (raise `NoReverseMatch` u 2.2; test skip per PR-5/PR-12).

**`clean()`** → validira `key_features` na BAZNOM accessor-u I za sve translated varijante (`key_features_sr`, `key_features_hu`, `key_features_en`) — iteracija kroz `settings.LANGUAGES`:
- mora biti `list`; svaka stavka mora biti `str`; `len() <= 3`
- na ValidationError ključ je TAČNO ime polja (`"key_features"` ili `f"key_features_{lang}"`)
- belt-and-suspenders dizajn → `message_dict` može sadržati BOTH base I translated key (TEA asercije koriste `in` membership, NE equality)

**`full_clean()` override (Pattern A iz 2.1):** auto-gen slug iz `name` PRE `super().full_clean()` poziva.

**`save()` override (Pattern A iz 2.1):** auto-gen slug iz `name` → `self.full_clean()` → `super().save()`.

### 3.3 `ProductImage` model (AC3)

**Inheritance:** `class ProductImage(TimestampedModel):` (no slug).

| Polje | Tip | Constraint | Translatable |
|---|---|---|---|
| `product` | `ForeignKey(Product, on_delete=CASCADE, related_name="images", verbose_name=_("Proizvod"))` | required | no |
| `image` | `ImageField(_("Slika"), upload_to="products/gallery/", max_length=255)` | **REQUIRED** | no |
| `order` | `PositiveSmallIntegerField(_("Redosled"), default=0, db_index=True)` | — | no |
| `alt_text` | `CharField(_("Alt tekst"), max_length=200, blank=True)` | optional | **YES** |

**Meta:**

```python
class Meta:
    ordering = ["order", "id"]
    verbose_name = _("Slika proizvoda")
    verbose_name_plural = _("Slike proizvoda")
    indexes = [
        models.Index(fields=["product", "order"], name="products_image_product_order_idx"),
    ]
```

**`__str__`** → `f"{self.product.name} — slika {self.order}"`

**NEMA `get_absolute_url()`** (child entity).

### 3.4 `ProductVariant` model (AC4)

**Inheritance:** `class ProductVariant(TimestampedModel):`.

| Polje | Tip | Constraint | Translatable |
|---|---|---|---|
| `product` | `ForeignKey(Product, on_delete=CASCADE, related_name="variants", verbose_name=_("Proizvod"))` | required | no |
| `name` | `CharField(_("Naziv"), max_length=200)` | required | **YES** |
| `code` | `CharField(_("Kod"), max_length=50, blank=True)` | optional, NE globally unique | no |
| `image` | `ImageField(_("Slika varijante"), upload_to="products/variants/", max_length=255, blank=True, null=True)` | optional | no |
| `description` | `TextField(_("Opis"), blank=True, validators=[MaxLengthValidator(50000)])` | optional, hard cap 50000 chars (SECURITY L1 iter-2) | **YES** |
| `order` | `PositiveSmallIntegerField(_("Redosled"), default=0, db_index=True)` | — | no |

**Meta:**

```python
class Meta:
    ordering = ["order", "id"]
    verbose_name = _("Varijanta")
    verbose_name_plural = _("Varijante")
    indexes = [
        models.Index(fields=["product", "order"], name="products_variant_product_order_idx"),
    ]
```

**`__str__`** → `self.name` (locale-aware kroz modeltranslation fallback).

### 3.5 `ProductSpecification` model (AC5)

**Inheritance:** `class ProductSpecification(TimestampedModel):`.

**Nested TextChoices:**

```python
class SpecSection(models.TextChoices):
    MOTOR = "motor", _("Motor")
    TRANSMISIJA = "transmisija", _("Transmisija")
    HIDRAULIKA = "hidraulika", _("Hidraulika")
    OSTALO = "ostalo", _("Ostalo")
```

| Polje | Tip | Constraint | Translatable |
|---|---|---|---|
| `product` | `ForeignKey(Product, on_delete=CASCADE, related_name="specifications", verbose_name=_("Proizvod"))` | required | no |
| `section` | `CharField(_("Sekcija"), max_length=20, choices=SpecSection.choices, default=OSTALO, db_index=True)` | required | no |
| `key` | `CharField(_("Naziv specifikacije"), max_length=200)` | required | **YES** |
| `value` | `CharField(_("Vrednost"), max_length=200)` | required | **YES** |
| `order` | `PositiveSmallIntegerField(_("Redosled"), default=0, db_index=True)` | — | no |

**Meta:**

```python
class Meta:
    # KRITIČNO: NEMA "section" u ordering (alphabetical sort != display order).
    ordering = ["product", "order", "id"]
    verbose_name = _("Specifikacija")
    verbose_name_plural = _("Specifikacije")
    indexes = [
        models.Index(fields=["product", "section", "order"],
                     name="products_spec_product_section_idx"),
    ]
```

**`__str__`** → `f"{self.get_section_display()}: {self.key} = {self.value}"`.

### 3.6 `ProductBrochure` model (AC6)

**Inheritance:** `class ProductBrochure(TimestampedModel):`.

| Polje | Tip | Constraint | Translatable |
|---|---|---|---|
| `product` | `ForeignKey(Product, on_delete=CASCADE, related_name="brochures", verbose_name=_("Proizvod"))` | required | no |
| `pdf_file` | `FileField(_("PDF brošura"), upload_to="products/brochures/", max_length=255)` | **REQUIRED** | no |
| `cover_thumbnail_image` | `ImageField(_("Cover thumbnail"), upload_to="products/brochure_covers/", max_length=255, blank=True, null=True)` | optional (auto-gen u 2.4 signal) | no |
| `title` | `CharField(_("Naslov brošure"), max_length=200, blank=True)` | optional | **YES** |

**Meta:**

```python
class Meta:
    ordering = ["product", "id"]
    verbose_name = _("Brošura")
    verbose_name_plural = _("Brošure")
    indexes = [
        models.Index(fields=["product"], name="products_brochure_product_idx"),
    ]
```

**`__str__`** → `self.title` ako postoji; inače `gettext_lazy` printf-style fallback: `_("Brošura — %(name)s") % {"name": self.product.name}`.

### 3.7 `ProductTestimonial` model (AC7)

**Inheritance:** `class ProductTestimonial(TimestampedModel):`.

| Polje | Tip | Constraint | Translatable |
|---|---|---|---|
| `product` | `ForeignKey(Product, on_delete=CASCADE, related_name="testimonials", verbose_name=_("Proizvod"))` | required | no |
| `photo` | `ImageField(_("Fotografija"), upload_to="products/testimonials/", max_length=255, blank=True, null=True)` | optional | no |
| `quote` | `TextField(_("Citat"), validators=[MaxLengthValidator(50000)])` | required, hard cap 50000 chars (SECURITY M2 iter-1) | **YES** |
| `author_name` | `CharField(_("Ime autora"), max_length=120)` | required | no (lično ime) |
| `location` | `CharField(_("Lokacija"), max_length=120, blank=True)` | optional | **YES** |
| `order` | `PositiveSmallIntegerField(_("Redosled"), default=0, db_index=True)` | — | no |

**Meta:**

```python
class Meta:
    ordering = ["order", "id"]
    verbose_name = _("Testimonijal")
    verbose_name_plural = _("Testimonijali")
    indexes = [
        models.Index(fields=["product", "order"],
                     name="products_testimonial_product_order_idx"),
    ]
```

**`__str__`** → `f"{self.author_name} — {self.product.name}"`.

### 3.8 `ProductSimilar` model (AC8)

**Inheritance:** `class ProductSimilar(TimestampedModel):` — pure relational (no translatable fields).

| Polje | Tip | Constraint | Translatable |
|---|---|---|---|
| `product` | `ForeignKey(Product, on_delete=CASCADE, related_name="outgoing_similars", verbose_name=_("Proizvod"))` | required | no |
| `related_product` | `ForeignKey(Product, on_delete=CASCADE, related_name="incoming_similars", verbose_name=_("Sličan proizvod"))` | required, NE auto-simetrična (PR-D5) | no |
| `order` | `PositiveSmallIntegerField(_("Redosled"), default=0, db_index=True)` | — | no |

**Meta:**

```python
class Meta:
    ordering = ["product", "order", "id"]
    verbose_name = _("Sličan proizvod")
    verbose_name_plural = _("Slični proizvodi")
    constraints = [
        models.UniqueConstraint(
            fields=["product", "related_product"],
            name="products_similar_pair_unique",
        ),
        models.CheckConstraint(
            check=~models.Q(product=models.F("related_product")),
            name="products_similar_no_self_reference",
        ),
    ]
    indexes = [
        models.Index(fields=["product", "order"],
                     name="products_similar_product_order_idx"),
    ]
```

**`__str__`** → `f"{self.product.name} → {self.related_product.name}"`.

**`clean()`** → ako `self.product_id == self.related_product_id` (oba ne-None) → `raise ValidationError(_("Sličan proizvod ne sme biti isti kao izvorni proizvod."))`. Bez `field` ključa → poruka ide pod `__all__` u `message_dict`.

**NEMA `save()` override** (intentional — vidi Dev Note "ProductSimilar save() bez full_clean() — dva test path-a"). Posledica: `Model.objects.create()` BYPASS-uje `clean()` i hita DB-level CheckConstraint → `IntegrityError`. `clean()` se aktivira SAMO kada caller eksplicitno pozove `instance.full_clean()` ili kroz admin form `is_valid()`.

**NEMA `get_absolute_url()`** (junction entity).

---

## 4. `apps/products/translation.py` (AC9)

**Translation scope (PR-D7):** 6 modela / 11 polja (expansion of epics.md 4-model spec — see PR-D7 rationale).

```python
from modeltranslation.translator import TranslationOptions, register

from apps.products.models import (
    Product,
    ProductBrochure,
    ProductImage,
    ProductSpecification,
    ProductTestimonial,
    ProductVariant,
)


@register(Product)
class ProductTranslationOptions(TranslationOptions):
    fields = ("name", "description", "key_features")


@register(ProductImage)
class ProductImageTranslationOptions(TranslationOptions):
    fields = ("alt_text",)


@register(ProductVariant)
class ProductVariantTranslationOptions(TranslationOptions):
    fields = ("name", "description")


@register(ProductSpecification)
class ProductSpecificationTranslationOptions(TranslationOptions):
    fields = ("key", "value")


@register(ProductBrochure)
class ProductBrochureTranslationOptions(TranslationOptions):
    fields = ("title",)


@register(ProductTestimonial)
class ProductTestimonialTranslationOptions(TranslationOptions):
    fields = ("quote", "location")
```

**`ProductSimilar` IZUZET** — nema translatable polja.

**Generisana virtuelna polja (per 3 jezika sr/hu/en iz Story 1.4 LANGUAGES):**

| Model | Polja | Translatable kolone |
|---|---|---|
| Product | name, description, key_features | name_sr/hu/en, description_sr/hu/en, key_features_sr/hu/en |
| ProductImage | alt_text | alt_text_sr/hu/en |
| ProductVariant | name, description | name_sr/hu/en, description_sr/hu/en |
| ProductSpecification | key, value | key_sr/hu/en, value_sr/hu/en |
| ProductBrochure | title | title_sr/hu/en |
| ProductTestimonial | quote, location | quote_sr/hu/en, location_sr/hu/en |

**Aggregate:** 11 translatable polja × 3 jezika = **33 dodatne kolone** u `0001_initial.py`.

---

## 5. `apps/products/admin.py` (AC11)

```python
from django.contrib import admin

from apps.products.models import (
    Product,
    ProductBrochure,
    ProductImage,
    ProductSimilar,
    ProductSpecification,
    ProductTestimonial,
    ProductVariant,
)

admin.site.register(Product)
admin.site.register(ProductImage)
admin.site.register(ProductVariant)
admin.site.register(ProductSpecification)
admin.site.register(ProductBrochure)
admin.site.register(ProductTestimonial)
admin.site.register(ProductSimilar)
```

**Bare register** (NE `TranslationAdmin`) → sr/hu/en tabovi se NE renderuju u 2.2 (PR-11 / C1 trap). Pun `TranslationAdmin` je Story 8.6 scope.

---

## 6. `config/settings/base.py` — delta

**Diff 1 — `INSTALLED_APPS` APENDUJ jednu liniju POSLE `"apps.brands",`:**

```python
INSTALLED_APPS = [
    "modeltranslation",            # MORA PRVI — ne reorder
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_htmx",
    "django_bootstrap5",
    "apps.core",
    "apps.brands",                  # Story 2.1
    "apps.products",                # NOVO Story 2.2 — APENDOVAN POSLE brands per dep rule
]
```

**Diff 2 — POSLE `LANGUAGES = [...]` blok (Story 1.4 lokacija):**

```python
MODELTRANSLATION_FALLBACK_LANGUAGES = ("sr",)  # Story 2.2 — architecture-defensive locale fallback chain
```

**KRITIČNO:** NE reorder-uj postojeći `INSTALLED_APPS` redosled — `modeltranslation` MORA ostati PRVI (Story 2.1 D2 / Gotcha BR-2).

---

## 7. Migracija `apps/products/migrations/0001_initial.py`

**Backend-agnostic asercija (per 2.1 CRIT-4):** strukturalna, NE column-type literal.

**Auto-generated dependencies (auto-detected):**

```python
dependencies = [
    ("brands", "0001_initial"),
]
```

**Expected operacije:**

- **7 × `CreateModel`:** Product, ProductImage, ProductVariant, ProductSpecification, ProductBrochure, ProductTestimonial, ProductSimilar
- **Translation field-ovi (33 dodatne kolone):**
  - Product: `name_sr/hu/en`, `description_sr/hu/en`, `key_features_sr/hu/en` (9)
  - ProductImage: `alt_text_sr/hu/en` (3)
  - ProductVariant: `name_sr/hu/en`, `description_sr/hu/en` (6)
  - ProductSpecification: `key_sr/hu/en`, `value_sr/hu/en` (6)
  - ProductBrochure: `title_sr/hu/en` (3)
  - ProductTestimonial: `quote_sr/hu/en`, `location_sr/hu/en` (6)
- **`AddIndex` (≥ 8):** 3 na Product + 1 svako na Image/Variant/Spec/Brochure/Testimonial/Similar
- **`AddConstraint` (2):**
  - `products_similar_pair_unique` (UniqueConstraint)
  - `products_similar_no_self_reference` (CheckConstraint)
- **FK `on_delete`:**
  - `PROTECT` (3): `Product.brand`, `Product.series`, `Product.subcategory`
  - `CASCADE` (7): `ProductImage.product`, `ProductVariant.product`, `ProductSpecification.product`, `ProductBrochure.product`, `ProductTestimonial.product`, `ProductSimilar.product`, `ProductSimilar.related_product`

---

## 8. Test infrastructure (RED phase pattern)

Story 2.2 testovi prate Story 2.1 pattern:

- `pytestmark = pytest.mark.django_db` na module level za DB-based testovi
- Plain `Model.objects.create()` (factory_boy NIJE u dev deps)
- Inline `_create_brand()` / `_create_subcategory_chain()` / `_create_product()` helper-i u test fajlu
- `@pytest.mark.skip(reason="URLs come in Story 2.7 ...")` za `get_absolute_url` testove
- `from django.core.files.uploadedfile import SimpleUploadedFile` za `ProductImage.image` REQUIRED stub
- `from django.core.files.base import ContentFile` za `ProductBrochure.pdf_file` REQUIRED stub
- `@pytest.mark.django_db(transaction=True)` za testove koji proveravaju DB-level CheckConstraint IntegrityError
- ValidationError asercije koriste `in` membership na `exc_info.value.message_dict` (NE equality)

### 8.1 Test summary mapping AC → test files

| AC | Test file | Tests |
|---|---|---|
| AC1 (app skeleton) | `apps/products/tests/test_apps.py` | `test_products_config_name_*` |
| AC1 (config delta) | `apps/products/tests/test_models.py` | `test_apps_products_in_installed_apps`, `test_modeltranslation_fallback_languages_setting` |
| AC2 (Product) | `apps/products/tests/test_models.py` | `test_product_*` |
| AC3 (ProductImage) | `apps/products/tests/test_models.py` | `test_product_image_*` |
| AC4 (ProductVariant) | `apps/products/tests/test_models.py` | `test_product_variant_*` |
| AC5 (ProductSpecification) | `apps/products/tests/test_models.py` | `test_product_specification_*` |
| AC6 (ProductBrochure) | `apps/products/tests/test_models.py` | `test_product_brochure_*` |
| AC7 (ProductTestimonial) | `apps/products/tests/test_models.py` | `test_product_testimonial_*` |
| AC8 (ProductSimilar) | `apps/products/tests/test_models.py` | `test_product_similar_*` |
| AC9 (translation) | `apps/products/tests/test_models.py` | `test_translation_*`, `test_product_translation_fields_*`, `test_modeltranslation_fallback_*` |
| AC10 (migration) | Manual review (per story spec § AC10 checklist) | — |
| AC11 (admin) | OUT OF SCOPE (mirror 2.1 — admin stub nema test) | — |
| AC12 (boundary) | `tests/integration/test_app_boundaries.py` | `test_brands_does_not_import_products`, `test_products_does_not_import_catalog` |
| AC13 (test coverage) | All test files above | — |

---

**End of Interface Contract 2.2**
