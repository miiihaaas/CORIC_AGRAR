"""Story 3.3 — AC2 (SM-D3): RAZREŠENJE header „Kontakt" placeholder-a + GET-only ContactView.

`pages:contact` postaje stvaran → header.html:96 „Kontakt" nav link `href="#"` se WIRE-uje
na pages:contact (/sr/kontakt/). Dodatno: ContactView je GET-only (C1/C3) — POST /sr/kontakt/
MORA vratiti DETERMINISTIČKI HTTP 405 (forma je skelet, http_method_names bez 'post').

RED phase (TEA). Regex parsiranje (projekat nema BeautifulSoup — mirror test_about_*).

RED razlog: dok Dev ne wire-uje, header „Kontakt" je `href="#"` → wire test pada; dok
ContactView/URL ne postoje, POST /sr/kontakt/ je 404 (NE 405) → 405 test pada.

AC2 — 2 testa:
- test_header_kontakt_link_wired
- test_contact_view_is_get_only  (POST -> TAČNO 405, deterministički)

Pokrenuti:
    just test apps/pages/tests/test_contact_header_wired.py -v
"""

from __future__ import annotations

import re

import pytest
from django.utils.translation import activate

pytestmark = pytest.mark.django_db


def _home_html(client) -> str:
    """Renderuj home (header se renderuje na svakoj strani — bira se home jer je tolerantna)."""
    activate("sr")
    response = client.get("/sr/")
    assert response.status_code == 200, (
        f"GET /sr/ MORA biti 200 da bi se header parsirao, dobio {response.status_code}."
    )
    return response.content.decode("utf-8")


def _href_of(tag: str) -> str:
    m = re.search(r"href=[\"']([^\"']*)[\"']", tag, re.IGNORECASE)
    return m.group(1) if m else ""


def test_header_kontakt_link_wired(client):
    """AC2/SM-D3: header „Kontakt" nav link href = pages:contact (/sr/kontakt/), NE '#'."""
    html = _home_html(client)
    # Pronađi <a> koji sadrži tekst „Kontakt" (header nav link).
    link_match = re.search(
        r"<a\b[^>]*>\s*Kontakt\s*</a>", html, re.IGNORECASE | re.DOTALL
    )
    assert link_match, (
        "Header MORA imati 'Kontakt' nav link. Nije pronađen u render-u."
    )
    href = _href_of(link_match.group(0))
    assert href == "/sr/kontakt/", (
        f"Header 'Kontakt' link MORA biti wire-ovan na pages:contact (/sr/kontakt/), "
        f"dobio {href!r}. RED: još href='#'."
    )


def test_contact_view_is_get_only(client):
    """AC2/C1/C3 (SM-D4/SM-D1): POST /sr/kontakt/ -> TAČNO HTTP 405 Method Not Allowed.

    ContactView.http_method_names = ["get", "head", "options"] (BEZ 'post') → Django
    View.dispatch vraća 405 za POST. Forma je skelet (disabled submit); funkcionalan
    submit (Lead/email/HTMX) dolazi iz Epic 4 (Story 4.2 — ZASEBAN apps/forms endpoint),
    NE na ContactView. Deterministički assert == 405 (BEZ 'ILI' alternative).
    """
    activate("sr")
    response = client.post("/sr/kontakt/", data={})
    assert response.status_code == 405, (
        "POST /sr/kontakt/ MORA vratiti TAČNO HTTP 405 (ContactView GET-only — "
        "http_method_names bez 'post'; forma je skelet — SM-D4/C3). "
        f"Dobio {response.status_code}. RED: ContactView/URL još ne postoje (404), ili "
        "neko je dodao post() metod."
    )
