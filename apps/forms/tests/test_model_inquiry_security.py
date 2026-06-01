"""Story 4.3 — AC2/AC5: server-side product rezolucija + spoofing + XSS — TEA RED.

Pokriva AC2 (KRITIČNO — NE veruj klijentu) / Task 3.1 + 3.3:
- Nepostojeći slug: validan POST sa product_slug="ne-postoji" → ODBIJEN; 0 Lead; 0 email;
  error partial 200 sa porukom „Proizvod nije pronađen." (SM-D8 default).
- Unpublished product: POST sa unpublished slug → ODBIJEN (is_published=True filter ga ne vidi); 0 Lead.
- Spoofing: POST sa DODATNIM `product_name`/`model` lažnom vrednošću → server IGNORIŠE;
  lead.data["product_name"] + subject iz Product.name (DB), NIKAD iz POST stringa.
- XSS (javna unauth forma): <script> u name/message → error rerender auto-escape-uje
  (&lt;script&gt;), NIKAD sirov <script>.

RED razlog: apps.forms.urls/views model_inquiry_submit ne postoji → NoReverseMatch / import error.

Pokrenuti:
    just test apps/forms/tests/test_model_inquiry_security.py -v

Refs: 4-3 AC2/AC5 + Task 3.1/3.3 + SM-D2/SM-D8; interface-contract § 2.
"""

from __future__ import annotations

import pytest

from apps.forms.models import Lead
from apps.products.tests.factories import ProductFactory

pytestmark = pytest.mark.django_db


# AC-2 (security): nepostojeći slug → ODBIJEN (0 Lead, 0 email, error partial 200 sa porukom)
def test_nonexistent_slug_rejected(
    htmx_post, model_inquiry_submit_url, model_inquiry_payload, recipient_env, mailoutbox
):
    payload = {**model_inquiry_payload, "product_slug": "ne-postoji-nikako"}
    response = htmx_post(model_inquiry_submit_url, payload)

    assert response.status_code == 200, (
        f"Nevalidan/nepostojeći slug → error partial 200 (SM-D8 default, NE 4xx), dobio "
        f"{response.status_code}."
    )
    assert Lead.objects.count() == 0, "Nepostojeći product → NE SME kreirati Lead (AC2)."
    assert len(mailoutbox) == 0, "Nepostojeći product → NE SME poslati email (AC2)."
    html = response.content.decode("utf-8")
    assert "Proizvod nije pronađen." in html, (
        "Error odgovor MORA sadržati poruku „Proizvod nije pronađen.” (SM-D8 default, pun "
        f"dijakritik đ). Sadržaj: {html[:400]!r}"
    )


# AC-2 (security): unpublished product → ODBIJEN (is_published=True filter ga ne vidi)
def test_unpublished_product_rejected(
    htmx_post, model_inquiry_submit_url, model_inquiry_payload, recipient_env, mailoutbox
):
    product = ProductFactory.create_unpublished(name="Skriveni Model")
    payload = {**model_inquiry_payload, "product_slug": product.slug}
    response = htmx_post(model_inquiry_submit_url, payload)

    assert response.status_code == 200, (
        f"Unpublished product → error partial 200 (isto kao nepostojeći), dobio {response.status_code}."
    )
    assert Lead.objects.count() == 0, (
        "Unpublished product NE SME kreirati Lead — server-side filter `is_published=True` "
        "ne sme da ga vidi (AC2 security)."
    )
    assert len(mailoutbox) == 0, "Unpublished product → NE SME poslati email (AC2)."


# AC-2 (security SPOOFING — KRITIČNO): POST sa lažnim product_name → server IGNORIŠE;
# lead.data["product_name"] iz Product.name (DB), NE iz POST stringa
def test_spoofed_product_name_field_ignored(
    htmx_post, model_inquiry_submit_url, model_inquiry_payload, recipient_env, mailoutbox
):
    product = ProductFactory.create(name="Agri Tracking TB804")
    payload = {
        **model_inquiry_payload,
        "product_slug": product.slug,
        "product_name": "GRATIS PROIZVOD",  # lažno polje — napadač pokušava spoof
        "model": "GRATIS PROIZVOD",  # lažno polje
    }
    response = htmx_post(model_inquiry_submit_url, payload)

    assert response.status_code == 200
    assert Lead.objects.count() == 1, "Validan slug → 1 Lead (lažna polja se IGNORIŠU, ne odbijaju)."
    lead = Lead.objects.get()
    assert lead.data["product_name"] == "Agri Tracking TB804", (
        f"lead.data['product_name'] MORA biti iz DB Product.name, NE iz POST stringa (SM-D2), "
        f"dobio {lead.data['product_name']!r}."
    )
    assert "GRATIS PROIZVOD" not in lead.data.values(), (
        f"Lažna POST vrednost NE SME biti u lead.data (mass-assignment zaštita, SM-D2), "
        f"dobio {lead.data!r}."
    )
    assert "GRATIS PROIZVOD" not in mailoutbox[0].subject, (
        f"Lažna POST vrednost NE SME biti u email subject-u (subject iz Product.name — SM-D2/SM-D3), "
        f"dobio {mailoutbox[0].subject!r}."
    )
    assert "Agri Tracking TB804" in mailoutbox[0].subject, (
        "Subject MORA biti iz pravog Product.name (DB), ne iz spoofed POST polja."
    )


# AC-5 (XSS insurance — javna unauth forma): <script> u name/message → escaped, NIKAD sirov
def test_invalid_submit_escapes_script_payload(
    htmx_post, model_inquiry_submit_url, model_inquiry_payload, recipient_env, mailoutbox
):
    product = ProductFactory.create(name="Agri Tracking TB804")
    payload = {
        **model_inquiry_payload,
        "product_slug": product.slug,
        "email": "",  # učini formu nevalidnom da se bound forma rerenderuje sa payload-om
        "name": "<script>alert(1)</script>",
        "message": "<script>alert(2)</script>",
    }
    response = htmx_post(model_inquiry_submit_url, payload)

    html = response.content.decode("utf-8")
    assert "<script>alert(1)</script>" not in html, (
        "Sirov <script> NE SME biti u response-u (Django auto-escape — XSS, Task 3.3)."
    )
    assert "&lt;script&gt;" in html, (
        "Payload MORA biti auto-escaped (&lt;script&gt;) u rerender-ovanoj bound formi (Task 3.3)."
    )
