"""Story 3.4 — singleton-friendly admin za SiteSettings (SM-D6).

Registracija na POSTOJEĆI `admin.site` (mount-ovan UNUTAR i18n_patterns → stvarni URL je
locale-prefiksovan /sr/admin/...). Singleton guardovi: has_add_permission False kad red
postoji, has_delete_permission False. changelist_view REDIREKTUJE na change-view jedinog
objekta (singleton UX) kroz reverse() — NIKAD hardkodovan put.

modeltranslation auto-rendera jezičke tabove za slogan/address/working_hours (NE ručno).
"""

from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from modeltranslation.admin import TranslationAdmin

from apps.pages.models import Page, SiteSettings

# Body locale-polja koja dobijaju WYSIWYG enhancement hook (SAMO body — NE title; G-9; mirror 8.7).
_WYSIWYG_BODY_FIELDS = ("body_sr", "body_hu", "body_en")


@admin.register(SiteSettings)
class SiteSettingsAdmin(TranslationAdmin):
    # TranslationAdmin (NE plain ModelAdmin) — AC6: modeltranslation auto-grupiše
    # slogan/address/working_hours po jeziku (sr/hu/en) umesto 4 ungrouped polja.
    list_display = ("company_name", "phone_sales", "email", "updated_at")
    search_fields = ("company_name", "phone_sales", "email")

    def has_add_permission(self, request):
        # Singleton — nema „Add another" kad red već postoji.
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Singleton se ne briše.
        return False

    def changelist_view(self, request, extra_context=None):
        # Singleton UX: vodi pravo na change-view jedinog objekta (NE 1-redni changelist).
        # load() get_or_create-uje pk=1 (jedan round-trip) → bezuslovan redirect kroz reverse().
        obj = SiteSettings.load()
        return HttpResponseRedirect(
            reverse("admin:pages_sitesettings_change", args=[obj.pk])
        )


@admin.register(Page)
class PageAdmin(TranslationAdmin):
    """Story 7.4 / 8.8 — generičke statičke strane (NIJE singleton — ima add/delete).

    TranslationAdmin auto-grupiše title/body po jeziku (sr/hu/en tabovi).
    `prepopulated_fields` radi na default-locale `title` polju (G-2 — provereno
    radeća kombinacija sa TranslationAdmin, blog 5-1 BL-2). NE override-uj
    has_add_permission/has_delete_permission (RAZLIKA od singleton admin-a).

    8.8: `search_fields` koristi REALNU kolonu `title_sr` (NE virtuelni translated
    `title` — G-1; mirror 8.4-8.7 ('name_sr',)/('title_sr',) konvencija). WYSIWYG
    enhancement na `body_sr/_hu/_en` Textarea-e (REUSE static/js/wysiwyg.js — 8.7
    GRANA B vanilla-JS; `Page.body` OSTAJE plain TextField — 0 migracija, SM-D2).
    NEMA SeoMetaInline/upload/publish-gate (Page nema te koncepte — G-3/SM-D6).
    `view_on_site` OSTAJE default (Page IMA radni get_absolute_url — SM-D7).
    """

    list_display = ("title", "slug", "updated_at")
    # REALNA DB kolona `title_sr` (NE virtuelni `title` — G-1/SM-D4). `list_display`
    # zadržava virtuelni `title` (per-active-locale render je ISPRAVAN tamo).
    search_fields = ("title_sr", "slug")
    prepopulated_fields = {"slug": ("title",)}

    class Media:
        # Progressive-enhancement WYSIWYG iz static/js/ — 0 dep, no jQuery, no build
        # (8.7 GRANA B; REUSE). addEventListener bind (CSP-friendlier — OQ-5 forward).
        js = ("js/wysiwyg.js",)

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        """Markiraj body locale Textarea-e WYSIWYG hook-om na nivou admin-built forme.

        modeltranslation gradi per-locale polja kroz formfield_for_dbfield → marker
        mora ići OVDE da `base_fields["body_sr"].widget` (koji test čita) nosi hook.
        SAMO `body` (NE `title` — G-9; title je jednolinijski naslov). Mirror 8.7
        apps/blog/admin.py _wire_wysiwyg_widgets.
        """
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if formfield is not None and db_field.name in _WYSIWYG_BODY_FIELDS:
            widget = formfield.widget
            existing = (widget.attrs.get("class") or "").split()
            if "wysiwyg" not in existing:
                existing.append("wysiwyg")
            widget.attrs["class"] = " ".join(existing)
            widget.attrs["data-wysiwyg"] = "true"
        return formfield
