"""Story 2.1 — Brand, Series, Category, Subcategory modeli (Epic 2 foundation).

Sva 4 modela slede pattern:
- Eksplicitni `on_delete` + `related_name` na svim FK-ovima
- ASCII slug discipline (slugify_ascii helper iz apps.core.utils)
- Meta.indexes sa imenima `<table>_<columns>_idx`
- `save()` override sa eksplicitnim redosledom: slug auto-gen → full_clean() → super().save()
- `gettext_lazy as _` za sve user-facing string-ove

Decision references (vidi 2-1-brand-series-category-subcategory-modeli.md):
- D2 — modeltranslation registracija auto-discovery
- D3 — eksplicitan slug umesto SluggedModel mixin (per-scope vs global uniqueness mismatch)
- D4 — Subcategory chain depth MAX 3 nivoa (FR-38 disambiguacija)
- D5 — JSONField (Django 5.2 native, NE postgres.fields)
- D6 — TextChoices za CategoryScope + LayoutMode (locale-aware labels)
- D7 — Category.slug globally unique (Series.slug per-brand)
- D8 — icon = CharField (Bootstrap Icons class), NE ImageField
- D9 — Subcategory.category CASCADE (NE PROTECT)
- D10 — Subcategory depth validation kroz clean() (NE pre_save signal)
- D14 — File upload MIME validation deferred to Story 2.3/2.4

NOTE on save()/full_clean() pattern (CRIT-2 iter-2 fix + Dev Review iter-1 clarification):
Each model overrides BOTH save() and full_clean() to enforce slug auto-gen + validation.
save() pattern: slug auto-gen → full_clean → super().save (per CRIT-2).
full_clean() override is defensive — allows callers to invoke full_clean() on unsaved
instances without explicit slug (test suite requires this for clean() method testing).
The save() override remains the single source of truth for slug auto-gen on .save() path.

TODO Story 2.x cleanup: modeltranslation patch_indexes auto-generates 3 variants
for translatable fields (name_sr/_hu/_en). Some index names exceed Django 30-char
limit and get hash-renamed (UserWarning at startup). Consider shortening base
names from "brands_brand_*" prefix to "brand_*" in a future cleanup PR.
"""

from __future__ import annotations

import re

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.core.utils import slugify_ascii

# Hex color regex za Brand.brand_color (#RRGGBB format)
_HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")

# Max Subcategory chain dubina (per Decision D4)
_SUBCATEGORY_MAX_DEPTH = 3

# Max Brand.statistics list size (per FR-37 "statistike do 4")
_BRAND_STATISTICS_MAX = 4


# =============================================================================
# Brand (AC2)
# =============================================================================


