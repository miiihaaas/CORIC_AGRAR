"""Story 2.12 — HZM + Tulip URL routing tests (RED phase TDD).

Pokriva AC1 — sr/hu/en locale resolve za HZM, sr resolve za Tulip, no-collision
regression guard sa Story 2-9/2-10/2-11 pattern-ima.

TEA RED phase: SVI testovi MORAJU pasti dok Dev ne implementira HzmRadneMasineView +
TulipMixPrikoliceView + apps/brands/urls.py path-ove + 0004 seed migraciju.

Pokrenuti sa:
    docker compose -f compose/local.yml run --rm django uv run pytest \\
        apps/brands/tests/test_urls_hzm_tulip.py -v

Refs:
- 2-12-hzm-radne-masine-tulip-mix-prikolice-strane.md (AC1, Subtask 8.1)
- 2-12-interface-contract.md (§ 1 URL patterns)
"""

from __future__ import annotations

import pytest
from django.urls import reverse
from django.utils.translation import activate

pytestmark = pytest.mark.django_db


def test_hzm_url_resolves_sr(client):
    """AC1: /sr/mehanizacija/radne-masine/ → HTTP 200 (HZM Brand seed kroz 0004)."""
    activate("sr")
    response = client.get("/sr/mehanizacija/radne-masine/")
    assert response.status_code == 200, (
        f"GET /sr/mehanizacija/radne-masine/ treba HTTP 200 (HZM Brand seed-ovan kroz "
        f"0004), dobio {response.status_code}. Dev MORA: HzmRadneMasineView + urls path "
        f"+ 0004_seed_hzm_tulip_brands.py."
    )


def test_hzm_url_resolves_hu(client):
    """AC1: /hu/mehanizacija/radne-masine/ → HTTP 200 (i18n_patterns multi-locale)."""
    activate("hu")
    response = client.get("/hu/mehanizacija/radne-masine/")
    assert response.status_code == 200, (
        f"GET /hu/mehanizacija/radne-masine/ treba HTTP 200, dobio {response.status_code}."
    )


def test_hzm_url_resolves_en(client):
    """AC1: /en/mehanizacija/radne-masine/ → HTTP 200."""
    activate("en")
    response = client.get("/en/mehanizacija/radne-masine/")
    assert response.status_code == 200, (
        f"GET /en/mehanizacija/radne-masine/ treba HTTP 200, dobio {response.status_code}."
    )


def test_tulip_url_resolves_sr(client):
    """AC1: /sr/mehanizacija/mix-prikolice/ → HTTP 200 (Tulip Brand seed kroz 0004)."""
    activate("sr")
    response = client.get("/sr/mehanizacija/mix-prikolice/")
    assert response.status_code == 200, (
        f"GET /sr/mehanizacija/mix-prikolice/ treba HTTP 200, dobio "
        f"{response.status_code}. Dev MORA: TulipMixPrikoliceView + urls path + 0004 seed."
    )


def test_hzm_tulip_reverse_returns_expected_paths(client):
    """AC1: reverse('brands:hzm_radne_masine') + reverse('brands:tulip_mix_prikolice')."""
    from django.urls import NoReverseMatch

    activate("sr")
    try:
        hzm = reverse("brands:hzm_radne_masine")
        tulip = reverse("brands:tulip_mix_prikolice")
    except NoReverseMatch:
        pytest.fail(
            "URL names 'brands:hzm_radne_masine' / 'brands:tulip_mix_prikolice' nisu "
            "registrovani. Dev MORA dodati 2 path-a u apps/brands/urls.py."
        )
    assert hzm == "/sr/mehanizacija/radne-masine/", (
        f"reverse('brands:hzm_radne_masine') treba '/sr/mehanizacija/radne-masine/', "
        f"dobio {hzm!r}."
    )
    assert tulip == "/sr/mehanizacija/mix-prikolice/", (
        f"reverse('brands:tulip_mix_prikolice') treba '/sr/mehanizacija/mix-prikolice/', "
        f"dobio {tulip!r}."
    )


