"""Story 2.12 — Data migracija 0004_seed_hzm_tulip_brands tests (RED phase).

Pokriva AC7: seed HZM Brand + radne-masine Category + 4 Subcategory + Tulip Brand +
2 Tulip Product + 8 ProductSpecification; idempotentnost (get_or_create); reverse
callable FK-safe delete; key_features cap ≤ 3 + price_eur set (6m³ < 8m³).

Pokrenuti sa:
    docker compose -f compose/local.yml run --rm django uv run pytest \\
        apps/brands/tests/test_migration_0004_seed_hzm_tulip.py -v

Refs:
- 2-12-hzm-radne-masine-tulip-mix-prikolice-strane.md (AC7, Subtask 8.6)
- 2-12-interface-contract.md (§ 5 Data migracija)
"""

from __future__ import annotations

from importlib import import_module

import pytest

from apps.brands.models import Brand, Category, Subcategory
from apps.products.models import Product, ProductSpecification

pytestmark = pytest.mark.django_db

_MIGRATION_PATH = "apps.brands.migrations.0004_seed_hzm_tulip_brands"

_HZM_SUBCATEGORY_SLUGS = {
    "mini-utovarivaci",
    "utovarivaci-bez-teleskopa",
    "teleskopski-utovarivaci",
    "telehendleri",
}
_TULIP_PRODUCT_SLUGS = {"tulip-mix-6m3", "tulip-mix-8m3"}


def _load_migration():
    try:
        return import_module(_MIGRATION_PATH)
    except ImportError:
        pytest.fail(
            f"Migration modul '{_MIGRATION_PATH}' nije pronađen. Dev MORA kreirati "
            f"apps/brands/migrations/0004_seed_hzm_tulip_brands.py per AC7."
        )


class _StubSchemaEditor:
    pass


def test_migration_creates_hzm_brand_category_4_subcategories():
    """AC7: HZM Brand + radne-masine Category + 4 Subcategory (parent=None) seed-ovani."""
    hzm = Brand.objects.filter(slug="hzm")
    assert hzm.exists(), (
        "HZM Brand MORA postojati posle 0004 migracije (pytest-django auto-apply)."
    )
    assert hzm.get().name == "HZM", "HZM Brand.name MORA biti 'HZM'."
    assert hzm.get().is_coming_soon is False, "HZM Brand.is_coming_soon MORA biti False."

    cat = Category.objects.filter(slug="radne-masine")
    assert cat.exists(), "radne-masine Category MORA postojati posle 0004."
    category = cat.get()
    assert category.is_for == "mehanizacija", (
        f"radne-masine Category.is_for MORA biti 'mehanizacija', dobio {category.is_for!r}."
    )
    assert category.name == "Radne mašine", (
        f"radne-masine Category.name MORA biti 'Radne mašine', dobio {category.name!r}."
    )

    subs = Subcategory.objects.filter(category__slug="radne-masine")
    assert subs.count() == 4, (
        f"radne-masine MORA imati TAČNO 4 Subcategory, dobio {subs.count()}."
    )
    assert set(subs.values_list("slug", flat=True)) == _HZM_SUBCATEGORY_SLUGS, (
        f"HZM subcategory slug-ovi se ne podudaraju, dobio "
        f"{set(subs.values_list('slug', flat=True))!r}."
    )


def test_subcategory_parents_are_none_and_category_is_radne_masine():
    """AC7: sve 4 HZM Subcategory su parent=None i pripadaju radne-masine Category."""
    subs = Subcategory.objects.filter(category__slug="radne-masine")
    assert subs.count() == 4, (
        f"radne-masine MORA imati TAČNO 4 seed-ovane Subcategory (0004 migracija) pre "
        f"provere parent/category invarianti — sprečava vacuous pass kad seed nedostaje, "
        f"dobio {subs.count()}."
    )
    for sub in subs:
        assert sub.parent_id is None, (
            f"Subcategory {sub.slug!r} MORA imati parent=None, dobio {sub.parent_id!r}."
        )
        assert sub.category.slug == "radne-masine"


def test_migration_creates_tulip_brand_2_products_with_specs():
    """AC7: Tulip Brand + 2 Product + 8 ProductSpecification (4 spec × 2 modela)."""
    tulip = Brand.objects.filter(slug="tulip")
    assert tulip.exists(), "Tulip Brand MORA postojati posle 0004."
    assert tulip.get().name == "Tulip"

    products = Product.objects.filter(brand__slug="tulip")
    assert products.count() == 2, (
        f"Tulip MORA imati TAČNO 2 Product, dobio {products.count()}."
    )
    assert set(products.values_list("slug", flat=True)) == _TULIP_PRODUCT_SLUGS, (
        f"Tulip product slug-ovi se ne podudaraju, dobio "
        f"{set(products.values_list('slug', flat=True))!r}."
    )

    specs = ProductSpecification.objects.filter(product__brand__slug="tulip")
    assert specs.count() == 8, (
        f"Tulip MORA imati TAČNO 8 ProductSpecification (4 dimenzije × 2 modela: Zapremina/"
        f"Dužina/Širina/Nosivost), dobio {specs.count()}."
    )
    # Zapremina key na oba modela
    zapremina = specs.filter(key="Zapremina")
    assert zapremina.count() == 2, (
        f"'Zapremina' spec MORA postojati na oba modela (2 redova), dobio {zapremina.count()}."
    )


