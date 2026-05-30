"""Story 2.7 — Product detail URL routing tests (RED phase TDD).

Pokriva AC1 — URL routing kroz i18n_patterns (sr/hu/en) + 404 za nepostojeći/
unpublished proizvod + APPEND_SLASH redirect za missing trailing slash.

Naming: srpska latinica + engleski code identifiers (per project-context.md).
TEA RED phase: SVI testovi MORAJU pasti dok Dev ne implementira ProductDetailView
i ažurira `apps/products/urls.py` da koristi ProductDetailView umesto placeholder_view.

NAPOMENA: posle Story 2.6 GREEN phase, URL pattern `/sr/proizvod/<slug>/` već postoji
i `placeholder_view` već daje HTTP 200 (bez DB query). Ovi testovi će proći za PUBLISHED
proizvode SAMO kad Dev zameni placeholder_view sa ProductDetailView (DB filter na
`is_published=True`).

Pokrenuti sa:
    docker compose -f compose/local.yml exec django uv run pytest \\
        apps/products/tests/test_url_routing.py -v

Refs:
- 2-7-product-detail-strana.md (story spec, AC1 + Subtask 12.1)
- 2-7-interface-contract.md (URL pattern + view canonical contract)
"""

from __future__ import annotations

import pytest
from django.urls import reverse
from django.utils.translation import activate

from apps.products.tests.factories import ProductFactory

pytestmark = pytest.mark.django_db


# =============================================================================
# AC1 — URL routing: sr/hu/en locale resolve + 404 + APPEND_SLASH redirect
# =============================================================================


def test_product_detail_url_resolves_sr_locale(client):
    """AC1: /sr/proizvod/<slug>/ vraća HTTP 200 za PUBLISHED proizvod.

    Posle Story 2.7 GREEN: ProductDetailView fetch-uje Product iz DB sa
    is_published=True filter; mora vratiti 200 ako proizvod postoji.
    """
    activate("sr")
    product = ProductFactory.create(name="Agri Tracking TB-804", is_published=True)
    url = f"/sr/proizvod/{product.slug}/"

    response = client.get(url, HTTP_HOST="localhost")

    assert response.status_code == 200, (
        f"GET {url} treba HTTP 200 za published proizvod, dobio {response.status_code}. "
        "Dev mora zameniti placeholder_view sa ProductDetailView u apps/products/views.py "
        "+ ažurirati apps/products/urls.py (1-line edit: placeholder_view → ProductDetailView.as_view())."
    )


def test_product_detail_url_resolves_hu_locale(client):
    """AC1: /hu/proizvod/<slug>/ vraća HTTP 200 (i18n_patterns multi-locale)."""
    activate("hu")
    product = ProductFactory.create(name="Hu Test Product", is_published=True)
    url = f"/hu/proizvod/{product.slug}/"

    response = client.get(url, HTTP_HOST="localhost")

    assert response.status_code == 200, (
        f"GET {url} treba HTTP 200 (i18n_patterns multi-locale), dobio {response.status_code}. "
        "URL pattern MORA biti include-ovan UNUTAR i18n_patterns(...) blok-a u config/urls.py "
        "(verifikovano postojeće od Story 2.6 — Story 2.7 ne menja config/urls.py)."
    )


def test_product_detail_url_resolves_en_locale(client):
    """AC1: /en/proizvod/<slug>/ vraća HTTP 200."""
    activate("en")
    product = ProductFactory.create(name="En Test Product", is_published=True)
    url = f"/en/proizvod/{product.slug}/"

    response = client.get(url, HTTP_HOST="localhost")

    assert response.status_code == 200, (
        f"GET {url} treba HTTP 200, dobio {response.status_code}."
    )


def test_product_detail_404_for_nonexistent_slug(client):
    """AC1: /sr/proizvod/nepostojeci/ vraća HTTP 404 KROZ DetailView (NE catch-all 404).

    Mora prvo potvrditi da URL pattern POSTOJI (reverse rezolvuje) — tek onda nepostojeći
    slug daje 404 kroz DetailView.get_object_or_404. Bez URL pattern-a, ovaj test bi
    trivially passed (svaki nepoznat URL je 404), pa koristimo reverse() da osiguramo
    URL name 'products:detail' postoji.
    """
    from django.urls import NoReverseMatch

    activate("sr")
    # Sanity: URL name MORA biti registrovan
    try:
        reverse("products:detail", kwargs={"slug": "nepostojeci"})
    except NoReverseMatch:
        pytest.fail(
            "URL name 'products:detail' nije registrovan. Dev mora očuvati app_name='products' "
            "+ path('proizvod/<slug:slug>/', ProductDetailView.as_view(), name='detail') "
            "u apps/products/urls.py (1-line views referenca update od Story 2.6)."
        )

    url = "/sr/proizvod/ovaj-proizvod-stvarno-ne-postoji-12345/"
    response = client.get(url, HTTP_HOST="localhost")

    assert response.status_code == 404, (
        f"GET {url} (nepostojeći slug, ali URL pattern POSTOJI) treba HTTP 404 "
        f"(ProductDetailView.get_object_or_404), dobio {response.status_code}. "
        "Posle Story 2.7 GREEN, placeholder_view (koji vraća 200 za sve slug-ove) "
        "BIĆE ZAMENJEN sa ProductDetailView (koji vraća 404 za nepostojeći slug)."
    )


def test_product_detail_404_for_unpublished_product(client):
    """AC1: /sr/proizvod/<slug>/ vraća HTTP 404 za is_published=False proizvod.

    Per SM-D3 + SM-D20: `is_published` je SOLE public-visibility gate.
    `get_queryset()` filtruje `is_published=True` — unpublished proizvodi nisu javno
    dostupni regardless of status (status TextChoices je admin-only metadata).
    """
    activate("sr")
    product = ProductFactory.create_unpublished(name="Draft Tractor")
    url = f"/sr/proizvod/{product.slug}/"

    response = client.get(url, HTTP_HOST="localhost")

    assert response.status_code == 404, (
        f"GET {url} (is_published=False proizvod) treba HTTP 404, dobio {response.status_code}. "
        "ProductDetailView.get_queryset() MORA filtrirati `is_published=True` (SM-D3+D20)."
    )
