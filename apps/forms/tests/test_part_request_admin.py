"""Story 4.5 — AC11: admin regression (part-request lead + slika kroz postojeći inline) — TEA RED.

Pokriva AC11 / Task 6.1 (regression-only — `apps/forms/admin.py` NETAKNUT — SM-D12):
- part-request Lead + 1 LeadAttachment → superuser GET reverse("admin:forms_lead_changelist") → 200;
- change-view tog lead-a → 200 (postojeći LeadAttachmentInline renderuje prilog, form-type-agnostičan);
- „Upit za rezervni deo" je dostupna FormType opcija (label puni dijakritik).

NAPOMENA: admin se NE menja u 4.5 — postojeći LeadAdmin + LeadAttachmentInline (4.1/4.4) automatski
prikazuju part-request lead. Ovo je čist regression smoke.

Pokrenuti:
    just test apps/forms/tests/test_part_request_admin.py -v

Refs: 4-5 AC11 + Task 6.1 + SM-D12; interface-contract § 8.
"""

from __future__ import annotations

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

pytestmark = pytest.mark.django_db


def _part_lead_with_attachment():
    from apps.forms.models import Lead, LeadAttachment

    lead = Lead.objects.create(
        form_type=Lead.FormType.PART_REQUEST,
        name="Marko Marković",
        email="marko@example.com",
        phone="+381641234567",
        message="Pozovite popodne.",
        locale="sr",
        data={
            "tractor_model": "Agri Tracking TB804",
            "part_name": "Filter ulja",
            "extra_description": "Original deo.",
            "payment_method": "cod",
            "delivery_method": "delivery",
        },
    )
    LeadAttachment.objects.create(
        lead=lead,
        file=SimpleUploadedFile("deo.jpg", b"jpeg-bytes", content_type="image/jpeg"),
    )
    return lead


# AC-11: superuser GET changelist → 200 (regression — part-request lead se prikazuje)
def test_lead_changelist_returns_200_with_part_request(client, superuser):
    _part_lead_with_attachment()
    url = reverse("admin:forms_lead_changelist")
    client.force_login(superuser)
    response = client.get(url)
    assert response.status_code == 200, (
        f"superuser GET {url!r} (sa part-request lead-om) MORA vratiti 200 (LeadAdmin regression), "
        f"dobio {response.status_code}."
    )


# AC-11: superuser GET change-view part-request lead-a SA slikom → 200 (postojeći inline renderuje)
def test_lead_change_view_part_request_with_attachment_returns_200(client, superuser):
    lead = _part_lead_with_attachment()
    url = reverse("admin:forms_lead_change", args=[lead.pk])
    client.force_login(superuser)
    response = client.get(url)
    assert response.status_code == 200, (
        f"superuser GET change-view {url!r} (part-request + slika) MORA vratiti 200 — postojeći "
        f"LeadAttachmentInline renderuje prilog (AC11), dobio {response.status_code}."
    )


# AC-11: „Upit za rezervni deo" je dostupna FormType opcija (label puni dijakritik)
def test_part_request_form_type_label():
    from django.utils.translation import activate

    from apps.forms.models import Lead

    activate("sr")
    label = str(Lead.FormType.PART_REQUEST.label)
    assert label == "Upit za rezervni deo", (
        f"FormType.PART_REQUEST label MORA biti 'Upit za rezervni deo' (AC11), dobio {label!r}."
    )
