"""Story 2.13 — AC3/AC5/AC6/AC7 view (search_dropdown / search_results) (TEA RED).

Pokriva view ponašanje:
- min-2-char guard (SM-D13 — NE izvršava SQL), query-length cap 100 (SM-D17),
- grouped dict UVEK ima `objave: []` (SM-D3 forward-compat),
- request.htmx branching (partial vs full strana),
- suggestion_count = total PRE slice (SM-D11),
- max 5 po grupi,
- empty-state render za 0 rezultata,
- GET-only (POST nije podržan).

⚠️ requires_postgres na FTS-zavisnim testovima (Task 8.0/IMP-2). Guard/branching
testovi koji NE pogađaju FTS path (min-char, length-cap struktura) mogu raditi bez
PG ali markirani su requires_postgres radi konzistentne PG test DB (story koristi
realan PG za sve view testove).

Pokrenuti sa:
    docker compose -f compose/local.yml exec django uv run pytest \\
        apps/search/tests/test_views.py -v

Refs:
- 2-13-global-search-sa-postgresql-fts.md AC3/AC5/AC6/AC7 + Task 4 + SM-D3/D11/D13/D17
- 2-13-interface-contract.md § 2 (views.py + Context surface)
"""

from __future__ import annotations

import pytest
from django.urls import reverse
from django.utils.translation import activate

from apps.search.tests.factories import SearchProductFactory

pytestmark = [pytest.mark.django_db, pytest.mark.requires_postgres]


def _dropdown_url():
    activate("sr")
    return reverse("search:dropdown")


# AC3/AC6/SM-D3: grouped dict UVEK ima `objave: []` (forward-compat skelet)
def test_grouped_context_always_has_empty_objave_key(client):
    activate("sr")
    SearchProductFactory.create(name_sr="Berba proizvod")

    response = client.get(
        _dropdown_url(), {"q": "berba"}, HTTP_HOST="localhost", HTTP_HX_REQUEST="true"
    )
    assert response.status_code == 200
    grouped = response.context.get("grouped")
    assert grouped is not None, "Context MORA imati 'grouped' dict."
    assert "objave" in grouped, "grouped MORA UVEK imati ključ 'objave' (SM-D3 forward-compat)."
    assert grouped["objave"] == [], "grouped['objave'] MORA biti prazna lista [] u v1 (SM-D3)."
    assert "proizvodi" in grouped, "grouped MORA imati ključ 'proizvodi'."


# AC3/SM-D13: min-2-char guard — < 2 znaka NE izvršava FTS upit (too_short proxy)
def test_short_query_no_sql_executed(client):
    activate("sr")
    SearchProductFactory.create(name_sr="Berba")

    # 1 znak — view MORA vratiti too_short partial BEZ FTS query-ja. Precizno brojanje
    # SQL-a je brittle (session/itd. queries variraju), pa se „no FTS" dokazuje preko
    # too_short=True + suggestion_count=0 proxy-ja (SM-D13 / Addendum B.2).
    response = client.get(
        _dropdown_url(), {"q": "b"}, HTTP_HOST="localhost", HTTP_HX_REQUEST="true"
    )
    assert response.status_code == 200
    assert response.context.get("too_short") is True, (
        "Za query < 2 znaka context['too_short'] MORA biti True (SM-D13)."
    )
    # suggestion_count za too_short ne sme reflektovati FTS rezultat
    assert response.context.get("suggestion_count", 0) == 0, (
        "too_short slučaj NE izvršava SQL → suggestion_count 0 (SM-D13)."
    )


# AC3/SM-D13: tačno 2 znaka POKREĆE pretragu (granica)
def test_exactly_two_chars_runs_search(client):
    activate("sr")
    SearchProductFactory.create(name_sr="TB proizvod")

    response = client.get(
        _dropdown_url(), {"q": "TB"}, HTTP_HOST="localhost", HTTP_HX_REQUEST="true"
    )
    assert response.status_code == 200
    assert response.context.get("too_short") in (False, None), (
        "Tačno 2 znaka NIJE too_short — pretraga se izvršava (SM-D13 granica)."
    )


# AC3/SM-D13: whitespace-only query (.strip) tretira se kao prazan → too_short
def test_whitespace_only_query_is_too_short(client):
    activate("sr")
    response = client.get(
        _dropdown_url(), {"q": "   "}, HTTP_HOST="localhost", HTTP_HX_REQUEST="true"
    )
    assert response.status_code == 200
    assert response.context.get("too_short") is True, (
        "Whitespace-only query MORA biti too_short posle .strip() (SM-D13)."
    )


# AC3/SM-D17: query > 100 znakova se trunkuje na 100 (DoS guard, NEMA 400)
def test_long_query_truncated_to_100(client):
    activate("sr")
    long_q = "a" * 250

    response = client.get(
        _dropdown_url(), {"q": long_q}, HTTP_HOST="localhost", HTTP_HX_REQUEST="true"
    )
    assert response.status_code == 200, (
        "Dugačak query NE SME vratiti 400 — samo se trunkuje (SM-D17)."
    )
    query_in_ctx = response.context.get("query", "")
    assert len(query_in_ctx) <= 100, (
        f"context['query'] MORA biti trunkovan na ≤100 znakova (SM-D17), dobio "
        f"dužinu {len(query_in_ctx)}."
    )


