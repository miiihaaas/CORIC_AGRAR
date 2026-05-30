"""Story 2.8 — HTMX filter request tests (RED phase TDD).

Pokriva AC6 — HTMX request handling: partial-only response, OOB div presence/absence
based on request.htmx (SM-D23 OOB guard fix), `hx-push-url` URL sync, pluralized count
message (sr nplurals=3, placeholder `%(counter)s` per BT fix), pagination preserves
filter params + uses HTMX (SM-D18 PAG fix), swap target.

Simulacija HTMX request-a: `Client.get(..., HTTP_HX_REQUEST="true")` postavlja
HX-Request header koji `django_htmx.middleware.HtmxMiddleware` parse-uje u `request.htmx=True`.

TEA RED phase: SVI testovi MORAJU pasti — view ne postoji, partial ne postoji.

Pokrenuti sa:
    docker compose -f compose/local.yml exec django uv run pytest \\
        apps/products/tests/test_htmx_tractor_filter.py -v

Refs:
- 2-8-tractor-listing-strana-sa-htmx-filterima.md (AC6 + SM-D15/D17/D18/D23)
- 2-8-interface-contract.md § 2 (HTMX branching) + § 3 (_results_grid.html OOB)
- project-context.md § HTMX response patterns (linija 184-194)
"""

from __future__ import annotations

import re

import pytest
from django.utils.translation import activate

from apps.brands.tests.factories import BrandFactory
from apps.products.tests.factories import TractorProductFactory

pytestmark = pytest.mark.django_db


# =============================================================================
# AC6 — HTMX request returns partial, not full page
# =============================================================================


def test_htmx_request_returns_partial_only(client):
    """AC6 + SM-D3: HTMX request (HX-Request: true) returns _results_grid.html partial
    — NEMA full page chrome (`<html>`, `<body>`, `<main>`, base.html header/footer).
    """
    activate("sr")
    brand = BrandFactory.create()
    TractorProductFactory.create(brand=brand, name="Partial Test Tractor")

    response = client.get("/sr/traktori/", HTTP_HOST="localhost", HTTP_HX_REQUEST="true")

    assert response.status_code == 200
    html = response.content.decode("utf-8")

    # NEMA full page chrome
    assert "<!DOCTYPE" not in html, (
        f"HTMX response NE SME imati DOCTYPE (partial only). Response starts: {html[:200]!r}."
    )
    assert "<html" not in html.lower(), (
        "HTMX response NE SME imati `<html>` tag (partial only)."
    )
    assert "<head" not in html.lower(), (
        "HTMX response NE SME imati `<head>` tag (partial only)."
    )
    # ALI MORA imati grid wrapper
    assert 'id="tractor-results"' in html, (
        "HTMX response MORA sadržati `<div id=\"tractor-results\">` wrapper "
        "(template selection: get_template_names() returns _results_grid.html)."
    )


# =============================================================================
# AC6 — OOB div guard (SM-D23 fix)
# =============================================================================


def test_oob_div_rendered_for_htmx_request(client):
    """AC6 + SM-D23 (OOB fix): HTMX request response MORA sadržati OOB div
    `<div hx-swap-oob="innerHTML:#aria-live">` sa pluralized count message.

    Per project-context.md linija 184-187, OOB pattern je KRITIČAN za HTMX swap responses.
    """
    activate("sr")
    brand = BrandFactory.create()
    TractorProductFactory.create(brand=brand, name="OOB Test Tractor")

    response = client.get("/sr/traktori/", HTTP_HOST="localhost", HTTP_HX_REQUEST="true")

    assert response.status_code == 200
    html = response.content.decode("utf-8")

    assert "hx-swap-oob" in html, (
        "HTMX response MORA sadržati `hx-swap-oob` atribut (OOB aria-live announcement). "
        "Per project-context.md linija 184-187 + SM-D23. Response sample: "
        f"{html[:500]!r}"
    )
    assert "#aria-live" in html, (
        "HTMX response OOB div MORA targetovati `#aria-live` (singleton iz base.html "
        "linija 29 — htmx_aria.aria_live tag)."
    )


