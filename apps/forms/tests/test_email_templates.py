"""Story 4.1 — AC5 email template-ovi base_email.html + lead_received.html (TEA RED phase).

Pokriva AC5: base_email.html + lead_received.html render bez greške sa Lead context-om;
render sadrži lead polja (ime/email/poruka/form_type prikaz); sr render nema ćirilice
(pune dijakritike, NEMA šišane latinice).

TEA RED phase: SVI testovi MORAJU pasti — templates/emails/ ne postoji →
TemplateDoesNotExist; apps.forms.models ne postoji → ImportError.

Refs:
- 4-1-lead-model-smtp-setup.md AC5 + Task 5 + SM-D9
- 4-1-interface-contract.md § 5 (Email template-ovi)
"""

from __future__ import annotations

import re

import pytest
from django.template.loader import render_to_string

pytestmark = pytest.mark.django_db

_CYRILLIC = re.compile(r"[Ѐ-ӿ]")


# AC5: base_email.html postoji i renderuje bez greške
def test_base_email_template_renders():
    html = render_to_string("emails/base_email.html", {})
    assert html is not None, "templates/emails/base_email.html MORA renderovati bez greške."


# AC5: lead_received.html renderuje sa Lead context-om i sadrži lead polja
def test_lead_received_template_renders_with_lead_fields():
    from apps.forms.models import Lead

    lead = Lead.objects.create(
        form_type=Lead.FormType.MODEL_INQUIRY,
        name="Đorđe Đorđević",
        email="djordje@example.com",
        phone="+381 11 222 333",
        message="Zanima me Tulip MIX prikolica.",
        data={"product_slug": "tulip-mix", "product_name": "Tulip MIX"},
        locale="sr",
    )
    html = render_to_string("emails/lead_received.html", {"lead": lead})

    assert "Đorđe Đorđević" in html, f"lead_received.html MORA renderovati ime, dobio {html[:300]!r}."
    assert "djordje@example.com" in html, "lead_received.html MORA renderovati email."
    assert "Zanima me Tulip MIX prikolica." in html, "lead_received.html MORA renderovati poruku."


# AC5: sr render nema ćirilice (pune dijakritike)
def test_lead_received_no_cyrillic_in_sr():
    from apps.forms.models import Lead

    lead = Lead.objects.create(
        form_type=Lead.FormType.KONTAKT, name="Marko Marković", email="marko@example.com", locale="sr"
    )
    html = render_to_string("emails/lead_received.html", {"lead": lead})
    assert not _CYRILLIC.search(html), (
        "lead_received.html (sr) NE SME sadržati ćirilicu (pune latinične dijakritike — SM-D9)."
    )
