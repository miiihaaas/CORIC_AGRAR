"""Story 8.6 — Product CRUD Admin sa Multi-locale.

Konvertuje ProductAdmin iz 6.1 stub-a (SeoWarningAdminMixin + ModelAdmin +
SeoMetaInline) u pun multi-locale CRUD:
- ProductAdmin → TranslationAdmin (sr/hu/en auto-tabovi za name/description/key_features).
- 6 inline-a: ProductImage/ProductVariant/ProductSpecification/ProductBrochure/
  ProductTestimonial = Translation*Inline; ProductSimilar = plain TabularInline
  (fk_name="product" — dva FK ka Product, G-11/G-12). SeoMetaInline OČUVAN (6.1 — G-8).
- Upload MIME/signature double-check za SVA upload polja DELEGIRAN na blessed
  media_pipeline.validate_image_mime/validate_pdf_mime (DRY + decompression-bomb guard;
  NE reimplementiraj — 8.4 M2 lekcija). ImageField polja override-ovana u plain FileField
  da srpska media_pipeline poruka ne bude pregažena Django Pillow to_python()-om (G-14).
- Publish-gate (8.6 NOVINA) u save_related: pre objave traži name_sr + ≥1 sliku galerije +
  ≥1 specifikaciju; graceful messages.error + revert-na-draft (NIKAD raise → 500; G-6).
- main_image_preview format_html (escape — G-15). search_fields=("name_sr",) realna
  kolona (G-1). list_select_related=("brand",) N+1 guard (G-10).

Reference patterns: apps/brands/admin.py (8.4 BrandAdmin TranslationAdmin + upload
double-check; 8.5 Category/Subcategory), apps/seo/admin.py (SeoMetaInline).
"""

from __future__ import annotations

from django import forms
from django.contrib import admin, messages
from django.db import models
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import (
    TranslationAdmin,
    TranslationStackedInline,
    TranslationTabularInline,
)

from apps.media_pipeline.pdf_utils import validate_pdf_mime
from apps.media_pipeline.utils import validate_image_mime
from apps.products.models import (
    Product,
    ProductBrochure,
    ProductImage,
    ProductSimilar,
    ProductSpecification,
    ProductTestimonial,
    ProductVariant,
)
from apps.seo.admin import SeoMetaInline, SeoWarningAdminMixin

# =============================================================================
# Upload size + MIME allowlists (UPPER_SNAKE_CASE — AC3 / G-13; mirror 8.4)
# =============================================================================
MAX_IMAGE_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 MB  — main_image, galerija, varijante...
MAX_PDF_UPLOAD_SIZE = 20 * 1024 * 1024  # 20 MB — brošure

# SVG namerno IZOSTAVLJEN (XSS vektor — OQ-4); gif izostavljen (v1 default).
ALLOWED_IMAGE_MIME_TYPES = ("image/jpeg", "image/png", "image/webp")
ALLOWED_PDF_MIME_TYPES = ("application/pdf",)


def _validate_image_field(value):
    """Delegira na blessed validate_image_mime sa lokalnim 8.6 konstantama.

    Pozivaoc je odgovoran za blank-skip PRE poziva (helper RAISE-uje na praznom
    uploadu — AC3 HARD RULE).
    """
    validate_image_mime(
        value,
        allowed_mimes=ALLOWED_IMAGE_MIME_TYPES,
        max_size_bytes=MAX_IMAGE_UPLOAD_SIZE,
    )


def _validate_pdf_field(value):
    validate_pdf_mime(
        value,
        allowed_mimes=ALLOWED_PDF_MIME_TYPES,
        max_size_bytes=MAX_PDF_UPLOAD_SIZE,
    )


