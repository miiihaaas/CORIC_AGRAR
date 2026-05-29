"""Story 2.1 — apps/brands/apps.py BrandsConfig smoke test (RED phase).

Pokriva AC1 / Gotcha BR-1 — `BrandsConfig.name` MORA biti "apps.brands"
(sa `apps.` prefiksom; matches INSTALLED_APPS entry per project-context.md).

Regression guard:
- Django startapp default generiše `name = "brands"` (bez prefiksa).
- INSTALLED_APPS u config/settings/base.py mora imati `"apps.brands"`.
- Ako su nekonzistentni: RuntimeError ili LookupError.

Pokrenuti sa:
    uv run pytest apps/brands/tests/test_apps.py -v

TEA RED phase: test MORA pasti dok Dev ne kreira apps/brands/apps.py.
"""

from __future__ import annotations


def test_brands_config_name_is_apps_brands():
    """BrandsConfig.name mora biti 'apps.brands' (Gotcha BR-1 regression guard)."""
    from apps.brands.apps import BrandsConfig

    assert BrandsConfig.name == "apps.brands", (
        f"BrandsConfig.name mora biti 'apps.brands' (sa apps. prefiksom), "
        f"dobio: {BrandsConfig.name!r}. Vidi Gotcha BR-1."
    )


def test_brands_config_default_auto_field_is_bigautofield():
    """BrandsConfig.default_auto_field mora biti BigAutoField (AC1)."""
    from apps.brands.apps import BrandsConfig

    assert BrandsConfig.default_auto_field == "django.db.models.BigAutoField", (
        f"BrandsConfig.default_auto_field mora biti BigAutoField, "
        f"dobio: {BrandsConfig.default_auto_field!r}"
    )
