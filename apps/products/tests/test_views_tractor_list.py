"""Story 2.8 — TractorListView tests (RED phase TDD).

Pokriva AC1 (query budget) + AC2 (CBV ListView — queryset filter Category.is_for='traktori'
scope + SM-D11 defensive filter parsing + context: brands_for_header/active_filters/count;
HTMX vs full-page template branching kroz get_template_names() per SM-D3).

Test scope (~13 tests):
- AC1 query budget: 1 test (assertNumQueries — view ne postoji, placeholder ?)
- AC2 view + queryset:
  - traktori scope filter (subcategory__category__is_for='traktori')
  - is_published=True filter
  - horse_power_min/max filter
  - price_min/max filter
  - SM-D11 defensive parsing (invalid input silently ignored)
- AC2 context: brands_for_header (is_coming_soon=False), active_filters, count
- AC2 HTMX branching: get_template_names() returns partial vs full per request.htmx

EMPIRICAL QUERY COUNT: view does not exist yet — test placeholder marked, lock in
GREEN fix iter 1. Speculation: 5 queries (Brand list + Product count + Product slice +
session/auth middleware overhead).

Pokrenuti sa:
    docker compose -f compose/local.yml exec django uv run pytest \\
        apps/products/tests/test_views_tractor_list.py -v

Refs:
- 2-8-tractor-listing-strana-sa-htmx-filterima.md (AC1+AC2 + SM-D3/D5/D7/D8/D11)
- 2-8-interface-contract.md § 2 + § 9
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.utils.translation import activate

from apps.brands.tests.factories import BrandFactory
from apps.products.tests.factories import (
    ProductFactory,
    TractorProductFactory,
)

pytestmark = pytest.mark.django_db


# =============================================================================
# AC1 — Query budget (TEA placeholder — lock posle empirical probe u GREEN fix iter 1)
# =============================================================================


def test_tractor_list_query_budget(client, django_assert_num_queries):
    """AC1 (SM-D14): inicijalni page render mora poštovati query budget ≤ 5 SQL upita.

    Empirical baseline NIJE moguć pre Dev impl-a — placeholder assertNumQueries(5) je
    SPECULATION (1 Brand list + 1 Product count + 1 Product slice + 2 sessions/middleware
    overhead). TEA će lock-ovati na empirical broj u GREEN fix iter 1 nakon Dev impl-a.

    Setup: 1 brand + 5 traktor products (seed dovoljan za page slice koji nije prazan).
    """
    activate("sr")
    brand = BrandFactory.create(name="Query Budget Brand")
    for i in range(5):
        TractorProductFactory.create(brand=brand, name=f"Tractor {i}", horse_power=60 + i * 10)

    # GREEN fix iter 1 LOCK (empirical): 3 SQL upita (per CaptureQueriesContext probe).
    # Speculation bila 5 (Brand list + Product count + Product slice + 2 middleware).
    # Empirical reveal: 3 = Brand list + Paginator COUNT + Product page slice (sa
    # select_related brand/series/subcategory). Middleware sessions/auth NE generišu
    # SQL upite za anonimni GET (Django session middleware lazy-loads samo na write).
    # Story 3.4: 3 view upita + 1 SiteSettings chrome upit (header/footer site_setting, 1/request).
    with django_assert_num_queries(4):
        response = client.get("/sr/traktori/", HTTP_HOST="localhost")
        assert response.status_code == 200


# =============================================================================
# AC2 — Queryset: traktori scope filter (SM-D7)
# =============================================================================


def test_queryset_filters_traktori_scope_only(client):
    """AC2 (SM-D7): get_queryset() filtruje subcategory__category__is_for='traktori'.

    Setup: 1 traktor product (TractorProductFactory) + 1 product BEZ subcategory
    (ProductFactory default — subcategory=None) + 1 product sa MEHANIZACIJA category.
    Očekivano: SAMO traktor product u response listing-u.
    """
    activate("sr")
    brand = BrandFactory.create(name="Scope Brand")
    tractor = TractorProductFactory.create(brand=brand, name="Real Tractor")
    no_subcat_product = ProductFactory.create(brand=brand, name="No Subcat Product")  # subcategory=None

    # Mehanizacija product
    from apps.brands.models import Category, Subcategory
    mech_category = Category.objects.create(
        name="Mehanizacija Cat", slug="mech-cat", is_for="mehanizacija"
    )
    mech_subcat = Subcategory.objects.create(
        category=mech_category, name="Mech Sub", slug="mech-sub"
    )
    mech_product = ProductFactory.create(brand=brand, name="Mechanization", subcategory=mech_subcat)

    response = client.get("/sr/traktori/", HTTP_HOST="localhost")

    assert response.status_code == 200
    products = list(response.context["products"])
    product_pks = [p.pk for p in products]

    assert tractor.pk in product_pks, (
        f"Tractor product (pk={tractor.pk}) MORA biti u queryset-u "
        f"(subcategory.category.is_for='traktori'). Dobili: {product_pks!r}."
    )
    assert no_subcat_product.pk not in product_pks, (
        f"Product BEZ subcategory (pk={no_subcat_product.pk}) NE SME biti u listing-u "
        f"(subcategory__category__is_for JOIN na NULL = no match). Dobili: {product_pks!r}."
    )
    assert mech_product.pk not in product_pks, (
        f"Mehanizacija product (pk={mech_product.pk}) NE SME biti u traktor listing-u "
        f"(subcategory.category.is_for='mehanizacija'). Dobili: {product_pks!r}."
    )


def test_queryset_filters_is_published_true(client):
    """AC2: get_queryset() filtruje is_published=True; unpublished tractors su skriveni."""
    activate("sr")
    brand = BrandFactory.create(name="Pub Brand")
    pub = TractorProductFactory.create(brand=brand, name="Published Tractor", is_published=True)
    unpub = TractorProductFactory.create_unpublished(brand=brand, name="Unpublished Tractor")

    response = client.get("/sr/traktori/", HTTP_HOST="localhost")

    assert response.status_code == 200
    product_pks = [p.pk for p in response.context["products"]]
    assert pub.pk in product_pks, (
        f"Published tractor (pk={pub.pk}) MORA biti u listing-u. Dobili: {product_pks!r}."
    )
    assert unpub.pk not in product_pks, (
        f"Unpublished tractor (pk={unpub.pk}) NE SME biti u listing-u (is_published=True filter). "
        f"Dobili: {product_pks!r}."
    )


# =============================================================================
# AC2 — Filter parsing: horse_power_min/max + price_min/max
# =============================================================================


def test_queryset_filters_horse_power_min(client):
    """AC2: ?snaga_min=80 filtruje samo product-e sa horse_power >= 80."""
    activate("sr")
    brand = BrandFactory.create()
    weak = TractorProductFactory.create(brand=brand, name="Weak Tractor", horse_power=60)
    strong = TractorProductFactory.create(brand=brand, name="Strong Tractor", horse_power=120)

    response = client.get("/sr/traktori/?snaga_min=80", HTTP_HOST="localhost")

    assert response.status_code == 200
    product_pks = [p.pk for p in response.context["products"]]
    assert strong.pk in product_pks, f"horse_power=120 MORA biti u listing-u sa snaga_min=80. Dobili: {product_pks!r}."
    assert weak.pk not in product_pks, f"horse_power=60 NE SME biti u listing-u sa snaga_min=80. Dobili: {product_pks!r}."


def test_queryset_filters_horse_power_max(client):
    """AC2: ?snaga_max=100 filtruje samo product-e sa horse_power <= 100."""
    activate("sr")
    brand = BrandFactory.create()
    weak = TractorProductFactory.create(brand=brand, name="Weak Tractor 2", horse_power=60)
    strong = TractorProductFactory.create(brand=brand, name="Strong Tractor 2", horse_power=120)

    response = client.get("/sr/traktori/?snaga_max=100", HTTP_HOST="localhost")

    assert response.status_code == 200
    product_pks = [p.pk for p in response.context["products"]]
    assert weak.pk in product_pks, f"horse_power=60 MORA biti u listing-u sa snaga_max=100. Dobili: {product_pks!r}."
    assert strong.pk not in product_pks, f"horse_power=120 NE SME biti u listing-u sa snaga_max=100. Dobili: {product_pks!r}."


def test_queryset_filters_price_min(client):
    """AC2: ?cena_min=20000 filtruje samo product-e sa price_eur >= 20000 (DecimalField)."""
    activate("sr")
    brand = BrandFactory.create()
    cheap = TractorProductFactory.create(brand=brand, name="Cheap", price_eur=Decimal("15000.00"))
    expensive = TractorProductFactory.create(brand=brand, name="Expensive", price_eur=Decimal("30000.00"))

    response = client.get("/sr/traktori/?cena_min=20000", HTTP_HOST="localhost")

    assert response.status_code == 200
    product_pks = [p.pk for p in response.context["products"]]
    assert expensive.pk in product_pks, f"price=30000 MORA biti sa cena_min=20000. Dobili: {product_pks!r}."
    assert cheap.pk not in product_pks, f"price=15000 NE SME biti sa cena_min=20000. Dobili: {product_pks!r}."


def test_queryset_filters_price_max(client):
    """AC2: ?cena_max=20000 filtruje samo product-e sa price_eur <= 20000."""
    activate("sr")
    brand = BrandFactory.create()
    cheap = TractorProductFactory.create(brand=brand, name="Cheap 2", price_eur=Decimal("15000.00"))
    expensive = TractorProductFactory.create(brand=brand, name="Expensive 2", price_eur=Decimal("30000.00"))

    response = client.get("/sr/traktori/?cena_max=20000", HTTP_HOST="localhost")

    assert response.status_code == 200
    product_pks = [p.pk for p in response.context["products"]]
    assert cheap.pk in product_pks, f"price=15000 MORA biti sa cena_max=20000. Dobili: {product_pks!r}."
    assert expensive.pk not in product_pks, f"price=30000 NE SME biti sa cena_max=20000. Dobili: {product_pks!r}."


# =============================================================================
# AC2 — SM-D11 defensive filter parsing (silent ignore za invalid input)
# =============================================================================


@pytest.mark.parametrize(
    "query_string",
    [
        "snaga_min=abc",                 # ValueError int parse
        "snaga_max=-50",                 # negative ne sme matchovati (min_value=0)
        "snaga_min=99999999999",         # too large (max_value=10000)
        "cena_min=not-a-number",         # InvalidOperation Decimal parse
        "cena_max=-100",                 # negative cena
        "snaga_min=&snaga_max=",         # empty strings
    ],
)
def test_invalid_filter_values_silently_ignored(client, query_string):
    """AC2 + SM-D11: invalid filter query params su silently ignored — view vraća 200,
    NE 400. Vraća sve traktor product-e (filter nije primenjen).

    Rationale: filter URL je shareable; korisnik može copy-paste corrupt URL od kolege;
    bolje render-ovati sve nego pukti sa 400.
    """
    activate("sr")
    brand = BrandFactory.create()
    TractorProductFactory.create(brand=brand, name="Valid Tractor", horse_power=80, price_eur=Decimal("15000.00"))

    response = client.get(f"/sr/traktori/?{query_string}", HTTP_HOST="localhost")

    assert response.status_code == 200, (
        f"GET /sr/traktori/?{query_string} (invalid param) treba HTTP 200, "
        f"dobio {response.status_code}. SM-D11 — silent ignore."
    )
    # Sve traktor product-e su prisutni (filter nije primenjen jer invalid)
    products = list(response.context["products"])
    assert len(products) >= 1, (
        f"Invalid filter '{query_string}' NE SME redukovati queryset; "
        f"očekivano sve traktor product-e (>=1), dobio {len(products)}."
    )


# =============================================================================
# AC2 — Context surface: brands_for_header + active_filters + count
# =============================================================================


def test_context_brands_for_header_filters_not_coming_soon(client):
    """AC2 + SM-D5: context['brands_for_header'] filtruje is_coming_soon=False brendove,
    ordered by name.
    """
    activate("sr")
    live_brand_a = BrandFactory.create(name="Aaa Live Brand")
    live_brand_b = BrandFactory.create(name="Bbb Live Brand")
    coming_brand = BrandFactory.create_coming_soon(name="Ccc Coming Soon Brand")
    # Seed bar 1 traktor product da page render ne padne na 0 results
    TractorProductFactory.create(brand=live_brand_a, name="Tractor for Header Test")

    response = client.get("/sr/traktori/", HTTP_HOST="localhost")

    assert response.status_code == 200
    brands_ctx = list(response.context["brands_for_header"])
    brand_pks = [b.pk for b in brands_ctx]

    assert live_brand_a.pk in brand_pks, (
        f"Live brand A (pk={live_brand_a.pk}) MORA biti u brands_for_header. Dobili: {brand_pks!r}."
    )
    assert live_brand_b.pk in brand_pks, (
        f"Live brand B (pk={live_brand_b.pk}) MORA biti u brands_for_header. Dobili: {brand_pks!r}."
    )
    assert coming_brand.pk not in brand_pks, (
        f"Coming-soon brand (pk={coming_brand.pk}) NE SME biti u brands_for_header "
        f"(SM-D5 is_coming_soon=False filter). Dobili: {brand_pks!r}."
    )
    # Verify alphabetical order
    names = [b.name for b in brands_ctx]
    assert names == sorted(names), (
        f"brands_for_header MORA biti ordered by name (SM-D5), dobili: {names!r}."
    )


def test_context_active_filters_reflects_request_get(client):
    """AC2: context['active_filters'] je dict 4 string vrednosti reflectujući request.GET."""
    activate("sr")
    BrandFactory.create()  # za brand header

    response = client.get(
        "/sr/traktori/?snaga_min=60&snaga_max=120&cena_min=15000&cena_max=30000",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 200
    active = response.context["active_filters"]
    assert isinstance(active, dict), f"active_filters MORA biti dict, dobio {type(active).__name__}."
    assert active.get("snaga_min") == "60", f"active_filters['snaga_min'] MORA biti '60', dobio {active.get('snaga_min')!r}."
    assert active.get("snaga_max") == "120", f"active_filters['snaga_max'] MORA biti '120', dobio {active.get('snaga_max')!r}."
    assert active.get("cena_min") == "15000", f"active_filters['cena_min'] MORA biti '15000', dobio {active.get('cena_min')!r}."
    assert active.get("cena_max") == "30000", f"active_filters['cena_max'] MORA biti '30000', dobio {active.get('cena_max')!r}."


def test_context_active_filters_empty_strings_when_no_query_params(client):
    """AC2: context['active_filters'] vraća prazan string za ključeve koji nisu u request.GET."""
    activate("sr")
    BrandFactory.create()

    response = client.get("/sr/traktori/", HTTP_HOST="localhost")

    assert response.status_code == 200
    active = response.context["active_filters"]
    for key in ("snaga_min", "snaga_max", "cena_min", "cena_max"):
        assert active.get(key) == "", (
            f"active_filters['{key}'] MORA biti '' (prazan string) bez query params, "
            f"dobio {active.get(key)!r}."
        )


def test_context_count_reflects_filtered_queryset_total(client):
    """AC2: context['count'] je int total broj filtriranih rezultata across all pages
    (NIJE samo current page slice).

    Bitno za OOB aria-live message koji najavi „Pronađeno N modela" total.
    """
    activate("sr")
    brand = BrandFactory.create()
    # Kreiraj 3 traktora: 2 sa snaga_min=80 (matchuje filter), 1 ispod
    TractorProductFactory.create(brand=brand, name="A", horse_power=100)
    TractorProductFactory.create(brand=brand, name="B", horse_power=120)
    TractorProductFactory.create(brand=brand, name="C", horse_power=60)  # ne matchuje

    response = client.get("/sr/traktori/?snaga_min=80", HTTP_HOST="localhost")

    assert response.status_code == 200
    count = response.context.get("count")
    assert isinstance(count, int), f"context['count'] MORA biti int, dobio {type(count).__name__}: {count!r}."
    assert count == 2, (
        f"context['count'] MORA biti 2 (filter snaga_min=80 matchuje 2 od 3 product-a), "
        f"dobio {count}."
    )


# =============================================================================
# AC2 — HTMX vs full-page template branching (SM-D3 single-view)
# =============================================================================


def test_htmx_request_uses_partial_template(client):
    """AC2 + SM-D3: GET sa HX-Request: true header renderuje _results_grid.html partial,
    NE tractor_listing.html full page.

    Detekcija: response.content NE SME sadržati `<html` ili `<body` tag-ove
    (full page chrome) — partial je samo grid div + opciono OOB div.
    """
    activate("sr")
    brand = BrandFactory.create()
    TractorProductFactory.create(brand=brand, name="HTMX Test Tractor")

    response = client.get("/sr/traktori/", HTTP_HOST="localhost", HTTP_HX_REQUEST="true")

    assert response.status_code == 200
    html = response.content.decode("utf-8")

    # Partial NEMA full HTML chrome
    assert "<html" not in html.lower(), (
        "HTMX response (HX-Request: true) MORA biti partial — NEMA `<html` tag. "
        f"Found: response content starts with: {html[:200]!r}. "
        "Per SM-D3, view.get_template_names() MORA returning partial path za request.htmx=True."
    )
    assert "<body" not in html.lower(), (
        "HTMX response MORA biti partial — NEMA `<body` tag (full page chrome)."
    )


def test_non_htmx_request_uses_full_page_template(client):
    """AC2 + SM-D3: GET bez HX-Request header-a renderuje tractor_listing.html full page
    (base.html chrome — <html>, <body>, <main>).
    """
    activate("sr")
    brand = BrandFactory.create()
    TractorProductFactory.create(brand=brand, name="Full Page Test Tractor")

    response = client.get("/sr/traktori/", HTTP_HOST="localhost")

    assert response.status_code == 200
    html = response.content.decode("utf-8")

    assert "<html" in html.lower(), (
        "Non-HTMX response (bez HX-Request header-a) MORA biti full page — sadrži `<html` tag. "
        "Per SM-D3, view.get_template_names() MORA returning tractor_listing.html za request.htmx=False."
    )
    assert "<body" in html.lower(), (
        "Non-HTMX response MORA imati `<body>` tag (base.html chrome)."
    )
    assert "<main" in html.lower(), (
        "Non-HTMX response MORA imati `<main>` tag (base.html provider)."
    )
