"""Story 3.1 — AC6 + AC7 + AC8: Priključna/Polovna baneri, Radne mašine (HZM), Priče
sa polja placeholder.

RED phase (TEA). Regex parsiranje.

AC6+AC7+AC8 — 7 testova:
- test_prikljucna_banner_cta_links_to_jeegee_prikljucna           (AC6)
- test_polovna_banner_cta_links_to_used_machinery_list            (AC6)
- test_radne_masine_renders_category_card_per_subcategory         (AC7)
- test_radne_masine_card_includes_repeating_element_green         (AC7/SM-D9)
- test_radne_masine_all_cards_use_single_shared_hzm_cta           (AC7/ITEM-3 LOCK)
- test_price_sa_polja_renders_2_lorem_ipsum_placeholder_cards     (AC8/SM-D7)
- test_price_sa_polja_placeholder_has_no_dead_404_links           (AC8/SM-D14)

Pokrenuti:
    docker compose -f compose/local.yml exec django python -m pytest \\
        apps/pages/tests/test_home_sections.py -v
"""

from __future__ import annotations

import re

import pytest
from django.urls import reverse
from django.utils.translation import activate

from .conftest import assert_home_template, get_hzm_category, make_traktori_brand

pytestmark = pytest.mark.django_db


def _home_html(client) -> str:
    activate("sr")
    make_traktori_brand(name="Sekcije Traktor Brend")
    response = client.get("/sr/")
    assert response.status_code == 200, "Home mora vratiti 200 (RED: HomeView ne postoji)."
    assert_home_template(response)
    return response.content.decode("utf-8")


def _links_to(html: str, href: str) -> bool:
    return bool(re.search(rf'<a\b[^>]*href="{re.escape(href)}"', html, re.IGNORECASE))


# ---------------------------------------------------------------------------
# AC6 — baneri
# ---------------------------------------------------------------------------


def test_prikljucna_banner_cta_links_to_jeegee_prikljucna(client):
    """AC6: Priključna baner CTA -> brands:jeegee_prikljucna."""
    html = _home_html(client)
    target = reverse("brands:jeegee_prikljucna")
    assert _links_to(html, target), (
        f"Priključna baner MORA imati CTA ka brands:jeegee_prikljucna ({target})."
    )


def test_polovna_banner_cta_links_to_used_machinery_list(client):
    """AC6: Polovna baner CTA -> products:used_machinery_list."""
    html = _home_html(client)
    target = reverse("products:used_machinery_list")
    assert _links_to(html, target), (
        f"Polovna baner MORA imati CTA ka products:used_machinery_list ({target})."
    )


# ---------------------------------------------------------------------------
# AC7 — Radne mašine (HZM)
# ---------------------------------------------------------------------------


def test_radne_masine_renders_category_card_per_subcategory(client):
    """AC7: po jedna coric-category-card za svaku HZM potkategoriju (seed 0004 = 4)."""
    if get_hzm_category() is None:
        pytest.skip("HZM radne-masine Category nije seed-ovana (migracija 0004).")
    html = _home_html(client)
    cards = re.findall(r'class="[^"]*coric-category-card', html)
    assert len(cards) >= 4, (
        f"Radne mašine sekcija MORA renderovati 1 coric-category-card po HZM potkategoriji "
        f"(>=4 iz seed-a), pronađeno {len(cards)}."
    )


def test_radne_masine_card_includes_repeating_element_green(client):
    """AC7/SM-D9: Repeating Element po kategoriji, variant='green'
    (coric-repeating-element--green) + aria-hidden SVG.
    """
    if get_hzm_category() is None:
        pytest.skip("HZM radne-masine Category nije seed-ovana (migracija 0004).")
    html = _home_html(client)
    re_green = re.findall(r"coric-repeating-element--green", html)
    # Hero koristi 1 + svaka HZM kartica 1 -> očekujemo > 1 (po kategoriji).
    assert len(re_green) >= 2, (
        f"Radne mašine MORAJU uključiti Repeating Element variant='green' PO KARTICI "
        f"(coric-repeating-element--green). Pronađeno {len(re_green)} (treba >=2: hero + kartice)."
    )


