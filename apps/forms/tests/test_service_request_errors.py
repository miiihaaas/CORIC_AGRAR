"""Story 4.4 — AC7: error rerender + dve a11y regije + file-reject PRE Lead-a — TEA RED.

Pokriva AC7 / Task 4.1:
- nevalidan POST (prazno name) → 200 (NE 4xx); 0 Lead; 0 LeadAttachment; 0 email; role="alert"
  + aria-live="assertive" + error tekst; rerender ČUVA tekstualna polja (name/description value-i);
- > 3 slike → 0 Lead, error „najviše 3"; > 5 MB → 0 Lead, error „5 MB";
- MIXED-BATCH endpoint (all-or-nothing): {**payload, "photos": [valid_jpeg, non_image]} → 0 Lead,
  0 attachment, 0 email, error (validna slika iz batch-a se NE perzistira — KRITIČNO).

RED razlog: apps.forms.urls/views service_request_submit ne postoji → NoReverseMatch → padaju.

Pokrenuti:
    just test apps/forms/tests/test_service_request_errors.py -v

Refs: 4-4 AC7 + Task 4.1 + SM-D4/SM-D15; interface-contract § 3.
"""

from __future__ import annotations

import io
import re

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

pytestmark = pytest.mark.django_db


def _jpeg(name: str) -> SimpleUploadedFile:
    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (10, 10), color=(34, 64, 47)).save(buffer, format="JPEG")
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type="image/jpeg")


def _multifile_post(htmx_post, url, payload, photos):
    """HTMX multipart POST sa listom `photos` (multi-file getlist putanja na endpointu)."""
    data = {**payload, "photos": list(photos)}
    return htmx_post(url, data)


# AC-7: nevalidan POST (prazno name) → 200; 0 Lead; 0 attachment; 0 email
def test_invalid_submit_no_lead_no_attachment_no_email(
    htmx_post, service_request_submit_url, service_request_payload, recipient_env, mailoutbox
):
    from apps.forms.models import Lead, LeadAttachment

    payload = {**service_request_payload, "name": ""}
    response = htmx_post(service_request_submit_url, payload)

    assert response.status_code == 200, (
        f"Nevalidan submit MORA vratiti 200 (HTMX swap error UI, NE 4xx), dobio {response.status_code}."
    )
    assert Lead.objects.count() == 0, "Nevalidan submit NE SME kreirati Lead (AC7)."
    assert LeadAttachment.objects.count() == 0, "Nevalidan submit NE SME kreirati LeadAttachment (AC7)."
    assert len(mailoutbox) == 0, "Nevalidan submit NE SME poslati email (AC7)."


# AC-7: error rerender ima in-form role="alert" + aria-live="assertive" + realan error tekst
def test_invalid_submit_has_assertive_alert_with_error_text(
    htmx_post, service_request_submit_url, service_request_payload, recipient_env, mailoutbox
):
    payload = {**service_request_payload, "name": ""}
    response = htmx_post(service_request_submit_url, payload)
    html = response.content.decode("utf-8")

    assert 'role="alert"' in html, (
        'Error rerender MORA imati in-form <div role="alert"> error summary (regija #1, AC7).'
    )
    assert 'aria-live="assertive"' in html, (
        'In-form error summary MORA biti aria-live="assertive" (regija #1, AC7).'
    )
    # role="alert" blok MORA nositi realan per-field error tekst (NE prazna a11y regija)
    alert = re.search(
        r'<div[^>]*role="alert"[^>]*>(.*?)</div>', html, re.IGNORECASE | re.DOTALL
    )
    assert alert and alert.group(1).strip(), (
        "In-form role=\"alert\" blok NE SME biti prazna a11y regija — MORA nositi per-field "
        "error tekst (AC7). Sadržaj: " + (alert.group(1)[:300] if alert else "<nema role=alert>")
    )