def _relax_base_translation_fields(form):
    """Relaksira `required` na BAZNIM translatable poljima kad raw ModelForm vidi i `_sr`.

    modeltranslation u adminu (formfield_for_dbfield) promoviše default-lang polje (`_sr`)
    u required i skida required sa baznog polja. Taj swap se dešava kroz admin sloj, NE
    kroz raw ModelForm — pa kad se ModelForm bind-uje DIREKTNO (testovi), bazno `name`
    ostaje required i blokira validan `_sr`-only payload. Ovde repliciramo admin ponašanje:
    bazno polje postaje opciono (vrednost se sinhronizuje iz `_sr` kroz modeltranslation
    descriptor), `name_sr` ostaje BEZUSLOVNO obavezan (NE relaksiramo ga — AC9/M1).
    """
    for field in form._meta.model._meta.get_fields():
        # Restrict to concrete model fields — get_fields() also yields reverse
        # relations (ManyToOneRel etc.) whose `.name` == related_name; a reverse-rel
        # name could otherwise accidentally match a form field and relax it. Concrete
        # `models.Field` instances are the only ones with a translatable `_sr` twin.
        if not isinstance(field, models.Field):
            continue
        name = field.name
        sr_name = f"{name}_sr"
        if name in form.fields and sr_name in form.fields:
            form.fields[name].required = False


def _relax_fields_with_model_default(form):
    """Relaksira `required` na poljima koja imaju model-level default (npr. condition/status).

    Django ModelForm drži takva polja required kad je `blank=False` na modelu, iako default
    popunjava vrednost pri save-u. U adminu se renderuju sa initial-om (default izabran), pa
    submit uvek nosi vrednost; u raw direct-bind testu izostaju → relaksacija je bezbedna jer
    model default popunjava prazno polje.
    """
    for field in form._meta.model._meta.fields:
        if field.has_default() and field.name in form.fields:
            form.fields[field.name].required = False


# =============================================================================
# ProductAdminForm + inline ModelForm-ovi (upload double-check — AC3 / G-13 / G-14)
# =============================================================================


class ProductAdminForm(forms.ModelForm):
    """Glavni Product admin ModelForm sa main_image upload double-check-om.

    main_image je ImageField na modelu → override u plain FileField da Django
    Pillow to_python() ne pregazi srpsku media_pipeline poruku (G-14). clean_main_image
    delegira na validate_image_mime (blank-skip jer je main_image blank=True — AC3 HARD
    RULE: helper RAISE-uje na praznom uploadu).

    key_features/name_sr validacije OSTAJU u modelu (Product.clean() + modeltranslation
    required-promotion) — admin NE duplira (G-7).
    """

    # G-14: override ImageField → plain FileField (Pillow to_python() ne pregazi srpsku poruku).
    main_image = forms.FileField(required=False)

    class Meta:
        model = Product
        exclude = ()  # MANDATORY — Meta.fields ILI Meta.exclude (G-13)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _relax_base_translation_fields(self)  # name_sr ostaje required; bazno name opciono
        _relax_fields_with_model_default(self)  # condition/status imaju model default

    def clean_main_image(self):
        f = self.cleaned_data.get("main_image")
        if not f:
            return f  # graceful skip (main_image blank=True — AC3 HARD RULE)
        _validate_image_field(f)
        return f


class ProductImageInlineForm(forms.ModelForm):
    """ProductImage inline form — image je OBAVEZAN (NE skip; uvek validiraj)."""

    # G-14: override ImageField → FileField, ali required=True (model image NIJE blank).
    image = forms.FileField(required=True)

    class Meta:
        model = ProductImage
        exclude = ()  # G-13

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _relax_base_translation_fields(self)
        _relax_fields_with_model_default(self)

    def clean_image(self):
        f = self.cleaned_data.get("image")
        # OBAVEZNO polje (required=True, model image NIJE blank) — NEMA blank-skip;
        # validator se zove BEZUSLOVNO da bi srpska "Slika je prazna..." poruka isplivala
        # ako bi se required ikad relaksiralo (AC3).
        _validate_image_field(f)
        return f


