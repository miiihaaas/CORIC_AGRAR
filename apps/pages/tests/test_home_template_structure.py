"""Story 3.1 — AC3 + AC10: home.html struktura, 7 sekcija redom, a11y, i18n.

RED phase (TEA). Projekat NEMA BeautifulSoup (pyproject.toml) — koristimo regex
parsiranje rendrovanog HTML-a (mirror apps/brands/tests/test_brand_coming_soon.py).

AC3+AC10 — 7 testova:
- test_home_renders_exactly_one_h1
- test_home_renders_exactly_one_main           (iz base.html — NE dupliran)
- test_home_renders_7_sections_in_order
- test_home_each_section_has_aria_landmark      (aria-labelledby/aria-label)
- test_home_heading_hierarchy_no_skip           (h1->h2->h3)
- test_home_no_cirillic_in_rendered_html
- test_home_renders_serbian_diacritics_not_sisana_latinica

Pokrenuti:
    docker compose -f compose/local.yml exec django python -m pytest \\
        apps/pages/tests/test_home_template_structure.py -v
"""

from __future__ import annotations

import re

import pytest
from django.utils.translation import activate

from .conftest import assert_home_template, make_traktori_brand

pytestmark = pytest.mark.django_db

_SECTION_RE = re.compile(r"<section\b[^>]*>", re.IGNORECASE)
_MAIN_RE = re.compile(r"<main\b[^>]*>", re.IGNORECASE)
_H1_RE = re.compile(r"<h1\b[^>]*>", re.IGNORECASE)
_HEADING_RE = re.compile(r"<h([1-6])\b[^>]*>", re.IGNORECASE)


def _get_home_html(client) -> str:
    activate("sr")
    make_traktori_brand(name="Struktura Traktor Brend")
    response = client.get("/sr/")
    assert response.status_code == 200, (
        "Home mora vratiti 200 da bi se HTML mogao parsirati (RED: HomeView ne postoji)."
    )
    assert_home_template(response)
    return response.content.decode("utf-8")


def test_home_renders_exactly_one_h1(client):
    """AC3/AC10: TAČNO 1 <h1> na strani (slogan kroz hero_overlay_card)."""
    html = _get_home_html(client)
    h1s = _H1_RE.findall(html)
    assert len(h1s) == 1, (
        f"Home MORA imati TAČNO 1 <h1> (single-h1 pravilo), pronađeno {len(h1s)}."
    )


def test_home_renders_exactly_one_main(client):
    """AC3/AC10: single <main> (iz base.html — home NE dodaje drugi)."""
    html = _get_home_html(client)
    mains = _MAIN_RE.findall(html)
    assert len(mains) == 1, (
        f"Home MORA imati TAČNO 1 <main> (base.html landmark, NE dupliran), "
        f"pronađeno {len(mains)}."
    )


def test_home_renders_7_sections_in_order(client):
    """AC3/SM-D3: 7 sekcija u TAČNOM redu — hero -> o-nama -> traktori -> prikljucna ->
    radne-masine -> polovna -> price-sa-polja. Verifikuje rastući redosled pozicija
    karakterističnih markera u DOM-u.
    """
    html = _get_home_html(client)

    markers = [
        ("hero (slogan)", "Prijatelj koji razume zemlju"),
        ("o-nama eyebrow", "O NAMA"),
        ("traktori eyebrow", "TRAKTORI"),
        ("prikljucna eyebrow", "PRIKLJU"),
        ("radne-masine eyebrow", "RADNE MA"),
        ("polovna eyebrow", "POLOVNA"),
        ("price-sa-polja eyebrow", "PRIČE"),  # finalno proveravamo nezavisno ispod
    ]

    positions = []
    for label, marker in markers[:-1]:
        idx = html.find(marker)
        assert idx != -1, f"Sekcija '{label}' (marker {marker!r}) nije pronađena u render-u."
        positions.append((label, idx))

    # "PRIČE SA POLJA" eyebrow mora doći POSLE "POLOVNA". Marker "PRIČE" (sa č) je
    # specifičan eyebrow-u 7. sekcije — ne hvata "PRIKLJUČNA" (3. sekcija) niti generičke
    # ASCII tokene poput "priority"/"PRI". Dijakritike su verifikovane susednim testom
    # test_home_renders_serbian_diacritics_not_sisana_latinica (č je siguran).
    price_idx = html.find("PRIČE", positions[-1][1] + 1)
    assert price_idx != -1, (
        "Sekcija 'price-sa-polja' (eyebrow 'PRIČE SA POLJA') nije pronađena posle POLOVNA."
    )
    positions.append(("price-sa-polja eyebrow", price_idx))

    ordered_positions = [p for _, p in positions]
    assert ordered_positions == sorted(ordered_positions), (
        "7 sekcija MORAJU biti u TAČNOM redu (SM-D3): hero -> o-nama -> traktori -> "
        "prikljucna -> radne-masine -> polovna -> price-sa-polja. "
        f"Detektovane pozicije: {positions!r}"
    )

    # I bar 7 <section> elemenata.
    sections = _SECTION_RE.findall(html)
    assert len(sections) >= 7, (
        f"Home MORA imati bar 7 <section> elemenata (po sekciji), pronađeno {len(sections)}."
    )


