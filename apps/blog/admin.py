"""Story 8.7 — Blog CRUD Admin sa WYSIWYG (Post / Category / Tag).

Nadograđuje 5.1 STUB u pun multi-locale CRUD obrazac (mirror 8.4/8.5/8.6):
- PostAdmin/CategoryAdmin/TagAdmin → TranslationAdmin (sr/hu/en auto-tabovi).
- PostAdminForm: main_image override u plain FileField + clean_main_image delegira
  na blessed media_pipeline.validate_image_mime (MIME + Pillow verify +
  MAX_IMAGE_PIXELS=50M decompression-bomb guard; NE reimplementiraj — G-10).
- WYSIWYG za `body` (i samo body) kroz `wysiwyg` CSS-hook na Textarea-i —
  progressive enhancement IZNAD plain Textarea (SM-D2; static/js/wysiwyg.js).
  `Post.body` OSTAJE plain TextField (0 migracija — SM-D2/AC11).
- Publish-gate u save_related (NOVINA): pre objave traži title_sr + body_sr +
  main_image + category; graceful messages.error + revert-na-draft kroz
  QuerySet.update() bypass (NIKAD raise → 500; G-6/G-7). published_at auto-set
  timezone.now() ako prazno (AC6/SM-D12; NE pregazi ručno postavljen).
- view_on_site RE-ENABLED (5-3 registrovao blog:detail — SM-D8).
- filter_horizontal=("tags",) (M2M slobodno dodavanje + `+` add-popup — AC7).
- SeoMetaInline + SeoWarningAdminMixin OČUVAN na PostAdmin (6.1 — G-8).

Reference: apps/products/admin.py (8.6 — najbliži presedan), apps/core/admin_forms.py
(SM-D6 relax helperi), apps/core/sanitize.py (7-5 nh3 — render-time sanitizacija).
"""

from __future__ import annotations

from django import forms
from django.contrib import admin, messages
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TranslationAdmin

from apps.blog.models import Category, Post, Tag
from apps.core.admin_forms import (
    relax_base_translation_fields,
    relax_fields_with_model_default,
)
from apps.media_pipeline.utils import validate_image_mime
from apps.seo.admin import SeoMetaInline, SeoWarningAdminMixin

# =============================================================================
# Upload size + MIME allowlist (UPPER_SNAKE_CASE — AC4 / G-13; mirror 8.6)
# =============================================================================
# 5 MB — EKSPLICITAN override 10MB media_pipeline default (AC4); inače bi blog
# koristio 10MB umesto 5MB cap-a (mirror products/admin.py).
MAX_IMAGE_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 MB
# SVG namerno IZOSTAVLJEN (XSS vektor; mirror 8.4/8.6).
ALLOWED_IMAGE_MIME_TYPES = ("image/jpeg", "image/png", "image/webp")


def _validate_image_field(value):
    """Delegira na blessed validate_image_mime sa lokalnim 8.7 konstantama.

    Pozivaoc je odgovoran za blank-skip PRE poziva (helper RAISE-uje na praznom
    uploadu — AC4 HARD RULE).
    """
    validate_image_mime(
        value,
        allowed_mimes=ALLOWED_IMAGE_MIME_TYPES,
        max_size_bytes=MAX_IMAGE_UPLOAD_SIZE,
    )


# Body locale-polja koja dobijaju WYSIWYG enhancement hook (SAMO body — NE perex/title; SM-D2).
_WYSIWYG_BODY_FIELDS = ("body_sr", "body_hu", "body_en")


