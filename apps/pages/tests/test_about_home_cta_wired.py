"""Story 3.2 — AC2 (SM-D3): RAZREŠENJE Story 3-1 placeholder-a.

`pages:about` postaje stvaran → home „Saznaj više" CTA + header „O nama" nav link
WIRE-uju se na pages:about; placeholder atributi (aria-disabled/tabindex=-1/role) se UKLANJAJU.

RED phase (TEA). Regex parsiranje (projekat nema BeautifulSoup — mirror test_home_*).

RED razlog: dok Dev ne wire-uje, home CTA i header link su `href="#"` (+ CTA ima
`aria-disabled="true"` / `tabindex="-1"`) → svi testovi padaju.

AC2 — 4 testa:
- test_home_about_cta_links_to_pages_about
- test_home_about_cta_no_longer_aria_disabled
- test_header_o_nama_link_wired
- test_home_about_cta_is_tabbable

Pokrenuti:
    just test apps/pages/tests/test_about_home_cta_wired.py -v
"""

from __future__ import annotations

import re

import pytest
from django.utils.translation import activate

pytestmark = pytest.mark.django_db

# Hvata <a ...> otvarajući tag koji nosi data-testid="home-about-cta".
_HOME_CTA_RE = re.compile(
    r"<a\b[^>]*data-testid=[\"']home-about-cta[\"'][^>]*>",
    re.IGNORECASE | re.DOTALL,
)


def _home_html(client) -> str:
    """Renderuj home; tolerantan na prazan domain (CTA/header su statički markup)."""
    activate("sr")
    response = client.get("/sr/")
    assert response.status_code == 200, (
        f"GET /sr/ MORA biti 200 da bi se HTML parsirao, dobio {response.status_code}."
    )
    return response.content.decode("utf-8")


def _href_of(tag: str) -> str:
    m = re.search(r"href=[\"']([^\"']*)[\"']", tag, re.IGNORECASE)
    return m.group(1) if m else ""


def test_home_about_cta_links_to_pages_about(client):
    """AC2: home „Saznaj više" CTA href = /sr/o-nama/ (NE '#')."""
    html = _home_html(client)
    m = _HOME_CTA_RE.search(html)
    assert m, (
        "Home MORA imati [data-testid=home-about-cta] CTA (data-testid ZADRŽAN posle wire)."
    )
    href = _href_of(m.group(0))
    assert href == "/sr/o-nama/", (
        f"Saznaj vise CTA href MORA rezolvovati pages:about (/sr/o-nama/), dobio {href!r}. "
        "RED: placeholder jos href='#'."
    )


def test_home_about_cta_no_longer_aria_disabled(client):
    """AC2: CTA NEMA aria-disabled (placeholder uklonjen — SM-D3)."""
    html = _home_html(client)
    m = _HOME_CTA_RE.search(html)
    assert m, "Home MORA imati [data-testid=home-about-cta] CTA."
    tag = m.group(0)
    assert "aria-disabled" not in tag.lower(), (
        f"CTA NE SME imati aria-disabled (placeholder uklonjen). Tag: {tag!r}"
    )


def test_header_o_nama_link_wired(client):
    """AC2: header „O nama" nav link href = pages:about (/sr/o-nama/), NE '#'."""
    html = _home_html(client)
    # Pronađi <a> koji sadrži tekst „O nama" (header nav link).
    link_match = re.search(
        r"<a\b[^>]*>\s*O nama\s*</a>", html, re.IGNORECASE | re.DOTALL
    )
    assert link_match, (
        "Header MORA imati 'O nama' nav link. Nije pronađen u render-u."
    )
    href = _href_of(link_match.group(0))
    assert href == "/sr/o-nama/", (
        f"Header 'O nama' link MORA biti wire-ovan na pages:about (/sr/o-nama/), dobio {href!r}. "
        "RED: jos href='#'."
    )


def test_home_about_cta_is_tabbable(client):
    """AC2: CTA je tab-abilan — NEMA tabindex='-1' (keyboard dostupan)."""
    html = _home_html(client)
    m = _HOME_CTA_RE.search(html)
    assert m, "Home MORA imati [data-testid=home-about-cta] CTA."
    tag = m.group(0)
    assert not re.search(r'tabindex=[\"\']-1[\"\']', tag), (
        f"CTA NE SME imati tabindex='-1' (mora biti tab-abilan posle wire). Tag: {tag!r}"
    )
