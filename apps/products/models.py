"""Story 2.2 — Product i related modeli (Epic 2 content layer).

Sva 7 modela slede 2.1 pattern:
- Eksplicitni `on_delete` + `related_name` na svim FK-ovima
- Product nasleđuje SluggedModel + TimestampedModel iz apps.core.models
- Cross-app FK-ovi (Brand, Series, Subcategory) kroz string lazy reference
- Meta.indexes sa imenima `<table>_<columns>_idx`
- `save()` override sa eksplicitnim redosledom: slug auto-gen → full_clean() → super().save()
- `gettext_lazy as _` za sve user-facing string-ove

Decision references (vidi 2-2-product-i-related-modeli.md):
- PR-D1 — apps.products POSLE apps.brands u INSTALLED_APPS (jednosmerna zavisnost)
- PR-D2 — Product.series nullable (Jeegee/HZM nemaju series koncept)
- PR-D3 — Product.subcategory nullable (top-tier traktori nemaju subcategory drill-down)
- PR-D4 — paralelno is_published + status (epic spec eksplicitni; admin sync opciono u 8.6)
- PR-D5 — ProductSimilar je directional (NE auto-simetrična)
- PR-D7 — translation scope: 6 entiteta / 11 polja (ProductImage.alt_text + ProductVariant
  name/description dodato vs epics.md 4-model spec — a11y + variant rendering rationale)

Out-of-scope za 2.2 (defer references):
- search_vector polje → Story 2.13 (zasebna migracija)
- MIME validation za upload polja → Story 2.3 (image) i 2.4 (PDF)
- post_save signal za ProductBrochure.cover_thumbnail → Story 2.4
- Custom managers (PublishedProductManager) → Story 2.6 (Brand Listing) je owner za
  apps/products/managers.py
- Views/urls/forms → Story 2.7/2.8/8.6
"""

from __future__ import annotations

from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.core.models import SluggedModel, TimestampedModel
from apps.core.utils import slugify_ascii

# Maksimum broj entry-ja u Product.key_features JSON listi (per AC2 + epics.md)
_PRODUCT_KEY_FEATURES_MAX = 3


# ARCHITECTURE NOTE (per Code Review iter-1 R5):
# _ProductIndex je referenciran BY DOTTED PATH iz apps/products/migrations/0001_initial.py
# (kao `apps.products.models._ProductIndex(...)` u svakom AddIndex pozivu). Bilo kakav
# rename/relocation ove klase ruši migration replay na fresh DB setup-u.
# Cleanup opcije za buduću Story 2.x naming PR:
#   (a) Premestiti u apps/core/indexes.py kao CoricIndex (shared utility)
#   (b) Vratiti se na vanilla models.Index sa kraćim imenima (≤30 chars)
#   (c) Squashmigrations approach
# Do tada, _ProductIndex je load-bearing — tretirati kao public API.
class _ProductIndex(models.Index):
    """Project-local Index subclass sa proširenim max_name_length.

    Django default `Index.max_name_length = 30` zbog cross-database Oracle compat-a.
    Story 2.2 imena indeksa (`products_product_brand_status_idx` itd.) prate
    project-context.md § `<table>_<columns>_idx` konvenciju i prelaze 30 char-a
    (32-38 chars). Production DB je PostgreSQL (63-char identifier limit) + SQLite
    (no hard limit); Oracle / SQL Server NIJE u stack-u (project-context.md § Stack).
    Proširenje na 64 omogućava semantičke nazive bez kršenja `E034` system check-a.

    Vidi takođe `apps/brands/models.py` TODO komentar — Story 2.x cleanup može
    razmotriti skraćivanje `<app>_<model>_` prefiksa, ali to je rebranding konvencije
    koji utiče na sve postojeće migracije. Trenutni stance: zadržati eksplicitne
    nazive + proširiti max_name_length.
    """

    max_name_length = 64


# =============================================================================
# Product (AC2) — root content entity
# =============================================================================


