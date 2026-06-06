"""Story 6.2 — <lastmod> iz updated_at; PageSitemap bez lastmod (TEA RED phase).

Pokriva AC9 (SM-D7):
- model <url> (Product) ima <lastmod> izveden iz updated_at (datum prefiks).
- PageSitemap <url> (pages:home) NEMA <lastmod> (statičke strane — OQ-4 omit).

Robustnost: ne asertujemo tačan ISO format/timezone — samo da <lastmod> postoji za
model URL i da sadrži YYYY-MM-DD datum dela updated_at-a; za static-page URL da
<lastmod> NIJE prisutan.

Refs:
- 6-2-...-hreflang.md AC9 + Task 6.7 + SM-D7 + Gotcha SM2-7
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

pytestmark = pytest.mark.django_db

SM_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"


def _url_for_loc_substring(content: bytes, needle: str):
    """Vrati prvi <url> element čiji <loc> sadrži needle (ili None)."""
    root = ET.fromstring(content)
    for url_el in root.findall(f".//{{{SM_NS}}}url"):
        loc_el = url_el.find(f"{{{SM_NS}}}loc")
        if loc_el is not None and loc_el.text and needle in loc_el.text:
            return url_el
    return None


def test_model_url_has_lastmod(client, product):
    response = client.get("/sitemap.xml")
    assert response.status_code == 200

    url_el = _url_for_loc_substring(response.content, product.get_absolute_url())
    assert url_el is not None, "Product <url> mora postojati u sitemap-u."
    lastmod = url_el.find(f"{{{SM_NS}}}lastmod")
    assert lastmod is not None and lastmod.text, (
        "Model <url> (Product) MORA imati <lastmod> iz updated_at (AC9)."
    )
    expected_date = product.updated_at.date().isoformat()
    assert expected_date in lastmod.text, (
        f"<lastmod> ({lastmod.text!r}) MORA reflektovati updated_at datum "
        f"({expected_date}; AC9/SM-D7)."
    )


def test_static_page_url_has_no_lastmod(client):
    from django.urls import reverse

    response = client.get("/sitemap.xml")
    assert response.status_code == 200

    home_path = reverse("pages:home")
    # IMP-4 pattern: loc završava na home_path sufiks (konzistentno sa ostalim testovima).
    root = ET.fromstring(response.content)
    home_url_el = None
    for url_el in root.findall(f".//{{{SM_NS}}}url"):
        loc_el = url_el.find(f"{{{SM_NS}}}loc")
        if loc_el is None or not loc_el.text:
            continue
        if loc_el.text.endswith(home_path):
            home_url_el = url_el
            break

    assert home_url_el is not None, (
        f"PageSitemap home <url> (path {home_path!r}) mora postojati u sitemap-u."
    )
    lastmod = home_url_el.find(f"{{{SM_NS}}}lastmod")
    assert lastmod is None, (
        "PageSitemap <url> (statička strana) NE SME imati <lastmod> (OQ-4/SM-D7)."
    )