def test_radne_masine_all_cards_use_single_shared_hzm_cta(client):
    """AC7/ITEM-3 LOCK: SVE HZM kartice koriste JEDAN zajednički CTA ->
    brands:hzm_radne_masine (NE per-subcategory get_absolute_url, koji bi bio NoReverseMatch).
    """
    if get_hzm_category() is None:
        pytest.skip("HZM radne-masine Category nije seed-ovana (migracija 0004).")
    html = _home_html(client)
    hzm_target = reverse("brands:hzm_radne_masine")
    assert _links_to(html, hzm_target), (
        f"Radne mašine sekcija MORA linkovati na brands:hzm_radne_masine ({hzm_target})."
    )

    # ITEM-3 LOCK: NE sme biti per-subcategory category_mehanizacija deep-link
    # (Category.get_absolute_url() reverzuje category_mehanizacija -> NoReverseMatch bug).
    cat = get_hzm_category()
    leak = []
    for sub in cat.subcategories.filter(parent=None):
        # Heuristika: per-subcategory deep-link bi sadržao slug potkategorije u href-u
        # ka mehanizacija ruti (NE ka hzm_radne_masine).
        sub_href_re = re.compile(
            rf'<a\b[^>]*href="[^"]*/{re.escape(sub.slug)}/?"', re.IGNORECASE
        )
        if sub_href_re.search(html):
            leak.append(sub.slug)
    assert not leak, (
        "ITEM-3 LOCK: HZM kartice NE SMEJU koristiti per-subcategory deep-link "
        f"(sub.get_absolute_url). Sve kartice MORAJU deliti CTA ka brands:hzm_radne_masine. "
        f"Detektovani per-subcategory linkovi: {leak!r}"
    )


def test_radne_masine_empty_state_when_no_subcategories(client):
    """ITEM-4 — {% empty %} grana Radne mašine sekcije renderuje empty-state tekst kada
    je hzm_subcategories prazan (mirror Traktori empty-state test).

    HZM kategorija je seed-ovana (migracija 0004) pa goli view render UVEK vraća
    potkategorije; zato renderujemo partial direktno sa praznim hzm_subcategories
    kontekstom (deterministički okida {% empty %} bez diranja seed-a).
    """
    from django.template.loader import render_to_string

    activate("sr")
    html = render_to_string(
        "pages/partials/_home_radne_masine.html",
        {"hzm_subcategories": []},
    )
    assert "coric-category-card" not in html, (
        "Bez HZM potkategorija NE sme biti coric-category-card ({% empty %} grana)."
    )
    assert "Radne mašine su u pripremi." in html, (
        "Empty-state poruka 'Radne mašine su u pripremi.' MORA biti renderovana "
        "({% empty %} clause Radne mašine sekcije)."
    )


# ---------------------------------------------------------------------------
# AC8 — Priče sa polja (forward-compat placeholder)
# ---------------------------------------------------------------------------


def test_price_sa_polja_renders_2_lorem_ipsum_placeholder_cards(client):
    """AC8/SM-D7: latest_posts=[] -> TAČNO 2 statičke Lorem Ipsum placeholder kartice."""
    html = _home_html(client)
    cards = re.findall(r'class="[^"]*coric-home-blog-card', html)
    assert len(cards) == 2, (
        f"Priče sa polja MORA renderovati TAČNO 2 placeholder kartice (coric-home-blog-card) "
        f"kad je latest_posts prazan (SM-D7), pronađeno {len(cards)}."
    )
    assert re.search(r"[Ll]orem [Ii]psum", html), (
        "Placeholder kartice MORAJU imati očigledan Lorem Ipsum sadržaj (SM-D7)."
    )


def test_price_sa_polja_placeholder_has_no_dead_404_links(client):
    """AC8/SM-D14: placeholder CTA (ako postoji) koristi kanonski disabled pattern —
    href='#' + aria-disabled='true' + tabindex='-1' + role='button'. NEMA fokusabilan
    mrtav link, NEMA link ka nepostojećoj blog strani.
    """
    html = _home_html(client)

    # Izoluj 'Priče sa polja' deo (od prve pojave coric-home-blog do kraja te <section>).
    # DEV-FIX (Story 3.1 GREEN): ograniči slice na zatvaranje blog <section> (ranije je
    # išao do kraja dokumenta i hvatao footer social `href="#"` linkove — site-wide
    # footer markup, NE blog placeholder; van scope-a ovog AC8 testa).
    blog_idx = html.find("coric-home-blog")
    if blog_idx != -1:
        end_idx = html.find("</section>", blog_idx)
        blog_section = html[blog_idx:end_idx] if end_idx != -1 else html[blog_idx:]
    else:
        blog_section = html

    # Svi <a> u blog sekciji.
    anchors = re.findall(r"<a\b[^>]*>", blog_section, re.IGNORECASE)
    for a in anchors:
        a_low = a.lower()
        # Ako CTA postoji, mora biti disabled pattern (href="#").
        if 'href="#"' in a_low:
            assert 'aria-disabled="true"' in a_low, (
                f"Placeholder CTA sa href='#' MORA imati aria-disabled='true' (SM-D14): {a!r}"
            )
            assert 'tabindex="-1"' in a_low, (
                f"Placeholder CTA MORA imati tabindex='-1' (van tab-reda, SM-D14): {a!r}"
            )
        # NE sme linkovati na nepostojeću blog rutu (npr. /blog/ ili /price/).
        href_match = re.search(r'href="([^"]*)"', a_low)
        if href_match:
            href = href_match.group(1)
            assert not href.startswith(("/blog", "/price", "/vesti")), (
                f"Placeholder kartica NE SME linkovati na nepostojeću blog stranu "
                f"(404 dead-link): {href!r}"
            )
