"""Story 2.10 — JeegeePrikljucnaView URL routing tests (RED phase TDD).

Pokriva AC1 (URL routing) — sr/hu/en locale resolve + no-shadow regression guard.

Test scope (4 tests):
- test_jeegee_prikljucna_url_resolves_sr_locale
- test_jeegee_prikljucna_url_resolves_hu_locale
- test_jeegee_prikljucna_url_resolves_en_locale
- test_jeegee_prikljucna_url_no_collision_with_existing_patterns

TEA RED phase: SVI testovi MORAJU pasti dok Dev ne implementira JeegeePrikljucnaView
+ apps/brands/urls.py path + 0003 seed migracija.

Pokrenuti sa:
    docker compose -f compose/local.yml exec django pytest \\
        apps/brands/tests/test_jeegee_prikljucna_urls.py -v

Refs:
- 2-10-jeegee-prikljucna-mehanizacija-strana.md (AC1)
- 2-10-interface-contract.md (§ 2 URL patterns)
"""

from __future__ import annotations

import pytest
from django.urls import reverse
from django.utils.translation import activate

pytestmark = pytest.mark.django_db


def test_jeegee_prikljucna_url_resolves_sr_locale(client):
    """AC1: /sr/mehanizacija/prikljucna/ vraća HTTP 200 (Jeegee Brand seed kroz 0003 migraciju)."""
    activate("sr")
    url = "/sr/mehanizacija/prikljucna/"

    response = client.get(url)

    assert response.status_code == 200, (
        f"GET {url} treba HTTP 200 (Jeegee Brand seed-ovan kroz migration 0003), "
        f"dobio {response.status_code}. Dev mora: (a) kreirati JeegeePrikljucnaView u "
        f"apps/brands/views.py, (b) dodati URL pattern u apps/brands/urls.py, "
        f"(c) kreirati data migraciju 0003_seed_jeegee_and_prikljucna_categories.py."
    )


def test_jeegee_prikljucna_url_resolves_hu_locale(client):
    """AC1: /hu/mehanizacija/prikljucna/ vraća HTTP 200 (i18n_patterns)."""
    activate("hu")
    url = "/hu/mehanizacija/prikljucna/"

    response = client.get(url)

    assert response.status_code == 200, (
        f"GET {url} treba HTTP 200 (i18n_patterns multi-locale), dobio "
        f"{response.status_code}. URL pattern MORA biti registrovan UNUTAR i18n_patterns "
        f"blok-a u config/urls.py (Story 2-6 wiring već postoji)."
    )


def test_jeegee_prikljucna_url_resolves_en_locale(client):
    """AC1: /en/mehanizacija/prikljucna/ vraća HTTP 200."""
    activate("en")
    url = "/en/mehanizacija/prikljucna/"

    response = client.get(url)

    assert response.status_code == 200, (
        f"GET {url} treba HTTP 200, dobio {response.status_code}."
    )


def test_jeegee_prikljucna_url_no_collision_with_existing_patterns(client):
    """AC1: novi URL ne shadow-uje Story 2-6/2-7/2-8/2-9 pattern-e.

    Regression guard — verifikuje:
    - URL name 'brands:jeegee_prikljucna' reverse-uje na /sr/mehanizacija/prikljucna/
    - 'brands:detail' reverse-uje na /sr/traktori/<slug>/ (Story 2-6 NETAKNUT)
    - 'products:used_machinery_list' reverse-uje na /sr/mehanizacija/polovna/ (Story 2-9 NETAKNUT)
    - 'products:tractor_list' reverse-uje na /sr/traktori/ (Story 2-8 NETAKNUT)
    - 'products:detail' reverse-uje na /sr/proizvod/<slug>/ (Story 2-7 NETAKNUT)
    """
    from django.urls import NoReverseMatch

    activate("sr")

    # 1. Novi URL name MORA biti registrovan
    try:
        new_url = reverse("brands:jeegee_prikljucna")
    except NoReverseMatch:
        pytest.fail(
            "URL name 'brands:jeegee_prikljucna' nije registrovan. Dev mora dodati "
            "path('mehanizacija/prikljucna/', JeegeePrikljucnaView.as_view(), "
            "name='jeegee_prikljucna') u apps/brands/urls.py."
        )
    assert new_url == "/sr/mehanizacija/prikljucna/", (
        f"reverse('brands:jeegee_prikljucna') treba '/sr/mehanizacija/prikljucna/', "
        f"dobio {new_url!r}."
    )

    # 2. Story 2-6 brands:detail NETAKNUT (regression — slug pattern radi)
    try:
        brand_detail_url = reverse("brands:detail", kwargs={"slug": "agri-tracking"})
    except NoReverseMatch:
        pytest.fail("Story 2-6 'brands:detail' shadow-ovan novim pattern-om.")
    assert brand_detail_url == "/sr/traktori/agri-tracking/"

    # 3. Story 2-9 products:used_machinery_list NETAKNUT
    try:
        used_url = reverse("products:used_machinery_list")
    except NoReverseMatch:
        pytest.fail("Story 2-9 'products:used_machinery_list' shadow-ovan.")
    assert used_url == "/sr/mehanizacija/polovna/"

    # 4. Story 2-8 products:tractor_list NETAKNUT
    try:
        tractor_url = reverse("products:tractor_list")
    except NoReverseMatch:
        pytest.fail("Story 2-8 'products:tractor_list' shadow-ovan.")
    assert tractor_url == "/sr/traktori/"

    # 5. Story 2-7 products:detail NETAKNUT
    try:
        product_url = reverse("products:detail", kwargs={"slug": "agri-tracking-tb804"})
    except NoReverseMatch:
        pytest.fail("Story 2-7 'products:detail' shadow-ovan.")
    assert product_url == "/sr/proizvod/agri-tracking-tb804/"
