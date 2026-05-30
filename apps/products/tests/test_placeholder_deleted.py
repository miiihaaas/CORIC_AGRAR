"""Story 2.7 — Regression guard za Subtask 1.3 + 1.4 placeholder DELETE (RED phase TDD).

Pokriva Subtask 12.5 — verifikuje da posle Story 2.7 GREEN phase:
1. `templates/products/_placeholder.html` fajl JE OBRISAN
2. `apps/products/views.py` više NE EKSPONUJE `placeholder_view` symbol
3. `apps/products/tests/test_placeholder.py` fajl JE OBRISAN (Subtask 1.4 zero-orphan policy)
4. URL `/sr/proizvod/<slug>/` sada serve-uje ProductDetailView (NE placeholder_view)

OVI TESTOVI ĆE PASTI U RED PHASE — placeholder fajlovi i symbol JOŠ POSTOJE.
Posle Dev Subtask 1.1+1.3+1.4 (DELETE FBV + DELETE template + DELETE test file)
testovi će PROĆI.

NAPOMENA: test #4 (URL serves ProductDetailView) je sanity check da ista URL ruta
koja je Story 2.6 servirala placeholder sada serve-uje ProductDetailView. Ovo je
REPLACEMENT za 4 obrisana placeholder testa koji asertuju isti URL serve-uje 200.

Pokrenuti sa:
    docker compose -f compose/local.yml exec django uv run pytest \\
        apps/products/tests/test_placeholder_deleted.py -v

Refs:
- 2-7-product-detail-strana.md (Subtask 1.3 + 1.4 + 12.5; SM-D16 + C2)
"""

from __future__ import annotations

import pathlib

import pytest
from django.utils.translation import activate

from apps.products.tests.factories import ProductFactory

pytestmark = pytest.mark.django_db


# Project root = parent direktorijum od tests/ folder-a (4 levels up od ovog fajla):
# apps/products/tests/test_placeholder_deleted.py → up 4 → CORIC_AGRAR/
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[3]


# =============================================================================
# Subtask 12.5 — Placeholder DELETE regression guards
# =============================================================================


def test_placeholder_template_file_does_not_exist():
    """Subtask 1.3 + 12.5: `templates/products/_placeholder.html` MORA biti obrisan."""
    placeholder_path = PROJECT_ROOT / "templates/products/_placeholder.html"
    assert not placeholder_path.exists(), (
        f"Subtask 1.3 (DELETE _placeholder.html) NIJE izvršen. "
        f"Fajl {placeholder_path} JOŠ POSTOJI. Dev mora obrisati template kao deo Story 2.7 GREEN."
    )


def test_placeholder_view_no_longer_in_views_module():
    """Subtask 1.1 + 12.5: `apps/products/views.py` NE SME više eksponovati `placeholder_view` symbol."""
    from apps.products import views

    assert not hasattr(views, "placeholder_view"), (
        "Subtask 1.1 (DELETE placeholder_view FBV) NIJE izvršen. "
        "apps.products.views JOŠ EKSPONUJE `placeholder_view` symbol. "
        "Dev mora ukloniti FBV i zameniti sa ProductDetailView CBV."
    )
    # Pozitivna sanity: ProductDetailView MORA postojati
    assert hasattr(views, "ProductDetailView"), (
        "apps.products.views MORA eksponovati `ProductDetailView` class (Story 2.7 replacement)."
    )


def test_placeholder_test_file_does_not_exist():
    """Subtask 1.4 + 12.5 (C2 zero-orphan policy): `apps/products/tests/test_placeholder.py`
    MORA biti obrisan (orfani testovi koji asertuju placeholder rendering)."""
    test_placeholder_path = PROJECT_ROOT / "apps/products/tests/test_placeholder.py"
    assert not test_placeholder_path.exists(), (
        f"Subtask 1.4 (DELETE test_placeholder.py) NIJE izvršen. "
        f"Fajl {test_placeholder_path} JOŠ POSTOJI. "
        "Story 2.6 placeholder tests (4 testa) su orfanovi posle Subtask 1.1+1.3 DELETE-ova "
        "(testiraju FBV+template koji više ne postoje). Zero-orphan policy zahteva DELETE."
    )


def test_product_detail_url_now_serves_product_detail_view(client):
    """Subtask 12.5 sanity: ista URL ruta `/sr/proizvod/<slug>/` koja je u Story 2.6
    servirala placeholder_view sada serve-uje ProductDetailView.

    Verifikuje response.resolver_match.func.view_class je ProductDetailView (NE FBV).
    """
    activate("sr")
    product = ProductFactory.create(name="URL Sanity Test", is_published=True)
    url = f"/sr/proizvod/{product.slug}/"

    response = client.get(url, HTTP_HOST="localhost")
    assert response.status_code == 200

    # CBV resolver match has 'view_class' atribut (NE FBV koji ima samo 'func')
    resolver_match = response.resolver_match
    view_class = getattr(resolver_match.func, "view_class", None)
    assert view_class is not None, (
        "URL `/sr/proizvod/<slug>/` MORA biti served kroz CBV (sa `view_class` atributom). "
        f"resolver_match.func: {resolver_match.func!r}. "
        "Story 2.7 zamenjuje placeholder_view FBV sa ProductDetailView CBV."
    )
    assert view_class.__name__ == "ProductDetailView", (
        f"URL MORA serve-ovati `ProductDetailView` class; dobio {view_class.__name__!r}."
    )
