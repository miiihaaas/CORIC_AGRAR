"""Story 3.1 — AC5: Traktori sekcija (brand kartice: logo + slika + CTA -> brands:detail;
coming-soon pill; 3 klikabilne zone; empty state; graceful degrade bez main_image).

RED phase (TEA). Regex parsiranje.

AC5 — 6+ testova:
- test_traktori_renders_brand_card_per_brand
- test_traktori_brand_logo_links_to_brand_detail
- test_traktori_brand_image_links_to_brand_detail
- test_traktori_cta_links_to_brand_detail
- test_traktori_coming_soon_brand_has_pill_badge_and_still_links
- test_traktori_empty_state_when_no_brands
- test_traktori_published_product_without_main_image_degrades_gracefully (ITEM-5 edge)

Pokrenuti:
    docker compose -f compose/local.yml exec django python -m pytest \\
        apps/pages/tests/test_home_traktori_section.py -v
"""

from __future__ import annotations

import re

import pytest
from django.urls import reverse
from django.utils.translation import activate

from .conftest import assert_home_template, make_traktori_brand

pytestmark = pytest.mark.django_db


def _home_html(client) -> str:
    activate("sr")
    response = client.get("/sr/")
    assert response.status_code == 200, "Home mora vratiti 200 (RED: HomeView ne postoji)."
    assert_home_template(response)
    return response.content.decode("utf-8")


def _links_to(html: str, href: str) -> bool:
    """True ako postoji bar jedan <a ... href="href" ...> u HTML-u."""
    pattern = re.compile(rf'<a\b[^>]*href="{re.escape(href)}"', re.IGNORECASE)
    return bool(pattern.search(html))


def test_traktori_renders_brand_card_per_brand(client):
    """AC5: po jedna brand kartica (coric-brand-card) za svaki Traktori brend."""
    activate("sr")
    make_traktori_brand(name="Brend Alfa")
    make_traktori_brand(name="Brend Beta")
    html = _home_html(client)

    cards = re.findall(r'class="[^"]*coric-brand-card', html)
    assert len(cards) >= 2, (
        f"Traktori sekcija MORA renderovati 1 coric-brand-card po brendu (>=2), "
        f"pronađeno {len(cards)}."
    )
    assert "Brend Alfa" in html and "Brend Beta" in html, (
        "Oba brand naziva MORAJU biti renderovana (h3 po kartici)."
    )


def test_traktori_brand_logo_links_to_brand_detail(client):
    """AC5: brand logo je klikabilna zona -> brands:detail (slug)."""
    activate("sr")
    from .conftest import png_upload
    from apps.brands.tests.factories import BrandFactory
    from apps.products.tests.factories import ProductFactory

    brand = BrandFactory.create(name="Logo Brend")
    brand.logo = png_upload(f"{brand.slug}-logo.png")
    brand.save()
    ProductFactory.create(brand=brand, is_published=True, main_image=png_upload("m.png"))

    html = _home_html(client)
    detail_url = reverse("brands:detail", kwargs={"slug": brand.slug})
    assert _links_to(html, detail_url), (
        f"Brand logo MORA biti klikabilan ka brands:detail ({detail_url}). "
        "AC5: 'klik na logo vodi na brand stranu'."
    )


def test_traktori_brand_image_links_to_brand_detail(client):
    """AC5: reprezentativna slika je ZASEBNA klikabilna zona -> brands:detail."""
    activate("sr")
    brand, _ = make_traktori_brand(name="Slika Brend", with_image=True)
    html = _home_html(client)
    detail_url = reverse("brands:detail", kwargs={"slug": brand.slug})
    # Slika-zona: očekujemo bar 2 <a href=detail> (logo/slika/CTA su odvojene zone) —
    # AC5 zahteva da je SLIKA zasebna klikabilna zona.
    anchors = re.findall(
        rf'<a\b[^>]*href="{re.escape(detail_url)}"', html, re.IGNORECASE
    )
    assert len(anchors) >= 2, (
        f"AC5: slika MORA biti ZASEBNA klikabilna zona ka brands:detail ({detail_url}) "
        f"(pored CTA). Pronađeno {len(anchors)} <a> ka detail URL-u (treba >= 2)."
    )


