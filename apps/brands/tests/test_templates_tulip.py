"""Story 2.12 — Tulip template + partials tests (RED phase TDD).

Pokriva AC5 (hero → 2-model showcase coric-product-card → uporedna dimenziona tabela
scope/caption → conditional testimonials → conditional catalog CTA) + AC8 (single h1 /
single main / em-dash missing value / divergent keys / empty stanja / NEMA ćirilice).

Pokrenuti sa:
    docker compose -f compose/local.yml run --rm django uv run pytest \\
        apps/brands/tests/test_templates_tulip.py -v

Refs:
- 2-12-hzm-radne-masine-tulip-mix-prikolice-strane.md (AC5, AC8, Subtask 8.5)
- 2-12-interface-contract.md (§ 3 Templates)
"""

from __future__ import annotations

import re

import pytest
from django.utils.translation import activate

from apps.products.models import Product, ProductSpecification, ProductTestimonial

pytestmark = pytest.mark.django_db

_TULIP_URL = "/sr/mehanizacija/mix-prikolice/"


def test_tulip_renders_exactly_one_h1(client):
    """AC5 + AC8: TAČNO 1 <h1> (brand.name 'Tulip' iz hero_overlay_card)."""
    activate("sr")
    response = client.get(_TULIP_URL)
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    h1_matches = re.findall(r"<h1\b[^>]*>(.*?)</h1>", html, re.IGNORECASE | re.DOTALL)
    assert len(h1_matches) == 1, (
        f"tulip_mix_prikolice.html MORA imati TAČNO 1 <h1>, pronađeno {len(h1_matches)}: "
        f"{h1_matches!r}."
    )
    assert "Tulip" in h1_matches[0], (
        f"<h1> MORA sadržati 'Tulip', dobio {h1_matches[0]!r}."
    )


def test_tulip_renders_exactly_one_main(client):
    """AC5 + AC8: TAČNO 1 <main> (base.html provider; outer wrapper je <section>)."""
    activate("sr")
    response = client.get(_TULIP_URL)
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    main_matches = re.findall(r"<main\b[^>]*>", html, re.IGNORECASE)
    assert len(main_matches) == 1, (
        f"tulip_mix_prikolice.html MORA imati TAČNO 1 <main>, pronađeno {len(main_matches)}."
    )


def test_tulip_outer_section_has_aria_label_not_aria_labelledby(client):
    """AC5 + SM-D8: outer <section coric-tulip-mix> ima aria-label (NE aria-labelledby)."""
    activate("sr")
    response = client.get(_TULIP_URL)
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    outer_matches = re.findall(
        r"<section[^>]*\bcoric-tulip-mix\b[^>]*>", html, re.IGNORECASE
    )
    outer_tag = next((t for t in outer_matches if "coric-brand-detail" in t), None)
    assert outer_tag is not None, (
        f"Outer <section class='coric-brand-detail coric-tulip-mix'> MORA postojati. "
        f"Pronađeno: {outer_matches!r}."
    )
    assert "aria-label=" in outer_tag and "aria-labelledby=" not in outer_tag, (
        f"Outer <section> MORA imati aria-label (NE aria-labelledby). Tag: {outer_tag!r}."
    )


def test_tulip_renders_2_model_cards(client):
    """AC5: 2-model showcase renderuje 2 coric-product-card sa per-model data-testid."""
    activate("sr")
    response = client.get(_TULIP_URL)
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    card_matches = re.findall(
        r"<article[^>]*\bcoric-product-card\b[^>]*>", html, re.IGNORECASE
    )
    assert len(card_matches) == 2, (
        f"Tulip MORA renderovati TAČNO 2 .coric-product-card kartice (REUSE Story 2-8 BEM), "
        f"pronađeno {len(card_matches)}."
    )
    for slug in ("tulip-mix-6m3", "tulip-mix-8m3"):
        assert f'data-testid="tulip-model-card-{slug}"' in html, (
            f"Model kartica za slug={slug!r} MORA imati "
            f"'data-testid=\"tulip-model-card-{slug}\"'."
        )


