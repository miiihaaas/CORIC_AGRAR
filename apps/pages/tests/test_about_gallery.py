"""Story 3.2 — AC7: Masonry galerija + GLightbox REUSE (NULA novog JS).

RED phase (TEA). Regex parsiranje (projekat nema BeautifulSoup).

RED razlog: _about_gallery.html ne postoji → GET 404 → pad na status assertion-u.

AC7 — 4 testa:
- test_gallery_renders_min_6_glightbox_links  (>=6 a.glightbox)
- test_gallery_links_share_data_gallery_group (svi data-gallery='o-nama-galerija')
- test_gallery_images_have_descriptive_alt    (img alt NIJE prazan — informativna)
- test_gallery_images_lazy_loaded             (loading='lazy')

Pokrenuti:
    just test apps/pages/tests/test_about_gallery.py -v
"""

from __future__ import annotations

import re

import pytest
from django.utils.translation import activate

pytestmark = pytest.mark.django_db


def _about_html(client) -> str:
    activate("sr")
    response = client.get("/sr/o-nama/")
    assert response.status_code == 200, (
        f"GET /sr/o-nama/ MORA biti 200, dobio {response.status_code} "
        "(RED: AboutView/template ne postoji)."
    )
    return response.content.decode("utf-8")


def _glightbox_links(html: str) -> list[str]:
    """Vrati listu <a ...class=...glightbox...> ... </a> linkova galerije."""
    anchors = re.findall(r"<a\b[^>]*>.*?</a>", html, re.IGNORECASE | re.DOTALL)
    return [a for a in anchors if re.search(r"class=[\"'][^\"']*\bglightbox\b", a, re.IGNORECASE)]


def test_gallery_renders_min_6_glightbox_links(client):
    """AC7: galerija ima MIN 6 <a class='glightbox'> linkova (6-9 slika)."""
    html = _about_html(client)
    links = _glightbox_links(html)
    assert len(links) >= 6, (
        f"Galerija MORA imati MIN 6 <a class='glightbox'> linkova (6-9 slika; SM-D8), "
        f"pronađeno {len(links)}."
    )


def test_gallery_links_share_data_gallery_group(client):
    """AC7: SVI galerijski linkovi imaju data-gallery='o-nama-galerija' (GLightbox grupisanje)."""
    html = _about_html(client)
    links = _glightbox_links(html)
    assert links, "Galerija MORA imati bar 1 .glightbox link."
    for a in links:
        assert re.search(
            r"data-gallery=[\"']o-nama-galerija[\"']", a, re.IGNORECASE
        ), (
            "Svaki galerijski link MORA imati data-gallery='o-nama-galerija' "
            f"(grupisanje za prev/next navigaciju). Link: {a!r}"
        )


def test_gallery_images_have_descriptive_alt(client):
    """AC7/SM-D10: svaki galerijski <img> ima OPISNI (neprazan) alt (informativna galerija)."""
    html = _about_html(client)
    links = _glightbox_links(html)
    assert links, "Galerija MORA imati bar 1 .glightbox link sa <img>."
    for a in links:
        img_match = re.search(r"<img\b[^>]*>", a, re.IGNORECASE)
        assert img_match, f"Galerijski link MORA sadržati <img>. Link: {a!r}"
        img = img_match.group(0)
        alt_match = re.search(r"alt=[\"']([^\"']*)[\"']", img, re.IGNORECASE)
        assert alt_match is not None and alt_match.group(1).strip() != "", (
            "Galerijski <img> MORA imati OPISNI (neprazan) alt (informativna galerija, "
            f"SM-D10 — NE prazan kao dekorativna hero pozadina). Img: {img!r}"
        )


def test_gallery_images_lazy_loaded(client):
    """AC7: svaki galerijski thumbnail je loading='lazy' (ispod fold-a)."""
    html = _about_html(client)
    links = _glightbox_links(html)
    assert links, "Galerija MORA imati bar 1 .glightbox link sa <img>."
    for a in links:
        img_match = re.search(r"<img\b[^>]*>", a, re.IGNORECASE)
        assert img_match, f"Galerijski link MORA sadržati <img>. Link: {a!r}"
        img = img_match.group(0)
        assert re.search(r'loading=[\"\']lazy[\"\']', img, re.IGNORECASE), (
            f"Galerijski thumbnail MORA imati loading='lazy'. Img: {img!r}"
        )
