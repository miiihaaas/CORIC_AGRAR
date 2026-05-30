"""Story 2.8 — Tractor listing URL routing tests (RED phase TDD).

Pokriva AC1 — URL routing kroz i18n_patterns (sr/hu/en) + URL deconfliction sa Story 2.6
`brands:detail` pattern (`traktori/<slug:slug>/`) + 404 za nepostojeći slug pod
brand-detail rutom + APPEND_SLASH redirect.

KRITIČNO (SM-D1 verifikacija): novi `path("traktori/", TractorListView.as_view(), name="tractor_list")`
u apps/products/urls.py NE SME shadow-ovati Story 2.6 `path("traktori/<slug:slug>/", BrandDetailView.as_view())`.
Django resolver iterira u redu (config/urls.py:27 brands prvo, :28 products drugo);
slug converter zahteva content, pa `/sr/traktori/` (bez slug-a) pada na products → TractorListView.

TEA RED phase: SVI testovi MORAJU pasti — `products:tractor_list` URL name nije registrovan,
ImportError za TractorListView u views.py.

Pokrenuti sa:
    docker compose -f compose/local.yml exec django uv run pytest \\
        apps/products/tests/test_url_routing_tractor.py -v

Refs:
- 2-8-tractor-listing-strana-sa-htmx-filterima.md (AC1 + SM-D1 + Subtask 1.3)
- 2-8-interface-contract.md § 2 (Python surface — URL patterns)
"""

from __future__ import annotations

import pytest
from django.urls import NoReverseMatch, reverse
from django.utils.translation import activate

from apps.brands.tests.factories import BrandFactory
from apps.products.tests.factories import TractorProductFactory

pytestmark = pytest.mark.django_db


# =============================================================================
# AC1 — URL routing: sr/hu/en locale resolve
# =============================================================================


def test_tractor_list_url_resolves_sr_locale(client):
    """AC1: /sr/traktori/ vraća HTTP 200 (TractorListView).

    Posle Story 2.8 GREEN: `products:tractor_list` URL name registrovan u
    apps/products/urls.py; view renderuje tractor_listing.html full page.
    """
    activate("sr")
    url = "/sr/traktori/"

    response = client.get(url, HTTP_HOST="localhost")

    assert response.status_code == 200, (
        f"GET {url} treba HTTP 200, dobio {response.status_code}. "
        "Dev mora dodati TractorListView u apps/products/views.py + "
        "path('traktori/', ...) u apps/products/urls.py."
    )


def test_tractor_list_url_resolves_hu_locale(client):
    """AC1: /hu/traktori/ vraća HTTP 200 (i18n_patterns multi-locale)."""
    activate("hu")
    url = "/hu/traktori/"

    response = client.get(url, HTTP_HOST="localhost")

    assert response.status_code == 200, (
        f"GET {url} treba HTTP 200, dobio {response.status_code}. "
        "URL pattern MORA biti UNUTAR i18n_patterns(...) blok-a (config/urls.py:25-31)."
    )


def test_tractor_list_url_resolves_en_locale(client):
    """AC1: /en/traktori/ vraća HTTP 200."""
    activate("en")
    url = "/en/traktori/"

    response = client.get(url, HTTP_HOST="localhost")

    assert response.status_code == 200, (
        f"GET {url} treba HTTP 200, dobio {response.status_code}."
    )


def test_tractor_list_reverse_resolves_to_sr_url():
    """AC1: reverse('products:tractor_list') vraća '/sr/traktori/' u sr locale-u."""
    activate("sr")
    try:
        url = reverse("products:tractor_list")
    except NoReverseMatch:
        pytest.fail(
            "URL name 'products:tractor_list' nije registrovan. "
            "Dev mora dodati path('traktori/', views.TractorListView.as_view(), "
            "name='tractor_list') u apps/products/urls.py."
        )
    assert url == "/sr/traktori/", (
        f"reverse('products:tractor_list') u sr locale-u mora vratiti '/sr/traktori/', "
        f"dobio {url!r}."
    )


# =============================================================================
# AC1 — URL deconfliction sa Story 2.6 brands:detail (SM-D1)
# =============================================================================


