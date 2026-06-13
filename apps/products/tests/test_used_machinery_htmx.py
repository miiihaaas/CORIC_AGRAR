"""Story 2.9 — HTMX request branching tests (RED phase TDD).

Pokriva AC2 + AC5 — HTMX request handling: partial-only response, OOB div presence/absence
based on request.htmx (SM-D23 OOB guard fix), `hx-push-url` URL sync, pluralized count
message (sr nplurals=3, placeholder `%(counter)s` per BT fix), pagination preserves
filter+sort params + uses HTMX (SM-D9 PAG pattern).

Simulacija HTMX request-a: `Client.get(..., HTTP_HX_REQUEST="true")` postavlja
HX-Request header koji `django_htmx.middleware.HtmxMiddleware` parse-uje u
`request.htmx=True`.

Test scope (~10 tests):
- HTMX partial-only return: 2 testa (full chrome absent, used-results wrapper present)
- OOB guard SM-D23: 2 testa (renders for HTMX, NOT for full page)
- HTMX request preserves active_filters in context: 1 test
- Pagination + HTMX integration: 3 testa (preserves filter+sort, hx-target, dual hx-get+href)
- Pagination URL no double `??`: 1 test (regression guard)
- Initial full-page render applies filters from URL: 1 test (server-side filter, NIJE samo HTMX swap)

Pokrenuti sa:
    docker compose -f compose/local.yml exec django uv run pytest \\
        apps/products/tests/test_used_machinery_htmx.py -v

Refs:
- 2-9-used-machinery-listing-sa-filterima.md (AC2 + AC5 + SM-D9/D15/D23)
- 2-9-interface-contract.md § 3 (_used_results_grid.html OOB + pagination)
- project-context.md § HTMX response patterns (linija 184-194)
"""

from __future__ import annotations

import re
from decimal import Decimal

import pytest
from django.utils.translation import activate

from apps.brands.tests.factories import BrandFactory
from apps.products.tests.factories import UsedProductFactory

pytestmark = pytest.mark.django_db


# =============================================================================
# AC2 — HTMX request returns partial only (no full page chrome)
# =============================================================================