def _wire_wysiwyg_widgets(fields):
    """Dodaj `wysiwyg` CSS-class + `data-wysiwyg` hook na body locale Textarea-e.

    Progressive enhancement (SM-D2/AC2): static/js/wysiwyg.js enhance-uje IZNAD plain
    Textarea — ako JS otkaže, admin i dalje radi (Marijana piše u textarea, save prolazi).
    Marker SAMO na body (NE perex/title). Idempotentno (NE dupliraj `wysiwyg`).
    """
    for fld in _WYSIWYG_BODY_FIELDS:
        if fld not in fields:
            continue
        widget = fields[fld].widget
        existing = (widget.attrs.get("class") or "").split()
        if "wysiwyg" not in existing:
            existing.append("wysiwyg")
        widget.attrs["class"] = " ".join(existing)
        widget.attrs["data-wysiwyg"] = "true"


# =============================================================================
# PostAdminForm — main_image upload double-check + WYSIWYG body widget (AC2/AC4/AC9)
# =============================================================================


class PostAdminForm(forms.ModelForm):
    """Glavni Post admin ModelForm sa main_image upload double-check-om + WYSIWYG body.

    main_image je ImageField na modelu → override u plain FileField da Django Pillow
    to_python() ne pregazi srpsku media_pipeline poruku (G-9/G-14). clean_main_image
    delegira na validate_image_mime (blank-skip jer je main_image blank=True — AC4 HARD
    RULE: helper RAISE-uje na praznom uploadu).

    WYSIWYG: `body_sr/_hu/_en` Textarea-e dobijaju `wysiwyg` CSS-hook (+ data-attr) →
    static/js/wysiwyg.js progressive-enhance-uje IZNAD plain Textarea (SM-D2). Editor je
    UX; podležno polje OSTAJE Textarea (JS otkaže → admin i dalje radi).

    title_sr OSTAJE bezuslovno required (AC9/G-11 — NE relaksiraj); bazno `title` se
    relaksira kroz core helper (SM-D6) jer direct-bind ModelForm vidi i `title` i `title_sr`.
    """

    # G-9/G-14: override ImageField → plain FileField (Pillow to_python() ne pregazi srpsku poruku).
    main_image = forms.FileField(required=False)

    class Meta:
        model = Post
        exclude = ()  # MANDATORY — Meta.fields ILI Meta.exclude (G-13)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        relax_base_translation_fields(self)  # title_sr ostaje required; bazno title opciono
        relax_fields_with_model_default(self)  # status ima model default (DRAFT)
        _wire_wysiwyg_widgets(self.fields)

    def clean_main_image(self):
        f = self.cleaned_data.get("main_image")
        if not f:
            return f  # graceful skip (main_image blank=True — AC4 HARD RULE)
        _validate_image_field(f)
        return f


# =============================================================================
# CategoryAdmin + TagAdmin (AC1, AC7, AC10) — NEMA SeoMetaInline (SM-D10/G-12)
# =============================================================================


@admin.register(Category)
class CategoryAdmin(TranslationAdmin):
    list_display = ("name", "slug")
    search_fields = ("name_sr",)  # REALNA kolona, NE virtuelni `name` (G-1)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Tag)
class TagAdmin(TranslationAdmin):
    list_display = ("name", "slug")
    search_fields = ("name_sr",)  # REALNA kolona (G-1)
    prepopulated_fields = {"slug": ("name",)}


# =============================================================================
# PostAdmin (AC1, AC2, AC5, AC6, AC7, AC8, AC9) — MRO: mixin PRVI (G-2)
# =============================================================================


