"""Story 2.6 — `templates/products/_placeholder.html` tests (RED phase TDD).

Pokriva AC2.6 (C8 fix + I-iter2-4 SEO noindex guard) — minimal product placeholder
template koji se renderuje iz `placeholder_view` FBV dok Story 2.7 ne uvede pravu
ProductDetailView.

Test scope (4 tests):
- test_placeholder_returns_http_200_with_template — GET /sr/proizvod/test/ → 200 + assertTemplateUsed
- test_placeholder_has_noindex_meta_tag — <meta name="robots" content="noindex, nofollow"> u <head>
- test_placeholder_has_single_h1 — TAČNO 1 <h1> sa "Stranica još nije dostupna"
- test_placeholder_uses_semantic_main_landmark — <main role="main"> wrapper

Pokrenuti sa:
    docker compose -f compose/local.yml exec django uv run pytest \\
        apps/products/tests/test_placeholder.py -v

Refs:
- 2-6-brand-listing-strana-sa-grid-extended-layout-om.md (AC2.6, Subtask 10.5)
- 2-6-interface-contract.md (§ 3 placeholder_view + § 4 _placeholder.html spec)
"""

from __future__ import annotations

import re

import pytest
from django.utils.translation import activate

pytestmark = pytest.mark.django_db


def test_placeholder_returns_http_200_with_template(client):
    """AC2.6: GET /sr/proizvod/<slug>/ vraća HTTP 200 + assertTemplateUsed(_placeholder.html).

    Sprečava regression NoReverseMatch kad brand listing grid kartica linkuje na
    {% url 'products:detail' slug=product.slug %} pre Story 2.7. Placeholder mora
    biti accessible za bilo koji slug (FBV ne radi DB lookup).
    """
    activate("sr")
    url = "/sr/proizvod/test-slug/"

    response = client.get(url)

    assert response.status_code == 200, (
        f"GET {url} treba HTTP 200 (placeholder_view), dobio {response.status_code}. "
        "Dev mora kreirati apps/products/urls.py + apps/products/views.py."
    )
    template_names = [t.name for t in response.templates if t.name]
    assert "products/_placeholder.html" in template_names, (
        f"Placeholder MORA renderovati 'products/_placeholder.html'. "
        f"Renderovani template-i: {template_names!r}"
    )


def test_placeholder_has_noindex_meta_tag(client):
    """AC2.6 (I-iter2-4): <meta name="robots" content="noindex, nofollow"> KRITIČAN SEO guard.

    Bez noindex meta tag-a, Googlebot bi indexirao "Stranica još nije dostupna" za
    ~stotine product slug-ova (SEO katastrofa). Story 2.7 zameni placeholder pravim
    ProductDetailView i ukloni noindex guard.
    """
    activate("sr")
    url = "/sr/proizvod/test-slug/"

    response = client.get(url)
    html = response.content.decode("utf-8")

    # Tolerantan pattern — može biti single ili double quotes, atributi u bilo kom redosledu
    noindex_pattern = re.compile(
        r'<meta\s+name=["\']robots["\']\s+content=["\']noindex,\s*nofollow["\']',
        re.IGNORECASE,
    )
    noindex_pattern2 = re.compile(
        r'<meta\s+content=["\']noindex,\s*nofollow["\']\s+name=["\']robots["\']',
        re.IGNORECASE,
    )
    assert noindex_pattern.search(html) or noindex_pattern2.search(html), (
        "Placeholder template MORA imati <meta name='robots' content='noindex, nofollow'> "
        "u {% block extra_head %} sekciji (I-iter2-4 SEO guard). "
        f"HTML <head> sektor (do </head>): {html[:html.find('</head>')+10]!r}"
    )


def test_placeholder_has_single_h1(client):
    """AC2.6: TAČNO 1 <h1> sa tekstom "Stranica još nije dostupna" (i18n marker prisutan)."""
    activate("sr")
    url = "/sr/proizvod/test-slug/"

    response = client.get(url)
    html = response.content.decode("utf-8")

    h1_pattern = re.compile(r"<h1\b[^>]*>(.*?)</h1>", re.IGNORECASE | re.DOTALL)
    h1_matches = h1_pattern.findall(html)
    assert len(h1_matches) == 1, (
        f"Placeholder template MORA imati TAČNO 1 <h1> element, pronađeno {len(h1_matches)}. "
        f"H1 contents: {h1_matches!r}"
    )
    h1_text = h1_matches[0]
    assert "Stranica još nije dostupna" in h1_text, (
        f"<h1> MORA sadržati tekst 'Stranica još nije dostupna' (sr render kroz {{% translate %}}), "
        f"dobio: {h1_text!r}."
    )


def test_placeholder_uses_semantic_main_landmark(client):
    """AC2.6: semantic main landmark za a11y.

    base.html renderuje JEDAN <main id="main-content"> wrapper (Story 1.6 deliverable);
    placeholder template extends base.html i renderuje sadržaj UNUTAR {% block content %}
    koji je već unutar tog <main>-a. Nested <main> elementi su HTML5 spec violation
    (samo jedan <main> per dokument), pa placeholder wrapper MORA biti <div role="main">
    ili <section> (NE drugi <main>), uz reuse postojećeg base.html <main> landmark-a.

    Test asertuje:
    - Postoji TAČNO 1 <main> element u render-u (base.html provider)
    - Placeholder wrapper koristi `coric-product-placeholder` BEM klasu (per SM-D21)
    """
    activate("sr")
    url = "/sr/proizvod/test-slug/"

    response = client.get(url)
    html = response.content.decode("utf-8")

    main_pattern = re.compile(r"<main\b[^>]*>", re.IGNORECASE)
    main_matches = main_pattern.findall(html)
    assert main_matches, "Placeholder render MORA imati bar 1 <main> element (base.html provider)."
    assert len(main_matches) == 1, (
        f"Placeholder render MORA imati TAČNO 1 <main> element (HTML5 spec — "
        f"nested <main> je invalid). Pronađeno: {len(main_matches)}: {main_matches!r}. "
        "Placeholder wrapper MORA biti <div class='coric-product-placeholder'> (NE drugi <main>)."
    )

    # Wrapper klasa za placeholder
    assert "coric-product-placeholder" in html, (
        "Placeholder wrapper MORA imati klasu 'coric-product-placeholder' "
        "(AC8 brand-listing.css selektor per SM-D21 scope)."
    )