def test_brand_detail_url_still_resolves_after_tractor_list_added(client):
    """AC1 + SM-D1: dodavanje `traktori/` pattern-a u apps/products/urls.py NE SME
    shadow-ovati Story 2.6 `traktori/<slug:slug>/` pattern u apps/brands/urls.py.

    Resolver iterira u redu (brands include je prvi u config/urls.py:27);
    `/sr/traktori/<slug>/` matchuje brands:detail (slug converter zahteva content).
    `/sr/traktori/` (bez slug content-a) pada na products:tractor_list.
    """
    activate("sr")
    brand = BrandFactory.create(name="Agri Tracking")
    url = f"/sr/traktori/{brand.slug}/"

    response = client.get(url, HTTP_HOST="localhost")

    assert response.status_code == 200, (
        f"GET {url} treba HTTP 200 (BrandDetailView — Story 2.6 ruta), "
        f"dobio {response.status_code}. Story 2.8 NE SME shadow-ovati Story 2.6 "
        "`brands:detail` URL — vidi SM-D1 deconfliction rationale."
    )


def test_tractor_list_and_brand_detail_both_reverse_independently():
    """AC1 + SM-D1: oba URL name-a (`products:tractor_list` + `brands:detail`)
    rezolvuju TAČNE distinct URL-ove u sr locale-u (smoke verifikacija per
    Subtask 1.3).
    """
    activate("sr")
    try:
        tractor_url = reverse("products:tractor_list")
        brand_url = reverse("brands:detail", kwargs={"slug": "agri-tracking"})
    except NoReverseMatch as exc:
        pytest.fail(
            f"URL reverse fail-ovao: {exc}. Dev mora očuvati BOTH `brands:detail` "
            "(Story 2.6) I `products:tractor_list` (Story 2.8) URL name-ove. "
            "Story 2.8 NE menja apps/brands/urls.py."
        )

    assert tractor_url == "/sr/traktori/", (
        f"products:tractor_list mora rezolvirati '/sr/traktori/', dobio {tractor_url!r}."
    )
    assert brand_url == "/sr/traktori/agri-tracking/", (
        f"brands:detail (slug=agri-tracking) mora rezolvirati '/sr/traktori/agri-tracking/', "
        f"dobio {brand_url!r}."
    )
    assert tractor_url != brand_url, (
        "URL-ovi MORAJU biti distinct (SM-D1 deconfliction). "
        f"tractor_url={tractor_url!r}, brand_url={brand_url!r}."
    )


def test_nonexistent_brand_slug_returns_404(client):
    """AC1 + SM-D1: /sr/traktori/<nepostojeci-slug>/ vraća 404 KROZ BrandDetailView,
    NE TractorListView (slug matchuje brands:detail pattern; brand objekat ne postoji
    → DetailView raise 404).
    """
    activate("sr")
    url = "/sr/traktori/ovaj-brand-stvarno-ne-postoji-12345/"

    response = client.get(url, HTTP_HOST="localhost")

    assert response.status_code == 404, (
        f"GET {url} (nepostojeći brand slug) treba HTTP 404, dobio {response.status_code}. "
        "URL matchuje brands:detail pattern (slug converter pasuje), "
        "BrandDetailView raise 404 jer Brand objekat ne postoji."
    )


def test_tractor_list_with_filter_query_params_returns_200(client):
    """AC1 + AC7: /sr/traktori/?snaga_min=60&cena_max=20000 vraća HTTP 200
    (filter param-i ne menjaju URL pattern resolution).
    """
    activate("sr")
    # Seed: 1 brand + 1 tractor product u traktori scope-u
    brand = BrandFactory.create(name="Test Tractor Brand")
    TractorProductFactory.create(brand=brand, name="Test Tractor", horse_power=80, price_eur=15000)
    url = "/sr/traktori/?snaga_min=60&cena_max=20000"

    response = client.get(url, HTTP_HOST="localhost")

    assert response.status_code == 200, (
        f"GET {url} (sa filter query params) treba HTTP 200, dobio {response.status_code}. "
        "Filter params se parsuju u view (SM-D11 defensive); URL resolution je nezavisan."
    )