@admin.register(Post)
class PostAdmin(SeoWarningAdminMixin, TranslationAdmin):
    form = PostAdminForm
    inlines = [SeoMetaInline]  # 6.1 regression KEPT (G-8)
    list_display = ("title", "category", "status", "published_at", "author")
    # OBAVEZAN N+1 guard — list_display renderuje FK kolone category + author (G-10; mirror 8.6).
    list_select_related = ("category", "author")
    list_filter = ("status", "category", "tags")
    search_fields = ("title_sr",)  # REALNA kolona, NE virtuelni `title` (G-1)
    prepopulated_fields = {"slug": ("title",)}  # radi sa TranslationAdmin (G-14)
    date_hierarchy = "published_at"
    filter_horizontal = ("tags",)  # M2M slobodno dodavanje + `+` add-popup (AC7)
    # SM-D8: view_on_site RE-ENABLED — 5-3 registrovao blog:detail (Post.get_absolute_url
    # radi za published; draft → 404 NE 500). 5-1 view_on_site=False NAMERNO uklonjen.
    # fieldsets koriste BAZNA imena — TranslationAdmin AUTO-ekspanduje per-locale (G-1).
    fieldsets = (
        (
            _("Osnovno"),
            {"fields": ("title", "slug", "category", "tags", "author")},
        ),
        (
            _("Status"),
            {"fields": ("status", "published_at")},
        ),
        (
            _("Sadržaj"),
            {"fields": ("perex", "body", "main_image")},
        ),
        (
            _("Meta"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
    readonly_fields = ("created_at", "updated_at")

    class Media:
        # Progressive-enhancement WYSIWYG iz static/js/ — 0 dep, no jQuery, no build
        # (SM-D2 GRANA B). addEventListener bind (CSP-friendlier — OQ-5 forward).
        js = ("js/wysiwyg.js",)

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        """Markiraj body locale Textarea-e WYSIWYG hook-om na nivou admin-built forme.

        modeltranslation gradi per-locale polja kroz formfield_for_dbfield → marker mora
        ići OVDE da `base_fields["body_sr"].widget` (koji test čita) nosi hook (NE samo
        per-instance __init__). PostAdminForm.__init__ dodatno osigurava marker pri
        direct-bind-u (SM-D2/AC2).
        """
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if formfield is not None and db_field.name in _WYSIWYG_BODY_FIELDS:
            _wire_wysiwyg_widgets({db_field.name: formfield})
        return formfield

    def save_related(self, request, form, formsets, change):
        """Publish-gate: pre objave traži title_sr + body_sr + main_image + category (AC5/SM-D5).

        super().save_related() se zove PRVI (perzistuje M2M/inline + prolazi kroz
        SeoWarningAdminMixin save lanac, G-3). Na neuspeh: graceful messages.error + revert
        status na DRAFT kroz direktan QuerySet.update() — bypass-uje Post.save()/full_clean()
        (koji ignoriše update_fields i BEZUSLOVNO re-validira, models.py:201-205 → latentni
        500 footgun; G-6). NIKAD raise (raise iz save_related → HTTP 500, G-7).

        published_at auto-set (AC6/SM-D12): pri uspešnoj objavi, ako je prazno → timezone.now()
        (NIKAD naive datetime.now()); ako već ima vrednost → NE pregazi (zakazana objava).
        """
        super().save_related(request, form, formsets, change)

        instance = form.instance
        if instance.status != Post.Status.PUBLISHED:
            return  # draft save se NIKAD ne gate-uje (AC5)

        missing = []
        if not (instance.title_sr or "").strip():
            missing.append(_("naslov na srpskom"))
        if not (instance.body_sr or "").strip():
            missing.append(_("telo objave na srpskom"))
        if not instance.main_image:
            missing.append(_("glavna slika"))
        if instance.category_id is None:
            missing.append(_("kategorija"))

        if missing:
            messages.error(
                request,
                _("Za objavljivanje je potrebno popuniti: %(items)s.")
                % {"items": "; ".join(str(m) for m in missing)},
            )
            # Revert na draft kroz QuerySet.update() — bypass save()/full_clean() (G-6 footgun).
            Post.objects.filter(pk=instance.pk).update(status=Post.Status.DRAFT)
            instance.status = Post.Status.DRAFT  # in-memory konzistentan re-render
            return

        # Gate prošao → published_at auto-set ako prazno (AC6; NE pregazi ručno postavljen).
        if instance.published_at is None:
            now = timezone.now()
            Post.objects.filter(pk=instance.pk).update(published_at=now)
            instance.published_at = now
