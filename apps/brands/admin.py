"""Story 8.4 — Brand CRUD Admin (full admin za Brand + Series hardening).

Konvertuje BrandAdmin iz 6.1 stub-a (plain ModelAdmin + SeoMetaInline) u pun
TranslationAdmin CRUD:
- BrandAdminForm (ModelForm) sa upload MIME/signature double-check DELEGIRANIM na
  media_pipeline.validate_image_mime/validate_pdf_mime (DRY + decompression-bomb guard),
  brand_color HTML5 color widget. name_sr je bezuslovno obavezan (model name blank=False).
- SeriesInline (TranslationStackedInline) — per-locale name/description, exclude slug.
- SeoMetaInline OSTAJE na Brand & Series (6.1 regression — G-8).
- SeriesAdmin.view_on_site = False (brands:series_detail neregistrovan — G-3).

Story 6.1 — SVA 4 modela (Brand/Series/Category/Subcategory) konvertovana iz
bare-register u ModelAdmin (SeoWarningAdminMixin + SeoMetaInline) za per-page SEO
meta unos.

⚠️ CategoryAdmin / SubcategoryAdmin OSTAJU NETAKNUTI (8.5 scope — SM-D1).

Reference patterns: apps/blog/admin.py (TranslationAdmin + search_fields=name_sr),
apps/seo/admin.py (SeoMetaInline), project-context.md upload double-check anti-pattern.
"""

from __future__ import annotations

from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TranslationAdmin, TranslationStackedInline

from apps.brands.models import Brand, Category, Series, Subcategory
from apps.media_pipeline.pdf_utils import validate_pdf_mime
from apps.media_pipeline.utils import validate_image_mime
from apps.seo.admin import SeoMetaInline, SeoWarningAdminMixin

# =============================================================================
# Upload size + MIME allowlists (UPPER_SNAKE_CASE — AC3 / SM-D9 / G-13)
# =============================================================================
MAX_IMAGE_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 MB  — logo, hero_image
MAX_PDF_UPLOAD_SIZE = 20 * 1024 * 1024  # 20 MB — catalog_pdf

# SVG namerno IZOSTAVLJEN (XSS vektor — OQ-5); gif izostavljen (v1 default).
ALLOWED_IMAGE_MIME_TYPES = ("image/jpeg", "image/png", "image/webp")
ALLOWED_PDF_MIME_TYPES = ("application/pdf",)


# =============================================================================
# BrandAdminForm (AC3, AC4, AC7)
# =============================================================================