def test_traktori_cta_links_to_brand_detail(client):
    """AC5: 'OPŠIRNIJE' CTA -> brands:detail (3. klikabilna zona)."""
    activate("sr")
    brand, _ = make_traktori_brand(name="CTA Brend")
    html = _home_html(client)
    detail_url = reverse("brands:detail", kwargs={"slug": brand.slug})
    assert _links_to(html, detail_url), (
        f"'OPŠIRNIJE' CTA MORA linkovati na brands:detail ({detail_url})."
    )
    assert "OPŠIRNIJE" in html or "Opširnije" in html, (
        "CTA tekst 'OPŠIRNIJE' MORA biti renderovan (pune dijakritike)."
    )


def test_traktori_coming_soon_brand_has_pill_badge_and_still_links(client):
    """AC5: is_coming_soon brend -> 'Uskoro' pill (coric-pill-badge--coming-soon,
    role='status') i I DALJE linkuje na brands:detail (NE mrtva strana).
    """
    activate("sr")
    brand, _ = make_traktori_brand(name="Uskoro Brend", is_coming_soon=True)
    html = _home_html(client)

    assert "coric-pill-badge--coming-soon" in html, (
        "Coming-soon brend MORA imati 'coric-pill-badge--coming-soon' (REUSE Story 2-6)."
    )
    badge_re = re.compile(
        r'<span[^>]*coric-pill-badge--coming-soon[^>]*role="status"', re.IGNORECASE
    )
    badge_re2 = re.compile(
        r'<span[^>]*role="status"[^>]*coric-pill-badge--coming-soon', re.IGNORECASE
    )
    assert badge_re.search(html) or badge_re2.search(html), (
        "Pill badge MORA imati role='status' (a11y live region)."
    )
    assert "Uskoro" in html, "Pill tekst 'Uskoro' MORA biti renderovan."

    detail_url = reverse("brands:detail", kwargs={"slug": brand.slug})
    assert _links_to(html, detail_url), (
        f"Coming-soon brend kartica MORA I DALJE linkovati na brands:detail ({detail_url}) "
        "(NE 404; mirror Story 2-6)."
    )


def test_traktori_empty_state_when_no_brands(client):
    """AC5: 0 Traktori brendova -> {% empty %} clause (NE crash, NE prazna sekcija)."""
    activate("sr")
    # NE seed-ujemo nijedan Traktori brend.
    html = _home_html(client)
    assert "coric-brand-card" not in html, (
        "Bez Traktori brendova NE sme biti coric-brand-card."
    )
    assert "Brendovi će uskoro biti dostupni" in html, (
        "Empty-state poruka 'Brendovi će uskoro biti dostupni.' MORA biti renderovana "
        "({% empty %} clause)."
    )


def test_traktori_published_product_without_main_image_degrades_gracefully(client):
    """AC5/ITEM-5 edge: objavljen condition=NEW proizvod BEZ main_image NE sme da
    pukne render (responsive_picture guard). Brend i dalje renderuje karticu + CTA.
    """
    activate("sr")
    brand, _ = make_traktori_brand(name="Bez Slike Brend", with_image=False)

    response = client.get("/sr/")
    assert response.status_code == 200, (
        "Objavljen proizvod BEZ main_image NE SME da pukne render "
        "(ITEM-5 guard u _home_traktori.html)."
    )
    html = response.content.decode("utf-8")
    assert "Bez Slike Brend" in html, (
        "Brend bez reprezentativne slike MORA i dalje renderovati karticu (graceful degrade)."
    )
    detail_url = reverse("brands:detail", kwargs={"slug": brand.slug})
    assert _links_to(html, detail_url), (
        "Brend bez slike MORA i dalje imati klikabilan CTA/logo ka brands:detail."
    )
