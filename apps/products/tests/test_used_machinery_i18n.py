"""Story 2.9 — i18n + plural completion tests (RED phase TDD).

Pokriva AC8 — i18n compliance: sva 3 locale (sr/hu/en) URL resolve + sr nplurals=3
plural completion za pluralized count message (REUSE iz Story 2.8 .po) + locale-aware
title/lead translation u response.

Test scope (~7 tests):
- Locale URL resolve: 3 testa (sr/hu/en — overlap sa view tests ali ovde parametrized)
- sr nplurals=3 plural completion: 3 testa (count=0, count=1, count=2)
- Locale-aware title in response: 1 test

Pokrenuti sa:
    docker compose -f compose/local.yml exec django uv run pytest \\
        apps/products/tests/test_used_machinery_i18n.py -v

Refs:
- 2-9-used-machinery-listing-sa-filterima.md (AC8 + Subtask 7 lokali)
- 2-9-interface-contract.md § 7 (Locale .po edits)
- project-context.md § HTMX response patterns (pluralized OOB count)
"""

from __future__ import annotations

import pytest
from django.utils.translation import activate

from apps.brands.tests.factories import BrandFactory
from apps.products.tests.factories import UsedProductFactory

pytestmark = pytest.mark.django_db


# =============================================================================
# AC8 — Locale URL resolve (sr/hu/en)
# =============================================================================


@pytest.mark.parametrize(
    "locale,expected_url",
    [
        ("sr", "/sr/mehanizacija/polovna/"),
        ("hu", "/hu/mehanizacija/polovna/"),
        ("en", "/en/mehanizacija/polovna/"),
    ],
)
def test_ac8_all_three_locales_resolve_used_machinery_list_url(client, locale, expected_url):
    """AC8: /<locale>/mehanizacija/polovna/ vraća HTTP 200 za sva 3 locale-a."""
    activate(locale)
    response = client.get(expected_url, HTTP_HOST="localhost")
    assert response.status_code == 200, (
        f"GET {expected_url} treba HTTP 200, dobio {response.status_code}. "
        f"URL pattern MORA biti UNUTAR i18n_patterns(...) bloka."
    )


# =============================================================================
# AC8 — sr nplurals=3 plural completion (REUSE iz Story 2.8 .po — SM-D15 BT fix)
# =============================================================================


def test_ac8_pluralized_count_message_singular_sr(client):
    """AC8 + SM-D15: OOB count za N=1 koristi sr singular „Pronađen 1 model." (msgstr[0])."""
    activate("sr")
    brand = BrandFactory.create()
    UsedProductFactory.create(brand=brand, name="Singular Test", price_eur=__import__("decimal").Decimal("5000.00"))

    # Use filter to ensure exactly 1 result
    response = client.get(
        "/sr/mehanizacija/polovna/?cena_min=4000&cena_max=6000",
        HTTP_HOST="localhost",
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert "Pronađen 1 model" in html, (
        "OOB count za N=1 MORA biti 'Pronađen 1 model.' (sr msgstr[0]). "
        f"Response sample: {html[-500:]!r}."
    )


def test_ac8_pluralized_count_message_few_sr(client):
    """AC8 + SM-D15: OOB count za N=2 koristi sr few „Pronađena 2 modela." (msgstr[1])."""
    activate("sr")
    from decimal import Decimal

    brand = BrandFactory.create()
    UsedProductFactory.create(brand=brand, name="Few A", price_eur=Decimal("5000.00"))
    UsedProductFactory.create(brand=brand, name="Few B", price_eur=Decimal("5000.00"))

    response = client.get(
        "/sr/mehanizacija/polovna/?cena_min=4000&cena_max=6000",
        HTTP_HOST="localhost",
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert "Pronađena 2 modela" in html, (
        "OOB count za N=2 MORA biti 'Pronađena 2 modela.' (sr msgstr[1]). "
        f"sr nplurals=3 plural completion is_complete? Vidi SM-D15. "
        f"Response sample: {html[-500:]!r}."
    )


def test_ac8_pluralized_count_message_zero_uses_other_sr(client):
    """AC8 + SM-D15: OOB count za N=0 koristi sr other „Pronađeno 0 modela." (msgstr[2])."""
    activate("sr")
    BrandFactory.create()
    # 0 USED proizvoda

    response = client.get(
        "/sr/mehanizacija/polovna/",
        HTTP_HOST="localhost",
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert "Pronađeno 0 modela" in html, (
        "OOB count za N=0 MORA biti 'Pronađeno 0 modela.' (sr msgstr[2]). "
        f"Response sample: {html[-500:]!r}."
    )


# =============================================================================
# AC8 — Locale-aware title (sr default)
# =============================================================================


def test_ac8_sr_locale_page_title_is_polovna_mehanizacija(client):
    """AC8: sr locale renderuje page title „Polovna mehanizacija" sa punim dijakriticima."""
    activate("sr")
    BrandFactory.create()
    UsedProductFactory.create(name="Title Test")

    response = client.get("/sr/mehanizacija/polovna/", HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    assert "Polovna mehanizacija" in html, (
        "sr locale MORA renderovati h1/title „Polovna mehanizacija\" "
        "(pune dijakritike — anti-pattern šišana latinica)."
    )