def test_oob_div_not_rendered_for_non_htmx_request(client):
    """AC6 + SM-D23 (OOB guard fix): Non-HTMX request (full page render) NE SME sadržati
    OOB div — guard `{% if request.htmx %}` u _results_grid.html sprečava plain-text
    render OOB markup-a u inicijalnom server-side full-page render-u.
    """
    activate("sr")
    brand = BrandFactory.create()
    TractorProductFactory.create(brand=brand, name="No-OOB Test Tractor")

    response = client.get("/sr/traktori/", HTTP_HOST="localhost")  # NEMA HX-Request header

    assert response.status_code == 200
    html = response.content.decode("utf-8")

    assert "hx-swap-oob" not in html, (
        "Non-HTMX (full page) response NE SME sadržati `hx-swap-oob` atribut "
        "(SM-D23 OOB guard `{% if request.htmx %}` u _results_grid.html). "
        "Bez guard-a, OOB div bi se render-ovao kao plain plutajući tekst ispod grid-a."
    )


# =============================================================================
# AC6 — Pluralized count message (sr nplurals=3, BT fix: %(counter)s placeholder)
# =============================================================================


def test_oob_count_message_is_pluralized_singular(client):
    """AC6 + SM-D15 (BT fix): OOB count message za N=1 koristi singular form
    „Pronađen 1 model." (msgstr[0] u sr nplurals=3).
    """
    activate("sr")
    brand = BrandFactory.create()
    TractorProductFactory.create(brand=brand, name="Singular Test", horse_power=80)

    response = client.get(
        "/sr/traktori/?snaga_min=80&snaga_max=80",
        HTTP_HOST="localhost",
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == 200
    html = response.content.decode("utf-8")

    # Singular form: "Pronađen 1 model" (msgstr[0] sa %(counter)s placeholder = "1")
    assert "Pronađen 1 model" in html, (
        "OOB count message za N=1 MORA biti 'Pronađen 1 model.' (msgstr[0] sa "
        f"placeholder %(counter)s=1). Response sample: {html[-500:]!r}."
    )


def test_oob_count_message_is_pluralized_few(client):
    """AC6 + SM-D15: OOB count message za N=2-4 koristi few form
    „Pronađena 2 modela." (msgstr[1] u sr nplurals=3).
    """
    activate("sr")
    brand = BrandFactory.create()
    TractorProductFactory.create(brand=brand, name="Few A", horse_power=80)
    TractorProductFactory.create(brand=brand, name="Few B", horse_power=80)

    response = client.get(
        "/sr/traktori/?snaga_min=80&snaga_max=80",
        HTTP_HOST="localhost",
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == 200
    html = response.content.decode("utf-8")

    # Few form: "Pronađena 2 modela" (msgstr[1])
    assert "Pronađena 2 modela" in html, (
        "OOB count message za N=2 MORA biti 'Pronađena 2 modela.' (msgstr[1]). "
        "sr nplurals=3 plural completion is_complete? Vidi SM-D15. "
        f"Response sample: {html[-500:]!r}."
    )


def test_oob_count_message_pluralized_zero_uses_other_form(client):
    """AC6 + SM-D15: OOB count message za N=0 koristi other form
    „Pronađeno 0 modela." (msgstr[2] u sr nplurals=3 — 0 spada u 5-20 grupu).
    """
    activate("sr")
    BrandFactory.create()
    # NEMA TractorProductFactory.create — 0 product-a

    response = client.get("/sr/traktori/", HTTP_HOST="localhost", HTTP_HX_REQUEST="true")

    assert response.status_code == 200
    html = response.content.decode("utf-8")

    # Other form: "Pronađeno 0 modela" (msgstr[2])
    assert "Pronađeno 0 modela" in html, (
        "OOB count message za N=0 MORA biti 'Pronađeno 0 modela.' (msgstr[2] — sr "
        f"plural form za 0 i 5-20). Response sample: {html[-500:]!r}."
    )


# =============================================================================
# AC6 — hx-push-url + URL sync via filter params
# =============================================================================


def test_filter_params_in_request_are_returned_in_active_filters_context(client):
    """AC6 + AC7 + SM-D17: HTMX request sa filter query params propagira u
    `context['active_filters']` koji template renderuje u hidden input values + slider
    data-value attributes — omogućava deep-link i form restore.
    """
    activate("sr")
    brand = BrandFactory.create()
    TractorProductFactory.create(brand=brand, name="Restore Test", horse_power=80, price_eur=15000)

    response = client.get(
        "/sr/traktori/?snaga_min=60&cena_max=25000",
        HTTP_HOST="localhost",
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == 200
    active = response.context.get("active_filters")
    assert active is not None, "active_filters MORA biti u context-u za HTMX request-e."
    assert active.get("snaga_min") == "60", (
        f"active_filters['snaga_min'] MORA biti '60', dobio {active.get('snaga_min')!r}."
    )
    assert active.get("cena_max") == "25000", (
        f"active_filters['cena_max'] MORA biti '25000', dobio {active.get('cena_max')!r}."
    )


# =============================================================================
# AC6 — Pagination + HTMX integration (SM-D18 PAG fix)
# =============================================================================


def test_pagination_link_preserves_filter_params_and_uses_htmx(client):
    """AC6 + SM-D18 (PAG fix): pagination CTAs koriste HTMX (NE plain full-reload <a>);
    preservuju ALL current filter params u URL-u kroz `{% querystring %}` Django 5.2+
    tag (override-uje samo `page=N`).

    Setup: 26 traktor product-a (paginate_by=24 → 2 strane). GET stranica 1 — pagination
    nav mora imati `hx-get` + `hx-target="#tractor-results"` + `hx-push-url="true"`.
    """
    activate("sr")
    brand = BrandFactory.create()
    for i in range(26):
        TractorProductFactory.create(brand=brand, name=f"PAG Tractor {i}", horse_power=80)

    response = client.get("/sr/traktori/?snaga_min=80", HTTP_HOST="localhost")

    assert response.status_code == 200
    html = response.content.decode("utf-8")

    # Pagination "next" link mora postojati (jer 26 > 24 paginate_by)
    next_pattern = re.compile(
        r'<a[^>]*data-testid="pagination-next"[^>]*>',
        re.IGNORECASE,
    )
    next_match = next_pattern.search(html)
    assert next_match, (
        "Pagination 'next' link sa `data-testid=\"pagination-next\"` MORA postojati "
        "(26 product-a > 24 paginate_by)."
    )
    next_tag = next_match.group(0)

    # MORA imati hx-get atribut sa filter param preservation
    assert "hx-get" in next_tag, (
        f"Pagination link MORA imati `hx-get` atribut (SM-D18 PAG fix). Tag: {next_tag!r}."
    )
    assert 'hx-target="#tractor-results"' in next_tag, (
        f"Pagination link MORA imati `hx-target=\"#tractor-results\"`. Tag: {next_tag!r}."
    )
    assert 'hx-push-url="true"' in next_tag, (
        f"Pagination link MORA imati `hx-push-url=\"true\"`. Tag: {next_tag!r}."
    )
    # Filter param mora biti preserved (snaga_min=80)
    assert "snaga_min=80" in next_tag, (
        f"Pagination link MORA preservovati current filter params (`snaga_min=80`). "
        f"`{{% querystring %}}` Django 5.2+ tag NIJE override-uje. Tag: {next_tag!r}."
    )
    # Page must be incremented
    assert "page=2" in next_tag, (
        f"Pagination 'next' link MORA imati `page=2` (next page number). Tag: {next_tag!r}."
    )


def test_pagination_link_has_href_fallback(client):
    """AC6 + SM-D18: pagination link MORA imati `href` fallback pored `hx-get`
    (right-click open-in-new-tab + noscript graceful degradation).
    """
    activate("sr")
    brand = BrandFactory.create()
    for i in range(26):
        TractorProductFactory.create(brand=brand, name=f"Href Fallback {i}")

    response = client.get("/sr/traktori/", HTTP_HOST="localhost")

    assert response.status_code == 200
    html = response.content.decode("utf-8")

    next_pattern = re.compile(
        r'<a[^>]*data-testid="pagination-next"[^>]*>',
        re.IGNORECASE,
    )
    next_match = next_pattern.search(html)
    assert next_match, "Pagination 'next' link MORA postojati."
    next_tag = next_match.group(0)

    assert "href=" in next_tag, (
        f"Pagination link MORA imati `href` fallback (right-click + noscript). Tag: {next_tag!r}."
    )


def test_pagination_url_has_no_double_question_mark(client):
    """AC6 + SM-D18 regression guard (cross-story discovery from Story 2.9 review):
    pagination URL-ovi NE SMEJU sadržati `??` substring.

    Django 5.2 `{% querystring %}` tag emituje vodeći `?` automatski; ako template
    pogrešno koristi `?{% querystring %}` (literal `?` + tag koji takođe emituje `?`),
    URL postaje `??page=N` što je broken pagination. Story 2.8 `_results_grid.html`
    je imao ovaj bug na linijama 39/43/51/55 — popravljen u Story 2.9 Iter-1 Fix Pass.

    Setup: 26 traktor product-a (paginate_by=24 → 2 strane → pagination CTAs postoje).
    """
    activate("sr")
    brand = BrandFactory.create()
    for i in range(26):
        TractorProductFactory.create(brand=brand, name=f"NoDoubleQ Tractor {i}")

    response = client.get("/sr/traktori/", HTTP_HOST="localhost")
    html = response.content.decode("utf-8")

    pagination_pattern = re.compile(
        r'<a[^>]*data-testid="pagination-(prev|next)"[^>]*>',
        re.IGNORECASE,
    )
    matches = list(pagination_pattern.finditer(html))
    assert matches, "Pagination links MORAJU postojati za regression guard (26 > 24 paginate_by)."

    for m in matches:
        tag = m.group(0)
        assert "??" not in tag, (
            f"Pagination link sadrži `??` (double question mark — Django 5.2 querystring "
            f"tag misuse). Tag: {tag!r}. Use `{{% querystring page=N %}}` BEZ literal "
            f"`?` prefiksa (querystring tag već emituje vodeći `?`)."
        )
        # Mora imati single ? sa page= negde u URL-u
        assert re.search(r'\?(?:[a-z_]+=[^&"]+&)*page=\d+', tag), (
            f"Pagination link MORA imati `?page=N` ili `?...&page=N` u URL-u. Tag: {tag!r}."
        )


# =============================================================================
# AC6 — Initial server-side render also has filtered results (URL deep-link)
# =============================================================================


def test_initial_full_page_render_applies_filter_params(client):
    """AC6 + AC7: GET full page sa filter params (browser visit to shared URL)
    renderuje filtrirane rezultate kroz initial server-side render — NE samo HTMX swap.
    """
    activate("sr")
    brand = BrandFactory.create()
    weak = TractorProductFactory.create(brand=brand, name="Weak Initial", horse_power=60)
    strong = TractorProductFactory.create(brand=brand, name="Strong Initial", horse_power=120)

    response = client.get("/sr/traktori/?snaga_min=100", HTTP_HOST="localhost")  # NO HX-Request

    assert response.status_code == 200
    html = response.content.decode("utf-8")

    # Strong product MORA biti u grid (horse_power=120 matches snaga_min=100)
    assert f'data-testid="tractor-card-{strong.slug}"' in html, (
        f"Initial full-page render sa ?snaga_min=100 MORA prikazati strong tractor "
        f"(testid='tractor-card-{strong.slug}'). Server-side filter applied to initial render."
    )
    # Weak product NE SME biti (horse_power=60 < 100)
    assert f'data-testid="tractor-card-{weak.slug}"' not in html, (
        f"Initial full-page render sa ?snaga_min=100 NE SME prikazati weak tractor "
        f"(testid='tractor-card-{weak.slug}'). Filter MORA biti applied PRE render-a."
    )
