"""Story 2.9 — Filter parsing tests (RED phase TDD).

Pokriva AC2 — SM-D11 defensive filter parsing (silent ignore za invalid input) +
SM-D11 IMP-3 normalization (invalid kategorija slug → active_filters reset to "") +
sort key fallback (sort whitelist enforcement per SM-D7) +
godina parser bounds (SM-D6 — bounds 1900-2100 šire od UI range 1990-current_year).

Test scope (~10 tests):
- Defensive parsing: 6 parametrized scenarija (cena_min=abc, godina_min=-100, etc.)
- Empty string handling: 1 test
- Invalid kategorija normalization: 1 test (IMP-3)
- Sort fallback: 1 test
- Active filters reflect request.GET: 1 test

Pokrenuti sa:
    docker compose -f compose/local.yml exec django uv run pytest \\
        apps/products/tests/test_used_machinery_filters.py -v

Refs:
- 2-9-used-machinery-listing-sa-filterima.md (AC2 + SM-D6/D7/D11)
- 2-9-interface-contract.md § 2 (active_filters IMP-3 normalization)
"""

from __future__ import annotations

import pytest
from django.utils.translation import activate

from apps.brands.tests.factories import BrandFactory
from apps.products.tests.factories import UsedProductFactory

pytestmark = pytest.mark.django_db


# =============================================================================
# AC2 — SM-D11 defensive parsing: invalid input silently ignored
# =============================================================================


@pytest.mark.parametrize(
    "query_string",
    [
        "cena_min=abc",                  # InvalidOperation Decimal parse
        "cena_max=-100",                 # negative
        "godina_min=not-a-number",       # ValueError int parse
        "godina_min=-100",               # below min_value=1900
        "godina_max=9999",               # above max_value=2100
        "cena_min=&cena_max=",           # empty strings
    ],
)
def test_ac2_invalid_filter_values_silently_ignored(client, query_string):
    """AC2 + SM-D11: invalid filter query params su silently ignored — view vraća 200,
    NIJE 400. Vraća sve USED proizvode (filter nije primenjen).

    Rationale: filter URL je shareable; korisnik može copy-paste corrupt URL od kolege;
    bolje render-ovati sve nego pukti sa 400.
    """
    activate("sr")
    brand = BrandFactory.create()
    UsedProductFactory.create(brand=brand, name=f"Valid Used {query_string[:20]}")

    response = client.get(f"/sr/mehanizacija/polovna/?{query_string}", HTTP_HOST="localhost")

    assert response.status_code == 200, (
        f"GET /sr/mehanizacija/polovna/?{query_string} (invalid param) treba HTTP 200, "
        f"dobio {response.status_code}. SM-D11 — silent ignore."
    )
    products = list(response.context["products"])
    assert len(products) >= 1, (
        f"Invalid filter '{query_string}' NE SME redukovati queryset; "
        f"očekivano sve USED product-e (>=1), dobio {len(products)}."
    )


# =============================================================================
# AC2 — Empty string handling
# =============================================================================


def test_ac2_empty_string_filter_values_treated_as_no_filter(client):
    """AC2 + SM-D11: prazne string vrednosti (`?kategorija=&brend=`) ne primenjuju filter,
    nego renderuju sve USED product-e.
    """
    activate("sr")
    brand = BrandFactory.create()
    UsedProductFactory.create(brand=brand, name="Empty Filter Test")

    response = client.get(
        "/sr/mehanizacija/polovna/?kategorija=&brend=&cena_min=&godina_max=",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 200
    products = list(response.context["products"])
    assert len(products) >= 1


# =============================================================================
# AC2 — Invalid kategorija slug normalization (SM-D11 IMP-3)
# =============================================================================


def test_ac2_invalid_kategorija_slug_resets_active_filter(client):
    """AC2 + SM-D11 IMP-3: ako URL-edit dolazi sa kategorija slug koji NIJE u
    mehanizacija dropdown listi (npr. traktor-only category ili nepostojeći slug),
    `active_filters['kategorija']` se silently normalize na "" da form-restore
    bude koherentan sa stvarnim dropdown setom.

    Bez normalizacije, dropdown bi prikazao „Sve kategorije" (default option) ali
    `active_filters` bi i dalje držao invalid slug — silent divergence.
    """
    activate("sr")
    BrandFactory.create()

    response = client.get(
        "/sr/mehanizacija/polovna/?kategorija=nepostojeci-slug-xyz",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 200
    active = response.context.get("active_filters")
    assert active is not None
    assert active.get("kategorija") == "", (
        f"Invalid kategorija slug MORA biti normalizovan na '' u active_filters "
        f"(SM-D11 IMP-3 form-restore koherencija). Dobio: {active.get('kategorija')!r}."
    )


def test_ac2_traktor_only_category_slug_resets_active_filter(client):
    """AC2 + SM-D11 IMP-3: kategorija slug koji ima is_for='traktori' (NIJE mehanizacija)
    se silently normalize na "" u active_filters.
    """
    activate("sr")
    BrandFactory.create()

    # Kreiraj traktori kategoriju
    from apps.brands.models import Category

    traktor_cat = Category.objects.create(
        slug="trakt-only-slug", name="Traktor Only", is_for="traktori"
    )

    response = client.get(
        f"/sr/mehanizacija/polovna/?kategorija={traktor_cat.slug}",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 200
    active = response.context.get("active_filters")
    assert active.get("kategorija") == "", (
        f"Traktori kategorija slug (is_for!='mehanizacija') MORA biti reset na '' "
        f"u active_filters. Dobio: {active.get('kategorija')!r}."
    )


# =============================================================================
# AC2 — Sort fallback (SM-D7 whitelist)
# =============================================================================


def test_ac2_invalid_sort_falls_back_to_default(client):
    """AC2 + SM-D7: ?sort=INVALID → context['selected_sort'] == 'default' (whitelist
    enforcement; not 400 error).
    """
    activate("sr")
    BrandFactory.create()

    response = client.get(
        "/sr/mehanizacija/polovna/?sort=KAKAVGOD_NEPOSTOJECI",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 200
    assert response.context.get("selected_sort") == "default", (
        f"Invalid sort key MORA fallback-ovati na 'default' "
        f"(SM-D7 whitelist). Dobio: {response.context.get('selected_sort')!r}."
    )


# =============================================================================
# AC2 — Active filters reflect request.GET
# =============================================================================


def test_ac2_active_filters_reflect_request_get_values(client):
    """AC2: active_filters dict vrednosti su raw string-ovi iz request.GET (za form restore)."""
    activate("sr")
    BrandFactory.create()

    response = client.get(
        "/sr/mehanizacija/polovna/?cena_min=5000&cena_max=30000&godina_min=2015&godina_max=2020",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 200
    active = response.context.get("active_filters")
    assert active.get("cena_min") == "5000"
    assert active.get("cena_max") == "30000"
    assert active.get("godina_min") == "2015"
    assert active.get("godina_max") == "2020"
