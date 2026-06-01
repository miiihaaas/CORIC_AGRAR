"""Story 4.1 — read-mostly LeadAdmin (SM-D8).

Registracija na POSTOJEĆI `admin.site` (mirror `apps/brands/admin.py`); admin je
mount-ovan UNUTAR `i18n_patterns` → stvarni URL je locale-prefiksovan
(`/sr/admin/forms/lead/...`); testovi koriste `reverse("admin:forms_lead_*")`.

NIJE dashboard sa segmentovanim count-om (Epic 8.3), NIJE custom slug/axes (Epic 8.1).
"""

from __future__ import annotations

from django.contrib import admin

from apps.forms.models import Lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("form_type", "name", "email", "phone", "created_at")
    list_filter = ("form_type", "created_at")
    search_fields = ("name", "email", "message")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "updated_at", "ip_address")
