"""Story 6.2 — /sitemap.xml well-formed XML + namespaces (TEA RED phase).

Pokriva AC2 + AC8 (SM-D1/SM-D2):
- GET /sitemap.xml → 200; Content-Type sadrži xml (application/xml ili text/xml).
- Telo je well-formed (ElementTree.fromstring bez ParseError).
- Root element je <urlset> u sitemaps.org/0.9 namespace-u.
- xmlns:xhtml="http://www.w3.org/1999/xhtml" deklaracija prisutna (za alternates).
- Bar 1 <url><loc> sa seed sadržajem.

⚠️ RED-phase: ElementTree parse je POSLE 200-assert-a → kad /sitemap.xml 404-uje
(nije registrovan), test pada na status assert (clean RED), NE na ParseError.
Django može servirati flat <urlset> ILI sitemap index — single sitemap() view sa
dict-om servira flat urlset za sve sekcije; ovde proveravamo urlset.

Refs:
- 6-2-...-hreflang.md AC2/AC8 + Task 6.1 + SM-D1/D2 + Gotcha SM2-1/SM2-2
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

pytestmark = pytest.mark.django_db

SM_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
XHTML_NS = "http://www.w3.org/1999/xhtml"


@pytest.fixture
def seed_one_public(product):
    """Bar jedan javni objekat tako da <urlset> ima >=1 <url> (PageSitemap ionako ima)."""
    return product


def test_sitemap_status_200(client):
    response = client.get("/sitemap.xml")
    assert response.status_code == 200


def test_sitemap_content_type_is_xml(client):
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    content_type = response.headers.get("Content-Type", response.get("Content-Type", ""))
    assert "xml" in content_type.lower(), (
        f"Content-Type MORA sadržati 'xml' (application/xml ili text/xml); dobijeno: {content_type!r}."
    )


def test_sitemap_body_is_well_formed(client, seed_one_public):
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    # Parse MORA biti POSLE 200-assert-a (404 telo bi pucalo ovde umesto na status).
    root = ET.fromstring(response.content)  # raise ParseError → test FAIL ako nije well-formed
    assert root is not None


def test_sitemap_root_is_urlset_in_sitemaps_namespace(client, seed_one_public):
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    root = ET.fromstring(response.content)
    assert root.tag == f"{{{SM_NS}}}urlset", (
        f"Root element MORA biti <urlset> u {SM_NS} namespace-u (AC8); dobijeno: {root.tag!r}."
    )


def test_sitemap_declares_xhtml_namespace(client, seed_one_public):
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    body = response.content.decode("utf-8")
    assert XHTML_NS in body, (
        f"xmlns:xhtml deklaracija ({XHTML_NS}) MORA biti prisutna na <urlset> "
        f"(za <xhtml:link> alternate — AC5/AC8)."
    )


def test_sitemap_has_at_least_one_url_loc(client, seed_one_public):
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    root = ET.fromstring(response.content)
    locs = root.findall(f".//{{{SM_NS}}}loc")
    assert len(locs) >= 1, (
        "Sitemap MORA imati bar jedan <url><loc> sa seed podacima (AC2)."
    )
