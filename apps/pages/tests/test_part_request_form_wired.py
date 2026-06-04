"""Story 4.5 — AC10: /servis/rezervni-delovi/ strana renderuje aktivnu formu (multipart) — TEA RED.

Pokriva AC10 / Task 5.2:
- GET /sr/servis/rezervni-delovi/ → 200; renderovana strana sadrži formu (NEMA `disabled` na poljima/submit-u);
- hx-post ka forms:part_request_submit; enctype="multipart/form-data";
- <input type="file" sa `accept` i BEZ `multiple` (max 1 — SM-D4);
- oba <select> (payment_method/delivery_method) sa opcijama;
- CSRF token (csrfmiddlewaretoken) prisutan; tel: hitni-pozivi CTA prisutan;
- forma se renderuje BEZ bound `form` na GET (None-safe sirov-<input> idiom).

RED razlog: pages/part-request.html + PartRequestView + forms partial ne postoje →
404 / TemplateDoesNotExist.

Pokrenuti:
    just test apps/pages/tests/test_part_request_form_wired.py -v

Refs: 4-5 AC10 + Task 5.2 + SM-D4/SM-D11/SM-D12; interface-contract § 6/7.
"""

from __future__ import annotations

import re

import pytest
from django.urls import reverse
from django.utils.translation import activate

pytestmark = pytest.mark.django_db


def _page_html(client) -> str:
    activate("sr")
    response = client.get("/sr/servis/rezervni-delovi/")
    assert response.status_code == 200, (
        f"GET /sr/servis/rezervni-delovi/ MORA biti 200 da bi se HTML parsirao, dobio "
        f"{response.status_code}."
    )
    return response.content.decode("utf-8")


# AC-10: forma ima hx-post ka forms:part_request_submit
def test_form_has_hx_post_to_submit_endpoint(client):
    html = _page_html(client)
    assert re.search(r"hx-post=", html, re.IGNORECASE), (
        "Rezervni-delovi forma MORA imati `hx-post` (HTMX submit — AC10)."
    )
    submit_url = reverse("forms:part_request_submit")
    assert submit_url in html, (
        f"`hx-post` MORA ciljati forms:part_request_submit ({submit_url}), AC10."
    )


# AC-10/AC-9: forma ima enctype="multipart/form-data" (file upload)
def test_form_has_multipart_enctype(client):
    html = _page_html(client)
    assert re.search(
        r'enctype=["\']multipart/form-data["\']', html, re.IGNORECASE
    ), (
        "Rezervni-delovi forma MORA imati enctype=\"multipart/form-data\" (HTMX file upload — AC9/AC10)."
    )


# AC-10/AC-9: forma ima hx-encoding="multipart/form-data" (HTMX file upload)
# Bez hx-encoding, HTMX serijalizuje formu kao urlencoded i TIHO ispusti fajl (enctype
# atribut sam ne utiče na HTMX XHR submit) — file upload bi se slomio a forma bi delovala OK.
# Locking-test: template već ima hx-encoding, ovde fiksiramo da ostane.
def test_form_has_hx_encoding_multipart(client):
    html = _page_html(client)
    assert re.search(
        r'hx-encoding=["\']multipart/form-data["\']', html, re.IGNORECASE
    ), (
        "Rezervni-delovi forma MORA imati hx-encoding=\"multipart/form-data\" — bez njega "
        "HTMX tiho ispušta fajl iz submit-a (enctype sam nije dovoljan za XHR — AC9/AC10)."
    )


# AC-10/AC-13: file input ima `accept` i NEMA `multiple` (max 1 — SM-D4)
def test_file_input_single_with_accept(client):
    html = _page_html(client)
    file_inputs = re.findall(r"<input\b[^>]*type=[\"']file[\"'][^>]*>", html, re.IGNORECASE)
    assert file_inputs, "Forma MORA imati <input type=\"file\"> (foto upload — AC10/AC13)."
    tag = file_inputs[0]
    assert not re.search(r"\bmultiple\b", tag, re.IGNORECASE), (
        f"File input NE SME imati `multiple` (max 1 slika — SM-D4/AC13), tag: {tag!r}"
    )
    assert re.search(r"accept=", tag, re.IGNORECASE), (
        f"File input MORA imati `accept` atribut (aktivira kameru/galeriju — AC13), tag: {tag!r}"
    )


# AC-10/Security: CSRF token prisutan u renderovanoj formi
def test_form_has_csrf_token(client):
    html = _page_html(client)
    assert re.search(r'name=["\']csrfmiddlewaretoken["\']', html, re.IGNORECASE), (
        "Rezervni-delovi forma MORA sadržati {% csrf_token %} (csrfmiddlewaretoken) — Security/AC10."
    )


# AC-10: polja NISU disabled (aktivna forma, NE skelet)
def test_form_fields_not_disabled(client):
    html = _page_html(client)
    field_tags = re.findall(r"<(?:input|textarea|select|button)\b[^>]*>", html, re.IGNORECASE)
    user_fields = [
        t for t in field_tags
        if "csrfmiddlewaretoken" not in t.lower() and 'type="hidden"' not in t.lower()
    ]
    assert user_fields, "Forma MORA imati input/textarea/select/button polja."
    for t in user_fields:
        assert not re.search(r"\bdisabled\b", t, re.IGNORECASE), (
            f"Polje NE SME biti `disabled` — rezervni-delovi forma je aktivna (AC10). Tag: {t!r}"
        )


# AC-10: forma renderuje payment_method select sa opcijama
def test_form_has_payment_method_select(client):
    html = _page_html(client)
    assert re.search(r'<select\b[^>]*name=["\']payment_method["\']', html, re.IGNORECASE), (
        "Forma MORA imati <select name=\"payment_method\"> dropdown (AC1/AC10)."
    )
    assert "Pouzeće" in html and "Predračun" in html, (
        "payment_method select MORA imati opcije 'Pouzeće' i 'Predračun' (puni dijakritik — AC1/AC10)."
    )


# AC-10: forma renderuje delivery_method select sa opcijama
def test_form_has_delivery_method_select(client):
    html = _page_html(client)
    assert re.search(r'<select\b[^>]*name=["\']delivery_method["\']', html, re.IGNORECASE), (
        "Forma MORA imati <select name=\"delivery_method\"> dropdown (AC1/AC10)."
    )
    assert "Dostava" in html and "Lično preuzimanje" in html, (
        "delivery_method select MORA imati opcije 'Dostava' i 'Lično preuzimanje' (AC1/AC10)."
    )


# AC-10 (SM-D11): hitni `tel:` CTA prisutan
def test_page_has_emergency_tel_cta(client):
    html = _page_html(client)
    assert 'href="tel:' in html, (
        "Rezervni-delovi strana MORA sadržati klikabilan emergency `<a href=\"tel:...\">` link "
        "(AC10/SM-D11)."
    )