class Brand(models.Model):
    """Brend (John Deere, Agri Tracking, Jeegee, ...) — root taksonomije kataloga.

    File upload polja (logo, hero_image, catalog_pdf) BEZ MIME validation u Story 2.1
    (Gotcha BR-3 / BR-11 / Decision D14 — deferred to Story 2.3 image pipeline i
    Story 2.4 PDF cover thumbnail generator).
    """

    name = models.CharField(_("Naziv"), max_length=120)
    slug = models.SlugField(_("Slug"), max_length=140, unique=True, db_index=True)
    logo = models.ImageField(
        _("Logo"),
        upload_to="brands/logos/",
        max_length=255,
        blank=True,
        null=True,
    )
    hero_image = models.ImageField(
        _("Hero slika"),
        upload_to="brands/heroes/",
        max_length=255,
        blank=True,
        null=True,
    )
    description = models.TextField(_("Opis"), blank=True)
    slogan = models.CharField(_("Slogan"), max_length=200, blank=True)
    statistics = models.JSONField(_("Statistike"), default=list, blank=True)
    catalog_pdf = models.FileField(
        _("Katalog (PDF)"),
        upload_to="brands/catalogs/",
        max_length=255,
        blank=True,
        null=True,
    )
    brand_color = models.CharField(_("Brend boja"), max_length=7, blank=True)
    # NEMA db_index=True — composite index (is_coming_soon, name) pokriva
    # leftmost-prefix scan (IMP-3).
    is_coming_soon = models.BooleanField(_("Uskoro"), default=False)
    created_at = models.DateTimeField(_("Kreiran"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Ažuriran"), auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = _("Brend")
        verbose_name_plural = _("Brendovi")
        indexes = [
            models.Index(
                fields=["is_coming_soon", "name"],
                name="brands_brand_coming_name_idx",
            ),
        ]

    def __str__(self) -> str:
        return self.name

    def clean(self) -> None:
        """Validacija brand_color hex format + statistics list-of-dict + max 4 entries."""
        super().clean()

        # brand_color hex validation (blank=True honored — CRIT-3 fix)
        if self.brand_color and not _HEX_COLOR_RE.match(self.brand_color):
            raise ValidationError({"brand_color": _("Hex format mora biti #RRGGBB.")})

        # statistics soft shape + max 4 (IMP-10)
        if self.statistics:
            if not isinstance(self.statistics, list):
                raise ValidationError({"statistics": _("Mora biti lista.")})
            for item in self.statistics:
                if not isinstance(item, dict):
                    raise ValidationError(
                        {"statistics": _("Svaka stavka mora biti dict.")}
                    )
            if len(self.statistics) > _BRAND_STATISTICS_MAX:
                raise ValidationError(
                    {"statistics": _("Statistike ne smeju imati više od 4 stavke.")}
                )

    def full_clean(self, *args, **kwargs):
        """Auto-generate slug iz name PRE Django field-level validation.

        Ovaj pattern omogućava direktan poziv `brand.full_clean()` na unsaved
        instance sa name ali bez slug-a — slug se auto-generiše umesto da baci
        ValidationError za slug.blank=False.
        """
        if not self.slug and self.name:
            self.slug = slugify_ascii(self.name)
        super().full_clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        """Auto-generate slug iz name + full_clean() (CRIT-2 iter-2 pattern)."""
        if not self.slug and self.name:
            self.slug = slugify_ascii(self.name)
        self.full_clean()
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        """URL pattern dolazi u Story 2.6 — raise-uje NoReverseMatch dotle."""
        return reverse("brands:detail", kwargs={"slug": self.slug})


# =============================================================================
# Series (AC3)
# =============================================================================


class Series(models.Model):
    """Serija modela unutar brenda (npr. John Deere — 8R Serija)."""

    class LayoutMode(models.TextChoices):
        GRID = "grid", _("Grid")
        EXTENDED = "extended", _("Extended")

    brand = models.ForeignKey(
        "brands.Brand",
        on_delete=models.PROTECT,
        related_name="series",
        verbose_name=_("Brend"),
    )
    name = models.CharField(_("Naziv"), max_length=120)
    slug = models.SlugField(_("Slug"), max_length=140, db_index=True)
    description = models.TextField(_("Opis"), blank=True)
    layout_mode = models.CharField(
        _("Režim prikaza"),
        max_length=10,
        choices=LayoutMode.choices,
        default=LayoutMode.GRID,
    )
    display_order = models.PositiveSmallIntegerField(
        _("Redosled prikaza"), default=0, db_index=True
    )
    created_at = models.DateTimeField(_("Kreirana"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Ažurirana"), auto_now=True)

    class Meta:
        # IMP-5: NO brand__name JOIN — brand-aware sort je view-layer concern
        ordering = ["display_order", "name"]
        verbose_name = _("Serija")
        verbose_name_plural = _("Serije")
        constraints = [
            models.UniqueConstraint(
                fields=["brand", "slug"],
                name="brands_series_brand_slug_unique",
            ),
        ]
        indexes = [
            models.Index(
                fields=["brand", "display_order"],
                name="brands_series_brand_order_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.brand.name} — {self.name}"

    def full_clean(self, *args, **kwargs):
        """Auto-generate slug iz name PRE Django field-level validation."""
        if not self.slug and self.name:
            self.slug = slugify_ascii(self.name)
        super().full_clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        """Auto-generate slug iz name pre full_clean() (CRIT-2 iter-2 pattern)."""
        if not self.slug and self.name:
            self.slug = slugify_ascii(self.name)
        self.full_clean()
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        """URL pattern dolazi u Story 2.6."""
        return reverse(
            "brands:series_detail",
            kwargs={"brand_slug": self.brand.slug, "series_slug": self.slug},
        )


# =============================================================================
# Category (AC4)
# =============================================================================


class Category(models.Model):
    """Top-level taksonomija — TRAKTORI ili MEHANIZACIJA scope.

    Slug je globally unique (Decision D7) — URL pattern je `/<is_for>/<slug>/`.
    """

    class CategoryScope(models.TextChoices):
        TRAKTORI = "traktori", _("Traktori")
        MEHANIZACIJA = "mehanizacija", _("Mehanizacija")

    name = models.CharField(_("Naziv"), max_length=120)
    slug = models.SlugField(_("Slug"), max_length=140, unique=True, db_index=True)
    description = models.TextField(_("Opis"), blank=True)
    is_for = models.CharField(
        _("Tip kataloga"),
        max_length=20,
        choices=CategoryScope.choices,
        db_index=True,
    )
    display_order = models.PositiveSmallIntegerField(
        _("Redosled prikaza"), default=0, db_index=True
    )
    icon = models.CharField(
        _("Ikona (Bootstrap Icons class)"), max_length=64, blank=True
    )
    created_at = models.DateTimeField(_("Kreirana"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Ažurirana"), auto_now=True)

    class Meta:
        ordering = ["is_for", "display_order", "name"]
        verbose_name = _("Kategorija")
        verbose_name_plural = _("Kategorije")
        indexes = [
            models.Index(
                fields=["is_for", "display_order"],
                name="brands_cat_scope_order_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.get_is_for_display()} — {self.name}"

    def full_clean(self, *args, **kwargs):
        """Auto-generate slug iz name PRE Django field-level validation."""
        if not self.slug and self.name:
            self.slug = slugify_ascii(self.name)
        super().full_clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        """Auto-generate slug iz name pre full_clean() (CRIT-2 iter-2 pattern)."""
        if not self.slug and self.name:
            self.slug = slugify_ascii(self.name)
        self.full_clean()
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        """Routes po is_for ka /traktori/<slug>/ ili /mehanizacija/<slug>/ URL pattern-u.

        URL pattern-i dolaze u Story 2.9/2.10/2.11.
        """
        if self.is_for == self.CategoryScope.TRAKTORI:
            return reverse("brands:category_traktori", kwargs={"slug": self.slug})
        return reverse("brands:category_mehanizacija", kwargs={"slug": self.slug})


# =============================================================================
# Subcategory (AC5, AC11)
# =============================================================================


class Subcategory(models.Model):
    """Hijerarhijski potkategorija unutar Category.

    Subcategory chain dubina je MAX 3 nivoa (per Decision D4 disambiguacija FR-38).
    Kombinovano sa Category root-om: Category → Sub L1 → Sub L2 → Sub L3 (4 nivoa stabla,
    3 nivoa Subcategory chain-a — matches Story 2.11 naziv).
    """

    category = models.ForeignKey(
        "brands.Category",
        on_delete=models.CASCADE,
        related_name="subcategories",
        verbose_name=_("Kategorija"),
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="children",
        blank=True,
        null=True,
        verbose_name=_("Roditeljska potkategorija"),
    )
    name = models.CharField(_("Naziv"), max_length=120)
    slug = models.SlugField(_("Slug"), max_length=140, db_index=True)
    description = models.TextField(_("Opis"), blank=True)
    icon = models.CharField(
        _("Ikona (Bootstrap Icons class)"), max_length=64, blank=True
    )
    display_order = models.PositiveSmallIntegerField(
        _("Redosled prikaza"), default=0, db_index=True
    )
    created_at = models.DateTimeField(_("Kreirana"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Ažurirana"), auto_now=True)

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
                name="brands_subcat_parent_order_idx",
            ),
        ]

    def __str__(self) -> str:
        return self.name

    def clean(self) -> None:
        """Validacija MAX 3 nivoa Subcategory chain dubine + circular reference guard.

        self counts kao level 1; chain traverse kroz self.parent computes depth.
        Circular reference (subcat.parent = subcat) detect-uje se kroz visited_ids set.
        """
        super().clean()

        depth = 1
        current = self.parent
        visited_ids: set[int | None] = set()

        # Edge case: self-referential parent (subcat.parent = subcat) — detect
        # cycle PRE entering loop. self.pk može biti None ako instance nije saved,
        # u tom slučaju koristimo id() kao stand-in.
        if current is not None and current.pk == self.pk and self.pk is not None:
            raise ValidationError(
                _("Subcategory hijerarhija ne sme imati cikličnu referencu.")
            )

        while current is not None:
            if current.pk in visited_ids:
                raise ValidationError(
                    _("Subcategory hijerarhija ne sme imati cikličnu referencu.")
                )
            visited_ids.add(current.pk)
            depth += 1
            if depth > _SUBCATEGORY_MAX_DEPTH:
                raise ValidationError(
                    _("Subcategory hijerarhija ne sme prelaziti 3 nivoa dubine.")
                )
            current = current.parent

    def full_clean(self, *args, **kwargs):
        """Auto-generate slug iz name PRE Django field-level validation."""
        if not self.slug and self.name:
            self.slug = slugify_ascii(self.name)
        super().full_clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        """Auto-generate slug iz name; full_clean() enforce-uje depth + slug validation."""
        if not self.slug and self.name:
            self.slug = slugify_ascii(self.name)
        self.full_clean()
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        """Subcategory URL pattern definiše se u Story 2.11."""
        # TODO Story 2.11: implement subcategory_path URL pattern sa variable depth
        raise NotImplementedError("Subcategory URL pattern defined in Story 2.11")

    # ------------------------------------------------------------------
    # AC11 helper metode
    # ------------------------------------------------------------------

    def get_ancestors_chain(self) -> list["Subcategory"]:
        """Vraća listu ancestors od najdaljeg parent-a do direct parent-a (BEZ self).

        Za L3 chain (L1 → L2 → L3), L3.get_ancestors_chain() vraća [L1, L2]
        (root-first order). Top-level Subcategory vraća praznu listu.
        """
        chain: list["Subcategory"] = []
        current = self.parent
        visited_ids: set[int | None] = set()
        while current is not None:
            if current.pk in visited_ids:
                break  # circular guard (defensive — clean() već blokira)
            visited_ids.add(current.pk)
            chain.append(current)
            current = current.parent
        return list(reversed(chain))

    def get_depth(self) -> int:
        """Vraća dubinu u Subcategory chain-u; top-level = 1, L3 = 3."""
        return len(self.get_ancestors_chain()) + 1
