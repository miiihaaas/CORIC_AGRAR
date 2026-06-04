"""Story 4.5 — AC7: error rerender + dve a11y regije + file-reject PRE Lead-a — TEA RED.

Pokriva AC7 / Task 4.1:
- nevalidan POST (prazno tractor_model ILI payment_method van choices) → 200 (NE 4xx); 0 Lead;
  0 LeadAttachment; 0 email; role="alert" + aria-live="assertive" + error tekst;
  rerender ČUVA tekstualna/select polja (tractor_model/part_name/payment_method/delivery_method);
- oversized foto (`oversized_image_real` — ENDPOINT-nivo stvarnih > 5 MB) → 0 Lead, error „5 MB";
- non_image_file (PDF) → 0 Lead, error prisutan.

RED razlog: apps.forms.urls/views part_request_submit ne postoji → NoReverseMatch → padaju.

Pokrenuti:
    just test apps/forms/tests/test_part_request_errors.py -v

Refs: 4-5 AC7 + Task 4.1 + SM-D4; interface-contract § 3.
"""

from __future__ import annotations

import re

import pytest

pytestmark = pytest.mark.django_db


# AC-7: nevalidan POST (prazno tractor_model) → 200; 0 Lead; 0 attachment; 0 email
def test_invalid_submit_no_lead_no_attachment_no_email(
    htmx_post, part_request_submit_url, part_request_payload, recipient_env, mailoutbox
):
    from apps.forms.models import Lead, LeadAttachment

    payload = {**part_request_payload, "tractor_model": ""}
    response = htmx_post(part_request_submit_url, payload)

    assert response.status_code == 200, (
        f"Nevalidan submit MORA vratiti 200 (HTMX swap error UI, NE 4xx), dobio {response.status_code}."
    )
    assert Lead.objects.count() == 0, "Nevalidan submit NE SME kreirati Lead (AC7)."
    assert LeadAttachment.objects.count() == 0, "Nevalidan submit NE SME kreirati LeadAttachment (AC7)."
    assert len(mailoutbox) == 0, "Nevalidan submit NE SME poslati email (AC7)."


# AC-7: nevalidan payment_method (van choices) → 200, 0 Lead, error na payment_method
def test_invalid_choice_field_no_lead(
    htmx_post, part_request_submit_url, part_request_payload, recipient_env, mailoutbox
):
    from apps.forms.models import Lead

    payload = {**part_request_payload, "payment_method": "bitcoin"}
    response = htmx_post(part_request_submit_url, payload)

    assert response.status_code == 200
    assert Lead.objects.count() == 0, "Nevalidan payment_method NE SME kreirati Lead (AC7)."


# AC-7: error rerender ima in-form role="alert" + aria-live="assertive" + realan error tekst
def test_invalid_submit_has_assertive_alert_with_error_text(
    htmx_post, part_request_submit_url, part_request_payload, recipient_env, mailoutbox
):
    payload = {**part_request_payload, "tractor_model": ""}
    response = htmx_post(part_request_submit_url, payload)
    html = response.content.decode("utf-8")

    assert 'role="alert"' in html, (
        'Error rerender MORA imati in-form <div role="alert"> error summary (regija #1, AC7).'
    )
    assert 'aria-live="assertive"' in html, (
        'In-form error summary MORA biti aria-live="assertive" (regija #1, AC7).'
    )
    alert = re.search(
        r'<div[^>]*role="alert"[^>]*>(.*?)</div>', html, re.IGNORECASE | re.DOTALL
    )
    assert alert and alert.group(1).strip(), (
        "In-form role=\"alert\" blok NE SME biti prazna a11y regija — MORA nositi per-field "
        "error tekst (AC7). Sadržaj: " + (alert.group(1)[:300] if alert else "<nema role=alert>")
    )


# AC-7: error rerender ČUVA tekstualna I select polja (korisnik ne gubi unos)
def test_invalid_submit_preserves_text_and_select_fields(
    htmx_post, part_request_submit_url, part_request_payload, recipient_env, mailoutbox
):
    payload = {
        **part_request_payload,
        "part_name": "",  # učini formu nevalidnom (part_name obavezan)
        "tractor_model": "Agri Tracking TB804",
        "payment_method": "proforma",
        "delivery_method": "pickup",
    }
    response = htmx_post(part_request_submit_url, payload)
    html = response.content.decode("utf-8")

    assert "Agri Tracking TB804" in html, (
        "Error rerender MORA ČUVATI `tractor_model` value (korisnik ne gubi unos — AC7)."
    )
    # select-i čuvaju izbor: proforma/pickup selected
    assert "proforma" in html, "Error rerender MORA ČUVATI `payment_method` izbor (proforma — AC7)."
    assert "pickup" in html, "Error rerender MORA ČUVATI `delivery_method` izbor (pickup — AC7)."


# AC-7: > 5 MB slika → 0 Lead, error „5 MB" (file-reject PRE kreiranja Lead-a).
# NAPOMENA: koristi `oversized_image_real` (STVARNO > 5 MB bajtova), NE `oversized_image`
# (forsiran `.size`) — test client encode_file serijalizuje kroz file.read(), pa se forsiran
# `.size` NE prenosi preko HTTP granice; server bi video stvaran (mali) size i kreirao Lead.
def test_oversized_photo_rejected_before_lead(
    htmx_post,
    part_request_submit_url,
    part_request_payload,
    oversized_image_real,
    recipient_env,
    mailoutbox,
):
    from apps.forms.models import Lead, LeadAttachment

    payload = {**part_request_payload, "photo": oversized_image_real}
    response = htmx_post(part_request_submit_url, payload)

    assert response.status_code == 200
    assert Lead.objects.count() == 0, "> 5 MB → NE Lead (file-reject PRE Lead-a — AC7)."
    assert LeadAttachment.objects.count() == 0
    assert len(mailoutbox) == 0
    assert "5 MB" in response.content.decode("utf-8"), (
        "Error odgovor MORA sadržati substring '5 MB' (konkretan limit — AC7)."
    )


# AC-7: ne-slika fajl (PDF) → 0 Lead, error prisutan (MIME-signature odbija PRE Lead-a)
def test_non_image_photo_rejected_before_lead(
    htmx_post,
    part_request_submit_url,
    part_request_payload,
    non_image_file,
    recipient_env,
    mailoutbox,
):
    from apps.forms.models import Lead, LeadAttachment

    payload = {**part_request_payload, "photo": non_image_file}
    response = htmx_post(part_request_submit_url, payload)

    assert response.status_code == 200
    assert Lead.objects.count() == 0, "Ne-slika (PDF) → NE Lead (file-reject PRE Lead-a — AC7)."
    assert LeadAttachment.objects.count() == 0
    assert len(mailoutbox) == 0
    assert 'role="alert"' in response.content.decode("utf-8"), (
        "Ne-slika error rerender MORA imati in-form role=\"alert\" (AC7)."
    )
