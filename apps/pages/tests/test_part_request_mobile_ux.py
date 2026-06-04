"""Story 4.5 — AC13: mobile-responsive UX (testabilno na nivou atributa/klasa) — TEA RED.

Pokriva AC13 / Task 5.3 (parity sa 4.4 AC8):
- <input type="file"> ima `accept` (kamera/galerija na mobilnom) i NE sadrži `multiple` (max 1 — SM-D4);
- submit/sekcija koristi očekivane `coric-` BEM klase (coric-contact-form__submit /
  coric-contact-form__indicator / coric-service-form__file — REUSE 4.4);
- `htmx-indicator` klasa prisutna (spinner tokom upload-a).

NAPOMENA: čisto vizuelno/responsive CSS ponašanje (breakpoint stacking < 768px, full-width render)
se asertuje SAMO na nivou prisustva klase/atributa — vizuelni CSS render je VAN scope-a
automatizovanog testa, konzistentno sa projektnom CSS-testing strategijom iz 4.4.

RED razlog: pages/part-request.html + PartRequestView + forms partial ne postoje →
404 / TemplateDoesNotExist.

Pokrenuti:
    just test apps/pages/tests/test_part_request_mobile_ux.py -v

Refs: 4-5 AC13 + Task 5.3 + SM-D4; interface-contract § 6.
"""

from __future__ import annotations

import re

import pytest
from django.utils.translation import activate

pytestmark = pytest.mark.django_db


def _page_html(client) -> str:
    activate("sr")
    response = client.get("/sr/servis/rezervni-delovi/")
    assert response.status_code == 200, (
        f"GET /sr/servis/rezervni-delovi/ MORA biti 200, dobio {response.status_code}."
    )
    return response.content.decode("utf-8")


# AC-13: file input ima `accept` i NEMA `multiple` (max 1 — SM-D4)
def test_file_input_accept_and_no_multiple(client):
    html = _page_html(client)
    file_inputs = re.findall(r"<input\b[^>]*type=[\"']file[\"'][^>]*>", html, re.IGNORECASE)
    assert file_inputs, "Forma MORA imati <input type=\"file\"> (foto upload — AC13)."
    tag = file_inputs[0]
    assert re.search(r"accept=", tag, re.IGNORECASE), (
        f"File input MORA imati `accept` (kamera/galerija na mobilnom — AC13), tag: {tag!r}"
    )
    assert not re.search(r"\bmultiple\b", tag, re.IGNORECASE), (
        f"File input NE SME imati `multiple` (max 1 — SM-D4/AC13), tag: {tag!r}"
    )


# AC-13: htmx-indicator spinner klasa prisutna (vidljiv tokom upload-a)
def test_htmx_indicator_present(client):
    html = _page_html(client)
    assert "htmx-indicator" in html, (
        "Forma MORA imati `htmx-indicator` klasu (spinner tokom upload-a — AC13/REUSE 4.4)."
    )


# AC-13: submit dugme koristi očekivanu coric- BEM klasu (REUSE 4.4 contact-form BEM)
def test_submit_uses_coric_bem_class(client):
    html = _page_html(client)
    assert "coric-contact-form__submit" in html, (
        "Submit dugme MORA koristiti `coric-contact-form__submit` BEM klasu (REUSE 4.4 — AC13)."
    )


# AC-13: file polje koristi očekivanu coric-service-form__file BEM klasu (REUSE 4.4)
def test_file_field_uses_coric_bem_class(client):
    html = _page_html(client)
    assert "coric-service-form__file" in html, (
        "File polje MORA koristiti `coric-service-form__file` BEM klasu (REUSE 4.4 — AC13)."
    )