def test_ac2_htmx_request_returns_partial_only(client):
    """AC2 + SM-D3: HTMX request (HX-Request: true) returns _used_results_grid.html
    partial — NEMA full page chrome (`<html>`, `<head>`, `<body>`, `<main>`).
    """
    activate("sr")
    brand = BrandFactory.create()
    UsedProductFactory.create(brand=brand, name="HTMX Partial Test")

    response = client.get(
        "/sr/mehanizacija/polovna/",
        HTTP_HOST="localhost",
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == 200
    html = response.content.decode("utf-8")

    assert "<!DOCTYPE" not in html, (
        f"HTMX response NE SME imati DOCTYPE (partial only). Response starts: {html[:200]!r}."
    )
    assert "<html" not in html.lower()
    assert "<head" not in html.lower()
    # ALI MORA imati grid wrapper
    assert 'id="used-results"' in html, (
        "HTMX response MORA sadržati `<div id=\"used-results\">` wrapper "
        "(template selection: get_template_names() returns _used_results_grid.html)."
    )


def test_ac2_full_page_request_renders_chrome(client):
    """AC2: non-HTMX request renderuje full page sa base.html chrome (<html>, <body>, <main>)."""
    activate("sr")
    brand = BrandFactory.create()
    UsedProductFactory.create(brand=brand, name="Full Page Test")

    response = client.get("/sr/mehanizacija/polovna/", HTTP_HOST="localhost")

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert "<html" in html.lower()
    assert "<body" in html.lower()
    assert "<main" in html.lower()


# =============================================================================
# AC5 — OOB div guard (SM-D23 fix)
# =============================================================================


def test_ac5_oob_div_renders_only_for_htmx_request(client):
    """AC5 + SM-D23 (OOB fix): HTMX request response MORA sadržati OOB div
    `<div hx-swap-oob="innerHTML:#aria-live">` sa pluralized count message.
    """
    activate("sr")
    brand = BrandFactory.create()
    UsedProductFactory.create(brand=brand, name="OOB Test")

    response = client.get(
        "/sr/mehanizacija/polovna/",
        HTTP_HOST="localhost",
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    # Co-location check: hx-swap-oob i #aria-live MORAJU biti na ISTOM <div> elementu,
    # NIJE samo nezavisno prisutni u response-u (regex tightening — sprečava false-pass
    # ako bi atributi bili u odvojenim div-ovima).
    oob_div_pattern = re.compile(
        r'<div[^>]*hx-swap-oob=["\']innerHTML:#aria-live["\']',
        re.IGNORECASE,
    )
    assert oob_div_pattern.search(html), (
        "HTMX response MORA sadržati `<div hx-swap-oob=\"innerHTML:#aria-live\">` "
        "sa OBA atributa na ISTOM div elementu (co-location). "
        f"Per project-context.md linija 184-187 + SM-D23. Response: {html[:500]!r}."
    )


def test_ac5_oob_div_not_rendered_for_non_htmx_request(client):
    """AC5 + SM-D23 (OOB guard fix): non-HTMX request (full page render) NE SME sadržati
    OOB div — guard `{% if request.htmx %}` u _used_results_grid.html sprečava
    plain-text render OOB markup-a u inicijalnom server-side render-u.
    """
    activate("sr")
    brand = BrandFactory.create()
    UsedProductFactory.create(brand=brand, name="No-OOB Test")

    response = client.get("/sr/mehanizacija/polovna/", HTTP_HOST="localhost")

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert "hx-swap-oob" not in html, (
        "Non-HTMX (full page) response NE SME sadržati `hx-swap-oob` atribut "
        "(SM-D23 OOB guard `{% if request.htmx %}` u _used_results_grid.html)."
    )


# =============================================================================
# AC5 — HTMX request preserves active_filters in context (form restore on HTMX swap)
# =============================================================================


def test_ac5_htmx_request_preserves_active_filters_in_context(client):
    """AC5: HTMX request sa filter query params propagira u context['active_filters']
    koje template renderuje u hidden input values + slider data-value attributes.
    """
    activate("sr")
    brand = BrandFactory.create()
    UsedProductFactory.create(brand=brand, name="Restore Ctx", price_eur=Decimal("10000.00"))

    response = client.get(
        "/sr/mehanizacija/polovna/?cena_min=5000&godina_max=2024&sort=cena_asc",
        HTTP_HOST="localhost",
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == 200
    active = response.context.get("active_filters")
    assert active is not None, "active_filters MORA biti u context-u za HTMX request-e."
    assert active.get("cena_min") == "5000"
    assert active.get("godina_max") == "2024"
    assert response.context.get("selected_sort") == "cena_asc"


# =============================================================================
# AC5 — Pagination + HTMX integration (SM-D9 PAG pattern REUSE Story 2.8)
# =============================================================================


def test_ac5_pagination_link_preserves_filter_params_and_uses_htmx(client):
    """AC5 + SM-D9: pagination CTAs preservuju ALL current filter+sort params u URL-u
    kroz `{% querystring %}` Django 5.2+ tag (override-uje samo `page=N`); koriste HTMX
    (NE plain full-reload).

    Setup: 14 USED proizvoda (paginate_by=12 → 2 strane).
    """
    activate("sr")
    brand = BrandFactory.create()
    for i in range(14):
        UsedProductFactory.create(brand=brand, name=f"PAG Used {i}", price_eur=Decimal("5000.00"))

    response = client.get(
        "/sr/mehanizacija/polovna/?cena_min=1000&sort=cena_asc",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 200
    html = response.content.decode("utf-8")

    # Pagination "next" link mora postojati (jer 14 > 12 paginate_by)
    next_pattern = re.compile(
        r'<a[^>]*data-testid="pagination-next"[^>]*>',
        re.IGNORECASE,
    )
    next_match = next_pattern.search(html)
    assert next_match, (
        "Pagination 'next' link sa `data-testid=\"pagination-next\"` MORA postojati "
        "(14 USED proizvoda > 12 paginate_by)."
    )
    next_tag = next_match.group(0)

    assert "hx-get" in next_tag, (
        f"Pagination link MORA imati `hx-get` atribut (SM-D9). Tag: {next_tag!r}."
    )
    assert 'hx-target="#used-results"' in next_tag, (
        f"Pagination link MORA imati `hx-target=\"#used-results\"`. Tag: {next_tag!r}."
    )
    assert 'hx-push-url="true"' in next_tag, (
        f"Pagination link MORA imati `hx-push-url=\"true\"`. Tag: {next_tag!r}."
    )
    # Filter param mora biti preserved
    assert "cena_min=1000" in next_tag, (
        f"Pagination link MORA preservovati current filter param (`cena_min=1000`). "
        f"Tag: {next_tag!r}."
    )
    # Sort param mora biti preserved
    assert "sort=cena_asc" in next_tag, (
        f"Pagination link MORA preservovati sort param (`sort=cena_asc`). Tag: {next_tag!r}."
    )
    # Page mora biti incremented
    assert "page=2" in next_tag


def test_ac5_pagination_link_has_dual_hx_get_and_href(client):
    """AC5: pagination link MORA imati `href` fallback pored `hx-get` (right-click
    open-in-new-tab + noscript graceful degradation).
    """
    activate("sr")
    brand = BrandFactory.create()
    for i in range(14):
        UsedProductFactory.create(brand=brand, name=f"Href Fallback {i}")

    response = client.get("/sr/mehanizacija/polovna/", HTTP_HOST="localhost")

    assert response.status_code == 200
    html = response.content.decode("utf-8")

    next_pattern = re.compile(
        r'<a[^>]*data-testid="pagination-next"[^>]*>',
        re.IGNORECASE,
    )
    next_match = next_pattern.search(html)
    assert next_match
    next_tag = next_match.group(0)

    assert "href=" in next_tag, (
        f"Pagination link MORA imati `href` fallback. Tag: {next_tag!r}."
    )


def test_ac5_pagination_url_has_no_double_question_mark(client):
    """AC5 + SM-D9 regression guard: pagination URL-ovi NE SMEJU sadržati `??` substring.

    Django 5.2 `{% querystring %}` tag emits ONLY `key=value&...` BEZ leading `?`;
    literal `?` u template-u je jedini separator. Bug: ako Dev pogresno koristi
    `?{% querystring %}` GDE `{% querystring %}` već vraća leading `?`, dobijemo `??page=N`.
    """
    activate("sr")
    brand = BrandFactory.create()
    for i in range(14):
        UsedProductFactory.create(brand=brand, name=f"NoDoubleQ {i}")

    response = client.get("/sr/mehanizacija/polovna/", HTTP_HOST="localhost")
    html = response.content.decode("utf-8")

    # Find all pagination link tags
    pagination_pattern = re.compile(
        r'<a[^>]*data-testid="pagination-(prev|next)"[^>]*>',
        re.IGNORECASE,
    )
    matches = list(pagination_pattern.finditer(html))
    assert matches, "Pagination links MORAJU postojati za regression guard."

    for m in matches:
        tag = m.group(0)
        assert "??" not in tag, (
            f"Pagination link sadrži `??` (double question mark — Django 5.2 querystring "
            f"tag misuse). Tag: {tag!r}. Use `?{{% querystring page=N %}}` "
            "(querystring vraća samo key=value bez vodećeg `?`)."
        )
        # Mora imati single ? sa page=
        assert re.search(r'\?page=\d+', tag) or re.search(r'\?[a-z_]+=[^&"]+(?:&page=\d+|&[^"]*page=\d+)', tag), (
            f"Pagination link MORA imati `?page=N` ili `?...&page=N` u URL-u. Tag: {tag!r}."
        )


# =============================================================================
# AC5 — Initial full-page render with filter params (server-side, NIJE HTMX swap)
# =============================================================================


def test_ac5_initial_full_page_render_applies_filter_params(client):
    """AC5 + AC8: GET full page sa filter params (browser visit to shared URL)
    renderuje filtrirane rezultate kroz initial server-side render — NIJE samo HTMX swap.
    """
    activate("sr")
    brand = BrandFactory.create()
    cheap = UsedProductFactory.create(brand=brand, name="Cheap Initial", price_eur=Decimal("3000.00"))
    expensive = UsedProductFactory.create(brand=brand, name="Expensive Initial", price_eur=Decimal("50000.00"))

    response = client.get(
        "/sr/mehanizacija/polovna/?cena_min=10000",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 200
    html = response.content.decode("utf-8")

    assert f'data-testid="used-card-{expensive.slug}"' in html, (
        f"Initial full-page render sa ?cena_min=10000 MORA prikazati expensive product "
        f"(testid='used-card-{expensive.slug}'). Server-side filter applied."
    )
    assert f'data-testid="used-card-{cheap.slug}"' not in html, (
        "Cheap product (price=3000) NE SME biti u listing-u sa ?cena_min=10000. "
        "Filter MORA biti applied PRE render-a."
    )
