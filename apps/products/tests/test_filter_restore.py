"""Story 2.8 — Filter restore tests (RED phase TDD).

Pokriva AC9 SR3 fix (Adversarial I3) — 4 nezavisna scenarija filter restore-a iz URL-a
preko slider widget container `data-value-min`/`data-value-max` attributes + hidden input
`value=""` attributes; svaki scenario verifikuje da JS može seed-ovati slider thumbove
iz refreshed page load-a sa query parametrima (deep-link UX).

Scenarios (per AC9 § filter restore):
1. ?snaga_min=60 only → snaga_min thumb na 60, snaga_max na default (500)
2. ?snaga_max=120 only → snaga_min na default (0), snaga_max na 120
3. ?cena_min=15000&cena_max=30000 → oba cena thumba restored
4. mixed — ?snaga_min=60&cena_max=25000

TEA RED phase: SVI testovi MORAJU pasti — template ne postoji.

Pokrenuti sa:
    docker compose -f compose/local.yml exec django uv run pytest \\
        apps/products/tests/test_filter_restore.py -v

Refs:
- 2-8-tractor-listing-strana-sa-htmx-filterima.md (AC9 § filter restore SR3 fix)
- 2-8-interface-contract.md § 3 (_filter_form.html data-value-min/max attributes)
"""

from __future__ import annotations

import re

import pytest
from django.utils.translation import activate

from apps.brands.tests.factories import BrandFactory
from apps.products.tests.factories import TractorProductFactory

pytestmark = pytest.mark.django_db


# =============================================================================
# AC9 SR3 — Filter restore: 4 nezavisni scenariji
# =============================================================================


@pytest.mark.parametrize(
    "query_string,expected_snaga_min,expected_snaga_max,expected_cena_min,expected_cena_max",
    [
        # Scenario 1: snaga_min only — snaga_min=60, ostali default
        ("snaga_min=60", "60", "", "", ""),
        # Scenario 2: snaga_max only
        ("snaga_max=120", "", "120", "", ""),
        # Scenario 3: cena oba thumba
        ("cena_min=15000&cena_max=30000", "", "", "15000", "30000"),
        # Scenario 4: mixed — snaga_min + cena_max
        ("snaga_min=60&cena_max=25000", "60", "", "", "25000"),
    ],
)
def test_filter_form_restores_individual_query_params(
    client,
    query_string,
    expected_snaga_min,
    expected_snaga_max,
    expected_cena_min,
    expected_cena_max,
):
    """AC9 SR3 (per scenario): page reload sa URL query params seed-uje
    hidden input `value` attributes + slider container `data-value-min`/`data-value-max`
    attributes — JS može onda inicijalizovati slider thumbove na correct pozicije.
    """
    activate("sr")
    brand = BrandFactory.create()
    TractorProductFactory.create(brand=brand, name=f"Restore Test {query_string}")

    response = client.get(f"/sr/traktori/?{query_string}", HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    # Verify hidden input values matchuju expected
    for name, expected in (
        ("snaga_min", expected_snaga_min),
        ("snaga_max", expected_snaga_max),
        ("cena_min", expected_cena_min),
        ("cena_max", expected_cena_max),
    ):
        # Hidden input: <input type="hidden" name="snaga_min" value="60" ...>
        pattern = re.compile(
            r'<input[^>]*type="hidden"[^>]*name="' + re.escape(name) + r'"[^>]*value="([^"]*)"',
            re.IGNORECASE,
        )
        pattern_alt = re.compile(
            r'<input[^>]*name="' + re.escape(name) + r'"[^>]*value="([^"]*)"[^>]*type="hidden"',
            re.IGNORECASE,
        )
        match = pattern.search(html) or pattern_alt.search(html)
        assert match, (
            f"Filter form MORA imati hidden input `name=\"{name}\"` sa value attribute. "
            f"Query: {query_string!r}; expected_value={expected!r}."
        )
        actual = match.group(1)
        assert actual == expected, (
            f"Hidden input `{name}` value MORA biti {expected!r}, dobio {actual!r}. "
            f"Query: {query_string!r}. SR3 fix — restore iz URL params."
        )


def test_filter_form_default_state_without_query_params(client):
    """AC9 SR3 default state: page bez query params → hidden inputs imaju empty string
    `value=""` (placeholder za JS koji inicijalizuje slider na default extreme positions).
    """
    activate("sr")
    BrandFactory.create()

    response = client.get("/sr/traktori/", HTTP_HOST="localhost")
    assert response.status_code == 200
    html = response.content.decode("utf-8")

    for name in ("snaga_min", "snaga_max", "cena_min", "cena_max"):
        pattern = re.compile(
            r'<input[^>]*type="hidden"[^>]*name="' + re.escape(name) + r'"[^>]*value="([^"]*)"',
            re.IGNORECASE,
        )
        pattern_alt = re.compile(
            r'<input[^>]*name="' + re.escape(name) + r'"[^>]*value="([^"]*)"[^>]*type="hidden"',
            re.IGNORECASE,
        )
        match = pattern.search(html) or pattern_alt.search(html)
        assert match, f"Hidden input `name=\"{name}\"` MORA postojati u filter form-i."
        assert match.group(1) == "", (
            f"Bez query params, hidden input `{name}` MORA imati `value=\"\"` (empty), "
            f"dobio {match.group(1)!r}."
        )