class ProductVariantInlineForm(forms.ModelForm):
    """ProductVariant inline form — image je blank=True → blank-skip."""

    image = forms.FileField(required=False)  # G-14

    class Meta:
        model = ProductVariant
        exclude = ()  # G-13

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _relax_base_translation_fields(self)  # name_sr required; bazno name opciono
        _relax_fields_with_model_default(self)

    def clean_image(self):
        f = self.cleaned_data.get("image")
        if not f:
            return f  # graceful skip (blank=True — AC3 HARD RULE)
        _validate_image_field(f)
        return f


class ProductBrochureInlineForm(forms.ModelForm):
    """ProductBrochure inline form — pdf_file OBAVEZAN; cover_thumbnail_image blank-skip.

    pdf_file je FileField na modelu (NE ImageField) → NEMA Pillow to_python() problema →
    NE treba override (G-14). cover_thumbnail_image je ImageField blank=True → override +
    blank-skip.
    """

    cover_thumbnail_image = forms.FileField(required=False)  # G-14

    class Meta:
        model = ProductBrochure
        exclude = ()  # G-13

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _relax_base_translation_fields(self)
        _relax_fields_with_model_default(self)

    def clean_pdf_file(self):
        f = self.cleaned_data.get("pdf_file")
        # OBAVEZNO polje (pdf_file FileField bez blank=True) — NEMA blank-skip;
        # validator se zove BEZUSLOVNO da bi srpska media_pipeline poruka isplivala
        # ako bi se required ikad relaksiralo (AC3).
        _validate_pdf_field(f)
        return f

    def clean_cover_thumbnail_image(self):
        f = self.cleaned_data.get("cover_thumbnail_image")
        if not f:
            return f  # graceful skip (blank=True — AC3 HARD RULE)
        _validate_image_field(f)
        return f


class ProductTestimonialInlineForm(forms.ModelForm):
    """ProductTestimonial inline form — photo je blank=True → blank-skip."""

    photo = forms.FileField(required=False)  # G-14

    class Meta:
        model = ProductTestimonial
        exclude = ()  # G-13

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _relax_base_translation_fields(self)
        _relax_fields_with_model_default(self)

    def clean_photo(self):
        f = self.cleaned_data.get("photo")
        if not f:
            return f  # graceful skip (blank=True — AC3 HARD RULE)
        _validate_image_field(f)
        return f


# =============================================================================
# Inline klase (5 Translation* + 1 plain TabularInline) — AC1 / AC2 / G-11 / G-12
# =============================================================================


class ProductImageInline(TranslationTabularInline):
    model = ProductImage
    form = ProductImageInlineForm
    extra = 0
    fields = ("image", "order", "alt_text")  # alt_text per-locale auto


class ProductVariantInline(TranslationStackedInline):
    model = ProductVariant
    form = ProductVariantInlineForm
    extra = 0
    fields = ("name", "code", "image", "description", "order")  # name/description per-locale


class ProductSpecificationInline(TranslationTabularInline):
    model = ProductSpecification
    extra = 0
    fields = ("section", "key", "value", "order")  # key/value per-locale; NEMA upload


class ProductBrochureInline(TranslationStackedInline):
    model = ProductBrochure
    form = ProductBrochureInlineForm
    extra = 0
    fields = ("pdf_file", "cover_thumbnail_image", "title")  # title per-locale


class ProductTestimonialInline(TranslationStackedInline):
    model = ProductTestimonial
    form = ProductTestimonialInlineForm
    extra = 0
    fields = ("photo", "quote", "author_name", "location", "order")  # quote/location per-locale


class ProductSimilarInline(admin.TabularInline):
    # PLAIN TabularInline — ProductSimilar NIJE translatable (translation.py ga izostavlja; G-12).
    # fk_name="product" OBAVEZAN — dva FK ka Product (product/related_product) → admin.E202
    # bez ovoga (G-11). ProductSimilar.clean() (self-ref) je delegirana — admin NE dura (G-7).
    model = ProductSimilar
    fk_name = "product"
    extra = 0
    fields = ("related_product", "order")


# =============================================================================
# ProductAdmin (AC1, AC2, AC6, AC7, AC8, AC12)
# =============================================================================


