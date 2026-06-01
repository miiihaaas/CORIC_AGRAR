"""Story 3.2 — AC3 + AC9: about.html struktura, 4 sekcije redom, a11y, i18n.

RED phase (TEA). Regex parsiranje (projekat nema BeautifulSoup — mirror
test_home_template_structure.py).

RED razlog: pages/about.html ne postoji → GET /sr/o-nama/ je 404 → parsiranje pada
na status_code assertion-u (RED iz pravog razloga: AboutView/template ne postoje).

AC3 + AC9 — 7 testova:
- test_about_renders_exactly_one_h1
- test_about_renders_exactly_one_main          (iz base.html — NE dupliran)
- test_about_renders_4_sections_in_order       (hero -> nasa-prica -> lenta -> galerija)
- test_about_each_section_has_aria_landmark
- test_about_heading_hierarchy_no_skip          (h1->h2->h3)
- test_about_no_cirillic_in_rendered_html
- test_about_has_non_empty_translatable_meta_description

Pokrenuti:
    just test apps/pages/tests/test_about_template_structure.py -v
"""

from __future__ import annotations

import re

import pytest
from django.utils.translation import activate

pytestmark = pytest.mark.django_db

_SECTION_RE = re.compile(r"<section\b[^>]*>", re.IGNORECASE)
_MAIN_RE = re.compile(r"<main\b[^>]*>", re.IGNORECASE)
_H1_RE = re.compile(r"<h1\b[^>]*>", re.IGNORECASE)
_HEADING_RE = re.compile(r"<h([1-6])\b[^>]*>", re.IGNORECASE)
_META_DESC_RE = re.compile(
    r"<meta\b[^>]*name=[\"']description[\"'][^>]*content=[\"']([^\"']*)[\"'][^>]*>",
    re.IGNORECASE,
)


def _about_html(client, lang: str = "sr") -> str:
    activate(lang)
    response = client.get(f"/{lang}/o-nama/")
    assert response.status_code == 200, (
        f"GET /{lang}/o-nama/ MORA biti 200 da bi se HTML parsirao, dobio "
        f"{response.status_code} (RED: AboutView/pages/about.html ne postoji)."
    )
    template_names = [t.name for t in response.templates if t.name]
    assert "pages/about.html" in template_names, (
        f"Render MORA koristiti 'pages/about.html', dobio {template_names!r}."
    )
    return response.content.decode("utf-8")


def test_about_renders_exactly_one_h1(client):
    """AC3: TAČNO 1 <h1> (kroz hero_overlay_card)."""
    html = _about_html(client)
    h1s = _H1_RE.findall(html)
    assert len(h1s) == 1, (
        f"About MORA imati TAČNO 1 <h1> (single-h1 pravilo), pronađeno {len(h1s)}."
    )


def test_about_renders_exactly_one_main(client):
    """AC3: single <main> (iz base.html — about NE dodaje drugi)."""
    html = _about_html(client)
    mains = _MAIN_RE.findall(html)
    assert len(mains) == 1, (
        f"About MORA imati TAČNO 1 <main> (base.html landmark, NE dupliran), "
        f"pronađeno {len(mains)}."
    )


def test_about_renders_4_sections_in_order(client):
    """AC3/SM-D4: 4 sekcije u TAČNOM redu — hero -> naša-priča -> vremenska-lenta -> galerija.

    Verifikuje rastući redosled pozicija karakterističnih markera u DOM-u.
    """
    html = _about_html(client)

    # Karakteristični markeri po sekciji (nezavisni od tačnog copy-ja).
    hero_idx = re.search(r"coric-about-hero", html)
    story_idx = re.search(r'id=[\"\']about-story-title[\"\']', html)
    timeline_idx = re.search(r"data-timeline\b", html)
    gallery_idx = re.search(r'id=[\"\']about-galerija-title[\"\']', html)

    assert hero_idx, "Hero sekcija (coric-about-hero) nije pronađena."
    assert story_idx, "Naša priča sekcija (id=about-story-title) nije pronađena."
    assert timeline_idx, "Vremenska lenta (data-timeline) nije pronađena."
    assert gallery_idx, "Galerija (id=about-galerija-title) nije pronađena."

    positions = [
        ("hero", hero_idx.start()),
        ("naša-priča", story_idx.start()),
        ("vremenska-lenta", timeline_idx.start()),
        ("galerija", gallery_idx.start()),
    ]
    ordered = [p for _, p in positions]
    assert ordered == sorted(ordered), (
        "4 sekcije MORAJU biti u TAČNOM redu (SM-D4): hero -> naša-priča -> "
        f"vremenska-lenta -> galerija. Detektovane pozicije: {positions!r}"
    )

    sections = _SECTION_RE.findall(html)
    assert len(sections) >= 4, (
        f"About MORA imati bar 4 <section> elemenata (po sekciji), pronađeno {len(sections)}."
    )