class Product(SluggedModel, TimestampedModel):
    """Proizvod (traktor, mehanizacija, priključak) — root content entitet.

    Prvi konzument 2.1 D3 foundation (SluggedModel + TimestampedModel iz apps.core).
    Slug je globally unique (kroz SluggedModel mixin). FK-ovi ka brands sa eksplicitnim
    PROTECT on_delete (brand) i nullable PROTECT (series, subcategory) — vidi PR-D2/D3.

    File upload polja (main_image) BEZ MIME validation u Story 2.2 (Gotcha PR-3 —
    deferred to Story 2.3 image pipeline).
    """

    class ConditionChoice(models.TextChoices):
        NEW = "new", _("Novo")
        USED = "used", _("Polovno")

    class StatusChoice(models.TextChoices):
        DRAFT = "draft", _("Nacrt")
        PUBLISHED = "published", _("Objavljen")
        ARCHIVED = "archived", _("Arhiviran")

    brand = models.ForeignKey(
        "brands.Brand",
        on_delete=models.PROTECT,
        related_name="products",
        verbose_name=_("Brend"),
    )
    series = models.ForeignKey(
        "brands.Series",
        on_delete=models.PROTECT,
        related_name="products",
        null=True,
        blank=True,
        verbose_name=_("Serija"),
    )
    subcategory = models.ForeignKey(
        "brands.Subcategory",
        on_delete=models.PROTECT,
        related_name="products",
        null=True,
        blank=True,
        verbose_name=_("Potkategorija"),
    )
    name = models.CharField(_("Naziv"), max_length=200)
    # SECURITY (Code Review iter-1 M2): MaxLengthValidator 50000 char hard cap
    # protiv abuse-a admin Editor role-a (kreira se u Story 2.6/8.6). Forma će
    # postaviti tighter cap; ovo je belt-and-suspenders na model nivou ako se
    # forma bypass-uje. 50000 char ≈ 8000 reči ≈ 50 strana — plenty za opis.
    description = models.TextField(
        _("Opis"), blank=True, validators=[MaxLengthValidator(50000)]
    )
    key_features = models.JSONField(
        _("Ključne karakteristike"),
        default=list,
        blank=True,
    )
    main_image = models.ImageField(
        _("Glavna slika"),
        upload_to="products/main/",
        max_length=255,
        blank=True,
        null=True,
    )
    year = models.PositiveSmallIntegerField(_("Godina"), blank=True, null=True)
    price_eur = models.DecimalField(
        _("Cena (EUR)"),
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
    )
    horse_power = models.PositiveSmallIntegerField(
        _("Konjska snaga"), blank=True, null=True
    )
    # NOTE I4: NEMA db_index=True — composite index `products_product_condition_pub_idx`
    # pokriva leftmost-prefix scan na (condition, is_published).
    condition = models.CharField(
        _("Stanje"),
        max_length=10,
        choices=ConditionChoice.choices,
        default=ConditionChoice.NEW,
    )
    # NOTE I4: status ZADRŽAVA db_index=True jer NIJE leftmost u nijednom composite
    # index-u (`products_product_brand_status_idx` ima brand kao leftmost, status drugi).
    status = models.CharField(
        _("Status"),
        max_length=12,
        choices=StatusChoice.choices,
        default=StatusChoice.DRAFT,
        db_index=True,
    )
    # NOTE I4: NEMA db_index=True — composite index `products_product_pub_created_idx`
    # ima `is_published` kao leftmost field.
    is_published = models.BooleanField(_("Objavljen"), default=False)
    # Story 2.13 (SM-D8) — search_vector ostaje UVEK NULL u v1 (annotation-at-query-time,
    # bez trigger/signal/save populacije). Field + GIN indeks su forward-compat skelet ka
    # materijalizovanom (trigger) pristupu u v1.1. Runtime FTS upit ide kroz annotation
    # alias `search` u apps/search/search.py — NE kroz ovu NULL kolonu (C3/SM-D8).
    search_vector = SearchVectorField(_("Search vektor"), null=True, editable=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Proizvod")
        verbose_name_plural = _("Proizvodi")
        indexes = [
            _ProductIndex(
                fields=["is_published", "-created_at"],
                name="products_product_pub_created_idx",
            ),
            _ProductIndex(
                fields=["brand", "status"],
                name="products_product_brand_status_idx",
            ),
            _ProductIndex(
                fields=["condition", "is_published"],
                name="products_product_condition_pub_idx",
            ),
            # Story 2.13 (SM-D20/C1) — GIN indeks na search_vector; ime 19 char ≤30
            # (Django Index.max_name_length). NE _ProductIndex subclass (on je models.Index).
            GinIndex(fields=["search_vector"], name="products_search_gin"),
        ]

    def __str__(self) -> str:
        # PERFORMANCE NOTE (Code Review iter-1 R6): pristupanje `self.brand.name`
        # trigger-uje extra SELECT na brands_brand tabelu ako caller nije pozvao
        # `.select_related("brand")` pre iteracije. Story 8.6 ProductAdmin MORA
        # postaviti `list_select_related = ["brand"]` da izbegne N+1 u changelist-u.
        return f"{self.brand.name} — {self.name}"

    def clean(self) -> None:
        """Validira key_features (base + translated varijante) — list-of-str, max 3.

        Belt-and-suspenders dizajn: iterira sve LANGUAGES i validira svaku translated
        varijantu (`key_features_sr/_hu/_en`) + base accessor. Admin više ne može
        upisati 5 stavki u `key_features_hu` bez ValidationError.
        """
        super().clean()

        # Validate translated varijante kroz settings.LANGUAGES iteraciju.
        # NOTE I-iter2-6: `_label` umesto single `_` — `_` u modulu je već
        # `gettext_lazy as _`; loop unpacking u `_` bi shadow-ovao gettext_lazy
        # unutar loop body-ja i prebio `_("Mora biti lista.")` pozive ispod.
        for lang_code, _label in settings.LANGUAGES:  # noqa: B007
            attr = f"key_features_{lang_code}"
            value = getattr(self, attr, None) or []
            if value:
                if not isinstance(value, list):
                    raise ValidationError({attr: _("Mora biti lista.")})
                for item in value:
                    if not isinstance(item, str):
                        raise ValidationError(
                            {attr: _("Svaka stavka mora biti string.")}
                        )
                if len(value) > _PRODUCT_KEY_FEATURES_MAX:
                    raise ValidationError(
                        {attr: _("Najviše 3 ključne karakteristike.")}
                    )

        # Belt-and-suspenders: validate base accessor too — kovers programmatic set
        # bez language context-a (npr. raw .key_features = [...] u skripti).
        base_value = self.key_features or []
        if base_value:
            if not isinstance(base_value, list):
                raise ValidationError({"key_features": _("Mora biti lista.")})
            for item in base_value:
                if not isinstance(item, str):
                    raise ValidationError(
                        {"key_features": _("Svaka stavka mora biti string.")}
                    )
            if len(base_value) > _PRODUCT_KEY_FEATURES_MAX:
                raise ValidationError(
                    {"key_features": _("Najviše 3 ključne karakteristike.")}
                )

    def full_clean(self, *args, **kwargs):
        """Auto-generate slug iz name PRE Django field-level validation.

        ⚠️ NIKAD ne pozivaj self.clean() direktno iz ovog override-a (I10) —
        super().full_clean(*args, **kwargs) već automatski poziva self.clean()
        kao deo svog standardnog flow-a. Double-poziv → duplikacija validation
        errors.
        """
        if not self.slug and self.name:
            self.slug = slugify_ascii(self.name)
        super().full_clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        """Auto-generate slug iz name + full_clean() (matches Story 2.1 CRIT-2 pattern).

        ⚠️ NE refaktoriši — duplikacija slug auto-gen logike sa full_clean() override-om
        je NAMERNA (I5). Story 2.1 Pattern A defensive guard: caller može pozvati
        full_clean() na unsaved instance bez slug-a i validacija će proći; save() path
        remains single source of truth za slug auto-gen pri DB persist-u.
        """
        if not self.slug and self.name:
            self.slug = slugify_ascii(self.name)
        self.full_clean()
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        """URL pattern dolazi u Story 2.7 — raise-uje NoReverseMatch dotle (Gotcha PR-5)."""
        return reverse("products:detail", kwargs={"slug": self.slug})


# =============================================================================
# ProductImage (AC3) — galerija slika
# =============================================================================


class ProductImage(TimestampedModel):
    """Galerijska slika proizvoda (Story 2.7 Product Detail — <picture> srcset)."""

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name=_("Proizvod"),
    )
    image = models.ImageField(
        _("Slika"),
        upload_to="products/gallery/",
        max_length=255,
    )
    order = models.PositiveSmallIntegerField(_("Redosled"), default=0, db_index=True)
    alt_text = models.CharField(_("Alt tekst"), max_length=200, blank=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = _("Slika proizvoda")
        verbose_name_plural = _("Slike proizvoda")
        indexes = [
            _ProductIndex(
                fields=["product", "order"],
                name="products_image_product_order_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.product.name} — slika {self.order}"


# =============================================================================
# ProductVariant (AC4) — varijante (Sa kabinom / Bez kabine, etc.)
# =============================================================================


class ProductVariant(TimestampedModel):
    """Varijanta proizvoda (npr. 'Sa kabinom', 'Bez kabine', 'AC paket').

    Story 2.7 Lightbox zoom card; translatable name + description (PR-D7).
    """

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants",
        verbose_name=_("Proizvod"),
    )
    name = models.CharField(_("Naziv"), max_length=200)
    code = models.CharField(_("Kod"), max_length=50, blank=True)
    image = models.ImageField(
        _("Slika varijante"),
        upload_to="products/variants/",
        max_length=255,
        blank=True,
        null=True,
    )
    # SECURITY (Code Review iter-2 L1): MaxLengthValidator 50000 char hard cap
    # protiv abuse-a admin Editor role-a (kreira se u Story 2.6/8.6). Mirror
    # Product.description rationale — belt-and-suspenders konzistentnost za sve
    # 3 translatable TextField polja (Product.description, ProductTestimonial.quote,
    # ProductVariant.description).
    description = models.TextField(
        _("Opis"), blank=True, validators=[MaxLengthValidator(50000)]
    )
    order = models.PositiveSmallIntegerField(_("Redosled"), default=0, db_index=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = _("Varijanta")
        verbose_name_plural = _("Varijante")
        indexes = [
            _ProductIndex(
                fields=["product", "order"],
                name="products_variant_product_order_idx",
            ),
        ]

    def __str__(self) -> str:
        return self.name


# =============================================================================
# ProductSpecification (AC5) — akordion specs (Motor/Transmisija/Hidraulika/Ostalo)
# =============================================================================


class ProductSpecification(TimestampedModel):
    """Tehnička specifikacija (key/value pair grupisan po section)."""

    class SpecSection(models.TextChoices):
        MOTOR = "motor", _("Motor")
        TRANSMISIJA = "transmisija", _("Transmisija")
        HIDRAULIKA = "hidraulika", _("Hidraulika")
        OSTALO = "ostalo", _("Ostalo")

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="specifications",
        verbose_name=_("Proizvod"),
    )
    section = models.CharField(
        _("Sekcija"),
        max_length=20,
        choices=SpecSection.choices,
        default=SpecSection.OSTALO,
        db_index=True,
    )
    key = models.CharField(_("Naziv specifikacije"), max_length=200)
    value = models.CharField(_("Vrednost"), max_length=200)
    order = models.PositiveSmallIntegerField(_("Redosled"), default=0, db_index=True)

    class Meta:
        # NOTE I3: NE uključuj "section" u ordering — alphabetical sort daje
        # hidraulika → motor → ostalo → transmisija što je SUPROTNO traženom
        # display order-u (Motor → Transmisija → Hidraulika → Ostalo). Display
        # order će biti primenjen u Story 2.7 view-layer kroz Case/When annotation.
        ordering = ["product", "order", "id"]
        verbose_name = _("Specifikacija")
        verbose_name_plural = _("Specifikacije")
        indexes = [
            _ProductIndex(
                fields=["product", "section", "order"],
                name="products_spec_product_section_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.get_section_display()}: {self.key} = {self.value}"


# =============================================================================
# ProductBrochure (AC6) — PDF brošure + cover thumbnail (auto-gen u 2.4)
# =============================================================================


class ProductBrochure(TimestampedModel):
    """PDF brošura sa cover thumbnail-om (auto-gen u Story 2.4 post_save signal)."""

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="brochures",
        verbose_name=_("Proizvod"),
    )
    pdf_file = models.FileField(
        _("PDF brošura"),
        upload_to="products/brochures/",
        max_length=255,
    )
    cover_thumbnail_image = models.ImageField(
        _("Cover thumbnail"),
        upload_to="products/brochure_covers/",
        max_length=255,
        blank=True,
        null=True,
    )
    title = models.CharField(_("Naslov brošure"), max_length=200, blank=True)

    class Meta:
        ordering = ["product", "id"]
        verbose_name = _("Brošura")
        verbose_name_plural = _("Brošure")
        indexes = [
            _ProductIndex(
                fields=["product"],
                name="products_brochure_product_idx",
            ),
        ]

    def __str__(self) -> str:
        if self.title:
            return self.title
        # NOTE I-iter3-6: fallback string OBAVEZNO kroz `gettext_lazy` (printf-style
        # `% {name: ...}` format je idiomatski pattern za gettext_lazy interpolaciju;
        # f-string bi eager-evaluovao lazy proxy i izgubio locale awareness).
        return _("Brošura — %(name)s") % {"name": self.product.name}


# =============================================================================
# ProductTestimonial (AC7) — "Iz prve ruke" slider
# =============================================================================


class ProductTestimonial(TimestampedModel):
    """Testimonijal vlasnika ("Iz prve ruke" slider u Story 2.7)."""

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="testimonials",
        verbose_name=_("Proizvod"),
    )
    photo = models.ImageField(
        _("Fotografija"),
        upload_to="products/testimonials/",
        max_length=255,
        blank=True,
        null=True,
    )
    # SECURITY (Code Review iter-1 M2): MaxLengthValidator 50000 char hard cap
    # protiv abuse-a admin Editor role-a. Mirror Product.description rationale.
    quote = models.TextField(_("Citat"), validators=[MaxLengthValidator(50000)])
    author_name = models.CharField(_("Ime autora"), max_length=120)
    location = models.CharField(_("Lokacija"), max_length=120, blank=True)
    order = models.PositiveSmallIntegerField(_("Redosled"), default=0, db_index=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = _("Testimonijal")
        verbose_name_plural = _("Testimonijali")
        indexes = [
            _ProductIndex(
                fields=["product", "order"],
                name="products_testimonial_product_order_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.author_name} — {self.product.name}"


# =============================================================================
# ProductSimilar (AC8) — manual override za FR-20 hibrid logiku (directional)
# =============================================================================


class ProductSimilar(TimestampedModel):
    """Slični proizvod (manual override za FR-20).

    Directional (NE auto-simetrična) per PR-D5. UniqueConstraint na (product,
    related_product) sprečava duplikat pair; CheckConstraint sprečava self-reference
    na DB nivou. Clean() override raise-uje friendly poruku za admin forme; NEMA
    save() override (Django default save() NE poziva full_clean()) — Model.objects.create()
    BYPASS-uje clean() i hita DB-level CheckConstraint direktno (vidi IMP-iter4-4
    Dev Note "ProductSimilar save() bez full_clean() — dva test path-a").
    """

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="outgoing_similars",
        verbose_name=_("Proizvod"),
    )
    related_product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="incoming_similars",
        verbose_name=_("Sličan proizvod"),
    )
    order = models.PositiveSmallIntegerField(_("Redosled"), default=0, db_index=True)

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
                condition=~models.Q(product=models.F("related_product")),
                name="products_similar_no_self_reference",
            ),
        ]
        indexes = [
            _ProductIndex(
                fields=["product", "order"],
                name="products_similar_product_order_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.product.name} → {self.related_product.name}"

    def clean(self) -> None:
        """Validira no-self-reference (defensive — DB CheckConstraint je primarno).

        ValidationError bez polja → poruka ide pod __all__ key u message_dict.
        NEMA save() override — Django default save() NE poziva clean() automatski;
        objects.create() BYPASS-uje clean() i hita DB-level CheckConstraint direktno.
        """
        super().clean()
        if self.product_id is not None and self.related_product_id is not None:
            if self.product_id == self.related_product_id:
                raise ValidationError(
                    _("Sličan proizvod ne sme biti isti kao izvorni proizvod.")
                )
