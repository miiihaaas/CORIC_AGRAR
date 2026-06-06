"""Story 6.2 — HREFLANG alternates sr/hu/en (TEA RED phase).

Pokriva AC5 (SM-D1):
- svaki <url> ima <xhtml:link rel="alternate" hreflang="sr|hu|en" href="...">.
- href je locale-prefiksovan (hreflang="hu" → /hu/...).
- sva 3 koda (sr/hu/en) prisutna; vrednosti su TAČNO LANGUAGES kodovi.
- generisano Django built-in-om (i18n=True+alternates=True), NE hand-rolled.

IMP-5: namespace-aware parse — root.findall(".//{http://www.w3.org/1999/xhtml}link"),
NE bare "xhtml:link" string (ElementTree ga ne razrešava).

Refs:
- 6-2-...-hreflang.md AC5 + Task 6.4 + SM-D1 + Gotcha SM2-1 + TEA napomene IMP-5
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

pytestmark = pytest.mark.django_db

SM_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
XHTML_NS = "http://www.w3.org/1999/xhtml"
EXPECTED_LANGS = {"sr", "hu", "en"}


@pytest.fixture
def seeded(product, post):
    return product, post


def test_url_elements_have_xhtml_alternate_links(client, seeded):
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    root = ET.fromstring(response.content)

    url_elements = root.findall(f".//{{{SM_NS}}}url")
    assert url_elements, "Sitemap MORA imati bar jedan <url> element (seed prisutan)."

    for url_el in url_elements:
        alt_links = url_el.findall(f"{{{XHTML_NS}}}link")
        assert alt_links, (
            "Svaki <url> MORA imati <xhtml:link> alternate elemente "
            "(alternates=True; AC5)."
        )
        langs = set()
        for link in alt_links:
            assert link.get("rel") == "alternate", (
                f"<xhtml:link> MORA imati rel='alternate'; dobijeno: {link.get('rel')!r}."
            )
            hreflang = link.get("hreflang")
            assert hreflang is not None, "<xhtml:link> MORA imati hreflang atribut."
            langs.add(hreflang)
        assert EXPECTED_LANGS.issubset(langs), (
            f"Svaki <url> MORA pokriti hreflang {EXPECTED_LANGS}; dobijeno: {langs}."
        )


def test_alternate_hrefs_are_locale_prefixed(client, seeded):
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    root = ET.fromstring(response.content)

    links = root.findall(f".//{{{XHTML_NS}}}link")
    assert links, "MORA postojati bar jedan <xhtml:link> alternate (AC5)."

    by_lang: dict[str, list[str]] = {"sr": [], "hu": [], "en": []}
    for link in links:
        lang = link.get("hreflang")
        href = link.get("href", "")
        if lang in by_lang:
            by_lang[lang].append(href)

    for lang, prefix in (("sr", "/sr/"), ("hu", "/hu/"), ("en", "/en/")):
        assert by_lang[lang], f"MORA postojati alternate za hreflang={lang} (AC5)."
        assert any(prefix in href for href in by_lang[lang]), (
            f"hreflang={lang} href MORA biti locale-prefiksovan ({prefix}); "
            f"dobijeno: {by_lang[lang]!r}."
        )


def test_hreflang_values_are_exactly_languages_codes(client, seeded):
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    root = ET.fromstring(response.content)

    links = root.findall(f".//{{{XHTML_NS}}}link")
    found_langs = {link.get("hreflang") for link in links}
    # x-default je DEFER (OQ-2) — ignoriši ako ga Dev doda; SVE od sr/hu/en mora biti tu.
    assert EXPECTED_LANGS.issubset(found_langs), (
        f"hreflang vrednosti MORAJU pokriti TAČNO LANGUAGES kodove {EXPECTED_LANGS}; "
        f"dobijeno: {found_langs}."
    )