def test_about_each_section_has_aria_landmark(client):
    """AC3/AC10: svaki <section> ima aria-labelledby ILI aria-label (a11y landmark)."""
    html = _about_html(client)
    sections = _SECTION_RE.findall(html)
    assert sections, "About mora imati bar 1 <section>."
    for tag in sections:
        assert ("aria-labelledby" in tag.lower()) or ("aria-label" in tag.lower()), (
            f"Svaki <section> MORA imati aria-labelledby/aria-label. Bez landmark-a: {tag!r}"
        )


def test_about_heading_hierarchy_no_skip(client):
    """AC3/AC10: heading hijerarhija h1->h2->h3 bez preskoka."""
    html = _about_html(client)
    levels = [int(m) for m in _HEADING_RE.findall(html)]
    assert levels, "About mora imati bar jedan heading."
    assert levels[0] == 1, f"Prvi heading na strani MORA biti <h1>, dobio h{levels[0]}."
    max_seen = 0
    for lvl in levels:
        assert lvl <= max_seen + 1, (
            f"Heading hijerarhija preskače nivo (sa h{max_seen} na h{lvl}). "
            f"Sekvenca nivoa: {levels!r}"
        )
        max_seen = max(max_seen, lvl)


def test_about_no_cirillic_in_rendered_html(client):
    """AC9: NEMA ćirilice u renderovanom HTML-u (sve Srpsko je latinica)."""
    html = _about_html(client)
    cyrillic = re.findall(r"[Ѐ-ӿ]", html)
    assert not cyrillic, (
        f"Renderovani HTML NE SME sadržati ćirilične karaktere, pronađeno: {set(cyrillic)!r}"
    )


def test_about_has_non_empty_translatable_meta_description(client):
    """AC3: <meta name='description'> postoji + NEPRAZAN (kroz {% translate %}).

    NAPOMENA (story AC3): TEA NE asertira tačan literal meta teksta (copy je biznis/8.8
    input) — samo da meta postoji + sadržaj neprazan/translatable (renderovan ne-prazno).
    """
    html = _about_html(client)
    m = _META_DESC_RE.search(html)
    assert m, "About MORA imati <meta name='description' content='...'> (AC3 block)."
    content = m.group(1).strip()
    assert content, (
        "meta description content MORA biti neprazan (kroz {% translate %}). "
        f"Dobio prazan/whitespace: {m.group(1)!r}"
    )


@pytest.mark.parametrize("lang", ["sr", "hu", "en"])
def test_about_renders_exactly_one_h1_per_locale(client, lang):
    """AC3 (multi-locale smoke): TAČNO 1 <h1> u sva 3 locale.

    Hvata locale-uslovljenu DOM regresiju (npr. {% if LANGUAGE_CODE %} oko h1).
    """
    html = _about_html(client, lang)
    h1s = _H1_RE.findall(html)
    assert len(h1s) == 1, (
        f"About ({lang}) MORA imati TAČNO 1 <h1> (single-h1 pravilo), "
        f"pronađeno {len(h1s)}."
    )


def test_about_keeps_site_wide_lightbox_script(client):
    """AC3: {% block scripts %}{{ block.super }} ZADRŽAVA site-wide lightbox-init.js.

    Galerija REUSE-uje GLightbox/lightbox-init.js (učitan u base.html). Ako neko ukloni
    `{{ block.super }}` iz about.html scripts bloka, skripta nestaje i galerija puca —
    ovaj test to hvata.
    """
    html = _about_html(client)
    assert re.search(r"lightbox-init\.js", html), (
        "About MORA i dalje učitavati site-wide 'lightbox-init.js' "
        "(scripts blok MORA zadržati {{ block.super }} za GLightbox galeriju)."
    )
