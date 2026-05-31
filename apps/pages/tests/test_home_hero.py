"""Story 3.1 — AC4: Hero sekcija (slogan h1 + hero_overlay_card variant=green +
Repeating Element watermark + dekorativna foto-pozadina).

RED phase (TEA). Regex parsiranje (projekat nema BeautifulSoup).

AC4 — 3 testa:
- test_hero_renders_slogan_as_h1
- test_hero_uses_overlay_card_and_repeating_element_green
- test_hero_background_is_decorative

Pokrenuti:
    docker compose -f compose/local.yml exec django python -m pytest \\
        apps/pages/tests/test_home_hero.py -v
"""

from __future__ import annotations

import re

import pytest
from django.utils.translation import activate

from .conftest import assert_home_template, make_traktori_brand

pytestmark = pytest.mark.django_db


def _home_html(client) -> str:
    activate("sr")
    make_traktori_brand(name="Hero Traktor Brend")
    response = client.get("/sr/")
    assert response.status_code == 200, "Home mora vratiti 200 (RED: HomeView ne postoji)."
    assert_home_template(response)
    return response.content.decode("utf-8")


def test_hero_renders_slogan_as_h1(client):
    """AC4/SM-D10: slogan 'Prijatelj koji razume zemlju!' renderovan kao h1 (FIKSAN copy)."""
    html = _home_html(client)
    h1_match = re.search(r"<h1\b[^>]*>(.*?)</h1>", html, re.IGNORECASE | re.DOTALL)
    assert h1_match, "Hero MORA renderovati <h1> (kroz hero_overlay_card)."
    h1_text = h1_match.group(1)
    assert "Prijatelj koji razume zemlju" in h1_text, (
        f"h1 MORA sadržati slogan 'Prijatelj koji razume zemlju!', dobio: {h1_text!r}"
    )


def test_hero_uses_overlay_card_and_repeating_element_green(client):
    """AC4/SM-D9: hero koristi hero_overlay_card (green variant) + Repeating Element
    watermark variant=green (coric-repeating-element--green; NE 'home'/druga vrednost).
    """
    html = _home_html(client)
    assert "coric-repeating-element--green" in html, (
        "Hero MORA uključiti Repeating Element variant='green' "
        "(coric-repeating-element--green; SM-D9 — repeating-element.css ima samo --green/--jeegee)."
    )
    # hero_overlay_card green varijanta (BEM modifier mirror Story 1-7/2-10).
    assert re.search(r"coric-hero-overlay-card[^\"']*--green", html) or (
        "coric-hero-overlay-card" in html and "--green" in html
    ), (
        "Hero MORA koristiti hero_overlay_card partial sa variant='green' "
        "(coric-hero-overlay-card--green BEM modifier)."
    )


def test_hero_background_is_decorative(client):
    """AC4/AC10: hero foto-pozadina je dekorativna (aria-hidden ili alt='' ako <img>)."""
    html = _home_html(client)
    # Repeating Element SVG mora biti aria-hidden (Story 1-7 kontrakt).
    assert 'aria-hidden="true"' in html, (
        "Dekorativni elementi (Repeating Element watermark / hero bg) MORAJU imati "
        "aria-hidden=\"true\" (a11y — AC4/AC10)."
    )