def test_home_each_section_has_aria_landmark(client):
    """AC3/AC10: svaki <section> ima aria-labelledby ILI aria-label (a11y landmark)."""
    html = _get_home_html(client)
    sections = _SECTION_RE.findall(html)
    assert sections, "Home mora imati bar 1 <section>."
    for tag in sections:
        assert ("aria-labelledby" in tag.lower()) or ("aria-label" in tag.lower()), (
            f"Svaki <section> MORA imati aria-labelledby/aria-label. Bez landmark-a: {tag!r}"
        )


def test_home_heading_hierarchy_no_skip(client):
    """AC3/AC10: heading hijerarhija h1->h2->h3 bez preskoka (nema h1 pa odmah h4 itd.)."""
    html = _get_home_html(client)
    levels = [int(m) for m in _HEADING_RE.findall(html)]
    assert levels, "Home mora imati bar jedan heading."
    assert levels[0] == 1, f"Prvi heading na strani MORA biti <h1>, dobio h{levels[0]}."
    max_seen = 0
    for lvl in levels:
        assert lvl <= max_seen + 1, (
            f"Heading hijerarhija preskače nivo (sa h{max_seen} na h{lvl}). "
            f"Sekvenca nivoa: {levels!r}"
        )
        max_seen = max(max_seen, lvl)


def test_home_no_cirillic_in_rendered_html(client):
    """AC10: NEMA ćirilice u rendrovanom HTML-u (sve Srpsko je latinica)."""
    html = _get_home_html(client)
    cyrillic = re.findall(r"[Ѐ-ӿ]", html)
    assert not cyrillic, (
        f"Rendrovani HTML NE SME sadržati ćirilične karaktere, pronađeno: {set(cyrillic)!r}"
    )


def test_home_renders_serbian_diacritics_not_sisana_latinica(client):
    """AC10: Srpski tekst koristi pune dijakritike (č/ć/ž/š/đ), NE šišanu latinicu.

    Slogan 'Prijatelj koji razume zemlju!' nema dijakritike, ali eyebrow-i imaju
    (PRIKLJUČNA, RADNE MAŠINE, PRIČE). Verifikujemo da je bar jedan diacritic prisutan
    i da NIJE degradiran u ASCII (npr. 'PRIKLJUCNA' šišana forma).
    """
    html = _get_home_html(client)
    # Bar jedan od očekivanih dijakritičkih string-ova mora biti prisutan u punoj formi.
    full_forms = ["PRIKLJUČNA", "RADNE MAŠINE", "PRIČE", "mašine", "priče"]
    assert any(form in html for form in full_forms), (
        "Rendrovani HTML MORA sadržati Srpski tekst sa punim dijakriticima (č/ć/ž/š/đ). "
        f"Nijedna od punih formi {full_forms!r} nije pronađena — proveri šišanu latinicu."
    )
    # Negativni guard: šišane forme NE smeju biti jedino prisutne.
    assert "PRIKLJUCNA" not in html, (
        "Detektovana ŠIŠANA latinica 'PRIKLJUCNA' (bez Č) — mora biti 'PRIKLJUČNA'."
    )
