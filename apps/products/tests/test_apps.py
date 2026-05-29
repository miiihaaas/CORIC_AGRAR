"""Story 2.2 — apps/products/apps.py ProductsConfig smoke test (RED phase).

Pokriva AC1 / Gotcha PR-1 — `ProductsConfig.name` MORA biti "apps.products"
(sa `apps.` prefiksom; matches INSTALLED_APPS entry per project-context.md).

Regression guard (mirror 2.1 BR-1 pattern):
- Django startapp default generiše `name = "products"` (bez prefiksa).
- INSTALLED_APPS u config/settings/base.py mora imati `"apps.products"`.
- Ako su nekonzistentni: RuntimeError ili LookupError.

Pokrenuti sa:
    uv run pytest apps/products/tests/test_apps.py -v

TEA RED phase: test MORA pasti dok Dev ne kreira apps/products/apps.py.
"""

from __future__ import annotations


def test_products_config_name_is_apps_products():
    """ProductsConfig.name mora biti 'apps.products' (Gotcha PR-1 regression guard)."""
    from apps.products.apps import ProductsConfig

    assert ProductsConfig.name == "apps.products", (
        f"ProductsConfig.name mora biti 'apps.products' (sa apps. prefiksom), "
        f"dobio: {ProductsConfig.name!r}. Vidi Gotcha PR-1."
    )


def test_products_config_default_auto_field_is_bigautofield():
    """ProductsConfig.default_auto_field mora biti BigAutoField (AC1)."""
    from apps.products.apps import ProductsConfig

    assert ProductsConfig.default_auto_field == "django.db.models.BigAutoField", (
        f"ProductsConfig.default_auto_field mora biti BigAutoField, "
        f"dobio: {ProductsConfig.default_auto_field!r}"
    )