def test_tulip_model_card_cta_links_to_product_detail(client):
    """AC5: 'OPŠIRNIJE' CTA href = product.get_absolute_url() → /sr/proizvod/<slug>/."""
    activate("sr")
    response = client.get(_TULIP_URL)
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    for product in Product.objects.filter(brand__slug="tulip"):
        expected_href = product.get_absolute_url()
        assert expected_href in html, (
            f"Model kartica CTA href MORA biti product.get_absolute_url() "
            f"({expected_href!r}); render ne sadrži taj href."
        )
    assert "OPŠIRNIJE" in html, "CTA dugme MORA imati tekst 'OPŠIRNIJE'."


def test_tulip_comparison_table_renders_with_scope_attributes(client):
    """AC5 + WCAG 1.3.1: uporedna tabela ima <th scope='col'> + <th scope='row'> + <caption>."""
    activate("sr")
    response = client.get(_TULIP_URL)
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    assert 'data-testid="tulip-comparison-table"' in html, (
        "Uporedna tabela MORA imati data-testid='tulip-comparison-table'."
    )
    assert 'class="coric-comparison-table"' in html, (
        "Tabela MORA imati klasu 'coric-comparison-table'."
    )
    # caption (visually-hidden za screen reader)
    assert re.search(r"<caption[^>]*>", html, re.IGNORECASE), (
        "Tabela MORA imati <caption> (WCAG screen reader kontekst)."
    )
    # th scope=col (model headers) + th scope=row (key cells)
    assert 'scope="col"' in html, (
        "Tabela MORA imati <th scope='col'> za model header ćelije (WCAG 1.3.1)."
    )
    assert 'scope="row"' in html, (
        "Tabela MORA imati <th scope='row'> za ključ ćelije (WCAG 1.3.1)."
    )
    # Oba model naziva u header-u
    for name in ("Tulip MIX 6 m³", "Tulip MIX 8 m³"):
        assert name in html, f"Tabela header MORA sadržati model naziv {name!r}."


def test_tulip_comparison_table_missing_value_shows_emdash(client):
    """AC5: prazna vrednost (None) → '—' kroz |default filter.

    Dodaj spec 'Boja' SAMO na 6 m³ model; 8 m³ kolona za Boja MORA prikazati '—'.
    """
    activate("sr")
    p6 = Product.objects.get(slug="tulip-mix-6m3")
    ProductSpecification.objects.create(
        product=p6, section="ostalo", key="Boja", value="Zelena", order=20
    )

    response = client.get(_TULIP_URL)
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    assert "—" in html, (
        "Tabela MORA renderovati '—' (em-dash) za missing spec vrednost (|default:'—')."
    )
    assert "Boja" in html and "Zelena" in html


def test_tulip_comparison_table_divergent_spec_keys_fills_emdash(client):
    """AC5 + OQ-2: neporavnati spec key-evi NE lome tabelu; oba smera (A-only i B-only).

    Model A (6 m³) dobija key 'Težina' (B nema); Model B (8 m³) dobija key 'Garancija'
    (A nema). Tabela MORA imati oba reda sa '—' u praznoj koloni.
    """
    activate("sr")
    p6 = Product.objects.get(slug="tulip-mix-6m3")
    p8 = Product.objects.get(slug="tulip-mix-8m3")
    ProductSpecification.objects.create(
        product=p6, section="ostalo", key="Težina", value="3200 kg", order=30
    )
    ProductSpecification.objects.create(
        product=p8, section="ostalo", key="Garancija", value="5 godina", order=30
    )

    response = client.get(_TULIP_URL)
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    spec_rows = response.context["spec_rows"]
    keys = [r["key"] for r in spec_rows]
    assert "Težina" in keys and "Garancija" in keys, (
        f"spec_rows MORA sadržati i 'Težina' (samo A) i 'Garancija' (samo B), dobio {keys!r}."
    )

    tezina = next(r for r in spec_rows if r["key"] == "Težina")
    garancija = next(r for r in spec_rows if r["key"] == "Garancija")
    assert tezina["values"] == ["3200 kg", None], (
        f"'Težina' (samo na 6 m³) MORA imati values ['3200 kg', None], dobio "
        f"{tezina['values']!r}."
    )
    assert garancija["values"] == [None, "5 godina"], (
        f"'Garancija' (samo na 8 m³) MORA imati values [None, '5 godina'], dobio "
        f"{garancija['values']!r}."
    )
    # Em-dash renderovan za obe prazne ćelije
    assert "—" in html