@admin.register(Product)
class ProductAdmin(SeoWarningAdminMixin, TranslationAdmin):  # MRO: mixin PRVI (G-2)
    form = ProductAdminForm
    inlines = [
        ProductImageInline,
        ProductVariantInline,
        ProductSpecificationInline,
        ProductBrochureInline,
        ProductTestimonialInline,
        ProductSimilarInline,
        SeoMetaInline,  # 6.1 regression KEPT (G-8) → 7 inline-ova ukupno
    ]
    list_display = ("name", "brand", "is_published", "status", "price_eur", "condition")
    list_filter = ("is_published", "status", "brand", "condition")
    search_fields = ("name_sr",)  # REALNA kolona, NE virtuelni `name` (G-1)
    list_select_related = ("brand",)  # OBAVEZAN N+1 guard — Product.__str__ čita brand.name (G-10)
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at", "main_image_preview")
    # view_on_site NIJE postavljen na False — products:detail JE registrovan (urls.py:10, SM-D9).
    # fieldsets koriste BAZNA imena — TranslationAdmin AUTO-ekspanduje per-locale (_sr/_hu/_en; G-1).
    fieldsets = (
        (
            _("Osnovno"),
            {"fields": ("name", "slug", "brand", "series", "subcategory", "condition")},
        ),
        (
            _("Status i parametri"),
            {"fields": ("is_published", "status", "year", "price_eur", "horse_power")},
        ),
        (
            _("Sadržaj"),
            {"fields": ("description", "key_features", "main_image", "main_image_preview")},
        ),
        (
            _("Meta"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    @admin.display(description=_("Pregled glavne slike"))
    def main_image_preview(self, obj):
        if obj.main_image:
            return format_html(
                '<img src="{}" style="max-height:120px">', obj.main_image.url
            )
        return "—"  # statički em-dash — BEZ slomljenog <img> kad slika ne postoji (G-15)

    def save_related(self, request, form, formsets, change):
        """Publish-gate: pre objave traži name_sr + ≥1 slika galerije + ≥1 spec (AC6/SM-D5).

        super().save_related() se zove PRVI — perzistuje inline redove (i prolazi kroz
        SeoWarningAdminMixin save lanac, G-3) → tek POSLE njega su instance.images.count()
        i instance.specifications.count() tačni (G-5). Na neuspeh: graceful messages.error +
        revert OBA publish flag-a na draft kroz direktan QuerySet.update() — bypass-uje
        Product.save()/full_clean() (koji ignoriše update_fields i BEZUSLOVNO re-validira,
        models.py ~275) → eliminiše latentni footgun da revert raise-uje → HTTP 500 (G-6).
        NIKAD raise (raise iz save_related → HTTP 500, G-6).
        """
        super().save_related(request, form, formsets, change)

        instance = form.instance
        publishing = (
            instance.is_published or instance.status == Product.StatusChoice.PUBLISHED
        )
        if not publishing:
            return  # draft save se NIKAD ne gate-uje (AC6)

        missing = []
        if not (instance.name_sr or ""):
            missing.append(_("naziv na srpskom"))
        if instance.images.count() == 0:  # DB COUNT posle super() — G-5
            missing.append(_("bar jedna slika galerije"))
        if instance.specifications.count() == 0:
            missing.append(_("bar jedna specifikacija"))

        if missing:
            messages.error(
                request,
                _("Za objavljivanje je potrebno: %(items)s.")
                % {"items": "; ".join(str(m) for m in missing)},
            )
            # Revert OBA flag-a na neobjavljeno stanje (dual-status koherencija — G-16).
            # Direktan QuerySet.update() — bypass-uje save()/full_clean() (G-6 footgun guard).
            type(instance).objects.filter(pk=instance.pk).update(
                is_published=False, status=Product.StatusChoice.DRAFT
            )
            # In-memory instance konzistentan posle DB update-a (subsequent reads reflect revert).
            instance.is_published = False
            instance.status = Product.StatusChoice.DRAFT
