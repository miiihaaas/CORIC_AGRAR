"""Story 2.12 — HZM template + partials tests (RED phase TDD).

Pokriva AC4 (hero variant=green + 4-card subcategory showcase + CTA href =
subcategory.get_absolute_url) + AC8 (single h1 / single main / aria-label / NEMA ćirilice).

Pokrenuti sa:
    docker compose -f compose/local.yml run --rm django uv run pytest \\
        apps/brands/tests/test_templates_hzm.py -v

Refs:
- 2-12-hzm-radne-masine-tulip-mix-prikolice-strane.md (AC4, AC8, Subtask 8.4)
- 2-12-interface-contract.md (§ 3 Templates)
"""

from __future__ import annotations

import re

import pytest
from django.utils.translation import activate

from apps.brands.models import Subcategory

pytestmark = pytest.mark.django_db

_HZM_URL = "/sr/mehanizacija/radne-masine/"


def test_hzm_renders_exactly_one_h1(client):
    """AC4 + AC8: TAČNO 1 <h1> (brand.name 'HZM' iz hero_overlay_card partial-a)."""
    activate("sr")
    response = client.get(_HZM_URL)
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    h1_matches = re.findall(r"<h1\b[^>]*>(.*?)</h1>", html, re.IGNORECASE | re.DOTALL)
    assert len(h1_matches) == 1, (
        f"hzm_radne_masine.html MORA imati TAČNO 1 <h1>, pronađeno {len(h1_matches)}: "
        f"{h1_matches!r}. h1 dolazi iz hero_overlay_card partial-a."
    )
    assert "HZM" in h1_matches[0], (
        f"<h1> MORA sadržati 'HZM' (brand.name iz 0004 seed-a), dobio {h1_matches[0]!r}."
    )


def test_hzm_renders_exactly_one_main(client):
    """AC4 + AC8: TAČNO 1 <main> (base.html provider; outer wrapper je <section>)."""
    activate("sr")
    response = client.get(_HZM_URL)
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    main_matches = re.findall(r"<main\b[^>]*>", html, re.IGNORECASE)
    assert len(main_matches) == 1, (
        f"hzm_radne_masine.html MORA imati TAČNO 1 <main> (HTML5 spec — nested <main> "
        f"invalid). Outer wrapper je <section class='coric-brand-detail coric-hzm-radne-"
        f"masine'>. Pronađeno: {len(main_matches)}."
    )


def test_hzm_renders_4_subcategory_cards(client):
    """AC4: 4-card grid za 4 seeded subcategory; per-card data-testid."""
    activate("sr")
    response = client.get(_HZM_URL)
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    card_matches = re.findall(
        r"<article[^>]*\bcoric-category-card\b[^>]*>", html, re.IGNORECASE
    )
    assert len(card_matches) == 4, (
        f"HZM MORA renderovati TAČNO 4 .coric-category-card kartice (REUSE Story 2-10 BEM), "
        f"pronađeno {len(card_matches)}."
    )

    for slug in (
        "mini-utovarivaci",
        "utovarivaci-bez-teleskopa",
        "teleskopski-utovarivaci",
        "telehendleri",
    ):
        assert f'data-testid="hzm-subcategory-card-{slug}"' in html, (
            f"Kartica za subcategory slug={slug!r} MORA imati "
            f"'data-testid=\"hzm-subcategory-card-{slug}\"'."
        )


def test_hzm_card_cta_href_uses_subcategory_get_absolute_url(client):
    """AC4 + SM-D4: CTA href = subcategory.get_absolute_url() = /sr/mehanizacija/prikljucna/radne-masine/<sub-slug>/.

    KRITIČNO: HZM kartice su Subcategory pa CTA NIJE {% url subcategory_listing_category %}
    već sub.get_absolute_url() koji vodi na Story 2-11 SubcategoryListView kroz generički
    'prikljucna' prefiks (URL path prefiks je generic mehanizacija drill-down).
    """
    activate("sr")
    response = client.get(_HZM_URL)
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    # get_absolute_url() na L1 subcategory (depth=1) → subcategory_listing_l1
    for sub in Subcategory.objects.filter(category__slug="radne-masine", parent=None):
        expected_href = f"/sr/mehanizacija/prikljucna/radne-masine/{sub.slug}/"
        assert expected_href in html, (
            f"CTA href '{expected_href}' MORA biti u render-u (SM-D4 — sub.get_absolute_url()). "
            f"Render NE sadrži taj href; verifikuj template koristi "
            f"`{{{{ sub.get_absolute_url }}}}` NE `{{% url ... %}}`."
        )