# AC6/SM-D11: max 5 po grupi; suggestion_count = TOTAL PRE slice (8 found / 5 shown → 8)
def test_max_5_per_group_but_suggestion_count_is_total(client):
    activate("sr")
    for i in range(8):
        SearchProductFactory.create(name_sr=f"Berba model {i}")

    response = client.get(
        _dropdown_url(), {"q": "berba"}, HTTP_HOST="localhost", HTTP_HX_REQUEST="true"
    )
    assert response.status_code == 200
    grouped = response.context["grouped"]
    assert len(grouped["proizvodi"]) == 5, (
        f"grouped['proizvodi'] MORA biti max 5 (slice u view-u, SM-D11), dobio "
        f"{len(grouped['proizvodi'])}."
    )
    assert response.context["suggestion_count"] == 8, (
        "suggestion_count MORA biti TOTAL (8) PRE slice — NE 5 (SM-D11). aria-live "
        f"najavljuje ukupan broj. Dobio {response.context['suggestion_count']}."
    )


# AC5/SM-D14: HTMX request vraća PARTIAL (dropdown), NE full stranu
def test_htmx_request_returns_partial_not_full_page(client):
    activate("sr")
    SearchProductFactory.create(name_sr="Berba proizvod")

    response = client.get(
        _dropdown_url(), {"q": "berba"}, HTTP_HOST="localhost", HTTP_HX_REQUEST="true"
    )
    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert "<!DOCTYPE" not in html, "HTMX dropdown response MORA biti partial (NEMA DOCTYPE)."
    assert "<html" not in html.lower(), "HTMX dropdown response NE SME imati <html> tag."


# AC7: empty-state — 0 rezultata (≥2 znaka) renderuje _search_empty.html
def test_empty_state_for_zero_results(client):
    activate("sr")
    # NEMA proizvoda koji matchuju
    response = client.get(
        _dropdown_url(), {"q": "nepostojeci"}, HTTP_HOST="localhost", HTTP_HX_REQUEST="true"
    )
    assert response.status_code == 200
    assert response.context["suggestion_count"] == 0, "0 rezultata → suggestion_count 0."
    assert response.context.get("too_short") in (False, None), (
        "0 rezultata sa ≥2 znaka NIJE too_short (AC7 — razlikuje se od < 2 znaka)."
    )
    html = response.content.decode("utf-8")
    assert 'data-testid="search-empty-state"' in html, (
        "0 rezultata MORA renderovati _search_empty.html (testid search-empty-state)."
    )


# AC7/SM-D18: empty-state context ima CTA data (popular_categories + header_brands)
def test_empty_state_cta_context(client):
    from apps.brands.tests.factories import BrandFactory, CategoryFactory

    activate("sr")
    CategoryFactory.create(name="Plugovi", display_order=1)
    BrandFactory.create(name="Vidljiv Brend", is_coming_soon=False)
    BrandFactory.create_coming_soon(name="Skriveni Brend")

    response = client.get(
        _dropdown_url(), {"q": "nepostojeci"}, HTTP_HOST="localhost", HTTP_HX_REQUEST="true"
    )
    assert response.status_code == 200
    assert "popular_categories" in response.context, (
        "Empty-state context MORA imati 'popular_categories' (SM-D18)."
    )
    brands_ctx = response.context.get("header_brands")
    assert brands_ctx is not None, "Empty-state context MORA imati 'header_brands' (SM-D18)."
    brand_names = {b.name for b in brands_ctx}
    assert "Skriveni Brend" not in brand_names, (
        "header_brands MORA filtrirati is_coming_soon=False (SM-D18)."
    )


# AC3/SM-D16: non-HTMX /pretraga/ vraća FULL stranu (search_results.html)
def test_results_page_full_render_non_htmx(client):
    activate("sr")
    SearchProductFactory.create(name_sr="Berba na full strani")

    url = reverse("search:results")
    response = client.get(url, {"q": "berba"}, HTTP_HOST="localhost")  # NEMA HX-Request
    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert 'data-testid="search-results-page"' in html, (
        "Non-HTMX /pretraga/ MORA renderovati search_results.html full stranu "
        "(testid search-results-page, SM-D16)."
    )


# NEGATIVE/SM-D17: GET-only — POST na dropdown endpoint NIJE podržan (405 ili nije GET path)
def test_dropdown_endpoint_is_get_only(client):
    activate("sr")
    response = client.post(_dropdown_url(), {"q": "berba"}, HTTP_HOST="localhost")
    assert response.status_code in (405, 400), (
        "search_dropdown je GET-only (SM-D17) — POST MORA vratiti 405 (Method Not Allowed) "
        f"ili 400. Dobio {response.status_code}."
    )