# AC-7: error rerender ČUVA tekstualna polja (name/description value-i prisutni)
def test_invalid_submit_preserves_text_fields(
    htmx_post, service_request_submit_url, service_request_payload, recipient_env, mailoutbox
):
    payload = {
        **service_request_payload,
        "name": "Stojan Stojanović",
        "phone": "",  # učini formu nevalidnom (phone obavezan — SM-D9)
        "description": "Curi ulje iz hidraulike.",
    }
    response = htmx_post(service_request_submit_url, payload)
    html = response.content.decode("utf-8")

    assert "Stojan Stojanović" in html, (
        "Error rerender MORA ČUVATI `name` value (korisnik ne gubi unos — AC7)."
    )
    assert "Curi ulje iz hidraulike." in html, (
        "Error rerender MORA ČUVATI `description` value (AC7)."
    )


# AC-7: > 3 slike → 0 Lead, error „najviše 3" (file-reject PRE kreiranja Lead-a)
def test_more_than_three_photos_rejected_before_lead(
    htmx_post,
    service_request_submit_url,
    service_request_payload,
    valid_image_jpeg,
    valid_image_png,
    recipient_env,
    mailoutbox,
):
    from apps.forms.models import Lead, LeadAttachment

    photos = [
        valid_image_jpeg,
        valid_image_png,
        _jpeg("c.jpg"),
        _jpeg("d.jpg"),
    ]
    response = _multifile_post(
        htmx_post, service_request_submit_url, service_request_payload, photos
    )

    assert response.status_code == 200
    assert Lead.objects.count() == 0, "> 3 slike → NE Lead (file-reject PRE Lead-a — AC7)."
    assert LeadAttachment.objects.count() == 0
    assert len(mailoutbox) == 0
    assert "najviše 3" in response.content.decode("utf-8"), (
        "Error odgovor MORA sadržati 'najviše 3' (epics.md:814)."
    )


# AC-7: > 5 MB slika → 0 Lead, error „5 MB"
# NAPOMENA: koristi `oversized_image_real` (STVARNO > 5 MB bajtova), NE `oversized_image`
# (forsiran `.size`) — test client encode_file serijalizuje kroz file.read(), pa se forsiran
# `.size` NE prenosi preko HTTP granice; server bi video stvaran (mali) size i kreirao Lead.
def test_oversized_photo_rejected_before_lead(
    htmx_post,
    service_request_submit_url,
    service_request_payload,
    oversized_image_real,
    recipient_env,
    mailoutbox,
):
    from apps.forms.models import Lead, LeadAttachment

    response = _multifile_post(
        htmx_post, service_request_submit_url, service_request_payload, [oversized_image_real]
    )

    assert response.status_code == 200
    assert Lead.objects.count() == 0, "> 5 MB → NE Lead (file-reject PRE Lead-a — AC7)."
    assert LeadAttachment.objects.count() == 0
    assert len(mailoutbox) == 0
    assert "5 MB" in response.content.decode("utf-8"), (
        "Error odgovor MORA sadržati substring '5 MB' (epics.md:816)."
    )


# AC-7 (KRITIČNO — all-or-nothing na endpointu): 1 validna + 1 nevalidna → 0 Lead, 0 attachment, 0 email
def test_mixed_batch_endpoint_all_or_nothing(
    htmx_post,
    service_request_submit_url,
    service_request_payload,
    valid_image_jpeg,
    non_image_file,
    recipient_env,
    mailoutbox,
):
    from apps.forms.models import Lead, LeadAttachment

    response = _multifile_post(
        htmx_post,
        service_request_submit_url,
        service_request_payload,
        [valid_image_jpeg, non_image_file],
    )

    assert response.status_code == 200
    assert Lead.objects.count() == 0, (
        "MIXED-BATCH (1 validna + 1 PDF) MORA biti ODBIJEN U CELOSTI — 0 Lead (validna slika "
        "iz batch-a se NE perzistira; all-or-nothing — AC7/SM-D4)."
    )
    assert LeadAttachment.objects.count() == 0, (
        "MIXED-BATCH → 0 LeadAttachment (validna slika se NE sme sačuvati — KRITIČNO)."
    )
    assert len(mailoutbox) == 0, "MIXED-BATCH → 0 email (AC7)."
    # error poruka prisutna (rerender error partial)
    assert 'role="alert"' in response.content.decode("utf-8"), (
        "MIXED-BATCH error rerender MORA imati in-form role=\"alert\" (AC7)."
    )