def test_hzm_hero_renders_green_variant_repeating_element(client):
    """AC4 + SM-D9: hero renderuje coric-repeating-element--green (NE --hzm).

    CSS NEMA --hzm varijantu (samo --green + --jeegee). variant='hzm' bi dao
    unstyled watermark (mirror Story 2-6 dormant bug).
    """
    activate("sr")
    response = client.get(_HZM_URL)
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    assert "coric-repeating-element--green" in html, (
        "Hero MORA renderovati 'coric-repeating-element--green' (SM-D9). _hzm_hero.html "
        "MORA prosediti variant='green' u hero_overlay_card.html."
    )
    assert "coric-repeating-element--hzm" not in html, (
        "Hero NE SME renderovati 'coric-repeating-element--hzm' (SM-D9 — varijanta ne "
        "postoji u CSS-u → unstyled watermark)."
    )


def test_hzm_outer_section_has_aria_label_not_aria_labelledby(client):
    """AC4 + AC8 + SM-D8: outer <section> ima aria-label (NE aria-labelledby).

    h1 u hero_overlay_card.html NEMA id pa aria-labelledby bi bila dangling reference.
    """
    activate("sr")
    response = client.get(_HZM_URL)
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    outer_matches = re.findall(
        r"<section[^>]*\bcoric-hzm-radne-masine\b[^>]*>", html, re.IGNORECASE
    )
    outer_tag = next((t for t in outer_matches if "coric-brand-detail" in t), None)
    assert outer_tag is not None, (
        f"Outer <section class='coric-brand-detail coric-hzm-radne-masine'> MORA postojati. "
        f"Pronađeno: {outer_matches!r}."
    )
    assert "aria-label=" in outer_tag, (
        f"Outer <section> MORA imati 'aria-label' (SM-D8 LOCK). Pronađen tag: {outer_tag!r}."
    )
    assert "aria-labelledby=" not in outer_tag, (
        f"Outer <section> NE SME imati 'aria-labelledby' (SM-D8 — h1 nema id, dangling). "
        f"Pronađen tag: {outer_tag!r}."
    )


def test_hzm_card_cta_aria_label_includes_subcategory_name(client):
    """AC4 + AC8: CTA aria-label sadrži 'Pogledaj kategoriju: <sub naziv>' (WCAG 2.4.4)."""
    activate("sr")
    response = client.get(_HZM_URL)
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    for name in (
        "Mini utovarivači",
        "Utovarivači bez teleskopa",
        "Teleskopski utovarivači",
        "Telehendleri",
    ):
        assert f'aria-label="Pogledaj kategoriju: {name}"' in html, (
            f"CTA dugme MORA imati 'aria-label=\"Pogledaj kategoriju: {name}\"' "
            f"(blocktranslate sa sub.name interpolacijom; pune dijakritike)."
        )


def test_hzm_empty_state_renders_when_zero_subcategories(client):
    """AC4: {% empty %} clause → 'Kategorije radnih mašina su u pripremi.'."""
    activate("sr")
    Subcategory.objects.filter(category__slug="radne-masine").delete()

    response = client.get(_HZM_URL)
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    assert "Kategorije radnih mašina su u pripremi." in html, (
        "Empty state MORA renderovati 'Kategorije radnih mašina su u pripremi.' kroz "
        "`{% empty %}` clause u _hzm_subcategory_showcase.html."
    )
    card_matches = re.findall(
        r"<article[^>]*\bcoric-category-card\b[^>]*>", html, re.IGNORECASE
    )
    assert len(card_matches) == 0, (
        f"Bez subcategory, NE SMEJU se renderovati .coric-category-card kartice, "
        f"pronađeno {len(card_matches)}."
    )


def test_hzm_no_cirillic_in_rendered_html(client):
    """AC8: NEMA ćirilice u render-u (project-context.md anti-pattern)."""
    activate("sr")
    response = client.get(_HZM_URL)
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    cirillic = re.findall(r"[А-Яа-яЁё]", html)
    assert not cirillic, (
        f"Render NE SME sadržati ćirilične karaktere. Pronađeno: {set(cirillic)!r}. "
        f"Sve user-facing string-ove u latinici sa punim dijakritikama (č/ć/ž/š/đ)."
    )
