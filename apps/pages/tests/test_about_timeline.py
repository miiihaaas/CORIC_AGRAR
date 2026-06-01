"""Story 3.2 — AC6: Vremenska lenta (inline SVG/CSS, min 3 događaja, reveal kontrakt).

RED phase (TEA). Regex parsiranje (projekat nema BeautifulSoup).

JS unit testovi van scope-a (mirror statistic-counter.js) — IntersectionObserver
behavior je manuelni smoke (Task 8). TEA verifikuje JS KONTRAKT kroz markup:
- data-timeline root + data-timeline-segment po događaju (timeline-reveal.js selektori)
- timeline-reveal.js učitan SAMO na about strani (about.html block scripts)
- NO-JS fallback: hidden stanje NIJE bezuslovno na segmentu (gejtovano coric-js markerom)

RED razlog: _about_timeline.html ne postoji → GET 404 → pad na status assertion-u.

AC6 — 5 testova:
- test_timeline_renders_min_3_events             (>=3 [data-timeline-segment])
- test_timeline_event_has_year_title_description (svaki segment: godina + h3 + opis)
- test_timeline_decorative_svg_aria_hidden       (SVG čvorovi/linija aria-hidden)
- test_timeline_text_content_not_in_svg_text     (godina/naslov/opis NE u SVG <text>)
- test_timeline_reveal_js_loaded_per_page        (timeline-reveal.js u about.html, NE base)

Pokrenuti:
    just test apps/pages/tests/test_about_timeline.py -v
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


def _timeline_block(html: str) -> str:
    """Izvuci <ol ... data-timeline> ... </ol> blok lente."""
    m = re.search(r"<ol\b[^>]*data-timeline\b.*?</ol>", html, re.IGNORECASE | re.DOTALL)
    return m.group(0) if m else ""


def _segments(html: str) -> list[str]:
    """Vrati listu <li ... data-timeline-segment> ... </li> blokova."""
    return re.findall(
        r"<li\b[^>]*data-timeline-segment\b.*?</li>", html, re.IGNORECASE | re.DOTALL
    )


def test_timeline_renders_min_3_events(client):
    """AC6: lenta ima MIN 3 događaja ([data-timeline-segment])."""
    html = _about_html(client)
    block = _timeline_block(html)
    assert block, (
        "Vremenska lenta MORA biti <ol data-timeline> (timeline-reveal.js root)."
    )
    segments = _segments(block)
    assert len(segments) >= 3, (
        f"Vremenska lenta MORA imati MIN 3 događaja [data-timeline-segment] (epics.md AC), "
        f"pronađeno {len(segments)}."
    )


def test_timeline_event_has_year_title_description(client):
    """AC6: svaki događaj ima godinu + h3 naslov + opis (<p>) — semantički HTML."""
    html = _about_html(client)
    block = _timeline_block(html)
    segments = _segments(block)
    assert segments, "Lenta MORA imati bar 1 [data-timeline-segment]."
    for i, seg in enumerate(segments, start=1):
        assert re.search(r"\b(19|20)\d{2}\b", seg), (
            f"Segment #{i} MORA sadržati godinu (4-cifreni broj). Segment: {seg!r}"
        )
        assert re.search(r"<h3\b[^>]*>.*?</h3>", seg, re.IGNORECASE | re.DOTALL), (
            f"Segment #{i} MORA imati <h3> naslov događaja. Segment: {seg!r}"
        )
        assert re.search(r"<p\b[^>]*>.*?</p>", seg, re.IGNORECASE | re.DOTALL), (
            f"Segment #{i} MORA imati <p> opis događaja. Segment: {seg!r}"
        )


def test_timeline_decorative_svg_aria_hidden(client):
    """AC6: dekorativni SVG/CSS čvorovi/linija lente imaju aria-hidden='true'.

    Lock (epics.md AC + contract:142 „dekorativni SVG/CSS čvorovi + linija lente:
    aria-hidden=true"): lenta sme biti inline SVG ILI ČIST CSS (čvorovi/linija kao
    <div>/<span>/<svg> bez teksta). Zahtev NIJE prisustvo <svg> taga (CSS-only
    implementacija je validna — mirror SM-D8 masonry „ČIST CSS"), nego:
      (1) lenta MORA imati bar jedan dekorativni element označen aria-hidden='true';
      (2) AKO postoji inline <svg>, MORA biti aria-hidden (NE izložen AT-u).
    """
    html = _about_html(client)
    block = _timeline_block(html)
    assert block, "Lenta MORA biti <ol data-timeline>."

    # (1) Bar jedan dekorativni element u lenti je aria-hidden='true'
    #     (SVG čvor/linija ILI CSS čvor <span>/<div> — SM-D7/contract:142).
    aria_hidden_decorative = re.findall(
        r"<(?:svg|span|div|i|b)\b[^>]*aria-hidden=[\"']true[\"'][^>]*>",
        block,
        re.IGNORECASE,
    )
    assert aria_hidden_decorative, (
        "Lenta MORA imati bar jedan dekorativni čvor/liniju označen aria-hidden='true' "
        "(SVG ILI CSS element — epics.md AC). Nije pronađen nijedan aria-hidden dekor."
    )

    # (2) Svaki inline <svg> (ako postoji) MORA biti aria-hidden — dekorativan, ne AT.
    for svg in re.findall(r"<svg\b[^>]*>", block, re.IGNORECASE):
        assert 'aria-hidden="true"' in svg.lower() or "aria-hidden='true'" in svg.lower(), (
            f"Dekorativni SVG element lente MORA biti aria-hidden='true'. Tag: {svg!r}"
        )


def test_timeline_text_content_not_in_svg_text(client):
    """AC6: tekstualni sadržaj (godina/naslov/opis) je semantički HTML, NE u SVG <text>.

    AT-čitljivost: SVG <text> elementi se NE smeju koristiti za sadržaj događaja.
    """
    html = _about_html(client)
    block = _timeline_block(html)
    assert block, "Lenta MORA biti <ol data-timeline>."
    svg_text = re.findall(r"<text\b[^>]*>.*?</text>", block, re.IGNORECASE | re.DOTALL)
    assert not svg_text, (
        "Tekstualni sadržaj lente (godina/naslov/opis) NE SME biti u SVG <text> "
        f"(mora biti semantički HTML — čitljiv AT-u). Pronađeno SVG <text>: {svg_text!r}"
    )


def test_timeline_reveal_js_loaded_per_page(client):
    """AC6/SM-D7: timeline-reveal.js učitan SAMO na about strani (about.html block scripts).

    Verifikuje da render uključuje <script src=".../timeline-reveal.js">.
    """
    html = _about_html(client)
    assert re.search(r"<script\b[^>]*timeline-reveal\.js[^>]*>", html, re.IGNORECASE), (
        "About strana MORA učitati timeline-reveal.js (about.html {% block scripts %}). "
        "RED: skripta još ne postoji / nije uključena."
    )
