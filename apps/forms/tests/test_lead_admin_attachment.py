"""Story 4.4 — AC13: LeadAttachment inline na LeadAdmin — TEA RED phase.

Pokriva AC13 / Task 6.1:
- LeadAttachmentInline registrovan na LeadAdmin (model=LeadAttachment);
- superuser GET reverse("admin:forms_lead_changelist") → 200 (regression — postojeći LeadAdmin radi);
- superuser GET change-view lead-a sa attachment-ima → 200 (inline se renderuje).

⛔ reverse() PRAVILO: admin pod i18n_patterns → NIKAD hardkodovan /admin/.

RED razlog: LeadAttachment + LeadAttachmentInline ne postoje → ImportError / inline nije registrovan.

Pokrenuti:
    just test apps/forms/tests/test_lead_admin_attachment.py -v

Refs: 4-4 AC13 + Task 6.1; interface-contract § 8.
"""

from __future__ import annotations

import pytest
from django.contrib import admin
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

pytestmark = pytest.mark.django_db


# AC-13: LeadAttachmentInline je registrovan na LeadAdmin (model=LeadAttachment)
def test_lead_attachment_inline_registered_on_lead_admin():
    from apps.forms.models import Lead, LeadAttachment

    lead_admin = admin.site._registry[Lead]
    inline_models = [inline.model for inline in lead_admin.inlines]
    assert LeadAttachment in inline_models, (
        "LeadAdmin MORA imati inline za LeadAttachment (TabularInline/StackedInline — AC13). "
        f"Inlines: {[i.model.__name__ for i in lead_admin.inlines]!r}."
    )


# AC-13: superuser GET changelist → 200 (regression — postojeći LeadAdmin radi sa novim inline-om)
def test_lead_changelist_returns_200_for_superuser(client, superuser):
    url = reverse("admin:forms_lead_changelist")
    client.force_login(superuser)
    response = client.get(url)
    assert response.status_code == 200, (
        f"superuser GET {url!r} MORA vratiti 200 (LeadAdmin regression sa inline-om), dobio "
        f"{response.status_code}."
    )


# AC-13: superuser GET change-view lead-a SA attachment-ima → 200 (inline se renderuje)
def test_lead_change_view_with_attachments_returns_200(client, superuser):
    from apps.forms.models import Lead, LeadAttachment

    lead = Lead.objects.create(
        form_type=Lead.FormType.SERVICE_REQUEST,
        name="Stojan Stojanović",
        email="stojan@example.com",
        data={"machine_type": "tractor", "brand_model": "Agri Tracking TB804"},
    )
    LeadAttachment.objects.create(
        lead=lead,
        file=SimpleUploadedFile("kvar.jpg", b"jpeg-bytes", content_type="image/jpeg"),
    )

    url = reverse("admin:forms_lead_change", args=[lead.pk])
    client.force_login(superuser)
    response = client.get(url)
    assert response.status_code == 200, (
        f"superuser GET change-view {url!r} (sa attachment-ima) MORA vratiti 200 — inline se "
        f"renderuje (AC13), dobio {response.status_code}."
    )
