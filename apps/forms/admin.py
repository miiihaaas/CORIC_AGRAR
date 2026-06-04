"""Story 4.1 — read-mostly LeadAdmin (SM-D8).

Registracija na POSTOJEĆI `admin.site` (mirror `apps/brands/admin.py`); admin je
mount-ovan UNUTAR `i18n_patterns` → stvarni URL je locale-prefiksovan
(`/sr/admin/forms/lead/...`); testovi koriste `reverse("admin:forms_lead_*")`.

NIJE dashboard sa segmentovanim count-om (Epic 8.3), NIJE custom slug/axes (Epic 8.1).
"""

from __future__ import annotations

from django.contrib import admin
from django.http import HttpRequest

from apps.forms.models import Lead, LeadAttachment


class LeadAttachmentInline(admin.TabularInline):
    """Story 4.4 — read-mostly inline prikaz priloženih servisnih slika (AC13).

    Admin SAMO pregleda/preuzima priloge (AC13 intent), NE kreira ručno priloge sa
    proizvoljnim fajlom (to bi zaobišlo formin MIME+Pillow double-check). Zato je
    `file` readonly i dodavanje novih priloga kroz inline je onemogućeno.
    """

    model = LeadAttachment
    extra = 0
    can_delete = True
    readonly_fields = ("file",)

    def has_add_permission(self, request: HttpRequest, obj=None) -> bool:
        return False


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("form_type", "name", "email", "phone", "created_at")
    list_filter = ("form_type", "created_at")
    search_fields = ("name", "email", "message")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "updated_at", "ip_address")
    inlines = [LeadAttachmentInline]
