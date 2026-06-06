"""Story 4.4 — AC11: /servis/ strana renderuje aktivnu servisnu formu (multipart) — TEA RED.

Pokriva AC11 / Task 5.2:
- GET /sr/servis/ → 200; renderovana strana sadrži servisnu formu (NEMA `disabled` na poljima/submit-u);
- hx-post ka forms:service_request_submit; enctype="multipart/form-data"; <input type="file" multiple accept>;
- CSRF token (csrfmiddlewaretoken) prisutan; tel: hitni-pozivi CTA prisutan;
- forma se renderuje BEZ bound `form` na GET (None-safe sirov-<input> idiom).

RED razlog: pages/service.html + ServiceView + forms partial ne postoje → 404 / TemplateDoesNotExist.

Pokrenuti:
    just test apps/pages/tests/test_service_form_wired.py -v

Refs: 4-4 AC11 + Task 5.2 + SM-D11/SM-D12; interface-contract § 6/7.
"""

from __future__ import annotations

import re

import pytest
from django.urls import reverse
from django.utils.translation import activate

pytestmark = pytest.mark.django_db


def _service_html(client) -> str:
    activate("sr")
    response = client.get("/sr/servis/")
    assert response.status_code == 200, (
        f"GET /sr/servis/ MORA biti 200 da bi se HTML parsirao, dobio {response.status_code}."
    )
    return response.content.decode("utf-8")


# AC-11: forma ima hx-post ka forms:service_request_submit
def test_form_has_hx_post_to_submit_endpoint(client):
    html = _service_html(client)
    assert re.search(r"hx-post=", html, re.IGNORECASE), (
        "Servisna forma MORA imati `hx-post` (HTMX submit — AC11)."
    )
    submit_url = reverse("forms:service_request_submit")
    assert submit_url in html, (
        f"`hx-post` MORA ciljati forms:service_request_submit ({submit_url}), AC11."
    )


# AC-11/AC-10: forma ima enctype="multipart/form-data" (file upload)
def test_form_has_multipart_enctype(client):
    html = _service_html(client)
    assert re.search(
        r'enctype=["\']multipart/form-data["\']', html, re.IGNORECASE
    ), (
        "Servisna forma MORA imati enctype=\"multipart/form-data\" (HTMX file upload — AC10/AC11)."
    )


# AC-11/AC-8: file input je multiple + accept (kamera/galerija na mobilnom)
def test_file_input_multiple_with_accept(client):
    html = _service_html(client)
    file_inputs = re.findall(r"<input\b[^>]*type=[\"']file[\"'][^>]*>", html, re.IGNORECASE)
    assert file_inputs, "Servisna forma MORA imati <input type=\"file\"> (foto upload — AC8/AC11)."
    tag = file_inputs[0]
    assert re.search(r"\bmultiple\b", tag, re.IGNORECASE), (
        f"File input MORA imati `multiple` (do 3 slike — AC8), tag: {tag!r}"
    )
    assert re.search(r"accept=", tag, re.IGNORECASE), (
        f"File input MORA imati `accept` atribut (aktivira kameru/galeriju — AC8), tag: {tag!r}"
    )


# AC-11/Security#1: CSRF token prisutan u renderovanoj formi
def test_form_has_csrf_token(client):
    html = _service_html(client)
    assert re.search(r'name=["\']csrfmiddlewaretoken["\']', html, re.IGNORECASE), (
        "Servisna forma MORA sadržati {% csrf_token %} (csrfmiddlewaretoken) — Security#1/AC11."
    )


# AC-11: polja NISU disabled (aktivna forma, NE skelet)
def test_form_fields_not_disabled(client):
    html = _service_html(client)
    # Scope na servisnu formu (forma sa hx-post; NE header search/jezik forme) —
    # site-wide GDPR baner (Story 7.2) sadrži legitiman `disabled` „Neophodan"
    # checkbox koji bi procureo u whole-page scan.
    form_m = re.search(
        r"<form\b[^>]*hx-post=.*?</form>", html, re.IGNORECASE | re.DOTALL
    )
    assert form_m, "Servisna forma <form hx-post=...> MORA postojati."
    html = form_m.group(0)
    field_tags = re.findall(r"<(?:input|textarea|select|button)\b[^>]*>", html, re.IGNORECASE)
    user_fields = [
        t for t in field_tags
        if "csrfmiddlewaretoken" not in t.lower() and 'type="hidden"' not in t.lower()
    ]
    assert user_fields, "Forma MORA imati input/textarea/select/button polja."
    for t in user_fields:
        assert not re.search(r"\bdisabled\b", t, re.IGNORECASE), (
            f"Polje VIŠE NE SME biti `disabled` — servisna forma je aktivna (AC11). Tag: {t!r}"
        )


# AC-11 (SM-D11): hitni `tel:` CTA prisutan (Stojan je sa terena)
def test_page_has_emergency_tel_cta(client):
    html = _service_html(client)
    assert 'href="tel:' in html, (
        "Servis strana MORA sadržati klikabilan emergency `<a href=\"tel:...\">` link (AC11/SM-D11)."
    )


# AC-11: forma renderuje machine_type select sa 4 opcije (dropdown)
def test_form_has_machine_type_select(client):
    html = _service_html(client)
    assert re.search(r'<select\b[^>]*name=["\']machine_type["\']', html, re.IGNORECASE), (
        "Servisna forma MORA imati <select name=\"machine_type\"> dropdown (AC2/AC11)."
    )