def test_hzm_tulip_no_collision_with_jeegee_subcategory_used_machinery(client):
    """AC1 + SM-D5: novi statički path-ovi NE shadow-uju Story 2-9/2-10/2-11.

    Verifikuje da postojeći mehanizacija pattern-i i dalje rezolvuju svoje view-ove:
    - /sr/mehanizacija/prikljucna/ → JeegeePrikljucnaView (Story 2-10)
    - /sr/mehanizacija/prikljucna/<cat>/ → SubcategoryListView (Story 2-11)
    - /sr/mehanizacija/polovna/ → UsedMachineryListView (Story 2-9)
    """
    from django.urls import NoReverseMatch, Resolver404, resolve

    activate("sr")

    # Jeegee landing — NETAKNUT
    try:
        jeegee = reverse("brands:jeegee_prikljucna")
    except NoReverseMatch:
        pytest.fail("Story 2-10 'brands:jeegee_prikljucna' shadow-ovan.")
    assert jeegee == "/sr/mehanizacija/prikljucna/"
    try:
        match = resolve("/sr/mehanizacija/prikljucna/")
    except Resolver404:
        pytest.fail("/sr/mehanizacija/prikljucna/ se ne rezolvuje (regression).")
    assert match.func.view_class.__name__ == "JeegeePrikljucnaView", (
        f"/sr/mehanizacija/prikljucna/ MORA rezolvovati JeegeePrikljucnaView, dobio "
        f"{match.func.view_class.__name__!r}."
    )

    # Subcategory drill-down — NETAKNUT
    try:
        sub_match = resolve("/sr/mehanizacija/prikljucna/osnovna-obrada-zemljista/")
    except Resolver404:
        pytest.fail(
            "/sr/mehanizacija/prikljucna/<cat>/ se ne rezolvuje (Story 2-11 regression)."
        )
    assert sub_match.func.view_class.__name__ == "SubcategoryListView", (
        f"Subcategory listing MORA rezolvovati SubcategoryListView, dobio "
        f"{sub_match.func.view_class.__name__!r}."
    )

    # Used machinery — NETAKNUT
    try:
        used = reverse("products:used_machinery_list")
    except NoReverseMatch:
        pytest.fail("Story 2-9 'products:used_machinery_list' shadow-ovan.")
    assert used == "/sr/mehanizacija/polovna/"


def test_hzm_url_routes_to_hzm_view(client):
    """AC1: /sr/mehanizacija/radne-masine/ je mapiran na HzmRadneMasineView."""
    from django.urls import Resolver404, resolve

    activate("sr")
    try:
        match = resolve("/sr/mehanizacija/radne-masine/")
    except Resolver404:
        pytest.fail(
            "/sr/mehanizacija/radne-masine/ se ne rezolvuje — HzmRadneMasineView + "
            "urls path još ne postoje (RED phase)."
        )
    assert match.func.view_class.__name__ == "HzmRadneMasineView", (
        f"/sr/mehanizacija/radne-masine/ MORA rezolvovati HzmRadneMasineView, dobio "
        f"{match.func.view_class.__name__!r}."
    )


def test_tulip_url_routes_to_tulip_view(client):
    """AC1: /sr/mehanizacija/mix-prikolice/ je mapiran na TulipMixPrikoliceView."""
    from django.urls import Resolver404, resolve

    activate("sr")
    try:
        match = resolve("/sr/mehanizacija/mix-prikolice/")
    except Resolver404:
        pytest.fail(
            "/sr/mehanizacija/mix-prikolice/ se ne rezolvuje — TulipMixPrikoliceView + "
            "urls path još ne postoje (RED phase)."
        )
    assert match.func.view_class.__name__ == "TulipMixPrikoliceView", (
        f"/sr/mehanizacija/mix-prikolice/ MORA rezolvovati TulipMixPrikoliceView, dobio "
        f"{match.func.view_class.__name__!r}."
    )
