"""Story 2.9 — UsedMachineryListView tests (RED phase TDD).

Pokriva AC1 (URL routing + URL deconfliction + query budget + Vary header) + AC2 (CBV
ListView — queryset filter condition='used' scope + SM-D11 defensive filter parsing +
SM-D7 sort whitelist + SM-D25 pagination overflow + context surface; HTMX vs full-page
template branching kroz get_template_names() per SM-D3).

Test scope (~22 tests):
- AC1 URL routing: 3 testa (sr/hu/en locale resolve)
- AC1 URL deconfliction (SM-D1): 3 testa (no shadow za tractor_list, brands:detail, products:detail)
- AC1 query budget: 1 test (placeholder per SM-D27 — Dev locks empirically)
- AC1 Vary header (SM-D21): 1 test
- AC2 queryset scope: 3 testa (condition='used', is_published=True, traktori scope excluded)
- AC2 filter application: 4 testa (kategorija, brend, cena, godina)
- AC2 sort application: 2 testa (cena_asc, godina_desc)
- AC2 sort whitelist fallback (SM-D7): 1 test
- AC2 pagination overflow safety (SM-D25): 1 test
- AC2 context surface: 3 testa (categories, brands, active_filters, year range constants, count)

Pokrenuti sa:
    docker compose -f compose/local.yml exec django uv run pytest \\
        apps/products/tests/test_used_machinery_view.py -v

Refs:
- 2-9-used-machinery-listing-sa-filterima.md (AC1 + AC2 + SM-D1/D2/D3/D5/D6/D7/D8/D11/D21/D25/D27)
- 2-9-interface-contract.md § 2 + § 9
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.urls import NoReverseMatch, reverse
from django.utils.translation import activate

from apps.brands.tests.factories import BrandFactory
from apps.products.tests.factories import (
    ProductFactory,
    TractorProductFactory,
    UsedProductFactory,
)

pytestmark = pytest.mark.django_db


# =============================================================================
# AC1 — URL routing (i18n_patterns: sr/hu/en)
# =============================================================================


def test_ac1_used_machinery_list_url_resolves_for_sr_locale(client):
    """AC1: /sr/mehanizacija/polovna/ vraća HTTP 200 (UsedMachineryListView)."""
    activate("sr")
    response = client.get("/sr/mehanizacija/polovna/", HTTP_HOST="localhost")
    assert response.status_code == 200, (
        f"GET /sr/mehanizacija/polovna/ treba HTTP 200, dobio {response.status_code}. "
        "Dev mora dodati UsedMachineryListView + path('mehanizacija/polovna/', ...) u apps/products/urls.py."
    )


def test_ac1_used_machinery_list_url_resolves_for_hu_locale(client):
    """AC1: /hu/mehanizacija/polovna/ vraća HTTP 200 (i18n_patterns multi-locale)."""
    activate("hu")
    response = client.get("/hu/mehanizacija/polovna/", HTTP_HOST="localhost")
    assert response.status_code == 200, (
        f"GET /hu/mehanizacija/polovna/ treba HTTP 200, dobio {response.status_code}. "
        "URL pattern MORA biti UNUTAR i18n_patterns(...) blok-a u config/urls.py."
    )


def test_ac1_used_machinery_list_url_resolves_for_en_locale(client):
    """AC1: /en/mehanizacija/polovna/ vraća HTTP 200."""
    activate("en")
    response = client.get("/en/mehanizacija/polovna/", HTTP_HOST="localhost")
    assert response.status_code == 200


def test_ac1_used_machinery_list_reverse_resolves_to_sr_url():
    """AC1: reverse('products:used_machinery_list') vraća '/sr/mehanizacija/polovna/' u sr locale-u."""
    activate("sr")
    try:
        url = reverse("products:used_machinery_list")
    except NoReverseMatch:
        pytest.fail(
            "URL name 'products:used_machinery_list' nije registrovan. "
            "Dev mora dodati path('mehanizacija/polovna/', views.UsedMachineryListView.as_view(), "
            "name='used_machinery_list') u apps/products/urls.py."
        )
    assert url == "/sr/mehanizacija/polovna/", (
        f"reverse('products:used_machinery_list') u sr locale-u mora vratiti "
        f"'/sr/mehanizacija/polovna/', dobio {url!r}."
    )


# =============================================================================
# AC1 — URL deconfliction (SM-D1): no shadow Story 2.6/2.7/2.8 patterns
# =============================================================================


def test_ac1_used_url_does_not_shadow_tractor_list_url(client):
    """AC1 + SM-D1: novi pattern `mehanizacija/polovna/` NE SME shadow-ovati Story 2.8
    `traktori/` URL (TractorListView).
    """
    activate("sr")
    BrandFactory.create()
    TractorProductFactory.create(name="Coexist Test")
    response = client.get("/sr/traktori/", HTTP_HOST="localhost")
    assert response.status_code == 200, (
        f"Story 2.8 /sr/traktori/ MORA i dalje vraćati HTTP 200 posle Story 2.9 dodavanja "
        f"mehanizacija/polovna/ pattern-a (SM-D1 deconfliction), dobio {response.status_code}."
    )


def test_ac1_used_url_does_not_shadow_brand_detail_url(client):
    """AC1 + SM-D1: novi pattern `mehanizacija/polovna/` NE SME shadow-ovati Story 2.6
    `traktori/<slug>/` URL (BrandDetailView).
    """
    activate("sr")
    brand = BrandFactory.create(name="Some Brand")
    url = f"/sr/traktori/{brand.slug}/"
    response = client.get(url, HTTP_HOST="localhost")
    assert response.status_code == 200, (
        f"Story 2.6 brands:detail ({url}) MORA i dalje vraćati HTTP 200, "
        f"dobio {response.status_code}. SM-D1 — Story 2.9 ne sme shadow-ovati."
    )


def test_ac1_used_url_does_not_shadow_product_detail_url(client):
    """AC1 + SM-D1: novi pattern `mehanizacija/polovna/` NE SME shadow-ovati Story 2.7
    `proizvod/<slug>/` URL (ProductDetailView).
    """
    activate("sr")
    product = ProductFactory.create(name="Shadow Test Product")
    url = f"/sr/proizvod/{product.slug}/"
    response = client.get(url, HTTP_HOST="localhost")
    assert response.status_code == 200, (
        f"Story 2.7 products:detail ({url}) MORA i dalje vraćati HTTP 200, "
        f"dobio {response.status_code}."
    )


def test_ac1_all_three_distinct_urls_coexist():
    """AC1 + SM-D1 smoke: reverse all 3 affected URL names; svi imaju distinct URL-ove."""
    activate("sr")
    try:
        used_url = reverse("products:used_machinery_list")
        tractor_url = reverse("products:tractor_list")
        brand_detail_url = reverse("brands:detail", kwargs={"slug": "agri-tracking"})
    except NoReverseMatch as exc:
        pytest.fail(
            f"URL reverse fail-ovao: {exc}. Sva 3 URL imena MORAJU biti registrovana "
            "(Story 2.6 brands:detail + Story 2.8 products:tractor_list + Story 2.9 "
            "products:used_machinery_list)."
        )
    distinct = {used_url, tractor_url, brand_detail_url}
    assert len(distinct) == 3, (
        f"Sva 3 URL-a MORAJU biti distinct. Dobio: used={used_url!r}, "
        f"tractor={tractor_url!r}, brand_detail={brand_detail_url!r}."
    )


# =============================================================================
# AC1 — Vary: HX-Request header (SM-D21 cache poisoning defense)
# =============================================================================


def test_ac1_vary_hx_request_header_present_on_dispatch(client):
    """AC1 + SM-D21 (cache poisoning defense): response MORA imati `Vary: HX-Request`
    header (kroz @method_decorator(vary_on_headers('HX-Request'), name='dispatch') dekorator
    na UsedMachineryListView klasu).

    Bez Vary headera, CDN ili browser cache može serve-ovati full-page response na
    HTMX request (broken in-place swap) ili obrnuto.
    """
    activate("sr")
    response = client.get("/sr/mehanizacija/polovna/", HTTP_HOST="localhost")
    assert response.status_code == 200
    vary_header = response.headers.get("Vary", "")
    assert "HX-Request" in vary_header, (
        f"Response MORA imati `Vary: HX-Request` u header-u (SM-D21 cache poisoning defense). "
        f"Dobio Vary={vary_header!r}. Dev MORA dodati @method_decorator(vary_on_headers('HX-Request'), "
        "name='dispatch') iznad UsedMachineryListView klase."
    )


# =============================================================================
# AC1 — Query budget (TEA placeholder per SM-D27 — Dev locks empirically posle GREEN iter 1)
# =============================================================================


def test_ac1_assertNumQueries_initial_render_under_budget(client, django_assert_num_queries):
    """AC1 + SM-D27: query budget placeholder.

    TEA placeholder `assertNumQueries(5)` SPECULATION (1 categories dropdown + 1 brands
    dropdown + 1 Product COUNT + 1 Product slice + 1 middleware overhead).
    Dev MORA empirijski lock-ovati posle prvog GREEN runa per SM-D27 — tail-up za
    LocaleMiddleware + session/auth middleware je očekivano.
    """
    activate("sr")
    brand = BrandFactory.create(name="Query Budget Brand")
    for i in range(5):
        UsedProductFactory.create(brand=brand, name=f"Used {i}", price_eur=Decimal(f"{1000 * (i + 1)}.00"))

    # SM-D27 — Dev empirically locked posle GREEN iter 1: actual = 4 queries
    # (1 categories dropdown + 1 brands dropdown + 1 Product COUNT + 1 Product slice)
    # NO middleware overhead in test runs — Django test client bypasses some middleware.
    # Story 3.4: 4 view upita + 1 SiteSettings chrome upit (header/footer site_setting, 1/request).
    with django_assert_num_queries(5):
        response = client.get("/sr/mehanizacija/polovna/", HTTP_HOST="localhost")
        assert response.status_code == 200


# =============================================================================
# AC2 — Queryset scope: condition='used' + is_published=True (SM-D2)
# =============================================================================


def test_ac2_get_queryset_filters_by_condition_used(client):
    """AC2 + SM-D2: queryset uključuje SAMO condition='used' proizvode; NEW proizvodi
    su excluded (zaštita scope-a).
    """
    activate("sr")
    brand = BrandFactory.create()
    used_product = UsedProductFactory.create(brand=brand, name="Used Tractor")
    # ProductFactory default je condition=NEW; ali subcategory=None pa ne match-uje
    # nijedan listing — eksplicitno postavi mehanizacija subcategory ali condition=NEW
    new_product_in_scope = UsedProductFactory.create(
        brand=brand, name="New in Scope", condition="new"
    )

    response = client.get("/sr/mehanizacija/polovna/", HTTP_HOST="localhost")

    assert response.status_code == 200
    product_pks = [p.pk for p in response.context["products"]]
    assert used_product.pk in product_pks, (
        f"USED product (pk={used_product.pk}) MORA biti u queryset-u. Dobili: {product_pks!r}."
    )
    assert new_product_in_scope.pk not in product_pks, (
        f"NEW product (pk={new_product_in_scope.pk}) NE SME biti u listing-u "
        f"(condition='used' hardcoded scope per SM-D2). Dobili: {product_pks!r}."
    )


def test_ac2_get_queryset_excludes_unpublished_products(client):
    """AC2: queryset filtruje is_published=True; unpublished USED proizvodi su skriveni."""
    activate("sr")
    brand = BrandFactory.create()
    pub = UsedProductFactory.create(brand=brand, name="Published Used")
    unpub = UsedProductFactory.create_unpublished(brand=brand, name="Unpublished Used")

    response = client.get("/sr/mehanizacija/polovna/", HTTP_HOST="localhost")

    assert response.status_code == 200
    product_pks = [p.pk for p in response.context["products"]]
    assert pub.pk in product_pks, (
        f"Published USED product (pk={pub.pk}) MORA biti u listing-u. Dobili: {product_pks!r}."
    )
    assert unpub.pk not in product_pks, (
        f"Unpublished USED product (pk={unpub.pk}) NE SME biti u listing-u "
        f"(is_published=True filter). Dobili: {product_pks!r}."
    )


def test_ac2_get_queryset_includes_used_regardless_of_subcategory_scope(client):
    """AC2 + SM-D2: condition='used' scope je SAMOSTALAN — NIJE vezan za traktori vs
    mehanizacija (used traktor je takođe valid USED product).

    NAPOMENA: razlika od Story 2.8 koja filtruje subcategory__category__is_for='traktori'.
    Story 2.9 filtruje SAMO condition='used' — bilo koja subcategory (ili nijedna) je OK.
    """
    activate("sr")
    brand = BrandFactory.create()
    # USED u mehanizacija scope-u
    used_mech = UsedProductFactory.create(brand=brand, name="Used Mech")
    # USED bez subcategory (defensive — ProductFactory default subcategory=None)
    from apps.products.models import Product

    used_no_subcat = ProductFactory.create(
        brand=brand,
        name="Used No Subcat",
        condition=Product.ConditionChoice.USED,
    )

    response = client.get("/sr/mehanizacija/polovna/", HTTP_HOST="localhost")
    assert response.status_code == 200
    product_pks = [p.pk for p in response.context["products"]]

    assert used_mech.pk in product_pks
    assert used_no_subcat.pk in product_pks, (
        f"USED product BEZ subcategory (pk={used_no_subcat.pk}) MORA biti u listing-u "
        "(Story 2.9 condition='used' scope je samostalan, NIJE vezan za subcategory). "
        f"Dobili: {product_pks!r}."
    )


# =============================================================================
# AC2 — Filter application: kategorija, brend, cena, godina
# =============================================================================


def test_ac2_get_queryset_applies_kategorija_filter(client):
    """AC2: ?kategorija=<slug> filtruje po subcategory__category__slug + is_for='mehanizacija'."""
    activate("sr")
    brand = BrandFactory.create()
    plugovi_product = UsedProductFactory.create_in_category(
        brand=brand, category_slug="plugovi", category_name="Plugovi", name="Plug 1"
    )
    other_product = UsedProductFactory.create_in_category(
        brand=brand, category_slug="grablje", category_name="Grablje", name="Grablje 1"
    )

    response = client.get("/sr/mehanizacija/polovna/?kategorija=plugovi", HTTP_HOST="localhost")

    assert response.status_code == 200
    product_pks = [p.pk for p in response.context["products"]]
    assert plugovi_product.pk in product_pks, (
        f"Plug product MORA biti sa ?kategorija=plugovi. Dobili: {product_pks!r}."
    )
    assert other_product.pk not in product_pks, (
        f"Grablje product NE SME biti sa ?kategorija=plugovi. Dobili: {product_pks!r}."
    )


def test_ac2_get_queryset_applies_brend_filter(client):
    """AC2: ?brend=<slug> filtruje po brand__slug."""
    activate("sr")
    target_brand = BrandFactory.create(name="JeegeeBrand")
    other_brand = BrandFactory.create(name="OtherBrand")
    target_product = UsedProductFactory.create(brand=target_brand, name="Jeegee Used")
    other_product = UsedProductFactory.create(brand=other_brand, name="Other Used")

    response = client.get(
        f"/sr/mehanizacija/polovna/?brend={target_brand.slug}",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 200
    product_pks = [p.pk for p in response.context["products"]]
    assert target_product.pk in product_pks
    assert other_product.pk not in product_pks, (
        f"Other brand product NE SME biti sa ?brend={target_brand.slug!r}. Dobili: {product_pks!r}."
    )


def test_ac2_get_queryset_applies_cena_range_filter(client):
    """AC2: ?cena_min=5000&cena_max=20000 primenuje gte+lte na price_eur."""
    activate("sr")
    brand = BrandFactory.create()
    cheap = UsedProductFactory.create(brand=brand, name="Cheap", price_eur=Decimal("3000.00"))
    mid = UsedProductFactory.create(brand=brand, name="Mid", price_eur=Decimal("10000.00"))
    expensive = UsedProductFactory.create(brand=brand, name="Expensive", price_eur=Decimal("50000.00"))

    response = client.get(
        "/sr/mehanizacija/polovna/?cena_min=5000&cena_max=20000",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 200
    product_pks = [p.pk for p in response.context["products"]]
    assert mid.pk in product_pks
    assert cheap.pk not in product_pks, (
        f"price=3000 NE SME biti sa cena_min=5000. Dobili: {product_pks!r}."
    )
    assert expensive.pk not in product_pks, (
        f"price=50000 NE SME biti sa cena_max=20000. Dobili: {product_pks!r}."
    )


def test_ac2_get_queryset_applies_godina_range_filter(client):
    """AC2: ?godina_min=2015&godina_max=2020 primenuje gte+lte na year."""
    activate("sr")
    brand = BrandFactory.create()
    old = UsedProductFactory.create(brand=brand, name="Old", year=2010)
    recent = UsedProductFactory.create(brand=brand, name="Recent", year=2018)
    very_new = UsedProductFactory.create(brand=brand, name="Very New", year=2024)

    response = client.get(
        "/sr/mehanizacija/polovna/?godina_min=2015&godina_max=2020",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 200
    product_pks = [p.pk for p in response.context["products"]]
    assert recent.pk in product_pks
    assert old.pk not in product_pks, (
        f"year=2010 NE SME biti sa godina_min=2015. Dobili: {product_pks!r}."
    )
    assert very_new.pk not in product_pks, (
        f"year=2024 NE SME biti sa godina_max=2020. Dobili: {product_pks!r}."
    )


# =============================================================================
# AC2 — Sort whitelist application (SM-D7)
# =============================================================================


def test_ac2_get_queryset_applies_sort_cena_asc(client):
    """AC2 + SM-D7: ?sort=cena_asc daje queryset ordered by price_eur ASC."""
    activate("sr")
    brand = BrandFactory.create()
    cheap = UsedProductFactory.create(brand=brand, name="A Cheap", price_eur=Decimal("1000.00"))
    expensive = UsedProductFactory.create(brand=brand, name="B Expensive", price_eur=Decimal("9999.00"))
    mid = UsedProductFactory.create(brand=brand, name="C Mid", price_eur=Decimal("5000.00"))

    response = client.get("/sr/mehanizacija/polovna/?sort=cena_asc", HTTP_HOST="localhost")

    assert response.status_code == 200
    products = list(response.context["products"])
    # Order MORA biti: cheap (1000), mid (5000), expensive (9999)
    assert products[0].pk == cheap.pk, (
        f"Sa ?sort=cena_asc, prvi MORA biti cheap (price=1000). Dobio: "
        f"{[(p.name, p.price_eur) for p in products]}."
    )
    assert products[-1].pk == expensive.pk, (
        f"Sa ?sort=cena_asc, poslednji MORA biti expensive (price=9999). Dobio: "
        f"{[(p.name, p.price_eur) for p in products]}."
    )


def test_ac2_get_queryset_applies_sort_godina_desc(client):
    """AC2 + SM-D7: ?sort=godina_desc daje queryset ordered by year DESC (najnoviji prvi)."""
    activate("sr")
    brand = BrandFactory.create()
    UsedProductFactory.create(brand=brand, name="A 2010", year=2010)
    UsedProductFactory.create(brand=brand, name="B 2022", year=2022)
    UsedProductFactory.create(brand=brand, name="C 2018", year=2018)

    response = client.get("/sr/mehanizacija/polovna/?sort=godina_desc", HTTP_HOST="localhost")

    assert response.status_code == 200
    products = list(response.context["products"])
    years = [p.year for p in products]
    assert years == sorted(years, reverse=True), (
        f"Sa ?sort=godina_desc, year-i MORAJU biti DESC sortirani. Dobio: {years!r}."
    )


# =============================================================================
# AC2 — Pagination overflow safety (SM-D25)
# =============================================================================


def test_ac2_pagination_out_of_range_page_clamps_to_last_page(client):
    """AC2 + SM-D25: GET ?page=999 (van opsega) MORA vratiti HTTP 200 sa poslednjom
    stranom — NIJE 404 EmptyPage. Verifies paginate_queryset koristi Paginator.get_page().

    Setup: 15 USED proizvoda + paginate_by=12 → 2 strane (12+3). page=999 MORA clampovati
    na page 2 (poslednja).
    """
    activate("sr")
    brand = BrandFactory.create()
    for i in range(15):
        UsedProductFactory.create(brand=brand, name=f"Used {i}")

    response = client.get("/sr/mehanizacija/polovna/?page=999", HTTP_HOST="localhost")

    assert response.status_code == 200, (
        f"GET ?page=999 (overflow) MORA vraćati 200 (Paginator.get_page() clamps). "
        f"Dobio {response.status_code}. Dev mora override-ovati paginate_queryset() per SM-D25."
    )
    page_obj = response.context.get("page_obj")
    assert page_obj is not None, "page_obj MORA biti u context-u (ListView default)."
    paginator = response.context.get("paginator")
    assert page_obj.number == paginator.num_pages, (
        f"Overflow page=999 MORA clampovati na last page ({paginator.num_pages}), "
        f"dobio page_obj.number={page_obj.number}."
    )


# =============================================================================
# AC2 — Context surface: categories_for_dropdown + brands_for_dropdown + count + year range
# =============================================================================


def test_ac2_get_context_data_includes_categories_for_dropdown(client):
    """AC2: context['categories_for_dropdown'] filtruje is_for='mehanizacija' kategorije,
    ordered by display_order, name.
    """
    activate("sr")
    BrandFactory.create()
    # Kreiraj 1 mehanizacija + 1 traktori kategoriju
    from apps.brands.models import Category

    mech_cat = Category.objects.create(
        slug="kat-mech", name="Mech Cat", is_for="mehanizacija", display_order=1
    )
    trakt_cat = Category.objects.create(
        slug="kat-trakt", name="Trakt Cat", is_for="traktori", display_order=0
    )

    response = client.get("/sr/mehanizacija/polovna/", HTTP_HOST="localhost")
    assert response.status_code == 200

    categories = list(response.context["categories_for_dropdown"])
    category_pks = [c.pk for c in categories]
    assert mech_cat.pk in category_pks, (
        f"Mehanizacija category MORA biti u dropdown-u. Dobili: {category_pks!r}."
    )
    assert trakt_cat.pk not in category_pks, (
        f"Traktori category NE SME biti u mehanizacija dropdown-u "
        f"(is_for='mehanizacija' filter). Dobili: {category_pks!r}."
    )


def test_ac2_get_context_data_includes_brands_for_dropdown(client):
    """AC2 + SM-D5: context['brands_for_dropdown'] filtruje is_coming_soon=False brendove,
    ordered by name.
    """
    activate("sr")
    live = BrandFactory.create(name="Live Brand X")
    coming = BrandFactory.create_coming_soon(name="Coming Brand Y")

    response = client.get("/sr/mehanizacija/polovna/", HTTP_HOST="localhost")
    assert response.status_code == 200

    brand_pks = [b.pk for b in response.context["brands_for_dropdown"]]
    assert live.pk in brand_pks
    assert coming.pk not in brand_pks, (
        f"Coming-soon brand NE SME biti u dropdown-u (SM-D5). Dobili: {brand_pks!r}."
    )


def test_ac2_get_context_data_active_filters_dict_keys(client):
    """AC2: context['active_filters'] je dict sa 7 ključeva: kategorija, brend, cena_min,
    cena_max, godina_min, godina_max, stanje.
    """
    activate("sr")
    BrandFactory.create()
    response = client.get("/sr/mehanizacija/polovna/", HTTP_HOST="localhost")
    assert response.status_code == 200

    active = response.context.get("active_filters")
    assert isinstance(active, dict), f"active_filters MORA biti dict, dobio {type(active).__name__}."
    expected_keys = {"kategorija", "brend", "cena_min", "cena_max", "godina_min", "godina_max", "stanje"}
    assert set(active.keys()) == expected_keys, (
        f"active_filters MORA imati TAČNO 7 ključeva: {expected_keys!r}. Dobio: {set(active.keys())!r}."
    )
    assert active["stanje"] == "used", (
        f"active_filters['stanje'] MORA default-ovati na 'used' (SM-D2 hardlock), "
        f"dobio {active['stanje']!r}."
    )


def test_ac2_get_context_data_count_matches_paginator_count(client):
    """AC2: context['count'] je int i match-uje paginator.count (NIJE recomputed sa
    dodatnim SQL upitom).
    """
    activate("sr")
    brand = BrandFactory.create()
    for i in range(8):
        UsedProductFactory.create(brand=brand, name=f"Count Test {i}")

    response = client.get("/sr/mehanizacija/polovna/", HTTP_HOST="localhost")
    assert response.status_code == 200

    count = response.context.get("count")
    paginator = response.context.get("paginator")
    assert isinstance(count, int)
    assert count == 8
    assert paginator is not None
    assert count == paginator.count, (
        f"context['count'] MORA biti == paginator.count (no double-count SQL). "
        f"Dobili count={count}, paginator.count={paginator.count}."
    )


def test_ac2_get_context_data_year_range_constants(client):
    """AC2 + SM-D6: context['year_min_range'] == 1990, context['year_max_range'] ==
    current year (timezone.now().year).

    NAPOMENA: SM-D6 lock je 1990 (FIX iter-1 — bila 1900 greška u early draft-u).
    Parser bounds (1900-2100) su NAMERNO šire za URL-edit resilience.
    """
    activate("sr")
    BrandFactory.create()
    response = client.get("/sr/mehanizacija/polovna/", HTTP_HOST="localhost")
    assert response.status_code == 200

    year_min = response.context.get("year_min_range")
    year_max = response.context.get("year_max_range")
    assert year_min == 1990, (
        f"year_min_range MORA biti 1990 (SM-D6 lock), dobio {year_min!r}."
    )
    from django.utils import timezone

    current_year = timezone.now().year
    assert year_max == current_year, (
        f"year_max_range MORA biti current year ({current_year}), dobio {year_max!r}. "
        "Dev MORA koristiti timezone.now().year (NE datetime.now() — naive datetime anti-pattern)."
    )


def test_ac2_get_context_data_sort_options_has_4_entries(client):
    """AC2 + SM-D7: context['sort_options'] je list sa TAČNO 4 (key, label) tuple-ova
    (default, cena_asc, cena_desc, godina_desc) per epics.md FR-13.
    """
    activate("sr")
    BrandFactory.create()
    response = client.get("/sr/mehanizacija/polovna/", HTTP_HOST="localhost")
    assert response.status_code == 200

    sort_options = response.context.get("sort_options")
    assert isinstance(sort_options, list), (
        f"sort_options MORA biti list, dobio {type(sort_options).__name__}."
    )
    assert len(sort_options) == 4, (
        f"sort_options MORA imati TAČNO 4 entries, dobio {len(sort_options)}."
    )
    keys = [k for (k, _label) in sort_options]
    expected_keys = ["default", "cena_asc", "cena_desc", "godina_desc"]
    assert keys == expected_keys, (
        f"sort_options keys MORAJU biti {expected_keys!r} u TAČNOM redosledu, "
        f"dobio {keys!r}."
    )


def test_ac2_get_context_data_selected_sort_defaults_to_default(client):
    """AC2: bez ?sort=, context['selected_sort'] == 'default'."""
    activate("sr")
    BrandFactory.create()
    response = client.get("/sr/mehanizacija/polovna/", HTTP_HOST="localhost")
    assert response.status_code == 200
    assert response.context.get("selected_sort") == "default"


def test_ac2_default_sort_orders_by_created_at_desc(client):
    """AC2 + SM-D7: bez ?sort= queryset MORA biti ordered by `-created_at` (newest-first).

    Highest-traffic path (default landing page) — positive ordering assertion (NIJE samo
    context selected_sort=='default' check). `_USED_SORT_OPTIONS['default'] = '-created_at'`
    iz apps/products/views.py linija 40.

    Setup: 3 USED proizvoda sa `created_at` overrides (auto_now_add zaobiđen kroz
    `.update()` POSLE create-a). Default GET MORA vratiti newest → oldest order.
    """
    from datetime import timedelta

    from django.utils import timezone

    from apps.products.models import Product

    activate("sr")
    brand = BrandFactory.create()

    now = timezone.now()
    oldest = UsedProductFactory.create(brand=brand, name="Oldest Used")
    middle = UsedProductFactory.create(brand=brand, name="Middle Used")
    newest = UsedProductFactory.create(brand=brand, name="Newest Used")

    # Override `created_at` (auto_now_add ne dozvoljava override pri create-u — koristi
    # `Manager.filter(pk=...).update()` koji bypassuje auto_now_add)
    Product.objects.filter(pk=oldest.pk).update(created_at=now - timedelta(days=6))
    Product.objects.filter(pk=middle.pk).update(created_at=now - timedelta(days=3))
    Product.objects.filter(pk=newest.pk).update(created_at=now)

    response = client.get("/sr/mehanizacija/polovna/", HTTP_HOST="localhost")

    assert response.status_code == 200
    products = list(response.context["products"])
    pks_in_order = [p.pk for p in products]
    assert pks_in_order == [newest.pk, middle.pk, oldest.pk], (
        f"Bez ?sort= (default sort = '-created_at'), products MORAJU biti ordered "
        f"newest → oldest. Očekivano [newest, middle, oldest], dobio: "
        f"{[(p.name, p.created_at) for p in products]}."
    )
