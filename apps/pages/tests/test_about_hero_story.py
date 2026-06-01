"""Story 3.2 — AC4 + AC5: Hero sekcija + „Naša priča" tekst sekcija.

RED phase (TEA). Regex parsiranje (projekat nema BeautifulSoup).

RED razlog: _about_hero.html / _about_story.html ne postoje → about.html ne postoji
-> GET 404 -> pad na status assertion-u.

AC4 + AC5 — 4 testa:
- test_about_hero_includes_overlay_card_green_variant (hero_overlay_card variant=green; h1)
- test_about_hero_bg_image_is_decorative              (foto-pozadina alt='' + aria-hidden)
- test_about_story_has_decorative_watermark_logo_aria_hidden
- test_about_story_section_has_text_paragraphs        (>=2 <p> u naša-priča sekciji)

Pokrenuti:
    just test apps/pages/tests/test_about_hero_story.py -v
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


def _hero_section(html: str) -> str:
    """Izvuci <section ...> ... </section> hero bloka (sadrži coric-about-hero)."""
    for m in re.finditer(r"<section\b.*?</section>", html, re.IGNORECASE | re.DOTALL):
        if "coric-about-hero" in m.group(0):
            return m.group(0)
    return ""


def _story_section(html: str) -> str:
    """Izvuci <section ...> ... </section> „Naša priča" bloka (about-story-title)."""
    for m in re.finditer(r"<section\b.*?</section>", html, re.IGNORECASE | re.DOTALL):
        if "about-story-title" in m.group(0):
            return m.group(0)
    return ""


def test_about_hero_includes_overlay_card_green_variant(client):
    """AC4/SM-D6: hero koristi hero_overlay_card sa variant='green' (Repeating Element
    watermark coric-repeating-element--green) + renderuje h1.
    """
    html = _about_html(client)
    assert "coric-hero-overlay-card" in html, (
        "Hero MORA uključiti hero_overlay_card partial (coric-hero-overlay-card)."
    )
    assert "coric-repeating-element--green" in html, (
        "Hero MORA koristiti variant='green' (coric-repeating-element--green watermark; "
        "SM-D6 — repeating-element.css ima samo --green/--jeegee)."
    )
    assert re.search(r"<h1\b[^>]*>", html, re.IGNORECASE), (
        "Hero MORA renderovati <h1> (kroz hero_overlay_card title)."
    )


def test_about_hero_bg_image_is_decorative(client):
    """AC4: hero foto-pozadina je dekorativni <img> (alt='' + aria-hidden='true').

    SM-D5/AC4: koristi <img class='coric-about-hero__bg'>, NE CSS background-image.
    """
    html = _about_html(client)
    hero = _hero_section(html)
    assert hero, "Hero <section> (coric-about-hero) nije pronađen u render-u."
    bg_match = re.search(r"<img\b[^>]*coric-about-hero__bg[^>]*>", hero, re.IGNORECASE)
    assert bg_match, (
        "Hero MORA imati foto-pozadinu kao <img class='coric-about-hero__bg'> "
        "(NE CSS background-image — AC4 token-test razlog)."
    )
    bg_tag = bg_match.group(0)
    assert 'aria-hidden="true"' in bg_tag.lower() or "aria-hidden='true'" in bg_tag.lower(), (
        f"Hero foto-pozadina MORA biti aria-hidden='true' (dekorativna). Tag: {bg_tag!r}"
    )
    # Dekorativna => prazan alt.
    alt_match = re.search(r"alt=[\"']([^\"']*)[\"']", bg_tag, re.IGNORECASE)
    assert alt_match is not None and alt_match.group(1).strip() == "", (
        f"Hero foto-pozadina MORA imati prazan alt='' (dekorativna). Tag: {bg_tag!r}"
    )


def test_about_story_has_decorative_watermark_logo_aria_hidden(client):
    """AC5: „Naša priča" sekcija ima dekorativni watermark logo <img> sa aria-hidden='true'
    i praznim alt (nije accessible nazivan).

    SM-D5/AC5: <img class='coric-about-story__watermark'>, NE CSS background-image.
    """
    html = _about_html(client)
    story = _story_section(html)
    assert story, "Nasa prica <section> (about-story-title) nije pronađen u render-u."
    wm_match = re.search(
        r"<img\b[^>]*coric-about-story__watermark[^>]*>", story, re.IGNORECASE
    )
    assert wm_match, (
        "Nasa prica sekcija MORA imati dekorativni watermark logo kao "
        "<img class='coric-about-story__watermark'> (NE CSS background-image — AC5)."
    )
    wm_tag = wm_match.group(0)
    assert "aria-hidden" in wm_tag.lower() and "true" in wm_tag.lower(), (
        f"Watermark logo MORA biti aria-hidden='true' (dekorativan). Tag: {wm_tag!r}"
    )
    alt_match = re.search(r"alt=[\"']([^\"']*)[\"']", wm_tag, re.IGNORECASE)
    assert alt_match is not None and alt_match.group(1).strip() == "", (
        f"Watermark logo MORA imati prazan alt='' (čisto dekorativan). Tag: {wm_tag!r}"
    )


def test_about_story_section_has_text_paragraphs(client):
    """AC5: „Naša priča" sekcija ima >=2 <p> paragrafa (duži tekst o kompaniji)."""
    html = _about_html(client)
    story = _story_section(html)
    assert story, "Nasa prica <section> nije pronađen u render-u."
    paragraphs = re.findall(r"<p\b[^>]*>.*?</p>", story, re.IGNORECASE | re.DOTALL)
    assert len(paragraphs) >= 2, (
        f"Nasa prica sekcija MORA imati >=2 <p> paragrafa (2-3 translatable copy), "
        f"pronađeno {len(paragraphs)}."
    )
