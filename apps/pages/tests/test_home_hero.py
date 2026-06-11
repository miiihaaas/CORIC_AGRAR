"""Story 3.1 — AC4: Hero sekcija (slogan h1 + lead + CTA preko dekorativne foto-pozadine).

RED phase (TEA). Regex parsiranje (projekat nema BeautifulSoup).

AC4 revidiran 2026-06-11 (design alignment): home hero prikazuje slogan + lead + CTA
DIREKTNO preko full-bleed slike, usklađeno sa usvojenim dizajnom (docs/Dizajn/_HTML/
index.html) — BEZ zelene overlay kartice i bez Repeating Element watermark-a.

AC4 — 3 testa:
- test_hero_renders_slogan_as_h1
- test_hero_text_directly_over_image_no_overlay_card
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
    """AC4/SM-D10: slogan 'Prijatelj koji razume zemlju!' renderovan kao h1 (FIKSAN copy).

    Dizajn naglašava 'razume zemlju!' kroz <strong> (index.html) — skidamo inline tagove
    pre provere da bismo testirali tekst slogana, ne markup.
    """
    html = _home_html(client)
    h1_match = re.search(r"<h1\b[^>]*>(.*?)</h1>", html, re.IGNORECASE | re.DOTALL)
    assert h1_match, "Hero MORA renderovati <h1>."
    h1_text = re.sub(r"<[^>]+>", "", h1_match.group(1))
    assert "Prijatelj koji razume zemlju" in h1_text, (
        f"h1 MORA sadržati slogan 'Prijatelj koji razume zemlju!', dobio: {h1_text!r}"
    )


def test_hero_text_directly_over_image_no_overlay_card(client):
    """AC4 (revidiran 2026-06-11 — design alignment): home hero prikazuje slogan + lead +
    CTA DIREKTNO preko full-bleed slike, BEZ zelene overlay kartice i bez Repeating Element
    watermark-a (usklađeno sa usvojenim dizajnom docs/Dizajn/_HTML/index.html).
    """
    html = _home_html(client)
    assert "coric-hero-overlay-card" not in html, (
        "Home hero NE sme više koristiti zelenu overlay karticu (design alignment — "
        "tekst ide direktno preko slike)."
    )
    assert "coric-home-hero__lead" in html, "Hero MORA imati lead pasus ispod slogana."
    assert "coric-home-hero__cta" in html, (
        "Hero MORA imati 'Saznaj više' CTA dugme (coric-home-hero__cta)."
    )


def test_hero_background_is_decorative(client):
    """AC4/AC10: hero foto-pozadina je dekorativna (aria-hidden ili alt='' ako <img>)."""
    html = _home_html(client)
    # Dekorativna hero foto-pozadina (<img>) mora biti aria-hidden (a11y kontrakt).
    assert 'aria-hidden="true"' in html, (
        'Dekorativna hero foto-pozadina MORA imati aria-hidden="true" (a11y — AC4/AC10).'
    )