class BrandAdminForm(forms.ModelForm):
    """Brand admin ModelForm: upload double-check + color widget.

    Upload validacija je DELEGIRANA na blessed media_pipeline helpere
    (`validate_image_mime` / `validate_pdf_mime`) — JEDAN kanonski validator za ceo
    projekat (DRY): MIME signature + Pillow `verify()` + size cap + decompression-bomb
    guard (Image.MAX_IMAGE_PIXELS=50M, DecompressionBombWarning→error). NE re-implementira
    upload validaciju inline (M2 fix — duplikat je propuštao 121Mpx PNG bombu).

    name_sr je BEZUSLOVNO obavezan (model `name` blank=False + sr default lang →
    modeltranslation promoviše name_sr u required form polje). NE relaksiramo to —
    prazan name_sr daje graceful FORM grešku (200), nikad model full_clean escape (M1 fix).
    `is_coming_soon` je NEZAVISAN flag i NE relaksira obavezan naziv.

    NE duplira hex/statistics validaciju — Brand.clean() je single source (G-7).
    """

    # Override image polja u plain FileField: Django ImageField form-field bi pokrenuo
    # SVOJ Pillow-validation u to_python() PRE clean_<field>, dajući default poruku
    # umesto helper srpske poruke (AC3). Naša clean_logo/clean_hero_image delegiraju na
    # validate_image_mime — JEDINI validator.
    logo = forms.FileField(required=False)
    hero_image = forms.FileField(required=False)

    class Meta:
        model = Brand
        exclude = ()  # MANDATORY — Meta.fields ILI Meta.exclude (G-12)
        widgets = {
            "brand_color": forms.TextInput(attrs={"type": "color"}),  # AC4 / G-6
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # AC4 / G-6: HTML5 color picker za brand_color. Meta.widgets SAM NIJE dovoljan —
        # modeltranslation/ModelForm rebuild widget-a (maxlength patch) pregazi `type` attr,
        # pa ga moramo re-postaviti ovde. VERIFIKOVANO testom: uklanjanje ove linije obara
        # test_ac4_brand_color_widget_is_color_input (NIJE redundantno sa Meta.widgets).
        # name_sr required-promotion se NE relaksira (M1 — bezuslovno obavezan; model
        # `name` blank=False) → prazan name_sr daje graceful form grešku (200).
        if "brand_color" in self.fields:
            self.fields["brand_color"].widget.attrs["type"] = "color"

    # ------------------------------------------------------------------
    # Upload double-check — DELEGIRANO na blessed media_pipeline helpere (AC3 / G-13 / M2)
    # ------------------------------------------------------------------
    def clean_logo(self):
        f = self.cleaned_data.get("logo")
        if not f:
            return f  # graceful skip (blank=True polja)
        validate_image_mime(
            f,
            allowed_mimes=ALLOWED_IMAGE_MIME_TYPES,
            max_size_bytes=MAX_IMAGE_UPLOAD_SIZE,
        )  # raise ValidationError; seek(0) na ulazu/izlazu — fajl ostaje intaktan
        return f

    def clean_hero_image(self):
        f = self.cleaned_data.get("hero_image")
        if not f:
            return f  # graceful skip
        validate_image_mime(
            f,
            allowed_mimes=ALLOWED_IMAGE_MIME_TYPES,
            max_size_bytes=MAX_IMAGE_UPLOAD_SIZE,
        )
        return f

    def clean_catalog_pdf(self):
        f = self.cleaned_data.get("catalog_pdf")
        if not f:
            return f  # graceful skip
        validate_pdf_mime(
            f,
            allowed_mimes=ALLOWED_PDF_MIME_TYPES,
            max_size_bytes=MAX_PDF_UPLOAD_SIZE,
        )  # raise ValidationError; seek(0) na ulazu/izlazu
        return f


# =============================================================================
# SeriesInline (AC6 / G-3 / G-10)
# =============================================================================


class SeriesInline(TranslationStackedInline):
    """Per-locale Series inline na BrandAdmin. exclude slug (Series.save() auto-gen)."""

    model = Series
    extra = 0
    exclude = ("slug",)  # MANDATORY (G-10) — slug auto-gen u Series.save()
    # NE show_change_link — vodilo bi na series_detail NoReverseMatch (G-3).


# =============================================================================
# BrandAdmin (AC1, AC2, AC8, AC9)
# =============================================================================


@admin.register(Brand)
class BrandAdmin(SeoWarningAdminMixin, TranslationAdmin):  # MRO: mixin PRVI (G-2)
    form = BrandAdminForm
    inlines = [SeoMetaInline, SeriesInline]  # SeoMetaInline KEPT (G-8) + SeriesInline
    list_display = ("name", "is_coming_soon", "brand_color", "has_pdf", "slug")
    list_filter = ("is_coming_soon",)
    search_fields = ("name_sr",)  # REALNA kolona, NE virtuelni `name` (G-1)
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at", "logo_preview", "hero_preview")
    # view_on_site NIJE postavljen — brands:detail JE registrovan (G-4).
    # Task 2 fieldsets: BASE field imena (`name`/`description`/`slogan`) —
    # modeltranslation TranslationAdmin AUTO-ekspanduje per-locale (_sr/_hu/_en);
    # NE enumerisati ručno (G-1). logo_preview uz logo, hero_preview uz hero_image,
    # created_at/updated_at u readonly Meta grupi (collapse).
    fieldsets = (
        (_("Osnovno"), {"fields": ("name", "slug", "is_coming_soon")}),
        (
            _("Vizuelni identitet"),
            {
                "fields": (
                    "logo",
                    "logo_preview",
                    "hero_image",
                    "hero_preview",
                    "brand_color",
                    "slogan",
                )
            },
        ),
        (_("Sadržaj"), {"fields": ("description", "statistics", "catalog_pdf")}),
        (
            _("Meta"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    @admin.display(boolean=True, description=_("PDF katalog"))
    def has_pdf(self, obj):
        return bool(obj.catalog_pdf)

    @admin.display(description=_("Pregled logoa"))
    def logo_preview(self, obj):
        if obj.logo:
            return format_html(
                '<img src="{}" style="max-height:80px">', obj.logo.url
            )
        return "—"

    @admin.display(description=_("Pregled hero slike"))
    def hero_preview(self, obj):
        if obj.hero_image:
            return format_html(
                '<img src="{}" style="max-height:80px">', obj.hero_image.url
            )
        return "—"


# =============================================================================
# SeriesAdmin — proactive view_on_site hardening (AC6 / G-3 / SM-D6 / SM-D8)
# =============================================================================


@admin.register(Series)
class SeriesAdmin(SeoWarningAdminMixin, admin.ModelAdmin):
    view_on_site = False  # brands:series_detail neregistrovan (G-3 / mirror blog BL-5)
    inlines = [SeoMetaInline]  # 6.1 regression KEPT


# =============================================================================
# Category / Subcategory — NETAKNUTI (8.5 scope — SM-D1)
# =============================================================================


@admin.register(Category)
class CategoryAdmin(SeoWarningAdminMixin, admin.ModelAdmin):
    inlines = [SeoMetaInline]


@admin.register(Subcategory)
class SubcategoryAdmin(SeoWarningAdminMixin, admin.ModelAdmin):
    inlines = [SeoMetaInline]
