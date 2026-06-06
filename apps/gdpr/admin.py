"""Story 7.1 — singleton-friendly admin za CookiePolicy (SM-D6).

Registracija na POSTOJEĆI `admin.site` (mount-ovan UNUTAR i18n_patterns → stvarni URL
je locale-prefiksovan /sr/admin/...; SM-D10). Singleton guardovi: has_add_permission
False kad red postoji, has_delete_permission False. changelist_view REDIREKTUJE na
change-view jedinog objekta (singleton UX) kroz reverse() — NIKAD hardkodovan put.

TranslationAdmin auto-rendera jezičke tabove za title/body (NE ručno) — mirror
SiteSettingsAdmin.
"""

from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from modeltranslation.admin import TranslationAdmin

from apps.gdpr.models import CookiePolicy


@admin.register(CookiePolicy)
class CookiePolicyAdmin(TranslationAdmin):
    # TranslationAdmin (NE plain ModelAdmin) — AC6: modeltranslation auto-grupiše
    # title/body po jeziku (sr/hu/en tabovi) umesto 6 ungrouped polja.
    list_display = ("__str__", "effective_date", "updated_at")

    def has_add_permission(self, request):
        # Singleton — nema „Add another" kad red već postoji.
        return not CookiePolicy.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Singleton se ne briše.
        return False

    def changelist_view(self, request, extra_context=None):
        # Singleton UX: vodi pravo na change-view jedinog objekta (NE 1-redni changelist).
        # load() get_or_create-uje pk=1 (jedan round-trip) → bezuslovan redirect kroz reverse().
        obj = CookiePolicy.load()
        return HttpResponseRedirect(
            reverse("admin:gdpr_cookiepolicy_change", args=[obj.pk])
        )