def test_tulip_comparison_table_hidden_when_no_spec_rows(client):
    """AC5: 0 spec_rows → comparison sekcija/tabela SE NE renderuje (`{% if spec_rows %}`)."""
    activate("sr")
    ProductSpecification.objects.filter(product__brand__slug="tulip").delete()

    response = client.get(_TULIP_URL)
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    assert 'data-testid="tulip-comparison-table"' not in html, (
        "Bez spec_rows, uporedna tabela NE SME biti u DOM-u (`{% if spec_rows %}` guard)."
    )
    assert 'id="tulip-comparison"' not in html, (
        "Bez spec_rows, comparison sekcija NE SME biti u DOM-u."
    )


def test_tulip_model_showcase_empty_state_when_no_products(client):
    """AC5: 0 products → model-showcase empty state; comparison/testimonials se ne renderuju."""
    activate("sr")
    Product.objects.filter(brand__slug="tulip").update(is_published=False)

    response = client.get(_TULIP_URL)
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    assert "Modeli prikolica su u pripremi." in html, (
        "Bez published products, model-showcase MORA renderovati empty state 'Modeli "
        "prikolica su u pripremi.'."
    )
    card_matches = re.findall(
        r"<article[^>]*\bcoric-product-card\b[^>]*>", html, re.IGNORECASE
    )
    assert len(card_matches) == 0, (
        f"Bez products, NE SMEJU se renderovati .coric-product-card kartice, pronađeno "
        f"{len(card_matches)}."
    )
    assert 'data-testid="tulip-comparison-table"' not in html, (
        "Bez products, comparison tabela SE NE renderuje."
    )


def test_tulip_testimonials_section_hidden_when_empty(client):
    """AC5: 0 testimonijala (seed) → 'Zadovoljni kupci' sekcija SE NE renderuje."""
    activate("sr")
    response = client.get(_TULIP_URL)
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    assert 'id="tulip-testimonials"' not in html, (
        "Bez testimonijala, testimonials sekcija NE SME biti u DOM-u (`{% if testimonials %}`)."
    )
    assert 'data-testid="testimonials-slider"' not in html, (
        "Bez testimonijala, testimonials slider NE SME biti renderovan."
    )


def test_tulip_testimonials_slider_id_matches_aria_labelledby(client):
    """AC5 + SM-D10: testimonials sekcija aria-labelledby == slider_id 'tulip-testimonials-title'.

    Seed-uj 1 testimonial na 6 m³ model → sekcija se renderuje; verifikuj slider_id
    matchuje aria-labelledby na outer testimonials sekciji.
    """
    activate("sr")
    p6 = Product.objects.get(slug="tulip-mix-6m3")
    ProductTestimonial.objects.create(
        product=p6,
        quote="Odlična prikolica, robusna i pouzdana.",
        author_name="Stojan Đurić",
        location="Bačka Topola",
        order=0,
    )

    response = client.get(_TULIP_URL)
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    assert 'id="tulip-testimonials"' in html, (
        "Sa testimonijalom, testimonials sekcija MORA biti renderovana."
    )
    # _testimonials_slider.html renderuje <h2 id="{{ slider_id }}"> = tulip-testimonials-title
    assert 'id="tulip-testimonials-title"' in html, (
        "Slider MORA renderovati h2 id='tulip-testimonials-title' (slider_id kwarg SM-D10)."
    )
    assert 'aria-labelledby="tulip-testimonials-title"' in html, (
        "Outer testimonials sekcija MORA imati aria-labelledby='tulip-testimonials-title' "
        "(matchuje slider_id — SM-D10)."
    )


def test_tulip_no_cirillic_in_rendered_html(client):
    """AC8: NEMA ćirilice u render-u."""
    activate("sr")
    response = client.get(_TULIP_URL)
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    cirillic = re.findall(r"[А-Яа-яЁё]", html)
    assert not cirillic, (
        f"Render NE SME sadržati ćirilične karaktere. Pronađeno: {set(cirillic)!r}."
    )
