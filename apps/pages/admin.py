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

from apps.pages.models import SiteSettings


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
