"""Story 4.1 — AC7 read-mostly LeadAdmin (TEA RED phase).

Pokriva AC7: Lead registrovan na admin.site; list_display/list_filter/search_fields
definisani; superuser GET reverse("admin:forms_lead_changelist") → 200.

⛔ reverse() PRAVILO: admin pod i18n_patterns → NIKAD hardkodovan /admin/ ni /sr/admin/.

TEA RED phase: SVI testovi MORAJU pasti — apps.forms.models ne postoji →
NoReverseMatch("admin:forms_lead_changelist") / LookupError.

Refs:
- 4-1-lead-model-smtp-setup.md AC7 + Task 8.8 + SM-D8/3-4-SM-D6
- 4-1-interface-contract.md § 6 (Admin contract)
"""

from __future__ import annotations

import pytest
from django.contrib import admin
from django.urls import reverse

pytestmark = pytest.mark.django_db


# AC7: Lead registrovan na admin.site
def test_lead_registered_in_admin():
    from apps.forms.models import Lead

    assert admin.site.is_registered(Lead), (
        "Lead MORA biti registrovan na admin.site (@admin.register(Lead) — AC7/SM-D8)."
    )


# AC7: list_display / list_filter / search_fields definisani
def test_lead_admin_options_defined():
    from apps.forms.models import Lead

    model_admin = admin.site._registry[Lead]

    assert "form_type" in model_admin.list_display and "name" in model_admin.list_display, (
        f"LeadAdmin.list_display MORA sadržati form_type+name (project-context.md:200), "
        f"dobio {model_admin.list_display!r}."
    )
    assert "form_type" in model_admin.list_filter and "created_at" in model_admin.list_filter, (
        f"LeadAdmin.list_filter MORA biti (form_type, created_at), dobio {model_admin.list_filter!r}."
    )
    assert set(("name", "email", "message")).issubset(set(model_admin.search_fields)), (
        f"LeadAdmin.search_fields MORA sadržati name/email/message, "
        f"dobio {model_admin.search_fields!r}."
    )


# AC7: superuser GET reverse("admin:forms_lead_changelist") → 200 (NIKAD hardkodovan put)
def test_lead_changelist_returns_200_for_superuser(client, superuser):
    # forms_lead_changelist se razrešava tek kad je Lead registrovan → RED: NoReverseMatch
    url = reverse("admin:forms_lead_changelist")
    client.force_login(superuser)
    response = client.get(url)
    assert response.status_code == 200, (
        f"superuser GET {url!r} MORA vratiti 200, dobio {response.status_code}."
    )


# AC7: change-view reverse radi (locale-aware, pod i18n_patterns)
def test_lead_change_view_reverse_resolves(client, superuser):
    from apps.forms.models import Lead

    lead = Lead.objects.create(
        form_type=Lead.FormType.KONTAKT, name="Marko Marković", email="marko@example.com"
    )
    url = reverse("admin:forms_lead_change", args=[lead.pk])
    client.force_login(superuser)
    response = client.get(url)
    assert response.status_code == 200, (
        f"superuser GET change-view {url!r} MORA vratiti 200, dobio {response.status_code}."
    )