def test_tulip_products_key_features_within_cap_and_price_set():
    """AC7: oba Tulip Product imaju len(key_features) <= 3 (cap) + price_eur (6m³ < 8m³).

    Dokazuje da seed prolazi full_clean() bez ValidationError (cap=3) i da je price
    ordering invariant deterministički.
    """
    p6 = Product.objects.get(slug="tulip-mix-6m3")
    p8 = Product.objects.get(slug="tulip-mix-8m3")

    assert len(p6.key_features) <= 3, (
        f"6 m³ key_features MORA imati <= 3 stavke (cap _PRODUCT_KEY_FEATURES_MAX=3), "
        f"dobio {len(p6.key_features)}: {p6.key_features!r}."
    )
    assert len(p8.key_features) <= 3, (
        f"8 m³ key_features MORA imati <= 3 stavke, dobio {len(p8.key_features)}."
    )

    assert p6.price_eur is not None and p8.price_eur is not None, (
        "Oba Tulip modela MORAJU imati eksplicitan price_eur (deterministički sort ključ)."
    )
    assert p6.price_eur < p8.price_eur, (
        f"6 m³ price_eur ({p6.price_eur}) MORA biti < 8 m³ price_eur ({p8.price_eur}) — "
        f"namerni ordering invariant (seed 6500 < 8200)."
    )


def test_migration_is_idempotent():
    """AC7: re-running seed callable NE baca exception + ne kreira duplikate."""
    migration = _load_migration()
    from django.apps import apps as django_apps

    seed_fn = getattr(migration, "seed_hzm_and_tulip", None) or getattr(
        migration, "seed_hzm_tulip", None
    )
    assert seed_fn is not None, (
        "Migracija MORA imati seed callable 'seed_hzm_and_tulip' (ili 'seed_hzm_tulip')."
    )

    initial_brands = Brand.objects.filter(slug__in=["hzm", "tulip"]).count()
    initial_subs = Subcategory.objects.filter(category__slug="radne-masine").count()
    initial_products = Product.objects.filter(brand__slug="tulip").count()
    assert initial_brands == 2 and initial_subs == 4 and initial_products == 2

    try:
        seed_fn(django_apps, _StubSchemaEditor())
    except Exception as exc:  # noqa: BLE001
        pytest.fail(
            f"Re-pokretanje seed callable NE SME bacati exception (idempotent "
            f"get_or_create). Dobijen: {exc!r}"
        )

    assert Brand.objects.filter(slug__in=["hzm", "tulip"]).count() == initial_brands, (
        "Re-run NE SME kreirati duplikate Brand-a."
    )
    assert (
        Subcategory.objects.filter(category__slug="radne-masine").count() == initial_subs
    ), "Re-run NE SME kreirati duplikate Subcategory-ja."
    assert (
        Product.objects.filter(brand__slug="tulip").count() == initial_products
    ), "Re-run NE SME kreirati duplikate Product-a."


def test_migration_reverse_deletes_all_seeded_data():
    """AC7: reverse callable DELETE-uje sav seed (FK-safe), čuva non-seeded instance."""
    migration = _load_migration()
    from django.apps import apps as django_apps

    reverse_fn = getattr(migration, "reverse_seed", None) or getattr(
        migration, "reverse_hzm_tulip", None
    )
    assert reverse_fn is not None, (
        "Migracija MORA imati reverse callable 'reverse_seed' (ili 'reverse_hzm_tulip')."
    )

    # Non-seeded instance koje NE smeju biti obrisane
    other_brand = Brand.objects.create(
        name="Other Brand", slug="other-brand-2-12", brand_color=""
    )

    reverse_fn(django_apps, _StubSchemaEditor())

    assert not Brand.objects.filter(slug="hzm").exists(), "Reverse MORA obrisati HZM Brand."
    assert not Brand.objects.filter(slug="tulip").exists(), "Reverse MORA obrisati Tulip Brand."
    assert not Category.objects.filter(slug="radne-masine").exists(), (
        "Reverse MORA obrisati radne-masine Category."
    )
    assert not Subcategory.objects.filter(category__slug="radne-masine").exists(), (
        "Reverse MORA obrisati svih 4 HZM Subcategory."
    )
    assert not Product.objects.filter(brand__slug="tulip").exists(), (
        "Reverse MORA obrisati 2 Tulip Product."
    )
    assert not ProductSpecification.objects.filter(
        product__slug__in=_TULIP_PRODUCT_SLUGS
    ).exists(), "Reverse MORA obrisati Tulip ProductSpecification."

    assert Brand.objects.filter(slug=other_brand.slug).exists(), (
        "Reverse NE SME obrisati non-seeded Brand-ove (slug-based filter discipline)."
    )
