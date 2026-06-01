"""Story 3.3 — AC3 + AC8: contact.html struktura, 3 sekcije redom, a11y, i18n.

RED phase (TEA). Regex parsiranje (projekat nema BeautifulSoup — mirror
test_about_template_structure.py).

RED razlog: pages/contact.html ne postoji → GET /sr/kontakt/ je 404 → parsiranje pada
na status_code assertion-u (RED iz pravog razloga: ContactView/template ne postoje).

NORMATIVNI DOM redosled (SM-D9): info → forma → mapa (semantički reading-order;
CSS vizuelni layout je ZASEBAN izbor — testiramo SAMO source/DOM redosled).

AC3 + AC8 — 5 testova (+ multi-locale h1 smoke + meta description):
- test_contact_renders_exactly_one_h1
- test_contact_renders_exactly_one_main           (iz base.html — NE dupliran)
- test_contact_renders_3_sections_in_order        (info -> forma -> mapa)
- test_contact_each_section_has_aria_landmark
- test_contact_no_cirillic_in_rendered_html

Pokrenuti:
    just test apps/pages/tests/test_contact_template_structure.py -v
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


def _contact_html(client, lang: str = "sr") -> str:
    activate(lang)
    response = client.get(f"/{lang}/kontakt/")
    assert response.status_code == 200, (
        f"GET /{lang}/kontakt/ MORA biti 200 da bi se HTML parsirao, dobio "
        f"{response.status_code} (RED: ContactView/pages/contact.html ne postoji)."
    )
    template_names = [t.name for t in response.templates if t.name]
    assert "pages/contact.html" in template_names, (
        f"Render MORA koristiti 'pages/contact.html', dobio {template_names!r}."
    )
    return response.content.decode("utf-8")


def test_contact_renders_exactly_one_h1(client):
    """AC3/SM-D10: TAČNO 1 <h1> (page title — „Kontakt"/„Kontaktirajte nas")."""
    html = _contact_html(client)
    h1s = _H1_RE.findall(html)
    assert len(h1s) == 1, (
        f"Kontakt MORA imati TAČNO 1 <h1> (single-h1 pravilo), pronađeno {len(h1s)}."
    )


def test_contact_renders_exactly_one_main(client):
    """AC3: single <main> (iz base.html — contact NE dodaje drugi)."""
    html = _contact_html(client)
    mains = _MAIN_RE.findall(html)
    assert len(mains) == 1, (
        f"Kontakt MORA imati TAČNO 1 <main> (base.html landmark, NE dupliran), "
        f"pronađeno {len(mains)}."
    )


def test_contact_renders_3_sections_in_order(client):
    """AC3/SM-D9: 3 bloka u NORMATIVNOM DOM redu — info -> forma -> mapa.

    Verifikuje rastući redosled pozicija karakterističnih markera u DOM-u
    (NE proverava CSS layout — vizuelni raspored je ZASEBAN Dev izbor).
    """
    html = _contact_html(client)

    # Karakteristični markeri po bloku (nezavisni od tačnog copy-ja).
    info_idx = re.search(r'id=[\"\']contact-info-title[\"\']', html)
    form_idx = re.search(r'id=[\"\']contact-form-title[\"\']', html)
    map_idx = re.search(r'id=[\"\']contact-map-title[\"\']', html)

    assert info_idx, "Kontakt-info blok (id=contact-info-title) nije pronađen."
    assert form_idx, "Forma blok (id=contact-form-title) nije pronađen."
    assert map_idx, "Mapa blok (id=contact-map-title) nije pronađen."

    positions = [
        ("info", info_idx.start()),
        ("forma", form_idx.start()),
        ("mapa", map_idx.start()),
    ]
    ordered = [p for _, p in positions]
    assert ordered == sorted(ordered), (
        "3 bloka MORAJU biti u NORMATIVNOM DOM redu (SM-D9): info -> forma -> mapa. "
        f"Detektovane pozicije: {positions!r}"
    )

    sections = _SECTION_RE.findall(html)
    assert len(sections) >= 3, (
        f"Kontakt MORA imati bar 3 <section> elementa (po bloku), pronađeno {len(sections)}."
    )


def test_contact_each_section_has_aria_landmark(client):
    """AC3/AC9: svaki <section> ima aria-labelledby ILI aria-label (a11y landmark)."""
    html = _contact_html(client)
    sections = _SECTION_RE.findall(html)
    assert sections, "Kontakt mora imati bar 1 <section>."
    for tag in sections:
        assert ("aria-labelledby" in tag.lower()) or ("aria-label" in tag.lower()), (
            f"Svaki <section> MORA imati aria-labelledby/aria-label. Bez landmark-a: {tag!r}"
        )


def test_contact_no_cirillic_in_rendered_html(client):
    """AC8: NEMA ćirilice u renderovanom HTML-u (sve Srpsko je latinica pune dijakritike)."""
    html = _contact_html(client)
    cyrillic = re.findall(r"[Ѐ-ӿ]", html)
    assert not cyrillic, (
        f"Renderovani HTML NE SME sadržati ćirilične karaktere, pronađeno: {set(cyrillic)!r}"
    )


def test_contact_heading_hierarchy_no_skip(client):
    """AC3/AC9: heading hijerarhija h1->h2(->h3) bez preskoka."""
    html = _contact_html(client)
    levels = [int(m) for m in _HEADING_RE.findall(html)]
    assert levels, "Kontakt mora imati bar jedan heading."
    assert levels[0] == 1, f"Prvi heading na strani MORA biti <h1>, dobio h{levels[0]}."
    max_seen = 0
    for lvl in levels:
        assert lvl <= max_seen + 1, (
            f"Heading hijerarhija preskače nivo (sa h{max_seen} na h{lvl}). "
            f"Sekvenca nivoa: {levels!r}"
        )
        max_seen = max(max_seen, lvl)


def test_contact_has_non_empty_translatable_meta_description(client):
    """AC3: <meta name='description'> postoji + NEPRAZAN (kroz {% translate %}).

    NAPOMENA (story AC3): TEA NE asertira tačan literal meta teksta — samo da meta
    postoji + sadržaj neprazan/translatable (renderovan ne-prazno).
    """
    html = _contact_html(client)
    m = _META_DESC_RE.search(html)
    assert m, "Kontakt MORA imati <meta name='description' content='...'> (AC3 block)."
    content = m.group(1).strip()
    assert content, (
        "meta description content MORA biti neprazan (kroz {% translate %}). "
        f"Dobio prazan/whitespace: {m.group(1)!r}"
    )


@pytest.mark.parametrize("lang", ["sr", "hu", "en"])
def test_contact_renders_exactly_one_h1_per_locale(client, lang):
    """AC3 (multi-locale smoke): TAČNO 1 <h1> u sva 3 locale.

    Hvata locale-uslovljenu DOM regresiju (npr. {% if LANGUAGE_CODE %} oko h1).
    """
    html = _contact_html(client, lang)
    h1s = _H1_RE.findall(html)
    assert len(h1s) == 1, (
        f"Kontakt ({lang}) MORA imati TAČNO 1 <h1> (single-h1 pravilo), "
        f"pronađeno {len(h1s)}."
    )
